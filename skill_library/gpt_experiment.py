"""Names-and-descriptions GPT planning baseline for the ZenoBench task set.

The model sees public Skill names/descriptions plus typed argument signatures,
not Contract plans or low-level policies. Its JSON is validated and grounded
before any simulator action. This module has no Isaac Sim dependency.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any

from .graph import compile_grounded_nodes, load_skills
from .relations import load_relations

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "gpt-5"


def skill_cards(*, overrides: dict[str, dict] | None = None,
                with_predicates: bool = False) -> list[dict]:
    """Give GPT all 50 names/descriptions and the minimum callable signature."""
    skills = load_skills()
    overrides = overrides or {}
    if not set(overrides) <= set(skills):
        raise ValueError("card overrides contain unknown skill IDs")
    result = []
    for sid, skill in skills.items():
        card = {
            "skill_id": sid,
            "name": skill["name"],
            "description": skill["description"],
            "args": {key: {"type": value["type"], "required": value["required"]}
                     for key, value in skill["args"].items()},
        }
        if with_predicates:
            card["action_predicate"] = skill["action_predicate"]
        if sid in overrides:
            replacement = overrides[sid]
            if set(replacement) != {"name", "description"} or any(
                not isinstance(replacement[key], str) or not replacement[key].strip()
                for key in ("name", "description")
            ):
                raise ValueError(f"{sid}: override needs nonempty name and description")
            card.update(replacement)
        result.append(card)
    names = [row["name"].casefold() for row in result]
    if len(set(names)) != len(names):
        raise ValueError("Skill cards have duplicate names")
    return result


def _goal_supports(goal: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(goal, dict):
        for key, value in goal.items():
            if key == "support":
                if isinstance(value, str):
                    found.add(value)
                elif isinstance(value, list):
                    found.update(item for item in value if isinstance(item, str))
            else:
                found |= _goal_supports(value)
    elif isinstance(goal, list):
        for item in goal:
            found |= _goal_supports(item)
    return found


def task_scene_view(task: dict, annotation: dict, state: dict | None = None) -> dict:
    """Compact grounding vocabulary; IDs are copied exactly from annotations."""
    wanted = _goal_supports(task["goal"])
    wanted.update(row.get("support") for row in annotation.get("objects", [])
                  if isinstance(row.get("support"), str))
    supports = [row for row in annotation.get("supports", [])
                if row["name"] in wanted or row.get("furniture") in wanted
                or row.get("furniture") == "kitchen_microwave"]
    objects = []
    for row in annotation.get("objects", []):
        current = (state or {}).get("objects", {}).get(row["name"], {})
        objects.append({"name": row["name"], "asset": row["asset"],
                        "support": row.get("support"),
                        "position": current.get("pos", row.get("position"))})
    return {
        "objects": objects,
        "supports": [{key: row.get(key) for key in ("name", "furniture", "z", "aabb_xy")}
                     for row in supports],
        "articulated": [{key: row.get(key) for key in ("name", "category", "type")}
                        for row in annotation.get("articulated", [])],
        "roles": task.get("roles", {}),
        "alternatives": task.get("alternatives", []),
        "place_hints": task.get("place_hints", {}),
        "robot_start": task.get("robot_start"),
    }


def identity_bindings(graph: dict) -> dict[str, str]:
    """The baseline uses exact scene IDs as refs to avoid unmeasured grounding."""
    return {value["ref"]: value["ref"]
            for node in graph.get("nodes", [])
            for value in node.get("args", {}).values()
            if isinstance(value, dict) and isinstance(value.get("ref"), str)}


def compile_proposal(graph: dict, annotation: dict,
                     bindings: dict[str, str] | None = None) -> list[dict]:
    return compile_grounded_nodes(graph, bindings or identity_bindings(graph), annotation)


PLAN_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["graph"],
    "properties": {"graph": {
        "type": "object", "additionalProperties": False,
        "required": ["schema_version", "kind", "subgoal_id", "nodes"],
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "kind": {"type": "string", "enum": ["skill_subgraph"]},
            "subgoal_id": {"type": "string"},
            "nodes": {"type": "array", "minItems": 1, "items": {
                "type": "object", "additionalProperties": False,
                "required": ["id", "skill_id", "args", "depends_on"],
                "properties": {
                    "id": {"type": "string"},
                    "skill_id": {"type": "string"},
                    "args": {"type": "object", "additionalProperties": {
                        "type": "object", "properties": {
                            "ref": {"type": "string"},
                            "value": {"anyOf": [
                                {"type": "number"},
                                {"type": "array", "items": {"type": "number"}}]},
                        }}},
                    "depends_on": {"type": "array", "items": {"type": "string"}},
                },
            }},
        },
    }},
}


def planning_payload(task: dict, annotation: dict, *, state: dict | None = None,
                     evaluation: dict | None = None, previous: dict | None = None,
                     with_relations: bool = False,
                     with_predicates: bool = False,
                     card_overrides: dict[str, dict] | None = None) -> dict:
    payload = {
        "task": task["task"], "instruction": task["instruction"],
        "goal": task["goal"], "scene": task_scene_view(task, annotation, state),
        "evaluation": evaluation, "skills": skill_cards(
            overrides=card_overrides, with_predicates=with_predicates),
        "previous_attempt": previous,
    }
    if with_relations:
        payload["conditional_relations"] = load_relations(load_skills())
    return payload


SYSTEM_PROMPT = """You plan ZenoBench robot tasks using only the provided Skill catalog.
Return one JSON object with key graph containing a skill_subgraph. Use only listed
skill_ids and valid args. Every ref MUST be an exact object, support, or articulated
name from the scene vocabulary; do not invent IDs. A ref is {"ref":"exact ID"};
a numeric or vector literal is {"value":number_or_array}. depends_on names
prior graph node IDs. Order manipulation of one right-hand-held object correctly.
Plan toward the unchanged task goal, including closure and terminal invariants.
Only the current simulator state and evaluation are authoritative. If a prior
attempt failed, revise from the new state; do not assume its effects succeeded.
Choose at most 32 nodes. Output JSON only. Do not claim physical success."""


def _response_text(response: dict) -> str:
    chunks = [part["text"] for item in response.get("output", [])
              if item.get("type") == "message"
              for part in item.get("content", [])
              if part.get("type") == "output_text" and "text" in part]
    if response.get("status") != "completed" or not chunks:
        raise RuntimeError(f"GPT response incomplete: {response.get('status')}, "
                           f"{response.get('incomplete_details')}")
    return "".join(chunks)


def request_json(system_prompt: str, payload: dict, *, schema: dict,
                 schema_name: str, model: str | None = None,
                 timeout_s: float = 180) -> tuple[dict, dict]:
    """Call the Responses API using stdlib; never persist or echo the API key."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the experiment process")
    model = model or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL
    body = {
        "model": model,
        "input": [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=float)},
        ],
        "text": {"format": {"type": "json_schema", "name": schema_name,
                            "schema": schema, "strict": False}},
        "max_output_tokens": 10000,
        "store": False,
    }
    url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    request = urllib.request.Request(
        url + "/responses", data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": "Bearer " + api_key,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as handle:
            response = json.load(handle)
    except urllib.error.HTTPError as exc:
        message = exc.read(1000).decode("utf-8", "replace")
        raise RuntimeError(f"GPT HTTP {exc.code}: {message}") from exc
    proposal = json.loads(_response_text(response))
    if not isinstance(proposal, dict):
        raise ValueError("GPT response must be a JSON object")
    return proposal, {"model": response.get("model", model), "usage": response.get("usage"),
                      "response_id": response.get("id")}


def request_plan(payload: dict, *, model: str | None = None) -> tuple[dict, dict]:
    proposal, meta = request_json(SYSTEM_PROMPT, payload, schema=PLAN_SCHEMA,
                                  schema_name="zenobench_skill_plan", model=model)
    if set(proposal) != {"graph"} or not isinstance(proposal["graph"], dict):
        raise ValueError("GPT response must contain exactly one graph object")
    return proposal["graph"], meta
