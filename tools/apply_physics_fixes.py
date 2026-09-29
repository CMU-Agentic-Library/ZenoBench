"""Re-apply the articulated-furniture physics fixes of zeno_skills/physics.py
to sim/zeno_house.usd (idempotent; run after changing fix_articulation).

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/apply_physics_fixes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from isaaclab.app import AppLauncher
    AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True})
    from pxr import Usd, UsdPhysics
    from zeno_skills import physics as P
    stage = Usd.Stage.Open(str(ROOT / "sim/zeno_house.usd"))
    n = 0
    for prim in Usd.PrimRange(stage.GetPrimAtPath("/World/ArticulatedAssets")):
        if prim.IsA(UsdPhysics.RevoluteJoint) or prim.IsA(UsdPhysics.PrismaticJoint):
            P.fix_articulation(stage, str(prim.GetPath()))
            n += 1
    stage.GetRootLayer().Save()
    print("FIXED", n, "joints", flush=True)


if __name__ == "__main__":
    main()
