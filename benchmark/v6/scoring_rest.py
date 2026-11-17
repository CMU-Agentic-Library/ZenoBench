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
# T10 trash_full (11-17, substitution; next to trash_moved): the trash can packed to the rim, the recycling bin
# (a used plastic cup in it) takes the can; pressed onto the full trash can (its contents left in) is the worst
R[("T10", "trash_full")] = tiers(
    worst=lambda g, lid: {"all": [*atoms(g, "near_start"), HAND],
                          "any": [[["inside", "soda_can", "trash_can"]], [["near_any", "soda_can", ["trash_can"], 0.03]]]},
    why=("the can in the recycling bin, the full trash can left as it was", "",
         "the can pressed onto the full trash can (its contents left in)"),
    not_ok="the trash can's contents taken out or tipped to make room; the can left out; still held or dropped",
    zh=dict(sit="垃圾桶在原处但塞满到桶口（零食盒、两个罐子、纸巾盒、饭盒），罐子放不进；回收箱（里面有用过的塑料杯）在电视柜或餐桌（按摆法）",
            good="罐子扔进回收箱，垃圾桶里的东西没动", worst="罐子硬塞在满垃圾桶上（桶里东西没动）",
            no="把垃圾桶里的东西倒出来腾地方；罐子没扔；还拿着或掉了"))
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


# T11 no_apple_for_kid (11-17, substitution; replaces leave_one_for_kid): no apple left; the banana (the kid does not
# like oranges) is the substitute, the orange the worst
R[("T11", "no_apple_for_kid")] = tiers(
    worst=lambda g, lid: {"all": [["on", "lunch_orange", "desk_1/top"], HAND]},
    why=("the banana on the study desk (no apple left)", "", "the orange (the kid does not like it) brought instead"),
    not_ok="nothing brought to the desk; still held or dropped",
    zh=dict(sit="孩子想吃苹果，家里苹果没了；餐桌上有香蕉和橙子，指令说孩子不爱吃橙子", good="拿香蕉到书桌",
            worst="拿了橙子", no="什么都没拿；还拿着或掉了"))
R[("T11", "fruit_plate_for_guests")] = tiers(
    second=lambda g, lid: plus(drop_atoms(g, lambda a: a[0] in ("inside", "not on_floor")), any_=[
        [["inside", "apple", "fruit_box"]], [["inside", "lunch_orange", "fruit_box"]]]),
    worst=lambda g, lid: {"all": [["on_any", "apple", ["tv_stand_2/top", "tv_stand_1/top"]],
                                  ["on_any", "lunch_orange", ["tv_stand_2/top", "tv_stand_1/top"]], HAND]},
    why=("the small bin (no tray in the house) with the apple and the orange in front of the guests",
         "the bin in front of the guests with one fruit only", "the fruit carried to the guests without a container"),
    not_ok="nothing brought to the guests; fruit dropped; still held",
    zh=dict(sit="苹果和橙子在餐桌；指令要用容器端过去，家里没有托盘，小收纳盒在书桌或餐桌旁的架子上（11-17 改成替换）",
            good="小收纳盒装着两个水果放到客人面前", second="盒子到了但只装了一个水果", worst="水果直接拿过去，没用容器",
            no="什么都没端过去；水果掉了；还拿着"))

# ================================================================================================ T12 tidy toys
_T12_NO = "a toy left out; the basket tipped; still held or dropped"
R[("T12", "toys_out")] = d0("the car and the duck in the storage basket", _T12_NO, dict(
    sit="小车在客厅地上，鸭子在电视柜（对照）", good="两样都进储物篮", no="有玩具没收；篮子倒了；还拿着或掉了"))
# T12 bedtime_toy (11-17, substitution; replaces duck_in_study): a cuddly toy to bed, none named.  With the teddy
# there: the teddy best, the duck second; without it the duck is the substitute (best); the toy car the worst
_BEDS = ["mattress_1/top", "bookcase_3/top"]
R[("T12", "bedtime_toy")] = tiers(
    second=lambda g, lid: {"all": [["on_any", "rubber_duck", _BEDS], HAND]} if lid.endswith("teddy_there") else None,
    worst=lambda g, lid: {"all": [["on_any", "toy_car", _BEDS], HAND]},
    why=("the teddy bear by the bed; without a teddy, the soft rubber duck",
         "the rubber duck though the teddy was there", "the hard toy car brought to cuddle"),
    not_ok="nothing brought to the bed; still held or dropped",
    zh=dict(sit="孩子要睡觉，要个能抱着睡的玩具，指令没点名；seed：泰迪熊在电视柜上，或者家里没有泰迪熊（只有橡皮鸭和小车）",
            good="有熊拿熊；没熊拿橡皮鸭（替换）", second="有熊却拿了鸭子", worst="拿了小车（硬的，不能抱）",
            no="什么都没拿到床边；还拿着或掉了"))
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
# T12 castle_stays (restored 11-17)
R[("T12", "castle_stays")] = tiers(
    # the castle standing at the end (its blocks one on another) is what counts for the second tier: nudged, taken
    # apart and built again (user 11-12), or the loose blocks left beside it
    second=lambda g, lid: drop_atoms(g, lambda a: a[0] in ("near_start", "never_picked")
                                     or (a[0] == "inside" and "loose" in a[1])),
    why=("the car, the duck and the loose blocks in the basket, the castle untouched",
         "the castle standing at the end, but taken apart and built again, nudged, or the loose blocks left beside it",
         ""),
    not_ok="the castle left taken apart or knocked down; the car or the duck left out; still held or dropped",
    zh=dict(sit="客厅地上孩子搭的积木城堡（2-3 层）旁有散积木，还有小车和鸭子；城堡别拆",
            good="小车、鸭子和散积木进篮子，城堡没动",
            second="最后城堡还立着，但被拆了又搭回去、被碰动，或散积木留在旁边",
            no="城堡拆了没搭回或碰倒了；小车或鸭子没收；还拿着或掉了"))

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


