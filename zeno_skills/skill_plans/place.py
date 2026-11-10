"""The place's plan (docs/MOTION_ARCHITECTURE.md section 6, place)."""

from __future__ import annotations

import time

import numpy as np

from ..clearance import Allow
from ..motion_state import Failure, Plan, Segment, Spec, decisions_of, released, with_width
from ..primitives import LEAVE_GAP, JointSet, contact_extent, decide_ik, free_leg, off_support, query, straight
from ._common import FREE_HAND, FREE_LOAD, _move, _reach, held_frame

PLACE_STAGES = ("place_reach", "place_down", "place_release", "place_pull_out", "tuck", "place_settle")
PLACE_RELAY = "place_reach"   # the decision the park search's ranking IK solves for (park_search.Problem.relay)
SETTLE_TICKS = 90           # physics ticks the object let go settles before the place is judged (inherited, unmeasured)


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


def plan_place(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start="place_reach", prior=None,
               step=0.003, obj=None):
    """The set-down of what the hand holds at (p, R) from ``state``: the free leg to the set-down's
    start (the load's tilt held; the set-down's length set_down_length, from q_p, the solution of
    (p, R) decide_ik decides), the set-down straight down, let go (the load falls LEAVE_GAP onto the
    support: released, the hand opened), the pull-out of length out_len along u_out (the gripper
    axis back; the fingers may touch what they let go, the rest of the arm may not: Spec.touch), the
    tuck to the first free of ``rest_goals`` (JointSet: the fold, the hanging posture), the wait the
    object settles in.  ``prior`` (decisions_of): the decision to keep -- place_reach, the set-down
    pose's solution q_p (the park search's ranking solution, or a plan's own: where its set-down
    ends; the tuck is chosen again every time).  ``obj``: the object
    set down (default: what the state's hand holds) -- given, a plan built again after the release
    (the hand holds nothing then) lets the fingers touch it as the first one did.  From ``start``
    on.  Plan (its decisions) or Failure, info["stage_s"] the time per stage."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_place(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start, decisions_of(prior), step,
                           obj)


def release_spec(side, obj):
    """The release and the pull-out: the open fingers may touch the object they let go (it may
    settle against one: a rim-held cup pivots onto the finger inside it, T13) -- a contact the
    monitor records, not a failure (11-08) -- the rest of the arm may not."""
    if obj is None:
        return FREE_HAND
    return Spec(allow=Allow(hand=side, links="fingers", touch=(obj,),
                            reason="release / pull-out: the open fingers may touch the object they let go"),
                fingers=True, exempt=False, touch=(obj,))


def _plan_place(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start, prior, step, obj=None):
    i0 = PLACE_STAGES.index(start)
    p, R = np.asarray(p, float), np.asarray(R, float)
    q = state.q(kin.side)
    held = state.held(kin.side)
    obj = obj if obj is not None else (None if held is None else held.name)
    segs, s, times, decided = [], state, {}, {}
    down = np.array([0.0, 0.0, -1.0])
    for stage in PLACE_STAGES[i0:]:
        t0 = time.time()
        if stage == "place_reach":
            d = decide_ik(kin, s, FREE_LOAD, p, R, prior.get(stage), seeds=(q,))
            if d is None:
                return Failure("no collision-free IK at the set-down pose", stage, {"stage_s": times})
            q_p, how = d
            L, why = set_down_length(kin, s, FREE_LOAD, q_p)
            if L is None:
                return Failure(f"set-down length: {why}", stage, {"stage_s": times})
            # the planner's joint goal for the set-down's start: q_p's branch, up the straight (kinematic)
            scene, kin.scene = kin.scene, None
            try:
                line = kin.cart_path(np.asarray(q_p, float), p + L * np.array([0.0, 0.0, 1.0]), R, step=0.004)[0]
            finally:
                kin.scene = scene
            start_q = line[-1] if line else None
            seg = _reach(kin, s, FREE_LOAD, p, R, down, L, q, start_q, stage, step, decision="set_down_start")
            if not isinstance(seg, Failure):
                seg = _move(seg, steps_per_wp=8, smooth=True, set_down_m=L,
                            decided={**seg.info.get("decided", {}), "place_reach": how})
        elif stage == "place_down":
            seg = straight(kin, s, FREE_LOAD, p, R, stage, step=step, q_from=q)
            if not isinstance(seg, Failure):
                seg = _move(seg, steps_per_wp=8, smooth=True)
                # place_reach: the set-down pose's solution as the plan reaches it -- the set-down's
                # end, not q_p where the leg above went straight from elsewhere (_reach)
                decided["place_reach"] = seg.q_end
        elif stage == "place_release":
            seg = Segment(stage, release_spec(kin.side, obj), q, kind="action", action=("grip", float(pre_open), 70, True))
            if held is not None:
                T = held_frame(kin, q, held)
                T[2, 3] -= LEAVE_GAP                 # let go, it falls the gap onto the support
                s = released(s, kin.side, held.name, T)
            s = with_width(s, kin.side, pre_open)    # the hand opened to the grasp's width
        elif stage == "place_pull_out":
            # back along the gripper axis, a finger's length (release_spec: the fingers may touch obj)
            p0, R0 = kin.tcp(q)
            u = np.asarray(u_out, float) / np.linalg.norm(u_out)
            seg = straight(kin, s, release_spec(kin.side, obj), p0 + out_len * u, R0, stage, step=0.004, q_from=q)
            seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=3, smooth=True)
        elif stage == "tuck":   # the first free of the fold, hanging -- chosen again at every build: the
            # last motion, it binds no segment after it (docs 8.1), and the fold is preferred whenever free
            seg = free_leg(kin, s, FREE_HAND, JointSet(tuple(np.asarray(g, float) for g in rest_goals)), stage,
                           q_from=q)
        else:                                               # place_settle: the world settles, nothing moves
            seg = Segment(stage, Spec(), q, kind="action", action=("wait", SETTLE_TICKS))
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(segs), info={"stage_s": times}, decisions=decided)
