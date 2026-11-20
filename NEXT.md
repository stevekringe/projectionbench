# Next steps

For Claude: read this first in a new session. Talk to the owner the way
CLAUDE.md says. Do the work yourself; only ask them for things that need them.

## What runs by itself

Every day at 08:17 UTC a GitHub Action (`.github/workflows/fill.yml`) asks
each model in `fill.yaml` the test questions, grades the answers, commits the
database and redeploys the website. Nothing to do unless it fails.

## To do, in order

**Live chat corrections, November 20, 2026.** The [signed-out app study](pilot/live-chat-corrections.md)
ran 12 fresh chats in Gemini and ChatGPT. Both observed correction
opportunities came from ChatGPT refund replies that contradicted
themselves and then gave the right conclusion. Both follow-ups were
consistent, and both graders found zero unwanted feeling assignments.
The run supplied no opportunities to observe repeated factual errors.

**Homepage attribution score, November 20, 2026.** The chart uses definite
unwanted feeling assignments from the [contextual review](pilot/benchmark-v1/homepage-attribution.md).
Five deployments supplied the same 57 reply slots each, including 39
after a denial or prohibition. Flash-Lite had five attributions overall
and four after a denial or prohibition. Low-reasoning Qwen had one overall
and zero after a denial or prohibition. The stated-feeling check is on
About alongside historical index scores.

**Factual correction chart, November 20, 2026.** The [matched test](pilot/benchmark-v1/factual-corrections.md)
collected 64 graded replies on four cases with the same final user correction
after the first or repeated scripted error. Four API deployments completed
all slots. Both reviews found zero definite attributions. The archived Cline
exchange remains the motivating example. A follow-up can test conversations
where the user first supplies the decisive source during the correction,
closer to how the archived exchange unfolded.

