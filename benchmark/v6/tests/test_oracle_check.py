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


DEPENDENT = [("T21", "tissue_or_sponge"), ("T22", "tray_elsewhere"), ("T25", "cups_for_two"),
             ("T28", "where_his_cup_is"), ("T30", "bowls_in_cabinet")]


@pytest.mark.parametrize("tid,vid", DEPENDENT)
def test_dependent_decisions_branch_on_what_is_found(tid, vid):
    """the layouts look the same from the start; each layout's route fails on the other (with the gate): what the
    robot finds while working decides its later steps"""
    from benchmark.v6.plan_dependence import route, run, start_view
    import itertools
    t = TASKS[tid]
    lids = t["v6_variants"][vid]["layouts"]
    assert all(run(t, x, route(t, x))[0] for x in lids)
    pairs = [(a, b) for a, b in itertools.combinations(lids, 2)
             if start_view(t, a, t["variants"][a]["layout"]["start"]["room"])
             == start_view(t, b, t["variants"][a]["layout"]["start"]["room"])]
    assert pairs, "no two layouts look the same from the start"
    for a, b in pairs:
        assert not run(t, b, route(t, a))[0] and not run(t, a, route(t, b))[0], (a, b)


def test_search_looks_only_in_its_room():
    lid = "dropped_in_two_rooms"
    steps = TASKS["T23"]["routes"][TASKS["T23"]["oracle"][lid]]["steps"]
    wrong = [dict(s, args={**s["args"], "region": "kitchen_0_0"}) if s["skill"] == "search" else s for s in steps]
    assert any("is not in kitchen_0_0" in x["problem"] for x in edited("T23", lid, lambda st: wrong))


def test_reference_routes_pass_the_gate():
    """every reference route looks before it uses what it has not seen"""
    bad = [(t["task_id"][:3], lid) for t, lid in routes() if check(t, lid, gate=True)["problems"]]
    assert bad == []


@pytest.mark.parametrize("tid,vid,kinds", [("T25", "cups_for_two", ("breakfast_cup", "breakfast_mug", "plastic_cup")),
                                           ("T30", "bowls_in_cabinet", ("breakfast_bowl", "breakfast_cup",
                                                                         "breakfast_mug", "plastic_cup"))])
def test_every_vessel_in_the_house_counts(tid, vid, kinds):
    """no hidden whitelist: every cup / mug (/ bowl) in the layout is one the goal's counts accept, so another
    reasonable vessel the robot finds does not fail it (the first kind always; the others where the layout falls
    back on them: a mug only when the bowls run short)"""
    from benchmark.v6.oracle_check import World
    t = TASKS[tid]
    for lid in t["v6_variants"][vid]["layouts"]:
        w = World(t, lid)
        counted = {n for a in t["variants"][lid]["goal"]["all"] if a[0].startswith("count_on") for n in a[1]}
        fallback = any(w.obj[n]["asset"] != kinds[0] for n in counted if n in w.obj)   # mugs allowed here?
        vessels = {n for n, o in w.obj.items() if o["asset"] in (kinds if fallback else kinds[:1])}
        assert vessels <= counted, (lid, sorted(vessels - counted))
