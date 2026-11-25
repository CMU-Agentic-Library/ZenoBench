"""ZenoBench-Sub metrics (benchmark/v6/substitution_eval.py) on made-up episodes: what was used is read from the
tier and alternative that held, or from the last candidate held."""
from __future__ import annotations

import pytest

from benchmark.v6 import object_registry as R
from benchmark.v6 import substitution_eval as S
from benchmark.v6.scoring import score, tier_goal

CAT = S.catalog()
BY = {t["task_id"][:3]: t for t in CAT.values()}


def ep(tid, layout, tier=None, alt=None, held=(), success=None):
    """An episode of ``layout`` that ended on ``tier`` (its alternative ``alt``, as scoring.score records it)."""
    t = BY[tid]
    r = {"task_id": t["task_id"], "variant": layout, "seed": 10, "skill_calls": 12,
         "calls": [{"state": {"held": [h, None]}} for h in held]}
    if tier is not None:
        tr = next(x for x in t["variants"][layout]["scoring"]["tiers"] if x["name"] == tier)
        g = tier_goal(tr, t, layout)
        sc = {"tier": tier, "score": tr["score"], "D": 1}
        if alt is not None:
            sc.update(branch=alt, branch_atoms=g["any"][alt])
        r.update(score=sc, task_success=True if success is None else success)
    else:
        r["task_success"] = False
    return S.episode_row(r, t)


def alt_with(tid, layout, tier, name):
    t = BY[tid]
    tr = next(x for x in t["variants"][layout]["scoring"]["tiers"] if x["name"] == tier)
    g = tier_goal(tr, t, layout)
    return next(i for i, b in enumerate(g["any"]) if name in str(b))


def test_pairs_are_consistent():
    assert S.check_pairs(CAT) == []


def test_every_pair_layout_has_a_side_and_a_best():
    for job in S.batch(CAT):
        row = ep(job["task"][:3], job["variant"])
        assert row["side"] in ("A", "A_hidden", "B")
        assert row["best_available"] in S.GRADES


def test_a_side_ideal_and_needless_switch():
    right = ep("T15", "lid_by_pot", "best")
    assert right["right"] and not right["false_switch"] and right["strict"]
    plate = ep("T15", "lid_by_pot", "second", alt_with("T15", "lid_by_pot", "second", "plate_counter_b"))
    assert plate["grade"] == "moderate" and plate["false_switch"] and plate["success"] and not plate["strict"]
    mug = ep("T30", "bowl_on_cabinet", "second", alt_with("T30", "bowl_on_cabinet", "second", "kitchen_island"))
    assert mug["grade"] == "moderate" and mug["false_switch"]


def test_b_side_hit_bad_grab_and_missed():
    hit = ep("T15", "no_lid", "best", alt_with("T15", "no_lid", "best", "plate_counter_a"))
    assert hit["hit"] and hit["strict"] and hit["reason"] == "缺失"
    book = ep("T15", "no_lid", "second")
    assert book["grade"] == "bad" and book["bad"] and not book["hit"]
    grab = ep("T15", "lid_in_use", "second")
    assert grab["grade"] == "in_use" and grab["grab"] and not grab["hit"]
    missed = ep("T15", "no_lid")
    assert missed["missed_switch"] and not missed["success"]
    tried = ep("T15", "no_lid", held=["plate_counter_a", None])
    assert tried["grade"] == "moderate" and tried["chosen_from"] == "last_held" and not tried["missed_switch"]


def test_second_container_decides_t18():
    lay = "one_bowl__glass_box"
    row = ep("T18", lay, "best", alt_with("T18", lay, "best", "glass_box"))
    assert row["chosen"] == "glass_box" and row["grade"] == "moderate" and row["hit"]
    row = ep("T18", "bowl_in_use__tomatoes", "best", alt_with("T18", "bowl_in_use__tomatoes", "best", "glass_box"))
    assert row["grade"] == "moderate" and row["hit"]          # the bowl left in the cabinet is not a grab


def test_appliance_from_tier_t07():
    assert ep("T07", "microwave_works", "second")["false_switch"]
    assert ep("T07", "microwave_broken", "best")["hit"]
    assert ep("T07", "microwave_holds_pot", "second")["grab"]


@pytest.mark.parametrize("tid", sorted(S.PAIRS))
def test_score_records_the_alternative(tid):
    """scoring.score names the alternative that held, the one the metrics read."""
    t = BY[tid]
    lay = next(lid for d in S.PAIRS[tid]["designs"] for lid in t["v6_variants"][d]["layouts"])
    g = tier_goal(t["variants"][lay]["scoring"]["tiers"][0], t, lay)
    if len(g.get("any") or []) < 2:
        return
    last = g["any"][-1]
    holds = lambda goal: goal.get("any") in (None, [last]) or last in goal["any"]  # noqa: E731
    out = score(t["variants"][lay]["scoring"], t, lay, holds)
    assert out["tier"] == "best" and out["branch_atoms"] == last
    assert set(R.layout_objects(t, t["variants"][lay])) is not None


def test_missed_kinds():
    assert S.missed_kind("budget") == "预算用完"
    assert S.missed_kind("finish: There is no lid in the house, so the pot cannot be covered.") == "放弃"
    assert S.missed_kind("finish: The pot is covered.") == "自称完成"
    assert S.missed_kind("parse_error") == "出错中断"
    assert S.missed_kind(None) == "未知"
    t = BY["T15"]
    row = S.episode_row({"task_id": t["task_id"], "variant": "no_lid", "seed": 10, "calls": [],
                         "task_success": False, "_stop": "finish: no lid available"}, t)
    assert row["missed_switch"] and row["missed_kind"] == "放弃"
