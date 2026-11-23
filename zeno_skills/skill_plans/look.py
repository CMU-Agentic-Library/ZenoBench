"""look's plan (docs/motion/MOTION_ARCHITECTURE.md 2.3, perception shape): navigate + head actions, the arms still.

A look aims the head camera at points (``heads``: the caller's function of the State -> head angles, the
look job's perception.look_angles from the base the plan assumes; the head geometry imports the predicates,
which a builder may not) and at fixed head angles (a sweep), each a head action segment (run.execute ->
Actuator.aim_head).
When the base must face elsewhere first (``face``: a heading), the turn is navigate's plan to the same
place at that heading (the arm into its travel posture, the drive, the ``arrive`` anchor); at the anchor
run builds the head segments again from the base it measures (docs 8.2-8.3).  No park: a look happens where
the robot stands (run_skill's step 2 for the perception shape)."""

from __future__ import annotations

import numpy as np

from ..motion_state import Failure, Plan, Segment, Spec
from ..tolerances import LOOK_STEPS  # noqa: F401  (re-exported)
from .navigate import NAV_STAGES, plan_navigate


def head_segment(q_from, yaw, pitch, steps, name, what=None):
    """One head action segment: the head to (yaw, pitch) in at most ``steps`` ticks, nothing else moves."""
    return Segment(name, Spec(), np.asarray(q_from, float), kind="action", action=("head", float(yaw), float(pitch),
                   int(steps)), info={"looks_at": what})


def plan_look(kin, left_kin, state, base, heads, face=None, carry=None, label="look", start=None):
    """look from ``state``: [navigate's plan to (x, y, ``face``)] + one head segment per entry of
    ``heads(state)`` -> [(yaw, pitch, steps, what)], named ``{label}_{i}``.  ``start``: a navigate stage
    (NAV_STAGES) or a head segment's name to build from (run's rebuild); None, the whole plan.  ``carry``:
    navigate's Carry when the hand holds a load.  Plan or Failure (the turn cannot be made)."""
    segs, s = [], state
    heads_from = 0
    if start is not None and start.startswith(label + "_") and start[len(label) + 1:].isdigit():
        heads_from = int(start[len(label) + 1:])
    elif face is not None:
        x, y, _ = state.base
        nav = plan_navigate(kin, left_kin, state, (x, y, float(face)), base, carry=carry, label=f"{label}_turn",
                            start=start if start in NAV_STAGES else "arm")
        if isinstance(nav, Failure):
            return nav
        segs += list(nav.segments)
        # the head angles from the base the turn arrives at (the anchor builds them again from the measured one)
        s = _turned(state, (x, y, float(face)))
    q_from = state.q("right")
    for i, (yaw, pitch, steps, what) in enumerate(heads(s)):
        if i >= heads_from:
            segs.append(head_segment(q_from, yaw, pitch, steps, f"{label}_{i}", what))
    return Plan(tuple(segs))


def _turned(state, base):
    """``state`` with the base at ``base`` (a State is a frozen dataclass; a stand-in has a base attribute)."""
    from dataclasses import is_dataclass, replace
    if is_dataclass(state):
        return replace(state, base=base)
    from copy import copy
    out = copy(state)
    out.base = base
    return out
