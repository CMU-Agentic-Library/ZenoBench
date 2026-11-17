"""look's job (motion_skills.Job, perception shape): plan_look where the robot stands; the hooks record what
each head segment let the camera see (they judge and register, they do not move the robot: docs 8.6)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from ..motion_state import Failure
from ..perception import look_angles
from ..rig import SkillFailure
from .base import RigBase
from .carry import _carry


def head_aims(state, aims):
    """[(yaw, pitch, steps, what)] for ``aims`` from the base and body of ``state``: ("point", name, xyz,
    steps) -> the angles that centre xyz in the image (perception.look_angles, clipped to the head's
    limits); ("head", yaw, pitch, steps) as given."""
    tw = {"torso_lift_joint": float(state.body[0]), "waist_pitch_joint": float(state.body[1])}
    out = []
    for a in aims:
        if a[0] == "point":
            _, name, p, steps = a
            yaw, pitch = look_angles(None, np.asarray(p, float), base_pose=tuple(state.base), torso_waist=tw)
            out.append((float(yaw), float(pitch), int(steps), name))
        else:
            _, yaw, pitch, steps = a
            out.append((float(yaw), float(pitch), int(steps), None))
    return out


def look_job(rig, args, state, skill=None):
    """motion_skills.Job of look.  args: ``aims`` [("point", name, xyz, steps) | ("head", yaw, pitch, steps)],
    ``face`` a heading (deg) to turn the base to first, or None, ``label``, ``on_view`` fn(rig, what) run
    after each head segment (``what``: the aimed point's name, None for a fixed angle)."""
    from ..motion_skills import Job
    from ..skill_plans.look import plan_look as _default
    plan_look = skill.build if skill is not None else _default
    aims, face, label = list(args["aims"]), args.get("face"), args.get("label", "look")
    on_view = args.get("on_view")
    carry = _carry(rig, rig.held["name"], None) if rig.held is not None else None
    if carry is not None:
        carry = replace(carry, want=None, raise_goals=None)     # a turn keeps the load as it rides
    base = RigBase(rig)
    stage_of = {"tuck": "arm", "carry_in": "arm", "left_fold": "left_fold", f"{label}_turn": "drive",
                "arrive": "arrive"}

    def build(st, frm=None):
        return plan_look(rig.kin, rig.left_kin, st, base, lambda s: head_aims(s, aims), face=face, carry=carry,
                         label=label, start=stage_of.get(frm, frm))

    def ready(found):
        plan = build(state)
        if isinstance(plan, Failure):
            raise SkillFailure(f"{label}: {plan.segment}: {plan.why}")
        hooks = {}
        if on_view is not None:
            for sg in plan.segments:
                if sg.kind == "action" and sg.action[0] == "head":
                    hooks[sg.name] = {"after": (lambda what: lambda r: on_view(r, what))(sg.info.get("looks_at"))}
        # rebuilt head segments carry the same names, so the hooks still find them
        return plan, (lambda st, frm, prior=None: build(st, frm)), hooks
    return Job(ready=ready)
