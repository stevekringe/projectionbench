# Matched API model comparison

Protocol fixed before collection on November 15, 2026.

Run two requests on each of three shared conversations for each of the six
configured API deployments. Every deployment receives the same scripts
through its regular API adapter. The replies generated for this comparison
are independent requests. Earlier replies in the schedule and film
scenarios are scripted and held fixed across deployments. The three prompts
cover a factual correction, a negative film opinion followed by a clarification,
and a complaint about an earlier feeling label. The first two leave feelings
unmentioned. The complaint quotes a label without adopting it.

Compare only the planned slots with a full set of replies and two usable
blinded grades for each included model. A deployment with an incomplete
set is listed with its coverage. The full results retain the incomplete
trials and all quoted evidence. Each bar counts direct and implied
attributions under the [shared rubric](benchmark-v1/rubric.txt). Show replies
flagged by both versus one reviewer. The reviewers grade the same full
reply and preceding messages, with model names hidden and grading order
shuffled. Record model-based agreement and disagreement.

Use default API settings except a 4,096-token output limit. Retry transient
connection failures once. These bars compare a fixed snapshot of six
replies per deployment on the same three scripts.

Run from the project root with the existing API credentials.

```sh
python pilot/benchmark-v1/compare_models.py model-run.json
python pilot/benchmark-v1/review.py model-run.json blind > blind.json
python pilot/benchmark-v1/review.py model-run.json mistral > mistral.json
python pilot/benchmark-v1/review.py model-run.json publish codex.json mistral.json > results.json
```

## Coverage

The six-deployment attempt returned 21 of 36 planned replies. Gemini 3.1
Flash-Lite and Qwen each completed 6 of 6. Gemini 3.5 and Gemini 3.6 each
completed three, Gemini 3.7 completed two, and Gemini 3.8 completed one.
The raw replies and request errors are in
`pilot/results/model-comparison-2026-11-15.json`. This attempt did not
supply full six-model scores. The expanded
[16-scenario suite](benchmark-v1/suite/README.md) was run separately.
