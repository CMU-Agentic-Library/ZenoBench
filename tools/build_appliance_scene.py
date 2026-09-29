"""Build the task-specific articulated fridge and serviceable microwave scene.

The base house is not modified. The microwave retains its physical door,
relocated onto its own stand with a complete shell and button-driven hinge; the
fridge is a new procedural, open-cavity USD articulation. Run with the Isaac Lab Python environment.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'sim/zeno_house_appliances.usd'
BASE = ROOT / 'sim/zeno_house.usd'


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


def build(microwave_xy, fridge_xy):
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, PhysxSchema
    from zeno_skills.physics import fix_articulation

    layer = Sdf.Layer.FindOrOpen(str(OUT)) if OUT.exists() else Sdf.Layer.CreateNew(str(OUT))
    layer.Clear()
    layer.subLayerPaths.append(os.path.relpath(BASE, OUT.parent))
    layer.Save()
    stage = Usd.Stage.Open(str(OUT))
    stage.SetEditTarget(stage.GetRootLayer())

    # Keep the existing microwave's contact-tested door and cavity. The original
    # position has a feasible handle grasp but no collision-free door ride.
    mroot = '/World/ArticulatedAssets/kitchen_microwave'
    root = stage.GetPrimAtPath(mroot)
    mx, my = microwave_xy
    root.GetAttribute('xformOp:translate').Set(Gf.Vec3d(mx, my, 0.70))
    cube(stage, mroot + '/base/stand', (0, 0, -0.35), (0.52, 0.38, 0.70), (0.19, 0.22, 0.26))
    cube(stage, mroot + '/base/start_button', (0.207, -0.302, 0.204),
         (0.025, 0.014, 0.025), (0.11, 0.82, 0.36))
    cube(stage, mroot + '/base/door_button', (0.207, -0.302, 0.315),
         (0.025, 0.014, 0.025), (0.12, 0.60, 0.92))
    hinge = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath(mroot + '/joints/microwave_door_hinge'))
    hinge.CreateLowerLimitAttr().Set(-85.0)
    drive = UsdPhysics.DriveAPI.Get(hinge.GetPrim(), 'angular')
    drive.GetStiffnessAttr().Set(120.0)
    drive.GetDampingAttr().Set(12.0)
    drive.GetMaxForceAttr().Set(120.0)
    drive.CreateTargetPositionAttr().Set(0.0)

    # Preserve a complete box around the cavity. Keep the hinge frame fixed.
    for part in ('floor', 'roof', 'left', 'right', 'rear', 'control', 'stand', 'start_button', 'door_button'):
        prim = stage.GetPrimAtPath(mroot + '/base/' + part)
        for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
            if op.GetOpName() in ('xformOp:translate', 'xformOp:scale'):
                v = op.Get()
                z = v[2]
                if part == 'roof' and op.GetOpName() == 'xformOp:translate':
                    z += 0.10
                elif part in ('left', 'right', 'rear', 'control'):
                    z += 0.05 if op.GetOpName() == 'xformOp:translate' else 0.10
                op.Set(type(v)(v[0], v[1], z))
    # A visible stem brings the physical start key in front of the oven face,
    # where Zeno's closed fingertips can reach it without striking the panel.
    cube(stage, mroot + '/base/start_button_stem', (0.114, -0.250, 0.204),
         (0.012, 0.105, 0.012), (0.11, 0.45, 0.30), collision=False)
    cube(stage, mroot + '/base/door_button_stem', (0.207, -0.250, 0.315),
         (0.012, 0.105, 0.012), (0.12, 0.38, 0.60), collision=False)
    for part in ('window', 'handle', 'handle_top_standoff', 'handle_bottom_standoff'):
        prim = stage.GetPrimAtPath(mroot + '/door/' + part)
        for op in UsdGeom.Xformable(prim).GetOrderedXformOps():
            if op.GetOpName() in ('xformOp:translate', 'xformOp:scale'):
                v = op.Get()
                z = v[2]
                if part == 'window':
                    z += 0.05 if op.GetOpName() == 'xformOp:translate' else 0.10
                op.Set(type(v)(v[0], v[1], z))

    # Compact refrigerator, front toward -Y, with an unobstructed interior
    # shelf at a Zeno-reachable height. The door hinges on its left edge.
    fx, fy = fridge_xy
    root_path = '/World/ArticulatedAssets/breakfast_fridge'
    froot = UsdGeom.Xform.Define(stage, root_path)
    froot.AddTranslateOp().Set(Gf.Vec3d(fx, fy, 0.0))
    body = UsdGeom.Xform.Define(stage, root_path + '/base')
    UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
    UsdPhysics.MassAPI.Apply(body.GetPrim()).CreateMassAttr().Set(45.0)
    white = (0.86, 0.90, 0.92)
    inside = (0.68, 0.75, 0.80)
    cube(stage, root_path + '/base/bottom', (0, 0, 0.05), (.60, .58, .10), white)
    cube(stage, root_path + '/base/left', (-.285, 0, .70), (.03, .58, 1.30), white)
    cube(stage, root_path + '/base/right', (.285, 0, .70), (.03, .58, 1.30), white)
    cube(stage, root_path + '/base/rear', (0, .275, .70), (.60, .03, 1.30), white)
    cube(stage, root_path + '/base/roof', (0, 0, 1.35), (.60, .58, .06), white)
    cube(stage, root_path + '/base/shelf', (0, 0, .79), (.54, .52, .025), inside)
    cube(stage, root_path + '/base/shelf_back', (0, .20, .84), (.52, .03, .08), inside)
    cube(stage, root_path + '/base/plinth', (0, -.305, .06), (.60, .03, .12), (0.22, .28, .32))

    door = UsdGeom.Xform.Define(stage, root_path + '/door')
    door.AddTranslateOp().Set(Gf.Vec3d(-.285, -.297, .69))
    UsdPhysics.RigidBodyAPI.Apply(door.GetPrim())
    UsdPhysics.MassAPI.Apply(door.GetPrim()).CreateMassAttr().Set(2.0)
    PhysxSchema.PhysxRigidBodyAPI.Apply(door.GetPrim()).CreateEnableCCDAttr().Set(True)
    UsdPhysics.FilteredPairsAPI.Apply(door.GetPrim()).CreateFilteredPairsRel().AddTarget(body.GetPath())
    cube(stage, root_path + '/door/panel', (.285, 0, 0), (.57, .035, 1.24), (0.68, 0.81, 0.87))
    cube(stage, root_path + '/door/trim', (.285, -.022, .47), (.54, .009, .19), (0.46, 0.62, 0.69), False)
    cube(stage, root_path + '/door/handle', (.515, -.095, .05), (.025, .025, .20), (0.78, 0.80, 0.82))
    cube(stage, root_path + '/door/handle_top_standoff', (.515, -.058, .13),
         (.025, .075, .016), (0.78, 0.80, 0.82))
    cube(stage, root_path + '/door/handle_bottom_standoff', (.515, -.058, -.03),
         (.025, .075, .016), (0.78, 0.80, 0.82))

    fixed = UsdPhysics.FixedJoint.Define(stage, root_path + '/root_joint')
    UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
    PhysxSchema.PhysxArticulationAPI.Apply(fixed.GetPrim()).CreateEnabledSelfCollisionsAttr().Set(False)
    fixed.CreateBody1Rel().SetTargets([body.GetPath()])
    fixed.CreateLocalPos0Attr().Set(Gf.Vec3f(fx, fy, 0))
    fixed.CreateLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
    hinge = UsdPhysics.RevoluteJoint.Define(stage, root_path + '/joints/fridge_door_hinge')
    hinge.CreateBody0Rel().SetTargets([body.GetPath()])
    hinge.CreateBody1Rel().SetTargets([door.GetPath()])
    hinge.CreateLocalPos0Attr().Set(Gf.Vec3f(-.285, -.297, .69))
    hinge.CreateLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
    hinge.CreateAxisAttr().Set('Z')
    hinge.CreateLowerLimitAttr().Set(-35.0)
    hinge.CreateUpperLimitAttr().Set(0.0)
    fix_articulation(stage, str(hinge.GetPath()), damping=.08)

    stage.GetRootLayer().customLayerData = {'appliances': 'microwave + breakfast_fridge',
                                             'microwave_xy': f'{mx},{my}',
                                             'fridge_xy': f'{fx},{fy}'}
    stage.GetRootLayer().Save()
    print('APPLIANCE_SCENE', OUT, 'microwave', microwave_xy, 'fridge', fridge_xy, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--microwave-xy', nargs=2, type=float, default=(4.5, 2.5))
    ap.add_argument('--fridge-xy', nargs=2, type=float, default=(5.9, 3.3))
    args = ap.parse_args()
    from isaaclab.app import AppLauncher
    app = AppLauncher({'headless': True, 'no_splash': True, 'fast_shutdown': True}).app
    build(args.microwave_xy, args.fridge_xy)
    app.close()


if __name__ == '__main__':
    main()
