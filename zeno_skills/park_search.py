"""Where to park the base for a skill (docs/MOTION_ARCHITECTURE.md section 7): candidates around
the skill's goals, the cheap tests on all of them at once, a ranking, then the skill's own plan
builder in that order -- the first park whose whole plan can be made wins, with that plan.

find_park knows nothing of arms beyond a kinematic IK for the ranking: whether the skill can be
done from a park is the skill's builder's answer (skill_plans), the one the execution builds again
with.  The old planner.find_park stays for the skills not moved yet."""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .kinematics import kept_joints, manipulability
from .motion_state import N_BODY, Failure, Spec, at_base, body_locked, locked_body, with_posture
from .tolerances import DEPTH_TOL

RADII = np.arange(0.45, 1.0, 0.05)    # m: rings of base positions around a goal's centre (as planner.find_park)
ANGLE_STEP = 15                        # deg between positions on a ring
YAW_OFFSETS = (-60, -45, -30, -15, 0, 15, 30, -75, -90, 45, 60, 75, 90)   # deg off facing the centre
SHOULDER = (0.09, -0.18)               # m: right shoulder in the base frame (the left's: y mirrored, shoulder)
REACH_XY = 0.78                        # m: the arm's horizontal reach from the shoulder (prefilter)
REACH_Z = (0.0, 1.5)                   # m: TCP heights the torso lift reaches (down to the floor)
FACE_LEFT = 30                         # deg: the right arm on the -y side, facing slightly left of the goal is
                                       # (the left arm: mirrored, face_off)
                                       # cheaper -- the goal FACE_LEFT to the right (yaw = face + FACE_LEFT)...
FACE_COST = 0.002                      # m of cost per deg off that.  (Before 11-09 the term was |off + FACE_LEFT|,
                                       # the goal 30 deg to the LEFT, against its own comment; the 11-08 parks
                                       # had 89% of the grasps on the right, median -15 deg: the ranking IK
                                       # overrode it.  Changes the candidates' order: a full run to confirm.)
NEAR_COST = 0.15                       # m of cost per m away from ``near``
VARIANT_COST = 0.05                    # m of goal cost per rank among the ways of one target (a door's
                                       # grasps, a push's closed-finger turns): a weak preference, the
                                       # score's manipulability outweighs it (PARK_DIST_W; tiers: a strict one)
MAX_PER_GOAL = 120                     # cheapest candidates per goal past the reach and footprint tests
LIMIT_CLEAR = 0.15                     # rad: arm joints closer than this to a limit cost (planner.LIMIT_CLEAR)
PARK_DIST_W = 0.5                      # weight of the candidate's own cost in the ranking (planner.PARK_DIST_W)
BUILD_S = 20.0                         # s: plans are built in rank order for at most this long (0.45 s each
                                       # in T20 s10 11-08, where 8 were too few: the reach-in straight
                                       # into the cabinet failed on 5 of the first 8)
BUILD_MAX = 60                         # ...and at most this many
FREE_CHECKS = 600                      # Problem.relay_free: at most this many ranking solutions checked free


def shoulder(side):
    """(x, y) m of ``side``'s shoulder in the base frame: the arms are mirror images in y."""
    return (SHOULDER[0], SHOULDER[1] if side == "right" else -SHOULDER[1])


def face_off(side):
    """deg the base preferably turns off facing a goal of ``side``'s arm (FACE_LEFT, mirrored)."""
    return FACE_LEFT if side == "right" else -FACE_LEFT


