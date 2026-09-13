"""`fill`: works toward a plan across invocations, backs off per quota scope,
continues interrupted conversations, and never re-does valid work."""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from projectionbench import fill, store
from projectionbench.adapters.base import MockAdapter, Reply
from projectionbench.judge.llm import LLMVerdict
from projectionbench.scenarios import load_all

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
SCEN = load_all(os.path.join(ROOT, "scenarios", "*.yaml"))
B07 = next(s for s in SCEN if s.id.startswith("b07"))
B09 = next(s for s in SCEN if s.id.startswith("b09"))

GEMINI_DAILY = (
    "ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your "
    "current quota ... limit: 20, model: gemini-3.8-flash\\nPlease retry in 47.86s.', 'details': "
    "[{'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}, {'retryDelay': '47s'}]}}"
)


class Scripted(MockAdapter):
    """A mock subject whose Nth call (1-based) returns a scripted error."""

    def __init__(self, model, errors=None, env="MOCK_KEY"):
        super().__init__(model)
        self.errors = errors or {}
        self.api_key_env = env
        self.calls = 0
        self.seen: list[list[dict]] = []

    def complete(self, messages, system=None):
        self.calls += 1
        err = self.errors.get(self.calls) or self.errors.get("*")
        if err:
            return Reply(text="", error=err)
        self.seen.append(messages)
        return Reply(text=f"reply {self.calls} from {self.model}", raw={})


class FakeJudge:
    key_env = "JUDGE_KEY"
    model = "fake"
    judge_id = "llm:fake:v0"

    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def judge(self, messages, response):
        self.calls += 1
        if self.error:
            return None, self.error
        return LLMVerdict(attributions=[], conduct_claims=[], user_expressed_affect=[],
                          fault_admission="none", corrected_the_error=False), None


class Clock:
    def __init__(self):
        self.t = datetime.now(timezone.utc)

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.slept = getattr(self, "slept", []) + [seconds]
        self.t += timedelta(seconds=seconds)


def _setup(subjects, judges=(), samples=1, collect=(B07,), caps=None):
    return fill.Setup(
        collect=list(collect), samples=samples, subjects=list(subjects),
        judge_scenarios=[s.id for s in collect] if judges else [], judges=list(judges),
        scenarios_by_id={s.id: s for s in SCEN}, caps=caps or {},
    )


def _run(conn, setup, clock, **kw):
    return fill.fill(conn, setup, now=clock.now, sleep=clock.sleep, log=lambda m: None, **kw)


def _convos(conn, subject, scenario_id):
    rows = conn.execute(
        "SELECT run_id, sample_idx, COUNT(*) n FROM probes WHERE subject=? AND scenario_id=? "
        "AND error IS NULL GROUP BY run_id, sample_idx ORDER BY sample_idx",
        (subject, scenario_id),
    ).fetchall()
    return [(r["sample_idx"], r["n"]) for r in rows]


@pytest.fixture
def conn(tmp_path):
    return store.connect(str(tmp_path / "t.sqlite"))


# --- classification against real stored errors ------------------------------------

@pytest.mark.parametrize("error,kind,per_model", [
    (GEMINI_DAILY, "daily", True),
    ("RateLimitError: Error code: 429 - {'error': {'message': 'Rate limit exceeded: "
     "free-models-per-day'}}", "daily", False),
    ("RateLimitError: Error code: 429 - {'metadata': {'raw': 'google/gemma-4-31b-it:free is "
     "temporarily rate-limited upstream. Please retry shortly'}}", "rate", True),
    ("ServerError: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'high demand'}}", "unavailable", True),
    ("TimeoutError: The read operation timed out", "transient", True),
    ("pabot subprocess timed out", "transient", True),
    ("ClientError: 401 UNAUTHENTICATED. Request had invalid authentication credentials.", "fatal", True),
    ("ClientError: 404 NOT_FOUND. This model models/gemini-2.5-flash-lite is no longer available",
     "fatal", True),
    ("judge output failed schema validation: 1 validation error, input_value=404", "bad_output", True),
])
def test_classify_real_errors(error, kind, per_model):
    got_kind, _, got_per_model = fill.classify(error)
    assert (got_kind, got_per_model) == (kind, per_model)


def test_retry_hint_is_used_once_then_backoff_takes_over():
    _, hint, _ = fill.classify("429 Too Many Requests. Please retry in 7s.")
    assert hint == 7
    assert fill.cooldown_seconds("rate", 1, hint) == 9
    assert fill.cooldown_seconds("rate", 2, hint) == 120
    assert fill.cooldown_seconds("daily", 10, None) == 6 * 3600


