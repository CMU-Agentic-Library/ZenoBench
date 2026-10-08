"""Validate an upper-layer skill subgraph (schema 2) and ground its nouns.

A subgraph is the VLM's plan for one subgoal::

    {"schema_version": 2, "kind": "skill_subgraph", "subgoal_id": "serve_soup",
     "nodes": [
       {"id": "n1", "skill": "search", "args": {"object": {"ref": "the pot"}}, "depends_on": []},
       {"id": "n2", "skill": "navigate", "args": {"destination": {"from": "n1.found_on"}}, "depends_on": ["n1"]},
       {"id": "n3", "skill": "uncover", "args": {"container": {"ref": "the pot"}}, "depends_on": ["n2"]}]}

``skill`` is a verb (``pick``) or a SkillNode ID (``skill_017``).  Argument
values are ``{"ref": phrase}`` for scene nouns (grounded through the
``bindings`` map), ``{"value": literal}`` for numbers/vectors/hands, or
``{"from": "<node>.<output>"}`` to use a measured output of an earlier node.
This module uses only the standard library and the exported catalogs.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class GraphValidationError(ValueError):
    """The graph, catalog, or explicit scene binding is invalid."""


def read_json(path):
    return json.loads(Path(path).read_text())


def load_skills(library_dir: str | Path = HERE) -> dict[str, dict]:
    """skill_id -> exported skill.json; checks the one-to-one Contract pairing."""
    root = Path(library_dir)
    index = read_json(root / "catalog.json")
    if index.get("schema_version") != 2 or index.get("kind") != "skill_catalog":
        raise GraphValidationError("catalog must be a schema_version 2 skill_catalog")
    contracts = {c["contract_id"]: c for c in read_json(ROOT / "contract_library/skill_contracts.json")["contracts"]}
    skills = {}
    for entry in index["skills"]:
        spec = read_json(root / entry["definition"])
        cid = spec["contract_id"]
        c = contracts.get(cid)
        if c is None or c["skill_id"] != spec["skill_id"] or c["inputs"] != spec["inputs"] or c["verb"] != spec["verb"]:
            raise GraphValidationError(f"{spec['skill_id']}: Contract {cid} missing or different")
        skills[spec["skill_id"]] = spec
    if len({s["verb"] for s in skills.values()}) != len(skills):
        raise GraphValidationError("verbs must be unique")
    return skills


def by_verb(skills):
    return {s["verb"]: s for s in skills.values()}


def _number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def valid_value(arg_type: str, value: Any) -> bool:
    if arg_type in ("number", "positive_number"):
        return _number(value) and (arg_type == "number" or value > 0)
    if arg_type in ("pose2d", "xy", "unit_vec2"):
        n = 3 if arg_type == "pose2d" else 2
        if not (isinstance(value, list) and len(value) == n and all(map(_number, value))):
            return False
        return arg_type != "unit_vec2" or abs(math.hypot(*value) - 1.0) <= 1e-3
    if arg_type == "hand":
        return value in ("right", "left", "both")
    if arg_type == "tag":
        return isinstance(value, str) and bool(value.strip())
    if arg_type == "object_list":
        return isinstance(value, list) and value and all(isinstance(v, str) for v in value)
    if arg_type == "category_map":
        return isinstance(value, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in value.items())
    return False


def resolve_skill(skills, key):
    if key in skills:
        return skills[key]
    verbs = by_verb(skills)
    if key in verbs:
        return verbs[key]
    raise GraphValidationError(f"unknown skill {key!r}")


def validate_subgraph(graph: dict, skills: dict | None = None) -> list[dict]:
    """Return the nodes in a stable topological order after validation."""
    skills = load_skills() if skills is None else skills
    if not isinstance(graph, dict) or graph.get("schema_version") != 2 or graph.get("kind") != "skill_subgraph":
        raise GraphValidationError("graph must be a schema_version 2 skill_subgraph")
    if set(graph) != {"schema_version", "kind", "subgoal_id", "nodes"}:
        raise GraphValidationError("graph needs schema_version, kind, subgoal_id, nodes only")
    if not isinstance(graph["subgoal_id"], str) or not NAME.fullmatch(graph["subgoal_id"]):
        raise GraphValidationError("subgoal_id must be an identifier")
    nodes = graph["nodes"]
    if not isinstance(nodes, list) or not nodes:
        raise GraphValidationError("nodes must be a non-empty list")
    by_id = {}
    for node in nodes:
        if not isinstance(node, dict) or set(node) != {"id", "skill", "args", "depends_on"}:
            raise GraphValidationError("each node needs id, skill, args, depends_on only")
        if not NAME.fullmatch(str(node["id"])) or node["id"] in by_id:
            raise GraphValidationError(f"duplicate or invalid node id {node['id']!r}")
        spec = resolve_skill(skills, node["skill"])
        args = node["args"]
        required = set(spec["required_inputs"])
        if not isinstance(args, dict) or not required <= set(args) or not set(args) <= set(spec["inputs"]):
            raise GraphValidationError(f"{node['id']}: {spec['verb']} needs {sorted(required)}, "
                                       f"allows {sorted(spec['inputs'])}")
        for k, v in args.items():
            t = spec["inputs"][k]["type"]
            if not isinstance(v, dict) or len(v) != 1:
                raise GraphValidationError(f"{node['id']}.{k}: use {{'ref'}}, {{'value'}} or {{'from'}}")
            (form, item), = v.items()
            if form == "ref":
                if not t.endswith("_ref") or not isinstance(item, str) or not item.strip():
                    raise GraphValidationError(f"{node['id']}.{k}: {t} cannot take a ref")
            elif form == "value":
                if t.endswith("_ref"):
                    if not isinstance(item, str):
                        raise GraphValidationError(f"{node['id']}.{k}: grounded {t} must be a scene name")
                elif not valid_value(t, item):
                    raise GraphValidationError(f"{node['id']}.{k}: invalid {t} value {item!r}")
            elif form == "from":
                if not isinstance(item, str) or "." not in item:
                    raise GraphValidationError(f"{node['id']}.{k}: from must be '<node>.<output>'")
            else:
                raise GraphValidationError(f"{node['id']}.{k}: unknown value form {form}")
        deps = node["depends_on"]
        if not isinstance(deps, list) or len(set(deps)) != len(deps):
            raise GraphValidationError(f"{node['id']}: depends_on must be a list of unique node ids")
        by_id[node["id"]] = node
    for node in nodes:
        for dep in node["depends_on"]:
            if dep not in by_id or dep == node["id"]:
                raise GraphValidationError(f"{node['id']}: bad dependency {dep!r}")
    ordered, done = [], set()
    while len(ordered) < len(nodes):
        ready = next((n for n in nodes if n["id"] not in done and all(d in done for d in n["depends_on"])), None)
        if ready is None:
            raise GraphValidationError("depends_on contains a cycle")
        ordered.append(ready)
        done.add(ready["id"])
    ancestors = {}
    for n in ordered:
        ancestors[n["id"]] = set(n["depends_on"]).union(*[ancestors[d] for d in n["depends_on"]])
        spec = resolve_skill(skills, n["skill"])
        for k, v in n["args"].items():
            if "from" in v:
                src, out = v["from"].split(".", 1)
                if src not in ancestors[n["id"]]:
                    raise GraphValidationError(f"{n['id']}.{k}: {src} is not an ancestor")
                src_spec = resolve_skill(skills, by_id[src]["skill"])
                if out not in src_spec["outputs"]:
                    raise GraphValidationError(f"{n['id']}.{k}: {src_spec['verb']} has no output {out}")
                ot, it = src_spec["outputs"][out]["type"], spec["inputs"][k]["type"]
                if ot != it and not (it in ("place_ref", "entity_ref", "receptacle_ref") and ot.endswith("_ref")) \
                        and not (it == "object_ref" and ot in ("lid_ref", "container_ref")):
                    raise GraphValidationError(f"{n['id']}.{k}: output {ot} does not fit input {it}")
    return ordered


def ground(graph: dict, bindings: dict[str, str], annotation: dict, skills: dict | None = None) -> list[dict]:
    """Ordered calls with every ``ref`` replaced by its scene instance name."""
    skills = load_skills() if skills is None else skills
    ordered = validate_subgraph(graph, skills)
    names = ({o["name"] for o in annotation.get("objects", [])} | {s["name"] for s in annotation.get("supports", [])}
             | {a["name"] for a in annotation.get("articulated", [])} | set(annotation.get("rooms", {}))
             | {a["name"] for a in annotation.get("appliances", [])}
             | {s.get("furniture") for s in annotation.get("supports", []) if s.get("furniture")})
    for a in annotation.get("articulated", []) + annotation.get("appliances", []):
        for b in ("door_button", "start_button", "power_button"):
            if b in a:
                names.add(f"{a['name']}/{b}")
    calls = []
    for n in ordered:
        spec = resolve_skill(skills, n["skill"])
        args = {}
        for k, v in n["args"].items():
            (form, item), = v.items()
            if form == "ref":
                if item not in bindings:
                    raise GraphValidationError(f"{n['id']}.{k}: unbound ref {item!r}")
                item = bindings[item]
                form = "value"
            if form == "value" and spec["inputs"][k]["type"].endswith("_ref") and item not in names:
                raise GraphValidationError(f"{n['id']}.{k}: {item!r} is not in the scene annotation")
            args[k] = {"from": item} if form == "from" else item
        calls.append({"node_id": n["id"], "skill_id": spec["skill_id"], "verb": spec["verb"],
                      "contract_id": spec["contract_id"], "depends_on": n["depends_on"], "args": args})
    return calls


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph", required=True, type=Path)
    ap.add_argument("--bindings", type=Path)
    ap.add_argument("--ann", type=Path)
    args = ap.parse_args()
    graph = read_json(args.graph)
    if args.bindings and args.ann:
        out = ground(graph, read_json(args.bindings), read_json(args.ann))
    else:
        out = [{"node_id": n["id"], "skill": n["skill"]} for n in validate_subgraph(graph)]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
