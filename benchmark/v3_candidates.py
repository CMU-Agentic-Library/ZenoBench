"""Candidate v3 conditions under physical debugging (not part of a committed benchmark version).

    python benchmark/define_tasks_v3.py --candidates OUT.json     # registry + these candidates, for research runs

A task's block moves into define_tasks_v3.EXT only after its conditions are
debugged (failure really happens, explicit recovery, full task success over
seeds 10-19); conditions that cannot be made to work go to its not_adopted.
"""
from define_tasks_v3 import *  # noqa: F401,F403
from define_tasks_v3 import (BIN, BOOKCASE_NEAR_DESK, DINING_ROOM, START_VARY, TURN_VARY, group, vary)  # noqa: F401
from define_tasks import (BOOKCASE, CAB2_TOP, CAB_START, CAB_TOP, DESK, DINING, DINING_START, HALL, ISLAND, MW,  # noqa: F401
                          MW_FLOOR, POT, STOVE_TOP, TV, S, _soup_tail, at, carry)

# ---------------------------------------------------------------------------- per-task extensions
CONDITIONS.update({
    "book_side_blocked": ("grasp_blocked", "fallback", "a neighbour beside the book's overhang blocks the edge pinch"),
    "pin_beside_block": ("grasp_blocked", "fallback", "the rolling pin and a bottle box the block in; the pin can be pushed aside"),
    "cup_crowded": ("grasp_blocked", "fallback", "neighbours at 3 mm around the cup block its rim pinch"),
    "sponge_side_blocked": ("grasp_blocked", "fallback", "one neighbour 3 mm from the sponge's pinch face"),
    "can_crowded": ("grasp_blocked", "fallback", "neighbours at 3 mm around the can block its side pinch"),
    "pencil_crowded": ("grasp_blocked", "fallback", "neighbours at 3 mm around the pencil"),
    "target_occluded": ("viewpoint", "explore", "the target is hidden behind other objects from the first viewpoint"),
    "tool_not_in_view": ("search_tool", "explore", "the tool is out of the first view"),
    "container_not_in_view": ("search_container", "explore", "the container to use is out of the first view"),
    "destination_occupied_clearable": ("destination_occupied", "fallback", "the first destination is full of easy objects: clear it, place again"),
    "microwave_occupied": ("appliance_occupied", "fallback", "a bowl in the middle of the cavity leaves no room: take it out, then use the microwave"),
    "spoon_unreachable": ("tool_unusable", "alternative", "the original spoon is visible but cannot be picked: the other spoon"),
    "trash_not_in_view": ("search_container", "explore", "the trash can stands in another room"),
})
EXT = {}

# ----------------------------------------------------------------- T01
BOOK_OVER = at(ISLAND, 7.62, 1.548, 90)
# the rolling pin along y right beside the book (3 mm), overhanging the front edge as far as the book: the hand
# that comes in horizontally under the edge to pinch the book's overhang meets the pin
PIN_BESIDE_BOOK = at(ISLAND, 7.709, 1.565, 90)
_t01_carry = [S("navigate", destination=DINING), S("place", object="paperback_book", receptacle=DINING, hint_xy=[3.72, 6.5])]
EXT["T01_book_to_dining_table"] = {
    "variants": {
        "book_out_of_view": {"note": "the robot starts at the wall cabinet facing away; the book overhangs the island edge",
                             "conditions": ["start_elsewhere"], "start": CAB_START, "move": {"paperback_book": BOOK_OVER}},
        "book_side_blocked": {"note": "the book overhangs the edge, the rolling pin lies right beside it (3 mm), "
                                      "overhanging as well",
                              "conditions": ["book_side_blocked"],
                              "move": {"paperback_book": BOOK_OVER, "rolling_pin": PIN_BESIDE_BOOK}},
        "far_book_side_blocked": {"note": "start at the wall cabinet facing away + the rolling pin beside the book",
                                  "conditions": ["start_elsewhere", "book_side_blocked"], "start": CAB_START,
                                  "move": {"paperback_book": BOOK_OVER, "rolling_pin": PIN_BESIDE_BOOK}}},
    "vary": {"overhang_ready": vary(group(["paperback_book"], dx=[-0.02, 0.04])),
             "no_overhang": vary(group(["paperback_book"], dx=[-0.02, 0.04])),
             "far_no_overhang": vary(group(["paperback_book"], dx=[-0.02, 0.04]), start=TURN_VARY),
             "book_out_of_view": vary(group(["paperback_book"], dx=[-0.02, 0.04]), start=TURN_VARY),
             "book_side_blocked": vary(group(["paperback_book", "rolling_pin"], dx=[-0.02, 0.04])),
             "far_book_side_blocked": vary(group(["paperback_book", "rolling_pin"], dx=[-0.02, 0.04]), start=TURN_VARY)},
    "routes": {
        "explore_search_book": {"kind": "explore", "variants": ["book_out_of_view"], "recovery": "search the book",
                                "steps": [S("search", role="recovery", object="paperback_book", region=HALL),
                                          S("navigate", destination="paperback_book"), S("pick", object="paperback_book"),
                                          *_t01_carry]},
        "fallback_separate": {"kind": "fallback", "variants": ["book_side_blocked"],
                              "recovery": "Pick fails (pin beside the overhang) -> Separate the book -> Pick",
                              "steps": [S("look", target=ISLAND), S("navigate", destination="paperback_book"),
                                        S("pick", "fail", "failure", object="paperback_book"),
                                        S("separate", role="recovery", object="paperback_book"),
                                        S("pick", role="retry_after_recovery", object="paperback_book"), *_t01_carry]},
        "fallback_push_pin": {"kind": "fallback", "variants": ["book_side_blocked"],
                              "recovery": "Pick fails -> Push the rolling pin away along the edge -> Pick",
                              "steps": [S("look", target=ISLAND), S("navigate", destination="paperback_book"),
                                        S("pick", "fail", "failure", object="paperback_book"),
                                        S("push", role="recovery", object="rolling_pin", direction_xy=[1.0, 0.0],
                                          distance_m=0.1),
                                        S("pick", role="retry_after_recovery", object="paperback_book"), *_t01_carry]},
        "hard_search_separate": {"kind": "fallback", "variants": ["far_book_side_blocked"],
                                 "recovery": "search the book -> Pick fails -> Separate -> Pick",
                                 "steps": [S("search", role="recovery", object="paperback_book", region=HALL),
                                           S("navigate", destination="paperback_book"),
                                           S("pick", "fail", "failure", object="paperback_book"),
                                           S("separate", role="recovery", object="paperback_book"),
                                           S("pick", role="retry_after_recovery", object="paperback_book"), *_t01_carry]}},
    "oracle": {"book_out_of_view": "explore_search_book", "book_side_blocked": "fallback_separate",
               "far_book_side_blocked": "hard_search_separate"},
    "not_adopted": [],
}

