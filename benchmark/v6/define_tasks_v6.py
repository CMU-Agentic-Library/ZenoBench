"""ZenoBench v6 task design: the v5 suite plus new task-level variant families (reads v5, never writes it).

    python benchmark/v6/define_tasks_v6.py            # writes benchmark/v6/tasks.json
    python benchmark/v6/define_tasks_v6.py --check    # fails if tasks.json is not up to date

v5 (benchmark/v5/tasks.json) is copied as it is: every v5 variant keeps its configuration, so every v5 episode
hash stays valid (tests/test_v6_catalog.py checks it).  v6 adds new **variants** (``v6_variants``).  A
variant is one task design (failures, conditions, substitutes, goal); its seeds 10-19 set the layout: the
seeded shift of objects and start (``vary``) and, for a variant with several **layouts** (the resource,
substitute or item in another place), which layout (``v6_variants[vid]["seeds"]``, deterministic and
balanced).  A layout is a concrete configuration ``<variant>__<layout>`` with its own oracle route.  Design
input below still lists them as ``cases``; a family in ``SPLIT`` (cases that differ in the design) becomes
one variant per case.

Every new design states, besides its overlay / failures / route:

* ``challenge``  - what the planner meets; ``rationale`` - why a plan has to change and why it stays solvable;
* ``control``    - the existing variant it differs from in one factor (isolation pairs for the analysis).

Each family is placed in the Action-Level or Task-Level track (or both) by ``tracks.py`` from its configuration.

Only existing skills (contract_library) and objects already in the base scenes / assets are used.
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmark.v5.define_tasks_v5 import (FAIL, FIELDS, OVERLAY, P, REC, START, S, _refresh_view,  # noqa: E402
                                          f_grasp, f_grasp_persist, f_ik, f_ik_persist, f_initial, f_joint, f_move,
                                          f_slip, find, seed_vary, with_grasp, with_ik, with_slip)

V5 = ROOT / "benchmark/v5/tasks.json"
OUT = ROOT / "benchmark/v6/tasks.json"
SEEDS = list(range(10, 20))
TOMATOES = ["cherry_tomato_1", "cherry_tomato_2"]


# ----------------------------------------------------------------- helpers
def f_slip_persist(x, one_handed=False):
    t = {"skill": "navigate", "while_holding": x, "nth": 1}
    if one_handed:
        t["one_handed"] = True
    return {"id": f"slip_{x}_persistent", "kind": "slip", "persist": True, "trigger": t}


def f_ik_where(skill, fid, **args):
    """Persistent IK refusal of ``skill`` wherever ``args`` match (e.g. every drop into one container)."""
    return {"id": fid, "kind": "ik", "persist": True, "until": "never", "trigger": {"skill": skill, "args": args, "nth": 1}}


def refused_twice(step, repark=None):
    """A persistent refusal: the call fails, a re-park (optional) and a retry fail the same way, then the
    plan changes."""
    out = [FAIL(step, True)]
    if repark:
        out.append(REC(S("approach", target=repark)))
    return out + [FAIL(step, True)]


def OR(t, vid):
    return copy.deepcopy(t["routes"][t["oracle"][vid]]["steps"])


def RT(t, name):
    return copy.deepcopy(t["routes"][name]["steps"])


def recs(*steps):
    return [REC(s) for s in steps]


def at(steps, skill, **match):
    return find(steps, skill, **match)


def nav(x):
    return S("navigate", destination=x)


def pick(x, **kw):
    return S("pick", object=x, **kw)


def place(x, r, hint=None):
    return S("place", object=x, receptacle=r, **({"hint_xy": hint} if hint else {}))


def look(x):
    return S("look", target=x)


def open_explore(art):
    """Open a low cabinet and look inside it (the v5 pencil-in-cabinet steps)."""
    return [nav(art), S("open", articulated=art), S("bend"), S("explore_furniture", furniture=art), S("straighten")]


def behind_wall(steps, target, blocker, aside):
    """The target stands against the wall with ``blocker`` right in front: every pick of the target is refused
    (no reach, no room to slide it out) until the blocker is moved aside; then pick the target as planned."""
    i = find(steps, "pick", object=target)
    return steps[:i] + refused_twice(steps[i]) + recs(nav(blocker), pick(blocker), place(blocker, *aside), nav(target),
                                                      look(target)) + [REC(steps[i])] + steps[i + 1:]


def put_away(steps_before, art_first, art_second, take, steps_after):
    """Inspect two closed cabinets in the worse order, take the item from the second, close both."""
    return steps_before + open_explore(art_first) + [S("close", articulated=art_first)] + open_explore(art_second) \
        + take(art_second) + steps_after


# ----------------------------------------------------------------- per-task families
def T01(t):
    B = "paperback_book"
    base = OR(t, "overhang_ready")                      # look, nav, approach, look, pick, nav table, place
    i = at(base, "pick", object=B)
    carry, place_ = base[i + 1], base[i + 2]
    # re-park at the slipped flat book with navigate: approach parks so close that it leaves the head's view
    two_hand = (base[:i + 1] + [FAIL(carry, True)] + recs(nav(B), look(B), pick(B))
                + [FAIL(carry, True)] + recs(nav(B), look(B), S("expose", object=B), pick(B, hands="both"), carry)
                + [place_])           # the bimanual flat pick needs an overhanging edge: expose first
    slip_once = base[:i + 1] + [FAIL(carry, True)] + recs(nav(B), look(B), pick(B), carry) + [place_]
    on_book = lambda x: {x: {"support": None, "z": 0.886, "xy": [7.62, 1.59], "yaw_deg": 0.0}}  # noqa: E731

    def clear_book(x):
        return [look("kitchen_island/top")] + recs(nav(x), pick(x), place(x, "kitchen_island/top", [7.2, 1.85])) + base[1:]
    return {
        "x6_sr_two_hand_carry": dict(
            base="overhang_ready", control="x6_m_slip_book",
            challenge="the paperback slips out of the one-handed pinch at the start of every carry; the first place "
                      "on the table is also refused from its park",
            rationale="a one-handed retry fails every time (persistent slip), so the carry procedure must change: "
                      "pick the book with both hands (the left hand steadies it); solvable because pick(hands=both) "
                      "is a library skill and the slip only affects one-handed carries",
            cases={"": dict(failures=[f_slip_persist(B, one_handed=True), f_ik("place", B)],
                            route=with_ik(two_hand, "place", B))}),
        "x6_m_slip_book": dict(
            base="overhang_ready", control="overhang_ready",
            challenge="the paperback slips once at the start of the carry",
            rationale="matched control of x6_sr_two_hand_carry: the same slip, transient, so picking it again works",
            cases={"": dict(failures=[f_slip(B)], route=slip_once)}),
        "x6_dr_block_on_book": dict(
            conditions=["multi_object_goal"], base="overhang_ready", control="overhang_ready",
            factor="which object lies on the book (blocking relation)",
            challenge="a toy block (or the sponge) lies on top of the paperback",
            rationale="the book cannot be lifted with something on it: take that off (and leave it on the island) "
                      "first; it is not part of the goal, so this is an inserted precondition",
            cases={{"wooden_block_a": "block", "kitchen_sponge": "sponge"}[x]: dict(
                move=on_book(x), failures=[f_initial("dependency", [["on_top_of", x, B]])],
                                          route=clear_book(x))
                   for x in ("wooden_block_a", "kitchen_sponge")}),
    }


def T02(t):
    A, B, F = "wooden_block_a", "wooden_block_b", "floor_block"
    base = OR(t, "clear")                               # look, nav B, pick B, rotate B, nav A, stack B on A
    swap_tail = recs(nav(A), pick(A), S("rotate", object=A, degrees=30), nav(B), S("approach", target=B),
                     S("stack", object=A, base=B))
    cases = {}
    for case, fail, rep in (("grasp", f_grasp_persist(B), None), ("ik", f_ik_persist("pick", B), B)):
        r = base[:2] + refused_twice(base[2], rep) + swap_tail
        cases[case] = dict(failures=[fail, f_ik("stack", A)], route=with_ik(r, "stack", A))
    # three-block tower: block A at the edge (edge_base), block B in the open, the floor block put on the island
    order = [(A, B), (F, A)]
    tower_goal = {"any": [[["on_top_of", m, b], ["on_top_of", top, m], ["away_from_edge", b, 0.05],
                           ["on", b, "kitchen_island/top"]]
                          for b in (B, F) for m in (A, B, F) for top in (A, B, F) if len({b, m, top}) == 3],
                  "all": [["hand_empty", "right"]]}
    def tower(region):
        return [look("kitchen_island/top")] + recs(nav(A), pick(A), nav(B), S("approach", target=B),
                                                   S("stack", object=A, base=B)) \
            + recs(S("search", object=F, region=region), nav(F), pick(F), nav(B), S("approach", target=B),
                   S("stack", object=F, base=A))
    put_down = base[:5] + refused_twice(base[5], A) + with_grasp(recs(
        place(B, "kitchen_island/top", [7.0, 1.8]), nav(A), pick(A), nav(B), S("approach", target=B),
        S("stack", object=A, base=B)), A)
    return {
        "x6_cl_base_a_unreachable": dict(
            base="clear", control="clear",
            challenge="no park reaches the top of block A for the stack (block B in hand); block A slips on its "
                      "first pick",
            rationale="stacking on A is impossible however the robot re-parks (persistent, pinned to A as the base): "
                      "set B down and swap the roles, A goes on top of B",
            cases={"": dict(failures=[f_ik_where("stack", "ik_stack_on_a_persistent", base=A), f_grasp(A)], route=put_down)}),
        "x6_cl_block_b_unholdable": dict(
            base="clear", control="m_grasp_b",
            factor="failure mechanism (grasp slip vs reach)",
            challenge="block B cannot be picked at all (it slips every time / no park reaches it); the first stack "
                      "of the other block is refused from its park",
            rationale="the goal allows either block on top: when B cannot be held, swap the roles and stack A on B; "
                      "retrying B never works (persistent)",
            cases=cases),
        "x6_gd_tower_with_event": dict(
            base="edge_base", control="edge_base",
            move={F: P("kitchen_island/top", 6.95, 1.85)},
            instruction="Tidy the toy blocks on the kitchen island: stack all three wooden blocks steadily into one "
                        "tower on the island.",
            goal=tower_goal, watch=[A, B, F],
            challenge="three blocks, one at the island edge (it must not be the base); once the first two are "
                      "stacked, the kid takes the third block to the TV stand",
            rationale="the tower decomposes into two ordered stack subgoals with a base constraint (the edge block "
                      "goes on top of the middle, never at the bottom); the event removes a resource after the first "
                      "subgoal: keep the two-block stack and fetch the third",
            factor="where the event takes the resource",
            cases={c: dict(failures=[f_move("resource", F, to, ("stack", {"object": A, "base": B}), fid="resource_floor_block")],
                           route=tower(region))
                   for c, to, region in (("tv_stand", P("tv_stand_2/top", 7.0, 0.36), "living_room_0_0"),
                                         ("dining", P("dining_table_2/top", 3.7, 6.3), "dining_room_0_1"))}),
    }


def T04(t):
    C, M = "cup_counter_b", "mug"
    base = OR(t, "cup_available")                       # look, nav cup, pick cup, nav cab6, place cup
    slip_r = base[:3] + [FAIL(base[3], True)] + recs(S("approach", target=C), look(C), pick(C)) + [FAIL(base[3], True)] \
        + with_ik(recs(nav(M), pick(M), nav("kitchen_cabinet_6/top"), place(M, "kitchen_cabinet_6/top")), "pick", M)
    ik_r = base[:2] + refused_twice(base[2], C) + with_grasp(recs(
        S("search", object=M, region="living_room_0_0"), nav(M), pick(M), nav("kitchen_cabinet_6/top"),
        place(M, "kitchen_cabinet_6/top")), M)
    spot_goal = copy.deepcopy(t["variants"]["h_task_spot_taken"]["goal"])
    filled = [f_move("destination", "pot_lid", P("kitchen_cabinet_6/top", 3.335, 0.36), ("pick", {"object": C}),
                     fid="destination_lid"),
              f_move("destination", "oatmeal", P("kitchen_cabinet_6/top", 3.7, 0.36), ("pick", {"object": C}),
                     fid="destination_oatmeal")]
    def make_room(x):
        return base[:4] + recs(look("kitchen_cabinet_6/top"), nav("kitchen_cabinet_4/top"),
                               place(C, "kitchen_cabinet_4/top", [1.2, 0.42]), nav(x), pick(x),
                               nav("kitchen_cabinet_4/top"), place(x, "kitchen_cabinet_4/top", [1.55, 0.42]),
                               nav(C), pick(C), nav("kitchen_cabinet_6/top"), place(C, "kitchen_cabinet_6/top"))
    filled_block = [filled[0], f_move("destination", "wooden_block_a", P("kitchen_cabinet_6/top", 3.62, 0.36),
                                      ("pick", {"object": C}), fid="destination_block")]
    cab_goal = {"all": [["on", C, "kitchen_cabinet_6/top"], ["upright", C], ["hand_empty", "right"],
                        ["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]}

    def cup_from(first, second):
        """Reference route in the worse order: the first cabinet holds no cup."""
        return [look("kitchen_island/top")] + open_explore(first) + [S("close", articulated=first)] + open_explore(second) \
            + [nav(C), pick(C), S("retreat", obstacle=second, distance_m=0.3), S("close", articulated=second),
               nav("kitchen_cabinet_6/top"), place(C, "kitchen_cabinet_6/top")]
    shelf = {"kitchen_cabinet_4": {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 0.0},
             "kitchen_cabinet_6": {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.5, 0.36], "yaw_deg": 0.0}}
    cup_cases = {}
    for where, first in (("kitchen_cabinet_4", "kitchen_cabinet_6"), ("kitchen_cabinet_6", "kitchen_cabinet_4")):
        cup_cases[f"cup_in_{where[-1]}"] = dict(
            move={C: shelf[where]}, route=cup_from(first, where),
            failures=[f_initial("resource", [["on", C, f"{where}/inside_shelf"]], fid="resource_cup_in_cabinet")])
    return {
        "x6_gd_cup_in_cabinets": dict(
            base="no_cup", control="no_cup",
            factor="which cabinet holds the preferred item",
            instruction="A guest is coming. Set out a cup at the drinks spot on the low wall cabinet; the cups are kept "
                        "in the two low kitchen cabinets. If there is no cup, the mug on the island will do. Close the "
                        "cabinets again.",
            challenge="the mug is in plain view, but a cup is preferred and the cups are kept in closed cabinets: the "
                      "cup is in one of the two (seed decides which)",
            rationale="the visible substitute must not end the search: the cabinets are inspected until the cup is "
                      "found (reference route: the worse order, the cup is in the second cabinet)",
            goal=cab_goal, cases=cup_cases),
        "x6_cl_cup_unusable": dict(
            base="cup_available", control="m_ik_cup",
            factor="failure mechanism and where the substitute is",
            challenge="the cup cannot be used: it slips out of the hand at every carry, or no park reaches it while "
                      "the mug stands on the TV stand",
            rationale="persistent failures on the cup make retries useless; the instruction allows a mug, so the "
                      "object changes (cross-level); in the second case the mug must also be found",
            cases={"slip": dict(failures=[f_slip_persist(C), f_ik("pick", M)], route=slip_r),
                   "ik_mug_away": dict(move={M: P("tv_stand_2/top", 7.75, 0.36)},
                                       failures=[f_ik_persist("pick", C), f_grasp(M)], route=ik_r)}),
        "x6_dr_spot_filled_dynamic": dict(
            base="cup_available", control="cup_available", goal=spot_goal,
            challenge="right after the robot picks the cup, someone puts the pot lid and the oatmeal bowl (or a toy "
                      "block) on the drinks spot",
            rationale="the destination is now full for any drink: set the cup down, move what stands in the way (the "
                      "bowl, or the toy block next to the lid) to the other low cabinet, then set the cup; neither is a "
                      "goal object",
            factor="what occupies the destination (occupancy)",
            cases={"bowl": dict(failures=filled, route=make_room("oatmeal")),
                   "block": dict(move={"wooden_block_a": P("kitchen_island/top", 7.2, 1.85)}, failures=filled_block,
                                 route=make_room("wooden_block_a"))}),
    }


def T05(t):
    base = OR(t, "h_task_pencil_in_cabinet")
    tail_desk = [nav("desk_1/top"), place("pencil", "desk_1/top")]
    nominal = RT(t, "nominal")                          # nav bookcase, look, nav pen, pick pen, nav desk, place pen
    pen_fail = nominal[:3] + refused_twice(nominal[3])
    cab_goal = copy.deepcopy(t["variants"]["h_task_pencil_in_cabinet"]["goal"])
    cab_goal["all"].append(["is_closed", "kitchen_cabinet_4"])
    two_cab = ("The kid needs something to write with for homework. Bring a pen to the study desk; if there is no "
               "pen, a pencil. Pens and pencils are kept in the two low kitchen cabinets; close them again afterwards.")
    other_cab = ("The kid needs something to write with for homework. Bring a pen to the study desk; if there is no "
                 "pen, a pencil. The pencils are kept in the low wall cabinet; close it again afterwards.")
    in4 = {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 90}

    def fetch(x, art):
        return [nav(x), pick(x), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]
    other = open_explore("kitchen_cabinet_6") + [S("close", articulated="kitchen_cabinet_6")] \
        + open_explore("kitchen_cabinet_4") + fetch("pencil", "kitchen_cabinet_4") + tail_desk
    pen4 = open_explore("kitchen_cabinet_6") + [S("close", articulated="kitchen_cabinet_6")] \
        + open_explore("kitchen_cabinet_4") + fetch("pen", "kitchen_cabinet_4") + [nav("desk_1/top"), place("pen", "desk_1/top")]
    pen6 = open_explore("kitchen_cabinet_4") + [S("close", articulated="kitchen_cabinet_4")] \
        + open_explore("kitchen_cabinet_6") + fetch("pen", "kitchen_cabinet_6") + [nav("desk_1/top"), place("pen", "desk_1/top")]
    pen_goal = {"all": [["on", "pen", "desk_1/top"], ["hand_empty", "right"], ["is_closed", "kitchen_cabinet_6"],
                        ["is_closed", "kitchen_cabinet_4"]]}
    return {
        "x6_cl_pen_unholdable": dict(
            base="pen_available", control="pen_available", contrast="no_pen",
            factor="where the substitute is",
            challenge="a pen lies on the bookcase but cannot be held (it slips from the pinch every time); the pencil "
                      "is on the bookcase too, or in another room",
            rationale="the pen is there, so 'no pen' is not observable: only the repeated grasp failure tells the "
                      "planner to fall back to the pencil the instruction allows (cross-level); the control no_pen "
                      "has no pen at all",
            cases={"pencil_here": dict(failures=[f_grasp_persist("pen"), f_ik("place", "pencil")],
                                       route=with_ik(pen_fail + recs(nav("pencil"), pick("pencil"), *tail_desk),
                                                     "place", "pencil")),
                   "pencil_away": dict(move={"pencil": P("dining_table_2/top", 3.7, 6.3)},
                                       failures=[f_grasp_persist("pen"), f_ik("place", "pencil")],
                                       route=with_ik(pen_fail + recs(S("search", object="pencil", region="dining_room_0_1"),
                                                                     nav("pencil"), pick("pencil"), *tail_desk),
                                                     "place", "pencil"))}),
        "x6_gd_pencil_other_cabinet": dict(
            base="h_task_pencil_in_cabinet", control="h_task_pencil_in_cabinet",
            move={"pencil": in4}, goal=cab_goal, instruction=other_cab,
            challenge="the pencil is not in the low wall cabinet the instruction names but in the other low cabinet",
            rationale="the expected location is empty: the search decomposes over the candidate cabinets (inspect the "
                      "second one, open and close both); the door is a precondition of the pick",
            cases={"": dict(failures=[f_initial("resource", [["on", "pencil", "kitchen_cabinet_4/inside_shelf"]],
                                                fid="resource_pencil_elsewhere")], route=other)}),
        "x6_gd_pen_or_pencil_cabinets": dict(
            base="h_task_pencil_in_cabinet", control="h_task_pencil_in_cabinet",
            factor="which cabinet holds the preferred item",
            instruction=two_cab,
            challenge="writing things are in the two low cabinets: a pencil in one, the pen in the other (seed "
                      "decides which)",
            rationale="the preference (a pen if there is one) makes finding the pencil insufficient: the cabinets are "
                      "inspected until the pen is found (reference route: the pencil's cabinet first)",
            cases={"pen_in_4": dict(move={"pen": in4}, goal=pen_goal, route=pen4,
                                    failures=[f_initial("resource", [["on", "pen", "kitchen_cabinet_4/inside_shelf"]],
                                                        fid="resource_pen_in_cabinet")]),
                   "pen_in_6": dict(move={"pen": {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.63, 0.36], "yaw_deg": 90},
                                          "pencil": in4}, goal=pen_goal, route=pen6,
                                    failures=[f_initial("resource", [["on", "pen", "kitchen_cabinet_6/inside_shelf"]],
                                                        fid="resource_pen_in_cabinet")])}),
    }


def T06(t):
    A, B = "wooden_block_a", "wooden_block_b"
    base = OR(t, "free")                                 # look, nav A, pick A, nav cab6, place A cab6
    fail_a = base[:2] + refused_twice(base[2])
    to_b = recs(nav(B), pick(B), nav("kitchen_cabinet_6/top"), place(B, "kitchen_cabinet_6/top"))
    dining_b = recs(S("search", object=B, region="dining_room_0_1")) + to_b
    unreach = with_grasp(base[:4], A) + refused_twice(base[4], "kitchen_cabinet_6/top") \
        + recs(nav("tv_stand_2/top"), place(A, "tv_stand_2/top"))
    displays = {"all": [["hand_empty", "right"]],
                "any": [[["on", x, "kitchen_cabinet_6/top"], ["on", y, "tv_stand_2/top"]] for x, y in ((A, B), (B, A))]}
    two = lambda *sr: base[:5] + recs(S("search", object=B, **dict(sr)), nav(B), pick(B), nav("tv_stand_2/top"),  # noqa: E731
                                      place(B, "tv_stand_2/top"))
    return {
        "x6_cl_block_a_unholdable": dict(
            base="free", control="x6_m_grasp_block_a",
            factor="where the substitute is",
            challenge="block A slips out of the fingers at every pick; block B (on the island or left on the dining "
                      "table) slips once at the start of its carry",
            rationale="the goal accepts either block: after A fails persistently the object changes to B (found "
                      "where it is), a transient slip of B only needs a re-pick",
            cases={"b_island": dict(failures=[f_grasp_persist(A), f_slip(B)], route=with_slip(fail_a + to_b, B)),
                   "b_dining": dict(move={B: P("dining_table_2/top", 3.7, 6.3)},
                                    failures=[f_grasp_persist(A), f_slip(B)], route=with_slip(fail_a + dining_b, B))}),
        "x6_m_grasp_block_a": dict(
            base="free", control="free",
            challenge="block A slips from the fingers on the first pick",
            rationale="matched control of x6_cl_block_a_unholdable: transient, the second pick works",
            cases={"": dict(failures=[f_grasp(A)], route=with_grasp(base, A))}),
        "x6_cl_cabinet_unreachable": dict(
            base="free", control="x6_m_ik_place_cabinet",
            challenge="block A slips on the first pick; then the cabinet top cannot be reached from any park",
            rationale="re-parking does not help (persistent refusal pinned to the cabinet): the destination changes "
                      "to the TV stand, the other display the instruction allows",
            cases={"": dict(failures=[f_grasp(A), f_ik_persist("place", A, receptacle="kitchen_cabinet_6/top")],
                            route=unreach)}),
        "x6_m_ik_place_cabinet": dict(
            base="free", control="free",
            challenge="the first place on the cabinet top is refused from its park",
            rationale="matched control of x6_cl_cabinet_unreachable: one re-park fixes it",
            cases={"": dict(failures=[f_ik("place", A)], route=with_ik(base, "place", A))}),
        "x6_gd_two_displays_event": dict(
            base="free", control="free", goal=displays,
            instruction="Put both toy blocks on display: one on the low wall cabinet and one on the TV stand, so they "
                        "can be seen from both rooms.",
            challenge="two blocks to two displays; once the first block is on the cabinet, the kid carries the other "
                      "block to the dining table",
            rationale="the goal decomposes into one placement per display; the event moves the second resource after "
                      "the first subgoal holds: keep block A where it is, find block B",
            factor="where the event takes the resource",
            cases={"dining": dict(failures=[f_move("resource", B, P("dining_table_2/top", 3.7, 6.3),
                                                   ("place", {"object": A}), fid="resource_block_b")],
                                  route=two(("region", "dining_room_0_1"))),
                   "cabinet4": dict(failures=[f_move("resource", B, P("kitchen_cabinet_4/top", 1.4, 0.42),
                                                     ("place", {"object": A}), fid="resource_block_b")], route=two())}),
    }


def T07(t):
    X, MW = "oatmeal", "kitchen_microwave"
    base = OR(t, "microwave_works")      # nav mw, open, look island, nav oat, pick, nav mw floor, place, close, heat
    stove = [nav("kitchen_stove/top"), place(X, "kitchen_stove/top"), S("heat", food=X, appliance="kitchen_stove", temp_c=40)]
    stuck_island = base[:1] + refused_twice(base[1], MW) + with_ik(recs(look("kitchen_island/top"), nav(X), pick(X), *stove),
                                                                   "pick", X)
    # the bowl on the wall cabinet: re-park with navigate (turning in place at an approach park hits furniture)
    stuck_cab = base[:1] + refused_twice(base[1], MW) + recs(S("search", object=X, region="living_room_0_0"), nav(X)) \
        + [FAIL(pick(X), True)] + recs(nav(X), pick(X), *stove)
    stuck_fail = [f_ik_persist("open", MW, key="articulated"), f_ik("pick", X)]
    holds = t["variants"]["microwave_holds_pot"]
    pot_in = [f_move("resource", "handled_cooking_pot", P("kitchen_microwave/inside_floor", 4.5, 2.5),
                     ("look", {"target": "kitchen_island/top"}), fid="resource_microwave_taken"),
              {**f_move("resource", "pot_lid", {"support": None, "z": 0.88, "xy": [4.5, 2.5], "yaw_deg": 0.0},
                        ("look", {"target": "kitchen_island/top"}), fid="resource_microwave_lid"),
               "after_fired": "resource_microwave_taken"}]
    taken = base[:6] + recs(look("kitchen_microwave/inside_floor"), S("close", articulated=MW), *stove)
    reopened = base + recs(S("close", articulated=MW))
    return {
        "x6_cl_microwave_door_stuck": dict(
            base="microwave_works", control="x6_m_ik_open_microwave",
            factor="where the food is",
            challenge="the microwave door cannot be opened from any park; the first pick of the bowl is refused (the "
                      "bowl is on the island, or on the wall cabinet out of view)",
            rationale="the microwave procedure is unavailable (persistent): heat on the stove instead; the microwave "
                      "stays closed, which the goal requires anyway",
            cases={"oatmeal_island": dict(failures=stuck_fail, route=stuck_island),
                   "oatmeal_cabinet": dict(move={X: P("kitchen_cabinet_6/top", 3.7, 0.36)}, failures=stuck_fail,
                                           route=stuck_cab)}),
        "x6_m_ik_open_microwave": dict(
            base="microwave_works", control="microwave_works",
            challenge="the first open of the microwave door is refused from its park",
            rationale="matched control of x6_cl_microwave_door_stuck: one re-park fixes it",
            cases={"": dict(failures=[f_ik("open", MW, key="articulated")],
                            route=with_ik(base, "open", MW, key="articulated"))}),
        "x6_sr_microwave_taken": dict(
            base="microwave_works", control="microwave_works",
            goal=copy.deepcopy(holds["goal"]),
            challenge="while the robot fetches the bowl, someone puts the covered soup pot into the open microwave",
            rationale="the appliance is occupied after the plan was made: the robot sees it on arrival, closes the "
                      "door and heats on the stove (now free) instead; the pot must not be taken out onto the floor",
            cases={"": dict(failures=pot_in, route=taken)}),
        "x6_pp_door_opened_after_heat": dict(
            base="microwave_works", control="microwave_works",
            challenge="right after the oatmeal is warm, someone opens the microwave door to look",
            rationale="the heating subgoal already holds; only the door subgoal is undone: close it again without "
                      "re-heating (re-running the plan would heat again)",
            cases={"": dict(failures=[f_joint("dependency", MW, "open", ("heat", {"food": X, "appliance": MW}))],
                            route=reopened)}),
    }


def T08(t):
    X = "kitchen_sponge"
    base = OR(t, "sponge_on_island")
    back = base + recs(look("kitchen_island/top"), S("search", object=X), nav(X), pick(X),
                       nav("kitchen_island/top"), place(X, "kitchen_island/top"))
    tv = OR(t, "sponge_on_tv_stand")
    return {
        "x6_cl_sponge_behind_mug": dict(
            base="sponge_on_tv_stand", control="m_grasp_sponge",
            move={X: P("tv_stand_2/top", 7.6, 0.245, 180.0), "mug": P("tv_stand_2/top", 7.6, 0.36)},
            challenge="the sponge lies at the back of the TV stand, against the wall, with a mug right in front of it",
            rationale="no park reaches the sponge while the mug is in front and the wall behind (persistent until the "
                      "mug is moved): insert the subgoal of moving the mug, then fetch the sponge",
            cases={"": dict(failures=[f_initial("dependency", [["on", "mug", "tv_stand_2/top"]], fid="dependency_in_front"),
                                      {**f_ik_persist("pick", X), "until_moved": "mug"}],
                            route=behind_wall(tv, X, "mug", ("tv_stand_2/top", [7.0, 0.36])))}),
        "x6_pp_sponge_taken_after_wipe": dict(
            base="sponge_on_island", control="sponge_on_island",
            challenge="right after the robot puts the sponge down on the wiped island, someone takes it to the TV stand",
            rationale="the island is already wiped; only the sponge subgoal is undone: fetch the sponge back without "
                      "wiping again",
            factor="where the event takes the resource",
            cases={c: dict(failures=[f_move("resource", X, to, ("place", {"object": X}), fid="resource_sponge")],
                           route=back[:-4] + recs(look(where)) + back[-4:])
                   for c, to, where in (("tv_stand", P("tv_stand_2/top", 7.6, 0.38), "tv_stand_2/top"),
                                        ("cabinet6", P("kitchen_cabinet_6/top", 3.7, 0.36), "kitchen_cabinet_6/top"))}),
    }


def T09(t):
    SP, POT, LID = "breakfast_spoon", "handled_cooking_pot", "pot_lid"
    base = OR(t, "lid_off")        # look, collect, nav spoon, pick spoon, nav pot, stir, nav island, place spoon,
    #                                nav lid, pick lid, nav pot, cover, nav stove, heat
    i_sp = at(base, "pick", object=SP)
    lid_tail = base[at(base, "navigate", destination=LID):]

    def alt_spoon(spoon, pre=()):
        return recs(*pre, nav(spoon), pick(spoon), nav(POT), S("stir", container=POT, tool=spoon),
                    nav("kitchen_island/top"), place(spoon, "kitchen_island/top"))
    spoon_fail = base[:i_sp] + refused_twice(base[i_sp])
    cabinet = with_ik(spoon_fail + alt_spoon("spoon_kitchen_cabinet") + lid_tail, "pick", LID)
    dining = with_ik(spoon_fail + alt_spoon("spoon_target_table", (S("search", object="spoon_target_table",
                                                                      region="dining_room_0_1"),)) + lid_tail, "pick", LID)
    col = base[1]
    per_item = recs(nav(TOMATOES[0]), pick(TOMATOES[0]), nav(POT), S("drop", object=TOMATOES[0], container=POT),
                    nav(TOMATOES[1]), pick(TOMATOES[1]), nav(POT), S("drop", object=TOMATOES[1], container=POT))
    split = base[:1] + refused_twice(col, POT) + with_grasp(per_item, TOMATOES[0]) + base[2:]
    j_lid = at(base, "navigate", destination=LID)
    lid_taken = lambda *sr: base[:j_lid] + recs(look("kitchen_stove/top"), S("search", object=LID, **dict(sr))) + base[j_lid:]  # noqa: E731
    tomato_out = lambda x: base[:2] + recs(look("kitchen_island/top"), nav(x), pick(x), nav(POT),  # noqa: E731
                                           S("drop", object=x, container=POT)) + base[2:]
    kept_tomato = {"atom": ["inside", TOMATOES[0], POT], "by": {"skill": "collect", "args": {"container": POT}}}

    def apart(region):
        return base[:1] + recs(S("collect", objects=[TOMATOES[0]], container=POT),
                               S("search", object=TOMATOES[1], region=region), nav(TOMATOES[1]), pick(TOMATOES[1]),
                               nav(POT), S("drop", object=TOMATOES[1], container=POT)) + base[2:]
    return {
        "x6_cl_spoon_unholdable": dict(
            base="lid_off", control="m_grasp_spoon",
            factor="which substitute exists and where",
            challenge="once the tomatoes are in the pot, the breakfast spoon cannot be held (it slips every time); "
                      "another spoon is on the wall cabinet, or only one on the dining table; the first lid pick is "
                      "refused",
            rationale="stirring needs a spoon, not this spoon: switch to another spoon (found where it is) and keep "
                      "the tomatoes in the pot",
            cases={"spoon_cabinet": dict(failures=[f_grasp_persist(SP), f_ik("pick", LID)], route=cabinet),
                   "spoon_dining": dict(remove=["spoon_kitchen_cabinet"], failures=[f_grasp_persist(SP), f_ik("pick", LID)],
                                        route=dining)}),
        "x6_sr_collect_refused": dict(
            base="lid_off", control="x6_m_ik_collect",
            challenge="collecting both tomatoes into the pot at once is refused from every park; the first single "
                      "tomato pick slips",
            rationale="the batch skill is unavailable (persistent): decompose into one pick-and-drop per tomato",
            cases={"": dict(failures=[f_ik_where("collect", "ik_collect_persistent", container=POT),
                                      f_grasp(TOMATOES[0])], route=split)}),
        "x6_gd_tomato_elsewhere": dict(
            conditions=["multi_object_goal"], base="lid_off", control="lid_off",
            factor="where the second tomato was left",
            challenge="one cherry tomato is on the island, the other was left on the dining table or on the wall "
                      "cabinet",
            rationale="collecting both at once only works for tomatoes on one surface: split the batch, collect the "
                      "near one, fetch the other on its own",
            cases={c: dict(move={TOMATOES[1]: to},
                           failures=[f_initial("resource", [["on", TOMATOES[1], to["support"]]], fid="resource_tomato_apart")],
                           route=apart(region))
                   for c, to, region in (("dining", P("dining_table_2/top", 3.7, 6.3), "dining_room_0_1"),
                                         ("cabinet6", P("kitchen_cabinet_6/top", 3.7, 0.36), "living_room_0_0"))}),
        "x6_m_ik_collect": dict(
            base="lid_off", control="lid_off",
            challenge="the first collect into the pot is refused from its park",
            rationale="matched control of x6_sr_collect_refused: one re-park fixes it",
            cases={"": dict(failures=[f_ik_where("collect", "ik_collect_once", container=POT) | {"persist": False,
                                                                                                "until": "base_skill"}],
                            route=base[:1] + [FAIL(col, True)] + recs(S("approach", target=POT), col) + base[2:])}),
        "x6_pp_lid_taken_after_stir": dict(
            base="lid_off", control="lid_off",
            challenge="right after the robot stirs, someone takes the pot lid to the other low cabinet",
            rationale="tomatoes in and stirred already hold: find the lid and cover; do not collect or stir again",
            factor="where the event takes the resource",
            cases={"cabinet4": dict(failures=[f_move("resource", LID, P("kitchen_cabinet_4/top", 1.4, 0.42),
                                                     ("stir", {"container": POT}), fid="resource_lid")], route=lid_taken()),
                   "dining": dict(failures=[f_move("resource", LID, P("dining_table_2/top", 3.7, 6.3),
                                                   ("stir", {"container": POT}), fid="resource_lid")],
                                  route=lid_taken(("region", "dining_room_0_1")))}),
        "x6_pp_tomato_taken_out": dict(
            base="lid_off", control="lid_off",
            challenge="right after the tomatoes go into the pot, the kid takes one back out onto the island",
            rationale="one subgoal is undone, the other still holds: put back only the missing tomato",
            factor="which subgoal the event undoes, and when (failure timing)",
            cases={**{f"tomato{x[-1]}": dict(
                failures=[f_move("resource", x, P("kitchen_island/top", 7.8 if x == TOMATOES[1] else 7.63, 1.62),
                                 ("collect", {"container": POT}), fid="resource_tomato")], route=tomato_out(x))
                for x, y in ((TOMATOES[1], TOMATOES[0]), (TOMATOES[0], TOMATOES[1]))},
                "tomato2_after_stir": dict(
                    failures=[f_move("resource", TOMATOES[1], P("kitchen_island/top", 7.8, 1.62),
                                     ("stir", {"container": POT}), fid="resource_tomato")],
                    route=base[:at(base, "place", object=SP) + 1] + recs(look("kitchen_island/top"), nav(TOMATOES[1]),
                                                                          pick(TOMATOES[1]), nav(POT),
                                                                          S("drop", object=TOMATOES[1], container=POT))
                    + base[at(base, "place", object=SP) + 1:])}),
    }


def T10(t):
    CAN = "soda_can"
    instr = ("Someone put the empty soda can away in the microwave or in the low wall cabinet instead of throwing it "
             "out. Throw it into the trash can, and close whatever you open.")
    goal = {"all": [["inside", CAN, "trash_can"], ["hand_empty", "right"], ["is_closed", "kitchen_microwave"],
                    ["is_closed", "kitchen_cabinet_6"]]}
    mw = [nav("kitchen_microwave"), S("open", articulated="kitchen_microwave"), look("kitchen_microwave/inside_floor")]
    take = lambda art: [nav(CAN), pick(CAN), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art),  # noqa: E731
                        nav("trash_can"), S("drop", object=CAN, container="trash_can")]
    in_cab = {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.63, 0.36], "yaw_deg": 0.0}
    in_mw = copy.deepcopy(t["variants"]["h_task_can_in_microwave"]["move"][CAN])
    base = OR(t, "can_on_island")
    j = at(base, "drop", object=CAN)
    on_tv = recs(look("tv_stand_2/top")) + base[1:]
    return {
        "x6_cl_can_behind_bottle": dict(
            base="can_on_island", control="m_ik_can",
            move={CAN: P("tv_stand_2/top", 7.2, 0.245), "juice_bottle": P("tv_stand_2/top", 7.2, 0.33)},
            challenge="the can stands at the back of the TV stand, against the wall, with the juice bottle right in front",
            rationale="no park reaches the can while the bottle blocks it (persistent until the bottle is moved): move "
                      "the bottle aside first",
            cases={"": dict(failures=[f_initial("dependency", [["on", "juice_bottle", "tv_stand_2/top"]],
                                                fid="dependency_in_front"),
                                      {**f_ik_persist("pick", CAN), "until_moved": "juice_bottle"}],
                            route=behind_wall(on_tv, CAN, "juice_bottle", ("tv_stand_2/top", [7.7, 0.36])))}),
        "x6_gd_can_put_away": dict(
            conditions=["item_put_away"], base="can_on_island", control="h_task_can_in_microwave",
            factor="which closed place holds the item",
            instruction=instr, goal=goal, remove=["plate_inside_kitchen_cabinet"],
            challenge="the can was put away in one of two closed places (microwave or wall cabinet)",
            rationale="the item's location is a disjunction the planner must resolve by inspecting both candidates "
                      "(reference route: the worse order, the can is in the second place); each door is opened "
                      "and closed again",
            cases={"in_cabinet": dict(move={CAN: in_cab}, route=mw + [S("close", articulated="kitchen_microwave")]
                                      + open_explore("kitchen_cabinet_6") + take("kitchen_cabinet_6"),
                                      failures=[f_initial("resource", [["on", CAN, "kitchen_cabinet_6/inside_shelf"]],
                                                          fid="resource_can_put_away")]),
                   "in_microwave": dict(move={CAN: in_mw}, route=open_explore("kitchen_cabinet_6")
                                        + [S("close", articulated="kitchen_cabinet_6")] + mw + take("kitchen_microwave"),
                                        failures=[f_initial("resource", [["on", CAN, "kitchen_microwave/inside_floor"]],
                                                            fid="resource_can_put_away")])}),
        "x6_sr_drop_refused": dict(
            base="can_on_island", control="x6_m_ik_drop",
            challenge="dropping the can over the trash can is refused from every park; the first pick is refused",
            rationale="the drop procedure is unavailable (persistent): put the can into the trash can with a place "
                      "instead",
            cases={"": dict(failures=[f_ik("pick", CAN), f_ik_where("drop", "ik_drop_trash_persistent", container="trash_can")],
                            route=with_ik(base[:j], "pick", CAN) + refused_twice(base[j], "trash_can")
                            + recs(place(CAN, "trash_can")))}),
        "x6_m_ik_drop": dict(
            base="can_on_island", control="can_on_island",
            challenge="the first drop over the trash can is refused from its park",
            rationale="matched control of x6_sr_drop_refused: one re-park fixes it",
            cases={"": dict(failures=[f_ik("drop", CAN)], route=with_ik(base, "drop", CAN))}),
    }


def T12(t):
    CAR, DUCK, BASKET = "toy_car", "rubber_duck", "storage_basket"
    base = OR(t, "toys_out")         # explore, explore, nav car, pick, nav basket, place, nav duck, pick, nav basket, place, nod
    tray = copy.deepcopy(t["variants"]["toys_everywhere"]["add"]["toy_tray"])
    small = copy.deepcopy(t["variants"]["toys_everywhere"]["add"]["toy_bin_small"])
    goal = {"all": [["upright", BASKET], ["hand_empty", "right"]],
            "any": [[["inside", CAR, a], ["inside", DUCK, b]] for a in (BASKET, "toy_tray") for b in (BASKET, "toy_bin_small")]}
    i = at(base, "place", object=CAR)
    unreach = with_grasp(base[:i], CAR) + refused_twice(base[i], BASKET) \
        + recs(nav("bookcase_2/top"), look("bookcase_2/top"), place(CAR, "toy_tray"), nav(DUCK), pick(DUCK),
               nav("toy_bin_small"), S("drop", object=DUCK, container="toy_bin_small"))
    k = at(base, "navigate", destination=DUCK)
    ev = t["variants"]["toys_everywhere"]
    bins = {"left": (0.84, -0.43), "right": (1.13, -0.43)}
    names = {"left": "toy_bin_small", "right": "toy_bin_small_2"}

    def half_full(side):
        """the six stored blocks in the ``side`` bin (two columns, the duck's gap in the middle)"""
        x0, y0 = bins[side]
        return {f"stored_block_{i + 1}": {"asset": "wooden_block", "support": None, "z": 0.718,
                                          "xy": [round(x0 + dx, 3), round(y0 + dy, 3)], "yaw_deg": 0}
                for i, (dx, dy) in enumerate((a, b) for a in (-0.078, 0.078) for b in (-0.055, 0.0, 0.055))}

    def cap_case(full):
        empty = "right" if full == "left" else "left"
        add = {names["left"]: {"asset": "small_storage_bin", "support": "bookcase_2/top", "xy": list(bins["left"]), "yaw_deg": 0.0},
               names["right"]: {"asset": "small_storage_bin", "support": "bookcase_2/top", "xy": list(bins["right"]), "yaw_deg": 0.0},
               **half_full(full)}
        goal = {"all": [["fully_inside", f"stored_block_{i}", names[full]] for i in range(1, 7)]
                + [["fully_inside", CAR, names[empty]], ["fully_inside", DUCK, names[full]], ["upright", names[full]],
                   ["upright", names[empty]], ["hand_empty", "right"]]}
        route = [nav("bookcase_2/top"), look("bookcase_2/top"), S("measure", object=names["left"]),
                 S("measure", object=names["right"]), S("explore_room", room="living_room_0_0"), nav(CAR), pick(CAR),
                 nav(names[empty]), place(CAR, names[empty]), S("search", object=DUCK, region="living_room_0_1"),
                 nav(DUCK), pick(DUCK), nav(names[full]), S("drop", object=DUCK, container=names[full])]
        return dict(add=add, goal=goal, route=route)
    moved = lambda region: base[:k] + recs(S("search", object=DUCK, region=region)) + base[k:]  # noqa: E731
    return {
        "x6_gd_bins_capacity": dict(
            conditions=["multi_object_goal"], base="toys_out", control="toys_everywhere",
            remove=[BASKET], move={DUCK: copy.deepcopy(ev["move"][DUCK])}, watch=[CAR, DUCK, names["left"], names["right"]],
            may_end_on_floor=[CAR],
            instruction="It is nearly bedtime. Put the kid's toy car and rubber duck away into the two small toy bins on "
                        "the bedroom bookcase, each toy completely inside a bin.",
            factor="which bin is already half full (capacity)",
            challenge="no storage basket; two small bins on the bookcase, one of them already half full of blocks (seed "
                      "decides which); the car is on the living-room floor, the duck on the study desk",
            rationale="the half-full bin only has room for the duck (between the block columns), the car needs the "
                      "empty bin: allocate by remaining capacity, which flips with the seed",
            cases={"left_full": cap_case("left"), "right_full": cap_case("right")}),
        "x6_cl_basket_unreachable": dict(
            base="toys_out", control="m_ik_duck_place",
            add={"toy_tray": tray, "toy_bin_small": small}, goal=goal, watch=[CAR, DUCK, BASKET, "toy_tray", "toy_bin_small"],
            instruction="It is nearly bedtime. Put the kid's toy car and rubber duck away in the storage basket in the "
                        "bedroom; if you cannot get them into it, use the toy tray and the small toy bin on the bedroom "
                        "bookcase (the duck is too tall for the tray).",
            challenge="the car slips on its first pick; then nothing can be put into the basket from any park",
            rationale="the basket is unreachable for every toy (persistent, pinned to the basket): the destinations "
                      "change to the stated tray (car) and small bin (duck), without trying the basket for the duck",
            cases={"": dict(failures=[f_grasp(CAR), f_ik_where("place", "ik_place_basket_persistent", receptacle=BASKET)],
                            route=unreach)}),
        "x6_pp_duck_moved": dict(
            base="toys_out", control="toys_out",
            factor="where the event takes the resource",
            challenge="once the car is in the basket, the kid carries the duck to another room (dining table or "
                      "study desk)",
            rationale="the car subgoal holds; the duck must be found where it went: keep the car, search the duck",
            cases={"dining": dict(failures=[f_move("resource", DUCK, P("dining_table_2/top", 3.7, 6.3),
                                                   ("place", {"object": CAR}), fid="resource_duck")],
                                  route=moved("dining_room_0_1")),
                   "study": dict(failures=[f_move("resource", DUCK, P("desk_1/top", -0.95, -6.02, 128.7),
                                                  ("place", {"object": CAR}), fid="resource_duck")],
                                 route=moved("living_room_0_1"))}),
    }


def T13(t):
    BOWL, CUP, MUG, SPOON = "bowl", "cup", "mug", "spoon"
    base = OR(t, "dishes_on_tv_stand")   # look dining, nav tv, look tv, nav bowl, pick bowl, nav dining, place bowl,
    #                                       nav cup, pick cup, nav dining, place cup
    i = at(base, "pick", object=CUP)
    mug_tail = lambda pre: recs(*pre, nav(MUG), pick(MUG), nav("dining_table_2/top"),  # noqa: E731
                                place(MUG, "dining_table_2/top", [3.2, 7.4]))
    slips = lambda pre: (with_ik(base[:i + 1], "pick", BOWL) + [FAIL(base[i + 1], True)]  # noqa: E731
                         + recs(S("approach", target=CUP), look(CUP), pick(CUP)) + [FAIL(base[i + 1], True)] + mug_tail(pre))
    spoon_back = lambda pre: base + recs(look("dining_table_2/top"), *pre, nav(SPOON), pick(SPOON),  # noqa: E731
                                         nav("dining_table_2/top"), place(SPOON, "dining_table_2/top", [2.98, 7.46]))
    put_away = ("Set the dining table for breakfast. The spoon is already there; bring a bowl and a cup and put them "
                "next to it. A mug is fine if there is no cup. The clean bowls were put away in the low wall cabinet "
                "or the microwave; close whatever you open.")
    g = copy.deepcopy(t["goal"])
    g["all"] += [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_microwave"]]
    mw = [nav("kitchen_microwave"), S("open", articulated="kitchen_microwave"), look("kitchen_microwave/inside_floor")]
    take = lambda art: [nav(BOWL), pick(BOWL), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]  # noqa: E731
    set_rest = [nav("dining_table_2/top"), place(BOWL, "dining_table_2/top", [3.05, 7.1])] + base[at(base, "navigate", destination=CUP):]
    head = base[:3]
    b2, s2 = "bowl_kitchen_cabinet", "spoon_target_table"
    two_goal = {"all": [["on", BOWL, "dining_table_2/top"], ["on", b2, "dining_table_2/top"], ["upright", BOWL],
                        ["upright", b2], ["hand_empty", "right"]],
                "any": [[["grouped", [x, c1, SPOON], "dining_table_2/top", 0.5], ["grouped", [y, c2, s2], "dining_table_2/top", 0.5],
                         ["upright", c1], ["upright", c2]]
                        for x, y in ((BOWL, b2), (b2, BOWL)) for c1, c2 in ((CUP, MUG), (MUG, CUP))]}
    two = lambda *sr: base + recs(nav(b2), pick(b2), nav("dining_table_2/top"), place(b2, "dining_table_2/top", [3.7, 7.12]),  # noqa: E731
                                  S("search", object=MUG, **dict(sr)), nav(MUG), pick(MUG), nav("dining_table_2/top"),
                                  place(MUG, "dining_table_2/top", [3.62, 7.62]))
    kept_bowl = {"atom": ["on", BOWL, "dining_table_2/top"], "by": {"skill": "place", "args": {"object": BOWL}}}
    return {
        "x6_cl_cup_slips": dict(
            base="dishes_on_tv_stand", control="x6_m_slip_cup",
            factor="where the substitute is",
            challenge="the first bowl pick is refused (re-park); once the bowl is set, the cup slips out of the hand "
                      "at every carry; the mug is on the bedroom bookcase or on the wall cabinet",
            rationale="the cup cannot be carried at all: the instruction allows a mug, found where it is; the bowl "
                      "on the table stays",
            cases={"mug_bookcase": dict(route=slips([nav("bookcase_2/top"), look("bookcase_2/top")])),
                   "mug_cabinet": dict(move={MUG: P("kitchen_cabinet_6/top", 3.68, 0.36)},
                                       route=slips([S("search", object=MUG, region="living_room_0_0")]))},
            failures=[f_ik("pick", BOWL), f_slip_persist(CUP)]),
        "x6_m_slip_cup": dict(
            base="dishes_on_tv_stand", control="dishes_on_tv_stand",
            challenge="the cup slips once at the start of its carry",
            rationale="matched control of x6_cl_cup_slips: transient, picking it again works",
            cases={"": dict(failures=[f_slip(CUP)], route=with_slip(base, CUP))}),
        "x6_pp_spoon_moved": dict(
            base="dishes_on_tv_stand", control="dishes_on_tv_stand",
            factor="where the event takes the resource, and when (failure timing)",
            challenge="the kid moves the spoon away (to the far end of the table, or to the TV stand), right after the "
                      "cup is set or already right after the bowl is set",
            rationale="bowl and cup are in place; only the grouping is broken: bring the spoon back next to them "
                      "instead of moving the dishes",
            cases={"early": dict(failures=[f_move("resource", SPOON, P("dining_table_2/top", 3.6, 5.75),
                                                  ("place", {"object": BOWL}), fid="resource_spoon")],
                                 route=base[:at(base, "place", object=BOWL) + 1]
                                 + recs(look("dining_table_2/top"), nav(SPOON), pick(SPOON), nav("dining_table_2/top"),
                                        place(SPOON, "dining_table_2/top", [2.98, 7.46]))
                                 + base[at(base, "place", object=BOWL) + 1:]),
                   "table_end": dict(failures=[f_move("resource", SPOON, P("dining_table_2/top", 3.6, 5.75),
                                                      ("place", {"object": CUP}), fid="resource_spoon")],
                                     route=spoon_back([])),
                   "tv_stand": dict(failures=[f_move("resource", SPOON, P("tv_stand_2/top", 7.0, 0.36),
                                                     ("place", {"object": CUP}), fid="resource_spoon")],
                                    route=spoon_back([S("search", object=SPOON, region="living_room_0_0")]))}),
        "x6_gd_bowl_put_away": dict(
            conditions=["item_put_away"], base="dishes_on_tv_stand", control="bowl_on_cabinet",
            factor="which closed place holds the item",
            instruction=put_away, goal=g, remove=["bowl_inside_kitchen_cabinet", "plate_inside_kitchen_cabinet"],
            challenge="no bowl is out: the clean bowl was put away in the wall cabinet or the microwave",
            rationale="the bowl's location is a disjunction resolved by inspecting both places (reference route: the "
                      "worse order); the cup is set as usual and the doors are closed again",
            cases={"in_cabinet": dict(move={BOWL: {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.5, 0.36], "yaw_deg": 0.0}},
                                      failures=[f_initial("resource", [["on", BOWL, "kitchen_cabinet_6/inside_shelf"]],
                                                          fid="resource_bowl_put_away")],
                                      route=head + mw + [S("close", articulated="kitchen_microwave")]
                                      + open_explore("kitchen_cabinet_6") + take("kitchen_cabinet_6") + set_rest),
                   "in_microwave": dict(move={BOWL: {"support": "kitchen_microwave/inside_floor", "xy": [1.8, 9.5], "yaw_deg": 0.0}},
                                        failures=[f_initial("resource", [["on", BOWL, "kitchen_microwave/inside_floor"]],
                                                            fid="resource_bowl_put_away")],
                                        route=head + open_explore("kitchen_cabinet_6") + [S("close", articulated="kitchen_cabinet_6")]
                                        + mw + take("kitchen_microwave") + set_rest)}),
        "x6_gd_two_settings": dict(
            base="dishes_on_tv_stand", control="dishes_on_tv_stand",
            move={b2: P("tv_stand_2/top", 6.9, 0.36)}, goal=two_goal, watch=[BOWL, b2, CUP, MUG, SPOON, s2],
            instruction="Set two breakfast places at the dining table: next to each spoon, a bowl and a cup (a mug is "
                        "fine where there is no cup).",
            challenge="two places, two bowls on the TV stand, one cup and the mug; once the first place is set, "
                      "someone takes the mug to the wall cabinet",
            rationale="the goal decomposes into two place settings with an allocation of the cups and bowls; the "
                      "event moves the second place's resource after the first setting holds: keep it, find the mug",
            factor="where the event takes the resource",
            cases={"cabinet6": dict(failures=[f_move("resource", MUG, P("kitchen_cabinet_6/top", 3.68, 0.36),
                                                     ("place", {"object": CUP}), fid="resource_mug")],
                                    route=two(("region", "living_room_0_0"))),
                   "cabinet4": dict(failures=[f_move("resource", MUG, P("kitchen_cabinet_4/top", 1.4, 0.42),
                                                     ("place", {"object": CUP}), fid="resource_mug")], route=two())}),
    }


def T14(t):
    B = "book_red"
    base = OR(t, "e1_book_ready")                 # nav desk, look, nav book, pick, nav bookcase, place
    i = at(base, "pick", object=B)
    carry, place_ = base[i + 1], base[i + 2]
    two = (base[:i + 1] + [FAIL(carry, True)] + recs(nav(B), look(B), pick(B)) + [FAIL(carry, True)]
           + recs(nav(B), look(B), S("expose", object=B), pick(B, hands="both"), carry) + [place_])
    slip_once = base[:i + 1] + [FAIL(carry, True)] + recs(nav(B), look(B), pick(B), carry) + [place_]
    shelf = {"kitchen_cabinet_4": {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 90.0},
             "kitchen_cabinet_6": {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.5, 0.36], "yaw_deg": 90.0}}
    take = lambda art: [nav(B), S("expose", object=B), pick(B), S("retreat", obstacle=art, distance_m=0.3),  # noqa: E731
                        S("close", articulated=art)]
    book_goal = copy.deepcopy(t["goal"])
    book_goal["all"] += [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]
    shelve = [nav("bookcase_2/top"), place(B, "bookcase_2/top")]
    return {
        "x6_gd_book_put_away": dict(
            conditions=["item_put_away"], base="e1_book_ready", control="book_on_desk", goal=book_goal,
            remove=["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"],
            instruction="The kid put the red book away in one of the low kitchen cabinets instead of the bookcase. Put it "
                        "back on the low bookcase in the bedroom, and close the cabinets again.",
            factor="which closed place holds the item",
            challenge="the red book is in one of the two low kitchen cabinets (seed decides which)",
            rationale="the location is a disjunction over closed places: inspect them (reference route: the worse "
                      "order), take the book out, close both doors",
            cases={f"in_{w[-1]}": dict(move={B: shelf[w]}, route=put_away([], o, w, take, shelve),
                                       failures=[f_initial("resource", [["on", B, f"{w}/inside_shelf"]], fid="resource_book_put_away")])
                   for w, o in (("kitchen_cabinet_4", "kitchen_cabinet_6"), ("kitchen_cabinet_6", "kitchen_cabinet_4"))}),
        "x6_sr_two_hand_carry": dict(
            base="e1_book_ready", control="x6_m_slip_book",
            challenge="the red book slips out of the one-handed pinch at the start of every carry; the first shelving "
                      "place is refused from its park",
            rationale="one-handed retries never work (persistent): carry it with both hands instead",
            cases={"": dict(failures=[f_slip_persist(B, one_handed=True), f_ik("place", B)],
                            route=with_ik(two, "place", B))}),
        "x6_m_slip_book": dict(
            base="e1_book_ready", control="e1_book_ready",
            challenge="the red book slips once at the start of the carry",
            rationale="matched control of x6_sr_two_hand_carry: transient, picking it again works",
            cases={"": dict(failures=[f_slip(B)], route=slip_once)}),
    }


