"""In-simulator permission tests of the observation-limited interface
(episode.episode.Episode with profiles/benchmark.yaml).

    $ISAACLAB_PYTHON benchmark/tests/sim_permissions.py      # -> benchmark/tests/results/sim_permissions.json

Checks on the real kitchen_skills scene (GT physics, real head camera):

1. hidden (inside the closed cabinet) and non-existent objects get the same
   refusal for pick / navigate / fetch / collect, and nothing moves;
2. search for the hidden object and for a non-existent name run the same
   static sweep and return the same (masked) failure;
3. dynamic occlusion: the bowl inside the closed cabinet is not visible from
   in front of the cabinet; open + inspect + close observes it; after the
   door closes it is known but not in view, so pick is refused (NOT_IN_VIEW);
4. a pick does not track an object outside the current view;
5. explore_room chooses viewpoints and computes coverage from the static layout
   only (the number of coverage targets equals the static furniture count).
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sys
import traceback
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "benchmark/tests/results"


def main():
    import numpy as np
    from benchmark.scene import episode_config
    from episode.episode import Episode
    from episode.profile import load_profile
    checks, log = [], []

    def check(name, ok, detail=""):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        print("CHECK", name, "PASS" if ok else "FAIL", detail, flush=True)

    rig = None
    try:
        # the kitchen_skills scene as it is: no task goal, no overlay
        task = {"task_id": "sim_permissions", "scene": {"base": "tasks/kitchen_skills"},
                "variants": {"default": {}}, "goal": {"all": []}, "watch": []}
        ep = Episode(task, episode_config(task, 0), load_profile("benchmark"), OUT / "sim_permissions",
                     image_dir=OUT / "sim_permissions_images")
        rig = ep.rig
        s = SimpleNamespace(observer=ep.observer,
                            call=lambda verb, args: ep.call({"contract": verb, "args": args})[0])
        hidden, ghost = "bowl_inside_kitchen_cabinet", "golden_teapot"
        CAB = "kitchen_cabinet_6"

        def frozen():
            st = rig.state()
            return (np.round(rig.base_pose(), 4).tolist(), np.round(rig.q(), 4).tolist(),
                    {k: np.round(v["pos"], 4).tolist() for k, v in st["objects"].items()},
                    {k: round(v, 4) for k, v in st["joints"].items()})

        # 1 ------------------------------------------------------------------
        for verb, args in (("pick", {"object": "{}"}), ("navigate", {"destination": "{}"}),
                           ("fetch", {"object": "{}", "receptacle": "kitchen_island/top"}),
                           ("collect", {"objects": ["{}"], "container": "trash_can"}),
                           ("push", {"object": "{}", "direction_xy": [1.0, 0.0], "distance_m": 0.1})):
            def fill(n):
                return {k: ([n] if isinstance(v, list) else v.format(n) if isinstance(v, str) else v)
                        for k, v in args.items()}
            before = frozen()
            a = s.call(verb, fill(hidden))
            b = s.call(verb, fill(ghost))
            after = frozen()
            same = (a["error_code"], a["error"].replace(hidden, "X")) == (b["error_code"], b["error"].replace(ghost, "X"))
            check(f"{verb}: hidden == nonexistent feedback", same and not a["success"], f"{a['error']} | {b['error']}")
            check(f"{verb}: refusal moved nothing", before == after)

        # 2 ------------------------------------------------------------------
        # the sweep visits the room's 8 nearest supports in order of distance from the robot: both
        # searches start from the same pose (the first one ended elsewhere and chose another set, 1/1)
        import ast
        from zeno_skills import skills as _sk
        pose0 = rig.base_pose()
        a = s.call("search", {"object": hidden, "region": "living_room_0_0"})
        _sk.navigate(rig, tuple(pose0), label="test_return")   # same start pose for the second search
        log.append({"search_start": [round(float(v), 3) for v in pose0],
                    "second_start": [round(float(v), 3) for v in rig.base_pose()]})
        b = s.call("search", {"object": ghost, "region": "living_room_0_0"})

        def visited(fb, name):
            e = fb["error"] or ""
            head, _, rest = e.replace(name, "X").partition(" at ")
            return fb["error_code"], head, sorted(ast.literal_eval(rest)) if rest.startswith("[") else rest
        check("search: hidden == nonexistent feedback", not a["success"] and not b["success"]
              and visited(a, hidden) == visited(b, ghost), f"{a['error']} | {b['error']}")

        # 3 ------------------------------------------------------------------
        fb = s.call("navigate", {"destination": CAB})
        from zeno_skills.perception import dynamic_occluder, rig_head_pose, look_angles
        from zeno_skills.policies.perceive import drive_head
        c = rig.geo.centre(hidden, rig.state())
        yaw, pitch = look_angles(rig, c)
        drive_head(rig, yaw, pitch)
        cam, _ = rig_head_pose(rig)
        why = dynamic_occluder(rig, hidden, cam, np.asarray(c))
        check("closed cabinet occludes its contents", why is not None and "closed" in why and not s.observer.visible(hidden),
              str(why))
        # inspect of the closed cabinet parks at (3.37, 1.09), grips the handle and the door does not
        # move (3/3, also after a knock; with auto-recovery off there is no second park): open it from
        # the open skill's park after a knock (as P12, 2/2), inspect the open cabinet, close it
        s.call("knock", {"articulated": CAB})
        fo = s.call("open", {"articulated": CAB})
        fb = s.call("inspect", {"receptacle": CAB})
        fc = s.call("close", {"articulated": CAB})
        check("open, inspect, close observes the hidden bowl", fo["success"] and fb["success"] and fc["success"]
              and s.observer.known(hidden), json.dumps(fb.get("outputs")))
        fb = s.call("pick", {"object": hidden})
        check("known but behind the closed door: pick refused NOT_IN_VIEW", fb["error_code"] == "NOT_IN_VIEW", fb["error"])

        # 4 ------------------------------------------------------------------
        s.call("navigate", {"destination": "kitchen_island/top"})
        s.call("look", {"target": "kitchen_island/top"})
        seen = sorted(s.observer.view)
        check("look at the island observes objects", "wooden_block_a" in seen or "soda_can" in seen, str(seen))
        target = "wooden_block_a" if "wooden_block_a" in seen else seen[0]
        s.call("look", {"target": "breakfast_fridge"})          # turn away
        fb = s.call("pick", {"object": target})
        check("pick does not track an object outside the view", fb["error_code"] == "NOT_IN_VIEW", fb["error"])

        # 5 ------------------------------------------------------------------
        from zeno_skills.evaluator import room_of
        room = "living_room_0_0"
        static = len({s_["furniture"] for s_ in rig.ann.supports
                      if room_of(rig.ann.rooms, ((s_["aabb_xy"][0] + s_["aabb_xy"][2]) / 2,
                                                (s_["aabb_xy"][1] + s_["aabb_xy"][3]) / 2)) == room
                      and (s_["aabb_xy"][2] - s_["aabb_xy"][0]) * (s_["aabb_xy"][3] - s_["aabb_xy"][1]) > 0.05
                      and 0.3 <= s_["z"] <= 1.6 and s_.get("clearance", 1.0) >= 0.3})
        fb = s.call("explore_room", {"room": room})
        ev = [e for e in rig.events if e["label"] == "explore_result"]
        n_t = ev[-1]["targets"] if ev else None
        check("explore coverage targets = static furniture only", n_t == static, f"targets {n_t}, static {static}, "
              f"result {fb['success']} {fb['error']}")
    except Exception as exc:
        checks.append({"check": "crash", "passed": False, "detail": f"{type(exc).__name__}: {exc}",
                       "traceback": traceback.format_exc()})
        print("CRASH", exc, flush=True)
    finally:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "sim_permissions.json").write_text(json.dumps({"checks": checks,
                                                               "passed": all(c["passed"] for c in checks) and bool(checks)},
                                                              indent=1, default=str))
        print("RESULT", sum(c["passed"] for c in checks), "/", len(checks), flush=True)
        sys.stdout.flush()
        os._exit(0)


if __name__ == "__main__":
    main()
