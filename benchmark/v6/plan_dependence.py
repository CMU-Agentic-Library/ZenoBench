"""Fixed plans and information dependence: a symbolic screening of the variants (no planner, no physics).

Every layout is replayed on the symbolic state of oracle_check.World with the benchmark's observation gate: an object
argument must have been seen (the start room in plain sight, then what a look, an explore, an arrival or a search
shows); ``search`` keeps to its room, opens that room's closed cabinets as the skill does and does not see under a
lid.  A plan *passes* a layout when every step is legal and every goal atom the symbolic state decides holds,
process requirements (never_picked) included.  Atoms only geometry decides (upright, fully_inside, clear_of ...) are
listed apart: passing here is not a physics validation.

Diagnostics:

1. **Control route moved to every other variant** of the task.
2. **Routes moved between the layouts of a variant**, and whether one candidate (any layout's route, or the
   control's) passes every layout: a *universal fixed sequence*.
3. **Hidden-state branches**: two layouts that look the same before the key observation (the same objects in plain
   sight in the start room, on the same supports) and differ in what is hidden, where each layout's route fails on
   the other.

A fixed sequence that passes does not mean the variant needs no observation or reasoning: its looks and searches
still use what they see, and a choice among same-kind objects is made by name here.  It means a sequence exists that
works across the layouts, so the variant may lack a planning branch and gets a closer look.  The results screen the
catalog; nothing is removed on them.

Why a moved route fails, from its first problem: ``unknown_object`` (a name this task never has), ``resource_missing``
(an object of the task that this layout leaves out), ``not_observed`` (the gate: never seen), ``argument_mismatch``
(a step that does not fit the state: not near, wrong hand, closed door, wrong search room ...), ``goal_not_met``.

The leakage audit checks what reaches a planner: the env_service ready message, the run_episode recovery planner's
inputs, the benchmark profiles' GT fields, static places, per-layout instructions, and instance names with a meaning.

    python benchmark/v6/plan_dependence.py   # -> PLAN_DEPENDENCE.json, summary on stdout
"""
from __future__ import annotations

import collections
import copy
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmark.v6.oracle_check import World, check  # noqa: E402

HERE = Path(__file__).resolve().parent
# variants whose instruction is meant to differ between layouts: the person's words carry the clue
INSTRUCTION_CLUES = {"T01 which_book": "the guest says where they read last night; the robot maps that to the room"}
NAME_HINTS = r"full|empty|spare|leftover|eating|dirty|clean|cold|warm|kid|child|guest|adult|dropped|homework|hw_|" \
             r"castle|loose|stray|example|snack|bought|stays|wrong|target|decoy|real|fake|old_|new_|his_|her_|stock"


def route(task, lid):
    return task["routes"][task["oracle"][lid]]["steps"]


def replay(task, lid, steps):
    t = copy.deepcopy(task)
    r = t["oracle"][lid]
    t["routes"][r] = dict(t["routes"][r], steps=copy.deepcopy(steps))
    return check(t, lid, gate=True)


def run(task, lid, steps):
    """(passes, geometric atoms left unchecked)"""
    res = replay(task, lid, steps)
    return not res["problems"], res["atoms_geometric"]


def task_names(task):
    """every object name any layout of the task (or its base scene) has"""
    names = set()
    for lid in task["variants"]:
        if task["variants"][lid].get("since") and lid != "bare":
            names |= set(World(task, lid).obj)
    return names


def why(res, known):
    if not res["problems"]:
        return None
    p = res["problems"][0]["problem"]
    m = re.match(r"(\S+) is not in the scene", p) or re.match(r"unknown destination (\S+)", p)
    if m:
        return "resource_missing" if m.group(1) in known else "unknown_object"
    if "never observed" in p:
        return "not_observed"
    if res["problems"][0]["skill"] == "goal":
        return "goal_not_met"
    return "argument_mismatch"


def start_view(task, lid, room):
    """what the robot sees before its key observation: plain-sight objects in the start room, on their supports"""
    w = World(task, lid)
    return frozenset((n, w.support_of(n)) for n in w.obj if w.plain(n) and w.room_of(w.obj[n]["xy"]) == room)


