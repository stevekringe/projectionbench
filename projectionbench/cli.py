from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

from projectionbench import metrics, report, runner, store, transcripts
from projectionbench.adapters import build
from projectionbench.judge import lexicon
from projectionbench.scenarios import load_all

DB = "results/projectionbench.sqlite"


def cmd_lint(args):
    scen = load_all(args.scenarios)
    for s in scen:
        probes = s.probes
        exp = {t.expect for _, t in probes}
        print(f"  {s.id:<26} {s.category:<20} {len(s.turns):>2} turns  "
              f"{len(probes)} probe(s)  expect={'/'.join(sorted(exp))}")
    print(f"\n{len(scen)} scenarios valid.")
    return 0


def cmd_patterns(args):
    from projectionbench.judge.patterns import PATTERNS

    print(json.dumps(
        [{"id": p.id, "category": p.category, "severity": p.severity,
          "regex": p.regex, "example": p.note} for p in PATTERNS],
        indent=2,
    ))
    return 0


def cmd_run(args):
    scen = load_all(args.scenarios)
    if args.only:
        wanted = [w.strip() for w in args.only.split(",") if w.strip()]
        scen = [
            s for s in scen
            if any(s.id == w or s.id.startswith(w) or s.category == w for w in wanted)
        ]
        if not scen:
            print(f"no scenarios matched {args.only!r}", file=sys.stderr)
            return 1

    adapters = []
    for spec in args.models:
        try:
            adapters.append(build(spec, max_tokens=args.max_tokens))
        except Exception as e:  # noqa: BLE001
            print(f"skipping {spec}: {e}", file=sys.stderr)
    if not adapters:
        print("no usable subjects -- check your API keys", file=sys.stderr)
        return 1

    run_id = runner.run(adapters, scen, args.samples, db=args.db, workers=args.workers)
    print(f"\nrun {run_id} complete. Next: projectionbench report")
    return 0


def cmd_judge(args):
    from projectionbench.judge.llm import LLMJudge

    conn = store.connect(args.db)
    run_id = args.run or store.latest_run(conn)
    rows = [
        r for r in store.probes_for(conn, run_id)
        if not r["error"] and not conn.execute(
            "SELECT 1 FROM judgments WHERE probe_id=? AND judge LIKE 'llm:%'", (r["id"],)
        ).fetchone()
    ]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("nothing to judge.")
        return 0

    j = LLMJudge()
    name = f"llm:{j.model}"
    print(f"judging {len(rows)} probes with {j.model}", file=sys.stderr)

    disagreements = 0
    for n, r in enumerate(rows, 1):
        v, err = j.judge(json.loads(r["messages"]), r["response"])
        store.insert_judgment(conn, r["id"], name, v.model_dump() if v else {}, err)
        if v and args.audit:
            # The scenario declares user_affect; the judge re-derives it. A clash
            # means the probe text is ambiguous -- fix the scenario, not the judge.
            declared_expressed = r["user_affect"] == "expressed"
            if bool(v.user_expressed_affect) != declared_expressed:
                disagreements += 1
                print(
                    f"\n  AUDIT {r['scenario_id']} probe {r['probe_ordinal']}: "
                    f"declared user_affect={r['user_affect']!r} but judge found "
                    f"{v.user_expressed_affect or 'no expression'}",
                    file=sys.stderr,
                )
        conn.commit()
        print(f"\r  {n}/{len(rows)}", end="", file=sys.stderr, flush=True)

    print(file=sys.stderr)
    if args.audit:
        print(f"{disagreements} ground-truth disagreement(s) across {len(rows)} probes.")
    conn.close()
    return 0


