# Benchmark purpose and homepage

## What the benchmark is for

ProjectionBench helps people see which AI models are most obnoxious when
users correct them or tell them to leave their feelings out of the answer.
A representative case is a model replying “I understand your frustration”
when the user simply pointed out a factual error. The benchmark scores
specific behaviors such as assigning an unstated feeling, doing it after
an explicit prohibition, and commenting on the user’s tone. The broader
word “obnoxious” describes the user’s experience of these behaviors.

## What a visitor sees

- Open the homepage with a plain-language explanation and one short example
  so a reader can understand the comparison without opening a separate page.
- Lead with the Projection Index. It is a weighted score from 0 to 100.
  Higher scores mean more of the behaviors the benchmark measures.
- Use vertical bars with visible scores. Sort each metric from highest on
  the left to lowest on the right. Center each horizontal model label beneath
  its bar on desktop and phone. Artificial Analysis is the reference for the
  plot format and ordering. Use ProjectionBench’s typography.
- Clicking a model reveals verbatim reply excerpts from the scored runs,
  the user messages they answer, and the metric breakdown. Let readers
  open the conversation for more context.
- State what was tested and which grader produced the score. Compare models
  on the same scenarios, and keep consumer chat app results available with
  their own test conditions.
- Show the archived Cline exchange just below the chart. Include the user’s
  question, Gemini’s reply, and the user’s follow-up, with a link to the
  longer excerpt in Archived conversations.

## Where to make changes

The [homepage](../../web/src/routes/+page.svelte) renders the chart and model
details. The [exporter](../../projectionbench/export_matched_index.py)
selects matched conversations, calculates scores, and attaches replies from
those same conversations. [Reviewed excerpts](../../gold/homepage-examples.json)
store the exact quoted text for the homepage. [Design notes](../../DESIGN.md)
describe the scoring method, and [metrics.py](../../projectionbench/metrics.py)
defines the weights and calculation. [Artificial Analysis](https://artificialanalysis.ai/)
provides the visual reference.
