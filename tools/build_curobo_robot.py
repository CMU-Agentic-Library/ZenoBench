"""Build the cuRobo robot config for Zeno Malo (robot_sources/curobo/zeno_malo.yml).

  docker/run.sh '$ISAACLAB_PYTHON tools/build_curobo_robot.py'      (ZENO_IMAGE=zenobench:isaaclab2.3-curobo07)

The collision spheres come from Isaac Sim's own sphere generator (lula, the one
behind the XRDF editor) fitted to the colliders PhysX uses for each link in a
task scene: every enabled collision mesh as its convex hull (the importer's
convexHull / convexDecomposition approximations) and the finger pad boxes.
base_link has no spheres: its collider is disabled in the scene too (base
navigation keeps the column clear of the furniture).

One model holds the torso lift, waist pitch, both arms and a virtual planar
base (base_x, base_y, base_yaw from world_link to base_link, written to
zeno_malo_mobile.urdf next to the original URDF), so the world stays in world
coordinates and a base move only changes three joint values.  Joint order:
ArmKin.names (right arm), the left arm's seven joints, then the base.  Head and
fingers are locked.  Tool frames right_tcp / left_tcp sit TCP_DEPTH below each
gripper link (kinematics.py).  Joints a query must not move are pinned by the
caller (zeno_skills/motion.py).
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "robot_sources/curobo"
ASSET = "/World/ZenoMalo/Asset"
LULA = "/opt/isaacsim-5.1-venv/lib/python3.11/site-packages/isaacsim/exts/isaacsim.robot_motion.lula/pip_prebundle"

SIDE_LINKS = [f"arm_link_{i}" for i in range(1, 8)] + [
    "gripper_link", "gripper_camera_link", "gripper_left_finger_link", "gripper_right_finger_link"]
LINKS = ["torso_lift_link", "torso_link", "head_yaw_link", "head_link", "stereo_camera_link"] + \
    [f"{s}_{l}" for s in ("right", "left") for l in SIDE_LINKS]
SPHERE_AREA = 0.004      # one sphere per this much hull surface (m^2), clipped to [MIN, MAX] per link
MIN_SPHERES, MAX_SPHERES = 6, 24
# head: coarser, to stay within cuRobo's fast
# self-collision kernel (see self_collision_ignore)
LINK_MAX_SPHERES = {"head_link": 12}
# the hands work close to objects and to each other (handovers): finer spheres, less inflation
HAND = ("arm_link_7", "gripper_link", "gripper_camera_link", "gripper_left_finger_link", "gripper_right_finger_link")
LINK_MIN_SPHERES = {f"{s}_{l}": 10 for s in ("right", "left") for l in HAND}
# lula's spheres sit inside the surface; every radius of a link grows by the 99th percentile of
# its surface samples' gap (at most MAX_GROW) so the spheres cover the collider
MAX_GROW = 0.02


def link_hulls(stage):
    """{link: trimesh} union of the convex hulls of the link's enabled colliders, in the link frame."""
    import numpy as np
    import trimesh
    from pxr import Usd, UsdGeom, UsdPhysics
    cache = UsdGeom.XformCache()
    it = Usd.TraverseInstanceProxies()

    def enabled(prim):
        p = prim
        while p and p.GetPath() != Usd.Stage.GetPseudoRoot(stage).GetPath():
            if p.HasAPI(UsdPhysics.CollisionAPI):
                return UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False
            p = p.GetParent()
        return False

    out = {}
    for link in LINKS:
        root = stage.GetPrimAtPath(f"{ASSET}/{link}")
        if not root:
            raise RuntimeError(f"no link prim {link}")
        inv = np.array(cache.GetLocalToWorldTransform(root).GetInverse(), float).T
        parts = []
        for p in Usd.PrimRange(root, it):
            if p.IsA(UsdGeom.Mesh):
                if not enabled(p):
                    continue
                pts = np.array(UsdGeom.Mesh(p).GetPointsAttr().Get(), float)
            elif p.IsA(UsdGeom.Cube) and p.HasAPI(UsdPhysics.CollisionAPI) and enabled(p):
                h = (UsdGeom.Cube(p).GetSizeAttr().Get() or 2.0) / 2
                pts = np.array([[x, y, z] for x in (-h, h) for y in (-h, h) for z in (-h, h)], float)
            else:
                continue
            M = np.array(cache.GetLocalToWorldTransform(p), float).T
            T = inv @ M
            local = pts @ T[:3, :3].T + T[:3, 3]
            parts.append(trimesh.convex.convex_hull(local))
        if parts:
            out[link] = trimesh.util.concatenate(parts)
    return out


