"""What the skill plans share (docs/MOTION_ARCHITECTURE.md section 6, 9.4): the collision rules of
free space, the contact criteria by name, the free leg to a straight's start.

Skill plans: the primitives chained in a skill's order,
each segment from where the one before really ends, the State moved on between them (the hand
closed on the load, the load let go).  The park search builds a plan at each candidate park, the
execution runs it and builds the rest again from where it stands when a segment no longer holds
(run.run) -- both with these functions.  They know no simulator: what is skill-specific (the
grasp, the carry goal set, the approach length) comes in as arguments."""

from __future__ import annotations

import numpy as np

from ..clearance import FREE, LEAVE_CONTACT
from ..motion_state import Failure, Plan, Segment, Spec, with_arm, with_width
from ..primitives import (ON_LINE, ON_LINE_TURN, TOUCHING, Pose, contact_extent, contact_segment, decide_ik, free_leg,
                          holds, turn)

FREE_HAND = Spec(fingers=True, exempt=False)                  # free space, the fingers in, nothing exempt
FREE_LOAD = Spec(fingers=True, exempt=False, hold_tilt=True)  # ...with a load in the hand, its tilt held


def T_of(R, p):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, p
    return T


def _on_line(kin, q, s, R, u, L):
    """The TCP at q already on the straight s -> s + L u (before its end), turned as R within
    ON_LINE_TURN: then the straight from there is the same straight, a translation along u."""
    p_q, R_q = kin.tcp(np.asarray(q, float))
    d = p_q - s
    along = float(d @ u)
    return L >= ON_LINE and -1e-3 <= along <= L + 1e-3 and np.linalg.norm(d - along * u) < ON_LINE and \
        turn(R, R_q) < ON_LINE_TURN


def _reach(kin, state, spec, p, R, u, L, q_from, prior, name, step, decision=None):
    """The free leg to the start of the straight of length L along u into (p, R): none when the
    TCP is on it already; else to its start, a pose whose solution decide_ik decides in the collision
    model of ``state`` / ``spec`` -- ``prior`` (the plan's own decision on a rebuild, the park
    search's ranking IK, the straight's start up from the set-down pose) as it is while it still
    reaches the start free, else the first seed of a solve (a kinematic solution in collision made
    the leg fail where another would do).  That solution is the leg's joint goal only where the TCP
    straight to the start fails (free_leg, Pose): a straight ends on its own solution, the one the
    rest of the plan is built from -- the leg's q_end, what a plan records as its decision, not the
    solution decided here.  Segment -- info["decided"] {``decision`` (default ``name``): how
    decide_ik decided, "prior" | "solved"} -- or Failure."""
    s = p - L * u
    if _on_line(kin, q_from, s, R, u, L):
        return Segment(name, spec, q_from, (), info={"how": "on the straight"})
    d = decide_ik(kin, state, spec, s, R, prior, seeds=(q_from,))
    if d is None:
        return Failure("no collision-free IK at the straight's start", name)
    q_s, how = d
    seg = free_leg(kin, state, spec, Pose(s, R, q_s), name, step=step, q_from=q_from)
    return seg if isinstance(seg, Failure) else _move(seg, decided={decision or name: how})


def _kept(kin, state, q, prior, name):
    """``prior``'s motion ``name`` (a Plan's: run's rebuild) as it is, when it still holds from q in
    ``state`` (primitives.holds: the check run makes before a segment, docs 8.3) -- else None, built
    again.  Moves only: an action or an anchor holds wherever the arm is, so one made for another
    start would carry that start on; they are made again, at no cost.  (Not for a motion whose goal
    is chosen again at every build: the place's tuck.)"""
    if not isinstance(prior, Plan):
        return None
    seg = next((sg for sg in prior.segments if sg.name == name), None)
    if seg is None or seg.kind != "move":
        return None
    return seg if holds(kin, with_arm(state, q, kin.side), seg) is None else None


def _move(seg, **info):
    """seg with how it is executed added to its info (steps per waypoint, smooth)."""
    return Segment(seg.name, seg.spec, seg.q_from, seg.qs, seg.kind, seg.target, seg.action, {**seg.info, **info})


def _aimed(kin, seg, aim, aimed, tol, **info):
    """seg built for the contact pose ``aimed`` that ``aim`` (motion_state.Aim) derives from the
    State: both recorded, where its end stands (kin.tcp at the built State's base) and ``tol`` (m,
    rad), how much further off the target the end may come before the segment no longer does what
    it was built for -- what primitives.holds checks again."""
    p, R = kin.tcp(seg.q_end)
    return _move(seg, aim=aim, aimed=aimed, end=(np.asarray(p, float).copy(), np.asarray(R, float).copy()),
                 tol=tuple(map(float, tol)), **info)


def _contact(kin, state, spec, u, touching, name, step, q_from, **info):
    ext = contact_extent(kin, state, spec, u, TOUCHING[touching], name, step=step, q_from=q_from)
    if isinstance(ext, Failure):
        return ext
    return _move(contact_segment(spec, ext, name), u=np.asarray(u, float), touching=touching, step=step, **info)


def held_frame(kin, q, held):
    """World pose of a held object's box frame with the hand at q."""
    p, R = kin.tcp(np.asarray(q, float))
    return T_of(R, p) @ np.asarray(held.T_tcp_obj, float)


def plan_clear(kin, state, open_width=None, leave=True, ticks=60, step=0.005, name="fail_clear"):
    """A skill's failure exit (docs/MOTION_ARCHITECTURE.md 8.6, build_clear): with nothing in the
    hand, open it to ``open_width`` (None, or that open already: no open) and (``leave``) back out of
    any contact straight up (contact_extent, near_world: no segment when nothing is touched).  With
    a load in the hand: None -- opening would drop it.  Still touching LEAVE_MAX up: the open alone
    (the exit is the contact model's call, not a shorter try).  Plan or None."""
    if state.held(kin.side) is not None:
        return None
    q = state.q(kin.side)
    segs, s, why = [], state, None
    hand = state.hands.get(kin.side)
    if open_width is not None and (hand is None or hand.width < open_width - 1e-3):
        segs.append(Segment(f"{name}_open", Spec(allow=FREE), q, kind="action",
                            action=("grip", float(open_width), int(ticks), False)))
        s = with_width(s, kin.side, open_width)
    if leave:
        seg = _contact(kin, s, Spec(allow=LEAVE_CONTACT), [0.0, 0.0, 1.0], "near_world", name, step, q,
                       steps_per_wp=3, smooth=True)
        if isinstance(seg, Failure):
            why = seg.why
        elif seg.qs:
            segs.append(seg)
    return Plan(tuple(segs), info={"exit": why}) if segs else None
