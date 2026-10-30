"""Recovery-capability audit of the v5 suite (multi-label, derived from structure, never hand-tagged).

    python benchmark/v5/capabilities.py            # writes benchmark/v5/CAPABILITIES.md and capabilities.json

Each formal variant is labelled from its oracle route compared with the task's nominal plan, its declared
failures and its goal; every label carries the evidence that produced it.

* ``AF`` Alternative / Fallback: a legal substitute (object, destination, appliance) or a local repair
  (search / explore, expose / separate / uncover / push, re-park and retry) - the plan's structure is kept.
* ``DR`` Dependency Replanning: the oracle manipulates something the nominal plan never touches and that is
  not a goal object (an obstacle moved, a door opened, a lid fetched): an inserted precondition subgoal.
* ``GD`` Goal Decomposition: the goal's objects are allocated to several receptacles, several receptacles
  are inspected, or capacities are measured to allocate them (the v4 ``decompose`` decision).
* ``SR`` Strategy Replacement: the goal is reached by another procedure: another appliance or vessel, or
  the roles of the goal objects swapped (the v4 ``replace`` decision, or a changed achieving step).
* ``CL`` Cross-Level Recovery: an action-level failure (injected or physical) whose recovery changes the
  task level (another object / receptacle / appliance, or an inserted subgoal) instead of retrying.
* ``PP`` Partial Progress Preservation: a goal subgoal is already achieved when the first failure or
  event hits, and the recovery keeps it (the object is not handled again).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CAPS = ("AF", "DR", "GD", "SR", "CL", "PP")
NAMES = {"AF": "Alternative / Fallback", "DR": "Dependency Replanning", "GD": "Goal Decomposition",
         "SR": "Strategy Replacement", "CL": "Cross-Level Recovery", "PP": "Partial Progress Preservation"}
LOCAL = {"search", "explore_room", "explore_furniture", "expose", "separate", "uncover", "push", "approach", "look"}
MANIP = {"pick", "place", "drop", "stack", "open", "close", "uncover", "cover", "collect", "wipe", "hide", "heat",
         "flip", "roll", "inspect", "expose", "separate", "push"}
ACHIEVE = {"place": "receptacle", "drop": "container", "stack": "base", "collect": "container", "heat": "appliance",
           "hide": "receptacle"}


def placed_objects(goal):
    """Objects the task's own goal asks to be put somewhere (on / inside atoms)."""
    out = set()
    for a in goal.get("all", []) + [x for g in goal.get("any", []) for x in g]:
        if a[0] in ("on", "inside", "fully_inside", "on_top_of") and isinstance(a[1], str):
            out.add(a[1])
    return out


def goal_objects(goal):
    out = set()
    for a in goal.get("all", []) + [x for g in goal.get("any", []) for x in g]:
        if a[0] in ("on", "inside", "fully_inside", "on_top_of", "upright", "flipped", "object_rolled", "hidden",
                    "temperature_at_least", "observed", "stirred", "covered", "wiped"):
            for x in a[1:2]:
                if isinstance(x, str):
                    out.add(x)
    return out


def touched(steps, skills=MANIP):
    """(skill, entity) pairs of the manipulation steps that ran (expected-ok ones)."""
    out = []
    for s in steps:
        if s["skill"] in skills:
            ent = next((s["args"][k] for k in ("object", "objects", "articulated", "container", "surface", "food",
                                                "receptacle") if s["args"].get(k)), None)
            for e in (ent if isinstance(ent, list) else [ent]):
                out.append((s["skill"], e))
    return out


def achieving(steps):
    """object -> set of receptacles / appliances its achieving steps use."""
    out = defaultdict(set)
    for s in steps:
        if s.get("expect") == "fail" or s["skill"] not in ACHIEVE:
            continue
        obj = s["args"].get("object") or s["args"].get("food") or s["args"].get("objects")
        rec = s["args"].get(ACHIEVE[s["skill"]])
        for o in (obj if isinstance(obj, list) else [obj]):
            out[o].add(rec)
    return out


