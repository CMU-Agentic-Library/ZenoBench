"""Two evaluation tracks over the v6 variants: Action-Level and Task-Level.

* **Action-Level** (``action``): recovering from transient action failures (grasp miss, slip, placement
  miss, IK refusal) with local repairs (retry, re-approach, expose / separate, re-grasp), and from scene
  conditions that block one action until a local repair of the same object (a flat book pushed over the edge,
  a crowded block pulled apart: several policies, but the same call follows).  Physical skills,
  observation-limited profile, no GT state; the recovery is the scripted route of the variant (planner
  ``scripted``), not a task planner.  It measures the skill layer and is owned by the skill side.
* **Task-Level** (``task``): the plan itself has to change.  GT skills (``sticky_snap/gt``: a held object
  stays in the hand, a pick / place that fails physically after its preconditions held is completed), so
  execution noise does not decide the episode; injected task-level conditions, dynamic events and persistent
  action failures still apply.  This is the track a planner is scored on.

The split reads only the variant's configuration (``content``):

* action content - a transient action failure, or a local-repair condition (``LOCAL_CONDITIONS``);
* task content - any other failure (a task-level failure, a dynamic event, an action failure no retry fixes),
  any other scene condition, or a goal that differs from the task's.

A variant goes to the tracks its layouts have content for.  With both, the full variant is in Action-Level and
its **task projection** in Task-Level: the transient action failures are dropped and, in the route, each call
they failed together with the local repair up to its successful retry.  A projection that equals another
variant of the task is not added again (``same_as``).  A variant with neither is a control for both tracks.

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

from benchmark.v6.routes import ACTION_KINDS, trig_hits  # noqa: E402

TRACKS = {
    "action": {
        "title": "Action-Level",
        "planner": "scripted",
        "profile": "benchmark",
        "measures": "local recovery from transient action failures and blocked actions (retry, re-approach, "
                    "expose / separate, re-grasp, then the same call) with physical skills and limited observation",
        "owner": "skill layer (scripted recovery routes); not scored for task planners",
    },
    "task": {
        "title": "Task-Level",
        "planner": "any task planner (fixed, retry, VLM, ours); oracle route for validation",
        "profile": "sticky_snap/gt",
        "measures": "task-level replanning when a failure, an event or the scene makes the nominal plan "
                    "wrong, on GT skills, so execution noise does not decide the episode",
        "owner": "task planners",
    },
}
META = ("note", "v5", "v6", "since", "decisions", "vary", "move")

# Action-Level subcategories: the failure mechanism the episode recovers from.
SUBCATEGORIES = {
    "AL-IK": "IK / reach refusal: re-approach or change the base pose, then retry",
    "AL-GRASP": "grasp miss or a blocked grasp: retry, or expose / separate the object first, then pick it",
    "AL-SLIP": "the object slips while carried: pick it up again and continue",
    "AL-PLACE": "placement miss: pick the object up and place it again",
    "AL-COMPOUND": "two or more of these mechanisms in one episode",
}
ACTION_SUB = {"ik": "AL-IK", "grasp": "AL-GRASP", "slip": "AL-SLIP", "placement": "AL-PLACE"}
# scene conditions that block one action until a local repair of the same object, after which the same call
# succeeds (pick! -> expose / separate -> pick): several policies, one action, so Action-Level.  Condition ->
# mechanism (the conditions of type grasp_blocked in the registry).
LOCAL_CONDITIONS = {"no_overhang": "grasp", "crowded": "grasp"}


def transient(f):
    return f["kind"] in ACTION_KINDS and not f.get("persist")


def local_conditions(v):
    return [c for c in v.get("conditions") or [] if c in LOCAL_CONDITIONS]


def content(task, vid):
    """``(task_level, action_level)`` of one variant, from its configuration."""
    v = task["variants"][vid]
    fs = v.get("failures") or []
    act = any(transient(f) for f in fs) or bool(local_conditions(v))
    tl = (any(not transient(f) for f in fs) or any(c not in LOCAL_CONDITIONS for c in v.get("conditions") or [])
          or v.get("goal", task["goal"]) != task["goal"])
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
    kinds = sorted({f["kind"] for v in cases for f in task["variants"][v].get("failures") or [] if transient(f)}
                   | {LOCAL_CONDITIONS[c] for v in cases for c in local_conditions(task["variants"][v])})
    return ("AL-COMPOUND" if len(kinds) > 1 else ACTION_SUB[kinds[0]]), kinds


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
    p["track_projection"] = {"of": vid, "dropped": [f["id"] for f in drop]}
    steps = project_route(task["routes"][task["oracle"][vid]]["steps"], drop)
    return p, steps


def apply_tracks(doc):
    """Adds the task projections (variants ``<vid>__tl``, routes ``tl_<vid>``) and per task ``v6_tracks``;
    doc-level ``tracks`` holds the track settings."""
    doc["tracks"] = copy.deepcopy(TRACKS)
    doc["tracks"]["action"]["subcategories"] = SUBCATEGORIES
    for t in doc["tasks"]:
        sigs = {}
        for vid in t["variants"]:
            sigs.setdefault(_sig(t["variants"][vid]), vid)
        tracks = {"action": {}, "task": {}, "controls": []}
        for fam, info in t["v6_variants"].items():
            kinds = [content(t, v) for v in info["layouts"]]
            tl, act = any(k[0] for k in kinds), any(k[1] for k in kinds)
            if not tl and not act:
                tracks["controls"].append(fam)
                continue
            if act:
                sub, kinds = action_sub(t, info["layouts"])
                tracks["action"][fam] = {
                    "sub": sub, "mechanisms": kinds, "with_task_content": tl,
                    "layouts": info["layouts"], "seeds": info["seeds"],
                    "action_failures": sorted({f["id"] for v in info["layouts"]
                                               for f in t["variants"][v].get("failures") or [] if transient(f)}),
                    "local_conditions": sorted({c for v in info["layouts"] for c in local_conditions(t["variants"][v])})}
            if not tl:
                continue
            cmap, same = {}, {}
            for v in info["layouts"]:
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
                cmap[v] = pid
            cases = list(dict.fromkeys(cmap.values()))
            tracks["task"][fam] = {
                "timing": timing(t, cases), "layouts": cases,
                "seeds": {s: cmap[v] for s, v in info["seeds"].items()},
                "projected": any(cmap[v] != v for v in info["layouts"]),
                **({"same_as": same} if same else {})}
        # a projection identical to another variant's layouts is one Task-Level design: keep the unprojected one
        first = {}
        for fam in sorted(tracks["task"], key=lambda f: tracks["task"][f]["projected"]):
            key = tuple(sorted(tracks["task"][fam]["layouts"]))
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
    """TRACKS.md (definitions, counts, per-variant table) and one batch per track:
    batches/track_task_scripted.json (oracle route replayed on GT skills), batches/track_action_scripted.json."""
    out = ROOT / "benchmark/v6"
    tasks = [t["task_id"] for t in doc["tasks"]]
    md = ["# ZenoBench v6 evaluation tracks", "",
          "Generated by `python benchmark/v6/tracks.py` from `tasks.json` (`v6_tracks` per task, `tracks` at the "
          "top).  Static only: physics status per variant is in `PHYSICS_TODO.md`.", ""]
    for k in ("action", "task"):
        cfg = doc["tracks"][k]
        fams = [(t, f, x) for t in doc["tasks"] for f, x in t["v6_tracks"][k].items()]
        md += [f"## {cfg['title']} (`{k}`)", "",
               f"* Measures: {cfg['measures']}.", f"* Runs with: planner `{cfg['planner']}`, profile "
               f"`{cfg['profile']}`.", f"* Owner: {cfg['owner']}.",
               f"* {len(fams)} variants, {sum(len(x['seeds']) for _, _, x in fams)} episodes (seeds 10-19) on "
               f"{len({t['task_id'] for t, _, _ in fams})} tasks.", ""]
        if k == "action":
            md += ["| subcategory | definition | variants | tasks |", "|---|---|---|---|"]
            for sub, desc in cfg["subcategories"].items():
                rows = [t for t, _, x in fams if x["sub"] == sub]
                md.append(f"| {sub} | {desc} | {len(rows)} | {len({t['task_id'] for t in rows})} |")
            md += ["", "Variants per subcategory and task:", "",
                   "| subcategory | " + " | ".join(short(x) for x in tasks) + " |",
                   "|---|" + "---|" * len(tasks)]
            for sub in cfg["subcategories"]:
                md.append(f"| {sub} | " + " | ".join(
                    str(sum(1 for x in t["v6_tracks"][k].values() if x["sub"] == sub) or "") for t in doc["tasks"]) + " |")
            md += ["", f"* {sum(x['with_task_content'] for _, _, x in fams)} of them also have task-level content "
                   "and are in Task-Level as a projection.", ""]
        else:
            n_dyn = sum(x["timing"] == "dynamic" for _, _, x in fams)
            n_proj = sum(x["projected"] for _, _, x in fams)
            n_merged = sum(len(x.get("merged", [])) for _, _, x in fams)
            md += ["Variants per task:", "", "| " + " | ".join(short(x) for x in tasks) + " |",
                   "|" + "---|" * len(tasks),
                   "| " + " | ".join(str(len(t["v6_tracks"][k])) for t in doc["tasks"]) + " |", "",
                   f"* {n_dyn} variants have a dynamic event (the rest act on the initial scene).",
                   f"* {n_proj} variants are task projections of a variant with transient action failures "
                   f"(`<vid>__tl`, failures and their local repairs removed); {n_merged} projections "
                   "equal another variant's configuration and are merged into it (`merged`).", ""]
    md += ["## Controls", "", f"{sum(len(t['v6_tracks']['controls']) for t in doc['tasks'])} variants without a "
           "failure, condition or goal change (the nominal plan works) are the control for both tracks.", "",
           "## Variants", "", "| task | variant | track | detail | layouts |", "|---|---|---|---|---|"]
    for t in doc["tasks"]:
        tr = t["v6_tracks"]
        for f, x in tr["task"].items():
            md.append(f"| {short(t['task_id'])} | {f} | task | {x['timing']}"
                      f"{' (merged: ' + ', '.join(x['merged']) + ')' if x.get('merged') else ''} | "
                      f"{', '.join(x['layouts'])} |")
        for f, x in tr["action"].items():
            md.append(f"| {short(t['task_id'])} | {f} | action | {x['sub']} ({', '.join(x['mechanisms'])}) | "
                      f"{', '.join(x['layouts'])} |")
        for f in tr["controls"]:
            md.append(f"| {short(t['task_id'])} | {f} | control | - | {f} |")
    (out / "TRACKS.md").write_text("\n".join(md) + "\n")
    jobs = {"task": [], "action": []}
    for t in doc["tasks"]:
        for k, planner in (("task", "scripted"), ("action", "scripted")):
            for f, x in t["v6_tracks"][k].items():
                for s, v in sorted(x["seeds"].items(), key=lambda kv: int(kv[0])):
                    jobs[k].append({"task": t["task_id"], "seed": int(s), "variant": v, "route": t["oracle"][v],
                                    "planner": planner, "profile": doc["tracks"][k]["profile"], "eval_track": k,
                                    **({"sub": x["sub"]} if "sub" in x else {}), "family": f})
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
        n["task"] += len(tr["task"])
        for x in tr["action"].values():
            n[("action", x["sub"])] += 1
        n["both"] += len(set(tr["action"]) & set(tr["task"]))
    jobs = report(doc)
    for k, v in sorted(n.items(), key=str):
        print(k, v)
    print("episodes:", {k: len(v) for k, v in jobs.items()}, "-> TRACKS.md, batches/track_*.json")


if __name__ == "__main__":
    main()