def T17(t):
    B, POT, LID, F = "wooden_block_b", "handled_cooking_pot", "pot_lid", "floor_block"
    base = OR(t, "lid_off")                     # nav stove, look stove, nav island, look island, hide
    hide = base[-1]
    primitive = recs(nav(B), pick(B), nav(POT), S("drop", object=B, container=POT), nav(LID), pick(LID), nav(POT),
                     S("cover", container=POT, lid=LID))
    refused = base[:-1] + refused_twice(hide, POT) + with_grasp(primitive, B)
    lifted = lambda *sr: base + recs(look("kitchen_stove/top"), S("search", object=LID, **dict(sr)), nav(LID), pick(LID),  # noqa: E731
                                     nav(POT), S("cover", container=POT, lid=LID))
    both_goal = {"all": [["hidden", B], ["hidden", F], ["covered", POT, LID], ["hand_empty", "right"]]}
    both = lambda region: base + recs(S("search", object=F, region=region), nav(POT), S("uncover", container=POT),  # noqa: E731
                                      nav(F), look(F), S("hide", object=F, receptacle=POT, lid=LID))
    return {
        "x6_sr_hide_refused": dict(
            base="lid_off", control="x6_m_ik_hide",
            challenge="the hide skill is refused from every park; the first block pick slips",
            rationale="the composite procedure is unavailable (persistent): realise it with primitives (pick the "
                      "block, drop it into the pot, pick the lid, cover)",
            cases={"": dict(failures=[f_ik_persist("hide", B), f_grasp(B)], route=refused)}),
        "x6_m_ik_hide": dict(
            base="lid_off", control="lid_off",
            challenge="the first hide is refused from its park",
            rationale="matched control of x6_sr_hide_refused: one re-park fixes it",
            cases={"": dict(failures=[f_ik("hide", B)], route=with_ik(base, "hide", B))}),
        "x6_pp_lid_lifted": dict(
            base="lid_off", control="lid_off",
            challenge="right after the block is hidden, someone peeks and leaves the lid on the other low cabinet",
            rationale="the block is still in the pot: find the lid and cover again, do not take the block out",
            factor="where the event takes the resource",
            cases={"cabinet4": dict(failures=[f_move("resource", LID, P("kitchen_cabinet_4/top", 1.4, 0.42),
                                                     ("hide", {"object": B}), fid="resource_lid")], route=lifted()),
                   "dining": dict(failures=[f_move("resource", LID, P("dining_table_2/top", 3.7, 6.3),
                                                   ("hide", {"object": B}), fid="resource_lid")],
                                  route=lifted(("region", "dining_room_0_1")))}),
        "x6_gd_hide_both_event": dict(
            base="lid_off", control="lid_off",
            move={F: P("kitchen_island/top", 7.25, 1.85)}, goal=both_goal, watch=[B, F, LID, POT, "oatmeal", "rolling_pin"],
            instruction="We are playing hide-and-seek with the kid's toy blocks: hide both wooden blocks in the empty "
                        "pot on the stove and put the lid on so they cannot see them.",
            challenge="two blocks to hide in one pot; once the first is hidden, the kid takes the other block to the "
                      "TV stand",
            rationale="the goal decomposes into two hides that share the lid (uncover between them); the event moves "
                      "the second block after the first subgoal holds: keep the first hidden, find the second",
            factor="where the event takes the resource",
            cases={c: dict(failures=[f_move("resource", F, to, ("hide", {"object": B}), fid="resource_floor_block")],
                           route=both(region))
                   for c, to, region in (("tv_stand", P("tv_stand_2/top", 7.0, 0.36), "living_room_0_0"),
                                         ("dining", P("dining_table_2/top", 3.7, 6.3), "dining_room_0_1"))}),
    }


