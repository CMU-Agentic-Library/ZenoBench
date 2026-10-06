"""Run the same GPT Skill-planning protocol on all built ZenoBench tasks.

Each task gets a fresh Isaac Sim process. Per-task result.json and simulator.log
are preserved; summary.json distinguishes planning errors, Contract failures,
and final TaskEvaluator success. Requires OPENAI_API_KEY in the process env.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TASKS = tuple(sorted(p.name for p in (ROOT / "tasks").iterdir()
                     if (p / "task.json").is_file()))


def _python_launcher(explicit: str | None) -> str:
    if explicit:
        return explicit
    if os.getenv("ISAACLAB_PYTHON"):
        return os.environ["ISAACLAB_PYTHON"]
    if importlib.util.find_spec("isaaclab"):
        return sys.executable
    raise RuntimeError("set --python or ISAACLAB_PYTHON to an IsaacLab Python executable")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=list(TASKS))
    parser.add_argument("--python", help="IsaacLab Python executable")
    parser.add_argument("--model", help="default: OPENAI_MODEL, then gpt-5")
    parser.add_argument("--out", type=Path, default=ROOT / "runs/gpt_skill_experiment/batch")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--timeout-s", type=int, default=5400)
    parser.add_argument("--with-relations", action="store_true")
    parser.add_argument("--with-predicates", action="store_true")
    parser.add_argument("--card-overrides", type=Path)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    summary = {"model": args.model or os.getenv("OPENAI_MODEL") or "gpt-5",
               "catalog_mode": "+".join(["names_descriptions_args"]
                                        + (["predicates"] if args.with_predicates else [])
                                        + (["relations"] if args.with_relations else [])),
               "tasks": {}, "successes": 0, "requested": list(args.tasks)}
    if not os.getenv("OPENAI_API_KEY"):
        summary["status"] = "not_run_missing_api_key"
        summary["tasks"] = {task: {"status": "not_run_missing_api_key"} for task in args.tasks}
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print("OPENAI_API_KEY is not set; no GPT task rollouts were run", flush=True)
        return 2
    python = _python_launcher(args.python)
    for task in args.tasks:
        run_dir = out / task
        run_dir.mkdir(parents=True, exist_ok=True)
        command = [python, str(ROOT / "tools/run_gpt_skill_task.py"), "--task", task,
                   "--out", str(run_dir), "--max-rounds", str(args.max_rounds)]
        if args.model:
            command += ["--model", args.model]
        if args.with_relations:
            command.append("--with-relations")
        if args.with_predicates:
            command.append("--with-predicates")
        if args.card_overrides:
            command += ["--card-overrides", str(args.card_overrides)]
        log_path = run_dir / "simulator.log"
        try:
            with log_path.open("w") as log:
                process = subprocess.run(command, cwd=ROOT, env={**os.environ,
                                         "OMNI_KIT_ACCEPT_EULA": "YES"},
                                         stdout=log, stderr=subprocess.STDOUT,
                                         timeout=args.timeout_s, check=False)
            result_path = run_dir / "result.json"
            if result_path.exists():
                result = json.loads(result_path.read_text())
                summary["tasks"][task] = {
                    "status": result["status"], "success": result["success"],
                    "initial_progress": result.get("initial", {}).get("progress"),
                    "final_progress": result.get("final", {}).get("progress"),
                    "rounds": len(result.get("rounds", [])),
                    "contract_failures": sum(
                        1 for rnd in result.get("rounds", [])
                        for node in rnd.get("execution", {}).get("results", [])
                        if node["status"] == "failed"),
                    "invalid_plans": sum(rnd.get("status") == "invalid_plan_or_model_error"
                                         for rnd in result.get("rounds", [])),
                    "exit_code": process.returncode,
                    "result": str(result_path.relative_to(out)),
                }
                summary["successes"] += bool(result["success"])
            else:
                summary["tasks"][task] = {"status": "process_exited_without_result",
                                           "exit_code": process.returncode}
        except subprocess.TimeoutExpired:
            summary["tasks"][task] = {"status": "timeout", "timeout_s": args.timeout_s}
        (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(task, summary["tasks"][task]["status"], flush=True)
    summary["status"] = "complete"
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("SUCCESS", summary["successes"], "/", len(args.tasks), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
