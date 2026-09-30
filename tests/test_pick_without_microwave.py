"""A generic scene must not require the breakfast appliance to pick an item."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import skills
from zeno_skills.rig import SkillFailure


def test_pick_without_microwave_uses_generic_grasp_search(monkeypatch):
    grasp = {"kind": "top_pinch", "p": np.array([1.0, 2.0, 0.8]),
             "R": np.eye(3), "pre_open": 0.03}
    ann = SimpleNamespace(
        objects={"apple": {"support": "table"}},
        articulated=[],
        grasp_poses=lambda *args, **kwargs: [grasp.copy()],
    )
    rig = SimpleNamespace(
        ann=ann,
        geo=SimpleNamespace(bottom=lambda *args: np.array([1.0, 2.0, 0.75])),
        kin=SimpleNamespace(coll_kw={}, rest=np.zeros(9)),
        world=object(),
        q_cmd=np.zeros(9),
        held=None,
        obj_pose=lambda name: (np.array([1.0, 2.0, 0.75]), np.array([1.0, 0.0, 0.0, 0.0])),
        state=lambda: {},
        sync_world=lambda: None,
        base_pose=lambda: (0.0, 0.0, 0.0),
    )
    monkeypatch.setattr(skills, "find_park", lambda *args, **kwargs: None)

    with pytest.raises(SkillFailure, match="no reachable grasp"):
        skills._pick_pinch(rig, "apple", max_candidates=1)