def T18(t):
    C6, C4, MW = "kitchen_cabinet_6", "kitchen_cabinet_4", "kitchen_microwave"
    base = OR(t, "at_island")                   # nav cab6, open, inspect, close
    mw = [nav(MW), S("open", articulated=MW), look("kitchen_microwave/inside_floor"), S("close", articulated=MW)]
    c4 = [nav(C4), S("open", articulated=C4), S("inspect", receptacle=C4), S("close", articulated=C4)]
    goal_mw = {"all": [["observed", "plate_inside_kitchen_cabinet"], ["observed", "bowl_inside_kitchen_cabinet"],
                       ["is_closed", C6], ["is_closed", MW], ["hand_empty", "right"]]}
    goal_3 = copy.deepcopy(goal_mw)
    goal_3["all"].append(["is_closed", C4])
    in_mw = {"support": "kitchen_microwave/inside_floor", "xy": [4.5, 2.5], "yaw_deg": 0.0}
    return {
        "x6_gd_bowl_elsewhere": dict(
            conditions=["item_put_away"], base="at_island", control="at_island",
            move={"bowl_inside_kitchen_cabinet": in_mw},
            factor="how many candidate places (and an empty one) the instruction names",
            challenge="the plate is in the wall cabinet, the bowl was left in the microwave; in the second case the "
                      "instruction also names the other low cabinet, which is empty",
            rationale="the first place answers only half of the question: the inspection continues, past an empty "
                      "place when there is one, until both dishes are seen",
            cases={"two_places": dict(goal=goal_mw, route=base + mw,
                                      instruction="Grandma wants to know whether there is still a clean plate and bowl "
                                                  "for dinner, in the low wall cabinet or the microwave. Have a look "
                                                  "and close every door properly afterwards."),
                   "three_places": dict(goal=goal_3, route=base + c4 + mw,
                                        instruction="Grandma wants to know whether there is still a clean plate and bowl "
                                                    "for dinner somewhere in the low kitchen cabinets or the microwave. "
                                                    "Have a look and close every door properly afterwards.")},
            failures=[f_initial("resource", [["on", "bowl_inside_kitchen_cabinet", "kitchen_microwave/inside_floor"]],
                                fid="resource_bowl_elsewhere")]),
        "x6_pp_door_reopened": dict(
            base="at_island", control="at_island",
            challenge="right after the robot closes the cabinet, someone opens the door again",
            rationale="both dishes were already seen: close the door again, do not inspect again",
            cases={"": dict(failures=[f_joint("dependency", C6, "open", ("close", {"articulated": C6}))],
                            route=base + recs(S("close", articulated=C6)))}),
    }


