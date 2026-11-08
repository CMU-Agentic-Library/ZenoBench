"""Torso and waist moves with a load: the held object rides along instead of refusing the move."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import skills
from zeno_skills.policies import posture
from zeno_skills.rig import SkillFailure


class FakeRig:
    def __init__(self, held, blocked=0):
        names = ["torso_lift_joint", "waist_pitch_joint", "a1"]
        self.kin = SimpleNamespace(names=names, lo=np.array([-0.54, 0.0, -1.0]), hi=np.array([0.0, 0.69, 1.0]),
                                   coll_kw={})
        self.q_cmd = np.zeros(3)
        self.left_q_cmd = np.zeros(7)
        self.held = held
        self.left_held = None
        self.blocked = blocked
        self.calls = []

    def sync_world(self):
        pass

    def joint_path(self, q_goal, label=None):
        if self.blocked:
            self.blocked -= 1
            raise SkillFailure("blocked")
        return [q_goal]

    def follow(self, path):
        self.q_cmd = np.asarray(path[-1], float)

    def q(self):
        return self.q_cmd

    def log(self, *a, **k):
        pass


@pytest.fixture
def record(monkeypatch):
    calls = []
    monkeypatch.setattr(skills, "check_held", lambda rig, label: calls.append(("check_held", label)))
    monkeypatch.setattr(skills, "check_left_held", lambda rig, label: calls.append(("check_left_held", label)))
    def relocate(rig, goal, postures, label, **kw):             # the base moves, the posture switch is made
        calls.append(("relocate", goal, postures[0][0], float(postures[0][1][0][1])))
        rig.q_cmd = np.asarray(postures[-1][1][0], float)
    monkeypatch.setattr(skills, "relocate", relocate)
    monkeypatch.setattr(posture.TuckArmPolicy, "execute", lambda self: calls.append(("tuck",)))
    return calls


def test_stand_with_a_load_moves_and_checks_the_grasp(record):
    rig = FakeRig(held={"name": "mug"})
    rig.q_cmd[0] = -0.4
    assert posture.RaiseTorsoPolicy(rig).execute() == pytest.approx(0.0)
    assert ("check_held", "torso_lift_joint") in record


def test_blocked_with_a_load_moves_the_base_to_where_the_joint_can_move_instead_of_tucking(record):
    rig = FakeRig(held={"name": "mug"}, blocked=1)
    posture.SetWaistPitchPolicy(rig).execute(0.3)
    assert ("relocate", None, "waist_pitch_joint", 0.3) in record and ("tuck",) not in record


def test_blocked_empty_handed_still_tucks_first(record):
    rig = FakeRig(held=None, blocked=1)
    posture.LowerTorsoPolicy(rig).execute(-0.3)
    assert record[0] == ("tuck",)
