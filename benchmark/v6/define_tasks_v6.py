"""ZenoBench v6 task design: the v5 suite plus new task-level variant families (reads v5, never writes it).

    python benchmark/v6/define_tasks_v6.py            # writes benchmark/v6/tasks.json
    python benchmark/v6/define_tasks_v6.py --check    # fails if tasks.json is not up to date

v5 (benchmark/v5/tasks.json) is copied as it is: every v5 variant keeps its configuration, so every v5 episode
hash stays valid (tests/test_v6_catalog.py checks it).  v6 adds **families** of new variants.  A family is one
design (one challenge, one capability hypothesis); its **cases** are decision instances: each case changes a
decision-relevant fact (which substitute exists and where, which container holds the item, which object the
event takes away) and therefore its oracle route.  Seeds 10-19 are assigned to the cases of a family
deterministically and balanced (``v6_families[fam]["seeds"]``); a case is a concrete variant
``<family>__<case>`` with its own configuration and route.  A family with one case is a plain variant.

Every new family states, besides its overlay / failures / route:

* ``challenge``  - what the planner meets; ``rationale`` - why a plan has to change and why it stays solvable;
* ``control``    - the existing variant it differs from in one factor (isolation pairs for the analysis);
* ``hyp``        - capability hypotheses in a structured form that ``hypotheses.py`` checks independently
                   (cause -> nominal plan blocked -> oracle consistent), never derived from the route alone.

Tiers (one definition for v5 and v6 variants, applied by ``hypotheses.py``):

* **Easy**   - the nominal plan works: no failure, no task-level constraint (only the start pose may differ);
* **Medium** - one local adaptation keeps the plan's structure: a transient action failure (retry, re-park),
               a search, or a substitute the instruction names; no core capability is required;
* **Hard**   - the plan must change at the task level: at least one verified core capability (DR dependency
               replanning, GD goal decomposition, SR strategy replacement, CL cross-level recovery, PP
               partial-progress preservation), and not solvable by retrying the nominal plan.

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
def H(cap, **kw):
    """A capability hypothesis (checked by hypotheses.py)."""
    return {"cap": cap, **kw}


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


# ----------------------------------------------------------------- per-task families
def T01(t):
    B = "paperback_book"
    base = OR(t, "overhang_ready")                      # look, nav, approach, look, pick, nav table, place
    i = at(base, "pick", object=B)
    carry, place_ = base[i + 1], base[i + 2]
    two_hand = (base[:i + 1] + [FAIL(carry, True)] + recs(S("approach", target=B), look(B), pick(B))
                + [FAIL(carry, True)] + recs(S("approach", target=B), look(B), pick(B, hands="both"), carry)
                + [place_])
    blocked = {"wooden_block_a": {"support": None, "z": 0.886, "xy": [7.62, 1.59], "yaw_deg": 0.0}}
    return {
        "x6_sr_two_hand_carry": dict(
            tier="hard", hard="action", base="overhang_ready", control="x6_m_slip_book",
            challenge="the paperback slips out of the one-handed pinch at the start of every carry; the first place "
                      "on the table is also refused from its park",
            rationale="a one-handed retry fails every time (persistent slip), so the carry procedure must change: "
                      "pick the book with both hands (the left hand steadies it); solvable because pick(hands=both) "
                      "is a library skill and the slip only affects one-handed carries",
            cases={"": dict(failures=[f_slip_persist(B, one_handed=True), f_ik("place", B)],
                            route=with_ik(two_hand, "place", B))},
            hyp=[H("SR", nominal={"skill": "pick", "args": {"object": B, "hands": "right"}},
                   replacement={"skill": "pick", "args": {"object": B, "hands": "both"}},
                   cause="failure:slip_paperback_book_persistent"),
                 H("CL", failure="slip_paperback_book_persistent", change="procedure", to="pick:hands=both")]),
        "x6_m_slip_book": dict(
            tier="medium", base="overhang_ready", control="overhang_ready",
            challenge="the paperback slips once at the start of the carry",
            rationale="matched control of x6_sr_two_hand_carry: the same slip, transient, so picking it again works",
            cases={"": dict(failures=[f_slip(B)], route=with_slip(base, B))},
            hyp=[H("AF", level="local")]),
        "x6_dr_block_on_book": dict(
            tier="hard", hard="task", base="overhang_ready", control="overhang_ready", move=blocked,
            challenge="a toy block lies on top of the paperback",
            rationale="the book cannot be lifted with the block on it: take the block off (and leave it on the "
                      "island) first; the block is not part of the goal, so this is an inserted precondition",
            cases={"": dict(failures=[f_initial("dependency", [["on_top_of", "wooden_block_a", B]])],
                            route=[look("kitchen_island/top")] + recs(
                                nav("wooden_block_a"), pick("wooden_block_a"),
                                place("wooden_block_a", "kitchen_island/top", [7.2, 1.85])) + base[1:])},
            hyp=[H("DR", blocker="wooden_block_a", blocked={"skill": "pick", "target": B},
                   cause="failure:dependency_initial")]),
    }


def T02(t):
    A, B, F = "wooden_block_a", "wooden_block_b", "floor_block"
    base = OR(t, "clear")                               # look, nav B, pick B, rotate B, nav A, stack B on A
    swap_tail = recs(nav(A), pick(A), S("rotate", object=A, degrees=30), nav(B), S("approach", target=B),
                     S("stack", object=A, base=B))
    cases = {}
    for case, fail, rep in (("grasp", f_grasp_persist(B), None), ("ik", f_ik_persist("pick", B), B)):
        r = base[:2] + refused_twice(base[2], rep) + swap_tail
        cases[case] = dict(failures=[fail, f_ik("stack", A)], route=with_ik(r, "stack", A),
                           hyp=[H("CL", failure=fail["id"], change="object", to=A),
                                H("SR", nominal={"skill": "stack", "args": {"object": B, "base": A}},
                                  replacement={"skill": "stack", "args": {"object": A, "base": B}},
                                  cause=f"failure:{fail['id']}")])
    # three-block tower: block A at the edge (edge_base), block B in the open, the floor block put on the island
    order = [(A, B), (F, A)]
    tower_goal = {"any": [[["on_top_of", m, b], ["on_top_of", top, m], ["away_from_edge", b, 0.05],
                           ["on", b, "kitchen_island/top"]]
                          for b in (B, F) for m in (A, B, F) for top in (A, B, F) if len({b, m, top}) == 3],
                  "all": [["hand_empty", "right"]]}
    tower = [look("kitchen_island/top")] + recs(nav(A), pick(A), nav(B), S("approach", target=B),
                                                S("stack", object=A, base=B)) \
        + recs(S("search", object=F, region="living_room_0_0"), nav(F), pick(F), nav(B), S("approach", target=B),
               S("stack", object=F, base=A))
    return {
        "x6_cl_block_b_unholdable": dict(
            tier="hard", hard="action", base="clear", control="m_grasp_b",
            factor="failure mechanism (grasp slip vs reach)",
            challenge="block B cannot be picked at all (it slips every time / no park reaches it); the first stack "
                      "of the other block is refused from its park",
            rationale="the goal allows either block on top: when B cannot be held, swap the roles and stack A on B; "
                      "retrying B never works (persistent)",
            cases=cases),
        "x6_gd_tower_with_event": dict(
            tier="hard", hard="dynamic", base="edge_base", control="edge_base",
            move={F: P("kitchen_island/top", 6.95, 1.85)},
            instruction="Tidy the toy blocks on the kitchen island: stack all three wooden blocks steadily into one "
                        "tower on the island.",
            goal=tower_goal, watch=[A, B, F],
            challenge="three blocks, one at the island edge (it must not be the base); once the first two are "
                      "stacked, the kid takes the third block to the TV stand",
            rationale="the tower decomposes into two ordered stack subgoals with a base constraint (the edge block "
                      "goes on top of the middle, never at the bottom); the event removes a resource after the first "
                      "subgoal: keep the two-block stack and fetch the third",
            cases={"": dict(failures=[f_move("resource", F, P("tv_stand_2/top", 7.0, 0.36),
                                             ("stack", {"object": A, "base": B}), fid="resource_floor_block")],
                            route=tower)},
            hyp=[H("GD", kind="decomposition", subgoals=[["on_top_of", a, b] for a, b in order], cause="goal"),
                 H("PP", kept={"atom": ["on_top_of", A, B], "by": {"skill": "stack", "args": {"object": A}}},
                   event="resource_floor_block"),
                 H("AF", level="task")]),
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
    make_room = base[:4] + recs(look("kitchen_cabinet_6/top"), nav("kitchen_cabinet_4/top"),
                                place(C, "kitchen_cabinet_4/top", [1.2, 0.42]), nav("oatmeal"), pick("oatmeal"),
                                nav("kitchen_cabinet_4/top"), place("oatmeal", "kitchen_cabinet_4/top", [1.55, 0.42]),
                                nav(C), pick(C), nav("kitchen_cabinet_6/top"), place(C, "kitchen_cabinet_6/top"))
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
            tier="hard", hard="task", base="no_cup", control="no_cup",
            factor="which cabinet holds the preferred item",
            instruction="A guest is coming. Set out a cup at the drinks spot on the low wall cabinet; the cups are kept "
                        "in the two low kitchen cabinets. If there is no cup, the mug on the island will do. Close the "
                        "cabinets again.",
            challenge="the mug is in plain view, but a cup is preferred and the cups are kept in closed cabinets: the "
                      "cup is in one of the two (seed decides which)",
            rationale="the visible substitute must not end the search: the cabinets are inspected until the cup is "
                      "found (reference route: the worse order, the cup is in the second cabinet)",
            goal=cab_goal, cases=cup_cases,
            hyp=[H("GD", kind="inspection", places=["kitchen_cabinet_6", "kitchen_cabinet_4"],
                   cause="failure:resource_cup_in_cabinet")]),
        "x6_cl_cup_unusable": dict(
            tier="hard", hard="action", base="cup_available", control="m_ik_cup",
            factor="failure mechanism and where the substitute is",
            challenge="the cup cannot be used: it slips out of the hand at every carry, or no park reaches it while "
                      "the mug stands on the TV stand",
            rationale="persistent failures on the cup make retries useless; the instruction allows a mug, so the "
                      "object changes (cross-level); in the second case the mug must also be found",
            cases={"slip": dict(failures=[f_slip_persist(C), f_ik("pick", M)], route=slip_r,
                                hyp=[H("CL", failure=f"slip_{C}_persistent", change="object", to=M)]),
                   "ik_mug_away": dict(move={M: P("tv_stand_2/top", 7.75, 0.36)},
                                       failures=[f_ik_persist("pick", C), f_grasp(M)], route=ik_r,
                                       hyp=[H("CL", failure=f"ik_pick_{C}_persistent", change="object", to=M)])},
            hyp=[H("AF", level="task")]),
        "x6_dr_spot_filled_dynamic": dict(
            tier="hard", hard="dynamic", base="cup_available", control="cup_available", goal=spot_goal,
            challenge="right after the robot picks the cup, someone puts the oatmeal bowl and the pot lid on the "
                      "drinks spot",
            rationale="the destination is now full for any drink: set the cup down, move the bowl to the other low "
                      "cabinet, then set the cup; the bowl is not a goal object (only kept upright)",
            cases={"": dict(failures=filled, route=make_room)},
            hyp=[H("DR", blocker="oatmeal", blocked={"skill": "place", "target": C}, cause="failure:destination_oatmeal")]),
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
            tier="hard", hard="action", base="pen_available", control="pen_available", contrast="no_pen",
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
                                                     "place", "pencil"))},
            hyp=[H("CL", failure="grasp_pen_persistent", change="object", to="pencil"), H("AF", level="task")]),
        "x6_gd_pencil_other_cabinet": dict(
            tier="hard", hard="task", base="h_task_pencil_in_cabinet", control="h_task_pencil_in_cabinet",
            move={"pencil": in4}, goal=cab_goal, instruction=other_cab,
            challenge="the pencil is not in the low wall cabinet the instruction names but in the other low cabinet",
            rationale="the expected location is empty: the search decomposes over the candidate cabinets (inspect the "
                      "second one, open and close both); the door is a precondition of the pick",
            cases={"": dict(failures=[f_initial("resource", [["on", "pencil", "kitchen_cabinet_4/inside_shelf"]],
                                                fid="resource_pencil_elsewhere")], route=other)},
            hyp=[H("GD", kind="inspection", places=["kitchen_cabinet_6", "kitchen_cabinet_4"],
                   cause="failure:resource_pencil_elsewhere"),
                 H("DR", blocker="kitchen_cabinet_4", blocked={"skill": "pick", "target": "pencil"},
                   cause="failure:resource_pencil_elsewhere")]),
        "x6_gd_pen_or_pencil_cabinets": dict(
            tier="hard", hard="task", base="h_task_pencil_in_cabinet", control="h_task_pencil_in_cabinet",
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
                                                        fid="resource_pen_in_cabinet")])},
            hyp=[H("GD", kind="inspection", places=["kitchen_cabinet_6", "kitchen_cabinet_4"],
                   cause="failure:resource_pen_in_cabinet")]),
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
    two = base[:5] + recs(S("search", object=B, region="dining_room_0_1"), nav(B), pick(B), nav("tv_stand_2/top"),
                          place(B, "tv_stand_2/top"))
    return {
        "x6_cl_block_a_unholdable": dict(
            tier="hard", hard="action", base="free", control="x6_m_grasp_block_a",
            factor="where the substitute is",
            challenge="block A slips out of the fingers at every pick; block B (on the island or left on the dining "
                      "table) slips once at the start of its carry",
            rationale="the goal accepts either block: after A fails persistently the object changes to B (found "
                      "where it is), a transient slip of B only needs a re-pick",
            cases={"b_island": dict(failures=[f_grasp_persist(A), f_slip(B)], route=with_slip(fail_a + to_b, B)),
                   "b_dining": dict(move={B: P("dining_table_2/top", 3.7, 6.3)},
                                    failures=[f_grasp_persist(A), f_slip(B)], route=with_slip(fail_a + dining_b, B))},
            hyp=[H("CL", failure=f"grasp_{A}_persistent", change="object", to=B), H("AF", level="task")]),
        "x6_m_grasp_block_a": dict(
            tier="medium", base="free", control="free",
            challenge="block A slips from the fingers on the first pick",
            rationale="matched control of x6_cl_block_a_unholdable: transient, the second pick works",
            cases={"": dict(failures=[f_grasp(A)], route=with_grasp(base, A))}, hyp=[H("AF", level="local")]),
        "x6_cl_cabinet_unreachable": dict(
            tier="hard", hard="action", base="free", control="x6_m_ik_place_cabinet",
            challenge="block A slips on the first pick; then the cabinet top cannot be reached from any park",
            rationale="re-parking does not help (persistent refusal pinned to the cabinet): the destination changes "
                      "to the TV stand, the other display the instruction allows",
            cases={"": dict(failures=[f_grasp(A), f_ik_persist("place", A, receptacle="kitchen_cabinet_6/top")],
                            route=unreach)},
            hyp=[H("CL", failure=f"ik_place_{A}_persistent", change="destination", to="tv_stand_2/top"),
                 H("AF", level="task")]),
        "x6_m_ik_place_cabinet": dict(
            tier="medium", base="free", control="free",
            challenge="the first place on the cabinet top is refused from its park",
            rationale="matched control of x6_cl_cabinet_unreachable: one re-park fixes it",
            cases={"": dict(failures=[f_ik("place", A)], route=with_ik(base, "place", A))}, hyp=[H("AF", level="local")]),
        "x6_gd_two_displays_event": dict(
            tier="hard", hard="dynamic", base="free", control="free", goal=displays,
            instruction="Put both toy blocks on display: one on the low wall cabinet and one on the TV stand, so they "
                        "can be seen from both rooms.",
            challenge="two blocks to two displays; once the first block is on the cabinet, the kid carries the other "
                      "block to the dining table",
            rationale="the goal decomposes into one placement per display; the event moves the second resource after "
                      "the first subgoal holds: keep block A where it is, find block B",
            cases={"": dict(failures=[f_move("resource", B, P("dining_table_2/top", 3.7, 6.3),
                                             ("place", {"object": A}), fid="resource_block_b")], route=two)},
            hyp=[H("GD", kind="decomposition", subgoals=[["on", A, "kitchen_cabinet_6/top"], ["on", B, "tv_stand_2/top"]],
                   cause="goal"),
                 H("PP", kept={"atom": ["on", A, "kitchen_cabinet_6/top"], "by": {"skill": "place", "args": {"object": A}}},
                   event="resource_block_b"),
                 H("AF", level="task")]),
    }


def T07(t):
    X, MW = "oatmeal", "kitchen_microwave"
    base = OR(t, "microwave_works")      # nav mw, open, look island, nav oat, pick, nav mw floor, place, close, heat
    stove = [nav("kitchen_stove/top"), place(X, "kitchen_stove/top"), S("heat", food=X, appliance="kitchen_stove", temp_c=40)]
    stuck_island = base[:1] + refused_twice(base[1], MW) + with_ik(recs(look("kitchen_island/top"), nav(X), pick(X), *stove),
                                                                   "pick", X)
    stuck_cab = base[:1] + refused_twice(base[1], MW) + with_ik(recs(S("search", object=X, region="living_room_0_0"),
                                                                     nav(X), pick(X), *stove), "pick", X)
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
            tier="hard", hard="action", base="microwave_works", control="x6_m_ik_open_microwave",
            factor="where the food is",
            challenge="the microwave door cannot be opened from any park; the first pick of the bowl is refused (the "
                      "bowl is on the island, or on the wall cabinet out of view)",
            rationale="the microwave procedure is unavailable (persistent): heat on the stove instead; the microwave "
                      "stays closed, which the goal requires anyway",
            cases={"oatmeal_island": dict(failures=stuck_fail, route=stuck_island),
                   "oatmeal_cabinet": dict(move={X: P("kitchen_cabinet_6/top", 3.7, 0.36)}, failures=stuck_fail,
                                           route=stuck_cab)},
            hyp=[H("CL", failure=f"ik_open_{MW}_persistent", change="appliance", to="kitchen_stove"),
                 H("SR", nominal={"skill": "heat", "args": {"food": X, "appliance": MW}},
                   replacement={"skill": "heat", "args": {"food": X, "appliance": "kitchen_stove"}},
                   cause=f"failure:ik_open_{MW}_persistent")]),
        "x6_m_ik_open_microwave": dict(
            tier="medium", base="microwave_works", control="microwave_works",
            challenge="the first open of the microwave door is refused from its park",
            rationale="matched control of x6_cl_microwave_door_stuck: one re-park fixes it",
            cases={"": dict(failures=[f_ik("open", MW, key="articulated")],
                            route=with_ik(base, "open", MW, key="articulated"))}, hyp=[H("AF", level="local")]),
        "x6_sr_microwave_taken": dict(
            tier="hard", hard="dynamic", base="microwave_works", control="microwave_works",
            goal=copy.deepcopy(holds["goal"]),
            challenge="while the robot fetches the bowl, someone puts the covered soup pot into the open microwave",
            rationale="the appliance is occupied after the plan was made: the robot sees it on arrival, closes the "
                      "door and heats on the stove (now free) instead; the pot must not be taken out onto the floor",
            cases={"": dict(failures=pot_in, route=taken)},
            hyp=[H("SR", nominal={"skill": "heat", "args": {"food": X, "appliance": MW}},
                   replacement={"skill": "heat", "args": {"food": X, "appliance": "kitchen_stove"}},
                   cause="failure:resource_microwave_taken")]),
        "x6_pp_door_opened_after_heat": dict(
            tier="hard", hard="dynamic", base="microwave_works", control="microwave_works",
            challenge="right after the oatmeal is warm, someone opens the microwave door to look",
            rationale="the heating subgoal already holds; only the door subgoal is undone: close it again without "
                      "re-heating (re-running the plan would heat again)",
            cases={"": dict(failures=[f_joint("dependency", MW, "open", ("heat", {"food": X, "appliance": MW}))],
                            route=reopened)},
            hyp=[H("PP", kept={"atom": ["temperature_at_least", X, 40], "by": {"skill": "heat", "args": {"food": X}}},
                   event=f"dependency_{MW}")]),
    }


def T08(t):
    X = "kitchen_sponge"
    base = OR(t, "sponge_on_island")
    back = base + recs(look("kitchen_island/top"), S("search", object=X, region="living_room_0_0"), nav(X), pick(X),
                       nav("kitchen_island/top"), place(X, "kitchen_island/top"))
    return {
        "x6_pp_sponge_taken_after_wipe": dict(
            tier="hard", hard="dynamic", base="sponge_on_island", control="sponge_on_island",
            challenge="right after the robot puts the sponge down on the wiped island, someone takes it to the TV stand",
            rationale="the island is already wiped; only the sponge subgoal is undone: fetch the sponge back without "
                      "wiping again",
            cases={"": dict(failures=[f_move("resource", X, P("tv_stand_2/top", 7.6, 0.38),
                                             ("place", {"object": X}), fid="resource_sponge")], route=back)},
            hyp=[H("PP", kept={"atom": ["wiped", "kitchen_island/top"], "by": {"skill": "wipe", "args": {"surface": "kitchen_island/top"}}},
                   event="resource_sponge"), H("AF", level="task")]),
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
    lid_taken = base[:j_lid] + recs(look("kitchen_stove/top"), S("search", object=LID)) + base[j_lid:]
    tomato_out = base[:2] + recs(look("kitchen_island/top"), nav(TOMATOES[1]), pick(TOMATOES[1]), nav(POT),
                                 S("drop", object=TOMATOES[1], container=POT)) + base[2:]
    kept_tomato = {"atom": ["inside", TOMATOES[0], POT], "by": {"skill": "collect", "args": {"container": POT}}}
    return {
        "x6_cl_spoon_unholdable": dict(
            tier="hard", hard="action", base="lid_off", control="m_grasp_spoon",
            factor="which substitute exists and where",
            challenge="once the tomatoes are in the pot, the breakfast spoon cannot be held (it slips every time); "
                      "another spoon is on the wall cabinet, or only one on the dining table; the first lid pick is "
                      "refused",
            rationale="stirring needs a spoon, not this spoon: switch to another spoon (found where it is) and keep "
                      "the tomatoes in the pot",
            cases={"spoon_cabinet": dict(failures=[f_grasp_persist(SP), f_ik("pick", LID)], route=cabinet,
                                         hyp=[H("CL", failure=f"grasp_{SP}_persistent", change="object",
                                                to="spoon_kitchen_cabinet")]),
                   "spoon_dining": dict(remove=["spoon_kitchen_cabinet"], failures=[f_grasp_persist(SP), f_ik("pick", LID)],
                                        route=dining,
                                        hyp=[H("CL", failure=f"grasp_{SP}_persistent", change="object",
                                               to="spoon_target_table")])},
            hyp=[H("PP", kept=kept_tomato, event=f"grasp_{SP}_persistent"), H("AF", level="task")]),
        "x6_sr_collect_refused": dict(
            tier="hard", hard="action", base="lid_off", control="x6_m_ik_collect",
            challenge="collecting both tomatoes into the pot at once is refused from every park; the first single "
                      "tomato pick slips",
            rationale="the batch skill is unavailable (persistent): decompose into one pick-and-drop per tomato",
            cases={"": dict(failures=[f_ik_where("collect", "ik_collect_persistent", container=POT),
                                      f_grasp(TOMATOES[0])], route=split)},
            hyp=[H("SR", nominal={"skill": "collect", "args": {"container": POT}},
                   replacement={"skill": "drop", "args": {"container": POT}}, cause="failure:ik_collect_persistent"),
                 H("GD", kind="split", batch={"skill": "collect", "args": {"container": POT}}, parts=TOMATOES,
                   cause="failure:ik_collect_persistent"),
                 H("CL", failure="ik_collect_persistent", change="procedure", to="drop")]),
        "x6_m_ik_collect": dict(
            tier="medium", base="lid_off", control="lid_off",
            challenge="the first collect into the pot is refused from its park",
            rationale="matched control of x6_sr_collect_refused: one re-park fixes it",
            cases={"": dict(failures=[f_ik_where("collect", "ik_collect_once", container=POT) | {"persist": False,
                                                                                                "until": "base_skill"}],
                            route=base[:1] + [FAIL(col, True)] + recs(S("approach", target=POT), col) + base[2:])},
            hyp=[H("AF", level="local")]),
        "x6_pp_lid_taken_after_stir": dict(
            tier="hard", hard="dynamic", base="lid_off", control="lid_off",
            challenge="right after the robot stirs, someone takes the pot lid to the other low cabinet",
            rationale="tomatoes in and stirred already hold: find the lid and cover; do not collect or stir again",
            cases={"": dict(failures=[f_move("resource", LID, P("kitchen_cabinet_4/top", 1.4, 0.42),
                                             ("stir", {"container": POT}), fid="resource_lid")], route=lid_taken)},
            hyp=[H("PP", kept=kept_tomato, event="resource_lid"), H("AF", level="task")]),
        "x6_pp_tomato_taken_out": dict(
            tier="hard", hard="dynamic", base="lid_off", control="lid_off",
            challenge="right after the tomatoes go into the pot, the kid takes one back out onto the island",
            rationale="one subgoal is undone, the other still holds: put back only the missing tomato",
            cases={"": dict(failures=[f_move("resource", TOMATOES[1], P("kitchen_island/top", 7.8, 1.62),
                                             ("collect", {"container": POT}), fid="resource_tomato")], route=tomato_out)},
            hyp=[H("PP", kept=kept_tomato, event="resource_tomato")]),
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
    return {
        "x6_gd_can_put_away": dict(
            tier="hard", hard="task", base="can_on_island", control="h_task_can_in_microwave",
            factor="which closed place holds the item",
            instruction=instr, goal=goal, remove=["plate_inside_kitchen_cabinet"],
            challenge="the can was put away in one of two closed places (microwave or wall cabinet)",
            rationale="the item's location is a disjunction the planner must resolve by inspecting both candidates "
                      "(reference route: the worse order, the can is in the second place); each door is opened "
                      "and closed again",
            cases={"in_cabinet": dict(move={CAN: in_cab}, route=mw + [S("close", articulated="kitchen_microwave")]
                                      + open_explore("kitchen_cabinet_6") + take("kitchen_cabinet_6"),
                                      failures=[f_initial("resource", [["on", CAN, "kitchen_cabinet_6/inside_shelf"]],
                                                          fid="resource_can_put_away")],
                                      hyp=[H("DR", blocker="kitchen_cabinet_6", blocked={"skill": "pick", "target": CAN},
                                             cause="failure:resource_can_put_away")]),
                   "in_microwave": dict(move={CAN: in_mw}, route=open_explore("kitchen_cabinet_6")
                                        + [S("close", articulated="kitchen_cabinet_6")] + mw + take("kitchen_microwave"),
                                        failures=[f_initial("resource", [["on", CAN, "kitchen_microwave/inside_floor"]],
                                                            fid="resource_can_put_away")])},
            hyp=[H("GD", kind="inspection", places=["kitchen_microwave", "kitchen_cabinet_6"],
                   cause="failure:resource_can_put_away")]),
        "x6_sr_drop_refused": dict(
            tier="hard", hard="action", base="can_on_island", control="x6_m_ik_drop",
            challenge="dropping the can over the trash can is refused from every park; the first pick is refused",
            rationale="the drop procedure is unavailable (persistent): put the can into the trash can with a place "
                      "instead",
            cases={"": dict(failures=[f_ik("pick", CAN), f_ik_where("drop", "ik_drop_trash_persistent", container="trash_can")],
                            route=with_ik(base[:j], "pick", CAN) + refused_twice(base[j], "trash_can")
                            + recs(place(CAN, "trash_can")))},
            hyp=[H("SR", nominal={"skill": "drop", "args": {"container": "trash_can"}},
                   replacement={"skill": "place", "args": {"receptacle": "trash_can"}},
                   cause="failure:ik_drop_trash_persistent"),
                 H("CL", failure="ik_drop_trash_persistent", change="procedure", to="place")]),
        "x6_m_ik_drop": dict(
            tier="medium", base="can_on_island", control="can_on_island",
            challenge="the first drop over the trash can is refused from its park",
            rationale="matched control of x6_sr_drop_refused: one re-park fixes it",
            cases={"": dict(failures=[f_ik("drop", CAN)], route=with_ik(base, "drop", CAN))}, hyp=[H("AF", level="local")]),
    }


def T12(t):
    CAR, DUCK, BASKET = "toy_car", "rubber_duck", "storage_basket"
    base = OR(t, "toys_out")         # explore, explore, nav car, pick, nav basket, place, nav duck, pick, nav basket, place, nod
    tray = copy.deepcopy(t["variants"]["toys_everywhere"]["add"]["toy_tray"])
    goal = {"all": [["upright", BASKET], ["hand_empty", "right"]],
            "any": [[["inside", CAR, a], ["inside", DUCK, b]] for a in (BASKET, "toy_tray") for b in (BASKET, "toy_tray")]}
    i = at(base, "place", object=CAR)
    unreach = with_grasp(base[:i], CAR) + refused_twice(base[i], BASKET) \
        + recs(nav("bookcase_2/top"), look("bookcase_2/top"), place(CAR, "toy_tray"), nav(DUCK), pick(DUCK),
               nav("bookcase_2/top"), place(DUCK, "toy_tray"))
    k = at(base, "navigate", destination=DUCK)
    moved = lambda region: base[:k] + recs(S("search", object=DUCK, region=region)) + base[k:]  # noqa: E731
    return {
        "x6_cl_basket_unreachable": dict(
            tier="hard", hard="action", base="toys_out", control="m_ik_duck_place", add={"toy_tray": tray}, goal=goal,
            watch=[CAR, DUCK, BASKET, "toy_tray"],
            instruction="It is nearly bedtime. Put the kid's toy car and rubber duck away in the storage basket in the "
                        "bedroom; if you cannot get them into it, the toy tray on the bedroom bookcase is fine.",
            challenge="the car slips on its first pick; then nothing can be put into the basket from any park",
            rationale="the basket is unreachable for every toy (persistent, pinned to the basket): the destination "
                      "changes to the stated tray, and the duck goes straight there without trying the basket",
            cases={"": dict(failures=[f_grasp(CAR), f_ik_where("place", "ik_place_basket_persistent", receptacle=BASKET)],
                            route=unreach)},
            hyp=[H("CL", failure="ik_place_basket_persistent", change="destination", to="toy_tray"),
                 H("AF", level="task")]),
        "x6_pp_duck_moved": dict(
            tier="hard", hard="dynamic", base="toys_out", control="toys_out",
            factor="where the event takes the resource",
            challenge="once the car is in the basket, the kid carries the duck to another room (dining table or "
                      "study desk)",
            rationale="the car subgoal holds; the duck must be found where it went: keep the car, search the duck",
            cases={"dining": dict(failures=[f_move("resource", DUCK, P("dining_table_2/top", 3.7, 6.3),
                                                   ("place", {"object": CAR}), fid="resource_duck")],
                                  route=moved("dining_room_0_1")),
                   "study": dict(failures=[f_move("resource", DUCK, P("desk_1/top", -0.95, -6.02, 128.7),
                                                  ("place", {"object": CAR}), fid="resource_duck")],
                                 route=moved("living_room_0_1"))},
            hyp=[H("PP", kept={"atom": ["inside", CAR, BASKET], "by": {"skill": "place", "args": {"object": CAR}}},
                   event="resource_duck"), H("AF", level="task")]),
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
    two = base + recs(nav(b2), pick(b2), nav("dining_table_2/top"), place(b2, "dining_table_2/top", [3.7, 7.12]),
                      S("search", object=MUG, region="living_room_0_0"), nav(MUG), pick(MUG), nav("dining_table_2/top"),
                      place(MUG, "dining_table_2/top", [3.62, 7.62]))
    kept_bowl = {"atom": ["on", BOWL, "dining_table_2/top"], "by": {"skill": "place", "args": {"object": BOWL}}}
    return {
        "x6_cl_cup_slips": dict(
            tier="hard", hard="action", base="dishes_on_tv_stand", control="x6_m_slip_cup",
            factor="where the substitute is",
            challenge="the first bowl pick is refused (re-park); once the bowl is set, the cup slips out of the hand "
                      "at every carry; the mug is on the bedroom bookcase or on the wall cabinet",
            rationale="the cup cannot be carried at all: the instruction allows a mug, found where it is; the bowl "
                      "on the table stays",
            cases={"mug_bookcase": dict(route=slips([nav("bookcase_2/top"), look("bookcase_2/top")])),
                   "mug_cabinet": dict(move={MUG: P("kitchen_cabinet_6/top", 3.68, 0.36)},
                                       route=slips([S("search", object=MUG, region="living_room_0_0")]))},
            failures=[f_ik("pick", BOWL), f_slip_persist(CUP)],
            hyp=[H("CL", failure=f"slip_{CUP}_persistent", change="object", to=MUG),
                 H("PP", kept=kept_bowl, event=f"slip_{CUP}_persistent"), H("AF", level="task")]),
        "x6_m_slip_cup": dict(
            tier="medium", base="dishes_on_tv_stand", control="dishes_on_tv_stand",
            challenge="the cup slips once at the start of its carry",
            rationale="matched control of x6_cl_cup_slips: transient, picking it again works",
            cases={"": dict(failures=[f_slip(CUP)], route=with_slip(base, CUP))}, hyp=[H("AF", level="local")]),
        "x6_pp_spoon_moved": dict(
            tier="hard", hard="dynamic", base="dishes_on_tv_stand", control="dishes_on_tv_stand",
            factor="where the event takes the resource",
            challenge="right after the cup is set, the kid moves the spoon away (to the far end of the table, or to "
                      "the TV stand)",
            rationale="bowl and cup are in place; only the grouping is broken: bring the spoon back next to them "
                      "instead of moving the dishes",
            cases={"table_end": dict(failures=[f_move("resource", SPOON, P("dining_table_2/top", 3.6, 5.75),
                                                      ("place", {"object": CUP}), fid="resource_spoon")],
                                     route=spoon_back([])),
                   "tv_stand": dict(failures=[f_move("resource", SPOON, P("tv_stand_2/top", 7.0, 0.36),
                                                     ("place", {"object": CUP}), fid="resource_spoon")],
                                    route=spoon_back([S("search", object=SPOON, region="living_room_0_0")]))},
            hyp=[H("PP", kept=kept_bowl, event="resource_spoon")]),
        "x6_gd_bowl_put_away": dict(
            tier="hard", hard="task", base="dishes_on_tv_stand", control="bowl_on_cabinet",
            factor="which closed place holds the item",
            instruction=put_away, goal=g, remove=["bowl_inside_kitchen_cabinet", "plate_inside_kitchen_cabinet"],
            challenge="no bowl is out: the clean bowl was put away in the wall cabinet or the microwave",
            rationale="the bowl's location is a disjunction resolved by inspecting both places (reference route: the "
                      "worse order); the cup is set as usual and the doors are closed again",
            cases={"in_cabinet": dict(move={BOWL: {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.5, 0.36], "yaw_deg": 0.0}},
                                      failures=[f_initial("resource", [["on", BOWL, "kitchen_cabinet_6/inside_shelf"]],
                                                          fid="resource_bowl_put_away")],
                                      route=head + mw + [S("close", articulated="kitchen_microwave")]
                                      + open_explore("kitchen_cabinet_6") + take("kitchen_cabinet_6") + set_rest,
                                      hyp=[H("DR", blocker="kitchen_cabinet_6", blocked={"skill": "pick", "target": BOWL},
                                             cause="failure:resource_bowl_put_away")]),
                   "in_microwave": dict(move={BOWL: {"support": "kitchen_microwave/inside_floor", "xy": [1.8, 9.5], "yaw_deg": 0.0}},
                                        failures=[f_initial("resource", [["on", BOWL, "kitchen_microwave/inside_floor"]],
                                                            fid="resource_bowl_put_away")],
                                        route=head + open_explore("kitchen_cabinet_6") + [S("close", articulated="kitchen_cabinet_6")]
                                        + mw + take("kitchen_microwave") + set_rest,
                                        hyp=[H("DR", blocker="kitchen_microwave", blocked={"skill": "pick", "target": BOWL},
                                               cause="failure:resource_bowl_put_away")])},
            hyp=[H("GD", kind="inspection", places=["kitchen_microwave", "kitchen_cabinet_6"],
                   cause="failure:resource_bowl_put_away")]),
        "x6_gd_two_settings": dict(
            tier="hard", hard="dynamic", base="dishes_on_tv_stand", control="dishes_on_tv_stand",
            move={b2: P("tv_stand_2/top", 6.9, 0.36)}, goal=two_goal, watch=[BOWL, b2, CUP, MUG, SPOON, s2],
            instruction="Set two breakfast places at the dining table: next to each spoon, a bowl and a cup (a mug is "
                        "fine where there is no cup).",
            challenge="two places, two bowls on the TV stand, one cup and the mug; once the first place is set, "
                      "someone takes the mug to the wall cabinet",
            rationale="the goal decomposes into two place settings with an allocation of the cups and bowls; the "
                      "event moves the second place's resource after the first setting holds: keep it, find the mug",
            cases={"": dict(failures=[f_move("resource", MUG, P("kitchen_cabinet_6/top", 3.68, 0.36),
                                             ("place", {"object": CUP}), fid="resource_mug")], route=two)},
            hyp=[H("GD", kind="decomposition", subgoals=[["grouped", [BOWL, CUP, SPOON]], ["grouped", [b2, MUG, s2]]],
                   cause="goal"),
                 H("PP", kept=kept_bowl, event="resource_mug"), H("AF", level="task")]),
    }


def T14(t):
    B = "book_red"
    base = OR(t, "e1_book_ready")                 # nav desk, look, nav book, pick, nav bookcase, place
    i = at(base, "pick", object=B)
    carry, place_ = base[i + 1], base[i + 2]
    two = (base[:i + 1] + [FAIL(carry, True)] + recs(S("approach", target=B), look(B), pick(B)) + [FAIL(carry, True)]
           + recs(S("approach", target=B), look(B), pick(B, hands="both"), carry) + [place_])
    return {
        "x6_sr_two_hand_carry": dict(
            tier="hard", hard="action", base="e1_book_ready", control="x6_m_slip_book",
            challenge="the red book slips out of the one-handed pinch at the start of every carry; the first shelving "
                      "place is refused from its park",
            rationale="one-handed retries never work (persistent): carry it with both hands instead",
            cases={"": dict(failures=[f_slip_persist(B, one_handed=True), f_ik("place", B)],
                            route=with_ik(two, "place", B))},
            hyp=[H("SR", nominal={"skill": "pick", "args": {"object": B, "hands": "right"}},
                   replacement={"skill": "pick", "args": {"object": B, "hands": "both"}},
                   cause=f"failure:slip_{B}_persistent"),
                 H("CL", failure=f"slip_{B}_persistent", change="procedure", to="pick:hands=both")]),
        "x6_m_slip_book": dict(
            tier="medium", base="e1_book_ready", control="e1_book_ready",
            challenge="the red book slips once at the start of the carry",
            rationale="matched control of x6_sr_two_hand_carry: transient, picking it again works",
            cases={"": dict(failures=[f_slip(B)], route=with_slip(base, B))}, hyp=[H("AF", level="local")]),
    }


def T17(t):
    B, POT, LID, F = "wooden_block_b", "handled_cooking_pot", "pot_lid", "floor_block"
    base = OR(t, "lid_off")                     # nav stove, look stove, nav island, look island, hide
    hide = base[-1]
    primitive = recs(nav(B), pick(B), nav(POT), S("drop", object=B, container=POT), nav(LID), pick(LID), nav(POT),
                     S("cover", container=POT, lid=LID))
    refused = base[:-1] + refused_twice(hide, POT) + with_grasp(primitive, B)
    lifted = base + recs(look("kitchen_stove/top"), S("search", object=LID), nav(LID), pick(LID),
                         nav(POT), S("cover", container=POT, lid=LID))
    both_goal = {"all": [["hidden", B], ["hidden", F], ["covered", POT, LID], ["hand_empty", "right"]]}
    both = base + recs(S("search", object=F, region="living_room_0_0"), nav(POT), S("uncover", container=POT),
                       nav(F), look(F), S("hide", object=F, receptacle=POT, lid=LID))
    return {
        "x6_sr_hide_refused": dict(
            tier="hard", hard="action", base="lid_off", control="x6_m_ik_hide",
            challenge="the hide skill is refused from every park; the first block pick slips",
            rationale="the composite procedure is unavailable (persistent): realise it with primitives (pick the "
                      "block, drop it into the pot, pick the lid, cover)",
            cases={"": dict(failures=[f_ik_persist("hide", B), f_grasp(B)], route=refused)},
            hyp=[H("SR", nominal={"skill": "hide", "args": {"object": B}},
                   replacement={"skill": "drop", "args": {"object": B, "container": POT}},
                   cause=f"failure:ik_hide_{B}_persistent"),
                 H("CL", failure=f"ik_hide_{B}_persistent", change="procedure", to="drop")]),
        "x6_m_ik_hide": dict(
            tier="medium", base="lid_off", control="lid_off",
            challenge="the first hide is refused from its park",
            rationale="matched control of x6_sr_hide_refused: one re-park fixes it",
            cases={"": dict(failures=[f_ik("hide", B)], route=with_ik(base, "hide", B))}, hyp=[H("AF", level="local")]),
        "x6_pp_lid_lifted": dict(
            tier="hard", hard="dynamic", base="lid_off", control="lid_off",
            challenge="right after the block is hidden, someone peeks and leaves the lid on the other low cabinet",
            rationale="the block is still in the pot: find the lid and cover again, do not take the block out",
            cases={"": dict(failures=[f_move("resource", LID, P("kitchen_cabinet_4/top", 1.4, 0.42),
                                             ("hide", {"object": B}), fid="resource_lid")], route=lifted)},
            hyp=[H("PP", kept={"atom": ["hidden", B], "by": {"skill": "hide", "args": {"object": B}}}, event="resource_lid"),
                 H("AF", level="task")]),
        "x6_gd_hide_both_event": dict(
            tier="hard", hard="dynamic", base="lid_off", control="lid_off",
            move={F: P("kitchen_island/top", 7.25, 1.85)}, goal=both_goal, watch=[B, F, LID, POT, "oatmeal", "rolling_pin"],
            instruction="We are playing hide-and-seek with the kid's toy blocks: hide both wooden blocks in the empty "
                        "pot on the stove and put the lid on so they cannot see them.",
            challenge="two blocks to hide in one pot; once the first is hidden, the kid takes the other block to the "
                      "TV stand",
            rationale="the goal decomposes into two hides that share the lid (uncover between them); the event moves "
                      "the second block after the first subgoal holds: keep the first hidden, find the second",
            cases={"": dict(failures=[f_move("resource", F, P("tv_stand_2/top", 7.0, 0.36), ("hide", {"object": B}),
                                             fid="resource_floor_block")], route=both)},
            hyp=[H("GD", kind="decomposition", subgoals=[["hidden", B], ["hidden", F]], cause="goal"),
                 H("PP", kept={"atom": ["hidden", B], "by": {"skill": "hide", "args": {"object": B}}},
                   event="resource_floor_block"), H("AF", level="task")]),
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
        "x6_gd_bowl_in_microwave": dict(
            tier="hard", hard="task", base="at_island", control="at_island", goal=goal_mw,
            move={"bowl_inside_kitchen_cabinet": in_mw},
            instruction="Grandma wants to know whether there is still a clean plate and bowl for dinner, in the low "
                        "wall cabinet or the microwave. Have a look and close every door properly afterwards.",
            challenge="the plate is in the wall cabinet, the bowl was left in the microwave",
            rationale="the cabinet answers only half of the question: the inspection continues at the second place",
            cases={"": dict(failures=[f_initial("resource", [["on", "bowl_inside_kitchen_cabinet", "kitchen_microwave/inside_floor"]],
                                                fid="resource_bowl_elsewhere")], route=base + mw)},
            hyp=[H("GD", kind="inspection", places=[C6, MW], cause="failure:resource_bowl_elsewhere")]),
        "x6_gd_three_places": dict(
            tier="hard", hard="task", base="at_island", control="h_task_two_cabinets", goal=goal_3,
            move={"bowl_inside_kitchen_cabinet": in_mw},
            instruction="Grandma wants to know whether there is still a clean plate and bowl for dinner somewhere in "
                        "the low kitchen cabinets or the microwave. Have a look and close every door properly afterwards.",
            challenge="the plate is in the wall cabinet, the other low cabinet is empty, the bowl is in the microwave",
            rationale="three candidate places, the answer is spread over two of them and one is empty: the "
                      "inspection must continue past the empty cabinet",
            cases={"": dict(failures=[f_initial("resource", [["on", "bowl_inside_kitchen_cabinet", "kitchen_microwave/inside_floor"]],
                                                fid="resource_bowl_elsewhere")], route=base + c4 + mw)},
            hyp=[H("GD", kind="inspection", places=[C6, C4, MW], cause="failure:resource_bowl_elsewhere")]),
        "x6_pp_door_reopened": dict(
            tier="hard", hard="dynamic", base="at_island", control="at_island",
            challenge="right after the robot closes the cabinet, someone opens the door again",
            rationale="both dishes were already seen: close the door again, do not inspect again",
            cases={"": dict(failures=[f_joint("dependency", C6, "open", ("close", {"articulated": C6}))],
                            route=base + recs(S("close", articulated=C6)))},
            hyp=[H("PP", kept={"atom": ["observed", "bowl_inside_kitchen_cabinet"],
                               "by": {"skill": "inspect", "args": {"receptacle": C6}}}, event=f"dependency_{C6}")]),
    }


def T19(t):
    CAN, CUBE, BIN = "soda_can", "foam_cube", "wide_storage_bin"
    base = OR(t, "bin_on_bookcase")             # ... approach bin, drop can, nav cube, pick cube, nav bin, drop cube
    j = at(base, "drop", object=CUBE)
    refused = with_grasp(base[:j], CUBE) + refused_twice(base[j], BIN) + recs(place(CUBE, BIN))
    return {
        "x6_sr_cube_drop_refused": dict(
            tier="hard", hard="action", base="bin_on_bookcase", control="x6_m_ik_drop_cube",
            challenge="once the can is in the bin, the cube slips on its first pick, then dropping it over the bin is "
                      "refused from every park (the light foam would not fall in)",
            rationale="the drop procedure is unavailable for the cube (persistent): place it into the bin instead, and "
                      "keep the can where it is",
            cases={"": dict(failures=[f_grasp(CUBE), f_ik_where("drop", "ik_drop_cube_persistent", object=CUBE, container=BIN)],
                            route=refused)},
            hyp=[H("SR", nominal={"skill": "drop", "args": {"object": CUBE, "container": BIN}},
                   replacement={"skill": "place", "args": {"object": CUBE, "receptacle": BIN}},
                   cause="failure:ik_drop_cube_persistent"),
                 H("CL", failure="ik_drop_cube_persistent", change="procedure", to="place"),
                 H("PP", kept={"atom": ["inside", CAN, BIN], "by": {"skill": "drop", "args": {"object": CAN}}},
                   event="ik_drop_cube_persistent")]),
        "x6_m_ik_drop_cube": dict(
            tier="medium", base="bin_on_bookcase", control="bin_on_bookcase",
            challenge="the first drop of the cube over the bin is refused from its park",
            rationale="matched control of x6_sr_cube_drop_refused: one re-park fixes it",
            cases={"": dict(failures=[f_ik("drop", CUBE)], route=with_ik(base, "drop", CUBE))}, hyp=[H("AF", level="local")]),
    }


def T20(t):
    J, M = "juice_bottle", "mug_counter"
    base = OR(t, "bottle_on_cabinet")           # nav cab6 top, look, nav bottle, pick, nav dining, place
    i = at(base, "pick", object=J)

    def behind(blocker):
        return base[:i] + refused_twice(base[i], J) + recs(nav(blocker), pick(blocker),
                                                          place(blocker, "kitchen_cabinet_6/top", [3.33, 0.4]),
                                                          nav(J), look(J)) + [REC(base[i])] + base[i + 1:]
    BW = "bowl_kitchen_cabinet"
    instr = ("Someone put the juice bottle away in one of the low kitchen cabinets. Put it back on the dining table, "
             "standing up, and close the cabinets again.")
    goal = copy.deepcopy(t["goal"])
    goal["all"] += [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]
    tail = base[i + 1:]
    take = lambda art: [nav(J), pick(J), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]  # noqa: E731
    return {
        "x6_cl_bottle_behind_mug": dict(
            tier="hard", hard="mixed", base="bottle_on_cabinet", control="m_ik_pick",
            factor="which object blocks the reach (blocking relation)",
            challenge="the bottle stands in the back corner of the cabinet top with a mug (or a bowl) right in front "
                      "of it: no park reaches the bottle until that object is moved",
            rationale="re-parking cannot help while the object blocks the reach (wall behind, object in front), so the "
                      "recovery inserts a subgoal on an object outside the goal: move it aside first",
            cases={"mug": dict(move={J: P("kitchen_cabinet_6/top", 3.7, 0.255), M: P("kitchen_cabinet_6/top", 3.7, 0.38)},
                               failures=[f_initial("dependency", [["on", M, "kitchen_cabinet_6/top"]], fid="dependency_in_front"),
                                         {**f_ik_persist("pick", J), "until_moved": M}], route=behind(M),
                               hyp=[H("DR", blocker=M, blocked={"skill": "pick", "target": J}, cause="failure:dependency_in_front"),
                                    H("CL", failure=f"ik_pick_{J}_persistent", change="subgoal", to=M)]),
                   "bowl": dict(move={J: P("kitchen_cabinet_6/top", 3.68, 0.25), BW: P("kitchen_cabinet_6/top", 3.68, 0.405)},
                                remove=["spoon_kitchen_cabinet"],
                                failures=[f_initial("dependency", [["on", BW, "kitchen_cabinet_6/top"]], fid="dependency_in_front"),
                                          {**f_ik_persist("pick", J), "until_moved": BW}], route=behind(BW),
                                hyp=[H("DR", blocker=BW, blocked={"skill": "pick", "target": J}, cause="failure:dependency_in_front"),
                                     H("CL", failure=f"ik_pick_{J}_persistent", change="subgoal", to=BW)])},
            hyp=[]),
        "x6_gd_bottle_put_away": dict(
            tier="hard", hard="task", base="bottle_on_cabinet", control="bottle_on_cabinet", instruction=instr, goal=goal,
            factor="which closed place holds the item",
            remove=["plate_inside_kitchen_cabinet"],
            challenge="the bottle was put away in one of the two low cabinets",
            rationale="a disjunction over closed places: inspect them (reference route: the worse order), take the "
                      "bottle, close both doors",
            cases={"in_cabinet_4": dict(move={J: {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 0.0}},
                                        failures=[f_initial("resource", [["on", J, "kitchen_cabinet_4/inside_shelf"]],
                                                            fid="resource_bottle_put_away")],
                                        route=open_explore("kitchen_cabinet_6") + [S("close", articulated="kitchen_cabinet_6")]
                                        + open_explore("kitchen_cabinet_4") + take("kitchen_cabinet_4") + tail,
                                        hyp=[H("DR", blocker="kitchen_cabinet_4", blocked={"skill": "pick", "target": J},
                                               cause="failure:resource_bottle_put_away")]),
                   "in_cabinet_6": dict(move={J: {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.63, 0.36], "yaw_deg": 0.0}},
                                        failures=[f_initial("resource", [["on", J, "kitchen_cabinet_6/inside_shelf"]],
                                                            fid="resource_bottle_put_away")],
                                        route=open_explore("kitchen_cabinet_4") + [S("close", articulated="kitchen_cabinet_4")]
                                        + open_explore("kitchen_cabinet_6") + take("kitchen_cabinet_6") + tail,
                                        hyp=[H("DR", blocker="kitchen_cabinet_6", blocked={"skill": "pick", "target": J},
                                               cause="failure:resource_bottle_put_away")])},
            hyp=[H("GD", kind="inspection", places=["kitchen_cabinet_6", "kitchen_cabinet_4"],
                   cause="failure:resource_bottle_put_away")]),
    }


def T11(t):
    X, BASKET = "apple", "fruit_basket"
    base = OR(t, "fruits_on_table")             # nav dining, look, nav apple, pick, nav bookcase, look, place basket
    i = at(base, "place", object=X)
    roll = {"id": "placement_apple_basket_persistent", "kind": "placement", "mode": "displaced", "persist": True,
            "to": P("bookcase_2/top", 1.2, -0.36), "report": [["inside", X, BASKET]],
            "trigger": {"skill": "place", "args": {"object": X, "receptacle": BASKET}, "nth": 1}}
    once = dict(roll, id="placement_apple_basket", persist=False)
    tray = recs(nav("desk_1/top"), look("desk_1/top"), nav("serving_tray"), place(X, "serving_tray"))
    again = [FAIL(base[i], True)] + recs(look(X), pick(X))
    return {
        "x6_cl_apple_rolls_out": dict(
            tier="hard", hard="action", base="fruits_on_table", control="x6_m_apple_rolls_out_once",
            challenge="the apple rolls back out of the basket onto the bookcase every time it is put in; the apple "
                      "slips on its first pick",
            rationale="the basket does not keep the apple (persistent placement failure, pinned to the basket): the "
                      "instruction's tray on the study desk replaces it",
            cases={"": dict(failures=[f_grasp(X), roll],
                            route=with_grasp(base[:i], X) + again + again + tray)},
            hyp=[H("CL", failure="placement_apple_basket_persistent", change="destination", to="serving_tray"),
                 H("AF", level="task")]),
        "x6_m_apple_rolls_out_once": dict(
            tier="medium", base="fruits_on_table", control="fruits_on_table",
            challenge="the apple rolls back out of the basket once",
            rationale="matched control of x6_cl_apple_rolls_out: transient, putting it in again works",
            cases={"": dict(failures=[once], route=base[:i] + again + [REC(base[i])])}, hyp=[H("AF", level="local")]),
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
    conds = list(v.get("conditions", []))
    if spec["tier"] == "hard" and spec["hard"] == "task" and not conds:
        conds.append("item_put_away" if any(h.get("kind") == "inspection" for h in spec.get("hyp", []) + cspec.get("hyp", []))
                     else "multi_object_goal")
    if conds:
        v["conditions"] = conds
    v["difficulty"] = spec["tier"]
    v["since"] = "v6"
    v["note"] = spec["challenge"]
    v["v6"] = {"family": fam, "case": case or None, "tier": spec["tier"], "hard_category": spec.get("hard"),
               "challenge": spec["challenge"], "rationale": spec["rationale"], "control": spec["control"],
               "contrast": spec.get("contrast"), "factor": spec.get("factor"),
               "derived_from": spec["base"], "hypotheses": copy.deepcopy(spec.get("hyp", []) + cspec.get("hyp", []))}
    v["move"], v["vary"] = seed_vary(t, v)
    return v


def build_task(t: dict) -> dict:
    t = copy.deepcopy(t)
    fams = FAMILIES[t["task_id"]](t) if t["task_id"] in FAMILIES else {}
    families = {}
    # every v5 formal variant is a one-case family of its own
    for tier, ids in t["v5_formal"].items():
        for vid in ids:
            families[vid] = {"origin": "v5", "design_tier": tier, "cases": [vid],
                             "seeds": {s: vid for s in SEEDS}}
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
        families[fam] = {"origin": "v6", "design_tier": spec["tier"], "hard_category": spec.get("hard"),
                         "control": spec["control"], "cases": names, "factor": spec.get("factor"),
                         "seeds": seed_cases(t["task_id"], fam, names)}
    t["v6_families"] = families
    t["benchmark_version"] = "v6"
    return t


def build() -> dict:
    doc = json.loads(V5.read_text())
    tasks = [build_task(t) for t in doc["tasks"]]
    reg = dict(doc["condition_registry"], **NEW_CONDITIONS)
    out = {"schema_version": 6, "benchmark_version": "v6", "kind": "zenobench_benchmark_tasks",
           "note": "Source: python benchmark/v6/define_tasks_v6.py (reads benchmark/v5/tasks.json); tiers and "
                   "capability verdicts: benchmark/v6/hypotheses.py.",
           "eval_seeds": SEEDS, "condition_registry": reg,
           "tier_definitions": {
               "easy": "the nominal plan works: no failure and no task-level constraint (only the start pose may differ)",
               "medium": "one local adaptation keeps the plan's structure (transient action failure, search, or a "
                         "substitute the instruction names); no core capability required",
               "hard": "the plan must change at the task level: >= 1 verified core capability (DR, GD, SR, CL, PP) "
                       "and not solvable by retrying the nominal plan"},
           "hard_categories": ["task", "action", "mixed", "dynamic"], "tasks": tasks}
    from benchmark.v6.hypotheses import apply_audit
    apply_audit(out)
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
    n_fam = sum(len(t["v6_families"]) for t in doc["tasks"])
    n_new = sum(1 for t in doc["tasks"] for f in t["v6_families"].values() if f["origin"] == "v6")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['tasks'])} tasks, {n_fam} families ({n_new} new)")


if __name__ == "__main__":
    main()
