"""Planning-only policies: compute the numeric target a motion policy needs
from a scene noun, without moving anything.  Contracts chain them in front of
pose-parameterised policies (e.g. policy_097 -> policy_001), passing the result
through ``{"from": "<step>.<key>"}`` arguments.

policy_095 PlanHomePolicy      joint vector of the home posture
policy_097 PlanStandoffPolicy  free base pose next to a place
policy_098 PlanReachPolicy     right TCP pose that reaches a target
policy_099 PlanHeadingPolicy   in-place yaw change that faces a target
policy_100 PlanRetreatPolicy   signed forward distance that backs away from a place
policy_101 PlanPointPolicy     right TCP pose that points at a target
"""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from ..kinematics import gripper_rot
from ..predicates import entity_footprint, entity_point, reach_targets
from ..rig import SkillFailure
from ..skill_jobs.carry import _carry_bottom_z      # noqa: F401  (policies chain it: PlanStandoffPolicy)


class PlanHomePolicy(AtomicPolicy):
    def execute(self):
        q = self.rig.kin.rest.copy()
        q[0] = self.rig.kin.hi[0]
        q[1] = 0.0
        return {"target": q.tolist()}


class PlanStandoffPolicy(AtomicPolicy):
    def execute(self, place):
        from .base_motion import standoff_poses
        poses = standoff_poses(self.rig, place)
        if not poses:
            raise SkillFailure(f"plan stand-off {place}: no free pose")
        return {"pose": [float(v) for v in poses[0]], "carry_bottom_z": _carry_bottom_z(self.rig, place)}


class PlanReachPolicy(AtomicPolicy):
    def execute(self, target):
        p, R = reach_targets(self.rig, target)[0]
        return {"position": np.asarray(p, float).tolist(), "rotation": np.asarray(R, float).tolist()}


class PlanHeadingPolicy(AtomicPolicy):
    def execute(self, target):
        x, y, yaw = self.rig.base_pose()
        p = entity_point(self.rig, target)
        bearing = math.degrees(math.atan2(p[1] - y, p[0] - x))
        return {"delta_yaw_deg": float((bearing - yaw + 180) % 360 - 180)}


class PlanRetreatPolicy(AtomicPolicy):
    def execute(self, place, distance_m):
        rig = self.rig
        box = entity_footprint(rig, place)
        x, y, yaw = rig.base_pose()
        dx = max(box[0] - x, 0.0, x - box[2])
        dy = max(box[1] - y, 0.0, y - box[3])
        gap = math.hypot(dx, dy)
        need = max(0.0, float(distance_m) - gap) + 0.02
        nearest = np.array([min(max(x, box[0]), box[2]), min(max(y, box[1]), box[3])])
        heading = np.array([math.cos(math.radians(yaw)), math.sin(math.radians(yaw))])
        toward = nearest - np.array([x, y])
        if np.linalg.norm(toward) > 1e-6 and heading @ toward < 0:
            raise SkillFailure(f"plan retreat {place}: the place is behind the robot; turn first")
        return {"forward_m": -float(need)}


class PlanPointPolicy(AtomicPolicy):
    def execute(self, target):
        rig = self.rig
        p = entity_point(rig, target)
        x, y, yaw = rig.base_pose()
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        shoulder = np.array([x + 0.09 * c + 0.18 * s, y + 0.09 * s - 0.18 * c, 1.05])
        d = p - shoulder
        d /= np.linalg.norm(d)
        side = np.cross(d, [0, 0, 1.0])
        side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-6 else np.array([0, 1.0, 0])
        return {"position": (shoulder + d * 0.42).tolist(), "rotation": gripper_rot(d, side).tolist()}
