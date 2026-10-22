"""Route acceptance per condition (benchmark v3), from scripted runs only.

    python benchmark/conditions.py --runs benchmark/runs/v3_smoke benchmark/runs/v3_routes   # -> v3/RESULTS.md, v3/conditions.json

A run counts as evidence for (task, variant, seed) only if the configuration
hash it recorded equals the hash the current task file generates for that
(task, variant, seed); older runs (v2, or a layout that has changed since) are
listed as not counted.  Later run directories supersede earlier ones for the
same task / route / variant / seed.

Per declared route (nominal / explore / fallback / alternative; diagnostic and
oracle routes apart) the outcome of each seed is: pass (the chain ran to its
end, every expected failure really failed, GT goal holds, nothing dropped),
route_violation (an expected failure did not happen; the run went on and its goal result is
kept, but it is no evidence for the condition), fail, incomplete.

Condition status, from its best route over the evaluation seeds:
  stable       one route passed on every evaluation seed (10 of 10)
  preliminary  every run of one route passed, fewer than 10 seeds run
  unstable     a route passed on some seeds and failed on others
  failing      runs exist, none passed
  unverified   no counted run
Scripted routes are feasibility evidence, not planner results.
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
from episode.catalog import load_catalog  # noqa: E402
from episode.profile import run_profile_current  # noqa: E402

GROUNDING = {"NOT_OBSERVED", "NOT_IN_VIEW", "NOT_FOUND"}
PRECONDITION = {"PRECONDITION_FAILED", "NO_PATH"}


def failure_class(code):
    if code in GROUNDING:
        return "observation"
    if code in PRECONDITION:
        return "precondition"
    return "execution"


def outcome(r):
    if r.get("incomplete") or r.get("crash"):
        return "incomplete"
    if r.get("route_violation"):
        return "route_violation"
    if r.get("stopped_at") is not None:
        return "fail"
    return "pass" if r.get("task_success") else "fail"


def load(roots):
    by = {}
    for root in roots:
        for f in sorted(Path(root).glob("*/*/result.json")):
            r = json.loads(f.read_text())
            if r.get("planner") != "scripted":
                continue
            cfg = json.loads((f.parent / "config.json").read_text()) if (f.parent / "config.json").exists() else {}
            code = cfg.get("code", {})
            r["_dir"] = str(f.parent.relative_to(ROOT)) if f.parent.is_relative_to(ROOT) else str(f.parent)
            r["_code"] = f"{code.get('commit', '?')[:7]}+{code.get('diff_sha1', '?')[:7]}"
            r["_hash"] = cfg.get("config_hash") or (cfg.get("scene") or {}).get("config_hash")
            r["_profile_ok"] = run_profile_current(cfg)
            by[(r["task_id"], r.get("route"), r.get("variant"), r.get("seed"))] = r
    return list(by.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--tasks", default=str(ROOT / "benchmark/v3/tasks.json"))
    ap.add_argument("--md", default=str(ROOT / "benchmark/v3/RESULTS.md"))
    ap.add_argument("--json", default=str(ROOT / "benchmark/v3/conditions.json"))
    a = ap.parse_args()
    doc = json.loads(Path(a.tasks).read_text())
    tasks = {k: t for k, t in load_catalog(a.tasks).items() if t.get("kind") != "probe"}
    seeds = doc.get("eval_seeds") or list(range(10, 20))
    expect = {}
    for tid, t in tasks.items():
        for v in t["variants"]:
            for s in seeds:
                expect[(tid, v, s)] = episode_config(t, s, v)["config_hash"]
    counted, stale, diag = defaultdict(list), [], defaultdict(list)
    for r in load(a.runs):
        tid, route, v, s = r["task_id"], r.get("route"), r.get("variant"), r.get("seed")
        t = tasks.get(tid)
        rt = (t or {}).get("routes", {}).get(route)
        if t is None or rt is None or v not in rt.get("variants", []) or r["_hash"] is None \
                or expect.get((tid, v, s)) != r["_hash"] or not r["_profile_ok"]:
            stale.append(r["_dir"])
            continue
        fail_steps = [c for c in r.get("calls", []) if c.get("expect") == "fail"]
        row = {"seed": s, "outcome": outcome(r), "dir": r["_dir"], "code": r["_code"], "config_hash": r["_hash"],
               "expected_failures": [{"call": c["feedback"]["action"], "failed": not c["feedback"]["success"],
                                      "class": failure_class(c["feedback"].get("error_code")),
                                      "error": str(c["feedback"].get("error"))[:160]} for c in fail_steps],
               "first_unexpected_failure": next((f"{c['feedback']['action']}: {c['feedback'].get('error')}"[:200]
                                                 for c in r.get("calls", []) if c.get("expect") != "fail"
                                                 and not c["feedback"]["success"]), ""),
               "dropped": r.get("dropped", [])}
        (diag if rt["kind"] in ("diagnostic", "negative") else counted)[(tid, v, route)].append(row)
    conds = []
    for tid, t in sorted(tasks.items()):
        for v, var in sorted(t["variants"].items()):
            routes = [n for n, r in t["routes"].items() if v in r["variants"] and r["kind"] not in ("diagnostic", "negative")
                      and not n.startswith("oracle")]
            per = []
            for n in routes:
                lst = sorted(counted.get((tid, v, n), []), key=lambda x: x["seed"])
                ok = sum(x["outcome"] == "pass" for x in lst)
                st = ("unverified" if not lst else "stable" if ok == len(lst) == len(seeds) else
                      "preliminary" if ok == len(lst) else "failing" if ok == 0 else "unstable")
                per.append({"route": n, "kind": t["routes"][n]["kind"], "runs": len(lst), "passed": ok, "status": st,
                            "seeds": lst})
            rank = ["stable", "preliminary", "unstable", "failing", "unverified"]
            best = min(per, key=lambda p: (rank.index(p["status"]), -p["passed"])) if per else None
            conds.append({"task": tid, "variant": v, "difficulty": difficulty_of(var), "since": var.get("since"),
                          "conditions": var.get("conditions", []), "condition_types": var.get("condition_types", []),
                          "decisions": var.get("decisions", []), "note": var.get("note", ""),
                          "status": best["status"] if best else ("diagnostic" if difficulty_of(var) == "diagnostic"
                                                                 else "no_route"),
                          "best_route": best["route"] if best else None, "routes": per,
                          "diagnostic_routes": [{"route": n, "seeds": sorted(x, key=lambda y: y["seed"])}
                                                for (tt, vv, n), x in sorted(diag.items()) if tt == tid and vv == v]})
    graded = [c for c in conds if c["difficulty"] in ("easy", "medium", "hard")]
    ep_run = [x for c in graded for p in c["routes"] for x in p["seeds"]]
    st_n = Counter(c["status"] for c in graded)
    summary = {"benchmark_version": doc.get("benchmark_version"), "tasks": len(tasks), "conditions": len(graded),
               "seeds_per_condition": len(seeds),
               "planned_route_episodes": sum(len(seeds) * len(c["routes"]) for c in graded),
               "episodes_run": len(ep_run), "episodes_passed": sum(x["outcome"] == "pass" for x in ep_run),
               "condition_status": dict(st_n), "not_counted_runs": len(stale)}
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps({"summary": summary, "conditions": conds, "not_counted": stale}, indent=1))
    rel = lambda p: str(Path(p).resolve().relative_to(ROOT)) if Path(p).resolve().is_relative_to(ROOT) else p
    md = [f"# ZenoBench {doc.get('benchmark_version', '')} route acceptance", "",
          f"Generated by `python benchmark/conditions.py --runs {' '.join(rel(x) for x in a.runs)}`. Scripted routes "
          "are feasibility evidence (failure really happens -> explicit recovery or alternative -> full task "
          "success), not planner results. A run counts only if its configuration hash equals the current one.", "",
          "## Counts", "", "| Quantity | Value |", "|---|---|",
          f"| Tasks | {summary['tasks']} |", f"| Graded conditions | {summary['conditions']} |",
          f"| Seeds per condition | {len(seeds)} ({seeds[0]}-{seeds[-1]}) |",
          f"| Planned route episodes (routes x seeds) | {summary['planned_route_episodes']} |",
          f"| Route episodes run (counted) | {summary['episodes_run']} |",
          f"| Route episodes physically passed | {summary['episodes_passed']} |",
          "| Condition status | " + ", ".join(f"{k} {n}" for k, n in sorted(st_n.items())) + " |",
          f"| Runs not counted (other configuration / route) | {len(stale)} |", "",
          "## Conditions", "",
          "| Task | Variant | Tier | Types | Status | Best route | Passed / run | Expected failure (class) | Code |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in conds:
        b = next((p for p in c["routes"] if p["route"] == c["best_route"]), None)
        ef = Counter(f"{e['call'].split('(')[0]} {e['class']}" + ("" if e["failed"] else " (did not fail)")
                     for x in (b["seeds"] if b else []) for e in x["expected_failures"])
        codes = sorted({x["code"] for x in (b["seeds"] if b else [])})
        md.append(f"| {c['task']} | `{c['variant']}` | {c['difficulty']} | {', '.join(c['condition_types']) or 'nominal'} | "
                  f"**{c['status']}** | {c['best_route'] or '-'} | {b['passed'] if b else 0}/{b['runs'] if b else 0} | "
                  f"{'; '.join(f'{k} x{n}' for k, n in ef.items()) or '-'} | {', '.join(codes) or '-'} |")
    md += ["", "## Episodes", "", "| Task | Variant | Route | Seed | Outcome | First unexpected failure | Dropped | Dir |",
           "|---|---|---|---|---|---|---|---|"]
    for c in conds:
        for p in c["routes"]:
            for x in p["seeds"]:
                md.append(f"| {c['task']} | {c['variant']} | {p['route']} | {x['seed']} | {x['outcome']} | "
                          f"{x['first_unexpected_failure'][:120]} | {', '.join(x['dropped'])} | `{x['dir']}` |")
        for d in c["diagnostic_routes"]:
            for x in d["seeds"]:
                md.append(f"| {c['task']} | {c['variant']} | {d['route']} (diagnostic) | {x['seed']} | {x['outcome']} | "
                          f"{x['first_unexpected_failure'][:120]} | {', '.join(x['dropped'])} | `{x['dir']}` |")
    Path(a.md).write_text("\n".join(md) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