@dataclass(frozen=True)
class Problem:
    """What a skill asks of a park search.
    goals:  per goal of the goal set, (TCP points the arm must reach (prefilter), the relay pose
            (p, R) the ranking IK solves, cost in m[, the hand: "right" / "left", default ``hand``]).
    build:  build(state_at_park, k, prior) -> Plan | Failure, the skill's plan builder; prior
            {relay: the ranking's kinematic solution of goal k's relay pose} here (decide_ik's
            prior: kept where it is free, else a seed -- never a check), a Plan where run_skill
            builds again at the base as it stands (park_here): a builder reads it through
            motion_state.decisions_of.
    relay:  the name the ranking's solution reaches the builder by -- required: the ranking always
            solves a relay pose.  Mostly the decision that pose stands for (skill_plans.PICK_RELAY,
            PLACE_RELAY, DOOR_RELAY: the builder's prior for it); else a seed of one, the pose the
            ranking had better judge by (SLIDE_RELAY: the push's end seeds slide_reach's IK).
    arrive: arrive(x, y, yaw) -> the posture at that park (what the drive arrives in, or the
            posture now where the base will not move): a motion_state.Posture -- the arms it names, its
            body unless another hand holds something (with_posture) -- or a planning chain of the goal's hand.
    near:   (x, y) or (x, y, yaw): parks cost NEAR_COST per m away from it; with a yaw it is the
            current pose, a candidate of its own, tried first.
    prefer: base poses tried before the rings (in front of a door's free edge: skill_jobs.pick).
    travel: the posture the base drives in (the whole-body test at the parks, once for every goal):
            a Posture, or a planning chain of ``hand``.
    hand:   the hand of a goal that names none.
    tiers:  per goal, its tier (Problem.tier): lower tiers are built first, whatever the score.
    relay_from: per goal, None or the TCP point its relay pose is reached from along a straight (the
            relay's R held): a goal that may be done in part -- a push as far as the arm gets.  Where no
            candidate reaches any goal's relay, the ranking measures how far along that straight each one's
            arm gets (reach_ik, to ``reach_step`` m) and ranks by what it leaves undone (Problem.start_of).
    reach_step: m, the resolution of that measure (a push: the plan's own sample step).
    relay_free: a Spec, or None: the parks whose ranking solution is free by it (in the State at the
            park) built first -- the relay's decide_ik takes such a solution as it is -- the others after
            them (at most FREE_CHECKS checked, in rank order; a check costs no build).  For a goal behind
            a door: the ranking checks no collisions, and an open door's leaf is where a forearm went
            (11-13: the fridge, 60 builds through it).
    body_free: the body joints a goal's build may still move while the other hand holds something (the
            rule keeps the body, motion_state.body_locked; a push lifts the torso on a leg of its own:
            skill_plans.plan_push) -- the ranking IK keeps the others where the state has them, as the
            build will (a ranking that bows the waist ranks parks no build can use).
    arrive / travel come from the skill's catalog entry (motion_skills.run_skill sets them)."""
    goals: tuple
    build: Callable
    relay: str
    arrive: Callable | None = None
    travel: np.ndarray | None = None
    near: tuple | None = None
    prefer: tuple = ()
    label: str = "park"
    hand: str = "right"
    body_free: tuple = ()
    relay_free: Spec | None = None
    tiers: tuple = ()
    relay_from: tuple = ()
    reach_step: float = 0.0

    def tier(self, k):
        """Goal k's tier: every candidate of a lower tier is built before any of a higher one, whatever their
        score (``tiers`` per goal; none: all 0).  A strict preference among the ways of a goal set, where a
        cost per rank is only a weak one (the score's manipulability outweighs it): a push before a drag
        (skill_jobs.slide)."""
        return self.tiers[k] if 0 <= k < len(self.tiers) else 0

    def start_of(self, k):
        """Where goal k's relay straight starts (relay_from), or None: its relay or nothing."""
        return self.relay_from[k] if 0 <= k < len(self.relay_from) else None

    def side(self, k):
        """The hand of goal k."""
        g = self.goals[k] if 0 <= k < len(self.goals) else ()
        return g[3] if len(g) > 3 else self.hand


@dataclass
class Found:
    """The park, the goal k, the plan made there (its decisions: the build's prior from then on)."""
    x: float
    y: float
    yaw: float
    k: int
    plan: object
    diag: dict = field(default_factory=dict)

    @property
    def pose(self):
        return (self.x, self.y, self.yaw)


