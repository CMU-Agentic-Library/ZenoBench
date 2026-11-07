"""T21-T30: ten new base tasks of v6, everyday goals with one step of reasoning each (the easy end).

The same house and existing assets only.  Each task is a control plus five Task-Level variants; no Action-Level
variant, no dynamic event.  The instruction states the goal; where, with what and how is left to the robot.

A base task here has the v5 shape (``build_task`` in define_tasks_v6.py takes it like a v5 task): a control
variant (a family of its own, origin "v5" in the catalog sense of "the task's nominal variant") and a helper
variant ``bare`` (the scene with none of the task's objects) that the five families start from.  Objects are
always added under new names: a name the scene removes cannot be placed again.
"""
from __future__ import annotations

import copy

from benchmark.v5.define_tasks_v5 import P, S

SEEDS = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
BASE = "tasks/kitchen_skills"
# the island's and the table's v5 task objects: none of them belongs to T21-T30 (the household's plates, bowls,
# cups, mugs, spoons, the pot on the stove and the trash can stay)
CLEAR = ["mug", "cherry_tomato_1", "cherry_tomato_2", "cherry_tomato_3", "wooden_block_a", "wooden_block_b",
         "juice_bottle", "rolling_pin", "paperback_book", "soda_can", "wide_storage_bin", "oatmeal", "floor_block",
         "kitchen_sponge", "breakfast_spoon", "spoon_target_table"]
T1, T2, ISL, TV, DESK, DESK3 = ("dining_table_1/top", "dining_table_2/top", "kitchen_island/top", "tv_stand_2/top",
                                "desk_1/top", "desk_3/top")
FR, FS = "breakfast_fridge", "breakfast_fridge/inside_shelf"
C4, C6 = "kitchen_cabinet_4", "kitchen_cabinet_6"
COUNTER = "kitchen_counter_2/top"


def nav(x):
    return S("navigate", destination=x)


def pick(x):
    return S("pick", object=x)


def place(x, r, hint=None):
    return S("place", object=x, receptacle=r, **({"hint_xy": list(hint)} if hint else {}))


def look(x):
    return S("look", target=x)


def on(asset, sup, x, y, yaw=0.0):
    return {"asset": asset, **P(sup, x, y, yaw)}


def floor(asset, x, y, yaw=0.0):
    return {"asset": asset, "support": None, "z": 0.0, "xy": [x, y], "yaw_deg": yaw}


def fetch(x, sup, hint=None):
    return [nav(x), pick(x), nav(sup), place(x, sup, hint)]


def into(x, cont):
    return [nav(x), pick(x), nav(cont), place(x, cont)]


def explore(art):
    return [nav(art), S("open", articulated=art), S("bend"), S("explore_furniture", furniture=art), S("straighten")]


def from_closed(x, art):
    """take x out of the open cabinet / fridge and close it"""
    return [nav(x), pick(x), S("retreat", obstacle=art, distance_m=0.3), S("close", articulated=art)]


