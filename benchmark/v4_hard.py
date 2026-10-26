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
                          STOVE_TOP, TV, S, _soup_tail, at)

VERSION = "v4"
HALL = "living_room_0_0"
BEDROOM = "bedroom_0_1"

# tag -> (condition type, decision, meaning); decision = the task-graph change the condition requires
CONDITIONS = {
    "surface_cluttered": ("occupied_workspace", "insert",
                          "objects stand where the work happens (the wiped strip): move them aside, do the work, put them back"),
    "cookware_choice": ("cookware_choice", "replace",
                        "several vessels by the food, only one supports every step (stirring, lid, burner): choose it "
                        "over the nearer ones"),
    "appliance_occupied": ("appliance_choice", "replace",
                           "the usual appliance is taken by something else; another one does the job without clearing "
                           "it (clearing stays allowed)"),
    "spot_quality": ("destination_constraint", "insert",
                     "the destination has free spots that violate the instruction (crowding the place settings, "
                     "hidden, at the edge): choose the spot from what is observed"),
    "unstable_base": ("support_stability", "insert",
                      "the obvious base lies at the edge: stack on the other one or move it in first"),
    "joint_capacity": ("container_capacity", "decompose",
                       "several containers, only one holds every item together: allocate the items jointly"),
    "anchor_boxed_in": ("anchor_relocation", "insert",
                        "the object to set things next to has no room around it: move it to where the whole setting "
                        "fits"),
    "no_cup": ("object_absent", "alternative", "the requested object does not exist; the allowed substitute is used"),
    "destination_full": ("destination_occupied", "insert",
                         "the destination has no room left: move what occupies it to a legal place, then put the "
                         "object there"),
    "item_out_of_view": ("search_target", "decompose",
                         "one of several items to collect is in another room, out of view: search, then route the "
                         "collection"),
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
# after cooking the island is cluttered along both long strips.  wipe sweeps a 30 cm strip 8 cm in from the edge
# the robot stands at (from the sponge on the TV stand, approach parks at x 7.74 on the front: strip x 7.59-7.89,
# y 1.595, s10 and s11), and it does not steer around what stands there: its free-strip test passes the strip box
# as [x0, y0, z0, x1, y1, z1] to skills._overlaps_objects, which reads [x0, y0, x1, y1, z0, z1], so the sponge
# shoves block B 9 cm aside and turns it (s10, the wipe "succeeds").  The plan has to take what stands in the strip
# off the island first and put it back afterwards; the verifier tells a put-back object (picked up, within 12 cm:
# restore lands +-10 cm) from a pushed one (never picked up, more than 3 cm from its start).  Moving more than
# block B (the whole front row near the robot) is a valid, slower plan
T08_FRONT = {"rolling_pin": at(ISLAND, 6.75, 1.62, 0), "wooden_block_a": at(ISLAND, 7.10, 1.62),
             "soda_can": at(ISLAND, 7.45, 1.62), "wooden_block_b": at(ISLAND, 7.80, 1.62),
             "mug": at(ISLAND, 8.10, 1.62)}
T08_BACK = {"oatmeal": at(ISLAND, 6.97, 1.88), "paperback_book": at(ISLAND, 7.27, 1.88, 0),
            "breakfast_spoon": at(ISLAND, 7.63, 1.88, 0), "juice_bottle": at(ISLAND, 7.94, 1.88)}
T08_LINE = {**T08_FRONT, **T08_BACK}
T08_GOAL = {"all": [["wiped", ISLAND], ["on", "kitchen_sponge", TV], ["hand_empty", "right"],
                    *[["near_start", n, 0.12, 0.03] for n in T08_LINE],
                    *[["upright", n] for n in ("soda_can", "mug", "juice_bottle", "oatmeal")]]}
_t08_sponge = [S("look", target=TV), S("navigate", destination="kitchen_sponge"), S("pick", object="kitchen_sponge")]
_t08_aside = [S("navigate", destination="wooden_block_b", role="insert"),
              S("pick", object="wooden_block_b", role="insert"), S("navigate", destination=TV, role="insert"),
              # west of the sponge, where block A landed in the passing runs: placed next to the sponge the block
              # slipped lifted over it (s10) or hid it from the head camera (s11); placed at the east end, the arm
              # swept the sponge off the stand on the way to it (s10, s11)
              S("place", object="wooden_block_b", receptacle=TV, hint_xy=[7.14, 0.44], role="insert")]
HARD["T08_wipe_island"] = {
    "variants": {"island_cluttered": hard(
        "after cooking the island is cluttered along both long strips (pin, two blocks, can and mug in front; bowl, "
        "book, spoon and bottle behind, staggered); the sponge dries on the TV stand", ["surface_cluttered"],
        # (the sponge goes back where it was found: left on the island, place put it on block B's own spot and
        # restore moved B 54 cm away, s10, s11; hinted beside the strip it knocked the soda can over, s10, s11)
        instruction="Wipe the kitchen island clean with the sponge. Deal with the things standing on it properly "
                    "and put them back as they were, and put the sponge back where you found it.",
        instruction_zh="用海绵擦净厨房岛台，妥善处理并恢复台面物品，最后把海绵放回原处。",
        goal=T08_GOAL, watch=["kitchen_sponge", *T08_LINE],
        # the sponge dries on the TV stand (on the island it was out of view behind the mug or missed, s10)
        move={**T08_LINE, "kitchen_sponge": at(TV, 7.6, 0.38)})},
    "routes": {
        "hard_proactive": {
            "kind": "alternative", "variants": ["island_cluttered"],
            "recovery": "block B stands in the strip the robot wipes: move it to the TV stand, wipe, put it back",
            "steps": [S("look", target=ISLAND), *_t08_aside, *_t08_sponge, S("approach", target=ISLAND),
                      S("wipe", surface=ISLAND, tool="kitchen_sponge"),
                      S("navigate", destination=TV), S("place", object="kitchen_sponge", receptacle=TV),
                      # back on its own spot: restore returns an object to its start support at a free spot near
                      # the robot (B came back 54 cm west of its spot, s10, s11), place honours an exact hint
                      S("navigate", destination="wooden_block_b", role="restore"),
                      S("pick", object="wooden_block_b", role="restore"),
                      S("navigate", destination=ISLAND, role="restore"),
                      S("place", object="wooden_block_b", receptacle=ISLAND, hint_xy=[7.80, 1.62], role="restore")]},
        "naive_wipe_around": {
            "kind": "negative", "variants": ["island_cluttered"],
            "note": "the Easy plan: wipe with the clutter in place; the sponge shoves block B aside",
            "steps": [S("look", target=ISLAND), *_t08_sponge, S("approach", target=ISLAND),
                      S("wipe", surface=ISLAND, tool="kitchen_sponge"),
                      S("navigate", destination=TV), S("place", object="kitchen_sponge", receptacle=TV)]}},
    "oracle": {"island_cluttered": "hard_proactive"},
    "vary": {"island_cluttered": vary()},
    "not_adopted": [{"condition": "a reactive route: wipe refused (no free strip) -> clear -> wipe again",
                     "reason": "wipe never refuses a cluttered strip (box-order mismatch in its free-strip test, "
                               "zeno_skills/policies/tooluse.py; skill code left unchanged), it shoves what stands "
                               "there (s10): the clutter has to be seen and cleared first"}],
}

# ----------------------------------------------------------------- T09 tomato soup (choose the cookware)
# three vessels could take the tomatoes: an empty breakfast bowl and a mug right next to them on the island, and the
# pot on the stove (its lid beside it).  The instruction asks for "a suitable pot" and names no vessel; only the pot
# takes the whole recipe (stirring room, its own lid, a burner).  The bowl and the mug are the nearer containers but
# neither is cookware for the lid and the stove: collecting into them is the plan the Hard rejects.
T09_DECOYS = {"bowl_kitchen_cabinet": at(ISLAND, 7.20, 1.80), "mug_counter": at(ISLAND, 8.10, 1.80),
              "pot_lid": at(STOVE_TOP, 8.715, 1.655)}
HARD["T09_tomato_soup"] = {
    "variants": {"cookware_choice": hard(
        "a breakfast bowl and a mug stand by the tomatoes on the island; the pot is on the stove, its lid beside it",
        ["cookware_choice"],
        instruction="Make tomato soup for lunch in a suitable pot: put the cherry tomatoes in, stir them, cover the "
                    "pot and heat the soup to 60 C, then turn the stove off.",
        instruction_zh="请用合适锅具完成番茄入锅、搅拌、盖锅、加热至60°C和关火。",
        watch=["cherry_tomato_1", "cherry_tomato_2", POT, "pot_lid", "breakfast_spoon", "bowl_kitchen_cabinet",
               "mug_counter"],
        move=dict(T09_DECOYS))},
    "routes": {
        "hard_pot_not_bowl": {
            "kind": "alternative", "variants": ["cookware_choice"],
            "recovery": "of the three vessels only the pot can be stirred in, lidded and heated on the stove",
            "steps": [S("look", target=ISLAND), S("look", target=STOVE_TOP),
                      S("collect", role="alternative", objects=["cherry_tomato_1", "cherry_tomato_2"], container=POT),
                      *_soup_tail]},
        "naive_nearest_vessel": {
            "kind": "negative", "variants": ["cookware_choice"],
            "note": "the nearest container, the breakfast bowl: the soup is not in the pot (and the bowl is no cookware)",
            "steps": [S("look", target=ISLAND),
                      S("collect", objects=["cherry_tomato_1", "cherry_tomato_2"], container="bowl_kitchen_cabinet")]}},
    "oracle": {"cookware_choice": "hard_pot_not_bowl"},
    "vary": {"cookware_choice": vary()},
    "not_adopted": [{"condition": "the pot off the stove (on the island), to be carried to a burner first",
                     "reason": "carried by its handle (pick grasp=handle; the rim pinch slipped while carried, s10) "
                               "the pot hangs tilted: lowered onto the left burner its rim caught the island's edge "
                               "2 cm west of the stove and it came to rest on it (targets x 8.41 / 8.45 / 8.50, 3/3, "
                               "s10); with the lid on the left burner the stove had no free spot for it on the right "
                               "(s10)"}],
}

# ----------------------------------------------------------------- T01 book to the dining table (where to read)
# the table is set along its east edge (the side the robot parks at, 4.33 / 6.25): the free edge slots between the
# settings fit the 18 cm book with 2-3 cm to spare except one, between the cup and the second plate (36 cm); place's
# own choice (the slot nearest the robot) crowds a setting, the reading spot has to be chosen
T01_SET = {"bowl_side_table": at(DINING, 3.70, 5.65), "plate_counter_a": at(DINING, 3.66, 6.093),
           "cup_side_table": at(DINING, 3.70, 6.502), "plate_counter_b": at(DINING, 3.66, 7.041),
           "clutter_cereal_a": at(DINING, 3.70, 7.46), "mug_dining_cabinet": at(DINING, 3.70, 7.84),
           "spoon_target_table": at(DINING, 3.38, 7.04), "clutter_cereal_b": at(DINING, 3.20, 7.60)}
T01_WARE = list(T01_SET)
T01_PLACES = ["bowl_side_table", "plate_counter_a", "plate_counter_b"]
# easy to read over breakfast: beside a place setting (within 15 cm of a plate or the bowl); out of the way: 5 cm clear
# of every piece of tableware, and none of it moved.  Three kinds of free spot exist: wedged between settings (too
# close), far from any setting (west edge, south end: not where one eats) and the one slot beside the second plate
T01_GOAL = {"all": [["on", "paperback_book", DINING], ["clear_of", "paperback_book", T01_WARE, 0.05],
                    ["near_any", "paperback_book", T01_PLACES, 0.15],
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
            "wooden_block_b": at(ISLAND, 7.00, 1.66)}             # in the open, 14.5 cm in
# (at y 1.75, 23.5 cm in, the pick of B missed it twice, s10, with and without an approach)
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
            # (picked straight after navigate, the arm reached B from the island's back and missed it, s10)
            "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_b"),
                      S("approach", target="wooden_block_b"), S("pick", object="wooden_block_b"),
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
        "the mug on the island next to the utensils, a small storage bin (22 x 17 cm) and the wide storage bin side "
        "by side on the TV stand: the spoon fits the small bin, the 22 cm rolling pin only the wide one",
        ["joint_capacity"],
        instruction="Baking is done. Put the rolling pin and the spoon away together in one suitable container, "
                    "both of them completely inside.",
        instruction_zh="烘焙结束，请把擀面杖和勺子一起收进同一个合适容器，确保两件都完整放入。",
        # "completely inside": fully_inside, not inside (an xy test: the pin laid across the small bin, 3 cm above
        # its rim, passed it, s10)
        goal={"any": [[["fully_inside", "rolling_pin", T03_BIN], ["fully_inside", "breakfast_spoon", T03_BIN]],
                      [["fully_inside", "rolling_pin", "mug"], ["fully_inside", "breakfast_spoon", "mug"]],
                      [["fully_inside", "rolling_pin", SMALL_BIN], ["fully_inside", "breakfast_spoon", SMALL_BIN]]],
              "all": [["hand_empty", "right"]]},
        watch=["rolling_pin", "breakfast_spoon", "mug", T03_BIN, SMALL_BIN],
        # the small bin stands on the TV stand beside the wide one, so the two differ only in size (on the island,
        # at y 1.80 and 1.68, no base pose reached above it for a drop, s10: the choice would have been forced by
        # reach, not capacity)
        add={SMALL_BIN: {"asset": "small_storage_bin", **at(TV, 7.85, 0.40)}})},
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
            "steps": [S("look", target=ISLAND), S("look", target=TV), S("navigate", destination="breakfast_spoon"),
                      # (dropped straight after navigate: no base pose above the bin, s10)
                      S("pick", object="breakfast_spoon"), S("navigate", destination=SMALL_BIN),
                      S("approach", target=SMALL_BIN), S("drop", object="breakfast_spoon", container=SMALL_BIN),
                      S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"),
                      S("navigate", destination=SMALL_BIN), S("approach", target=SMALL_BIN),
                      S("place", object="rolling_pin", receptacle=SMALL_BIN)]}},
    "oracle": {"three_containers": "hard_measure_then_wide_bin"},
    "vary": {"three_containers": vary()},
}

