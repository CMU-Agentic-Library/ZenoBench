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
    tcp, R = rig.kin.tcp(rig.q_cmd)
    rig.kin.coll_kw = {"ignore_fingers": True}
    hang = max(0.0, tcp[2] - float(rig.geo.bottom(rig.held["name"], rig.state())[2]))
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
    for lx, ly, z in ((0.35, -0.10, tcp[2]), (0.35, -0.10, 0.6), (0.40, -0.25, tcp[2])):
        w = np.array([x + c * lx - s * ly, y + s * lx + c * ly, z])
        try:
            rig.move_to(w, R, step=0.01, steps_per_wp=4, label="carry_in")
            return
        except SkillFailure:
            continue


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
    if slip > 0.05 or f.min() < 0.002:
        rig.log("dropped", obj=h["name"], during=label, slip_m=round(slip, 3), fingers=f.round(4).tolist(),
                at=[round(float(v), 3) for v in body])
        rig.held = None
        rig.grip(0.04, 20)
        raise Dropped(f"{label}: {h['name']} slipped out of the hand while carrying it")


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


def check_left_held(rig, label):
    """Verify a left-hand load after motion using finger gap and TCP distance."""
    h = rig.left_held
    if h is None:
        return
    tcp, _ = rig.left_kin.tcp(rig.left_q())
    body, _ = rig.obj_pose(h["name"])
    slip = abs(float(np.linalg.norm(tcp-body))-float(np.linalg.norm(h["tcp_minus_body"])))
    fingers = rig.left_fingers()
    if slip > 0.06 or fingers.min() < 0.002:
        rig.log("left_dropped", obj=h["name"], during=label, slip_m=round(slip, 3),
                fingers=fingers.round(4).tolist())
        rig.left_held = None
        raise Dropped(f"{label}: {h['name']} slipped from the left hand")


def navigate(rig, pose, label="navigate", min_bottom_z=None):
    """Tuck (or carry the held object), plan an A* path, drive (slower and
    with gentler turns while carrying)."""
    if rig.held is None:
        if not rig.tuck():
            raise SkillFailure(f"{label}: cannot fold the arm without hitting something")
    else:
        # reverse out first: lifting straight up next to furniture can hit
        # whatever stands on it (the TV on the TV stand knocked objects out)
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

    def score(x, y, yaw, qs):
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
        q0 = q_now
        rig.sync_world()
        p, R, appr, targets = _handle_targets(rig, a, q0, flip, tilt, grasp)
        park = find_park(rig.kin, rig.world, targets, near=rig.base_pose(), q_start=rig.q_cmd,
                         ride=_ride_check(rig, a, q0, goal), score=score, n_best=5)
        if park is None:
            raise SkillFailure(f"{verb} {name}: part moved to {q0:.3f} and no base pose reaches it now")
        _goto_park(rig, park)
        park_qs = park[3]
    rig.caption = f"{verb.upper()} {a['category']}: grasp handle ({'side hook' if grasp == 'side' else 'front pinch'})"
    # a bar close to its panel (PartNet handles, ~3 cm gap): open only as far as
    # keeps the inner pad between panel and bar
    pre_open = a["handle"].get("pre_open", 0.04)
    t = a["handle"].get("thickness", 0.025)
    if grasp == "front":                  # the fingers straddle the bar across its width
        t = float(np.abs(np.asarray(a["handle"]["bar_size"], float)) @ np.abs(np.asarray(a["handle"]["along"], float)))
        pre_open = min(0.04, t / 2 + 0.015)
    rig.grip(pre_open, 30)
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


def open_articulated(rig, name, goal=None):
    a = rig.ann.art(name)
    return _move_articulated(rig, name, a["open_q"] if goal is None else goal, "open")


