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
    hfov, vfov = getattr(rig, "head_fov_deg", (HEAD_HFOV_DEG, HEAD_VFOV_DEG))
    if abs(h) > hfov / 2 or abs(v) > vfov / 2 or dist > VIEW_RANGE_M:
        return False, f"outside frustum (h {h:.0f}, v {v:.0f} deg, {dist:.1f} m)"
    if _segment_blocked(getattr(rig, "world", None), cam, np.asarray(point, float)):
        return False, f"line of sight blocked (h {h:.0f}, v {v:.0f} deg)"
    if getattr(rig, "occlusion", False) and exclude is not None:
        why = dynamic_occluder(rig, exclude, cam, np.asarray(point, float))
        if why:
            return False, f"occluded: {why}"
    return True, f"h {h:.0f}, v {v:.0f} deg, {dist:.1f} m"


def _open_fraction(rig, a):
    span = abs(a["open_q"] - a["closed_q"])
    return abs(rig.joint(a["name"]) - a["closed_q"]) / max(span, 1e-9)


def dynamic_occluder(rig, name, cam, point, st=None):
    """Why a visible-in-frustum object is still hidden (None if it is not):
    inside a closed cabinet / appliance, under a lid, below the rim of an
    opaque container seen from the side, or behind another object.  Only
    used when ``rig.occlusion`` is set (the observation-limited benchmark)."""
    ann = rig.ann
    if name not in ann.objects:
        return None
    st = st or rig.state()
    c = np.asarray(rig.geo.centre(name, st), float)
    held = {(rig.held or {}).get("name"), (getattr(rig, "left_held", None) or {}).get("name")} - {None}
    if name in held:
        return None
    # closed doors: cavity / body boxes and shelves behind a door
    sup = rig.geo.support_under(name, st)
    for a in ann.articulated:
        box = a.get("cavity_aabb") or (a.get("body_aabb") if a.get("category") == "refrigerator" else None)
        inside = box is not None and all(box[i] < c[i] < box[i + 3] for i in range(3))
        inside = inside or (sup is not None and sup.get("furniture") == a["name"]
                            and sup.get("category") == "cabinet_inside")
        if inside and _open_fraction(rig, a) < 0.3:
            return f"inside closed {a['name']}"
    from .predicates import lid_on, lids
    for other, o in ann.objects.items():
        if other == name or other in held:
            continue
        asset = ann.asset_of(o)
        if asset.get("container") and rig.geo.inside(name, other, st)[0]:
            if any(lid_on(rig, other, l, st)[0] for l in lids(rig) if l != other):
                return f"under the lid of {other}"
            rim = float(rig.geo.bottom(other, st)[2]) + float(asset["container"].get("rim_height", asset["size"][2]))
            if cam[2] < rim + 0.02:
                return f"below the rim of {other}"
    # other objects on the ray (their axis-aligned boxes): hidden only when
    # every sample point of the target (centre, top, four sides) is blocked
    boxes = []
    for other, o in ann.objects.items():
        if other == name or other in held:
            continue
        asset = ann.asset_of(o)
        if asset.get("container") and rig.geo.inside(name, other, st)[0]:
            continue                      # seen over the rim (checked above)
        fp = rig.geo.footprint(other, st)
        z0 = float(rig.geo.bottom(other, st)[2])
        lo = np.array([fp[0], fp[1], z0])
        hi = np.array([fp[2], fp[3], z0 + float(asset["size"][2])])
        if np.all(c > lo - 0.01) and np.all(c < hi + 0.01):
            continue                      # the target rests on / in this box
        boxes.append((other, lo, hi))
    if not boxes:
        return None
    fp = rig.geo.footprint(name, st)
    b = rig.geo.bottom(name, st)
    top = float(b[2]) + float(ann.asset_of(ann.objects[name])["size"][2])
    mx, my = 0.35 * (fp[2] - fp[0]), 0.35 * (fp[3] - fp[1])
    pts = [c, np.array([c[0], c[1], top - 0.005])] + \
          [np.array([c[0] + sx * mx, c[1] + sy * my, c[2]]) for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    blocker = None
    for p in pts:
        d = p - cam
        hit = None
        for other, lo, hi in boxes:
            # slab test on the segment, ignoring the last 4 cm before the target
            t0, t1 = 0.0, 1.0 - 0.04 / max(float(np.linalg.norm(d)), 1e-6)
            for i in range(3):
                if abs(d[i]) < 1e-9:
                    if cam[i] < lo[i] or cam[i] > hi[i]:
                        t0, t1 = 1.0, 0.0
                        break
                    continue
                ta, tb = (lo[i] - cam[i]) / d[i], (hi[i] - cam[i]) / d[i]
                t0, t1 = max(t0, min(ta, tb)), min(t1, max(ta, tb))
            if t0 < t1:
                hit = other
                break
        if hit is None:
            return None
        blocker = blocker or hit
    return f"behind {blocker}"