# ----------------------------------------------------------------- T06 display the block (visible, steady)
# three cereal boxes (turned: 12.5 cm wide) and the juice bottle line the wall cabinet's front with 3 cm gaps (the
# block is 5 cm): only the front edge is open (walls behind and at both sides), so every free spot is behind the row,
# out of sight.  (With two boxes and the bottle 7-14 cm apart the block went into a gap and could be seen, s10)
T06_CAB = {"clutter_cereal_a": at(CAB_TOP, 3.2777, 0.44, 90), "clutter_cereal_b": at(CAB_TOP, 3.4327, 0.44, 90),
           "juice_bottle": at(CAB_TOP, 3.710, 0.45)}
T06_ADD = {"clutter_cereal_c": {"asset": "cereal_box", **at(CAB_TOP, 3.5880, 0.44, 90)}}
T06_GOAL = {"any": [[["on", b, sup], ["front_visible", b], ["away_from_edge", b, 0.02]]
                    for b in ("wooden_block_a", "wooden_block_b") for sup in (CAB_TOP, TV)],
            "all": [*[["upright", n] for n in (*T06_CAB, *T06_ADD)], ["hand_empty", "right"]]}
HARD["T06_block_destination_occupied"] = {
    "variants": {"display_hidden": hard(
        "three cereal boxes and the juice bottle stand along the wall cabinet's front; the free space behind them "
        "is hidden from the room, the TV stand is open", ["spot_quality"],
        instruction="Put the toy block on display on the low wall cabinet or the TV stand, in a spot where it can "
                    "be seen clearly and stands steadily.",
        instruction_zh="请把积木展示在靠墙矮柜或电视柜上一个醒目、稳定的位置。",
        goal=T06_GOAL, watch=["wooden_block_a", "wooden_block_b", *T06_CAB, *T06_ADD], move=dict(T06_CAB),
        add=dict(T06_ADD))},
    "routes": {
        "hard_open_display": {"kind": "alternative", "variants": ["display_hidden"],
                              "recovery": "the cabinet's free spot is hidden behind the boxes: the TV stand",
                              "steps": [S("look", target=ISLAND), S("look", target=CAB_TOP),
                                        S("navigate", destination="wooden_block_a"),
                                        S("pick", object="wooden_block_a"),
                                        S("navigate", destination=TV, role="alternative"),
                                        S("place", object="wooden_block_a", receptacle=TV, role="alternative")]},
        "naive_hidden_spot": {"kind": "negative", "variants": ["display_hidden"],
                              "note": "the cabinet's free space, behind the boxes",
                              "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_a"),
                                        S("pick", object="wooden_block_a"), S("navigate", destination=CAB_TOP),
                                        S("place", object="wooden_block_a", receptacle=CAB_TOP)]}},
    "oracle": {"display_hidden": "hard_open_display"},
    "vary": {"display_hidden": vary()},
}