def T19(t):
    CAN, CUBE, BIN = "soda_can", "foam_cube", "wide_storage_bin"
    base = OR(t, "bin_on_bookcase")             # ... approach bin, drop can, nav cube, pick cube, nav bin, drop cube
    j = at(base, "drop", object=CUBE)
    refused = with_grasp(base[:j], CUBE) + refused_twice(base[j], BIN) + recs(place(CUBE, BIN))
    shelf = {"kitchen_cabinet_4": {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 0.0},
             "kitchen_cabinet_6": {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.63, 0.36], "yaw_deg": 0.0}}
    take = lambda art: [nav(CAN), pick(CAN), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]  # noqa: E731
    i_can = at(base, "pick", object=CAN)
    rest = base[i_can + 1:]
    can_goal = copy.deepcopy(t["goal"])
    can_goal["all"] += [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]
    return {
        "x6_gd_can_put_away": dict(
            conditions=["item_put_away"], base="bin_on_bookcase", control="m_can_in_dining_room", goal=can_goal,
            remove=["plate_inside_kitchen_cabinet"],
            instruction="Movie night is over. Someone put the empty soda can away in one of the low kitchen cabinets, and "
                        "the foam packing cube from the delivery lies on the living-room floor; take both to the wide "
                        "storage bin we use for recycling, on the low bookcase in the bedroom. Close the cabinets again.",
            factor="which closed place holds the item",
            challenge="the can is in one of the two low kitchen cabinets (seed decides which); the cube on the floor",
            rationale="inspect the closed places for the can (reference route: the worse order), then recycle both",
            cases={f"in_{w[-1]}": dict(move={CAN: shelf[w]}, route=put_away([], o, w, take, rest),
                                       failures=[f_initial("resource", [["on", CAN, f"{w}/inside_shelf"]], fid="resource_can_put_away")])
                   for w, o in (("kitchen_cabinet_4", "kitchen_cabinet_6"), ("kitchen_cabinet_6", "kitchen_cabinet_4"))}),
        "x6_sr_cube_drop_refused": dict(
            base="bin_on_bookcase", control="x6_m_ik_drop_cube",
            challenge="once the can is in the bin, the cube slips on its first pick, then dropping it over the bin is "
                      "refused from every park (the light foam would not fall in)",
            rationale="the drop procedure is unavailable for the cube (persistent): place it into the bin instead, and "
                      "keep the can where it is",
            cases={"": dict(failures=[f_grasp(CUBE), f_ik_where("drop", "ik_drop_cube_persistent", object=CUBE, container=BIN)],
                            route=refused)}),
        "x6_m_ik_drop_cube": dict(
            base="bin_on_bookcase", control="bin_on_bookcase",
            challenge="the first drop of the cube over the bin is refused from its park",
            rationale="matched control of x6_sr_cube_drop_refused: one re-park fixes it",
            cases={"": dict(failures=[f_ik("drop", CUBE)], route=with_ik(base, "drop", CUBE))}),
    }


