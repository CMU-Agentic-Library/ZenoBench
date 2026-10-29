"""ZenoBench v5 task suite: the 20 household tasks, each with 2 Easy + 3 Medium + 4 Hard formal variants (180).

    python benchmark/v5/define_tasks_v5.py            # writes benchmark/v5/tasks.json
    python benchmark/v5/define_tasks_v5.py --check    # fails if tasks.json is not up to date

The v3/v4 catalog (benchmark/v3/tasks.json) is read, never written: every existing variant keeps its
configuration (and therefore its hash and its evidence), and Graph Manager / the HTTP service keep reading
v3.  v5 adds variants next to them in a separate catalog with the same task ids, and selects the formal
set per task (``v5_formal``); existing variants outside it stay as ``supplementary``.

Tiers (planning ability, as in v4):

* **Easy**: nominal execution; E2 is a second independent nominal layout (another start room, a longer
  carry), never a failure.
* **Medium**: skill-level adaptation: search, a legal alternative, or a local fallback after a real
  failure; v5 adds action-level injected failures (grasp, slip, IK, placement) with a local recovery.
* **Hard**: four per task, one per category:
  * ``task``    - task-level replanning forced by an initial constraint (capacity, destination,
                  resource, dependency): the v4 Hard where one exists, else a new one;
  * ``action``  - two action-level failures in one episode whose recoveries chain;
  * ``mixed``   - a task-level constraint and an action-level failure in the same episode;
  * ``dynamic`` - a task-level event during execution (something moved, filled or closed).

Every variant names its challenge, its goal (the task's or its own) and one feasible recovery route
(``oracle``); the route's failing steps carry ``expect: fail`` (injected ones also ``injected: true``).
Assets: only objects already annotated in the base scenes or already used by v3/v4 overlays.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
V3 = ROOT / "benchmark/v3/tasks.json"
OUT = ROOT / "benchmark/v5/tasks.json"
VARY = {"groups": [], "start": {"dx": 0.1, "dyaw": 10, "step": 0.05, "step_deg": 5}}

# known free robot start poses (each the default start of a base scene, or a v3 start)
START = {"kitchen": [7.5, 1.0, 0.0], "kitchen_wall": [4.764, 0.699, 20.0], "dining": [4.24, 5.12, 120.0],
         "hall": [4.3, 2.0, 0.0], "bedroom_hall": [3.0, -3.0, 0.0], "living_north": [4.3, -2.2, 0.0],
         "dining_west": [1.6, 8.4, 0.0], "study_hall": [1.7526, -4.05, -150.0], "kitchen_west": [2.2, 1.2, 0.0]}


# ----------------------------------------------------------------- route building
def S(skill, **args):
    return {"skill": skill, "args": args}


def FAIL(step, injected=False):
    out = dict(copy.deepcopy(step), expect="fail", role="failure")
    if injected:
        out["injected"] = True
    return out


def REC(step):
    return dict(copy.deepcopy(step), role="recover")


def find(steps, skill, start=0, last=False, **match):
    idx = [i for i, s in enumerate(steps) if i >= start and s["skill"] == skill and s.get("expect") != "fail"
           and all(s["args"].get(k) == v for k, v in match.items())]
    if not idx:
        raise KeyError(f"no {skill} {match} in route from {start}")
    return idx[-1] if last else idx[0]


def first_carry(steps, x):
    """Index of the navigate that carries ``x`` after its first successful pick."""
    i = find(steps, "pick", object=x)
    return find(steps, "navigate", start=i + 1)


def with_grasp(steps, x, nth=1):
    """The nth pick of x is injected to fail (the object falls back); look at it and pick it again."""
    steps = copy.deepcopy(steps)
    i = find(steps, "pick", object=x)
    steps[i:i + 1] = [FAIL(steps[i], True), REC(S("look", target=x)), REC(steps[i])]
    return steps


def with_ik(steps, skill, x, key="object"):
    """The first ``skill`` on x is refused (no IK from this park); re-park with approach, then retry."""
    steps = copy.deepcopy(steps)
    i = find(steps, skill, **{key: x})
    target = x if skill != "place" else steps[i]["args"].get("receptacle", x)
    steps[i:i + 1] = [FAIL(steps[i], True), REC(S("approach", target=target)), REC(steps[i])]
    return steps


def with_slip(steps, x):
    """x slips at the start of its first carry; look, pick it again, drive on."""
    steps = copy.deepcopy(steps)
    i = first_carry(steps, x)
    steps[i:i + 1] = [FAIL(steps[i], True), REC(S("look", target=x)), REC(S("pick", object=x)), REC(steps[i])]
    return steps


def with_place_miss(steps, x, skill="place"):
    """The last place / drop of x is injected to miss; look, pick it again, repeat the same placement."""
    steps = copy.deepcopy(steps)
    i = find(steps, skill, last=True, object=x)
    steps[i:i + 1] = [FAIL(steps[i], True), REC(S("look", target=x)), REC(S("pick", object=x)), REC(steps[i])]
    return steps


def prefix(steps, *pre):
    return [REC(p) for p in pre] + copy.deepcopy(steps)


def replace_first(steps, skill, new, **match):
    steps = copy.deepcopy(steps)
    i = find(steps, skill, **match)
    steps[i:i + 1] = new
    return steps


# ----------------------------------------------------------------- failure specs
def f_grasp(x, nth=1):
    return {"id": f"grasp_{x}", "kind": "grasp", "trigger": {"skill": "pick", "args": {"object": x}, "nth": nth}}


def f_ik(skill, x, key="object", fid=None):
    return {"id": fid or f"ik_{skill}_{x}", "kind": "ik", "trigger": {"skill": skill, "args": {key: x}, "nth": 1},
            "until": "base_skill"}


def f_slip(x):
    return {"id": f"slip_{x}", "kind": "slip", "trigger": {"skill": "navigate", "while_holding": x, "nth": 1}}


def f_place_miss(x, to, report, skill="place"):
    return {"id": f"place_{x}", "kind": "placement", "mode": "displaced", "to": to, "report": report,
            "trigger": {"skill": skill, "args": {"object": x}, "nth": 1}}


def f_move(kind, obj, to, after, fid=None, nth=1, after_fired=None, on="success"):
    """Dynamic task-level event: ``obj`` is moved to ``to`` after the call ``after`` = (skill, {args})."""
    f = {"id": fid or f"{kind}_{obj}", "kind": kind, "when": "dynamic",
         "trigger": {"skill": after[0], "args": after[1], "nth": nth, "on": on},
         "event": {"type": "move_object", "object": obj, "to": to}}
    if after_fired:
        f["after_fired"] = after_fired
    return f


def f_joint(kind, art, value, after, fid=None):
    return {"id": fid or f"{kind}_{art}", "kind": kind, "when": "dynamic",
            "trigger": {"skill": after[0], "args": after[1], "nth": 1},
            "event": {"type": "set_joint", "articulated": art, "value": value}}


def f_initial(kind, check, fid=None, event=None):
    f = {"id": fid or f"{kind}_initial", "kind": kind, "when": "initial", "check": check}
    if event:
        f["event"] = event
    return f


def P(support, x, y, yaw=0.0):
    return {"support": support, "xy": [x, y], "yaw_deg": yaw}


# ----------------------------------------------------------------- per-task design
# Each entry: formal ids per tier (existing ids are reused as they are), and the new variants:
#   {id: {"tier", "base": existing variant whose overlay is copied, "challenge", "route": steps | name,
#         + any variant field (move, add, start, failures, goal, instruction, ...)}}
def design(t, R):
    """t: the v3 task; R(name): a copy of one of its routes' steps."""
    tid = t["task_id"]
    D = DESIGNS[tid]
    return D(t, R)


