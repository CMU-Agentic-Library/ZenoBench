"""Static validation of the v6 suite (no simulator).

    python benchmark/v6/validate_v6.py            # writes benchmark/v6/STATIC.json, exit 1 on any problem

Checks, per variant and per episode of its seed manifest (seed -> concrete variant):

* **v5 preserved** - every v5 formal variant keeps the configuration hash FREEZE.json records for each seed;
* **configuration / route / failures / geometry** - benchmark.v5.validate.check_variant on the episode's
  concrete variant and seed (goal predicates and objects present, every route call a known skill with known
  inputs and objects, failure specs valid against the scene and reached by the route, overlay and event poses
  inside their support and clear of other objects, planner view free of hidden state; v5's tier labels are not
  checked); v5 variants were checked by the v5 validator and are re-checked here only for hashes;
* **persistent failures** - every matching call the route makes while a persistent failure holds is marked to
  fail, every later one (``until_moved``: after the obstruction is moved) succeeds or is absent;
* **seed manifest** - deterministic (recomputed), balanced, every case exercised;
* **decision diversity** - the layouts of a multi-layout variant differ in their oracle route;
* **distinct configurations** - no two variants of a task share a configuration at seed 10;
* **spec card** - every new variant names its challenge, rationale and control;
* **tracks** - every variant is in exactly the tracks its content calls for (``tracks.py``).
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
TASKS = ROOT / "benchmark/v6/tasks.json"
SEEDS = list(range(10, 20))
OUT = ROOT / "benchmark/v6/STATIC.json"


def route_sig(steps):
    return hashlib.sha1(json.dumps([[s["skill"], s["args"], s.get("expect")] for s in steps], sort_keys=True).encode()).hexdigest()[:12]


def persistent_problems(task, vid):
    from benchmark.v6.routes import MANIP, ok, trig_hits, vals
    v = task["variants"][vid]
    steps = task["routes"][task["oracle"][vid]]["steps"]
    out = []
    for f in v.get("failures", []):
        if not f.get("persist"):
            continue
        hits = trig_hits(steps, f)
        if f.get("until_moved"):
            moved = next((i for i, s in enumerate(steps) if ok(s) and s["skill"] in MANIP - {"pick"} and
                          f["until_moved"] in vals(s)), len(steps))
            if any(ok(steps[i]) for i in hits if i < moved):
                out.append(f"{f['id']}: a call succeeds while {f['until_moved']} still blocks it")
            if any(not ok(steps[i]) for i in hits if i > moved):
                out.append(f"{f['id']}: a call is expected to fail after {f['until_moved']} was moved")
        elif any(ok(steps[i]) for i in hits):
            out.append(f"{f['id']}: the route makes the failing call again and expects success")
    return out


def variant_problems(t, vid, contracts, assets, seeds):
    """benchmark.v5.validate.check_variant without its tier-label rules (v6 has no tiers)."""
    from benchmark.v5.validate import check_variant
    return [(s, p) for s, p in check_variant(t, None, vid, contracts, assets, seeds) if not p.startswith("tier ")]


def track_problems(t, contracts, assets):
    """Task-Level projections (``<vid>__tl``): the v5 per-variant rules on their seeds, persistent-failure
    consistency, no transient action failure left; every variant in exactly the tracks its content calls for."""
    from benchmark.v6.tracks import content, transient
    out = []
    tr = t["v6_tracks"]
    for fam, x in tr["task"].items():
        for v in x["layouts"]:
            if any(transient(f) for f in t["variants"][v].get("failures") or []):
                out.append({"family": fam, "seed": None, "problem": f"task track: {v} keeps a transient action failure"})
            if not v.endswith("__tl"):
                continue
            seeds = sorted(int(s) for s, c in x["seeds"].items() if c == v)
            out += [{"family": fam, "seed": s, "problem": f"task track {v}: {p}"}
                    for s, p in variant_problems(t, v, contracts, assets, seeds)]
            out += [{"family": fam, "seed": None, "problem": f"task track {v}: {p}"} for p in persistent_problems(t, v)]
    for fam, x in tr["action"].items():
        if not x["action_failures"] and not x["local_conditions"]:
            out.append({"family": fam, "seed": None,
                        "problem": "action track without a transient action failure or a local-repair condition"})
    placed = set(tr["task"]) | set(tr["action"]) | set(tr["controls"]) | \
        {m for x in tr["task"].values() for m in x.get("merged", [])}
    for fam, info in t["v6_variants"].items():
        kinds = [content(t, v) for v in info["layouts"]]
        want = {k for k, on in (("task", any(k[0] for k in kinds)), ("action", any(k[1] for k in kinds))) if on}
        merged = any(fam in x.get("merged", []) for x in tr["task"].values())
        have = {k for k in ("task", "action") if fam in tr[k]} | ({"task"} if merged else set())
        if fam not in placed:
            out.append({"family": fam, "seed": None, "problem": "in no track"})
        elif have != want or (not want and fam not in tr["controls"]):
            out.append({"family": fam, "seed": None, "problem": f"tracks {sorted(have)}, content {sorted(want)}"})
    return out


def main():
    from benchmark.scene import episode_config
    from benchmark.v6.define_tasks_v6 import seed_cases
    doc = json.loads(TASKS.read_text())
    contracts = {c["verb"]: c for c in json.loads((ROOT / "contract_library/skill_contracts.json").read_text())["contracts"]}
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    frozen = json.loads((ROOT / "benchmark/v5/FREEZE.json").read_text())["episodes"]
    out = {"variants": 0, "episodes": 0, "static_ok": 0, "problems": [], "per_task": {}, "v5_hashes_checked": 0,
           "tracks": {}}
    for t in doc["tasks"]:
        tid = t["task_id"]
        n_ok = n_ep = 0
        hashes = defaultdict(list)
        for fam, info in t["v6_variants"].items():
            out["variants"] += 1
            probs = []
            if info["origin"] == "v5":
                for s in SEEDS:                  # the v5 variant itself: unchanged for every seed
                    h = episode_config(t, s, fam)["config_hash"]
                    out["v5_hashes_checked"] += 1
                    if frozen.get(f"{tid}/{fam}/{s}") != h:
                        probs.append((s, f"v5 configuration hash changed ({h})"))
                for v in info["layouts"][1:]:      # seed extension: a second case, checked like a new variant
                    seeds = sorted(int(s) for s, x in info["seeds"].items() if x == v)
                    probs += [(s, f"{v}: {p}") for s, p in variant_problems(t, v, contracts, assets, seeds)]
                if len(info["layouts"]) > 1:
                    if {str(k): v for k, v in seed_cases(tid, fam, info["layouts"]).items()} != \
                            {str(k): v for k, v in info["seeds"].items()}:
                        probs.append((None, "seed manifest is not the deterministic assignment"))
                    if len({route_sig(t["routes"][t["oracle"][v]]["steps"]) for v in info["layouts"]}) < len(info["layouts"]):
                        probs.append((None, "two layouts share one oracle route"))
                hashes[episode_config(t, 10, fam)["config_hash"]].append(fam)
            else:
                if {str(k): v for k, v in seed_cases(tid, fam, info["layouts"]).items()} != \
                        {str(k): v for k, v in info["seeds"].items()}:
                    probs.append((None, "seed manifest is not the deterministic assignment"))
                cnt = Counter(info["seeds"].values())
                if set(cnt) != set(info["layouts"]) or max(cnt.values()) - min(cnt.values()) > 1:
                    probs.append((None, f"unbalanced seed manifest {dict(cnt)}"))
                sigs = {route_sig(t["routes"][t["oracle"][v]]["steps"]) for v in info["layouts"]}
                if len(info["layouts"]) > 1 and len(sigs) < len(info["layouts"]):
                    probs.append((None, "two layouts share one oracle route (no decision difference)"))
                for v in info["layouts"]:
                    meta = t["variants"][v].get("v6") or {}
                    for k in ("challenge", "rationale", "control"):
                        if not meta.get(k):
                            probs.append((None, f"{v}: spec card lacks {k}"))
                    for p in persistent_problems(t, v):
                        probs.append((None, f"{v}: {p}"))
                    seeds = sorted(int(s) for s, x in info["seeds"].items() if x == v)
                    probs += [(s, f"{v}: {p}") for s, p in variant_problems(t, v, contracts, assets, seeds)]
                hashes[episode_config(t, 10, info["layouts"][0])["config_hash"]].append(fam)
            n = len(info["seeds"])
            n_ep += n
            bad = {s for s, _ in probs}
            n_ok += 0 if None in bad else n - len(bad)
            for s, p in probs:
                out["problems"].append({"task": tid, "family": fam, "seed": s, "problem": p})
        for h, fams in hashes.items():
            if len(fams) > 1:
                out["problems"].append({"task": tid, "family": fams, "seed": 10, "problem": f"same configuration {h}"})
        for p in track_problems(t, contracts, assets):
            out["problems"].append({"task": tid, **p})
        for k in ("action", "task"):
            tr = out["tracks"].setdefault(k, {"variants": 0, "episodes": 0})
            tr["variants"] += len(t["v6_tracks"][k])
            tr["episodes"] += sum(len(x["seeds"]) for x in t["v6_tracks"][k].values())
        out["tracks"].setdefault("controls", {"variants": 0})["variants"] += len(t["v6_tracks"]["controls"])
        out["per_task"][tid] = {"episodes": n_ep, "static_ok": n_ok}
        out["episodes"] += n_ep
        out["static_ok"] += n_ok
    out["tasks_sha1"] = hashlib.sha1(TASKS.read_bytes()).hexdigest()
    OUT.write_text(json.dumps(out, indent=1))
    print(f"static: {out['variants']} variants, {out['episodes']} episodes, {out['static_ok']} statically ok, "
          f"{len(out['problems'])} problems; v5 hashes checked {out['v5_hashes_checked']}")
    for p in out["problems"][:60]:
        print("  ", p)
    return 1 if out["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