def candidates(problem):
    """[(cost, x, y, yaw, k)] cheapest first: the current pose and the preferred ones, then the rings."""
    out = []
    for k, (points, _, gcost, *_) in enumerate(problem.goals):
        pref = face_off(problem.side(k))
        c = np.mean([np.asarray(p, float)[:2] for p in points], axis=0)
        for r in RADII:
            for ang in np.radians(np.arange(0, 360, ANGLE_STEP)):
                x, y = c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)
                face = math.degrees(math.atan2(c[1] - y, c[0] - x))
                for off in YAW_OFFSETS:
                    cost = r + FACE_COST * abs(off - pref) + float(gcost)
                    if problem.near is not None:
                        cost += NEAR_COST * math.hypot(x - problem.near[0], y - problem.near[1])
                    out.append((cost, x, y, face + off, k))
    out.sort(key=lambda t: t[0])
    first = []
    for k, (_, _, gcost, *_) in enumerate(problem.goals):
        if problem.near is not None and len(problem.near) == 3:
            first.append((-1.0 + float(gcost) * 1e-3, *map(float, problem.near), k))
        first += [(-0.5 + float(gcost) * 1e-3, *map(float, p), k) for p in problem.prefer]
    return sorted(first, key=lambda t: t[0]) + out


def reachable(cands, problem):
    """Per candidate: every TCP point within REACH_XY of its goal's hand's shoulder, heights in REACH_Z."""
    out = []
    for _, x, y, yaw, k in cands:
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        sx, sy = shoulder(problem.side(k))
        sh = np.array([x + sx * c - sy * s, y + sx * s + sy * c])
        P = np.array([np.asarray(p, float) for p in problem.goals[k][0]])
        out.append(bool(np.all(np.linalg.norm(P[:, :2] - sh, axis=1) < REACH_XY) and
                        np.all((P[:, 2] > REACH_Z[0]) & (P[:, 2] < REACH_Z[1]))))
    return out


def _free_first(kins, problem, state, ranked, order, diag, dbg=None):
    """``order`` with the candidates whose ranking solution is free by problem.relay_free (in the State
    at the park, as the build will have it) first, the rest after them in their order; the first
    FREE_CHECKS checked, the rest after those.  diag["relay_free"]: (checked, free)."""
    from .primitives import query
    free, other = [], []
    for n, i in enumerate(order):
        if n >= FREE_CHECKS:
            break
        (cost, x, y, yaw, k), q, _ = ranked[i]
        side = problem.side(k)
        kin = kins[side]
        s = with_posture(at_base(state, (x, y, yaw)), problem.arrive(x, y, yaw), side)
        with query(kin, s, problem.relay_free):
            ok = kin.free(np.asarray(q, float))
            (free if ok else other).append(i)
            if dbg is not None:
                dbg.setdefault("free_checked", []).append([x, y, yaw, k, bool(ok)])
    diag["relay_free"] = [len(free) + len(other), len(free)]
    return free + other + list(order[FREE_CHECKS:])


def rank_ik(kin, cands, problem, q0, poses=None):
    """Per candidate: a kinematic IK solution of its goal's relay pose (``poses``: of that pose of its
    own instead; None: none), all candidates in one batched call -- the poses taken into each
    candidate's base frame, kin's base at the origin and no world (the collision world moves with the
    base; collisions are the build's)."""
    P, Rs = [], []
    for i, (_, x, y, yaw, k) in enumerate(cands):
        p, R = problem.goals[k][1] if poses is None else poses[i]
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


