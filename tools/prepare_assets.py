"""Scale EmbodiedGen V2 text-to-3D assets to real size, convert them to USD and
write asset-level manipulation annotations (annotations/assets.json).

The text3d pipeline sizes assets with an LLM; without API access every asset
comes out 1 m tall and 1 kg, so sizes/masses come from SPECS below.

    cd zeno-house   # repository root
    ${ISAACLAB_PYTHON:-python} tools/prepare_assets.py [--convert]
"""

from __future__ import annotations

import argparse
import json
import os
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# EmbodiedGen checkout (only needed for --convert, which uses its URDF->USD converter)
REPO = Path(os.environ.get("EMBODIEDGEN_ROOT", ROOT.parent / "EmbodiedGen"))
GEN = ROOT / "assets" / "asset3d"
USD_OUT = ROOT / "usd" / "assets"
ANN = ROOT / "annotations" / "assets.json"

# name: (longest extent m, mass kg, tags, collider, source)
#   collider: solid | round_container | rect_container
SPECS = {
    # breakfast set (already real-scale from the earlier V2 run)
    "breakfast_plate": (None, 0.35, ["dish", "plate", "flat"], "solid", None),
    "breakfast_bowl": (None, 0.20, ["dish", "bowl", "container"], "round_container", None),
    "breakfast_cup": (None, 0.03, ["dish", "cup", "drinking_container", "container"], "round_container", None),
    "breakfast_mug": (None, 0.25, ["dish", "mug", "drinking_container", "container"], "round_container", None),
    "breakfast_spoon": (None, 0.04, ["utensil", "spoon"], "solid", None),
    "cereal_box": (None, 0.50, ["food", "box", "clutter"], "solid", None),
    # new assets (EmbodiedGen V2 text3d-cli, tools/../assets/gen_v2_assets.sh)
    "apple": (0.070, 0.16, ["fruit", "apple"], "solid", None),
    "banana": (0.190, 0.12, ["fruit", "banana"], "solid", None),
    "orange": (0.068, 0.15, ["fruit", "orange"], "solid", None),
    "fruit_basket": (0.300, 0.50, ["container", "basket", "fruit_container"], "round_container", None),
    "serving_tray": (0.420, 0.80, ["container", "tray", "fruit_container"], "rect_container", None),
    "notebook": (0.210, 0.25, ["stationery", "notebook", "flat"], "solid", None),
    "pen": (0.140, 0.015, ["stationery", "pen", "writing_tool"], "solid", None),
    "pencil": (0.180, 0.010, ["stationery", "pencil", "writing_tool"], "solid", None),
    "book_red": (0.240, 0.55, ["book", "flat"], "solid", None),
    "book_green": (0.220, 0.45, ["book", "flat"], "solid", None),
    "book_blue": (0.200, 0.30, ["book", "flat"], "solid", None),
    "toy_car": (0.120, 0.15, ["toy", "toy_car"], "solid", None),
    "teddy_bear": (0.160, 0.15, ["toy", "plush"], "solid", None),   # small plush: crown pinch on the head
    "toy_block": (0.040, 0.03, ["toy", "block"], "solid", None),     # 4 cm like the wooden blocks
    "rubber_duck": (0.090, 0.05, ["toy", "duck"], "solid", None),
    "toy_box": (0.500, 3.00, ["container", "toy_box", "storage"], "rect_container", None),
    "storage_basket": (0.380, 0.60, ["container", "basket", "storage"], "rect_container", None),
}
# rest these with the thinnest axis vertical and the longest along x
SIDE_PINCH_MIN_H = 0.12    # round solids taller than this are pinched from the side
LAY_FLAT = {"notebook", "pen", "pencil", "book_red", "book_green", "book_blue", "breakfast_spoon", "banana"}
# lay-flat assets whose generated mesh is too thick: resting height (m); the
# footprint keeps the uniform scale from SPECS
THICKNESS = {"book_red": 0.040}

# the open hand's palm over a top pinch: the right gripper's palm and camera collision spheres
# (the cuRobo model the planner checks the grasp pose with) must stay this far above the object
# (rig.LEAVE_GAP: closer, the robot still touches it)
ROBOT_YML = ROOT / "robot_sources" / "curobo" / "zeno_malo.yml"
ROBOT_URDF = ROOT / "robot_sources" / "zeno_malo_description-master" / "zeno_malo_mobile.urdf"
PALM_LINKS = ("right_gripper_link", "right_gripper_camera_link")

