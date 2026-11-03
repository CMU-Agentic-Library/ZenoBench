"""Per-track evaluation metrics for the v6 tracks (benchmark/v6/tracks.py).

    python benchmark/v6/track_metrics.py --runs benchmark/runs/v5_grid [--runs ...] [--md OUT.md] [--json OUT.json]

Reads every ``result.json`` under the run directories (newest per planner / task / variant / seed / profile),
assigns it to a track and computes that track's metrics, overall and per subcategory, tier and planner.
The track comes from the episode's profile: ``sticky_snap/*`` (GT skills) -> Task-Level; any other profile ->
Action-Level when the variant belongs to an Action-Level family.  Episodes outside the v6 tracks are skipped.
Rates carry a Wilson 95 % interval; a metric with nothing eligible is N/A, never 0.

**Action-Level** (scripted recovery on physical skills; the skill layer's score)

* ``ASR``   action-track success: the route ran to its end, every expected failure failed, every declared
            failure fired and manifested, the goal holds, nothing dropped (``result.success``).
* ``LRR``   local recovery rate, per injected transient failure that fired and per call a local-repair condition
            blocks (``tracks.LOCAL_CONDITIONS``, e.g. the pick of a flat book before expose): the same call
            (skill + arguments, ``hint*`` ignored) succeeds later in the episode.  Also per mechanism (IK, grasp,
            slip, placement).
* ``RC``    repair cost: calls between a recovered failure and its successful retry (mean).
* ``NSR``   nominal skill reliability: success rate of the calls that no injected failure targeted and the
            route expects to succeed (physical execution quality, independent of the injected failures).
* ``CDR``   collateral drop rate: episodes with an object dropped to the floor.
* ``FIV``   failure-injection validity: episodes whose declared transient failures all fired and manifested
            (the others do not test what they claim; reported, and excluded from LRR).

**Task-Level** (any planner on GT skills; the planner's score)

* ``TSR``   task success: the goal holds (legal substitutes included: the goal checker decides) and nothing was
            dropped.  Reported per subcategory (TL-DR ... TL-SEARCH), tier, timing (initial / dynamic).
* ``RRSR``  reactive recovery success: of the episodes in which a call failed or a dynamic event fired, the
            share that still succeed.
* ``PAR``   proactive adaptation rate: of the episodes with a declared task-level failure that never fired
            (the planner avoided the blocked step, e.g. chose the substitute or stove first), the share that
            succeed.  N/A when every declared failure fired.
* ``FRR``   futile repeat rate: episodes in which a call that failed for a persistent reason (a persistent
            failure, or a task-level condition) fails a third time with the same arguments, over the episodes
            that met such a failure.  One retry is allowed (it is how a planner learns that the failure
            persists; the reference routes do it too); lower is better.
* ``PPR``   progress preservation, TL-PP families: episodes that do not redo the work the event did not
            undo (the hypothesis' ``kept.by`` call after the event), over the PP episodes where the event fired.
* ``PE``    plan efficiency, successful episodes: oracle-route successful calls / the episode's calls (<= 1 is
            longer than the reference; capped at 1).
* ``GAP``   replanning gap per family: TSR of its control variant minus TSR of the family, same planner and
            same kind of profile (GT skills or not), when both were run; reported as the mean over families with both (paired on seeds when possible).
* ``STOP``  stop reasons of failed episodes (planner_done with the goal unmet, budget, refused ...).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmark.v6.tracks import LOCAL_CONDITIONS, local_conditions, transient  # noqa: E402

TASKS = ROOT / "benchmark/v6/tasks.json"


def wilson(num, den):
    if not den:
        return {"value": None, "num": num, "den": den, "ci95": None}
    z, p = 1.96, num / den
    c = (p + z * z / (2 * den)) / (1 + z * z / den)
    h = z * math.sqrt(p * (1 - p) / den + z * z / (4 * den * den)) / (1 + z * z / den)
    return {"value": p, "num": num, "den": den, "ci95": [max(0.0, c - h), min(1.0, c + h)]}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return {"value": sum(xs) / len(xs) if xs else None, "n": len(xs)}


def _key(c):
    return c["skill"], json.dumps({k: v for k, v in c["args"].items() if not k.startswith("hint")}, sort_keys=True)


def ok(c):
    return bool((c.get("feedback") or {}).get("success"))


def call_at(calls, e):
    """The top-level call a failure-log row belongs to: the first call ending at or after the row's tick whose
    skill is the row's verb (a refusal moves nothing, so several calls can end on the same tick; the
    injector's own counter also counts nested calls).  Without a verb match, the first call at that tick."""
    later = [c for c in calls if c.get("tick") is not None and c["tick"] >= e.get("tick", -1)]
    return next((c for c in later if c["skill"] == e.get("verb") and not ok(c)),
                next((c for c in later if not ok(c)), later[0] if later else None))


