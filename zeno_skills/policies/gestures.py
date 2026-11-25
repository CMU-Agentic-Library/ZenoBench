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
    """Point the closed right fingers at a target from in front of the chest."""

    def execute(self, target):
        rig = self.rig
        p = entity_point(rig, target)
        x, y, yaw = rig.base_pose()
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        shoulder = np.array([x + 0.09 * c + 0.18 * s, y + 0.09 * s - 0.18 * c, 1.05])
        d = p - shoulder
        d /= np.linalg.norm(d)
        if d[:2] @ np.array([c, s]) < 0.2:
            from .base_motion import FaceTargetPolicy
            FaceTargetPolicy(rig).execute(target)
            return self.execute(target)
        side = np.cross(d, [0, 0, 1.0])
        side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-6 else np.array([0, 1.0, 0])
        R = gripper_rot(d, side)
        if rig.held is None:
            rig.grip(0.0, 40)
        last = None
        for reach in (0.45, 0.38, 0.52, 0.30):
            tcp = shoulder + d * reach
            try:
                rig.move_to(tcp, R, label="point", smooth=True)
                break
            except SkillFailure as exc:
                last = exc
        else:
            raise last
        tcp, R2 = rig.kin.tcp(rig.q())
        v = p - tcp
        ang = math.degrees(math.acos(np.clip((-R2[:, 2]) @ v / np.linalg.norm(v), -1, 1)))
        rig.log("point_result", target=target, angle_deg=round(ang, 2))
        if ang > 8.0:
            raise SkillFailure(f"point at {target}: {ang:.1f} deg off")
        return ang


class PresentHeldPolicy(AtomicPolicy):
    """Bring the held object in front of the body at eye level and look at it: the present skill
    (skill_jobs.held.present_job, HAND_PLAN 9e) with the hand that holds it."""

    def execute(self, name):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["present"], {"name": name})
