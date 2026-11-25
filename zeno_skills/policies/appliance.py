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
    """Retired (policy_030): move clear of the door's swing to a hand-written pose.  The door key's press plans
    its park clear of the swing itself (skills.press_button door=, skill_plans.plan_press press_door)."""

    def execute(self, name="kitchen_microwave"):
        raise SkillFailure("MicrowaveDoorClearPolicy is retired: open / close the microwave (its door key's press "
                           "parks clear of the door's swing)")


class MicrowaveHingeDrivePolicy(AtomicPolicy):
    """Retired (policy_031): drive the powered hinge with no press -- the door moves only by its key now."""

    def execute(self, name="kitchen_microwave", *, target="open"):
        raise SkillFailure("MicrowaveHingeDrivePolicy is retired: the door moves by its key (open / close)")


class MicrowaveDoorCycle:
    """Composite demonstration. Use OpenPolicy/ClosePolicy for atomic steps."""

    def __init__(self, rig):
        self.open = OpenPolicy(rig)
        self.close = ClosePolicy(rig)

    def execute(self, name="kitchen_microwave"):
        self.open.execute(name)
        self.close.execute(name)
        return True
