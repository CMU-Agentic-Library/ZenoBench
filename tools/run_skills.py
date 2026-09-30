"""Run a sequence of annotation-driven Zeno skills in any scene and record it.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/run_skills.py \
        --scene sim/zeno_house.usd --ann annotations/zeno_house.json --out runs/demo \
        --plan "open KitchenCabinetFactory_7025538_spawn_asset_6631478" \
               "close KitchenCabinetFactory_7025538_spawn_asset_6631478"

Plan steps:  open <art> | close <art> | pick <obj>
             | place <obj> in:<container>          drop into a container
             | place <obj> <support> [<x> <y>]      free spot on a support (near x, y)
             | push <obj> <dx> <dy>                 slide along its support (world m)
             | goto <x> <y> <yaw_deg>
Supports may be aliases from task_specs/places.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--ann", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", nargs="+", required=True)
    ap.add_argument("--res", nargs=2, type=int, default=[720, 1280])
    ap.add_argument("--stride", type=int, default=4)
    ap.add_argument("--no-video", action="store_true")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    from zeno_skills.runtime import launch
    app = launch(not args.no_video)
    import numpy as np
    from zeno_skills.policies import PolicySuite
    from zeno_skills.rig import SkillFailure
    from zeno_skills.runtime import make_rig
    from zeno_skills.tasks import load_places, resolve_place

    places = load_places()
    report = {"scene": args.scene, "plan": args.plan, "steps": [], "success": False,
              "written_state": "robot drive targets and base anchor only"}
    rig = None
    try:
        rig = make_rig(app, args.scene, args.ann, video=not args.no_video, res=args.res, stride=args.stride)
        rig.caption = "start"
        rig.step(60)
        policies = PolicySuite(rig)
        for raw in args.plan:
            tok = raw.split()
            t0 = time.time()
            row = {"step": raw}
            report["steps"].append(row)
            if tok[0] == "open":
                row["result_q"] = policies.open.execute(tok[1])
            elif tok[0] == "close":
                row["result_q"] = policies.close.execute(tok[1])
            elif tok[0] == "pick":
                policies.pick.execute(tok[1])
            elif tok[0] == "place" and tok[2].startswith("in:"):
                policies.place.execute(tok[1], tok[2])
            elif tok[0] == "place":
                hint = (float(tok[3]), float(tok[4])) if len(tok) >= 5 else None
                policies.place.on(tok[1], resolve_place(tok[2], places), hint=hint)
            elif tok[0] == "push":
                d = np.array([float(tok[2]), float(tok[3])])
                sup = rig.geo.support_under(tok[1], rig.state())
                if sup is None:
                    raise SkillFailure(f"push {tok[1]}: not on an annotated support")
                row["moved_m"] = policies.push.execute(tok[1], sup, d / np.linalg.norm(d), float(np.linalg.norm(d)))
            elif tok[0] == "goto":
                policies.navigate.execute((float(tok[1]), float(tok[2]), float(tok[3])))
            else:
                raise ValueError(raw)
            row["success"] = True
            row["wall_s"] = round(time.time() - t0, 1)
        rig.caption = "done"
        rig.step(60)
        report["success"] = True
    except Exception as exc:
        report["failure"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print("FAIL", report["failure"], flush=True)
    finally:
        if rig is not None:
            report["events"] = rig.events
            if not args.no_video:
                report["video"] = str(rig.write_video(out / "run.mp4"))
        (out / "result.json").write_text(json.dumps(report, indent=1, default=float))
        print("RESULT", out / "result.json", "SUCCESS", report["success"], flush=True)
        sys.stdout.flush()
        os._exit(0 if report["success"] else 3)


if __name__ == "__main__":
    main()
