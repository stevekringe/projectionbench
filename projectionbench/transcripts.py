"""Human-readable transcripts, written automatically after every run.

One file per run, named by run id, so a transcript can never drift from the run
it describes. Turns are recorded EXACTLY as they were sent -- if a scenario's
wording was edited afterwards, old transcripts keep the old wording, because
that is what the model actually saw. The scenario file is the plan; this is the
record.
"""

from __future__ import annotations

import json
import os


def _render(conn, run_id: str | None) -> str:
    q = """
        SELECT p.*, j.verdict FROM probes p
        LEFT JOIN judgments j ON j.probe_id = p.id AND j.judge = 'lexicon'
        %s ORDER BY p.run_id, p.subject, p.scenario_id, p.sample_idx, p.probe_ordinal
    """ % ("WHERE p.run_id = ?" if run_id else "")
    rows = conn.execute(q, (run_id,) if run_id else ()).fetchall()

    meta = conn.execute(
        "SELECT started_at, params FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone() if run_id else None

    out: list[str] = []
    w = out.append
    w(f"# Transcripts — run {run_id or '(all runs)'}")
    if meta:
        w(f"\nStarted {meta['started_at']}")
        w(f"\n```json\n{json.dumps(json.loads(meta['params']), indent=2)}\n```")
    ok = [r for r in rows if not r["error"]]
    w(f"\n{len(ok)} completed probe(s), {len(rows) - len(ok)} errored. Nothing truncated.")
    w("""
## How to read this

Most of what follows is **script we wrote**, not model output. Only one block
type is the model actually talking. Every block is labelled:

| Label | Who wrote it |
|---|---|
| `[SCRIPT] USER` | Us. Sent to the model as the user's turn. |
| `[FABRICATED] ASSISTANT` | **Us, not the model.** Fake history planted so every model is corrected on an identical error. The model never said this. |
| `[REAL] <model> SAID:` | **The model.** This is the only real output on the page. |

The fabricated turns often contain the exact phrase under study
("I understand your frustration"). That is us baiting the probe -- it is not
evidence of anything. Look only at the `[REAL]` blocks.

Turns appear exactly as sent, so transcripts of older runs keep the wording the
scenario had at the time, even if the scenario file has been edited since.
""")

    seen = None
    for r in rows:
        # run_id is part of the key: the same scenario re-run later is a separate
        # conversation, not a continuation of the earlier one.
        key = (r["run_id"], r["subject"], r["scenario_id"], r["sample_idx"])
        model = r["subject"].split(":", 1)[-1].split("@")[0]
        if key != seen:
            seen = key
            w("\n" + "=" * 78)
            w(f"## {r['scenario_id']} — {r['subject']}")
            w(f"run {r['run_id']}, sample {r['sample_idx']}")
            w("=" * 78)
            if r["system"]:
                w(f"\n`[SCRIPT]` **SYSTEM PROMPT:**\n```\n{r['system'].strip()}\n```")
            for m in json.loads(r["messages"])[:-1]:
                who = (
                    "`[SCRIPT]` **USER**"
                    if m["role"] == "user"
                    else f"`[FABRICATED]` **ASSISTANT** — written by us; "
                         f"{model} did NOT say this"
                )
                w(f"\n{who}:\n```\n{m['content'].strip()}\n```")

        w(f"\n`[SCRIPT]` **USER** — probe {r['probe_ordinal']}, testing: {r['tests']}:")
        w(f"```\n{json.loads(r['messages'])[-1]['content'].strip()}\n```")

        if r["error"]:
            w(f"\n**ERROR:** `{r['error'][:300]}`")
            continue
        v = json.loads(r["verdict"]) if r["verdict"] else {}
        verdict = "PASS — no attribution" if v.get("passed") else "FAIL"
        hits = ", ".join(sorted({h["pattern_id"] for h in v.get("hits", [])})) or "no lexicon hits"
        w(f"\n`[REAL]` **{model} SAID** — {verdict} [{hits}]:")
        w(f"```\n{r['response'].strip()}\n```")

    return "\n".join(out) + "\n"


def write(conn, run_id: str | None, path: str | None = None) -> str:
    path = path or f"results/{run_id or 'all'}.transcript.md"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(_render(conn, run_id))
    return path
