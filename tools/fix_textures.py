"""Give every converted asset its own diffuse texture.

EmbodiedGen names every generated texture `material_0.png`; the URDF->USD
converter copies it to the shared usd/assets/configuration/materials/textures/
directory, so each conversion overwrote the previous one and all assets ended
up with the texture of the last one converted (the grey storage basket).  This
copies each asset's own texture to `<name>_diffuse.png` and repoints
`inputs:diffuse_texture` in `<name>_base.usd`.  Run after any
`prepare_assets.py --convert`.

    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/fix_textures.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "usd/assets/configuration/materials/textures"


def source_texture(name):
    for d in (ROOT / "assets/asset3d" / name / "result/mesh",):
        if (d / "material_0.png").exists():
            return d / "material_0.png"
    return None


def main():
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    from pxr import Sdf
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    for name in assets:
        src = source_texture(name)
        base = ROOT / "usd/assets/configuration" / f"{name}_base.usd"
        if src is None or not base.exists():
            print("SKIP", name, src, base.exists(), flush=True)
            continue
        dst = TEX / f"{name}_diffuse.png"
        shutil.copyfile(src, dst)
        layer = Sdf.Layer.FindOrOpen(str(base))
        n = 0

        def visit(path):
            nonlocal n
            if path.IsPropertyPath() and path.name == "inputs:diffuse_texture":
                spec = layer.GetAttributeAtPath(path)
                spec.default = Sdf.AssetPath(f"./materials/textures/{name}_diffuse.png")
                n += 1
        layer.Traverse(Sdf.Path.absoluteRootPath, visit)
        layer.Save()
        print("FIXED", name, "textures", n, flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
