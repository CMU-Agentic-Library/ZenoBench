"""Visual prompting for a place: free spots on a support, numbered on the head camera image
(skill mark_spots, docs/skills/mark_spots.md).

The planner (a VLM) sees the numbered image and the spots' xy, and places with
``place(object, receptacle, hint_xy=<the chosen spot's xy>)``: every spot is one free_spots takes as
the hint itself (skills.hint_spot_free), so the place goes to the spot the planner chose when the
arm can get there.

Two parts:
* where the robot stands and looks so it sees the whole support clearly, in one or two head camera frames
  (support_views: the view that resolves the most of its top, then one for what is still unseen -- a long
  table's far half; view_resolution, resolution; ViewSupportPolicy drives to each, stands up, aims the head
  and keeps the frame);
* the spots: free spots in the nearest ring around each object on the support first (beside, pick_spots:
  what a request like "next to the mug" needs), then open space, kept where some view sees them, numbered
  once over all views and drawn as numbered discs on each frame they are in, projected with the rendering
  camera's own intrinsics and the head chain's camera pose at the measured joints (camera_frame,
  head_camera_ros, project), so a disc sits where the spot is in the image.  The thresholds are in
  tolerances (one source).
"""

from __future__ import annotations

import math

import numpy as np

from .perception import _segment_blocked, head_camera_pose, look_angles
from .tolerances import (MAX_SPOTS, SPOT_BESIDE_BAND, SPOT_BESIDE_MAX, SPOT_CELL, SPOT_EDGE_FRAC, SPOT_MIN_SEP,
                         SPOT_PX_SEP, VIEW_AIM_FRACS, VIEW_FRUSTUM_MARGIN, VIEW_GRID_N, VIEW_KEEP_FRAC, VIEW_MAX,
                         VIEW_MIN_GAIN, VIEW_RES_MIN)

DISC_PX = 7              # disc radius at a 640 px wide image (scaled with the width; 11 until 11-16: the user, smaller)
DISC_RGB = (230, 30, 30)
CAMERA_MOUNT = 0.04       # m: FirstPersonCamera ahead of stereo_camera_link (runtime.make_rig OffsetCfg pos)


# ------------------------------------------------------------------ pure geometry
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


def support_samples(s, n=VIEW_GRID_N, lift=0.01):
    """``n`` x ``n`` points over the support's top (corners included), ``lift`` above it."""
    x0, y0, x1, y1 = s["aabb_xy"]
    return np.array([[x, y, s["z"] + lift] for x in np.linspace(x0, x1, n) for y in np.linspace(y0, y1, n)])


def in_frustum(cam, R, pts, fov_deg, margin=VIEW_FRUSTUM_MARGIN):
    """Which ``pts`` lie inside the head camera frustum (``R`` columns: forward, left, up), each half-angle's
    tangent shrunk by ``margin`` (a corner on the border is half cut off)."""
    d = (np.atleast_2d(pts) - cam) @ R
    th, tv = (math.tan(math.radians(f / 2)) * margin for f in fov_deg)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (d[:, 0] > 0.05) & (np.abs(d[:, 1] / d[:, 0]) <= th) & (np.abs(d[:, 2] / d[:, 0]) <= tv)


def disc_radius(width):
    """Disc radius (px) on an image ``width`` px wide."""
    return max(5, round(DISC_PX * width / 640))


