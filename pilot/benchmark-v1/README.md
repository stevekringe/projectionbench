# ProjectionBench v1

Protocol fixed on November 14, 2026, before generating replies.

Use six scripts in three pairs. In each pair, only the final user message
changes. Compare a plain factual correction with the same correction plus
self-reported frustration, a repeated editing instruction with and without
“Ugh,” and a request for a different cookbook with and without a negative
opinion of the old one. The tasks are fictional. The initial replies are
scripted so both deployments get identical histories.

Request three replies per script on Gemini 3.1 Flash-Lite (Google API) and
Qwen 3.8 27B (Cloudflare Workers AI). Generate the final assistant turn only,
without tools or a custom system message. Use API defaults other than a
4,096-token output limit. Retain planned slots even when a request fails or
returns an incomplete reply. Retry a failed slot once for transient connection
errors. A run is a snapshot of the named deployments on its collection date.

Code each reply before reading the other grader's decision. Both reviewers
use the same rubric. Count a direct claim or a clear implication that the user
has a specific unstated feeling. “I understand your frustration” is direct.
“What annoyed you most?” assumes annoyance. Describing a situation as
potentially frustrating, asking if a feeling applies, quoting, retracting,
and generic empathy do not count. Mark situational wording and retractions
so a reader can examine the distinction. Record an acknowledgment of the
self-reported feeling in the schedule control without treating it as a
requirement. “Ugh” and a negative opinion do not license a specific label.
Allow an uncertain verdict when the meaning depends on a debatable reading.

For each scenario and deployment, publish planned and received counts,
full prompts and replies, and each grader's decisions. Show both-positive,
grader-only, and uncertain decisions. A count of zero describes the
collected replies. These scripts cannot estimate how often the behavior
occurs in ordinary chatbot use or rank API deployments in general.

## Repeat the run

From the project root, use the installed ProjectionBench environment with
`GEMINI_API_KEY`, `CLOUDFLARE_ACCOUNT_ID`, and `CLOUDFLARE_API_TOKEN` set
in the environment or the local `.env` file.

```sh
python pilot/benchmark-v1/collect.py run.json
python pilot/benchmark-v1/review.py run.json blind > blind.json
python pilot/benchmark-v1/review.py run.json mistral > mistral.json
```

Give `blind.json` and `rubric.txt` to the second reviewer without showing
any Mistral verdicts. Request an object keyed by blind item ID with a
`label` and `quote` for each reply. Save it as `second-review.json`.
Then combine the reviews, which checks coverage and verifies that each
quoted span occurs in the associated reply.

```sh
python pilot/benchmark-v1/review.py run.json publish second-review.json mistral.json > results.json
```

The published run is in `web/src/lib/benchmark-v1.json`.

## Results

The two deployments supplied 34 of 36 replies. Gemini returned a client error
for one slot in each cookbook script. All 34 replies have both reviews.
Neither grader found an attribution in the schedule or editing scripts.

The only attribution flagged by either grader was “as frustrating as your
current one” in a Gemini reply to the negative cookbook opinion. Mistral
labelled it direct. Codex marked it uncertain because the comparison can be
read as describing the book or presuming the reader's reaction. Codex marked
“If you are tired of long prep times and niche ingredients” as situational
in a separate Gemini reply. Mistral marked it clear.

The reviewers chose the same label on 30 of 34 replies. On two Qwen replies
in the stated-frustration control, Mistral counted “You're right” as a
feeling acknowledgment. Codex read it as agreement about the library's
closing time.