def fit_spheres(hulls):
    import numpy as np
    sys.path.insert(0, LULA)
    import lula
    import trimesh
    spheres, report = {}, []
    for link, m in hulls.items():
        n = int(np.clip(round(m.area / SPHERE_AREA), LINK_MIN_SPHERES.get(link, MIN_SPHERES),
                        max(LINK_MAX_SPHERES.get(link, MAX_SPHERES), LINK_MIN_SPHERES.get(link, 0))))
        gen = lula.create_collision_sphere_generator(np.asarray(m.vertices, float), np.asarray(m.faces, np.int32))
        sph = gen.generate_spheres(n, 0.0)
        C = np.array([s.center for s in sph], float)
        R = np.array([s.radius for s in sph], float)
        S = m.sample(4000)
        gap = np.min(np.linalg.norm(S[:, None, :] - C[None], axis=2) - R[None], axis=1)
        R = R + float(np.clip(np.percentile(gap, 99), 0.0, MAX_GROW))
        spheres[link] = [{"center": [round(float(v), 4) for v in c], "radius": round(float(r), 4)}
                         for c, r in zip(C, R)]
        # coverage: hull surface samples outside every sphere (how far, worst case)
        gap = np.min(np.linalg.norm(S[:, None, :] - C[None], axis=2) - R[None], axis=1)
        # protrusion: how far the spheres reach past the collider (conservatism)
        far = np.max(R - trimesh.proximity.signed_distance(m, C)) if m.is_watertight else float("nan")
        report.append((link, len(sph), float(np.mean(gap > 0.005)), float(gap.max()), float(far)))
    return spheres, report


BASE_JOINTS = ("base_x", "base_y", "base_yaw")


def mobile_urdf():
    """The robot URDF under a planar x / y / yaw chain rooted at world_link."""
    from zeno_skills.kinematics import URDF
    tree = ET.parse(URDF)
    robot = tree.getroot()
    chain = [("world_link", "base_x_link", "base_x", "prismatic", "1 0 0", (-50, 50)),
             ("base_x_link", "base_y_link", "base_y", "prismatic", "0 1 0", (-50, 50)),
             ("base_y_link", "base_link", "base_yaw", "revolute", "0 0 1", (-3.3, 3.3))]
    for name in ("world_link", "base_x_link", "base_y_link"):
        robot.insert(0, ET.Element("link", name=name))
    for parent, child, name, typ, axis, (lo, hi) in chain:
        j = ET.SubElement(robot, "joint", name=name, type=typ)
        ET.SubElement(j, "parent", link=parent)
        ET.SubElement(j, "child", link=child)
        ET.SubElement(j, "origin", xyz="0 0 0", rpy="0 0 0")
        ET.SubElement(j, "axis", xyz=axis)
        ET.SubElement(j, "limit", lower=str(lo), upper=str(hi), effort="1000", velocity="1.0")
    path = URDF.parent / "zeno_malo_mobile.urdf"
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def joint_limits():
    joints = {j.get("name"): j for j in ET.parse(ROOT / "robot_sources/zeno_malo_description-master/"
                                                 "zeno_malo_edu.isaac.urdf").getroot().findall("joint")}
    return joints


