"""Write annotations/<scene>.json: the GT needed to operate every asset.

Static part (from the Infinigen export House_seed77, cached in
annotations/house_static.json): rooms (floor triangles), wall segments,
furniture AABBs, horizontal support surfaces (table tops, desk tops, shelf
levels) found from upward-facing mesh faces.

Scene part (from the USD): articulated furniture (joint, pivot, axis, limits,
moving-part box, handle frame), task objects (asset type, body prim, pose,
room, support), robot start pose.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} \
        tools/annotate_scene.py sim/zeno_house.usd annotations/zeno_house.json
"""

from __future__ import annotations

import json
import math
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "House_seed77/urdf/export_scene"
STATIC = ROOT / "annotations/house_static.json"
SKIP_FURNITURE = ("Window", "Rug", "KitchenCabinetFactory", "SingleCabinetFactory")  # windows=walls, rugs=flat, cabinets=articulated


def _T(o):
    from scipy.spatial.transform import Rotation
    M = np.eye(4)
    if o is None:
        return M
    M[:3, :3] = Rotation.from_euler("xyz", [float(x) for x in (o.get("rpy") or "0 0 0").split()]).as_matrix()
    M[:3, 3] = [float(x) for x in (o.get("xyz") or "0 0 0").split()]
    return M


def house_static():
    """Needs the Infinigen export (House_seed77/urdf/export_scene, not in this
    repository: 1.7 GB).  annotations/house_static.json is the cached result."""
    if not (EXPORT / "scene_articulated.urdf").exists():
        raise SystemExit(f"{EXPORT} missing: keep annotations/house_static.json (cached)")
    import trimesh
    r = ET.parse(EXPORT / "scene_articulated.urdf").getroot()   # final house URDF (cabinets are articulated USD)
    links = {l.get("name"): l for l in r.findall("link")}
    joints = {j.find("child").get("link"): j for j in r.findall("joint")}

    def world(link):
        ch = []
        while link in joints:
            j = joints[link]
            ch.append(_T(j.find("origin")))
            link = j.find("parent").get("link")
        T = np.eye(4)
        for M in reversed(ch):
            T = T @ M
        return T

    def mesh(name):
        L = links[name]
        v = L.find("collision") if L.find("collision") is not None else L.find("visual")
        fn = v.find("geometry").find("mesh").get("filename")
        m = trimesh.load(EXPORT / fn, force="mesh")
        m.apply_transform(world(name) @ _T(v.find("origin")))
        return m

    rooms, walls, furniture, supports = {}, [], [], []
    for name in links:
        if name.endswith("_floor"):
            m = mesh(name)
            room = name[: -len("_floor")]
            rooms[room] = {"triangles": np.round(m.vertices[m.faces][:, :, :2], 3).tolist(),
                           "aabb_xy": np.round(np.r_[m.bounds[0, :2], m.bounds[1, :2]], 3).tolist()}
        elif name.endswith("_wall") or name.endswith("_exterior"):
            m = mesh(name)
            sec = m.section(plane_origin=[0, 0, 0.5], plane_normal=[0, 0, 1])
            if sec is None:
                continue
            for ent in sec.entities:
                pts = sec.vertices[ent.points][:, :2]
                for a, b in zip(pts[:-1], pts[1:]):
                    if np.linalg.norm(b - a) > 0.02:
                        walls.append([round(float(v), 3) for v in (*a, *b)])
    for name in links:
        if any(k in name for k in ("_floor", "_wall", "_exterior", "_ceiling")) or name in ("world", "base"):
            continue
        if any(k in name for k in SKIP_FURNITURE) or name.startswith(("breakfast", "cereal")):
            continue
        try:
            m = mesh(name)
        except Exception:
            continue
        furniture.append({"name": name, "category": name.split("Factory")[0],
                          "aabb": np.round(np.r_[m.bounds[0], m.bounds[1]], 3).tolist()})
        # support surfaces: upward faces clustered by height
        up = m.face_normals[:, 2] > 0.97
        if not up.any():
            continue
        zc = m.triangles_center[up, 2]
        areas = m.area_faces[up]
        tris = m.triangles[up]
        order = np.argsort(zc)
        level, groups = None, []
        for i in order:
            if level is None or zc[i] - level > 0.015:
                groups.append([])
            groups[-1].append(i)
            level = zc[i]
        k = 0
        for g in groups:
            A = float(areas[g].sum())
            z = float(np.median(zc[g]))
            if A < 0.03 or z < 0.15 or z > 1.9:
                continue
            xy = tris[g][:, :, :2].reshape(-1, 2)
            lo, hi = xy.min(0), xy.max(0)
            # clearance above this surface up to the next level/ceiling
            supports.append({"name": f"{name}/surface_{k}", "furniture": name,
                             "category": name.split("Factory")[0], "z": round(z, 3),
                             "area": round(A, 3), "aabb_xy": np.round(np.r_[lo, hi], 3).tolist()})
            k += 1
    # vertical clearance per support (distance to the next surface of the same furniture)
    by_f = {}
    for s in supports:
        by_f.setdefault(s["furniture"], []).append(s)
    for f, ss in by_f.items():
        ss.sort(key=lambda s: s["z"])
        top = next(o["aabb"][5] for o in furniture if o["name"] == f)
        for a, b in zip(ss, ss[1:] + [None]):
            a["clearance"] = round((b["z"] if b else top + 1.0) - a["z"], 3)
    return {"rooms": rooms, "walls": walls, "furniture": furniture, "supports": supports}


