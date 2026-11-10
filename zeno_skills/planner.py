"""Where to park the base and how to drive there.

find_park   search base poses around a set of TCP targets; a pose is feasible
            when the footprint is clear, the arms in their travel posture (and
            what the hands hold) touch nothing, every target is reachable by a
            collision-free continuous IK path (optionally while the base rides
            along with an articulated part) and the base can drive there
            (base_planner).
"""

from __future__ import annotations

import math

import numpy as np

from .kinematics import manipulability, tips_over


def _ik_sequence(kin, targets, q0=None):
    """targets: list of (p, R). Continuous, collision-free; returns qs or None.
    Forward first; if that breaks (IK continuity near the joint limits, e.g.
    a tilted approach to the floor), solve the last target and chain
    backwards, which keeps every leg on that final configuration's branch."""
    qs = _chain(kin, targets, q0)
    if qs is None and q0 is None and len(targets) > 1:
        rev = _chain(kin, targets[::-1], None)
        if rev is not None:
            qs = rev[::-1]
    return qs


def _chain(kin, targets, q):
    """targets: (p, R) or (p, R, coll_kw): that target (and the line into it) checked with this
    coll_kw instead of kin's (the fingers checked on a free approach, not on the contact after it)."""
    qs = []
    base = kin.coll_kw
    try:
        for t in targets:
            p, R = t[0], t[1]
            kin.coll_kw = t[2] if len(t) > 2 else base
            if q is None:
                q, ok = kin.ik_global(np.asarray(p, float), R)
                if not ok:
                    return None
            else:
                path, ok = kin.cart_path(q, np.asarray(p, float), R, 0.02)
                if not ok:
                    return None
                q = path[-1]
            qs.append(q)
    finally:
        kin.coll_kw = base
    return qs


def _unfolds(kin, travel_q, q, target, carry):
    """joint_reachable from the travel posture to the first target's solution q, checked with that
    target's own coll_kw when it has one (the free approach of a grasp: the fingers too), as the
    motion there will be."""
    base = kin.coll_kw
    kin.coll_kw = target[2] if len(target) > 2 else base
    try:
        return joint_reachable(kin, travel_q, q, carry=carry)
    finally:
        kin.coll_kw = base


def _segment_free(kin, qa, qb):
    return kin.segment_free(np.asarray(qa, float), np.asarray(qb, float))


def _whole_body(kin, travel_q):
    """(depths, sphere sets, travel posture (right, left)) of the whole robot in the travel posture
    -- travel_q for the right arm, the left folded unless it holds something -- for
    Motion.base_depths, or None without cuRobo (or before the first sync)."""
    motion = getattr(kin, "motion", None)
    rig = getattr(motion, "rig", None) if motion is not None else None
    if rig is None:
        return None
    travel_q = np.asarray(travel_q, float)
    left = rig.left_kin.rest[2:] if rig.left_held is None else rig.left_q_cmd.copy()     # as skills.navigate arrives
    sets = motion.body_spheres(rig, [(travel_q, left)])
    return (lambda poses, sph: motion.base_depths(rig, poses, sph)), sets, (travel_q, left)


def _drivable(kin, world, body, origin, goal):
    """The base can drive from ``origin`` to ``goal``: a whole-body base plan in the postures it
    drives in (skills.navigate: the travel posture, hanging where it does not fit).  Without a
    whole-body model -- no cuRobo, or a caller that names no travel posture -- there is nothing to
    check the drive against and the drive itself decides (11-10: the 5 cm grid over a 0.28 m
    cylinder that used to answer here was the base as it was modelled before the two layers)."""
    if body is None:
        return True
    from . import base_planner
    from .motion_state import Hand, Held, State
    from .skill_plans import travel_chain
    from .skills import posture_sets, scene_area
    depths, _, travel = body
    rig = kin.motion.rig
    hand = lambda h: Hand(0.0, None if h is None else Held(h["name"], np.eye(4)))
    st = State(base=tuple(origin), q_right=np.asarray(travel[0], float), q_left=np.asarray(travel[1], float),
               hands={"right": hand(rig.held), "left": hand(rig.left_held)})
    chain = [p for _, p in travel_chain(rig.kin, rig.left_kin, st)]
    if any(np.max(np.abs(p[0] - chain[0][0])) >= 0.02 for p in chain):
        sets, switches, dense = posture_sets(rig, chain)
    else:
        sets, switches, dense = posture_sets(rig, chain[:1])
    area = scene_area(world)
    with kin.motion.base_world(area[:2], area[2:]):
        return base_planner.plan(depths, origin, goal, sets, switches, area=area, footprint=world.footprints_clear,
                                 passable=world.circles_clear, dense_switches=dense)[0] is not None


