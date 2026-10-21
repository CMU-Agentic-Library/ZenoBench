"""Evaluation-only outcome evidence; no policies, simulator or action sequences.

Final task predicates remain authoritative. Intermediate evidence comes from
logged states or verified postconditions, never from matching a reference route.
Missing evidence is unknown, not a successful outcome.
"""

from __future__ import annotations

import ast
from functools import lru_cache
import json
from pathlib import Path
import re


def parse_atom(text):
    """Accept logged positional or named predicate arguments without evaluating code."""
    match = re.fullmatch(r"([\w ]+)\((.*)\)", str(text).strip())
    if not match:
        return None
    parts, start, depth, quote = [], 0, 0, None
    body = match[2]
    for i, char in enumerate(body):
        if char in "\"'" and (i == 0 or body[i - 1] != "\\"):
            quote = None if quote == char else char if quote is None else quote
        if quote is not None:
            continue
        if char in "[({":
            depth += 1
        elif char in "])}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(body[start:i]); start = i + 1
    if body.strip():
        parts.append(body[start:])
    args = []
    for part in parts:
        part = part.strip()
        if re.match(r"^\w+\s*=", part):
            part = part.split("=", 1)[1].strip()
        try:
            args.append(ast.literal_eval(part))
        except (ValueError, SyntaxError):
            args.append(part)
    return [match[1], *args]


@lru_cache(maxsize=1)
def _contracts():
    root = Path(__file__).resolve().parents[1] / "skill_library" / "skills"
    out = {}
    for path in sorted(root.glob("*/skill.json")):
        spec = json.loads(path.read_text())
        out[spec["verb"]] = spec
        out[spec.get("action_predicate", {}).get("name", spec["verb"])] = spec
    return out


def contract_effects(skill, args, *, path=None):
    """Conjunctions of bound Contract postconditions, one per possible policy path.

Annotation-dependent bindings cannot be inferred offline. Their conjunction is
omitted rather than weakened. This reads definitions, not a successful sequence.
"""
    spec = _contracts().get(skill)
    if spec is None:
        return []
    base = spec.get("postconditions") or []
    paths = spec.get("policy_paths") or [{}]
    selected = [p for p in paths if p.get("path_id") == path] if path else []
    groups = []
    for policy in selected or paths:
        group = []
        for cond in base + (policy.get("extra_postconditions") or []):
            atom = [("not " if cond.get("negated") else "") + cond["name"]]
            for val in cond.get("args", {}).values():
                if isinstance(val, str) and val.startswith("$"):
                    val = args.get(val[1:])
                if val is None or isinstance(val, str) and val.startswith("@"):
                    break
                atom.append(val)
            else:
                group.append(atom)
                continue
            break
        else:
            if group and group not in groups:
                groups.append(group)
    return groups


def post_checks(row):
    """Only proven postconditions; combined feedback checks may include stale preconditions."""
    fb = row.get("feedback") or {}
    if not fb.get("success"):
        return []
    expected = [a for g in contract_effects(row.get("skill"), row.get("args") or {}, path=fb.get("path")) for a in g]
    measured = list(fb.get("postconditions") or []) + [
        c for c in fb.get("checks", []) if parse_atom(c.get("atom")) in expected
    ]
    # A successful Contract guarantees its shared postconditions even in older
    # logs which omitted individual checks. Do not infer path-specific effects.
    groups = contract_effects(row.get("skill"), row.get("args") or {}, path=fb.get("path"))
    shared = [a for a in groups[0] if all(a in g for g in groups)] if groups else []
    return measured + [{"atom": a, "holds": True, "inferred": True} for a in shared
                       if not any(parse_atom(c.get("atom")) == a for c in measured)]


def holds(atom, state=None, checks=()):
    """Three-valued evidence for a predicate. No geometric tolerances are invented."""
    state = state or {}
    name, *args = atom
    value = None
    if name == "holding" and len(args) == 2 and state.get("held") is not None:
        hand, obj = args
        index = {"right": 0, "left": 1}.get(hand)
        if index is not None and len(state["held"]) > index:
            value = state["held"][index] == obj
    elif name == "hand_empty" and len(args) == 1 and state.get("held") is not None:
        index = {"right": 0, "left": 1}.get(args[0])
        if index is not None and len(state["held"]) > index:
            value = state["held"][index] is None
    elif name == "on" and len(args) == 2:
        support = (state.get(args[0]) or {}).get("on")
        if support is not None:
            value = support == args[1]
    elif name == "temperature_at_least" and len(args) == 2:
        temp = (state.get("temp_c") or {}).get(args[0])
        if temp is not None:
            value = temp >= float(args[1])
    # Measured postconditions have precedence over a coarse summary (e.g. holding).
    for check in checks:
        checked = check.get("atom")
        checked = checked if isinstance(checked, list) else parse_atom(checked)
        if checked == atom and isinstance(check.get("holds"), bool) and not (check.get("inferred") and value is not None):
            return check["holds"]
    return value


def all_hold(atoms, state=None, checks=()):
    values = [holds(a, state, checks) for a in atoms]
    if not values or any(v is False for v in values):
        return False
    return True if all(v is True for v in values) else None


def option_groups(option, task):
    """An option is a disjunction of allowed result conjunctions, not skill names."""
    groups = task.get("goal", {}).get("any", [])
    return [groups[i] for i in option.get("groups", []) if 0 <= i < len(groups)] + option.get("outcomes", [])


def recovery_targets(rec):
    """Effects of the failed leaf Contract, even if the retry uses another skill/arguments."""
    skill, args = rec["skill"], rec["args"]
    if rec.get("failed_substep"):
        leaf = rec["failed_substep"][-1]
        match = re.fullmatch(r"([\w]+)\((.*)\)", leaf or "")
        if match:
            parsed = parse_atom(leaf)
            # Leaf actions use named inputs. Split at top-level commas, including list values.
            names = re.findall(r"(?:^|,)\s*(\w+)\s*=", match[2])
            if parsed and len(names) == len(parsed) - 1:
                skill, args = match[1], dict(zip(names, parsed[1:]))
    groups = contract_effects(skill, args, path=rec.get("path"))
    names = {v for v in args.values() if isinstance(v, str)}
    # A generic empty hand alone must not count as delivering a particular object.
    groups = [g for g in groups if any(a[0] != "hand_empty" and any(v in names for v in a[1:] if isinstance(v, str))
                                     for a in g)]
    if rec.get("skill") == "pick" and rec["args"].get("hands") == "both":
        extra = ["holding", "left", rec["args"].get("object")]
        groups = [g + [extra] if extra not in g else g for g in groups]
    return groups
