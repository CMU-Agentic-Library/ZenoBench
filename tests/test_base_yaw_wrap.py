"""Rig.step: the base yaw reading set back by a turn when it passes pi must not undo the tick's drive
targets.  Isaac's Articulation.set_joint_positions also sets every joint's drive target to where the
joint is (set_dof_position_targets); done after the targets, it held whatever was moving for that
tick, and parked at 180 deg (the reading crossing pi back and forth) a torso lowering stalled at
-0.35..-0.38 of -0.54 (11-16: all 10 lowerings at +-180 deg, T26 / T05 / T02)."""

import math
import sys
import types

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from zeno_skills.rig import Rig


class Action:
    def __init__(self, joint_positions=None, joint_velocities=None, joint_indices=None):
        self.joint_positions, self.joint_velocities, self.joint_indices = joint_positions, joint_velocities, joint_indices


class Robot:
    """An articulation's drive targets and readings, with Isaac's set_joint_positions side effect."""

    def __init__(self, n, yaw_i, yaw):
        self.pos = np.zeros(n)
        self.pos[yaw_i] = yaw
        self.target = np.full(n, np.nan)

    def get_joint_positions(self):
        return torch.tensor(self.pos)

    def set_joint_positions(self, positions, joint_indices):
        self.pos[np.asarray(joint_indices, int)] = np.asarray(positions, float)
        self.target[:] = self.pos                 # set_dof_position_targets(new_dof_pos): every joint

    def apply_action(self, action):
        self.target[np.asarray(action.joint_indices, int)] = np.asarray(action.joint_positions, float)


class Sim:
    def __init__(self, robot):
        self.robot, self.stepped = robot, []

    def step(self, render=False):
        self.stepped.append(self.robot.target.copy())   # the targets the physics step runs with


def _rig(yaw):
    ids = lambda a, b: torch.tensor(list(range(a, b)), dtype=torch.int32)
    rig = Rig.__new__(Rig)
    rig.torch = torch
    rig.robot = Robot(25, 24, yaw)
    rig.sim = Sim(rig.robot)
    rig.arm, rig.fing, rig.left, rig.left_fing, rig.head, rig.base = (
        ids(0, 9), ids(9, 11), ids(11, 18), ids(18, 20), ids(20, 22), ids(22, 25))
    rig.q_cmd = np.r_[-0.54, 0.0, 0.3, 1.2, 0.0, 1.3, 0.0, 0.0, 0.0]     # lowering the torso
    rig.grip_cmd, rig.left_grip_cmd = 0.04, 0.0
    rig.left_q_cmd = np.linspace(0.1, 0.7, 7)
    rig.head_cmd = np.array([0.0, 0.3])
    rig.base_cmd, rig.base_vel = np.array([4.81, 1.68, math.pi]), np.zeros(3)
    rig._payload_feedforward = lambda: None
    rig._advance_thermal = lambda dt: None
    rig.cams, rig.stride, rig.tick, rig.frames, rig.tick_watchers = {}, 1, 0, [], []
    rig.clear = types.SimpleNamespace(monitor=False)
    return rig


@pytest.fixture(autouse=True)
def _isaac_types(monkeypatch):
    monkeypatch.setitem(sys.modules, "isaacsim.core.utils.types", types.SimpleNamespace(ArticulationAction=Action))


@pytest.mark.parametrize("yaw", [math.pi + 1e-3, -math.pi - 1e-3, math.pi - 1e-3])
def test_targets_survive_the_yaw_wrap(yaw):
    rig = _rig(yaw)
    Rig.step(rig, 1)
    sent = rig.sim.stepped[-1]
    assert np.allclose(sent[0:9], rig.q_cmd)                  # the torso keeps going down
    assert np.allclose(sent[9:11], rig.grip_cmd) and np.allclose(sent[18:20], rig.left_grip_cmd)
    assert np.allclose(sent[11:18], rig.left_q_cmd) and np.allclose(sent[20:22], rig.head_cmd)
    reading = rig.robot.pos[24]
    assert -math.pi <= reading <= math.pi                    # set back by a turn: the same pose
    assert math.isclose(math.cos(reading), math.cos(yaw), abs_tol=1e-9)
    assert abs(sent[24] - reading) <= math.pi                 # the yaw target within half a turn of it
    assert math.isclose(math.cos(sent[24]), -1.0, abs_tol=1e-9)