def assemble(spheres):
    from zeno_skills.kinematics import FINGER_OPEN, LEFT_ARM_FOLD, TCP_DEPTH, URDF, ArmKin
    right, left = ArmKin(side="right"), ArmKin(side="left")
    names = list(right.names) + list(left.names[2:]) + list(BASE_JOINTS)
    urdf = mobile_urdf()
    joints = joint_limits()
    default = dict(zip(right.names, right.posture))
    default.update({n: LEFT_ARM_FOLD.get(n, 0.0) for n in left.names[2:]})
    default.update({n: 0.0 for n in BASE_JOINTS})
    links = [l for l in LINKS if l in spheres]
    # self-collision ignore pairs: sampled afterwards (self_collision_ignore), parent/child here
    parent = {j.find("child").get("link"): j.find("parent").get("link") for j in joints.values()}
    ignore = {l: set() for l in links}
    for l in links:
        p = parent.get(l)
        if p in ignore:
            ignore[l].add(p)
    tcp = {f"{s}_tcp": {"parent_link_name": f"{s}_gripper_link", "link_name": f"{s}_tcp",
                        "fixed_transform": [0.0, 0.0, -TCP_DEPTH, 1.0, 0.0, 0.0, 0.0],
                        "joint_type": "FIXED", "joint_name": f"{s}_tcp_joint"} for s in ("right", "left")}
    lock = {"head_yaw_joint": 0.0, "head_pitch_joint": 0.0}
    for s in ("right", "left"):
        lock[f"{s}_gripper_left_finger_axis"] = FINGER_OPEN      # the right finger mimics it
    return {"robot_cfg": {"kinematics": {
        "urdf_path": str(urdf.relative_to(ROOT)),
        "asset_root_path": str(URDF.parent.relative_to(ROOT)),
        "base_link": "world_link",
        "ee_link": "right_tcp",
        "link_names": ["right_tcp", "left_tcp"],
        "extra_links": tcp,
        "collision_link_names": links,
        "collision_spheres": {l: spheres[l] for l in links},
        "collision_sphere_buffer": 0.0,
        "self_collision_ignore": {l: sorted(v) for l, v in ignore.items() if v},
        "self_collision_buffer": {l: 0.0 for l in links},
        "mesh_link_names": links,
        "lock_joints": lock,
        "use_global_cumul": True,
        "cspace": {
            "joint_names": names,
            "retract_config": [float(default[n]) for n in names],
            "null_space_weight": [1.0] * len(names),
            "cspace_distance_weight": [1.0] * len(names),
            "max_acceleration": 15.0,
            "max_jerk": 500.0,
            "velocity_scale": [1.0] * len(names),
        },
    }}}


def _fingers_of(side):
    return [f"{side}_gripper_left_finger_link", f"{side}_gripper_right_finger_link"]