def reach_ik(kin, cands, problem, q0):
    """Per candidate of a goal whose relay may be done in part (Problem.relay_from): (a kinematic IK
    solution of the farthest point along its relay's straight the arm gets to, the m of the straight
    it leaves undone) -- (None, length) where it does not get to the start.  Bisected to
    problem.reach_step (the arm taken to get as far as its farthest solved point), one batched rank_ik
    per round."""
    if problem.reach_step <= 0:
        raise ValueError(f"{problem.label}: relay_from needs a reach_step")
    lines = []
    for c in cands:
        p1, R = problem.goals[c[4]][1]
        lines.append((np.asarray(problem.start_of(c[4]), float), np.asarray(p1, float), np.asarray(R, float)))
    length = [float(np.linalg.norm(b - a)) for a, b, _ in lines]

    def at(i, f):
        a, b, R = lines[i]
        return a + f * (b - a), R
    out = [(q, length[i]) for i, q in enumerate(rank_ik(kin, cands, problem, q0, [at(i, 0.0) for i in range(len(cands))]))]
    lo, hi = [0.0] * len(cands), [1.0] * len(cands)
    live = [i for i, (q, _) in enumerate(out) if q is not None]
    while True:
        live = [i for i in live if (hi[i] - lo[i]) * length[i] > problem.reach_step]
        if not live:
            break
        mid = {i: 0.5 * (lo[i] + hi[i]) for i in live}
        for i, q in zip(live, rank_ik(kin, [cands[i] for i in live], problem, q0, [at(i, mid[i]) for i in live])):
            if q is None:
                hi[i] = mid[i]
            else:
                lo[i] = mid[i]
                out[i] = (q, (1.0 - mid[i]) * length[i])
    return out


def score(kin, cands, sols):
    """Ranking score per candidate (lower is better), as planner.rank_parks without the clearance
    (a world query per park): joints near a limit, manipulability below the best, the candidate's
    own cost above the cheapest.  ``kin``: the arm's kinematics, or one per candidate (its hand's)."""
    ks = list(kin) if isinstance(kin, (list, tuple)) else [kin] * len(cands)
    manip = [manipulability(k, q) if q is not None else 0.0 for k, q in zip(ks, sols)]
    best = max(max(manip, default=0.0), 1e-9)
    c0 = min((c[0] for c in cands), default=0.0)
    out = []
    for c, q, m, k in zip(cands, sols, manip, ks):
        lo, hi = np.asarray(k.lo, float)[2:], np.asarray(k.hi, float)[2:]
        margin = float(np.min(np.minimum(np.asarray(q)[2:] - lo, hi - np.asarray(q)[2:])))
        out.append(max(0.0, LIMIT_CLEAR - margin) / LIMIT_CLEAR + (1.0 - m / best) + PARK_DIST_W * (c[0] - c0))
    return out


def _dumping(problem):
    """The search's debug record (env ZB_PARK_DUMP: a directory; ZB_PARK_DUMP_MATCH: a substring of the
    problem's label, default every search) -- {} to fill, or None: not recorded.  Changes nothing found."""
    out = os.environ.get("ZB_PARK_DUMP")
    if not out or os.environ.get("ZB_PARK_DUMP_MATCH", "") not in problem.label:
        return None
    return {"label": problem.label, "dir": out, "near": problem.near, "prefer": list(problem.prefer),
            "goals": [[float(v) for v in np.asarray(g[1][0], float)] for g in problem.goals],
            "goal_cost": [float(g[2]) for g in problem.goals],
            "tiers": [problem.tier(k) for k in range(len(problem.goals))]}


def _dump_arm(dbg, kin, s, problem, k, q_rank, plan):
    """The debug record of one build: the relay pose (the EEP), the arm's collision spheres at the
    ranking solution and at the relay solution the build decided (a Failure's info["q_relay"]; a
    plan's decisions), in the State at the park."""
    from .primitives import robot_spheres
    spec = problem.relay_free or Spec()
    p, R = problem.goals[k][1]
    rec = {"eep": [[float(v) for v in np.asarray(p, float)], np.asarray(R, float).tolist()],
           "base": list(s.base), "rank": robot_spheres(kin, s, spec, q_rank)}
    q_rel = (plan.info or {}).get("q_relay") if isinstance(plan, Failure) else \
        (getattr(plan, "decisions", None) or {}).get(problem.relay)
    if q_rel is not None:
        rec["relay"] = robot_spheres(kin, s, spec, q_rel)
    dbg.setdefault("arms", []).append(rec)


