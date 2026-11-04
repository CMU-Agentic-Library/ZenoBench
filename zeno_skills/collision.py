"""Annotation boxes for the base: the footprint check and the navigation grid
(planner.py), plus the moving parts of articulated furniture posed at their
current joint value.

The arm does not use these boxes: arm IK and collision go to cuRobo against
the scene's real colliders (motion.py).  WorldModel also carries the joint
values of both arms (``right_q`` / ``left_q``) that a query on the other arm
keeps locked.
"""

from __future__ import annotations

import math
from contextlib import contextmanager

import numpy as np

BASE_HALF = 0.26   # base column half size (0.244) + margin
FOOTPRINT_MARGIN = 0.03   # m the base column keeps from the boxes and moving parts, on top of BASE_HALF's
                          # (two margins stacked: inherited, 3ccd5e99; docs/COLLISION_PLAN.md §2)
FOOTPRINT_GRID = 6        # points per side the column's square is sampled at
COLUMN_Z = (0.15, 0.6)    # m: heights the column is sampled at (inherited, 3ccd5e99, unmeasured)
CIRCLE_RES = 0.025  # m: grid of circles_clear against the static boxes (half the base planner's lattice step)


def _aabb_dist(pts, lo, hi):
    return np.linalg.norm(np.maximum(np.maximum(lo - pts, pts - hi), 0.0), axis=1)


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

    def set_base_obstacles(self, boxes):
        self.base_only = np.asarray(boxes, float).reshape(-1, 6)

    def set_joint(self, name, q):
        self.joint_q[name] = float(q)

    def moving_part_dist(self, pts):
        """Distance to every articulated moving part (leaf/drawer) at its q."""
        d = np.full(len(pts), np.inf)
        for a in self.ann.articulated:
            q = self.joint_q.get(a["name"], a["closed_q"])
            T = self.ann.part_pose(a, q)                      # 4x4 world pose of part frame
            local = (pts - T[:3, 3]) @ T[:3, :3]
            for lo, hi in a.get("part_boxes") or [a["part_box"]]:
                d = np.minimum(d, _aabb_dist(local, np.asarray(lo), np.asarray(hi)))
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
        """(N,) bool: a vertical cylinder of radius r (the column's inscribed one) at each xy is clear
        of the boxes up to the column's height and of the moving parts: a relaxation of
        footprints_clear at every heading.  The static boxes come from a grid computed once
        (CIRCLE_RES; the cell nearest each xy), the loose objects and moving parts per call."""
        xy = np.atleast_2d(np.asarray(xy, float))
        ok = self._static_circle_grid(r)(xy)
        if len(self.base_only):
            ok &= self._circles_clear_boxes(xy, self.base_only, r)
        if self.ann.articulated:
            for z in COLUMN_Z:
                ok[ok] &= self.moving_part_dist(np.c_[xy[ok], np.full(int(ok.sum()), z)]) > r
        return ok

    def _static_circle_grid(self, r):
        """xy -> bool lookup of circles_clear against the static boxes, rasterised once."""
        cache = self.__dict__.setdefault("_circle_grids", {})
        if r not in cache:
            B = self.B[(self.B[:, 2] > -0.5) & (self.B[:, 2] < 1.05)]
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
        g = np.linspace(-BASE_HALF, BASE_HALF, FOOTPRINT_GRID)
        u, v, z = (a.ravel() for a in np.meshgrid(g, g, COLUMN_Z, indexing="ij"))
        c, s = np.cos(poses[:, 2])[:, None], np.sin(poses[:, 2])[:, None]
        P = np.stack([poses[:, :1] + c * u - s * v, poses[:, 1:2] + s * u + c * v,
                      np.broadcast_to(z, (len(poses), len(z)))], -1)            # (N, 72, 3)
        lo, hi = poses[:, :2].min(0), poses[:, :2].max(0)
        B = self.B[self.B[:, 2] > -0.5]                    # not the floor
        if len(self.base_only):
            B = np.vstack([B, self.base_only])
        r = BASE_HALF * math.sqrt(2) + margin           # the column's half diagonal: boxes beyond cannot touch
        B = B[(B[:, 3] > lo[0] - r) & (B[:, 0] < hi[0] + r) & (B[:, 4] > lo[1] - r) & (B[:, 1] < hi[1] + r)]
        ok = np.ones(len(poses), bool)
        for k in range(0, len(B), 64):
            b = B[k:k + 64]
            inside = np.all((P[:, :, None, :] > b[None, None, :, :3] - margin) &
                            (P[:, :, None, :] < b[None, None, :, 3:] + margin), axis=-1)
            ok &= ~inside.any(axis=(1, 2))
        if self.ann.articulated:
            ok &= (self.moving_part_dist(P.reshape(-1, 3)) > margin).reshape(len(poses), -1).all(axis=1)
        return ok

    def footprint_clear(self, x, y, yaw, margin=FOOTPRINT_MARGIN):
        """Base column (0.52 m square, 1.05 m tall) vs static boxes and parts."""
        c, s = np.cos(yaw), np.sin(yaw)
        g = np.linspace(-BASE_HALF, BASE_HALF, FOOTPRINT_GRID)
        pts = np.array([[x + c * u - s * v, y + s * u + c * v, z]
                        for u in g for v in g for z in COLUMN_Z])
        B = self.near_boxes((x, y))
        B = B[B[:, 2] > -0.5]                    # not the floor
        if len(self.base_only):
            B = np.vstack([B, self.base_only])
        P = pts[:, None, :]
        d = np.linalg.norm(np.maximum(np.maximum(B[None, :, :3] - margin - P, P - B[None, :, 3:] - margin), 0.0), axis=2)
        if len(B) and np.any(d == 0.0):
            return False
        return bool(np.all(self.moving_part_dist(pts) > margin))