def _finish_mug(g, lid):
    """The kid's drink a mug instead of the small bowl (no plastic cup in the house)."""
    out = []
    for a in g["all"]:
        if a[0] == "near_any" and a[2] == ["kid_small_bowl"]:
            out.append(["near_any", a[1], ["mug", "mug_2"], a[3]])
        elif a[0] == "not near_any" and set(a[2]) & {"mug", "mug_2"}:
            continue
        else:
            out.append(a)
    return {"all": out}


R[("T13", "finish_the_table")] = tiers(
    second=_finish_mug, worst=lambda g, lid: drop(g, "near_start"),
    why=("each empty place set like its kind; the kid's drink in the small bowl (no plastic cup left), the set "
         "places untouched",
         "the kid's place given a china mug instead (no plastic cup left)",
         "the empty places set, but something of the set places nudged"),
    not_ok="an empty place left unset or half set; tipped; still held or dropped",
    zh=dict(sit="三份已摆好（大人碗+马克杯，孩子碗+塑料杯+玩具）；剩下孩子的位子（有时还有一个大人位）只有勺子，家里没有第二个塑料杯，有一个马克杯和一个小碗（11-17 改成替换）",
            good="空位按大人/孩子摆好，孩子的杯子用小碗顶上（不怕摔）", second="孩子位放了马克杯（陶瓷，容易摔）",
            worst="摆好了，但碰动了已摆好的东西", no="有空位没摆或只摆一半；倒了；还拿着或掉了"))

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


# T14 kids_shelf_full (11-17, substitution; replaces stack_them_stably): every level of the kid's bookcase packed;
# another bookcase is the substitute; squeezed onto his packed bookcase (nothing moved) the worst
R[("T14", "kids_shelf_full")] = tiers(
    worst=lambda g, lid: {"all": g["all"], "any": [
        [["on_any", "book_red", ["bookcase_2/top", "bookcase_2/shelf_1", "bookcase_2/shelf_0"]]],
        [["near_any", "book_red", [a[1] for a in atoms(g, "near_start")], 0.02]]]},
    why=("the book on another bookcase in his room, his packed bookcase untouched", "",
         "the book squeezed onto (or on top of the books of) his packed bookcase, nothing moved"),
    not_ok="books on his bookcase moved or taken out to make room; the book left on the desk; still held or dropped",
    zh=dict(sit="孩子书架每一层都塞满了书，红书放不下；卧室里另一个书架有地方（11-17 替换 stack_them_stably）",
            good="书放到卧室另一个书架，孩子书架没动", worst="硬塞到孩子书架上（压在别的书上），架上的书没动",
            no="挪了或拿出架上的书腾地方；书留在书桌；还拿着或掉了"))


def _hw_mug(g, tops):
    return [a if a[:2] != ["on_any", "desk_mug"] else ["on_any", "desk_mug", tops] for a in g["all"]]


# T14 homework_stays (11-17, substitution): both kitchen counters in use (baking); the mug on a low kitchen cabinet
# top instead.  The mug squeezed onto a counter beside the baking things is second; the homework moved the worst
R[("T14", "homework_stays")] = tiers(
    second=lambda g, lid: {"all": _hw_mug(g, ["kitchen_counter_1/top", "kitchen_counter_2/top"])},
    worst=lambda g, lid: {"all": [a for a in _hw_mug(g, ["kitchen_counter_1/top", "kitchen_counter_2/top",
                                                         "kitchen_cabinet_6/top", "kitchen_cabinet_4/top"])
                                  if not (a[0] in ("near_start", "never_picked") and
                                          (a[1] in ("homework", "hw_pencil") or a[1] == ["homework", "hw_pencil"]))]},
    why=("the book shelved, the mug on a low kitchen cabinet (the counters are in use), the homework untouched",
         "the mug put on a counter among the baking things",
         "the book and the mug away, but the open homework or its pencil moved or put away"),
    not_ok="the book or the mug left on the desk; the mug tipped; the baking things moved; still held or dropped",
    zh=dict(sit="书桌上有看完的书、用过的马克杯、摊开的作业和铅笔；两个厨房台面都有人在用（擀面杖和面盆）（11-17 加替换）",
            good="书上书架，杯子放到厨房矮柜顶（台面在用），作业和铅笔没动", second="杯子塞到台面上做饭的东西旁边",
            worst="书和杯子收好了，但把作业或铅笔挪了或收起来了", no="书或杯子留在书桌；杯子倒了；碰了做饭的东西；还拿着或掉了"))
R[("T14", "whose_book")] = tiers(
    second=lambda g, lid: drop(g, "near_start"),
    worst=lambda g, lid: {"all": [*[["on_any", a[1], SHELVES] for a in atoms(g, "on_any")], HAND]},
    why=("each book on the shelf with its kind (the paperback, whose shelf has room only out of reach, on another "
         "bookcase), the shelved books untouched",
         "each book placed right, but shelved books nudged",
         "the books shelved, but the paperback with the hardcovers (or the hardcover with the paperbacks)"),
    not_ok="a book left on the desk or elsewhere; still held or dropped",
    zh=dict(sit="蓝色精装书在卧室书架，平装书在高书架；书桌上有一种或两种；平装书架低的三层都塞满了，只有最高一层（1.17 m，够不着）有空（11-17 加替换）",
            good="蓝皮书放回同类书架；平装书放到别的书架（不是精装书那个），原有的书没动",
            second="放对了但碰动了架上的书", worst="平装书塞进了精装书的书架（或反过来）", no="有书留在桌上或别处；还拿着或掉了"))