# ----------------------------------------------------------------- T02
CROWD = {"oatmeal": at(ISLAND, 7.0, 1.717), "rolling_pin": at(ISLAND, 6.864, 1.59, 0)}
# block B at (7.0, 1.60): the rolling pin lies along x against its +x face, the juice bottle stands against its
# +y face (3 mm gaps).  Pushing the pin back (+y) frees the +x face; the bottle's x span ends before the pin's.
PIN_SIDE = {"rolling_pin": at(ISLAND, 7.141, 1.60, 0), "juice_bottle": at(ISLAND, 7.0, 1.657)}
# block B behind the juice bottle and the soda can (seen from the front of the island)
OCCLUDED = {"wooden_block_b": at(ISLAND, 7.0, 1.76), "juice_bottle": at(ISLAND, 6.99, 1.62),
            "soda_can": at(ISLAND, 7.06, 1.63)}
_t02_stack = [S("rotate", object="wooden_block_b", degrees=30), S("navigate", destination="wooden_block_a"),
              S("approach", target="wooden_block_a"), S("stack", object="wooden_block_b", base="wooden_block_a")]
_t02_find = [S("search", role="recovery", object="wooden_block_a", region=HALL), S("navigate", destination=TV),
             S("look", target=ISLAND)]
EXT["T02_stack_blocks"] = {
    "variants": {
        "pin_beside_block": {"note": "block B is boxed in by the rolling pin along its +x face and the juice bottle "
                                     "behind it (3 mm gaps); the pin can be pushed back",
                             "conditions": ["pin_beside_block"], "move": dict(PIN_SIDE)},
        "block_occluded": {"note": "block B stands behind the juice bottle and the soda can: hidden from the front "
                                   "of the island", "conditions": ["target_occluded"], "move": dict(OCCLUDED)},
        "far_pin_beside_block": {"note": "start at the wall cabinet facing away + block B boxed in by the pin and the "
                                         "bottle", "conditions": ["start_elsewhere", "pin_beside_block"],
                                 "start": CAB_START, "move": dict(PIN_SIDE)}},
    "vary": {"clear": vary(group(["wooden_block_a", "wooden_block_b"], dx=0.02)),
             "crowded": vary(group(["wooden_block_b", "oatmeal", "rolling_pin"], dx=0.02)),
             "far_crowded": vary(group(["wooden_block_b", "oatmeal", "rolling_pin"], dx=0.02), start=TURN_VARY),
             "pin_beside_block": vary(group(["wooden_block_b", "rolling_pin", "juice_bottle"], dx=0.02)),
             "block_occluded": vary(group(["wooden_block_b", "juice_bottle", "soda_can"], dx=0.02)),
             "far_pin_beside_block": vary(group(["wooden_block_b", "rolling_pin", "juice_bottle"], dx=0.02),
                                          start=TURN_VARY)},
    "routes": {
        "fallback_push_pin": {"kind": "fallback", "variants": ["pin_beside_block"],
                              "recovery": "Pick fails -> Push the rolling pin back -> Pick",
                              "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_b"),
                                        S("pick", "fail", "failure", object="wooden_block_b"),
                                        S("push", role="recovery", object="rolling_pin", direction_xy=[0.0, 1.0],
                                          distance_m=0.08),
                                        S("pick", role="retry_after_recovery", object="wooden_block_b"), *_t02_stack]},
        "explore_viewpoint": {"kind": "explore", "variants": ["block_occluded"],
                              "recovery": "B not seen from the front -> search it from other viewpoints",
                              "steps": [S("look", target=ISLAND),
                                        S("navigate", "fail", "failure", destination="wooden_block_b"),
                                        S("search", role="recovery", object="wooden_block_b", region=HALL),
                                        S("navigate", destination="wooden_block_b"), S("pick", object="wooden_block_b"),
                                        *_t02_stack]},
        "hard_search_push_pin": {"kind": "fallback", "variants": ["far_pin_beside_block"],
                                 "recovery": "find the blocks -> Pick fails -> Push the pin back -> Pick",
                                 "steps": [*_t02_find, S("navigate", destination="wooden_block_b"),
                                           S("pick", "fail", "failure", object="wooden_block_b"),
                                           S("push", role="recovery", object="rolling_pin", direction_xy=[0.0, 1.0],
                                             distance_m=0.08),
                                           S("pick", role="retry_after_recovery", object="wooden_block_b"), *_t02_stack]},
        "alternative_reverse": {"kind": "alternative", "variants": ["clear"],
                                "recovery": "execution alternative: stack A on B (same condition, not a new scene)",
                                "steps": [S("look", target=ISLAND), S("navigate", destination="wooden_block_a"),
                                          S("pick", object="wooden_block_a"), S("rotate", object="wooden_block_a", degrees=30),
                                          S("navigate", destination="wooden_block_b"),
                                          S("approach", target="wooden_block_b"),
                                          S("stack", object="wooden_block_a", base="wooden_block_b")]}},
    "oracle": {"pin_beside_block": "fallback_push_pin", "block_occluded": "explore_viewpoint",
               "far_pin_beside_block": "hard_search_push_pin"},
    "not_adopted": [
        {"condition": "push block B itself out of the 3 mm crowd (v2 fallback_push)",
         "reason": "kept diagnostic: with one obstacle per pinch axis the pad behind B lands on an obstacle for every "
                   "direction that frees B (v2: B did not move on 1 of 4 seeds); the new push condition pushes the "
                   "obstacle instead"}],
}

# ----------------------------------------------------------------- T03
BIN_CAB2 = at(CAB2_TOP, 1.40, 0.42, 0)          # the lower wall cabinet (0.62 m, rim at 0.76 m), behind the robot
SPOON_CAB = at(CAB_TOP, 3.5, 0.36, -49.3)       # T09's verified spoon spot on the low wall cabinet
_t03_spoon_bin = [S("navigate", destination="breakfast_spoon"), S("pick", object="breakfast_spoon"),
                  S("navigate", destination=BIN), S("approach", target=BIN),
                  S("drop", object="breakfast_spoon", container=BIN)]
