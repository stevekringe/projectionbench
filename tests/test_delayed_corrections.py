"""Tests for the delayed-source factual correction study scripts."""

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "pilot" / "benchmark-v1"


def _load_delayed():
    sys.path.insert(0, str(BENCH_DIR))
    spec = importlib.util.spec_from_file_location(
        "run_delayed_corrections", BENCH_DIR / "run_delayed_corrections.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_delayed_scenarios_withhold_source_from_opening():
    mod = _load_delayed()
    cases = {
        c["id"]: c
        for c in json.loads((ROOT / "pilot" / "source-correction" / "cases.json").read_text())
    }
    built = list(mod.scenarios())
    assert len(built) == 8
    for s in built:
        case_id = s.id.removesuffix("_first").removesuffix("_repeat")
        source = cases[case_id]["sourceQuote"]
        assert source not in s.turns[0].content, f"{s.id} leaked source into opening"
        assert source in s.turns[-1].content, f"{s.id} missing source in final correction"
        assert s.turns[-1].probe is True
        assert s.turns[-1].role == "user"
        assert all(
            not any(w in t.content.lower() for w in ("frustrat", "annoy", "upset", "angry"))
            for t in s.turns if t.role == "user"
        )
