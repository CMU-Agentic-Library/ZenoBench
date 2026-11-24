"""Appliance policies that work from the annotation, for any appliance.

policy_094 PressButtonPolicy   press any annotated button (skills.press_button: run_skill press)
policy_090 WaitHeatPolicy      wait until a food reaches a temperature on any heat source, then stop it
policy_089 WaitCoolPolicy      wait until a food in the closed refrigerator cools below a temperature
"""

from __future__ import annotations

import math

from .base import AtomicPolicy
from .. import skills
from ..physics import PHYSICS_HZ
from ..predicates import entity_kind
from ..rig import SkillFailure


def button_record(rig, button):
    kind, rec = entity_kind(rig.ann, button)
    if kind != "button":
        raise SkillFailure(f"press: {button} is not an annotated button")
    return rec


class PressButtonPolicy(AtomicPolicy):
    """Press an annotated button with the closed right fingertips (skills.press_button: run_skill press,
    one plan from a park whose search checks the press itself).

    The microwave's start key starts its cycle (door closed, food inside), its door key only records the
    press (open drives the door); another key (the stove's power key) switches its appliance's heat
    source: to ``state`` when given -- already there, nothing is pressed -- else to the other one."""

    def execute(self, button, *, state=None):
        rig = self.rig
        rec = button_record(rig, button)
        app, which = rec["appliance"], rec["button"]
        if rig.held is not None:
            raise SkillFailure("press: release the held object first")
        if which in ("door_button", "start_button"):
            skills.press_button(rig, button)
            return True
        thermal = getattr(rig, "thermal", None)
        current = bool(thermal.on.get(app)) if thermal is not None else False
        if state is not None and bool(state) == current:
            rig.log("button_already", button=button, on=current)
            return current
        return skills.press_button(rig, button, on=not current if thermal is not None and app in thermal.on else None)


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
            rig.step(PHYSICS_HZ)
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
            rig.step(PHYSICS_HZ)
        t = float(th.temperatures_c[name])
        rig.log("cool_done", food=name, appliance=appliance, temp_c=round(t, 1))
        if t > float(max_temp_c):
            raise SkillFailure(f"wait cool: {t:.1f} C above {max_temp_c} C")
        return t