_t03_pin_bin = [S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"),
                S("navigate", destination=BIN), S("approach", target=BIN),
                S("place", object="rolling_pin", receptacle=BIN)]
_t03_pin_mug_fail = [S("navigate", destination="rolling_pin"), S("pick", object="rolling_pin"),
                     S("navigate", destination="mug"), S("place", "fail", "failure", object="rolling_pin", receptacle="mug"),
                     S("lift", role="unwind", object="rolling_pin", height_m=1.04),
                     S("retreat", role="unwind", obstacle="kitchen_island", distance_m=0.3)]
EXT["T03_utensils_one_container"] = {
    "variants": {
        "bin_out_of_view": {"note": "no mug; the storage bin stands on the lower wall cabinet behind the robot",
                            "conditions": ["container_not_in_view"], "remove": ["mug"], "move": {BIN: BIN_CAB2}},
        "spoon_out_of_view": {"note": "no mug; the spoon was left on the low wall cabinet, out of the first view",
                              "conditions": ["tool_not_in_view"], "remove": ["mug", "spoon_kitchen_cabinet"],
                              "move": {"breakfast_spoon": SPOON_CAB}},
        "bin_away_small": {"note": "the mug is on the island, the storage bin on the lower wall cabinet behind the robot",
                           "conditions": ["container_not_in_view", "small_container_present"], "move": {BIN: BIN_CAB2}},
        "spoon_away_small": {"note": "the spoon is on the low wall cabinet; the mug on the island, the bin on the TV stand",
                             "conditions": ["tool_not_in_view", "small_container_present"],
                             "remove": ["spoon_kitchen_cabinet"], "move": {"breakfast_spoon": SPOON_CAB}}},
    "vary": {k: vary() for k in ("small_and_large", "large_only", "bin_out_of_view", "spoon_out_of_view",
                                  "bin_away_small", "spoon_away_small")} | {"far_small_and_large": vary(start=TURN_VARY)},
    "routes": {
        "explore_search_bin": {"kind": "explore", "variants": ["bin_out_of_view"], "recovery": "search the container",
                               "steps": [S("look", target=ISLAND), S("look", target=TV),
                                         S("search", role="recovery", object=BIN, region=HALL),
                                         *_t03_spoon_bin, *_t03_pin_bin]},
        "explore_search_spoon": {"kind": "explore", "variants": ["spoon_out_of_view"], "recovery": "search the spoon",
                                 "steps": [S("look", target=ISLAND), S("look", target=TV),
                                           S("search", role="recovery", object="breakfast_spoon", region=HALL),
                                           *_t03_spoon_bin, *_t03_pin_bin]},
        "hard_search_bin_alt": {"kind": "alternative", "variants": ["bin_away_small"],
                                "recovery": "the pin does not fit the mug -> search a larger container -> the bin",
                                "steps": [S("look", target=ISLAND), S("measure", object="mug"), *_t03_pin_mug_fail,
                                          S("search", role="alternative", object=BIN, region=HALL),
                                          S("navigate", destination=BIN, role="alternative"), S("approach", target=BIN),
                                          S("place", role="alternative", object="rolling_pin", receptacle=BIN),
                                          *_t03_spoon_bin]},
        "hard_search_spoon_alt": {"kind": "alternative", "variants": ["spoon_away_small"],
                                  "recovery": "search the spoon; the pin does not fit the mug -> the bin",
                                  "steps": [S("look", target=ISLAND), S("look", target=TV),
                                            S("search", role="recovery", object="breakfast_spoon", region=HALL),
                                            *_t03_spoon_bin, *_t03_pin_mug_fail,
                                            S("navigate", destination=BIN, role="alternative"), S("approach", target=BIN),
                                            S("place", role="alternative", object="rolling_pin", receptacle=BIN)]}},
    "oracle": {"bin_out_of_view": "explore_search_bin", "spoon_out_of_view": "explore_search_spoon",
               "bin_away_small": "hard_search_bin_alt", "spoon_away_small": "hard_search_spoon_alt"},
    "not_adopted": [
        {"condition": "capacity: a container that takes one utensil but then has no room for the other",
         "reason": "no existing container is large enough for the 22 cm rolling pin and too small for pin + spoon: "
                   "the mug (8 cm opening) takes neither the pin alone, the pot and bowls are shorter than the pin, "
                   "the storage bin (34 x 30 cm) holds both. A capacity condition would need a new asset or a count "
                   "threshold, which the rules exclude"}],
}

# ----------------------------------------------------------------- T04
CUP_ISLAND = at(ISLAND, 7.62, 1.64)
# cup (10.8 cm) boxed in on the island: soda can on its -x side, juice bottle on its +x side, sponge behind (3 mm)
# (between the spoon, x <= 7.54, and the mug, x >= 7.90)
CUP_CROWD = {"cup_counter_b": at(ISLAND, 7.683, 1.64), "soda_can": at(ISLAND, 7.593, 1.64),
             "juice_bottle": at(ISLAND, 7.769, 1.64), "kitchen_sponge": at(ISLAND, 7.683, 1.728)}
CUP_DINING = at(DINING, 3.70, 6.30)
# cup on the dining table between the two cereal boxes (3 mm)
CUP_DINING_CROWD = {"cup_counter_b": CUP_DINING, "clutter_cereal_a": at(DINING, 3.70, 6.1795),
                    "clutter_cereal_b": at(DINING, 3.70, 6.4205)}
