"""Build task scenes as USD layers over sim/zeno_house.usd (rooms untouched;
only furniture-top / floor assets are added) + a machine-readable task spec.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} \
        tools/build_tasks.py --task collect_fruits [--seed 0]

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

DINING = "TableDiningFactory_1437886_spawn_asset_2104395/surface_2"
TV = "TVStandFactory_6305370_spawn_asset_6627927/surface_1"
DESK = "SimpleDeskFactory_5016639_spawn_asset_2990980/surface_1"
DESK2 = "SimpleDeskFactory_7424700_spawn_asset_8101679/surface_0"
SHELF_TOP = "CellShelfFactory_2688822_spawn_asset_5011983/surface_4"
SHELF_MID = "CellShelfFactory_2688822_spawn_asset_5011983/surface_2"
CELL2 = "CellShelfFactory_867098_spawn_asset_5571502/surface_2"
COUNTER = "repair/kitchen_counter_top"
BOOKCASE = "SimpleBookcaseFactory_2318999_spawn_asset_8416993"
BOOKCASE2 = "SimpleBookcaseFactory_6105320_spawn_asset_9196243"
MATTRESS = "MattressFactory_4281756_spawn_asset_1415123/surface_0"
SIDEBOARD = "KitchenCabinetFactory_7025538_spawn_asset_6631478/top"
# floor areas (room, x0, y0, x1, y1): open floor away from furniture
FLOOR_LIVING = ("floor:living_room", 4.2, 1.6, 6.2, 3.0)
FLOOR_BEDROOM = ("floor:bedroom", 3.4, -4.4, 6.0, -1.2)
FLOOR_BEDROOM2 = ("floor:bedroom2", 0.2, -2.6, 2.2, -1.0)

TASKS = {
    "breakfast_setup": {
        "instruction": "Set up the dining table for breakfast.",
        "robot_start_near": (1.6, 8.4),
        "objects": {},                         # the base scene already holds the breakfast set
        "existing": {"plate": ["plate_counter_a", "plate_counter_b", "plate_dining_cabinet",
                               "plate_inside_kitchen_cabinet"],
                     "bowl_fallback": ["bowl_dining_cabinet", "bowl_kitchen_cabinet", "bowl_side_table",
                                       "bowl_inside_kitchen_cabinet"],
                     "cup": ["cup_counter_b", "cup_kitchen_cabinet", "cup_side_table"],
                     "mug_fallback": ["mug_counter", "mug_shelf", "mug_dining_cabinet"],
                     "spoon": ["spoon_counter", "spoon_kitchen_cabinet", "spoon_inside_kitchen_drawer",
                               "spoon_side_table", "spoon_target_table"],
                     "table_clutter": ["clutter_cereal_a", "clutter_cereal_b"]},
        "drop_existing": {"plate": 0.25, "cup": 0.25},
        "target": {"support": DINING, "place_xy": {"plate": [3.16, 6.75], "cup": [3.45, 6.75],
                                                    "spoon": [3.30, 6.45]}},
        "alternatives": ["plate missing -> bowl", "cup missing -> mug",
                         "target spot occupied (cereal boxes) -> move clutter off the table first"],
        "success": {"all_of": [{"role": "plate|bowl_fallback", "on_support": DINING},
                               {"role": "cup|mug_fallback", "on_support": DINING},
                               {"role": "spoon", "on_support": DINING}]},
    },
    "collect_fruits": {
        "instruction": "Collect the fruits and place them in a container on the dining table.",
        "robot_start_near": (3.3, 4.9),
        "objects": {
            "apple": {"asset": "apple", "supports": [COUNTER, DINING, TV]},
            "banana": {"asset": "banana", "supports": [TV, SHELF_TOP, DESK2]},
            "orange": {"asset": "orange", "supports": [DINING, COUNTER, SHELF_MID]},
            "fruit_basket": {"asset": "fruit_basket", "supports": [DINING], "optional": 0.3},
            "serving_tray": {"asset": "serving_tray", "supports": [DINING]},
        },
        "alternatives": ["fruit_basket missing -> serving_tray (or the breakfast bowls)"],
        "success": {"all_of": [{"objects": ["apple", "banana", "orange"],
                                "inside_container": "fruit_basket|serving_tray"},
                               {"objects": ["fruit_basket|serving_tray"], "on_support": DINING}]},
    },
    "desk_prep": {
        "instruction": "Prepare the desk with a notebook, a pen, and a mug.",
        "robot_start_near": (5.4, -3.6),
        "objects": {
            "notebook": {"asset": "notebook", "supports": [SHELF_TOP, DINING, TV]},
            "pen": {"asset": "pen", "supports": [DINING, SHELF_MID, TV], "optional": 0.3},
            "pencil": {"asset": "pencil", "supports": [f"{BOOKCASE2}/surface_3", DESK2]},
        },
        "existing": {"mug": ["mug_shelf", "mug_counter", "mug_dining_cabinet"],
                     "cup_fallback": ["cup_counter_b", "cup_kitchen_cabinet", "cup_side_table"]},
        "alternatives": ["mug missing -> cup", "pen missing -> pencil"],
        "success": {"all_of": [{"objects": ["notebook", "pen|pencil"], "on_support": DESK},
                               {"role": "mug|cup_fallback", "on_support": DESK}]},
    },
    "tidy_toys": {
        "instruction": "Collect the toys and store them in the toy box.",
        "robot_start_near": (4.3, -2.2),
        "objects": {
            "toy_car": {"asset": "toy_car", "supports": [FLOOR_LIVING, TV]},
            "teddy_bear": {"asset": "teddy_bear", "supports": [FLOOR_BEDROOM, MATTRESS]},
            "toy_block": {"asset": "toy_block", "supports": [FLOOR_BEDROOM, FLOOR_BEDROOM2, DESK]},
            "rubber_duck": {"asset": "rubber_duck", "supports": [TV, FLOOR_LIVING]},
            "toy_box": {"asset": "toy_box", "supports": [FLOOR_BEDROOM], "optional": 0.3},
            "storage_basket": {"asset": "storage_basket", "supports": [FLOOR_BEDROOM2, FLOOR_LIVING]},
        },
        "alternatives": ["toy_box missing -> storage_basket"],
        "success": {"all_of": [{"objects": ["toy_car", "teddy_bear", "toy_block", "rubber_duck"],
                                "inside_container": "toy_box|storage_basket"}]},
    },
    "shelve_books": {
        "instruction": "Collect the books and place them on the bookshelf.",
        "robot_start_near": (1.2, -3.8),
        "objects": {
            "book_red": {"asset": "book_red", "supports": [DESK2, DESK]},
            "book_green": {"asset": "book_green", "supports": [FLOOR_BEDROOM2, FLOOR_BEDROOM]},
            "book_blue": {"asset": "book_blue", "supports": [MATTRESS, TV]},
            "shelf_blocker": {"asset": "rubber_duck", "supports": [f"{BOOKCASE}/surface_1"]},
        },
        "alternatives": ["middle shelf occupied (toy duck) -> another shelf level or bookcase "
                         f"{BOOKCASE2}", "book hard to grasp (flat, wider than the gripper) -> "
                         "push it over a support edge, then pinch the overhang"],
        "success": {"all_of": [{"objects": ["book_red", "book_green", "book_blue"],
                                "on_support_of": [BOOKCASE, BOOKCASE2]}]},
    },
}


def support_box(ann, name):
    if isinstance(name, tuple):                      # floor area
        _, x0, y0, x1, y1 = name
        return {"name": name[0], "z": 0.0, "aabb_xy": [x0, y0, x1, y1], "clearance": 2.0}
    for s in ann["supports"]:
        if s["name"] == name:
            return s
    raise KeyError(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=sorted(TASKS))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    spec = TASKS[args.task]
    rng = np.random.default_rng(args.seed)
    out = ROOT / "tasks" / args.task
    out.mkdir(parents=True, exist_ok=True)
    base_ann = json.loads((ROOT / "annotations/zeno_house.json").read_text())
    assets = json.loads((ROOT / "annotations/assets.json").read_text())

    # ---- sample placements (kinematic, collision-free vs placed + existing)
    taken = [np.array(o["aabb"]) for o in base_ann["objects"]]
    placements, dropped = {}, []
    for name, o in spec.get("objects", {}).items():
        if rng.random() < o.get("optional", 0.0):
            dropped.append(name)
            continue
        a = assets[o["asset"]]
        sx, sy, sz = a["size"]
        ok = False
        for attempt in range(200):
            sup = o["supports"][rng.integers(len(o["supports"]))] if attempt > 20 else o["supports"][0]
            s = support_box(base_ann, sup)
            yaw = float(rng.uniform(-math.pi, math.pi)) if "flat" not in a["tags"] else float(rng.choice([0, math.pi / 2]))
            c, sn = abs(math.cos(yaw)), abs(math.sin(yaw))
            hx, hy = (c * sx + sn * sy) / 2 + 0.02, (sn * sx + c * sy) / 2 + 0.02
            x0, y0, x1, y1 = s["aabb_xy"]
            if x1 - x0 < 2 * hx or y1 - y0 < 2 * hy or s.get("clearance", 1) < sz + 0.02:
                continue
            x, y = rng.uniform(x0 + hx, x1 - hx), rng.uniform(y0 + hy, y1 - hy)
            # reachability-aware: Zeno's arm reaches ~0.4 m past a furniture
            # edge, so objects sit in a band along the edges of big surfaces
            if not str(s["name"]).startswith("floor:") and \
                    min(x - x0, x1 - x, y - y0, y1 - y) > max(hx, hy) + 0.12:
                continue
            box = np.array([x - hx, y - hy, s["z"], x + hx, y + hy, s["z"] + sz])
            if any((box[0] < t[3] and t[0] < box[3] and box[1] < t[4] and t[1] < box[4]
                    and box[2] < t[5] and t[2] < box[5]) for t in taken):
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

    # ---- robot start: nearest free base pose
    from zeno_skills.annotations import SceneAnnotations
    from zeno_skills.collision import WorldModel
    ann = SceneAnnotations(ROOT / "annotations/zeno_house.json")
    world = WorldModel(ann)
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
    layer.subLayerPaths.append("../../sim/zeno_house.usd")
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
        if spec_a.get("container"):
            c = spec_a["container"]
            P.container_collider(stage, f"/World/Tasks/{name}", c["bands"], shape=c["shape"], mats=mats)
        else:
            P.solid_collider(stage, f"/World/Tasks/{name}", mats=mats)
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

    task = {"task": args.task, "instruction": spec["instruction"], "seed": args.seed,
            "scene_usd": f"tasks/{args.task}/scene.usd", "annotation": f"tasks/{args.task}/annotation.json",
            "robot": "Zeno Malo EDU (right arm + 8 cm pinch gripper, holonomic base)",
            "robot_start": start, "placed_objects": placements, "dropped_optional_objects": dropped,
            "deactivated_base_objects": removed, "existing_objects": spec.get("existing", {}),
            "candidate_supports": {k: [s if isinstance(s, str) else s[0] for s in v["supports"]]
                                   for k, v in spec.get("objects", {}).items()},
            "alternatives": spec["alternatives"], "success": spec["success"]}
    if "target" in spec:
        task["target"] = spec["target"]
    (out / "task.json").write_text(json.dumps(task, indent=1))
    print("TASK", args.task, "placed", list(placements), "dropped", dropped, "removed", removed,
          "robot", [round(v, 2) for v in start], flush=True)
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
