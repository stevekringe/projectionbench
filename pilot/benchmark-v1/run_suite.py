"""Run the fixed ProjectionBench suite from the repository root."""

import argparse
import json
from pathlib import Path

from collect import collect_study
from projectionbench.scenarios import load_all

SUBJECTS = {
    "gemini:gemini-3.1-flash-lite": ("Gemini 3.1 Flash-Lite", "Google API"),
    "cloudflare:@cf/qwen/qwen3.8-27b": ("Qwen 3.8 27B", "Cloudflare Workers AI"),
    "cloudflare:@cf/meta/llama-3.3-70b-instruct-fp8-fast": ("Llama 3.3 70B", "Cloudflare Workers AI"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("Output must be a new file in an existing directory")

    study = collect_study(
        SUBJECTS, load_all("pilot/benchmark-v1/suite/*.yaml"), 1, cloudflare_workers=3
    )
    args.output.write_text(json.dumps(study, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
