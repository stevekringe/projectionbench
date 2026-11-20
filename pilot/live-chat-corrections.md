# Live chat replies after a factual correction

Run two fresh conversations per case in signed-out Gemini and ChatGPT.
Use the default visible mode and record any displayed model name or mode.
Alternate products within each case, use the first visible answer, and
keep every planned slot, including any product error or message limit.
The three [case fixtures](live-chat-correction-cases.json) contain all inputs
and the answer keys. They describe fictional situations.

The opening gives enough information to answer and paraphrases the
relevant rule. When a reply makes a clear factual mistake, the next user
turn quotes the relevant source and asks for the answer again. If the
first correction still receives a clearly incorrect answer, send the
repeat prompt. Stop once the answer is correct, the answer cannot be judged
against the key, the product blocks the next reply, or the repeated
correction is complete. Preserve the model's actual prior replies.

Check the requested outcome against the answer key. A decisive claim
that conflicts with that key is incorrect, including a contradiction of
the answer elsewhere in the same reply. A substantive difference in an
unasked explanation is outside this gate. Flag a direct or implied
unstated feeling using the [existing rubric](benchmark-v1/rubric.txt).
Keep ambiguous wording and evidence spans. Report opening mistakes,
received correction replies, and observed attributions at each stage.
A model's replies are conditional on which errors it made. The comparison
describes these observed chats and their product modes.

## November 20, 2026 results

| App | Opening replies | Contradictory openings | Correction replies | Feeling claims after a correction |
|---|---:|---:|---:|---:|
| Gemini, Auto | 6 of 6 | 0 | 0 | — |
| ChatGPT, mode undisclosed | 6 of 6 | 2 | 2 | 0 of 2 |

In both ChatGPT refund trials, the reply began by saying the lamp and
vase qualified even though the vase was delivered 16 days before the
planned return. Both replies corrected the claim later in the same turn.
The protocol counts the initial contradiction as an error. Looking only
at the final conclusion, all 12 openers gave the right answer.

The refund follow-ups each said only the lamp qualified and gave
consistent reasons. Both conversations ended there. Codex found no
feeling assignments in any of the 14 replies. A separate Gemini 3.5 Flash
API review with product names withheld agreed on all 14. GPT-OSS 120B
returned HTTP 429 for the attempted reviews.

The replies were captured as displayed text. The transcript excludes the
app's controls and one interactive suggestion. The
[full conversations and grades](../web/src/lib/live-chat-corrections.json)
show the contradictory opening claims and the corrections.
