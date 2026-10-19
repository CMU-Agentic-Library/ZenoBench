"""Static check of every task variant's overlay: moved objects must sit on
their support and must not intersect another object (no simulator).

    python benchmark/check_layouts.py
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
    return out


def main():
    from benchmark.scene import episode_config
    tasks = json.loads((ROOT / "benchmark/tasks.json").read_text())["tasks"]
    bad = 0
    for t in tasks:
        for v in t["variants"]:
            cfg = episode_config(t, 0, v)
            cfg["remove"] = [r for r in cfg["remove"] if r not in cfg["distractors_removed"]]   # worst case: all present
            B = boxes(cfg)
            for n in cfg["move"]:
                if n not in B:
                    continue
                for o, b in B.items():
                    if o == n:
                        continue
                    a = B[n]
                    inter = [min(a[3], b[3]) - max(a[0], b[0]), min(a[4], b[4]) - max(a[1], b[1]),
                             min(a[5], b[5]) - max(a[2], b[2])]
                    if all(x > 0.002 for x in inter):
                        bad += 1
                        print(f"{t['task_id']}/{v}: {n} intersects {o} by {np.round(inter, 3).tolist()}")
    print("layout conflicts:", bad)


if __name__ == "__main__":
    main()