# containers whose mesh has a carry handle above the body: fraction of the
# total height that is the body (walls stop there)
BODY_FRACTION = {"fruit_basket": 0.58}

# your own assets: assets/custom_assets.json (README "Add your own assets")
#   {"soda_can": {"size": 0.12, "mass": 0.35, "tags": ["can"], "collider": "solid",
#                 "lay_flat": false, "urdf": "assets/asset3d/soda_can/result/soda_can.urdf"}}
CUSTOM = ROOT / "assets" / "custom_assets.json"
CUSTOM_RECORDS = json.loads(CUSTOM.read_text()) if CUSTOM.exists() else {}
for _n, _c in CUSTOM_RECORDS.items():
    if _n.startswith("_"):
        continue
    SPECS[_n] = (_c["size"], _c["mass"], _c.get("tags", []), _c.get("collider", "solid"),
                 ROOT / _c["urdf"] if _c.get("urdf") else None)
    if _c.get("lay_flat"):
        LAY_FLAT.add(_n)
    if "body_fraction" in _c:
        BODY_FRACTION[_n] = _c["body_fraction"]
GRIPPER_GAP = 0.080          # Zeno Malo pinch gripper: 2 x 0.04 m
# thickness pinch: the TCP this far inside the pinched side.  The old edge pinch took 2-4.5 cm by
# the overhang; the planner's fingertip reaches 2.4 cm past the TCP, so a side overhanging its
# support by about 5.4 cm (EDGE_MIN_OVERHANG 5.5 cm, what expose pushes to) leaves the lower pad clear
THICKNESS_PINCH_DEPTH = 0.025
PINCH_MAX = 0.068            # leave >= 6 mm clearance per side
CROWN = 0.05                 # crown pinch: top slab the pads straddle


def source_urdf(name):
    spec = SPECS[name]
    return spec[4] or GEN / name / "result" / f"{name}.urdf"


def flat_rotation(mesh):
    """Rotation that puts the mesh's thinnest principal axis on z and the
    longest on x (oriented bounding box)."""
    T, ext = trimesh.bounds.oriented_bounds(mesh)
    R = T[:3, :3]                          # world -> obb
    order = np.argsort(ext)[::-1]          # longest, middle, thinnest
    P = np.zeros((3, 3))
    for i, k in enumerate(order):
        P[i, k] = 1.0
    Rf = P @ R
    if np.linalg.det(Rf) < 0:
        Rf[1] *= -1
    return Rf


def mesh_zup(urdf):
    """Visual mesh in the URDF link frame (z up), with the URDF scale."""
    link = ET.parse(urdf).getroot().find("link")
    vis = link.find("visual")
    m = vis.find("geometry").find("mesh")
    mesh = trimesh.load(urdf.parent / m.get("filename"), force="mesh")
    s = [float(v) for v in (m.get("scale") or "1 1 1").split()]
    mesh.apply_scale(s)
    rpy = [float(v) for v in vis.find("origin").get("rpy").split()]
    from scipy.spatial.transform import Rotation
    T = np.eye(4)
    T[:3, :3] = Rotation.from_euler("xyz", rpy).as_matrix()
    mesh.apply_transform(T)
    return mesh


ELLIPSE_MIN = 1.06           # body outline with axis ratio above this: an ellipse, not a circle
CENTRE_MIN_M = 0.002         # body centre further than this from the bbox centre is written out


def _outline(xy, c, nsec=36):
    """Outermost point per angular sector around c (top view)."""
    d = xy - c
    k = ((np.arctan2(d[:, 1], d[:, 0]) + np.pi) / (2 * np.pi) * nsec).astype(int) % nsec
    r = np.hypot(d[:, 0], d[:, 1])
    out = [d[k == s][np.argmax(r[k == s])] + c for s in range(nsec) if (k == s).sum() >= 3]
    return np.asarray(out)


def fit_body(xy, c0):
    """Centre and axis radii (outer surface) of a container body in top view.

    The outline is the outermost point per 10-degree sector; sectors sticking out more
    than 12 % past the median radius are a handle (mug, pot) and are left out.  An
    axis-aligned ellipse is fitted to the rest, re-centred, four times.  (The old profile
    took the 90th-percentile radius around the bounding-box centre: a mug's handle moved
    that centre 1.6 cm towards the handle and widened the walls by 1.2 cm.)"""
    c = np.asarray(c0, float)
    for _ in range(4):
        e = _outline(xy, c)
        r = np.hypot(*(e - c).T)
        p = e[r <= 1.12 * np.median(r)]
        A, B, C, D = np.linalg.lstsq(np.c_[p[:, 0] ** 2, p[:, 1] ** 2, p[:, 0], p[:, 1]],
                                     np.ones(len(p)), rcond=None)[0]
        c = np.array([-C / (2 * A), -D / (2 * B)])
        g = 1 + A * c[0] ** 2 + B * c[1] ** 2
        rx, ry = math.sqrt(g / A), math.sqrt(g / B)
    return c, rx, ry


