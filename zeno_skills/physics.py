"""Physics fixes that are *baked into* the scene USD (tools/bake_scene.py) and
applied to every asset a task layer adds (tools/build_tasks.py).

Each function is idempotent and documents the bug it removes.
"""

from __future__ import annotations

import math

import numpy as np

ROBOT = "/World/ZenoMalo"
ASSET = ROBOT + "/Asset"
ANCHOR = ROBOT + "/base_anchor"
GRIP_MATERIAL = "/World/PhysicsMaterials/rubber_pad"
OBJECT_MATERIAL = "/World/PhysicsMaterials/household"
PHYSICS_HZ = 120            # physics steps per simulated second (CPU PhysX; sticky.py was checked at this rate)


def deinstance(stage, root_path):
    """Instanced (instanceable=True) prims silently ignore edits to their
    proxies; make the subtree editable."""
    from pxr import Usd
    root = stage.GetPrimAtPath(root_path)
    changed = True
    while changed:
        changed = False
        for prim in Usd.PrimRange(root, Usd.TraverseInstanceProxies()):
            if prim.IsInstance() and not prim.IsInstanceProxy():
                prim.SetInstanceable(False)
                changed = True


def disable_colliders(stage, root_path):
    from pxr import Usd, UsdPhysics
    deinstance(stage, root_path)
    n = 0
    for prim in Usd.PrimRange(stage.GetPrimAtPath(root_path)):
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            UsdPhysics.CollisionAPI(prim).CreateCollisionEnabledAttr().Set(False)
            n += 1
    return n


def materials(stage):
    """Rubber finger pads (friction combine = max, so the pad value governs
    every pad contact) and a realistic household default."""
    from pxr import PhysxSchema, UsdPhysics, UsdShade
    out = {}
    for path, mu_s, mu_d, combine in ((GRIP_MATERIAL, 2.0, 1.8, "max"),
                                      (OBJECT_MATERIAL, 0.6, 0.5, "average")):
        prim = stage.DefinePrim(path, "Material")
        m = UsdPhysics.MaterialAPI.Apply(prim)
        m.CreateStaticFrictionAttr().Set(mu_s)
        m.CreateDynamicFrictionAttr().Set(mu_d)
        m.CreateRestitutionAttr().Set(0.0)
        px = PhysxSchema.PhysxMaterialAPI.Apply(prim)
        px.CreateFrictionCombineModeAttr().Set(combine)
        px.CreateRestitutionCombineModeAttr().Set("min")
        out[path] = UsdShade.Material(prim)
    return out


def bind(prim, material):
    from pxr import UsdShade
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(material, UsdShade.Tokens.weakerThanDescendants, "physics")


# ---------------------------------------------------------------- robot
PAD_LINKS = ("right_gripper_left_finger_link", "right_gripper_right_finger_link",
             "left_gripper_left_finger_link", "left_gripper_right_finger_link")
PAD_TORSION_RADIUS = 0.01      # m: torsional friction patch of a rubber pad (2.8 x 5.5 cm)


def pad_torsion(stage, radius=PAD_TORSION_RADIUS):
    """Torsional friction on the finger pads.  Without it PhysX resists no rotation about
    the contact normal, so a two-pad pinch holds an object like an axle: a bottle pinched
    across its diameter swung 22-25 degrees about the pinch axis while carried.  Runtime,
    idempotent (scenes baked before it lack it)."""
    from pxr import PhysxSchema
    for link in PAD_LINKS:
        prim = stage.GetPrimAtPath(f"{ASSET}/{link}/pad_collider")
        if prim:
            api = PhysxSchema.PhysxCollisionAPI.Apply(prim)
            api.CreateTorsionalPatchRadiusAttr().Set(radius)
            api.CreateMinTorsionalPatchRadiusAttr().Set(radius)


