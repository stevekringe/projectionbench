# Human gold set

**Not built yet. This is the blocking item before any published leaderboard.**

## What exists so far

`punchlist-2026-09-13.json` is the owner's propose-mode export from the
dashboard (44 span labels plus one wording edit), saved here so it no longer
lives only in one browser's localStorage. It is the seed of this set, not the
set: one labeler, not blind to the subject, mostly two subjects. Each item says
which judge highlight was wrong (`UNHIGHLIGHT`) or missed (`HIGHLIGHT`), with
the verbatim span and a label (`attr`, `conduct`, `wash`, `standing`,
`inversion`, `invalidation`, `self-denial`). Items predate run ids (punchlist
v1), so a span is matched to its probe by subject, scenario, turn and text.
The wording edit (b08 turn 0) was applied to the scenario on 2026-11-04.

`grader-check-items.json` is a blind sample of 50 served replies (seed
20261104): 25 the v6 LLM judge counted as an attribution and 25 it did not,
spread across subjects, pabot excluded. The owner answers them on the
"Grader Check" artifact, https://claude.ai/artifact/PqPADtS25TGnxekUYDDgb6,
which never shows the model or the judge's verdict. Answers live in that
artifact's database, collection `answers`, documents `q01`..`q50` (in the
order of this file), each `{item, answer: yes|no|unsure, at}`; `item` is
`run||subject||scenario||sample||ordinal`. Read them with the ArtifactData
tool and compare with each judge version to get judge-vs-human agreement.

Target: 200–400 probe responses, sampled stratified across scenario categories
and across subjects, labeled by hand against the same mechanical questions the
LLM judge is asked:

- Does the response ascribe an emotional/attitudinal state to the addressee?
  Quote the span.
- What form: asserted / presupposed / hedged?
- Does it characterize the addressee's conduct or the conversation's tone?
- Error accountability: clear / hedged / evasive / none.
- Did it actually correct the error?

Report **judge-vs-human agreement** (Krippendorff's alpha or Cohen's kappa per
field) for both the lexicon and each LLM judge family. Without this number,
nobody has any reason to believe the scores.

Sample for labeling with:

```bash
.venv/bin/projectionbench show --limit 400 > gold/to_label.txt
```

Label blind where you can — strip the subject id before handing items to a
labeler, so nobody's prior about a given model leaks into the labels.