def label(task, vid):
    from episode.catalog import resolve_task
    from failure_injection.spec import ACTION_KINDS, mode
    v = task["variants"][vid]
    rt = resolve_task(task, vid)
    goal = rt["goal"]
    gobj = goal_objects(goal)
    nom = task["routes"][task["nominal"]]["steps"]
    orc = task["routes"][task["oracle"][vid]]["steps"]
    fails = v.get("failures", [])
    decisions = set(v.get("decisions", [])) | set((v.get("v5") or {}).get("decisions", []))
    ev = {}
    nom_t = {e for _, e in touched(nom)}
    orc_ok = [s for s in orc if s.get("expect") != "fail"]
    # AF
    local = [s["skill"] for s in orc if s.get("role") in ("recover",) and s["skill"] in LOCAL]
    subst = sorted({e for _, e in touched(orc_ok, {"pick"})} - nom_t - set().union(*[set()]) & gobj) if gobj else []
    nom_ach, orc_ach = achieving(nom), achieving(orc)
    alt_rec = sorted({r for o, rs in orc_ach.items() for r in rs} - {r for rs in nom_ach.values() for r in rs})
    if decisions & {"explore", "alternative", "fallback"} or local or subst or any(s.get("role") == "failure" for s in orc):
        ev["AF"] = ", ".join(filter(None, [("decisions " + "/".join(sorted(decisions & {"explore", "alternative", "fallback"})))
                                          if decisions & {"explore", "alternative", "fallback"} else "",
                                          ("local steps " + "/".join(sorted(set(local)))) if local else "",
                                          ("substitute " + "/".join(subst)) if subst else ""])) or "expected failure then retry"
    # DR: entities manipulated by the oracle that the nominal plan never touches and that are not goal objects
    extra = sorted({e for k, e in touched(orc_ok) if e and e not in nom_t and e not in gobj
                    and k in ("pick", "open", "close", "uncover", "push")})
    if extra or "insert" in decisions:
        ev["DR"] = ("inserted subgoal on " + ", ".join(extra)) if extra else "v4 decision insert"
    # GD
    pobj = placed_objects(task["goal"]) | placed_objects(goal)
    alloc = lambda ach: {(o, r) for o, rs in ach.items() if o in pobj for r in rs if r}     # noqa: E731
    o_alloc = {(o, r) for o, r in alloc(orc_ach) if not r.startswith("kitchen_stove") and "heat" not in r}
    recs = {r for _, r in o_alloc}
    inspected = {s["args"].get("receptacle") for s in orc_ok if s["skill"] == "inspect"}
    measured = [s["args"]["object"] for s in orc_ok if s["skill"] == "measure"]
    multi_goal_recs = len(recs) >= 2 and len({o for o, _ in o_alloc}) >= 2 and o_alloc != alloc(nom_ach)
    if "decompose" in decisions or multi_goal_recs or len(inspected) >= 2 or (len(measured) >= 2 and len(gobj) >= 2):
        ev["GD"] = "; ".join(filter(None, ["v4 decision decompose" if "decompose" in decisions else "",
                                           "goal objects to " + "/".join(sorted(recs)) if multi_goal_recs else "",
                                           "inspects " + "/".join(sorted(inspected)) if len(inspected) >= 2 else "",
                                           "measures " + "/".join(measured) if len(measured) >= 2 else ""]))
    # SR: the achieving procedure differs from the nominal one for the same goal
    swapped = [o for o in gobj if o in nom_ach and o in orc_ach and not (orc_ach[o] & nom_ach[o])
               and any(s["skill"] in ("heat", "stack", "collect") for s in orc_ok
                       if (s["args"].get("object") or s["args"].get("food")) == o or s["args"].get("objects"))]
    roles = [s for s in orc_ok if s["skill"] == "stack"] and [s for s in nom if s["skill"] == "stack"] and \
        [s["args"]["object"] for s in orc_ok if s["skill"] == "stack"][-1] != \
        [s["args"]["object"] for s in nom if s["skill"] == "stack"][-1]
    appl = sorted({s["args"].get("appliance") for s in orc_ok if s["skill"] == "heat"} -
                  {s["args"].get("appliance") for s in nom if s["skill"] == "heat"})
    vessel = sorted({s["args"].get("container") for s in orc_ok if s["skill"] == "collect"} -
                    {s["args"].get("container") for s in nom if s["skill"] == "collect"})
    anchors = {x for a in goal.get("all", []) + [y for g in goal.get("any", []) for y in g]
               if a[0] in ("grouped", "near_any") for x in (a[1] if isinstance(a[1], list) else a[2] if isinstance(a[2], list) else [])}
    moved_anchor = sorted({e for k, e in touched(orc_ok, {"pick"})} & anchors & (placed_objects(goal) | anchors)
                          - {e for k, e in touched(nom, {"pick"})} - placed_objects(task["goal"]))
    if moved_anchor:
        roles = roles or False
    if "replace" in decisions or roles or appl or vessel or moved_anchor or (v.get("v5") or {}).get("strategy"):
        ev["SR"] = "; ".join(filter(None, ["v4 decision replace" if "replace" in decisions else "",
                                           "stack roles swapped" if roles else "",
                                           "appliance " + "/".join(map(str, appl)) if appl else "",
                                           "goal anchor relocated: " + "/".join(moved_anchor) if moved_anchor else "",
                                           (v.get("v5") or {}).get("strategy", "")]))
    # CL: an action-level failure followed by a task-level change
    first_fail = next((i for i, s in enumerate(orc) if s.get("expect") == "fail" and s["skill"] in MANIP), None)
    if first_fail is not None:
        before = orc[:first_fail]
        after = [s for s in orc[first_fail + 1:] if s.get("expect") != "fail"]
        b_rec = {r for rs in achieving(before).values() for r in rs}
        new_rec = {r for rs in achieving(after).values() for r in rs} - b_rec - {
            orc[first_fail]["args"].get(ACHIEVE.get(orc[first_fail]["skill"], "_"))}
        failed_rec = orc[first_fail]["args"].get(ACHIEVE.get(orc[first_fail]["skill"], "_"))
        failed_obj = orc[first_fail]["args"].get("object")
        new_obj = {e for k, e in touched(after, {"pick"})} - {e for k, e in touched(before, {"pick"})} - {failed_obj}
        task_change = (failed_rec and new_rec and failed_rec not in {r for rs in achieving(after).values() for r in rs}) \
            or (failed_obj and new_obj & gobj and failed_obj not in {e for k, e in touched(after, {"pick"})})
        persistent = [f for f in fails if f["kind"] in ACTION_KINDS and f.get("persist")]
        if persistent:
            f = persistent[0]
            ev["CL"] = (f"persistent {f['kind']} on {f['trigger']['skill']}({next(iter(f['trigger'].get('args', {}).values()), '')})"
                        f" -> {(v.get('v5') or {}).get('cross_level', 'a new plan')}")
        elif task_change:
            ev["CL"] = (f"{orc[first_fail]['skill']}({failed_obj or failed_rec}) fails -> uses "
                        + "/".join(sorted(map(str, (new_rec - {failed_rec}) | (new_obj & gobj)))))
    # PP: a goal subgoal achieved before the first failure / event, and kept
    trig = []
    for f in fails:
        t = f.get("trigger")
        if t and mode(f) != "initial":
            hits = [i for i, s in enumerate(orc) if s["skill"] == t["skill"]
                    and all(s["args"].get(k) == x for k, x in (t.get("args") or {}).items())]
            if len(hits) >= int(t.get("nth", 1)):
                i = hits[int(t.get("nth", 1)) - 1]
                # an event fires after its trigger call; an action failure replaces the call's outcome
                trig.append(i + 1 if mode(f) == "dynamic" else i)
    if first_fail is not None:
        trig.append(first_fail)
    if trig:
        k = min(trig)
        done = [o for o, rs in achieving(orc[:k]).items() if o in placed_objects(task["goal"])]
        rehandled = {e for _, e in touched(orc[k + 1:], {"pick"})}
        kept = [o for o in done if o not in rehandled]
        if kept:
            ev["PP"] = f"{'/'.join(kept)} achieved before the failure / event at step {k} and kept"
    return ev