_t04_place = [S("navigate", destination=CAB_TOP), S("place", object="cup_counter_b", receptacle=CAB_TOP)]
EXT["T04_cup_or_mug_to_cabinet"] = {
    "variants": {
        "cup_out_of_view": {"note": "the cup is on the dining table in the next room; the mug on the island is in view",
                            "conditions": ["not_in_view"], "move": {"cup_counter_b": CUP_DINING}},
        "cup_crowded": {"note": "the cup on the island is boxed in by the soda can, the juice bottle and the sponge "
                                "(3 mm gaps)", "conditions": ["cup_crowded"], "move": dict(CUP_CROWD)},
        "cup_away_crowded": {"note": "the cup is on the dining table between the two cereal boxes (3 mm)",
                             "conditions": ["not_in_view", "cup_crowded"], "move": dict(CUP_DINING_CROWD)}},
    "vary": {"cup_available": vary(group(["cup_counter_b"], dx=0.03)), "no_cup": vary(),
             "no_cup_mug_away": vary(), "cup_out_of_view": vary(group(["cup_counter_b"], dy=0.05)),
             "cup_crowded": vary(group(list(CUP_CROWD), dx=[-0.02, 0.04])),
             "cup_away_crowded": vary(group(list(CUP_DINING_CROWD), dx=0.0, dy=0.05))},
    "routes": {
        "explore_search_cup": {"kind": "explore", "variants": ["cup_out_of_view"],
                               "recovery": "count cup = 0 in view -> search the cup (do not assume it is absent)",
                               "steps": [S("look", target=ISLAND), S("count", category="cup"),
                                         S("search", role="recovery", object="cup_counter_b", region=DINING_ROOM),
                                         S("navigate", destination="cup_counter_b"), S("pick", object="cup_counter_b"),
                                         *_t04_place]},
        "fallback_separate": {"kind": "fallback", "variants": ["cup_crowded"],
                              "recovery": "Pick fails (boxed in) -> Separate -> Pick",
                              "steps": [S("look", target=ISLAND), S("navigate", destination="cup_counter_b"),
                                        S("pick", "fail", "failure", object="cup_counter_b"),
                                        S("separate", role="recovery", object="cup_counter_b"),
                                        S("pick", role="retry_after_recovery", object="cup_counter_b"), *_t04_place]},
        "hard_search_separate": {"kind": "fallback", "variants": ["cup_away_crowded"],
                                 "recovery": "search the cup -> Pick fails -> Separate -> Pick",
                                 "steps": [S("look", target=ISLAND), S("count", category="cup"),
                                           S("search", role="recovery", object="cup_counter_b", region=DINING_ROOM),
                                           S("navigate", destination="cup_counter_b"),
                                           S("pick", "fail", "failure", object="cup_counter_b"),
                                           S("separate", role="recovery", object="cup_counter_b"),
                                           S("pick", role="retry_after_recovery", object="cup_counter_b"), *_t04_place]}},
    "oracle": {"cup_out_of_view": "explore_search_cup", "cup_crowded": "fallback_separate",
               "cup_away_crowded": "hard_search_separate"},
    "not_adopted": [{"condition": "another legal destination for the cup",
                     "reason": "the instruction names one drinks spot (low wall cabinet); no second destination is added"}],
}

# ----------------------------------------------------------------- T05
PEN_NEAR = at(BOOKCASE_NEAR_DESK, 2.10, -4.88, 0)
PENCIL_NEAR = at(BOOKCASE_NEAR_DESK, 2.10, -4.88, 90)
# the pencil (18 x 1.7 cm) turned along y between the two cereal boxes on the low bookcase (3 mm on each side):
# both slots of its top pinch are taken
PENCIL_CROWD = {"pencil": at(BOOKCASE, 0.965, -0.495, 90), "clutter_cereal_a": at(BOOKCASE, 0.901, -0.495),
                "clutter_cereal_b": at(BOOKCASE, 1.029, -0.495)}
EXT["T05_pen_or_pencil_to_desk"] = {
    "variants": {
        "pen_near_desk": {"note": "candidate easy tier: a pen (and the pencil) on the bookcase in the bedroom, 2 m "
                                  "from the desk (diagnostic until the pen carry passes)",
                          "difficulty": "diagnostic", "move": {"pen": PEN_NEAR}},
        "no_pen_pencil_near": {"note": "no pen; the pencil lies on the bookcase in the bedroom, behind the robot",
                               "conditions": ["no_pen", "not_in_view"], "remove": ["pen"], "move": {"pencil": PENCIL_NEAR}},
        "no_pen_pencil_crowded": {"note": "no pen; the pencil lies between the two cereal boxes on the low bookcase "
                                          "(3 mm)", "conditions": ["no_pen", "pencil_crowded"], "remove": ["pen"],
                                  "move": dict(PENCIL_CROWD)}},
    "vary": {"no_pen": vary(start=TURN_VARY), "no_pen_pencil_away": vary(start=TURN_VARY),
             "no_pen_pencil_near": vary(start=TURN_VARY), "no_pen_pencil_crowded": vary(start=TURN_VARY),
             "pen_near_desk": vary(start=TURN_VARY), "pen_available": vary(start=TURN_VARY)},
    "routes": {
        "nominal_pen_near": {"kind": "diagnostic", "variants": ["pen_near_desk"],
                             "status": "research: does the pen survive a 2 m carry (it slipped 4/4 over 6-12 m)?",
                             "steps": [S("search", object="pen", region="bedroom_0_1"), S("navigate", destination="pen"),
                                       S("pick", object="pen"), S("navigate", destination=DESK),
                                       S("place", object="pen", receptacle=DESK)]},
        "hard_search_pencil_near": {"kind": "alternative", "variants": ["no_pen_pencil_near"],
                                    "recovery": "no pen at the bookcase -> search the pencil -> pencil",
                                    "steps": [S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE),
                                              S("navigate", "fail", "failure", destination="pen"),
                                              S("search", role="alternative", object="pencil", region="bedroom_0_1"),
                                              S("navigate", destination="pencil"), S("pick", object="pencil"),
                                              S("navigate", destination=DESK),
                                              S("place", object="pencil", receptacle=DESK)]},
        "hard_alt_separate": {"kind": "alternative", "variants": ["no_pen_pencil_crowded"],
                              "recovery": "no pen -> pencil; Pick fails (boxed in) -> Separate -> Pick",
                              "steps": [S("navigate", destination=BOOKCASE), S("look", target=BOOKCASE),
                                        S("navigate", "fail", "failure", destination="pen"),
                                        S("navigate", destination="pencil", role="alternative"),
                                        S("pick", "fail", "failure", object="pencil"),
                                        S("separate", role="recovery", object="pencil"),
                                        S("pick", role="retry_after_recovery", object="pencil"),
                                        S("navigate", destination=DESK), S("place", object="pencil", receptacle=DESK)]}},
    "oracle": {"no_pen_pencil_near": "hard_search_pencil_near", "no_pen_pencil_crowded": "hard_alt_separate"},
    "not_adopted": [{"condition": "medium tier besides no_pen",
                     "reason": "the instruction asks for a pen first; while the pen carry is diagnostic every pencil "
                               "condition comes on top of no_pen, so it is hard by construction"},
                    {"condition": "'any writing tool' instruction",
                     "reason": "would change the task's semantics; it would have to be a separate task"}],
}

