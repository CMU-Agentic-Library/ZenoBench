"""User rule (11-20): when the ideal is there, the ideal alone scores 1.0 -- a substitute is at most 0.6.

A seed whose ideal is missing (ideals.IDEAL present=False) has a reference route that uses the substitute.  That
route is replayed symbolically in every sibling layout of the same design whose ideal is there, and scored with the
sibling's tiers: it must not reach 1.0 there."""
import json
from pathlib import Path

from benchmark.v6.oracle_check import World
from benchmark.v6.scoring import score

TASKS = Path(__file__).resolve().parents[1] / "tasks.json"

# (substitute seed, ideal-present seed): not a substitute in the sibling, checked by hand 11-20
NOT_A_LEAK = {
    # loose: block B is free, any two blocks are the ideal (the walk to the other room's block is SPL-c's)
    ("crowded_use_another__tight_tv", "crowded_use_another__loose"),
    ("crowded_use_another__tight_dining", "crowded_use_another__loose"),
    # pen_in_use leaves the desk as it is; on pen_on_desk that is the ideal too (the pen already there)
    ("check_desk_first__pen_in_use", "check_desk_first__pen_on_desk"),
    # in_use cooks in the empty pot; on free the same pot is the ideal one
    ("pot_in_use__in_use", "pot_in_use__free"),
    # the mug is placed but same_arrangement (geometry, symbolically unknown) needs the cup: fails in sim
    ("copy_the_setting__no_cup", "copy_the_setting__bowl_cup"),
    # nothing_to_clear has no toy car: the route's pick/place does nothing there
    ("belongs_on_table__no_toy_box", "nothing_to_clear"),
}


def _replay(task, world_lid, route_lid):
    w = World(task, world_lid, False)
    for i, s in enumerate(task["routes"][task["oracle"][route_lid]]["steps"]):
        if s.get("expect") != "fail":
            w.step(i, s)
    return w


def _holds(w):
    def h(g):
        if any(w.holds(a) is False for a in g.get("all", [])):
            return False
        groups = g.get("any") or []
        return not groups or any(all(w.holds(a) is not False for a in grp) for grp in groups)
    return h


def test_substitute_route_below_one_where_ideal_is_there():
    bad = []
    for t in json.loads(TASKS.read_text())["tasks"]:
        for design, info in t["v6_variants"].items():
            seeds = [lid for lid in info["layouts"] if t["variants"][lid].get("scoring")]
            for a in seeds:
                if t["variants"][a]["scoring"].get("ideal_present", True):
                    continue
                for b in seeds:
                    sb = t["variants"][b]["scoring"]
                    if b == a or not sb.get("ideal_present", True) or (a, b) in NOT_A_LEAK:
                        continue
                    got = score(sb, {**t, "goal": t["variants"][b].get("goal") or t["goal"]}, b,
                                _holds(_replay(t, b, a)))
                    if got["score"] == 1.0:
                        bad.append((t["task_id"], a, b))
    assert not bad, bad