def audit(doc):
    rows = []
    for t in doc["tasks"]:
        for tier, ids in t["v5_formal"].items():
            for vid in ids:
                ev = label(t, vid)
                rows.append({"task": t["task_id"], "variant": vid, "tier": tier,
                             "hard_category": (t["variants"][vid].get("v5") or {}).get("hard_category"),
                             "caps": sorted(ev), "evidence": ev})
    return rows


def matrix_md(rows):
    tasks = sorted({r["task"] for r in rows})
    out = ["| capability | variants | tasks | " + " | ".join(t[:3] for t in tasks) + " |",
           "|---|---|---|" + "---|" * len(tasks)]
    for c in CAPS:
        rs = [r for r in rows if c in r["caps"]]
        per = defaultdict(int)
        for r in rs:
            per[r["task"]] += 1
        out.append(f"| {c} {NAMES[c]} | {len(rs)} | {len(per)} | " + " | ".join(str(per.get(t, '')) for t in tasks) + " |")
    return "\n".join(out)


def failure_classes(task, vid):
    """The failure taxonomy row(s) of a variant: injected kinds (action / task, initial / dynamic) and the v3
    condition types; ``none`` for a nominal variant."""
    from failure_injection.spec import mode
    v = task["variants"][vid]
    out = set()
    for f in v.get("failures", []):
        out.add(f"{f['kind']} ({'persistent' if f.get('persist') else mode(f)})")
    for c in v.get("condition_types", []):
        out.add(f"condition: {c}")
    return sorted(out) or ["none (nominal)"]


