"""The capability inventory must not claim missing code as executable."""

import json
from pathlib import Path
from types import SimpleNamespace

from zeno_skills.policies import AtomicPolicy, PolicySuite
from tools.render_policy_catalog import render

ROOT = Path(__file__).resolve().parents[1]


def test_policy_catalog_status_matches_callable_api():
    catalog = json.loads((ROOT / "zeno_skills/policies/catalog.json").read_text())
    rows = catalog["policies"]
    assert catalog["schema_version"] == 1
    assert len(rows) >= 50
    assert len({row["id"] for row in rows}) == len(rows)
    suite = PolicySuite(SimpleNamespace())
    assert len({row["policy_id"] for row in rows}) == len(rows)
    for row in rows:
        assert row["schema_version"] == 1
        assert row["kind"] == "low_level_policy"
        assert getattr(suite, row["policy_id"]) is getattr(suite, row["id"])
        status = row["status"]
        assert status in {"verified", "callable", "embedded", "planned"}
        if status in {"verified", "callable"}:
            assert isinstance(getattr(suite, row["executor"]), AtomicPolicy)
        elif status == "embedded":
            assert row.get("basis") and "executor" not in row
        else:
            assert row.get("gap") and "executor" not in row
        if status == "verified":
            assert row.get("verification")


def test_catalog_document_is_current():
    catalog = json.loads((ROOT / "zeno_skills/policies/catalog.json").read_text())
    assert (ROOT / "docs/POLICY_CATALOG.md").read_text() == render(catalog)


def test_all_sixty_four_policies_have_contract_relations_with_real_direct_bindings():
    from zeno_skills.contracts import CONTRACTS, policy_contract_relations
    from tools.render_contract_layers import render as render_contract_layers

    catalog = json.loads((ROOT / "zeno_skills/policies/catalog.json").read_text())
    rows = catalog["policies"]
    relations = policy_contract_relations(rows)
    assert len(rows) == 64
    assert len(relations) == len(CONTRACTS) == 8
    covered = {policy_id for group in relations.values()
               for ids in group.values() for policy_id in ids}
    assert covered == {row["id"] for row in rows if row["id"] != "wait_for_temperature"}
    suite = PolicySuite(SimpleNamespace())
    for contract_id, group in relations.items():
        direct_classes = set(CONTRACTS[contract_id].executor.values())
        for policy_id in group["direct"]:
            assert type(getattr(suite, policy_id)) in direct_classes
        assert not set(group["direct"]) & set(group["support"])
    svg, _, _ = render_contract_layers(catalog)
    assert (ROOT / "docs/contract_layers.svg").read_text() == svg
