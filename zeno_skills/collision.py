"""The base's world: the footprint check and the inscribed-circle relaxation
(base_planner.py) against the static scene -- its PhysX colliders sliced at the heights of the
base's two layers (StaticBands, WorldModel.use_colliders; the annotation's
boxes where no stage is at hand) -- plus the moving parts of articulated
furniture posed at their current joint value.

The arm does not use these boxes: arm IK and collision go to cuRobo against
the scene's real colliders (motion.py).  WorldModel also carries the joint
values of both arms (``right_q`` / ``left_q``) that a query on the other arm
keeps locked.
"""

from __future__ import annotations

import math
import os
from contextlib import contextmanager

import numpy as np

from .tolerances import FOOTPRINT_MARGIN

# The base in two layers, measured on base_link.STL's cross sections (11-09): a wide chassis up to
# 0.25 m -- a square of +-0.2442 m with rounded corners, 0.296 m from the centre at 45 deg, not the
# square's 0.345 -- and above it a slim column behind the centre up to 1.05 m.  Until 11-09 the
# footprint was the whole bounding box, a 0.49 m square column 0.03-1.05 m tall: at 0.6 m it took
# 0.49 m where the robot has 0.13 m, and turned 45 deg its corners stood 5 cm further out.
BASE_HALF = 0.2442        # m: half size of the chassis' square (base_link.STL's bounding box: +-0.2442 m)
LOW_CORNER = 0.115        # m: radius of the chassis' rounded corners (0.296 m from the centre at 45 deg)
LOW_BOTTOM = 0.027        # m: the chassis' underside (base_link.STL; the floor and the rugs lie below it)
LOW_TOP = 0.27            # m: top of the chassis (the mesh's 0.25 m and its taper, 2 cm up)
COLUMN_XY = (-0.115, -0.063, -0.010, 0.063)   # m: the column above the chassis, base frame x0 y0 x1 y1
COLUMN_TOP = 1.05         # m: the column's top (boxes starting below it are in its way)
# Each layer is a band of heights, and a box is in its way when their heights overlap -- never a
# sample height (until 11-10 the chassis was one sample at 0.15 m and the column one at 0.6 m): a
# 4 cm block on the floor passed under the chassis' sample while the real chassis, 2.7 cm off the
# floor, drives into it.  The bands are the base's own heights, with no margin up or down:
# FOOTPRINT_MARGIN is a margin in xy only.
LOW_SPAN = (LOW_BOTTOM, LOW_TOP)
COLUMN_SPAN = (LOW_TOP, COLUMN_TOP)
LOW_SIDE_N = 8            # points per side of the chassis' inner square (the corners' centres) -- its
                          # outline and centre are tested within LOW_CORNER + margin, ~1 mm short at most
COLUMN_GRID = 4           # points per side the column's rectangle is sampled at
CIRCLE_RES = 0.025  # m: grid of circles_clear against the static boxes (half the base planner's lattice step)
PART_SAMPLE = 0.05  # m between the heights a layer is sampled at against a moving part whose frame is not
                    # upright (none in the scenes so far: every door and drawer turns or slides on its own axis)


def _base_points():
    """The base's test points in its own frame, in xy -- each layer's heights are its band: the
    chassis' (the outline and centre of the square its rounded corners are drawn around: a point
    within LOW_CORNER + margin of a box is the chassis within margin of it) and the column's (its
    rectangle on a grid: within margin of a box as the old column's)."""
    h = BASE_HALF - LOW_CORNER
    t = np.linspace(-h, h, LOW_SIDE_N)
    low = np.unique(np.round(np.concatenate([np.c_[t, np.full_like(t, -h)], np.c_[t, np.full_like(t, h)],
                                             np.c_[np.full_like(t, -h), t], np.c_[np.full_like(t, h), t],
                                             [[0.0, 0.0]]]), 9), axis=0)
    x0, y0, x1, y1 = COLUMN_XY
    col = np.array([[u, v] for u in np.linspace(x0, x1, COLUMN_GRID) for v in np.linspace(y0, y1, COLUMN_GRID)])
    return low, col


LOW_PTS, COLUMN_PTS = _base_points()
REACH_R = (BASE_HALF - LOW_CORNER) * math.sqrt(2) + LOW_CORNER   # m: the base's farthest point from its centre