def container_profile(mesh, kind, wall=0.007, body_fraction=1.0):
    """Wall bands of a container (consumed by zeno_skills.physics.container_collider).

    round:   bands (z_lo, z_hi, r)        wall-centre radius
    ellipse: bands (z_lo, z_hi, rx, ry)   wall-centre semi-axes
    rect:    bands (z_lo, z_hi, hx, hy)   wall-centre half sizes, per height (sloped sides)
    centre:  body centre minus the bbox bottom centre (x, y), when they differ (a mug's handle)"""
    b = mesh.bounds
    h = (b[1, 2] - b[0, 2]) * body_fraction
    v = mesh.vertices
    c0 = (b[0, :2] + b[1, :2]) / 2
    z = v[:, 2] - b[0, 2]
    edges = np.linspace(0.12 * h, h, 5)
    slabs = [(za, zb, (z >= za) & (z <= zb)) for za, zb in zip(edges[:-1], edges[1:])]
    slabs = [s for s in slabs if s[2].sum() >= 10]
    if kind == "rect_container":
        # one band of straight walls at the bbox.  Walls per height band following sloped sides
        # were tried (11-13): the rim lip of the small storage bin left a 2 cm step between the top
        # band and the one below, and dropping the toy car into it failed in T12 bins_capacity
        # (passes with these walls).
        hx, hy = (b[1, 0] - b[0, 0]) / 2 - wall / 2, (b[1, 1] - b[0, 1]) / 2 - wall / 2
        return {"shape": "rect", "bands": [[0.0, round(h, 4), round(hx, 4), round(hy, 4)]],
                "rim_height": round(h, 4)}
    fits = [(za, zb, *fit_body(v[sel, :2], c0)) for za, zb, sel in slabs]
    centre = np.mean([f[2] for f in fits], axis=0) - c0
    ratio = max(max(f[3], f[4]) / min(f[3], f[4]) for f in fits)
    if ratio > ELLIPSE_MIN:
        shape = "ellipse"
        bands = [[round(za, 4), round(zb, 4), round(rx - wall / 2, 4), round(ry - wall / 2, 4)]
                 for za, zb, _, rx, ry in fits]
        rim = min(bands[-1][2:])
    else:
        shape = "round"
        bands = [[round(za, 4), round(zb, 4), round((rx + ry) / 2 - wall / 2, 4)] for za, zb, _, rx, ry in fits]
        rim = bands[-1][2]
    out = {"shape": shape, "bands": bands, "rim_height": round(h, 4), "rim_radius": rim}
    if np.hypot(*centre) > CENTRE_MIN_M:
        out["centre"] = [round(float(centre[0]), 4), round(float(centre[1]), 4)]
    return out


def palm_spheres():
    """(n, 4) palm and camera collision spheres of the right gripper (PALM_LINKS) in its TCP frame:
    centres relative to the TCP, z along the fingers' opposite (up for a top pinch), y the
    closing direction; radius."""
    import yaml
    from scipy.spatial.transform import Rotation
    from zeno_skills.kinematics import TCP_DEPTH
    cs = yaml.safe_load(ROBOT_YML.read_text())["robot_cfg"]["kinematics"]["collision_spheres"]
    joints = {j.get("name"): j for j in ET.parse(ROBOT_URDF).getroot().iter("joint")}
    out = []
    for link in PALM_LINKS:
        R, t = np.eye(3), np.zeros(3)
        if link != "right_gripper_link":
            o = joints[link.replace("_link", "_joint")].find("origin")
            R = Rotation.from_euler("xyz", [float(x) for x in o.get("rpy").split()]).as_matrix()
            t = np.array([float(x) for x in o.get("xyz").split()])
        for sph in cs[link]:
            out.append(np.r_[R @ np.asarray(sph["center"], float) + t + [0.0, 0.0, TCP_DEPTH], sph["radius"]])
    return np.array(out)


