"""The posture shape's plan (docs/motion/MOTION_ARCHITECTURE.md 2.3, 6, 9.3 step 5): crouch / stand, bend /
straighten, tuck -- one free leg to a joint goal where the robot stands.

No park and no anchor before the leg: a posture is built from the State measured right before it runs (run_skill
builds a shape without a park where the robot stands); run checks the leg against the measured State (holds)
and builds it again from there when it no longer holds.  Nothing else is tried: a posture the planner cannot
make here fails (docs section 1, rule 3) -- no tuck first, no base move (the old policies/posture.py's
_move_posture_joint fell back on both).

A body posture moves one body joint and nothing else (Spec.joints, docs 4.2): both arms ride the body as they
are, and so does what either hand holds (on its held link, Spec.arms_still, 4.4).  Each arm's model checks
its own arm against the robot's base (BODY_ENV, 4.4) but not the other arm, so the leg is checked with the
other arm's chain too, at the same body values.  A posture asked "as far as it goes" (the torso to its bottom,
the waist bent fully: ``reach``) ends where the straight joint line first meets the robot's own base or the
world for either arm -- its extent measured by the collision model, as a push's (scripted reach) is: the left
arm's fold reaches into the chassis before the torso reaches its lower limit (11-16)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from ..motion_state import BODY_JOINTS, N_BODY, Failure, Plan, Segment, kept
from ..primitives import Joint, chain, dense, free_leg, query
from ..tolerances import PLAN_AT_START
from ._common import FREE_HAND, FREE_LOAD, _move


def plan_posture(kin, state, goal, joints=None, other=None, open_hand=None, name="posture", start=None, prior=None,
                 reach=False, hold_tilt=True):
    """``kin``'s chain from ``state`` to ``goal`` (primitives.Joint or JointSet) where the robot stands:
    [``{name}_open``: ``kin``'s hand to ``open_hand`` (m per finger), when given] + ``name``: one free_leg
    under FREE_HAND, or FREE_LOAD when that hand holds something, with Spec.joints ``joints`` (None: the
    rule, docs 4.1).  When ``joints`` names body joints only, the other hand's load rides on its held link
    and ``other`` (the other arm's kin) checks the same leg with its own arm at the State's; ``reach``: the
    Joint goal is how far to go, the leg ends at the last point toward it where both arms are free.
    ``start``, ``prior``: run's rebuild (the leg is made again from the State; nothing of it is kept).  An
    empty Plan when the chain is at the goal; Failure when the leg cannot be made here.  ``hold_tilt`` False: a
    load in the hand may tilt on the way (upright turns it to vertical, HAND_PLAN 9f) -- still in the
    collision model, its tilt not held."""
    side = kin.side
    body_only = joints is not None and len(joints) > 0 and all(j in BODY_JOINTS for j in joints)
    spec = FREE_LOAD if state.held(side) is not None and hold_tilt else FREE_HAND
    spec = replace(spec, joints=None if joints is None else tuple(joints), arms_still=body_only)
    q0 = np.asarray(state.q(side), float)
    segs = []
    if open_hand is not None and start in (None, f"{name}_open") and abs(state.hands[side].width - open_hand) > 1e-4:
        segs.append(Segment(f"{name}_open", spec, q0, kind="action", action=("grip", float(open_hand), 30, False),
                            info={"side": side}))
    if reach and body_only and isinstance(goal, Joint):
        goal = _extent(kin, other, state, spec, q0, goal.q, name)
        if isinstance(goal, Failure):
            return goal
    leg = free_leg(kin, state, spec, goal, name)
    if isinstance(leg, Failure):
        return leg
    if not leg.qs or np.max(np.abs(np.asarray(leg.q_end, float) - q0)) < PLAN_AT_START:
        return Plan(tuple(segs))                       # there already
    if body_only and other is not None:
        why = _other_arm(other, state, spec, leg)
        if why is not None:
            return Failure(why, name)
    loaded = any(state.held(s) is not None for s in ("right", "left"))
    # a load rides the body (either hand's): gently, as push_body moves it
    segs.append(_move(leg, steps_per_wp=4, smooth=True) if loaded else leg)
    return Plan(tuple(segs))


def _riding(other, state, qs):
    """The other arm's chain at each of ``qs``'s body values, its arm where the State has it."""
    arm = np.asarray(state.q(other.side), float)[N_BODY:]
    return [np.r_[np.asarray(q, float)[:N_BODY], arm] for q in qs]


def _first_hit(kin, state, spec, qs):
    """The index of the first of ``qs`` that is not free in ``kin``'s model under ``spec`` and what it runs into
    (Kinematics.explain), or (len(qs), "")."""
    with query(kin, state, spec):
        for i, q in enumerate(qs):
            if not kin.free(q):
                return i, (kin.explain(q) if hasattr(kin, "explain") else "")
    return len(qs), ""


def _where(qs, i, names):
    """The moving body joints' values at waypoint i, for a failure's message."""
    q = np.asarray(qs[min(i, len(qs) - 1)], float)
    return ", ".join(f"{n} {q[j]:+.3f}" for j, n in enumerate(names[:N_BODY]))


def _extent(kin, other, state, spec, q0, q1, name):
    """How far a body posture goes toward q1: the last point of the straight joint line q0 -> q1 (the joints the
    spec keeps at q0's) where ``kin``'s arm and ``other``'s, riding the body, are free.  Joint of it, or Failure
    when not even the first step is."""
    names = chain(kin)
    keep = kept(state, spec, kin.side, names)
    q1 = np.asarray(q1, float).copy()
    q1[:len(keep)][keep] = np.asarray(q0, float)[:len(keep)][keep]
    line = [np.asarray(q0, float)] + [np.asarray(q, float) for q in dense(q0, q1)]
    n, why = _first_hit(kin, state, spec, line)
    who = kin.side
    if other is not None:
        m, why_o = _first_hit(other, state, spec, _riding(other, state, line))
        if m < n:
            n, why, who = m, why_o, other.side
    if n <= 1:
        return Failure(f"the {who} arm cannot ride the body from {_where(line, 0, names)} ({why})", name)
    return Joint(line[n - 1])


def _other_arm(other, state, spec, leg):
    """Why the other arm (and what it holds) cannot ride the body along ``leg``, or None: its chain at each
    waypoint's body values, its arm where the State has it, checked in its own model (its arm and load against
    the world and the robot's base)."""
    qs = _riding(other, state, (leg.q_from, *leg.qs))
    with query(other, state, spec):
        if other.path_free(qs):
            return None
    i, why = _first_hit(other, state, spec, qs)
    return (f"the {other.side} arm, riding the body, collides at {_where(qs, i, chain(other))} "
            f"({why or 'between waypoints'})")


def plan_held_move(kin, state, z_goal, name="lift", start=None, prior=None, step=0.005):
    """lift / lower (HAND_PLAN 9e): what ``kin``'s hand holds moved straight up or down where the robot
    stands, the TCP from where the State has it to the height ``z_goal`` (m, world) with its xy and rotation
    kept -- the load's tilt held all the way (a straight keeps the hand's rotation) -- under FREE_LOAD.  One
    straight, nothing tried instead (docs section 1, rule 3): the old held_vertical_move pulled the load toward
    the body from up to five staging points when the straight had no IK.  ``start`` / ``prior``: run's rebuild
    (made again from the State).  An empty Plan when the TCP is at ``z_goal`` already; Failure when the
    straight cannot be made here."""
    from ..primitives import sided, straight
    from ..tolerances import NUMERIC_M
    side = kin.side
    if state.held(side) is None:
        return Failure(f"the {side} hand holds nothing to move", name)
    q0 = np.asarray(state.q(side), float)
    with query(kin, state, FREE_LOAD):
        p, R = kin.tcp(q0)
    if abs(float(z_goal) - float(p[2])) < NUMERIC_M:
        return Plan(())
    seg = straight(kin, state, FREE_LOAD, np.r_[p[:2], float(z_goal)], R, name, step=step, q_from=q0)
    if isinstance(seg, Failure):
        return seg
    return Plan((sided(_move(seg, steps_per_wp=5, smooth=True), side),))
