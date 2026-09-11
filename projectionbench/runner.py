"""Execute scenarios against subjects.

One unit of work = (subject, scenario, sample). Units run concurrently; the
turns inside a unit are strictly sequential, because a persistence probe only
means anything if turn 4 is reacting to what the model actually said at turn 2.
"""

from __future__ import annotations

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from projectionbench import store, transcripts
from projectionbench.adapters import Adapter
from projectionbench.judge import lexicon
from projectionbench.scenarios import Scenario

# A subject whose units keep failing is not going to recover mid-run -- it is
# throttled, down, or misconfigured. Letting every remaining unit burn a full
# request timeout each is how a free-tier run turns into half an hour of
# silence, so after this many CONSECUTIVE failed units the subject's remaining
# units are skipped outright. A clean unit resets the count, so one transient
# 429 never kills a subject. With workers=1 (the free-tier mode) units run in
# order and this behaves as a strict ordered rotation.
SKIP_AFTER_CONSECUTIVE_FAILURES = 2


@dataclass
class ProbeResult:
    subject: str
    scenario_id: str
    category: str
    sample_idx: int
    turn_index: int
    probe_ordinal: int
    user_affect: str
    expect: str
    invites_self_disclosure: bool
    tests: str
    system: str | None
    messages: list[dict]
    response: str
    raw: dict
    error: str | None


def run_unit(adapter: Adapter, scenario: Scenario, sample_idx: int) -> list[ProbeResult]:
    history: list[dict] = []
    results: list[ProbeResult] = []
    ordinal = 0

    for i, turn in enumerate(scenario.turns):
        if turn.role == "assistant":
            # Planted history. Always followed by a user turn, so this is never
            # a trailing-assistant prefill.
            history.append({"role": "assistant", "content": turn.content})
            continue

        history.append({"role": "user", "content": turn.content})
        if not turn.probe:
            continue

        reply = adapter.complete(list(history), system=scenario.system)
        results.append(
            ProbeResult(
                subject=adapter.subject_id,
                scenario_id=scenario.id,
                category=scenario.category,
                sample_idx=sample_idx,
                turn_index=i,
                probe_ordinal=ordinal,
                user_affect=turn.user_affect,
                expect=turn.expect,
                invites_self_disclosure=turn.invites_self_disclosure,
                tests=turn.tests,
                system=scenario.system,
                messages=list(history),
                response=reply.text,
                raw=reply.raw,
                error=reply.error,
            )
        )
        ordinal += 1

        if reply.error:
            break  # the rest of this conversation would be meaningless
        history.append({"role": "assistant", "content": reply.text})

    return results


def run(
    adapters: list[Adapter],
    scenarios: list[Scenario],
    samples: int,
    db: str = "results/projectionbench.sqlite",
    workers: int = 8,
) -> str:
    conn = store.connect(db)
    run_id = store.new_run(
        conn,
        {
            "subjects": [a.subject_id for a in adapters],
            "scenarios": [s.id for s in scenarios],
            "samples": samples,
        },
    )

    units = [
        (a, s, n) for a in adapters for s in scenarios for n in range(samples)
    ]
    # Request count per subject, not just conversation count -- free tiers meter
    # requests, and you need to know the number BEFORE spending the quota.
    per_subject = sum(len(s.probes) for s in scenarios) * samples
    print(
        f"run {run_id}: {len(units)} conversations, "
        f"{per_subject} requests per subject ({per_subject * len(adapters)} total)\n"
        f"  {len(adapters)} subjects x {len(scenarios)} scenarios x {samples} samples",
        file=sys.stderr,
    )

    done = 0
    skipped: dict[str, str] = {}  # subject -> reason, for the end-of-run report
    dead: dict[str, int] = {}  # subject -> consecutive failed units
    lock = threading.Lock()

    def guarded(a: Adapter, s: Scenario, n: int) -> list[ProbeResult] | None:
        """None means skipped: the subject already failed out of this run."""
        with lock:
            if dead.get(a.subject_id, 0) >= SKIP_AFTER_CONSECUTIVE_FAILURES:
                return None
        try:
            results = run_unit(a, s, n)
        except Exception:
            with lock:
                dead[a.subject_id] = dead.get(a.subject_id, 0) + 1
            raise
        with lock:
            if any(r.error for r in results):
                dead[a.subject_id] = dead.get(a.subject_id, 0) + 1
            else:
                dead[a.subject_id] = 0
        return results

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(guarded, a, s, n): (a, s, n) for a, s, n in units}
        for fut in as_completed(futures):
            a, s, n = futures[fut]
            try:
                results = fut.result()
            except Exception as e:  # noqa: BLE001 - one bad unit must not kill the run
                print(f"  !! {a.subject_id} / {s.id} #{n}: {e}", file=sys.stderr)
                continue
            if results is None:
                with lock:
                    skipped.setdefault(
                        a.subject_id,
                        f"skipped after {SKIP_AFTER_CONSECUTIVE_FAILURES} "
                        "consecutive failed units (throttled, down, or misconfigured)",
                    )
                done += 1
                print(f"\r  {done}/{len(units)}", end="", file=sys.stderr, flush=True)
                continue

            # All DB writes happen on this thread; SQLite stays single-writer.
            for r in results:
                probe_id = store.insert_probe(
                    conn,
                    {
                        "run_id": run_id,
                        "subject": r.subject,
                        "scenario_id": r.scenario_id,
                        "category": r.category,
                        "sample_idx": r.sample_idx,
                        "turn_index": r.turn_index,
                        "probe_ordinal": r.probe_ordinal,
                        "user_affect": r.user_affect,
                        "expect": r.expect,
                        "invites_self_disclosure": int(r.invites_self_disclosure),
                        "tests": r.tests,
                        "system": r.system,
                        "messages": json.dumps(r.messages),
                        "response": r.response,
                        "raw": json.dumps(r.raw),
                        "error": r.error,
                    },
                )
                if not r.error:
                    v = lexicon.score_probe(r.response, r.user_affect, r.expect,
                                            r.invites_self_disclosure)
                    store.insert_judgment(conn, probe_id, "lexicon", v.to_dict())
            conn.commit()

            done += 1
            print(f"\r  {done}/{len(units)}", end="", file=sys.stderr, flush=True)

    print(file=sys.stderr)

    # A run that "completed" while every request 404'd is not a completed run.
    # Surface it here rather than letting it show up as missing data later.
    errs = conn.execute(
        "SELECT subject, COUNT(*) n, MIN(error) sample FROM probes "
        "WHERE run_id = ? AND error IS NOT NULL GROUP BY subject",
        (run_id,),
    ).fetchall()
    if errs:
        print("\nERRORS:", file=sys.stderr)
        for e in errs:
            total = conn.execute(
                "SELECT COUNT(*) c FROM probes WHERE run_id=? AND subject=?",
                (run_id, e["subject"]),
            ).fetchone()["c"]
            print(f"  {e['subject']}: {e['n']}/{total} probes failed", file=sys.stderr)
            print(f"    {e['sample'][:160]}", file=sys.stderr)

    # Subjects that failed out via the skip rule above: populated-vs-skipped
    # summary, so a throttled run reports what it got and what it didn't.
    if skipped:
        print("\nSKIPPED:", file=sys.stderr)
        for subject, reason in skipped.items():
            print(f"  {subject}: {reason}", file=sys.stderr)

    tpath = transcripts.write(conn, run_id)
    print(f"\ntranscripts: {tpath}", file=sys.stderr)

    conn.close()
    return run_id
