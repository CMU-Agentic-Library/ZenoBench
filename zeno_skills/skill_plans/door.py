"""Opening a door or a drawer by its handle (docs/MOTION_ARCHITECTURE.md section 6, open / close): one
grasp, one task segment, one release -- the base rides the part (carry "base").

The handle comes in the part's frame (Aim with a frame: the grasp pose follows the part wherever the
State has it), the ride is a Script over the part's joint value (primitives.scripted: checked whole
at every ride step, the base by the BaseModel), and the hold is a Held(kind="part") between the
close and the release (its fingers may touch the part, the rest of the robot may not)."""

from __future__ import annotations

import time

import numpy as np

from ..clearance import Allow, closing
from ..motion_state import (Aim, Failure, Held, Plan, Segment, Spec, aim_pose, at_base, decisions_of, holding,
                            released, with_arm, with_part, with_width)
from ..tolerances import DOOR_LEAVE, DOOR_TOL
from ..primitives import JointSet, PartAt, Script, free_leg, query, ride_base, scripted, straight
from ._common import FREE_HAND, T_of, _aimed, _kept, _move, _reach, anchor

DOOR_STAGES = ("door_arrive", "door_open_hand", "door_reach", "door_grasp", "door_close_hand", "door_held",
               "door_ride", "door_moved", "door_release", "door_leave", "tuck", "door_settle")
DOOR_ANCHORS = ("door_arrive", "door_held", "door_moved")   # the base and the part; the hold; where the part went
DOOR_RELAY = "door_reach"     # the decision the park search's ranking IK solves for (park_search.Problem.relay)
# DOOR_TOL (m, rad): the reach and the reach-in's end may come further off the handle than when built
# (the part moved, the base stopped off its park) -- the hook is a fine motion onto the bar, as a
# pick's grasp.  Value and source: tolerances.py
DOOR_SETTLE_TICKS = 60        # physics ticks the part settles after the hand left it (skills._move_articulated's)


def touch_part(side, part, why):
    """The Spec of a motion whose fingers may touch the articulated ``part`` (the reach-in onto its
    handle, the release): the monitor told the same (Allow), the rest of the arm checked against it."""
    return Spec(allow=Allow(hand=side, links="fingers", touch=(part,), reason=why), fingers=True, exempt=False,
                touch=(part,))


def plan_door(kin, state, grip, rest_goals, base=None, start="door_arrive", prior=None, step=0.003):
    """The handle grip = {part, kind ("hinge" | "slider"), pose (v -> the part frame's world pose at
    joint value v), T_part_tcp (the grasp in the part frame), u (the reach-in's direction in the TCP
    frame), L (its length), pre_open, s1 (where the ride's script ends), ride_step, track (lead,
    rate, done: primitives.TRACK_KW)} from ``state``:

        door_arrive      anchor: the base and the part as they are
        door_open_hand   open to pre_open
        door_reach       the free leg to the reach-in's start (its solution decided: _reach, decide_ik)
        door_grasp       the straight onto the handle, the fingers may touch the part
        door_close_hand  close; the hand holds the part (Held kind "part")
        door_held        anchor: the hold measured
        door_ride        the task segment: the part from where it is to s1, the base riding it
                         (Script carry "base", PartAt), checked by ``base`` (motion_state.BaseModel)
        door_moved       anchor: where the part went
        door_release     open to pre_open, let go
        door_leave       the reach-in backwards: the straight DOOR_LEAVE back along u from where the ride
                         left the hand (the bar out from behind the fingers -- the opened hook clears it by
                         more than a contact gap, so a measured contact reads 0 m there -- and the hand clear
                         of the door, which swings on after it is let go)
        tuck             the first free of ``rest_goals`` (JointSet; never kept)
        door_settle      the part settles

    The reach and the reach-in carry the Aim (the handle in the part frame), the pose they were built
    for and DOOR_TOL (primitives.holds checks them again).  From ``start`` on; ``prior`` as
    plan_pick's (a Plan: its motions that still hold kept, its decisions tried first; else the park
    search's ranking solution) -- door_reach, the reach-in start's solution.  Plan or Failure."""
    with query(kin, state, FREE_HAND):          # kin.tcp at the state's base throughout
        return _plan_door(kin, state, grip, rest_goals, base, start, prior, step)


