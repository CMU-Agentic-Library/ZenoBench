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

from benchmark.retired_skills import drop_retired_steps  # noqa: E402
from benchmark.v5.define_tasks_v5 import (FIELDS, OVERLAY, P, REC, S, _refresh_view,  # noqa: E402
                                          f_initial, f_joint, f_move, find, seed_vary)

V5 = ROOT / "benchmark/v5/tasks.json"
OUT = ROOT / "benchmark/v6/tasks.json"
SEEDS = list(range(10, 20))
TOMATOES = ["cherry_tomato_1", "cherry_tomato_2"]


# ----------------------------------------------------------------- helpers


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


def put_away(steps_before, art_first, art_second, take, steps_after):
    """Inspect two closed cabinets in the worse order, take the item from the second, close both."""
    return steps_before + open_explore(art_first) + [S("close", articulated=art_first)] + open_explore(art_second) \
        + take(art_second) + steps_after


# ----------------------------------------------------------------- per-task families
# T01: breakfast for three in one row along the east edge of the dining table (the edge the robot works from; a
# book is placed edge-held, so only edge slots count).  A row lists objects and free gaps (m) south to north;
# the layout names the gap beside a seat that is wide enough, and the plate the spoon lies behind.
DINING = "dining_table_2/top"
T01_TABLE_Y0, T01_TABLE_Y1 = 5.52, 7.935
T01_KIND = {"plate_counter_a": "plate", "plate_counter_b": "plate", "bowl_side_table": "bowl",
            "cup_side_table": "cup", "cup_counter_b": "cup", "mug_dining_cabinet": "mug",
            "clutter_cereal_a": "cereal", "clutter_cereal_b": "cereal"}
T01_LEN = {"plate_counter_a": 0.248, "plate_counter_b": 0.248, "bowl_side_table": 0.176, "cup_side_table": 0.11,
           "cup_counter_b": 0.11, "mug_dining_cabinet": 0.127, "clutter_cereal_a": 0.125, "clutter_cereal_b": 0.125}
T01_ROW_X = {"plate": 3.66}
T01_PLATES = ["bowl_side_table", "plate_counter_a", "plate_counter_b"]
T01_WARE6 = [*T01_KIND, "spoon_target_table"]
T01_UPRIGHT = ["cup_side_table", "cup_counter_b", "mug_dining_cabinet", "clutter_cereal_a", "clutter_cereal_b"]
NARROW, WIDE = 0.17, 0.34          # a book (12 cm along the edge) + 2 x 5 cm does not fit / fits
T01_LAYOUTS = {   # name: (row, index of the suitable gap, plate the spoon lies behind)
    # far south end | narrow between seats 1 and 2 | wide between seats 2 and 3 (suitable)
    "seats_a": ([0.30, "clutter_cereal_a", 0.05, "bowl_side_table", 0.04, "cup_side_table", NARROW, "plate_counter_a",
                 0.04, "cup_counter_b", WIDE, "plate_counter_b", 0.04, "mug_dining_cabinet", 0.05, "clutter_cereal_b"],
                5, "plate_counter_b"),
    # wide between seats 1 and 2 (suitable) | narrow between seats 2 and 3 | far north end beyond the cereal
    "seats_b": ([0.05, "plate_counter_a", 0.04, "cup_counter_b", WIDE, "bowl_side_table", 0.04, "cup_side_table",
                 NARROW, "plate_counter_b", 0.04, "mug_dining_cabinet", 0.05, "clutter_cereal_a", 0.05,
                 "clutter_cereal_b"], 2, "plate_counter_a"),
    # far south end beyond both cereal boxes | wide between the cereal and seat 1's plate (suitable) | narrow
    # between seats 2 and 3.  Seats 1 and 2 sit 5 cm apart, so the only wide slot beside a plate is south of seat 1;
    # it lies where seats_a and seats_b have tableware, so no one book position solves two layouts
    "seats_c": ([0.36, "clutter_cereal_a", 0.05, "clutter_cereal_b", WIDE, "plate_counter_a", 0.04, "cup_counter_b",
                 0.05, "bowl_side_table", 0.04, "cup_side_table", NARROW, "plate_counter_b", 0.04,
                 "mug_dining_cabinet"], 2, "plate_counter_a"),
}
HALF = (WIDE - 0.125) / 2          # either side of a cereal box standing in a wide slot: too narrow for the book
T01_FULL = {   # no_room_fallback: seats_a with the second cereal box in the one suitable slot
    "full_a": ([0.30, "clutter_cereal_a", 0.05, "bowl_side_table", 0.04, "cup_side_table", NARROW, "plate_counter_a",
                0.04, "cup_counter_b", HALF, "clutter_cereal_b", HALF, "plate_counter_b", 0.04, "mug_dining_cabinet"],
               "plate_counter_b"),
}
# "back to the kitchen counter": any kitchen worktop does (both counters, the island where there is one)
KITCHEN_WORKTOPS = ["kitchen_counter_1/top", "kitchen_counter_2/top", "kitchen_island/top"]
KITCHEN_WORKTOPS_DESK = ["kitchen_counter_1/top", "kitchen_counter_2/top"]     # tasks/desk_prep has no island
BLOCK_H = 0.04                         # the toy blocks' edge (annotations/assets.json wooden_block)
T01_BOOKCASES = [f"bookcase_{k}/{lv}" for k in (1, 2, 3, 4) for lv in ("top", "shelf_1", "shelf_0")]  # any bookcase
T01_FALLBACK = "bookcase_2/top"     # reference: the nearest bookcase (bedroom)
# reader_seat: three seats, each a plate or bowl and its drink north of it, with a wide slot south of every plate
# (beside that seat only: the next plate is 26 cm away); the coffee drinker's seat has the mug, the others a cup
T01_READER = {   # name: the seats south to north, (plate, drink)
    "mug_1": [("plate_counter_a", "mug_dining_cabinet"), ("bowl_side_table", "cup_side_table"),
              ("plate_counter_b", "cup_counter_b")],
    "mug_2": [("plate_counter_a", "cup_side_table"), ("bowl_side_table", "mug_dining_cabinet"),
              ("plate_counter_b", "cup_counter_b")],
    "mug_3": [("plate_counter_b", "cup_counter_b"), ("bowl_side_table", "cup_side_table"),
              ("plate_counter_a", "mug_dining_cabinet")],
}
# which_book: the book the guest read last night lies in the room the instruction names; another book lies in the
# other room and one on the island (where the book of the other T01 variants lies)
T01_BOOK_AT = {"living": ("tv_stand_2/top", [7.40, 0.484]),     # overhangs the north edge, toward the room
               "bedroom": ("bookcase_2/top", [1.00, -0.589])}   # overhangs the south edge, toward the room
T01_BOOK_OTHER = {"living": ("bookcase_2/top", [1.00, -0.43]), "bedroom": ("tv_stand_2/top", [7.60, 0.36])}
# which_table: the other dining table (the west dining room, 16 m from the island); its east edge faces the room
FAR_DINING = "dining_table_1/top"
T01_TABLES = {DINING: (T01_TABLE_Y0, T01_TABLE_Y1, 3.839), FAR_DINING: (6.89, 8.83, -7.488)}   # y0, y1, east edge x
T01_FAR_LAYOUTS = {   # the shorter table: one cereal box; narrow between seats 1 and 2, wide between 2 and 3
    "far_a": ([0.05, "clutter_cereal_a", 0.05, "plate_counter_a", 0.04, "cup_counter_b", NARROW, "bowl_side_table",
               0.04, "cup_side_table", WIDE, "plate_counter_b", 0.04, "mug_dining_cabinet"], 5, "plate_counter_b"),
    # wide between seats 1 and 2, narrow between 2 and 3
    "far_b": ([0.05, "plate_counter_a", 0.04, "cup_counter_b", WIDE, "bowl_side_table", 0.04, "cup_side_table", NARROW,
               "plate_counter_b", 0.04, "mug_dining_cabinet", 0.05, "clutter_cereal_a"], 2, "plate_counter_a"),
}
# the table nobody eats at: the kid's toys and the storage bin, east-edge slots free, no tableware
T01_IDLE = {DINING: {"wide_storage_bin": [2.985, 6.6], "clutter_cereal_b": [3.70, 6.0],
                     "wooden_block_a": [3.75, 6.9], "wooden_block_b": [3.62, 7.3]},
            FAR_DINING: {"wide_storage_bin": [-8.0, 7.9], "wooden_block_a": [-7.6, 7.2], "wooden_block_b": [-7.72, 7.6]}}


def T01(t):
    B = "paperback_book"
    # "the dining table": either dining table in the house will do where nothing tells them apart
    t["goal"] = {"all": [["on_any", B, ["dining_table_2/top", "dining_table_1/top"]], ["hand_empty", "right"]]}
    base = OR(t, "overhang_ready")                      # look, nav, approach, look, pick, nav table, place

    def table(seq, sup=DINING):
        """One row of tableware along the east edge of a dining table, south to north: an object name or a gap in
        metres.  Returns the poses and the centre y of every gap."""
        (y, y1, edge), poses, gaps = T01_TABLES[sup], {}, []
        dx = edge - T01_TABLES[DINING][2]                # the rows are given for the east edge of DINING
        for x in seq:
            if isinstance(x, float):
                gaps.append(round(y + x / 2, 3))
                y += x
                continue
            poses[x] = {"support": sup, "xy": [round(T01_ROW_X.get(T01_KIND[x], 3.70) + dx, 3),
                                               round(y + T01_LEN[x] / 2, 3)], "yaw_deg": 0.0}
            y += T01_LEN[x]
        if y > y1:
            raise ValueError(f"T01 table row too long: {y:.3f}")
        return poses, gaps

    def seats(poses, spoon_by):
        sup = poses[spoon_by]["support"]
        poses["spoon_target_table"] = {"support": sup, "xy": [round(3.40 + T01_TABLES[sup][2] - T01_TABLES[DINING][2], 3),
                                                              poses[spoon_by]["xy"][1]], "yaw_deg": 0.0}
        return poses

    def book_at(sup, y):
        return [round(3.72 + T01_TABLES[sup][2] - T01_TABLES[DINING][2], 3), y]

    carry = base[:5] + [nav(DINING), look(DINING)]
    cases, full = {}, {}
    for name, (seq, valid, spoon_by) in T01_LAYOUTS.items():
        poses, gaps = table(seq)
        cases[name] = dict(move={B: copy.deepcopy(t["variants"]["overhang_ready"]["move"][B]), **seats(poses, spoon_by)},
                           route=carry + [place(B, DINING, [3.72, gaps[valid]])])
    for name, (seq, spoon_by) in T01_FULL.items():      # a cereal box stands in the one suitable slot
        poses, _ = table(seq)
        full[name] = {B: copy.deepcopy(t["variants"]["overhang_ready"]["move"][B]), **seats(poses, spoon_by)}
    seat_goal = lambda moved=(), sup=DINING, ware=T01_WARE6, still=(): {"all": [  # noqa: E731
        ["on", B, sup], ["clear_of", B, list(ware), 0.05], ["near_any", B, T01_PLATES, 0.15],
        *[["near_start", n, 0.03] for n in [*ware, *still] if n not in moved],
        *[["on", n, sup] for n in moved],
        *[["upright", n] for n in T01_UPRIGHT if n in ware], ["hand_empty", "right"]]}

    # which_table: breakfast is set on one of the two dining tables, the other holds toys and the bin.  The robot
    # carries the book to the near table and looks; at the far setting it goes on to the west dining room.
    which = {}
    for name, seq, valid, spoon_by, sup in [("near_a", *T01_LAYOUTS["seats_a"], DINING),
                                            ("near_b", *T01_LAYOUTS["seats_b"], DINING),
                                            ("far_a", *T01_FAR_LAYOUTS["far_a"], FAR_DINING),
                                            ("far_b", *T01_FAR_LAYOUTS["far_b"], FAR_DINING)]:
        poses, gaps = table(seq, sup)
        idle = DINING if sup == FAR_DINING else FAR_DINING
        toys = {n: {"support": idle, "xy": xy, "yaw_deg": 0.0} for n, xy in T01_IDLE[idle].items()}
        ware = [n for n in T01_WARE6 if n in poses or n == "spoon_target_table"]
        route = base[:5] + [nav(DINING), look(DINING)] + ([nav(FAR_DINING), look(FAR_DINING)] if sup == FAR_DINING else [])
        which[name] = dict(move={B: copy.deepcopy(t["variants"]["overhang_ready"]["move"][B]), **seats(poses, spoon_by),
                                 **toys},
                           goal=seat_goal(sup=sup, ware=ware, still=[n for n in toys if n not in ware]),
                           route=route + [place(B, sup, book_at(sup, gaps[valid]))])
    reader = {}
    for name, row in T01_READER.items():
        seq = [x for plate, drink in row for x in (WIDE, plate, 0.04, drink)] + [0.05, "clutter_cereal_a"]
        poses, gaps = table(seq)
        k = next(i for i, (_, d) in enumerate(row) if d == "mug_dining_cabinet")
        mine, others = row[k][0], [p for p, _ in row if p != row[k][0]]
        poses["clutter_cereal_b"] = {"support": DINING, "xy": [3.15, 5.80], "yaw_deg": 0.0}  # the west half
        reader[name] = dict(
            move={B: copy.deepcopy(t["variants"]["overhang_ready"]["move"][B]), **seats(poses, mine)},
            goal={"all": [["on", B, DINING], ["clear_of", B, T01_WARE6, 0.05],
                          ["near_any", B, [mine, "mug_dining_cabinet"], 0.15], ["not near_any", B, others, 0.15],
                          *[["near_start", n, 0.03] for n in T01_WARE6], *[["upright", n] for n in T01_UPRIGHT],
                          ["hand_empty", "right"]]},
            route=carry + [place(B, DINING, [3.72, gaps[2 * k]])])     # the slot south of the seat's plate
    books = {}
    for room, (sup, xy) in T01_BOOK_AT.items():
        osup, oxy = T01_BOOK_OTHER[room]
        said = {"living": ("Last night the guest read for a while in the living room while watching TV and left "
                           "the book there.", "客人昨晚在客厅看电视时看了会儿书，看完就放在那儿了。"),
                "bedroom": ("Last night the guest read in the bedroom before going to sleep and left the book "
                            "there.", "客人昨晚睡前在卧室看书，看完就放在那儿了。")}[room]
        colour = {"living": "red", "bedroom": "green"}[room]
        if True:
            books[room] = dict(
                move={B: {"support": sup, "xy": list(xy), "yaw_deg": 90.0}},
                add={"book_island": {"asset": f"book_{colour}", "support": "kitchen_island/top", "xy": [7.30, 1.76],
                                     "yaw_deg": 0.0},
                     "book_other": {"asset": "book_blue", "support": osup, "xy": list(oxy), "yaw_deg": 0.0}},
                instruction=said[0] + " Bring that book to the dining table; they want to go on reading at breakfast. "
                                      "Apart from that book, do not move anything.",
                instruction_zh=said[1] + "把那本书拿到餐桌上，客人想边吃早饭边接着看。除了那本书，别的东西都别挪动。",
                goal={"all": [["on_any", B, [DINING, "dining_table_1/top"]], ["near_start", "book_island", 0.03],
                              ["near_start", "book_other", 0.03], ["hand_empty", "right"]]},
                route=[look("kitchen_island/top"), nav(sup), look(sup), nav(B), S("approach", target=B), look(B),
                       pick(B), nav(DINING), place(B, DINING, [3.72, 6.5])])
    # where the book goes is said (beside a guest's place, clear of the tableware); which free slot that is, and
    # whether the book fits there, the robot judges from what it sees
    suitable = dict(instruction="Breakfast is set on the dining table for the guests. Bring the paperback from the "
                                "island and put it beside one of the guests' places, so they can read while they "
                                "eat; leave some space between the book and the tableware, do not put it right "
                                "against it. Apart from the book, do not move anything.",
                    instruction_zh="餐桌上已经给客人摆好了早餐。请把岛台上的书拿过去，放在某位客人吃饭的位置旁边，"
                                   "方便边吃边看；书和餐具之间要留出空隙，不要挨着。除了这本书，别的东西都别挪动。")
    fams = {
        "table_seats": dict(
            base="table_set", control="overhang_ready", conditions=["spot_quality"], **suitable, keep_design=[DINING],
            goal=seat_goal(), watch=[B, *T01_WARE6],
            factor="which free slot on the set table is the suitable one (seed: one of three settings)",
            challenge="breakfast is set for three along the east edge of the dining table (a plate or bowl and a "
                      "drink per seat, two cereal boxes); the edge has several free slots: one too narrow between "
                      "two seats, one wide but at the far end beyond the cereal boxes, away from every seat, and "
                      "one wide slot beside a seat; the west half of the table is empty",
            rationale="a suitable place for a book at a breakfast table is beside a seat (within 15 cm of a plate "
                      "or bowl) and clear of the tableware (5 cm): look at the table, judge the slots and put it in "
                      "the one beside a seat; which slot that is changes with the setting",
            cases=cases),
        "which_table": dict(
            base="overhang_ready", control="overhang_ready",
            conditions=["destination_unnamed", "spot_quality"], keep_design=[DINING, FAR_DINING],
            remove=["spoon_side_table"], watch=[B, *T01_WARE6, "wide_storage_bin", "wooden_block_a", "wooden_block_b"],
            instruction="The guests are having breakfast. Bring the paperback from the kitchen island to the table "
                        "where they are eating and put it beside one of the guests' places, so they can read while "
                        "they eat; leave some space between the book and the tableware, do not put it right against "
                        "it. Apart from the book, do not move anything.",
            instruction_zh="客人正在吃早饭。把岛台上的书拿到他们吃饭的那张桌子上，放在某位客人的位置旁边，方便边吃边看；"
                           "书和餐具之间要留出空隙，不要挨着。除了这本书，别的东西都别挪动。",
            factor="which of the two dining tables the guests eat at, and its setting (seed: one of four)",
            challenge="the house has two dining tables, the near one "
                      "(6 m) and one in the west dining room (16 m); breakfast for three is set on one of them, the "
                      "other holds the kid's toys and the storage bin and has free edge slots too; the instruction "
                      "does not say which table",
            rationale="find the table the guests eat at: look at the near table, and if no places are set there go on to the other dining room; there "
                      "judge the slots as in table_seats.  Putting the book on the idle table fails",
            cases=which),
        "no_room_fallback": dict(
            base="table_set", control="table_seats", conditions=["spot_quality", "infeasible_fallback"],
            keep_design=[DINING], watch=[B, *T01_WARE6],
            instruction=suitable["instruction"][:-1] + "; if there is no such place on the table, put the book away "
                        "on a bookcase instead.",
            instruction_zh=suitable["instruction_zh"][:-1] + "；要是桌上没有这样的位置，就把书放到书柜收起来。",
            factor="whether the set table has a suitable slot (seed: two settings with one, one with a cereal box in "
                   "it)",
            challenge="breakfast is set for three as in table_seats; in one layout of three a cereal box stands in "
                      "the one wide slot beside a seat, so no slot is both beside a seat and clear of the tableware; "
                      "the instruction forbids moving the tableware and the cereal and names a fallback place",
            rationale="judge the table first: if a slot beside a seat fits, use it (the fallback then fails); if "
                      "none fits, the goal cannot be met under the constraint: take the named fallback, a bookcase "
                      "(any one, any level), instead of clearing the slot (moving the cereal box fails)",
            cases={**{n: dict(move=cases[n]["move"], goal=seat_goal(), route=cases[n]["route"])
                      for n in ("seats_b", "seats_c")},
                   **{n: dict(move=mv, goal={"any": [[["on", B, bc]] for bc in T01_BOOKCASES], "all": [
                                                     *[["near_start", x, 0.03] for x in T01_WARE6],
                                                     *[["upright", x] for x in T01_UPRIGHT], ["hand_empty", "right"]]},
                              route=carry + [nav(T01_FALLBACK), place(B, T01_FALLBACK, [1.15, -0.43])])
                      for n, mv in full.items()}}),
        "reader_seat": dict(
            base="table_set", control="table_seats", conditions=["referent_clue", "spot_quality"],
            keep_design=[DINING], watch=[B, *T01_WARE6],
            instruction="Breakfast is set on the dining table for the guests. The paperback on the island belongs to "
                        "the guest who drinks coffee from a mug with a handle in the morning (the others have cups without "
                        "a handle): put it beside "
                        "that guest's place, so they can read while they eat; leave some space between the book and "
                        "the tableware. Apart from the book, do not move anything.",
            instruction_zh="餐桌上已经给客人摆好了早餐。岛台上那本书是早上用带把手的马克杯喝咖啡的那位客人的（另外两位用的是没把手的杯子），"
                           "把它放在那位客人的位置旁边，方便边吃边看；书和餐具之间要留出空隙。除了这本书，别的东西都别挪动。",
            factor="which seat has the coffee mug (seed: one of three)",
            challenge="three seats, each a plate or bowl with its drink, and a wide free slot beside every seat; one "
                      "seat has a coffee mug (with a handle), the other two a cup without one; the instruction says the "
                      "guest drinks coffee from the mug with a handle, not which seat that is",
            rationale="every seat has room, so the slot alone does not decide: find the seat with the mug and put the "
                      "book in the slot beside it (within 15 cm of its plate or mug, not within 15 cm of another "
                      "seat's plate); which seat that is changes with the seed",
            cases=reader),
        "which_book": dict(
            base="overhang_ready", control="overhang_ready", conditions=["referent_clue", "item_out_of_view"],
            watch=[B, "book_island", "book_other"],
            factor="the room the guest read in (seed: living room or bedroom)",
            challenge="a book lies on the island; the guest's book is in the room they read in last night (on the TV "
                      "stand in the living room, or on the bookcase in the bedroom), and the other room has a "
                      "third book; the instruction names only the room and the occasion",
            rationale="the nearest book is not the one meant: go to the room the instruction names, take the book "
                      "there and bring it to the dining table; the island book and the book in the other room stay",
            cases=books),
    }
    for vid in T01_FLAT_TWINS:                           # every layout also with the book lying flat
        spec = fams[vid]
        conds = [*spec["conditions"], "no_overhang"]
        spec["cases"].update({f"{n}_flat": flat_book(c, conds) for n, c in list(spec["cases"].items())})
        spec["factor"] += "; and whether the book overhangs the island's edge or lies flat on it (Action: expose it)"
    return fams


# T01 variants whose book starts on the island: every layout also comes with the book flat, 1.5 cm over the front
# edge (v5 no_overhang), so the edge pinch needs it pushed out first (expose: Action at the island)
T01_FLAT_TWINS = ("table_seats", "which_table", "no_room_fallback", "reader_seat")
T01_FLAT_BOOK = {"support": "kitchen_island/top", "xy": [7.62, 1.59], "yaw_deg": 90}


def flat_book(case, conds):
    """A T01 case with the paperback flat on the island: expose it, look, then pick (route otherwise the same)."""
    B = "paperback_book"
    c = copy.deepcopy(case)
    c["move"] = {**c.get("move", {}), B: copy.deepcopy(T01_FLAT_BOOK)}
    r = c["route"]
    i = next(k for k, st in enumerate(r) if st["skill"] == "navigate" and st["args"].get("destination") == B)
    j = next(k for k in range(i + 1, len(r)) if r[k]["skill"] == "pick" and r[k]["args"].get("object") == B)
    c["route"] = r[:i + 1] + [S("expose", object=B), look(B)] + r[j:]
    c["conditions"] = list(conds)
    return c


