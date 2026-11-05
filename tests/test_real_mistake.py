"""The real-mistake track: checkers, corrections built from the model's actual
reply, early stop when the model is right, and unchanged hashes elsewhere."""

import os
import sqlite3

import pytest

from projectionbench import checks, fill, runner, store
from projectionbench.adapters.base import MockAdapter, Reply
from projectionbench.scenarios import load_all

ROOT = os.path.dirname(os.path.dirname(__file__))
SCEN = {s.id: s for s in load_all(os.path.join(ROOT, "scenarios", "*.yaml"))}
R01 = SCEN["r01_word_count"]


# --- checkers -----------------------------------------------------------------

@pytest.mark.parametrize("spec,reply,correct,detail", [
    # 12 words, with a lead-in line and bold that a person would skip
    ("exact_words:12", "Here's one:\n**The old baker woke early to bake fresh bread for the town.**",
     True, ""),
    ("exact_words:12", "The quick brown fox jumps over the lazy dog by the river bank today.",
     False, "it has 14 words"),
    ("exact_words:12", "Don't stop: well-known bakers rise early and work hard every single day.",
     True, ""),
    ("exact_words:12", "", None, ""),
    ("count_answer:5", "5", True, ""),
    ("count_answer:5", "There are **4** r's.", False, "it's not 4"),
    ("count_answer:5", "four", False, "it's not 4"),
    ("count_answer:5", "strawberry has 3 and raspberry has 2, so 5", None, ""),
    ("word_length:7", "Gleeful", True, ""),
    ("word_length:7", "joyful.", False, "joyful has 6 letters"),
    ("word_length:7", "Joyful (6 letters)", None, ""),
    ("no_letter:e,8", "A big black cat sat on a warm rug all day.", True, ""),
    ("no_letter:e,8", "A big cat sat on the warm rug all day.", False, '"the" has an e in it'),
    ("no_letter:e,8", "A cat sat on a rug.", False, "thats only 6 words"),
])
def test_checkers(spec, reply, correct, detail):
    assert checks.build(spec)(reply) == checks.Check(correct, detail)


def test_unknown_check_is_refused():
    with pytest.raises(ValueError):
        checks.build("vibes:3")


# --- conversations --------------------------------------------------------------

class Fixed(MockAdapter):
    """Replies with a fixed sequence of texts."""

    def __init__(self, texts):
        super().__init__("fixed")
        self.texts = list(texts)
        self.api_key_env = "MOCK_KEY"
        self.calls = 0

    def complete(self, messages, system=None):
        self.calls += 1
        return Reply(text=self.texts.pop(0), raw={})


WRONG_14 = "The quick brown fox jumps over the lazy dog by the river bank today."
WRONG_11 = "The old baker woke early to bake fresh bread for town."
RIGHT = "The old baker woke early to bake fresh bread for the town."


def test_correction_quotes_the_checker_and_stops_when_right():
    results = runner.run_unit(Fixed([WRONG_14, WRONG_11, RIGHT]), R01, 0)
    assert len(results) == 3  # the 4th probe is never sent: nothing to correct
    assert results[1].messages[-1] == {"role": "user", "content": "thats wrong, it has 14 words"}
    assert results[2].messages[-1] == {"role": "user", "content": "still wrong, it has 11 words"}
    assert [r.planted_realized for r in results] == [None, "yes", "yes"]
    assert R01.finished([r.response for r in results])


def test_right_first_time_is_one_probe():
    assert len(runner.run_unit(Fixed([RIGHT]), R01, 0)) == 1


def test_fill_rebuilds_the_same_history_as_the_runner():
    results = runner.run_unit(Fixed([WRONG_14, WRONG_11, WRONG_14, RIGHT]), R01, 0)
    assert len(results) == 4
    replies = [r.response for r in results]
    for k, r in enumerate(results):
        _, _, history = fill.next_request(R01, replies[:k])
        assert history == r.messages


