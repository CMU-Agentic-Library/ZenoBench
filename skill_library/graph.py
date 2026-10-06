"""Validate an upper-layer Skill Subgraph and compile grounded contract calls.

This module needs only the Python standard library. It does not start Isaac Sim,
choose a policy route, or claim that natural-language references are grounded
without an explicit binding supplied by the caller.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
from typing import Any


HERE = Path(__file__).resolve().parent
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class GraphValidationError(ValueError):
    """The graph, catalog, or explicit scene binding is invalid."""


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def load_skills(library_dir: str | Path = HERE) -> dict[str, dict]:
    """Load the public SkillNode view and enforce a one-to-one Contract pair."""
    from zeno_skills.node_contracts import NODE_CONTRACTS

    root = Path(library_dir)
    index = read_json(root / "catalog.json")
    if index.get("schema_version") != 1 or index.get("kind") != "skill_catalog":
        raise GraphValidationError("catalog must be a schema_version 1 skill_catalog")
    skills: dict[str, dict] = {}
    seen_contracts = set()
    for entry in index.get("skills", []):
        skill_id = entry.get("skill_id")
        if not isinstance(skill_id, str) or skill_id in skills:
            raise GraphValidationError(f"duplicate or invalid skill ID: {skill_id!r}")
        path = (root / entry["definition"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise GraphValidationError(f"skill definition leaves library: {path}")
        spec = read_json(path)
        if (spec.get("schema_version") != 1 or spec.get("kind") != "skill_node"
                or spec.get("skill_id") != skill_id):
            raise GraphValidationError(f"invalid definition for {skill_id}")
        cid = spec.get("contract_id")
        if cid not in NODE_CONTRACTS or cid in seen_contracts:
            raise GraphValidationError(f"{skill_id}: unknown or reused contract {cid!r}")
        contract = NODE_CONTRACTS[cid]
        if contract["skill_id"] != skill_id or spec.get("args") != contract["inputs"]:
            raise GraphValidationError(f"{skill_id}: Contract pairing or inputs differ")
        if spec.get("achieves") != contract["achieves"] or spec.get("requires") != contract["requires"]:
            raise GraphValidationError(f"{skill_id}: Contract pre/postconditions differ")
        if spec.get("invocation", {}).get("input_order") != contract["legacy_call_args"]:
            raise GraphValidationError(f"{skill_id}: invocation input order differs")
        if spec.get("expected_state_change") != contract["expected_state_change"]:
            raise GraphValidationError(f"{skill_id}: expected state change differs")
        if spec.get("action_predicate") != contract["action_predicate"]:
            raise GraphValidationError(f"{skill_id}: action predicate differs")
        if spec.get("fallback_hints", []) != contract.get("fallback_hints", []):
            raise GraphValidationError(f"{skill_id}: fallback hints differ")
        seen_contracts.add(cid)
        skills[skill_id] = spec
    if not skills:
        raise GraphValidationError("skill catalog is empty")
    if root.resolve() == HERE.resolve():
        if seen_contracts != set(NODE_CONTRACTS):
            raise GraphValidationError("public SkillNode catalog must pair every active Contract")
        from .relations import load_relations
        try:
            load_relations(skills)
        except ValueError as exc:
            raise GraphValidationError(str(exc)) from exc
    return skills


def _valid_value(arg_type: str, item: Any) -> bool:
    """Validate an upper-layer typed literal without invoking the simulator."""
    if not isinstance(item, dict):
        return False
    if arg_type.endswith("_ref"):
        return (set(item) == {"ref"} and isinstance(item["ref"], str)
                and bool(item["ref"].strip()))
    if set(item) != {"value"}:
        return False
    value = item["value"]
    number = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    if arg_type in ("number", "positive_number"):
        return number(value) and (arg_type != "positive_number" or value > 0)
    if arg_type in ("pose2d", "unit_vec2", "xy"):
        length = 3 if arg_type == "pose2d" else 2
        if not isinstance(value, list) or len(value) != length or not all(map(number, value)):
            return False
        return arg_type != "unit_vec2" or abs(math.hypot(*value) - 1.0) <= 1e-3
    return False


def validate_subgraph(graph: dict, skills: dict[str, dict] | None = None) -> list[dict]:
    """Return nodes in stable topological order after structural validation."""
    skills = load_skills() if skills is None else skills
    if not isinstance(graph, dict) or graph.get("schema_version") != 1:
        raise GraphValidationError("graph must use schema_version 1")
    if set(graph) != {"schema_version", "kind", "subgoal_id", "nodes"}:
        raise GraphValidationError("graph needs schema_version, kind, subgoal_id, nodes only")
    if graph.get("kind") != "skill_subgraph":
        raise GraphValidationError("kind must be skill_subgraph")
    if not isinstance(graph.get("subgoal_id"), str) or not NAME.fullmatch(graph["subgoal_id"]):
        raise GraphValidationError("subgoal_id must be a nonempty identifier")
    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise GraphValidationError("nodes must be a nonempty array")

    by_id: dict[str, dict] = {}
    for node in nodes:
        if not isinstance(node, dict) or set(node) != {"id", "skill_id", "args", "depends_on"}:
            raise GraphValidationError("each node needs id, skill_id, args, depends_on only")
        node_id = node["id"]
        if not isinstance(node_id, str) or not NAME.fullmatch(node_id) or node_id in by_id:
            raise GraphValidationError(f"duplicate or invalid node ID: {node_id!r}")
        skill_id = node["skill_id"]
        if not isinstance(skill_id, str) or skill_id not in skills:
            raise GraphValidationError(f"{node_id}: unknown skill_id {skill_id!r}")
        args = node["args"]
        spec_args = skills[skill_id]["args"]
        required = {key for key, value in spec_args.items() if value.get("required")}
        if not isinstance(args, dict) or not required <= set(args) or not set(args) <= set(spec_args):
            raise GraphValidationError(
                f"{node_id}: expected args {sorted(required)}; allowed {sorted(spec_args)}"
            )
        for key, value in args.items():
            arg_type = spec_args[key]["type"]
            if not _valid_value(arg_type, value):
                raise GraphValidationError(f"{node_id}.{key}: invalid {arg_type} argument")
        deps = node["depends_on"]
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
            raise GraphValidationError(f"{node_id}: depends_on must be a list of node IDs")
        if len(set(deps)) != len(deps):
            raise GraphValidationError(f"{node_id}: repeated dependency")
        by_id[node_id] = node

    for node in nodes:
        for dep in node["depends_on"]:
            if dep not in by_id:
                raise GraphValidationError(f"{node['id']}: missing dependency {dep!r}")
            if dep == node["id"]:
                raise GraphValidationError(f"{node['id']}: self dependency")

    # Kahn order preserves the input order among simultaneously ready nodes.
    ordered: list[dict] = []
    done: set[str] = set()
    while len(ordered) < len(nodes):
        ready = next((node for node in nodes
                      if node["id"] not in done
                      and all(dep in done for dep in node["depends_on"])), None)
        if ready is None:
            raise GraphValidationError("depends_on contains a cycle")
        ordered.append(ready)
        done.add(ready["id"])
    return ordered


def compile_grounded_nodes(
    graph: dict,
    bindings: dict[str, str],
    annotation: dict,
    skills: dict[str, dict] | None = None,
) -> list[dict]:
    """Keep graph node IDs while grounding refs to executable contract calls."""
    skills = load_skills() if skills is None else skills
    ordered = validate_subgraph(graph, skills)
    if not isinstance(bindings, dict):
        raise GraphValidationError("bindings must map ref phrases to scene object IDs")
    scene_objects = {obj["name"]: obj for obj in annotation.get("objects", [])}
    if not scene_objects:
        raise GraphValidationError("annotation has no scene objects")
    assets = read_json(HERE.parent / "annotations" / "assets.json")

    calls = []
    for node in ordered:
        skill = skills[node["skill_id"]]
        resolved: dict[str, Any] = {}
        for arg, value in node["args"].items():
            arg_type = skill["args"][arg]["type"]
            if not arg_type.endswith("_ref"):
                resolved[arg] = value["value"]
                continue
            phrase = value["ref"]
            if phrase not in bindings or not isinstance(bindings[phrase], str):
                raise GraphValidationError(f"{node['id']}.{arg}: unresolved ref {phrase!r}")
            instance = bindings[phrase]
            if arg_type in ("object_ref", "container_ref"):
                allowed = scene_objects
            elif arg_type in ("support_ref", "microwave_support_ref"):
                allowed = {row["name"]: row for row in annotation.get("supports", [])}
            elif arg_type in ("articulated_ref", "appliance_ref"):
                allowed = {row["name"]: row for row in annotation.get("articulated", [])}
            else:
                raise GraphValidationError(f"{node['id']}.{arg}: unsupported ref type {arg_type}")
            if instance not in allowed:
                raise GraphValidationError(
                    f"{node['id']}.{arg}: {instance!r} is absent from scene annotation"
                )
            if arg_type == "container_ref":
                asset_name = scene_objects[instance]["asset"]
                if not assets.get(asset_name, {}).get("container"):
                    raise GraphValidationError(
                        f"{node['id']}.{arg}: {instance!r} is not an annotated container"
                    )
            if arg_type == "microwave_support_ref" and allowed[instance].get("furniture") != "kitchen_microwave":
                raise GraphValidationError(
                    f"{node['id']}.{arg}: {instance!r} is not a microwave cavity support"
                )
            if arg_type == "appliance_ref":
                button = "start_button" if node["skill_id"] == "skill_010" else "door_button"
                if button not in allowed[instance]:
                    raise GraphValidationError(
                        f"{node['id']}.{arg}: {instance!r} lacks {button} annotation"
                    )
            resolved[arg] = instance

        order = skill["invocation"]["input_order"]
        call_args = [resolved[arg] for arg in order]
        calls.append({
            "node_id": node["id"],
            "skill_id": node["skill_id"],
            "depends_on": node["depends_on"],
            "resolved_args": resolved,
            "action_predicate": {
                "name": skill["action_predicate"]["name"],
                "arguments": {name: resolved[name] for name in skill["action_predicate"]["arguments"]},
            },
            "contract": skill["contract_id"],
            "route": "compose",
            "args": call_args,
        })
    return calls


def compile_contract_calls(
    graph: dict,
    bindings: dict[str, str],
    annotation: dict,
    skills: dict[str, dict] | None = None,
) -> list[dict]:
    """Create the current run_contracts.py plan format from grounded nodes."""
    return [
        {"contract": call["contract"], "route": call["route"], "args": call["args"]}
        for call in compile_grounded_nodes(graph, bindings, annotation, skills)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--bindings", required=True, type=Path)
    parser.add_argument("--ann", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="write the compiled JSON")
    parser.add_argument("--format", choices=("upper", "legacy"), default="upper",
                        help="upper keeps node IDs; legacy works with run_contracts.py")
    args = parser.parse_args()
    compiler = compile_grounded_nodes if args.format == "upper" else compile_contract_calls
    calls = compiler(read_json(args.graph), read_json(args.bindings), read_json(args.ann))
    result = json.dumps(calls, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result)
        print(args.out)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
