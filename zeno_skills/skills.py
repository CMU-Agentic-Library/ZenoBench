"""Annotation-driven Zeno Malo skills.  Nothing here is asset-specific: every
number comes from annotations/<scene>.json + annotations/assets.json.

    navigate(rig, (x, y, yaw))
    open_articulated(rig, name) / close_articulated(rig, name)
    pick(rig, object_name)
    place(rig, object_name, support_name, xy)

Each skill measures its own success from simulator state (joint angle, object
pose, finger gap) and raises SkillFailure otherwise.
"""

from __future__ import annotations

import math

import numpy as np

from .planner import find_park, plan_path, torque_ratio
from .rig import SkillFailure

TCP_BACKOFF = 0.12


# ---------------------------------------------------------------- navigation
def navigate(rig, pose, label="navigate"):
    """Tuck (or lift the carried object), plan an A* path, drive."""
    if rig.held is None:
        if not rig.tuck():
            raise SkillFailure(f"{label}: cannot fold the arm without hitting something")
    else:
        rig.sync_world()
        tcp, R = rig.kin.tcp(rig.q_cmd)
        for dz in (0.06, 0.03):                  # a little clearance if the arm allows
            try:
                rig.move_to(tcp + np.array([0, 0, dz]), R, step=0.005, steps_per_wp=5, label="carry_up",
                            collision=False)
                break
            except SkillFailure:
                continue
    rig.sync_world()
    path = plan_path(rig.world, rig.base_pose(), pose)
    if path is None:
        raise SkillFailure(f"{label}: no base path to {pose}")
    rig.log("path", waypoints=[[round(v, 2) for v in w] for w in path])
    rig.drive_base(path)


# ---------------------------------------------------------------- articulated
def _handle_targets(rig, a, q):
    p, R, appr = rig.ann.handle_pose(a, q, "side")
    return p, R, appr, [(p - TCP_BACKOFF * appr + np.array([0, 0, 0.08]), R),
                        (p - TCP_BACKOFF * appr, R), (p, R)]


def _ride_check(rig, a, q_from, q_to):
    """Base follows the part rigidly: footprint + arm must stay clear."""
    ann, kin, world = rig.ann, rig.kin, rig.world
    M0inv = np.linalg.inv(ann.motion(a, q_from))

    def check(x, y, yaw_deg, q_arm):
        ok = True
        saved = world.joint_q[a["name"]]
        for q in np.linspace(q_from, q_to, 8)[1:]:
            M = ann.motion(a, q) @ M0inv
            p = M[:3, :3] @ np.array([x, y, 0.0]) + M[:3, 3]
            dyaw = math.atan2(M[1, 0], M[0, 0])
            world.set_joint(a["name"], q)
            if not world.footprint_clear(p[0], p[1], math.radians(yaw_deg) + dyaw):
                ok = False
                break
            kin.set_base((p[0], p[1], 0.0), math.radians(yaw_deg) + dyaw)
            if not kin.free(q_arm):
                ok = False
                break
        world.set_joint(a["name"], saved)
        kin.set_base((x, y, 0.0), math.radians(yaw_deg))
        return ok
    return check


def _ride(rig, a, goal, lead=0.03, rate=0.25):
    """Closed loop: read the real joint value, put the base at the pose that
    keeps the robot rigid w.r.t. the part at (value + lead).  The grasped
    handle is the only thing that moves the part."""
    ann = rig.ann
    x0, y0, yaw0 = rig.base_pose()
    q_start = rig.joint(a["name"])
    Minv0 = np.linalg.inv(ann.motion(a, q_start))
    sign = 1.0 if goal > q_start else -1.0
    cmd, last, stall = q_start, q_start, 0
    for it in range(6000):
        q = rig.joint(a["name"])
        if sign * (goal - q) <= 0.02 * (1 if a["type"] == "revolute" else 0.3):
            rig.log("ride_done", q=q)
            return True
        target = q + sign * lead if sign * (goal - (q + sign * lead)) > 0 else goal + sign * 0.02
        cmd += float(np.clip(target - cmd, -rate / 120, rate / 120))
        M = ann.motion(a, cmd) @ Minv0
        p = M[:3, :3] @ np.array([x0, y0, 0.0]) + M[:3, 3]
        rig.set_base(p[0], p[1], yaw0 + math.degrees(math.atan2(M[1, 0], M[0, 0])))
        rig.step(1)
        if it % 60 == 0:
            rig.log("ride", q=round(q, 4), cmd=round(cmd, 4), fingers=[round(v, 4) for v in rig.fingers()])
            if abs(q - last) < 0.003 and it:
                stall += 1
                if stall >= 4:
                    return False
            else:
                stall = 0
            last = q
    return False