def palm_floor(v, bottom_z, tcp_xy, close_yaws, gap):
    """Lowest TCP height above the bottom at which no palm sphere (grown by ``gap``) reaches a
    vertex of ``v`` (mesh frame), for a top pinch at ``tcp_xy`` closing along each of
    ``close_yaws`` (all of them: the pick may take any)."""
    S = palm_spheres()
    need = -np.inf
    for c in close_yaws:
        y = np.array([math.cos(c), math.sin(c), 0.0])
        z = np.array([0.0, 0.0, 1.0])
        R = np.column_stack((np.cross(y, z), y, z))          # kinematics.gripper_rot, fingers down
        for s in S:
            ctr = R @ s[:3]
            r = s[3] + gap
            rho2 = ((v[:, :2] - (tcp_xy + ctr[:2])) ** 2).sum(1)
            under = rho2 < r * r
            if under.any():
                need = max(need, float((v[under, 2] - bottom_z - ctr[2] + np.sqrt(r * r - rho2[under])).max()))
    return need


def grasps(name, mesh, kind, body_fraction=1.0, profile=None):
    """Grasp primitives in the object frame (origin = bbox centre of the
    bottom face, z up).  Consumed by zeno_skills.annotations.grasp_poses."""
    b = mesh.bounds
    ext = b[1] - b[0]
    out = []
    if kind == "round_container":
        prof = profile or container_profile(mesh, kind, body_fraction=body_fraction)
        g = {"type": "rim_pinch", "radius": prof["rim_radius"], "rim_height": prof["rim_height"],
             "depth": 0.035, "azimuths_deg": list(range(0, 360, 30)), "tilts": [0.5, 0.35, 0.2],
             "pre_open": 0.03}
        if prof.get("centre"):
            g["centre"] = prof["centre"]               # the body's centre, not the bbox's (mug handle)
        if prof.get("shape") == "ellipse":
            g["radii"] = prof["bands"][-1][2:4]        # wall-centre semi-axes at the rim
        out.append(g)
    elif kind == "rect_container":
        out.append({"type": "rim_pinch_rect", "half_x": float(ext[0] / 2), "half_y": float(ext[1] / 2),
                    "rim_height": float(ext[2]), "depth": 0.03, "tilts": [0.4, 0.2], "pre_open": 0.03})
    # top pinch: slide a pad-wide (2.8 cm) slab along the object and find the
    # narrowest graspable cross-section (bananas, pens, spoons, toy cars)
    best = None
    c0 = (b[0, :2] + b[1, :2]) / 2
    v = mesh.vertices
    for yaw in np.radians(np.arange(0, 180, 15)):
        d = np.array([math.cos(yaw), math.sin(yaw)])          # closing direction
        e = np.array([-d[1], d[0]])                            # along the pads
        pd, pe = (v[:, :2] - c0) @ d, (v[:, :2] - c0) @ e
        # central 60 % only: slabs at corners/ends are narrow but not graspable
        lo_e, hi_e = pe.min() + 0.2 * np.ptp(pe), pe.max() - 0.2 * np.ptp(pe)
        for off in np.linspace(lo_e, hi_e, 7) if hi_e - lo_e > 0.005 else [float((pe.min() + pe.max()) / 2)]:
            sel = np.abs(pe - off) < 0.014
            if sel.sum() < 20:
                continue
            width = float(np.ptp(pd[sel]))
            centre = float((pd[sel].max() + pd[sel].min()) / 2)
            top = float(v[sel, 2].max() - b[0, 2])
            score = width + 0.3 * abs(off)                      # prefer central slabs
            if best is None or score < best[0]:
                best = (score, float(yaw), width, c0 + d * centre + e * off - c0, top)
    if best is not None and best[2] <= PINCH_MAX and kind == "solid":
        _, yaw, width, off, top = best
        out.append({"type": "top_pinch", "close_yaw": yaw, "width": width,
                    "offset_xy": [round(float(off[0]), 4), round(float(off[1]), 4)],
                    "height": float(min(top * 0.5, max(top - 0.02, 0.01))),
                    "pre_open": float(min(0.04, width / 2 + 0.012))})
        # Round in top view (can, bottle, fruit): the 2-D hull fills ~pi/4 of
        # its bounding box, and any diameter is a valid closing direction.
        from scipy.spatial import ConvexHull
        hull_area = ConvexHull(mesh.vertices[:, :2]).volume
        if (hull_area / max(ext[0] * ext[1], 1e-9) < 0.86 and abs(ext[0] - ext[1]) < 0.12 * max(ext[:2])) \
                or CUSTOM_RECORDS.get(name, {}).get("round_top"):
            out[-1]["round"] = True
        # Long thin objects (rolling pin, spoon, pen): extra pinch points along
        # the long axis, so a second hand finds a contact away from the first.
        # Only points whose cross-section is no wider than the centre's are
        # kept (a spoon's bowl or a brush head is not a pinch point).
        if max(ext[:2]) >= 0.15 and max(ext[:2]) >= 2.5 * min(ext[:2]):
            ax = int(np.argmax(ext[:2]))
            v = mesh.vertices
            mid = 0.5 * (v[:, ax].min() + v[:, ax].max())

            def under_pads(o):
                # widest cross-section and tallest point under the 2.8 cm pads centred at o
                ws, hs = [], []
                for d in np.linspace(-0.03, 0.03, 9):     # pad span plus 1.5 cm reach tolerance
                    sel = np.abs(v[:, ax] - (mid + o + d)) < 0.004
                    ws.append(float(np.ptp(v[sel, 1 - ax])) if sel.sum() > 3 else 0.0)
                    hs.append(float(v[sel, 2].max() - v[:, 2].min()) if sel.sum() > 3 else 0.0)
                return max(ws), max(hs)
            offs = [round(k * 0.3 * float(max(ext[:2])), 3) for k in (-1, 0, 1)]
            prof = {o: under_pads(o) for o in offs}
            w_min = min(w for w, _ in prof.values())
            keep = [o for o in offs if prof[o][0] <= 1.5 * w_min + 0.005]
            # uniform section first: a bowl or head rising under the pads stops
            # the descent and the pads wedge on its flank (spoon); ties: centre
            out[-1]["along_offsets"] = sorted(keep, key=lambda o: (round(prof[o][1], 3), round(prof[o][0], 3), abs(o)))
        # Tall and round (a bottle): a top pinch at half height puts the palm on the cap long before
        # the pads get there.  Grasp it from the side instead (annotations.grasp_poses: side_pinch;
        # lying on its side it gets the top pinch across it).
        if out[-1].get("round") and top > SIDE_PINCH_MIN_H:
            tp = out.pop()
            out.append({"type": "side_pinch", "width": tp["width"], "offset_xy": tp["offset_xy"],
                        "height": float(min(max(0.55 * top, 0.04), top - 0.03)),
                        "pre_open": tp["pre_open"], "azimuths_deg": list(range(0, 360, 30))})
    # crown pinch: when no full-height slab fits, pinch only the top CROWN
    # metres (what the 5 cm pads span when the TCP sits 2.2 cm below the top):
    # the head of a plush toy, a knob, a lid handle.  Below the crown the
    # object may be wider; the fingertips never reach down there.
    if kind == "solid" and (best is None or best[2] > PINCH_MAX):
        topz = float(b[1, 2])
        crown = v[v[:, 2] > topz - CROWN]
        cc = crown[:, :2].mean(0)
        best_c = None
        for yaw in np.radians(np.arange(0, 180, 15)):
            d = np.array([math.cos(yaw), math.sin(yaw)])
            e = np.array([-d[1], d[0]])
            pd, pe = (crown[:, :2] - cc) @ d, (crown[:, :2] - cc) @ e
            for off in np.linspace(pe.min() + 0.25 * np.ptp(pe), pe.max() - 0.25 * np.ptp(pe), 5):
                sel = np.abs(pe - off) < 0.014
                if sel.sum() < 20:
                    continue
                width = float(np.ptp(pd[sel]))
                centre = float((pd[sel].max() + pd[sel].min()) / 2)
                score = width + 0.3 * abs(off)
                if best_c is None or score < best_c[0]:
                    best_c = (score, float(yaw), width, cc + d * centre + e * off - c0)
        if best_c is not None and best_c[2] <= PINCH_MAX:
            _, yaw, width, off = best_c
            out.append({"type": "top_pinch", "crown": True, "close_yaw": yaw, "width": width,
                        "offset_xy": [round(float(off[0]), 4), round(float(off[1]), 4)],
                        "height": float(topz - b[0, 2] - 0.022),
                        "pre_open": float(min(0.04, width / 2 + 0.012))})
            best = (best_c[0], yaw, width, off, topz)
    min_w = best[2] if best else float("inf")
    if ext[2] < 0.075 and max(ext[:2]) > GRIPPER_GAP and not out:
        # flat, wider than the gripper and no other pinch: across its thickness at a side
        out.append({"type": "thickness_pinch", "depth": THICKNESS_PINCH_DEPTH,
                    "pre_open": float(min(0.04, ext[2] / 2 + 0.012)),
                    "note": "pads above and below, from outside a side; the side must overhang its support"})
    if name == "breakfast_mug":
        # Collision OBJ is rotated +90 deg about X by the URDF.  Its handle
        # protrudes in object -Y at mid-height, separate from the rim contact.
        out.append({"type": "handle_pinch", "center": [0.0, -0.080, 0.025],
                    "approach": [0.0, 1.0, 0.0], "close_dir": [1.0, 0.0, 0.0],
                    "pre_open": 0.03,
                    "note": "TCP sits 19 mm outside the -Y handle bar so fingertip pads pinch the bar without contacting the mug wall; mesh transformed by +90 deg about X"})
    if "top_grasp" in CUSTOM_RECORDS.get(name, {}):
        out.append(CUSTOM_RECORDS[name]["top_grasp"])
    if "handle_grasp" in CUSTOM_RECORDS.get(name, {}):
        out.append(CUSTOM_RECORDS[name]["handle_grasp"])
    # the palm stays above the object: half the height put the palm of a top pinch 2.4 cm into a
    # soda can, and the hand stopped that much short of the grasp (planner 6.2 measurement)
    from zeno_skills.rig import LEAVE_GAP
    square = abs(ext[0] - ext[1]) < 0.01 and max(ext[:2]) < 0.075     # annotations: extra_rotations
    for g in out:
        if g["type"] != "top_pinch" or "close_yaw" not in g:
            continue
        flips = np.radians(np.arange(0, 360, 45)) if g.get("round") else \
            np.radians([0, 90, 180, 270]) if square else np.radians([0, 180])
        y0 = g["close_yaw"]
        along = np.array([-math.sin(y0), math.cos(y0)])
        floor = max(palm_floor(mesh.vertices, b[0, 2], c0 + np.asarray(g["offset_xy"]) + along * a,
                               y0 + flips, LEAVE_GAP) for a in g.get("along_offsets", [0.0]))
        if floor > g["height"]:
            g["height"] = float(floor)
    return out, min_w


