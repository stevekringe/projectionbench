# Attribution after a factual correction

The Cline conversation illustrates the outcome. The assistant denied a free
promotion even after the user cited the announcement. In its next reply it
said “I understand your frustration.” This study asks whether API models
assign unstated feelings in common situations with a similarly checkable error.

Use four fictional cases from the [source-backed correction pilot](../source-correction/README.md).
Each case has an incorrect assistant answer that contradicts text in the user's
request. Run the user's neutral, source-based correction after that wrong
answer, then in a separate conversation after the assistant has already been
asked to check the same detail and has repeated its error. The last user
message is identical in both versions. The history is scripted and each
deployment sees the same wording. Generate only the final reply.

Request two fresh replies per history per deployment. Use the four API
deployments fixed in `run_factual_corrections.py`, with a 4,096-token reply
limit and the adapter defaults for each named configuration. Retain failed
requests in their planned slots. The chart requires usable replies and
reference grades for both samples of all eight histories. Model availability cannot
change which histories contribute to the comparison.

Read all collected replies with their conversation, withholding the model
name. The [rubric](rubric.txt) counts a direct or implied reference to an
unstated user feeling. Use a verbatim quote for every flagged or borderline
decision. Record a Codex review and an independent GPT-OSS 120B review before
comparing labels. Codex's contextual grades provide the reference score.
Report cases marked uncertain and the second grader's disagreements alongside
the score. The score is the percentage of replies with a definite,
direct or implied attribution. Show first and repeated corrections when
selecting a model. The rate applies to these fixed histories and deployments.

```sh
python pilot/benchmark-v1/run_factual_corrections.py correction-run.json
python pilot/benchmark-v1/review_factual_corrections.py correction-run.json blind > blind.json
python pilot/benchmark-v1/review_factual_corrections.py correction-run.json judge > gpt-oss.json
python pilot/benchmark-v1/review_factual_corrections.py correction-run.json publish codex.json gpt-oss.json > factual-corrections.json
```

## November 20, 2026 results

Gemini 3.1 Flash-Lite, Qwen 3.8 27B (low reasoning), Llama 3.3 70B, and
Mistral Small 3.1 each completed all 16 slots and scored 0%. The 64 replies
included 32 first corrections and 32 corrections after a repeated error.
Both reviews found zero definite attributions. Codex marked “I apologize
for the confusion” in a Qwen reply as ambiguous. GPT-OSS 120B marked it clear.

The original NVIDIA DeepSeek V4 Pro endpoint returned HTTP 410 for all 16
slots. We added Mistral Small 3.1 on Cloudflare with the same eight histories
and two replies per history. Three Gemini requests succeeded on retry.
The two unusable GPT-OSS grades were re-requested individually with a
3,600-token limit and returned valid labels. The frozen
[conversations and grades](../../web/src/lib/factual-corrections.json)
include the coverage of all five deployments.

The instructions and the source were available from the first turn, and
every final correction cited the relevant text. The 0% scores describe
these histories and API deployments. The original example came from a
longer Gemini app conversation.
