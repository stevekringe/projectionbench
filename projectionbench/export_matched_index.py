"""Export the documented Projection Index on the same completed tests per model."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from projectionbench import metrics, scenarios
from projectionbench.export_web import SERVED_SCENARIOS
from projectionbench.judge.lexicon import score_probe

SAMPLES = 3


def make_example(row, title, excerpt):
    return {
        "probeId": row["id"],
        "title": title,
        "excerpt": excerpt,
        "history": json.loads(row["messages"]),
        "reply": row["response"],
    }


def export(db: Path, target: Path) -> None:
    scripts = {s.id: s for s in scenarios.load_all() if s.id in SERVED_SCENARIOS}
    if scripts.keys() != set(SERVED_SCENARIOS):
        raise ValueError("Every served scenario must have a local definition")
    with sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        runs = defaultdict(list)
        for row in conn.execute(
            """
            SELECT id, run_id, subject, scenario_id, sample_idx, probe_ordinal,
                   scenario_hash, messages, response
            FROM probes
            WHERE error IS NULL AND response != ''
            ORDER BY run_id, sample_idx, probe_ordinal
            """
        ):
            script = scripts.get(row["scenario_id"])
            if script and row["scenario_hash"] == script.content_hash:
                key = (row["subject"], script.id, row["run_id"], row["sample_idx"])
                runs[key].append(row)

    complete = defaultdict(list)
    for (subject, script_id, _, _), rows in runs.items():
        ordinals = [row["probe_ordinal"] for row in rows]
        if ordinals == list(range(len(scripts[script_id].probes))):
            complete[subject, script_id].append(rows)

    probes = []
    sources = defaultdict(list)
    examples = defaultdict(list)
    first_replies = {}
    index_eligible = set()
    attribution_scripts = {s.id for s in scripts.values() if any(
        turn.expect == "forbid" for _, turn in s.probes
    )}
    reviewed = json.loads(Path("gold/homepage-examples.json").read_text())
    for subject in sorted({key[0] for key in complete}):
        if subject.startswith(("pabot:", "mock:", "paste:")):
            continue
        available = {script for script in scripts if len(complete[subject, script]) >= SAMPLES}
        if not attribution_scripts <= available:
            continue
        if available == scripts.keys():
            index_eligible.add(subject)
        for script_id, script in scripts.items():
            if script_id not in available:
                continue
            for sample_idx, rows in enumerate(complete[subject, script_id][:SAMPLES]):
                for row in rows:
                    first_replies.setdefault(subject, row)
                    example = reviewed.get(str(row["id"]))
                    if example and example["excerpt"] in row["response"]:
                        examples[subject].append(make_example(row, example["title"], example["excerpt"]))
                    _, turn = script.probes[row["probe_ordinal"]]
                    verdict = score_probe(
                        row["response"], turn.user_affect, turn.expect,
                        turn.invites_self_disclosure, turn.licensed,
                    )
                    probes.append(metrics.Probe(
                        subject=subject,
                        scenario_id=script_id,
                        category=script.category,
                        sample_idx=sample_idx,
                        probe_ordinal=row["probe_ordinal"],
                        user_affect=turn.user_affect,
                        expect=turn.expect,
                        invites_self_disclosure=turn.invites_self_disclosure,
                        prohibited=turn.prohibited,
                        licensed=turn.licensed,
                        scenario_hash=script.content_hash,
                        v=verdict.to_dict(),
                    ))
                    sources[subject].append(row["id"])

    for subject, row in first_replies.items():
        if not examples[subject]:
            excerpt = row["response"].strip().split("\n\n", 1)[0]
            examples[subject].append(make_example(row, "Example from the benchmark", excerpt))

    results = metrics.score(probes, judge="lexicon")
    output = {
        "judge": "Lexicon cross-check",
        "samples": SAMPLES,
        "scenarios": list(scripts),
        "metrics": [
            {"key": key, "label": label, "weight": metrics.WEIGHTS.get(key)}
            for key, label in metrics.LABELS.items()
        ],
        "scores": [
            {
                "subject": s.subject,
                "index": round(s.index, 2) if s.subject in index_eligible else None,
                "interval": ([round(bound, 2) for bound in s.ci]
                             if s.subject in index_eligible else None),
                "counts": s.counts,
                "probes": s.n_probes,
                "sourceIds": sources[s.subject],
                "examples": examples[s.subject],
            }
            for s in results
        ],
    }
    target.write_text(json.dumps(output, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("results/projectionbench.sqlite"))
    parser.add_argument("--output", type=Path, default=Path("web/src/lib/matched-index.json"))
    args = parser.parse_args()
    export(args.db, args.output)


if __name__ == "__main__":
    main()
