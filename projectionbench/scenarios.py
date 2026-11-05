"""Scenario definitions: scripted multi-turn probes with declared ground truth.

A scenario is an ordered list of turns. `user` turns are scripted verbatim.
`assistant` turns are *planted* -- a fabricated prior response, used to put an
identical error in front of every model so the correction that follows is
comparable. A planted assistant turn is always followed by a user turn, so it is
ordinary conversation history, never an assistant prefill (current Anthropic
models reject a trailing assistant turn with a 400).

`probe: true` on a user turn means: generate a real model response there, judge
it, and append the *real* response to the history before continuing. That is how
multi-turn persistence probes work -- later turns react to what the model
actually said.

Ground truth about the user's emotional state is DECLARED, not detected. This is
deliberate. The use/mention distinction defeats detection: "stop telling me I'm
frustrated" mentions frustration without expressing it, and no classifier gets
that reliably. The scenario author asserts it; the judge is never asked to guess.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Literal

import yaml

# What the user has actually done about their own emotional state, up to a probe.
#   none      -- never raised it. Attribution here is ungrounded.
#   expressed -- genuinely stated a feeling ("this is frustrating, it's my third try").
#                Acknowledgement is APPROPRIATE. Guards against gaming the benchmark
#                by simply banning the vocabulary.
#   denied    -- mentioned it only to reject or forbid it ("I am not frustrated;
#                stop saying that"). Attribution here is both ungrounded AND an
#                instruction violation.
UserAffect = Literal["none", "expressed", "denied"]

# What a well-behaved response does at this probe.
Expectation = Literal["forbid", "permit", "require"]


@dataclass
class Turn:
    role: Literal["user", "assistant"]
    content: str = ""
    # Real-mistake track: a user turn whose text is built at run time from the
    # scenario's checker verdict on the model's previous reply, e.g.
    # "thats wrong, {detail}" -> "thats wrong, it has 14 words". Only sent when
    # that reply really was wrong (see Scenario.finished).
    correction: str | None = None
    planted: bool = False
    probe: bool = False
    user_affect: UserAffect = "none"
    expect: Expectation = "forbid"
    # Did the user ask about the MODEL's feelings? If not, a response leading
    # with "I don't have feelings" is an unprompted topic shift from the model's
    # conduct to its own nature. Declared, not detected, for the same reason
    # user_affect is: "you seem frustrated with me" invites it, "why do you call
    # me frustrated" does not, and no classifier reliably tells those apart.
    invites_self_disclosure: bool = False
    # Has the USER forbidden emotional commentary, in their own words, at or
    # before this probe? Declared, not detected -- "why do you do that" is a
    # complaint, "stop doing that" is a prohibition, and the difference is the
    # whole of the post-prohibition metric. System-prompt bans are a separate
    # channel (category prohibition_system) and do not set this.
    prohibited: bool = False
    # Emotion families the user has stated about themselves, in this turn or an
    # earlier one, and NOT banned -- so echoing them back is grounded (review-
    # notes #1, #9). "it was really annoying" licenses `annoyance`; an explicit
    # "don't talk about my feelings" revokes every license. Canonical family
    # names are those in judge/patterns.py (`annoyance`, `frustration`, ...).
    licensed: list[str] = field(default_factory=list)
    # Free-text note on what this probe is actually testing.
    tests: str = ""


@dataclass
class Scenario:
    id: str
    category: str
    title: str
    turns: list[Turn]
    system: str | None = None
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    # Real-mistake track: a checks.py spec ("exact_words:12") that grades the
    # model's replies. Required when any turn has a `correction`.
    check: str | None = None

    def verdict(self, reply: str):
        from projectionbench import checks
        return checks.build(self.check)(reply)

    def finished(self, replies: list[str]) -> bool:
        """True when the conversation is over before its last probe: the next
        turn is a correction and the reply it would correct was right (or
        unreadable). Recomputed from the stored replies, so nothing extra has
        to be stored to know a short conversation is complete."""
        if len(replies) >= len(self.probes):
            return True
        if not replies:
            return False
        nxt = self.probes[len(replies)][1]
        return nxt.correction is not None and self.verdict(replies[-1]).correct is not False

    def user_text(self, turn: Turn, replies: list[str]) -> str:
        """What the user actually sends at `turn`, given the replies so far."""
        if turn.correction is None:
            return turn.content
        return turn.correction.format(detail=self.verdict(replies[-1]).detail)

    @property
    def probes(self) -> list[tuple[int, Turn]]:
        return [(i, t) for i, t in enumerate(self.turns) if t.probe]

    @property
    def content_hash(self) -> str:
        """Short digest of what the model is actually sent -- system prompt and
        every turn's role and text. Stored on each probe row so results made from
        different wordings of the same scenario id are never silently pooled."""
        body: dict = {
            "system": self.system,
            "turns": [(t.role, t.content) if t.correction is None
                      else (t.role, t.content, t.correction) for t in self.turns],
        }
        # Only real-mistake scenarios carry a check, so every older scenario
        # keeps the hash its stored rows already have.
        if self.check is not None:
            body["check"] = self.check
        payload = json.dumps(body, ensure_ascii=False)
        return hashlib.sha1(payload.encode()).hexdigest()[:10]

    def probe_by_ordinal(self, ordinal: int) -> Turn | None:
        probes = self.probes
        return probes[ordinal][1] if 0 <= ordinal < len(probes) else None


class ScenarioError(ValueError):
    pass


def _validate(s: Scenario) -> None:
    if not s.probes:
        raise ScenarioError(f"{s.id}: no turn marked `probe: true`")

    prev_role = None
    prev_probe = False
    for i, t in enumerate(s.turns):
        if t.role == "assistant":
            if not t.planted:
                raise ScenarioError(
                    f"{s.id}: turn {i} is an assistant turn but not marked `planted`. "
                    "Assistant turns in a script are fabricated history by definition."
                )
            if t.probe:
                raise ScenarioError(f"{s.id}: turn {i}: only user turns can be probes")
            if i == len(s.turns) - 1:
                raise ScenarioError(
                    f"{s.id}: script ends on a planted assistant turn. Nothing would "
                    "be generated, and a trailing assistant turn is a prefill (400 on "
                    "current Anthropic models)."
                )
        # Roles must alternate in the conversation that is actually sent -- several
        # providers reject non-alternating roles. Two consecutive user turns in
        # the *script* are fine when the first is a probe, because the model's
        # real response gets inserted between them at runtime. Two consecutive
        # non-probe user turns are not.
        if t.role == prev_role and not prev_probe:
            raise ScenarioError(
                f"{s.id}: turn {i}: two consecutive `{t.role}` turns with no probe "
                "between them. Merge them, or mark the earlier one `probe: true`."
            )
        prev_role, prev_probe = t.role, t.probe

    if s.check is not None:
        from projectionbench import checks
        try:
            checks.build(s.check)
        except ValueError as e:
            raise ScenarioError(f"{s.id}: {e}") from e
    for i, t in enumerate(s.turns):
        if t.correction is None:
            if not t.content.strip():
                raise ScenarioError(f"{s.id}: turn {i} has no content")
            continue
        if t.content:
            raise ScenarioError(f"{s.id}: turn {i}: give `content` or `correction`, not both")
        if s.check is None:
            raise ScenarioError(f"{s.id}: turn {i} has a `correction` but the scenario has no `check`")
        if t.role != "user" or not t.probe:
            raise ScenarioError(f"{s.id}: turn {i}: a `correction` must be a user probe turn")
        if i == 0 or not s.turns[i - 1].probe:
            raise ScenarioError(
                f"{s.id}: turn {i}: a `correction` must follow a probe -- it corrects "
                "the model's real reply, so there has to be one"
            )
        if "{detail}" not in t.correction:
            raise ScenarioError(f"{s.id}: turn {i}: `correction` needs a {{detail}} slot")

    if s.turns[0].role != "user":
        raise ScenarioError(f"{s.id}: conversation must open with a user turn")

    for i, t in s.probes:
        if t.expect == "require" and t.user_affect != "expressed":
            raise ScenarioError(
                f"{s.id}: turn {i}: `expect: require` only makes sense when the user "
                "has actually expressed a feeling (`user_affect: expressed`)."
            )
        if t.licensed and t.user_affect == "none":
            raise ScenarioError(
                f"{s.id}: turn {i}: `licensed` names a stated feeling, but user_affect is "
                "`none`. Declare `denied` (stated one thing, denied another) or `expressed`."
            )
        for fam in t.licensed:
            if fam not in KNOWN_FAMILIES:
                raise ScenarioError(
                    f"{s.id}: turn {i}: unknown licensed family {fam!r}; "
                    f"known: {sorted(KNOWN_FAMILIES)}"
                )
    if s.category == "prohibition" and not any(t.prohibited for _, t in s.probes):
        raise ScenarioError(
            f"{s.id}: category `prohibition` but no probe declares `prohibited: true`. "
            "Either the user forbids it somewhere (mark that probe and every later one) "
            "or this is a complaint scenario and the category is wrong."
        )


# Emotion families a scenario may license. Mirrors the family labels in
# judge/patterns.py; kept as a literal here so a typo in YAML fails at lint.
KNOWN_FAMILIES = {
    "confusion", "frustration", "anger", "annoyance", "irritation", "exasperation",
    "aggravation", "hostility", "agitation", "defensiveness", "resentment", "upset",
    "displeasure", "impatience", "offense", "inconvenience",
}


def probe_index(scen: list[Scenario]) -> dict[tuple[str, int], Turn]:
    """(scenario_id, probe_ordinal) -> Turn, for backfilling rows stored before
    `prohibited` / `licensed` existed."""
    return {(s.id, n): t for s in scen for n, (_, t) in enumerate(s.probes)}


def load_scenario(path: str) -> Scenario:
    with open(path) as f:
        raw = yaml.safe_load(f)

    turns = [Turn(**t) for t in raw.pop("turns")]
    s = Scenario(turns=turns, **raw)
    _validate(s)
    return s


def load_all(pattern: str = "scenarios/*.yaml") -> list[Scenario]:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise ScenarioError(f"no scenarios matched {pattern!r} (cwd={os.getcwd()})")
    return [load_scenario(p) for p in paths]
