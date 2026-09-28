"""Run a sequence of annotation-driven Zeno skills in any scene and record it.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/run_skills.py \
        --scene sim/zeno_house.usd --ann annotations/zeno_house.json --out runs/demo \
        --plan "open KitchenCabinetFactory_7025538_spawn_asset_6631478" \
               "close KitchenCabinetFactory_7025538_spawn_asset_6631478"

Plan steps:  open <art> | close <art> | pick <obj> | place <obj> <support> <x> <y>
             | goto <x> <y> <yaw_deg>
"""

from __future__ import annotations

import argparse
import json
import math
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

    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "enable_cameras": not args.no_video, "no_splash": True,
                       "fast_shutdown": True}).app
    import numpy as np
    import omni.usd
    import torch
    import isaaclab.sim as sim_utils
    from isaacsim.core.prims import SingleArticulation
    from zeno_skills import skills as S
    from zeno_skills.annotations import SceneAnnotations
    from zeno_skills.collision import WorldModel
    from zeno_skills.kinematics import ArmKin
    from zeno_skills.rig import Rig, SkillFailure

    report = {"scene": args.scene, "plan": args.plan, "steps": [], "success": False,
              "written_state": "robot drive targets and base anchor only"}
    rig = None
    try:
        omni.usd.get_context().open_stage(str(ROOT / args.scene))
        for _ in range(10):
            app.update()
        stage = omni.usd.get_context().get_stage()
        sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1 / 120, device="cpu",
                                                                  physics_prim_path="/World/PhysicsScene"))
        cams = {}
        if not args.no_video:
            from isaaclab.sensors import Camera, CameraCfg
            H, W = args.res
            for k, f in (("follow", 13.0), ("wide", 11.0)):
                cams[k] = Camera(CameraCfg(prim_path=f"/World/RunCam_{k}", update_period=0, height=H, width=W,
                                           data_types=["rgb"], spawn=sim_utils.PinholeCameraCfg(
                                               focal_length=f, clipping_range=(0.05, 40.0))))
        robot = SingleArticulation("/World/ZenoMalo/Asset", name="zeno")
        sim.reset()
        robot.initialize()
        ann = SceneAnnotations(ROOT / args.ann)
        kin = ArmKin()
        world = WorldModel(ann)
        kin.scene = world
        rig = Rig(sim, stage, robot, kin, world, ann, cams=cams, stride=args.stride,
                  log=lambda s: print(s, flush=True))

        if cams:
            orig_step = rig.step

            def step_with_cams(n=1):
                # cameras follow the base: over-the-shoulder + a higher wide view
                for _ in range(n):
                    if rig.tick % rig.stride == 0:
                        x, y, yaw = rig.base_pose()
                        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

                        def w(u, v, z):
                            return [x + c * u - s * v, y + s * u + c * v, z]
                        f32 = torch.float32
                        cams["follow"].set_world_poses_from_view(torch.tensor([w(-1.1, 1.0, 1.75)], dtype=f32),
                                                                 torch.tensor([w(0.55, -0.25, 0.55)], dtype=f32))
                        cams["wide"].set_world_poses_from_view(torch.tensor([w(-2.2, -1.2, 2.4)], dtype=f32),
                                                               torch.tensor([w(0.4, 0.0, 0.5)], dtype=f32))
                    orig_step(1)
            rig.step = step_with_cams
        rig.caption = "start"
        rig.step(60)
        for raw in args.plan:
            tok = raw.split()
            t0 = time.time()
            row = {"step": raw}
            report["steps"].append(row)
            if tok[0] == "open":
                row["result_q"] = S.open_articulated(rig, tok[1])
            elif tok[0] == "close":
                row["result_q"] = S.close_articulated(rig, tok[1])
            elif tok[0] == "pick":
                S.pick(rig, tok[1])
            elif tok[0] == "place":
                S.place(rig, tok[1], tok[2], (float(tok[3]), float(tok[4])))
            elif tok[0] == "goto":
                S.navigate(rig, (float(tok[1]), float(tok[2]), float(tok[3])))
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
