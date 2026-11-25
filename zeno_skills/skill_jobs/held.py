"""The jobs of a held load moved where the robot stands (motion_skills.Job; HAND_PLAN 9e): lift / lower (the load
straight up or down to a height, skill_plans.plan_held_move) and present (the load in front of the head camera,
plan_posture to a goal set and a head segment).  Either hand: the one that holds the load (HAND_PLAN 9c).  The
hooks check the hold after each move and done() judges the result; they do not move the robot (docs 8.6)."""

from __future__ import annotations

import math

import numpy as np

from ..motion_state import Failure, Plan
from ..rig import SkillFailure
from ..skills import check_held

HEIGHT_TOL = 0.02       # m: lift / lower -- the load's bottom this close to the height asked got there (the old
#                         CarryHeightAdjustPolicy's / SetHeldHeightPolicy's tolerance and the held_above / held_below
#                         predicates')
# present: the load's centre in front of the base (forward, sideways toward the holding hand's side, height), m.
# One goal set (any of them presents it), not tried one after another as the old PresentHeldPolicy did
PRESENT_AT = ((0.55, -0.05, 1.10), (0.50, -0.15, 1.05), (0.60, 0.0, 1.00), (0.45, -0.10, 0.95))
PRESENT_HEAD_STEPS = 60  # ticks the head turns toward the presented load in


def _held(rig, name, what):
    """(side, kin) of the hand that holds ``name``; SkillFailure when neither does."""
    side = rig.hand_of(name)
    if side is None:
        raise SkillFailure(f"{what} {name}: not held")
    return side, rig.arm_kin(side)


def _hooks(plan, side):
    """After each move the hold checked (the load is still in that hand)."""
    return {sg.name: {"after": lambda r, n=sg.name: check_held(r, n, side=side)}
            for sg in plan.segments if sg.kind == "move"}


def _bottom(rig, name):
    return float(rig.geo.bottom(name, rig.state())[2])


def lift_job(rig, args, state, skill=None):
    """motion_skills.Job of lift: what a hand holds (``args["name"]``) straight up where the robot stands until
    its bottom is at ``args["height"]`` (m, world) -- nothing moves when it is that high already (within
    HEIGHT_TOL).  done(): the measured bottom at least height - HEIGHT_TOL (SkillFailure otherwise; a load whose
    end is caught lags the hand, and that is a failure, not a second try), logged as held_height_result."""
    return _height_job(rig, args, skill, up=True)


def lower_job(rig, args, state, skill=None):
    """motion_skills.Job of lower: as lift_job, straight down until the bottom is at ``args["height"]`` --
    nothing moves when it is that low already.  done(): the bottom at most height + HEIGHT_TOL."""
    return _height_job(rig, args, skill, up=False)


def _height_job(rig, args, skill, up):
    from ..motion_skills import Job
    from ..skill_plans import plan_held_move as _default
    plan_held_move = skill.build if skill is not None else _default
    name, height = args["name"], float(args["height"])
    if not np.isfinite(height) or height < 0:
        raise ValueError("a held height must be finite and nonnegative")
    label = "lift" if up else "lower"
    side, kin = _held(rig, name, label)
    bottom = _bottom(rig, name)
    dz = height - bottom
    still = (dz <= HEIGHT_TOL) if up else (dz >= -HEIGHT_TOL)
    # the TCP's height goal, fixed now: the load moves with the hand (a rebuild goes on to the same height)
    tcp, _ = kin.tcp(rig.chain_q(side))
    z_goal = None if still else float(tcp[2]) + dz

    def build(st, frm=None, prior=None):
        return Plan(()) if z_goal is None else plan_held_move(kin, st, z_goal, name=label, start=frm, prior=prior)

    def ready(found):
        plan = build(_observe(rig))
        if isinstance(plan, Failure):
            raise SkillFailure(f"{label} {name}: {plan.why}")
        return plan, build, _hooks(plan, side)

    def done():
        actual = _bottom(rig, name)
        rig.log("held_height_result", obj=name, hand=side, bottom_z=round(actual, 3), target=round(height, 3),
                moved=z_goal is not None)
        if (up and actual < height - HEIGHT_TOL) or (not up and actual > height + HEIGHT_TOL):
            raise SkillFailure(f"{label} {name}: bottom at {actual:.3f} m, asked {height:.3f} m")
        return actual
    return Job(ready=ready, done=done)


