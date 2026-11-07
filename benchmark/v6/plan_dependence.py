"""Which variants need information the robot only gets while it works?  A symbolic study (no planner, no physics).

Every layout is replayed on the symbolic state of oracle_check.World with the benchmark's observation gate (an
object argument must have been seen: the start room in plain sight, then what a look, an explore, an arrival or a
search of the right room shows).  A plan *passes* a layout when every step is legal and every goal atom the symbolic
state can decide holds; the atoms only geometry decides (upright, clear_of, ...) are counted apart, not assumed.

Two questions:

1. **Fixed plans.**  Does a skill sequence fixed before the episode pass?  Tried: the control's route, another
   layout's route, every other route of the task.  A pass does *not* show the variant needs no observation or
   reasoning (a fixed search or look still uses what it sees, and a choice among same-kind objects is made by name
   here); it shows a fixed sequence exists that works across layouts, so the variant may lack a planning branch and
   is listed for a closer look.
2. **Hidden-state branches.**  For two layouts of one variant that look the same from the start (the same objects
   in plain sight in the start room, on the same supports) but differ in what is hidden (inside a closed cabinet, in
   another room): does each layout's route fail on the other?  Then the robot must change its later subgoals,
   resources or order on what it finds while working; that is the property the hard variants are built for.

Seeds are not part of it: skills take object names, so a seed changes perception and motion, not the plan.

A leakage audit lists what could tell the answer without looking: instance names with a meaning (``full_bowl``),
variant / layout / condition names in what the planner receives, and planner-facing GT fields (positions of
objects never seen, the goal state).

    python benchmark/v6/plan_dependence.py   # -> PLAN_DEPENDENCE.json, summary on stdout
"""
from __future__ import annotations

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
NAME_HINTS = r"full|empty|spare|leftover|eating|dirty|clean|cold|warm|kid|child|guest|adult|dropped|homework|hw_|" \
             r"castle|loose|stray|example|snack|bought|stays|wrong|target|decoy|real|fake|old_|new_|his_|her_"


def run(task, lid, steps):
    """(passes, geometric atoms left unchecked)"""
    t = copy.deepcopy(task)
    r = t["oracle"][lid]
    t["routes"][r] = dict(t["routes"][r], steps=copy.deepcopy(steps))
    res = check(t, lid, gate=True)
    return not res["problems"], res["atoms_geometric"]


def route(task, lid):
    return task["routes"][task["oracle"][lid]]["steps"]


def start_view(task, lid, room):
    """what the robot sees from the start room: plain-sight objects there and the support each stands on"""
    w = World(task, lid)
    return frozenset((n, w.support_of(n)) for n in w.obj if w.plain(n) and w.room_of(w.obj[n]["xy"]) == room)


def leakage(doc):
    """what reaches the planner beyond the instruction and what it has seen"""
    found = []
    worker = (ROOT / "env_service" / "worker.py").read_text()
    if re.search(r'send\(\{"type": "ready".*"episode": meta', worker):
        found.append({"where": "env_service/worker.py ready message",
                      "what": "episode metadata: the variant (with the layout name) and its conditions reach the "
                              "HTTP planner",
                      "fix": "send the planner only what it needs (task_id, seed) and keep the rest in config.json"})
    for prof in sorted((ROOT / "episode" / "profiles").glob("*/benchmark.yaml")):
        txt = prof.read_text()
        for k in ("gt_objects", "task_status"):
            if re.search(rf"^\s*{k}:\s*true", txt, re.M):
                found.append({"where": str(prof.relative_to(ROOT)), "what": f"{k} on: GT positions / goal state"})
    names = {}
    for t in doc["tasks"]:
        for vid, m in t["v6_variants"].items():
            for lid in m["layouts"]:
                v = t["variants"][lid]
                for n in list(v.get("add") or {}) + list(v.get("watch") or []):
                    if re.search(NAME_HINTS, n):
                        names.setdefault(f"{t['task_id'][:3]} {vid}", set()).add(n)
    return found, {k: sorted(v) for k, v in sorted(names.items())}