def T01(t, R):
    X = "paperback_book"
    nom = R("nominal")
    return {
        "easy": ["overhang_ready", "e2_from_dining_room"],
        "medium": ["no_overhang", "far_no_overhang", "m_ik_pick"],
        "hard": ["table_set", "h_action_ik_pick_and_place", "h_mixed_table_set_ik", "h_dynamic_pushed_back"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="overhang_ready", start=START["dining"],
                                        challenge="the robot starts in the dining room; a longer trip to the island and back",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_ik_pick": dict(tier="medium", base="overhang_ready", failures=[f_ik("pick", X)],
                              challenge="the first pick is refused (no IK from that park): re-park and retry",
                              route=with_ik(nom, "pick", X)),
            "h_action_ik_pick_and_place": dict(
                tier="hard", hard="action", base="overhang_ready",
                failures=[f_ik("pick", X), f_ik("place", X, fid="ik_place_book")],
                challenge="both the pick at the island and the place at the table are refused from their first parks",
                route=with_ik(with_ik(nom, "pick", X), "place", X)),
            "h_mixed_table_set_ik": dict(
                tier="hard", hard="mixed", base="table_set", failures=[f_ik("pick", X)],
                challenge="the set table (choose a reading spot clear of the tableware) and a refused first pick",
                route=with_ik(R("hard_reading_spot"), "pick", X)),
            "h_dynamic_pushed_back": dict(
                tier="hard", hard="dynamic", base="overhang_ready",
                failures=[f_move("dependency", X, P("kitchen_island/top", 7.62, 1.59, 90),
                                 ("navigate", {"destination": X}))],
                challenge="while the robot drives over, someone pushes the book back from the edge: "
                          "the edge pinch fails until it is exposed again",
                route=R("fallback_expose")),
        }}


def T02(t, R):
    nom = R("nominal")
    return {
        "easy": ["clear", "e2_from_wall_cabinet"],
        "medium": ["crowded", "far_crowded", "m_grasp_b"],
        "hard": ["edge_base", "h_action_grasp_and_ik", "h_mixed_edge_base_grasp", "h_dynamic_base_moved_to_edge"],
        "new": {
            "e2_from_wall_cabinet": dict(tier="easy", base="clear", start=START["kitchen_wall"],
                                         challenge="the robot starts by the wall cabinet, facing the island",
                                         route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_grasp_b": dict(tier="medium", base="clear", failures=[f_grasp("wooden_block_b")],
                              challenge="block B slips from the fingers on the first pick",
                              route=with_grasp(nom, "wooden_block_b")),
            "h_action_grasp_and_ik": dict(
                tier="hard", hard="action", base="clear",
                failures=[f_grasp("wooden_block_b"), f_ik("stack", "wooden_block_b")],
                challenge="block B slips on the first pick, then the first stack is refused from its park",
                route=with_ik(with_grasp(nom, "wooden_block_b"), "stack", "wooden_block_b")),
            "h_mixed_edge_base_grasp": dict(
                tier="hard", hard="mixed", base="edge_base", failures=[f_grasp("wooden_block_a")],
                challenge="block A at the island edge must not be the base, and it slips on the first pick",
                route=with_grasp(R("hard_stack_on_open_block"), "wooden_block_a")),
            "h_dynamic_base_moved_to_edge": dict(
                tier="hard", hard="dynamic", base="clear",
                failures=[f_move("destination", "wooden_block_a", P("kitchen_island/top", 7.3, 1.535),
                                 ("pick", {"object": "wooden_block_b"}))],
                challenge="after block B is picked, someone shoves block A to the island edge: stacking on it "
                          "would topple, so B goes down in the open and A is stacked on B",
                route=nom[:3] + [REC(S("look", target="wooden_block_a")),
                                 REC(S("place", object="wooden_block_b", receptacle="kitchen_island/top",
                                       hint_xy=[7.0, 1.66])),
                                 REC(S("navigate", destination="wooden_block_a")),
                                 REC(S("pick", object="wooden_block_a")),
                                 REC(S("navigate", destination="wooden_block_b")),
                                 REC(S("approach", target="wooden_block_b")),
                                 REC(S("stack", object="wooden_block_a", base="wooden_block_b"))]),
        }}


def T03(t, R):
    nom = R("nominal")
    return {
        "easy": ["large_only", "e2_from_dining_room"],
        "medium": ["small_and_large", "far_small_and_large", "m_grasp_spoon"],
        "hard": ["three_containers", "h_action_slip_and_miss", "h_mixed_three_containers_ik", "h_dynamic_spoon_taken"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="large_only", start=START["dining"],
                                        challenge="the robot starts in the dining room",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_grasp_spoon": dict(tier="medium", base="large_only", failures=[f_grasp("breakfast_spoon")],
                                  challenge="the spoon slips from the fingers on the first pick",
                                  route=with_grasp(nom, "breakfast_spoon")),
            "h_action_slip_and_miss": dict(
                tier="hard", hard="action", base="large_only",
                failures=[f_slip("rolling_pin"),
                          f_place_miss("rolling_pin", P("tv_stand_2/top", 7.75, 0.36, 0),
                                       [["inside", "rolling_pin", "wide_storage_bin"]])],
                challenge="the rolling pin slips at the start of the carry, and the first place misses the bin",
                route=with_place_miss(with_slip(nom, "rolling_pin"), "rolling_pin")),
            "h_mixed_three_containers_ik": dict(
                tier="hard", hard="mixed", base="three_containers", failures=[f_ik("pick", "rolling_pin")],
                challenge="allocate by size (the pin only fits the wide bin) and the first pin pick is refused",
                route=with_ik(R("hard_measure_then_wide_bin"), "pick", "rolling_pin")),
            "h_dynamic_spoon_taken": dict(
                tier="hard", hard="dynamic", base="large_only",
                failures=[f_move("resource", "breakfast_spoon", P("kitchen_cabinet_6/top", 3.70, 0.36, 90),
                                 ("look", {"target": "tv_stand_2/top"}))],
                challenge="once the robot has looked around, someone takes the spoon to the wall cabinet: "
                          "it is not where it was seen and must be searched for",
                route=R("nominal")[:2] + [REC(S("search", object="breakfast_spoon", region="living_room_0_0"))]
                + R("nominal")[2:]),
        }}


def T04(t, R):
    nom = R("nominal")
    occupied = {"pot_lid": P("kitchen_cabinet_6/top", 3.335, 0.36), "oatmeal": P("kitchen_cabinet_6/top", 3.7, 0.36)}
    make_room = [S("look", target="kitchen_island/top"), S("navigate", destination="kitchen_cabinet_6/top"),
                 S("look", target="kitchen_cabinet_6/top"), S("navigate", destination="oatmeal"),
                 S("pick", object="oatmeal"), S("navigate", destination="kitchen_cabinet_4/top"),
                 S("place", object="oatmeal", receptacle="kitchen_cabinet_4/top"),
                 S("navigate", destination="cup_counter_b"), S("pick", object="cup_counter_b"),
                 S("navigate", destination="kitchen_cabinet_6/top"),
                 S("place", object="cup_counter_b", receptacle="kitchen_cabinet_6/top")]
    task_goal = {"any": t["goal"]["any"], "all": t["goal"]["all"] + [["upright", "oatmeal"], ["upright", "pot_lid"]]}
    return {
        "easy": ["cup_available", "e2_from_dining_room"],
        "medium": ["no_cup", "no_cup_mug_away", "m_ik_cup"],
        "hard": ["h_task_spot_taken", "h_action_ik_and_grasp", "h_mixed_spot_taken_ik", "h_dynamic_cup_taken"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="cup_available", start=START["dining"],
                                        challenge="the robot starts in the dining room",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_ik_cup": dict(tier="medium", base="cup_available", failures=[f_ik("pick", "cup_counter_b")],
                             challenge="the first cup pick is refused (no IK from that park): re-park and retry",
                             route=with_ik(nom, "pick", "cup_counter_b")),
            "h_task_spot_taken": dict(
                tier="hard", hard="task", base="cup_available", move=occupied, goal=task_goal,
                failures=[f_initial("destination", [["on", "oatmeal", "kitchen_cabinet_6/top"],
                                                    ["on", "pot_lid", "kitchen_cabinet_6/top"]])],
                challenge="the drinks spot is taken by the oatmeal bowl and the pot lid (no free spot for a cup): "
                          "make room first (move the bowl), then set the cup",
                route=make_room),
            "h_action_ik_and_grasp": dict(
                tier="hard", hard="action", base="cup_available",
                failures=[f_ik("pick", "cup_counter_b"), f_ik("place", "cup_counter_b", fid="ik_place_cup")],
                challenge="the first cup pick and the first place on the cabinet are both refused from their parks",
                route=with_ik(with_ik(nom, "pick", "cup_counter_b"), "place", "cup_counter_b")),
            "h_mixed_spot_taken_ik": dict(
                tier="hard", hard="mixed", base="cup_available", move=occupied, goal=task_goal,
                failures=[f_initial("destination", [["on", "oatmeal", "kitchen_cabinet_6/top"]]),
                          f_ik("pick", "oatmeal")],
                challenge="make room on the cabinet, and the first pick of the bowl is refused",
                route=with_ik(make_room, "pick", "oatmeal")),
            "h_dynamic_cup_taken": dict(
                tier="hard", hard="dynamic", base="cup_available",
                failures=[f_move("resource", "cup_counter_b", P("dining_table_2/top", 3.7, 6.3),
                                 ("look", {"target": "kitchen_island/top"}))],
                challenge="right after the robot looked, someone takes the cup away: the mug next to it is the "
                          "allowed substitute (or search the cup)",
                route=[REC(S("look", target="kitchen_island/top")), REC(S("navigate", destination="mug")),
                       REC(S("pick", object="mug")), REC(S("navigate", destination="kitchen_cabinet_6/top")),
                       REC(S("place", object="mug", receptacle="kitchen_cabinet_6/top"))]),
        }}