def T02(t):
    A, B, F = "wooden_block_a", "wooden_block_b", "floor_block"
    # three-block tower: block A at the edge (edge_base), block B in the open, the floor block put on the island
    tower_goal = {"any": [[["on_top_of", m, b], ["on_top_of", top, m], ["away_from_edge", b, 0.05],
                           ["on", b, "kitchen_island/top"]]
                          for b in (B, F) for m in (A, B, F) for top in (A, B, F) if len({b, m, top}) == 3],
                  "all": [["hand_empty", "right"]]}
    # third_toy_elsewhere: a three-level tower of the kid's toys; two blocks are on the island, there is no third
    # block in the house; another toy of the kid's (the rubber duck or a toy block of another make) is in another
    # room and does as the third level.  The block-sized sponge next to the blocks is no toy.
    sponge = {"kitchen_sponge": P("kitchen_island/top", 6.95, 1.85)}       # moved: never left out by the seed
    def toy_tower(x):
        """A, B and the substitute x; the duck has no flat top, so it can only be the top level."""
        trio = (A, B) if x == "rubber_duck" else (A, B, x)
        return {"any": [[["on_top_of", m, b], ["on_top_of", top, m], ["on", b, "kitchen_island/top"]]
                        for b in trio for m in (A, B, x) for top in (A, B, x)
                        if len({b, m, top}) == 3 and (x != "rubber_duck" or top == x)],
                "all": [["hand_empty", "right"]]}
    # tower_for_kid: the three blocks are spread over the house; the tower goes on the dining table, whose bin,
    # cereal boxes and spoon stay where they are, the base 5 cm from the edge and clear of them
    table_ware = ["wide_storage_bin", "clutter_cereal_a", "clutter_cereal_b", "spoon_target_table"]
    table_tower = {"any": [[["on_top_of", m, b], ["on_top_of", top, m], ["on", b, DINING],
                            ["away_from_edge", b, 0.05], ["clear_of", b, table_ware, 0.05]]
                           for b in (A, B, F) for m in (A, B, F) for top in (A, B, F) if len({b, m, top}) == 3],
                   "all": [*[["near_start", n, 0.03] for n in table_ware], ["hand_empty", "right"]]}
    # tower_for_kid_duck: no third block; the rubber duck tops the two blocks
    duck_table_tower = {"any": [[["on_top_of", m, b], ["on_top_of", "rubber_duck", m], ["on", b, DINING],
                                 ["away_from_edge", b, 0.05], ["clear_of", b, table_ware, 0.05]]
                                for b, m in ((A, B), (B, A))],
                        "all": copy.deepcopy(table_tower["all"])}
    base_xy = [3.70, 6.60]                       # 14 cm in from the east edge, clear of the bin and the cereal boxes
    def table_route(second, r2, third, r3):
        """Block A from the island as the base on the dining table, then the other two in turn."""
        return [look("kitchen_island/top"), nav(A), pick(A), nav(DINING), look(DINING), place(A, DINING, base_xy),
                S("search", object=second, region=r2), nav(second), pick(second), nav(A), S("approach", target=A),
                S("stack", object=second, base=A),
                S("search", object=third, region=r3), nav(third), pick(third), nav(A), S("approach", target=A),
                S("stack", object=third, base=second)]
    TV, COUNTER, DESK = P("tv_stand_2/top", 7.6, 0.36), P("kitchen_counter_2/top", -0.1, 7.3), P("desk_1/top", -0.7, -6.0)
    # block_put_away: as edge_base (A at the edge, B in the open), the third block put away in a closed low cabinet
    in_cab = {"kitchen_cabinet_4": {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 0.0},
              "kitchen_cabinet_6": {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.5, 0.36], "yaw_deg": 0.0}}
    put_away_goal = copy.deepcopy(tower_goal)
    put_away_goal["all"] += [["is_closed", "kitchen_cabinet_4"], ["is_closed", "kitchen_cabinet_6"]]
    edge_two = OR(t, "edge_base")                # look, nav A, pick A, nav B, approach B, stack A on B
    # crowded_use_another: block B is wedged between the full oatmeal bowl and the rolling pin; the instruction
    # only says not to disturb what is around the full bowl; that a third block exists the robot finds out itself.  In the loose
    # layout B stands clear of them and the two island blocks are stacked; the other block stays.
    crowd = copy.deepcopy(t["variants"]["crowded"]["move"])          # oatmeal, rolling pin, A, B (3 mm gaps)
    keep = ["oatmeal", "rolling_pin"]
    pair = lambda x, y: {"any": [[["on_top_of", x, y]], [["on_top_of", y, x]]]}  # noqa: E731
    crowd_cases = {}
    for c, (pose, region) in {"tight_tv": (TV, "living_room_0_0"),
                              "tight_dining": (P(DINING, 3.7, 6.3), "dining_room_0_1")}.items():
        crowd_cases[c] = dict(
            move={**crowd, F: pose},
            goal={**pair(A, F), "all": [*[["near_start", n, 0.02] for n in (B, *keep)], ["upright", "oatmeal"],
                                        ["hand_empty", "right"]]},
            route=[look("kitchen_island/top"), nav(B), look(B), S("search", object=F, region=region), nav(F), pick(F),
                   nav(A), S("approach", target=A), S("stack", object=F, base=A)])
    crowd_cases["loose"] = dict(
        move={**crowd, B: P("kitchen_island/top", 7.45, 1.80), F: TV},
        goal={"any": [[["on_top_of", x, y]] for x in (A, B, F) for y in (A, B, F) if x != y],
              "all": [*[["near_start", n, 0.02] for n in keep], ["upright", "oatmeal"], ["hand_empty", "right"]]},
        route=[look("kitchen_island/top"), nav(B), pick(B), S("rotate", object=B, degrees=30), nav(A),
               S("approach", target=A), S("stack", object=B, base=A)])
    return {
        "crowded_use_another": dict(
            base="crowded", control="clear", conditions=["infeasible_fallback", "not_in_view"],
            instruction="Stack two of the kid's wooden blocks on top of each other. The bowl of oatmeal on the island "
                        "is filled to the brim; do not disturb the things around it, or it will spill.",
            instruction_zh="把孩子的两块木积木叠起来。岛台上那碗燕麦盛得很满，别碰它周围的东西，免得洒出来。",
            watch=[A, B, F, *keep],
            factor="whether block B is wedged in (seed: tight with the other block on the TV stand or the dining "
                   "table, or loose)",
            challenge="block B lies 3 mm from the full oatmeal bowl and the rolling pin; the instruction only says "
                      "not to disturb what is around the bowl: it names neither the wedged block nor the other "
                      "block elsewhere in the house",
            rationale="look at B first: wedged, the local fix (separate) is ruled out, so find the other block and "
                      "stack it with A; B, the bowl and the pin stay.  When B is loose, stack the two island blocks "
                      "and leave the other block where it is",
            cases=crowd_cases),
        "third_toy_elsewhere": dict(
            base="clear", control="clear", conditions=["missing_piece", "not_in_view"],
            instruction="Build the kid a three-level tower out of their toys on the kitchen island.",
            instruction_zh="用孩子的玩具在岛台上搭一座三层的小塔。",
            remove=[F], move=sponge,
            factor="which toy stands in for the third block and where (seed: the rubber duck on the dining table or "
                   "a toy block on the kitchen counter)",
            challenge="only two toy blocks are in the house, both on the island; the block-sized sponge next to them "
                      "is no toy; another of the kid's toys (the rubber duck or a toy block of another make) is in "
                      "another room, out of view",
            rationale="the tower needs three toys and there is no third block: do not stop at two and do not use the "
                      "sponge; any toy of the kid's does as the third level, so find one in another room and put it "
                      "on top (the duck has no flat top: it can only be the top level)",
            cases={c: dict(add={x: {"asset": x, "support": sup, "xy": list(xy), "yaw_deg": 0.0}},
                           goal=toy_tower(x), watch=[A, B, x, "kitchen_sponge"],
                           route=OR(t, "clear") + recs(S("search", object=x, region=region), nav(x), pick(x), nav(A),
                                                       S("approach", target=A), S("stack", object=x, base=B)))
                   for c, x, sup, xy, region in (("duck", "rubber_duck", "dining_table_2/top", (3.7, 6.3),
                                                  "dining_room_0_1"),
                                                 ("toy_block", "toy_block", "kitchen_counter_2/top", (-0.1, 7.3),
                                                  "kitchen_0_1"))}),
        "tower_for_kid": dict(
            base="clear", control="clear", conditions=["item_out_of_view", "spot_quality"],
            instruction="The kid wants to look at a block tower on the dining table. Find all three toy blocks in the "
                        "house and stack them into one tower on the dining table.",
            instruction_zh="孩子想在餐桌上看积木塔。把家里三块积木都找到，在餐桌上叠成一座塔。",
            goal=table_tower, watch=[A, B, F, *table_ware], keep_design=[DINING],
            factor="where the other two blocks are (seed: the TV stand and the kitchen counter, or the TV stand and "
                   "the study desk)",
            challenge="the three blocks are spread over the house: one on the island, one on the TV stand, one on a "
                      "table in another room (out of view); the dining table holds the storage bin, two cereal "
                      "boxes and a spoon",
            rationale="find all three (one is out of view), carry them one at a time with one hand and order the "
                      "trips; the first block is the base: put it on a free spot of the dining table away from the "
                      "edge and clear of the bin and the boxes, then stack the other two on it; the table's things "
                      "stay where they are",
            cases={"counter": dict(move={A: P("kitchen_island/top", 7.22, 1.625), B: TV, F: COUNTER},
                                   route=table_route(B, "living_room_0_0", F, "kitchen_0_1")),
                   "study": dict(move={A: P("kitchen_island/top", 7.22, 1.625), F: TV, B: DESK},
                                 route=table_route(F, "living_room_0_0", B, "living_room_0_1"))}),
        "tower_for_kid_duck": dict(
            base="clear", control="tower_for_kid", conditions=["missing_piece", "item_out_of_view", "spot_quality"],
            instruction="The kid wants to look at a three-level tower on the dining table. Build one there out of "
                        "the kid's toys.",
            instruction_zh="孩子想在餐桌上看一座三层的塔，用他的玩具在餐桌上搭一座。",
            remove=[F], goal=duck_table_tower, watch=[A, B, "rubber_duck", *table_ware], keep_design=[DINING],
            factor="where the second block and the duck are (seed: block on the TV stand and duck on the kitchen "
                   "counter, or block on the study desk and duck on the TV stand)",
            challenge="only two toy blocks are in the house: one on the island, one on the TV stand or the study "
                      "desk; the rubber duck is on the kitchen counter or the TV stand; the dining table holds the "
                      "storage bin, two cereal boxes and a spoon",
            rationale="as tower_for_kid, but after finding two blocks the robot must notice there is no third and "
                      "bring the duck instead; the duck has no flat top, so it is the top level, and it is fetched "
                      "last",
            cases={"counter": dict(move={A: P("kitchen_island/top", 7.22, 1.625), B: TV},
                                   add={"rubber_duck": {"asset": "rubber_duck", **COUNTER}},
                                   route=table_route(B, "living_room_0_0", "rubber_duck", "kitchen_0_1")),
                   "study": dict(move={A: P("kitchen_island/top", 7.22, 1.625), B: DESK},
                                 add={"rubber_duck": {"asset": "rubber_duck", **TV}},
                                 route=table_route(B, "living_room_0_1", "rubber_duck", "living_room_0_0"))}),
        "block_put_away": dict(
            base="edge_base", control="clear", conditions=["unstable_base", "not_in_view"],
            instruction="Stack the three toy blocks into one tower on the kitchen island. I put one of them away in "
                        "a low cabinet along the living-room wall; close the cabinet doors again afterwards.",
            instruction_zh="把三块积木在岛台上叠成一座塔。有一块我收进客厅靠墙的矮柜里了，找完把柜门关好。",
            goal=put_away_goal, watch=[A, B, F], remove=["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"],
            factor="which closed low cabinet holds the third block (seed: cabinet 4 or 6)",
            challenge="two blocks on the island, block A at the edge (5 mm over it, it must not be the base); the "
                      "third block was put away in one of the two closed low kitchen cabinets",
            rationale="at the island: stack A on B, not B on A (Action); then open the cabinets one by one until the "
                      "block is found, close each again, and put the block on top (Task)",
            cases={f"in_{cab[-1]}": dict(
                move={F: in_cab[cab]},
                failures=[f_initial("resource", [["on", F, f"{cab}/inside_shelf"]], fid="resource_block_in_cabinet")],
                route=edge_two + open_explore(other) + [S("close", articulated=other)] + open_explore(cab)
                + [nav(F), pick(F), S("retreat", obstacle=cab, distance_m=0.3), S("close", articulated=cab),
                   nav(A), S("approach", target=A), S("stack", object=F, base=A)])
                for cab, other in (("kitchen_cabinet_4", "kitchen_cabinet_6"), ("kitchen_cabinet_6", "kitchen_cabinet_4"))}),
    }


def T04(t):
    C = "cup_counter_b"
    # h_task_spot_taken (from v5): the bowl sat 15 cm from the lid, room enough for the cup (11 cm), so nothing had
    # to be moved.  Centred in the free stretch it leaves 8 cm either side: no spot fits a cup until it is moved
    t["variants"]["h_task_spot_taken"]["move"]["oatmeal"]["xy"] = [3.629, 0.36]
    base = OR(t, "cup_available")                       # look, nav cup, pick cup, nav cab6, place cup
    # any cup or mug in the house set out upright on the drinks spot does what is asked (a mug is a cup too)
    t["goal"] = {"any": [[["on", x, "kitchen_cabinet_6/top"], ["upright", x]]
                         for x in (C, "mug", "mug_dining_cabinet", "mug_shelf", "mug_counter")],
                 "all": [["hand_empty", "right"]]}
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
    SPOT = "kitchen_cabinet_6/top"
    MUGS = ["mug", "mug_dining_cabinet", "mug_shelf", "mug_counter"]       # every mug in the house
    away = {"dining": (P("dining_table_2/top", 3.7, 6.3), "dining_room_0_1"),
            "study": (P("desk_1/top", -0.7, -6.0), "living_room_0_1")}
    # two_guests: two drinks, one cup in the house; a mug (in another room) for the second
    two_goal = {"any": [[["on", C, SPOT], ["upright", C], ["on", m, SPOT], ["upright", m], ["clear_of", C, [m], 0.03]]
                        for m in MUGS], "all": [["hand_empty", "right"]]}
    two_cases = {c: dict(move={"mug": pose},
                         route=base[:4] + [place(C, SPOT, [3.36, 0.36]), S("search", object="mug", region=region),
                                           nav("mug"), pick("mug"), nav(SPOT), place("mug", SPOT, [3.62, 0.36])])
                 for c, (pose, region) in away.items()}
    # clear_the_drinks_spot: breakfast is over and the bowl of oatmeal and the pot lid were left on the drinks spot;
    # tidy them back to the kitchen and set out a cup.  Which things are meant ("the used kitchen things") and where
    # the kitchen is the robot works out; the cup then has room.
    KITCHEN = ["kitchen_island/top", "kitchen_stove/top", "kitchen_counter_1/top", "kitchen_counter_2/top"]
    ISL = "kitchen_island/top"
    spot_route = [look(ISL), nav(SPOT), look(SPOT), nav("oatmeal"), pick("oatmeal"), nav(ISL),
                  place("oatmeal", ISL, [6.70, 1.84]), nav("pot_lid"), pick("pot_lid"), nav(ISL),
                  place("pot_lid", ISL, [7.10, 1.85]), nav(C), pick(C), nav(SPOT), place(C, SPOT)]
    return {
        "clear_the_drinks_spot": dict(
            base="h_task_spot_taken", control="cup_available", conditions=["goal_items_unstated", "destination_occupied"],
            instruction="Breakfast is over. Tidy away the used kitchen things on the low wall cabinet and set out a "
                        "cup there; a guest is coming for tea soon.",
            instruction_zh="早餐结束了，把靠墙矮柜上用过的餐厨用品收拾好，放上杯子，待会儿客人要来喝茶。",
            goal={"any": [[["on", x, SPOT], ["upright", x]] for x in (C, *MUGS)],
                  "all": [["on_any", "oatmeal", KITCHEN], ["on_any", "pot_lid", KITCHEN], ["upright", "oatmeal"],
                          ["hand_empty", "right"]]},
            watch=[C, *MUGS, "oatmeal", "pot_lid"],
            challenge="the bowl of oatmeal and the pot lid were left on the drinks spot after breakfast and fill it; "
                      "the instruction does not name them nor say where the kitchen things go",
            rationale="the used kitchen things on the cabinet are the oatmeal bowl and the pot lid: take both back to "
                      "the kitchen (island, stove or a counter), then set a cup on the cleared spot",
            cases={"": dict(route=spot_route)}),
        "two_guests": dict(
            base="cup_available", control="cup_available", conditions=["missing_piece", "not_in_view"],
            instruction="Two guests are coming. Set out two cups at the drinks spot on the low wall cabinet, not touching each other.",
            instruction_zh="有两位客人要来。在靠墙矮柜上的饮品角摆两个杯子，两个别挨着。",
            goal=two_goal, watch=[C, *MUGS],
            factor="where the mug is (seed: the dining table or the study desk)",
            challenge="two drinks are needed and the house has one cup (on the island); the mug is in another room, "
                      "out of view",
            rationale="set out the cup, notice there is no second cup, and fetch a mug from another room for the "
                      "second place; the two stand apart on the spot",
            cases=two_cases),
        "x6_gd_cup_in_cabinets": dict(
            base="no_cup", control="no_cup",
            factor="which cabinet holds the preferred item",
            instruction="A guest is coming. Set out a cup without a handle at the drinks spot on the low wall "
                        "cabinet; such cups are kept in the low kitchen cabinets. Close the cabinets again.",
            instruction_zh="有客人要来。在靠墙矮柜上的饮品角摆一个不带把手的杯子，这种杯子收在厨房的矮柜里。用完把柜门关好。",
            challenge="the mug (with a handle) is in plain view, but a cup without a handle is asked for and those are "
                      "kept in closed cabinets: the cup is in one of the two (seed decides which)",
            rationale="the visible substitute must not end the search: the cabinets are inspected until the cup is "
                      "found (reference route: the worse order, the cup is in the second cabinet)",
            goal=cab_goal, cases=cup_cases),
    }


