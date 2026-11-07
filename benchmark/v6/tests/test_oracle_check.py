"""The symbolic oracle check: every reference route reaches its goal, and a broken route is caught."""
import copy
import json
from pathlib import Path

import pytest

from benchmark.v6.oracle_check import check

DOC = json.loads((Path(__file__).resolve().parents[1] / "tasks.json").read_text())
TASKS = {t["task_id"][:3]: t for t in DOC["tasks"]}


def routes():
    for t in DOC["tasks"]:
        for info in t["v6_variants"].values():
            for lid in info["layouts"]:
                yield t, lid


@pytest.mark.parametrize("t,lid", list(routes()), ids=lambda x: x if isinstance(x, str) else x["task_id"][:3])
def test_route_reaches_goal(t, lid):
    assert check(t, lid)["problems"] == []


def broken(tid, lid, drop):
    t = copy.deepcopy(TASKS[tid])
    r = t["oracle"][lid]
    t["routes"][r]["steps"] = [s for i, s in enumerate(t["routes"][r]["steps"]) if not drop(i, s)]
    return check(t, lid)["problems"]


def test_missing_open_is_caught():
    p = broken("T09", "tomato_in_fridge__in_fridge", lambda i, s: s["skill"] == "open")
    assert any("inside closed breakfast_fridge" in x["problem"] for x in p)


def test_missing_walk_is_caught():
    lid = "far_sponge_tv__alt_dining_table_2"
    steps = TASKS["T08"]["routes"][TASKS["T08"]["oracle"][lid]]["steps"]
    k = next(i for i, s in enumerate(steps) if s["skill"] == "navigate" and s["args"]["destination"] == "kitchen_island/top")
    p = broken("T08", lid, lambda i, s: i == k)
    assert any("not near kitchen_island/top" in x["problem"] for x in p)


def test_missing_place_fails_the_goal():
    p = broken("T10", "after_dinner_clear__rubbish_leftovers",
               lambda i, s: s["skill"] == "place" and s["args"]["object"] == "leftovers")
    assert any(x["skill"] == "goal" or "holding" in x["problem"] for x in p)


def edited(tid, lid, edit):
    t = copy.deepcopy(TASKS[tid])
    r = t["oracle"][lid]
    t["routes"][r]["steps"] = edit(t["routes"][r]["steps"])
    return check(t, lid)["problems"]


def test_castle_taken_apart_and_rebuilt_fails():
    """never_picked is a process requirement: lifting the top block and putting it back is not keeping the castle"""
    top = "castle_block_3"
    lift = [{"skill": "navigate", "args": {"destination": top}}, {"skill": "pick", "args": {"object": top}},
            {"skill": "stack", "args": {"object": top, "base": "castle_block_2"}}]
    p = edited("T12", "castle_stays__tall_two_loose", lambda st: lift + st)
    assert any(x["skill"] == "goal" and "never_picked" in x["problem"] for x in p)


def test_cup_on_the_desk_beside_the_bed_passes():
    """on_any: the desk beside bed 1 does what was asked as well as the low bookcase"""
    def to_desk(st):
        return [dict(s, args={**s["args"], **({"destination": "desk_1/top"} if s["args"].get("destination") == "bookcase_3/top" else {}),
                              **({"receptacle": "desk_1/top", "hint_xy": [0.20, -2.95]}
                                 if s["args"].get("receptacle") == "bookcase_3/top" else {})}) for s in st]
    assert edited("T28", "cup_on_counter", to_desk) == []


@pytest.mark.parametrize("tid,vid", [("T21", "no_tissue_sponge_away"), ("T28", "his_cup_put_away"),
                                     ("T30", "not_enough_bowls")])
def test_dependent_decisions_need_a_new_plan(tid, vid):
    """the control's route, fixed before the episode, does not solve a dependent-decisions variant (with the gate)"""
    t = TASKS[tid]
    m = t["v6_variants"][vid]
    lid, ctl = m["layouts"][0], t["v6_variants"][m["control"]]["layouts"][0]
    assert check(t, lid, gate=True)["problems"] == []
    assert edited(tid, lid, lambda st: copy.deepcopy(t["routes"][t["oracle"][ctl]]["steps"])) != []
