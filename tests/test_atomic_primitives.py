"""Check primitive policy guards and measured outcomes independent of Isaac Sim."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import skills
from zeno_skills.policies import (PushFromBehindPolicy, RightGripperClosePolicy,
                                  RightGripperOpenPolicy, RightJointMovePolicy,
                                  RightTcpMovePolicy, TopDragPolicy)
from zeno_skills.rig import SkillFailure


def test_gripper_joint_readback_does_not_claim_grasp():
    rig = SimpleNamespace(held=None, grip=lambda width: np.array([width, width]))
    assert np.allclose(RightGripperOpenPolicy(rig).execute(), [0.04, 0.04])
    assert np.allclose(RightGripperClosePolicy(rig).execute(), [0.0, 0.0])
    with pytest.raises(ValueError, match="finger position"):
        RightGripperOpenPolicy(rig).execute(0.1)
    rig.grip = lambda width: np.array([0.01, 0.01])
    with pytest.raises(SkillFailure, match="did not reach"):
        RightGripperClosePolicy(rig).execute()
    rig.held = {"name": "cup"}
    with pytest.raises(SkillFailure, match="release the held object"):
        RightGripperOpenPolicy(rig).execute()


def test_tcp_motion_checks_measured_pose():
    target = np.array([0.4, 0.0, 0.6])
    calls = []
    rig = SimpleNamespace(held=None, move_to=lambda *a, **k: calls.append((a, k)),
                          kin=SimpleNamespace(tcp=lambda q: (target, np.eye(3))), q=lambda: np.zeros(9))
    result = RightTcpMovePolicy(rig).execute(target, np.eye(3))
    assert result["position_error_m"] == 0
    assert calls[0][1]["label"] == "right_tcp_move"
    rig.kin.tcp = lambda q: (target, np.diag([-1., -1., 1.]))
    with pytest.raises(SkillFailure, match="rotation error"):
        RightTcpMovePolicy(rig).execute(target, np.eye(3))


def test_joint_motion_rejects_limits_and_unsettled_result():
    rig = SimpleNamespace(q_cmd=np.zeros(9),
                          kin=SimpleNamespace(lo=-np.ones(9), hi=np.ones(9),
                                              names=[f"joint_{i}" for i in range(9)]),
                          sync_world=lambda: None,
                          joint_path=lambda q, **kw: [q], follow=lambda path: None,
                          q=lambda: np.zeros(9), held=None)
    q = np.zeros(9)
    q[2] = 0.2
    with pytest.raises(SkillFailure, match="missed target"):
        RightJointMovePolicy(rig).execute(q)
    with pytest.raises(ValueError, match="exceeds robot limits"):
        RightJointMovePolicy(rig).execute(np.full(9, 2.0))


def test_explicit_contact_policy_fixes_mode(monkeypatch):
    modes = []
    monkeypatch.setattr(skills, "push", lambda *a, **kw: modes.append(kw["mode"]) or 0.12)
    rig = SimpleNamespace(held=None, ann=SimpleNamespace(objects={"book": {}}))
    support = {"z": 0.7}
    assert PushFromBehindPolicy(rig).execute("book", support, [1, 0], 0.12) == 0.12
    assert TopDragPolicy(rig).execute("book", support, [1, 0], 0.12) == 0.12
    assert modes == ["push", "drag"]
    with pytest.raises(ValueError, match="unit vector"):
        TopDragPolicy(rig).execute("book", support, [2, 0], 0.12)


def test_local_base_motion_checks_sweep_and_measured_pose():
    from zeno_skills.policies import BaseRotateInPlacePolicy, BaseTranslateLocalPolicy

    pose = [0.0, 0.0, 0.0]
    checked = []

    def clear(x, y, yaw):
        checked.append((x, y, yaw))
        return True

    def drive(path):
        pose[:] = path[-1]

    rig = SimpleNamespace(held=None, q=lambda: np.zeros(9),
                          kin=SimpleNamespace(rest=np.zeros(9)),
                          world=SimpleNamespace(footprint_clear=clear),
                          base_pose=lambda: tuple(pose), drive_base=drive)
    assert BaseRotateInPlacePolicy(rig).execute(15) == 15
    assert len(checked) >= 4
    checked.clear()
    bx, by, yaw = BaseTranslateLocalPolicy(rig).execute(0.1)
    assert np.allclose([bx, by], [0.1 * np.cos(np.pi / 12), 0.1 * np.sin(np.pi / 12)])
    assert yaw == 15
    assert len(checked) >= 3
    rig.world.footprint_clear = lambda *args: False
    with pytest.raises(SkillFailure, match="occupied footprint"):
        BaseTranslateLocalPolicy(rig).execute(0.1)
