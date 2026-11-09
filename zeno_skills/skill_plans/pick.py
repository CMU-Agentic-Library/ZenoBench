"""The pick's plan (docs/MOTION_ARCHITECTURE.md section 6, pick)."""

from __future__ import annotations

import time
from dataclasses import replace

import numpy as np

from ..clearance import LEAVE_CONTACT, closing
from ..motion_state import Failure, Held, Plan, Segment, Spec, holding, with_width
from ..primitives import free_leg, query, straight
from ._common import FREE_HAND, FREE_LOAD, T_of, _contact, _move, _reach

PICK_STAGES = ("pick_open", "pick_reach", "pick_grasp", "pick_close", "pick_lift", "carry_in")
# m the load's spheres grow by on a pick's carry planned before the close (the hold assumed from where
# the load stood; the hand moves it a little closing): T01 overhang_ready 11-08, a carry planned with
# no room collided by 0 mm once the book sat in the hand.  The carry only (the lift measures the
# contact with the hold as assumed).  First value, to be set from the logged held_offset (planned vs
# measured hold) of the targeted runs.
HELD_POSE_MARGIN = 0.005


def plan_pick(kin, state, grasp, u, L, carry_goals, start="pick_open", q_seed=None, step=0.003):
    """The pick of grasp = {name, p, R, pre_open, kind} from ``state``: open the hand (the State's
    hand at pre_open from there on, for the search and every rebuild alike), the free leg
    to the reach-in's start (its solution solved in the collision model, ``q_seed`` -- the park
    search's ranking IK -- first among the seeds: _reach), the reach-in straight
    of length L along u, close, the lift off the support (contact_extent, off_support), the free
    leg to the carry pose (``carry_goals(state, q) -> (PoseSet, {step, steps_per_wp, smooth})``, the
    load's tilt held).  From
    ``start`` on (the stages before it done).  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_pick(kin, state, grasp, u, L, carry_goals, start, q_seed, step)


def _plan_pick(kin, state, grasp, u, L, carry_goals, start, q_seed, step):
    i0 = PICK_STAGES.index(start)
    name, p, R = grasp["name"], np.asarray(grasp["p"], float), np.asarray(grasp["R"], float)
    u = np.asarray(u, float) / np.linalg.norm(u)
    q = state.q(kin.side)
    segs = []
    s = state
    # a carry planned after a close in this same plan rides on an assumed hold (HELD_POSE_MARGIN);
    # one built after the real close (run's rebuild from pick_lift / carry_in) on the measured one
    assumed = ("carry_in",) if i0 <= PICK_STAGES.index("pick_close") else ()
    times = {}
    for stage in PICK_STAGES[i0:]:
        t0 = time.time()
        if stage == "pick_open":
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", float(grasp["pre_open"]), 40, False))
            s = with_width(s, kin.side, grasp["pre_open"])
        elif stage == "pick_reach":
            seg = _reach(kin, s, FREE_HAND, p, R, u, L, q, q_seed, stage, step)
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
            h = s.held(kin.side)
            sc = s if h is None or h.pad or stage not in assumed else \
                holding(s, kin.side, replace(h, pad=HELD_POSE_MARGIN))
            with query(kin, sc, FREE_LOAD):
                goals, how = carry_goals(sc, q)
            seg = free_leg(kin, sc, FREE_LOAD, goals, stage, step=how.get("step", 0.01), q_from=q) \
                if goals.goals else Failure("no carry goal", stage)
            seg = seg if isinstance(seg, Failure) else _move(seg, steps_per_wp=how.get("steps_per_wp", 4),
                                                             smooth=how.get("smooth", False))
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(segs), info={"stage_s": times})