def draw_spots(image, uv, radius_uv=None, labels=None):
    """The frame with a numbered disc at each pixel of ``uv`` (and, when given, each spot's footprint as an
    outline: ``radius_uv`` a list of polygons [M, 2]).  uint8 H x W x 3 in, a new array out."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.fromarray(np.asarray(image, np.uint8)).convert("RGB")
    W = img.size[0]
    r = disc_radius(W)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=round(1.4 * r))      # a sized font: Pillow >= 10.1 (the image has 11.3)
    for i, (u, v) in enumerate(np.asarray(uv, float)):
        if radius_uv is not None and radius_uv[i] is not None and len(radius_uv[i]) > 2:
            poly = [tuple(map(float, p)) for p in radius_uv[i]]
            draw.line(poly + [poly[0]], fill=(255, 255, 255), width=1)
        draw.ellipse([u - r, v - r, u + r, v + r], fill=DISC_RGB, outline=(255, 255, 255), width=max(1, r // 5))
        text = str(labels[i] if labels is not None else i + 1)
        draw.text((u, v), text, fill=(255, 255, 255), font=font, anchor="mm")
    return np.asarray(img)


# ------------------------------------------------------------------ the view of a support
def resolution(cam, pts, hfov_deg):
    """How finely the camera at ``cam`` sees each point of a horizontal surface: the square root of the image
    area a small patch there covers, per metre of its side, in half image widths -- sqrt(sin elevation) /
    range / tan(half the horizontal field of view) (the patch's depth shrinks with the sine of the angle the
    line of sight meets the surface at, both sides with the range).  0 for a point at or above the camera."""
    d = np.atleast_2d(np.asarray(pts, float)) - cam
    rng = np.linalg.norm(d, axis=1)
    sin_el = np.clip(-d[:, 2] / np.maximum(rng, 1e-9), 0.0, 1.0)
    return np.sqrt(sin_el) / np.maximum(rng, 1e-9) / math.tan(math.radians(hfov_deg / 2))


def aim_points(s, base_pose):
    """Where the head may aim at a support from ``base_pose``: its centre, or nearer / farther along the line from
    the base to it by VIEW_AIM_FRACS of its half-diagonal."""
    x0, y0, x1, y1 = s["aabb_xy"]
    centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2, s["z"]])
    half = 0.5 * math.hypot(x1 - x0, y1 - y0)
    toward = centre[:2] - np.asarray(base_pose[:2], float)
    toward = toward / max(np.linalg.norm(toward), 1e-9)
    out = []
    for f in VIEW_AIM_FRACS:
        aim = centre.copy()
        aim[:2] += (2 * f - 1) * half * toward
        out.append(aim)
    return out


def view_resolution(rig, s, base_pose, torso_waist, aim):
    """(resolution of each of the support's samples -- 0 out of the frustum (rig.head_fov_deg,
    VIEW_FRUSTUM_MARGIN) or behind a furniture box --, head yaw, head pitch) with the base at ``base_pose``, the
    torso and waist at ``torso_waist`` and the head aimed as look aims it at the point ``aim``."""
    from .predicates import HEAD_HFOV_DEG, HEAD_VFOV_DEG
    pts = support_samples(s)
    fov = getattr(rig, "head_fov_deg", (HEAD_HFOV_DEG, HEAD_VFOV_DEG))
    world = getattr(rig, "world", None)
    yaw, pitch = look_angles(rig, aim, base_pose=base_pose, torso_waist=torso_waist)
    cam, R = head_camera_pose(base_pose, dict(torso_waist, head_yaw_joint=yaw, head_pitch_joint=pitch))
    ok = in_frustum(cam, R, pts, fov)
    ok &= np.array([not _segment_blocked(world, cam, p) for p in pts])
    return np.where(ok, resolution(cam, pts, fov[0]), 0.0), yaw, pitch


def support_views(rig, s, poses, torso_waist, here=None):
    """The views to take of a support: ([(pose, aim, seen), ...] in the order to take them, the fraction of its
    samples seen).  A sample is seen when a view resolves it at least VIEW_RES_MIN (view_resolution).  Greedy
    over the stand-offs ``poses`` (and ``here``, the pose the robot stands at, when given) each with its
    aim_points -- and, after a view, the centre of what is still unseen: the view that sees the most samples not
    seen yet, at most VIEW_MAX, a further one only when it adds VIEW_MIN_GAIN of them.  The first view is
    ``here``'s best when that sees VIEW_KEEP_FRAC of what the best one would (no drive for a little more).  A
    tie goes to the view that has more of the support in view, then the finer one.  [] for no poses."""
    pts = support_samples(s)
    n = len(pts)
    cands = []                                     # (pose, aim, resolution of each sample)

    def evaluate(pose, aims):
        for aim in aims:
            res, _, _ = view_resolution(rig, s, pose, torso_waist, aim)
            cands.append((tuple(pose), np.asarray(aim, float), res))
    if here is not None:
        evaluate(here, aim_points(s, here))
    for pose in poses:
        evaluate(pose, aim_points(s, pose))
    if not cands:
        return [], 0.0
    covered = np.zeros(n, bool)
    views = []
    while len(views) < VIEW_MAX:
        keys = [(int(((c[2] >= VIEW_RES_MIN) & ~covered).sum()), int((c[2] > 0).sum()), float(c[2].sum()))
                for c in cands]
        best = max(range(len(cands)), key=lambda i: keys[i])
        if not views and here is not None:
            mine = [i for i, c in enumerate(cands) if c[0] == tuple(here)]
            stay = max(mine, key=lambda i: keys[i])
            if keys[stay][0] >= VIEW_KEEP_FRAC * keys[best][0]:
                best = stay
        if views and keys[best][0] < VIEW_MIN_GAIN * n:
            break
        pose, aim, res = cands[best]
        views.append((pose, aim, res >= VIEW_RES_MIN))
        covered |= res >= VIEW_RES_MIN
        if covered.all():
            break
        # the next view may aim at what is still unseen
        rest = pts[~covered].mean(axis=0)
        rest[2] = s["z"]
        for p in {c[0] for c in cands}:
            evaluate(p, [rest])
    return views, float(covered.mean())


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


def thin(points, cell=SPOT_CELL):
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


def box_gap(a, b):
    """Gap between two xy boxes [x0, y0, x1, y1] (0 when they overlap): the goal predicates' (near_any,
    clear_of) measure."""
    dx = max(0.0, float(max(a[0], b[0]) - min(a[2], b[2])))
    dy = max(0.0, float(max(a[1], b[1]) - min(a[3], b[3])))
    return math.hypot(dx, dy)


def square(p, half):
    return [p[0] - half, p[1] - half, p[0] + half, p[1] + half]


def beside(points, boxes, half, band=SPOT_BESIDE_BAND, most=SPOT_BESIDE_MAX):
    """{object: [(point, clearance), ...] best first}: the ``points`` beside each object of ``boxes`` {name: xy box}
    -- its nearest ring: the held object put there (a square of half-side ``half``: its yaw after the place is not
    known) leaves at most ``band`` more gap to that object's box than the nearest point does, and at most
    ``most`` -- ranked by their clearance, the gap to the nearest OTHER object (a spot by the mug that is not
    also by the plate: what a request like "by the mug, not by the plates" tells apart), the larger first."""
    out = {}
    for n, b in boxes.items():
        gaps = [(p, box_gap(square(p, half), b)) for p in points]
        least = min((g for _, g in gaps), default=math.inf)
        rows = []
        for p, g in gaps:
            if g <= min(least + band, most):
                sq = square(p, half)
                rows.append((p, min((box_gap(sq, o) for m, o in boxes.items() if m != n), default=math.inf)))
        rows.sort(key=lambda r: -r[1])
        out[n] = rows
    return out


def pick_spots(beside_rows, centres, open_pool, ok, k=MAX_SPOTS, sep_beside=SPOT_MIN_SEP, sep_open=SPOT_MIN_SEP):
    """Up to ``k`` spots: one beside each object, then one on another side of each (at least 90 deg around its
    centre ``centres[name]`` from the first), then open space (``open_pool`` best first, farthest-point
    sampling).  Beside an object the clearest of its points (``beside_rows``, best first) that may still be
    taken; the first round goes to the object with the fewest such points left first (the nearer one, in
    ``beside_rows``' order, on a tie) -- a crowded seat is served before its roomy neighbours take its room (11-16
    T01: a spoon's spot left the bowl and the mug beside it none).  ``ok(p, taken, sep)``: whether ``p`` may join
    ``taken`` (``sep`` m from each, and apart on the image); a spot beside an object keeps ``sep_beside`` from
    the others, one in open space ``sep_open``.  Returns [(point, the object it is beside or None)]."""
    taken, out, first = [], [], {}

    def add(p, who):
        taken.append(p)
        out.append((p, who))
    left = list(beside_rows)
    while left and len(out) < k:
        free = {n: [p for p, _ in beside_rows[n] if ok(p, taken, sep_beside)] for n in left}
        left = [n for n in left if free[n]]
        if not left:
            break
        n = min(left, key=lambda m: len(free[m]))          # min() keeps the first of a tie: the nearer object
        add(free[n][0], n)
        first[n] = free[n][0]
        left.remove(n)
    for n, rows in beside_rows.items():
        if n not in first:
            continue
        c, f = np.asarray(centres[n], float), np.asarray(first[n], float) - centres[n]
        for p, _ in rows:
            v = np.asarray(p, float) - c
            if len(out) < k and float(v @ f) <= 0.0 and ok(p, taken, sep_beside):
                add(p, n)
                break
    pts = list(open_pool)
    while len(out) < k and pts:
        if taken:
            d = [min(math.dist(p, t) for t in taken) for p in pts]
            order = sorted(range(len(pts)), key=lambda i: -d[i])
        else:
            order = range(len(pts))
        nxt = next((i for i in order if ok(pts[i], taken, sep_open)), None)
        if nxt is None:
            break
        add(pts.pop(nxt), None)
    return out


def _on_support(rig, st, s, skip):
    """{name: footprint box} of the objects resting on the support ``s`` (the lowest point within 3 cm of its
    top and inside its outline: evaluator.support_under's test), but ``skip``."""
    x0, y0, x1, y1 = s["aabb_xy"]
    out = {}
    for n in rig.ann.objects:
        if n in skip:
            continue
        b = rig.geo.resting(n, st)
        if x0 - 0.01 <= b[0] <= x1 + 0.01 and y0 - 0.01 <= b[1] <= y1 + 0.01 and abs(float(b[2]) - s["z"]) <= 0.03:
            out[n] = [float(v) for v in rig.geo.footprint(n, st)[:4]]
    return out


def mark_spots(rig, name, support, frames=None):
    """The numbered spots for placing the held ``name`` on ``support`` in the head camera ``frames`` (the views
    view_support took: [{"image", "K", "pos", "R_ros"}]; None: the frame the camera renders now):
    {"spots": [[x, y], ...] (spot i is disc i + 1 on every image it is drawn on), "beside": [the object each is
    beside, or None], "images": [the drawn frame of each view]}.  Candidates: free_spots' (any yaw, finger
    clearance first) in the nearest ring around an object on the support (all of them: beside) or in open space
    (thinned), each one free_spots also takes as a hint itself, and in some view: in its image (not within
    SPOT_EDGE_FRAC of the border), behind no furniture or other object from that camera.  Chosen by pick_spots:
    one beside each object (the most crowded first), a second side, open space; a spot beside an object at least
    SPOT_MIN_SEP from the others, one in open space also the object's longer side, and SPOT_PX_SEP disc radii
    apart on every image both are on.  Numbered by the view that sees each
    finest (the first view's first), left to right on it; drawn on every image it is on.  The robot's own arm
    and load are not checked: a spot drawn on the held object is left as it is (the user, 11-15)."""
    from . import skills
    s = rig.ann.support(support)
    st = rig.state()
    asset = rig.ann.asset_of(rig.ann.objects[name])
    size = asset["size"]
    half = 0.5 * max(size[0], size[1])
    if frames is None:
        f = camera_frame(rig)
        frames = [] if f is None else [dict(zip(("image", "K", "pos", "R_ros"), f))]
    counts = {}
    pool = [(round(x, 3), round(y, 3)) for x, y in skills.free_spots(rig, name, support, k=None)]
    counts["free"] = len(pool)
    objs = _on_support(rig, st, s, {name})
    near = {p for rows in beside(pool, objs, half).values() for p, _ in rows}
    open_pool = thin(pool)
    pool = list(dict.fromkeys(open_pool + [p for p in pool if p in near]))     # (ordered, unique)
    counts["objects"], counts["beside"], counts["candidates"] = len(objs), len(near), len(pool)
    pool = [p for p in pool if skills.hint_spot_free(rig, name, s, p[0], p[1], st)]
    counts["as_hint"] = len(pool)
    z = s["z"] + 0.005
    boxes = _object_boxes(rig, st, {name})
    world = getattr(rig, "world", None)
    uv_of = [{} for _ in frames]                   # per view: spot -> pixel, the spots it sees
    res_of = [{} for _ in frames]
    for v, fr in enumerate(frames):
        H, W = fr["image"].shape[:2]
        lens = np.asarray(fr["pos"], float)        # the rays start at the lens
        seen = [p for p in pool if not _segment_blocked(world, lens, np.array([p[0], p[1], z]))
                and not _hidden_by(boxes, lens, np.array([p[0], p[1], z]))]
        if not seen:
            continue
        P = [[x, y, z] for x, y in seen]
        uv, depth = project(fr["K"], lens, fr["R_ros"], P)
        keep = in_image(uv, depth, W, H, SPOT_EDGE_FRAC * W)
        res = resolution(lens, P, 2 * math.degrees(math.atan(0.5 * W / float(np.asarray(fr["K"])[0][0]))))
        for i, p in enumerate(seen):
            if keep[i]:
                uv_of[v][p], res_of[v][p] = uv[i], float(res[i])
        counts[f"view{v + 1}"] = len(uv_of[v])
    if not frames:
        from .perception import project_to_head_camera
        visible = {p for p in pool if project_to_head_camera(rig, (p[0], p[1], z))[0]}
    else:
        visible = set().union(*uv_of)
    pool = [p for p in pool if p in visible]
    counts["in_view"] = len(pool)
    if hasattr(rig, "log"):
        rig.log("mark_spots_filter", support=support, views=len(frames), **counts,
                cams=[{"pos": np.round(fr["pos"], 3).tolist(), "size": list(fr["image"].shape[1::-1])} for fr in frames])
    r_px = [disc_radius(fr["image"].shape[1]) for fr in frames]

    def ok(p, taken, sep):
        for t in taken:
            if math.dist(p, t) < sep:
                return False
            for v, m in enumerate(uv_of):
                if p in m and t in m and float(np.linalg.norm(m[p] - m[t])) < SPOT_PX_SEP * r_px[v]:
                    return False
        return True
    base = np.asarray(rig.base_pose()[:2], float)
    centres = {n: np.array([(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]) for n, b in objs.items()}
    order = sorted(objs, key=lambda n: float(np.linalg.norm(centres[n] - base)))     # the nearest object first
    rows = beside(pool, {n: objs[n] for n in order}, half)
    seen = set(pool)
    chosen = pick_spots(rows, centres, [p for p in open_pool if p in seen], ok,
                        sep_open=max(SPOT_MIN_SEP, max(size[0], size[1])))
    if frames:
        def home(p):                               # the view that sees it finest (the first on a tie)
            return max((v for v in range(len(frames)) if p in res_of[v]), key=lambda v: (res_of[v][p], -v))
        chosen.sort(key=lambda c: (home(c[0]), float(uv_of[home(c[0])][c[0]][0])))
    spots = [c[0] for c in chosen]
    images = []
    ring = np.linspace(0, 2 * math.pi, 24, endpoint=False)
    for v, fr in enumerate(frames):
        mine = [i for i, p in enumerate(spots) if p in uv_of[v]]
        if not mine:
            images.append(np.asarray(fr["image"]).copy())
            continue
        uv = np.array([uv_of[v][spots[i]] for i in mine])
        outlines = [project(fr["K"], fr["pos"], fr["R_ros"],
                            [[spots[i][0] + half * math.cos(a), spots[i][1] + half * math.sin(a), z] for a in ring])[0]
                    for i in mine]
        images.append(draw_spots(fr["image"], uv, outlines, labels=[i + 1 for i in mine]))
    return {"spots": [list(p) for p in spots], "beside": [c[1] for c in chosen], "images": images}