def _place(pts, x, y, c, s):
    """Base-frame points (N, 2) at base poses: x, y, c = cos yaw, s = sin yaw, each (M, 1) -> (M, N, 2)."""
    return np.stack([x + c * pts[:, 0] - s * pts[:, 1], y + s * pts[:, 0] + c * pts[:, 1]], -1)


def _spans_overlap(B, span):
    """(N,) bool: each box of ``B`` (N, 6) reaches into the height band ``span``."""
    return (B[:, 5] > span[0]) & (B[:, 2] < span[1])


def _aabb_dist(pts, lo, hi, zspan=None):
    """Distance from each point to the box [lo, hi]; with ``zspan`` the points are vertical segments
    spanning those heights (their own z is ignored): the distance in xy when the segment and the box
    overlap in height, inf when they do not."""
    d = np.maximum(np.maximum(lo - pts, pts - hi), 0.0)
    if zspan is None:
        return np.linalg.norm(d, axis=1)
    if lo[2] >= zspan[1] or hi[2] <= zspan[0]:
        return np.full(len(pts), np.inf)
    return np.linalg.norm(d[:, :2], axis=1)


# The static scene as the base sees it, from the colliders themselves (11-09): a table is its top and
# legs, not the box from the floor to its top, so the low chassis may go under the top while the
# column stays out.  Each layer of the base gets the xy footprint of the static colliders in the
# heights it spans, rasterised once per scene, and a distance field over it.
BAND_RES = 0.01           # m: raster of the bands
BAND_SAMPLE = 0.004       # m between the samples laid on each collider triangle (< BAND_RES / 2)
BAND_BATCH_STEPS = 64     # a triangle crossing a band's end with at most this many sample steps per edge
                          # is sampled whole (vectorised) and its samples outside the band dropped
BAND_CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
                          "zenobench/base_bands")   # rasters per scene (StaticBands)


def _clip_z(tri, z0, z1):
    """The part of triangle ``tri`` (3, 3) with z in [z0, z1], as a convex polygon (list of points)."""
    poly = list(tri)
    for value, keep_below in ((z1, True), (z0, False)):
        out = []
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            pin = p[2] <= value if keep_below else p[2] >= value
            qin = q[2] <= value if keep_below else q[2] >= value
            if pin:
                out.append(p)
            if pin != qin:
                out.append(p + (value - p[2]) / (q[2] - p[2]) * (q - p))
        poly = out
        if len(poly) < 3:
            return []
    return poly


def _samples(tri, step):
    """Points on triangle ``tri`` (3, 3), at most ``step`` apart in xy along its edges."""
    e = tri[:, :2]
    n = max(1, int(math.ceil(max(np.linalg.norm(e[1] - e[0]), np.linalg.norm(e[2] - e[0]),
                                 np.linalg.norm(e[2] - e[1])) / step)))
    a, b = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
    keep = a + b <= n
    a, b = a[keep] / n, b[keep] / n
    return tri[0] + a[:, None] * (tri[1] - tri[0]) + b[:, None] * (tri[2] - tri[0])


