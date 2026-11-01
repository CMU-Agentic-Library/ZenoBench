"""Design audit of the v6 suite (static evidence plus the v5 physics baseline; nothing simulated here).

    python benchmark/v6/report_v6.py

Writes, in benchmark/v6/:

* DESIGN_AUDIT.md / design_audit.json - scale, the task x family x capability x failure mechanism x tier x
  recovery matrix, failure / recovery diversity per capability, difficulty audit (tier rule, re-tiered v5
  variants, control pairs), seed diversity, duplication, status per family, and the conference-level checklist;
* ROUTES.md        - every formal family's oracle reference route(s);
* SKILL_FIX_LIST.md - skill / physics problems for the skill owner, from the v5 baseline and the v6 routes;
* PHYSICS_TODO.md and batches/physics_v6_new.json, batches/physics_todo.json - what still needs simulation.

Status labels (never merged): PHYSICS_VALIDATED (every manifest episode passed in simulation with the current
configuration hash and route), STATIC_VALIDATED (all static checks and capability checks pass; physics missing
or partial), DESIGN_COMPLETE (specified, static checks not yet passing).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
V6 = ROOT / "benchmark/v6"
TARGET = {"variants": 20, "tasks": 8}
CAP_NAMES = {"DR": "Dependency Replanning", "GD": "Goal Decomposition", "SR": "Strategy Replacement",
             "CL": "Cross-Level Recovery", "PP": "Partial Progress Preservation", "AF": "Alternative / Fallback"}


def short(tid):
    return tid[:3]


# ----------------------------------------------------------------- per-variant descriptors
def mechanisms(v):
    """Failure mechanisms of a variant: kind + persistence / mode (+ event type), constraint-only overlays."""
    from failure_injection.spec import ACTION_KINDS
    out = set()
    for f in v.get("failures", []):
        if f["kind"] in ACTION_KINDS:
            out.add(f"{f['kind']}/{'persistent' + ('-until-moved' if f.get('until_moved') else '') if f.get('persist') else 'transient'}")
        elif f.get("when", "initial") == "dynamic":
            out.add(f"{f['kind']}/dynamic-{(f.get('event') or {}).get('type')}")
        else:
            out.add(f"{f['kind']}/initial")
    if not out and v.get("conditions"):
        out |= {f"condition/{c}" for c in v["conditions"]}
    return sorted(out) or ["none"]


def strategies(aud, task=None, vid=None):
    """Abstract recovery strategies, one per verified capability (from the accepted hypothesis)."""
    out = set()
    v = task["variants"][vid] if task else {}
    steps = task["routes"][task["oracle"][vid]]["steps"] if task else []
    fails = {f["id"]: f for f in v.get("failures", [])}
    for cap, h in aud["evidence"].items():
        if cap == "CL":
            out.add(f"CL:{h['change']}")
        elif cap == "SR":
            n, r = h["nominal"], h["replacement"]
            diff = [k for k in set(n["args"]) | set(r["args"]) if n["args"].get(k) != r["args"].get(k)
                    and k in ("appliance", "hands", "base")]
            out.add(f"SR:{n['skill']}->{r['skill']}" + (f"({','.join(sorted(diff))})" if diff else ""))
        elif cap == "DR":
            sk = next((s["skill"] for s in steps if s.get("expect") != "fail" and h["blocker"] in
                       [x for x in s["args"].values() if isinstance(x, str)] and s["skill"] not in ("navigate", "look", "approach")), "")
            out.add({"open": "DR:open-door", "push": "DR:push-aside", "uncover": "DR:uncover",
                     "clear": "DR:clear-surface"}.get(sk, "DR:relocate-obstacle"))
        elif cap == "GD":
            out.add(f"GD:{h['kind']}")
        elif cap == "PP":
            from benchmark.v6.hypotheses import subjects
            from episode.catalog import resolve_task
            f = fails.get(h["event"], {})
            ev = f.get("event") or {}
            if f.get("kind") in ("grasp", "slip", "placement", "ik"):
                out.add("PP:switch-after-progress")
            elif ev.get("type") == "set_joint":
                out.add("PP:restore-state")
            elif task and ev.get("object") in subjects(resolve_task(task, vid)["goal"]):
                out.add("PP:redo-undone-part")
            else:
                out.add("PP:fetch-moved-resource")
        elif cap == "AF":
            out.add(f"AF:{h['level']}")
    return sorted(out)


def physics_status(doc):
    """(task, family) -> (passed, run, declared) over the manifest episodes, from benchmark/v5/PHYSICS.json
    (only results whose configuration hash and route match the current catalog)."""
    p = ROOT / "benchmark/v5/PHYSICS.json"
    rows = json.loads(p.read_text())["rows"] if p.exists() else []
    from benchmark.scene import episode_config
    from benchmark.v5.validate import route_sha1
    by = {(r["task"], r["variant"], r["seed"]): r for r in rows}
    out = {}
    for t in doc["tasks"]:
        for fam, info in t["v6_families"].items():
            ok = run = 0
            for s, vid in info["seeds"].items():
                r = by.get((t["task_id"], vid, int(s)))
                if not r or r["status"] == "unrun":
                    continue
                if r["hash"] != episode_config(t, int(s), vid)["config_hash"] or \
                        r["route_sha1"] != route_sha1(t["routes"][t["oracle"][vid]]["steps"]):
                    continue
                run += 1
                ok += r["status"] == "passed"
            out[(t["task_id"], fam)] = (ok, run, len(info["seeds"]))
    return out


# ----------------------------------------------------------------- report
def main():
    doc = json.loads((V6 / "tasks.json").read_text())
    static = json.loads((V6 / "STATIC.json").read_text())
    stale_static = static.get("tasks_sha1") != hashlib.sha1((V6 / "tasks.json").read_bytes()).hexdigest()
    phys = physics_status(doc)
    bad_static = {(p["task"], p["family"] if isinstance(p["family"], str) else None) for p in static["problems"]}
    fixes_rerun = {("T11_collect_fruits", "h_action_grasp_and_ik"): "failure-injection fix 019e517 (pinned IK block)"}
    rows = []
    for t in doc["tasks"]:
        for fam, info in t["v6_families"].items():
            auds = [t["v6_audit"][v] for v in info["cases"]]
            v0 = t["variants"][info["cases"][0]]
            mech = sorted({m for v in info["cases"] for m in mechanisms(t["variants"][v])})
            strat = sorted({x for v, a in zip(info["cases"], auds) for x in strategies(a, t, v)})
            ok, run, dec = phys[(t["task_id"], fam)]
            if (t["task_id"], fam) in bad_static:
                status = "DESIGN_COMPLETE"
            elif ok == dec and (t["task_id"], fam) not in fixes_rerun:
                status = "PHYSICS_VALIDATED"
            else:
                status = "STATIC_VALIDATED"
            meta = v0.get("v6") or v0.get("v5") or {}
            rows.append({"task": t["task_id"], "family": fam, "origin": info["origin"], "tier": info["tier"],
                         "v5_tier": info.get("v5_tier"), "retiered": info.get("retiered"),
                         "hard_category": info.get("hard_category") or meta.get("hard_category"),
                         "caps": info["capabilities"], "core": [c for c in info["capabilities"] if c != "AF"],
                         "mechanisms": mech, "strategies": strat, "cases": info["cases"], "factor": info.get("factor"),
                         "control": auds[0]["control"], "challenge": meta.get("challenge") or v0.get("note", ""),
                         "rationale": meta.get("rationale", ""), "physics": f"{ok}/{run} of {dec}", "status": status,
                         "rerun_needed": fixes_rerun.get((t["task_id"], fam)),
                         "retry_solvable": any(a["retry_solvable"] for a in auds)})
    hard = [r for r in rows if r["tier"] == "hard"]
    # duplicates: same task and same (core caps, mechanisms, strategies)
    sig = defaultdict(list)
    for r in hard:
        sig[(r["task"], tuple(r["core"]), tuple(r["mechanisms"]), tuple(r["strategies"]))].append(r["family"])
    dups = {f"{k[0][:3]}: {', '.join(k[1])} | {'; '.join(k[2])}": v for k, v in sig.items() if len(v) > 1}
    for k, fams in sig.items():
        if len(fams) > 1:
            for r in hard:
                if r["task"] == k[0] and r["family"] in fams[1:]:
                    r["same_design_as"] = fams[0]
    # coverage
    cov = {}
    for cap in ("DR", "GD", "SR", "CL", "PP", "AF"):
        rs = [r for r in hard if cap in r["caps"]]
        cov[cap] = {"variants": len(rs), "designs": sum(1 for r in rs if not r.get("same_design_as")),
                    "tasks": len({r["task"] for r in rs}),
                    "mechanisms": sorted({m for r in rs for m in r["mechanisms"]}),
                    "strategies": sorted({s for r in rs for s in r["strategies"] if s.startswith(cap)}),
                    "categories": dict(Counter(r["hard_category"] for r in rs)),
                    "new": sum(r["origin"] == "v6" for r in rs)}
    gsig = Counter((tuple(r["core"]), tuple(r["mechanisms"]), tuple(r["strategies"])) for r in hard)
    # difficulty audit
    tiers = Counter((r["origin"], r["tier"]) for r in rows)
    ret = [r for r in rows if r["retiered"]]
    controls = [r for r in hard if r["control"] and r["control"] != r["family"]]
    ctrl_tier = Counter(next((x["tier"] for x in rows if x["task"] == r["task"] and r["control"] in x["cases"]), "non-formal")
                        for r in controls)
    ladders = sum(1 for t in doc["tasks"] for f in t["v6_formal"]["easy"] if
                  any(r["task"] == t["task_id"] and r["control"] == f and r["tier"] == "hard" for r in rows) and
                  any(r["task"] == t["task_id"] and r["control"] == f and r["tier"] == "medium" for r in rows))
    multi = [r for r in rows if len(r["cases"]) > 1]
    factors = Counter(r["factor"] for r in multi)
    status = Counter(r["status"] for r in rows)
    cats = Counter(r["hard_category"] for r in hard)
    modes = Counter(m.split("/")[1].split("-")[0] if "/" in m else m for r in hard for m in r["mechanisms"])
    n_episodes = 10 * len(rows)
    audit = {"families": len(rows), "episodes": n_episodes, "tiers": {f"{a}/{b}": n for (a, b), n in sorted(tiers.items())},
             "coverage": cov, "duplicates_within_task": dups, "distinct_hard_signatures": len(gsig),
             "hard_families": len(hard), "retiered": [{k: r[k] for k in ("task", "family", "retiered", "caps")} for r in ret],
             "control_tiers": dict(ctrl_tier), "ladders": ladders, "multi_case_families": len(multi),
             "decision_factors": dict(factors), "status": dict(status), "hard_categories": dict(cats),
             "failure_modes_in_hard": dict(modes), "static": {k: static[k] for k in ("episodes", "static_ok")},
             "static_problems": len(static["problems"]), "static_stale": stale_static, "rows": rows}
    (V6 / "design_audit.json").write_text(json.dumps(audit, indent=1))
    (V6 / "variant_cards.json").write_text(json.dumps(cards(doc), indent=1, ensure_ascii=False))
    (V6 / "capability_hypotheses.json").write_text(json.dumps(predictions(doc, rows), indent=1))
    (V6 / "DESIGN_AUDIT.md").write_text(design_md(doc, audit))
    (V6 / "ROUTES.md").write_text(routes_md(doc))
    skill_fix(doc, rows)
    physics_todo(doc, rows)
    print(f"{len(rows)} families, {n_episodes} episodes; status {dict(status)}; coverage "
          + ", ".join(f"{c} {v['variants']}/{v['tasks']}" for c, v in cov.items()))


def cards(doc):
    """One spec card per concrete variant: instruction, initial conditions, failure triggers, goal, expected
    capabilities (verified), oracle route, challenge / rationale, success criteria."""
    from episode.catalog import resolve_task
    out = {}
    for t in doc["tasks"]:
        for fam, info in t["v6_families"].items():
            for vid in info["cases"]:
                v = t["variants"][vid]
                rt = resolve_task(t, vid)
                meta = v.get("v6") or v.get("v5") or {}
                aud = t["v6_audit"][vid]
                fails = v.get("failures", [])
                out[f"{t['task_id']}/{vid}"] = {
                    "family": fam, "tier": info["tier"], "hard_category": info.get("hard_category"),
                    "seeds": sorted(int(s) for s, x in info["seeds"].items() if x == vid),
                    "instruction": rt["instruction"],
                    "initial_conditions": {"scene": t["scene"]["base"], "start": v.get("start"),
                                           "moved": sorted(v.get("move", {})), "added": sorted(v.get("add", {})),
                                           "removed": v.get("remove", []), "conditions": v.get("conditions", []),
                                           "initial_checks": [a for f in fails if f.get("when") == "initial" for a in f.get("check", [])]},
                    "failure_triggers": [{"id": f["id"], "kind": f["kind"], "persist": bool(f.get("persist")),
                                          "until_moved": f.get("until_moved"), "trigger": f.get("trigger"),
                                          "event": f.get("event"), "when": f.get("when", "action" if "trigger" in f and
                                                                                   f["kind"] in ("grasp", "slip", "placement", "ik") else "initial")}
                                         for f in fails],
                    "goal_constraints": rt["goal"],
                    "expected_capabilities": aud["verified"],
                    "capability_evidence": aud["evidence"],
                    "retry_solvable": aud["retry_solvable"], "control": aud["control"],
                    "oracle_route": t["oracle"][vid],
                    "challenge": meta.get("challenge") or v.get("note", ""), "rationale": meta.get("rationale", ""),
                    "success_criteria": "every GT goal atom holds at the end, nothing watched on the floor (unless "
                                        "allowed), every declared failure fired and manifested, the route's expected "
                                        "failures failed (benchmark/v5/validate.py classify)"}
    return out


def predictions(doc, rows):
    """Capability hypotheses for the baseline experiments: what each planner class should do per family.
    fixed  - executes the control plan, no recovery: fails whenever a failure or constraint touches it;
    retry  - repeats failed steps after re-parking: succeeds iff the family is retry-solvable;
    replanner - needs the family's verified capabilities."""
    out = []
    for r in rows:
        out.append({"task": r["task"], "family": r["family"], "tier": r["tier"], "capabilities": r["caps"],
                    "core": r["core"], "same_design_as": r.get("same_design_as"),
                    "expected": {"oracle": "success",
                                 "fixed": "success" if r["tier"] == "easy" else "fail",
                                 "retry": "success" if r["tier"] == "easy" or (r["tier"] == "medium" and not r["mechanisms"] == ["none"]
                                                                                and r["retry_solvable"]) else "fail",
                                 "task_level_replanner": "success (needs " + (", ".join(r["core"]) or "AF") + ")"},
                    "falsified_if": "retry succeeds on this Hard family" if r["tier"] == "hard" else None})
    return out


