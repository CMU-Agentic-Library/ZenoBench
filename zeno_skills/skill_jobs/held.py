"""The jobs of a held load moved where the robot stands (motion_skills.Job; HAND_PLAN 9e): lift / lower (the load
straight up or down to a height, skill_plans.plan_held_move) and present (the load in front of the head camera,
plan_posture to a goal set and a head segment).  Either hand: the one that holds the load (HAND_PLAN 9c).  The
hooks check the hold after each move and done() judges the result; they do not move the robot (docs 8.6)."""

from __future__ import annotations

import math

import numpy as np

from ..motion_state import Failure, Plan
from ..rig import SkillFailure
from ..predicates import FLIPPED_DOT, HELD_HEIGHT_TOL, POINTING_DEG, PRESENT_FWD, PRESENT_Z
from ..skills import check_held
from ..tolerances import (FLIP_MIN, FLIP_PAST, FLIP_PUSH_TO, FLIP_RELEASE, POINT_FRONT, ROTATE_NEAR_BASE, ROTATE_TOL_DEG,
                          SHAKE_SLIP, UPRIGHT_RAISE, WAVE_AMP)

# present: the load's centre anywhere in the region the presenting predicate defines (predicates.PRESENT_FWD /
# PRESENT_Z: in front of the base, at eye level) -- a grid PRESENT_INSET inside its bounds, PRESENT_STEPS points
# along forward and along height, at each of PRESENT_SIDEWAYS (m, negative: toward the holding hand's side; mirrored
# for the left).  One goal set (free_leg takes the cheapest); until the rule audit of 11-25 the old
# PresentHeldPolicy's four tries, numbers of their own
PRESENT_INSET = 0.1
PRESENT_STEPS = 3
PRESENT_SIDEWAYS = (0.0, -0.10)


def present_at():
    """(forward, sideways, height) m of present's goal set: the grid of the presenting region (PRESENT_FWD / _Z)."""
    f = np.linspace(PRESENT_FWD[0] + PRESENT_INSET, PRESENT_FWD[1] - PRESENT_INSET, PRESENT_STEPS)
    z = np.linspace(PRESENT_Z[0] + PRESENT_INSET, PRESENT_Z[1] - PRESENT_INSET, PRESENT_STEPS)
    return tuple((float(a), float(lat), float(b)) for a in f for b in z for lat in PRESENT_SIDEWAYS)
PRESENT_HEAD_STEPS = 60  # ticks the head turns toward the presented load in


def _held(rig, name, what):
    """(side, kin) of the hand that holds ``name``; SkillFailure when neither does."""
    side = rig.hand_of(name)
    if side is None:
        raise SkillFailure(f"{what} {name}: not held")
    return side, rig.arm_kin(side)


def _hooks(plan, side):
    """After each move the hold checked (the load is still in that hand); a drop asks run for the failure exit that
    opens that hand (docs 8.6: a hook does not move the robot)."""
    return {sg.name: {"after": lambda r, n=sg.name: check_held(r, n, open_hand=False, side=side)}
            for sg in plan.segments if sg.kind == "move"}


def _bottom(rig, name):
    return float(rig.geo.bottom(name, rig.state())[2])


def lift_job(rig, args, state, skill=None):
    """motion_skills.Job of lift: what a hand holds (``args["name"]``) straight up where the robot stands until
    its bottom is at ``args["height"]`` (m, world) -- nothing moves when it is that high already (within
    HELD_HEIGHT_TOL).  done(): the measured bottom at least height - HELD_HEIGHT_TOL (SkillFailure otherwise; a load whose
    end is caught lags the hand, and that is a failure, not a second try), logged as held_height_result."""
    return _height_job(rig, args, skill, up=True)


def lower_job(rig, args, state, skill=None):
    """motion_skills.Job of lower: as lift_job, straight down until the bottom is at ``args["height"]`` --
    nothing moves when it is that low already.  done(): the bottom at most height + HELD_HEIGHT_TOL."""
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
    still = (dz <= HELD_HEIGHT_TOL) if up else (dz >= -HELD_HEIGHT_TOL)
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
        if (up and actual < height - HELD_HEIGHT_TOL) or (not up and actual > height + HELD_HEIGHT_TOL):
            raise SkillFailure(f"{label} {name}: bottom at {actual:.3f} m, asked {height:.3f} m")
        return actual
    return Job(ready=ready, done=done)