def write_sim_urdf(name):
    L, mass, tags, kind, _ = SPECS[name]
    src = source_urdf(name)
    mesh = mesh_zup(src)
    custom = CUSTOM_RECORDS.get(name, {})
    target_size = custom.get("target_size")
    s = 1.0 if L is None else L / float(np.max(mesh.extents))
    tree = ET.parse(src)
    link = tree.getroot().find("link")
    Rf = flat_rotation(mesh) if (name in LAY_FLAT and L is not None) else np.eye(3)
    if target_size is not None:
        if name in LAY_FLAT:
            raise ValueError(f"{name}: target_size with lay_flat is unsupported")
        target = np.asarray(target_size, dtype=float)
        if target.shape != (3,) or np.any(target <= 0):
            raise ValueError(f"{name}: target_size must contain three positive dimensions")
        world_scale = target / mesh.extents
    elif name in THICKNESS:
        flat_h = np.ptp((mesh.vertices @ Rf.T)[:, 2])
        world_scale = np.array([s, s, THICKNESS[name] / flat_h])
    else:
        world_scale = np.full(3, s)
    nonuniform = target_size is not None or name in THICKNESS
    from scipy.spatial.transform import Rotation
    for tag in ("visual", "collision"):
        for el in link.findall(tag):
            m = el.find("geometry").find("mesh")
            old = np.asarray([float(v) for v in (m.get("scale") or "1 1 1").split()])
            o = el.find("origin")
            R0 = Rotation.from_euler("xyz", [float(v) for v in o.get("rpy").split()]).as_matrix()
            axes = np.abs(Rf @ R0)
            if target_size is not None and not (np.allclose(axes.sum(axis=0), 1, atol=1e-3)
                                                and np.allclose(axes.sum(axis=1), 1, atol=1e-3)):
                raise ValueError(f"{name}: target_size requires an axis-aligned URDF orientation")
            if name in THICKNESS:
                # the OBB flat rotation is a near-permutation: snap it
                if np.abs(axes - np.round(axes)).max() > 0.02:
                    raise ValueError(f"{name}: thickness requires an axis-aligned flat orientation")
                axes = np.round(axes)
            local_scale = axes.T @ world_scale if nonuniform else world_scale
            m.set("scale", " ".join(f"{v:.6f}" for v in old * local_scale))
            o.set("rpy", " ".join(f"{v:.6f}" for v in Rotation.from_matrix(Rf @ R0).as_euler("xyz")))
    T = np.eye(4)
    T[:3, :3] = Rf
    mesh.apply_transform(T)
    mesh.apply_scale(world_scale)
    ext = mesh.extents
    inert = link.find("inertial")
    inert.find("mass").set("value", f"{mass:.4f}")
    I = inert.find("inertia")
    I.set("ixx", f"{mass * (ext[1] ** 2 + ext[2] ** 2) / 12:.3e}")
    I.set("iyy", f"{mass * (ext[0] ** 2 + ext[2] ** 2) / 12:.3e}")
    I.set("izz", f"{mass * (ext[0] ** 2 + ext[1] ** 2) / 12:.3e}")
    for k in ("ixy", "ixz", "iyz"):
        I.set(k, "0.0")
    out = src.parent / f"{name}_sim.urdf"
    tree.write(out)
    b = mesh.bounds
    bf = BODY_FRACTION.get(name, 1.0)
    custom = CUSTOM_RECORDS.get(name, {})
    profile = custom.get("container_profile") or (container_profile(mesh, kind, body_fraction=bf)
                                                   if kind != "solid" else None)
    g, min_width = grasps(name, mesh, kind, bf, profile)
    ann = {"name": name, "tags": tags, "mass": mass, "collider": kind,
           "size": [round(float(v), 4) for v in ext],
           # vector from the rigid-body origin to the bottom-centre of the bbox
           "origin_to_bottom_center": [round(float((b[0, 0] + b[1, 0]) / 2), 4),
                                       round(float((b[0, 1] + b[1, 1]) / 2), 4), round(float(b[0, 2]), 4)],
           "min_pinch_width": round(min_width, 4),
           "graspable_by_zeno": bool(g),
           "grasps": g,
           "usd": f"usd/assets/{name}.usd",
           "source_urdf": str(out.relative_to(ROOT)),
           "generator": CUSTOM_RECORDS.get(name, {}).get("generator", "EmbodiedGen V2 text3d-cli (SAM3D backend)")}
    if "knob_collider" in custom:
        ann["knob_collider"] = custom["knob_collider"]
    if kind != "solid":
        ann["container"] = profile
        if "handle_collider" in custom:
            ann["container"]["handle_collider"] = custom["handle_collider"]
        if "extra_handle_colliders" in custom:
            ann["container"]["extra_handle_colliders"] = custom["extra_handle_colliders"]
        if name == "breakfast_mug":
            # The imported mug handle is a thin bar, about 14 mm wide at
            # local y=-61 mm; the round-wall approximation omits it.
            ann["container"]["handle_collider"] = {
                "center": [0.0, -0.061, 0.025], "size": [0.014, 0.008, 0.055]}
    return out, ann