def self_collision_ignore(cfg, samples=40000, always=0.5):
    """MoveIt-style collision matrix on the fitted spheres: a link pair is ignored when the
    links are parent/child, touch in the default posture, touch in >= ``always`` of random
    postures, or never touch in any of them (every active joint uniform in its limits, base
    at the origin).  cuRobo's fast self-collision kernel takes at most 32 * 512 sphere pairs."""
    import copy
    import numpy as np
    import torch
    from curobo.cuda_robot_model.cuda_robot_model import CudaRobotModel
    from curobo.types.robot import RobotConfig
    c = copy.deepcopy(cfg["robot_cfg"])
    k = c["kinematics"]
    k["urdf_path"] = str(ROOT / k["urdf_path"])
    k["asset_root_path"] = str(ROOT / k["asset_root_path"])
    k["self_collision_ignore"] = {}
    model = CudaRobotModel(RobotConfig.from_dict(c).kinematics)
    names = model.joint_names
    lim = model.get_joint_limits().position.cpu().numpy()
    links = k["collision_link_names"]
    owner = np.concatenate([[i] * len(k["collision_spheres"][l]) for i, l in enumerate(links)])
    default = np.array(k["cspace"]["retract_config"], float)
    rng = np.random.default_rng(0)
    Q = rng.uniform(lim[0], lim[1], (samples, len(names)))
    for j, n in enumerate(names):
        if n in BASE_JOINTS:
            Q[:, j] = 0.0
    Q = np.vstack([default, Q])
    hits = np.zeros((len(Q), len(links), len(links)), bool)
    O = torch.as_tensor(owner, device="cuda")
    for b in range(0, len(Q), 200):
        q = torch.as_tensor(Q[b:b + 200], device="cuda", dtype=torch.float32)
        sph = model.get_state(q).link_spheres_tensor          # [B, n, 4]
        d = torch.cdist(sph[..., :3], sph[..., :3]) - sph[..., 3:4] - sph[..., 3].unsqueeze(1)
        touch = d < 0
        for i in range(len(links)):
            mi = O == i
            hits[b:b + 200, i] = torch.stack([(touch[:, mi][:, :, O == j]).flatten(1).any(1)
                                              for j in range(len(links))], 1).cpu().numpy()
    frac = hits[1:].mean(0)
    out = {l: set(cfg["robot_cfg"]["kinematics"]["self_collision_ignore"].get(l, [])) for l in links}
    for i, a in enumerate(links):
        for j, b in enumerate(links):
            if i < j and (hits[0, i, j] or frac[i, j] >= always or not hits[:, i, j].any()):
                out[a].add(b)
    # one hand's fingers against the other arm (handovers put both hands on one object): the old
    # inter-arm check left the fingers out too
    for s_, o_ in (("right", "left"), ("left", "right")):
        for f in _fingers_of(s_):
            for b in links:
                if b.startswith(o_ + "_") and f in out:
                    out[f].add(b)
    n = [len(k["collision_spheres"][l]) for l in links]
    pairs = sum(n[i] * n[j] for i in range(len(links)) for j in range(i + 1, len(links))
                if links[j] not in out[links[i]] and links[i] not in out[links[j]])
    print(f"  self-collision sphere pairs checked: {pairs} (fast kernel limit {32 * 512})", flush=True)
    for i, a in enumerate(links):
        for j, b in enumerate(links):
            if i < j and b not in out[a] and a not in out[b]:
                print(f"    check {a} - {b}  ({n[i] * n[j]} pairs, touch in {frac[i, j] * 100:.1f}%)", flush=True)
    for i, a in enumerate(links):
        for j, b in enumerate(links):
            if i < j and hits[0, i, j]:
                print(f"  ignore (touch in default posture) {a} - {b}", flush=True)
    return {l: sorted(v) for l, v in out.items() if v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="tasks/collect_fruits/scene.usd")
    args = ap.parse_args()
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    import omni.usd
    import yaml
    from zeno_skills import physics as P
    omni.usd.get_context().open_stage(str(ROOT / args.scene))
    for _ in range(5):
        app.update()
    stage = omni.usd.get_context().get_stage()
    P.patch_left_gripper(stage)
    hulls = link_hulls(stage)
    spheres, report = fit_spheres(hulls)
    for link, n, outside, worst, far in report:
        print(f"  {link:34s} {n:3d} spheres  surface >5 mm outside: {outside * 100:5.1f}%  worst {worst * 1000:5.1f} mm"
              f"  spheres reach {far * 1000:5.1f} mm past the hull", flush=True)
    cfg = assemble(spheres)
    cfg["robot_cfg"]["kinematics"]["self_collision_ignore"] = self_collision_ignore(cfg)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "zeno_malo.yml"
    with open(path, "w") as f:
        f.write(f"# generated by tools/build_curobo_robot.py from {args.scene} (lula spheres on PhysX colliders)\n")
        yaml.safe_dump(cfg, f, sort_keys=False)
    print(f"[curobo] {sum(len(v) for v in spheres.values())} spheres on {len(spheres)} links -> {path}", flush=True)
    app.close()


if __name__ == "__main__":
    main()
