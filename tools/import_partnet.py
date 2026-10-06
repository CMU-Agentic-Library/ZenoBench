"""Import a PartNet-Mobility articulated object (cabinet, fridge, ...) as a
sim-ready articulated USD in the layout of the house's cabinets, so that
tools/annotate_scene.py annotates it and the open/close skills operate it.

    cd zeno-house   # repository root
    ${ISAACLAB_PYTHON:-python} tools/import_partnet.py --id 48452 --name partnet_cabinet_48452 --height 1.0

Input: /data/PartNetMobility/<id>.zip (or --root).  Output:
  usd/partnet/<name>/<name>.usd     the articulated asset (+ textures/)
  usd/partnet/<name>/import.json    source, scale, joint, handle check
Put it in the house with tools/place_partnet.py.

USD layout (the same as the cabinets in sim/zeno_house.usd):
  /<name>              asset frame: bottom centre of the closed object, front (door side) = -y
    base               rigid body: visual/ meshes, one convex-hull collider per PartNet part,
                       named by role (bottom, top, shelf, side, back, ...: the annotation finds
                       the shelves inside the carcass by these names)
    door               one rigid body per moving part, origin on its joint: visual/, panel
                       colliders, the handle bar ("handle", a box, zeno:bar_axis = its long
                       axis) and its standoffs ("handle_standoff_<k>")
    joints/door_hinge  revolute (drawers: joints/drawer_slide, prismatic), closed at q = 0
    root_joint         fixed joint to the world (articulation root), posed by place_partnet.py

Several parts (a two-door fridge, a dresser): door_0, door_1, drawer_0, ... (top row
first, then left to right) with joints/door_0_hinge, joints/drawer_0_slide, ...
Every movable joint on the carcass becomes a part; joints nested in a moving
part (a knob on a door) and continuous joints are fixed into their parent.

The handle is not a convex hull: that would fill the gap between bar and
panel that the side-hook grasp puts a finger into.  The handle mesh is sliced
parallel to the panel; the levels whose section runs along the whole handle
are the bar, the pieces below them are the standoffs.  import.json reports the
gap and bar thickness; a handle without a usable gap is marked not hookable.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "usd" / "partnet"
PAD = 0.012            # Zeno finger pad thickness (zeno_skills/physics.py fix_robot)

# PartNet part name -> collider role.  annotate_scene.py reads bottom/shelf/floor
# as supports inside the carcass and roof/top/shelf as what bounds them above.
ROLES = {"bottom_panel": "bottom", "base_side_panel": "plinth", "top_panel": "top", "shelf": "shelf",
         "back_panel": "back", "vertical_side_panel": "side", "vertical_divider_panel": "divider",
         "frame_horizontal_bar": "frame", "frame_vertical_bar": "frame", "cabinet_door_surface": "panel",
         "door_frame": "panel", "drawer_front": "panel", "handle": "handle"}


def T_of(o):
    from scipy.spatial.transform import Rotation
    M = np.eye(4)
    if o is None:
        return M
    M[:3, :3] = Rotation.from_euler("xyz", [float(x) for x in (o.get("rpy") or "0 0 0").split()]).as_matrix()
    M[:3, 3] = [float(x) for x in (o.get("xyz") or "0 0 0").split()]
    return M


def rz(a):
    M = np.eye(4)
    c, s = math.cos(a), math.sin(a)
    M[:2, :2] = [[c, -s], [s, c]]
    return M


# ---------------------------------------------------------------- OBJ / MTL
def parse_mtl(text):
    mats, cur = {}, None
    for line in text.splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] == "newmtl":
            cur = mats.setdefault(" ".join(t[1:]), {"Kd": [0.8, 0.8, 0.8], "map_Kd": None})
        elif cur is not None and t[0] == "Kd":
            cur["Kd"] = [float(v) for v in t[1:4]]
        elif cur is not None and t[0] == "map_Kd":
            cur["map_Kd"] = t[-1]
    return mats


def parse_obj(text):
    """-> v (N,3), vt (M,2), groups [(material, [[(vi, ti), ...] per face])]"""
    v, vt, groups, cur, mtllib = [], [], [], None, None
    for line in text.splitlines():
        t = line.split()
        if not t:
            continue
        if t[0] == "v":
            v.append([float(x) for x in t[1:4]])
        elif t[0] == "vt":
            vt.append([float(x) for x in t[1:3]])
        elif t[0] == "mtllib":
            mtllib = t[1]
        elif t[0] == "usemtl":
            cur = (" ".join(t[1:]), [])
            groups.append(cur)
        elif t[0] == "f":
            if cur is None:
                cur = (None, [])
                groups.append(cur)
            face = []
            for w in t[1:]:
                idx = w.split("/")
                vi = int(idx[0])
                ti = int(idx[1]) if len(idx) > 1 and idx[1] else None
                face.append((vi - 1 if vi > 0 else len(v) + vi,
                             None if ti is None else (ti - 1 if ti > 0 else len(vt) + ti)))
            cur[1].append(face)
    return np.array(v, float).reshape(-1, 3), np.array(vt, float).reshape(-1, 2), \
        [g for g in groups if g[1]], mtllib


# ---------------------------------------------------------------- handle
def _loops(mesh, n_dir, level):
    """Section loops of ``mesh`` with the plane {x . n_dir = level}: list of (K,3)."""
    sec = mesh.section(plane_origin=n_dir * level, plane_normal=n_dir)
    if sec is None:
        return []
    return [np.asarray(d) for d in sec.discrete if len(d) >= 2]


def handle_geometry(H, face_n, n_dir, long_ax, slot=0.03):
    """Bar box + standoff boxes of a handle mesh (asset frame, closed).

    H: trimesh of the handle; face_n: panel front at x . n_dir = face_n;
    long_ax: 0 (x) or 2 (z), the handle's long axis.  The finger hooks behind
    the handle's middle: ``slot`` (a pad width) around the centre along the
    handle.  The bar is the material in front of that slot (a straight bar, or
    the apex of an arched pull), gap = free depth behind it; everything else
    (standoffs, arch legs) becomes stacked boxes.  Returns dict with bar
    [lo, hi], standoffs [[lo, hi], ...], gap, thickness, length."""
    n_hi = float((H.vertices @ n_dir).max())
    L = float(np.ptp(H.vertices[:, long_ax]))
    mid = float(H.vertices[:, long_ax].min()) + L / 2
    levels = np.arange(face_n + 0.0005, n_hi - 0.0003, 0.0005)
    loops = [_loops(H, n_dir, lv) for lv in levels]

    def in_slot(lps):
        return any(lp[:, long_ax].min() < mid + slot / 2 and lp[:, long_ax].max() > mid - slot / 2 for lp in lps)
    hit = np.array([in_slot(lps) for lps in loops], bool)
    if not hit.any():
        return {"hookable": False, "reason": "nothing in front of the handle middle"}
    # bar: the contiguous run of levels with material in the slot, from the front down
    k = len(levels) - 1
    while k >= 0 and not hit[k]:
        k -= 1
    top = k
    while k >= 0 and hit[k]:
        k -= 1
    bar_levels = range(k + 1, top + 1)
    bar_lo = float(levels[k + 1])
    gap = bar_lo - face_n
    sign = int(np.argmax(np.abs(n_dir)))
    pts = np.concatenate([lp for i in bar_levels for lp in loops[i]])
    lo, hi = pts.min(0), pts.max(0)
    lo[sign], hi[sign] = sorted((bar_lo * n_dir[sign], n_hi * n_dir[sign]))
    # below the bar: one box per loop, merged across levels while it stays put
    face_axes = [ax for ax in range(3) if ax != sign]
    standoffs, open_ = [], []
    below = list(range(0, k + 1, 4))                  # 2 mm layers
    for m, i in enumerate(below):
        z0 = face_n if m == 0 else levels[i]
        z1 = levels[below[m + 1]] if m + 1 < len(below) else bar_lo
        nxt = []
        for lp in loops[i]:
            a, b = lp.min(0), lp.max(0)
            same = [q for q, box in enumerate(open_) if np.all(np.abs(box[0] - a)[face_axes] < 0.005)
                    and np.all(np.abs(box[1] - b)[face_axes] < 0.005)]
            if same:
                box = open_.pop(same[0])
                box[3] = z1
                nxt.append(box)
            else:
                nxt.append([a, b, z0, z1])
        standoffs += open_
        open_ = nxt
    standoffs += open_
    boxes = []
    for a, b, z0, z1 in standoffs:
        a, b = a.copy(), b.copy()
        a[sign], b[sign] = sorted((z0 * n_dir[sign], (z1 + 0.001) * n_dir[sign]))
        boxes.append([a.tolist(), b.tolist()])
    t = n_hi - bar_lo
    ok = gap >= PAD + 0.008 and L >= 0.06
    return {"hookable": bool(ok), "reason": "" if ok else f"gap {gap:.3f} m / length {L:.3f} m too small",
            "bar": [lo.tolist(), hi.tolist()], "standoffs": boxes, "gap": round(gap, 4),
            "thickness": round(t, 4), "length": round(L, 4), "long_axis": "xyz"[long_ax]}


# ---------------------------------------------------------------- main
def joint_axis(J):
    """Unit joint axis (some PartNet URDFs store e.g. 0 0 -0.961)."""
    a = np.array([float(x) for x in (J.find("axis").get("xyz") if J.find("axis") is not None else "1 0 0").split()])
    return a / (np.linalg.norm(a) or 1.0)


def front_dir(elems, top, world):
    """Horizontal unit axis (+-x or +-y, URDF frame) the moving parts face.

    Each door/drawer votes, weighted by its face area: a drawer slides along
    the normal; a door on a vertical hinge is thinnest along it; a door on a
    horizontal hinge (oven, flap) has the normal perpendicular to the hinge.
    The sign is the side of the carcass box the part sits on.  (The mean of
    the part vertices, the fallback, is pulled sideways by uneven meshes: a
    microwave door beside its control panel.)"""
    base_v = [e["v"] for e in elems if e["owner"] is None]
    allv = np.concatenate([e["v"] for e in elems])
    bv = np.concatenate(base_v) if base_v else allv
    bc = (bv.min(0) + bv.max(0)) / 2
    votes = np.zeros((2, 2))                       # [axis x/y][sign -/+]
    for J in top:
        mine = [e["v"] for e in elems if e["owner"] is J]
        if not mine:
            continue
        v = np.concatenate(mine)
        ext = np.ptp(v, axis=0)
        ax = world(J.find("child").get("link"))[:3, :3] @ joint_axis(J)
        if J.get("type") == "prismatic":
            if abs(ax[2]) > 0.7:                   # vertical slider: says nothing about the front
                continue
            k = int(np.argmax(np.abs(ax[:2])))
        elif abs(ax[2]) > 0.7:
            k = int(np.argmin(ext[:2]))
        else:
            k = 1 - int(np.argmax(np.abs(ax[:2])))
        s = (v[:, k].min() + v[:, k].max()) / 2 - bc[k]
        if abs(s) < 1e-6:
            continue
        votes[k, int(s > 0)] += ext[1 - k] * ext[2]
    out = np.zeros(3)
    if votes.max() > 0:
        k, s = np.unravel_index(int(np.argmax(votes)), votes.shape)
        out[k] = 1.0 if s else -1.0
        return out
    d = np.concatenate([e["v"] for e in elems if e["owner"] is not None]).mean(0) - bv.mean(0)
    k = int(np.argmax(np.abs(d[:2])))
    out[k] = np.sign(d[k]) or 1.0
    return out


def load(zip_path, mid):
    f = zipfile.ZipFile(zip_path)
    meta = json.loads(f.read(f"{mid}/meta.json"))
    urdf = ET.fromstring(f.read(f"{mid}/mobility.urdf"))
    return f, meta, urdf


def build(args):
    zpath = Path(args.root) / f"{args.id}.zip"
    zf, meta, urdf = load(zpath, args.id)
    joints = urdf.findall("joint")
    parent = {j.find("child").get("link"): j for j in joints}
    kinds = ("revolute", "prismatic") + (("continuous",) if args.keep_continuous else ())

    def movable_on_path(link):
        """Movable joints between ``link`` and the root, nearest the root last."""
        out = []
        while link in parent:
            j = parent[link]
            if j.get("type") in kinds:
                out.append(j)
            link = j.find("parent").get("link")
        return out

    # one moving body per joint that hangs directly on the carcass; joints
    # nested in a moving part (a knob on a door) are fixed into that part
    top = [j for j in joints if j.get("type") in kinds and not movable_on_path(j.find("parent").get("link"))]
    nested = [j.get("name") for j in joints if j.get("type") in ("revolute", "prismatic", "continuous")
              and j not in top]
    if not top:
        raise SystemExit(f"{args.id}: no movable joint")

    def world(link):
        T = np.eye(4)
        while link in parent:
            j = parent[link]
            T = T_of(j.find("origin")) @ T
            link = j.find("parent").get("link")
        return T

    def owner(link):
        path = movable_on_path(link)
        return path[-1] if path else None

    elems = []
    for L in urdf.findall("link"):
        for vis in L.findall("visual"):
            fn = vis.find("geometry/mesh").get("filename")
            pname = re.sub(r"-\d+$", "", vis.get("name") or "part")
            elems.append({"owner": owner(L.get("name")), "part": pname, "part_id": vis.get("name"),
                          "file": fn, "T": world(L.get("name")) @ T_of(vis.find("origin"))})
    for e in elems:
        v, vt, groups, mtllib = parse_obj(zf.read(f"{args.id}/{e['file']}").decode())
        e.update(v=(e["T"][:3, :3] @ v.T).T + e["T"][:3, 3], vt=vt, groups=groups)
        mtl = Path(e["file"]).parent / mtllib if mtllib else None
        e["mtl"] = parse_mtl(zf.read(f"{args.id}/{mtl}").decode()) if mtl else {}
        e["mtl_dir"] = str(mtl.parent) if mtl else ""

    # canonical frame: the side of the object with the moving parts faces -y
    allv = np.concatenate([e["v"] for e in elems])
    out_dir = front_dir(elems, top, world)
    yaw = math.atan2(-1.0, 0.0) - math.atan2(out_dir[1], out_dir[0])
    R = rz(yaw)
    rot = (R[:3, :3] @ allv.T).T
    s = args.height / float(np.ptp(rot[:, 2]))
    lo, hi = rot.min(0) * s, rot.max(0) * s
    A = np.eye(4)
    A[:3, :3] = s * R[:3, :3]
    A[:3, 3] = -np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    for e in elems:
        e["v"] = (A[:3, :3] @ e["v"].T).T + A[:3, 3]

    n_dir = np.array([0.0, -1.0, 0.0])

    def hmesh(es):
        return trimesh.util.concatenate([trimesh.Trimesh(e["v"], [
            [f[0][0], f[i][0], f[i + 1][0]] for f in (ff for g in e["groups"] for ff in g[1])
            for i in range(1, len(f) - 1)], process=True) for e in es])

    parts = []
    for J in top:
        mine = [e for e in elems if e["owner"] is J]
        if not mine:
            continue
        Tc = world(J.find("child").get("link"))
        pivot = A[:3, :3] @ Tc[:3, 3] + A[:3, 3]
        axis = R[:3, :3] @ Tc[:3, :3] @ joint_axis(J)
        ai = int(np.argmax(np.abs(axis)))
        if abs(axis[ai]) < 0.98:
            raise SystemExit(f"{args.id}: joint {J.get('name')} axis {axis.round(3)} is not along x/y/z")
        lim = J.find("limit")               # continuous joints have none
        lo_l, hi_l = (0.0, 0.0) if lim is None else (float(lim.get("lower", 0)), float(lim.get("upper", 0)))
        if J.get("type") == "continuous":
            lo_l, hi_l = 0.0, math.pi
        rev = J.get("type") != "prismatic"
        if not rev:
            lo_l, hi_l = lo_l * s, hi_l * s
        if axis[ai] < 0:                    # joint about +axis: q -> -q
            lo_l, hi_l = -hi_l, -lo_l
        if not (lo_l - 1e-6 <= 0.0 <= hi_l + 1e-6):
            raise SystemExit(f"{args.id}: {J.get('name')}: q = 0 (the mesh pose) is outside [{lo_l}, {hi_l}]")
        # handle: the one farthest from the hinge (doors) / the longest (drawers)
        handles = {}
        for e in mine:
            if e["part"] == "handle":
                handles.setdefault(e["part_id"], []).append(e)
        hinfo, handle_id = {"hookable": False, "reason": "no handle part"}, None
        if handles:
            cand = {hid: hmesh(es) for hid, es in handles.items()}

            def rank(hid):
                c = cand[hid].bounds.mean(0)
                if rev:
                    r = (c - pivot) - np.dot(c - pivot, np.eye(3)[ai]) * np.eye(3)[ai]
                    return float(np.linalg.norm(r))
                return float(np.ptp(cand[hid].vertices[:, [0, 2]], axis=0).max())
            handle_id = max(cand, key=rank)
            H = cand[handle_id]
            # panel front behind the handle: every panel element whose extent
            # overlaps the handle footprint (low-poly boards have no vertex there)
            hb = H.bounds
            fronts = [float((e["v"] @ n_dir).max()) for e in mine if e["part"] != "handle"
                      and np.all(e["v"][:, [0, 2]].min(0) < hb[1, [0, 2]])
                      and np.all(e["v"][:, [0, 2]].max(0) > hb[0, [0, 2]])]
            face_n = max(fronts) if fronts else float((hb[0] if n_dir @ hb[0] < n_dir @ hb[1] else hb[1]) @ n_dir)
            long_ax = 0 if np.ptp(H.vertices[:, 0]) > np.ptp(H.vertices[:, 2]) else 2
            hinfo = handle_geometry(H, face_n, n_dir, long_ax)
            hinfo["part"] = handle_id
            hinfo["long_axis"] = "xyz"[long_ax]
            # round pulls (fixed cabinet "knobs") and short pulls without a finger gap: pinched from the front
            hinfo["grasp"] = "side" if hinfo["hookable"] else "front"
        c = np.concatenate([e["v"] for e in mine]).mean(0)
        parts.append({"J": J, "elems": mine, "rev": rev, "pivot": pivot, "ai": ai, "limits": (lo_l, hi_l),
                      "hinfo": hinfo, "handle_id": handle_id, "centre": c})
    # names: top row first, then left to right; a single part keeps the plain name
    parts.sort(key=lambda p: (-round(p["centre"][2], 1), p["centre"][0]))
    seen = {}
    for p in parts:
        kind = "door" if p["rev"] else "drawer"
        if len(parts) == 1:
            p["body"] = kind
        else:
            p["body"] = f"{kind}_{seen.get(kind, 0)}"
            seen[kind] = seen.get(kind, 0) + 1
        p["joint_name"] = ("door_hinge" if p["rev"] else "drawer_slide") if len(parts) == 1 else \
            f"{p['body']}_{'hinge' if p['rev'] else 'slide'}"
        for e in p["elems"]:
            e["body"] = p["body"]
    for e in elems:
        e.setdefault("body", "base")

    write_usd(args, meta, elems, parts, zf)
    size = (hi - lo).round(4).tolist()
    info = {"source": f"PartNet-Mobility {args.id}", "category": meta.get("model_cat"), "name": args.name,
            "scale": round(s, 5), "yaw_deg": round(math.degrees(yaw), 2), "size": size,
            "parts": [{"body": p["body"], "joint": p["joint_name"], "source_joint": p["J"].get("name"),
                       "type": "revolute" if p["rev"] else "prismatic", "axis": "XYZ"[p["ai"]],
                       "pivot": p["pivot"].round(4).tolist(), "limits": [round(v, 4) for v in p["limits"]],
                       "handle": {k: v for k, v in p["hinfo"].items() if k not in ("bar", "standoffs")}}
                      for p in parts],
            "fixed_nested_joints": nested,
            "usd": str((OUT / args.name / f"{args.name}.usd").relative_to(ROOT))}
    (OUT / args.name / "import.json").write_text(json.dumps(info, indent=1))
    print("IMPORTED", json.dumps(info), flush=True)


def write_usd(args, meta, elems, parts, zf):
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt, PhysxSchema
    d = OUT / args.name
    if d.exists():
        shutil.rmtree(d)
    (d / "textures").mkdir(parents=True)
    stage = Usd.Stage.CreateNew(str(d / f"{args.name}.usd"))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.SetStageKilogramsPerUnit(stage, 1.0)
    rootp = f"/{args.name}"
    root = UsdGeom.Xform.Define(stage, rootp).GetPrim()
    stage.SetDefaultPrim(root)
    root.SetMetadata("kind", "component")
    root.CreateAttribute("zeno:source", Sdf.ValueTypeNames.String).Set(f"PartNet-Mobility {args.id} "
                                                                       f"({meta.get('model_cat')})")
    offset = {"base": np.zeros(3), **{p["body"]: p["pivot"] for p in parts}}
    bodies = {}
    for b, mass in [("base", args.base_mass)] + [(p["body"], args.door_mass) for p in parts]:
        x = UsdGeom.Xform.Define(stage, f"{rootp}/{b}")
        if b != "base":
            x.AddTranslateOp().Set(Gf.Vec3d(*offset[b].tolist()))
        UsdPhysics.RigidBodyAPI.Apply(x.GetPrim())
        UsdPhysics.MassAPI.Apply(x.GetPrim()).CreateMassAttr().Set(float(mass))
        UsdGeom.Xform.Define(stage, f"{rootp}/{b}/visual")
        bodies[b] = x.GetPrim()
    for p in parts:
        UsdPhysics.FilteredPairsAPI.Apply(bodies[p["body"]]).CreateFilteredPairsRel().AddTarget(
            bodies["base"].GetPath())
    hooked = {p["handle_id"]: p for p in parts if p["hinfo"].get("hookable")}
    pinched = {p["handle_id"]: p for p in parts if p["handle_id"] is not None and not p["hinfo"].get("hookable")}
    pinch_pts = {}                          # body -> handle vertices (one hull, front pinch)

    # materials (UsdPreviewSurface, textures copied next to the asset)
    looks, mat_cache = UsdGeom.Scope.Define(stage, f"{rootp}/Looks"), {}

    def material(m, mtl_dir):
        kd = tuple(round(c, 4) for c in (m or {}).get("Kd", [0.8, 0.8, 0.8]))
        tex = (m or {}).get("map_Kd")
        key = (kd, tex and str(Path(mtl_dir) / tex))
        if key in mat_cache:
            return mat_cache[key]
        mp = f"{looks.GetPath()}/mat_{len(mat_cache)}"
        mat = UsdShade.Material.Define(stage, mp)
        sh = UsdShade.Shader.Define(stage, mp + "/surface")
        sh.CreateIdAttr("UsdPreviewSurface")
        sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.6)
        if tex:
            src = (Path(f"{args.id}") / mtl_dir / tex).as_posix()
            src = re.sub(r"[^/]+/\.\./", "", src)
            name = Path(src).name
            (d / "textures" / name).write_bytes(zf.read(src))
            st = UsdShade.Shader.Define(stage, mp + "/st")
            st.CreateIdAttr("UsdPrimvarReader_float2")
            st.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
            tx = UsdShade.Shader.Define(stage, mp + "/tex")
            tx.CreateIdAttr("UsdUVTexture")
            tx.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(f"./textures/{name}")
            tx.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(st.ConnectableAPI(), "result")
            tx.CreateInput("wrapS", Sdf.ValueTypeNames.Token).Set("repeat")
            tx.CreateInput("wrapT", Sdf.ValueTypeNames.Token).Set("repeat")
            tx.CreateInput("scale", Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(*kd, 1.0))
            sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(tx.ConnectableAPI(), "rgb")
        else:
            sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*kd))
        mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
        mat_cache[key] = mat
        return mat

    def mesh(path, pts, faces, st=None):
        m = UsdGeom.Mesh.Define(stage, path)
        m.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*p) for p in pts.tolist()]))
        m.CreateFaceVertexCountsAttr([len(f) for f in faces])
        m.CreateFaceVertexIndicesAttr([int(i) for f in faces for i in f])
        m.CreateSubdivisionSchemeAttr("none")
        m.CreateDoubleSidedAttr(True)
        if st is not None:
            pv = UsdGeom.PrimvarsAPI(m).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray,
                                                     UsdGeom.Tokens.faceVarying)
            pv.Set(Vt.Vec2fArray([Gf.Vec2f(*u) for u in st.tolist()]))
        lo, hi = pts.min(0), pts.max(0)
        m.CreateExtentAttr([Gf.Vec3f(*lo.tolist()), Gf.Vec3f(*hi.tolist())])
        return m

    def collider(path, pts, faces=None):
        """Invisible convex-hull collider (hull computed here, so its bounds are exact)."""
        if faces is None:
            h = trimesh.Trimesh(pts).convex_hull
            pts, faces = h.vertices, h.faces.tolist()
        m = mesh(path, np.asarray(pts, float), faces)
        m.CreateVisibilityAttr("invisible")
        UsdPhysics.CollisionAPI.Apply(m.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(m.GetPrim()).CreateApproximationAttr().Set("convexHull")
        return m

    def box(path, lo, hi):
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        c = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        return collider(path, c)

    names = {}

    def uniq(parent, n):
        k = names.get((parent, n), 0)
        names[(parent, n)] = k + 1
        return n if k == 0 else f"{n}_{k}"

    for i, e in enumerate(elems):
        b = e["body"]
        v = e["v"] - offset[b]
        # visual: one mesh per material group
        for g, (mname, faces) in enumerate(e["groups"]):
            used = sorted({vi for f in faces for vi, _ in f})
            remap = {vi: j for j, vi in enumerate(used)}
            st = None
            if len(e["vt"]) and all(ti is not None for f in faces for _, ti in f):
                st = np.array([e["vt"][ti] for f in faces for _, ti in f])
            vm = mesh(f"{rootp}/{b}/visual/e{i:03d}_{g}", v[used], [[remap[vi] for vi, _ in f] for f in faces], st)
            UsdShade.MaterialBindingAPI.Apply(vm.GetPrim()).Bind(material(e["mtl"].get(mname), e["mtl_dir"]))
        if e["part_id"] in hooked and hooked[e["part_id"]]["body"] == b:
            continue                        # replaced by the bar + standoff boxes below
        if e["part_id"] in pinched and pinched[e["part_id"]]["body"] == b:
            pinch_pts.setdefault(b, []).append(e["v"])      # one "handle" hull below
            continue
        role = ROLES.get(e["part"], re.sub(r"[^a-z0-9_]", "_", e["part"].lower()))
        if role == "handle":
            role = "handle_part"             # only the hooked bar is called "handle"
        used = sorted({vi for _, faces in e["groups"] for f in faces for vi, _ in f})
        pc = e["v"][used].copy()
        if b != "base":
            # PartNet doors reach the floor: a moving part touching the floor
            # or a rug locks the joint.  Colliders keep a gap, visuals do not.
            pc[:, 2] = np.maximum(pc[:, 2], args.floor_gap)
        pc -= offset[b]
        if len(used) >= 4 and np.linalg.matrix_rank(pc - pc.mean(0), tol=1e-5) == 3:
            collider(f"{rootp}/{b}/{uniq(b, role)}", pc)
    from zeno_skills.physics import fix_articulation
    UsdGeom.Scope.Define(stage, f"{rootp}/joints")
    for p in parts:
        b, pv, h = p["body"], p["pivot"], p["hinfo"]
        if h.get("hookable"):
            bar = box(f"{rootp}/{b}/handle", *(np.asarray(h["bar"]) - pv))
            # the bar's long axis (part frame): the side hook slides across it
            bar.GetPrim().CreateAttribute("zeno:bar_axis", Sdf.ValueTypeNames.Float3).Set(
                Gf.Vec3f(*np.eye(3)["xyz".index(h["long_axis"])].tolist()))
            bar.GetPrim().CreateAttribute("zeno:outward", Sdf.ValueTypeNames.Float3).Set(Gf.Vec3f(0.0, -1.0, 0.0))
            for k, (lo, hi) in enumerate(h["standoffs"]):
                box(f"{rootp}/{b}/handle_standoff_{k}", np.asarray(lo) - pv, np.asarray(hi) - pv)
        elif b in pinch_pts:
            # round / short pull (rigid on the part): its hull is the handle, zeno:grasp = front
            hp = np.concatenate(pinch_pts[b])
            hp[:, 2] = np.maximum(hp[:, 2], args.floor_gap)
            hc = collider(f"{rootp}/{b}/handle", hp - pv)
            hc.GetPrim().CreateAttribute("zeno:bar_axis", Sdf.ValueTypeNames.Float3).Set(
                Gf.Vec3f(*np.eye(3)["xyz".index(h["long_axis"])].tolist()))
            hc.GetPrim().CreateAttribute("zeno:outward", Sdf.ValueTypeNames.Float3).Set(Gf.Vec3f(0.0, -1.0, 0.0))
            hc.GetPrim().CreateAttribute("zeno:grasp", Sdf.ValueTypeNames.String).Set("front")
        J = (UsdPhysics.RevoluteJoint if p["rev"] else UsdPhysics.PrismaticJoint).Define(
            stage, f"{rootp}/joints/{p['joint_name']}")
        J.CreateBody0Rel().SetTargets([bodies["base"].GetPath()])
        J.CreateBody1Rel().SetTargets([bodies[b].GetPath()])
        J.CreateLocalPos0Attr().Set(Gf.Vec3f(*pv.tolist()))
        J.CreateLocalRot0Attr().Set(Gf.Quatf(1.0))
        J.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0))
        J.CreateLocalRot1Attr().Set(Gf.Quatf(1.0))
        J.CreateAxisAttr("XYZ"[p["ai"]])
        lo_l, hi_l = p["limits"]
        if p["rev"]:
            lo_l, hi_l = math.degrees(lo_l), math.degrees(hi_l)
        J.CreateLowerLimitAttr().Set(lo_l)
        J.CreateUpperLimitAttr().Set(hi_l)
        fix_articulation(stage, str(J.GetPath()))
    rj = UsdPhysics.FixedJoint.Define(stage, f"{rootp}/root_joint")
    rj.CreateBody1Rel().SetTargets([bodies["base"].GetPath()])
    rj.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0))
    rj.CreateLocalRot0Attr().Set(Gf.Quatf(1.0))
    UsdPhysics.ArticulationRootAPI.Apply(rj.GetPrim())
    pa = PhysxSchema.PhysxArticulationAPI.Apply(rj.GetPrim())
    pa.CreateEnabledSelfCollisionsAttr().Set(False)
    pa.CreateSolverPositionIterationCountAttr().Set(32)
    pa.CreateSolverVelocityIterationCountAttr().Set(1)
    stage.GetRootLayer().Save()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True, help="PartNet-Mobility model id")
    ap.add_argument("--name", required=True)
    ap.add_argument("--height", type=float, required=True, help="real height of the object, m")
    ap.add_argument("--root", default="/data/PartNetMobility", help="directory with <id>.zip")
    ap.add_argument("--base-mass", type=float, default=20.0)
    ap.add_argument("--door-mass", type=float, default=3.0)
    ap.add_argument("--floor-gap", type=float, default=0.015, help="m under the moving part's colliders")
    ap.add_argument("--keep-continuous", action="store_true",
                    help="continuous joints (knobs, wheels) become parts too; default: fixed")
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT))
    from isaaclab.app import AppLauncher
    AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True})
    build(args)
    import os
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
