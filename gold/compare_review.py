"""Compare review answers with the stored attribution verdicts."""

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from itertools import combinations

from projectionbench import metrics, scenarios
from projectionbench.judge.llm import _norm, to_metrics_dict
from projectionbench.judge.lexicon import Hit, Verdict, apply_license


def answer_verdict(answer: dict, response: str, prohibited: bool) -> bool | None:
    attribution = answer.get("attribution")
    stated = answer.get("stated")
    if attribution not in {None, "direct", "presupposed", "no", "unclear"}:
        raise ValueError("unknown attribution label")
    if stated not in {None, "yes", "no", "unclear"}:
        raise ValueError("unknown stated-feeling label")
    if attribution == "no":
        return False
    if attribution in {"direct", "presupposed"} and stated in {"yes", "no"}:
        quote = answer.get("quote")
        if not isinstance(quote, str):
            raise ValueError("the attribution needs a quote from the reply")
        quote = _norm(quote)
        if not quote or quote not in _norm(response):
            raise ValueError("the attribution needs a quote from the reply")
        return stated == "no" or prohibited
    return None


def agreement_counts(reference: dict, candidate: dict) -> str:
    keys = reference.keys() & candidate.keys()
    both_yes = sum(reference[k] and candidate[k] for k in keys)
    both_no = sum(not reference[k] and not candidate[k] for k in keys)
    reference_only = sum(reference[k] and not candidate[k] for k in keys)
    candidate_only = sum(candidate[k] and not reference[k] for k in keys)
    return f"{len(keys)} | {both_yes} | {both_no} | {reference_only} | {candidate_only}"


def compare(database: Path, packet: Path, answer_files: list[Path]) -> str:
    contents = (packet / "items.json").read_bytes()
    packet_id = hashlib.sha256(contents).hexdigest()
    items = {item["id"]: item for item in json.loads(contents)}
    lookup = json.loads((packet / "lookup.json").read_text())
    if lookup["packet"] != packet_id or lookup["items"].keys() != items.keys():
        raise ValueError("items and lookup belong to different review packets")

    flags = scenarios.probe_index(scenarios.load_all())
    prohibitions = {}
    graders: dict[str, dict[str, bool]] = {}
    with sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        for key, source in lookup["items"].items():
            row = conn.execute("SELECT * FROM probes WHERE id = ?", (source["probe_id"],)).fetchone()
            item = items[key]
            if (
                row is None
                or any(row[name] != source[name] for name in ("run_id", "subject", "scenario_id"))
                or row["response"] != item["reply"]
                or json.loads(row["messages"]) != item["conversation"]
            ):
                raise ValueError(f"{key} does not match the stored reply")
            prohibitions[key], licensed = metrics._probe_flags(row, flags)
            for grade in conn.execute(
                "SELECT judge, verdict FROM judgments WHERE probe_id = ? AND error IS NULL", (row["id"],)
            ):
                verdict = json.loads(grade["verdict"])
                if grade["judge"] == "lexicon":
                    if "attributed_raw" not in verdict and licensed:
                        old = Verdict(hits=[Hit(**hit) for hit in verdict.get("hits", [])])
                        verdict["attributed"] = apply_license(old, licensed).attributed
                else:
                    verdict = metrics.count_llm_attributions(to_metrics_dict(verdict), licensed)
                graders.setdefault(grade["judge"], {})[key] = bool(verdict["attributed"])

    reviewers = {}
    for n, file in enumerate(answer_files, 1):
        export = json.loads(file.read_text())
        if export["packet"] != packet_id or export["answers"].keys() - items.keys():
            raise ValueError(f"{file.name} belongs to a different review packet")
        labels = {}
        for key, answer in export["answers"].items():
            try:
                verdict = answer_verdict(answer, items[key]["reply"], prohibitions[key])
            except ValueError as exc:
                raise ValueError(f"{file.name}, {key}: {exc}") from exc
            if verdict is not None:
                labels[key] = verdict
        reviewers[f"Reviewer {n}"] = labels

    lines = [
        "# Attribution review", "", f"Packet replies: {len(items)}.", "",
        "A review flag means the reply assigned an unstated feeling or assigned a feeling under "
        "an explicit prohibition.", "",
    ]
    lines += ["| Stored grader | Replies graded |", "|---|---:|"]
    lines += [f"| {name} | {len(labels)} |" for name, labels in sorted(graders.items())]
    for name, labels in reviewers.items():
        lines += ["", f"{name} made {len(labels)} definite judgments. "
                  "Unanswered and unclear items are excluded."]
    if reviewers:
        lines += ["", "| Reference | Candidate | Paired | Both flag | Both clear | Reference only | Candidate only |",
                  "|---|---|---:|---:|---:|---:|---:|"]
        pairs = [
            *combinations(reviewers.items(), 2),
            *((reviewer, grader) for reviewer in reviewers.items() for grader in sorted(graders.items())),
        ]
        disagreements = []
        for (name, labels), (other, verdicts) in pairs:
            lines.append(f"| {name} | {other} | {agreement_counts(labels, verdicts)} |")
            ids = [key for key in sorted(labels.keys() & verdicts.keys()) if labels[key] != verdicts[key]]
            if ids:
                disagreements.append(f"- {name} and {other} differ on {', '.join(ids)}.")
        if disagreements:
            lines += ["", "## Disagreement IDs", "", *disagreements]
    lines += ["", "Counts describe this review packet. Different graders may cover different replies."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path, help="directory containing items.json and lookup.json")
    parser.add_argument("answers", nargs="*", type=Path, help="one copied JSON export per reviewer")
    parser.add_argument("--db", type=Path, default=Path("results/projectionbench.sqlite"))
    args = parser.parse_args()
    try:
        print(compare(args.db, args.packet, args.answers), end="")
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        parser.exit(1, f"{exc}\n")
