"""Skill plans (docs/MOTION_ARCHITECTURE.md section 6): the primitives chained in a skill's order,
each segment from where the one before really ends, the State moved on between them (the hand
closed on the load, the load let go).  The park search builds a plan at each candidate park, the
execution runs it and builds the rest again from where it stands when a segment no longer holds
(run.run) -- both with these functions.  They know no simulator: what is skill-specific (the
grasp, the carry goal set, the approach length) comes in as arguments."""

from __future__ import annotations

import numpy as np

from .clearance import FREE, LEAVE_CONTACT, closing
from .motion_state import Failure, Held, Plan, Segment, Spec, holding, released, with_width
from .primitives import (LEAVE_GAP, ON_LINE, Pose, Joint, contact_extent, contact_segment, free_leg, in_world,
                         near_world, off_support, query, straight)

FREE_HAND = Spec(fingers=True, exempt=False)                  # free space, the fingers in, nothing exempt
FREE_LOAD = Spec(fingers=True, exempt=False, hold_tilt=True)  # ...with a load in the hand, its tilt held
PICK_STAGES = ("pick_open", "pick_reach", "pick_grasp", "pick_close", "pick_lift", "carry_in")
PLACE_STAGES = ("place_reach", "place_down", "place_release", "place_pull_out", "tuck")
TOUCHING = {"near_world": near_world, "off_support": off_support, "in_world": in_world}


def T_of(R, p):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, p
    return T


def _on_line(kin, q, s, u, L):
    """The TCP at q already on the straight s -> s + L u (before its end)."""
    d = kin.tcp(np.asarray(q, float))[0] - s
    along = float(d @ u)
    return L >= ON_LINE and -1e-3 <= along <= L + 1e-3 and np.linalg.norm(d - along * u) < ON_LINE


def _reach(kin, state, spec, p, R, u, L, q_from, q_hint, name, step):
    """The free leg to the start of the straight of length L along u into (p, R): none when the
    TCP is on it already; else to its start, a pose (q_hint the planner's joint goal)."""
    if _on_line(kin, q_from, p - L * u, u, L):
        return Segment(name, spec, q_from, (), info={"how": "on the straight"})
    return free_leg(kin, state, spec, Pose(p - L * u, R, q_hint), name, step=step, q_from=q_from)


def _move(seg, **info):
    """seg with how it is executed added to its info (steps per waypoint, smooth)."""
    return Segment(seg.name, seg.spec, seg.q_from, seg.qs, seg.kind, seg.target, seg.action, {**seg.info, **info})


def _contact(kin, state, spec, u, touching, name, step, q_from, **info):
    ext = contact_extent(kin, state, spec, u, TOUCHING[touching], name, step=step, q_from=q_from)
    if isinstance(ext, Failure):
        return ext
    return _move(contact_segment(spec, ext, name), u=np.asarray(u, float), touching=touching, step=step, **info)


def held_frame(kin, q, held):
    """World pose of a held object's box frame with the hand at q."""
    p, R = kin.tcp(np.asarray(q, float))
    return T_of(R, p) @ np.asarray(held.T_tcp_obj, float)


# ------------------------------------------------------------------------------------- pick
def plan_pick(kin, state, grasp, u, L, carry_goals, start="pick_open", q_hint=None, step=0.003):
    """The pick of grasp = {name, p, R, pre_open, kind} from ``state``: open the hand, the free leg
    to the reach-in's start (``q_hint``: the park search's solution of it), the reach-in straight
    of length L along u, close, the lift off the support (contact_extent, off_support), the free
    leg to the carry pose (``carry_goals(state, q) -> (PoseSet, {step, steps_per_wp, smooth})``, the
    load's tilt held).  From
    ``start`` on (the stages before it done).  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_pick(kin, state, grasp, u, L, carry_goals, start, q_hint, step)


def _plan_pick(kin, state, grasp, u, L, carry_goals, start, q_hint, step):
    i0 = PICK_STAGES.index(start)
    name, p, R = grasp["name"], np.asarray(grasp["p"], float), np.asarray(grasp["R"], float)
    u = np.asarray(u, float) / np.linalg.norm(u)
    q = state.q(kin.side)
    segs = []
    s = state
    for stage in PICK_STAGES[i0:]:
        if stage == "pick_open":
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", float(grasp["pre_open"]), 40, False))
        elif stage == "pick_reach":
            seg = _reach(kin, s, FREE_HAND, p, R, u, L, q, q_hint, stage, step)
            seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=4, smooth=True)
        elif stage == "pick_grasp":
            seg = straight(kin, s, FREE_HAND, p, R, stage, step=step, q_from=q)
            seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=4, smooth=True)
        elif stage == "pick_close":
            seg = Segment(stage, Spec(allow=closing(name)), q, kind="action", action=("grip", 0.0, None, True))
            if name in s.objects:
                T_hand = T_of(kin.tcp(q)[1], kin.tcp(q)[0])
                s = holding(s, kin.side, Held(name, np.linalg.inv(T_hand) @ s.objects[name], grasp.get("kind", "pinch")))
        elif stage == "pick_lift":
            seg = _contact(kin, s, Spec(allow=LEAVE_CONTACT), [0.0, 0.0, 1.0], "off_support", stage, 0.002, q,
                           steps_per_wp=6, smooth=True)
        else:                                               # carry_in
            with query(kin, s, FREE_LOAD):
                goals, how = carry_goals(s, q)
            seg = free_leg(kin, s, FREE_LOAD, goals, stage, step=how.get("step", 0.01), q_from=q) \
                if goals.goals else Failure("no carry goal", stage)
            seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=how.get("steps_per_wp", 4),
                                                             smooth=how.get("smooth", False))
        if isinstance(seg, Failure):
            return seg
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(segs))


# ------------------------------------------------------------------------------------- place
def set_down_length(kin, state, spec, q_p, step=0.004):
    """The straight a load is set down along: pick's lift off the same support reversed, measured
    from where that lift would start -- the load LEAVE_GAP lower, on the support -- with
    off_support; the part of it above q_p.  (length, None) or (None, why)."""
    q_p = np.asarray(q_p, float)
    p, R = kin.tcp(q_p)
    with query(kin, state, spec):
        scene, kin.scene = kin.scene, None
        try:
            down, ok = kin.cart_path(q_p, p - np.array([0.0, 0.0, LEAVE_GAP]), R, step=step)
        finally:
            kin.scene = scene
    if not ok or not down:
        return None, "no IK LEAVE_GAP below the set-down pose"
    ext = contact_extent(kin, state, spec, [0.0, 0.0, 1.0], off_support, "set_down", step=step, q_from=down[-1])
    if isinstance(ext, Failure):
        return None, ext.why
    L = ext.length - LEAVE_GAP
    if L <= 0:
        return None, "the set-down has no length above its pose"
    return L, None


def plan_place(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start="place_reach", q_p=None,
               step=0.003):
    """The set-down of what the hand holds at (p, R) from ``state``: the free leg to the set-down's
    start (the load's tilt held; the set-down's length set_down_length, from ``q_p``, the park
    search's solution of (p, R), or one solved here), the set-down straight down, let go (the load
    falls LEAVE_GAP onto the support: released), the pull-out of length out_len along u_out (the
    gripper axis back; a hand that starts in the load -- in the model after the release -- first
    out of that contact, near_world), the tuck to the first free of ``rest_goals`` (the fold, the
    hanging posture).  From ``start`` on.  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_place(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start, q_p, step)