def cmd_report(args):
    conn = store.connect(args.db)
    run_id = args.run or store.latest_run(conn)
    if not run_id:
        print("no runs in the database yet.", file=sys.stderr)
        return 1

    probes = metrics.load(conn, None if args.all else run_id)
    if not probes:
        print(f"no judged probes for run {run_id}.", file=sys.stderr)
        return 1

    scores = metrics.score(probes, bootstrap=not args.fast)
    judge_label = "lexicon"  # the only judge metrics.load() currently reads (judge='lexicon')
    print(report.to_terminal(scores, judge_label))

    csv_path = args.out or f"results/{run_id}.csv"
    report.to_csv(scores, csv_path, judge_label)
    png = report.to_chart(scores, csv_path.replace(".csv", ".png"), judge_label)
    print(f"\nwrote {csv_path}" + (f" and {png}" if png else ""))
    conn.close()
    return 0


def cmd_show(args):
    conn = store.connect(args.db)
    q = "SELECT * FROM probes WHERE 1=1"
    p: list = []
    if args.subject:
        q += " AND subject LIKE ?"; p.append(f"%{args.subject}%")
    if args.scenario:
        q += " AND scenario_id LIKE ?"; p.append(f"%{args.scenario}%")
    q += " ORDER BY scenario_id, subject, sample_idx, probe_ordinal LIMIT ?"
    p.append(args.limit)

    for r in conn.execute(q, tuple(p)).fetchall():
        jr = conn.execute(
            "SELECT verdict FROM judgments WHERE probe_id=? AND judge='lexicon'", (r["id"],)
        ).fetchone()
        v = json.loads(jr["verdict"]) if jr else {}
        if r["error"]:
            flag = "ERROR"
        elif not v:
            flag = "UNJUDGED"
        else:
            flag = "FAIL" if not v.get("passed", True) else "pass"
        print("=" * 78)
        print(f"[{flag}] {r['subject']}  /  {r['scenario_id']}  "
              f"sample {r['sample_idx']}  probe {r['probe_ordinal']}")
        if r["error"]:
            print(f"       error: {r['error'][:200]}")
        if r["tests"]:
            print(f"       tests: {r['tests']}")
        if v.get("hits"):
            for h in v["hits"]:
                print(f"       hit  {h['pattern_id']:<28} {h['span']!r}")
        print("-" * 78)
        for m in json.loads(r["messages"])[-2:]:
            print(f"{m['role'].upper()}: {m['content'][:400]}")
        print(f"\nRESPONSE: {r['response'][:1200]}")
    conn.close()
    return 0


PASTE_HELP = """\
Paste mode: run scenarios by hand against a free chatbot.

  - Open a NEW chat for each scenario. A scenario shares one chat; do not reuse
    a chat between scenarios, and do not edit or regenerate replies.
  - Send the block between the ==== markers exactly, then paste the whole reply
    back here and type a single `.` on its own line to end it.
  - `:skip` skips the current probe. Ctrl-C stops; finished probes are saved.

This measures the CHAT PRODUCT, not the API. They are different systems with
different personas -- which is why runs are tagged @web and never pooled with
API runs of the same model.
"""


# --- clipboard I/O ---------------------------------------------------------
# Typing a terminator into a terminal after pasting multi-line text is a bad
# interface: whether you need to press Enter first depends on whether the
# pasted text ended in a newline, which the user cannot see. Reading the
# clipboard directly removes the problem -- copy the reply, press Enter, done.

def _clipboard_tools() -> tuple[list[str], list[str]] | None:
    if sys.platform == "darwin":
        return (["pbcopy"], ["pbpaste"])
    for paste, copy in ((["wl-paste", "-n"], ["wl-copy"]),
                        (["xclip", "-selection", "clipboard", "-o"],
                         ["xclip", "-selection", "clipboard"])):
        if shutil.which(paste[0]):
            return (copy, paste)
    return None


def _clip_write(cmd: list[str], text: str) -> None:
    subprocess.run(cmd, input=text, text=True, check=False)


def _flush_stdin() -> None:
    """Discard anything already typed or pasted at the terminal.

    Pasting the reply into the terminal is the natural reflex even when the
    instruction says just press Enter. Without this, the unconsumed lines of
    that paste are eaten by the NEXT turn's prompt, which then reports "that's
    still the prompt" once per leftover line and never waits for the user.
    """
    try:
        import termios
        if sys.stdin.isatty():
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except Exception:  # noqa: BLE001 - non-tty, Windows, or no termios
        pass