def T20(t):
    J, M = "juice_bottle", "mug_counter"
    base = OR(t, "bottle_on_cabinet")           # nav cab6 top, look, nav bottle, pick, nav dining, place
    i = at(base, "pick", object=J)

    def behind(blocker, aside):
        return base[:i] + refused_twice(base[i]) + recs(nav(blocker), pick(blocker), *aside, nav(J), look(J)) \
            + [REC(base[i])] + base[i + 1:]
    on_cab6 = [place(M, "kitchen_cabinet_6/top", [3.33, 0.4])]
    # the bowl needs more room than the cabinet top has left: the other low cabinet
    on_cab4 = [nav("kitchen_cabinet_4/top"), S("place", object="bowl_kitchen_cabinet", receptacle="kitchen_cabinet_4/top")]
    BW = "bowl_kitchen_cabinet"
    instr = ("Someone put the juice bottle away in one of the low kitchen cabinets. Put it back on the dining table, "
             "standing up, and close the cabinets again.")
    goal = copy.deepcopy(t["goal"])
    goal["all"] += [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]
    tail = base[i + 1:]
    take = lambda art: [nav(J), pick(J), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]  # noqa: E731
    return {
        "x6_cl_bottle_behind_mug": dict(
            base="bottle_on_cabinet", control="m_ik_pick",
            factor="which object blocks the reach (blocking relation)",
            challenge="the bottle stands in the back corner of the cabinet top with a mug (or a bowl) right in front "
                      "of it: no park reaches the bottle until that object is moved",
            rationale="re-parking cannot help while the object blocks the reach (wall behind, object in front), so the "
                      "recovery inserts a subgoal on an object outside the goal: move it aside first",
            cases={"mug": dict(move={J: P("kitchen_cabinet_6/top", 3.7, 0.265), M: P("kitchen_cabinet_6/top", 3.7, 0.39)},
                               failures=[f_initial("dependency", [["on", M, "kitchen_cabinet_6/top"]], fid="dependency_in_front"),
                                         {**f_ik_persist("pick", J), "until_moved": M}], route=behind(M, on_cab6)),
                   "bowl": dict(move={J: P("kitchen_cabinet_6/top", 3.68, 0.26), BW: P("kitchen_cabinet_6/top", 3.68, 0.408)},
                                remove=["spoon_kitchen_cabinet"],
                                failures=[f_initial("dependency", [["on", BW, "kitchen_cabinet_6/top"]], fid="dependency_in_front"),
                                          {**f_ik_persist("pick", J), "until_moved": BW}], route=behind(BW, on_cab4))}),
        "x6_gd_bottle_put_away": dict(
            conditions=["item_put_away"], base="bottle_on_cabinet", control="bottle_on_cabinet", instruction=instr, goal=goal,
            factor="which closed place holds the item",
            remove=["plate_inside_kitchen_cabinet"],
            challenge="the bottle was put away in one of the two low cabinets",
            rationale="a disjunction over closed places: inspect them (reference route: the worse order), take the "
                      "bottle, close both doors",
            cases={"in_cabinet_4": dict(move={J: {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 0.0}},
                                        failures=[f_initial("resource", [["on", J, "kitchen_cabinet_4/inside_shelf"]],
                                                            fid="resource_bottle_put_away")],
                                        route=open_explore("kitchen_cabinet_6") + [S("close", articulated="kitchen_cabinet_6")]
                                        + open_explore("kitchen_cabinet_4") + take("kitchen_cabinet_4") + tail),
                   "in_cabinet_6": dict(move={J: {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.63, 0.36], "yaw_deg": 0.0}},
                                        failures=[f_initial("resource", [["on", J, "kitchen_cabinet_6/inside_shelf"]],
                                                            fid="resource_bottle_put_away")],
                                        route=open_explore("kitchen_cabinet_4") + [S("close", articulated="kitchen_cabinet_4")]
                                        + open_explore("kitchen_cabinet_6") + take("kitchen_cabinet_6") + tail)}),
    }