# ----------------------------------------------------------------- T07 heat the oatmeal (choose the appliance)
# the microwave works, but the soup pot with its lid was put away in it: its 26 cm leave 13 cm on either side of the
# cavity, the 18 cm oatmeal bowl does not fit beside it.  Both burners are free.  Valid plans: heat on the stove (no
# clearing), or take the pot out of the microwave first and use it.  Nothing fails on purpose; what the cavity holds
# is seen once the door is open
T07_MW = {"handled_cooking_pot": {"support": MW_FLOOR, "xy": [4.50, 2.50], "yaw_deg": 0},
          "pot_lid": {"support": None, "z": 0.880, "xy": [4.50, 2.50], "yaw_deg": 0}}
HARD["T07_heat_oatmeal"] = {
    "variants": {"microwave_holds_pot": hard(
        "the soup pot with its lid stands in the microwave (no room for the bowl beside it); both burners are free",
        ["appliance_occupied"],
        instruction="Warm up the leftover oatmeal for breakfast to at least 40 C in a way that works. When you are "
                    "done, the stove must be off and the microwave door closed.",
        instruction_zh="请用合适方式把燕麦粥加热到至少 40°C，完成后关火并关好微波炉门。",
        goal={"all": [["temperature_at_least", "oatmeal", 40], ["not heating", "kitchen_stove"], ["is_closed", MW],
                      ["not on_floor", POT], ["hand_empty", "right"]]},
        watch=["oatmeal", POT, "pot_lid"], move=dict(T07_MW))},
    "routes": {
        "hard_stove_instead": {
            "kind": "alternative", "variants": ["microwave_holds_pot"],
            "recovery": "the microwave is taken by the pot: heat on the free stove instead of clearing it",
            "steps": [S("navigate", destination=MW), S("open", articulated=MW), S("look", target=MW_FLOOR),
                      S("close", articulated=MW), S("look", target=ISLAND), S("navigate", destination="oatmeal"),
                      S("pick", object="oatmeal"), S("navigate", destination=STOVE_TOP, role="alternative"),
                      S("place", object="oatmeal", receptacle=STOVE_TOP, role="alternative"),
                      S("heat", role="alternative", food="oatmeal", appliance="kitchen_stove", temp_c=40)]},
        "naive_microwave_anyway": {
            "kind": "negative", "variants": ["microwave_holds_pot"],
            "note": "the Easy plan: the bowl does not fit next to the pot",
            "steps": [S("navigate", destination=MW), S("open", articulated=MW), S("look", target=ISLAND),
                      S("navigate", destination="oatmeal"), S("pick", object="oatmeal"),
                      S("navigate", destination=MW_FLOOR),
                      S("place", "fail", object="oatmeal", receptacle=MW_FLOOR)]}},
    "oracle": {"microwave_holds_pot": "hard_stove_instead"},
    "vary": {"microwave_holds_pot": vary()},
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
# the can is not on the TV stand today but on the dining table (out of the living-room views: search); the foam cube
# lies on the living-room floor.  A second wide storage bin holding toy blocks stands on the living-room cabinet by the
# bedroom door, on the way; the recycling bin on the bedroom bookcase already holds a used plastic cup.  Collecting
# the two items from two rooms and keeping to the instructed bin is the plan
DECOY_BIN = "toy_storage_bin"
CAB4_TOP = "kitchen_cabinet_4/top"
HARD["T19_recycling"] = {
    "variants": {"lookalike_bin": hard(
        "the can was left on the dining table (out of view); a look-alike wide storage bin with toy blocks in it "
        "stands on the living-room cabinet by the bedroom door; the recycling bin with a used plastic cup in it is on "
        "the bedroom bookcase", ["decoy_destination", "item_out_of_view"],
        instruction="Take the empty soda can and the foam packing cube to the wide storage bin we use for recycling, "
                    "near the low bookcase in the bedroom.",
        instruction_zh="把易拉罐和泡沫块送到卧室矮书架附近用于回收的宽储物箱中。",
        goal={"all": [["inside", "soda_can", "wide_storage_bin"], ["inside", "foam_cube", "wide_storage_bin"],
                      ["hand_empty", "right"]]},
        watch=["soda_can", "foam_cube", "wide_storage_bin", DECOY_BIN],
        move={"soda_can": at(DINING, 3.70, 6.30)},
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
                                          S("look", target=TV),
                                          S("search", role="recovery", object="soda_can", region="dining_room_0_1"),
                                          S("navigate", destination="soda_can"),
                                          S("pick", object="soda_can"), S("navigate", destination=BOOKCASE),
                                          S("look", target=BOOKCASE), S("navigate", destination="wide_storage_bin"),
                                          S("approach", target="wide_storage_bin"),
                                          S("drop", object="soda_can", container="wide_storage_bin"),
                                          S("navigate", destination="foam_cube"), S("pick", object="foam_cube"),
                                          S("navigate", destination="wide_storage_bin"),
                                          S("drop", object="foam_cube", container="wide_storage_bin")]},
        "naive_nearest_bin": {"kind": "negative", "variants": ["lookalike_bin"],
                              "note": "the first wide bin on the way",
                              "steps": [S("explore_room", room="living_room_0_0"),
                                        S("search", object="soda_can", region="dining_room_0_1"),
                                        S("navigate", destination="soda_can"),
                                        S("pick", object="soda_can"), S("navigate", destination=DECOY_BIN),
                                        S("drop", object="soda_can", container=DECOY_BIN)]}},
    "oracle": {"lookalike_bin": "hard_instructed_bin"},
    "vary": {"lookalike_bin": vary()},
}


