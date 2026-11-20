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


def fridge(items, y0=3.18, xs=(5.78, 5.98), spots=None):
    """open the fridge, put each item in, close it (one hand: the door first); y0: the first row's depth
    (the shelf's front edge is y 3.04); xs: the two columns (the shelf spans x 5.63-6.17, y 3.04-3.56);
    spots: each item's [x, y] instead"""
    out = [nav(FR), S("open", articulated=FR)]
    for k, x in enumerate(items):
        xy = list(spots[k]) if spots else [xs[k % 2], y0 + 0.2 * (k // 2)]
        out += [nav(x), pick(x), nav(FR), place(x, FS, xy)]
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
# the task asks for "something to wipe it up"; where a sponge and tissues are both about, "something to wipe with":
# either one does
TISSUES_ASKED = dict(instruction="Some soup got spilled at the dining table. Bring something to wipe it with.",
                     instruction_zh="餐桌上洒了点汤，拿个能擦的用具过去。")


def t21():
    TIS = "tissue"
    meal = {"soup_bowl": on("oatmeal_bowl", T2, 3.10, 6.95), "meal_spoon": on("breakfast_spoon", T2, 3.10, 7.14)}
    ctl = {"note": "the tissue box on the TV stand, a bowl of soup on the dining table",
           "add": {TIS: on("tissue_box", TV, 7.60, 0.36), **meal}}
    t = base_task("T21_bring_tissues", "ZB-T21", "Some soup got spilled at the dining table. Bring something to wipe "
                  "it up.", "餐桌上洒了点汤，拿点擦的东西过去。", "tissue_on_tv_stand", ctl,
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
                      route=[look(TV)] + to_table("spare_sponge"))},
            **TISSUES_ASKED),
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
             for a, o, xy in ((C4, C6, (1.40, 0.50)), (C6, C4, (3.50, 0.36)))},   # C4: front of the shelf (0.30 m headroom)
            instruction="Some soup got spilled at the dining table. Bring something to wipe it up; the tissues are "
                        "put away in a cabinet, close its door again afterwards.",
            instruction_zh="餐桌上洒了点汤，拿点擦的东西过去。纸巾收在柜子里了，拿完把柜门关好。"),
        "the_kids_side": fam(
            "tissue_on_tv_stand", ["referent_clue"], "which end of the table the kid sits at (seed)",
            "two places at the table: the kid's (a plastic cup) and a grown-up's (a mug)",
            "the kid spilled: tell the kid's place by the plastic cup and put the tissues next to it",
            {c: dict(add={TIS: on("tissue_box", TV, 7.60, 0.36), **places}, goal=kid_goal,
                     watch=[TIS, *places],
                     route=fetch(TIS, T2, [3.10, places["kid_cup"]["xy"][1]]))
             for c, places in (("kid_north", kid_n), ("kid_south", kid_s))},
            instruction="The kid spilled some soup at the dining table. Bring something to wipe it up and put it on "
                        "the kid's side of the table.",
            instruction_zh="孩子吃饭把汤洒了，拿点擦的东西过去，放在孩子那一边。"),
    }
    return t, fams


# ================================================================== T22 put the shopping away
# eat_now desk_corner (11-17, user): the kid's homework spread over the study desk (x -1.41..-0.03, y -6.33..-5.71,
# the robot at its front, y < -6.33) in three rows, 5 cm apart (the 6 x 11 cm carton fits nowhere between them), a
# pencil in the first strip; the only free spot is the front corner at the east end (x -0.25..-0.03, y -6.33..-6.16)
_NB, _RED, _GRN = "notebook", "book_red", "book_green"
HOMEWORK_SPREAD = {
    # front row (back edges at y -6.161)
    "hw_notebook_1": on(_NB, DESK, -1.290, -6.245), "hw_book_red": on(_RED, DESK, -1.055, -6.244),
    "hw_notebook_2": on(_NB, DESK, -0.815, -6.245), "hw_notebook_3": on(_NB, DESK, -0.585, -6.245),
    "hw_paperback": on("paperback_book", DESK, -0.370, -6.221), "hw_pen": on("pen", DESK, -0.255, -6.245, 90.0),
    "hw_pencil": on("pencil", DESK, -0.400, -6.136),
    # middle row: six green books (y -6.112..-5.929)
    **{f"hw_book_green_{k + 1}": on(_GRN, DESK, x, -6.020)
       for k, x in enumerate((-1.295, -1.070, -0.845, -0.620, -0.395, -0.170))},
    # back row (front edges at y -5.879, flush with the back edge)
    "hw_book_red_2": on(_RED, DESK, -1.290, -5.794), "homework": on(_NB, DESK, -1.050, -5.795),
    **{f"hw_notebook_{k + 4}": on(_NB, DESK, x, -5.795) for k, x in enumerate((-0.825, -0.600, -0.375, -0.150))}}
DESK_CORNER = (-0.14, -6.22)


