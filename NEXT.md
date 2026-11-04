# Next steps

For Claude: read this first in a new session. Talk to the owner the way
CLAUDE.md says. Do the work yourself; only ask them for things that need them.

## What runs by itself

Every day at 08:17 UTC a GitHub Action (`.github/workflows/fill.yml`) asks
each model in `fill.yaml` the test questions, grades the answers, commits the
database and redeploys the website. Nothing to do unless it fails.

## To do, in order

1. **The grader check.** If the owner says they finished it (or answered
   some), read their answers (see `gold/README.md`) and compare them with
   the grader. Tell them in one or two plain sentences how often the grader
   was right, under the old grading rules (v6) and the new ones (v7).
2. **Look at the "keep saying no" test results** (`a05_rejection_loop`).
   Show the owner the two or three most telling replies, quoted, in the chat.
   Say plainly whether the test catches the habit or not.
3. **Check the new grading rules took effect.** v7 re-grades everything over
   a few daily runs. The site switches to v7 by itself once it has caught up.
4. **Big-name models.** ChatGPT, Claude and Grok are not in the results.
   They can be added for free with paste mode (`projectionbench paste`), but
   that needs the owner at their laptop for about 20 minutes per model.
   Ask before starting.
5. **A second grader from another company** (Gemini free tier), so the
   grader is not DeepSeek grading its own answers. Add it as a second entry
   under `judge: judges:` in `fill.yaml`.

## Known open questions

- In b08 the user bans talk about their feelings. Does "you weren't
  frustrated" break that ban? (review-notes #17). Not scored either way yet.
- `zen:big-pickle` was added without confirming the model id. If the fill
  status shows it parked with a 404, ask the owner for the current free
  OpenCode model name, or drop it.
