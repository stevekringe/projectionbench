"""Collect the fixed v1 prompts using the regular scenario runner."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import partial
from itertools import product, repeat
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


def collect_subject(spec, scenarios, samples, cloudflare_workers):
    adapter = build(spec, max_tokens=MAX_TOKENS)
    if adapter.name == "cloudflare":
        adapter.request_timeout = 30
    if adapter.name == "gemini":
        adapter.max_attempts = 1
        adapter.request_timeout = 35

    def collect_trial(unit):
        scenario, index = unit
        result = run_unit(adapter, scenario, index)[0]
        first_error = incomplete_reason(result)
        retry = first_error in {"URLError", "TimeoutError", "RemoteDisconnected"}
        if retry:
            result = run_unit(adapter, scenario, index)[0]
        error = incomplete_reason(result)
        print(scenario.id, spec, index + 1, error or "received", flush=True)
        return {
            "id": f"{scenario.id}/{spec}/{index + 1}",
            "scenario": scenario.id,
            "subject": spec,
            "sample": index + 1,
            "reply": None if error else result.response,
            "error": error,
            "retry": first_error if retry else None,
        }

    units = product(scenarios, range(samples))
    if adapter.name == "cloudflare" and cloudflare_workers > 1:
        with ThreadPoolExecutor(max_workers=cloudflare_workers) as pool:
            return list(pool.map(collect_trial, units))
    return [collect_trial(unit) for unit in units]


def collect_study(subjects, scenarios, samples, cloudflare_workers=1):
    load_env_file()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with ThreadPoolExecutor(max_workers=len(subjects)) as pool:
        collect = partial(collect_subject, cloudflare_workers=cloudflare_workers)
        results = pool.map(collect, subjects, repeat(scenarios), repeat(samples))
        trials = [trial for batch in results for trial in batch]

    return {
        "started": started,
        "samples": samples,
        "maxOutputTokens": MAX_TOKENS,
        "subjects": [
            {"id": spec, "name": name, "surface": surface}
            for spec, (name, surface) in subjects.items()
        ],
        "scenarios": [
            {
                "id": scenario.id,
                "title": scenario.title,
                "notes": scenario.notes,
                "category": scenario.category,
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("Output must be a new file in an existing directory")

    folder = Path(__file__).resolve().parent
    scenarios = load_all(str(folder / "*.yaml"))
    study = collect_study(SUBJECTS, scenarios, SAMPLES)
    with args.output.open("x") as file:
        json.dump(study, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
