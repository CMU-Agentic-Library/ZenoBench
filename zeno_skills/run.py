"""Executing a plan (docs/MOTION_ARCHITECTURE.md section 8): ``run`` takes the segments one by one
-- checks that each still holds in the world as it is now (``holds``), else builds the rest of the
plan again from here with the skill's own builder, runs it, and reads the State back
(``observe``)."""

from __future__ import annotations

from contextlib import ExitStack

import numpy as np

from .kinematics import FINGER_OPEN
from .motion_state import Failure, Hand, Held, State
from .primitives import contact_extent, free_path, query
from .rig import PLAN_AT_START, SkillFailure


def observe(rig):
    """The State now: the base, the commanded arm postures, the head, each hand's finger opening
    (the wider finger, as Motion.live_locks) and what it holds (its box frame in the TCP frame,
    Motion.held_in_tcp), the objects' box frames and the parts' joint values, all as synced into
    the collision model (Rig.sync_world)."""
    rig.sync_world()
    motion = rig.kin.motion
    hands = {}
    for side, kin, q, held, fingers in (
            ("right", rig.kin, rig.q_cmd, rig.held, rig.fingers),
            ("left", rig.left_kin, np.r_[rig.q_cmd[:2], rig.left_q_cmd], rig.left_held, rig.left_fingers)):
        width = float(np.clip(np.asarray(fingers(), float)[:2].max(), 0.0, FINGER_OPEN))
        h = None
        if held is not None:
            name = held["name"]
            T = motion.held_in_tcp(kin, q, name) if motion is not None and motion.by_owner.get(f"object:{name}") \
                else np.eye(4)
            h = Held(name, T, held.get("kind", "pinch"))
        hands[side] = Hand(width=width, held=h)
    return State(base=tuple(rig.base_pose()), q_right=np.asarray(rig.q_cmd, float).copy(),
                 q_left=np.asarray(rig.left_q_cmd, float).copy(), head=dict(rig.head_q()), hands=hands,
                 objects=motion.object_frames() if motion is not None else {},
                 parts={a["name"]: rig.joint(a["name"]) for a in rig.ann.articulated})


def holds(kin, state, seg):
    """Why ``seg`` no longer holds in ``state``, or None: the arm not at its start (PLAN_AT_START);
    a motion whose path is not free now (its Spec, the world as the state has it); a contact whose
    extent measured again from here (contact_extent) ends elsewhere.  Actions always hold."""
    if seg.kind == "action":
        return None
    q = state.q(kin.side)
    if np.max(np.abs(q - np.asarray(seg.q_from, float))) > PLAN_AT_START:
        return "the arm is not where the segment starts"
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


def execute(rig, seg):
    """Run one segment: an action (the gripper), or the waypoints under the segment's Allow (a
    contact Allow with what the hand and its load touch now, Rig._from_contact), at its speed."""
    kin = rig.kin
    if seg.kind == "action":
        what = seg.action[0]
        if what == "grip":
            _, width, ticks, gradual = seg.action
            if seg.spec.allow is not None and (seg.spec.allow.to_contact or not seg.spec.allow.checked):
                rig.clear.motion(seg.name, seg.spec.allow, follows=False)
            rig.grip(width, ticks if ticks is not None else _hz(), gradual=gradual)
            return
        raise ValueError(f"unknown action {what}")
    if not seg.qs:
        return
    allow = rig._from_contact(kin, seg.spec.allow) if seg.spec.allow.from_contact else seg.spec.allow
    if seg.spec.allow.from_contact:
        rig.clear.motion(seg.name, allow, side=kin.side)
    else:
        rig.clear.motion(seg.name, allow)
    follow = rig.follow_smooth if seg.info.get("smooth") else rig.follow
    follow(list(seg.qs), seg.info.get("steps_per_wp", 3))


def _hz():
    from .physics import PHYSICS_HZ
    return PHYSICS_HZ


def run(rig, plan, rebuild, hooks=None):
    """Run ``plan`` (motion_state.Plan): before each segment the State is read (observe) and the
    segment checked (holds); one that does not hold has the rest of the plan built again from here
    by ``rebuild(state, segment name) -> Plan | Failure`` -- the skill's builder, the one the park
    search used -- and a rest that cannot be built fails the skill (SkillFailure, no fallback).
    ``hooks``: {segment name: {"around": context factory, "before": fn(rig), "after": fn(rig)}},
    the skill's own steps between segments (the grasp judged, the load registered as held).
    Returns the segments run."""
    hooks = hooks or {}
    segs, done, i = list(plan.segments), [], 0
    while i < len(segs):
        seg = segs[i]
        state = observe(rig)
        why = holds(rig.kin, state, seg)
        if why is not None:
            new = rebuild(state, seg.name)
            rig.log("segment", target=seg.name, reused=False, why=why,
                    rebuilt=None if isinstance(new, Failure) else [s.name for s in new.segments])
            if isinstance(new, Failure):
                raise SkillFailure(f"{seg.name}: {why}; built again from here: {new.why}")
            segs = segs[:i] + list(new.segments)
            seg = segs[i]
        else:
            rig.log("segment", target=seg.name, reused=True, kind=seg.kind, waypoints=len(seg.qs),
                    how=seg.info.get("how"))
        h = hooks.get(seg.name, {})
        if "before" in h:
            h["before"](rig)
        with ExitStack() as st:
            if "around" in h:
                st.enter_context(h["around"]())
            execute(rig, seg)
        if "after" in h:
            h["after"](rig)
        done.append(seg)
        i += 1
    return done
