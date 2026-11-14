"""Build a blind review packet and a separate lookup key from stored replies."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import sqlite3

from projectionbench.scenarios import load_all


# Replies inspected in the targeted and stratified reviews documented in
# leaderboard-audit-2026-11-14.md.
PREVIOUSLY_REVIEWED = {
    386, 442, 445, 446, 449, 450, 453, 456, 463, 467, 496, 501, 558, 559,
    568, 580, 582, 584, 586, 588, 591, 601, 604, 605,
}


def write_packet(database: Path, output: Path) -> None:
    scenarios = {scenario.id: scenario.content_hash for scenario in load_all()}
    groups = defaultdict(list)
    with sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM probes
            WHERE error IS NULL AND trim(response) <> '' AND subject NOT LIKE 'pabot:%'
                AND ((scenario_id GLOB 'r0[5-8]*' AND probe_ordinal > 0
                        AND planted_realized = 'yes')
                    OR scenario_id GLOB 'b0[789]*'
                    OR scenario_id = 'g03_cold_open_expressed')
            ORDER BY id
        """)
        for row in rows:
            scenario_id = row["scenario_id"]
            if row["id"] in PREVIOUSLY_REVIEWED or scenarios.get(scenario_id) != row["scenario_hash"]:
                continue
            groups[scenario_id[:3]].append(row)

    rng = random.Random(20261114)
    picked = [
        row
        for group, rows in sorted(groups.items())
        for row in rng.sample(rows, min(8 if group.startswith("r") else 6, len(rows)))
    ]
    rng.shuffle(picked)
    packet = []
    lookup = {}
    for number, row in enumerate(picked, 1):
        label_id = f"q{number:02d}"
        packet.append({
            "id": label_id,
            "conversation": json.loads(row["messages"]),
            "reply": row["response"],
        })
        lookup[label_id] = {
            "probe_id": row["id"],
            "run_id": row["run_id"],
            "scenario_id": row["scenario_id"],
            "subject": row["subject"],
        }
    output.mkdir(parents=True, exist_ok=True)
    for name, data in (("items", packet), ("lookup", lookup)):
        (output / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Prepared {len(packet)} replies for blind review.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("results/projectionbench.sqlite"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_packet(args.db, args.output)
