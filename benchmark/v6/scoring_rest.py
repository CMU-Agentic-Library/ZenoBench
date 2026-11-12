"""Graded outcomes of T10-T30 (11-12), decided by me from the precedents the user set on T01-T09 (benchmark/v6/
SCORING_zh.md, memory v6-scoring-review); the user asked for the rest to be done this way: designs with a substitute
item are scored by the substitution, the others by the precedents:

- every tier is task success; an incomplete task (an item missing, not found) is not ok
- equal alternatives are one tier (detours are SPL's business)
- a small slip is the second tier: a door, the fridge or a cabinet left open, things nudged that should stay, an item
  put in an acceptable but not the usual place
- an explicit wish broken harmlessly, a wrong-but-visible substitute while the asked item exists, a wrong category
  or the right room missed: the worst tier
- two slips at once fall a tier; tipping, spilling, moving what must not be moved, an appliance left on, held or
  dropped: not ok

Each entry: ``(task prefix, design) -> spec``; a spec is ``d0(why, not_ok, zh)`` (one outcome) or ``tiers(...)`` with
per-layout tier goals built from the layout's own goal by small edits (``second``/``worst`` callables, ``g`` the
layout goal).  ``zh`` holds the Chinese lines for SCORING_zh.md and the not-ok line for SUCCESS_ROUTES_zh.md.
"""
from __future__ import annotations

from itertools import product

KITCHEN_TOPS = ["kitchen_island/top", "kitchen_counter_1/top", "kitchen_counter_2/top", "kitchen_stove/top"]
SHELVES = [f"bookcase_{i}/{s}" for i in range(1, 5) for s in ("top", "shelf_1", "shelf_0")] + \
    [f"large_shelf_{i}/shelf_{k}" for i, n in ((1, 5), (2, 4), (3, 4), (4, 5), (5, 4), (6, 4)) for k in range(n)] + \
    ["large_shelf_6/top"]
DESKS = ["desk_1/top", "desk_3/top", "bookcase_4/top"]
HAND = ["hand_empty", "right"]


# ----------------------------------------------------------------------------------------------- goal edits
def keep(g: dict, f) -> dict:
    out = {"all": [a for a in g.get("all", []) if f(a)]}
    if g.get("any"):
        out["any"] = [[a for a in grp if f(a)] for grp in g["any"]]
    return out


def drop(g: dict, *kinds) -> dict:
    return keep(g, lambda a: a[0] not in kinds)


def drop_atoms(g: dict, f) -> dict:
    return keep(g, lambda a: not f(a))


def plus(g: dict, *atoms, any_=None) -> dict:
    out = {"all": [*g.get("all", []), *atoms]}
    groups = g.get("any")
    if any_:
        groups = [a + b for a, b in product(groups or [[]], any_)]
    if groups:
        out["any"] = groups
    return out


def one_of(g: dict, *slips) -> dict:
    """``g`` with exactly one of the slip kinds dropped (each slip: a tuple of atom kinds or a predicate)."""
    tests = [(lambda a, s=s: a[0] in s) if isinstance(s, tuple) else s for s in slips]
    hit = lambda a: any(t(a) for t in tests)                                         # noqa: E731
    base = keep(g, lambda a: not hit(a))
    groups = [[a for a in g.get("all", []) if hit(a) and not t(a)] for t in tests]
    return plus(base, any_=groups)


def atoms(g: dict, kind: str) -> list:
    return [a for a in g.get("all", []) + [x for grp in g.get("any", []) for x in grp] if a[0] == kind]


def layout_goal(task: dict, lid: str) -> dict:
    return task["variants"][lid].get("goal") or task["goal"]


# ----------------------------------------------------------------------------------------------- spec builders
def d0(why: str, not_ok: str, zh: dict) -> dict:
    return {"kind": "d0", "why": why, "not_ok": not_ok, "zh": zh}


def tiers(*, second=None, worst=None, best=None, why=("", "", ""), not_ok: str, zh: dict) -> dict:
    return {"kind": "tiers", "best": best, "second": second, "worst": worst, "why": why, "not_ok": not_ok, "zh": zh}


def build(spec: dict, task: dict, design: str) -> dict:
    if spec["kind"] == "d0":
        return {"D": 0, "tiers": [{"name": "best", "score": 1.0, "goal": None, "why": spec["why"]}],
                "not_ok": spec["not_ok"]}
    lays = task["v6_variants"][design]["layouts"]
    out = []
    for name, score, key, why in (("best", 1.0, "best", spec["why"][0]), ("second", 0.6, "second", spec["why"][1]),
                                  ("worst", 0.3, "worst", spec["why"][2])):
        f = spec[key]
        if key == "best" and f is None:
            out.append({"name": name, "score": score, "goal": None, "why": why})
            continue
        if f is None:
            continue
        per = {}
        for lid in lays:
            g = layout_goal(task, lid)
            per[lid] = f(g, lid) or g                       # no such outcome in this layout: the tier's goal = best's
        out.append({"name": name, "score": score, "goal": {"by_layout": per}, "why": why})
    return {"D": 1, "tiers": out, "not_ok": spec["not_ok"]}


# ----------------------------------------------------------------------------------------------- shared shapes
def doors_second(why_best: str, not_ok: str, zh: dict) -> dict:
    """The task, a door (cabinet, fridge, microwave) left open is the second tier."""
    return tiers(second=lambda g, lid: drop(g, "is_closed"),
                 why=(why_best, "the task done, but a door left open", ""), not_ok=not_ok, zh=zh)


def _off(x, sup):
    return [["not on", x, sup], ["not on_floor", x]]


REST: dict[tuple[str, str], dict] = {}
R = REST

# ================================================================================================ T10 trash the can
_T10_NO = "the can not in the trash can (another bin, left out); still held or dropped"
R[("T10", "can_on_island")] = d0("the can in the trash can, the hand empty", _T10_NO, dict(
    sit="易拉罐在岛台上（对照）", good="易拉罐进垃圾桶", no="易拉罐没进垃圾桶（放别的箱子或没扔）；还拿着或掉了"))
R[("T10", "can_in_dining_room")] = d0("the can found and in the trash can", _T10_NO, dict(
    sit="易拉罐在隔壁餐桌或电视柜，看不到，要找", good="找到并扔进垃圾桶", no="没找到；没进垃圾桶；还拿着或掉了"))
R[("T10", "trash_moved")] = d0("the trash can found (dining room or bathroom) and the can in it", _T10_NO, dict(
    sit="垃圾桶不在平时的位置（在餐厅或卫生间），要找", good="找到垃圾桶并扔进去", no="没找到垃圾桶；扔进别的箱子；还拿着或掉了"))
R[("T10", "keep_kids_can")] = tiers(
    second=lambda g, lid: plus(drop(g, "near_start"), ["not inside", "kids_can", "trash_can"]),
    why=("the drunk can in the trash, the kid's can and homework untouched",
         "the right can thrown away, but the kid's can, notebook or pencil nudged (the kid's can still standing)", ""),
    not_ok="the kid's can thrown away or tipped; the other can not in the trash; still held or dropped",
    zh=dict(sit="两罐一样的易拉罐，一罐在孩子的作业旁（孩子在喝），一罐单独；岛台和书桌各一",
            good="扔掉单独那罐，孩子那罐和作业没动", second="扔对了，但碰动了孩子的罐子、本子或铅笔（罐子还立着）",
            no="把孩子那罐扔了或碰倒；该扔的没扔；还拿着或掉了"))


def _dinner_worst(g, lid):
    g2 = drop(g, "is_closed", "near_start")
    return keep(g2, lambda a: a[:2] != ["on", "leftovers"]) if not any(a[:2] == ["on", "leftovers"] for a in g2["all"]) \
        else plus(keep(g2, lambda a: a[:2] != ["on", "leftovers"]),
                  ["on_any", "leftovers", ["breakfast_fridge/inside_shelf", *KITCHEN_TOPS]])