def T11(t):
    X, BASKET = "apple", "fruit_basket"
    base = OR(t, "fruits_on_table")             # nav dining, look, nav apple, pick, nav bookcase, look, place basket
    i = at(base, "place", object=X)
    roll = {"id": "placement_apple_basket_persistent", "kind": "placement", "mode": "displaced", "persist": True,
            "to": P("bookcase_2/top", 1.21, -0.29), "report": [["inside", X, BASKET]],
            "trigger": {"skill": "place", "args": {"object": X, "receptacle": BASKET}, "nth": 1}}
    once = dict(roll, id="placement_apple_basket", persist=False)
    tray = recs(nav("desk_1/top"), look("desk_1/top"), nav("serving_tray"), place(X, "serving_tray"))
    # re-park at the apple that rolled out (from the bookcase park the basket hides it)
    again = [FAIL(base[i], True)] + recs(S("approach", target=X), pick(X))
    O = "orange_2"
    fruit_goal = {"all": [["hand_empty", "right"]],
                  "any": [[["inside", X, a], ["inside", O, b]] for a in (BASKET, "serving_tray") for b in (BASKET, "serving_tray")]}
    two = RT(t, "alternative_tray")
    k = next(i for i, st in enumerate(two) if st.get("expect") == "fail")
    two = [st for st in two[:k]] + recs(nav("desk_1/top"), look("desk_1/top"), nav("serving_tray"), place(X, "serving_tray"),
                                        S("search", object=O, region="living_room_0_0"), nav(O), pick(O),
                                        nav("serving_tray"), place(O, "serving_tray"))
    return {
        "x6_gd_fruits_event": dict(
            base="basket_missing", control="basket_missing",
            add={O: {"asset": "orange", "support": "dining_table_2/top", "xy": [3.63, 5.66], "yaw_deg": 0.0}},
            goal=fruit_goal, watch=[X, O, "serving_tray"],
            instruction="Lunch is over and the apple and the orange are still on the dining table. Put them into the "
                        "fruit basket on the low bookcase in the bedroom; if the basket is not there, the serving tray "
                        "on the study desk will do.",
            challenge="two fruits, no basket (the stated tray instead); once the apple is on the tray, the kid takes "
                      "the orange to the TV stand",
            rationale="the goal decomposes into one placement per fruit; the event moves the second resource after the "
                      "first subgoal holds: keep the apple, find the orange",
            cases={"": dict(failures=[f_move("resource", O, P("tv_stand_2/top", 7.2, 0.36), ("place", {"object": X}),
                                             fid="resource_orange")], route=two)}),
        "x6_cl_apple_rolls_out": dict(
            base="fruits_on_table", control="x6_m_apple_rolls_out_once",
            challenge="the apple rolls back out of the basket onto the bookcase every time it is put in; the apple "
                      "slips on its first pick",
            rationale="the basket does not keep the apple (persistent placement failure, pinned to the basket): the "
                      "instruction's tray on the study desk replaces it",
            cases={"": dict(failures=[f_grasp(X), roll],
                            route=with_grasp(base[:i], X) + again + again + tray)}),
        "x6_m_apple_rolls_out_once": dict(
            base="fruits_on_table", control="fruits_on_table",
            challenge="the apple rolls back out of the basket once",
            rationale="matched control of x6_cl_apple_rolls_out: transient, putting it in again works",
            cases={"": dict(failures=[once], route=base[:i] + again + [REC(base[i])])}),
    }


