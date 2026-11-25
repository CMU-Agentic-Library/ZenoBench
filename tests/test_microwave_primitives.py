"""Microwave stage guards must prevent pressing or moving a hinge out of order."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import skills
from zeno_skills.policies import MicrowaveHingeDrivePolicy
from zeno_skills.rig import SkillFailure


def test_the_door_moves_only_by_its_key_the_clearance_and_hinge_policies_are_retired():
    # 9.3 step 8b: the door key's press parks clear of the swing and drives the door (plan_press press_door)
    from zeno_skills.policies import MicrowaveDoorClearPolicy
    with pytest.raises(SkillFailure, match="retired"):
        MicrowaveHingeDrivePolicy(object()).execute("oven", target="close")
    with pytest.raises(SkillFailure, match="retired"):
        MicrowaveDoorClearPolicy(object()).execute("oven")


def test_cavity_release_requires_insertion_and_measured_open_fingers():
    from zeno_skills.policies import MicrowaveCavityReleasePolicy

    body = np.array([0.5, 0.5, 0.5])
    tcp = np.array([0.5, 0.5, 0.6])
    rig = SimpleNamespace(held={"name": "oatmeal", "tcp_minus_body": tcp - body},
                          _microwave_load_stage=None,
                          grip=lambda width, steps: np.array([0.0, 0.0]),
                          fingers=lambda: np.array([0.01, 0.01]),
                          kin=SimpleNamespace(tcp=lambda q: (tcp, np.eye(3))),
                          q=lambda: np.zeros(9),
                          base_pose=lambda: (0.0, 0.0, 0.0),
                          obj_pose=lambda name: (body, np.array([1, 0, 0, 0])),
                          log=lambda *a, **k: None)
    with pytest.raises(SkillFailure, match="not staged"):
        MicrowaveCavityReleasePolicy(rig).execute("oatmeal")
    stage = {"name": "oatmeal", "phase": "inserted", "pre_open": 0.04,
             "targets": [(tcp, np.eye(3)), (tcp, np.eye(3))],
             "cavity": [0, 0, 0, 1, 1, 1]}
    rig._microwave_load_stage = stage
    with pytest.raises(SkillFailure, match="did not open"):
        MicrowaveCavityReleasePolicy(rig).execute("oatmeal")
    assert rig.held is not None and stage["phase"] == "inserted"
    rig.grip = lambda width, steps: np.array([width, width])
    assert np.allclose(MicrowaveCavityReleasePolicy(rig).execute("oatmeal"), [0.04, 0.04])
    assert rig.held is None and stage["phase"] == "released"
