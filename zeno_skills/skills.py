"""Annotation-driven Zeno Malo skills.  Nothing here is asset-specific: every
number comes from annotations/<scene>.json + annotations/assets.json.

    navigate(rig, (x, y, yaw))
    open_articulated(rig, name) / close_articulated(rig, name)   doors and drawers
    pick(rig, name)          pinch grasp (top / rim), or push-then-edge-pinch for
                             flat objects wider than the gripper; floor objects
                             with the torso lowered
    push(rig, name, n, d)    slide an object along the support (fingers closed)
    place(rig, name, "in:<container>")        drop into a container
    place_on(rig, name, support, hint_xy)     free spot on a support surface
                             (edge-held flat objects go back over a free edge)

Each skill measures its own success from simulator state (joint angle, object
pose, finger gap) and raises SkillFailure otherwise.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from .annotations import rz
from .evaluator import quat_R
from .kinematics import gripper_rot
from .planner import find_park, joint_reachable, plan_path, torque_ratio
from .rig import Dropped, SkillFailure

TCP_BACKOFF = 0.12
EDGE_GRIP_DEPTH = 0.045       # edge pinch: TCP up to this far inside the gripped edge
EDGE_PAD_CLEAR = 0.025        # ... but the lower pad stays this far outside the support edge
EDGE_PLACE_OVERHANG = 0.065   # edge place: gripped edge this far past the support edge
EDGE_MIN_OVERHANG = 0.055     # below this the lower finger hits the support edge
COM_MARGIN = 0.035            # centre of mass stays this far inside the edge while overhanging
PUSH_SEG = 0.25               # longest single push; the base re-parks between pushes
CARRY_Z = 0.55                # carried objects ride at least this high (floor picks)


# ---------------------------------------------------------------- navigation
def _carry_pose(rig, min_bottom_z=None):
    """Held object: lift to CARRY_Z (floor picks) and bring it next to the
    body so the arm does not stick out through doorways."""
    rig.sync_world()
    low_load = float(rig.geo.bottom(rig.held["name"], rig.state())[2]) < 0.30
    if low_load and (rig.q_cmd[0] < rig.kin.hi[0] - 0.05 or abs(rig.q_cmd[1]) > 0.05):
        # only after a floor pick (load near the floor): straightening a deep
        # waist bend swung a rim-held bowl taken out of the microwave
        # stand up with the load first (after a floor pick the torso is down
        # and the arm alone cannot lift the load to carry height)
        try:
            # slowly, torso first then waist: a fast 0.57 rad waist swing threw
            # a rim-held bowl out of the pinch
            for j, v in ((0, float(rig.kin.hi[0])), (1, 0.0)):
                q_goal = rig.q_cmd.copy()
                q_goal[j] = v
                if abs(rig.q_cmd[j] - v) > 0.01:
                    rig.follow(rig.joint_path(q_goal, "carry_stand_up"), steps_per_wp=12)
                    check_held(rig, "carry_stand_up")
        except Dropped:
            raise
        except SkillFailure as exc:
            rig.log("carry_stand_up_short", reason=str(exc))
    tcp, R = rig.kin.tcp(rig.q_cmd)
    rig.kin.coll_kw = {"ignore_fingers": True}
    hang = max(0.0, tcp[2] - float(rig.geo.bottom(rig.held["name"], rig.state())[2]))
    if min_bottom_z is not None and rig.held.get("kind") == "edge":
        min_bottom_z += 0.06       # an edge-held book droops: its free end needs more clearance
    target_bottom_z = max(CARRY_Z, min_bottom_z or 0.0)
    up = tcp + np.array([0, 0, max(0.06, target_bottom_z + hang - tcp[2])])
    for p, coll in ((up, True), (up, False), (tcp + np.array([0, 0, 0.03]), False)):
        try:
            rig.move_to(p, R, step=0.005, steps_per_wp=5, label="carry_up", collision=coll)
            break
        except SkillFailure:
            continue
    # bring the hand in front of the body, near its centre line (base frame
    # x 0.35, y -0.10): held out to the side, objects caught on door frames
    x, y, yaw = rig.base_pose()
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    tcp, R = rig.kin.tcp(rig.q_cmd)
    low_ok = min_bottom_z is None or 0.6 - hang >= min_bottom_z       # the 0.6 m fallback must respect the minimum
    options = ((0.35, -0.10, tcp[2]),) + (((0.35, -0.10, 0.6),) if low_ok else ()) + ((0.40, -0.25, tcp[2]),)
    # lower (but still above the requested bottom) and further out: a can
    # held high with no IK at the first options stayed out at the side for
    # the whole drive and the place then swung it out of the pinch
    z_min = tcp[2] if min_bottom_z is None else max(min_bottom_z + hang + 0.01, 0.0)
    options += tuple((lx, ly, z) for z in sorted({round(min(tcp[2], max(z_min, zz)), 3) for zz in (0.95, 0.85)},
                                                   reverse=True)
                     for lx, ly in ((0.35, -0.10), (0.45, -0.15), (0.45, -0.30)))
    rim = bool(rig.ann.asset_of(rig.ann.objects[rig.held["name"]]).get("container"))

    def bring_in():
        for lx, ly, z in options:
            w = np.array([x + c * lx - s * ly, y + s * lx + c * ly, z])
            try:
                # a rim-pinched bowl swings out of the pads on a fast sweep
                rig.move_to(w, R, step=0.005 if rim else 0.01, steps_per_wp=6 if rim else 4, label="carry_in",
                            smooth=rim)
                check_held(rig, "carry_in")
                return True
            except Dropped:
                raise
            except SkillFailure:
                continue
        return False
    if bring_in():
        return
    # far out at the side (a side pick): straight up first, then half-way in
    goal0 = np.array([x + c * 0.35 + s * 0.10, y + s * 0.35 - c * 0.10, tcp[2]])
    for via in (tcp + np.array([0, 0, 0.08]), 0.5 * (tcp + goal0), 0.5 * (tcp + goal0) + np.array([0, 0, 0.08])):
        try:
            rig.move_to(via, R, step=0.005, steps_per_wp=6, label="carry_in_via", smooth=True)
            check_held(rig, "carry_in_via")
        except Dropped:
            raise
        except SkillFailure:
            continue
        if bring_in():
            return
    rig.log("carry_in_failed", tcp=np.round(tcp, 3).tolist())


def check_held(rig, label):
    """Is the carried object still in the hand?  Its distance to the TCP must
    match the one measured at the grasp and the fingers must not have shut."""
    h = rig.held
    if h is None:
        return
    tcp, _ = rig.kin.tcp(rig.q())
    body, _ = rig.obj_pose(h["name"])
    slip = abs(float(np.linalg.norm(tcp - body)) - float(np.linalg.norm(h["tcp_minus_body"])))
    f = rig.fingers()
    gap = float(f.sum())          # an off-centre rim pinch drives one finger to ~0 while holding
    if 0.05 < slip < 0.08 and gap > 0.008:
        # shifted in the pinch but still between the pads: re-anchor
        rig.log("held_shift", obj=h["name"], during=label, slip_m=round(slip, 3), fingers=f.round(4).tolist())
        h["tcp_minus_body"] = tcp - body
        return
    if slip > 0.05 or gap < 0.004:
        rig.log("dropped", obj=h["name"], during=label, slip_m=round(slip, 3), fingers=f.round(4).tolist(),
                at=[round(float(v), 3) for v in body])
        rig.held = None
        rig.grip(0.04, 20)
        raise Dropped(f"{label}: {h['name']} slipped out of the hand while carrying it")


def _load_near_furniture(rig, margin=0.02):
    """Is the held object above a support surface (within ``margin``)?"""
    st = rig.state()
    name = rig.held["name"]
    c = rig.geo.centre(name, st)
    low = float(_lowest_z(rig, name, st))
    for s in rig.ann.supports:
        if str(s.get("category")) == "floor" or s["z"] < 0.05:
            continue
        x0, y0, x1, y1 = s["aabb_xy"]
        if x0 - margin <= c[0] <= x1 + margin and y0 - margin <= c[1] <= y1 + margin and low < s["z"] + 0.30:
            return True
    return False


def _back_off(rig, dist=0.35):
    """Holding something next to furniture: first reverse straight out, so
    turning in place does not sweep the object into the furniture (or a TV)."""
    rig.sync_world()
    x, y, yaw = rig.base_pose()
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for d in (dist, 0.2, 0.1):
        tx, ty = x - c * d, y - s * d
        if all(rig.world.footprint_clear(x - c * u, y - s * u, math.radians(yaw)) for u in np.linspace(0.05, d, 4)):
            rig.drive_base([(tx, ty, yaw)], speed=0.2)
            bx, by, _ = rig.base_pose()
            return max(0.0, (x - bx) * c + (y - by) * s)
    return 0.0


def _clear_for_tuck(rig):
    """Move the base (shift up to 0.35 m and/or turn up to 90 deg) to the
    nearest pose where the rest posture is collision-free and the base path
    and the current arm posture stay clear on the way."""
    rig.sync_world()
    x, y, yaw = rig.base_pose()
    kw = rig.kin.coll_kw
    rig.kin.coll_kw = {"ignore_fingers": True}
    cands = []
    for d in (0.0, 0.15, 0.25, 0.35):
        for ang in (range(0, 360, 45) if d else [0]):
            for dyaw in (0, 30, -30, 60, -60, 90, -90):
                if d == 0 and dyaw == 0:
                    continue
                tx = x + d * math.cos(math.radians(ang))
                ty = y + d * math.sin(math.radians(ang))
                cands.append((d + 0.004 * abs(dyaw), tx, ty, yaw + dyaw))
    cands.sort()
    try:
        for _, tx, ty, tyaw in cands:
            ok = True
            for u in np.linspace(0.25, 1.0, 4):
                px, py, pyaw = x + (tx - x) * u, y + (ty - y) * u, yaw + (tyaw - yaw) * u
                if not rig.world.footprint_clear(px, py, math.radians(pyaw)):
                    ok = False
                    break
                rig.kin.set_base((px, py, 0.0), math.radians(pyaw))
                if u < 1.0 and rig.world.clearance(rig.kin, rig.q_cmd, ignore_fingers=True) < -0.06:
                    ok = False             # do not sweep a deeply colliding arm further in
                    break
            if ok and rig.kin.free(rig.kin.rest):
                rig.kin.set_base((x, y, 0.0), math.radians(yaw))
                rig.drive_base([(tx, ty, tyaw)], speed=0.15, turn=0.4)
                rig.log("tuck_clearance_move", to=[round(tx, 3), round(ty, 3), round(tyaw, 1)])
                return True
        return False
    finally:
        rig.kin.coll_kw = kw
        bx, by, byaw = rig.base_pose()
        rig.kin.set_base((bx, by, 0.0), math.radians(byaw))


def held_vertical_move(rig, dz, label, R_goal=None, step=0.005, allow_pull=True):
    """Move the held object up (or down) by dz at the current base.  Straight
    up when the arm allows; otherwise from a staging point pulled toward the
    body (an arm stretched out after a far pick has no vertical range left)."""
    tcp, R = rig.kin.tcp(rig.q_cmd)
    R_goal = R if R_goal is None else R_goal
    x, y, _ = rig.base_pose()
    toward = np.array([x, y]) - tcp[:2]
    dist = float(np.linalg.norm(toward))
    unit = toward / dist if dist > 1e-6 else np.zeros(2)
    last = None
    for pull in ((0.0, 0.08, 0.15, 0.22, 0.30) if allow_pull else (0.0,)):
        pull = min(pull, max(0.0, dist - 0.30))
        goal = tcp + np.r_[unit * pull, dz]
        q_goal, ok = rig.kin.ik_global(goal, R_goal, seeds=[rig.q_cmd])
        # a held load must not ride a big arm reconfiguration (a 12 s swing
        # to another IK branch flung a mug 4 m across the kitchen)
        if not ok or float(np.max(np.abs(np.asarray(q_goal) - rig.q_cmd))) > 1.2:
            continue
        stage = tcp + np.r_[unit * pull, max(0.0, dz) * 0.3]
        if pull > 0:
            q_stage, ok = rig.kin.ik_global(stage, R, seeds=[rig.q_cmd])
            if not ok or float(np.max(np.abs(np.asarray(q_stage) - rig.q_cmd))) > 1.0:
                continue
        try:
            if pull > 0:
                rig.move_to(stage, R, step=step, steps_per_wp=5,
                            label=f"{label}_stage", collision=False, smooth=True, q_hint=q_stage)
                check_held(rig, f"{label}_stage")
            rig.move_to(goal, R_goal, step=step, steps_per_wp=5, label=label, collision=False, smooth=True)
            check_held(rig, label)
            return goal
        except SkillFailure as exc:
            last = exc
            if rig.held is None:
                raise
            tcp, R = rig.kin.tcp(rig.q_cmd)
    raise last or SkillFailure(f"{label}: no IK for a {dz:+.2f} m vertical move from any staging point")


def check_left_held(rig, label):
    """Verify a left-hand load after motion using finger gap and TCP distance."""
    h = rig.left_held
    if h is None:
        return
    tcp, _ = rig.left_kin.tcp(rig.left_q())
    body, _ = rig.obj_pose(h["name"])
    slip = abs(float(np.linalg.norm(tcp-body))-float(np.linalg.norm(h["tcp_minus_body"])))
    fingers = rig.left_fingers()
    if slip > 0.06 or float(fingers.sum()) < 0.004:
        rig.log("left_dropped", obj=h["name"], during=label, slip_m=round(slip, 3),
                fingers=fingers.round(4).tolist())
        rig.left_held = None
        raise Dropped(f"{label}: {h['name']} slipped from the left hand")


def navigate(rig, pose, label="navigate", min_bottom_z=None):
    """Tuck (or carry the held object), plan an A* path, drive (slower and
    with gentler turns while carrying)."""
    if rig.held is None:
        # just opened a door beside the base: reverse straight out first, so
        # the turn onto the route does not brush the open door back (a fridge
        # door was pushed from 60 to 45 deg open while turning away)
        x0, y0, _ = rig.base_pose()
        rig.sync_world()
        near_door = np.inf
        pts_ = np.array([[x0, y0, 0.6], [x0, y0, 1.0]])
        for a_ in rig.ann.articulated:
            q_, qc_, qo_ = rig.joint(a_["name"]), a_["closed_q"], a_["open_q"]
            if a_["type"] != "revolute" or abs(q_ - qc_) < 0.2 * abs(qo_ - qc_):
                continue
            T_ = rig.ann.part_pose(a_, q_)
            loc_ = (pts_ - T_[:3, 3]) @ T_[:3, :3]
            for lo_, hi_ in a_.get("part_boxes") or [a_["part_box"]]:
                d_ = np.linalg.norm(np.maximum(np.maximum(np.asarray(lo_) - loc_, loc_ - np.asarray(hi_)), 0.0), axis=1)
                near_door = min(near_door, float(d_.min()))
        if near_door < 0.75:
            moved = _back_off(rig, dist=0.30)
            rig.log("navigate_back_from_door", door_dist=round(near_door, 3), moved_m=round(moved, 3))
        if not rig.tuck():
            # The hand is still over furniture (e.g. just released into a bin on
            # a shelf): reverse the base out first, then fold in free space.
            moved = _back_off(rig, dist=0.35)
            rig.log("tuck_after_back_off", moved_m=round(moved, 3))
            if not (moved > 0.05 and rig.tuck()):
                # e.g. parked along a wall with the right elbow toward it:
                # shift/turn the base to where the folded arm is free
                if not (_clear_for_tuck(rig) and rig.tuck()):
                    raise SkillFailure(f"{label}: cannot fold the arm without hitting something")
    else:
        # reverse out first: lifting straight up next to furniture can hit
        # whatever stands on it (the TV on the TV stand knocked objects out).
        # Only when the load is over a surface: a needless reverse
        # and return drive swung a rim-held bowl out of its pinch.
        if _load_near_furniture(rig):
            _back_off(rig)
        _carry_pose(rig, min_bottom_z=min_bottom_z)
        if min_bottom_z is not None:
            bottom_z = float(rig.geo.bottom(rig.held["name"], rig.state())[2])
            rig.log("carry_height", bottom_z=round(bottom_z, 3), requested=round(float(min_bottom_z), 3))
        check_held(rig, "carry_up")
    rig.sync_world()
    path = None
    loaded = rig.held is not None or rig.left_held is not None
    for margin in ((0.15, 0.10, 0.06) if loaded else ()):   # the carried object sticks out
        path = plan_path(rig.world, rig.base_pose(), pose, margin=margin)
        if path is not None:
            rig.log("carry_clearance", margin=margin)
            break
    if path is None:
        path = plan_path(rig.world, rig.base_pose(), pose)
    if path is None:
        raise SkillFailure(f"{label}: no base path to {pose}")
    rig.log("path", waypoints=[[round(v, 2) for v in w] for w in path])
    if rig.held is None and rig.left_held is None:
        rig.drive_base(path)
    elif rig.held is None:
        check_left_held(rig, "left_carry_start")
        rig.drive_base(path, speed=0.17, turn=0.30, ramp=1.2)
        check_left_held(rig, "left_carry_end")
    else:
        obj = rig.ann.asset_of(rig.ann.objects[rig.held["name"]])
        if obj.get("container"):
            rig.drive_base(path, speed=0.17, turn=0.30, ramp=1.2)
        else:
            rig.drive_base(path, speed=0.25, turn=0.5)
        check_held(rig, "carry")


def _travel_q(rig):
    """Arm posture while driving to a park: tucked, or the current carry pose."""
    return rig.kin.rest if rig.held is None else rig.q_cmd


def _goto_park(rig, park, min_bottom_z=None):
    x, y, yaw, _ = park
    bx, by, byaw = rig.base_pose()
    if math.hypot(x - bx, y - by) > 0.02 or abs((yaw - byaw + 180) % 360 - 180) > 2:
        navigate(rig, (x, y, yaw), min_bottom_z=min_bottom_z)


# ---------------------------------------------------------------- articulated
def _handle_targets(rig, a, q, flip=False, tilt=0.0, grasp="side"):
    p, R, appr = rig.ann.handle_pose(a, q, grasp, flip, tilt)
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
    if a.get("handle") is None:          # e.g. a PartNet microwave without a handle part
        raise SkillFailure(f"{verb} {name}: no graspable handle annotated")
    q0 = rig.joint(name)
    rig.sync_world()
    rig.kin.coll_kw = {"hand_touches_part": True}
    # among feasible parks prefer the one whose arm can pull hardest along the
    # handle's motion (the 3 N·m wrist joints were the weak link)
    pull = np.asarray(a["handle"]["outward"], float) * (1 if goal != a["closed_q"] else -1) * 20.0

    failed = getattr(rig, "_failed_art_parks", {}).get(name, [])

    def score(x, y, yaw, qs):
        if any(math.hypot(x - fx, y - fy) < 0.20 for fx, fy, _ in failed):
            return -1e9                    # a ride from here already left the part unmoved
        rig.kin.set_base((x, y, 0.0), math.radians(yaw))
        return torque_ratio(rig.kin, qs[-1], pull)
    # doors hook from the free side; a drawer pull from either end
    park = None
    # untilted first; tilted side hooks for bars close to their panel; last a
    # front pinch across the bar (held by friction), for a handle whose free
    # side is blocked (the two middle handles of a double door)
    hooks = [("side", flip, tilt) for tilt in (0.0, math.radians(10), math.radians(20))
             for flip in ((False, True) if a["type"] == "prismatic" or a["handle"].get("flip_ok") else (False,))]
    if a["handle"].get("grasp") == "front":            # round pull: no gap behind it to hook into
        hooks = []
    if a["handle"].get("pre_open") is not None:        # imported handles (bar geometry annotated)
        hooks.append(("front", False, 0.0))
    for grasp, flip, tilt in hooks:
        p, R, appr, targets = _handle_targets(rig, a, q0, flip, tilt, grasp)
        if a["category"] == "microwave" and verb == "open" and abs(q0 - a["closed_q"]) < 0.05:
            # Park beside the hinge sweep. A frontal park can be IK-valid yet
            # the tucked robot grazes the door while navigating to it.
            h = a["handle"]
            side = np.asarray(h["along"], float)
            outward = np.asarray(h["outward"], float)
            xy = np.asarray(h["center"], float)[:2] - 0.555 * side[:2] - 0.25 * outward[:2]
            yaw = math.degrees(math.atan2(outward[1], outward[0])) + 15.0
            park = find_park(rig.kin, rig.world, targets, near=(xy[0], xy[1], yaw),
                             q_start=None, travel_q=_travel_q(rig),
                             ride=_ride_check(rig, a, q0, goal), max_tries=1)
            if park is not None:
                rig.kin.set_base((park[0], park[1], 0.0), math.radians(park[2]))
                if not joint_reachable(rig.kin, _travel_q(rig), park[3][0]):
                    park = None
            if park is not None:
                break
        park = find_park(rig.kin, rig.world, targets, near=rig.base_pose(), q_start=rig.q_cmd, travel_q=_travel_q(rig),
                         ride=_ride_check(rig, a, q0, goal), score=score,
                         n_best=1 if a["category"] == "refrigerator" else 3 if a["category"] == "microwave" else 10)
        if park is not None:
            break
    if park is None:
        raise SkillFailure(f"{verb} {name}: no base pose can grasp the handle and ride the motion")
    x, y, yaw, park_qs = park
    rig._last_art_park = (name, (x, y, yaw))
    rig.log(f"{verb}_park", park=[round(x, 3), round(y, 3), round(yaw, 1)], hook_side="far" if flip else "near",
            tilt_deg=round(math.degrees(tilt)), grasp=grasp)
    rig.caption = f"{verb.upper()} {a['category']}: go to handle"
    bx, by, byaw = rig.base_pose()
    if math.hypot(x - bx, y - by) > 0.02 or abs((yaw - byaw + 180) % 360 - 180) > 2:
        navigate(rig, (x, y, yaw))
    rig.kin.coll_kw = {"hand_touches_part": True}
    q_now = rig.joint(name)
    rig.log(f"{verb}_at_park", q_before=q0, q_now=q_now)
    if abs(q_now - q0) > 0.01:          # the part moved meanwhile: re-plan from here
        q_prev, q0 = q0, q_now
        rig.sync_world()
        p, R, appr, targets = _handle_targets(rig, a, q0, flip, tilt, grasp)
        bx, by, byaw = rig.base_pose()
        if abs(q_now - q_prev) < 0.05 and math.hypot(x - bx, y - by) <= 0.02:
            # Only a brush of the base nudged it: stay, and solve the handle
            # IK afresh from the real base pose instead of reusing stale hints.
            park_qs = (None, None, None)
        else:
            park = find_park(rig.kin, rig.world, targets, near=rig.base_pose(), q_start=rig.q_cmd,
                             ride=_ride_check(rig, a, q0, goal), score=score, n_best=5)
            if park is None:
                raise SkillFailure(f"{verb} {name}: part moved to {q0:.3f} and no base pose reaches it now")
            _goto_park(rig, park)
            rig.sync_world()
            park_qs = park[3]
    rig.caption = f"{verb.upper()} {a['category']}: grasp handle ({'side hook' if grasp == 'side' else 'front pinch'})"
    # a bar close to its panel (PartNet handles, ~3 cm gap): open only as far as
    # keeps the inner pad between panel and bar
    pre_open = a["handle"].get("pre_open", 0.04)
    t = a["handle"].get("thickness", 0.025)
    if grasp == "front":                  # the fingers straddle the bar across its width
        t = float(np.abs(np.asarray(a["handle"]["bar_size"], float)) @ np.abs(np.asarray(a["handle"]["along"], float)))
        pre_open = min(0.04, t / 2 + 0.015)
    rig.grip(pre_open, 90)        # fingers may start closed (after a push or a knock)
    for (tp, tR), lab, st, qh in zip(targets, ("pre_high", "pre", "handle"), (0.02, 0.01, 0.004), park_qs):
        rig.move_to(tp, tR, step=st, steps_per_wp=4 if lab == "handle" else 3, label=f"{verb}_{lab}", q_hint=qh)
    f = rig.grip(0.0, 120)
    # closed on the bar: both fingers stopped by it (thin arched pulls: ~5 mm)
    if not (f.min() > min(0.004, 0.3 * t) and max(0.6 * t, t - 0.007) < f.sum() < t + 0.03):
        raise SkillFailure(f"{verb} {name}: handle not grasped, fingers {f.round(4).tolist()}")
    rig.caption = f"{verb.upper()} {a['category']}: base follows the joint motion"
    if grasp == "front":                  # held by friction only: pull gently
        _ride(rig, a, goal, lead=0.01, rate=0.12)
    else:
        _ride(rig, a, goal)
    rig.step(30)
    rig.caption = f"{verb.upper()} {a['category']}: release"
    rig.grip(pre_open, 70)
    q = rig.joint(name)
    p, R, appr = rig.ann.handle_pose(a, q, grasp, flip, tilt)
    # the hand is free already: back off as far as the arm allows, then up
    for back in (0.14, 0.08, 0.04):
        try:
            rig.move_to(p - back * appr, R, step=0.006, steps_per_wp=4, label=f"{verb}_back", collision=False)
            rig.move_to(p - back * appr + np.array([0, 0, 0.12]), R, step=0.01, label=f"{verb}_up",
                        collision=False)
            break
        except SkillFailure as e:
            rig.log("retreat_short", back=back, reason=str(e))
    else:                                 # no straight retreat: at least lift the open hand off the handle
        try:
            rig.move_to(p + np.array([0, 0, 0.08]), R, step=0.005, label=f"{verb}_up", collision=False)
        except SkillFailure as e:
            rig.log("retreat_short", back=0.0, reason=str(e))
    rig.step(60)
    q = rig.joint(name)
    rig.log(f"{verb}_result", name=name, before=q0, after=q, goal=goal)
    if a["type"] == "revolute":
        tol = 0.10
    elif goal == a["closed_q"]:
        tol = 0.04           # same as the evaluator's "closed"
    else:                    # a released drawer slides back a little: 60 % open is open
        tol = 0.4 * abs(a["open_q"] - a["closed_q"])
    ok = abs(q - goal) < tol
    if not ok:
        raise SkillFailure(f"{verb} {name}: joint {q0:.3f} -> {q:.3f}, goal {goal:.3f}")
    return q


def _move_with_retry(rig, name, goal, verb):
    """Waist kept nearly upright while the left hand carries a load: bending
    it swings the left arm (and its load) into the furniture being worked
    (a 39-degree bow to a cabinet door knocked a rolling pin out)."""
    if getattr(rig, "left_held", None) is None or not hasattr(rig.kin, "names"):
        return _move_with_retry_impl(rig, name, goal, verb)
    widx = rig.kin.names.index("waist_pitch_joint")
    hi = float(rig.kin.hi[widx])
    rig.kin.hi[widx] = min(hi, 0.25)
    try:
        return _move_with_retry_impl(rig, name, goal, verb)
    finally:
        rig.kin.hi[widx] = hi


def _move_with_retry_impl(rig, name, goal, verb):
    """A handle grasp can slide along the bar from some parks (the joint does
    not move at all): remember that park and try once from another."""
    q0 = rig.joint(name)
    try:
        return _move_articulated(rig, name, goal, verb)
    except SkillFailure as exc:
        last = getattr(rig, "_last_art_park", None)
        progress = abs(rig.joint(name) - q0) / max(1e-6, abs(goal - q0))
        if rig.held is not None or last is None or last[0] != name or progress > 0.3 \
                or not ("joint" in str(exc) or "handle not grasped" in str(exc)):
            raise
        if not hasattr(rig, "_failed_art_parks"):
            rig._failed_art_parks = {}
        rig._failed_art_parks.setdefault(name, []).append(last[1])
        rig.log(f"{verb}_retry_other_park", failed_park=[round(v, 3) for v in last[1]])
        rig.tuck()
        return _move_articulated(rig, name, goal, verb)


def open_articulated(rig, name, goal=None):
    a = rig.ann.art(name)
    return _move_with_retry(rig, name, a["open_q"] if goal is None else goal, "open")


def close_articulated(rig, name):
    a = rig.ann.art(name)
    return _move_with_retry(rig, name, a["closed_q"], "close")


# ---------------------------------------------------------------- geometry
def _yaw(quat):
    R = quat_R(quat)
    return math.atan2(R[1, 0], R[0, 0])


def _half_along(size, yaw, n):
    """Half extent of a flat box (size, yaw) along the horizontal unit vector n."""
    ex = np.array([math.cos(yaw), math.sin(yaw)])
    ey = np.array([-math.sin(yaw), math.cos(yaw)])
    return abs(float(n @ ex)) * size[0] / 2 + abs(float(n @ ey)) * size[1] / 2


def _perp(n):
    return np.array([-n[1], n[0]])


def _edge_coord(s, n):
    """Coordinate of the support edge with outward normal n (axis aligned), along n."""
    x0, y0, x1, y1 = s["aabb_xy"]
    return {(1, 0): x1, (-1, 0): -x0, (0, 1): y1, (0, -1): -y0}[(int(round(n[0])), int(round(n[1])))]


def _holder_mask(B, s):
    """Obstacle boxes that carry the support itself (table, bookcase...)."""
    x0, y0, x1, y1 = s["aabb_xy"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (B[:, 0] <= cx) & (B[:, 3] >= cx) & (B[:, 1] <= cy) & (B[:, 4] >= cy) & \
        (B[:, 2] <= s["z"] - 0.005) & (B[:, 5] >= s["z"] - 0.03)


def _free_beyond(rig, s, n, depth=0.25):
    """No wall/furniture in a slab just beyond the support edge (the
    support's own furniture excluded)."""
    B = rig.world.B[:-1]
    B = B[~_holder_mask(B, s)]
    x0, y0, x1, y1 = s["aabb_xy"]
    # lateral inset: a surface against a wall overlaps the wall box by ~2 cm
    ins = 0.03
    x0, x1 = (x0 + ins, x1 - ins) if x1 - x0 > 3 * ins else (x0, x1)
    y0, y1 = (y0 + ins, y1 - ins) if y1 - y0 > 3 * ins else (y0, y1)
    e = _edge_coord(s, n)
    if abs(n[0]) > 0.5:
        lo = np.array([e + 0.005 if n[0] > 0 else -e - depth, y0, s["z"] - 0.08])
        hi = np.array([e + depth if n[0] > 0 else -e - 0.005, y1, s["z"] + 0.12])
    else:
        lo = np.array([x0, e + 0.005 if n[1] > 0 else -e - depth, s["z"] - 0.08])
        hi = np.array([x1, e + depth if n[1] > 0 else -e - 0.005, s["z"] + 0.12])
    hit = (B[:, 0] < hi[0]) & (B[:, 3] > lo[0]) & (B[:, 1] < hi[1]) & (B[:, 4] > lo[1]) & \
        (B[:, 2] < hi[2]) & (B[:, 5] > lo[2])
    return not bool(hit.any())


def _open_edges(rig, s):
    """Edges of a support a flat object can hang over.  Interior shelves
    (another level above) only open at the front: the side of the depth axis
    with more free space."""
    dirs = [np.array(d, float) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    B = rig.world.B[:-1]
    hold = B[_holder_mask(B, s)]
    interior = len(hold) and float(hold[:, 5].max()) > s["z"] + 0.12
    if not interior:
        return [n for n in dirs if _free_beyond(rig, s, n)]
    x0, y0, x1, y1 = s["aabb_xy"]
    axis = 0 if (x1 - x0) < (y1 - y0) else 1          # depth axis = the short one
    best, room = None, -1.0
    for sign in (1.0, -1.0):
        n = np.zeros(2)
        n[axis] = sign
        free = 0.0
        for d in np.arange(0.1, 1.01, 0.1):
            if not _free_beyond_hold(rig, s, n, hold, d):
                break
            free = d
        if free > room:
            best, room = n, free
    return [best] if room >= 0.3 else []


def _free_beyond_hold(rig, s, n, hold, depth):
    """Slab beyond the holder's own face (for the front of a bookcase)."""
    B = rig.world.B[:-1]
    x0, y0, x1, y1 = s["aabb_xy"]
    lo, hi = np.array([x0, y0, 0.05]), np.array([x1, y1, 1.0])
    k = 0 if abs(n[0]) > 0.5 else 1
    if n[k] > 0:
        face = float(hold[:, 3 + k].max())
        lo[k], hi[k] = face + 0.01, face + depth
    else:
        face = float(hold[:, k].min())
        lo[k], hi[k] = face - depth, face - 0.01
    hit = (B[:, 0] < hi[0]) & (B[:, 3] > lo[0]) & (B[:, 1] < hi[1]) & (B[:, 4] > lo[1]) & \
        (B[:, 2] < hi[2]) & (B[:, 5] > lo[2])
    return not bool(hit.any())


def _overlaps_objects(rig, box, exclude, st, margin=0.02):
    for other in rig.ann.objects:
        if other in exclude:
            continue
        b = rig.geo.bottom(other, st)
        fp = rig.geo.footprint(other, st, margin)
        if box[0] < fp[2] and fp[0] < box[2] and box[1] < fp[3] and fp[1] < box[3] and \
                box[4] > b[2] - 0.01 and box[5] < b[2] + 0.5:
            return True
    return False


# ---------------------------------------------------------------- pick
def _grasp_legs(g):
    appr = -g["R"][:, 2]
    p = g["p"]
    if g["kind"] == "top_pinch" and p[2] > 0.92:
        # a high top pinch (a lid knob on the hob): fingers-down reach ends
        # near 1.0 m, so approach from 5 cm instead of 12 cm above
        return [(p - 0.05 * appr, g["R"]), (p - 0.025 * appr, g["R"]), (p, g["R"])]
    return [(p - 0.08 * appr + np.array([0, 0, 0.04]), g["R"]), (p - 0.04 * appr, g["R"]), (p, g["R"])]


def _lift_height(g):
    return 0.045 if g["kind"] == "top_pinch" and g["p"][2] > 0.92 else 0.07


def pick(rig, name, max_candidates=12):
    """Pinch grasp if the asset has one; flat objects wider than the gripper
    are pushed over a support edge and pinched at the overhang."""
    obj = rig.ann.objects[name]
    kinds = [g["type"] for g in rig.ann.asset_of(obj)["grasps"]]
    if not kinds:
        raise SkillFailure(f"pick {name}: asset '{obj['asset']}' has no Zeno-feasible grasp annotation")
    if any(k != "edge_pinch_after_push" for k in kinds):
        try:
            return _pick_pinch(rig, name, max_candidates)
        except SkillFailure as e:
            if "edge_pinch_after_push" not in kinds or rig.held is not None:
                raise
            rig.log("pick_fallback", obj=name, reason=str(e), to="push_then_edge_pinch")
    return pick_flat(rig, name)


def _pick_pinch(rig, name, max_candidates=12, kinds=("top_pinch", "rim_pinch", "rim_pinch_rect")):
    """Pinch pick; above table height the waist stays nearly upright (a
    40-degree bow at a counter drove the forearm into it and knocked the
    object before the grasp)."""
    pos, _ = rig.obj_pose(name)
    if not hasattr(rig.kin, "names"):          # minimal rig stubs in unit tests
        return _pick_pinch_impl(rig, name, max_candidates, kinds)
    widx = rig.kin.names.index("waist_pitch_joint")
    hi = float(rig.kin.hi[widx])
    sup = rig.geo.support_under(name, rig.state())
    inside = sup is not None and (sup.get("category") == "cabinet_inside" or "/inside" in sup["name"])
    if pos[2] <= 0.5 or inside or hi <= 0.2:  # cavities and shelves need the bow to reach in
        return _pick_pinch_impl(rig, name, max_candidates, kinds)
    rig.kin.hi[widx] = 0.2
    try:
        return _pick_pinch_impl(rig, name, max_candidates, kinds)
    except SkillFailure as exc:
        if "no reachable grasp" not in str(exc):
            raise
        rig.log("pick_waist_relaxed", obj=name)
    finally:
        rig.kin.hi[widx] = hi
    try:
        return _pick_pinch_impl(rig, name, max_candidates, kinds)   # high knobs need the bow
    except SkillFailure as exc:
        if "no reachable grasp" not in str(exc):
            raise
        # last resort: neighbours as whole boxes over-constrain a pick from a
        # tight cluster at a counter edge; the finger slots are still checked
        rig.log("pick_neighbours_relaxed", obj=name)
        return _pick_pinch_impl(rig, name, max_candidates, kinds, use_neighbours=False)


def _neighbour_boxes(rig, name, st, radius=0.30):
    """Loose objects next to a pick target that stand taller than its grasp
    height: the forearm must not hit them (a stalled arm 7 cm short of a can
    in a cluster).  The target, its contents and lid are excluded."""
    from .predicates import lid_on
    c = rig.geo.centre(name, st)
    z_grasp = float(rig.geo.bottom(name, st)[2])
    from .annotations import _tilted
    if _tilted(st["objects"][name]["quat"]):
        z_grasp = float(c[2])        # lying on its side: pinched across its centre
    a = rig.ann.asset_of(rig.ann.objects[name])
    out = []
    for o in rig.ann.objects:
        if o == name or (rig.held is not None and o == rig.held["name"]):
            continue
        if a.get("container") and (rig.geo.inside(o, name, st)[0] or lid_on(rig, name, o, st)[0]):
            continue
        fp = rig.geo.footprint(o, st)
        d = math.hypot(max(fp[0] - c[0], 0, c[0] - fp[2]), max(fp[1] - c[1], 0, c[1] - fp[3]))
        if d > radius:
            continue
        b = float(rig.geo.bottom(o, st)[2])
        top = b + float(rig.ann.asset_of(rig.ann.objects[o])["size"][2])
        if top < z_grasp + 0.04:
            continue
        out.append([fp[0] - 0.005, fp[1] - 0.005, b, fp[2] + 0.005, fp[3] + 0.005, top + 0.005])
    return out


def _pick_pinch_impl(rig, name, max_candidates=12, kinds=("top_pinch", "rim_pinch", "rim_pinch_rect"),
                     use_neighbours=True):
    world = getattr(rig, "world", None)
    if world is None or not hasattr(world, "temp_obstacles"):          # minimal rig stubs in unit tests
        return _pick_pinch_core(rig, name, max_candidates, kinds)
    boxes = _neighbour_boxes(rig, name, rig.state()) if use_neighbours else []
    if boxes:
        rig.log("pick_neighbour_obstacles", obj=name, n=len(boxes))
        with rig.world.temp_obstacles(boxes):
            return _pick_pinch_core(rig, name, max_candidates, kinds)
    return _pick_pinch_core(rig, name, max_candidates, kinds)


def _pick_pinch_core(rig, name, max_candidates=12, kinds=("top_pinch", "rim_pinch", "rim_pinch_rect")):
    obj = rig.ann.objects[name]
    pos, quat = rig.obj_pose(name)
    st = rig.state()
    floor_z = float(rig.geo.bottom(name, st)[2])
    cands = rig.ann.grasp_poses(obj, pos, quat, kinds=kinds)
    if not cands:
        raise SkillFailure(f"pick {name}: no pinch grasp annotated")
    # a finger slot occupied by a neighbour jams the finger before it closes
    # (the arm model ignores the fingers); keep the pinches whose slots are free
    from .predicates import slot_blocker, _neighbour_boxes
    try:
        st_ = rig.state()
        nb = _neighbour_boxes(rig, name, st_)
        free = [g for g in cands if slot_blocker(rig, name, g, st_, nb) is None]
        if free and len(free) < len(cands):
            rig.log("pick_free_slots", obj=name, kept=len(free), of=len(cands))
            cands = free
    except Exception as exc:      # minimal rigs in unit tests
        rig.log("pick_free_slots_skipped", reason=str(exc)) if hasattr(rig, "log") else None
    for g in cands:              # pads must not dig into the surface below
        if g["kind"] == "top_pinch":
            g["p"] = g["p"].copy()
            g["p"][2] = max(g["p"][2], floor_z + 0.022)
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    rig.focus_z = float(pos[2])
    bx, by, _ = rig.base_pose()
    # A fridge shelf is recessed behind its door. The robot's post-opening
    # pose biases the generic park search toward the hinge; seed the open
    # side of this shelf so a reachable rim grasp is considered promptly.
    fridge_shelf = str(obj.get("support", "")).startswith("breakfast_fridge/")
    microwave = next((a for a in rig.ann.articulated
                      if a["name"] == "kitchen_microwave" and "cavity_aabb" in a), None)
    cavity = microwave["cavity_aabb"] if microwave is not None else None
    in_microwave = microwave is not None and all(
        cavity[i] < pos[i] < cavity[i + 3] for i in range(3))
    retrieval_q = None
    if in_microwave:
        if abs(rig.joint("kitchen_microwave") - microwave["open_q"]) > 0.10:
            raise SkillFailure(f"pick {name}: microwave door is closed")
        # The only entry is from the front (low Y). Return to the arm/base
        # pose that physically cleared the open door during loading.
        retrieval_q = getattr(rig, "microwave_retrieval_q", None)
        search_near = (4.8, 1.7, 150.0) if retrieval_q is not None else (4.8, 1.7)
        cands.sort(key=lambda g: (g["p"][1], -g.get("tilt", 0),
                                  abs(g["p"][0] - (cavity[0] + cavity[3]) / 2)))
    elif fridge_shelf:
        search_near = (6.246, 2.337, 135.0)
        cands.sort(key=lambda g: (abs((g.get("azimuth", 0) + 180) % 360 - 180),
                                  -g.get("tilt", 0)))
    else:
        search_near = rig.base_pose()
        # off-centre pinch points of a long object let it swing in the hand:
        # prefer the centre, use the others when it is out of reach
        cands.sort(key=lambda g: np.linalg.norm(g["p"][:2] - np.array([bx, by])) + 0.3 * g.get("along_rank", 0))
    park, g = None, None
    for g in cands[:max_candidates]:
        lift = [(g["p"] + np.array([0, 0, _lift_height(g)]), g["R"])]
        park = find_park(rig.kin, rig.world, _grasp_legs(g) + lift, near=search_near,
                         max_tries=1 if in_microwave and retrieval_q is not None else 60 if in_microwave else 120,
                         q_start=retrieval_q if in_microwave and retrieval_q is not None else
                                 None if in_microwave or fridge_shelf else rig.q_cmd,
                         travel_q=None if in_microwave and retrieval_q is not None else _travel_q(rig))
        if park:
            break
    if park is None and "top_pinch" in kinds and hasattr(rig.ann, "asset_of"):
        # a square block can also be pinched across its other pair of faces
        extra = [c for c in rig.ann.grasp_poses(obj, pos, quat, kinds=("top_pinch",), extra_rotations=True)
                 if not any(np.allclose(c["R"], c0["R"], atol=1e-3) and np.allclose(c["p"], c0["p"], atol=1e-3)
                            for c0 in cands)]
        for g in extra:
            g["p"] = g["p"].copy()
            g["p"][2] = max(g["p"][2], floor_z + 0.022)
            lift = [(g["p"] + np.array([0, 0, _lift_height(g)]), g["R"])]
            park = find_park(rig.kin, rig.world, _grasp_legs(g) + lift, near=search_near, max_tries=120,
                             q_start=rig.q_cmd, travel_q=_travel_q(rig))
            if park:
                rig.log("pick_rotated_pinch", obj=name)
                break
    if park is None:
        from .planner import LAST_PARK_DIAG
        getattr(rig, "log", lambda *a, **k: None)("pick_no_park", obj=name, pos=[round(float(v), 3) for v in pos],
                quat=[round(float(v), 3) for v in quat], n_cands=len(cands),
                diag={k: v for k, v in LAST_PARK_DIAG.items() if v})
        raise SkillFailure(f"pick {name}: no reachable grasp from any base pose")
    x, y, yaw, park_qs = park
    rig.log("pick_park", obj=name, kind=g["kind"], park=[round(x, 3), round(y, 3), round(yaw, 1)],
            floor=bool(floor_z < 0.05))
    rig.caption = f"PICK {name}: approach" + (" (torso down: floor)" if floor_z < 0.05 else "")
    if in_microwave and retrieval_q is not None:
        rig.sync_world()
        rig.follow(rig.joint_path(retrieval_q, "microwave_pick_safe"))
        rig.drive_base([(x, y, yaw)], speed=0.2)
        rig.sync_world()
    else:
        _goto_park(rig, park)
    rig.kin.coll_kw = {"ignore_fingers": True}
    pos, quat = rig.obj_pose(name)          # re-read after driving
    g2 = [c for c in rig.ann.grasp_poses(obj, pos, quat) if c["kind"] == g["kind"]
          and np.linalg.norm(c["p"] - g["p"]) < 0.03 and np.allclose(c["R"], g["R"], atol=1e-3)]
    if g2:
        p2 = g2[0]["p"].copy()
        p2[2] = max(p2[2], g["p"][2]) if g["kind"] == "top_pinch" else p2[2]
        g = dict(g2[0], p=p2)
    rig.log("pick_target", obj=name, pos=[round(float(v), 3) for v in pos],
            quat=[round(float(v), 3) for v in quat], p=[round(float(v), 3) for v in g["p"]],
            kind=g["kind"], azimuth=g.get("azimuth"), tilt=g.get("tilt"))
    rig.grip(g["pre_open"], 40)
    for (tp, tR), lab, st_, spw, qh in zip(_grasp_legs(g), ("pre_far", "pre", "grasp"), (0.02, 0.005, 0.003),
                                           (3, 3, 4), park_qs):
        err = rig.move_to(tp, tR, step=st_, steps_per_wp=spw, label=f"pick_{lab}", q_hint=qh, smooth=True)
    if err > 0.008:                     # round objects pop out of an off-centre pinch
        rig.move_to(g["p"], g["R"], step=0.002, steps_per_wp=6, label="pick_grasp_fix", collision=False, smooth=True)
    rig.caption = f"PICK {name}: close gripper"
    rig.grip(0.0, 120, gradual=True)
    rig.caption = f"PICK {name}: lift"
    rig.move_to(g["p"] + np.array([0, 0, _lift_height(g)]), g["R"], step=0.002, steps_per_wp=6, label="pick_lift",
                collision=False, smooth=True)
    rig.step(40)
    after, _ = rig.obj_pose(name)
    f = rig.fingers()
    held = bool(f.min() > 0.003) and after[2] - pos[2] > 0.015
    rig.log("pick_result", obj=name, kind=g["kind"], lift_m=round(float(after[2] - pos[2]), 4),
            fingers=f.round(4).tolist(), held=held)
    rig.focus_z = None
    if not held:
        raise SkillFailure(f"pick {name}: not held (lift {after[2] - pos[2]:.3f} m)")
    tcp, R = rig.kin.tcp(rig.q_cmd)
    rig.held = {"name": name, "kind": "pinch", "tcp_minus_body": tcp - after, "R": R, "pre_open": g["pre_open"]}
    if in_microwave:
        # Lift alone leaves most of the bowl behind the door plane. Withdraw
        # horizontally through the front before moving the base away.
        for y, label in ((cavity[1] - 0.10, "microwave_pick_front"),
                         (cavity[1] - 0.23, "microwave_pick_clear")):
            tcp_now, _ = rig.kin.tcp(rig.q_cmd)
            target = tcp_now.copy()
            target[1] = y
            rig.move_to(target, R, step=0.004, steps_per_wp=5, label=label)
            check_held(rig, label)
    return True


def push(rig, name, s, n, distance, label="PUSH", enough=None, *, mode=None):
    """Slide ``name`` by ``distance`` along the horizontal unit vector n on
    support s: fingers closed and pointing down, pads just above the surface,
    starting behind the object; when nothing reaches behind it (back of a
    counter against a wall) drag it instead, pads pressed on its top.  Legs of
    at most PUSH_SEG; the base re-parks between legs.  Returns the distance
    actually moved (measured).  Stops early once ``enough`` has been moved:
    every extra leg re-parks the base next to an object that may overhang."""
    if mode not in (None, "push", "drag"):
        raise ValueError(f"unknown contact mode: {mode}")
    geo = rig.geo
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    b0 = geo.bottom(name, rig.state())
    moved = 0.0
    lat = _perp(n)
    # Closed fingers push equally well whichever way they would close; the arm
    # can reach some of these wrist yaws and not others from a given side.
    R_options = [gripper_rot([0, 0, -1.0], [d[0], d[1], 0.0]) for d in (lat, -lat, n, -n)]
    z = s["z"] + 0.03                   # pad bottom ~5 mm above the surface
    while moved < distance - 0.01 and (enough is None or moved < enough):
        st = rig.state()
        b = geo.bottom(name, st)
        h = _half_along(size, _yaw(st["objects"][name]["quat"]), n)
        d = min(PUSH_SEG, distance - moved)
        start = b[:2] - n * (h + 0.035)
        def _push_legs(R):
            return [(np.r_[start, z + 0.10], R), (np.r_[start, z], R), (np.r_[start + n * (d + 0.025), z], R),
                    (np.r_[start + n * (d + 0.025), z + 0.10], R)]
        # Drag with the closed fingertips pressing into the top near the leading
        # rim. The TCP is about 2 cm above the pad tip; a higher target only
        # brushes the object and produces no measurable drag.
        # used when nothing can reach behind the object (back of a counter)
        top = b[2] + size[2] - 0.004 + 0.010
        grab = b[:2] + n * max(0.0, h - 0.03)
        drag_travel = d + 0.025  # fingertip skid: compensate with measured-motion loop
        def _drag_legs(R):
            return [(np.r_[grab, top + 0.08], R), (np.r_[grab, top], R),
                    (np.r_[grab + n * drag_travel, top], R),
                    (np.r_[grab + n * drag_travel, top + 0.08], R)]
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        park, selected_mode, legs = None, None, None
        candidates = [(m, f(R)) for m, f in (("push", _push_legs), ("drag", _drag_legs)) for R in R_options]
        for candidate_mode, cand_legs in candidates:
            if mode is not None and candidate_mode != mode:
                continue
            park = find_park(rig.kin, rig.world, cand_legs, near=rig.base_pose(), max_tries=60, q_start=rig.q_cmd,
                             travel_q=_travel_q(rig))
            if park is not None:
                selected_mode, legs = candidate_mode, cand_legs
                break
        if park is None:
            raise SkillFailure(f"push {name}: no base pose reaches {mode or 'a push or a drag'}")
        rig.log("push_park", obj=name, mode=selected_mode, dir=n.round(3).tolist(), d=round(d, 3),
                park=[round(v, 3) for v in park[:3]])
        rig.caption = f"{label} {name}: " + ("go behind it" if selected_mode == "push" else "press on it to drag")
        rig.focus_z = s["z"]
        _goto_park(rig, park)
        rig.kin.coll_kw = {"ignore_fingers": True}
        rig.grip(0.0, 30)
        rig.move_to(*legs[0], step=0.02, label="push_above", q_hint=park[3][0])
        rig.move_to(*legs[1], step=0.005, steps_per_wp=4, label=f"{selected_mode}_down", collision=False)
        rig.caption = f"{label} {name}: " + ("slide along the surface" if selected_mode == "push" else "drag it along")
        rig.move_to(*legs[2], step=0.003, steps_per_wp=4, label="push_slide", collision=False)
        rig.move_to(*legs[3], step=0.01, label="push_up", collision=False)
        b2 = geo.bottom(name, rig.state())
        step_moved = float(n @ (b2[:2] - b[:2]))
        moved = float(n @ (b2[:2] - b0[:2]))
        rig.log("push_result", obj=name, moved=round(step_moved, 3), total=round(moved, 3))
        # a short top-up leg is mostly approach: judge it against its own length
        if step_moved < min(0.01, 0.3 * d):
            raise SkillFailure(f"push {name}: object did not move")
    rig.focus_z = None
    rig.grip(0.04, 40)            # leave the hand open for whatever comes next
    return moved


def pick_flat(rig, name):
    """Flat object wider than the gripper (plate, book, notebook): push it
    until it overhangs a free support edge (centre of mass still on the
    support), then pinch the overhang between the pads, approaching
    horizontally from outside the edge."""
    geo = rig.geo
    st = rig.state()
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    s = geo.support_under(name, st)
    if s is None:
        if geo.bottom(name, st)[2] < 0.05:
            return _corner_pinch(rig, name)
        raise SkillFailure(f"pick {name}: flat object not on an annotated support: no edge to push it over")
    b = geo.bottom(name, st)
    yaw = _yaw(st["objects"][name]["quat"])
    edges = []
    for n in _open_edges(rig, s):
        h = _half_along(size, yaw, n)
        o = min(0.08, h - COM_MARGIN)
        if o < EDGE_MIN_OVERHANG:
            continue
        over = float(n @ b[:2]) + h - _edge_coord(s, n)
        edges.append((max(0.0, o - over), n, o))
    edges.sort(key=lambda e: e[0])
    rig.log("flat_edges", obj=name, support=s["name"], edges=[[round(e[0], 3), e[1].tolist()] for e in edges])
    if not edges:
        raise SkillFailure(f"pick {name}: no free edge of {s['name']} it can overhang")
    last = None
    for need, n, o in edges[:3]:
        try:
            st = rig.state()
            b = geo.bottom(name, st)
            h = _half_along(size, _yaw(st["objects"][name]["quat"]), n)
            over = float(n @ b[:2]) + h - _edge_coord(s, n)
            if over < o - 0.012:
                push(rig, name, s, n, o - over + 0.005, label="PUSH (edge pinch)",
                     enough=EDGE_MIN_OVERHANG + 0.005 - over)
            return _edge_pinch(rig, name, s, n)
        except SkillFailure as e:
            last = e
            rig.log("edge_failed", obj=name, dir=n.tolist(), reason=str(e))
            if rig.held is not None:
                raise
    raise last


def _corner_pinch(rig, name):
    """Flat object on the floor (book, notebook): no edge to push it over, so
    pinch it diagonally.  The lower pad presses one side face just above the
    floor (up and in), the upper pad the top face d further in; the closing
    axis is tilted ~atan(d/t) from vertical, inside the rubber pads' friction
    cone (mu 2 -> 63 deg).  The TCP sits back along the approach so the lower
    pad meets the side face with its tip and never digs into the floor."""
    geo = rig.geo
    st = rig.state()
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    t = size[2]
    reach = 0.075                                       # contact spacing inside the 8 cm opening
    if t > reach - 0.005:
        raise SkillFailure(f"corner pinch {name}: {t:.3f} m thick, the gripper opens {reach:.3f}")
    d = min(0.055, math.sqrt(reach ** 2 - t ** 2))
    b = np.array(geo.bottom(name, st), float)
    # the measured lowest point (rotated box), never below the floor it rests on
    b[2] = max(float(_lowest_z(rig, name, st)), 0.0) if b[2] < 0.05 else float(_lowest_z(rig, name, st))
    rig.log("corner_pinch_measure", obj=name, bottom_z=round(float(b[2]), 4), thickness=round(float(t), 4))
    yaw = _yaw(st["objects"][name]["quat"])
    cands = []
    for k in range(4):                                  # the four sides of the object
        n = np.array([math.cos(yaw + k * math.pi / 2), math.sin(yaw + k * math.pi / 2)])
        h = _half_along(size, yaw, n)
        # lower pad on the side face 1.6 cm up (its open tip would touch the
        # floor at the very edge), upper pad on the top face d further in
        # heights relative to the measured bottom: the resting collider can sit
        # a few mm off z = 0, and absolute heights then pinch above the object
        low = np.r_[b[:2] + n * (h + 0.003), max(0.012, b[2] + 0.016)]
        up = np.r_[b[:2] + n * (h - d), b[2] + t]
        c = (up - low) / np.linalg.norm(up - low)
        a = np.r_[-n * t, -d] / math.hypot(t, d)        # into the object and down
        tcp = (low + up) / 2 - a * 0.022
        R = gripper_rot(a, c)
        legs = [(tcp - a * 0.12 + np.array([0, 0, 0.03]), R), (tcp - a * 0.04, R), (tcp, R)]
        lift = tcp + np.array([0, 0, 0.10])
        bx, by, _ = rig.base_pose()
        cands.append((math.hypot(tcp[0] - bx, tcp[1] - by), n, legs, lift, R))
    cands.sort(key=lambda c_: c_[0])
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    park = None
    for _, n, legs, lift, R in cands:
        # the lift is left out of the park search: it rides the torso up and
        # its straight line breaks the IK chain of the tilted approach
        park = find_park(rig.kin, rig.world, legs, near=rig.base_pose(), max_tries=150,
                         q_start=rig.q_cmd, travel_q=_travel_q(rig))
        if park:
            break
    if park is None:
        raise SkillFailure(f"corner pinch {name}: no base pose reaches any side")
    rig.log("corner_pinch_park", obj=name, side=n.round(3).tolist(), park=[round(v, 3) for v in park[:3]],
            d=round(d, 3))
    rig.caption = f"PICK {name}: corner pinch from the floor (torso down)"
    rig.focus_z = 0.1
    _goto_park(rig, park)
    rig.kin.coll_kw = {"ignore_fingers": True}
    rig.grip(0.04, 40)
    rig.move_to(*legs[0], step=0.02, label="corner_pre_far", q_hint=park[3][0])
    rig.move_to(*legs[1], step=0.005, steps_per_wp=3, label="corner_pre", collision=False)
    contact_error = rig.move_to(*legs[2], step=0.003, steps_per_wp=4,
                                label="corner_grasp", collision=False)
    if contact_error > 0.02:
        contact_error = rig.move_to(*legs[2], step=0.002, steps_per_wp=8,
                                    label="corner_grasp_retry", collision=False, smooth=True)
    if contact_error > 0.02:
        raise SkillFailure(f"corner pinch {name}: contact pose missed by {contact_error:.3f} m")
    rig.caption = f"PICK {name}: close across the edge and the top face"
    rig.grip(0.0, 140)
    rig.caption = f"PICK {name}: lift"
    rig.move_to(lift, R, step=0.002, steps_per_wp=6, label="corner_lift", collision=False)
    rig.step(40)
    st2 = rig.state()
    b2 = geo.bottom(name, st2)
    f = rig.fingers()
    held = bool(f.min() > 0.003) and b2[2] - b[2] > 0.03
    rig.log("pick_result", obj=name, kind="corner_pinch", lift_m=round(float(b2[2] - b[2]), 4),
            fingers=f.round(4).tolist(), held=held)
    rig.focus_z = None
    if not held:
        raise SkillFailure(f"corner pinch {name}: not held (lift {b2[2] - b[2]:.3f} m)")
    tcp_now, R_now = rig.kin.tcp(rig.q_cmd)
    body, _ = rig.obj_pose(name)
    rig.held = {"name": name, "kind": "corner", "tcp_minus_body": tcp_now - body, "R": R_now, "pre_open": 0.04,
                "body_minus_low": float(body[2] - _lowest_z(rig, name, st2))}
    return True


def _lowest_z(rig, name, st):
    """Lowest corner of the object's box (tilted objects)."""
    o = st["objects"][name]
    a = rig.ann.asset_of(rig.ann.objects[name])
    R = quat_R(o["quat"])
    lo = np.asarray(a["origin_to_bottom_center"], float) - np.r_[np.asarray(a["size"][:2]) / 2, 0.0]
    corners = np.array([[lo[0] + i * a["size"][0], lo[1] + j * a["size"][1], lo[2] + k * a["size"][2]]
                        for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    return float((np.asarray(o["pos"]) + corners @ R.T)[:, 2].min())


def _edge_pinch(rig, name, s, n):
    geo = rig.geo
    st = rig.state()
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    b = geo.bottom(name, st)
    yaw = _yaw(st["objects"][name]["quat"])
    h = _half_along(size, yaw, n)
    over = float(n @ b[:2]) + h - _edge_coord(s, n)
    if over < EDGE_MIN_OVERHANG - 0.01:
        raise SkillFailure(f"edge pinch {name}: overhang only {over:.3f} m")
    n3 = np.r_[n, 0.0]
    depth = max(0.02, min(EDGE_GRIP_DEPTH, over - EDGE_PAD_CLEAR))
    tcp = np.r_[b[:2] + n * (h - depth), b[2] + size[2] / 2]
    R = gripper_rot(-n3, [0, 0, 1.0])
    pre_open = min(0.04, size[2] / 2 + 0.012)
    legs = [(tcp + n3 * 0.12 + np.array([0, 0, 0.03]), R), (tcp + n3 * 0.05, R), (tcp, R)]
    lift = tcp + np.array([0, 0, 0.04])
    pull = lift + n3 * 0.12
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    park = find_park(rig.kin, rig.world, legs + [(lift, R), (pull, R)], near=rig.base_pose(), max_tries=150,
                     q_start=rig.q_cmd, travel_q=_travel_q(rig))
    if park is None:
        raise SkillFailure(f"edge pinch {name}: no base pose reaches the overhang")
    rig.log("edge_pinch_park", obj=name, park=[round(v, 3) for v in park[:3]], overhang=round(over, 3))
    rig.caption = f"PICK {name}: edge pinch (approach from outside the edge)"
    rig.focus_z = s["z"]
    _goto_park(rig, park)
    rig.kin.coll_kw = {"ignore_fingers": True}
    rig.grip(pre_open, 40)
    rig.move_to(*legs[0], step=0.02, label="edge_pre_far", q_hint=park[3][0])
    rig.move_to(*legs[1], step=0.005, steps_per_wp=3, label="edge_pre", collision=False)
    rig.move_to(*legs[2], step=0.003, steps_per_wp=4, label="edge_grasp", collision=False)
    rig.caption = f"PICK {name}: pinch the overhang"
    rig.grip(0.0, 120)
    rig.caption = f"PICK {name}: lift and pull out"
    rig.move_to(lift, R, step=0.002, steps_per_wp=6, label="edge_lift", collision=False)
    rig.step(40)
    b2 = geo.bottom(name, rig.state())
    f = rig.fingers()
    held = bool(f.min() > 0.003) and b2[2] - b[2] > 0.015
    rig.log("pick_result", obj=name, kind="edge_pinch", lift_m=round(float(b2[2] - b[2]), 4),
            fingers=f.round(4).tolist(), held=held)
    if not held:
        raise SkillFailure(f"edge pinch {name}: not held (lift {b2[2] - b[2]:.3f} m)")
    rig.move_to(pull, R, step=0.004, steps_per_wp=4, label="edge_pull", collision=False)
    rig.focus_z = None
    tcp_now, R_now = rig.kin.tcp(rig.q_cmd)
    body, _ = rig.obj_pose(name)
    b3 = geo.bottom(name, rig.state())
    rig.held = {"name": name, "kind": "edge", "tcp_minus_body": tcp_now - body, "R": R_now, "pre_open": pre_open,
                "h": h, "depth": depth, "lat_half": _half_along(size, yaw, _perp(n)),
                "dz": float(tcp_now[2] - b3[2])}
    return True


# ---------------------------------------------------------------- place
def _yaw_of(R):
    return math.atan2(R[1, 0], R[0, 0])


def insert_microwave_cavity(rig, name, support):
    """Carry a rim-held object through the *front* of an open microwave.

    The shell has real side/roof walls. A vertical lowering path chosen from
    the side can be IK-valid at its endpoint yet cannot enter the cavity.
    Plan a front staging point and horizontal insertion at release height;
    the complete shell leaves too little room for a vertical lowering stroke.
    """
    rig._microwave_load_stage = None
    if rig.held is None or rig.held["name"] != name:
        raise SkillFailure(f"place {name}: not holding it")
    a = rig.ann.art("kitchen_microwave")
    if abs(rig.joint(a["name"]) - a["open_q"]) > 0.10:
        raise SkillFailure("microwave loading: door is not open")
    s = rig.ann.support(support)
    asset = rig.ann.asset_of(rig.ann.objects[name])
    cavity = a["cavity_aabb"]
    half_x, half_y = float(asset["size"][0]) / 2, float(asset["size"][1]) / 2
    x = (cavity[0] + cavity[3]) / 2 - 0.02
    y = cavity[1] + half_y + 0.015
    if not (cavity[0] + half_x + 0.005 < x < cavity[3] - half_x - 0.005 and
            y + half_y + 0.005 < cavity[4]):
        raise SkillFailure(f"microwave loading: {name} does not fit the annotated cavity")
    body = np.array([x, y, s["z"] - asset["origin_to_bottom_center"][2] + 0.006])
    off0, R0 = rig.held["tcp_minus_body"], rig.held["R"]
    parks = ((4.8, 1.7, 150.0), (4.8, 1.8, 150.0),
             (4.8, 1.9, 210.0), (4.8, 2.0, 210.0))

    def legs(off, R):
        final = body + off + np.array([0, 0, 0.01])
        front = final.copy()
        front[1] = cavity[1] - 0.095
        return [(front, R), (final, R)]

    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    rig.log("microwave_load_grasp", obj=name, offset=np.round(off0, 3).tolist(),
            orientation=np.round(R0, 3).tolist())
    found = None
    # Prefer a park clear of the open door even if rotating the held bowl
    # requires a different arm yaw. The closest park made the bowl hit the door.
    for near in parks:
        for deg in (0, 45, -45, 90, -90, 135, -135, 180):
            rot = rz(math.radians(deg))
            R, off = rot @ R0, rot @ off0
            targets = legs(off, R)
            park = find_park(rig.kin, rig.world, targets, near=near,
                             max_tries=1, q_start=None, travel_q=None)
            if park is not None:
                found = (park, deg, R, targets)
                break
        if found is not None:
            break
    if found is None:
        raise SkillFailure(f"microwave loading: no front-entry IK path for {name}")
    park, deg, R, targets = found
    rig.log("microwave_load_park", obj=name, park=[round(v, 3) for v in park[:3]], yaw_deg=deg,
            body=body.round(3).tolist())
    rig.caption = f"PLACE {name}: carry to microwave front"
    rig.focus_z = s["z"]
    # The open door occupies the robot's carry corridor at bowl height.
    # Keep the bowl's bottom above the appliance roof while the base moves;
    # the staged arm trajectory lowers it in front of the cavity afterwards.
    # A carry above the roof (cavity top + 8 cm) is out of reach for a
    # rim-held bowl; instead come in straight along the park heading from
    # 45 cm behind it, so the bowl approaches the cavity front beside the open
    # door rather than sweeping across it.
    yaw_r = math.radians(park[2])
    f = np.array([math.cos(yaw_r), math.sin(yaw_r)])
    pre = (park[0] - 0.45 * f[0], park[1] - 0.45 * f[1], park[2])
    rig.sync_world()
    straight = all(rig.world.footprint_clear(park[0] - u * f[0], park[1] - u * f[1], yaw_r)
                   for u in np.linspace(0.0, 0.45, 6))
    if straight and plan_path(rig.world, rig.base_pose(), pre) is not None:
        rig.log("microwave_load_straight_in", pre=[round(v, 3) for v in pre])
        navigate(rig, pre)
        check_held(rig, "microwave_load_pre")
        rig.drive_base([park[:3]], speed=0.08, turn=0.3, ramp=1.0)
    else:
        _goto_park(rig, park, min_bottom_z=cavity[5] + 0.08)
    check_held(rig, "microwave_load_carry")
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    tcp, R_now = rig.kin.tcp(rig.q())
    body_now, _ = rig.obj_pose(name)
    hang = float(body_now[2] - _lowest_z(rig, name, rig.state()))
    body[2] = s["z"] + hang + 0.004
    off = (R @ R_now.T) @ (tcp - body_now)
    corrected = legs(off, R)
    shift = float(np.linalg.norm(corrected[1][0] - targets[1][0]))
    rig.log("microwave_load_remeasure", obj=name, shift_m=round(shift, 3),
            hang_m=round(hang, 3), offset=off.round(3).tolist(),
            target=corrected[1][0].round(3).tolist())
    replanned = find_park(rig.kin, rig.world, corrected, near=park[:3],
                          max_tries=1, q_start=None, travel_q=None)
    if replanned is None:
        # a small shift: nearby parks (short base move), else the original
        # verified entry (the cavity is wider than a few centimetres of shift)
        near_park = find_park(rig.kin, rig.world, corrected, near=park[:3], max_tries=25,
                              radii=np.arange(0.45, 0.80, 0.05), q_start=None, travel_q=None)
        if near_park is not None and math.hypot(near_park[0] - park[0], near_park[1] - park[1]) < 0.25:
            rig.log("microwave_load_repark", park=[round(v, 3) for v in near_park[:3]])
            rig.drive_base([near_park[:3]], speed=0.06, turn=0.3, ramp=0.8)
            replanned = near_park
        elif shift < 0.08:
            rig.log("microwave_load_original_entry", shift_m=round(shift, 3))
            corrected, replanned = targets, park
        else:
            raise SkillFailure(f"microwave loading: held {name} shifted {shift:.3f} m and entry is blocked")
    rig.caption = f"PLACE {name}: enter microwave from front"
    for (point, orient), label, step, hint in zip(corrected,
                                                   ("microwave_front", "microwave_insert"),
                                                   (0.005, 0.003), replanned[3]):
        # the insertion is a planned straight line into the cavity (both ends
        # IK- and collision-checked): the in-between check against the walls
        # rejected every joint path for some rim grasps
        rig.move_to(point, orient, step=step, steps_per_wp=6, label=label, q_hint=hint,
                    collision=label != "microwave_insert")
        check_held(rig, label)
    actual_body, _ = rig.obj_pose(name)
    if not (cavity[0] < actual_body[0] < cavity[3] and cavity[1] < actual_body[1] < cavity[4]):
        raise SkillFailure(f"microwave loading: held {name} did not enter the cavity")
    rig._microwave_load_stage = {"name": name, "support": support, "phase": "inserted",
                                  "targets": corrected, "R": R, "cavity": cavity,
                                  "pre_open": rig.held["pre_open"]}
    rig.log("microwave_inserted", obj=name, body=np.round(actual_body, 3).tolist())
    return True


def release_microwave_cavity(rig, name):
    """Open the fingers at an inserted cavity pose; report measured release gap."""
    stage = getattr(rig, "_microwave_load_stage", None)
    if not stage or (stage["name"], stage["phase"]) != (name, "inserted"):
        raise SkillFailure(f"microwave release {name}: item is not staged inside the cavity")
    if rig.held is None or rig.held["name"] != name:
        raise SkillFailure(f"microwave release {name}: object is no longer held")
    check_held(rig, "microwave_cavity_release")
    tcp, _ = rig.kin.tcp(rig.q())
    if np.linalg.norm(tcp - stage["targets"][1][0]) > 0.04:
        raise SkillFailure(f"microwave release {name}: hand left insertion pose")
    body, _ = rig.obj_pose(name)
    cavity = stage["cavity"]
    if not (cavity[0] < body[0] < cavity[3] and cavity[1] < body[1] < cavity[4]):
        raise SkillFailure(f"microwave release {name}: object left the cavity")
    actual = rig.grip(stage["pre_open"], 70)
    if float(np.min(actual)) < float(stage["pre_open"]) - 0.005:
        raise SkillFailure(f"microwave release {name}: fingers did not open")
    rig.held = None
    stage["release_body"] = body.copy()
    stage["release_tcp"] = tcp.copy()
    stage["release_base"] = rig.base_pose()
    stage["phase"] = "released"
    rig.log("microwave_released", obj=name, fingers=np.round(actual, 4).tolist())
    return actual


def withdraw_microwave_cavity(rig, name):
    """Withdraw hand/base after release and check that the item settled."""
    stage = getattr(rig, "_microwave_load_stage", None)
    if not stage or (stage["name"], stage["phase"]) != (name, "released"):
        raise SkillFailure(f"microwave withdraw {name}: item has not been released")
    corrected, R, support = stage["targets"], stage["R"], stage["support"]
    tcp, _ = rig.kin.tcp(rig.q())
    if np.linalg.norm(tcp - corrected[1][0]) > 0.05:
        raise SkillFailure(f"microwave withdraw {name}: hand left release pose")
    try:
        rig.move_to(corrected[1][0] + np.array([0, 0, 0.06]), R, step=0.003,
                    label="microwave_release_up", collision=False)
        rig.move_to(corrected[0][0] + np.array([0, 0, 0.06]), R, step=0.004,
                    label="microwave_retreat", collision=False)
    except SkillFailure as e:
        rig.log("retreat_short", reason=str(e))
    # This arm pose cleared the actual open door during loading. Reuse it as
    # the travel pose when coming back to retrieve the bowl after heating.
    rig.microwave_retrieval_q = rig.q_cmd.copy()
    moved = _back_off(rig, dist=0.35)
    rig.log("microwave_load_clear", base=[round(v, 3) for v in rig.base_pose()], reversed_m=round(moved, 3))
    if moved < 0.08:
        raise SkillFailure(f"microwave withdraw {name}: base could not reverse clear of the cavity")
    tcp, _ = rig.kin.tcp(rig.q())
    if tcp[1] >= stage["cavity"][1] - 0.02:
        raise SkillFailure(f"microwave withdraw {name}: hand is still at the cavity opening")
    rig.step(90)
    rig.focus_z = None
    st = rig.state()
    on, why = rig.geo.on(name, support, st)
    pos, _ = rig.obj_pose(name)
    cavity = stage["cavity"]
    inside = all(cavity[i] + 0.005 < pos[i] < cavity[i + 3] - 0.005 for i in range(3))
    from .evaluator import tilt_deg
    tilt = tilt_deg(st["objects"][name]["quat"])
    rig.log("microwave_load_result", obj=name, on_support=bool(on), in_cavity=bool(inside),
            tilt_deg=round(tilt, 1), detail=why)
    if not (on and inside) or tilt > 20:
        raise SkillFailure(f"microwave loading: {name} not settled in cavity ({why}; inside={inside}; tilt={tilt:.0f})")
    rig._microwave_retrieval_stage = dict(stage)
    rig._microwave_load_stage = None
    return True


def place_microwave(rig, name, support):
    """Compose cavity insertion, gripper release, and hand/base withdrawal."""
    insert_microwave_cavity(rig, name, support)
    release_microwave_cavity(rig, name)
    return withdraw_microwave_cavity(rig, name)


def place(rig, name, support, xy=None):
    """Put the held object down.  support = "in:<container>" (dropped from
    just above the rim of deep containers), or a support surface at xy
    (see place_on for choosing xy)."""
    if rig.held is None or rig.held["name"] != name:
        raise SkillFailure(f"place {name}: not holding it")
    if not support.startswith("in:") and rig.ann.support(support).get("furniture") == "kitchen_microwave":
        return place_microwave(rig, name, support)
    if rig.held["kind"] == "edge" and not support.startswith("in:"):
        return place_flat(rig, name, support, xy)
    obj = rig.ann.objects[name]
    asset = rig.ann.asset_of(obj)
    geo = rig.geo
    container = None
    if support.startswith("in:"):
        container = support[3:]
        ca = rig.ann.asset_of(rig.ann.objects[container])
        st = rig.state()
        cb = geo.bottom(container, st)
        rim = ca["container"]["rim_height"]
        # deep containers (toy box, basket): release 3 cm above the rim
        # instead of lowering the wrist between the walls
        drop = rim > 0.12
        floor = cb[2] + (rim + 0.03 if drop else 0.013)
        s = {"name": support, "z": float(floor)}
        c = geo.centre(container, st)
        container_start = np.asarray(rig.obj_pose(container)[0], float)
        xy = (float(c[0]), float(c[1]))
        # drop on the robot's side of the opening, still well inside the walls:
        # the centre of a bin deep on a table is out of reach
        bxy = np.array(rig.base_pose()[:2])
        toward = bxy - np.asarray(c[:2], float)
        if drop and np.linalg.norm(toward) > 1e-6:     # deep bins only: a shallow basket's wall got pushed
            toward /= np.linalg.norm(toward)
            cfp = geo.footprint(container, st)
            inner = 0.5 * min(cfp[2] - cfp[0], cfp[3] - cfp[1]) - 0.015
            osz = rig.ann.asset_of(rig.ann.objects[name])["size"]
            room = inner - 0.5 * math.hypot(osz[0], osz[1]) - 0.02
            if room > 0.01:
                xy = tuple(float(v) for v in np.asarray(c[:2], float) + toward * min(room, 0.5 * inner))
    else:
        s = rig.ann.support(support)
        drop = False
    body_z = s["z"] - asset["origin_to_bottom_center"][2] + 0.006
    if rig.held["kind"] == "corner":          # tilted in the hand: lowest corner 1 cm above
        body_z = s["z"] + rig.held["body_minus_low"] + 0.01
    body = np.array([xy[0], xy[1], body_z])
    off0, R0 = rig.held["tcp_minus_body"], rig.held["R"]
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    park = None
    search_near, q_start, travel_q = rig.base_pose(), rig.q_cmd, _travel_q(rig)
    if math.hypot(search_near[0] - xy[0], search_near[1] - xy[1]) > 1.0:
        # far from the target: rank parks by reach to the target, not by
        # distance from here (all tries were spent near a corner 1.4 m away)
        search_near, q_start = None, None
    if s.get("furniture") == "kitchen_microwave":
        # The refrigerator and microwave are far apart. Ranking microwave
        # parks by distance to the *current* fridge pose exhausts the search
        # before it tests the collision-free loading position beside the oven.
        h = rig.ann.art("kitchen_microwave")["handle"]
        side = np.asarray(h["along"], float)
        front = np.asarray(h["outward"], float)
        near_xy = body[:2] - 0.46 * side[:2] + 0.214 * front[:2]
        side_yaw = math.degrees(math.atan2(-side[1], -side[0])) + 150.0
        search_near = (float(near_xy[0]), float(near_xy[1]), side_yaw)
        # The arm is compacted during the subsequent carry, so its current
        # fridge grasp configuration is not the posture at this park.
        q_start, travel_q = None, None
    shelf_front = None
    if s.get("category") == "cabinet_inside" and s.get("furniture") != "kitchen_microwave":
        # a shelf behind a door: come in horizontally from the open front
        # (a vertical approach from 6 cm above hits the compartment)
        hint = _behind_door_hint(rig, support)
        x0, y0, x1, y1 = s["aabb_xy"]
        centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        a = next((x for x in rig.ann.articulated if x["name"] == s.get("furniture") or
                  support.startswith(x["name"] + "/")), None)
        if a is not None:
            f = np.asarray(a["pivot"][:2], float) - centre
            shelf_front = np.array([np.sign(f[0]), 0.0]) if abs(f[0]) > abs(f[1]) else np.array([0.0, np.sign(f[1])])
            if hint is not None:
                search_near = (float(hint[0] + shelf_front[0] * 0.75), float(hint[1] + shelf_front[1] * 0.75),
                               math.degrees(math.atan2(-shelf_front[1], -shelf_front[0])) + 30.0)
            q_start = None
    clear_z0 = _tallest_near(rig, xy, {name, container} if container else {name}, radius=0.30) \
        if shelf_front is None else None
    st_slots = rig.state()
    open_w = float(rig.held.get("pre_open", 0.04)) if rig.held else 0.04

    def slots_blocked(tcp_p, R_):
        # the open fingers come down beside the object: a neighbour in a
        # finger slot stops the hand above the support (a block placed 1.5 cm
        # from another with the fingers straddling toward it)
        c_ = R_[:, 1]
        for sgn in (1.0, -1.0):
            f_ = tcp_p[:2] + sgn * c_[:2] * (open_w + 0.008)
            for o_ in rig.ann.objects:
                if o_ in (name, container) or o_ not in st_slots["objects"]:
                    continue
                fp_ = rig.geo.footprint(o_, st_slots, 0.008)
                if fp_[0] <= f_[0] <= fp_[2] and fp_[1] <= f_[1] <= fp_[3] and \
                        float(rig.geo.bottom(o_, st_slots)[2]) < tcp_p[2] + 0.02:
                    return o_
        return None
    for psi in np.radians([0, 90, -90, 45, -45, 135, -135, 180]):
        Rz = rz(psi)
        off, R = Rz @ off0, Rz @ R0
        legs = [(body + off + np.array([0, 0, 0.06]), R), (body + off + np.array([0, 0, 0.01]), R)]
        blocker = slots_blocked(body + off, R) if shelf_front is None and not container else None
        if blocker is not None:
            rig.log("place_yaw_slot_blocked", deg=round(math.degrees(psi)), by=blocker)
            continue
        if clear_z0 is not None:
            # pass over the tallest neighbour (a lidded pot beside the burner)
            low0 = body[2] + 0.06 - (body_z - s["z"])
            if clear_z0 + 0.03 > low0:
                legs.insert(0, (legs[0][0] + np.array([0, 0, clear_z0 + 0.03 - low0]), R))
        if shelf_front is not None:
            out = np.r_[shelf_front * 0.16, 0.0]
            legs = [(body + off + out + np.array([0, 0, 0.03]), R), (body + off + np.array([0, 0, 0.03]), R),
                    (body + off + np.array([0, 0, 0.01]), R)]
        if s.get("furniture") == "kitchen_microwave":
            # Approach the opening from in front of the right corner: with a
            # rim-held bowl, the rearward side park brushes the oven back wall.
            park = find_park(rig.kin, rig.world, legs, near=(4.95, 2.18, 165.0),
                             max_tries=1, q_start=None, travel_q=None)
        if park is None:
            park = find_park(rig.kin, rig.world, legs, near=search_near, max_tries=120,
                             q_start=q_start, travel_q=travel_q, path_from=rig.base_pose())
        if park:
            rig.log("place_yaw", deg=round(math.degrees(psi)))
            break
    if park is None and clear_z0 is not None:
        # no base reaches over the tall neighbour: plan the plain approach
        rig.log("place_clearance_dropped", obj=name)
        clear_z0 = None
        for psi in np.radians([0, 90, -90, 45, -45, 135, -135, 180]):
            Rz = rz(psi)
            off, R = Rz @ off0, Rz @ R0
            legs = [(body + off + np.array([0, 0, 0.06]), R), (body + off + np.array([0, 0, 0.01]), R)]
            park = find_park(rig.kin, rig.world, legs, near=search_near, max_tries=120,
                             q_start=q_start, travel_q=travel_q, path_from=rig.base_pose())
            if park:
                rig.log("place_yaw", deg=round(math.degrees(psi)))
                break
    if park is None:
        from .planner import LAST_PARK_DIAG
        raise SkillFailure(f"place {name}: target {tuple(round(v, 2) for v in xy)} on {support} unreachable "
                           f"(rejected: { {k: v for k, v in LAST_PARK_DIAG.items() if v} })")
    x, y, yaw, park_qs = park
    if len(legs) == 3 and shelf_front is None:
        legs, park_qs = legs[1:], park_qs[1:]       # the clearance leg is re-derived after the re-measure
    rig.log("place_park", obj=name, park=[round(x, 3), round(y, 3), round(yaw, 1)])
    rig.caption = f"PLACE {name}: carry"
    rig.focus_z = s["z"]
    # arrive with the load above the target surface: carried lower, it reached
    # the stove's front edge below the hob and scraped on the way up
    # (and above the loose objects already on it: a bowl carried 3 cm over the
    # island top dragged a rolling pin along its edge)
    from .policies.plan_helpers import _carry_bottom_z
    clear_z = None if container or s.get("furniture") == "kitchen_microwave" else _carry_bottom_z(rig, support)
    _goto_park(rig, park, min_bottom_z=s["z"] + 0.15 if s.get("furniture") == "kitchen_microwave"
               else (max(s["z"] + 0.03, clear_z or 0.0) if not container else None))
    rig.kin.coll_kw = {"ignore_fingers": True}
    if s.get("category") == "TableDining" and rig.held["kind"] == "pinch":
        # The compact carry pose can put a bowl below the tabletop. Back the
        # base far enough to leave room for a forward, high wrist pose outside
        # the edge; a diagonal lift through the edge knocks the bowl out.
        base_at_table = rig.base_pose()
        before = float(geo.bottom(name, rig.state())[2])
        if before < s["z"] + 0.08:
            _back_off(rig, dist=0.40)
            if np.linalg.norm(np.asarray(rig.base_pose()[:2]) - np.asarray(base_at_table[:2])) < 0.35:
                raise SkillFailure(f"place {name}: no room to clear the table edge before lifting")
            tcp_lift, R_lift = rig.kin.tcp(rig.q_cmd)
            # A high wrist pose needs forward reach. Extend while the bowl is
            # still outside the table footprint, then lift before coming in.
            forward = tcp_lift.copy()
            forward[0] += 0.20
            rig.move_to(forward, R_lift, step=0.005, steps_per_wp=5,
                        label="table_staging", collision=False)
            check_held(rig, "table_staging")
            tcp_lift, R_lift = rig.kin.tcp(rig.q_cmd)
            bottom = float(geo.bottom(name, rig.state())[2])
            dz = max(0.0, s["z"] + 0.04 - bottom)
            rig.log("table_pre_lift_target", obj=name, bottom_z=round(bottom, 3),
                    target_bottom_z=round(s["z"] + 0.04, 3), tcp=np.round(tcp_lift, 3).tolist())
            rig.move_to(tcp_lift + np.array([0, 0, dz]), R_lift, step=0.005,
                        steps_per_wp=5, label="table_pre_lift", collision=False)
            check_held(rig, "table_pre_lift")
            rig.drive_base([base_at_table], speed=0.15)
            check_held(rig, "table_edge_clear")
    if s.get("furniture") == "kitchen_microwave":
        tcp, R_lift = rig.kin.tcp(rig.q_cmd)
        bottom_z = float(geo.bottom(name, rig.state())[2])
        raise_by = max(0.0, s["z"] + 0.08 - bottom_z)
        if raise_by > 0.01:
            rig.move_to(tcp + np.array([0, 0, raise_by]), R_lift, step=0.005,
                        steps_per_wp=6, label="microwave_pre_lift", collision=False)
            check_held(rig, "microwave_pre_lift")
    # the object may have turned in the pinch on the way (bowls held at the
    # rim, spoons): re-measure how it hangs now and aim its body at xy with its
    # lowest point just above the surface
    tcp_now, R_now = rig.kin.tcp(rig.q())
    body_now, _ = rig.obj_pose(name)
    hang = float(body_now[2] - _lowest_z(rig, name, rig.state()))
    off = (R @ R_now.T) @ (tcp_now - body_now)
    body = np.array([xy[0], xy[1], s["z"] + hang + 0.004])
    new = [(body + off + np.array([0, 0, 0.06]), R), (body + off + np.array([0, 0, 0.01]), R)]
    # the approach waypoint clears whatever stands next to the target (a
    # lidded pot beside a free burner): the carried object must pass over it
    over = None
    if clear_z0 is not None:
        need = clear_z0 + 0.03 - (new[0][0][2] - off[2] - hang)
        if need > 0:
            for k in (1.0, 0.7, 0.4):
                cand = new[0][0] + np.array([0, 0, need * k])
                if rig.kin.ik_global(cand, R, seeds=[rig.q_cmd])[1]:
                    over = cand
                    rig.log("place_above_clearance", obj=name, raised_m=round(float(need * k), 3))
                    break

    if shelf_front is not None:
        new = [(body + off + np.r_[shelf_front * 0.16, 0.0] + np.array([0, 0, 0.03]), R),
               (body + off + np.array([0, 0, 0.03]), R), (body + off + np.array([0, 0, 0.01]), R)]
    moved = float(np.linalg.norm(new[1][0] - legs[1][0]))
    rig.log("place_remeasure", obj=name, shift_m=round(moved, 3), hang_m=round(hang, 3),
            pos=np.round(body_now, 4).tolist(),
            container_pos=(np.round(rig.obj_pose(container)[0], 4).tolist() if container else None))
    hints = park_qs if moved < 0.02 else (None, None)
    planned_legs = legs
    legs = new
    container_exit_pose = None
    if container and drop:
        # At a deep bin the loaded hand can start below the rim after travel.
        # Lift outside the bin first; a direct diagonal to its centre sweeps
        # the carried object through the wall and pushes the bin away.
        current_bottom = float(geo.bottom(name, rig.state())[2])
        rim_z = float(geo.bottom(container, rig.state())[2] + ca["container"]["rim_height"])
        prelift = max(0.0, rim_z + 0.05 - current_bottom)
        if prelift > 0.01:
            tcp_lift, R_lift = rig.kin.tcp(rig.q_cmd)
            rig.move_to(tcp_lift + np.array([0, 0, prelift]), R_lift,
                        step=0.005, steps_per_wp=6, label="container_pre_lift", collision=False)
            check_held(rig, "container_pre_lift")
            rig.log("container_pre_lift_result", obj=name, container=container,
                    bottom_z=round(float(geo.bottom(name, rig.state())[2]), 4),
                    rim_z=round(rim_z, 4),
                    container_pos=np.round(rig.obj_pose(container)[0], 4).tolist())
        exit_position, exit_orientation = rig.kin.tcp(rig.q_cmd)
        container_exit_pose = (exit_position.copy(), exit_orientation.copy())
    st_now = rig.state()
    if not container and float(_lowest_z(rig, name, st_now)) < s["z"] + 0.02 and "aabb_xy" in s:
        # carried below the target surface right at its edge: back away
        # from the surface before rising, or the load scrapes the edge
        x0, y0, x1, y1 = s["aabb_xy"]
        c_now = rig.geo.centre(name, st_now)
        fp_now = rig.geo.footprint(name, st_now)
        # clearance of the load's near edge past each side of the surface
        # (> 0: fully outside on that side); the load is on the side of largest clearance
        clr = {(1.0, 0.0): fp_now[0] - x1, (-1.0, 0.0): x0 - fp_now[2],
               (0.0, 1.0): fp_now[1] - y1, (0.0, -1.0): y0 - fp_now[3]}
        out_key = max(clr, key=lambda k: clr[k])
        out = np.array(out_key)
        need = 0.02 - clr[out_key]                          # distance to move out to clear by 2 cm
        inside = clr[out_key] < 0.0                          # under the surface's footprint
        t_now, R_now = rig.kin.tcp(rig.q_cmd)
        for d in ((min(0.10, max(need, 0.02)), 0.04) if inside else ()):
            try:
                rig.move_to(t_now + np.r_[out * d, 0.0], R_now, step=0.002, steps_per_wp=10,
                            label="place_back_from_edge", smooth=True, collision=False)
                check_held(rig, "place_back_from_edge")
                break
            except SkillFailure as exc:
                if rig.held is None:
                    raise
                rig.log("place_back_from_edge_short", d=d, reason=str(exc))
        t_now, _ = rig.kin.tcp(rig.q_cmd)
        rise_z = over[2] if over is not None else legs[0][0][2]
        mid = np.array([t_now[0], t_now[1], rise_z])
        if rig.kin.ik_global(mid, R, seeds=[rig.q_cmd])[1]:
            rig.move_to(mid, R, step=0.002, steps_per_wp=10, label="place_rise", smooth=True, collision=False)
            check_held(rig, "place_rise")
    if over is not None:
        rig.move_to(over, R, step=0.002, steps_per_wp=10, label="place_over_neighbours", smooth=True, collision=False)
        check_held(rig, "place_over_neighbours")
    import contextlib
    guard = contextlib.nullcontext()
    if container and hasattr(rig.world, "temp_obstacles"):
        # the container itself is not in the arm model: a joint-space fallback
        # to the pose above it swung the forearm through a trash can
        cst = rig.state()
        cfp = geo.footprint(container, cst)
        cz = float(geo.bottom(container, cst)[2])
        guard = rig.world.temp_obstacles([[cfp[0], cfp[1], cz, cfp[2], cfp[3],
                                           cz + float(ca["container"]["rim_height"])]])
    if shelf_front is not None and hints[0] is not None and \
            not rig.kin.cart_path(rig.q_cmd, np.asarray(legs[0][0], float), R, step=0.02)[1]:
        # no straight line into the shelf from the carry pose: a joint-space
        # detour here, beside the open fridge, jammed the arm against it.  Back
        # out, shape the arm into the planned posture in free space, drive in.
        px, py, pyaw = rig.base_pose()
        if _back_off(rig, dist=0.40) > 0.1:
            try:
                rig.sync_world()
                rig.follow(rig.joint_path(np.asarray(hints[0]), "place_preshape"), steps_per_wp=8)
                check_held(rig, "place_preshape")
                rig.drive_base([(px, py, pyaw)], speed=0.08, turn=0.3, ramp=0.8)
                check_held(rig, "place_preshape_in")
                rig.log("place_preshape", obj=name)
            except Dropped:
                raise
            except SkillFailure as exc:
                rig.log("place_preshape_short", reason=str(exc))
                _goto_park(rig, park)
    try:
        with guard:
            # into a container the hand travels down past furniture (a floor bin
            # beside the stove): check the arm against the scene on the way
            err = rig.move_to(legs[0][0], R, step=0.004, steps_per_wp=8, label="place_above", smooth=True,
                              collision=bool(container), q_hint=hints[0])
        if err > 0.03:
            raise SkillFailure(f"place {name}: hand blocked above support ({err:.3f} m)")
    except SkillFailure as e:
        if moved > 0.10 or "no IK" not in str(e):
            raise
        # A rim-held bowl can pivot slightly during the short carry. The
        # original target remains within the wider cavity and has a verified
        # IK branch at this park; use it if the measured correction cannot be
        # reached from the loaded arm configuration.
        rig.log("place_remeasure_fallback", obj=name, reason=str(e))
        legs, hints = planned_legs, park_qs
        rig.move_to(legs[0][0], R, step=0.004, steps_per_wp=8, label="place_above", smooth=True, collision=False,
                    q_hint=hints[0])
    stage_pos, _ = rig.obj_pose(name)
    rig.log("place_after_above", obj=name, pos=np.round(stage_pos, 4).tolist(),
            fingers=np.round(rig.fingers(), 4).tolist(),
            container_pos=(np.round(rig.obj_pose(container)[0], 4).tolist() if container else None))
    check_held(rig, "place_above")
    if shelf_front is not None:
        # slide in horizontally over the shelf, then lower as usual
        hints = tuple(hints) + (None,) * (3 - len(hints))
        rig.move_to(legs[1][0], R, step=0.003, steps_per_wp=8, label="place_insert", smooth=True, collision=False,
                    q_hint=hints[1])
        check_held(rig, "place_insert")
        legs, hints = [legs[0], legs[2]], (hints[0], hints[2])
    if not drop:
        rig.caption = f"PLACE {name}: lower"
        err = rig.move_to(legs[1][0], R, step=0.002, steps_per_wp=8, label="place_lower", smooth=True, collision=False,
                          q_hint=hints[1])
        if err > 0.03:
            raise SkillFailure(f"place {name}: hand blocked at support ({err:.3f} m)")
        rig.step(30)
        stage_pos, _ = rig.obj_pose(name)
        rig.log("place_after_lower", obj=name, pos=np.round(stage_pos, 4).tolist(),
                fingers=np.round(rig.fingers(), 4).tolist())
        check_held(rig, "place_lower")
        if not container:
            # the measured gap under the object decides, not the planned offset:
            # a can let go 5 cm above a fridge shelf tumbled 11 cm away
            gap = float(_lowest_z(rig, name, rig.state())) - float(s["z"])
            if gap > 0.015:
                try:
                    held_vertical_move(rig, -(gap - 0.006), "place_lower_to_contact", step=0.002, allow_pull=False)
                except SkillFailure as exc:
                    if rig.held is None:
                        raise
                    rig.log("place_lower_to_contact_short", gap_m=round(gap, 3), reason=str(exc))
    rig.caption = f"PLACE {name}: release" + (f" into the {container}" if container else "")
    kind = rig.held["kind"]
    before_release, _ = rig.obj_pose(name)
    if container:
        current_container, _ = rig.obj_pose(container)
        shift = float(np.linalg.norm(current_container[:2] - container_start[:2]))
        rig.log("place_container_shift", obj=name, container=container,
                shift_m=round(shift, 4), pos=np.round(current_container, 4).tolist())
        if shift > 0.05:
            raise SkillFailure(f"place {name}: container shifted {shift:.3f} m before release")
    rig.log("place_before_release", obj=name, pos=np.round(before_release, 4).tolist(),
            target=[round(float(v), 4) for v in body])
    rig.grip(rig.held["pre_open"], 70, gradual=True)
    after_open, _ = rig.obj_pose(name)
    rig.log("place_after_open", obj=name, pos=np.round(after_open, 4).tolist(),
            container_pos=(np.round(rig.obj_pose(container)[0], 4).tolist() if container else None))
    top = legs[0][0] if drop else legs[1][0]
    rig.held = None                    # released: a short retreat is not part of the outcome
    tcp, _ = rig.kin.tcp(rig.q_cmd)
    away = np.asarray(rig.base_pose()[:2]) - np.asarray(xy)
    away /= max(1e-9, float(np.linalg.norm(away)))
    retreats = [("place_retreat_up", top + np.array([0, 0, 0.06])),
                ("place_retreat_back", tcp + 0.08 * R[:, 2]),
                ("place_retreat_base", tcp + np.r_[0.08 * away, 0.03])]
    if shelf_front is not None:
        # behind a door: back out horizontally through the opening first (a
        # lift left the hand inside the fridge and the next tuck had no exit)
        retreats = [("place_retreat_out", tcp + np.r_[shelf_front * 0.22, 0.01]),
                    ("place_retreat_out_short", tcp + np.r_[shelf_front * 0.14, 0.01])] + retreats
    errors = []
    for label, target in retreats:
        try:
            rig.move_to(target, R, step=0.004, label=label, smooth=True, collision=False)
            break
        except SkillFailure as e:
            errors.append(str(e))
    else:
        rig.log("retreat_short", reasons=errors)
    if container_exit_pose is not None:
        # The release retreat only clears the object vertically. Return the
        # empty hand to its known outside-of-bin staging position as well, so
        # the next navigation can fold the arm without sweeping the rim.
        exit_target, exit_orientation = container_exit_pose
        try:
            rig.move_to(exit_target, exit_orientation, step=0.005, steps_per_wp=6,
                        label="container_exit", collision=False)
        except SkillFailure as e:
            rig.log("container_exit_short", reason=str(e))
    rig.step(90)
    rig.focus_z = None
    st = rig.state()
    if container:
        ok, why = geo.inside(name, container, st)
        rig.log("place_result", obj=name, container=container, inside=bool(ok), detail=why)
        if not ok:
            raise SkillFailure(f"place {name} in {container}: {why}")
        return True
    p = geo.bottom(name, st)
    err = float(np.linalg.norm(p[:2] - np.asarray(xy)))
    on, why = geo.on(name, support, st)
    rig.log("place_result", obj=name, support=support, xy_err_m=round(err, 4), on_support=bool(on))
    if not on:
        # what is it resting on: the objects next to it
        near = {o: [round(float(v), 3) for v in st["objects"][o]["pos"]] for o in rig.ann.objects
                if o != name and o in st["objects"] and
                np.linalg.norm(np.asarray(st["objects"][o]["pos"][:2]) - p[:2]) < 0.30}
        rig.log("place_not_on_support", obj=name, bottom=[round(float(v), 3) for v in p],
                quat=[round(float(v), 3) for v in st["objects"][name]["quat"]], near=near)
    tol = 0.12 if kind == "corner" else 0.10   # a corner-held object pivots flat on release
    if s.get("category") == "cabinet_inside":
        # inside a fridge/cabinet the hand exits through a narrow opening and
        # nudges the object; resting upright on the shelf is what counts
        tilt = math.degrees(math.acos(float(np.clip(quat_R(st["objects"][name]["quat"])[2, 2], -1.0, 1.0))))
        rig.log("place_shelf_check", obj=name, tilt_deg=round(tilt, 1))
        if on and tilt < 20.0:
            tol = 0.15
    if not (on and err < tol):
        raise SkillFailure(f"place {name}: xy err {err:.3f} m, on support {on} ({why})")
    return True


def free_spots(rig, name, support, hint=None, k=8):
    """Collision-free xy on a support for the object's footprint, near the
    hint (or near an open edge, where the arm reaches), best first."""
    s = rig.ann.support(support)
    st = rig.state()
    asset = rig.ann.asset_of(rig.ann.objects[name])
    size = asset["size"]
    r = 0.5 * math.hypot(size[0], size[1]) + 0.015          # any yaw
    if (asset.get("container") or {}).get("shape") == "round" or any(g.get("round") for g in asset.get("grasps", [])):
        r = 0.5 * max(size[0], size[1]) + 0.015            # round: yaw does not matter
    if s.get("category") == "cabinet_inside":
        # The cavity is narrow. The carried container is held upright, so its
        # actual lateral half-width is more useful than its diagonal radius.
        r = 0.5 * max(size[0], size[1]) + 0.008
        if s.get("furniture") == "kitchen_microwave":
            # The round bowl can safely overhang the flat floor by a few mm.
            # This shifts it left of the low right wall during insertion.
            r = 0.5 * max(size[0], size[1]) - 0.004
    x0, y0, x1, y1 = s["aabb_xy"]
    if x1 - x0 < 2 * r or y1 - y0 < 2 * r:
        r = 0.5 * min(size[0], size[1]) + 0.01
    edges = _open_edges(rig, s) or [np.array(d, float) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    bx, by, _ = rig.base_pose()
    out = []
    if hint is not None:
        # an explicit request is honoured exactly when that point itself is free
        hx, hy = float(hint[0]), float(hint[1])
        re = 0.5 * max(size[0], size[1]) + 0.002          # the object's own half-size, not any-yaw
        re += 0.04 if s.get("category") == "counter" else 0.0   # (off the counter's open edge)
        if x0 + re <= hx <= x1 - re and y0 + re <= hy <= y1 - re and not _overlaps_objects(
                rig, [hx - re, hy - re, hx + re, hy + re, s["z"] + 0.005, s["z"] + size[2]], {name}, st, margin=0.005):
            out.append((-1.0, hx, hy))
    # first keep a finger's clearance to every neighbour (the object stays
    # pickable afterwards), then accept the tight 2 cm margin
    # an explicit hint (swap onto the other's spot, a requested position) is
    # honoured closely: tight margin first; otherwise keep finger clearance first
    # (7 cm first: lowered 4.5 cm from a rolling pin, a rim-held bowl and the
    # hand around it pushed the pin and the bowl came to rest tilted on it)
    first = (0.10,) if asset.get("container") else ()   # the hand wraps a rim-held bowl
    for margin in ((0.02, 0.045) if hint is not None and not str(support).startswith("breakfast_fridge")
                   else first + (0.07, 0.045, 0.02)):
        # 4 cm in from the open edges of a counter: a block left 3 cm from the
        # island edge was knocked off by the robot body driving along it
        ins = 0.04 if s.get("category") == "counter" else 0.0
        for x in np.arange(x0 + r + ins, x1 - r - ins + 1e-6, 0.03):
            for y in np.arange(y0 + r + ins, y1 - r - ins + 1e-6, 0.03):
                box = [x - r, y - r, x + r, y + r, s["z"] + 0.005, s["z"] + size[2]]
                if _overlaps_objects(rig, box, {name}, st, margin=margin):
                    continue
                to_edge = min(_edge_coord(s, n) - float(n @ np.array([x, y])) for n in edges)
                # no hint: prefer spots near the robot (all edge spots score 0 otherwise
                # and the search started in the far corner of a long counter)
                score = (math.hypot(x - hint[0], y - hint[1]) if hint is not None
                         else 0.3 * math.hypot(x - bx, y - by)) + 0.5 * max(0.0, to_edge - 0.2)
                out.append((score, float(x), float(y)))
        if len(out) > (1 if hint is not None and out and out[0][0] < 0 else 0):
            break
    out.sort()
    return [(x, y) for _, x, y in out[:k]]


def place_on(rig, name, support, hint=None, tries=4):
    """Place the held object on a support at the best free spot."""
    if rig.ann.support(support).get("furniture") == "kitchen_microwave":
        return place_microwave(rig, name, support)
    if rig.held is not None and rig.held["kind"] == "edge":
        return place_flat(rig, name, support, hint)
    if hint is None:
        hint = _behind_door_hint(rig, support)
    spots = free_spots(rig, name, support, hint)
    if not spots:
        raise SkillFailure(f"place {name}: no free spot on {support}")
    last = None
    for xy in spots[:tries]:
        try:
            return place(rig, name, support, xy)
        except SkillFailure as e:
            last = e
            rig.log("place_retry", obj=name, xy=[round(v, 3) for v in xy], reason=str(e))
            if rig.held is None:          # released but not where it should be
                raise
    raise last


def _tallest_near(rig, xy, exclude, radius=0.30):
    """Highest top (z) of the objects whose footprint comes within ``radius``
    of xy, or None."""
    st = rig.state()
    best = None
    for o in rig.ann.objects:
        if o in exclude:
            continue
        fp = rig.geo.footprint(o, st)
        d = math.hypot(max(fp[0] - xy[0], 0, xy[0] - fp[2]), max(fp[1] - xy[1], 0, xy[1] - fp[3]))
        if d > radius:
            continue
        top = float(rig.geo.bottom(o, st)[2]) + float(rig.ann.asset_of(rig.ann.objects[o])["size"][2])
        best = top if best is None else max(best, top)
    return best


def _behind_door_hint(rig, support):
    """A shelf behind a hinged door is reachable through the open side only:
    the front corner farthest from the hinge (None for other supports)."""
    furniture = support.split("/", 1)[0]
    a = next((x for x in rig.ann.articulated if x["name"] == furniture and x.get("type") == "revolute"), None)
    if a is None or "/" not in support:
        return None
    x0, y0, x1, y1 = rig.ann.support(support)["aabb_xy"]
    pivot = np.asarray(a["pivot"][:2], float)
    body = a.get("body_aabb")
    centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    front = pivot - centre                     # the hinge sits on the front face
    front = np.array([np.sign(front[0]), 0.0]) if abs(front[0]) > abs(front[1]) else np.array([0.0, np.sign(front[1])])
    corners = [np.array([x, y]) for x in (x0 + 0.08, x1 - 0.08) for y in (y0 + 0.08, y1 - 0.08)]
    corners = [c for c in corners if (c - centre) @ front > 0] or corners
    far = max(corners, key=lambda c: np.linalg.norm(c - pivot))
    # halfway between the shelf centre and the open front corner: in the
    # corner itself the hand meets the side wall
    return tuple(centre + 0.5 * (far - centre))


def place_flat(rig, name, support, hint=None):
    """Edge-held flat object: its gripped edge goes back over a free edge of
    the support (the front of an interior shelf), EDGE_PLACE_OVERHANG past
    it, so the lower finger never ends up between the object and the surface."""
    held = rig.held
    # fingertips at least 3.5 cm past the support edge: real tops reach a bit
    # beyond the annotated edge and a lower finger resting on it gets pinned
    over_p = max(EDGE_PLACE_OVERHANG, held.get("depth", EDGE_GRIP_DEPTH) + 0.035)
    s = rig.ann.support(support)
    st = rig.state()
    h, lat_half = held["h"], held["lat_half"]
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    x0, y0, x1, y1 = s["aabb_xy"]
    bx, by, _ = rig.base_pose()
    cands = []
    open_dirs = [tuple(np.round(d, 3)) for d in _open_edges(rig, s)]
    for n in _open_edges(rig, s):
        lat = _perp(n)
        e = _edge_coord(s, n)
        depth = (x1 - x0) if abs(n[0]) > 0.5 else (y1 - y0)
        if 2 * h - over_p > depth + 0.02:
            continue
        # 4 cm from an end that is closed (a raised side panel, not part of the
        # annotated top, caught a book released at the very end of a bookcase
        # top); 1 cm from an open end, where extra margin only costs reach
        ax = np.array([0.0, 1.0]) if abs(n[0]) > 0.5 else np.array([1.0, 0.0])
        m_lo = 0.01 if tuple(np.round(-ax, 3)) in open_dirs else 0.04
        m_hi = 0.01 if tuple(np.round(ax, 3)) in open_dirs else 0.04
        lo_l = (y0 if abs(n[0]) > 0.5 else x0) + lat_half + m_lo
        hi_l = (y1 if abs(n[0]) > 0.5 else x1) - lat_half - m_hi
        for l in np.arange(lo_l, hi_l + 1e-6, 0.03) if hi_l >= lo_l else []:
            edge_pt = n * e + np.abs(lat) * l
            c = edge_pt - n * (h - over_p)
            half = np.abs(n) * h + np.abs(lat) * lat_half
            # free where it is released and where it is pushed to afterwards
            c_in = c - n * (over_p + 0.01)
            box = [min(c[0], c_in[0]) - half[0], min(c[1], c_in[1]) - half[1],
                   max(c[0], c_in[0]) + half[0], max(c[1], c_in[1]) + half[1], s["z"] + 0.005, s["z"] + size[2]]
            if _overlaps_objects(rig, box, {name}, st, margin=0.02):
                continue
            score = math.hypot(c[0] - hint[0], c[1] - hint[1]) if hint is not None else \
                0.3 * math.hypot(c[0] - bx, c[1] - by)
            if "bookcase" in str(s.get("category", "")).lower():
                # on shelving: the long (front) edge, away from its ends (a book
                # slid in over the short side / next to a side panel stalled)
                edge_len = (y1 - y0) if abs(n[0]) > 0.5 else (x1 - x0)
                score += 0.5 * abs(l - 0.5 * (lo_l + hi_l))
                if edge_len < 0.8 * max(x1 - x0, y1 - y0):
                    score += 0.4
            cands.append((score, n, c))
    cands.sort(key=lambda t: t[0])
    if not cands:
        raise SkillFailure(f"place {name}: no free edge spot on {support}")
    R0 = held["R"]
    a0 = -R0[:, 2]
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    start, attempts = 0, 0
    while True:
        park = None
        for idx in range(start, min(len(cands), start + 6)):
            _, n, c = cands[idx]
            n3 = np.r_[n, 0.0]
            psi = math.atan2(-n[1], -n[0]) - math.atan2(a0[1], a0[0])
            R = rz(psi) @ R0
            tcp = np.r_[c + n * (h - held["depth"]), s["z"] + held["dz"] + 0.004]
            legs = [(tcp + n3 * 0.10 + np.array([0, 0, 0.04]), R), (tcp + np.array([0, 0, 0.02]), R), (tcp, R)]
            retreat = tcp + n3 * 0.10
            face = math.degrees(math.atan2(-n[1], -n[0]))

            def square(x, y, yaw, qs, face=face):
                # facing the edge squarely: from 15 deg off, another link caught
                # the book during the release push and flipped it off the shelf
                return -abs((yaw - face + 180.0) % 360.0 - 180.0)
            park = find_park(rig.kin, rig.world, legs + [(retreat, R)], near=rig.base_pose(), max_tries=120,
                             q_start=rig.q_cmd, travel_q=_travel_q(rig), score=square, n_best=5)
            if park:
                break
        if park is None:
            raise SkillFailure(f"place {name}: no reachable edge spot on {support}")
        rig.log("place_flat_park", obj=name, support=support, centre=[round(v, 3) for v in c],
                park=[round(v, 3) for v in park[:3]])
        rig.caption = f"PLACE {name}: carry to the {s.get('category', 'support')} edge"
        rig.focus_z = s["z"]
        _goto_park(rig, park)
        rig.kin.coll_kw = {"ignore_fingers": True}
        # an edge-held book turns down in the pinch during the carry (7 cm of
        # droop dropped it in front of the shelf): level it with the wrist
        st_lv = rig.state()
        bz = quat_R(st_lv["objects"][name]["quat"])[:, 2]
        bz = bz if bz[2] >= 0 else -bz
        droop = math.degrees(math.acos(float(np.clip(bz[2], -1.0, 1.0))))
        if droop > 6.0:
            ax = np.cross(bz, [0.0, 0.0, 1.0])
            R_fix = Rotation.from_rotvec(ax / max(1e-9, np.linalg.norm(ax)) * math.radians(droop)).as_matrix()
            legs2 = [(lp, R_fix @ lR) for lp, lR in legs]
            if all(rig.kin.ik_global(lp, lR, seeds=[park[3][0]])[1] for lp, lR in legs2):
                legs = legs2
                R = R_fix @ R
                rig.log("flat_level", obj=name, droop_deg=round(droop, 1))
        rig.move_to(*legs[0], step=0.01, label="flat_pre", q_hint=park[3][0] if droop <= 6.0 else None)
        # the book may hang lower in the pinch than when it was picked (droop
        # during the carry): slide in with its lowest point 1 cm above the surface
        st_now = rig.state()
        t_now, _ = rig.kin.tcp(rig.q_cmd)
        sag = float(t_now[2] - _lowest_z(rig, name, st_now))
        need = s["z"] + 0.01 + sag - float(legs[1][0][2])
        if need > 0.002:
            legs = [legs[0], (legs[1][0] + np.array([0, 0, need]), legs[1][1]), legs[2]]
            rig.log("flat_over_raised", obj=name, raised_m=round(need, 3))
        rig.caption = f"PLACE {name}: slide in over the surface"
        rig.move_to(*legs[1], step=0.004, steps_per_wp=4, label="flat_over", collision=False)
        err = float(np.linalg.norm(rig.kin.tcp(rig.q())[0] - legs[1][0]))
        if err < 0.02 or attempts >= 2 or rig.held is None:
            break
        # the book caught on the shelf (side panel / a neighbour): back out
        # and use the next free spot
        rig.log("flat_over_blocked", obj=name, err_m=round(err, 3), centre=[round(v, 3) for v in c])
        rig.move_to(*legs[0], step=0.004, label="flat_back_out", collision=False)
        check_held(rig, "flat_back_out")
        # skip spots within 8 cm of the blocked one (3 cm steps along the edge)
        cands = cands[:idx + 1] + [t for t in cands[idx + 1:] if np.linalg.norm(t[2] - c) > 0.08]
        start, attempts = idx + 1, attempts + 1
    rig.move_to(*legs[2], step=0.002, steps_per_wp=6, label="flat_lower", collision=False)
    rig.step(30)
    rig.caption = f"PLACE {name}: release, pull the hand out"
    rig.grip(0.04, 70)
    rig.held = None
    # the open pads drag the object back out with them: drop the hand 1.5 cm
    # (frees the lower finger pinned under the overhang; the upper pad still
    # clears the top), back out, then push the object fully onto the surface
    # with the closed fingertips (gripped edge ends 1 cm inside the support edge)
    up = tcp - np.array([0, 0, 0.015])
    out = up + n3 * 0.10
    low = np.r_[out[:2], s["z"] + size[2] / 2]
    push_end = np.r_[(tcp + n3 * (held["depth"] - over_p - 0.01))[:2], low[2]]
    try:
        rig.move_to(up, R, step=0.003, steps_per_wp=4, label="flat_release_down", collision=False)
        rig.move_to(out, R, step=0.004, label="flat_retreat", collision=False)
        rig.grip(0.0, 40)
        rig.caption = f"PLACE {name}: push it fully onto the surface"
        rig.move_to(low, R, step=0.004, label="flat_push_down", collision=False)
        rig.move_to(push_end, R, step=0.003, steps_per_wp=4, label="flat_push", collision=False)
        rig.move_to(push_end + n3 * 0.12 + np.array([0, 0, 0.06]), R, step=0.01, label="flat_up", collision=False)
    except SkillFailure as e:
        rig.log("retreat_short", reason=str(e))
    rig.step(90)
    rig.focus_z = None
    st = rig.state()
    on, why = rig.geo.on(name, support, st)
    from .evaluator import tilt_deg
    tilt = tilt_deg(st["objects"][name]["quat"])
    rig.log("place_result", obj=name, support=support, on_support=bool(on), tilt_deg=round(tilt, 1), detail=why)
    if not on or tilt > 20:
        raise SkillFailure(f"place {name} on {support}: {why}, tilt {tilt:.0f} deg")
    return True


def _microwave_start_food(rig, name):
    """Check the closed door, thermal task state, and food inside the cavity."""
    a = rig.ann.art(name)
    if rig.thermal is None:
        raise SkillFailure("microwave: thermal task state is not configured")
    if abs(rig.joint(name) - a["closed_q"]) > 0.10:
        raise SkillFailure("microwave: door must be closed before heating")
    b = a["cavity_aabb"]
    inside = []
    for obj in rig.thermal.config:
        p, _ = rig.obj_pose(obj)
        if all(b[i] + 0.005 < p[i] < b[i + 3] - 0.005 for i in range(3)):
            inside.append(obj)
    if not inside:
        raise SkillFailure("microwave: no task food is inside the cavity")
    return inside


def _microwave_button_targets(rig, name, button):
    if button not in ("door", "start"):
        raise ValueError(f"microwave: unknown button {button!r}")
    spec = rig.ann.art(name).get(f"{button}_button")
    if spec is None:
        raise SkillFailure(f"microwave: no annotated {button} button")
    p = np.asarray(spec["center"], float)
    outward = np.asarray(spec["outward"], float)
    R = gripper_rot(-outward, [1.0, 0.0, 0.0])
    return p + outward * 0.12, p + outward * 0.005, R, p


def approach_microwave_button(rig, name="kitchen_microwave", button="door"):
    """Park and align closed fingertips in front of an annotated button."""
    if rig.held is not None:
        raise SkillFailure("microwave button: release the held object first")
    if button == "start":
        _microwave_start_food(rig, name)
    pre, contact, R, center = _microwave_button_targets(rig, name, button)
    targets = [(pre + np.array([0, 0, 0.06]), R), (pre, R)]
    rig._microwave_button_stage = None
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    preferred = (float(center[0] - 0.1165), float(center[1] - 0.5163), 75.0)
    park = find_park(rig.kin, rig.world, targets, near=preferred,
                     max_tries=1, q_start=None, travel_q=rig.kin.rest)
    if park is not None and button == "start":
        rig.kin.set_base((park[0], park[1], 0.0), math.radians(park[2]))
        scene, rig.kin.scene = rig.kin.scene, None
        try:
            _, contact_ok = rig.kin.cart_path(park[3][-1], contact, R, 0.005)
        finally:
            rig.kin.scene = scene
        if not contact_ok:
            park = None
    if park is None:
        park = find_park(rig.kin, rig.world, targets, near=rig.base_pose(),
                         max_tries=160, q_start=rig.q_cmd, travel_q=rig.kin.rest)
    if park is None:
        raise SkillFailure(f"microwave: no collision-free reach to {button} button")
    _goto_park(rig, park)
    if button == "door":
        rig.caption = "OPEN microwave: press door control"
    rig.grip(0.0, 40)
    prefix = "microwave_door_button" if button == "door" else "microwave_button"
    rig.move_to(*targets[0], label=prefix + "_pre", q_hint=park[3][0])
    rig.move_to(*targets[1], step=0.005, label=prefix + "_align", collision=False)
    tcp, _ = rig.kin.tcp(rig.q())
    error = float(np.linalg.norm(tcp - pre))
    if error > 0.04:
        raise SkillFailure(f"microwave: {button} button alignment missed by {error:.3f} m")
    rig._microwave_button_stage = {"name": name, "button": button, "phase": "aligned",
                                   "pre": pre, "contact": contact, "R": R}
    rig.log("microwave_button_aligned", button=button, error_m=round(error, 4))
    return error


def press_aligned_microwave_button(rig, name="kitchen_microwave", button="door"):
    """Move from an aligned pose into contact and check measured TCP error."""
    stage = getattr(rig, "_microwave_button_stage", None)
    if not stage or (stage["name"], stage["button"], stage["phase"]) != (name, button, "aligned"):
        raise SkillFailure(f"microwave: {button} button is not aligned")
    if rig.held is not None:
        raise SkillFailure("microwave button: release the held object first")
    tcp, _ = rig.kin.tcp(rig.q())
    if np.linalg.norm(tcp - stage["pre"]) > 0.04:
        raise SkillFailure(f"microwave: {button} button alignment is stale")
    inside = _microwave_start_food(rig, name) if button == "start" else None
    prefix = "microwave_door_button" if button == "door" else "microwave_button"
    rig.move_to(stage["contact"], stage["R"], step=0.003, label=prefix + "_press", collision=False)
    rig.step(24)
    tcp, _ = rig.kin.tcp(rig.q())
    distance = float(np.linalg.norm(tcp - stage["contact"]))
    if distance > 0.035:
        raise SkillFailure(f"microwave: {button} button press missed by {distance:.3f} m")
    if button == "start":
        rig.thermal.active = True
        rig.log("microwave_start", food=inside, button_error_m=round(distance, 4))
    else:
        rig.log("microwave_door_button", button_error_m=round(distance, 4))
    stage["phase"] = "pressed"
    return distance


def retract_microwave_button(rig, name="kitchen_microwave", button="door"):
    """Withdraw fingertips from a pressed button and check the retreat pose."""
    stage = getattr(rig, "_microwave_button_stage", None)
    if not stage or (stage["name"], stage["button"], stage["phase"]) != (name, button, "pressed"):
        raise SkillFailure(f"microwave: {button} button has not been pressed")
    tcp, _ = rig.kin.tcp(rig.q())
    if np.linalg.norm(tcp - stage["contact"]) > 0.04:
        raise SkillFailure(f"microwave: {button} button press pose is stale")
    prefix = "microwave_door_button" if button == "door" else "microwave_button"
    rig.move_to(stage["pre"], stage["R"], step=0.005, label=prefix + "_release", collision=False)
    tcp, _ = rig.kin.tcp(rig.q())
    error = float(np.linalg.norm(tcp - stage["pre"]))
    if error > 0.04:
        raise SkillFailure(f"microwave: {button} button retreat missed by {error:.3f} m")
    rig._microwave_button_stage = None
    rig.log("microwave_button_retracted", button=button, error_m=round(error, 4))
    return error


def press_microwave_start(rig, name="kitchen_microwave"):
    """Compose approach, physical start press, and fingertip withdrawal."""
    approach_microwave_button(rig, name, "start")
    press_aligned_microwave_button(rig, name, "start")
    retract_microwave_button(rig, name, "start")
    return True


def _press_microwave_door_control(rig, name):
    """Compose approach, physical door-control press, and withdrawal."""
    approach_microwave_button(rig, name, "door")
    press_aligned_microwave_button(rig, name, "door")
    retract_microwave_button(rig, name, "door")
    return True


def clear_microwave_door_sweep(rig, name="kitchen_microwave"):
    """Move an empty or loaded robot to the existing hinge-clearance pose."""
    rig._microwave_clear = None
    target = (5.1, 1.6, 150.0)
    navigate(rig, target)
    x, y, yaw = rig.base_pose()
    if math.hypot(x - target[0], y - target[1]) > 0.05 or abs((yaw - target[2] + 180) % 360 - 180) > 5:
        raise SkillFailure("microwave hinge: base did not reach clearance pose")
    if rig.held is None:
        q = rig.q()
        if min(np.max(np.abs(q - rig.kin.rest)), np.max(np.abs(q))) > 0.07:
            rig.tuck()                     # the arm can be left half-folded after a place
            q = rig.q()
            if min(np.max(np.abs(q - rig.kin.rest)), np.max(np.abs(q))) > 0.07:
                raise SkillFailure("microwave hinge: arm is not tucked")
    else:
        check_held(rig, "microwave_door_clear")
    rig._microwave_clear = {"name": name, "held": rig.held["name"] if rig.held else None}
    rig.log("microwave_sweep_clear", base=[round(x, 3), round(y, 3), round(yaw, 3)])
    return (x, y, yaw)


def _set_microwave_hinge(rig, name, target, caption):
    """Drive the physical hinge only after the robot has cleared its sweep."""
    clear = getattr(rig, "_microwave_clear", None)
    if not isinstance(clear, dict) or clear.get("name") != name:
        raise SkillFailure("microwave hinge: clear the door sweep before driving the hinge")
    held_name = rig.held["name"] if rig.held else None
    if held_name != clear["held"]:
        raise SkillFailure("microwave hinge: grasp state changed after clearance")
    if rig.held is None:
        q = rig.q()
        if min(np.max(np.abs(q - rig.kin.rest)), np.max(np.abs(q))) > 0.07:
            raise SkillFailure("microwave hinge: arm left its tucked pose")
    else:
        check_held(rig, "microwave_hinge_drive")
    x, y, yaw = rig.base_pose()
    if math.hypot(x - 5.1, y - 1.6) > 0.05 or abs((yaw - 150.0 + 180) % 360 - 180) > 5:
        raise SkillFailure("microwave hinge: robot left the clearance pose")
    rig._microwave_clear = None
    from isaacsim.core.utils.types import ArticulationAction
    motor = rig._arts[name]
    start = rig.joint(name)
    previous_camera = rig.camera_override
    rig.camera_override = ([4.78, 1.44, 1.42], [4.5, 2.5, 0.94])
    try:
        rig.caption = caption
        for i in range(1, 301):
            q = start + (target - start) * i / 300
            motor.apply_action(ArticulationAction(joint_positions=rig.torch.tensor([q], dtype=rig.torch.float32),
                                                  joint_indices=rig.torch.tensor([rig._dof[name]])))
            rig.step(1)
        rig.step(120)
        actual = rig.joint(name)
        rig.log("microwave_door_motion", target=round(target, 3), actual=round(actual, 3))
        if abs(actual - target) > 0.10:
            raise SkillFailure(f"microwave: powered door stopped at {actual:.3f}, target {target:.3f}")
    finally:
        rig.camera_override = previous_camera
    return actual


def open_microwave_door(rig, name="kitchen_microwave"):
    """Press the door release and open the powered physical hinge."""
    a = rig.ann.art(name)
    q = rig.joint(name)
    if abs(q - a["open_q"]) <= 0.10:
        return q
    if abs(q - a["closed_q"]) > 0.10:
        raise SkillFailure(f"microwave: door is neither closed nor open ({q:.3f})")
    _press_microwave_door_control(rig, name)
    clear_microwave_door_sweep(rig, name)
    return _set_microwave_hinge(rig, name, a["open_q"], "OPEN microwave: powered door")


def close_microwave_door(rig, name="kitchen_microwave"):
    """Move clear and close the powered physical hinge."""
    a = rig.ann.art(name)
    q = rig.joint(name)
    if abs(q - a["closed_q"]) <= 0.10:
        return q
    clear_microwave_door_sweep(rig, name)
    return _set_microwave_hinge(rig, name, a["closed_q"], "CLOSE microwave: powered door")


def cycle_microwave_door(rig, name="kitchen_microwave"):
    """Composite demonstration: open, then close the powered microwave door."""
    a = rig.ann.art(name)
    if abs(rig.joint(name) - a["closed_q"]) > 0.10:
        raise SkillFailure("microwave: door must begin closed for inspection")
    open_microwave_door(rig, name)
    close_microwave_door(rig, name)
    return True
