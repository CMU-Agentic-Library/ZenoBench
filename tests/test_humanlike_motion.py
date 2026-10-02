"""Command-level checks for gentle manipulation timing (Isaac Sim is not required)."""

from types import SimpleNamespace

import numpy as np

from zeno_skills.kinematics import ArmKin, vel_limits
from zeno_skills.rig import Rig


class FakeRig:
    def __init__(self):
        self.kin = SimpleNamespace(names=ArmKin().names)
        self.q_cmd = np.zeros(len(self.kin.names))
        self.grip_cmd = 0.04
        self.commands = []
        self.grip_commands = []

    def step(self, n=1):
        for _ in range(n):
            self.commands.append(self.q_cmd.copy())
            self.grip_commands.append(float(self.grip_cmd))

    def q(self):
        return self.q_cmd.copy()

    def fingers(self):
        return np.array([self.grip_cmd, self.grip_cmd])

    def log(self, *_args, **_kwargs):
        pass


def test_smooth_arm_motion_stays_on_planned_segments_and_under_joint_speed_limits():
    rig = FakeRig()
    first = rig.q_cmd.copy()
    first[2] = 0.16
    second = first.copy()
    second[3] = 0.12
    Rig.follow_smooth(rig, [first, second], steps_per_wp=4)
    commands = np.asarray(rig.commands)
    velocity_bound = 0.6 * vel_limits(rig.kin.names) / 120
    assert np.all(np.abs(np.diff(np.vstack([np.zeros_like(first), commands]), axis=0)) <= velocity_bound + 1e-5)
    assert np.allclose(commands[-1], second)
    # A right-angle joint path must not be shortened across its corner.
    assert np.all((commands[:, 2] >= first[2] - 1e-6) | (np.abs(commands[:, 3]) < 1e-6))
    deltas = np.linalg.norm(np.diff(np.vstack([np.zeros_like(first), commands]), axis=0), axis=1)
    assert deltas[0] < np.max(deltas) / 10
    assert deltas[-1] < np.max(deltas) / 10


def test_gradual_grip_reaches_target_without_an_initial_jump():
    rig = FakeRig()
    Rig.grip(rig, 0.0, steps=80, gradual=True)
    commands = np.asarray(rig.grip_commands)
    assert len(commands) == 80
    assert commands[0] > 0.039
    assert commands[-1] == 0.0
    assert np.all(np.diff(commands) <= 1e-9)