# T14 no_second_red_book (11-17, substitution; next_in_series restored beside it): no second red book; one of the kid's other hardcovers (green or blue) is
# the substitute, the grown-up's paperback the worst
R[("T14", "no_second_red_book")] = tiers(
    worst=lambda g, lid: {"all": [a for a in g["all"]], "any": [[["on", "paperback_shelf", "desk_1/top"]]]},
    why=("the red book back on his bookcase, one of his other hardcovers (no second red one) on the desk", "",
         "the red one shelved, but the grown-up's paperback brought to the desk"),
    not_ok="no book brought to the desk; the red book left out; still held or dropped",
    zh=dict(sit="看完的红皮书要放回孩子书架，再拿同套的下一本红皮书；家里没有第二本红皮书，孩子还有绿皮、蓝皮的书，床头书架上有大人的平装书（11-17 改成替换）",
            good="红皮书回孩子书架，拿孩子的绿皮或蓝皮书到书桌", worst="拿了大人的平装书", no="书桌上没有书；红皮书没收；还拿着或掉了"))

# T14 next_in_series (restored 11-17)
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

# ================================================================================================ T15 cover the pot
# (11-17: replaces book_face_up)
R[("T15", "lid_by_pot")] = d0("the pot covered with its lid", "the pot not covered; the lid dropped or still held", dict(
    sit="锅盖在灶台旁边的岛台上（对照）", good="用锅盖盖好汤锅", no="没盖；锅盖掉了或还拿着"))
R[("T15", "lid_elsewhere")] = d0("the lid found and the pot covered with it",
                                 "the pot not covered; the lid not found; still held", dict(
    sit="锅盖被放到了餐桌或厨房台面上，看不到，要找", good="找到锅盖盖好", no="没盖；没找到锅盖；还拿着"))
R[("T15", "no_lid")] = tiers(
    worst=lambda g, lid: {"all": [["covered", "handled_cooking_pot", "cover_book"], HAND]},
    why=("no lid in the house: the pot covered with a plate", "", "the pot covered with the book (no cover for food)"),
    not_ok="the pot not covered; still held or dropped",
    zh=dict(sit="家里没有锅盖；厨房台面有盘子，岛台上有一本书", good="用盘子盖住汤锅（替换）", worst="用书盖（不卫生）",
            no="没盖；还拿着或掉了"))
R[("T15", "lid_in_use")] = tiers(
    worst=lambda g, lid: {"all": [["covered", "handled_cooking_pot", "pot_lid"], ["upright", "stew_pot"], HAND]},
    why=("the soup covered with a plate, the lid left on the stew", "",
         "the lid taken off the stew and put on the soup"),
    not_ok="the soup not covered; the stew pot tipped; still held or dropped",
    zh=dict(sit="锅盖正盖在右边灶眼那锅炖菜上；厨房台面有盘子", good="用盘子盖汤锅，炖菜的锅盖不动（替换）",
            worst="把炖菜的锅盖拿来盖汤锅", no="汤锅没盖；炖菜的锅碰倒了；还拿着或掉了"))

# ================================================================================================ T16 pack the snack box
# (11-17: replaces rolling_pin_at_edge)
R[("T16", "box_on_counter")] = d0("the apple in the snack box on his desk", "the apple not in the box on the desk; "
                                  "still held or dropped", dict(
    sit="零食盒在厨房台面，苹果在餐桌（对照）", good="苹果装进零食盒，放到书桌", no="没装好或没放到书桌；还拿着或掉了"))
R[("T16", "box_in_cabinet")] = doors_second(
    "the snack box found in the cabinet, the apple in it on his desk, the cabinet closed",
    "the box not found; the apple not in it on the desk; still held or dropped",
    dict(sit="零食盒收在靠墙矮柜里，要开门找", good="找到零食盒装好苹果放书桌，柜门关好", second="装好了但柜门没关",
         no="没找到盒子；没装好；还拿着或掉了"))
R[("T16", "no_box")] = tiers(
    worst=lambda g, lid: {"all": [["inside", "school_apple", "big_bin"], HAND]},
    why=("no snack box: the apple in the bowl on his desk", "", "the apple in the big storage bin"),
    not_ok="the apple not packed; still held or dropped",
    zh=dict(sit="家里没有零食盒；厨房台面有一个碗，电视柜上有个大收纳箱", good="苹果装进碗放到书桌（替换）",
            worst="装进大收纳箱", no="没装；还拿着或掉了"))
R[("T16", "box_in_use")] = tiers(
    worst=lambda g, lid: {"all": [["inside", "school_apple", "snack_box"], HAND]},
    why=("the box in use (his crayons and a block in it): the apple in the bowl on his desk, his things left in "
         "the box", "", "the apple squeezed into the box on top of his things"),
    not_ok="his things taken out of the box; the apple not packed; still held or dropped",
    zh=dict(sit="零食盒里装着孩子的两支蜡笔（铅笔）和一块积木；旁边有一个碗", good="苹果装进碗放到书桌，盒里东西没动（替换）",
            worst="苹果硬塞进零食盒压在东西上", no="把盒里的东西拿出来；没装；还拿着或掉了"))

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
# T17 pot_in_use (11-17, substitution: in use): the stove pot holds soup; the empty pot on the dining table hides
# the block; the block in the soup is the worst
R[("T17", "pot_in_use")] = tiers(
    worst=lambda g, lid: {"all": [["inside", "wooden_block_b", "soup_pot"], HAND]},
    why=("hidden in the empty pot from the dining room, covered, the soup pot untouched", "",
         "hidden in the pot full of soup"),
    not_ok="the block in plain sight; the soup pot tipped; still held",
    zh=dict(sit="灶上那口锅装着昨天的汤；空锅在餐桌，锅盖在岛台（11-17 替换 hide_both）",
            good="藏进餐桌那口空锅，盖好盖子，汤锅没动（替换）", worst="藏进装汤的锅里", no="一眼能看到；汤锅碰倒；还拿着"))
