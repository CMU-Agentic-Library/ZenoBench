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
    got = dict(info.get("scoring") or {})
    got.pop("D_by_layout", None), got.pop("top_by_layout", None)     # 11-17: per-seed summaries
    assert got == spec
    from benchmark.v6.scoring import per_layout, with_ideal
    for lid in info["layouts"]:
        assert t["variants"][lid]["scoring"] == with_ideal(t["task_id"], key[1], lid, per_layout(spec, lid))
        for tier in spec["tiers"]:
            g = tier["goal"]
            if g and "by_layout" in g:
                assert lid in g["by_layout"]


def test_first_tier_that_holds():
    s = {"D": 1, "tiers": [{"name": "best", "score": 1.0, "goal": {"all": ["a"]}},
                           {"name": "worst", "score": 0.3, "goal": {"all": ["b"]}}], "not_ok": "x"}
    task = {"goal": {"all": ["a"]}}
    assert score(s, task, None, lambda g: g["all"] == ["b"]) == {"tier": "worst", "level": "bad", "score": 0.3, "D": 1}
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


def test_every_substitution_seed_has_its_ideal():
    """11-18 (user): every seed that asks for a substitution has its ideal set by hand (ideals.IDEAL), and where the
    ideal is there the best tier is the ideal"""
    from benchmark.v6.ideals import ideal_of
    from benchmark.v6.substitution_stats import KIND
    doc = json.loads((Path(__file__).resolve().parents[1] / "tasks.json").read_text())
    missing = []
    for t in doc["tasks"]:
        for d, info in t["v6_variants"].items():
            kinds = next((k for (tid, dd), k in KIND.items() if t["task_id"].startswith(tid) and dd == d), {})
            for lid in info["layouts"]:
                case = lid.split("__", 1)[1] if "__" in lid else ""
                if kinds.get(case, kinds.get(lid, kinds.get("*"))) and ideal_of(t["task_id"], d, lid) is None:
                    missing.append(lid)
                sc = t["variants"][lid].get("scoring")
                if sc and sc.get("ideal_present"):
                    assert sc["top"] == "ideal", lid
    assert missing == []