def _move_articulated(rig, name, goal, verb):
    a = rig.ann.art(name)
    q0 = rig.joint(name)
    rig.sync_world()
    rig.kin.coll_kw = {"hand_touches_part": True}
    p, R, appr, targets = _handle_targets(rig, a, q0)
    # among feasible parks prefer the one whose arm can pull hardest along the
    # handle's motion (the 3 N·m wrist joints were the weak link)
    pull = np.asarray(a["handle"]["outward"], float) * (1 if goal != a["closed_q"] else -1) * 20.0

    def score(x, y, yaw, qs):
        rig.kin.set_base((x, y, 0.0), math.radians(yaw))
        return torque_ratio(rig.kin, qs[-1], pull)
    park = find_park(rig.kin, rig.world, targets, near=rig.base_pose(), q_start=rig.q_cmd,
                     ride=_ride_check(rig, a, q0, goal), score=score, n_best=10)
    if park is None:
        raise SkillFailure(f"{verb} {name}: no base pose can grasp the handle and ride the motion")
    x, y, yaw, park_qs = park
    rig.log(f"{verb}_park", park=[round(x, 3), round(y, 3), round(yaw, 1)])
    rig.caption = f"{verb.upper()} {a['category']}: go to handle"
    bx, by, byaw = rig.base_pose()
    if math.hypot(x - bx, y - by) > 0.02 or abs((yaw - byaw + 180) % 360 - 180) > 2:
        navigate(rig, (x, y, yaw))
    rig.kin.coll_kw = {"hand_touches_part": True}
    q_now = rig.joint(name)
    rig.log(f"{verb}_at_park", q_before=q0, q_now=q_now)
    if abs(q_now - q0) > 0.01:          # the part moved meanwhile: re-target
        q0 = q_now
        p, R, appr, targets = _handle_targets(rig, a, q0)
        park_qs = [None, None, None]
    rig.caption = f"{verb.upper()} {a['category']}: grasp handle (side hook)"
    rig.grip(0.04, 30)
    for (tp, tR), lab, st, qh in zip(targets, ("pre_high", "pre", "handle"), (0.02, 0.01, 0.004), park_qs):
        rig.move_to(tp, tR, step=st, steps_per_wp=4 if lab == "handle" else 3, label=f"{verb}_{lab}", q_hint=qh)
    f = rig.grip(0.0, 120)
    if not (f.min() > 0.004 and 0.018 < f.sum() < 0.055):
        raise SkillFailure(f"{verb} {name}: handle not grasped, fingers {f.round(4).tolist()}")
    rig.caption = f"{verb.upper()} {a['category']}: base follows the joint motion"
    done = _ride(rig, a, goal)
    rig.step(30)
    rig.caption = f"{verb.upper()} {a['category']}: release"
    rig.grip(0.04, 70)
    q = rig.joint(name)
    p, R, appr = rig.ann.handle_pose(a, q, "side")
    rig.move_to(p - 0.14 * appr, R, step=0.006, steps_per_wp=4, label=f"{verb}_back", collision=False)
    rig.move_to(p - 0.14 * appr + np.array([0, 0, 0.12]), R, step=0.01, label=f"{verb}_up", collision=False)
    rig.step(60)
    q = rig.joint(name)
    rig.log(f"{verb}_result", name=name, before=q0, after=q, goal=goal)
    ok = abs(q - goal) < (0.10 if a["type"] == "revolute" else 0.02)
    if not (done and ok):
        raise SkillFailure(f"{verb} {name}: joint {q0:.3f} -> {q:.3f}, goal {goal:.3f}")
    return q


