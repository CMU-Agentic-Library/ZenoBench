"""The motion primitives (docs/MOTION_ARCHITECTURE.md section 5): each makes one segment of a plan
from a State and a Spec, the same way for the park search and for the execution.

    decide_ik        a contact pose's joint solution: the prior as it is, else solved near it
    free_leg         free-space motion to a joint goal, a pose or a goal set of poses
    straight         the collision-checked TCP straight from a given joint solution
    contact_extent   how far along u the robot (and its load) keeps touching the world
    contact_segment  that stretch as an unchecked segment under a contact Allow
    holds            whether a segment made before still holds in a State (the converse: a check,
                     not a motion; run's before every segment, build's on the segments of its prior)

They know no skill and no simulator: ``kin`` (kinematics.ArmKin, its collision backend
kin.motion) and the State / Spec say everything; a primitive that cannot make its segment
returns a Failure with why -- no fallback (COLLISION_PLAN section 1, principle 2)."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass

import numpy as np

from .kinematics import tips_over
from .motion_state import Failure, Segment, Spec, aim_pose

LEAVE_GAP = 0.005         # m: closer to the world than this, the robot (and its load) still touches it
LEAVE_MARGIN = 0.01       # m: a contact exit runs this far past where the robot (and its load) first comes clear
LEAVE_MAX = 0.06          # m: ...and no further
ON_LINE = 0.005           # m: a TCP this close to a straight (and on it before its end) is on it
ON_LINE_TURN = 0.01       # rad: ...and turned this little from the straight's rotation
JOINT_GOAL_TOL = 0.01     # rad: a planned leg ending this close (every joint) to its joint goal ends at it
DENSE = 0.01              # rad: joint waypoints of a joint-space leg about this far apart (Rig._dense)
HINT_REACH = 0.001        # m: a decided solution whose TCP is this close to its pose still decides it (decide_ik)
HINT_TURN = 0.01          # rad: ...and turned this little from it (a base off its park by more is re-solved)


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


def turn(Ra, Rb):
    """rad between two rotations."""
    c = (np.trace(np.asarray(Ra, float).T @ np.asarray(Rb, float)) - 1.0) / 2.0
    return float(np.arccos(np.clip(c, -1.0, 1.0)))


def near_pose(p_a, R_a, p_b, R_b):
    """Two TCP poses the same one: within HINT_REACH and HINT_TURN (a decided solution still decides
    its pose: decide_ik, Rig._goal; a target still the one planned for: run.holds)."""
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


# ------------------------------------------------------------------------- checking a segment (docs 8.4)
PLAN_AT_START = 1e-3      # rad: the commanded arm this close (every joint) to where a segment starts is
                          # there (q_cmd is a command: the posture a drive arrives in is set exactly)
EXTENT_TOL = LEAVE_MARGIN / 2   # m: a contact exit measured again within this of the planned one is
                          # that one -- its end still clears with half the margin, and it runs at most
                          # this much further unchecked.  (One step, 2 mm, was the measure's own
                          # resolution: 7 of the 13 rebuilds of the 11-08 run were +-1 step.)
TARGET_TOL = 0.005        # m: a segment built for a contact pose whose end, at the base as it stands, has
                          # moved this far against that pose since it was built does not hold -- the
                          # tolerance its execution is judged by (skills.PICK_REACH_TOL: a hand stopped
                          # this far short of its pose is blocked), so a plan off by more before it runs
                          # would end that way.  No measured error behind it (9.3 step 2.1 skipped)
TARGET_TURN = HINT_TURN   # rad: ...turned this far
TOUCHING = {"near_world": near_world, "off_support": off_support, "in_world": in_world}   # contact criteria by name


def holds(kin, state, seg):
    """Why ``seg`` no longer holds in ``state``, or None: the arm not at its start (PLAN_AT_START);
    a segment built for a contact pose (info["aim"]) the state no longer gives -- off the pose it
    was built for by more than near_pose's HINT_REACH / HINT_TURN (the object moved, the load turned
    in the hand) -- or whose end, at the state's base, has moved against that pose by more than
    TARGET_TOL / TARGET_TURN since it was built (info["end"]: the base stopped off the one it was
    built at; the end's own offset from the pose, an IK solution's or a planner's, is what it was);
    a motion whose path is not free now (its Spec, the world as the state has it); a contact whose
    extent measured again from here (contact_extent) ends elsewhere.  Actions and anchors always
    hold; a drive holds while the arm is where it starts (its path is the base planner's, made from
    this state when navigate was planned).  The same check for the execution (run, before every
    segment) and for a builder keeping its prior's segments (docs 8.3)."""
    if seg.kind in ("action", "anchor"):
        return None
    q = state.q(kin.side)
    if np.max(np.abs(q - np.asarray(seg.q_from, float))) > PLAN_AT_START:
        return "the arm is not where the segment starts"
    aim = seg.info.get("aim")
    if aim is not None:
        now = aim_pose(state, aim)
        if now is None:
            return f"its target {aim.obj} is not in the state"
        p0, R0 = seg.info["aimed"]
        if not near_pose(p0, R0, *now):
            return (f"its target moved {np.linalg.norm(now[0] - p0):.4f} m, turned "
                    f"{np.degrees(turn(R0, now[1])):.2f} deg")
        end = seg.info.get("end")
        if end is not None:
            with query(kin, state, seg.spec):            # kin.tcp at the state's base
                p_e, R_e = kin.tcp(seg.q_end)
            off = float(np.linalg.norm((p_e - now[0]) - (np.asarray(end[0], float) - p0)))
            rot = turn(R_e @ now[1].T, np.asarray(end[1], float) @ R0.T)
            if off > TARGET_TOL or rot > TARGET_TURN:
                return f"its end moved {off:.4f} m, turned {np.degrees(rot):.2f} deg off its target"
    if seg.kind == "drive":
        return None
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
