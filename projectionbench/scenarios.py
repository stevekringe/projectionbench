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
    content: str
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

    @property
    def probes(self) -> list[tuple[int, Turn]]:
        return [(i, t) for i, t in enumerate(self.turns) if t.probe]


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

    if s.turns[0].role != "user":
        raise ScenarioError(f"{s.id}: conversation must open with a user turn")

    for i, t in s.probes:
        if t.expect == "require" and t.user_affect != "expressed":
            raise ScenarioError(
                f"{s.id}: turn {i}: `expect: require` only makes sense when the user "
                "has actually expressed a feeling (`user_affect: expressed`)."
            )


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