# ----------------------------------------------------------------- T06
# the pot lid and the soda can split the cabinet top into gaps of 10, 10 and 8 cm: no room for the block
CLEARABLE = {"pot_lid": at(CAB_TOP, 3.427, 0.36), "soda_can": at(CAB_TOP, 3.685, 0.36)}
EXT["T06_block_destination_occupied"] = {
    "variants": {
        "occupied_clearable": {"note": "the pot lid and the soda can split the cabinet top into gaps too narrow for "
                                       "the block; both are easy to pick",
                               "conditions": ["destination_occupied_clearable"], "move": dict(CLEARABLE)},
        "clearable_block_away": {"note": "the block is on the dining table; the cabinet top holds the lid and the can",
                                 "conditions": ["destination_occupied_clearable", "not_in_view"],
                                 "move": {**CLEARABLE, "wooden_block_a": at(DINING, 3.70, 6.30)}}},
    "vary": {"free": vary(group(["wooden_block_a"], dx=0.03)), "occupied": vary(group(["wooden_block_a"], dx=0.03)),
             "occupied_block_away": vary(), "occupied_clearable": vary(group(["wooden_block_a"], dx=0.03)),
             "clearable_block_away": vary()},
    "routes": {
        "fallback_clear_easy": {"kind": "fallback", "variants": ["occupied_clearable"],
                           "recovery": "Place on the cabinet fails -> set the block down, Clear the top, fetch the "
                                       "block again",
                           "steps": [S("look", target=ISLAND), *carry("wooden_block_a", CAB_TOP)[:3],
                                     S("place", "fail", "failure", object="wooden_block_a", receptacle=CAB_TOP),
                                     S("navigate", destination=CAB2_TOP),
                                     S("place", object="wooden_block_a", receptacle=CAB2_TOP),
                                     S("navigate", destination=CAB_TOP), S("look", target=CAB_TOP),
                                     S("clear", role="recovery", support=CAB_TOP, receptacle=CAB2_TOP),
                                     S("look", target=CAB2_TOP),
                                     S("fetch", role="retry_after_recovery", object="wooden_block_a", receptacle=CAB_TOP)]},
        "hard_search_clear": {"kind": "fallback", "variants": ["clearable_block_away"],
                              "recovery": "search the block -> place fails -> set it down, Clear, fetch again",
                              "steps": [S("look", target=ISLAND),
                                        S("search", role="recovery", object="wooden_block_a", region=DINING_ROOM),
                                        S("navigate", destination="wooden_block_a"), S("pick", object="wooden_block_a"),
                                        S("navigate", destination=CAB_TOP),
                                        S("place", "fail", "failure", object="wooden_block_a", receptacle=CAB_TOP),
                                        S("navigate", destination=CAB2_TOP),
                                        S("place", object="wooden_block_a", receptacle=CAB2_TOP),
                                        S("navigate", destination=CAB_TOP), S("look", target=CAB_TOP),
                                        S("clear", role="recovery", support=CAB_TOP, receptacle=CAB2_TOP),
                                        S("look", target=CAB2_TOP),
                                        S("fetch", role="retry_after_recovery", object="wooden_block_a", receptacle=CAB_TOP)]}},
    "oracle": {"occupied_clearable": "fallback_clear_easy", "clearable_block_away": "hard_search_clear"},
    "not_adopted": [
        {"condition": "TV stand occupied, cabinet free",
         "reason": "the nominal route (cabinet first) already succeeds unchanged, so the condition requires no "
                   "decision; filling the 1.7 m TV stand would also need more objects than the scene has"},
        {"condition": "clearable cabinet + TV stand unavailable",
         "reason": "the TV stand top (1.7 m x 0.24 m) cannot be made unavailable with the scene's objects"},
        {"condition": "a single occupant",
         "reason": "the largest easy object (pot lid, 25 cm) leaves 17 cm on each side of the 60 cm top, where the "
                   "block fits; two easy objects (lid + soda can) are needed"}],
}

# ----------------------------------------------------------------- T07
OAT_CAB = at(CAB_TOP, 3.70, 0.36)
MW_BLOCKER = {"bowl_inside_kitchen_cabinet": at(MW_FLOOR, 4.50, 2.50)}
_t07_close_heat = [S("close", articulated=MW), S("heat", food="oatmeal", appliance=MW, temp_c=40)]
_t07_clear_mw = [S("place", role="recovery", object="oatmeal", receptacle=ISLAND, hint_xy=[7.0, 1.62]),
                 S("navigate", destination="bowl_inside_kitchen_cabinet"),
                 S("pick", role="recovery", object="bowl_inside_kitchen_cabinet"),
                 S("navigate", destination=ISLAND, role="recovery"),
                 S("place", role="recovery", object="bowl_inside_kitchen_cabinet", receptacle=ISLAND),
                 S("navigate", destination="oatmeal"), S("pick", role="retry_after_recovery", object="oatmeal"),
                 S("navigate", destination=MW_FLOOR),
                 S("place", role="retry_after_recovery", object="oatmeal", receptacle=MW_FLOOR)]