def fridge(items):
    """open the fridge, put each item in, close it (one hand: the door first)"""
    out = [nav(FR), S("open", articulated=FR)]
    for k, x in enumerate(items):
        out += [nav(x), pick(x), nav(FR), place(x, FS, [5.78 + 0.2 * (k % 2), 3.18 + 0.2 * (k // 2)])]
    return out + [S("close", articulated=FR)]


def base_task(tid, exp, instr, instr_zh, ctl, ctl_spec, goal, route, watch, remove=(), start=None):
    note = ctl_spec.pop("note")
    v = {"note": note, "since": "v6", "condition_types": [], "decisions": ["none"],
         "v5": {"tier": "easy", "challenge": note, "existing": False}, **ctl_spec}
    if start:
        v["start"] = list(start)
    bare = {"note": "helper: the scene without the task's objects; the v6 variants start from it", "since": "v6"}
    if start:
        bare["start"] = list(start)
    return {
        "task_id": tid, "exp_id": exp, "since": "v6", "source": ["benchmark/v6/new_tasks_v6.py"],
        "instruction": instr, "instruction_zh": instr_zh,
        "scene": {"base": BASE, "remove": sorted(set(CLEAR) | set(remove)), "distractors": []},
        "variants": {ctl: v, "bare": bare}, "watch": list(watch), "goal": goal, "nominal": "nominal",
        "oracle": {ctl: "nominal"}, "routes": {"nominal": {"kind": "nominal", "variants": [ctl], "steps": route}},
        "vary": {}, "not_adopted": [], "benchmark_version": "v6", "eval_seeds": SEEDS, "entities": [],
        "v5_study": [], "v5_formal": {"easy": [ctl]}, "v5_supplementary": []}


def fam(control, conditions, factor, challenge, rationale, cases, **kw):
    return dict(base="bare", control=control, conditions=conditions, factor=factor, challenge=challenge,
                rationale=rationale, cases=cases, **kw)


H = ["hand_empty", "right"]
# the household's own clean bowls and cups (base scene): bringing one of them does what was asked as well
HOUSE_BOWLS = ["bowl_dining_cabinet", "bowl_kitchen_cabinet", "bowl_side_table", "bowl_inside_kitchen_cabinet"]
HOUSE_CUPS = ["cup_counter_b", "cup_kitchen_cabinet", "cup_side_table", "mug_dining_cabinet", "mug_shelf", "mug_counter"]


# ================================================================== T21 bring tissues to the spill
def t21():
    TIS = "tissue"
    meal = {"soup_bowl": on("oatmeal_bowl", T2, 3.10, 6.95), "meal_spoon": on("breakfast_spoon", T2, 3.10, 7.14)}
    ctl = {"note": "the tissue box on the TV stand, a bowl of soup on the dining table",
           "add": {TIS: on("tissue_box", TV, 7.60, 0.36), **meal}}
    t = base_task("T21_bring_tissues", "ZB-T21", "Some soup got spilled at the dining table. Bring some tissues over.",
                  "餐桌上洒了点汤，拿点纸巾过去。", "tissue_on_tv_stand", ctl,
                  {"all": [["on", TIS, T2], H]}, fetch(TIS, T2, [3.30, 6.65]), [TIS, "soup_bowl"])
    to_table = lambda x=TIS, sup=T2, hint=(3.30, 6.65): fetch(x, sup, hint)  # noqa: E731
    west_meal = {"soup_bowl": on("oatmeal_bowl", T1, -7.95, 7.60), "meal_spoon": on("breakfast_spoon", T1, -7.95, 7.79)}
    side = {"bowl_side_table", "cup_side_table", "spoon_side_table"}
    kid_n = {"kid_bowl": on("oatmeal_bowl", T2, 3.35, 7.45), "kid_cup": on("plastic_cup", T2, 3.60, 7.45),
             "adult_bowl": on("oatmeal_bowl", T2, 3.35, 6.40), "adult_mug": on("breakfast_mug", T2, 3.60, 6.40)}
    kid_s = {"kid_bowl": on("oatmeal_bowl", T2, 3.35, 6.40), "kid_cup": on("plastic_cup", T2, 3.60, 6.40),
             "adult_bowl": on("oatmeal_bowl", T2, 3.35, 7.45), "adult_mug": on("breakfast_mug", T2, 3.60, 7.45)}
    kid_goal = {"all": [["on", TIS, T2], ["near_any", TIS, ["kid_bowl", "kid_cup"], 0.15],
                        ["not near_any", TIS, ["adult_bowl", "adult_mug"], 0.25], H]}
    fams = {
        "tissue_out_of_view": fam(
            "tissue_on_tv_stand", ["not_in_view"], "the seed's layout only",
            "the tissue box is not on the TV stand where it usually is but on the study desk, out of view",
            "find the tissues first, then bring them to the table",
            {"": dict(add={TIS: on("tissue_box", DESK, -0.70, -5.95), **meal},
                      route=[S("search", object=TIS, region="living_room_0_1")] + to_table())}),
        "which_table": fam(
            "tissue_on_tv_stand", ["destination_unnamed"], "which table the meal is on (seed: east or west dining room)",
            "two dining tables; a bowl of soup stands on one of them, the other is bare",
            "the spill is where someone eats: look which table has the meal and bring the tissues there",
            {"east": dict(add={TIS: on("tissue_box", TV, 7.60, 0.36), **meal}, remove=sorted(side),
                          goal={"all": [["on", TIS, T2], H]},
                          route=[nav(TIS), pick(TIS), look(T1), nav(T2), place(TIS, T2, [3.30, 6.65])]),
             "west": dict(add={TIS: on("tissue_box", TV, 7.60, 0.36), **west_meal}, remove=sorted(side),
                          goal={"all": [["on", TIS, T1], H]},
                          route=[nav(TIS), pick(TIS), look(T2), nav(T1), place(TIS, T1, [-7.75, 7.40])])}),
        "no_tissue": fam(
            "tissue_on_tv_stand", ["resource_absent"], "the seed's layout only",
            "there are no tissues in the house; a dry kitchen sponge lies on the island",
            "the purpose is to wipe the spill: bring the closest thing that does that (the sponge)",
            {"": dict(add={"spare_sponge": on("kitchen_sponge", ISL, 8.00, 1.80), **meal},
                      goal={"all": [["on", "spare_sponge", T2], H]}, watch=["spare_sponge", "soup_bowl"],
                      route=[look(TV)] + to_table("spare_sponge"))}),
        "tissue_put_away": fam(
            "tissue_on_tv_stand", ["item_put_away"], "which low cabinet holds the tissues (seed)",
            "the tissue box was put away in one of the two low wall cabinets",
            "look in the cabinets until the tissues are found, take them out, close the doors",
            {f"in_{a[-1]}": dict(
                add={TIS: on("tissue_box", f"{a}/inside_shelf", *xy), **meal},
                remove=["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"],
                goal={"all": [["on", TIS, T2], ["is_closed", C4], ["is_closed", C6], H]},
                route=explore(o) + [S("close", articulated=o)] + explore(a) + from_closed(TIS, a)
                + [nav(T2), place(TIS, T2, [3.30, 6.65])])
             for a, o, xy in ((C4, C6, (1.40, 0.42)), (C6, C4, (3.50, 0.36)))}),
        "the_kids_side": fam(
            "tissue_on_tv_stand", ["referent_clue"], "which end of the table the kid sits at (seed)",
            "two places at the table: the kid's (a plastic cup) and a grown-up's (a mug)",
            "the kid spilled: tell the kid's place by the plastic cup and put the tissues next to it",
            {c: dict(add={TIS: on("tissue_box", TV, 7.60, 0.36), **places}, goal=kid_goal,
                     watch=[TIS, *places],
                     route=fetch(TIS, T2, [3.10, places["kid_cup"]["xy"][1]]))
             for c, places in (("kid_north", kid_n), ("kid_south", kid_s))},
            instruction="The kid spilled some soup at the dining table. Bring him some tissues.",
            instruction_zh="孩子吃饭把汤洒了，拿点纸巾给他。"),
        "no_tissue_sponge_away": fam(
            "tissue_on_tv_stand", ["resource_absent", "item_put_away", "dependent_decisions"], "the seed's layout only",
            "no tissues in the house and nothing to wipe with in sight; a dry sponge is kept in the low wall cabinet",
            "each decision rests on what the last one found: the tissues are not where they are kept, so something "
            "else that wipes; nothing like that is out, so where such things are kept; take it out, close the door",
            {"": dict(add={"spare_sponge": on("kitchen_sponge", f"{C4}/inside_shelf", 1.40, 0.42), **meal},
                      goal={"all": [["on", "spare_sponge", T2], ["is_closed", C4], H]}, watch=["spare_sponge", "soup_bowl"],
                      route=[look(TV), look(ISL)] + explore(C4) + from_closed("spare_sponge", C4)
                      + [nav(T2), place("spare_sponge", T2, [3.30, 6.65])])}),
    }
    return t, fams


# ================================================================== T22 put the shopping away
def t22():
    J, A, SN = "bought_juice", "bought_apple", "bought_snack"
    BASKET = "home_basket"
    ctl = {"note": "a bottle of juice from the shop on the dining table", "add": {J: on("juice_bottle", T2, 3.30, 6.70)}}
    jgoal = [["on", J, FS], ["upright", J], ["is_closed", FR]]
    t = base_task("T22_put_away_shopping", "ZB-T22", "Put the shopping away.", "买回来的东西放好。",
                  "juice_on_table", ctl, {"all": jgoal + [H]}, fridge([J]), [J],
                  remove=["clutter_cereal_a", "clutter_cereal_b"])
    pantry = {"old_snack": on("snack_carton", f"{C6}/inside_shelf", 3.35, 0.36)}
    no_dishes = ["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"]
    snack_away = [nav(C6), S("open", articulated=C6), S("inspect", receptacle=C6), nav(SN), pick(SN), nav(C6),
                  place(SN, f"{C6}/inside_shelf", [3.60, 0.36]), S("close", articulated=C6)]
    fams = {
        "by_kind": fam(
            "juice_on_table", ["storage_place", "multi_object_goal"], "the seed's layout only",
            "juice, an apple and a box of snacks on the table; the fruit basket is on the island, the snacks are "
            "kept in the low wall cabinet (an opened box is already there)",
            "each item where its kind is kept: the juice in the fridge, the apple in the fruit basket, the snack "
            "box in the cabinet with the other snacks",
            {"": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), A: on("apple", T2, 3.30, 7.00),
                           SN: on("snack_carton", T2, 3.30, 7.30), BASKET: on("fruit_basket", ISL, 7.10, 1.78),
                           **pantry},
                      remove=no_dishes, watch=[J, A, SN, BASKET],
                      goal={"all": jgoal + [["inside", A, BASKET], ["on", SN, f"{C6}/inside_shelf"],
                                            ["is_closed", C6], H]},
                      route=fridge([J]) + into(A, BASKET) + snack_away)}),
        "eat_now": fam(
            "juice_on_table", ["preference_allocation"], "the seed's layout only",
            "juice and a box of snacks; the kid doing homework in the study wants the snacks now",
            "the snacks are not put away but brought to the kid; the juice goes into the fridge",
            {"": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), SN: on("snack_carton", T2, 3.30, 7.00),
                           "homework": on("notebook", DESK, -0.70, -5.95)},
                      watch=[J, SN], goal={"all": jgoal + [["on", SN, DESK], H]},
                      route=fridge([J]) + fetch(SN, DESK, [-1.10, -5.95]))},
            instruction="Put the shopping away. The kid says he wants the snacks now; he is doing homework in "
                        "the study.",
            instruction_zh="买回来的东西放好。孩子说零食现在就要吃，他在书房写作业。"),
        "basket_missing": fam(
            "juice_on_table", ["container_absent", "storage_place"], "the seed's layout only",
            "juice and an apple; no fruit basket in the house, a serving tray on the island",
            "the apple has no basket to go to: the tray stands in for it; the juice into the fridge",
            {"": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), A: on("apple", T2, 3.30, 7.00),
                           "fruit_tray": on("serving_tray", ISL, 7.20, 1.75)},
                      watch=[J, A, "fruit_tray"],
                      goal={"all": jgoal + [["inside", A, "fruit_tray"], H]},
                      route=fridge([J]) + into(A, "fruit_tray"))}),
        "not_shopping": fam(
            "juice_on_table", ["goal_items_unstated"], "the seed's layout only",
            "the juice from the shop, and the kid's toy car and picture book on the same table",
            "only what was bought is put away: the toy and the book are not shopping and stay",
            {"": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), "table_car": on("toy_car", T2, 3.30, 7.10),
                           "table_book": on("book_blue", T2, 3.35, 6.20)},
                      watch=[J, "table_car", "table_book"],
                      goal={"all": jgoal + [["near_start", "table_car", 0.03], ["near_start", "table_book", 0.03], H]},
                      route=[look(T2)] + fridge([J]))}),
        "two_spots": fam(
            "juice_on_table", ["goal_items_unstated", "not_in_view"], "the seed's layout only",
            "the juice on the dining table; a second bag was emptied on the island: an apple and a box of "
            "snacks there, the basket next to them",
            "the shopping is in two places: find both, put each item away",
            {"": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), A: on("apple", ISL, 7.60, 1.75),
                           SN: on("snack_carton", ISL, 7.85, 1.75), BASKET: on("fruit_basket", ISL, 7.10, 1.78),
                           **pantry},
                      remove=no_dishes, watch=[J, A, SN, BASKET],
                      goal={"all": jgoal + [["inside", A, BASKET], ["on", SN, f"{C6}/inside_shelf"],
                                            ["is_closed", C6], H]},
                      route=[look(T2)] + fridge([J]) + [look(ISL)] + into(A, BASKET) + snack_away)}),
    }
    return t, fams


