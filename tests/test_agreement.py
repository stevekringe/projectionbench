"""Judge agreement and default-judge selection."""

import os

from projectionbench import metrics, runner, store
from projectionbench.adapters import build
from projectionbench.scenarios import load_all

ROOT = os.path.dirname(os.path.dirname(__file__))


def _db(tmp_path):
    db = str(tmp_path / "t.sqlite")
    scen = [s for s in load_all(os.path.join(ROOT, "scenarios", "*.yaml"))
            if s.id.startswith(("a01", "b07"))]
    runner.run([build("mock:emotive"), build("mock:clean")], scen, samples=1, db=db, workers=1)
    return store.connect(db)


def _fake_llm(conn, judge, agree_with_lexicon: bool):
    rows = conn.execute(
        "SELECT p.id, j.verdict FROM probes p JOIN judgments j ON j.probe_id=p.id "
        "AND j.judge='lexicon'"
    ).fetchall()
    import json
    for r in rows:
        lex = json.loads(r["verdict"])["attributed"]
        say = lex if agree_with_lexicon else not lex
        store.insert_judgment(conn, r["id"], judge,
                              {"attributions": [{"quote": "x", "emotion": "anger"}] if say else [],
                               "conduct_claims": [], "user_expressed_affect": [],
                               "fault_admission": "none", "corrected_the_error": True})
    conn.commit()


def test_no_llm_judges_means_lexicon_only(tmp_path):
    conn = _db(tmp_path)
    assert metrics.llm_judges_in_db(conn) == []


def test_perfect_and_inverse_agreement(tmp_path):
    conn = _db(tmp_path)
    _fake_llm(conn, "llm:same:v1", True)
    _fake_llm(conn, "llm:opposite:v1", False)
    same = metrics.agreement(conn, "llm:same:v1", "lexicon")
    opp = metrics.agreement(conn, "llm:opposite:v1", "lexicon")
    assert same.n > 0 and same.kappa == 1.0 and same.a_only == same.b_only == 0
    assert opp.kappa is not None and opp.kappa < 0 and opp.both_yes == opp.both_no == 0
    # Most-judged first; both have the same count so the tie breaks on id.
    assert {j for j, _ in metrics.llm_judges_in_db(conn)} == {"llm:same:v1", "llm:opposite:v1"}


def test_errored_llm_judgments_do_not_count_toward_coverage(tmp_path):
    conn = _db(tmp_path)
    pid = conn.execute("SELECT id FROM probes LIMIT 1").fetchone()["id"]
    store.insert_judgment(conn, pid, "llm:broken:v1", {}, error="429")
    conn.commit()
    assert metrics.llm_judges_in_db(conn) == []