def close_articulated(rig, name):
    a = rig.ann.art(name)
    return _move_articulated(rig, name, a["closed_q"], "close")


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
    return [(p - 0.08 * appr + np.array([0, 0, 0.04]), g["R"]), (p - 0.04 * appr, g["R"]), (p, g["R"])]


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
    obj = rig.ann.objects[name]
    pos, quat = rig.obj_pose(name)
    st = rig.state()
    floor_z = float(rig.geo.bottom(name, st)[2])
    cands = rig.ann.grasp_poses(obj, pos, quat, kinds=kinds)
    if not cands:
        raise SkillFailure(f"pick {name}: no pinch grasp annotated")
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
        cands.sort(key=lambda g: np.linalg.norm(g["p"][:2] - np.array([bx, by])))
    park, g = None, None
    for g in cands[:max_candidates]:
        lift = [(g["p"] + np.array([0, 0, 0.07]), g["R"])]
        park = find_park(rig.kin, rig.world, _grasp_legs(g) + lift, near=search_near,
                         max_tries=1 if in_microwave and retrieval_q is not None else 60 if in_microwave else 120,
                         q_start=retrieval_q if in_microwave and retrieval_q is not None else
                                 None if in_microwave or fridge_shelf else rig.q_cmd,
                         travel_q=None if in_microwave and retrieval_q is not None else _travel_q(rig))
        if park:
            break
    if park is None:
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
    rig.grip(g["pre_open"], 40)
    for (tp, tR), lab, st_, spw, qh in zip(_grasp_legs(g), ("pre_far", "pre", "grasp"), (0.02, 0.005, 0.003),
                                           (3, 3, 4), park_qs):
        err = rig.move_to(tp, tR, step=st_, steps_per_wp=spw, label=f"pick_{lab}", q_hint=qh, smooth=True)
    if err > 0.008:                     # round objects pop out of an off-centre pinch
        rig.move_to(g["p"], g["R"], step=0.002, steps_per_wp=6, label="pick_grasp_fix", collision=False, smooth=True)
    rig.caption = f"PICK {name}: close gripper"
    rig.grip(0.0, 120, gradual=True)
    rig.caption = f"PICK {name}: lift"
    rig.move_to(g["p"] + np.array([0, 0, 0.07]), g["R"], step=0.002, steps_per_wp=6, label="pick_lift",
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
    R = gripper_rot([0, 0, -1.0], [lat[0], lat[1], 0.0])
    z = s["z"] + 0.03                   # pad bottom ~5 mm above the surface
    while moved < distance - 0.01 and (enough is None or moved < enough):
        st = rig.state()
        b = geo.bottom(name, st)
        h = _half_along(size, _yaw(st["objects"][name]["quat"]), n)
        d = min(PUSH_SEG, distance - moved)
        start = b[:2] - n * (h + 0.035)
        push_legs = [(np.r_[start, z + 0.10], R), (np.r_[start, z], R), (np.r_[start + n * (d + 0.025), z], R),
                     (np.r_[start + n * (d + 0.025), z + 0.10], R)]
        # Drag with the closed fingertips pressing into the top near the leading
        # rim. The TCP is about 2 cm above the pad tip; a higher target only
        # brushes the object and produces no measurable drag.
        # used when nothing can reach behind the object (back of a counter)
        top = b[2] + size[2] - 0.004 + 0.010
        grab = b[:2] + n * max(0.0, h - 0.03)
        drag_travel = d + 0.025  # fingertip skid: compensate with measured-motion loop
        drag_legs = [(np.r_[grab, top + 0.08], R), (np.r_[grab, top], R),
                     (np.r_[grab + n * drag_travel, top], R),
                     (np.r_[grab + n * drag_travel, top + 0.08], R)]
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        park, selected_mode = None, None
        candidates = (("push", push_legs), ("drag", drag_legs))
        for candidate_mode, legs in candidates:
            if mode is not None and candidate_mode != mode:
                continue
            park = find_park(rig.kin, rig.world, legs, near=rig.base_pose(), max_tries=150, q_start=rig.q_cmd,
                             travel_q=_travel_q(rig))
            if park is not None:
                selected_mode = candidate_mode
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
        if step_moved < 0.01:
            raise SkillFailure(f"push {name}: object did not move")
    rig.focus_z = None
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
    b = geo.bottom(name, st)
    yaw = _yaw(st["objects"][name]["quat"])
    cands = []
    for k in range(4):                                  # the four sides of the object
        n = np.array([math.cos(yaw + k * math.pi / 2), math.sin(yaw + k * math.pi / 2)])
        h = _half_along(size, yaw, n)
        # lower pad on the side face 1.6 cm up (its open tip would touch the
        # floor at the very edge), upper pad on the top face d further in
        low = np.r_[b[:2] + n * (h + 0.003), 0.016]
        up = np.r_[b[:2] + n * (h - d), t]
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
    rig.move_to(*legs[2], step=0.003, steps_per_wp=4, label="corner_grasp", collision=False)
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
        raise SkillFailure(f"microwave loading: held {name} shifted {shift:.3f} m and entry is blocked")
    rig.caption = f"PLACE {name}: enter microwave from front"
    for (point, orient), label, step, hint in zip(corrected,
                                                   ("microwave_front", "microwave_insert"),
                                                   (0.005, 0.003), replanned[3]):
        rig.move_to(point, orient, step=step, steps_per_wp=6, label=label, q_hint=hint)
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
        xy = (float(c[0]), float(c[1]))
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
    for psi in np.radians([0, 90, -90, 45, -45, 135, -135, 180]):
        Rz = rz(psi)
        off, R = Rz @ off0, Rz @ R0
        legs = [(body + off + np.array([0, 0, 0.06]), R), (body + off + np.array([0, 0, 0.01]), R)]
        if s.get("furniture") == "kitchen_microwave":
            # Approach the opening from in front of the right corner: with a
            # rim-held bowl, the rearward side park brushes the oven back wall.
            park = find_park(rig.kin, rig.world, legs, near=(4.95, 2.18, 165.0),
                             max_tries=1, q_start=None, travel_q=None)
        if park is None:
            park = find_park(rig.kin, rig.world, legs, near=search_near, max_tries=120,
                             q_start=q_start, travel_q=travel_q)
        if park:
            rig.log("place_yaw", deg=round(math.degrees(psi)))
            break
    if park is None:
        raise SkillFailure(f"place {name}: target {tuple(round(v, 2) for v in xy)} on {support} unreachable")
    x, y, yaw, park_qs = park
    rig.log("place_park", obj=name, park=[round(x, 3), round(y, 3), round(yaw, 1)])
    rig.caption = f"PLACE {name}: carry"
    rig.focus_z = s["z"]
    _goto_park(rig, park, min_bottom_z=s["z"] + 0.15 if s.get("furniture") == "kitchen_microwave" else None)
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
    moved = float(np.linalg.norm(new[1][0] - legs[1][0]))
    rig.log("place_remeasure", obj=name, shift_m=round(moved, 3), hang_m=round(hang, 3),
            pos=np.round(body_now, 4).tolist())
    hints = park_qs if moved < 0.02 else (None, None)
    planned_legs = legs
    legs = new
    try:
        err = rig.move_to(legs[0][0], R, step=0.004, steps_per_wp=8, label="place_above", smooth=True, collision=False,
                          q_hint=hints[0])
        if err > 0.03:
            raise SkillFailure(f"place {name}: hand blocked above support ({err:.3f} m)")
    except SkillFailure as e:
        if s.get("furniture") != "kitchen_microwave" or moved > 0.10 or "no IK" not in str(e):
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
            fingers=np.round(rig.fingers(), 4).tolist())
    check_held(rig, "place_above")
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
    rig.caption = f"PLACE {name}: release" + (f" into the {container}" if container else "")
    kind = rig.held["kind"]
    before_release, _ = rig.obj_pose(name)
    rig.log("place_before_release", obj=name, pos=np.round(before_release, 4).tolist(),
            target=[round(float(v), 4) for v in body])
    rig.grip(rig.held["pre_open"], 70, gradual=True)
    after_open, _ = rig.obj_pose(name)
    rig.log("place_after_open", obj=name, pos=np.round(after_open, 4).tolist())
    top = legs[0][0] if drop else legs[1][0]
    rig.held = None                    # released: a short retreat is not part of the outcome
    tcp, _ = rig.kin.tcp(rig.q_cmd)
    away = np.asarray(rig.base_pose()[:2]) - np.asarray(xy)
    away /= max(1e-9, float(np.linalg.norm(away)))
    retreats = [("place_retreat_up", top + np.array([0, 0, 0.06])),
                ("place_retreat_back", tcp + 0.08 * R[:, 2]),
                ("place_retreat_base", tcp + np.r_[0.08 * away, 0.03])]
    errors = []
    for label, target in retreats:
        try:
            rig.move_to(target, R, step=0.004, label=label, smooth=True, collision=False)
            break
        except SkillFailure as e:
            errors.append(str(e))
    else:
        rig.log("retreat_short", reasons=errors)
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
    tol = 0.12 if kind == "corner" else 0.10   # a corner-held object pivots flat on release
    if not (on and err < tol):
        raise SkillFailure(f"place {name}: xy err {err:.3f} m, on support {on} ({why})")
    return True


