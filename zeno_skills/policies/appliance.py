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
            skills._press_microwave_door_control(self.rig, name)
            return True
        if button == "start":
            if "start_button" not in art:
                raise SkillFailure(f"click {name}: no start button annotation")
            return skills.press_microwave_start(self.rig, name)
        raise ValueError(f"click {name}: unknown button {button!r}")


class MicrowaveStartPolicy(AtomicPolicy):
    """Press start after checking door closure and food in the cavity."""

    def execute(self, name="kitchen_microwave"):
        return skills.press_microwave_start(self.rig, name)


class MicrowaveButtonApproachPolicy(AtomicPolicy):
    """Align closed fingertips at the annotated door or start button."""

    def execute(self, name="kitchen_microwave", *, button="door"):
        return skills.approach_microwave_button(self.rig, name, button)


class MicrowaveButtonPressPolicy(AtomicPolicy):
    """Press only an aligned button, with measured TCP contact error."""

    def execute(self, name="kitchen_microwave", *, button="door"):
        return skills.press_aligned_microwave_button(self.rig, name, button)


class MicrowaveButtonRetractPolicy(AtomicPolicy):
    """Withdraw the hand from a pressed button and check its retreat pose."""

    def execute(self, name="kitchen_microwave", *, button="door"):
        return skills.retract_microwave_button(self.rig, name, button)


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