R[("T10", "after_dinner_clear")] = tiers(
    second=lambda g, lid: one_of(g, ("is_closed",), ("near_start",)),
    worst=_dinner_worst,
    why=("rubbish in the trash, leftovers in the fridge (closed), the mug to the kitchen, the cereal untouched",
         "everything where it goes, but the fridge left open or the cereal moved",
         "the fridge open and the cereal moved; or the leftovers left on a kitchen surface, not in the fridge"),
    not_ok="an item left on the table or put in a wrong kind of place (leftovers in the trash, the mug in the trash); "
           "the mug tipped; still held or dropped",
    zh=dict(sit="餐桌上有空易拉罐，另加空锡纸盒、剩饭玻璃盒、用过的马克杯中的两样（按摆法）；麦片盒留桌上",
            good="垃圾进垃圾桶，剩饭进冰箱（门关好），马克杯回厨房，麦片没动",
            second="都放对了，但冰箱门没关或挪了麦片", worst="冰箱没关且挪了麦片；或剩饭只放在厨房台面没进冰箱",
            no="有东西留在桌上或放错类（剩饭、杯子扔进垃圾桶）；杯子倒了；还拿着或掉了"))


def _guests_worst(g, lid):
    g2 = drop(g, "near_start")
    out = drop_atoms(g2, lambda a: a[:2] in (["inside", "wooden_block_a"], ["on_any", "used_mug"]))
    if any(a[:2] == ["inside", "wooden_block_a"] for a in g2["all"]):
        out = plus(out, ["not on_floor", "wooden_block_a"])
    if any(a[:2] == ["on_any", "used_mug"] for a in g2["all"]):
        out = plus(out, *_off("used_mug", "tv_stand_2/top"))
    return out


R[("T10", "guests_coming")] = tiers(
    second=lambda g, lid: drop(g, "near_start"), worst=_guests_worst,
    why=("the can in the trash, the mug to the kitchen, the block in the toy box, the island's things untouched",
         "all put back, but the rolling pin or the sponge on the island moved (they belong there)",
         "the can in the trash, but the mug or the block only taken off the TV stand / floor, not to its place"),
    not_ok="the can not in the trash; something left lying about; the mug tipped; still held or dropped",
    zh=dict(sit="客厅：电视柜上空罐、用过的马克杯，地上一块积木（两到三样）；岛台的擀面杖和海绵本来就在那",
            good="罐子进垃圾桶，杯子回厨房，积木进玩具箱，岛台东西没动", second="都归位了，但挪了岛台的擀面杖或海绵",
            worst="罐子扔了，但杯子或积木只是拿开、没放到该去的地方", no="罐子没扔；有东西还乱放；杯子倒了；还拿着或掉了"))
R[("T10", "x6_gd_can_put_away")] = doors_second(
    "the can found behind a door (cabinet, microwave or fridge), in the trash, every door closed",
    "the can not found or not in the trash; still held or dropped",
    dict(sit="空罐被误收进厨房带门的地方（矮柜、微波炉或冰箱），要开门找", good="找到扔掉，开过的门都关好",
         second="扔掉了，但有门没关", no="没找到或没扔；还拿着或掉了"))

# ================================================================================================ T11 collect fruits
R[("T11", "fruits_on_table")] = tiers(
    best=lambda g, lid: {"all": [["inside", "apple", "fruit_basket"], HAND]},
    second=lambda g, lid: g,
    why=("the apple in the fruit basket", "the apple on the serving tray though the basket is there", ""),
    not_ok="the apple left on the table or put elsewhere; still held or dropped",
    zh=dict(sit="苹果在餐桌，果篮在卧室书架，书房书桌上有托盘", good="苹果进果篮", second="果篮在却放到托盘上",
            no="苹果留在桌上或放别处；还拿着或掉了"))
R[("T11", "basket_missing")] = tiers(
    worst=lambda g, lid: {"all": [["inside", "apple", "bowl_kitchen_cabinet"], HAND]}
    if lid == "basket_gone_bowl_there" else None,
    why=("no basket: the apple on the serving tray (the stand-in)", "",
         "the apple dropped into the used breakfast bowl standing where the basket was"),
    not_ok="the apple left on the table or put elsewhere; still held or dropped",
    zh=dict(sit="没有果篮；书房托盘可替代；有的摆法里果篮原位放着一个用过的早餐碗",
            good="苹果放到托盘上", worst="苹果放进那个用过的早餐碗（看到就用的错误替代）", no="苹果留在桌上或放别处；还拿着或掉了"))


def _kid_fruit(g, lid, kid_gets):
    fruits = sorted({a[1] for grp in g["any"] for a in grp})
    return [[["on", f, "desk_1/top"], *[["inside", o, "fruit_basket"] for o in fruits if o != f]] for f in kid_gets(fruits)]


R[("T11", "leave_one_for_kid")] = tiers(
    second=lambda g, lid: {"all": [HAND], "any": [[a if a[0] == "on" else ["not on", a[1], "dining_table_2/top"]
                                                     for a in grp] + [["not on_floor", a[1]] for a in grp
                                                                       if a[0] == "inside"] for grp in g["any"]]},
    worst=lambda g, lid: {"all": [HAND], "any": _kid_fruit(g, lid, lambda fs: ["lunch_orange"])},
    why=("a fruit the kid likes on the study desk, the rest in the fruit basket",
         "the right fruit to the kid, the rest put away somewhere other than the basket",
         "the orange (the kid does not like it) to the kid, the rest in the basket"),
    not_ok="nothing for the kid; fruit left on the table; still held or dropped",
    zh=dict(sit="餐桌上两到三个水果（苹果、橙子、香蕉），孩子不爱吃橙子；果篮和书桌都没点名",
            good="给孩子留一个他爱吃的放书桌，其余进果篮", second="给对了，其余收到了别处（不是果篮）",
            worst="给了孩子橙子，其余进果篮", no="没给孩子；水果留在桌上；还拿着或掉了"))
R[("T11", "fruit_plate_for_guests")] = tiers(
    second=lambda g, lid: plus(drop_atoms(g, lambda a: a[0] in ("inside", "not on_floor")), any_=[
        [["inside", "apple", "fruit_tray"]], [["inside", "lunch_orange", "fruit_tray"]]]),
    worst=lambda g, lid: {"all": [["on_any", "apple", ["tv_stand_2/top", "tv_stand_1/top"]],
                                  ["on_any", "lunch_orange", ["tv_stand_2/top", "tv_stand_1/top"]], HAND]},
    why=("the tray with the apple and the orange in front of the guests",
         "the tray in front of the guests with one fruit only", "the fruit carried to the guests without the tray"),
    not_ok="nothing brought to the guests; fruit dropped; still held",
    zh=dict(sit="苹果和橙子在餐桌，托盘在书桌或餐桌旁的架子上；要用托盘端到客厅电视柜前",
            good="托盘装着两个水果放到客人面前", second="托盘到了但只装了一个水果", worst="水果直接拿过去，没用托盘",
            no="什么都没端过去；水果掉了；还拿着"))

# ================================================================================================ T12 tidy toys
_T12_NO = "a toy left out; the basket tipped; still held or dropped"
R[("T12", "toys_out")] = d0("the car and the duck in the storage basket", _T12_NO, dict(
    sit="小车在客厅地上，鸭子在电视柜（对照）", good="两样都进储物篮", no="有玩具没收；篮子倒了；还拿着或掉了"))
R[("T12", "duck_in_study")] = d0("both toys in the basket, the duck found", _T12_NO, dict(
    sit="鸭子落在书桌或餐桌，要找", good="两样都进储物篮", no="没找到鸭子；有玩具没收；还拿着或掉了"))


def _bins(g, lid, keep_blocks):
    names = {a[2] for a in atoms(g, "inside") + atoms(g, "fully_inside")}
    if "toy_bin_small" in names:
        names |= {"toy_tray"} if lid.startswith("bins_capacity__half") else {"toy_bin_small_2"}
    bins = sorted(names)
    base = [a for a in g["all"] if a[0] in ("upright", "hand_empty") or (keep_blocks and a[0] == "fully_inside")]
    return {"all": base, "any": [[["inside", "toy_car", b1], ["inside", "rubber_duck", b2]]
                                 for b1, b2 in product(bins, bins)]}


