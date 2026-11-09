"""The place's plan (docs/MOTION_ARCHITECTURE.md section 6, place)."""

from __future__ import annotations

import numpy as np

from ..clearance import Allow
from ..motion_state import Failure, Plan, Segment, Spec, released, with_width
from ..primitives import LEAVE_GAP, Joint, contact_extent, free_leg, off_support, query, straight
from ._common import FREE_HAND, FREE_LOAD, _move, _reach, held_frame

PLACE_STAGES = ("place_reach", "place_down", "place_release", "place_pull_out", "tuck")


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
               step=0.003, q_seed=None):
    """The set-down of what the hand holds at (p, R) from ``state``: the free leg to the set-down's
    start (the load's tilt held; the set-down's length set_down_length, from ``q_p``, the park
    search's solution of (p, R), or one solved here -- ``q_seed`` first among its seeds), the
    set-down straight down, let go (the load
    falls LEAVE_GAP onto the support: released, the hand opened), the pull-out of length out_len
    along u_out (the gripper axis back; the fingers may touch what they let go, the rest of the arm
    may not: Spec.touch), the tuck to the first free of ``rest_goals`` (the fold, the hanging
    posture).  From ``start`` on.  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_place(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start, q_p, step, q_seed)


def _plan_place(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start, q_p, step, q_seed=None):
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
                    q_p, ok = kin.ik_global(p, R, seeds=([q_seed] if q_seed is not None else []) + [q])
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
            # back along the gripper axis, a finger's length; the fingers may touch what they let go
            # (it may settle against one: a rim-held cup pivots onto the finger inside it, T13) -- a
            # contact the monitor records, not a failure (11-08) -- the rest of the arm may not
            p0, R0 = kin.tcp(q)
            u = np.asarray(u_out, float) / np.linalg.norm(u_out)
            touch = () if held is None else (held.name,)
            spec = FREE_HAND if not touch else Spec(
                allow=Allow(hand=kin.side, links="fingers", touch=touch,
                            reason="pull-out: the open fingers may touch the object they let go"),
                fingers=True, exempt=False, touch=touch)
            seg = straight(kin, s, spec, p0 + out_len * u, R0, stage, step=0.004, q_from=q)
            seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=3, smooth=True)
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
