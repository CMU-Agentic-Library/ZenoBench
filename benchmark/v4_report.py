"""Validation report of the v4 Hard variants (scripted oracle and negative routes).

    python benchmark/v4_report.py --runs benchmark/runs/v4_accept [more dirs] --md benchmark/v3/V4_HARD_VALIDATION.md

Only runs whose configuration hash matches the current catalog count (a later dir supersedes an earlier one for
the same task / variant / route / seed).  Every run gets one outcome class, kept apart as the report asks:

* ``passed``: the chain ran to its end, expected failures failed, the goal holds, nothing dropped;
* ``planning_failure``: every call the route expected to work did work, yet the goal is false: the plan does not
  satisfy the instruction (what a negative route is meant to show);
* ``physical_failure``: a call the route expected to work failed in execution (POLICY_FAILED, NO_PATH, a slip,
  an object dropped) or the goal failed only because something fell;
* ``refused``: a call was refused by a precondition / observation gate (NOT_OBSERVED, NOT_IN_VIEW,
  PRECONDITION_FAILED): a route-authoring or perception issue, neither physics nor the plan's logic;
* ``condition_not_met``: a step expected to fail succeeded (the Hard condition did not hold);
* ``system_error``: crash or incomplete run.

Scripted routes show that one strategy is executable in this configuration; they are not planner results.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REFUSALS = {"NOT_OBSERVED", "NOT_IN_VIEW", "PRECONDITION_FAILED", "INPUT_UNKNOWN", "UNKNOWN_CONTRACT", "BAD_CALL"}


def classify(r: dict) -> tuple[str, str]:
    if r.get("crash") or r.get("incomplete"):
        return "system_error", r.get("crash", "incomplete")
    if r.get("route_violations"):
        return "condition_not_met", r["route_violations"][0]
    bad = next((c for c in r["calls"] if c.get("expect", "ok") == "ok" and not c["feedback"]["success"]), None)
    if bad is not None:
        fb = bad["feedback"]
        cls = "refused" if fb.get("error_code") in REFUSALS else "physical_failure"
        return cls, f"{fb['action']}: {fb.get('error_code')}: {(fb.get('error') or '')[:140]}"
    if r.get("task_success"):
        return "passed", ""
    false = [g["atom"] for g in r.get("goal", {}).get("all", []) if not g["holds"]]
    groups = r.get("goal", {}).get("any", [])
    if groups and not any(all(g["holds"] for g in grp) for grp in groups):
        false.append("no alternative of the goal holds")
    if r.get("dropped") and not false:
        return "physical_failure", f"dropped {r['dropped']}"
    return "planning_failure", "; ".join(false)[:200]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--tasks", default=str(ROOT / "benchmark/v3/tasks.json"))
    ap.add_argument("--md", default=str(ROOT / "benchmark/v3/V4_HARD_VALIDATION.md"))
    ap.add_argument("--json", default=str(ROOT / "benchmark/v3/v4_hard_validation.json"))
    a = ap.parse_args()
    from benchmark.scene import episode_config
    from episode.catalog import difficulty_of
    doc = json.loads(Path(a.tasks).read_text())
    tasks = {t["task_id"]: t for t in doc["tasks"] if t.get("kind") != "probe"}
    hard = {(tid, v) for tid, t in tasks.items() for v, var in t["variants"].items()
            if difficulty_of(var) == "hard" and var.get("since") == "v4"}
    runs = {}
    stale = 0
    for d in a.runs:
        for f in sorted(Path(d).glob("*/*/result.json")):
            r = json.loads(f.read_text())
            key = (r["task_id"], r.get("variant"))
            if key not in hard or r.get("planner") != "scripted":
                continue
            if r.get("config_hash") != episode_config(tasks[key[0]], r["seed"], key[1])["config_hash"]:
                stale += 1
                continue
            r["_dir"] = str(f.parent.relative_to(ROOT) if f.parent.is_relative_to(ROOT) else f.parent)
            runs[(*key, r["route"], r["seed"])] = r                # later dirs supersede earlier ones
    rows = []
    for tid, v in sorted(hard):
        t = tasks[tid]
        var = t["variants"][v]
        for rname, route in t["routes"].items():
            if v not in route["variants"] or route["kind"] == "diagnostic":
                continue
            done = sorted(((s, runs[(tid, v, rname, s)]) for (a_, b_, c_, s) in runs
                           if (a_, b_, c_) == (tid, v, rname)), key=lambda x: x[0])
            for s, r in done:
                cls, why = classify(r)
                rows.append({"task": tid, "variant": v, "route": rname, "kind": route["kind"],
                             "oracle": t["oracle"].get(v) == rname, "seed": s, "class": cls, "detail": why,
                             "dir": r["_dir"], "decisions": var["decisions"], "conditions": var["conditions"]})
            if not done:
                rows.append({"task": tid, "variant": v, "route": rname, "kind": route["kind"],
                             "oracle": t["oracle"].get(v) == rname, "seed": None, "class": "not_run", "detail": "",
                             "dir": "", "decisions": var["decisions"], "conditions": var["conditions"]})
    Path(a.json).write_text(json.dumps({"rows": rows, "stale_runs_ignored": stale}, indent=1))

    def status(tid, v):
        orr = [x for x in rows if x["task"] == tid and x["variant"] == v and x["oracle"] and x["seed"] is not None]
        ok = [x for x in orr if x["class"] == "passed"]
        if not orr:
            return "unverified"
        return f"oracle passed {len(ok)}/{len(orr)} seeds" if ok else "oracle failing"

    md = ["# v4 Hard: scripted oracle validation", "",
          f"Generated by `python benchmark/v4_report.py --runs {' '.join(a.runs)}`. Runs with a configuration hash "
          f"that no longer matches the catalog are ignored ({stale}). Scripted routes show that one strategy is "
          "physically executable in the configuration; they are not planner results. Negative routes document the "
          "plan the Hard is designed to reject: their expected outcome is `planning_failure` (every call works, the "
          "goal is false).", "",
          "| Outcome class | Meaning |", "|---|---|",
          "| passed | chain ran, expected failures failed, goal holds, nothing dropped |",
          "| planning_failure | every expected call worked, the goal is false: the plan does not satisfy the instruction |",
          "| physical_failure | a call expected to work failed in execution (grasp, IK, slip, drop) |",
          "| refused | precondition / observation gate refused a call (route authoring, perception) |",
          "| condition_not_met | a step expected to fail succeeded |",
          "| system_error | crash / incomplete |", "",
          "## Summary", "", "| Task | Variant | Decisions | Status |", "|---|---|---|---|"]
    for tid, v in sorted(hard):
        md.append(f"| {tid} | `{v}` | {', '.join(tasks[tid]['variants'][v]['decisions'])} | {status(tid, v)} |")
    md += ["", "## Runs", "", "| Task | Variant | Route | Kind | Seed | Outcome | Detail | Run |", "|---|---|---|---|---|---|---|---|"]
    for x in rows:
        md.append(f"| {x['task']} | `{x['variant']}` | {x['route']}{' (oracle)' if x['oracle'] else ''} | {x['kind']} | "
                  f"{x['seed'] if x['seed'] is not None else '-'} | {x['class']} | {x['detail'].replace('|', '/')} | "
                  f"{x['dir']} |")
    Path(a.md).write_text("\n".join(md) + "\n")
    print(f"{len(rows)} rows -> {a.md}")


if __name__ == "__main__":
    main()