def T05(t):
    # every instruction names the one kind of pen wanted, no "if there is no pen, a pencil" fallback
    PENCIL_TXT = ("The kid needs a pencil for homework. Bring a pencil to the study desk.",
                  "孩子写作业要用铅笔，拿一支铅笔到书房书桌上。")
    PEN_TXT = ("The kid needs a pen for homework. Bring a pen to the study desk.",
               "孩子写作业要用钢笔，拿一支钢笔到书房书桌上。")
    t["instruction"], t["instruction_zh"] = PENCIL_TXT
    tail_desk = [nav("desk_1/top"), place("pencil", "desk_1/top")]
    two_cab = ("The kid needs a pen for homework. Bring a pen to the study desk. Pens and pencils are kept in the "
               "two low kitchen cabinets; close them again afterwards.")
    in4 = {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 90}

    def fetch(x, art):
        return [nav(x), pick(x), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]
    pen4 = open_explore("kitchen_cabinet_6") + [S("close", articulated="kitchen_cabinet_6")] \
        + open_explore("kitchen_cabinet_4") + fetch("pen", "kitchen_cabinet_4") + [nav("desk_1/top"), place("pen", "desk_1/top")]
    pen6 = open_explore("kitchen_cabinet_4") + [S("close", articulated="kitchen_cabinet_4")] \
        + open_explore("kitchen_cabinet_6") + fetch("pen", "kitchen_cabinet_6") + [nav("desk_1/top"), place("pen", "desk_1/top")]
    pen_goal = {"all": [["on", "pen", "desk_1/top"], ["hand_empty", "right"], ["is_closed", "kitchen_cabinet_6"],
                        ["is_closed", "kitchen_cabinet_4"]]}
    # ---- reasoning about the goal itself: already met, how many, which items, in which order
    DESK = "desk_1/top"
    BOOK, DT, TV, KC = "bookcase_2/top", "dining_table_2/top", "tv_stand_2/top", "kitchen_counter_2/top"
    REG = {BOOK: "bedroom_0_1", DT: "dining_room_0_1", TV: "living_room_0_0", KC: "kitchen_0_1"}
    PENCIL0 = P(BOOK, 0.9646, -0.4948, -72.1)            # the pencil where the base scene has it (bedroom bookcase)

    def put(name, sup, x, y, yaw=0.0, asset=None):
        """A pose (move) or, with ``asset``, an added object."""
        return {name: {**({"asset": asset} if asset else {}), "support": sup, "xy": [x, y], "yaw_deg": yaw}}

    def fetch_to(x, sup, hint, flat=False):
        grab = [nav(x), S("expose", object=x), look(x), pick(x)] if flat else [nav(x), pick(x)]
        return [S("search", object=x, region=REG[sup])] + grab + [nav(DESK), place(x, DESK, hint)]
    desk_x = [-1.2, -0.9, -0.6, -0.3]

    # check_desk_first: what the instruction asks for is already on the desk (the usual instruction)
    check_cases = {
        "pen_on_desk": dict(move={"pen": P(DESK, -0.65, -5.95, 90.0), "pencil": PENCIL0},
                            goal={"all": [["on", "pen", DESK], ["near_start", "pen", 0.10], ["near_start", "pencil", 0.03],
                                          ["hand_empty", "right"]]},
                            watch=["pen", "pencil"]),
        # a pencil lies on the desk, the pen asked for is on the bedroom bookcase: what is there does not count
        "pencil_on_desk": dict(move={"pencil": P(DESK, -0.65, -5.95, 90.0), "pen": P(BOOK, 0.96, -0.49, -72.1)},
                               goal={"all": [["on", "pen", DESK], ["near_start", "pencil", 0.10],
                                             ["hand_empty", "right"]]},
                               watch=["pen", "pencil"])}
    check_cases["pen_on_desk"]["route"] = [nav(DESK), look(DESK), S("identify", object="pen")]   # already there: stop
    check_cases["pencil_on_desk"]["route"] = [nav(DESK), look(DESK), S("identify", object="pencil"),
                                              S("search", object="pen", region=REG[BOOK]), nav("pen"), pick("pen"),
                                              nav(DESK), place("pen", DESK, [-0.30, -5.95])]

    # all_pens: every pen and pencil in the house to the desk; how many there are is not said (seed: 2, 3 or 4)
    spots = [("pencil", BOOK, (0.96, -0.49, -72.1), None), ("pen", DT, (3.6, 6.6, 0.0), None),
             ("pencil_2", TV, (7.2, 0.36, 0.0), "pencil"), ("pen_2", KC, (-0.1, 7.2, 0.0), "pen")]
    all_cases = {}
    for n, case in ((2, "two"), (3, "three"), (4, "four")):
        mv, add = {}, {}
        for name, sup, (x, y, yaw), asset in spots[:n]:
            (add if asset else mv).update(put(name, sup, x, y, yaw, asset))
        names = [s_[0] for s_ in spots[:n]]
        all_cases[case] = dict(
            move=mv, add=add, watch=names,
            goal={"all": [*[["on", x, DESK] for x in names], ["hand_empty", "right"]]},
            route=[x for i, (name, sup, *_r) in enumerate(spots[:n]) for x in fetch_to(name, sup, [desk_x[i], -5.95])])

    # homework_ready: the instruction names the purpose only; the seed sets how many writing things and notebooks
    # there are (one of each, several, no pen); a book is no notebook, the teddy is no homework thing
    TOOLS = ["pen", "pencil", "pen_2"]
    NBS = ["notebook_1", "notebook_2"]
    ready_layouts = {
        "single": ({**put("pen", BOOK, 1.15, -0.40)},
                   {**put("notebook_1", DT, 3.6, 6.5, asset="notebook"), **put("teddy_bear", BOOK, 0.85, -0.45, asset="teddy_bear"),
                    **put("book_red", DT, 3.65, 6.85, asset="book_red")},
                   ["pencil"], [("pen", BOOK, False), ("notebook_1", DT, True)]),
        "several": ({**put("pen", BOOK, 1.15, -0.40), "pencil": PENCIL0},
                    {**put("pen_2", TV, 6.9, 0.36, asset="pen"), **put("notebook_1", DT, 3.6, 6.5, asset="notebook"),
                     **put("notebook_2", TV, 7.9, 0.36, asset="notebook"),
                     **put("teddy_bear", TV, 7.35, 0.36, asset="teddy_bear"), **put("book_red", DT, 3.65, 6.85, asset="book_red")},
                    [], [("pen", BOOK, False), ("notebook_2", TV, True)]),          # the nearer notebook
        "pencil_only": ({**put("pencil", DT, 3.3, 5.8)},
                        {**put("notebook_1", BOOK, 1.0, -0.45, asset="notebook"),
                         **put("teddy_bear", TV, 7.35, 0.36, asset="teddy_bear"), **put("book_red", DT, 3.65, 6.85, asset="book_red")},
                        ["pen"], [("notebook_1", BOOK, True), ("pencil", DT, False)]),
    }
    ready_cases = {}
    for case, (mv, add, rm, order) in ready_layouts.items():
        tools = [x for x in TOOLS if x in mv or x in add]
        nbs = [x for x in NBS if x in add]
        ready_cases[case] = dict(
            move=mv, add=add, remove=rm, watch=[*tools, *nbs, "teddy_bear", "book_red"],
            goal={"any": [[["on", w, DESK], ["on", nb, DESK]] for w in tools for nb in nbs],
                  "all": [["near_start", "teddy_bear", 0.05], ["near_start", "book_red", 0.05], ["hand_empty", "right"]]},
            route=[x for i, (name, sup, flat) in enumerate(order) for x in fetch_to(name, sup, [desk_x[1 + i], -5.95], flat)])

    # pens_per_notebook: one writing thing beside each notebook on the desk; the number is read off the desk (seed:
    # 2 or 3 notebooks); four writing things around the house, so it is not "bring them all"
    W4 = {**{"pen": P(BOOK, 1.15, -0.40), "pencil": PENCIL0}}
    W4_add = {**put("pen_2", TV, 7.2, 0.36, asset="pen"), **put("pencil_2", DT, 3.6, 6.6, asset="pencil")}
    W_ALL = ["pencil", "pen", "pen_2", "pencil_2"]
    W_SUP = {"pencil": BOOK, "pen": BOOK, "pen_2": TV, "pencil_2": DT}
    from itertools import combinations
    per_cases = {}
    for n, xs in ((2, [-1.0, -0.45]), (3, [-1.15, -0.72, -0.29])):
        nbs = {f"hw_notebook_{i + 1}": {"asset": "notebook", "support": DESK, "xy": [x, -5.92], "yaw_deg": 0.0}
               for i, x in enumerate(xs)}
        per_cases[f"notebooks_{n}"] = dict(
            move=copy.deepcopy(W4), add={**copy.deepcopy(W4_add), **nbs}, watch=[*W_ALL, *nbs],
            goal={"any": [[*[["on", w, DESK] for w in sub], *[["near_start", w, 0.03] for w in W_ALL if w not in sub]]
                          for sub in combinations(W_ALL, n)],
                  "all": [*[["near_any", nb, W_ALL, 0.10] for nb in nbs], ["hand_empty", "right"]]},
            route=[x for i, w in enumerate(W_ALL[:n]) for x in fetch_to(w, W_SUP[w], [round(xs[i] + 0.15, 3), -5.92])])

    # errand_combined: bring a pen to the desk and take the used mug on the desk back to the kitchen counter; the
    # pen first, so the trip to the desk also starts the mug's
    MUG = "used_mug"
    errand_cases = {c: dict(move={"pen": P(sup, *xy)},
                            route=fetch_to("pen", sup, [-0.75, -5.95])
                            + [pick(MUG), nav(KC), place(MUG, KC, [-0.15, 7.3])])
                    for c, sup, xy in (("pen_bedroom", BOOK, (1.15, -0.40)), ("pen_dining", DT, (3.6, 6.6)))}
    return {
        "check_desk_first": dict(
            base="e1_pencil_asked", control="e1_pencil_asked", conditions=["goal_already_met"],
            instruction=PEN_TXT[0], instruction_zh=PEN_TXT[1],
            factor="what lies on the desk (seed: the pen asked for, or only a pencil with the pen on the bedroom "
                   "bookcase)",
            challenge="a pen is asked for; a writing thing already lies on the study desk: the pen itself, or only a "
                      "pencil (the pen is then on the bedroom bookcase)",
            rationale="look before fetching: if the pen is there the goal already holds and the right plan is to stop "
                      "(fetching another is a wasted errand); a pencil is not what was asked for, so then fetch the pen",
            cases=check_cases),
        "all_pens": dict(
            base="e1_pencil_asked", control="e1_pencil_asked", conditions=["unknown_count", "not_in_view"],
            instruction="The kid is filling the pencil case. Collect every pen and pencil in the house onto the study "
                        "desk.",
            instruction_zh="孩子要整理文具盒。把家里所有的钢笔和铅笔都收到书房的书桌上。",
            factor="how many writing things there are and where (seed: 2, 3 or 4, over the bedroom, the dining room, "
                   "the living room and the kitchen)",
            challenge="the instruction does not say how many; two to four pens and pencils are spread over different "
                      "rooms, most of them out of view",
            rationale="an open-ended collection: search room after room, one item per trip, and stop only when every "
                      "place has been checked; missing one fails",
            cases=all_cases),
        "homework_ready": dict(
            base="e1_pencil_asked", control="e1_pencil_asked", conditions=["goal_items_unstated", "not_in_view"],
            instruction="The kid is about to do homework at the study desk. Get the desk ready with what they need to "
                        "do written homework.",
            instruction_zh="孩子马上要在书房书桌写作业了。把写作业要用的东西准备到书桌上。",
            factor="how many writing things and notebooks there are (seed: one pen and one notebook; several; a pencil "
                   "and no pen)",
            challenge="the instruction names the purpose, not the items; writing things and notebooks are in other "
                      "rooms, next to a book (no notebook) and the kid's teddy bear",
            rationale="written homework needs something to write with and a notebook to write in: bring one of each "
                      "(any pen or pencil, any notebook), not the book or the teddy",
            cases=ready_cases),
        "pens_per_notebook": dict(
            base="e1_pencil_asked", control="e1_pencil_asked", conditions=["count_from_scene", "not_in_view"],
            instruction="The kids are doing homework at the study desk, each with a notebook. Bring one pen or pencil "
                        "for each notebook on the desk and put it beside that notebook; one per notebook, no more.",
            instruction_zh="孩子们在书房书桌写作业，每人一本作业本。桌上有几本作业本，就拿几支笔（钢笔、铅笔都行）来，"
                           "每本旁边放一支，不要多拿。",
            keep_design=[DESK],
            factor="how many notebooks are on the desk (seed: 2 or 3)",
            challenge="the number of pens is not in the instruction but on the desk (two or three notebooks); four "
                      "writing things are spread over the bedroom bookcase, the TV stand and the dining table",
            rationale="count the notebooks first, then bring exactly that many writing things and put one by each; "
                      "the others stay where they are",
            cases=per_cases),
        "errand_combined": dict(
            base="e1_pencil_asked", control="e1_pencil_asked", conditions=["errands_combined"],
            add={MUG: {"asset": "breakfast_mug", "support": DESK, "xy": [-0.35, -5.95], "yaw_deg": 0.0}},
            instruction="The kid needs a pen for homework at the study desk. Also, there is a used mug on that desk: "
                        "take it back to the kitchen counter.",
            instruction_zh="孩子在书房书桌写作业要用钢笔，拿一支过去。另外，那张书桌上有个用过的马克杯，要拿回厨房台面。",
            goal={"all": [["on", "pen", DESK], ["on_any", MUG, KITCHEN_WORKTOPS_DESK], ["upright", MUG],
                          ["hand_empty", "right"]]},
            watch=["pen", MUG],
            factor="where the pen is (seed: the bedroom bookcase or the dining table)",
            challenge="two errands that meet at the study desk: a pen to bring there, a used mug to take from there to "
                      "the kitchen; one hand",
            rationale="order the errands: fetch the pen, put it on the desk and take the mug from the same spot to the "
                      "kitchen, instead of a separate trip to the desk for the mug",
            cases=errand_cases),
        "x6_gd_pen_or_pencil_cabinets": dict(
            base="h_task_pencil_in_cabinet", control="h_task_pencil_in_cabinet",
            factor="which cabinet holds the preferred item",
            instruction=two_cab,
            instruction_zh="孩子写作业要用钢笔，拿一支钢笔到书房书桌上。笔都收在厨房那两个矮柜里，拿完把柜门关好。",
            challenge="writing things are in the two low cabinets: a pencil in one, the pen in the other (seed "
                      "decides which)",
            rationale="a pen is asked for, so finding the pencil is not enough: the cabinets are inspected until the "
                      "pen is found (reference route: the pencil's cabinet first)",
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
    F, CAB, ISL = "floor_block", "kitchen_cabinet_6/top", "kitchen_island/top"
    # display_row: three blocks squared in a row at the front of the cabinet top, apart
    row_goal = {"all": [*[["on", x, CAB] for x in (A, B, F)], *[["squared", x] for x in (A, B, F)],
                        *[["front_visible", x] for x in (A, B, F)],
                        ["clear_of", A, [B, F], 0.03], ["clear_of", B, [A, F], 0.03], ["clear_of", F, [A, B], 0.03],
                        ["hand_empty", "right"]]}
    row_xy = {A: [3.32, 0.45], B: [3.50, 0.45], F: [3.68, 0.45]}

    def row_route(where):
        out = [look(ISL)]
        for x, region in where:
            out += ([S("search", object=x, region=region)] if region else []) + [nav(x), pick(x), nav(CAB),
                                                                                place(x, CAB, row_xy[x])]
        return out
    row_cases = {"island_floor": dict(route=row_route([(A, None), (B, None), (F, "living_room_0_0")])),
                 "spread": dict(move={B: P("dining_table_2/top", 3.7, 6.3), F: P("kitchen_counter_2/top", -0.1, 7.3)},
                                route=row_route([(A, None), (B, "dining_room_0_1"), (F, "kitchen_0_1")]))}
    # display_spot_or_tv: the cabinet top holds the family's cereal boxes and juice, not to be moved; the block goes
    # on the cabinet where it can be seen, or, if the boxes leave no visible place there, on the TV stand.  Seed:
    # the boxes stand in the front row (display_hidden's layout: the TV stand) or along the back (the cabinet).
    hidden = copy.deepcopy(t["variants"]["display_hidden"])
    on_cab = [*hidden["move"], *hidden["add"]]                           # cereal a, b, c and the juice bottle
    shown = lambda sup: [["on", A, sup], ["front_visible", A], ["away_from_edge", A, 0.02]]  # noqa: E731
    stay = [*[["near_start", n, 0.02] for n in on_cab], *[["upright", n] for n in on_cab], ["hand_empty", "right"]]
    back = {n: {**m, "xy": [m["xy"][0], 0.28]} for n, m in hidden["move"].items()}
    back_add = {n: {**m, "xy": [m["xy"][0], 0.28]} for n, m in hidden["add"].items()}
    other_display = {"any": [shown(sup) for sup in ("tv_stand_2/top", "kitchen_cabinet_4/top")], "all": stay}
    spot_cases = {
        "front_taken": dict(move=hidden["move"], add=hidden["add"], goal=other_display,
                            route=[look(ISL), look(CAB), nav(A), pick(A), nav("tv_stand_2/top"),
                                   place(A, "tv_stand_2/top")]),
        "front_free": dict(move=back, add=back_add, goal={"all": shown(CAB) + stay},
                           route=[look(ISL), look(CAB), nav(A), pick(A), nav(CAB), place(A, CAB, [3.433, 0.465])]),
        # the block is not at hand (occupied_block_away's design): find it, then judge the cabinet as above
        "front_taken_block_away": dict(
            move={**hidden["move"], A: P("dining_table_2/top", 3.7, 6.3)}, add=hidden["add"], goal=other_display,
            route=[look(ISL), look(CAB), S("search", object=A, region="dining_room_0_1"), nav(A), pick(A),
                   nav("tv_stand_2/top"), place(A, "tv_stand_2/top")]),
        "front_free_block_away": dict(
            move={**back, A: P("bookcase_2/top", 1.0, -0.43)}, add=back_add, goal={"all": shown(CAB) + stay},
            route=[look(ISL), look(CAB), S("search", object=A, region="bedroom_0_1"), nav(A), pick(A), nav(CAB),
                   place(A, CAB, [3.433, 0.465])])}
    # seen_from_bed: the kid wants to see the block from bed.  The bedside bookcase is the surface in view of the
    # pillow (farther, lower furniture is hidden by the bed itself); the kid's cereal boxes stand on it, and the
    # part of the top behind them cannot be seen from the pillow.  Which part that is depends on where the boxes
    # stand (seed).  visible_from checks the line of sight from the kid's eye at the end.
    BED = "bookcase_3/top"
    EYE = [0.0, -4.6, 1.2]                               # the kid's eye, head on the pillow
    BOX_ROWS = {"boxes_middle": ([(2.10, -5.0145), (2.10, -4.8895), (2.10, -4.7645)], [1.88, -4.88]),
                "boxes_corner": ([(1.85, -5.0145), (1.85, -4.8895)], [2.15, -4.74])}
    bed_cases = {}
    for case, (row, spot) in BOX_ROWS.items():
        names = [f"bedside_box_{i + 1}" for i in range(len(row))]
        bed_cases[case] = dict(
            add={n: {"asset": "cereal_box", "support": BED, "xy": list(xy), "yaw_deg": 0.0} for n, xy in zip(names, row)},
            goal={"all": [["on", A, BED], ["visible_from", A, EYE, 0.5], *[["near_start", n, 0.05] for n in names],
                          *[["upright", n] for n in names], ["hand_empty", "right"]]},
            watch=[A, B, *names],
            route=[look(ISL), nav(A), pick(A), S("explore_room", room="bedroom_0_1"), nav(BED), look(BED),
                   place(A, BED, spot)])
    return {
        "display_row": dict(
            base="free", control="free", conditions=["arrangement"],
            instruction="Put the three toy blocks on display in a row on top of the low wall cabinet: squared to its "
                        "edge, at the front where they can be seen, not touching each other.",
            instruction_zh="把三块积木在靠墙矮柜顶上排成一排展示：摆正（和柜子边平行），放在前面看得见的地方，彼此别挨着。",
            goal=row_goal, watch=[A, B, F],
            factor="where the blocks are (seed: two on the island and one on the living-room floor, or spread over "
                   "the island, the dining table and the kitchen counter)",
            challenge="three blocks, some out of view, to be arranged together on one small cabinet top (60 x 32 cm)",
            rationale="fetch the blocks one by one and compose the row: each placement has to leave room and spacing "
                      "for the next, squared and at the front",
            cases=row_cases),
        "display_spot_or_tv": dict(
            base="display_hidden", control="free", conditions=["infeasible_fallback", "spot_quality"],
            instruction="Put the toy block on display where it can be seen from the room, best on top of the low "
                        "wall cabinet. Leave the boxes and the bottle on the cabinet where they are.",
            instruction_zh="把积木摆出来展示，要从房间里看得见，最好摆在靠墙矮柜顶上。柜顶上的盒子和瓶子都别挪。",
            watch=[A, B, *on_cab],
            factor="where the boxes and the bottle stand on the cabinet top (seed: the front row, or along the back), "
                   "and whether the block is at hand on the island or has to be found (dining table, bedroom bookcase)",
            challenge="three cereal boxes and a juice bottle stand on the cabinet top, either in the front row (the "
                      "free space behind them cannot be seen from the room) or along the back (the front is free); "
                      "the instruction forbids moving them and names no other place",
            rationale="judge the cabinet top from the room: if the front is free, put the block there (elsewhere "
                      "then fails); if the boxes fill the front row, moving one is ruled out, so find another place "
                      "seen from the room (the TV stand, or the other low cabinet)",
            cases=spot_cases),
        "seen_from_bed": dict(
            base="free", control="free", conditions=["viewer_place", "not_in_view"],
            instruction="The kid wants to look at the toy block while lying in bed tonight. Put it on display "
                        "somewhere the kid can see from the bed.",
            instruction_zh="孩子今晚想躺在床上看着积木。把积木摆在孩子躺在床上能看到的地方。",
            keep_design=[BED],
            viewer={"eye": EYE, "label": "躺在床上看", "targets": [BED]},
            factor="where the kid's boxes stand on the bedside bookcase (seed: in the middle of the top, or in the "
                   "corner on the bed side)",
            challenge="the bed is in the bedroom; the bookcase beside its head is the surface the kid sees from the "
                      "pillow; the kid's cereal boxes stand on it, and the part of the top behind them (as seen from "
                      "the pillow) is out of sight",
            rationale="judge from where the kid lies: put the block on the part of the bedside top that faces the "
                      "pillow, not behind the boxes; which part that is changes with where the boxes stand; the "
                      "boxes stay",
            cases=bed_cases),
    }


def T07(t):
    X, POT, LID, MW, ST = "oatmeal", "handled_cooking_pot", "pot_lid", "kitchen_microwave", "kitchen_stove"
    ISL, BURNER = "kitchen_island/top", [8.41, 1.725]
    # leftovers in their own containers (assets/embodiedgen_heating_assets.json): metal goes on the stove (it does
    # not heat in the microwave), glass and ceramic go in the microwave (a ceramic bowl does not count on the burner)
    MICRO = {"initial_c": 4.0, "heating_rate_c_per_s": 4.0, "stove_rate_c_per_s": 0.0, "cooling_rate_c_per_s": 1.0}
    STOVE = {"initial_c": 4.0, "heating_rate_c_per_s": 0.0, "stove_rate_c_per_s": 2.0, "cooling_rate_c_per_s": 1.0}
    FLAT = {"glass_food_container", "steel_lunch_box", "foil_takeout_tray"}     # pushed to the edge, then pinched
    done = [["not heating", ST], ["not heating", MW], ["is_closed", MW], ["hand_empty", "right"]]
    clear_stove = [X, POT, LID]                          # the old bowl and the empty pot on the burner leave

    def grab(x, region=None):
        return ([S("search", object=x, region=region)] if region else []) + [nav(x)] \
            + ([S("expose", object=x), look(x)] if x in FLAT else []) + [pick(x)]

    def to_microwave(x, region=None, temp=40, heat=True):
        return [nav(MW), S("open", articulated=MW), look(ISL)] + grab(x, region) \
            + [nav("kitchen_microwave/inside_floor"), place(x, "kitchen_microwave/inside_floor"),
               S("close", articulated=MW)] + ([S("heat", food=x, appliance=MW, temp_c=temp)] if heat else [])

    def to_stove(x, region=None, temp=40, heat=True):
        return [look(ISL)] + grab(x, region) + [nav("kitchen_stove/top"), place(x, "kitchen_stove/top", BURNER)] \
            + ([S("heat", food=x, appliance=ST, temp_c=temp)] if heat else [])

    # vessel_decides_appliance: which container the leftovers are in (seed); the right appliance follows from it
    ON_ISLAND = {"support": ISL, "xy": [6.69, 1.83], "yaw_deg": 0.0}
    POT_DINING = {"support": "dining_table_2/top", "xy": [3.35, 6.75], "yaw_deg": 0.0}
    VESSELS = {"in_ceramic_bowl": ("oatmeal_bowl", MICRO, ON_ISLAND, None),
               "in_glass_box": ("glass_food_container", MICRO, ON_ISLAND, None),
               "in_pot": ("soup_pot", STOVE, POT_DINING, "dining_room_0_1"),
               "in_steel_box": ("steel_lunch_box", STOVE, ON_ISLAND, None),
               "in_foil_tray": ("foil_takeout_tray", STOVE, ON_ISLAND, None)}
    vessel_cases = {}
    for case, (x, rates, pose, region) in VESSELS.items():
        vessel_cases[case] = dict(
            add={x: {"asset": x, **copy.deepcopy(pose)}}, thermal_override={x: dict(rates)}, watch=[x],
            goal={"all": [["temperature_at_least", x, 40], *done]},
            route=(to_microwave if rates is MICRO else to_stove)(x, region))
    # two_portions: the oatmeal bowl (microwave) and the pot of soup (stove), both warm at the same time; food cools
    # (0.2 C/s), so heating one after the other (heat waits for its target and switches off) leaves the first one
    # cold: start both appliances (press), wait, switch both off
    BOWL, SOUP = "oatmeal_bowl", "soup_pot"
    SOUP_AT = {"dining": (POT_DINING, "dining_room_0_1"),
               "counter": ({"support": "kitchen_counter_2/top", "xy": [-0.13, 7.3], "yaw_deg": 0.0}, "kitchen_0_1")}

    def both_at_once(region):
        return (to_stove(SOUP, region, heat=False)[1:] + [S("press", button="kitchen_stove/power_button")]
                + to_microwave(BOWL, heat=False)
                + [S("approach", target="kitchen_microwave/start_button"),
                   S("press", button="kitchen_microwave/start_button"), S("wait", seconds=25),
                   S("stop", appliance=MW), S("close", articulated=MW), nav(ST), S("stop", appliance=ST)])
    two_cases = {c: dict(add={SOUP: {"asset": SOUP, **copy.deepcopy(pose)},
                              BOWL: {"asset": BOWL, **copy.deepcopy(ON_ISLAND)}},
                         route=both_at_once(region)) for c, (pose, region) in SOUP_AT.items()}
    return {
        "vessel_decides_appliance": dict(
            base="microwave_works", control="microwave_works", conditions=["appliance_compatibility"],
            remove=clear_stove,
            instruction="Warm up the leftovers for breakfast (at least 40 C); mind whether their container can go in "
                        "the microwave or on the burner. Afterwards the stove must be off and the microwave door "
                        "closed.",
            instruction_zh="把剩饭热一下当早饭（至少 40 度），注意装剩饭的容器适不适合进微波炉或放到灶上。"
                           "做完后灶台要关火，微波炉门要关好。",
            factor="which container the leftovers are in (seed: a ceramic bowl or a glass box -> microwave; the "
                   "metal pot, a steel lunch box or a foil tray -> stove)",
            challenge="both appliances work; the leftovers come in one of five containers: ceramic and glass do not "
                      "heat on the burner, metal does not heat in the microwave",
            rationale="choose the appliance by the container's material: the wrong one does not heat the food",
            cases=vessel_cases),
        "two_portions": dict(
            base="microwave_works", control="microwave_works",
            conditions=["appliance_compatibility", "multi_object_goal"], remove=clear_stove,
            thermal_override={BOWL: dict(MICRO, cooling_rate_c_per_s=0.2), SOUP: dict(STOVE, cooling_rate_c_per_s=0.2)},
            instruction="Breakfast needs two things warmed up: the bowl of oatmeal and the pot of leftover soup, both "
                        "to at least 40 C. Afterwards the stove must be off and the microwave door closed.",
            instruction_zh="早饭要热两样：一碗燕麦粥和一锅剩汤，都要热到至少 40 度。做完后灶台要关火，微波炉门要关好。",
            goal={"all": [["temperature_at_least", BOWL, 40], ["temperature_at_least", SOUP, 40], *done]},
            watch=[BOWL, SOUP],
            factor="where the pot of soup is (seed: the dining table or the kitchen counter)",
            challenge="two foods wanted warm together: the oatmeal in a ceramic bowl (microwave only) and the soup in "
                      "the metal pot (stove only); food cools while it waits",
            rationale="each food to its own appliance, and run them at the same time: start the stove and the "
                      "microwave (press), wait, switch both off; heating one after the other lets the first go cold",
            cases=two_cases),
    }


def T08(t):
    X, ISL = "kitchen_sponge", "kitchen_island/top"
    TV_SPONGE = P("tv_stand_2/top", 7.6, 0.38)
    # wipe_and_sort: island_cluttered's island (two rows of things), but the kid's toys among them go to the toy box
    # on the TV stand for good; the kitchen things stay (the wiping strip is free once the toys are gone)
    clutter = copy.deepcopy(t["variants"]["island_cluttered"]["move"])
    kitchen = ["rolling_pin", "soda_can", "mug", "oatmeal", "paperback_book", "breakfast_spoon", "juice_bottle"]
    TOY = "toy_box"
    toy_box = {TOY: {"asset": "toy_box", "support": None, "z": 0.001, "xy": [5.70, 0.80], "yaw_deg": 0.0}}

    def to_box(x):
        return [nav(x), pick(x), nav(TOY), S("approach", target=TOY), place(x, TOY)]
    sponge_wipe = [look("tv_stand_2/top"), nav(X), pick(X), S("approach", target=ISL),
                   S("wipe", surface=ISL, tool=X), place(X, ISL)]
    sort_cases = {}
    for case, toys in (("blocks", ["wooden_block_a", "wooden_block_b"]), ("duck", ["wooden_block_a", "rubber_duck"])):
        mv = {k: v for k, v in clutter.items() if k in kitchen or k in toys or k == X}
        add = dict(toy_box)
        if case == "duck":
            add["rubber_duck"] = {"asset": "rubber_duck", **clutter["wooden_block_b"]}
        sort_cases[case] = dict(
            move=mv, add=add, remove=["wooden_block_b"] if case == "duck" else [],
            goal={"all": [["wiped", ISL], ["on", X, ISL], ["hand_empty", "right"],
                          *[["inside", x, TOY] for x in toys],
                          *[["near_start", x, 0.12, 0.03] for x in kitchen],
                          *[["upright", x] for x in ("soda_can", "mug", "juice_bottle", "oatmeal")]]},
            watch=[X, TOY, *toys, *kitchen],
            route=[look(ISL)] + [st for x in toys for st in to_box(x)] + sponge_wipe)
    # return_sponge_home: someone left the sponge on a table; after wiping it goes back to where sponges are kept:
    # the shallow tray on the low wall cabinet with the spare sponge in it (the instruction does not say where)
    TRAY = "sponge_tray"
    tray = {TRAY: {"asset": "shallow_sorting_tray", "support": "kitchen_cabinet_4/top", "xy": [1.40, 0.42],
                   "yaw_deg": 0.0},
            "spare_sponge": {"asset": "kitchen_sponge", "support": None, "z": 0.645, "xy": [1.45, 0.42],
                             "yaw_deg": 0.0}}
    left = {"dining": (P(DINING, 3.7, 6.3), "dining_room_0_1"),
            "study": (P("desk_1/top", -0.7, -6.0), "living_room_0_1"),
            "far_dining": (P(FAR_DINING, -7.8, 7.6), "dining_room_0_0")}
    home_cases = {c: dict(
        move={X: pose}, add=tray,
        route=[look(ISL), S("search", object=X, region=region), nav(X), pick(X), nav(ISL), S("approach", target=ISL),
               S("wipe", surface=ISL, tool=X), nav(TRAY), S("approach", target=TRAY), place(X, TRAY)])
        for c, (pose, region) in left.items()}
    # which_surface: breakfast was eaten at the island or at the dining table; the used one has the bowl of oatmeal,
    # the spoon and the rolling pin on it, the other is clean; only the used one is to be wiped
    dishes = {ISL: {"oatmeal": P(ISL, 6.97, 1.88), "breakfast_spoon": P(ISL, 7.63, 1.88),
                    "rolling_pin": P(ISL, 7.30, 1.88)},
              DINING: {"oatmeal": P(DINING, 3.25, 6.2), "breakfast_spoon": P(DINING, 3.25, 6.5),
                       "rolling_pin": P(DINING, 3.30, 7.0)}}
    sponge_isl = copy.deepcopy(t["variants"]["sponge_on_island"]["move"][X])
    surf_cases = {}
    for case, used, other in (("island", ISL, DINING), ("dining", DINING, ISL)):
        surf_cases[case] = dict(
            move={X: sponge_isl, **dishes[used]},
            goal={"all": [["wiped", used], ["not wiped", other], ["on", X, ISL], ["hand_empty", "right"]]},
            watch=[X, "oatmeal", "breakfast_spoon", "rolling_pin"],
            route=[look(ISL), nav(X), pick(X)]
            + ([S("wipe", surface=ISL, tool=X), place(X, ISL)] if used == ISL else
               [nav(DINING), look(DINING), S("approach", target=DINING), S("wipe", surface=DINING, tool=X),
                nav(ISL), place(X, ISL)]))
    return {
        "wipe_and_sort": dict(
            base="island_cluttered", control="sponge_on_island", conditions=["category_rule", "not_in_view"],
            instruction="Wipe the kitchen island with the sponge. The kid's toys lying on it go into the kid's toy box "
                        "in the living room; the kitchen things stay on the island. Leave the sponge on the island.",
            instruction_zh="用海绵把厨房岛台擦一下。岛台上孩子的玩具收进客厅里孩子的玩具箱，厨房的东西留在岛台上。"
                           "擦完把海绵留在岛台上。",
            factor="which toys lie among the kitchen things (seed: two blocks, or a block and the rubber duck)",
            challenge="the island holds two rows of things: kitchen things (rolling pin, can, mug, oatmeal, book, "
                      "spoon, juice) and the kid's toys among them; the toy box (with a toy in it) is on the TV "
                      "stand; the sponge is on the TV stand too",
            rationale="sort by kind: each toy goes into the toy box for good, the kitchen things stay where they "
                      "are; with the toys gone the front strip is free to wipe; then the sponge goes on the island",
            cases=sort_cases),
        "return_sponge_home": dict(
            base="sponge_on_island", control="sponge_on_island", conditions=["storage_place", "not_in_view"],
            instruction="Someone used the sponge and left it lying on a table somewhere. Wipe down the kitchen island "
                        "with it, then put the sponge away where it is normally kept.",
            instruction_zh="有人用完海绵随手放在了某张桌子上。用它把厨房岛台擦一下，擦完把海绵收回平时放海绵的地方。",
            goal={"all": [["wiped", ISL], ["inside", X, TRAY], ["inside", "spare_sponge", TRAY],
                          ["hand_empty", "right"]]},
            watch=[X, TRAY, "spare_sponge"],
            factor="which table the sponge was left on (seed: the dining table next door, the study desk, or the "
                   "dining table in the west dining room)",
            challenge="the sponge lies on a table, out of view; where sponges are kept is not said: a shallow tray "
                      "on the low wall cabinet holds the spare sponge",
            rationale="find the sponge and wipe; then put it away, not back on the table it was found on and not "
                      "left on the island: the tray with the other sponge is where sponges are kept",
            cases=home_cases),
        "which_surface": dict(
            base="sponge_on_island", control="sponge_on_island", conditions=["referent_clue"],
            instruction="Breakfast was eaten either at the kitchen island or at the dining table. Wipe the one that "
                        "was used with the sponge; the other one is clean, leave it. Leave the sponge on the island.",
            instruction_zh="早饭是在岛台或者餐桌上吃的。用海绵把吃过饭的那个擦一下；另一个是干净的，别擦。"
                           "擦完把海绵留在岛台上。",
            factor="where breakfast was eaten (seed: the island or the dining table)",
            challenge="one of the two surfaces has the used bowl of oatmeal, the spoon and the rolling pin on it, the "
                      "other has no dishes; the instruction names both and not which",
            rationale="tell the used surface from the things left on it and wipe only that one (wiping the clean "
                      "one too fails)",
            cases=surf_cases),
    }


def T09(t):
    SP, POT, LID = "breakfast_spoon", "handled_cooking_pot", "pot_lid"
    base = OR(t, "lid_off")        # look, collect, nav spoon, pick spoon, nav pot, stir, nav island, place spoon,
    #                                nav lid, pick lid, nav pot, cover, nav stove, heat

    STOVE, ISL = "kitchen_stove/top", "kitchen_island/top"
    goal = copy.deepcopy(t["goal"])
    # pot_in_use: yesterday's soup (the soup pot, full) is on the left burner; the empty pot is in the dining room.
    # The tomatoes must not go into the full pot: fetch the empty one to the free burner.  Seed: the full pot on the
    # stove (in use) or on the dining table with the empty pot on the stove (the nominal plan works).
    SOUP = "soup_pot"
    lid_isl = P(ISL, 7.25, 1.85)                          # the lid by the tomatoes: the right burner stays free
    use_goal = {"all": [*goal["all"], ["near_start", SOUP, 0.03], ["upright", SOUP],
                        *[["not inside", x, SOUP] for x in TOMATOES]]}
    in_use = dict(
        move={POT: P(DINING, 3.55, 5.75), LID: lid_isl}, add={SOUP: {"asset": SOUP, **P(STOVE, 8.41, 1.725)}},
        goal=use_goal,
        route=[look(ISL), look(STOVE), S("search", object=POT, region="dining_room_0_1"), nav(POT), pick(POT),
               nav(STOVE), place(POT, STOVE, [8.70, 1.725])] + base[1:])
    free = dict(
        add={SOUP: {"asset": SOUP, **P(DINING, 3.35, 6.75)}}, goal=use_goal,
        route=[look(ISL), look(STOVE)] + base[1:])
    # tomato_in_fridge: three tomatoes for the soup; two are on the island, the third is kept in the fridge (food is
    # kept there; the instruction does not say so).  Seed: the third in the fridge, or on the island with the others.
    F3, FRIDGE = "fridge_tomato", "breakfast_fridge"
    cold = {F3: {"initial_c": 4.0, "stove_rate_c_per_s": 3.0, "cooling_rate_c_per_s": 1.5, "heating_rate_c_per_s": 4.0}}
    three_goal = {"all": [*goal["all"], ["inside", F3, POT], ["temperature_at_least", F3, 60],
                          ["is_closed", FRIDGE]]}
    fridge = dict(
        add={F3: {"asset": "cherry_tomato", "support": f"{FRIDGE}/inside_shelf", "xy": [5.90, 3.30], "yaw_deg": 0.0}},
        route=base[:2] + open_explore(FRIDGE) + [nav(F3), pick(F3), S("retreat", obstacle=FRIDGE, distance_m=0.3),
                                                 S("close", articulated=FRIDGE), nav(POT),
                                                 S("drop", object=F3, container=POT)] + base[2:])
    on_island = dict(
        add={F3: {"asset": "cherry_tomato", **P(ISL, 7.715, 1.70)}},
        route=[base[0], S("collect", objects=[*TOMATOES, F3], container=POT)] + base[2:])

    def apart(region):
        return base[:1] + recs(S("collect", objects=[TOMATOES[0]], container=POT),
                               S("search", object=TOMATOES[1], region=region), nav(TOMATOES[1]), pick(TOMATOES[1]),
                               nav(POT), S("drop", object=TOMATOES[1], container=POT)) + base[2:]
    return {
        "pot_in_use": dict(
            base="lid_off", control="lid_off", conditions=["resource_in_use", "not_in_view"],
            watch=[POT, SOUP, LID, *TOMATOES],
            factor="whether the pot on the stove is full (seed: yesterday's soup on the left burner and the empty pot "
                   "in the dining room, or the full pot on the dining table and the empty one on the stove)",
            challenge="a pot full of yesterday's tomato soup may stand on the stove's left burner; the empty cooking "
                      "pot is then on the dining table next door; the instruction only says 'the pot on the stove'",
            rationale="look into the pot first: one already full of other soup is in use, the tomatoes must not go "
                      "in it and it stays where it is; fetch the empty pot to the free right burner and cook there. "
                      "When the pot on the stove is the empty one, use it",
            cases={"in_use": in_use, "free": free}),
        "tomato_in_fridge": dict(
            base="lid_off", control="lid_off", conditions=["storage_place", "not_in_view", "closed_fridge"],
            instruction="Make tomato soup for lunch with three cherry tomatoes: put them into the pot on the stove, "
                        "stir, cover the pot and heat the soup to 60 C. Turn the stove off afterwards.",
            instruction_zh="午饭用三颗小番茄做番茄汤：放进灶上的锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。",
            goal=three_goal, thermal_override=cold, watch=[POT, LID, F3, *TOMATOES],
            factor="where the third tomato is (seed: in the fridge, or on the island with the other two)",
            challenge="the soup needs three tomatoes; two are on the island; the third is kept in the closed fridge "
                      "(the instruction does not say where it is)",
            rationale="count: two are not enough; food is kept in the fridge, so look there (open it, take the "
                      "tomato, close it again: Action) rather than search the house (Task); when all three are on "
                      "the island, opening the fridge is a needless trip",
            cases={"in_fridge": fridge, "on_island": on_island}),
        "x6_gd_tomato_elsewhere": dict(
            base="lid_off", control="lid_off",
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
    }


def T10(t):
    CAN = "soda_can"
    instr = ("An empty soda can was put away in the kitchen by mistake; a door has to be opened to find it. Find it, "
             "throw it into the trash can, and close the doors you opened at the end.")
    goal = {"all": [["inside", CAN, "trash_can"], ["hand_empty", "right"], ["is_closed", "kitchen_microwave"],
                    ["is_closed", "kitchen_cabinet_6"], ["is_closed", "breakfast_fridge"]]}
    mw = [nav("kitchen_microwave"), S("open", articulated="kitchen_microwave"), look("kitchen_microwave/inside_floor")]
    take = lambda art: [nav(CAN), pick(CAN), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art),  # noqa: E731
                        nav("trash_can"), S("drop", object=CAN, container="trash_can")]
    in_cab = {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.63, 0.36], "yaw_deg": 0.0}
    in_mw = copy.deepcopy(t["variants"]["h_task_can_in_microwave"]["move"][CAN])
    TRASH, ISL, COUNTER = "trash_can", "kitchen_island/top", "kitchen_counter_2/top"
    base = OR(t, "can_on_island")       # look, explore_room, nav can, pick, lift, nav trash, hover, drop
    throw = lambda x: [nav(x), pick(x), S("lift", object=x, height_m=0.95), nav(TRASH),  # noqa: E731
                       S("hover", object=x, target=TRASH), S("drop", object=x, container=TRASH)]
    # keep_kids_can: two empty cans; the kid's one stands among craft things (a notebook, a pencil) and is kept
    KID = "kids_can"
    craft = lambda sup, x, y: {  # noqa: E731
        KID: {"asset": "soda_can", **P(sup, x, y)},
        "craft_notebook": {"asset": "notebook", **P(sup, x - 0.22, y)},
        "craft_pencil": {"asset": "pencil", **P(sup, x, y + 0.12, 90.0)}}
    kid_goal = {"all": [["inside", CAN, TRASH], ["hand_empty", "right"],
                        *[["near_start", n, 0.03] for n in (KID, "craft_notebook", "craft_pencil")],
                        ["upright", KID]]}
    kid_cases = {
        "kid_desk": dict(add=craft("desk_1/top", -0.55, -6.05), goal=kid_goal,
                         route=[look(ISL), S("search", object=KID, region="living_room_0_1")] + base[2:]),
        "kid_island": dict(add=craft(ISL, 7.40, 1.72), move={CAN: P("desk_1/top", -0.55, -6.05)}, goal=kid_goal,
                           route=[look(ISL), S("search", object=CAN, region="living_room_0_1")] + throw(CAN))}
    # trash_moved: the trash can is not by the island today (dining room, or the bathroom); the can is on the island
    moved = {"dining": ({"support": None, "z": 0.0, "xy": [4.60, 6.00], "yaw_deg": 0}, "dining_room_0_1"),
             "bathroom": ({"support": None, "z": 0.0, "xy": [-0.40, 6.00], "yaw_deg": 0}, "bathroom_0_1")}
    moved_cases = {c: dict(move={TRASH: pose},
                           route=[look(ISL), nav(CAN), pick(CAN), S("lift", object=CAN, height_m=0.95),
                                  S("search", object=TRASH, region=region), nav(TRASH),
                                  S("hover", object=CAN, target=TRASH), S("drop", object=CAN, container=TRASH)])
                   for c, (pose, region) in moved.items()}
    # after_dinner_clear: what is on the dining table decides where it goes: the empty can and the empty foil takeout
    # tray are rubbish, the glass box with leftover rice goes into the fridge, the used mug to the kitchen counter;
    # the cereal boxes stay.  The fridge door is opened before the leftovers are picked up (one hand).
    TRAY, LEFT, MUG, FRIDGE = "takeout_tray", "leftovers", "used_mug", "breakfast_fridge"
    on_table = {CAN: P(DINING, 3.62, 5.95), TRAY: P(DINING, 3.58, 6.45), LEFT: P(DINING, 3.58, 6.85),
                MUG: P(DINING, 3.62, 7.55)}
    asset = {TRAY: "foil_takeout_tray", LEFT: "glass_food_container", MUG: "breakfast_mug"}
    fate = {CAN: [["inside", CAN, TRASH]], TRAY: [["inside", TRAY, TRASH]],
            LEFT: [["on", LEFT, f"{FRIDGE}/inside_shelf"], ["is_closed", FRIDGE]],
            MUG: [["on_any", MUG, KITCHEN_WORKTOPS], ["upright", MUG]]}
    steps = {CAN: throw(CAN), TRAY: [nav(TRAY), pick(TRAY), S("lift", object=TRAY, height_m=0.95), nav(TRASH),
                                     S("drop", object=TRAY, container=TRASH)],
             LEFT: [nav(FRIDGE), S("open", articulated=FRIDGE), nav(LEFT), pick(LEFT), nav(FRIDGE),
                    place(LEFT, f"{FRIDGE}/inside_shelf"), S("retreat", obstacle=FRIDGE, distance_m=0.3),
                    S("close", articulated=FRIDGE)],
             MUG: [nav(MUG), pick(MUG), nav(COUNTER), place(MUG, COUNTER)]}
    dinner_cases = {}
    for c, items in (("rubbish_leftovers", (CAN, TRAY, LEFT)), ("leftovers_mug", (CAN, LEFT, MUG)),
                     ("rubbish_mug", (CAN, TRAY, MUG))):
        dinner_cases[c] = dict(
            move={CAN: on_table[CAN]},
            add={x: {"asset": asset[x], **on_table[x]} for x in items if x != CAN},
            goal={"all": [a for x in items for a in fate[x]] + [["near_start", n, 0.03] for n in
                                                                 ("clutter_cereal_a", "clutter_cereal_b")]
                  + [["hand_empty", "right"]]},
            watch=[*items, "clutter_cereal_a", "clutter_cereal_b"],
            route=[look(DINING)] + [st for x in items for st in steps[x]])
    # guests_coming: things lying about the living room go where they belong (the can into the trash, the used mug
    # to the kitchen counter, the kid's block into the toy box); what belongs there (the island's rolling pin and
    # sponge, the fruit basket) stays
    BOX, BLOCK = "toy_box", "wooden_block_a"
    stays = ["rolling_pin", "kitchen_sponge"]
    lying = {CAN: P("tv_stand_2/top", 7.60, 0.36), MUG: P("tv_stand_2/top", 7.20, 0.36),
             BLOCK: {"support": None, "z": 0.0, "xy": [6.70, 0.95], "yaw_deg": 20.0}}
    put = {CAN: [["inside", CAN, TRASH]], MUG: [["on_any", MUG, KITCHEN_WORKTOPS], ["upright", MUG]],
           BLOCK: [["inside", BLOCK, BOX]]}
    put_steps = {CAN: throw(CAN), MUG: steps[MUG],
                 BLOCK: [nav(BLOCK), pick(BLOCK), nav(BOX), S("approach", target=BOX), place(BLOCK, BOX)]}
    guest_cases = {}
    for c, items in (("can_mug_block", (CAN, MUG, BLOCK)), ("can_block", (CAN, BLOCK)), ("can_mug", (CAN, MUG))):
        guest_cases[c] = dict(
            move={**{x: lying[x] for x in items if x != MUG},
                  "rolling_pin": P(ISL, 6.80, 1.80), "kitchen_sponge": P(ISL, 8.10, 1.80)},
            add={BOX: {"asset": "toy_box", "support": None, "z": 0.001, "xy": [5.70, 0.80], "yaw_deg": 0.0},
                 **({MUG: {"asset": "breakfast_mug", **lying[MUG]}} if MUG in items else {})},
            goal={"all": [a for x in items for a in put[x]] + [["near_start", n, 0.03] for n in stays]
                  + [["hand_empty", "right"]]},
            watch=[*items, BOX, *stays],
            route=[look(ISL), look("tv_stand_2/top")] + [st for x in items for st in put_steps[x]])
    return {
        "keep_kids_can": dict(
            base="can_on_island", control="can_on_island", conditions=["referent_clue", "not_in_view"],
            instruction="Throw the finished soda can into the trash can. Leave the one the kid is drinking from "
                        "while doing homework.",
            instruction_zh="把喝完的易拉罐扔进垃圾桶。孩子一边写作业一边喝的那罐别扔。",
            watch=[CAN, KID, "craft_notebook", "craft_pencil"],
            factor="which can is the kid's (seed: the one on the study desk among the homework things, or the one on "
                   "the island among them)",
            challenge="two identical cans: one stands among the kid's homework things (a notebook and a pencil), "
                      "the other on its own; one of them is on the island, the other on the study desk",
            rationale="the instruction excludes one can by a clue: tell the kid's can from what stands around it "
                      "and throw out only the other one (throwing the kid's out fails)",
            cases=kid_cases),
        "trash_moved": dict(
            base="can_on_island", control="can_on_island", conditions=["destination_unnamed", "not_in_view"],
            watch=[CAN, TRASH],
            factor="where the trash can is today (seed: the dining room or the bathroom)",
            challenge="the can is on the island, but the trash can is not in its usual place by the island: it "
                      "stands in the dining room or in the bathroom, out of view",
            rationale="the destination, not the item, has to be found: take the can and look for the trash can",
            cases=moved_cases),
        "after_dinner_clear": dict(
            base="can_on_island", control="can_on_island", conditions=["disposal_by_state", "multi_object_goal"],
            instruction="Dinner is over; clear the dining table and take each thing where it should go. The "
                        "cereal boxes stay on the table.",
            instruction_zh="晚饭吃完了，把餐桌收拾干净，每样东西拿到它该去的地方。麦片盒留在桌上。",
            keep_design=[DINING],
            factor="what is left on the table (seed: can, empty takeout tray and leftovers; can, leftovers and a "
                   "mug; or can, takeout tray and a mug)",
            challenge="the dining table holds an empty soda can, and two of: an empty foil takeout tray, a glass box "
                      "with leftover rice, a used mug; the instruction names the kinds, not the objects",
            rationale="decide for each object what it is in its state: the empty can and the empty disposable tray "
                      "are rubbish, the glass box with rice is leftovers (fridge), the mug is a used cup (counter); "
                      "the cereal stays.  One hand: open the fridge before picking up the leftovers, close it after",
            cases=dinner_cases),
        "guests_coming": dict(
            base="can_on_island", control="can_on_island", conditions=["goal_items_unstated", "multi_object_goal"],
            instruction="Guests arrive in ten minutes; make the living room presentable. Put whatever is lying "
                        "about where it belongs, and leave things that belong where they are.",
            instruction_zh="客人十分钟后到，把客厅收拾得能见人：乱放的东西各回各处，本来就该在那儿的东西别动。",
            factor="what lies about (seed: the can, a used mug and a toy block; the can and the block; or the can "
                   "and the mug)",
            challenge="in the living room an empty can and a used mug stand on the TV stand and a toy block lies on "
                      "the floor (two or three of them); the island's rolling pin and sponge belong there",
            rationale="find what is out of place in the room and send each to its own place (trash, counter, toy "
                      "box); leave what belongs (the island's things)",
            cases=guest_cases),
        "x6_gd_can_put_away": dict(
            base="can_on_island", control="can_on_island",
            instruction=instr, goal=goal, remove=["plate_inside_kitchen_cabinet"],
            instruction_zh="厨房里有个空易拉罐被误收起来了，要打开门才能找到。找出来扔进垃圾桶，最后把打开的门关好。",
            factor="which closed place holds the can (seed: the low wall cabinet, the microwave or the fridge)",
            challenge="the can was put away behind a door in the kitchen (the microwave, the wall cabinet or the "
                      "fridge); the instruction names none of them",
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
                                                            fid="resource_can_put_away")]),
                   "in_fridge": dict(move={CAN: {"support": "breakfast_fridge/inside_shelf", "xy": [5.90, 3.30],
                                                 "yaw_deg": 0.0}},
                                     route=mw + [S("close", articulated="kitchen_microwave")]
                                     + open_explore("kitchen_cabinet_6") + [S("close", articulated="kitchen_cabinet_6")]
                                     + open_explore("breakfast_fridge") + take("breakfast_fridge"),
                                     failures=[f_initial("resource", [["on", CAN, "breakfast_fridge/inside_shelf"]],
                                                         fid="resource_can_put_away")])}),
    }


