"""Scene / asset annotations = the GT a scripted policy (or an RL reward /
privileged observation) needs to operate every asset.

annotations/assets.json  (per asset type, object frame; tools/prepare_assets.py)
    tags, mass, size, origin_to_bottom_center, container profile, grasps:
      rim_pinch        round container: pinch the wall at the rim (azimuth, tilt); a plate: its outer rim
                       from above and outside, the TCP above the rim's top (a negative depth), no pad
                       under the plate (tools/prepare_assets.plate_rim_pinch)
      rim_pinch_rect   rectangular container rim
      top_pinch        vertical approach, fingers across the narrowest width
      side_pinch       from the side (side_pinch_rot): a tall round object (every 30 degrees,
                       fingers across the diameter) or a box (from two opposite faces, fingers
                       across the other two), its approach ``tilt`` rad below level, its TCP
                       ``height`` above the bottom and at most ``depth`` inside the near face;
                       lying on its side, the top pinch across it instead
      thickness_pinch  flat & wider than the gripper: horizontal approach from outside one of its
                       four sides, the pads above and below it across its thickness, ``depth``
                       inside the side.  Below it is its support: only a side that overhangs the
                       support's edge leaves room for the lower pad (expose slides it there)
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


def side_pinch_rot(d, tilt):
    """The TCP frame of a side pinch from horizontal ``d`` (the hand comes in along -d), its approach
    dipped ``tilt`` rad below level, the fingers closing horizontally across d.  The closing sign
    puts the palm and the wrist camera above the TCP, not below: the hand clears the surface the
    object stands on with the TCP 43 mm up, against 73 mm the other way (tools/prepare_assets.py
    side_pinches)."""
    d = np.asarray(d, float)
    appr = -math.cos(tilt) * d - math.sin(tilt) * np.array([0.0, 0.0, 1.0])
    return gripper_rot(appr, -np.cross([0.0, 0.0, 1.0], d))


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
        lying = body_quat_wxyz is not None and _tilted(body_quat_wxyz)
        for g in a["grasps"]:
            if g["type"] == "side_pinch" and lying:
                if any(h["type"] == "top_pinch" for h in a["grasps"]):
                    continue                 # its top pinch gives the pinches across it
                # a tall bottle on its side: pinched across it from above, like a lying top pinch
                if kinds and "side_pinch" not in kinds and "top_pinch" not in kinds:
                    continue
                out += self._lying_pinches(g, a, body_pos, body_quat_wxyz)
                continue
            if kinds and g["type"] not in kinds:
                continue
            if g["type"] == "rim_pinch":
                # the body's centre (a mug's handle shifts the bbox) and, for an oval rim, the
                # radius along each azimuth
                centre = bottom + rz(yaw) @ np.array([*g.get("centre", (0.0, 0.0)), 0.0])
                for az in g["azimuths_deg"]:
                    d = np.array([math.cos(math.radians(az) + yaw), math.sin(math.radians(az) + yaw), 0.0])
                    r = g["radius"]
                    if g.get("radii"):
                        rx, ry = g["radii"]
                        ca, sa = math.cos(math.radians(az)), math.sin(math.radians(az))
                        r = rx * ry / math.hypot(ry * ca, rx * sa)
                    p = centre + r * d + np.array([0, 0, g["rim_height"] - g["depth"]])
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
            elif g["type"] == "thickness_pinch":
                if lying:
                    continue                 # not lying flat: no thickness to pinch across
                t = float(a["size"][2])
                for k in range(4):
                    d = rz(yaw) @ np.array([math.cos(k * math.pi / 2), math.sin(k * math.pi / 2), 0.0])
                    half = 0.5 * float(a["size"][k % 2])
                    p = bottom + d * (half - g["depth"]) + np.array([0.0, 0.0, 0.5 * t])
                    out.append({"kind": "thickness_pinch", "p": p, "R": gripper_rot(-d, [0.0, 0.0, 1.0]),
                                "pre_open": g["pre_open"], "side": k})
                continue
            elif g["type"] == "top_pinch" and lying:
                out += self._lying_pinches(g, a, body_pos, body_quat_wxyz)
                continue
            elif g["type"] == "side_pinch":
                axis = bottom + rz(yaw) @ np.r_[g.get("offset_xy", [0.0, 0.0]), 0.0]
                for az in g["azimuths_deg"]:
                    a_ = math.radians(az)
                    d = np.array([math.cos(a_ + yaw), math.sin(a_ + yaw), 0.0])
                    # the near face's distance from the axis: the radius, or the box's half extent along d
                    half = 0.5 * float(g["width"]) if g.get("round") else \
                        0.5 * (abs(math.cos(a_)) * float(a["size"][0]) + abs(math.sin(a_)) * float(a["size"][1]))
                    p = axis + d * max(0.0, half - g["depth"]) + np.array([0.0, 0.0, g["height"]])
                    out.append({"kind": "side_pinch", "p": p, "R": side_pinch_rot(d, g["tilt"]),
                                "pre_open": g["pre_open"], "azimuth": az, "tilt": g["tilt"]})
                continue
            elif g["type"] == "handle_pinch":
                if not kinds:
                    continue                 # only when asked for (every other caller sees what it saw before 9j)
                # 11-26 (zihan, bench GT): the handle pick became pick_job with kinds ("handle_pinch",) in HAND_PLAN 9j,
                # but no candidate was built for that kind ("no pinch grasp annotated" on every handle pick).  The
                # contact as PickCupHandlePolicy computed it before 9j: the annotated centre / approach / close
                # direction in the body's frame (its full rotation: a mug may stand tilted)
                B = _quat_R(body_quat_wxyz) if body_quat_wxyz is not None else rz(yaw)
                p = np.asarray(body_pos, float) + B @ np.asarray(g["center"], float)
                appr = B @ np.asarray(g["approach"], float)
                close = B @ np.asarray(g["close_dir"], float)
                out.append({"kind": "handle_pinch", "p": p, "R": gripper_rot(appr, close),
                            "pre_open": g["pre_open"]})
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
    def _lying_pinches(g, a, body_pos, body_quat_wxyz):
        """Lying on its side (a tipped bottle): pinch across it from above at the centre's
        height, along its current long axis."""
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
        out = []
        for rank, d in enumerate(offs):
            p = centre + long_ax * d
            for sgn in (1.0, -1.0):
                out.append({"kind": "top_pinch", "p": p, "R": gripper_rot([0, 0, -1.0], sgn * across),
                            "pre_open": min(0.04, 0.5 * float(min(size[:2])) + 0.02),
                            "along": float(d), "along_rank": rank, "lying": True})
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


def behind_door(ann, support=None, point=None):
    """The articulated (a door, a drawer front) that shuts in what stands on ``support`` (a support
    record) or at ``point`` (world xyz), else None.  One rule for every reader -- the pick and the place
    behind a door, the location and visibility attributes, the hidden predicate, the carry height:

    * a support inside it: category ``cabinet_inside`` (tools/annotate_scene.py: the shelves, bottoms
      and floors inside a carcass; its top is ``cabinet_top``, in the open), its ``furniture`` the
      articulated;
    * otherwise the point in its cavity (``cavity_aabb``: the microwave) or a refrigerator's body
      (``body_aabb``: the fridge has no cavity box) -- something standing on no annotated support.

    Whether it is open is each reader's question (the reach asks more than the view)."""
    if support is not None and support.get("category") == "cabinet_inside":
        f = support.get("furniture")
        a = next((x for x in ann.articulated if x["name"] == f), None)
        if a is not None:
            return a
    if point is None:
        return None
    for a in ann.articulated:
        box = a.get("cavity_aabb") or (a.get("body_aabb") if a.get("category") == "refrigerator" else None)
        if box is not None and all(box[i] < point[i] < box[i + 3] for i in range(3)):
            return a
    return None


def opening(a):
    """The unit horizontal direction out of articulated ``a``'s opening (its handle's outward normal,
    annotated), or None where it has none."""
    h = a.get("handle")
    if not isinstance(h, dict) or "outward" not in h:
        return None
    out = np.asarray(h["outward"], float)[:2]
    n = float(np.linalg.norm(out))
    return out / n if n > 1e-9 else None


def _quat_R(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def _tilted(q, deg=45.0):
    """Body up-axis more than ``deg`` from vertical."""
    return float(_quat_R(q)[2, 2]) < math.cos(math.radians(deg))
