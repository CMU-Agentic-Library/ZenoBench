"""Build task scenes as USD layers over sim/zeno_house.usd (rooms untouched;
only furniture-top / floor assets are added) + a machine-readable task file.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} \
        tools/build_tasks.py --task collect_fruits [--seed 0]
    # a task of your own (any path; see README "Define your own task")
    ... tools/build_tasks.py --spec my_specs/serve_guest.json [--seed 0] [--out tasks/serve_guest]

The task definition is task_specs/<task>.json (places may be aliases from
task_specs/places.json).

Output: tasks/<task>/scene.usd (sublayers ../../sim/zeno_house.usd),
        tasks/<task>/task.json.  Then run settle_scene.py / check_scene.py /
        annotate_scene.py on the scene (tools/make_tasks.sh does all of it).

Randomization: every object has a list of candidate supports; the seed picks
the support, the position on it (collision-free vs. other placed objects) and
the yaw; `optional` objects are dropped with the given probability so the
alternative/recovery branches of the task are exercised.
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
from zeno_skills.tasks import place_name  # noqa: E402


def support_box(ann, name):
    if isinstance(name, dict):                       # floor area
        x0, y0, x1, y1 = name["xy"]
        return {"name": place_name(name), "z": 0.0, "aabb_xy": [x0, y0, x1, y1],
                "clearance": 2.0}
    for s in ann["supports"]:
        if s["name"] == name:
            return s
    raise KeyError(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", help="name of a spec in task_specs/")
    ap.add_argument("--spec", help="path of a task spec JSON (your own task)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", help="output directory (default tasks/<task>)")
    ap.add_argument("--no-reach-check", action="store_true", help="skip the (slow) arm reachability test")
    args = ap.parse_args()
    from zeno_skills.tasks import load_places, load_spec, resolve_goal, resolve_place
    spec = load_spec(args.spec or args.task)
    args.task = spec["task"]
    places = load_places()
    for o in spec.get("objects", {}).values():
        o["supports"] = [resolve_place(p, places) for p in o["supports"]]
    rng = np.random.default_rng(args.seed)
    out = Path(args.out).resolve() if args.out else ROOT / "tasks" / args.task
    out.mkdir(parents=True, exist_ok=True)
    base_scene = spec.get("base_scene", "sim/zeno_house.usd")
    base_annotation = spec.get("base_annotation", "annotations/zeno_house.json")
    base_ann = json.loads((ROOT / base_annotation).read_text())
    assets = json.loads((ROOT / "annotations/assets.json").read_text())

    # ---- reachability: Zeno must be able to pinch the object where it is put
    # (a container: drop into it) from some collision-free base pose
    from zeno_skills.annotations import SceneAnnotations
    from zeno_skills.collision import WorldModel
    from zeno_skills.kinematics import ArmKin, gripper_rot
    from zeno_skills.planner import find_park
    ann = SceneAnnotations(ROOT / base_annotation)
    world = WorldModel(ann)
    kin = ArmKin()
    kin.scene = world
    kin.coll_kw = {"ignore_fingers": True}

    def reachable(x, y, z_top, a):
        if a.get("container"):                      # drop point: just above the rim
            z = z_top - a["size"][2] + a["container"]["rim_height"] + 0.05
        else:
            z = z_top - min(0.03, a["size"][2] / 2)
        R = gripper_rot([0, 0, -1.0], [1.0, 0.0, 0.0])
        p = np.array([x, y, max(z, 0.03)])
        legs = [(p + np.array([0, 0, 0.08]), R), (p + np.array([0, 0, 0.03]), R), (p, R),
                (p + np.array([0, 0, 0.07]), R)]
        return find_park(kin, world, legs, near=(x, y), max_tries=40, travel_q=kin.rest) is not None

    # ---- sample placements (kinematic, collision-free vs placed + existing, reachable)
    taken = [np.array(o["aabb"]) for o in base_ann["objects"]]
    placements, dropped = {}, []
    for name, o in spec.get("objects", {}).items():
        if rng.random() < o.get("optional", 0.0):
            dropped.append(name)
            continue
        a = assets[o["asset"]]
        if o.get("inside") or o.get("on_object"):
            # Spawned in or on an already placed object: inside a container
            # (a ring of small items above its floor) or resting on its rim/top.
            host = o.get("inside") or o.get("on_object")
            hp = placements[host]
            ha = assets[hp["asset"]]
            hb = np.array(hp["position"]) + np.r_[np.array([[math.cos(hp["yaw"]), -math.sin(hp["yaw"])],
                                                            [math.sin(hp["yaw"]), math.cos(hp["yaw"])]])
                                                  @ np.array(ha["origin_to_bottom_center"][:2]),
                                                  ha["origin_to_bottom_center"][2]]
            ob = np.array(a["origin_to_bottom_center"])
            if o.get("inside"):
                k = sum(1 for v in placements.values() if v.get("inside") == host)
                ring = float(o.get("ring_m", 0.02))
                ang = 2 * math.pi / 3 * (k % 3) + (math.pi / 3 if (k // 3) % 2 else 0.0)
                z = hb[2] + 0.015 + a["size"][2] * 0.95 * (k // 3)
                x, y = hb[0] + ring * math.cos(ang), hb[1] + ring * math.sin(ang)
            else:
                rim = ha["container"]["rim_height"] if ha.get("container") else ha["size"][2]
                x, y, z = hb[0], hb[1], hb[2] + rim + 0.004
            placements[name] = {"asset": o["asset"], "support": None, "yaw": 0.0,
                                ("inside" if o.get("inside") else "on_object"): host,
                                "position": [float(x - ob[0]), float(y - ob[1]), float(z - ob[2])]}
            continue
        sx, sy, sz = a["size"]
        ok = False
        for attempt in range(120):
            sup = o["supports"][rng.integers(len(o["supports"]))] if attempt > 12 else o["supports"][0]
            s = support_box(base_ann, sup)
            yaw = float(rng.uniform(-math.pi, math.pi)) if "flat" not in a["tags"] else float(rng.choice([0, math.pi / 2]))
            if attempt == 0 and o.get("spawn_yaw_deg") is not None:
                yaw = math.radians(float(o["spawn_yaw_deg"]))
            c, sn = abs(math.cos(yaw)), abs(math.sin(yaw))
            hx, hy = (c * sx + sn * sy) / 2 + 0.02, (sn * sx + c * sy) / 2 + 0.02
            x0, y0, x1, y1 = s["aabb_xy"]
            if x1 - x0 < 2 * hx or y1 - y0 < 2 * hy or s.get("clearance", 1) < sz + 0.02:
                continue
            x, y = rng.uniform(x0 + hx, x1 - hx), rng.uniform(y0 + hy, y1 - hy)
            if attempt == 0 and o.get("spawn_xy") is not None:
                x, y = map(float, o["spawn_xy"])
                if not (x0 + hx <= x <= x1 - hx and y0 + hy <= y <= y1 - hy):
                    raise ValueError(f"{name}: spawn_xy outside {s['name']} safe region")
            # reachability-aware: Zeno's arm reaches ~0.4 m past a furniture
            # edge, so objects sit in a band along the edges of big surfaces
            fixed = attempt == 0 and o.get("spawn_xy") is not None
            if not str(s["name"]).startswith("floor") and \
                    min(x - x0, x1 - x, y - y0, y1 - y) > max(hx, hy) + 0.12:
                if fixed:
                    print(f"WARN {name}: spawn_xy too far from every edge of {s['name']}; sampling instead")
                continue
            box = np.array([x - hx, y - hy, s["z"], x + hx, y + hy, s["z"] + sz])
            hit = [t for t in taken if box[0] < t[3] and t[0] < box[3] and box[1] < t[4] and t[1] < box[4]
                   and box[2] < t[5] and t[2] < box[5]]
            if hit:
                if fixed:
                    print(f"WARN {name}: spawn_xy box {np.round(box, 3).tolist()} overlaps "
                          f"{[np.round(t, 3).tolist() for t in hit]}; sampling instead")
                continue
            # floor spots are all reachable (torso down); blockers etc. opt out
            if not args.no_reach_check and o.get("reach_check", True) and not str(s["name"]).startswith("floor") \
                    and not reachable(x, y, s["z"] + sz, a):
                if fixed:
                    print(f"WARN {name}: spawn_xy not reachable; sampling instead")
                continue
            taken.append(box)
            # body origin = bottom-centre - origin_to_bottom_center (object frame, yaw)
            ob = np.array(a["origin_to_bottom_center"])
            R2 = np.array([[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]])
            oxy = R2 @ ob[:2]
            placements[name] = {"asset": o["asset"], "support": s["name"], "yaw": yaw,
                                "position": [float(x - oxy[0]), float(y - oxy[1]), float(s["z"] - ob[2] + 0.012)]}
            ok = True
            break
        if not ok:
            raise RuntimeError(f"{args.task}: could not place {name}")
    removed = []
    for role, p in spec.get("drop_existing", {}).items():
        for inst in spec["existing"][role]:
            if rng.random() < p:
                removed.append(inst)
    existing = {k: [i for i in v if i not in removed] for k, v in spec.get("existing", {}).items()}
    roles = dict(existing)
    for k, v in spec.get("roles", {}).items():
        roles[k] = [i for i in v if i not in dropped]

    # ---- robot start: nearest free base pose
    sx0, sy0 = spec["robot_start_near"]
    start = None
    for r in np.arange(0.0, 1.6, 0.1):
        for ang in np.radians(np.arange(0, 360, 30)):
            x, y = sx0 + r * math.cos(ang), sy0 + r * math.sin(ang)
            yaw = math.degrees(math.atan2(-y + sy0, -x + sx0)) if r else 0.0
            if world.footprint_clear(x, y, math.radians(yaw), margin=0.15) and \
                    not any(t[0] - 0.4 < x < t[3] + 0.4 and t[1] - 0.4 < y < t[4] + 0.4 for t in taken):
                start = (float(x), float(y), float(yaw))
                break
        if start:
            break
    if start is None:
        raise RuntimeError("no free robot start")

    # ---- author the layer
    from isaaclab.app import AppLauncher
    app = AppLauncher({"headless": True, "no_splash": True, "fast_shutdown": True}).app
    from pxr import Gf, Sdf, Usd, UsdGeom
    from zeno_skills import physics as P
    path = out / "scene.usd"
    layer = Sdf.Layer.CreateNew(str(path)) if not path.exists() else Sdf.Layer.FindOrOpen(str(path))
    layer.Clear()
    layer.subLayerPaths.append(os.path.relpath(ROOT / base_scene, out))
    layer.Save()
    stage = Usd.Stage.Open(str(path))
    stage.SetEditTarget(stage.GetRootLayer())
    mats = P.materials(stage)
    UsdGeom.Xform.Define(stage, "/World/Tasks")
    for name, pl in placements.items():
        x = UsdGeom.Xform.Define(stage, f"/World/Tasks/{name}")
        x.AddTranslateOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(*pl["position"]))
        x.AddRotateZOp().Set(math.degrees(pl["yaw"]))
        a = stage.DefinePrim(f"/World/Tasks/{name}/Asset")
        a.GetReferences().AddReference(os.path.relpath(ROOT / assets[pl["asset"]]["usd"], out))
        spec_a = assets[pl["asset"]]
        P.set_box_inertia(stage, f"/World/Tasks/{name}", spec_a["mass"])
        if max(spec_a["size"]) < 0.06:
            # small, light bodies tunnel through thin walls without CCD
            from pxr import PhysxSchema
            rb = PhysxSchema.PhysxRigidBodyAPI.Apply(P.body_prim(stage, f"/World/Tasks/{name}"))
            rb.CreateEnableCCDAttr().Set(True)
            # PhysX has no rolling resistance: small round items otherwise roll
            # around a cup floor forever.  Angular damping stands in for it.
            rb.CreateAngularDampingAttr().Set(3.0)
        if spec_a.get("container"):
            c = spec_a["container"]
            P.container_collider(stage, f"/World/Tasks/{name}", c["bands"], shape=c["shape"],
                                 mats=mats, handle=c.get("handle_collider"),
                                 extra_handles=c.get("extra_handle_colliders", []))
            # grip bars added to an asset (storage bin end handles) also get a visible mesh
            body = P.body_prim(stage, f"/World/Tasks/{name}")
            for i, hc in enumerate(c.get("extra_handle_colliders", []), start=1):
                if not hc.get("visual"):
                    continue
                bar = UsdGeom.Cube.Define(stage, f"{body.GetPath()}/grip_bar_{i}")
                bar.CreateSizeAttr(1.0)
                bar.AddTransformOp().Set(Gf.Matrix4d().SetScale(Gf.Vec3d(*hc["size"])) *
                                         Gf.Matrix4d().SetTranslate(Gf.Vec3d(*hc["center"])))
                bar.CreateDisplayColorAttr([Gf.Vec3f(0.12, 0.25, 0.55)])
        else:
            P.solid_collider(stage, f"/World/Tasks/{name}", mats=mats)
            if spec_a.get("knob_collider"):
                # a grasp post on a flat knob: collider + matching dark visual
                body = P.body_prim(stage, f"/World/Tasks/{name}")
                kc = spec_a["knob_collider"]
                P.add_handle_collider(stage, str(body.GetPath()), kc, mats=mats, name="knob_collider")
                post = UsdGeom.Cylinder.Define(stage, f"{body.GetPath()}/knob_post")
                post.CreateRadiusAttr(kc["size"][0] / 2)
                post.CreateHeightAttr(kc["size"][2])
                post.AddTranslateOp().Set(Gf.Vec3d(*kc["center"]))
                post.CreateDisplayColorAttr([Gf.Vec3f(0.05, 0.05, 0.05)])
        if o := spec["objects"][name].get("visual_fill"):
            # Food-colored visual inside a pre-existing bowl; no extra collider
            # or rigid body, so the generated object's mass and grasp stay the
            # same. The sphere is authored in the rigid body's local frame.
            body = P.body_prim(stage, f"/World/Tasks/{name}")
            fill = UsdGeom.Sphere.Define(stage, f"{body.GetPath()}/food_fill")
            fill.CreateRadiusAttr(1.0)
            fill.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.016))
            fill.AddScaleOp().Set(Gf.Vec3f(0.068, 0.068, 0.009))
            fill.CreateDisplayColorAttr([Gf.Vec3f(*o)])
    for inst in removed:
        stage.GetPrimAtPath(f"/World/TaskAssets/{inst}").SetActive(False)
    # robot start
    r = stage.GetPrimAtPath(P.ROBOT)
    r.GetAttribute("xformOp:translate").Set(Gf.Vec3d(start[0], start[1], 0.0))
    r.GetAttribute("xformOp:rotateZ").Set(start[2])
    an = stage.GetPrimAtPath(P.ANCHOR)
    z = an.GetAttribute("physics:localPos0").Get()[2]
    an.GetAttribute("physics:localPos0").Set(Gf.Vec3f(start[0], start[1], z))
    yr = math.radians(start[2])
    an.GetAttribute("physics:localRot0").Set(Gf.Quatf(math.cos(yr / 2), 0, 0, math.sin(yr / 2)))
    stage.GetRootLayer().customLayerData = {"task": args.task, "seed": args.seed}
    stage.GetRootLayer().Save()

    rel = os.path.relpath(out, ROOT)
    hints = spec.get("place_hints", {})
    hints = {k: (resolve_place(v, places) if isinstance(v, str) or (isinstance(v, list) and v and isinstance(v[0], str))
                 else v) for k, v in hints.items()}
    task = {"task": args.task, "instruction": spec["instruction"], "instruction_zh": spec.get("instruction_zh"),
            "seed": args.seed, "spec": os.path.relpath(Path(args.spec).resolve(), ROOT) if args.spec
            else f"task_specs/{args.task}.json",
            "scene_usd": f"{rel}/scene.usd", "annotation": f"{rel}/annotation.json",
            "base_scene": base_scene, "thermal": spec.get("thermal", {}),
            "demonstrate_microwave_door": spec.get("demonstrate_microwave_door", False),
            "robot": "Zeno Malo EDU (right arm + 8 cm pinch gripper, holonomic base)",
            "robot_start": start, "placed_objects": placements, "dropped_optional_objects": dropped,
            "deactivated_base_objects": removed, "existing_objects": existing, "roles": roles,
            "candidate_supports": {k: [place_name(s) for s in v["supports"]]
                                   for k, v in spec.get("objects", {}).items()},
            "alternatives": spec.get("alternatives", []), "place_hints": hints,
            "goal": resolve_goal(spec["goal"], places)}
    (out / "task.json").write_text(json.dumps(task, indent=1))
    print("TASK", args.task, "placed", list(placements), "dropped", dropped, "removed", removed,
          "robot", [round(v, 2) for v in start], flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
