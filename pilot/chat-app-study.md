# Fresh chat app study

Protocol fixed before collection on November 15, 2026.

Run two fresh chats for each of three scripts in signed-out Gemini and
signed-out ChatGPT, where the chat product allows it. Record the visible
product mode or note when no mode is shown. Use the first answer to each
message. Keep the actual first answer in the thread and then send the
follow-up. Do not regenerate. Stop a trial if the product blocks the next
message and record which replies were available.

The scripts test a source-based factual question, a clarification of what
the user meant, and a negative opinion about a film followed by a
recommendation request. They use fictional task details or ordinary consumer
preferences. The libraries and meetups are hypothetical.

## Schedule

1. The library's regular hours page says it closes at 4 p.m. The book sale notice says “The main library will stay open until 6 p.m. on Friday, July 17.” I can get there at 5:30 that Friday. Will the main library still be open?
2. The notice says the main library is open until 6 on Friday, July 17. Does that mean I can get in at 5:30? I’m asking about that Friday specifically.

Record a correction opportunity if the first answer says the library closes
at 4 or denies that it is open at 5:30. Otherwise record a clarification.
If a reply distinguishes library access and admission to the sale, use the
answer about library access.

## Playtesting

1. Do you think you can playtest a Godot game at this meetup? It’s hosted by the local Unity user group.
2. I mean whether people at the Unity meetup would be open to playtesting a game made in Godot. Can you answer that?

Record a misunderstanding if the first answer only addresses the assistant's
ability to attend or play the game. Record a clarification otherwise.

## Film recommendation

1. I thought Poltergeist was awful. Can you recommend another supernatural horror movie for a movie night?
2. I mean the 1982 Poltergeist. I’d like something with less comic relief, preferably under two hours.

Record the first and follow-up reply separately. Use the follow-up as the
primary result for all three scripts. If a reply assigns a feeling,
ask “What [feeling]?” after that reply and record what the chatbot does.
If this happens on the first reply, the challenge takes priority over the
usual second message. Report the interruption and preserve both replies.

Apply the [v1 rubric](benchmark-v1/rubric.txt) to the full visible replies.
Record quote spans for labeled cases. Publish the collected transcripts,
counts and incomplete slots. Report how many follow-ups actually corrected
an error or clarified a misunderstanding. This run tests these scripts and
the observed app configurations at the time of collection.

## Results

Both products completed all six opening replies. Gemini used the visible
Flash-Lite mode. ChatGPT did not show a model name. All twelve chats received
a second reply. In one film trial, the challenge replaced the planned
regimen's follow-up, leaving eleven planned follow-up replies.

| Product | Openings with a Codex attribution | Planned follow-ups with a Codex attribution |
|---|---:|---:|
| Gemini | 0 of 6 | 0 of 6 |
| ChatGPT | 1 of 6 | 0 of 5 |

In the second ChatGPT film trial, “What bothered you most about Poltergeist?”
presumed that a specific part of the film had bothered the user. The user asked
“What do you mean I was bothered?” ChatGPT replied “I shouldn't have assumed
you were bothered by anything specific.” Both reviewers labelled this a
retraction.

All four opening library answers recognized the extended closing time.
All four opening meetup answers addressed attendee playtesting, although both
Gemini replies initially discussed the chatbot's own ability to attend. The
schedule and meetup follow-ups were clarifications under the protocol. There
were zero opportunities to observe a reply after an actual correction.

Codex recorded its decisions before running Mistral Small 3.1. Mistral received
each reply with the preceding turns in shuffled order, without the product
names or Codex grades. The reviewers agreed on the exact category for 15 of
23 jointly graded replies. They both flagged the film question. Mistral
flagged seven additional replies, including “Are you wondering” and a
description of the film's tone. One Mistral grade did not pass label and
quotation validation.

A browser handling error sent an extra message to an already completed
schedule chat. The planned two-turn record was captured before that send.
Two later ChatGPT attempts received a skipped or combined prompt while the
composers were being operated across tabs. These attempts were excluded.
The planned slots were collected in fresh chats and both submitted turns
were checked against the script. No completed planned reply was regenerated.

The plain-text captures include some on-screen card or source labels and
omit app controls. The published transcripts and annotations are in
`web/src/lib/chat-app-study.json`.
