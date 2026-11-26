"""How different the seeds of each v6 design look (user 11-25: episodes must not look alike).

For every design (variant) and every pair of its seeds 10-19: how far the objects moved (largest and mean move of the
objects the layout places) and how far apart the starts are.  A pair is *alike* when no object moved more than
``OBJ_ALIKE_M`` and the starts are within ``START_ALIKE_M`` and ``YAW_ALIKE_DEG``.  A design whose layout has no
cluster that can move (every seed the same object poses) is *frozen*.

    python benchmark/v6/layout_similarity.py [--json benchmark/v6/LAYOUT_SIMILARITY.json]
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmark.scene import episode_config  # noqa: E402

TASKS = ROOT / "benchmark/v6/tasks.json"
SEEDS = range(10, 20)
OBJ_ALIKE_M = 0.10
START_ALIKE_M = 1.0
YAW_ALIKE_DEG = 60.0


def poses(cfg):
    out = {}
    for src in (cfg.get("move") or {}, cfg.get("add") or {}):
        for n, p in src.items():
            if isinstance(p, dict) and p.get("xy"):
                out[n] = (float(p["xy"][0]), float(p["xy"][1]))
    return out


def start_of(cfg):
    s = cfg.get("start") or {}
    if isinstance(s, dict):
        xy = s.get("xy") or s.get("pos") or [s.get("x", 0), s.get("y", 0)]
        return float(xy[0]), float(xy[1]), float(s.get("yaw_deg", s.get("yaw", 0.0)))
    return float(s[0]), float(s[1]), float(s[2]) if len(s) > 2 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    tasks = json.loads(TASKS.read_text())["tasks"]
    rows = []
    for t in tasks:
        for v, spec in t["variants"].items():
            if not spec.get("layout"):
                continue
            cfgs = {s: episode_config(t, s, v) for s in SEEDS}
            P = {s: poses(c) for s, c in cfgs.items()}
            S = {s: start_of(c) for s, c in cfgs.items()}
            alike, moved_any = [], False
            for s1, s2 in itertools.combinations(SEEDS, 2):
                common = set(P[s1]) & set(P[s2])
                d = [math.dist(P[s1][n], P[s2][n]) for n in common]
                dmax = max(d) if d else 0.0
                moved_any |= dmax > 0.005
                ds = math.dist(S[s1][:2], S[s2][:2])
                dyaw = abs((S[s1][2] - S[s2][2] + 180) % 360 - 180)
                if dmax < OBJ_ALIKE_M and ds < START_ALIKE_M and dyaw < YAW_ALIKE_DEG:
                    alike.append([s1, s2, round(dmax, 3), round(ds, 2), round(dyaw)])
            movable = len((spec["layout"] or {}).get("clusters", []))
            rows.append({"task": t["task_id"], "variant": v, "clusters": movable, "objects_move": moved_any,
                         "alike_pairs": alike})
    frozen = [r for r in rows if not r["objects_move"]]
    alike = [r for r in rows if r["alike_pairs"]]
    print(f"{len(rows)} designs; objects never move across seeds: {len(frozen)}; designs with alike seed pairs: "
          f"{len(alike)} ({sum(len(r['alike_pairs']) for r in alike)} pairs)")
    for r in frozen:
        print(f"  FROZEN {r['task'][:3]} {r['variant']} (clusters {r['clusters']})")
    for r in alike:
        print(f"  ALIKE  {r['task'][:3]} {r['variant']}: {r['alike_pairs'][:4]}")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1) + "\n")


if __name__ == "__main__":
    main()
