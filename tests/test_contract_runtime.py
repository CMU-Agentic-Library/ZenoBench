"""Contract failures remain observable to a replanning upper layer."""

from types import SimpleNamespace

import pytest

from zeno_skills.contract_runtime import ContractRunner
from zeno_skills.rig import SkillFailure


def test_failed_precondition_is_traced_without_changing_held_state():
    rig = SimpleNamespace(held={"name": "apple"}, left_held=None, events=[],
                          obj_pose=lambda name: ([0.0, 0.0, 0.7], None))
    runner = ContractRunner(rig)
    with pytest.raises(SkillFailure, match="occupied"):
        runner.run("pick.v1", "top", "toy_block")
    assert rig.held["name"] == "apple"
    assert [(r.contract_id, r.route, r.success) for r in runner.trace] == [
        ("pick.v1", "top", False)]
