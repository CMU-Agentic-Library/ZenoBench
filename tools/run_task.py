"""Run a whole task: evaluate the start state, execute the goal-driven
scripted policy, evaluate the end state, record a video.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/run_task.py --task collect_fruits
    # only score the current scene state (no policy): what a learned policy must achieve
    ... tools/run_task.py --task collect_fruits --evaluate-only
    # a task built elsewhere (tools/build_tasks.py --spec ... --out DIR)
    ... tools/run_task.py --task-json DIR/task.json

Output (--out, default runs/<task>): result.json (initial + final
evaluation, every policy decision, skill events), run.mp4.
Exit code 0 = success, 3 = task failed, 4 = crash.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", help="tasks/<task>/task.json")
    ap.add_argument("--task-json", help="path to a task.json")
    ap.add_argument("--out")
    ap.add_argument("--evaluate-only", action="store_true")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--res", nargs=2, type=int, default=[720, 1280])
    ap.add_argument("--stride", type=int, default=4)
    ap.add_argument("--max-rounds", type=int, default=3)
    ap.add_argument("--max-seconds", type=float, default=3600, help="wall-clock budget of the policy")
    args = ap.parse_args()
    tpath = Path(args.task_json) if args.task_json else ROOT / "tasks" / args.task / "task.json"
    task = json.loads(tpath.read_text())
    out = Path(args.out) if args.out else ROOT / "runs" / task["task"]
    out = out if out.is_absolute() else ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    video = not (args.no_video or args.evaluate_only)

    from zeno_skills.runtime import launch
    app = launch(video)
    from zeno_skills.evaluator import TaskEvaluator, format_report
    from zeno_skills.runtime import make_rig
    from zeno_skills.task_policy import TaskPolicy

    report = {"task": task["task"], "seed": task.get("seed"), "instruction": task["instruction"],
              "scene": task["scene_usd"], "success": False,
              "written_state": "robot drive targets and base anchor only"}
    rig, code = None, 4
    t0 = time.time()
    try:
        rig = make_rig(app, task["scene_usd"], task["annotation"], video=video, res=args.res, stride=args.stride)
        rig.caption = f"TASK: {task['instruction']}"
        rig.step(60)
        st0 = rig.state()
        ev = TaskEvaluator(task, rig.ann, initial_state=st0)
        rep0 = ev.evaluate(st0)
        report["initial"] = rep0
        print(format_report(rep0), flush=True)
        if not args.evaluate_only:
            policy = TaskPolicy(rig, task, ev, max_seconds=args.max_seconds)
            try:
                policy.run(max_rounds=args.max_rounds)
            finally:
                report["decisions"] = policy.decisions
            rig.caption = "done"
            rig.step(90)
        rep = ev.evaluate(rig.state())
        report["final"] = rep
        report["success"] = rep["success"]
        report["progress"] = rep["progress"]
        if not args.evaluate_only:
            print(format_report(rep), flush=True)
        code = 0 if rep["success"] else 3
    except Exception as exc:
        report["failure"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print("CRASH", report["failure"], flush=True)
        print(report["traceback"], flush=True)
    finally:
        report["wall_s"] = round(time.time() - t0, 1)
        if rig is not None:
            report["sim_s"] = round(rig.tick / 120, 1)
            report["events"] = rig.events
            if video:
                report["video"] = str(rig.write_video(out / "run.mp4"))
        (out / "result.json").write_text(json.dumps(report, indent=1, default=float))
        print("RESULT", out / "result.json", "SUCCESS", report["success"], "PROGRESS", report.get("progress"),
              flush=True)
        sys.stdout.flush()
        os._exit(code)


if __name__ == "__main__":
    main()
