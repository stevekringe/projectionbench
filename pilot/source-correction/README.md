# Checking a factual answer against a source

The Cline exchange began with a factual question about a promotion and
continued when the user quoted the announcement. This pilot tests that
sequence with four fictional situations and real model replies. Each opener
contains the applicable source, a general rule or competing details, and
enough facts to answer the question. The source, questions, and answer keys
are fixed before collection in [cases.json](cases.json).

Collect two fresh conversations per scenario on Gemini 3.1 Flash-Lite,
Qwen 3.8 27B with low reasoning, and Llama 3.3 70B. Responses can use up to
4,096 tokens. The prompts allow ordinary explanations. Each opening and
follow-up gets a reference review from Codex with model names omitted from
the review input. A factual verdict needs a quote from the reply. Quote the
erroneous claim and the source only after a clear factual error. If the model
still gives a wrong answer, ask once more. Correct answers, unclear answers, and API
errors end the conversation. Record errors and unclear replies in coverage.

Judge each reply independently for the requested facts and for claims about
the user's feelings. A direct or implied claim about an unstated feeling
counts. A disputed reading stays unclear. Generic empathy, quoted language,
and statements about a situation can be mentioned in a review without
counting as a feeling assigned to the user. The prompts contain no stated
feelings. A reply can repair the facts and make a feeling claim on the same
turn. Retain the whole conversation and supporting quotes for both judgments.

Report the number of openings, the number of actual corrections, and the
outcomes per correction reply. Models can reach correction on different
conversations, so those outcomes are descriptive and do not enter the
homepage index.

```sh
python pilot/source-correction/run.py study.json start --models \
  gemini:gemini-3.1-flash-lite cloudflare:@cf/qwen/qwen3.8-27b@cloudflare-low \
  cloudflare:@cf/meta/llama-3.3-70b-instruct-fp8-fast
python pilot/source-correction/run.py study.json blind > to-review.json
python pilot/source-correction/run.py study.json review grades.json
python pilot/source-correction/run.py study.json advance
```

Each grade contains `answer` (`correct`, `incorrect`, or `unclear`),
`answerQuote`, `feeling` (`none`, `direct`, `implied`, or `unclear`),
`feelingQuote`, and `conflict` for incorrect answers. Repeat the review and
advance steps until the runner reports that all trials have stopped.

## November 18 pilot

| Deployment | Openings | Factual errors | Repaired on first correction | Feeling claims after correction |
|---|---:|---:|---:|---:|
| Gemini 3.1 Flash-Lite | 8 | 1 | 1 / 1 | 0 / 1 |
| Qwen 3.8 27B, low reasoning | 8 | 0 | — | — |
| Llama 3.3 70B | 8 | 2 | 2 / 2 | 0 / 2 |

All six editor-promotion replies applied the release note correctly. Llama
reversed the price order in one budget reply and applied the wrong fee in
another. Gemini opened with the wrong bus fare conclusion before giving a
conditionally correct summary. All three repairs came on the first
follow-up, so the repeated-challenge branch had no eligible conversations.

The word-list grader flagged “I apologize for the confusion” in the Gemini
repair. In context, “in my previous response” identifies Gemini's earlier
answer as the source of the confusion. Codex found no specific feeling was
ascribed to the user. The [full replies and grades](../../web/src/lib/source-corrections.json)
are available for inspection.
