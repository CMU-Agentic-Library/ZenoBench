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
    ap.add_argument("--start-base", nargs=3, type=float,
                    metavar=("X", "Y", "YAW_DEG"),
                    help="optional local robot start pose for a reproducible smoke run")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    if not isinstance(plan, list) or not all(isinstance(row, dict) for row in plan):
        raise ValueError("contract plan must be a JSON array of call objects")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    from zeno_skills.runtime import launch, make_rig
    from zeno_skills.contract_runtime import ContractRunner
    from zeno_skills.interface_ids import resolve_contract_id
    app = launch(args.video)
    rig = None
    runner = None
    step_index = -1
    report = {"scene": args.scene, "plan": plan, "start_base": args.start_base,
              "success": False, "contracts": []}
    try:
        handle_objects = {row["args"][0] for row in plan
                          if (resolve_contract_id(row.get("contract", "")) == "pick.v1"
                              and row.get("route") == "cup_handle")
                          or row.get("contract") == "contract_025"}
        rig = make_rig(app, args.scene, args.ann, video=args.video,
                       handle_objects=handle_objects)
        task_path = (ROOT / args.scene).parent / "task.json"
        if task_path.is_file():
            rig.configure_thermal(json.loads(task_path.read_text()))
        if args.start_base is not None:
            rig.set_base(*args.start_base)
        rig.step(60)
        runner = ContractRunner(rig)
        for step_index, row in enumerate(plan):
            if "policy" in row:
                from zeno_skills.policies import PolicySuite
                from zeno_skills.interface_ids import resolve_policy_id
                policy_id = row["policy"]
                getattr(PolicySuite(rig), resolve_policy_id(policy_id)).execute(
                    *row.get("args", []), **row.get("kwargs", {}))
                report.setdefault("preparation_policies", []).append(policy_id)
                continue
            result = runner.run(row["contract"], row.get("route", "auto"),
                                *row.get("args", []), **row.get("kwargs", {}))
            report["contracts"].append(asdict(result))
        rig.step(60)
        report["success"] = True
    except Exception as exc:
        if runner is not None:
            report["contracts"] = [asdict(item) for item in runner.trace]
        report["failure"] = f"{type(exc).__name__}: {exc}"
        report["unreached_contracts"] = [row["contract"] for row in plan[step_index + 1:]
                                         if "contract" in row]
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
