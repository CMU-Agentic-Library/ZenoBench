"""Whole-body base planning (docs/COLLISION_PLAN.md step 2).

The base moves on a lattice of (x, y, yaw) poses -- RES m, YAW_STEP deg -- carrying the arms in one of
a chain of postures ("modes", e.g. current -> tucked -> hanging -> tucked).  A mode whose posture
is the same as a later one's (the tuck and the arrival) passes to it where it stands without
moving an arm: the modes between (hanging at the side, narrower) are a detour the search takes
only where the path needs it.  A pose is feasible in a
mode when the whole robot there is clear: the base's footprint, chassis and column, of the static
colliders at their heights (WorldModel.footprints_clear, a hand-made shape: the base collider is
off in the simulator and has no spheres in cuRobo), both arms at that posture and what the hands hold of
the scene's real colliders (Motion.base_depths); a posture switch m -> m+1 is allowed at a pose
where the straight joint interpolation between the two postures is.  A* finds the cheapest path from
the start through every mode to the goal pose (or, without a goal, to the nearest pose where the
last mode is reached: "where can the arm fold").  Feasibility is evaluated lazily, BLOCK x BLOCK
cells and every yaw at once, so only the region the search touches costs GPU time.

Between lattice poses the robot moves too: a 15 deg turn sweeps a hand 0.7 m out by 18 cm, a cell
by 5 cm.  The path the search returns is checked edge by edge (and each posture switch) at poses
no point of the robot moves more than DENSE apart.  Where an edge fails, the same move out of
every node of its block is checked the same way (one batch) and the search runs again avoiding
the failed ones (lazy edge evaluation: only the blocks and moves where a path failed pay for it).  The shortcuts that
smooth the path are checked the same way.

Nothing near the start or goal is exempt.  The robot starts where it is, though, and may already
touch something in its start posture: in the first mode a pose is feasible when it does not sink
deeper than the start does.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

import numpy as np

RES = 0.05                  # m between lattice cells
YAW_STEP = 15.0             # deg between lattice headings
N_YAW = int(round(360 / YAW_STEP))
BLOCK = 8                   # cells per side of a lazily evaluated block (x every heading)
TURN_COST = 1.0             # m of driving one radian of turning costs (cheap turns let every heading of a
                            # cell be expanded)
SWITCH_COST = 0.3           # m a posture switch costs
SWITCH_SAMPLES = 6          # postures checked along a switch on the lattice (both ends included)
SWITCH_FINE = 129           # postures a switch is sampled at, before dense_sets thins them to DENSE
DENSE = 0.02                # m: the farthest any point of the robot moves between two poses (or postures)
                            # the path is checked at
LAZY_ROUNDS = 40            # searches a plan may take, each cutting the edges the last path failed on
MARGIN = 2.0                # m the search may stray beyond the start / goal box
REGION_RADIUS = 1.0         # m around the start searched for a goal region
DEPTH_TOL = 1e-4            # m: a penetration this shallow is clear (numerical slack of the sphere queries,
                            # not a margin); every whole-body base check compares against it
MAX_EXPAND = 200000          # lattice states one search may expand before it gives up (a budget, unmeasured)
GREEDY = 2.5                # weighted A*: the heuristic counts this much (a path at most this much costlier
                            # than the cheapest, for far fewer expansions over a 4-D lattice)
NBRS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0),
        (0, 0, 1), (0, 0, -1)]


@dataclass
class Step:
    """One step of a base plan: ``drive`` along ``path`` [(x, y, yaw_deg)] in posture ``mode``, or
    ``switch`` the arms from posture ``mode`` to ``mode + 1`` where the base stands."""
    kind: str
    mode: int
    path: list = field(default_factory=list)


class Lattice:
    """Feasibility of lattice poses per mode and of posture switches, evaluated by blocks.

    ``depths(poses, sets)``: (P, N) penetration of the robot with its base at poses ((N, 3) x, y,
    yaw rad) and its body as each sphere set (Motion.base_depths); ``modes``: one sphere set per
    posture, ``switches[m]``: the sets along the switch m -> m+1; ``tol0``: what the first mode
    may penetrate (the start's own depth); ``footprint(poses)``: (N,) bool, the column's low part
    clear (any posture); the start node is exempt from it (the robot stands there)."""

    def __init__(self, depths, origin, modes, switches, tol0=0.0, footprint=None, start=None, dense_switches=None):
        self.depths, self.origin = depths, np.asarray(origin, float)
        self.modes, self.switches, self.tol0 = modes, switches, tol0
        self.dense_switches = switches if dense_switches is None else dense_switches
        self.footprint, self.start = footprint, start
        # per mode: the farthest sphere centre from the base centre (what a turn sweeps)
        self.reach = [float(np.max(np.hypot(s[:, 0], s[:, 1]))) if len(s) else 0.0 for s in modes]
        # identical postures: one feasibility cache (canon), and the later reached from the earlier
        # without moving an arm (skip); min_sw: switches still needed from a mode to the last
        same = [[a.shape == b.shape and np.allclose(a, b) for b in modes] for a in modes]
        self.canon = [next(c for c in range(m + 1) if same[c][m] and self._tol(c) == self._tol(m))
                      for m in range(len(modes))]
        self.skip = [[m2 for m2 in range(m + 2, len(modes)) if same[m][m2]] for m in range(len(modes))]
        self.min_sw = [0] * len(modes)
        for m in range(len(modes) - 2, -1, -1):
            self.min_sw[m] = min([1 + self.min_sw[m + 1]] + [self.min_sw[m2] for m2 in self.skip[m]])
        self.cut = set()                 # (node, node) transitions the dense check refused
        self.start_low = True            # the start pose's footprint is clear (else leaving it is exempt)
        self.blocks = {}
        self.evaluated = 0

    def pose(self, n):
        i, j, k = n[:3]
        return (float(self.origin[0] + i * RES), float(self.origin[1] + j * RES), math.radians(k * YAW_STEP))

    def _tol(self, m):
        return self.tol0 if m == 0 else 0.0

    def _block(self, bi, bj, what):
        key = (bi, bj, what)
        if key not in self.blocks:
            ii, jj, kk = np.meshgrid(np.arange(BLOCK) + bi * BLOCK, np.arange(BLOCK) + bj * BLOCK,
                                     np.arange(N_YAW), indexing="ij")
            poses = np.c_[self.origin[0] + ii.ravel() * RES, self.origin[1] + jj.ravel() * RES,
                          np.radians(kk.ravel() * YAW_STEP)]
            kind, m = what
            if kind == "low":
                ok = self.footprint(poses) if self.footprint is not None else np.ones(len(poses), bool)
                self.blocks[key] = ok.reshape(BLOCK, BLOCK, N_YAW)
                return self.blocks[key]
            low = self._block(bi, bj, ("low", 0)).ravel()
            if kind == "mode":
                ok = self.depths(poses, self.modes[m][None])[0] <= self._tol(m) + DEPTH_TOL
            else:
                d = self.depths(poses, self.switches[m])
                # along the switch the first mode's tolerance holds, its end posture is strict
                ok = np.all(d[:-1] <= self._tol(m) + DEPTH_TOL, axis=0) & (d[-1] <= self._tol(m + 1) + DEPTH_TOL)
            self.evaluated += len(poses)
            self.blocks[key] = (ok & low).reshape(BLOCK, BLOCK, N_YAW)
        return self.blocks[key]

    def free(self, n, m):
        i, j, k = n[:3]
        if m == 0 and tuple(n[:3]) == self.start:
            return bool(self._block(i // BLOCK, j // BLOCK, ("mode", 0))[i % BLOCK, j % BLOCK, k % N_YAW] or
                        self.depths(np.array([self.pose(n)]), self.modes[0][None])[0, 0] <= self.tol0 + DEPTH_TOL)
        return bool(self._block(i // BLOCK, j // BLOCK, ("mode", self.canon[m]))[i % BLOCK, j % BLOCK, k % N_YAW])

    def reaches(self, n, goal_pose):
        """The straight move from lattice node n (in the last mode) to the exact goal pose is clear: a
        tight park sits off the lattice, its nearest node may already touch what the goal clears."""
        key = ("goal", tuple(n[:3]))
        if key not in self.blocks:
            self.blocks[key] = self.segments_clear([(self.pose(n), goal_pose)], len(self.modes) - 1)[0]
        return self.blocks[key]

    def segments_clear(self, segs, m, exempt=None):
        """Per segment (a, b) (x, y, yaw rad): the whole robot in mode m clear at every pose of
        segment(a, b), all in one batch; ``exempt[i]``: segment i leaves the start, whose footprint
        is tight (the robot stands there already): its footprint counts from the first pose clear
        of it on."""
        runs = [segment(a, b, self.reach[m]) for a, b in segs]
        cuts = np.cumsum([len(r) for r in runs])[:-1]
        poses = np.vstack(runs)
        ok = self.depths(poses, self.modes[m][None])[0] <= self._tol(m) + DEPTH_TOL
        self.evaluated += len(poses)
        out = []
        lows = np.split(self.footprint(poses), cuts) if self.footprint is not None else None
        for i, part in enumerate(np.split(ok, cuts)):
            if lows is not None:
                low = lows[i].copy()
                if exempt is not None and exempt[i]:
                    low[:int(np.argmax(low)) if low.any() else len(low)] = True
                part = part & low
            out.append(bool(np.all(part)))
        return out

    def edge_ok(self, n, d, m):
        """The drive move NBRS[d] out of node n in mode m passes the dense check: known in the blocks
        a failed path activated for that move, assumed elsewhere (the path check finds out)."""
        blk = self.blocks.get((n[0] // BLOCK, n[1] // BLOCK, ("edges", self.canon[m], d)))
        return True if blk is None else bool(blk[n[0] % BLOCK, n[1] % BLOCK, n[2] % N_YAW])

    def activate(self, n, d, m):
        """Dense-check the drive move NBRS[d] out of every node of n's block in mode m, one batch:
        the poses strictly between the two nodes (the nodes are the lattice's)."""
        bi, bj = n[0] // BLOCK, n[1] // BLOCK
        m = self.canon[m]
        key = (bi, bj, ("edges", m, d))
        if key in self.blocks:
            return
        ii, jj, kk = np.meshgrid(np.arange(BLOCK) + bi * BLOCK, np.arange(BLOCK) + bj * BLOCK,
                                 np.arange(N_YAW), indexing="ij")
        base = np.c_[self.origin[0] + ii.ravel() * RES, self.origin[1] + jj.ravel() * RES,
                     np.radians(kk.ravel() * YAW_STEP)]
        at_start = (ii.ravel() == self.start[0]) & (jj.ravel() == self.start[1]) & (kk.ravel() == self.start[2]) \
            if m == 0 and not self.start_low else np.zeros(len(base), bool)
        ok = np.ones(len(base), bool)
        di, dj, dk = NBRS[d]
        step = np.array([di * RES, dj * RES, math.radians(dk * YAW_STEP)])
        k = int(math.ceil((math.hypot(step[0], step[1]) + self.reach[m] * abs(step[2])) / DENSE))
        if k > 1:
            us = np.arange(1, k) / k
            poses = (base[:, None, :] + us[None, :, None] * step).reshape(-1, 3)
            good = self.depths(poses, self.modes[m][None])[0] <= self._tol(m) + DEPTH_TOL
            if self.footprint is not None:
                good &= self.footprint(poses) | np.repeat(at_start, len(us))
            ok = good.reshape(len(base), len(us)).all(axis=1)
            self.evaluated += len(poses)
        self.blocks[key] = ok.reshape(BLOCK, BLOCK, N_YAW)

    def switch_clear(self, n, m):
        """The switch m -> m+1 at node n, checked at every posture of its dense sampling."""
        d = self.depths(np.array([self.pose(n)]), self.dense_switches[m])[:, 0]
        self.evaluated += len(d)
        return bool(np.all(d[:-1] <= self._tol(m) + DEPTH_TOL) and d[-1] <= self._tol(m + 1) + DEPTH_TOL)

    def can_switch(self, n, m):
        i, j, k = n[:3]
        return bool(self._block(i // BLOCK, j // BLOCK, ("switch", m))[i % BLOCK, j % BLOCK, k % N_YAW])


def segment(a, b, reach):
    """Poses (n, 3) along the straight (x, y, yaw) move from a to b (yaw rad, the short way round, as
    Rig.drive_base drives it), so close that no point within ``reach`` of the base centre moves
    more than DENSE from one to the next."""
    a, b = np.asarray(a, float), np.array(b, float)
    b[2] = a[2] + (b[2] - a[2] + math.pi) % (2 * math.pi) - math.pi
    n = int(math.ceil((math.hypot(b[0] - a[0], b[1] - a[1]) + reach * abs(b[2] - a[2])) / DENSE)) + 1
    return a + (b - a) * np.linspace(0, 1, max(n, 2))[:, None]


def dense_sets(fine):
    """Of the sphere sets ``fine`` ((P, S, 4) along a posture switch), the first, the last and
    between them the last set before some sphere would move more than DENSE from the one kept
    before (fine itself samples closer than DENSE)."""
    keep, last = [0], fine[0]
    for p in range(1, len(fine)):
        if np.max(np.linalg.norm(fine[p][:, :3] - last[:, :3], axis=1)) > DENSE and keep[-1] != p - 1:
            keep.append(p - 1)
            last = fine[p - 1]
    if keep[-1] != len(fine) - 1:
        keep.append(len(fine) - 1)
    return fine[keep]


def _yaw_bin(yaw_deg):
    return int(round(yaw_deg / YAW_STEP)) % N_YAW


def _ang(a, b):
    """|a - b| in yaw bins, the short way round."""
    d = (a - b) % N_YAW
    return min(d, N_YAW - d)


def distance_field(passable, origin, goal, bounds, start):
    """(D, i0, j0): metres from each lattice cell in ``bounds`` to the ``goal`` cell moving on the
    8-connected cells where ``passable(xy)`` ((N, 2) -> (N,) bool: the column's inscribed circle
    is clear, a relaxation of the footprint at any heading), inf where it cannot get to;
    D[i - i0, j - j0]."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    i0, j0, i1, j1 = bounds
    nx, ny = i1 - i0 + 1, j1 - j0 + 1
    ii, jj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing="ij")
    free = passable(np.c_[origin[0] + ii.ravel() * RES, origin[1] + jj.ravel() * RES]).reshape(nx, ny)
    for c in (goal, start):
        free[c[0] - i0, c[1] - j0] = True        # standing there already / checked as the goal
    idx = np.arange(nx * ny).reshape(nx, ny)
    rows, cols, w = [], [], []
    for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
        a = free[max(0, -di):nx - max(0, di), max(0, -dj):ny - max(0, dj)]
        b = free[max(0, di):nx - max(0, -di), max(0, dj):ny - max(0, -dj)]
        ok = a & b
        ia = idx[max(0, -di):nx - max(0, di), max(0, -dj):ny - max(0, dj)][ok]
        ib = idx[max(0, di):nx - max(0, -di), max(0, dj):ny - max(0, -dj)][ok]
        rows.append(ia), cols.append(ib), w.append(np.full(len(ia), math.hypot(di, dj) * RES))
    g = coo_matrix((np.concatenate(w), (np.concatenate(rows), np.concatenate(cols))), shape=(nx * ny, nx * ny))
    D = dijkstra(g.tocsr(), directed=False, indices=idx[goal[0] - i0, goal[1] - j0])
    return D.reshape(nx, ny), i0, j0


def search(lat, start, goal, bounds, field=None, goal_pose=None):
    """A* over (i, j, k, mode) -- a mode passes to the next by a posture switch, or for free to a
    later one of the same posture (Lattice.skip) -- from ``start`` (i, j, k) in mode 0 to a node of
    the last mode within one cell and one heading of ``goal`` (i, j, k) that reaches ``goal_pose``
    (x, y, yaw rad) straight -- or (goal None) to any pose of the last mode.  Transitions in
    ``lat.cut`` and drive moves the activated blocks refuse (Lattice.edge_ok) are not taken.
    ``field``: distance_field to the goal (else the straight-line distance).  Returns the node
    list, or None."""
    last = len(lat.modes) - 1
    turn = TURN_COST * math.radians(YAW_STEP)

    def h(n):
        if goal is None:
            return 0.0
        if field is not None:
            D, i0, j0 = field
            d = D[n[0] - i0, n[1] - j0]
        else:
            d = math.hypot(n[0] - goal[0], n[1] - goal[1]) * RES
        return d + _ang(n[2], goal[2]) * turn + SWITCH_COST * lat.min_sw[n[3]]

    s = (*start, 0)
    lat.expanded = 0
    if not lat.free(s, 0):
        lat.limit = False
        return None
    openq = [(GREEDY * h(s), 0.0, s)]
    came, cost = {s: None}, {s: 0.0}
    closed = set()
    expanded = 0
    while openq:
        _, c, cur = heapq.heappop(openq)
        if cur in closed:
            continue                     # weighted A* without reopening: still within GREEDY of the best
        closed.add(cur)
        if cur[3] == last and (goal is None or (
                max(abs(cur[0] - goal[0]), abs(cur[1] - goal[1])) <= 1 and _ang(cur[2], goal[2]) <= 1 and
                lat.reaches(cur, goal_pose))):
            out = []
            while cur is not None:
                out.append(cur)
                cur = came[cur]
            return out[::-1]
        expanded += 1
        lat.expanded = expanded
        if expanded > MAX_EXPAND:
            lat.limit = True
            _visited(lat, came)
            return None
        i, j, k, m = cur
        steps = []
        for d, (di, dj, dk) in enumerate(NBRS):
            n = (i + di, j + dj, (k + dk) % N_YAW, m)
            if not (bounds[0] <= n[0] <= bounds[2] and bounds[1] <= n[1] <= bounds[3]) or not lat.edge_ok(cur, d, m):
                continue
            steps.append((n, math.hypot(di, dj) * RES + abs(dk) * turn))
        if m < last:
            steps.append(((i, j, k, m + 1), SWITCH_COST))
        steps += [((i, j, k, m2), 0.0) for m2 in lat.skip[m]]
        for n, dc in steps:
            if (cur, n) in lat.cut:
                continue
            hn = h(n)
            if hn == math.inf:
                continue                         # the inscribed cylinder cannot reach the goal from there
            if n[3] == m + 1:
                if not (lat.can_switch(cur, m) and lat.free(n, n[3])):
                    continue
            elif n[3] != m:
                if not lat.free(n, n[3]):        # a skip: the same posture, nothing moves
                    continue
            elif not lat.free(n, m):
                continue
            nc = c + dc
            if n not in closed and nc < cost.get(n, math.inf):
                cost[n], came[n] = nc, cur
                heapq.heappush(openq, (nc + GREEDY * hn, nc, n))
    lat.limit = False
    _visited(lat, came)
    return None


def _visited(lat, came):
    """What a failed search reached: per mode the states and the xy extent (m from the start)."""
    out = {}
    for n in came:
        st = out.setdefault(n[3], [0, [math.inf, math.inf, -math.inf, -math.inf]])
        st[0] += 1
        e = st[1]
        e[0], e[1], e[2], e[3] = min(e[0], n[0]), min(e[1], n[1]), max(e[2], n[0]), max(e[3], n[1])
    lat.visited = {m: (c, [round(v * RES, 2) for v in e]) for m, (c, e) in sorted(out.items())}


def _move(a, b):
    """The index in NBRS of the drive move from node a to its neighbour b."""
    dk = (b[2] - a[2] + N_YAW // 2) % N_YAW - N_YAW // 2
    return NBRS.index((b[0] - a[0], b[1] - a[1], dk))


def _leaves_start(lat, n):
    return n[3] == 0 and tuple(n[:3]) == lat.start and not lat.start_low


def _bad_transitions(lat, nodes):
    """The transitions of a searched path that fail the dense check: drives along segment(),
    switches at every posture of their dense sampling; one batch per mode."""
    bad, drives = [], {}
    for a, b in zip(nodes[:-1], nodes[1:]):
        if b[3] == a[3] + 1:
            if not lat.switch_clear(a, a[3]):
                bad.append((a, b))
        elif b[3] != a[3]:
            continue                             # a skip: the same posture, nothing moves
        else:
            drives.setdefault(a[3], []).append((a, b))
    for m, pairs in drives.items():
        ok = lat.segments_clear([(lat.pose(a), lat.pose(b)) for a, b in pairs], m,
                                [_leaves_start(lat, a) for a, _ in pairs])
        bad += [p for p, o in zip(pairs, ok) if not o]
    return bad


def _shortcut(lat, nodes, m):
    """Fewest lattice nodes of one mode's run: from each kept node, the farthest later one whose
    straight (x, y, yaw) move passes the dense check (every candidate of a node in one batch; the
    next node always does, the search path was checked)."""
    if len(nodes) <= 2:
        return nodes
    out, i = [nodes[0]], 0
    while i < len(nodes) - 1:
        js = list(range(i + 2, len(nodes)))
        ok = lat.segments_clear([(lat.pose(nodes[i]), lat.pose(nodes[j])) for j in js], m,
                                [_leaves_start(lat, nodes[i])] * len(js)) if js else []
        i = max([j for j, o in zip(js, ok) if o], default=i + 1)
        out.append(nodes[i])
    return out


def plan(depths, start, goal, modes, switches, area=None, footprint=None, passable=None, dense_switches=None):
    """Base plan from ``start`` (x, y, yaw_deg) through every mode to ``goal`` (x, y, yaw_deg; None:
    the nearest pose where the last mode is reached).  ``depths`` / ``modes`` / ``switches`` as in
    Lattice, ``dense_switches`` the same switches sampled every DENSE (dense_sets; else
    ``switches``), ``area`` (x0, y0, x1, y1) where the base may go (else MARGIN around the start
    and goal), ``footprint`` as in Lattice, ``passable`` as in distance_field (else the
    straight-line distance guides the search).  Returns ([Step], lattice), or (None, lattice)
    with ``lattice.why``."""
    s = (0, 0, _yaw_bin(start[2]))
    here = np.array([[start[0], start[1], math.radians(start[2])], [start[0], start[1], math.radians(s[2] * YAW_STEP)]])
    tol0 = float(depths(here, modes[0][None]).max())      # where the robot stands it may already touch
    lat = Lattice(depths, start[:2], modes, switches, tol0, footprint, s, dense_switches)
    lat.why, lat.rounds = None, 0
    if footprint is not None:
        lat.start_low = bool(footprint(here[:1])[0])
    # the exact start to its lattice heading: the first move of every path
    if not lat.segments_clear([(here[0], here[1])], 0, [not lat.start_low])[0]:
        lat.why, lat.expanded, lat.limit = "the turn to the start's lattice heading is blocked", 0, False
        return None, lat
    gp = np.array([[goal[0], goal[1], math.radians(goal[2])]]) if goal is not None else None
    if goal is not None and (depths(gp, modes[-1][None])[0, 0] > DEPTH_TOL or
                             (footprint is not None and not footprint(gp)[0])):
        lat.why = "the goal pose collides in the arrival posture"
        return None, lat
    if goal is None:
        r = int(math.ceil(REGION_RADIUS / RES))
        g, bounds = None, (-r, -r, r, r)
    else:
        g = (int(round((goal[0] - start[0]) / RES)), int(round((goal[1] - start[1]) / RES)), _yaw_bin(goal[2]))
        pad = int(math.ceil(MARGIN / RES))
        bounds = (min(0, g[0]) - pad, min(0, g[1]) - pad, max(0, g[0]) + pad, max(0, g[1]) + pad)
        if area is not None:
            a = [int(math.floor((area[0] - start[0]) / RES)), int(math.floor((area[1] - start[1]) / RES)),
                 int(math.ceil((area[2] - start[0]) / RES)), int(math.ceil((area[3] - start[1]) / RES))]
            bounds = (min(a[0], 0, g[0]), min(a[1], 0, g[1]), max(a[2], 0, g[0]), max(a[3], 0, g[1]))
    field = distance_field(passable, start[:2], g, bounds, s) if g is not None and passable is not None else None
    if field is not None and field[0][s[0] - field[1], s[1] - field[2]] == math.inf:
        lat.why, lat.expanded, lat.limit = "no base path: even the column's inscribed circle cannot get there", 0, False
        return None, lat
    for lat.rounds in range(1, LAZY_ROUNDS + 1):
        nodes = search(lat, s, g, bounds, field, None if goal is None else (goal[0], goal[1], math.radians(goal[2])))
        if nodes is None:
            lat.why = (f"search limit: {lat.expanded} states expanded" if lat.limit else "no whole-body path") + \
                f" ({lat.evaluated} poses checked, {lat.rounds} searches)"
            return None, lat
        bad = _bad_transitions(lat, nodes)
        if not bad:
            break
        for a, b in bad:
            lat.cut.add((a, b))
            if a[3] == b[3]:
                lat.activate(a, _move(a, b), a[3])
    else:
        lat.why = f"{LAZY_ROUNDS} searched paths each crossed a blocked edge"
        return None, lat
    steps, run = [], [nodes[0]]
    for n in nodes[1:]:
        if n[3] != run[-1][3]:
            steps.append(_drive(lat, run))
            if n[3] == run[-1][3] + 1:
                steps.append(Step("switch", run[-1][3], [_deg(lat.pose(run[-1]))]))
            run = [n]
        else:
            run.append(n)
    steps.append(_drive(lat, run))
    # the exact start and goal poses (the lattice snaps the heading, the goal also the position)
    first = next(st for st in steps if st.kind == "drive")
    first.path.insert(0, (float(start[0]), float(start[1]), float(start[2])))
    if goal is not None:
        steps[-1].path.append((float(goal[0]), float(goal[1]), float(goal[2])))
    for st in steps:
        if st.kind == "drive":           # a repeated point: the exact start / goal stands
            path = []
            for k, pt in enumerate(st.path):
                if path and np.max(np.abs(np.subtract(pt, path[-1]))) <= 1e-6:
                    path[-1] = pt if k == len(st.path) - 1 else path[-1]
                else:
                    path.append(pt)
            st.path = path
    return [st for st in steps if st.kind == "switch" or len(st.path) > 1], lat


def _deg(p):
    return (p[0], p[1], math.degrees(p[2]))


def _drive(lat, run):
    m = run[0][3]
    return Step("drive", m, [_deg(lat.pose(n)) for n in _shortcut(lat, run, m)])