def patch_left_gripper(stage, finger_kp=1.0e4, finger_kd=300.0):
    """Runtime fix for scenes baked before it: the left gripper's left finger
    kept its fused wedge collider (jammed open) and both left finger joints
    had torso-lift gains.  Pad box collider + finger gains, idempotent."""
    from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdPhysics
    path = f"{ASSET}/left_gripper_left_finger_link"
    if stage.GetPrimAtPath(path) and not stage.GetPrimAtPath(f"{path}/pad_collider"):
        disable_colliders(stage, path)
        pad = UsdGeom.Cube.Define(stage, f"{path}/pad_collider")
        pad.CreateSizeAttr(1.0)
        pad.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.006, 0.0175))
        pad.AddScaleOp().Set(Gf.Vec3d(0.028, 0.012, 0.055))
        pad.CreatePurposeAttr().Set("guide")
        UsdPhysics.CollisionAPI.Apply(pad.GetPrim())
        PhysxSchema.PhysxCollisionAPI.Apply(pad.GetPrim()).CreateContactOffsetAttr().Set(0.002)
        mats = materials(stage)
        bind(pad.GetPrim(), mats[GRIP_MATERIAL])
    for prim in Usd.PrimRange(stage.GetPrimAtPath(ASSET)) if stage.GetPrimAtPath(ASSET) else []:
        if prim.GetName() in ("left_gripper_left_finger_axis", "left_gripper_right_finger_axis"):
            drive = UsdPhysics.DriveAPI.Get(prim, "linear")
            if drive:
                drive.GetStiffnessAttr().Set(finger_kp)
                drive.GetDampingAttr().Set(finger_kd)


BASE_LINKS = ("base_root_link", "base_x_link", "base_y_link")
BASE_JOINTS = ("base_x_joint", "base_y_joint", "base_yaw_joint")


def base_joints(stage, lin_kp=1.0e6, lin_kd=2.0e4, yaw_kp=2.0e4, yaw_kd=200.0):
    """Runtime fix for scenes baked before it: the base hung on base_anchor, a fixed joint from
    the world outside the articulation (a floating-base articulation whose root was base_link),
    and moving that joint's frame dragged the robot by a constraint force.  Driving forward at
    0.35 m/s the drag bent the waist to its 0.70 rad limit (40 deg, the hand down on the
    counters), backward to -0.09; turning in place and sideways it did not.  Now the base is part
    of a fixed-base articulation, as Isaac Lab's Ridgeback-Franka: world -fixed-> base_root_link
    -x-> base_x_link -y-> base_y_link -yaw-> base_link, the joints along the world axes so their
    values are the base pose (x m, y m, yaw).  Position drives (gains per m and per degree)
    move it; base_anchor stays as the scene's record of the start and is disabled.  Must run
    after anything that moves the robot's start (benchmark.scene.spawn_at_start).  Idempotent."""
    from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics
    base = stage.GetPrimAtPath(f"{ASSET}/base_link")
    if not base or stage.GetPrimAtPath(f"{ASSET}/{BASE_LINKS[0]}"):
        return
    cache = UsdGeom.XformCache()
    start = cache.GetLocalToWorldTransform(base)
    p = start.ExtractTranslation()
    yaw = math.degrees(math.atan2(start[0][1], start[0][0]))
    to_asset = cache.GetLocalToWorldTransform(stage.GetPrimAtPath(ASSET)).GetInverse()
    base.RemoveAPI(UsdPhysics.ArticulationRootAPI)
    base.RemoveAPI(PhysxSchema.PhysxArticulationAPI)
    links = []
    for name, (x, y) in zip(BASE_LINKS, ((0.0, 0.0), (p[0], 0.0), (p[0], p[1]))):
        link = UsdGeom.Xform.Define(stage, f"{ASSET}/{name}")
        world = Gf.Matrix4d().SetTranslate(Gf.Vec3d(x, y, p[2]))
        link.AddTransformOp().Set(world * to_asset)
        UsdPhysics.RigidBodyAPI.Apply(link.GetPrim())
        PhysxSchema.PhysxRigidBodyAPI.Apply(link.GetPrim()).CreateDisableGravityAttr().Set(True)
        mass = UsdPhysics.MassAPI.Apply(link.GetPrim())
        mass.CreateMassAttr().Set(1.0)
        mass.CreateDiagonalInertiaAttr().Set(Gf.Vec3f(0.01, 0.01, 0.01))
        links.append(link.GetPath())
    root = UsdPhysics.FixedJoint.Define(stage, f"{ASSET}/joints/base_root_joint")
    root.CreateBody1Rel().SetTargets([links[0]])
    root.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0, 0.0, float(p[2])))
    root.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
    UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())
    PhysxSchema.PhysxArticulationAPI.Apply(root.GetPrim()).CreateEnabledSelfCollisionsAttr().Set(False)
    chain = ((BASE_JOINTS[0], UsdPhysics.PrismaticJoint, "X", links[0], links[1], p[0]),
             (BASE_JOINTS[1], UsdPhysics.PrismaticJoint, "Y", links[1], links[2], p[1]),
             (BASE_JOINTS[2], UsdPhysics.RevoluteJoint, "Z", links[2], base.GetPath(), yaw))
    for name, kind, axis, b0, b1, value in chain:
        j = kind.Define(stage, f"{ASSET}/joints/{name}")
        j.CreateAxisAttr().Set(axis)
        j.CreateBody0Rel().SetTargets([b0])
        j.CreateBody1Rel().SetTargets([b1])
        j.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        j.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        j.CreateLocalRot0Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        j.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        lin = kind is UsdPhysics.PrismaticJoint
        drive = UsdPhysics.DriveAPI.Apply(j.GetPrim(), "linear" if lin else "angular")
        drive.CreateTypeAttr().Set("force")
        drive.CreateStiffnessAttr().Set(lin_kp if lin else yaw_kp)
        drive.CreateDampingAttr().Set(lin_kd if lin else yaw_kd)
        drive.CreateTargetPositionAttr().Set(float(value))
        state = PhysxSchema.JointStateAPI.Apply(j.GetPrim(), "linear" if lin else "angular")
        state.CreatePositionAttr().Set(float(value))
        state.CreateVelocityAttr().Set(0.0)
    anchor = stage.GetPrimAtPath(ANCHOR)
    if anchor:
        anchor.GetAttribute("physics:jointEnabled").Set(False)


