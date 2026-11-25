"""11-24 (user): instructions name what the success condition checks.

After the first VLM baseline review, the user asked for instructions with qualifiers that match the scored outcome:
the object by what it holds or is ("the bowl of leftover oatmeal", "the glass box"), and the destination the
condition checks ("into the storage basket", "on his desk", "to the kitchen counter").  A planner that moved the
bin of blocks for "put the kid's toys away" read the old text literally.

Checked design by design against its conditions (11-24, user: the qualified text must not change what a design
tests); the designs whose test it would give away keep their own text (the block at the end of DESIGN).  Two things
stay as they were:
- what a design deliberately leaves to the planner (its note says "the instruction does not say ..."): which
  table, whose book, which desk, what to recycle, where a dropped thing belongs, how many bowls;
- the stand-in: an instruction names the ideal (the storage bin, the tissues), never what replaces it when it is
  missing, so a missing ideal is an explicit substitution.

Applied by define_tasks_v6.build() before loosen_1124 (which keeps is_closed only when the text says close).
    BASE    task prefix -> (en, zh): the task's own instruction, used by every layout without one
    DESIGN  (task prefix, design) -> (en, zh), or "BASE" to drop the design's own text for the task's
    LAYOUT  (task prefix, layout id) -> (en, zh), after DESIGN
"""
from __future__ import annotations

BASE = {
    "T03": ("Baking is done. Put the rolling pin and the spoon away together in the wide storage bin.",
            "烘焙结束了，把擀面杖和勺子一起收进那个宽的储物箱里。"),
    "T04": ("A guest is coming for tea. Set out a glass, standing upright, at the drinks spot on the low wall "
            "cabinet.",
            "有客人要来喝茶，在靠墙矮柜上的饮品角立着摆一个玻璃杯。"),
    "T07": ("Warm up the bowl of leftover oatmeal for breakfast to at least 40 C, then switch off what you used.",
            "把那碗剩燕麦粥热一下当早饭，至少热到 40 度，热完把用过的电器关掉。"),
    "T11": ("Lunch is over and the apple is still on the dining table. Put it away in the fruit basket.",
            "午饭吃完了，苹果还在餐桌上，把它收进果篮里。"),
    "T13": ("Breakfast is soon. Set a place at the dining table: a bowl, a cup and a spoon, standing together.",
            "快吃早饭了，在餐桌上摆一份餐具：碗、杯子和勺子，立着摆在一起。"),
    "T14": ("The kid finished reading. Put the book back on his bookcase.",
            "孩子看完书了，帮他把书放回他的书架上。"),
    "T16": ("The kid takes some fruit to school tomorrow. Put an apple into his snack box and leave the box on his "
            "study desk.",
            "孩子明天上学要带水果，把一个苹果装进他的零食盒，再把零食盒放到书房书桌上。"),
    "T21": ("Some soup got spilled at the dining table. Bring the tissues there and leave them on the table.",
            "餐桌上洒了点汤，把纸巾拿过去放在桌上。"),
    "T22": ("I just got back from the shop and left the shopping on the dining table. Please put it away in the "
            "kitchen.",
            "我刚买东西回来，放在餐桌上了，帮我收到厨房里。"),
    "T24": ("The kid is doing homework at the study desk and is hungry. Bring him something to eat and put it on "
            "his desk.",
            "孩子在书房书桌写作业饿了，给他拿点吃的，放到他书桌上。"),
    "T25": ("A guest is sitting in the living room. Bring him the juice and a cup, and put them on the TV stand in "
            "front of him.",
            "客人在客厅坐着，给他拿果汁和一个杯子，放到他面前的电视柜上。"),
    "T26": ("Take the things the kid left in the living room back to his room: toys into his toy basket, books "
            "onto his bookcase.",
            "把孩子落在客厅的东西拿回他房间：玩具放进他的玩具筐，书放到他的书架上。"),
    "T28": ("The kid is going to bed. Bring his cup to his bedside and leave it standing up.",
            "孩子要睡了，把他的水杯拿到床边，立着放好。"),
    "T29": ("Dinner is about to start. Take away what doesn't belong on the dining table and put each thing "
            "where it belongs: toys in the toy box, rubbish in the trash can, books on a bookshelf, homework on "
            "the study desk.",
            "要吃饭了，把餐桌上不该放的东西拿走，各放到该放的地方：玩具放进玩具箱，垃圾扔进垃圾桶，书放到书架上，"
            "作业放到书房书桌上。"),
    "T30": ("The soup is almost ready. Bring a clean bowl to the kitchen island next to the stove for serving it.",
            "汤快好了，拿一只干净的碗放到灶台旁边的岛台上准备盛汤。"),
}

