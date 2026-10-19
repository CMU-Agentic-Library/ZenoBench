"""Consistency checks of the result.json fields written by run_episode.py
(stop_reason, final_state, sim_ticks, goal / drops / outcome) on live runs,
and of evaluate.py on them and on old runs without those fields.

    python benchmark/tests/check_live_fields.py benchmark/runs/retest [--old benchmark/runs/final]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmark.evaluate import episode_metrics, load  # noqa: E402

SETTLE_TICKS = 60      # run_episode steps 60 ticks after the last call before the GT check


def check(r, task):
    out = []
    ok = lambda cond, msg: out.append(("PASS" if cond else "FAIL", msg))
    calls = r.get("calls", [])
    m = episode_metrics(r, task, verified_refs=set())
    if r.get("incomplete"):
        ok(not m["success"], "incomplete run is not a success")
        ok(m["incomplete"], "evaluate marks it incomplete")
        ok("goal" not in r and "final_state" not in r, "no goal / final state recorded after the crash")
        return out, m
    ok(isinstance(r.get("sim_ticks"), int), "sim_ticks recorded")
    last = max((c.get("tick") or 0 for c in calls), default=0)
    ok(r["sim_ticks"] >= last + SETTLE_TICKS, f"sim_ticks {r['sim_ticks']} >= last call tick {last} + settle")
    ok(abs(m["sim_s"] - r["sim_ticks"] / 120.0) < 1e-6, f"sim_s = {m['sim_s']:.2f} s")
    fs = r.get("final_state") or {}
    ok(bool(fs.get("base")), "final_state recorded")
    # final_state is read after the settle, at the GT goal check: an object whose on() goal holds rests on a
    # support (not on the floor, not in the hand), and it is where the state after the last call put it
    held = set(fs.get("held") or []) - {None}
    prev = (calls[-1].get("state") or {}) if calls else {}
    for g in r.get("goal", {}).get("all", []):
        if g["atom"].startswith("on(") and g["holds"]:
            obj = g["atom"][3:-1].split(",", 1)[0].strip()
            p = (fs.get(obj) or {}).get("pos")
            ok(p is not None and p[2] > 0.3 and obj not in held,
               f"final_state[{obj}] at z {p[2] if p else None} on a support ({(fs.get(obj) or {}).get('on')}), not held")
            p0 = (prev.get(obj) or {}).get("pos")
            if p0 and p:
                d = sum((x - y) ** 2 for x, y in zip(p, p0)) ** 0.5
                ok(d < 0.05, f"{obj} moved {d:.3f} m between the last call and the settled final state")
    for d in r.get("dropped", []):
        ok((fs.get(d) or {}).get("pos", [0, 0, 1])[2] < 0.15, f"dropped {d} is low in final_state")
    ok(m["success"] == bool(r.get("task_success")) or r.get("stopped_at") is not None,
       "evaluate success == run_episode task_success")
    if r.get("planner") == "recovery":
        ok(r.get("stop_reason") in ("planner_done", "budget"), f"stop_reason = {r.get('stop_reason')}")
        if r.get("stop_reason") == "budget":
            ok(len(calls) >= 1, f"budget exit after {len(calls)} calls")
    else:
        ok("stop_reason" not in r, "no stop_reason outside the closed loop")
    return out, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--old", help="old run directory (fields absent): evaluate must still read it")
    a = ap.parse_args()
    tasks = {t["task_id"]: t for t in json.loads((ROOT / "benchmark/tasks.json").read_text())["tasks"]}
    n_fail = 0
    for r in load(a.runs):
        rows, m = check(r, tasks[r["task_id"]])
        name = Path(r["_dir"]).relative_to(Path(a.runs).resolve()) if Path(r["_dir"]).is_relative_to(Path(a.runs).resolve()) else r["_dir"]
        state = "incomplete" if m["incomplete"] else ("success" if m["success"] else "fail")
        print(f"== {name}: {state}, stop_reason={r.get('stop_reason')}, calls={m['calls']}, sim_s={m['sim_s']:.1f}, "
              f"pre/exec/gate={m['pre']}/{m['exec']}/{m['gate']}")
        for s, msg in rows:
            print(f"   {s} {msg}")
            n_fail += s == "FAIL"
    if a.old:
        olds = list(load(a.old))
        ms = [episode_metrics(r, tasks[r["task_id"]], set()) for r in olds if r["task_id"] in tasks]
        src = {m["final_state_source"] for m in ms}
        print(f"== old runs {a.old}: {len(ms)} read, final state from {sorted(src)}")
        n_fail += not ms
    print("RESULT", "PASS" if n_fail == 0 else f"{n_fail} FAILED")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
