"""Rewrite absolute asset paths in sim/zeno_house.usd as paths relative to the
layer, so the repository can be cloned anywhere."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    from pxr import Sdf, UsdUtils
    path = ROOT / "sim/zeno_house.usd"
    layer = Sdf.Layer.FindOrOpen(str(path))
    n = 0
    for dep in layer.GetCompositionAssetDependencies():
        if os.path.isabs(dep):
            rel = os.path.relpath(dep, path.parent)
            layer.UpdateCompositionAssetDependency(dep, rel)
            n += 1
    layer.Save()
    left = layer.ExportToString().count(str(ROOT.parents[2]))
    print("RELATIVIZED", n, "absolute paths left:", left, flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