# ================================================================== T23 pick up what was dropped
def t23():
    SP = "dropped_spoon"
    START = (-1.20, 9.40, 0.0)                       # the small kitchen with the counter
    ctl = {"note": "a spoon on the kitchen floor; the spoons are kept on the kitchen counter",
           "add": {SP: floor("breakfast_spoon", -0.85, 7.70, 30.0)}}
    # either kitchen counter is where a spoon belongs (the kitchen's two counters stand 1.7 m apart)
    sgoal = [["on_any", SP, [COUNTER, "kitchen_counter_1/top"]]]
    t = base_task("T23_pick_up_dropped", "ZB-T23", "Something fell on the floor. Please pick it up and put it "
                  "where it belongs.", "地上掉了东西，帮忙捡起来放好。", "spoon_on_floor", ctl,
                  {"all": sgoal + [H]}, [look(COUNTER)] + fetch(SP, COUNTER, [-0.10, 7.60]), [SP], start=START)
    spoon = {SP: floor("breakfast_spoon", -0.85, 7.70, 30.0)}
    back = fetch(SP, COUNTER, [-0.10, 7.60])
    fams = {
        "by_kind": fam(
            "spoon_on_floor", ["storage_place", "multi_object_goal"], "the seed's layout only",
            "a spoon and a toy block on the kitchen floor; the kid's toy box stands in the living room",
            "each thing goes back where its kind belongs: the spoon to the counter, the block to the toy box",
            {"": dict(add={**spoon, "dropped_block": floor("wooden_block", -1.00, 8.50),
                           "toy_box": floor("toy_box", 5.70, 0.80)},
                      watch=[SP, "dropped_block", "toy_box"],
                      goal={"all": sgoal + [["inside", "dropped_block", "toy_box"], H]},
                      route=[look(COUNTER)] + back + into("dropped_block", "toy_box"))}),
        "belongs_on_floor": fam(
            "spoon_on_floor", ["goal_items_unstated"], "the seed's layout only",
            "next to the spoon on the floor stand a waste bin and a laundry basket, which live on the floor",
            "only what fell is picked up: the bin and the basket belong on the floor and stay",
            {"": dict(add={**spoon, "kitchen_bin": floor("trash_can", -1.10, 7.25),
                           "laundry_basket": floor("storage_basket", -1.15, 8.40)},
                      watch=[SP, "kitchen_bin", "laundry_basket"],
                      goal={"all": sgoal + [["near_start", "kitchen_bin", 0.03], ["near_start", "laundry_basket", 0.03],
                                            H]},
                      route=[look(COUNTER)] + back)}),
        "dropped_out_of_view": fam(
            "spoon_on_floor", ["not_in_view"], "the seed's layout only",
            "the spoon fell and slid into the dining room next door, out of view from the kitchen",
            "look around until the dropped thing is found, then put it back on the counter",
            {"": dict(add={SP: floor("breakfast_spoon", 0.75, 7.50, 30.0)},
                      route=[look(COUNTER), S("search", object=SP, region="dining_room_0_1")] + back)}),
        "only_this_room": fam(
            "spoon_on_floor", ["referent_clue"], "the seed's layout only",
            "a spoon on the kitchen floor, and the kid's toy car on the living-room floor",
            "the instruction names the kitchen: pick up the spoon, leave the car in the living room",
            {"": dict(add={**spoon, "living_car": floor("toy_car", 4.36, 1.68)},
                      watch=[SP, "living_car"], goal={"all": sgoal + [["near_start", "living_car", 0.03], H]},
                      route=[look(COUNTER)] + back)},
            instruction="Something fell on the kitchen floor. Please pick it up and put it where it belongs.",
            instruction_zh="厨房地上掉了东西，帮忙捡起来放好。"),
        "dropped_in_two_rooms": fam(
            "spoon_on_floor", ["goal_items_unstated", "not_in_view"], "the seed's layout only",
            "a spoon on the kitchen floor, and a pencil under the study desk (the kid's notebook is on the desk)",
            "more than one thing fell, in different rooms: look through the house, put each back (the spoon on "
            "the counter, the pencil on the desk with the notebook)",
            {"": dict(add={**spoon, "dropped_pencil": floor("pencil", -0.70, -5.40, 20.0),
                           "homework": on("notebook", DESK, -0.70, -5.95)},
                      watch=[SP, "dropped_pencil"],
                      goal={"all": sgoal + [["on", "dropped_pencil", DESK], H]},
                      route=[look(COUNTER)] + back + [S("search", object="dropped_pencil", region="living_room_0_1")]
                      + fetch("dropped_pencil", DESK, [-1.05, -5.95]))},
            instruction="Some things fell on the floor around the house. Please pick them up and put them where "
                        "they belong.",
            instruction_zh="家里地上掉了些东西，帮忙捡起来放好。"),
    }
    return t, fams