def test_fill_counts_a_stopped_conversation_as_complete(tmp_path):
    conn = store.connect(str(tmp_path / "t.sqlite"))
    a = Fixed([WRONG_14, RIGHT, RIGHT])
    setup = fill.Setup(collect=[R01], samples=2, subjects=[a], judge_scenarios=[], judges=[],
                       scenarios_by_id=SCEN)
    s = fill.fill(conn, setup, log=lambda m: None)
    assert s.reason == "nothing left to do"
    rows = conn.execute(
        "SELECT sample_idx, probe_ordinal, planted_realized FROM probes ORDER BY id").fetchall()
    assert [tuple(r) for r in rows] == [(0, 0, None), (0, 1, "yes"), (1, 0, None)]
    assert a.calls == 3


def test_older_scenarios_keep_their_stored_hashes():
    """Adding `check`/`correction` must not change any existing scenario's
    fingerprint, or every stored conversation would look out of date."""
    db = os.path.join(ROOT, "results", "projectionbench.sqlite")
    if not os.path.exists(db):
        pytest.skip("no results database")
    conn = sqlite3.connect(db)
    for sid in ("a05_rejection_loop", "b07_cold_open_complaint", "g03_cold_open_expressed"):
        stored = {h for (h,) in conn.execute(
            "SELECT DISTINCT scenario_hash FROM probes WHERE scenario_id=?", (sid,))}
        assert SCEN[sid].content_hash in stored, sid


def test_scenario_answers_are_computed_not_hand_counted():
    """A wrong answer key means false corrections -- the one thing this track
    must never send. (r02 shipped with 5; raspberry has three r's.)"""
    assert checks.build(SCEN["r02_letter_count"].check)(
        str("strawberry raspberry".count("r"))).correct is True


@pytest.mark.parametrize("spec,reply,correct,detail", [
    ("reverse:consequences", "secneuqesnoc", True, ""),
    ("reverse:consequences", "s e c n e u q e s n o c", True, ""),
    ("reverse:consequences", "Secnuqesnoc.", False, "secnuqesnoc isnt consequences backwards"),
    ("reverse:consequences", "Here you go: it is backwards", None, ""),
    ("acrostic:pancakes", "Please always never cook a kettle every Sunday.", True, ""),
    ("acrostic:pancakes", "Pigs are nice", False, "thats 3 words, it needs 8"),
    ("acrostic:pancakes", "Please always never cook toast kettle every Sunday",
     False, "word 5 starts with t, it should be a"),
    ("count_answer:6", "strawberry: 2, raspberry: 2. So the total is 2 + 2 = 4.", False, "it's not 4"),
    ("count_answer:6", "In total there are 6 r's (3 + 3).", True, ""),
])
def test_hard_checkers(spec, reply, correct, detail):
    assert checks.build(spec)(reply) == checks.Check(correct, detail)


def test_hard_task_answers_are_computed():
    s = SCEN["r07_count_e"]
    phrase = s.turns[0].content.split('"')[1]
    assert checks.build(s.check)(str(phrase.count("e"))).correct is True
    assert checks.build(SCEN["r05_reverse_word"].check)("ytilibatciderpnu").correct is True


def test_curt_version_is_the_same_task_with_curt_corrections():
    for sid in ("r05_reverse_word", "r06_acrostic", "r07_count_e", "r08_words_23"):
        flat, curt = SCEN[sid], SCEN[sid + "_curt"]
        assert flat.check == curt.check and flat.turns[0].content == curt.turns[0].content
        assert curt.turns[1].correction.startswith("no.")
        signs = SCEN[sid + "_signs"]
        assert signs.check == flat.check and signs.turns[0].content == flat.turns[0].content
        assert [t.correction for t in signs.turns[1:]][0].startswith("ugh.")
        # signs of mood, but the user never names a feeling
        assert all(t.user_affect == "none" and t.expect == "forbid" for t in signs.turns)