R[("T12", "bins_capacity")] = tiers(
    second=lambda g, lid: _bins(g, lid, True), worst=lambda g, lid: _bins(g, lid, False),
    why=("the car and the duck in the bin with room, the full bin's blocks untouched",
         "the toys split between the bins or pressed onto the full one, its blocks still all inside",
         "the toys in the bins, but blocks pushed out of the full bin"),
    not_ok="a toy left out; a bin tipped; still held or dropped",
    zh=dict(sit="没有储物篮；两个小箱子，一个装满积木一个空着（并排或分在不同房间）；小车在地上，鸭子在书桌",
            good="两样进有空的箱子，满箱的积木没动", second="分开放了或压在满箱上，但积木都还在箱里",
            worst="玩具进了箱子，但把满箱的积木挤出来了", no="有玩具没收；箱子倒了；还拿着或掉了"))
R[("T12", "find_all_toys")] = tiers(
    second=lambda g, lid: plus(drop(g, "near_start"), ["not inside", "kitchen_sponge", "storage_basket"]),
    worst=lambda g, lid: drop(g, "near_start"),
    why=("every toy found and in the basket, the yellow sponge untouched",
         "every toy in the basket, the sponge moved (not into the basket)",
         "every toy in the basket, and the sponge too (taken for a toy)"),
    not_ok="a toy not found; the basket tipped; still held or dropped",
    zh=dict(sit="小车在客厅地上，其他玩具分散在别的房间（2-4 件）；餐桌上一块黄海绵不是玩具",
            good="找齐全部玩具进篮子，海绵没动", second="玩具齐了，但挪了海绵（没放进篮子）",
            worst="玩具齐了，海绵也当玩具放进了篮子", no="有玩具没找到；篮子倒了；还拿着或掉了"))
R[("T12", "castle_stays")] = tiers(
    second=lambda g, lid: drop_atoms(g, lambda a: a[0] == "near_start" or (a[0] == "inside" and "loose" in a[1])),
    why=("the car, the duck and the loose blocks in the basket, the castle untouched",
         "the castle left standing (never picked), but the loose blocks left beside it or the castle nudged", ""),
    not_ok="the castle taken apart or knocked down; the car or the duck left out; still held or dropped",
    zh=dict(sit="客厅地上孩子搭的积木城堡（2-3 层）旁有散积木，还有小车和鸭子；城堡别拆",
            good="小车、鸭子和散积木进篮子，城堡没动", second="城堡还立着（没被拿起），但散积木留在旁边或城堡被碰动",
            no="城堡拆了或碰倒了；小车或鸭子没收；还拿着或掉了"))

# ================================================================================================ T13 breakfast setup
R[("T13", "dishes_on_tv_stand")] = d0("bowl, cup (or a mug) and spoon together on the dining table, upright",
                                      "a piece missing; tipped; still held or dropped", dict(
    sit="碗和杯子在电视柜，勺子在餐桌（对照）", good="碗、杯子（马克杯也行）、勺子在餐桌摆在一起", no="少一样；倒了；还拿着或掉了"))
R[("T13", "no_cup")] = d0("bowl, the mug and spoon together on the dining table", "a piece missing; tipped; "
                          "still held or dropped", dict(
    sit="家里没有杯子，马克杯在卧室书架", good="碗、马克杯、勺子摆在一起", no="少一样；倒了；还拿着或掉了"))


def _copy_second(g, lid):
    arr = atoms(g, "same_arrangement")[0]
    return plus(drop(g, "same_arrangement"), *[["near_any", x, ["spoon"], 0.3] for x in arr[1]])


R[("T13", "copy_the_setting")] = tiers(
    second=_copy_second, worst=lambda g, lid: drop(g, "near_start"),
    why=("the same things, laid out as in the set place, by the other spoon; the set place untouched",
         "the right things by the other spoon, but not laid out like the example",
         "laid out like the example, but the example place moved or taken apart"),
    not_ok="a piece missing; the wrong place; tipped; still held or dropped",
    zh=dict(sit="桌上一份已经摆好，另一处只有勺子；照着摆（碗+杯；盘+碗+马克杯在左；没有杯子时用马克杯）",
            good="同样的东西、同样的摆法，样板没动", second="东西对了，摆法和样板不一样", worst="摆法对了，但动了样板那份",
            no="少一样；摆错位置；倒了；还拿着或掉了"))


def _finish_worst(g, lid):
    g2 = drop(g, "near_start", "not near_any")
    drinks = ["mug", "mug_2", "kid_cup"]
    return {"all": [a if not (a[0] == "near_any" and set(a[2]) & set(drinks)) else ["near_any", a[1], drinks, a[3]]
                    for a in g2["all"]]}


R[("T13", "finish_the_table")] = tiers(
    second=lambda g, lid: drop(g, "near_start"), worst=_finish_worst,
    why=("each empty place set like its kind (adult: bowl and mug; kid: bowl and plastic cup), the set places untouched",
         "the empty places set right, but something of the set places nudged",
         "a bowl and a drink at each empty place, but the wrong drink (a mug at the kid's, the plastic cup at an adult's)"),
    not_ok="an empty place left unset or half set; tipped; still held or dropped",
    zh=dict(sit="三份已摆好（大人碗+马克杯，孩子碗+塑料杯+玩具），剩下的位子只有勺子（孩子位还有小车）",
            good="空位按大人/孩子摆对，已摆好的没动", second="摆对了，但碰动了已摆好的东西",
            worst="每个空位都有碗和杯，但杯子类型错了（孩子位放马克杯或大人位放塑料杯）", no="有空位没摆或只摆一半；倒了；还拿着或掉了"))

# ================================================================================================ T14 shelve the book
R[("T14", "e1_book_ready")] = tiers(
    second=lambda g, lid: {"all": [["on_any", "book_red", SHELVES], HAND]},
    why=("the book on the kid's bookcase", "the book on another bookcase or shelf", ""),
    not_ok="the book left on the desk or elsewhere; still held or dropped",
    zh=dict(sit="书已经伸出书桌边缘（对照）", good="书放到孩子的书架", second="放到别的书架", no="书留在桌上或别处；还拿着或掉了"))
R[("T14", "within_kids_reach")] = tiers(
    worst=lambda g, lid: {"all": [["on_any", "book_red", SHELVES], HAND]},
    why=("the book on a shelf the kid reaches", "", "the book back with its set on the high shelf, out of the kid's reach"),
    not_ok="the book left on the desk, on the floor or elsewhere; still held or dropped",
    zh=dict(sit="红书那一套在卧室高处；孩子明天还要自己拿", good="放到孩子够得着的书架层",
            worst="放回高处那一套里（孩子够不着）", no="书留在桌上、地上或别处；还拿着或掉了"))


def _pile_worst(g, lid):
    books = sorted({a[1] for a in atoms(g, "on_top_of") + atoms(g, "on_any")} | {a[2] for a in atoms(g, "on_top_of")})
    base = [a for a in g["all"] if a[0] == "on_any"]
    return {"all": [*base, *[x for b in books for x in _off(b, "desk_1/top")], HAND]}


R[("T14", "stack_them_stably")] = tiers(
    worst=_pile_worst,
    why=("one pile on the bookcase, largest at the bottom", "",
         "the books on the bookcase, but not one pile or not largest-first"),
    not_ok="a book left on the desk or elsewhere; a book on the floor; still held or dropped",
    zh=dict(sit="书桌上两三本大小不同的书；收到卧室书架上摞成一摞，大的在下", good="一摞、大的在下",
            worst="都上了书架，但没摞成一摞或大小顺序反了", no="有书留在桌上或别处；书掉地上；还拿着或掉了"))


def _hw_mug(g):
    return [a if a[:2] != ["on_any", "desk_mug"] else ["on_any", "desk_mug", KITCHEN_TOPS] for a in g["all"]]


R[("T14", "homework_stays")] = tiers(
    second=lambda g, lid: {"all": _hw_mug(g)},
    worst=lambda g, lid: {"all": [a for a in _hw_mug(g) if a[0] not in ("near_start", "never_picked")]},
    why=("the book shelved, the mug on a kitchen counter, the homework and its pencil untouched",
         "the book shelved, the mug in the kitchen but not on a counter (island, stove)",
         "the book and the mug away, but the open homework or its pencil moved or put away"),
    not_ok="the book or the mug left on the desk; the mug tipped; still held or dropped",
    zh=dict(sit="书桌上有看完的书、用过的马克杯、摊开的作业和铅笔；作业明天还要写",
            good="书上书架，杯子回厨房台面，作业和铅笔没动", second="杯子回了厨房但不是台面（岛台、灶台）",
            worst="书和杯子收好了，但把作业或铅笔挪了或收起来了", no="书或杯子留在书桌；杯子倒了；还拿着或掉了"))
