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

from ..motion_state import Failure, Segment, Spec
from ..primitives import (ON_LINE, Pose, contact_extent, contact_segment, free_leg, in_world, near_world,
                          off_support, query)

FREE_HAND = Spec(fingers=True, exempt=False)                  # free space, the fingers in, nothing exempt
FREE_LOAD = Spec(fingers=True, exempt=False, hold_tilt=True)  # ...with a load in the hand, its tilt held
TOUCHING = {"near_world": near_world, "off_support": off_support, "in_world": in_world}


def T_of(R, p):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, p
    return T


def _on_line(kin, q, s, u, L):
    """The TCP at q already on the straight s -> s + L u (before its end)."""
    d = kin.tcp(np.asarray(q, float))[0] - s
    along = float(d @ u)
    return L >= ON_LINE and -1e-3 <= along <= L + 1e-3 and np.linalg.norm(d - along * u) < ON_LINE


def _reach(kin, state, spec, p, R, u, L, q_from, seed, name, step):
    """The free leg to the start of the straight of length L along u into (p, R): none when the
    TCP is on it already; else to its start, a pose whose solution is solved here in the collision
    model of ``state`` / ``spec`` (Kinematics.ik_global; ``seed`` -- the park search's ranking IK,
    the straight's start up from the set-down pose -- only the first of its seeds, never the goal
    as it is: those are kinematic, and a solution in collision made the leg fail where another
    would do).  No collision-free solution: Failure."""
    s = p - L * u
    if _on_line(kin, q_from, s, u, L):
        return Segment(name, spec, q_from, (), info={"how": "on the straight"})
    with query(kin, state, spec):
        q_s, ok = kin.ik_global(s, R, seeds=([np.asarray(seed, float)] if seed is not None else []) + [q_from])
    if not ok:
        return Failure("no collision-free IK at the straight's start", name)
    return free_leg(kin, state, spec, Pose(s, R, np.asarray(q_s, float)), name, step=step, q_from=q_from)


def _move(seg, **info):
    """seg with how it is executed added to its info (steps per waypoint, smooth)."""
    return Segment(seg.name, seg.spec, seg.q_from, seg.qs, seg.kind, seg.target, seg.action, {**seg.info, **info})


def _contact(kin, state, spec, u, touching, name, step, q_from, **info):
    ext = contact_extent(kin, state, spec, u, TOUCHING[touching], name, step=step, q_from=q_from)
    if isinstance(ext, Failure):
        return ext
    return _move(contact_segment(spec, ext, name), u=np.asarray(u, float), touching=touching, step=step, **info)


def held_frame(kin, q, held):
    """World pose of a held object's box frame with the hand at q."""
    p, R = kin.tcp(np.asarray(q, float))
    return T_of(R, p) @ np.asarray(held.T_tcp_obj, float)