def free_spots(rig, name, support, hint=None, k=8):
    """Collision-free xy on a support for the object's footprint, near the
    hint (or near an open edge, where the arm reaches), best first."""
    s = rig.ann.support(support)
    st = rig.state()
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    r = 0.5 * math.hypot(size[0], size[1]) + 0.015          # any yaw
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
    out = []
    for x in np.arange(x0 + r, x1 - r + 1e-6, 0.03):
        for y in np.arange(y0 + r, y1 - r + 1e-6, 0.03):
            box = [x - r, y - r, x + r, y + r, s["z"] + 0.005, s["z"] + size[2]]
            if _overlaps_objects(rig, box, {name}, st, margin=0.02):
                continue
            to_edge = min(_edge_coord(s, n) - float(n @ np.array([x, y])) for n in edges)
            score = (math.hypot(x - hint[0], y - hint[1]) if hint is not None else 0.0) + 0.5 * max(0.0, to_edge - 0.2)
            out.append((score, float(x), float(y)))
    out.sort()
    return [(x, y) for _, x, y in out[:k]]


def place_on(rig, name, support, hint=None, tries=4):
    """Place the held object on a support at the best free spot."""
    if rig.ann.support(support).get("furniture") == "kitchen_microwave":
        return place_microwave(rig, name, support)
    if rig.held is not None and rig.held["kind"] == "edge":
        return place_flat(rig, name, support, hint)
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
    for n in _open_edges(rig, s):
        lat = _perp(n)
        e = _edge_coord(s, n)
        depth = (x1 - x0) if abs(n[0]) > 0.5 else (y1 - y0)
        if 2 * h - over_p > depth + 0.02:
            continue
        lo_l = (y0 if abs(n[0]) > 0.5 else x0) + lat_half + 0.01
        hi_l = (y1 if abs(n[0]) > 0.5 else x1) - lat_half - 0.01
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
            cands.append((score, n, c))
    cands.sort(key=lambda t: t[0])
    if not cands:
        raise SkillFailure(f"place {name}: no free edge spot on {support}")
    R0 = held["R"]
    a0 = -R0[:, 2]
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    park = None
    for _, n, c in cands[:6]:
        n3 = np.r_[n, 0.0]
        psi = math.atan2(-n[1], -n[0]) - math.atan2(a0[1], a0[0])
        R = rz(psi) @ R0
        tcp = np.r_[c + n * (h - held["depth"]), s["z"] + held["dz"] + 0.004]
        legs = [(tcp + n3 * 0.10 + np.array([0, 0, 0.04]), R), (tcp + np.array([0, 0, 0.02]), R), (tcp, R)]
        retreat = tcp + n3 * 0.10
        park = find_park(rig.kin, rig.world, legs + [(retreat, R)], near=rig.base_pose(), max_tries=120,
                         q_start=rig.q_cmd, travel_q=_travel_q(rig))
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
    rig.move_to(*legs[0], step=0.01, label="flat_pre", q_hint=park[3][0])
    rig.caption = f"PLACE {name}: slide in over the surface"
    rig.move_to(*legs[1], step=0.004, steps_per_wp=4, label="flat_over", collision=False)
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