def static_triangles(cols, body_pose):
    """World triangles (N, 3, 3) of the static colliders of ``cols`` (scene_geometry.Colliders):
    the house, its furniture, the support slabs, the windows, the carcasses of articulated
    furniture (posed by their body: ``body_pose(path)`` -> 4x4).  Loose objects and the moving
    parts are not static (WorldModel.base_only, moving_part_dist)."""
    out = []
    for c in cols.items:
        if c.owner != "static":
            continue
        T = c.local if c.body is None else body_pose(c.body) @ c.local
        if c.kind == "cuboid":
            h = np.asarray(c.dims, float) / 2
            V = np.array([[x, y, z] for x in (-h[0], h[0]) for y in (-h[1], h[1]) for z in (-h[2], h[2])])
            F = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                          [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
        else:
            V, F = np.asarray(c.vertices, float), np.asarray(c.faces, int)
        W = V @ T[:3, :3].T + T[:3, 3]
        out.append(W[F])
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


class StaticBands:
    """Distance (m) in xy from a point to the static colliders within each band of heights:
    ``low`` the chassis' (LOW_SPAN: the floor, the rugs (3.6 mm) and the floor slabs lie below it),
    ``column`` the column's (COLUMN_SPAN).  Every collider triangle is clipped to the band,
    sampled BAND_SAMPLE apart and rasterised at BAND_RES; a Euclidean distance transform of the
    free cells gives the distance.  ``dist`` takes off what the raster may add (BAND_RES * 1.5:
    the point's and the sample's offsets from their cell centres), so it never exceeds the true
    distance to the samples."""

    def __init__(self, tris, cache=None):
        """``cache``: a directory for the rasters, keyed by the triangles and the parameters (a scene
        takes ~12 s to rasterise, a cached one well under a second); None: no cache."""
        from scipy.ndimage import distance_transform_edt
        tris = np.asarray(tris, float).reshape(-1, 3, 3)
        self.bands = {"low": LOW_SPAN, "column": COLUMN_SPAN}
        xy = tris[..., :2].reshape(-1, 2)
        self.lo = (xy.min(0) if len(xy) else np.zeros(2)) - 1.0
        hi = (xy.max(0) if len(xy) else np.zeros(2)) + 1.0
        self.n = np.ceil((hi - self.lo) / BAND_RES).astype(int) + 1
        occ, path = None, None
        if cache is not None:
            import hashlib
            from pathlib import Path
            key = hashlib.sha1(np.ascontiguousarray(tris, np.float32).tobytes()
                               + repr((self.bands, BAND_RES, BAND_SAMPLE, BAND_BATCH_STEPS)).encode()).hexdigest()
            path = Path(cache) / f"{key}.npz"
            if path.exists():
                with np.load(path) as f:
                    occ = {k: np.unpackbits(f[k])[:int(np.prod(self.n))].reshape(self.n).astype(bool)
                           for k in self.bands}
        if occ is None:
            occ = self._rasterise(tris)
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_name(f"{key}.{os.getpid()}.tmp.npz")   # two sims may write it at once
                np.savez_compressed(tmp, **{k: np.packbits(v) for k, v in occ.items()})
                tmp.replace(path)
        self.dist_grid = {k: (distance_transform_edt(~v) * BAND_RES).astype(np.float32) for k, v in occ.items()}

    def _rasterise(self, tris):
        """{band: (n) bool}: the cells the band's colliders cover."""
        out = {}
        # sample counts from the edges' xy lengths: only the triangle's footprint matters
        steps = np.ceil(np.max(np.linalg.norm((tris - np.roll(tris, 1, axis=1))[..., :2], axis=2), axis=1) / BAND_SAMPLE)
        steps = np.maximum(steps, 1).astype(int) if len(tris) else np.zeros(0, int)
        for name, (z0, z1) in self.bands.items():
            occ = np.zeros(self.n, bool)
            mark = lambda P: occ.__setitem__(tuple(np.floor((P[..., :2].reshape(-1, 2) - self.lo) / BAND_RES)
                                                   .astype(int).T), True)
            zmin, zmax = tris[:, :, 2].min(1), tris[:, :, 2].max(1)
            touch = (zmax >= z0) & (zmin <= z1)
            inside = touch & (zmin >= z0) & (zmax <= z1)
            # in batches of one sample count: the triangles inside the band, and those crossing its
            # ends that are small (their samples outside the band dropped -- sampled BAND_RES apart in
            # z too, so a sliver in the band is not missed); the big ones (walls) clipped one by one
            n_all = np.where(inside, steps, np.maximum(steps, np.ceil((zmax - zmin) / BAND_RES).astype(int)))
            batch = inside | (touch & (n_all <= BAND_BATCH_STEPS))
            for n in np.unique(n_all[batch]):
                group = tris[batch & (n_all == n)]
                a, b = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
                keep = a + b <= n
                a, b = a[keep] / n, b[keep] / n
                for k in range(0, len(group), max(1, 200000 // len(a))):
                    g = group[k:k + max(1, 200000 // len(a))]
                    P = (g[:, None, 0] + a[None, :, None] * (g[:, None, 1] - g[:, None, 0])
                         + b[None, :, None] * (g[:, None, 2] - g[:, None, 0])).reshape(-1, 3)
                    mark(P[(P[:, 2] >= z0) & (P[:, 2] <= z1)])
            for tri in tris[touch & ~batch]:
                poly = _clip_z(tri, z0, z1)
                for k in range(1, len(poly) - 1):
                    mark(_samples(np.array([poly[0], poly[k], poly[k + 1]]), BAND_SAMPLE))
            out[name] = occ
        return out

    def dist(self, name, xy):
        """(N,) distance in xy from each point of ``xy`` (N, 2) to the band's colliders (0 outside the grid)."""
        xy = np.asarray(xy, float).reshape(-1, 2)
        ij = np.floor((xy - self.lo) / BAND_RES).astype(int)
        inside = np.all((ij >= 0) & (ij < self.n), axis=1)
        out = np.zeros(len(xy))
        out[inside] = self.dist_grid[name][ij[inside, 0], ij[inside, 1]] - 1.5 * BAND_RES
        return out


class WorldModel:
    """Obstacles from a scene annotation (see annotations.py)."""

    def __init__(self, ann, ignore=()):
        self.ann = ann
        self.boxes = []
        for obstacle in ann.obstacles:
            if obstacle["name"] in ignore:
                continue
            box = np.asarray(obstacle["aabb"], float)
            if obstacle["name"].startswith("kitchen_counter"):
                # The kitchen fixture's single AABB spans its counter and
                # upper cabinets. The worktop's clearance is the open band
                # between them; keeping one solid box makes every counter
                # grasp collision-infeasible even while the robot is clear.
                top = next((s for s in ann.supports if s.get("furniture") == obstacle["name"]), None)
                if top is not None and top.get("clearance", 1.0) > 0.25 and top["z"] + top["clearance"] < box[5]:
                    lower, upper = box.copy(), box.copy()
                    lower[5] = top["z"]
                    upper[2] = top["z"] + top["clearance"]
                    self.boxes.extend((lower, upper))
                    continue
            self.boxes.append(box)
        self.boxes.append(np.array([-50, -50, -1.0, 50, 50, 0.0]))      # floor
        self.B = np.array(self.boxes)
        self._near_key, self._near = None, None
        self.joint_q = {a["name"]: a["closed_q"] for a in ann.articulated}
        self.active = None       # articulation whose moving part the hand may touch
        self.part_margin = 0.06
        # free objects low enough to block the base column (toys, toy box,
        # basket on the floor), refreshed from the simulator by Rig.sync_world.
        # Base footprint and path planning only: the hand must still reach
        # into a toy box.
        self.base_only = np.zeros((0, 6))
        self.left_active = False
        self.right_kin = self.left_kin = None
        self.right_q = self.left_q = None
        # the static scene from its colliders (use_colliders); None: the annotation's boxes stand in
        # (offline: tools/build_tasks.py, benchmark/v6/layout.py, the unit tests)
        self.bands = None

    def use_colliders(self, cols, body_pose, cache=BAND_CACHE):
        """Check the base against the static colliders of ``cols`` (scene_geometry.Colliders; a
        carcass posed by ``body_pose(path)`` -> 4x4, its start pose) instead of the annotation's
        furniture and wall boxes."""
        self.bands = StaticBands(static_triangles(cols, body_pose), cache=cache)
        self.__dict__.pop("_circle_grids", None)

    def set_base_obstacles(self, boxes):
        self.base_only = np.asarray(boxes, float).reshape(-1, 6)

    def set_joint(self, name, q):
        self.joint_q[name] = float(q)

    def moving_part_dist(self, pts, span=None):
        """Distance to every articulated moving part (leaf/drawer) at its q.  ``pts``: (N, 3) points,
        or (N, 2) with ``span`` (z0, z1) -- each point is then the vertical segment between those
        heights, so one call covers a whole layer of the base instead of a sample height."""
        pts = np.asarray(pts, float)
        d = np.full(len(pts), np.inf)
        for a in self.ann.articulated:
            q = self.joint_q.get(a["name"], a["closed_q"])
            T = self.ann.part_pose(a, q)                      # 4x4 world pose of part frame
            if span is None:
                queries = [(pts, None)]
            elif abs(T[2, 2]) > 1 - 1e-6:
                # the frame stands upright (every door and drawer here): world z is its own z, so the
                # segment is one interval there and the part's xy distance does not depend on height
                z = sorted(math.copysign(1.0, T[2, 2]) * (np.asarray(span, float) - T[2, 3]))
                queries = [(np.c_[pts[:, :2], np.zeros(len(pts))], z)]
            else:                                             # a tilted frame: sample the span
                n = max(2, int(math.ceil((span[1] - span[0]) / PART_SAMPLE)) + 1)
                queries = [(np.c_[pts[:, :2], np.full(len(pts), zv)], None) for zv in np.linspace(*span, n)]
            for P, z in queries:
                local = (P - T[:3, 3]) @ T[:3, :3]
                for lo, hi in a.get("part_boxes") or [a["part_box"]]:
                    d = np.minimum(d, _aabb_dist(local, np.asarray(lo), np.asarray(hi), z))
        return d

    @contextmanager
    def temp_obstacles(self, boxes, fingers=False):
        """No-op: loose objects are real obstacles in cuRobo's world (motion.py)."""
        yield

    def near_boxes(self, xy, r=1.6):
        key = (round(float(xy[0]), 2), round(float(xy[1]), 2))
        if key != self._near_key:
            B = self.B
            dx = np.maximum(np.maximum(B[:, 0] - xy[0], xy[0] - B[:, 3]), 0)
            dy = np.maximum(np.maximum(B[:, 1] - xy[1], xy[1] - B[:, 4]), 0)
            self._near = B[np.hypot(dx, dy) < r]
            self._near_key = key
        return self._near

    def circles_clear(self, xy, r=BASE_HALF):
        """(N,) bool: a vertical cylinder of radius r (the bare chassis' inscribed one, without
        FOOTPRINT_MARGIN) at each xy is clear
        of what reaches into the chassis' heights (LOW_SPAN) and of the moving parts there: a
        relaxation of footprints_clear at every heading.  The static boxes come from a grid computed
        once (CIRCLE_RES; the cell nearest each xy), the loose objects and moving parts per call."""
        xy = np.atleast_2d(np.asarray(xy, float))
        if self.bands is not None:      # the chassis' disc vs the colliders in its heights
            ok = self.bands.dist("low", xy) > r
        else:
            ok = self._static_circle_grid(r)(xy)
        if len(self.base_only):
            # only the boxes in the chassis' heights: a box above it is the column's business, and
            # the column is a slim rectangle behind the centre, not a cylinder around it -- counting
            # one here would block a disc the footprint lets through at every heading, and this is
            # the relaxation the reachability field and the search's cut-off trust
            B = self.base_only[_spans_overlap(self.base_only, LOW_SPAN)]
            if len(B):
                ok &= self._circles_clear_boxes(xy, B, r)
        if self.ann.articulated:
            ok[ok] &= self.moving_part_dist(xy[ok], LOW_SPAN) > r
        return ok

    def _static_circle_grid(self, r):
        """xy -> bool lookup of circles_clear against the static boxes, rasterised once."""
        cache = self.__dict__.setdefault("_circle_grids", {})
        if r not in cache:
            B = self.B[(self.B[:, 2] > -0.5) & _spans_overlap(self.B, LOW_SPAN)]
            lo, hi = B[:, :2].min(0) - 1.0, B[:, 3:5].max(0) + 1.0
            n = np.ceil((hi - lo) / CIRCLE_RES).astype(int) + 1
            free = np.ones(n, bool)
            for b in B:
                i0, j0 = np.floor((b[:2] - r - lo) / CIRCLE_RES).astype(int)
                i1, j1 = np.ceil((b[3:5] + r - lo) / CIRCLE_RES).astype(int)
                i0, j0, i1, j1 = max(i0, 0), max(j0, 0), min(i1, n[0] - 1), min(j1, n[1] - 1)
                gx = lo[0] + np.arange(i0, i1 + 1) * CIRCLE_RES
                gy = lo[1] + np.arange(j0, j1 + 1) * CIRCLE_RES
                dx = np.maximum(np.maximum(b[0] - gx, gx - b[3]), 0)[:, None]
                dy = np.maximum(np.maximum(b[1] - gy, gy - b[4]), 0)[None, :]
                free[i0:i1 + 1, j0:j1 + 1] &= np.hypot(dx, dy) > r

            def lookup(xy):
                ij = np.round((xy - lo) / CIRCLE_RES).astype(int)
                inside = np.all((ij >= 0) & (ij < n), axis=1)
                out = np.zeros(len(xy), bool)
                out[inside] = free[ij[inside, 0], ij[inside, 1]]
                return out
            cache[r] = lookup
        return cache[r]

    @staticmethod
    def _circles_clear_boxes(xy, B, r):
        ok = np.ones(len(xy), bool)
        for k in range(0, len(B), 64):
            b = B[k:k + 64]
            dx = np.maximum(np.maximum(b[None, :, 0] - xy[:, :1], xy[:, :1] - b[None, :, 3]), 0)
            dy = np.maximum(np.maximum(b[None, :, 1] - xy[:, 1:], xy[:, 1:] - b[None, :, 4]), 0)
            ok &= np.all(np.hypot(dx, dy) > r, axis=1)
        return ok

    def footprints_clear(self, poses, margin=FOOTPRINT_MARGIN):
        """footprint_clear for many base poses ((N, 3): x, y, yaw rad) at once: (N,) bool."""
        poses = np.atleast_2d(np.asarray(poses, float))
        lo, hi = poses[:, :2].min(0), poses[:, :2].max(0)
        B = self._static_boxes()
        if len(self.base_only):
            B = np.vstack([B, self.base_only])
        r = REACH_R + margin                               # boxes beyond cannot touch
        B = B[(B[:, 3] > lo[0] - r) & (B[:, 0] < hi[0] + r) & (B[:, 4] > lo[1] - r) & (B[:, 1] < hi[1] + r)]
        return self._clear(poses, B, margin)

    def footprint_clear(self, x, y, yaw, margin=FOOTPRINT_MARGIN):
        """The base (the chassis and the column above it, _base_points) vs static boxes and parts,
        FOOTPRINT_MARGIN apart."""
        B = self.near_boxes((x, y)) if self.bands is None else self._static_boxes()
        B = B[B[:, 2] > -0.5]                    # not the floor
        if len(self.base_only):
            B = np.vstack([B, self.base_only])
        return bool(self._clear(np.array([[x, y, yaw]], float), B, margin)[0])

    def _static_boxes(self):
        """The annotation's boxes the base is checked against: all but the floor, none once the
        colliders stand in for them (use_colliders)."""
        return self.B[self.B[:, 2] > -0.5] if self.bands is None else np.zeros((0, 6))

    def _clear(self, poses, B, margin):
        """(N,) bool: the base at each pose clear of the static scene, the boxes B and the moving
        parts.  The chassis' points within LOW_CORNER + margin of a box whose heights reach into
        LOW_SPAN touch it, the column's points within margin of one reaching into COLUMN_SPAN."""
        x, y = poses[:, :1], poses[:, 1:2]
        c, s = np.cos(poses[:, 2])[:, None], np.sin(poses[:, 2])[:, None]
        L, C = _place(LOW_PTS, x, y, c, s), _place(COLUMN_PTS, x, y, c, s)
        ok = np.ones(len(poses), bool)
        reach = LOW_CORNER + margin
        if self.bands is not None:
            ok &= (self.bands.dist("low", L.reshape(-1, 2)) > reach).reshape(len(poses), -1).all(axis=1)
            ok &= (self.bands.dist("column", C.reshape(-1, 2)) > margin).reshape(len(poses), -1).all(axis=1)
        for k in range(0, len(B), 64):
            b = B[k:k + 64]
            dx = np.maximum(np.maximum(b[None, None, :, 0] - L[..., :1], L[..., :1] - b[None, None, :, 3]), 0)
            dy = np.maximum(np.maximum(b[None, None, :, 1] - L[..., 1:2], L[..., 1:2] - b[None, None, :, 4]), 0)
            low = _spans_overlap(b, LOW_SPAN)[None, None, :]
            ok &= ~((np.hypot(dx, dy) <= reach) & low).any(axis=(1, 2))
            inside = np.all((C[:, :, None, :] > b[None, None, :, :2] - margin) &
                            (C[:, :, None, :] < b[None, None, :, 3:5] + margin), axis=-1)
            ok &= ~(inside & _spans_overlap(b, COLUMN_SPAN)[None, None, :]).any(axis=(1, 2))
        if self.ann.articulated:
            ok &= (self.moving_part_dist(L.reshape(-1, 2), LOW_SPAN) > reach).reshape(len(poses), -1).all(axis=1)
            ok &= (self.moving_part_dist(C.reshape(-1, 2), COLUMN_SPAN) > margin).reshape(len(poses), -1).all(axis=1)
        return ok
