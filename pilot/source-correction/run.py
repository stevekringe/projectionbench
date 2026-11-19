"""Collect and review source-grounded corrections in real conversations."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from projectionbench.adapters import build
from projectionbench.fill import load_env_file, quiet

CASES = Path(__file__).with_name("cases.json")
MAX_TOKENS = 4096
MAX_TURNS = 3
ANSWERS = {"correct", "incorrect", "unclear"}
FEELINGS = {"none", "direct", "implied", "unclear"}


def read(path):
    return json.loads(path.read_text())


def save(path, study):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(study, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def models(specs):
    load_env_file()
    result = {}
    for spec in specs:
        adapter = quiet(build(spec, max_tokens=MAX_TOKENS))
        if hasattr(adapter, "request_timeout"):
            adapter.request_timeout = 35
        result[adapter.subject_id] = adapter
    return result


def conversation(trial):
    return [message for turn in trial["turns"] for message in (
        {"role": "user", "content": turn["prompt"]},
        {"role": "assistant", "content": turn["reply"]},
    )]


def collect(path, study, adapters, tasks):
    def request(trial, prompt):
        history = conversation(trial) + [{"role": "user", "content": prompt}]
        try:
            response = adapters[trial["subject"]].complete(history)
            text, error = response.text, response.error
        except Exception as exc:
            text, error = "", f"{type(exc).__name__}: {exc}"
        return {"prompt": prompt, "reply": text if text.strip() and not error else None,
                "error": error or (None if text.strip() else "Empty reply"), "review": None}

    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(request, trial, prompt): trial for trial, prompt in tasks}
        for future in as_completed(pending):
            trial = pending[future]
            turn = future.result()
            trial["turns"].append(turn)
            save(path, study)
            outcome = turn["error"].split(":", 1)[0] if turn["error"] else "received"
            print(f"{trial['id']} turn {len(trial['turns'])}: {outcome}", flush=True)


def pending_reviews(study):
    return {t["id"]: t for t in study["trials"] if t["turns"] and
            t["turns"][-1]["reply"] is not None and t["turns"][-1]["review"] is None}


def accept_reviews(study, reviews):
    pending = pending_reviews(study)
    if reviews.keys() != pending.keys():
        raise ValueError("Supply one review for each unreviewed reply")
    for trial_id, verdict in reviews.items():
        turn = pending[trial_id]["turns"][-1]
        answer, feeling = verdict["answer"], verdict["feeling"]
        if answer not in ANSWERS or feeling not in FEELINGS:
            raise ValueError(f"{trial_id}: invalid answer or feeling label")
        for key, required in (("answerQuote", answer != "unclear"),
                              ("feelingQuote", feeling != "none")):
            quote = verdict.get(key)
            if required and (not isinstance(quote, str) or not quote.strip() or quote not in turn["reply"]):
                raise ValueError(f"{trial_id}: {key} must quote the reply verbatim")
            if not required and quote is not None:
                raise ValueError(f"{trial_id}: {key} must be null for this label")
        if answer == "incorrect" and not verdict.get("conflict", "").strip():
            raise ValueError(f"{trial_id}: record why the answer contradicts the source")
    for trial_id, verdict in reviews.items():
        pending[trial_id]["turns"][-1]["review"] = verdict


def next_turns(study):
    if pending_reviews(study):
        raise ValueError("Review each completed reply before sending follow-ups")
    cases = {case["id"]: case for case in study["cases"]}
    tasks = []
    for trial in study["trials"]:
        turns = trial["turns"]
        case = cases[trial["case"]]
        if not turns:
            tasks.append((trial, case["opening"]))
        elif len(turns) < MAX_TURNS and (turns[-1]["review"] or {}).get("answer") == "incorrect":
            follow_up = (case["correction"].format(source=case["sourceQuote"])
                         if len(turns) == 1 else case["repeat"])
            quote = turns[-1]["review"]["answerQuote"]
            tasks.append((trial, f"You wrote ‘{quote}’ {follow_up}"))
    return tasks


def start(path, specs, samples):
    if path.exists() or samples < 1:
        raise ValueError("Start requires a new output file and a positive sample count")
    cases = read(CASES)
    for case in cases:
        if case["sourceQuote"] not in case["opening"]:
            raise ValueError(f"{case['id']}: the correction must quote the opening source")
    adapters = models(specs)
    trials = [{"id": f"t{number:02}", "case": case["id"], "subject": subject,
               "sample": sample, "turns": []}
              for number, (sample, case, subject) in enumerate(
                  ((sample, case, subject) for sample in range(1, samples + 1)
                   for case in cases for subject in adapters), 1)]
    study = {"started": datetime.now(timezone.utc).isoformat(), "models": specs,
             "samples": samples, "maxTokens": MAX_TOKENS, "cases": cases, "trials": trials}
    save(path, study)
    collect(path, study, adapters, next_turns(study))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    opening = commands.add_parser("start")
    opening.add_argument("--models", nargs="+", required=True)
    opening.add_argument("--samples", type=int, default=2)
    commands.add_parser("blind")
    review = commands.add_parser("review")
    review.add_argument("reviews", type=Path)
    commands.add_parser("advance")
    args = parser.parse_args()
    if args.command == "start":
        start(args.output, args.models, args.samples)
        return

    study = read(args.output)
    if args.command == "blind":
        cases = {case["id"]: case for case in study["cases"]}
        items = {key: {"answerKey": cases[t["case"]]["answerKey"], "conversation": conversation(t)}
                 for key, t in pending_reviews(study).items()}
        print(json.dumps(items, ensure_ascii=False, indent=2))
    elif args.command == "review":
        accept_reviews(study, read(args.reviews))
        save(args.output, study)
    else:
        tasks = next_turns(study)
        if tasks:
            collect(args.output, study, models(study["models"]), tasks)
        else:
            print("All trials have stopped.")


if __name__ == "__main__":
    main()
