"""Command-level checks for gentle manipulation timing (Isaac Sim is not required)."""

from types import SimpleNamespace

import numpy as np

from zeno_skills.kinematics import ArmKin, vel_limits
from zeno_skills.rig import Rig


class FakeRig:
    held = None
    _vmax, _carrying, _settle = Rig._vmax, Rig._carrying, Rig._settle

    def __init__(self):
        # the TCP stands in for _settle's arrival check: q() follows q_cmd exactly here
        self.kin = SimpleNamespace(names=ArmKin().names, tcp=lambda q: (np.asarray(q, float)[:3], np.eye(3)))
        self.q_cmd = np.zeros(len(self.kin.names))
        self.grip_cmd = 0.04
        self.clear = SimpleNamespace(executing=lambda: None)
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


class SettleRig(FakeRig):
    """The arm closes on q_cmd at ``rate`` of the remaining error per tick, stopping ``stuck`` short."""

    def __init__(self, start, rate, stuck=0.0):
        super().__init__()
        self.actual, self.rate, self.stuck = np.asarray(start, float), rate, stuck

    def step(self, n=1):
        for _ in range(n):
            gap = self.q_cmd - self.actual
            if np.linalg.norm(gap) > self.stuck:
                self.actual = self.actual + self.rate * gap
            self.commands.append(self.q_cmd.copy())

    def q(self):
        return self.actual.copy()


def test_settle_waits_past_the_joint_tolerance_until_the_hand_arrives():
    from zeno_skills.rig import SETTLE_TCP
    start = np.zeros(9)
    start[0] = -0.008                          # 8 mm off at the TCP, inside the old 0.01 rad stop
    rig = SettleRig(start, rate=0.02)
    rig._settle(150, 0.01)
    assert np.linalg.norm(rig.q()[:3] - rig.q_cmd[:3]) < SETTLE_TCP


def test_settle_stops_when_the_hand_is_held_short():
    start = np.zeros(9)
    start[0] = -0.03
    rig = SettleRig(start, rate=0.05, stuck=0.007)   # blocked 7 mm short
    rig._settle(150, 0.01)
    assert len(rig.commands) < 2 * 150                 # stopped, did not wait out the budget
    assert np.linalg.norm(rig.q()[:3] - rig.q_cmd[:3]) > 0.005   # the error is left for the reach check
