"""Graded outcomes (benchmark/v6/scoring.py): every reviewed design is well formed and reaches tasks.json."""
import json
from pathlib import Path

import pytest

from benchmark.v6.scoring import BUILT, SCORING, check_spec, score, scoring_for

TASKS = json.loads((Path(__file__).resolve().parents[1] / "tasks.json").read_text())


KEYS = sorted(set(SCORING) | set(BUILT))


def _spec(key):
    t = next(t for t in TASKS["tasks"] if t["task_id"].startswith(key[0]))
    return t, scoring_for(t["task_id"], key[1], t)


@pytest.mark.parametrize("key", KEYS, ids=lambda k: f"{k[0]}-{k[1]}")
def test_spec(key):
    assert check_spec(_spec(key)[1]) == []


@pytest.mark.parametrize("key", KEYS, ids=lambda k: f"{k[0]}-{k[1]}")
def test_in_tasks_json(key):
    t, spec = _spec(key)
    info = t["v6_variants"][key[1]]
    assert info.get("scoring") == spec
    for lid in info["layouts"]:
        assert t["variants"][lid]["scoring"] == spec
        for tier in spec["tiers"]:
            g = tier["goal"]
            if g and "by_layout" in g:
                assert lid in g["by_layout"]


def test_first_tier_that_holds():
    s = {"D": 1, "tiers": [{"name": "best", "score": 1.0, "goal": {"all": ["a"]}},
                           {"name": "worst", "score": 0.3, "goal": {"all": ["b"]}}], "not_ok": "x"}
    task = {"goal": {"all": ["a"]}}
    assert score(s, task, None, lambda g: g["all"] == ["b"]) == {"tier": "worst", "score": 0.3, "D": 1}
    assert score(s, task, None, lambda g: False)["tier"] == "not_ok"
    assert score(None, task, None, lambda g: True) is None


def test_drop_tier():
    from benchmark.v6.scoring import tier_goal
    task = {"goal": {"all": [["on", "b", "t"], ["near_any", "b", ["p"], 0.15], ["clear_of", "b", ["p"], 0.05]]}}
    assert tier_goal({"goal": {"drop": ["near_any", "clear_of"]}}, task, None) == {"all": [["on", "b", "t"]]}


@pytest.mark.parametrize("key", KEYS, ids=lambda k: f"{k[0]}-{k[1]}")
def test_not_ok_in_chinese(key):
    from benchmark.v6.scoring import NOT_OK_ZH
    assert key in NOT_OK_ZH
