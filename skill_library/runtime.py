"""Execute a grounded skill subgraph on a live rig and package failures for replanning.

``run_subgraph(rig, graph, bindings)`` runs the nodes in topological order
through SkillContractRunner.  Each node's ``{"from": "<node>.<output>"}``
arguments are filled from measured outputs of earlier nodes.  Execution stops
at the first node whose Contract fails; the result then carries a
``replan_request`` with the measured predicates and the relation-graph
fallback candidates.  Nothing is retried automatically.
"""

from __future__ import annotations

from typing import Any

from .graph import ground, load_skills


def _plain(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def observe(rig) -> dict:
    return {"base_pose": _plain(rig.base_pose()),
            "held_right": rig.held["name"] if rig.held else None,
            "held_left": rig.left_held["name"] if rig.left_held else None,
            "scene_state": _plain(rig.state())}


def run_subgraph(rig, graph: dict, bindings: dict[str, str], *, runner=None) -> dict:
    from zeno_skills.skill_runtime import SkillContractRunner
    skills = load_skills()
    calls = ground(graph, bindings, rig.ann.data, skills)
    runner = runner or SkillContractRunner(rig)
    outputs: dict[str, dict] = {}
    results = []
    for call in calls:
        args = {}
        for k, v in call["args"].items():
            if isinstance(v, dict) and "from" in v:
                src, key = v["from"].split(".", 1)
                args[k] = outputs.get(src, {}).get(key)
            else:
                args[k] = v
        res = runner.run(call["contract_id"], args)
        row = {"node_id": call["node_id"], "skill_id": call["skill_id"], "verb": call["verb"],
               "action": res.action, "status": "success" if res.success else "failed",
               "selected_path": res.selected_path, "preconditions": res.preconditions,
               "postconditions": res.postconditions, "outputs": _plain(res.outputs),
               "error_code": res.error_code, "error": res.error}
        results.append(row)
        if not res.success:
            done = {r["node_id"] for r in results if r["status"] == "success"}
            return {"subgoal_id": graph["subgoal_id"], "status": "failed", "results": results,
                    "replan_request": {
                        "failed_node": call["node_id"], "failed_action": res.action,
                        "error_code": res.error_code, "measured": res.preconditions + res.postconditions,
                        "recovery_candidates": res.recovery,
                        "completed": sorted(done),
                        "unexecuted": [c["node_id"] for c in calls if c["node_id"] not in done | {call["node_id"]}],
                        "observation": observe(rig)}}
        outputs[call["node_id"]] = res.outputs
    return {"subgoal_id": graph["subgoal_id"], "status": "success", "results": results,
            "observation": observe(rig)}
