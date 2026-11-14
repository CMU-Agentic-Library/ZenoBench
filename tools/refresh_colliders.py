"""Re-apply the asset colliders (zeno_skills.physics.apply_asset_colliders) to scenes already built.

The collider of every task object is authored into the scene that defines the object: the house
(sim/zeno_house.usd, /World/TaskAssets) and each task layer (tasks/<task>/scene.usd, /World/Tasks;
it sublayers the house).  Rebuilding a task with tools/build_tasks.py re-draws every placement, so
when only the collider rules change (11-13: container walls fitted around the body, not the bbox;
concave solids as convex pieces; the smaller tissue box) this rewrites the colliders in place and
leaves positions, rest poses and annotations alone.  Mass and inertia are re-set from the asset
annotation too (the tissue box got lighter).

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/refresh_colliders.py [--dry-run] [scene.usd ...]

Without scene arguments: the house, every tasks/*/scene*.usd and scenes/*/scene.usd.  Only prims whose
definition is in the scene's own layer are edited (a task layer never overrides house objects).
Idempotent: the generated prims (wall_*, hull_*, handle_collider*) are removed and rebuilt.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OBJECT_ROOTS = ("/World/TaskAssets", "/World/Tasks")


def default_scenes():
    return [ROOT / "sim/zeno_house.usd", *sorted(ROOT.glob("tasks/*/scene*.usd")), *sorted(ROOT.glob("scenes/*/scene.usd"))]


def asset_of(prim):
    """The asset name an object prim references (usd/assets/<name>.usd), on it or its 'Asset' child."""
    for q in (prim, prim.GetChild("Asset")):
        if q and q.HasAuthoredReferences():
            for ref in q.GetMetadata("references").GetAddedOrExplicitItems():
                return Path(str(ref.assetPath)).stem
    return None


def refresh(path, assets, dry_run=False):
    from pxr import Sdf, Usd
    from zeno_skills import physics as P
    stage = Usd.Stage.Open(str(path))
    layer = stage.GetRootLayer()
    mats = None if dry_run else P.materials(stage)
    out = []
    for root in OBJECT_ROOTS:
        parent = stage.GetPrimAtPath(root)
        if not parent:
            continue
        for prim in parent.GetChildren():
            spec = layer.GetPrimAtPath(prim.GetPath())
            if spec is None or spec.specifier != Sdf.SpecifierDef:
                continue                        # defined by a sublayer (the house), not here
            name = asset_of(prim)
            a = assets.get(name)
            if a is None:
                out.append((str(prim.GetPath()), name, "no asset annotation"))
                continue
            if dry_run:
                out.append((str(prim.GetPath()), name, "would refresh"))
                continue
            P.set_box_inertia(stage, str(prim.GetPath()), a["mass"])
            out.append((str(prim.GetPath()), name, P.apply_asset_colliders(stage, str(prim.GetPath()), a, mats=mats)))
    if not dry_run:
        layer.Save()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app  # noqa: F841 (pxr)
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    for s in [Path(p).resolve() for p in args.scenes] or default_scenes():
        for prim, name, what in refresh(s, assets, args.dry_run):
            print(f"{s.relative_to(ROOT)}  {prim}  {name}: {what}", flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