def T05(t, R):
    pencil_goal = {"all": [["on", "pencil", "desk_1/top"], ["hand_empty", "right"]]}
    instr = ("The kid needs a pencil for maths homework. Bring the pencil to the study desk.",
             "孩子做数学作业需要铅笔，请把铅笔拿到书房的书桌上。")
    alt = R("alternative_pencil")
    nom_p = [s for s in alt if s.get("expect") != "fail"]          # the pencil route without the pen probe
    in_cab = {"pencil": P("kitchen_cabinet_6/inside_shelf", 3.63, 0.36, 90)}
    no_plate = ["plate_inside_kitchen_cabinet"]           # the pencil lies where the plate usually is
    cab_route = [S("navigate", destination="kitchen_cabinet_6"), S("open", articulated="kitchen_cabinet_6"),
                 S("look", target="kitchen_cabinet_6/inside_shelf"), S("navigate", destination="pencil"),
                 S("pick", object="pencil"), S("retreat", obstacle="kitchen_cabinet_6", distance_m=0.3),
                 S("close", articulated="kitchen_cabinet_6"), S("navigate", destination="desk_1/top"),
                 S("place", object="pencil", receptacle="desk_1/top")]
    cab_goal = {"any": t["goal"]["any"], "all": t["goal"]["all"] + [["is_closed", "kitchen_cabinet_6"]]}
    cab_instr = ("The kid needs something to write with for homework. Bring a pen to the study desk; if there is no "
                 "pen, a pencil. The pencils are kept in the low wall cabinet; close it again afterwards.",
                 "孩子写作业需要笔。请把钢笔拿到书房书桌上；没有钢笔就拿铅笔。铅笔收在矮墙柜里，拿完请把柜门关好。")
    return {
        "easy": ["e1_pencil_asked", "e2_pencil_asked_far"],
        "medium": ["no_pen", "no_pen_pencil_away", "m_grasp_pencil"],
        "hard": ["h_task_pencil_in_cabinet", "h_action_grasp_and_ik", "h_mixed_cabinet_ik", "h_dynamic_pencil_taken"],
        "new": {
            "e1_pencil_asked": dict(tier="easy", base="no_pen", goal=pencil_goal, instruction=instr[0],
                                    instruction_zh=instr[1], challenge="bring the named pencil from the bedroom bookcase",
                                    route=nom_p),
            "e2_pencil_asked_far": dict(tier="easy", base="no_pen", goal=pencil_goal, instruction=instr[0],
                                        instruction_zh=instr[1], start=START["kitchen"],
                                        challenge="the same chore starting in the kitchen: a long trip across the house",
                                        route=nom_p),
            "m_grasp_pencil": dict(tier="medium", base="no_pen", failures=[f_grasp("pencil")],
                                   challenge="no pen (pencil substitute) and the pencil slips on the first pick",
                                   route=with_grasp(alt, "pencil")),
            "h_task_pencil_in_cabinet": dict(
                tier="hard", hard="task", base="no_pen", move=in_cab, remove=no_plate, goal=cab_goal, instruction=cab_instr[0],
                instruction_zh=cab_instr[1],
                failures=[f_initial("dependency", [["is_closed", "kitchen_cabinet_6"],
                                                   ["on", "pencil", "kitchen_cabinet_6/inside_shelf"]])],
                challenge="no pen; the pencil is behind a closed cabinet door: open, take it, close again",
                route=cab_route),
            "h_action_grasp_and_ik": dict(
                tier="hard", hard="action", base="no_pen",
                failures=[f_grasp("pencil"), f_ik("place", "pencil", fid="ik_place_pencil")],
                challenge="the pencil slips on the first pick and the first place on the desk is refused",
                route=with_ik(with_grasp(alt, "pencil"), "place", "pencil")),
            "h_mixed_cabinet_ik": dict(
                tier="hard", hard="mixed", base="no_pen", move=in_cab, remove=no_plate, goal=cab_goal, instruction=cab_instr[0],
                instruction_zh=cab_instr[1],
                failures=[f_initial("dependency", [["is_closed", "kitchen_cabinet_6"]]),
                          f_ik("open", "kitchen_cabinet_6", key="articulated")],
                challenge="the pencil behind a closed door, and the first open is refused from its park",
                route=with_ik(cab_route, "open", "kitchen_cabinet_6", key="articulated")),
            "h_dynamic_pencil_taken": dict(
                tier="hard", hard="dynamic", base="no_pen",
                failures=[f_move("resource", "pencil", P("dining_table_2/top", 3.7, 6.3),
                                 ("look", {"target": "bookcase_2/top"}))],
                challenge="no pen; just after the robot saw the pencil, someone takes it to the dining table",
                route=R("hard_search_pencil")),
        }}


def T06(t, R):
    nom = R("nominal")
    occ = [f_move("destination", "pot_lid", P("kitchen_cabinet_6/top", 3.335, 0.36),
                  ("pick", {"object": "wooden_block_a"}), fid="destination_lid"),
           f_move("destination", "oatmeal", P("kitchen_cabinet_6/top", 3.7, 0.36),
                  ("pick", {"object": "wooden_block_a"}), fid="destination_oatmeal")]
    return {
        "easy": ["free", "e2_from_dining_room"],
        "medium": ["occupied", "occupied_block_away", "m_slip_block"],
        "hard": ["display_hidden", "h_action_slip_and_ik", "h_mixed_hidden_grasp", "h_dynamic_cabinet_filled"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="free", start=START["dining"],
                                        challenge="the robot starts in the dining room",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_slip_block": dict(tier="medium", base="free", failures=[f_slip("wooden_block_a")],
                                 challenge="the block slips at the start of the carry",
                                 route=with_slip(nom, "wooden_block_a")),
            "h_action_slip_and_ik": dict(
                tier="hard", hard="action", base="free",
                failures=[f_slip("wooden_block_a"), f_ik("place", "wooden_block_a")],
                challenge="the block slips on the way, then the first place on the cabinet is refused",
                route=with_ik(with_slip(nom, "wooden_block_a"), "place", "wooden_block_a")),
            "h_mixed_hidden_grasp": dict(
                tier="hard", hard="mixed", base="display_hidden", failures=[f_grasp("wooden_block_a")],
                challenge="the cabinet's free space is hidden behind a row (display on the TV stand) and the block "
                          "slips on the first pick",
                route=with_grasp(R("hard_open_display"), "wooden_block_a")),
            "h_dynamic_cabinet_filled": dict(
                tier="hard", hard="dynamic", base="free", move={"oatmeal": P("kitchen_island/top", 6.69, 1.83)},
                failures=occ,
                challenge="after the block is picked, someone puts the pot lid and the oatmeal on the cabinet top: "
                          "no room left, the TV stand is the other allowed display",
                route=R("alternative_tv_stand")),
        }}