def fix_robot(stage, x, y, yaw_deg, arm_kp=800.0, arm_kd=40.0, finger_kp=1.0e4, finger_kd=300.0):
    """Zeno Malo as imported from URDF had: zero damping on every drive, a free
    floating base on 2 N·m wheel drives (the base, not the door, moved when the
    arm pulled), finger colliders that stall 3.4 cm open, and a left arm that
    hangs into the floor when the torso lowers."""
    from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdPhysics
    mats = materials(stage)
    root = stage.GetPrimAtPath(ROBOT)
    root.GetAttribute("xformOp:translate").Set(Gf.Vec3d(x, y, 0.0))
    root.GetAttribute("xformOp:rotateZ").Set(float(yaw_deg))

    # Base anchor: fixed joint world -> base_link, the record of the start pose.
    # Moving its frame dragged the base and bent the waist: base_joints (at load)
    # disables it and moves the base on joints instead.
    base = stage.GetPrimAtPath(ASSET + "/base_link")
    xf = UsdGeom.XformCache().GetLocalToWorldTransform(base)
    t = xf.ExtractTranslation()
    yaw = math.radians(yaw_deg)
    fj = UsdPhysics.FixedJoint.Define(stage, ANCHOR)
    fj.CreateBody1Rel().SetTargets([base.GetPath()])
    fj.CreateLocalPos0Attr().Set(Gf.Vec3f(float(x), float(y), float(t[2])))
    fj.CreateLocalRot0Attr().Set(Gf.Quatf(math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)))
    fj.CreateLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
    fj.CreateLocalRot1Attr().Set(Gf.Quatf(1, 0, 0, 0))

    from .kinematics import FINGERS, LEFT_ARM_FOLD
    for prim in Usd.PrimRange(stage.GetPrimAtPath(ASSET)):
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            # gravity compensation, as on the real arm controller
            PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
        if not (prim.IsA(UsdPhysics.RevoluteJoint) or prim.IsA(UsdPhysics.PrismaticJoint)):
            continue
        name = prim.GetName()
        lin = prim.IsA(UsdPhysics.PrismaticJoint)
        drive = UsdPhysics.DriveAPI.Get(prim, "linear" if lin else "angular")
        if not drive or "wheel" in name or "steering" in name:
            continue
        if name in FINGERS or name in ("left_gripper_left_finger_axis", "left_gripper_right_finger_axis"):
            drive.GetStiffnessAttr().Set(finger_kp)
            drive.GetDampingAttr().Set(finger_kd)
            drive.CreateTargetPositionAttr().Set(0.04)
        elif lin:
            drive.GetStiffnessAttr().Set(2.0e5)          # torso lift, N/m
            drive.GetDampingAttr().Set(2.0e4)
        else:
            drive.GetStiffnessAttr().Set(arm_kp)         # USD angular gains are per degree
            drive.GetDampingAttr().Set(arm_kd)
        if name in LEFT_ARM_FOLD:
            drive.CreateTargetPositionAttr().Set(math.degrees(LEFT_ARM_FOLD[name]))

    # The base is positioned kinematically; its floor-contact colliders only
    # snag on floor seams/rug edges.  Base footprints are planned instead.
    for link in ["base_link"] + [f"{c}_{k}_link" for c in ("fl", "fr", "rl", "rr")
                                 for k in ("steering", "wheel")]:
        if stage.GetPrimAtPath(f"{ASSET}/{link}"):
            disable_colliders(stage, f"{ASSET}/{link}")

    # Finger pads: the convex decomposition fused pad + slide rail into a
    # wedge reaching ~2 cm into the grasp gap.  Pad-sized boxes instead
    # (finger frame: x +-0.014, |y| 0..0.012, z -0.01..0.045).
    # (all four fingers: the left gripper's left finger had been missed and its
    # fused wedge collider jammed it open, so left grasps closed one finger only)
    for link, sign in (("right_gripper_left_finger_link", 1.0), ("right_gripper_right_finger_link", -1.0),
                       ("left_gripper_left_finger_link", 1.0), ("left_gripper_right_finger_link", -1.0)):
        path = f"{ASSET}/{link}"
        if not stage.GetPrimAtPath(path):
            continue
        disable_colliders(stage, path)
        pad = UsdGeom.Cube.Define(stage, f"{path}/pad_collider")
        pad.CreateSizeAttr(1.0)
        if not pad.GetOrderedXformOps():
            pad.AddTranslateOp().Set(Gf.Vec3d(0.0, sign * 0.006, 0.0175))
            pad.AddScaleOp().Set(Gf.Vec3d(0.028, 0.012, 0.055))
        pad.CreatePurposeAttr().Set("guide")
        UsdPhysics.CollisionAPI.Apply(pad.GetPrim())
        PhysxSchema.PhysxCollisionAPI.Apply(pad.GetPrim()).CreateContactOffsetAttr().Set(0.002)
        bind(pad.GetPrim(), mats[GRIP_MATERIAL])


