"""Run one benchmark episode in Isaac Sim.

    $ISAACLAB_PYTHON benchmark/run_episode.py --task T01_book_to_shelf --seed 1 --route fallback_expose
    $ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --seed 0 --planner fixed
    python benchmark/run_episode.py --batch benchmark/batches/accept.json --jobs 2   # one Isaac process each

Planners (same low-level skills, same observation limits except the oracle):

* ``scripted`` - a declared route of benchmark/tasks.json (nominal, fallback,
  alternative or negative).  Steps marked ``"expect": "fail"`` must really
  fail in physics; the route then continues in the same simulator.  This
  proves a route is physically executable; it is not a planner result.
* ``fixed``    - the task's nominal plan, stops at the first failed call.
* ``retry``    - the nominal plan; a failed call is repeated (max 2 times).
* ``oracle``   - independent GT oracle: the original GT runner (full state,
  original automatic repairs) executes the route the task maps the
  episode's variant to.
* ``recovery`` - explicit recovery planning: a Planner object (benchmark/
  planners.py) decides every call from observations and feedback.  The VLM
  plugs in here; ``--planner recovery --policy <module:Class>``.

The episode is episode.episode.Episode, the same class the env_service worker drives.  Its
profile (episode/profiles/*.yaml) follows the planner: ``oracle`` for the oracle, ``benchmark``
for every other planner; ``--profile`` overrides it (the run directory then ends in
``@<profile>``).  ``--tasks`` takes any catalog, also skill_library/tasks.json (one variant
``default`` per task, its skill subgraph as the ``nominal`` route).

Output: <out>/<task>/<seed>_<route-or-planner>/ result.json, calls.jsonl,
config.json (scene, profile, config_hash, episode_hash), first-person images (images/),
annotation.json, run.mp4 with --video.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TASKS = ROOT / "benchmark/tasks.json"
OUT = ROOT / "benchmark/runs"


def load_tasks(path=TASKS):
    """Any catalog: benchmark task files, or skill_library/tasks.json (one variant per task)."""
    from episode.catalog import load_catalog
    return load_catalog(path)


def code_version():
    def git(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    diff = git("diff", "HEAD")
    return {"commit": git("rev-parse", "HEAD"), "dirty_files": git("status", "--short").splitlines(),
            "diff_sha1": hashlib.sha1(diff.encode()).hexdigest()}


def tasks_ref(path):
    """Which task file (and which content of it) an episode was built from."""
    p = Path(path).resolve()
    return {"path": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),
            "sha1": hashlib.sha1(p.read_bytes()).hexdigest()}


def resolve_steps(task, cfg, route_name):
    route = task["routes"][route_name]
    return route, [dict(s) for s in route["steps"]]


PLANNER_PROFILES = {"scripted": "benchmark", "fixed": "benchmark", "retry": "benchmark", "recovery": "benchmark",
                    "oracle": "oracle"}


def run_episode(task, seed, route=None, planner="scripted", variant=None, out_root=OUT, video=False,
                images=True, policy=None, difficulty=None, max_calls=None, tasks_file=TASKS, profile=None):
    from benchmark.scene import episode_config
    from episode.episode import Episode, state_summary
    from episode.profile import load_profile, max_calls as profile_max_calls
    prof = load_profile(profile or PLANNER_PROFILES[planner])
    cfg = episode_config(task, seed, variant, difficulty)
    if planner == "oracle" and route is None:
        route = task["oracle"][cfg["variant"]]
    if planner in ("fixed", "retry") and route is None:
        route = task["nominal"]
    label = route if planner == "scripted" else f"{planner}" + (f"-{route}" if planner == "oracle" else "") + \
        (f"-{policy.rsplit(':', 1)[-1]}" if planner == "recovery" and policy else "")
    if profile:
        label += f"@{prof['name']}"
    out = Path(out_root) / task["task_id"] / f"s{seed}_{cfg['variant']}_{label}"
    out.mkdir(parents=True, exist_ok=True)
    config = {"task_id": task["task_id"], "exp_id": f"{task['exp_id']}-s{seed}-{label}", "seed": seed,
              "planner": planner, "route": route, "scene": cfg, "code": code_version(),
              "tasks_file": tasks_ref(tasks_file), "benchmark_version": task.get("benchmark_version", "v2"),
              "config_hash": cfg["config_hash"], "profile": prof["name"], "profile_hash": prof["hash"],
              "profile_body": prof, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    (out / "config.json").write_text(json.dumps(config, indent=1))
    report = {"task_id": task["task_id"], "exp_id": config["exp_id"], "seed": seed, "variant": cfg["variant"],
              "config_hash": cfg["config_hash"], "benchmark_version": config["benchmark_version"],
              "profile": prof["name"], "profile_hash": prof["hash"],
              "planner": planner, "route": route, "calls": [], "success": False, "started": time.time()}
    ep = None
    calls_f = open(out / "calls.jsonl", "w")

    def log_row(row):
        report["calls"].append(row)
        calls_f.write(json.dumps(row, default=float) + "\n")
        calls_f.flush()

    try:
        ep = Episode(task, cfg, prof, out, video=video, images=images,
                     image_dir=out / "images" if images else None)
        rig = ep.rig
        meta = ep.metadata()
        report["episode_hash"] = config["episode_hash"] = meta["episode_hash"]
        report["base_sha1"] = config["base_sha1"] = meta["base_sha1"]
        (out / "config.json").write_text(json.dumps(config, indent=1))
        report["initial_positions"] = ep.initial_positions
        if planner != "oracle":
            report["initial_observation"] = ep.observation("path", "initial")
        if planner == "recovery":
            from benchmark.planners import load_policy
            pol = load_policy(policy)
            report["stop_reason"] = "budget"     # max_calls reached without the planner ending the episode
            pol.reset(task_instruction=task["instruction"], skills=task.get("skill_menu"))
            for i in range(max_calls or profile_max_calls(prof, task)):
                act = pol.next_call(ep.observation("path", f"step{i}"))
                if act is None:
                    report["stop_reason"] = "planner_done"
                    break
                t0 = time.time()
                _, record = ep.call({"contract": act["skill"], "args": act.get("args", {})})
                log_row({"index": i, "skill": act["skill"], "args": act.get("args", {}), "feedback": record,
                         "planner_note": act.get("note", ""), "wall_s": round(time.time() - t0, 1), "tick": rig.tick,
                         "state": state_summary(rig, task)})
        else:
            _, steps = resolve_steps(task, cfg, route)
            for i, st in enumerate(steps):
                expect = st.get("expect", "ok") if planner == "scripted" else "ok"
                if planner == "oracle" and (st.get("expect") == "fail" or st.get("role") == "unwind"):
                    continue                           # the oracle knows the failing call is useless (and
                                                       # skips the steps that only undo its side effects)
                tries = 3 if planner == "retry" else 1
                for k in range(tries):
                    t0 = time.time()
                    _, fb = ep.call({"contract": st["skill"], "args": st.get("args", {})})
                    if task.get("auto_look") and fb["error_code"] == "NOT_IN_VIEW":
                        # probes only: an explicit look at the remembered object, then the call again
                        target = fb["error"].split("'")[1]
                        _, lk = ep.call({"contract": "look", "args": {"target": target}})
                        log_row({"index": i, "try": k, "skill": "look", "args": {"target": target}, "expect": "ok",
                                 "role": "auto_look", "note": "", "feedback": lk, "wall_s": 0.0, "tick": rig.tick,
                                 "state": state_summary(rig, task)})
                        print("CALL", i, k, lk["action"], "OK" if lk["success"] else f"FAIL {lk['error']}",
                              "(auto look)", flush=True)
                        _, fb = ep.call({"contract": st["skill"], "args": st.get("args", {})})
                    log_row({"index": i, "try": k, "skill": st["skill"], "args": st.get("args", {}), "expect": expect,
                             "role": st.get("role", ""), "note": st.get("note", ""), "feedback": fb,
                             "wall_s": round(time.time() - t0, 1), "tick": rig.tick,
                             "state": state_summary(rig, task)})
                    print("CALL", i, k, fb["action"], "OK" if fb["success"] else f"FAIL {fb['error_code']}: {fb['error']}",
                          f"(expect {expect})", flush=True)
                    if fb["success"] or planner != "retry":
                        break
                ok = fb["success"]
                if expect == "fail" and ok:
                    report["route_violation"] = f"call {i} {fb['action']} was expected to fail but succeeded"
                    break
                if expect == "ok" and not ok:
                    report["stopped_at"] = i
                    break
        chk = ep.check()
        report["goal"] = chk["goal"]
        report["dropped"] = chk["dropped"]
        report["final_state"] = chk["final_state"]           # side effects for benchmark/evaluate.py
        report["sim_ticks"] = chk["sim_ticks"]               # 120 ticks per simulated second
        report["task_success"] = bool(chk["success"] and not report.get("route_violation"))
        report["skill_calls"] = len(report["calls"])
        report["skill_failures"] = [c["feedback"]["action"] for c in report["calls"] if not c["feedback"]["success"]]
        report["success"] = report["task_success"]
        for g in chk["goal"]["all"] + [r for grp in chk["goal"]["any"] for r in grp]:
            print("GOAL", g["atom"], "OK" if g["holds"] else f"FALSE {g['detail']}", flush=True)
    except Exception as exc:
        report["crash"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        report["incomplete"] = True
        print("CRASH", report["crash"], flush=True)
    finally:
        calls_f.close()
        if ep is not None:
            rig = ep.rig
            report["events"] = rig.events[-300:]
            if ep.observer is not None:
                report["observation_cache"] = ep.observer.cache
                report["images"] = ep.observer.images
                report["gate_calls"] = ep.runner.calls
            if video:
                try:
                    report["video"] = str(rig.write_video(out / "run.mp4"))
                except Exception as exc:
                    report["video_error"] = str(exc)
        report["wall_s"] = round(time.time() - report["started"], 1)
        (out / "result.json").write_text(json.dumps(report, indent=1, default=float))
        print("RESULT", task["task_id"], seed, label, "SUCCESS" if report.get("success") else "FAILED", flush=True)
        sys.stdout.flush()
        os._exit(0 if report.get("success") else 3)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", default=str(TASKS))
    ap.add_argument("--task")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--variant")
    ap.add_argument("--difficulty", choices=["easy", "medium", "hard"], help="sample the variant from this tier")
    ap.add_argument("--route")
    ap.add_argument("--planner", default="scripted", choices=["scripted", "fixed", "retry", "oracle", "recovery"])
    ap.add_argument("--policy", help="module:Class of a recovery planner")
    ap.add_argument("--profile", help="episode profile (name or YAML) instead of the planner's default "
                                      f"{PLANNER_PROFILES}")
    ap.add_argument("--max-calls", type=int, help="call budget of a recovery planner (default: task max_calls or 60)")
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--batch", help="JSON list of {task, seed, route?, planner?, variant?, video?}")
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    if a.batch:
        return run_batch(a)
    tasks = load_tasks(a.tasks)
    run_episode(tasks[a.task], a.seed, a.route, a.planner, a.variant, a.out, a.video, not a.no_images, a.policy,
                a.difficulty, a.max_calls, a.tasks, a.profile)


def run_batch(a):
    """At most ``--jobs`` Isaac processes at a time (the benchmark limit is 2)."""
    jobs = json.loads(Path(a.batch).read_text())
    py = os.environ.get("ISAACLAB_PYTHON", sys.executable)
    logs = Path(a.out) / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    queue, procs = list(jobs), []
    while queue or procs:
        while queue and len(procs) < min(a.jobs, 2):
            j = queue.pop(0)
            cmd = [py, __file__, "--tasks", a.tasks, "--task", j["task"], "--seed", str(j.get("seed", 0)),
                   "--planner", j.get("planner", "scripted"), "--out", a.out]
            for k in ("route", "variant", "policy", "difficulty", "max_calls", "profile"):
                if j.get(k):
                    cmd += [f"--{k.replace('_', '-')}", str(j[k])]
            if j.get("video"):
                cmd.append("--video")
            name = (f"{j['task']}_s{j.get('seed', 0)}_{j.get('variant') or j.get('difficulty') or 'any'}_"
                    f"{j.get('route') or j.get('planner', 'scripted')}")
            log = open(logs / f"{name}.log", "w")
            procs.append((name, subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                                 env=dict(os.environ, OMNI_KIT_ACCEPT_EULA="YES")), time.time()))
            print("START", name, flush=True)
        time.sleep(5)
        for item in list(procs):
            name, p, t0 = item
            if p.poll() is not None:
                procs.remove(item)
                print(name, "OK" if p.returncode == 0 else f"FAILED({p.returncode})", f"{time.time() - t0:.0f}s",
                      flush=True)
            elif time.time() - t0 > 5400:
                p.kill()
                procs.remove(item)
                print(name, "TIMEOUT (incomplete)", flush=True)


if __name__ == "__main__":
    main()
