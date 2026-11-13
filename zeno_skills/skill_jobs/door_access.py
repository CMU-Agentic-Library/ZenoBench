"""Reaching what stands behind a door (a shelf of a cabinet, the fridge, the microwave's cavity): the
door it is behind (annotations.behind_door), open enough to reach past it, the park in front of its
free edge, the way out of its opening.  The pick from behind a door and the set-down behind one
alike: one is the other backwards (docs/skills/place.md)."""

from __future__ import annotations

import math
import numpy as np

from ..annotations import behind_door, opening
from ..rig import SkillFailure

FRONT_SEED_M = 0.65            # m in front of a door's free edge the first park behind it stands
                               # (the hand-placed fridge seed of 11-0x stood 0.67 m out, 6 cm past the edge)


def door_ahead(rig, support, point, what):
    """The articulated ``support`` (a support record, or None) / ``point`` is behind
    (annotations.behind_door), where its opening is annotated -- open at least OPEN_ENOUGH, else
    SkillFailure (``what``: the skill and its object, for the message).  None: in the open."""
    a = behind_door(rig.ann, support, point)
    if a is None or opening(a) is None:
        return None
    from ..predicates import OPEN_ENOUGH, _art_open
    if _art_open(rig, a["name"])[0] < OPEN_ENOUGH:
        raise SkillFailure(f"{what}: {a['name']} door is closed")
    return a


def outward(a, p):
    """m point ``p`` stands out toward articulated ``a``'s opening (its xy along annotations.opening):
    what stands most outward is reached past the least."""
    return float(np.asarray(p, float)[:2] @ opening(a))


def leave_tier(a, u):
    """How many 45-degree steps the horizontal part of the hand's way out ``u`` (a unit 3-vector: a
    set-down's pull-out, back along the gripper axis) turns from ``a``'s opening: 0 straight out
    through it, 4 into the back wall.  The arm reaches in through the opening, so a hand whose way out
    points elsewhere has the wrist somewhere the arm cannot be -- the kinematic ranking of a park search
    does not see that (it checks no collisions), so these are the goal set's tiers (Problem.tiers):
    built in this order.  A way out mostly vertical (a top pinch, lifted off) turns from nothing: 0."""
    h = np.asarray(u, float)[:2]
    n = float(np.linalg.norm(h))
    if n < 0.5:
        return 0
    c = max(-1.0, min(1.0, float(h @ opening(a)) / n))
    return int(round(math.degrees(math.acos(c)) / 45.0))


def front_of(rig, a, target):
    """A base pose FRONT_SEED_M out of ``a``'s opening in front of its door's free edge -- the end of
    the closed door away from the hinge, where the open door is not; the handle for a drawer --
    facing ``target`` with it off to the right arm's side by park_search.FACE_LEFT, as the
    candidates' cost prefers (and the hand-placed seeds had it)."""
    from ..park_search import FACE_LEFT
    out = opening(a)
    if a.get("type") == "revolute":
        T = rig.ann.part_pose(a, a["closed_q"])
        boxes = a.get("part_boxes") or [a["part_box"]]
        ends = [T[:3, :3] @ np.array([x, 0.5 * (lo[1] + hi[1]), 0.0]) + T[:3, 3]
                for lo, hi in boxes for x in (lo[0], hi[0])]
        pivot = np.asarray(a["pivot"], float)
        edge = max(ends, key=lambda e: float(np.hypot(*(e - pivot)[:2])))[:2]
    else:
        edge = np.asarray(a["handle"]["center"], float)[:2]
    xy = edge + FRONT_SEED_M * out
    face = math.degrees(math.atan2(target[1] - xy[1], target[0] - xy[0]))
    return float(xy[0]), float(xy[1]), float(face + FACE_LEFT)
