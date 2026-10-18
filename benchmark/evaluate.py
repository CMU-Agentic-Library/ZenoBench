"""Planner-level evaluation of benchmark runs (offline, from result.json).

    python benchmark/evaluate.py --runs benchmark/runs/final            # -> benchmark/EVALUATION.md, metrics.json
    python benchmark/evaluate.py --runs DIR --group planner,tier        # other groupings: task, route, kind, variant

report.py answers "did each declared route run and which SkillNodes did it
cover"; this script scores how a planner behaved.  Metrics (README,
*Evaluation*):

  SR       task success (GT goal holds, nothing dropped, no route violation)
  GC       goal-condition score: fraction of goal atoms that hold (best ``any`` group)
  pass^k   per task: share of tasks whose every seed in the group passed
  SPL-c    call efficiency, mean of S * L_ref / max(L, L_ref); L_ref = oracle calls for the variant
  sim_s    simulated seconds (120 ticks per s) per episode
  ground   gate refusals per episode: unseen (exists, not observed yet), ghost (not in
           this episode), not_in_view; invalid = BAD_CALL / unknown arguments
  phys     physical failures (PRECONDITION_FAILED / POLICY_FAILED) per episode
  recov    of episodes with >= 1 physical failure, the share that still succeeded
  repeat   share of physical failures followed by the same call with the same arguments
  drops    episodes with a task object on the floor
  side     non-goal watched objects moved > 5 cm (informational: some routes move them on purpose)
  budget   closed-loop episodes that hit max_calls
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICK_HZ = 120.0
GROUNDING = {"NOT_OBSERVED", "NOT_IN_VIEW", "NOT_FOUND"}
PHYSICAL = {"PRECONDITION_FAILED", "POLICY_FAILED"}
SIDE_EFFECT_M = 0.05


def load(root):
    for f in sorted(Path(root).glob("*/*/result.json")):
        r = json.loads(f.read_text())
        d = f.parent
        cfg = json.loads((d / "config.json").read_text()) if (d / "config.json").exists() else {}
        ann = json.loads((d / "annotation.json").read_text()) if (d / "annotation.json").exists() else {}
        r["_dir"] = str(d)
        r["_scene"] = cfg.get("scene", {})
        r["_objects"] = {o["name"] for o in ann.get("objects", [])}
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


def episode_metrics(r, task):
    calls = r.get("calls", [])
    fbs = [c["feedback"] for c in calls]
    m = {"incomplete": bool(r.get("incomplete") or r.get("crash"))}
    m["success"] = bool(r.get("task_success")) and not m["incomplete"]
    if r.get("planner") == "scripted" and r.get("stopped_at") is not None:
        m["success"] = False            # the declared chain did not run to its end
    m["gc"] = goal_score(r.get("goal", {})) if r.get("goal") else 0.0
    m["calls"] = len(calls)
    L = ref_len(task, r.get("variant"))
    m["l_ref"] = L
    m["spl"] = (float(m["success"]) * L / max(m["calls"], L)) if L and m["calls"] else None
    ticks = r.get("sim_ticks") or max((c.get("tick") or 0 for c in calls), default=0)
    m["sim_s"] = ticks / TICK_HZ
    m["wall_s"] = r.get("wall_s")
    g = defaultdict(int)
    phys = repeats = 0
    for i, fb in enumerate(fbs):
        code = fb.get("error_code")
        if fb.get("success") or code is None:
            continue
        if code in GROUNDING:
            name = re.findall(r"'([^']+)'", fb.get("error") or "")
            name = name[0] if name else None
            if code == "NOT_IN_VIEW":
                g["not_in_view"] += 1
            elif name is not None and r["_objects"] and name not in r["_objects"] and name in r["_scene"].get("remove", []) + list(task.get("watch", [])):
                g["ghost"] += 1          # an object this episode does not contain
            else:
                g["unseen"] += 1
        elif code in PHYSICAL:
            phys += 1
            if i + 1 < len(calls) and calls[i + 1]["skill"] == calls[i]["skill"] and calls[i + 1]["args"] == calls[i]["args"]:
                repeats += 1
        else:
            g["invalid"] += 1
    m.update(unseen=g["unseen"], ghost=g["ghost"], not_in_view=g["not_in_view"], invalid=g["invalid"],
             phys=phys, repeats=repeats, dropped=bool(r.get("dropped")))
    # side effects: non-goal watched objects displaced from where the episode started
    final = r.get("final_state") or (calls[-1].get("state") if calls and calls[-1].get("state") else {})
    keep = goal_objects(task)
    side = []
    for n, p0 in (r.get("initial_positions") or {}).items():
        p1 = (final.get(n) or {}).get("pos")
        if n in keep or p1 is None:
            continue
        if sum((a - b) ** 2 for a, b in zip(p0, p1)) ** 0.5 > SIDE_EFFECT_M:
            side.append(n)
    m["side"] = side
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
    raise ValueError(key)


def aggregate(eps):
    n = len(eps)
    mean = lambda xs: (sum(xs) / len(xs)) if xs else None
    by_task = defaultdict(list)
    for r, m in eps:
        by_task[r["task_id"]].append(m["success"])
    failed = [m for _, m in eps if m["phys"]]
    phys = sum(m["phys"] for _, m in eps)
    return {
        "n": n, "incomplete": sum(m["incomplete"] for _, m in eps),
        "SR": mean([m["success"] for _, m in eps]),
        "GC": mean([m["gc"] for _, m in eps]),
        "pass^k": mean([all(v) for v in by_task.values()]), "tasks": len(by_task),
        "SPL-c": mean([m["spl"] for _, m in eps if m["spl"] is not None]),
        "calls": mean([m["calls"] for _, m in eps]),
        "sim_s": mean([m["sim_s"] for _, m in eps]),
        "unseen": mean([m["unseen"] for _, m in eps]), "ghost": mean([m["ghost"] for _, m in eps]),
        "not_in_view": mean([m["not_in_view"] for _, m in eps]), "invalid": mean([m["invalid"] for _, m in eps]),
        "phys": mean([m["phys"] for _, m in eps]),
        "recov": mean([m["success"] for m in failed]), "recov_n": len(failed),
        "repeat": (sum(m["repeats"] for _, m in eps) / phys) if phys else None,
        "drops": sum(m["dropped"] for _, m in eps),
        "side": mean([len(m["side"]) for _, m in eps]),
        "budget": sum(m["budget"] for _, m in eps),
    }


def fmt(v, pct=False):
    if v is None:
        return "-"
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    return f"{100 * v:.0f}%" if pct else f"{v:.2f}"


COLS = [("n", 0), ("SR", 1), ("GC", 1), ("pass^k", 1), ("SPL-c", 0), ("calls", 0), ("sim_s", 0), ("unseen", 0),
        ("ghost", 0), ("not_in_view", 0), ("invalid", 0), ("phys", 0), ("recov", 1), ("repeat", 1), ("drops", 0),
        ("side", 0), ("budget", 0)]


def table(groups, keys):
    head = "| " + " | ".join(keys) + " | " + " | ".join(c for c, _ in COLS) + " |"
    lines = [head, "|" + "---|" * (len(keys) + len(COLS))]
    for g, agg in sorted(groups.items()):
        cells = [fmt(agg[c], pct) for c, pct in COLS]
        cells[COLS.index(("recov", 1))] += f" ({agg['recov_n']})" if agg["recov_n"] else ""
        lines.append("| " + " | ".join(g) + " | " + " | ".join(cells) + " |")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default=str(ROOT / "benchmark/runs/final"))
    ap.add_argument("--tasks", default=str(ROOT / "benchmark/tasks.json"))
    ap.add_argument("--group", default="planner,tier", help="comma list of planner,tier,task,route,kind,variant")
    ap.add_argument("--probes", action="store_true", help="include the P* probes (default: tasks T* only)")
    ap.add_argument("--md", default=str(ROOT / "benchmark/EVALUATION.md"))
    ap.add_argument("--json", default=str(ROOT / "benchmark/metrics.json"))
    a = ap.parse_args()
    tasks = {t["task_id"]: t for t in json.loads(Path(a.tasks).read_text())["tasks"]}
    keys = a.group.split(",")
    eps = []
    for r in load(a.runs):
        t = tasks.get(r["task_id"])
        if t is None or (not a.probes and not r["task_id"].startswith("T")):
            continue
        if r.get("planner") == "scripted":
            rt = t.get("routes", {}).get(r.get("route"))
            if rt is None or rt.get("kind") == "diagnostic" or r.get("variant") not in rt.get("variants", []):
                continue                 # superseded or diagnostic route
        eps.append((r, episode_metrics(r, t)))
    groups = defaultdict(list)
    for r, m in eps:
        groups[tuple(label(r, k, tasks) for k in keys)].append((r, m))
    aggs = {g: aggregate(v) for g, v in groups.items()}
    by_planner = defaultdict(list)
    for r, m in eps:
        by_planner[(label(r, "planner", tasks),)].append((r, m))
    rel = Path(a.runs).resolve()
    rel = rel.relative_to(ROOT) if rel.is_relative_to(ROOT) else rel
    md = ["# Planner evaluation", "",
          f"Generated by `python benchmark/evaluate.py --runs {rel} --group {a.group}`; {len(eps)} episodes. "
          "Column definitions: README, *Evaluation*.  `scripted` rows replay declared routes (their expected "
          "failures are by design); `fixed` / `retry` / `oracle` / `recovery` are planners.", "",
          "## By planner", ""] + table({g: aggregate(v) for g, v in by_planner.items()}, ["planner"]) + [
          "", f"## By {', '.join(keys)}", ""] + table(aggs, keys) + ["", "## Episodes", "",
          "| Task | Seed | Variant | Tier | Planner | Route | S | GC | Calls / L_ref | Refusals u/g/v/i | Phys (repeat) | Side effects |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r, m in sorted(eps, key=lambda x: (x[0]["task_id"], x[0].get("planner"), str(x[0].get("route")), x[0]["seed"])):
        md.append(f"| {r['task_id']} | {r['seed']} | {r['variant']} | {r['_scene'].get('difficulty', '?')} | "
                  f"{r.get('planner')} | {r.get('route')} | {int(m['success'])} | {m['gc']:.2f} | "
                  f"{m['calls']} / {m['l_ref'] if m['l_ref'] is not None else '-'} | "
                  f"{m['unseen']}/{m['ghost']}/{m['not_in_view']}/{m['invalid']} | {m['phys']} ({m['repeats']}) | "
                  f"{', '.join(m['side'])} |")
    Path(a.md).write_text("\n".join(md) + "\n")
    Path(a.json).write_text(json.dumps({
        "groups": [{"group": dict(zip(keys, g)), **agg} for g, agg in sorted(aggs.items())],
        "episodes": [{"task": r["task_id"], "seed": r["seed"], "variant": r["variant"],
                      "tier": r["_scene"].get("difficulty"), "planner": r.get("planner"), "route": r.get("route"),
                      "dir": r["_dir"], **m} for r, m in eps]}, indent=1))
    print("\n".join(table({g: aggregate(v) for g, v in by_planner.items()}, ["planner"])))
    print(f"{len(eps)} episodes -> {a.md}, {a.json}")


if __name__ == "__main__":
    main()
