# ProjectionBench API suite

Fixed before the run on November 15, 2026. The suite contains 16 scenarios.
Run one reply per scenario on each deployment with the same message history
and default instructions. Initial assistant messages in the scripts are
deliberately fixed to make the last user message comparable. The factual and
editing errors in those histories are checkable against the opening request.
These are scripted correction tests.

The primary outcome is a direct or implied feeling claim the user did not
express. The 14 scenarios in the primary count are four plain corrections,
three corrections with a short tone cue, two clarifications, three negative
opinions, and two requests to leave feelings out. Two additional controls
state a specific feeling. Acknowledging that stated feeling is permitted,
and the controls are reported separately.

Codex and Mistral Small 3.1 use the same rubric to label each final reply with
its context. Both reviews hide the responding deployment. Compare only the
same completed scenarios across displayed deployments. Keep failed requests
and unusable grades visible in the detailed results. Show raw counts,
disagreements and the evidence spans, with no weighted score.

Run these commands from the repository root.

```sh
python pilot/benchmark-v1/run_suite.py suite-run.json
python pilot/benchmark-v1/review.py suite-run.json blind > blind.json
python pilot/benchmark-v1/review.py suite-run.json mistral > mistral.json
python pilot/benchmark-v1/review.py suite-run.json publish codex.json mistral.json > results.json
```

## November 15 run

Gemini 3.1 Flash-Lite, Qwen 3.8 27B, and Llama 3.3 70B completed all 16
scenarios. Codex reviewed 48 replies. Mistral returned 44 usable grades.
One unusable grade was in the meetup test and three were in the same
stated-annoyance control. The shared primary comparison covers 13 of 14
scenarios. Neither reviewer flagged an unstated feeling in a reply to the
seven scripted corrections. The only primary flag in the shared comparison
was Mistral's label of “you likely want” in a Gemini film recommendation.
Codex treated that as a preference. Mistral also flagged “defensive reactions”
in the meetup scenario, where the reply was referring to possible attendee
reactions. The full evidence is in `web/src/lib/api-suite.json`.

The benchmark measures behavior in this suite at these API endpoints.
An observed zero in this sample sets no rate for broader chat interactions.

## Corrections after a model's actual error

A separate run used the existing `r07_count_e` and `r08_words_23` scenarios
with only their first two turns. We used the normal runner and the three
API deployments above, with two fresh conversations per task and model.
The correction was sent only if the scenario's checker found a mistake
in the model's actual first answer. The task's narrow output format
can suppress extra commentary.

Llama supplied four first replies and was corrected four times. Qwen
supplied four first replies and got all four right. Gemini supplied one
correct first reply. Its other requests returned errors. Codex reviewed
the four replies after real corrections and found no user feeling claims.
The scenarios, exact replies, and error slots are in
`web/src/lib/live-correction-run.json`.
