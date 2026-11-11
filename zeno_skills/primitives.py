"""The motion primitives (docs/MOTION_ARCHITECTURE.md section 5): each makes one segment of a plan
from a State and a Spec, the same way for the park search and for the execution.

    decide_ik        a contact pose's joint solution: the prior as it is, else solved again
    free_leg         free-space motion to a joint goal, a pose or a goal set of poses
    straight         the collision-checked TCP straight from a given joint solution
    contact_extent   how far along u the robot (and its load) keeps touching the world
    contact_segment  that stretch as an unchecked segment under a contact Allow
    scripted         a task segment: a skill's trajectory function (Script) over its task quantity s,
                     checked whole with what moves with s (a Coupling) where s puts it
    holds            whether a segment made before still holds in a State (the converse: a check,
                     not a motion; run's before every segment, build's on the segments of its prior)

They know no skill and no simulator: ``kin`` (kinematics.ArmKin, its collision backend
kin.motion) and the State / Spec say everything; a primitive that cannot make its segment
returns a Failure with why -- no fallback (COLLISION_PLAN section 1, principle 2)."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from typing import Callable

import numpy as np

from .kinematics import tips_over
from .motion_state import Failure, Segment, Spec, aim_pose, at_base, touches, with_part

# the contact geometry and the checks' thresholds: one source with their units and where their values
# come from (tolerances.py, docs 4.5); here as the primitives' own names
from .tolerances import (EXTENT_TOL, HINT_REACH, HINT_TURN, JOINT_GOAL_TOL, LEAVE_GAP, LEAVE_MARGIN,  # noqa: F401
                         LEAVE_MAX, ON_LINE, ON_LINE_TURN, PLAN_AT_START, TARGET_TOL, TARGET_TURN)

DENSE = 0.01              # rad: joint waypoints of a joint-space leg about this far apart (Rig._dense)


# ------------------------------------------------------------------------- goals of free_leg
@dataclass(frozen=True)
class Joint:
    q: np.ndarray


@dataclass(frozen=True)
class Pose:
    p: np.ndarray
    R: np.ndarray
    q_hint: np.ndarray | None = None     # a solution of (p, R): the planner's joint goal when the pose fails


@dataclass(frozen=True)
class PoseSet:
    """Any one of ``goals`` [(p, R)]: the one the arm gets to most cheaply (batched IK near ``prefer``,
    per-joint ``weights``, plus ``cost``)."""
    goals: tuple
    cost: tuple | None = None
    prefer: np.ndarray | None = None
    weights: np.ndarray | None = None


@dataclass(frozen=True)
class JointSet:
    """Any one of the joint goals ``goals``, in order of preference: the first one free where it stands
    (the fold before hanging at the side: Rig.tuck, the place's tuck), then as a Joint."""
    goals: tuple


@dataclass(frozen=True)
class Extent:
    """contact_extent's measure: the straight waypoints of the contact (after q_from), its TCP
    length, whether it ended clear of the world."""
    q_from: np.ndarray
    qs: tuple
    length: float
    clear: bool


# ------------------------------------------------------------------------- touching predicates
# Each takes (kin, q_from) and returns touching(q): whether q is still in the contact that started at
# q_from.  contact_extent calls it with kin's queries set to the state.
def near_world(kin, q_from=None, gap=LEAVE_GAP):
    """Still in the contact while within ``gap`` of the world (a hand backing out)."""
    return lambda q: kin.near(q, gap)


def in_world(kin, q_from=None):
    """Still in the contact while the collision model says it penetrates (an end pose that touches)."""
    return lambda q: not kin.free(q)


def off_support(kin, q_from, gap=LEAVE_GAP):
    """A load lifted off its support: it touches it until the hand has risen ``gap``, whatever the
    model says (its spheres sit inside its box: 65 of 252 lifts read clear at once, T10), and
    while within ``gap`` of the world."""
    z0 = kin.tcp(np.asarray(q_from, float))[0][2]
    return lambda q: kin.tcp(q)[0][2] - z0 < gap or kin.near(q, gap)


def exit_length(kin, start, qs, touching=None):
    """(how many of the straight waypoints ``qs`` the contact takes, whether it ends clear): up to
    LEAVE_MARGIN of TCP travel past the first clear one -- clear all along that margin -- or up to
    LEAVE_MAX, or all of them.  ``touching(q)``: still in the contact (default near_world)."""
    touching = touching or near_world(kin, start)
    if not touching(start):
        return 0, True
    p0 = kin.tcp(start)[0]
    since = None                       # TCP travel where the current clear stretch began
    for i, q in enumerate(qs):
        d = float(np.linalg.norm(kin.tcp(q)[0] - p0))
        if d > LEAVE_MAX:
            return i, False
        if touching(q):
            since = None
            continue
        since = d if since is None else since
        if d - since >= LEAVE_MARGIN:
            return i + 1, True
    return len(qs), since is not None


# ------------------------------------------------------------------------- helpers
@contextmanager
def query(kin, state, spec):
    """kin's queries inside take ``state`` and ``spec`` (Motion.query); nothing to set without a
    collision backend."""
    motion = getattr(kin, "motion", None)
    with (motion.query(kin, state, spec) if motion is not None and hasattr(motion, "query") else nullcontext()):
        yield


def dense(qa, qb):
    """Straight joint interpolation qa -> qb, about DENSE apart (qa left out)."""
    qa, qb = np.asarray(qa, float), np.asarray(qb, float)
    k = max(2, int(np.max(np.abs(qb - qa)) / DENSE))
    return [qa + (qb - qa) * u for u in np.linspace(0, 1, k)[1:]]


def via(q0, qs):
    """Dense joint waypoints from q0 through ``qs`` (a planner's trajectory)."""
    out, qa = [], np.asarray(q0, float)
    for qb in qs:
        out += dense(qa, qb)
        qa = np.asarray(qb, float)
    return out


def free_path(kin, state, spec, qs):
    """``qs`` (joint waypoints, the first the start) free in ``state`` by ``spec``: the whole robot
    checked, what the hand may touch (spec.touch, a part it holds: motion_state.touches) no
    obstacle to its touching links -- and the arm without them clear of it too
    (Kinematics.path_free_only)."""
    t = touches(state, spec, kin.side)
    with query(kin, state, spec):
        if not kin.path_free(list(qs)):
            return False
        return not t or kin.path_free_only(list(qs), t)


def free_at(kin, state, spec, q):
    """The pose ``q`` alone free in ``state`` by ``spec`` (free_path's rules at one point)."""
    t = touches(state, spec, kin.side)
    with query(kin, state, spec):
        if not kin.free(q):
            return False
        return not t or kin.path_free_only([q, q], t)


def turn(Ra, Rb):
    """rad between two rotations."""
    c = (np.trace(np.asarray(Ra, float).T @ np.asarray(Rb, float)) - 1.0) / 2.0
    return float(np.arccos(np.clip(c, -1.0, 1.0)))


def near_pose(p_a, R_a, p_b, R_b):
    """Two TCP poses the same one: within HINT_REACH and HINT_TURN (a decided solution still decides
    its pose: decide_ik, Rig._goal)."""
    return float(np.linalg.norm(np.asarray(p_a, float) - np.asarray(p_b, float))) <= HINT_REACH and \
        turn(R_a, R_b) <= HINT_TURN


def _why_straight(kin, q0, p, R, step):
    """Why the straight q0 -> (p, R) failed: it collides, or there is no IK along it."""
    scene, kin.scene = kin.scene, None
    try:
        ok = kin.cart_path(q0, p, R, step=step)[1]
    finally:
        kin.scene = scene
    return "it collides" if ok else "no IK along it"


def _first(first, n):
    """A set's goal decided before -- (index, the size of its set): seg.info["chosen"], ["goals"] --
    as an index into a set of n goals: only while the set is as big as the one it was chosen from
    (a set made from the state changes its layout with it: skills._carry_goals has 2 or 3 heights
    per spot), else None, chosen again."""
    if first is None:
        return None
    i, size = int(first[0]), int(first[1])
    return i if size == n and 0 <= i < n else None


# ------------------------------------------------------------------------- primitives
def decide_ik(kin, state, spec, p, R, prior, seeds=()):
    """The joint solution of a contact pose (p, R) -- the decision that binds the segments around it
    (docs 5.7, 8.1): ``prior`` itself while its TCP is within HINT_REACH / HINT_TURN of (p, R) and it
    is free by ``spec`` in ``state`` (a rebuild stays on the branch the plan was made on, and out of
    the planner's noise: a re-solve 0.6 mrad off a solution, its waist 1 mrad inside the limit,
    planned 1 time in 4 where the solution itself planned 4 in 4 -- T04, Rig._goal); else solved in
    the collision model, ``prior`` the first seed, ``seeds`` after it -- Motion.ik's global choice,
    not a local re-solve on the prior's branch (Rig._goal's): nearness to the prior, the joint-limit
    margin and IK_MANIP_W's manipulability, so it may land up to ~0.3 rad off the prior (T20, docs
    9.3 step 2.2).  (q, "prior" | "solved"), or None: no collision-free solution (the caller says
    which pose in its Failure)."""
    p, R = np.asarray(p, float), np.asarray(R, float)
    prior = None if prior is None else np.asarray(prior, float)
    with query(kin, state, spec):
        if prior is not None and near_pose(*kin.tcp(prior), p, R) and kin.free(prior):
            return prior.copy(), "prior"
        q, ok = kin.ik_global(p, R, seeds=([] if prior is None else [prior]) + [np.asarray(s, float) for s in seeds])
    return (np.asarray(q, float), "solved") if ok else None


def free_leg(kin, state, spec, goal, name, step=0.01, q_from=None, first=None):
    """Free-space motion of ``kin``'s arm from q_from (default the state's) to ``goal``.
    Joint: the straight joint move when it is free (and keeps a held load level with
    spec.hold_tilt), else a trajectory; a tilt-held trajectory ends at the goal's pose, so it must
    end at the goal itself or a free, level joint move must join it there.  Pose: the straight TCP
    line, else to q_hint (its solution) as a Joint is, else (no q_hint) the planner to the pose.
    PoseSet: the cheapest reachable goal (batched IK), then as a Pose with its solution.  JointSet:
    the first goal free where it stands, then as a Joint.  ``first``: a set's goal decided before,
    (info["chosen"], info["goals"]) of a plan's segment -- that one while its set is the same size
    (_first) and it is reachable (PoseSet) / free (JointSet), else chosen again."""
    q0 = np.asarray(state.q(kin.side) if q_from is None else q_from, float)
    with query(kin, state, spec):
        if isinstance(goal, JointSet):
            f = _first(first, len(goal.goals))
            order = sorted(range(len(goal.goals)), key=lambda j: j != f)
            i = next((i for i in order if kin.free(np.asarray(goal.goals[i], float))), None)
            if i is None:
                return Failure(f"every goal of {len(goal.goals)} collides", name)
            seg = free_leg(kin, state, spec, Joint(np.asarray(goal.goals[i], float)), name, step, q0)
            if isinstance(seg, Segment):
                seg = Segment(seg.name, seg.spec, seg.q_from, seg.qs, target=seg.target,
                              info={**seg.info, "chosen": i, "goals": len(goal.goals)})
            return seg
        if isinstance(goal, PoseSet):
            ref = q0 if goal.prefer is None else np.asarray(goal.prefer, float)
            w = np.ones(len(ref)) if goal.weights is None else np.asarray(goal.weights, float)
            sols = kin.ik_set(list(goal.goals), ref, weights=w)
            cost = np.zeros(len(goal.goals)) if goal.cost is None else np.asarray(goal.cost, float)
            score = np.array([np.inf if q is None else float(np.max(np.abs(q - ref) * w)) + c
                              for q, c in zip(sols, cost)])
            i = int(np.argmin(score))
            f = _first(first, len(sols))
            if f is not None and sols[f] is not None:
                i = f
            if not np.isfinite(score[i]):
                return Failure(f"no goal of {len(goal.goals)} reachable", name)
            p, R = goal.goals[i]
            seg = free_leg(kin, state, spec, Pose(np.asarray(p, float), np.asarray(R, float), sols[i]), name,
                           step, q0)
            if isinstance(seg, Segment):
                seg = Segment(seg.name, seg.spec, seg.q_from, seg.qs, target=seg.target,
                              info={**seg.info, "chosen": i, "goals": len(goal.goals)})
            return seg
        if isinstance(goal, Joint):
            q1 = np.asarray(goal.q, float)
            if kin.segment_free(q0, q1) and not (spec.hold_tilt and tips_over(kin, q0, q1)):
                return Segment(name, spec, q0, tuple(dense(q0, q1)), target=("q", q1), info={"how": "joint"})
            qs, status = kin.plan(q0, q1, carry=spec.hold_tilt)
            if qs is None:
                return Failure(f"no collision-free trajectory to the joint goal ({status})", name)
            end = np.asarray(qs[-1], float)
            if np.max(np.abs(end - q1)) > JOINT_GOAL_TOL:
                if not (kin.segment_free(end, q1) and not (spec.hold_tilt and tips_over(kin, end, q1))):
                    return Failure("the tilt-held trajectory ends off the joint goal", name)
                qs = list(qs) + [q1]
            return Segment(name, spec, q0, tuple(via(q0, qs)), target=("q", q1), info={"how": "planned"})
        p, R = np.asarray(goal.p, float), np.asarray(goal.R, float)
        qs, ok = kin.cart_path(q0, p, R, step=step)
        if ok:
            return Segment(name, spec, q0, tuple(qs), target=("pose", p, R), info={"how": "straight"})
        if goal.q_hint is not None:
            # a solution of the goal (the park search's, the PoseSet's IK): the straight joint move
            # to it when free, else the joint plan, with a load the tilt held (Kinematics.plan,
            # carry: else the tilt-held plan to its pose).  Not plan_to's pose plan first: with a
            # load that and the same plan again after the joint plan is a retry (T01 s11 11-08,
            # 6.1 s to FINETUNE_TRAJOPT_FAIL, then 0.7 s to the same pose); without one it never
            # made pick_reach (11-08 run: 0 of 150 planned) and may end on another solution than
            # the one the park search ranked
            qh = np.asarray(goal.q_hint, float)
            if kin.segment_free(q0, qh) and not (spec.hold_tilt and tips_over(kin, q0, qh)):
                return Segment(name, spec, q0, tuple(dense(q0, qh)), target=("pose", p, R), info={"how": "joint"})
            qs, status = kin.plan(q0, qh, carry=spec.hold_tilt)
            how = "planned (tilt held)" if spec.hold_tilt else "joint"
        else:
            qs, status = kin.plan_to(q0, p, R, carry=spec.hold_tilt)
            how = status
        if qs is None:
            return Failure(f"no collision-free path to the pose ({status})", name)
        return Segment(name, spec, q0, tuple(via(q0, qs)), target=("pose", p, R), info={"how": how})


def straight(kin, state, spec, p, R, name, step=0.003, q_from=None):
    """The collision-checked TCP straight from q_from (default the state's) to (p, R): from that
    joint solution, never from another solution of its start (T20 bottle_on_cabinet)."""
    q0 = np.asarray(state.q(kin.side) if q_from is None else q_from, float)
    p, R = np.asarray(p, float), np.asarray(R, float)
    t = touches(state, spec, kin.side)
    with query(kin, state, spec):
        qs, ok = kin.cart_path(q0, p, R, step=step)
        if not ok:
            return Failure(f"no collision-free straight ({_why_straight(kin, q0, p, R, step)})", name)
        if t and not kin.path_free_only([q0] + list(qs), t):
            return Failure(f"no collision-free straight (the arm, not its touching links, touches "
                           f"{', '.join(n for n, _ in t)})", name)
    return Segment(name, spec, q0, tuple(qs), target=("pose", p, R),
                   info={"length": float(np.linalg.norm(p - kin.tcp(q0)[0]))})


def contact_extent(kin, state, spec, u, touching, name, step=0.004, q_from=None):
    """How far along the unit direction u the robot (and its load) keeps touching the world from
    q_from (default the state's): the kinematic straight along u as far as the arm has IK (at
    most LEAVE_MAX), measured by exit_length with ``touching`` (near_world, off_support, in_world).  Failure when it still touches where the
    straight ends (LEAVE_MAX, or the arm runs out of IK)."""
    q0 = np.asarray(state.q(kin.side) if q_from is None else q_from, float)
    u = np.asarray(u, float) / np.linalg.norm(u)
    with query(kin, state, spec):
        p0, R0 = kin.tcp(q0)
        scene, kin.scene = kin.scene, None
        try:
            line, _ = kin.cart_path(q0, p0 + LEAVE_MAX * u, R0, step=step)
        finally:
            kin.scene = scene
        n, clear = exit_length(kin, q0, line, touching(kin, q0))
    if not clear:
        reach = float(np.linalg.norm(kin.tcp(line[-1])[0] - p0)) if line else 0.0
        if reach < LEAVE_MAX - step:
            return Failure(f"the arm has IK only {reach:.3f} m along the exit and still touches there", name)
        return Failure(f"still touching {LEAVE_MAX} m along the exit", name)
    qs = tuple(line[:n])
    length = float(np.linalg.norm(kin.tcp(qs[-1])[0] - p0)) if qs else 0.0
    return Extent(q0, qs, length, True)


def contact_segment(spec, extent, name):
    """The contact a contact_extent measured, as a segment run under spec.allow (a contact Allow:
    LEAVE_CONTACT, lifting; unchecked, only what is touched at its start may be touched)."""
    return Segment(name, spec, extent.q_from, extent.qs, target=None, info={"length": extent.length})


# ------------------------------------------------------------------------- task segments (3.1, 5.5)
# Couplings: what moves with a task segment's quantity s, and where the frame its TCP is written in
# stands then -- named, like the touching predicates.  value(state): s as the state has it (None:
# nothing moves); moved(state, s): the state with it at s; frame(state, s): that frame's world pose.
@dataclass(frozen=True, eq=False)
class PartAt:
    """The articulated part ``part`` at joint value s, its handle in the hand: a door on its hinge
    (kind "hinge"), a drawer on its slide ("slider").  ``pose(v)``: the world pose (4x4) of the part
    frame at joint value v (annotations part_pose, handed down by the skill's job: no rig here)."""
    kind: str
    part: str
    pose: Callable

    def value(self, state):
        return state.parts.get(self.part)

    def moved(self, state, s):
        return with_part(state, self.part, s)

    def frame(self, state, s):
        return np.asarray(self.pose(float(s)), float)


@dataclass(frozen=True, eq=False)
class Still:
    """Nothing moves with s; the frame is the object ``obj`` where the State has it (a pot stirred in,
    a table wiped)."""
    obj: str
    kind: str = "still"

    def value(self, state):
        return None

    def moved(self, state, s):
        return state

    def frame(self, state, s):
        return np.asarray(state.objects[self.obj], float)


def hinge(part, pose):
    return PartAt("hinge", part, pose)


def slider(part, pose):
    return PartAt("slider", part, pose)


def still(obj):
    return Still(obj)


COUPLINGS = {"hinge": hinge, "slider": slider, "still": still}   # couplings by name


@dataclass(frozen=True, eq=False)
class Script:
    """A task segment's trajectory (docs 3.1): a function and its interval, never a list of points.
    The task quantity s (a hinge angle, a drawer's travel, a phase -- never a robot quantity) runs
    from ``s0`` to ``s1``; ``coupling`` (PartAt / Still) moves what moves with it and gives the frame;
    ``tcp(s)``: the TCP's pose (4x4) in that frame, None: rigid in it as it stands at s0 (a hand on a
    handle).  ``carry``: how the robot follows -- "base": the arm stays, the base moves rigidly with
    the frame (riding a door; tcp None); "arm": the base stays, the arm follows the TCP, IK continued
    from the arm at s0.  ``step``: the s step the plan checks at (docs 2.4: by angle or travel); the
    execution samples the same function at its own rate."""
    coupling: object
    s0: float
    s1: float
    step: float
    tcp: Callable | None = None
    carry: str = "base"

    def samples(self):
        """s0 .. s1 at most ``step`` apart, both ends included."""
        n = max(1, int(np.ceil(abs(self.s1 - self.s0) / self.step - 1e-9)))
        return np.linspace(self.s0, self.s1, n + 1)


TRACK_KW = ("lead", "rate", "done")   # what a ride's closed loop needs (Actuator.ride)


def part_start(script, state, track=None):
    """Why the part a task segment couples is not where it can start, or None.  A ride (``track``)
    starts its command at the measured value anywhere along [s0, s1] and up to its lead short of s0
    (the command never leaves the script's interval, so a part further back would lag the base
    from the start); an arm task holds the part rigid from s0: within TARGET_TOL of it."""
    v = script.coupling.value(state)
    if v is None:
        return None
    sign = 1.0 if script.s1 >= script.s0 else -1.0
    back, ahead = (track["lead"], abs(script.s1 - script.s0)) if track else (TARGET_TOL, TARGET_TOL)
    if not -back <= sign * (v - script.s0) <= ahead:
        return f"{script.coupling.part} is at {v:.4f}, the task segment starts at {script.s0:.4f}"
    return None


def _pose4(p, R):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, p
    return T


def _base4(base):
    x, y, yaw = base
    c, s_ = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    return np.array([[c, -s_, 0, x], [s_, c, 0, y], [0, 0, 1, 0], [0, 0, 0, 1]], float)


def ride_base(script, base0, s, state=None):
    """The base (x, y, yaw_deg) at s of a task segment that carries the base: rigid with the
    coupling's frame from ``base0`` at s0 (docs 5.5) -- the function the plan checks and the ride
    executes.  ``state``: for a frame the State places (Still)."""
    c = script.coupling
    B = c.frame(state, s) @ np.linalg.inv(c.frame(state, script.s0)) @ _base4(base0)
    return float(B[0, 3]), float(B[1, 3]), float(np.degrees(np.arctan2(B[1, 0], B[0, 0])))


def _script_path(kin, state, spec, script, info, base=None, arm_step=0.005):
    """Make (carry "arm") or check (carry "base") the task segment ``script`` from ``state``: each s
    of script.samples() in the world the coupling gives -- carry "base": the base at ride_base,
    clear by ``base`` (motion_state.BaseModel) where given, the robot free there (free_at); carry
    "arm": the TCP at s by the kinematic straight from the arm at the s before (IK continued), that
    motion free with the coupling at s.  (qs, s at each q) or why it fails (a str)."""
    q, qs, s_at = np.asarray(state.q(kin.side), float), [], []
    for i, s in enumerate(script.samples()):
        st = script.coupling.moved(state, s)
        where = f"s={s:.3f}"
        if script.carry == "base":
            b = ride_base(script, info["base0"], s, state)
            st = at_base(st, b)
            if base is not None and not base.clear(st, [b])[0]:
                return f"the base collides at {where}"
            if not free_at(kin, st, spec, q):
                return f"the robot collides at {where}{_explain(kin, st, spec, q)}"
            continue
        if i == 0:
            continue
        rel = info["rel"] if script.tcp is None else np.asarray(script.tcp(s), float)
        T = script.coupling.frame(st, s) @ rel
        with query(kin, st, spec):
            scene, kin.scene = kin.scene, None
            try:
                line, ok = kin.cart_path(q, T[:3, 3], T[:3, :3], step=arm_step)
            finally:
                kin.scene = scene
        if not ok:
            return f"no IK along the task at {where}"
        if line and not free_path(kin, st, spec, [q] + list(line)):
            return f"the robot collides by {where}"
        qs += [np.asarray(x, float) for x in line]
        s_at += [float(s)] * len(line)
        q = qs[-1] if qs else q
    return qs, s_at


def _explain(kin, state, spec, q):
    explain = getattr(kin, "explain", None)
    if explain is None:
        return ""
    with query(kin, state, spec):
        return f": {explain(q)}" if not kin.free(q) else ""


def scripted(kin, state, spec, script, name, base=None, track=None, arm_step=0.005, clear=None):
    """A task segment (docs 3, 5.5) from the arm and the base as ``state`` has them: ``script``
    (Script) checked whole at its samples -- what the coupling moves where s puts it, what the hand
    may touch by spec.touch and its held part, the base by ``base`` (motion_state.BaseModel) where
    it moves.  All or nothing: one sample that collides is a Failure, none skipped.  It starts where
    the state is: the coupled part where it can start (part_start), and a TCP the script
    places (tcp given) within ON_LINE / ON_LINE_TURN of the arm's.
    carry "base": the executor is the ride (Actuator.ride: the base at ride_base of the commanded s,
    closed on the measured part), ``track`` its TRACK_KW; carry "arm": "follow", the arm's IK
    continuation (``qs``, made at ``arm_step`` m) open loop.  ``clear``: the failure exit a ride that
    stops short asks for (motion_state.clearing's open_width / leave: a hand on a handle lets go and
    backs out, docs 8.6).  info: script, base0, rel (the TCP in the frame at s0), s_at (s of each of
    qs), executor, track, clear."""
    if script.carry not in ("base", "arm"):
        raise ValueError(f"{name}: carry is 'base' or 'arm', not {script.carry!r}")
    track = dict(track or {})
    if script.carry == "base":
        missing = [k for k in TRACK_KW if k not in track]
        if script.tcp is not None or not isinstance(script.coupling, PartAt) or missing:
            raise ValueError(f"{name}: a ride keeps the arm rigid with a part it holds (tcp None, a PartAt coupling) "
                             f"and is tracked ({', '.join(missing) or 'ok'} missing)")
    why = part_start(script, state, track or None)
    if why is not None:
        return Failure(why, name)
    q0 = np.asarray(state.q(kin.side), float)
    with query(kin, state, spec):
        T0 = _pose4(*kin.tcp(q0))
    F0 = script.coupling.frame(state, script.s0)
    rel = np.linalg.inv(F0) @ T0
    if script.tcp is not None:
        start = F0 @ np.asarray(script.tcp(script.s0), float)
        if np.linalg.norm(start[:3, 3] - T0[:3, 3]) > ON_LINE or turn(start[:3, :3], T0[:3, :3]) > ON_LINE_TURN:
            return Failure("the arm is not at the task's start", name)
    info = {"script": script, "base0": tuple(map(float, state.base)), "rel": rel, "side": kin.side}
    out = _script_path(kin, state, spec, script, info, base, arm_step)
    if isinstance(out, str):
        return Failure(f"the task segment: {out}", name)
    qs, s_at = out
    return Segment(name, spec, q0, tuple(qs), kind="scripted", target=("s", float(script.s1)),
                   info={**info, "s_at": tuple(s_at), "executor": "ride" if script.carry == "base" else "follow",
                         "track": track, "clear": dict(clear) if clear else None})


# ------------------------------------------------------------------------- the base (5.4)
def drive(base, state, goal, chain, name, spec=None, **drive_kw):
    """The base to ``goal`` (x, y, yaw_deg; None: as little as possible) on a whole-body plan of
    ``base`` (motion_state.BaseModel: what the hands hold counts), the arms leaving the state's
    posture through ``chain`` [(name, (q_right, q_left))] where the planner puts each switch (a
    checked straight joint move: Rig.swing).  One segment, kind "drive": the drives and swings in
    info["steps"], ``drive_kw`` (speed, turn, ramp) for the execution.  Failure when there is none."""
    from .clearance import FREE
    steps, why = base.plan(state, goal, chain, name)
    if steps is None:
        return Failure(why, name)
    arm = tuple(np.asarray(st[2], float) for st in steps if st[0] == "swing")
    return Segment(name, spec or Spec(allow=FREE), np.asarray(state.q_right, float), arm, kind="drive",
                   target=("base", None if goal is None else tuple(map(float, goal))),
                   info={"steps": tuple(steps), "drive_kw": drive_kw})


def drive_straight(base, state, target, name, spec=None, **drive_kw):
    """The base straight to ``target`` (x, y, yaw_deg) -- a turn in place, a sidestep, a retreat:
    the motion the caller asks for, not a search -- the whole robot checked along it, the arms as
    they are (BaseModel.straight).  Failure, nothing moves, when it is blocked."""
    from .clearance import FREE
    path, why = base.straight(state, target, name)
    if path is None:
        return Failure(why, name)
    path = [tuple(map(float, w)) for w in path]
    return Segment(name, spec or Spec(allow=FREE), np.asarray(state.q_right, float), (), kind="drive",
                   target=("base", path[-1]), info={"steps": (("drive", path),), "drive_kw": drive_kw})


# ------------------------------------------------------------------------- checking a segment (docs 8.4)
# PLAN_AT_START, EXTENT_TOL, TARGET_TOL, TARGET_TURN: tolerances.py (imported above)
TOUCHING = {"near_world": near_world, "off_support": off_support, "in_world": in_world}   # contact criteria by name


def aim_excess(kin, state, seg):
    """A contact pose's segment (info["aim"]) in ``state``: (off m, rot rad) its end at the state's base
    stands further off the pose the state gives now than it did when built (holds judges these by
    info["tol"]), and (m, rad) the pose itself moved since -- None when the target is not in the state."""
    aim = seg.info["aim"]
    now = aim_pose(state, aim)
    if now is None:
        return None
    (p0, R0), (p_b, R_b) = seg.info["aimed"], seg.info["end"]
    with query(kin, state, seg.spec):                # kin.tcp at the state's base
        p_e, R_e = kin.tcp(seg.q_end)
    off = float(np.linalg.norm((p_e - now[0]) - (np.asarray(p_b, float) - p0)))
    rot = turn(R_e @ now[1].T, np.asarray(R_b, float) @ R0.T)
    return off, rot, float(np.linalg.norm(now[0] - p0)), turn(R0, now[1])


def holds(kin, state, seg):
    """Why ``seg`` no longer holds in ``state``, or None: the arm not at its start (PLAN_AT_START);
    a segment built for a contact pose (info["aim"]) whose end, at the state's base, stands off the
    pose the state gives now by more than it did when built -- more than its info["tol"] (m, rad):
    the object moved, the load turned in the hand, the base stopped off its park all count alike
    (the end's own offset from the pose, an IK solution's or a planner's, is what it was) -- or
    whose target is not in the state; a motion whose path is not free now (its Spec, the world as
    the state has it); a contact whose extent measured again from here (contact_extent) ends
    elsewhere.  Actions and anchors always hold; a drive holds while the arm is where it starts
    (its path is the base planner's, made from this state when navigate was planned).  A task
    segment (scripted) holds while the base stands where it was built (carry "base": TARGET_TOL /
    TARGET_TURN), the part it moves is where it can start (part_start), and the robot
    is free along it in the world as the state has it now -- carry "base": the same function from
    the base it was built at; carry "arm": its qs, each with the coupling at its s.  The base along a
    ride is not checked again (built against the static world; no BaseModel here).  The same
    check for the execution (run, before every segment) and for a builder keeping its prior's
    segments (docs 8.3)."""
    if seg.kind in ("action", "anchor"):
        return None
    q = state.q(kin.side)
    if np.max(np.abs(q - np.asarray(seg.q_from, float))) > PLAN_AT_START:
        return "the arm is not where the segment starts"
    if seg.info.get("aim") is not None:
        ex = aim_excess(kin, state, seg)
        if ex is None:
            return f"its target {seg.info['aim'].obj} is not in the state"
        off, rot, moved, moved_turn = ex
        tol, tol_turn = seg.info["tol"]
        if off > tol or rot > tol_turn:
            return (f"its end is {off:.4f} m, {np.degrees(rot):.2f} deg further off its target than built "
                    f"(the target moved {moved:.4f} m, turned {np.degrees(moved_turn):.2f} deg)")
    if seg.kind == "drive":
        return None
    if seg.kind == "scripted":
        info = seg.info
        script = info["script"]
        if script.carry == "base":
            b0 = info["base0"]
            off = float(np.hypot(state.base[0] - b0[0], state.base[1] - b0[1]))
            rot = abs(np.radians((state.base[2] - b0[2] + 180.0) % 360.0 - 180.0))
            if off > TARGET_TOL or rot > TARGET_TURN:
                return f"the base is {off:.4f} m, {np.degrees(rot):.2f} deg off where the task segment was built"
        why = part_start(script, state, info["track"] or None)
        if why is not None:
            return why
        if script.carry == "base":
            why = _script_path(kin, state, seg.spec, script, info)
            why = why if isinstance(why, str) else None
        else:
            why, prev = None, np.asarray(seg.q_from, float)
            for s in sorted(set(info["s_at"]), key=list(info["s_at"]).index):
                group = [q for q, s_ in zip(seg.qs, info["s_at"]) if s_ == s]
                if not free_path(kin, script.coupling.moved(state, s), seg.spec, [prev] + group):
                    why = f"the robot collides by s={s:.3f}"
                    break
                prev = group[-1]
        return None if why is None else f"the task segment now: {why}"
    if seg.spec.allow.from_contact:
        ext = contact_extent(kin, state, seg.spec, seg.info["u"], TOUCHING[seg.info["touching"]], seg.name,
                             step=seg.info["step"], q_from=q)
        if isinstance(ext, Failure):
            return f"the contact measured again: {ext.why}"
        if abs(ext.length - seg.info.get("length", 0.0)) > EXTENT_TOL:
            return f"the contact measured again is {ext.length:.3f} m, planned {seg.info.get('length', 0.0):.3f} m"
        return None
    if not seg.qs:
        return None
    if not free_path(kin, state, seg.spec, [q] + list(seg.qs)):
        with query(kin, state, seg.spec):
            # where along it and into what
            at = next((i for i, qi in enumerate(seg.qs) if not kin.free(qi)), None)
            what = "" if at is None else f" at {at + 1}/{len(seg.qs)}: {kin.explain(seg.qs[at])}"
            return "its path collides now" + (what or " (between waypoints)")
    return None
