"""A generic scene must not require the breakfast appliance to pick an item."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import motion_skills, skills
from zeno_skills.skill_jobs import pick as pick_job
from zeno_skills.rig import SkillFailure


def test_pick_without_microwave_uses_generic_grasp_search(monkeypatch):
    grasp = {"kind": "top_pinch", "p": np.array([1.0, 2.0, 0.8]),
             "R": np.eye(3), "pre_open": 0.03}
    ann = SimpleNamespace(
        objects={"apple": {"support": "table"}},
        articulated=[],
        grasp_poses=lambda *args, **kwargs: [grasp.copy()],
        asset_of=lambda obj: {"size": [0.07, 0.07, 0.07]},
    )
    rig = SimpleNamespace(
        ann=ann,
        geo=SimpleNamespace(bottom=lambda *args: np.array([1.0, 2.0, 0.75]),
                            centre=lambda *args: np.array([1.0, 2.0, 0.785]),
                            support_under=lambda *args: {"name": "table/top", "z": 0.75}),
        kin=SimpleNamespace(coll_kw={}, rest=np.zeros(9)),
        world=object(),
        q_cmd=np.zeros(9),
        held=None,
        obj_pose=lambda name: (np.array([1.0, 2.0, 0.75]), np.array([1.0, 0.0, 0.0, 0.0])),
        state=lambda: {"objects": {"apple": {"pos": [1.0, 2.0, 0.75], "quat": [1.0, 0.0, 0.0, 0.0]}}},
        sync_world=lambda: None,
        base_pose=lambda: (0.0, 0.0, 0.0),
        log=lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(skills, "find_park", lambda *args, **kwargs: None)
    monkeypatch.setattr(motion_skills, "observe", lambda rig: None)
    monkeypatch.setattr(pick_job, "_carry_goal_set", lambda rig, name, min_bottom_z=None: None)
    monkeypatch.setattr(motion_skills, "find_park", lambda *args, **kwargs: (None, {}))

    with pytest.raises(SkillFailure, match="no reachable grasp"):
        skills._pick_pinch(rig, "apple", max_candidates=1)