# ---------------------------------------------------------------- furniture
def fix_articulation(stage, joint_path, damping=0.05, friction=0.0):
    """Hinges/slides had no damping: a released door kept swinging.  Small
    viscous damping (per degree for revolute).  PhysX articulation joint
    friction scales with the joint *constraint* force (door weight etc.), so
    even 0.02 made a 3 kg door un-openable by the gripper: keep it 0."""
    from pxr import PhysxSchema, UsdPhysics
    j = stage.GetPrimAtPath(joint_path)
    lin = j.IsA(UsdPhysics.PrismaticJoint)
    d = UsdPhysics.DriveAPI.Apply(j, "linear" if lin else "angular")
    d.CreateStiffnessAttr().Set(0.0)
    d.CreateDampingAttr().Set(damping * (100.0 if lin else 1.0))
    d.CreateMaxForceAttr().Set(1.0e3)
    # no joint friction on slides either: 0.02 (scaled by the drawer's
    # constraint force) held drawers shut against the gripper's pull.  The
    # viscous damping above keeps them from drifting open when bumped.
    PhysxSchema.PhysxJointAPI.Apply(j).CreateJointFrictionAttr().Set(friction)


# ---------------------------------------------------------------- objects
def body_prim(stage, root_path):
    from pxr import Usd, UsdPhysics
    for prim in Usd.PrimRange(stage.GetPrimAtPath(root_path)):
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            return prim
    raise RuntimeError(f"no rigid body under {root_path}")


def strip_nested_bodies(stage, root_path):
    """The URDF->USD converter also puts RigidBodyAPI on the 'collisions'
    child of the link: a rigid body nested in a rigid body, which PhysX
    rejects (invalidated simulation views, very slow stepping).  Keep only the
    top-most body."""
    from pxr import Usd, UsdPhysics
    deinstance(stage, root_path)
    top = body_prim(stage, root_path)
    n = 0
    for prim in Usd.PrimRange(top):
        if prim != top and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            prim.RemoveAPI(UsdPhysics.RigidBodyAPI)
            if prim.HasAPI(UsdPhysics.MassAPI):
                prim.RemoveAPI(UsdPhysics.MassAPI)
            n += 1
    return n


