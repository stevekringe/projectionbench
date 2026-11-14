import json
from pathlib import Path

import pytest

from projectionbench.judge.lexicon import classify


CASES = json.loads(
    (Path(__file__).resolve().parents[1] / "gold" / "everyday-grader-check.json").read_text()
)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_everyday_reply_attribution(case):
    verdict = classify(case["reply"])
    expected = case["expected"]
    if "quote" in case:
        assert case["quote"] in case["reply"]
    if expected in {"direct", "none"}:
        assert verdict.attributed == (expected == "direct")


@pytest.mark.parametrize("reply", [
    "The bulb burned out, so replace it.",
    "You are not feeling burnt out.",
    'I should not have said "you are feeling burnt out".',
])
def test_burnout_mention_is_not_an_attribution(reply):
    assert not classify(reply).attributed
