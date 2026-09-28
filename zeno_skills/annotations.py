"""Scene / asset annotations = the GT a scripted policy (or an RL reward /
privileged observation) needs to operate every asset.

annotations/assets.json  (per asset type, object frame; tools/prepare_assets.py)
    tags, mass, size, origin_to_bottom_center, container profile, grasps:
      rim_pinch        round container: pinch the wall at the rim (azimuth, tilt)
      rim_pinch_rect   rectangular container rim
      top_pinch        vertical approach, fingers across the narrowest width
      edge_pinch_after_push  flat & wider than the gripper
annotations/<scene>.json (per scene, world frame; tools/annotate_scene.py)
    rooms, obstacles (furniture AABBs), supports (horizontal surfaces),
    articulated (joint, pivot/axis, limits, moving-part box, handle frame),
    objects (prim, body, asset type, room, support it rests on)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from .kinematics import gripper_rot

ROOT = Path(__file__).resolve().parents[1]


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def axis_rot(axis, a):
    from scipy.spatial.transform import Rotation
    axis = np.asarray(axis, float)
    return Rotation.from_rotvec(axis / np.linalg.norm(axis) * a).as_matrix()


class SceneAnnotations:
    def __init__(self, path):
        self.path = Path(path)
        d = json.loads(self.path.read_text())
        self.data = d
        self.scene_usd = d["scene_usd"]
        self.rooms = d["rooms"]
        self.obstacles = d["obstacles"]
        self.supports = d["supports"]
        self.articulated = d["articulated"]
        self.objects = {o["name"]: o for o in d["objects"]}
        assets = json.loads((ROOT / "annotations/assets.json").read_text())
        self.assets = assets

    # ------------------------------------------------------------ articulated
    def art(self, name):
        for a in self.articulated:
            if a["name"] == name or a["joint"] == name or a["prim"] == name:
                return a
        raise KeyError(name)

    def motion(self, a, q):
        """4x4 rigid motion of the moving part from closed_q to q (world)."""
        T = np.eye(4)
        dq = float(q) - float(a["closed_q"])
        if a["type"] == "revolute":
            R = axis_rot(a["axis"], dq)
            p = np.asarray(a["pivot"], float)
            T[:3, :3] = R
            T[:3, 3] = p - R @ p
        else:
            T[:3, 3] = np.asarray(a["axis"], float) * dq
        return T

    def part_pose(self, a, q):
        return self.motion(a, q) @ np.asarray(a["part_frame"], float)

    def handle_pose(self, a, q, grasp="side"):
        """TCP position/orientation to hold the handle bar at joint value q.

        side: slide along the face (from the handle's free side), one finger
              between panel and bar -> pulling loads the bar via the finger's
              normal force, not friction.
        front: approach into the face, fingers across the bar.
        """
        h = a["handle"]
        M = self.motion(a, q)
        c = M[:3, :3] @ np.asarray(h["center"], float) + M[:3, 3]
        out = M[:3, :3] @ np.asarray(h["outward"], float)
        along = M[:3, :3] @ np.asarray(h["along"], float)       # toward the hinge / across bar
        if grasp == "side":
            approach, close = along, out
        else:
            approach, close = -out, along
        return c, gripper_rot(approach, close), approach

    # ------------------------------------------------------------ objects
    def asset_of(self, obj):
        return self.assets[obj["asset"]]

    def grasp_poses(self, obj, body_pos, body_quat_wxyz=None, kinds=None):
        """World TCP grasp candidates for an object at its current pose.
        Returns list of dict(p, R, pre_open, kind, lift_dir)."""
        a = self.asset_of(obj)
        yaw = 0.0
        if body_quat_wxyz is not None:
            w, x, y, z = body_quat_wxyz
            yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        # origin_to_bottom_center is in the object frame at authoring yaw 0
        off = rz(yaw) @ np.asarray(a["origin_to_bottom_center"], float)
        bottom = np.asarray(body_pos, float) + off
        out = []
        for g in a["grasps"]:
            if kinds and g["type"] not in kinds:
                continue
            if g["type"] == "rim_pinch":
                for az in g["azimuths_deg"]:
                    d = np.array([math.cos(math.radians(az) + yaw), math.sin(math.radians(az) + yaw), 0.0])
                    p = bottom + g["radius"] * d + np.array([0, 0, g["rim_height"] - g["depth"]])
                    for tilt in g["tilts"]:
                        appr = np.array([0, 0, -math.cos(tilt)]) - d * math.sin(tilt)
                        out.append({"kind": "rim_pinch", "p": p, "R": gripper_rot(appr, d),
                                    "pre_open": g["pre_open"], "azimuth": az, "tilt": tilt})
            elif g["type"] == "rim_pinch_rect":
                for sx, sy, hx in ((1, 0, g["half_x"]), (-1, 0, g["half_x"]), (0, 1, g["half_y"]), (0, -1, g["half_y"])):
                    d = rz(yaw) @ np.array([sx, sy, 0.0])
                    p = bottom + hx * d + np.array([0, 0, g["rim_height"] - g["depth"]])
                    for tilt in g["tilts"]:
                        appr = np.array([0, 0, -math.cos(tilt)]) - d * math.sin(tilt)
                        out.append({"kind": "rim_pinch_rect", "p": p, "R": gripper_rot(appr, d),
                                    "pre_open": g["pre_open"], "tilt": tilt})
            elif g["type"] == "top_pinch":
                off = rz(yaw) @ np.r_[g.get("offset_xy", [0.0, 0.0]), 0.0]
                p = bottom + off + np.array([0, 0, g["height"]])
                for flip in (0.0, math.pi):
                    c = g["close_yaw"] + yaw + flip
                    out.append({"kind": "top_pinch", "p": p,
                                "R": gripper_rot([0, 0, -1.0], [math.cos(c), math.sin(c), 0.0]),
                                "pre_open": g["pre_open"]})
        return out

    # ------------------------------------------------------------ supports
    def support(self, name):
        for s in self.supports:
            if s["name"] == name:
                return s
        raise KeyError(name)

    def place_poses(self, obj, support_name, xy, grasp):
        """TCP pose that puts ``obj`` (held with ``grasp`` = dict from
        grasp_poses, i.e. known offset tcp->bottom) with its bottom at xy on
        the support surface."""
        s = self.support(support_name)
        return np.array([xy[0], xy[1], s["z"]])
