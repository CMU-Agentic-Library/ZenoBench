"""Static check of every task variant's overlay: moved objects must sit on
their support and must not intersect another object (no simulator).

    python benchmark/check_layouts.py                                   # v2 task file, seed 0
    python benchmark/check_layouts.py --tasks benchmark/v3/tasks.json  # every variant x evaluation seed (vary applied)
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def boxes(cfg):
    from benchmark.scene import overlay_pose, rz
    ann = json.loads((ROOT / cfg["base"] / "annotation.json").read_text())
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    sup = {s["name"]: s for s in ann["supports"]}
    out = {}
    for o in ann["objects"]:
        n = o["name"]
        if n in cfg["remove"]:
            continue
        a = assets[o["asset"]]
        if n in cfg["move"]:
            m = cfg["move"][n]
            yaw = math.radians(m.get("yaw_deg", 0.0))
            pos, _ = overlay_pose(a, m, sup)
            b = np.asarray(pos) + rz(yaw) @ np.asarray(a["origin_to_bottom_center"])
            half = np.abs(rz(yaw)) @ (np.asarray(a["size"]) / 2)
            out[n] = np.r_[b[:2] - half[:2], b[2], b[:2] + half[:2], b[2] + a["size"][2]]
        else:
            out[n] = np.asarray(o["aabb"], float)
    for n, m in (cfg.get("add") or {}).items():          # objects the base scene does not have
        a = assets[m["asset"]]
        yaw = math.radians(m.get("yaw_deg", 0.0))
        pos, _ = overlay_pose(a, m, sup)
        b = np.asarray(pos) + rz(yaw) @ np.asarray(a["origin_to_bottom_center"])
        half = np.abs(rz(yaw)) @ (np.asarray(a["size"]) / 2)
        out[n] = np.r_[b[:2] - half[:2], b[2], b[:2] + half[:2], b[2] + a["size"][2]]
    return out


def _contained(box, cont, cname, cfg, assets, ann):
    """An object deliberately put inside an open container (its footprint within the container's)."""
    asset = (cfg.get("add") or {}).get(cname, {}).get("asset") or next(
        (o["asset"] for o in ann["objects"] if o["name"] == cname), None)
    if not asset or not assets[asset].get("container"):
        return False
    return cont[0] <= box[0] and cont[1] <= box[1] and box[3] <= cont[3] and box[4] <= cont[4] and box[2] >= cont[2]


def main():
    from benchmark.scene import episode_config
    path = Path(sys.argv[sys.argv.index("--tasks") + 1]) if "--tasks" in sys.argv else ROOT / "benchmark/tasks.json"
    doc = json.loads(path.read_text())
    tasks = doc["tasks"]
    seeds = doc.get("eval_seeds") or [0]
    bad = 0
    seen = set()
    for t in tasks:
        for v in t["variants"]:
          for seed in (seeds if t.get("kind") != "probe" else [0]):
            cfg = episode_config(t, seed, v)
            if cfg["config_hash"] in seen:
                continue
            seen.add(cfg["config_hash"])
            ann = json.loads((ROOT / cfg["base"] / "annotation.json").read_text())
            sup = {x["name"]: x for x in ann["supports"]}
            for n, m in {**cfg["move"], **(cfg.get("add") or {})}.items():
                s_ = sup.get(m.get("support"))
                if s_ is not None:
                    x0, y0, x1, y1 = s_["aabb_xy"]
                    if not (x0 <= m["xy"][0] <= x1 and y0 <= m["xy"][1] <= y1):
                        bad += 1
                        print(f"{t['task_id']}/{v}/s{seed}: {n} centre {m['xy']} is off {m['support']}")
            cfg["remove"] = [r for r in cfg["remove"] if r not in cfg["distractors_removed"]]   # worst case: all present
            B = boxes(cfg)
            assets = json.loads((ROOT / "annotations/assets.json").read_text())
            for n in [*cfg["move"], *(cfg.get("add") or {})]:
                if n not in B:
                    continue
                for o, b in B.items():
                    if o == n or _contained(B[n], b, o, cfg, assets, ann) or _contained(b, B[n], n, cfg, assets, ann):
                        continue
                    a = B[n]
                    inter = [min(a[3], b[3]) - max(a[0], b[0]), min(a[4], b[4]) - max(a[1], b[1]),
                             min(a[5], b[5]) - max(a[2], b[2])]
                    if all(x > 0.002 for x in inter):
                        bad += 1
                        print(f"{t['task_id']}/{v}/s{seed}: {n} intersects {o} by {np.round(inter, 3).tolist()}")
    print("layout conflicts:", bad)


if __name__ == "__main__":
    main()
