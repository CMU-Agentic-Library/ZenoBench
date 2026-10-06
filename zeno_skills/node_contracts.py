"""Static, one-to-one SkillNode contracts and policy sequences."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import re


SOURCE = Path(__file__).with_name("node_contracts.json")

CUSTOM_VERIFIER_PREDICATES = {
    "edge_ready": {"edge_overhang_ready"},
    "upright": {"object_upright"},
    "temperature": {"temperature_at_least"},
    "carry_height": {"held_object_above_height"},
    "back_off": {"base_backed_off", "grasp_preserved"},
    "base_rotate": {"base_yaw_changed"},
    "base_translate": {"base_translated_locally"},
    "floor_reach": {"floor_reach_ready"},
    "microwave_clear": {"microwave_sweep_clear"},
}
EXTRA_CHECK_PREDICATES = {
    "upright": {"object_upright"},
    "within_hint": {"within_hint_radius"},
}



def load_node_contracts(path: Path = SOURCE) -> dict[str, dict]:
    catalog = json.loads(path.read_text())
    if catalog.get("schema_version") != 1 or catalog.get("kind") != "skill_contract_catalog":
        raise ValueError("invalid Skill Contract catalog")
    policy_catalog = json.loads((path.parent / "policies" / "catalog.json").read_text())
    policies = {row["policy_id"]: row for row in policy_catalog["policies"]}
    result = {}
    skills = set()
    action_verbs = set()
    from .contracts import CONTRACTS
    from .interface_ids import resolve_contract_id
    from .policies import PolicySuite
    suite = PolicySuite(None)
    for row in catalog["contracts"]:
        cid, sid = row["contract_id"], row["skill_id"]
        if cid in result or sid in skills or row.get("kind") != "skill_contract":
            raise ValueError(f"duplicate or invalid Skill Contract {cid}")
        skills.add(sid)
        verifier = row["verifier"]
        family = resolve_contract_id(verifier["legacy_family_contract"]) if verifier.get("legacy_family_contract") else None
        route = verifier.get("route")
        custom = verifier.get("custom")
        if family is not None and (family not in CONTRACTS or route not in CONTRACTS[family].executor):
            raise ValueError(f"{cid}: unknown verifier route")
        if family is None and custom not in CUSTOM_VERIFIER_PREDICATES:
            raise ValueError(f"{cid}: unknown custom verifier")
        if family is not None and custom is not None:
            raise ValueError(f"{cid}: choose one primary verifier")
        inputs = row["inputs"]
        if (not isinstance(inputs, dict) or set(row["legacy_call_args"]) != set(inputs)
                or len(row["legacy_call_args"]) != len(inputs)):
            raise ValueError(f"{cid}: invalid input order")
        for name in row["argument_transforms"]:
            if name not in inputs:
                raise ValueError(f"{cid}: invalid argument transform")
        noun_bindings = row.get("noun_bindings", {})
        noun_inputs = {name for name, meta in inputs.items() if meta["type"].endswith("_ref")}
        if set(noun_bindings) != noun_inputs:
            raise ValueError(f"{cid}: noun slots must match reference inputs")
        for name, binding in noun_bindings.items():
            if binding.get("argument") != name or binding.get("kind") not in {
                    "scene_object", "container", "support", "articulated"}:
                raise ValueError(f"{cid}: invalid noun binding for {name}")
        family_order = verifier.get("family_arg_order", row["legacy_call_args"])
        if not isinstance(family_order, list) or any(name not in inputs for name in family_order):
            raise ValueError(f"{cid}: invalid verifier argument order")
        plan = row["policy_plan"]
        if plan.get("kind") == "sequence":
            paths = [{"path_id": "fixed", "steps": plan.get("steps", [])}]
        elif plan.get("kind") == "choice":
            paths = plan.get("paths", [])
            if plan.get("selection") != "first_matching_before_execution" or not paths:
                raise ValueError(f"{cid}: invalid noun-conditioned policy choice")
        else:
            raise ValueError(f"{cid}: unknown policy plan kind")
        path_ids = set()
        for path in paths:
            if not path.get("path_id") or path["path_id"] in path_ids or not path.get("steps"):
                raise ValueError(f"{cid}: duplicate or empty policy path")
            path_ids.add(path["path_id"])
            if plan["kind"] == "choice":
                if not path.get("when"):
                    raise ValueError(f"{cid}: conditional path needs noun tests")
                for condition in path["when"]:
                    if (condition.get("noun") not in noun_bindings
                            or condition.get("field") not in {
                                "grasp_types", "on_floor", "location", "handle_collider",
                                "powered_microwave", "type", "has_handle", "furniture",
                                "held_kind", "kind"}
                            or ("equals" in condition) == ("contains" in condition)):
                        raise ValueError(f"{cid}: invalid noun path condition")
            for step in path["steps"]:
                pid = step["policy_id"]
                if pid not in policies:
                    raise ValueError(f"{cid}: unknown policy {pid}")
                for arg in step["args"]:
                    if set(arg) != {"arg"} or arg["arg"] not in inputs:
                        raise ValueError(f"{cid}: invalid policy argument")
                policy = getattr(suite, pid)
                sig = inspect.signature(policy.execute)
                placeholder = [None for _ in step["args"]]
                bound_kwargs = {}
                for name, value in step.get("kwargs", {}).items():
                    if isinstance(value, dict):
                        if set(value) != {"arg"} or value["arg"] not in inputs:
                            raise ValueError(f"{cid}: invalid dynamic keyword argument")
                        bound_kwargs[name] = None
                    else:
                        bound_kwargs[name] = value
                try:
                    sig.bind(*placeholder, **bound_kwargs)
                except TypeError as exc:
                    raise ValueError(f"{cid}: invalid {pid} call: {exc}") from exc
        # Each advertised effect must be backed by a measured verifier.
        guaranteed = set(CUSTOM_VERIFIER_PREDICATES.get(custom, set()))
        if family is not None:
            for item in CONTRACTS[family].profile["achieves"]:
                if item["check"] != "runner":
                    continue
                when = item.get("when")
                is_container = row["argument_transforms"].get("container") == "in:"
                if when == "target starts with in:" and not is_container:
                    continue
                if when == "target does not start with in:" and is_container:
                    continue
                if when == "button is start" and route != "start":
                    continue
                guaranteed.add(item["predicate"])
        for check in verifier.get("extra_checks", []):
            if check not in EXTRA_CHECK_PREDICATES:
                raise ValueError(f"{cid}: unknown extra check {check}")
            guaranteed.update(EXTRA_CHECK_PREDICATES[check])
        claims = {item["predicate"] for item in row["achieves"]}
        if row.get("expected_state_change") != [item["predicate"] for item in row["achieves"]]:
            raise ValueError(f"{cid}: expected state change differs from postconditions")
        action = row.get("action_predicate")
        if not isinstance(action, dict) or set(action) != {
                "name", "verb", "noun", "arguments", "verified_by"}:
            raise ValueError(f"{cid}: invalid action predicate")
        verb, noun = action["verb"], action["noun"]
        if (not isinstance(verb, str) or not re.fullmatch(r"[a-z]+", verb)
                or not isinstance(noun, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", noun)
                or action["name"] != f"{verb}_{noun}" or verb in action_verbs
                or action["arguments"] != row["legacy_call_args"]
                or action["verified_by"] != row["expected_state_change"]):
            raise ValueError(f"{cid}: action predicate must be unique verb+noun with verified inputs")
        action_verbs.add(verb)
        if not claims <= guaranteed:
            raise ValueError(f"{cid}: unverified postconditions {claims-guaranteed}")
        result[cid] = row
    for cid, row in result.items():
        for hint in row.get("fallback_hints", []):
            if hint.get("skill_id") not in skills or not hint.get("when"):
                raise ValueError(f"{cid}: unknown or unconditional fallback hint")
    return result


NODE_CONTRACTS = load_node_contracts()
