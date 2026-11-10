"""Executing a plan (docs/MOTION_ARCHITECTURE.md section 8): ``run`` takes the segments one by one
-- checks that each still holds in the world as it is now (primitives.holds), else builds the rest of the
plan again from here with the skill's own builder, runs it, and reads the State back
(``observe``).  It touches the simulator only through motion_state.Actuator (docs 2.5): the reads
in ``observe``, the writes in ``execute``."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import replace

from .motion_state import Failure, SkillFailure
from .primitives import holds


def observe(act):
    """The State now (Actuator.snapshot: the rig syncs the collision model and reads it back)."""
    return act.snapshot()


def execute(act, seg):
    """Run one segment through the Actuator, each declared to the contact monitor under its Allow
    first: an action (the gripper); a drive (the base along its paths, the arms switched where the
    planner put it); the waypoints of an arm (a contact Allow with what the hand and its load touch
    now), at its speed.  An anchor moves nothing and declares nothing."""
    if seg.kind == "anchor":
        return
    if seg.kind == "action":
        what = seg.action[0]
        if what == "grip":
            _, width, ticks, gradual = seg.action
            act.declare(seg.name, seg.spec.allow, side=seg.info.get("side", "right"), follows=False)
            act.grip(width, ticks if ticks is not None else _hz(), gradual=gradual)
            return
        if what == "wait":                      # let the world settle (an object let go), nothing moves
            act.declare(seg.name, seg.spec.allow, side=seg.info.get("side", "right"), follows=False)
            act.wait(seg.action[1])
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


def _how_decided(seg):
    """For the segment log: how the decisions a segment was built on were made, info["decided"]
    {decision: "prior" kept | "solved" again} (decide_ik; the builder names them), if any."""
    return {"decided": dict(seg.info["decided"])} if seg.info.get("decided") else {}


def run_clear(act, clear, exc):
    """A skill's failure exit (docs 8.6), when ``exc`` asks for one (motion_state.clearing): the
    plan ``clear(state, exc.clear)`` makes from the State now (skill_plans.plan_clear: the hand
    opened, out of the contact), run as it is -- built just now, nothing to build again.  A failure
    of the exit itself propagates (the skill's failure is its __context__), as the hooks' own
    leave did before the exit was a plan."""
    spec = getattr(exc, "clear", None)
    if clear is None or spec is None:
        return
    why = exc
    plan = clear(observe(act), spec)
    if plan is None or not plan.segments:
        return
    act.log("fail_clear", why=str(why)[:200], segments=[s.name for s in plan.segments], exit=plan.info.get("exit"))
    _run(act, plan, None, {})


def run(act, plan, rebuild, hooks=None, clear=None):
    """Run ``plan`` (motion_state.Plan): before each segment the State is read (observe) and the
    segment checked (holds); one that does not hold has the rest of the plan built again from here
    by ``rebuild(state, segment name, prior) -> Plan | Failure`` -- the skill's builder, the one the
    park search used; ``prior`` the plan as it stands, its decisions kept where they still hold
    (decide_ik) -- and a rest that cannot be built fails the skill (SkillFailure, no fallback).
    ``act``: the motion_state.Actuator (the rig).  ``rebuild`` None: a segment that does not hold
    fails the skill (a plan nobody can build again, docs 8.8).
    ``hooks``: {segment name: {"around": context factory, "before": fn(act), "after": fn(act)}},
    the skill's own steps between segments (the grasp judged, the load registered as held) -- they
    judge, register and log; they do not move the robot.  ``clear``: the skill's failure exit
    ((state, what) -> Plan | None, run_clear), run when a hook fails asking for it
    (motion_state.clearing), before the failure is raised.  Returns the segments run."""
    try:
        return _run(act, plan, rebuild, hooks or {})
    except Exception as exc:
        run_clear(act, clear, exc)
        raise


def _run(act, plan, rebuild, hooks):
    segs, done, i = list(plan.segments), [], 0
    decisions = dict(plan.decisions)
    while i < len(segs):
        seg = segs[i]
        state = observe(act)
        why = holds(act.arm_kin(seg.info.get("side", "right")), state, seg)
        if why is not None:
            if rebuild is None:
                raise SkillFailure(f"{seg.name}: {why}")
            # the plan as it stands: a copy, the decisions as of now (run's own dict goes on changing)
            name = seg.name
            new = rebuild(state, name, replace(plan, segments=tuple(segs), decisions=dict(decisions)))
            if isinstance(new, Failure):
                act.log("segment", target=name, reused=False, why=why, rebuilt=None)
                raise SkillFailure(f"{name}: {why}; built again from here: {new.why}")
            segs = segs[:i] + list(new.segments)
            decisions.update(new.decisions)
            seg = segs[i]
            # the rebuilt segment run now has no event of its own: how it was decided goes here
            act.log("segment", target=name, reused=False, why=why, rebuilt=[s.name for s in new.segments],
                    **_how_decided(seg))
        else:
            act.log("segment", target=seg.name, reused=True, kind=seg.kind, waypoints=len(seg.qs),
                    how=seg.info.get("how"), **_how_decided(seg))
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
