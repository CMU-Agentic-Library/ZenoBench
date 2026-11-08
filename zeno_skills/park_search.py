"""Where to park the base for a skill (docs/MOTION_ARCHITECTURE.md section 7): candidates around
the skill's goals, the cheap tests on all of them at once, a ranking, then the skill's own plan
builder in that order -- the first park whose whole plan can be made wins, with that plan.

find_park knows nothing of arms beyond a kinematic IK for the ranking: whether the skill can be
done from a park is the skill's builder's answer (skill_plans), the one the execution builds again
with.  The old planner.find_park stays for the skills not moved yet."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .kinematics import manipulability
from .motion_state import Failure, at_base, with_arm

RADII = np.arange(0.45, 1.0, 0.05)    # m: rings of base positions around a goal's centre (as planner.find_park)
ANGLE_STEP = 15                        # deg between positions on a ring
YAW_OFFSETS = (-60, -45, -30, -15, 0, 15, 30, -75, -90, 45, 60, 75, 90)   # deg off facing the centre
SHOULDER = (0.09, -0.18)               # m: right shoulder in the base frame
REACH_XY = 0.78                        # m: the arm's horizontal reach from the shoulder (prefilter)
REACH_Z = (0.0, 1.5)                   # m: TCP heights the torso lift reaches (down to the floor)
FACE_LEFT = 30                         # deg: the right arm on the -y side, facing slightly left is cheaper...
FACE_COST = 0.002                      # m of cost per deg off that
NEAR_COST = 0.15                       # m of cost per m away from ``near``
MAX_PER_GOAL = 120                     # cheapest candidates per goal past the reach and footprint tests
LIMIT_CLEAR = 0.15                     # rad: arm joints closer than this to a limit cost (planner.LIMIT_CLEAR)
PARK_DIST_W = 0.5                      # weight of the candidate's own cost in the ranking (planner.PARK_DIST_W)
BUILD_S = 20.0                         # s: plans are built in rank order for at most this long (0.45 s each
                                       # in T20 s10 11-08, where 8 were too few: the reach-in straight
                                       # into the cabinet failed on 5 of the first 8)
BUILD_MAX = 60                         # ...and at most this many


@dataclass(frozen=True)
class Problem:
    """What a skill asks of a park search.
    goals:  per goal of the goal set, (TCP points the arm must reach (prefilter), the relay pose
            (p, R) the ranking IK solves, cost in m).
    build:  build(state_at_park, k, q_rank) -> Plan | Failure, the skill's plan builder; q_rank
            the ranking's kinematic solution of goal k's relay pose (a seed, never a check).
    arrive: arrive(x, y, yaw) -> the arm posture at that park (what the drive arrives in, or the
            posture now where the base will not move).
    near:   (x, y) or (x, y, yaw): parks cost NEAR_COST per m away from it; with a yaw it is the
            current pose, a candidate of its own, tried first.
    prefer: base poses tried before the rings (a scene's known good park, the fridge's open side).
    travel: the arm posture the base drives in (the whole-body test at the parks)."""
    goals: tuple
    build: Callable
    arrive: Callable
    travel: np.ndarray
    near: tuple | None = None
    prefer: tuple = ()
    label: str = "park"


@dataclass
class Found:
    x: float
    y: float
    yaw: float
    k: int
    plan: object
    q_rank: np.ndarray | None = None
    diag: dict = field(default_factory=dict)

    @property
    def pose(self):
        return (self.x, self.y, self.yaw)


def candidates(problem):
    """[(cost, x, y, yaw, k)] cheapest first: the current pose and the preferred ones, then the rings."""
    out = []
    for k, (points, _, gcost) in enumerate(problem.goals):
        c = np.mean([np.asarray(p, float)[:2] for p in points], axis=0)
        for r in RADII:
            for ang in np.radians(np.arange(0, 360, ANGLE_STEP)):
                x, y = c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)
                face = math.degrees(math.atan2(c[1] - y, c[0] - x))
                for off in YAW_OFFSETS:
                    cost = r + FACE_COST * abs(off + FACE_LEFT) + float(gcost)
                    if problem.near is not None:
                        cost += NEAR_COST * math.hypot(x - problem.near[0], y - problem.near[1])
                    out.append((cost, x, y, face + off, k))
    out.sort(key=lambda t: t[0])
    first = []
    for k, (_, _, gcost) in enumerate(problem.goals):
        if problem.near is not None and len(problem.near) == 3:
            first.append((-1.0 + float(gcost) * 1e-3, *map(float, problem.near), k))
        first += [(-0.5 + float(gcost) * 1e-3, *map(float, p), k) for p in problem.prefer]
    return sorted(first, key=lambda t: t[0]) + out


def reachable(cands, problem):
    """Per candidate: every TCP point within REACH_XY of the right shoulder, heights in REACH_Z."""
    out = []
    for _, x, y, yaw, k in cands:
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        sh = np.array([x + SHOULDER[0] * c - SHOULDER[1] * s, y + SHOULDER[0] * s + SHOULDER[1] * c])
        P = np.array([np.asarray(p, float) for p in problem.goals[k][0]])
        out.append(bool(np.all(np.linalg.norm(P[:, :2] - sh, axis=1) < REACH_XY) and
                        np.all((P[:, 2] > REACH_Z[0]) & (P[:, 2] < REACH_Z[1]))))
    return out


def rank_ik(kin, cands, problem, q0):
    """Per candidate: a kinematic IK solution of its goal's relay pose (None: none), all candidates
    in one batched call -- the poses taken into each candidate's base frame, kin's base at the
    origin and no world (the collision world moves with the base; collisions are the build's)."""
    P, Rs = [], []
    for _, x, y, yaw, k in cands:
        p, R = problem.goals[k][1]
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        Rz = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        P.append(Rz.T @ (np.asarray(p, float) - np.array([x, y, 0.0])))
        Rs.append(Rz.T @ np.asarray(R, float))
    if not P:
        return []
    base, scene = (kin.base_p.copy(), kin.base_R.copy()), kin.scene
    try:
        kin.set_base((0.0, 0.0, 0.0), 0.0)
        kin.scene = None
        return kin.ik_set(list(zip(P, Rs)), np.asarray(q0, float))
    finally:
        kin.base_p, kin.base_R = base
        kin.scene = scene


def score(kin, cands, sols):
    """Ranking score per candidate (lower is better), as planner.rank_parks without the clearance
    (a world query per park): joints near a limit, manipulability below the best, the candidate's
    own cost above the cheapest."""
    lo, hi = np.asarray(kin.lo, float)[2:], np.asarray(kin.hi, float)[2:]
    manip = [manipulability(kin, q) if q is not None else 0.0 for q in sols]
    best = max(max(manip, default=0.0), 1e-9)
    c0 = min((c[0] for c in cands), default=0.0)
    out = []
    for c, q, m in zip(cands, sols, manip):
        margin = float(np.min(np.minimum(np.asarray(q)[2:] - lo, hi - np.asarray(q)[2:])))
        out.append(max(0.0, LIMIT_CLEAR - margin) / LIMIT_CLEAR + (1.0 - m / best) + PARK_DIST_W * (c[0] - c0))
    return out


def find_park(rig, problem, state):
    """The park for ``problem`` (Problem) from ``state`` (motion_state.State, now): Found with the
    plan the skill's builder made there, or None; the counts of every test in ``diag`` either way
    (also logged as park_search)."""
    from .planner import _drivable, _whole_body
    from .skills import base_reachable
    kin, world = rig.kin, rig.world
    t0 = time.time()
    diag = {"candidates": 0, "out_of_reach": 0, "footprint": 0, "travel_pose": 0, "drive": 0, "ik": 0,
            "built": 0, "no_path": 0, "build_failed": {}, "stage_s": {}}
    cands = candidates(problem)
    diag["candidates"] = len(cands)
    here = None if problem.near is None or len(problem.near) != 3 else tuple(map(float, problem.near))
    is_here = lambda c: here is not None and c[1:4] == here

    # cheap, per candidate, cheapest first, up to MAX_PER_GOAL per goal
    pool, per = [], [0] * len(problem.goals)
    for c, ok in zip(cands, reachable(cands, problem)):
        k = c[4]
        if per[k] >= MAX_PER_GOAL and not is_here(c):
            continue
        if not ok:
            diag["out_of_reach"] += 1
            continue
        if not is_here(c) and not world.footprint_clear(c[1], c[2], math.radians(c[3])):
            diag["footprint"] += 1
            continue
        pool.append(c)
        per[k] += 1
        if min(per) >= MAX_PER_GOAL:
            break
    # batched: the whole robot in its travel posture at each park; the base can drive there
    body = _whole_body(kin, problem.travel)
    moving = [c for c in pool if not is_here(c)]
    if body is not None and moving:
        depths, sets, _ = body
        d = depths(np.array([[x, y, math.radians(yaw)] for _, x, y, yaw, _ in moving]), sets)[0]
        blocked = {c[1:4] for c, dc in zip(moving, d) if dc > 1e-4}
        diag["travel_pose"] = len(blocked)
        pool = [c for c in pool if is_here(c) or c[1:4] not in blocked]
        moving = [c for c in pool if not is_here(c)]
    if moving:
        reach = base_reachable(rig, [c[1:4] for c in moving])
        unreachable = {c[1:4] for c, r in zip(moving, reach) if not r}
        diag["drive"] = len(unreachable)
        pool = [c for c in pool if is_here(c) or c[1:4] not in unreachable]
    # ranking: a kinematic IK of each relay pose, then joint margin, manipulability and cost
    sols = rank_ik(kin, pool, problem, problem.travel)
    diag["ik"] = sum(q is None for q in sols)
    ranked = [(c, q) for c, q in zip(pool, sols) if q is not None]
    scores = score(kin, [c for c, _ in ranked], [q for _, q in ranked])
    order = sorted(range(len(ranked)), key=lambda i: (not is_here(ranked[i][0]), scores[i]))
    # the skill's plan, in that order
    found, t_build = None, time.time()
    for i in order:
        if diag["built"] >= BUILD_MAX or time.time() - t_build > BUILD_S:
            break
        (cost, x, y, yaw, k), q_rank = ranked[i]
        diag["built"] += 1
        s = with_arm(at_base(state, (x, y, yaw)), problem.arrive(x, y, yaw), kin.side)
        plan = problem.build(s, k, q_rank)
        for st_, sec in getattr(plan, "info", {}).get("stage_s", {}).items():     # where the building time goes
            diag["stage_s"][st_] = round(diag["stage_s"].get(st_, 0.0) + sec, 2)
        if isinstance(plan, Failure):
            key = f"{plan.segment}: {plan.why.split(' (')[0]}"
            diag["build_failed"][key] = diag["build_failed"].get(key, 0) + 1
            continue
        if not is_here(ranked[i][0]) and body is not None and \
                not _drivable(kin, world, body, tuple(state.base), (x, y, yaw)):
            diag["no_path"] += 1
            continue
        found = Found(x, y, yaw, k, plan, q_rank)
        break
    diag["seconds"] = round(time.time() - t0, 2)
    diag["build_seconds"] = round(time.time() - t_build, 2)
    rig.log("park_search", target=problem.label, found=None if found is None else
            [round(found.x, 3), round(found.y, 3), round(found.yaw, 1), found.k], **diag)
    if found is not None:
        found.diag = diag
    return found, diag
