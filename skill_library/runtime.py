"""Execute a grounded Skill Subgraph on one live ZenoBench rig.

The adapter keeps graph node IDs and records a fresh observation after both
successful and failed ContractRunner calls. It does not launch Isaac Sim or
plan a recovery graph; the upper layer owns those operations.
"""

from __future__ import annotations

from typing import Any

from .graph import compile_grounded_nodes


def _plain(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _observation(rig: Any, resolved_args: dict[str, str]) -> dict:
    """Small JSON-compatible state snapshot relevant to the attempted node."""
    result = {
        "base_pose": _plain(rig.base_pose()),
        "held_right": None if rig.held is None else rig.held["name"],
        "held_left": None if rig.left_held is None else rig.left_held["name"],
        "objects": {},
    }
    try:
        result["scene_state"] = _plain(rig.state())
    except Exception:
        pass
    for object_id in sorted({value for value in resolved_args.values()
                             if isinstance(value, str)}):
        try:
            position, quaternion = rig.obj_pose(object_id)
            result["objects"][object_id] = {
                "position": _plain(position),
                "quaternion": _plain(quaternion),
            }
        except Exception as exc:
            result["objects"][object_id] = {"observation_error": str(exc)}
    return result


def run_grounded_nodes(rig: Any, calls: list[dict], *, runner: Any = None) -> dict:
    """Execute in topological order and stop at the first failed node."""
    if runner is None:
        from zeno_skills.contract_runtime import ContractRunner
        runner = ContractRunner(rig)
    results: list[dict] = []
    for call in calls:
        try:
            contract_result = runner.run(
                call["contract"], call["route"], *call["args"]
            )
        except Exception as exc:
            # A failed physical action can move the scene. Include the
            # ContractRunner trace and independently read the live rig.
            trace = getattr(runner, "trace", [])
            last = trace[-1] if trace and trace[-1].contract_id == call["contract"] else None
            result = {
                "node_id": call["node_id"],
                "skill_id": call["skill_id"],
                "contract_id": call["contract"],
                "route": call["route"],
                "status": "failed",
                "error_code": last.error_code if last else type(exc).__name__,
                "error": str(exc),
                "contract_observations": _plain(last.observations) if last else {},
                "verified_predicates": [],
                "observed_state": _observation(rig, call["resolved_args"]),
            }
            results.append(result)
            return {"status": "failed", "results": results,
                    "last_observation": result["observed_state"]}
        result = {
            "node_id": call["node_id"],
            "skill_id": call["skill_id"],
            "contract_id": call["contract"],
            "route": call["route"],
            "status": "success",
            "error_code": None,
            "error": None,
            "contract_observations": _plain(contract_result.observations),
            "verified_predicates": contract_result.observations.get("verified_predicates", []),
            "observed_state": _observation(rig, call["resolved_args"]),
        }
        results.append(result)
    return {
        "status": "success",
        "results": results,
        "last_observation": results[-1]["observed_state"] if results else None,
    }


def run_subgraph(rig: Any, graph: dict, bindings: dict[str, str]) -> dict:
    """Validate, ground, and execute one proposed subgoal graph on a live rig."""
    calls = compile_grounded_nodes(graph, bindings, rig.ann.data)
    result = run_grounded_nodes(rig, calls)
    return {"subgoal_id": graph["subgoal_id"], **result}
