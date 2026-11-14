"""Prepare blinded reviews and combine independently submitted labels."""

import argparse
import json
import random
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from projectionbench.adapters import build
from projectionbench.fill import load_env_file

LABELS = {"direct", "implied", "uncertain", "situation", "retraction", "stated", "clear"}
MISTRAL = "cloudflare:@cf/mistralai/mistral-small-3.1-24b-instruct"
RUBRIC = Path(__file__).with_name("rubric.txt")


def blind_items(study):
    scenarios = {scenario["id"]: scenario for scenario in study["scenarios"]}
    trials = [trial for trial in study["trials"] if trial["reply"] is not None]
    random.Random(2114).shuffle(trials)
    return {
        f"{index:02}": (
            trial,
            {
                "history": scenarios[trial["scenario"]]["messages"],
                "reply": trial["reply"],
            },
        )
        for index, trial in enumerate(trials, 1)
    }


def validate(verdict, reply):
    label, quote = verdict["label"], verdict["quote"]
    if label not in LABELS:
        raise ValueError(f"Unknown label {label!r}")
    if label == "clear":
        if quote is not None:
            raise ValueError("A clear verdict must have a null quote")
    elif not isinstance(quote, str) or not quote.strip() or quote not in reply:
        raise ValueError("Verdict quote is not a verbatim span in the reply")
    return {"label": label, "quote": quote}


def grade(item, judge, rubric):
    item_id, (_, conversation) = item
    response = judge.complete(
        [{"role": "user", "content": json.dumps(conversation, ensure_ascii=False)}],
        system=rubric,
    )
    if response.error:
        return item_id, {"error": response.error.split(":", 1)[0]}
    try:
        raw = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", response.text)
        verdict = validate(json.loads(raw), conversation["reply"])
    except (TypeError, KeyError, ValueError):
        return item_id, {"error": "Invalid label or quote"}
    return item_id, verdict


def grade_with_mistral(items):
    load_env_file()
    judge = build(MISTRAL, max_tokens=300)
    judge.request_timeout = 25
    rubric = RUBRIC.read_text()
    with ThreadPoolExecutor(max_workers=3) as pool:
        return dict(pool.map(lambda item: grade(item, judge, rubric), items.items()))


def attach_reviews(study, items, codex, mistral):
    if codex.keys() != items.keys() or mistral.keys() != items.keys():
        raise ValueError("Both files must have one decision per blind item")
    for item_id, (trial, conversation) in items.items():
        trial["codex"] = validate(codex[item_id], conversation["reply"])
        mistral_verdict = mistral[item_id]
        trial["mistral"] = (
            {"error": mistral_verdict["error"]}
            if "error" in mistral_verdict
            else validate(mistral_verdict, conversation["reply"])
        )
    return study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("blind")
    commands.add_parser("mistral")
    publish = commands.add_parser("publish")
    publish.add_argument("codex", type=Path)
    publish.add_argument("mistral", type=Path)
    args = parser.parse_args()

    study = json.loads(args.study.read_text())
    items = blind_items(study)
    if args.command == "blind":
        result = {item_id: conversation for item_id, (_, conversation) in items.items()}
    elif args.command == "mistral":
        result = grade_with_mistral(items)
    else:
        result = attach_reviews(
            study, items, json.loads(args.codex.read_text()), json.loads(args.mistral.read_text())
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
