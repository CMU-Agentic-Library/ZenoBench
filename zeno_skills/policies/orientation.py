"""Correct the orientation of an already grasped object."""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from .base import AtomicPolicy
from .. import skills
from ..evaluator import quat_R
from ..rig import SkillFailure


class UprightObjectPolicy(AtomicPolicy):
    """Lift and rotate a right-held object's local up axis to world vertical."""

    def execute(self, name, *, max_tilt_deg=15.0):
        rig = self.rig
        if rig.held is None or rig.held["name"] != name or rig.left_held is not None:
            raise SkillFailure(f"upright {name}: requires a right-only grasp of this object")
        skills.check_held(rig, "upright_start")
        body, quat = rig.obj_pose(name)
        body_R = quat_R(quat)
        tilt = math.degrees(math.acos(np.clip(body_R[2, 2], -1.0, 1.0)))
        if tilt <= max_tilt_deg:
            rig.log("upright_result", obj=name, tilt_deg=round(tilt, 3))
            return tilt
        axis = body_R[:2, 0]
        if np.linalg.norm(axis) < 0.2:
            axis = np.array([body_R[1, 1], -body_R[0, 1]])
        yaw = math.atan2(axis[1], axis[0])
        desired_body_R = Rotation.from_euler("z", yaw).as_matrix()
        tcp, tcp_R = rig.kin.tcp(rig.q())
        desired_tcp_R = desired_body_R @ body_R.T @ tcp_R
        lift = max(0.12, 0.5*max(rig.ann.asset_of(rig.ann.objects[name])["size"]))
        rig.move_to(tcp+np.array([0, 0, lift]), tcp_R, label="upright_clear")
        skills.check_held(rig, "upright_clear")
        tcp, _ = rig.kin.tcp(rig.q())
        rig.move_to(tcp, desired_tcp_R, step=0.01, steps_per_wp=5, label="upright_rotate")
        skills.check_held(rig, "upright_rotate")
        body, quat = rig.obj_pose(name)
        actual_R = quat_R(quat)
        actual = math.degrees(math.acos(np.clip(actual_R[2, 2], -1.0, 1.0)))
        tcp, tcp_R = rig.kin.tcp(rig.q())
        rig.held["tcp_minus_body"] = tcp-body
        rig.held["R"] = tcp_R
        rig.log("upright_result", obj=name, before_deg=round(tilt, 3), tilt_deg=round(actual, 3))
        if actual > max_tilt_deg:
            raise SkillFailure(f"upright {name}: remaining tilt {actual:.1f} degrees")
        return actual
