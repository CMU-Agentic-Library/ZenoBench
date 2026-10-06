"""Public planning context and failure handoff for an upper-layer VLM.

This module supplies data and validates the handoff. It never chooses a
fallback or treats a relation hint as an executable instruction.
"""

from __future__ import annotations

from typing import Any

from .graph import load_skills, validate_subgraph
from .relations import load_relations


def planner_catalog() -> dict[str, Any]:
    """Return only the semantic fields the planner needs to compose Skills."""
    skills = load_skills()
    return {
        "schema_version": 1,
        "kind": "skill_planner_catalog",
        "skills": [
            {key: spec[key] for key in (
                "skill_id", "name", "description", "args", "requires",
                "achieves", "action_predicate", "availability", "contract_id", "fallback_hints"
            )}
            for spec in skills.values()
        ],
        "relations": load_relations(skills),
    }


def replan_request(
    goal: str,
    graph: dict,
    execution: dict,
    bindings: dict[str, str],
) -> dict[str, Any]:
    """Package a failed run and conditional recovery options for the planner.

    The caller must provide a fresh live execution result. Candidate relations
    are suggestions only; the VLM must inspect the observed state, preserve
    the task goal, and submit a new graph through compile_grounded_nodes.
    """
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal must be nonempty")
    skills = load_skills()
    ordered = validate_subgraph(graph, skills)
    if not isinstance(bindings, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in bindings.items()
    ):
        raise ValueError("bindings must map ref phrases to scene instance IDs")
    if execution.get("status") != "failed":
        raise ValueError("replan_request requires a failed execution")
    results = execution.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("failed execution needs at least one node result")
    failed = results[-1]
    if failed.get("status") != "failed":
        raise ValueError("last result must identify the failed node")
    attempted_ids = [row.get("node_id") for row in results]
    expected_ids = [node["id"] for node in ordered[:len(results)]]
    if attempted_ids != expected_ids or len(results) > len(ordered):
        raise ValueError("execution node IDs do not match the proposed graph")
    if any(row.get("status") != "success" for row in results[:-1]):
        raise ValueError("only the last attempted node may be failed")
    failed_node = ordered[len(results) - 1]
    failed_skill = failed_node["skill_id"]
    if failed.get("skill_id") != failed_skill:
        raise ValueError("failed Skill ID differs from the graph")
    if not isinstance(execution.get("last_observation"), dict):
        raise ValueError("failed execution needs a fresh last_observation")

    relations = [row for row in load_relations(skills)
                 if row["from"] == failed_skill
                 and row["kind"] in ("alternative", "recovery")]
    hints = skills[failed_skill]["fallback_hints"]
    candidate_ids = list(dict.fromkeys(
        [row["to"] for row in relations] + [row["skill_id"] for row in hints]
    ))
    return {
        "schema_version": 1,
        "kind": "skill_replan_request",
        "goal": goal,
        "subgoal_id": graph["subgoal_id"],
        "completed": [
            {"node_id": row["node_id"], "skill_id": row["skill_id"],
             "verified_predicates": row.get("verified_predicates", []),
             "verified_action_predicate": row.get("verified_action_predicate")}
            for row in results[:-1]
        ],
        "failed": {
            "node_id": failed["node_id"],
            "skill_id": failed_skill,
            "args": failed_node["args"],
            "error_code": failed.get("error_code"),
            "error": failed.get("error"),
            "contract_observations": failed.get("contract_observations", {}),
            "requested_action_predicate": failed.get("requested_action_predicate"),
        },
        "unexecuted": [node["id"] for node in ordered[len(results):]],
        "last_observation": execution["last_observation"],
        "bindings": bindings,
        "conditional_relations": relations,
        "fallback_hints": hints,
        "candidate_skills": [
            {key: skills[sid][key] for key in (
                "skill_id", "name", "description", "args", "requires",
                "achieves", "action_predicate", "availability", "contract_id"
            )}
            for sid in candidate_ids
        ],
    }