def present_job(rig, args, state, skill=None):
    """motion_skills.Job of present: what a hand holds (``args["name"]``) brought in front of the body where the
    robot stands -- its centre at any of PRESENT_AT (sideways mirrored for the left hand), the hand's rotation
    as it is: one goal set, the free leg to its first reachable goal (plan_posture, the load's tilt held) --
    then the head turned to the load where the leg leaves it.  done(): the view recorded (perceive.record_view),
    the load's centre returned."""
    from ..motion_skills import Job
    from ..perception import look_angles
    from ..policies.perceive import record_view
    from ..primitives import PoseSet
    from ..skill_plans import head_segment, plan_posture as _default
    plan_posture = skill.build if skill is not None else _default
    name = args["name"]
    side, kin = _held(rig, name, "present")
    sgn = 1.0 if side == "right" else -1.0
    x, y, yaw = rig.base_pose()
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    tcp, R = kin.tcp(rig.chain_q(side))
    centre = np.asarray(rig.geo.centre(name, rig.state()), float)
    off = np.asarray(tcp, float) - centre             # TCP minus the load's centre: kept (the hand does not turn)
    goals = PoseSet(tuple((np.array([x + c * f - s * sgn * l, y + s * f + c * sgn * l, z]) + off, np.asarray(R, float))
                          for f, l, z in PRESENT_AT))

    def build(st, frm=None, prior=None):
        plan = plan_posture(kin, st, goals, name="present")
        if isinstance(plan, Failure):
            return plan
        legs = [sg for sg in plan.segments if sg.kind == "move"]
        q_end = legs[-1].q_end if legs else st.q(side)
        at = kin.tcp(np.asarray(q_end, float))[0] - off
        body = {n: float(v) for n, v in zip(kin.names[:2], np.asarray(q_end, float)[:2])}
        yaw_h, pitch_h = look_angles(rig, at, torso_waist=body)
        return Plan(tuple(plan.segments) + (head_segment(q_end, yaw_h, pitch_h, PRESENT_HEAD_STEPS, "present_look",
                                                         what=name),))

    def ready(found):
        plan = build(_observe(rig))
        if isinstance(plan, Failure):
            raise SkillFailure(f"present {name}: {plan.why}")
        return plan, build, _hooks(plan, side)

    def done():
        record_view(rig)
        at = np.asarray(rig.geo.centre(name, rig.state()), float)
        rig.log("present_result", obj=name, hand=side, centre=np.round(at, 3).tolist())
        return at.tolist()
    return Job(ready=ready, done=done)


def _observe(rig):
    from ..run import observe
    return observe(rig)


# rotate: where the turned hand may stand -- the hand where it is first, then pulled toward the base and raised
# (m along the floor toward the base, m up; the old RotateHeldPolicy's staging poses, where the wrist has more
# range).  One goal set, not tried one after another
ROTATE_AT = ((0.0, 0.0), (0.15, 0.06), (0.25, 0.12), (0.05, 0.04), (0.30, 0.20))
ROTATE_NEAR_BASE = 0.35     # m: no staging pose is pulled closer to the base than this (the old code's)
ROTATE_TOL_DEG = 10.0       # deg: the load's yaw changed this close to the angle asked (rotate_result; the old value)
# upright: the hand raised by this much at least (or half the load's longest side) where it is, or a TCP in front
# of the chest (forward, sideways toward the hand's side, height, m) -- the old stage grid's core; the turned
# load's heading about the vertical free (UPRIGHT_YAWS deg)
UPRIGHT_RAISE = 0.12
UPRIGHT_FRONT = tuple((f, l, z) for f in (0.45, 0.38) for l in (-0.15, -0.05) for z in (1.0, 1.1))
UPRIGHT_YAWS = (0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0)