EXT["T07_heat_oatmeal"] = {
    "variants": {
        "oatmeal_out_of_view": {"note": "the microwave heats; the oatmeal was left on the low wall cabinet",
                                "conditions": ["not_in_view"], "move": {"oatmeal": OAT_CAB}},
        "microwave_occupied": {"note": "a bowl stands in the middle of the microwave cavity: 17 cm left on each side "
                                       "and 10 cm in front, too little for the 18 cm oatmeal bowl",
                               "conditions": ["microwave_occupied"], "move": dict(MW_BLOCKER)},
        "occupied_oatmeal_away": {"note": "the microwave is occupied and the oatmeal is on the low wall cabinet",
                                  "conditions": ["microwave_occupied", "not_in_view"],
                                  "move": {**MW_BLOCKER, "oatmeal": OAT_CAB}}},
    "vary": {k: vary() for k in ("microwave_works", "microwave_broken", "broken_oatmeal_away", "oatmeal_out_of_view",
                                  "microwave_occupied", "occupied_oatmeal_away")},
    "routes": {
        "explore_search_oatmeal": {"kind": "explore", "variants": ["oatmeal_out_of_view"], "recovery": "search the oatmeal",
                                   "steps": [S("navigate", destination=MW), S("open", articulated=MW),
                                             S("search", role="recovery", object="oatmeal", region=HALL),
                                             S("navigate", destination="oatmeal"), S("pick", object="oatmeal"),
                                             S("navigate", destination=MW_FLOOR),
                                             S("place", object="oatmeal", receptacle=MW_FLOOR), *_t07_close_heat]},
        "fallback_clear_microwave": {"kind": "fallback", "variants": ["microwave_occupied"],
                                     "recovery": "Place into the microwave fails (no room) -> set the oatmeal down, take "
                                                 "the bowl out, place again",
                                     "steps": [S("navigate", destination=MW), S("open", articulated=MW),
                                               S("look", target=ISLAND), *carry("oatmeal", MW_FLOOR)[:3],
                                               S("place", "fail", "failure", object="oatmeal", receptacle=MW_FLOOR),
                                               S("navigate", destination=ISLAND, role="recovery"), *_t07_clear_mw,
                                               *_t07_close_heat]},
        "alternative_stove_occupied": {"kind": "alternative", "variants": ["microwave_occupied"],
                                       "recovery": "Place into the microwave fails (no room) -> heat on the stove, close "
                                                   "the microwave",
                                       "steps": [S("navigate", destination=MW), S("open", articulated=MW),
                                                 S("look", target=ISLAND), *carry("oatmeal", MW_FLOOR)[:3],
                                                 S("place", "fail", "failure", object="oatmeal", receptacle=MW_FLOOR),
                                                 S("navigate", destination=STOVE_TOP, role="alternative"),
                                                 S("place", role="alternative", object="oatmeal", receptacle=STOVE_TOP),
                                                 S("heat", role="alternative", food="oatmeal", appliance="kitchen_stove",
                                                   temp_c=40),
                                                 S("navigate", destination=MW), S("close", articulated=MW)]},
        "hard_search_clear_microwave": {"kind": "fallback", "variants": ["occupied_oatmeal_away"],
                                        "recovery": "search the oatmeal -> place fails (no room) -> take the bowl out",
                                        "steps": [S("navigate", destination=MW), S("open", articulated=MW),
                                                  S("search", role="recovery", object="oatmeal", region=HALL),
                                                  S("navigate", destination="oatmeal"), S("pick", object="oatmeal"),
                                                  S("navigate", destination=MW_FLOOR),
                                                  S("place", "fail", "failure", object="oatmeal", receptacle=MW_FLOOR),
                                                  S("navigate", destination=ISLAND, role="recovery"), *_t07_clear_mw,
                                                  *_t07_close_heat]}},
    "oracle": {"oatmeal_out_of_view": "explore_search_oatmeal", "microwave_occupied": "fallback_clear_microwave",
               "occupied_oatmeal_away": "hard_search_clear_microwave"},
    "not_adopted": [{"condition": "v2 'microwave_occupied' (a bowl at the back of the cavity)",
                     "reason": "the oatmeal still went in in front of it (benchmark/runs/dbg2): not a real occupancy"}],
}

# ----------------------------------------------------------------- T08
SPONGE_CAB = at(CAB_TOP, 3.70, 0.36)       # beside the cabinet spoon (x <= 3.59)
# the sponge (9 x 6 cm, pinched across its 6 cm) at its island spot, the soda can 3 mm from its front face
SPONGE_BLOCK = {"kitchen_sponge": at(ISLAND, 8.165, 1.82), "soda_can": at(ISLAND, 8.165, 1.754)}
EXT["T08_wipe_island"] = {
    "variants": {
        "sponge_on_cabinet": {"note": "the sponge lies on the low wall cabinet, out of the first view",
                              "conditions": ["tool_not_in_view"], "move": {"kitchen_sponge": SPONGE_CAB}},
        "sponge_blocked": {"note": "the soda can stands 3 mm from the sponge's front face, the one pinch axis of the "
                                  "sponge has a finger slot taken", "conditions": ["sponge_side_blocked"],
                           "move": dict(SPONGE_BLOCK)},
        "far_sponge_blocked": {"note": "start in the dining room + the soda can against the sponge",
                               "conditions": ["start_elsewhere", "sponge_side_blocked"], "start": DINING_START,
                               "move": dict(SPONGE_BLOCK)}},
    "vary": {"sponge_on_island": vary(), "sponge_on_tv_stand": vary(group(["kitchen_sponge"], dx=0.03)),
             "far_sponge_tv": vary(group(["kitchen_sponge"], dx=0.03), start=TURN_VARY),
             "sponge_on_cabinet": vary(group(["kitchen_sponge"], dx=0.03)),
             "sponge_blocked": vary(group(list(SPONGE_BLOCK), dx=0.02)),
             "far_sponge_blocked": vary(group(list(SPONGE_BLOCK), dx=0.02), start=TURN_VARY)},
    "routes": {
        "explore_search_sponge": {"kind": "explore", "variants": ["sponge_on_cabinet"],
                                  "recovery": "search the sponge -> approach the island -> wipe",
                                  "steps": [S("look", target=ISLAND), S("look", target=TV),
                                            S("search", role="recovery", object="kitchen_sponge", region=HALL),
                                            S("navigate", destination="kitchen_sponge"), S("pick", object="kitchen_sponge"),
                                            S("approach", target=ISLAND), S("wipe", surface=ISLAND, tool="kitchen_sponge"),
                                            S("place", object="kitchen_sponge", receptacle=ISLAND)]},
        "fallback_separate": {"kind": "fallback", "variants": ["sponge_blocked"],
                              "recovery": "Pick fails (can against the sponge) -> Separate -> Pick",
                              "steps": [S("look", target=ISLAND), S("navigate", destination="kitchen_sponge"),
                                        S("pick", "fail", "failure", object="kitchen_sponge"),
                                        S("separate", role="recovery", object="kitchen_sponge"),
                                        S("pick", role="retry_after_recovery", object="kitchen_sponge"),
                                        S("wipe", surface=ISLAND, tool="kitchen_sponge"),
                                        S("place", object="kitchen_sponge", receptacle=ISLAND)]},
        "hard_search_separate": {"kind": "fallback", "variants": ["far_sponge_blocked"],
                                 "recovery": "search the sponge -> Pick fails -> Separate -> Pick -> approach -> wipe",
                                 "steps": [S("search", role="recovery", object="kitchen_sponge", region=HALL),
                                           S("navigate", destination="kitchen_sponge"),
                                           S("pick", "fail", "failure", object="kitchen_sponge"),
                                           S("separate", role="recovery", object="kitchen_sponge"),
                                           S("pick", role="retry_after_recovery", object="kitchen_sponge"),
                                           S("approach", target=ISLAND), S("wipe", surface=ISLAND, tool="kitchen_sponge"),
                                           S("place", object="kitchen_sponge", receptacle=ISLAND)]}},
    "oracle": {"sponge_on_cabinet": "explore_search_sponge", "sponge_blocked": "fallback_separate",
               "far_sponge_blocked": "hard_search_separate"},
    "not_adopted": [{"condition": "another object as a wiping tool",
                     "reason": "no other object in the scene is a wiping tool; no semantic alternative"}],
}

