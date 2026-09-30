"""Open and close policies for doors, drawers and powered microwaves."""

from __future__ import annotations

from .base import AtomicPolicy
from .. import skills


class OpenPolicy(AtomicPolicy):
    """Open one articulated target, dispatching by annotated mechanism."""

    def execute(self, name, *, goal=None):
        art = self.rig.ann.art(name)
        if art["category"] == "microwave" and "door_button" in art:
            if goal is not None and abs(goal - art["open_q"]) > 0.10:
                raise ValueError("powered microwave open policy only supports its annotated open target")
            return skills.open_microwave_door(self.rig, name)
        return skills.open_articulated(self.rig, name, goal=goal)


class ClosePolicy(AtomicPolicy):
    """Close one articulated target and verify its measured joint value."""

    def execute(self, name):
        art = self.rig.ann.art(name)
        if art["category"] == "microwave" and "door_button" in art:
            return skills.close_microwave_door(self.rig, name)
        return skills.close_articulated(self.rig, name)
