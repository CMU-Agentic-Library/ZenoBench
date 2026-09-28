"""Bake the final Zeno house scene: sim/zeno_house.usd.

Starts from the (stability-checked) taskready scene and writes every physics
fix permanently (see zeno_skills/physics.py for what each fixes):
  * robot: damped drives, gravity compensation, movable base anchor, finger
    pad colliders, folded left arm, no floor-snagging base colliders
  * 15 cabinets + microwave: hinge/slide damping and friction
  * task objects: real inertia, thin-walled containers rebuilt as walls,
    household friction material
  * kitchen cabinet 6631478 (+ its bowl/plate/spoon) moved from the 1.2 m wide
    kitchen corridor, where Zeno cannot open it, to the living room wall
    (validated open/close/pick/place location)

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/bake_scene.py

Provenance note: this produced sim/zeno_house.usd once from the former
taskready scene, which was deleted in the clean-up (only the final scene is
kept).  sim/zeno_house.usd is now the source of truth; to re-apply physics
fixes to it, call the zeno_skills.physics functions on it directly.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "sim/scenes/breakfast_house_zeno_taskready.usd"
OUTPUT = ROOT / "sim/zeno_house.usd"

MOVE = {  # prim -> world offset (x, y, z)
    "/World/ArticulatedAssets/cabinets/KitchenCabinetFactory_7025538_spawn_asset_6631478": (4.70, -6.64, 0.03),
    "/World/TaskAssets/bowl_inside_kitchen_cabinet": (4.70, -6.64, 0.03),
    "/World/TaskAssets/plate_inside_kitchen_cabinet": (4.70, -6.64, 0.03),
    "/World/TaskAssets/spoon_kitchen_cabinet": (4.70, -6.64, 0.03),
}
ROBOT_START = (4.40, 1.90, -135.0)


def asset_type(prim):
    from pathlib import Path as P
    for q in (prim, prim.GetChild("Asset")):
        if q and q.HasAuthoredReferences():
            for ref in q.GetMetadata("references").GetAddedOrExplicitItems():
                return P(str(ref.assetPath)).stem
    return None


def main():
    if not SOURCE.exists():
        raise SystemExit(f"{SOURCE} was removed in the clean-up; sim/zeno_house.usd is the source of truth")
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    from pxr import Usd, UsdPhysics
    from zeno_skills import physics as P

    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    from pxr import Sdf
    src = Sdf.Layer.FindOrOpen(str(SOURCE))
    src.Export(str(OUTPUT))
    stage = Usd.Stage.Open(str(OUTPUT))
    mats = P.materials(stage)
    P.scene_settings(stage)

    for path, (dx, dy, dz) in MOVE.items():
        a = stage.GetPrimAtPath(path).GetAttribute("xformOp:translate")
        v = a.Get()
        a.Set(type(v)(v[0] + dx, v[1] + dy, v[2] + dz))

    # spoon_counter sat on the edge of a counter-top hole and slid off; rest it
    # on plate_counter_b instead
    pb = stage.GetPrimAtPath("/World/TaskAssets/plate_counter_b").GetAttribute("xformOp:translate").Get()
    sa = stage.GetPrimAtPath("/World/TaskAssets/spoon_counter").GetAttribute("xformOp:translate")
    v = sa.Get()
    sa.Set(type(v)(pb[0], pb[1], pb[2] + 0.035))

    P.fix_robot(stage, *ROBOT_START)

    n_joint = 0
    for prim in Usd.PrimRange(stage.GetPrimAtPath("/World/ArticulatedAssets")):
        if prim.IsA(UsdPhysics.RevoluteJoint) or prim.IsA(UsdPhysics.PrismaticJoint):
            P.fix_articulation(stage, str(prim.GetPath()))
            n_joint += 1

    report = {}
    for inst in stage.GetPrimAtPath("/World/TaskAssets").GetChildren():
        t = asset_type(inst)
        a = assets.get(t)
        if a is None:
            report[inst.GetName()] = "no asset annotation"
            continue
        path = str(inst.GetPath())
        P.set_box_inertia(stage, path, a["mass"])
        if a["collider"] != "solid" and a.get("container"):
            c = a["container"]
            n = P.container_collider(stage, path, c["bands"], shape=c["shape"], mats=mats)
            report[inst.GetName()] = f"{t}: container walls x{n}"
        else:
            P.solid_collider(stage, path, mats=mats)
            report[inst.GetName()] = f"{t}: solid"
    # start every free object 1 cm above its support; settle_scene.py then
    # drops it and bakes the true rest pose (no initial interpenetration)
    for inst in stage.GetPrimAtPath("/World/TaskAssets").GetChildren():
        a = inst.GetAttribute("xformOp:translate")
        v = a.Get()
        a.Set(type(v)(v[0], v[1], v[2] + 0.01))
    stage.GetRootLayer().customLayerData = {
        "zeno_house": "baked by tools/bake_scene.py; physics fixes in zeno_skills/physics.py"}
    stage.GetRootLayer().Save()
    print("BAKED", OUTPUT, "joints", n_joint, flush=True)
    for k, v in report.items():
        print("OBJ", k, v, flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