def patch_usd(name, urdf):
    """Write the sim URDF's mesh scales, mass and inertia into the existing
    usd/assets/<name>.usd layers (same prims the URDF converter authored), so a
    rescale needs neither EmbodiedGen nor Isaac."""
    from pxr import Gf, Sdf
    link = ET.parse(urdf).getroot().find("link")
    cfg = USD_OUT / "configuration"
    for tag, layer, path in (("visual", "base", f"/visuals/{name}/{name}"),
                             ("collision", "physics", f"/colliders/{name}/{name}_collision")):
        scale = [float(v) for v in link.find(tag).find("geometry").find("mesh").get("scale").split()]
        lay = Sdf.Layer.FindOrOpen(str(cfg / f"{name}_{layer}.usd"))
        if lay.GetAttributeAtPath(f"{path}.xformOp:scale") is None:   # collider kept in the base layer
            lay = Sdf.Layer.FindOrOpen(str(cfg / f"{name}_base.usd"))
        lay.GetAttributeAtPath(f"{path}.xformOp:scale").default = Gf.Vec3d(*scale)
        lay.Save()
    inert = link.find("inertial")
    I = inert.find("inertia")
    lay = Sdf.Layer.FindOrOpen(str(cfg / f"{name}_physics.usd"))
    body = f"/{name}/{name}"
    lay.GetAttributeAtPath(f"{body}.physics:mass").default = float(inert.find("mass").get("value"))
    lay.GetAttributeAtPath(f"{body}.physics:diagonalInertia").default = Gf.Vec3f(
        *(float(I.get(k)) for k in ("ixx", "iyy", "izz")))
    lay.Save()


