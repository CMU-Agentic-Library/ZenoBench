"""Stable public IDs with explicit legacy aliases for existing scripts."""

from __future__ import annotations

import json
from pathlib import Path

_IDS = json.loads(Path(__file__).with_name("interface_ids.json").read_text())
CONTRACT_PUBLIC_IDS: dict[str, str] = _IDS["contract_ids"]
POLICY_PUBLIC_IDS: dict[str, str] = _IDS["policy_ids"]
CONTRACT_LEGACY_IDS: dict[str, str] = {
    public: legacy for legacy, public in CONTRACT_PUBLIC_IDS.items()
}
POLICY_LEGACY_IDS: dict[str, str] = {
    public: legacy for legacy, public in POLICY_PUBLIC_IDS.items()
}


def resolve_contract_id(contract_id: str) -> str:
    """Accept a public or legacy Contract ID and return the legacy registry key."""
    return CONTRACT_LEGACY_IDS.get(contract_id, contract_id)


def resolve_policy_id(policy_id: str) -> str:
    """Accept a public or legacy Policy ID and return its PolicySuite attribute."""
    return POLICY_LEGACY_IDS.get(policy_id, policy_id)