def open_articulated(rig, name, goal=None):
    a = rig.ann.art(name)
    return _move_articulated(rig, name, a["open_q"] if goal is None else goal, "open")


def close_articulated(rig, name):
    a = rig.ann.art(name)
    return _move_articulated(rig, name, a["closed_q"], "close")


# ---------------------------------------------------------------- pick / place
def _grasp_legs(g):
    appr = -g["R"][:, 2]
    p = g["p"]
    return [(p - 0.08 * appr + np.array([0, 0, 0.04]), g["R"]), (p - 0.04 * appr, g["R"]), (p, g["R"])]


def pick(rig, name, max_candidates=12):
    obj = rig.ann.objects[name]
    pos, quat = rig.obj_pose(name)
    cands = rig.ann.grasp_poses(obj, pos, quat)
    if not cands:
        raise SkillFailure(f"pick {name}: asset '{obj['asset']}' has no Zeno-feasible grasp annotation")
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    # prefer grasps facing the robot's current position
    bx, by, _ = rig.base_pose()
    cands.sort(key=lambda g: np.linalg.norm(g["p"][:2] - np.array([bx, by])))
    park, g = None, None
    for g in cands[:max_candidates]:
        lift = [(g["p"] + np.array([0, 0, 0.07]), g["R"])]
        park = find_park(rig.kin, rig.world, _grasp_legs(g) + lift, near=rig.base_pose(), max_tries=120,
                         q_start=rig.q_cmd)
        if park:
            break
    if park is None:
        raise SkillFailure(f"pick {name}: no reachable grasp from any base pose")
    x, y, yaw, park_qs = park
    rig.log("pick_park", obj=name, kind=g["kind"], park=[round(x, 3), round(y, 3), round(yaw, 1)])
    rig.caption = f"PICK {name}: approach"
    bx, by, byaw = rig.base_pose()
    if math.hypot(x - bx, y - by) > 0.02 or abs((yaw - byaw + 180) % 360 - 180) > 2:
        navigate(rig, (x, y, yaw))
    rig.kin.coll_kw = {"ignore_fingers": True}
    pos, quat = rig.obj_pose(name)          # re-read after driving
    g2 = [c for c in rig.ann.grasp_poses(obj, pos, quat) if c["kind"] == g["kind"]
          and np.linalg.norm(c["p"] - g["p"]) < 0.03 and np.allclose(c["R"], g["R"], atol=1e-3)]
    g = g2[0] if g2 else g
    rig.grip(g["pre_open"], 40)
    for (tp, tR), lab, st, spw, qh in zip(_grasp_legs(g), ("pre_far", "pre", "grasp"), (0.02, 0.005, 0.003),
                                          (3, 3, 4), park_qs):
        rig.move_to(tp, tR, step=st, steps_per_wp=spw, label=f"pick_{lab}", q_hint=qh)
    rig.caption = f"PICK {name}: close gripper"
    rig.grip(0.0, 120)
    rig.caption = f"PICK {name}: lift"
    rig.move_to(g["p"] + np.array([0, 0, 0.07]), g["R"], step=0.002, steps_per_wp=6, label="pick_lift",
                collision=False)
    rig.step(40)
    after, _ = rig.obj_pose(name)
    f = rig.fingers()
    held = bool(f.min() > 0.003) and after[2] - pos[2] > 0.015
    rig.log("pick_result", obj=name, lift_m=round(float(after[2] - pos[2]), 4), fingers=f.round(4).tolist(),
            held=held)
    if not held:
        raise SkillFailure(f"pick {name}: not held (lift {after[2] - pos[2]:.3f} m)")
    tcp, R = rig.kin.tcp(rig.q_cmd)
    rig.held = {"name": name, "tcp_minus_body": tcp - after, "R": R, "pre_open": g["pre_open"]}
    return True