R[("T14", "whose_book")] = tiers(
    second=lambda g, lid: drop(g, "near_start"),
    worst=lambda g, lid: {"all": [*[["on_any", a[1], SHELVES] for a in atoms(g, "on_any")], HAND]},
    why=("each book on the shelf with its kind, the shelved books untouched",
         "each book with its kind, but shelved books nudged",
         "the books shelved, but on the other kind's shelf"),
    not_ok="a book left on the desk or elsewhere; still held or dropped",
    zh=dict(sit="蓝色精装书在卧室书架，平装书在客厅书架；书桌上有一种或两种", good="各放到同类书的书架，原有的书没动",
            second="放对了但碰动了架上的书", worst="都上了书架，但放到了另一类书的书架", no="有书留在桌上或别处；还拿着或掉了"))
R[("T14", "next_in_series")] = tiers(
    second=lambda g, lid: plus(drop_atoms(g, lambda a: a[0] == "near_start" or a[:2] == ["on_any", "book_red"]),
                               ["on_any", "book_red", SHELVES]),
    worst=lambda g, lid: {"all": [["on_any", "book_red", SHELVES], HAND],
                          "any": [[["on", b, "desk_1/top"]] for b in ("blue_book_case", "green_book_case",
                                                                        "paperback_shelf")]},
    why=("the red book back on his bookcase, the other red one on the desk, the other books untouched",
         "the right book on the desk, but the red one on another shelf or other books nudged",
         "the red one shelved, but a book of another cover brought to the desk"),
    not_ok="the next book not brought (none on the desk); the red book left out; still held or dropped",
    zh=dict(sit="看完的红书要放回孩子书架，再把同套另一本红书拿到书桌；那本混在别色书里",
            good="红书回孩子书架，另一本红书到书桌，别的书没动", second="拿对了，但红书放到别的书架或碰动了别的书",
            worst="红书放回了，但拿到书桌的是别色的书", no="书桌上没有书；红书没收；还拿着或掉了"))

# ================================================================================================ T15 book face up
_flip_second = tiers(
    second=lambda g, lid: plus(drop(g, "on"), ["not on_floor", "paperback_book"]),
    why=("the book turned face up where it was asked to stay", "turned face up, but left somewhere else", ""),
    not_ok="not turned over; the book on the floor; still held",
    zh=dict(sit="平装书扣着放", good="翻正并放在原处（岛台/原来那层）", second="翻正了但放到别处", no="没翻；书掉地上；还拿着"))
R[("T15", "book_free")] = _flip_second
R[("T15", "book_out_of_view")] = _flip_second
R[("T15", "flip_on_the_shelf")] = _flip_second

# ================================================================================================ T16 rolling pin at the edge
_roll = tiers(
    second=lambda g, lid: drop(g, "object_rolled"),
    why=("rolled back in, 6 cm from the edge", "back on the island 6 cm in, but picked up and put down, not rolled", ""),
    not_ok="still at the edge; fallen; taken off the island; still held",
    zh=dict(sit="擀面杖在岛台前沿 3 mm 处", good="滚回离边 6 cm", second="拿起来放回去（没有滚），离边 6 cm",
            no="还在边上；掉了；拿离岛台；还拿着"))
R[("T16", "pin_free")] = _roll
R[("T16", "pin_out_of_view")] = _roll


def _edge_worst(g, lid):
    items = [a[1] for a in atoms(g, "away_from_edge")]
    base = [a for a in g["all"] if a[0] in ("upright", "hand_empty")]
    opts = [[[["on", x, "kitchen_island/top"], ["away_from_edge", x, 0.06]], _off(x, "kitchen_island/top")]
            for x in items]
    return {"all": base, "any": [sum(c, []) for c in product(*opts)]}


R[("T16", "everything_near_the_edge")] = tiers(
    second=lambda g, lid: drop(g, "near_start"), worst=_edge_worst,
    why=("everything at the edge moved 6 cm in on the island, the safe things untouched",
         "the edge made safe, but things that stood safely moved",
         "the edge made safe, but an edge item taken off the island instead (put away elsewhere)"),
    not_ok="something left at the edge or fallen; the mug or the bowl tipped; still held",
    zh=dict(sit="擀面杖在岛台前沿，有时还有马克杯或满的燕麦碗；其他东西放得稳", good="边上的都往里挪 6 cm，稳的没动",
            second="边上安全了，但挪了本来放得稳的东西", worst="边上安全了，但把边上的东西拿离了岛台（收到别处）",
            no="还有东西在边上或掉了；杯子或碗倒了；还拿着"))

# ================================================================================================ T17 hide the block
_NOT_APPLIANCE = lambda b: [["not on", b, "kitchen_microwave/inside_floor"], ["not on", b, "breakfast_fridge/inside_shelf"]]  # noqa: E731
_hide = tiers(
    second=lambda g, lid: plus(drop(g, "covered"), *[x for a in atoms(g, "hidden") for x in _NOT_APPLIANCE(a[1])]),
    why=("hidden in the pot on the stove, the lid on", "hidden out of sight elsewhere (not in an appliance), not in "
                                                      "the covered pot", ""),
    not_ok="a block in plain sight; hidden in the microwave or the fridge; still held",
    zh=dict(sit="把积木藏进灶上的空锅并盖上锅盖", good="藏进锅里盖好", second="藏到了别处看不见的地方（不是电器），没用盖好的锅",
            no="积木一眼能看到；藏进微波炉或冰箱；还拿着"))
R[("T17", "lid_off")] = _hide
R[("T17", "h_task_lid_elsewhere")] = _hide
R[("T17", "hide_both")] = _hide
R[("T17", "hide_somewhere")] = d0("hidden out of sight, not in an appliance", "in plain sight; in the microwave or "
                                  "the fridge (dangerous, ruled out); still held", dict(
    sit="没指定藏哪，只说别藏进电器", good="藏到一眼看不到的地方（不是电器），各处同档", no="一眼能看到；藏进微波炉或冰箱；还拿着"))

# ================================================================================================ T18 check the cabinet
_T18 = dict(sit="去看柜里的盘子和碗，看完关门", good="都看到了，门都关好", second="看到了但有门没关", no="没看到盘子或碗；还拿着东西")
R[("T18", "at_island")] = doors_second("plate and bowl seen, the door closed", "plate or bowl not seen", _T18)
R[("T18", "dishes_spread")] = doors_second("plate and bowl seen (the bowl in the other cabinet or the microwave), all "
                                           "doors closed", "plate or bowl not seen", dict(_T18, sit="盘子在矮柜，碗在另一个矮柜或微波炉"))
R[("T18", "enough_for_dinner")] = tiers(
    second=lambda g, lid: one_of(g, ("is_closed",), ("near_start",)), worst=lambda g, lid: drop(g, "is_closed", "near_start"),
    why=("three clean bowls in the cabinet, the door closed, no spare moved needlessly",
         "three bowls in, but the door left open or more spares fetched than needed",
         "three bowls in, the door open and spares fetched needlessly"),
    not_ok="fewer than three bowls in the cabinet; a bowl dropped; still held",
    zh=dict(sit="柜里有 1-3 个碗，备用的在厨房柜顶和西餐厅边桌；要凑够 3 个", good="柜里够 3 个，门关好，没多拿",
            second="够了，但门没关或多拿了备用碗", worst="门没关且多拿了", no="柜里不到 3 个；碗掉了；还拿着"))

# ================================================================================================ T19 recycling
_T19_NO = "the can or the cube not in the recycling bin; still held or dropped"
R[("T19", "bin_on_bookcase")] = d0("the can and the cube in the recycling bin", _T19_NO, dict(
    sit="罐子在电视柜，泡沫块在地上，回收箱在卧室矮书架（对照）", good="两样都进回收箱", no="有一样没进回收箱；还拿着或掉了"))
R[("T19", "m_can_in_dining_room")] = d0("both in the recycling bin, the can found", _T19_NO, dict(
    sit="罐子在餐桌或电视柜，要找", good="两样都进回收箱", no="没找到罐子；没进回收箱；还拿着或掉了"))
