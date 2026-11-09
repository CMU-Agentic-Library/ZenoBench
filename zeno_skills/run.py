"""Executing a plan (docs/MOTION_ARCHITECTURE.md section 8): ``run`` takes the segments one by one
-- checks that each still holds in the world as it is now (``holds``), else builds the rest of the
plan again from here with the skill's own builder, runs it, and reads the State back
(``observe``).  It touches the simulator only through motion_state.Actuator (docs 2.5): the reads
in ``observe``, the writes in ``execute``."""

from __future__ import annotations

from contextlib import ExitStack

import numpy as np

from .motion_state import Failure
from .primitives import contact_extent, free_path, query
from .rig import PLAN_AT_START, SkillFailure


def observe(act):
    """The State now (Actuator.snapshot: the rig syncs the collision model and reads it back)."""
    return act.snapshot()


def holds(kin, state, seg):
    """Why ``seg`` no longer holds in ``state``, or None: the arm not at its start (PLAN_AT_START);
    a motion whose path is not free now (its Spec, the world as the state has it); a contact whose
    extent measured again from here (contact_extent) ends elsewhere.  Actions and anchors always
    hold; a drive holds while the arm is where it starts (its path is the base planner's, made from
    this state when navigate was planned)."""
    if seg.kind in ("action", "anchor"):
        return None
    q = state.q(kin.side)
    if np.max(np.abs(q - np.asarray(seg.q_from, float))) > PLAN_AT_START:
        return "the arm is not where the segment starts"
    if seg.kind == "drive":
        return None
    if seg.spec.allow.from_contact:
        from .skill_plans import TOUCHING
        ext = contact_extent(kin, state, seg.spec, seg.info["u"], TOUCHING[seg.info["touching"]], seg.name,
                             step=seg.info["step"], q_from=q)
        if isinstance(ext, Failure):
            return f"the contact measured again: {ext.why}"
        if abs(ext.length - seg.info.get("length", 0.0)) > seg.info["step"]:
            return f"the contact measured again is {ext.length:.3f} m, planned {seg.info.get('length', 0.0):.3f} m"
        return None
    if not seg.qs:
        return None
    if not free_path(kin, state, seg.spec, [q] + list(seg.qs)):
        with query(kin, state, seg.spec):
            # where along it and into what
            at = next((i for i, qi in enumerate(seg.qs) if not kin.free(qi)), None)
            what = "" if at is None else f" at {at + 1}/{len(seg.qs)}: {kin.explain(seg.qs[at])}"
            return "its path collides now" + (what or " (between waypoints)")
    return None


def execute(act, seg):
    """Run one segment through the Actuator: an action (the gripper); a drive (the base along its
    paths, the arms switched where the planner put it); the waypoints of an arm under the segment's
    Allow (a contact Allow with what the hand and its load touch now), at its speed; an anchor is
    no motion."""
    if seg.kind == "anchor":
        return
    if seg.kind == "action":
        what = seg.action[0]
        if what == "grip":
            _, width, ticks, gradual = seg.action
            if seg.spec.allow is not None and (seg.spec.allow.to_contact or not seg.spec.allow.checked):
                act.declare(seg.name, seg.spec.allow, follows=False)
            act.grip(width, ticks if ticks is not None else _hz(), gradual=gradual)
            return
        raise ValueError(f"unknown action {what}")
    if seg.kind == "drive":
        kw = dict(seg.info.get("drive_kw") or {})
        for st in seg.info["steps"]:
            if st[0] == "drive":
                act.log("path", target=seg.name, waypoints=[[round(v, 2) for v in w] for w in st[1]],
                        **({"posture": st[2]} if len(st) > 2 else {}))
                act.drive_base(list(st[1]), allow=seg.spec.allow, **kw)
            else:
                _, name, qr, ql = st
                act.swing(qr, ql, f"{seg.name}_{name}")
        return
    if not seg.qs:
        return
    side = seg.info.get("side", "right")
    kin = act.arm_kin(side)
    allow = act.contact_allow(kin, seg.spec.allow) if seg.spec.allow.from_contact else seg.spec.allow
    act.declare(seg.name, allow, side=side)
    act.follow(list(seg.qs), seg.info.get("steps_per_wp", 3), smooth=bool(seg.info.get("smooth")), side=side)


def _hz():
    from .physics import PHYSICS_HZ
    return PHYSICS_HZ


def run(act, plan, rebuild, hooks=None):
    """Run ``plan`` (motion_state.Plan): before each segment the State is read (observe) and the
    segment checked (holds); one that does not hold has the rest of the plan built again from here
    by ``rebuild(state, segment name) -> Plan | Failure`` -- the skill's builder, the one the park
    search used -- and a rest that cannot be built fails the skill (SkillFailure, no fallback).
    ``act``: the motion_state.Actuator (the rig).  ``rebuild`` None: a segment that does not hold
    fails the skill (a plan nobody can build again, docs 8.8).
    ``hooks``: {segment name: {"around": context factory, "before": fn(act), "after": fn(act)}},
    the skill's own steps between segments (the grasp judged, the load registered as held).
    Returns the segments run."""
    hooks = hooks or {}
    segs, done, i = list(plan.segments), [], 0
    while i < len(segs):
        seg = segs[i]
        state = observe(act)
        why = holds(act.arm_kin(seg.info.get("side", "right")), state, seg)
        if why is not None:
            if rebuild is None:
                raise SkillFailure(f"{seg.name}: {why}")
            new = rebuild(state, seg.name)
            act.log("segment", target=seg.name, reused=False, why=why,
                    rebuilt=None if isinstance(new, Failure) else [s.name for s in new.segments])
            if isinstance(new, Failure):
                raise SkillFailure(f"{seg.name}: {why}; built again from here: {new.why}")
            segs = segs[:i] + list(new.segments)
            seg = segs[i]
        else:
            act.log("segment", target=seg.name, reused=True, kind=seg.kind, waypoints=len(seg.qs),
                    how=seg.info.get("how"))
        h = hooks.get(seg.name, {})
        if "before" in h:
            h["before"](act)
        with ExitStack() as st:
            if "around" in h:
                st.enter_context(h["around"]())
            execute(act, seg)
        if "after" in h:
            h["after"](act)
        done.append(seg)
        i += 1
    return done
