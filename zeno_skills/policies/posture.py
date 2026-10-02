"""Measured right-arm, torso-lift, and waist-pitch posture policies."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy
from ..rig import SkillFailure


class TuckArmPolicy(AtomicPolicy):
    """Move the right arm into a collision-checked travel posture."""

    def execute(self):
        if self.rig.held is not None:
            raise SkillFailure("tuck arm: release the held object first")
        if not self.rig.tuck():
            raise SkillFailure("tuck arm: no collision-free retreat")
        if np.max(np.abs(self.rig.q() - self.rig.q_cmd)) > 0.05:
            raise SkillFailure("tuck arm: posture did not settle")
        return True


def _move_posture_joint(rig, joint_name, target, tolerance):
    """Move one posture joint; tuck first if the initial arm sweep is blocked."""
    if rig.held is not None:
        raise SkillFailure(f"{joint_name}: release the held object first")
    idx = rig.kin.names.index(joint_name)
    target = float(target)
    lo, hi = float(rig.kin.lo[idx]), float(rig.kin.hi[idx])
    if not lo <= target <= hi:
        raise ValueError(f"{joint_name} target {target:.3f} outside [{lo:.3f}, {hi:.3f}]")
    q_goal = rig.q_cmd.copy()
    q_goal[idx] = target
    rig.sync_world()
    old_kw = rig.kin.coll_kw
    rig.kin.coll_kw = {}
    try:
        try:
            path = rig.joint_path(q_goal, joint_name)
        except SkillFailure:
            TuckArmPolicy(rig).execute()
            rig.sync_world()
            q_goal = rig.q_cmd.copy()
            q_goal[idx] = target
            path = rig.joint_path(q_goal, joint_name)
        rig.follow(path)
    finally:
        rig.kin.coll_kw = old_kw
    actual = float(rig.q()[idx])
    if abs(actual - target) > tolerance:
        raise SkillFailure(f"{joint_name}: actual {actual:.3f}, target {target:.3f}")
    rig.log("posture_joint", joint=joint_name, target=round(target, 3), actual=round(actual, 3))
    return actual


class SetTorsoHeightPolicy(AtomicPolicy):
    """Move the torso lift to a joint height, keeping other right-arm joints fixed."""

    def execute(self, height):
        return _move_posture_joint(self.rig, "torso_lift_joint", height, 0.02)


class LowerTorsoPolicy(SetTorsoHeightPolicy):
    """Lower the torso to its safe kinematic limit, or a requested joint height."""

    def execute(self, height=None):
        idx = self.rig.kin.names.index("torso_lift_joint")
        return super().execute(self.rig.kin.lo[idx] if height is None else height)


class RaiseTorsoPolicy(SetTorsoHeightPolicy):
    """Raise the torso to its safe kinematic limit, or a requested joint height."""

    def execute(self, height=None):
        idx = self.rig.kin.names.index("torso_lift_joint")
        return super().execute(self.rig.kin.hi[idx] if height is None else height)


class SetWaistPitchPolicy(AtomicPolicy):
    """Bend the waist to a specified radian angle with collision checks."""

    def execute(self, pitch_rad):
        return _move_posture_joint(self.rig, "waist_pitch_joint", pitch_rad, 0.035)


class LeanForwardPolicy(SetWaistPitchPolicy):
    """Bend forward to the safe kinematic limit or a requested angle."""

    def execute(self, pitch_rad=None):
        idx = self.rig.kin.names.index("waist_pitch_joint")
        return super().execute(self.rig.kin.hi[idx] if pitch_rad is None else pitch_rad)


class StraightenWaistPolicy(SetWaistPitchPolicy):
    """Return the waist to neutral pitch."""

    def execute(self):
        return super().execute(0.0)
