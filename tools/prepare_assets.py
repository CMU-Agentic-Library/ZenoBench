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
    "toy_block": (0.050, 0.04, ["toy", "block"], "solid", None),
    "rubber_duck": (0.090, 0.05, ["toy", "duck"], "solid", None),
    "toy_box": (0.500, 3.00, ["container", "toy_box", "storage"], "rect_container", None),
    "storage_basket": (0.380, 0.60, ["container", "basket", "storage"], "rect_container", None),
}
# rest these with the thinnest axis vertical and the longest along x
LAY_FLAT = {"notebook", "pen", "pencil", "book_red", "book_green", "book_blue", "breakfast_spoon", "banana"}

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


def container_profile(mesh, kind, wall=0.007, body_fraction=1.0):
    b = mesh.bounds
    h = (b[1, 2] - b[0, 2]) * body_fraction
    if kind == "rect_container":
        hx, hy = (b[1, 0] - b[0, 0]) / 2 - wall / 2, (b[1, 1] - b[0, 1]) / 2 - wall / 2
        return {"shape": "rect", "bands": [[0.0, round(h, 4), round(hx, 4), round(hy, 4)]],
                "rim_height": round(h, 4)}
    v = mesh.vertices
    c = (b[0, :2] + b[1, :2]) / 2
    r = np.linalg.norm(v[:, :2] - c, axis=1)
    z = v[:, 2] - b[0, 2]
    bands = []
    edges = np.linspace(0.12 * h, h, 5)
    for za, zb in zip(edges[:-1], edges[1:]):
        sel = (z >= za) & (z <= zb)
        if sel.sum() < 10:
            continue
        # wall centre: outer radius minus half a wall (handles excluded by the
        # 90th percentile)
        ro = float(np.percentile(r[sel], 90))
        bands.append([round(za, 4), round(zb, 4), round(ro - wall / 2, 4)])
    return {"shape": "round", "bands": bands, "rim_height": round(h, 4),
            "rim_radius": bands[-1][2] if bands else None}


def grasps(name, mesh, kind, body_fraction=1.0, profile=None):
    """Grasp primitives in the object frame (origin = bbox centre of the
    bottom face, z up).  Consumed by zeno_skills.annotations.grasp_poses."""
    b = mesh.bounds
    ext = b[1] - b[0]
    out = []
    if kind == "round_container":
        prof = profile or container_profile(mesh, kind, body_fraction=body_fraction)
        out.append({"type": "rim_pinch", "radius": prof["rim_radius"], "rim_height": prof["rim_height"],
                    "depth": 0.035, "azimuths_deg": list(range(0, 360, 30)), "tilts": [0.5, 0.35, 0.2],
                    "pre_open": 0.03})
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
    if ext[2] < 0.075 and max(ext[:2]) > GRIPPER_GAP:
        out.append({"type": "edge_pinch_after_push",
                    "note": "flat & wider than the gripper: slide to a support edge, pinch the overhang",
                    "thickness": float(ext[2])})
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
    else:
        world_scale = np.full(3, s)
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
            local_scale = axes.T @ world_scale if target_size is not None else world_scale
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--convert", action="store_true", help="URDF -> USD for assets missing a USD")
    ap.add_argument("--only", nargs="*")
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
