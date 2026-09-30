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
    door               rigid body with its origin on the joint: visual/, panel colliders, the
                       handle bar ("handle", a box) and its standoffs ("handle_standoff_<k>")
    joints/door_hinge  revolute (drawers: joints/drawer_slide, prismatic), closed at q = 0
    root_joint         fixed joint to the world (articulation root), posed by place_partnet.py

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


def handle_geometry(H, face_n, n_dir, long_ax):
    """Bar box + standoff boxes of a handle mesh (asset frame, closed).

    H: trimesh of the handle; face_n: panel front at x . n_dir = face_n;
    long_ax: 0 (x) or 2 (z), the handle's long axis.  Returns dict with
    bar [lo, hi], standoffs [[lo, hi], ...], gap, thickness, length."""
    n_hi = float((H.vertices @ n_dir).max())
    L = float(np.ptp(H.vertices[:, long_ax]))
    levels = np.arange(face_n + 0.0005, n_hi - 0.0005, 0.0005)
    cov = []
    for lv in levels:
        ints = sorted((float(lp[:, long_ax].min()), float(lp[:, long_ax].max())) for lp in _loops(H, n_dir, lv))
        tot, end = 0.0, -1e9
        for a, b in ints:          # union length of the loops along the handle
            if b > end:
                tot += b - max(a, end)
                end = b
        cov.append(tot / max(L, 1e-9))
    cov = np.array(cov)
    bar = np.nonzero(cov >= 0.8)[0]
    if len(bar) == 0:
        return {"hookable": False, "reason": "no level spans the handle"}
    bar_lo = float(levels[bar[0]])
    gap = bar_lo - face_n
    other = 2 if long_ax == 0 else 0
    pts = np.concatenate([lp for lv in levels[bar] for lp in _loops(H, n_dir, lv)])
    sign = int(np.argmax(np.abs(n_dir)))
    lo, hi = pts.min(0), pts.max(0)
    # the bar spans [bar_lo, n_hi] along the outward normal
    lo_n, hi_n = sorted((bar_lo * n_dir[sign], n_hi * n_dir[sign]))
    lo[sign], hi[sign] = lo_n, hi_n
    standoffs = []
    if gap > 0.002:
        for lp in _loops(H, n_dir, face_n + gap / 2):
            a, b = lp.min(0), lp.max(0)
            s_lo, s_hi = sorted((face_n * n_dir[sign], (bar_lo + 0.001) * n_dir[sign]))
            a[sign], b[sign] = s_lo, s_hi
            standoffs.append([a.tolist(), b.tolist()])
    t = n_hi - bar_lo
    ok = gap >= PAD + 0.008 and float(hi[long_ax] - lo[long_ax]) >= 0.06
    return {"hookable": bool(ok), "reason": "" if ok else f"gap {gap:.3f} m / length too small",
            "bar": [lo.tolist(), hi.tolist()], "standoffs": standoffs, "gap": round(gap, 4),
            "thickness": round(t, 4), "length": round(float(hi[long_ax] - lo[long_ax]), 4),
            "long_axis": "xyz"[long_ax]}