def _rz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0.0], [math.sin(a), math.cos(a), 0.0], [0.0, 0.0, 1.0]])


def _yaw_deg(quat):
    w, x, y, z = quat
    return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def _reanchor(rig, side, name):
    """The hold as it is after the hand turned it (the grasp's tcp_minus_body and R, which check_held reads)."""
    kin = rig.arm_kin(side)
    tcp, R = kin.tcp(rig.chain_q(side))
    held = rig.held_by(side)
    held["tcp_minus_body"] = tcp - np.asarray(rig.obj_pose(name)[0], float)
    held["R"] = R


def _turn_job(rig, name, side, kin, goals, label, hold_tilt, done, skill):
    from ..motion_skills import Job
    from ..skill_plans import plan_posture as _default
    plan_posture = skill.build if skill is not None else _default

    def build(st, frm=None, prior=None):
        return plan_posture(kin, st, goals, name=label, hold_tilt=hold_tilt)

    def ready(found):
        plan = build(_observe(rig))
        if isinstance(plan, Failure):
            raise SkillFailure(f"{label} {name}: {plan.why}")
        return plan, build, _hooks(plan, side)
    return Job(ready=ready, done=done)


def rotate_job(rig, args, state, skill=None):
    """motion_skills.Job of rotate (HAND_PLAN 9f): what a hand holds (``args["name"]``) turned about the vertical
    by ``args["degrees"]`` where the robot stands -- the hand's rotation turned by that much, the TCP where it is
    or at one of ROTATE_AT: one goal set, the free leg (the load's tilt held: a turn about the vertical keeps it)
    to its cheapest reachable goal (plan_posture).  The old policy's 15-degree steps from each staging pose in
    turn are gone: the planner's trajectory is the turn.  done(): the load's yaw changed by the angle asked
    within ROTATE_TOL_DEG (SkillFailure otherwise), the hold re-anchored, the change returned."""
    from ..primitives import PoseSet
    name, deg = args["name"], float(args["degrees"])
    side, kin = _held(rig, name, "rotate")
    tcp, R = kin.tcp(rig.chain_q(side))
    tcp = np.asarray(tcp, float)
    x, y, _ = rig.base_pose()
    toward = np.array([x, y]) - tcp[:2]
    dist = float(np.linalg.norm(toward))
    unit = toward / dist if dist > 1e-6 else np.zeros(2)
    R1 = _rz(deg) @ np.asarray(R, float)
    goals = PoseSet(tuple((tcp + np.r_[unit * min(pull, max(0.0, dist - ROTATE_NEAR_BASE)), up], R1)
                          for pull, up in ROTATE_AT))
    yaw0 = _yaw_deg(rig.obj_pose(name)[1])

    def done():
        change = (_yaw_deg(rig.obj_pose(name)[1]) - yaw0 + 180.0) % 360.0 - 180.0
        rig.log("rotate_result", obj=name, hand=side, requested=deg, yaw_change=round(change, 1))
        if abs((change - deg + 180.0) % 360.0 - 180.0) > ROTATE_TOL_DEG:
            raise SkillFailure(f"rotate {name}: yaw changed {change:.1f} deg, asked {deg:.1f}")
        _reanchor(rig, side, name)
        return change
    return _turn_job(rig, name, side, kin, goals, "rotate_held", True, done, skill)


