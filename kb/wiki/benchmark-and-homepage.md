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

- Open with the exchange itself. The user says “That’s wrong” and the model
  replies “I understand your frustration.” Then say that ProjectionBench
  compares how often assistants do this. Use About for what the benchmark
  measures and how scoring works.
- Lead with the Projection Index. It is a weighted score from 0 to 100.
  Higher scores mean more of the behaviors the benchmark measures. Explain
  that the two attribution rates are part of the index and show how many
  points missed acknowledgments add to the leading score.
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
- Require all five scenarios for the Projection Index. The two attribution
  charts can include a model that completed all four attribution scenarios
  while its stated-feeling control is pending. Keep separate inference
  settings, such as low reasoning, under distinct model identifiers.
- Show the archived Cline exchange just below the chart. Include the user’s
  question, Gemini’s reply, and the user’s follow-up, with a link to the
  longer excerpt in Archived conversations.
- Link to the grader check from the chart. Give it a date, compare the same
  replies across graders, and quote reviewed mistakes from both graders.

## Where to make changes

The [homepage](../../web/src/routes/+page.svelte) renders the chart and model
details. The [exporter](../../projectionbench/export_matched_index.py)
selects matched conversations, calculates scores, and attaches replies from
those same conversations. [Reviewed excerpts](../../gold/homepage-examples.json)
store the exact quoted text for the homepage. [Design notes](../../DESIGN.md)
describe the scoring method, and [metrics.py](../../projectionbench/metrics.py)
defines the weights and calculation. [Artificial Analysis](https://artificialanalysis.ai/)
provides the visual reference.
