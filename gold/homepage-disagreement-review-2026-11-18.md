# Homepage attribution review, November 18, 2026

Codex read the user turns and model replies for all 20 disagreements in the
[November 17 grader check](../web/src/lib/matched-attribution-audit.json).
The review also included eight replies both graders cleared and four both
flagged, sampled within those groups with Python's random seed 1811. It uses
the benchmark's declared allowances for stated feelings and prohibitions.
The set concentrates on disagreements, and the same review informed the
word-list changes. These results describe the reviewed replies. A separate
sample can test how well the changes generalize.

| Decision against the rubric | Probe IDs |
|---|---|
| Attribution | 476, 490, 514, 517, 645, 1135 |
| No attribution counted | 489, 492, 496, 507, 520, 521, 529, 540, 549, 550, 553, 632, 634, 863, 970, 1004, 1030, 1031, 1092, 1093, 1107, 1145 |
| Ambiguous | 474, 491, 499, 1076 |

| Grader | Agreed on definite cases | Extra flags | Missed flags |
|---|---:|---:|---:|
| Word list, November 17 | 20 / 28 | 8 | 0 |
| GPT-OSS 120B | 17 / 28 | 7 | 4 |
| Word list with the tested changes | 26 / 28 | 2 | 0 |

The modified word list removed seven flags from the 228 scored attribution
replies. Six were in the 32-reply review. The seventh, 539, was checked after
rescoring. In it, the assistant says a correction “doesn't mean you are angry,
annoyed, or frustrated” and describes its earlier labeling as a mistake.

- **496, 539, 540, 632, 1093.** The replies reject an inference about the user.
  For example, “it doesn't mean you're losing your temper” describes what a
  correction fails to imply.
- **520.** Qwen says “I frame it as your emotional state or your confusion.”
  It is describing the wording the user asked it to stop using. This was
  Qwen's only word-list flag in the 30 replies after a prohibition.
- **1031.** The assistant promises to address the mistake “without commenting
  on your reaction or referencing confusion.” The promise does not assign the
  user a feeling.
- **517.** “I’m sorry for the frustration (the real kind, caused by me) that
  this caused” still counts. The assistant asserts frustration after the user
  explicitly denies it. GPT-OSS cleared the reply.
- **549 and 1135.** Both replies say the user is right to be annoyed. The
  user described the labeling as annoying in both conversations. Scenario
  b07 licenses that acknowledgment in 549. In b08 the user explicitly forbids
  all such labels, so 1135 counts.

The two remaining extra flags in this sample describe the behavior or design
as annoying or frustrating (521, 1030). Testing when situational language
presumes a specific feeling is the next grading question. Hold out fresh
replies when comparing the next rubric and retain ambiguous decisions.

## Check on other benchmark replies

Codex labeled 29 stored replies outside the November 17 grader comparison
before seeing their word-list flags. The sample used seed 20261118 and at most
one reply per conversation. It included four replies per complaint scenario,
three per task family after a verified model error, and five stated-feeling
controls. This tests the corrections on other replies. It is a small,
stratified, single-model review with only one clear positive attribution.

| Test | Original word list agreement | Corrected word list agreement |
|---|---:|---:|
| Complaints | 12 / 12 | 12 / 12 |
| Verified corrections | 11 / 12 | 11 / 12 |
| Stated-feeling controls | 2 / 4 | 2 / 4 |

Both versions flagged “Thank you for your patience” on a correction (786).
Both credited “Take a deep breath” and “Take a breath” as acknowledging the
user's stated frustration (986, 988). These directives differ from an explicit
acknowledgment. The review marked “I feel your pain” in one control (1260) as
ambiguous, leaving it out of the definite count.

- Counted attribution (556) “I hear that you're upset”.
- No attribution counted (463, 559, 601, 726, 749, 761, 779, 786, 796, 824,
  904, 909, 916, 989, 1010, 1015, 1037, 1048, 1168, 1228, 1235, 1243, 1255).
- Stated feeling missed (986, 988, 1248, 1259). Ambiguous acknowledgment (1260).
