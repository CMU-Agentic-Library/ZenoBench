"""Reports over the v6 suite (static evidence plus the v5 physics baseline; nothing simulated here).

    python benchmark/v6/report_v6.py

Writes, in benchmark/v6/:

* variant_cards.json - one spec card per concrete variant (instruction, initial conditions, failure triggers,
  goal, tracks, oracle route, challenge / rationale, control);
* ROUTES.md         - every variant's oracle reference route(s), by track;
* SKILL_FIX_LIST.md - skill / physics problems for the skill owner, from the v5 baseline and the v6 routes;
* PHYSICS_TODO.md and batches/physics_v6_new.json, batches/physics_todo.json - what still needs simulation.

Status labels (never merged): PHYSICS_VALIDATED (every manifest episode passed in simulation with the current
configuration hash and route), STATIC_VALIDATED (all static checks pass; physics missing or partial),
DESIGN_COMPLETE (specified, static checks not yet passing).
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


def short(tid):
    return tid[:3]


def tracks_of(t, fam):
    tr = t["v6_tracks"]
    merged = any(fam in x.get("merged", []) for x in tr["task"].values())
    return [k for k in ("action", "task") if fam in tr[k] or (k == "task" and merged)]


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


def physics_status(doc):
    """(task, variant) -> (passed, run, declared) over the manifest episodes, from benchmark/v5/PHYSICS.json
    (only results whose configuration hash and route match the current catalog)."""
    p = ROOT / "benchmark/v5/PHYSICS.json"
    rows = json.loads(p.read_text())["rows"] if p.exists() else []
    from benchmark.scene import episode_config
    from benchmark.v5.validate import route_sha1
    by = {(r["task"], r["variant"], r["seed"]): r for r in rows}
    out = {}
    for t in doc["tasks"]:
        for fam, info in t["v6_variants"].items():
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
    if static.get("tasks_sha1") != hashlib.sha1((V6 / "tasks.json").read_bytes()).hexdigest():
        print("warning: STATIC.json is stale (python benchmark/v6/validate_v6.py)")
    phys = physics_status(doc)
    bad_static = {(p["task"], p["family"] if isinstance(p["family"], str) else None) for p in static["problems"]}
    fixes_rerun = {("T11_collect_fruits", "h_action_grasp_and_ik"): "failure-injection fix 019e517 (pinned IK block)"}
    rows = []
    for t in doc["tasks"]:
        for fam, info in t["v6_variants"].items():
            v0 = t["variants"][info["layouts"][0]]
            ok, run, dec = phys[(t["task_id"], fam)]
            if (t["task_id"], fam) in bad_static:
                status = "DESIGN_COMPLETE"
            elif ok == dec and (t["task_id"], fam) not in fixes_rerun:
                status = "PHYSICS_VALIDATED"
            else:
                status = "STATIC_VALIDATED"
            meta = v0.get("v6") or v0.get("v5") or {}
            rows.append({"task": t["task_id"], "family": fam, "origin": info["origin"], "tracks": tracks_of(t, fam),
                         "mechanisms": sorted({m for v in info["layouts"] for m in mechanisms(t["variants"][v])}),
                         "layouts": info["layouts"], "factor": info.get("factor"), "control": info.get("control"),
                         "challenge": meta.get("challenge") or v0.get("note", ""),
                         "physics": f"{ok}/{run} of {dec}", "status": status,
                         "rerun_needed": fixes_rerun.get((t["task_id"], fam))})
    (V6 / "variant_cards.json").write_text(json.dumps(cards(doc), indent=1, ensure_ascii=False))
    (V6 / "ROUTES.md").write_text(routes_md(doc))
    skill_fix(doc, rows)
    physics_todo(doc, rows)
    print(f"{len(rows)} variants, {10 * len(rows)} episodes; status {dict(Counter(r['status'] for r in rows))}")


def cards(doc):
    """One spec card per concrete variant: instruction, initial conditions, failure triggers, goal, tracks,
    oracle route, challenge / rationale, control, success criteria."""
    from episode.catalog import resolve_task
    out = {}
    for t in doc["tasks"]:
        for fam, info in t["v6_variants"].items():
            for vid in info["layouts"]:
                v = t["variants"][vid]
                rt = resolve_task(t, vid)
                meta = v.get("v6") or v.get("v5") or {}
                fails = v.get("failures", [])
                out[f"{t['task_id']}/{vid}"] = {
                    "family": fam, "tracks": tracks_of(t, fam),
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
                    "control": info.get("control"),
                    "oracle_route": t["oracle"][vid],
                    "challenge": meta.get("challenge") or v.get("note", ""), "rationale": meta.get("rationale", ""),
                    "success_criteria": "every GT goal atom holds at the end, nothing watched on the floor (unless "
                                        "allowed), every declared failure fired and manifested, the route's expected "
                                        "failures failed (benchmark/v5/validate.py classify)"}
    return out


def routes_md(doc):
    md = ["# v6 oracle reference routes", "", "One line per concrete variant of each variant (`!` expected to "
          "fail, `+` recovery step). Seeds: the variant's manifest in tasks.json.", ""]
    for t in doc["tasks"]:
        md += [f"## {t['task_id']}", ""]
        tr = t["v6_tracks"]
        for title, fams in (("Controls", tr["controls"]), ("Action-Level", list(tr["action"])),
                            ("Task-Level", list(tr["task"]))):
            if not fams:
                continue
            md += [f"### {title}", ""]
            for fam in fams:
                cases = tr["task"][fam]["layouts"] if title == "Task-Level" else t["v6_variants"][fam]["layouts"]
                for v in cases:
                    steps = t["routes"][t["oracle"][v]]["steps"]
                    txt = " ".join(("!" if s.get("expect") == "fail" else "") + ("+" if s.get("role") in ("recover", "recovery", "alternative") else "")
                                   + s["skill"] + "(" + ",".join(str(x) for x in s["args"].values()) + ")" for s in steps)
                    md.append(f"* `{v}` ({t['oracle'][v]}, {len(steps)} steps): {txt}")
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
    # exposure of the new variants
    need = defaultdict(set)
    for t in doc["tasks"]:
        for fam, info in t["v6_variants"].items():
            if info["origin"] != "v6":
                continue
            for v in info["layouts"]:
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
          "| skill | object | ok | failed | fail rate | main causes | tasks | v6 variants also using it | example |",
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
           "| skill | object | variants |", "|---|---|---|"]
    for (sk, obj), fams in never:
        md.append(f"| {sk} | {obj} | {', '.join(sorted(fams))} |")
    md += ["", "## 3. Priorities", "",
           "1. **Low cabinet doors** (`open` / `close` / `explore_furniture` on kitchen_cabinet_4 and _6): every v5 "
           "cabinet Hard was 0/10; v6 inspection variants (T04, T05, T10, T13, T18, T20) depend on them.",
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
           "8. **From the oracle smoke of the 40 new variants without a known blocker** (benchmark/runs/v6_smoke_free, "
           "one episode each; 18 pass end to end after two route fixes): `search` misses the object (floor block, "
           "wooden block, rubber duck, mug: 5), grasp `not held` (apple on the bookcase, orange, oatmeal bowl, pot "
           "lid: 5), carry slips of the paperback / mug (4), `look` / `face` blocked or the object out of the "
           "frustum (4), no IK for `hover_above` (T10) and the microwave button press (T07), placement off the "
           "support (spoon on the island), and the T12 two-bin capacity episode ending with a toy not fully inside.",
           "9. New primitive uses: cherry-tomato `pick` + `drop` into the pot (T09 split), `place` into the trash can "
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
        for fam, info in t["v6_variants"].items():
            r = next(x for x in rows if x["task"] == t["task_id"] and x["family"] == fam)
            if r["status"] == "PHYSICS_VALIDATED":
                continue
            deps = sorted({d for v in info["layouts"] for s in t["routes"][t["oracle"][v]]["steps"]
                           if s.get("expect") != "fail" for d in [deps_of(t, v, s)] if d})
            for s, vid in sorted(info["seeds"].items()):
                job = {"task": t["task_id"], "seed": int(s), "variant": vid, "route": t["oracle"][vid], "family": fam}
                todo.append(job)
                if info["origin"] == "v6":
                    new_jobs.append(job)
            r["depends_on"] = deps
    (V6 / "batches").mkdir(exist_ok=True)
    (V6 / "batches/physics_v6_new.json").write_text(json.dumps(new_jobs, indent=0))
    (V6 / "batches/physics_todo.json").write_text(json.dumps(todo, indent=0))
    by_status = Counter(r["status"] for r in rows)
    md = ["# Physics validation to do", "",
          f"* {by_status.get('PHYSICS_VALIDATED', 0)} variants are PHYSICS_VALIDATED (10/10 seeds passed in the v5 "
          "grid with the current hash and route).",
          f"* {len(todo)} episodes remain ({len(new_jobs)} of the {sum(1 for r in rows if r['origin'] == 'v6')} new "
          "variants): `batches/physics_todo.json`; the new variants alone: `batches/physics_v6_new.json`.",
          "* Run: `$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch "
          "benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval` "
          "(~43 episodes / hour with 2 simulators).",
          "* Order: (1) new variants without a skill dependency (`depends on` -), (2) after each skill fix the "
          "variants that depend on it, (3) re-run T11 `h_action_grasp_and_ik` (failure-injection fix 019e517; it "
          "passed in the smoke run), (4) the v5 variants below 10/10 after each skill fix.", "",
          "| task | variant | tracks | physics now | depends on |", "|---|---|---|---|---|"]
    for r in rows:
        if r["status"] != "PHYSICS_VALIDATED":
            md.append(f"| {short(r['task'])} | {r['family']} | {', '.join(r['tracks']) or 'control'} | {r['physics']} | "
                      f"{', '.join(r.get('depends_on', [])) or '-'}{' ; ' + r['rerun_needed'] if r['rerun_needed'] else ''} |")
    (V6 / "PHYSICS_TODO.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