def _plan_door(kin, state, grip, rest_goals, base, start, prior_plan, step):
    i0 = DOOR_STAGES.index(start)
    prior = decisions_of(prior_plan)
    part, side = grip["part"], kin.side
    aim = Aim(part, np.asarray(grip["T_part_tcp"], float), side=side, frame=grip["pose"])
    aimed = aim_pose(state, aim)
    if aimed is None and i0 <= DOOR_STAGES.index("door_grasp"):
        return Failure(f"{part} is not in the State", start)
    p, R = aimed if aimed is not None else (None, None)
    u_tcp = np.asarray(grip["u"], float) / np.linalg.norm(grip["u"])
    pre_open = float(grip["pre_open"])
    q, s = state.q(side), state
    segs, decided, times = [], {}, {}
    for stage in DOOR_STAGES[i0:]:
        t0 = time.time()
        kept = _kept(kin, s, q, prior_plan, stage) if stage != "tuck" else None
        if stage in DOOR_ANCHORS:
            seg = anchor(stage, q, s, (part,), side)
        elif stage == "door_open_hand":
            seg = Segment(stage, FREE_HAND, q, kind="action", action=("grip", pre_open, 30, False))
            s = with_width(s, side, pre_open)
        elif stage == "door_reach":
            seg = kept or _reach(kin, s, FREE_HAND, p, R, R @ u_tcp, float(grip["L"]), q, prior.get(stage), stage, step)
            if not isinstance(seg, Failure):
                seg = kept or _aimed(kin, seg, aim, aimed, DOOR_TOL, steps_per_wp=3)
                if seg.qs:                                  # the reach-in's start as the plan reaches it
                    decided[stage] = seg.q_end
        elif stage == "door_grasp":
            spec = touch_part(side, part, "the reach-in onto the handle: the fingers may touch the part")
            seg = kept or straight(kin, s, spec, p, R, stage, step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _aimed(kin, seg, aim, aimed, DOOR_TOL, steps_per_wp=4)
        elif stage == "door_close_hand":
            seg = Segment(stage, Spec(allow=closing(part, side)), q, kind="action", action=("grip", 0.0, None, False))
            v = s.parts.get(part)
            if v is not None:
                T_hand = T_of(kin.tcp(q)[1], kin.tcp(q)[0])
                s = holding(s, side, Held(part, np.linalg.inv(T_hand) @ np.asarray(grip["pose"](float(v)), float),
                                          "part"))
        elif stage == "door_ride":
            v = s.parts.get(part)
            if v is None:
                return Failure(f"{part} is not in the State", stage)
            script = Script(PartAt(grip["kind"], part, grip["pose"]), float(v), float(grip["s1"]),
                            step=float(grip["ride_step"]), carry="base")
            spec = Spec(allow=Allow(hand=side, links="fingers", touch=(part,),
                                    reason="riding the part: the fingers on its handle"))
            # from the arm as the plan has it (q: on the handle), not as the State it moves on had it
            seg = scripted(kin, with_arm(s, q, side), spec, script, stage, base=base, track=grip["track"],
                           clear={"open_width": pre_open, "leave": True})
            if not isinstance(seg, Failure):
                s = at_base(with_part(s, part, script.s1), ride_base(script, s.base, script.s1))
        elif stage == "door_release":
            seg = Segment(stage, touch_part(side, part, "letting go of the handle: the fingers may touch the part"),
                          q, kind="action", action=("grip", pre_open, 70, False))
            if s.held(side) is not None:
                s = released(s, side, part)
            s = with_width(s, side, pre_open)
        elif stage == "door_leave":
            with query(kin, s, FREE_HAND):                  # the TCP at the base the ride left it
                p_now, R_now = kin.tcp(q)
            spec = touch_part(side, part, "backing off the handle: the fingers may touch the part")
            seg = kept or straight(kin, s, spec, p_now - DOOR_LEAVE * (R_now @ u_tcp), R_now, stage,
                                   step=step, q_from=q)
            if not (isinstance(seg, Failure) or kept):
                seg = _move(seg, steps_per_wp=4, smooth=True)
        elif stage == "tuck":   # the first free of the fold, hanging: chosen again whenever it is built
            seg = free_leg(kin, s, FREE_HAND, JointSet(tuple(np.asarray(g, float) for g in rest_goals)), stage,
                           q_from=q)
        else:                                               # door_settle: nothing moves
            seg = Segment(stage, Spec(), q, kind="action", action=("wait", DOOR_SETTLE_TICKS))
        times[stage] = round(time.time() - t0, 3)
        if isinstance(seg, Failure):
            return Failure(seg.why, seg.segment, {"stage_s": times})
        segs.append(seg)
        q = seg.q_end
    return Plan(tuple(segs), info={"stage_s": times}, decisions=decided)