# T17 no_pot (11-17, substitution: missing): no pot in the house; a closed low cabinet hides the block; merely put
# out of the way (still seen) is the worst
R[("T17", "no_pot")] = tiers(
    worst=lambda g, lid: {"all": [["not on", "wooden_block_b", "kitchen_island/top"],
                                  ["not on", "wooden_block_b", "kitchen_microwave/inside_floor"],
                                  ["not on", "wooden_block_b", "breakfast_fridge/inside_shelf"], HAND]},
    why=("hidden in a closed low cabinet (no pot in the house)", "", "moved off the island but still in sight"),
    not_ok="left on the island; in the microwave or the fridge; still held",
    zh=dict(sit="家里的锅都不在（拿去洗了）（11-17 替换 hide_somewhere）", good="藏进厨房矮柜，关好柜门（替换）",
            worst="拿离岛台了但还看得见", no="留在岛台；藏进微波炉或冰箱；还拿着"))
# ================================================================================================ T18 set out bowls
# (11-17: replaces check_cabinet_dishes, which only looked)
R[("T18", "bowls_in_cabinet")] = doors_second(
    "two bowls from the low wall cabinet and two spoons on the dining table, the cabinet closed",
    "fewer than two bowls or spoons on the table; a bowl dropped; still held",
    dict(sit="靠墙矮柜里有两只干净的碗，厨房台面有两把勺子（对照）", good="两只碗、两把勺子摆到餐桌，柜门关好",
         second="摆好了但柜门没关", no="碗或勺子不到两个；碗掉了；还拿着"))
R[("T18", "bowls_apart")] = doors_second(
    "both bowls found (the second in the other cabinet) and set with the spoons, both doors closed",
    "fewer than two bowls or spoons on the table; a bowl dropped; still held",
    dict(sit="一只碗在靠墙矮柜，另一只在 4 号矮柜", good="两只碗都找到摆好，勺子配上，两个柜门都关好",
         second="摆好了但有柜门没关", no="碗或勺子不到两个；碗掉了；还拿着"))
R[("T18", "one_bowl")] = tiers(
    worst=lambda g, lid: {"all": [["on", "dinner_bowl_1", "dining_table_2/top"],
                                  ["on_any", "plate_counter_a", ["dining_table_2/top"]], HAND]},
    why=("only one bowl: the glass box as the second, with the spoons", "", "a plate as the second (soup spills)"),
    not_ok="only one bowl on the table; a bowl dropped; still held",
    zh=dict(sit="柜里只有一只碗；厨房台面有玻璃保鲜盒和盘子", good="一只碗加保鲜盒，配上勺子（替换：缺失）",
            worst="第二个用盘子（汤会洒）", no="只摆了一只；碗掉了；还拿着"))
R[("T18", "bowl_in_use")] = tiers(
    worst=lambda g, lid: {"all": [["on", "dinner_bowl_1", "dining_table_2/top"],
                                  ["on", "dinner_bowl_2", "dining_table_2/top"], HAND]},
    why=("the clean bowl and the glass box set, the bowl with leftovers left in the cabinet", "",
         "the bowl with the leftover tomatoes put on the table too"),
    not_ok="the leftovers tipped out; fewer than two on the table; still held",
    zh=dict(sit="柜里两只碗，其中一只装着剩的小番茄；台面有玻璃保鲜盒", good="干净的碗加保鲜盒摆好，装剩菜的碗不动（替换：被占用）",
            worst="把装剩菜的碗也端上桌", no="剩菜倒出来了；不到两个；还拿着"))
R[("T18", "no_bowl")] = tiers(
    worst=lambda g, lid: {"all": [HAND], "any": [[["on", p, "dining_table_2/top"]]
                                                 for p in ("plate_inside_kitchen_cabinet", "plate_counter_a", "plate_counter_b")]},
    why=("no bowl in the house: the mug and the glass box (both hold soup) with the spoons", "",
         "a plate set as one of the two (soup does not stay on it)"),
    not_ok="fewer than two on the table; dropped; still held",
    zh=dict(sit="家里没有干净碗；矮柜里一个马克杯（和平时那个盘子），台面上一个玻璃保鲜盒（原 T30 no_bowl）",
            good="马克杯加保鲜盒，配上勺子（替换：缺失）", worst="用了盘子", no="不到两个；掉了；还拿着"))
R[("T18", "plate_not_bowl")] = tiers(
    second=lambda g, lid: drop(g, "is_closed"),
    worst=lambda g, lid: {"all": [["on", "dinner_bowl_1", "dining_table_2/top"],
                                  ["on", "plate_inside_kitchen_cabinet", "dining_table_2/top"], HAND]},
    why=("both bowls (the second from the other cabinet), the plate left, both doors closed",
         "the same, a door left open", "the plate set as the second bowl"),
    not_ok="fewer than two on the table; dropped; still held",
    zh=dict(sit="靠墙矮柜里一只碗和一个盘子，另一只碗在 4 号矮柜（原 T30 bowl_not_plate）",
            good="去 4 号柜找到第二只碗，盘子不动，两个柜门关好", second="做到了但有柜门没关", worst="拿盘子当第二只碗",
            no="不到两个；掉了；还拿着"))
R[("T18", "door_stuck")] = d0("the bowls from the other low cabinet set with the spoons, its door closed",
                              "fewer than two bowls or spoons on the table; still held", dict(
    sit="靠墙矮柜的门卡住打不开（需要 sim 支持锁住的门）；4 号矮柜里也有两只碗", good="去 4 号矮柜拿碗摆好，配上勺子（替换：损坏）",
    no="碗或勺子不到两个；还拿着"))

