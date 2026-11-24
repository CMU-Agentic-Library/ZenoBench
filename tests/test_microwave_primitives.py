"""Microwave stage guards must prevent pressing or moving a hinge out of order."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import skills
from zeno_skills.policies import MicrowaveHingeDrivePolicy
from zeno_skills.rig import SkillFailure


def test_hinge_driver_requires_clearance_before_motor_motion(monkeypatch):
    art = {"category": "microwave", "door_button": {}, "open_q": 1.0, "closed_q": 0.0}
    rig = SimpleNamespace(ann=SimpleNamespace(art=lambda name: art), _microwave_clear=None,
                          base_pose=lambda: (5.1, 1.6, 150.0))
    with pytest.raises(SkillFailure, match="clear the door sweep"):
        MicrowaveHingeDrivePolicy(rig).execute("oven", target="open")
    calls = []
    monkeypatch.setattr(skills, "_set_microwave_hinge", lambda rig, name, q, caption: calls.append(q) or q)
    rig._microwave_clear = {"name": "oven", "held": None}
    assert MicrowaveHingeDrivePolicy(rig).execute("oven", target="close") == 0.0
    assert calls == [0.0]
    with pytest.raises(ValueError, match="open or close"):
        MicrowaveHingeDrivePolicy(rig).execute("oven", target="half")


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