def smoke_rows(doc):
    """Physical smoke episodes of v6 features (benchmark/runs/v6_smoke*): did the injected failures fire, does
    the result belong to the current catalog, where did the episode end."""
    from benchmark.scene import episode_config
    from benchmark.v5.validate import classify, route_sha1
    T = {t["task_id"]: t for t in doc["tasks"]}
    out = []
    for f in sorted((ROOT / "benchmark/runs").glob("v6_smoke*/*/*/result.json")):
        r = json.loads(f.read_text())
        t = T.get(r["task_id"])
        cur = bool(t and r["variant"] in t["variants"]
                   and r.get("config_hash") == episode_config(t, r["seed"], r["variant"])["config_hash"]
                   and r.get("route_sha1") == route_sha1(t["routes"][t["oracle"][r["variant"]]]["steps"]))
        fi = r.get("failure_injection") or {}
        stop = next((c for c in r.get("calls", []) if not c["feedback"]["success"] and c.get("expect") != "fail"), None)
        out.append({"run": f.parts[-4], "task": r["task_id"], "variant": r["variant"], "seed": r["seed"], "current": cur,
                    "status": classify(r), "fired": fi.get("fired"), "manifested": fi.get("manifested"),
                    "not_fired": fi.get("not_fired"),
                    "stop": f"{stop['skill']}: {(stop['feedback'].get('error') or '')[:120]}" if stop else None})
    return out