FAMILIES = {"T01_book_to_dining_table": T01, "T02_stack_blocks": T02, "T04_cup_or_mug_to_cabinet": T04,
            "T05_pen_or_pencil_to_desk": T05, "T06_block_destination_occupied": T06, "T07_heat_oatmeal": T07,
            "T08_wipe_island": T08, "T09_tomato_soup": T09, "T10_trash_the_can": T10, "T11_collect_fruits": T11, "T12_tidy_toys": T12,
            "T13_breakfast_setup": T13, "T14_shelve_the_book": T14, "T17_hide_and_seek_block": T17,
            "T18_check_cabinet_dishes": T18, "T19_recycling": T19, "T20_juice_back_to_table": T20}
NEW_CONDITIONS = {
    "item_put_away": {"type": "location_disjunction", "decision": "decompose",
                      "meaning": "the item is in one of several closed places the instruction names"},
    "multi_object_goal": {"type": "goal_structure", "decision": "decompose",
                          "meaning": "the goal has several ordered or allocated subgoals"},
}


# ----------------------------------------------------------------- seed extensions of v5 families
# A v5 family whose plan must find a resource (moved there by a dynamic event, or out of view in the overlay) gets a
# second case with the resource in another known-valid place: the search and the route change, the v5 variant itself
# stays a case with its configuration and hash untouched.  SEED_EXT holds the place chosen per family (the first
# candidate that passes every static check, found by ``python benchmark/v6/define_tasks_v6.py --select-ext``).
EXT_PLACES = [("dining_table_2/top", [3.7, 6.3], "dining_room_0_1"), ("tv_stand_2/top", [7.0, 0.36], "living_room_0_0"),
              ("kitchen_cabinet_4/top", [1.4, 0.42], None), ("kitchen_cabinet_6/top", [3.7, 0.36], "living_room_0_0")]
