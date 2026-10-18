"""Summarise benchmark runs: pass/fail/incomplete per route, fallback and
alternative evidence, and the SkillNode coverage table.

    python benchmark/report.py --runs benchmark/runs/final benchmark/runs/retest   # -> RESULTS.md, coverage.json

With several run directories, an episode of a later directory replaces the one
with the same task / route / planner / variant / seed of an earlier directory
(a retest after a code change supersedes the old evidence).  README.md only
gets a one-paragraph summary between its results markers.

A skill counts as covered by a task only through calls in that task's runs
that passed every GT pre/postcondition (nested calls inside multi-object
skills count); history outside these runs never counts.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_runs(roots):
    by_key = {}
    for root in roots:
        for f in sorted(Path(root).glob("*/*/result.json")):
            r = json.loads(f.read_text())
            if r.get("planner") == "recovery":
                continue        # closed-loop runs are planner evaluations (evaluate.py), not route evidence
            r["_dir"] = str(f.parent.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f.parent)
            cfg = f.parent / "config.json"
            code = json.loads(cfg.read_text()).get("code", {}) if cfg.exists() else {}
            r["_code"] = f"{code.get('commit', '?')[:7]}+{code.get('diff_sha1', '?')[:7]}"
            key = (r["task_id"], r.get("route"), r.get("planner"), r.get("variant"), r.get("seed"))
            by_key[key] = r
    return list(by_key.values())


def verbs():
    cat = json.loads((ROOT / "contract_library/skill_contracts.json").read_text())
    return [(c["skill_id"], c["verb"]) for c in sorted(cat["contracts"], key=lambda c: c["skill_id"])]


def outcome(r):
    if r.get("incomplete") or r.get("crash"):
        return "incomplete"
    if r.get("route_violation"):
        return "route_violation"
    if r.get("planner") == "scripted" and r.get("stopped_at") is not None:
        return "fail"                    # the declared chain did not run to its end
    return "pass" if r.get("task_success") else "fail"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", default=[str(ROOT / "benchmark/runs/final")])
    ap.add_argument("--tasks", default=str(ROOT / "benchmark/tasks.json"))
    ap.add_argument("--md", default=str(ROOT / "benchmark/RESULTS.md"))
    ap.add_argument("--json", default=str(ROOT / "benchmark/coverage.json"))
    a = ap.parse_args()
    tasks = {t["task_id"]: t for t in json.loads(Path(a.tasks).read_text())["tasks"]}
    runs = load_runs(a.runs)
    a.runs = [str(Path(x).resolve().relative_to(ROOT)) if Path(x).resolve().is_relative_to(ROOT) else x for x in a.runs]
    rows, routes = [], defaultdict(list)
    cover = defaultdict(lambda: {"tasks": set(), "calls": 0, "ok": 0, "paths": set(), "evidence": []})
    stale, diag = [], defaultdict(list)
    for r in runs:
        tid = r["task_id"]
        if r.get("planner") == "scripted":
            rt = tasks.get(tid, {}).get("routes", {}).get(r.get("route"))
            if rt is not None and rt.get("kind") == "diagnostic":
                diag[(tid, r.get("route"))].append(outcome(r))
                continue
            if rt is None or r.get("variant") not in rt.get("variants", []):
                stale.append(r["_dir"])          # a route that was redesigned
                continue
        key = (tid, r.get("route") or r.get("planner"), r.get("planner"))
        o = outcome(r)
        routes[key].append((r["seed"], r["variant"], o, r["_dir"], r["_code"]))
        fail = next((c for c in r.get("calls", []) if c.get("expect") == "fail"), None)
        rec = [c for c in r.get("calls", []) if c.get("role") in ("recovery", "alternative", "retry_after_recovery")]
        rows.append({"task": tid, "seed": r["seed"], "variant": r["variant"], "planner": r.get("planner"),
                     "route": r.get("route"), "outcome": o, "calls": len(r.get("calls", [])),
                     "failed_calls": r.get("skill_failures", []),
                     "evidence_failure": (fail["feedback"]["action"] + ": " + str(fail["feedback"]["error"])) if fail else "",
                     "recovery": [c["feedback"]["action"] + (" OK" if c["feedback"]["success"] else " FAIL") for c in rec],
                     "goal": [g["atom"] + (" OK" if g["holds"] else " FALSE") for g in r.get("goal", {}).get("all", [])],
                     "dropped": r.get("dropped", []), "wall_s": r.get("wall_s"), "dir": r["_dir"],
                     "crash": r.get("crash", "")})
        if r.get("planner") == "oracle":
            continue
        for c in r.get("gate_calls", []):
            v = c["verb"]
            cover[v]["calls"] += 1
            if c["success"]:
                cover[v]["ok"] += 1
                cover[v]["tasks"].add(tid)
                if c.get("path"):
                    cover[v]["paths"].add(c["path"])
                if len(cover[v]["evidence"]) < 2:
                    cover[v]["evidence"].append(f"{r['_dir']}")
    table = []
    for sid, v in verbs():
        c = cover.get(v)
        status = "covered" if c and c["ok"] else ("called, failed" if c and c["calls"] else "not covered")
        table.append({"skill_id": sid, "verb": v, "status": status, "tasks": sorted(c["tasks"]) if c else [],
                      "calls": c["calls"] if c else 0, "successful_calls": c["ok"] if c else 0,
                      "paths": sorted(c["paths"]) if c else [], "evidence": c["evidence"] if c else []})
    Path(a.json).write_text(json.dumps({"skills": table, "runs": rows}, indent=1))
    n_cov = sum(t["status"] == "covered" for t in table)
    md = ["# Benchmark results", "",
          f"Generated by `python benchmark/report.py --runs {' '.join(a.runs)}`.", "",
          f"**SkillNode coverage: {n_cov}/{len(table)}** verbs with at least one GT-verified call inside these "
          "benchmark runs (observation-limited interface, nested calls included).", "",
          "## Routes", "",
          "Stability: **stable** = every run passed (at least 2 runs), **flaky** = some passed, **failing** = none "
          "passed, **single** = one run only.  Diagnostic routes (kept to document a physical limit) are listed "
          "after the table and are not acceptance routes.", "",
          "| Task | Route / planner | Stability | Seeds (variant: outcome) | Code |", "|---|---|---|---|---|"]
    stability = {}
    for (tid, route, planner), lst in sorted(routes.items()):
        kind = tasks.get(tid, {}).get("routes", {}).get(route, {}).get("kind", planner)
        n_ok = sum(x[2] == "pass" for x in lst)
        st_ = "single" if len(lst) < 2 else "stable" if n_ok == len(lst) else "failing" if n_ok == 0 else "flaky"
        stability[(tid, route, planner)] = st_
        md.append(f"| {tid} | {route} ({kind}) | {st_} | " + ", ".join(f"s{s} {v}: **{o}**" for s, v, o, _, _ in sorted(lst))
                  + " | " + ", ".join(sorted({x[4] for x in lst})) + " |")
    md += ["", "Diagnostic routes: " + ("; ".join(f"{t} {r}: {', '.join(v)}" for (t, r), v in sorted(diag.items()))
                                        or "none in these runs") + "."]
    codes = defaultdict(int)
    for r in runs:
        codes[r["_code"]] += 1
    md += ["", "Evidence code versions (commit + hash of the tracked diff): " +
           ", ".join(f"`{c}` ({n} episodes)" for c, n in sorted(codes.items())) + ".  Run directories: " +
           ", ".join(f"`{Path(x).name}`" for x in a.runs) + " (later ones supersede earlier ones)."]
    md += ["", "## Episodes", "", "| Task | Seed | Variant | Planner | Route | Outcome | Real failure | Recovery / alternative calls | Dropped | Dir |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda x: (x["task"], str(x["route"]), x["seed"])):
        md.append(f"| {r['task']} | {r['seed']} | {r['variant']} | {r['planner']} | {r['route']} | {r['outcome']} | "
                  f"{r['evidence_failure'][:110]} | {'; '.join(r['recovery'])[:140]} | {', '.join(r['dropped'])} | `{r['dir']}` |")
    md += ["", "## SkillNode coverage", "", "| SkillNode | Verb | Status | Tasks | Calls (ok/all) | Paths |", "|---|---|---|---|---|---|"]
    for t in table:
        md.append(f"| `{t['skill_id']}` | {t['verb']} | {t['status']} | {', '.join(t['tasks'])} | "
                  f"{t['successful_calls']}/{t['calls']} | {', '.join(t['paths'])} |")
    Path(a.md).write_text("\n".join(md) + "\n")
    # README: one-paragraph summary only (the tables live in RESULTS.md)
    readme = ROOT / "benchmark/README.md"
    if readme.exists():
        task_routes = [(k, v) for k, v in routes.items() if k[2] == "scripted" and k[0].startswith("T")]
        ep = [x for _, v in task_routes for x in v]
        probe = [x for k, v in routes.items() if k[2] == "scripted" and k[0].startswith("P") for x in v]
        cnt = defaultdict(int)
        for k, _ in task_routes:
            cnt[stability[k]] += 1
        base = {p: [x for k, v in routes.items() if k[2] == p for x in v] for p in ("fixed", "retry", "oracle")}
        lines = [f"Declared task routes: **{sum(x[2] == 'pass' for x in ep)}/{len(ep)}** episodes pass "
                 f"({len(task_routes)} routes: " + ", ".join(f"{n} {k}" for k, n in sorted(cnt.items())) + "); "
                 f"probes {sum(x[2] == 'pass' for x in probe)}/{len(probe)}; baselines " +
                 ", ".join(f"{p} {sum(x[2] == 'pass' for x in v)}/{len(v)}" for p, v in base.items() if v) +
                 f"; SkillNode coverage **{n_cov}/{len(table)}** "
                 f"({sum(t['status'] == 'called, failed' for t in table)} called but failed, "
                 f"{sum(t['status'] == 'not covered' for t in table)} never called).  Per route and seed: "
                 "[RESULTS.md](RESULTS.md); per skill: [coverage.json](coverage.json)."]
        txt = readme.read_text()
        a0, a1 = "<!-- results:start -->", "<!-- results:end -->"
        if a0 in txt and a1 in txt:
            txt = txt[:txt.index(a0) + len(a0)] + "\n" + "\n".join(lines) + "\n" + txt[txt.index(a1):]
            readme.write_text(txt)
    print(f"{len(rows)} episodes ({len(stale)} of superseded routes skipped), coverage {n_cov}/{len(table)} -> {a.md}")


if __name__ == "__main__":
    main()
