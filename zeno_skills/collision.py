"""Sphere model of Zeno Malo + a world model built from scene annotations.

The world is a list of static AABBs (furniture, walls from the annotation) plus
the moving parts of articulated furniture, posed at their *current* joint value.
``WorldModel.clearance(kin, q)`` is the signed distance between the robot
spheres and the world (negative = penetration); ``kin.scene = world`` makes the
IK in kinematics.py collision-aware.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.transform import Rotation

from .kinematics import _axis_rot

# Sphere model per link frame (centre xyz, radius), from the collision mesh
# bounds of zeno_malo_edu.isaac.urdf.  Right-only plans keep the default
# folded-left envelope in the torso frame; active two-arm plans also evaluate
# moving left-arm spheres and inter-arm clearance.
SPHERES = {
    "torso_link": [((0, 0, 0.03), 0.12), ((0, 0, 0.13), 0.12), ((0, 0, 0.23), 0.12),
                   ((0.01, 0, 0.42), 0.10),
                   ((0.0, 0.19, 0.24), 0.05), ((0.02, 0.23, 0.12), 0.05), ((0.05, 0.25, 0.04), 0.05),
                   ((0.10, 0.25, 0.12), 0.045), ((0.15, 0.25, 0.22), 0.045)],
    "right_arm_link_1": [((0, -0.03, 0), 0.05), ((0, -0.09, 0), 0.05)],
    "right_arm_link_2": [((0.02, 0, -0.02), 0.05)],
    "right_arm_link_3": [((0.01, 0, -0.04), 0.045), ((0.01, 0, -0.10), 0.045), ((0.01, 0, -0.16), 0.045)],
    "right_arm_link_4": [((-0.01, 0.025, -0.015), 0.05)],
    "right_arm_link_5": [((0, 0, -0.03), 0.04), ((0, 0, -0.08), 0.04), ((0, 0, -0.13), 0.04)],
    "right_arm_link_6": [((-0.025, 0, 0), 0.035)],
    "right_arm_link_7": [((0, -0.006, -0.02), 0.03)],
    "right_gripper_link": [((0.018, 0, -0.02), 0.045), ((0.018, 0, -0.06), 0.045)],
}
LEFT_SPHERES = {"torso_link": SPHERES["torso_link"][:4]}
for _link, _parts in SPHERES.items():
    if _link.startswith("right_"):
        LEFT_SPHERES[_link.replace("right_", "left_", 1)] = [
            ((c[0], -c[1], c[2]), radius) for c, radius in _parts]
HAND_LINKS = ("right_gripper_link", "right_arm_link_7", "right_arm_link_6", "right_arm_link_5",
              "left_gripper_link", "left_arm_link_7", "left_arm_link_6", "left_arm_link_5")
FINGER_SPHERES = [((0, 0, -0.10), 0.03), ((0, 0, -0.13), 0.025)]
BASE_HALF = 0.26   # base column half size (0.244) + margin


def link_frames(kin, q):
    """World pose (p, R) of every link on the right-arm chain."""
    p, R = kin.base_p.copy(), kin.base_R.copy()
    out, i = {}, 0
    for (name, typ, xyz, axis), child in zip(kin.chain, kin.children):
        p = p + R @ xyz
        if typ == "prismatic":
            p = p + (R @ axis) * q[i]
            i += 1
        elif typ != "fixed":
            R = R @ _axis_rot(axis, q[i])
            i += 1
        out[child] = (p.copy(), R.copy())
    return out


def robot_spheres(kin, q, hand_is_finger=False, with_link=False):
    fr = link_frames(kin, np.asarray(q, float))
    pts, rad, fin, links = [], [], [], []
    side = getattr(kin, "side", "right")
    spheres = LEFT_SPHERES if side == "left" else SPHERES
    for link, sph in spheres.items():
        p, R = fr[link]
        for c, r in sph:
            pts.append(p + R @ np.asarray(c, float))
            rad.append(r)
            fin.append(False)
            links.append(link)
    p, R = fr[f"{side}_gripper_link"]
    for c, r in FINGER_SPHERES:
        pts.append(p + R @ np.asarray(c, float))
        rad.append(r)
        fin.append(True)
        links.append("finger")
    if with_link:
        return np.array(pts), np.array(rad), np.array(fin), np.array(links)
    return np.array(pts), np.array(rad), np.array(fin)


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
            if obstacle["name"].startswith("KitchenSpaceFactory_"):
                # The kitchen fixture's single AABB spans its counter and
                # upper cabinets. Its support levels expose an open band
                # between them; keeping one solid box makes every counter
                # grasp collision-infeasible even while the robot is clear.
                levels = sorted({float(s["z"]) for s in ann.supports
                                 if s.get("furniture") == obstacle["name"]})
                if len(levels) >= 2 and levels[1] - levels[0] > 0.25:
                    lower, upper = box.copy(), box.copy()
                    lower[5] = levels[0]
                    upper[2] = levels[1]
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

    def near_boxes(self, xy, r=1.6):
        key = (round(float(xy[0]), 2), round(float(xy[1]), 2))
        if key != self._near_key:
            B = self.B
            dx = np.maximum(np.maximum(B[:, 0] - xy[0], xy[0] - B[:, 3]), 0)
            dy = np.maximum(np.maximum(B[:, 1] - xy[1], xy[1] - B[:, 4]), 0)
            self._near = B[np.hypot(dx, dy) < r]
            self._near_key = key
        return self._near

    def clearance(self, kin, q, hand_touches_part=False, ignore_fingers=False, **_):
        pts, rad, fin, links = robot_spheres(kin, q, hand_is_finger=hand_touches_part, with_link=True)
        keep = ~fin if ignore_fingers else np.ones(len(pts), bool)
        B = self.near_boxes(kin.base_p[:2])
        P = pts[keep][:, None, :]
        d = np.linalg.norm(np.maximum(np.maximum(B[None, :, :3] - P, P - B[None, :, 3:]), 0.0), axis=2)
        c = float((d - rad[keep][:, None]).min()) if len(B) else np.inf
        m = ~fin
        if m.any():
            # when the hand works a part: gripper/fingers may touch it, the
            # wrist must not intersect it, and the rest of the body keeps a
            # real gap (a torso/left arm resting on a door blocks it)
            extra = np.zeros(m.sum())
            if hand_touches_part:
                extra = np.where(np.isin(links[m], HAND_LINKS), 0.0, self.part_margin)
            c = min(c, float((self.moving_part_dist(pts[m]) - rad[m] - extra).min()))
        if self.left_active and self.right_kin is not None and self.left_kin is not None:
            side = getattr(kin, "side", "right")
            other_kin = self.right_kin if side == "left" else self.left_kin
            other_q = self.right_q if side == "left" else self.left_q
            if other_q is not None:
                op, orad, _, olinks = robot_spheres(other_kin, other_q, with_link=True)
                own = np.array(["arm_link_" in link or "gripper_link" in link for link in links])
                other = np.array(["arm_link_" in link or "gripper_link" in link for link in olinks])
                if own.any() and other.any():
                    dd = np.linalg.norm(pts[own, None, :]-op[None, other, :], axis=2)
                    c = min(c, float((dd-rad[own, None]-orad[None, other]).min()))
        return c

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
