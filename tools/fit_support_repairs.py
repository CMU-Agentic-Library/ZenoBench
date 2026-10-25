"""Lay a collider slab on every support layer of the static furniture (annotations/support_layers.json).

Infinigen's collision mesh of a furniture piece is a separate, simplified mesh: its
boards are not where the rendered boards are (TV stand top: rendered 0.485,
collision 0.472; cell shelf floor: rendered 0.046, collision a wave 0.06-0.10;
kitchen counter: rendered 1.000, collision 1.009 and 5 cm narrower), and it has
upward strips no rendered board has. This tool makes physics match rendering for
each listed layer:

* the layer height is snapped to the rendered board top within 2 cm of the listed
  height (fit_layers); the slab is the box of the board's top faces, 2 cm thick, invisible (the rendered mesh is what shows), named
  /World/SupportRepairs/<furniture>__<layer> with customData zeno:support,
  zeno:category and zeno:clearance (to the next rendered board above it, 1.0 when
  open) that tools/annotate_scene.py reads;
* collision faces reaching into the space a layer keeps free (the slab's footprint
  1 cm inset, from 3 mm above the slab to 3 mm below the next rendered board, or 1 m
  up when open) are removed from the furniture's collision mesh when they are not
  vertical (|n_z| > 0.5), so nothing invisible lies on or hovers over a board.
  Vertical faces stay: panels and cubby dividers cross the footprint, and the
  collision mesh places some of them centimetres off the rendered ones, so a test
  against the rendering cannot tell a divider from a stray face. The faces under a
  slab stay too: the slab covers them.

Slabs of layers no longer listed are removed. Each run rebuilds the collision face
lists from the referenced meshes, so it is idempotent and furniture whose layers
are dropped gets its faces back.  Objects resting on a moved board are shifted by
tools/shift_supported_objects.py.

    $USD_PY tools/fit_support_repairs.py [--dry-run]     # edits sim/zeno_house.usd
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HOUSE = ROOT / "sim/zeno_house.usd"
BASE = "/World/House/Asset/base"
LAYERS = ROOT / "annotations/support_layers.json"
NAMES = ROOT / "annotations/furniture_names.json"
STATIC = ROOT / "annotations/house_static.json"
SNAP = 0.02          # listed height -> rendered board top
FOOT = 0.004         # upward faces within this of the board top give the slab box
THICK = 0.02         # slab thickness below the board top
INSET = 0.01         # kept-free space: slab footprint inset, and
GAP = 0.003          # its distance from the slab top and the next board


def triangles(stage, path):
    from pxr import Usd, UsdGeom
    out = []
    for m in Usd.PrimRange(stage.GetPrimAtPath(path)):
        if not m.IsA(UsdGeom.Mesh):
            continue
        M = np.array(UsdGeom.Xformable(m).ComputeLocalToWorldTransform(0)).T
        mesh = UsdGeom.Mesh(m)
        V = np.array(mesh.GetPointsAttr().Get(), float)
        V = V @ M[:3, :3].T + M[:3, 3]
        C = np.array(mesh.GetFaceVertexCountsAttr().Get())
        I = np.array(mesh.GetFaceVertexIndicesAttr().Get())
        for o, c in zip(np.r_[0, np.cumsum(C)[:-1]], C):
            out += [V[[I[o], I[o + j], I[o + j + 1]]] for j in range(1, c - 1)]
    return np.array(out)


def heights_at(T, x, y):
    """Heights of the triangles T above (x, y)."""
    a, b, c = T[:, 0, :2], T[:, 1, :2], T[:, 2, :2]
    d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    ok = np.abs(d) > 1e-12
    d = np.where(ok, d, 1.0)
    l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / d
    l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / d
    inside = ok & (l1 >= -1e-6) & (l2 >= -1e-6) & (1 - l1 - l2 >= -1e-6)
    z = l1 * T[:, 0, 2] + l2 * T[:, 1, 2] + (1 - l1 - l2) * T[:, 2, 2]
    return z[inside]


def normals_z(T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    return n[:, 2] / (np.linalg.norm(n, axis=1) + 1e-12)


def grid(lo, hi, inset=0.02, step=0.05):
    xs = np.linspace(lo[0] + inset, hi[0] - inset, max(2, int((hi[0] - lo[0]) / step) + 1))
    ys = np.linspace(lo[1] + inset, hi[1] - inset, max(2, int((hi[1] - lo[1]) / step) + 1))
    return [(x, y) for x in xs for y in ys]


def fit_layers(V, layers):
    """{layer: (lo xyz, hi xyz, clearance)} of the slabs on the rendered boards V.

    Horizontal faces of either winding: several Infinigen tops (both dining tables,
    the kitchen counters) have their upper face wound downward. Near the listed
    height a board shows as its top and bottom faces plus thin rims and leg ends;
    the board top is the highest 3 mm height bin holding at least 30 % of the
    largest bin's area."""
    flat = V[np.abs(normals_z(V)) > 0.97]
    zc = flat[:, :, 2].mean(1)
    n = np.cross(flat[:, 1] - flat[:, 0], flat[:, 2] - flat[:, 0])
    area = np.linalg.norm(n, axis=1) / 2
    out = {}
    for layer, z_hint in layers.items():
        near = np.abs(zc - z_hint) <= SNAP
        if not near.any():
            raise ValueError(f"{layer}: no rendered board within {SNAP} m of {z_hint}")
        bins = np.round(zc[near] / 0.003).astype(int)
        acc = {b: area[near][bins == b].sum() for b in set(bins.tolist())}
        main = max(b for b, a in acc.items() if a >= 0.3 * max(acc.values()))
        top = float(zc[near][bins == main].max())
        board = flat[near & (np.abs(zc - top) <= FOOT)].reshape(-1, 3)
        lo, hi = board.min(0), board.max(0)
        # clearance: lowest horizontal rendered face over the board's middle, 3 cm or more
        # above it (closer ones are the board's own rims and bulges)
        above = [h for x, y in grid(lo, hi, inset=0.05) for h in heights_at(flat, x, y) if h > top + 0.03]
        clear = round(min(above) - top, 3) if above else 1.0
        out[layer] = (np.r_[lo[:2], top - THICK], np.r_[hi[:2], top], clear)
    return out


