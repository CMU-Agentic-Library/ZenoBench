"""Give every room shell the triangles of its visual mesh as its collider (sim/zeno_house.usd).

The Infinigen export's shell colliders (<room>_exterior_collision_openroof_wideopen) are a convex
decomposition of the visual shell -- 20-25 hulls merged into one mesh -- while the stage collides
them as a triangle mesh (approximation "none", two-sided; the converter's "convexHull" would make a
room one solid hull).  So the hulls buy nothing and keep their error: a floor-slab hull that took
in a stub of wall rises to 0.2-0.3 m along a room's open side (living_room_0_0 at x = -1.09, 2.5 m
long; dining_room_0_1 at x ~ 0.6), a ghost threshold across a wide-open passage.  The visual shell
is the room as rendered (walls, floor slab, the doorways cut by tools/cut_doorway.py); windows have
colliders of their own.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/shell_colliders_from_visual.py

Idempotent: a collider already equal to its visual mesh is skipped.  Then the wall segments of
annotations/house_static.json (the base footprint's walls) are cut again from the new colliders
(cut_doorway.wall_segments); the scene annotations carry them as wall_<i> obstacles only once
tools/annotate_scene.py is run again.
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


def _mesh(stage, root):
    from pxr import Usd, UsdGeom
    meshes = [p for p in Usd.PrimRange(stage.GetPrimAtPath(root)) if p.IsA(UsdGeom.Mesh)]
    assert len(meshes) == 1, (root, len(meshes))
    return UsdGeom.Mesh(meshes[0])


def main():
    from isaaclab.app import AppLauncher
    AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True})
    from pxr import Gf, Vt

    from pxr import Usd, UsdGeom
    stage = Usd.Stage.Open(str(SCENE))
    cache = UsdGeom.XformCache()
    changed = 0
    for c in stage.GetPrimAtPath(BASE + "collisions").GetChildren():
        name = c.GetName()
        if not name.endswith("_exterior_collision_openroof_wideopen"):
            continue
        room = name[:-len("_exterior_collision_openroof_wideopen")]
        col = _mesh(stage, BASE + "collisions/" + name)
        vis = _mesh(stage, BASE + f"visuals/{room}_exterior_openroof_wideopen")
        Mv = np.array(cache.GetLocalToWorldTransform(vis.GetPrim())).T
        Mc = np.array(cache.GetLocalToWorldTransform(col.GetPrim())).T
        T = np.linalg.inv(Mc) @ Mv                      # visual frame -> collider frame
        pts = np.array(vis.GetPointsAttr().Get(), float)
        pts = (T[:3, :3] @ pts.T).T + T[:3, 3]
        counts = np.array(vis.GetFaceVertexCountsAttr().Get())
        idx = np.array(vis.GetFaceVertexIndicesAttr().Get())
        old = np.array(col.GetPointsAttr().Get(), float)
        if (len(old) == len(pts) and np.allclose(old, pts, atol=1e-6)
                and np.array_equal(np.array(col.GetFaceVertexIndicesAttr().Get()), idx)):
            print("SKIP", room, "(already the visual mesh)")
            continue
        n_old = len(col.GetFaceVertexCountsAttr().Get())
        col.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*map(float, v)) for v in pts]))
        col.GetFaceVertexCountsAttr().Set(Vt.IntArray([int(v) for v in counts]))
        col.GetFaceVertexIndicesAttr().Set(Vt.IntArray([int(v) for v in idx]))
        ext = col.GetExtentAttr()
        if ext and ext.Get() is not None:
            ext.Set(Vt.Vec3fArray([Gf.Vec3f(*map(float, pts.min(0))), Gf.Vec3f(*map(float, pts.max(0)))]))
        print("SHELL", room, f"{n_old} -> {len(counts)} faces", flush=True)
        changed += 1
    if changed:
        stage.GetRootLayer().Save()
    print("changed", changed)

    sys.path.insert(0, str(ROOT / "tools"))
    from cut_doorway import wall_segments
    segs = wall_segments(stage)
    static = json.loads(STATIC.read_text())
    print("WALLS", len(static["walls"]), "->", len(segs))
    static["walls"] = segs
    STATIC.write_text(json.dumps(static))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