def _clip_read(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout


def _collect_via_clipboard(copy, paste, outgoing: str) -> str | None:
    """Put the prompt on the clipboard; read the reply back off it."""
    _clip_write(copy, outgoing)
    print("\n  [copied to clipboard] Paste into the chat (Cmd+V) and send it.")
    print("  Then copy its whole reply (Cmd+C), come back here, and press Enter.")
    print("  Do NOT paste into this terminal -- it reads your clipboard by itself.")
    print("  (or type s + Enter to skip this turn, q + Enter to quit)")
    while True:
        _flush_stdin()
        try:
            cmd = input("  press Enter > ").strip().lower()
        except EOFError:
            return None
        if cmd == "s":
            return None
        if cmd == "q":
            raise KeyboardInterrupt
        reply = _clip_read(paste).strip()
        if not reply:
            print("  clipboard is empty -- copy the reply, then press Enter.")
            continue
        if reply == outgoing.strip():
            print("  clipboard still holds the prompt -- copy the model's REPLY first.")
            continue
        preview = reply.replace("\n", " ")[:70]
        print(f"  got {len(reply)} chars: {preview}...")
        return reply


def _read_block() -> str | None:
    lines: list[str] = []
    try:
        while True:
            line = input()
            if line.strip() == ".":
                break
            if line.strip() == ":skip":
                return None
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines).strip()


def _ask(question: str, options: str) -> str:
    while True:
        a = input(f"{question} [{options}] ").strip().lower()
        if a and a[0] in options:
            return a[0]


