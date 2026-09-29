"""Cut doorways into the house walls (visual + collision meshes).

The Infinigen export has no opening between the living room and the
bedroom (and only a 30 cm slit into the west corridor): every room shell is
closed at wall height, so the bedroom half of the house (bedroom desk,
bookcases, toy box) and the corridor (study desk) were unreachable for the
robot and for the base planner.  This clips every triangle of both rooms' wall shells
against a door box, keeps the parts outside it (UVs interpolated), and writes
the result as overrides in sim/zeno_house.usd.  Then the wall segments of
annotations/house_static.json are re-extracted from the new collision meshes.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/cut_doorway.py
    # then: tools/annotate_scene.py sim/zeno_house.usd annotations/zeno_house.json
    #       and rebuild the task layers (tools/make_tasks.sh)

Idempotent: a doorway whose box no longer intersects any wall is skipped.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "sim/zeno_house.usd"
STATIC = ROOT / "annotations/house_static.json"
BASE = "/World/House/Asset/base/"

# world boxes [x0, y0, z0, x1, y1, z1]; z0 above 0 keeps the floor slab
DOORS = {
    "living_room_to_bedroom": {"box": [2.10, -0.35, 0.005, 3.00, 0.40, 2.10],
                               "rooms": ["living_room_0_0", "bedroom_0_1"]},
    # the west corridor (study desk) only had a 30 cm slit
    "living_room_to_west_corridor": {"box": [-5.45, 0.90, 0.005, -4.40, 1.90, 2.10],
                                     "rooms": ["living_room_0_0", "living_room_0_1"]},
}


def clip_polygon(poly, attrs, axis, value, keep_below):
    """Split a convex polygon by the plane x[axis] = value.  Returns
    (kept, kept_attrs) for the side keep_below (x <= value) or above."""
    out, out_a = [], []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        a, b = attrs[i], attrs[(i + 1) % n]
        pin = (p[axis] <= value) if keep_below else (p[axis] >= value)
        qin = (q[axis] <= value) if keep_below else (q[axis] >= value)
        if pin:
            out.append(p)
            out_a.append(a)
        if pin != qin:
            t = (value - p[axis]) / (q[axis] - p[axis])
            out.append(p + t * (q - p))
            out_a.append(a + t * (b - a))
    return out, out_a


def cut_box(tris, uvs, lo, hi):
    """Remove the part of every triangle inside the box [lo, hi]; returns
    convex polygons (with per-corner uvs) covering the rest."""
    keep_p, keep_a = [], []
    for tri, uv in zip(tris, uvs):
        tmin, tmax = tri.min(0), tri.max(0)
        if np.any(tmax < lo) or np.any(tmin > hi):
            keep_p.append(list(tri))
            keep_a.append(list(uv))
            continue
        poly, att = list(tri), list(uv)
        for axis in range(3):
            for value, below in ((lo[axis], True), (hi[axis], False)):
                if len(poly) < 3:
                    break
                outside, oa = clip_polygon(poly, att, axis, value, below)
                if len(outside) >= 3:
                    keep_p.append(outside)
                    keep_a.append(oa)
                poly, att = clip_polygon(poly, att, axis, value, not below)
        # what is left of poly is inside the box: dropped
    return keep_p, keep_a


def main():
    from isaaclab.app import AppLauncher
    AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True})
    from pxr import Gf, Usd, UsdGeom, Vt
    import trimesh

    stage = Usd.Stage.Open(str(SCENE))
    cache = UsdGeom.XformCache()
    changed = 0
    for door, spec in DOORS.items():
        box = np.asarray(spec["box"], float)
        for room in spec["rooms"]:
            for group, suffix in (("visuals/", "_exterior_openroof_wideopen"),
                                  ("collisions/", "_exterior_collision_openroof_wideopen")):
                root = stage.GetPrimAtPath(BASE + group + room + suffix)
                for prim in Usd.PrimRange(root):
                    if not prim.IsA(UsdGeom.Mesh):
                        continue
                    mesh = UsdGeom.Mesh(prim)
                    M = np.array(cache.GetLocalToWorldTransform(prim)).T
                    Minv = np.linalg.inv(M)
                    corners = np.array([[x, y, z, 1.0] for x in box[[0, 3]] for y in box[[1, 4]] for z in box[[2, 5]]])
                    loc = (Minv @ corners.T).T[:, :3]
                    lo, hi = loc.min(0), loc.max(0)
                    pts = np.array(mesh.GetPointsAttr().Get(), float)
                    fvc = np.array(mesh.GetFaceVertexCountsAttr().Get())
                    fvi = np.array(mesh.GetFaceVertexIndicesAttr().Get())
                    assert (fvc == 3).all(), prim.GetPath()
                    tris = pts[fvi].reshape(-1, 3, 3)
                    # strict overlap (1 mm): pieces left by an earlier cut only touch the box
                    if not np.any(np.all((tris.max(1) > lo + 1e-3) & (tris.min(1) < hi - 1e-3), axis=1)):
                        print("SKIP", door, prim.GetPath(), "(no wall in the box)")
                        continue
                    st = UsdGeom.PrimvarsAPI(prim).GetPrimvar("st")
                    has_st = bool(st) and st.Get() is not None and st.GetInterpolation() == "faceVarying"
                    uv = np.array(st.Get(), float).reshape(-1, 3, 2) if has_st else np.zeros((len(tris), 3, 2))
                    polys, puv = cut_box(tris, uv, lo, hi)
                    new_pts, new_uv, counts = [], [], []
                    for p, a in zip(polys, puv):          # fan-triangulate the convex pieces
                        for k in range(1, len(p) - 1):
                            new_pts += [p[0], p[k], p[k + 1]]
                            new_uv += [a[0], a[k], a[k + 1]]
                            counts.append(3)
                    new_pts = np.array(new_pts)
                    mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*map(float, v)) for v in new_pts]))
                    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray(counts))
                    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(list(range(len(new_pts)))))
                    if has_st:
                        st.Set(Vt.Vec2fArray([Gf.Vec2f(*map(float, v)) for v in new_uv]))
                    ext = mesh.GetExtentAttr()
                    if ext and ext.Get() is not None:
                        ext.Set(Vt.Vec3fArray([Gf.Vec3f(*map(float, new_pts.min(0))), Gf.Vec3f(*map(float, new_pts.max(0)))]))
                    print("CUT", door, prim.GetPath(), f"{len(tris)} -> {len(counts)} triangles", flush=True)
                    changed += 1
    if changed:
        stage.GetRootLayer().Save()

    # wall segments for the planner: z = 0.5 section of every collision shell
    segs = []
    for c in stage.GetPrimAtPath(BASE + "collisions").GetChildren():
        if "exterior" not in c.GetName():
            continue
        for prim in Usd.PrimRange(c):
            if not prim.IsA(UsdGeom.Mesh):
                continue
            mesh = UsdGeom.Mesh(prim)
            M = np.array(cache.GetLocalToWorldTransform(prim)).T
            pts = np.array(mesh.GetPointsAttr().Get(), float)
            W = (M[:3, :3] @ pts.T).T + M[:3, 3]
            fvi = np.array(mesh.GetFaceVertexIndicesAttr().Get()).reshape(-1, 3)
            tm = trimesh.Trimesh(W, fvi, process=False)
            sec = tm.section(plane_origin=[0, 0, 0.5], plane_normal=[0, 0, 1])
            if sec is None:
                continue
            for ent in sec.entities:
                q = sec.vertices[ent.points][:, :2]
                for a, b in zip(q[:-1], q[1:]):
                    if np.linalg.norm(b - a) > 0.02:
                        segs.append([round(float(v), 3) for v in (*a, *b)])
    static = json.loads(STATIC.read_text())
    print("WALLS", len(static["walls"]), "->", len(segs))
    static["walls"] = segs
    static["doorways"] = {k: v["box"] for k, v in DOORS.items()}
    STATIC.write_text(json.dumps(static))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