def set_box_inertia(stage, root_path, mass):
    """Imported assets carried a placeholder inertia of (1,1,1) kg·m² —
    thousands of times too large, objects barely rotate.  Solid-box estimate."""
    from pxr import Gf, UsdGeom, UsdPhysics
    strip_nested_bodies(stage, root_path)
    body = body_prim(stage, root_path)
    rng = UsdGeom.Imageable(stage.GetPrimAtPath(root_path)).ComputeWorldBound(0, "default").ComputeAlignedRange()
    sx, sy, sz = (rng.GetMax() - rng.GetMin())
    m = UsdPhysics.MassAPI.Apply(body)
    m.CreateMassAttr().Set(float(mass))
    m.CreateDiagonalInertiaAttr().Set(Gf.Vec3f(mass * (sy * sy + sz * sz) / 12,
                                               mass * (sx * sx + sz * sz) / 12,
                                               mass * (sx * sx + sy * sy) / 12))


def container_collider(stage, root_path, profile, n_seg=24, wall=0.007, shape="round", mats=None, handle=None, extra_handles=()):
    """Thin-walled containers (bowl, cup, basket, box, tray) were imported with
    a single convex hull or a cavity-filling decomposition: a *solid* object
    that cannot hold anything or be rim-pinched.  Rebuild the collider as wall
    segments following the mesh profile plus a base plate.

    profile: list of (z_lo, z_hi, r) bands above the object's bottom (round),
             or for shape="rect": (z_lo, z_hi, half_x, half_y).
    """
    from pxr import Gf, UsdGeom, UsdPhysics
    deinstance(stage, root_path)
    root = stage.GetPrimAtPath(root_path)
    body = body_prim(stage, root_path)
    disable_colliders(stage, root_path)
    Mb = UsdGeom.XformCache().GetLocalToWorldTransform(body)
    Minv = Mb.GetInverse()
    rng = UsdGeom.Imageable(root).ComputeWorldBound(0, "default").ComputeAlignedRange()
    cx, cy = (rng.GetMin()[0] + rng.GetMax()[0]) / 2, (rng.GetMin()[1] + rng.GetMax()[1]) / 2
    z0 = rng.GetMin()[2]
    mats = mats or materials(stage)
    k = 0

    def add_box(center, size, yaw):
        nonlocal k
        cube = UsdGeom.Cube.Define(stage, f"{body.GetPath()}/wall_{k:02d}")
        k += 1
        cube.CreateSizeAttr(1.0)
        cube.CreatePurposeAttr().Set("guide")
        world = Gf.Matrix4d().SetScale(Gf.Vec3d(*size)) * \
            Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(0, 0, 1), math.degrees(yaw))) * \
            Gf.Matrix4d().SetTranslate(Gf.Vec3d(*center))
        cube.ClearXformOpOrder()
        cube.AddTransformOp().Set(world * Minv)
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim()).CreateCollisionEnabledAttr().Set(True)
        bind(cube.GetPrim(), mats[OBJECT_MATERIAL])

    base_r = None
    for band in profile:
        if shape == "round":
            za, zb, r = band
            seg_w = 2 * math.pi * r / n_seg * 1.15
            for i in range(n_seg):
                a = 2 * math.pi * i / n_seg
                add_box((cx + r * math.cos(a), cy + r * math.sin(a), z0 + (za + zb) / 2),
                        (wall, seg_w, zb - za), a)
            base_r = r if base_r is None else min(base_r, r)
        else:
            za, zb, hx, hy = band
            zc = z0 + (za + zb) / 2
            add_box((cx + hx, cy, zc), (wall, 2 * hy, zb - za), 0.0)
            add_box((cx - hx, cy, zc), (wall, 2 * hy, zb - za), 0.0)
            add_box((cx, cy + hy, zc), (2 * hx, wall, zb - za), 0.0)
            add_box((cx, cy - hy, zc), (2 * hx, wall, zb - za), 0.0)
            base_r = (hx, hy)
    # base plate
    if shape == "round":
        add_box((cx, cy, z0 + 0.006), (1.5 * base_r, 1.5 * base_r, 0.012), 0.0)
        add_box((cx, cy, z0 + 0.006), (1.5 * base_r, 1.5 * base_r, 0.012), math.pi / 4)
        # The two squares only cover ~0.75 r; tiles out to the wall close the
        # ring where small items (cherry tomatoes) used to fall through.
        tile_w = 2 * math.pi * base_r / n_seg * 1.15
        for i in range(n_seg):
            a = 2 * math.pi * i / n_seg
            rm = 0.82 * base_r
            add_box((cx + rm * math.cos(a), cy + rm * math.sin(a), z0 + 0.006),
                    (0.36 * base_r + wall / 2, tile_w, 0.012), a)
    else:
        add_box((cx, cy, z0 + 0.006), (2 * base_r[0], 2 * base_r[1], 0.012), 0.0)
    if handle is not None:
        add_handle_collider(stage, str(body.GetPath()), handle, mats)
        k += 1
    for i, other in enumerate(extra_handles, start=1):
        add_handle_collider(stage, str(body.GetPath()), other, mats, name=f"handle_collider_{i}")
        k += 1
    return k