def main():
    doc = json.loads((HERE / "tasks.json").read_text())
    rows, branches = [], []
    for t in doc["tasks"]:
        vs = t["v6_variants"]
        all_lids = {lid: vid for vid, m in vs.items() for lid in m["layouts"]}
        for vid, m in vs.items():
            ctl = m.get("control")
            if ctl in (None, vid):
                continue
            ctl_lid = vs[ctl]["layouts"][0] if ctl in vs else None
            for lid in m["layouts"]:
                ok, geo = run(t, lid, route(t, lid))
                row = {"task": t["task_id"], "variant": vid, "layout": lid, "steps": len(route(t, lid)),
                       "own_route_passes": ok, "geometric_atoms_unchecked": geo}
                row["control_plan"] = bool(ctl_lid) and run(t, lid, route(t, ctl_lid))[0]
                row["other_layout_plans"] = [o for o in m["layouts"] if o != lid and run(t, lid, route(t, o))[0]]
                row["other_variant_plans"] = [o for o, ov in all_lids.items()
                                              if ov != vid and o != ctl_lid and run(t, lid, route(t, o))[0]]
                rows.append(row)
            for a, b in itertools.combinations(m["layouts"], 2):
                room = ((t["variants"][a].get("layout") or {}).get("start") or {}).get("room")
                same = room is not None and start_view(t, a, room) == start_view(t, b, room)
                a_on_b, b_on_a = run(t, b, route(t, a))[0], run(t, a, route(t, b))[0]
                branches.append({"task": t["task_id"], "variant": vid, "layouts": [a, b], "start_room": room,
                                 "same_start_view": same, "route_a_passes_b": a_on_b, "route_b_passes_a": b_on_a,
                                 "hidden_state_branch": same and not a_on_b and not b_on_a})
    by_var = {}
    for r in rows:
        by_var.setdefault((r["task"], r["variant"]), []).append(r)
    key = lambda tv: f"{tv[0][:3]} {tv[1]}"  # noqa: E731
    leaks, names = leakage(doc)
    hb = sorted({key((b["task"], b["variant"])) for b in branches if b["hidden_state_branch"]})
    summary = {
        "layouts": len(rows), "variants": len(by_var),
        "fixed_sequence_exists": {
            "note": "a fixed skill sequence passes: the variant may lack a planning branch; check it, it is not "
                    "proof that no observation or reasoning is needed",
            "control_route": sorted({key(k) for k, rs in by_var.items() if any(r["control_plan"] for r in rs)}),
            "another_layouts_route": sorted({key(k) for k, rs in by_var.items()
                                             if any(r["other_layout_plans"] for r in rs)}),
            "another_variants_route": sorted({key(k) for k, rs in by_var.items()
                                              if any(r["other_variant_plans"] for r in rs)}),
        },
        "hidden_state_branch": hb,
        "multi_layout_variants": len({key((b["task"], b["variant"])) for b in branches}),
        "own_route_fails_with_gate": sorted({key((r["task"], r["variant"])) for r in rows if not r["own_route_passes"]}),
        "geometric_atoms_unchecked": sum(r["geometric_atoms_unchecked"] for r in rows),
        "leaks": leaks, "names_may_tell": names,
    }
    (HERE / "PLAN_DEPENDENCE.json").write_text(json.dumps({"summary": summary, "layouts": rows, "branches": branches},
                                                          indent=1, ensure_ascii=False) + "\n")
    f = summary["fixed_sequence_exists"]
    print(f"{len(rows)} layouts of {len(by_var)} non-control variants (gate on; geometric atoms left to the "
          f"simulation: {summary['geometric_atoms_unchecked']})")
    print(f"reference route fails under the gate: {len(summary['own_route_fails_with_gate'])}")
    print(f"a fixed sequence passes (check, not proof): control route {len(f['control_route'])}, another layout's "
          f"{len(f['another_layouts_route'])}, another variant's {len(f['another_variants_route'])}")
    print(f"hidden-state branch (same start view, each route fails on the other): {len(hb)} of "
          f"{summary['multi_layout_variants']} multi-layout variants")
    for x in hb:
        print("   ", x)
    print(f"leaks to the planner: {len(leaks)}")
    for x in leaks:
        print("   ", x["where"], "-", x["what"])
    print(f"instance names that may tell: {len(names)} variants")


if __name__ == "__main__":
    main()
