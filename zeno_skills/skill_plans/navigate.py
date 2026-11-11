"""navigate's plan (docs/MOTION_ARCHITECTURE.md section 6, navigate): the arm into its travel
posture, the base driven there, the arrival.

    tuck / carry_in   empty hand: free_leg to the first free of {fold, hanging at the side}, none
                      when it is already folded; with a load: the carry posture checked against the
                      carry constraints (Carry.check) and kept when it meets them -- pick's carry_in
                      decided it (rule 2) -- else free_leg to the carry goal set, the tilt held
    left_fold         an empty left arm left out folds (none when it is folded)
    drive             drive: the whole-body base plan, the arms through travel_chain
    arrive            anchor

travel_chain is the one source of the postures the base drives in: the park search's drive check
(BaseModel.drivable) and this plan take them from it (9.3 step 1.4)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import numpy as np

from ..motion_state import Failure, Plan, Segment, Spec, at_base, with_arm
from ..primitives import JointSet, Joint, drive, free_leg, query
from ..tolerances import PLAN_AT_START, SAME_POSTURE
from ._common import FREE_HAND, FREE_LOAD, _move, anchor

NAV_STAGES = ("arm", "left_fold", "drive", "arrive")


@dataclass(frozen=True)
class Carry:
    """What a load in the right hand asks of the posture it is driven in.
    check(state) -> None when the posture meets the carry constraints, else why not;
    goals(state, q) -> (PoseSet, {step, steps_per_wp, smooth}): the carry goal set when it does not.
    want(state) -> None, or why the load should ride higher (a rim the destination asks to clear:
    not a constraint -- the drive's whole-body plan checks the load against the world -- so the
    load is raised to raise_goals when one is reachable, else it rides as it is)."""
    check: Callable
    goals: Callable
    want: Callable | None = None
    raise_goals: Callable | None = None


def travel_chain(kin, left_kin, state, arrive=None):
    """The postures the base drives in from ``state`` [(name, (q_right, q_left))]: the fold (each
    empty arm folded, an arm with a load as it is), hanging at the side where the fold does not fit
    (empty-handed only: both arms down, kin.drive), the arrival (the fold, or ``arrive``: right-arm
    joints, or (right, left)).  The base planner passes to the arrival without a swing where it is
    the fold and hangs only where the path needs it."""
    right_held, left_held = state.held("right") is not None, state.held("left") is not None
    rest = (np.asarray(state.q_right, float).copy() if right_held else np.asarray(kin.rest, float).copy(),
            np.asarray(state.q_left, float).copy() if left_held else np.asarray(left_kin.rest, float)[2:].copy())
    hang = rest if right_held or left_held else (np.asarray(kin.drive, float), np.asarray(left_kin.drive, float)[2:])
    if arrive is None:
        end = rest
    elif isinstance(arrive, tuple):
        end = (np.asarray(arrive[0], float), np.asarray(arrive[1], float)[-7:])
    else:
        end = (np.asarray(arrive, float), rest[1])
    return [("fold", rest), ("hang", hang), ("arrive", end)]


def plan_navigate(kin, left_kin, state, goal, base, carry=None, arrive=None, label="navigate", start="arm",
                  stop="arrive", **drive_kw):
    """navigate to ``goal`` (x, y, yaw_deg) from ``state``: the right arm into its travel posture
    (``carry``: a Carry when it holds a load), an empty left arm folded, the drive (``base``:
    motion_state.BaseModel; ``drive_kw`` its speeds), the arrival; the stages ``start`` to ``stop``
    (NAV_STAGES).  Plan, its info["skipped"] the
    arm motions left out because there is none (the base plan then makes the switch where it finds
    room, as navigate always did), or Failure.  The arm stages query in their own Spec (free_leg);
    the drive outside any arm query, as the base planner always ran."""
    return _plan_navigate(kin, left_kin, state, goal, base, carry, arrive, label, start, stop, drive_kw)


def _plan_navigate(kin, left_kin, state, goal, base, carry, arrive, label, start, stop, drive_kw):
    segs, s, skipped, info = [], state, {}, {}
    for stage in NAV_STAGES[NAV_STAGES.index(start):NAV_STAGES.index(stop) + 1]:
        seg = None
        if stage == "arm":
            q = s.q("right")
            if s.held("right") is None:
                if np.max(np.abs(q - np.asarray(kin.rest, float))) > PLAN_AT_START:
                    seg = free_leg(kin, s, FREE_HAND, JointSet((kin.rest, kin.drive)), "tuck")
                    if isinstance(seg, Failure):
                        skipped["tuck"], seg = seg.why, None
            elif carry is not None:
                why = carry.check(s)            # the State now: kin at its base already
                want = None if why is not None or carry.want is None else carry.want(s)
                info["carry"] = "kept" if why is None and want is None else (why or want)
                if why is not None or want is not None:
                    with query(kin, s, FREE_LOAD):
                        goals, how = (carry.goals if why is not None else carry.raise_goals)(s, q)
                    seg = free_leg(kin, s, FREE_LOAD, goals, "carry_in", step=how.get("step", 0.01)) \
                        if goals.goals else Failure("no carry goal", "carry_in")
                    if isinstance(seg, Failure) and why is None:
                        # the constraints hold, only the higher ride is out of reach: as it is
                        info["carry"], seg = f"kept: {want}; no higher goal reachable ({seg.why})", None
                    elif isinstance(seg, Failure):
                        return Failure(f"{why}; to the carry pose: {seg.why}", "carry_in", {"carry": why})
                    else:
                        seg = _move(seg, steps_per_wp=how.get("steps_per_wp", 4), smooth=how.get("smooth", False))
        elif stage == "left_fold":
            ql = s.q("left")
            goal_l = np.r_[ql[:2], np.asarray(left_kin.rest, float)[2:]]
            if s.held("left") is None and np.max(np.abs(goal_l - ql)) >= SAME_POSTURE:
                seg = free_leg(left_kin, s, Spec(fingers=True), Joint(goal_l), "left_fold")
                if isinstance(seg, Failure):
                    skipped["left_fold"], seg = seg.why, None
                else:
                    seg = _move(seg, side="left")
        elif stage == "drive":
            seg = drive(base, s, goal, travel_chain(kin, left_kin, s, arrive), label, **drive_kw)
            if isinstance(seg, Failure):
                return seg
        else:                                               # arrive
            seg = replace(anchor("arrive", s.q_right, s),
                          target=("base", None if goal is None else tuple(map(float, goal))))
        if seg is None:
            continue
        segs.append(seg)
        if seg.kind == "move":
            s = with_arm(s, seg.q_end, seg.info.get("side", "right"))
        elif seg.kind == "drive":
            s = with_arm(s, seg.q_end, "right")
            if goal is not None:
                s = at_base(s, goal)
    return Plan(tuple(segs), info={"skipped": skipped, **info})