DESIGN = {
    # T03: no storage bin in the house: the named bin is missing, the substitution is explicit
    ("T03", "no_bin_substitute"): "BASE",
    ("T04", "two_guests"): ("Two guests are coming for tea. Set out two glasses, standing upright and not touching "
                            "each other, at the drinks spot on the low wall cabinet.",
                            "有两位客人要来喝茶。在靠墙矮柜上的饮品角立着摆两个玻璃杯，两个别挨着。"),
    ("T05", "errand_combined"): ("The kid needs a pen for homework at the study desk; bring one there. Also, "
                                 "there is a used mug on that desk: take it back to the kitchen counter.",
                                 "孩子在书房书桌写作业要用钢笔，拿一支过去。另外，那张书桌上有个用过的马克杯，"
                                 "拿回厨房台面上。"),
    ("T07", "two_portions"): ("Breakfast needs two things warmed up: the bowl of oatmeal and the pot of leftover "
                              "soup, both to at least 40 C. Switch off what you used afterwards.",
                              "早饭要热两样：一碗燕麦粥和一锅剩汤，都要热到至少 40 度。热完把用过的电器关掉。"),
    ("T10", "after_dinner_clear"): ("Dinner is over; clear the dining table: rubbish goes in the trash can, "
                                    "leftover food in the fridge, used dishes back to the kitchen counter. The "
                                    "cereal boxes stay on the table.",
                                    "晚饭吃完了，把餐桌收拾干净：垃圾扔进垃圾桶，剩饭剩菜放进冰箱，用过的餐具拿回"
                                    "厨房台面。麦片盒留在桌上。"),
    ("T10", "guests_coming"): ("Guests arrive in ten minutes; make the living room presentable. Put whatever is "
                               "lying about where it belongs (rubbish in the trash can, dishes to the kitchen, toys "
                               "in the toy box), and leave things that belong where they are.",
                               "客人十分钟后到，把客厅收拾得能见人：乱放的东西各回各处（垃圾扔进垃圾桶，餐具拿回"
                               "厨房，玩具放进玩具箱），本来就该在那儿的东西别动。"),
    ("T11", "fruit_plate_for_guests"): ("The guests are watching TV in the living room. Bring them the apple and the "
                                        "orange from the dining table on a tray, and leave the tray on the TV stand "
                                        "in front of them.",
                                        "客人在客厅看电视，把餐桌上的苹果和橙子放在托盘上端过去，托盘放在他们面前的"
                                        "电视柜上。"),
    ("T12", "castle_stays"): ("It is nearly bedtime. Put the kid's toys away in the storage basket. Don't take "
                              "apart the block castle the kid built; the kid wants to keep building it tomorrow.",
                              "快到睡觉时间了，把孩子的玩具收进收纳篮里。他搭的积木城堡别拆，明天还要接着搭。"),
    # T21: no tissues in the house: the named tissues are missing, the substitution is explicit
    ("T21", "no_tissue"): "BASE",
    ("T21", "the_kids_side"): ("The kid spilled some soup at the dining table. Bring the tissues there and put "
                               "them on the kid's side of the table.",
                               "孩子吃饭把汤洒了，把纸巾拿过去，放在孩子那一边。"),
    ("T24", "dinner_soon"): ("The kid is doing homework at the study desk and is hungry. Bring him something to "
                             "eat and put it on his desk; dinner is in half an hour.",
                             "孩子在书房书桌写作业饿了，给他拿点吃的放到他书桌上。还有半小时就吃晚饭了。"),
    # T24 where_is_he: the room is still not named
    ("T24", "where_is_he"): ("The kid is doing homework and is hungry. Bring him something to eat and put it on "
                             "the desk where he is doing his homework.",
                             "孩子写作业饿了，给他拿点吃的，放到他写作业的那张书桌上。"),
    ("T24", "two_kids"): ("The kids are doing homework and are hungry. Bring them something to eat: one thing "
                          "for each, put by their homework.",
                          "孩子们在写作业，饿了，给他们拿点吃的：每人一样，放在各自的作业旁边。"),
    ("T25", "two_guests"): ("Two guests are sitting in the living room. Bring them the juice and a cup each, and "
                            "put them on the TV stand in front of them.",
                            "两位客人在客厅坐着，给他们拿果汁，每人一个杯子，放到他们面前的电视柜上。"),
    ("T25", "little_guest"): ("A little girl is visiting and sitting in the living room. Bring her some juice and "
                              "a cup, and put them on the TV stand in front of her.",
                              "来了个小朋友，在客厅坐着，给她拿果汁和一个杯子，放到她面前的电视柜上。"),
    # T30 how many: the count still follows from the spoons at the table
    ("T30", "how_many"): ("The soup is almost ready. Bring clean bowls to the kitchen island next to the stove "
                          "for serving it.",
                          "汤快好了，拿几只干净的碗放到灶台旁边的岛台上准备盛汤。"),
    ("T30", "bowls_in_cabinet"): ("The soup is almost ready. Bring clean bowls to the kitchen island next to the "
                                  "stove for serving it.",
                                  "汤快好了，拿几只干净的碗放到灶台旁边的岛台上准备盛汤。"),
    # -- 11-24 check: a design whose test the qualified text would give away keeps (or regains) its own text --
    # T03: whether the small bin holds the 22 cm rolling pin is the planner's call (small_container_present)
    ("T03", "small_bin_or_bedroom_bin"): ("Baking is done. Put the rolling pin and the spoon away together in one "
                                          "container.", "烘焙结束了，把擀面杖和勺子一起收进同一个容器里。"),
    # T04: the mug in view is a poor cup for an iced drink; "glass" would tell (no_cup)
    ("T04", "x6_gd_cup_in_cabinets"): ("A guest is coming and would like iced lemonade. Set out a cup for it, "
                                       "standing upright, at the drinks spot on the low wall cabinet.",
                                       "有客人要来，想喝冰柠檬水，在靠墙矮柜上的饮品角立着摆个杯子。"),
    # T11: where the fruit is kept and where the snack goes are the planner's (storage_place)
    ("T11", "leave_one_for_kid"): ("Lunch is over. Put the fruit on the table away, but leave one for the kid doing "
                                   "homework in the study as a snack. The kid doesn't like oranges.",
                                   "午饭吃完了，把桌上的水果收起来，给在书房写作业的孩子留一个当点心。孩子不爱吃橙子。"),
    # T14: where each thing belongs is the test (category_rule)
    ("T14", "homework_stays"): ("The kid finished reading. Tidy up his desk and put each thing where it belongs "
                                "best; he will go on with his homework tomorrow.",
                                "孩子看完书了，把他的书桌收拾一下，东西都放到最合适的地方。作业他明天还要接着写。"),
    # T25: on one seed the fridge holds a soda, not juice: "juice" would contradict the cold drink scored best
    ("T25", "cold_one"): ("It's a hot day. A guest is sitting in the living room; bring him something to drink "
                          "and a cup, and put them on the TV stand in front of him.",
                          "天很热，客人在客厅坐着，给他拿点喝的和一个杯子，放到他面前的电视柜上。"),
    # T26: his room is the one with the toy basket (two_bedrooms); where in his room things go (where_in_room,
    # whose, bear_to_bed) -- the basket and the bookcase would tell
    **{("T26", d): ("Take the things the kid left in the living room back to his room.",
                    "把孩子落在客厅的东西拿回他房间。") for d in ("two_bedrooms", "where_in_room", "whose")},
    ("T26", "bear_to_bed"): ("The kid is going to bed. Take the things he left in the living room back to his room.",
                             "孩子要睡觉了，把他落在客厅的东西拿回他房间。"),
    # T29: where each thing goes is the test (storage_place)
    **{("T29", d): ("Dinner is about to start. Take away what doesn't belong on the dining table.",
                    "要吃饭了，把餐桌上不该放的东西拿走。") for d in ("homework_on_table", "several")},
    # T30: "clean" would tell the clean bowl from the full one (referent_clue); the place stays named
    ("T30", "bowl_not_plate"): ("The soup is almost ready. Bring a bowl to the kitchen island next to the stove for "
                                "serving it.", "汤快好了，拿一只碗放到灶台旁边的岛台上准备盛汤。"),
}

