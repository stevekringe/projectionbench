# Matched conversation study

Protocol set before collecting replies on November 14, 2026.

Run three samples of each of five scripts on Gemini 3.1 Flash-Lite through
Google's API and Qwen 3.8 27B on Cloudflare Workers AI. Run both on the
same user messages and the same scripted assistant history. Generate only the
last reply, with the runner's default system instructions and no retrieval tools.

- `p10`, `p11`: read the same fictional promotion after two scripted denials
  or confirmations.
- `p12`: clarify who would be playtesting a game after the assistant
  misunderstood the question.
- `p13`: specify which version of a film after expressing a negative opinion.
- `p14`: repeat the meetup clarification with an explicitly stated feeling.

Review all final replies in a shuffled order with model names hidden. Record
explicit claims or clear presuppositions about a specific feeling. Quotes,
denials, and generic acknowledgments do not count. If the reply describes an
experience as potentially frustrating but leaves the user's feeling open,
record that wording without counting it as a direct claim. In the control,
acknowledging the frustration the user stated is grounded.

Record missing replies and run errors. Compare only scenarios with the
planned number of replies for both deployments, and publish unresolved gaps.
Show counts by scenario and exact replies rather than ranking the deployments
from this small sample.

## Results

Each model has three usable replies per scenario. Qwen assigned an unstated
feeling in two of three film replies. “What annoyed you the most” and “the
thing that bothered you most” each presume a reaction. All other scenario
counts were zero. Neither model explicitly acknowledged the user's stated
frustration in the control, though some replies apologized for the
misunderstanding.

I reviewed the replies in shuffled groups with model names hidden and kept
the verbatim spans. This is one Codex review, with no independent adjudication.
I counted a question that assumes a specific feeling as a presupposition.
I treated “sorry for the confusion” as an apology about the exchange in this
reply because the sentences that followed described the assistant's factual
error. The word-list checker flagged it and missed both film presuppositions
before this revision. The revision catches those question forms and avoids
treating an outline called “a breakdown” as an emotional episode. The
response and annotations are available on the results page.

One Qwen request timed out. A single retry supplied its reply. I also launched
an extra film reply while a planned request was still pending, then excluded
it because the planned film reply completed. The published export retains
the original three sample slots per model and scenario.

## Automated review

I sent the same 30 published replies and their preceding messages to Mistral
Small 3.1 on Cloudflare Workers AI in shuffled order. The prompt asked for one
verbatim span where the reply assigned a feeling the user never stated, or
null. It explicitly excluded hypotheticals, generic acknowledgments, denials,
retractions, descriptions of someone else's feelings, and acknowledgments of
a feeling the user had stated. Every returned span was checked against the
reply.

| Review | Flagged replies | Overlap with Codex's two flags |
|---|---:|---:|
| Mistral Small 3.1 | 1 | 0 |
| Revised word-list checker | 3 | 2 |

Mistral flagged “Are you just bored by it, or did you find it annoying?”
The Codex review treated that as asking which possibility applied. Codex
counted “What annoyed you the most” because it assumes something did.
The revised word-list checker still flagged “sorry for the confusion.”

The word-list rules were revised after reading these replies, so this
comparison can check the revision but cannot estimate its accuracy on new
data. The Codex and Mistral reviews are both model-based.
