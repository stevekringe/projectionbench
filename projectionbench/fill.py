"""Fill the database toward a plan, one request at a time, whenever quota allows.

`run` spends a fixed batch of requests and stops. That is the wrong shape for
free tiers, where each key has its own per-minute and per-day ceiling and the
ceiling, not the work, decides how far a session gets. `fill` compares the
database against a plan (fill.yaml) and makes the next useful request:

- A conversation is complete when every probe exists, error-free, at the
  scenario's CURRENT wording (content_hash). Rewording a scenario or raising
  `samples` just creates new gaps; nothing still valid is re-run.
- A probe is judged when a successful verdict exists for the judge's current id
  (model + RUBRIC_VERSION). Bumping the rubric creates new gaps the same way.

It never substitutes one model for another. A subject is the thing being
measured and a judge is pinned per leaderboard generation, so when one is out
of quota fill works on something else and comes back when its cooldown ends.
Cooldowns are stored per API key and model in the database, so a daily limit
hit tonight is still respected by tomorrow's invocation.

Every successful request is written immediately. Ctrl-C, a crash, or a quota
wall mid-conversation loses nothing: the next invocation continues that
conversation from its last stored reply (within RESUME_WINDOW).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

import yaml

from projectionbench import store
from projectionbench.adapters import Adapter
from projectionbench.judge import lexicon
from projectionbench.scenarios import Scenario

# A stored partial conversation older than this is left alone rather than
# continued. Model aliases float (REVIEW B4), so a reply from days ago and one
# from now may not come from the same weights. A day and a half covers a daily
# quota wall hit mid-conversation.
RESUME_WINDOW = timedelta(hours=36)

# Failures that belong to the task rather than the quota (timeouts, malformed
# judge output). After this many in one invocation the task waits for the next
# invocation, so one poisoned probe cannot spin the loop all night.
MAX_TASK_ATTEMPTS = 3

# Seconds a failure benches its quota scope: (first strike, cap), doubling per
# consecutive strike. Daily quotas are polled every few hours rather than
# computed -- reset times differ by provider, and a wrong guess costs one request.
BACKOFF = {
    "rate": (60, 30 * 60),
    "daily": (60 * 60, 6 * 60 * 60),
    # Provider overloaded (503 "high demand"): nothing to do with the task, and
    # it can last an hour, so it backs off further than a one-off timeout.
    "unavailable": (30, 30 * 60),
    "transient": (30, 10 * 60),
}

# Re-export the dashboard data after this many new rows, so a long fill shows
# progress without waiting for the end.
EXPORT_EVERY = 20

TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"


# --- plan ----------------------------------------------------------------------

@dataclass
class Plan:
    collect_scenarios: list[str]
    samples: int
    subjects: list[str]
    judge_scenarios: list[str]
    judges: list[str]
    caps: dict[str, int] = field(default_factory=dict)


def load_plan(path: str) -> Plan:
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    c, j = raw.get("collect") or {}, raw.get("judge") or {}
    return Plan(
        collect_scenarios=list(c.get("scenarios") or []),
        samples=int(c.get("samples", 1)),
        subjects=list(c.get("subjects") or []),
        judge_scenarios=list(j.get("scenarios") or []),
        judges=[str(x) for x in (j.get("judges") or [])],
        caps={str(k): int(v) for k, v in (raw.get("caps") or {}).items()},
    )


def match_scenarios(scen: list[Scenario], wanted: list[str]) -> list[Scenario]:
    """Same matching as `run --only` (id, id prefix, or category), in plan order."""
    out: list[Scenario] = []
    for w in wanted:
        hits = [s for s in scen if s.id == w or s.id.startswith(w) or s.category == w]
        if not hits:
            raise ValueError(f"plan names scenario {w!r}, which matches nothing")
        out += [s for s in hits if s not in out]
    return out


def load_env_file(path: str = ".env") -> list[str]:
    """Export variables from a .env file that are not already set. Returns the
    names it set, never the values. Blank values are skipped, so an unfilled
    `ANTHROPIC_API_KEY=` line cannot shadow a real credential."""
    if not os.path.isfile(path):
        return []
    names = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.removeprefix("export ").partition("=")
            name = name.strip()
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip().strip("'\"")
            if value and name not in os.environ:
                os.environ[name] = value
                names.append(name)
    return names


# --- error classification --------------------------------------------------------

_BAD_OUTPUT = re.compile(r"schema validation|no parsed output", re.I)
_RATE = re.compile(r"\b429\b|RESOURCE_EXHAUSTED|RateLimit|rate[ _-]?limit|quota", re.I)
_DAILY = re.compile(r"per[ _-]?day|daily", re.I)
_FATAL = re.compile(
    # 410 Gone: the provider retired the model (NVIDIA did this to
    # deepseek-v4-pro-0813 on 2026-11-04). Waiting never brings it back.
    r"\b(400|401|403|404|410)\b|UNAUTHENTICATED|PERMISSION_DENIED|NOT_FOUND|INVALID_ARGUMENT"
    r"|AuthenticationError|PermissionDenied|NotFoundError|BadRequestError"
    r"|no longer available|is not set|node not found",
    re.I,
)
_UNAVAILABLE = re.compile(
    r"\b(500|502|503|504|529)\b|UNAVAILABLE|overloaded|InternalServerError|high demand", re.I
)
_RETRY_HINT = re.compile(r"retry in ([\d.]+)\s*s|retryDelay['\"]?:\s*['\"]([\d.]+)s", re.I)


def classify(error: str) -> tuple[str, float | None, bool]:
    """(kind, provider's retry hint in seconds, whether the limit is per model).

    kind: `rate` and `daily` bench the quota scope; `unavailable` (5xx, the
    provider is overloaded) benches it with a longer backoff; `transient`
    (timeouts, dropped connections) benches it briefly and counts against the
    task, since a conversation that always times out may be the task's own
    fault; `fatal` (bad key, unknown model) parks the scope for the rest of the
    invocation, since waiting does not fix configuration; `bad_output` (a judge
    reply that failed the schema) is the task's problem, not the key's.

    A daily limit is per model only when the provider says so (Gemini's quota
    ids end in PerModel); OpenRouter's free-model cap and Cloudflare's neuron
    budget are account-wide, so those bench every model on the key.
    """
    e = error or ""
    if _BAD_OUTPUT.search(e):
        return "bad_output", None, True
    hints = [float(a or b) for a, b in _RETRY_HINT.findall(e)]
    hint = max(hints) if hints else None
    if _RATE.search(e):
        if _DAILY.search(e):
            return "daily", hint, "PerModel" in e
        return "rate", hint, True
    if _FATAL.search(e):
        return "fatal", None, True
    if _UNAVAILABLE.search(e):
        return "unavailable", hint, True
    return "transient", hint, True


def cooldown_seconds(kind: str, strikes: int, hint: float | None) -> float:
    first, cap = BACKOFF[kind]
    backoff = min(first * 2 ** (strikes - 1), cap)
    # Trust a short provider hint once; if the same scope keeps failing, the
    # hint was wrong and doubling takes over.
    if kind == "rate" and hint and strikes == 1:
        return hint + 2
    return backoff


# --- conversations -----------------------------------------------------------------

def next_request(scenario: Scenario, replies: list[str]) -> tuple[int, object, list[dict]]:
    """(turn index, turn, history) for probe number `len(replies)`, with the
    stored replies standing in for earlier probes -- exactly what
    runner.run_unit would have sent had it not been interrupted."""
    history: list[dict] = []
    ordinal = 0
    for i, turn in enumerate(scenario.turns):
        history.append({"role": turn.role, "content": scenario.user_text(turn, replies[:ordinal])})
        if turn.role == "assistant" or not turn.probe:
            continue
        if ordinal == len(replies):
            return i, turn, history
        history.append({"role": "assistant", "content": replies[ordinal]})
        ordinal += 1
    raise ValueError(f"{scenario.id} has only {ordinal} probes")


def _conversations(conn, subject: str, scenario: Scenario, now: datetime):
    """(complete count, resumable conversations) for one subject and scenario,
    at the scenario's current wording. A resumable conversation is a stored
    prefix -- probes 0..k-1, no gaps, current hash, recent run -- whose last
    stored history matches what next_request rebuilds, so continuing it sends
    the model exactly the conversation it was already in."""
    rows = conn.execute(
        "SELECT p.*, r.started_at FROM probes p JOIN runs r ON r.run_id = p.run_id "
        "WHERE p.subject = ? AND p.scenario_id = ? AND p.error IS NULL "
        "ORDER BY p.run_id, p.sample_idx, p.probe_ordinal",
        (subject, scenario.id),
    ).fetchall()
    groups: dict[tuple[str, int], list] = {}
    for r in rows:
        groups.setdefault((r["run_id"], r["sample_idx"]), []).append(r)

    n = len(scenario.probes)
    complete, resumable = 0, []
    for (run_id, sample_idx), g in groups.items():
        if [r["probe_ordinal"] for r in g] != list(range(len(g))):
            continue
        if any(r["scenario_hash"] != scenario.content_hash for r in g):
            continue
        if len(g) == n or scenario.finished([r["response"] for r in g]):
            # Real-mistake track: a conversation that stopped because the
            # model was right is complete too.
            complete += 1
            continue
        if now - datetime.fromisoformat(g[0]["started_at"]) > RESUME_WINDOW:
            continue
        replies = [r["response"] for r in g]
        _, _, rebuilt = next_request(scenario, replies[:-1])
        stored = [{"role": m["role"], "content": m["content"]} for m in json.loads(g[-1]["messages"])]
        if rebuilt != stored:
            continue
        resumable.append((run_id, sample_idx, replies))
    resumable.sort(reverse=True)  # newest run first
    return complete, resumable


# --- tasks ---------------------------------------------------------------------------

@dataclass
class Task:
    kind: str                 # collect | judge
    scope: str                # quota scope: '<KEY_ENV>|<model>'
    rank: tuple               # lower runs first within a scope
    key: tuple                # identity, for per-task failure counts
    adapter: Adapter | None = None
    scenario: Scenario | None = None
    run_id: str | None = None
    sample_idx: int | None = None
    replies: list[str] = field(default_factory=list)
    judge: object | None = None
    probe: object | None = None


def subject_scope(a: Adapter) -> str:
    env = getattr(a, "api_key_env", None) or getattr(a, "api_token_env", None) or a.name
    return f"{env}|{a.model}"


def judge_scope(j) -> str:
    return f"{j.key_env}|{j.model}"


def quiet(a):
    """Turn off retry sleeps: the adapter's own loop and the SDK client's
    built-in retries (openai/anthropic retry twice by default, each up to the
    full request timeout). Waiting inside one request blocks every other key;
    fill would rather note the cooldown and move on. Works on judges too."""
    if hasattr(a, "max_retries"):
        a.max_retries = 0
    if hasattr(a, "max_attempts"):
        a.max_attempts = 1
    client = getattr(a, "_client", None)
    if hasattr(client, "with_options"):
        a._client = client.with_options(max_retries=0)
    return a


@dataclass
class Setup:
    collect: list[Scenario]
    samples: int
    subjects: list[Adapter]
    judge_scenarios: list[str]
    judges: list
    scenarios_by_id: dict[str, Scenario]
    caps: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)


def setup_from_plan(plan: Plan, scen: list[Scenario], max_tokens: int = 16000) -> Setup:
    from projectionbench.adapters import build
    from projectionbench.judge.llm import LLMJudge

    skipped: dict[str, str] = {}
    subjects = []
    for spec in plan.subjects:
        try:
            subjects.append(quiet(build(spec, max_tokens=max_tokens)))
        except Exception as e:  # noqa: BLE001 - a missing key skips one subject
            skipped[spec] = str(e)
    judges = []
    for spec in plan.judges:
        try:
            judges.append(quiet(LLMJudge() if spec == "default" else LLMJudge(model=spec)))
        except Exception as e:  # noqa: BLE001
            skipped[f"judge {spec}"] = str(e)
    return Setup(
        collect=match_scenarios(scen, plan.collect_scenarios),
        samples=plan.samples,
        subjects=subjects,
        judge_scenarios=[s.id for s in match_scenarios(scen, plan.judge_scenarios)],
        judges=judges,
        scenarios_by_id={s.id: s for s in scen},
        caps=plan.caps,
        skipped=skipped,
    )


def gaps(conn, setup: Setup, now: datetime) -> tuple[list[Task], dict]:
    """Everything still missing, as tasks, plus per-(subject, scenario)
    coverage (complete, in progress) for the status report."""
    tasks: list[Task] = []
    coverage: dict[tuple[str, str], tuple[int, int]] = {}
    for a in setup.subjects:
        scope = subject_scope(a)
        for order, s in enumerate(setup.collect):
            complete, resumable = _conversations(conn, a.subject_id, s, now)
            need = setup.samples - complete
            live = resumable[: max(need, 0)]
            coverage[(a.subject_id, s.id)] = (complete, len(live))
            for run_id, sample_idx, replies in live:
                tasks.append(Task(
                    "collect", scope, rank=(0, complete, order),
                    key=("collect", a.subject_id, s.id, run_id, sample_idx, len(replies)),
                    adapter=a, scenario=s, run_id=run_id, sample_idx=sample_idx, replies=replies,
                ))
            if need > len(live):
                # Breadth-first: the scenario with the fewest complete
                # conversations goes first, so a partial fill is still even.
                tasks.append(Task(
                    "collect", scope, rank=(2, complete, order),
                    key=("collect", a.subject_id, s.id, "new"), adapter=a, scenario=s,
                ))

    if setup.judge_scenarios:
        marks = ",".join("?" for _ in setup.judge_scenarios)
        for j in setup.judges:
            rows = conn.execute(
                f"SELECT p.* FROM probes p WHERE p.error IS NULL AND p.scenario_id IN ({marks}) "
                "AND NOT EXISTS (SELECT 1 FROM judgments x WHERE x.probe_id = p.id "
                "AND x.judge = ? AND x.error IS NULL) ORDER BY p.id",
                (*setup.judge_scenarios, j.judge_id),
            ).fetchall()
            for r in rows:
                s = setup.scenarios_by_id.get(r["scenario_id"])
                current = s is not None and r["scenario_hash"] == s.content_hash
                tasks.append(Task(
                    "judge", judge_scope(j), rank=(1, 0 if current else 1, r["id"]),
                    key=("judge", j.judge_id, r["id"]), judge=j, probe=r,
                ))
    return tasks, coverage


# --- cooldown store --------------------------------------------------------------------

def _fmt(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime(TIME_FMT)


def _parse(s: str) -> datetime:
    return datetime.strptime(s, TIME_FMT).replace(tzinfo=timezone.utc)


def active_cooldowns(conn, now: datetime) -> dict[str, dict]:
    return {
        r["scope"]: dict(r)
        for r in conn.execute(
            "SELECT * FROM cooldowns WHERE kind != 'fatal' AND until > ?", (_fmt(now),)
        )
    }


def _blocking(scope: str, cooldowns: dict[str, dict]) -> dict | None:
    return cooldowns.get(scope) or cooldowns.get(scope.split("|", 1)[0] + "|*")


def _bench(conn, scope: str, kind: str, hint: float | None, reason: str, now: datetime) -> datetime:
    prev = conn.execute("SELECT strikes FROM cooldowns WHERE scope = ?", (scope,)).fetchone()
    strikes = prev["strikes"] + 1 if prev else 1
    until = now + timedelta(seconds=cooldown_seconds(kind, strikes, hint)) if kind != "fatal" else now
    conn.execute(
        "INSERT OR REPLACE INTO cooldowns (scope, until, kind, strikes, reason) VALUES (?, ?, ?, ?, ?)",
        (scope, _fmt(until), kind, strikes, reason[:500]),
    )
    conn.commit()
    return until


# --- execution ----------------------------------------------------------------------------

def _collect(conn, t: Task, new_run: Callable[[], str]) -> str | None:
    i, turn, history = next_request(t.scenario, t.replies)
    reply = t.adapter.complete(list(history), system=t.scenario.system)
    if reply.error:
        return reply.error

    run_id, sample_idx = t.run_id, t.sample_idx
    if run_id is None:
        # A fresh sample number per (subject, scenario) across all runs, so no
        # two conversations share one -- the collision the dashboard's proposal
        # keys used to trip over when every run started at 0.
        run_id = new_run()
        sample_idx = conn.execute(
            "SELECT COALESCE(MAX(sample_idx), -1) + 1 FROM probes WHERE subject = ? AND scenario_id = ?",
            (t.adapter.subject_id, t.scenario.id),
        ).fetchone()[0]
    s = t.scenario
    probe_id = store.insert_probe(conn, {
        "run_id": run_id, "subject": t.adapter.subject_id, "scenario_id": s.id,
        "category": s.category, "sample_idx": sample_idx, "turn_index": i,
        "probe_ordinal": len(t.replies), "user_affect": turn.user_affect,
        "expect": turn.expect, "invites_self_disclosure": int(turn.invites_self_disclosure),
        "prohibited": int(turn.prohibited), "licensed": json.dumps(list(turn.licensed)),
        "scenario_hash": s.content_hash, "tests": turn.tests, "system": s.system,
        "messages": json.dumps(history), "response": reply.text,
        "raw": json.dumps(reply.raw), "error": None,
        "planted_realized": "yes" if turn.correction is not None else None,
    })
    v = lexicon.score_probe(reply.text, turn.user_affect, turn.expect,
                            turn.invites_self_disclosure, list(turn.licensed))
    store.insert_judgment(conn, probe_id, "lexicon", v.to_dict())
    conn.commit()
    return None


def _judge(conn, t: Task) -> str | None:
    v, err = t.judge.judge(json.loads(t.probe["messages"]), t.probe["response"])
    if err:
        # Only a malformed verdict is about this probe. A 429 or timeout says
        # nothing about it, so it leaves no row behind.
        if classify(err)[0] == "bad_output":
            store.insert_judgment(conn, t.probe["id"], t.judge.judge_id, {}, err)
            conn.commit()
        return err
    store.insert_judgment(conn, t.probe["id"], t.judge.judge_id, v.model_dump(), None)
    conn.commit()
    return None


def _describe(t: Task) -> str:
    if t.kind == "judge":
        p = t.probe
        return f"judge   {p['subject']} {p['scenario_id'][:3]} #{p['id']} t{p['probe_ordinal']}"
    sample = "new" if t.sample_idx is None else f"s{t.sample_idx}"
    return f"collect {t.adapter.subject_id} {t.scenario.id[:3]} {sample} t{len(t.replies)}"


def _pick(ready: list[Task], last_scope: str | None, last_kind: dict[str, str]) -> Task:
    """Round-robin across quota scopes, so every key with quota makes progress
    instead of the first one starving the rest. Inside a scope, alternate
    collecting and judging when both are waiting (a judge and a subject can
    share one key)."""
    scopes = sorted({t.scope for t in ready})
    later = [s for s in scopes if last_scope is not None and s > last_scope]
    scope = later[0] if later else scopes[0]
    lane = sorted((t for t in ready if t.scope == scope), key=lambda t: t.rank)
    other = [t for t in lane if t.kind != last_kind.get(scope)]
    return other[0] if other and lane[0].kind == last_kind.get(scope) else lane[0]


@dataclass
class Summary:
    ok: int = 0
    failed: int = 0
    reason: str = ""
    status: str = ""


def _local(t: datetime) -> str:
    return t.astimezone().strftime("%a %H:%M %Z")


def status_report(conn, setup: Setup, now: datetime, coverage: dict, tasks: list[Task],
                  parked: dict[str, str], capped: set[str]) -> str:
    lines = [f"projectionbench fill -- status at {_local(now)}", ""]
    if setup.subjects and setup.collect:
        lines.append(f"collect: complete conversations at current wording (target {setup.samples})")
        width = max(len(a.subject_id) for a in setup.subjects)
        lines.append("  " + " " * width + "  " + "  ".join(f"{s.id[:3]:>9}" for s in setup.collect))
        for a in setup.subjects:
            cells = []
            for s in setup.collect:
                done, live = coverage.get((a.subject_id, s.id), (0, 0))
                cells.append(f"{done}/{setup.samples}{'+' if live else ' '}".rjust(9))
            lines.append(f"  {a.subject_id:<{width}}  " + "  ".join(cells))
        lines.append("  (+ = a conversation in progress; it continues on the next request)")
        lines.append("")
    if setup.judges and setup.judge_scenarios:
        marks = ",".join("?" for _ in setup.judge_scenarios)
        total = conn.execute(
            f"SELECT COUNT(*) FROM probes WHERE error IS NULL AND scenario_id IN ({marks})",
            setup.judge_scenarios,
        ).fetchone()[0]
        for j in setup.judges:
            missing = sum(1 for t in tasks if t.kind == "judge" and t.judge is j)
            lines.append(f"judge {j.judge_id}: {total - missing}/{total} probes judged")
        lines.append("")
    pending = Counter(t.scope for t in tasks)
    cooldowns = active_cooldowns(conn, now)
    waiting = [(s, c) for s, c in cooldowns.items() if any(_blocking(t, {s: c}) for t in pending)]
    if waiting:
        lines.append("cooling down:")
        for s, c in sorted(waiting, key=lambda x: x[1]["until"]):
            why = re.sub(r"\s+", " ", c["reason"] or "")[:110]
            lines.append(f"  {s}  {c['kind']} until {_local(_parse(c['until']))}  -- {why}")
        lines.append("")
    if parked:
        lines.append("parked this session (fix the config, then run fill again):")
        for s, why in parked.items():
            why = re.sub(r"\s+", " ", why)[:140]
            lines.append(f"  {s}  -- {why}")
        lines.append("")
    if capped:
        lines.append("hit this session's request cap (caps: in the plan): " + ", ".join(sorted(capped)))
        lines.append("")
    if setup.skipped:
        lines.append("not started (could not build):")
        for spec, why in setup.skipped.items():
            lines.append(f"  {spec}  -- {why[:140]}")
        lines.append("")
    left = Counter(t.kind for t in tasks)
    lines.append(f"still to do: {left['collect']} conversation step(s) queued, {left['judge']} probe(s) to judge")
    return "\n".join(lines) + "\n"


def fill(
    conn,
    setup: Setup,
    *,
    watch: bool = False,
    deadline: datetime | None = None,
    dry_run: bool = False,
    on_export: Callable[[], None] | None = None,
    status_path: str | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = lambda m: print(m, file=sys.stderr, flush=True),
) -> Summary:
    summary = Summary()
    parked: dict[str, str] = {}      # scope -> fatal error, this invocation only
    capped: set[str] = set()
    attempts: Counter = Counter()    # task key -> task-owned failures
    spent: Counter = Counter()       # scope -> requests made this invocation
    last_scope: str | None = None
    last_kind: dict[str, str] = {}
    unexported = 0
    run_id: str | None = None

    def new_run() -> str:
        nonlocal run_id
        if run_id is None:
            run_id = store.new_run(conn, {
                "mode": "fill",
                "subjects": [a.subject_id for a in setup.subjects],
                "scenarios": [s.id for s in setup.collect],
                "samples": setup.samples,
            })
        return run_id

    def cap_for(scope: str) -> int | None:
        env = scope.split("|", 1)[0]
        return setup.caps.get(scope, setup.caps.get(env))

    def export() -> None:
        nonlocal unexported
        if unexported and on_export:
            try:
                on_export()
            except Exception as e:  # noqa: BLE001 - a stale dashboard must not end a fill
                log(f"[{_local(now())}] export failed, continuing: {type(e).__name__}: {e}")
        unexported = 0

    try:
        while not dry_run:
            if deadline and now() >= deadline:
                summary.reason = "time limit reached"
                break
            tasks, coverage = gaps(conn, setup, now())
            workable = [t for t in tasks if t.scope not in parked and t.scope not in capped
                        and attempts[t.key] < MAX_TASK_ATTEMPTS]
            if not workable:
                summary.reason = ("nothing left to do" if not tasks else
                                  "what is left is parked, capped, or failed repeatedly this session")
                break
            cooldowns = active_cooldowns(conn, now())
            ready = [t for t in workable if not _blocking(t.scope, cooldowns)]
            if not ready:
                wake = min(_parse(_blocking(t.scope, cooldowns)["until"]) for t in workable)
                export()
                if not watch or (deadline and wake >= deadline):
                    summary.reason = f"everything left is cooling down; next retry {_local(wake)}"
                    break
                log(f"[{_local(now())}] all {len({t.scope for t in workable})} scope(s) cooling "
                    f"down; sleeping until {_local(wake)}")
                if status_path:
                    _write(status_path, status_report(conn, setup, now(), coverage, tasks, parked, capped))
                sleep(max(1.0, (wake - now()).total_seconds() + 1))
                continue

            t = _pick(ready, last_scope, last_kind)
            last_scope, last_kind[t.scope] = t.scope, t.kind
            spent[t.scope] += 1
            try:
                err = _collect(conn, t, new_run) if t.kind == "collect" else _judge(conn, t)
            except Exception as e:  # noqa: BLE001 - an SDK error the adapter missed is one failed request
                err = f"{type(e).__name__}: {e}"
            cap = cap_for(t.scope)
            if cap is not None and spent[t.scope] >= cap:
                capped.add(t.scope)

            if not err:
                summary.ok += 1
                unexported += 1
                conn.execute("DELETE FROM cooldowns WHERE scope IN (?, ?)",
                             (t.scope, t.scope.split("|", 1)[0] + "|*"))
                conn.commit()
                log(f"[{_local(now())}] ok      {_describe(t)}")
                if unexported >= EXPORT_EVERY:
                    export()
                continue

            summary.failed += 1
            kind, hint, per_model = classify(err)
            short = re.sub(r"\s+", " ", err)[:120]
            if kind == "fatal":
                parked[t.scope] = err
                _bench(conn, t.scope, "fatal", None, err, now())
                log(f"[{_local(now())}] PARKED  {_describe(t)} -- {short}")
            elif kind == "bad_output":
                attempts[t.key] += 1
                log(f"[{_local(now())}] bad     {_describe(t)} -- {short}")
            else:
                if kind == "transient":
                    attempts[t.key] += 1
                scope = t.scope if per_model else t.scope.split("|", 1)[0] + "|*"
                until = _bench(conn, scope, kind, hint, err, now())
                log(f"[{_local(now())}] {kind:<7} {_describe(t)} -> {scope} rests until "
                    f"{_local(until)} -- {short}")
    except KeyboardInterrupt:
        summary.reason = "interrupted"
    finally:
        export()
        tasks, coverage = gaps(conn, setup, now())
        if dry_run:
            summary.reason = "dry run: no requests made"
        summary.status = status_report(conn, setup, now(), coverage, tasks, parked, capped)
        if status_path and not dry_run:
            _write(status_path, summary.status + f"\nstopped: {summary.reason}\n")
    return summary


def _write(path: str, text: str) -> None:
    with open(path, "w") as f:
        f.write(text)
