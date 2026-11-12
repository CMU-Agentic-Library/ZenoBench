"""Contact skills (docs/MOTION_ARCHITECTURE.md section 6, contact): an object pushed or dragged across its
support by the closed fingers -- plan_slide.  Its trajectory is a task segment over the hand's travel
(primitives.Pushed: the object along n from where the fingers meet it, the hand rigid in its frame), checked
whole with the object where each step of the push puts it, as far as the arm reaches from the park; where
the object really went is read at the anchor after it."""

from __future__ import annotations

import time

import numpy as np

from ..clearance import LEAVE_CONTACT
from ..motion_state import Aim, Failure, Plan, Segment, Spec, aim_pose, decisions_of, with_arm, with_width
from ..primitives import JointSet, Script, free_leg, pushed, query, scripted, sided, straight
from ..tolerances import SLIDE_TOL
from ._common import FREE_HAND, _aimed, _contact, _kept, _move, _reach, anchor, may_touch

SLIDE_STAGES = ("slide_arrive", "slide_close_hand", "slide_reach", "slide_down", "slide_in", "slide_push",
                "slide_moved", "slide_leave", "tuck", "slide_open_hand")
SLIDE_ANCHORS = ("slide_arrive", "slide_moved")   # the base and the object; where the push left it
SLIDE_RELAY = "slide_end"     # what the park search's ranking IK solves (park_search.Problem.relay): the push's
                              # end -- or, where no park reaches all of it, the farthest along it a park's arm
                              # gets (Problem.relay_from); the descent's start alone ranked parks from which 14 of
                              # 15 pushes ran out of IK along the way (T05 notebook 11-12).  A seed, not a
                              # decision: its solution seeds slide_reach's IK (decide_ik's first seed) on that branch
SLIDE_OPEN = 0.04             # m per finger the hand is left open at the end (skills' old push: for what comes next)
SLIDE_STEP = 0.02             # m of travel between the push's checked samples (docs 2.4: by travel; not measured)


def slide_travel(plan):
    """m a plan's push moves its object -- the hand's travel less its lag: the plan's prediction -- or
    None (no push in it)."""
    seg = next((sg for sg in getattr(plan, "segments", ()) if sg.name == "slide_push"), None)
    if seg is None:
        return None
    sc = seg.info["script"]
    return sc.coupling.travel(sc.s1)


