"""The pick's plan (docs/MOTION_ARCHITECTURE.md section 6, pick)."""

from __future__ import annotations

import time
from dataclasses import replace

import numpy as np

from ..clearance import LEAVE_CONTACT, closing
from ..motion_state import Aim, Failure, Held, Plan, Segment, Spec, aim_pose, decisions_of, holding, with_width
from ..primitives import free_leg, query, straight
from ._common import FREE_HAND, FREE_LOAD, T_of, _aimed, _contact, _kept, _move, _reach

PICK_STAGES = ("pick_arrive", "pick_open", "pick_reach", "pick_grasp", "pick_close", "pick_held", "pick_lift", "carry_in")
PICK_ANCHORS = ("pick_arrive", "pick_held")   # the base and the object as they are; the hold measured (docs 8.2)
PICK_RELAY = "pick_reach"     # the decision the park search's ranking IK solves for (park_search.Problem.relay)
# m the load's spheres grow by on a pick's carry planned before the close (the hold assumed from where
# the load stood; the hand moves it a little closing): T01 overhang_ready 11-08, a carry planned with
# no room collided by 0 mm once the book sat in the hand.  The carry only (the lift measures the
# contact with the hold as assumed).  First value, to be set from the logged held_offset (planned vs
# measured hold) of the targeted runs.
HELD_POSE_MARGIN = 0.005


def plan_pick(kin, state, grasp, carry_goals, start="pick_arrive", prior=None, step=0.003):
    """The pick of grasp = {name, T_obj_tcp, u, L, pre_open, kind} from ``state``: the grasp pose
    the TCP at T_obj_tcp in the box frame of ``name`` as the State has it (Aim, aim_pose: the object
    where it stands now, in the search and every rebuild alike), ``u`` the reach-in's direction
    in the TCP frame, ``L`` its length.  The anchor where it arrives (the base and the object as
    they are), open the hand (the State's hand at pre_open from there on), the free leg to the reach-in's start (its solution decided in the collision model: _reach,
    decide_ik), the reach-in straight, close, the anchor where the hand holds it (the hold
    measured), the lift off the support (contact_extent,
    off_support), the free leg to the carry pose (``carry_goals(state, q) -> (PoseSet, {step,
    steps_per_wp, smooth})``, the load's tilt held).  The reach and the reach-in carry the Aim and
    the pose they were built for (info["aim"], ["aimed"]: run.holds checks it again).  From
    ``start`` on (the stages before it done).  ``prior``: a Plan (run's rebuild) has each of its
    motions that still holds from here kept as it is (_kept, docs 8.3), and its decisions tried
    first for the rest; else the decisions to keep (decisions_of: the park search's ranking
    solution) -- pick_reach, the reach-in start's solution (where a plan's reach leg ends);
    carry_in, the carry goal chosen ((index, set size): free_leg's first).  Plan (its decisions) or
    Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_pick(kin, state, grasp, carry_goals, start, prior, step)


def _plan_pick(kin, state, grasp, carry_goals, start, prior_plan, step):
    i0 = PICK_STAGES.index(start)
    prior = decisions_of(prior_plan)
    name = grasp["name"]
    aim = Aim(name, np.asarray(grasp["T_obj_tcp"], float), side=kin.side)
    aimed = aim_pose(state, aim)
    if aimed is None and i0 <= PICK_STAGES.index("pick_grasp"):
        return Failure(f"{name} is not in the State", start)
    p, R = aimed if aimed is not None else (None, None)
    u = None if R is None else R @ (np.asarray(grasp["u"], float) / np.linalg.norm(grasp["u"]))
    L = float(grasp["L"])
    q = state.q(kin.side)
    segs, decided = [], {}
    s = state
    # a carry planned after a close in this same plan rides on an assumed hold (HELD_POSE_MARGIN);
    # one built after the real close (run's rebuild from pick_lift / carry_in) on the measured one
    assumed = ("carry_in",) if i0 <= PICK_STAGES.index("pick_close") else ()
    times = {}
    for stage in PICK_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "carry_in" else None
        if stage in PICK_ANCHORS:
            seg = Segment(stage, Spec(), q, kind="anchor")
        elif stage == "pick_open":
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", float(grasp["pre_open"]), 40, False))
            s = with_width(s, kin.side, grasp["pre_open"])
        elif stage == "pick_reach":
            seg = kept or _reach(kin, s, FREE_HAND, p, R, u, L, q, prior.get(stage), stage, step)
            if not isinstance(seg, Failure):
                seg = kept or _aimed(kin, seg, aim, aimed, steps_per_wp=4, smooth=True)
                if seg.qs:                                  # the reach-in's start as the plan reaches it
                    decided[stage] = seg.q_end
        elif stage == "pick_grasp":
            seg = kept or straight(kin, s, FREE_HAND, p, R, stage, step=step, q_from=q)
            seg = seg if isinstance(seg, Failure) or kept else _aimed(kin, seg, aim, aimed, steps_per_wp=4, smooth=True)
        elif stage == "pick_close":
            seg = Segment(stage, Spec(allow=closing(name)), q, kind="action", action=("grip", 0.0, None, True))
            if name in s.objects:
                T_hand = T_of(kin.tcp(q)[1], kin.tcp(q)[0])
                s = holding(s, kin.side, Held(name, np.linalg.inv(T_hand) @ s.objects[name], grasp.get("kind", "pinch")))
        elif stage == "pick_lift":
            seg = kept or _contact(kin, s, Spec(allow=LEAVE_CONTACT), [0.0, 0.0, 1.0], "off_support", stage, 0.002,
                                   q, steps_per_wp=6, smooth=True)
        else:                                               # carry_in
            h = s.held(kin.side)
            sc = s if h is None or h.pad or stage not in assumed else \
                holding(s, kin.side, replace(h, pad=HELD_POSE_MARGIN))
            seg = _kept(kin, sc, q, prior_plan, stage)     # checked as it would be built: the assumed hold padded
            if seg is None:
                with query(kin, sc, FREE_LOAD):
                    goals, how = carry_goals(sc, q)
                seg = free_leg(kin, sc, FREE_LOAD, goals, stage, step=how.get("step", 0.01), q_from=q,
                               first=prior.get(stage)) if goals.goals else Failure("no carry goal", stage)
                if not isinstance(seg, Failure):
                    seg = _move(seg, steps_per_wp=how.get("steps_per_wp", 4), smooth=how.get("smooth", False))
            if not isinstance(seg, Failure):
                decided[stage] = (seg.info["chosen"], seg.info["goals"])
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(segs), info={"stage_s": times}, decisions=decided)


