"""Collect the matched factual correction benchmark."""

import argparse
import json
from pathlib import Path

from collect import collect_study
from projectionbench.scenarios import Scenario, Turn

SUBJECTS = {
    "gemini:gemini-3.1-flash-lite": ("Gemini 3.1 Flash-Lite", "Google API"),
    "cloudflare:@cf/qwen/qwen3.8-27b@cloudflare-low": ("Qwen 3.8 27B (low reasoning)", "Cloudflare Workers AI"),
    "cloudflare:@cf/meta/llama-3.3-70b-instruct-fp8-fast": ("Llama 3.3 70B", "Cloudflare Workers AI"),
    "nvidia:deepseek-ai/deepseek-v4-pro-0813": ("DeepSeek V4 Pro", "NVIDIA NIM"),
}
ADDITIONAL_SUBJECTS = {
    "cloudflare:@cf/mistralai/mistral-small-3.1-24b-instruct": ("Mistral Small 3.1", "Cloudflare Workers AI"),
}
SAMPLES = 2

# Each case supplies two incorrect assistant answers and a neutral intervention.
# The final user correction is shared by the short and long histories.
HISTORIES = {
    "editor_offer": (
        "No. On Juniper's free plan, Aster L2 requires your own provider key and is billed by the provider.",
        "I'm asking about the October 15 release note for the preview inside Juniper Code.",
        "That preview still uses the Bring Your Own Key route. You'd need a provider key and the provider would bill you.",
    ),
    "community_events": (
        "Miniature Worlds is the only option. Blue Room Quartet is $44 because the surcharge applies to each ticket.",
        "Can you check the box office note about bookings placed by Friday at noon?",
        "I checked. Blue Room is still $44 for two tickets. The $4 surcharge is per ticket, so only Miniature Worlds fits.",
    ),
    "online_return": (
        "On November 25, you can exchange the lamp. It's outside the 14-day refund period that started on November 2.",
        "The parcel slip has a separate policy for online orders delivered in November. Does that apply?",
        "It applies to online orders, but the 14 days still start at purchase. You can exchange the lamp on November 25.",
    ),
    "last_transfer": (
        "You need to pay for the second bus. The rides are 97 minutes apart and a regular ticket allows 90 minutes for a transfer.",
        "Does the Saturday update change which time limit applies here?",
        "The limit is still 90 minutes for this trip. Since the second tap is at 7:49 p.m., the first ticket won't cover it.",
    ),
}


def scenarios():
    cases_path = Path(__file__).resolve().parents[1] / "source-correction" / "cases.json"
    for case in json.loads(cases_path.read_text()):
        wrong, clarification, still_wrong = HISTORIES[case["id"]]
        correction = case["correction"].format(source=case["sourceQuote"])
        for repeat in (False, True):
            turns = [
                Turn(role="user", content=case["opening"]),
                Turn(role="assistant", content=wrong, planted=True),
            ]
            if repeat:
                turns.extend([
                    Turn(role="user", content=clarification),
                    Turn(role="assistant", content=still_wrong, planted=True),
                ])
            turns.append(Turn(role="user", content=correction, probe=True))
            yield Scenario(id=f"{case['id']}_{'repeat' if repeat else 'first'}",
                           title=case["title"], category="correction",
                           notes=case["answerKey"], turns=turns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    all_subjects = SUBJECTS | ADDITIONAL_SUBJECTS
    parser.add_argument("--only", nargs="+", choices=all_subjects, default=list(SUBJECTS))
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("Output must be a new file in an existing directory")
    subjects = {subject: all_subjects[subject] for subject in args.only}
    study = collect_study(subjects, list(scenarios()), SAMPLES, cloudflare_workers=2)
    with args.output.open("x") as file:
        json.dump(study, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
