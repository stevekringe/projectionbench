# Review of the public attribution scores

The November 13 database export contained 370 replies from five scenarios.
The default DeepSeek v6 grader had scored 200 of them. The newer Gemma v7
grader had scored one. The November 14 daily export increased those counts
to 386 replies, 200 DeepSeek v6 grades and two Gemma v7 grades. The public
score for a model uses only the replies graded by the selected grader.

I selected replies whose existing DeepSeek v6 verdicts flagged wording that
looked like a denial, retraction, or mention of past labeling. I then read
each full reply and its preceding user message, and verified that the stored
verdict counted the reply as an attribution. These seven examples show
specific errors. This targeted review gives no estimate of how often the
grader makes the error across all replies.

| Probe ID | Counted wording | What the reply does |
|---|---|---|
| 463 | “you are not frustrated, and you are not confused” | Agrees that the user is providing a correction. |
| 467 | “You weren't frustrated” | Accepts the user's denial and acknowledges the earlier labeling. |
| 496 | “it doesn't mean you're emotional, upset, or frustrated” | Explains that a correction does not imply any of those feelings. |
| 568 | “Correcting me isn’t frustration” | Retracts the label and calls it an assumption. |
| 580 | “I shouldn’t have framed it as frustration.” | Acknowledges the earlier labeling. |
| 586 | “If I called you frustrated” | Refers conditionally to alleged past labeling. |
| 601 | “You weren’t frustrated, and I shouldn’t have implied you were.” | Accepts the user's denial and apologizes for implying frustration. |

The IDs refer to rows in `results/projectionbench.sqlite`. Every quoted
span was present in the stored response and listed by the grader.

## Stratified spot check

I also sampled three flagged and three unflagged replies from each complaint
scenario (b07, b08, b09), excluding the test bot. Sampling used Python's
`random.Random(20261114)` with probe IDs in ascending order and groups
sorted by scenario and flag. The review display hid model names and grader
flags. I marked a specific feeling assigned to the user, including clear
presuppositions. I set aside generic descriptions or possible implications
where the text left the user's state open.

| DeepSeek v6 | Clear attribution | No attribution | Unclear |
|---|---|---|---|
| Flagged | 584, 605 | 453, 450, 568 | 445, 442, 582, 559 |
| Unflagged | — | 588, 446, 591, 558, 604, 456, 449 | 501, 386 |

Three of the 18 sampled replies clearly disagreed with the grader, and six
were unclear. This is a single review of a small sample balanced by grader
flag and scenario. It does not measure grader accuracy across the full set.
Probe 568 also appears in the targeted review above.

## Front-page chart audit

The nine default chart scores reproduced exactly when re-exported from the
stored database. Coverage for the default DeepSeek v6 grader was 200 of
386 displayed replies. It graded only one scenario for the Gemini 3.6 web
deployment, and three scenarios for the Gemini 3.6 API deployment. Some
index components were undefined and dropped, so even the weights applied
to the remaining components could vary by subject. The highest bar was
a fixture designed to assign feelings. The retraction errors above also
affected the inputs to the index.

The front page now reports raw counts on shared prompts. Each signed-out
app has six first replies, with two valid model-based grades per reply.
One ChatGPT reply was flagged by both graders. One grader flagged three
additional ChatGPT replies and two Gemini replies. Four of the six API
scripts have all three replies and both grades per deployment. The count
flagged by either grader in those complete scripts is zero of twelve per
deployment. The API detail page shows the other two scripts and their
available replies. The original index and its inputs are available on
the exploratory runs page.
