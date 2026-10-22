"""Planner-level evaluation of benchmark runs (offline, from result.json).

    python benchmark/evaluate.py --runs benchmark/runs/final            # -> benchmark/EVALUATION.md, metrics.json
    python benchmark/evaluate.py --runs DIR --group planner,tier        # other groupings: task, route, kind, variant,
                                                                        # ctype (condition type), condition
    python benchmark/evaluate.py --tasks benchmark/v3/tasks.json --runs DIR --md benchmark/v3/EVALUATION.md \
        --json benchmark/v3/metrics.json      # v3: runs whose configuration hash differs are not counted

report.py answers "did each declared route run and which SkillNodes did it
cover"; this script scores how a planner behaved.  Definitions: README,
*Evaluation*.  Short form:

  SR        task success over completed episodes (incomplete = crash / timeout, counted apart)
  skill_SR  share of calls that succeeded (scripted calls marked expect: fail left out)
  GC        goal-condition score: fraction of goal atoms that hold (best ``any`` group)
  pass^k    share of tasks whose every seed in the group passed
  SPL-c     S * L_ref / max(L, L_ref); L_ref = calls of the variant's oracle route, used only
            when a passing run of that route on that variant is in the evaluated runs
  failures per episode by class:
    gate    observation refusals: unseen (exists, not observed), ghost (not in this
            episode), not_in_view
    pre     state / geometry preconditions (PRECONDITION_FAILED, NO_PATH)
    exec    execution failures (POLICY_FAILED, SUBSKILL_FAILED, POSTCONDITION_FAILED)
    invalid interface errors (BAD_CALL, INPUT_*, NOUN_INVALID, BINDING)
  recov_*   of the episodes with >= 1 failure of that class, the share that succeeded (n shown)
  repeat    share of pre + exec failures followed by the same call with the same arguments
  drops / side / budget   floor drops, non-goal objects moved > 5 cm, closed-loop budget hits
N/A: no sample for that ratio.

EVALUATION_SPEC.md metrics (benchmark/metrics.py; section "Evaluation-spec metrics" of
the output, per-episode facts in <json>.facts.jsonl): TSR under the instruction
semantics (benchmark/eval_semantics.py), Planning Correctness, FSR, ERSR with local
recovery kept apart from task success, robustness groups, efficiency, success types
and failure attribution.  Feasibility evidence for FSR / attribution: passing scripted
routes in the evaluated runs plus ``--conditions`` (default: conditions.json next to
the task file).  ``--planned N`` / ``--batch FILE...`` give the planned episode count.

Equal weights (v3): ``SR_task`` is the mean over tasks of each task's SR, ``SR_cond``
the mean over (task, variant) conditions, so a task with more conditions does not
dominate.  Grouping by ``ctype`` puts an episode in every one of its condition types
(easy conditions: ``nominal``); those groups overlap.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from episode.catalog import load_catalog  # noqa: E402
from episode.profile import run_profile_current  # noqa: E402

TICK_HZ = 120.0
GROUNDING = {"NOT_OBSERVED", "NOT_IN_VIEW", "NOT_FOUND"}
PRECONDITION = {"PRECONDITION_FAILED", "NO_PATH"}
EXECUTION = {"POLICY_FAILED", "SUBSKILL_FAILED", "POSTCONDITION_FAILED"}
SIDE_EFFECT_M = 0.05


def load(root):
    for f in sorted(Path(root).glob("*/*/result.json")):
        r = json.loads(f.read_text())
        d = f.parent
        cfg = json.loads((d / "config.json").read_text()) if (d / "config.json").exists() else {}
        ann = json.loads((d / "annotation.json").read_text()) if (d / "annotation.json").exists() else {}
        r["_dir"] = str(d)
        r["_scene"] = cfg.get("scene", {})
        r["_hash"] = cfg.get("config_hash") or r["_scene"].get("config_hash")
        r["_profile_ok"] = run_profile_current(cfg)
        r["_objects"] = {o["name"] for o in ann.get("objects", [])}
        r["_rooms"] = ann.get("rooms") or {}
        r["_removed"] = list(r["_scene"].get("remove") or [])
        yield r


def ref_len(task, variant):
    """Calls the GT oracle makes on this variant (expected failures and unwinds skipped)."""
    route = (task.get("oracle") or {}).get(variant)
    steps = (task.get("routes") or {}).get(route, {}).get("steps")
    if not steps:
        return None
    return sum(1 for s in steps if s.get("expect") != "fail" and s.get("role") != "unwind")


def goal_score(goal):
    rows = goal.get("all", [])
    groups = goal.get("any", [])
    best = max((sum(r["holds"] for r in g) / len(g) for g in groups if g), default=None)
    parts = [r["holds"] for r in rows]
    n = len(parts) + (1 if best is not None else 0)
    return (sum(parts) + (best or 0)) / n if n else 0.0


def goal_objects(task):
    names = set()
    for a in task.get("goal", {}).get("all", []) + [a for g in task.get("goal", {}).get("any", []) for a in g]:
        names.update(x for x in a[1:] if isinstance(x, str))
    return names


def episode_metrics(r, task, verified_refs):
    calls = r.get("calls", [])
    fbs = [c["feedback"] for c in calls]
    m = {"incomplete": bool(r.get("incomplete") or r.get("crash"))}
    m["success"] = bool(r.get("task_success")) and not m["incomplete"]
    if r.get("planner") == "scripted" and r.get("stopped_at") is not None:
        m["success"] = False            # the declared chain did not run to its end
    m["gc"] = goal_score(r.get("goal", {})) if r.get("goal") else 0.0
    m["calls"] = len(calls)
    graded = [fb for c, fb in zip(calls, fbs) if c.get("expect") != "fail"]
    m["skill_ok"], m["skill_n"] = sum(bool(fb.get("success")) for fb in graded), len(graded)
    L = ref_len(task, r.get("variant"))
    ok_ref = L is not None and (r["task_id"], r.get("variant")) in verified_refs
    m["l_ref"] = L if ok_ref else None
    m["spl"] = (float(m["success"]) * L / max(m["calls"], L)) if ok_ref and m["calls"] and not m["incomplete"] else None
    ticks = r.get("sim_ticks") or max((c.get("tick") or 0 for c in calls), default=0)
    m["sim_s"] = ticks / TICK_HZ
    m["wall_s"] = r.get("wall_s")
    g = defaultdict(int)
    repeats = 0
    for i, fb in enumerate(fbs):
        code = fb.get("error_code")
        if fb.get("success") or code is None:
            continue
        if code in GROUNDING:
            name = re.findall(r"'([^']+)'", fb.get("error") or "")
            name = name[0] if name else None
            if code == "NOT_IN_VIEW":
                g["not_in_view"] += 1
            elif name is not None and r["_objects"] and name not in r["_objects"]:
                g["ghost"] += 1          # an object this episode does not contain
            else:
                g["unseen"] += 1
            continue
        g["pre" if code in PRECONDITION else "exec" if code in EXECUTION else "invalid"] += 1
        if code in PRECONDITION | EXECUTION and i + 1 < len(calls) and \
                calls[i + 1]["skill"] == calls[i]["skill"] and calls[i + 1]["args"] == calls[i]["args"]:
            repeats += 1
    m.update({k: g[k] for k in ("unseen", "ghost", "not_in_view", "pre", "exec", "invalid")})
    m["gate"] = g["unseen"] + g["ghost"] + g["not_in_view"]
    m["repeats"] = repeats
    m["dropped"] = bool(r.get("dropped"))
    # side effects: non-goal watched objects displaced from where the episode started
    final = r.get("final_state") or (calls[-1].get("state") if calls and calls[-1].get("state") else {})
    m["final_state_source"] = "final_state" if r.get("final_state") else "last_call_state"
    keep = goal_objects(task)
    side = []
    for n, p0 in (r.get("initial_positions") or {}).items():
        p1 = (final.get(n) or {}).get("pos")
        if n in keep or p1 is None:
            continue
        if sum((a_ - b_) ** 2 for a_, b_ in zip(p0, p1)) ** 0.5 > SIDE_EFFECT_M:
            side.append(n)
    m["side"] = side
    m["stop_reason"] = r.get("stop_reason")
    m["budget"] = r.get("stop_reason") == "budget"
    return m


def label(r, key, tasks):
    t = tasks.get(r["task_id"], {})
    if key == "planner":
        return r.get("planner") or "?"
    if key == "tier":
        return r["_scene"].get("difficulty", "?")
    if key == "task":
        return r["task_id"]
    if key == "route":
        return str(r.get("route") or r.get("planner"))
    if key == "kind":
        return t.get("routes", {}).get(r.get("route"), {}).get("kind", r.get("planner"))
    if key == "variant":
        return r.get("variant", "?")
    if key == "condition":
        return f"{r['task_id'][:3]}/{r.get('variant', '?')}"
    if key == "ctype":
        return r["_ctype"]
    if key == "profile":
        return r.get("profile") or "benchmark"       # runs from before profiles: LimitedSession
    raise ValueError(key)


def aggregate(eps):
    done = [(r, m) for r, m in eps if not m["incomplete"]]
    mean = lambda xs: (sum(xs) / len(xs)) if xs else None
    by_task = defaultdict(list)
    for r, m in done:
        by_task[r["task_id"]].append(m["success"])
    by_cond = defaultdict(list)
    for r, m in done:
        by_cond[(r["task_id"], r.get("variant"))].append(m["success"])
    out = {"n": len(eps), "incomplete": len(eps) - len(done),
           "SR": mean([m["success"] for _, m in done]),
           "SR_task": mean([mean(v) for v in by_task.values()]), "SR_cond": mean([mean(v) for v in by_cond.values()]),
           "skill_SR": (sum(m["skill_ok"] for _, m in done) / max(1, sum(m["skill_n"] for _, m in done)))
           if any(m["skill_n"] for _, m in done) else None,
           "GC": mean([m["gc"] for _, m in done]),
           "pass^k": mean([all(v) for v in by_task.values()]), "tasks": len(by_task),
           "SPL-c": mean([m["spl"] for _, m in done if m["spl"] is not None]),
           "spl_n": sum(m["spl"] is not None for _, m in done),
           "calls": mean([m["calls"] for _, m in done]), "sim_s": mean([m["sim_s"] for _, m in done])}
    for k in ("gate", "unseen", "ghost", "not_in_view", "pre", "exec", "invalid"):
        out[k] = mean([m[k] for _, m in done])
    for k in ("gate", "pre", "exec"):
        hit = [m for _, m in done if m[k]]
        out[f"recov_{k}"], out[f"recov_{k}_n"] = mean([m["success"] for m in hit]), len(hit)
    fails = sum(m["pre"] + m["exec"] for _, m in done)
    out["repeat"] = (sum(m["repeats"] for _, m in done) / fails) if fails else None
    out["repeat_n"] = fails
    out["drops"] = sum(m["dropped"] for _, m in done)
    out["side"] = mean([len(m["side"]) for _, m in done])
    out["budget"] = sum(m["budget"] for _, m in done)
    return out


def fmt(v, pct=False):
    if v is None:
        return "N/A"
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    return f"{100 * v:.0f}%" if pct else f"{v:.2f}"


# (column, percent?, denominator key shown in brackets)
COLS = [("n", 0, None), ("incomplete", 0, None), ("SR", 1, None), ("SR_task", 1, None), ("SR_cond", 1, None),
        ("skill_SR", 1, None), ("GC", 1, None),
        ("pass^k", 1, None), ("SPL-c", 0, "spl_n"), ("calls", 0, None), ("sim_s", 0, None),
        ("unseen", 0, None), ("ghost", 0, None), ("not_in_view", 0, None), ("pre", 0, None), ("exec", 0, None),
        ("invalid", 0, None), ("recov_gate", 1, "recov_gate_n"), ("recov_pre", 1, "recov_pre_n"),
        ("recov_exec", 1, "recov_exec_n"), ("repeat", 1, "repeat_n"), ("drops", 0, None), ("side", 0, None),
        ("budget", 0, None)]


def table(groups, keys):
    lines = ["| " + " | ".join(keys) + " | " + " | ".join(c for c, _, _ in COLS) + " |",
             "|" + "---|" * (len(keys) + len(COLS))]
    for g, agg in sorted(groups.items()):
        cells = [fmt(agg[c], pct) + (f" ({agg[d]})" if d else "") for c, pct, d in COLS]
        lines.append("| " + " | ".join(g) + " | " + " | ".join(cells) + " |")
    return lines


PLANNER_NOTE = ("`fixed`, `retry` and `recovery` share the observation gate, the low-level settings "
                "(`auto_recovery` off, upright edge-pinch waist) and the skill set; `fixed` runs the nominal plan "
                "once, `retry` repeats a failed call up to twice, `recovery` is bounded by the task's `max_calls` "
                "(default 60). `oracle` is a capability upper bound, not a planner: it uses the GT runner (full "
                "state, no observation gate, nested repair on) and the hand-written route for the variant, without "
                "its expected-failure and unwind steps. `scripted` replays declared routes, which fail on purpose "
                "(feasibility evidence). Neither is a baseline for VLM recovery gain.")


def feasibility(a, runs, tasks):
    """(task, variant) pairs with a passing scripted route, and those with a passing alternative route."""
    feas, alt, routes = set(), set(), set()
    for r in runs:
        t = tasks.get(r["task_id"], {})
        rt = t.get("routes", {}).get(r.get("route"))
        if r.get("planner") != "scripted" or rt is None or rt.get("kind") == "diagnostic":
            continue
        if r.get("task_success") and r.get("stopped_at") is None and not r.get("incomplete"):
            feas.add((r["task_id"], r.get("variant")))
            routes.add((r["task_id"], r.get("variant"), r.get("route")))
            if rt.get("kind") == "alternative":
                alt.add((r["task_id"], r.get("variant")))
    cpath = Path(a.conditions) if a.conditions else Path(a.tasks).with_name("conditions.json")
    if cpath.exists():
        for c in json.loads(cpath.read_text()).get("conditions", []):
            for rt in c.get("routes", []):
                if rt.get("passed"):
                    feas.add((c["task"], c["variant"]))
                    routes.add((c["task"], c["variant"], rt.get("route")))
                    if rt.get("kind") == "alternative":
                        alt.add((c["task"], c["variant"]))
    return feas, alt, routes


def spec_metrics(a, eps, runs, tasks):
    """EVALUATION_SPEC.md: per-episode facts and the six metrics per planner."""
    from benchmark.metrics import episode_facts, spec_markdown, spec_summary
    feas, alt, routes = feasibility(a, runs, tasks)
    facts = []
    for r, m in eps:
        t = tasks[r["task_id"]]
        ctx = {"objects": r["_objects"], "rooms": r["_rooms"], "feasible": feas, "alt_feasible": alt,
               "feasible_routes": routes,
               "ref_len": ref_len(t, r.get("variant"))}
        facts.append(episode_facts(r, t, ctx))
    planned = a.planned
    if planned is None and a.batch:
        planned = sum(len(json.loads(Path(b).read_text())) for b in a.batch)
    by = defaultdict(list)
    for f in facts:
        by[f["planner"] or "?"].append(f)
    summaries = {p: spec_summary(v, planned if len(by) == 1 else None) for p, v in by.items()}
    return {"facts": facts, "summaries": summaries, "markdown": spec_markdown(summaries)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", default=[str(ROOT / "benchmark/runs/final")],
                    help="run directories (a later one supersedes the same task/seed/variant/planner/route)")
    ap.add_argument("--tasks", default=str(ROOT / "benchmark/tasks.json"))
    ap.add_argument("--group", default="planner,tier", help="comma list of planner,tier,task,route,kind,variant,profile")
    ap.add_argument("--probes", action="store_true", help="include the P* probes (default: tasks T* only)")
    ap.add_argument("--md", default=str(ROOT / "benchmark/EVALUATION.md"))
    ap.add_argument("--json", default=str(ROOT / "benchmark/metrics.json"))
    ap.add_argument("--conditions", help="conditions.json with route acceptance (default: next to --tasks)")
    ap.add_argument("--batch", nargs="*", default=[], help="batch files: planned episodes = their job count")
    ap.add_argument("--planned", type=int, help="planned episodes (instead of --batch)")
    a = ap.parse_args()
    doc = json.loads(Path(a.tasks).read_text())
    tasks = load_catalog(a.tasks)
    keys = a.group.split(",")
    by_key = {}
    for root in a.runs:
        for r in load(root):
            by_key[(r["task_id"], r.get("seed"), r.get("variant"), r.get("planner"), r.get("route"))] = r
    runs = list(by_key.values())
    not_counted = []
    if doc.get("schema_version", 1) >= 3:
        # benchmark v3 and skill_library/tasks.json: only episodes of the configuration the current
        # task file and profile generate count
        from benchmark.scene import episode_config
        keep = []
        for r in runs:
            t = tasks.get(r["task_id"])
            ok = t is not None and r.get("variant") in t["variants"] and r["_profile_ok"] and \
                episode_config(t, r["seed"], r["variant"])["config_hash"] == r["_hash"]
            (keep if ok else not_counted).append(r)
        runs = keep
    for r in runs:
        var = tasks.get(r["task_id"], {}).get("variants", {}).get(r.get("variant"), {})
        r["_ctypes"] = sorted(set(var.get("condition_types") or [])) or ["nominal"]
    # an oracle route counts as an efficiency reference for a variant only if a run of it passed there
    verified = set()
    for r in runs:
        t = tasks.get(r["task_id"], {})
        if r.get("task_success") and not r.get("incomplete") and r.get("route") == (t.get("oracle") or {}).get(r.get("variant")) \
                and r.get("planner") in ("scripted", "oracle") and r.get("stopped_at") is None:
            verified.add((r["task_id"], r.get("variant")))
    eps = []
    for r in runs:
        t = tasks.get(r["task_id"])
        if t is None or (not a.probes and (r["task_id"].startswith("P") or t.get("kind") == "probe")):
            continue
        if r.get("planner") == "scripted":
            rt = t.get("routes", {}).get(r.get("route"))
            if rt is None or rt.get("kind") == "diagnostic" or r.get("variant") not in rt.get("variants", []):
                continue                 # superseded or diagnostic route
        eps.append((r, episode_metrics(r, t, verified)))
    spec = spec_metrics(a, eps, runs, tasks)
    groups = defaultdict(list)
    for r, m in eps:
        for ct in (r["_ctypes"] if "ctype" in keys else [None]):
            r["_ctype"] = ct
            groups[tuple(label(r, k, tasks) for k in keys)].append((r, m))
    aggs = {g: aggregate(v) for g, v in groups.items()}
    by_planner = defaultdict(list)
    for r, m in eps:
        by_planner[(label(r, "planner", tasks),)].append((r, m))
    rel = " ".join(str(Path(x).resolve().relative_to(ROOT)) if Path(x).resolve().is_relative_to(ROOT) else x
                   for x in a.runs)
    md = ["# Planner evaluation", "",
          f"Generated by `python benchmark/evaluate.py --runs {rel} --group {a.group}`; {len(eps)} episodes"
          + (f" ({len(not_counted)} runs of another configuration not counted)" if not_counted else "") + ". "
          "Column definitions: README, *Evaluation*; N/A = no sample; (n) = denominator.", "", PLANNER_NOTE, "",
          "## By planner", ""] + table({g: aggregate(v) for g, v in by_planner.items()}, ["planner"]) + [
          "", f"## By {', '.join(keys)}", ""] + table(aggs, keys) + [""] + spec["markdown"] + ["", "## Episodes", "",
          "| Task | Seed | Variant | Tier | Planner | Route | S | GC | Skill ok | Calls / L_ref | Gate u/g/v | Pre / exec / invalid (repeat) | Stop | Side effects |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r, m in sorted(eps, key=lambda x: (x[0]["task_id"], x[0].get("planner"), str(x[0].get("route")), x[0]["seed"])):
        md.append(f"| {r['task_id']} | {r['seed']} | {r['variant']} | {r['_scene'].get('difficulty', '?')} | "
                  f"{r.get('planner')} | {r.get('route')} | {'incomplete' if m['incomplete'] else int(m['success'])} | "
                  f"{m['gc']:.2f} | {m['skill_ok']}/{m['skill_n']} | "
                  f"{m['calls']} / {m['l_ref'] if m['l_ref'] is not None else 'N/A'} | "
                  f"{m['unseen']}/{m['ghost']}/{m['not_in_view']} | {m['pre']} / {m['exec']} / {m['invalid']} ({m['repeats']}) | "
                  f"{m['stop_reason'] or '-'} | {', '.join(m['side'])} |")
    Path(a.md).write_text("\n".join(md) + "\n")
    Path(a.json).write_text(json.dumps({
        "groups": [{"group": dict(zip(keys, g)), **agg} for g, agg in sorted(aggs.items())],
        "spec": spec["summaries"],
        "episodes": [{"task": r["task_id"], "seed": r["seed"], "variant": r["variant"],
                      "tier": r["_scene"].get("difficulty"), "planner": r.get("planner"), "route": r.get("route"),
                      "dir": r["_dir"], **m} for r, m in eps]}, indent=1))
    print("\n".join(table({g: aggregate(v) for g, v in by_planner.items()}, ["planner"])))
    facts_path = Path(a.json).with_suffix(".facts.jsonl")
    facts_path.write_text("".join(json.dumps(f, default=float) + "\n" for f in spec["facts"]))
    print("\n".join(spec["markdown"]))
    print(f"{len(eps)} episodes -> {a.md}, {a.json}, {facts_path}")


if __name__ == "__main__":
    main()