# ----------------------------------------------------------------- T12 tidy all the toys (allocate by capacity)
# the report's Hard widens the instruction to every scattered toy: the car on the living-room floor and the duck left
# on the study desk.  The storage basket is gone; the bedroom bookcase holds the two toy containers that are left,
# and their capacity binds:
#   * the small storage bin (9 cm deep) already holds six wooden blocks along both ends; the 11 x 16 cm gap between
#     them takes the duck or the car, not both (6.6 + 5.3 cm > 11 cm across, 9 + 12 cm > 16 cm along);
#   * the shallow sorting tray (5.5 cm rim) takes the car but not the 6.6-8.4 cm duck: it would stick out.
# So no single container holds both toys: the duck must take the bin's gap and the car the tray.  Put away = fully
# inside (episode.goal_predicates.fully_inside), the stored blocks included.  (A third toy was dropped: container
# place and drop release at the container's centre, so a container that already holds one toy cannot be filled
# reliably by a second, s10)
T12_TOYS = ["toy_car", "rubber_duck"]
T12_BIN, T12_TRAY = "toy_bin_small", "toy_tray"
_t12_blocks = {f"stored_block_{i}": {"asset": "wooden_block", "support": None, "z": 0.718, "xy": [x, y], "yaw_deg": 0}
               for i, (x, y) in enumerate([(x, y) for x in (0.762, 0.918) for y in (-0.485, -0.43, -0.375)], 1)}
