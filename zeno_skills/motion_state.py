"""What a motion is planned for, and by what rules (docs/MOTION_ARCHITECTURE.md section 4).

``State``: the robot and the objects as they are (Rig.observe) or as a plan assumes they will be
(a park the base is not at yet, an object the hand has not closed on yet, one let go) -- data
only, never changed in place: the helpers below return a new one.  ``Spec``: the collision rules
of one segment.  ``Segment`` / ``Plan``: what the primitives (primitives.py) and the skill plans
make, and the execution runs.  Nothing here plans, executes or knows the simulator; the collision
backend takes a State and a Spec as one query (Motion.query)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping, Protocol

import numpy as np

from .clearance import FREE, Allow

SIDES = ("right", "left")


class SkillFailure(RuntimeError):
    """A skill could not be done: a plan that cannot be made, or a simulated result that is wrong
    (docs/MOTION_ARCHITECTURE.md 8.6).  Here, below every layer that raises it (rig re-exports it)."""


class Dropped(SkillFailure):
    """The held object left the hand while carrying it (worth a re-pick)."""


def clearing(exc, open_width=None, leave=True, ticks=60):
    """``exc`` asking for the skill's failure exit before it is raised (run.run_clear, docs 8.6):
    open the empty hand to ``open_width`` (None: as it is) over ``ticks``, then (``leave``) back out
    of any contact straight up.  A hook judges and marks; the exit is a plan run.run makes."""
    exc.clear = {"open_width": open_width, "leave": leave, "ticks": ticks}
    return exc


@dataclass(frozen=True)
class Held:
    """An object in a hand: its box frame (Motion._box_of) in the TCP frame (Motion.held_in_tcp).
    ``pad``: m its collision spheres are grown by -- a hold a plan assumes (taken from where the
    object stood before the hand closed) rather than one measured in the hand."""
    name: str
    T_tcp_obj: np.ndarray
    kind: str = "pinch"              # pinch / edge / corner / bimanual
    pad: float = 0.0


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
    position; never with a load in the hand).  ``hold_tilt``: a load in the hand keeps its tilt.
    ``touch``: objects the fingers may touch -- no obstacle to them, still one to the rest of the
    arm (primitives.free_path checks that apart); ``allow`` then lists them for the monitor."""
    allow: Allow = FREE
    fingers: bool = True
    exempt: bool = False
    hold_tilt: bool = False
    touch: tuple = ()


@dataclass(frozen=True)
class Segment:
    """One step of a plan.  kind "move": joint waypoints ``qs`` after ``q_from`` (of the arm
    ``info["side"]``, default right); "action": no arm motion, ``action`` says what (("grip", width),
    ...); "drive": the base, ``info["steps"]`` (BaseModel.plan's), ``qs`` the right arm's postures after
    each swing on the way; "anchor": where an error comes in (docs 8.2), nothing moves.  ``target``: what the segment is for --
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
    """Why a primitive or a plan could not be made (what a park search counts, what a skill reports).
    ``info``: what it measured on the way (a plan builder's time per stage)."""
    why: str
    segment: str = ""
    info: Mapping = field(default_factory=dict)

    def __bool__(self):
        return False


@dataclass(frozen=True)
class Plan:
    """``decisions``: what the builder decided that binds its segments together (docs 4.3, 8.1),
    {name: value} -- a contact pose's joint solution as the plan reaches it (pick_reach: the reach
    leg's end; place_reach: the set-down's end), the chosen goal of a goal set as (index, set size)
    (carry_in, tuck).  A rebuild gets them back as its prior (decisions_of)."""
    segments: tuple
    goal: int = 0                    # which goal of the skill's goal set it serves
    info: Mapping = field(default_factory=dict)   # a builder's time per stage (stage_s)
    decisions: Mapping = field(default_factory=dict)


def decisions_of(prior):
    """A builder's prior as {decision: value}: a Plan's decisions (a rebuild), a mapping as it is
    (the park search's ranking solution), None: none."""
    if prior is None:
        return {}
    return dict(prior.decisions if isinstance(prior, Plan) else prior)


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


# --------------------------------------------------------------------- the simulator, as layer 4 sees it
class Actuator(Protocol):
    """All of the simulator the execution (run.py, layer 4) may touch (docs/MOTION_ARCHITECTURE.md
    2.5): the writes ``execute`` makes, the read ``observe`` makes.  Rig implements it; another
    robot or simulator implements this and the kinematics, nothing above.

    Writes:
      follow(qs, steps_per_wp, smooth, side)   arm waypoints (slower with a load in the hand); side "left": the left arm
      grip(width, steps, gradual)              the gripper
      wait(ticks)                              the world settles that many physics ticks, nothing moves
      drive_base(path, allow=...)              the base along waypoints [(x, y, yaw_deg)]
      swing(q_right, q_left, label)            both arms straight in joint space (a travel-posture switch)
      declare(name, allow, side, follows)      the segment to the contact monitor (Clearance.motion)
      contact_allow(kin, allow)                a from-contact Allow narrowed to what the hand touches now
    Reads:
      snapshot() -> State                      the robot and the world now (synced into the collision model)
      arm_kin(side) -> ArmKin                  that arm's kinematics (its collision queries)
      log(label, **kw)"""

    def follow(self, qs, steps_per_wp=3, smooth=False, side="right"): ...
    def grip(self, width, steps=100, gradual=False): ...
    def wait(self, ticks): ...
    def drive_base(self, path, **kw): ...
    def swing(self, q_right, q_left, label, **kw): ...
    def declare(self, name, allow, side="right", follows=True): ...
    def contact_allow(self, kin, allow): ...
    def snapshot(self) -> State: ...
    def arm_kin(self, side="right"): ...
    def log(self, label, **kw): ...


class BaseModel(Protocol):
    """The whole-body base model the drive primitives and the park search query (docs/MOTION_ARCHITECTURE.md
    5.4): the base planner over the robot's sphere model, what the hands hold included.  Like ``kin`` it
    is handed down, never imported: skills.RigBase implements it on a rig.  It plans from the robot as it
    stands (``state`` is the State now, or now with the arms elsewhere: the loads ride as they sit in the
    hands now).

      plan(state, goal, chain, label, quiet=False) -> (steps | None, why)
            the base from state.base to goal (x, y, yaw_deg; None: as little as possible) with the arms
            leaving state's posture through ``chain`` [(name, (q_right, q_left))]; steps
            [("drive", [(x, y, yaw_deg)...]) | ("swing", name, q_right, q_left)]
      straight(state, target, label) -> (path | None, why)   the straight base move to target (the yaw the
                                                      short way round), the arms as they are
      depths(state, poses) -> [m]                     penetration in the travel posture at each base pose
      reachable(state, poses) -> [bool]               the base column can drive there (a distance field)
      drivable(state, goal) -> bool                   plan in the travel chain (skill_plans.travel_chain)"""

    def plan(self, state, goal, chain, label, quiet=False): ...
    def straight(self, state, target, label): ...
    def depths(self, state, poses): ...
    def reachable(self, state, poses): ...
    def drivable(self, state, goal): ...
