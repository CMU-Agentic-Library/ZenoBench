"""Add a cooking corner (prep island + electric stove) in the living room.

The default footprint (x 6.55-8.85, y 1.53-1.98) was chosen by a search that keeps
the base paths start <-> microwave, microwave/fridge <-> dining table and to the
bookcase and TV stand open, keeps the refrigerator's door-ride poses free, and
leaves 1 m of free floor along both long sides.

Output: sim/zeno_house_kitchen.usd, a layer over sim/zeno_house_appliances.usd.
The house and the appliance layer are not modified.  The fixtures are static
colliders under /World/Appliances; each carries ``zeno:fixture`` custom data
that tools/annotate_scene.py turns into an obstacle box, a support surface and
(for the stove) an ``appliances`` record with the burner disc and the power
button.  The burner itself is a task-level heat source (zeno_skills/thermal.py)
switched by physically pressing the power button.

    OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/build_kitchen_scene.py
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "sim/zeno_house_kitchen.usd"
BASE = ROOT / "sim/zeno_house_appliances.usd"

TOP_Z = 0.86          # counter height, same as the kitchen counter repair top
STOVE_Z = 0.70        # low hob: a lid knob on a pot stays inside the arm's top-down reach (~0.9 m)
DEPTH = 0.45


def cube(stage, path, pos, size, color, collision=True):
    from pxr import Gf, UsdGeom, UsdPhysics
    g = UsdGeom.Cube.Define(stage, path)
    g.CreateSizeAttr(1.0)
    g.AddTranslateOp().Set(Gf.Vec3d(*pos))
    g.AddScaleOp().Set(Gf.Vec3f(*size))
    g.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    if collision:
        UsdPhysics.CollisionAPI.Apply(g.GetPrim())
    return g.GetPrim()


def disc(stage, path, pos, radius, height, color):
    from pxr import Gf, UsdGeom
    g = UsdGeom.Cylinder.Define(stage, path)
    g.CreateRadiusAttr(radius)
    g.CreateHeightAttr(height)
    g.CreateAxisAttr("Z")
    g.AddTranslateOp().Set(Gf.Vec3d(*pos))
    g.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    return g.GetPrim()


def build(island_x, stove_x, front_y):
    from pxr import Sdf, Usd, UsdGeom
    layer = Sdf.Layer.FindOrOpen(str(OUT)) if OUT.exists() else Sdf.Layer.CreateNew(str(OUT))
    layer.Clear()
    layer.subLayerPaths.append(os.path.relpath(BASE, OUT.parent))
    layer.Save()
    stage = Usd.Stage.Open(str(OUT))
    stage.SetEditTarget(stage.GetRootLayer())
    UsdGeom.Xform.Define(stage, "/World/Appliances")
    cy = front_y + DEPTH / 2

    # Prep island: a plain counter whose top is a support surface.
    ix0, ix1 = island_x
    island = UsdGeom.Xform.Define(stage, "/World/Appliances/kitchen_island").GetPrim()
    island.SetCustomDataByKey("zeno:fixture", "counter")
    cube(stage, "/World/Appliances/kitchen_island/body", ((ix0 + ix1) / 2, cy, (TOP_Z - 0.03) / 2),
         (ix1 - ix0, DEPTH, TOP_Z - 0.03), (0.80, 0.78, 0.74))
    cube(stage, "/World/Appliances/kitchen_island/top", ((ix0 + ix1) / 2, cy, TOP_Z - 0.015),
         (ix1 - ix0 + 0.02, DEPTH + 0.02, 0.03), (0.93, 0.93, 0.91))

    # Stove: cabinet, glass cooktop, a visible burner disc and a front power key.
    sx0, sx1 = stove_x
    sxc = (sx0 + sx1) / 2
    stove = UsdGeom.Xform.Define(stage, "/World/Appliances/kitchen_stove").GetPrim()
    stove.SetCustomDataByKey("zeno:fixture", "stove")
    cube(stage, "/World/Appliances/kitchen_stove/body", (sxc, cy, (STOVE_Z - 0.03) / 2),
         (sx1 - sx0, DEPTH, STOVE_Z - 0.03), (0.30, 0.31, 0.33))
    cube(stage, "/World/Appliances/kitchen_stove/cooktop", (sxc, cy, STOVE_Z - 0.015),
         (sx1 - sx0 + 0.02, DEPTH + 0.02, 0.03), (0.06, 0.06, 0.07))
    # Two burners: the pot starts on the left one, the right one stays free
    # for placing a vessel (mug, bowl) to heat it.
    for bname, bx in (("burner", sx0 + 0.16), ("burner_right", sx1 - 0.15)):
        b = disc(stage, f"/World/Appliances/kitchen_stove/{bname}", (bx, front_y + 0.20, STOVE_Z + 0.001),
                 0.10, 0.002, (0.55, 0.12, 0.08))
        b.SetCustomDataByKey("zeno:burner_radius", 0.10)
    # The key sits on a stem 4 cm in front of the face so the closed fingertips
    # press it without the wrist touching the cooktop edge (as on the microwave).
    key = cube(stage, "/World/Appliances/kitchen_stove/power_button", (sx1 - 0.08, front_y - 0.045, STOVE_Z - 0.10),
               (0.03, 0.016, 0.03), (0.92, 0.32, 0.14))
    key.SetCustomDataByKey("zeno:button", "power_button")
    cube(stage, "/World/Appliances/kitchen_stove/power_button_stem", (sx1 - 0.08, front_y - 0.019, STOVE_Z - 0.10),
         (0.012, 0.038, 0.012), (0.45, 0.20, 0.10), collision=False)
    # The appliance layer's refrigerator door stops at 35 deg: at the 65 %
    # "open" goal its free end leaves ~6 cm beside the cabinet and no arm can
    # put a can on the shelf.  A real door swings ~100 deg; the sweep is free
    # of furniture up to 100 deg here, so this layer widens the limit (the
    # appliance layer and the heat_breakfast tasks built on it are unchanged).
    hinge = stage.OverridePrim("/World/ArticulatedAssets/breakfast_fridge/joints/fridge_door_hinge")
    hinge.CreateAttribute("physics:lowerLimit", Sdf.ValueTypeNames.Float).Set(-100.0)
    # Bind the household contact material (same friction as furniture tops) to
    # every collider of the fixtures; unbound colliders fall back to PhysX defaults.
    from pxr import UsdPhysics
    from zeno_skills import physics as P
    mats = P.materials(stage)
    for prim in Usd.PrimRange(stage.GetPrimAtPath("/World/Appliances")):
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            P.bind(prim, mats[P.OBJECT_MATERIAL])
    stage.GetRootLayer().customLayerData = {"fixtures": "kitchen_island + kitchen_stove",
                                            "island_x": f"{ix0},{ix1}", "stove_x": f"{sx0},{sx1}",
                                            "front_y": f"{front_y}"}
    stage.GetRootLayer().Save()
    print("KITCHEN_SCENE", OUT, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--island-x", nargs=2, type=float, default=(6.55, 8.25))
    ap.add_argument("--stove-x", nargs=2, type=float, default=(8.25, 8.85))
    ap.add_argument("--front-y", type=float, default=1.525)
    args = ap.parse_args()
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    build(args.island_x, args.stove_x, args.front_y)
    app.close()


if __name__ == "__main__":
    main()
