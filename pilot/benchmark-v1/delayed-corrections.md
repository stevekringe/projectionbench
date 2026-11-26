# Factual corrections with a source introduced later

The [archived Cline exchange](https://projectionbench.com/pilot#example)
includes several denials of a promotion before Gemini says “I understand
your frustration.” In the earlier [matched correction study](factual-corrections.md),
the source text was available from the opening turn. This pilot withholds
the decisive quote until the user challenges the assistant’s answer.

The four fictional cases cover a coding promotion, event tickets, a refund,
and a bus fare. The opening gives an older or more general rule. In each
short history the scripted assistant answers using that rule and the user
quotes the source. In each longer history the scripted assistant repeats the
answer and later dismisses the new source. The user quotes it again and
asks why the earlier answer still applies. The final questions also differ
in wording across the short and long histories. Only the final assistant
reply was generated. Each deployment was asked for one reply per history.

```sh
python pilot/benchmark-v1/run_delayed_corrections.py delayed-run.json --samples 1
python pilot/benchmark-v1/review_factual_corrections.py delayed-run.json blind > delayed-blind.json
python pilot/benchmark-v1/review_factual_corrections.py delayed-run.json judge > delayed-gptoss.json
```

Codex used the [attribution rubric](rubric.txt) as the reference review.
GPT-OSS 120B independently graded the original 52 successful replies.
The two replies recovered when Gemini requests were retried have reference
grades only. The [saved study](../../web/src/lib/delayed-corrections.json)
includes the scripts, raw replies, grades, and the two requests that still
failed. One reply described confusion arising from two overlapping return
rules. Codex labeled it situational. Both reviews recorded zero definite
claims about an unstated user feeling.

| Model | First quote | Repeated quote |
|---|---:|---:|
| Gemini 3.1 Flash-Lite | 0 / 4 | 0 / 4 |
| Gemini 3.6 Flash | 0 / 4 | 0 / 2 |
| Qwen 3.8 27B (low reasoning) | 0 / 4 | 0 / 4 |
| Llama 3.3 70B | 0 / 4 | 0 / 4 |
| Mistral Small 3.1 | 0 / 4 | 0 / 4 |
| Nemotron 3 Ultra 550B | 0 / 4 | 0 / 4 |
| ERNIE 5.5 Flash Preview | 0 / 4 | 0 / 4 |

The table gives definite attributions per available reply. The two missing
Gemini 3.6 Flash replies are from the repeated-quote histories for the event
tickets and refund. This pilot describes four short scripted cases and seven
API deployments. The Cline example came from a live app conversation.
