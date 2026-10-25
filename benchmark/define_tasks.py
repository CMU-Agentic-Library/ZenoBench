"""Source of benchmark/tasks.json (python benchmark/define_tasks.py).

Every task: one fixed base scene + a local overlay, condition variants chosen
by the seed (does the failure / alternative condition hold?), random removal
of distractors, a GT goal, and scripted routes that prove each declared
nominal / fallback / alternative path is physically executable.

Route step: {"skill", "args", "expect": "ok"|"fail", "role"}.  A step with
"expect": "fail" must really fail in the simulator; the route continues in the
same simulator.  "kind" of a route: nominal | fallback (a real failure, then an
auxiliary skill repairs the state) | alternative (another legal object, skill
or destination reaches the same goal) | negative (documents a route that does
not work; never counted as passed).
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).with_name("tasks.json")

ISLAND = "kitchen_island/top"
BOOKCASE = "bookcase_2/top"
DINING = "dining_table_2/top"
CAB = "kitchen_cabinet_6"
CAB_TOP = CAB + "/top"
CAB2_TOP = "kitchen_cabinet_4/top"
TV = "tv_stand_2/top"
DESK = "desk_1/top"
STOVE_TOP = "kitchen_stove/top"
MW = "kitchen_microwave"
MW_FLOOR = "kitchen_microwave/inside_floor"
FRIDGE = "breakfast_fridge"
FRIDGE_SHELF = "breakfast_fridge/inside_shelf"
TOMATOES = ["cherry_tomato_1", "cherry_tomato_2", "cherry_tomato_3"]
CUPS = ["cup_counter_b", "cup_kitchen_cabinet", "cup_side_table"]


def S(skill, expect="ok", role="", **args):
    st = {"skill": skill, "args": args}
    if expect != "ok":
        st["expect"] = expect
    if role:
        st["role"] = role
    return st


def at(support, x, y, yaw=0.0):
    return {"support": support, "xy": [x, y], "yaw_deg": yaw}


def carry(obj, dest, kind="place"):
    """navigate to obj, pick, navigate to dest, place/drop."""
    out = [S("navigate", destination=obj), S("pick", object=obj), S("navigate", destination=dest)]
    out.append(S("place", object=obj, receptacle=dest) if kind == "place" else S("drop", object=obj, container=dest))
    return out


TASKS = []

# --------------------------------------------------------------------- T01
TASKS.append({
    "task_id": "T01_book_to_dining_table", "exp_id": "ZB-T01",
    "source": ["skill_library/tasks.json:flip_book (book)", "verification:g_expose_then_pick_book", "k_book", "b_books"],
    "instruction": "Someone left their paperback on the kitchen island. Bring it to the dining table so they can read over breakfast.",
    "instruction_zh": "有人把平装书落在厨房岛台上了，把它拿到餐桌上，方便吃早饭时看。",
    "scene": {"base": "tasks/kitchen_skills",
              "remove": ["mug", *TOMATOES, "soda_can", "juice_bottle"],
              "distractors": ["rolling_pin", "wooden_block_a", "wooden_block_b", "oatmeal",
                              "kitchen_sponge"]},
    "variants": {
        "overhang_ready": {"note": "the book already overhangs the island's front edge by about 6 cm",
                           "move": {"paperback_book": at(ISLAND, 7.62, 1.548, 90)}},
        "no_overhang": {"note": "the book overhangs the front edge by 1.5 cm only: the edge pinch fails until it is exposed",
                        "move": {"paperback_book": at(ISLAND, 7.62, 1.59, 90)}}},
    "watch": ["paperback_book"],
    "goal": {"all": [["on", "paperback_book", DINING], ["hand_empty", "right"]]},
    "diagnostics": ["bookcase top SimpleBookcaseFactory_6105320/surface_3 as destination: place_flat's final push "
                    "stalled and the book fell in front of the bookcase in 2/2 runs (benchmark/runs/dbg) -> the "
                    "destination was moved to the dining table"],
    "nominal": "nominal",
    "oracle": {"overhang_ready": "nominal", "no_overhang": "fallback_expose"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["overhang_ready"], "steps": [
            S("look", target=ISLAND), S("navigate", destination="paperback_book"),
            S("approach", target="paperback_book"), S("pick", object="paperback_book"),
            S("navigate", destination=DINING),
            S("place", object="paperback_book", receptacle=DINING, hint_xy=[3.72, 6.5])]},
        "fallback_expose": {"kind": "fallback", "variants": ["no_overhang"], "recovery": "Pick -> failure -> Expose -> Pick",
                            "steps": [S("look", target=ISLAND), S("navigate", destination="paperback_book"),
                                      S("pick", "fail", "failure", object="paperback_book"),
                                      S("expose", role="recovery", object="paperback_book"),
                                      S("pick", role="retry_after_recovery", object="paperback_book"),
                                      S("navigate", destination=DINING),
                                      S("place", object="paperback_book", receptacle=DINING, hint_xy=[3.72, 6.5])]}}})

# --------------------------------------------------------------------- T02
TASKS.append({
    "task_id": "T02_stack_blocks", "exp_id": "ZB-T02",
    "source": ["skill_library/tasks.json:stack_blocks", "k_blocks", "k_separate", "k_sweep"],
    "instruction": "Tidy the toy blocks left on the kitchen island: stack one wooden block on top of the other.",
    "instruction_zh": "收拾孩子落在岛台上的积木：把一块木积木叠到另一块上面。",
    "scene": {"base": "tasks/kitchen_skills", "remove": ["mug", *TOMATOES],
              "move": {"wooden_block_a": at(ISLAND, 7.3, 1.58), "wooden_block_b": at(ISLAND, 7.0, 1.60)},
              "distractors": ["paperback_book", "breakfast_spoon", "kitchen_sponge", "soda_can", "juice_bottle"]},
    "variants": {
        "clear": {"note": "the blocks stand 30 cm apart, every finger slot is free", "move": {}},
        "crowded": {"note": "block B is boxed in: the oatmeal bowl right behind it and the end of the rolling pin "
                            "right beside it (3 mm gaps), so both pinch axes of B have a finger slot taken",
                    "move": {"oatmeal": at(ISLAND, 7.0, 1.717), "rolling_pin": at(ISLAND, 6.864, 1.59, 0)}}},
    "watch": ["wooden_block_a", "wooden_block_b", "rolling_pin", "oatmeal"],
    "diagnostics": ["crowding B with block A (A then the stacking base next to the pin): the stack onto A failed "
                    "1/2 per recovery route (fingers blocked 3 cm above A, or B slid off) -> the bowl crowds B and A "
                    "stays in the open spot where stacking passed 2/2",
                    "A 12.5 cm behind the island's front edge (y 1.64): after separate the stack kept the approach park "
                    "beside A and the waist stalled at 0.51 of 0.65 rad, chest on the island edge, hand 5 cm above A "
                    "(2/4 separate runs) -> A 6.5 cm behind the edge (y 1.58)",
                    "5 mm gaps around block B: the first pick held B on seed 10 (crowded, 2/2 routes), so the route's "
                    "expected failure did not happen -> 3 mm gaps (bowl y 1.717, pin x 6.864): the pick failed 12/12"],
    "goal": {"any": [[["on_top_of", "wooden_block_b", "wooden_block_a"]], [["on_top_of", "wooden_block_a", "wooden_block_b"]]],
             "all": [["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"clear": "nominal", "crowded": "fallback_separate"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["clear"], "steps": [
            S("look", target=ISLAND), S("navigate", destination="wooden_block_b"), S("pick", object="wooden_block_b"),
            S("rotate", object="wooden_block_b", degrees=30), S("navigate", destination="wooden_block_a"),
            S("stack", object="wooden_block_b", base="wooden_block_a")]},
        "fallback_separate": {"kind": "fallback", "variants": ["crowded"], "recovery": "Pick -> failure -> Separate -> Pick",
                              "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_b"),
                                        S("pick", "fail", "failure", object="wooden_block_b"),
                                        S("separate", role="recovery", object="wooden_block_b"),
                                        S("pick", role="retry_after_recovery", object="wooden_block_b"),
                                        S("rotate", object="wooden_block_b", degrees=30),
                                        S("navigate", destination="wooden_block_a"),
                                        # stacking from the navigate pose chose an angled base and the fingers met
                                        # block A (hand blocked 5 cm above it, 3/4): park square to A first
                                        S("approach", target="wooden_block_a"),
                                        S("stack", object="wooden_block_b", base="wooden_block_a")]},
        # diagnostic since the 3 mm gaps: the fixed +x push puts the pad between B and the rolling pin and B did
        # not move (1/4 seeds); separate chooses its own direction (4/4)
        "fallback_push": {"kind": "diagnostic", "variants": ["crowded"], "recovery": "Pick -> failure -> Push -> Pick",
                          "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_b"),
                                    S("pick", "fail", "failure", object="wooden_block_b"),
                                    S("push", role="recovery", object="wooden_block_b", direction_xy=[1.0, 0.0],
                                      distance_m=0.1),
                                    S("pick", role="retry_after_recovery", object="wooden_block_b"),
                                    S("rotate", object="wooden_block_b", degrees=30),
                                    S("navigate", destination="wooden_block_a"),
                                    S("stack", object="wooden_block_b", base="wooden_block_a")]}}})

# --------------------------------------------------------------------- T03
BIN = "wide_storage_bin"
TASKS.append({
    "task_id": "T03_utensils_one_container", "exp_id": "ZB-T03",
    "source": ["skill_library/tasks.json:collect_fruits / tidy_toys (collect into one container)", "k_fetch_collect",
               "k_hands (rolling pin)", "k_stir_cover (spoon)"],
    "instruction": "Baking is done. Put the rolling pin and the spoon away together in one container.",
    "instruction_zh": "烘焙结束了，把擀面杖和勺子一起收进同一个容器里。",
    "scene": {"base": "tasks/kitchen_skills", "remove": [*TOMATOES, "oatmeal", "wooden_block_a", "wooden_block_b"],
              # the storage bin on the dining table cannot be reached for a place, neither at its default
              # spot nor at the near edge (2/2 runs: no base pose with IK, chairs block the base; the
              # recycle_and_store rollout failed the same way): it stands at the island's left end instead
              # (at the island's left end place_object of the spoon into the bin found no reachable pose,
              # 6/6 - its pinch must go down inside the 14 cm walls; the spoon is dropped in from above)
              # on the island the spoon could neither be placed (10/10) nor dropped (6/6) into the bin: the
              # hand above the middle of a 1.0 m high opening is out of reach.  On the TV stand (0.47 m) the rim
              # is at 0.61 m; the bin is 30 cm deep on a 24 cm top, centred 5 cm in front of the stand's middle (wall)
              "move": {BIN: at(TV, 7.3, 0.40, 0)},
              "distractors": ["juice_bottle", "paperback_book", "soda_can", "kitchen_sponge"]},
    "variants": {
        "small_and_large": {"note": "two open containers: a mug (8 cm opening) on the island and the wide storage "
                                    "bin (34 x 30 cm) on the TV stand", "move": {}},
        "large_only": {"note": "no mug: the storage bin on the TV stand is the only open container",
                       "remove": ["mug"]}},
    "watch": ["rolling_pin", "breakfast_spoon", "mug", BIN],
    "goal": {"any": [[["inside", "rolling_pin", BIN], ["inside", "breakfast_spoon", BIN]],
                     [["inside", "rolling_pin", "mug"], ["inside", "breakfast_spoon", "mug"]]],
             "all": [["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"small_and_large": "nominal", "large_only": "nominal"},
    # the spoon goes in first, dropped from above (place_object into the bin: no reachable pose, 10/10)
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["small_and_large", "large_only"], "steps": [
            S("look", target=ISLAND), S("look", target=TV), S("navigate", destination="breakfast_spoon"), S("pick", object="breakfast_spoon"), S("navigate", destination=BIN), S("approach", target=BIN), S("drop", object="breakfast_spoon", container=BIN), S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"), S("navigate", destination=BIN), S("approach", target=BIN), S("place", object="rolling_pin", receptacle=BIN)]},
        "alternative_large_container": {
            "kind": "alternative", "variants": ["small_and_large"],
            "recovery": "Place into the mug -> failure (does not fit) -> choose the storage bin",
            "steps": [S("look", target=ISLAND), S("look", target=TV), S("measure", object="mug"), S("navigate", destination="breakfast_spoon"), S("pick", object="breakfast_spoon"), S("navigate", destination=BIN), S("approach", target=BIN), S("drop", object="breakfast_spoon", container=BIN),
                      S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"),
                      S("navigate", destination="mug"),
                      S("place", "fail", "failure", object="rolling_pin", receptacle="mug"),
                      # lift the pin clear of the mug rim, then back out: driving off (1/1) or retreating
                      # (2/2) with the pin still caught on the mug dragged the mug off the island; the lift
                      # target is the object's bottom height (1.0 m was already reached at the rim and did
                      # nothing, 2/2; 1.2 m had no IK 4/4; 1.08 m stopped at 1.03-1.04 m, 4/4): the mug rim is
                      # at 0.98 m, the arm's straight-up range from the rim pose ends ~5 cm above it
                      S("lift", role="unwind", object="rolling_pin", height_m=1.04),
                      S("retreat", role="unwind", obstacle="kitchen_island", distance_m=0.3),
                      S("navigate", destination=BIN, role="alternative"), S("approach", target=BIN),
                      S("place", role="alternative", object="rolling_pin", receptacle=BIN)]}}})

# --------------------------------------------------------------------- T04
TASKS.append({
    "task_id": "T04_cup_or_mug_to_cabinet", "exp_id": "ZB-T04",
    "source": ["skill_library/tasks.json:breakfast_setup", "k_handle_mug / k_brace (mug rim pick)"],
    "instruction": "A guest is coming. Set out a cup at the drinks spot on the low wall cabinet; if there is no cup, a mug will do.",
    "instruction_zh": "有客人要来，在靠墙矮柜上的饮品角摆一个杯子；没有杯子的话马克杯也行。",
    "scene": {"base": "tasks/kitchen_skills", "remove": [*TOMATOES, "cup_kitchen_cabinet", "cup_side_table", "plate_inside_kitchen_cabinet",
                         "bowl_inside_kitchen_cabinet", "spoon_kitchen_cabinet"],
              "distractors": ["juice_bottle", "paperback_book", "wooden_block_a", "rolling_pin", "kitchen_sponge"]},
    "variants": {
        "cup_available": {"note": "a cup stands on the island next to the mug",
                          "move": {"cup_counter_b": at(ISLAND, 7.62, 1.64)}, "remove": ["juice_bottle"]},
        "no_cup": {"note": "there is no cup in the house: the mug is the legal substitute", "remove": ["cup_counter_b"]}},
    "watch": ["cup_counter_b", "mug"],
    "diagnostics": ["destination dining table: the cup passed (1/1); the mug slipped out of the rim pinch (1/2) "
                    "and the handle pinch (1/1) during the carry, and its place failed at the table edge (2/2)",
                    "destination TV stand (0.47 m): the mug passed (1/1), the cup tipped over on release (2/2)",
                    "-> destination: the low wall cabinet top; cup and mug both passed (1/1 each)"],
    "goal": {"any": [[["on", "cup_counter_b", CAB_TOP], ["upright", "cup_counter_b"]],
                     [["on", "mug", CAB_TOP], ["upright", "mug"]]],
             "all": [["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"cup_available": "nominal", "no_cup": "alternative_mug"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["cup_available"], "steps": [
            S("look", target=ISLAND), *carry("cup_counter_b", CAB_TOP)[:3],
            S("place", object="cup_counter_b", receptacle=CAB_TOP)]},
        "alternative_mug": {"kind": "alternative", "variants": ["no_cup"],
                            "recovery": "no cup is observed (count cup = 0, search fails) -> substitute the mug",
                            "steps": [S("look", target=ISLAND), S("count", category="cup"),
                                      S("search", "fail", "failure", object="cup"),
                                      S("navigate", destination="mug", role="alternative"),
                                      S("pick", role="alternative", object="mug"),
                                      S("navigate", destination=CAB_TOP), S("place", object="mug", receptacle=CAB_TOP)]}}})

# --------------------------------------------------------------------- T05
TASKS.append({
    "task_id": "T05_pen_or_pencil_to_desk", "exp_id": "ZB-T05",
    "source": ["skill_library/tasks.json:desk_prep", "tasks/desk_prep"],
    "instruction": "The kid needs something to write with for homework. Bring a pen to the study desk; if there is no pen, a pencil.",
    "instruction_zh": "孩子写作业要用笔，把一支钢笔拿到书桌上；没有钢笔就拿铅笔。",
    "scene": {"base": "tasks/desk_prep", "remove": ["notebook", "desk_mug"],
              # the pen lies next to the pencil: carried from the dining table (12 m) the 1 cm pen slipped out
              # of the pinch on the way (2/2); the pencil passed the bookcase-to-desk carry
              "move": {"pen": at(BOOKCASE, 1.15, -0.40)},
              "distractors": ["clutter_cereal_a", "clutter_cereal_b", "spoon_target_table"]},
    "variants": {
        "pen_available": {"note": "a pen and a pencil lie on the low bookcase (diagnostic only: the pen cannot be "
                                  "carried, see routes.nominal)", "move": {}, "difficulty": "diagnostic"},
        "no_pen": {"note": "only the pencil lies on the low bookcase", "remove": ["pen"]}},
    "watch": ["pen", "pencil"],
    "goal": {"any": [[["on", "pen", DESK]], [["on", "pencil", DESK]]], "all": [["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"no_pen": "alternative_pencil"},
    "routes": {
        "nominal": {"kind": "diagnostic", "variants": ["pen_available"],
                    "status": "not passed: the 1 cm pen slipped out of the top pinch during every carry to the "
                              "desk (from the dining table 2/2, from the bookcase 2/2); the pencil passes",
                    "steps": [
            S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE), *carry("pen", DESK)]},
        "alternative_pencil": {"kind": "alternative", "variants": ["no_pen"],
                               "recovery": "no pen is observed (navigate to it refused) -> the pencil",
                               "steps": [S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE),
                                         S("navigate", "fail", "failure", destination="pen"),
                                         S("navigate", destination="pencil", role="alternative"),
                                         S("pick", role="alternative", object="pencil"),
                                         S("navigate", destination=DESK), S("place", object="pencil", receptacle=DESK)]}}})

# --------------------------------------------------------------------- T06
TASKS.append({
    "task_id": "T06_block_destination_occupied", "exp_id": "ZB-T06",
    "source": ["skill_library/tasks.json:clear_tv_stand", "o_clear", "k_cabinet (navigate to the cabinet)"],
    "instruction": "Put a toy block on display, either on the low wall cabinet or on the TV stand.",
    "instruction_zh": "把积木摆到靠墙矮柜上或电视柜上做展示。",
    "scene": {"base": "tasks/kitchen_skills",
              # the plate and bowl stored inside this cabinet count as obstacles for spots on its top
              # (free_spots looks 0.5 m below a spot): removed so that "free" really has room
              "remove": [*TOMATOES, "plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet",
                         "spoon_kitchen_cabinet"],
              "move": {"wooden_block_a": at(ISLAND, 7.2, 1.62)},
              "distractors": ["paperback_book", "rolling_pin", "kitchen_sponge"]},
    "variants": {
        "free": {"note": "the cabinet top is empty", "move": {}},
        "occupied": {"note": "the pot lid and the oatmeal bowl take up the cabinet top: the 15 cm gap between "
                             "them is too narrow for a block",
                     "move": {"pot_lid": at(CAB_TOP, 3.335, 0.36), "oatmeal": at(CAB_TOP, 3.70, 0.36)}}},
    "diagnostics": ["occupants oatmeal bowl + mug + soda can + juice bottle: Clear failed at the mug's rim pinch "
                    "in the crowd (1/1); three bowls 3 cm apart: Clear failed at the first bowl's rim pinch (1/1) "
                    "-> two well separated occupants (lid by its knob, bowl by its rim)"],
    "watch": ["wooden_block_a", "wooden_block_b", "oatmeal", "pot_lid"],
    "goal": {"any": [[["on", b, sup]] for b in ("wooden_block_a", "wooden_block_b") for sup in (CAB_TOP, TV)],
             "all": [["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"free": "nominal", "occupied": "alternative_tv_stand"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["free"], "steps": [
            S("look", target=ISLAND), *carry("wooden_block_a", CAB_TOP)]},
        "alternative_tv_stand": {"kind": "alternative", "variants": ["occupied"],
                                 "recovery": "Place on the cabinet top -> failure (no free spot) -> TV stand",
                                 "steps": [S("look", target=ISLAND), *carry("wooden_block_a", CAB_TOP)[:3],
                                           S("place", "fail", "failure", object="wooden_block_a", receptacle=CAB_TOP),
                                           S("navigate", destination=TV, role="alternative"),
                                           S("place", role="alternative", object="wooden_block_a", receptacle=TV)]},
        "fallback_clear": {"kind": "diagnostic", "variants": ["occupied"],
                           "status": "not passed: clear could not pick the occupants off the cabinet top "
                                     "(mug in a crowd 1/1, bowl next to bowls 1/1, oatmeal bowl after the lid was "
                                     "moved 1/1: rim pinch 'not held')",
                           "recovery": "Place on the cabinet top -> failure -> set the block down, Clear the top, "
                                       "fetch the block again",
                           "steps": [S("look", target=ISLAND), *carry("wooden_block_a", CAB_TOP)[:3],
                                     S("place", "fail", "failure", object="wooden_block_a", receptacle=CAB_TOP),
                                     S("navigate", destination=CAB2_TOP),
                                     S("place", object="wooden_block_a", receptacle=CAB2_TOP),
                                     S("navigate", destination=CAB_TOP), S("look", target=CAB_TOP),
                                     S("clear", role="recovery", support=CAB_TOP, receptacle=CAB2_TOP),
                                     S("look", target=CAB2_TOP),
                                     S("fetch", role="retry_after_recovery", object="wooden_block_a",
                                       receptacle=CAB_TOP)]}}})

# --------------------------------------------------------------------- T07
NO_MW = {"oatmeal": {"heating_rate_c_per_s": 0.0}}      # the magnetron does not heat
TASKS.append({
    "task_id": "T07_heat_oatmeal", "exp_id": "ZB-T07",
    "source": ["skill_library/tasks.json:heat_breakfast_preloaded / heat_without_microwave", "k_microwave",
               "k_mug_on_burner", "g_heat_on_stove_instead_of_microwave"],
    "instruction": "Warm up the leftover oatmeal for breakfast (at least 40 C). When you are done, the stove must be off and the microwave door closed.",
    "instruction_zh": "把剩下的燕麦粥热一下当早饭（至少 40 度）。做完后灶台要关火，微波炉门要关好。",
    "scene": {"base": "tasks/kitchen_skills", "remove": [*TOMATOES],
              "distractors": ["juice_bottle", "paperback_book", "wooden_block_a", "wooden_block_b", "kitchen_sponge"]},
    "variants": {
        "microwave_works": {"note": "the microwave heats", "move": {}},
        "microwave_broken": {"note": "the microwave runs its cycle but does not heat: the heat call "
                                     "fails on the measured temperature",
                             "thermal_override": NO_MW}},
    "diagnostics": ["variant 'microwave_occupied' (a bowl of leftovers in the cavity) was dropped: the oatmeal was "
                    "still inserted in front of it (the cavity holds two bowls front to back), so the condition did "
                    "not block the microwave route (benchmark/runs/dbg2/T07_heat_oatmeal)"],
    "watch": ["oatmeal"],
    "goal": {"all": [["temperature_at_least", "oatmeal", 40], ["not heating", "kitchen_stove"],
                     ["is_closed", MW], ["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"microwave_works": "nominal", "microwave_broken": "oracle_stove"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["microwave_works"], "steps": [
            S("navigate", destination=MW), S("open", articulated=MW), S("look", target=ISLAND),
            *carry("oatmeal", MW_FLOOR), S("close", articulated=MW), S("heat", food="oatmeal", appliance=MW, temp_c=40)]},
        "alternative_stove": {"kind": "alternative", "variants": ["microwave_broken"],
                              "recovery": "Heat in the microwave -> failure (temperature does not rise) -> Stop the "
                                          "microwave, take the oatmeal out, heat it on the stove",
                              "steps": [S("navigate", destination=MW), S("open", articulated=MW),
                                        S("look", target=ISLAND), *carry("oatmeal", MW_FLOOR),
                                        S("close", articulated=MW),
                                        S("heat", "fail", "failure", food="oatmeal", appliance=MW, temp_c=40),
                                        S("stop", role="alternative", appliance=MW),
                                        S("pick", role="alternative", object="oatmeal"),
                                        S("navigate", destination=STOVE_TOP, role="alternative"),
                                        S("place", role="alternative", object="oatmeal", receptacle=STOVE_TOP),
                                        S("heat", role="alternative", food="oatmeal", appliance="kitchen_stove",
                                          temp_c=40),
                                        S("navigate", destination=MW), S("close", articulated=MW)]},
        "oracle_stove": {"kind": "alternative", "variants": ["microwave_broken"], "steps": [
            S("look", target=ISLAND), *carry("oatmeal", STOVE_TOP),
            S("heat", food="oatmeal", appliance="kitchen_stove", temp_c=40)]}}})

# --------------------------------------------------------------------- T08
TASKS.append({
    "task_id": "T08_wipe_island", "exp_id": "ZB-T08",
    "source": ["skill_library/tasks.json:wipe_island", "k_wipe"],
    "instruction": "Wipe down the kitchen island with the sponge after cooking, then leave the sponge on the island.",
    "instruction_zh": "做完饭用海绵擦一下厨房岛台，擦完把海绵放回岛台上。",
    "scene": {"base": "tasks/kitchen_skills", "remove": [*TOMATOES],
              "distractors": ["juice_bottle", "paperback_book", "wooden_block_a", "wooden_block_b", "soda_can"]},
    "variants": {
        "sponge_on_island": {"note": "the sponge lies on the island", "move": {}},
        "sponge_on_tv_stand": {"note": "the sponge lies on the TV stand behind the island",
                               "move": {"kitchen_sponge": at(TV, 7.6, 0.38)}}},
    "diagnostics": ["former T08 'chill the soda can in the fridge' moved to diagnostics: the open fridge door "
                    "drifted below 60 % open before the place (1/2), the can tipped on the shelf (xy err 0.11 m, "
                    "1/2; the same failure as k_fridge_chill in verification round 30), and with the can in the "
                    "dining room the door was pushed shut on the way (2/2)"],
    "watch": ["kitchen_sponge"],
    # navigate to the island before wiping parked behind it, where wipe found no base pose (2/2); approach
    # from next to the island's sponge spot found no base pose either (1/1): the island variant wipes directly
    "goal": {"all": [["wiped", ISLAND], ["on", "kitchen_sponge", ISLAND], ["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"sponge_on_island": "nominal", "sponge_on_tv_stand": "nominal_from_tv_stand"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["sponge_on_island"], "steps": [
            S("look", target=ISLAND), S("look", target=TV), S("navigate", destination="kitchen_sponge"),
            S("pick", object="kitchen_sponge"), S("wipe", surface=ISLAND, tool="kitchen_sponge"),
            S("place", object="kitchen_sponge", receptacle=ISLAND)]},
        "nominal_from_tv_stand": {"kind": "nominal", "variants": ["sponge_on_tv_stand"],
                                  "note": "approach the island before wiping; the fallback 'wipe fails -> approach "
                                          "-> wipe' is not used: after the failed wipe the approach parked but its IK "
                                          "check failed (2/2), and navigating to the stove instead did not help (1/1)",
                                  "steps": [S("look", target=ISLAND), S("look", target=TV),
                                            S("navigate", destination="kitchen_sponge"), S("pick", object="kitchen_sponge"),
                                            S("approach", target=ISLAND),
                                            S("wipe", surface=ISLAND, tool="kitchen_sponge"),
                                            S("place", object="kitchen_sponge", receptacle=ISLAND)]},
        "oracle_approach": {"kind": "fallback", "variants": ["sponge_on_tv_stand"], "steps": [
            S("navigate", destination="kitchen_sponge"), S("pick", object="kitchen_sponge"),
            S("approach", target=ISLAND), S("wipe", surface=ISLAND, tool="kitchen_sponge"),
            S("place", object="kitchen_sponge", receptacle=ISLAND)]}}})

# --------------------------------------------------------------------- T09
POT = "handled_cooking_pot"
LOOSE = {"cherry_tomato_1": at(ISLAND, 7.63, 1.62), "cherry_tomato_2": at(ISLAND, 7.8, 1.62),
         "cherry_tomato_3": at(ISLAND, 8.05, 1.62)}
TASKS.append({
    "task_id": "T09_tomato_soup", "exp_id": "ZB-T09",
    "source": ["skill_library/tasks.json:cook_tomato_soup", "k_stir_cover", "g_heat_on_stove_instead_of_microwave"],
    "instruction": "Make tomato soup for lunch: put the cherry tomatoes into the pot on the stove, stir them, cover the "
                   "pot and heat the soup to 60 C. Turn the stove off afterwards.",
    "instruction_zh": "午饭做个番茄汤：把小番茄放进灶上的锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。",
    "scene": {"base": "tasks/kitchen_skills",
              "remove": ["mug", "juice_bottle", "soda_can", "cherry_tomato_3", "paperback_book", "kitchen_sponge"],
              "move": {k: v for k, v in LOOSE.items() if k != "cherry_tomato_3"},
              "distractors": ["wooden_block_a", "wooden_block_b", "oatmeal", "rolling_pin"]},
    "variants": {
        "lid_on": {"note": "the lid is on the pot", "move": {}},
        "lid_off": {"note": "the lid lies on the stove beside the pot (where uncover sets it aside)",
                    "move": {"pot_lid": at(STOVE_TOP, 8.715, 1.655)}}},
    "watch": ["cherry_tomato_1", "cherry_tomato_2", POT, "pot_lid", "breakfast_spoon"],
    "diagnostics": ["lid_off with the lid on the stove's right burner: the lid slipped out of the hand during cover "
                    "(place_rise), 1/1; on the island next to the pot it was pushed during the stir/spoon place "
                    "and its pick missed (2/2); at the island's left end it slipped out of the hand on the way to "
                    "the pot (2/2) -> the spot uncover itself uses (cover passed 2/2 from there)"],
    "goal": {"all": [["inside", "cherry_tomato_1", POT], ["inside", "cherry_tomato_2", POT],
                     ["temperature_at_least", "cherry_tomato_1", 60], ["temperature_at_least", "cherry_tomato_2", 60],
                     ["stirred", POT], ["covered", POT, "pot_lid"], ["not heating", "kitchen_stove"],
                     ["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"lid_on": "fallback_uncover", "lid_off": "nominal"},
    "routes": {}})
_soup_tail = [S("navigate", destination="breakfast_spoon"), S("pick", object="breakfast_spoon"),
              S("navigate", destination=POT), S("stir", container=POT, tool="breakfast_spoon"),
              S("navigate", destination=ISLAND), S("place", object="breakfast_spoon", receptacle=ISLAND),
              *carry("pot_lid", POT)[:3], S("cover", container=POT, lid="pot_lid"),
              S("navigate", destination="kitchen_stove"),
              S("heat", food="cherry_tomato_1", appliance="kitchen_stove", temp_c=60)]
TASKS[-1]["routes"] = {
    "nominal": {"kind": "nominal", "variants": ["lid_off"], "steps": [
        S("look", target=ISLAND), S("collect", objects=["cherry_tomato_1", "cherry_tomato_2"], container=POT),
        *_soup_tail]},
    "fallback_uncover": {"kind": "fallback", "variants": ["lid_on"],
                         "recovery": "Collect into the pot -> refused (lid on) -> Uncover -> Collect",
                         "steps": [S("look", target=ISLAND),
                                   S("collect", "fail", "failure", objects=["cherry_tomato_1", "cherry_tomato_2"],
                                     container=POT),
                                   S("navigate", destination=POT), S("uncover", role="recovery", container=POT),
                                   S("collect", role="retry_after_recovery",
                                     objects=["cherry_tomato_1", "cherry_tomato_2"], container=POT),
                                   *_soup_tail]}}

# --------------------------------------------------------------------- T10
TASKS.append({
    "task_id": "T10_trash_the_can", "exp_id": "ZB-T10",
    "source": ["skill_library/tasks.json:throw_away_can", "k_trash", "g_search_then_fetch"],
    "instruction": "Someone left an empty soda can lying around. Throw it into the trash can.",
    "instruction_zh": "有人随手放了个空易拉罐，把它扔进垃圾桶。",
    "scene": {"base": "tasks/kitchen_skills", "remove": [*TOMATOES],
              # the trash can's default spot right behind the stove is hidden by the stove body from every
              # viewpoint (look, search and explore all missed it, 3/3): it stands in the open beside the stove
              "move": {"trash_can": {"support": None, "z": 0.0, "xy": [9.05, 1.12], "yaw_deg": 0}},
              "distractors": ["juice_bottle", "paperback_book", "wooden_block_a", "wooden_block_b", "kitchen_sponge",
                              "rolling_pin"]},
    "variants": {
        "can_on_island": {"note": "the can stands on the island", "move": {}},
        "can_in_dining_room": {"note": "the can stands on the dining table in the next room, out of sight",
                               "move": {"soda_can": at(DINING, 3.70, 6.30)}}},
    "watch": ["soda_can"],
    "goal": {"all": [["inside", "soda_can", "trash_can"], ["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"can_on_island": "nominal", "can_in_dining_room": "search_first"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["can_on_island"], "steps": [
            S("look", target=ISLAND), S("explore_room", room="living_room_0_0"),
            S("navigate", destination="soda_can"), S("pick", object="soda_can"),
            S("lift", object="soda_can", height_m=0.95), S("navigate", destination="trash_can"),
            S("hover", object="soda_can", target="trash_can"), S("drop", object="soda_can", container="trash_can")]},
        "search_first": {"kind": "fallback", "variants": ["can_in_dining_room"],
                         "recovery": "Pick refused (can not observed) -> Search -> found on the dining table",
                         "steps": [S("look", target=ISLAND), S("explore_room", room="living_room_0_0"),
                                   S("pick", "fail", "failure", object="soda_can"),
                                   S("search", role="recovery", object="soda_can", region="dining_room_0_1"),
                                   S("navigate", destination="soda_can"), S("pick", object="soda_can"),
                                   S("navigate", destination="trash_can"),
                                   S("drop", object="soda_can", container="trash_can")]}}})


# ===================================================================== difficulty tiers
# easy = no failure / alternative condition, medium = one, hard = several in one episode.
# Hard variants combine a task's own condition with a reason to search first (the robot
# starts in another room, or a needed object is out of sight) so the planner has to
# discover the situation before it can react to it.
CONDITIONS = {
    "T01_book_to_dining_table": {"no_overhang": ["no_overhang"]},
    "T02_stack_blocks": {"crowded": ["crowded"]},
    "T03_utensils_one_container": {"small_and_large": ["small_container_present"]},
    "T04_cup_or_mug_to_cabinet": {"no_cup": ["no_cup"]},
    "T05_pen_or_pencil_to_desk": {"no_pen": ["no_pen"]},
    "T06_block_destination_occupied": {"occupied": ["destination_occupied"]},
    "T07_heat_oatmeal": {"microwave_broken": ["microwave_broken"]},
    "T08_wipe_island": {"sponge_on_tv_stand": ["tool_away_from_surface"]},
    "T09_tomato_soup": {"lid_on": ["lid_on"]},
    "T10_trash_the_can": {"can_in_dining_room": ["not_in_view"]},
}
DINING_START = [4.24, 5.12, 120.0]          # a free pose in the dining room (the robot drove through it)
CAB_START = [4.764, 0.699, 195.0]           # at the low wall cabinet, facing away from the island
HALL = "living_room_0_0"                     # kitchen island, stove, fridge, microwave, TV stand

HARD = {
    "T01_book_to_dining_table": (
        # starting at the dining table's park (DINING_START), the carry back to the table took the island's
        # far side; the book drooped 7.7 deg in the hand and fell at the table (2/4 seeds, the medium tier's
        # carry passed 4/4): it starts at the wall cabinet instead
        {"far_no_overhang": {"note": "the robot starts at the wall cabinet facing away; the book on the island does "
                                     "not overhang enough", "conditions": ["start_elsewhere", "no_overhang"],
                             "start": CAB_START, "move": {"paperback_book": at(ISLAND, 7.62, 1.59, 90)}}},
        {"hard_search_expose": {"kind": "fallback", "variants": ["far_no_overhang"],
                                "recovery": "search the book -> Pick fails -> Expose -> Pick",
                                "steps": [S("search", role="recovery", object="paperback_book", region=HALL),
                                          S("navigate", destination="paperback_book"),
                                          S("pick", "fail", "failure", object="paperback_book"),
                                          S("expose", role="recovery", object="paperback_book"),
                                          S("pick", role="retry_after_recovery", object="paperback_book"),
                                          S("navigate", destination=DINING),
                                          S("place", object="paperback_book", receptacle=DINING, hint_xy=[3.72, 6.5])]}}),
    "T02_stack_blocks": (
        # from the dining room the robot came round the island's far side and the carry pose swept
        # block B out of its box before the pick (2/2): it starts at the wall cabinet instead
        {"far_crowded": {"note": "the robot starts at the wall cabinet facing away; block B is boxed in",
                         "conditions": ["start_elsewhere", "crowded"], "start": CAB_START,
                         "move": {"oatmeal": at(ISLAND, 7.0, 1.717), "rolling_pin": at(ISLAND, 6.864, 1.59, 0)}}},
        {"hard_search_separate": {"kind": "fallback", "variants": ["far_crowded"],
                                  "recovery": "search the blocks -> Pick fails -> Separate -> Pick",
                                  # block B hides behind the bowl and the rolling pin from every search viewpoint
                                  # (search B failed 2/2; a look from block A's north side did not see it either,
                                  # 2/2): find block A, then look at the island from the other side, the TV stand.
                                  # Push as the recovery (hard_search_push) left the base at x 7.00 and the retry
                                  # pick / rotate swept the rolling pin off the island (4/4, approach did not re-park)
                                  "steps": [S("search", role="recovery", object="wooden_block_a", region=HALL),
                                            S("navigate", destination=TV),
                                            S("look", target=ISLAND),
                                            S("navigate", destination="wooden_block_b"),
                                            S("pick", "fail", "failure", object="wooden_block_b"),
                                            S("separate", role="recovery", object="wooden_block_b"),
                                            S("pick", role="retry_after_recovery", object="wooden_block_b"),
                                            S("rotate", object="wooden_block_b", degrees=30),
                                            S("navigate", destination="wooden_block_a"),
                                            S("approach", target="wooden_block_a"),
                                            S("stack", object="wooden_block_b", base="wooden_block_a")]}}),
    "T04_cup_or_mug_to_cabinet": (
        {"no_cup_mug_away": {"note": "no cup in the house and the mug stands on the TV stand, out of the first view",
                             "conditions": ["no_cup", "not_in_view"], "remove": ["cup_counter_b"],
                             "move": {"mug": at(TV, 7.75, 0.36)}}},
        {"hard_count_search_mug": {"kind": "alternative", "variants": ["no_cup_mug_away"],
                                   "recovery": "no cup (count 0, search fails) -> search the mug -> mug",
                                   "steps": [S("look", target=ISLAND), S("count", category="cup"),
                                             S("search", "fail", "failure", object="cup"),
                                             S("search", role="alternative", object="mug", region=HALL),
                                             S("navigate", destination="mug"), S("pick", object="mug"),
                                             S("navigate", destination=CAB_TOP),
                                             S("place", object="mug", receptacle=CAB_TOP)]}}),
    "T05_pen_or_pencil_to_desk": (
        {"no_pen_pencil_away": {"note": "no pen; the pencil lies on the dining table in another room",
                                "conditions": ["no_pen", "not_in_view"], "remove": ["pen"],
                                "move": {"pencil": at(DINING, 3.70, 6.30)}}},
        {"hard_search_pencil": {"kind": "alternative", "variants": ["no_pen_pencil_away"],
                                "recovery": "no pen at the bookcase -> search the pencil -> pencil",
                                "steps": [S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE),
                                          S("navigate", "fail", "failure", destination="pen"),
                                          S("search", role="alternative", object="pencil", region="dining_room_0_1"),
                                          S("navigate", destination="pencil"), S("pick", object="pencil"),
                                          S("navigate", destination=DESK), S("place", object="pencil", receptacle=DESK)]}}),
    "T07_heat_oatmeal": (
        {"broken_oatmeal_away": {"note": "the microwave does not heat and the oatmeal was left on the wall cabinet "
                                         "(carried from the dining table it slipped out of the rim pinch, 2/2)",
                                 "conditions": ["microwave_broken", "not_in_view"], "thermal_override": NO_MW,
                                 # from the TV stand (0.47 m) the low rim grasp found no collision-free
                                 # path into the microwave (2/2): it stands on the wall cabinet instead
                                 "move": {"oatmeal": at(CAB_TOP, 3.70, 0.36)}}},
        {"hard_search_stove": {"kind": "alternative", "variants": ["broken_oatmeal_away"],
                               "recovery": "search the oatmeal -> heat in the microwave fails -> stop, take it out, stove",
                               "steps": [S("navigate", destination=MW), S("open", articulated=MW),
                                         S("search", role="recovery", object="oatmeal", region=HALL),
                                         S("navigate", destination="oatmeal"), S("pick", object="oatmeal"),
                                         S("navigate", destination=MW_FLOOR),
                                         S("place", object="oatmeal", receptacle=MW_FLOOR), S("close", articulated=MW),
                                         S("heat", "fail", "failure", food="oatmeal", appliance=MW, temp_c=40),
                                         S("stop", role="alternative", appliance=MW),
                                         S("pick", role="alternative", object="oatmeal"),
                                         S("navigate", destination=STOVE_TOP, role="alternative"),
                                         S("place", role="alternative", object="oatmeal", receptacle=STOVE_TOP),
                                         S("heat", role="alternative", food="oatmeal", appliance="kitchen_stove", temp_c=40),
                                         S("navigate", destination=MW), S("close", articulated=MW)]}}),
    "T10_trash_the_can": (
        {"far_can_far": {"note": "the robot starts in the dining room, the can is on the TV stand",
                         "conditions": ["start_elsewhere", "not_in_view"], "start": DINING_START,
                         "move": {"soda_can": at(TV, 7.2, 0.36)}}},
        {"hard_explore_search": {"kind": "fallback", "variants": ["far_can_far"],
                                 "recovery": "pick refused (can not observed) -> search -> explore for the trash can",
                                 "steps": [S("pick", "fail", "failure", object="soda_can"),
                                           S("search", role="recovery", object="soda_can", region=HALL),
                                           S("explore_room", role="recovery", room=HALL),
                                           S("navigate", destination="soda_can"), S("pick", object="soda_can"),
                                           S("navigate", destination="trash_can"),
                                           S("drop", object="soda_can", container="trash_can")]}}),
}

HARD.update({
    "T03_utensils_one_container": (
        {"far_small_and_large": {"note": "the robot starts at the wall cabinet facing away; a mug on the island, "
                                         "the storage bin on the TV stand",
                                 "conditions": ["start_elsewhere", "small_container_present"], "start": CAB_START}},
        {"hard_search_alt_container": {
            "kind": "alternative", "variants": ["far_small_and_large"],
            "recovery": "search the utensils -> the mug does not fit -> the storage bin",
            # search the flat spoon: after a search for the rolling pin the spoon was not in view (2/2)
            "steps": [S("search", role="recovery", object="breakfast_spoon", region=HALL), S("look", target=ISLAND),
                      S("navigate", destination="breakfast_spoon"), S("pick", object="breakfast_spoon"),
                      S("navigate", destination=BIN), S("approach", target=BIN),
                      S("drop", object="breakfast_spoon", container=BIN),
                      S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"),
                      S("navigate", destination="mug"),
                      S("place", "fail", "failure", object="rolling_pin", receptacle="mug"),
                      S("lift", role="unwind", object="rolling_pin", height_m=1.04),
                      S("retreat", role="unwind", obstacle="kitchen_island", distance_m=0.3),
                      S("navigate", destination=BIN, role="alternative"), S("approach", target=BIN),
                      S("place", role="alternative", object="rolling_pin", receptacle=BIN)]}}),
    "T06_block_destination_occupied": (
        {"occupied_block_away": {"note": "the cabinet top is full and the block was left on the dining table",
                                 "conditions": ["destination_occupied", "not_in_view"],
                                 "move": {"pot_lid": at(CAB_TOP, 3.335, 0.36), "oatmeal": at(CAB_TOP, 3.70, 0.36),
                                          "wooden_block_a": at(DINING, 3.70, 6.30)}}},
        {"hard_search_alt_support": {
            "kind": "alternative", "variants": ["occupied_block_away"],
            "recovery": "search the block -> place on the cabinet fails (full) -> TV stand",
            "steps": [S("look", target=ISLAND),
                      S("search", role="recovery", object="wooden_block_a", region="dining_room_0_1"),
                      S("navigate", destination="wooden_block_a"), S("pick", object="wooden_block_a"),
                      S("navigate", destination=CAB_TOP),
                      S("place", "fail", "failure", object="wooden_block_a", receptacle=CAB_TOP),
                      S("navigate", destination=TV, role="alternative"),
                      S("place", role="alternative", object="wooden_block_a", receptacle=TV)]}}),
    "T08_wipe_island": (
        {"far_sponge_tv": {"note": "the robot starts in the dining room; the sponge is on the TV stand",
                           "conditions": ["start_elsewhere", "tool_away_from_surface"], "start": DINING_START,
                           "move": {"kitchen_sponge": at(TV, 7.6, 0.38)}}},
        {"hard_search_approach": {
            "kind": "fallback", "variants": ["far_sponge_tv"],
            "recovery": "search the sponge -> approach the island -> wipe",
            "steps": [S("search", role="recovery", object="kitchen_sponge", region=HALL),
                      S("navigate", destination="kitchen_sponge"), S("pick", object="kitchen_sponge"),
                      S("approach", target=ISLAND), S("wipe", surface=ISLAND, tool="kitchen_sponge"),
                      S("place", object="kitchen_sponge", receptacle=ISLAND)]}}),
    "T09_tomato_soup": (
        {"lid_on_spoon_away": {"note": "the lid is on the pot and the spoon was left on the low wall cabinet",
                               "conditions": ["lid_on", "not_in_view"],
                               # picked from the TV stand (0.47 m) the spoon sat in the hand so that the stir
                               # reached only 0.59 turns (yaw 0, 2/2) or found no base pose (yaw 130.7, 2/2);
                               # on the cabinet top (0.81 m, near the island's height) it is approached from the
                               # opposite side, so it is turned by 180 deg to sit in the hand as on the island
                               "remove": ["spoon_kitchen_cabinet"],
                               "move": {"breakfast_spoon": at(CAB_TOP, 3.5, 0.36, -49.3)}}},
        {"hard_uncover_search_spoon": {
            "kind": "fallback", "variants": ["lid_on_spoon_away"],
            "recovery": "collect refused (lid) -> uncover -> collect; spoon not on the island -> search",
            "steps": [S("look", target=ISLAND),
                      S("collect", "fail", "failure", objects=["cherry_tomato_1", "cherry_tomato_2"], container=POT),
                      S("navigate", destination=POT), S("uncover", role="recovery", container=POT),
                      S("collect", role="retry_after_recovery", objects=["cherry_tomato_1", "cherry_tomato_2"],
                        container=POT),
                      S("search", role="recovery", object="breakfast_spoon", region=HALL), *_soup_tail]}}),
})

for _t in TASKS:
    for _v, _c in CONDITIONS.get(_t["task_id"], {}).items():
        _t["variants"][_v]["conditions"] = _c
    if _t["task_id"] in HARD:
        _vars, _routes = HARD[_t["task_id"]]
        _t["variants"].update(_vars)
        _t["routes"].update(_routes)
        for _v in _vars:
            _t["oracle"][_v] = next(n for n, r in _routes.items() if _v in r["variants"])


# ===================================================================== probes
# Small single-scene checks for SkillNodes that do not fit the ten tasks
# without being inserted mechanically.  Same interface, same limits; the
# probe runner issues an explicit look(object) when a contact skill is refused
# with NOT_IN_VIEW (recorded as its own call).
def probe(pid, title, steps, goal, source, remove=(), move=None, watch=(), start=None, thermal=None):
    return {"task_id": pid, "exp_id": "ZB-" + pid.split("_")[0], "kind": "probe", "source": source,
            "instruction": title, "auto_look": True,
            "scene": {"base": "tasks/kitchen_skills", "remove": list(remove), "move": move or {}, "distractors": [],
                      **({"start": start} if start else {})},
            "variants": {"default": {"note": "single fixed layout", "move": {}, **({"thermal_override": thermal} if thermal else {})}},
            "watch": list(watch), "goal": {"all": goal}, "nominal": "nominal", "oracle": {"default": "nominal"},
            "routes": {"nominal": {"kind": "nominal", "variants": ["default"], "steps": steps}}}


PROBES = [
    probe("P01_body_and_gesture", "Greet the person by the fridge, then return to the home posture.",
          [S("wave"), S("nod"), S("navigate", destination=ISLAND), S("sidestep", distance_m=0.2),
           S("retreat", obstacle="kitchen_island", distance_m=0.6), S("face", target=FRIDGE),
           S("point", target=FRIDGE), S("crouch"), S("stand"), S("crouch", height_m=-0.3), S("stand"),
           # bend from the crouched torso found no collision-free waist path (1/1): stand up first
           S("bend"),
           S("straighten"), S("bend", pitch_rad=0.3), S("reset"), S("wait", seconds=2), S("tuck", hand="right")],
          [["waved"], ["nodded"], ["arm_stowed", "right"], ["torso_raised"], ["waist_straight"]],
          ["k_body", "k_posture", "skill_library/tasks.json:greet_and_point"]),
    probe("P02_perception", "Find out what is on the island and explore the living room.",
          [S("look", target=ISLAND), S("identify", object="soda_can"), S("measure", object="juice_bottle"),
           S("count", category="cherry_tomato"), S("navigate", destination="mug"), S("inspect", receptacle="mug"),
           S("explore_room", room="living_room_0_0")],
          [["identified", "soda_can"], ["measured", "juice_bottle"], ["counted", "cherry_tomato"],
           ["room_explored", "living_room_0_0"]],
          ["k_perceive", "skill_library/tasks.json:explore_living_room / count_tomatoes"]),
    probe("P03_rolling_pin", "Roll the rolling pin, pull it toward you and centre it on the island.",
          [S("look", target=ISLAND), S("navigate", destination="rolling_pin"),
           S("roll", object="rolling_pin", distance_m=0.1), S("pull", object="rolling_pin", distance_m=0.08),
           S("center", object="rolling_pin", margin_m=0.06)],
          [["away_from_edge", "rolling_pin", 0.06], ["on", "rolling_pin", ISLAND]],
          ["k_pin", "skill_library/tasks.json:roll_pin"], watch=["rolling_pin"]),
    probe("P04_bottle", "Lay the juice bottle down, then stand it up again.",
          [S("look", target=ISLAND), S("navigate", destination="juice_bottle"), S("tip", object="juice_bottle"),
           S("upright", object="juice_bottle")],
          [["upright", "juice_bottle"], ["on", "juice_bottle", ISLAND]],
          ["k_bottle", "skill_library/tasks.json:lay_down_bottle"], watch=["juice_bottle"]),
    probe("P05_flip_book", "Turn the paperback book over on the island.",
          [S("look", target=ISLAND), S("navigate", destination="paperback_book"), S("expose", object="paperback_book"),
           S("pick", object="paperback_book"), S("place", object="paperback_book", receptacle=ISLAND),
           S("flip", object="paperback_book")],
          [["flipped", "paperback_book"], ["on", "paperback_book", ISLAND]],
          ["k_book", "skill_library/tasks.json:flip_book"], watch=["paperback_book"],
          # at its default spot the exposed book was still not held by the edge pinch (1/1): T01's layout
          move={"paperback_book": at(ISLAND, 7.62, 1.59, 90)}, remove=["juice_bottle"]),
    probe("P06_two_hands", "Hand the rolling pin to the left hand and open and close the low cabinet while holding it.",
          [S("look", target=ISLAND), S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"),
           S("regrasp", object="rolling_pin", support=ISLAND), S("handover", object="rolling_pin"),
           S("retreat", obstacle="kitchen_island", distance_m=0.6), S("navigate", destination=CAB),
           # open from the navigate pose missed the handle (1/1): park at the handle first
           S("approach", target=CAB), S("open", articulated=CAB), S("close", articulated=CAB)],
          [["holding", "left", "rolling_pin"], ["is_closed", CAB]],
          ["k_hands", "skill_library/tasks.json:serve_in_left_hand"], watch=["rolling_pin"]),
    probe("P07_present_and_brace", "Show a wooden block to the camera, then steady the mug with the left hand.",
          [S("look", target=ISLAND), S("navigate", destination="wooden_block_b"), S("pick", object="wooden_block_b"),
           S("present", object="wooden_block_b"), S("shake", object="wooden_block_b"),
           S("navigate", destination=ISLAND), S("place", object="wooden_block_b", receptacle=ISLAND),
           S("navigate", destination="mug"), S("brace", object="mug"), S("release", object="mug", hand="left"),
           S("tuck", hand="left")],
          [["on", "wooden_block_b", ISLAND], ["hand_empty", "left"], ["hand_empty", "right"], ["upright", "mug"]],
          ["k_present", "k_brace", "skill_library/tasks.json:present_block"], watch=["wooden_block_b", "mug"]),
    probe("P08_block_alignment", "Square one block with the island, then stack the other on it rotated and touch it.",
          [S("look", target=ISLAND), S("navigate", destination="wooden_block_a"), S("square", object="wooden_block_a"),
           S("pick", object="wooden_block_b"), S("rotate", object="wooden_block_b", degrees=30),
           S("stack", object="wooden_block_b", base="wooden_block_a"), S("touch", object="wooden_block_b")],
          [["on_top_of", "wooden_block_b", "wooden_block_a"], ["squared", "wooden_block_a"]],
          ["k_blocks", "skill_library/tasks.json:square_block"], watch=["wooden_block_a", "wooden_block_b"]),
    probe("P09_sweep_blocks", "Sweep the two wooden blocks together, then push one aside.",
          [S("look", target=ISLAND), S("navigate", destination="wooden_block_a"),
           S("sweep", objects=["wooden_block_a", "wooden_block_b"], radius_m=0.05),
           S("push", object="wooden_block_a", direction_xy=[1.0, 0.0], distance_m=0.1)],
          [["on", "wooden_block_a", ISLAND], ["on", "wooden_block_b", ISLAND]],
          ["k_sweep", "skill_library/tasks.json:sweep_blocks"], watch=["wooden_block_a", "wooden_block_b"]),
    probe("P11_stove_cycle", "Put the mug on the stove, switch the burner on for a few seconds and off again.",
          [S("look", target=ISLAND), S("navigate", destination="mug"), S("approach", target="mug"),
           S("pick", object="mug"), S("navigate", destination=STOVE_TOP), S("place", object="mug", receptacle=STOVE_TOP),
           S("press", button="kitchen_stove/power_button"), S("wait", seconds=3), S("stop", appliance="kitchen_stove")],
          [["on_burner", "mug", "kitchen_stove"], ["not heating", "kitchen_stove"]],
          ["k_mug_on_burner", "skill_library/tasks.json:heat_without_microwave"], watch=["mug"]),
    probe("P12_cabinet", "Knock on the low cabinet, look inside, open it and close it again.",
          # inspect of the closed cabinet opened it from the knock pose and the door did not move (1/1); the
          # library rollout knock -> open passed: open from its own handle park, then inspect the open cabinet
          [S("navigate", destination=CAB), S("knock", articulated=CAB), S("open", articulated=CAB),
           S("inspect", receptacle=CAB), S("close", articulated=CAB)],
          [["knocked", CAB], ["is_closed", CAB]], ["k_cabinet", "skill_library/tasks.json:knock_then_open"]),
    probe("P13_microwave_buttons", "Heat the oatmeal in the microwave with its start key, then stop the microwave.",
          [S("navigate", destination=MW), S("open", articulated=MW), S("look", target=ISLAND),
           S("navigate", destination="oatmeal"), S("pick", object="oatmeal"), S("navigate", destination=MW),
           S("place", object="oatmeal", receptacle=MW_FLOOR), S("close", articulated=MW),
           S("press", button="kitchen_microwave/start_button"), S("wait", seconds=3), S("stop", appliance=MW)],
          [["in_appliance", "oatmeal", MW], ["not heating", MW]], ["k_microwave"], watch=["oatmeal"]),
    probe("P14_restore_swap", "Move a block to the stove, put it back where it was, then swap it with the soda can.",
          [S("look", target=ISLAND), S("fetch", object="wooden_block_a", receptacle=STOVE_TOP),
           S("restore", object="wooden_block_a"), S("look", target=ISLAND), S("swap", a="wooden_block_a", b="soda_can")],
          [["positions_swapped", "wooden_block_a", "soda_can"]], ["k_restore_swap", "skill_library/tasks.json:swap_blocks"],
          watch=["wooden_block_a", "soda_can"]),
    probe("P15_arrange_and_sort", "Group two blocks and the can on the island, then sort the can into the trash and a block onto the stove.",
          [S("look", target=ISLAND), S("arrange", objects=["wooden_block_a", "wooden_block_b", "soda_can"], support=ISLAND,
                                       max_dist_m=0.3),
           S("search", object="trash_can", region=HALL),
           S("sort", objects=["soda_can", "wooden_block_b"], rule={"recyclable": "trash_can", "block": STOVE_TOP})],
          [["sorted_by_category", ["soda_can", "wooden_block_b"], {"recyclable": "trash_can", "block": STOVE_TOP}]],
          ["k_arrange_sort", "skill_library/tasks.json:sort_items"], watch=["wooden_block_a", "wooden_block_b", "soda_can"],
          # the trash can behind the stove is never in view (T10): on the floor beside the island, as in T10
          move={"trash_can": {"support": None, "z": 0.0, "xy": [9.05, 1.12], "yaw_deg": 0}}),
    # P16 / P17 used to chain empty -> hide and pour -> dip: the first skill failed physically (1/1 each) and the
    # second was never tested, so each multi-skill probe is split
    probe("P16_empty_mug", "Empty the mug of tomatoes into the pot.",
          # look from the pot's park: turning in place there hits the stove (1/1), so drive to the island first
          [S("navigate", destination=POT), S("uncover", container=POT), S("navigate", destination=ISLAND),
           S("look", target=ISLAND), S("empty", container="mug", receptacle=POT)],
          [["container_empty", "mug"]], ["k_empty_hide", "skill_library/tasks.json:empty_mug"], watch=["mug"]),
    probe("P17_pour", "Pour the tomatoes from the mug into the pot.",
          [S("navigate", destination=POT), S("uncover", container=POT), S("navigate", destination=ISLAND),
           S("look", target=ISLAND), S("navigate", destination="mug"), S("pick", object="mug"), S("navigate", destination=POT),
           S("hover", object="mug", target=POT), S("pour", source="mug", target=POT)],
          [["container_empty", "mug"]], ["k_soup_stove"], watch=["mug"]),
    probe("P19_spoon_dip", "Taste the soup: lift the spoon, lower it again, then dip it into the open pot.",
          [S("navigate", destination=POT), S("uncover", container=POT), S("navigate", destination=ISLAND),
           S("look", target=ISLAND), S("navigate", destination="breakfast_spoon"), S("pick", object="breakfast_spoon"),
           S("lift", object="breakfast_spoon", height_m=1.0), S("lower", object="breakfast_spoon", height_m=0.95),
           S("navigate", destination=POT), S("dip", tool="breakfast_spoon", container=POT)],
          [["dipped", POT]], ["k_stir_cover", "k_soup_stove"], watch=["breakfast_spoon"]),
    probe("P20_hide_block", "Hide a wooden block in the pot under its lid.",
          [S("navigate", destination=POT), S("look", target=STOVE_TOP), S("navigate", destination=ISLAND),
           S("look", target=ISLAND), S("hide", object="wooden_block_b", receptacle=POT, lid="pot_lid")],
          [["hidden", "wooden_block_b"]], ["k_empty_hide", "skill_library/tasks.json:hide_block"],
          # the lid on the pot was never observed (1/1): it lies beside the pot, where uncover sets it (as T09 lid_off)
          move={"pot_lid": at(STOVE_TOP, 8.715, 1.655)}, watch=["wooden_block_b", "pot_lid"]),
    probe("P21_clear_cabinet", "Clear the top of the low wall cabinet onto the kitchen island.",
          [S("navigate", destination=CAB_TOP), S("look", target=CAB_TOP), S("clear", support=CAB_TOP, receptacle=ISLAND)],
          [["support_clear", CAB_TOP]], ["skill_library/tasks.json:clear_counter"], watch=["spoon_kitchen_cabinet"]),
    probe("P22_chill_oatmeal", "The leftover oatmeal went into the fridge still warm: check it and chill it to 8 C; "
          "leave the fridge closed.",
          # carrying the bowl into the fridge slipped at carry_in (1/1): the bowl starts on the fridge shelf
          [S("navigate", destination=FRIDGE), S("open", articulated=FRIDGE), S("look", target=FRIDGE_SHELF),
           S("close", articulated=FRIDGE), S("chill", food="oatmeal", appliance=FRIDGE, temp_c=8)],
          [["temperature_at_most", "oatmeal", 8], ["is_closed", FRIDGE]], ["k_fridge", "skill_library/tasks.json:chill_drink"],
          move={"oatmeal": at(FRIDGE_SHELF, 5.9, 3.15)},
          # warm oatmeal (the scene's oatmeal starts at 4 C, already cold)
          watch=["oatmeal"], thermal={"oatmeal": {"initial_c": 22.0}}),
    probe("P18_floor_pick", "Pick the wooden block up from the floor and put it on the island.",
          # search visits furniture only and never saw the floor block (1/1): the robot starts 2.3 m
          # away facing it, so it is in the first view
          [S("look", target="floor_block"), S("navigate", destination="floor_block"), S("pick", object="floor_block"),
           S("navigate", destination=ISLAND), S("place", object="floor_block", receptacle=ISLAND)],
          [["on", "floor_block", ISLAND]], ["k_floor"], watch=["floor_block"], start=[7.9, 1.05, 180.0]),
]


def main():
    OUT.write_text(json.dumps({"schema_version": 1, "kind": "zenobench_benchmark_tasks",
                               "note": __doc__.strip().splitlines()[0], "tasks": TASKS + PROBES}, indent=1))
    print(f"{len(TASKS)} tasks + {len(PROBES)} probes -> {OUT}")


if __name__ == "__main__":
    main()
