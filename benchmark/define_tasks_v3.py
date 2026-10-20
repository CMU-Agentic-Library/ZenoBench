"""Source of benchmark/v3/tasks.json (python benchmark/define_tasks_v3.py).

Benchmark v3 extends v2 (benchmark/tasks.json, kept unchanged with its evidence):

* every v2 variant and route is kept under its name; v2 runs do not count as v3
  evidence (a v3 episode has its own configuration hash, see scene.config_hash);
* new condition variants per task (one condition = one variant_id; medium = one
  condition, hard = two), each with its condition tags, condition types and the
  decision it is expected to require (CONDITIONS below);
* seeds 10-19 vary only what a variant declares safe (``vary``): the robot start
  and rigid shifts of object groups whose relative geometry makes the condition;
* every new variant starts as a candidate: its status (unverified / preliminary /
  stable / unstable / failing) comes from runs only (benchmark/conditions.py);
* ``not_adopted`` records conditions that were considered and not registered,
  with the reason.

Route kinds: nominal | explore (search / look / explore only, no physical
repair) | fallback (a real failure, then an auxiliary skill repairs the state)
| alternative (another legal object, destination, appliance or tool) |
diagnostic (documents a limit, never counted) | negative.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import define_tasks as v2  # noqa: E402
from define_tasks import (BOOKCASE, CAB, CAB2_TOP, CAB_START, CAB_TOP, DESK, DINING, DINING_START, HALL,  # noqa: E402,F401
                          ISLAND, MW, MW_FLOOR, NO_MW, POT, STOVE_TOP, TV, S, _soup_tail, at, carry)

OUT = Path(__file__).with_name("v3") / "tasks.json"
VERSION = "v3"
EVAL_SEEDS = list(range(10, 20))
DINING_ROOM = "dining_room_0_1"
BIN = "wide_storage_bin"
BOOKCASE_NEAR_DESK = "SimpleBookcaseFactory_2318999_spawn_asset_8416993/surface_2"   # 2 m from the desk

# ---------------------------------------------------------------------------- condition registry
# tag -> (condition type, decision the condition is meant to require, one-line meaning)
CONDITIONS = {
    "no_overhang": ("grasp_blocked", "fallback", "flat book does not overhang: edge pinch fails until Expose"),
    "crowded": ("grasp_blocked", "fallback", "both pinch axes of the block have a finger slot taken (3 mm gaps)"),
    "not_in_view": ("search_target", "explore", "the target object is out of the first view (another surface or room)"),
    "start_elsewhere": ("search_target", "explore", "the robot starts elsewhere, facing away from the task area"),
    "tool_away_from_surface": ("search_tool", "explore", "the tool is on another surface than the one to work on"),
    "small_container_present": ("container_choice", "alternative", "a too-small container is in view; the large one must be chosen"),
    "no_cup": ("object_absent", "alternative", "the requested object does not exist; the allowed substitute is used"),
    "no_pen": ("object_absent", "alternative", "the requested object does not exist; the allowed substitute is used"),
    "destination_occupied": ("destination_occupied", "alternative", "the first destination has no free spot; the other allowed one is used"),
    "microwave_broken": ("appliance_failure", "alternative", "the microwave runs but does not heat: the stove"),
    "lid_on": ("state_precondition", "fallback", "collect is refused while the lid is on: Uncover first"),
}


def tag_conditions(variant: dict) -> None:
    tags = variant.get("conditions", [])
    variant["condition_types"] = [CONDITIONS[c][0] for c in tags]
    variant["decisions"] = sorted({CONDITIONS[c][1] for c in tags}) or ["none"]


START_VARY = {"dx": 0.10, "dyaw": 10, "step": 0.05, "step_deg": 5}     # around the base scene's start
TURN_VARY = {"dyaw": 10, "step_deg": 5}                                  # an explicit start: heading only


def vary(*groups, start=START_VARY):
    out = {"groups": [g for g in groups if g]}
    if start:
        out["start"] = start
    return out


def group(names, dx=0.0, dy=0.0, dyaw=0.0, step=0.01, step_deg=5):
    return {"names": list(names), "dx": dx, "dy": dy, "dyaw": dyaw, "step": step, "step_deg": step_deg}


# ---------------------------------------------------------------------------- per-task extensions
# debugged v3 conditions per task (variants, vary, routes, oracle, not_adopted); candidates under debugging live in
# benchmark/v3_candidates.py until they pass
EXT = {}
# seed variation of the v2 variants (per task: {variant: vary})
V2_VARY = {}
# debugged new tasks (T11 ...), full task dicts in the v2 format plus v3 fields
NEW_TASKS = []
# v3 tasks whose Normal route and every declared condition route ran end to end on 1-2 seeds (preliminary);
# candidates under debugging live in v3_candidates.py.  T15-T18 are small chores built around one manipulation
# skill.
T01_REMOVE = ["mug", "cherry_tomato_1", "cherry_tomato_2", "cherry_tomato_3", "soda_can", "juice_bottle"]
BOOK_FLUSH = at(ISLAND, 7.62, 1.59, 90)        # the book flush with the island's front edge (no overhang)

# ----------------------------------------------------------------- T15 book face up (flip)
NEW_TASKS.append({
    "task_id": "T15_book_face_up", "exp_id": "ZB-T15", "since": "v3",
    "source": ["skill_library/tasks.json:flip_book", "k_book", "probe P05_flip_book"],
    "instruction": "Someone left their paperback face down on the kitchen island and the spine is getting bent. Turn "
                   "it face up and leave it on the island for them; they are still reading it.",
    "instruction_zh": "有人把平装书扣在厨房岛台上了，书脊都快压弯了。帮忙把它翻过来正面朝上，还放在岛台上，他还没看完。",
    "scene": {"base": "tasks/kitchen_skills", "remove": list(T01_REMOVE),
              "distractors": ["wooden_block_a", "wooden_block_b", "kitchen_sponge"]},
    "variants": {
        "book_free": {"note": "the book lies on the island with free paths to the front edge",
                      "move": {"paperback_book": BOOK_FLUSH}},
        "book_out_of_view": {"note": "the robot starts at the wall cabinet facing away", "conditions": ["start_elsewhere"],
                             "start": CAB_START, "move": {"paperback_book": BOOK_FLUSH}}},
    "watch": ["paperback_book"],
    "goal": {"all": [["flipped", "paperback_book"], ["on", "paperback_book", ISLAND], ["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"book_free": "nominal", "book_out_of_view": "explore_search_book"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["book_free"], "steps": [
            S("look", target=ISLAND), S("navigate", destination="paperback_book"), S("flip", object="paperback_book")]},
        "explore_search_book": {"kind": "explore", "variants": ["book_out_of_view"], "recovery": "search the book",
                                "steps": [S("search", role="recovery", object="paperback_book", region=HALL),
                                          S("navigate", destination="paperback_book"), S("flip", object="paperback_book")]}},
    "vary": {"book_free": vary(group(["paperback_book"], dx=[-0.02, 0.04])),
             "book_out_of_view": vary(group(["paperback_book"], dx=[-0.02, 0.04]), start=TURN_VARY)},
    "not_adopted": [{"condition": "edge_path_blocked: pin and bowl in the book's way to the edges -> Push the pin -> Flip",
                     "reason": "flip does not refuse the blocked path: its slide pushed the book through the rolling "
                               "pin and both fell off the island (s10, s11 and the far start s10, "
                               "benchmark/runs/v3_round2); no clean failure to recover from"},
                    {"condition": "Pick fails -> Expose -> Pick (T01's fallback)",
                     "reason": "flip slides the book to an edge itself (contract path edge_roll: slide, edge pinch, "
                               "arc), so a book without overhang needs no decision"},
                    {"condition": "no room on the island to land the turned book",
                     "reason": "flip checks the room to the support's edges only (0.33 m behind the book on the 47 cm "
                               "island): never short"},
                    {"condition": "turn it over, then put it back on the bedroom bookcase",
                     "reason": "after flip the book lies at the island edge without overhang (-0.5 cm); expose left "
                               "5.2 cm (< 5.5 cm EDGE_MIN_OVERHANG) and the edge pinch closed on nothing (s10, "
                               "benchmark/runs/v3_normal); T01 carries the book face down instead"}],
})

# ----------------------------------------------------------------- T16 rolling pin at the edge (roll)
PIN_DEFAULT = at(ISLAND, 6.75, 1.541, 0)        # 3 mm from the front edge (y 1.515)
# roll moves the pin away from the robot (+y), from the front edge into the island
_roll_tail = [S("roll", object="rolling_pin", distance_m=0.12)]
NEW_TASKS.append({
    "task_id": "T16_rolling_pin_at_edge", "exp_id": "ZB-T16", "since": "v3",
    "source": ["skill_library/tasks.json:roll_pin", "k_pin", "probe P03_rolling_pin"],
    "instruction": "We are about to make dumplings and the rolling pin has rolled right to the front edge of the "
                   "island. Roll it back in so it cannot fall off; that also shows whether it rolls smoothly.",
    "instruction_zh": "准备包饺子了，擀面杖滚到岛台前沿快掉下去了。把它往里滚回去别让它掉下来，顺便看看滚得顺不顺。",
    "scene": {"base": "tasks/kitchen_skills", "remove": ["mug", "cherry_tomato_1", "cherry_tomato_2", "cherry_tomato_3",
                                                        "juice_bottle", "soda_can"],
              "distractors": ["wooden_block_a", "wooden_block_b", "paperback_book", "kitchen_sponge"]},
    "variants": {
        "pin_free": {"note": "the pin lies 3 mm from the island's front edge with room behind it", "move": {"rolling_pin": PIN_DEFAULT}},
        "pin_out_of_view": {"note": "the robot starts at the wall cabinet facing away", "conditions": ["start_elsewhere"],
                            "start": CAB_START, "move": {"rolling_pin": PIN_DEFAULT}}},
    "watch": ["rolling_pin"],
    "goal": {"all": [["object_rolled", "rolling_pin"], ["on", "rolling_pin", ISLAND],
                     ["away_from_edge", "rolling_pin", 0.06], ["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"pin_free": "nominal", "pin_out_of_view": "explore_search_pin"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["pin_free"], "steps": [
            S("look", target=ISLAND), S("navigate", destination="rolling_pin"), *_roll_tail]},
        "explore_search_pin": {"kind": "explore", "variants": ["pin_out_of_view"], "recovery": "search the pin",
                               "steps": [S("search", role="recovery", object="rolling_pin", region=HALL),
                                         S("navigate", destination="rolling_pin"), *_roll_tail]}},
    "vary": {"pin_free": vary(group(["rolling_pin"], dx=[0.0, 0.05])),
             "pin_out_of_view": vary(group(["rolling_pin"], dx=[0.0, 0.05]), start=TURN_VARY)},
    "not_adopted": [{"condition": "roll_blocked: the oatmeal bowl 4 mm behind the pin -> Push the bowl -> Roll",
                     "reason": "roll does not fail: the pin pushed the bowl 9 cm aside and the roll completed (s10, "
                               "s11, benchmark/runs/v3_round2); with the far start the search did not see the pin "
                               "behind the bowl. A movable object on the island gives way the same way"}],
})

# ----------------------------------------------------------------- T17 hide and seek (hide)
LID_BESIDE = at(STOVE_TOP, 8.715, 1.655)
B_CROWD = {"wooden_block_b": at(ISLAND, 7.0, 1.60), "oatmeal": at(ISLAND, 7.0, 1.717),
           "rolling_pin": at(ISLAND, 6.864, 1.59, 0)}
_hide = S("hide", object="wooden_block_b", receptacle=POT, lid="pot_lid")
_hide_pre = [S("navigate", destination=POT), S("look", target=STOVE_TOP), S("navigate", destination=ISLAND),
             S("look", target=ISLAND)]
NEW_TASKS.append({
    "task_id": "T17_hide_and_seek_block", "exp_id": "ZB-T17", "since": "v3",
    "source": ["skill_library/tasks.json:hide_block", "k_empty_hide", "probe P20_hide_block"],
    "instruction": "We are playing hide-and-seek with the kid's toy block: hide the wooden block in the empty pot on the "
                   "stove and put the lid on so they cannot see it.",
    "instruction_zh": "陪孩子玩藏东西的游戏：把木积木藏进灶台上的空锅里，再盖好锅盖，别让孩子一眼看到。",
    "scene": {"base": "tasks/kitchen_skills", "remove": ["mug", "cherry_tomato_1", "cherry_tomato_2", "cherry_tomato_3",
                                                        "wooden_block_a", "juice_bottle", "soda_can"],
              "distractors": ["paperback_book", "kitchen_sponge", "breakfast_spoon"]},
    "variants": {
        "lid_off": {"note": "the lid lies on the stove beside the pot", "move": {"pot_lid": LID_BESIDE}},
        "lid_on": {"note": "the lid is on the pot: hide is refused until the pot is uncovered", "conditions": ["lid_on"],
                   "move": {}},
        "block_crowded": {"note": "the lid lies beside the pot; the block is boxed in by the oatmeal bowl and the rolling pin "
                                 "(3 mm, T02's crowd)", "conditions": ["crowded"], "move": {"pot_lid": LID_BESIDE, **B_CROWD}},
        "lid_on_crowded": {"note": "the lid is on the pot and the block is boxed in", "conditions": ["lid_on", "crowded"],
                           "move": dict(B_CROWD)},
        "far_lid_on": {"note": "the robot starts at the wall cabinet facing away; the lid is on the pot",
                       "conditions": ["start_elsewhere", "lid_on"], "start": CAB_START, "move": {}}},
    "watch": ["wooden_block_b", "pot_lid", POT, "oatmeal", "rolling_pin"],
    "goal": {"all": [["hidden", "wooden_block_b"], ["covered", POT, "pot_lid"], ["hand_empty", "right"]]},
    "nominal": "nominal",
    "oracle": {"lid_off": "nominal", "lid_on": "fallback_uncover", "block_crowded": "fallback_separate",
               "lid_on_crowded": "hard_uncover_separate", "far_lid_on": "hard_search_uncover"},
    "routes": {
        "nominal": {"kind": "nominal", "variants": ["lid_off"], "steps": [*_hide_pre, _hide]},
        "fallback_uncover": {"kind": "fallback", "variants": ["lid_on"],
                             "recovery": "Hide refused (lid on) -> Uncover -> Hide",
                             "steps": [*_hide_pre, S("hide", "fail", "failure", object="wooden_block_b", receptacle=POT,
                                                     lid="pot_lid"),
                                       S("navigate", destination=POT), S("uncover", role="recovery", container=POT),
                                       S("navigate", destination=ISLAND), S("look", target=ISLAND),
                                       S("hide", role="retry_after_recovery", object="wooden_block_b", receptacle=POT,
                                         lid="pot_lid")]},
        "fallback_separate": {"kind": "fallback", "variants": ["block_crowded"],
                              "recovery": "Hide fails (its pick of the block fails) -> Separate -> Hide",
                              "steps": [*_hide_pre, S("hide", "fail", "failure", object="wooden_block_b", receptacle=POT,
                                                      lid="pot_lid"),
                                        S("navigate", destination="wooden_block_b"),
                                        S("separate", role="recovery", object="wooden_block_b"),
                                        S("hide", role="retry_after_recovery", object="wooden_block_b", receptacle=POT,
                                          lid="pot_lid")]},
        "hard_uncover_separate": {"kind": "fallback", "variants": ["lid_on_crowded"],
                                  "recovery": "Hide refused (lid) -> Uncover; Hide fails (pick) -> Separate -> Hide",
                                  "steps": [*_hide_pre, S("hide", "fail", "failure", object="wooden_block_b",
                                                          receptacle=POT, lid="pot_lid"),
                                            S("navigate", destination=POT), S("uncover", role="recovery", container=POT),
                                            S("navigate", destination=ISLAND), S("look", target=ISLAND),
                                            S("hide", "fail", "failure", object="wooden_block_b", receptacle=POT,
                                              lid="pot_lid"),
                                            S("navigate", destination="wooden_block_b"),
                                            S("separate", role="recovery", object="wooden_block_b"),
                                            S("hide", role="retry_after_recovery", object="wooden_block_b", receptacle=POT,
                                              lid="pot_lid")]},
        "hard_search_uncover": {"kind": "fallback", "variants": ["far_lid_on"],
                                "recovery": "search the block and the pot -> Hide refused (lid) -> Uncover -> Hide",
                                "steps": [S("search", role="recovery", object="wooden_block_b", region=HALL),
                                          S("navigate", destination=STOVE_TOP), S("look", target=STOVE_TOP),
                                          S("hide", "fail", "failure", object="wooden_block_b", receptacle=POT,
                                            lid="pot_lid"),
                                          S("uncover", role="recovery", container=POT),
                                          S("navigate", destination=ISLAND), S("look", target=ISLAND),
                                          S("hide", role="retry_after_recovery", object="wooden_block_b", receptacle=POT,
                                            lid="pot_lid")]}},
    "vary": {"lid_off": vary(), "lid_on": vary(), "far_lid_on": vary(start=TURN_VARY),
             "block_crowded": vary(group(list(B_CROWD), dx=0.02)), "lid_on_crowded": vary(group(list(B_CROWD), dx=0.02))},
    "not_adopted": [{"condition": "alternative block (A instead of a blocked B)",
                     "reason": "with a free block A in the scene the nominal route can hide A without any failure; "
                               "the task keeps one block so the blocked pick needs a decision"}],
})

# ----------------------------------------------------------------- T18 check the cabinet for dishes (cabinet)
CONTENTS = ["plate_inside_kitchen_cabinet", "bowl_inside_kitchen_cabinet"]
_t18 = [S("navigate", destination=CAB), S("open", articulated=CAB), S("inspect", receptacle=CAB),
        S("close", articulated=CAB)]
NEW_TASKS.append({
    "task_id": "T18_check_cabinet_dishes", "exp_id": "ZB-T18", "since": "v3",
    "source": ["skill_library/tasks.json:inspect_cabinet", "k_cabinet", "probe P12_cabinet"],
    "instruction": "Grandma wants to know whether there is still a clean plate and bowl in the low wall cabinet for "
                   "dinner. Have a look inside and close the cabinet door properly afterwards.",
    "instruction_zh": "奶奶想知道靠墙矮柜里还有没有干净的盘子和碗，晚饭要用。去看一眼里面，看完把柜门关好。",
    "scene": {"base": "tasks/kitchen_skills", "remove": ["cherry_tomato_1", "cherry_tomato_2", "cherry_tomato_3"],
              "distractors": ["paperback_book", "wooden_block_a", "kitchen_sponge"]},
    "variants": {"at_island": {"note": "the robot starts at its default spot in front of the island", "move": {}}},
    "watch": CONTENTS,
    "goal": {"all": [["observed", CONTENTS[0]], ["observed", CONTENTS[1]], ["is_closed", CAB], ["hand_empty", "right"]]},
    "nominal": "nominal", "oracle": {"at_island": "nominal"},
    "routes": {"nominal": {"kind": "nominal", "variants": ["at_island"], "steps": _t18}},
    "vary": {"at_island": vary()},
    "not_adopted": [{"condition": "take a clean bowl out of the cabinet to the dining table",
                     "reason": "pick of the bowl on the cabinet's inside shelf: no reachable grasp from any base pose, "
                               "at its source spot and moved to the shelf front (s10, benchmark/runs/v3_normal)"},
                    {"condition": "start in the dining room",
                     "reason": "the cabinet is a known place: navigate reaches it from anywhere, no decision"},
                    {"condition": "knock before opening (source task knock_then_open)",
                     "reason": "knocking on one's own cabinet is not a household need; knock stays covered by probe P12"},
                    {"condition": "cabinet initially open (close first)",
                     "reason": "the scene overlay moves and removes objects only; it cannot set a joint state"}],
})


# v2 route kinds that were search-only (no physical repair): reclassified as explore
EXPLORE_ROUTES = {("T08_wipe_island", "nominal_from_tv_stand"), ("T08_wipe_island", "oracle_approach"),
                  ("T08_wipe_island", "hard_search_approach"), ("T10_trash_the_can", "search_first"),
                  ("T10_trash_the_can", "hard_explore_search")}


def build(ext_all=None, new_tasks=None):
    ext_all = EXT if ext_all is None else ext_all
    tasks = copy.deepcopy(v2.TASKS) + copy.deepcopy(NEW_TASKS if new_tasks is None else new_tasks)
    for t in tasks:
        tid = t["task_id"]
        ext = ext_all.get(tid, {})
        t["benchmark_version"] = VERSION
        t["eval_seeds"] = EVAL_SEEDS
        for name, var in ext.get("variants", {}).items():
            assert name not in t["variants"], (tid, name)
            t["variants"][name] = copy.deepcopy(var)
            t["variants"][name]["since"] = VERSION
        since = t.setdefault("since", "v2")
        for name, var in t["variants"].items():
            var.setdefault("since", since)
            vy = {**V2_VARY.get(tid, {}), **ext.get("vary", {})}
            if name in vy:
                var["vary"] = vy[name]
            tag_conditions(var)
        for name, r in ext.get("routes", {}).items():
            assert name not in t["routes"], (tid, name)
            t["routes"][name] = copy.deepcopy(r)
            t["routes"][name]["since"] = VERSION
        for name, r in t["routes"].items():
            r.setdefault("since", since)
            if (tid, name) in EXPLORE_ROUTES:
                r["kind"] = "explore"
        t["oracle"].update(ext.get("oracle", {}))
        t["not_adopted"] = ext.get("not_adopted", [])
    return tasks


def main():
    out = OUT
    if "--candidates" in sys.argv:
        import v3_candidates
        cand = v3_candidates.EXT
        CONDITIONS.update(v3_candidates.CONDITIONS)       # (imported as a separate module when run as a script)
        tasks = build({**EXT, **cand}, NEW_TASKS + v3_candidates.NEW_TASKS)
        out = Path(sys.argv[sys.argv.index("--candidates") + 1])
    else:
        tasks = build()
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"schema_version": 3, "benchmark_version": VERSION, "kind": "zenobench_benchmark_tasks",
                               "note": __doc__.strip().splitlines()[0], "eval_seeds": EVAL_SEEDS,
                               "condition_registry": {k: {"type": a, "decision": b, "meaning": c}
                                                      for k, (a, b, c) in CONDITIONS.items()},
                               "tasks": tasks + copy.deepcopy(v2.PROBES)}, indent=1))
    nv = sum(len(t["variants"]) for t in tasks)
    print(f"{len(tasks)} tasks, {nv} variants + {len(v2.PROBES)} probes -> {out}")


if __name__ == "__main__":
    main()