def cmd_paste(args):
    scen = load_all(args.scenarios)
    if args.only:
        wanted = [w.strip() for w in args.only.split(",") if w.strip()]
        scen = [s for s in scen
                if any(s.id == w or s.id.startswith(w) or s.category == w for w in wanted)]
    if not scen:
        print(f"no scenarios matched {args.only!r}", file=sys.stderr)
        return 1

    subject = args.subject if "@" in args.subject else f"{args.subject}@web"
    clip = None if args.typed else _clipboard_tools()
    if clip:
        print("Clipboard mode: prompts are copied for you; replies are read from "
              "your clipboard.\nNo typing into the terminal. Use --typed to disable.\n")
    conn = store.connect(args.db)
    run_id = args.run or store.new_run(
        conn, {"mode": "paste", "subjects": [subject], "scenarios": [s.id for s in scen]}
    )

    if not args.quiet:
        print(PASTE_HELP)
    total = sum(len(s.probes) for s in scen)
    print(f"subject: {subject}   run: {run_id}   {len(scen)} scenario(s), {total} probe(s)\n")

    collected = 0
    try:
        for s in scen:
            recorded = {
                r["probe_ordinal"]: r["response"]
                for r in conn.execute(
                    "SELECT probe_ordinal, response FROM probes WHERE run_id=? AND "
                    "subject=? AND scenario_id=? AND sample_idx=?",
                    (run_id, subject, s.id, args.sample),
                )
            }
            if len(recorded) >= len(s.probes):
                print(f"-- {s.id}: already complete, skipping")
                continue
            if recorded:
                print(f"-- {s.id}: resuming, {len(recorded)} turn(s) already recorded. "
                      "Keep using the SAME chat window.")

            print("\n" + "#" * 74)
            print(f"# SCENARIO {s.id}  ({s.category})")
            print(f"# {s.title}")
            print("#" * 74)
            print("\n>>> Start a NEW chat for this scenario.\n")

            if s.system:
                print("!! This scenario needs a SYSTEM PROMPT. Put the following in the")
                print("!! product's custom-instructions field if it has one. If it does not,")
                print("!! skip this scenario -- sending it as a chat message is a different")
                print("!! test and the results are not comparable.\n")
                print("-" * 74)
                print(s.system.strip())
                print("-" * 74)
                if _ask("\nSystem prompt set?", "yn") == "n":
                    print("skipping scenario.\n")
                    continue

            history: list[dict] = []
            ordinal = 0
            planted_realized = None
            aborted = False

            for i, turn in enumerate(s.turns):
                if turn.role == "assistant":
                    # Can't plant a reply in a real chat product. The real one the
                    # user pasted already went into history; this only records
                    # whether it carried the error the next correction assumes.
                    print("\n    (script assumed the reply would be roughly:")
                    for ln in turn.content.strip().splitlines():
                        print(f"     | {ln}")
                    print("    )")
                    a = _ask(
                        "\n    Did the real reply contain that error?",
                        "yns",
                    )
                    if a == "s":
                        aborted = True
                        break
                    planted_realized = {"y": "yes", "n": "no"}[a]
                    if a == "n":
                        print("    noted -- the next correction will be a FALSE correction.")
                        print("    Recorded, but excluded from the headline metrics.")
                    continue

                if not (turn.probe and ordinal in recorded):
                    print("\n" + "=" * 74)
                    print(turn.content.strip())
                    print("=" * 74)

                if turn.probe:
                    print(f"\n[probe {ordinal}] {turn.tests}")
                if not clip:
                    print("(send that, then paste the reply, then `.` on its own line)")

                history.append({"role": "user", "content": turn.content})

                # Already collected on an earlier attempt: replay it into the
                # history and move on, so the browser chat and this script stay
                # in step without re-sending the turn.
                if turn.probe and ordinal in recorded:
                    print(f"\n  (turn {ordinal} already recorded -- skipping ahead)")
                    history.append({"role": "assistant", "content": recorded[ordinal]})
                    ordinal += 1
                    continue

                if clip:
                    reply = _collect_via_clipboard(clip[0], clip[1], turn.content.strip())
                else:
                    reply = _read_block()
                if reply is None:
                    print("skipped.")
                    if turn.probe:
                        ordinal += 1
                    continue
                if not reply:
                    print("empty reply -- skipping scenario.")
                    aborted = True
                    break

                history.append({"role": "assistant", "content": reply})

                if turn.probe:
                    probe_id = store.insert_probe(conn, {
                        "run_id": run_id, "subject": subject, "scenario_id": s.id,
                        "category": s.category, "sample_idx": args.sample,
                        "turn_index": i, "probe_ordinal": ordinal,
                        "user_affect": turn.user_affect, "expect": turn.expect,
                        "invites_self_disclosure": int(turn.invites_self_disclosure),
                        "tests": turn.tests, "system": s.system,
                        "messages": json.dumps(history[:-1]), "response": reply,
                        "raw": json.dumps({"mode": "paste"}), "error": None,
                        "planted_realized": planted_realized,
                    })
                    v = lexicon.score_probe(reply, turn.user_affect, turn.expect,
                                            turn.invites_self_disclosure)
                    store.insert_judgment(conn, probe_id, "lexicon", v.to_dict())
                    conn.commit()
                    collected += 1
                    ordinal += 1

                    mark = "PASS" if v.passed else "FAIL"
                    print(f"\n  --> {mark}", end="")
                    if v.hits:
                        print("  " + ", ".join(sorted({h.pattern_id for h in v.hits})))
                    else:
                        print("  (no lexicon hits)")

            if aborted:
                print("scenario abandoned; probes already recorded are kept.\n")

    except KeyboardInterrupt:
        print("\n\ninterrupted.")

    print(f"\n{collected} probe(s) recorded for {subject} in run {run_id}.")
    print(f"transcripts: {transcripts.write(conn, run_id)}")
    print("Next: projectionbench report")
    conn.close()
    return 0


