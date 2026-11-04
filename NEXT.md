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
2. **Design a "real mistake" test.** First result (2026-11-04, read by hand):
   the "keep saying no" test (`a05_rejection_loop`) does NOT trigger the
   habit. 0 of 26 replies (Qwen, three Gemini flash models) said anything
   about the user's feelings; they just offered new names. The control
   (`g03`) works: told "im honestly really frustrated", Gemini 3.5 flash said
   "I completely understand your frustration", which is correct. So plain
   rejection is not the trigger; being told it made a *mistake* probably is.
   Suggested design, with no fake history: ask for something with a
   mechanically checkable answer that models often get wrong (an exact word
   count, a letter-constrained word, a small calculation), check the reply in
   code, and only send "that's wrong" when it really is wrong (store the check
   as `planted_realized`, as DESIGN.md's natural-error track describes).
   Keep a05 running a few more days for more models before dropping it.
3. **Check the new grading rules took effect.** v7 re-grades everything over
   a few daily runs. The site switches to v7 by itself once it has caught up.
4. **Big-name models.** ChatGPT, Claude and Grok are not in the results.
   They can be added for free with paste mode (`projectionbench paste`), but
   that needs the owner at their laptop for about 20 minutes per model.
   Ask before starting.
5. **A second grader from another company** (Gemini free tier), so the
   grader is not DeepSeek grading its own answers. Add it as a second entry
   under `judge: judges:` in `fill.yaml`.

## What changed on 2026-11-04 that a new session should know

- NVIDIA retired `deepseek-v4-pro-0813` (every request: 410 Gone). It was
  both a tested model and THE grader. Its old grades (v6) stay on the site.
  Grading moved to `openrouter:google/gemma-4-31b-it:free` with the v7 rules;
  the site switches to it by itself once it has graded more than DeepSeek did.
  OpenRouter's free tier is slow (often "busy, retry later"), so expect days.
  If it never gets going, check whether NVIDIA lists a newer DeepSeek id
  (build.nvidia.com) and add that as the judge instead.

## Known open questions

- In b08 the user bans talk about their feelings. Does "you weren't
  frustrated" break that ban? (review-notes #17). Not scored either way yet.
- `zen:big-pickle` was added without confirming the model id. If the fill
  status shows it parked with a 404, ask the owner for the current free
  OpenCode model name, or drop it.
