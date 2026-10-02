"""Run a JSON sequence of semantic contracts on one live Isaac Sim rig.

Plan format: [{"contract": "pick.v1", "route": "round_rim",
               "args": ["cup"], "kwargs": {}}]. Each call binds a real atomic
policy and verifies the measured postcondition before the next call.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--ann", required=True)
    ap.add_argument("--plan", required=True, help="JSON array of contract calls")
    ap.add_argument("--out", required=True)
    ap.add_argument("--video", action="store_true")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    if not isinstance(plan, list) or not all(isinstance(row, dict) for row in plan):
        raise ValueError("contract plan must be a JSON array of call objects")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from zeno_skills.runtime import launch, make_rig
    from zeno_skills.contract_runtime import ContractRunner
    app = launch(args.video)
    rig = None
    runner = None
    report = {"scene": args.scene, "plan": plan, "success": False, "contracts": []}
    try:
        handle_objects = {row["args"][0] for row in plan
                          if row.get("contract") == "pick.v1" and row.get("route") == "cup_handle"}
        rig = make_rig(app, args.scene, args.ann, video=args.video,
                       handle_objects=handle_objects)
        task_path = (ROOT / args.scene).parent / "task.json"
        if task_path.is_file():
            rig.configure_thermal(json.loads(task_path.read_text()))
        rig.step(60)
        runner = ContractRunner(rig)
        for row in plan:
            result = runner.run(row["contract"], row.get("route", "auto"),
                                *row.get("args", []), **row.get("kwargs", {}))
            report["contracts"].append(asdict(result))
        rig.step(60)
        report["success"] = True
    except Exception as exc:
        if runner is not None:
            report["contracts"] = [asdict(item) for item in runner.trace]
        report["failure"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print("FAIL", report["failure"], flush=True)
    finally:
        if rig is not None:
            report["events"] = rig.events
            if args.video:
                report["video"] = str(rig.write_video(out / "run.mp4"))
        (out / "result.json").write_text(json.dumps(report, indent=2, default=float))
        print("RESULT", out / "result.json", "SUCCESS", report["success"], flush=True)
        sys.stdout.flush()
        os._exit(0 if report["success"] else 3)


if __name__ == "__main__":
    main()