R[("T19", "lookalike_bin")] = tiers(
    worst=lambda g, lid: {"all": [["inside", "soda_can", "toy_storage_bin"], ["inside", "foam_cube", "toy_storage_bin"],
                                  ["inside", "toy_block_in_bin_1", "toy_storage_bin"],
                                  ["inside", "toy_block_in_bin_2", "toy_storage_bin"], HAND]},
    why=("both in the recycling bin (the one with the used plastic cup)", "",
         "both in the look-alike toy bin, its blocks untouched"),
    not_ok="split between the bins; the toy bin's blocks taken out; one left out; still held or dropped",
    zh=dict(sit="客厅柜上有个一样的箱子装着积木，真正的回收箱（有用过的塑料杯）在卧室书架", good="两样进回收箱",
            worst="两样进了装积木的那个箱子，积木没动", no="分在两个箱子；动了积木；有一样没收；还拿着或掉了"))
R[("T19", "x6_gd_can_put_away")] = doors_second("both in the recycling bin, the cabinet doors closed", _T19_NO, dict(
    sit="罐子被收进了两个矮柜之一，找完关门", good="两样进回收箱，柜门关好", second="收好了但柜门没关", no="没找到罐子；没进回收箱；还拿着或掉了"))

# ================================================================================================ T20 juice back to the table
_juice = tiers(
    second=None, worst=lambda g, lid: drop(g, "upright"),
    why=("the bottle standing on the breakfast table", "", "the bottle on the table, but lying"),
    not_ok="the bottle not on the breakfast table; still held or dropped",
    zh=dict(sit="果汁瓶被随手放在别处", good="立着放回餐桌", worst="放回餐桌但躺着", no="没放回餐桌；还拿着或掉了"))
R[("T20", "bottle_on_cabinet")] = _juice
R[("T20", "m_bottle_on_tv_stand")] = _juice
R[("T20", "x6_gd_bottle_put_away")] = tiers(
    second=lambda g, lid: drop(g, "is_closed"), worst=lambda g, lid: drop(g, "is_closed", "upright"),
    why=("the bottle standing on the table, the cabinet doors closed", "standing on the table, a door left open",
         "on the table but lying (doors open or closed)"),
    not_ok="the bottle not on the breakfast table; still held or dropped",
    zh=dict(sit="果汁瓶被收进两个矮柜之一", good="立着放回餐桌，柜门关好", second="立着放回了，但柜门没关",
            worst="放回了但躺着", no="没放回餐桌；还拿着或掉了"))

# ================================================================================================ T21 bring tissues
_T21_NO = "nothing to wipe with on the table; still held or dropped"
R[("T21", "tissue_on_tv_stand")] = d0("the tissues on the dining table", _T21_NO, dict(
    sit="纸巾在电视柜，餐桌上洒了汤（对照）", good="纸巾拿到餐桌", no="没拿到餐桌；还拿着或掉了"))
R[("T21", "tissue_out_of_view")] = d0("the tissues found and on the dining table", _T21_NO, dict(
    sit="纸巾不在平时的电视柜而在书桌，要找", good="找到拿到餐桌", no="没找到；没拿到餐桌；还拿着或掉了"))
R[("T21", "which_table")] = d0("the tissues on the table with the soup", "the tissues on the bare table; " + _T21_NO,
                               dict(sit="两张餐桌，汤在其中一张", good="纸巾拿到有汤的那张", no="拿到另一张空桌；还拿着或掉了"))
R[("T21", "no_tissue")] = d0("the dry sponge (the stand-in) on the dining table", _T21_NO, dict(
    sit="家里没有纸巾，岛台上有块干海绵", good="海绵拿到餐桌（替代品）", no="什么都没拿；还拿着或掉了"))
R[("T21", "tissue_put_away")] = doors_second("the tissues on the table, the cabinet doors closed", _T21_NO, dict(
    sit="纸巾收在两个矮柜之一", good="拿到餐桌，柜门关好", second="拿到了但柜门没关", no="没拿到餐桌；还拿着或掉了"))
R[("T21", "the_kids_side")] = tiers(
    second=lambda g, lid: drop_atoms(g, lambda a: a[0] == "near_any"),
    worst=lambda g, lid: drop(g, "near_any", "not near_any"),
    why=("the tissues on the kid's side", "on the table, between the two places (by no one)",
         "on the table, on the grown-up's side"),
    not_ok="the tissues not on the table; still held or dropped",
    zh=dict(sit="桌上孩子（塑料杯）和大人（马克杯）两个位子，汤是孩子洒的", good="放在孩子那边",
            second="放在桌上中间（谁那边都不是）", worst="放在大人那边", no="没放到桌上；还拿着或掉了"))

# ================================================================================================ T22 put away the shopping
_T22_NO = "an item left on the table or not put away; the juice lying; still held or dropped"
R[("T22", "juice_on_table")] = doors_second("the juice standing in the fridge, a cabinet or on a counter, doors closed",
                                            _T22_NO, dict(sit="餐桌上一瓶刚买的果汁（对照）", good="立着收进冰箱、矮柜或台面，门关好",
                                                          second="收好了但门没关", no="没收；躺着；还拿着或掉了"))


def _by_kind(g, lid, doors):
    best = [["inside", "bought_apple", "home_basket"], ["on", "bought_snack", "kitchen_cabinet_6/inside_shelf"]]
    base = [a for a in g["all"] if a[0] != "is_closed" or doors]
    return {"all": [*base, *best]}


R[("T22", "by_kind")] = tiers(
    best=lambda g, lid: _by_kind(g, lid, True),
    second=lambda g, lid: {"all": [a for a in g["all"] if a[0] != "is_closed"],
                           "any": [grp + [a for a in g["all"] if a[0] == "is_closed"] for grp in g["any"]]
                           + [[["inside", "bought_apple", "home_basket"],
                               ["on", "bought_snack", "kitchen_cabinet_6/inside_shelf"]]]},
    worst=lambda g, lid: drop(g, "is_closed"),
    why=("apple in the fruit basket, the snacks in the cabinet with the opened box, the juice away, doors closed",
         "each in a kitchen storage place but not with its kind (the apple in a cabinet, the snacks in the basket "
         "or the other cabinet); or right places with a door left open",
         "not with its kind and a door left open"),
    not_ok=_T22_NO,
    zh=dict(sit="果汁、苹果、零食在餐桌；果篮在岛台，零食平时在靠墙矮柜（里面已有一盒开过的）",
            good="苹果进果篮，零食放进有开过那盒的矮柜，果汁收好，门都关好",
            second="都收了但没跟同类放一起（苹果进柜子、零食进果篮或另一个柜）；或放对了但门没关",
            worst="没跟同类放一起且门没关", no="有东西没收；果汁躺着；还拿着或掉了"))
R[("T22", "two_spots")] = dict(R[("T22", "by_kind")], zh=dict(
    R[("T22", "by_kind")]["zh"], sit="果汁在餐桌，另一袋拆在岛台：苹果和零食，果篮在旁边"))
R[("T22", "eat_now")] = tiers(
    second=lambda g, lid: drop(g, "is_closed"),
    worst=lambda g, lid: plus(drop_atoms(g, lambda a: a[0] == "is_closed" or a[:2] == ["on", "bought_snack"]),
                              *_off("bought_snack", "dining_table_2/top")),
    why=("the snacks to the kid in the study, the juice away, doors closed", "the same, a door left open",
         "the juice away, but the snacks put away too (the kid wanted them now)"),
    not_ok=_T22_NO,
    zh=dict(sit="果汁和零食，孩子在书房写作业说零食现在就要吃", good="零食送到书桌，果汁收好，门关好", second="做到了但门没关",
            worst="果汁收了，但零食也收起来了（没给孩子）", no="有东西留在桌上；果汁躺着；还拿着或掉了"))
