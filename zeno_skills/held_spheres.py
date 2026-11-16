"""Spheres for a held object in the planner's model (docs/MOTION_ARCHITECTURE.md 4.4).

cuRobo models the robot, and what its hands hold, as spheres.  A held object's spheres have to
stay close to its surface both ways: sticking out by more than LEAVE_GAP below it, a set-down's
end (the load LEAVE_GAP above its support) is in collision; falling short of it, a load's edge
scrapes a pot's rim or a cup unseen (T17 pot_lid, T04 mug, 11-10).  The old box_spheres (equal
spheres inscribed in the cells of the bounding box) fell short by up to 2-3 cm at the edges and
stuck out at the corners of round objects.

``fit(pieces)``: the object as convex pieces (its colliders: cuboids and convex hulls), spheres of
varying radius -- each centred inside a piece, its radius the centre's depth in that piece plus
``out`` (so nothing sticks out of the object by more than ``out``) -- chosen greedily until every
sample of the object's surface lies within ``gap`` of one.  Big spheres fill the inside, small ones
the edges.  Pure numpy / scipy: no simulator, no cuRobo."""

from __future__ import annotations

import heapq

import numpy as np

from .tolerances import HELD_SPHERE_GAP as GAP, HELD_SPHERE_GAP_MAX as GAP_MAX, HELD_SPHERE_OUT as OUT

SAMPLE = 0.003    # m: spacing of the surface samples (a point between samples is within SAMPLE / sqrt(3) of one)
VERSION = 3       # bump when the fit changes (the cache of motion._cached_fit is keyed by it)
CANDIDATES = 12000 # inside centres tried (the big spheres), on a grid spaced to give about this many (at
                   # least 6 mm apart); the surface samples are tried too (small spheres for the edges)
CUBOID_FACES = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                         [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])


def cuboid(dims, T=np.eye(4)):
    """A box of edge lengths ``dims`` at pose T as a piece (vertices, triangles)."""
    c = 0.5 * np.asarray(dims, float) * np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])
    return c @ np.asarray(T, float)[:3, :3].T + np.asarray(T, float)[:3, 3], CUBOID_FACES


def hull(points):
    """The convex hull of ``points`` as a piece (vertices, triangles)."""
    from scipy.spatial import ConvexHull
    P = np.asarray(points, float)
    h = ConvexHull(P)
    return P[h.vertices], np.searchsorted(h.vertices, h.simplices)


def _planes(V, F):
    """Outward unit normals n and offsets d of a convex piece's faces (n . x <= d inside)."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(b - a, c - a)
    keep = np.linalg.norm(n, axis=1) > 1e-12
    n, a = n[keep] / np.linalg.norm(n[keep], axis=1, keepdims=True), a[keep]
    flip = np.einsum("ij,ij->i", n, V.mean(0) - a) > 0          # pointing in: turn it out
    n[flip] = -n[flip]
    return n, np.einsum("ij,ij->i", n, a)


def depth(planes, X):
    """Depth of points X inside a convex piece (negative: outside; for an outside point a lower bound)."""
    n, d = planes
    return np.min(d[None] - X @ n.T, axis=1)


def surface(pieces, step=SAMPLE):
    """Samples of the outside surface of the union of ``pieces``: each face sampled on a triangular
    grid about ``step`` apart, the samples inside another piece left out."""
    planes = [_planes(V, F) for V, F in pieces]
    out = []
    for k, (V, F) in enumerate(pieces):
        for f in F:
            a, b, c = V[f]
            m = max(1, int(np.ceil(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / step)))
            i, j = np.meshgrid(np.arange(m + 1), np.arange(m + 1), indexing="ij")
            ok = i + j <= m
            u, v = i[ok] / m, j[ok] / m
            out.append(a + u[:, None] * (b - a) + v[:, None] * (c - a))
    S = np.unique(np.round(np.vstack(out), 5), axis=0)
    inside = np.zeros(len(S), bool)
    for pl in planes:
        inside |= depth(pl, S) > 1e-4
    return S[~inside]


def fit(pieces, out=OUT, gap=GAP, n_max=None, gap_max=GAP_MAX):
    """(spheres (n, 4): x, y, z, r in the pieces' frame, the gap reached): the fewest spheres the
    greedy cover finds that stick out of the union of the convex ``pieces`` by at most ``out``
    and leave no surface sample further than ``gap`` from them; with more than ``n_max`` the gap
    is widened (x1.25) up to ``gap_max`` -- past it ValueError."""
    from scipy.spatial import cKDTree
    planes = [_planes(V, F) for V, F in pieces]
    S = surface(pieces)
    lo = np.min([V.min(0) for V, _ in pieces], axis=0)
    hi = np.max([V.max(0) for V, _ in pieces], axis=0)
    step = max(0.006, float(np.prod(np.maximum(hi - lo, 1e-3)) / CANDIDATES) ** (1 / 3))
    g = [np.arange(l + step / 2, h, step) if h - l > step else np.array([(l + h) / 2]) for l, h in zip(lo, hi)]
    C = np.stack(np.meshgrid(*g, indexing="ij"), -1).reshape(-1, 3)
    # the surface samples too (radius out: a centre on the surface), so thin parts can always be covered
    C = np.vstack([C, S])
    D = np.max([depth(pl, C) for pl in planes], axis=0)       # the deepest any piece holds it
    keep = D >= -1e-9
    C, R = C[keep], np.maximum(D[keep], 0.0) + out
    tree = cKDTree(S)
    while True:
        cover = tree.query_ball_point(C, R + gap, return_sorted=False)
        covered = np.zeros(len(S), bool)
        heap = [(-len(c), i) for i, c in enumerate(cover)]
        heapq.heapify(heap)
        chosen = []
        while not covered.all() and heap:
            neg, i = heapq.heappop(heap)
            n = int((~covered[cover[i]]).sum())
            if n == 0:
                continue
            if heap and n < -heap[0][0]:
                heapq.heappush(heap, (-n, i))                    # stale count: try it again later
                continue
            chosen.append(i)
            covered[cover[i]] = True
        if n_max is None or len(chosen) <= n_max:
            return np.c_[C[chosen], R[chosen]], gap
        if gap >= gap_max:
            raise ValueError(f"{len(chosen)} spheres at gap {gap:.4f} m: more than {n_max}")
        gap = min(gap * 1.25, gap_max)


def check(pieces, spheres, n=20000, seed=0):
    """(how far the spheres stick out of the union at most, how far the surface is from them at
    most) on dense random samples -- what a test asserts."""
    rng = np.random.default_rng(seed)
    planes = [_planes(V, F) for V, F in pieces]
    S = surface(pieces, step=SAMPLE / 3)
    S = S[rng.choice(len(S), min(n, len(S)), replace=False)]
    gaps = np.min(np.linalg.norm(S[:, None] - spheres[None, :, :3], axis=2) - spheres[None, :, 3], axis=1)
    # sticking out: points on each sphere's surface, their distance outside the union
    u = rng.normal(size=(64, 3))
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    P = (spheres[:, None, :3] + spheres[:, None, 3:] * u[None]).reshape(-1, 3)
    outside = -np.max([depth(pl, P) for pl in planes], axis=0)
    return float(max(outside.max(), 0.0)), float(gaps.max())
