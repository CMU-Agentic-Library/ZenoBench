"""Physics sanity check of a scene USD: every free rigid body must settle
(drift < 1 cm over the settle time, no fall-through), articulated parts must
stay closed, the robot must hold its pose.  Optionally renders previews.

    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} \
        tools/check_scene.py sim/zeno_house.usd --out sim/checks/zeno_house \
        [--view name ex ey ez tx ty tz ...]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--view", nargs=7, action="append", default=[],
                    metavar=("NAME", "EX", "EY", "EZ", "TX", "TY", "TZ"))
    ap.add_argument("--res", nargs=2, type=int, default=[720, 1280])
    args = ap.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "enable_cameras": bool(args.view), "no_splash": True,
                       "fast_shutdown": True}).app
    import numpy as np
    import omni.usd
    import torch
    import isaaclab.sim as sim_utils
    from isaacsim.core.prims import SingleArticulation, SingleRigidPrim
    from pxr import Usd, UsdPhysics

    omni.usd.get_context().open_stage(str(ROOT / args.scene))
    for _ in range(10):
        app.update()
    stage = omni.usd.get_context().get_stage()
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1 / 120, device="cpu",
                                                              physics_prim_path="/World/PhysicsScene"))
    cams = []
    if args.view:
        from isaaclab.sensors import Camera, CameraCfg
        H, W = args.res
        for i, v in enumerate(args.view):
            cams.append((v[0], [float(x) for x in v[1:]], Camera(CameraCfg(
                prim_path=f"/World/CheckCam{i}", update_period=0, height=H, width=W, data_types=["rgb"],
                spawn=sim_utils.PinholeCameraCfg(focal_length=14.0, clipping_range=(0.05, 40.0))))))
    bodies = []
    for group in ("/World/TaskAssets", "/World/Tasks"):
        g = stage.GetPrimAtPath(group)
        if g:
            bodies += [p for p in Usd.PrimRange(g) if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    joints = [p for p in Usd.PrimRange(stage.GetPrimAtPath("/World/ArticulatedAssets"))
              if p.IsA(UsdPhysics.RevoluteJoint) or p.IsA(UsdPhysics.PrismaticJoint)]
    sim.reset()
    rigid = {}
    for i, b in enumerate(bodies):
        r = SingleRigidPrim(str(b.GetPath()), name=f"b{i}")
        r.initialize()
        rigid[str(b.GetPath())] = r
    arts = {}
    for i, j in enumerate(joints):
        a = SingleArticulation(str(j.GetParent().GetParent().GetPath()), name=f"a{i}")
        a.initialize()
        arts[str(j.GetPath())] = a
    robot = SingleArticulation("/World/ZenoMalo/Asset", name="zeno")
    robot.initialize()
    p0 = {k: r.get_world_pose()[0].cpu().numpy().copy() for k, r in rigid.items()}
    rb0 = robot.get_world_pose()[0].cpu().numpy().copy()
    for c in cams:
        c[2].set_world_poses_from_view(torch.tensor([c[1][:3]]), torch.tensor([c[1][3:]]))
    n = int(args.seconds * 120)
    for i in range(n):
        sim.step(render=bool(cams) and i >= n - 3)
    for name, _, cam in cams:
        cam.update(1 / 120)
        import imageio.v2 as imageio
        imageio.imwrite(out / f"{name}.png", cam.data.output["rgb"][0, ..., :3].cpu().numpy())
    res = {"scene": args.scene, "seconds": args.seconds, "objects": {}, "articulations": {}}
    bad = []
    for k, r in rigid.items():
        p = r.get_world_pose()[0].cpu().numpy()
        d = float(np.linalg.norm(p - p0[k]))
        res["objects"][k] = {"drift_m": round(d, 4), "z0": round(float(p0[k][2]), 4), "z": round(float(p[2]), 4)}
        if d > 0.01 or p[2] < 0.0:
            bad.append(k)
    for k, a in arts.items():
        q = float(a.get_joint_positions()[0])
        res["articulations"][k] = round(q, 5)
        if abs(q) > 0.02:
            bad.append(k)
    rb = robot.get_world_pose()[0].cpu().numpy()
    res["robot_drift_m"] = round(float(np.linalg.norm(rb - rb0)), 4)
    res["unstable"] = bad
    res["pass"] = not bad and res["robot_drift_m"] < 0.01
    (out / "check.json").write_text(json.dumps(res, indent=1))
    print("CHECK", "PASS" if res["pass"] else "FAIL", "unstable:", bad, "robot drift", res["robot_drift_m"],
          flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