def _dump_write(dbg, found):
    """Write the debug record next to the others (one JSON per search)."""
    os.makedirs(dbg["dir"], exist_ok=True)
    dbg["found"] = None if found is None else [found.x, found.y, found.yaw, found.k]
    name = "".join(ch if ch.isalnum() else "_" for ch in dbg["label"]) + f"_{int(time.time() * 1000)}.json"
    with open(os.path.join(dbg.pop("dir"), name), "w") as f:
        json.dump(dbg, f, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


def find_park(kin, world, problem, state, log, base=None):
    """The park for ``problem`` (Problem) from ``state`` (motion_state.State, now): Found with the
    plan the skill's builder made there, or None; the counts of every test in ``diag`` either way
    (also logged as park_search through ``log``).  ``kin`` the arms' kinematics, {side: ArmKin} (one
    ArmKin: that arm's only) -- each goal's ranking IK in its hand's (docs 7, which hand); ``world`` the
    WorldModel (footprints), ``base`` the motion_state.BaseModel (the whole robot in its travel
    posture at a park, the base reaching it; None: neither is tested).  No rig: docs 2.5."""
    kins = dict(kin) if isinstance(kin, Mapping) else {kin.side: kin}
    t0 = time.time()
    diag = {"candidates": 0, "out_of_reach": 0, "footprint": 0, "travel_pose": 0, "drive": 0, "ik": 0,
            "built": 0, "no_path": 0, "build_failed": {}, "stage_s": {}, "filter_s": {}}
    lap = [time.time()]

    def timed(key):                     # where the time before the building goes (filter_s)
        now = time.time()
        diag["filter_s"][key] = round(now - lap[0], 2)
        lap[0] = now

    cands = candidates(problem)
    diag["candidates"] = len(cands)
    dbg = _dumping(problem)
    if dbg is not None:
        dbg["base_now"], dbg["rejected"] = list(state.base), {"out_of_reach": [], "footprint": []}
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
            if dbg is not None:
                dbg["rejected"]["out_of_reach"].append(c[1:5])
            continue
        if not is_here(c) and not world.footprint_clear(c[1], c[2], math.radians(c[3])):
            diag["footprint"] += 1
            if dbg is not None:
                dbg["rejected"]["footprint"].append(c[1:5])
            continue
        pool.append(c)
        per[k] += 1
        if min(per) >= MAX_PER_GOAL:
            break
    timed("candidates_reach_footprint")
    # batched: the whole robot in its travel posture at each park; the base can drive there
    travel = with_posture(state, problem.travel, problem.hand)
    moving = [c for c in pool if not is_here(c)]
    if base is not None and moving:
        d = base.depths(travel, [c[1:4] for c in moving])
        blocked = {c[1:4] for c, dc in zip(moving, d) if dc > DEPTH_TOL}
        diag["travel_pose"] = len(blocked)
        if dbg is not None:
            dbg["rejected"]["travel_pose"] = sorted(blocked)
        pool = [c for c in pool if is_here(c) or c[1:4] not in blocked]
        moving = [c for c in pool if not is_here(c)]
    timed("travel_pose")
    if base is not None and moving:
        reach = base.reachable(state, [c[1:4] for c in moving])
        unreachable = {c[1:4] for c, r in zip(moving, reach) if not r}
        diag["drive"] = len(unreachable)
        if dbg is not None:
            dbg["rejected"]["drive"] = sorted(unreachable)
        pool = [c for c in pool if is_here(c) or c[1:4] not in unreachable]
    timed("drive")
    # ranking: a kinematic IK of each relay pose, then joint margin, manipulability and cost
    sols, left = [None] * len(pool), [0.0] * len(pool)

    def by_hand(solve, keep_goal=lambda k: True):
        """solve(kin, candidates, seed) per hand, one batched call each, under the build's body rule."""
        for side in sorted({problem.side(c[4]) for c in pool}):
            if side not in kins:
                raise ValueError(f"{problem.label}: a goal of the {side} hand, no {side} kinematics")
            idx = [i for i, c in enumerate(pool) if problem.side(c[4]) == side and keep_goal(c[4])]
            k = kins[side]
            # the body joints the build keeps, kept here too (the rule, but for problem.body_free)
            keep = locked_body(state, Spec(joints=problem.body_free) if body_locked(state, Spec(), side) else Spec(), side)
            seed = travel.q(side)
            seed[:N_BODY][keep] = np.asarray(state.body, float)[keep]
            with kept_joints(k, keep, state.body):
                yield idx, solve(k, [pool[i] for i in idx], seed)

    for idx, got in by_hand(lambda k, cs, seed: rank_ik(k, cs, problem, seed)):
        for i, q in zip(idx, got):
            sols[i] = q
    if problem.relay_from and all(q is None for q in sols):
        # no park reaches any relay: how far along its straight each one's arm gets (Problem.relay_from)
        for idx, got in by_hand(lambda k, cs, seed: reach_ik(k, cs, problem, seed),
                                lambda k: problem.start_of(k) is not None):
            for i, (q, undone) in zip(idx, got):
                sols[i], left[i] = q, undone
        reached = [u for q, u in zip(sols, left) if q is not None]
        diag["reach"] = {"measured": len(reached), "least_left": round(min(reached), 3) if reached else None}
    timed("rank_ik")
    diag["ik"] = sum(q is None for q in sols)
    ranked = [(c, q, u) for c, q, u in zip(pool, sols, left) if q is not None]
    scores = score([kins[problem.side(c[4])] for c, _, _ in ranked], [c for c, _, _ in ranked],
                   [q for _, q, _ in ranked])
    # a goal's tier first (Problem.tier: a strict preference -- a push before a drag), then what it leaves
    # undone (a push the arm gets only part of: the farthest first; 0 for every other), then here, then the score
    order = sorted(range(len(ranked)), key=lambda i: (problem.tier(ranked[i][0][4]), ranked[i][2],
                                                      not is_here(ranked[i][0]), scores[i]))
    timed("score")
    diag["pool"] = len(pool)
    # the skill's plan, in that order (Problem.relay_free: the free ranking solutions first)
    if dbg is not None:
        dbg["rejected"]["ik"] = [c[1:5] for c, q in zip(pool, sols) if q is None]
        dbg["ranked"] = [[*ranked[i][0][1:5], problem.tier(ranked[i][0][4]), float(scores[i])] for i in order]
    if problem.relay_free is not None:
        order = _free_first(kins, problem, state, ranked, order, diag, dbg)
    found, t_build = None, time.time()
    for i in order:
        if diag["built"] >= BUILD_MAX or time.time() - t_build > BUILD_S:
            break
        (cost, x, y, yaw, k), q_rank, _ = ranked[i]
        diag["built"] += 1
        s = with_posture(at_base(state, (x, y, yaw)), problem.arrive(x, y, yaw), problem.side(k))
        plan = problem.build(s, k, {problem.relay: q_rank})
        for st_, sec in getattr(plan, "info", {}).get("stage_s", {}).items():     # where the building time goes
            diag["stage_s"][st_] = round(diag["stage_s"].get(st_, 0.0) + sec, 2)
        if dbg is not None:
            dbg.setdefault("built", []).append([x, y, yaw, k, "ok" if not isinstance(plan, Failure)
                                                else f"{plan.segment}: {plan.why[:200]}"])
            _dump_arm(dbg, kins[problem.side(k)], s, problem, k, q_rank, plan)
        if isinstance(plan, Failure):
            key = f"{plan.segment}: {plan.why.split(' (')[0]}"
            diag["build_failed"][key] = diag["build_failed"].get(key, 0) + 1
            if len(diag.setdefault("build_examples", {})) < 8:          # one full why per kind, for the log
                diag["build_examples"].setdefault(key, plan.why[:400])
            continue
        if not is_here(ranked[i][0]) and base is not None and not base.drivable(travel, (x, y, yaw)):
            diag["no_path"] += 1
            continue
        found = Found(x, y, yaw, k, plan)
        break
    diag["seconds"] = round(time.time() - t0, 2)
    diag["build_seconds"] = round(time.time() - t_build, 2)
    log("park_search", target=problem.label, found=None if found is None else
            [round(found.x, 3), round(found.y, 3), round(found.yaw, 1), found.k], **diag)
    if dbg is not None:
        _dump_write(dbg, found)
    if found is not None:
        found.diag = diag
    return found, diag