def T12(t):
    CAR, DUCK, BASKET, LIVING = "toy_car", "rubber_duck", "storage_basket", "living_room_0_0"
    BEAR, BLOCK, SPONGE = "teddy_bear", "stray_block", "kitchen_sponge"
    # bins_capacity: no basket; two small bins, one already full of blocks (two layers): car and duck both go into
    # the empty one.  The seed sets which bin is full and whether the two stand side by side on the bedroom bookcase
    # or far apart (the full one in view first, the empty one in another room)
    ev = t["variants"]["toys_everywhere"]
    FULL, EMPTY = "toy_bin_small", "toy_bin_small_2"
    SZ = {"bookcase_2/top": 0.709, "tv_stand_2/top": 0.484, "desk_1/top": 0.70}
    REG_OF = {"bookcase_2/top": "bedroom_0_1", "tv_stand_2/top": LIVING, "desk_1/top": "living_room_0_1"}
    N_STORED = 24

    def full_of_blocks(sup, x0, y0):
        """Twenty-four 4 cm blocks, 4 x 3 per layer (1 mm apart), two layers, inside the floor (smaller than the
        rim): the bin looks and is full."""
        z0 = SZ[sup] + 0.009
        cells = [(dx, dy, dz) for dz in (0.0, BLOCK_H + 0.001) for dx in (-0.0615, -0.0205, 0.0205, 0.0615)
                 for dy in (-0.041, 0.0, 0.041)]
        return {f"stored_block_{i + 1}": {"asset": "wooden_block", "support": None, "z": round(z0 + dz, 3),
                                          "xy": [round(x0 + dx, 3), round(y0 + dy, 3)], "yaw_deg": 0}
                for i, (dx, dy, dz) in enumerate(cells)}

    def cap_case(full_at, empty_at, swap=False):
        """``swap``: the bin called EMPTY is the full one (side by side, the full one on the right)."""
        (fs, fxy), (es, exy) = full_at, empty_at
        FULL_, EMPTY_ = (EMPTY, FULL) if swap else (FULL, EMPTY)
        add = {FULL_: {"asset": "small_storage_bin", "support": fs, "xy": list(fxy), "yaw_deg": 0.0},
               EMPTY_: {"asset": "small_storage_bin", "support": es, "xy": list(exy), "yaw_deg": 0.0}}
        add.update(full_of_blocks(fs, *fxy))
        goal = {"all": [["fully_inside", f"stored_block_{i}", FULL_] for i in range(1, N_STORED + 1)]
                + [["fully_inside", CAR, EMPTY_], ["fully_inside", DUCK, EMPTY_],
                   ["upright", FULL_], ["upright", EMPTY_], ["hand_empty", "right"]]}
        find_empty = [] if fs == es else [S("search", object=EMPTY_, region=REG_OF[es])]
        route = [nav(fs), look(fs), S("measure", object=FULL_), *find_empty, S("measure", object=EMPTY_),
                 S("explore_room", room=LIVING), nav(CAR), pick(CAR), nav(EMPTY_), place(CAR, EMPTY_),
                 S("search", object=DUCK, region="living_room_0_1"), nav(DUCK), pick(DUCK), nav(EMPTY_),
                 S("drop", object=DUCK, container=EMPTY_)]
        return dict(add=add, goal=goal, route=route)
    BC = "bookcase_2/top"
    cap_cases = {"side_left_full": cap_case((BC, (0.84, -0.43)), (BC, (1.13, -0.43))),
                 "side_right_full": cap_case((BC, (1.13, -0.43)), (BC, (0.84, -0.43)), swap=True),
                 "apart_full_on_tv": cap_case(("tv_stand_2/top", (7.60, 0.36)), (BC, (1.00, -0.43))),
                 "apart_empty_on_desk": cap_case((BC, (1.00, -0.43)), ("desk_1/top", (-0.45, -5.95)))}
    # toys_everywhere (v5) is the same design with other containers: a half-full bin and a shallow tray, the duck to
    # be found; it joins as two seeds (the duck on the study desk or on the dining table)
    tev = t["variants"]["toys_everywhere"]
    tev_route = t["routes"][t["oracle"]["toys_everywhere"]]["steps"]
    for case, duck, region in (("half_bin_and_tray", tev["move"][DUCK], "living_room_0_1"),
                               ("half_bin_and_tray_duck_dining", P("dining_table_2/top", 3.7, 6.3), "dining_room_0_1")):
        steps = copy.deepcopy(tev_route)
        for st in steps:
            if st["skill"] == "search":
                st["args"]["region"] = region
                st.pop("role", None)
        cap_cases[case] = dict(move={DUCK: copy.deepcopy(duck)}, add=copy.deepcopy(tev["add"]),
                               remove=list(tev.get("remove", [])), goal=copy.deepcopy(tev["goal"]), route=steps)

    def put_away(x):
        return [nav(x), pick(x), nav(BASKET), place(x, BASKET)]

    def found(x, region):
        return [S("search", object=x, region=region)] + put_away(x)
    in_basket = lambda xs: [["inside", x, BASKET] for x in xs]  # noqa: E731
    # find_all_toys: the toys are spread over the house and the instruction does not say which or how many; a
    # sponge on the dining table looks like a toy block and is not one
    spots = {DUCK: (P("desk_1/top", -0.95, -6.02, 128.7), "living_room_0_1"),
             "duck_bath": (P("large_shelf_3/shelf_1", -1.75, 5.65), "bathroom_0_1"),
             BEAR: (P("dining_table_2/top", 3.30, 6.80), "dining_room_0_1"),
             BLOCK: (P("tv_stand_2/top", 7.40, 0.36), LIVING)}
    all_cases = {}
    for c, toys in (("car_duck", {DUCK: DUCK}), ("car_duck_bear", {DUCK: "duck_bath", BEAR: BEAR}),
                    ("all_four", {DUCK: DUCK, BEAR: BEAR, BLOCK: BLOCK})):
        add = {SPONGE: {"asset": "kitchen_sponge", **P("dining_table_2/top", 3.50, 7.20)}}
        add.update({x: {"asset": "wooden_block" if x == BLOCK else x, **spots[k][0]} for x, k in toys.items() if x != DUCK})
        all_cases[c] = dict(
            move={DUCK: spots[toys[DUCK]][0]}, add=add,
            goal={"all": in_basket([CAR, *toys]) + [["near_start", SPONGE, 0.03], ["upright", BASKET],
                                                    ["hand_empty", "right"]]},
            watch=[CAR, *toys, SPONGE, BASKET],
            route=[S("explore_room", room=LIVING)] + put_away(CAR)
            + [st for x, k in toys.items() for st in found(x, spots[k][1])])
    # castle_stays: the kid's block castle on the living-room floor stays built; loose blocks next to it go away
    def floor(x, y, z=0.0):
        return {"asset": "wooden_block", "support": None, "z": z, "xy": [x, y], "yaw_deg": 0.0}
    castle_cases = {}
    for c, levels, loose in (("tall_two_loose", 3, 2), ("short_one_loose", 2, 1), ("tall_none_loose", 3, 0)):
        tower = [f"castle_block_{i + 1}" for i in range(levels)]
        strays = [f"loose_block_{i + 1}" for i in range(loose)]
        add = {b: floor(5.00, 1.00, BLOCK_H * i) for i, b in enumerate(tower)}
        add.update({b: floor(*xy) for b, xy in zip(strays, ((4.70, 1.30), (5.35, 1.45)))})
        castle_cases[c] = dict(
            add=add,
            goal={"all": in_basket([CAR, DUCK, *strays]) + [["near_start", b, 0.03] for b in tower]
                  + [["never_picked", list(tower)]]
                  + [["on_top_of", tower[i + 1], tower[i]] for i in range(levels - 1)]
                  + [["upright", BASKET], ["hand_empty", "right"]]},
            watch=[CAR, DUCK, *tower, *strays, BASKET],
            route=[S("explore_room", room=LIVING)] + put_away(CAR) + put_away(DUCK)
            + [st for b in strays for st in put_away(b)])
    return {
        "bins_capacity": dict(
            conditions=["joint_capacity"], base="toys_out", control="toys_out",
            remove=[BASKET], move={DUCK: copy.deepcopy(ev["move"][DUCK])},
            watch=[CAR, DUCK, FULL, EMPTY], may_end_on_floor=[CAR],
            factor="which bin is full and where the two stand (seed: side by side on the bedroom bookcase, either "
                   "one full; or apart: the full one on the TV stand and the empty one in the bedroom, or the full "
                   "one in the bedroom and the empty one on the study desk)",
            challenge="no storage basket; two small bins, one already full of toy blocks (two layers), the other "
                      "empty; they stand side by side or in different rooms; the car on the living-room floor, the "
                      "duck on the study desk",
            rationale="the full bin has no room left: both toys go into the empty one, which may have to be found in "
                      "another room; the blocks stay in the full bin",
            cases=cap_cases),
        "find_all_toys": dict(
            base="toys_out", control="toys_out", conditions=["goal_items_unstated", "not_in_view", "multi_object_goal"],
            factor="which toys are out and where (seed: car + duck; car, duck, bear; or car, duck, bear and a block)",
            challenge="the car on the living-room floor, the other toys in other rooms (study desk, bathroom shelf, "
                      "dining table, TV stand); a yellow sponge on the dining table is not a toy",
            rationale="the instruction does not list the toys: search the rooms until every toy is found, tell toys "
                      "from look-alikes (leave the sponge), put each into the basket; stopping after the first few "
                      "fails",
            cases=all_cases),
        "castle_stays": dict(
            base="toys_out", control="toys_out", conditions=["relational_exception", "multi_object_goal"],
            instruction="It is nearly bedtime. Put the kid's toys away. Don't take apart the block castle the kid "
                        "built; the kid wants to keep building it tomorrow.",
            instruction_zh="快到睡觉时间了，把孩子的玩具收起来。他搭的积木城堡别拆，明天还要接着搭。",
            factor="how tall the castle is and how many loose blocks lie next to it (seed: 3 + 2, 2 + 1, 3 + 0)",
            challenge="a tower of identical wooden blocks on the living-room floor, loose blocks of the same kind "
                      "beside it, the car and the duck",
            rationale="the same kind of object is treated by its relation: blocks in the tower stay where they are, "
                      "loose blocks are toys to put away; taking the tower apart or leaving loose blocks fails",
            cases=castle_cases),
    }


