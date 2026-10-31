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


def test_place_near_with_pass_by_is_refused(ref):
    values = {"object": "bowl", "receptacle": "dining_table_2/top", "hint_xy": None, "near": "spoon",
              "pass_by": [3.0, 6.5, 90.0]}
    with pytest.raises(ContractError, match="pass_by"):
        resolve_near(ref, "place", values)


def _path(verb, nouns):
    return next(p["path_id"] for p in CONTRACTS[verb]["policy_plan"]["paths"]
                if all(condition_holds(w, nouns) for w in p["when"]))


EMPTY_READY = {"right_held": False, "left_held": False, "base_ready": True}


@pytest.mark.parametrize("bearing, robot, want", [
    (1.0, EMPTY_READY, "already_facing"),
    (60.0, EMPTY_READY, "rotate_empty"),
    (150.0, EMPTY_READY, "rotate_loaded"),                 # beyond the in-place primitive's 90 deg
    (60.0, dict(EMPTY_READY, base_ready=False), "rotate_loaded"),   # crouched, bent or arm out
])
def test_face_routes_what_the_rotation_primitive_refuses(bearing, robot, want):
    assert _path("face", {"target": {"bearing_abs_deg": bearing}, "robot": robot}) == want


@pytest.mark.parametrize("distance, ready, want", [
    (0.3, True, "empty_tucked"), (-0.4, True, "empty_tucked"),
    (0.8, True, "loaded"), (0.3, False, "loaded"),
])
def test_sidestep_routes_long_or_untucked_moves_to_the_general_policy(distance, ready, want):
    robot = dict(EMPTY_READY, base_ready=ready)
    assert _path("sidestep", {"args": {"distance_m": distance}, "robot": robot}) == want


def test_policy_value_error_is_a_policy_failure(monkeypatch):
    from zeno_skills import policies

    class Refusing:
        def __init__(self, rig):
            pass

        def __getattr__(self, name):
            return SimpleNamespace(execute=lambda *a, **k: (_ for _ in ()).throw(ValueError("out of range")))

    monkeypatch.setattr(policies, "PolicySuite", Refusing)
    runner = skill_runtime.SkillContractRunner.__new__(skill_runtime.SkillContractRunner)
    runner.rig = SimpleNamespace(log=lambda *a, **k: None)
    with pytest.raises(ContractError) as exc:
        runner._run_steps([{"policy": "policy_103", "args": [700]}], {}, {}, {}, SimpleNamespace(policy_steps=[]), 0)
    assert exc.value.code == "POLICY_FAILED" and "out of range" in str(exc.value)
