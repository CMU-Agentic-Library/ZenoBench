"""Annotation boxes for the base: the footprint check and the navigation grid
(planner.py), plus the moving parts of articulated furniture posed at their
current joint value.

The arm does not use these boxes: arm IK and collision go to cuRobo against
the scene's real colliders (motion.py).  WorldModel also carries the joint
values of both arms (``right_q`` / ``left_q``) that a query on the other arm
keeps locked.
"""

from __future__ import annotations

from contextlib import contextmanager

import numpy as np

BASE_HALF = 0.26   # base column half size (0.244) + margin


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

    def footprint_clear(self, x, y, yaw, margin=0.03):
        """Base column (0.52 m square, 1.05 m tall) vs static boxes and parts."""
        c, s = np.cos(yaw), np.sin(yaw)
        g = np.linspace(-BASE_HALF, BASE_HALF, 6)
        pts = np.array([[x + c * u - s * v, y + s * u + c * v, z]
                        for u in g for v in g for z in (0.15, 0.6)])
        B = self.near_boxes((x, y))
        B = B[B[:, 2] > -0.5]                    # not the floor
        if len(self.base_only):
            B = np.vstack([B, self.base_only])
        P = pts[:, None, :]
        d = np.linalg.norm(np.maximum(np.maximum(B[None, :, :3] - margin - P, P - B[None, :, 3:] - margin), 0.0), axis=2)
        if len(B) and np.any(d == 0.0):
            return False
        return bool(np.all(self.moving_part_dist(pts) > margin))
