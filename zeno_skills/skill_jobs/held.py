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
