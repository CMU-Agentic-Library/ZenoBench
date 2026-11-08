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
        from .. import skills
        if not skills.fold_where_possible(self.rig, "tuck_arm"):
            raise SkillFailure("tuck arm: no collision-free retreat")
        if np.max(np.abs(self.rig.q() - self.rig.q_cmd)) > 0.05:
            raise SkillFailure("tuck arm: posture did not settle")
        return True


def _move_posture_joint(rig, joint_name, target, tolerance):
    """Move one posture joint.  Empty-handed, tuck first if the initial arm sweep is blocked; then
    (or with a load: the held object is in the plan's collision model) the least base move after
    which the joint moves straight clear of everything (skills.relocate); the grasp is checked
    afterwards."""
    idx = rig.kin.names.index(joint_name)
    target = float(target)
    lo, hi = float(rig.kin.lo[idx]), float(rig.kin.hi[idx])
    if not lo <= target <= hi:
        raise ValueError(f"{joint_name} target {target:.3f} outside [{lo:.3f}, {hi:.3f}]")
    from .. import skills

    def plan():
        rig.sync_world()
        q_goal = rig.q_cmd.copy()
        q_goal[idx] = target
        return rig.joint_path(q_goal, joint_name)

    old_kw = rig.kin.coll_kw
    rig.kin.coll_kw = {}
    try:
        def reposition():
            q_goal = rig.q_cmd.copy()
            q_goal[idx] = target
            skills.relocate(rig, None, [(joint_name, (q_goal, rig.left_q_cmd.copy()))], label=joint_name,
                            speed=0.15, turn=0.4)
        try:
            rig.follow(plan())
        except SkillFailure:
            if rig.held is not None:
                reposition()            # the load would sweep into the furniture in front
            else:
                TuckArmPolicy(rig).execute()
                try:
                    rig.follow(plan())
                except SkillFailure:
                    reposition()        # the tucked hand would sweep into the furniture in front
    finally:
        rig.kin.coll_kw = old_kw
    skills.check_held(rig, joint_name)
    skills.check_left_held(rig, joint_name)
    actual = float(rig.q()[idx])
    if abs(actual - target) > tolerance:
        raise SkillFailure(f"{joint_name}: actual {actual:.3f}, target {target:.3f}")
    rig.log("posture_joint", joint=joint_name, target=round(target, 3), actual=round(actual, 3),
            held=(rig.held or {}).get("name"))
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
