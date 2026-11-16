"""Each asset's collider as the simulator builds it, as one convex hull in its body frame:
annotations/assets.json "collider_hull" (vertices, m).

The object is authored the way benchmark/scene.add_objects authors it (the asset's USD referenced,
physics.apply_asset_colliders: container walls, convex hull or convex pieces), its colliders read the way the planner reads them
(scene_geometry.collect: a mesh collider its convex hull, at most 64 vertices like PhysX's cooking;
a Cube its box) and put in the rigid body's frame -- the frame of a state's pos / quat.  The hull
of all of them is what Geometry.resting takes the lowest point of: a box's corner hangs below a
tilted round object (11-14, v6 T24 apple_on_table: an apple at rest on desk_1 read 2.2 cm under
it), its collider's lowest point does not.

Only "collider_hull" is written; the asset's other fields stay as tools/prepare_assets.py wrote
them.  Run in the container (pxr):  $ISAACLAB_PYTHON tools/collider_hulls.py [--only NAME ...] [--check]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ANN = ROOT / "annotations" / "assets.json"
DIGITS = 4                      # 0.1 mm


def hull_of(name, spec):
    """(n, 3) vertices of the convex hull of ``spec``'s colliders in its rigid body's frame."""
    import trimesh
    from pxr import Usd, UsdGeom
    from zeno_skills import physics as P
    from zeno_skills import scene_geometry as G
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = f"/World/Tasks/{name}"
    UsdGeom.Xform.Define(stage, root)
    stage.DefinePrim(f"{root}/Asset").GetReferences().AddReference(str(ROOT / spec["usd"]))
    P.strip_nested_bodies(stage, root)                 # the converter's body inside the body
    mats = P.materials(stage)
    P.apply_asset_colliders(stage, root, {"name": name, **spec}, mats=mats)   # as every scene builds it
    body = str(P.body_prim(stage, root).GetPath())
    ann = SimpleNamespace(objects={name: {"prim": root}}, articulated=[])
    pts = []
    for c in G.collect(stage, ann).items:
        if c.owner != f"object:{name}":
            continue
        if c.body != body:
            raise RuntimeError(f"{name}: collider {c.name} moves with {c.body}, not the body {body}")
        if c.kind == "cuboid":
            V = np.array([[i, j, k] for i in (-.5, .5) for j in (-.5, .5) for k in (-.5, .5)]) * c.dims
        else:
            V = np.asarray(c.vertices, float)
        pts.append(V @ c.local[:3, :3].T + c.local[:3, 3])
    if not pts:
        raise RuntimeError(f"{name}: no collider")
    return np.asarray(trimesh.convex.convex_hull(np.vstack(pts)).vertices)


def dump(anns):
    """assets.json as prepare_assets writes it (indent 1), each hull on one line."""
    hulls = {n: a.pop("collider_hull") for n, a in anns.items() if isinstance(a, dict) and "collider_hull" in a}
    for n in hulls:
        anns[n]["collider_hull"] = f"@HULL:{n}@"
    text = json.dumps(anns, indent=1)
    for n, V in hulls.items():
        text = text.replace(f'"@HULL:{n}@"', json.dumps(V))
        anns[n]["collider_hull"] = V
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--check", action="store_true", help="fail when a stored hull differs from the colliders")
    args = ap.parse_args()
    from isaaclab.app import AppLauncher           # pxr and the PhysX schemas come with the app
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    anns = json.loads(ANN.read_text())
    stale = []
    for name, spec in anns.items():
        if not isinstance(spec, dict) or "usd" not in spec or (args.only and name not in args.only):
            continue
        V = np.round(hull_of(name, spec), DIGITS)
        lo, hi = V.min(0), V.max(0)
        box_lo = np.asarray(spec["origin_to_bottom_center"], float)
        print(f"{name:24s} {len(V):4d} vertices  lowest z {lo[2]:+.4f} (box {box_lo[2]:+.4f})  "
              f"extent {np.round(hi - lo, 4).tolist()} (box {spec['size']})", flush=True)
        new = V.tolist()
        if spec.get("collider_hull") != new:
            stale.append(name)
            spec["collider_hull"] = new
    if args.check:
        print(f"collider_hull stale for {stale}: run tools/collider_hulls.py" if stale else "collider_hull current")
    else:
        ANN.write_text(dump(anns))
        print(f"wrote {ANN} ({len(stale)} changed)")
    sys.stdout.flush()
    app.close()
    os._exit(1 if args.check and stale else 0)


if __name__ == "__main__":
    main()