def cmd_rejudge(args):
    """Re-score stored responses against the current lexicon. No API calls.

    This is why raw transcripts are stored: a pattern fix must never require
    re-spending on the API, and old runs must stay comparable to new ones.
    """
    conn = store.connect(args.db)
    rows = [r for r in store.probes_for(conn, args.run) if not r["error"]]
    changed = 0
    for r in rows:
        old = conn.execute(
            "SELECT verdict FROM judgments WHERE probe_id=? AND judge='lexicon'", (r["id"],)
        ).fetchone()
        v = lexicon.score_probe(r["response"], r["user_affect"], r["expect"],
                                bool(r["invites_self_disclosure"]))
        if old and json.loads(old["verdict"])["passed"] != v.passed:
            changed += 1
            was = "FAIL" if not json.loads(old["verdict"])["passed"] else "pass"
            now = "FAIL" if not v.passed else "pass"
            print(f"  {r['subject']} / {r['scenario_id']}#{r['probe_ordinal']}: {was} -> {now}")
        store.insert_judgment(conn, r["id"], "lexicon", v.to_dict())
    conn.commit()
    conn.close()
    print(f"re-judged {len(rows)} probes; {changed} verdict(s) changed.")
    return 0


def cmd_transcripts(args):
    conn = store.connect(args.db)
    if args.all:
        print(transcripts.write(conn, None, args.out))
    else:
        run_id = args.run or store.latest_run(conn)
        if not run_id:
            print("no runs in the database yet.", file=sys.stderr)
            return 1
        print(transcripts.write(conn, run_id, args.out))
    conn.close()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="projectionbench", description=__doc__)
    ap.add_argument("--db", default=DB)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint", help="validate the scenario set")
    p.add_argument("--scenarios", default="scenarios/*.yaml")
    p.set_defaults(fn=cmd_lint)

    p = sub.add_parser("patterns", help="dump the lexicon as JSON for publication")
    p.set_defaults(fn=cmd_patterns)

    p = sub.add_parser("run", help="run scenarios against subjects")
    p.add_argument("--models", "-m", nargs="+", required=True,
                   help="provider:model, e.g. anthropic:claude-opus-5 openai:gpt-5")
    p.add_argument("--samples", "-n", type=int, default=8)
    p.add_argument("--scenarios", default="scenarios/*.yaml")
    p.add_argument("--only", help="comma-separated scenario ids or categories")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--max-tokens", type=int, default=16000)
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("paste", help="run scenarios by hand against a free chatbot")
    p.add_argument("--subject", "-s", required=True,
                   help="label for what you are testing, e.g. paste:grok@web")
    p.add_argument("--scenarios", default="scenarios/*.yaml")
    p.add_argument("--only", help="comma-separated scenario ids or categories")
    p.add_argument("--sample", type=int, default=0, help="sample index, for repeat passes")
    p.add_argument("--run", help="append to an existing run id instead of starting one")
    p.add_argument("--quiet", action="store_true", help="skip the instructions banner")
    p.add_argument("--typed", action="store_true",
                   help="paste into the terminal and end with `.` instead of using the clipboard")
    p.set_defaults(fn=cmd_paste)

    p = sub.add_parser("judge", help="run the LLM judge over stored probes")
    p.add_argument("--run")
    p.add_argument("--limit", type=int)
    p.add_argument("--audit", action="store_true",
                   help="flag scenarios whose declared ground truth the judge disputes")
    p.set_defaults(fn=cmd_judge)

    p = sub.add_parser("rejudge", help="re-score stored responses after a lexicon change (free)")
    p.add_argument("--run")
    p.set_defaults(fn=cmd_rejudge)

    p = sub.add_parser("transcripts", help="(re)write the readable transcript file")
    p.add_argument("--run")
    p.add_argument("--all", action="store_true", help="every run in one file")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_transcripts)

    p = sub.add_parser("report", help="metrics, CSV and charts")
    p.add_argument("--run")
    p.add_argument("--all", action="store_true", help="pool every run in the db")
    p.add_argument("--out")
    p.add_argument("--fast", action="store_true", help="skip bootstrap CIs")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("show", help="print transcripts -- read these by hand")
    p.add_argument("--subject")
    p.add_argument("--scenario")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(fn=cmd_show)

    args = ap.parse_args(argv)
    return args.fn(args)
