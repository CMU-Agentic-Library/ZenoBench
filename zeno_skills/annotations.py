"""Scene / asset annotations = the GT a scripted policy (or an RL reward /
privileged observation) needs to operate every asset.

annotations/assets.json  (per asset type, object frame; tools/prepare_assets.py)
    tags, mass, size, origin_to_bottom_center, container profile, grasps:
      rim_pinch        round container: pinch the wall at the rim (azimuth, tilt)
      rim_pinch_rect   rectangular container rim
      top_pinch        vertical approach, fingers across the narrowest width
      edge_pinch_after_push  flat & wider than the gripper
      handle_pinch           annotated object-handle contact (consumed by PickCupHandlePolicy)
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
        # static appliances without joints (stove: burner disc + power button)
        self.appliances = d.get("appliances", [])
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

    def handle_pose(self, a, q, grasp="side", flip=False, tilt=0.0):
        """TCP position/orientation to hold the handle bar at joint value q.

        side: slide along the face (from the handle's free side), one finger
              between panel and bar -> pulling loads the bar via the finger's
              normal force, not friction.
        front: approach into the face, fingers across the bar.
        flip:  hook from the other end (drawers: both ends of the pull are free;
               doors: the hinge side is not).
        tilt:  side grasp yawed by this angle (rad) away from the panel: the
               wrist behind the TCP clears a panel that the bar sits close to.
        """
        h = a["handle"]
        M = self.motion(a, q)
        c = M[:3, :3] @ np.asarray(h["center"], float) + M[:3, 3]
        out = M[:3, :3] @ np.asarray(h["outward"], float)
        along = M[:3, :3] @ np.asarray(h["along"], float)       # toward the hinge / across bar
        if flip:
            along = -along
        if grasp == "side":
            # wide pulls (drawer plates, 13 cm): hook the near end, pads just
            # past its edge, so the hand behind the pads stays clear of the plate
            ext = float(np.abs(np.asarray(h["bar_size"], float)) @ np.abs(np.asarray(h["along"], float)))
            c = c - along * max(0.0, ext / 2 - 0.008)
            ct, st = math.cos(tilt), math.sin(tilt)
            approach, close = ct * along - st * out, ct * out + st * along
        else:
            approach, close = -out, along
        return c, gripper_rot(approach, close), approach

    # ------------------------------------------------------------ objects
    def asset_of(self, obj):
        return self.assets[obj["asset"]]

    def grasp_poses(self, obj, body_pos, body_quat_wxyz=None, kinds=None, extra_rotations=False):
        """World TCP grasp candidates for an object at its current pose.
        Returns list of dict(p, R, pre_open, kind, lift_dir).  With
        ``extra_rotations`` a square block also gets its 90-degree pinches
        (a pick fallback; the annotated pinches define grasp clearance)."""
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
            elif g["type"] == "top_pinch" and body_quat_wxyz is not None and _tilted(body_quat_wxyz):
                # lying on its side (a tipped bottle): pinch across it from above
                # at the centre's height, along its current long axis
                Rb = _quat_R(body_quat_wxyz)
                size = np.asarray(a["size"], float)
                centre = np.asarray(body_pos, float) + Rb @ (np.asarray(a["origin_to_bottom_center"], float)
                                                             + np.array([0.0, 0.0, 0.5 * size[2]]))
                long_ax = Rb[:, int(np.argmax(size))].copy()
                long_ax[2] = 0.0
                if np.linalg.norm(long_ax) < 1e-6:
                    long_ax = np.array([1.0, 0.0, 0.0])
                long_ax /= np.linalg.norm(long_ax)
                across = np.cross([0.0, 0.0, 1.0], long_ax)
                # the centre first, then 4 cm either way (a lying bottle between
                # neighbours may only be reachable off-centre)
                offs = list(g.get("along_offsets", [0.0]))
                offs += [o for o in (-0.04, 0.04) if all(abs(o - x) > 0.015 for x in offs)]
                for rank, d in enumerate(offs):
                    p = centre + long_ax * d
                    for sgn in (1.0, -1.0):
                        out.append({"kind": "top_pinch", "p": p, "R": gripper_rot([0, 0, -1.0], sgn * across),
                                    "pre_open": min(0.04, 0.5 * float(min(size[:2])) + 0.02),
                                    "along": float(d), "along_rank": rank, "lying": True})
                continue
            elif g["type"] == "top_pinch":
                off = rz(yaw) @ np.r_[g.get("offset_xy", [0.0, 0.0]), 0.0]
                # pads close across close_yaw; the object's long axis is perpendicular to it
                along = rz(yaw) @ np.array([-math.sin(g["close_yaw"]), math.cos(g["close_yaw"]), 0.0])
                sx_, sy_ = float(a["size"][0]), float(a["size"][1])
                square = extra_rotations and abs(sx_ - sy_) < 0.01 and max(sx_, sy_) < 0.075
                for rank, d in enumerate(g.get("along_offsets", [0.0])):
                    p = bottom + off + along * d + np.array([0, 0, g["height"]])
                    out += [dict(c, along=float(d), along_rank=rank)
                            for c in self._top_pinch_rotations(g, yaw, p, square=square)]
                continue
        return out

    @staticmethod
    def _top_pinch_rotations(g, yaw, p, square=False):
        # a round contact (knob, fruit, tomato) may be pinched across any
        # diameter; a square block across either pair of faces
        flips = (0.0, math.pi / 4, math.pi / 2, 3 * math.pi / 4, math.pi, -math.pi / 4, -math.pi / 2,
                 -3 * math.pi / 4) if g.get("round") else \
            (0.0, math.pi, math.pi / 2, -math.pi / 2) if square else (0.0, math.pi)
        out = []
        for flip in flips:
            c = g["close_yaw"] + yaw + flip
            # at least 2 cm of free opening per side: with ~1 cm a fingertip
            # landed on top of a 1.3 cm spoon handle (reach + yaw error)
            pre_open = max(float(g["pre_open"]), min(0.04, 0.5 * float(g.get("width", 0.0)) + 0.02))
            out.append({"kind": "top_pinch", "p": p,
                        "R": gripper_rot([0, 0, -1.0], [math.cos(c), math.sin(c), 0.0]),
                        "pre_open": pre_open})
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


def _quat_R(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def _tilted(q, deg=45.0):
    """Body up-axis more than ``deg`` from vertical."""
    return float(_quat_R(q)[2, 2]) < math.cos(math.radians(deg))