# ================================================================== T24 something to eat for the kid
def t24():
    AP = "snack_apple"
    hw = {"homework": on("notebook", DESK, -0.70, -5.95)}
    ctl = {"note": "an apple on the dining table, the kid's homework on the study desk",
           "add": {AP: on("apple", T2, 3.30, 6.70), **hw}}
    t = base_task("T24_snack_for_kid", "ZB-T24", "The kid is doing homework in the study and is hungry. Bring him "
                  "something to eat.", "孩子在书房写作业饿了，给他拿点吃的。", "apple_on_table", ctl,
                  {"all": [["on", AP, DESK], H]}, fetch(AP, DESK, [-1.10, -5.95]), [AP],
                  remove=["clutter_cereal_a", "clutter_cereal_b"])
    BA, SN = "snack_banana", "snack_box"
    hw3 = {"homework_3": on("notebook", DESK3, 6.60, -5.50)}
    fams = {
        "no_apples_for_him": fam(
            "apple_on_table", ["preference_allocation"], "the seed's layout only",
            "an apple and a banana on the table; the kid does not like apples",
            "choose by what the kid likes: the banana",
            {"": dict(add={AP: on("apple", T2, 3.30, 6.70), BA: on("banana", T2, 3.30, 7.10), **hw},
                      watch=[AP, BA], goal={"all": [["on", BA, DESK], ["not on", AP, DESK], H]},
                      route=[look(T2)] + fetch(BA, DESK, [-1.10, -5.95]))},
            instruction="The kid is doing homework in the study and is hungry. Bring him something to eat; he "
                        "doesn't like apples.",
            instruction_zh="孩子在书房写作业饿了，给他拿点吃的。他不爱吃苹果。"),
        "dinner_soon": fam(
            "apple_on_table", ["preference_allocation"], "the seed's layout only",
            "an apple and a box of snacks on the table; dinner is in half an hour",
            "with dinner close, the fruit, not the snacks",
            {"": dict(add={AP: on("apple", T2, 3.30, 6.70), SN: on("snack_carton", T2, 3.30, 7.10), **hw},
                      watch=[AP, SN], goal={"all": [["on", AP, DESK], ["near_start", SN, 0.03], H]},
                      route=[look(T2)] + fetch(AP, DESK, [-1.10, -5.95]))},
            instruction="The kid is doing homework in the study and is hungry. Bring him something to eat; "
                        "dinner is in half an hour.",
            instruction_zh="孩子在书房写作业饿了，给他拿点吃的。还有半小时就吃晚饭了。"),
        "fruit_out_of_view": fam(
            "apple_on_table", ["not_in_view"], "the seed's layout only",
            "no food on the dining table; the fruit basket with an apple is on the bedroom bookcase",
            "find where food is kept (the fruit basket), take something from it",
            {"": dict(add={"home_basket": on("fruit_basket", "bookcase_2/top", 0.92, -0.43),
                           AP: {"asset": "apple", "support": None, "z": 0.73, "xy": [0.92, -0.43], "yaw_deg": 0.0},
                           **hw},
                      watch=[AP, "home_basket"],
                      route=[look(T2), S("search", object="home_basket", region="bedroom_0_1")]
                      + fetch(AP, DESK, [-1.10, -5.95]))}),
        "where_is_he": fam(
            "apple_on_table", ["referent_clue"], "where the homework lies (seed: the study desk or the bedroom desk)",
            "the kid's open homework lies on one of two desks; the instruction does not say which room",
            "the kid is where his homework is: bring the food to that desk",
            {"study": dict(add={AP: on("apple", T2, 3.30, 6.70), **hw}, goal={"all": [["on", AP, DESK], H]},
                           route=[nav(AP), pick(AP), look(DESK3), nav(DESK), place(AP, DESK, [-1.10, -5.95])]),
             "bedroom": dict(add={AP: on("apple", T2, 3.30, 6.70), **hw3}, goal={"all": [["on", AP, DESK3], H]},
                             route=[nav(AP), pick(AP), look(DESK), nav(DESK3), place(AP, DESK3, [6.20, -5.50])])},
            instruction="The kid is doing homework and is hungry. Bring him something to eat.",
            instruction_zh="孩子写作业饿了，给他拿点吃的。"),
        "two_kids": fam(
            "apple_on_table", ["count_from_scene", "multi_object_goal"], "the seed's layout only",
            "two kids' homework, on the study desk and on the bedroom desk; an apple and a banana on the table",
            "one snack for each kid: as many as there are kids doing homework, one to each desk",
            {"": dict(add={AP: on("apple", T2, 3.30, 6.70), BA: on("banana", T2, 3.30, 7.10), **hw, **hw3},
                      watch=[AP, BA],
                      goal={"all": [H], "any": [[["on", AP, DESK], ["on", BA, DESK3]],
                                                [["on", BA, DESK], ["on", AP, DESK3]]]},
                      route=fetch(AP, DESK, [-1.10, -5.95]) + fetch(BA, DESK3, [6.20, -5.50]))},
            instruction="The kids are doing homework and are hungry. Bring them something to eat.",
            instruction_zh="孩子们在写作业，饿了，给他们拿点吃的。"),
    }
    return t, fams


