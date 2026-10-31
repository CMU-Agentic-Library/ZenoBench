"""Torso and waist moves with a load: the held object rides along instead of refusing the move."""

import contextlib
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

    def held_collision(self):
        self.calls.append("held_collision")
        return contextlib.nullcontext()

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
    monkeypatch.setattr(skills, "_back_off", lambda rig, d: calls.append(("back_off", d)) or d)
    monkeypatch.setattr(posture.TuckArmPolicy, "execute", lambda self: calls.append(("tuck",)))
    return calls


def test_stand_with_a_load_moves_and_checks_the_grasp(record):
    rig = FakeRig(held={"name": "mug"})
    rig.q_cmd[0] = -0.4
    assert posture.RaiseTorsoPolicy(rig).execute() == pytest.approx(0.0)
    assert "held_collision" in rig.calls
    assert ("check_held", "torso_lift_joint") in record


def test_blocked_with_a_load_backs_out_instead_of_tucking(record):
    rig = FakeRig(held={"name": "mug"}, blocked=1)
    posture.SetWaistPitchPolicy(rig).execute(0.3)
    assert ("back_off", 0.35) in record and ("tuck",) not in record


def test_blocked_empty_handed_still_tucks_first(record):
    rig = FakeRig(held=None, blocked=1)
    posture.LowerTorsoPolicy(rig).execute(-0.3)
    assert record[0] == ("tuck",)
