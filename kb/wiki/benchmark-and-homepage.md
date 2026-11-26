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
- Lead with the percentage of matched replies that assign an unstated or
  prohibited feeling. Higher rates mean more unwanted feeling assignments.
  Show the rate after an explicit denial or prohibition in its own chart.
  Report stated-feeling acknowledgment as a check on About.
- Offer After a factual correction as a percentage on matched
  source-based conversations. Require complete coverage for each model.
  Show what each model said after the first and repeated error.
- Use vertical bars with visible scores. Sort each metric from highest on
  the left to lowest on the right. Center each horizontal model label beneath
  its bar on desktop and phone. Artificial Analysis is the reference for the
  plot format and ordering. Use Allo at maximum roundness with a slashed zero
  and a double-storey lowercase a. The self-hosted font is Allo 1.1.0 with
  its `ROND` axis fixed at 100.
- Default to dark mode. The theme switch in the header remembers the visitor’s
  choice in their browser.
- Clicking a model reveals verbatim reply excerpts from the scored runs,
  the user messages they answer, and the metric breakdown. Let readers
  open the conversation for more context.
- State what was tested and which grader produced the score. Compare models
  on the same scenarios, and keep consumer chat app results available with
  their own test conditions.
- Require three complete conversations per model on each of the four
  attribution scenarios. Keep inference settings such as low reasoning
  under distinct model identifiers.
- Show the archived Cline exchange just below the chart. Include the user’s
  question, Gemini’s reply, and the user’s follow-up, with a link to the
  longer excerpt in Everyday chats.
- Use Conversations in the main menu for both Everyday chats, which shows
  examples from ordinary use, and Benchmark runs, which shows the tests and
  their replies and grades. List the excerpts at the top of Everyday chats.
- Link to the grader check from the chart. Give it a date, compare the same
  replies across graders, and quote reviewed mistakes from both graders.

## Where to make changes

The [homepage](../../web/src/routes/+page.svelte) renders the chart and model
details. The [homepage review](../../pilot/benchmark-v1/homepage-attribution.md)
documents how the matched replies are graded and exported.
[Design notes](../../DESIGN.md) describe the broader tests and historical
composite. [Artificial Analysis](https://artificialanalysis.ai/) provides
the visual reference.
