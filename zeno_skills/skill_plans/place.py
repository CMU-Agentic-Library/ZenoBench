"""The place's plan and the drop's (docs/motion/MOTION_ARCHITECTURE.md section 6, place; docs/skills/drop_hover.md)."""

from __future__ import annotations

import time

import numpy as np

from ..clearance import Allow
from ..motion_state import Aim, Failure, Plan, Segment, Spec, aim_pose, decisions_of, released, with_width
from ..primitives import sided, JointSet, Pose, contact_extent, decide_ik, free_leg, ik_why, off_support, query, straight
from ..tolerances import EDGE_PAD_CLEAR, LEAVE_GAP, NUMERIC_M, PLACE_TOL
from ._common import FREE_HAND, built_so_far, FREE_LOAD, _aimed, _kept, _move, _reach, anchor, held_frame

PLACE_STAGES = ("place_arrive", "place_reach", "place_down", "place_release", "place_landed", "place_clear",
                "place_pull_out", "place_exit", "tuck", "place_settle")
PLACE_ANCHORS = ("place_arrive", "place_landed")   # the base and the hold as they are; where it landed (docs 8.2)
PLACE_RELAY = "place_reach"   # the decision the park search's ranking IK solves for (park_search.Problem.relay)
# PLACE_TOL (m, rad): the set-down's start and end may come further off their pose than when built
# (the hold moved in the hand, the base stopped off its park) and still hold -- less sets the load down
# a few mm off (a pick is stricter: PICK_TOL).  Value and source: tolerances.py
SETTLE_TICKS = 90           # physics ticks the object let go settles before the place is judged (inherited, unmeasured)

DROP_STAGES = ("drop_arrive", "drop_reach", "drop_release", "drop_fall", "tuck")
DROP_RELAY = "drop_reach"   # the decision the park search's ranking IK solves for: the pose over the opening
HOVER_STAGES = ("hover_arrive", "hover_reach")    # the drop's arrive and reach, nothing let go (plan_hover)
HOVER_RELAY = "hover_reach"
_ROLE = {"hover_arrive": "drop_arrive", "hover_reach": "drop_reach"}     # a hover stage: the drop stage it is
DROP_GRIP_TICKS = 40        # physics ticks the hand opens in (inherited: the old drop_into's grip)
DROP_FALL_TICKS = 120       # ...and the load falls clear of the open fingers in before the tuck (inherited: 1 s)


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
               step=0.003, obj=None, on=None, edge_box=None, cavity=None):
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
    then) lets the fingers touch it as the first one did.  ``on``: what it is set down on (the
    release lets it touch that: release_spec).  ``edge_box``: an edge hold (a flat load pinched at its
    thickness, the fingers above and below it) -- the load's box (lo, hi) in its box frame: after it
    landed the open pads are moved along their closing axis only as far as they need to clear it by
    EDGE_PAD_CLEAR (place_clear: it fell the gap, the hand did not), and neither they nor the
    pull-out may touch it, a touch drags it back out with the hand.  ``cavity``: a support inside a cavity
    closed on five sides (a microwave's: annotated cavity_aabb), {"box": its world aabb (6), "out": the unit
    horizontal out of its opening, "load": the load's box (lo, hi) in its box frame} -- the pull-out goes only
    as far as the fingertips need to clear the load (_off_load: a finger's length rose into the cavity's
    ceiling, HAND_PLAN 9d), then place_exit takes the hand out through the opening (_out_of_cavity) before
    the tuck, which could not be planned from inside (cuRobo TRAJOPT, 14 of 26 builds).  From ``start`` on.  Plan (its decisions) or Failure, info["stage_s"] the time per
    stage."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_place(kin, state, goal, pre_open, out_len, rest_goals, start, prior, step, obj, on, edge_box,
                           cavity)


def release_spec(side, obj, on=None):
    """The release and the pull-out: the open fingers may touch the object they let go (it may
    settle against one: a rim-held cup pivots onto the finger inside it, T13) -- a contact the
    monitor records, not a failure (11-08) -- the rest of the arm may not; and the object, still
    the hand's while it opens, may touch ``on`` (the furniture or object it is set down on: it
    falls the last LEAVE_GAP onto it)."""
    if obj is None:
        return FREE_HAND
    return Spec(allow=Allow(hand=side, links="fingers", touch=(obj,), held_on=(on,) if on else (),
                            reason="release / pull-out: the open fingers may touch the object they let go, "
                                   "it what it is set down on"),
                fingers=True, exempt=False, touch=(obj,))


