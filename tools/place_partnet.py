"""Put imported PartNet articulated assets (tools/import_partnet.py) into the
house: a scene layer over sim/zeno_house.usd, the house itself unchanged.

    cd zeno-house   # repository root
    ${ISAACLAB_PYTHON:-python} tools/place_partnet.py --asset partnet_cabinet_48452 --name partnet_cabinet \
        [--room living_room_0_0 | --near 4.4 1.9] [--xy X Y --yaw DEG] [--out sim/zeno_house_partnet.usd]
    ${ISAACLAB_PYTHON:-python} tools/annotate_scene.py sim/zeno_house_partnet.usd annotations/zeno_house_partnet.json

Without --xy the spot is searched: the footprint is free of every annotated
obstacle and inside one room, the back stands against a wall, and in front of
the door there is a free area for the robot and the door swing.  The spot
closest to --near (default: the robot start) wins; it keeps 1.1 m from the
robot's start pose.  Run again with another
--name to add more assets to the same layer (--out is extended, not replaced).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def in_room(room, pts):
    tris = np.asarray(room["triangles"], float)
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    ok = []
    for x, y in pts:
        d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
        with np.errstate(divide="ignore", invalid="ignore"):
            l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / d
            l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / d
        ok.append(bool(np.any((np.abs(d) > 1e-12) & (l1 >= -1e-6) & (l2 >= -1e-6) & (1 - l1 - l2 >= -1e-6))))
    return all(ok)


def room_of(rooms, xy):
    for name, r in rooms.items():
        if in_room(r, [xy]):
            return name
    return None


def find_spot(ann, size, room, near, front_depth=1.4, front_extra=1.0, wall_gap=0.08, margin=0.02,
              robot_clear=1.1):
    """-> (x, y, yaw_deg) of the asset's bottom centre; front = local -y.
    robot_clear: distance from the robot's start pose to the footprint (the
    hanging arm must not start against the new furniture)."""
    rxy = np.asarray(ann["robot"]["xy"], float)
    B = np.array([o["aabb"] for o in ann["obstacles"]], float)
    walls = np.array([o["aabb"] for o in ann["obstacles"] if o["kind"] == "wall"], float)
    w, dpt, h = size

    def free(lo, hi, boxes, zmax):
        hit = (boxes[:, 0] < hi[0]) & (boxes[:, 3] > lo[0]) & (boxes[:, 1] < hi[1]) & (boxes[:, 4] > lo[1]) & \
              (boxes[:, 2] < zmax) & (boxes[:, 5] > 0.02)
        return not hit.any()
    r = ann["rooms"][room]
    x0, y0, x1, y1 = r["aabb_xy"]
    best = None
    for yaw in (0, 90, 180, 270):
        f = np.array([math.sin(math.radians(yaw)), -math.cos(math.radians(yaw))])   # Rz(yaw) @ (0, -1)
        side = np.array([-f[1], f[0]])
        hx, hy = (w / 2, dpt / 2) if yaw in (0, 180) else (dpt / 2, w / 2)
        for x in np.arange(x0 + hx, x1 - hx, 0.05):
            for y in np.arange(y0 + hy, y1 - hy, 0.05):
                c = np.array([x, y])
                lo, hi = c - [hx + margin, hy + margin], c + [hx + margin, hy + margin]
                if not free(lo, hi, B, h):
                    continue
                if np.linalg.norm(np.maximum(np.maximum(lo - rxy, rxy - hi), 0.0)) < robot_clear:
                    continue
                corners = [c + sx * hx * np.array([1, 0]) + sy * hy * np.array([0, 1]) for sx in (-1, 1) for sy in (-1, 1)]
                if not in_room(r, corners + [c]):
                    continue
                # back against a wall
                back = c - f * (dpt / 2 + wall_gap / 2)
                bl = back - np.abs(side) * (w / 2 - 0.05) - np.abs(f) * wall_gap / 2
                bh = back + np.abs(side) * (w / 2 - 0.05) + np.abs(f) * wall_gap / 2
                if free(bl, bh, walls, 2.0):
                    continue
                # free area in front: robot + door swing
                fc = c + f * (dpt / 2 + front_depth / 2 + 0.02)
                ext = np.abs(f) * front_depth / 2 + np.abs(side) * (w + front_extra) / 2
                if not free(fc - ext, fc + ext, B, 1.5):
                    continue
                if not in_room(r, [fc - ext, fc + ext, fc + ext * [1, -1], fc - ext * [1, -1]]):
                    continue
                d = float(np.linalg.norm(fc - near))
                if best is None or d < best[0]:
                    best = (d, float(x), float(y), yaw)
    if best is None:
        raise SystemExit(f"no free wall spot for a {w:.2f} x {dpt:.2f} m asset in {room}")
    return best[1], best[2], best[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", required=True, help="name given to tools/import_partnet.py")
    ap.add_argument("--name", required=True, help="instance name (= articulated name in the annotation)")
    ap.add_argument("--base", default="sim/zeno_house.usd")
    ap.add_argument("--base-ann", default="annotations/zeno_house.json")
    ap.add_argument("--out", default="sim/zeno_house_partnet.usd")
    ap.add_argument("--room")
    ap.add_argument("--near", nargs=2, type=float)
    ap.add_argument("--xy", nargs=2, type=float)
    ap.add_argument("--yaw", type=float, default=0.0, help="deg; 0 = door faces -y")
    args = ap.parse_args()

    info = json.loads((ROOT / "usd/partnet" / args.asset / "import.json").read_text())
    ann = json.loads((ROOT / args.base_ann).read_text())
    if args.out != args.base and (ROOT / args.out).exists():
        # assets placed earlier in this layer are obstacles too
        prev = ROOT / "annotations" / (Path(args.out).stem + ".json")
        if prev.exists():
            ann = json.loads(prev.read_text())
    if args.xy:
        x, y, yaw = args.xy[0], args.xy[1], args.yaw
    else:
        near = np.array(args.near or ann["robot"]["xy"], float)
        room = args.room or room_of(ann["rooms"], near)
        x, y, yaw = find_spot(ann, info["size"], room, near)
    print("SPOT", json.dumps({"name": args.name, "xy": [round(x, 3), round(y, 3)], "yaw_deg": yaw,
                              "room": room_of(ann["rooms"], (x, y))}), flush=True)

    from isaaclab.app import AppLauncher
    AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True})
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade
    from zeno_skills.physics import bind, fix_articulation

    out = ROOT / args.out
    if out.exists():
        layer = Sdf.Layer.FindOrOpen(str(out))
    else:
        layer = Sdf.Layer.CreateNew(str(out))
        layer.subLayerPaths.append(os.path.relpath(ROOT / args.base, out.parent))
        layer.Save()
    stage = Usd.Stage.Open(str(out))
    stage.SetEditTarget(stage.GetRootLayer())
    UsdGeom.Xform.Define(stage, "/World/ArticulatedAssets/partnet")
    path = f"/World/ArticulatedAssets/partnet/{args.name}"
    if stage.GetPrimAtPath(path):
        stage.RemovePrim(path)
    # stand on whatever flat collider is under the footprint (rugs are not in
    # the annotation obstacles, and a door sunk into a rug cannot move)
    c, s_ = abs(math.cos(math.radians(yaw))), abs(math.sin(math.radians(yaw)))
    hx = (c * info["size"][0] + s_ * info["size"][1]) / 2
    hy = (s_ * info["size"][0] + c * info["size"][1]) / 2
    cache = UsdGeom.BBoxCache(0, ["default", "guide", "proxy", "render"])
    z0 = 0.001
    for p in stage.Traverse():
        if not p.HasAPI(UsdPhysics.CollisionAPI) or str(p.GetPath()).startswith("/World/ZenoMalo"):
            continue
        r = cache.ComputeWorldBound(p).ComputeAlignedRange()
        lo, hi = r.GetMin(), r.GetMax()
        if hi[2] < 0.05 and lo[0] < x + hx and hi[0] > x - hx and lo[1] < y + hy and hi[1] > y - hy:
            z0 = max(z0, float(hi[2]) + 0.001)
    print("FLOOR_Z", round(z0, 4), flush=True)
    inst = UsdGeom.Xform.Define(stage, path)
    inst.GetPrim().GetReferences().AddReference(os.path.relpath(ROOT / info["usd"], out.parent))
    inst.ClearXformOpOrder()
    inst.AddTranslateOp().Set(Gf.Vec3d(x, y, z0))
    inst.AddRotateZOp().Set(float(yaw))
    rj = stage.GetPrimAtPath(path + "/root_joint")
    rj.GetAttribute("physics:localPos0").Set(Gf.Vec3f(x, y, z0))
    h = math.radians(yaw) / 2
    rj.GetAttribute("physics:localRot0").Set(Gf.Quatf(math.cos(h), 0.0, 0.0, math.sin(h)))
    # the house's contact materials: wood carcass and door, rubber handle
    mats = {k: UsdShade.Material(stage.GetPrimAtPath(f"/World/ContactMaterials/{k}")) for k in ("wood", "rubber")}
    for p in Usd.PrimRange(inst.GetPrim()):
        if p.HasAPI(UsdPhysics.CollisionAPI) and mats["wood"]:
            bind(p, mats["rubber" if p.GetName().startswith("handle") and mats["rubber"] else "wood"])
        if p.IsA(UsdPhysics.RevoluteJoint) or p.IsA(UsdPhysics.PrismaticJoint):
            fix_articulation(stage, str(p.GetPath()))
    stage.GetRootLayer().Save()
    print("PLACED", path, "in", args.out, flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
