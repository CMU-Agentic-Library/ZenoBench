"""Visual prompting for a place: free spots on a support, numbered on the head camera image
(skill mark_spots, docs/skills/mark_spots.md).

The planner (a VLM) sees the numbered image and the spots' xy, and places with
``place(object, receptacle, hint_xy=<the chosen spot's xy>)``: every spot is one free_spots takes as
the hint itself (skills.hint_spot_free), so the place goes to the spot the planner chose when the
arm can get there.

Two parts:
* where the robot stands and looks so the whole support is in one head camera frame
  (view_coverage, best_view; ViewSupportPolicy drives there and aims the head);
* the spots: free_spots' spots, spread apart (spread), kept where the head camera sees them, drawn
  as numbered discs on the rendered frame, projected with the rendering camera's own intrinsics and the
  head chain's camera pose at the measured joints (camera_frame, head_camera_ros, project), so a disc
  sits where the spot is in the image.
"""

from __future__ import annotations

import math

import numpy as np

from .perception import _segment_blocked, head_camera_pose, look_angles

MAX_SPOTS = 6            # spots numbered on one image (chosen: a VLM tells six discs apart, 11-15)
MIN_SEP_M = 0.12         # m between two spots at least (and at least the object's footprint)
SPOT_CELL_M = 0.06       # free spots thinned to one per cell this wide before the checks (all of the support)
EDGE_FRAC = 0.04         # of the image width: a spot or support corner this close to the border is out
GRID_N = 5               # support samples per side for the coverage of a view (corners included)
VIEW_MARGIN = 0.92       # of the frustum's half-angle tangents a support sample must be within
AIM_FRACS = (0.5, 0.3, 0.7)   # the head aims at the support's centre, or nearer / farther along the view line
DISC_PX = 11             # disc radius at a 640 px wide image (scaled with the width)
DISC_RGB = (230, 30, 30)
CAMERA_MOUNT = 0.04       # m: FirstPersonCamera ahead of stereo_camera_link (runtime.make_rig OffsetCfg pos)


# ------------------------------------------------------------------ pure geometry
def spread(points, k=MAX_SPOTS, min_sep=MIN_SEP_M):
    """Up to ``k`` of ``points`` (best first) at least ``min_sep`` apart: the first, then each time the one
    farthest from those taken (farthest-point sampling), so the spots cover the support, not one corner."""
    pts = [np.asarray(p, float)[:2] for p in points]
    if not pts:
        return []
    taken = [0]
    d = np.array([np.linalg.norm(p - pts[0]) for p in pts])
    while len(taken) < k:
        i = int(np.argmax(d))
        if d[i] < min_sep:
            break
        taken.append(i)
        d = np.minimum(d, [np.linalg.norm(p - pts[i]) for p in pts])
    return [points[i] for i in taken]