T12_ADD = {T12_BIN: {"asset": "small_storage_bin", **at(BOOKCASE, 0.84, -0.43)},
           T12_TRAY: {"asset": "shallow_sorting_tray", **at(BOOKCASE, 1.13, -0.43)}, **_t12_blocks}
_combos = [[]]
for _t in T12_TOYS:
    _combos = [c + [["fully_inside", _t, b]] for c in _combos for b in (T12_BIN, T12_TRAY)]
T12_GOAL = {"any": _combos,
            "all": [*[["fully_inside", b, T12_BIN] for b in _t12_blocks], ["upright", T12_BIN], ["hand_empty", "right"]]}
_t12_put = lambda toy, c, how="place": [S("navigate", destination=toy), S("pick", object=toy),
                                        S("navigate", destination=c),
                                        S("drop", object=toy, container=c) if how == "drop"
                                        else S("place", object=toy, receptacle=c)]
HARD["T12_tidy_toys"] = {
    "variants": {"toys_everywhere": hard(
        "the car on the living-room floor, the duck on the study desk; no storage basket: a small bin already half "
        "full of blocks and a shallow tray on the bedroom bookcase", ["joint_capacity"],
        instruction="It is nearly bedtime. Put away all the toys lying around the house into suitable storage "
                    "containers in the bedroom.",
        instruction_zh="快睡觉了，请把房间里分散的玩具全部收好，放入卧室合适的储物容器。",
        goal=T12_GOAL, watch=[*T12_TOYS, T12_BIN, T12_TRAY], may_end_on_floor=["toy_car"],
        remove=["storage_basket"], add=dict(T12_ADD),
        move={"rubber_duck": at(DESK, -0.95, -6.02, 128.7)})},
    "routes": {
        "hard_allocate_by_size": {
            "kind": "alternative", "variants": ["toys_everywhere"],
            "recovery": "look at the containers first: the duck needs the bin's last gap, so the car goes to the tray",
            "steps": [S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE),
                      S("measure", object=T12_BIN), S("measure", object=T12_TRAY), S("explore_room", room=HALL),
                      *_t12_put("toy_car", T12_TRAY),
                      S("search", role="recovery", object="rubber_duck", region="living_room_0_1"),
                      *_t12_put("rubber_duck", T12_BIN, "drop")]},
        "naive_first_toy_in_the_bin": {
            "kind": "negative", "variants": ["toys_everywhere"],
            "note": "the deeper container for the first toy found: the car takes the bin's gap, the duck fits nowhere",
            "steps": [S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE),
                      S("explore_room", room=HALL), *_t12_put("toy_car", T12_BIN, "drop"),
                      S("search", object="rubber_duck", region="living_room_0_1"),
                      *_t12_put("rubber_duck", T12_TRAY)]}},
    "oracle": {"toys_everywhere": "hard_allocate_by_size"},
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
                      S("navigate", destination=BOOKCASE), S("place", object="book_red", receptacle=BOOKCASE)]},
        "probe_approach_then_place": {
            "kind": "diagnostic", "variants": ["shelf_taken"],
            "note": "the book placement on the bookcase top after an approach / with a hint (place_flat regression)",
            "steps": [S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE),
                      S("navigate", destination="mug_shelf"), S("pick", object="mug_shelf"),
                      S("place", object="mug_shelf", receptacle=BOOKCASE, hint_xy=[0.79, -0.31]),
                      S("navigate", destination=DESK), S("look", target=DESK),
                      S("navigate", destination="book_red"), S("expose", object="book_red"),
                      S("pick", object="book_red"), S("navigate", destination=BOOKCASE),
                      S("approach", target=BOOKCASE),
                      S("place", object="book_red", receptacle=BOOKCASE, hint_xy=[0.98, -0.52])]},
        "naive_book_elsewhere": {
            "kind": "negative", "variants": ["shelf_taken"],
            "note": "place refused on the full top; the book is left on the shelf below instead of making room",
            "steps": [S("navigate", destination=DESK), S("look", target=DESK),
                      S("navigate", destination="book_red"), S("expose", object="book_red"),
                      S("pick", object="book_red"), S("navigate", destination=BOOKCASE),
                      S("place", "fail", object="book_red", receptacle=BOOKCASE),
                      S("place", object="book_red", receptacle="bookcase_2/shelf_1")]}},
    "oracle": {"shelf_taken": "hard_make_room_first"},
    "blocker": "the last step, place of the book on bookcase_2/top, fails on the current support slabs: the book "
               "falls to the floor (s10, also with approach + hint).  The v3 Medium route T14 book_on_desk / nominal "
               "fails the same way on this code (s10): the place_flat parking regression of "
               "docs/HANDOFF_2026-10-24_support_slabs.md section 1.2 (3), a physical / skill issue, not a planning "
               "one.  Everything before it (seeing the full top, moving the mug to its back corner, fetching the "
               "flat book with expose) runs.",
    "not_adopted": [{"condition": "book start yaw changed by -16 / +16 deg to work around the place_flat regression",
                     "reason": "the edge pinch then missed (yaw 74, s10) or the book slipped while carried (yaw 106, "
                               "s10)"}],
    "vary": {"shelf_taken": vary()},
}


