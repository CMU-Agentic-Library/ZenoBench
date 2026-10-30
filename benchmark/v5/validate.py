"""Validation of the v5 suite: static configuration checks (no simulator) and the physical episode grid.

    python benchmark/v5/validate.py static                      # 180 variants x 10 seeds, writes STATIC.json
    python benchmark/v5/validate.py batch --seeds 10 --out benchmark/v5/batches/physics_s10.json
    $ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v5/tasks.json --batch ... --jobs 2 --out DIR
    python benchmark/v5/validate.py report --runs DIR [DIR ...] # classifies every physical episode

The two kinds of evidence are never merged:

* **static** (``STATIC.json``): what can be decided from the configuration alone, for all 1,800 episodes
  (180 formal variants x seeds 10-19): tier counts and Hard categories; a goal with known predicates over
  objects that exist in the episode; an oracle route whose every call names a known skill, known inputs and
  objects present in that seed's scene; failure specs that validate against the scene and whose triggers are
  reached by the oracle route (the injected step is the one marked to fail); overlay / event poses inside
  their support and clear of the other objects; distinct configurations within a task; the planner view
  (``public_task``) free of hidden state; v3 configurations unchanged.
* **physical** (``report``): only episodes actually simulated with the current catalog's configuration hash
  count.  Each is classified ``passed`` (route ran to its end, every expected failure failed, every declared
  failure fired and manifested, goal holds, nothing dropped), ``goal_failed``, ``route_violation`` (a step
  expected to fail succeeded), ``failure_not_triggered``, ``stopped`` (an expected-ok call failed),
  ``crash`` or ``incomplete``.  Unrun episodes are reported as unrun, never as passed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TASKS = ROOT / "benchmark/v5/tasks.json"
V3 = ROOT / "benchmark/v3/tasks.json"
SEEDS = list(range(10, 20))
TIERS = {"easy": 2, "medium": 3, "hard": 4}
HARD = {"task", "action", "mixed", "dynamic"}
REF_TYPES = {"object_ref", "container_ref", "tool_ref", "lid_ref", "entity_ref", "receptacle_ref", "support_ref",
             "place_ref", "articulated_ref", "appliance_ref", "furniture_ref", "room_ref", "button_ref"}


def load(path=TASKS):
    return json.loads(Path(path).read_text())


def formal(doc):
    for t in doc["tasks"]:
        for tier, ids in t["v5_formal"].items():
            for vid in ids:
                yield t, tier, vid


# ----------------------------------------------------------------- scene of one episode
_ANN_CACHE = {}


def episode_scene(task, seed, vid):
    from benchmark.scene import build_annotation, episode_config
    cfg = episode_config(task, seed, vid)
    key = cfg["config_hash"]
    if key not in _ANN_CACHE:
        with tempfile.TemporaryDirectory() as d:
            p = build_annotation(cfg, Path(d) / "a.json")
            _ANN_CACHE[key] = json.loads(p.read_text())
    return cfg, _ANN_CACHE[key]


def names_of(ann):
    objs = {o["name"]: o for o in ann["objects"]}
    sups = {s["name"]: s for s in ann["supports"]}
    arts = {a["name"] for a in ann["articulated"]}
    furn = {s.get("furniture") for s in ann["supports"]} | {o.get("name") for o in ann.get("obstacles", [])}
    rooms = set(ann["rooms"]) if isinstance(ann["rooms"], dict) else {r["name"] if isinstance(r, dict) else r
                                                                       for r in ann["rooms"]}
    appl = {a["name"] if isinstance(a, dict) else a for a in ann.get("appliances", [])}
    return objs, sups, arts, furn, rooms, appl


def overlap(a, b, gap=0.0):
    return a[0] < b[3] - gap and b[0] < a[3] - gap and a[1] < b[4] - gap and b[1] < a[4] - gap


def footprint_box(asset, m, sups):
    """aabb of an asset placed by ``m`` ({support|z, xy, yaw_deg}), as build_annotation computes it."""
    import math

    import numpy as np

    from benchmark.scene import overlay_pose, rz
    pos, _ = overlay_pose(asset, m, sups)
    yaw = math.radians(m.get("yaw_deg", 0.0))
    half = np.abs(rz(yaw)) @ (np.asarray(asset["size"], float) / 2)
    b = np.asarray(pos) + rz(yaw) @ np.asarray(asset["origin_to_bottom_center"])
    return [float(b[0] - half[0]), float(b[1] - half[1]), float(b[2]), float(b[0] + half[0]),
            float(b[1] + half[1]), float(b[2] + asset["size"][2])]


# ----------------------------------------------------------------- static checks
def check_variant(task, tier, vid, contracts, assets, seeds=SEEDS):
    """List of (seed or None, problem) for one formal variant."""
    from episode.catalog import difficulty_of, public_task, resolve_task
    from failure_injection.spec import FailureSpecError, category, mode, public_view_is_clean, validate
    from skill_ext.predicates import predicate_names
    preds = predicate_names()
    probs = []
    v = task["variants"][vid]
    if difficulty_of(v) != tier:
        probs.append((None, f"tier {difficulty_of(v)} != formal {tier}"))
    meta = v.get("v5") or {}
    if not meta.get("challenge"):
        probs.append((None, "no stated challenge"))
    if tier == "hard" and meta.get("hard_category") not in HARD:
        probs.append((None, f"hard category {meta.get('hard_category')!r}"))
    rt = resolve_task(task, vid)
    goal = rt.get("goal") or {}
    if not goal.get("all") and not goal.get("any"):
        probs.append((None, "empty goal"))
    if not public_view_is_clean(public_task(task, vid)):
        probs.append((None, "public task leaks hidden state"))
    rname = task["oracle"].get(vid)
    if rname not in task["routes"]:
        probs.append((None, f"no oracle route ({rname})"))
        return probs
    steps = task["routes"][rname]["steps"]
    fails = v.get("failures", [])
    # tier semantics
    n_fail_steps = sum(s.get("expect") == "fail" for s in steps)
    if tier == "easy" and (fails or n_fail_steps):
        probs.append((None, "an easy variant must not fail on purpose"))
    if tier == "medium" and not (fails or v.get("conditions")):
        probs.append((None, "a medium variant needs a condition or a failure"))
    cat = meta.get("hard_category")
    if tier == "hard":
        cats = category(fails) if fails else set()
        n_act = sum(f["kind"] in ("grasp", "slip", "placement", "ik") for f in fails)
        persistent = any(f.get("persist") for f in fails)     # cross-level: an unusable object / place
        want = {"task": lambda c: (not c and v.get("conditions")) or c == {"task"},
                "action": lambda c: ("task" in c or persistent) and n_act >= 2,
                "mixed": lambda c: "mixed" in c,
                "dynamic": lambda c: "dynamic" in c}
        if cat in want and not want[cat](cats):
            probs.append((None, f"hard category {cat} but failures give {sorted(cats)}"))
        # every Hard contains task-level replanning: a declared task-level constraint, or a v4 Hard's own condition
        if not ("task" in cats or persistent or (cat == "task" and v.get("conditions"))):
            probs.append((None, "a Hard variant without a task-level constraint"))
    # route vs failures: every action failure's nth matching call is a step marked injected + expect fail
    for f in fails:
        t = f.get("trigger")
        if not t:
            continue
        hits = [i for i, s in enumerate(steps) if s["skill"] == t["skill"]
                and all(s["args"].get(k) == x for k, x in (t.get("args") or {}).items())]
        if t.get("while_holding"):
            hits = [i for i in hits if _holding_before(steps, i) == t["while_holding"]]
        nth = int(t.get("nth", 1))
        if len(hits) < nth:
            probs.append((None, f"failure {f['id']}: the oracle route never makes call #{nth} of {t['skill']} {t.get('args')}"))
            continue
        i = hits[nth - 1]
        if mode(f) == "action" and not (steps[i].get("expect") == "fail" and steps[i].get("injected")):
            probs.append((None, f"failure {f['id']}: step {i} ({steps[i]['skill']}) is not marked injected/expect fail"))
        if mode(f) == "dynamic" and steps[i].get("expect") == "fail" and t.get("on", "success") == "success":
            probs.append((None, f"failure {f['id']}: trigger step {i} is expected to fail, the event would never fire"))
    for i, s in enumerate(steps):
        if s.get("injected") and not any(f.get("trigger", {}).get("skill") == s["skill"] for f in fails):
            probs.append((None, f"step {i} {s['skill']} marked injected but no failure attaches to it"))
    # per seed: scene names
    for seed in seeds:
        cfg, ann = episode_scene(task, seed, vid)
        objs, sups, arts, furn, rooms, appl = names_of(ann)
        known = set(objs) | set(sups) | arts | furn | rooms | appl | {"right", "left"}
        for a in goal.get("all", []) + [x for g in goal.get("any", []) for x in g]:
            p = a[0][4:] if a[0].startswith("not ") else a[0]
            if p not in preds:
                probs.append((seed, f"goal predicate {p} unknown"))
        # goal objects: in an any-group, a group may name an absent object (a legal alternative that is
        # not in this scene); every ``all`` atom's objects must exist
        for a in goal.get("all", []):
            for x in a[1:]:
                for n in (x if isinstance(x, list) else [x]):
                    if isinstance(n, str) and n not in known and not _is_literal(n):
                        probs.append((seed, f"goal atom {a[0]} names {n}, not in the episode"))
        if goal.get("any") and not any(all(all(n in known or _is_literal(n) for n in
                                                (x if isinstance(x, list) else [x]) if isinstance(n, str))
                                           for a in g for x in a[1:]) for g in goal["any"]):
            probs.append((seed, "no goal alternative is achievable with the objects of this episode"))
        for i, s in enumerate(steps):
            c = contracts.get(s["skill"])
            if c is None:
                probs.append((seed, f"step {i}: unknown skill {s['skill']}"))
                continue
            bad = set(s["args"]) - set(c["inputs"])
            if bad:
                probs.append((seed, f"step {i} {s['skill']}: unknown inputs {sorted(bad)}"))
            for k, meta_in in c["inputs"].items():
                if meta_in.get("required") and k not in s["args"]:
                    probs.append((seed, f"step {i} {s['skill']}: missing {k}"))
                x = s["args"].get(k)
                vals = x if isinstance(x, list) else [x]
                for n in vals:
                    if isinstance(n, str) and (meta_in["type"] in REF_TYPES or meta_in["type"] == "object_list") \
                            and n not in known:
                        # a step expected to fail may name an absent object on purpose (search(cup) in T04)
                        if s.get("expect") != "fail" and not (s["skill"] == "search" and k == "object"):
                            probs.append((seed, f"step {i} {s['skill']}: {k}={n} not in this episode"))
        try:
            validate(fails, vid, objects=set(objs), articulated=arts, supports=set(sups))
        except FailureSpecError as exc:
            probs.append((seed, f"failures: {exc}"))
        # geometry of the overlay and of every moved object / event landing
        boxes = {n: o["aabb"] for n, o in objs.items()}
        movers = dict(v.get("move", {}))
        movers.update({n: m for n, m in (v.get("add") or {}).items()})
        for n in movers:
            if n in objs and objs[n].get("support") in sups:
                if not _inside_support(boxes[n], sups[objs[n]["support"]]):
                    probs.append((seed, f"{n} sticks out of {objs[n]['support']} by more than its overhang allowance"))
        for f in fails:
            ev = f.get("event") or ({"type": "move_object", "object": None, "to": f.get("to")} if f.get("to") else None)
            if not ev or ev["type"] != "move_object":
                continue
            to = ev["to"]
            obj = ev.get("object") or (f.get("trigger", {}).get("args", {}) or {}).get("object")
            if obj not in objs:
                continue
            box = footprint_box(assets[objs[obj]["asset"]], to, sups)
            for m, b in boxes.items():
                if m != obj and m != ev.get("onto") and abs(b[2] - box[2]) < 0.3 and overlap(box, b, 0.003):
                    probs.append((seed, f"failure {f['id']}: {obj} would land on {m}"))
            if to.get("support") in sups and not _inside_support(box, sups[to["support"]]):
                probs.append((seed, f"failure {f['id']}: {obj} lands outside {to['support']}"))
        for gname, shift in (cfg.get("vary_applied") or {}).items():
            if gname == "start" or not any(shift[:2]):
                continue
            members = set(gname.split("+"))
            for n in members:
                if n not in objs:
                    continue
                if objs[n].get("support") in sups and not _inside_support(objs[n]["aabb"], sups[objs[n]["support"]], 0.0) \
                        and _inside_support(_unshifted(objs[n]["aabb"], shift), sups[objs[n]["support"]], 0.0):
                    probs.append((seed, f"seed shift {shift} pushes {n} over the edge of {objs[n]['support']}"))
                for m, o in objs.items():
                    if m not in members and abs(o["aabb"][2] - objs[n]["aabb"][2]) < 0.3 \
                            and overlap(objs[n]["aabb"], o["aabb"], -0.002) \
                            and not overlap(_unshifted(objs[n]["aabb"], shift), o["aabb"], -0.002):
                        probs.append((seed, f"seed shift {shift} pushes {n} into {m}"))
        x0, y0, _ = cfg.get("start") or json.loads((ROOT / cfg["base"] / "task.json").read_text())["robot_start"]
        for n, o in objs.items():
            b = o["aabb"]
            if b[2] < 0.15 and b[0] - 0.45 < x0 < b[3] + 0.45 and b[1] - 0.45 < y0 < b[4] + 0.45:
                probs.append((seed, f"robot start within 0.45 m of {n} on the floor"))
    return probs


def _unshifted(box, shift):
    return [box[0] - shift[0], box[1] - shift[1], box[2], box[3] - shift[0], box[4] - shift[1], box[5]]


def _is_literal(n):
    try:
        float(n)
        return True
    except ValueError:
        return False


def _holding_before(steps, i):
    held = None
    for s in steps[:i]:
        if s.get("expect") == "fail":
            continue
        if s["skill"] == "pick":
            held = s["args"]["object"]
        elif s["skill"] in ("place", "drop", "stack") and s["args"].get("object") == held:
            held = None
    return held


def _inside_support(box, sup, allowance=0.07):
    a = sup.get("aabb_xy")
    if not a:
        return True
    return box[0] > a[0] - allowance and box[1] > a[1] - allowance and box[3] < a[2] + allowance and \
        box[4] < a[3] + allowance


def static(doc, seeds=SEEDS):
    from benchmark.scene import episode_config
    contracts = {c["verb"]: c for c in json.loads((ROOT / "contract_library/skill_contracts.json").read_text())["contracts"]}
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    out = {"episodes": 0, "variants": 0, "problems": [], "per_task": {}, "hard_categories": {}}
    v3 = {t["task_id"]: t for t in load(V3)["tasks"]}
    for t in doc["tasks"]:
        counts = {k: len(t["v5_formal"][k]) for k in TIERS}
        if counts != TIERS:
            out["problems"].append({"task": t["task_id"], "problem": f"formal counts {counts}"})
        cats = sorted(t["variants"][v]["v5"]["hard_category"] for v in t["v5_formal"]["hard"])
        out["hard_categories"][t["task_id"]] = cats
        if set(cats) != HARD:
            out["problems"].append({"task": t["task_id"], "problem": f"hard categories {cats}"})
        hashes = defaultdict(list)
        for tier, ids in t["v5_formal"].items():
            for vid in ids:
                hashes[episode_config(t, 10, vid)["config_hash"]].append(vid)
        for h, vs in hashes.items():
            if len(vs) > 1:
                out["problems"].append({"task": t["task_id"], "problem": f"same configuration {h}: {vs}"})
        # v3 variants keep their configuration exactly
        for vid, v in v3[t["task_id"]]["variants"].items():
            if t["variants"][vid].get("v5", {}).get("seed_vary_added"):
                continue                        # v5 adds seeded object variation; v3 keeps the original
            for seed in seeds:
                if episode_config(v3[t["task_id"]], seed, vid)["config_hash"] != episode_config(t, seed, vid)["config_hash"]:
                    out["problems"].append({"task": t["task_id"], "variant": vid, "seed": seed,
                                            "problem": "v3 configuration changed"})
        n_ok = 0
        for tier, ids in t["v5_formal"].items():
            for vid in ids:
                out["variants"] += 1
                probs = check_variant(t, tier, vid, contracts, assets, seeds)
                out["episodes"] += len(seeds)
                bad_seeds = {s for s, _ in probs}
                if not probs:
                    n_ok += len(seeds)
                else:
                    n_ok += 0 if None in bad_seeds else len(seeds) - len(bad_seeds)
                for s, p in probs:
                    out["problems"].append({"task": t["task_id"], "variant": vid, "seed": s, "problem": p})
        out["per_task"][t["task_id"]] = {"episodes": len(seeds) * 9, "static_ok": n_ok}
        for vid in t.get("v5_study", []):                    # failure-timing study: checked, counted apart
            out["study_episodes"] = out.get("study_episodes", 0) + len(seeds)
            for sd, p in check_variant(t, "medium", vid, contracts, assets, seeds):
                out["problems"].append({"task": t["task_id"], "variant": vid, "seed": sd, "problem": p, "study": True})
    out["static_ok"] = sum(x["static_ok"] for x in out["per_task"].values())
    return out


# ----------------------------------------------------------------- physical grid
def make_batch(doc, seeds, variants=None):
    jobs = []
    for t, tier, vid in formal(doc):
        if variants and f"{t['task_id']}/{vid}" not in variants and vid not in variants:
            continue
        for s in seeds:
            jobs.append({"task": t["task_id"], "seed": s, "variant": vid, "route": t["oracle"][vid],
                         "tier": tier})
    return jobs


def route_sha1(steps) -> str:
    return hashlib.sha1(json.dumps(steps, sort_keys=True).encode()).hexdigest()[:12]


def classify(res: dict) -> str:
    if res.get("crash"):
        return "crash"
    if res.get("incomplete"):
        return "incomplete"
    if res.get("route_violations"):
        return "route_violation"
    if "stopped_at" in res:
        return "stopped"                        # an expected-ok call failed (later triggers never reached)
    fi = res.get("failure_injection")
    if fi:
        not_manifest = [r["id"] for r in fi["log"] if not r["manifested"]]
        if fi["not_fired"] or not_manifest:
            return "failure_not_triggered"
    if not res.get("task_success"):
        return "goal_failed"
    return "passed"


def report(doc, runs, seeds=SEEDS):
    from benchmark.scene import episode_config
    want = {}
    for t, tier, vid in formal(doc):
        for s in seeds:
            cfg = episode_config(t, s, vid)
            want[(t["task_id"], vid, s)] = {"tier": tier, "hash": cfg["config_hash"],
                                            "route_sha1": route_sha1(t["routes"][t["oracle"][vid]]["steps"]),
                                            "hard_category": t["variants"][vid]["v5"].get("hard_category"),
                                            "route": t["oracle"][vid]}
    got = {}
    stale = 0
    for d in runs:
        for f in sorted(Path(d).glob("*/*/result.json")):
            try:
                r = json.loads(f.read_text())
            except ValueError:
                continue
            key = (r.get("task_id"), r.get("variant"), r.get("seed"))
            if key not in want or r.get("route") != want[key]["route"]:
                continue
            if r.get("route_sha1") != want[key]["route_sha1"]:
                stale += 1                      # run with another version of the route (or before it was recorded)
                continue
            if r.get("config_hash") != want[key]["hash"]:
                stale += 1
                continue
            got[key] = {"status": classify(r), "file": str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f),
                        "stopped_at": r.get("stopped_at"), "wall_s": r.get("wall_s"),
                        "failed_goal": [g["atom"] for g in (r.get("goal") or {}).get("all", []) if not g["holds"]],
                        "failure_injection": {k: (r.get("failure_injection") or {}).get(k)
                                              for k in ("fired", "manifested", "not_fired")},
                        "stop_call": _stop_call(r)}
    rows = []
    for key, w in want.items():
        g = got.get(key)
        rows.append({"task": key[0], "variant": key[1], "seed": key[2], **w,
                     "status": g["status"] if g else "unrun", **({k: v for k, v in g.items() if k != "status"} if g else {})})
    by = Counter(r["status"] for r in rows)
    out = {"episodes_declared": len(rows), "episodes_run": sum(r["status"] != "unrun" for r in rows),
           "stale_ignored": stale, "status": dict(by), "rows": rows}
    for key in ("tier", "hard_category", "task"):
        agg = defaultdict(Counter)
        for r in rows:
            agg[str(r.get(key))][r["status"]] += 1
        out[f"by_{key}"] = {k: dict(v) for k, v in sorted(agg.items())}
    var = defaultdict(Counter)
    for r in rows:
        var[(r["task"], r["variant"])][r["status"]] += 1
    out["variants"] = {f"{k[0]}/{k[1]}": dict(v) for k, v in sorted(var.items())}
    return out


STATUSES = ("passed", "goal_failed", "stopped", "route_violation", "failure_not_triggered", "crash", "incomplete",
            "unrun")


def _table(title, agg):
    lines = [f"| {title} | " + " | ".join(STATUSES) + " | run | passed / run |", "|---" * (len(STATUSES) + 3) + "|"]
    for k, c in agg.items():
        run = sum(v for s, v in c.items() if s != "unrun")
        lines.append(f"| {k} | " + " | ".join(str(c.get(s, 0)) for s in STATUSES) +
                     f" | {run} | {c.get('passed', 0)}/{run} |")
    return "\n".join(lines)


def markdown(out, static_doc, runs):
    """VALIDATION.md: static and physical evidence side by side, never merged."""
    rows = out["rows"]
    run = out["episodes_run"]
    passed = out["status"].get("passed", 0)
    md = ["# ZenoBench v5 validation", "",
          "Generated by `python benchmark/v5/validate.py report --runs " + " ".join(map(str, runs)) + "`.",
          f"Catalog sha1 `{out.get('tasks_sha1', '')[:12]}`. Only episodes whose configuration hash and route match "
          "the current catalog count; others are ignored (" + str(out["stale_ignored"]) + " stale results).", "",
          "## Static configuration checks (no simulator)", ""]
    if static_doc:
        md += [f"* {static_doc['variants']} formal variants, {static_doc['episodes']} episodes (seeds 10-19).",
               f"* **{static_doc['static_ok']} / {static_doc['episodes']}** episodes pass every static check; "
               f"{len(static_doc['problems'])} problems listed in `STATIC.json`.",
               "* Checks: tier counts and Hard categories, goal predicates and objects, oracle route inputs and objects "
               "per seed, failure specs against the scene, triggers reached by the oracle route, overlay / event "
               "landing poses, distinct configurations, planner view free of hidden state, v3 hashes unchanged.", ""]
    md += ["## Physical simulation (Isaac Sim, profile `benchmark`, scripted oracle route per variant)", "",
           f"* Declared: {out['episodes_declared']} episodes. **Run: {run}. Passed: {passed}"
           + (f" ({100 * passed / run:.1f} % of run)" if run else "") + f". Unrun: {out['status'].get('unrun', 0)}.**",
           "* `passed` = route ran to its end, every expected failure failed, every declared failure fired and "
           "manifested, GT goal holds, nothing dropped. A static pass is never counted here.", "",
           "### By tier", "", _table("tier", out["by_tier"]), "",
           "### By Hard category", "", _table("hard category", {k: v for k, v in out["by_hard_category"].items()
                                                              if k != "None"}), "",
           "### By task", "", _table("task", out["by_task"]), "", "### Per variant", "",
           "| task / variant | " + " | ".join(STATUSES) + " |", "|---" * (len(STATUSES) + 1) + "|"]
    for k, c in out["variants"].items():
        md.append(f"| {k} | " + " | ".join(str(c.get(s, 0)) for s in STATUSES) + " |")
    bad = [r for r in rows if r["status"] not in ("passed", "unrun")]
    md += ["", f"### Episodes not passed ({len(bad)})", "", "| task | variant | seed | status | where it stopped / why |",
           "|---|---|---|---|---|"]
    for r in sorted(bad, key=lambda r: (r["task"], r["variant"], r["seed"])):
        why = r.get("stop_call") or ", ".join(r.get("failed_goal") or [])
        fi = r.get("failure_injection") or {}
        if r["status"] == "failure_not_triggered":
            why = f"not fired {fi.get('not_fired')}, fired {fi.get('fired')}, manifested {fi.get('manifested')}; " + (why or "")
        md.append(f"| {r['task']} | {r['variant']} | {r['seed']} | {r['status']} | {(why or '').replace('|', '/')[:220]} |")
    return "\n".join(md) + "\n"


def _stop_call(r):
    i = r.get("stopped_at")
    calls = r.get("calls") or []
    bad = [c for c in calls if not c["feedback"]["success"] and c.get("expect") != "fail"]
    c = bad[-1] if bad else None
    return f"{c['skill']}: {c['feedback'].get('error_code')}: {(c['feedback'].get('error') or '')[:160]}" if c else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("static")
    s.add_argument("--out", default=str(ROOT / "benchmark/v5/STATIC.json"))
    b = sub.add_parser("batch")
    b.add_argument("--seeds", default="10-19")
    b.add_argument("--variants", nargs="*")
    b.add_argument("--out", required=True)
    r = sub.add_parser("report")
    r.add_argument("--runs", nargs="+", required=True)
    r.add_argument("--seeds", default="10-19")
    r.add_argument("--out", default=str(ROOT / "benchmark/v5/PHYSICS.json"))
    r.add_argument("--md", default=str(ROOT / "benchmark/v5/VALIDATION.md"))
    a = ap.parse_args()
    doc = load()

    def seeds(x):
        lo, _, hi = x.partition("-")
        return list(range(int(lo), int(hi or lo) + 1))

    if a.cmd == "static":
        out = static(doc)
        out["tasks_sha1"] = hashlib.sha1(TASKS.read_bytes()).hexdigest()
        Path(a.out).write_text(json.dumps(out, indent=1))
        print(f"study: {out.get('study_episodes', 0)} episodes (failure timing, not formal)")
        print(f"static: {out['variants']} variants, {out['episodes']} episodes, {out['static_ok']} statically ok, "
              f"{len(out['problems'])} problems")
        for p in out["problems"][:80]:
            print("  ", p)
        return 1 if out["problems"] else 0
    if a.cmd == "batch":
        jobs = make_batch(doc, seeds(a.seeds), a.variants)
        Path(a.out).write_text(json.dumps(jobs, indent=0))
        print(f"{len(jobs)} episodes -> {a.out}")
        return 0
    out = report(doc, a.runs, seeds(a.seeds))
    out["tasks_sha1"] = hashlib.sha1(TASKS.read_bytes()).hexdigest()
    Path(a.out).write_text(json.dumps(out, indent=1))
    static_path = ROOT / "benchmark/v5/STATIC.json"
    st = json.loads(static_path.read_text()) if static_path.exists() else None
    Path(a.md).write_text(markdown(out, st, a.runs))
    print(json.dumps({k: out[k] for k in ("episodes_declared", "episodes_run", "stale_ignored", "status")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
