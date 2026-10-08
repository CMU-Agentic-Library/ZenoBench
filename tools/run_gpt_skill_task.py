"""Run one ZenoBench task with GPT-selected SkillNode JSON and Contract checks.

Plan/evaluate: GPT reads all public Skill names/descriptions, typed args,
task goal, and compact scene IDs. Its skill_subgraph JSON is grounded and
validated before invoking any Contract. The benchmark evaluator scores the
final simulator state. A failed Contract stops the current graph; GPT may
replan from the measured new state for up to --max-rounds.

For a simulator-only control, --proposal-file uses a saved graph without GPT.
--validate-only checks that file without launching Isaac Sim.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skill_library.gpt_experiment import (compile_proposal, identity_bindings,
                                          planning_payload, request_plan)
from skill_library.graph import GraphValidationError


def _load_proposal(path: Path) -> dict:
    value = json.loads(path.read_text())
    return value.get("graph", value)


def _handle_objects(annotation: dict) -> list[str]:
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    return [row["name"] for row in annotation.get("objects", [])
            if assets.get(row["asset"], {}).get("container", {}).get("handle_collider")]


def _write(out: Path, report: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                                default=float) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, choices=sorted(p.name for p in (ROOT / "tasks").iterdir()
                                                       if (p / "task.json").is_file()))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--model", help="default: OPENAI_MODEL, then gpt-5")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--with-relations", action="store_true",
                        help="include conditional Skill relations; baseline omits them")
    parser.add_argument("--with-predicates", action="store_true",
                        help="show unique action predicates and their verified state facts")
    parser.add_argument("--card-overrides", type=Path,
                        help="GPT-authored name/description JSON by skill_id")
    parser.add_argument("--proposal-file", type=Path,
                        help="simulator control using saved JSON; no GPT call")
    parser.add_argument("--bindings-file", type=Path,
                        help="explicit bindings for --proposal-file control")
    parser.add_argument("--validate-only", action="store_true",
                        help="compile --proposal-file without Isaac Sim")
    args = parser.parse_args()
    if args.max_rounds < 1:
        parser.error("--max-rounds must be positive")
    if args.validate_only and not args.proposal_file:
        parser.error("--validate-only needs --proposal-file")
    if args.bindings_file and not args.proposal_file:
        parser.error("--bindings-file needs --proposal-file")

    task = json.loads((ROOT / "tasks" / args.task / "task.json").read_text())
    annotation = json.loads((ROOT / task["annotation"]).read_text())
    overrides = json.loads(args.card_overrides.read_text()) if args.card_overrides else None
    out = args.out or ROOT / "runs" / "gpt_skill_experiment" / args.task
    out = out if out.is_absolute() else ROOT / out
    report = {
        "task": args.task, "instruction": task["instruction"],
        "model": args.model or os.getenv("OPENAI_MODEL") or "gpt-5",
        "catalog_mode": "+".join(["names_descriptions_args"]
                                 + (["predicates"] if args.with_predicates else [])
                                 + (["relations"] if args.with_relations else [])),
        "card_overrides": str(args.card_overrides) if args.card_overrides else None,
        "proposal_file": str(args.proposal_file) if args.proposal_file else None,
        "success": False, "rounds": [], "status": "not_started",
    }
    control_bindings = json.loads(args.bindings_file.read_text()) if args.bindings_file else None
    if args.proposal_file:
        graph = _load_proposal(args.proposal_file)
        calls = compile_proposal(graph, annotation, control_bindings)
        if len(calls) > 40:
            raise GraphValidationError("proposal exceeds 40 SkillNode calls")
        if args.validate_only:
            report.update(status="validated_only", compiled_calls=calls)
            _write(out, report)
            print(out / "result.json", "VALIDATED", len(calls), flush=True)
            return 0
    elif not os.getenv("OPENAI_API_KEY"):
        report.update(status="not_run_missing_api_key",
                      error="OPENAI_API_KEY is not set in the experiment process")
        _write(out, report)
        print(report["error"], flush=True)
        return 2

    from zeno_skills.runtime import launch, make_rig
    app = launch(video=False)
    rig = None
    t0 = time.time()
    try:
        from zeno_skills.evaluator import TaskEvaluator
        from skill_library.runtime import run_subgraph
        rig = make_rig(app, task["scene_usd"], task["annotation"], video=False,
                       handle_objects=_handle_objects(annotation))
        rig.configure_thermal(task)
        rig.step(60)
        initial_state = rig.state()
        evaluator = TaskEvaluator(task, rig.ann, initial_state=initial_state)
        report["initial"] = evaluator.evaluate(initial_state)
        previous = None
        for index in range(args.max_rounds if not args.proposal_file else 1):
            state = rig.state()
            before = evaluator.evaluate(state)
            if before["success"]:
                break
            round_report = {"index": index + 1, "evaluation_before": before}
            report["rounds"].append(round_report)
            try:
                if args.proposal_file:
                    proposal = graph
                    round_report["source"] = "saved_proposal_control"
                else:
                    payload = planning_payload(task, annotation, state=state,
                                               evaluation=before, previous=previous,
                                               with_relations=args.with_relations,
                                               with_predicates=args.with_predicates,
                                               card_overrides=overrides)
                    round_report["planning_input"] = payload
                    proposal, meta = request_plan(payload, model=args.model)
                    round_report["source"] = "gpt_responses_api"
                    round_report["model_response"] = meta
                round_report["graph"] = proposal
                calls = compile_proposal(proposal, annotation, control_bindings)
                if len(calls) > 40:
                    raise GraphValidationError("proposal exceeds 40 SkillNode calls")
                round_report["compiled_calls"] = calls
            except (ValueError, RuntimeError, KeyError) as exc:
                round_report["status"] = "invalid_plan_or_model_error"
                round_report["error"] = f"{type(exc).__name__}: {exc}"
                previous = {"validation_error": round_report["error"],
                            "last_observation": state, "evaluation": before}
                continue
            execution = run_subgraph(rig, proposal, control_bindings or identity_bindings(proposal))
            round_report["execution"] = execution
            after = evaluator.evaluate(rig.state())
            round_report["evaluation_after"] = after
            round_report["status"] = "task_success" if after["success"] else execution["status"]
            if after["success"]:
                break
            previous = {"evaluation": after, "graph": proposal,
                        "results": [{k: r[k] for k in ("node_id", "action", "status", "error_code", "error")}
                                    for r in execution["results"]]}
            if execution["status"] == "failed":
                previous["replan_request"] = execution["replan_request"]
        report["final"] = evaluator.evaluate(rig.state())
        report["success"] = report["final"]["success"]
        report["status"] = "task_success" if report["success"] else "task_incomplete"
    except Exception as exc:
        report["status"] = "crash"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print("CRASH", report["error"], flush=True)
    finally:
        report["wall_s"] = round(time.time() - t0, 1)
        if rig is not None:
            report["sim_s"] = round(rig.tick / 120, 1)
            report["events"] = rig.events
        _write(out, report)
        print("RESULT", out / "result.json", report["status"], flush=True)
        sys.stdout.flush()
        os._exit(0 if report["success"] else 3)


if __name__ == "__main__":
    raise SystemExit(main())