def seat_xy(spoon, facing, f, l):
    """A point of a place setting in the diner's frame: ``f`` forward (away from the diner), ``l`` to the diner's
    left, from the setting's spoon."""
    fx, fy = facing
    return [round(spoon[0] + f * fx - l * fy, 3), round(spoon[1] + f * fy + l * fx, 3)]


def T13(t):
    BOWL, CUP, MUG, SPOON, TABLE = "bowl", "cup", "mug", "spoon", "dining_table_2/top"
    TABLE_Z = 0.848
    clear = ["clutter_cereal_a", "clutter_cereal_b", "spoon_target_table"]
    W, E = (1.0, 0.0), (-1.0, 0.0)               # a diner on the west side faces +x, on the east side -x

    def on_table(asset, spoon, facing, f, l, yaw=0.0):
        return {"asset": asset, "support": TABLE, "xy": seat_xy(spoon, facing, f, l), "yaw_deg": yaw}

    def fetch(x, spoon, facing, f, l):
        return [nav(x), pick(x), nav(TABLE), place(x, TABLE, seat_xy(spoon, facing, f, l))]
    # copy_the_setting: one place is set (the example, east side); the other place has only its spoon (west side).
    # Copy what it holds and where, in the diner's frame: the copy faces the other way, so left and right flip in
    # the room.  No cup in the house: the mug takes the cup's place.
    B_SP, A_SP = [2.93, 7.30], [3.70, 6.55]
    RIGHT = {"bowl": (0.0, 0.19), "cup": (0.17, 0.0)}
    LEFT = {"plate": (0.0, 0.19), "bowl": (0.0, 0.19), "mug": (0.17, 0.36)}
    copy_cases = {}
    for c, pattern, kinds, use in (("bowl_cup", RIGHT, {"bowl": "breakfast_bowl", "cup": "breakfast_cup"},
                                    {"bowl": BOWL, "cup": CUP}),
                                   ("plate_bowl_mug_left", LEFT, {"plate": "breakfast_plate", "bowl": "breakfast_bowl",
                                                                  "mug": "breakfast_mug"},
                                    {"plate": "plate_counter_a", "bowl": BOWL, "mug": MUG}),
                                   ("no_cup", RIGHT, {"bowl": "breakfast_bowl", "cup": "breakfast_cup"},
                                    {"bowl": BOWL, "cup": MUG})):
        ex = {f"example_{k}": on_table(a, A_SP, E, *pattern[k]) for k, a in kinds.items()}
        ex["example_spoon"] = on_table("breakfast_spoon", A_SP, E, 0.0, 0.0, 180.0)
        if "plate" in kinds:                     # the example bowl sits on its plate
            ex["example_bowl"].update(support=None, z=TABLE_Z + 0.0325)
        order = [k for k in ("plate", "bowl", "cup", "mug") if k in kinds]
        route = [look(TABLE), S("measure", object="example_spoon")]
        for k in order:
            x = use[k]
            if k == "bowl" and "plate" in kinds:
                route += [nav(x), pick(x), nav(TABLE), S("stack", object=x, base=use["plate"])]
            else:
                route += fetch(x, B_SP, W, *pattern[k])
        news, refs = [use[k] for k in order], [f"example_{k}" for k in order]
        goal = {"all": [["same_arrangement", news, refs, SPOON, "example_spoon", list(W), list(E), 0.07]]
                + [["near_start", r, 0.03] for r in [*refs, "example_spoon"]]
                + [["upright", use[k]] for k in order if k in ("bowl", "cup", "mug")]
                + ([["on_top_of", BOWL, "plate_counter_a"]] if "plate" in kinds else []) + [["hand_empty", "right"]]}
        copy_cases[c] = dict(add=ex, move={SPOON: {"support": TABLE, "xy": B_SP, "yaw_deg": 0.0}},
                             remove=clear + ([CUP] if c == "no_cup" else []), goal=goal,
                             watch=[*news, *refs, "example_spoon", SPOON], route=route)
    # finish_the_table: some places are set (adults: bowl and mug; the kid: bowl and a plastic cup, a toy beside it);
    # the empty places (a spoon each) are set by the rule of whoever sits there: a toy beside the spoon means the kid
    ADULT, KID = {"bowl": (0.0, 0.19), "drink": (0.17, 0.0)}, {"bowl": (0.0, 0.19), "drink": (0.17, 0.0), "toy": (0.0, -0.16)}
    seats = {"e_north": ([3.70, 7.55], E), "e_mid": ([3.70, 6.70], E), "w_north": ([2.93, 7.55], W),
             "w_mid": ([2.93, 6.70], W), "w_south": ([2.93, 5.85], W)}

    def set_place(name, kind, toy_asset="rubber_duck"):
        sp, fc = seats[name]
        out = {f"{name}_spoon": on_table("breakfast_spoon", sp, fc, 0.0, 0.0, 0.0 if fc == W else 180.0),
               f"{name}_bowl": on_table("breakfast_bowl", sp, fc, *ADULT["bowl"]),
               f"{name}_drink": on_table("breakfast_mug" if kind == "adult" else "plastic_cup", sp, fc, *ADULT["drink"])}
        if kind == "kid":
            out[f"{name}_toy"] = on_table(toy_asset, sp, fc, *KID["toy"])
        return out
    examples = {**set_place("e_north", "adult"), **set_place("e_mid", "kid"), **set_place("w_north", "adult")}
    stock = {"bowl_2": {"asset": "breakfast_bowl", **P("tv_stand_2/top", 7.70, 0.34)},
             "mug_2": {"asset": "breakfast_mug", **P("kitchen_counter_2/top", -0.30, 7.70)},
             "kid_cup": {"asset": "plastic_cup", **P("kitchen_counter_2/top", -0.30, 7.95)}}
    finish_cases = {}
    for c, empty in (("adult_seat", {"w_mid": "adult"}), ("kid_seat", {"w_mid": "kid"}),
                     ("adult_and_kid", {"w_mid": "adult", "w_south": "kid"})):
        add = {**examples, **stock}
        goal, route, bowls, mugs = [], [look(TABLE)], [BOWL, "bowl_2"], [MUG, "mug_2"]
        for name, kind in empty.items():
            sp, fc = seats[name]
            add[f"{name}_spoon"] = on_table("breakfast_spoon", sp, fc, 0.0, 0.0)
            if kind == "kid":
                add[f"{name}_toy"] = on_table("toy_car", sp, fc, *KID["toy"])
            drink, avoid = ("kid_cup", mugs) if kind == "kid" else (mugs[0], ["kid_cup"])
            bowl = bowls.pop(0)
            if kind == "adult":
                mugs = mugs[1:]
            goal += [["near_any", f"{name}_spoon", [BOWL, "bowl_2"], 0.12],
                     ["near_any", f"{name}_spoon", [drink] if kind == "kid" else [MUG, "mug_2"], 0.12],
                     ["not near_any", f"{name}_spoon", avoid if kind == "kid" else ["kid_cup"], 0.25]]
            route += fetch(bowl, sp, fc, *ADULT["bowl"]) + fetch(drink, sp, fc, *ADULT["drink"])
        set_names = [n for n in examples]
        finish_cases[c] = dict(add=add, remove=clear + [SPOON, CUP],
                               goal={"all": goal + [["near_start", n, 0.03] for n in set_names]
                                     + [["hand_empty", "right"]]},
                               watch=[BOWL, "bowl_2", MUG, "mug_2", "kid_cup", *[f"{n}_spoon" for n in empty]],
                               route=route)
    return {
        "copy_the_setting": dict(
            base="dishes_on_tv_stand", control="dishes_on_tv_stand", keep_design=[TABLE], conditions=["goal_by_example"],
            instruction="Set the other place, at the second spoon, the same way as the place that is already set.",
            instruction_zh="照着桌上摆好的那份，在另一把勺子那里也摆一份。",
            factor="what the set place holds and how (seed: bowl with the cup on the right; plate, bowl on it and "
                   "the mug on the left; bowl and cup, but no cup left in the house)",
            challenge="one place is set across the table; the other has only its spoon; the instruction does not "
                      "say what to bring",
            rationale="read the example (which things, where relative to its spoon, stacked or not), copy it at "
                      "the other spoon in the diner's frame (the other diner faces the other way: left and right "
                      "flip in the room), and when a kind is missing in the house put the closest one (the mug for "
                      "the cup) in its place",
            cases=copy_cases),
        "finish_the_table": dict(
            base="dishes_on_tv_stand", control="dishes_on_tv_stand", keep_design=[TABLE], conditions=["rule_induction", "referent_clue"],
            instruction="Set the rest of the places at the table.",
            instruction_zh="把桌上剩下的位子也摆好。",
            factor="which places are empty (seed: one adult's, one kid's, or both)",
            challenge="three places are set: two adults' with a bowl and a mug, the kid's with a bowl, a plastic cup "
                      "and a toy beside it; the empty places have a spoon, a kid's one also a toy car",
            rationale="induce the rule from the set places (adults: bowl and mug; the kid: bowl and plastic cup), "
                      "tell whose empty place it is from the toy beside it, set it by that rule",
            cases=finish_cases),
    }