_HEAT_OFF = ("to at least 40 C, then switch off what you used.", "至少热到 40 度，热完把用过的电器关掉。")
LAYOUT = {
    ("T07", f"vessel_decides_appliance__{k}"): (f"Warm up the {en} for breakfast {_HEAT_OFF[0]}",
                                                f"把{zh}热一下当早饭，{_HEAT_OFF[1]}")
    for k, en, zh in (("in_ceramic_bowl", "leftover oatmeal in the ceramic bowl", "陶瓷碗里的剩燕麦粥"),
                      ("in_glass_box", "leftovers in the glass food box", "玻璃饭盒里的剩饭"),
                      ("in_pot", "leftover soup in the pot", "锅里的剩汤"),
                      ("in_steel_box", "leftovers in the steel lunch box", "不锈钢饭盒里的剩饭"),
                      ("in_foil_tray", "leftovers in the foil takeout tray", "锡纸外卖盒里的剩饭"))
}


def apply(out: dict) -> list:
    """Set the instructions in place; returns [(task, layout, old en, new en)] for the layouts whose text changed."""
    log = []
    for t in out["tasks"]:
        p = t["task_id"][:3]
        before = {lid: v.get("instruction") or t["instruction"] for lid, v in t["variants"].items()}
        if p in BASE:
            t["instruction"], t["instruction_zh"] = BASE[p]
        for design, info in t.get("v6_variants", {}).items():
            text = DESIGN.get((p, design))
            for lid in info["layouts"] if text else ():
                v = t["variants"][lid]
                if text == "BASE":
                    v.pop("instruction", None)
                    v.pop("instruction_zh", None)
                else:
                    v["instruction"], v["instruction_zh"] = text
        for (q, lid), text in LAYOUT.items():
            if q == p and lid in t["variants"]:
                t["variants"][lid]["instruction"], t["variants"][lid]["instruction_zh"] = text
        for lid, v in t["variants"].items():
            now = v.get("instruction") or t["instruction"]
            if now != before[lid]:
                log.append((t["task_id"], lid, before[lid], now))
    return log