def plan_slide(kin, state, push, rest_goals, start="slide_arrive", prior=None, step=0.003):
    """The object push["obj"] pushed along the horizontal unit push["n"] by ``kin``'s closed hand from
    ``state``, as far as the arm reaches from here: push = {obj, T_obj_tcp (the push point: the TCP in
    the object's box frame where the push starts), n, d (m the hand runs along n at most), lag (m it runs
    before the object moves: primitives.Pushed), least (m the object must move on this leg: less fails
    the plan), above (m: the hand comes straight down from this far above where it lands), back (m: it
    lands this far behind the push point along -n, the push-in closes it; 0: on it -- a drag pressing on
    the top)}:

        slide_arrive      anchor: the base and the object as they are
        slide_close_hand  close the fingers: one blunt tip
        slide_reach       the free leg to ``above`` over where the descent lands (decide_ik: _reach)
        slide_down        the straight down
        slide_in          the straight along n onto the push point (none when back is 0)
        slide_push        the task segment (Script, primitives.Pushed, carry "arm"): the hand along n as
                          far as the arm has IK, up to push["d"] (scripted's reach: the leg is measured,
                          not set), the object moving from s = lag on; the fingers may touch it
        slide_moved       anchor: where the object went
        slide_leave       out of the contact: the straight away from what the fingers touch -- up and off
                          the pushed face at 45 deg (a drag: up off the top) -- as far as contact_extent
                          measures (near_world: LEAVE_GAP clear, then LEAVE_MARGIN); none when nothing is
                          touched
        tuck              the first free of ``rest_goals`` (JointSet; never kept)
        slide_open_hand   the hand opened for what comes next

    The reach, the descent and the push-in carry the Aim (the push point in the object's frame) and
    SLIDE_TOL (primitives.holds checks them again).  From ``start`` on; ``prior`` as plan_pick's (a
    Plan: its motions that still hold kept, its decisions tried first; else the park search's ranking
    solution of the push's end, SLIDE_RELAY) -- slide_reach, the descent's start.  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_slide(kin, state, push, rest_goals, start, prior, step)


def _plan_slide(kin, state, push, rest_goals, start, prior_plan, step):
    i0 = SLIDE_STAGES.index(start)
    prior = decisions_of(prior_plan)
    obj, side = push["obj"], kin.side
    n = np.asarray(push["n"], float)
    up = np.array([0.0, 0.0, 1.0])
    back, above = float(push["back"]), float(push["above"])
    aim = Aim(obj, np.asarray(push["T_obj_tcp"], float), side=side)
    aimed = aim_pose(state, aim)
    if aimed is None and i0 <= SLIDE_STAGES.index("slide_push"):
        return Failure(f"{obj} is not in the State", start)
    p, R = aimed if aimed is not None else (None, None)
    land = None if p is None else p - back * n                     # where the descent lands
    on_it = may_touch(side, obj, "the closed fingers onto the object they push")
    # out of the contact: away from both things the fingers touch -- the pushed face (-n) and the support
    # (up) -- or off a drag's top
    out = up - n if back > 0 else up
    out = out / np.linalg.norm(out)
    q, s = state.q(side), state
    segs, decided, times = [], {}, {}
    for stage in SLIDE_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "tuck" else None
        if stage in SLIDE_ANCHORS:
            seg = anchor(stage, q, s, (obj,), side)
        elif stage == "slide_close_hand":
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", 0.0, 30, False))
            s = with_width(s, side, 0.0)
        elif stage == "slide_reach":
            seg = kept or _reach(kin, s, FREE_HAND, land, R, -up, above, q, prior.get(stage, prior.get(SLIDE_RELAY)),
                                 stage, step)
            if not isinstance(seg, Failure):
                seg = kept or _aimed(kin, seg, aim, aimed, SLIDE_TOL, steps_per_wp=3)
                if seg.qs:                                  # the descent's start as the plan reaches it
                    decided[stage] = seg.q_end
        elif stage == "slide_down":
            spec = FREE_HAND if back > 0 else on_it        # a drag lands on the object, a push behind it
            seg = kept or straight(kin, s, spec, land, R, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _aimed(kin, seg, aim, aimed, SLIDE_TOL, steps_per_wp=4)
        elif stage == "slide_in":
            if back <= 0:
                continue
            seg = kept or straight(kin, s, on_it, p, R, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _aimed(kin, seg, aim, aimed, SLIDE_TOL, steps_per_wp=4)
        elif stage == "slide_push":
            T0 = s.objects.get(obj)
            if T0 is None:
                return Failure(f"{obj} is not in the State", stage, {"stage_s": times})
            script = Script(pushed(obj, T0, n, push["lag"]), 0.0, float(push["d"]), step=SLIDE_STEP, carry="arm")
            # from the arm as the plan has it (q: on the push point), not as the State it moves on had it;
            # kept as it is while it holds (_kept: the IK continuation made again comes out a little
            # otherwise, and what follows from its end with it)
            seg = kept or scripted(kin, with_arm(s, q, side), on_it, script, stage, arm_step=step, reach=True)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4)
            if not isinstance(seg, Failure):
                sc = seg.info["script"]             # the one it runs (a kept one's own), ending where the arm got
                gone = sc.coupling.travel(sc.s1)
                if gone < float(push["least"]):
                    seg = Failure(f"the arm pushes {obj} only {gone:.3f} m from here (the hand to s={sc.s1:.3f}, "
                                  f"{float(push['least']):.3f} m asked at least)", stage)
                else:
                    s = sc.coupling.moved(s, sc.s1)
        elif stage == "slide_leave":
            seg = kept or _contact(kin, s, Spec(allow=LEAVE_CONTACT), out, "near_world", stage, step, q,
                                   steps_per_wp=3, smooth=True)
            if not isinstance(seg, Failure) and not seg.qs:    # touching nothing: no exit
                times[stage] = round(time.time() - t0, 3)
                continue
        elif stage == "tuck":   # the first free of the fold, hanging: chosen again whenever it is built
            seg = free_leg(kin, s, FREE_HAND, JointSet(tuple(np.asarray(g, float) for g in rest_goals)), stage,
                           q_from=q)
        else:                                               # slide_open_hand
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", SLIDE_OPEN, 40, False))
            s = with_width(s, side, SLIDE_OPEN)
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(sided(sg, side) for sg in segs), info={"stage_s": times}, decisions=decided)