def _pads_clear(kin, state, q, obj, box, name):
    """The straight that gives an edge hold's open pads EDGE_PAD_CLEAR from ``obj`` on both sides along
    their closing axis (Y_link, kinematics.gripper_rot), the load as the State has it (it fell the gap,
    the hand stayed): the least move that does -- none when they clear it already -- or the load centred
    between them when the opening leaves less.  ``box`` (lo, hi): its box in its box frame; each pad
    stands its finger's opening off the TCP, the left finger along +Y_link, the right along -Y_link (the
    URDF's finger axes, both hands) -- each finger as it stands (Hand.fingers: after the release they part
    ways, one pushed 3-9 mm off the other, T27 rice / T14 book left, s11 11-26), else both at the hand's
    width (planned).  Checked, the load an obstacle for all but the fingers: they may touch what they let
    go where the move starts (release_spec: the move takes a pad off it).  None: nothing to move (or the
    load not in the State)."""
    T, hand = state.objects.get(obj), state.hands.get(kin.side)
    if T is None or hand is None:
        return None
    T = np.asarray(T, float)
    lo, hi = (np.asarray(v, float) for v in box)
    p, R = kin.tcp(q)
    y = R[:, 1]
    c = (T @ np.r_[0.5 * (lo + hi), 1.0])[:3]
    half = float(np.abs(T[:3, :3].T @ y) @ (0.5 * (hi - lo)))      # the load's half extent along y
    w, m = float(hand.width), EDGE_PAD_CLEAR
    fl, fr = (w, w) if hand.fingers is None else (float(hand.fingers[0]), float(hand.fingers[1]))
    d = float((c - p) @ y)                                          # its centre off the TCP along y
    least, most = half + m - fr, fl - half - m                      # where d leaves both pads m clear
    mid = 0.5 * (fl - fr)                                           # the load centred between the pads
    s = d - (mid if least > most else min(max(d, least), most))     # the TCP's move along y
    if abs(s) < NUMERIC_M:
        return None
    seg = straight(kin, state, release_spec(kin.side, obj), p + s * y, R, name, step=0.002, q_from=q)
    return seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=3, smooth=True)


def _off_load(kin, state, q, obj, u, box):
    """m along the unit ``u`` (back along the gripper axis) the TCP at ``q`` goes until the fingertips (the
    planner's finger, finger_model_box: their tips below the TCP) stand LEAVE_MARGIN past the top of
    ``obj``'s box (lo, hi) in its box frame along u, the load as the State has it -- 0 when they are past
    it already; None without the load in the State."""
    from ..kinematics import finger_model_box
    from ..tolerances import LEAVE_MARGIN
    T = state.objects.get(obj)
    if T is None:
        return None
    T = np.asarray(T, float)
    lo, hi = (np.asarray(v, float) for v in box)
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    top = float(np.max((corners @ T[:3, :3].T + T[:3, 3]) @ u))
    tips = float(kin.tcp(q)[0] @ u) - finger_model_box()[3]
    return max(0.0, top - tips) + LEAVE_MARGIN


def _out_of_cavity(kin, state, q, cavity, name):
    """The straight out of ``cavity``'s opening (plan_place), horizontal along cavity["out"], as long as the
    arm's collision spheres inside the cavity's box need to pass its open face by LEAVE_MARGIN (their
    radius included) -- the hand at ``q``, checked (FREE_HAND).  None: nothing of the arm inside."""
    from ..primitives import robot_spheres
    from ..tolerances import LEAVE_MARGIN
    b = np.asarray(cavity["box"], float)
    o = np.r_[np.asarray(cavity["out"], float)[:2], 0.0]
    o /= np.linalg.norm(o)
    face = max(float(np.array([x, y, 0.0]) @ o) for x in (b[0], b[3]) for y in (b[1], b[4]))
    need = 0.0
    for x, y, z, r, *_ in robot_spheres(kin, state, FREE_HAND, q):
        c = np.array([x, y, z])
        if np.all(c > b[:3] - r) and np.all(c < b[3:] + r):
            need = max(need, face - float(c @ o) + r)
    if need <= 0.0:
        return None
    p, R = kin.tcp(q)
    seg = straight(kin, state, FREE_HAND, p + (need + LEAVE_MARGIN) * o, R, name, step=0.004, q_from=q)
    return seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=3, smooth=True)