# ---------------------------------------------------------------- main
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
    movable = [j for j in joints if j.get("type") in ("revolute", "continuous", "prismatic")]
    if len(movable) != 1:
        raise SystemExit(f"{args.id}: {len(movable)} movable joints; only single-joint objects are supported "
                         "(zeno_skills.rig reads one DOF per articulation)")
    J = movable[0]
    part_link = J.find("child").get("link")

    def world(link):
        T = np.eye(4)
        while link in parent:
            j = parent[link]
            T = T_of(j.find("origin")) @ T
            link = j.find("parent").get("link")
        return T

    def body_of(link):
        while link in parent:
            if parent[link] is J:
                return "door"
            link = parent[link].find("parent").get("link")
        return "base"

    # every visual element: (body, part name, role, obj text, transform to Z-up world)
    elems = []
    for L in urdf.findall("link"):
        for vis in L.findall("visual"):
            fn = vis.find("geometry/mesh").get("filename")
            pname = re.sub(r"-\d+$", "", vis.get("name") or "part")
            elems.append({"body": body_of(L.get("name")), "part": pname, "part_id": vis.get("name"),
                          "file": fn, "T": world(L.get("name")) @ T_of(vis.find("origin"))})
    for e in elems:
        v, vt, groups, mtllib = parse_obj(zf.read(f"{args.id}/{e['file']}").decode())
        e.update(v=(e["T"][:3, :3] @ v.T).T + e["T"][:3, 3], vt=vt, groups=groups)
        mtl = Path(e["file"]).parent / mtllib if mtllib else None
        e["mtl"] = parse_mtl(zf.read(f"{args.id}/{mtl}").decode()) if mtl else {}
        e["mtl_dir"] = str(mtl.parent) if mtl else ""

    # canonical frame: the moving part's side of the object faces -y
    allv = np.concatenate([e["v"] for e in elems])
    base_c = np.concatenate([e["v"] for e in elems if e["body"] == "base"]).mean(0)
    part_v = np.concatenate([e["v"] for e in elems if e["body"] == "door"])
    d = part_v.mean(0) - base_c
    d[2] = 0.0
    k = int(np.argmax(np.abs(d[:2])))
    out_dir = np.zeros(3)
    out_dir[k] = np.sign(d[k])
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

    # joint in the asset frame
    Tc = world(part_link)
    pivot = A[:3, :3] @ Tc[:3, 3] + A[:3, 3]
    axis = R[:3, :3] @ Tc[:3, :3] @ np.array([float(x) for x in J.find("axis").get("xyz").split()])
    ai = int(np.argmax(np.abs(axis)))
    if abs(axis[ai]) < 0.98:
        raise SystemExit(f"{args.id}: joint axis {axis.round(3)} is not along x/y/z")
    sgn = float(np.sign(axis[ai]))
    lim = J.find("limit")               # continuous joints have none
    lo_l, hi_l = (0.0, 0.0) if lim is None else (float(lim.get("lower", 0)), float(lim.get("upper", 0)))
    if J.get("type") == "continuous":
        lo_l, hi_l = 0.0, math.pi
    rev = J.get("type") != "prismatic"
    if not rev:
        lo_l, hi_l = lo_l * s, hi_l * s
    if sgn < 0:                      # joint about +axis: q -> -q
        lo_l, hi_l = -hi_l, -lo_l
    if not (lo_l - 1e-6 <= 0.0 <= hi_l + 1e-6):
        raise SystemExit(f"{args.id}: q = 0 (the mesh pose) is outside the limits [{lo_l}, {hi_l}]")

    # handle: the part farthest from the hinge (revolute) of the moving body
    n_dir = np.array([0.0, -1.0, 0.0])
    handles = {}
    for e in elems:
        if e["body"] == "door" and e["part"] == "handle":
            handles.setdefault(e["part_id"], []).append(e)
    hinfo, handle_id = {"hookable": False, "reason": "no handle part"}, None
    if handles:
        def hmesh(es):
            return trimesh.util.concatenate([trimesh.Trimesh(e["v"], [
                [f[0][0], f[i][0], f[i + 1][0]] for f in (ff for g in e["groups"] for ff in g[1])
                for i in range(1, len(f) - 1)], process=True) for e in es])
        cand = {hid: hmesh(es) for hid, es in handles.items()}

        def far(hid):
            c = cand[hid].bounds.mean(0)
            return np.linalg.norm((c - pivot)[[0, 1]]) if rev else -abs(c[2] - pivot[2])
        handle_id = max(cand, key=far)
        H = cand[handle_id]
        panel = np.concatenate([e["v"] for e in elems if e["body"] == "door" and e["part"] != "handle"])
        hb = H.bounds
        near = np.all((panel[:, [0, 2]] > hb[0, [0, 2]] - 0.03) & (panel[:, [0, 2]] < hb[1, [0, 2]] + 0.03), axis=1)
        face_n = float(((panel[near] if near.any() else panel) @ n_dir).max())
        long_ax = 0 if np.ptp(H.vertices[:, 0]) > np.ptp(H.vertices[:, 2]) else 2
        hinfo = handle_geometry(H, face_n, n_dir, long_ax)
        hinfo["part"] = handle_id

    write_usd(args, meta, elems, pivot, ai, lo_l, hi_l, rev, hinfo, handle_id, zf)
    size = (hi - lo).round(4).tolist()
    info = {"source": f"PartNet-Mobility {args.id}", "category": meta.get("model_cat"), "name": args.name,
            "scale": round(s, 5), "yaw_deg": round(math.degrees(yaw), 2), "size": size,
            "joint": {"type": "revolute" if rev else "prismatic", "axis": "XYZ"[ai],
                      "pivot": pivot.round(4).tolist(), "limits": [round(lo_l, 4), round(hi_l, 4)]},
            "handle": {k: v for k, v in hinfo.items() if k not in ("bar", "standoffs")},
            "usd": str((OUT / args.name / f"{args.name}.usd").relative_to(ROOT))}
    (OUT / args.name / "import.json").write_text(json.dumps(info, indent=1))
    print("IMPORTED", json.dumps(info), flush=True)