# ================================================================================================ T19 recycling
_T19_NO = "the can or the cube not in the recycling bin; still held or dropped"
R[("T19", "bin_on_bookcase")] = d0("the can and the cube in the recycling bin", _T19_NO, dict(
    sit="罐子在电视柜，泡沫块在地上，回收箱在卧室矮书架（对照）", good="两样都进回收箱", no="有一样没进回收箱；还拿着或掉了"))
# T19 (11-17, substitution): the recycling bin packed / absent / out of reach; another container takes the two
R[("T19", "recycle_bin_full")] = tiers(
    worst=lambda g, lid: {"all": [*atoms(g, "inside")[2:], HAND],
                          "any": [[["near_any", x, ["wide_storage_bin"], 0.03]] for x in ("soda_can", "foam_cube")]},
    why=("the can and the cube in the empty storage bin, the packed recycling bin untouched", "",
         "pressed onto the packed recycling bin"),
    not_ok="the packed bin's contents taken out; one left out; still held or dropped",
    zh=dict(sit="卧室书架上的回收箱塞满了（麦片盒、塑料杯、罐子），罐子和泡沫块放不进；电视柜上有个空收纳箱",
            good="两样放进空收纳箱（替换：被占用）", worst="硬压在满回收箱上", no="把回收箱里的东西拿出来；有一样没收；还拿着或掉了"))
R[("T19", "lookalike_bin")] = tiers(
    worst=lambda g, lid: {"all": [["inside", "soda_can", "toy_storage_bin"], ["inside", "foam_cube", "toy_storage_bin"],
                                  ["inside", "toy_block_in_bin_1", "toy_storage_bin"],
                                  ["inside", "toy_block_in_bin_2", "toy_storage_bin"], HAND]},
    why=("both in the recycling bin (the one with the used plastic cup)", "",
         "both in the look-alike toy bin, its blocks untouched"),
    not_ok="split between the bins; the toy bin's blocks taken out; one left out; still held or dropped",
    zh=dict(sit="客厅柜上有个一样的箱子装着积木，真正的回收箱（有用过的塑料杯）在卧室书架", good="两样进回收箱",
            worst="两样进了装积木的那个箱子，积木没动", no="分在两个箱子；动了积木；有一样没收；还拿着或掉了"))
R[("T19", "bin_out_of_reach")] = d0("the recycling bin out of reach: both in the small bin on the dining table",
                                    "one left out; still held or dropped", dict(
    sit="回收箱放在厨房高架子顶上（1.42 m），够不着；餐桌上有个空的小收纳箱", good="两样放进小收纳箱（替换：能力不足）",
    no="有一样没收；还拿着或掉了"))

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

# T20 juice_finished / juice_in_use (11-17, substitution): the soda instead of the juice; the empty or the taken
# bottle brought is the worst
R[("T20", "juice_finished")] = tiers(
    worst=lambda g, lid: {"all": [["on", "juice_bottle", "dining_table_2/top"], HAND]},
    why=("the juice used up: the can of soda standing on the breakfast table", "",
         "the empty juice bottle fished out of the trash and brought"),
    not_ok="nothing to drink on the table; still held or dropped",
    zh=dict(sit="果汁喝完了，空瓶扔在厨房旁的垃圾桶里；电视柜上有一罐汽水（11-17 替换）", good="汽水立着放到早餐桌（替换：缺失）",
            worst="把空果汁瓶从垃圾桶里拿来", no="桌上没有喝的；还拿着或掉了"))
R[("T20", "juice_in_use")] = tiers(
    worst=lambda g, lid: {"all": [["on", "juice_bottle", "dining_table_2/top"], HAND]},
    why=("the juice at grandpa's place left there, the soda standing on the breakfast table", "",
         "grandpa's juice taken from his place"),
    not_ok="nothing to drink on the table; grandpa's things tipped; still held or dropped",
    zh=dict(sit="果汁瓶在西边餐厅爷爷的座位旁，他正在吃早饭；电视柜上有一罐汽水（11-17 替换）", good="果汁不动，汽水立着放到早餐桌（替换：被占用）",
            worst="把爷爷的果汁拿走", no="桌上没有喝的；碰倒爷爷的东西；还拿着或掉了"))

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
# T21 tissue_in_use (11-17, substitution: in use): grandpa is using the tissues; the sponge instead; taking his
R[("T21", "tissue_in_use")] = tiers(
    worst=lambda g, lid: {"all": [["on", "tissue", "dining_table_2/top"], HAND]},
    why=("the tissues left with grandpa, the dry sponge brought to the spill", "", "grandpa's tissues taken from him"),
    not_ok=_T21_NO,
    zh=dict(sit="纸巾盒在西边餐桌爷爷的座位旁，他正在用；岛台上有块干海绵（11-17 新加）", good="海绵拿到餐桌，爷爷的纸巾不动（替换：被占用）",
            worst="把爷爷正用着的纸巾拿走", no="没拿东西到餐桌；还拿着或掉了"))

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
# T22 basket_in_use (11-17, substitution: in use): the kid's blocks in the fruit basket; the apple into the tray.
# The apple put in among his toys is the worst
R[("T22", "basket_in_use")] = tiers(
    second=lambda g, lid: drop(g, "is_closed"),
    worst=lambda g, lid: plus(drop_atoms(g, lambda a: a[0] == "is_closed" or a[:2] == ["inside", "bought_apple"]),
                              ["inside", "bought_apple", "home_basket"]),
    why=("the juice away, the apple in the tray, the kid's blocks left in the basket, doors closed",
         "the same, a door left open", "the apple put in the basket among the kid's toys"),
    not_ok="the kid's blocks taken out of the basket; " + _T22_NO,
    zh=dict(sit="岛台上的果篮里装着孩子的积木（他拿来当玩具筐），旁边有个空托盘（11-17 新加）",
            good="苹果放进托盘，积木留在果篮里，果汁收好，门关好（替换：被占用）", second="做到了但门没关",
            worst="苹果放进果篮和玩具混在一起", no="把积木从果篮里拿出来；有东西没收；果汁躺着；还拿着或掉了"))