def _check(ok):
    return "PASS" if ok else "**OPEN**"


def design_md(doc, a):
    rows = a["rows"]
    cov = a["coverage"]
    md = ["# ZenoBench v6 design audit", "",
          "Generated by `python benchmark/v6/report_v6.py` from `tasks.json`, `STATIC.json` (static checks) and "
          "`benchmark/v5/PHYSICS.json` (the v5 physics baseline). Static and physical evidence are kept apart; "
          "a static pass is never reported as physically solvable.", "",
          "## Scale", "",
          f"* 20 base tasks, **{a['families']} formal families** (v5: 180, new: {a['families'] - 180}), "
          f"**{a['episodes']} formal episodes** (seeds 10-19 per family).",
          "* Tiers (origin/tier): " + ", ".join(f"{k} {v}" for k, v in a["tiers"].items()) + ".",
          f"* Hard: {a['hard_families']} families; categories " + ", ".join(f"{k} {v}" for k, v in sorted(a['hard_categories'].items(), key=str)) + ".",
          f"* Static checks: {a['static']['static_ok']} / {a['static']['episodes']} episodes pass, "
          f"{a['static_problems']} problems" + (" (STATIC.json is stale!)" if a["static_stale"] else "") + ".",
          "* Status: " + ", ".join(f"{k} {v}" for k, v in sorted(a["status"].items())) + ".", "",
          "## Core-capability coverage (Hard tier, verified hypotheses only)", "",
          "| capability | Hard families | distinct designs | tasks | new | failure mechanisms | recovery strategies | Hard categories |",
          "|---|---|---|---|---|---|---|---|"]
    for c, v in cov.items():
        md.append(f"| {c} {CAP_NAMES[c]} | {v['variants']} | {v['designs']} | {v['tasks']} | {v['new']} | {len(v['mechanisms'])}: "
                  + ", ".join(v["mechanisms"]) + f" | {len(v['strategies'])}: " + ", ".join(v["strategies"])
                  + " | " + ", ".join(f"{k} {n}" for k, n in sorted(v["categories"].items(), key=str)) + " |")
    tasks = sorted({r["task"] for r in rows})
    md += ["", "### Capability x task (Hard families)", "", "| capability | " + " | ".join(short(t) for t in tasks) + " |",
           "|---|" + "---|" * len(tasks)]
    for c in cov:
        md.append(f"| {c} | " + " | ".join(str(sum(1 for r in rows if r['task'] == t and r['tier'] == 'hard' and c in r['caps']) or "")
                                          for t in tasks) + " |")
    md += ["", "## Difficulty audit", "",
           "One rule for every variant (`hypotheses.py`): **Hard** = at least one verified core capability (DR, GD, SR, "
           "CL, PP) and not solvable by retrying the control plan; **Medium** = an adaptation (transient failure, "
           "search, stated substitute, constraint) without a core capability; **Easy** = the nominal plan works.", "",
           f"* Re-tiered v5 variants (configurations unchanged, labels only): {len(a['retiered'])}.",
           "  " + "; ".join(f"`{short(r['task'])}/{r['family']}` {r['retiered']}" for r in a["retiered"]),
           "  Typical reasons: the challenge is a stated substitute, a decoy, a free-spot choice or fetching a goal "
           "object (AF only), or the nominal plan already works (distractor resistance).",
           f"* Hard families with a matched control in the same task: {sum(a['control_tiers'].values())} "
           f"(control tier: " + ", ".join(f"{k} {v}" for k, v in a["control_tiers"].items()) + "); "
           f"{a['ladders']} Easy variants anchor an Easy -> Medium -> Hard ladder of new families.",
           "", "## Seed diversity", "",
           f"* {a['multi_case_families']} families vary a decision-relevant fact across seeds (each case its own "
           "oracle route); factors: " + "; ".join(f"{k} ({v})" for k, v in a["decision_factors"].items()) + ".",
           "* All other families vary object positions (1 cm grid, gaps that make a condition hold kept) and the "
           "start pose per seed; the v5 configurations are frozen by design, so their seeds stay positional. The "
           "v5 failure-timing study (T09, T12, T13, T19: early / middle / late, 120 episodes) covers failure timing.",
           "* Every seed is reproducible: the seed -> case manifest is a fixed-RNG balanced assignment and every "
           "configuration has a hash (tests/test_v6_catalog.py).", "",
           "## Duplication", "",
           f"* {a['distinct_hard_signatures']} distinct (core capabilities, failure mechanisms, recovery strategies) "
           f"signatures among {a['hard_families']} Hard families.",
           f"* Same signature within one task: {len(a['duplicates_within_task'])} groups"
           + (": " + "; ".join(f"{k} -> {v}" for k, v in a["duplicates_within_task"].items()) if a["duplicates_within_task"] else "")
           + ". These are v5 Action / Mixed variants of one task-level scene that differ only in which transient "
             "local failures are added; their configurations are frozen, so they stay, marked `same_design_as` in "
             "design_audit.json / capability_hypotheses.json: analyses count each group as one design "
             f"({a['hard_families'] - sum(len(v) - 1 for v in a['duplicates_within_task'].values())} distinct Hard "
             "designs).", "",
           "## Conference-level design checklist", "",
           "| # | requirement | measured | result |", "|---|---|---|---|"]
    core = ["DR", "GD", "SR", "CL", "PP"]
    c1 = all(cov[c]["designs"] >= TARGET["variants"] and cov[c]["tasks"] >= TARGET["tasks"] for c in core)
    md.append(f"| 1 | each core capability >= {TARGET['variants']} variants on >= {TARGET['tasks']} tasks | "
              + ", ".join(f"{c} {cov[c]['designs']} designs ({cov[c]['variants']} families) / {cov[c]['tasks']} tasks"
                          for c in core) + f" | {_check(c1)} |")
    c2 = all(len(cov[c]["mechanisms"]) >= 3 and len(cov[c]["strategies"]) >= 2 for c in core)
    md.append("| 2 | several failure mechanisms and recovery strategies per capability | "
              + ", ".join(f"{c} {len(cov[c]['mechanisms'])} mech / {len(cov[c]['strategies'])} strat" for c in core)
              + f" | {_check(c2)} |")
    modes = a["failure_modes_in_hard"]
    c3 = all(k in a["hard_categories"] for k in ("task", "action", "mixed", "dynamic")) and modes.get("initial") and modes.get("dynamic")
    md.append("| 3 | action / task / mixed / dynamic failures, before and during execution | categories "
              + ", ".join(f"{k} {v}" for k, v in sorted(a['hard_categories'].items(), key=str)) + "; modes "
              + ", ".join(f"{k} {v}" for k, v in sorted(modes.items())) + f" | {_check(c3)} |")
    c4 = all(r["core"] and not r["retry_solvable"] for r in rows if r["tier"] == "hard")
    md.append(f"| 4 | Hard requires task-level replanning, no retry-only Hard | every Hard has a verified core capability "
              f"and is not retry-solvable; {len(a['retiered'])} v5 labels corrected | {_check(c4)} |")
    md.append(f"| 5 | one difficulty definition, control variants | rule in `hypotheses.py`; "
              f"{sum(a['control_tiers'].values())} Hard families with a control in the task | PASS |")
    c6 = a["multi_case_families"] >= 20
    md.append(f"| 6 | decision-relevant seed diversity, reproducible | {a['multi_case_families']} families with decision "
              f"cases ({len(a['decision_factors'])} factors); positional jitter elsewhere; v5 seeds frozen | "
              f"{_check(c6)} (v5 families positional by the freeze) |")
    md.append("| 7 | full spec per variant | instruction, initial conditions, failure triggers, goal, verified "
              "capabilities, oracle route, challenge / rationale, success criteria for every concrete variant: "
              "`variant_cards.json` | PASS |")
    md.append(f"| 8 | semantics, objects, skills, scene constraints, trigger timing, feasible route | static checks "
              f"{a['static']['static_ok']}/{a['static']['episodes']}; physical feasibility only where simulated | "
              f"{_check(a['static_problems'] == 0)} (static) |")
    md.append("| 9 | independent capability rules, capability hypotheses for baselines | cause -> blocked control "
              "plan -> oracle consistency per capability, negative tests; per-family planner predictions in "
              "`capability_hypotheses.json` (a Hard family a retry planner solves falsifies its label) | PASS |")
    nd = sum(len(v) - 1 for v in a["duplicates_within_task"].values())
    md.append(f"| 10 | no inflated duplicates | {a['distinct_hard_signatures']} distinct signatures / "
              f"{a['hard_families']} Hard; {nd} frozen v5 near-duplicates marked and counted once; no new family "
              f"duplicates another in its task | {_check(not any(f.startswith('x6_') for v in a['duplicates_within_task'].values() for f in v))} |")
    sm = smoke_rows(doc)
    md += ["", "## Physical smoke runs (failure-injection features in Isaac Sim)", "",
           "Light checks, not a validation grid: one episode per new runtime feature. `current`: the result's hash "
           "and route match this catalog (earlier rows show what the route fixes were based on).", "",
           "| run | task | variant | seed | current | result | injected failures fired / manifested | stopped at |",
           "|---|---|---|---|---|---|---|---|"]
    for r in sm:
        md.append(f"| {r['run']} | {short(r['task'])} | {r['variant']} | {r['seed']} | {'yes' if r['current'] else 'no'} | "
                  f"{r['status']} | {len(r['manifested'] or [])}/{len((r['fired'] or [])) + len(r['not_fired'] or [])} | "
                  f"{(r['stop'] or '-').replace('|', '/')} |")
    md += ["", "External dependencies (cannot be closed at the task level): physical solvability of the skills "
           "(SKILL_FIX_LIST.md) and the simulation of every new family (PHYSICS_TODO.md).", "",
           "## Family matrix", "",
           "| task | family | tier | cat | capabilities | failure mechanisms | recovery strategies | cases | control | physics | status |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["task"], ["easy", "medium", "hard"].index(r["tier"]), r["family"])):
        md.append(f"| {short(r['task'])} | {r['family']} | {r['tier']}{' (v5 ' + r['v5_tier'] + ')' if r['retiered'] else ''} | "
                  f"{r['hard_category'] or ''} | {' '.join(r['caps']) or '-'} | {'; '.join(r['mechanisms'])} | "
                  f"{'; '.join(r['strategies'])} | {len(r['cases'])} | {r['control']} | {r['physics']} | {r['status']} |")
    return "\n".join(md) + "\n"


def routes_md(doc):
    md = ["# v6 oracle reference routes", "", "One line per concrete variant of each formal family (`!` expected to "
          "fail, `+` recovery step). Seeds: the family's manifest in tasks.json.", ""]
    for t in doc["tasks"]:
        md += [f"## {t['task_id']}", ""]
        for tier in ("easy", "medium", "hard"):
            for fam in t["v6_formal"][tier]:
                for v in t["v6_families"][fam]["cases"]:
                    steps = t["routes"][t["oracle"][v]]["steps"]
                    txt = " ".join(("!" if s.get("expect") == "fail" else "") + ("+" if s.get("role") in ("recover", "recovery", "alternative") else "")
                                   + s["skill"] + "(" + ",".join(str(x) for x in s["args"].values()) + ")" for s in steps)
                    md.append(f"* `{v}` ({tier}, {t['oracle'][v]}, {len(steps)} steps): {txt}")
        md.append("")
    return "\n".join(md)


def _cause(err):
    e = (err or "").lower()
    if "slipped" in e or "dropped" in e:
        return "carry slip"
    if "not held" in e or "finger contact" in e or "handle not grasped" in e or "overhang" in e:
        return "grasp miss"
    if "no ik" in e or "no base pose" in e or "reach" in e or "posture" in e or "turning in place" in e or "trajopt" in e:
        return "IK / reach / base pose"
    if "joint" in e:
        return "articulation (door does not move)"
    if "xy err" in e or "tilt" in e or "flipped" in e:
        return "placement result"
    if "not seen" in e or "in_view" in e or "frustum" in e or "occluded" in e or "not_found" in e:
        return "perception / search"
    return "other"


def skill_fix(doc, rows):
    """Skill Fix List: v5 baseline failures by skill / object, and the v6 routes' exposure to them."""
    P = json.loads((ROOT / "benchmark/v5/PHYSICS.json").read_text())
    stats = defaultdict(lambda: {"ok": 0, "fail": 0, "causes": Counter(), "tasks": set(), "examples": []})
    for r in P["rows"]:
        if r["status"] == "unrun":
            continue
        res = json.loads((ROOT / r["file"]).read_text())
        for c in res.get("calls", []):
            if c.get("expect") == "fail":
                continue
            obj = c["args"].get("object") or c["args"].get("articulated") or c["args"].get("surface") or \
                c["args"].get("container") or c["args"].get("target") or c["args"].get("destination") or ""
            k = (c["skill"], obj)
            if c["feedback"]["success"]:
                stats[k]["ok"] += 1
            else:
                stats[k]["fail"] += 1
                stats[k]["causes"][_cause(c["feedback"].get("error"))] += 1
                stats[k]["tasks"].add(r["task"][:3])
                if len(stats[k]["examples"]) < 2:
                    stats[k]["examples"].append((c["feedback"].get("error") or "")[:140])
    # exposure of the new families
    need = defaultdict(set)
    for t in doc["tasks"]:
        for fam, info in t["v6_families"].items():
            if info["origin"] != "v6":
                continue
            for v in info["cases"]:
                for s in t["routes"][t["oracle"][v]]["steps"]:
                    if s.get("expect") == "fail":
                        continue
                    obj = s["args"].get("object") or s["args"].get("articulated") or s["args"].get("surface") or \
                        s["args"].get("container") or s["args"].get("target") or s["args"].get("destination") or ""
                    extra = ":both" if s["args"].get("hands") == "both" else ""
                    need[(s["skill"] + extra, obj)].add(f"{t['task_id'][:3]}/{fam}")
    top = sorted(((k, v) for k, v in stats.items() if v["fail"] >= 3), key=lambda kv: -kv[1]["fail"])
    md = ["# Skill Fix List (for the skill / physics owner)", "",
          "Task design does not change skills; this list is what the v5 physics baseline (1,800 oracle episodes, "
          "`benchmark/v5/PHYSICS.json`) and the v6 reference routes need from them. No new skill interface is "
          "required: every v6 route uses existing contracts. Counts are calls in oracle episodes that were expected "
          "to succeed.", "",
          "## 1. Failing skill uses in the v5 baseline (>= 3 failures)", "",
          "| skill | object | ok | failed | fail rate | main causes | tasks | v6 families also using it | example |",
          "|---|---|---|---|---|---|---|---|---|"]
    for (sk, obj), v in top:
        n = v["ok"] + v["fail"]
        users = sorted(need.get((sk, obj), set()))
        md.append(f"| {sk} | {obj} | {v['ok']} | {v['fail']} | {100 * v['fail'] / n:.0f}% | "
                  + ", ".join(f"{c} {k}" for c, k in v["causes"].most_common(3)) + f" | {' '.join(sorted(v['tasks']))} | "
                  f"{len(users)} | {v['examples'][0] if v['examples'] else ''} |".replace("|  |", "| |"))
    never = sorted((k, v) for k, v in need.items() if k not in stats and k[0] not in ("look", "navigate", "search",
                                                                                         "bend", "straighten", "nod"))
    md += ["", "## 2. Skill uses the v6 routes need that the v5 baseline never ran", "",
           "| skill | object | families |", "|---|---|---|"]
    for (sk, obj), fams in never:
        md.append(f"| {sk} | {obj} | {', '.join(sorted(fams))} |")
    md += ["", "## 3. Priorities", "",
           "1. **Low cabinet doors** (`open` / `close` / `explore_furniture` on kitchen_cabinet_4 and _6): every v5 "
           "cabinet Hard was 0/10; v6 inspection families (T04, T05, T10, T13, T18, T20) depend on them.",
           "2. **Grasp of tall / round / rimmed objects**: juice bottle (side pinch knocks it over), mug and bowl rim "
           "pinches (T13, T20), cup carry.",
           "3. **Book carry**: one-handed slip of paperback / red book (T01, T14); v6 adds the two-handed carry "
           "(`pick(hands=both)` then `navigate`) as the strategy-replacement route - it needs to work physically.",
           "4. **Wipe reach** (T08) and **pick from inside the microwave cavity** (T10 v5 Hards 0/10; v6 "
           "`x6_gd_can_put_away__in_microwave`, `x6_gd_bowl_put_away__in_microwave`).",
           "5. **Search of small objects** on the dining table (smoke run: `search wooden_block_b` did not see the "
           "block on the dining table in T06) and of the pot lid (v5: `search pot_lid` 0/10 in T17).",
           "6. **Bimanual flat pick** (`pick(hands=both)`, zeno_skills/policies/bimanual.py): it needs the book's "
           "long side (half length >= 9 cm) along an overhanging edge; the T01 / T14 books overhang with the short "
           "side (yaw 90), so the two-handed carry of `x6_sr_two_hand_carry` stops there (smoke runs v6_smoke3/4, "
           "after the injected slips and the slip restore worked). Either accept short-edge overhangs or provide a "
           "re-orientation the route can call.",
           "7. **Apple pick from the bookcase top** after it rolled out of the basket (T11 `x6_cl_apple_rolls_out`, "
           "smoke: `not held`).",
           "8. New primitive uses: cherry-tomato `pick` + `drop` into the pot (T09 split), `place` into the trash can "
           "(T10) and of the foam cube into the bin (T19), `drop` + `cover` instead of `hide` (T17), three-block "
           "`stack` (T02).", ""]
    (V6 / "SKILL_FIX_LIST.md").write_text("\n".join(md) + "\n")


def physics_todo(doc, rows):
    new_jobs, todo = [], []
    def deps_of(t, vid, st):
        a = st["args"]
        if st["skill"] in ("open", "close", "explore_furniture") and str(a.get("articulated") or a.get("furniture")).startswith("kitchen_cabinet"):
            return "low cabinet doors"
        if st["skill"] == "pick" and a.get("hands") == "both":
            return "bimanual flat pick (long side along an overhanging edge)"
        if st["skill"] == "pick" and a.get("object") == "juice_bottle":
            return "juice bottle grasp"
        if st["skill"] == "pick" and ((t["variants"][vid].get("move", {}).get(a.get("object")) or {}).get("support") or "").startswith("kitchen_microwave/"):
            return "pick from the microwave cavity"
        if st["skill"] == "search" and a.get("object") == "pot_lid":
            return "search of the pot lid"
        if st["skill"] == "wipe":
            return "wipe reach"
        return None
    for t in doc["tasks"]:
        for fam, info in t["v6_families"].items():
            r = next(x for x in rows if x["task"] == t["task_id"] and x["family"] == fam)
            if r["status"] == "PHYSICS_VALIDATED":
                continue
            deps = sorted({d for v in info["cases"] for s in t["routes"][t["oracle"][v]]["steps"]
                           if s.get("expect") != "fail" for d in [deps_of(t, v, s)] if d})
            for s, vid in sorted(info["seeds"].items()):
                job = {"task": t["task_id"], "seed": int(s), "variant": vid, "route": t["oracle"][vid], "tier": info["tier"],
                       "family": fam}
                todo.append(job)
                if info["origin"] == "v6":
                    new_jobs.append(job)
            r["depends_on"] = deps
    (V6 / "batches").mkdir(exist_ok=True)
    (V6 / "batches/physics_v6_new.json").write_text(json.dumps(new_jobs, indent=0))
    (V6 / "batches/physics_todo.json").write_text(json.dumps(todo, indent=0))
    by_status = Counter(r["status"] for r in rows)
    md = ["# Physics validation to do", "",
          f"* {by_status.get('PHYSICS_VALIDATED', 0)} families are PHYSICS_VALIDATED (10/10 seeds passed in the v5 "
          "grid with the current hash and route).",
          f"* {len(todo)} episodes remain ({len(new_jobs)} of the {sum(1 for r in rows if r['origin'] == 'v6')} new "
          "families): `batches/physics_todo.json`; the new families alone: `batches/physics_v6_new.json`.",
          "* Run: `$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch "
          "benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval` "
          "(~43 episodes / hour with 2 simulators).",
          "* Order: (1) new families without a skill dependency (`depends on` -), (2) after each skill fix the "
          "families that depend on it, (3) re-run T11 `h_action_grasp_and_ik` (failure-injection fix 019e517; it "
          "passed in the smoke run), (4) the v5 families below 10/10 after each skill fix.", "",
          "| task | family | tier | physics now | depends on |", "|---|---|---|---|---|"]
    for r in rows:
        if r["status"] != "PHYSICS_VALIDATED":
            md.append(f"| {short(r['task'])} | {r['family']} | {r['tier']} | {r['physics']} | "
                      f"{', '.join(r.get('depends_on', [])) or '-'}{' ; ' + r['rerun_needed'] if r['rerun_needed'] else ''} |")
    (V6 / "PHYSICS_TODO.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
