"""Where to park the base and how to drive there.

find_park   search base poses around a set of TCP targets; a pose is feasible
            when the footprint is clear and every target is reachable by a
            collision-free continuous IK path (optionally while the base rides
            along with an articulated part).
plan_path   A* on a 5 cm grid over free base positions (circumscribed circle
            of the base column), then shortcut smoothing.
"""

from __future__ import annotations

import heapq
import math

import numpy as np

from .collision import BASE_HALF

# The base drives facing along the path (drive_base yaws to the segment
# direction), so laterally only the half width of the 0.49 m column matters;
# the circumscribed radius (0.37 m) would close every interior doorway.
R_BASE = 0.28


def _ik_sequence(kin, targets, q0=None):
    """targets: list of (p, R). Continuous, collision-free; returns qs or None."""
    q = q0
    qs = []
    for p, R in targets:
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
    return qs


def torque_ratio(kin, q, force):
    """max_i |(J^T F)_i| / effort_limit_i for a TCP force F (world, N)."""
    from .kinematics import effort_limits
    J, _, _ = kin.jac(np.asarray(q, float))
    tau = J[:3].T @ np.asarray(force, float)
    return float(np.max(np.abs(tau) / effort_limits(kin.names)))


def find_park(kin, world, targets, near=None, radii=np.arange(0.45, 1.0, 0.05),
              yaw_offsets=(-60, -45, -30, -15, 0, 15, 30, -75, -90), ride=None, max_tries=400,
              score=None, n_best=1, q_start=None):
    """Return (x, y, yaw_deg, qs) or None.

    targets: list of (p, R) TCP poses executed in order from this park.
    ride:    optional callable(x, y, yaw_deg, q_last) -> bool that validates a
             base ride (e.g. following an opening door).
    """
    c = np.mean([np.asarray(p, float)[:2] for p, _ in targets], axis=0)
    cands = []
    for r in radii:
        for ang in np.radians(np.arange(0, 360, 15)):
            x, y = c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)
            face = math.degrees(math.atan2(c[1] - y, c[0] - x))
            for off in yaw_offsets:
                # the right arm sits on the robot's -y side: face slightly left
                cost = r + 0.002 * abs(off + 30)
                if near is not None:
                    cost += 0.15 * math.hypot(x - near[0], y - near[1])
                cands.append((cost, x, y, face + off))
    cands.sort()
    if near is not None and len(near) == 3:
        # the current base pose first: no need to move if it already works
        cands.insert(0, (-1.0, float(near[0]), float(near[1]), float(near[2])))
    P = np.array([np.asarray(p, float) for p, _ in targets])

    def reachable(x, y, yaw):
        """Cheap prefilter: right shoulder (base + R(0.09, -0.18)) within arm
        reach of every target, heights within the torso-lift range."""
        c_, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        sh = np.array([x + 0.09 * c_ + 0.18 * s_, y + 0.09 * s_ - 0.18 * c_])
        d = np.linalg.norm(P[:, :2] - sh, axis=1)
        return bool(np.all(d < 0.78) and np.all((P[:, 2] > 0.15) & (P[:, 2] < 1.5)))
    tried = 0
    found = []
    for cost, x, y, yaw in cands:
        if not reachable(x, y, yaw) or not world.footprint_clear(x, y, math.radians(yaw)):
            continue
        tried += 1
        if tried > max_tries:
            break
        kin.set_base((x, y, 0.0), math.radians(yaw))
        qs = _ik_sequence(kin, targets, q0=q_start if cost < 0 else None)
        if qs is None:
            continue
        if ride is not None and not ride(x, y, yaw, qs[-1]):
            continue
        if score is None or cost < 0:
            return x, y, yaw, qs
        found.append((score(x, y, yaw, qs), (x, y, yaw, qs)))
        if len(found) >= n_best:
            break
    if found:
        found.sort(key=lambda t: t[0])
        return found[0][1]
    return None


class Grid:
    def __init__(self, world, res=0.05, margin=0.02):
        self.world, self.res, self.margin = world, res, margin
        boxes = np.array(world.boxes[:-1])
        tall = boxes[:, 2] < 1.0                     # anything the column (0..1.05 m) can hit
        self.boxes = boxes[tall]
        lo = self.boxes[:, :2].min(0) - 1.0
        hi = self.boxes[:, 3:5].max(0) + 1.0
        self.lo = lo
        self.shape = np.ceil((hi - lo) / res).astype(int)
        self.cache = {}

    def free(self, ij):
        if ij in self.cache:
            return self.cache[ij]
        x, y = self.lo + (np.asarray(ij) + 0.5) * self.res
        b = self.boxes
        dx = np.maximum(np.maximum(b[:, 0] - x, x - b[:, 3]), 0)
        dy = np.maximum(np.maximum(b[:, 1] - y, y - b[:, 4]), 0)
        ok = bool(np.all(np.hypot(dx, dy) > R_BASE + self.margin))
        if ok:
            ok = bool(np.all(self.world.moving_part_dist(np.array([[x, y, 0.4]])) > R_BASE + self.margin))
        self.cache[ij] = ok
        return ok

    def ij(self, xy):
        return tuple(((np.asarray(xy) - self.lo) / self.res).astype(int))

    def xy(self, ij):
        return self.lo + (np.asarray(ij) + 0.5) * self.res


def plan_path(world, start, goal, res=0.05):
    """start/goal: (x, y, yaw_deg).  Returns waypoints [(x, y, yaw_deg), ...].
    Start/goal cells may be tight (parked next to furniture); the search lets
    the first/last 0.4 m ignore the clearance check."""
    g = Grid(world, res)
    s, t = g.ij(start[:2]), g.ij(goal[:2])
    relax = int(0.4 / res)

    def ok(ij):
        near_end = max(abs(ij[0] - s[0]), abs(ij[1] - s[1])) <= relax or \
            max(abs(ij[0] - t[0]), abs(ij[1] - t[1])) <= relax
        return near_end or g.free(ij)

    openq = [(0.0, s)]
    came, cost = {s: None}, {s: 0.0}
    nbrs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    while openq:
        _, cur = heapq.heappop(openq)
        if cur == t:
            break
        for dx, dy in nbrs:
            n = (cur[0] + dx, cur[1] + dy)
            if not ok(n):
                continue
            c = cost[cur] + math.hypot(dx, dy)
            if c < cost.get(n, 1e18):
                cost[n] = c
                came[n] = cur
                heapq.heappush(openq, (c + math.hypot(n[0] - t[0], n[1] - t[1]), n))
    if t not in came:
        return None
    cells = []
    n = t
    while n is not None:
        cells.append(n)
        n = came[n]
    cells.reverse()
    # shortcut smoothing
    pts = [np.asarray(start[:2], float)]
    i = 0
    while i < len(cells) - 1:
        j = len(cells) - 1
        while j > i + 1:
            a, b = g.xy(cells[i]), g.xy(cells[j])
            steps = int(np.linalg.norm(b - a) / res) + 1
            if all(ok(g.ij(a + (b - a) * u)) for u in np.linspace(0, 1, steps)):
                break
            j -= 1
        pts.append(g.xy(cells[j]))
        i = j
    pts[-1] = np.asarray(goal[:2], float)
    out = []
    for k, p in enumerate(pts[1:], 1):
        yaw = goal[2] if k == len(pts) - 1 else math.degrees(math.atan2(p[1] - pts[k - 1][1], p[0] - pts[k - 1][0]))
        out.append((float(p[0]), float(p[1]), float(yaw)))
    return out