def _plan_place(kin, state, goal, pre_open, out_len, rest_goals, start, prior_plan, step, obj=None, on=None,
                edge_box=None, cavity=None):
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
            seg = anchor(stage, q, s, (obj,) if obj else (), kin.side, stages=PLACE_STAGES)
        elif stage == "place_reach" and kept:
            seg = kept
        elif stage == "place_reach":
            d = decide_ik(kin, s, FREE_LOAD, p, R, prior.get(stage), seeds=(q,))
            if d is None:
                # what the robot penetrates there (ik_why: at the ranking's solution, else a kinematic
                # one), as the pick's reach-in start says it -- the park search keeps it as an example
                seeds = tuple(x for x in (prior.get(stage), q) if x is not None)
                return Failure(f"no collision-free IK at the set-down pose ({ik_why(kin, s, FREE_LOAD, p, R, seeds)})",
                               stage, {"stage_s": times})
            q_p, how = d
            L, why = set_down_length(kin, s, FREE_LOAD, q_p)
            if L is None:
                return Failure(f"set-down length: {why}", stage, {"stage_s": times, "q_relay": q_p})
            # the planner's joint goal for the set-down's start: q_p's branch, up the straight (kinematic)
            scene, kin.scene = kin.scene, None
            try:
                line = kin.cart_path(np.asarray(q_p, float), p + L * np.array([0.0, 0.0, 1.0]), R, step=0.004)[0]
            finally:
                kin.scene = scene
            start_q = line[-1] if line else None
            seg = _reach(kin, s, FREE_LOAD, p, R, down, L, q, start_q, stage, step, decision="set_down_start")
            if isinstance(seg, Failure):
                seg = Failure(seg.why, seg.segment, {**(seg.info or {}), "q_relay": q_p})
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
            seg = Segment(stage, release_spec(kin.side, obj, on), q, kind="action",
                          action=("grip", float(pre_open), 70, True))
            if held is not None:
                T = held_frame(kin, q, held)
                T[2, 3] -= LEAVE_GAP                 # let go, it falls the gap onto the support
                s = released(s, kin.side, held.name, T)
            s = with_width(s, kin.side, pre_open)    # the hand opened to the grasp's width
        elif stage == "place_clear":
            seg = None if edge_box is None else (kept or _pads_clear(kin, s, q, obj, edge_box, stage))
            if seg is None:                     # not an edge hold, or its pads clear the load already
                times[stage] = round(time.time() - t0, 3)
                continue
        elif stage == "place_pull_out":
            # back along the gripper axis, a finger's length (release_spec: the fingers may touch
            # obj; an edge hold: they may not, FREE_HAND): the set-down pose's, else (built again after
            # the release: nothing held to derive it from) the axis where the hand let go
            p0, R0 = kin.tcp(q)
            u = (R if R is not None else R0)[:, 2]
            spec = FREE_HAND if edge_box is not None else release_spec(kin.side, obj)
            L = out_len if cavity is None else _off_load(kin, s, q, obj, u, cavity["load"])
            L = out_len if L is None else L
            seg = kept or straight(kin, s, spec, p0 + L * u, R0, stage, step=0.004, q_from=q)
            seg = seg if isinstance(seg, Failure) or kept else _move(seg, steps_per_wp=3, smooth=True)
        elif stage == "place_exit":
            seg = None if cavity is None else (kept or _out_of_cavity(kin, s, q, cavity, stage))
            if seg is None:                     # in the open, or nothing of the arm inside the cavity
                times[stage] = round(time.time() - t0, 3)
                continue
        elif stage == "tuck":   # the first free of the fold, hanging -- made again whenever it is built,
            # never kept: the last motion, it binds no segment after it (docs 8.1), and the fold is
            # preferred whenever free (a kept one would ride on what was free when it was built)
            seg = free_leg(kin, s, FREE_HAND, JointSet(tuple(np.asarray(g, float) for g in rest_goals)), stage,
                           q_from=q)
        else:                                               # place_settle: the world settles, nothing moves
            seg = Segment(stage, Spec(), q, kind="action", action=("wait", SETTLE_TICKS))
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            # the set-down pose's solution once decided (a debug view shows the arm there: park_search dump)
            q_rel = (seg.info or {}).get("q_relay", decided.get("place_reach"))
            return Failure(seg.why, seg.segment, {"stage_s": times, "partial": built_so_far(segs, kin.side, decided), **({"q_relay": q_rel} if q_rel is not None else {})})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, kin.side) for sg in segs), info={"stage_s": times}, decisions=decided)


