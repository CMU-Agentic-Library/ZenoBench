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
