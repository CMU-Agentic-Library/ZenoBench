"""What a motion is planned for, and by what rules (docs/MOTION_ARCHITECTURE.md section 4).

``State``: the robot and the objects as they are (Rig.observe) or as a plan assumes they will be
(a park the base is not at yet, an object the hand has not closed on yet, one let go) -- data
only, never changed in place: the helpers below return a new one.  ``Spec``: the collision rules
of one segment.  ``Segment`` / ``Plan``: what the primitives (primitives.py) and the skill plans
make, and the execution runs.  Nothing here plans, executes or knows the simulator; the collision
backend takes a State and a Spec as one query (Motion.query)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable, Mapping, Protocol

import numpy as np

from .clearance import FREE, Allow
from .tolerances import MOVED_MM

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
    object stood before the hand closed) rather than one measured in the hand.
    ``kind`` "part": the hand holds the handle of the articulated part ``name`` (docs 4.1):
    ``T_tcp_obj`` is the part frame (annotations part_pose) in the TCP frame; nothing rides on the
    hand, the part stays where State.parts puts it, and the hand's PART_HOLD links may touch it
    (touches) -- the rest of the robot may not."""
    name: str
    T_tcp_obj: np.ndarray
    kind: str = "pinch"              # pinch / edge / corner / bimanual / part
    pad: float = 0.0


@dataclass(frozen=True, eq=False)
class Aim:
    """A contact pose as a State gives it (docs/MOTION_ARCHITECTURE.md section 6): the TCP at ``T``
    in the box frame of ``obj`` standing in the world (``held`` False: a grasp) -- with ``frame``,
    ``obj`` is an articulated part and ``frame(v)`` its frame's world pose at joint value v
    (State.parts: a handle where the part stands now) -- or the TCP that
    puts the box frame of ``obj``, held in ``side``'s hand, at the world pose ``T`` (``held`` True: a
    set-down, through the hold Held.T_tcp_obj).  A plan derives its contact pose from the State it
    is built from this way and records the Aim with the pose it got (Segment.info["aim"],
    ["aimed"]); primitives.holds checks it again against the State now (aim_pose)."""
    obj: str
    T: np.ndarray
    held: bool = False
    side: str = "right"
    frame: Callable | None = None


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


TOUCH_LINKS = ("fingers", "hand")   # what of a hand a Spec.touch entry lets touch (clearance.Allow.links)
PART_HOLD = "fingers"                # the links of a hand holding a part's handle that may touch the part


