"""Mug-handle pinch from an annotated contact, separate from rim pinch."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..evaluator import quat_R
from ..kinematics import gripper_rot
from ..planner import find_park
from ..rig import SkillFailure


class PickCupHandlePolicy(AtomicPolicy):
    """Approach a mug handle from outside, pinch it, and check a real lift."""

    def execute(self, name):
        rig = self.rig
        if rig.held is not None or rig.left_held is not None:
            raise SkillFailure("pick cup handle: both hands must be empty")
        if name not in rig.ann.objects:
            raise SkillFailure(f"pick cup handle: unknown object {name}")
        obj = rig.ann.objects[name]
        asset = rig.ann.asset_of(obj)
        spec = next((g for g in asset["grasps"] if g["type"] == "handle_pinch"), None)
        if spec is None:
            raise SkillFailure(f"pick cup handle: {obj['asset']} has no handle contact annotation")
        if not rig.stage.GetPrimAtPath(obj["body"] + "/handle_collider"):
            raise SkillFailure("pick cup handle: construct the rig with handle_objects=(name,)")

        def contact():
            pos, quat = rig.obj_pose(name)
            B = quat_R(quat)
            p = pos+B @ np.asarray(spec["center"], float)
            approach = B @ np.asarray(spec["approach"], float)
            close = B @ np.asarray(spec["close_dir"], float)
            R = gripper_rot(approach, close)
            return pos, p, R, approach

        before, p, R, approach = contact()
        pre = p-0.10*approach+np.array([0, 0, 0.02])
        lift = p+np.array([0, 0, 0.08])
        rig.sync_world()
        park = find_park(rig.kin, rig.world, [(pre, R), (p, R), (lift, R)],
                         near=rig.base_pose(), q_start=rig.q_cmd,
                         travel_q=skills._travel_q(rig), max_tries=160)
        if park is None:
            raise SkillFailure(f"pick cup handle {name}: no reachable contact path")
        skills._goto_park(rig, park)
        before, p, R, approach = contact()
        pre = p-0.10*approach+np.array([0, 0, 0.02])
        rig.grip(float(spec["pre_open"]), 40)
        rig.move_to(pre, R, step=0.01, label="handle_pick_pre")
        rig.move_to(p, R, step=0.004, label="handle_pick_contact")
        fingers = rig.grip(0.0, 120)
        rig.move_to(p+np.array([0, 0, 0.08]), R, step=0.004,
                    steps_per_wp=5, label="handle_pick_lift", collision=False)
        rig.step(40)
        after, _ = rig.obj_pose(name)
        lift_m = float(after[2]-before[2])
        if fingers.min() < 0.003 or lift_m < 0.02:
            raise SkillFailure(f"pick cup handle {name}: failed contact/lift, {lift_m:.3f} m")
        tcp, actual_R = rig.kin.tcp(rig.q())
        rig.held = {"name": name, "kind": "pinch", "tcp_minus_body": tcp-after,
                    "R": actual_R, "pre_open": float(spec["pre_open"])}
        skills.check_held(rig, "pick_cup_handle")
        rig.log("pick_cup_handle_result", obj=name, lift_m=round(lift_m, 4),
                fingers=fingers.tolist())
        return lift_m
