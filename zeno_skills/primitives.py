"""The motion primitives (docs/MOTION_ARCHITECTURE.md section 5): each makes one segment of a plan
from a State and a Spec, the same way for the park search and for the execution.

    free_leg         free-space motion to a joint goal, a pose or a goal set of poses
    straight         the collision-checked TCP straight from a given joint solution
    contact_extent   how far along u the robot (and its load) keeps touching the world
    contact_segment  that stretch as an unchecked segment under a contact Allow

They know no skill and no simulator: ``kin`` (kinematics.ArmKin, its collision backend
kin.motion) and the State / Spec say everything; a primitive that cannot make its segment
returns a Failure with why -- no fallback (COLLISION_PLAN section 1, principle 2)."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass

import numpy as np

from .kinematics import tips_over
from .motion_state import Failure, Segment, Spec

LEAVE_GAP = 0.005         # m: closer to the world than this, the robot (and its load) still touches it
LEAVE_MARGIN = 0.01       # m: a contact exit runs this far past where the robot (and its load) first comes clear
LEAVE_MAX = 0.06          # m: ...and no further
ON_LINE = 0.005           # m: a TCP this close to a straight (and on it before its end) is on it
ON_LINE_TURN = 0.01       # rad: ...and turned this little from the straight's rotation
JOINT_GOAL_TOL = 0.01     # rad: a planned leg ending this close (every joint) to its joint goal ends at it
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
    checked, the objects of spec.touch no obstacle to the fingers -- and the arm without its
    fingers clear of them too (Kinematics.path_free_only)."""
    with query(kin, state, spec):
        if not kin.path_free(list(qs)):
            return False
        return not spec.touch or kin.path_free_only(list(qs), spec.touch)


def _why_straight(kin, q0, p, R, step):
    """Why the straight q0 -> (p, R) failed: it collides, or there is no IK along it."""
    scene, kin.scene = kin.scene, None
    try:
        ok = kin.cart_path(q0, p, R, step=step)[1]
    finally:
        kin.scene = scene
    return "it collides" if ok else "no IK along it"


# ------------------------------------------------------------------------- primitives
def free_leg(kin, state, spec, goal, name, step=0.01, q_from=None):
    """Free-space motion of ``kin``'s arm from q_from (default the state's) to ``goal``.
    Joint: the straight joint move when it is free (and keeps a held load level with
    spec.hold_tilt), else a trajectory; a tilt-held trajectory ends at the goal's pose, so it must
    end at the goal itself or a free, level joint move must join it there.  Pose: the straight TCP
    line, else to q_hint (its solution) as a Joint is, else (no q_hint) the planner to the pose.
    PoseSet: the cheapest reachable goal (batched IK), then as a Pose with its solution.  JointSet:
    the first goal free where it stands, then as a Joint."""
    q0 = np.asarray(state.q(kin.side) if q_from is None else q_from, float)
    with query(kin, state, spec):
        if isinstance(goal, JointSet):
            i = next((i for i, g in enumerate(goal.goals) if kin.free(np.asarray(g, float))), None)
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
    with query(kin, state, spec):
        qs, ok = kin.cart_path(q0, p, R, step=step)
        if not ok:
            return Failure(f"no collision-free straight ({_why_straight(kin, q0, p, R, step)})", name)
        if spec.touch and not kin.path_free_only([q0] + list(qs), spec.touch):
            return Failure(f"no collision-free straight (the arm, not its fingers, touches {', '.join(spec.touch)})",
                           name)
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