# ----------------------------------------------------------------- T09
SPOON_MW_TOP = at("kitchen_microwave/top", 4.50, 2.60, 0)     # visible from the kitchen, at the back of a 1.12 m top
EXT["T09_tomato_soup"] = {
    "variants": {
        "spoon_out_of_view": {"note": "the lid lies beside the pot; the spoon was left on the low wall cabinet",
                              "conditions": ["tool_not_in_view"],
                              "remove": ["spoon_kitchen_cabinet"],
                              "move": {"pot_lid": at(STOVE_TOP, 8.715, 1.655), "breakfast_spoon": SPOON_CAB}},
        "spoon_unreachable": {"note": "the lid lies beside the pot; the island spoon was left at the back of the "
                                      "microwave top (1.12 m) out of reach; the other spoon lies on the low wall cabinet",
                              "conditions": ["spoon_unreachable"],
                              "move": {"pot_lid": at(STOVE_TOP, 8.715, 1.655), "breakfast_spoon": SPOON_MW_TOP,
                                       "spoon_kitchen_cabinet": SPOON_CAB}},
        "lid_on_spoon_unreachable": {"note": "the lid is on the pot; the island spoon is out of reach on the microwave, "
                                             "the other spoon lies on the low wall cabinet",
                                     "conditions": ["lid_on", "spoon_unreachable"],
                                     "move": {"breakfast_spoon": SPOON_MW_TOP, "spoon_kitchen_cabinet": SPOON_CAB}}},
    "vary": {k: vary() for k in ("lid_on", "lid_off", "lid_on_spoon_away", "spoon_out_of_view", "spoon_unreachable",
                                  "lid_on_spoon_unreachable")},
    "routes": {},
    "oracle": {"spoon_out_of_view": "explore_search_spoon", "spoon_unreachable": "alternative_spoon",
               "lid_on_spoon_unreachable": "hard_uncover_alt_spoon"},
    "not_adopted": [],
}
_tail_alt = [S("navigate", destination="spoon_kitchen_cabinet", role="alternative"),
             S("pick", role="alternative", object="spoon_kitchen_cabinet"),
             S("navigate", destination=POT), S("stir", container=POT, tool="spoon_kitchen_cabinet"),
             S("navigate", destination=ISLAND), S("place", object="spoon_kitchen_cabinet", receptacle=ISLAND),
             *carry("pot_lid", POT)[:3], S("cover", container=POT, lid="pot_lid"),
             S("navigate", destination="kitchen_stove"),
             S("heat", food="cherry_tomato_1", appliance="kitchen_stove", temp_c=60)]
_collect = S("collect", objects=["cherry_tomato_1", "cherry_tomato_2"], container=POT)
_spoon_fail = [S("look", target="kitchen_microwave/top"), S("navigate", destination="breakfast_spoon"),
               S("pick", "fail", "failure", object="breakfast_spoon"),
               S("search", role="alternative", object="spoon_kitchen_cabinet", region=HALL)]
EXT["T09_tomato_soup"]["routes"] = {
    "explore_search_spoon": {"kind": "explore", "variants": ["spoon_out_of_view"], "recovery": "search the spoon",
                             "steps": [S("look", target=ISLAND), _collect,
                                       S("search", role="recovery", object="breakfast_spoon", region=HALL), *_soup_tail]},
    "alternative_spoon": {"kind": "alternative", "variants": ["spoon_unreachable"],
                          "recovery": "Pick the island spoon fails (out of reach) -> the other spoon",
                          "steps": [S("look", target=ISLAND), _collect, *_spoon_fail, *_tail_alt]},
    "hard_uncover_alt_spoon": {"kind": "fallback", "variants": ["lid_on_spoon_unreachable"],
                               "recovery": "collect refused (lid) -> uncover -> collect; spoon out of reach -> other spoon",
                               "steps": [S("look", target=ISLAND),
                                         S("collect", "fail", "failure", objects=["cherry_tomato_1", "cherry_tomato_2"],
                                           container=POT),
                                         S("navigate", destination=POT), S("uncover", role="recovery", container=POT),
                                         S("collect", role="retry_after_recovery",
                                           objects=["cherry_tomato_1", "cherry_tomato_2"], container=POT),
                                         *_spoon_fail, *_tail_alt]}}

# ----------------------------------------------------------------- T10
TRASH_DINING = {"support": None, "z": 0.0, "xy": [4.60, 5.60], "yaw_deg": 0}
# the can (6.6 cm) boxed in on the island: juice bottle -x, mug +x, sponge behind (3 mm)
CAN_CROWD = {"soda_can": at(ISLAND, 8.0, 1.62), "juice_bottle": at(ISLAND, 7.935, 1.62), "mug": at(ISLAND, 8.083, 1.62),
             "kitchen_sponge": at(ISLAND, 8.0, 1.701, 90)}
CAN_DINING_CROWD = {"soda_can": at(DINING, 3.70, 6.30), "clutter_cereal_a": at(DINING, 3.70, 6.2013),
                    "clutter_cereal_b": at(DINING, 3.70, 6.3987)}