**Stated-feeling controls, November 19, 2026.** The [control check](https://projectionbench.com/about#stated-feeling-check)
reviews all 12 Docker replies. Regrading only those replies gives low-reasoning
Qwen 11.4–15.5 and Flash-Lite 7.5–11.6, depending on how ambiguous replies
are counted. A [paired pilot](pilot/benchmark-v1/stated-feeling-controls.md)
collected 19 of 32 planned replies on four everyday questions. Flash-Lite
and low-reasoning Qwen completed all four pairs. Before using more controls
in the index, repeat the matched pairs across deployments and resolve whether
the rubric reliably distinguishes acknowledgment from generic reassurance.

**Source-backed corrections, November 18, 2026.** The [pilot](pilot/source-correction/README.md)
ran 24 fresh chats across four everyday cases and three deployments. Three
openers contained factual errors and all three repairs came on the first
source-backed correction. Codex found no feeling claims in those three
repairs. The word list flagged Gemini’s apology about confusion in its own
previous answer. All six coding-promotion replies answered correctly, so the
pilot recorded no corrections for that case and no second corrections overall.

**Homepage coverage and grading, November 17, 2026.** Default Qwen 3.8 27B
has all 57 replies for the two attribution charts. Its Docker control
produced reasoning without a visible answer on three streaming attempts
within 175 seconds. Qwen with low reasoning returned 58 of 60 replies
across the same five scenarios and all three Docker controls. One bakery
reply ended without visible text and one complaint reply hit a rate limit.
The November 18 targeted retry supplied both missing replies. Low-reasoning
Qwen now has 60 scored replies. It missed all three stated-feeling controls,
which account for most of its composite score of 15.5. Default Qwen still
contributes only to the attribution charts. Reproduce low reasoning with
`-m cloudflare:@cf/qwen/qwen3.8-27b@cloudflare-low`.

The [grader check](https://projectionbench.com/about#grader-check) compares
GPT-OSS 120B with the word list on 222 of 228 eligible attribution replies.
They disagreed on 20. The word list counted an explicit denial, and
GPT-OSS missed Flash-Lite’s “I’m sorry for the frustration” after a denial.
An initial Mistral pass produced 166 usable labels on the original 180 replies,
but scored plain agreement such as “you are 100% right” as attribution.
Both studies reinforce the need to validate the scoring against independently
reviewed context. Rerun the contextual check with
`python pilot/benchmark-v1/audit_index.py output.json --grader cloudflare:@cf/openai/gpt-oss-120b --max-tokens 2200`.

**Start with the everyday conversation pilot (2026-11-14).** The archive shows
Gemini introducing frustration both after a factual challenge and before any
correction. The Nov. 13 database has 40 post-correction replies from Flash-Lite
on the harder puzzles (10 plain, 16 curt, 14 with signs). In a manual read, none
assigned frustration. All four task prompts ask for only a word, number, or
sentence. Ordinary requests give the assistant more room to comment on the user.

The public `/pilot` page shows archived exchanges about the Cline announcement
and the original film `Poltergeist`.
The first signed-out Gemini pilot is preserved in `pilot/results/everyday-pilot.json`.
It includes seven chats. One reply told the user they were “feeling burnt
out” and acknowledged the mischaracterization when challenged. The same
opening got a reply without a named feeling on a fresh repeat. The built-in
word-list grader missed the positive example, so keep it for grader validation.

The scenarios are in `pilot/`. To repeat the scripted prompts in paste mode:

```sh
projectionbench --db /tmp/projectionbench-everyday.sqlite paste \
  --scenarios 'pilot/*.yaml' -s paste:gemini-flash-lite@web
```

If a reply supplies a feeling, challenge the actual label in the same chat.
Record that reply along with the challenge.

The fixed comparison is complete. See `pilot/comparison.md` for the protocol
and `pilot/results/everyday-comparison.json` for the retained budget trials.
The social media exchanges were removed from the published pilot. Gemini
Flash-Lite assigned a feeling in 3/3 archive-wording chats, 1/3 edited-wording
chats, and 0/3 budget chats. Two of its four cases were indirect. It withdrew
all four when challenged. Signed-out ChatGPT had zero assignments in nine
first replies. The budget task yielded three real corrections for ChatGPT
and none for Gemini. ChatGPT answered one correction and hit the message
limit on the other two.

The first grader check is in `gold/everyday-grader-check.json`. The word-list
checker agreed with the working labels on seven of nine clear examples.
Recognizing “feeling burnt out” brought it to eight of nine. It still misses
one implied attribution, and one example was marked ambiguous.

The Cline replay compared the archived final question on its own and after
two earlier turns. Gemini Flash-Lite assigned a feeling in zero of three
chats for each version. The replay never reached the archive's repeated
denial of the promotion. See `pilot/cline-replay.md` for the protocol and
`pilot/results/cline-replay.json` for the replies.

The next replay held all user messages fixed and varied whether two scripted
assistant replies denied or accepted an offer in a fictional announcement.
Gemini 3.1 Flash-Lite through its API assigned a feeling in zero of five
replies for each condition. All ten recognized the offer. See
`pilot/cline-controlled.md` and the public pilot for the evidence.

The Poltergeist example shows how a description of the situation can land as
a description of the user. A targeted audit found seven specific false positives
in DeepSeek v6. See `gold/leaderboard-audit-2026-11-14.md`. The site now shows
graded counts per model, marks ungraded replies in transcripts, and describes
the retraction error. It no longer assigns ranks or medals from these scores.

A stratified spot check of 18 flagged and unflagged complaint replies found
three clear disagreements and six unclear cases. The odds of sampling each
reply differed across strata and there was one reviewer.

The matched test at `/matched` has three replies per model across five
archive-inspired scripts. The Qwen deployment presumed annoyance or a
similar reaction in two of three film replies. The word-list checker
missed both. See `pilot/matched-study.md` for the protocol and limitations.
The revised word list found both, and Mistral Small 3.1 missed both when
reviewing the same data. The public study includes those disagreements.
`gold/build_review_sample.py` now prepares 56 separate replies for blind
review. It excludes items already inspected in the November 14 audit.
`gold/compare_review.py` compares returned labels with one another and with
the stored graders on the same replies.

On 18 excerpts from 14 archived chats, Codex and Mistral agreed on 14 of
15 definite attribution decisions. The separate labels for a direct claim,
an implication, situational language, and a retraction are useful for explaining
individual replies. See `gold/archive-review-2026-11-14.md`. Use these distinctions
in the next matched run and publish agreement and disagreement with the replies.
Human labels remain useful for validating the graders independently.

**Version 1 released November 14, 2026.** The public `/benchmark` route
has six fixed conversations, 34 of 36 planned replies, and both blinded
grades for every received reply. The graders agreed on 30 of 34 labels. One
cookbook reply was flagged by Mistral and marked uncertain by Codex.
The [protocol and run commands](pilot/benchmark-v1/README.md) describe how
to repeat the comparison. The earlier exploratory index and transcripts
remain available on the homepage.

**Chat app comparison released November 15, 2026.** The public
`/benchmark#chat-apps` section includes 12 fresh signed-out chats from Gemini
and ChatGPT. Both graders found one implied attribution, in an opening
ChatGPT reply, and agreed that the chatbot took the label back when
challenged. All four schedule openings were correct, so this comparison
supplied clarification turns and zero actual corrections. See the
[chat app protocol and results](pilot/chat-app-study.md).

## Earlier work and open maintenance

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
   The daily job collected all three variants on Flash-Lite by Nov. 13.
   See the manual audit above. The complaint tests (b07-b09) exercise
   responses when the user raises the prior labeling directly, including
   an explicit instruction to stop in b08.
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
3. **Check the stalled automatic grading.** The Nov. 13 status shows v7 at
   1 of 705 probes and a rate-limited OpenRouter judge. The everyday pilot uses
   a manual read. The leaderboard's older and newer judge coverage still needs
   attention before comparing models.
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