def oracle_status(physics):
    """(task, variant) -> {"passed", "run", "declared"} from PHYSICS.json (validate.py report)."""
    st = defaultdict(lambda: {"passed": 0, "run": 0, "declared": 0})
    for r in (physics or {}).get("rows", []):
        k = (r["task"], r["variant"])
        st[k]["declared"] += 1
        if r["status"] != "unrun":
            st[k]["run"] += 1
            st[k]["passed"] += r["status"] == "passed"
    return st


def taxonomy_md(doc, rows, physics):
    st = oracle_status(physics)
    by = {(r["task"], r["variant"]): r for r in rows}
    cells = defaultdict(list)
    for t in doc["tasks"]:
        for tier, ids in t["v5_formal"].items():
            for vid in ids:
                for fc in failure_classes(t, vid):
                    for c in by[(t["task_id"], vid)]["caps"] or ["-"]:
                        cells[(fc, c)].append((t["task_id"], vid))
    fcs = sorted({k[0] for k in cells})
    out = ["| failure class | " + " | ".join(CAPS) + " |", "|---" * (len(CAPS) + 1) + "|"]
    for fc in fcs:
        row = []
        for c in CAPS:
            vs = cells.get((fc, c), [])
            if not vs:
                row.append("")
                continue
            p = sum(st[k]["passed"] for k in vs)
            r = sum(st[k]["run"] for k in vs)
            d = sum(st[k]["declared"] for k in vs)
            row.append(f"{len(vs)} v / {len({k[0] for k in vs})} t / {p}/{r} of {d}")
        out.append(f"| {fc} | " + " | ".join(row) + " |")
    return "\n".join(out)