def place(rig, name, support, xy):
    if rig.held is None or rig.held["name"] != name:
        raise SkillFailure(f"place {name}: not holding it")
    obj = rig.ann.objects[name]
    asset = rig.ann.asset_of(obj)
    if support.startswith("in:"):
        # into a container: its floor (base plate) is the support, centre xy
        cname = support[3:]
        cobj = rig.ann.objects[cname]
        ca = rig.ann.asset_of(cobj)
        cp, cq = rig.obj_pose(cname)
        yaw = math.atan2(2 * (cq[0] * cq[3] + cq[1] * cq[2]), 1 - 2 * (cq[2] ** 2 + cq[3] ** 2))
        from .annotations import rz
        cb = cp + rz(yaw) @ np.asarray(ca["origin_to_bottom_center"], float)
        s = {"name": support, "z": float(cb[2] + 0.013)}
        xy = (float(cb[0]), float(cb[1]))
    else:
        s = rig.ann.support(support)
    body_z = s["z"] - asset["origin_to_bottom_center"][2] + 0.006
    body = np.array([xy[0], xy[1], body_z])
    off0, R0 = rig.held["tcp_minus_body"], rig.held["R"]
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    # the object's yaw at the destination is free: rotate the held pose about
    # the vertical and keep the first yaw that is reachable
    from .annotations import rz
    park = None
    for psi in np.radians([0, 90, -90, 45, -45, 135, -135, 180]):
        Rz = rz(psi)
        off, R = Rz @ off0, Rz @ R0
        appr = -R[:, 2]
        legs = [(body + off + np.array([0, 0, 0.06]), R), (body + off + np.array([0, 0, 0.01]), R)]
        park = find_park(rig.kin, rig.world, legs, near=rig.base_pose(), max_tries=120, q_start=rig.q_cmd)
        if park:
            rig.log("place_yaw", deg=round(math.degrees(psi)))
            break
    if park is None:
        raise SkillFailure(f"place {name}: target {xy} on {support} unreachable")
    x, y, yaw, park_qs = park
    rig.log("place_park", obj=name, park=[round(x, 3), round(y, 3), round(yaw, 1)])
    rig.caption = f"PLACE {name}: carry"
    bx, by, byaw = rig.base_pose()
    if math.hypot(x - bx, y - by) > 0.02 or abs((yaw - byaw + 180) % 360 - 180) > 2:
        navigate(rig, (x, y, yaw))
    rig.kin.coll_kw = {"ignore_fingers": True}
    rig.move_to(legs[0][0], R, step=0.004, steps_per_wp=8, label="place_above", collision=False, q_hint=park_qs[0])
    rig.caption = f"PLACE {name}: lower"
    rig.move_to(legs[1][0], R, step=0.002, steps_per_wp=8, label="place_lower", collision=False, q_hint=park_qs[1])
    rig.step(30)
    rig.caption = f"PLACE {name}: release"
    rig.grip(rig.held["pre_open"], 70)
    rig.move_to(legs[1][0] + np.array([0, 0, 0.06]), R, step=0.004, label="place_retreat", collision=False)
    rig.held = None
    rig.step(90)
    p, _ = rig.obj_pose(name)
    err = float(np.linalg.norm(p[:2] - np.asarray(xy)))
    on = abs((p[2] + asset["origin_to_bottom_center"][2]) - s["z"]) < 0.03
    rig.log("place_result", obj=name, support=support, xy_err_m=round(err, 4), on_support=bool(on))
    if not (on and err < 0.06):
        raise SkillFailure(f"place {name}: xy err {err:.3f} m, on support {on}")
    return True
