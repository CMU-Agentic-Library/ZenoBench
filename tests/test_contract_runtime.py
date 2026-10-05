"""Contract failures remain observable to a replanning upper layer."""

from types import SimpleNamespace

import pytest

from zeno_skills.contract_runtime import ContractRunner
from zeno_skills.rig import SkillFailure


def test_failed_precondition_is_traced_without_changing_held_state():
    rig = SimpleNamespace(held={"name": "apple"}, left_held=None, events=[],
                          obj_pose=lambda name: ([0.0, 0.0, 0.7], None),
                          base_pose=lambda: (1.0, 2.0, 0.0),
                          state=lambda: {"objects": {"apple": {"pos": [0.0, 0.0, 0.7]}}})
    runner = ContractRunner(rig)
    with pytest.raises(SkillFailure, match="occupied"):
        runner.run("pick.v1", "top", "toy_block")
    assert rig.held["name"] == "apple"
    assert [(r.contract_id, r.route, r.success) for r in runner.trace] == [
        ("pick.v1", "top", False)]
    assert runner.trace[0].error_code == "SkillFailure"
    assert runner.trace[0].observations["held_right"] == "apple"
    assert runner.trace[0].observations["scene_state"]["objects"]["apple"]["pos"] == [
        0.0, 0.0, 0.7
    ]


def test_place_contract_requires_right_hand_empty_after_execution():
    rig = SimpleNamespace(held={"name": "orange"})
    runner = ContractRunner(rig)
    with pytest.raises(SkillFailure, match="right hand is not empty"):
        runner._verify("place.v1", "container", ("apple", "in:fruit_basket"), {}, {})