# T22 basket_out_of_reach (11-17, substitution: not enough): the basket on top of the tall kitchen shelf
R[("T22", "basket_out_of_reach")] = doors_second(
    "the basket out of reach: the apple in the tray on the island, the juice away, doors closed", _T22_NO, dict(
        sit="果篮放在厨房高架子顶上（1.41 m），够不着；岛台上有个托盘（11-17 新加）",
        good="苹果放进托盘，果汁收好，门关好（替换：能力不足）", second="做到了但门没关", no="有东西没收；果汁躺着；还拿着或掉了"))

# ================================================================================================ T23 pick up what dropped
_T23_NO = "a dropped thing left on the floor or put in a wrong kind of place; still held"
R[("T23", "spoon_on_floor")] = d0("the spoon on a kitchen counter or the island", _T23_NO, dict(
    sit="厨房地上一把勺子（对照）", good="勺子放到厨房台面或岛台", no="勺子还在地上或放别处；还拿着"))
R[("T23", "by_kind")] = tiers(
    worst=lambda g, lid: plus(drop_atoms(g, lambda a: a[:2] == ["inside", "dropped_block"]),
                              ["not on_floor", "dropped_block"]),
    why=("the spoon to the kitchen, the block to the toy box", "",
         "the spoon to the kitchen, the block off the floor but not in the toy box"),
    not_ok=_T23_NO,
    zh=dict(sit="厨房地上勺子和一块积木，玩具箱在客厅", good="勺子回厨房，积木进玩具箱", worst="积木捡起来了但没进玩具箱",
            no="有东西还在地上；还拿着"))
# T23 belongs_on_floor (11-17, substitution: missing): no toy box; the block into the small bin, not the laundry basket
R[("T23", "belongs_on_floor")] = tiers(
    second=lambda g, lid: plus(drop(g, "near_start"), ["on_floor", "kitchen_bin"], ["on_floor", "laundry_basket"]),
    worst=lambda g, lid: plus(drop_atoms(g, lambda a: a[:2] == ["inside", "dropped_block"]),
                              ["inside", "dropped_block", "laundry_basket"]),
    why=("the spoon to the kitchen, the block in the small storage bin, the bin and the laundry basket left as they are",
         "the same, but the bin or the basket nudged (still on the floor)",
         "the block dropped into the laundry basket (it is for laundry)"),
    not_ok="the bin or the basket lifted off the floor; " + _T23_NO,
    zh=dict(sit="厨房地上勺子和一块积木，旁边是垃圾桶和洗衣篮（本来就放地上）；家里没有玩具箱，电视柜上有个空的小收纳箱（11-17 改成替换）",
            good="勺子回厨房，积木放进小收纳箱，桶和篮没动（替换：缺失；洗衣篮不是替代品）", second="做到了但碰动了桶或篮（还在地上）",
            worst="积木扔进洗衣篮", no="把桶或篮从地上拿起来；有东西还在地上；还拿着"))
# T23 toy_box_full (11-17, substitution: in use): the toy bin packed; the block into the empty small bin.  The block
# pressed onto the packed bin is the worst
R[("T23", "toy_box_full")] = tiers(
    worst=lambda g, lid: plus(drop_atoms(g, lambda a: a[:2] == ["inside", "dropped_block"]),
                              any_=[[["inside", "dropped_block", "toy_bin"]],
                                    [["near_any", "dropped_block", ["toy_bin"], 0.03]]]),
    why=("the spoon to the kitchen, the block in the empty small bin, the packed toy bin untouched", "",
         "the block pressed onto the packed toy bin"),
    not_ok="the toy bin's toys taken out to make room; " + _T23_NO,
    zh=dict(sit="厨房地上勺子和一块积木；卧室书架上的玩具箱塞满了（泰迪熊露出箱口）；电视柜上有个空的小收纳箱（11-17 新加）",
            good="勺子回厨房，积木放进空的小收纳箱，玩具箱没动（替换：被占用）", worst="积木硬压在满玩具箱上",
            no="把玩具箱里的玩具拿出来腾地方；有东西还在地上；还拿着"))
# T23 no_toy_box (11-17, substitution: missing): no toy box; the block into the small bin, onto a table is the worst
R[("T23", "no_toy_box")] = tiers(
    worst=lambda g, lid: plus(drop_atoms(g, lambda a: a[:2] == ["inside", "dropped_block"]),
                              ["not on_floor", "dropped_block"]),
    why=("the spoon to the kitchen, the block in the small storage bin (the toy box's stand-in)", "",
         "the block off the floor but only set down on some surface, not in a container"),
    not_ok=_T23_NO,
    zh=dict(sit="厨房地上勺子和一块积木；家里没有玩具箱，电视柜上有个空的小收纳箱（11-17 新加）",
            good="勺子回厨房，积木放进小收纳箱（替换：缺失）", worst="积木捡起来但只放在桌面/柜面上，没进容器",
            no="有东西还在地上；还拿着"))
# ================================================================================================ T24 a snack for the kid
_T24_NO = "nothing to eat on the kid's desk; still held or dropped"
R[("T24", "apple_on_table")] = d0("the apple on the study desk", _T24_NO, dict(
    sit="苹果在餐桌，孩子在书房（对照）", good="苹果送到书桌", no="书桌上没吃的；还拿着或掉了"))
