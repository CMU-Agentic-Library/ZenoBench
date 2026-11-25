"""Gesture policies: the point and present skills (motion_skills.run_skill; HAND_PLAN 9e / 9h), either hand.

policy_071 PointAtPolicy       point the closed fingers at a target (the robot turned to it first when it is not in front)
policy_072 PresentHeldPolicy   hold the carried object in front of the head camera
"""

from __future__ import annotations

from .base import AtomicPolicy


class PointAtPolicy(AtomicPolicy):
    """Point the closed fingers at a target from in front of the chest: the point skill (skill_jobs.held.point_job,
    plan_gesture; HAND_PLAN 9h).  A target not in front: the robot turns to it first (FaceTargetPolicy, the task
    layer), then points."""

    def execute(self, target):
        from ..motion_skills import SKILLS, run_skill
        from ..skill_jobs.held import point_in_front
        rig = self.rig
        if not point_in_front(rig, target):        # the skill's own test (one source): else it would refuse
            from .base_motion import FaceTargetPolicy
            FaceTargetPolicy(rig).execute(target)
        return run_skill(rig, SKILLS["point"], {"target": target})


class PresentHeldPolicy(AtomicPolicy):
    """Bring the held object in front of the body at eye level and look at it: the present skill
    (skill_jobs.held.present_job, HAND_PLAN 9e) with the hand that holds it."""

    def execute(self, name):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["present"], {"name": name})