# Concave solids whose single convex hull fills hollows by 1.3-3.7 cm (95th percentile of the hull's
# surface off the mesh): they collide as V-HACD convex pieces instead (zeno_skills.physics.solid_collider).
# Not pot_lid / soup_pot: the lid's hull only fills under its dome, and the pot's pieces bulged
# 2-6 cm past the mesh (worse than its hull).  Not foil_takeout_tray: it is a closed takeout box
# with food in it; as an open shell, expose's top push pressed into it and it did not move (11-13).
DECOMPOSE = {"banana", "teddy_bear", "toy_car", "rubber_duck", "breakfast_spoon", "breakfast_plate"}
HULLS = ROOT / "annotations" / "collision_hulls.json"
HULL_VERTS = 60              # cuRobo takes at most 64 vertices per hull (zeno_skills/scene_geometry.py)


def _outer_overfill(parts, mesh):
    """95th percentile distance from the pieces' outer surface (not the faces shared inside the union)
    to the mesh: how far the collider bulges past what is drawn."""
    pts = []
    area = sum(p.area for p in parts)
    for i, h in enumerate(parts):
        p, _ = trimesh.sample.sample_surface(h, max(200, int(3000 * h.area / area)), seed=i)
        keep = np.ones(len(p), bool)
        for j, o in enumerate(parts):
            if j != i:
                keep &= ~o.contains(p)
        pts.append(p[keep])
    _, d, _ = trimesh.proximity.closest_point(mesh, np.vstack(pts))
    return float(np.percentile(d, 95))