# ================================================================== T25 a drink for the guest
def t25():
    J, CUP = "guest_juice", "guest_cup"
    ctl = {"note": "a bottle of juice and a cup on the kitchen island; the guest sits in the living room",
           "add": {J: on("juice_bottle", ISL, 7.30, 1.80), CUP: on("breakfast_cup", ISL, 7.55, 1.80)}}
    def serve(j=J, cups=(CUP,), n=1, house=True):
        """the drink, and n cups (one of those on the island or any of the house's own cups)"""
        return [["on", j, TV], ["upright", j],
                ["count_on_at_least", list(cups) + (HOUSE_CUPS if house else []), TV, n]]
    t = base_task("T25_drink_for_guest", "ZB-T25", "A guest is sitting in the living room. Bring him something "
                  "to drink.", "客人在客厅坐着，给他拿点喝的。", "drink_on_island", ctl,
                  {"all": serve() + [H]}, fetch(J, TV, [7.30, 0.36]) + fetch(CUP, TV, [7.55, 0.36]), [J, CUP])
    in_fridge = lambda n: {"asset": "juice_bottle", **P(FS, 5.90, 3.30)}  # noqa: E731
    fams = {
        "cup_elsewhere": fam(
            "drink_on_island", ["not_in_view"], "the seed's layout only",
            "the juice on the island, no cup there; cups stand on the kitchen counter in the small kitchen",
            "a drink is served with a cup: find one",
            {"": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80)}, watch=[J, "cup_counter_b"],
                      goal={"all": serve(J, ()) + [H]},
                      route=fetch(J, TV, [7.30, 0.36]) + [S("search", object="cup_counter_b", region="kitchen_0_1")]
                      + fetch("cup_counter_b", TV, [7.55, 0.36]))}),
        "cold_one": fam(
            "drink_on_island", ["preference_allocation"], "the seed's layout only",
            "a bottle on the island at room temperature, another one in the fridge; it is a hot day",
            "on a hot day the cold one: open the fridge for it, close it again",
            {"": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80), CUP: on("breakfast_cup", ISL, 7.55, 1.80),
                           "cold_juice": in_fridge("cold_juice")},
                      watch=[J, "cold_juice", CUP],
                      goal={"all": serve("cold_juice") + [["near_start", J, 0.03], ["is_closed", FR], H]},
                      route=[nav(FR), S("open", articulated=FR), nav("cold_juice"), pick("cold_juice"),
                             S("retreat", obstacle=FR, distance_m=0.3), S("close", articulated=FR), nav(TV),
                             place("cold_juice", TV, [7.30, 0.36])] + fetch(CUP, TV, [7.55, 0.36]))},
            instruction="It's a hot day. A guest is sitting in the living room; bring him something to drink.",
            instruction_zh="天很热，客人在客厅坐着，给他拿点喝的。"),
        "drink_in_fridge": fam(
            "drink_on_island", ["storage_place", "not_in_view"], "the seed's layout only",
            "a cup on the island, nothing to drink out; the juice is in the fridge",
            "drinks are kept in the fridge: open it, take the juice, close it",
            {"": dict(add={CUP: on("breakfast_cup", ISL, 7.55, 1.80), "cold_juice": in_fridge("cold_juice")},
                      watch=["cold_juice", CUP], goal={"all": serve("cold_juice") + [["is_closed", FR], H]},
                      route=[look(ISL), nav(FR), S("open", articulated=FR), nav("cold_juice"), pick("cold_juice"),
                             S("retreat", obstacle=FR, distance_m=0.3), S("close", articulated=FR), nav(TV),
                             place("cold_juice", TV, [7.30, 0.36])] + fetch(CUP, TV, [7.55, 0.36]))}),
        "two_guests": fam(
            "drink_on_island", ["count_from_scene", "multi_object_goal"], "the seed's layout only",
            "two guests; one bottle of juice and two cups on the island",
            "one cup per guest: both cups with the bottle",
            {"": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80), CUP: on("breakfast_cup", ISL, 7.55, 1.80),
                           "guest_cup_2": on("breakfast_cup", ISL, 7.80, 1.80)},
                      watch=[J, CUP, "guest_cup_2"], goal={"all": serve(J, (CUP, "guest_cup_2"), 2) + [H]},
                      route=fetch(J, TV, [7.30, 0.36]) + fetch(CUP, TV, [7.55, 0.36])
                      + fetch("guest_cup_2", TV, [7.80, 0.36]))},
            instruction="Two guests are sitting in the living room. Bring them something to drink.",
            instruction_zh="两位客人在客厅坐着，给他们拿点喝的。"),
        "little_guest": fam(
            "drink_on_island", ["preference_allocation"], "the seed's layout only",
            "the guest is a small child; a china cup and a plastic cup on the island",
            "for a small child the plastic cup, not the china one",
            {"": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80), CUP: on("breakfast_cup", ISL, 7.55, 1.80),
                           "kid_cup": on("plastic_cup", ISL, 7.80, 1.80)},
                      watch=[J, CUP, "kid_cup"],
                      goal={"all": serve(J, ("kid_cup",), house=False) + [["near_start", CUP, 0.03], H]},
                      route=fetch(J, TV, [7.30, 0.36]) + fetch("kid_cup", TV, [7.55, 0.36]))},
            instruction="A little girl is visiting and sitting in the living room. Bring her something to drink.",
            instruction_zh="来了个小朋友，在客厅坐着，给她拿点喝的。"),
    }
    return t, fams


# ================================================================== T26 the kid's things back to his room
def t26():
    CAR, BASK = "living_car", "kids_basket"
    room = {BASK: floor("storage_basket", 0.89, -1.93), "kids_shelf_book": on("book_blue", "bookcase_2/top", 0.90, -0.43)}
    ctl = {"note": "the kid's toy car on the living-room floor; his toy basket is in his bedroom",
           "add": {CAR: floor("toy_car", 4.36, 1.68), **room}}
    t = base_task("T26_kids_things_to_room", "ZB-T26", "Take the things the kid left in the living room back to "
                  "his room.", "把孩子落在客厅的东西拿回他房间。", "car_in_living_room", ctl,
                  {"all": [["inside", CAR, BASK], H]}, [S("explore_room", room="living_room_0_0")] + into(CAR, BASK),
                  [CAR, BASK])
    kb, nv = "kid_book", "adult_novel"
    fams = {
        "whose": fam(
            "car_in_living_room", ["referent_clue"], "the seed's layout only",
            "a picture book like the ones on the kid's bookcase and a grown-up's novel on the TV stand",
            "only the kid's things go: the picture book to his bookcase, the novel stays",
            {"": dict(add={kb: on("book_blue", TV, 7.20, 0.36), nv: on("paperback_book", TV, 7.80, 0.36), **room},
                      watch=[kb, nv], goal={"all": [["on", kb, "bookcase_2/top"], ["near_start", nv, 0.03], H]},
                      route=[look(TV)] + fetch(kb, "bookcase_2/top", [1.12, -0.43]))}),
        "scattered": fam(
            "car_in_living_room", ["goal_items_unstated", "multi_object_goal"], "the seed's layout only",
            "the car on the floor, the duck on the TV stand, a block on the island",
            "everything of his in the living room, not only the first thing seen",
            {"": dict(add={CAR: floor("toy_car", 4.36, 1.68), "living_duck": on("rubber_duck", TV, 7.00, 0.36),
                           "living_block": on("wooden_block", ISL, 7.20, 1.80), **room},
                      watch=[CAR, "living_duck", "living_block", BASK],
                      goal={"all": [["inside", x, BASK] for x in (CAR, "living_duck", "living_block")] + [H]},
                      route=[S("explore_room", room="living_room_0_0")] + into(CAR, BASK) + into("living_duck", BASK)
                      + into("living_block", BASK))}),
        "where_in_room": fam(
            "car_in_living_room", ["storage_place", "multi_object_goal"], "the seed's layout only",
            "the car and one of his picture books in the living room",
            "in his room each by kind: the car into the toy basket, the book onto his bookcase",
            {"": dict(add={CAR: floor("toy_car", 4.36, 1.68), kb: on("book_blue", TV, 7.20, 0.36), **room},
                      watch=[CAR, kb, BASK],
                      goal={"all": [["inside", CAR, BASK], ["on", kb, "bookcase_2/top"], H]},
                      route=[S("explore_room", room="living_room_0_0")] + into(CAR, BASK)
                      + fetch(kb, "bookcase_2/top", [1.12, -0.43]))}),
        "bear_to_bed": fam(
            "car_in_living_room", ["storage_place"], "the seed's layout only",
            "his teddy bear on the TV stand; it is bedtime",
            "at bedtime the bear goes to his bed, not into the toy basket",
            {"": dict(add={"living_bear": on("teddy_bear", TV, 7.40, 0.36), **room}, watch=["living_bear", BASK],
                      goal={"all": [["on", "living_bear", "mattress_1/top"], H]},
                      route=[look(TV)] + fetch("living_bear", "mattress_1/top", [0.00, -4.00]))},
            instruction="The kid is going to bed. Take the things he left in the living room back to his room.",
            instruction_zh="孩子要睡觉了，把他落在客厅的东西拿回他房间。"),
        "two_bedrooms": fam(
            "car_in_living_room", ["referent_clue", "not_in_view"], "which bedroom is his (seed: where his toy basket is)",
            "two bedrooms; his is the one with the toy basket",
            "tell his room by his things in it and take the car there",
            {c: dict(add={CAR: floor("toy_car", 4.36, 1.68), BASK: floor("storage_basket", *xy)},
                     watch=[CAR, BASK], route=[nav(CAR), pick(CAR), S("search", object=BASK, region=r), nav(BASK),
                                                place(CAR, BASK)])
             for c, xy, r in (("room_east", (0.89, -1.93), "bedroom_0_1"), ("room_south", (4.30, -9.80), "bedroom_0_0"))}),
    }
    return t, fams