def plan_drop(kin, state, goal, pre_open, rest_goals, into, fall, start="drop_arrive", prior=None, step=0.005,
              obj=None):
    """The drop of what the hand holds into the container ``into``, let go with its box frame at the
    world pose ``goal`` (4x4) over the opening, from ``state``: the anchor where it arrives (the base
    and the hold as they are); the free leg there, the load's tilt held, to the solution decide_ik
    decides of the TCP pose the Aim gives through the hold the State has -- carrying the Aim and
    PLACE_TOL, primitives.holds checks it again; let go in the air (the open fingers may touch the
    load, the load the container: release_spec); the wait it falls clear of the fingers in; the tuck
    to the first free of ``rest_goals``.  No set-down and no pull-out: nothing is left between the
    fingers once it falls.  No anchor where it landed: where it comes to rest is not predicted (docs
    8.5) -- the State has it ``fall`` m lower (its lowest point on the container's floor), out of the
    tuck's way; the job judges it inside.  ``prior``: a Plan (run's rebuild) has its reach kept while
    it still holds (_kept), its decision tried first; else the decision to keep (the park search's
    ranking solution).  ``obj``: the object dropped (default: what the state's hand holds).  From
    ``start`` on.  Plan (its decisions) or Failure, info["stage_s"] the time per stage."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_drop(kin, state, goal, pre_open, rest_goals, into, fall, start, prior, step, obj)


def plan_hover(kin, state, goal, start="hover_arrive", prior=None, step=0.005, obj=None):
    """The hover (docs/skills/drop_hover.md): plan_drop's arrive and reach -- the anchor where it arrives, the
    free leg, the load's tilt held, to the solution decide_ik decides of the TCP pose that puts what the hand
    holds with its box frame at ``goal`` (4x4), carrying the Aim and PLACE_TOL -- and nothing let go: the hand
    stays there holding it (HAND_PLAN 9e; the old HoverOverPolicy's one move_to from a park_over park).
    ``prior``, ``start``, ``obj``: as plan_drop's.  Plan or Failure."""
    with query(kin, state, FREE_HAND):
        return _plan_drop(kin, state, goal, None, (), None, 0.0, start, prior, step, obj, stages=HOVER_STAGES)


def _plan_drop(kin, state, goal, pre_open, rest_goals, into, fall, start, prior_plan, step, obj, stages=DROP_STAGES):
    i0 = stages.index(start)
    prior = decisions_of(prior_plan)
    q = state.q(kin.side)
    held = state.held(kin.side)
    obj = obj if obj is not None else (None if held is None else held.name)
    aim = aimed = None
    if held is not None:
        aim = Aim(held.name, np.asarray(goal, float), held=True, side=kin.side)
        aimed = aim_pose(state, aim)
    if aimed is None and (stages is HOVER_STAGES or i0 <= DROP_STAGES.index("drop_release")):
        return Failure("nothing in the hand to drop" if stages is DROP_STAGES else "nothing in the hand to hover",
                       start)
    segs, s, times, decided = [], state, {}, {}
    for stage in stages[i0:]:
        t0 = time.time()
        role = _ROLE.get(stage, stage)
        if role == "drop_arrive":
            seg = anchor(stage, q, s, (obj,) if obj else (), kin.side)
        elif role == "drop_reach":
            seg = _kept(kin, s, q, prior_plan, stage)
            if seg is None:
                p, R = aimed
                d = decide_ik(kin, s, FREE_LOAD, p, R, prior.get(stage), seeds=(q,))
                if d is None:
                    seeds = tuple(x for x in (prior.get(stage), q) if x is not None)
                    return Failure(f"no collision-free IK over the opening ({ik_why(kin, s, FREE_LOAD, p, R, seeds)})",
                                   stage, {"stage_s": times})
                q_p, how = d
                seg = free_leg(kin, s, FREE_LOAD, Pose(p, R, q_p), stage, step=step, q_from=q)
                if not isinstance(seg, Failure):
                    seg = _aimed(kin, seg, aim, aimed, PLACE_TOL, steps_per_wp=5, smooth=True, decided={stage: how})
            if not isinstance(seg, Failure):
                decided[stage] = seg.q_end
        elif stage == "drop_release":
            seg = Segment(stage, release_spec(kin.side, obj, into), q, kind="action",
                          action=("grip", float(pre_open), DROP_GRIP_TICKS, False))
            if held is not None:
                T = held_frame(kin, q, held)
                T[2, 3] -= fall                     # it falls onto the container's floor, out of the tuck's way
                s = released(s, kin.side, held.name, T)
            s = with_width(s, kin.side, pre_open)    # the hand opened to the grasp's width
        elif stage == "drop_fall":                  # it falls clear of the open fingers, nothing moves
            seg = Segment(stage, Spec(), q, kind="action", action=("wait", DROP_FALL_TICKS))
        else:   # the tuck: made again whenever it is built, never kept (plan_place's)
            seg = free_leg(kin, s, FREE_HAND, JointSet(tuple(np.asarray(g, float) for g in rest_goals)), stage,
                           q_from=q)
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times, "partial": built_so_far(segs, kin.side, decided)})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, kin.side) for sg in segs), info={"stage_s": times}, decisions=decided)


