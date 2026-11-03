"""Two evaluation tracks over the v6 families: Action-Level and Task-Level.

* **Action-Level** (``action``): recovering from transient action failures (grasp miss, slip, placement
  miss, IK refusal) with local repairs (retry, re-approach, expose / separate, re-grasp).  Physical skills,
  observation-limited profile, no GT state; the recovery is the scripted route of the variant (planner
  ``scripted``), not a task planner.  It measures the skill layer and is owned by the skill side.
* **Task-Level** (``task``): replanning at the task level (DR, GD, SR, CL, PP, task-level alternatives).  GT
  skills (``sticky_snap/gt``: a held object stays in the hand, a pick / place that fails physically after its
  preconditions held is completed), so execution noise does not decide the episode; injected task-level
  conditions, dynamic events and persistent action failures still apply.  This is the track a planner is
  scored on.

A family goes to the tracks its cases call for:

* transient action failures only -> Action-Level;
* task-level content only (a core capability, a task-level alternative, a scene condition, a task-level
  failure, a persistent action failure, or a search / stated-substitute adaptation) -> Task-Level;
* both (the v5 Action / Mixed Hards, x6 families with an extra transient failure) -> both: the full variant
  in Action-Level, its **task projection** in Task-Level.  The projection drops the transient action failures
  and, in the route, each call they failed together with the local repair up to its successful retry; it is
  re-audited with the same capability checker, so its Task-Level tier is the rule's tier for what is left.
  A projection that equals another variant of the task is not added again (``same_as``);
* no challenge (Easy) -> a control in both tracks.

    python benchmark/v6/tracks.py          # summary of the split (tasks.json must be current)
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmark.v6.hypotheses import ACTION_KINDS, audit_variant, trig_hits  # noqa: E402

TRACKS = {
    "action": {
        "title": "Action-Level",
        "planner": "scripted",
        "profile": "benchmark",
        "measures": "local recovery from transient action failures (retry, re-approach, expose / separate, "
                    "re-grasp) with physical skills and limited observation",
        "owner": "skill layer (scripted recovery routes); not scored for task planners",
    },
    "task": {
        "title": "Task-Level",
        "planner": "any task planner (fixed, retry, VLM, ours); oracle route for validation",
        "profile": "sticky_snap/gt",
        "measures": "goal-preserving task-level replanning (DR, GD, SR, CL, PP, task-level alternatives) on "
                    "GT skills, so execution noise does not decide the episode",
        "owner": "task planners",
    },
}
META = ("note", "v5", "v6", "since", "decisions", "vary", "move")

# subcategories: what the episode tests.  Action-Level by the transient failure mechanism; Task-Level Hard by
# its primary core capability, Task-Level Medium by the kind of adaptation.
SUBCATEGORIES = {
    "action": {
        "AL-IK": "IK / reach refusal: re-approach or change the base pose, then retry",
        "AL-GRASP": "grasp miss: retry, or expose / separate the object first",
        "AL-SLIP": "the object slips while carried: pick it up again and continue",
        "AL-PLACE": "placement miss: pick the object up and place it again",
        "AL-COMPOUND": "two or more of these mechanisms in one episode",
    },
    "task": {
        "TL-DR": "dependency replanning: discover a missing precondition and insert the step "
                 "(open a door, move an obstacle)",
        "TL-GD": "goal decomposition: split or re-allocate the goal (capacity, several places to inspect, "
                 "several containers)",
        "TL-SR": "strategy replacement: another procedure, appliance, base or hand use reaches the same goal",
        "TL-CL": "cross-level recovery: an action failure no retry fixes, solved by changing object, "
                 "destination, appliance or procedure",
        "TL-PP": "partial-progress preservation: an event undoes or blocks part of the work; repair only that "
                 "part and keep the rest",
        "TL-SUB": "substitution (Medium): the preferred object, container, destination or tool is absent, "
                  "taken or unsuitable; use one the goal allows",
        "TL-PRE": "precondition / constraint (Medium): one enabling step or a constraint to respect (lid on, "
                  "grasp blocked, door state, destination rule, capacity)",
        "TL-SEARCH": "search (Medium): the object, tool or destination is out of view or in another room",
    },
}
CORE_ORDER = ("CL", "PP", "SR", "GD", "DR")        # the more specific capability is the primary one
SUB_COND = {
    "search_target": "TL-SEARCH", "search_tool": "TL-SEARCH",
    "object_absent": "TL-SUB", "container_choice": "TL-SUB", "cookware_choice": "TL-SUB",
    "destination_identity": "TL-SUB", "destination_occupied": "TL-SUB", "anchor_relocation": "TL-SUB",
    "grasp_blocked": "TL-PRE", "state_precondition": "TL-PRE", "destination_constraint": "TL-PRE",
    "container_capacity": "TL-PRE",
}
SUB_FAIL = {"resource": "TL-SUB", "destination": "TL-SUB", "capacity": "TL-PRE", "dependency": "TL-PRE"}
MEDIUM_ORDER = ("TL-SUB", "TL-PRE", "TL-SEARCH")
ACTION_SUB = {"ik": "AL-IK", "grasp": "AL-GRASP", "slip": "AL-SLIP", "placement": "AL-PLACE"}


def transient(f):
    return f["kind"] in ACTION_KINDS and not f.get("persist")


def content(task, vid):
    """``(task_level, action_level)`` of one variant."""
    v, a = task["variants"][vid], task["v6_audit"][vid]
    fs = v.get("failures") or []
    act = any(transient(f) for f in fs)
    tl = bool(a["core"] or (a["evidence"].get("AF") or {}).get("level") == "task" or v.get("condition_types")
              or any(not transient(f) for f in fs) or (a["tier_rule"] != "easy" and not act))
    return tl, act


def project_route(steps, drop):
    """The route without the calls the dropped failures make fail: each such call and the local repair after
    it, up to the next call of the same skill with the same arguments (its retry), which stays."""
    hit = sorted({i for f in drop for i in trig_hits(steps, f) if steps[i].get("expect") == "fail"})
    out, skip_to = [], -1
    for i, s in enumerate(steps):
        if i < skip_to:
            continue
        if i in hit:
            j = next((k for k in range(i + 1, len(steps)) if steps[k]["skill"] == s["skill"] and
                      steps[k]["args"] == s["args"] and steps[k].get("expect") != "fail"), i + 1)
            skip_to = j
            continue
        out.append(s)
    return out


def action_sub(task, cases):
    kinds = sorted({f["kind"] for v in cases for f in task["variants"][v].get("failures") or [] if transient(f)})
    return ("AL-COMPOUND" if len(kinds) > 1 else ACTION_SUB[kinds[0]]), kinds


def task_sub(task, cases, tier):
    """``(primary, all)`` subcategories of a Task-Level family from its cases."""
    if tier == "hard":
        caps = set.intersection(*[set(task["v6_audit"][v]["core"]) for v in cases])
        declared = [h["cap"] for h in (task["variants"][cases[0]].get("v6") or {}).get("hypotheses") or []
                    if h["cap"] in caps]
        primary = declared[0] if declared else next(c for c in CORE_ORDER if c in caps)
        return f"TL-{primary}", sorted(f"TL-{c}" for c in caps)
    subs = set()
    for v in cases:
        x = task["variants"][v]
        subs |= {SUB_COND[c] for c in x.get("condition_types") or [] if c in SUB_COND}
        subs |= {SUB_FAIL[f["kind"]] for f in x.get("failures") or [] if f["kind"] in SUB_FAIL}
    if not subs:                                    # a named target elsewhere, or a start far from it
        subs = {"TL-SEARCH"}
    return next(s for s in MEDIUM_ORDER if s in subs), sorted(subs)


def timing(task, cases):
    whens = {f.get("when", "initial") for v in cases for f in task["variants"][v].get("failures") or []}
    return "dynamic" if "dynamic" in whens else "initial"


def _sig(v):
    return json.dumps({k: x for k, x in v.items() if k not in META}, sort_keys=True)


def project(task, vid):
    """Task projection of a variant: ``(variant, steps)`` without its transient action failures, or None when
    it has none."""
    v = task["variants"][vid]
    drop = [f for f in v.get("failures") or [] if transient(f)]
    if not drop:
        return None
    p = copy.deepcopy(v)
    keep = [f for f in v["failures"] if not transient(f)]
    if keep:
        p["failures"] = keep
    else:
        p.pop("failures")
    if p.get("v6", {}).get("hypotheses"):
        gone = {f"failure:{f['id']}" for f in drop}
        p["v6"]["hypotheses"] = [h for h in p["v6"]["hypotheses"] if h.get("cause") not in gone] or None
        if p["v6"]["hypotheses"] is None:
            p["v6"].pop("hypotheses")
    p["track_projection"] = {"of": vid, "dropped": [f["id"] for f in drop]}
    steps = project_route(task["routes"][task["oracle"][vid]]["steps"], drop)
    return p, steps


def apply_tracks(doc):
    """Adds the task projections (variants ``<vid>__tl``, routes ``tl_<vid>``, re-audited) and per task
    ``v6_tracks``; doc-level ``tracks`` holds the track settings."""
    doc["tracks"] = {k: dict(v, subcategories=SUBCATEGORIES[k]) for k, v in TRACKS.items()}
    for t in doc["tasks"]:
        sigs = {}
        for vid in t["variants"]:
            sigs.setdefault(_sig(t["variants"][vid]), vid)
        tracks = {"action": {}, "task": {}, "controls": []}
        for fam, info in t["v6_families"].items():
            kinds = [content(t, v) for v in info["cases"]]
            tl, act = any(k[0] for k in kinds), any(k[1] for k in kinds)
            if info["tier"] == "easy" or not tl and not act:
                tracks["controls"].append(fam)
                continue
            if act:
                sub, kinds = action_sub(t, info["cases"])
                tracks["action"][fam] = {
                    "sub": sub, "mechanisms": kinds, "with_task_content": tl,
                    "cases": info["cases"], "seeds": info["seeds"], "family_tier": info["tier"],
                    "action_failures": sorted({f["id"] for v in info["cases"]
                                               for f in t["variants"][v].get("failures") or [] if transient(f)})}
            if not tl:
                continue
            cmap, same = {}, {}
            for v in info["cases"]:
                pr = project(t, v)
                if pr is None:
                    cmap[v] = v
                    continue
                p, steps = pr
                hit = sigs.get(_sig({k: x for k, x in p.items() if k != "track_projection"}))
                if hit is not None:
                    cmap[v], same[v] = hit, hit
                    continue
                pid = f"{v}__tl"
                t["variants"][pid] = p
                t["routes"][f"tl_{v}"] = {"steps": steps, "kind": "v6_task_projection", "variant": pid}
                t["oracle"][pid] = f"tl_{v}"
                t["v6_audit"][pid] = audit_variant(t, pid)
                cmap[v] = pid
            cases = list(dict.fromkeys(cmap.values()))
            tiers = Counter(t["v6_audit"][c]["tier_rule"] for c in cases)
            tier = min(tiers, key=["easy", "medium", "hard"].index)
            sub, subs = task_sub(t, cases, tier)
            tracks["task"][fam] = {
                "sub": sub, "subs": subs, "timing": timing(t, cases),
                "cases": cases, "seeds": {s: cmap[v] for s, v in info["seeds"].items()},
                "tier": tier, "family_tier": info["tier"],
                "projected": any(cmap[v] != v for v in info["cases"]),
                **({"same_as": same} if same else {}),
                **({"mixed_tiers": dict(tiers)} if len(tiers) > 1 else {})}
        # a projection identical to another family's cases is one Task-Level design: keep the unprojected one
        first = {}
        for fam in sorted(tracks["task"], key=lambda f: tracks["task"][f]["projected"]):
            key = tuple(sorted(tracks["task"][fam]["cases"]))
            if key in first:
                tracks["task"][first[key]].setdefault("merged", []).append(fam)
                tracks["task"].pop(fam)
            else:
                first[key] = fam
        t["v6_tracks"] = tracks
    return doc


def short(tid):
    return tid.split("_")[0]


def report(doc):
    """TRACKS.md (taxonomy, counts, per-family table) and one batch per track:
    batches/track_task_scripted.json (oracle route replayed on GT skills), batches/track_action_scripted.json."""
    out = ROOT / "benchmark/v6"
    tasks = [t["task_id"] for t in doc["tasks"]]
    md = ["# ZenoBench v6 evaluation tracks", "",
          "Generated by `python benchmark/v6/tracks.py` from `tasks.json` (`v6_tracks` per task, `tracks` at the "
          "top).  Two top-level categories; subcategories say what an episode tests.  Static only: physics status "
          "per family is in `PHYSICS_TODO.md`.", ""]
    for k in ("action", "task"):
        cfg = doc["tracks"][k]
        fams = [(t, f, x) for t in doc["tasks"] for f, x in t["v6_tracks"][k].items()]
        md += [f"## {cfg['title']} (`{k}`)", "",
               f"* Measures: {cfg['measures']}.", f"* Runs with: planner `{cfg['planner']}`, profile "
               f"`{cfg['profile']}`.", f"* Owner: {cfg['owner']}.",
               f"* {len(fams)} families, {sum(len(x['seeds']) for _, _, x in fams)} episodes (seeds 10-19).", ""]
        tierkey = "tier" if k == "task" else "family_tier"
        md += ["| subcategory | definition | families | Medium | Hard | tasks |", "|---|---|---|---|---|---|"]
        for sub, desc in cfg["subcategories"].items():
            rows = [(t, x) for t, _, x in fams if x["sub"] == sub]
            md.append(f"| {sub} | {desc} | {len(rows)} | {sum(x[tierkey] == 'medium' for _, x in rows)} | "
                      f"{sum(x[tierkey] == 'hard' for _, x in rows)} | {len({t['task_id'] for t, _ in rows})} |")
        md += ["", "Families per subcategory and task:", "",
               "| subcategory | " + " | ".join(short(x) for x in tasks) + " |",
               "|---|" + "---|" * len(tasks)]
        for sub in cfg["subcategories"]:
            md.append(f"| {sub} | " + " | ".join(
                str(sum(1 for f, x in t["v6_tracks"][k].items() if x["sub"] == sub) or "") for t in doc["tasks"]) + " |")
        md.append("")
        if k == "action":
            md += ["`family_tier` is the family's v6 tier, which counts its task-level content too; within this "
                   "track the episode is scored on the scripted route.", ""]
        else:
            n_dyn = sum(x["timing"] == "dynamic" for _, _, x in fams)
            n_proj = sum(x["projected"] for _, _, x in fams)
            n_merged = sum(len(x.get("merged", [])) for _, _, x in fams)
            md += [f"* {n_dyn} families have a dynamic event (the rest act on the initial scene).",
                   f"* {n_proj} families are task projections of a variant with transient action failures "
                   f"(`<vid>__tl`, failures and their local repairs removed, re-audited); {n_merged} projections "
                   "equal another family's configuration and are merged into it (`merged`).",
                   "* Every Hard family keeps its Hard tier after projection (checked by `validate_v6.py`).", ""]
    md += ["## Controls", "", f"{sum(len(t['v6_tracks']['controls']) for t in doc['tasks'])} Easy families (the "
           "nominal plan works) are the control for both tracks.", "", "## Families", "",
           "| task | family | track | subcategory | also | tier | cases |", "|---|---|---|---|---|---|---|"]
    for t in doc["tasks"]:
        tr = t["v6_tracks"]
        for f, x in tr["task"].items():
            md.append(f"| {short(t['task_id'])} | {f} | task | {x['sub']} | {', '.join(s for s in x['subs'] if s != x['sub'])}"
                      f"{' (merged: ' + ', '.join(x['merged']) + ')' if x.get('merged') else ''} | {x['tier']} | "
                      f"{', '.join(x['cases'])} |")
        for f, x in tr["action"].items():
            md.append(f"| {short(t['task_id'])} | {f} | action | {x['sub']} | {', '.join(x['mechanisms'])} | "
                      f"{x['family_tier']} | {', '.join(x['cases'])} |")
        for f in tr["controls"]:
            md.append(f"| {short(t['task_id'])} | {f} | control | - | - | easy | {f} |")
    (out / "TRACKS.md").write_text("\n".join(md) + "\n")
    jobs = {"task": [], "action": []}
    for t in doc["tasks"]:
        for k, planner in (("task", "scripted"), ("action", "scripted")):
            for f, x in t["v6_tracks"][k].items():
                for s, v in sorted(x["seeds"].items(), key=lambda kv: int(kv[0])):
                    jobs[k].append({"task": t["task_id"], "seed": int(s), "variant": v, "route": t["oracle"][v],
                                    "planner": planner, "profile": doc["tracks"][k]["profile"], "eval_track": k,
                                    "sub": x["sub"], "family": f})
    (out / "batches").mkdir(exist_ok=True)
    (out / "batches/track_task_scripted.json").write_text(json.dumps(jobs["task"], indent=0))
    (out / "batches/track_action_scripted.json").write_text(json.dumps(jobs["action"], indent=0))
    return jobs


def main():
    doc = json.loads((ROOT / "benchmark/v6/tasks.json").read_text())
    n = Counter()
    for t in doc["tasks"]:
        tr = t["v6_tracks"]
        n["controls"] += len(tr["controls"])
        for k in ("action", "task"):
            for fam, x in tr[k].items():
                n[(k, x.get("tier", x.get("family_tier")))] += 1
                n[(k, x["sub"])] += 1
        n["both"] += len(set(tr["action"]) & set(tr["task"]))
    jobs = report(doc)
    for k, v in sorted(n.items(), key=str):
        print(k, v)
    print("episodes:", {k: len(v) for k, v in jobs.items()}, "-> TRACKS.md, batches/track_*.json")


if __name__ == "__main__":
    main()