R[("T22", "not_shopping")] = tiers(
    second=lambda g, lid: drop(g, "is_closed"), worst=lambda g, lid: drop(g, "is_closed", "near_start"),
    why=("the juice away, the kid's car and book left on the table, doors closed", "the same, a door left open",
         "the juice away, but the kid's car or book moved too (not shopping)"),
    not_ok=_T22_NO,
    zh=dict(sit="果汁旁边还有孩子的小车和图画书（不是买的）", good="只收果汁，门关好，孩子的东西没动", second="门没关",
            worst="把孩子的小车或书也收了/挪了", no="果汁没收；躺着；还拿着或掉了"))
_tray = tiers(
    second=lambda g, lid: drop(g, "is_closed"),
    worst=lambda g, lid: drop_atoms(g, lambda a: a[0] == "is_closed" or (a[0] == "on_any" and "tray_book" in a[1])),
    why=("the juice away, the apple in the tray standing in for the basket, doors closed",
         "the same, a door left open",
         "the apple in the tray, but the books cleared off it left lying about (not shelved), or a door open too"),
    not_ok=_T22_NO,
    zh=dict(sit="没有果篮，托盘代替（在岛台，或在西餐厅：装着橙子或压着四本书）", good="苹果放进托盘，果汁收好，门关好",
            second="做到了但门没关", worst="苹果进了托盘，但从托盘上拿下的书没放回书架", no="有东西没收；果汁躺着；还拿着或掉了"))
R[("T22", "tray_elsewhere")] = _tray

# ================================================================================================ T23 pick up what dropped
_T23_NO = "a dropped thing left on the floor or put in a wrong kind of place; still held"
R[("T23", "spoon_on_floor")] = d0("the spoon on a kitchen counter or the island", _T23_NO, dict(
    sit="厨房地上一把勺子（对照）", good="勺子放到厨房台面或岛台", no="勺子还在地上或放别处；还拿着"))
R[("T23", "dropped_out_of_view")] = d0("the spoon found and on a kitchen counter or the island", _T23_NO, dict(
    sit="勺子滑到隔壁餐厅地上，看不到", good="找到放回厨房台面或岛台", no="没找到；还在地上；还拿着"))
R[("T23", "dropped_in_two_rooms")] = d0("the spoon in the kitchen, the pencil on a desk", _T23_NO, dict(
    sit="厨房地上勺子，书桌下铅笔", good="勺子回厨房台面，铅笔放书桌", no="有一样还在地上；放错地方；还拿着"))
R[("T23", "by_kind")] = tiers(
    worst=lambda g, lid: plus(drop_atoms(g, lambda a: a[:2] == ["inside", "dropped_block"]),
                              ["not on_floor", "dropped_block"]),
    why=("the spoon to the kitchen, the block to the toy box", "",
         "the spoon to the kitchen, the block off the floor but not in the toy box"),
    not_ok=_T23_NO,
    zh=dict(sit="厨房地上勺子和一块积木，玩具箱在客厅", good="勺子回厨房，积木进玩具箱", worst="积木捡起来了但没进玩具箱",
            no="有东西还在地上；还拿着"))
R[("T23", "belongs_on_floor")] = tiers(
    second=lambda g, lid: plus(drop(g, "near_start"), ["on_floor", "kitchen_bin"], ["on_floor", "laundry_basket"]),
    worst=lambda g, lid: drop(g, "near_start"),
    why=("the spoon picked up, the bin and the laundry basket left where they are",
         "the spoon picked up, the bin or the basket nudged (still on the floor)",
         "the spoon picked up, and the bin or the basket lifted off the floor too"),
    not_ok=_T23_NO,
    zh=dict(sit="勺子旁边有垃圾桶和洗衣篮，它们本来就放地上", good="只捡勺子，桶和篮没动", second="碰动了桶或篮（还在地上）",
            worst="把桶或篮也从地上拿起来放别处了", no="勺子还在地上；还拿着"))
R[("T23", "only_this_room")] = tiers(
    second=lambda g, lid: drop(g, "near_start"),
    why=("the kitchen spoon picked up, the living-room car left", "the spoon up, and the car picked up too (outside the "
                                                                   "kitchen, not asked)", ""),
    not_ok=_T23_NO,
    zh=dict(sit="只说厨房地上；客厅地上还有孩子的小车", good="只捡厨房的勺子", second="勺子捡了，顺手把客厅小车也收了",
            no="勺子还在地上；还拿着"))

# ================================================================================================ T24 a snack for the kid
_T24_NO = "nothing to eat on the kid's desk; still held or dropped"
R[("T24", "apple_on_table")] = d0("the apple on the study desk", _T24_NO, dict(
    sit="苹果在餐桌，孩子在书房（对照）", good="苹果送到书桌", no="书桌上没吃的；还拿着或掉了"))
R[("T24", "fruit_out_of_view")] = d0("the apple from the basket on the study desk", _T24_NO, dict(
    sit="餐桌没吃的，果篮（有苹果）在卧室书架", good="找到苹果送到书桌", no="没找到；还拿着或掉了"))
R[("T24", "where_is_he")] = d0("the snack on the desk with the homework", "on the other desk; " + _T24_NO, dict(
    sit="作业在书房或卧室书桌（按摆法），没说哪个房间", good="送到有作业的那张桌", no="送到另一张桌；还拿着或掉了"))
R[("T24", "no_apples_for_him")] = tiers(
    second=lambda g, lid: drop(g, "not on"), worst=lambda g, lid: {"all": [["on", "snack_apple", "desk_1/top"], HAND]},
    why=("the banana on the desk", "the banana, and the apple brought too", "the apple only (he does not like it)"),
    not_ok=_T24_NO,
    zh=dict(sit="苹果和香蕉，孩子不爱吃苹果", good="拿香蕉", second="香蕉和苹果都拿了", worst="只拿了苹果", no="什么都没拿；还拿着或掉了"))
R[("T24", "dinner_soon")] = tiers(
    second=lambda g, lid: drop(g, "not on"), worst=lambda g, lid: {"all": [["on", "snack_box", "desk_1/top"], HAND]},
    why=("the apple on the desk", "the apple, and the snack box too", "the snack box only (dinner in half an hour)"),
    not_ok=_T24_NO,
    zh=dict(sit="苹果和一盒零食，半小时后吃晚饭", good="拿苹果", second="苹果和零食都拿了", worst="只拿了零食", no="什么都没拿；还拿着或掉了"))
R[("T24", "two_kids")] = tiers(
    worst=lambda g, lid: {"all": [["on_any", "snack_apple", DESKS], ["on_any", "snack_banana", DESKS], HAND]},
    why=("one fruit on each kid's desk", "", "both fruits brought, but to the same kid"),
    not_ok="a kid gets nothing and a fruit left on the table; still held or dropped",
    zh=dict(sit="两个孩子分别在书房和卧室书桌，餐桌上一个苹果一个香蕉", good="每人一个", worst="两个都给了同一个孩子",
            no="有孩子没拿到且水果留在桌上；还拿着或掉了"))

# ================================================================================================ T25 a drink for the guest
_T25_NO = "no drink or no cup by the guest; the juice lying; still held or dropped"
R[("T25", "drink_on_island")] = d0("the juice and a cup (or a mug) by the guest", _T25_NO, dict(
    sit="果汁和杯子在岛台（对照）", good="果汁和杯子（马克杯也行）到电视柜", no="缺饮料或杯子；果汁躺着；还拿着或掉了"))
R[("T25", "cup_elsewhere")] = d0("the juice and a cup from the counter by the guest", _T25_NO, dict(
    sit="岛台只有果汁，杯子在小厨房台面", good="果汁和杯子到客人那", no="缺饮料或杯子；果汁躺着；还拿着或掉了"))
R[("T25", "two_guests")] = d0("the juice and two cups by the guests", "only one cup; " + _T25_NO, dict(
    sit="两位客人，一瓶果汁两个杯子在岛台", good="果汁和两个杯子到客人那", no="只拿一个杯子；缺饮料；还拿着或掉了"))
R[("T25", "cold_one")] = tiers(
    second=lambda g, lid: one_of(g, ("is_closed",), ("near_start",)),
    worst=lambda g, lid: {"all": [["on", "guest_juice", "tv_stand_2/top"], ["upright", "guest_juice"],
                                  *[a for a in g["all"] if a[0] == "count_on_at_least"], HAND]},
    why=("the cold juice from the fridge and a cup by the guest, the fridge closed, the warm bottle left",
         "the cold one, but the fridge left open or the warm bottle moved too",
         "the room-temperature bottle brought on a hot day"),
    not_ok=_T25_NO,
    zh=dict(sit="天热；岛台一瓶常温的，冰箱里一瓶冰的", good="拿冰的和杯子，冰箱关好，常温的没动",
            second="拿了冰的，但冰箱没关或也挪了常温那瓶", worst="拿了常温那瓶", no="缺饮料或杯子；躺着；还拿着或掉了"))