def T14(t):
    B, DESK, CASE = "book_red", "desk_1/top", "bookcase_2/top"
    KIDS_CASE = ["bookcase_2/top", "bookcase_2/shelf_1", "bookcase_2/shelf_0"]        # his bookcase, any level
    t["goal"] = {"all": [["on_any", B, KIDS_CASE], ["hand_empty", "right"]]}
    SIZE = {"book_red": 0.24, "book_green": 0.22, "book_blue": 0.20, "paperback_book": 0.18}

    def on_desk(asset, x):
        """a book flat on the study desk, its long side across the front edge, overhanging it by 6.5 cm"""
        return {"asset": asset, "support": DESK, "xy": [x, round(-6.326 + SIZE[asset] / 2 - 0.065, 3)], "yaw_deg": 90.0}

    def book(asset, sup, x, y, yaw=0.0):
        return {"asset": asset, "support": sup, "xy": [x, y], "yaw_deg": yaw}

    def shelve(x, sup=CASE, hint=None):
        return [nav(x), pick(x), nav(sup), place(x, sup, hint)]
    low = ["bookcase_2/top", "bookcase_2/shelf_1", "bookcase_2/shelf_0", "bookcase_3/top", "bookcase_3/shelf_1",
           "bookcase_3/shelf_0", "large_shelf_4/shelf_0", "large_shelf_4/shelf_1", "large_shelf_4/shelf_2",
           "large_shelf_5/shelf_0", "large_shelf_5/shelf_1"]
    # within_kids_reach: the red book's set is on a high shelf (where it belongs); the kid reads it on his own
    # tomorrow, so it goes where he can reach it
    reach_cases = {}
    for c, high, lower, xs in (("set_on_large_shelf_4", "large_shelf_4/shelf_4", "large_shelf_4/shelf_1", (3.20, 3.45)),
                               ("set_on_large_shelf_5", "large_shelf_5/shelf_3", "large_shelf_5/shelf_1", (3.95, 4.20))):
        y = -5.15 if "_4" in high else -0.35
        reach_cases[c] = dict(
            add={f"set_book_{i + 1}": book("book_red", high, x, y) for i, x in enumerate(xs)},
            watch=[B, "set_book_1", "set_book_2"],
            route=[look(DESK), S("explore_room", room="bedroom_0_1")] + shelve(B, lower, [xs[0] + 0.5, y]))
    # stack_them_stably: every book from the desk onto the bookcase in one pile, the largest at the bottom
    stack_cases = {}
    for c, books in (("red_blue_paperback", ("paperback_book", "book_red", "book_blue")),
                     ("green_paperback", ("paperback_book", "book_green")),
                     ("blue_green_paperback", ("book_blue", "paperback_book", "book_green"))):
        names = {a: ("book_red" if a == "book_red" else f"desk_{a}") for a in books}
        add = {names[a]: on_desk(a, x) for a, x in zip(books, (-1.20, -0.90, -0.60)) if a != "book_red"}
        move = {B: on_desk("book_red", -0.90 if books[1] == "book_red" else -1.20)} if "book_red" in books else {}
        order = sorted(books, key=lambda a: -SIZE[a])
        rm = [] if "book_red" in books else [B]
        route = [look(DESK)] + shelve(names[order[0]], CASE, [1.00, -0.45])
        for lo, hi in zip(order, order[1:]):
            route += [nav(names[hi]), pick(names[hi]), nav(CASE), S("stack", object=names[hi], base=names[lo])]
        stack_cases[c] = dict(
            add=add, move=move, remove=rm, watch=[names[a] for a in books],
            goal={"all": [["on_any", names[order[0]], [CASE, "bookcase_3/top"]]]
                  + [["on_top_of", names[hi], names[lo]] for lo, hi in zip(order, order[1:])] + [["hand_empty", "right"]]},
            route=route)
    # homework_stays: tidy the desk; the finished book to the bookcase, the used mug to the kitchen, the homework
    # (an open notebook and a pencil) stays for tomorrow
    hw = {"homework": book("notebook", DESK, -0.55, -5.95, 10.0), "hw_pencil": book("pencil", DESK, -0.30, -5.95, 80.0)}
    hw_cases = {}
    for c, mug_at in (("", -1.00),):
        hw_cases[c] = dict(
            add={**hw, "desk_mug": {"asset": "breakfast_mug", "support": DESK, "xy": [mug_at, -5.90], "yaw_deg": 0.0}},
            route=[look(DESK)] + shelve(B) + [nav("desk_mug"), pick("desk_mug"), nav("kitchen_counter_2/top"),
                                              place("desk_mug", "kitchen_counter_2/top", [-0.30, 7.60])])
    # whose_book: each book from the desk to the shelf that holds books of its kind: the blue hardcovers stand on
    # the bedroom bookcase, the paperbacks on the living-room shelf
    KIDS, ADULT = "bookcase_2/top", "large_shelf_2/shelf_2"
    SHELF_LEVELS = {KIDS: KIDS_CASE, ADULT: [f"large_shelf_2/shelf_{k}" for k in range(4)]}   # any level of that shelf
    shelves = {"blue_shelved_1": book("book_blue", KIDS, 0.85, -0.45), "blue_shelved_2": book("book_blue", KIDS, 1.10, -0.45),
               "paperback_shelved_1": book("paperback_book", ADULT, -1.86, -1.60, 90.0),
               "paperback_shelved_2": book("paperback_book", ADULT, -1.86, -1.30, 90.0)}
    whose_cases = {}
    for c, items in (("blue_book", {"blue_book": ("book_blue", KIDS)}),
                     ("paperback", {"paperback": ("paperback_book", ADULT)}),
                     ("both", {"blue_book": ("book_blue", KIDS), "paperback": ("paperback_book", ADULT)})):
        add = dict(shelves)
        add.update({n: on_desk(a, x) for (n, (a, _)), x in zip(items.items(), (-0.95, -0.55))})
        whose_cases[c] = dict(
            add=add, remove=[B], watch=[*items, *shelves],
            goal={"all": [["on_any", n, SHELF_LEVELS[sup]] for n, (_, sup) in items.items()]
                  + [["near_start", n, 0.03] for n in shelves] + [["hand_empty", "right"]]},
            route=[look(DESK)] + [st for n, (_, sup) in items.items()
                                  for st in shelve(n, sup, [1.0, -0.45] if sup == KIDS else [-1.86, -0.95])])
    # next_in_series: the red book back, and the other book of its set (the same red cover, among other books) to
    # the desk for tomorrow
    others = {"blue_book_case": book("book_blue", CASE, 0.85, -0.45), "green_book_case": book("book_green", CASE, 1.12, -0.45),
              "paperback_shelf": book("paperback_book", "bookcase_3/top", 2.05, -4.90)}
    series_cases = {}
    for c, (sup, xy, region) in (("on_bookcase", (CASE, (1.00, -0.30), None)),
                                 ("on_other_bookcase", ("bookcase_3/top", (2.25, -4.90), "bedroom_0_1")),
                                 ("on_tall_shelf", ("large_shelf_4/shelf_1", (3.60, -5.15), "bedroom_0_1"))):
        add = {**others, "red_book_2": book("book_red", sup, *xy)}
        if sup == CASE:
            add["green_book_case"] = book("book_green", "large_shelf_4/shelf_1", 3.60, -5.15)
        series_cases[c] = dict(
            add=add, watch=[B, "red_book_2", *others],
            route=[look(DESK)] + shelve(B, CASE, [1.00, -0.55]) + [look(CASE)]
            + ([S("search", object="red_book_2", region=region), look(sup)] if region else [])
            + [nav("red_book_2"), pick("red_book_2"), nav(DESK), place("red_book_2", DESK, [-0.80, -6.05])])
    return {
        "within_kids_reach": dict(
            base="e1_book_ready", control="e1_book_ready", conditions=["agent_ability"],
            instruction="The kid finished reading. Put the book away for him; he wants to read it again tomorrow "
                        "on his own.",
            instruction_zh="孩子看完书了，帮他把书收好。他明天还想自己拿来接着看。",
            goal={"all": [["not on", B, "large_shelf_4/shelf_4"], ["not on", B, "large_shelf_5/shelf_3"],
                          ["not on_floor", B], ["hand_empty", "right"]],
                  "any": [[["on", B, sup]] for sup in low]},
            factor="where the red book's set stands, high up (seed: the top of the tall shelf, or the high shelf of "
                   "the other one)",
            challenge="the red book belongs with its set on a high shelf in the bedroom, out of the kid's reach",
            rationale="weigh where it belongs against who will use it: the kid fetches it himself, so it goes on a "
                      "low shelf (below 0.8 m), not back with its set",
            cases=reach_cases),
        "stack_them_stably": dict(
            base="e1_book_ready", control="e1_book_ready", conditions=["subgoal_order", "multi_object_goal"],
            instruction="The kid finished reading. Put the books on the desk away on his bookcase, in one pile, the "
                        "biggest at the bottom and the smallest on top.",
            instruction_zh="孩子看完书了，把书桌上的书都收到他卧室的书架上，摞成一摞，大的放下面，小的放上面。",
            factor="which books are on the desk (seed: three or two, of different sizes)",
            challenge="two or three books of different sizes on the desk; one pile on the bookcase",
            rationale="the order follows from the sizes: the largest at the bottom, each smaller one on top, so no "
                      "book overhangs the one below",
            cases=stack_cases),
        "homework_stays": dict(
            base="e1_book_ready", control="e1_book_ready", conditions=["category_rule", "multi_object_goal"],
            instruction="The kid finished reading. Tidy up his desk and put each thing where it belongs best; he will "
                        "go on with his homework tomorrow.",
            instruction_zh="孩子看完书了，把他的书桌收拾一下，东西都放到最合适的地方。作业他明天还要接着写。",
            # where a thing belongs is a kind of place, not one spot: the book on any bookcase (any level), the mug
            # on any kitchen worktop
            goal={"all": [["on_any", B, T01_BOOKCASES],
                          ["on_any", "desk_mug", ["kitchen_counter_1/top", "kitchen_counter_2/top"]],
                          ["upright", "desk_mug"],
                          ["near_start", "homework", 0.03], ["near_start", "hw_pencil", 0.03],
                          ["never_picked", ["homework", "hw_pencil"]], ["hand_empty", "right"]]},
            watch=[B, "desk_mug", "homework", "hw_pencil"],
            factor="the seed's layout only",
            challenge="the desk holds the finished book, a used mug and the open homework with its pencil",
            rationale="each thing by what it is and what the instruction says about it: the book back on a "
                      "bookcase, the mug to a kitchen worktop, the homework stays as it lies",
            cases=hw_cases),
        "whose_book": dict(
            base="e1_book_ready", control="e1_book_ready", conditions=["storage_place", "referent_clue"],
            instruction="Put the books from the study desk on the shelves with books of the same kind.",
            instruction_zh="把书房书桌上的书收好，放到摆着同类书的书架上。",
            factor="which books are on the desk (seed: a blue hardcover, a paperback, or both)",
            challenge="blue hardcovers stand on the bookcase in the bedroom, paperbacks on the living-room shelf; the "
                      "desk holds one or both kinds",
            rationale="where each book goes follows from the books already shelved: each to the shelf holding its "
                      "kind",
            cases=whose_cases),
        "next_in_series": dict(
            base="e1_book_ready", control="e1_book_ready", conditions=["referent_clue", "not_in_view"],
            instruction="The kid finished the red book. Put it back on his bookcase, and bring the other book of "
                        "the same set to his desk for tomorrow.",
            instruction_zh="孩子看完这本红书了，收回他的书架，再把同一套的另一本拿到书桌上，他明天看。",
            goal={"all": [["on_any", B, KIDS_CASE], ["on", "red_book_2", DESK], ["near_start", "blue_book_case", 0.03],
                          ["near_start", "paperback_shelf", 0.03], ["hand_empty", "right"]]},
            factor="where the other book of the set is (seed: the kid's bookcase, the other bookcase, the tall shelf)",
            challenge="the set is told by its red cover; the other book stands among books of other covers, on the "
                      "kid's bookcase or another shelf in the bedroom",
            rationale="two subgoals in opposite directions; the second item is named only by its relation to the "
                      "first (same set): look at the covers, search the shelves until the matching one is found",
            cases=series_cases),
    }


def T15(t):
    BOOK = "paperback_book"
    # flip_on_the_shelf: the face-down book lies on a low shelf inside the bookcase, too little room above it to
    # turn it over there: take it to the open top, turn it, put it back on its shelf
    cases = {}
    for c, shelf in (("shelf_1", "bookcase_2/shelf_1"), ("shelf_0", "bookcase_2/shelf_0")):
        cases[c] = dict(
            move={BOOK: P(shelf, 1.00, -0.44, 90.0)},
            goal={"all": [["flipped", BOOK], ["on", BOOK, shelf], ["hand_empty", "right"]]},
            route=[S("search", object=BOOK, region="bedroom_0_1"), nav(BOOK), pick(BOOK), nav("bookcase_2/top"),
                   place(BOOK, "bookcase_2/top", [1.00, -0.45]), S("flip", object=BOOK), pick(BOOK),
                   place(BOOK, shelf, [1.00, -0.44])])
    return {
        "flip_on_the_shelf": dict(
            base="book_free", control="book_free", conditions=["workspace_choice", "not_in_view"],
            instruction="A paperback is lying face down in the bedroom bookcase. Turn it face up for me and leave it "
                        "on the same shelf.",
            instruction_zh="卧室书架里有本平装书封面朝下放着，帮我翻正，仍放在原来那一层。",
            watch=[BOOK],
            factor="which low shelf (seed: the upper or the lower one inside the bookcase)",
            challenge="the face-down book lies on a shelf inside the bookcase, with only about 24 cm above it",
            rationale="the turn needs room above the book: do it where there is room (the open top of the "
                      "bookcase), then put the book back on its shelf; turning it in place fails",
            cases=cases),
    }


def T16(t):
    PIN, ISL = "rolling_pin", "kitchen_island/top"
    # everything_near_the_edge: whatever is about to fall off the island's front edge is moved in (the pin rolled,
    # a mug or a bowl set back); what stands safely stays
    edge = {"edge_mug": P(ISL, 7.30, 1.565), "oatmeal": P(ISL, 7.90, 1.575)}
    cases = {}
    for c, risky in (("pin_and_mug", ("edge_mug",)), ("pin_and_bowl", ("oatmeal",)), ("pin_only", ())):
        safe = [x for x in ("edge_mug", "oatmeal") if x not in risky]
        add = {"edge_mug": {"asset": "breakfast_mug", **(edge["edge_mug"] if "edge_mug" in risky else P(ISL, 7.30, 1.85))}}
        move = {"oatmeal": edge["oatmeal"] if "oatmeal" in risky else P(ISL, 7.90, 1.85)}
        route = [look(ISL), nav(PIN), S("roll", object=PIN, distance_m=0.12)]
        for x, hx in zip(risky, (7.30, 7.90)):
            route += [nav(x), pick(x), place(x, ISL, [hx, 1.80])]
        cases[c] = dict(
            add=add, move=move, watch=[PIN, "edge_mug", "oatmeal"],
            goal={"all": [["on", PIN, ISL], ["away_from_edge", PIN, 0.06]]
                  + [a for x in risky for a in (["on", x, ISL], ["away_from_edge", x, 0.06], ["upright", x])]
                  + [["near_start", x, 0.03] for x in safe] + [["hand_empty", "right"]]},
            route=route)
    return {
        "everything_near_the_edge": dict(
            base="pin_free", control="pin_free", conditions=["goal_items_unstated", "multi_object_goal"],
            instruction="Things on the kitchen island are close to falling off its edge. Please take care of it.",
            instruction_zh="岛台边上有东西快掉下去了，处理一下。",
            factor="what else stands at the edge (seed: a mug, the oatmeal bowl, or nothing else)",
            challenge="the rolling pin at the front edge, and sometimes a mug or the full oatmeal bowl too; other "
                      "things on the island stand safely",
            rationale="find every object at risk, not only the pin, and secure each in its own way (roll the pin, "
                      "set the mug or bowl back); leave what is safe",
            cases=cases),
    }


