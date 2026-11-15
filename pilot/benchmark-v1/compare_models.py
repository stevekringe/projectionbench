"""Run the shared multi-model comparison prompts."""

import argparse
import json
from pathlib import Path

from collect import collect_study
from projectionbench.scenarios import load_scenario

SUBJECTS = {
    "gemini:gemini-3.1-flash-lite": ("Gemini 3.1 Flash-Lite", "Google API"),
    "gemini:gemini-3.5-flash": ("Gemini 3.5 Flash", "Google API"),
    "gemini:gemini-3.6-flash": ("Gemini 3.6 Flash", "Google API"),
    "gemini:gemini-3.7-flash": ("Gemini 3.7 Flash", "Google API"),
    "gemini:gemini-3.8-flash": ("Gemini 3.8 Flash", "Google API"),
    "cloudflare:@cf/qwen/qwen3.8-27b": ("Qwen 3.8 27B", "Cloudflare Workers AI"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("Output must be a new file in an existing directory")

    schedule = load_scenario("pilot/benchmark-v1/b01_schedule.yaml")
    film = load_scenario("pilot/p13_film_clarification.yaml")
    complaint = load_scenario("scenarios/b09_cold_open_stupid.yaml")
    complaint.turns = complaint.turns[:1]
    complaint.title = "Questioning a past feeling label"
    complaint.notes = "The user quotes the earlier label while asking why it was introduced."
    study = collect_study(SUBJECTS, [schedule, film, complaint], 2)
    with args.output.open("x") as file:
        json.dump(study, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
