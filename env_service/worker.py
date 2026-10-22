"""One exp = one simulator.  Run under Isaac Sim's Python by the server:

    $ISAACLAB_PYTHON -m env_service.worker --task-id collect_fruits --catalog skill_library/tasks.json \\
        --profile gt --seed 0 --out-dir runs/env_service/<exp> --cmd-fd 5 --resp-fd 6

Line-delimited JSON over two pipes (stdout/stderr stay free for Isaac's logs).
The worker first answers ``{"type": "ready", "observation": ..., "episode": metadata}`` (or
``{"type": "error", ...}``), then serves requests ``{"op": ...}``:

* ``contract`` {"call": {"contract": verb, "args": {...}}} -> {"result": public contract result}
* ``observe``  -> {"observation": ...}
* ``check``    -> {"success", "goal_ok", "goal", "dropped", "final_state", "sim_ticks"}
* ``close``    -> exits

The episode itself (scene, runner, observation fields) is episode.episode.Episode with the
exp's profile.  <out-dir> gets the same files as a benchmark/run_episode.py run (config.json,
annotation.json, calls.jsonl, result.json with planner "http"), so benchmark/evaluate.py scores
HTTP planners too; an exp released without check_task leaves an incomplete result.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from episode.catalog import load_catalog  # noqa: E402
from episode.profile import load_profile  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--variant")
    ap.add_argument("--difficulty")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cmd-fd", type=int, required=True)
    ap.add_argument("--resp-fd", type=int, required=True)
    args = ap.parse_args()
    cmd = os.fdopen(args.cmd_fd, "r")
    resp = os.fdopen(args.resp_fd, "w")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def send(msg):
        resp.write(json.dumps(msg, default=float) + "\n")
        resp.flush()

    t_start = time.time()
    try:
        from benchmark.scene import episode_config
        from episode.episode import Episode, state_summary
        task = load_catalog(args.catalog)[args.task_id]
        cfg = episode_config(task, args.seed, args.variant, args.difficulty)
        ep = Episode(task, cfg, load_profile(args.profile), out)
        meta = ep.metadata()
        (out / "config.json").write_text(json.dumps(
            {"task_id": task["task_id"], "exp_id": out.name, "seed": args.seed, "planner": "http", "route": None,
             "scene": cfg, "catalog": args.catalog, "benchmark_version": task.get("benchmark_version"),
             **{k: meta[k] for k in ("config_hash", "base_sha1", "profile", "profile_hash", "episode_hash")},
             "profile_body": ep.profile, "started": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=1))
        log = open(out / "calls.jsonl", "w")
        send({"type": "ready", "observation": ep.observation(), "episode": meta})
    except Exception as exc:
        traceback.print_exc()
        send({"type": "error", "error": f"{type(exc).__name__}: {exc}"})
        os._exit(1)
    report = {"task_id": task["task_id"], "exp_id": out.name, "seed": args.seed, "variant": cfg["variant"],
              "config_hash": cfg["config_hash"], "benchmark_version": task.get("benchmark_version"),
              "profile": meta["profile"], "profile_hash": meta["profile_hash"], "episode_hash": meta["episode_hash"],
              "planner": "http", "route": None, "initial_positions": ep.initial_positions, "calls": [],
              "success": False, "incomplete": True, "stop_reason": "released"}

    def write_result():
        report["wall_s"] = round(time.time() - t_start, 1)
        report["skill_calls"] = len(report["calls"])
        (out / "result.json").write_text(json.dumps(report, indent=1, default=float))

    for line in cmd:
        req = json.loads(line)
        op = req.get("op")
        try:
            if op == "contract":
                t0 = time.time()
                call = req.get("call")
                result, record = ep.call(call)
                ok_call = isinstance(call, dict)
                row = {"index": len(report["calls"]), "skill": call.get("contract") if ok_call else None,
                       "args": call.get("args", {}) if ok_call else {}, "feedback": record,
                       "wall_s": round(time.time() - t0, 1), "tick": ep.rig.tick, "state": state_summary(ep.rig, task)}
                report["calls"].append(row)
                log.write(json.dumps(row, default=float) + "\n")
                log.flush()
                send({"result": result})
            elif op == "observe":
                send({"observation": ep.observation()})
            elif op == "check":
                res = ep.check()
                report.update(goal=res["goal"], dropped=res["dropped"], final_state=res["final_state"],
                              sim_ticks=res["sim_ticks"], task_success=res["success"], success=res["success"],
                              incomplete=False, stop_reason="planner_done")
                write_result()
                send(res)
            elif op == "close":
                break
            else:
                send({"error": f"unknown op {op!r}"})
        except Exception as exc:
            traceback.print_exc()
            send({"error": f"{type(exc).__name__}: {exc}"})
    if report["incomplete"]:
        write_result()
    sys.stdout.flush()
    os._exit(0)          # Isaac's own shutdown can hang; the process is disposable


if __name__ == "__main__":
    main()