# ----------------------------------------------------------------- T13 breakfast setup (re-anchor the setting)
# no cup (the mug substitutes) and the spoon already on the table is hemmed in by cereal boxes and plates (none of
# them graspable): neither the bowl nor the mug fits within 40 cm of it (offline free-spot map with place's margins).
# The free part of the table is further south.  The setting has to move: carry the spoon to the free part and set the
# bowl and the mug beside it there.  Squeezing a hint in next to the spoon finds no spot
T13_SET = {"clutter_cereal_a": at(DINING, 2.86, 7.22), "clutter_cereal_b": at(DINING, 2.86, 7.70),
           "plate_counter_a": at(DINING, 3.22, 7.24), "plate_counter_b": at(DINING, 3.22, 7.62),
           "plate_dining_cabinet": at(DINING, 3.10, 7.88)}
# "next to it": the three within 40 cm of each other (the boxed-in spoon has no bowl or mug spot within 40 cm either,
# offline map; a placed column bowl / spoon / mug spanned 0.373 m, s10)
T13_GOAL = {"any": [[["on", "cup", DINING], ["upright", "cup"], ["grouped", ["bowl", "cup", "spoon"], DINING, 0.40]],
                    [["on", "mug", DINING], ["upright", "mug"], ["grouped", ["bowl", "mug", "spoon"], DINING, 0.40]]],
            "all": [["on", "bowl", DINING], ["upright", "bowl"], ["on", "spoon", DINING], ["hand_empty", "right"]]}