def leakage(doc):
    found = []
    worker = (ROOT / "env_service" / "worker.py").read_text()
    if re.search(r'send\(\{"type": "ready".*"episode": meta', worker):
        found.append({"where": "env_service/worker.py, ready message to the HTTP planner",
                      "what": "episode metadata: variant (with the layout name), conditions, seed (with tasks.json "
                              "the seed names the layout)",
                      "fix": "send the planner the instruction and the observation only; keep the metadata in "
                             "config.json"})
    run_ep = (ROOT / "benchmark" / "run_episode.py").read_text()
    m = re.search(r"pol\.reset\((.*?)\)\n", run_ep, re.S)
    if m and re.search(r"cfg|variant|oracle|note|config", m.group(1)):
        found.append({"where": "benchmark/run_episode.py, recovery planner reset", "what": m.group(1)})
    for prof in sorted((ROOT / "episode" / "profiles").glob("*/benchmark.yaml")):
        txt = prof.read_text()
        for k in ("gt_objects", "task_status"):
            if re.search(rf"^\s*{k}:\s*true", txt, re.M):
                found.append({"where": str(prof.relative_to(ROOT)), "what": f"{k} on: GT positions / goal state"})
        if not re.search(r"^\s*mask_feedback:\s*true", txt, re.M):
            found.append({"where": str(prof.relative_to(ROOT)), "what": "feedback not masked: unseen names"})
    obs = (ROOT / "benchmark" / "observation.py").read_text()
    sp = obs[obs.index("def static_places"):]
    sp = re.split(r"\n(?:def|class) ", sp[5:])[0]
    if "ann.objects" in sp:
        found.append({"where": "benchmark/observation.py static_places", "what": "objects in the known places"})
    per_layout, names = [], {}
    for t in doc["tasks"]:
        for vid, m_ in t["v6_variants"].items():
            texts = {t["variants"][lid].get("instruction") or t["instruction"] for lid in m_["layouts"]}
            if len(texts) > 1:
                per_layout.append(f"{t['task_id'][:3]} {vid}")
            for lid in m_["layouts"]:
                txt = t["variants"][lid].get("instruction") or t["instruction"]
                if vid in txt or lid in txt:
                    found.append({"where": f"{t['task_id'][:3]} {lid} instruction", "what": "names the variant"})
                v = t["variants"][lid]
                for n in list(v.get("add") or {}) + list(v.get("watch") or []):
                    if re.search(NAME_HINTS, n):
                        names.setdefault(f"{t['task_id'][:3]} {vid}", set()).add(n)
    per_layout = [x for x in per_layout if x not in INSTRUCTION_CLUES]
    if per_layout:
        found.append({"where": "instructions", "what": "the instruction differs between layouts: "
                      + ", ".join(per_layout)})
    checked = ["env_service ready message", "run_episode recovery planner inputs (instruction, skills, observation)",
               "benchmark profiles: gt_objects, task_status, mask_feedback", "static known places (no objects)",
               "instructions: no variant / layout name, the same for every layout (except INSTRUCTION_CLUES, where "
               "the person's words are the clue)",
               "oracle routes and configuration notes: not in any planner-facing field above"]
    return checked, found, {k: sorted(v) for k, v in sorted(names.items())}