def T07(t, R):
    nom = R("nominal")
    X = "oatmeal"
    return {
        "easy": ["microwave_works", "e2_from_dining_room"],
        "medium": ["microwave_broken", "broken_oatmeal_away", "m_ik_oatmeal"],
        "hard": ["microwave_holds_pot", "h_action_ik_and_slip", "h_mixed_pot_inside_grasp", "h_dynamic_door_opened"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="microwave_works", start=START["dining"],
                                        challenge="the robot starts in the dining room", route=nom),
            "m_ik_oatmeal": dict(tier="medium", base="microwave_works", failures=[f_ik("pick", X)],
                                 challenge="the first pick of the bowl is refused from its park",
                                 route=with_ik(nom, "pick", X)),
            "h_action_ik_and_slip": dict(
                tier="hard", hard="action", base="microwave_works", failures=[f_ik("pick", X), f_slip(X)],
                challenge="the first pick is refused and the bowl then slips at the start of the carry",
                route=with_slip(with_ik(nom, "pick", X), X)),
            "h_mixed_pot_inside_grasp": dict(
                tier="hard", hard="mixed", base="microwave_holds_pot", failures=[f_ik("pick", X)],
                challenge="the microwave holds the soup pot (use the stove) and the first bowl pick is refused",
                route=with_ik(R("hard_stove_instead"), "pick", X)),
            "h_dynamic_door_opened": dict(
                tier="hard", hard="dynamic", base="microwave_works",
                failures=[f_joint("dependency", "kitchen_microwave", "open",
                                  ("close", {"articulated": "kitchen_microwave"}))],
                challenge="just after the robot closes the microwave, someone opens the door again: heating "
                          "needs it closed",
                route=nom[:-1] + [FAIL(nom[-1]), REC(S("close", articulated="kitchen_microwave")), REC(nom[-1])]),
        }}


def T08(t, R):
    nom = R("nominal")
    X = "kitchen_sponge"
    return {
        "easy": ["sponge_on_island", "e2_from_dining_room"],
        "medium": ["sponge_on_tv_stand", "far_sponge_tv", "m_grasp_sponge"],
        "hard": ["island_cluttered", "h_action_grasp_and_ik", "h_mixed_cluttered_grasp", "h_dynamic_sponge_taken"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="sponge_on_island", start=START["dining"],
                                        challenge="the robot starts in the dining room",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_grasp_sponge": dict(tier="medium", base="sponge_on_island", failures=[f_grasp(X)],
                                   challenge="the sponge slips on the first pick", route=with_grasp(nom, X)),
            "h_action_grasp_and_ik": dict(
                tier="hard", hard="action", base="sponge_on_island",
                failures=[f_grasp(X), f_ik("wipe", "kitchen_island/top", key="surface")],
                challenge="the sponge slips on the first pick, and the first wipe is refused from its park",
                route=with_ik(with_grasp(nom, X), "wipe", "kitchen_island/top", key="surface")),
            "h_mixed_cluttered_grasp": dict(
                tier="hard", hard="mixed", base="island_cluttered", failures=[f_grasp(X)],
                challenge="clear the strip first (put everything back) and the sponge slips on the first pick",
                route=with_grasp(R("hard_proactive"), X)),
            "h_dynamic_sponge_taken": dict(
                tier="hard", hard="dynamic", base="sponge_on_island",
                failures=[f_move("resource", X, P("tv_stand_2/top", 7.6, 0.38), ("look", {"target": "kitchen_island/top"}))],
                challenge="after the robot looked at the island, someone puts the sponge on the TV stand",
                route=[REC(S("look", target="kitchen_island/top")), REC(S("search", object=X, region="living_room_0_0"))]
                + R("nominal_from_tv_stand")[2:]),
        }}


def T09(t, R):
    nom = R("nominal")
    X = "breakfast_spoon"
    return {
        "easy": ["lid_off", "e2_from_dining_room"],
        "medium": ["lid_on", "lid_on_spoon_away", "m_grasp_spoon"],
        "hard": ["cookware_choice", "h_action_grasp_and_ik", "h_mixed_cookware_grasp", "h_dynamic_spoon_taken"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="lid_off", start=START["dining"],
                                        challenge="the robot starts in the dining room",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_grasp_spoon": dict(tier="medium", base="lid_off", failures=[f_grasp(X)],
                                  challenge="the spoon slips on the first pick", route=with_grasp(nom, X)),
            "h_action_grasp_and_ik": dict(
                tier="hard", hard="action", base="lid_off",
                failures=[f_grasp(X), f_ik("pick", "pot_lid", fid="ik_pick_lid")],
                challenge="the spoon slips on its first pick and the first lid pick is refused",
                route=with_ik(with_grasp(nom, X), "pick", "pot_lid")),
            "h_mixed_cookware_grasp": dict(
                tier="hard", hard="mixed", base="cookware_choice", failures=[f_grasp(X)],
                challenge="choose the pot over the nearer bowl and mug, and the spoon slips on the first pick",
                route=with_grasp(R("hard_pot_not_bowl"), X)),
            "h_dynamic_spoon_taken": dict(
                tier="hard", hard="dynamic", base="lid_off",
                failures=[f_move("resource", X, P("kitchen_cabinet_6/top", 3.70, 0.36, 90),
                                 ("collect", {"container": "handled_cooking_pot"}))],
                challenge="while the tomatoes go into the pot, someone takes the spoon to the wall cabinet",
                route=nom[:2] + [REC(S("search", object=X, region="living_room_0_0"))] + nom[2:]),
        }}


def T10(t, R):
    nom = R("nominal")
    X = "soda_can"
    in_mw = {X: P("kitchen_microwave/inside_floor", 4.5, 2.5)}
    mw_route = [S("navigate", destination="kitchen_microwave"), S("open", articulated="kitchen_microwave"),
                S("look", target="kitchen_microwave/inside_floor"), S("navigate", destination=X),
                S("pick", object=X), S("retreat", obstacle="kitchen_microwave", distance_m=0.3),
                S("close", articulated="kitchen_microwave"), S("navigate", destination="trash_can"),
                S("drop", object=X, container="trash_can")]
    mw_goal = {"all": t["goal"]["all"] + [["is_closed", "kitchen_microwave"]]}
    mw_instr = ("Someone left an empty soda can in the microwave. Throw it into the trash can and close the "
                "microwave again.", "有人把空汽水罐落在微波炉里了。请把它扔进垃圾桶，并把微波炉门关好。")
    return {
        "easy": ["can_on_island", "e2_from_dining_room"],
        "medium": ["can_in_dining_room", "far_can_far", "m_ik_can"],
        "hard": ["h_task_can_in_microwave", "h_action_ik_pick_and_drop", "h_mixed_microwave_ik", "h_dynamic_can_moved"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="can_on_island", start=START["dining"],
                                        challenge="the robot starts in the dining room",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_ik_can": dict(tier="medium", base="can_on_island", failures=[f_ik("pick", X)],
                             challenge="the first can pick is refused from its park", route=with_ik(nom, "pick", X)),
            "h_task_can_in_microwave": dict(
                tier="hard", hard="task", base="can_on_island", move=in_mw, goal=mw_goal, instruction=mw_instr[0],
                instruction_zh=mw_instr[1],
                failures=[f_initial("dependency", [["is_closed", "kitchen_microwave"],
                                                   ["in_appliance", X, "kitchen_microwave"]])],
                challenge="the can is inside the closed microwave: open it, take the can, close it, then trash it",
                route=mw_route),
            "h_action_ik_pick_and_drop": dict(
                tier="hard", hard="action", base="can_on_island",
                failures=[f_ik("pick", X), f_ik("drop", X, fid="ik_drop_can")],
                challenge="the first pick and the first drop over the trash can are both refused from their parks",
                route=with_ik(with_ik(nom, "pick", X), "drop", X)),
            "h_mixed_microwave_ik": dict(
                tier="hard", hard="mixed", base="can_on_island", move=in_mw, goal=mw_goal, instruction=mw_instr[0],
                instruction_zh=mw_instr[1],
                failures=[f_initial("dependency", [["is_closed", "kitchen_microwave"]]), f_ik("pick", X)],
                challenge="the can behind the microwave door, and the first pick inside is refused",
                route=with_ik(mw_route, "pick", X)),
            "h_dynamic_can_moved": dict(
                tier="hard", hard="dynamic", base="can_on_island",
                failures=[f_move("resource", X, P("dining_table_2/top", 3.7, 6.3),
                                 ("explore_room", {"room": "living_room_0_0"}))],
                challenge="after the robot looked around the living room, someone carries the can to the dining table",
                route=R("search_first")),
        }}


