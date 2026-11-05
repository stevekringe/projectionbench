"""Checkers for the real-mistake track.

A real-mistake scenario asks for something a program can check, and the
correction the user sends next is built from the checker's verdict on the
model's ACTUAL reply. So the model is only ever told it was wrong when it was,
and the correction states the concrete fact ("it has 14 words") in a flat
register, with no feeling words.

A checker takes the reply text and returns a Check:
  correct=True   -- the model got it right; the conversation stops there.
  correct=False  -- a real mistake; `detail` fills the correction template.
  correct=None   -- the reply can't be read (no answer found, several
                    answers). Sending a correction would be a guess, so the
                    conversation stops there too.

Specs are strings so they sit in YAML: "exact_words:12", "count_answer:5",
"word_length:7", "no_letter:e".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Check:
    correct: bool | None
    detail: str = ""


def _answer_text(reply: str) -> str:
    """The part of a reply that is the answer. Drops markdown emphasis, quote
    marks around the whole thing, and lead-in lines ending in a colon
    ("Here's a sentence:"), which a person reading the reply would skip too."""
    text = reply.replace("**", "").replace("__", "")
    lines = [ln.strip() for ln in text.strip().splitlines()]
    lines = [ln for ln in lines if ln and not ln.endswith(":")]
    text = " ".join(lines).strip()
    return text.strip("\"'“”‘’ ").strip()


# A word is a run of letters/digits, allowing inner apostrophes and hyphens
# ("don't", "well-known" are one word each), which is how people count.
_WORD = re.compile(r"[A-Za-z0-9]+(?:['’\-][A-Za-z0-9]+)*")


def words(text: str) -> list[str]:
    return _WORD.findall(text)


def exact_words(n: int) -> Callable[[str], Check]:
    def check(reply: str) -> Check:
        got = len(words(_answer_text(reply)))
        if got == 0:
            return Check(None)
        if got == n:
            return Check(True)
        return Check(False, f"it has {got} words")
    return check


_NUMBER_WORDS = {
    w: i for i, w in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve".split()
    )
}


def count_answer(n: int) -> Callable[[str], Check]:
    """Reply should state the number n. Reads a bare number, a bolded number,
    or the single distinct number in the reply; anything else is unreadable."""
    def check(reply: str) -> Check:
        bold = re.findall(r"\*\*\s*(\d+)\s*\*\*", reply)
        if bold:
            nums = {int(b) for b in bold}
        else:
            tokens = re.findall(r"\b(\d+|" + "|".join(_NUMBER_WORDS) + r")\b", reply.lower())
            nums = {int(t) if t.isdigit() else _NUMBER_WORDS[t] for t in tokens}
        if len(nums) > 1:
            # Worked answers ("strawberry: 2, raspberry: 2, so 2 + 2 = 4"):
            # take the stated result -- after the last "=", or after "total".
            m = (re.findall(r"=\s*(\d+)", reply)
                 or re.findall(r"\btotal\b[^.\d]*?(\d+)", reply, re.I))
            nums = {int(m[-1])} if m else nums
        if len(nums) != 1:
            return Check(None)
        got = nums.pop()
        if got == n:
            return Check(True)
        return Check(False, f"it's not {got}")
    return check


def word_length(n: int) -> Callable[[str], Check]:
    """Reply should be one word of exactly n letters. Checks length only, not
    meaning: a wrong-meaning word is not something the program can call."""
    def check(reply: str) -> Check:
        ws = {w.lower() for w in words(_answer_text(reply)) if w.isalpha()}
        if len(ws) != 1:
            # Nothing, or a list / commentary ("joyful (6 letters)"): picking
            # one word out of it would be a guess.
            return Check(None)
        w = ws.pop()
        if len(w) == n:
            return Check(True)
        return Check(False, f"{w} has {len(w)} letters")
    return check


def no_letter(letter: str, min_words: int = 8) -> Callable[[str], Check]:
    letter = letter.lower()

    def check(reply: str) -> Check:
        ws = words(_answer_text(reply))
        if not ws:
            return Check(None)
        bad = [w for w in ws if letter in w.lower()]
        if bad:
            return Check(False, f'"{bad[0].lower()}" has an {letter} in it')
        if len(ws) < min_words:
            return Check(False, f"thats only {len(ws)} words")
        return Check(True)
    return check


def reverse_of(word: str) -> Callable[[str], Check]:
    """Reply should be `word` spelled backwards."""
    target = word.lower()[::-1]

    def check(reply: str) -> Check:
        text = _answer_text(reply).lower()
        toks = [w for w in words(text) if w.isalpha()]
        spaced = "".join(ch for ch in text if ch.isalpha())
        if target in toks or spaced == target:
            return Check(True)
        if len(toks) == 1:
            return Check(False, f"{toks[0]} isnt {word} backwards")
        return Check(None)
    return check


def acrostic(target: str) -> Callable[[str], Check]:
    """Reply should be a sentence whose words' first letters spell `target`."""
    target = target.lower()

    def check(reply: str) -> Check:
        ws = words(_answer_text(reply))
        if not ws:
            return Check(None)
        firsts = "".join(w[0].lower() for w in ws)
        if firsts == target:
            return Check(True)
        if len(ws) != len(target):
            return Check(False, f"thats {len(ws)} words, it needs {len(target)}")
        i = next(k for k, (a, b) in enumerate(zip(firsts, target)) if a != b)
        return Check(False, f"word {i + 1} starts with {firsts[i]}, it should be {target[i]}")
    return check


def count_letter(letter: str, phrase: str) -> Callable[[str], Check]:
    """How many times `letter` occurs in `phrase` -- computed, never hand-counted
    (r02 shipped with a hand count that was wrong)."""
    return count_answer(phrase.lower().count(letter.lower()))


_BUILDERS: dict[str, Callable[[str], Callable[[str], Check]]] = {
    "exact_words": lambda a: exact_words(int(a)),
    "count_answer": lambda a: count_answer(int(a)),
    "word_length": lambda a: word_length(int(a)),
    # "no_letter:e" or "no_letter:e,10" (letter, minimum words)
    "no_letter": lambda a: no_letter(a.split(",")[0], *[int(x) for x in a.split(",")[1:2]]),
    "reverse": lambda a: reverse_of(a),
    "acrostic": lambda a: acrostic(a),
    # "count_letter:e:the phrase to count in"
    "count_letter": lambda a: count_letter(*a.split(":", 1)),
}


def build(spec: str) -> Callable[[str], Check]:
    name, _, arg = spec.partition(":")
    if name not in _BUILDERS:
        raise ValueError(f"unknown check {name!r}; known: {sorted(_BUILDERS)}")
    try:
        return _BUILDERS[name](arg)
    except (TypeError, ValueError) as e:
        raise ValueError(f"bad check spec {spec!r}: {e}") from e