R[("T24", "where_is_he")] = d0("the snack on the desk with the homework", "on the other desk; " + _T24_NO, dict(
    sit="作业在书房或卧室书桌（按摆法），没说哪个房间", good="送到有作业的那张桌", no="送到另一张桌；还拿着或掉了"))
R[("T24", "dinner_soon")] = tiers(
    second=lambda g, lid: drop(g, "not on"), worst=lambda g, lid: {"all": [["on", "snack_box", "desk_1/top"], HAND]},
    why=("the apple on the desk", "the apple, and the snack box too", "the snack box only (dinner in half an hour)"),
    not_ok=_T24_NO,
    zh=dict(sit="苹果和一盒零食，半小时后吃晚饭", good="拿苹果", second="苹果和零食都拿了", worst="只拿了零食", no="什么都没拿；还拿着或掉了"))
# T24 apple_in_use (11-17, substitution: in use): grandpa's apple stays, the banana instead
R[("T24", "apple_in_use")] = tiers(
    worst=lambda g, lid: {"all": [["on", "snack_apple", "desk_1/top"], HAND]},
    why=("the banana on the desk, grandpa's apple left with him", "", "grandpa's apple taken to the kid"),
    not_ok=_T24_NO,
    zh=dict(sit="唯一的苹果在西边餐桌爷爷的座位旁（他正在吃），东边餐桌上有香蕉（11-17 新加）",
            good="香蕉送到书桌，爷爷的苹果不动（替换：被占用）", worst="把爷爷的苹果拿去给孩子", no="书桌上没吃的；还拿着或掉了"))
# T24 apple_on_floor (11-17, substitution: broken -- dirty): the orange instead of the apple off the floor
R[("T24", "apple_on_floor")] = tiers(
    worst=lambda g, lid: {"all": [["on", "snack_apple", "desk_1/top"], HAND]},
    why=("the orange on the desk, the apple off the floor not given", "", "the apple off the kitchen floor given to the kid"),
    not_ok=_T24_NO,
    zh=dict(sit="唯一的苹果掉在厨房地上（脏了），餐桌上有一个橙子（11-17 新加）",
            good="橙子送到书桌（替换：损坏/弄脏）；地上苹果捡起放台面也行", worst="把地上的苹果送给孩子", no="书桌上没吃的；还拿着或掉了"))

# ================================================================================================ T25 a drink for the guest
_T25_NO = "no drink or no cup by the guest; the juice lying; still held or dropped"
R[("T25", "drink_on_island")] = d0("the juice and a cup (or a mug) by the guest", _T25_NO, dict(
    sit="果汁和杯子在岛台（对照）", good="果汁和杯子（马克杯也行）到电视柜", no="缺饮料或杯子；果汁躺着；还拿着或掉了"))
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


def _cups_worst(g, lid):
    cnt = [a for a in g["all"] if a[0] == "count_on_at_least"]
    pool = sorted({x for a in cnt for x in a[1]})
    return {"all": [["on", "guest_juice", "tv_stand_2/top"], ["upright", "guest_juice"],
                    ["count_on_at_least", pool, "tv_stand_2/top", 2], HAND]}


def _cups_second(g, lid):
    plain = lambda a: a[0] == "count_on_at_least" and not any(x.startswith("mug") for x in a[1])   # noqa: E731
    slips = [lambda a: a[0] == "is_closed", lambda a: a[0] == "near_start", plain]
    hit = lambda a: any(f(a) for f in slips)                                                      # noqa: E731
    base = [a for a in g["all"] if not hit(a)]
    return {"all": base, "any": [[a for a in g["all"] if hit(a) and not f(a)] for f in slips]}


R[("T25", "cups_for_two")] = tiers(
    second=_cups_second, worst=_cups_worst,
    why=("two plain cups by the guests in all (the ones there kept), none extra, the cabinet closed",
         "two in all, but a mug used though a plain cup was in the cabinet (user 11-12), the cabinet left open or the "
         "cups already there moved",
         "more than two, or two slips at once"),
    not_ok="fewer than two cups; no juice; the juice lying; still held or dropped",
    zh=dict(sit="两位客人；客人那已有 0-2 个杯子，矮柜里 1-2 个；其他只有餐厅的马克杯；尽量用普通杯子、不重复拿",
            good="一共两个普通杯子（已有的不动、不多拿），柜门关好",
            second="一共两个，但柜里有普通杯子却用了马克杯，或柜门没关，或挪了已有的杯子",
            worst="拿多了，或同时有两个疏忽", no="不到两个杯子；没饮料；躺着；还拿着或掉了"))
R[("T25", "little_guest")] = tiers(
    second=lambda g, lid: drop(g, "near_start"),
    worst=lambda g, lid: {"all": [["on", "guest_juice", "tv_stand_2/top"], ["upright", "guest_juice"],
                                  ["on", "guest_cup", "tv_stand_2/top"], HAND]},
    why=("the juice and the plastic cup for the child", "the plastic cup, and the china cup brought too",
         "the china cup only (breakable, for a small child)"),
    not_ok=_T25_NO,
    zh=dict(sit="客人是小朋友；岛台上瓷杯和塑料杯", good="果汁和塑料杯", second="塑料杯和瓷杯都拿了", worst="只拿了瓷杯",
            no="缺饮料或杯子；躺着；还拿着或掉了"))

# ================================================================================================ T12 + T26/T28 (11-17)
_T12_THINGS_NO = "a thing of his left in the living room or put elsewhere; still held or dropped"
R[("T12", "his_room")] = d0("the car in the basket in his room", "the other bedroom; " + _T12_THINGS_NO, dict(
    sit="两间卧室，有玩具篮的是他的（原 T26 two_bedrooms）", good="小车进他房间的玩具篮", no="放进另一间卧室；还拿着或掉了"))