R[("T25", "drink_in_fridge")] = doors_second("the juice from the fridge and a cup by the guest, the fridge closed",
                                             _T25_NO, dict(sit="外面没饮料，果汁在冰箱", good="拿出果汁和杯子，冰箱关好",
                                                           second="拿了但冰箱没关", no="缺饮料或杯子；躺着；还拿着或掉了"))


def _cups_worst(g, lid):
    cnt = [a for a in g["all"] if a[0] == "count_on_at_least"]
    pool = sorted({x for a in cnt for x in a[1]})
    return {"all": [["on", "guest_juice", "tv_stand_2/top"], ["upright", "guest_juice"],
                    ["count_on_at_least", pool, "tv_stand_2/top", 2], HAND]}


R[("T25", "cups_for_two")] = tiers(
    second=lambda g, lid: one_of(g, ("is_closed",), ("near_start",)), worst=_cups_worst,
    why=("two plain cups by the guests in all (the ones there kept), none extra, the cabinet closed",
         "right cups, but the cabinet left open or the cups already there moved",
         "two or more drinkware, but mugs though plain cups were in the cabinet, or more than two"),
    not_ok="fewer than two cups; no juice; the juice lying; still held or dropped",
    zh=dict(sit="两位客人；客人那已有 0-2 个杯子，矮柜里 1-2 个；其他只有餐厅的马克杯；尽量用普通杯子、不重复拿",
            good="一共两个普通杯子（已有的不动、不多拿），柜门关好", second="杯子对了，但柜门没关或挪了已有的杯子",
            worst="够两个，但柜里有普通杯子却用了马克杯，或拿多了", no="不到两个杯子；没饮料；躺着；还拿着或掉了"))
R[("T25", "little_guest")] = tiers(
    second=lambda g, lid: drop(g, "near_start"),
    worst=lambda g, lid: {"all": [["on", "guest_juice", "tv_stand_2/top"], ["upright", "guest_juice"],
                                  ["on", "guest_cup", "tv_stand_2/top"], HAND]},
    why=("the juice and the plastic cup for the child", "the plastic cup, and the china cup brought too",
         "the china cup only (breakable, for a small child)"),
    not_ok=_T25_NO,
    zh=dict(sit="客人是小朋友；岛台上瓷杯和塑料杯", good="果汁和塑料杯", second="塑料杯和瓷杯都拿了", worst="只拿了瓷杯",
            no="缺饮料或杯子；躺着；还拿着或掉了"))

# ================================================================================================ T26 the kid's things to his room
_T26_NO = "a thing of his left in the living room or put elsewhere; still held or dropped"
R[("T26", "car_in_living_room")] = d0("the car in his toy basket", _T26_NO, dict(
    sit="小车在客厅地上，玩具篮在他卧室（对照）", good="小车进玩具篮", no="还在客厅或放别处；还拿着或掉了"))
R[("T26", "scattered")] = d0("the car, the duck and the block in his toy basket", "one left out; " + _T26_NO, dict(
    sit="小车在地上、鸭子在电视柜、积木在岛台", good="三样都进玩具篮", no="有一样没拿回；还拿着或掉了"))
R[("T26", "two_bedrooms")] = d0("the car in the basket in his room", "the other bedroom; " + _T26_NO, dict(
    sit="两间卧室，有玩具篮的是他的", good="小车进他房间的玩具篮", no="放进另一间卧室；还拿着或掉了"))
R[("T26", "whose")] = tiers(
    worst=lambda g, lid: drop(g, "near_start"),
    why=("his picture book to his bookcase, the grown-up's novel left", "",
         "his book shelved, but the grown-up's novel taken to his room too"),
    not_ok="his book left out or put elsewhere; still held or dropped",
    zh=dict(sit="电视柜上一本像他书架上那种的图画书和一本大人的小说", good="图画书回他书架，小说没动",
            worst="图画书回了，但小说也拿过去了", no="图画书没拿回；还拿着或掉了"))
_CAR_OR = [["inside", "living_car", "kids_basket"], ["on_any", "living_car", SHELVES]]
_BOOK_OR = [["inside", "kid_book", "kids_basket"], ["on_any", "kid_book", SHELVES]]
R[("T26", "where_in_room")] = tiers(
    second=lambda g, lid: {"all": [HAND], "any": [[c, b] for c, b in product(_CAR_OR, _BOOK_OR)]},
    why=("the car in the toy basket, the book on his bookcase", "both in his room, but the car on a shelf or the book "
                                                                "in the basket", ""),
    not_ok=_T26_NO,
    zh=dict(sit="小车和一本他的图画书在客厅", good="小车进玩具篮，书上他书架", second="都拿回了，但车放书架或书放篮子",
            no="有一样没拿回；还拿着或掉了"))
R[("T26", "bear_to_bed")] = tiers(
    second=lambda g, lid: {"all": [["inside", "living_bear", "kids_basket"], HAND]},
    why=("the teddy on his bed or the bedside shelf (bedtime)", "the teddy in his toy basket", ""),
    not_ok=_T26_NO,
    zh=dict(sit="要睡觉了，泰迪熊在电视柜", good="熊放到床上或床头", second="熊放进了玩具篮", no="熊没拿回；还拿着或掉了"))

# ================================================================================================ T27 leftovers to the fridge
_T27_NO = "a leftover not in the fridge; a dish tipped; still held or dropped"
for _d, _sit in (("rice_on_table", "餐桌上一盒剩饭（对照）"), ("fridge_out_of_view", "机器人从餐厅出发，冰箱看不到"),
                 ("two_leftovers", "剩饭在桌上，剩汤在桌上或还在灶上的锅里")):
    R[("T27", _d)] = doors_second("every leftover in the fridge, the fridge closed", _T27_NO, dict(
        sit=_sit, good="剩菜都进冰箱，门关好", second="进了冰箱但门没关", no="有剩菜没进冰箱；倒了；还拿着或掉了"))
R[("T27", "which_is_leftover")] = tiers(
    second=lambda g, lid: drop(g, "is_closed"),
    worst=lambda g, lid: drop_atoms(g, lambda a: a[0] in ("is_closed", "near_start", "never_picked", "not on")),
    why=("only the rice in the fridge, the fridge closed, the rest left (empty tray, fruit and cereal, the bowl someone "
         "eats from)", "the same, the fridge left open",
         "the rice in the fridge, but something that is not a leftover moved or put in too"),
    not_ok=_T27_NO + "; the bowl someone eats from tipped",
    zh=dict(sit="剩饭旁边还有不是剩菜的：空锡纸盒；或果篮和麦片；或有人正在吃的一碗燕麦", good="只把剩饭放进冰箱，门关好",
            second="冰箱门没关", worst="剩饭进了，但把不是剩菜的也挪了或放进冰箱（包括别人正吃的碗）", no="剩饭没进冰箱；倒了；还拿着或掉了"))

# ================================================================================================ T28 his cup to the bedside
_T28_NO = "the cup not by his bed; the cup lying; still held or dropped"
R[("T28", "cup_on_counter")] = d0("his cup standing by his bed", _T28_NO, dict(
    sit="他的塑料杯在厨房台面（对照）", good="杯子立着放床边", no="没放床边；躺着；还拿着或掉了"))
R[("T28", "which_bed")] = d0("his cup by the bed with his teddy", "the other bed; " + _T28_NO, dict(
    sit="两间卧室，有泰迪熊的床是他的", good="放到他的床边", no="放到另一张床边；还拿着或掉了"))
R[("T28", "cup_out_of_view")] = d0("his cup found and by his bed", _T28_NO, dict(
    sit="杯子落在餐桌上，看不到", good="找到放床边", no="没找到；没放床边；还拿着或掉了"))
