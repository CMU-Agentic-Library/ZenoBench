"""Appliance policies that work from the annotation, for any appliance.

policy_094 PressButtonPolicy   park, align closed fingertips, press, retract (any annotated button)
policy_090 WaitHeatPolicy      wait until a food reaches a temperature on any heat source, then stop it
policy_089 WaitCoolPolicy      wait until a food in the closed refrigerator cools below a temperature
"""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..kinematics import gripper_rot
from ..planner import find_park
from ..predicates import entity_kind
from ..rig import SkillFailure


def button_record(rig, button):
    kind, rec = entity_kind(rig.ann, button)
    if kind != "button":
        raise SkillFailure(f"press: {button} is not an annotated button")
    return rec


class PressButtonPolicy(AtomicPolicy):
    """Press an annotated button with the closed right fingertips.

    Microwave buttons go through the measured microwave stages (policy_027,
    028, 029), which also start the heating cycle for the start key.  Other
    buttons (the stove power key) toggle their appliance's heat source."""

    def execute(self, button, *, state=None):
        rig = self.rig
        rec = button_record(rig, button)
        app, which = rec["appliance"], rec["button"]
        if rig.held is not None:
            raise SkillFailure("press: release the held object first")
        if which in ("door_button", "start_button"):
            kind = "door" if which == "door_button" else "start"
            skills.approach_microwave_button(rig, app, kind)
            skills.press_aligned_microwave_button(rig, app, kind)
            skills.retract_microwave_button(rig, app, kind)
            return True
        thermal = getattr(rig, "thermal", None)
        current = bool(thermal.on.get(app)) if thermal is not None else False
        if state is not None and bool(state) == current:
            rig.log("button_already", button=button, on=current)
            return current
        c = np.asarray(rec["center"], float)
        out = np.asarray(rec["outward"], float)
        R = gripper_rot(-out, [1.0, 0.0, 0.0])
        pre, contact = c + out * 0.12, c + out * 0.005
        targets = [(pre + np.array([0, 0, 0.06]), R), (pre, R)]
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        # the press itself is part of the search: a park that only reaches the
        # pre-pose can leave the last 11 cm forward without IK
        park = find_park(rig.kin, rig.world, targets + [(contact + out * 0.01, R)], near=rig.base_pose(),
                         max_tries=200, q_start=rig.q_cmd, travel_q=rig.kin.rest)
        if park is None:
            raise SkillFailure(f"press {button}: no collision-free reach")
        skills._goto_park(rig, park)
        rig.grip(0.0, 40)
        rig.caption = f"PRESS {button}"
        rig.move_to(*targets[0], label="button_pre", q_hint=park[3][0])
        rig.move_to(*targets[1], step=0.005, label="button_align", collision=False)
        rig.move_to(contact, R, step=0.003, label="button_press", collision=False)
        rig.step(24)
        tcp, _ = rig.kin.tcp(rig.q())
        miss = float(np.linalg.norm(tcp - contact))
        if miss > 0.035:
            raise SkillFailure(f"press {button}: missed by {miss:.3f} m")
        if thermal is not None and app in thermal.on:
            thermal.on[app] = not current
        rig.log("button_press", button=button, appliance=app, error_m=round(miss, 4),
                on=bool(thermal.on.get(app)) if thermal is not None else None)
        rig.move_to(pre, R, step=0.005, label="button_retract", collision=False)
        return bool(thermal.on.get(app)) if thermal is not None else True


class WaitHeatPolicy(AtomicPolicy):
    """Let simulated time pass until the food reaches ``min_temp_c`` while its
    heat source stays on; then switch the source off (microwave: cycle end;
    stove: press the power key again)."""

    def execute(self, name, min_temp_c, appliance, *, max_wait_s=90.0):
        rig = self.rig
        th = getattr(rig, "thermal", None)
        if th is None or name not in th.temperatures_c:
            raise SkillFailure(f"wait heat: {name} has no thermal state")
        for _ in range(int(math.ceil(max_wait_s))):
            if th.temperatures_c[name] >= float(min_temp_c):
                break
            if not th.on.get(appliance):
                raise SkillFailure(f"wait heat: {appliance} switched off before the target")
            rig.step(120)
        t = float(th.temperatures_c[name])
        if t < float(min_temp_c):
            raise SkillFailure(f"wait heat: {t:.1f} C below {min_temp_c} C")
        kind, rec = entity_kind(rig.ann, appliance)
        if kind == "appliance" and "power_button" in rec:
            PressButtonPolicy(rig).execute(f"{appliance}/power_button", state=False)
        else:
            th.on[appliance] = False
        rig.log("heat_done", food=name, appliance=appliance, temp_c=round(t, 1))
        return t


class WaitCoolPolicy(AtomicPolicy):
    """Let simulated time pass until the food in the closed refrigerator is at
    or below ``max_temp_c``."""

    def execute(self, name, max_temp_c, appliance="breakfast_fridge", *, max_wait_s=120.0):
        rig = self.rig
        th = getattr(rig, "thermal", None)
        if th is None or name not in th.temperatures_c:
            raise SkillFailure(f"wait cool: {name} has no thermal state")
        a = rig.ann.art(appliance)
        for _ in range(int(math.ceil(max_wait_s))):
            if th.temperatures_c[name] <= float(max_temp_c):
                break
            if abs(rig.joint(appliance) - a["closed_q"]) > 0.10:
                raise SkillFailure(f"wait cool: {appliance} door is open")
            rig.step(120)
        t = float(th.temperatures_c[name])
        rig.log("cool_done", food=name, appliance=appliance, temp_c=round(t, 1))
        if t > float(max_temp_c):
            raise SkillFailure(f"wait cool: {t:.1f} C above {max_temp_c} C")
        return t