def T17(t):
    B, POT, LID, F = "wooden_block_b", "handled_cooking_pot", "pot_lid", "floor_block"
    base = OR(t, "lid_off")                     # nav stove, look stove, nav island, look island, hide
    lifted = lambda *sr: base + recs(look("kitchen_stove/top"), S("search", object=LID, **dict(sr)), nav(LID), pick(LID),  # noqa: E731
                                     nav(POT), S("cover", container=POT, lid=LID))
    both_goal = {"all": [["hidden", B], ["hidden", F], ["covered", POT, LID], ["hand_empty", "right"]]}
    both = lambda region: base + recs(S("search", object=F, region=region), nav(POT), S("uncover", container=POT),  # noqa: E731
                                      nav(F), look(F), S("hide", object=F, receptacle=POT, lid=LID))
    return {
        "hide_both": dict(
            base="lid_off", control="lid_off", conditions=["multi_object_goal", "not_in_view"],
            goal=both_goal, watch=[B, F, LID, POT, "oatmeal", "rolling_pin"],
            instruction="We are playing hide-and-seek with the kid's toy blocks: hide both wooden blocks in the empty "
                        "pot on the stove and put the lid on so they cannot see them.",
            instruction_zh="我们在和孩子玩捉迷藏，藏的是他的玩具积木：把两块木积木都藏进灶上那个空锅里，再盖上锅盖，别让孩子看见。",
            factor="where the second block is (seed: the TV stand or the dining table)",
            challenge="one block on the island, the other in another room; one pot, one lid",
            rationale="two hides share the lid: find the second block, take the lid off again between the hides, "
                      "cover at the end",
            cases={c: dict(move={F: to}, route=both(region))
                   for c, to, region in (("tv_stand", P("tv_stand_2/top", 7.0, 0.36), "living_room_0_0"),
                                         ("dining", P("dining_table_2/top", 3.7, 6.3), "dining_room_0_1"))}),
        "hide_somewhere": dict(
            base="lid_off", control="lid_off", conditions=["storage_place"],
            remove=["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"],
            instruction="We are playing hide-and-seek with the kid: hide the wooden block where the kid cannot see it "
                        "at a glance. Not inside an appliance, that is dangerous.",
            instruction_zh="陪孩子玩捉迷藏，把木积木藏到孩子一眼看不到的地方。别藏进电器里，危险。",
            goal={"all": [["hidden", B], ["not on", B, "kitchen_microwave/inside_floor"],
                          ["not on", B, "breakfast_fridge/inside_shelf"], ["hand_empty", "right"]]},
            watch=[B, POT, LID],
            factor="what is at hand for hiding (seed: the empty pot with its lid beside it on the stove; or the lid "
                   "put away on the wall cabinet, so a low cabinet serves)",
            challenge="the instruction names no hiding place, only rules out appliances (the microwave and the fridge "
                      "would hide the block too); the pot on the stove hides it when its lid is at hand",
            rationale="pick a place that hides the block and is not an appliance: the pot under its lid when the lid "
                      "is there, else a low cabinet (open it with the free hand, put the block in, close it)",
            cases={"pot_ready": dict(route=base),
                   "lid_away": dict(move={LID: P("kitchen_cabinet_6/top", 3.335, 0.36)},
                                    route=[look("kitchen_island/top"), nav("kitchen_stove/top"), look("kitchen_stove/top"),
                                           nav("kitchen_cabinet_4"), S("open", articulated="kitchen_cabinet_4"), nav(B),
                                           pick(B), nav("kitchen_cabinet_4"),
                                           place(B, "kitchen_cabinet_4/inside_shelf", [1.40, 0.42]),
                                           S("close", articulated="kitchen_cabinet_4")])}),
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
    # enough_for_dinner: three bowls are needed in the cabinet; count, fetch only what is missing
    SHELF6 = "kitchen_cabinet_6/inside_shelf"
    slots = [3.315, 3.50, 3.685]
    spares = ["bowl_kitchen_cabinet", "bowl_side_table"]
    dinner_cases = {}
    for c, have in (("enough", 3), ("one_short", 2), ("two_short", 1)):
        inside = ["bowl_inside_kitchen_cabinet"] + [f"clean_bowl_{i}" for i in range(2, have + 1)]
        add = {f"clean_bowl_{i}": {"asset": "breakfast_bowl", **P(SHELF6, slots[i - 1], 0.36)} for i in range(2, have + 1)}
        route = [nav(C6), S("open", articulated=C6), S("inspect", receptacle=C6)]
        for k, b in enumerate(spares[:3 - have]):
            route += [nav(b), pick(b), nav(C6), place(b, SHELF6, [slots[have + k], 0.36])]
        dinner_cases[c] = dict(
            add=add, move={"bowl_inside_kitchen_cabinet": P(SHELF6, slots[0], 0.36)},
            watch=[*inside, *spares],
            goal={"all": [["count_on_at_least", inside + spares, SHELF6, 3], ["is_closed", C6], ["hand_empty", "right"]]
                  + [["near_start", b, 0.03] for b in spares[3 - have:]]},
            route=route + [S("close", articulated=C6)])
    return {
        "dishes_spread": dict(
            base="at_island", control="at_island", conditions=["item_put_away"],
            instruction="Grandma wants to know whether there is still a clean plate and bowl for dinner. Have a look "
                        "behind the kitchen doors and close every door properly afterwards.",
            instruction_zh="奶奶想知道晚饭还有没有干净的盘子和碗。去厨房带门的地方看一看，看完把门都关好。",
            goal={"all": [*goal_3["all"]]},
            factor="where the bowl is (seed: in the other low cabinet, or in the microwave)",
            challenge="the plate is in the wall cabinet, the bowl is not: it is in the other low cabinet or was left in "
                      "the microwave; the instruction names neither",
            rationale="the first place answers only half of the question: keep looking behind the other doors until "
                      "both dishes are seen, closing each door again",
            cases={"in_cabinet_4": dict(move={"bowl_inside_kitchen_cabinet": P("kitchen_cabinet_4/inside_shelf", 1.4, 0.42)},
                                        route=base + c4,
                                        failures=[f_initial("resource", [["on", "bowl_inside_kitchen_cabinet",
                                                                          "kitchen_cabinet_4/inside_shelf"]],
                                                            fid="resource_bowl_elsewhere")]),
                   "in_microwave": dict(move={"bowl_inside_kitchen_cabinet": in_mw}, route=base + mw,
                                        failures=[f_initial("resource", [["on", "bowl_inside_kitchen_cabinet",
                                                                          "kitchen_microwave/inside_floor"]],
                                                            fid="resource_bowl_elsewhere")])}),
        "enough_for_dinner": dict(
            base="at_island", control="at_island", conditions=["count_against_need"],
            remove=["plate_inside_kitchen_cabinet"],
            instruction="Three of us are having dinner tonight; there should be enough clean bowls in the low wall "
                        "cabinet. Close its door when you are done.",
            instruction_zh="今晚三个人吃晚饭，靠墙矮柜里的干净碗要够用。弄完把柜门关好。",
            factor="how many clean bowls are in the cabinet (seed: three, two or one)",
            challenge="the cabinet holds one to three bowls; spare clean bowls stand on the kitchen cabinet top and "
                      "the side table in the west dining room",
            rationale="count what is there against what is needed and act only on the difference: nothing to "
                      "bring when there are three, one or two bowls fetched otherwise",
            cases=dinner_cases),
    }


def T19(t):
    CAN = "soda_can"
    base = OR(t, "bin_on_bookcase")             # ... approach bin, drop can, nav cube, pick cube, nav bin, drop cube
    shelf = {"kitchen_cabinet_4": {"support": "kitchen_cabinet_4/inside_shelf", "xy": [1.4, 0.42], "yaw_deg": 0.0},
             "kitchen_cabinet_6": {"support": "kitchen_cabinet_6/inside_shelf", "xy": [3.63, 0.36], "yaw_deg": 0.0}}
    take = lambda art: [nav(CAN), pick(CAN), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]  # noqa: E731
    i_can = at(base, "pick", object=CAN)
    rest = base[i_can + 1:]
    can_goal = copy.deepcopy(t["goal"])
    can_goal["all"] += [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]
    return {
        "x6_gd_can_put_away": dict(
            base="bin_on_bookcase", control="m_can_in_dining_room", goal=can_goal,
            remove=["plate_inside_kitchen_cabinet"],
            instruction="Movie night is over; put what goes to recycling into the recycling bin. Someone put the "
                        "empty soda can away in a low kitchen cabinet; close the cabinets again afterwards.",
            instruction_zh="电影看完了，把该回收的东西放进回收箱。有人把空易拉罐收进了厨房的矮柜里，找完把柜门关好。",
            factor="which closed place holds the item",
            challenge="the can is in one of the two low kitchen cabinets (seed decides which); the cube on the floor",
            rationale="inspect the closed places for the can (reference route: the worse order), then recycle both",
            cases={f"in_{w[-1]}": dict(move={CAN: shelf[w]}, route=put_away([], o, w, take, rest),
                                       failures=[f_initial("resource", [["on", CAN, f"{w}/inside_shelf"]], fid="resource_can_put_away")])
                   for w, o in (("kitchen_cabinet_4", "kitchen_cabinet_6"), ("kitchen_cabinet_6", "kitchen_cabinet_4"))}),
    }


def T20(t):
    J = "juice_bottle"
    base = OR(t, "bottle_on_cabinet")           # nav cab6 top, look, nav bottle, pick, nav dining, place
    i = at(base, "pick", object=J)

    # the bowl needs more room than the cabinet top has left: the other low cabinet
    instr = ("Someone put the juice bottle away in one of the low kitchen cabinets. Put it back on the dining table, "
             "standing up, and close the cabinets again.")
    goal = copy.deepcopy(t["goal"])
    goal["all"] += [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]
    tail = base[i + 1:]
    take = lambda art: [nav(J), pick(J), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]  # noqa: E731
    return {
        "x6_gd_bottle_put_away": dict(
            base="bottle_on_cabinet", control="bottle_on_cabinet", instruction=instr, goal=goal, instruction_zh="有人把果汁瓶收进了厨房的一个矮柜里。把它拿回餐桌上立着放好，再把柜门关好。",
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
    X, BASKET, DINING, DESK = "apple", "fruit_basket", "dining_table_2/top", "desk_1/top"
    OR, BA, TRAY = "lunch_orange", "lunch_banana", "fruit_tray"
    fruit_at = {OR: {"asset": "orange", "support": DINING, "xy": [3.63, 5.66], "yaw_deg": 0.0},
                BA: {"asset": "banana", "support": DINING, "xy": [3.30, 5.62], "yaw_deg": 80.0}}
    find_basket = S("search", object=BASKET, region="bedroom_0_1")

    def to_kid(x):
        return [nav(x), pick(x), nav(DESK), place(x, DESK, [-0.90, -6.00])]

    def to_basket(x):
        return [nav(x), pick(x), nav("bookcase_2/top"), place(x, BASKET)]
    # leave_one_for_kid: the fruit on the table goes away (the basket), one stays for the kid as a snack, on the
    # study desk; the kid does not like oranges, so the snack is the apple or the banana
    kid_cases = {}
    for c, fruits, kid in (("apple_orange", (X, OR), X), ("orange_banana", (OR, BA), BA), ("all_three", (X, OR, BA), X)):
        ok = [f for f in fruits if f != OR]
        kid_cases[c] = dict(
            add={f: fruit_at[f] for f in fruits if f != X},
            remove=[] if X in fruits else [X],
            goal={"all": [["hand_empty", "right"]],
                  "any": [[["on", k, DESK]] + [["inside", f, BASKET] for f in fruits if f != k] for k in ok]},
            watch=[*fruits, BASKET],
            route=[look(DINING), find_basket] + to_kid(kid) + [st for f in fruits if f != kid for st in to_basket(f)])
    # fruit_plate_for_guests: the tray has to end on the TV stand with the fruit on it; carried empty first and
    # filled there, no loaded tray is ever lifted
    plate_cases = {}
    for c, tray_at, region in (("tray_in_study", {"support": DESK, "xy": [-0.90, -6.00], "yaw_deg": 0.0}, "living_room_0_1"),
                               ("tray_by_table", {"support": "cell_shelf_4/top", "xy": [4.30, 4.42], "yaw_deg": 0.0},
                                "dining_room_0_1")):
        plate_cases[c] = dict(
            add={OR: fruit_at[OR], TRAY: {"asset": "shallow_sorting_tray", **tray_at}},
            route=[look(DINING), S("search", object=TRAY, region=region), nav(TRAY), pick(TRAY),
                   nav("tv_stand_2/top"), place(TRAY, "tv_stand_2/top", [7.50, 0.36])]
            + [st for f in (X, OR) for st in (nav(f), pick(f), nav(TRAY), place(f, TRAY))])
    return {
        "leave_one_for_kid": dict(
            base="fruits_on_table", control="fruits_on_table",
            conditions=["storage_place", "preference_allocation", "multi_object_goal"],
            instruction="Lunch is over. Put the fruit on the table away, but leave one for the kid doing homework "
                        "in the study as a snack. The kid doesn't like oranges.",
            instruction_zh="午饭吃完了，把桌上的水果收起来，给在书房写作业的孩子留一个当点心。孩子不爱吃橙子。",
            factor="which fruits are on the table (seed: apple and orange, orange and banana, or all three)",
            challenge="two or three fruits on the dining table; the instruction names neither the basket nor the "
                      "desk, and which fruit is the snack follows from the kid's dislike",
            rationale="split the goal: one fruit the kid eats goes to the study desk, the rest to where fruit is "
                      "kept (the basket on the bedroom bookcase); with orange and banana only the banana can be the "
                      "snack, with apple and banana either",
            cases=kid_cases),
        "fruit_plate_for_guests": dict(
            base="fruits_on_table", control="fruits_on_table", conditions=["subgoal_order", "not_in_view"],
            remove=["serving_tray"],
            instruction="The guests are watching TV in the living room. Bring them some fruit on a tray.",
            instruction_zh="客人在客厅看电视，用托盘给他们端点水果过去。",
            goal={"all": [["inside", X, TRAY], ["inside", OR, TRAY], ["not on_floor", X], ["not on_floor", OR],
                          ["hand_empty", "right"]],
                  "any": [[["on", TRAY, "tv_stand_2/top"]], [["on", TRAY, "tv_stand_1/top"]]]},
            watch=[X, OR, TRAY],
            factor="where the tray is (seed: on the study desk, or on the shelf beside the dining table)",
            challenge="the apple and an orange on the dining table, a small tray elsewhere; the tray is to end in "
                      "front of the guests with the fruit on it",
            rationale="order the subgoals so that each step is feasible: one hand cannot carry a loaded tray "
                      "safely, so the empty tray goes to the TV stand first and the fruit is put on it there "
                      "(filling it beside the fruit and then lifting it risks dropping the fruit)",
            cases=plate_cases),
    }


FAMILIES = {"T01_book_to_dining_table": T01, "T02_stack_blocks": T02, "T04_cup_or_mug_to_cabinet": T04,
            "T05_pen_or_pencil_to_desk": T05, "T06_block_destination_occupied": T06, "T07_heat_oatmeal": T07,
            "T08_wipe_island": T08, "T09_tomato_soup": T09, "T10_trash_the_can": T10, "T11_collect_fruits": T11, "T12_tidy_toys": T12,
            "T13_breakfast_setup": T13, "T14_shelve_the_book": T14, "T15_book_face_up": T15,
            "T16_rolling_pin_at_edge": T16, "T17_hide_and_seek_block": T17,
            "T18_check_cabinet_dishes": T18, "T19_recycling": T19, "T20_juice_back_to_table": T20}
# ----------------------------------------------------------------- long-horizon versions of in-place choices
# A Task-Level choice made where the robot already is (which container, which cookware, the substitute next to
# it) is moved to a longer horizon: the right container / pot / substitute is in another room.  The variant it
# replaces leaves v6 (``REPLACED``).
BEDROOM_BIN = {"support": "bookcase_2/top", "xy": [1.0888, -0.4277], "yaw_deg": 0.0}


SUP_Z = {"kitchen_island/top": 0.86, "bookcase_2/top": 0.709, "tv_stand_2/top": 0.484}
SMALL_BIN_BLOCKS = ["small_bin_block_1", "small_bin_block_2"]


def small_bin_with_blocks(sup, xy, yaw=0.0):
    """The small storage bin (inside 21 x 16 cm) with two toy blocks in the corners along one long side: a 10 cm
    strip along the other side takes the 18 cm spoon, the 22 cm rolling pin fits neither straight nor diagonally."""
    import math
    c, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    z = SUP_Z[sup] + 0.009
    out = {"small_storage_bin": {"asset": "small_storage_bin", "support": sup, "xy": list(xy), "yaw_deg": yaw}}
    for name, (dx, dy) in zip(SMALL_BIN_BLOCKS, ((-0.055, 0.035), (0.055, 0.035))):   # the floor is smaller than the rim
        out[name] = {"asset": "wooden_block", "support": None, "z": z,
                     "xy": [round(xy[0] + c * dx - s_ * dy, 4), round(xy[1] + s_ * dx + c * dy, 4)], "yaw_deg": yaw}
    return out


def T03_long(t):
    bin_, spoon, pin = "wide_storage_bin", "breakfast_spoon", "rolling_pin"
    find_bins = [look("kitchen_island/top"), S("search", object=bin_, region="bedroom_0_1"),
                 nav("bookcase_2/top"), look("bookcase_2/top")]
    put_both = [nav(spoon), pick(spoon), nav(bin_), S("approach", target=bin_), S("drop", object=spoon, container=bin_),
                nav(pin), pick(pin), nav(bin_), S("approach", target=bin_), place(pin, bin_)]
    bin_goal = {"all": [["inside", pin, bin_], ["inside", spoon, bin_], ["hand_empty", "right"]]}   # no mug option
    blocks_stay = [["inside", b, "small_storage_bin"] for b in SMALL_BIN_BLOCKS]       # the toys stay in the small bin
    return {
        "small_bin_or_bedroom_bin": dict(
            base="small_and_large", control="large_only", conditions=["small_container_present", "not_in_view"],
            move={bin_: copy.deepcopy(BEDROOM_BIN)}, remove=["mug"],
            add=small_bin_with_blocks("kitchen_island/top", (7.1, 1.75)),
            goal={"all": bin_goal["all"] + blocks_stay}, watch=[pin, spoon, bin_, "small_storage_bin", *SMALL_BIN_BLOCKS],
            factor="where the small bin stands (seed: on the island next to the utensils, or beside the wide bin on "
                   "the bedroom bookcase)",
            challenge="a small storage bin (22 x 17 cm) with two toy blocks in it: the spoon would still fit, the 22 cm "
                      "rolling pin does not, straight or diagonally; the wide storage bin is on the low bookcase in "
                      "the bedroom; the small bin stands either on the island next to the utensils (in view, near) "
                      "or beside the wide bin",
            rationale="measure what room is left: the small bin cannot take the rolling pin, and both go into one "
                      "container, so both utensils go to the wide bin in the bedroom (the blocks stay in the small "
                      "bin).  With the small bin on the island it has to be ruled out before any other container is "
                      "in view",
            cases={"on_island": dict(route=[look("kitchen_island/top"), S("measure", object="small_storage_bin"),
                                            S("measure", object=pin)] + find_bins[1:] + put_both),
                   "beside_wide_bin": dict(
                       move={bin_: {"support": "bookcase_2/top", "xy": [0.885, -0.43], "yaw_deg": 0.0}},
                       add=small_bin_with_blocks("bookcase_2/top", (1.195, -0.43), 90.0),
                       route=find_bins + [S("measure", object="small_storage_bin"), S("measure", object=pin)]
                       + put_both)}),
    }


def T03_more(t):
    """Task-Level designs of T03 beyond the container size: which bin by its contents, a substitute container, the
    spoon in another room."""
    bin_, spoon, pin = "wide_storage_bin", "breakfast_spoon", "rolling_pin"
    TV_BIN = {"support": "tv_stand_2/top", "xy": [7.3, 0.4], "yaw_deg": 0.0}
    sup_z = {"tv_stand_2/top": 0.484, "bookcase_2/top": 0.709}

    def put_both(c, drop_spoon=True):
        return [nav(spoon), pick(spoon), nav(c), S("approach", target=c),
                S("drop", object=spoon, container=c) if drop_spoon else place(spoon, c),
                nav(pin), pick(pin), nav(c), S("approach", target=c), place(pin, c)]

    def inside_bin(where, items):
        """Items lying in a wide bin at ``where`` (support pose): [(name, dx, dy, yaw)]."""
        x, y = where["xy"]
        z = sup_z[where["support"]] + 0.009
        return {n: {"support": None, "z": z, "xy": [round(x + dx, 3), round(y + dy, 3)], "yaw_deg": yaw}
                for n, dx, dy, yaw in items}

    # which_bin_by_contents: two wide bins of one make, one in the living room and one in the bedroom; the toy bin
    # holds the kid's blocks, the kitchen bin holds spoons; the seed decides which one is near
    TOY = "toy_storage_bin"
    toys = [("toy_bin_block_1", -0.08, -0.05, 15.0), ("toy_bin_block_2", 0.07, 0.04, -20.0)]
    tools = [("spoon_counter", 0.0, 0.10, 0.0), ("spoon_side_table", 0.0, 0.05, 0.0)]
    which = {}
    for case, kitchen_at, toy_at in (("toys_near", BEDROOM_BIN, TV_BIN), ("tools_near", TV_BIN, BEDROOM_BIN)):
        look_far = [S("search", object=bin_, region="bedroom_0_1"), nav("bookcase_2/top"), look("bookcase_2/top")]
        which[case] = dict(
            move={bin_: copy.deepcopy(kitchen_at), **inside_bin(kitchen_at, tools)},
            add={TOY: {"asset": "wide_storage_bin", **copy.deepcopy(toy_at)},
                 **{n: {"asset": "wooden_block", **m} for n, m in inside_bin(toy_at, toys).items()}},
            route=[look("kitchen_island/top"), look("tv_stand_2/top")]
            + (look_far if case == "toys_near" else []) + put_both(bin_))
    which_goal = {"all": [["inside", pin, bin_], ["inside", spoon, bin_],
                          *[["inside", n, TOY] for n, *_ in toys], *[["inside", n, bin_] for n, *_ in tools],
                          ["hand_empty", "right"]]}

    # no_bin_substitute: no wide bin; the small bin (TV stand) is too small; the substitute (the
    # storage basket on the bedroom floor or the serving tray on the study desk) is in another room; the fruit
    # basket on the dining table is big enough but holds fruit
    subs = {"basket": ("storage_basket", {"support": None, "z": 0.001, "xy": [0.894, -1.931], "yaw_deg": 0.0},
                       "bedroom_0_1"),
            "tray": ("serving_tray", {"support": "desk_1/top", "xy": [-0.278, -5.994], "yaw_deg": 0.0},
                     "living_room_0_1")}
    fruit = {"fruit_basket": {"asset": "fruit_basket", "support": "dining_table_2/top", "xy": [3.2, 7.6], "yaw_deg": 0.0},
             "apple": {"asset": "apple", "support": None, "z": 0.87, "xy": [3.17, 7.58], "yaw_deg": 0.0},
             "orange": {"asset": "orange", "support": None, "z": 0.87, "xy": [3.24, 7.63], "yaw_deg": 0.0}}
    small = small_bin_with_blocks("tv_stand_2/top", (7.3, 0.4))
    sub_cases = {}
    for case, (x, pose, region) in subs.items():
        sub_cases[case] = dict(
            add={**small, **fruit, x: {"asset": x, **pose}},
            goal={"all": [["inside", pin, x], ["inside", spoon, x], ["inside", "apple", "fruit_basket"],
                          ["inside", "orange", "fruit_basket"],
                          *[["inside", b, "small_storage_bin"] for b in SMALL_BIN_BLOCKS], ["hand_empty", "right"]]},
            watch=[pin, spoon, "small_storage_bin", *SMALL_BIN_BLOCKS, x, "fruit_basket", "apple", "orange"],
            route=[look("kitchen_island/top"), S("measure", object=pin),
                   look("tv_stand_2/top"), S("measure", object="small_storage_bin"),
                   S("search", object=x, region=region), nav(x), look(x)] + put_both(x, drop_spoon=(x != "serving_tray")))

    # utensils_apart: the rolling pin on the island, the spoon left in another room, the bin in the bedroom
    apart = {}
    for case, sp, region in (("dining", P("dining_table_2/top", 3.7, 6.3), "dining_room_0_1"),
                             ("counter", P("kitchen_counter_2/top", -0.1, 7.3), "kitchen_0_1")):
        apart[case] = dict(
            move={bin_: copy.deepcopy(BEDROOM_BIN), spoon: sp},
            route=[look("kitchen_island/top"), S("search", object=bin_, region="bedroom_0_1"), nav("bookcase_2/top"),
                   look("bookcase_2/top"), nav(pin), pick(pin), nav(bin_), S("approach", target=bin_), place(pin, bin_),
                   S("search", object=spoon, region=region), nav(spoon), pick(spoon), nav(bin_),
                   S("approach", target=bin_), S("drop", object=spoon, container=bin_)])
    bin_goal = {"all": [["inside", pin, bin_], ["inside", spoon, bin_], ["hand_empty", "right"]]}
    return {
        "which_bin_by_contents": dict(
            base="large_only", control="large_only", conditions=["decoy_destination", "not_in_view"],
            instruction="Baking is done. Put the rolling pin and the spoon away together in the bin where the "
                        "kitchen utensils are kept.",
            instruction_zh="烘焙结束了，把擀面杖和勺子一起收进放厨房用具的那个箱子里。",
            goal=which_goal, watch=[pin, spoon, bin_, TOY, *[n for n, *_ in toys + tools]],
            factor="which bin is near (seed: the toy bin on the TV stand and the kitchen bin in the bedroom, or the "
                   "other way round)",
            challenge="two wide bins of one make, one on the TV stand and one on the low bookcase in the bedroom; the "
                      "toy bin holds the kid's two blocks, the kitchen bin holds two spoons",
            rationale="the bins look the same from outside: look into the near one; if it holds toys, the utensils go "
                      "to the other one in the bedroom; leave the toys and the spoons where they are",
            cases=which),
        "no_bin_substitute": dict(
            base="large_only", control="large_only", conditions=["container_absent", "small_container_present",
                                                                 "decoy_destination", "not_in_view"],
            remove=[bin_],
            instruction="Baking is done. Put the rolling pin and the spoon away together in one container.",
            instruction_zh="烘焙结束了，把擀面杖和勺子一起收进一个容器里。",
            factor="which substitute and where (seed: the storage basket on the bedroom floor or the serving tray "
                   "on the study desk)",
            challenge="no storage bin in the house; the small bin on the TV stand (22 x 17 cm, two toy blocks in it) "
                      "has no room for the 22 cm rolling pin; the fruit basket on the dining table is big enough but holds an apple and an "
                      "orange; a basket or a tray in another room holds both",
            rationale="no bin is named and none is in the house: measure the near bin, rule it out by size, do not use the "
                      "fruit basket (food), find the substitute in another room and put both utensils in it",
            cases=sub_cases),
        "utensils_apart": dict(
            base="large_only", control="large_only", conditions=["item_out_of_view", "not_in_view"],
            goal=bin_goal, watch=[pin, spoon, bin_],
            factor="where the spoon was left (seed: the dining table or the kitchen counter)",
            challenge="the rolling pin is on the island, the spoon was left in another room (out of view), the bin is "
                      "on the low bookcase in the bedroom",
            rationale="only one utensil is in view: find the bin and the spoon, one hand, so carry them one at a "
                      "time (the pin first, then the spoon)",
            cases=apart),
    }


def T09_long(t):
    POT = "handled_cooking_pot"
    tail = OR(t, "cookware_choice")
    i = at(tail, "navigate", destination="cherry_tomato_1")
    return {
        "pot_in_dining_room": dict(
            base="cookware_choice", control="lid_off", conditions=["cookware_choice", "not_in_view"],
            instruction=t["instruction"], instruction_zh=t["instruction_zh"],     # the task's own words
            move={POT: {"support": "dining_table_2/top", "xy": [3.55, 5.75], "yaw_deg": 0.0}},
            challenge="a breakfast bowl and a mug stand by the tomatoes on the island; the pot is not on the stove but "
                      "on the dining table in the next room, its lid on the stove",
            rationale="the soup needs the pot, not the near bowl or mug: fetch the pot from the dining room to the "
                      "burner, then cook",
            cases={"": dict(route=tail[:2] + [S("search", object=POT, region="dining_room_0_1"), nav(POT), pick(POT),
                                              nav("kitchen_stove/top"), place(POT, "kitchen_stove/top", [8.41, 1.725])]
                            + tail[i:])}),
    }


LONG = {"T03_utensils_one_container": lambda t: {**T03_long(t), **T03_more(t)}, "T09_tomato_soup": T09_long}
# v5 routes that tried the destination they could see was full (a place that fails) before the other one: look at
# it instead and go on
LOOK_FIRST = {"T06_block_destination_occupied": ("occupied", "occupied_block_away")}
def _broken_tried(t):
    """microwave_broken: nothing tells the robot the microwave does not heat; it puts the bowl in, the heat cycle
    fails (the scene fact), then it goes to the stove (the broken_oatmeal_away route without its search)."""
    return [st for st in RT(t, t["oracle"]["broken_oatmeal_away"]) if st["skill"] != "search"]


ROUTE_FIX = {"T07_heat_oatmeal": {"microwave_broken": _broken_tried}}
# variant -> why it leaves v6
REPLACED = {
    ("T12_tidy_toys", "h_mixed_everywhere_ik"): "the same design as toys_everywhere (its injected failures are gone), "
                                                "now seeds of bins_capacity",
    ("T12_tidy_toys", "h_action_grasp_and_ik"): "the same design as toys_everywhere (its injected failures are gone), "
                                                "now seeds of bins_capacity",
    ("T12_tidy_toys", "toys_everywhere"): "merged into bins_capacity (seeds: a half-full bin and a shallow tray)",
    ("T11_collect_fruits", "h_mixed_bowl_there_grasp"): "the same design as basket_gone_bowl_there, now a seed of "
                                                        "basket_missing",
    ("T18_check_cabinet_dishes", "h_task_two_cabinets"): "merged into dishes_spread (seed: the bowl in the other low "
                                                         "cabinet)",
    ("T06_block_destination_occupied", "occupied"): "removed: the lid and the bowl leave room for a 5 cm block, and "
                                                     "either display place counts; display_spot_or_tv is the design",
    ("T06_block_destination_occupied", "occupied_block_away"): "merged into display_spot_or_tv as the seeds with the "
                                                               "block to be found",
    ("T05_pen_or_pencil_to_desk", "h_task_pencil_in_cabinet"): "removed: with the pencil asked for, opening the "
                                                               "cabinet it is in is all that is left (Action-Level)",
    ("T05_pen_or_pencil_to_desk", "h_action_grasp_and_ik"): "removed: the same design as h_task_pencil_in_cabinet",
    ("T04_cup_or_mug_to_cabinet", "h_task_spot_taken"): "replaced by clear_the_drinks_spot (tidy the used kitchen "
                                                        "things off the cabinet, then set the cup)",
    ("T10_trash_the_can", "h_task_can_in_microwave"): "removed: opening the microwave first is a local precondition "
                                                      "(Action); x6_gd_can_put_away is its Task form",
    ("T10_trash_the_can", "h_dynamic_can_moved"): "removed: no dynamic events in T10 (someone takes the can)",
    ("T11_collect_fruits", "h_dynamic_basket_taken"): "removed: no dynamic events in T11 (someone takes the basket)",
    ("T12_tidy_toys", "h_dynamic_duck_taken"): "removed: no dynamic events in T12 (the kid takes the duck)",
    ("T13_breakfast_setup", "bowl_on_cabinet"): "removed: T13 tests reading the scene (copy_the_setting, finish_the_table), not another search",
    ("T13_breakfast_setup", "no_cup_bowl_on_cabinet"): "removed: no_cup and bowl_on_cabinet together, nothing new",
    ("T13_breakfast_setup", "no_cup_spoon_boxed_in"): "removed: moving the boxed-in spoon is clearing at the work spot (Action-Level)",
    ("T13_breakfast_setup", "h_dynamic_mug_taken"): "removed: no dynamic events in T13 (someone takes the mug)",
    ("T14_shelve_the_book", "book_on_desk"): "removed: exposing the flat book is an Action-Level precondition",
    ("T14_shelve_the_book", "shelf_taken"): "removed: clearing the destination is Action-Level",
    ("T14_shelve_the_book", "h_dynamic_shelf_taken"): "removed: no dynamic events in T14",
    ("T15_book_face_up", "h_task_block_on_book"): "removed: clearing the block off the book is Action-Level",
    ("T15_book_face_up", "h_dynamic_book_moved"): "removed: no dynamic events in T15",
    ("T16_rolling_pin_at_edge", "h_task_bowl_behind"): "removed: clearing the bowl from the path is Action-Level",
    ("T16_rolling_pin_at_edge", "h_dynamic_bowl_put_behind"): "removed: no dynamic events in T16",
    ("T17_hide_and_seek_block", "lid_on"): "removed: lifting the lid first is Action-Level",
    ("T17_hide_and_seek_block", "block_crowded"): "removed: separating the crowded block is Action-Level",
    ("T17_hide_and_seek_block", "lid_on_crowded"): "removed: both Action-Level preconditions together",
    ("T17_hide_and_seek_block", "h_dynamic_lid_put_on"): "removed: no dynamic events in T17",
    ("T18_check_cabinet_dishes", "m_door_left_open"): "removed: a door already open is Action-Level",
    ("T18_check_cabinet_dishes", "h_dynamic_door_closed"): "removed: no dynamic events in T18",
    ("T19_recycling", "h_dynamic_cube_moved"): "removed: no dynamic events in T19",
    ("T20_juice_back_to_table", "table_full"): "removed: making room on the table is Action-Level",
    ("T20_juice_back_to_table", "h_dynamic_bottle_taken"): "removed: no dynamic events in T20",
    ("T10_trash_the_can", "far_can_far"): "removed: can_in_dining_room is the same search",
    ("T09_tomato_soup", "lid_on"): "removed: taking the lid off first is a local precondition (Action); it lives on "
                                   "inside lid_on_spoon_away (Action + Task)",
    ("T09_tomato_soup", "h_dynamic_spoon_taken"): "removed: no dynamic events in T09 (someone takes the spoon)",
    ("T08_wipe_island", "island_cluttered"): "replaced by wipe_and_sort (moving the clutter aside and back is a "
                                              "local step; the toys among it go to the toy box by kind)",
    ("T08_wipe_island", "h_dynamic_sponge_taken"): "removed: no dynamic events in T08 (someone takes the sponge)",
    ("T08_wipe_island", "sponge_on_tv_stand"): "removed: far_sponge_tv is the same search over a longer way",
    ("T02_stack_blocks", "crowded"): "replaced by crowded_use_another (prying the wedged block out is ruled out; "
                                     "another block in the house instead)",
    ("T02_stack_blocks", "edge_base"): "removed: choosing the other block as the base is a local step (Action); it "
                                       "lives on inside block_put_away (Action + Task)",
    ("T06_block_destination_occupied", "display_hidden"): "replaced by display_spot_or_tv (the same scene, plus a "
                                                          "layout with the front free)",
    ("T01_book_to_dining_table", "table_set"): "replaced by table_seats (several free slots, the suitable one changes "
                                               "with the setting)",
    ("T01_book_to_dining_table", "h_dynamic_pushed_back"): "removed: two unrelated challenges (no_overhang mid-way "
                                                           "and table_set)",
    ("T01_book_to_dining_table", "no_overhang"): "removed: pushing the book over the edge is a local precondition "
                                                 "(Action), no task-level choice",
    ("T01_book_to_dining_table", "far_no_overhang"): "replaced by which_table (the search was one turn to the island; "
                                                     "now the table the guests eat at is to be found)",
    ("T03_utensils_one_container", "small_and_large"): "replaced by small_bin_or_bedroom_bin (a small bin near, the wide "
                                                       "bin in the bedroom; a mug is no candidate for a rolling pin)",
    ("T03_utensils_one_container", "h_dynamic_pin_taken"): "removed: no dynamic events in T03 (someone takes the "
                                                           "rolling pin away)",
    ("T03_utensils_one_container", "far_small_and_large"): "removed: the bin on the TV stand is the in-place choice "
                                                           "small_bin_or_bedroom_bin replaced, and its route tried the "
                                                           "rolling pin in the mug first",
    ("T03_utensils_one_container", "three_containers"): "replaced by small_bin_or_bedroom_bin, seed beside_wide_bin (both bins in the bedroom)",
    ("T04_cup_or_mug_to_cabinet", "h_dynamic_cup_taken"): "removed: no dynamic events in T04 (someone takes the cup away)",
    ("T09_tomato_soup", "cookware_choice"): "replaced by pot_in_dining_room (the pot in the dining room)",
    ("T02_stack_blocks", "h_dynamic_base_moved_to_edge"): "removed: no dynamic events in T02 (someone pushes the "
                                                          "base to the edge)",
    ("T02_stack_blocks", "far_crowded"): "replaced by tower_for_kid (the search was one turn to the island; now "
                                         "three blocks are spread over the house and the tower goes on the dining "
                                         "table)",
    ("T07_heat_oatmeal", "h_dynamic_door_opened"): "removed: no dynamic events in T07 (someone opens the microwave "
                                                   "door again)",
    ("T06_block_destination_occupied", "h_dynamic_cabinet_filled"): "removed: no dynamic events in T06 (someone "
                                                                     "fills the cabinet top)",
    ("T05_pen_or_pencil_to_desk", "h_dynamic_pencil_taken"): "removed: no dynamic events in T05 (someone takes the "
                                                             "pencil away)",
    ("T05_pen_or_pencil_to_desk", "no_pen"): "removed: no_pen_pencil_away is the same choice over a longer horizon",
}


NEW_CONDITIONS = {
    "workspace_choice": {"type": "feasibility", "decision": "decompose",
                         "meaning": "the action cannot be done where the object is (no room to turn the book "
                                    "over inside the shelf): move it to a place where it can, then back"},
    "history_exclusion": {"type": "goal_inference", "decision": "alternative",
                          "meaning": "the usual choice is ruled out by what happened before (the kid found the "
                                     "block in the pot last time): pick another one that meets the goal"},
    "count_against_need": {"type": "goal_inference", "decision": "decompose",
                           "meaning": "count what is there against what is needed and act on the difference only "
                                      "(nothing, or fetch the missing ones)"},
    "agent_ability": {"type": "goal_inference", "decision": "decompose",
                      "meaning": "where or what follows from what another person can do (the kid reaches only low "
                                 "shelves), even against where the thing usually belongs"},
    "goal_by_example": {"type": "goal_inference", "decision": "decompose",
                        "meaning": "what to do is shown by an example in the scene (a set place): copy which things "
                                   "and where, in the frame of the person it is for; a missing kind is replaced by "
                                   "the closest one in the same spot"},
    "rule_induction": {"type": "goal_inference", "decision": "decompose",
                       "meaning": "several examples follow rules that depend on who they are for (adults: a mug, "
                                  "the kid: a plastic cup); induce the rules and apply the one that fits"},
    "relational_exception": {"type": "goal_inference", "decision": "decompose",
                             "meaning": "objects of one kind are treated differently by how they stand: the blocks "
                                        "built into the kid's castle stay, loose ones are put away"},
    "preference_allocation": {"type": "goal_inference", "decision": "decompose",
                              "meaning": "one of the items is set aside for a person; which one follows from what "
                                         "the instruction says about them (the kid does not like oranges)"},
    "subgoal_order": {"type": "goal_structure", "decision": "decompose",
                      "meaning": "the subgoals must be ordered so each step is feasible (the empty tray to its "
                                 "place first, then the fruit onto it; never lift a loaded tray)"},
    "closed_fridge": {"type": "access", "decision": "precondition",
                      "meaning": "the item is in the closed fridge next to the work spot: open it, take the item, "
                                 "close it again (the Action-Level part of a Task-Level design)"},
    "disposal_by_state": {"type": "goal_inference", "decision": "decompose",
                          "meaning": "the instruction names kinds of destination (trash, fridge, counter); which "
                                     "object goes where follows from what it is and its state (an empty disposable "
                                     "tray is rubbish, a glass box with food is leftovers)"},
    "resource_in_use": {"type": "resource_state", "decision": "alternative",
                        "meaning": "the resource the instruction names is there but already in use (a pot full of "
                                   "other soup): it is not to be used or disturbed; another one is fetched"},
    "category_rule": {"type": "goal_inference", "decision": "decompose",
                      "meaning": "the instruction gives a rule by kind (the kid's toys away, the kitchen things stay); "
                                 "what happens to each object follows from what it is"},
    "storage_place": {"type": "destination_identity", "decision": "explore",
                      "meaning": "the item is to go back where it is normally kept; that place is not named and "
                                 "follows from the scene (where items of its kind are kept)"},
    "referent_clue": {"type": "referent_identity", "decision": "explore",
                      "meaning": "the instruction names the object or place by a clue (whose it is, where it was "
                                 "used), not by its name; the nearest look-alike is not the one meant"},
    "infeasible_fallback": {"type": "goal_feasibility", "decision": "alternative",
                            "meaning": "under the stated constraints the goal may not be reachable: check, and if not, "
                                       "take the fallback the instruction names instead of breaking a constraint"},
    "appliance_compatibility": {"type": "appliance_choice", "decision": "replace",
                                "meaning": "which appliance can heat an item follows from its container (metal "
                                           "not in the microwave, a ceramic bowl not on the burner)"},
    "arrangement": {"type": "spatial_arrangement", "decision": "decompose",
                    "meaning": "several objects make one layout (a row, spacing, squared): each placement leaves room "
                               "for the next"},
    "viewer_place": {"type": "destination_identity", "decision": "explore",
                     "meaning": "the instruction names who is to see it, not where: the place follows from where the "
                                "viewer is"},
    "goal_already_met": {"type": "goal_state", "decision": "verify",
                         "meaning": "what the instruction asks for already holds: check, and do not fetch again"},
    "unknown_count": {"type": "resource_count", "decision": "explore",
                      "meaning": "how many items the goal covers is not said: search every place before stopping"},
    "goal_items_unstated": {"type": "goal_inference", "decision": "decompose",
                            "meaning": "the instruction names a purpose; which items it needs is to be inferred"},
    "count_from_scene": {"type": "goal_inference", "decision": "decompose",
                         "meaning": "how many items to bring is read off the scene, not the instruction"},
    "errands_combined": {"type": "goal_structure", "decision": "decompose",
                         "meaning": "two errands meet at one place; an order that joins them saves a trip"},
    "missing_piece": {"type": "object_absent", "decision": "alternative",
                      "meaning": "the goal needs one more piece than the house has (no third block); another item of "
                                 "the kind the instruction names (another toy) stands in, in another room; a look-alike "
                                 "of another kind nearby (the sponge) does not count"},
    "destination_unnamed": {"type": "destination_identity", "decision": "explore",
                            "meaning": "several places fit the instruction's words; which one is meant (the table "
                                       "the guests eat at) shows only on looking, possibly in another room"},
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
              ("kitchen_cabinet_4/top", [1.4, 0.42], None), ("kitchen_cabinet_6/top", [3.7, 0.36], "living_room_0_0"),
              ("bookcase_2/top", [1.0, -0.43], "bedroom_0_1")]
SEED_EXT = {
    ('T04_cup_or_mug_to_cabinet', 'no_cup_mug_away'): 0,
    # the TV stand is T06's other display place and kitchen cabinet 4 another low wall cabinet: the kid's bookcase
    ('T06_block_destination_occupied', 'occupied_block_away'): 4,
    ('T07_heat_oatmeal', 'broken_oatmeal_away'): 0,
    ('T08_wipe_island', 'far_sponge_tv'): 0,
    ('T08_wipe_island', 'h_dynamic_sponge_taken'): 0,
    ('T09_tomato_soup', 'h_dynamic_spoon_taken'): 0,
    ('T09_tomato_soup', 'lid_on_spoon_away'): 0,
    ('T10_trash_the_can', 'can_in_dining_room'): 1,
    ('T10_trash_the_can', 'far_can_far'): 0,
    ('T10_trash_the_can', 'h_dynamic_can_moved'): 1,
    ('T12_tidy_toys', 'duck_in_study'): 0,
    ('T19_recycling', 'h_action_grasp_and_miss'): 1,
    ('T19_recycling', 'h_mixed_lookalike_ik'): 1,
    ('T19_recycling', 'lookalike_bin'): 1,
    ('T19_recycling', 'm_can_in_dining_room'): 1,
    ('T20_juice_back_to_table', 'm_bottle_on_tv_stand'): 0,
}


# v5 variants that are one design with the layout changed: merged into the first as its seeds
MERGE = {("T04_cup_or_mug_to_cabinet", "no_cup"): ["no_cup_mug_away"],
         ("T07_heat_oatmeal", "microwave_broken"): ["broken_oatmeal_away"],
         ("T11_collect_fruits", "basket_missing"): ["basket_gone_bowl_there"],
         ("T22_put_away_shopping", "tray_elsewhere"): ["basket_missing"],
         ("T27_leftovers_to_fridge", "which_is_leftover"): ["fruit_stays_out", "still_eating"],
         ("T29_clear_table_for_dinner", "belongs_on_table"): ["nothing_to_clear"],
         ("T30_bowls_for_soup", "bowl_not_plate"): ["clean_one"]}
MERGE_FACTOR = {("T04_cup_or_mug_to_cabinet", "no_cup"): "where the mug is (seed: on the island in view, on the TV "
                                                         "stand or on the dining table, out of view)",
                ("T07_heat_oatmeal", "microwave_broken"): "where the oatmeal is (seed: by the microwave, or elsewhere "
                                                          "and to be found first)",
                ("T11_collect_fruits", "basket_missing"): "what stands where the basket used to be (seed: nothing, or "
                                                          "a used breakfast bowl)",
                ("T12_tidy_toys", "bins_capacity"): "which containers there are and how full (seed: two small bins, "
                                                    "one full, side by side or apart; or a half-full bin and a "
                                                    "shallow tray with the duck to be found)",
                ("T22_put_away_shopping", "tray_elsewhere"): "where the stand-in for the basket is and what lies on "
                                                             "it (seed: a tray on the island; the tray in the west "
                                                             "dining room with an orange, or covered with books)",
                ("T27_leftovers_to_fridge", "which_is_leftover"): "what else is on the table that is not leftovers "
                                                                  "(seed: an empty takeout tray; the fruit basket "
                                                                  "and cereal; a bowl someone is still eating from)",
                ("T29_clear_table_for_dinner", "belongs_on_table"): "what is on the table besides the place setting "
                                                                    "(seed: a toy car, or nothing)",
                ("T30_bowls_for_soup", "bowl_not_plate"): "what stands next to the clean bowl (seed: a plate, or a "
                                                          "bowl still full of oatmeal)",
                ("T28_cup_to_bedside", "where_his_cup_is"): "where his cup is and what else stands on the counter "
                                                            "(seed: on the counter among other cups; in the cabinet "
                                                            "with other cups on the counter; in the cabinet, the "
                                                            "counter empty)"}


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
    # the v5 route may work on right after the pick (the item was within reach of the work spot); from the new
    # place the robot walks back first
    for j, st in enumerate(steps):
        if st["skill"] == "pick" and st["args"].get("object") == x and j + 1 < len(steps):
            nxt = steps[j + 1]
            if nxt["skill"] not in ("navigate", "search"):
                to = next((nxt["args"][k] for k in ("target", "receptacle", "surface", "container", "base")
                           if nxt["args"].get(k)), None)
                if to:
                    steps.insert(j + 1, {"skill": "navigate", "args": {"destination": to}})
            break
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
    if ("instruction" in spec or "instruction" in cspec) and not ("instruction_zh" in spec or "instruction_zh" in cspec):
        v.pop("instruction_zh", None)            # the Chinese text of the base no longer matches
    fails = copy.deepcopy(spec.get("failures", [])) + copy.deepcopy(cspec.get("failures", []))
    if fails:
        v["failures"] = fails
    v["since"] = "v6"
    if spec.get("keep_design"):
        v["keep_design"] = list(spec["keep_design"])     # the seed leaves the design on these supports as it is
    v["note"] = spec["challenge"]
    v["v6"] = {"family": fam, "case": case or None, "challenge": spec["challenge"], "rationale": spec["rationale"], "control": spec["control"],
               "contrast": spec.get("contrast"), "factor": spec.get("factor"),
               "derived_from": spec["base"], **({"viewer": spec["viewer"]} if spec.get("viewer") else {})}
    v["move"], v["vary"] = seed_vary(t, v)
    return v


# Families whose cases differ in the design (which object blocks, which failure, which subgoal the event undoes,
# how many places are named), not only in where things are: each case is a variant of its own.  The other
# multi-case families keep one variant whose seeds choose among layouts (where the resource / substitute /
# item is, where an event takes it, which bin is full).
SPLIT = set()


# conditions that are no challenge for the variant's own instruction: it names the substitute itself
NOT_A_CHALLENGE = {("T05_pen_or_pencil_to_desk", "e1_pencil_asked"): ["no_pen"],
                   # a pencil is asked for: no pen in the house is no longer a substitution
                   ("T05_pen_or_pencil_to_desk", "no_pen_pencil_away"): ["no_pen"],
                   ("T05_pen_or_pencil_to_desk", "e2_pencil_asked_far"): ["no_pen"]}


# a task whose v5 instruction spelled out every place and fallback: one short instruction for the task and all of
# its v5 variants (where things go is for the robot to work out)
TASK_TEXT = {
    # asks for a cup only (no "a mug will do"): a mug is a cup too, whether to settle for it the robot decides
    "T04_cup_or_mug_to_cabinet": ("A guest is coming. Set out a cup at the drinks spot on the low wall cabinet.",
                                  "有客人要来，在靠墙矮柜上的饮品角摆一个杯子。"),
    "T11_collect_fruits": ("Lunch is over and the apple is still on the dining table. Put it away.",
                           "午饭吃完了，苹果还在餐桌上，把它收起来。"),
    "T12_tidy_toys": ("It is nearly bedtime. Put the kid's toys away.", "快到睡觉时间了，把孩子的玩具收起来。"),
    "T13_breakfast_setup": ("Breakfast is soon. Set the place at the dining table.", "快吃早饭了，把餐桌上的位子摆好。"),
    "T14_shelve_the_book": ("The kid finished reading. Put the book away for him.", "孩子看完书了，帮他把书收好。"),
    "T15_book_face_up": ("A paperback has been lying face down on the kitchen island; its spine is getting bent. "
                         "Please sort it out; leave it on the island, he has not finished it.",
                         "岛台上有本平装书一直扣着放，书脊都快压弯了，帮忙处理一下。书还放在岛台上，他还没看完。"),
    "T19_recycling": ("Movie night is over. Put what goes to recycling into the recycling bin.",
                      "电影看完了，把该回收的东西放进回收箱。"),
}


# a v5 variant whose own instruction read like a form ("heat it in a suitable way ..."): it takes the task's
INSTR_TO_TASK = {("T07_heat_oatmeal", "microwave_holds_pot"), ("T07_heat_oatmeal", "h_mixed_pot_inside_grasp")}


def build_task(t: dict) -> dict:
    t = copy.deepcopy(t)
    if t["task_id"] in TASK_TEXT:
        t["instruction"], t["instruction_zh"] = TASK_TEXT[t["task_id"]]
        for v in t["variants"].values():
            v.pop("instruction", None)
            v.pop("instruction_zh", None)
    for tid, vid in INSTR_TO_TASK:
        if tid == t["task_id"]:
            t["variants"][vid].pop("instruction", None)
            t["variants"][vid].pop("instruction_zh", None)
    fams = FAMILIES[t["task_id"]](t) if t["task_id"] in FAMILIES else {}
    if t["task_id"] in LONG:
        fams.update(LONG[t["task_id"]](t))
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
    for vid, fix in ROUTE_FIX.get(t["task_id"], {}).items():
        for lid in families[vid]["layouts"]:
            t["routes"][f"v6_{lid}"] = {"steps": fix(t), "kind": "v6_route_fix", "variant": lid}
            t["oracle"][lid] = f"v6_{lid}"
    for vid in LOOK_FIRST.get(t["task_id"], ()):
        for lid in families[vid]["layouts"]:
            steps, out = t["routes"][t["oracle"][lid]]["steps"], []
            for i, st in enumerate(steps):
                nxt = steps[i + 1] if i + 1 < len(steps) else {}
                if st["skill"] == "navigate" and nxt.get("skill") == "place" and nxt.get("expect") == "fail":
                    continue                            # the trip to the full destination ...
                if st["skill"] == "place" and st.get("expect") == "fail":
                    out.append(look(st["args"]["receptacle"]))     # ... becomes a look at it
                    continue
                out.append(st)
            t["routes"][f"v6_{lid}"] = {"steps": out, "kind": "v6_look_first", "variant": lid}
            t["oracle"][lid] = f"v6_{lid}"
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
    for (tid, into), parts in MERGE.items():        # one design, the layouts differ: one family, the parts its seeds
        if tid == t["task_id"]:
            fam = families[into]
            fam["layouts"] = [*fam["layouts"], *[lid for p in parts for lid in families.pop(p)["layouts"]]]
            fam["seeds"] = seed_cases(t["task_id"], into, fam["layouts"])
            fam["factor"] = MERGE_FACTOR[(tid, into)]
    t["v6_variants"] = families
    t["v6_replaced"] = {vid: why for (tid, vid), why in REPLACED.items() if tid == t["task_id"]}
    for (tid, vid), conds in NOT_A_CHALLENGE.items():
        if tid == t["task_id"]:
            v = t["variants"][vid]
            v["conditions"] = [c for c in v.get("conditions", []) if c not in conds]
            if not v["conditions"]:
                v.pop("conditions")
            v["conditions_ignored"] = conds
    for k in ("v5_formal", "v5_study", "v5_supplementary"):       # v5's tier lists; v6 lists families instead
        t.pop(k, None)
    t["benchmark_version"] = "v6"
    return t


def exact_base_poses(t, v):
    """Watched task objects still at their base pose whose yaw the v5 seed shift could not read off the box (not 0 /
    90 deg, e.g. the spoon at 131 deg, the rolling pin whose mesh box is wider than its size): their pose from the
    base scene's task.json (exact yaw), so the seed moves them too."""
    import math
    base = ROOT / t["scene"]["base"]
    placed = json.loads((base / "task.json").read_text()).get("placed_objects", {})
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    sups = {x["name"] for x in json.loads((base / "annotation.json").read_text())["supports"]}
    removed = set(t["scene"].get("remove", [])) | set(v.get("remove", []))
    have = set(t["scene"].get("move", {})) | set(v.get("move", {})) | set(v.get("add", {}))
    out = {}
    for n in dict.fromkeys([*(t.get("watch") or []), *(v.get("watch") or [])]):
        o = placed.get(n)
        if not o or n in have or n in removed or o.get("support") not in sups:
            continue
        yaw = float(o.get("yaw", 0.0))
        ox, oy = assets[o["asset"]]["origin_to_bottom_center"][:2]
        x = o["position"][0] + math.cos(yaw) * ox - math.sin(yaw) * oy
        y = o["position"][1] + math.sin(yaw) * ox + math.cos(yaw) * oy
        out[n] = {"support": o["support"], "xy": [round(x, 4), round(y, 4)], "yaw_deg": round(math.degrees(yaw), 2)}
    return out


def build() -> dict:
    doc = json.loads(V5.read_text())
    from benchmark.v6.new_tasks_v6 import NEW_CONDITIONS as NEW_TASK_CONDITIONS, families_for, new_base_tasks
    new = [t for t, _ in new_base_tasks()]       # T21-T30: base tasks of v6's own, built like the v5 ones
    for t in new:
        FAMILIES.setdefault(t["task_id"], lambda t, tid=t["task_id"]: families_for(tid))
    tasks = [build_task(t) for t in doc["tasks"] + new]
    reg = dict(doc["condition_registry"], **NEW_CONDITIONS, **NEW_TASK_CONDITIONS)
    out = {"schema_version": 6, "benchmark_version": "v6", "kind": "zenobench_benchmark_tasks",
           "note": "Source: python benchmark/v6/define_tasks_v6.py (reads benchmark/v5/tasks.json); tracks: "
                   "benchmark/v6/tracks.py.",
           "eval_seeds": SEEDS, "condition_registry": reg, "tasks": tasks}
    from benchmark.v6.layout import layout_spec
    from benchmark.v6.tracks import apply_tracks, strip_injected
    strip_injected(out)
    for t in out["tasks"]:                       # the seed draws the layout (benchmark/v6/layout.py)
        for info in t["v6_variants"].values():
            for lid in info["layouts"]:
                v = t["variants"][lid]
                v["move"] = {**v.get("move", {}), **exact_base_poses(t, v)}
                v["move"], _ = seed_vary(t, v)   # task objects still at their base pose join the overlay
                v.pop("vary", None)
                c = info.get("control")
                ctl = t["v6_variants"][c]["layouts"][0] if c in t["v6_variants"] else None
                v["layout"] = layout_spec(t, lid, reg, ctl)
    from benchmark.v6.oracle_check import observe_first
    for t in out["tasks"]:                       # reference routes look before they use what was not seen
        for info in t["v6_variants"].values():
            c = info.get("control")
            ctl = t["v6_variants"][c]["layouts"][0] if c in t["v6_variants"] else None
            for lid in info["layouts"]:
                if observe_first(t, lid):
                    t["variants"][lid]["layout"] = layout_spec(t, lid, reg, ctl)
                    observe_first(t, lid)
    apply_tracks(out)
    # approach left the library (benchmark/retired_skills.py): its steps in the routes v6 inherits from v5
    # and in its own designs become the navigate they still need, or go when a navigate there precedes them
    return drop_retired_steps(out)


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
