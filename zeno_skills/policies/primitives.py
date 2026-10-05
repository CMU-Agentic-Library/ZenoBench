"""Small measured actuator policies for the right hand and arm."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..kinematics import FINGER_OPEN
from ..rig import SkillFailure


def _width(width):
    value = float(width)
    if not np.isfinite(value) or not 0.0 <= value <= FINGER_OPEN:
        raise ValueError(f"finger position must be in [0, {FINGER_OPEN}] m per finger")
    return value


class RightGripperOpenPolicy(AtomicPolicy):
    """Open an empty right gripper; read back both finger joint positions."""

    def execute(self, width=FINGER_OPEN, *, tolerance=0.005):
        width = _width(width)
        if self.rig.held is not None:
            raise SkillFailure("gripper open: release the held object through a place policy")
        actual = np.asarray(self.rig.grip(width), dtype=float)
        if actual.shape != (2,) or np.max(np.abs(actual - width)) > tolerance:
            raise SkillFailure(f"gripper open: fingers did not reach {width:.3f} m")
        return actual


class RightGripperClosePolicy(AtomicPolicy):
    """Close empty right gripper; report its measured gap, without claiming a grasp."""

    def execute(self, width=0.0, *, tolerance=0.005):
        width = _width(width)
        if self.rig.held is not None:
            raise SkillFailure("gripper close: an object is already held")
        actual = np.asarray(self.rig.grip(width), dtype=float)
        if actual.shape != (2,) or np.max(np.abs(actual - width)) > tolerance:
            raise SkillFailure(f"gripper close: fingers did not reach {width:.3f} m")
        return actual


class RightTcpMovePolicy(AtomicPolicy):
    """Move right TCP to a Cartesian pose and check measured position and attitude."""

    def execute(self, position, rotation, *, step=0.01, position_tolerance=0.03,
                rotation_tolerance=0.15):
        p = np.asarray(position, dtype=float)
        R = np.asarray(rotation, dtype=float)
        if p.shape != (3,) or R.shape != (3, 3) or not np.all(np.isfinite(p)) or not np.all(np.isfinite(R)):
            raise ValueError("TCP target must be a finite xyz position and 3x3 rotation")
        if not np.allclose(R.T @ R, np.eye(3), atol=1e-3) or not np.isclose(np.linalg.det(R), 1.0, atol=1e-3):
            raise ValueError("TCP rotation must be a proper orthonormal matrix")
        if step <= 0 or position_tolerance <= 0 or rotation_tolerance <= 0:
            raise ValueError("TCP step and tolerances must be positive")
        self.rig.move_to(p, R, step=step, label="right_tcp_move")
        actual_p, actual_R = self.rig.kin.tcp(self.rig.q())
        p_error = float(np.linalg.norm(actual_p - p))
        cos_angle = np.clip((np.trace(R.T @ actual_R) - 1.0) / 2.0, -1.0, 1.0)
        angle_error = float(np.arccos(cos_angle))
        if p_error > position_tolerance or angle_error > rotation_tolerance:
            raise SkillFailure(f"right TCP: position error {p_error:.3f} m, rotation error {angle_error:.3f} rad")
        if self.rig.held is not None:
            skills.check_held(self.rig, "right_tcp_move")
        return {"position_error_m": p_error, "rotation_error_rad": angle_error}


class RightJointMovePolicy(AtomicPolicy):
    """Move the nine controlled torso, waist and right-arm joints to a target vector."""

    def execute(self, target, *, tolerance=0.03):
        q_goal = np.asarray(target, dtype=float)
        if q_goal.shape != self.rig.q_cmd.shape or not np.all(np.isfinite(q_goal)):
            raise ValueError("joint target must match the controlled joint vector")
        # The simulated joint readback can sit a fraction of a millimetre
        # outside a URDF endpoint (notably the torso's -0.0001 m upper limit).
        # Accept only that small boundary noise and clamp the commanded goal.
        below = q_goal < self.rig.kin.lo - 0.005
        above = q_goal > self.rig.kin.hi + 0.005
        if np.any(below | above):
            bad = [(self.rig.kin.names[i], round(float(q_goal[i]), 4),
                    round(float(self.rig.kin.lo[i]), 4), round(float(self.rig.kin.hi[i]), 4))
                   for i in np.flatnonzero(below | above)]
            raise ValueError(f"joint target exceeds robot limits (name, target, lo, hi): {bad}")
        q_goal = np.clip(q_goal, self.rig.kin.lo, self.rig.kin.hi)
        if tolerance <= 0:
            raise ValueError("joint tolerance must be positive")
        self.rig.sync_world()
        path = self.rig.joint_path(q_goal, label="right_joint_move", check=True)
        self.rig.follow(path)
        actual = np.asarray(self.rig.q(), dtype=float)
        if np.max(np.abs(actual - q_goal)) > tolerance:
            raise SkillFailure("right joint move: measured joints missed target")
        if self.rig.held is not None:
            skills.check_held(self.rig, "right_joint_move")
        return actual
