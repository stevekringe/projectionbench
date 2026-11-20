"""Review the matched factual correction replies with deployment names hidden."""

import argparse
import json
from pathlib import Path

from audit_index import AUDIT_INSTRUCTIONS, grade
from review import blind_items, validate

GRADER = "cloudflare:@cf/openai/gpt-oss-120b"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("blind")
    commands.add_parser("judge")
    publish = commands.add_parser("publish")
    publish.add_argument("reference", type=Path)
    publish.add_argument("second", type=Path)
    args = parser.parse_args()

    study = json.loads(args.study.read_text())
    items = blind_items(study)
    if args.command == "blind":
        output = {key: conversation for key, (_, conversation) in items.items()}
    elif args.command == "judge":
        queued = [{"probeId": key, "conversation": conversation}
                  for key, (_, conversation) in items.items()]
        output = dict(grade(queued, GRADER, 2200, AUDIT_INSTRUCTIONS))
    else:
        reference = json.loads(args.reference.read_text())
        second = json.loads(args.second.read_text())
        if reference.keys() != items.keys() or second.keys() != items.keys():
            raise ValueError("Both reviews must cover the same blinded reply IDs")
        for trial in study["trials"]:
            trial["reference"] = None
            trial["secondReview"] = None
        for key, (trial, conversation) in items.items():
            trial["reference"] = validate(reference[key], conversation["reply"])
            trial["secondReview"] = (second[key] if "error" in second[key]
                                     else validate(second[key], conversation["reply"]))
        study["referenceGrader"] = "Codex"
        study["secondGrader"] = "GPT-OSS 120B"
        output = study
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