def _plan_place(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start, q_p, step):
    i0 = PLACE_STAGES.index(start)
    p, R = np.asarray(p, float), np.asarray(R, float)
    q = state.q(kin.side)
    held = state.held(kin.side)
    segs, s = [], state
    down = np.array([0.0, 0.0, -1.0])
    for stage in PLACE_STAGES[i0:]:
        if stage == "place_reach":
            if q_p is None:
                with query(kin, s, FREE_LOAD):
                    q_p, ok = kin.ik_global(p, R, seeds=[q])
                if not ok:
                    return Failure("no collision-free IK at the set-down pose", stage)
            L, why = set_down_length(kin, s, FREE_LOAD, q_p)
            if L is None:
                return Failure(f"set-down length: {why}", stage)
            # the planner's joint goal for the set-down's start: q_p's branch, up the straight (kinematic)
            scene, kin.scene = kin.scene, None
            try:
                line = kin.cart_path(np.asarray(q_p, float), p + L * np.array([0.0, 0.0, 1.0]), R, step=0.004)[0]
            finally:
                kin.scene = scene
            start_q = line[-1] if line else None
            seg = _reach(kin, s, FREE_LOAD, p, R, down, L, q, start_q, stage, step)
            seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=8, smooth=True, set_down_m=L)
        elif stage == "place_down":
            seg = straight(kin, s, FREE_LOAD, p, R, stage, step=step, q_from=q)
            seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=8, smooth=True)
        elif stage == "place_release":
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", float(pre_open), 70, True))
            if held is not None:
                T = held_frame(kin, q, held)
                T[2, 3] -= LEAVE_GAP                 # let go, it falls the gap onto the support
                s = released(s, kin.side, held.name, T)
            s = with_width(s, kin.side, pre_open)    # the hand opened to the grasp's width
        elif stage == "place_pull_out":
            p0, R0 = kin.tcp(q)
            u = np.asarray(u_out, float) / np.linalg.norm(u_out)
            with query(kin, s, FREE_HAND):
                stuck = not kin.free(q)
            if stuck:
                # let go, it settled against a finger (a rim-held cup pivots onto the one inside it,
                # T13): out of that contact first, only what the hand touches at its start touched
                seg = _contact(kin, s, Spec(allow=LEAVE_CONTACT), u, "near_world", "place_pull_out_contact", 0.004,
                               q, steps_per_wp=3, smooth=True)
                if isinstance(seg, Failure):
                    return seg
                segs.append(seg)
                q = seg.q_end
            rest = out_len - float((kin.tcp(q)[0] - p0) @ u)
            if rest > ON_LINE:
                seg = straight(kin, s, FREE_HAND, p0 + out_len * u, R0, stage, step=0.004, q_from=q)
                seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=3, smooth=True)
            else:
                continue
        else:                                               # tuck
            with query(kin, s, FREE_HAND):
                goal = next((g for g in rest_goals if kin.free(g)), None)
            seg = Failure("the fold and the hanging posture collide here", stage) if goal is None else \
                free_leg(kin, s, FREE_HAND, Joint(np.asarray(goal, float)), stage, q_from=q)
        if isinstance(seg, Failure):
            return seg
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(segs))