def write_usd(args, meta, elems, pivot, ai, lo_l, hi_l, rev, hinfo, handle_id, zf):
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
    offset = {"base": np.zeros(3), "door": pivot}
    bodies = {}
    for b, mass in (("base", args.base_mass), ("door", args.door_mass)):
        x = UsdGeom.Xform.Define(stage, f"{rootp}/{b}")
        if b == "door":
            x.AddTranslateOp().Set(Gf.Vec3d(*pivot.tolist()))
        UsdPhysics.RigidBodyAPI.Apply(x.GetPrim())
        UsdPhysics.MassAPI.Apply(x.GetPrim()).CreateMassAttr().Set(float(mass))
        UsdGeom.Xform.Define(stage, f"{rootp}/{b}/visual")
        bodies[b] = x.GetPrim()
    UsdPhysics.FilteredPairsAPI.Apply(bodies["door"]).CreateFilteredPairsRel().AddTarget(bodies["base"].GetPath())

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
        if e["part_id"] == handle_id and hinfo.get("hookable"):
            continue                        # replaced by the bar + standoff boxes below
        role = ROLES.get(e["part"], re.sub(r"[^a-z0-9_]", "_", e["part"].lower()))
        if role == "handle":
            role = "handle_part"             # only the hooked bar is called "handle"
        used = sorted({vi for _, faces in e["groups"] for f in faces for vi, _ in f})
        pc = e["v"][used].copy()
        if b == "door":
            # PartNet doors reach the floor: a moving part touching the floor
            # or a rug locks the joint.  Colliders keep a gap, visuals do not.
            pc[:, 2] = np.maximum(pc[:, 2], args.floor_gap)
        pc -= offset[b]
        if len(used) >= 4 and np.linalg.matrix_rank(pc - pc.mean(0), tol=1e-5) == 3:
            collider(f"{rootp}/{b}/{uniq(b, role)}", pc)
    if hinfo.get("hookable"):
        box(f"{rootp}/door/handle", *(np.asarray(hinfo["bar"]) - pivot))
        for k, (lo, hi) in enumerate(hinfo["standoffs"]):
            box(f"{rootp}/door/handle_standoff_{k}", np.asarray(lo) - pivot, np.asarray(hi) - pivot)

    jn = "door_hinge" if rev else "drawer_slide"
    UsdGeom.Scope.Define(stage, f"{rootp}/joints")
    J = (UsdPhysics.RevoluteJoint if rev else UsdPhysics.PrismaticJoint).Define(stage, f"{rootp}/joints/{jn}")
    J.CreateBody0Rel().SetTargets([bodies["base"].GetPath()])
    J.CreateBody1Rel().SetTargets([bodies["door"].GetPath()])
    J.CreateLocalPos0Attr().Set(Gf.Vec3f(*pivot.tolist()))
    J.CreateLocalRot0Attr().Set(Gf.Quatf(1.0))
    J.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0))
    J.CreateLocalRot1Attr().Set(Gf.Quatf(1.0))
    J.CreateAxisAttr("XYZ"[ai])
    if rev:
        J.CreateLowerLimitAttr().Set(math.degrees(lo_l))
        J.CreateUpperLimitAttr().Set(math.degrees(hi_l))
    else:
        J.CreateLowerLimitAttr().Set(lo_l)
        J.CreateUpperLimitAttr().Set(hi_l)
    from zeno_skills.physics import fix_articulation
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
