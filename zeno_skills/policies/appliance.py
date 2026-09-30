"""Microwave-specific physical button action and demonstration sequence."""

from __future__ import annotations

from .base import AtomicPolicy
from .articulation import OpenPolicy, ClosePolicy
from .. import skills


class MicrowaveStartPolicy(AtomicPolicy):
    """Press start after checking door closure and food in the cavity."""

    def execute(self, name="kitchen_microwave"):
        return skills.press_microwave_start(self.rig, name)


class MicrowaveDoorCycle:
    """Composite demonstration. Use OpenPolicy/ClosePolicy for atomic steps."""

    def __init__(self, rig):
        self.open = OpenPolicy(rig)
        self.close = ClosePolicy(rig)

    def execute(self, name="kitchen_microwave"):
        self.open.execute(name)
        self.close.execute(name)
        return True