_t10_drop = [S("navigate", destination="trash_can"), S("drop", object="soda_can", container="trash_can")]
EXT["T10_trash_the_can"] = {
    "variants": {
        "trash_out_of_view": {"note": "the can is on the island; the trash can stands in the dining room",
                              "conditions": ["trash_not_in_view"], "move": {"trash_can": TRASH_DINING}},
        "can_crowded": {"note": "the can is boxed in by the juice bottle, the mug and the sponge (3 mm)",
                        "conditions": ["can_crowded"], "move": dict(CAN_CROWD)},
        "can_and_trash_away": {"note": "the can is on the TV stand, the trash can in the dining room",
                               "conditions": ["not_in_view", "trash_not_in_view"],
                               "move": {"soda_can": at(TV, 7.2, 0.36), "trash_can": TRASH_DINING}},
        "can_away_crowded": {"note": "the can is on the dining table between the two cereal boxes (3 mm)",
                             "conditions": ["not_in_view", "can_crowded"], "move": dict(CAN_DINING_CROWD)}},
    "vary": {"can_on_island": vary(), "can_in_dining_room": vary(group(["soda_can"], dy=0.05)),
             "far_can_far": vary(group(["soda_can"], dx=0.05), start=TURN_VARY),
             "trash_out_of_view": vary(), "can_crowded": vary(group(list(CAN_CROWD), dx=0.02)),
             "can_and_trash_away": vary(group(["soda_can"], dx=0.05)),
             "can_away_crowded": vary(group(list(CAN_DINING_CROWD), dy=0.05))},
    "routes": {
        "explore_search_trash": {"kind": "explore", "variants": ["trash_out_of_view"],
                                 "recovery": "drop refused (no trash can observed) -> explore the dining room",
                                 "steps": [S("look", target=ISLAND), S("explore", room=HALL),
                                           S("navigate", destination="soda_can"), S("pick", object="soda_can"),
                                           S("navigate", "fail", "failure", destination="trash_can"),
                                           S("explore", role="recovery", room=DINING_ROOM), *_t10_drop]},
        "fallback_separate": {"kind": "fallback", "variants": ["can_crowded"],
                              "recovery": "Pick fails (boxed in) -> Separate -> Pick",
                              "steps": [S("look", target=ISLAND), S("explore", room=HALL),
                                        S("navigate", destination="soda_can"),
                                        S("pick", "fail", "failure", object="soda_can"),
                                        S("separate", role="recovery", object="soda_can"),
                                        S("pick", role="retry_after_recovery", object="soda_can"), *_t10_drop]},
        "hard_search_both": {"kind": "explore", "variants": ["can_and_trash_away"],
                             "recovery": "search the can -> explore the dining room for the trash can",
                             "steps": [S("look", target=ISLAND), S("explore", room=HALL),
                                       S("search", role="recovery", object="soda_can", region=HALL),
                                       S("navigate", destination="soda_can"), S("pick", object="soda_can"),
                                       S("explore", role="recovery", room=DINING_ROOM), *_t10_drop]},
        "hard_search_separate": {"kind": "fallback", "variants": ["can_away_crowded"],
                                 "recovery": "search the can -> Pick fails -> Separate -> Pick",
                                 "steps": [S("look", target=ISLAND), S("explore", room=HALL),
                                           S("search", role="recovery", object="soda_can", region=DINING_ROOM),
                                           S("navigate", destination="soda_can"),
                                           S("pick", "fail", "failure", object="soda_can"),
                                           S("separate", role="recovery", object="soda_can"),
                                           S("pick", role="retry_after_recovery", object="soda_can"), *_t10_drop]}},
    "oracle": {"trash_out_of_view": "explore_search_trash", "can_crowded": "fallback_separate",
               "can_and_trash_away": "hard_search_both", "can_away_crowded": "hard_search_separate"},
    "not_adopted": [{"condition": "another ordinary container as the trash",
                     "reason": "not a legal substitute for the trash can"}],
}


# ----------------------------------------------------------------- shared: the book's way to an edge is blocked
# the book (yaw 90, 18 cm along y) 5.5 cm behind the island's front edge; the rolling pin lies along x between the
# book and the edge, the oatmeal bowl right behind the book: the slide to the front edge and the one to the back
# edge both sweep through an object, the side edges need more than the 0.45 m limit -> slide_to_edge (expose, and
# flip's own slide) finds no free edge.  Pushing the pin 0.2 m along its axis clears the front path.
BOOK_BACK = at(ISLAND, 7.66, 1.66, 90)       # (x 7.66: the bowl clears the island spoon, x <= 7.54)
PATH_BLOCK = {"paperback_book": BOOK_BACK, "rolling_pin": at(ISLAND, 7.66, 1.542, 0), "oatmeal": at(ISLAND, 7.66, 1.851)}
CONDITIONS.update({"edge_path_blocked": ("grasp_blocked", "fallback",
                                         "objects in the book's way to every reachable edge: Expose cannot slide it")})
_push_pin = S("push", role="recovery", object="rolling_pin", direction_xy=[1.0, 0.0], distance_m=0.2)
EXT["T01_book_to_dining_table"]["variants"]["edge_path_blocked"] = {
    "note": "the book lies 5.5 cm behind the edge with the rolling pin in front of it and the oatmeal bowl behind it",
    "conditions": ["edge_path_blocked"], "move": dict(PATH_BLOCK)}
EXT["T01_book_to_dining_table"]["vary"]["edge_path_blocked"] = vary(group(list(PATH_BLOCK), dx=[0.0, 0.04]))
EXT["T01_book_to_dining_table"]["routes"]["fallback_push_expose"] = {
    "kind": "fallback", "variants": ["edge_path_blocked"],
    "recovery": "Pick fails (no overhang) -> Expose fails (no free path to an edge) -> Push the rolling pin -> Expose -> Pick",
    "steps": [S("look", target=ISLAND), S("navigate", destination="paperback_book"),
              S("pick", "fail", "failure", object="paperback_book"),
              S("expose", "fail", "failure", object="paperback_book"), _push_pin,
              S("expose", role="retry_after_recovery", object="paperback_book"),
              S("pick", role="retry_after_recovery", object="paperback_book"), *_t01_carry]}
EXT["T01_book_to_dining_table"]["oracle"]["edge_path_blocked"] = "fallback_push_expose"

NEW_TASKS = []

# T11-T20 are in define_tasks_v3.NEW_TASKS.

from define_tasks_v3 import _to  # noqa: E402
BEDROOM = "bedroom_0_1"

# T14, T19 and T20 passed and moved to define_tasks_v3.NEW_TASKS.

# ----------------------------------------------------------------- T14 homework desk: not adopted (slot open)
# kept for the record; not in NEW_TASKS
DROPPED_TASKS = [{
    "task_id": "T14_homework_desk", "source": "skill_library/tasks.json:desk_prep",
    "goal": "notebook and a pen (or the pencil) from the dining table to the study desk",
    "reason": "the 4 cm notebook: the edge pinch closed on nothing with 6 cm and 7.5 cm overhang over the dining table "
              "edge (s10, benchmark/runs/v3_normal, v3_round2); the pen slips while carried (T05 diagnostic, 4/4). "
              "Pencil to the desk is T05's alternative already"}]