# ================================================================== T27 leftovers into the fridge
def t27():
    R = "leftover_rice"
    ctl = {"note": "a glass box of leftover rice on the dining table", "add": {R: on("glass_food_container", T2, 3.30, 6.70)}}
    rg = [["on", R, FS], ["is_closed", FR]]
    t = base_task("T27_leftovers_to_fridge", "ZB-T27", "Dinner is over. Put the leftovers in the fridge.",
                  "晚饭吃完了，把剩菜收进冰箱。", "rice_on_table", ctl, {"all": rg + [H]}, fridge([R]), [R],
                  remove=["clutter_cereal_a", "clutter_cereal_b", "handled_cooking_pot", "pot_lid"])
    rice = {R: on("glass_food_container", T2, 3.30, 6.70)}
    fams = {
        "which_is_leftover": fam(
            "rice_on_table", ["disposal_by_state"], "the seed's layout only",
            "the box of rice and an empty takeout tray on the table",
            "only food goes into the fridge: the empty tray does not",
            {"": dict(add={**rice, "empty_tray": on("foil_takeout_tray", T2, 3.25, 7.30)}, watch=[R, "empty_tray"],
                      goal={"all": rg + [["not on", "empty_tray", FS], H]}, route=[look(T2)] + fridge([R]))}),
        "two_leftovers": fam(
            "rice_on_table", ["goal_items_unstated", "multi_object_goal"],
            "where the leftover soup is (seed: on the table, or still in its pot on the stove)",
            "the box of rice on the table, and a pot of leftover soup, on the table or still on the stove",
            "all the leftovers, not only the first one seen: both into the fridge",
            {c: dict(add={**rice, "leftover_soup": on("soup_pot", sup, *xy)}, watch=[R, "leftover_soup"],
                     goal={"all": rg + [["on", "leftover_soup", FS], ["upright", "leftover_soup"], H]},
                     route=[look(T2)] + ([look("kitchen_stove/top")] if "stove" in sup else []) + fridge([R, "leftover_soup"]))
             for c, sup, xy in (("soup_on_table", T2, (3.35, 6.05)), ("soup_on_stove", "kitchen_stove/top", (8.41, 1.725)))}),
        "still_eating": fam(
            "rice_on_table", ["referent_clue"], "the seed's layout only",
            "the box of rice, and a bowl of oatmeal with a spoon in front of a seat: someone is still eating",
            "a portion someone is still eating is not a leftover: only the rice",
            {"": dict(add={**rice, "eating_bowl": on("oatmeal_bowl", T2, 3.05, 7.30),
                           "eating_spoon": on("breakfast_spoon", T2, 3.05, 7.49)},
                      watch=[R, "eating_bowl"], goal={"all": rg + [["near_start", "eating_bowl", 0.03], ["never_picked", ["eating_bowl"]], H]},
                      route=[look(T2)] + fridge([R]))}),
        "fridge_out_of_view": fam(
            "rice_on_table", ["not_in_view"], "the seed's layout only",
            "the robot starts in the dining room; the fridge stands in the open kitchen, out of view",
            "find the fridge first, then put the rice in",
            {"": dict(add=rice, start=[3.80, 4.90, 180.0],
                      route=[look(T2), S("explore_room", room="living_room_0_0")] + fridge([R]))}),
        "fruit_stays_out": fam(
            "rice_on_table", ["category_rule"], "the seed's layout only",
            "the box of rice, the fruit basket with an apple and a box of cereal on the table",
            "only leftovers go into the fridge: the fruit and the cereal stay where they are",
            {"": dict(add={**rice, "table_basket": on("fruit_basket", T2, 3.35, 7.30),
                           "table_cereal": on("cereal_box", T2, 3.35, 6.00)},
                      watch=[R, "table_basket", "table_cereal"],
                      goal={"all": rg + [["near_start", "table_basket", 0.03], ["near_start", "table_cereal", 0.03], H]},
                      route=[look(T2)] + fridge([R]))}),
    }
    return t, fams


# ================================================================== T28 the kid's cup to his bedside
def t28():
    KC = "kid_cup"
    BEAR = {"bed_bear": on("teddy_bear", "mattress_1/top", -0.20, -4.20)}
    side = "bookcase_3/top"
    SIDES = [side, "desk_1/top"]                     # beside bed 1: the low bookcase (0.7 m) or the desk (0.4 m)
    ctl = {"note": "the kid's plastic cup on the kitchen counter; his bed has the teddy bear on it",
           "add": {KC: on("plastic_cup", COUNTER, -0.20, 7.60), **BEAR}}
    t = base_task("T28_cup_to_bedside", "ZB-T28", "The kid is going to bed. Bring his cup to his bedside.",
                  "孩子要睡了，把他的水杯拿到床边。", "cup_on_counter", ctl,
                  {"all": [["on_any", KC, SIDES], ["upright", KC], H]}, fetch(KC, side, [2.10, -4.88]), [KC])
    to_side = fetch(KC, side, [2.10, -4.88])
    fams = {
        "which_cup": fam(
            "cup_on_counter", ["referent_clue"], "the seed's layout only",
            "on the counter: the kid's plastic cup, a china cup and a mug",
            "his cup is the plastic one: bring that one",
            {"": dict(add={KC: on("plastic_cup", COUNTER, -0.20, 7.60), "counter_mug": on("breakfast_mug", COUNTER, -0.30, 9.00),
                           **BEAR},
                      watch=[KC, "cup_counter_b", "counter_mug"],
                      goal={"all": [["on_any", KC, SIDES], ["upright", KC], ["near_start", "cup_counter_b", 0.03],
                                    ["near_start", "counter_mug", 0.03], H]},
                      route=[look(COUNTER)] + to_side)}),
        "cup_put_away": fam(
            "cup_on_counter", ["item_put_away"], "the seed's layout only",
            "the cup was put away in the low wall cabinet",
            "look in the cabinet, take the cup, close the door",
            {"": dict(add={KC: on("plastic_cup", f"{C4}/inside_shelf", 1.40, 0.42), **BEAR},
                      goal={"all": [["on_any", KC, SIDES], ["upright", KC], ["is_closed", C4], H]},
                      route=explore(C4) + from_closed(KC, C4) + [nav(side), place(KC, side, [2.10, -4.88])])}),
        "which_bed": fam(
            "cup_on_counter", ["referent_clue"], "which bed is his (seed: the teddy bear on one of the two beds)",
            "two bedrooms with a bed each; his teddy bear lies on his",
            "his bed is the one with his bear: the cup goes next to that bed",
            {"east": dict(add={KC: on("plastic_cup", COUNTER, -0.20, 7.60), **BEAR},
                          route=[nav(KC), pick(KC), look("mattress_2/top"), nav(side), place(KC, side, [2.10, -4.88])]),
             "south": dict(add={KC: on("plastic_cup", COUNTER, -0.20, 7.60),
                                "bed_bear": on("teddy_bear", "mattress_2/top", 3.30, -9.80)},
                           goal={"all": [["on", KC, "cell_shelf_2/top"], ["upright", KC], H]},
                           route=[nav(KC), pick(KC), look("mattress_1/top"), nav("cell_shelf_2/top"),
                                  place(KC, "cell_shelf_2/top", [1.42, -10.80])])}),
        "his_cup_put_away": fam(
            "cup_on_counter", ["referent_clue", "item_put_away", "dependent_decisions"], "the seed's layout only",
            "on the counter a china cup and a mug, neither of them his; his plastic cup was put away in the low cabinet",
            "each decision rests on what the last one found: the cups in sight are not his (not any cup will do), so "
            "his was put away: look in the cabinet, take it, close the door",
            {"": dict(add={KC: on("plastic_cup", f"{C4}/inside_shelf", 1.40, 0.42),
                           "counter_mug": on("breakfast_mug", COUNTER, -0.30, 9.00), **BEAR},
                      watch=[KC, "cup_counter_b", "counter_mug"],
                      goal={"all": [["on_any", KC, SIDES], ["upright", KC], ["near_start", "cup_counter_b", 0.03],
                                    ["near_start", "counter_mug", 0.03], ["is_closed", C4], H]},
                      route=[look(COUNTER)] + explore(C4) + from_closed(KC, C4) + [nav(side), place(KC, side, [2.10, -4.88])])}),
        "cup_out_of_view": fam(
            "cup_on_counter", ["not_in_view"], "the seed's layout only",
            "the cup was left on the dining table, out of view",
            "find the cup first",
            {"": dict(add={KC: on("plastic_cup", T2, 3.30, 6.70), **BEAR},
                      route=[look(COUNTER), S("search", object=KC, region="dining_room_0_1")] + to_side)}),
        "already_there": fam(
            "cup_on_counter", ["goal_already_met"], "the seed's layout only",
            "the cup already stands by his bed",
            "the goal already holds: check and leave it",
            {"": dict(add={KC: on("plastic_cup", side, 2.10, -4.88), **BEAR},
                      goal={"all": [["on_any", KC, SIDES], ["near_start", KC, 0.03], H]},
                      route=[nav(side), look(side)])}),
    }
    return t, fams