def T11(t, R):
    nom = R("nominal")
    X = "apple"
    return {
        "easy": ["fruits_on_table", "e2_from_kitchen"],
        "medium": ["basket_missing", "m_grasp_apple", "m_ik_basket"],
        "hard": ["basket_gone_bowl_there", "h_action_grasp_and_ik", "h_mixed_bowl_there_grasp", "h_dynamic_basket_taken"],
        "new": {
            "e2_from_kitchen": dict(tier="easy", base="fruits_on_table", start=START["kitchen"],
                                    challenge="the robot starts in the kitchen", route=nom),
            "m_grasp_apple": dict(tier="medium", base="fruits_on_table", failures=[f_grasp(X)],
                                  challenge="the apple slips on the first pick", route=with_grasp(nom, X)),
            "m_ik_basket": dict(tier="medium", base="fruits_on_table", failures=[f_ik("place", X)],
                                challenge="the first place into the basket is refused from its park",
                                route=with_ik(nom, "place", X)),
            "h_action_grasp_and_ik": dict(
                tier="hard", hard="action", base="fruits_on_table", failures=[f_grasp(X), f_ik("place", X)],
                challenge="the apple slips on the first pick and the first place into the basket is refused",
                route=with_ik(with_grasp(nom, X), "place", X)),
            "h_mixed_bowl_there_grasp": dict(
                tier="hard", hard="mixed", base="basket_gone_bowl_there", failures=[f_grasp(X)],
                challenge="the basket is gone and a bowl stands in its place (use the tray), and the apple slips",
                route=with_grasp(R("hard_tray_not_bowl"), X)),
            "h_dynamic_basket_taken": dict(
                tier="hard", hard="dynamic", base="fruits_on_table",
                failures=[f_move("resource", "fruit_basket", P("kitchen_cabinet_4/top", 1.4, 0.42),
                                 ("pick", {"object": X}))],
                challenge="while the robot picks the apple, someone takes the basket away: the serving tray on "
                          "the study desk is the stated substitute",
                route=R("hard_tray_not_bowl")),
        }}


def T12(t, R):
    nom = R("nominal")
    return {
        "easy": ["toys_out", "e2_from_kitchen"],
        "medium": ["duck_in_study", "m_grasp_car", "m_ik_duck_place"],
        "hard": ["toys_everywhere", "h_action_grasp_and_ik", "h_mixed_everywhere_ik", "h_dynamic_duck_taken"],
        "new": {
            "e2_from_kitchen": dict(tier="easy", base="toys_out", start=START["kitchen"],
                                    challenge="the robot starts in the kitchen", route=nom),
            "m_grasp_car": dict(tier="medium", base="toys_out", failures=[f_grasp("toy_car")],
                                challenge="the car slips on the first pick from the floor", route=with_grasp(nom, "toy_car")),
            "m_ik_duck_place": dict(tier="medium", base="toys_out", failures=[f_ik("place", "rubber_duck")],
                                    challenge="the first place of the duck into the basket is refused",
                                    route=with_ik(nom, "place", "rubber_duck")),
            "h_action_grasp_and_ik": dict(
                tier="hard", hard="action", base="toys_out",
                failures=[f_grasp("toy_car"), f_ik("place", "rubber_duck")],
                challenge="the car slips on its first pick, the duck's first place is refused",
                route=with_ik(with_grasp(nom, "toy_car"), "place", "rubber_duck")),
            "h_mixed_everywhere_ik": dict(
                tier="hard", hard="mixed", base="toys_everywhere", failures=[f_ik("pick", "toy_car")],
                challenge="allocate the toys by size (no basket) and the first car pick is refused",
                route=with_ik(R("hard_allocate_by_size"), "pick", "toy_car")),
            "h_dynamic_duck_taken": dict(
                tier="hard", hard="dynamic", base="toys_out",
                failures=[f_move("resource", "rubber_duck", P("desk_1/top", -0.95, -6.02, 128.7),
                                 ("explore_room", {"room": "living_room_0_0"}))],
                challenge="after the robot looked around the living room, the kid carries the duck to the study desk",
                route=R("explore_search_duck")),
        }}


def T13(t, R):
    nom = R("nominal")
    return {
        "easy": ["dishes_on_tv_stand", "e2_from_kitchen"],
        "medium": ["no_cup", "bowl_on_cabinet", "no_cup_bowl_on_cabinet"],
        "hard": ["no_cup_spoon_boxed_in", "h_action_ik_and_grasp", "h_mixed_boxed_in_ik", "h_dynamic_bowl_taken"],
        "new": {
            "e2_from_kitchen": dict(tier="easy", base="dishes_on_tv_stand", start=START["hall"],
                                    challenge="the robot starts in the hall by the kitchen",
                                    route=prefix(nom, S("navigate", destination="dining_table_2/top"))),
            "h_action_ik_and_grasp": dict(
                tier="hard", hard="action", base="dishes_on_tv_stand",
                failures=[f_ik("pick", "bowl"), f_ik("place", "cup", fid="ik_place_cup")],
                challenge="the first bowl pick and the first cup place are both refused from their parks",
                route=with_ik(with_ik(nom, "pick", "bowl"), "place", "cup")),
            "h_mixed_boxed_in_ik": dict(
                tier="hard", hard="mixed", base="no_cup_spoon_boxed_in", failures=[f_ik("pick", "spoon")],
                challenge="move the boxed-in setting (no cup: mug) and the first spoon pick is refused",
                route=with_ik(R("hard_move_the_setting"), "pick", "spoon")),
            "h_dynamic_bowl_taken": dict(
                tier="hard", hard="dynamic", base="dishes_on_tv_stand",
                failures=[f_move("resource", "bowl", P("kitchen_cabinet_6/top", 3.68, 0.36),
                                 ("look", {"target": "tv_stand_2/top"}))],
                challenge="after the robot saw the dishes, someone puts the bowl on the wall cabinet",
                route=R("explore_search_bowl")),
        }}


def T14(t, R):
    nom = R("nominal")
    X = "book_red"
    ready = {X: P("desk_1/top", -1.241, -5.769, 90)}
    ready_route = [s for s in nom if s["skill"] != "expose"]
    return {
        "easy": ["e1_book_ready", "e2_book_ready_far"],
        "medium": ["book_on_desk", "m_ik_place", "m_ik_pick"],
        "hard": ["shelf_taken", "h_action_ik_pick_and_place", "h_mixed_shelf_taken_ik", "h_dynamic_shelf_taken"],
        "new": {
            "e1_book_ready": dict(tier="easy", base="book_on_desk", move=ready, conditions=[],
                                  challenge="the book already overhangs the desk's front edge: pick it and shelve it",
                                  route=ready_route),
            "e2_book_ready_far": dict(tier="easy", base="book_on_desk", move=ready, conditions=[],
                                      start=START["hall"],
                                      challenge="the same chore starting in the hall by the kitchen", route=ready_route),
            "m_ik_place": dict(tier="medium", base="book_on_desk", failures=[f_ik("place", X)],
                               challenge="the first shelving place is refused from its park",
                               route=with_ik(R("fallback_expose"), "place", X)),
            "m_ik_pick": dict(tier="medium", base="book_on_desk", failures=[f_ik("expose", X)],
                              challenge="the first expose is refused from its park (re-park, then expose and pick)",
                              route=with_ik(nom, "expose", X)),
            "h_action_ik_pick_and_place": dict(
                tier="hard", hard="action", base="book_on_desk",
                failures=[f_ik("expose", X), f_ik("place", X, fid="ik_place_book")],
                challenge="the first expose and the first shelving place are both refused",
                route=with_ik(with_ik(nom, "expose", X), "place", X)),
            "h_mixed_shelf_taken_ik": dict(
                tier="hard", hard="mixed", base="shelf_taken", failures=[f_ik("pick", "mug_shelf")],
                challenge="make room on the shelf first, and the first mug pick is refused",
                route=with_ik(R("hard_make_room_first"), "pick", "mug_shelf")),
            "h_dynamic_shelf_taken": dict(
                tier="hard", hard="dynamic", base="book_on_desk",
                failures=[f_move("destination", "mug_shelf", P("bookcase_2/top", 0.86, -0.53),
                                 ("look", {"target": "desk_1/top"}), fid="destination_mug"),
                          f_move("destination", "shelf_blocker", P("bookcase_2/top", 1.13, -0.43, 90),
                                 ("look", {"target": "desk_1/top"}), fid="destination_duck")],
                challenge="while the robot is at the desk, someone puts a mug and the duck on the bookcase top: "
                          "move the mug to a legal place before shelving",
                route=R("hard_make_room_first")[:0] + R("nominal")[:2]
                + [REC(s) for s in R("hard_make_room_first")]),
        }}