def project(K, pos, R_ros, points):
    """Pixels (u, v) and depths of world ``points`` [N, 3] for a pinhole camera with intrinsics ``K`` at
    ``pos``, turned ``R_ros`` (camera to world, ROS convention: columns +x right, +y down, +z forward)."""
    P = np.atleast_2d(np.asarray(points, float))
    c = (P - np.asarray(pos, float)) @ np.asarray(R_ros, float)     # world -> camera: R^T (p - pos)
    z = c[:, 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        uv = (np.asarray(K, float) @ (c / z[:, None]).T).T[:, :2]
    return uv, z


def in_image(uv, depth, width, height, edge_px):
    return (depth > 0.05) & (uv[:, 0] >= edge_px) & (uv[:, 0] <= width - edge_px) & \
        (uv[:, 1] >= edge_px) & (uv[:, 1] <= height - edge_px)


def support_samples(s, n=GRID_N, lift=0.01):
    """``n`` x ``n`` points over the support's top (corners included), ``lift`` above it."""
    x0, y0, x1, y1 = s["aabb_xy"]
    return np.array([[x, y, s["z"] + lift] for x in np.linspace(x0, x1, n) for y in np.linspace(y0, y1, n)])


def in_frustum(cam, R, pts, fov_deg, margin=VIEW_MARGIN):
    """Which ``pts`` lie inside the head camera frustum (``R`` columns: forward, left, up), each half-angle's
    tangent shrunk by ``margin`` (a corner on the border is half cut off)."""
    d = (np.atleast_2d(pts) - cam) @ R
    th, tv = (math.tan(math.radians(f / 2)) * margin for f in fov_deg)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (d[:, 0] > 0.05) & (np.abs(d[:, 1] / d[:, 0]) <= th) & (np.abs(d[:, 2] / d[:, 0]) <= tv)


def draw_spots(image, uv, radius_uv=None, labels=None):
    """The frame with a numbered disc at each pixel of ``uv`` (and, when given, each spot's footprint as an
    outline: ``radius_uv`` a list of polygons [M, 2]).  uint8 H x W x 3 in, a new array out."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.fromarray(np.asarray(image, np.uint8)).convert("RGB")
    W = img.size[0]
    r = max(7, round(DISC_PX * W / 640))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=round(1.3 * r))      # a sized font: Pillow >= 10.1 (the image has 11.3)
    for i, (u, v) in enumerate(np.asarray(uv, float)):
        if radius_uv is not None and radius_uv[i] is not None and len(radius_uv[i]) > 2:
            poly = [tuple(map(float, p)) for p in radius_uv[i]]
            draw.line(poly + [poly[0]], fill=(255, 255, 255), width=max(1, r // 6))
        draw.ellipse([u - r, v - r, u + r, v + r], fill=DISC_RGB, outline=(255, 255, 255), width=max(2, r // 5))
        text = str(labels[i] if labels is not None else i + 1)
        draw.text((u, v), text, fill=(255, 255, 255), font=font, anchor="mm")
    return np.asarray(img)


# ------------------------------------------------------------------ the view of a support
def view_coverage(rig, s, base_pose, torso_waist):
    """(fraction of the support's samples in view, head yaw, head pitch) with the base at ``base_pose`` and the
    head aimed as look aims it at the best of AIM_FRACS along the line from the base to the support's centre:
    the head camera frustum (rig.head_fov_deg, VIEW_MARGIN) and no furniture box on the line of sight."""
    from .predicates import HEAD_HFOV_DEG, HEAD_VFOV_DEG
    pts = support_samples(s)
    x0, y0, x1, y1 = s["aabb_xy"]
    centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2, s["z"]])
    half = 0.5 * math.hypot(x1 - x0, y1 - y0)
    toward = centre[:2] - np.asarray(base_pose[:2], float)
    toward = toward / max(np.linalg.norm(toward), 1e-9)
    fov = getattr(rig, "head_fov_deg", (HEAD_HFOV_DEG, HEAD_VFOV_DEG))
    world = getattr(rig, "world", None)
    best = (-1.0, 0.0, 0.0)
    for f in AIM_FRACS:
        aim = centre.copy()
        aim[:2] += (2 * f - 1) * half * toward
        yaw, pitch = look_angles(rig, aim, base_pose=base_pose, torso_waist=torso_waist)
        cam, R = head_camera_pose(base_pose, dict(torso_waist, head_yaw_joint=yaw, head_pitch_joint=pitch))
        ok = in_frustum(cam, R, pts, fov)
        ok &= np.array([not _segment_blocked(world, cam, p) for p in pts])
        cov = float(ok.mean())
        if cov > best[0] + 1e-9:
            best = (cov, yaw, pitch)
    return best


def best_view(rig, s, poses, torso_waist):
    """(pose, coverage, yaw, pitch) of ``poses`` (best first): the first one that sees the whole support, else
    the one that sees the most of it (the earlier one on a tie).  None for no poses."""
    best = None
    for pose in poses:
        cov, yaw, pitch = view_coverage(rig, s, pose, torso_waist)
        if best is None or cov > best[1] + 1e-9:
            best = (tuple(pose), cov, yaw, pitch)
        if cov >= 1.0:
            break
    return best


# ------------------------------------------------------------------ the spots
def head_camera_ros(base_pose, q_named):
    """(position, R_ros) of the rendering head camera: the URDF head chain to stereo_camera_link
    (perception.head_camera_pose, columns forward, left, up) and the FirstPersonCamera's mount on it
    (CAMERA_MOUNT forward, looking along the link's +x: runtime.make_rig's OffsetCfg)."""
    p, R = head_camera_pose(base_pose, q_named)
    return p + R @ np.array([CAMERA_MOUNT, 0.0, 0.0]), np.column_stack([-R[:, 1], -R[:, 2], R[:, 0]])


def camera_frame(rig):
    """(image, K, pos, R_ros) of the head camera as rendered now; None without a head camera.  The intrinsics
    are the camera's own; the pose is the head chain at the measured joints (head_camera_ros): Isaac Lab's
    pose buffers are not kept with the image (CameraCfg.update_latest_camera_pose off), and the prim's USD
    pose they would read is the robot's spawn pose (T20 / T24 11-15: the same camera pose 6 m away for both)."""
    cam = getattr(rig, "first_person_camera", None)
    if cam is None:
        return None
    image = rig.get_first_person_image()
    q = {n: float(v) for n, v in zip(rig.kin.names[:2], rig.q()[:2])}
    q.update(rig.head_q() if hasattr(rig, "head_q") else {})
    pos, R_ros = head_camera_ros(rig.base_pose(), q)
    return image, cam.data.intrinsic_matrices[0].cpu().numpy(), pos, R_ros


def _object_boxes(rig, st, skip):
    out = []
    for n in rig.ann.objects:
        if n in skip:
            continue
        fp = rig.geo.footprint(n, st)
        low = float(rig.geo.resting(n, st)[2])
        top = 2 * float(rig.geo.centre(n, st)[2]) - low
        out.append(np.array([fp[0], fp[1], low, fp[2], fp[3], top]))
    return out


def _hidden_by(boxes, cam, p):
    """An object box on the segment from the camera to ``p`` (a spot is free, so none stands on it)."""
    if not boxes:
        return False
    world = type("W", (), {"B": np.vstack(boxes + [np.zeros(6)])})()
    return _segment_blocked(world, cam, p)


def thin(points, cell=SPOT_CELL_M):
    """The first of ``points`` (best first) in each ``cell`` x ``cell`` square: every part of the support keeps a
    spot (free_spots' best k sit in the corner nearest the robot: T20 11-15, the far half of a 2.5 m table
    had none), and the checks below run on hundreds, not thousands."""
    seen, out = set(), []
    for p in points:
        key = (math.floor(p[0] / cell), math.floor(p[1] / cell))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def mark_spots(rig, name, support):
    """The numbered spots for placing the held ``name`` on ``support`` as the head camera sees it now:
    {"spots": [[x, y], ...] (spot i is disc i + 1), "image": the drawn frame or None}.  Spots: free_spots'
    (any yaw, finger clearance first) over the whole support (thin), each one free_spots also takes as a hint
    itself, in the image (not within EDGE_FRAC of its border), not behind furniture or another object, spread
    (spread).  The robot's own arm and load are not checked: a spot drawn on the held object is left as it is
    (the user, 11-15)."""
    from . import skills
    from .perception import rig_head_pose
    s = rig.ann.support(support)
    st = rig.state()
    asset = rig.ann.asset_of(rig.ann.objects[name])
    size = asset["size"]
    counts = {}
    pool = skills.free_spots(rig, name, support, k=None)
    counts["free"] = len(pool)
    pool = thin([(round(x, 3), round(y, 3)) for x, y in pool])
    counts["thinned"] = len(pool)
    pool = [p for p in pool if skills.hint_spot_free(rig, name, s, p[0], p[1], st)]
    counts["as_hint"] = len(pool)
    z = s["z"] + 0.005
    cam_urdf = rig_head_pose(rig)[0]
    q = {n: float(v) for n, v in zip(rig.kin.names[:2], rig.q()[:2])}
    q.update(rig.head_q() if hasattr(rig, "head_q") else {})
    lens = head_camera_ros(rig.base_pose(), q)[0]          # the rays start at the lens
    boxes = _object_boxes(rig, st, {name})
    world = getattr(rig, "world", None)
    pool = [p for p in pool if not _segment_blocked(world, lens, np.array([p[0], p[1], z]))]
    counts["no_furniture"] = len(pool)
    pool = [p for p in pool if not _hidden_by(boxes, lens, np.array([p[0], p[1], z]))]
    counts["no_object"] = len(pool)
    frame = camera_frame(rig)
    cam_log = {}
    if frame is not None:
        image, K, pos, R_ros = frame
        H, W = image.shape[:2]
        uv, depth = project(K, pos, R_ros, [[x, y, z] for x, y in pool]) if pool else (np.zeros((0, 2)), np.zeros(0))
        keep = in_image(uv, depth, W, H, EDGE_FRAC * W)
        cam_log = {"K": np.round(K, 2).tolist(), "pos": np.round(pos, 3).tolist(), "R_ros": np.round(R_ros, 4).tolist(),
                   "cam_urdf": np.round(cam_urdf, 3).tolist(), "size": [W, H],
                   "uv_sample": np.round(uv[:3], 1).tolist(), "depth_sample": np.round(depth[:3], 2).tolist()}
        pool = [p for p, k in zip(pool, keep) if k]
    else:
        from .perception import project_to_head_camera
        pool = [p for p in pool if project_to_head_camera(rig, (p[0], p[1], z))[0]]
    counts["in_image"] = len(pool)
    if hasattr(rig, "log"):
        rig.log("mark_spots_filter", support=support, **counts, **cam_log)
    spots = spread(pool, MAX_SPOTS, max(MIN_SEP_M, max(size[0], size[1])))
    drawn = None
    if frame is not None and spots:
        uv, _ = project(K, pos, R_ros, [[x, y, z] for x, y in spots])
        r = 0.5 * max(size[0], size[1])
        ring = np.linspace(0, 2 * math.pi, 24, endpoint=False)
        outlines = [project(K, pos, R_ros, [[x + r * math.cos(a), y + r * math.sin(a), z] for a in ring])[0]
                    for x, y in spots]
        drawn = draw_spots(image, uv, outlines)
    return {"spots": [list(p) for p in spots], "image": drawn}