# ================================================================== T29 clear the dining table for the meal
def t29():
    TC, BOX = "table_car", "toy_box"
    tb = {BOX: floor("toy_box", 5.70, 0.80)}
    ctl = {"note": "the kid's toy car on the dining table; his toy box in the living room",
           "add": {TC: on("toy_car", T2, 3.30, 6.70), **tb}}
    t = base_task("T29_clear_table_for_dinner", "ZB-T29", "Dinner is about to start. Take away what doesn't belong "
                  "on the dining table.", "要吃饭了，把餐桌上不该放的东西拿走。", "car_on_table", ctl,
                  {"all": [["inside", TC, BOX], H]}, [look(T2)] + into(TC, BOX), [TC, BOX],
                  remove=["clutter_cereal_a", "clutter_cereal_b"])
    setting = {"set_bowl": on("breakfast_bowl", T2, 3.30, 7.30), "set_spoon": on("breakfast_spoon", T2, 3.30, 7.49)}
    keep = [["near_start", "set_bowl", 0.03], ["near_start", "set_spoon", 0.03]]
    shelves = ["bookcase_2/top", "bookcase_3/top", "large_shelf_2/shelf_1", "large_shelf_2/shelf_2"]
    fams = {
        "belongs_on_table": fam(
            "car_on_table", ["category_rule"], "the seed's layout only",
            "the toy car, and a bowl and a spoon set for the meal",
            "what is set for the meal stays; only the toy goes",
            {"": dict(add={TC: on("toy_car", T2, 3.30, 6.70), **tb, **setting}, watch=[TC, "set_bowl", "set_spoon"],
                      goal={"all": [["inside", TC, BOX]] + keep + [H]}, route=[look(T2)] + into(TC, BOX))}),
        "homework_on_table": fam(
            "car_on_table", ["storage_place", "multi_object_goal"], "the seed's layout only",
            "the kid's notebook and pencil on the dining table",
            "homework goes back to the study desk, not just off the table",
            {"": dict(add={"hw_notebook": on("notebook", T2, 3.30, 6.30), "hw_pencil": on("pencil", T2, 3.55, 6.30, 90.0)},
                      watch=["hw_notebook", "hw_pencil"],
                      goal={"all": [["on", "hw_notebook", DESK], ["on", "hw_pencil", DESK], H]},
                      route=[look(T2)] + fetch("hw_notebook", DESK, [-0.70, -5.95])
                      + fetch("hw_pencil", DESK, [-0.35, -5.95]))}),
        "several": fam(
            "car_on_table", ["category_rule", "multi_object_goal"], "the seed's layout only",
            "the toy car, a paperback and an empty soda can on the table",
            "each to its place: the toy to the toy box, the book to a bookshelf, the empty can into the bin",
            {"": dict(add={TC: on("toy_car", T2, 3.30, 6.70), "table_book": on("paperback_book", T2, 3.30, 7.20),
                           "empty_can": on("soda_can", T2, 3.30, 6.20), **tb},
                      watch=[TC, "table_book", "empty_can"],
                      goal={"all": [["inside", TC, BOX], ["inside", "empty_can", "trash_can"], H],
                            "any": [[["on", "table_book", s]] for s in shelves]},
                      route=[look(T2)] + into(TC, BOX) + [nav("empty_can"), pick("empty_can"), nav("trash_can"),
                                                          S("drop", object="empty_can", container="trash_can")]
                      + fetch("table_book", "bookcase_2/top", [1.00, -0.43]))}),
        "nothing_to_clear": fam(
            "car_on_table", ["goal_already_met"], "the seed's layout only",
            "the table holds only what is set for the meal",
            "nothing on it is out of place: leave the table as it is",
            {"": dict(add=dict(setting), watch=["set_bowl", "set_spoon"], goal={"all": keep + [H]},
                      route=[nav(T2), look(T2)])}),
        "which_table": fam(
            "car_on_table", ["destination_unnamed"], "where the meal is served (seed: east or west dining room)",
            "a toy on each dining table; the pot of soup stands on one of them",
            "clear the table the meal is served on; the other table is left as it is",
            {c: dict(add={"toy_east": on("toy_car", T2, 3.30, 6.70), "toy_west": on("toy_car", T1, -7.95, 7.40),
                          "dinner_pot": on("soup_pot", sup, *xy), **tb},
                     remove=["bowl_side_table", "cup_side_table", "spoon_side_table"],
                     watch=["toy_east", "toy_west", "dinner_pot"],
                     goal={"all": [["inside", here, BOX], ["near_start", there, 0.03], H]},
                     route=[look(T2), look(T1)] + into(here, BOX))
             for c, sup, xy, here, there in (("east", T2, (3.35, 7.30), "toy_east", "toy_west"),
                                             ("west", T1, (-7.95, 8.20), "toy_west", "toy_east"))}),
    }
    return t, fams