def room_of(rooms, xy):
    x, y = xy
    for name, r in rooms.items():
        a = r["aabb_xy"]
        if not (a[0] <= x <= a[2] and a[1] <= y <= a[3]):
            continue
        for t in r["triangles"]:
            (x1, y1), (x2, y2), (x3, y3) = t
            d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(d) < 1e-12:
                continue
            l1 = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d
            l2 = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d
            if l1 >= -1e-6 and l2 >= -1e-6 and 1 - l1 - l2 >= -1e-6:
                return name
    return None


def main():
    scene, out = Path(sys.argv[1]), Path(sys.argv[2])
    if not STATIC.exists():
        STATIC.parent.mkdir(parents=True, exist_ok=True)
        STATIC.write_text(json.dumps(house_static()))
    static = json.loads(STATIC.read_text())

    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    from pxr import Gf, Usd, UsdGeom, UsdPhysics
    stage = Usd.Stage.Open(str(scene))
    cache = UsdGeom.XformCache()

    def bounds(prim):
        r = UsdGeom.Imageable(prim).ComputeWorldBound(0, "default").ComputeAlignedRange()
        return np.array(r.GetMin()), np.array(r.GetMax())

    def M(prim):
        return np.array(cache.GetLocalToWorldTransform(prim)).T      # USD is row-vector

    obstacles = [{"name": f["name"], "kind": "furniture", "aabb": f["aabb"]} for f in static["furniture"]]
    for i, (x1, y1, x2, y2) in enumerate(static["walls"]):
        obstacles.append({"name": f"wall_{i}", "kind": "wall",
                          "aabb": [min(x1, x2) - 0.02, min(y1, y2) - 0.02, 0.0,
                                   max(x1, x2) + 0.02, max(y1, y2) + 0.02, 2.4]})
    supports = list(static["supports"])
    for p in (stage.GetPrimAtPath("/World/SupportRepairs").GetChildren()
              if stage.GetPrimAtPath("/World/SupportRepairs") else []):
        lo, hi = bounds(p)
        supports.append({"name": f"repair/{p.GetName()}", "furniture": "SupportRepair", "category": "counter",
                         "z": round(float(hi[2]), 3), "aabb_xy": np.round(np.r_[lo[:2], hi[:2]], 3).tolist(),
                         "clearance": 0.8})

    articulated = []
    root = stage.GetPrimAtPath("/World/ArticulatedAssets")
    for prim in Usd.PrimRange(root):
        if not (prim.IsA(UsdPhysics.RevoluteJoint) or prim.IsA(UsdPhysics.PrismaticJoint)):
            continue
        j = UsdPhysics.Joint(prim)
        cab = prim.GetParent().GetParent()
        b0 = stage.GetPrimAtPath(j.GetBody0Rel().GetTargets()[0])
        b1 = stage.GetPrimAtPath(j.GetBody1Rel().GetTargets()[0])
        M0 = M(b0)
        lp = np.array(j.GetLocalPos0Attr().Get(), float)
        lr = j.GetLocalRot0Attr().Get()
        from scipy.spatial.transform import Rotation
        Rj = M0[:3, :3] @ Rotation.from_quat([*lr.GetImaginary(), lr.GetReal()]).as_matrix()
        pivot = M0[:3, :3] @ lp + M0[:3, 3]
        ax = {"X": 0, "Y": 1, "Z": 2}[prim.GetAttribute("physics:axis").Get()]
        axis = Rj[:, ax]
        rev = prim.IsA(UsdPhysics.RevoluteJoint)
        lo_l, hi_l = prim.GetAttribute("physics:lowerLimit").Get(), prim.GetAttribute("physics:upperLimit").Get()
        if rev:
            lo_l, hi_l = math.radians(lo_l), math.radians(hi_l)
        closed = 0.0
        far = lo_l if abs(lo_l) > abs(hi_l) else hi_l
        open_q = max(min(far, 1.40), -1.40) if rev else 0.85 * far
        P1 = M(b1)
        # moving-part box in its own frame (all colliders of the part)
        pts = []
        part_boxes = []          # one box per collider (panel, handle, standoffs) in the part frame
        handle = None
        for c in Usd.PrimRange(b1):
            if c.HasAPI(UsdPhysics.CollisionAPI):
                lo, hi = bounds(c)
                corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
                pts.append(corners)
                lc = (corners - P1[:3, 3]) @ P1[:3, :3]
                part_boxes.append([lc.min(0).round(4).tolist(), lc.max(0).round(4).tolist()])
            if c.GetName() == "handle":
                handle = c
        pts = np.concatenate(pts)
        local = (pts - P1[:3, 3]) @ P1[:3, :3]
        part_box = [local.min(0).round(4).tolist(), local.max(0).round(4).tolist()]
        # handle frame: bar centre; outward = from panel toward bar; along =
        # horizontal in the face, pointing toward the pivot (revolute) or +x
        h = None
        if handle is not None:
            hlo, hhi = bounds(handle)
            hc = (hlo + hhi) / 2
            panel_c = P1[:3, :3] @ ((np.array(part_box[0]) + np.array(part_box[1])) / 2) + P1[:3, 3]
            ext = np.array(part_box[1]) - np.array(part_box[0])
            thin = int(np.argmin(ext))
            n = P1[:3, :3][:, thin]
            if np.dot(hc - panel_c, n) < 0:
                n = -n
            n[2] = 0.0
            n /= np.linalg.norm(n)
            if rev:
                along = np.cross(axis, n) if np.dot(np.cross(axis, n), pivot - hc) > 0 else -np.cross(axis, n)
            else:
                along = np.cross([0, 0, 1.0], n)
            along[2] = 0.0
            along /= np.linalg.norm(along)
            # pulling the handle along +outward must open the part
            if not rev and np.dot(axis, n) * (open_q - closed) < 0:
                pass
            h = {"prim": str(handle.GetPath()), "center": hc.round(4).tolist(), "outward": n.round(4).tolist(),
                 "along": along.round(4).tolist(), "bar_axis": [0, 0, 1],
                 "bar_size": (hhi - hlo).round(4).tolist(), "grasp": "side"}
        articulated.append({
            "name": cab.GetName(), "prim": str(cab.GetPath()), "joint": str(prim.GetPath()),
            "type": "revolute" if rev else "prismatic", "pivot": pivot.round(4).tolist(),
            "axis": axis.round(4).tolist(), "limits": [lo_l, hi_l], "closed_q": closed,
            "open_q": round(open_q, 3), "part": str(b1.GetPath()), "part_frame": P1.round(5).tolist(),
            "part_box": part_box, "part_boxes": part_boxes, "handle": h,
            "room": room_of(static["rooms"], pivot[:2]),
            "category": "microwave" if "microwave" in cab.GetName() else ("drawer" if not rev else "cabinet_door"),
        })
        body = stage.GetPrimAtPath(j.GetBody0Rel().GetTargets()[0])
        lo, hi = bounds(body)
        articulated[-1]["body_aabb"] = np.r_[lo, hi].round(3).tolist()
        # carcass as its panels (top, sides, back, shelf...): the inside is free
        # space, so the arm can reach into an opened cabinet
        panels = [c for c in Usd.PrimRange(body) if c != body and c.HasAPI(UsdPhysics.CollisionAPI)]
        if not panels:
            panels = [body]
        pb = []
        for c in panels:
            plo, phi = bounds(c)
            pb.append((c.GetName(), plo, phi))
            obstacles.append({"name": f"{cab.GetName()}/body/{c.GetName()}", "kind": "articulated_panel",
                              "aabb": np.r_[plo, phi].round(3).tolist()})
        # horizontal panels inside the carcass (bottom, shelf) hold things too
        for name, plo, phi in pb:
            if name in ("bottom", "shelf") and phi[2] - plo[2] < 0.05:
                above = [q[1][2] for q in pb if q[1][2] > phi[2] + 0.02 and
                         q[1][0] < phi[0] and q[2][0] > plo[0] and q[1][1] < phi[1] and q[2][1] > plo[1]]
                supports.append({"name": f"{cab.GetName()}/inside_{name}", "furniture": cab.GetName(),
                                 "category": "cabinet_inside", "z": round(float(phi[2]), 3),
                                 "aabb_xy": np.r_[plo[:2], phi[:2]].round(3).tolist(),
                                 "clearance": round(float(min(above) - phi[2]), 3) if above else 0.3})
        # carcass top is a support surface too
        supports.append({"name": cab.GetName() + "/top", "furniture": cab.GetName(), "category": "cabinet_top",
                         "z": round(float(hi[2]), 3), "aabb_xy": np.r_[lo[:2], hi[:2]].round(3).tolist(),
                         "clearance": 1.0})

    objects = []
    assets_dir = ROOT / "usd/assets"
    for group in ("/World/TaskAssets", "/World/Tasks"):
        g = stage.GetPrimAtPath(group)
        if not g:
            continue
        for p in Usd.PrimRange(g):
            body = None
            if p.GetParent() and p.GetParent().GetPath() == g.GetPath() or \
                    (group == "/World/Tasks" and p.GetMetadata("kind") == "component"):
                pass
            if not p.HasAPI(UsdPhysics.RigidBodyAPI):
                continue
            body = p
            inst = body.GetParent().GetParent() if body.GetParent().GetName() == "Asset" else body.GetParent()
            asset = None
            for q in (inst, inst.GetChild("Asset")):
                if q and q.HasAuthoredReferences():
                    for ref in q.GetMetadata("references").GetAddedOrExplicitItems():
                        asset = Path(str(ref.assetPath)).stem
            asset = asset or body.GetName()
            lo, hi = bounds(inst)
            pos = M(body)[:3, 3]
            below = [s for s in supports if s["aabb_xy"][0] - 0.02 <= pos[0] <= s["aabb_xy"][2] + 0.02
                     and s["aabb_xy"][1] - 0.02 <= pos[1] <= s["aabb_xy"][3] + 0.02 and s["z"] <= lo[2] + 0.03]
            sup = max(below, key=lambda s: s["z"])["name"] if below else None
            objects.append({"name": inst.GetName(), "prim": str(inst.GetPath()), "body": str(body.GetPath()),
                            "asset": asset, "position": pos.round(4).tolist(),
                            "aabb": np.r_[lo, hi].round(4).tolist(),
                            "room": room_of(static["rooms"], pos[:2]), "support": sup})
    rp = stage.GetPrimAtPath("/World/ZenoMalo")
    robot = {"prim": "/World/ZenoMalo", "xy": list(rp.GetAttribute("xformOp:translate").Get())[:2],
             "yaw_deg": rp.GetAttribute("xformOp:rotateZ").Get(), "base_anchor": "/World/ZenoMalo/base_anchor",
             "gripper_max_opening": 0.08, "reach_m": 0.75}
    rel = os.path.relpath(scene, ROOT)
    out.write_text(json.dumps({"scene_usd": rel, "rooms": static["rooms"], "obstacles": obstacles,
                               "supports": supports, "articulated": articulated, "objects": objects,
                               "robot": robot}, indent=1))
    print("ANNOTATION", out, "articulated", len(articulated), "objects", len(objects),
          "supports", len(supports), "obstacles", len(obstacles), flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