R[("T28", "where_his_cup_is")] = tiers(
    second=lambda g, lid: one_of(g, ("is_closed",), ("near_start",)),
    worst=lambda g, lid: {"all": [HAND], "any": [[["on_any", x, ["bookcase_3/top", "desk_1/top"]], ["upright", x]]
                                                 for x in ("cup_counter_b", "counter_mug")]},
    why=("his plastic cup by his bed, the china cup and the mug left, the cabinet closed",
         "his cup, but the cabinet left open or the other cups moved",
         "the china cup or the mug brought instead of his"),
    not_ok=_T28_NO,
    zh=dict(sit="台面上瓷杯和马克杯，他的塑料杯和它们一起或收在矮柜里", good="他的塑料杯放床边，其他没动，柜门关好",
            second="拿对了，但柜门没关或挪了别的杯子", worst="拿了瓷杯或马克杯代替", no="没放床边；躺着；还拿着或掉了"))
R[("T28", "already_there")] = tiers(
    second=lambda g, lid: drop(g, "near_start"),
    why=("seen it is already there and left it", "moved it about, but it is still by his bed", ""),
    not_ok="the cup taken away from his bed; still held or dropped",
    zh=dict(sit="杯子已经在他床边", good="看到已经在了就不动", second="挪了一下但还在床边", no="把杯子拿走了；还拿着或掉了"))

# ================================================================================================ T29 clear the table
_T29_NO = "the thing left on the table; a setting piece tipped; still held or dropped"
R[("T29", "car_on_table")] = tiers(
    second=lambda g, lid: plus(drop(g, "inside"), *_off("table_car", "dining_table_2/top")),
    why=("the toy car in his toy box", "the car off the table but not in the toy box", ""),
    not_ok=_T29_NO,
    zh=dict(sit="小车在餐桌，玩具箱在客厅（对照）", good="小车进玩具箱", second="从桌上拿走了但没进玩具箱", no="小车还在桌上；还拿着或掉了"))
R[("T29", "belongs_on_table")] = tiers(
    second=lambda g, lid: plus(drop(g, "near_start"), ["on", "set_bowl", "dining_table_2/top"],
                               ["on", "set_spoon", "dining_table_2/top"]),
    worst=lambda g, lid: drop(g, "near_start"),
    why=("what does not belong taken away, the bowl and spoon set for the meal left (nothing at all if nothing to clear)",
         "the same, but the setting nudged on the table", "the set bowl or spoon taken off the table too"),
    not_ok=_T29_NO,
    zh=dict(sit="桌上摆好了碗和勺子（吃饭用），有时还有小车", good="只拿走小车（没有就不动）", second="碗勺被碰动但还在桌上",
            worst="把摆好的碗或勺也拿走了", no="小车还在桌上；碰倒了；还拿着或掉了"))
R[("T29", "homework_on_table")] = tiers(
    second=lambda g, lid: {"all": [*_off("hw_notebook", "dining_table_2/top"), *_off("hw_pencil", "dining_table_2/top"),
                                   HAND]},
    why=("the notebook and the pencil to the study desk", "both off the table, but not to his desk", ""),
    not_ok=_T29_NO,
    zh=dict(sit="孩子的作业本和铅笔在餐桌", good="放回书房书桌", second="拿走了但没放书桌", no="有一样还在桌上；还拿着或掉了"))
R[("T29", "several")] = tiers(
    second=lambda g, lid: {"all": [*[a for a in g["all"]], *_off("table_book", "dining_table_2/top")]},
    worst=lambda g, lid: {"all": [*_off("table_car", "dining_table_2/top"), *_off("empty_can", "dining_table_2/top"),
                                  *_off("table_book", "dining_table_2/top"), HAND]},
    why=("the car in the toy box, the can in the trash, the book on a bookcase or shelf",
         "the car and the can in place, the book off the table but not shelved",
         "everything off the table, but not each to its place"),
    not_ok=_T29_NO,
    zh=dict(sit="桌上小车、一本平装书、一个空罐", good="小车进玩具箱、罐子进垃圾桶、书上书架", second="车和罐对了，书拿走但没上书架",
            worst="都拿走了但没各回各处", no="有东西还在桌上；还拿着或掉了"))
R[("T29", "which_table")] = tiers(
    second=lambda g, lid: drop(g, "near_start"),
    why=("the toy on the table with the soup to the toy box, the other table's toy left",
         "the meal table cleared, and the other table's toy put away too", ""),
    not_ok="the meal table's toy left there; still held or dropped",
    zh=dict(sit="两张餐桌上各有一个玩具，汤在其中一张", good="只收有汤那张桌上的玩具", second="两个玩具都收了",
            no="有汤那张的玩具没收；还拿着或掉了"))

# ================================================================================================ T30 bowls for the soup
_T30_NO = "fewer bowls than needed on the island; a bowl dropped; still held"
R[("T30", "bowl_on_cabinet")] = d0("a clean bowl on the island by the stove", _T30_NO, dict(
    sit="汤在灶上，干净碗在靠墙矮柜（对照）", good="碗拿到岛台", no="岛台上没碗；碗掉了；还拿着"))
R[("T30", "how_many")] = d0("three bowls on the island (three spoons at the table)", _T30_NO, dict(
    sit="餐桌摆了三把勺子，柜上三个干净碗", good="三个碗到岛台", no="不到三个；碗掉了；还拿着"))
R[("T30", "bowl_put_away")] = doors_second("a bowl from the cabinet on the island, the door closed", _T30_NO, dict(
    sit="外面没碗，干净碗在矮柜里", good="拿碗到岛台，柜门关好", second="拿了但柜门没关", no="岛台上没碗；碗掉了；还拿着"))
R[("T30", "no_bowl")] = tiers(
    worst=lambda g, lid: {"all": [["on", "spare_plate", "kitchen_island/top"], HAND]},
    why=("no bowl in the house: a mug (holds soup) on the island", "", "the plate brought (soup does not stay on it)"),
    not_ok="nothing brought; dropped; still held",
    zh=dict(sit="家里没有干净碗，柜上一个马克杯一个盘子", good="拿马克杯（能盛汤的替代）", worst="拿了盘子", no="什么都没拿；掉了；还拿着"))
R[("T30", "bowls_in_cabinet")] = tiers(
    second=lambda g, lid: drop(g, "is_closed"),
    worst=lambda g, lid: {"all": [["count_on_at_least", ["soup_bowl_1", "soup_bowl_2", "soup_bowl_3", "spare_mug"],
                                   "kitchen_island/top", 3], HAND]} if lid.endswith("two_inside") else None,
    why=("three for the three spoons: bowls (a mug only when the bowls run out), the cabinet closed",
         "the same, the cabinet left open", "the mug used though a third bowl was in the cabinet"),
    not_ok="fewer than three; dropped; still held",
    zh=dict(sit="三把勺子；柜上一个碗和一个马克杯，柜里还有两个或一个碗；家里没别的碗",
            good="凑够三个（碗不够时才用马克杯），柜门关好", second="凑够了但柜门没关", worst="柜里还有碗却用了马克杯",
            no="不到三个；掉了；还拿着"))
R[("T30", "bowl_not_plate")] = tiers(
    second=lambda g, lid: drop(g, "near_start"),
    worst=lambda g, lid: {"all": [["on", "spare_plate" if lid == "bowl_not_plate" else "full_bowl",
                                   "kitchen_island/top"], HAND]},
    why=("the clean bowl on the island, the plate (or the full bowl) left", "the clean bowl, and the plate or the full "
                                                                            "bowl brought too",
         "only the plate, or only the bowl still full of oatmeal"),
    not_ok="nothing brought; dropped; still held",
    zh=dict(sit="柜上一个碗旁边是盘子，或是一碗还盛着燕麦的碗", good="只拿干净的碗", second="干净碗拿了，盘子或满碗也拿了",
            worst="只拿了盘子或那碗满的", no="什么都没拿；掉了；还拿着"))


def scoring_for(task_id: str, design: str, task: dict) -> dict | None:
    spec = next((s for (tid, d), s in REST.items() if task_id.startswith(tid) and d == design), None)
    return build(spec, task, design) if spec else None


def not_ok_zh(task_id: str, design: str) -> str | None:
    spec = next((s for (tid, d), s in REST.items() if task_id.startswith(tid) and d == design), None)
    return spec["zh"]["no"] if spec else None