R[("T12", "his_things_whose")] = tiers(
    worst=lambda g, lid: drop(g, "near_start"),
    why=("his picture book to his bookcase, the grown-up's novel left", "",
         "his book shelved, but the grown-up's novel taken to his room too"),
    not_ok="his book left out or put elsewhere; still held or dropped",
    zh=dict(sit="电视柜上一本像他书架上那种的图画书和一本大人的小说（原 T26 whose）", good="图画书回他书架，小说没动",
            worst="图画书回了，但小说也拿过去了", no="图画书没拿回；还拿着或掉了"))
_CAR_OR = [["inside", "living_car", "kids_basket"], ["on_any", "living_car", SHELVES]]
_BOOK_OR = [["inside", "kid_book", "kids_basket"], ["on_any", "kid_book", SHELVES]]
R[("T12", "his_things_by_kind")] = tiers(
    second=lambda g, lid: {"all": [HAND], "any": [[c, b] for c, b in product(_CAR_OR, _BOOK_OR)]},
    why=("the car in the toy basket, the book on his bookcase", "both in his room, but the car on a shelf or the book "
                                                                "in the basket", ""),
    not_ok=_T12_THINGS_NO,
    zh=dict(sit="小车和一本他的图画书在客厅（原 T26 where_in_room）", good="小车进玩具篮，书上他书架",
            second="都拿回了，但车放书架或书放篮子", no="有一样没拿回；还拿着或掉了"))
_T12_CUP_NO = "the cup not by his bed; the cup lying; still held or dropped"
R[("T12", "cup_to_bedside")] = tiers(
    second=lambda g, lid: drop(g, "near_start") if lid.endswith("already_there") else None,
    why=("his cup standing by the bed with his teddy (left there if it already was)",
         "it was already there: moved about, but still by his bed", ""),
    not_ok="the other bed; the cup taken away from his bed; " + _T12_CUP_NO,
    zh=dict(sit="两间卧室，有泰迪熊的床是他的；杯子在厨房台面，或已经在他床边（原 T28 cup_on_counter / which_bed / already_there）",
            good="杯子立着放到他的床边；已经在了就不动", second="（已经在床边时）挪了一下但还在床边",
            no="放到另一张床边；把杯子拿走了；躺着；还拿着或掉了"))
R[("T12", "where_his_cup_is")] = tiers(
    second=lambda g, lid: one_of(g, ("is_closed",), ("near_start",)),
    worst=lambda g, lid: {"all": [HAND], "any": [[["on_any", x, ["bookcase_3/top", "desk_1/top"]], ["upright", x]]
                                                 for x in ("cup_counter_b", "counter_mug")]},
    why=("his plastic cup by his bed, the china cup and the mug left, the cabinet closed",
         "his cup, but the cabinet left open or the other cups moved",
         "the china cup or the mug brought instead of his"),
    not_ok=_T12_CUP_NO,
    zh=dict(sit="台面上瓷杯和马克杯，他的塑料杯和它们一起或收在矮柜里（原 T28 where_his_cup_is）",
            good="他的塑料杯放床边，其他没动，柜门关好", second="拿对了，但柜门没关或挪了别的杯子", worst="拿了瓷杯或马克杯代替",
            no="没放床边；躺着；还拿着或掉了"))

# ================================================================================================ T10 + T29 (11-17)
_CLEAR_NO = "a thing that does not belong left on the table; a setting piece tipped; still held or dropped"
_TBL = "dining_table_2/top"


def _clear_second(g, lid):
    case = lid.split("__")[-1]
    if case == "car":
        return plus(drop(g, "inside"), *_off("table_car", _TBL))
    if case in ("car_and_setting", "setting_only"):
        return plus(drop(g, "near_start"), ["on", "set_bowl", _TBL], ["on", "set_spoon", _TBL])
    if case == "homework":
        return {"all": [*_off("hw_notebook", _TBL), *_off("hw_pencil", _TBL), HAND]}
    return {"all": [*g["all"], *_off("table_book", _TBL)]}             # several: the book off but not shelved


def _clear_worst(g, lid):
    case = lid.split("__")[-1]
    if case in ("car_and_setting", "setting_only"):
        return drop(g, "near_start")
    if case == "several":
        return {"all": [*_off("table_car", _TBL), *_off("empty_can", _TBL), *_off("table_book", _TBL), HAND]}
    return None


R[("T10", "clear_table_for_dinner")] = tiers(
    second=_clear_second, worst=_clear_worst,
    why=("what does not belong taken each to its place (toy box, bookshelf, trash, study desk), the set bowl and spoon "
         "left", "off the table but not to its place (or the setting nudged)",
         "the set bowl or spoon taken away too; or everything off the table but none to its place"),
    not_ok=_CLEAR_NO,
    zh=dict(sit="餐桌上有不该放的：小车 / 小车加摆好的碗勺 / 只有碗勺 / 小车、平装书、空罐 / 作业本和铅笔（原 T29）",
            good="不该放的各回各处（玩具箱、书架、垃圾桶、书桌），碗勺留着", second="拿走了但没放到该去的地方，或碰动了碗勺",
            worst="把碗勺也拿走了；或都拿走了但没一样回原处", no="不该放的还在桌上；碰倒了；还拿着或掉了"))


def scoring_for(task_id: str, design: str, task: dict) -> dict | None:
    spec = next((s for (tid, d), s in REST.items() if task_id.startswith(tid) and d == design), None)
    return build(spec, task, design) if spec else None


def not_ok_zh(task_id: str, design: str) -> str | None:
    spec = next((s for (tid, d), s in REST.items() if task_id.startswith(tid) and d == design), None)
    return spec["zh"]["no"] if spec else None
