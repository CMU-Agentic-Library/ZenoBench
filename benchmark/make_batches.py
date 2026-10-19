"""Write the run lists for the acceptance rounds (benchmark/batches/*.json).

    python benchmark/make_batches.py
    python benchmark/run_episode.py --batch benchmark/batches/accept.json --jobs 2 --out benchmark/runs/accept

accept.json    every declared route of every task on two seeds (two distractor draws)
baselines.json fixed plan / direct retry / GT oracle on one failure variant per task
probes.json    the single-skill probes, one run each
eval.json      planner grid: every task x tier x EVAL_SEEDS for fixed / retry / oracle
               (+ recovery with ``--policy module:Class``); score with benchmark/evaluate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark"))
from scene import difficulty_of  # noqa: E402
OUT = ROOT / "benchmark/batches"
EVAL_SEEDS = (10, 11)          # disjoint from the acceptance (0, 1) and baseline (2, 3) seeds


def main():
    tasks = json.loads((ROOT / "benchmark/tasks.json").read_text())["tasks"]
    policy = sys.argv[sys.argv.index("--policy") + 1] if "--policy" in sys.argv else None
    accept, base, probes, grid = [], [], [], []
    for t in tasks:
        if t.get("kind") == "probe":
            probes.append({"task": t["task_id"], "seed": 0, "route": "nominal", "variant": "default"})
            continue
        for rname, r in t["routes"].items():
            if r["kind"] in ("negative", "diagnostic") or rname.startswith("oracle"):
                continue
            for v in r["variants"]:
                for seed in (0, 1):
                    accept.append({"task": t["task_id"], "seed": seed, "route": rname, "variant": v})
        # one failure / alternative variant per task (the medium tier when there is one)
        hard = [v for v, rn in t["oracle"].items() if rn != t["nominal"]]
        med = [v for v in hard if difficulty_of(t["variants"][v]) == "medium"]
        hard = med[:1] or hard[:1]
        for v in hard:
            base += [{"task": t["task_id"], "seed": 2, "planner": "fixed", "variant": v},
                     {"task": t["task_id"], "seed": 2, "planner": "retry", "variant": v}]
        for v in hard:
            base.append({"task": t["task_id"], "seed": 3, "planner": "oracle", "variant": v})
        tiers = sorted({difficulty_of(v) for v in t["variants"].values()} & {"easy", "medium", "hard"})
        for tier in tiers:
            for seed in EVAL_SEEDS:
                for planner in ("fixed", "retry", "oracle") + (("recovery",) if policy else ()):
                    j = {"task": t["task_id"], "seed": seed, "planner": planner, "difficulty": tier}
                    if planner == "recovery":
                        j["policy"] = policy
                    grid.append(j)
    OUT.mkdir(exist_ok=True)
    for name, jobs in (("accept", accept), ("baselines", base), ("probes", probes), ("eval", grid)):
        (OUT / f"{name}.json").write_text(json.dumps(jobs, indent=1))
        print(name, len(jobs))


if __name__ == "__main__":
    main()
