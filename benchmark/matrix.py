"""The v3 evaluation matrix, enumerated explicitly (no simulator).

    python benchmark/matrix.py                      # benchmark/v3/tasks.json -> v3/matrix.json, v3/MATRIX.md, v3/batches/
    python benchmark/matrix.py --tasks X.json --out DIR

Every condition is one variant_id; the matrix is task x variant x seed x planner
over the fixed evaluation seeds (10-19), and every planner gets the identical
episode configuration of (task, variant, seed).  Nothing is sampled: the
``--difficulty`` entry point of run_episode.py stays for single episodes only.

Written:
  matrix.json     every (task, variant, seed): difficulty, conditions, types, decisions, config hash, the
                  generated configuration; per variant the number of distinct configurations
  MATRIX.md       counts and the per-condition episode list
  batches/routes.json   every declared route (not diagnostic / negative) x its variants x seeds: acceptance
  batches/smoke.json    the first seed of each (route, variant): the one-chain check before ten seeds
  batches/eval.json     task x variant x seed x planner (fixed, retry, oracle; + recovery with --policy) for the
                        variants whose route acceptance is stable (--all: every registered variant)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmark.scene import difficulty_of, episode_config  # noqa: E402

PLANNERS = ("fixed", "retry", "oracle")
TIERS = ("easy", "medium", "hard")


def enumerate_matrix(doc):
    seeds = doc.get("eval_seeds") or list(range(10, 20))
    rows = []
    for t in doc["tasks"]:
        if t.get("kind") == "probe":
            continue
        for v in sorted(t["variants"]):
            var = t["variants"][v]
            tier = difficulty_of(var)
            for seed in seeds:
                cfg = episode_config(t, seed, v)
                rows.append({"task": t["task_id"], "variant": v, "difficulty": tier, "seed": seed,
                             "conditions": var.get("conditions", []), "condition_types": var.get("condition_types", []),
                             "decisions": var.get("decisions", []), "since": var.get("since"),
                             "oracle_route": t["oracle"].get(v), "config_hash": cfg["config_hash"],
                             "vary_applied": cfg.get("vary_applied", {}),
                             "distractors_removed": cfg["distractors_removed"], "config": cfg})
    return seeds, rows


def route_jobs(doc, seeds):
    out = []
    for t in doc["tasks"]:
        if t.get("kind") == "probe":
            continue
        for rname, r in t["routes"].items():
            if r["kind"] in ("negative", "diagnostic") or rname.startswith("oracle"):
                continue
            for v in r["variants"]:
                for seed in seeds:
                    out.append({"task": t["task_id"], "seed": seed, "route": rname, "variant": v})
    return out


def eval_jobs(doc, seeds, accepted, policy=None):
    out = []
    for t in doc["tasks"]:
        if t.get("kind") == "probe":
            continue
        for v in sorted(t["variants"]):
            if difficulty_of(t["variants"][v]) not in TIERS or (accepted is not None and (t["task_id"], v) not in accepted):
                continue
            for seed in seeds:
                for p in PLANNERS + (("recovery",) if policy else ()):
                    j = {"task": t["task_id"], "seed": seed, "planner": p, "variant": v}
                    if p == "recovery":
                        j["policy"] = policy
                    out.append(j)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", default=str(ROOT / "benchmark/v3/tasks.json"))
    ap.add_argument("--out", default=str(ROOT / "benchmark/v3"))
    ap.add_argument("--conditions", default=None, help="conditions.json of benchmark/conditions.py (route status)")
    ap.add_argument("--all", action="store_true", help="eval batch over every registered variant")
    ap.add_argument("--policy", help="module:Class of a recovery planner for the eval batch")
    a = ap.parse_args()
    doc = json.loads(Path(a.tasks).read_text())
    out = Path(a.out)
    (out / "batches").mkdir(parents=True, exist_ok=True)
    seeds, rows = enumerate_matrix(doc)
    status = {}
    cpath = Path(a.conditions) if a.conditions else out / "conditions.json"
    if cpath.exists():
        status = {(c["task"], c["variant"]): c["status"] for c in json.loads(cpath.read_text())["conditions"]}
    accepted = None if a.all else {k for k, s in status.items() if s == "stable"}
    routes = route_jobs(doc, seeds)
    smoke = [j for j in routes if j["seed"] == seeds[0]]
    ev = eval_jobs(doc, seeds, accepted, a.policy)
    for name, jobs in (("routes", routes), ("smoke", smoke), ("eval", ev)):
        (out / "batches" / f"{name}.json").write_text(json.dumps(jobs, indent=1))

    by_var = defaultdict(list)
    for r in rows:
        by_var[(r["task"], r["variant"])].append(r)
    variants = []
    for (tid, v), lst in sorted(by_var.items()):
        hashes = Counter(r["config_hash"] for r in lst)
        variants.append({"task": tid, "variant": v, "difficulty": lst[0]["difficulty"], "since": lst[0]["since"],
                         "conditions": lst[0]["conditions"], "condition_types": lst[0]["condition_types"],
                         "decisions": lst[0]["decisions"], "oracle_route": lst[0]["oracle_route"],
                         "seeds": [r["seed"] for r in lst], "distinct_configs": len(hashes),
                         "repeated_configs": {h: n for h, n in hashes.items() if n > 1},
                         "status": status.get((tid, v), "unverified")})
    all_hash = Counter(r["config_hash"] for r in rows)
    tasks = sorted({r["task"] for r in rows})
    tier_n = Counter(v["difficulty"] for v in variants)
    graded = [v for v in variants if v["difficulty"] in TIERS]
    n_eval_eps = len(graded) * len(seeds)
    summary = {"benchmark_version": doc.get("benchmark_version"), "tasks": len(tasks), "conditions": len(variants),
               "graded_conditions": len(graded), "conditions_by_tier": dict(tier_n), "seeds": seeds,
               "episodes_per_planner": n_eval_eps, "planners": list(PLANNERS),
               "episode_configs": len(rows), "distinct_configs": len(all_hash),
               # one configuration shared by two conditions of one task would mean the conditions do not differ
               # (the same scene under two tasks is expected: the tasks share one base scene)
               "same_task_cross_variant_collisions": sum(
                   1 for h in all_hash if any(len({r["variant"] for r in rows if r["config_hash"] == h and r["task"] == t}) > 1
                                              for t in tasks)),
               "route_jobs": len(routes), "smoke_jobs": len(smoke), "eval_jobs": len(ev),
               "eval_scope": "all registered variants" if a.all else "variants with stable route acceptance"}
    (out / "matrix.json").write_text(json.dumps({"summary": summary, "variants": variants,
                                                 "episodes": [{k: v for k, v in r.items()} for r in rows]}, indent=1))

    md = [f"# ZenoBench {doc.get('benchmark_version', '')} evaluation matrix", "",
          f"Generated by `python benchmark/matrix.py` from `{Path(a.tasks).resolve().relative_to(ROOT) if Path(a.tasks).resolve().is_relative_to(ROOT) else a.tasks}` "
          "(no simulator). A generated configuration is not a physical result: route status comes from runs "
          "(`benchmark/conditions.py`).", "",
          "## Counts", "",
          "| Quantity | Value |", "|---|---|",
          f"| Tasks | {len(tasks)} |",
          f"| Conditions (variants) | {len(variants)} ({', '.join(f'{k} {n}' for k, n in sorted(tier_n.items()))}) |",
          f"| Graded conditions (easy/medium/hard) | {len(graded)} |",
          f"| Seeds per condition | {len(seeds)} ({seeds[0]}-{seeds[-1]}) |",
          f"| Episodes per planner (graded conditions x seeds) | {n_eval_eps} |",
          f"| Distinct configurations among them | {len({r['config_hash'] for r in rows if r['difficulty'] in TIERS})} |",
          f"| Planners in the shared matrix | {', '.join(PLANNERS)} (+ recovery) |",
          f"| Route acceptance jobs (declared routes x variants x seeds) | {len(routes)} |",
          f"| Eval jobs written ({summary['eval_scope']}) | {len(ev)} |", "",
          "Repeats: a seed changes the distractor subset and, where a variant declares a safe range (`vary`), a "
          "small shift of an object group or of the robot start. Two seeds with the same configuration hash are "
          "physical repeats of one scene, not two scenes.", "",
          "## Conditions", "",
          "| Task | Variant | Tier | Since | Conditions | Types | Decision | Oracle route | Distinct configs / seeds | Status |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for v in variants:
        md.append(f"| {v['task']} | `{v['variant']}` | {v['difficulty']} | {v['since']} | {', '.join(v['conditions']) or '-'} | "
                  f"{', '.join(v['condition_types']) or 'nominal'} | {', '.join(v['decisions'])} | {v['oracle_route']} | "
                  f"{v['distinct_configs']} / {len(v['seeds'])} | {v['status']} |")
    md += ["", "## Episodes (task, variant, seed -> configuration hash)", "",
           "| Task | Variant | " + " | ".join(f"s{s}" for s in seeds) + " |", "|---|---|" + "---|" * len(seeds)]
    for (tid, v), lst in sorted(by_var.items()):
        md.append(f"| {tid} | {v} | " + " | ".join(f"`{r['config_hash'][:6]}`" for r in lst) + " |")
    na = [(t["task_id"], x) for t in doc["tasks"] for x in t.get("not_adopted", [])]
    if na:
        md += ["", "## Considered, not adopted", "", "| Task | Condition | Reason |", "|---|---|---|"]
        md += [f"| {tid} | {x['condition']} | {x['reason']} |" for tid, x in na]
    (out / "MATRIX.md").write_text("\n".join(md) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
