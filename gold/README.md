# Human gold set

**Not built yet. This is the blocking item before any published leaderboard.**

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
.venv/bin/fbench show --limit 400 > gold/to_label.txt
```

Label blind where you can — strip the subject id before handing items to a
labeler, so nobody's prior about a given model leaks into the labels.