def convex_pieces(name):
    """V-HACD pieces of the sim mesh in the body frame (16 or 32 pieces, whichever bulges less)."""
    mesh = mesh_zup(source_urdf(name).parent / f"{name}_sim.urdf")   # the body frame (write_sim_urdf)
    best = None
    for n in (16, 32):
        parts = mesh.convex_decomposition(maxConvexHulls=n, resolution=400000, maxNumVerticesPerCH=HULL_VERTS)
        parts = [p if isinstance(p, trimesh.Trimesh) else trimesh.Trimesh(**p) for p in parts]
        err = _outer_overfill(parts, mesh)
        if best is None or err < best[0]:
            best = (err, parts)
    err, parts = best
    single = _outer_overfill([mesh.convex_hull], mesh)
    print(f"HULLS {name}: {len(parts)} pieces, bulge p95 {err * 1000:.1f} mm (one hull {single * 1000:.1f} mm)",
          flush=True)
    return [{"points": np.round(p.vertices, 5).tolist(), "faces": p.faces.tolist()} for p in parts]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--convert", action="store_true", help="URDF -> USD for assets missing a USD")
    ap.add_argument("--patch-usd", action="store_true",
                    help="rescale the existing USDs in place from the sim URDFs (no EmbodiedGen needed)")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--hulls", action="store_true",
                    help="recompute the convex pieces of the DECOMPOSE assets (annotations/collision_hulls.json)")
    args = ap.parse_args()
    names = [n for n in SPECS if (args.only is None or n in args.only) and source_urdf(n).exists()]
    missing = [n for n in SPECS if not source_urdf(n).exists()]
    anns = json.loads(ANN.read_text()) if ANN.exists() else {}
    urdfs = {}
    for n in names:
        urdfs[n], anns[n] = write_sim_urdf(n)
        print("ANNOTATED", n, anns[n]["size"], [g["type"] for g in anns[n]["grasps"]], flush=True)
    ANN.parent.mkdir(parents=True, exist_ok=True)
    ANN.write_text(json.dumps(anns, indent=1))
    print("MISSING (not generated yet):", missing)
    if args.hulls:
        hulls = json.loads(HULLS.read_text()) if HULLS.exists() else {}
        for n in names:
            if n in DECOMPOSE:
                hulls[n] = convex_pieces(n)
        HULLS.write_text(json.dumps(hulls, separators=(",", ":")))
    if args.patch_usd:
        for n in names:
            patch_usd(n, urdfs[n])
            print("PATCHED", USD_OUT / f"{n}.usd", flush=True)
    if not args.convert:
        return
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    sys.path.insert(0, str(REPO))
    from embodied_gen.data.asset_converter import AssetConverterFactory
    from embodied_gen.utils.enum import AssetType
    conv = AssetConverterFactory.create(target_type=AssetType.USD, source_type=AssetType.URDF,
                                        fix_base=False, merge_fixed_joints=False, make_instanceable=False,
                                        collision_from_visuals=False, simulation_app=app)
    USD_OUT.mkdir(parents=True, exist_ok=True)
    for n in names:
        usd = USD_OUT / f"{n}.usd"
        if usd.exists() and SPECS[n][0] is None:
            continue                     # breakfast set: keep the USDs the scene already uses
        conv.convert(str(urdfs[n]), str(usd))
        print("USD", usd, flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
