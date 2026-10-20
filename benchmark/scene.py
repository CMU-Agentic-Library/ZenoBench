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
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def rz(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def difficulty_of(v: dict) -> str:
    """easy: no failure / alternative condition; medium: one; hard: several."""
    return v.get("difficulty", "easy" if not v.get("conditions") else
                 "medium" if len(v["conditions"]) == 1 else "hard")


def episode_config(task: dict, seed: int, variant: str | None = None, difficulty: str | None = None) -> dict:
    """Variant + overlay of one episode (deterministic in the seed).  With
    ``difficulty`` the seed picks among that tier's variants only."""
    rng = random.Random(f"{task['task_id']}:{seed}")
    variants = task["variants"]
    if variant is None:
        names = sorted(n for n, v in variants.items() if difficulty is None or difficulty_of(v) == difficulty)
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
    blob = json.dumps({k: r(cfg.get(k)) for k in PHYSICAL_KEYS}, sort_keys=True)
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
            m = dict(cfg["move"][n])
            m["xy"] = [round(m["xy"][0] + dx, 4), round(m["xy"][1] + dy, 4)]
            m["yaw_deg"] = round(m.get("yaw_deg", 0.0) + dyaw, 2)
            cfg["move"][n] = m
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
    return prepare
