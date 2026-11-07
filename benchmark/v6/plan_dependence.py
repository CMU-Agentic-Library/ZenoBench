"""Does a variant need what the robot observes?  A symbolic check with fixed plans (no planner, no simulation).

Every layout of every variant is replayed (oracle_check.World) with plans that were fixed before the episode:

* ``control``: the task's control route, as if the robot did not notice what the variant changed;
* ``other layouts``: the route of another layout of the same variant (a plan that remembers one place);
* ``other variants``: the route of any other variant or layout of the same task (a library of branches
  picked without looking).

A layout that one of them solves did not force the plan to change on what was seen.  Seeds are not tested here:
skills take object names, so where an object stands never changes the symbolic plan (the seed tests perception
and motion, not planning).

The planner sees object instance names (benchmark.observation), so a name can tell the answer by itself
(``full_bowl`` next to ``soup_bowl_1``); ``NAME_HINTS`` lists the words that do, and the report names the variants
whose distractors or targets carry one.

    python benchmark/v6/plan_dependence.py   # -> PLAN_DEPENDENCE.json, summary on stdout
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmark.v6.oracle_check import check  # noqa: E402

HERE = Path(__file__).resolve().parent
NAME_HINTS = r"full|empty|spare|leftover|eating|dirty|clean|cold|warm|kid|child|guest|adult|dropped|homework|hw_|" \
             r"castle|loose|stray|example|set_|seat_|snack|bought|shopping|table_|living_|bed_|toy_|novel|" \
             r"stays|wrong|right|target|decoy|real|fake|old|new_"


def run_with(task, lid, steps):
    t = copy.deepcopy(task)
    r = t["oracle"][lid]
    t["routes"][r] = dict(t["routes"][r], steps=copy.deepcopy(steps))
    return not check(t, lid, gate=True)["problems"]


def route(task, lid):
    return task["routes"][task["oracle"][lid]]["steps"]


def main():
    doc = json.loads((HERE / "tasks.json").read_text())
    rows = []
    for t in doc["tasks"]:
        vs = t["v6_variants"]
        lids = {lid: vid for vid, m in vs.items() for lid in m["layouts"]}
        for vid, m in vs.items():
            ctl = m.get("control")
            is_control = ctl in (None, vid)
            ctl_lid = vs[ctl]["layouts"][0] if ctl and ctl in vs else None
            for lid in m["layouts"]:
                if is_control:
                    continue
                row = {"task": t["task_id"], "variant": vid, "layout": lid, "steps": len(route(t, lid))}
                row["control_plan"] = bool(ctl_lid) and run_with(t, lid, route(t, ctl_lid))
                row["other_layout_plans"] = [o for o in m["layouts"] if o != lid and run_with(t, lid, route(t, o))]
                row["other_variant_plans"] = [o for o, ov in lids.items()
                                              if ov != vid and o != ctl_lid and run_with(t, lid, route(t, o))]
                v = t["variants"][lid]
                names = sorted(set(v.get("watch") or t.get("watch") or []))
                row["named_hints"] = [n for n in names if re.search(NAME_HINTS, n)]
                rows.append(row)
    by_var = {}
    for r in rows:
        by_var.setdefault((r["task"], r["variant"]), []).append(r)
    summary = {"layouts": len(rows), "variants": len(by_var)}
    summary["control_plan_solves"] = sorted({f"{t[:3]} {v}" for (t, v), rs in by_var.items()
                                            if any(r["control_plan"] for r in rs)})
    summary["one_layout_plan_solves_another"] = sorted({f"{t[:3]} {v}" for (t, v), rs in by_var.items()
                                                       if any(r["other_layout_plans"] for r in rs)})
    summary["another_variants_plan_solves"] = sorted({f"{t[:3]} {v}" for (t, v), rs in by_var.items()
                                                     if any(r["other_variant_plans"] for r in rs)})
    summary["names_may_tell"] = sorted({f"{t[:3]} {v}: {', '.join(rs[0]['named_hints'])}" for (t, v), rs in by_var.items()
                                       if rs[0]["named_hints"]})
    (HERE / "PLAN_DEPENDENCE.json").write_text(json.dumps({"summary": summary, "layouts": rows}, indent=1,
                                                          ensure_ascii=False) + "\n")
    for k in ("control_plan_solves", "one_layout_plan_solves_another", "another_variants_plan_solves"):
        print(f"{k}: {len(summary[k])}")
        for x in summary[k]:
            print("   ", x)
    print(f"names_may_tell: {len(summary['names_may_tell'])} of {len(by_var)} variants")
    print(f"{len(rows)} layouts of {len(by_var)} non-control variants replayed")


if __name__ == "__main__":
    main()
