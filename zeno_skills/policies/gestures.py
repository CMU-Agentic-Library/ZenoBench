"""Gesture policies (they move the arm; not migrated to the motion layers yet -- rig.move_to).

policy_071 PointAtPolicy       point the closed right fingers at a target
policy_072 PresentHeldPolicy   hold the carried object in front of the head camera
"""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..kinematics import gripper_rot
from ..perception import look_angles
from ..predicates import entity_point
from ..rig import SkillFailure
from ..skill_jobs.look import drive_head
from .perceive import record_view


class PointAtPolicy(AtomicPolicy):
    """Point the closed fingers at a target from in front of the chest: the point skill (skill_jobs.held.point_job,
    plan_gesture; HAND_PLAN 9h).  A target not in front: the robot turns to it first (FaceTargetPolicy, the task
    layer), then points."""

    def execute(self, target):
        from ..motion_skills import SKILLS, run_skill
        rig = self.rig
        p = entity_point(rig, target)
        x, y, yaw = rig.base_pose()
        fwd = np.array([math.cos(math.radians(yaw)), math.sin(math.radians(yaw))])
        d = np.asarray(p, float)[:2] - np.array([x, y])
        if np.linalg.norm(d) > 1e-6 and (d / np.linalg.norm(d)) @ fwd < 0.2:
            from .base_motion import FaceTargetPolicy
            FaceTargetPolicy(rig).execute(target)
        return run_skill(rig, SKILLS["point"], {"target": target})


class PresentHeldPolicy(AtomicPolicy):
    """Bring the held object in front of the body at eye level and look at it: the present skill
    (skill_jobs.held.present_job, HAND_PLAN 9e) with the hand that holds it."""

    def execute(self, name):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["present"], {"name": name})
