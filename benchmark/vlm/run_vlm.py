"""Run VLM episodes end to end and summarise them: scene -> image + instruction -> VLM -> skill calls -> goal check.

    $ISAACLAB_PYTHON benchmark/vlm/run_vlm.py --episodes T30_bowls_for_soup:bowl_on_cabinet:10 \\
        --backend replay --profile sticky_snap/benchmark
    $ISAACLAB_PYTHON benchmark/vlm/run_vlm.py --episodes T21_bring_tissues:tissue_or_sponge:10-12 --backend claude

An episode is ``task:variant:seed`` (a v6 variant id; the seed picks its layout from the variant's seed manifest;
``10-12`` is a seed range).  Each runs in its own Isaac process (``benchmark/run_episode.py --planner recovery
--policy benchmark.vlm.planner:VLMPlanner``), one at a time.  ``--backend replay`` answers with the variant's oracle
route: a pipeline test of loading, observation, calling, checking and logging, not a planner result.

Output: ``<out>/<task>/s<seed>_<layout>_recovery-VLMPlanner[@profile]/`` (result.json, calls.jsonl,
vlm_steps.jsonl, images/), and ``<out>/vlm_summary.json`` + ``vlm_summary.md``: per episode the success, the stop
reason, calls, failed calls, the goal atoms that did not hold, and the wall time.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def parse_episodes(specs):
    out = []
    for spec in specs:
        task, variant, seeds = spec.split(":")
        a, _, b = seeds.partition("-")
        out += [(task, variant, s) for s in range(int(a), int(b or a) + 1)]
    return out


def layout_of(task, variant, seed):
    info = task["v6_variants"].get(variant)
    if info is None:                              # already a layout name
        return variant
    return info["seeds"].get(str(seed)) or info["layouts"][0]


def run_dir(out, task_id, seed, layout, profile):
    label = "recovery-VLMPlanner" + (("@" + profile.replace("/", "_")) if profile else "")
    return Path(out) / task_id / f"s{seed}_{layout}_{label}"


def summarise(d):
    r = json.loads((d / "result.json").read_text())
    steps = [json.loads(x) for x in (d / "vlm_steps.jsonl").read_text().splitlines()] \
        if (d / "vlm_steps.jsonl").exists() else []
    goal = r.get("goal") or {"all": [], "any": []}
    false = [g["atom"] for g in goal["all"] if not g["holds"]]
    return {"task": r["task_id"], "seed": r["seed"], "layout": r["variant"], "success": bool(r.get("success")),
            "stop_reason": r.get("stop_reason"), "planner_error": r.get("planner_error"), "crash": r.get("crash"),
            "calls": r.get("skill_calls", len(r.get("calls", []))), "failed_calls": r.get("skill_failures", []),
            "goal_false": false, "vlm_replies": len(steps),
            "invalid_replies": sum(1 for s in steps if s.get("parsed") == "error"),
            "wall_s": r.get("wall_s"), "dir": str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", default=str(ROOT / "benchmark/v6/tasks.json"))
    ap.add_argument("--episodes", nargs="+", required=True, help="task:variant:seed or task:variant:a-b")
    ap.add_argument("--backend", default="replay", choices=["replay", "claude"])
    ap.add_argument("--profile", help="episode profile, e.g. sticky_snap/benchmark (default: benchmark)")
    ap.add_argument("--max-calls", type=int)
    ap.add_argument("--out", default=str(ROOT / "benchmark/runs/vlm"))
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--timeout", type=int, default=3600, help="seconds per episode")
    a = ap.parse_args()

    from episode.catalog import load_catalog
    tasks = load_catalog(a.tasks)
    py = os.environ.get("ISAACLAB_PYTHON", sys.executable)
    out = Path(a.out)
    (out / "logs").mkdir(parents=True, exist_ok=True)
    rows = []
    for task_id, variant, seed in parse_episodes(a.episodes):
        task = tasks[task_id]
        layout = layout_of(task, variant, seed)
        env = dict(os.environ, OMNI_KIT_ACCEPT_EULA="YES", VLM_BACKEND=a.backend)
        if a.backend == "replay":                 # the stand-in answers with the oracle route of this layout
            rp = out / "logs" / f"replay_{task_id}_{layout}.json"
            rp.write_text(json.dumps(task["routes"][task["oracle"][layout]]["steps"], indent=1))
            env["VLM_REPLAY"] = str(rp)
        cmd = [py, str(ROOT / "benchmark/run_episode.py"), "--tasks", a.tasks, "--task", task_id, "--variant", layout,
               "--seed", str(seed), "--planner", "recovery", "--policy", "benchmark.vlm.planner:VLMPlanner",
               "--out", str(out)]
        if a.profile:
            cmd += ["--profile", a.profile]
        if a.max_calls:
            cmd += ["--max-calls", str(a.max_calls)]
        if a.video:
            cmd.append("--video")
        log = out / "logs" / f"{task_id}_s{seed}_{layout}.log"
        print("RUN", task_id, layout, seed, flush=True)
        t0 = time.time()
        try:
            with open(log, "w") as f:
                rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, timeout=a.timeout).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
        d = run_dir(out, task_id, seed, layout, a.profile)
        if (d / "result.json").exists():
            row = summarise(d)
        else:
            row = {"task": task_id, "seed": seed, "layout": layout, "success": False, "stop_reason": "no result",
                   "crash": f"exit {rc}, see {log}"}
        row["exit"] = rc
        row["log"] = str(log)
        rows.append(row)
        print("  ->", "SUCCESS" if row["success"] else "FAILED", row.get("stop_reason"), f"{time.time() - t0:.0f}s",
              flush=True)
    (out / "vlm_summary.json").write_text(json.dumps(rows, indent=1, default=str))
    md = ["| task | seed | layout | success | stop | calls | failed calls | goal atoms false | invalid replies |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['task']} | {r['seed']} | {r['layout']} | {'yes' if r['success'] else 'no'} | "
                  f"{r.get('stop_reason')}{' ' + str(r.get('crash')) if r.get('crash') else ''} | {r.get('calls', '')} | "
                  f"{', '.join(r.get('failed_calls') or [])} | {'; '.join(r.get('goal_false') or [])} | "
                  f"{r.get('invalid_replies', '')} |")
    (out / "vlm_summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
