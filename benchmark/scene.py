"""Per-episode scene: a task's fixed base scene plus a local overlay.

The house layout and furniture never change.  An episode may only

* remove objects (the prim is deactivated before the simulation starts and
  the object leaves the annotation), and
* re-place objects that already exist in the scene on an annotated support
  (``move``: bottom-centre xy on a support, yaw), e.g. a book at the island
  edge or two bowls in the microwave.

A condition is a variant (variant_id); the seed never chooses the condition in
the evaluation matrix (benchmark/matrix.py enumerates every variant).  The seed
draws a random subset of removable distractors and, where a variant declares
safe ranges (``vary``), a small shift of objects and of the robot start.  The
--difficulty entry point (seed picks a variant of one tier) is kept for single
episodes.  ``episode_config``
returns everything needed to rebuild the episode exactly.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))          # also when imported as `scene` from benchmark/ (make_batches)
from episode.catalog import difficulty_of, selectable_variants  # noqa: E402,F401  (difficulty_of: re-exported)


def rz(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])



def episode_config(task: dict, seed: int, variant: str | None = None, difficulty: str | None = None) -> dict:
    """Variant + overlay of one episode (deterministic in the seed).  Without a variant the seed
    picks among the graded variants (episode.catalog.selectable_variants: never a diagnostic
    one), with ``difficulty`` among that tier's only."""
    rng = random.Random(f"{task['task_id']}:{seed}")
    variants = task["variants"]
    if variant is None:
        names = selectable_variants(task, difficulty)
        if not names:
            raise ValueError(f"{task['task_id']}: no {difficulty} variant")
        variant = names[seed % len(names)]
    v = variants[variant]
    scene = task["scene"]
    remove = list(scene.get("remove", [])) + list(v.get("remove", []))
    move = dict(scene.get("move", {}))
    move.update(v.get("move", {}))
    pool = [d for d in scene.get("distractors", []) if d not in remove and d not in move]
    k = rng.randint(0, len(pool)) if pool else 0
    dropped = sorted(rng.sample(pool, k)) if pool else []
    cfg = {"task_id": task["task_id"], "seed": seed, "variant": variant, "variant_note": v.get("note", ""),
           "difficulty": difficulty_of(v), "conditions": list(v.get("conditions", [])),
           "base": scene["base"], "remove": sorted(set(remove) | set(dropped)), "distractors_removed": dropped,
           "move": move, "start": v.get("start", scene.get("start")),
           # appliance heat/cool sources of this episode (None: the scene default); a variant can
           # make an appliance unavailable, e.g. a microwave that runs but does not heat
           "thermal_sources": v.get("thermal_sources", scene.get("thermal_sources")),
           # per-food thermal parameters of this episode, e.g. a microwave that runs but does not heat
           "thermal_override": v.get("thermal_override", {})}
    add = {**scene.get("add", {}), **v.get("add", {})}
    if add:
        # objects the base scene does not have (an asset of annotations/assets.json placed like ``move``);
        # only present when used, so the configurations and hashes of every other variant stay as they were
        cfg["add"] = copy.deepcopy(add)
    if v.get("failures"):
        # v5 failure injection (failure_injection/): declared failures of this variant; only present when
        # used, so every earlier configuration and hash stays as it was
        cfg["failures"] = copy.deepcopy(v["failures"])
    vary = v["vary"] if "vary" in v else scene.get("vary")
    if vary:
        apply_vary(cfg, vary, random.Random(f"{task['task_id']}:{variant}:{seed}:vary"))
    cfg["config_hash"] = config_hash(cfg)
    return cfg


PHYSICAL_KEYS = ("base", "remove", "move", "start", "thermal_sources", "thermal_override")


