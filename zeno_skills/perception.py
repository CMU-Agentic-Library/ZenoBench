"""Head-camera geometry for Zeno Malo: exact URDF forward kinematics of
base -> torso lift -> waist -> head yaw -> head pitch -> stereo camera, and a
frustum + line-of-sight test against the annotated furniture boxes.

The first-person RGB camera (runtime.make_rig(first_person=True)) is mounted on
``stereo_camera_link`` and looks along that link's +X axis.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

import numpy as np

from .kinematics import URDF, _axis_rot
from .predicates import HEAD_HFOV_DEG, HEAD_VFOV_DEG, VIEW_RANGE_M

HEAD_JOINTS = ("head_yaw_joint", "head_pitch_joint")


def _head_chain():
    root = ET.parse(URDF).getroot()
    by_child = {j.find("child").get("link"): j for j in root.findall("joint")}
    out, link = [], "stereo_camera_link"
    while link in by_child:
        j = by_child[link]
        o = j.find("origin")
        xyz = np.array([float(v) for v in o.get("xyz").split()])
        rpy = [float(v) for v in (o.get("rpy") or "0 0 0").split()]
        ax = j.find("axis")
        axis = np.array([float(v) for v in ax.get("xyz").split()]) if ax is not None else None
        out.append((j.get("name"), j.get("type"), xyz, rpy, axis))
        link = j.find("parent").get("link")
    return out[::-1]


def _limits():
    root = ET.parse(URDF).getroot()
    joints = {j.get("name"): j for j in root.findall("joint")}
    return {n: (float(joints[n].find("limit").get("lower")), float(joints[n].find("limit").get("upper")))
            for n in HEAD_JOINTS}


CHAIN = _head_chain()
HEAD_LIMITS = _limits()


def head_camera_pose(base_xy_yaw, q_named):
    """World camera position and rotation (columns: forward, left, up).

    ``q_named`` maps joint names (torso_lift_joint, waist_pitch_joint,
    head_yaw_joint, head_pitch_joint) to positions; missing ones are 0."""
    from scipy.spatial.transform import Rotation
    x, y, yaw = base_xy_yaw
    p = np.array([x, y, 0.0])
    R = Rotation.from_euler("z", math.radians(yaw)).as_matrix()
    for name, typ, xyz, rpy, axis in CHAIN:
        p = p + R @ xyz
        if any(rpy):
            R = R @ Rotation.from_euler("xyz", rpy).as_matrix()
        if typ == "fixed" or axis is None:
            continue
        v = float(q_named.get(name, 0.0))
        if typ == "prismatic":
            p = p + R @ axis * v
        else:
            R = R @ _axis_rot(axis, v)
    return p, R


def rig_head_pose(rig):
    q = {n: float(v) for n, v in zip(rig.kin.names[:2], rig.q()[:2])}
    q.update(rig.head_q() if hasattr(rig, "head_q") else {})
    return head_camera_pose(rig.base_pose(), q)


def look_angles(rig, point, base_pose=None, torso_waist=None):
    """Head yaw/pitch that centre ``point`` in the image (clipped to limits)."""
    base_pose = base_pose or rig.base_pose()
    tw = torso_waist if torso_waist is not None else {n: float(v) for n, v in zip(rig.kin.names[:2], rig.q()[:2])}
    yaw_t, pitch_t = 0.0, 0.0
    for _ in range(4):      # the camera is offset from both axes: iterate
        cam, R = head_camera_pose(base_pose, dict(tw, head_yaw_joint=yaw_t, head_pitch_joint=pitch_t))
        d = R.T @ (np.asarray(point, float) - cam)
        yaw_t += math.atan2(d[1], d[0])
        pitch_t += -math.atan2(d[2], math.hypot(d[0], d[1]))
        yaw_t = min(max(yaw_t, HEAD_LIMITS["head_yaw_joint"][0]), HEAD_LIMITS["head_yaw_joint"][1])
        pitch_t = min(max(pitch_t, HEAD_LIMITS["head_pitch_joint"][0]), HEAD_LIMITS["head_pitch_joint"][1])
    return yaw_t, pitch_t


def _segment_blocked(world, a, b, exclude_boxes=()):
    if world is None:
        return False
    B = np.asarray(world.B[:-1] if hasattr(world, "B") else [], float)
    if B.size == 0:
        return False
    P = a[None, :] + np.linspace(0.05, 0.92, 24)[:, None] * (b - a)[None, :]
    inside = ((P[:, None, 0] > B[None, :, 0]) & (P[:, None, 0] < B[None, :, 3]) &
              (P[:, None, 1] > B[None, :, 1]) & (P[:, None, 1] < B[None, :, 4]) &
              (P[:, None, 2] > B[None, :, 2]) & (P[:, None, 2] < B[None, :, 5]))
    hit = inside.any(axis=0)
    for i in np.flatnonzero(hit):
        box = B[i]
        if any(np.all(np.abs(box - np.asarray(e, float)) < 1e-6) for e in exclude_boxes):
            continue
        # a target sitting on/inside this box: the last samples touch it legitimately
        if box[0] - 0.05 <= b[0] <= box[3] + 0.05 and box[1] - 0.05 <= b[1] <= box[4] + 0.05 \
                and box[2] - 0.05 <= b[2] <= box[5] + 0.08:
            continue
        return True
    return False


def project_to_head_camera(rig, point, exclude=None):
    """(visible, detail) for a world point in the current head camera."""
    cam, R = rig_head_pose(rig)
    d = R.T @ (np.asarray(point, float) - cam)
    dist = float(np.linalg.norm(d))
    if d[0] <= 0.05:
        return False, "behind the camera"
    h = math.degrees(math.atan2(d[1], d[0]))
    v = math.degrees(math.atan2(d[2], d[0]))
    if abs(h) > HEAD_HFOV_DEG / 2 or abs(v) > HEAD_VFOV_DEG / 2 or dist > VIEW_RANGE_M:
        return False, f"outside frustum (h {h:.0f}, v {v:.0f} deg, {dist:.1f} m)"
    if _segment_blocked(getattr(rig, "world", None), cam, np.asarray(point, float)):
        return False, f"line of sight blocked (h {h:.0f}, v {v:.0f} deg)"
    return True, f"h {h:.0f}, v {v:.0f} deg, {dist:.1f} m"


def pixel_of(rig, point, width=640, height=480):
    """Pinhole pixel (u, v) of a world point in the first-person image."""
    cam, R = rig_head_pose(rig)
    d = R.T @ (np.asarray(point, float) - cam)
    if d[0] <= 0:
        return None
    fx = width / (2 * math.tan(math.radians(HEAD_HFOV_DEG / 2)))
    return (width / 2 - fx * d[1] / d[0], height / 2 - fx * d[2] / d[0])
