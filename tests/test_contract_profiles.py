"""Public contract claims must match the measured result on each route."""

from types import SimpleNamespace
import numpy as np
import pytest

from zeno_skills.contract_runtime import ContractRunner
from zeno_skills.contracts import CONTRACTS, PUBLIC_CONTRACTS, public_contract_profiles
from zeno_skills.rig import SkillFailure


def test_every_registered_contract_has_a_machine_readable_measured_scope():
    profiles = public_contract_profiles()
    assert set(profiles) == set(PUBLIC_CONTRACTS)
    assert PUBLIC_CONTRACTS["contract_002"] is CONTRACTS["pick.v1"]
    for contract_id, profile in profiles.items():
        assert profile["scope"] and profile["inputs"]
        assert profile["achieves"], contract_id
        assert all(row["check"] == "runner" for row in profile["achieves"])
        assert all(row["check"] in {"runner", "policy_attempt", "not_enforced"}
                   for row in profile["requires"])


def test_route_specific_achievements_are_not_reported_on_other_routes():
    checked = ContractRunner._verified_predicates
    place = CONTRACTS["place.v1"]
    assert checked(place, "container", ("apple", "in:basket"), {}) == [
        "inside", "right_hand_empty"
    ]
    assert checked(place, "surface", ("apple", "table"), {}) == [
        "on", "right_hand_empty"
    ]
    click = CONTRACTS["click.v1"]
    assert checked(click, "auto", ("kitchen_microwave",), {}) == [
        "button_pressed_this_call"
    ]
    assert checked(click, "start", ("kitchen_microwave",), {}) == [
        "button_pressed_this_call", "heating_active"
    ]


def test_place_rejects_mismatched_route_before_releasing_object():
    rig = SimpleNamespace(
        held={"name": "apple"}, left_held=None, events=[]
    )
    runner = ContractRunner(rig)
    with pytest.raises(SkillFailure, match="must start with in:"):
        runner._before("place.v1", "container", ("apple", "table"))
    assert rig.held["name"] == "apple"


def test_success_result_exposes_only_verified_place_predicates(monkeypatch):
    rig = SimpleNamespace(
        held={"name": "apple"}, left_held=None, events=[],
        geo=SimpleNamespace(inside=lambda obj, target, state: (True, {"inside": True})),
        state=lambda: {"objects": {"apple": {}}},
    )
    class ReleasePolicy:
        def execute(self, object_name, target):
            rig.held = None

    actual = CONTRACTS["place.v1"]
    proxy = SimpleNamespace(id=actual.id, profile=actual.profile,
                            bind=lambda rig, route: ReleasePolicy())
    monkeypatch.setattr("zeno_skills.contract_runtime.CONTRACTS", {"place.v1": proxy})
    result = ContractRunner(rig).run("contract_003", "container", "apple", "in:basket")
    assert result.success
    assert result.contract_id == "contract_003"
    assert result.observations["verified_predicates"] == ["inside", "right_hand_empty"]


def test_failed_push_check_preserves_measured_partial_progress():
    position = np.array([0.04, 0.0, 0.7])
    rig = SimpleNamespace(
        held=None, left_held=None, events=[],
        obj_pose=lambda name: (position.copy(), None),
        base_pose=lambda: (0.0, 0.0, 0.0),
        state=lambda: {"objects": {"apple": {"x": float(position[0])}}},
    )
    runner = ContractRunner(rig)
    with pytest.raises(SkillFailure, match="only"):
        runner._verify("push.v1", "auto", ("apple", "table", [1.0, 0.0], 0.2),
                       {}, {"object_pos": np.array([0.0, 0.0, 0.7])})
    snapshot = runner._after_snapshot("push.v1", "auto", ("apple",))
    assert snapshot["object_position"][0] == pytest.approx(0.04)
    assert snapshot["scene_state"]["objects"]["apple"]["x"] == pytest.approx(0.04)
