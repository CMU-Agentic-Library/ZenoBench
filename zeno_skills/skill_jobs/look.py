"""The jobs of the perception shape (motion_skills.Job): look and inspect, plan_look where the robot stands;
the hooks record what each head segment let the camera see and done() judges the result (they judge and
register, they do not move the robot: docs 8.6)."""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from ..motion_state import Failure
from ..perception import HEAD_LIMITS, look_angles, project_to_head_camera
from ..rig import SkillFailure
from ..tolerances import LOOK_STEPS
from .base import RigBase
from .carry import _carry


def head_segment(rig, yaw, pitch, steps=LOOK_STEPS, name="head"):
    """The head aimed at (yaw, pitch) rad as a plan segment (skill_plans.look.head_segment)."""
    from ..skill_plans.look import head_segment as seg
    return seg(rig.q(), yaw, pitch, steps, name)


def drive_head(rig, yaw, pitch, steps=LOOK_STEPS):
    """One head segment run by run.execute, outside any skill's plan: for the skills not migrated yet that
    still turn the head on their own (present, nod) and run_skill's head-straight step."""
    from ..run import execute
    execute(rig, head_segment(rig, yaw, pitch, steps))


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


def facing_for(rig, p):
    """The heading (deg) to turn the base to so the head can centre ``p``, or None when its yaw is within
    the head's range from where the base stands."""
    yaw, _ = look_angles(rig, p)
    if abs(yaw) < HEAD_LIMITS["head_yaw_joint"][1] - 0.02:
        return None
    x, y, _ = rig.base_pose()
    return math.degrees(math.atan2(p[1] - y, p[0] - x))


def _job(rig, state, skill, aims, face, label, on_view=None, done=None):
    """The Job of a look at ``aims`` [after a turn to ``face``]: plan_look where the robot stands, hooks
    ``on_view(rig, what)`` after each head segment, ``done()`` the result."""
    from ..motion_skills import Job
    from ..skill_plans.look import plan_look as _default
    plan_look = skill.build if skill is not None else _default
    aims = list(aims)
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
    return Job(ready=ready, done=done)


def look_job(rig, args, state, skill=None):
    """motion_skills.Job of look.  args, one of:
    ``target`` (an entity): the head at it (entity_point, or ``point``), the base turned toward it first when
      its bearing is past the head's yaw range (facing_for); the result judged (done): in view, or
      SkillFailure; what came into view recorded (perceive.record_view) -- the skill look;
    ``aims`` [("point", name, xyz, steps) | ("head", yaw, pitch, steps)], ``face`` a heading (deg) or None,
      ``on_view`` fn(rig, what) after each head segment (``what``: the aimed point's name, None for a fixed
      angle) -- the looks of the task layer above it (search, explore, count), which judge for themselves.
    ``label``: the segments' names."""
    if "target" not in args:
        return _job(rig, state, skill, args["aims"], args.get("face"), args.get("label", "look"),
                    on_view=args.get("on_view"))
    from ..policies.perceive import record_view
    from ..predicates import entity_point, memory
    target = args["target"]
    p = np.asarray(args["point"] if args.get("point") is not None else entity_point(rig, target), float)
    label = args.get("label", "look")

    def done():
        ok, detail = project_to_head_camera(rig, p, exclude=target)
        seen = record_view(rig)
        rig.log("look_result", target=target, visible=ok, detail=detail, seen=seen)
        if not ok:
            raise SkillFailure(f"look at {target}: {detail}")
        memory(rig)["observed"][target] = rig.tick
        return {"visible": True, "seen": seen}
    return _job(rig, state, skill, [("point", target, [float(v) for v in p], LOOK_STEPS)], facing_for(rig, p),
                label, done=done)


def inspect_job(rig, args, state, skill=None):
    """motion_skills.Job of inspect: a look at the inside of a receptacle -- a container's rim, an
    articulated part's cavity, a support or appliance top -- then (done) the objects inside it the head
    camera sees, recorded as its contents; SkillFailure when the receptacle itself is not in view."""
    from ..policies.perceive import record_view
    from ..predicates import entity_kind, entity_point, memory, objects_inside, objects_on_support
    receptacle = args["receptacle"]
    kind, rec = entity_kind(rig.ann, receptacle)
    st = rig.state()
    if kind == "object":
        if not rig.ann.asset_of(rec).get("container"):
            raise SkillFailure(f"inspect {receptacle}: not a container")
        b = rig.geo.bottom(receptacle, st)
        p = np.array([b[0], b[1], b[2] + rig.ann.asset_of(rec)["container"]["rim_height"]])
        inside = objects_inside(rig, receptacle, st)
    elif kind == "articulated":
        box = rec.get("cavity_aabb") or rec.get("body_aabb")
        p = np.array([(box[0] + box[3]) / 2, (box[1] + box[4]) / 2, (box[2] + box[5]) / 2])
        inside = [n for n in rig.ann.objects
                  if all(box[i] < rig.geo.centre(n, st)[i] < box[i + 3] for i in range(3))]
        for sname in [s["name"] for s in rig.ann.supports if s.get("furniture") == receptacle]:
            inside += [n for n in objects_on_support(rig, sname, st) if n not in inside]
    elif kind in ("support", "furniture", "appliance"):
        p = entity_point(rig, receptacle, st)
        inside = objects_on_support(rig, receptacle if kind != "appliance" else receptacle + "/top", st)
    else:
        raise SkillFailure(f"inspect {receptacle}: unsupported receptacle kind {kind}")

    def done():
        ok, detail = project_to_head_camera(rig, p, exclude=receptacle)
        record_view(rig)
        visible = [n for n in inside if project_to_head_camera(rig, rig.geo.centre(n, rig.state()), exclude=n)[0]]
        mem = memory(rig)
        for n in visible:
            mem["observed"][n] = rig.tick
        mem["observed"][receptacle] = rig.tick
        mem.setdefault("contents", {})[receptacle] = visible
        rig.log("inspect_result", receptacle=receptacle, visible=ok, contents=visible,
                hidden=sorted(set(inside) - set(visible)))
        if not ok:
            raise SkillFailure(f"inspect {receptacle}: {detail}")
        return {"contents": visible}
    return _job(rig, state, skill, [("point", receptacle, [float(v) for v in p], LOOK_STEPS)], facing_for(rig, p),
                f"inspect_{receptacle}", done=done)