def upright_job(rig, args, state, skill=None):
    """motion_skills.Job of upright (HAND_PLAN 9f): what a hand holds (``args["name"]``) turned so its own up
    axis is vertical, where the robot stands -- nothing moves when it tilts ``args["max_tilt_deg"]`` or less.  The
    goal set: the hand's rotation that stands the load up, its heading about the vertical free (UPRIGHT_YAWS),
    the TCP raised UPRIGHT_RAISE (or half the load's longest side) where it is or at one of UPRIGHT_FRONT
    (sideways mirrored for the left hand); the free leg there, the load in the collision model but its tilt
    not held (plan_posture hold_tilt=False).  The old policy's 100-point stage grid, its IK continuity search and
    its fallbacks (set it down and pivot, hang it) are gone: one goal set, else the skill fails.  done(): the
    load's tilt at most max_tilt_deg (SkillFailure otherwise), the hold re-anchored, the tilt returned."""
    from ..evaluator import quat_R
    from ..primitives import PoseSet
    name, max_tilt = args["name"], float(args.get("max_tilt_deg", 15.0))
    side, kin = _held(rig, name, "upright")

    def tilt_now():
        return math.degrees(math.acos(float(np.clip(quat_R(rig.obj_pose(name)[1])[2, 2], -1.0, 1.0))))
    tilt0 = tilt_now()
    goals = None
    if tilt0 > max_tilt:
        body_R = quat_R(rig.obj_pose(name)[1])
        tcp, R = kin.tcp(rig.chain_q(side))
        axis = body_R[:2, 0] if np.linalg.norm(body_R[:2, 0]) >= 0.2 else np.array([body_R[1, 1], -body_R[0, 1]])
        yaw0 = math.degrees(math.atan2(axis[1], axis[0]))
        size = rig.ann.asset_of(rig.ann.objects[name])["size"]
        x, y, byaw = rig.base_pose()
        c, s = math.cos(math.radians(byaw)), math.sin(math.radians(byaw))
        sgn = 1.0 if side == "right" else -1.0
        at = [np.asarray(tcp, float) + np.r_[0.0, 0.0, max(UPRIGHT_RAISE, 0.5 * float(max(size)))]]
        at += [np.array([x + c * f - s * sgn * l, y + s * f + c * sgn * l, z]) for f, l, z in UPRIGHT_FRONT]
        Rs = [_rz(yaw0 + d) @ body_R.T @ np.asarray(R, float) for d in UPRIGHT_YAWS]
        goals = PoseSet(tuple((p, Rg) for p in at for Rg in Rs))

    def done():
        tilt = tilt_now()
        rig.log("upright_result", obj=name, hand=side, tilt_deg=round(tilt, 3), moved=goals is not None)
        if tilt > max_tilt:
            raise SkillFailure(f"upright {name}: still {tilt:.1f} deg from vertical")
        if goals is not None:
            _reanchor(rig, side, name)
        return tilt
    if goals is None:
        from ..motion_skills import Job
        return Job(ready=lambda found: (Plan(()), None, {}), done=done)
    return _turn_job(rig, name, side, kin, goals, "upright_turn", False, done, skill)


def release_job(rig, args, state, skill=None):
    """motion_skills.Job of release (HAND_PLAN 9f): the ``args["hand"]`` hand (default right) lets go of
    ``args["name"]`` where it is and pulls out a finger's length back along the gripper axis (plan_release:
    both built before anything moves).  The hand registered empty once it opened.  done(): the hand empty."""
    from ..motion_skills import Job
    from ..skill_plans import plan_release as _default
    from ..skills import pick_approach
    plan_release = skill.build if skill is not None else _default
    name, side = args["name"], args.get("hand", "right")
    held = rig.held_by(side)
    if held is None or held["name"] != name:
        raise SkillFailure(f"release {name}: not in the {side} hand")
    kin = rig.arm_kin(side)
    pre_open = float(held.get("pre_open", 0.04))

    def build(st, frm=None, prior=None):
        return plan_release(kin, st, pre_open, pick_approach(), start=frm or "release_open", obj=name)

    def ready(found):
        plan = build(_observe(rig))
        if isinstance(plan, Failure):
            raise SkillFailure(f"release {name}: {plan.why}")
        return plan, build, {"release_open": {"after": lambda r: r.set_held(side, None)}}

    def done():
        rig.log("release_result", obj=name, hand=side)
        if rig.held_by(side) is not None:
            raise SkillFailure(f"release {name}: the {side} hand still holds {rig.held_by(side)['name']}")
        return True
    return Job(ready=ready, done=done)
