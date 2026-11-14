"""Collect the fixed v1 prompts using the regular scenario runner."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from projectionbench.adapters import build
from projectionbench.fill import load_env_file
from projectionbench.runner import run_unit
from projectionbench.scenarios import load_all

SUBJECTS = {
    "gemini:gemini-3.1-flash-lite": ("Gemini 3.1 Flash-Lite", "Google API"),
    "cloudflare:@cf/qwen/qwen3.8-27b": ("Qwen 3.8 27B", "Cloudflare Workers AI"),
}
SAMPLES = 3
MAX_TOKENS = 4096


def incomplete_reason(result):
    if result.error:
        # Provider error bodies can contain account or credential details.
        return result.error.split(":", 1)[0]
    candidates = result.raw.get("candidates") or []
    choices = (result.raw.get("result") or {}).get("choices") or []
    if candidates and candidates[0].get("finish_reason") == "MAX_TOKENS":
        return "Output limit reached"
    if choices and choices[0].get("finish_reason") == "length":
        return "Output limit reached"
    return None if result.response.strip() else "Empty reply"


def collect_subject(spec, scenarios):
    adapter = build(spec, max_tokens=MAX_TOKENS)
    if adapter.name == "cloudflare":
        adapter.request_timeout = 30
    if adapter.name == "gemini":
        adapter.max_attempts = 1

    trials = []
    for scenario in scenarios:
        for index in range(SAMPLES):
            result = run_unit(adapter, scenario, index)[0]
            first_error = incomplete_reason(result)
            retry = first_error in {"URLError", "TimeoutError", "RemoteDisconnected"}
            if retry:
                result = run_unit(adapter, scenario, index)[0]
            error = incomplete_reason(result)
            trials.append({
                "id": f"{scenario.id}/{adapter.name}/{index + 1}",
                "scenario": scenario.id,
                "subject": spec,
                "sample": index + 1,
                "reply": None if error else result.response,
                "error": error,
                "retry": first_error if retry else None,
            })
            print(scenario.id, adapter.name, index + 1, error or "received", flush=True)
    return trials


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("Output must be a new file in an existing directory")

    load_env_file()
    folder = Path(__file__).resolve().parent
    scenarios = load_all(str(folder / "*.yaml"))
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with ThreadPoolExecutor(max_workers=len(SUBJECTS)) as pool:
        results = pool.map(collect_subject, SUBJECTS, [scenarios] * len(SUBJECTS))
        trials = [trial for batch in results for trial in batch]

    study = {
        "started": started,
        "samples": SAMPLES,
        "maxOutputTokens": MAX_TOKENS,
        "subjects": [
            {"id": spec, "name": name, "surface": surface}
            for spec, (name, surface) in SUBJECTS.items()
        ],
        "scenarios": [
            {
                "id": scenario.id,
                "title": scenario.title,
                "notes": scenario.notes,
                "hash": scenario.content_hash,
                "licensed": scenario.probes[0][1].licensed,
                "messages": [
                    {"role": turn.role, "content": turn.content} for turn in scenario.turns
                ],
            }
            for scenario in scenarios
        ],
        "trials": trials,
    }
    with args.output.open("x") as file:
        json.dump(study, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
