"""Graded outcomes (benchmark/v6/scoring.py): every reviewed design is well formed and reaches tasks.json."""
import json
from pathlib import Path

import pytest

from benchmark.v6.scoring import SCORING, check_spec, score

TASKS = json.loads((Path(__file__).resolve().parents[1] / "tasks.json").read_text())


@pytest.mark.parametrize("key", sorted(SCORING), ids=lambda k: f"{k[0]}-{k[1]}")
def test_spec(key):
    assert check_spec(SCORING[key]) == []


@pytest.mark.parametrize("key", sorted(SCORING), ids=lambda k: f"{k[0]}-{k[1]}")
def test_in_tasks_json(key):
    tid, design = key
    t = next(t for t in TASKS["tasks"] if t["task_id"].startswith(tid))
    info = t["v6_variants"][design]
    assert info.get("scoring") == SCORING[key]
    for lid in info["layouts"]:
        assert t["variants"][lid]["scoring"] == SCORING[key]
        for tier in SCORING[key]["tiers"]:
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