def joint_reachable(kin, qa, qb, carry=False):
    """A collision-free joint-space move qa -> qb exists: straight, or a cuRobo
    trajectory (the options Rig.joint_path executes).  ``carry`` (an object in
    the hand) asks for the same tilt-held trajectory the execution will use:
    without it a park passes the search on a free plan and then fails the
    constrained one it actually has to run."""
    qa, qb = np.asarray(qa, float), np.asarray(qb, float)
    if _segment_free(kin, qa, qb) and not (carry and tips_over(kin, qa, qb)):
        return True
    return kin.plan(qa, qb, carry=carry)[0] is not None


def torque_ratio(kin, q, force):
    """max_i |(J^T F)_i| / effort_limit_i for a TCP force F (world, N)."""
    from .kinematics import effort_limits
    J, _, _ = kin.jac(np.asarray(q, float))
    tau = J[:3].T @ np.asarray(force, float)
    return float(np.max(np.abs(tau) / effort_limits(kin.names)))


LAST_PARK_DIAG: dict = {}      # rejection counts of the last find_park call (for failure messages)


PARK_CANDIDATES = 4        # feasible parks compared by park_quality before one is taken
LIMIT_CLEAR = 0.15         # rad: arm joints closer than this to a limit cost (same as motion.LIMIT_CLEAR)
PARK_DIST_W = 0.5          # weight of the candidate's own cost (distance, yaw) in the ranking


def park_quality(kin, qs, targets):
    """Worst over a park's joint solutions of: arm joint-limit margin (rad), manipulability,
    clearance to the world (m, capped; fingers and the targeted objects left out)."""
    Q = np.array([np.asarray(q, float) for q in qs])
    margin = float(np.min(np.minimum(Q - kin.lo, kin.hi - Q)[:, 2:]))
    manip = min(manipulability(kin, q) for q in Q)
    clear = float(np.min(kin.clearance(Q, [t[0] for t in targets])))
    return {"margin": margin, "manip": manip, "clear": clear}


def rank_parks(found):
    """found: [(cost, quality, park)].  Each term in [0, 1], lower is better: joints near a limit,
    manipulability below the best candidate's, clearance below the cap, and (PARK_DIST_W) the
    candidate's distance/yaw cost above the cheapest one's.  Returns the list sorted."""
    best_m = max(max(f[1]["manip"] for f in found), 1e-9)
    c0 = min(f[0] for f in found)
    cap = max(max(f[1]["clear"] for f in found), 1e-9)

    def total(f):
        cost, q, _ = f
        return (max(0.0, LIMIT_CLEAR - q["margin"]) / LIMIT_CLEAR + (1.0 - q["manip"] / best_m)
                + (1.0 - min(q["clear"], cap) / cap) + PARK_DIST_W * (cost - c0))
    return sorted(found, key=total), total


def find_park(kin, world, targets, **kw):
    """Return (x, y, yaw_deg, qs) or None: _find_park for one target sequence."""
    found = _find_park(kin, world, [targets], [0.0], **kw)
    return None if found is None else found[0]


def find_park_set(kin, world, target_sets, set_cost, **kw):
    """A park for any one of the target sequences ``target_sets`` (a goal set: spots, wrist turns):
    (park, index of the sequence) or None.  Every (park candidate, sequence) pair is one candidate
    of the same search, its cost raised by ``set_cost[k]`` (m, like a candidate's distance), so
    the sequences are weighed together rather than tried one after another."""
    return _find_park(kin, world, target_sets, set_cost, **kw)


