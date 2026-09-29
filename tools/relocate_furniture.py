"""Move furniture inside sim/zeno_house.usd (and keep the annotations in sync).

Infinigen placed four articulated cabinets and two bookcases in the two
bathrooms.  MOVES below puts each one against a free wall of a living space
(spots found by sliding the footprint along the walls of the target room:
back within 6 cm of a wall, no overlap, >= 1.1 m of free floor in front).

A move is a rigid motion about the vertical (dx, dy, dyaw about the
furniture's footprint centre) and handles every kind of prim involved:

  articulated cabinet   /World/ArticulatedAssets/cabinets/<name> translate +
                        rotateZ, and its world-anchored root fixed joint
                        (localPos0/localRot0 are world coordinates: leaving
                        them stale snaps the cabinet back when PhysX starts)
  static furniture      /World/House/Asset/base/visuals/<name> and
                        .../collisions/<name>_collision (translate + orient),
                        annotations/house_static.json (furniture box, every
                        support surface of it)
  objects on top        /World/TaskAssets/<obj> listed in `carry` ride along

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/relocate_furniture.py [--dry-run]

Then: tools/settle_scene.py sim/zeno_house.usd, tools/annotate_scene.py
sim/zeno_house.usd annotations/zeno_house.json, and rebuild the task layers
(tools/make_tasks.sh).  The script is idempotent: a furniture piece that is
already at its target is skipped.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SCENE = ROOT / "sim/zeno_house.usd"
STATIC = ROOT / "annotations/house_static.json"
CAB = "/World/ArticulatedAssets/cabinets/"
BASE = "/World/House/Asset/base/"

# name -> target footprint centre (x, y), facing (deg: 0 = -y, 90 = +x,
# 180 = +y, 270 = -x, the cabinets' rotateZ convention), objects carried along
MOVES = {
    # kitchen drawer unit: bathroom_0_1 -> dining room west wall, facing +x
    "KitchenCabinetFactory_9483010_spawn_asset_2619144": {
        "kind": "articulated", "to": (0.83, 5.45), "facing": 90,
        "carry": ["mug_counter"]},
    # kitchen door cabinet: bathroom_0_0 -> living-room south wall, facing +y
    # (next to cabinet 6631478, the validated open/close location)
    "KitchenCabinetFactory_3699907_spawn_asset_505866": {
        "kind": "articulated", "to": (1.40, 0.42), "facing": 180, "carry": []},
    # single cabinet: bathroom_0_0 -> bedroom north wall, facing -y
    "SingleCabinetFactory_7330242_spawn_asset_8918727": {
        "kind": "articulated", "to": (7.30, -0.58), "facing": 0, "carry": []},
    # tall single cabinet: bathroom_0_1 -> bedroom east wall, facing -x (clear
    # of the plant on the handle side)
    "SingleCabinetFactory_680597_spawn_asset_3676420": {
        "kind": "articulated", "to": (9.36, -4.40), "facing": 270, "carry": []},
    # bookcases (shelve_books targets): bathroom_0_0 -> bedroom
    "SimpleBookcaseFactory_2318999_spawn_asset_8416993": {
        "kind": "static", "to": (2.10, -4.88), "facing": 180, "from_facing": 0},
    "SimpleBookcaseFactory_6105320_spawn_asset_9196243": {
        "kind": "static", "to": (1.00, -0.43), "facing": 0, "from_facing": 270},
}
# objects that sat on a moved cabinet and go somewhere else: name -> (dx, dy)
# offset on top of another moved piece.  The breakfast bowl stood on the
# 1.75 m tall bathroom cabinet (out of Zeno's reach); it joins the mug on the
# dining-room drawer unit.
REHOME = {"bowl_kitchen_cabinet": ("KitchenCabinetFactory_9483010_spawn_asset_2619144", (0.0, -0.22))}


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s], [s, c]])


def quat_z(deg):
    from pxr import Gf
    a = math.radians(deg) / 2
    return Gf.Quatd(math.cos(a), 0.0, 0.0, math.sin(a))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    # Isaac Sim's own USD build, so the crate file stays readable by it
    from isaaclab.app import AppLauncher
    AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True})
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    stage = Usd.Stage.Open(str(SCENE))
    static = json.loads(STATIC.read_text())
    report = []

    def bound(prim):
        r = UsdGeom.Imageable(prim).ComputeWorldBound(0, "default").ComputeAlignedRange()
        return np.array(r.GetMin()), np.array(r.GetMax())

    def move_object(path, c_old, dyaw_deg, c_new):
        """Rigid motion of a free object (translate + orient ops)."""
        p = stage.GetPrimAtPath(path)
        t = p.GetAttribute("xformOp:translate")
        o = p.GetAttribute("xformOp:orient")
        v = np.array(t.Get(), float)
        xy = rz(math.radians(dyaw_deg)) @ (v[:2] - c_old) + c_new
        t.Set(type(t.Get())(float(xy[0]), float(xy[1]), float(v[2])))
        if o and o.Get() is not None:
            q = o.Get()
            o.Set(type(q)(quat_z(dyaw_deg) * Gf.Quatd(q)))
        return xy

    placed = {}
    for name, m in MOVES.items():
        if m["kind"] == "articulated":
            prim = stage.GetPrimAtPath(CAB + name)
            lo, hi = bound(prim.GetChild("base"))
            c_old = (lo[:2] + hi[:2]) / 2
            t = prim.GetAttribute("xformOp:translate")
            r = prim.GetAttribute("xformOp:rotateZ")
            old_face = float(r.Get()) % 360
            dyaw = (m["facing"] - old_face) % 360
            c_new = np.asarray(m["to"], float)
            if np.linalg.norm(c_new - c_old) < 0.02 and dyaw == 0:
                report.append(f"SKIP {name}: already in place")
                placed[name] = (c_old, 0.0, c_new)
                continue
            tv = np.array(t.Get(), float)
            # translate is the prim origin; keep its offset to the footprint centre
            off = rz(math.radians(dyaw)) @ (tv[:2] - c_old)
            new_t = c_new + off
            t.Set(Gf.Vec3d(float(new_t[0]), float(new_t[1]), float(tv[2])))
            r.Set(float(m["facing"]))
            j = UsdPhysics.Joint(prim.GetChild("root_joint"))
            j.GetLocalPos0Attr().Set(Gf.Vec3f(float(new_t[0]), float(new_t[1]), float(tv[2])))
            j.GetLocalRot0Attr().Set(Gf.Quatf(quat_z(m["facing"])))
            for obj in m.get("carry", []):
                move_object("/World/TaskAssets/" + obj, c_old, dyaw, c_new)
            placed[name] = (c_old, dyaw, c_new)
            report.append(f"MOVE {name}: ({c_old[0]:.2f}, {c_old[1]:.2f}) -> ({c_new[0]:.2f}, {c_new[1]:.2f}), "
                          f"yaw +{dyaw:.0f}, carried {m.get('carry', [])}")
        else:
            f = next(f for f in static["furniture"] if f["name"] == name)
            a = np.array(f["aabb"], float)
            c_old = (a[:2] + a[3:5]) / 2
            dyaw = (m["facing"] - m["from_facing"]) % 360
            c_new = np.asarray(m["to"], float)
            if np.linalg.norm(c_new - c_old) < 0.02:
                report.append(f"SKIP {name}: already in place")
                continue
            R = rz(math.radians(dyaw))
            for path in (BASE + "visuals/" + name, BASE + "collisions/" + name + "_collision"):
                p = stage.GetPrimAtPath(path)
                if not p:
                    raise SystemExit(f"missing prim {path}")
                t = p.GetAttribute("xformOp:translate")
                o = p.GetAttribute("xformOp:orient")
                v = np.array(t.Get(), float)
                xy = R @ (v[:2] - c_old) + c_new
                t.Set(type(t.Get())(float(xy[0]), float(xy[1]), float(v[2])))
                q = o.Get()
                o.Set(type(q)(Gf.Quatd(quat_z(dyaw)) * Gf.Quatd(q)))

            def move_box(lo_xy, hi_xy):
                corners = np.array([[x, y] for x in (lo_xy[0], hi_xy[0]) for y in (lo_xy[1], hi_xy[1])])
                w = (R @ (corners - c_old).T).T + c_new
                return w.min(0), w.max(0)
            lo2, hi2 = move_box(a[:2], a[3:5])
            f["aabb"] = [round(float(lo2[0]), 3), round(float(lo2[1]), 3), a[2],
                         round(float(hi2[0]), 3), round(float(hi2[1]), 3), a[5]]
            n = 0
            for s in static["supports"]:
                if s["furniture"] == name:
                    b = s["aabb_xy"]
                    lo2, hi2 = move_box(b[:2], b[2:])
                    s["aabb_xy"] = [round(float(v), 3) for v in (*lo2, *hi2)]
                    n += 1
            report.append(f"MOVE {name}: ({c_old[0]:.2f}, {c_old[1]:.2f}) -> ({c_new[0]:.2f}, {c_new[1]:.2f}), "
                          f"yaw +{dyaw:.0f}, {n} support surfaces")
    for obj, (host, dxy) in REHOME.items():
        if host not in placed:
            continue
        c_old, dyaw, c_new = placed[host]
        p = stage.GetPrimAtPath("/World/TaskAssets/" + obj)
        t = p.GetAttribute("xformOp:translate")
        v = np.array(t.Get(), float)
        top = bound(stage.GetPrimAtPath(CAB + host).GetChild("base"))[1][2]
        olo, _ = bound(p)
        xy = c_new + np.asarray(dxy, float)
        # bottom 1 cm above the host top; settle_scene.py drops it
        t.Set(type(t.Get())(float(xy[0]), float(xy[1]), float(v[2] - olo[2] + top + 0.01)))
        report.append(f"REHOME {obj} -> top of {host} at ({xy[0]:.2f}, {xy[1]:.2f})")
    for line in report:
        print(line, flush=True)
    if args.dry_run:
        print("dry run: nothing written")
        return
    stage.GetRootLayer().Save()
    STATIC.write_text(json.dumps(static))
    print("WROTE", SCENE, STATIC)


if __name__ == "__main__":
    main()
