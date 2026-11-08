"""What a motion is planned for, and by what rules (docs/MOTION_ARCHITECTURE.md section 4).

``State``: the robot and the objects as they are (Rig.observe) or as a plan assumes they will be
(a park the base is not at yet, an object the hand has not closed on yet, one let go) -- data
only, never changed in place: the helpers below return a new one.  ``Spec``: the collision rules
of one segment.  ``Segment`` / ``Plan``: what the primitives (primitives.py) and the skill plans
make, and the execution runs.  Nothing here plans, executes or knows the simulator; the collision
backend takes a State and a Spec as one query (Motion.query)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping

import numpy as np

from .clearance import FREE, Allow

SIDES = ("right", "left")


@dataclass(frozen=True)
class Held:
    """An object in a hand: its box frame (Motion._box_of) in the TCP frame (Motion.held_in_tcp)."""
    name: str
    T_tcp_obj: np.ndarray
    kind: str = "pinch"              # pinch / edge / corner / bimanual


@dataclass(frozen=True)
class Hand:
    width: float                     # m per finger, as the fingers stand (or will)
    held: Held | None = None


@dataclass(frozen=True)
class State:
    """The robot and the world for a collision query; whatever changes a query is in here."""
    base: tuple                      # (x, y, yaw_deg), as Rig.base_pose
    q_right: np.ndarray              # torso, waist and the 7 right-arm joints (the commanded posture)
    q_left: np.ndarray               # the 7 left-arm joints
    head: Mapping[str, float] = field(default_factory=dict)       # head joint -> value
    hands: Mapping[str, Hand] = field(default_factory=dict)       # "right" / "left"
    objects: Mapping[str, np.ndarray] = field(default_factory=dict)   # name -> 4x4 world pose of its box frame
    parts: Mapping[str, float] = field(default_factory=dict)      # articulated part -> joint value

    def q(self, side="right"):
        """The joints of ``side``'s planning chain (torso and waist first, as ArmKin.names)."""
        return np.asarray(self.q_right, float) if side == "right" else \
            np.r_[np.asarray(self.q_right, float)[:2], np.asarray(self.q_left, float)]

    def held(self, side="right"):
        h = self.hands.get(side)
        return None if h is None else h.held


@dataclass(frozen=True)
class Spec:
    """The collision rules of one segment.  ``fingers``: the hand's fingers in the collision model.
    ``exempt``: what the TCP target touches may be touched (the backend exempts by the target's
    position; never with a load in the hand).  ``hold_tilt``: a load in the hand keeps its tilt."""
    allow: Allow = FREE
    fingers: bool = True
    exempt: bool = False
    hold_tilt: bool = False


@dataclass(frozen=True)
class Segment:
    """One step of a plan.  kind "move": joint waypoints ``qs`` after ``q_from``; "action": no arm
    motion, ``action`` says what (("grip", width), ...).  ``target``: what the segment is for --
    a pose (p, R), a joint goal q, or None -- checked again before it runs.  ``info``: what the
    primitive measured or chose (a straight's length, how a free leg was made)."""
    name: str
    spec: Spec
    q_from: np.ndarray
    qs: tuple = ()
    kind: str = "move"
    target: tuple | None = None
    action: tuple | None = None
    info: Mapping = field(default_factory=dict)

    @property
    def q_end(self):
        return np.asarray(self.qs[-1], float) if self.qs else np.asarray(self.q_from, float)


@dataclass(frozen=True)
class Failure:
    """Why a primitive or a plan could not be made (what a park search counts, what a skill reports)."""
    why: str
    segment: str = ""

    def __bool__(self):
        return False


@dataclass(frozen=True)
class Plan:
    segments: tuple
    goal: int = 0                    # which goal of the skill's goal set it serves


# --------------------------------------------------------------------- new states from a state
def at_base(s: State, base) -> State:
    return replace(s, base=tuple(float(v) for v in base))


def with_arm(s: State, q, side="right") -> State:
    q = np.asarray(q, float)
    if side == "right":
        return replace(s, q_right=q.copy())
    return replace(s, q_right=np.r_[q[:2], np.asarray(s.q_right, float)[2:]], q_left=q[2:].copy())


def with_width(s: State, side, width) -> State:
    h = s.hands.get(side, Hand(width=0.0))
    return replace(s, hands={**s.hands, side: replace(h, width=float(width))})


def holding(s: State, side, held: Held) -> State:
    """``side``'s hand closed on ``held`` (no longer an obstacle to it)."""
    h = s.hands.get(side, Hand(width=0.0))
    return replace(s, hands={**s.hands, side: replace(h, held=held)})


def released(s: State, side, name, T_frame) -> State:
    """``side``'s hand let go of ``name``, which now stands with its box frame at T_frame."""
    h = s.hands.get(side, Hand(width=0.0))
    return replace(s, hands={**s.hands, side: replace(h, held=None)},
                   objects={**s.objects, name: np.asarray(T_frame, float).copy()})


def with_object(s: State, name, T_frame) -> State:
    return replace(s, objects={**s.objects, name: np.asarray(T_frame, float).copy()})