@dataclass(frozen=True)
class Spec:
    """The collision rules of one segment.  ``fingers``: the hand's fingers in the collision model.
    ``exempt``: what the TCP target touches may be touched (the backend exempts by the target's
    position; never with a load in the hand).  ``hold_tilt``: a load in the hand keeps its tilt.
    ``touch``: what the hand may touch -- each entry an object or articulated part name (the
    fingers may touch it) or (name, links), links one of TOUCH_LINKS ("hand": the fingers, the
    gripper and its camera: a door pushed with the hand).  No obstacle to those links, still one
    to the rest of the arm (primitives.free_path checks that apart); ``allow`` then lists them for
    the monitor.  A part the hand holds (Held kind "part") is touched the same way without being
    listed (touches)."""
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
    each swing on the way; "scripted": a task segment (primitives.scripted, docs 5.5) -- ``info["script"]``
    its trajectory (primitives.Script: a function of the task quantity s over an interval, and what
    moves with s), ``qs`` the arm's IK continuation along it (none when the base carries it),
    ``info["executor"]`` what runs it ("follow": the arm's qs open loop;
    "ride": the base along the script's function closed on the measured part, Actuator.ride); "anchor": where an
    error comes in (docs 8.2), nothing moves.  ``target``: what the segment is for --
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
    (carry_in).  A rebuild gets them back as its prior (decisions_of)."""
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


def aim_pose(state, aim):
    """(p, R) of the TCP ``aim`` (Aim) gives in ``state``, or None: the object not in the State, or
    not in that hand."""
    if aim.held:
        h = state.held(aim.side)
        if h is None or h.name != aim.obj:
            return None
        T = np.asarray(aim.T, float) @ np.linalg.inv(np.asarray(h.T_tcp_obj, float))
    else:
        if aim.frame is not None:
            v = state.parts.get(aim.obj)
            T_obj = None if v is None else aim.frame(float(v))
        else:
            T_obj = state.objects.get(aim.obj)
        if T_obj is None:
            return None
        T = np.asarray(T_obj, float) @ np.asarray(aim.T, float)
    return T[:3, 3].copy(), T[:3, :3].copy()


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


def released(s: State, side, name, T_frame=None) -> State:
    """``side``'s hand let go of ``name``, which now stands with its box frame at T_frame (None: a
    part's handle let go -- the part stays where State.parts has it)."""
    h = s.hands.get(side, Hand(width=0.0))
    objects = s.objects if T_frame is None else {**s.objects, name: np.asarray(T_frame, float).copy()}
    return replace(s, hands={**s.hands, side: replace(h, held=None)}, objects=objects)


def with_object(s: State, name, T_frame) -> State:
    return replace(s, objects={**s.objects, name: np.asarray(T_frame, float).copy()})


def with_part(s: State, name, value) -> State:
    """The articulated part ``name`` at joint value ``value`` (rad or m)."""
    return replace(s, parts={**s.parts, name: float(value)})


MOVED_MAX = 5       # the farthest this many of the others off by more than MOVED_MM are listed


def _frame_off(Ta, Tb):
    """(mm, deg) between two 4x4 frames: the origins apart, the rotation between them."""
    Ta, Tb = np.asarray(Ta, float), np.asarray(Tb, float)
    c = (np.trace(Ta[:3, :3].T @ Tb[:3, :3]) - 1.0) / 2.0
    return round(1000.0 * float(np.linalg.norm(Tb[:3, 3] - Ta[:3, 3])), 2), \
        round(float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))), 3)


def state_offset(assumed: State, now: State, watch=()) -> dict:
    """How the State read back at an anchor (``now``) stands off the State the plan assumed there
    (``assumed``): the error that came in since the plan was built (docs/MOTION_ARCHITECTURE.md 8.2,
    9.3 step 2.1), JSON-ready, for the log only -- nothing is judged here.
      base       [mm, deg] the base off where the plan put it (the park: how it stopped)
      arm        rad, the commanded arm joints off the plan's (PLAN_AT_START judges them)
      hold_<side> {obj, kind, mm, deg, pad_mm} the hold (Held.T_tcp_obj, TCP frame) off the assumed one:
                 at the close the planned hold against the measured, after a drive the slip; or
                 {assumed, now} when the hand holds another object or none
      watch      {name: [mm, deg]} the objects the skill aims at (an articulated part: its joint value
                 off, rad or m; None: not in ``now``); one held in either State is the hold's
      moved      {name: [mm, deg]} the others off by more than MOVED_MM (knocked), the MOVED_MAX farthest"""
    b0, b1 = assumed.base, now.base
    out = {"base": [round(1000.0 * float(np.hypot(b1[0] - b0[0], b1[1] - b0[1])), 2),
                    round(abs((float(b1[2]) - float(b0[2]) + 180.0) % 360.0 - 180.0), 3)],
           "arm": round(float(max(np.max(np.abs(np.asarray(now.q_right, float) - np.asarray(assumed.q_right, float))),
                                  np.max(np.abs(np.asarray(now.q_left, float) - np.asarray(assumed.q_left, float))))),
                        4)}
    held = set()
    for side in SIDES:
        h0, h1 = assumed.held(side), now.held(side)
        held |= {h.name for h in (h0, h1) if h is not None}
        if h0 is None and h1 is None:
            continue
        if h0 is None or h1 is None or h0.name != h1.name:
            out[f"hold_{side}"] = {"assumed": h0 and h0.name, "now": h1 and h1.name}
            continue
        mm, deg = _frame_off(h0.T_tcp_obj, h1.T_tcp_obj)
        out[f"hold_{side}"] = {"obj": h0.name, "kind": h0.kind, "mm": mm, "deg": deg, "pad_mm": round(1000.0 * h0.pad, 1)}
    seen = {}
    for name in watch:
        if name in held:
            continue
        if name in assumed.parts:
            v = now.parts.get(name)
            seen[name] = None if v is None else round(float(v) - float(assumed.parts[name]), 4)
        elif name in assumed.objects:
            seen[name] = list(_frame_off(assumed.objects[name], now.objects[name])) if name in now.objects else None
    if seen:
        out["watch"] = seen
    moved = sorted(((name, _frame_off(T, now.objects[name])) for name, T in assumed.objects.items()
                    if name in now.objects and name not in held and name not in watch), key=lambda x: -x[1][0])
    moved = {n: list(d) for n, d in moved[:MOVED_MAX] if d[0] > MOVED_MM}
    if moved:
        out["moved"] = moved
    return out


