"""The place's plan (docs/MOTION_ARCHITECTURE.md section 6, place)."""

from __future__ import annotations

import time

import numpy as np

from ..clearance import Allow
from ..motion_state import Aim, Failure, Plan, Segment, Spec, aim_pose, decisions_of, released, with_width
from ..primitives import (LEAVE_GAP, TARGET_TOL, TARGET_TURN, JointSet, contact_extent, decide_ik, free_leg,
                          off_support, query, straight)
from ._common import FREE_HAND, FREE_LOAD, _aimed, _kept, _move, _reach, held_frame

PLACE_STAGES = ("place_arrive", "place_reach", "place_down", "place_release", "place_landed", "place_pull_out", "tuck",
                "place_settle")
PLACE_ANCHORS = ("place_arrive", "place_landed")   # the base and the hold as they are; where it landed (docs 8.2)
PLACE_RELAY = "place_reach"   # the decision the park search's ranking IK solves for (park_search.Problem.relay)
# (m, rad) the set-down's start and end may come further off their pose than when built (the hold
# moved in the hand, the base stopped off its park) and still hold: the tolerance the set-down is
# judged by (TARGET_TOL, skills.PICK_REACH_TOL) -- less sets the load down a few mm off, no problem
# (a pick is stricter: pick.PICK_TOL)
PLACE_TOL = (TARGET_TOL, TARGET_TURN)
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


def plan_place(kin, state, goal, pre_open, out_len, rest_goals, start="place_arrive", prior=None,
               step=0.003, obj=None):
    """The set-down of what the hand holds with its box frame at the world pose ``goal`` (4x4) from
    ``state``: the set-down pose (p, R) the TCP that puts it there through the hold the State has
    (Aim, aim_pose: the hold as it is now, in the search and every rebuild alike).  The anchor where
    it arrives (the base and the hold as they are); the free leg to the set-down's start (the load's
    tilt held; the set-down's length set_down_length, from q_p, the solution of (p, R) decide_ik
    decides) and the set-down straight down, both carrying the Aim, the pose they were built for and
    PLACE_TOL (primitives.holds checks them again); let go (the load falls LEAVE_GAP onto the
    support: released, the hand opened); the anchor where it landed; the pull-out of length out_len
    back along the set-down pose's gripper axis (built after the release: the axis where the hand
    let go; the fingers may touch what they let go, the rest of the arm may not: Spec.touch); the
    tuck to the first free of ``rest_goals`` (JointSet: the fold, the hanging posture); the wait the
    object settles in.  ``prior``: a Plan (run's rebuild) has each of its motions but the tuck kept
    as it is while it still holds from here (_kept, docs 8.3), its decision tried first for the
    rest; else the decision to keep (decisions_of: the park search's ranking solution) --
    place_reach, the set-down pose's solution q_p (where a plan's set-down ends).  The tuck is no
    decision: chosen again whenever it is built.  ``obj``: the object set down (default: what the
    state's hand holds) -- given, a plan built again after the release (the hand holds nothing
    then) lets the fingers touch it as the first one did.  From ``start`` on.  Plan (its
    decisions) or Failure, info["stage_s"] the time per stage."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_place(kin, state, goal, pre_open, out_len, rest_goals, start, prior, step, obj)


def release_spec(side, obj):
    """The release and the pull-out: the open fingers may touch the object they let go (it may
    settle against one: a rim-held cup pivots onto the finger inside it, T13) -- a contact the
    monitor records, not a failure (11-08) -- the rest of the arm may not."""
    if obj is None:
        return FREE_HAND
    return Spec(allow=Allow(hand=side, links="fingers", touch=(obj,),
                            reason="release / pull-out: the open fingers may touch the object they let go"),
                fingers=True, exempt=False, touch=(obj,))


def _plan_place(kin, state, goal, pre_open, out_len, rest_goals, start, prior_plan, step, obj=None):
    i0 = PLACE_STAGES.index(start)
    prior = decisions_of(prior_plan)
    q = state.q(kin.side)
    held = state.held(kin.side)
    obj = obj if obj is not None else (None if held is None else held.name)
    aim = aimed = None
    if held is not None:
        aim = Aim(held.name, np.asarray(goal, float), held=True, side=kin.side)
        aimed = aim_pose(state, aim)
    if aimed is None and i0 <= PLACE_STAGES.index("place_down"):
        return Failure("nothing in the hand to set down", start)
    p, R = aimed if aimed is not None else (None, None)
    segs, s, times, decided = [], state, {}, {}
    down = np.array([0.0, 0.0, -1.0])
    for stage in PLACE_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "tuck" else None
        if stage in PLACE_ANCHORS:
            seg = Segment(stage, Spec(), q, kind="anchor")
        elif stage == "place_reach" and kept:
            seg = kept
        elif stage == "place_reach":
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
                seg = _aimed(kin, seg, aim, aimed, PLACE_TOL, steps_per_wp=8, smooth=True, set_down_m=L,
                             decided={**seg.info.get("decided", {}), "place_reach": how})
        elif stage == "place_down":
            seg = kept or straight(kin, s, FREE_LOAD, p, R, stage, step=step, q_from=q)
            if not isinstance(seg, Failure):
                seg = kept or _aimed(kin, seg, aim, aimed, PLACE_TOL, steps_per_wp=8, smooth=True)
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
            # back along the gripper axis, a finger's length (release_spec: the fingers may touch
            # obj): the set-down pose's, else (built again after the release: nothing held to derive
            # it from) the axis where the hand let go
            p0, R0 = kin.tcp(q)
            u = (R if R is not None else R0)[:, 2]
            seg = kept or straight(kin, s, release_spec(kin.side, obj), p0 + out_len * u, R0, stage, step=0.004,
                                   q_from=q)
            seg = seg if isinstance(seg, Failure) or kept else _move(seg, steps_per_wp=3, smooth=True)
        elif stage == "tuck":   # the first free of the fold, hanging -- made again whenever it is built,
            # never kept: the last motion, it binds no segment after it (docs 8.1), and the fold is
            # preferred whenever free (a kept one would ride on what was free when it was built)
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