def T15(t, R):
    nom = R("nominal")
    X = "paperback_book"
    blocked = {"wooden_block_a": {"support": None, "z": 0.886, "xy": [7.62, 1.65], "yaw_deg": 0.0}}
    clear_route = [S("look", target="kitchen_island/top"), S("navigate", destination="wooden_block_a"),
                   S("pick", object="wooden_block_a"),
                   S("place", object="wooden_block_a", receptacle="kitchen_island/top", hint_xy=[7.2, 1.85]),
                   S("navigate", destination=X), S("flip", object=X)]
    goal = {"all": t["goal"]["all"] + [["on", "wooden_block_a", "kitchen_island/top"]]}
    return {
        "easy": ["book_free", "e2_from_dining_room"],
        "medium": ["book_out_of_view", "m_ik_flip", "m_start_dining_away"],
        "hard": ["h_task_block_on_book", "h_action_ik_twice", "h_mixed_block_on_book_ik", "h_dynamic_book_moved"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="book_free", start=START["dining"],
                                        challenge="the robot starts in the dining room",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_ik_flip": dict(tier="medium", base="book_free", failures=[f_ik("flip", X)],
                              challenge="the first flip is refused from its park", route=with_ik(nom, "flip", X)),
            "m_start_dining_away": dict(tier="medium", base="book_free", start=[4.24, 5.12, 300.0],
                                        conditions=["start_elsewhere"],
                                        challenge="the robot starts in the dining room facing away: find the book",
                                        route=R("explore_search_book")),
            "h_task_block_on_book": dict(
                tier="hard", hard="task", base="book_free", move=blocked, goal=goal,
                failures=[f_initial("dependency", [["on_top_of", "wooden_block_a", X]])],
                challenge="a toy block lies on the book: take it off (and leave it on the island) before flipping",
                route=clear_route),
            "h_action_ik_twice": dict(
                tier="hard", hard="action", base="book_free",
                failures=[f_ik("flip", X), {**f_ik("flip", X, fid="ik_flip_again"), "after_fired": f"ik_flip_{X}",
                                            "trigger": {"skill": "flip", "args": {"object": X}, "nth": 2}}],
                challenge="the flip is refused from two parks in a row: re-park twice",
                route=with_ik(with_ik(nom, "flip", X), "flip", X)),
            "h_mixed_block_on_book_ik": dict(
                tier="hard", hard="mixed", base="book_free", move=blocked, goal=goal,
                failures=[f_initial("dependency", [["on_top_of", "wooden_block_a", X]]), f_ik("flip", X)],
                challenge="clear the block off the book, and the first flip is refused",
                route=with_ik(clear_route, "flip", X)),
            "h_dynamic_book_moved": dict(
                tier="hard", hard="dynamic", base="book_free",
                failures=[f_move("resource", X, P("kitchen_island/top", 7.9, 1.59, 90),
                                 ("look", {"target": "kitchen_island/top"}))],
                challenge="after the robot looked, someone slides the book along the island",
                route=nom[:1] + [REC(S("look", target=X))] + nom[1:]),
        }}


def T16(t, R):
    nom = R("nominal")
    X = "rolling_pin"
    behind = {"oatmeal": P("kitchen_island/top", 6.69, 1.70)}
    clear_route = [S("look", target="kitchen_island/top"), S("navigate", destination="oatmeal"),
                   S("pick", object="oatmeal"),
                   S("place", object="oatmeal", receptacle="kitchen_island/top", hint_xy=[7.3, 1.85]),
                   S("navigate", destination=X), S("roll", object=X, distance_m=0.12)]
    goal = {"all": t["goal"]["all"] + [["on", "oatmeal", "kitchen_island/top"], ["upright", "oatmeal"]]}
    return {
        "easy": ["pin_free", "e2_from_dining_room"],
        "medium": ["pin_out_of_view", "m_ik_roll", "m_start_dining_away"],
        "hard": ["h_task_bowl_behind", "h_action_ik_twice", "h_mixed_bowl_behind_ik", "h_dynamic_bowl_put_behind"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="pin_free", start=START["dining"],
                                        challenge="the robot starts in the dining room",
                                        route=prefix(nom, S("navigate", destination="kitchen_island/top"))),
            "m_ik_roll": dict(tier="medium", base="pin_free", failures=[f_ik("roll", X)],
                              challenge="the first roll is refused from its park", route=with_ik(nom, "roll", X)),
            "m_start_dining_away": dict(tier="medium", base="pin_free", start=[4.24, 5.12, 300.0],
                                        conditions=["start_elsewhere"],
                                        challenge="the robot starts in the dining room facing away: find the pin",
                                        route=R("explore_search_pin")),
            "h_task_bowl_behind": dict(
                tier="hard", hard="task", base="pin_free", move=behind, goal=goal,
                failures=[f_initial("dependency", [["on", "oatmeal", "kitchen_island/top"]])],
                challenge="the oatmeal bowl stands right behind the pin, in its rolling path: move it first",
                route=clear_route),
            "h_action_ik_twice": dict(
                tier="hard", hard="action", base="pin_free",
                failures=[f_ik("roll", X), {**f_ik("roll", X, fid="ik_roll_again"), "after_fired": f"ik_roll_{X}",
                                            "trigger": {"skill": "roll", "args": {"object": X}, "nth": 2}}],
                challenge="the roll is refused from two parks in a row",
                route=with_ik(with_ik(nom, "roll", X), "roll", X)),
            "h_mixed_bowl_behind_ik": dict(
                tier="hard", hard="mixed", base="pin_free", move=behind, goal=goal,
                failures=[f_initial("dependency", [["on", "oatmeal", "kitchen_island/top"]]), f_ik("pick", "oatmeal")],
                challenge="move the bowl out of the rolling path, and its first pick is refused",
                route=with_ik(clear_route, "pick", "oatmeal")),
            "h_dynamic_bowl_put_behind": dict(
                tier="hard", hard="dynamic", base="pin_free", goal=goal,
                move={"oatmeal": P("kitchen_island/top", 6.69, 1.83)},
                failures=[f_move("dependency", "oatmeal", P("kitchen_island/top", 6.69, 1.70),
                                 ("look", {"target": "kitchen_island/top"}))],
                challenge="after the robot looked, someone pushes the oatmeal bowl into the pin's rolling path",
                route=[REC(S("look", target="kitchen_island/top")), REC(S("look", target="oatmeal"))] + clear_route[1:]),
        }}


def T17(t, R):
    nom = R("nominal")
    lid_away = {"pot_lid": P("kitchen_cabinet_6/top", 3.335, 0.36)}
    fetch_lid = [S("navigate", destination="kitchen_cabinet_6/top"), S("look", target="kitchen_cabinet_6/top"),
                 S("navigate", destination="pot_lid"), S("pick", object="pot_lid"),
                 S("navigate", destination="kitchen_stove/top"),
                 S("place", object="pot_lid", receptacle="kitchen_stove/top", hint_xy=[8.715, 1.655])]
    lid_on = {"support": None, "z": 0.8591, "xy": [8.4096, 1.725], "yaw_deg": 0.0}
    return {
        "easy": ["lid_off", "e2_from_dining_room"],
        "medium": ["lid_on", "block_crowded", "lid_on_crowded"],
        "hard": ["h_task_lid_elsewhere", "h_action_ik_twice", "h_mixed_lid_elsewhere_ik", "h_dynamic_lid_put_on"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="lid_off", start=START["dining"],
                                        challenge="the robot starts in the dining room", route=nom),
            "h_task_lid_elsewhere": dict(
                tier="hard", hard="task", base="lid_off", move=lid_away,
                failures=[f_initial("resource", [["on", "pot_lid", "kitchen_cabinet_6/top"]])],
                challenge="the pot's lid was left on the wall cabinet: fetch it to the stove first, then hide",
                route=fetch_lid + nom),
            "h_action_ik_twice": dict(
                tier="hard", hard="action", base="lid_off",
                failures=[f_ik("hide", "wooden_block_b"),
                          {**f_ik("hide", "wooden_block_b", fid="ik_hide_again"), "after_fired": "ik_hide_wooden_block_b",
                           "trigger": {"skill": "hide", "args": {"object": "wooden_block_b"}, "nth": 2}}],
                challenge="the hide is refused from two parks in a row",
                route=with_ik(with_ik(nom, "hide", "wooden_block_b"), "hide", "wooden_block_b")),
            "h_mixed_lid_elsewhere_ik": dict(
                tier="hard", hard="mixed", base="lid_off", move=lid_away,
                failures=[f_initial("resource", [["on", "pot_lid", "kitchen_cabinet_6/top"]]), f_ik("pick", "pot_lid")],
                challenge="fetch the lid first, and its first pick is refused",
                route=with_ik(fetch_lid + nom, "pick", "pot_lid")),
            "h_dynamic_lid_put_on": dict(
                tier="hard", hard="dynamic", base="lid_off",
                failures=[{**f_move("dependency", "pot_lid", lid_on, ("look", {"target": "kitchen_island/top"})),
                           "event": {"type": "move_object", "object": "pot_lid", "to": lid_on,
                                     "onto": "handled_cooking_pot"}}],
                challenge="while the robot looks for the block, someone puts the lid back on the pot",
                route=R("fallback_uncover")),
        }}