def t22():
    J, A, SN = "bought_juice", "bought_apple", "bought_snack"
    BASKET = "home_basket"
    JY = 3.12           # the juice 8 cm behind the fridge shelf's front edge (at 3.18 place_arrive found no path)
    JX = (5.90, 6.05)   # mid-shelf: at x 5.78 the tuck after the release brushed the fridge's left wall and tipped it
    ctl = {"note": "a bottle of juice from the shop on the dining table", "add": {J: on("juice_bottle", T2, 3.30, 6.70)}}
    # bought juice keeps in the fridge, a low cabinet or on a kitchen counter: any of them is put away
    JUICE_SPOTS = [FS, f"{C4}/inside_shelf", f"{C6}/inside_shelf", "kitchen_counter_1/top", "kitchen_counter_2/top"]
    jgoal = [["on_any", J, JUICE_SPOTS], ["upright", J], ["is_closed", FR], ["is_closed", C4], ["is_closed", C6]]
    t = base_task("T22_put_away_shopping", "ZB-T22", "I just got back from the shop and left the shopping on the "
                  "dining table. Please put it away.", "我刚买东西回来，放在餐桌上了，帮我收好。",
                  "juice_on_table", ctl, {"all": jgoal + [H]}, fridge([J], JY, JX), [J],
                  remove=["clutter_cereal_a", "clutter_cereal_b"])
    pantry = {"old_snack": on("snack_carton", f"{C6}/inside_shelf", 3.35, 0.36)}
    no_dishes = ["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"]
    TRAY = "west_tray"
    SHELVES = [f"bookcase_{i}/{sh}" for i in (1, 2, 3, 4) for sh in ("shelf_0", "shelf_1", "top")] + \
        [f"large_shelf_{i}/shelf_{k}" for i, n in ((1, 5), (2, 4), (3, 4), (4, 5), (5, 4), (6, 4)) for k in range(n)] + \
        ["large_shelf_6/top"]                                 # where books are kept (every bookcase and shelf)
    BK = ["bookcase_1/top", "bookcase_1/shelf_1"]          # the bookcase in the west dining room

    def inside_tray(asset, dx, dy):
        """lying in the serving tray on the west dining table (table top 0.71 m, tray floor 1 cm up)"""
        return {"asset": asset, "support": None, "z": 0.72, "xy": [round(-8.00 + dx, 3), round(7.40 + dy, 3)],
                "yaw_deg": 0.0}
    # fruit and snacks may both go in the fruit basket or in a low cabinet: any such pairing is put away
    keep_spots = lambda x: [["inside", x, BASKET], ["on", x, f"{C6}/inside_shelf"], ["on", x, f"{C4}/inside_shelf"]]  # noqa: E731
    loose_goal = {"any": [[a, b] for a in keep_spots(A) for b in keep_spots(SN)],
                  "all": jgoal + [["is_closed", C6], ["is_closed", C4], H]}
    def snack_away(hint=(3.60, 0.36)):
        return [nav(C6), S("open", articulated=C6), S("inspect", receptacle=C6), nav(SN), pick(SN), nav(C6),
                place(SN, f"{C6}/inside_shelf", list(hint)), S("close", articulated=C6)]
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
                      goal=loose_goal,
                      route=fridge([J], JY, JX) + into(A, BASKET) + snack_away())},
            instruction="I just got back from the shop; the juice, an apple and some snacks are on the dining table. Put each where things of its kind are kept, and close any door you open.",
            instruction_zh="我刚买东西回来，果汁、苹果和零食都在餐桌上。每样都收到平时放同类东西的地方，开过的门记得关上。"),
        # 11-17 (user): what is substituted is where the snacks are set down -- scored by the place (per-seed tiers
        # in scoring.LAYOUT_TIERS): the desk has room beside the homework (ideal), or the homework, books and
        # pencils cover the desk but for one small corner at its front (the study has no other top)
        "eat_now": fam(
            "juice_on_table", ["preference_allocation"],
            "how much of the desk is free (seed: room beside the homework; or the homework spread over all of it "
            "but one small corner)",
            "juice and a box of snacks; the kid doing homework in the study wants the snacks now; on one seed his "
            "homework covers the desk but for one small corner",
            "the snacks are not put away but brought to the kid, set down where they leave his homework as it is "
            "(the free corner when the desk is covered); the juice goes into the fridge",
            {"desk_free": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), SN: on("snack_carton", T2, 3.30, 7.00),
                                    "homework": on("notebook", DESK, -0.70, -5.95)},
                               watch=[J, SN], goal={"all": jgoal + [["on", SN, DESK], H]},
                               route=fridge([J], JY, JX) + fetch(SN, DESK, [-1.10, -5.95])),
             "desk_corner": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), SN: on("snack_carton", T2, 3.30, 7.00),
                                      **HOMEWORK_SPREAD},
                                 watch=[J, SN, *HOMEWORK_SPREAD],
                                 goal={"all": jgoal + [["on", SN, DESK], ["clear_of", SN, sorted(HOMEWORK_SPREAD), 0.0],
                                                       *[["near_start", n, 0.03] for n in sorted(HOMEWORK_SPREAD)], H]},
                                 route=fridge([J], JY, JX) + [nav(DESK), look(DESK)]
                                 + fetch(SN, DESK, list(DESK_CORNER)))},
            instruction="I just got back from the shop and left the shopping on the dining table. Please put it "
                        "away. The kid says he wants the snacks now; he is doing homework in the study.",
            instruction_zh="我刚买东西回来，放在餐桌上了，帮我收好。孩子说零食现在就要吃，他在书房写作业。"),
        "basket_missing": fam(
            "juice_on_table", ["container_absent", "storage_place"], "the seed's layout only",
            "juice and an apple; no fruit basket in the house, a serving tray on the island",
            "the apple has no basket to go to: the tray stands in for it; the juice into the fridge",
            {"": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), A: on("apple", T2, 3.30, 7.00),
                           "fruit_tray": on("serving_tray", ISL, 7.20, 1.75)},
                      watch=[J, A, "fruit_tray"],
                      goal={"all": jgoal + [["inside", A, "fruit_tray"], H]},
                      route=fridge([J], JY, JX) + into(A, "fruit_tray"))},
            instruction="I just got back from the shop and left the juice and an apple on the dining table. Put them away; fruit usually goes in the fruit basket.",
            instruction_zh="我刚买东西回来，果汁和苹果放在餐桌上了，帮我收好。水果平时放在果篮里。"),
        "not_shopping": fam(
            "juice_on_table", ["goal_items_unstated"], "the seed's layout only",
            "the juice from the shop, and the kid's toy car and picture book on the same table",
            "only what was bought is put away: the toy and the book are not shopping and stay",
            {"": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), "table_car": on("toy_car", T2, 3.30, 7.10),
                           "table_book": on("book_blue", T2, 3.35, 6.20)},
                      watch=[J, "table_car", "table_book"],
                      goal={"all": jgoal + [["near_start", "table_car", 0.03], ["near_start", "table_book", 0.03], H]},
                      route=[look(T2)] + fridge([J], JY, JX))}),
        "two_spots": fam(
            "juice_on_table", ["goal_items_unstated", "not_in_view"], "the seed's layout only",
            "the juice on the dining table; a second bag was emptied on the island: an apple and a box of "
            "snacks there, the basket next to them",
            "the shopping is in two places: find both, put each item away",
            {"": dict(add={J: on("juice_bottle", T2, 3.30, 6.70), A: on("apple", ISL, 7.60, 1.75),
                           SN: on("snack_carton", ISL, 7.85, 1.75), BASKET: on("fruit_basket", ISL, 7.10, 1.78),
                           **pantry},
                      remove=no_dishes, watch=[J, A, SN, BASKET],
                      goal=loose_goal,
                      # drive off the closed fridge first: turning on the spot there to face the island hit it
                      route=[look(T2)] + fridge([J], JY, JX) + [nav(ISL), look(ISL)] + into(A, BASKET)
                      # from the island no plan put the snack in at (3.60, 0.36): nearer the front, off the hinge
                      + snack_away((3.45, 0.42)))},
            instruction="I just got back from the shop with two bags and unpacked them in two different places. Put everything I bought away.",
            instruction_zh="我刚买东西回来，两袋东西拆开放在了两个不同的地方，买的东西都帮我收好。"),
        "tray_elsewhere": fam(
            "juice_on_table", ["container_absent", "not_in_view", "destination_full", "dependent_decisions"],
            "what lies on the tray (seed: an orange, or books covering it); seen only on arrival",
            "juice and an apple on the dining table; no fruit basket; a serving tray on the table in the west dining "
            "room: with an orange in it, or with four books lying flat over its floor",
            "the basket is missing, so find something else that holds fruit (the tray in the other room); what lies "
            "on it decides the rest: an orange -> the apple goes in beside it (fruit shares the tray, nothing to move); "
            "books over the floor -> the books back on the bookcase there, then the apple; the juice into the fridge",
            {c: dict(add={J: on("juice_bottle", T2, 3.30, 6.70), A: on("apple", T2, 3.30, 7.00),
                          TRAY: on("serving_tray", T1, -8.00, 7.40), **on_tray},
                     watch=[J, A, TRAY, *on_tray],
                     goal={"all": jgoal + [["fully_inside", A, TRAY], ["not on_floor", TRAY]]
                           + [["on_any", b, SHELVES] for b in on_tray if b.startswith("tray_book")] + [H]},
                     route=fridge([J], JY, JX) + [S("search", object=TRAY, region="dining_room_0_0"), look(TRAY)]
                     + [x for k, b in enumerate(sorted(n for n in on_tray if n.startswith("tray_book")))
                        for x in (nav(b), pick(b), nav(BK[k // 2]), place(b, BK[k // 2], [-9.59, 6.52 + 0.30 * (k % 2)]))]
                     + into(A, TRAY))
             for c, on_tray in (("orange_in_it", {"tray_orange": inside_tray("orange", -0.12, 0.08)}),
                                ("books_on_it", {f"tray_book_{k + 1}": inside_tray("book_blue", dx, dy)
                                                 for k, (dx, dy) in enumerate(((-0.10, -0.075), (0.10, -0.075),
                                                                               (-0.10, 0.075), (0.10, 0.075)))}))},
            instruction="I just got back from the shop and left the juice and an apple on the dining table. Put them away; fruit usually goes in the fruit basket.",
            instruction_zh="我刚买东西回来，果汁和苹果放在餐桌上了，帮我收好。水果平时放在果篮里。"),
    }
    return t, fams


# ================================================================== T23 pick up what was dropped
# 11-17 (user): every design but the control turns on a substitution of where the thing goes; per-seed tiers
# (scoring.LAYOUT_TIERS[("T23", "*")], built here with cost_tiers): the best place a seed offers is the best tier
TV_Z, BLOCK_H = 0.484, 0.04
WORKTOPS = [COUNTER, "kitchen_counter_1/top", ISL]
OTHER_TOPS = ["kitchen_counter_1/top", ISL]            # a kitchen worktop other than the small kitchen's counter


def toy_bin_full(name, sup_z, x0, y0):
    """the kid's small toy bin (22 x 17 x 9 cm) full of toy blocks, two layers of 4 x 3 (T12's full bin): no room"""
    add = {name: {"asset": "small_storage_bin", "support": "tv_stand_2/top", "xy": [x0, y0], "yaw_deg": 0.0}}
    cells = [(dx, dy, dz) for dz in (0.0, BLOCK_H + 0.001) for dx in (-0.0615, -0.0205, 0.0205, 0.0615)
             for dy in (-0.041, 0.0, 0.041)]
    add.update({f"bin_block_{i + 1}": {"asset": "wooden_block", "support": None, "z": round(sup_z + 0.009 + dz, 3),
                                       "xy": [round(x0 + dx, 3), round(y0 + dy, 3)], "yaw_deg": 0}
                for i, (dx, dy, dz) in enumerate(cells)})
    return add


def counter_dishes(cups_between):
    """dropped_out_of_view: the small kitchen's counter (x -0.52..0.25, y 6.97..9.44; the base reaches it from the
    west edge and both ends) covered where it can be reached: a row of plates at each end, plates along the west
    edge 3 cm apart and a row of bowls behind them 1.7 cm apart (no 4 cm spoon fits anywhere).  ``cups_between``:
    every other plate of the west row a cup instead -- 7 cm gaps beside each cup: a spoon fits, a 25 cm plate or
    pot lid does not"""
    out = {}
    for k, x in enumerate((-0.398, -0.148, 0.100)):
        out[f"counter_plate_s{k + 1}"] = on("breakfast_plate", COUNTER, x, 7.094)
        out[f"counter_plate_n{k + 1}"] = on("breakfast_plate", COUNTER, x, 9.313)
    for k in range(7):
        y = round(7.371 + 0.277 * k, 3)
        cup = cups_between and k % 2 == 1
        out[f"counter_{'cup' if cup else 'plate'}_w{k + 1}"] = on("breakfast_cup" if cup else "breakfast_plate",
                                                                  COUNTER, -0.398, y)
    for k in range(10):
        out[f"counter_bowl_{k + 1}"] = on("breakfast_bowl", COUNTER, -0.181, round(7.324 + 0.195 * k, 3))
    return out


def shelf_books(levels):
    """dropped_in_two_rooms: the kid's bookcase (bookcase_2, 59 x 36 cm a level): four piles of two red books on
    each named level (48 x 33 cm of it, 2 cm in from the sides, an 8 cm strip left: the 20 x 14 cm book does not fit, and on a pile it
    would lie 8 cm up, not on the level)"""
    Z = {"bookcase_2/shelf_0": 0.207, "bookcase_2/shelf_1": 0.458, "bookcase_2/top": 0.709}
    out = {}
    for lv, high in levels:
        tag = lv.split("/")[1]
        for i, (x, y) in enumerate([(x, y) for x in (0.845, 1.090) for y in (-0.525, -0.355)]):
            for h in range(high):        # the pile's bottom book on the level (it moves with it), the next on it
                out[f"kid_book_{tag}_{i + 1}{'abc'[h]}"] = on("book_red", lv, x, y) if h == 0 else \
                    {"asset": "book_red", "support": None, "z": round(Z[lv] + 0.0405 * h, 4), "xy": [x, y],
                     "yaw_deg": 0.0}
    return out


def t23():
    from benchmark.v6.scoring import LAYOUT_TIERS, cost_tiers
    SP = "dropped_spoon"
    START = (-1.20, 9.40, 0.0)                       # the small kitchen with the counter
    ctl = {"note": "a spoon on the kitchen floor; the spoons are kept on the kitchen counter",
           "add": {SP: floor("breakfast_spoon", -0.85, 7.70, 30.0)}}
    # either kitchen counter is where a spoon belongs (the kitchen's two counters stand 1.7 m apart)
    sgoal = [["on_any", SP, WORKTOPS]]                                         # any kitchen worktop
    t = base_task("T23_pick_up_dropped", "ZB-T23", "Something fell on the floor. Please pick it up and put it "
                  "where it belongs.", "地上掉了东西，帮忙捡起来放好。", "spoon_on_floor", ctl,
                  {"all": sgoal + [H]}, [look(COUNTER)] + fetch(SP, COUNTER, [-0.10, 7.60]), [SP], start=START)
    spoon = {SP: floor("breakfast_spoon", -0.85, 7.70, 30.0)}
    back = fetch(SP, COUNTER, [-0.10, 7.60])
    LT = LAYOUT_TIERS.setdefault(("T23", "*"), {})
    BLK, BIN, TRAY = "dropped_block", "toy_bin", "spare_tray"
    BIN_AT, TRAY_AT = (7.30, 0.36), (7.80, 0.36)
    full_bin = toy_bin_full(BIN, TV_Z, *BIN_AT)
    bin_stays = [["fully_inside", f"bin_block_{i}", BIN] for i in range(1, 25)]
    tray = {TRAY: on("shallow_sorting_tray", TV, *TRAY_AT)}
    find_tv = [S("explore_room", room="living_room_0_0"), nav(TV), look(TV)]
    # 11-19 (physics side): place into the tray needs base_near(tray) (1.3 m); navigate(TV) parks at the 1.7 m
    # stand's nearest stand-off, which from its west end is about 1.3 m from the tray at the east end
    into_tray = [nav(TRAY), place(BLK, TRAY)]
    off_floor = lambda x: [["not on_floor", x]]  # noqa: E731

    # by_kind: the block goes where the kid's toys are kept -- the toy box (ideal); or (11-17) his small toy bin,
    # full of blocks, an empty sorting tray beside it (capacity)
    block_k = floor("wooden_block", -1.00, 8.50)
    LT["by_kind__toy_box"] = cost_tiers([(sgoal + [["inside", BLK, "toy_box"]], 0), (sgoal + off_floor(BLK), 2)])
    LT["by_kind__bin_full"] = cost_tiers([(sgoal + [["inside", BLK, TRAY]] + bin_stays, 0),
                                          (sgoal + [["inside", BLK, BIN]], 1), (sgoal + off_floor(BLK), 2)])

    # belongs_on_floor (11-17): the kid's block fell beside the kitchen bin and the laundry basket (they live on
    # the floor and stay); no toy box in the house, a sorting tray on the TV stand (absent); or his toy bin full,
    # the tray beside it (capacity).  The laundry basket holds clothes: the block in it is the worst
    BB, LB = "kitchen_bin", "laundry_basket"
    floor_things = {BB: floor("trash_can", -1.10, 7.25), LB: floor("storage_basket", -1.15, 8.40)}
    stay = [["near_start", BB, 0.03], ["near_start", LB, 0.03]]
    on_floor = [["on_floor", BB], ["on_floor", LB]]
    blk_f = {BLK: floor("wooden_block", -0.85, 7.70)}
    LT["belongs_on_floor__no_toy_box"] = cost_tiers(
        [([["inside", BLK, TRAY]], 0), ([["inside", BLK, LB]], 2)], [(stay, 1), (on_floor, 1)])
    LT["belongs_on_floor__bin_full"] = cost_tiers(
        [([["inside", BLK, TRAY]] + bin_stays, 0), ([["inside", BLK, BIN]], 1), ([["inside", BLK, LB]], 2)],
        [(stay, 1), (on_floor, 1)])

    # dropped_out_of_view (11-17): the spoon slid into the dining room next door and the small kitchen's counter
    # is covered with dishes (taken); or (11-19) the pot lid slid there and the counter's gaps fit a spoon, not the
    # 25 cm lid (capacity): another worktop (the island, the other kitchen's counter) is the best.  Not a plate any
    # more: a plate has only its thickness pinch, and pick has no path for a flat thing on the floor (muqingj
    # 11-19); the lid is taken by its knob.  The island's pot and lid are removed in that seed (one lid in the house)
    PL = "dropped_lid"
    dishes_a, dishes_b = counter_dishes(False), counter_dishes(True)
    counter_base = ["plate_counter_a", "plate_counter_b", "cup_counter_b", "spoon_counter"]

    def out_of_view_tiers(x, dishes):
        return cost_tiers([([["on_any", x, OTHER_TOPS]], 0),
                           ([["on", x, COUNTER], ["clear_of", x, sorted(dishes), 0.0]], 1),
                           ([["on", x, COUNTER]], 2)])
    LT["dropped_out_of_view__counter_full"] = out_of_view_tiers(SP, dishes_a)
    LT["dropped_out_of_view__no_room_for_lid"] = out_of_view_tiers(PL, dishes_b)

    # only_this_room (11-17): "the kitchen floor"; the kid's plastic cup fell there, his cups are kept on low
    # cabinet 4: with room (ideal); or cabinet 4's top full -- two pots and three of his cups (capacity): a
    # worktop or the other low cabinet.  The toy car on the living-room floor is not in the kitchen and stays.
    # 11-19 (muqingj): on cabinet 4's top, not on its inside shelf -- a rim-pinched cup put on a shelf with a board
    # 29.5 cm above it lifts the hand out into that board (as T17's top-pinched block did)
    CUP, CAR = "dropped_cup", "living_car"
    C4S, C6S, C4T = f"{C4}/inside_shelf", f"{C6}/inside_shelf", f"{C4}/top"
    car = {CAR: floor("toy_car", 4.36, 1.68)}
    kid_cups_a = {f"kid_cup_{k + 1}": on("plastic_cup", C4T, x, 0.42) for k, x in enumerate((1.15, 1.26))}
    full_c4 = {"stored_pot_1": on("soup_pot", C4T, 1.20, 0.42, 90.0), "stored_pot_2": on("soup_pot", C4T, 1.50, 0.42, 90.0),
               **{f"kid_cup_{k + 1}": on("plastic_cup", C4T, 1.70, y) for k, y in enumerate((0.325, 0.42, 0.515))}}
    not_in_pots = [["not inside", CUP, "stored_pot_1"], ["not inside", CUP, "stored_pot_2"]]
    closed = [["is_closed", C4], ["is_closed", C6]]
    car_stays = [["near_start", CAR, 0.03]]
    LT["only_this_room__cabinet_room"] = cost_tiers(
        [([["on", CUP, C4T]], 0), ([["on_any", CUP, [C4S, C6S, f"{C6}/top"]]], 1), ([["on_any", CUP, WORKTOPS]], 1)],
        [(closed, 1), (car_stays, 2)])
    LT["only_this_room__cabinet_full"] = cost_tiers(
        [([["on_any", CUP, [C4S, C6S, f"{C6}/top"]]], 0), ([["on_any", CUP, WORKTOPS]], 0),
         ([["on", CUP, C4T]] + not_in_pots, 1)], [(closed, 1), (car_stays, 2)])

    # dropped_in_two_rooms (11-17): the spoon on the kitchen floor and the kid's teddy bear on the study floor; his
    # bookcase (bookcase_2) with room (ideal), or his bed; or every level full, piles of books (capacity): another
    # bookcase or a desk.  Anywhere else (a table, a kitchen top) is the worst.  11-19 (muqingj): a bear, not a
    # book -- a book has only its thickness pinch and pick has no path for a flat thing on the floor; the bear
    # (10.6 x 16 cm, top pinch) fits in no gap of the piles either.  The reference puts it on a bookcase's top: a
    # top-pinched thing set on a level with a board above lifts the hand out into that board
    BK = "dropped_bear"
    BED = "mattress_1/top"
    KIDS = ["bookcase_2/shelf_0", "bookcase_2/shelf_1", "bookcase_2/top"]
    OTHER_CASES = [f"bookcase_{i}/{sh}" for i in (1, 3, 4) for sh in ("shelf_0", "shelf_1", "top")] + \
        [f"large_shelf_{i}/shelf_{k}" for i, n in ((1, 5), (2, 4), (3, 4), (4, 5), (5, 4), (6, 4)) for k in range(n)] + \
        ["large_shelf_6/top", DESK, DESK3]
    books_a, books_b = shelf_books([("bookcase_2/shelf_1", 1)]), shelf_books([(lv, 2) for lv in KIDS])
    LT["dropped_in_two_rooms__shelf_room"] = cost_tiers(
        [(sgoal + [["on_any", BK, KIDS + [BED]]], 0), (sgoal + [["on_any", BK, OTHER_CASES]], 1),
         (sgoal + off_floor(BK), 2)])
    LT["dropped_in_two_rooms__shelf_full"] = cost_tiers(
        [(sgoal + [["on_any", BK, OTHER_CASES + [BED]]] + [["near_start", n, 0.03] for n in sorted(books_b)], 0),
         (sgoal + [["on_any", BK, KIDS]], 1), (sgoal + off_floor(BK), 2)])
    book = {BK: floor("teddy_bear", 0.25, -6.10, 15.0)}

    fams = {
        "by_kind": fam(
            "spoon_on_floor", ["storage_place", "multi_object_goal"],
            "where the kid's toys are kept (seed: the toy box in the living room; or his small toy bin on the TV "
            "stand, full, an empty sorting tray beside it)",
            "a spoon and a toy block on the kitchen floor; the kid's toys are kept in the toy box, or in a small bin "
            "already full of blocks",
            "each thing goes back where its kind belongs: the spoon to the counter, the block with the toys -- into "
            "the tray beside the toy bin when the bin is full",
            {"toy_box": dict(add={**spoon, BLK: block_k, "toy_box": floor("toy_box", 5.70, 0.80)},
                             watch=[SP, BLK, "toy_box"], goal={"all": sgoal + [["inside", BLK, "toy_box"], H]},
                             route=[look(COUNTER)] + back + into(BLK, "toy_box")),
             "bin_full": dict(add={**spoon, BLK: block_k, **full_bin, **tray}, watch=[SP, BLK, BIN, TRAY],
                              goal={"all": sgoal + [["inside", BLK, TRAY], *bin_stays, H]},
                              route=[look(COUNTER)] + back + [nav(BLK), pick(BLK)] + find_tv
                              + [S("measure", object=BIN)] + into_tray)}),
        "belongs_on_floor": fam(
            "spoon_on_floor", ["goal_items_unstated", "container_absent"],
            "what holds the kid's toys (seed: no toy box, a sorting tray on the TV stand; or his toy bin there, "
            "full, the tray beside it)",
            "the kid's toy block fell on the kitchen floor beside the waste bin and the laundry basket, which live "
            "on the floor; no toy box, or his toy bin full",
            "only what fell is picked up (the bin and the basket stay); the block goes in the tray, not in the "
            "laundry basket next to it",
            {"no_toy_box": dict(add={**blk_f, **floor_things, **tray}, watch=[BLK, BB, LB, TRAY],
                                goal={"all": [["inside", BLK, TRAY], *stay, H]},
                                route=[nav(BLK), look(BLK), pick(BLK)] + find_tv + into_tray),
             "bin_full": dict(add={**blk_f, **floor_things, **full_bin, **tray}, watch=[BLK, BB, LB, BIN, TRAY],
                              goal={"all": [["inside", BLK, TRAY], *bin_stays, *stay, H]},
                              route=[nav(BLK), look(BLK), pick(BLK)] + find_tv
                              + [S("measure", object=BIN)] + into_tray)}),
        "dropped_out_of_view": fam(
            "spoon_on_floor", ["not_in_view", "storage_place"],
            "what slid away and how the counter is taken (seed: the spoon, the counter covered with dishes; or the "
            "pot lid, the counter's gaps too small for it)",
            "the dropped thing slid into the dining room next door, out of view; the small kitchen's counter is "
            "covered with dishes (no room; or only room for small things)",
            "find it, then put it on another kitchen worktop (the island) rather than on or among the dishes",
            {"counter_full": dict(add={SP: floor("breakfast_spoon", 1.05, 7.50, 30.0), **dishes_a},
                                  remove=counter_base, watch=[SP, *dishes_a],
                                  goal={"all": [["on_any", SP, OTHER_TOPS], H]},
                                  route=[look(COUNTER), S("search", object=SP, region="dining_room_0_1")]
                                  + fetch(SP, ISL, [7.40, 1.62])),
             "no_room_for_lid": dict(add={PL: floor("pot_lid", 1.10, 7.50), **dishes_b},
                                     remove=counter_base + ["handled_cooking_pot", "pot_lid"], watch=[PL, *dishes_b],
                                       goal={"all": [["on_any", PL, OTHER_TOPS], H]},
                                       route=[look(COUNTER), S("search", object=PL, region="dining_room_0_1")]
                                       + fetch(PL, ISL, [7.40, 1.70]))}),
        "only_this_room": fam(
            "spoon_on_floor", ["referent_clue", "storage_place"],
            "how full the kid's cup spot is (seed: room; or two pots and three of his cups on it)",
            "the kid's plastic cup on the kitchen floor (his cups are kept on low cabinet 4), the kid's toy car on "
            "the living-room floor",
            "the instruction names the kitchen: pick up the cup, leave the car; the cup with his cups, or -- the "
            "cabinet's top full -- on a worktop or in a low cabinet",
            {"cabinet_room": dict(add={CUP: floor("plastic_cup", -0.85, 7.70), **car, **kid_cups_a},
                                  watch=[CUP, CAR, *kid_cups_a],
                                  goal={"all": [["on", CUP, C4T], *closed, *car_stays, H]},
                                  route=[nav(CUP), look(CUP), pick(CUP), nav(C4T), look(C4T),
                                         place(CUP, C4T, [1.45, 0.42])]),
             "cabinet_full": dict(add={CUP: floor("plastic_cup", -0.85, 7.70), **car, **full_c4},
                                  watch=[CUP, CAR, *full_c4],
                                  goal={"all": [["on_any", CUP, WORKTOPS], *closed, *car_stays, H]},
                                  route=[nav(CUP), look(CUP), pick(CUP), nav(C4T), look(C4T), nav(COUNTER),
                                         place(CUP, COUNTER, [-0.10, 7.60])])},
            instruction="Something fell on the kitchen floor. Please pick it up and put it where it belongs.",
            instruction_zh="厨房地上掉了东西，帮忙捡起来放好。"),
        "dropped_in_two_rooms": fam(
            "spoon_on_floor", ["goal_items_unstated", "not_in_view", "storage_place"],
            "how full the kid's bookcase is (seed: room, his books on one level; or every level full of piles)",
            "a spoon on the kitchen floor, and the kid's teddy bear on the study floor; his bookcase in the bedroom "
            "has room, or is full on every level",
            "more than one thing fell, in different rooms: find both; the spoon to the counter, the bear to his "
            "bookcase or his bed -- or, when the bookcase is full, another bookcase or a desk",
            {"shelf_room": dict(add={**spoon, **book, **books_a}, watch=[SP, BK, *books_a],
                                goal={"all": sgoal + [["on_any", BK, KIDS + [BED]], H]},
                                route=[look(COUNTER)] + back + [S("search", object=BK, region="living_room_0_1")]
                                + fetch(BK, "bookcase_2/top", [1.00, -0.43])),
             "shelf_full": dict(add={**spoon, **book, **books_b}, watch=[SP, BK, *books_b],
                                goal={"all": sgoal + [["on_any", BK, OTHER_CASES + [BED]], H]},
                                route=[look(COUNTER)] + back + [S("search", object=BK, region="living_room_0_1"),
                                                               nav(BK), pick(BK), nav("bookcase_2/top"),
                                                               look("bookcase_2/top"), nav("bookcase_3/top"),
                                                               place(BK, "bookcase_3/top", [2.10, -4.85])])},
            instruction="Some things fell on the floor around the house. Please pick them up and put them where "
                        "they belong.",
            instruction_zh="家里地上掉了些东西，帮忙捡起来放好。"),
    }
    return t, fams


# ================================================================== T24 something to eat for the kid
AT_DESK3 = [DESK3, "bookcase_4/top"]       # by the bedroom desk: the desk or the bookcase beside it
SHELF4 = "bookcase_4/top"
# two_kids desk3_covered (11-18, user): the bedroom kid's homework over the whole bedroom desk (x 5.834..7.488,
# y -5.789..-5.188, the robot at its front, y > -5.188) in three rows of seven, ~4 cm between the rows and ~1.3 cm
# between the books (the 6 cm apple fits nowhere); his things go on the bookcase beside it (its west edge reachable)
_ROWS3 = ((-5.272, ("notebook", "book_red", "notebook", "book_red", "notebook", "book_red", "notebook")),
          (-5.488, ("book_green",) * 7),
          (-5.705, ("book_red", "notebook", "book_red", "notebook", "book_red", "notebook", "book_red")))
_W3 = {"notebook": 0.21, "book_red": 0.24, "book_green": 0.22}


def _desk3_spread():
    out, k = {}, 0
    for y, row in _ROWS3:
        gap = (7.488 - 5.834 - sum(_W3[a] for a in row)) / (len(row) + 1)
        x = 5.834 + gap
        for a in row:
            k += 1
            out["homework_3" if k == 18 else f"hw3_{a}_{k}"] = on(a, DESK3, round(x + _W3[a] / 2, 3), y)
            x += _W3[a] + gap
    return out


HOMEWORK3_SPREAD = _desk3_spread()


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
    from benchmark.v6.scoring import LAYOUT_TIERS, cost_tiers
    LT = LAYOUT_TIERS.setdefault(("T24", "*"), {})
    to_desk = lambda x: fetch(x, DESK, [-1.10, -5.95])  # noqa: E731
    at = lambda x: [["on", x, DESK]]  # noqa: E731
    basket_isl = {"home_basket": on("fruit_basket", ISL, 7.10, 1.78)}
    # no_apples_for_him (11-17, user: no "he doesn't like apples"; the task's words): the apple free on the table
    # (ideal); or on someone's plate at a place set at the table, someone eating (in use), a banana in the fruit
    # basket on the island -- someone's apple taken is the worst
    SEAT = {"seat_plate": on("breakfast_plate", T2, 3.30, 6.70), "seat_spoon": on("breakfast_spoon", T2, 3.30, 6.90),
            "seat_cup": on("breakfast_cup", T2, 3.52, 6.70)}
    apple_on_seat = {AP: {"asset": "apple", "support": None, "z": 0.858, "xy": [3.30, 6.70], "yaw_deg": 0.0}}
    banana_in_basket = {BA: {"asset": "banana", "support": None, "z": 0.881, "xy": [7.10, 1.78], "yaw_deg": 0.0}}
    seat_stays = [["near_start", n, 0.03] for n in (AP, "seat_plate")]
    LT["no_apples_for_him__apple_free"] = cost_tiers([(at(AP), 0)])
    LT["no_apples_for_him__apple_in_use"] = cost_tiers(
        [(at(BA) + seat_stays, 0), (at(BA), 1), (at(AP), 2)])
    # dinner_soon (11-17, user): dinner in half an hour -- fruit, not the snacks; the fruit is an apple, or (no
    # apple) a banana beside the snacks
    LT["dinner_soon__apple"] = cost_tiers([(at(AP) + [["not on", SN, DESK]], 0), (at(AP), 1), (at(SN), 2)])
    LT["dinner_soon__banana"] = cost_tiers([(at(BA) + [["not on", SN, DESK]], 0), (at(BA), 1), (at(SN), 2)])
    # fruit_out_of_view (11-17, user): no food on the dining table; the fruit basket on the bedroom bookcase holds
    # an apple (ideal, to be found); or it is empty and the only fruit is a banana on the kitchen counter (absent)
    LT["fruit_out_of_view__apple_in_basket"] = cost_tiers([(at(AP), 0), (at("home_basket"), 2)])
    LT["fruit_out_of_view__basket_empty"] = cost_tiers([(at(BA), 0), (at("home_basket"), 2)])
    # two_kids (11-17, user): one each -- an apple and a banana; or only an apple and a box of snacks (absent);
    # 11-18 (user): scored by where each thing is set down -- on the kid's own desk beside his homework; one step
    # down: on the homework, or (the bedroom kid) on the bookcase beside his desk; both to one kid the worst.  Seed
    # desk3_covered: the bedroom desk all homework, so the bookcase is his best spot (occupied)
    each = lambda a, b: [[["on", a, DESK], ["on_any", b, AT_DESK3]], [["on", b, DESK], ["on_any", a, AT_DESK3]]]  # noqa: E731
    same = lambda a, b: [[["on", a, DESK], ["on", b, DESK]], [["on_any", a, AT_DESK3], ["on_any", b, AT_DESK3]]]  # noqa: E731

    def kids_tiers(a, b, hw3_names, covered):
        study = lambda x: [([["on", x, DESK], ["clear_of", x, ["homework"], 0.0]], 0), ([["on", x, DESK]], 1)]  # noqa: E731
        bed = lambda y: (([] if covered else [([["on", y, DESK3], ["clear_of", y, hw3_names, 0.0]], 0)])  # noqa: E731
                         + [([["on", y, SHELF4]], 0 if covered else 1), ([["on", y, DESK3]], 1)])
        opts = [(gs + gb, cs + cb) for x, y in ((a, b), (b, a)) for gs, cs in study(x) for gb, cb in bed(y)]
        return cost_tiers(opts + [(g, 3) for g in same(a, b)])
    for case, (a, b) in (("apple_banana", (AP, BA)), ("apple_snacks", (AP, SN))):
        LT[f"two_kids__{case}"] = kids_tiers(a, b, ["homework_3"], False)
    LT["two_kids__desk3_covered"] = kids_tiers(AP, BA, sorted(HOMEWORK3_SPREAD), True)
    fams = {
        "no_apples_for_him": fam(
            "apple_on_table", ["resource_in_use"],
            "whether the apple is free (seed: alone on the table; or on someone's plate at a place set at the "
            "table, a banana in the fruit basket on the island)",
            "an apple on the dining table: free, or on someone's plate at a place where someone is eating",
            "bring something nobody is eating: the apple when it is free, else the banana from the basket",
            {"apple_free": dict(add={AP: on("apple", T2, 3.30, 6.70), **hw}, watch=[AP],
                                goal={"all": at(AP) + [H]}, route=[look(T2)] + to_desk(AP)),
             "apple_in_use": dict(add={**SEAT, **apple_on_seat, **basket_isl, **banana_in_basket, **hw},
                                  watch=[AP, BA, *SEAT],
                                  goal={"all": at(BA) + seat_stays + [H]},
                                  route=[nav(T2), look(T2), nav(ISL), look(ISL)] + to_desk(BA))}),
        "dinner_soon": fam(
            "apple_on_table", ["preference_allocation"],
            "which fruit is beside the snacks (seed: an apple; or a banana)",
            "a fruit and a box of snacks on the table; dinner is in half an hour",
            "with dinner close, the fruit, not the snacks",
            {"apple": dict(add={AP: on("apple", T2, 3.30, 6.70), SN: on("snack_carton", T2, 3.30, 7.10), **hw},
                           watch=[AP, SN], goal={"all": at(AP) + [["not on", SN, DESK], H]},
                           route=[look(T2)] + to_desk(AP)),
             "banana": dict(add={BA: on("banana", T2, 3.30, 6.70), SN: on("snack_carton", T2, 3.30, 7.10), **hw},
                            watch=[BA, SN], goal={"all": at(BA) + [["not on", SN, DESK], H]},
                            route=[look(T2)] + to_desk(BA))},
            instruction="The kid is doing homework in the study and is hungry. Bring him something to eat; "
                        "dinner is in half an hour.",
            instruction_zh="孩子在书房写作业饿了，给他拿点吃的。还有半小时就吃晚饭了。"),
        "fruit_out_of_view": fam(
            "apple_on_table", ["not_in_view", "resource_absent"],
            "what the fruit basket holds (seed: an apple; or nothing, a banana on the kitchen counter)",
            "no food on the dining table; the fruit basket is on the bedroom bookcase, with an apple in it or empty",
            "find where food is kept (the fruit basket) and take something from it; when it is empty, look on for "
            "other fruit (the banana on the kitchen counter)",
            {"apple_in_basket": dict(
                add={"home_basket": on("fruit_basket", "bookcase_2/top", 0.92, -0.43),
                     AP: {"asset": "apple", "support": None, "z": 0.73, "xy": [0.92, -0.43], "yaw_deg": 0.0}, **hw},
                watch=[AP, "home_basket"], goal={"all": at(AP) + [H]},
                route=[look(T2), S("search", object="home_basket", region="bedroom_0_1")] + to_desk(AP)),
             "basket_empty": dict(
                add={"home_basket": on("fruit_basket", "bookcase_2/top", 0.92, -0.43),
                     BA: on("banana", COUNTER, -0.40, 8.70), **hw},
                watch=[BA, "home_basket"], goal={"all": at(BA) + [H]},
                route=[look(T2), S("search", object="home_basket", region="bedroom_0_1"), look("bookcase_2/top"),
                       S("search", object=BA, region="kitchen_0_1")] + to_desk(BA))}),
        "where_is_he": fam(
            "apple_on_table", ["referent_clue"], "where the homework lies (seed: the study desk or the bedroom desk)",
            "the kid's open homework lies on one of two desks; the instruction does not say which room",
            "the kid is where his homework is: bring the food to that desk",
            {"study": dict(add={AP: on("apple", T2, 3.30, 6.70), **hw}, goal={"all": [["on", AP, DESK], H]},
                           route=[nav(AP), pick(AP), look(DESK3), nav(DESK), place(AP, DESK, [-1.10, -5.95])]),
             "bedroom": dict(add={AP: on("apple", T2, 3.30, 6.70), **hw3}, goal={"all": [["on_any", AP, AT_DESK3], H]},
                             route=[nav(AP), pick(AP), look(DESK), nav(DESK3), place(AP, DESK3, [6.20, -5.50])])},
            instruction="The kid is doing homework and is hungry. Bring him something to eat.",
            instruction_zh="孩子写作业饿了，给他拿点吃的。"),
        "two_kids": fam(
            "apple_on_table", ["count_from_scene", "multi_object_goal"],
            "what there is to share and where it can go (seed: an apple and a banana; or an apple and a box of "
            "snacks; or an apple and a banana, the bedroom desk covered in homework)",
            "two kids' homework, on the study desk and on the bedroom desk; two things to eat on the table (two "
            "fruits, or one fruit and a box of snacks); the bedroom desk may be all homework",
            "one snack for each kid, each set down by his homework without covering it: on the desk, or on the "
            "bookcase beside a desk that has no room",
            {**{case: dict(add={AP: on("apple", T2, 3.30, 6.70), b: on(asset, T2, 3.30, 7.10), **hw, **hw3},
                           watch=[AP, b], goal={"all": [H], "any": each(AP, b)},
                           route=fetch(AP, DESK, [-1.10, -5.95]) + fetch(b, DESK3, [6.20, -5.50]))
                for case, b, asset in (("apple_banana", BA, "banana"), ("apple_snacks", SN, "snack_carton"))},
             "desk3_covered": dict(add={AP: on("apple", T2, 3.30, 6.70), BA: on("banana", T2, 3.30, 7.10), **hw,
                                        **HOMEWORK3_SPREAD},
                                   watch=[AP, BA, *HOMEWORK3_SPREAD], goal={"all": [H], "any": each(AP, BA)},
                                   route=fetch(AP, DESK, [-1.10, -5.95]) + [nav(DESK3), look(DESK3)]
                                   + fetch(BA, SHELF4, [7.00, -6.76]))},
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
    MUGS = ["mug_dining_cabinet", "mug_shelf", "mug_counter"]       # the dining room's mugs: the fallback

    def cups_goal(n_tv, n_in):
        """exactly two cups by the guests, as many ordinary ones as the house has (up to two), the ones there stay"""
        mine = [f"tv_cup_{k + 1}" for k in range(n_tv)] + [f"stock_cup_{k + 1}" for k in range(n_in)]
        return [["count_on_at_least", mine + MUGS, TV, 2], ["count_on_at_most", mine + MUGS, TV, 2],
                ["count_on_at_least", mine, TV, min(2, len(mine))]] + \
            [["near_start", f"tv_cup_{k + 1}", 0.03] for k in range(n_tv)]

    def cups_route(n_tv, n_in):
        need, out, hints = 2 - n_tv, [], [7.55, 7.05]
        if need <= 0:
            return out
        out += explore(C4)
        take = min(need, n_in)
        for k in range(take):
            x = f"stock_cup_{k + 1}"
            out += (from_closed(x, C4) if k == take - 1 else [nav(x), pick(x)]) + [nav(TV), place(x, TV, [hints[k], 0.36])]
        if take == 0:
            out += [S("close", articulated=C4)]
        for k in range(take, need):
            out += [S("search", object="mug_shelf", region="dining_room_0_1")] + fetch("mug_shelf", TV, [hints[k], 0.36])
        return out
    # 11-18 (user): every design but the control and little_guest gets a seed where the thing is substituted
    from benchmark.v6.scoring import LAYOUT_TIERS, cost_tiers
    LT = LAYOUT_TIERS.setdefault(("T25", "*"), {})
    PLAIN = ["cup_counter_b", "cup_kitchen_cabinet", "cup_side_table"]      # the house's ordinary cups
    CB = "cup_counter_b"
    BLOCKS = [f"cup_block_{k + 1}" for k in range(3)]     # the kid's wooden blocks kept in the counter's cup
    drink = [["on", J, TV], ["upright", J]]
    mug_route = [S("search", object="mug_shelf", region="dining_room_0_1")] + fetch("mug_shelf", TV, [7.55, 0.36])
    # cup_elsewhere: a cup on the counter (find it); no ordinary cup in the house, a mug (absent); the counter's
    # cup holds the kid's three wooden blocks (its inside is 7 cm across: a sponge does not fit), the other
    # ordinary cups gone (in use): a mug; the blocks taken out and that cup used is second; the cup brought with
    # the blocks in it the worst
    LT["cup_elsewhere__counter_cup"] = cost_tiers([(drink + [["count_on_at_least", HOUSE_CUPS, TV, 1]], 0)])
    LT["cup_elsewhere__only_mugs"] = cost_tiers([(drink + [["count_on_at_least", MUGS, TV, 1]], 0)])
    LT["cup_elsewhere__blocks_in_cup"] = cost_tiers(
        [(drink + [["count_on_at_least", MUGS, TV, 1], ["near_start", CB, 0.03]] + [["inside", b, CB] for b in BLOCKS], 0),
         (drink + [["on", CB, TV]] + [["not inside", b, CB] for b in BLOCKS], 1), (drink + [["on", CB, TV]], 2)])
    fams = {
        "cup_elsewhere": fam(
            "drink_on_island", ["not_in_view", "resource_absent"],
            "what cup there is (seed: one on the kitchen counter; or only the dining room's mugs; or the counter's "
            "cup holds the kid's blocks, the other ordinary cups gone)",
            "the juice on the island, no cup there; a cup on the kitchen counter in the small kitchen (maybe "
            "holding the kid's blocks), or no ordinary cup at all; mugs in the dining room",
            "a drink is served with a cup: find one free to drink from -- a mug when the only cup is in use",
            {"counter_cup": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80)}, watch=[J, CB],
                                 # the cup at the counter's front edge: 18 cm deep under the wall cabinet no arm
                                 # reached it
                                 move={CB: P(COUNTER, -0.45, 8.20)},
                                 goal={"all": serve(J, ()) + [H]},
                                 route=fetch(J, TV, [7.30, 0.36]) + [S("search", object=CB, region="kitchen_0_1")]
                                 + fetch(CB, TV, [7.55, 0.36])),
             "only_mugs": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80)}, remove=PLAIN, watch=[J, *MUGS],
                               goal={"all": drink + [["count_on_at_least", MUGS, TV, 1], H]},
                               route=fetch(J, TV, [7.30, 0.36]) + mug_route),
             "blocks_in_cup": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80),
                                        **{b: {"asset": "wooden_block", "support": None, "z": round(1.019 + 0.041 * k, 3),
                                               "xy": [-0.45, 8.20], "yaw_deg": 0.0} for k, b in enumerate(BLOCKS)}},
                                remove=["cup_kitchen_cabinet", "cup_side_table"], move={CB: P(COUNTER, -0.45, 8.20)},
                                watch=[J, CB, *BLOCKS, *MUGS],
                                goal={"all": drink + [["count_on_at_least", MUGS + [CB], TV, 1], H]},
                                route=fetch(J, TV, [7.30, 0.36]) + [S("search", object=CB, region="kitchen_0_1"),
                                                                    look(COUNTER)] + mug_route)}),
        "cold_one": fam(
            "drink_on_island", ["preference_allocation", "resource_absent"],
            "what is cold in the fridge (seed: a bottle of the same juice; or only a can of soda)",
            "a bottle on the island at room temperature; in the fridge another juice or (no juice) a can of soda; "
            "it is a hot day",
            "on a hot day the cold one, juice or not: open the fridge for it, close it again",
            {case: dict(add={J: on("juice_bottle", ISL, 7.30, 1.80), CUP: on("breakfast_cup", ISL, 7.55, 1.80),
                             cold: {**in_fridge(cold), "asset": asset}},
                        watch=[J, cold, CUP],
                        goal={"all": serve(cold) + [["near_start", J, 0.03], ["is_closed", FR], H]},
                        route=[nav(FR), S("open", articulated=FR), nav(cold), pick(cold),
                               S("retreat", obstacle=FR, distance_m=0.3), S("close", articulated=FR), nav(TV),
                               place(cold, TV, [7.30, 0.36])] + fetch(CUP, TV, [7.55, 0.36]))
             for case, cold, asset in (("cold_juice", "cold_juice", "juice_bottle"),
                                       ("cold_soda", "cold_soda", "soda_can"))},
            instruction="It's a hot day. A guest is sitting in the living room; bring him something to drink.",
            instruction_zh="天很热，客人在客厅坐着，给他拿点喝的。"),
        "drink_in_fridge": fam(
            "drink_on_island", ["storage_place", "not_in_view", "resource_absent"],
            "what drink the fridge holds (seed: the juice; or only a can of soda)",
            "a cup on the island, nothing to drink out; the juice (or, no juice, a can of soda) is in the fridge",
            "drinks are kept in the fridge: open it, take what there is to drink, close it",
            {case: dict(add={CUP: on("breakfast_cup", ISL, 7.55, 1.80), cold: {**in_fridge(cold), "asset": asset}},
                        watch=[cold, CUP], goal={"all": serve(cold) + [["is_closed", FR], H]},
                        route=[look(ISL), nav(FR), S("open", articulated=FR), nav(cold), pick(cold),
                               S("retreat", obstacle=FR, distance_m=0.3), S("close", articulated=FR), nav(TV),
                               place(cold, TV, [7.30, 0.36])] + fetch(CUP, TV, [7.55, 0.36]))
             for case, cold, asset in (("juice", "cold_juice", "juice_bottle"), ("soda_only", "cold_soda", "soda_can"))}),
        "cups_for_two": fam(
            "drink_on_island", ["count_from_scene", "item_put_away", "resource_absent", "dependent_decisions"],
            "how many cups already stand by the guests and how many the closed cabinet holds (seed: 1 + 1, 0 + 1, "
            "0 + 2, 2 + 1); the last two look the same until the door is open",
            "two guests; the juice on the island; by the guests none, one or two cups; in the low cabinet one or two "
            "cups; the house's only other cups are mugs in the dining room",
            "two decisions on what is found: what stands by the guests says how many cups are missing; what the "
            "cabinet holds says whether ordinary cups cover it or a mug from the dining room makes up the rest; "
            "exactly two cups in the end, the ones already there left where they are",
            {c: dict(add={J: on("juice_bottle", ISL, 7.30, 1.80),
                          **{f"tv_cup_{k + 1}": on("breakfast_cup", TV, x, 0.36) for k, x in enumerate((7.80, 8.05)[:n_tv])},
                          **{f"stock_cup_{k + 1}": on("breakfast_cup", f"{C4}/inside_shelf", x, 0.50)
                             for k, x in enumerate((1.25, 1.55)[:n_in])}},
                     remove=["cup_counter_b", "cup_kitchen_cabinet", "cup_side_table"],
                     watch=[J, *[f"tv_cup_{k + 1}" for k in range(n_tv)], *[f"stock_cup_{k + 1}" for k in range(n_in)]],
                     goal={"all": [["on", J, TV], ["upright", J]] + cups_goal(n_tv, n_in) + [["is_closed", C4], H]},
                     route=[look(TV)] + fetch(J, TV, [7.30, 0.36]) + cups_route(n_tv, n_in))
             for c, n_tv, n_in in (("one_there", 1, 1), ("none_one_inside", 0, 1), ("none_two_inside", 0, 2),
                                   ("two_there", 2, 1))},
            instruction="Two guests are sitting in the living room. Get the drink and the cups ready for them, one cup "
                        "each, ordinary cups where possible; what is already on their table need not be brought again.",
            instruction_zh="两位客人在客厅，给他们准备好饮料和杯子，每人一个杯子，尽量用普通杯子；桌上已有的不用重复拿。"),
        "two_guests": fam(
            "drink_on_island", ["count_from_scene", "multi_object_goal", "resource_absent"],
            "how many cups there are (seed: two on the island; or one, the house's other ordinary cups gone, mugs "
            "in the dining room)",
            "two guests; one bottle of juice and two cups on the island, or one cup and no other ordinary cup",
            "one cup per guest: both cups with the bottle; with one cup, a mug for the other guest",
            {"two_cups": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80), CUP: on("breakfast_cup", ISL, 7.55, 1.80),
                                   "guest_cup_2": on("breakfast_cup", ISL, 7.80, 1.80)},
                              watch=[J, CUP, "guest_cup_2"], goal={"all": serve(J, (CUP, "guest_cup_2"), 2) + [H]},
                              route=fetch(J, TV, [7.30, 0.36]) + fetch(CUP, TV, [7.55, 0.36])
                              + fetch("guest_cup_2", TV, [7.80, 0.36])),
             "one_cup": dict(add={J: on("juice_bottle", ISL, 7.30, 1.80), CUP: on("breakfast_cup", ISL, 7.55, 1.80)},
                             remove=PLAIN, watch=[J, CUP, *MUGS],
                             goal={"all": drink + [["count_on_at_least", [CUP] + MUGS, TV, 2], H]},
                             route=fetch(J, TV, [7.30, 0.36]) + fetch(CUP, TV, [7.55, 0.36])
                             + [S("search", object="mug_shelf", region="dining_room_0_1")]
                             + fetch("mug_shelf", TV, [7.80, 0.36]))},
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
# the top of the bookcase by bed 1 (bookcase_3/top, x 1.79..2.41, y -5.08..-4.68) covered with his books: three
# red books turned 90 deg along the front, three paperbacks behind, ~2 cm apart (no 10 x 16 cm spot left)
B3_TOP_BOOKS = {**{f"b3_book_{k + 1}": on("book_red", "bookcase_3/top", x, -4.80, 90.0)
                   for k, x in enumerate((1.903, 2.100, 2.297))},
                **{f"b3_paperback_{k + 1}": on("paperback_book", "bookcase_3/top", x, -5.00)
                   for k, x in enumerate((1.895, 2.100, 2.305))}}
