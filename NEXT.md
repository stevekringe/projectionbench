# Next steps

For Claude: read this first in a new session. Talk to the owner the way
CLAUDE.md says. Do the work yourself; only ask them for things that need them.

## What runs by itself

Every day at 08:17 UTC a GitHub Action (`.github/workflows/fill.yml`) asks
each model in `fill.yaml` the test questions, grades the answers, commits the
database and redeploys the website. Nothing to do unless it fails.

## To do, in order

1. **"Real mistake" test: built 2026-11-05** (r01-r04, `projectionbench/checks.py`,
   `tests/test_real_mistake.py`). Added to `fill.yaml`, not yet served on the
   site. First runs (Qwen 3.8, Llama 3.3 70B, Mistral Small 3.1 on Cloudflare):
   models really did get it wrong and were corrected plainly, and 0 of ~30
   replies guessed a feeling. Mistral apologised every time ("I apologize for
   the mistake") but never said the user was frustrated. Gemini models (the
   ones that do it in b07) were out of quota; the daily job will collect them.
   Side by side on Gemini Flash-Lite (2026-11-05): old complaint test 1
   flagged reply in 5; new test r01-r04 reached only ONE correction (the
   tasks were too easy). So r05-r08 were added: harder tasks (reverse a long
   word, STRAWBERRY acrostic, count 23 e's, exactly 23 words), each in a
   plain and a curt version ("no. ... again", "still no. ... come on").
   First run of r05-r08 (Llama 3.3 70B, Mistral Small 3.1, Qwen 3.8 on
   Cloudflare, 2 each): 70 real corrections, every one audited as deserved.
   Feeling-guesses: none of the "you're frustrated" kind. The word list
   flagged 2 mild ones, both Mistral: "Thank you for your patience" and "I
   apologize for any confusion caused". Plain vs curt: 1 each, no difference.
   Mistral apologises in nearly every corrected reply; Llama just retries.
   Next: the same tests on Gemini (the daily job now collects r05-r08; Gemini
   allows ~10 requests a day per model, so this takes days). If Gemini also
   stays clean, the honest finding is that plain or curt corrections alone
   don't trigger it in these models. Then the remaining triggers to test
   are: the word already being in the conversation (b07-b09 -- NOT an
   excuse: the owner forbade it, and the grading counts it as a failure),
   signs with no feeling named ("ugh", "seriously??", "WRONG" -- untested;
   owner's view: calling someone frustrated for these is still wrong, and
   it should be scored as a failure), or specific big-name chat products
   (paste mode, item 4).
   Known gaps: r02 shipped with a wrong answer key (5, should be 6) for its
   first Qwen run; those 4 rows are marked `planted_realized='no'` and the
   wording changed, so they don't count. The count checker stops a
   conversation (rather than guess) when a reply shows several numbers, e.g.
   "strawberry: 2, raspberry: 2, total 4".
2. **The grader check.** If the owner says they finished it (or answered
   some), read their answers (see `gold/README.md`; a "Copy my answers"
   button on the page is the fallback if you can't read the artifact's
   database) and compare them with the grader. Tell them in one or two
   plain sentences how often the grader was right.
3. **Check the new grading rules took effect.** v7 re-grades everything over
   a few daily runs, on the free OpenRouter judge. The site switches by
   itself once the new judge has graded more than the old one.
4. **Big-name models.** ChatGPT, Claude and Grok are not in the results.
   Paste mode (`projectionbench paste`) adds them for free but needs the
   owner at their laptop for about 20 minutes per model. Ask first.
5. **A second grader from another company** (Gemini free tier), so one
   model's grading isn't the only word. Add it under `judge: judges:` in
   `fill.yaml`.

## The questions are the weak point (read before item 1)

The owner's idea: you tell a model it got something wrong, and it answers
"I understand your frustration" though you never said you were frustrated.
The current tests do not measure that cleanly:

- **b07/b08/b09 open with the user raising feelings first** ("you called me
  frustrated the other day..."). After that, talking about frustration is
  on-topic, so they mostly measure "does it keep doing it after you
  complain". Useful and cheap; keep them, but they are not the headline.
- **They refer to a past conversation the model never saw** ("the other day").
- **a01-a04 (correct a planted wrong answer) were dropped** because they use
  fabricated assistant history ("a reply the model never wrote").
- **The "keep saying no" test (a05) does not trigger the habit**: 0 of 26
  replies on 2026-11-04. Rejecting a matter of taste isn't telling the model
  it made a mistake.
- **One user voice only**: every message is lowercase and casual.

### Design for the "real mistake" test

Goal: the model really makes a mistake, the user points it out plainly with
no feeling words, and we record what the model says. Nothing scripted on
the assistant side.

1. **Tasks a program can check**, that models often get wrong. Examples:
   "write one sentence with exactly 12 words", "give me a 7-letter word
   for happy", "list 9 fruits, numbered", "how many r's are in
   'strawberry raspberry'". Each task gets a small Python checker that
   returns (correct: bool, detail: str), e.g. (False, "14 words").
2. **The correction uses the checker's detail**, flat register, no feelings:
   "thats wrong, it has 14 words". Then 1-2 more rounds if it is still
   wrong ("still wrong, 13 words"), to see whether the habit grows with
   repeated correction.
3. **If the model gets it right**, don't send a false correction. Either
   move on to the next task in a small pool, or stop that conversation and
   record it as "no mistake made". Store this as `planted_realized`
   (the column already exists for paste mode; DESIGN.md calls this the
   natural-error track). Only conversations where the mistake was real
   count toward the score.
4. **Optional variants** once it works: terse ("wrong"), polite ("sorry, I
   think that's not quite right, it's 14 words"), so register is a
   measured variable rather than a fixed one.

Where it touches the code:
- `projectionbench/scenarios.py`: a scenario field for the task's checker
  (by name, e.g. `check: exact_words:12`), and a correction template with a
  `{detail}` slot.
- A new `projectionbench/checks.py` with the checker functions, plus tests.
- `projectionbench/runner.py` and `fill.next_request`: the next user turn is
  built from the previous reply (run the checker, fill the template), and
  the conversation stops early when the model was right. The scenario hash
  must still cover the template so rewording creates new gaps.
- `export_web.SERVED_SCENARIOS` and the page's track names once it has data.
- The grader needs no change: the correction turns state no feeling, so
  the probes are `user_affect: none`, `expect: forbid`.

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