def load_results(dirs):
    """Newest result per (planner, task, variant, seed, profile)."""
    best = {}
    for d in dirs:
        for f in Path(d).rglob("result.json"):
            try:
                r = json.loads(f.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if "calls" not in r:
                continue
            k = (r.get("planner"), r["task_id"], r.get("variant"), r.get("seed"), r.get("profile"))
            if k not in best or (r.get("started") or "") >= (best[k].get("started") or ""):
                best[k] = r
    return list(best.values())


def membership(doc):
    """(task, variant) -> {track: (family, entry)}"""
    out = defaultdict(dict)
    for t in doc["tasks"]:
        for k in ("action", "task"):
            for fam, x in t["v6_tracks"][k].items():
                for v in x["cases"]:
                    out[(t["task_id"], v)][k] = (fam, x)
    return out


def track_of(r, mem):
    m = mem.get((r["task_id"], r.get("variant")), {})
    if str(r.get("profile", "")).startswith("sticky_snap"):
        return "task" if "task" in m else None
    return "action" if "action" in m else None


# ------------------------------------------------------------------ Action-Level
def action_facts(r, task):
    v = task["variants"][r["variant"]]
    fspec = {f["id"]: f for f in v.get("failures") or []}
    fi = r.get("failure_injection") or {}
    log = [e for e in fi.get("log", []) if e["id"] in fspec and transient(fspec[e["id"]])]
    want = {i for i, f in fspec.items() if transient(f)}
    valid = want <= set(fi.get("manifested", []))
    calls = r["calls"]
    events = []
    for e in log:
        c = call_at(calls, e)
        if c is None:
            continue
        later = [d for d in calls if d["index"] > c["index"] and _key(d) == _key(c) and ok(d)]
        events.append({"kind": e["kind"], "recovered": bool(later),
                       "cost": (later[0]["index"] - c["index"] - 1) if later else None})
    hit = {c["index"] for e in fi.get("log", []) for c in [call_at(calls, e)] if c}
    for cond in local_conditions(v):                # the blocked call the route expects to fail, then repairs
        for c in calls:
            if c["index"] in hit or c.get("expect") != "fail" or ok(c):
                continue
            later = [d for d in calls if d["index"] > c["index"] and _key(d) == _key(c) and ok(d)]
            events.append({"kind": LOCAL_CONDITIONS[cond], "recovered": bool(later),
                           "cost": (later[0]["index"] - c["index"] - 1) if later else None})
            hit.add(c["index"])
    nominal = [c for c in calls if c["index"] not in hit and c.get("expect", "ok") != "fail"]
    return {"success": bool(r.get("success")), "valid": valid, "events": events,
            "nominal_ok": sum(ok(c) for c in nominal), "nominal_n": len(nominal), "dropped": bool(r.get("dropped"))}


def action_summary(rows):
    ev = [e for f in rows if f["valid"] for e in f["events"]]
    out = {"n": len(rows),
           "ASR": wilson(sum(f["success"] for f in rows), len(rows)),
           "LRR": wilson(sum(e["recovered"] for e in ev), len(ev)),
           "RC": mean([e["cost"] for e in ev if e["recovered"]]),
           "NSR": wilson(sum(f["nominal_ok"] for f in rows), sum(f["nominal_n"] for f in rows)),
           "CDR": wilson(sum(f["dropped"] for f in rows), len(rows)),
           "FIV": wilson(sum(f["valid"] for f in rows), len(rows))}
    for k in ("ik", "grasp", "slip", "placement"):
        e2 = [e for e in ev if e["kind"] == k]
        out[f"LRR_{k}"] = wilson(sum(e["recovered"] for e in e2), len(e2))
    return out


# ------------------------------------------------------------------ Task-Level
def task_facts(r, task, fam, entry):
    v = task["variants"][r["variant"]]
    fspec = {f["id"]: f for f in v.get("failures") or []}
    fi = r.get("failure_injection") or {}
    fired = set(fi.get("fired", []))
    calls = r["calls"]
    success = bool(r.get("task_success", r.get("success"))) and not r.get("dropped")
    failed = [c for c in calls if not ok(c)]
    dyn_fired = any(fspec[i].get("when") == "dynamic" for i in fired if i in fspec)
    declared_task = [i for i, f in fspec.items() if not transient(f)]
    # futile repeats: a call that failed for a persistent reason, issued again and failed again
    persistent_idx = {c["index"] for e in fi.get("log", []) for c in [call_at(calls, e)]
                      if c and e["id"] in fspec and (fspec[e["id"]].get("persist") or not transient(fspec[e["id"]]))}
    persistent_keys = {_key(c) for c in calls if c["index"] in persistent_idx and not ok(c)}
    if v.get("condition_types") and failed:     # a task-level condition refuses a call: treat its refusals alike
        persistent_keys |= {_key(c) for c in failed}
    n_failed, futile = Counter(), False
    for c in calls:
        k = _key(c)
        if k in persistent_keys and not ok(c):
            n_failed[k] += 1
            futile = futile or n_failed[k] >= 3
    pp = None
    ev = (task["v6_audit"][r["variant"]]["evidence"].get("PP") or {})
    if entry["sub"] == "TL-PP" and ev.get("event") in fired:
        ev_c = next((call_at(calls, e) for e in fi.get("log", []) if e["id"] == ev["event"]), None)
        ev_idx = ev_c["index"] if ev_c else None
        by = ev.get("kept", {}).get("by") or {}
        redo = any(c["index"] > (ev_idx or -1) and ok(c) and c["skill"] == by.get("skill") and
                   all(c["args"].get(a) == b for a, b in (by.get("args") or {}).items()) for c in calls)
        pp = not redo
    ref = sum(1 for s in task["routes"][task["oracle"][r["variant"]]]["steps"] if s.get("expect") != "fail")
    return {"success": success, "fam": fam, "sub": entry["sub"], "tier": entry["tier"], "timing": entry["timing"],
            "reactive": bool(failed) or dyn_fired, "proactive": bool(declared_task) and not (set(declared_task) & fired),
            "persistent_met": bool(persistent_keys), "futile": futile, "pp": pp,
            "pe": min(1.0, ref / len(calls)) if success and calls else None,
            "stop": r.get("stop_reason") or ("success" if success else "route_end"),
            "control": task["v6_audit"][r["variant"]].get("control"), "seed": r.get("seed")}


def task_summary(rows):
    re_ = [f for f in rows if f["reactive"]]
    pa = [f for f in rows if f["proactive"]]
    pm = [f for f in rows if f["persistent_met"]]
    pp = [f for f in rows if f["pp"] is not None]
    return {"n": len(rows),
            "TSR": wilson(sum(f["success"] for f in rows), len(rows)),
            "RRSR": wilson(sum(f["success"] for f in re_), len(re_)),
            "PAR": wilson(sum(f["success"] for f in pa), len(pa)),
            "FRR": wilson(sum(f["futile"] for f in pm), len(pm)),
            "PPR": wilson(sum(f["pp"] for f in pp), len(pp)),
            "PE": mean([f["pe"] for f in rows]),
            "STOP": dict(Counter(f["stop"] for f in rows if not f["success"]))}


def gap(rows, control_rows):
    """Mean over families of TSR(control) - TSR(family), for families whose control was run too."""
    by_fam = defaultdict(list)
    for f in rows:
        by_fam[(f["task"], f["fam"], f["control"])].append(f["success"])
    ctrl = defaultdict(list)
    for f in control_rows:
        ctrl[(f["task"], f["variant"])].append(f["success"])
    ds = [sum(ctrl[(t, c)]) / len(ctrl[(t, c)]) - sum(s) / len(s) for (t, _, c), s in by_fam.items() if ctrl.get((t, c))]
    return mean(ds)


# ------------------------------------------------------------------ driver
def evaluate(dirs, doc=None):
    doc = doc or json.loads(TASKS.read_text())
    tasks = {t["task_id"]: t for t in doc["tasks"]}
    mem = membership(doc)
    controls = {(t["task_id"], f) for t in doc["tasks"] for f in t["v6_tracks"]["controls"]}
    rows = {"action": defaultdict(list), "task": defaultdict(list)}
    ctrl_rows = defaultdict(list)
    for r in load_results(dirs):
        t = tasks.get(r["task_id"])
        if t is None or r.get("variant") not in t["variants"]:
            continue
        planner = r.get("planner") or "?"
        gt_skills = str(r.get("profile", "")).startswith("sticky_snap")
        if (r["task_id"], r["variant"]) in controls:
            ctrl_rows[(planner, gt_skills)].append({"task": r["task_id"], "variant": r["variant"],
                                       "success": bool(r.get("task_success", r.get("success"))) and not r.get("dropped")})
        k = track_of(r, mem)
        if k == "action":
            fam, x = mem[(r["task_id"], r["variant"])]["action"]
            rows["action"][planner].append(dict(action_facts(r, t), task=r["task_id"], fam=fam, sub=x["sub"],
                                                tier=x["family_tier"]))
        elif k == "task":
            fam, x = mem[(r["task_id"], r["variant"])]["task"]
            rows["task"][planner].append(dict(task_facts(r, t, fam, x), task=r["task_id"], variant=r["variant"]))
    out = {"action": {}, "task": {}}
    for planner, rs in rows["action"].items():
        out["action"][planner] = {"all": action_summary(rs),
                                  "by_sub": {s: action_summary([f for f in rs if f["sub"] == s])
                                             for s in sorted({f["sub"] for f in rs})},
                                  "by_tier": {s: action_summary([f for f in rs if f["tier"] == s])
                                              for s in sorted({f["tier"] for f in rs})}}
    for planner, rs in rows["task"].items():
        out["task"][planner] = {"all": dict(task_summary(rs), GAP=gap(rs, ctrl_rows[(planner, True)])),
                                "by_sub": {s: task_summary([f for f in rs if f["sub"] == s])
                                           for s in sorted({f["sub"] for f in rs})},
                                "by_tier": {s: task_summary([f for f in rs if f["tier"] == s])
                                            for s in sorted({f["tier"] for f in rs})},
                                "by_timing": {s: task_summary([f for f in rs if f["timing"] == s])
                                              for s in sorted({f["timing"] for f in rs})}}
    return out


def _r(x):
    if x is None or x.get("value") is None:
        return "N/A"
    if "den" in x:
        return f"{100 * x['value']:.0f}% ({x['num']}/{x['den']})"
    return f"{x['value']:.2f} (n={x['n']})"


def markdown(res, dirs):
    md = ["# v6 track evaluation", "", f"`python benchmark/v6/track_metrics.py` over: {', '.join(map(str, dirs))}.",
          "Metric definitions: the module docstring of `benchmark/v6/track_metrics.py` and `TRACKS.md`.", ""]
    acols = ["ASR", "LRR", "RC", "NSR", "CDR", "FIV", "LRR_ik", "LRR_grasp", "LRR_slip", "LRR_placement"]
    tcols = ["TSR", "RRSR", "PAR", "FRR", "PPR", "PE"]
    for k, cols in (("action", acols), ("task", tcols)):
        md += [f"## {'Action' if k == 'action' else 'Task'}-Level", ""]
        if not res[k]:
            md += ["No episodes.", ""]
            continue
        for planner, s in res[k].items():
            md += [f"### planner `{planner}`", "", "| group | n | " + " | ".join(cols) + " |",
                   "|---|---|" + "---|" * len(cols)]
            groups = [("all", s["all"])] + [(g, x) for part in ("by_tier", "by_sub", "by_timing")
                                            for g, x in s.get(part, {}).items()]
            for g, x in groups:
                md.append(f"| {g} | {x['n']} | " + " | ".join(_r(x.get(c)) for c in cols) + " |")
            if k == "task":
                md += ["", f"GAP (control TSR - family TSR, mean over families with a control run): "
                       f"{_r(s['all']['GAP'])}.", f"Stop reasons of failed episodes: {s['all']['STOP'] or '-'}."]
            md.append("")
    return "\n".join(md) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", action="append", required=True)
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = evaluate(a.runs)
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
    text = markdown(res, a.runs)
    if a.md:
        Path(a.md).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
