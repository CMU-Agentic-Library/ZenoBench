"""Benchmark v4 Hard variants: task-level replanning (ZenoBench Task-Level Replanning report, 2026-10-24).

v4 is a label, not a new catalog: the variants below are added to benchmark/v3/tasks.json in place
(define_tasks_v3.build), so the task ids, the catalog path and every existing variant stay as they were.
The old v3 Hard variants (two local conditions) are relabelled Medium there (``"difficulty": "medium"``,
``"v3_difficulty": "hard"``); their configurations and hashes do not change.

A v4 Hard variant asks for a change of the task graph, not for one more local repair:

* ``decompose``: split the task / allocate resources by capacity, location, several goals
  (T03, T11, T12, T19);
* ``insert``: a missing precondition becomes a new subgoal with its dependency
  (T01, T02, T06, T08, T13, T14, T20);
* ``replace``: the original strategy is infeasible; another subgraph or order (T07, T09).

Each variant may carry its own ``instruction`` / ``instruction_zh`` (the report's Proposed Hard
instruction) and ``goal`` (episode.catalog.resolve_task); the instruction never states the solution,
the constraint has to be observed or met through feedback.  The goal accepts every
instruction-compliant strategy and rejects the shortcuts the instruction rules out (clearing a whole
table, a container the instruction does not allow, a layout that is not restored).

Every Hard variant has an oracle route (``hard_*``), a scripted chain that shows one complete
strategy is physically feasible on the variant's configuration.  Routes of kind ``negative`` document
the plan a planner gets wrong (they are expected to end with the goal false) and are never counted.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from define_tasks import (BOOKCASE, CAB, CAB2_TOP, CAB_TOP, DESK, DINING, ISLAND, MW, MW_FLOOR, NO_MW, POT,  # noqa: E402,F401
                          STOVE_TOP, TV, S, at)

VERSION = "v4"
HALL = "living_room_0_0"
BEDROOM = "bedroom_0_1"

# tag -> (condition type, decision, meaning); decision = the task-graph change the condition requires
CONDITIONS = {
    "surface_cluttered": ("occupied_workspace", "insert",
                          "objects cover every free strip of the surface: move one aside, do the work, put it back"),
    "cookware_off_burner": ("cookware_placement", "replace",
                            "the pot stands off the stove: bring it to a burner before (or instead of) cooking in place"),
    "spot_quality": ("destination_constraint", "insert",
                     "the destination has free spots that violate the instruction (crowding the place settings, "
                     "hidden, at the edge): choose the spot from what is observed"),
    "unstable_base": ("support_stability", "insert",
                      "the obvious base lies at the edge: stack on the other one or move it in first"),
    "joint_capacity": ("container_capacity", "decompose",
                       "several containers, only one holds every item together: allocate the items jointly"),
    "appliance_and_burner": ("appliance_failure", "replace",
                             "the microwave does not heat and the free burner is taken: switch appliance and clear "
                             "the burner first"),
    "no_cup": ("object_absent", "alternative", "the requested object does not exist; the allowed substitute is used"),
    "destination_full": ("destination_occupied", "insert",
                         "the destination has no room left: move what occupies it to a legal place, then put the "
                         "object there"),
    "decoy_destination": ("destination_identity", "decompose",
                          "a container that the instruction does not allow stands where the named one should be"),
}


def tag(variant):
    tags = variant.get("conditions", [])
    variant["condition_types"] = [CONDITIONS[c][0] for c in tags]
    variant["decisions"] = sorted({CONDITIONS[c][1] for c in tags})


START_VARY = {"dx": 0.10, "dyaw": 10, "step": 0.05, "step_deg": 5}


def vary(*groups, start=START_VARY):
    out = {"groups": [g for g in groups if g]}
    if start:
        out["start"] = start
    return out


def group(names, dx=0.0, dy=0.0, dyaw=0.0, step=0.01, step_deg=5):
    return {"names": list(names), "dx": dx, "dy": dy, "dyaw": dyaw, "step": step, "step_deg": step_deg}


def hard(note, conditions, instruction=None, instruction_zh=None, goal=None, **physical):
    """A v4 Hard variant: explicit tier, v4 label, optional instruction / goal of its own."""
    v = {"note": note, "difficulty": "hard", "since": VERSION, "conditions": list(conditions)}
    if instruction:
        v["instruction"], v["instruction_zh"] = instruction, instruction_zh
    if goal:
        v["goal"] = goal
    v.update(physical)
    v.setdefault("move", {})
    tag(v)
    return v


# task id -> {"variants": {name: variant}, "routes": {name: route}, "oracle": {variant: route},
#             "vary": {variant: vary}, "not_adopted": [...]}
HARD = {}

# ----------------------------------------------------------------- T08 wipe the island (insert: clear, wipe, restore)
# after cooking the island is cluttered along both long strips (the robot wipes from the front or from the back,
# 8 cm in from the edge it stands at): the gaps between the objects are 0.21-0.29 m, a 30 cm strip with 2 cm
# clearance needs 0.40 m, so wipe refuses ("no free strip near the robot") wherever the robot stands (both ends are
# blocked too: the rolling pin and the oatmeal bowl at the west end, the stove at the east end).  Taking one object
# off the island opens a strip; restore puts it back on its own spot afterwards (restore needs it on another support)
T08_FRONT = {"rolling_pin": at(ISLAND, 6.75, 1.62, 0), "wooden_block_a": at(ISLAND, 7.10, 1.62),
             "soda_can": at(ISLAND, 7.45, 1.62), "wooden_block_b": at(ISLAND, 7.80, 1.62),
             "mug": at(ISLAND, 8.05, 1.62)}
T08_BACK = {"oatmeal": at(ISLAND, 6.75, 1.88), "paperback_book": at(ISLAND, 7.15, 1.88, 0),
            "juice_bottle": at(ISLAND, 7.50, 1.88), "breakfast_spoon": at(ISLAND, 7.85, 1.88, 0)}
T08_LINE = {**T08_FRONT, **T08_BACK}
T08_GOAL = {"all": [["wiped", ISLAND], ["on", "kitchen_sponge", ISLAND], ["hand_empty", "right"],
                    *[["near_start", n, 0.06] for n in T08_LINE],
                    *[["upright", n] for n in ("soda_can", "mug", "juice_bottle", "oatmeal")]]}
_t08_tail = [S("navigate", destination="kitchen_sponge"), S("pick", object="kitchen_sponge"),
             S("wipe", surface=ISLAND, tool="kitchen_sponge"),
             S("place", object="kitchen_sponge", receptacle=ISLAND)]
_t08_aside = [S("navigate", destination="wooden_block_a", role="insert"),
              S("pick", object="wooden_block_a", role="insert"), S("navigate", destination=TV, role="insert"),
              S("place", object="wooden_block_a", receptacle=TV, role="insert")]
_t08_wipe = [S("navigate", destination="kitchen_sponge"), S("pick", object="kitchen_sponge"),
             S("approach", target=ISLAND, role="insert"), S("wipe", surface=ISLAND, tool="kitchen_sponge"),
             S("place", object="kitchen_sponge", receptacle=ISLAND), S("restore", object="wooden_block_a",
                                                                       role="restore")]
HARD["T08_wipe_island"] = {
    "variants": {"island_cluttered": hard(
        "after cooking the island is cluttered along both long strips (pin, two blocks, can and mug in front; bowl, "
        "book, bottle and spoon behind); the sponge lies at its spot behind them", ["surface_cluttered"],
        instruction="Wipe the kitchen island clean with the sponge. Deal with the things standing on it properly "
                    "and put them back as they were, then leave the sponge on the island.",
        instruction_zh="用海绵擦净厨房岛台，妥善处理并恢复台面物品，最后把海绵留在岛台。",
        goal=T08_GOAL, watch=["kitchen_sponge", *T08_LINE],
        move=dict(T08_LINE))},            # the sponge stays at its own spot (8.16, 1.82)
    "routes": {
        "hard_clear_wipe_restore": {
            "kind": "fallback", "variants": ["island_cluttered"],
            "recovery": "wipe refused (no free strip) -> put the sponge down, move one block to the TV stand -> "
                        "wipe -> put the block back",
            "steps": [S("look", target=ISLAND), *_t08_tail[:2],
                      S("wipe", "fail", "failure", surface=ISLAND, tool="kitchen_sponge"),
                      S("place", object="kitchen_sponge", receptacle=ISLAND, hint_xy=[8.16, 1.82]),
                      *_t08_aside, *_t08_wipe]},
        "hard_proactive": {
            "kind": "alternative", "variants": ["island_cluttered"],
            "recovery": "the clutter is seen first: move one block to the TV stand, wipe, put it back",
            "steps": [S("look", target=ISLAND), *_t08_aside, *_t08_wipe]}},
    "oracle": {"island_cluttered": "hard_proactive"},
    "vary": {"island_cluttered": vary()},
}

# ----------------------------------------------------------------- T09 tomato soup (replace / reorder: pot to the stove first)
# the pot's handle points to the robot side (yaw 180)
T09_POT_OFF = {"handled_cooking_pot": at(ISLAND, 7.20, 1.78, 180), "pot_lid": at(STOVE_TOP, 8.715, 1.655)}
_t09_soup = [S("navigate", destination="breakfast_spoon"), S("pick", object="breakfast_spoon"),
             S("navigate", destination=POT), S("stir", container=POT, tool="breakfast_spoon"),
             S("navigate", destination=ISLAND), S("place", object="breakfast_spoon", receptacle=ISLAND),
             S("navigate", destination="pot_lid"), S("pick", object="pot_lid"), S("navigate", destination=POT),
             S("cover", container=POT, lid="pot_lid"), S("navigate", destination="kitchen_stove"),
             S("heat", food="cherry_tomato_1", appliance="kitchen_stove", temp_c=60)]
HARD["T09_tomato_soup"] = {
    "variants": {"pot_off_stove": hard(
        "the empty pot stands on the island next to the tomatoes, its lid lies on the stove", ["cookware_off_burner"],
        instruction="Make tomato soup for lunch in a suitable pot: put the cherry tomatoes in, stir them, cover the "
                    "pot and heat the soup to 60 C, then turn the stove off.",
        instruction_zh="请用合适锅具完成番茄入锅、搅拌、盖锅、加热至60°C和关火。",
        remove=["wooden_block_a", "wooden_block_b"], move=dict(T09_POT_OFF),
        handle_objects=[POT])},              # the pot's handle collider (pick grasp=handle)
    "routes": {
        "hard_pot_to_stove": {
            "kind": "alternative", "variants": ["pot_off_stove"],
            "recovery": "the pot is not on the stove: carry it to a burner first, then cook in it",
            "steps": [S("look", target=ISLAND), S("navigate", destination=POT, role="insert"),
                      S("pick", object=POT, grasp="handle", role="insert"),
                      S("navigate", destination=STOVE_TOP, role="insert"),
                      # from the navigate pose the hand hanging the pot by its handle had no IK above the burner;
                      # after approach the place ran, but at (8.41, 1.64) the pot's rim caught the island's edge
                      # (2 cm west of the stove) and it came to rest on it (s10): 4 cm further east, still on the
                      # burner (on_burner: 13 cm)
                      S("approach", target=STOVE_TOP, role="insert"),
                      S("place", object=POT, receptacle=STOVE_TOP, hint_xy=[8.45, 1.66], role="insert"),
                      S("navigate", destination=ISLAND), S("look", target=ISLAND),
                      S("collect", objects=["cherry_tomato_1", "cherry_tomato_2"], container=POT), *_t09_soup]},
        "probe_place_pot": {
            "kind": "diagnostic", "variants": ["pot_off_stove"],
            "note": "placement attempts of the handle-held pot on the stove",
            "steps": [S("look", target=ISLAND), S("navigate", destination=POT), S("pick", object=POT, grasp="handle"),
                      S("navigate", destination=STOVE_TOP),
                      S("place", "fail", object=POT, receptacle=STOVE_TOP, hint_xy=[8.41, 1.64]),
                      S("place", "fail", object=POT, receptacle=STOVE_TOP),
                      S("approach", "fail", target=STOVE_TOP),
                      S("place", "fail", object=POT, receptacle=STOVE_TOP, hint_xy=[8.41, 1.64]),
                      S("place", "fail", object=POT, receptacle=STOVE_TOP, hint_xy=[8.70, 1.725])]}},
    "oracle": {"pot_off_stove": "hard_pot_to_stove"},
    "vary": {"pot_off_stove": vary()},
}


# ----------------------------------------------------------------- T01 book to the dining table (choose the spot)
# the table is set along its east edge (the side the robot parks at, 4.33 / 6.25): the free edge slots between the
# settings fit the 18 cm book with 2-3 cm to spare except one, between the cup and the second plate (36 cm); place's
# own choice (the slot nearest the robot) crowds a setting, the reading spot has to be chosen
T01_SET = {"bowl_side_table": at(DINING, 3.70, 5.65), "plate_counter_a": at(DINING, 3.66, 6.093),
           "cup_side_table": at(DINING, 3.70, 6.502), "plate_counter_b": at(DINING, 3.66, 7.041),
           "clutter_cereal_a": at(DINING, 3.70, 7.46), "mug_dining_cabinet": at(DINING, 3.70, 7.84),
           "spoon_target_table": at(DINING, 3.38, 7.04), "clutter_cereal_b": at(DINING, 3.20, 7.60)}
T01_WARE = list(T01_SET)
T01_GOAL = {"all": [["on", "paperback_book", DINING], ["clear_of", "paperback_book", T01_WARE, 0.05],
                    *[["near_start", n, 0.03] for n in T01_WARE],
                    *[["upright", n] for n in ("cup_side_table", "mug_dining_cabinet", "clutter_cereal_a",
                                               "clutter_cereal_b")], ["hand_empty", "right"]]}
_t01_carry = [S("look", target=ISLAND), S("navigate", destination="paperback_book"),
              S("approach", target="paperback_book"), S("pick", object="paperback_book"),
              S("navigate", destination=DINING), S("look", target=DINING)]
HARD["T01_book_to_dining_table"] = {
    "variants": {"table_set": hard(
        "the dining table is set for breakfast along its east edge; one free edge slot leaves room around the book",
        ["spot_quality"],
        instruction="Bring the paperback from the island to the dining table and put it where it is easy to read "
                    "without getting in the way of the tableware.",
        instruction_zh="请把岛台上的书送到餐桌上，放在方便阅读、又不影响其他餐具的位置。",
        goal=T01_GOAL, watch=["paperback_book", *T01_WARE],
        move={"paperback_book": at(ISLAND, 7.62, 1.548, 90), **T01_SET})},
    "routes": {
        "hard_reading_spot": {"kind": "alternative", "variants": ["table_set"],
                              "recovery": "the table is set: put the book in the one slot that keeps clear of the "
                                          "settings (hint between the cup and the second plate)",
                              "steps": [*_t01_carry, S("place", object="paperback_book", receptacle=DINING,
                                                       hint_xy=[3.72, 6.737], role="alternative")]},
        "naive_nearest_slot": {"kind": "negative", "variants": ["table_set"],
                               "note": "place's own choice: the slot nearest the robot, wedged between two settings",
                               "steps": [*_t01_carry, S("place", object="paperback_book", receptacle=DINING)]}},
    "oracle": {"table_set": "hard_reading_spot"},
    "vary": {"table_set": vary()},
}

# ----------------------------------------------------------------- T02 stack the blocks (choose a stable base)
# (the juice bottle next to block A was swept off the island by the arm picking A, s10: a physical hazard, not a
# planning one, so block A stands alone at the edge)
T02_EDGE = {"wooden_block_a": at(ISLAND, 7.30, 1.535),            # 5 mm over the island's front edge
            "wooden_block_b": at(ISLAND, 7.00, 1.75)}             # in the open
T02_GOAL = {"any": [[["on_top_of", "wooden_block_b", "wooden_block_a"], ["away_from_edge", "wooden_block_a", 0.05]],
                    [["on_top_of", "wooden_block_a", "wooden_block_b"], ["away_from_edge", "wooden_block_b", 0.05]]],
            "all": [["hand_empty", "right"]]}
HARD["T02_stack_blocks"] = {
    "variants": {"edge_base": hard(
        "block A sits at the island's front edge (5 mm over it), block B in the open",
        ["unstable_base"],
        instruction="Stack the two wooden blocks steadily somewhere suitable on the island, without knocking "
                    "anything over.",
        instruction_zh="请把两块木积木稳稳叠在岛台合适位置，不要碰倒其他物品。",
        goal=T02_GOAL, watch=["wooden_block_a", "wooden_block_b", "rolling_pin", "oatmeal"],
        move=dict(T02_EDGE))},
    "routes": {
        "hard_stack_on_open_block": {
            "kind": "alternative", "variants": ["edge_base"],
            "recovery": "block A is at the edge: take it and stack it on block B in the open",
            "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_a"),
                      S("pick", object="wooden_block_a", role="alternative"),
                      S("navigate", destination="wooden_block_b"),
                      S("approach", target="wooden_block_b"),
                      S("stack", object="wooden_block_a", base="wooden_block_b", role="alternative")]},
        "naive_stack_on_edge_block": {
            "kind": "negative", "variants": ["edge_base"], "note": "the Easy plan: B onto A at the edge",
            "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_b"),
                      S("pick", object="wooden_block_b"),
                      S("navigate", destination="wooden_block_a"), S("approach", target="wooden_block_a"),
                      S("stack", object="wooden_block_b", base="wooden_block_a")]}},
    "oracle": {"edge_base": "hard_stack_on_open_block"},
    "vary": {"edge_base": vary()},
}

# ----------------------------------------------------------------- T03 utensils in one container (joint capacity)
SMALL_BIN = "small_storage_bin"
T03_BIN = "wide_storage_bin"
HARD["T03_utensils_one_container"] = {
    "variants": {"three_containers": hard(
        "the mug and a small storage bin (22 x 17 cm) on the island next to the utensils, the wide storage bin on "
        "the TV stand: the spoon fits the small bin, the 22 cm rolling pin only the wide one", ["joint_capacity"],
        instruction="Baking is done. Put the rolling pin and the spoon away together in one suitable container, "
                    "both of them completely inside.",
        instruction_zh="烘焙结束，请把擀面杖和勺子一起收进同一个合适容器，确保两件都完整放入。",
        goal={"any": [[["inside", "rolling_pin", T03_BIN], ["inside", "breakfast_spoon", T03_BIN]],
                      [["inside", "rolling_pin", "mug"], ["inside", "breakfast_spoon", "mug"]],
                      [["inside", "rolling_pin", SMALL_BIN], ["inside", "breakfast_spoon", SMALL_BIN]]],
              "all": [["hand_empty", "right"]]},
        watch=["rolling_pin", "breakfast_spoon", "mug", T03_BIN, SMALL_BIN],
        add={SMALL_BIN: {"asset": "small_storage_bin", **at(ISLAND, 7.10, 1.80)}})},
    "routes": {
        "hard_measure_then_wide_bin": {
            "kind": "alternative", "variants": ["three_containers"],
            "recovery": "measure the containers: only the wide bin takes the 22 cm pin, so both go there",
            "steps": [S("look", target=ISLAND), S("look", target=TV), S("measure", object="mug"),
                      S("measure", object=SMALL_BIN), S("measure", object="rolling_pin"),
                      S("navigate", destination="breakfast_spoon"), S("pick", object="breakfast_spoon"),
                      S("navigate", destination=T03_BIN), S("approach", target=T03_BIN),
                      S("drop", object="breakfast_spoon", container=T03_BIN, role="alternative"),
                      S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"),
                      S("navigate", destination=T03_BIN), S("approach", target=T03_BIN),
                      S("place", object="rolling_pin", receptacle=T03_BIN, role="alternative")]},
        "naive_spoon_in_small_bin": {
            "kind": "negative", "variants": ["three_containers"],
            "note": "greedy per item: the spoon into the nearest bin that fits it, then the pin does not fit there",
            "steps": [S("look", target=ISLAND), S("navigate", destination="breakfast_spoon"),
                      S("pick", object="breakfast_spoon"), S("navigate", destination=SMALL_BIN),
                      S("drop", object="breakfast_spoon", container=SMALL_BIN),
                      S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"),
                      S("navigate", destination=SMALL_BIN), S("place", object="rolling_pin", receptacle=SMALL_BIN)]}},
    "oracle": {"three_containers": "hard_measure_then_wide_bin"},
    "vary": {"three_containers": vary()},
}

# ----------------------------------------------------------------- T06 display the block (visible, steady)
# two cereal boxes and the juice bottle line the wall cabinet's front: its only free spot is behind them, out of sight
T06_CAB = {"clutter_cereal_a": at(CAB_TOP, 3.30, 0.44), "clutter_cereal_b": at(CAB_TOP, 3.50, 0.44),
           "juice_bottle": at(CAB_TOP, 3.70, 0.45)}
T06_GOAL = {"any": [[["on", b, sup], ["front_visible", b], ["away_from_edge", b, 0.02]]
                    for b in ("wooden_block_a", "wooden_block_b") for sup in (CAB_TOP, TV)],
            "all": [*[["upright", n] for n in T06_CAB], ["hand_empty", "right"]]}
HARD["T06_block_destination_occupied"] = {
    "variants": {"display_hidden": hard(
        "two cereal boxes and the juice bottle stand along the wall cabinet's front; the free spot behind them is "
        "hidden from the room, the TV stand is open", ["spot_quality"],
        instruction="Put the toy block on display on the low wall cabinet or the TV stand, in a spot where it can "
                    "be seen clearly and stands steadily.",
        instruction_zh="请把积木展示在靠墙矮柜或电视柜上一个醒目、稳定的位置。",
        goal=T06_GOAL, watch=["wooden_block_a", "wooden_block_b", *T06_CAB], move=dict(T06_CAB))},
    "routes": {
        "hard_open_display": {"kind": "alternative", "variants": ["display_hidden"],
                              "recovery": "the cabinet's free spot is hidden behind the boxes: the TV stand",
                              "steps": [S("look", target=ISLAND), S("look", target=CAB_TOP),
                                        S("navigate", destination="wooden_block_a"),
                                        S("pick", object="wooden_block_a"),
                                        S("navigate", destination=TV, role="alternative"),
                                        S("place", object="wooden_block_a", receptacle=TV, role="alternative")]},
        "naive_hidden_spot": {"kind": "negative", "variants": ["display_hidden"],
                              "note": "the cabinet's only free spot, behind the boxes",
                              "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_a"),
                                        S("pick", object="wooden_block_a"), S("navigate", destination=CAB_TOP),
                                        S("place", object="wooden_block_a", receptacle=CAB_TOP)]}},
    "oracle": {"display_hidden": "hard_open_display"},
    "vary": {"display_hidden": vary()},
}

# ----------------------------------------------------------------- T07 heat the oatmeal (replace appliance, clear burner)
_t07_mw = [S("navigate", destination=MW), S("open", articulated=MW), S("look", target=ISLAND),
           S("navigate", destination="oatmeal"), S("pick", object="oatmeal"), S("navigate", destination=MW_FLOOR),
           S("place", object="oatmeal", receptacle=MW_FLOOR), S("close", articulated=MW),
           S("heat", "fail", "failure", food="oatmeal", appliance=MW, temp_c=40),
           S("stop", role="alternative", appliance=MW), S("pick", role="alternative", object="oatmeal")]
HARD["T07_heat_oatmeal"] = {
    "variants": {"microwave_broken_burner_taken": hard(
        "the microwave runs but does not heat; the pot stands on the left burner and a mug on the right one",
        ["appliance_and_burner"],
        instruction="Warm up the leftover oatmeal for breakfast to at least 40 C in a way that works. When you are "
                    "done, the stove must be off and the microwave door closed.",
        instruction_zh="请用合适方式把燕麦粥加热到至少 40°C，完成后关火并关好微波炉门。",
        goal={"all": [["temperature_at_least", "oatmeal", 40], ["not heating", "kitchen_stove"], ["is_closed", MW],
                      ["upright", "mug"], ["hand_empty", "right"]]},
        watch=["oatmeal", "mug"], thermal_override=NO_MW, move={"mug": at(STOVE_TOP, 8.70, 1.725)})},
    "routes": {
        "hard_stove_clear_burner": {
            "kind": "alternative", "variants": ["microwave_broken_burner_taken"],
            "recovery": "microwave does not heat -> stove; the free burner holds a mug: set the oatmeal down, move "
                        "the mug to the island, then heat on that burner",
            "steps": [*_t07_mw, S("navigate", destination=STOVE_TOP, role="alternative"),
                      S("place", "fail", "failure", object="oatmeal", receptacle=STOVE_TOP),
                      S("navigate", destination=ISLAND, role="insert"),
                      S("place", object="oatmeal", receptacle=ISLAND, role="insert"),
                      S("navigate", destination=STOVE_TOP, role="insert"), S("look", target=STOVE_TOP, role="insert"),
                      S("navigate", destination="mug", role="insert"), S("pick", object="mug", role="insert"),
                      S("navigate", destination=ISLAND, role="insert"),
                      S("place", object="mug", receptacle=ISLAND, role="insert"),
                      S("navigate", destination="oatmeal"), S("pick", object="oatmeal"),
                      S("navigate", destination=STOVE_TOP), S("place", object="oatmeal", receptacle=STOVE_TOP),
                      S("heat", role="alternative", food="oatmeal", appliance="kitchen_stove", temp_c=40),
                      S("navigate", destination=MW), S("close", articulated=MW)]}},
    "oracle": {"microwave_broken_burner_taken": "hard_stove_clear_burner"},
    "vary": {"microwave_broken_burner_taken": vary()},
}

# ----------------------------------------------------------------- T11 collect the fruit (decoy where the basket was)
T11_DECOY = {"bowl_kitchen_cabinet": at(BOOKCASE, 0.92, -0.43)}
_t11_to_bookcase = [S("navigate", destination=DINING), S("look", target=DINING), S("navigate", destination="apple"),
                    S("pick", object="apple"), S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE)]
HARD["T11_collect_fruits"] = {
    "variants": {"basket_gone_bowl_there": hard(
        "no fruit basket: a breakfast bowl stands on the bookcase where the basket usually is; the serving tray is "
        "on the study desk", ["decoy_destination"],
        instruction="Put the apple from the dining table into the fruit basket on the bedroom bookcase; if the "
                    "basket is not there, put it on the serving tray on the study desk.",
        instruction_zh="请把餐桌上的苹果放进卧室书架的果篮；若果篮不在，就放进书桌的托盘。",
        watch=["apple", "serving_tray", "bowl_kitchen_cabinet"],
        remove=["fruit_basket"], move=dict(T11_DECOY))},
    "routes": {
        "hard_tray_not_bowl": {"kind": "alternative", "variants": ["basket_gone_bowl_there"],
                               "recovery": "no basket on the bookcase, only a bowl the instruction does not allow: "
                                           "the tray on the study desk",
                               "steps": [*_t11_to_bookcase, S("navigate", role="alternative", destination=DESK),
                                         S("look", role="alternative", target=DESK),
                                         S("navigate", role="alternative", destination="serving_tray"),
                                         S("place", role="alternative", object="apple", receptacle="serving_tray")]},
        "naive_into_bowl": {"kind": "negative", "variants": ["basket_gone_bowl_there"],
                            "note": "the nearest fruit container: the bowl on the bookcase",
                            "steps": [*_t11_to_bookcase, S("place", object="apple", receptacle="bowl_kitchen_cabinet")]}},
    "oracle": {"basket_gone_bowl_there": "hard_tray_not_bowl"},
    "vary": {"basket_gone_bowl_there": vary()},
}

# ----------------------------------------------------------------- T19 recycling (the instructed bin, not a look-alike)
# a second wide storage bin holding toy blocks stands on the living-room cabinet next to the bedroom door (on the way);
# the recycling bin on the bedroom bookcase already holds a used plastic cup
DECOY_BIN = "toy_storage_bin"
CAB4_TOP = "kitchen_cabinet_4/top"
HARD["T19_recycling"] = {
    "variants": {"lookalike_bin": hard(
        "a look-alike wide storage bin with toy blocks in it stands on the living-room cabinet by the bedroom door; "
        "the recycling bin with a used plastic cup in it is on the bedroom bookcase", ["decoy_destination"],
        instruction="Take the empty soda can and the foam packing cube to the wide storage bin we use for recycling, "
                    "near the low bookcase in the bedroom.",
        instruction_zh="把易拉罐和泡沫块送到卧室矮书架附近用于回收的宽储物箱中。",
        goal={"all": [["inside", "soda_can", "wide_storage_bin"], ["inside", "foam_cube", "wide_storage_bin"],
                      ["hand_empty", "right"]]},
        watch=["soda_can", "foam_cube", "wide_storage_bin", DECOY_BIN],
        add={DECOY_BIN: {"asset": "wide_storage_bin", **at(CAB4_TOP, 1.40, 0.42)},
             "toy_block_in_bin_1": {"asset": "wooden_block", "support": None, "z": 0.632, "xy": [1.33, 0.40],
                                    "yaw_deg": 0},
             "toy_block_in_bin_2": {"asset": "wooden_block", "support": None, "z": 0.632, "xy": [1.47, 0.45],
                                    "yaw_deg": 20},
             "used_plastic_cup": {"asset": "plastic_cup", "support": None, "z": 0.721, "xy": [1.20, -0.50],
                                  "yaw_deg": 0}})},
    "routes": {
        "hard_instructed_bin": {"kind": "alternative", "variants": ["lookalike_bin"],
                                "recovery": "a wide bin with toys stands on the way: keep to the recycling bin by "
                                            "the bedroom bookcase",
                                "steps": [S("explore_room", room="living_room_0_0"), S("navigate", destination=TV),
                                          S("look", target=TV), S("navigate", destination="soda_can"),
                                          S("pick", object="soda_can"), S("navigate", destination=BOOKCASE),
                                          S("look", target=BOOKCASE), S("navigate", destination="wide_storage_bin"),
                                          S("approach", target="wide_storage_bin"),
                                          S("drop", object="soda_can", container="wide_storage_bin"),
                                          S("navigate", destination="foam_cube"), S("pick", object="foam_cube"),
                                          S("navigate", destination="wide_storage_bin"),
                                          S("drop", object="foam_cube", container="wide_storage_bin")]},
        "naive_nearest_bin": {"kind": "negative", "variants": ["lookalike_bin"],
                              "note": "the first wide bin on the way",
                              "steps": [S("explore_room", room="living_room_0_0"), S("navigate", destination=TV),
                                        S("look", target=TV), S("navigate", destination="soda_can"),
                                        S("pick", object="soda_can"), S("navigate", destination=DECOY_BIN),
                                        S("drop", object="soda_can", container=DECOY_BIN)]}},
    "oracle": {"lookalike_bin": "hard_instructed_bin"},
    "vary": {"lookalike_bin": vary()},
}


# ----------------------------------------------------------------- T12 tidy all the toys (decompose / allocate)
# the report's Hard widens the instruction to every scattered toy: the car on the living-room floor, the duck left on
# the study desk, the toy block on the bedroom floor; the storage basket is gone, the bedroom bookcase has a small
# storage bin (22 x 17 x 9 cm) and the wide one (34 x 30 x 14 cm): the toys are spread over three rooms and over the
# two containers by size (the 12 cm car and the duck do not go into the small bin together with the block)
T12_TOYS = ["toy_car", "rubber_duck", "toy_block"]
T12_BINS = {"toy_bin_small": {"asset": "small_storage_bin", **at(BOOKCASE, 0.80, -0.43, 90)},
            "toy_bin_wide": {"asset": "wide_storage_bin", **at(BOOKCASE, 1.10, -0.43)}}
_combos = [[]]
for _t in T12_TOYS:
    _combos = [c + [["inside", _t, b]] for c in _combos for b in T12_BINS]
T12_GOAL = {"any": _combos, "all": [*[["upright", b] for b in T12_BINS], ["hand_empty", "right"]]}
_t12_drop = lambda toy, b: [S("navigate", destination=toy), S("pick", object=toy), S("navigate", destination=b),
                            S("drop", object=toy, container=b)]
HARD["T12_tidy_toys"] = {
    "variants": {"toys_everywhere": hard(
        "three toys in three rooms (car on the living-room floor, duck on the study desk, block on the bedroom "
        "floor); no storage basket, a small and a wide storage bin on the bedroom bookcase", ["joint_capacity"],
        instruction="It is nearly bedtime. Put away all the toys lying around the house into suitable storage "
                    "containers in the bedroom.",
        instruction_zh="快睡觉了，请把房间里分散的玩具全部收好，放入卧室合适的储物容器。",
        goal=T12_GOAL, watch=[*T12_TOYS, *T12_BINS], may_end_on_floor=list(T12_TOYS),
        remove=["storage_basket"], add=dict(T12_BINS),
        move={"rubber_duck": at(DESK, -0.95, -6.02, 128.7)})},
    "routes": {
        "hard_three_rooms_two_bins": {
            "kind": "alternative", "variants": ["toys_everywhere"],
            "recovery": "explore the rooms for every toy; the car and the block into the wide bin, the duck into "
                        "the small one",
            "steps": [S("explore_room", room=BEDROOM), S("navigate", destination=BOOKCASE),
                      S("look", target=BOOKCASE), S("explore_room", room=HALL),
                      *_t12_drop("toy_car", "toy_bin_wide"),
                      S("search", role="recovery", object="rubber_duck", region="living_room_0_1"),
                      *_t12_drop("rubber_duck", "toy_bin_small"), *_t12_drop("toy_block", "toy_bin_wide")]}},
    "oracle": {"toys_everywhere": "hard_three_rooms_two_bins"},
    "vary": {"toys_everywhere": vary()},
}

# ----------------------------------------------------------------- T14 shelve the book (insert: make room first)
# the mug and the rubber duck stand along the front of the bookcase top: no edge slot is wide enough for the book
# (0.07 / 0.18 / 0.08 m between them and the ends, the book needs 0.21 m); moving the mug to the back corner of the
# top frees the front slot
T14_OCC = {"mug_shelf": at(BOOKCASE, 0.86, -0.53), "shelf_blocker": at(BOOKCASE, 1.13, -0.53, 90)}
HARD["T14_shelve_the_book"] = {
    "variants": {"shelf_taken": hard(
        "the flat red book on the study desk; a mug and the rubber duck take up the front of the bedroom bookcase "
        "top", ["destination_full"],
        instruction="Put the red book back on the low bookcase in the bedroom, and deal properly with whatever is "
                    "taking up the space there.",
        instruction_zh="把红书放回卧室矮书架，并妥善处理原有占位物。",
        goal={"all": [["on", "book_red", BOOKCASE], ["hand_empty", "right"], ["upright", "mug_shelf"],
                      ["not on_floor", "mug_shelf"], ["not on_floor", "shelf_blocker"]]},
        watch=["book_red", *T14_OCC], move=dict(T14_OCC))},
    "routes": {
        "hard_make_room_first": {
            "kind": "alternative", "variants": ["shelf_taken"],
            "recovery": "the front of the bookcase top is taken: move the mug to the back corner, then fetch the book",
            "steps": [S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE),
                      S("navigate", destination="mug_shelf", role="insert"),
                      S("pick", object="mug_shelf", role="insert"),
                      S("place", object="mug_shelf", receptacle=BOOKCASE, hint_xy=[0.79, -0.31], role="insert"),
                      S("navigate", destination=DESK), S("look", target=DESK),
                      S("navigate", destination="book_red"), S("expose", object="book_red"),
                      S("pick", object="book_red"), S("navigate", destination=BOOKCASE),
                      S("place", object="book_red", receptacle=BOOKCASE)]},
        "hard_place_fails_then_make_room": {
            "kind": "fallback", "variants": ["shelf_taken"],
            "recovery": "place refused (no free edge spot) -> set the book on the bookcase shelf below, move the "
                        "mug back, put the book on top",
            "steps": [S("navigate", destination=DESK), S("look", target=DESK),
                      S("navigate", destination="book_red"), S("expose", object="book_red"),
                      S("pick", object="book_red"), S("navigate", destination=BOOKCASE),
                      S("place", "fail", "failure", object="book_red", receptacle=BOOKCASE),
                      S("place", object="book_red", receptacle="bookcase_2/shelf_1", role="insert"),
                      S("look", target=BOOKCASE), S("navigate", destination="mug_shelf", role="insert"),
                      S("pick", object="mug_shelf", role="insert"),
                      S("place", object="mug_shelf", receptacle=BOOKCASE, hint_xy=[0.79, -0.31], role="insert"),
                      S("navigate", destination="book_red"), S("pick", object="book_red"),
                      S("navigate", destination=BOOKCASE), S("place", object="book_red", receptacle=BOOKCASE)]}},
    "oracle": {"shelf_taken": "hard_make_room_first"},
    "vary": {"shelf_taken": vary()},
}


# ----------------------------------------------------------------- T13 breakfast setup (lay out bowl and mug together)
# the spoon's neighbourhood on the set table (cereal boxes and plates around it, none of them graspable) leaves two
# slots within 35 cm of the spoon: one south of it that takes a bowl (or a mug), one east of it that takes only a mug.
# No cup: the mug substitutes.  The bowl has to take the south slot; a mug put there first leaves the bowl no room
# next to the spoon (offline free-spot map, margins of place's free_spots)
T13_SET = {"clutter_cereal_a": at(DINING, 2.85, 7.66), "clutter_cereal_b": at(DINING, 3.00, 7.72),
           "plate_counter_a": at(DINING, 3.40, 7.30), "plate_counter_b": at(DINING, 3.20, 7.66)}
T13_GOAL = {"any": [[["on", "cup", DINING], ["upright", "cup"], ["grouped", ["bowl", "cup", "spoon"], DINING, 0.35]],
                    [["on", "mug", DINING], ["upright", "mug"], ["grouped", ["bowl", "mug", "spoon"], DINING, 0.35]]],
            "all": [["on", "bowl", DINING], ["upright", "bowl"], ["hand_empty", "right"]]}
_t13h_look = [S("look", target=DINING), S("navigate", destination=TV), S("look", target=TV)]
_t13h_mug = lambda hint: [S("navigate", destination=BOOKCASE, role="alternative"),
                          S("look", target=BOOKCASE, role="alternative"), S("pick", object="mug", role="alternative"),
                          S("navigate", destination=DINING), S("place", object="mug", receptacle=DINING, hint_xy=hint)]
_t13h_bowl = lambda hint: [S("navigate", destination="bowl"), S("pick", object="bowl"),
                           S("navigate", destination=DINING), S("place", object="bowl", receptacle=DINING, hint_xy=hint)]
HARD["T13_breakfast_setup"] = {
    "variants": {"no_cup_tight_setting": hard(
        "no cup (the mug on the bedroom bookcase substitutes); the spoon on the dining table is hemmed in by cereal "
        "boxes and plates: one slot next to it takes the bowl, the other only the mug", ["no_cup", "spot_quality"],
        instruction="Set a bowl and a cup next to the spoon that is already on the dining table; a mug is fine if "
                    "there is no cup. Lay them out sensibly.",
        instruction_zh="请在餐桌已有的勺子旁摆好碗和杯子；没有 Cup 可用 Mug，保证摆放合理。",
        goal=T13_GOAL, watch=["bowl", "cup", "mug", "spoon", *T13_SET], remove=["cup"], move=dict(T13_SET))},
    "routes": {
        "hard_bowl_slot_then_mug": {"kind": "alternative", "variants": ["no_cup_tight_setting"],
                                    "recovery": "no cup -> the mug; the bowl takes the one slot it fits, the mug the "
                                                "narrow one",
                                    "steps": [*_t13h_look, *_t13h_bowl([2.95, 7.19]), *_t13h_mug([3.156, 7.40])]},
        "naive_mug_in_bowl_slot": {"kind": "negative", "variants": ["no_cup_tight_setting"],
                                   "note": "the mug first, into the larger slot: the bowl has no room next to the spoon",
                                   "steps": [S("look", target=DINING), *_t13h_mug([2.95, 7.19]),
                                             S("navigate", destination=TV), S("look", target=TV),
                                             *_t13h_bowl([3.156, 7.40])]}},
    "oracle": {"no_cup_tight_setting": "hard_bowl_slot_then_mug"},
    "vary": {"no_cup_tight_setting": vary()},
}

# ----------------------------------------------------------------- T20 juice back to the table (make room first)
# after a party the dining table is covered by trays and plates (offline free-spot map: no 13 cm spot for the
# upright bottle with place's margins); the bread bin at the west end is the one light, graspable item: moving it to
# the wall cabinet (where the bottle waits) frees a spot.  place honours an exact hint with a 7.2 cm test, so a hint
# squeezed between two plates (7.7 cm gaps) is a second instruction-compliant strategy the goal accepts
T20_TABLE = {
    "buffet_tray_1": {"asset": "serving_tray", **at(DINING, 3.068, 5.7693)},
    "buffet_tray_2": {"asset": "serving_tray", **at(DINING, 3.558, 5.7693)},
    "party_plate_3": {"asset": "breakfast_plate", **at(DINING, 2.9885, 6.1676)},
    "party_plate_4": {"asset": "breakfast_plate", **at(DINING, 3.313, 6.1676)},
    "party_plate_5": {"asset": "breakfast_plate", **at(DINING, 3.6375, 6.1676)},
    "buffet_tray_6": {"asset": "serving_tray", **at(DINING, 3.068, 6.5659)},
    "buffet_tray_7": {"asset": "serving_tray", **at(DINING, 3.558, 6.5659)},
    "party_plate_8": {"asset": "breakfast_plate", **at(DINING, 2.9885, 6.9642)},
    "party_plate_9": {"asset": "breakfast_plate", **at(DINING, 3.313, 6.9642)},
    "party_plate_10": {"asset": "breakfast_plate", **at(DINING, 3.6375, 6.9642)},
    "buffet_tray_11": {"asset": "serving_tray", **at(DINING, 3.068, 7.3625)},
    "buffet_tray_12": {"asset": "serving_tray", **at(DINING, 3.558, 7.3625)},
    "bread_bin": {"asset": "small_storage_bin", **at(DINING, 2.9693, 7.76, 90)},
    "party_plate_13": {"asset": "breakfast_plate", **at(DINING, 3.2746, 7.7608)},
    "party_plate_14": {"asset": "breakfast_plate", **at(DINING, 3.6189, 7.7608)},
}
T20_GOAL = {"all": [["on", "juice_bottle", DINING], ["upright", "juice_bottle"], ["hand_empty", "right"],
                    ["count_on_at_least", list(T20_TABLE), DINING, len(T20_TABLE) - 2]]}
HARD["T20_juice_back_to_table"] = {
    "variants": {"table_full": hard(
        "the bottle on the low wall cabinet; the dining table is covered by six trays, eight plates and a small bread "
        "bin: no spot left for the bottle to stand", ["destination_full"],
        instruction="Find the juice bottle and put it back on the dining table, standing up; if needed, first make "
                    "room among the things on the table.",
        instruction_zh="找到果汁瓶，确保它直立放回餐桌；必要时先为桌面其他物品腾出空间。",
        goal=T20_GOAL, watch=["juice_bottle", *T20_TABLE],
        remove=["clutter_cereal_a", "clutter_cereal_b", "spoon_target_table"],
        move={"juice_bottle": at(CAB_TOP, 3.68, 0.36, 0)}, add=dict(T20_TABLE))},
    "routes": {
        "hard_make_room_first": {
            "kind": "alternative", "variants": ["table_full"],
            "recovery": "the table has no free spot: take the bread bin to the wall cabinet, bring the bottle back in "
                        "its place",
            "steps": [S("navigate", destination=DINING), S("look", target=DINING),
                      S("navigate", destination="bread_bin", role="insert"), S("pick", object="bread_bin", role="insert"),
                      S("navigate", destination=CAB_TOP, role="insert"),
                      S("place", object="bread_bin", receptacle=CAB_TOP, hint_xy=[3.36, 0.36], role="insert"),
                      S("look", target=CAB_TOP), S("pick", object="juice_bottle"), S("navigate", destination=DINING),
                      S("place", object="juice_bottle", receptacle=DINING, hint_xy=[2.97, 7.76])]},
        "naive_no_room": {"kind": "negative", "variants": ["table_full"], "note": "the Easy plan: place is refused",
                          "steps": [S("navigate", destination=CAB_TOP), S("look", target=CAB_TOP),
                                    S("navigate", destination="juice_bottle"), S("pick", object="juice_bottle"),
                                    S("navigate", destination=DINING),
                                    S("place", object="juice_bottle", receptacle=DINING)]}},
    "oracle": {"table_full": "hard_make_room_first"},
    "vary": {"table_full": vary()},
}


def merge(tasks: list) -> list:
    """Add the v4 Hard variants, routes and oracle entries to the built v3 tasks (in place)."""
    by = {t["task_id"]: t for t in tasks}
    for tid, ext in HARD.items():
        t = by[tid]
        for name, var in ext["variants"].items():
            assert name not in t["variants"], (tid, name)
            var = dict(var)
            if name in ext.get("vary", {}):
                var["vary"] = ext["vary"][name]
            t["variants"][name] = var
        for name, r in ext["routes"].items():
            assert name not in t["routes"], (tid, name)
            t["routes"][name] = dict(r, since=VERSION)
        t["oracle"].update(ext["oracle"])
        t["not_adopted"] = t.get("not_adopted", []) + ext.get("not_adopted", [])
    return tasks
