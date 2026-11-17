"""The posture policies (docs/MOTION_ARCHITECTURE.md 2.3, 9.3 step 5): each is run_skill of a posture skill --
tuck (an empty arm's fold), crouch / stand (the torso lift), bend / straighten (the waist pitch).  The plan,
its checks and the result are the skill's (skill_plans.posture, skill_jobs.posture): one leg where the robot
stands, nothing tried instead when it cannot be made."""

from __future__ import annotations

from .base import AtomicPolicy


def _posture(rig, skill, joint, target, as_far=False):
    """run_skill of the posture skill ``skill``: ``joint`` to ``target``, or (``as_far``: a limit) as far toward
    it as both arms ride the body free (skill_jobs.posture.body_job)."""
    from ..motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS[skill], {"joint": joint, "target": float(target), "as_far": bool(as_far)})


class TuckArmPolicy(AtomicPolicy):
    """Fold the empty right arm to its travel posture (the body with it unless the left hand holds something)."""

    def execute(self):
        from ..motion_skills import SKILLS, run_skill
        run_skill(self.rig, SKILLS["tuck"], {"hand": "right"})
        return True


class SetTorsoHeightPolicy(AtomicPolicy):
    """The torso lift to a joint height, everything else riding it as it is (crouch)."""
    skill = "crouch"

    def execute(self, height, as_far=False):
        return _posture(self.rig, self.skill, "torso_lift_joint", height, as_far)


class LowerTorsoPolicy(SetTorsoHeightPolicy):
    """The torso as low as it goes (toward its lower limit, as far as both arms ride it free), or a requested
    joint height."""

    def execute(self, height=None):
        idx = self.rig.kin.names.index("torso_lift_joint")
        return super().execute(self.rig.kin.lo[idx] if height is None else height, as_far=height is None)


class RaiseTorsoPolicy(SetTorsoHeightPolicy):
    """The torso as high as it goes (toward its upper limit), or a requested joint height (stand)."""
    skill = "stand"

    def execute(self, height=None):
        idx = self.rig.kin.names.index("torso_lift_joint")
        return super().execute(self.rig.kin.hi[idx] if height is None else height, as_far=height is None)


class SetWaistPitchPolicy(AtomicPolicy):
    """The waist to a pitch (rad), everything else riding it as it is (bend)."""
    skill = "bend"

    def execute(self, pitch_rad, as_far=False):
        return _posture(self.rig, self.skill, "waist_pitch_joint", pitch_rad, as_far)


class LeanForwardPolicy(SetWaistPitchPolicy):
    """Bend forward as far as it goes (toward the upper limit), or to a requested angle."""

    def execute(self, pitch_rad=None):
        idx = self.rig.kin.names.index("waist_pitch_joint")
        return super().execute(self.rig.kin.hi[idx] if pitch_rad is None else pitch_rad, as_far=pitch_rad is None)


class StraightenWaistPolicy(SetWaistPitchPolicy):
    """The waist back to upright (straighten)."""
    skill = "straighten"

    def execute(self):
        return super().execute(0.0)
