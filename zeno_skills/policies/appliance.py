"""Physical button policies and appliance demonstration sequences."""

from __future__ import annotations

from .base import AtomicPolicy
from .articulation import OpenPolicy, ClosePolicy
from .. import skills
from ..rig import SkillFailure


class ClickPolicy(AtomicPolicy):
    """Physically press an annotated microwave door or start button."""

    def execute(self, name="kitchen_microwave", *, button="door"):
        if self.rig.held is not None:
            raise SkillFailure("click: release the held object before pressing a button")
        art = self.rig.ann.art(name)
        if button == "door":
            if "door_button" not in art:
                raise SkillFailure(f"click {name}: no door button annotation")
            skills.press_button(self.rig, f"{name}/door_button")
            return True
        if button == "start":
            if "start_button" not in art:
                raise SkillFailure(f"click {name}: no start button annotation")
            skills.press_button(self.rig, f"{name}/start_button")
            return True
        raise ValueError(f"click {name}: unknown button {button!r}")


class MicrowaveStartPolicy(AtomicPolicy):
    """Press start after checking door closure and food in the cavity."""

    def execute(self, name="kitchen_microwave"):
        skills.press_button(self.rig, f"{name}/start_button")
        return True


class _RetiredStage(AtomicPolicy):
    """A stage of the old staged press (approach, press, withdraw as three calls): a press is one plan now
    (skills.press_button: run_skill press, skill_plans.plan_press) -- retired (skill_library/check.py
    RETIRED_POLICIES), the id kept."""

    def execute(self, name="kitchen_microwave", *, button="door"):
        raise SkillFailure(f"{type(self).__name__} is retired: press the {button} key with policy_032 / 033 / 094 "
                           f"(one plan: the reach, the press and the way back out)")


class MicrowaveButtonApproachPolicy(_RetiredStage):
    """Retired (policy_027): align closed fingertips at the annotated door or start button."""


class MicrowaveButtonPressPolicy(_RetiredStage):
    """Retired (policy_028): press only an aligned button."""


class MicrowaveButtonRetractPolicy(_RetiredStage):
    """Retired (policy_029): withdraw the hand from a pressed button."""


class MicrowaveDoorClearPolicy(AtomicPolicy):
    """Move clear of the hinge sweep; tuck empty arm or verify held load."""

    def execute(self, name="kitchen_microwave"):
        return skills.clear_microwave_door_sweep(self.rig, name)


class MicrowaveHingeDrivePolicy(AtomicPolicy):
    """Move a powered hinge only from the measured door-clear pose."""

    def execute(self, name="kitchen_microwave", *, target="open"):
        art = self.rig.ann.art(name)
        if art.get("category") != "microwave" or "door_button" not in art:
            raise SkillFailure(f"microwave hinge: {name} is not a powered microwave door")
        if target not in ("open", "close"):
            raise ValueError("microwave hinge target must be open or close")
        q = art["open_q"] if target == "open" else art["closed_q"]
        return skills._set_microwave_hinge(self.rig, name, q, f"{target.upper()} microwave: powered door")


class MicrowaveDoorCycle:
    """Composite demonstration. Use OpenPolicy/ClosePolicy for atomic steps."""

    def __init__(self, rig):
        self.open = OpenPolicy(rig)
        self.close = ClosePolicy(rig)

    def execute(self, name="kitchen_microwave"):
        self.open.execute(name)
        self.close.execute(name)
        return True
