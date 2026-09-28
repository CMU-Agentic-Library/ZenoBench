"""Drop-and-settle: simulate, then write every free body's rest pose back into
the scene USD so loading starts at rest (no initial floating or
interpenetration).  Bodies that end below 5 cm (fell to the floor) or moved
more than --max-move are reported and NOT written.

    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} \
        tools/settle_scene.py sim/zeno_house.usd
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--max-move", type=float, default=0.25)
    ap.add_argument("--layer", help="write into this layer (default: the scene root layer)")
    args = ap.parse_args()
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    import numpy as np
    import omni.usd
    import isaaclab.sim as sim_utils
    from isaacsim.core.prims import SingleRigidPrim
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    path = str(ROOT / args.scene)
    omni.usd.get_context().open_stage(path)
    for _ in range(10):
        app.update()
    stage = omni.usd.get_context().get_stage()
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1 / 120, device="cpu",
                                                              physics_prim_path="/World/PhysicsScene"))
    bodies = []
    for group in ("/World/TaskAssets", "/World/Tasks"):
        g = stage.GetPrimAtPath(group)
        if g:
            bodies += [p for p in Usd.PrimRange(g) if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    cache = UsdGeom.XformCache()
    info = []
    for b in bodies:
        inst = b
        while inst.GetParent().GetPath() not in (Sdf.Path("/World/TaskAssets"), Sdf.Path("/World/Tasks")) and \
                inst.GetParent().GetParent():
            inst = inst.GetParent()
        Mb = cache.GetLocalToWorldTransform(b)
        Mi = cache.GetLocalToWorldTransform(inst)
        info.append((b, inst, Mb * Mi.GetInverse()))       # body in instance frame
    sim.reset()
    rig = []
    for i, (b, _, _) in enumerate(info):
        r = SingleRigidPrim(str(b.GetPath()), name=f"s{i}")
        r.initialize()
        rig.append(r)
    p0 = [r.get_world_pose()[0].cpu().numpy().copy() for r in rig]
    for _ in range(int(args.seconds * 120)):
        sim.step(render=False)
    poses = [(r.get_world_pose()[0].cpu().numpy(), r.get_world_pose()[1].cpu().numpy()) for r in rig]
    vel = [float(np.linalg.norm(r.get_linear_velocity().cpu().numpy())) for r in rig]
    edits = []
    for (b, inst, Mbi), (p, q), p_0, v in zip(info, poses, p0, vel):
        move = float(np.linalg.norm(p - p_0))
        fell = p[2] < 0.05 and p_0[2] > 0.10          # dropped to the floor from a support
        if fell or move > args.max_move or v > 0.02:
            print("SKIP", inst.GetName(), "move", round(move, 3), "z", round(float(p[2]), 3), "v", round(v, 3))
            continue
        Mb_new = Gf.Matrix4d().SetRotate(Gf.Quatd(float(q[0]), float(q[1]), float(q[2]), float(q[3]))) * \
            Gf.Matrix4d().SetTranslate(Gf.Vec3d(*[float(x) for x in p]))
        Mi_new = Mbi.GetInverse() * Mb_new
        parent = cache.GetLocalToWorldTransform(inst.GetParent())
        edits.append((inst.GetPath(), Mi_new * parent.GetInverse(), move))
    # write into a fresh stage (the simulated one has fabric state)
    st = Usd.Stage.Open(path)
    if args.layer:
        st.SetEditTarget(Sdf.Layer.FindOrOpen(str(ROOT / args.layer)))
    for pth, local, move in edits:
        x = UsdGeom.Xformable(st.GetPrimAtPath(pth))
        scale = None
        for op in x.GetOrderedXformOps():
            if op.GetOpType() == UsdGeom.XformOp.TypeScale:
                scale = op.Get()
        x.ClearXformOpOrder()
        t = local.ExtractTranslation()
        r = local.RemoveScaleShear().ExtractRotationQuat()
        x.AddTranslateOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(t))
        x.AddOrientOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(r))
        if scale is not None:
            x.AddScaleOp().Set(scale)
        print("SETTLED", pth.name, "moved", round(move, 4))
    st.GetEditTarget().GetLayer().Save()
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