# 11-17: bed_2 moved 0.6 m east and cell_shelf_2 into bedroom_0_0's south-west corner (tools/relocate_furniture.py,
# the room was closed off from its west door); the basket, the teddy and the cup spot below follow
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
    KIDS_CASE = [f"bookcase_{i}/{lv}" for i in (2, 3) for lv in ("top", "shelf_1", "shelf_0")]   # a bookcase in his room
    # 11-18 (user): every design gets a substitution seed (where things go in his room), per-seed tiers
    from itertools import product
    from benchmark.v6.scoring import LAYOUT_TIERS, cost_tiers
    LT = LAYOUT_TIERS.setdefault(("T26", "*"), {})
    B2 = [f"bookcase_2/{lv}" for lv in ("top", "shelf_1", "shelf_0")]
    B3 = [f"bookcase_3/{lv}" for lv in ("top", "shelf_1", "shelf_0")]
    ROOM_TOPS = [DESK3] + [f"large_shelf_4/shelf_{k}" for k in range(5)] + \
        [f"large_shelf_5/shelf_{k}" for k in range(4)]          # other furniture in his room
    basket = {BASK: floor("storage_basket", 0.89, -1.93)}
    nv_stays = [["near_start", nv, 0.03]]
    stays = lambda names: [["near_start", n, 0.03] for n in sorted(names)]  # noqa: E731

    def per_item(items, opts, faults=()):
        """each item its own options [(atoms(x), cost)], the costs added"""
        combos = product(*[[(f(x), c) for f, c in opts[x]] for x in items])
        return cost_tiers([([a for at, _ in cb for a in at], sum(c for _, c in cb)) for cb in combos], list(faults))

    # whose: his bookcase with room (ideal); or (capacity) bookcase_2 full on every level (T23's piles of his
    # books), his other bookcase by the bed has room; the grown-up's novel stays either way
    full_b2 = shelf_books([(lv, 2) for lv in B2])
    LT["whose__shelf_room"] = cost_tiers([([["on_any", kb, KIDS_CASE]], 0)], [(nv_stays, 2)])
    LT["whose__shelf_full"] = cost_tiers([([["on_any", kb, B3]], 0), ([["on_any", kb, ROOM_TOPS]], 1)],
                                         [(nv_stays, 2), (stays(full_b2), 1)])
    # scattered: the toy basket (ideal); or (absent) no basket, his small toy bin on his bookcase: the three in
    # the bin best; on his bookcase / other furniture in his room a step down each
    TB = "kids_toy_bin"
    toys = (CAR, "living_duck", "living_block")
    scat = {CAR: floor("toy_car", 4.36, 1.68), "living_duck": on("rubber_duck", TV, 7.00, 0.36),
            "living_block": on("wooden_block", ISL, 7.20, 1.80)}
    LT["scattered__basket"] = cost_tiers([([["inside", x, BASK] for x in toys], 0)])
    LT["scattered__no_basket"] = per_item(toys, {x: [(lambda y: [["inside", y, TB]], 0),
                                                     (lambda y: [["on_any", y, KIDS_CASE + ROOM_TOPS]], 1)]
                                                 for x in toys})
    # where_in_room: the car to the basket, the book to his bookcase (ideal); or (looks right, isn't) no toy
    # basket, a waste bin where it stood: the car onto his bookcase with his things, never into the bin
    WB = "kids_room_bin"
    LT["where_in_room__basket"] = per_item((CAR, kb), {
        CAR: [(lambda y: [["inside", y, BASK]], 0), (lambda y: [["on_any", y, KIDS_CASE]], 1)],
        kb: [(lambda y: [["on_any", y, KIDS_CASE]], 0), (lambda y: [["inside", y, BASK]], 1)]})
    LT["where_in_room__waste_bin"] = per_item((CAR, kb), {
        CAR: [(lambda y: [["on_any", y, KIDS_CASE]], 0), (lambda y: [["on_any", y, ROOM_TOPS]], 1),
              (lambda y: [["inside", y, WB]], 3)],
        kb: [(lambda y: [["on_any", y, KIDS_CASE]], 0), (lambda y: [["on_any", y, ROOM_TOPS]], 1),
             (lambda y: [["inside", y, WB]], 3)]})
    # bear_to_bed: the bedside bookcase's top free (ideal); or (taken) covered with his books: his bed, a lower
    # level of that bookcase or his other bookcase (11-19: all best -- the reference uses the other bookcase's
    # open top: the top-pinched bear set on a level with a board 12 cm above its head lifts the hand out into
    # that board, muqingj), the toy basket a step down
    BEAR = "living_bear"
    top_books = B3_TOP_BOOKS
    LT["bear_to_bed__top_free"] = cost_tiers([([["on_any", BEAR, ["mattress_1/top", "bookcase_3/top"]]], 0),
                                              ([["inside", BEAR, BASK]], 1)])
    LT["bear_to_bed__top_covered"] = cost_tiers(
        [([["on_any", BEAR, ["mattress_1/top", "bookcase_3/shelf_1", "bookcase_3/shelf_0", *B2]]], 0),
         ([["inside", BEAR, BASK]], 1)], [(stays(top_books), 1)])
    fams = {
        "whose": fam(
            "car_in_living_room", ["referent_clue", "storage_place"],
            "how full his bookcase is (seed: room; or every level of it full of his books, his other bookcase by "
            "the bed with room)",
            "a picture book like the ones on the kid's bookcase and a grown-up's novel on the TV stand; his "
            "bookcase may be full",
            "only the kid's things go: the picture book to his bookcase -- the other one by his bed when it is "
            "full -- the novel stays",
            {"shelf_room": dict(add={kb: on("book_blue", TV, 7.20, 0.36), nv: on("paperback_book", TV, 7.80, 0.36),
                                     **room},
                                watch=[kb, nv], goal={"all": [["on_any", kb, KIDS_CASE], *nv_stays, H]},
                                route=[look(TV)] + fetch(kb, "bookcase_2/top", [1.12, -0.43])),
             "shelf_full": dict(add={kb: on("book_blue", TV, 7.20, 0.36), nv: on("paperback_book", TV, 7.80, 0.36),
                                     **basket, **full_b2},
                                watch=[kb, nv, *full_b2],
                                goal={"all": [["on_any", kb, B3 + ROOM_TOPS], *nv_stays, H]},
                                route=[look(TV), nav(kb), pick(kb), nav("bookcase_2/top"), look("bookcase_2/top"),
                                       nav("bookcase_3/top"), place(kb, "bookcase_3/top", [2.10, -4.78])])}),
        "scattered": fam(
            "car_in_living_room", ["goal_items_unstated", "multi_object_goal", "container_absent"],
            "what holds his toys (seed: the toy basket on his floor; or no basket, his small toy bin on his "
            "bookcase)",
            "the car on the floor, the duck on the TV stand, a block on the island; his toys kept in the basket, or "
            "(no basket) in a small bin",
            "everything of his in the living room, not only the first thing seen, into what holds his toys",
            {"basket": dict(add={**scat, **room}, watch=[*toys, BASK],
                            goal={"all": [["inside", x, BASK] for x in toys] + [H]},
                            route=[S("explore_room", room="living_room_0_0")] + into(CAR, BASK)
                            + into("living_duck", BASK) + into("living_block", BASK)),
             "no_basket": dict(add={**scat, TB: on("small_storage_bin", "bookcase_2/top", 1.00, -0.43)},
                               watch=[*toys, TB],
                               goal={"all": [["on_any", x, KIDS_CASE + ROOM_TOPS] for x in toys]
                                     + [["not on_floor", x] for x in toys] + [H]},
                               route=[S("explore_room", room="living_room_0_0")] + into(CAR, TB)
                               + into("living_duck", TB) + into("living_block", TB))}),
        "where_in_room": fam(
            "car_in_living_room", ["storage_place", "multi_object_goal", "container_absent"],
            "what stands on his floor (seed: the toy basket; or no basket, a waste bin there)",
            "the car and one of his picture books in the living room; in his room the toy basket, or only a waste "
            "bin on the floor",
            "in his room each by kind: the car into the toy basket -- or, with no basket, onto his bookcase, not "
            "into the waste bin -- the book onto his bookcase",
            # the book turned 90 deg, its 20 cm side to the stand's front edge: along its 14 cm side it could
            # hang over by 5.5 cm with its centre 1.5 cm on the top -- just short (slide to edge, 11-15)
            {"basket": dict(add={CAR: floor("toy_car", 4.36, 1.68), kb: on("book_blue", TV, 7.20, 0.36, 90.0), **room},
                            watch=[CAR, kb, BASK],
                            goal={"all": [["inside", CAR, BASK], ["on_any", kb, KIDS_CASE], H]},
                            route=[S("explore_room", room="living_room_0_0")] + into(CAR, BASK)
                            + fetch(kb, "bookcase_2/top", [1.12, -0.43])),
             "waste_bin": dict(add={CAR: floor("toy_car", 4.36, 1.68), kb: on("book_blue", TV, 7.20, 0.36, 90.0),
                                    WB: floor("trash_can", 0.89, -1.93),
                                    "kids_shelf_book": on("book_blue", "bookcase_2/top", 0.90, -0.43)},
                               watch=[CAR, kb, WB],
                               goal={"all": [["on_any", x, KIDS_CASE + ROOM_TOPS] for x in (CAR, kb)] + [H]},
                               route=[S("explore_room", room="living_room_0_0"), nav(CAR), pick(CAR), nav(WB),
                                      look(WB), nav("bookcase_2/top"), place(CAR, "bookcase_2/top", [1.15, -0.43])]
                               + fetch(kb, "bookcase_3/top", [2.10, -4.78]))}),
        "bear_to_bed": fam(
            "car_in_living_room", ["storage_place"],
            "how the bedside bookcase's top is (seed: free; or covered with his books)",
            "his teddy bear on the TV stand; it is bedtime; the top of the bookcase by his bed free or covered",
            "at bedtime the bear goes to his bed or the bookcase by it -- when its top is covered, elsewhere on "
            "his bookcases (his other bookcase's top), the books left -- not into the toy basket",
            {"top_free": dict(add={BEAR: on("teddy_bear", TV, 7.40, 0.36), **room}, watch=[BEAR, BASK],
                              goal={"all": [["on_any", BEAR, ["mattress_1/top", "bookcase_3/top"]], H]},
                              # the reference sets it on his bookcase: the bed frame keeps the base 0.70 m from
                              # the mattress's top, out of the arm's reach
                              route=[look(TV)] + fetch(BEAR, "bookcase_3/top", [2.10, -4.78])),
             "top_covered": dict(add={BEAR: on("teddy_bear", TV, 7.40, 0.36), **room, **top_books},
                                 watch=[BEAR, BASK, *top_books],
                                 goal={"all": [["on_any", BEAR, ["mattress_1/top", *B3, *B2]], H]},
                                 route=[look(TV), nav(BEAR), pick(BEAR), nav("bookcase_3/top"),
                                        look("bookcase_3/top"), nav("bookcase_2/top"),
                                        place(BEAR, "bookcase_2/top", [1.12, -0.43])])},
            instruction="The kid is going to bed. Take the things he left in the living room back to his room.",
            instruction_zh="孩子要睡觉了，把他落在客厅的东西拿回他房间。"),
        "two_bedrooms": fam(
            "car_in_living_room", ["referent_clue", "not_in_view"], "which bedroom is his (seed: where his toy basket is)",
            "two bedrooms; his is the one with the toy basket",
            "tell his room by his things in it and take the car there",
            {c: dict(add={CAR: floor("toy_car", 4.36, 1.68), BASK: floor("storage_basket", *xy)},
                     watch=[CAR, BASK], route=[nav(CAR), pick(CAR), S("search", object=BASK, region=r), nav(BASK),
                                                place(CAR, BASK)])
             for c, xy, r in (("room_east", (0.89, -1.93), "bedroom_0_1"), ("room_south", (5.25, -9.80), "bedroom_0_0"))}),
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
    # with a second thing on the table the edge search pushed the box 0.5 m west and the hand jammed on its rim;
    # 15 cm east the east edge is the short push (the one that works in rice_on_table)
    rice_east = {R: on("glass_food_container", T2, 3.45, 6.70)}
    # 11-18 (user): every design with a substitution.  two_leftovers + soup_at_seat: the soup pot at a place
    # where someone is still eating from a bowl (in use): only the rice; fridge_out_of_view + fridge_crowded: the
    # left of the fridge shelf full of stored lunch boxes and juice (taken): the rice in the free right part
    from benchmark.v6.scoring import LAYOUT_TIERS, cost_tiers
    LT = LAYOUT_TIERS.setdefault(("T27", "*"), {})
    SOUP_P, closed = "leftover_soup", [["is_closed", FR]]
    STORED = {**{f"stored_box_{k + 1}": on("steel_lunch_box", FS, x, y, 90.0)
                 for k, (x, y) in enumerate([(5.695, 3.14), (5.815, 3.14), (5.695, 3.31), (5.815, 3.31)])},
              **{f"stored_juice_{k + 1}": on("juice_bottle", FS, x, 3.48) for k, x in enumerate((5.69, 5.82))}}
    seat = {"eating_bowl": on("oatmeal_bowl", T2, 3.05, 7.30), "eating_spoon": on("breakfast_spoon", T2, 3.05, 7.49)}
    both_in = [["on", R, FS], ["on", SOUP_P, FS], ["upright", SOUP_P]]
    for c in ("soup_on_table", "soup_on_stove"):
        LT[f"two_leftovers__{c}"] = cost_tiers([(both_in, 0)], [(closed, 1)])
    LT["two_leftovers__soup_at_seat"] = cost_tiers(
        [([["on", R, FS], ["near_start", SOUP_P, 0.03], ["near_start", "eating_bowl", 0.03]], 0),
         ([["on", R, FS]], 2)], [(closed, 1)])
    LT["fridge_out_of_view__fridge_free"] = cost_tiers([([["on", R, FS]], 0)], [(closed, 1)])
    LT["fridge_out_of_view__fridge_crowded"] = cost_tiers(
        [([["on", R, FS]], 0)], [(closed, 1), ([["near_start", n, 0.03] for n in sorted(STORED)], 1)])
    fams = {
        "which_is_leftover": fam(
            "rice_on_table", ["disposal_by_state"], "the seed's layout only",
            "the box of rice and an empty takeout tray on the table",
            "only food goes into the fridge: the empty tray does not",
            {"": dict(add={**rice, "empty_tray": on("foil_takeout_tray", T2, 3.25, 7.30)}, watch=[R, "empty_tray"],
                      goal={"all": rg + [["not on", "empty_tray", FS], H]}, route=[look(T2)] + fridge([R]))}),
        "two_leftovers": fam(
            "rice_on_table", ["goal_items_unstated", "multi_object_goal"],
            "where the soup is (seed: on the table, or still in its pot on the stove -- leftovers; or on the "
            "table where someone is still eating from a bowl -- in use)",
            "the box of rice on the table, and a pot of soup: left over on the table or the stove, or still being "
            "eaten from at a place",
            "all the leftovers, not only the first one seen: both into the fridge -- unless someone is still eating "
            "the soup, then only the rice",
            {"soup_at_seat": dict(add={**rice_east, SOUP_P: on("soup_pot", T2, 3.35, 7.40), **seat},
                                  watch=[R, SOUP_P, "eating_bowl"],
                                  goal={"all": rg + [["near_start", SOUP_P, 0.03], ["near_start", "eating_bowl", 0.03], H]},
                                  route=[look(T2)] + fridge([R])),
             **{c: dict(add={**(rice_east if "table" in c else rice), "leftover_soup": on("soup_pot", sup, *xy)}, watch=[R, "leftover_soup"],
                     goal={"all": rg + [["on", "leftover_soup", FS], ["upright", "leftover_soup"], H]},
                     route=[look(T2)] + ([look("kitchen_stove/top")] if "stove" in sup else []) + fridge([R, "leftover_soup"], spots=((5.90, 3.46), (5.90, 3.20))))   # the pot (30 cm with handles) does not fit beside the box: the flat box at the back, the pot in front
             for c, sup, xy in (("soup_on_table", T2, (3.35, 6.05)), ("soup_on_stove", "kitchen_stove/top", (8.41, 1.725)))}}),
        "still_eating": fam(
            "rice_on_table", ["referent_clue"], "the seed's layout only",
            "the box of rice, and a bowl of oatmeal with a spoon in front of a seat: someone is still eating",
            "a portion someone is still eating is not a leftover: only the rice",
            {"": dict(add={**rice_east, "eating_bowl": on("oatmeal_bowl", T2, 3.05, 7.30),
                           "eating_spoon": on("breakfast_spoon", T2, 3.05, 7.49)},
                      watch=[R, "eating_bowl"], goal={"all": rg + [["near_start", "eating_bowl", 0.03], ["never_picked", ["eating_bowl"]], H]},
                      route=[look(T2)] + fridge([R]))}),
        "fridge_out_of_view": fam(
            "rice_on_table", ["not_in_view", "storage_place"],
            "how full the fridge shelf is (seed: free; or its left part packed with stored lunch boxes and juice)",
            "the robot starts in the dining room; the fridge stands in the open kitchen, out of view; its shelf "
            "free, or half taken by what is stored there",
            "find the fridge first, then put the rice in -- in the part of the shelf that is free, the stored food "
            "left as it is",
            {"fridge_free": dict(add=rice, start=[3.80, 4.90, 180.0],
                                 route=[look(T2), S("explore_room", room="living_room_0_0")] + fridge([R])),
             "fridge_crowded": dict(add={**rice, **STORED}, start=[3.80, 4.90, 180.0], watch=[R, *STORED],
                                    goal={"all": rg + [H]},
                                    route=[look(T2), S("explore_room", room="living_room_0_0")]
                                    + fridge([R], spots=((6.05, 3.30),)))}),
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
    # 11-18 (user): every design with a substitution.  where_his_cup_is + no_kid_cup: no plastic cup in the
    # house, a china cup and a mug on the counter (absent): a cup of the house; cup_out_of_view + side_covered:
    # the bookcase top by his bed covered with books (taken): a lower level of it or the desk (11-19: the
    # reference uses the desk -- a rim-pinched cup set on a level with a board above lifts the hand out into it,
    # muqingj); already_there +
    # wrong_cup: a china cup by his bed, his plastic cup on the counter (looks right, isn't): bring his
    from benchmark.v6.scoring import LAYOUT_TIERS, cost_tiers
    LT = LAYOUT_TIERS.setdefault(("T28", "*"), {})
    OTHER = ["cup_counter_b", "counter_mug"]
    at_side = lambda x, where=SIDES: [["on_any", x, where], ["upright", x]]  # noqa: E731
    stay_cnt = [["near_start", n, 0.03] for n in OTHER]
    LT["where_his_cup_is__on_counter"] = cost_tiers([(at_side(KC), 0)] + [(at_side(x), 2) for x in OTHER],
                                                    [(stay_cnt, 1)])
    LT["where_his_cup_is__in_cabinet"] = cost_tiers([(at_side(KC), 0)] + [(at_side(x), 2) for x in OTHER],
                                                    [(stay_cnt, 1), ([["is_closed", C4]], 1)])
    LT["where_his_cup_is__no_kid_cup"] = cost_tiers([(at_side(x), 0) for x in OTHER + HOUSE_CUPS[1:3]],
                                                    [([["is_closed", C4]], 1)])
    LOWER = ["bookcase_3/shelf_1", "bookcase_3/shelf_0", "desk_1/top"]
    LT["cup_out_of_view__cup_found"] = cost_tiers([(at_side(KC), 0)])
    LT["cup_out_of_view__side_covered"] = cost_tiers(
        [(at_side(KC, LOWER), 0)], [([["near_start", n, 0.03] for n in sorted(B3_TOP_BOOKS)], 1)])
    fams = {
        "which_bed": fam(
            "cup_on_counter", ["referent_clue"], "which bed is his (seed: the teddy bear on one of the two beds)",
            "two bedrooms with a bed each; his teddy bear lies on his",
            "his bed is the one with his bear: the cup goes next to that bed",
            {"east": dict(add={KC: on("plastic_cup", COUNTER, -0.20, 7.60), **BEAR},
                          route=[nav(KC), pick(KC), look("mattress_2/top"), nav(side), place(KC, side, [2.10, -4.88])]),
             "south": dict(add={KC: on("plastic_cup", COUNTER, -0.20, 7.60),
                                "bed_bear": on("teddy_bear", "mattress_2/top", 3.90, -9.80)},
                           goal={"all": [["on", KC, "cell_shelf_2/top"], ["upright", KC], H]},
                           route=[nav(KC), pick(KC), look("mattress_1/top"), nav("cell_shelf_2/top"),
                                  place(KC, "cell_shelf_2/top", [1.30, -11.90])])}),
        "where_his_cup_is": fam(
            "cup_on_counter", ["referent_clue", "item_put_away", "dependent_decisions", "resource_absent"],
            "whether his cup is on the counter among the others or put away in the low cabinet (seed)",
            "on the counter a china cup and a mug, and his plastic cup with them, or not (then it is in the low "
            "cabinet)",
            "what the counter shows decides the rest: his plastic cup there -> bring it; only cups that are not his "
            "-> not any cup will do, his was put away: open the cabinet, take it, close the door",
            {"on_counter": dict(add={KC: on("plastic_cup", COUNTER, -0.20, 7.60),
                                     "counter_mug": on("breakfast_mug", COUNTER, -0.30, 9.00), **BEAR},
                                watch=[KC, "cup_counter_b", "counter_mug"],
                                goal={"all": [["on_any", KC, SIDES], ["upright", KC], ["near_start", "cup_counter_b", 0.03],
                                              ["near_start", "counter_mug", 0.03], H]},
                                route=[look(COUNTER)] + to_side),
             "in_cabinet": dict(add={KC: on("plastic_cup", f"{C4}/inside_shelf", 1.40, 0.42),
                                     "counter_mug": on("breakfast_mug", COUNTER, -0.30, 9.00), **BEAR},
                                watch=[KC, "cup_counter_b", "counter_mug"],
                                goal={"all": [["on_any", KC, SIDES], ["upright", KC], ["near_start", "cup_counter_b", 0.03],
                                              ["near_start", "counter_mug", 0.03], ["is_closed", C4], H]},
                                route=[look(COUNTER)] + explore(C4) + from_closed(KC, C4)
                                + [nav(side), place(KC, side, [2.10, -4.88])]),
             "no_kid_cup": dict(add={"counter_mug": on("breakfast_mug", COUNTER, -0.30, 9.00), **BEAR},
                                watch=["cup_counter_b", "counter_mug"],
                                goal={"all": [["count_on_at_least", OTHER + HOUSE_CUPS[1:3], side, 1]]
                                      + [["is_closed", C4], H]},
                                route=[look(COUNTER)] + explore(C4) + [S("close", articulated=C4)]
                                + fetch("cup_counter_b", side, [2.10, -4.88]))}),
        "cup_out_of_view": fam(
            "cup_on_counter", ["not_in_view", "storage_place"],
            "how the top by his bed is (seed: free; or covered with his books)",
            "the cup was left on the dining table, out of view; the bookcase top by his bed free or covered",
            "find the cup first; by his bed -- on the desk or a lower level of that bookcase when its top is "
            "covered, the books left",
            {"cup_found": dict(add={KC: on("plastic_cup", T2, 3.30, 6.70), **BEAR},
                               route=[look(COUNTER), S("search", object=KC, region="dining_room_0_1")] + to_side),
             "side_covered": dict(add={KC: on("plastic_cup", T2, 3.30, 6.70), **BEAR, **B3_TOP_BOOKS},
                                  watch=[KC, *B3_TOP_BOOKS],
                                  goal={"all": at_side(KC, LOWER) + [H]},
                                  route=[look(COUNTER), S("search", object=KC, region="dining_room_0_1"), nav(KC),
                                         pick(KC), nav(side), look(side), nav("desk_1/top"),
                                         place(KC, "desk_1/top", [-0.35, -5.95])])}),
        "already_there": fam(
            "cup_on_counter", ["goal_already_met", "referent_clue"],
            "what cup stands by his bed (seed: his plastic cup; or a china cup, his still on the counter)",
            "a cup already stands by his bed: his own, or a china one that is not his",
            "his cup already there: check and leave it; a cup that is not his does not count: bring his",
            {"his_cup": dict(add={KC: on("plastic_cup", side, 2.10, -4.88), **BEAR},
                             goal={"all": [["on_any", KC, SIDES], ["near_start", KC, 0.03], H]},
                             route=[nav(side), look(side)]),
             "wrong_cup": dict(add={"bedside_cup": on("breakfast_cup", side, 2.28, -4.88),
                                    KC: on("plastic_cup", COUNTER, -0.20, 7.60), **BEAR},
                               watch=[KC, "bedside_cup"],
                               goal={"all": [["on_any", KC, SIDES], ["upright", KC], ["near_start", "bedside_cup", 0.03], H]},
                               route=[nav(side), look(side)] + fetch(KC, side, [2.00, -4.88]))}),
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
    shelves = [f"bookcase_{i}/{lv}" for i in (1, 2, 3, 4) for lv in ("top", "shelf_1", "shelf_0")] + \
        [f"large_shelf_2/shelf_{k}" for k in range(4)]                      # a book goes on any bookshelf
    # 11-18 (user): every design with a substitution.  belongs_on_table + no_toy_box: no toy box, a sorting
    # tray on the TV stand (absent); homework_on_table + desk_covered: the study desk covered with someone's
    # books (taken): the kid's own desk in the bedroom or his bookcase; several + bin_full: no toy box, his small
    # toy bin full, a tray beside it (capacity)
    from benchmark.v6.scoring import LAYOUT_TIERS, cost_tiers
    LT = LAYOUT_TIERS.setdefault(("T29", "*"), {})
    TRAY29 = "spare_tray"
    tray29 = {TRAY29: on("shallow_sorting_tray", TV, 7.80, 0.36)}
    # 11-20: the spread's own pencil renamed -- it was called hw_pencil like the kid's pencil, so it replaced the
    # kid's (which then started on the study desk) and the best tier asked for that pencil both moved and left
    DESK_FULL = {**{("desk_pencil" if k == "hw_pencil" else k): v for k, v in HOMEWORK_SPREAD.items()},
                 "hw_notebook_corner": on("notebook", DESK, -0.138, -6.245)}
    HW = ["hw_notebook", "hw_pencil"]
    KIDS_SPOTS = [DESK3] + [f"bookcase_2/{lv}" for lv in ("top", "shelf_1", "shelf_0")]
    off_t = lambda x: [["not on", x, T2], ["not on_floor", x]]  # noqa: E731
    LT["homework_on_table__desk_free"] = cost_tiers([([["on", x, DESK] for x in HW], 0),
                                                     ([a for x in HW for a in off_t(x)], 2)])
    LT["homework_on_table__desk_covered"] = cost_tiers(
        [([["on_any", x, KIDS_SPOTS] for x in HW], 0), ([["on", x, DESK] for x in HW], 1),
         ([a for x in HW for a in off_t(x)], 2)], [([["near_start", n, 0.03] for n in sorted(DESK_FULL)], 1)])
    fams = {
        "belongs_on_table": fam(
            "car_on_table", ["category_rule", "container_absent"],
            "what holds the toys (seed: the toy box; or no toy box, a sorting tray on the TV stand)",
            "the toy car, and a bowl and a spoon set for the meal; the toy box in the living room, or none",
            "what is set for the meal stays; only the toy goes -- into the toy box, or the tray when there is none",
            {"": dict(add={TC: on("toy_car", T2, 3.30, 6.70), **tb, **setting}, watch=[TC, "set_bowl", "set_spoon"],
                      goal={"all": [["inside", TC, BOX]] + keep + [H]}, route=[look(T2)] + into(TC, BOX)),
             "no_toy_box": dict(add={TC: on("toy_car", T2, 3.30, 6.70), **tray29, **setting},
                                watch=[TC, "set_bowl", "set_spoon", TRAY29],
                                goal={"all": [["inside", TC, TRAY29]] + keep + [H]},
                                route=[look(T2), nav(TC), pick(TC), S("explore_room", room="living_room_0_0"),
                                       nav(TRAY29), place(TC, TRAY29)])}),
        "homework_on_table": fam(
            "car_on_table", ["storage_place", "multi_object_goal"],
            "how the study desk is (seed: free; or covered with someone's books)",
            "the kid's notebook and pencil on the dining table; the study desk free, or covered with books",
            "homework goes back to a desk, not just off the table: the study desk, or -- covered -- his own desk "
            "in the bedroom (or his bookcase), the books left",
            {"desk_free": dict(add={"hw_notebook": on("notebook", T2, 3.30, 6.30),
                                    "hw_pencil": on("pencil", T2, 3.55, 6.30, 90.0)},
                               watch=HW, goal={"all": [["on", x, DESK] for x in HW] + [H]},
                               route=[look(T2)] + fetch("hw_notebook", DESK, [-0.70, -5.95])
                               + fetch("hw_pencil", DESK, [-0.35, -5.95])),
             "desk_covered": dict(add={"hw_notebook": on("notebook", T2, 3.30, 6.30),
                                       "hw_pencil": on("pencil", T2, 3.55, 6.30, 90.0), **DESK_FULL},
                                  watch=[*HW, *DESK_FULL],
                                  goal={"all": [["on_any", x, KIDS_SPOTS + [DESK]] for x in HW] + [H]},
                                  route=[look(T2), nav("hw_notebook"), pick("hw_notebook"), nav(DESK), look(DESK),
                                         nav(DESK3), place("hw_notebook", DESK3, [6.20, -5.50])]
                                  + fetch("hw_pencil", DESK3, [6.50, -5.50]))}),
        "several": fam(
            "car_on_table", ["category_rule", "multi_object_goal", "storage_place"],
            "what holds the toys (seed: the toy box; or no toy box, his small toy bin full, a tray beside it)",
            "the toy car, a paperback and an empty soda can on the table; the toy box, or only a full toy bin",
            "each to its place: the toy to the toy box (the tray beside the full bin), the book to a bookshelf, the "
            "empty can into the bin",
            {"toy_box": dict(add={TC: on("toy_car", T2, 3.30, 6.70), "table_book": on("paperback_book", T2, 3.30, 7.20),
                                  "empty_can": on("soda_can", T2, 3.30, 6.20), **tb},
                             watch=[TC, "table_book", "empty_can"],
                             goal={"all": [["inside", TC, BOX], ["inside", "empty_can", "trash_can"], H],
                                   "any": [[["on", "table_book", s]] for s in shelves]},
                             route=[look(T2)] + into(TC, BOX) + [nav("empty_can"), pick("empty_can"), nav("trash_can"),
                                                                 S("drop", object="empty_can", container="trash_can")]
                             + fetch("table_book", "bookcase_2/top", [1.00, -0.43])),
             "bin_full": dict(add={TC: on("toy_car", T2, 3.30, 6.70), "table_book": on("paperback_book", T2, 3.30, 7.20),
                                   "empty_can": on("soda_can", T2, 3.30, 6.20),
                                   **toy_bin_full("toy_bin", TV_Z, 7.30, 0.36), **tray29},
                              watch=[TC, "table_book", "empty_can", "toy_bin", TRAY29],
                              goal={"all": [["inside", TC, TRAY29], ["inside", "empty_can", "trash_can"], H]
                                    + [["fully_inside", f"bin_block_{i}", "toy_bin"] for i in range(1, 25)],
                                    "any": [[["on", "table_book", s]] for s in shelves]},
                              route=[look(T2), nav(TC), pick(TC), S("explore_room", room="living_room_0_0"),
                                     nav("toy_bin"), S("measure", object="toy_bin"), place(TC, TRAY29)]
                              + [nav("empty_can"), pick("empty_can"), nav("trash_can"),
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
    spoons3 = {f"seat_spoon_{i + 1}": on("breakfast_spoon", T2, 3.05, y) for i, y in enumerate((5.90, 6.70, 7.50))}
    fams = {
        "how_many": fam(
            "bowl_on_cabinet", ["count_from_scene", "multi_object_goal", "resource_absent"],
            "how many bowls there are (seed: three; or two and a mug)",
            "three spoons laid out at the dining table; three clean bowls on the cabinet, or two and a mug (the "
            "house has no other bowl)",
            "as many bowls as places at the table: three -- with two bowls, the mug for the third",
            {"three_bowls": dict(add={**SOUP, **{f"soup_bowl_{i + 1}": on("breakfast_bowl", top6, x, 0.36)
                                                 for i, x in enumerate((3.29, 3.50, 3.71))}, **spoons3},
                                 remove=["clutter_cereal_a", "clutter_cereal_b"],
                                 watch=["soup_bowl_1", "soup_bowl_2", "soup_bowl_3"],
                                 goal={"all": [bowls("soup_bowl_1", "soup_bowl_2", "soup_bowl_3", n=3), H]},
                                 route=[look(T2)] + fetch("soup_bowl_1", ISL, [7.65, 1.75])
                                 + fetch("soup_bowl_2", ISL, [7.85, 1.75]) + fetch("soup_bowl_3", ISL, [8.05, 1.75])),
             # 11-18 (user): only two bowls in the house and a mug beside them (absent): the mug for the third
             "two_bowls": dict(add={**SOUP, "soup_bowl_1": on("breakfast_bowl", top6, 3.29, 0.36),
                                    "soup_bowl_2": on("breakfast_bowl", top6, 3.50, 0.36),
                                    "spare_mug": on("breakfast_mug", top6, 3.71, 0.36), **spoons3},
                               remove=["clutter_cereal_a", "clutter_cereal_b", "plate_inside_kitchen_cabinet", *HOUSE_BOWLS],
                               watch=["soup_bowl_1", "soup_bowl_2", "spare_mug"],
                               goal={"all": [["count_on_at_least", ["soup_bowl_1", "soup_bowl_2"], ISL, 2],
                                             ["count_on_at_least", ["soup_bowl_1", "soup_bowl_2", "spare_mug"] + HOUSE_CUPS,
                                              ISL, 3], H]},
                               route=[look(T2)] + fetch("soup_bowl_1", ISL, [7.65, 1.75])
                               + fetch("soup_bowl_2", ISL, [7.85, 1.75]) + fetch("spare_mug", ISL, [8.05, 1.75]))},
            instruction="The soup is almost ready. Bring bowls over for serving it.",
            instruction_zh="汤快好了，拿碗过来准备盛。"),
        "bowls_in_cabinet": fam(
            "bowl_on_cabinet", ["count_from_scene", "item_put_away", "resource_absent", "dependent_decisions"],
            "how many bowls the cabinet holds (seed: two or one): seen only when its door is open",
            "three spoons laid out at the dining table; one bowl and a mug on the low cabinet; inside it two more "
            "bowls, or only one; the house has no other bowl",
            "three places, so three bowls; one is out, so open the cabinet; what is inside decides the rest: two "
            "bowls -> three bowls; one bowl -> two bowls and the mug for the third (a mug holds soup, a plate would not)",
            {c: dict(add={**SOUP, B1: on("breakfast_bowl", top6, 3.35, 0.36), "spare_mug": on("breakfast_mug", top6, 3.65, 0.36),
                          **{f"soup_bowl_{k + 2}": on("breakfast_bowl", f"{C6}/inside_shelf", x, 0.36)
                             for k, x in enumerate((3.36, 3.63)[:n])},
                          **{f"seat_spoon_{i + 1}": on("breakfast_spoon", T2, 3.05, y) for i, y in enumerate((5.90, 6.70, 7.50))}},
                     remove=["clutter_cereal_a", "clutter_cereal_b", "plate_inside_kitchen_cabinet", *HOUSE_BOWLS],
                     watch=[B1, "spare_mug", *[f"soup_bowl_{k + 2}" for k in range(n)]],
                     goal={"all": ([["count_on_at_least", [B1, "soup_bowl_2", "soup_bowl_3"], ISL, 3]] if n == 2 else
                                   [["count_on_at_least", [B1, "soup_bowl_2"], ISL, 2],
                                    ["count_on_at_least", [B1, "soup_bowl_2", "spare_mug"] + HOUSE_CUPS, ISL, 3]])
                           + [["is_closed", C6], H]},
                     route=[look(T2)] + fetch(B1, ISL, [7.65, 1.75]) + explore(C6)
                     + ([nav("soup_bowl_2"), pick("soup_bowl_2"), nav(ISL), place("soup_bowl_2", ISL, [7.85, 1.75])]
                        + from_closed("soup_bowl_3", C6) + [nav(ISL), place("soup_bowl_3", ISL, [8.05, 1.75])]
                        if n == 2 else
                        from_closed("soup_bowl_2", C6) + [nav(ISL), place("soup_bowl_2", ISL, [7.85, 1.75])]
                        + fetch("spare_mug", ISL, [8.05, 1.75])))
             for c, n in (("two_inside", 2), ("one_inside", 1))},
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
            "bowl_on_cabinet", ["item_put_away", "resource_absent"],
            "what the low cabinet holds (seed: a bowl; or, no bowl in the house, a plate and a mug)",
            "no bowl out; the low cabinet holds the clean bowl, or only a plate and a mug",
            "look in the cabinet, take a bowl -- or the mug, which holds soup, not the plate -- close the door",
            {"bowl_inside": dict(add={**SOUP, B1: on("breakfast_bowl", f"{C4}/inside_shelf", 1.40, 0.42)},
                                 goal={"all": [bowls(B1), ["is_closed", C4], H]},
                                 route=explore(C4) + from_closed(B1, C4) + [nav(ISL), place(B1, ISL, [8.05, 1.75])]),
             "mug_inside": dict(add={**SOUP, "stored_mug": on("breakfast_mug", f"{C4}/inside_shelf", 1.40, 0.42),
                                     "stored_plate": on("breakfast_plate", f"{C4}/inside_shelf", 1.20, 0.42)},
                                remove=["bowl_dining_cabinet", "bowl_kitchen_cabinet", "bowl_side_table",
                                        "bowl_inside_kitchen_cabinet"],
                                watch=["stored_mug", "stored_plate"],
                                goal={"all": [["count_on_at_least", ["stored_mug"] + HOUSE_CUPS, ISL, 1],
                                              ["is_closed", C4], H]},
                                route=explore(C4) + from_closed("stored_mug", C4)
                                + [nav(ISL), place("stored_mug", ISL, [8.05, 1.75])])}),
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


# ================================================================== T15 cover the pot (11-17: replaces T15 book_face_up)
# the instruction names the lid; the B variants make it unusable (absent, in use on the other pot) and a plate from
# the counter covers the pot instead (the cover skill sets any held object centred on the rim)
def t15():
    POT, LID, STOVE = "handled_cooking_pot", "pot_lid", "kitchen_stove/top"
    PLATES = ["plate_counter_a", "plate_counter_b"]
    cover = lambda lid: [nav(POT), S("cover", container=POT, lid=lid)]  # noqa: E731
    ctl = {"note": "the pot on the left burner, its lid on the island beside the stove",
           "move": {LID: P(ISL, 8.05, 1.80)}}
    t = base_task("T15_cover_the_pot", "ZB-T15", "The soup will sit a while before we eat. Cover the pot of soup on "
                  "the stove with its lid.", "汤要放一会儿再吃，用锅盖把灶台上的汤锅盖好。", "lid_by_pot", ctl,
                  {"all": [["covered", POT, LID], H]}, [look(STOVE), nav(LID), pick(LID)] + cover(LID), [POT, LID])
    by_plate = {"any": [[["covered", POT, p]] for p in PLATES], "all": [H]}
    plate_route = [look(STOVE), look(ISL), S("search", object=PLATES[0], region="kitchen_0_1"), nav(PLATES[0]),
                   pick(PLATES[0])] + cover(PLATES[0])
    STEW = "stew_pot"
    fams = {
        # 11-17 (user): the seed changes what the lid is doing -- left free on the dining table (find it, ideal), or
        # there but covering someone's unfinished bowl of oatmeal (a spoon beside it): leave it, cover with a plate
        "lid_elsewhere": fam(
            "lid_by_pot", ["not_in_view"], "what the lid is doing (seed: left on the dining table; or covering "
            "someone's unfinished bowl there, plates on the kitchen counter)",
            "the lid is not by the stove: it lies on the dining table, out of view -- free, or covering a bowl of "
            "oatmeal someone has not finished",
            "find the lid; when it is free cover the pot with it, when it covers someone's food leave it and use a "
            "plate",
            {"dining": dict(move={LID: P(T2, 3.70, 6.30)}, goal={"all": [["covered", POT, LID], H]}, watch=[POT, LID],
                            route=[look(STOVE), look(ISL), S("search", object=LID, region="dining_room_0_1"),
                                   nav(LID), pick(LID)] + cover(LID)),
             "covering_bowl": dict(
                 add={"covered_bowl": on("oatmeal_bowl", T2, 3.70, 6.30),
                      "bowl_spoon": on("breakfast_spoon", T2, 3.70, 6.52)},
                 move={LID: {"support": None, "z": 0.94, "xy": [3.70, 6.30], "yaw_deg": 0.0}},
                 goal={"any": by_plate["any"], "all": [["near_start", LID, 0.03], ["near_start", "covered_bowl", 0.03],
                                                       H]},
                 watch=[POT, LID, "covered_bowl", *PLATES],
                 route=[look(STOVE), look(ISL), S("search", object=LID, region="dining_room_0_1"), look(LID),
                        S("search", object=PLATES[0], region="kitchen_0_1"), nav(PLATES[0]), pick(PLATES[0])]
                 + cover(PLATES[0]))}),
        "no_lid": fam(
            "lid_by_pot", ["resource_absent", "not_in_view"], "the layout only",
            "there is no pot lid in the house; plates stand on the kitchen counter; a book lies on the island",
            "the lid does not exist: a plate wider than the pot's rim covers it as well (moderate); the book is no "
            "cover for food (bad)",
            {"": dict(remove=[LID], add={"cover_book": on("book_blue", ISL, 8.05, 1.80)}, goal=by_plate,
                      watch=[POT, "cover_book", *PLATES], route=plate_route)}),
        "lid_in_use": fam(
            "lid_by_pot", ["resource_in_use", "not_in_view"], "the layout only",
            "the lid is on the other pot (a stew on the right burner); plates stand on the kitchen counter",
            "the lid is in use on the stew: leave it there and cover the soup with a plate instead",
            {"": dict(add={STEW: on("soup_pot", STOVE, 8.70, 1.725)},
                      move={LID: {"support": None, "z": 0.8591, "xy": [8.70, 1.725], "yaw_deg": 0.0}},
                      goal={"any": by_plate["any"], "all": [["covered", STEW, LID], ["upright", STEW], H]},
                      watch=[POT, STEW, LID, *PLATES], route=plate_route)}),
    }
    return t, fams


# ================================================================== T16 pack the kid's snack box (11-17: replaces T16
# rolling_pin_at_edge).  The snack box is the small storage bin (an open container); the instruction names it.  The
# empty box goes to the desk first, then the apple into it (a loaded box is not carried)
def t16():
    BOX, APPLE, BOWL, BIG = "snack_box", "school_apple", "spare_bowl", "big_bin"
    box_on = lambda sup, x, y: {BOX: on("small_storage_bin", sup, x, y)}  # noqa: E731
    apple = {APPLE: on("apple", T2, 3.70, 6.30)}
    pack = lambda c: [nav(c), pick(c), nav(DESK), place(c, DESK, [-0.70, -6.20]), nav(APPLE), pick(APPLE),  # noqa: E731
                      nav(c), place(APPLE, c)]
    goal = lambda c: {"all": [["inside", APPLE, c], ["on", c, DESK], H]}  # noqa: E731
    ctl = {"note": "the snack box on the kitchen counter, the apple on the dining table",
           "add": {**box_on(COUNTER, -0.10, 7.30), **apple}}
    t = base_task("T16_pack_snack_box", "ZB-T16", "The kid takes some fruit to school tomorrow. Put an apple into "
                  "his snack box and leave it on his desk.", "孩子明天上学要带水果，把一个苹果装进他的零食盒，放到他书桌上。",
                  "box_on_counter", ctl, goal(BOX), [look(COUNTER)] + pack(BOX), [BOX, APPLE])
    spares = {BOWL: on("breakfast_bowl", COUNTER, -0.10, 7.70), BIG: on("wide_storage_bin", TV, 7.30, 0.40)}
    fams = {
        # 11-17 (user): the seed changes whether the box can take the apple -- empty in the closed cabinet (ideal),
        # or on the counter already full of tomorrow's snacks (a banana, three oranges: no 6 cm gap left), a bowl
        # beside it (the stand-in)
        "box_in_cabinet": fam(
            "box_on_counter", ["item_put_away", "not_in_view"], "whether the box has room (seed: empty, put away in "
            "the low wall cabinet; or on the counter full of snacks, a bowl beside it)",
            "the snack box was put away in the low wall cabinet (kitchen cabinet 6), behind its door; or it stands on "
            "the counter already full of snacks",
            "the named box: open the cabinet, take it, close the door, then pack; when it is full, the apple goes in "
            "the bowl and the snacks stay",
            {"in_cabinet": dict(add={**box_on("kitchen_cabinet_6/inside_shelf", 3.50, 0.40), **apple},
                                remove=["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"],
                                goal={"all": [*goal(BOX)["all"], ["is_closed", C6]]}, watch=[BOX, APPLE],
                                route=explore(C6) + from_closed(BOX, C6) + [nav(DESK), place(BOX, DESK, [-0.70, -6.20]),
                                                                            nav(APPLE), pick(APPLE), nav(BOX),
                                                                            place(APPLE, BOX)]),
             "box_full": dict(
                 add={**box_on(COUNTER, -0.10, 7.30), **apple, BOWL: spares[BOWL],
                      "box_banana": {"asset": "banana", "support": None, "z": 1.009, "xy": [-0.10, 7.264],
                                     "yaw_deg": 0.0},
                      **{f"box_orange_{i + 1}": {"asset": "orange", "support": None, "z": 1.009, "xy": [x, 7.345],
                                                 "yaw_deg": 0.0} for i, x in enumerate((-0.17, -0.10, -0.03))}},
                 goal={"all": [*goal(BOWL)["all"], *[["inside", n, BOX] for n in ("box_banana", "box_orange_1",
                                                                                  "box_orange_2", "box_orange_3")]]},
                 watch=[BOX, APPLE, BOWL, "box_banana", "box_orange_1", "box_orange_2", "box_orange_3"],
                 route=[look(COUNTER)] + pack(BOWL))}),
        "no_box": fam(
            "box_on_counter", ["resource_absent", "not_in_view"], "the layout only",
            "there is no snack box in the house; a bowl on the kitchen counter, a big storage bin on the TV stand",
            "the box does not exist: a bowl carries an apple as well (moderate); the big storage bin is no box to "
            "take to school (bad)",
            {"": dict(add={**apple, **spares}, goal=goal(BOWL), watch=[APPLE, BOWL, BIG],
                      route=[look(COUNTER)] + pack(BOWL))}),
        "box_in_use": fam(
            "box_on_counter", ["resource_in_use"], "the layout only",
            "the snack box on the counter holds the kid's crayons (two pencils) and a toy block; a bowl stands "
            "next to it",
            "the box is in use: leave his things in it and carry the apple in the bowl instead",
            {"": dict(add={**box_on(COUNTER, -0.10, 7.30), **apple, BOWL: spares[BOWL],
                           "box_crayon_1": {"asset": "pencil", "support": None, "z": 1.009, "xy": [-0.13, 7.27],
                                            "yaw_deg": 0.0},
                           "box_crayon_2": {"asset": "pencil", "support": None, "z": 1.009, "xy": [-0.13, 7.33],
                                            "yaw_deg": 0.0},
                           "box_block": {"asset": "toy_block", "support": None, "z": 1.009, "xy": [-0.02, 7.30],
                                         "yaw_deg": 0.0}},
                      goal={"all": [*goal(BOWL)["all"], *[["inside", n, BOX] for n in ("box_crayon_1", "box_crayon_2",
                                                                                       "box_block")]]},
                      watch=[BOX, APPLE, BOWL, "box_crayon_1", "box_crayon_2", "box_block"],
                      route=[look(COUNTER)] + pack(BOWL))}),
    }
    return t, fams


# ================================================================== T18 set out bowls and spoons (11-17: replaces T18
# check_cabinet_dishes, which only looked).  Two clean bowls from the low wall cabinet (kitchen cabinet 6), a spoon by
# each, on the dining table; the cabinet closed again
def t18():
    B1, B2, S1, S2 = "dinner_bowl_1", "dinner_bowl_2", "dinner_spoon_1", "dinner_spoon_2"
    GBOX, CAB6, CAB4 = "glass_box", "kitchen_cabinet_6/inside_shelf", "kitchen_cabinet_4/inside_shelf"
    bowl = lambda sup, x, y: on("breakfast_bowl", sup, x, y)  # noqa: E731
    spoons = {S1: on("breakfast_spoon", COUNTER, 0.10, 7.30, 90.0), S2: on("breakfast_spoon", COUNTER, 0.10, 7.55, 90.0)}
    SPOTS = [(3.66, 6.20), (3.66, 6.75)]                  # the dining table's east edge, two places
    SPOON_AT = [(3.66, 6.42), (3.66, 6.97)]
    to_table = lambda x, k: [nav(T2), place(x, T2, SPOTS[k])]  # noqa: E731
    spoon_route = [st for k, sp in enumerate((S1, S2)) for st in [nav(sp), pick(sp), nav(T2), place(sp, T2, SPOON_AT[k])]]
    remove = ["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"]

    def goal(vessels, closed=(C6,)):
        return {"all": [*[["on", v, T2] for v in vessels], ["on", S1, T2], ["on", S2, T2],
                        *[["is_closed", c] for c in closed], H]}

    def two_from(cab, a, b):
        """open the cabinet, take one bowl to the table, come back for the other, close"""
        return [nav(cab), S("open", articulated=cab), S("bend"), S("explore_furniture", furniture=cab), S("straighten"),
                nav(a), pick(a), S("retreat", obstacle=cab, distance_m=0.3)] + to_table(a, 0) + \
               [nav(b), pick(b), S("retreat", obstacle=cab, distance_m=0.3), S("close", articulated=cab)] + to_table(b, 1)
    ctl = {"note": "two clean bowls in the low wall cabinet, two spoons on the kitchen counter",
           "add": {B1: bowl(CAB6, 3.32, 0.40), B2: bowl(CAB6, 3.60, 0.40), **spoons}, "remove": remove}
    t = base_task("T18_set_out_bowls", "ZB-T18", "Dinner is soon. Take two clean bowls from the low wall cabinet to "
                  "the dining table, with a spoon by each.", "快吃晚饭了，从靠墙矮柜里拿两只干净的碗摆到餐桌上，每只碗配一把勺子。",
                  "bowls_in_cabinet", ctl, goal([B1, B2]), two_from(C6, B1, B2) + spoon_route, [B1, B2, S1, S2])
    gbox = {GBOX: on("glass_food_container", COUNTER, 0.19, 7.85, 90.0)}     # over the counter's front edge (pinch)
    one_and_box = lambda b: [nav(C6), S("open", articulated=C6), S("bend"), S("explore_furniture", furniture=C6),  # noqa: E731
                             S("straighten"), nav(b), pick(b), S("retreat", obstacle=C6, distance_m=0.3),
                             S("close", articulated=C6)] + to_table(b, 0) + [nav(GBOX), pick(GBOX)] + to_table(GBOX, 1)
    MUG = "spare_mug"
    mug_out = {MUG: on("breakfast_mug", COUNTER, 0.15, 7.85)}
    one_and = lambda b, x: [nav(C6), S("open", articulated=C6), S("bend"), S("explore_furniture", furniture=C6),  # noqa: E731
                            S("straighten"), nav(b), pick(b), S("retreat", obstacle=C6, distance_m=0.3),
                            S("close", articulated=C6)] + to_table(b, 0) + [nav(x), pick(x)] + to_table(x, 1)
    apart_route = [nav(C6), S("open", articulated=C6), S("bend"), S("explore_furniture", furniture=C6),
                   S("straighten"), nav(B1), pick(B1), S("retreat", obstacle=C6, distance_m=0.3),
                   S("close", articulated=C6)] + to_table(B1, 0) + \
        [nav(C4), S("open", articulated=C4), S("bend"), S("explore_furniture", furniture=C4),
         S("straighten"), nav(B2), pick(B2), S("retreat", obstacle=C4, distance_m=0.3),
         S("close", articulated=C4)] + to_table(B2, 1) + spoon_route
    fams = {
        "bowls_apart": fam(
            "bowls_in_cabinet", ["item_put_away", "not_in_view"], "the layout only",
            "one clean bowl in the low wall cabinet, the other in the other low cabinet (kitchen cabinet 4)",
            "the named bowls are in the house: find the second one in the other cabinet, close both doors",
            {"": dict(add={B1: bowl(CAB6, 3.32, 0.40), B2: bowl(CAB4, 1.40, 0.42), **spoons}, remove=remove,
                      goal=goal([B1, B2], (C6, C4)), watch=[B1, B2, S1, S2],
                      route=[nav(C6), S("open", articulated=C6), S("bend"), S("explore_furniture", furniture=C6),
                             S("straighten"), nav(B1), pick(B1), S("retreat", obstacle=C6, distance_m=0.3),
                             S("close", articulated=C6)] + to_table(B1, 0)
                      + [nav(C4), S("open", articulated=C4), S("bend"), S("explore_furniture", furniture=C4),
                         S("straighten"), nav(B2), pick(B2), S("retreat", obstacle=C4, distance_m=0.3),
                         S("close", articulated=C4)] + to_table(B2, 1) + spoon_route)}),
        "one_bowl": fam(
            "bowls_in_cabinet", ["resource_absent"], "the layout only",
            "only one clean bowl in the cabinet; a glass food box and the plates on the kitchen counter",
            "the second bowl does not exist: the glass box holds soup as well (moderate); a plate does not (bad)",
            {"glass_box": dict(add={B1: bowl(CAB6, 3.32, 0.40), **spoons, **gbox}, remove=remove,
                               goal=goal([B1, GBOX]), watch=[B1, GBOX, S1, S2, "plate_counter_a", "plate_counter_b"],
                               route=one_and_box(B1) + spoon_route),
             # 11-17, from T30 bowls_in_cabinet: the stand-in on the counter is a mug (it holds soup as well)
             "mug": dict(add={B1: bowl(CAB6, 3.32, 0.40), **spoons, **mug_out}, remove=remove,
                         goal=goal([B1, MUG]), watch=[B1, MUG, S1, S2, "plate_counter_a", "plate_counter_b"],
                         route=one_and(B1, MUG) + spoon_route)}),
        "bowl_in_use": fam(
            "bowls_in_cabinet", ["resource_in_use"], "the layout only",
            "two bowls in the cabinet, but one holds leftover cherry tomatoes; a glass food box on the counter",
            "one bowl is in use (leftovers in it): leave it, take the clean one and the glass box instead",
            {"tomatoes": dict(add={B1: bowl(CAB6, 3.32, 0.40), B2: bowl(CAB6, 3.60, 0.40), **spoons, **gbox,
                           "left_tomato_1": {"asset": "cherry_tomato", "support": None, "z": 0.425, "xy": [3.58, 0.40],
                                             "yaw_deg": 0.0},
                           "left_tomato_2": {"asset": "cherry_tomato", "support": None, "z": 0.425, "xy": [3.62, 0.40],
                                             "yaw_deg": 0.0}}, remove=remove,
                      goal={"all": [*goal([B1, GBOX])["all"], ["on", B2, CAB6], ["inside", "left_tomato_1", B2],
                                    ["inside", "left_tomato_2", B2]]},
                      watch=[B1, B2, GBOX, S1, S2, "left_tomato_1", "left_tomato_2"],
                      route=one_and_box(B1) + spoon_route),
             # 11-17, from T30 bowl_not_plate: the second bowl still holds someone's oatmeal
             "oatmeal": dict(add={B1: bowl(CAB6, 3.32, 0.40), B2: on("oatmeal_bowl", CAB6, 3.60, 0.40), **spoons, **gbox},
                             remove=remove, goal={"all": [*goal([B1, GBOX])["all"], ["on", B2, CAB6]]},
                             watch=[B1, B2, GBOX, S1, S2], route=one_and_box(B1) + spoon_route)}),
        "door_stuck": fam(
            "bowls_in_cabinet", ["appliance_failure"], "the layout only",
            "the low wall cabinet's door is stuck and does not open (locked_articulated, to be supported in sim); "
            "the other low cabinet also holds two clean bowls",
            "the named cabinet cannot be opened: take the bowls from the other low cabinet instead",
            {"": dict(add={B1: bowl(CAB4, 1.25, 0.42), B2: bowl(CAB4, 1.55, 0.42), **spoons}, remove=remove,
                      locked_articulated=[C6], goal=goal([B1, B2], (C4,)), watch=[B1, B2, S1, S2],
                      route=[nav(C6), look(C6)] + two_from(C4, B1, B2) + spoon_route)}),
    }
    return t, fams


MAKERS = [t15, t16, t18, t21, t22, t23, t24, t25, t26, t27, t28, t29, t30]
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