def test_load_env_file_never_overrides_and_skips_blanks(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("A_KEY=abc   # comment\nB_KEY=      # unset\nC_KEY=keep\n# X=1\n")
    monkeypatch.setenv("C_KEY", "already")
    monkeypatch.delenv("A_KEY", raising=False)
    monkeypatch.delenv("B_KEY", raising=False)
    assert fill.load_env_file(str(p)) == ["A_KEY"]
    assert os.environ["A_KEY"] == "abc" and os.environ["C_KEY"] == "already"
    assert "B_KEY" not in os.environ


# --- the loop ----------------------------------------------------------------------------

def test_reaches_target_with_unique_samples_and_stops(conn):
    a, b = Scripted("clean"), Scripted("emotive", env="OTHER_KEY")
    judge = FakeJudge()
    setup = _setup([a, b], judges=[judge], samples=2, collect=(B07, B09))
    s = _run(conn, setup, Clock())
    assert s.reason == "nothing left to do"
    n = len(B07.probes)
    for subj in (a.subject_id, b.subject_id):
        assert _convos(conn, subj, B07.id) == [(0, n), (1, n)]
        assert _convos(conn, subj, B09.id) == [(0, len(B09.probes)), (1, len(B09.probes))]
    unjudged = conn.execute(
        "SELECT COUNT(*) FROM probes p WHERE NOT EXISTS (SELECT 1 FROM judgments j "
        "WHERE j.probe_id = p.id AND j.judge = 'llm:fake:v0')").fetchone()[0]
    assert unjudged == 0

    # A second invocation finds nothing missing and makes no requests.
    calls = (a.calls, b.calls, judge.calls)
    assert _run(conn, setup, Clock()).ok == 0
    assert (a.calls, b.calls, judge.calls) == calls


def test_interrupted_conversation_continues_where_it_stopped(conn):
    flaky = Scripted("clean", errors={3: "ServerError: 503 UNAVAILABLE"})
    clock = Clock()
    s = _run(conn, _setup([flaky]), clock)
    assert s.reason.startswith("everything left is cooling down")
    assert _convos(conn, flaky.subject_id, B07.id) == [(0, 2)]

    clock.t += timedelta(minutes=5)
    _run(conn, _setup([flaky]), clock)
    assert _convos(conn, flaky.subject_id, B07.id) == [(0, len(B07.probes))]
    # Same conversation, not a second one, and the model saw its own stored
    # replies as history on the continued turn.
    assert conn.execute("SELECT COUNT(DISTINCT run_id) FROM probes").fetchone()[0] == 1
    continued = flaky.seen[2]
    assert [m["content"] for m in continued if m["role"] == "assistant" and m["content"].startswith("reply")] \
        == ["reply 1 from clean", "reply 2 from clean"]


def test_daily_quota_benches_one_model_while_others_proceed(conn):
    gem = Scripted("gemini-3.8-flash", errors={"*": GEMINI_DAILY}, env="GEMINI_API_KEY")
    other = Scripted("clean")
    clock = Clock()
    _run(conn, _setup([gem, other]), clock)
    assert gem.calls == 1
    assert _convos(conn, other.subject_id, B07.id) == [(0, len(B07.probes))]
    row = conn.execute("SELECT * FROM cooldowns").fetchone()
    assert (row["scope"], row["kind"]) == ("GEMINI_API_KEY|gemini-3.8-flash", "daily")

    # The cooldown is in the database, so a later invocation respects it...
    clock.t += timedelta(minutes=30)
    _run(conn, _setup([gem, other]), clock)
    assert gem.calls == 1
    # ...and tries again once it has passed.
    clock.t += timedelta(hours=1)
    _run(conn, _setup([gem, other]), clock)
    assert gem.calls == 2


def test_fatal_error_parks_the_subject_without_looping(conn):
    gone = Scripted("gone", errors={"*": "ClientError: 404 NOT_FOUND. model is no longer available"})
    other = Scripted("clean")
    s = _run(conn, _setup([gone, other]), Clock(), watch=True)
    assert gone.calls == 1
    assert "parked" in s.reason
    assert "parked this session" in s.status


def test_watch_sleeps_through_a_rate_limit_and_finishes(conn):
    slow = Scripted("clean", errors={1: "RateLimitError: Error code: 429 - Please retry in 5s."})
    clock = Clock()
    s = _run(conn, _setup([slow]), clock, watch=True)
    assert s.reason == "nothing left to do"
    assert clock.slept and 5 <= clock.slept[0] <= 10
    assert _convos(conn, slow.subject_id, B07.id) == [(0, len(B07.probes))]


def test_overloaded_provider_never_exhausts_the_task(conn):
    """A 503 says the provider is busy, not that the task is broken. Found on
    the first real run: gemini-3.7/3.8-flash answered 'high demand' three times
    at 4am and, when 503s counted as task failures, dropped out for the night."""
    busy = Scripted("clean", errors={i: "ServerError: 503 UNAVAILABLE. high demand" for i in range(1, 7)})
    clock = Clock()
    s = _run(conn, _setup([busy]), clock, watch=True)
    assert s.reason == "nothing left to do"
    assert busy.calls == 6 + len(B07.probes)
    assert max(clock.slept) > fill.BACKOFF["transient"][1] / 2


def test_deadline_stops_a_watch(conn):
    stuck = Scripted("clean", errors={"*": GEMINI_DAILY.replace("PerModel", "")})
    clock = Clock()
    s = _run(conn, _setup([stuck]), clock, watch=True, deadline=clock.t + timedelta(minutes=30))
    assert stuck.calls == 1
    assert s.reason.startswith("everything left is cooling down")


def test_cap_limits_requests_per_invocation(conn):
    capped = Scripted("gemini-x", env="GEMINI_API_KEY")
    s = _run(conn, _setup([capped], samples=3, caps={"GEMINI_API_KEY": 4}), Clock())
    assert capped.calls == 4
    assert "capped" in s.reason


def test_rewording_a_scenario_creates_new_work_and_keeps_old_rows(conn):
    subj = Scripted("clean")
    _run(conn, _setup([subj]), Clock())
    before = conn.execute("SELECT COUNT(*) FROM probes").fetchone()[0]

    import copy
    reworded = copy.deepcopy(B07)
    reworded.turns[0].content += " (reworded)"
    _run(conn, _setup([subj], collect=(reworded,)), Clock())
    assert conn.execute("SELECT COUNT(*) FROM probes").fetchone()[0] == before + len(B07.probes)
    hashes = {r[0] for r in conn.execute("SELECT DISTINCT scenario_hash FROM probes")}
    assert hashes == {B07.content_hash, reworded.content_hash}


def test_bad_judge_output_is_recorded_and_not_retried_forever(conn):
    subj = Scripted("clean")
    judge = FakeJudge(error="judge output failed schema validation: missing field")
    s = _run(conn, _setup([subj], judges=[judge]), Clock(), watch=True)
    assert judge.calls == len(B07.probes) * fill.MAX_TASK_ATTEMPTS
    assert "failed repeatedly" in s.reason
    errs = conn.execute("SELECT COUNT(*) FROM judgments WHERE judge='llm:fake:v0' AND error IS NOT NULL")
    assert errs.fetchone()[0] == len(B07.probes)


def test_stale_partial_conversation_is_not_continued(conn):
    subj = Scripted("clean", errors={3: "ServerError: 503 UNAVAILABLE"})
    clock = Clock()
    _run(conn, _setup([subj]), clock)
    # Rename the run too: run ids are second-resolution, and the next
    # invocation's run could otherwise reuse (and refresh) this one.
    old = (clock.t - fill.RESUME_WINDOW - timedelta(hours=1)).isoformat()
    conn.execute("UPDATE runs SET run_id = 'old', started_at = ?", (old,))
    conn.execute("UPDATE probes SET run_id = 'old'")
    conn.commit()
    clock.t += timedelta(minutes=5)
    _run(conn, _setup([subj]), clock)
    assert _convos(conn, subj.subject_id, B07.id) == [(0, 2), (1, len(B07.probes))]


def test_dry_run_makes_no_requests(conn):
    subj, judge = Scripted("clean"), FakeJudge()
    s = _run(conn, _setup([subj], judges=[judge]), Clock(), dry_run=True)
    assert subj.calls == 0 and judge.calls == 0
    assert "still to do: 1 conversation step(s) queued" in s.status


def test_next_request_matches_runner_history():
    from projectionbench import runner

    mock = MockAdapter("clean")
    results = runner.run_unit(mock, B07, 0)
    replies = [r.response for r in results]
    for k, r in enumerate(results):
        _, _, history = fill.next_request(B07, replies[:k])
        assert history == r.messages
