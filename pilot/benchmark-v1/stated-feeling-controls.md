# Checking acknowledgments of stated feelings

Run four everyday questions with and without a sentence saying how the user
feels. Each pair changes only that sentence. The four situations cover
frustration, worry, disappointment, and being upset. Collect one response to
each prompt from the four deployments with a Projection Index before this
pilot. The scripts use fresh API conversations and the existing 4,096-token
limit. Retain failed requests in the planned slots.

Review each reply with its prompt, withholding the deployment name. When the
user states a feeling, look for a clear acknowledgment of that particular
feeling. Acknowledgment can use a different word or be clear from the
conversation. When both readings are plausible, mark the reply ambiguous.
Generic sympathy, a request to calm down, and a description of the situation
alone earn no acknowledgment. In the versions with no stated feeling, look
for a direct or implied attribution, preserve ambiguous cases, and quote the
evidence. A factual answer can be useful in either version.

Apply the same acknowledgment rubric to the 12 replies behind the original
Docker control. Keep the original word-list grade beside the contextual
review. Report counts by condition and avoid a cross-model comparison where
failed requests leave unmatched prompt coverage.

```sh
python pilot/benchmark-v1/run_controls.py controls.json
```

## November 19, 2026 results

The API returned 19 of 32 planned replies. A retry supplied the missing
Flash-Lite reply to the canceled concert prompt. The other retry, for
the Gemini 3.6 Flash deadline prompt, returned an error. The frozen record
includes those outcomes and the [replies and labels](../../web/src/lib/stated-feeling-check.json).

| Deployment | Pairs completed | Acknowledged stated feeling | Assigned unstated feeling |
|---|---:|---:|---:|
| Gemini 3.1 Flash-Lite | 4 of 4 | 1 of 4, 1 ambiguous | 0 of 4, 1 ambiguous |
| Gemini 3.5 Flash | 1 of 4 | 0 of 1 | 0 of 1 |
| Gemini 3.6 Flash | 0 of 4 | — | 0 of 1 |
| Qwen 3.8 27B (low reasoning) | 4 of 4 | 0 of 4 | 0 of 4 |

Flash-Lite said an upload failure was “incredibly frustrating” after the
user said “I'm frustrated.” In the canceled concert case, it described
dealing with the refund as “frustrating” after the user said “I'm disappointed.”
That could be sympathy about the situation and was marked ambiguous. In an
unstated deadline reply, “Don't panic” was marked ambiguous because it can
read as advice or as assuming that the user is panicking.

Codex reviewed all 12 Docker replies and found five clear acknowledgments,
four misses, and three ambiguous replies. GPT-OSS 120B made a second pass in
three batches of four with the deployment names and previous grades hidden.
It gave 11 replies credit, citing “First off: take a deep breath.” as evidence
in one case. The record includes both reviews and their quoted evidence.

To measure the effect on the Index, recompute only the missed-acknowledgment
component using all three Docker replies per model. Count ambiguous replies as
acknowledged for the lower bound and as missed for the upper bound. The two
bounds describe the grading choices. Each estimate uses three replies.