def present_job(rig, args, state, skill=None):
    """motion_skills.Job of present: what a hand holds (``args["name"]``) brought in front of the body where the
    robot stands -- its centre at any of present_at() (the presenting region; sideways mirrored for the left hand), the
    hand's rotation
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
                          for f, l, z in present_at()))

    def build(st, frm=None, prior=None):
        plan = plan_posture(kin, st, goals, name="present")
        if isinstance(plan, Failure):
            return plan
        legs = [sg for sg in plan.segments if sg.kind == "move"]
        q_end = legs[-1].q_end if legs else st.q(side)
        at = kin.tcp(np.asarray(q_end, float))[0] - off
        body = {n: float(v) for n, v in zip(kin.names[:2], np.asarray(q_end, float)[:2])}
        # from the State it builds from (its base, the body the leg leaves), not the rig's -- a build reads the State
        yaw_h, pitch_h = look_angles(None, at, base_pose=tuple(st.base), torso_waist=body)
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
# upright: the hand raised UPRIGHT_RAISE at least (or half the load's longest side) where it is, or a TCP in front
# of the chest (forward, sideways toward the hand's side, height, m) -- the old stage grid's core; the turned
# load's heading about the vertical free (UPRIGHT_YAWS deg)
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
    """motion_skills.Job of release (HAND_PLAN 9f): the ``args["hand"]`` hand (default: the one holding it) lets go of
    ``args["name"]`` where it is and pulls out back along the gripper axis as far as contact_extent measures
    (plan_release: built before anything moves; an anchor where it let go).  The hand registered empty once it
    opened.  done(): the hand empty."""
    from ..motion_skills import Job
    from ..skill_plans import plan_release as _default
    from ..skills import pick_approach
    plan_release = skill.build if skill is not None else _default
    name = args["name"]
    side = args.get("hand") or rig.hand_of(name) or "right"      # the hand the route names, else the one holding it
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


# gestures (HAND_PLAN 9h): one goal set each where the old policies tried poses one after another
WAVE_AT = (0.35, 0.25, (1.25, 1.15, 1.05))   # m: the hand raised this far forward, toward its own side, at any of
#                                             these heights (the old WaveHandPolicy's three tries)
POINT_SHOULDER = (0.09, 0.18, 1.05)           # m: the pointing ray's origin -- forward, toward the hand's side, height
POINT_REACH = (0.45, 0.38, 0.52, 0.30)        # m out along the ray the hand may stand (the old four tries)


def _hands_for(rig, may_hold=False):
    """The hands an in-place gesture may use: the empty ones; with ``may_hold`` (point), both when neither is."""
    empty = [sd for sd in ("right", "left") if rig.held_by(sd) is None]
    return empty or (["right", "left"] if may_hold else [])


def _either_hand(rig, st, sides, goals_of, spec_of, build_for):
    """The plan of an in-place skill any of ``sides`` may make (HAND_PLAN 3.1: the hand a dimension of the goal set,
    not chosen first): every hand's goal set ranked by free_leg's own score (primitives.pose_set_scores, from the arm
    as it stands in ``st``) -- a hand after the first VARIANT_COST more: the right first only as a weak preference --
    and built in that order; one that does not build gives way to the next (another goal of the set, not a
    fallback: rule 3).  ``goals_of(side)``: that hand's PoseSet, ``spec_of(side)`` the Spec its reach is ranked in,
    ``build_for(side)`` its plan.  Plan or Failure (every hand's reason)."""
    from ..park_search import VARIANT_COST
    from ..primitives import pose_set_scores
    ranked = []
    for j, sd in enumerate(sides):
        scores, _ = pose_set_scores(rig.arm_kin(sd), st, spec_of(sd), goals_of(sd))
        ranked.append((float(np.min(scores)) + VARIANT_COST * j if len(scores) else np.inf, j, sd))
    why = []
    for score, _, sd in sorted(ranked):
        if not np.isfinite(score):
            why.append(f"{sd}: no goal of its set reachable")
            continue
        plan = build_for(sd)
        if not isinstance(plan, Failure):
            return plan
        why.append(f"{sd}: {plan.why}")
    return Failure("; ".join(why) or "no hand to do it with")


def _plan_hand(plan):
    """The hand a gesture's plan works with (its segments are sided)."""
    return next((sg.info["side"] for sg in plan.segments if sg.info.get("side")), "right")


def _gesture_job(rig, label, build, done, ctx):
    """The Job of an in-place gesture: ``build(st, frm=None, prior=None)`` makes the plan (the first: either hand, by
    _either_hand; run's rebuild: the hand ``prior`` has) -- ``ctx["side"]`` the hand it chose, for ``done``."""
    from ..motion_skills import Job

    def ready(found):
        plan = build(_observe(rig))
        if isinstance(plan, Failure):
            raise SkillFailure(f"{label}: {plan.why}")
        side = ctx["side"] = _plan_hand(plan)
        return plan, build, _hooks(plan, side) if rig.held_by(side) is not None else {}
    return Job(ready=ready, done=done)


def wave_job(rig, args, state, skill=None):
    """motion_skills.Job of wave (HAND_PLAN 9h): an empty hand opened, raised fingers up and palm forward in front of
    the body toward its own side (WAVE_AT: one goal set of three heights per hand, either empty hand: _either_hand),
    swung WAVE_AMP to each side ``swings`` times (plan_gesture's swing, a task segment), then folded (kin.rest).
    done(): memory gestures["wave"]."""
    from ..kinematics import gripper_rot
    from ..predicates import memory
    from ..primitives import JointSet, PoseSet
    from ..skill_plans import plan_gesture as _default
    from ..skill_plans._common import FREE_HAND
    plan_gesture = skill.build if skill is not None else _default
    swings = int(args.get("swings", 3))
    sides = _hands_for(rig)
    if not sides:
        raise SkillFailure("wave: both hands hold something")
    x, y, yaw = rig.base_pose()
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    fwd, out, heights = WAVE_AT
    R = gripper_rot([0.0, 0.0, 1.0], [c, s, 0.0])

    def goals_of(sd):
        sgn = 1.0 if sd == "right" else -1.0
        return PoseSet(tuple((np.array([x + fwd * c + sgn * out * s, y + fwd * s - sgn * out * c, z]), R)
                             for z in heights))

    def plan_for(sd, st, frm=None):
        kin = rig.arm_kin(sd)
        return plan_gesture(kin, st, "wave", goals=goals_of(sd), swing=((-s, c, 0.0), WAVE_AMP, swings), open_hand=0.04,
                            back=JointSet((np.asarray(kin.rest, float),)), hold_tilt=False, start=frm)

    def build(st, frm=None, prior=None):
        if frm is not None and prior is not None:          # run's rebuild: the hand the plan has (its decision)
            return plan_for(_plan_hand(prior), st, frm)
        return _either_hand(rig, st, sides, goals_of, lambda sd: FREE_HAND, lambda sd: plan_for(sd, st))
    ctx = {}

    def done():
        memory(rig).setdefault("gestures", {})["wave"] = swings
        rig.log("wave_result", hand=ctx.get("side"), swings=swings)
        return {"swings": swings}
    return _gesture_job(rig, "wave", build, done, ctx)


def _point_ray(rig, p, sd):
    """(the ``sd`` hand's shoulder -- POINT_SHOULDER from the base, toward that hand's side --, the unit ray from it
    to the point p, the base's forward unit in the plane)."""
    x, y, yaw = rig.base_pose()
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    f, l, z = POINT_SHOULDER
    sgn = 1.0 if sd == "right" else -1.0
    shoulder = np.array([x + f * c + sgn * l * s, y + f * s - sgn * l * c, z])
    d = np.asarray(p, float) - shoulder
    return shoulder, d / np.linalg.norm(d), np.array([c, s])


def point_in_front(rig, target, p=None):
    """Whether a hand that may point (_hands_for) has ``target`` in front: its shoulder's ray to it runs at least
    POINT_FRONT forward.  The one test: the point skill refuses by it, the task layer turns the robot by it
    (policies.gestures.PointAtPolicy)."""
    from ..predicates import entity_point
    p = np.asarray(entity_point(rig, target) if p is None else p, float)
    return any(_point_ray(rig, p, sd)[1][:2] @ _point_ray(rig, p, sd)[2] >= POINT_FRONT
               for sd in _hands_for(rig, may_hold=True))


def point_job(rig, args, state, skill=None):
    """motion_skills.Job of point (HAND_PLAN 9h): the closed fingers (an empty hand closed first) along the ray from
    the hand's shoulder (POINT_SHOULDER) to ``args["target"]``, the hand anywhere along it at POINT_REACH -- one goal
    set per hand, either empty hand (both when neither is: a hand that holds something points with it), _either_hand.
    A target not in front (the ray's forward part < 0.2): SkillFailure (the task layer turns the robot first).
    done(): the fingers' axis within POINTING_DEG of the target (point_result), the angle returned."""
    from ..kinematics import gripper_rot
    from ..predicates import entity_point
    from ..primitives import PoseSet
    from ..skill_plans import plan_gesture as _default
    from ..skill_plans._common import FREE_HAND, FREE_LOAD
    plan_gesture = skill.build if skill is not None else _default
    target = args["target"]
    sides = _hands_for(rig, may_hold=True)
    p = np.asarray(entity_point(rig, target), float)
    if not point_in_front(rig, target, p):
        raise SkillFailure(f"point at {target}: not in front of the robot")

    def goals_of(sd):
        shoulder, d, fwd = _point_ray(rig, p, sd)
        if d[:2] @ fwd < POINT_FRONT:
            return PoseSet(())                                   # not in front of this hand's shoulder
        across = np.cross(d, [0.0, 0.0, 1.0])
        across = across / np.linalg.norm(across) if np.linalg.norm(across) > 1e-6 else np.array([0.0, 1.0, 0.0])
        return PoseSet(tuple((shoulder + d * r, gripper_rot(d, across)) for r in POINT_REACH))

    def plan_for(sd, st, frm=None):
        return plan_gesture(rig.arm_kin(sd), st, "point", goals=goals_of(sd),
                            open_hand=0.0 if rig.held_by(sd) is None else None, start=frm)

    def build(st, frm=None, prior=None):
        if frm is not None and prior is not None:          # run's rebuild: the hand the plan has (its decision)
            return plan_for(_plan_hand(prior), st, frm)
        return _either_hand(rig, st, sides, goals_of, lambda sd: FREE_HAND if rig.held_by(sd) is None else FREE_LOAD,
                            lambda sd: plan_for(sd, st))
    ctx = {}

    def done():
        side = ctx["side"]
        tcp, R2 = rig.arm_kin(side).tcp(rig.chain_q(side))
        v = p - np.asarray(tcp, float)
        ang = math.degrees(math.acos(float(np.clip((-R2[:, 2]) @ v / np.linalg.norm(v), -1.0, 1.0))))
        rig.log("point_result", target=target, hand=side, angle_deg=round(ang, 2))
        if ang > POINTING_DEG:
            raise SkillFailure(f"point at {target}: {ang:.1f} deg off")
        return ang
    return _gesture_job(rig, "point", build, done, ctx)


def shake_job(rig, args, state, skill=None):
    """motion_skills.Job of shake (HAND_PLAN 9h): what a hand holds (``args["name"]``) shaken ``cycles`` times
    ``amplitude`` m to each side along the pinch's closing axis (its horizontal part; the base's sideways where it is
    near vertical) -- the pads take the load in compression, a sideways shake rolled a block in the pinch -- one task
    segment, the load's tilt held, ending where it started.  done(): the pinch closed at most SHAKE_SLIP (the object
    did not turn in it), memory shaken counted."""
    from ..predicates import memory
    from ..skill_plans import plan_gesture as _default
    plan_gesture = skill.build if skill is not None else _default
    name = args["name"]
    cycles, amp = int(args.get("cycles", 3)), float(args.get("amplitude", 0.02))
    side, kin = _held(rig, name, "shake")
    _, R = kin.tcp(rig.chain_q(side))
    lat = np.asarray(R, float)[:, 1].copy()
    lat[2] = 0.0
    if np.linalg.norm(lat) < 0.3:
        yaw = math.radians(rig.base_pose()[2])
        lat = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
    gap0 = float(np.sum(rig.fingers() if side == "right" else rig.left_fingers()))

    def build(st, frm=None, prior=None):
        return plan_gesture(kin, st, "shake", swing=(lat, amp, cycles), start=frm)

    def done():
        gap1 = float(np.sum(rig.fingers() if side == "right" else rig.left_fingers()))
        rig.log("shake_grip", obj=name, hand=side, gap_before=round(gap0, 4), gap_after=round(gap1, 4))
        if gap0 - gap1 > SHAKE_SLIP:
            raise SkillFailure(f"shake {name}: the pinch closed {gap0 - gap1:.3f} m (object turned in the hand)")
        mem = memory(rig).setdefault("shaken", {})
        mem[name] = mem.get(name, 0) + cycles
        rig.log("shake_result", obj=name, cycles=cycles)
        return {"cycles": cycles}
    return _gesture_job(rig, "shake", build, done, {})          # the hand that holds it: no choice




def flip_job(rig, args, state, skill=None):
    """motion_skills.Job of flip (HAND_PLAN 9h): what a hand holds by its edge (``args["name"]``, an edge pinch, picked
    from an overhang) turned over where the robot stands -- the pivot its far edge on the support along the approach,
    the arc about it (skill_plans.plan_flip); an arm that turns it less than FLIP_MIN fails the build (plan_flip's
    "min_arc", every build: the first and run's).  done(): its up
    axis points down (SkillFailure otherwise), the arc returned."""
    from ..motion_skills import Job
    from ..evaluator import quat_R
    from ..policies.contact import _room_along
    from ..skill_plans import plan_flip as _default
    plan_flip = skill.build if skill is not None else _default
    name = args["name"]
    side, kin = _held(rig, name, "flip")
    held = rig.held_by(side)
    if held.get("kind") != "edge":
        raise SkillFailure(f"flip {name}: needs an edge pinch (pick it from an overhang first)")
    st = rig.state()
    _, R0 = kin.tcp(rig.chain_q(side))
    a = -np.asarray(R0, float)[:, 2]
    a = np.array([a[0], a[1], 0.0])
    a /= max(1e-9, float(np.linalg.norm(a)))
    size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
    Rb = quat_R(rig.obj_pose(name)[1])
    length = float(np.abs(Rb[:2, :2].T @ a[:2]) @ size[:2])
    bottom = np.asarray(rig.geo.bottom(name, st), float)
    pivot = np.r_[bottom[:2] + a[:2] * length / 2, bottom[2]]
    # held, it is lifted off its support: the highest annotated one under its footprint, no higher than its bottom
    s = rig.geo.support_under(name, st) or max(
        (x for x in rig.ann.supports if x["aabb_xy"][0] <= bottom[0] <= x["aabb_xy"][2]
         and x["aabb_xy"][1] <= bottom[1] <= x["aabb_xy"][3] and x["z"] <= bottom[2] + 0.01),
        key=lambda x: x["z"], default=None)
    if s is None:
        raise SkillFailure(f"flip {name}: not over an annotated support")
    if _room_along(rig, name, s, a[:2]) < length * 0.9:
        raise SkillFailure(f"flip {name}: no room on {s['name']} to land it turned over")
    k = np.cross(-a, [0.0, 0.0, 1.0])
    k /= np.linalg.norm(k)
    flip = {"obj": name, "support": s.get("furniture") or s["name"].split("/")[0], "pivot": pivot, "axis": k,
            "release": FLIP_RELEASE, "past": FLIP_PAST, "push_to": FLIP_PUSH_TO, "min_arc": FLIP_MIN,
            "pre_open": float(held.get("pre_open", 0.04))}
    z0 = Rb[:, 2].copy()
    rests = (kin.rest, kin.drive)
    ctx = {}

    def build(st_, frm=None, prior=None):
        # the arc short of FLIP_MIN fails plan_flip itself ("min_arc"): here and in run's rebuild alike
        return plan_flip(kin, st_, flip, rests, start=frm or "flip_arrive", prior=prior)

    def ready(found):
        plan = build(_observe(rig))
        if isinstance(plan, Failure):
            raise SkillFailure(f"flip {name}: {plan.why}")
        ctx["arc"] = plan.info.get("arc_rad")
        return plan, build, {"flip_release": {"after": lambda r: r.set_held(side, None)}}

    def done():
        z1 = quat_R(rig.obj_pose(name)[1])[:, 2]
        dot = float(z0 @ z1)
        rig.log("flip_result", obj=name, hand=side, arc_deg=round(math.degrees(ctx.get("arc") or 0.0), 1),
                z_dot=round(dot, 3))
        if dot > FLIPPED_DOT:
            raise SkillFailure(f"flip {name}: not turned over (z dot {dot:.2f})")
        return math.degrees(ctx.get("arc") or 0.0)
    return Job(ready=ready, done=done)