def add_handle_collider(stage, body_path, handle, mats=None, name="handle_collider"):
    """Idempotently attach a named grasp handle collider to an existing rigid body."""
    from pxr import Gf, UsdGeom, UsdPhysics
    mats = mats or materials(stage)
    body = stage.GetPrimAtPath(body_path)
    if not body:
        raise ValueError(f"missing rigid body {body_path}")
    cube = UsdGeom.Cube.Define(stage, f"{body_path}/{name}")
    cube.CreateSizeAttr(1.0)
    cube.CreatePurposeAttr().Set("guide")
    cube.ClearXformOpOrder()
    cube.AddTransformOp().Set(
        Gf.Matrix4d().SetScale(Gf.Vec3d(*handle["size"])) *
        Gf.Matrix4d().SetTranslate(Gf.Vec3d(*handle["center"])))
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim()).CreateCollisionEnabledAttr().Set(True)
    bind(cube.GetPrim(), mats[OBJECT_MATERIAL])
    return cube.GetPrim()


def solid_collider(stage, root_path, approximation="convexHull", mats=None):
    """Solid objects (fruit, books, toys, boxes).

    The importer put CollisionAPI on *Xforms* ('collisions' with a convex
    decomposition, '.../World' with a convex hull) and none on the Mesh; which
    one PhysX cooks is fragile, and thin objects fell through supports.  Put a
    convex hull on the collision Mesh itself (flat, stable base; generated
    meshes have uneven bottoms that made tall boxes rock forever) and strip
    the Xform-level APIs.
    """
    from pxr import PhysxSchema, Usd, UsdGeom, UsdPhysics
    deinstance(stage, root_path)
    mats = mats or materials(stage)
    for prim in list(Usd.PrimRange(stage.GetPrimAtPath(root_path))):
        in_col = "/collisions" in str(prim.GetPath())
        if prim.IsA(UsdGeom.Mesh) and in_col:
            UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr().Set(True)
            UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr().Set(approximation)
            PhysxSchema.PhysxCollisionAPI.Apply(prim).CreateContactOffsetAttr().Set(0.004)
            PhysxSchema.PhysxCollisionAPI.Apply(prim).CreateRestOffsetAttr().Set(0.0)
            bind(prim, mats[OBJECT_MATERIAL])
        elif prim.HasAPI(UsdPhysics.CollisionAPI) and not prim.IsA(UsdGeom.Gprim):
            prim.RemoveAPI(UsdPhysics.MeshCollisionAPI)
            prim.RemoveAPI(PhysxSchema.PhysxConvexDecompositionCollisionAPI)
            prim.RemoveAPI(UsdPhysics.CollisionAPI)


def scene_settings(stage):
    """TGS with enough iterations for thin contacts; CPU-safe settings."""
    from pxr import PhysxSchema
    ps = stage.GetPrimAtPath("/World/PhysicsScene")
    api = PhysxSchema.PhysxSceneAPI.Apply(ps)
    api.CreateSolverTypeAttr().Set("TGS")
    api.CreateEnableCCDAttr().Set(True)
    api.CreateMinPositionIterationCountAttr().Set(16)
    api.CreateTimeStepsPerSecondAttr().Set(PHYSICS_HZ)