def touch_entries(touch):
    """Spec.touch as ((name, links), ...): a bare name is the fingers'."""
    out = []
    for t in touch:
        name, links = (t, "fingers") if isinstance(t, str) else (str(t[0]), str(t[1]))
        if links not in TOUCH_LINKS:
            raise ValueError(f"touch {name}: links {links!r} is not one of {TOUCH_LINKS}")
        out.append((name, links))
    return tuple(out)


def touches(state, spec, side="right"):
    """What ``side``'s hand may touch in a query of ``state`` by ``spec``, as ((name, links), ...):
    spec.touch, and the part the hand holds (Held kind "part", PART_HOLD) -- one list for the
    backend (Motion.query) and the separate check of the rest of the arm (primitives.free_path)."""
    out = list(touch_entries(spec.touch))
    h = state.held(side) if state is not None else None
    if h is not None and h.kind == "part" and (h.name, PART_HOLD) not in out:
        out.append((h.name, PART_HOLD))
    return tuple(out)


# --------------------------------------------------------------------- the simulator, as layer 4 sees it
class Actuator(Protocol):
    """All of the simulator the execution (run.py, layer 4) may touch (docs/MOTION_ARCHITECTURE.md
    2.5): the writes ``execute`` makes, the read ``observe`` makes.  Rig implements it; another
    robot or simulator implements this and the kinematics, nothing above.

    Writes:
      follow(qs, steps_per_wp, smooth, side)   arm waypoints (slower with a load in the hand); side "left": the left arm
      ride(part, base_at, s_from, s_to, label, lead, rate, done)
                                               the closed loop of a task segment that carries the base
                                               (primitives.scripted): the base at base_at(s) -- the script's
                                               function, s the part's joint value -- for a commanded s kept
                                               ``lead`` ahead of the measured one, within [s_from, s_to]; stops
                                               when the part reaches ``done``, drops back behind the command
                                               (it slipped) or stalls.  -> {"done": bool, "s", "why", ...}
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
    def ride(self, part, base_at, s_from, s_to, label, lead, rate, done): ...
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
      drivable(state, goal) -> bool                   plan in the travel chain (skill_plans.travel_chain)
      clear(state, poses) -> [bool]                   the base itself (chassis and column) clear of the static
                                                      world and of the parts where ``state`` has them, at each pose
                                                      (a task segment that moves the base: primitives.scripted)"""

    def plan(self, state, goal, chain, label, quiet=False): ...
    def straight(self, state, target, label): ...
    def depths(self, state, poses): ...
    def reachable(self, state, poses): ...
    def drivable(self, state, goal): ...
    def clear(self, state, poses): ...