def main():
    doc = json.loads((HERE / "tasks.json").read_text())
    rows, branches, universal = [], [], []
    for t in doc["tasks"]:
        vs = t["v6_variants"]
        known = task_names(t)
        all_lids = {lid: vid for vid, m in vs.items() for lid in m["layouts"]}
        for vid, m in vs.items():
            ctl = m.get("control")
            if ctl in (None, vid):
                continue
            ctl_lid = vs[ctl]["layouts"][0] if ctl in vs else None
            for lid in m["layouts"]:
                own = replay(t, lid, route(t, lid))
                row = {"task": t["task_id"], "variant": vid, "layout": lid, "steps": len(route(t, lid)),
                       "own_route_passes": not own["problems"], "geometric_atoms": own["geometric_atoms"]}
                if ctl_lid:
                    r = replay(t, lid, route(t, ctl_lid))
                    row["control_route"] = why(r, known) or "passes"
                row["other_layouts"] = {o: why(replay(t, lid, route(t, o)), known) or "passes"
                                        for o in m["layouts"] if o != lid}
                row["other_variants_passing"] = [o for o, ov in all_lids.items()
                                                 if ov != vid and o != ctl_lid and run(t, lid, route(t, o))[0]]
                rows.append(row)
            if len(m["layouts"]) > 1:
                cands = list(m["layouts"]) + ([ctl_lid] if ctl_lid else [])
                ok = [c for c in cands if all(run(t, lid, route(t, c))[0] for lid in m["layouts"])]
                universal.append({"task": t["task_id"], "variant": vid, "candidates": cands, "passes_all": ok})
            for a, b in itertools.combinations(m["layouts"], 2):
                room = ((t["variants"][a].get("layout") or {}).get("start") or {}).get("room")
                same = room is not None and start_view(t, a, room) == start_view(t, b, room)
                ra, rb = replay(t, b, route(t, a)), replay(t, a, route(t, b))
                branches.append({"task": t["task_id"], "variant": vid, "layouts": [a, b], "start_room": room,
                                 "same_before_key_observation": same,
                                 "route_a_on_b": why(ra, known) or "passes", "route_b_on_a": why(rb, known) or "passes",
                                 "hidden_state_branch": same and bool(ra["problems"]) and bool(rb["problems"])})
    key = lambda tv: f"{tv[0][:3]} {tv[1]}"  # noqa: E731
    by_var = collections.defaultdict(list)
    for r in rows:
        by_var[(r["task"], r["variant"])].append(r)
    checked, leaks, names = leakage(doc)
    reasons = collections.Counter(r["control_route"] for r in rows if "control_route" in r)
    lay_reasons = collections.Counter(x for r in rows for x in r["other_layouts"].values())
    summary = {
        "scope": {"layouts": len(rows), "variants": len(by_var),
                  "candidates": "per layout: the control's route, every other layout's route of the variant, every "
                                "route of the task's other variants; per variant: one route through all its layouts"},
        "control_route_on_other_variants": dict(reasons),
        "control_route_passes": sorted({key(k) for k, rs in by_var.items() if any(r.get("control_route") == "passes" for r in rs)}),
        "routes_between_layouts": dict(lay_reasons),
        "universal_fixed_sequence": sorted(key((u["task"], u["variant"])) for u in universal if u["passes_all"]),
        "multi_layout_variants": len(universal),
        "hidden_state_branch": sorted({key((b["task"], b["variant"])) for b in branches if b["hidden_state_branch"]}),
        "own_route_fails_with_gate": sorted({key(k) for k, rs in by_var.items() if not all(r["own_route_passes"] for r in rs)}),
        "geometric_atoms_unchecked": sum(len(r["geometric_atoms"]) for r in rows),
        "leakage_checked": checked, "leaks": leaks, "names_may_tell": names,
    }
    (HERE / "PLAN_DEPENDENCE.json").write_text(json.dumps(
        {"summary": summary, "layouts": rows, "universal": universal, "branches": branches},
        indent=1, ensure_ascii=False) + "\n")
    s = summary
    print(f"{len(rows)} layouts of {len(by_var)} non-control variants; gate on; geometric atoms not checked: "
          f"{s['geometric_atoms_unchecked']}")
    print(f"reference route fails under the gate: {len(s['own_route_fails_with_gate'])}")
    print(f"control route on the other variants: {dict(reasons)}")
    print(f"routes moved between layouts: {dict(lay_reasons)}")
    print(f"universal fixed sequence (check, not proof): {len(s['universal_fixed_sequence'])} of "
          f"{s['multi_layout_variants']} multi-layout variants")
    print(f"hidden-state branch: {len(s['hidden_state_branch'])} of {s['multi_layout_variants']}")
    print(f"leaks: {len(leaks)}")
    for x in leaks:
        print("   ", x["where"], "-", x["what"])
    print(f"instance names that may tell: {len(names)} variants")


if __name__ == "__main__":
    main()
