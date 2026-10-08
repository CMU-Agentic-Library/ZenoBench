"""Run SkillNode scenarios in Isaac Sim and record GT-verified results.

    $ISAACLAB_PYTHON tools/verify_skills.py --scenarios skill_library/verification/scenarios.json --id kitchen_pour
    python tools/verify_skills.py --scenarios ... --all --jobs 4      # one Isaac process per scenario

A scenario is a chain of skill calls on one scene::

    {"id": "pick_top", "task": "tasks/kitchen_skills", "start": [2.4, 2.3, 90],
     "steps": [{"skill": "navigate", "args": {"destination": "wooden_block_a"}}, ...]}

Every call goes through SkillContractRunner: preconditions are evaluated on the
live GT state, the noun-selected policy path runs, postconditions are evaluated.
The scenario stops at the first failed step.  Output:
runs/skillv2/verify/<id>/result.json (+ run.mp4 with --video).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "runs/skillv2/verify"


def run_one(sc, video=False, out_root=OUT):
    out = Path(out_root) / sc["id"]
    out.mkdir(parents=True, exist_ok=True)
    from zeno_skills.runtime import launch, make_rig
    from zeno_skills.skill_runtime import SkillContractRunner
    import numpy as np
    app = launch(video)
    task_dir = ROOT / sc["task"]
    task = json.loads((task_dir / "task.json").read_text())
    report = {"id": sc["id"], "task": sc["task"], "steps": [], "success": False, "started": time.time()}
    rig = None
    try:
        rig = make_rig(app, f"{sc['task']}/scene.usd", f"{sc['task']}/annotation.json", video=video,
                       res=(540, 960), handle_objects=tuple(sc.get("handle_objects", ())))
        rig.configure_thermal(task)
        rig.step(30)
        if sc.get("start"):
            # move the anchor in small steps: one large jump makes PhysX explode
            x0, y0, yaw0 = rig.base_pose()
            x1, y1, yaw1 = sc["start"]
            dyaw = (yaw1 - yaw0 + 180) % 360 - 180
            n = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) / 0.02), int(abs(dyaw) / 2))
            for u in np.linspace(0, 1, n + 1)[1:]:
                rig.set_base(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, yaw0 + dyaw * u)
                rig.step(1)
        rig.step(90)
        for name, temp in sc.get("set_temperature", {}).items():
            rig.thermal.temperatures_c[name] = float(temp)
        runner = SkillContractRunner(rig)
        if sc.get("subgraph"):
            # a VLM-format plan: validate, ground and execute through run_subgraph
            from skill_library.runtime import run_subgraph
            graph = json.loads((ROOT / sc["subgraph"]).read_text())
            bindings = json.loads((ROOT / sc["bindings"]).read_text()) if sc.get("bindings") else {}
            res = run_subgraph(rig, graph, bindings, runner=runner)
            for i, r in enumerate(res["results"]):
                report["steps"].append({"index": i, "skill": r["verb"], "action": r["action"],
                                        "success": r["status"] == "success", "path": r["selected_path"],
                                        "error_code": r["error_code"], "error": r["error"],
                                        "preconditions": r["preconditions"], "postconditions": r["postconditions"],
                                        "outputs": r["outputs"], "children": [], "policy_steps": []})
                print("STEP", i, r["action"], "OK" if r["status"] == "success" else f"FAIL {r['error']}", flush=True)
            if res["status"] == "failed":
                report["replan_request"] = res["replan_request"]
            sc = dict(sc, steps=[{}] * len(graph["nodes"]))
        for i, st in enumerate([] if sc.get("subgraph") else sc["steps"]):
            t0 = time.time()
            before = {k: list(v["pos"]) for k, v in rig.state()["objects"].items()}
            held_before, left_before = rig.held, getattr(rig, "left_held", None)
            res = runner.run(st["skill"], st.get("args", {}))
            row = {"index": i, "skill": st["skill"], "action": res.action, "success": res.success,
                   "path": res.selected_path, "error_code": res.error_code, "error": res.error,
                   "preconditions": res.preconditions, "postconditions": res.postconditions,
                   "outputs": res.outputs, "policy_steps": res.policy_steps,
                   "children": [{"action": c["action"], "success": c["success"], "path": c["selected_path"],
                                 "error": c["error"]} for c in res.children],
                   "recovery": res.recovery, "wall_s": round(time.time() - t0, 1), "sim_tick": rig.tick}
            # objects disturbed by the step (moved > 3 cm although not named
            # in its arguments): side effects BC/RL data should not contain
            named = json.dumps(st.get("args", {}))
            st_after = rig.state()
            after = st_after["objects"]
            # contents of a named container (or of the held object) travel with it
            held_now = {(rig.held or {}).get("name"), (getattr(rig, "left_held", None) or {}).get("name"),
                        (held_before or {}).get("name"), (left_before or {}).get("name")} - {None}
            carriers = [o for o in rig.ann.objects if f'"{o}"' in named or o in held_now]
            def rides(k):
                return any(rig.geo.inside(k, c, st_after)[0] for c in carriers if c != k and
                           rig.ann.asset_of(rig.ann.objects[c]).get("container"))
            row["disturbed"] = {k: round(float(np.linalg.norm(np.asarray(after[k]["pos"]) - np.asarray(p0))), 3)
                                for k, p0 in before.items() if k in after and f'"{k}"' not in named
                                and k not in held_now
                                and np.linalg.norm(np.asarray(after[k]["pos"]) - np.asarray(p0)) > 0.03
                                and not rides(k)}
            if row["disturbed"]:
                print("DISTURBED", i, json.dumps(row["disturbed"]), flush=True)
            report["steps"].append(row)
            print("STEP", i, res.action, "OK" if res.success else f"FAIL {res.error_code}: {res.error}",
                  "path", res.selected_path, flush=True)
            if not res.success and not st.get("may_fail"):
                break
        report["success"] = all(r["success"] or (sc["steps"][r["index"]] or {}).get("may_fail")
                                for r in report["steps"]) and len(report["steps"]) == len(sc["steps"])
        if sc.get("goal"):
            # whole-task rollouts: the task goal itself, measured on GT state
            from zeno_skills.predicates import REGISTRY
            rig.step(60)
            ctx = {}
            report["goal"] = []
            for atom in sc["goal"]:
                pred, args = REGISTRY[atom[0]], atom[1:]
                kw = dict(zip(pred.arg_names, args))
                ok, detail = pred.evaluate(rig, ctx, **kw)
                report["goal"].append({"atom": f"{atom[0]}({', '.join(map(str, args))})", "holds": bool(ok),
                                       "detail": str(detail)})
                print("GOAL", atom[0], args, "OK" if ok else f"FALSE {detail}", flush=True)
            report["success"] = report["success"] and all(g["holds"] for g in report["goal"])
    except Exception as exc:
        report["crash"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print("CRASH", report["crash"], flush=True)
    finally:
        if rig is not None:
            report["events"] = rig.events[-400:]
            if video:
                try:
                    report["video"] = str(rig.write_video(out / "run.mp4"))
                except Exception as exc:
                    report["video_error"] = str(exc)
        report["wall_s"] = round(time.time() - report["started"], 1)
        (out / "result.json").write_text(json.dumps(report, indent=1, default=float))
        print("RESULT", sc["id"], "SUCCESS" if report["success"] else "FAILED", flush=True)
        sys.stdout.flush()
        os._exit(0 if report["success"] else 3)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", default=str(ROOT / "skill_library/verification/scenarios.json"))
    ap.add_argument("--id", action="append")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    scenarios = json.loads(Path(args.scenarios).read_text())["scenarios"]
    by_id = {s["id"]: s for s in scenarios}
    if args.id and len(args.id) == 1 and not args.all:
        return run_one(by_id[args.id[0]], args.video, args.out)
    ids = [s["id"] for s in scenarios] if args.all else args.id
    py = os.environ.get("ISAACLAB_PYTHON", sys.executable)
    procs, queue = [], list(ids)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    while queue or procs:
        while queue and len(procs) < args.jobs:
            sid = queue.pop(0)
            log = open(Path(args.out) / f"{sid}.log", "w")
            cmd = [py, __file__, "--scenarios", args.scenarios, "--id", sid, "--out", args.out]
            if args.video:
                cmd.append("--video")
            procs.append((sid, subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                                env=dict(os.environ, OMNI_KIT_ACCEPT_EULA="YES")), time.time()))
        time.sleep(5)
        for item in list(procs):
            sid, p, t0 = item
            if p.poll() is not None:
                procs.remove(item)
                print(sid, "OK" if p.returncode == 0 else f"FAILED({p.returncode})", f"{time.time() - t0:.0f}s",
                      flush=True)
            elif time.time() - t0 > 3600:
                p.kill()
                procs.remove(item)
                print(sid, "TIMEOUT", flush=True)


if __name__ == "__main__":
    main()