RELEASE_STAGES = ("release_open", "release_let_go", "release_pull_out")
RELEASE_TICKS = 60      # physics ticks the hand opens in, gradually (inherited: the old ReleaseInPlacePolicy's)


def plan_release(kin, state, pre_open, out_len, start="release_open", prior=None, obj=None, step=0.004):
    """release (HAND_PLAN 9f): let go of what ``kin``'s hand holds where it is -- the hand opened to
    ``pre_open`` (the fingers may touch what they let go: release_spec), the anchor where it let go -- and the pull-out
    back along the gripper axis
    as far as contact_extent measures (the fingers still allowed on it; ``out_len`` unused, kept for the callers).  Both built before
    anything moves: a pull-out that cannot be made fails the release with the hand still closed (the old
    ReleaseInPlacePolicy opened first and logged a short back-off).  ``obj``: what it lets go (default what the
    State's hand holds; given, a plan built again after the opening).  ``start`` / ``prior``: run's rebuild.
    Plan or Failure."""
    with query(kin, state, FREE_HAND):
        held = state.held(kin.side)
        obj = obj if obj is not None else (None if held is None else held.name)
        if obj is None and start == "release_open":
            return Failure("nothing in the hand to release", start)
        q = np.asarray(state.q(kin.side), float)
        spec = release_spec(kin.side, obj)
        segs, s = [], state
        for stage in RELEASE_STAGES[RELEASE_STAGES.index(start):]:
            if stage == "release_open":
                seg = Segment(stage, spec, q, kind="action", action=("grip", float(pre_open), RELEASE_TICKS, True))
                if held is not None:
                    s = released(s, kin.side, held.name, held_frame(kin, q, held))
                s = with_width(s, kin.side, pre_open)
            elif stage == "release_let_go":
                # where an error comes in (docs 8.2, rule 9: arrival, grasp, release): what it let go stands where it
                # does; run builds the pull-out again from the State there when it no longer holds
                seg = anchor(stage, q, s, (obj,) if obj else (), kin.side)
            else:
                # back along the gripper axis as far as contact_extent measures (LEAVE_GAP clear of what it let go and
                # everything else, then LEAVE_MARGIN; rule 4) -- a finger's length had no IK where a handover's giving
                # hand let go (P06 11-25)
                from ._common import _contact
                _, R0 = kin.tcp(q)
                seg = _contact(kin, s, spec, np.asarray(R0, float)[:, 2], "near_world", stage, step, q,
                               steps_per_wp=3, smooth=True)
            if isinstance(seg, Failure):
                return seg
            segs.append(seg)
            q = seg.q_end
        return Plan(tuple(sided(sg, kin.side) for sg in segs))