SEED_EXT = {
    ('T03_utensils_one_container', 'h_dynamic_pin_taken'): 0,
    ('T04_cup_or_mug_to_cabinet', 'no_cup_mug_away'): 0,
    ('T05_pen_or_pencil_to_desk', 'h_dynamic_pencil_taken'): 1,
    ('T06_block_destination_occupied', 'occupied_block_away'): 1,
    ('T07_heat_oatmeal', 'broken_oatmeal_away'): 0,
    ('T08_wipe_island', 'far_sponge_tv'): 0,
    ('T08_wipe_island', 'h_dynamic_sponge_taken'): 0,
    ('T09_tomato_soup', 'h_dynamic_spoon_taken'): 0,
    ('T09_tomato_soup', 'lid_on_spoon_away'): 0,
    ('T10_trash_the_can', 'can_in_dining_room'): 1,
    ('T10_trash_the_can', 'far_can_far'): 0,
    ('T10_trash_the_can', 'h_dynamic_can_moved'): 1,
    ('T12_tidy_toys', 'duck_in_study'): 0,
    ('T12_tidy_toys', 'h_action_grasp_and_ik'): 0,
    ('T12_tidy_toys', 'h_dynamic_duck_taken'): 1,
    ('T12_tidy_toys', 'h_mixed_everywhere_ik'): 0,
    ('T12_tidy_toys', 'toys_everywhere'): 0,
    ('T13_breakfast_setup', 'bowl_on_cabinet'): 0,
    ('T13_breakfast_setup', 'h_dynamic_mug_taken'): 0,
    ('T13_breakfast_setup', 'no_cup_bowl_on_cabinet'): 0,
    ('T19_recycling', 'h_action_grasp_and_miss'): 1,
    ('T19_recycling', 'h_dynamic_cube_moved'): 3,
    ('T19_recycling', 'h_mixed_lookalike_ik'): 1,
    ('T19_recycling', 'lookalike_bin'): 1,
    ('T19_recycling', 'm_can_in_dining_room'): 1,
    ('T20_juice_back_to_table', 'h_dynamic_bottle_taken'): 2,
    ('T20_juice_back_to_table', 'm_bottle_on_tv_stand'): 0,
}


def ext_target(t, fam):
    """(mode, object, its place in the v5 variant, trigger skill args or None) when the family qualifies."""
    v = t["variants"][fam]
    steps = t["routes"][t["oracle"][fam]]["steps"]
    looked = {s["args"].get("object") for s in steps if s["skill"] == "search"} | \
        {s["args"].get("destination") for s in steps if s["skill"] == "navigate"}
    for f in v.get("failures", []):
        ev = f.get("event") or {}
        if ev.get("type") == "move_object" and (ev["object"] in looked and
                                                any(s["skill"] == "search" and s["args"].get("object") == ev["object"]
                                                    for s in steps) or ev["to"].get("support") in looked):
            return "event", ev["object"], ev["to"].get("support"), f["id"]
    for s in steps:
        if s["skill"] == "search":
            x = s["args"].get("object")
            m = (v.get("move") or {}).get(x)
            if m and m.get("support"):
                return "overlay", x, m["support"], None
    return None


def ext_variant(t, fam, k):
    mode, x, old, fid = ext_target(t, fam)
    sup, xy, region = EXT_PLACES[k]
    v = copy.deepcopy(t["variants"][fam])
    meta = v.pop("v5", {}) or {}
    if mode == "event":
        for f in v["failures"]:
            if f["id"] == fid:
                f["event"]["to"] = {"support": sup, "xy": list(xy), "yaw_deg": 0.0}
    else:
        v["move"][x] = {"support": sup, "xy": list(xy), "yaw_deg": 0.0}
    steps = copy.deepcopy(t["routes"][t["oracle"][fam]]["steps"])
    for st in steps:
        if st["skill"] == "search" and st["args"].get("object") == x:
            if region:
                st["args"]["region"] = region
            else:
                st["args"].pop("region", None)
        for key in ("destination", "target"):
            if st["args"].get(key) == old:
                st["args"][key] = sup
    case = "alt_" + sup.split("/")[0]
    v["since"] = "v6"
    v["note"] = f"{meta.get('challenge') or v.get('note', '')} (here the {x} is on {sup})"
    v["v6"] = {"family": fam, "case": case, "tier": meta.get("tier"), "hard_category": meta.get("hard_category"),
               "challenge": v["note"], "derived_from": fam, "seed_extension": True,
               "rationale": f"seed extension of the v5 design: the {x} ends up somewhere else, so where to search and the "
                            "route change; everything else is the v5 variant"}
    return f"{fam}__{case}", v, steps


# ----------------------------------------------------------------- assembly
def seed_cases(task_id, fam, cases):
    """Seeds 10-19 -> case ids: balanced (each case gets floor/ceil of 10 / k seeds), shuffled per family with a
    fixed RNG, so every seed is reproducible and every case is exercised."""
    slots = [cases[i % len(cases)] for i in range(len(SEEDS))]
    random.Random(f"{task_id}:{fam}:cases").shuffle(slots)
    return dict(zip(SEEDS, slots))


def make_variant(t, fam, spec, case, cspec):
    base = copy.deepcopy(t["variants"][spec["base"]])
    v = {k: base[k] for k in OVERLAY if k in base and k != "vary"}
    for src in (spec, cspec):
        if "move" in src:
            v["move"] = {**v.get("move", {}), **copy.deepcopy(src["move"])}
        if "remove" in src:
            v["remove"] = sorted(set(v.get("remove", [])) | set(src["remove"]))
        if "add" in src:
            v["add"] = {**v.get("add", {}), **copy.deepcopy(src["add"])}
        for k in FIELDS:
            if k in src and k not in ("move", "remove", "add", "failures"):
                v[k] = copy.deepcopy(src[k])
    placed = set(spec.get("move", {})) | set(cspec.get("move", {})) | set(spec.get("add", {})) | set(cspec.get("add", {}))
    if v.get("remove") and placed & set(v["remove"]):
        v["remove"] = sorted(set(v["remove"]) - placed)      # an object the base removes but this variant places
    for k in ("goal", "instruction", "instruction_zh", "watch", "handle_objects"):
        if k in base and k not in v:
            v[k] = copy.deepcopy(base[k])
    if "instruction" in spec or "instruction" in cspec:
        v.pop("instruction_zh", None)            # the Chinese text of the base no longer matches
    fails = copy.deepcopy(spec.get("failures", [])) + copy.deepcopy(cspec.get("failures", []))
    if fails:
        v["failures"] = fails
    v["since"] = "v6"
    v["note"] = spec["challenge"]
    v["v6"] = {"family": fam, "case": case or None, "challenge": spec["challenge"], "rationale": spec["rationale"], "control": spec["control"],
               "contrast": spec.get("contrast"), "factor": spec.get("factor"),
               "derived_from": spec["base"]}
    v["move"], v["vary"] = seed_vary(t, v)
    return v


# Families whose cases differ in the design (which object blocks, which failure, which subgoal the event undoes,
# how many places are named), not only in where things are: each case is a variant of its own.  The other
# multi-case families keep one variant whose seeds choose among layouts (where the resource / substitute /
# item is, where an event takes it, which bin is full).
SPLIT = {("T01_book_to_dining_table", "x6_dr_block_on_book"), ("T02_stack_blocks", "x6_cl_block_b_unholdable"),
         ("T04_cup_or_mug_to_cabinet", "x6_cl_cup_unusable"), ("T04_cup_or_mug_to_cabinet", "x6_dr_spot_filled_dynamic"),
         ("T09_tomato_soup", "x6_cl_spoon_unholdable"), ("T09_tomato_soup", "x6_pp_tomato_taken_out"),
         ("T13_breakfast_setup", "x6_pp_spoon_moved"), ("T18_check_cabinet_dishes", "x6_gd_bowl_elsewhere"),
         ("T20_juice_back_to_table", "x6_cl_bottle_behind_mug")}


def build_task(t: dict) -> dict:
    t = copy.deepcopy(t)
    fams = FAMILIES[t["task_id"]](t) if t["task_id"] in FAMILIES else {}
    families = {}
    # every v5 formal variant is a one-case family of its own; its control is the task's first nominal variant
    easy = t["v5_formal"].get("easy") or []
    for ids in t["v5_formal"].values():
        for vid in ids:
            families[vid] = {"origin": "v5", "control": easy[0] if easy and easy[0] != vid else None, "layouts": [vid],
                             "seeds": {s: vid for s in SEEDS}}
            k = SEED_EXT.get((t["task_id"], vid))
            if k is not None:
                alt, v, steps = ext_variant(t, vid, k)
                t["variants"][alt] = v
                t["routes"][f"v6_{alt}"] = {"steps": steps, "kind": "v6_seed_extension", "variant": alt}
                t["oracle"][alt] = f"v6_{alt}"
                fam = families[vid]
                fam["layouts"] = [vid, alt]
                fam["seeds"] = seed_cases(t["task_id"], vid, fam["layouts"])
                fam["factor"] = "where the resource is to be found (seed extension)"
    for fam, spec in fams.items():
        if fam in t["variants"]:
            raise ValueError(f"{t['task_id']}: {fam} exists in v5")
        names = []
        for case, cspec in spec["cases"].items():
            vid = f"{fam}__{case}" if case else fam
            v = make_variant(t, fam, spec, case, cspec)
            rname = f"v6_{vid}"
            t["routes"][rname] = {"steps": _refresh_view(cspec["route"]), "kind": "v6_oracle", "variant": vid}
            t["oracle"][vid] = rname
            t["variants"][vid] = v
            names.append(vid)
        if (t["task_id"], fam) in SPLIT:
            for vid in names:                    # different designs: one variant each, every seed on it
                families[vid] = {"origin": "v6", "control": spec["control"], "layouts": [vid],
                                 "seeds": {s: vid for s in SEEDS}}
            continue
        families[fam] = {"origin": "v6", "control": spec["control"], "layouts": names, "factor": spec.get("factor"),
                         "seeds": seed_cases(t["task_id"], fam, names)}
    t["v6_variants"] = families
    for k in ("v5_formal", "v5_study", "v5_supplementary"):       # v5's tier lists; v6 lists families instead
        t.pop(k, None)
    t["benchmark_version"] = "v6"
    return t


def build() -> dict:
    doc = json.loads(V5.read_text())
    tasks = [build_task(t) for t in doc["tasks"]]
    reg = dict(doc["condition_registry"], **NEW_CONDITIONS)
    out = {"schema_version": 6, "benchmark_version": "v6", "kind": "zenobench_benchmark_tasks",
           "note": "Source: python benchmark/v6/define_tasks_v6.py (reads benchmark/v5/tasks.json); tracks: "
                   "benchmark/v6/tracks.py.",
           "eval_seeds": SEEDS, "condition_registry": reg, "tasks": tasks}
    from benchmark.v6.tracks import apply_tracks
    apply_tracks(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit("benchmark/v6/tasks.json is out of date: python benchmark/v6/define_tasks_v6.py")
        print("up to date")
        return
    OUT.write_text(text)
    n_fam = sum(len(t["v6_variants"]) for t in doc["tasks"])
    n_new = sum(1 for t in doc["tasks"] for f in t["v6_variants"].values() if f["origin"] == "v6")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['tasks'])} tasks, {n_fam} variants ({n_new} new)")


if __name__ == "__main__":
    main()
