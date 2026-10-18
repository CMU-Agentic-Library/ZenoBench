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

Output: <out>/<task>/<seed>_<route-or-planner>/ result.json, calls.jsonl,
config.json, first-person images (images/), annotation.json, run.mp4 with --video.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
    return {t["task_id"]: t for t in json.loads(Path(path).read_text())["tasks"]}


def code_version():
    def git(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    diff = git("diff", "HEAD")
    return {"commit": git("rev-parse", "HEAD"), "dirty_files": git("status", "--short").splitlines(),
            "diff_sha1": hashlib.sha1(diff.encode()).hexdigest()}


def resolve_steps(task, cfg, route_name):
    route = task["routes"][route_name]
    return route, [dict(s) for s in route["steps"]]


def evaluate_goal(rig, goal, start_snapshot):
    """{"all": [atom], "any": [[atom...], ...]}: every ``all`` atom and at
    least one ``any`` group must hold on the final GT state."""
    from zeno_skills.predicates import REGISTRY
    ctx = {"before": start_snapshot}

    def atom(a):
        missing = [x for x in a[1:] if isinstance(x, str) and x in start_snapshot.get("_removed", ())]
        if missing:
            return {"atom": f"{a[0]}({', '.join(map(str, a[1:]))})", "holds": False,
                    "detail": f"{missing[0]} is not in this episode"}
        neg = a[0].startswith("not ")
        name = a[0][4:] if neg else a[0]
        pred = REGISTRY[name]
        ok, detail = pred.evaluate(rig, ctx, **dict(zip(pred.arg_names, a[1:])))
        ok = bool(ok) != neg
        return {"atom": f"{a[0]}({', '.join(map(str, a[1:]))})", "holds": ok, "detail": str(detail)}
    rows = [atom(a) for a in goal.get("all", [])]
    groups = [[atom(a) for a in g] for g in goal.get("any", [])]
    ok = all(r["holds"] for r in rows) and (not groups or any(all(r["holds"] for r in g) for g in groups))
    return ok, {"all": rows, "any": groups}


def floor_drops(rig, task, start_snapshot):
    """Task objects that ended on the floor although they did not start there."""
    out = []
    st = rig.state()
    for n in task.get("watch", []):
        if n not in rig.ann.objects:
            continue
        z0 = start_snapshot["objects"][n]["pos"][2]
        # the centre, not the bottom: a mug lying on its side has its "bottom" 5 cm up
        low = min(float(rig.geo.bottom(n, st)[2]), float(rig.geo.centre(n, st)[2]))
        in_container = any(rig.geo.inside(n, c, st)[0] for c, o in rig.ann.objects.items()
                           if c != n and rig.ann.asset_of(o).get("container"))
        if low < 0.08 and z0 > 0.3 and not in_container and n not in task.get("may_end_on_floor", []):
            out.append(n)
    return out


def run_episode(task, seed, route=None, planner="scripted", variant=None, out_root=OUT, video=False,
                images=True, policy=None, difficulty=None, max_calls=None):
    from benchmark.scene import build_annotation, episode_config, make_prepare
    cfg = episode_config(task, seed, variant, difficulty)
    if planner == "oracle" and route is None:
        route = task["oracle"][cfg["variant"]]
    if planner in ("fixed", "retry") and route is None:
        route = task["nominal"]
    label = route if planner == "scripted" else f"{planner}" + (f"-{route}" if planner == "oracle" else "") + \
        (f"-{policy.rsplit(':', 1)[-1]}" if planner == "recovery" and policy else "")
    out = Path(out_root) / task["task_id"] / f"s{seed}_{cfg['variant']}_{label}"
    out.mkdir(parents=True, exist_ok=True)
    ann_path = build_annotation(cfg, out / "annotation.json")
    config = {"task_id": task["task_id"], "exp_id": f"{task['exp_id']}-s{seed}-{label}", "seed": seed,
              "planner": planner, "route": route, "scene": cfg, "code": code_version(),
              "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    (out / "config.json").write_text(json.dumps(config, indent=1))
    report = {"task_id": task["task_id"], "exp_id": config["exp_id"], "seed": seed, "variant": cfg["variant"],
              "planner": planner, "route": route, "calls": [], "success": False, "started": time.time()}
    rig = None
    session = None
    from zeno_skills.runtime import launch, make_rig
    app = launch(video, first_person=images)
    calls_f = open(out / "calls.jsonl", "w")
    try:
        import numpy as np
        base = ROOT / cfg["base"]
        base_task = json.loads((base / "task.json").read_text())
        rig = make_rig(app, f"{cfg['base']}/scene.usd", str(ann_path), video=video, res=(540, 960),
                       handle_objects=tuple(task.get("handle_objects", ())), prepare=make_prepare(cfg),
                       first_person=images)
        # benchmark low-level setting, the same for every planner and the oracle
        rig.edge_pinch_upright_waist = True
        # thermal state only for the foods that exist in this episode (removed objects have no body)
        base_task = dict(base_task, thermal={k: v for k, v in (base_task.get("thermal") or {}).items()
                                             if k not in cfg["remove"]})
        for food, over in (cfg.get("thermal_override") or {}).items():
            if food in base_task["thermal"]:
                base_task["thermal"][food] = dict(base_task["thermal"][food], **over)
        if cfg.get("thermal_sources") is not None:
            base_task = dict(base_task, thermal_sources=cfg["thermal_sources"])
        rig.configure_thermal(base_task)
        rig.step(30)
        if cfg.get("start"):
            x0, y0, yaw0 = rig.base_pose()
            x1, y1, yaw1 = cfg["start"]
            dyaw = (yaw1 - yaw0 + 180) % 360 - 180
            n = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) / 0.02), int(abs(dyaw) / 2))
            for u in np.linspace(0, 1, n + 1)[1:]:
                rig.set_base(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, yaw0 + dyaw * u)
                rig.step(1)
        rig.step(120)
        from zeno_skills.skill_runtime import before_snapshot, SkillContractRunner
        start = before_snapshot(rig)
        report["initial_positions"] = {n: [round(v, 3) for v in start["objects"][n]["pos"]]
                                       for n in task.get("watch", []) if n in start["objects"]}
        if planner == "oracle":
            runner = SkillContractRunner(rig)          # GT runner: full state, original behaviour
            session = None
        else:
            from benchmark.session import LimitedSession
            session = LimitedSession(rig, image_dir=out / "images" if images else None)
            runner = session.runner
            report["initial_observation"] = session.observe(image_tag="initial")
        if planner == "recovery":
            from benchmark.planners import load_policy
            pol = load_policy(policy)
            steps_iter = None
            report["calls"] = session.run_planner(pol, task, max_calls=max_calls or task.get("max_calls", 60),
                                                  sink=calls_f)
            report["stop_reason"] = session.stop_reason
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
                    if session is not None:
                        fb = session.call(st["skill"], st.get("args", {}))
                        if task.get("auto_look") and fb["error_code"] == "NOT_IN_VIEW":
                            # probes only: an explicit look at the remembered object, then the call again
                            target = fb["error"].split("'")[1]
                            lk = session.call("look", {"target": target})
                            row = {"index": i, "try": k, "skill": "look", "args": {"target": target}, "expect": "ok",
                                   "role": "auto_look", "note": "", "feedback": lk, "wall_s": 0.0, "tick": rig.tick,
                                   "state": state_summary(rig, task)}
                            report["calls"].append(row)
                            calls_f.write(json.dumps(row, default=float) + "\n")
                            print("CALL", i, k, lk["action"], "OK" if lk["success"] else f"FAIL {lk['error']}",
                                  "(auto look)", flush=True)
                            fb = session.call(st["skill"], st.get("args", {}))
                    else:
                        res = runner.run(st["skill"], st.get("args", {}))
                        fb = {"action": res.action, "success": res.success, "error_code": res.error_code,
                              "error": res.error, "path": res.selected_path}
                    row = {"index": i, "try": k, "skill": st["skill"], "args": st.get("args", {}), "expect": expect,
                           "role": st.get("role", ""), "note": st.get("note", ""), "feedback": fb,
                           "wall_s": round(time.time() - t0, 1), "tick": rig.tick,
                           "state": state_summary(rig, task)}
                    report["calls"].append(row)
                    calls_f.write(json.dumps(row, default=float) + "\n")
                    calls_f.flush()
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
        rig.step(60)
        start["_removed"] = cfg["remove"]
        ok, goal = evaluate_goal(rig, task["goal"], start)
        drops = floor_drops(rig, task, start)
        report["goal"] = goal
        report["dropped"] = drops
        report["final_state"] = state_summary(rig, task)      # side effects for benchmark/evaluate.py
        report["sim_ticks"] = int(rig.tick)                   # 120 ticks per simulated second
        report["task_success"] = bool(ok and not drops and not report.get("route_violation"))
        report["skill_calls"] = len(report["calls"])
        report["skill_failures"] = [c["feedback"]["action"] for c in report["calls"] if not c["feedback"]["success"]]
        report["success"] = report["task_success"]
        for g in goal["all"] + [r for grp in goal["any"] for r in grp]:
            print("GOAL", g["atom"], "OK" if g["holds"] else f"FALSE {g['detail']}", flush=True)
    except Exception as exc:
        report["crash"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        report["incomplete"] = True
        print("CRASH", report["crash"], flush=True)
    finally:
        calls_f.close()
        if rig is not None:
            report["events"] = rig.events[-300:]
            if session is not None:
                report["observation_cache"] = session.observer.cache
                report["images"] = session.observer.images
                report["gate_calls"] = session.runner.calls
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


def state_summary(rig, task):
    st = rig.state()
    out = {"base": [round(v, 3) for v in rig.base_pose()],
           "held": [(rig.held or {}).get("name"), (getattr(rig, "left_held", None) or {}).get("name")]}
    for n in task.get("watch", []):
        if n in st["objects"]:
            sup = rig.geo.support_under(n, st)
            q = st["objects"][n]["quat"]
            yaw = math.degrees(math.atan2(2 * (q[0] * q[3] + q[1] * q[2]), 1 - 2 * (q[2] ** 2 + q[3] ** 2)))
            out[n] = {"pos": [round(v, 3) for v in st["objects"][n]["pos"]], "yaw_deg": round(yaw, 1),
                      "on": sup["name"] if sup else None}
    if rig.thermal is not None:
        out["temp_c"] = {k: round(v, 1) for k, v in rig.thermal.temperatures_c.items()
                         if k in task.get("watch", [])}
    return out


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
                a.difficulty, a.max_calls)


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
            for k in ("route", "variant", "policy", "difficulty", "max_calls"):
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