def _find_park(kin, world, target_sets, set_cost, near=None, radii=np.arange(0.45, 1.0, 0.05),
               yaw_offsets=(-60, -45, -30, -15, 0, 15, 30, -75, -90, 45, 60, 75, 90), ride=None, max_tries=400,
               score=None, n_best=None, q_start=None, travel_q=None, shoulder=(0.09, -0.18), path_from=None,
               check=None, carry=False, ride_set=None, unfold=True):
    """Return ((x, y, yaw_deg, qs), k) or None, k the target sequence of target_sets it serves.
    ``ride_set``: as ``ride``, for the sequence k: callable(k, x, y, yaw_deg, q_last) -> bool.

    Without ``score`` the first PARK_CANDIDATES feasible parks are ranked by park_quality
    (rank_parks) and the best is taken; with ``score`` (a skill's own criterion, lowest wins)
    the first ``n_best`` (default 1).  ``near`` with a yaw is the current base pose: when it
    works it competes with those parks (it costs no drive, so a park must be clearly better
    to move there); with ``max_tries=1`` it is the only pose tried (a probe of that pose).

    travel_q: arm posture while the base drives there (tucked, or the carry
              pose); a park where it would already hit the furniture is
              rejected (the footprint check covers the base column only).
    carry:    an object is in the hand: the unfold from travel_q is checked with
              the tilt held, as Rig.joint_path will plan it.

    targets: list of (p, R) TCP poses executed in order from this park.
    ride:    optional callable(x, y, yaw_deg, q_last) -> bool that validates a
             base ride (e.g. following an opening door).
    check:   optional callable(x, y, yaw_deg, qs) -> bool, a further test of the
             joint solutions at this park (the base is set to it).
    unfold:  False when ``check`` tests the unfold itself (to a pose the targets do not list:
             a set-down's straight starts where the collision model says, place._park_check).
    """
    cands = []
    for k, targets in enumerate(target_sets):
        c = np.mean([np.asarray(t[0], float)[:2] for t in targets], axis=0)
        for r in radii:
            for ang in np.radians(np.arange(0, 360, 15)):
                x, y = c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)
                face = math.degrees(math.atan2(c[1] - y, c[0] - x))
                for off in yaw_offsets:
                    # the right arm sits on the robot's -y side: face slightly left
                    cost = r + 0.002 * abs(off + 30) + float(set_cost[k])
                    if near is not None:
                        cost += 0.15 * math.hypot(x - near[0], y - near[1])
                    cands.append((cost, x, y, face + off, k))
    cands.sort(key=lambda t: t[0])
    if near is not None and len(near) == 3:
        # the current base pose first: no need to move if it already works
        cands[:0] = sorted(((-1.0 + float(set_cost[k]) * 1e-3, float(near[0]), float(near[1]), float(near[2]), k)
                            for k in range(len(target_sets))), key=lambda t: t[0])
    Ps = [np.array([np.asarray(t[0], float) for t in targets]) for targets in target_sets]

    def reachable(x, y, yaw, P):
        """Cheap prefilter: right shoulder (base + R(0.09, -0.18)) within arm
        reach of every target, heights within the torso-lift range (down to
        the floor: torso fully lowered + waist pitched)."""
        c_, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        sh = np.array([x + shoulder[0] * c_ - shoulder[1] * s_, y + shoulder[0] * s_ + shoulder[1] * c_])
        d = np.linalg.norm(P[:, :2] - sh, axis=1)
        return bool(np.all(d < 0.78) and np.all((P[:, 2] > 0.0) & (P[:, 2] < 1.5)))
    if n_best is None:
        n_best = PARK_CANDIDATES if score is None else 1
    found = []
    stay = False
    diag = {"candidates": len(cands), "out_of_reach": 0, "footprint": 0, "travel_pose": 0, "ik": 0,
            "unfold": 0, "ride": 0}
    LAST_PARK_DIAG.clear()
    LAST_PARK_DIAG.update(diag)
    pool = []
    per_set = [0] * len(target_sets)       # max_tries is each sequence's own budget (cheapest first overall)
    for cost, x, y, yaw, k in cands:
        if per_set[k] >= max_tries:
            continue
        if not reachable(x, y, yaw, Ps[k]):
            LAST_PARK_DIAG["out_of_reach"] += 1
            continue
        if not world.footprint_clear(x, y, math.radians(yaw)):
            LAST_PARK_DIAG["footprint"] += 1
            continue
        pool.append((cost, x, y, yaw, k))
        per_set[k] += 1
        if min(per_set) >= max_tries:
            break
    body = _whole_body(kin, travel_q) if travel_q is not None else None
    if body is not None:
        # strict: parked there in its travel posture both arms and what the hands hold touch nothing
        # (the footprint was checked above); one batched check for every candidate
        depths, sets, _ = body
        moving = [c for c in pool if c[0] >= 0]
        d = depths(np.array([[x, y, math.radians(yaw)] for _, x, y, yaw, _ in moving]), sets)[0] if moving else []
        blocked = {c[1:4] for c, dc in zip(moving, d) if dc > 1e-4}
        LAST_PARK_DIAG["travel_pose"] += len(blocked)
        pool = [c for c in pool if c[0] < 0 or c[1:4] not in blocked]
    for cost, x, y, yaw, k in pool:
        targets = target_sets[k]
        kin.set_base((x, y, 0.0), math.radians(yaw))
        if body is None and travel_q is not None and cost >= 0:
            kw, kin.coll_kw = kin.coll_kw, {"ignore_fingers": kin.coll_kw.get("ignore_fingers", False)}
            clear = kin.free(travel_q)          # strict: the parked arm touches nothing
            kin.coll_kw = kw
            if not clear:
                LAST_PARK_DIAG["travel_pose"] += 1
                continue
        qs = _ik_sequence(kin, targets, q0=q_start if cost < 0 and q_start is not None else None)
        if qs is None:
            LAST_PARK_DIAG["ik"] += 1
            continue
        if check is not None and not check(x, y, yaw, qs):
            LAST_PARK_DIAG["check"] = LAST_PARK_DIAG.get("check", 0) + 1
            continue
        if unfold and travel_q is not None and cost >= 0 and not _unfolds(kin, travel_q, qs[0], targets[0], carry):
            LAST_PARK_DIAG["unfold"] += 1
            continue                    # the arm cannot unfold to the first target here
        if (ride is not None and not ride(x, y, yaw, qs[-1])) or \
                (ride_set is not None and not ride_set(k, x, y, yaw, qs[-1])):
            LAST_PARK_DIAG["ride"] += 1
            continue
        origin = path_from if path_from is not None else (near if near is not None and len(near) == 3 else None)
        if origin is not None and cost >= 0 and \
                math.hypot(x - origin[0], y - origin[1]) > 0.05 and not _drivable(kin, world, body, origin, (x, y, yaw)):
            # footprint-clear but enclosed (e.g. behind a counter): not drivable from here
            LAST_PARK_DIAG["no_path"] = LAST_PARK_DIAG.get("no_path", 0) + 1
            continue
        if cost < 0:
            if max_tries <= 1:
                return (x, y, yaw, qs), k
            if stay:
                continue                # the current pose already serves a cheaper sequence
            stay = True                 # the current pose works: rank it against n_best others
            cost = float(set_cost[k])
        if score is None:
            found.append((cost, park_quality(kin, qs, targets), ((x, y, yaw, qs), k)))
        else:
            found.append((score(x, y, yaw, qs), ((x, y, yaw, qs), k)))
        if len(found) >= n_best + stay:
            break
    if found and score is None:
        ranked, total = rank_parks(found)
        LAST_PARK_DIAG["ranked"] = [{"park": [round(v, 3) for v in f[2][0][:3]], "set": f[2][1],
                                     "score": round(total(f), 3), **{n: round(v, 4) for n, v in f[1].items()}}
                                    for f in ranked]
        print("find_park: ranked", LAST_PARK_DIAG["ranked"], flush=True)
        x, y, yaw, qs = ranked[0][2][0]
        kin.set_base((x, y, 0.0), math.radians(yaw))
        return ranked[0][2]
    if found:
        found.sort(key=lambda t: t[0])          # stable: on a tie the current pose (first found) stays
        x, y, yaw, qs = found[0][1][0]
        kin.set_base((x, y, 0.0), math.radians(yaw))
        return found[0][1]
    print("find_park: no park", {k: v for k, v in LAST_PARK_DIAG.items() if v}, flush=True)
    return None