def config_hash(cfg: dict) -> str:
    """Hash of everything that changes the simulated episode (not the task, variant or seed labels): two
    episodes with one hash are physical repeats of one configuration."""
    def r(x):
        if isinstance(x, float):
            return round(x, 4)
        if isinstance(x, dict):
            return {k: r(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [r(v) for v in x]
        return x
    keys = PHYSICAL_KEYS + (("add",) if cfg.get("add") else ()) + (("failures",) if cfg.get("failures") else ())
    blob = json.dumps({k: r(cfg.get(k)) for k in keys}, sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def _grid(rng, half, step):
    """A value on the grid -half, ..., +half (step apart), or lo, ..., hi for half = [lo, hi]; 0 when half is 0."""
    if not half:
        return 0.0
    lo, hi = (-half, half) if not isinstance(half, (list, tuple)) else half
    return rng.randint(int(round(lo / step)), int(round(hi / step))) * step


def apply_vary(cfg: dict, vary: dict, rng) -> None:
    """Seeded local variation inside ranges a variant declares as safe (benchmark v3):

    * ``groups``: [{"names": [...], "dx", "dy", "dyaw", "step", "step_deg"}] (a half range, or [lo, hi]) shift / turn every named object
      of ``move`` together (yaw about its own centre), so the gaps between them that make a condition hold
      (a boxed-in block, an overhang) stay exactly as declared;
    * ``start``: {"dx", "dy", "dyaw", "step", "step_deg"} around the episode's start pose (the base scene's
      ``robot_start`` when the variant has none).

    Values are on a grid, so seeds can repeat a configuration; ``config_hash`` tells repeats apart."""
    applied = {}
    for g in vary.get("groups", []):
        dx, dy = _grid(rng, g.get("dx", 0), g.get("step", 0.01)), _grid(rng, g.get("dy", 0), g.get("step", 0.01))
        dyaw = _grid(rng, g.get("dyaw", 0), g.get("step_deg", 5))
        for n in g["names"]:
            where = cfg["move"] if n in cfg["move"] else cfg["add"]       # a moved or an added object
            m = dict(where[n])
            m["xy"] = [round(m["xy"][0] + dx, 4), round(m["xy"][1] + dy, 4)]
            m["yaw_deg"] = round(m.get("yaw_deg", 0.0) + dyaw, 2)
            where[n] = m
        applied["+".join(g["names"])] = [round(dx, 4), round(dy, 4), dyaw]
    if vary.get("start"):
        sv = vary["start"]
        s0 = cfg["start"] or json.loads((ROOT / cfg["base"] / "task.json").read_text())["robot_start"]
        dx, dy = _grid(rng, sv.get("dx", 0), sv.get("step", 0.05)), _grid(rng, sv.get("dy", 0), sv.get("step", 0.05))
        dyaw = _grid(rng, sv.get("dyaw", 0), sv.get("step_deg", 5))
        cfg["start"] = [round(s0[0] + dx, 4), round(s0[1] + dy, 4), round(s0[2] + dyaw, 2)]
        applied["start"] = [round(dx, 4), round(dy, 4), dyaw]
    cfg["vary_applied"] = applied


def build_annotation(cfg: dict, out_path: Path) -> Path:
    """Write the episode annotation: base annotation minus removed objects,
    moved objects at their new pose and support."""
    base = ROOT / cfg["base"]
    ann = json.loads((base / "annotation.json").read_text())
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    sup = {s["name"]: s for s in ann["supports"]}
    objs = []
    for o in ann["objects"]:
        if o["name"] in cfg["remove"]:
            continue
        m = cfg["move"].get(o["name"])
        if m:
            o = copy.deepcopy(o)
            a = assets[o["asset"]]
            pos, quat = overlay_pose(a, m, sup)
            o["position"] = [round(float(v), 4) for v in pos]
            half = np.abs(rz(math.radians(m.get("yaw_deg", 0.0)))) @ (np.asarray(a["size"], float) / 2)
            b = np.asarray(pos) + rz(math.radians(m.get("yaw_deg", 0.0))) @ np.asarray(a["origin_to_bottom_center"])
            o["aabb"] = [float(b[0] - half[0]), float(b[1] - half[1]), float(b[2]),
                         float(b[0] + half[0]), float(b[1] + half[1]), float(b[2] + a["size"][2])]
            o["support"] = m.get("support")
            o.pop("inside", None)
        objs.append(o)
    for name, m in (cfg.get("add") or {}).items():
        a = assets[m["asset"]]
        pos, _ = overlay_pose(a, m, sup)
        yaw = math.radians(m.get("yaw_deg", 0.0))
        half = np.abs(rz(yaw)) @ (np.asarray(a["size"], float) / 2)
        b = np.asarray(pos) + rz(yaw) @ np.asarray(a["origin_to_bottom_center"])
        from zeno_skills.evaluator import room_of
        room = room_of(ann.get("rooms", {}), (float(b[0]), float(b[1])))
        objs.append({"name": name, "prim": f"{ADD_ROOT}/{name}", "body": f"{ADD_ROOT}/{name}/Asset/{m['asset']}",
                     "asset": m["asset"], "position": [round(float(v), 4) for v in pos],
                     "aabb": [float(b[0] - half[0]), float(b[1] - half[1]), float(b[2]),
                              float(b[0] + half[0]), float(b[1] + half[1]), float(b[2] + a["size"][2])],
                     **({"room": room} if room else {}), "support": m.get("support")})
    ann["objects"] = objs
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(ann))
    return out_path


def overlay_pose(asset, m, supports):
    """Body origin + wxyz quaternion that put the asset's bottom centre at
    ``m["xy"]`` on support ``m["support"]`` (or at ``m["z"]``), yawed."""
    yaw = math.radians(m.get("yaw_deg", 0.0))
    z = m.get("z")
    if z is None:
        z = supports[m["support"]]["z"]
    bottom = np.array([m["xy"][0], m["xy"][1], float(z) + m.get("lift", 0.003)])
    pos = bottom - rz(yaw) @ np.asarray(asset["origin_to_bottom_center"], float)
    quat = [math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]
    return pos, quat


def make_prepare(cfg: dict):
    """USD edits applied before the simulation starts."""
    base = ROOT / cfg["base"]
    ann = json.loads((base / "annotation.json").read_text())
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    by = {o["name"]: o for o in ann["objects"]}
    sup = {s["name"]: s for s in ann["supports"]}

    def prepare(stage):
        from pxr import Gf, UsdGeom
        if cfg.get("add"):
            add_objects(stage, cfg["add"], assets, sup)
        for name in cfg["remove"]:
            prim = stage.GetPrimAtPath(by[name]["prim"])
            if prim.IsValid():
                prim.SetActive(False)
        for name, m in cfg["move"].items():
            o = by[name]
            prim = stage.GetPrimAtPath(o["prim"])
            pos, q = overlay_pose(assets[o["asset"]], m, sup)
            xf = UsdGeom.Xformable(prim)
            ops = {op.GetOpName(): op for op in xf.GetOrderedXformOps()}
            ops["xformOp:translate"].Set(Gf.Vec3d(*[float(v) for v in pos]))
            orient = ops["xformOp:orient"]
            val = Gf.Quatd(q[0], Gf.Vec3d(q[1], q[2], q[3]))
            orient.Set(val if isinstance(orient.Get(), Gf.Quatd) else Gf.Quatf(val))
        spawn_at_start(stage, cfg)
    return prepare


ROBOT_PRIM, ROBOT_ANCHOR = "/World/ZenoMalo", "/World/ZenoMalo/base_anchor"
SPAWN_SLIDE_M = 1.0


def spawn_at_start(stage, cfg: dict) -> bool:
    """Put the robot at a far ``start`` before the simulation starts.  The episode reset slides the
    anchored base from the scene's spawn to ``start`` in a straight line; across a room that line goes
    through the kitchen island and the fridge and knocks objects off before the first step.  Short
    offsets (seed jitter) keep the slide."""
    from pxr import Gf, UsdGeom
    if not cfg.get("start"):
        return False
    ops = {op.GetOpName(): op for op in UsdGeom.Xformable(stage.GetPrimAtPath(ROBOT_PRIM)).GetOrderedXformOps()}
    s0 = ops["xformOp:translate"].Get()
    x, y, yaw = (float(v) for v in cfg["start"])
    if math.hypot(x - s0[0], y - s0[1]) <= SPAWN_SLIDE_M:
        return False
    ops["xformOp:translate"].Set(Gf.Vec3d(x, y, s0[2]))
    if "xformOp:rotateZ" in ops:
        ops["xformOp:rotateZ"].Set(yaw)
    else:
        UsdGeom.Xformable(stage.GetPrimAtPath(ROBOT_PRIM)).AddRotateZOp().Set(yaw)
    anchor = stage.GetPrimAtPath(ROBOT_ANCHOR)
    z = anchor.GetAttribute("physics:localPos0").Get()[2]
    anchor.GetAttribute("physics:localPos0").Set(Gf.Vec3f(x, y, z))
    h = math.radians(yaw) / 2
    anchor.GetAttribute("physics:localRot0").Set(Gf.Quatf(math.cos(h), 0.0, 0.0, math.sin(h)))
    return True


ADD_ROOT = "/World/Tasks"           # added objects sit next to the base scene's task objects


def add_objects(stage, add: dict, assets: dict, supports: dict):
    """Author the added objects into the stage before the simulation starts, the way
    tools/build_tasks.py authors a base scene's task objects (reference, inertia, colliders)."""
    from pxr import Gf, UsdGeom
    from zeno_skills import physics as P
    mats = P.materials(stage)
    for name, m in add.items():
        spec = assets[m["asset"]]
        pos, _ = overlay_pose(spec, m, supports)
        root = f"{ADD_ROOT}/{name}"
        x = UsdGeom.Xform.Define(stage, root)
        x.AddTranslateOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(Gf.Vec3d(*[float(v) for v in pos]))
        x.AddOrientOp(precision=UsdGeom.XformOp.PrecisionDouble).Set(
            Gf.Quatd(math.cos(math.radians(m.get("yaw_deg", 0.0)) / 2), Gf.Vec3d(0, 0, math.sin(math.radians(m.get("yaw_deg", 0.0)) / 2))))
        a = stage.DefinePrim(f"{root}/Asset")
        a.GetReferences().AddReference(str(ROOT / spec["usd"]))
        P.set_box_inertia(stage, root, spec["mass"])
        if max(spec["size"]) < 0.06:
            from pxr import PhysxSchema
            rb = PhysxSchema.PhysxRigidBodyAPI.Apply(P.body_prim(stage, root))
            rb.CreateEnableCCDAttr().Set(True)
            rb.CreateAngularDampingAttr().Set(3.0)
        if spec.get("container"):
            c = spec["container"]
            P.container_collider(stage, root, c["bands"], shape=c["shape"], mats=mats,
                                 handle=c.get("handle_collider"), extra_handles=c.get("extra_handle_colliders", []))
        else:
            P.solid_collider(stage, root, mats=mats)