def tri_box_overlap(T, lo, hi):
    """Which triangles T (n, 3, 3) intersect the box [lo, hi] (separating axis test)."""
    c, h = (lo + hi) / 2, (hi - lo) / 2
    v = T - c
    e = np.stack([v[:, 1] - v[:, 0], v[:, 2] - v[:, 1], v[:, 0] - v[:, 2]], 1)
    axes = [np.broadcast_to(a, (len(T), 3)) for a in np.eye(3)]
    axes.append(np.cross(e[:, 0], e[:, 1]))
    axes += [np.cross(e[:, i], a) for i in range(3) for a in np.eye(3)]
    sep = np.zeros(len(T), bool)
    for ax in axes:
        p = np.einsum("nkj,nj->nk", v, ax)
        r = np.abs(ax) @ h
        sep |= (p.min(1) > r + 1e-9) | (p.max(1) < -r - 1e-9)
    return ~sep


def free_boxes(slabs):
    """The space each layer keeps free of collision faces, as boxes."""
    return [(np.r_[lo[:2] + INSET, hi[2] + GAP], np.r_[hi[:2] - INSET, hi[2] + clear - GAP])
            for lo, hi, clear in slabs.values()]


def clear_faces(stage, coll_path, slabs):
    """Drop the non-vertical collision faces inside the layers' free space:
    {mesh prim: (kept face mask, counts, indices, face starts)}."""
    from pxr import Usd, UsdGeom
    out = {}
    for m in Usd.PrimRange(stage.GetPrimAtPath(coll_path)):
        if not m.IsA(UsdGeom.Mesh):
            continue
        mesh = UsdGeom.Mesh(m)
        for a in (mesh.GetFaceVertexCountsAttr(), mesh.GetFaceVertexIndicesAttr()):
            a.Clear()                                   # the referenced faces, not the last run's
        M = np.array(UsdGeom.Xformable(m).ComputeLocalToWorldTransform(0)).T
        X = np.array(mesh.GetPointsAttr().Get(), float) @ M[:3, :3].T + M[:3, 3]
        C = np.array(mesh.GetFaceVertexCountsAttr().Get())
        I = np.array(mesh.GetFaceVertexIndicesAttr().Get())
        start = np.r_[0, np.cumsum(C)[:-1]]
        tri, face = [], []
        for f, (o, c) in enumerate(zip(start, C)):
            for j in range(1, c - 1):
                tri.append(X[[I[o], I[o + j], I[o + j + 1]]])
                face.append(f)
        tri, face = np.array(tri), np.array(face)
        inside = np.zeros(len(tri), bool)
        for lo, hi in free_boxes(slabs):
            inside |= tri_box_overlap(tri, lo, hi)
        hit = inside & (np.abs(normals_z(tri)) > 0.5)
        keep = np.ones(len(C), bool)
        keep[face[hit]] = False
        out[m.GetPath()] = (keep, C, I, start)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics
    spec = json.loads(LAYERS.read_text())["layers"]
    prim_of = {v: k for k, v in json.loads(NAMES.read_text())["names"].items()}
    category = {f["name"]: f["category"] for f in json.loads(STATIC.read_text())["furniture"]}
    stage = Usd.Stage.Open(str(HOUSE))
    root = stage.DefinePrim("/World/SupportRepairs")
    made = set()
    for furniture, layers in spec.items():
        prim = prim_of[furniture]
        slabs = fit_layers(triangles(stage, f"{BASE}/visuals/{prim}"), layers)
        cleared = clear_faces(stage, f"{BASE}/collisions/{prim}_collision", slabs)
        dropped = sum(int((~k).sum()) for k, *_ in cleared.values())
        total = sum(len(k) for k, *_ in cleared.values())
        print(f"{furniture}: " + "  ".join(f"{k} {v[1][2]:.3f} (c {v[2]:.2f})" for k, v in slabs.items())
              + f"  | {dropped}/{total} collision faces dropped")
        if args.dry_run:
            continue
        for layer, (lo, hi, clear) in slabs.items():
            name = f"{furniture}__{layer}"
            made.add(name)
            slab = UsdGeom.Cube.Define(stage, root.GetPath().AppendChild(name))
            UsdPhysics.CollisionAPI.Apply(slab.GetPrim())
            slab.CreateSizeAttr(1.0)
            slab.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
            slab.ClearXformOpOrder()
            slab.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(*((lo + hi) / 2).tolist()))
            slab.AddScaleOp().Set(Gf.Vec3f(*(hi - lo).tolist()))
            p = slab.GetPrim()
            p.SetCustomDataByKey("zeno:support", f"{furniture}/{layer}")
            p.SetCustomDataByKey("zeno:category", category[furniture])
            p.SetCustomDataByKey("zeno:clearance", float(clear))
        for path, (kept, C, I, start) in cleared.items():
            if kept.all():
                continue
            mesh = UsdGeom.Mesh(stage.GetPrimAtPath(path))
            idx = np.concatenate([I[o:o + c] for o, c, k in zip(start, C, kept) if k])
            mesh.GetFaceVertexCountsAttr().Set(C[kept].tolist())
            mesh.GetFaceVertexIndicesAttr().Set(idx.tolist())
    if not args.dry_run:
        # furniture only: the room shells carry tools/cut_doorway.py's own face (and point)
        # overrides, and clearing their faces alone leaves the cut points under the original
        # faces - garbage walls across the doorways
        for f, prim in prim_of.items():
            if f in spec:
                continue
            p = stage.GetPrimAtPath(f"{BASE}/collisions/{prim}_collision")
            if not p:
                continue
            for m in Usd.PrimRange(p):
                if m.IsA(UsdGeom.Mesh):
                    for a in (UsdGeom.Mesh(m).GetFaceVertexCountsAttr(), UsdGeom.Mesh(m).GetFaceVertexIndicesAttr()):
                        a.Clear()
        for p in root.GetChildren():
            if p.GetName() not in made:
                print("removed slab", p.GetName())
                stage.RemovePrim(p.GetPath())
        stage.GetRootLayer().Save()
        print("saved", HOUSE.relative_to(ROOT), len(made), "slabs")


if __name__ == "__main__":
    main()
