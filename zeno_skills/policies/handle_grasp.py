"""Mug-handle pinch from an annotated contact, separate from rim pinch."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..clearance import lifting
from ..evaluator import quat_R
from ..kinematics import gripper_rot
from ..physics import PHYSICS_HZ
from ..rig import SkillFailure


class PickCupHandlePolicy(AtomicPolicy):
    """Pick a mug by its handle: the pick on the motion layers with only its annotated handle pinch in the goal set
    (pick_job kinds ("handle_pinch",); HAND_PLAN 9j), the hold marked a handle grasp (a pour then tips it sideways)."""

    def execute(self, name, hand=None):
        from ..motion_skills import SKILLS, run_skill
        rig = self.rig
        if name not in rig.ann.objects:
            raise SkillFailure(f"pick cup handle: unknown object {name}")
        run_skill(rig, SKILLS["pick"], {"name": name, "kinds": ("handle_pinch",), "hand": hand})
        side = rig.hand_of(name)
        held = rig.held_by(side)
        held["grasp"] = "handle"
        lift = float(rig.obj_pose(name)[0][2])
        rig.log("pick_cup_handle_result", obj=name, hand=side)
        return lift
