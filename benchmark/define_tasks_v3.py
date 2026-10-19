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
