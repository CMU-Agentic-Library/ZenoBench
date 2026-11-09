"""navigate's job (motion_skills.Job): plan_navigate from the state now, the load checked around the drive."""

from __future__ import annotations

from dataclasses import replace

from ..motion_state import Failure
from ..rig import SkillFailure
from ..skills import (check_held, check_left_held)
from .base import RigBase
from .carry import _carry


def navigate_job(rig, args, state, skill=None):
    """motion_skills.Job of navigate: no park to choose (the pose is given), plan_navigate from the
    state now; the hooks check the load before and after the drive."""
    from ..motion_skills import Job
    from ..skill_plans import plan_navigate as _default
    plan_navigate = skill.build if skill is not None else _default
    pose, label, mbz, arrive = args["pose"], args.get("label", "navigate"), args.get("min_bottom_z"), args.get("arrive")
    carry = _carry(rig, rig.held["name"], mbz) if rig.held is not None else None
    if carry is not None and not args.get("raise_load", True):
        # the caller's carry_posture made the higher-ride decision for this min_bottom_z (kept or
        # raised): one decision, one place (rule 2) -- a second try could land, by the planner's
        # chance, on a posture the caller's park search never assumed
        carry = replace(carry, want=None, raise_goals=None)
    base = RigBase(rig)
    stage_of = {"tuck": "arm", "carry_in": "arm", "left_fold": "left_fold", label: "drive", "arrive": "arrive"}

    def build(st, frm="arm"):
        return plan_navigate(rig.kin, rig.left_kin, st, pose, base, carry=carry, arrive=arrive, label=label,
                             start=stage_of.get(frm, frm))

    def ready(found):
        plan = build(state)
        if isinstance(plan, Failure):
            raise SkillFailure(plan.why if plan.segment == label else f"{label}: {plan.segment}: {plan.why}")
        for what, why in plan.info.get("skipped", {}).items():
            rig.log(f"{what}_blocked", reason=str(why)[:200])
        if "carry" in plan.info:
            rig.log("carry_posture", how=plan.info["carry"], moved=any(sg.name == "carry_in" for sg in plan.segments))

        def before_drive(r):
            if r.held is not None:
                if mbz is not None:
                    bottom_z = float(r.geo.bottom(r.held["name"], r.state())[2])
                    r.log("carry_height", bottom_z=round(bottom_z, 3), requested=round(float(mbz), 3))
                check_held(r, "carry_up", open_hand=False)

        def after_drive(r):
            if r.held is not None:
                check_held(r, "carry", open_hand=False)
            if r.left_held is not None:
                check_left_held(r, "left_carry")
        hooks = {"carry_in": {"after": lambda r: check_held(r, "carry_in", open_hand=False)},
                 label: {"before": before_drive, "after": after_drive}}
        return plan, (lambda st, frm: build(st, frm)), hooks
    return Job(ready=ready)
