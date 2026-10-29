"""SKILL.md schema: the JSON schema (skill_ext/skill.schema.json) and the checks behind it.

A small validator for the JSON-schema subset the file uses (type, required, properties,
additionalProperties, enum, pattern, items, minItems, oneOf), so the Isaac Sim interpreter needs
no extra package, plus the semantic checks a schema cannot express: every predicate exists, every
``$param`` an atom names is declared, a scripted step names a known skill.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("skill.schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())

# parameter types: the built-in contracts' input types plus plain JSON values
PARAM_TYPES = ("place_ref", "object_list", "object_ref", "unit_vec2", "support_ref", "number", "button_ref",
               "lid_ref", "xy", "pose2d", "receptacle_ref", "room_ref", "appliance_ref", "tag", "hand",
               "articulated_ref", "category_map", "entity_ref", "tool_ref", "furniture_ref", "positive_number",
               "container_ref", "string", "integer", "boolean")
EXECUTOR_TYPES = ("scripted", "python", "vla", "rl", "scripted_policy")

_ATOM = re.compile(r"^\s*(not\s+)?([a-z_][a-z0-9_]*)\s*\((.*)\)\s*$")


class SkillSchemaError(ValueError):
    def __init__(self, where: str, errors: list[str]):
        self.where, self.errors = where, list(errors)
        super().__init__(f"{where}: " + "; ".join(self.errors))


# ----------------------------------------------------------------- JSON-schema subset
_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _type_ok(value, t):
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[t])


def check(value, schema, path="$", defs=None) -> list[str]:
    defs = SCHEMA.get("$defs", {}) if defs is None else defs
    if "$ref" in schema:
        return check(value, defs[schema["$ref"].rsplit("/", 1)[-1]], path, defs)
    errs = []
    if "oneOf" in schema:
        if sum(not check(value, s, path, defs) for s in schema["oneOf"]) != 1:
            return [f"{path}: matches none (or several) of the allowed forms"]
        return []
    t = schema.get("type")
    if t is not None:
        ts = t if isinstance(t, list) else [t]
        if not any(_type_ok(value, x) for x in ts):
            return [f"{path}: expected {'/'.join(ts)}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        errs.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errs.append(f"{path}: shorter than {schema['minLength']}")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                errs.append(f"{path}: missing {k!r}")
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for k, v in value.items():
            if k in props:
                errs += check(v, props[k], f"{path}.{k}", defs)
            elif extra is False:
                errs.append(f"{path}: unknown field {k!r}")
            elif isinstance(extra, dict):
                errs += check(v, extra, f"{path}.{k}", defs)
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errs.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "items" in schema:
            for i, v in enumerate(value):
                errs += check(v, schema["items"], f"{path}[{i}]", defs)
    return errs


# ----------------------------------------------------------------- atoms
def parse_atom(atom) -> dict:
    """``"holding(hand=right)"`` / ``"not on(object=$object, support=$support)"`` / {"pred", "args",
    "negated"} -> {"pred", "args", "negated"} (the built-in contracts' form, ``$slot`` references kept)."""
    if isinstance(atom, dict):
        return {"pred": atom["pred"], "args": dict(atom.get("args", {})), "negated": bool(atom.get("negated"))}
    m = _ATOM.match(atom)
    if not m:
        raise ValueError(f"not a predicate atom: {atom!r}")
    args = {}
    for part in filter(None, (p.strip() for p in _split_args(m.group(3)))):
        if "=" not in part:
            raise ValueError(f"{atom!r}: argument {part!r} must be name=value")
        k, v = (x.strip() for x in part.split("=", 1))
        args[k] = _literal(v)
    return {"pred": m.group(2), "args": args, "negated": bool(m.group(1))}


def _split_args(s):
    depth, cur = 0, ""
    for ch in s:
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth -= 1
        if ch == "," and depth == 0:
            yield cur
            cur = ""
        else:
            cur += ch
    yield cur


def _literal(v: str):
    if v.startswith("$") or v.startswith("@"):
        return v
    try:
        return json.loads(v)
    except ValueError:
        return v.strip("'\"")


def atom_text(a: dict) -> str:
    return ("not " if a.get("negated") else "") + a["pred"] + "(" + ", ".join(
        f"{k}={v}" for k, v in a["args"].items()) + ")"


# ----------------------------------------------------------------- the spec
def validate_spec(spec: dict, where: str = "SKILL.md", *, predicates=None, builtin_verbs=()) -> dict:
    """Schema + semantic checks.  Returns the normalised spec (atoms parsed); raises SkillSchemaError
    listing every problem at once."""
    errs = check(spec, SCHEMA)
    if errs:
        raise SkillSchemaError(where, errs)
    if predicates is None:
        from skill_ext.predicates import predicate_names
        predicates = predicate_names()
    params = spec.get("parameters", {})
    norm = dict(spec)
    for key in ("preconditions", "effects"):
        rows = []
        for i, a in enumerate(spec.get(key, [])):
            try:
                p = parse_atom(a)
            except ValueError as exc:
                errs.append(f"{key}[{i}]: {exc}")
                continue
            if p["pred"] not in predicates:
                errs.append(f"{key}[{i}]: unknown predicate {p['pred']!r}")
            for k, v in p["args"].items():
                if isinstance(v, str) and v.startswith("$") and v[1:] not in params:
                    errs.append(f"{key}[{i}]: {k}={v} names no declared parameter")
            rows.append(p)
        norm[key] = rows
    ex = spec["executor"]
    if ex["type"] == "scripted":
        if not ex.get("steps"):
            errs.append("executor: a scripted executor needs steps")
        for i, st in enumerate(ex.get("steps", [])):
            if builtin_verbs and st["skill"] not in builtin_verbs and st["skill"] != spec["name"]:
                # a step may also call another user skill; the registry checks those when it resolves
                norm.setdefault("_calls_user_skills", []).append(st["skill"])
            for k, v in st.get("args", {}).items():
                if isinstance(v, str) and v.startswith("$") and v[1:] not in params:
                    errs.append(f"executor.steps[{i}].args.{k}={v} names no declared parameter")
            if st["skill"] == spec["name"]:
                errs.append(f"executor.steps[{i}]: a skill cannot call itself")
    elif not ex.get("entry"):
        errs.append(f"executor: a {ex['type']} executor needs entry (file.py:Class or module:Class)")
    if spec["name"] in builtin_verbs:
        errs.append(f"name {spec['name']!r} is a built-in skill; user skills cannot replace built-ins")
    if errs:
        raise SkillSchemaError(where, errs)
    return norm