_t13h_look = [S("look", target=DINING), S("navigate", destination=TV), S("look", target=TV)]
_t13h_mug = lambda hint: [S("navigate", destination=BOOKCASE, role="alternative"),
                          S("look", target=BOOKCASE, role="alternative"), S("pick", object="mug", role="alternative"),
                          S("navigate", destination=DINING), S("place", object="mug", receptacle=DINING, hint_xy=hint)]
_t13h_bowl = lambda hint: [S("navigate", destination="bowl"), S("pick", object="bowl"),
                           S("navigate", destination=DINING), S("place", object="bowl", receptacle=DINING, hint_xy=hint)]
HARD["T13_breakfast_setup"] = {
    "variants": {"no_cup_spoon_boxed_in": hard(
        "no cup (the mug on the bedroom bookcase substitutes); the spoon on the dining table is boxed in by cereal "
        "boxes and plates, no room for a bowl or a mug next to it", ["no_cup", "anchor_boxed_in"],
        instruction="Set a bowl and a cup next to the spoon that is already on the dining table; a mug is fine if "
                    "there is no cup. Lay them out sensibly.",
        instruction_zh="请在餐桌已有的勺子旁摆好碗和杯子；没有 Cup 可用 Mug，保证摆放合理。",
        goal=T13_GOAL, watch=["bowl", "cup", "mug", "spoon", *T13_SET], remove=["cup"], move=dict(T13_SET))},
    "routes": {
        "hard_move_the_setting": {"kind": "alternative", "variants": ["no_cup_spoon_boxed_in"],
                                  "recovery": "no room by the spoon: carry the spoon to the free part of the table, "
                                              "set the bowl and (no cup) the mug beside it",
                                  "steps": [S("navigate", destination=DINING), S("look", target=DINING),
                                            S("navigate", destination="spoon", role="insert"),
                                            S("pick", object="spoon", role="insert"),
                                            # placed straight from the pick pose, the arm knocked cereal box a
                                            # over onto the mug's spot (s11; s10 it fell just clear): re-park first
                                            S("navigate", destination=DINING, role="insert"),
                                            # the new setting is a column at x ~3.0, where the robot reaches from
                                            # the west (x 3.20-3.24 was out of reach at y 6.7, s10): bowl, spoon,
                                            # mug from south to north
                                            # (a mug released 4 cm from the spoon tipped over, s10: more room)
                                            # (14 cm further south than first tried: the arm still knocks
                                            # cereal box a over while placing the spoon, it lies at y ~7.0 and
                                            # the mug at y 6.92 leaned on it, s11)
                                            S("place", object="spoon", receptacle=DINING, hint_xy=[3.02, 6.61],
                                              role="insert"),
                                            S("navigate", destination=TV), S("look", target=TV),
                                            *_t13h_bowl([3.00, 6.44]), *_t13h_mug([3.00, 6.78])]},
        "naive_squeeze_by_the_spoon": {"kind": "negative", "variants": ["no_cup_spoon_boxed_in"],
                                       "note": "the Easy plan: no spot next to the spoon, the bowl lands elsewhere",
                                       "steps": [*_t13h_look, *_t13h_bowl([3.00, 7.46])]}},
    "oracle": {"no_cup_spoon_boxed_in": "hard_move_the_setting"},
    "vary": {"no_cup_spoon_boxed_in": vary()},
}

