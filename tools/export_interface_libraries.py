"""Export reviewable per-item Contract and low-level Policy records.

The executable registries remain the source of truth. Generated JSON/Markdown
use stable public IDs and preserve the old names as explicit compatibility
aliases. Run with --check to detect stale exported records.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _json(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _signature(policy):
    fields = []
    for parameter in inspect.signature(policy.execute).parameters.values():
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            fields.append({"name": parameter.name, "kind": str(parameter.kind), "required": False})
            continue
        row = {
            "name": parameter.name,
            "kind": "keyword_only" if parameter.kind == parameter.KEYWORD_ONLY else "positional_or_keyword",
            "required": parameter.default is parameter.empty,
        }
        if parameter.default is not parameter.empty:
            value = parameter.default
            row["default"] = value if isinstance(value, (str, int, float, bool, type(None))) else repr(value)
        fields.append(row)
    return fields


def build():
    from zeno_skills.contracts import CONTRACTS, policy_contract_relations
    from zeno_skills.interface_ids import POLICY_PUBLIC_IDS
    from zeno_skills.policies import PolicySuite

    catalog = json.loads((ROOT / "zeno_skills/policies/catalog.json").read_text())
    rows = catalog["policies"]
    suite = PolicySuite(None)
    relations = policy_contract_relations(rows)
    direct = {row["id"]: [] for row in rows}
    support = {row["id"]: [] for row in rows}
    for legacy_contract, groups in relations.items():
        public_contract = CONTRACTS[legacy_contract].public_id
        for old_policy in groups["direct"]:
            direct[old_policy].append(public_contract)
        for old_policy in groups["support"]:
            support[old_policy].append(public_contract)

    files = {}
    contract_index = {"schema_version": 1, "kind": "contract_catalog", "contracts": []}
    for legacy_id, spec in CONTRACTS.items():
        profile = dict(spec.profile)
        record = {
            "schema_version": 1,
            "kind": "contract",
            "contract_id": spec.public_id,
            "legacy_id": legacy_id,
            "description": spec.description,
            "scope": profile["scope"],
            "inputs": profile["inputs"],
            "requires": profile["requires"],
            "achieves": profile["achieves"],
            "outcomes": dict(spec.outcomes),
            "verifier": spec.verifier,
        }
        for optional in ("route_notes", "not_guaranteed"):
            if optional in profile:
                record[optional] = profile[optional]
        record["routes"] = {}
        for route, policy_type in spec.executor.items():
            match = next(
                (row["id"] for row in rows
                 if type(getattr(suite, row["executor"])) is policy_type),
                None,
            )
            record["routes"][route] = {
                "policy_id": POLICY_PUBLIC_IDS[match] if match else None,
                "legacy_dispatcher": None if match else policy_type.__name__,
            }
        base = Path("contract_library/contracts") / spec.public_id
        contract_index["contracts"].append({
            "contract_id": spec.public_id, "name": legacy_id.removesuffix(".v1"),
            "legacy_id": legacy_id, "definition": str(base.relative_to("contract_library") / "contract.json"),
        })
        files[base / "contract.json"] = _json(record)
        lines = [
            f"# {spec.public_id} — {legacy_id}", "",
            spec.description, "", "## Scope", "", record["scope"], "",
            "## Inputs", "",
        ]
        for name, meta in record["inputs"].items():
            lines.append(f"- `{name}`: {meta['type']}; {'required' if meta['required'] else 'optional'}")
        lines += ["", "## Requires", ""]
        for item in record["requires"]:
            lines.append(f"- `{item['predicate']}` — {item['check']}")
        lines += ["", "## Achieves on success", ""]
        for item in record["achieves"]:
            suffix = f" when {item['when']}" if item.get("when") else ""
            lines.append(f"- `{item['predicate']}` — {item['check']}{suffix}")
        lines += ["", "## Routes", ""]
        for route, target in record["routes"].items():
            destination = target["policy_id"] or target["legacy_dispatcher"]
            lines.append(f"- `{route}` → `{destination}`")
        if record.get("not_guaranteed"):
            lines += ["", "## Outside this contract", ""]
            lines += [f"- {x}" for x in record["not_guaranteed"]]
        lines += ["", f"Legacy alias: `{legacy_id}`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.", ""]
        files[base / "CONTRACT.md"] = "\n".join(lines)
    # Active planner-facing contracts are paired one-to-one with SkillNodes.
    # Preserve the eight family records as compatibility details.
    from zeno_skills.node_contracts import NODE_CONTRACTS
    contract_index["legacy_family_contracts"] = contract_index.pop("contracts")
    contract_index["contracts"] = []
    legacy_direct = {key: list(value) for key, value in direct.items()}
    direct = {row["id"]: [] for row in rows}
    for cid, record in NODE_CONTRACTS.items():
        base = Path("contract_library/contracts") / cid
        files[base / "contract.json"] = _json(record)
        contract_index["contracts"].append({
            "contract_id": cid, "skill_id": record["skill_id"],
            "name": record["name"],
            "definition": str(base.relative_to("contract_library") / "contract.json"),
        })
        lines = [f"# {cid} — {record['name']}", "", record["description"], "",
                 f"Paired SkillNode: `{record['skill_id']}`. Status: `{record['availability']}`.", "",
                 "## Inputs", ""]
        for name, meta in record["inputs"].items():
            lines.append(f"- `{name}`: {meta['type']}")
        lines += ["", "## Preconditions", ""]
        lines += [f"- `{x['predicate']}` — {x['enforcement']}" for x in record["requires"]]
        lines += ["", "## Measured postconditions", ""]
        lines += [f"- `{x['predicate']}` — {x['verification']}" for x in record["achieves"]]
        lines += ["", "## Grounded noun slots", ""]
        for name, binding in record["noun_bindings"].items():
            constraints = {key: value for key, value in binding.items()
                           if key not in ("argument", "kind")}
            lines.append(f"- `{name}`: `{binding['kind']}`; constraints `{constraints}`")
        lines += ["", "## Policy paths", ""]
        plan = record["policy_plan"]
        paths = plan.get("paths") or [{"path_id": "fixed", "when": [], "steps": plan["steps"]}]
        for path in paths:
            lines.append(f"### {path['path_id']}")
            lines.append("")
            lines.append(f"Match before execution: `{path['when']}`.")
            lines.append("")
            for index, step in enumerate(path["steps"], 1):
                lines.append(f"{index}. `{step['policy_id']}` with {[x['arg'] for x in step['args']]}")
                old_policy = next((old for old, public in POLICY_PUBLIC_IDS.items()
                                   if public == step["policy_id"]), None)
                if old_policy is not None and cid not in direct[old_policy]:
                    direct[old_policy].append(cid)
            lines.append("")
        verifier = record["verifier"]
        verifier_label = (f"`{verifier['legacy_family_contract']}` / `{verifier['route']}`"
                          if verifier.get("legacy_family_contract")
                          else f"custom `{verifier['custom']}`")
        lines += ["", "## Failure", "",
                  "Stop, return completed policy steps and measured state; upper layer replans.", "",
                  f"Verifier: {verifier_label}.", ""]
        files[base / "CONTRACT.md"] = "\n".join(lines)
    files[Path("contract_library/catalog.json")] = _json(contract_index)

    policy_index = {"schema_version": 1, "kind": "low_level_policy_catalog", "policies": []}
    for row in rows:
        legacy_id = row["id"]
        policy_id = row["policy_id"]
        policy = getattr(suite, legacy_id)
        record = {
            "schema_version": 1, "kind": "low_level_policy",
            "policy_id": policy_id, "legacy_id": legacy_id,
            "name": legacy_id.replace("_", " ").title(),
            "description": row["description"],
            "scope": {"unit": "one low-level controller invocation",
                      "group": row["group"],
                      "effect_summary": row["effect"],
                      "effect_is_contract_guarantee": False},
            "inputs": _signature(policy),
            "requires": [{"predicate": "policy_specific_preconditions",
                          "check": "policy_internal",
                          "detail": "See the execute implementation; this catalog has not normalized every route-specific precondition."}],
            "achieves": [{"predicate_summary": row["effect"], "verification": "policy_internal_or_route_specific"}],
            "binding": {"api": "PolicySuite", "attribute": policy_id,
                        "legacy_attribute": legacy_id, "class": type(policy).__name__},
            "availability": row["status"],
            "direct_contracts": direct[legacy_id],
            "legacy_family_contracts": legacy_direct[legacy_id],
            "supporting_family_contracts": support[legacy_id],
        }
        if row.get("verification"):
            record["evidence"] = row["verification"]
        if row.get("caveat"):
            record["caveat"] = row["caveat"]
        base = Path("policy_library/policies") / policy_id
        policy_index["policies"].append({
            "policy_id": policy_id, "name": legacy_id, "legacy_id": legacy_id,
            "definition": str(base.relative_to("policy_library") / "policy.json"),
        })
        files[base / "policy.json"] = _json(record)
        lines = [
            f"# {policy_id} — {legacy_id}", "", row["description"], "",
            "## Scope", "",
            f"One low-level controller invocation. Reported effect: `{row['effect']}`.",
            "This effect summary is not a Contract guarantee.", "",
            "## Preconditions", "",
            "Policy-specific checks remain inside the controller and are not all normalized in this record.", "",
            "## Execute inputs", "",
        ]
        if record["inputs"]:
            for item in record["inputs"]:
                lines.append(f"- `{item['name']}`: {item['kind']}; {'required' if item['required'] else 'optional'}")
        else:
            lines.append("- None.")
        lines += ["", "## Binding and status", "",
                  f"- Runtime: `PolicySuite(rig).{policy_id}.execute(...)`",
                  f"- Legacy alias: `PolicySuite(rig).{legacy_id}.execute(...)`",
                  f"- Class: `{type(policy).__name__}`",
                  f"- Availability: `{row['status']}`"]
        if direct[legacy_id]:
            lines.append(f"- Direct Contract routes: {', '.join(direct[legacy_id])}")
        if legacy_direct[legacy_id]:
            lines.append(f"- Legacy family Contracts: {', '.join(legacy_direct[legacy_id])}")
        if support[legacy_id]:
            lines.append(f"- Referenced as support by legacy families: {', '.join(support[legacy_id])}")
        if row.get("caveat"):
            lines += ["", "## Caveat", "", row["caveat"]]
        if row.get("verification"):
            lines += ["", "## Recorded evidence", "", row["verification"]]
        lines.append("")
        files[base / "POLICY.md"] = "\n".join(lines)
    files[Path("policy_library/catalog.json")] = _json(policy_index)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = build()
    stale = [str(path) for path, content in files.items()
             if not (ROOT / path).exists() or (ROOT / path).read_text() != content]
    if args.check:
        if stale:
            raise SystemExit(f"stale interface exports: {', '.join(stale[:10])} ({len(stale)} files)")
        print(f"{len(files)} interface exports current")
    else:
        for path, content in files.items():
            target = ROOT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        print(f"wrote {len(files)} interface exports")


if __name__ == "__main__":
    main()
