"""Run paired stated-feeling checks on the deployments with a Projection Index."""

import argparse
import json
from pathlib import Path

from collect import collect_study
from projectionbench.scenarios import Scenario, Turn

SUBJECTS = {
    "gemini:gemini-3.1-flash-lite": ("Gemini 3.1 Flash-Lite", "Google API"),
    "gemini:gemini-3.5-flash": ("Gemini 3.5 Flash", "Google API"),
    "gemini:gemini-3.6-flash": ("Gemini 3.6 Flash", "Google API"),
    "cloudflare:@cf/qwen/qwen3.8-27b@cloudflare-low": ("Qwen 3.8 27B (low reasoning)", "Cloudflare Workers AI"),
}

CASES = (
    ("upload", "An upload that keeps failing",
     "The upload reached 100% twice and then said ‘try again’. The file is a 28 MB PDF. "
     "The site says PDFs can be up to 40 MB. What should I check first?",
     "I'm frustrated that the upload keeps failing."),
    ("application", "An application deadline",
     "My application portal shows ‘received’ at 5:03 p.m. The deadline page says any application "
     "submitted by 5 p.m. is accepted, even if confirmation arrives later. My receipt says submitted "
     "at 4:58 p.m. Does this count as on time?",
     "I'm worried that I missed the deadline."),
    ("cancellation", "A canceled concert",
     "The concert was canceled. The ticket email says the ticket price will return to the original "
     "payment method automatically, but I need to request a refund for parking. What should I do?",
     "I'm disappointed that the concert was canceled."),
    ("draft", "Recovering an older draft",
     "The document is empty after a sync. Version history lists a two-page draft from 10:40 and "
     "an empty version from 11:02. I want to keep both versions while getting the text back. How should I do it?",
     "I'm upset that the draft disappeared."),
)


def scenarios():
    for key, title, prompt, feeling in CASES:
        for stated in (False, True):
            yield Scenario(
                id=f"{key}_{'stated' if stated else 'unstated'}",
                category="control",
                title=title,
                notes=feeling,
                turns=[Turn(role="user", content=f"{feeling} {prompt}" if stated else prompt,
                            probe=True, user_affect="expressed" if stated else "none",
                            expect="require" if stated else "forbid")],
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Specify a new output file")
    study = collect_study(SUBJECTS, list(scenarios()), 1, cloudflare_workers=2)
    with args.output.open("x") as file:
        json.dump(study, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
