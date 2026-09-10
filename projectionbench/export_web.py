"""Export the sqlite db to one JSON file for web/'s dashboard.

Includes both the aggregate scores (via metrics.score, one per judge found
in the db) and, per probe, the raw verdict detail -- lexicon hits/spans,
LLM judge quotes/attributions -- so the dashboard can show the actual
evidence behind a score, not just the number.
"""

from __future__ import annotations

import json
import sys

from projectionbench import metrics, scenarios, store


def _judges_in_db(conn) -> list[str]:
    return [r["judge"] for r in conn.execute("SELECT DISTINCT judge FROM judgments").fetchall()]


def _planted_flags(scen: scenarios.Scenario | None, messages: list[dict]) -> list[bool]:
    """Tag scripted (planted) assistant history by content.

    Every assistant turn in a scenario script is fabricated history
    (enforced by scenarios._validate), so an assistant history message is
    planted iff it byte-matches a scripted assistant turn. The model's own
    earlier replies in multi-turn runs never match verbatim. Matching by
    content rather than position keeps this working for runs stored before
    a scenario's user-turn wording was revised.
    """
    planted_texts = (
        {t.content.strip() for t in scen.turns if t.role == "assistant"} if scen else set()
    )
    return [
        m.get("role") == "assistant" and m.get("content", "").strip() in planted_texts
        for m in messages
    ]


def _tag_messages(
    by_scenario: dict[str, scenarios.Scenario], r
) -> list[dict]:
    """History messages with a `planted` flag on scripted setup turns."""
    messages = json.loads(r["messages"])
    flags = _planted_flags(by_scenario.get(r["scenario_id"]), messages)
    return [
        {"role": m.get("role"), "content": m.get("content"), "planted": f}
        for m, f in zip(messages, flags)
    ]


def export(db_path: str, out_path: str) -> None:
    conn = store.connect(db_path)
    judges = _judges_in_db(conn)
    by_scenario = {s.id: s for s in scenarios.load_all()}

    scores_by_judge = {}
    for judge in judges:
        probes = metrics.load(conn, None, judge=judge)
        if not probes:
            continue
        scores = metrics.score(probes, bootstrap=False, judge=judge)
        scores_by_judge[judge] = [
            {
                "subject": s.subject,
                "n_probes": s.n_probes,
                "index": round(s.index, 2),
                "rates": {k: (round(v, 4) if v is not None else None) for k, v in s.rates.items()},
                "counts": s.counts,
            }
            for s in scores
        ]

    probe_rows = conn.execute(
        """
        SELECT p.id, p.subject, p.scenario_id, p.category, p.sample_idx,
               p.probe_ordinal, p.user_affect, p.expect, p.tests,
               p.messages, p.response, p.error
        FROM probes p
        WHERE p.error IS NULL
        ORDER BY p.subject, p.scenario_id, p.sample_idx, p.probe_ordinal
        """
    ).fetchall()

    verdicts_by_probe: dict[int, dict] = {}
    for r in conn.execute("SELECT probe_id, judge, verdict, error FROM judgments").fetchall():
        verdicts_by_probe.setdefault(r["probe_id"], {})[r["judge"]] = {
            "verdict": json.loads(r["verdict"]) if r["verdict"] else None,
            "error": r["error"],
        }

    probes = [
        {
            "subject": r["subject"],
            "scenario_id": r["scenario_id"],
            "category": r["category"],
            "sample_idx": r["sample_idx"],
            "probe_ordinal": r["probe_ordinal"],
            "user_affect": r["user_affect"],
            "expect": r["expect"],
            "tests": r["tests"],
            "messages": _tag_messages(by_scenario, r),
            "response": r["response"],
            "judgments": verdicts_by_probe.get(r["id"], {}),
        }
        for r in probe_rows
    ]

    conn.close()

    out = {"judges": judges, "scores": scores_by_judge, "probes": probes}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {out_path}: {len(probes)} probes, judges={judges}", file=sys.stderr)


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "results/projectionbench.sqlite"
    out = sys.argv[2] if len(sys.argv) > 2 else "web/src/lib/data.json"
    export(db, out)