# ----------------------------------------------------------------- T20 juice back to the table (make room first)
# after a party the dining table is covered by trays, plates and a row of bowls (offline free-spot map: no 13 cm spot
# for the upright bottle with place's margins; trays and plates are not graspable).  Moving one bowl out of the row
# (onto the tray beside it, or off the table) frees a spot.  (A small bread bin in the bowl's place was tried first:
# its rim pinch did not hold, s10; carried to the wall cabinet the bowl slipped out of the hand, s10.  Fetching the
# bottle first and standing it on a tray while making room: the tray's centre was out of reach, s10.)  place honours an exact hint with a 7.2 cm test, so a hint
# squeezed between two plates (7.7 cm gaps) is a second instruction-compliant strategy the goal accepts
T20_TABLE = {
    "buffet_tray_1": {"asset": "serving_tray", **at(DINING, 3.068, 5.776)},
    "buffet_tray_2": {"asset": "serving_tray", **at(DINING, 3.558, 5.776)},
    "party_plate_3": {"asset": "breakfast_plate", **at(DINING, 2.9885, 6.181)},
    "party_plate_4": {"asset": "breakfast_plate", **at(DINING, 3.313, 6.181)},
    "party_plate_5": {"asset": "breakfast_plate", **at(DINING, 3.6375, 6.181)},
    "buffet_tray_6": {"asset": "serving_tray", **at(DINING, 3.068, 6.586)},
    "buffet_tray_7": {"asset": "serving_tray", **at(DINING, 3.558, 6.586)},
    "party_plate_8": {"asset": "breakfast_plate", **at(DINING, 2.9885, 6.991)},
    "party_plate_9": {"asset": "breakfast_plate", **at(DINING, 3.313, 6.991)},
    "party_plate_10": {"asset": "breakfast_plate", **at(DINING, 3.6375, 6.991)},
    "buffet_tray_11": {"asset": "serving_tray", **at(DINING, 3.068, 7.396)},
    "buffet_tray_12": {"asset": "serving_tray", **at(DINING, 3.558, 7.396)},
    "party_bowl_1": {"asset": "breakfast_bowl", **at(DINING, 2.945, 7.765)},
    "party_bowl_2": {"asset": "breakfast_bowl", **at(DINING, 3.191, 7.765)},
    "party_bowl_3": {"asset": "breakfast_bowl", **at(DINING, 3.437, 7.765)},
    "party_bowl_4": {"asset": "breakfast_bowl", **at(DINING, 3.683, 7.765)},
}
T20_GOAL = {"all": [["on", "juice_bottle", DINING], ["upright", "juice_bottle"], ["hand_empty", "right"],
                    ["count_on_at_least", list(T20_TABLE), DINING, len(T20_TABLE) - 2]]}
HARD["T20_juice_back_to_table"] = {
    "variants": {"table_full": hard(
        "the bottle on the low wall cabinet; the dining table is covered by six trays, six plates and four bowls: no "
        "spot left for the bottle to stand", ["destination_full"],
        instruction="Find the juice bottle and put it back on the dining table, standing up; if needed, first make "
                    "room among the things on the table.",
        instruction_zh="找到果汁瓶，确保它直立放回餐桌；必要时先为桌面其他物品腾出空间。",
        goal=T20_GOAL, watch=["juice_bottle", *T20_TABLE],
        remove=["clutter_cereal_a", "clutter_cereal_b", "spoon_target_table"],
        move={"juice_bottle": at(CAB_TOP, 3.68, 0.36, 0)}, add=dict(T20_TABLE))},
    "routes": {
        "hard_make_room_first": {
            "kind": "alternative", "variants": ["table_full"],
            "recovery": "the table has no free spot: stack one bowl onto the tray beside it, bring the bottle back "
                        "in its place",
            "steps": [S("navigate", destination=DINING), S("look", target=DINING),
                      S("navigate", destination="party_bowl_1", role="insert"),
                      # square to the bowl first: from the navigate pose the rim pinch held once and slipped once
                      # while moving it (s10)
                      S("approach", target="party_bowl_1", role="insert"),
                      S("pick", object="party_bowl_1", role="insert"),
                      # onto the tray next to it (carried to the wall cabinet it slipped out of the hand, s10)
                      S("place", object="party_bowl_1", receptacle="buffet_tray_11", role="insert"),
                      # (physical detail, not part of the decision: arriving at the cabinet straight from the dining
                      # room, the pick tipped the bottle off and approach found no base pose (s10); arriving from the
                      # east (the TV stand side), as the Easy route does from the start pose, the pick holds)
                      S("navigate", destination=TV), S("navigate", destination=CAB_TOP), S("look", target=CAB_TOP),
                      S("navigate", destination="juice_bottle"), S("pick", object="juice_bottle"),
                      S("navigate", destination=DINING),
                      S("place", object="juice_bottle", receptacle=DINING, hint_xy=[2.945, 7.765])]},
        "naive_no_room": {"kind": "negative", "variants": ["table_full"], "note": "the Easy plan: place is refused",
                          "steps": [S("navigate", destination=CAB_TOP), S("look", target=CAB_TOP),
                                    S("navigate", destination="juice_bottle"), S("pick", object="juice_bottle"),
                                    S("navigate", destination=DINING),
                                    S("place", "fail", object="juice_bottle", receptacle=DINING)]}},
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
        if ext.get("blocker"):
            for name in ext["variants"]:
                t["variants"][name]["blocker"] = ext["blocker"]
    return tasks