def T18(t, R):
    nom = R("nominal")
    C = "kitchen_cabinet_6"
    two = {"bowl_inside_kitchen_cabinet": P("kitchen_cabinet_4/inside_shelf", 1.4, 0.42)}
    two_route = nom[:3] + [S("close", articulated=C), S("navigate", destination="kitchen_cabinet_4"),
                           S("open", articulated="kitchen_cabinet_4"), S("inspect", receptacle="kitchen_cabinet_4"),
                           S("close", articulated="kitchen_cabinet_4")]
    two_goal = {"all": t["goal"]["all"] + [["is_closed", "kitchen_cabinet_4"]]}
    two_instr = ("Grandma wants to know whether there is still a clean plate and bowl in the low wall cabinets for "
                 "dinner. Have a look inside and close the cabinet doors properly afterwards.",
                 "奶奶想知道矮墙柜里还有没有干净的盘子和碗做晚饭用。请看一下柜子里面，看完把柜门关好。")
    return {
        "easy": ["at_island", "e2_from_dining_room"],
        "medium": ["m_ik_open", "m_ik_close", "m_door_left_open"],
        "hard": ["h_task_two_cabinets", "h_action_ik_open_and_close", "h_mixed_two_cabinets_ik", "h_dynamic_door_closed"],
        "new": {
            "e2_from_dining_room": dict(tier="easy", base="at_island", start=START["dining"],
                                        challenge="the robot starts in the dining room", route=nom),
            "m_ik_open": dict(tier="medium", base="at_island", failures=[f_ik("open", C, key="articulated")],
                              challenge="the first open is refused from its park",
                              route=with_ik(nom, "open", C, key="articulated")),
            "m_ik_close": dict(tier="medium", base="at_island", failures=[f_ik("close", C, key="articulated")],
                               challenge="the first close is refused from its park",
                               route=with_ik(nom, "close", C, key="articulated")),
            "m_door_left_open": dict(
                tier="medium", base="at_island", conditions=["state_differs"],
                failures=[f_initial("dependency", [["is_open", C]],
                                    event={"type": "set_joint", "articulated": C, "value": "open"})],
                challenge="the door was left open: no need to open it (open would be refused), inspect and close",
                route=[nom[0]] + nom[2:]),
            "h_task_two_cabinets": dict(
                tier="hard", hard="task", base="at_island", move=two, goal=two_goal, instruction=two_instr[0],
                instruction_zh=two_instr[1],
                failures=[f_initial("resource", [["on", "bowl_inside_kitchen_cabinet", "kitchen_cabinet_4/inside_shelf"]])],
                challenge="the bowl is not in the first cabinet: check the other low cabinet too and close both",
                route=two_route),
            "h_action_ik_open_and_close": dict(
                tier="hard", hard="action", base="at_island",
                failures=[f_ik("open", C, key="articulated"), f_ik("close", C, key="articulated")],
                challenge="the first open and the first close are both refused from their parks",
                route=with_ik(with_ik(nom, "open", C, key="articulated"), "close", C, key="articulated")),
            "h_mixed_two_cabinets_ik": dict(
                tier="hard", hard="mixed", base="at_island", move=two, goal=two_goal, instruction=two_instr[0],
                instruction_zh=two_instr[1],
                failures=[f_initial("resource", [["on", "bowl_inside_kitchen_cabinet", "kitchen_cabinet_4/inside_shelf"]]),
                          f_ik("open", "kitchen_cabinet_4", key="articulated")],
                challenge="check both cabinets, and the second cabinet's first open is refused",
                route=with_ik(two_route, "open", "kitchen_cabinet_4", key="articulated")),
            "h_dynamic_door_closed": dict(
                tier="hard", hard="dynamic", base="at_island",
                failures=[f_joint("dependency", C, "closed", ("open", {"articulated": C}))],
                challenge="just after the robot opens the door, someone pushes it shut: inspecting needs it open",
                route=nom[:2] + [FAIL(nom[2]), REC(nom[1]), REC(nom[2])] + nom[3:]),
        }}


def T19(t, R):
    nom = R("nominal")
    return {
        "easy": ["bin_on_bookcase", "e2_from_kitchen"],
        "medium": ["m_can_in_dining_room", "m_grasp_can", "m_ik_cube"],
        "hard": ["lookalike_bin", "h_action_grasp_and_miss", "h_mixed_lookalike_ik", "h_dynamic_can_moved"],
        "new": {
            "e2_from_kitchen": dict(tier="easy", base="bin_on_bookcase", start=START["kitchen"],
                                    challenge="the robot starts in the kitchen", route=nom),
            "m_can_in_dining_room": dict(
                tier="medium", base="bin_on_bookcase", conditions=["not_in_view"],
                move={"soda_can": P("dining_table_2/top", 3.7, 6.3)},
                challenge="the can was left on the dining table, out of view: search it",
                route=R("hard_instructed_bin")),
            "m_grasp_can": dict(tier="medium", base="bin_on_bookcase", failures=[f_grasp("soda_can")],
                                challenge="the can slips on the first pick", route=with_grasp(nom, "soda_can")),
            "m_ik_cube": dict(tier="medium", base="bin_on_bookcase", failures=[f_ik("pick", "foam_cube")],
                              challenge="the first floor pick of the cube is refused from its park",
                              route=with_ik(nom, "pick", "foam_cube")),
            "h_action_grasp_and_miss": dict(
                tier="hard", hard="action", base="bin_on_bookcase",
                failures=[f_grasp("foam_cube"),
                          f_place_miss("soda_can", P("bookcase_2/top", 0.80, -0.43),
                                       [["inside", "soda_can", "wide_storage_bin"]], skill="drop")],
                challenge="the can's first drop misses the bin, the cube slips on its first pick",
                route=with_grasp(with_place_miss(nom, "soda_can", skill="drop"), "foam_cube")),
            "h_mixed_lookalike_ik": dict(
                tier="hard", hard="mixed", base="lookalike_bin", failures=[f_ik("pick", "foam_cube")],
                challenge="route both items past the look-alike bin to the instructed one, and the first cube pick "
                          "is refused",
                route=with_ik(R("hard_instructed_bin"), "pick", "foam_cube")),
            "h_dynamic_can_moved": dict(
                tier="hard", hard="dynamic", base="bin_on_bookcase",
                failures=[f_move("resource", "soda_can", P("dining_table_2/top", 3.7, 6.3),
                                 ("explore_room", {"room": "living_room_0_0"}))],
                challenge="after the robot looked around the living room, someone takes the can to the dining table",
                route=R("hard_instructed_bin")),
        }}


