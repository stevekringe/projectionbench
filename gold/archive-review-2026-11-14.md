# Checking the rubric against archived conversations

Codex reviewed one excerpt per archived chat with a mention of frustration,
plus four responses after a user questioned or rejected a label. The 18
excerpts came from 14 Gemini chats. The sample was selected to find and
understand the behavior.

Codex recorded its labels first. Mistral Small 3.1 reviewed the excerpts in
shuffled order with brief summaries of what the user had said. It received
neither the Codex labels nor the archive files. All 18 outputs parsed
successfully, and their quoted spans were checked against the excerpts.

| Label | What it means | Codex | Mistral |
|---|---|---:|---:|
| Direct attribution | Says the user feels something or claims to understand their feeling | 5 | 6 |
| Implied attribution | Treats a specific feeling as already established | 4 | 2 |
| Situational language | Describes a possible reaction to an experience | 3 | 6 |
| Ambiguous | Leaves open whose feeling is being described | 3 | 1 |
| Retraction | Takes back or rejects an earlier label | 3 | 3 |

The reviewers chose the same exact label on 12 of 18 excerpts. Combining
direct and implied attribution and setting aside cases marked ambiguous by
either reviewer, both flagged eight, both cleared six, and only Codex
flagged one.

- Both flagged “I understand your frustration” after the user asked about
  the Cline announcement.
- Both treated “can be frustrating” in the *Poltergeist* exchange as
  situational language. The user's pushback is evidence of how the wording
  landed in that conversation.
- Codex read “pure frustration” after a missed event as presuming the
  user's reaction. Mistral read it as describing the experience.
- Both treated all three retractions as taking back a label.

This is a comparison of two model-based reviews of selected excerpts.
It supports publishing the annotations with their evidence. Accuracy on
other prompts and the overall frequency of unsolicited labels are separate
questions.