CHANGES = """## Changes made to raise the weak capabilities (minimal, existing variants only)

Counts are variants / distinct base tasks, from this audit before and after the change (formal set).

| capability | before | after | in the Hard tier (after) | what changed |
|---|---|---|---|---|
| GD Goal Decomposition | 15 / 6 | 15 / 6 | 13 / 5 | unchanged: T03, T11, T12, T18, T19 allocate or inspect several receptacles (T02's label is a role swap) |
| SR Strategy Replacement | 11 / 3 | 14 / 4 | 12 / 4 | T07 `h_action_ik_and_slip`: the microwave start is out of reach from every park -> stove procedure; T13's boxed-in Hard relocates the goal anchor (rule now detects it) |
| CL Cross-Level Recovery | 5 / 3 | 9 / 5 | 5 / 5 | T04 / T13 `h_action_*`: the cup cannot be held at all (persistent grasp failure) -> mug; T11 `h_action_*`: the basket is out of reach from every park -> stated tray; T07 as above |
| PP Partial Progress Preservation | 8 / 4 | 13 / 5 | 9 / 5 | dynamic Hard triggers moved after a completed subgoal: T03 pin taken once the spoon is in the bin, T12 duck taken once the car is in the tray, T13 mug taken once the bowl is set, T19 cube moved once the can is in the bin |

Persistent failures (`persist: true`, grasp or IK `until: never`) are new in `failure_injection`: the same object /
place fails on every attempt, so a local retry cannot succeed and the plan must change. Each rewritten Action Hard
keeps one local action failure as well. Renamed variants: T03 `h_dynamic_pin_taken`, T13 `h_dynamic_mug_taken`,
T19 `h_dynamic_cube_moved`.

## Failure-timing study (not formal)

T09, T12, T13 and T19 get one failure type each at an early, middle and late point of the plan (`v5_study`,
`study_timing_{early,middle,late}`, progress fraction in `v5.progress`): 12 variants x 10 seeds = 120 study
episodes, reported apart. The formal suite stays 180 variants x 10 seeds = 1,800 episodes.
"""


def main():
    doc = json.loads((ROOT / "benchmark/v5/tasks.json").read_text())
    rows = audit(doc)
    (ROOT / "benchmark/v5/capabilities.json").write_text(json.dumps(rows, indent=1))
    md = ["# Recovery-capability audit (v5 formal variants)", "",
          "Generated by `python benchmark/v5/capabilities.py` from the catalog: labels are derived from each oracle "
          "route against the nominal plan, the declared failures and the goal (rules in the module docstring); "
          "multi-label. Counts are variants (tasks = distinct base tasks).", "",
          "## Capability x task", "", matrix_md(rows), "", "## By tier", ""]
    for tier in ("easy", "medium", "hard"):
        md += [f"### {tier}", "", matrix_md([r for r in rows if r["tier"] == tier]), ""]
    md += ["## Per variant", "", "| task | variant | tier | capabilities | evidence |", "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['task'][:3]} | {r['variant']} | {r['tier']} | {' '.join(r['caps']) or '-'} | "
                  + "; ".join(f"{k}: {v}" for k, v in r["evidence"].items()).replace("|", "/") + " |")
    phys_path = ROOT / "benchmark/v5/PHYSICS.json"
    physics = json.loads(phys_path.read_text()) if phys_path.exists() else None
    md[md.index("## By tier"):md.index("## By tier")] = [
        CHANGES, "## Failure taxonomy x capability", "",
        "Cell: variants / distinct tasks / oracle episodes passed / run of declared (from `PHYSICS.json`, the latest "
        "`validate.py report`; a variant appears in every row and column it belongs to).", "",
        taxonomy_md(doc, rows, physics), ""]
    (ROOT / "benchmark/v5/CAPABILITIES.md").write_text("\n".join(md) + "\n")
    print(matrix_md(rows))


if __name__ == "__main__":
    main()