def T20(t, R):
    nom = R("nominal")
    X = "juice_bottle"
    return {
        "easy": ["bottle_on_cabinet", "e2_from_bedroom_hall"],
        "medium": ["m_ik_pick", "m_ik_place", "m_bottle_on_tv_stand"],
        "hard": ["table_full", "h_action_ik_pick_and_place", "h_mixed_table_full_ik", "h_dynamic_bottle_taken"],
        "new": {
            "e2_from_bedroom_hall": dict(tier="easy", base="bottle_on_cabinet", start=START["kitchen"],
                                         challenge="the robot starts in the kitchen", route=nom),
            "m_ik_pick": dict(tier="medium", base="bottle_on_cabinet", failures=[f_ik("pick", X)],
                              challenge="the first bottle pick is refused from its park", route=with_ik(nom, "pick", X)),
            "m_ik_place": dict(tier="medium", base="bottle_on_cabinet", failures=[f_ik("place", X)],
                               challenge="the first place on the table is refused from its park",
                               route=with_ik(nom, "place", X)),
            "m_bottle_on_tv_stand": dict(
                tier="medium", base="bottle_on_cabinet", conditions=["not_in_view"], move={X: P("tv_stand_2/top", 8.155, 0.366)},
                challenge="the bottle is on the TV stand in the living room, out of the first view: search it",
                route=[S("search", object=X, region="living_room_0_0")] + nom[2:]),
            "h_action_ik_pick_and_place": dict(
                tier="hard", hard="action", base="bottle_on_cabinet",
                failures=[f_ik("pick", X), f_ik("place", X, fid="ik_place_bottle")],
                challenge="the first pick and the first place are both refused from their parks",
                route=with_ik(with_ik(nom, "pick", X), "place", X)),
            "h_mixed_table_full_ik": dict(
                tier="hard", hard="mixed", base="table_full", failures=[f_ik("pick", "party_bowl_1")],
                challenge="make room on the party table, and the first bowl pick is refused",
                route=with_ik(R("hard_make_room_first"), "pick", "party_bowl_1")),
            "h_dynamic_bottle_taken": dict(
                tier="hard", hard="dynamic", base="bottle_on_cabinet",
                failures=[f_move("resource", X, P("tv_stand_2/top", 8.155, 0.366),
                                 ("look", {"target": "kitchen_cabinet_6/top"}))],
                challenge="just after the robot saw the bottle, someone takes it to the TV stand",
                route=nom[:2] + [REC(S("search", object=X, region="living_room_0_0"))] + nom[2:]),
        }}


DESIGNS = {"T01_book_to_dining_table": T01, "T02_stack_blocks": T02, "T03_utensils_one_container": T03,
           "T04_cup_or_mug_to_cabinet": T04, "T05_pen_or_pencil_to_desk": T05, "T06_block_destination_occupied": T06,
           "T07_heat_oatmeal": T07, "T08_wipe_island": T08, "T09_tomato_soup": T09, "T10_trash_the_can": T10,
           "T11_collect_fruits": T11, "T12_tidy_toys": T12, "T13_breakfast_setup": T13, "T14_shelve_the_book": T14,
           "T15_book_face_up": T15, "T16_rolling_pin_at_edge": T16, "T17_hide_and_seek_block": T17,
           "T18_check_cabinet_dishes": T18, "T19_recycling": T19, "T20_juice_back_to_table": T20}

V4_CONSTRAINT = {      # (kind, check atoms that hold at the start) of each v4 Hard's environment
    "table_set": ("destination", [["on", "bowl_side_table", "dining_table_2/top"], ["on", "plate_counter_a", "dining_table_2/top"]]),
    "edge_base": ("dependency", [["on", "wooden_block_a", "kitchen_island/top"]]),
    "three_containers": ("capacity", [["on", "small_storage_bin", "tv_stand_2/top"]]),
    "display_hidden": ("destination", [["on", "juice_bottle", "kitchen_cabinet_6/top"]]),
    "microwave_holds_pot": ("resource", [["in_appliance", "handled_cooking_pot", "kitchen_microwave"]]),
    "island_cluttered": ("destination", [["on", "soda_can", "kitchen_island/top"], ["on", "wooden_block_a", "kitchen_island/top"]]),
    "cookware_choice": ("resource", [["on", "bowl_kitchen_cabinet", "kitchen_island/top"]]),
    "basket_gone_bowl_there": ("resource", [["on", "bowl_kitchen_cabinet", "bookcase_2/top"]]),
    "toys_everywhere": ("capacity", [["on", "toy_bin_small", "bookcase_2/top"]]),
    "no_cup_spoon_boxed_in": ("destination", [["on", "clutter_cereal_a", "dining_table_2/top"]]),
    "shelf_taken": ("destination", [["on", "mug_shelf", "bookcase_2/top"]]),
    "lookalike_bin": ("resource", [["inside", "toy_block_in_bin_1", "toy_storage_bin"]]),
    "table_full": ("destination", [["on", "buffet_tray_1", "dining_table_2/top"]]),
}
HARD_FROM_V4 = "task"           # every v4 Hard is a task-level replanning variant (initial constraint)
OVERLAY = ("move", "add", "remove", "start", "thermal_sources", "thermal_override", "vary", "conditions")
FIELDS = OVERLAY + ("goal", "instruction", "instruction_zh", "watch", "failures", "may_end_on_floor")


# ----------------------------------------------------------------- assembly
def build_task(t: dict) -> dict:
    t = copy.deepcopy(t)

    def R(name):
        return copy.deepcopy(t["routes"][name]["steps"])

    d = design(t, R)
    formal = {k: list(d[k]) for k in ("easy", "medium", "hard")}
    for vid, spec in d["new"].items():
        if vid in t["variants"]:
            raise ValueError(f"{t['task_id']}: {vid} exists in v3")
        base = copy.deepcopy(t["variants"][spec["base"]])
        v = {k: base[k] for k in OVERLAY if k in base and k != "vary"}
        if "move" in spec:
            v["move"] = {**v.get("move", {}), **copy.deepcopy(spec["move"])}
        if "remove" in spec:
            v["remove"] = sorted(set(v.get("remove", [])) | set(spec["remove"]))
        for k in FIELDS:
            if k in spec and k not in ("move", "remove"):
                v[k] = copy.deepcopy(spec[k])
        for k in ("goal", "instruction", "instruction_zh", "watch", "handle_objects"):
            if k in base and k not in v:
                v[k] = copy.deepcopy(base[k])          # a v4 Hard's own goal / instruction carries over
        v["vary"] = copy.deepcopy(VARY)
        v["difficulty"] = spec["tier"]
        v["since"] = "v5"
        v["note"] = spec["challenge"]
        v["v5"] = {"tier": spec["tier"], "challenge": spec["challenge"], "derived_from": spec["base"]}
        if spec["tier"] == "hard":
            v["v5"]["hard_category"] = spec["hard"]
        if spec.get("failures"):
            v["failures"] = copy.deepcopy(spec["failures"])
        if spec["tier"] == "hard" and spec["base"] in V4_CONSTRAINT:
            kind, check = V4_CONSTRAINT[spec["base"]]       # the inherited v4 environment, verified at the start
            v["failures"] = [f_initial(kind, check, fid=f"{kind}_v4_{spec['base']}")] + v.get("failures", [])
        rname = f"v5_{vid}"
        t["routes"][rname] = {"steps": spec["route"], "kind": "v5_oracle", "variant": vid}
        t["oracle"][vid] = rname
        t["variants"][vid] = v
    # meta for the existing variants of the formal set
    for tier, ids in formal.items():
        for vid in ids:
            v = t["variants"][vid]
            if v.get("since") == "v5":
                continue
            meta = {"tier": tier, "challenge": v.get("note", ""), "derived_from": vid, "existing": True}
            if tier == "hard":
                meta["hard_category"] = HARD_FROM_V4
            v["v5"] = meta
            if difficulty(v) != tier:
                raise ValueError(f"{t['task_id']}/{vid}: v3 tier {difficulty(v)} != formal {tier}")
    t["v5_formal"] = formal
    t["v5_supplementary"] = sorted(set(t["variants"]) - {x for ids in formal.values() for x in ids})
    t["benchmark_version"] = "v5"
    return t


def difficulty(v):
    from episode.catalog import difficulty_of
    return difficulty_of(v)


def build() -> dict:
    doc = json.loads(V3.read_text())
    tasks = [build_task(t) for t in doc["tasks"] if t["task_id"] in DESIGNS]
    reg = dict(doc["condition_registry"])
    reg["state_differs"] = {"type": "state_precondition", "decision": "alternative",
                            "meaning": "the world is already in a different state than the usual plan expects"}
    return {"schema_version": 5, "benchmark_version": "v5", "kind": "zenobench_benchmark_tasks",
            "note": "Source: python benchmark/v5/define_tasks_v5.py (reads benchmark/v3/tasks.json).",
            "eval_seeds": doc["eval_seeds"], "condition_registry": reg,
            "tiers": {"easy": 2, "medium": 3, "hard": 4},
            "hard_categories": ["task", "action", "mixed", "dynamic"], "tasks": tasks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit("benchmark/v5/tasks.json is out of date: python benchmark/v5/define_tasks_v5.py")
        print("up to date")
        return
    OUT.write_text(text)
    n = sum(len(ids) for t in doc["tasks"] for ids in t["v5_formal"].values())
    print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['tasks'])} tasks, {n} formal variants")


if __name__ == "__main__":
    main()