# ================================================================== T30 bowls for the soup
def t30():
    B1 = "soup_bowl_1"
    top6 = f"{C6}/top"
    # the soup in its pot on the stove (the scene's empty cooking pot and its lid leave): what the bowls are for
    SOUP = {"stove_soup": on("soup_pot", "kitchen_stove/top", 8.41, 1.725)}
    def bowls(*mine, n=1):
        return ["count_on_at_least", list(mine) + HOUSE_BOWLS, ISL, n]
    ctl = {"note": "the soup cooking in the pot on the stove; a clean bowl on the low wall cabinet",
           "add": {**SOUP, B1: on("breakfast_bowl", top6, 3.40, 0.36)}}
    t = base_task("T30_bowls_for_soup", "ZB-T30", "The soup is almost ready. Bring a bowl over for serving it.",
                  "汤快好了，拿碗过来准备盛。", "bowl_on_cabinet", ctl, {"all": [bowls(B1), H]},
                  fetch(B1, ISL, [8.05, 1.75]), [B1],
                  remove=["spoon_kitchen_cabinet", "handled_cooking_pot", "pot_lid"])
    fams = {
        "how_many": fam(
            "bowl_on_cabinet", ["count_from_scene", "multi_object_goal"], "the seed's layout only",
            "three spoons laid out at the dining table; three clean bowls on the cabinet",
            "as many bowls as places at the table: three",
            {"": dict(add={**SOUP, **{f"soup_bowl_{i + 1}": on("breakfast_bowl", top6, x, 0.36)
                              for i, x in enumerate((3.29, 3.50, 3.71))},
                           **{f"seat_spoon_{i + 1}": on("breakfast_spoon", T2, 3.05, y) for i, y in enumerate((5.90, 6.70, 7.50))}},
                      remove=["clutter_cereal_a", "clutter_cereal_b"],
                      watch=["soup_bowl_1", "soup_bowl_2", "soup_bowl_3"],
                      goal={"all": [bowls("soup_bowl_1", "soup_bowl_2", "soup_bowl_3", n=3), H]},
                      route=[look(T2)] + fetch("soup_bowl_1", ISL, [7.65, 1.75]) + fetch("soup_bowl_2", ISL, [7.85, 1.75])
                      + fetch("soup_bowl_3", ISL, [8.05, 1.75]))},
            instruction="The soup is almost ready. Bring bowls over for serving it.",
            instruction_zh="汤快好了，拿碗过来准备盛。"),
        "not_enough_bowls": fam(
            "bowl_on_cabinet", ["count_from_scene", "item_put_away", "not_in_view", "dependent_decisions"],
            "the seed's layout only",
            "three spoons laid out at the dining table; one clean bowl on the cabinet, one inside it, the others in "
            "the small kitchen",
            "each decision rests on what the last one found: three places, so three bowls; one is out, so look where "
            "bowls are kept (the cabinet: one more, close the door); still one short, so the other kitchen",
            {"": dict(add={**SOUP, B1: on("breakfast_bowl", top6, 3.40, 0.36),
                           **{f"seat_spoon_{i + 1}": on("breakfast_spoon", T2, 3.05, y) for i, y in enumerate((5.90, 6.70, 7.50))}},
                      remove=["clutter_cereal_a", "clutter_cereal_b"],
                      watch=[B1, "bowl_inside_kitchen_cabinet", "bowl_kitchen_cabinet"],
                      goal={"all": [bowls(B1, n=3), ["is_closed", C6], H]},
                      route=[look(T2)] + fetch(B1, ISL, [7.65, 1.75]) + explore(C6)
                      + from_closed("bowl_inside_kitchen_cabinet", C6)
                      + [nav(ISL), place("bowl_inside_kitchen_cabinet", ISL, [7.85, 1.75]),
                         S("search", object="bowl_kitchen_cabinet", region="kitchen_0_1")]
                      + fetch("bowl_kitchen_cabinet", ISL, [8.05, 1.75]))},
            instruction="The soup is almost ready. Bring bowls over for serving it.",
            instruction_zh="汤快好了，拿碗过来准备盛。"),
        "clean_one": fam(
            "bowl_on_cabinet", ["referent_clue"], "the seed's layout only",
            "two bowls on the cabinet: one still has oatmeal in it, the other is empty",
            "for serving, the empty bowl",
            {"": dict(add={**SOUP, "full_bowl": on("oatmeal_bowl", top6, 3.35, 0.36), B1: on("breakfast_bowl", top6, 3.62, 0.36)},
                      watch=[B1, "full_bowl"],
                      goal={"all": [bowls(B1), ["near_start", "full_bowl", 0.03], H]},
                      route=[look(top6)] + fetch(B1, ISL, [8.05, 1.75]))}),
        "bowl_put_away": fam(
            "bowl_on_cabinet", ["item_put_away"], "the seed's layout only",
            "no bowl out; the clean bowls are in the low cabinet",
            "look in the cabinet, take a bowl, close the door",
            {"": dict(add={**SOUP, B1: on("breakfast_bowl", f"{C4}/inside_shelf", 1.40, 0.42)},
                      goal={"all": [bowls(B1), ["is_closed", C4], H]},
                      route=explore(C4) + from_closed(B1, C4) + [nav(ISL), place(B1, ISL, [8.05, 1.75])])}),
        "no_bowl": fam(
            "bowl_on_cabinet", ["resource_absent"], "the seed's layout only",
            "no clean bowl anywhere; a mug and a plate on the cabinet",
            "soup needs something that holds liquid: the mug, not the plate",
            {"": dict(add={**SOUP, "spare_mug": on("breakfast_mug", top6, 3.35, 0.36),
                           "spare_plate": on("breakfast_plate", top6, 3.62, 0.36)},
                      remove=["bowl_dining_cabinet", "bowl_kitchen_cabinet", "bowl_side_table", "bowl_inside_kitchen_cabinet"],
                      watch=["spare_mug", "spare_plate"],
                      goal={"all": [["count_on_at_least", ["spare_mug"] + HOUSE_CUPS, ISL, 1], H]},
                      route=[look(top6)] + fetch("spare_mug", ISL, [8.05, 1.75]))}),
        "bowl_not_plate": fam(
            "bowl_on_cabinet", ["referent_clue"], "the seed's layout only",
            "a plate and a bowl on the cabinet",
            "soup is served in a bowl: the bowl, not the plate",
            {"": dict(add={**SOUP, "spare_plate": on("breakfast_plate", top6, 3.35, 0.36), B1: on("breakfast_bowl", top6, 3.64, 0.36)},
                      watch=[B1, "spare_plate"],
                      goal={"all": [bowls(B1), ["near_start", "spare_plate", 0.03], H]},
                      route=[look(top6)] + fetch(B1, ISL, [8.05, 1.75]))}),
    }
    return t, fams


MAKERS = [t21, t22, t23, t24, t25, t26, t27, t28, t29, t30]
NEW_CONDITIONS = {
    "resource_absent": {"type": "resource_identity", "decision": "alternative",
                        "meaning": "the usual thing is not in the house; the closest thing that serves the purpose "
                                   "is used (a sponge for tissues, a mug for a soup bowl)"},
    "dependent_decisions": {"type": "task_structure", "decision": "sequence",
                            "meaning": "two or three decisions in a row, each on what the step before found (the "
                                       "usual thing is absent -> a substitute -> the substitute is put away)"},
}


def new_base_tasks():
    """[(base task, families)] for T21-T30."""
    return [mk() for mk in MAKERS]


def families_for(tid):
    for mk in MAKERS:
        t, fams = mk()
        if t["task_id"] == tid:
            return copy.deepcopy(fams)
    return {}
