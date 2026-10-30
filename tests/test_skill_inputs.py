"""Optional inputs that pick a path or stand for a number the planner would compute."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from zeno_skills import skill_runtime
from zeno_skills.skill_runtime import ContractError, condition_holds, resolve_near

CONTRACTS = {c["verb"]: c for c in json.loads(
    (Path(__file__).resolve().parents[1] / "contract_library/skill_contracts.json").read_text())["contracts"]}


def _crouch_path(height_m):
    nouns = {"args": {"height_m": height_m}}
    return next(p["path_id"] for p in CONTRACTS["crouch"]["policy_plan"]["paths"]
                if all(condition_holds(w, nouns) for w in p["when"]))


def test_crouch_zero_is_a_requested_height_not_the_lowest():
    assert _crouch_path(0.0) == "to_height"
    assert _crouch_path(-0.3) == "to_height"
    assert _crouch_path(None) == "lowest"


@pytest.fixture
def ref(monkeypatch):
    monkeypatch.setattr(skill_runtime, "entity_point", lambda rig, name, st=None: [3.0, 7.5, 0.86])
    monkeypatch.setattr(skill_runtime, "entity_top_z", lambda rig, name, st=None: 0.92)
    return SimpleNamespace()


def test_place_near_becomes_the_hint(ref):
    values = {"object": "bowl", "receptacle": "dining_table_2/top", "hint_xy": None, "near": "spoon"}
    resolve_near(ref, "place", values)
    assert values["hint_xy"] == [3.0, 7.5]


def test_place_near_and_hint_together_are_refused(ref):
    values = {"object": "bowl", "receptacle": "dining_table_2/top", "hint_xy": [3.0, 7.0], "near": "spoon"}
    with pytest.raises(ContractError, match="not both"):
        resolve_near(ref, "place", values)


@pytest.mark.parametrize("verb", ["lift", "lower"])
def test_height_is_measured_above_near(ref, verb):
    values = {"object": "breakfast_spoon", "height_m": 0.05, "near": "handled_cooking_pot"}
    resolve_near(ref, verb, values)
    assert values["height_m"] == pytest.approx(0.97)


def test_without_near_nothing_changes(ref):
    values = {"object": "breakfast_spoon", "height_m": 0.95, "near": None}
    resolve_near(ref, "lower", values)
    assert values["height_m"] == 0.95
