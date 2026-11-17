"""The jobs of the posture shape (motion_skills.Job; docs/MOTION_ARCHITECTURE.md 2.3, 6, 9.3 step 5): crouch,
stand, bend and straighten move one body joint (body_job), tuck folds an empty arm (tuck_job) -- plan_posture
where the robot stands.  The hooks check what the hands hold after the move and done() whether the posture
got where it was sent; they judge and register, they do not move the robot (docs 8.6)."""

from __future__ import annotations

import numpy as np

from ..motion_state import ARM, Failure
from ..primitives import Joint, JointSet
from ..rig import SkillFailure
from ..skills import check_held, check_left_held
from ..tolerances import STOWED_TOL, TORSO_AT, WAIST_AT

AT = {"torso_lift_joint": TORSO_AT, "waist_pitch_joint": WAIST_AT}   # a body joint this close to its target got there


def _job(rig, state, build, label, done):
    """The Job of a posture: the plan ``build(state, None)`` makes here (Failure: SkillFailure, nothing tried
    instead), each leg followed by the grasp checks of both hands, ``done()`` the result."""
    from ..motion_skills import Job

    def ready(found):
        plan = build(state, None)
        if isinstance(plan, Failure):
            raise SkillFailure(f"{label}: {plan.why}")
        hooks = {sg.name: {"after": lambda r, n=sg.name: (check_held(r, n), check_left_held(r, n))}
                 for sg in plan.segments if sg.kind == "move"}
        return plan, (lambda st, frm, prior=None: build(st, frm)), hooks
    return Job(ready=ready, done=done)


def body_job(rig, args, state, skill=None):
    """motion_skills.Job of crouch / stand / bend / straighten: the body joint ``args["joint"]``
    (torso_lift_joint, waist_pitch_joint) to ``args["target"]`` (m / rad, within its limits: ValueError
    otherwise), nothing else moving (Spec.joints, docs 4.2) -- the arms ride the body as they are and what
    either hand holds with them, both arms' chains checked (plan_posture).  done(): the measured joint within
    TORSO_AT / WAIST_AT of the target (SkillFailure otherwise), logged as posture_joint."""
    from ..skill_plans import plan_posture as _default
    plan_posture = skill.build if skill is not None else _default
    joint = args["joint"]
    kin = rig.kin
    idx = kin.names.index(joint)
    target, lo, hi = float(args["target"]), float(kin.lo[idx]), float(kin.hi[idx])
    if not lo <= target <= hi:
        raise ValueError(f"{joint} target {target:.3f} outside [{lo:.3f}, {hi:.3f}]")

    def build(st, frm):
        q = np.asarray(st.q(kin.side), float).copy()
        q[idx] = target
        return plan_posture(kin, st, Joint(q), joints=(joint,), other=getattr(rig, "left_kin", None), name=joint,
                            start=frm)

    def done():
        actual = float(rig.q()[idx])
        if abs(actual - target) > AT[joint]:
            raise SkillFailure(f"{joint}: actual {actual:.3f}, target {target:.3f}")
        rig.log("posture_joint", joint=joint, target=round(target, 3), actual=round(actual, 3),
                held=(rig.held or {}).get("name"))
        return actual
    return _job(rig, state, build, joint, done)


def tuck_job(rig, args, state, skill=None):
    """motion_skills.Job of tuck: the empty arm of ``args["hand"]`` (default right) to its fold (its kin.rest)
    where the robot stands -- the right fold takes the body with it unless the left hand holds something (the
    rule, docs 4.1), the left fold moves that arm alone (Spec.joints ARM) after opening its fingers.  A hand
    that holds something: SkillFailure (navigate carries a load in its carry pose).  done(): the arm joints
    within STOWED_TOL of the fold (the skill's arm_stowed), SkillFailure otherwise."""
    from ..skill_plans import plan_posture as _default
    plan_posture = skill.build if skill is not None else _default
    side = args.get("hand", "right")
    kin, held = (rig.kin, rig.held) if side == "right" else (rig.left_kin, rig.left_held)
    label = "tuck_arm" if side == "right" else "left_fold"
    if held is not None:
        raise SkillFailure(f"tuck {side} arm: the hand holds {held.get('name')}; release it first")
    fold = np.asarray(kin.rest, float)

    def build(st, frm):
        return plan_posture(kin, st, JointSet((fold,)), joints=None if side == "right" else (ARM,),
                            open_hand=None if side == "right" else 0.04, name=label, start=frm)

    def done():
        q = np.asarray(rig.q() if side == "right" else rig.left_q(), float)
        err = float(np.max(np.abs(q[2:] - fold[2:])))
        rig.log("tuck_result", hand=side, error_rad=round(err, 4))
        if err > STOWED_TOL:
            raise SkillFailure(f"tuck {side} arm: joint error {err:.3f} rad")
        return err
    return _job(rig, state, build, label, done)
