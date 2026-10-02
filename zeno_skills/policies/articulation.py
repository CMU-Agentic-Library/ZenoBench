"""Handle-driven and powered open/close policies for annotated joints."""

from __future__ import annotations

from .base import AtomicPolicy
from .. import skills
from ..rig import SkillFailure


def _powered(rig, name):
    art = rig.ann.art(name)
    return art["category"] == "microwave" and "door_button" in art


class HandleOpenPolicy(AtomicPolicy):
    """Pull a door or drawer handle and verify measured joint travel."""

    def execute(self, name, *, goal=None):
        art = self.rig.ann.art(name)
        if not art.get("handle") or _powered(self.rig, name):
            raise SkillFailure(f"handle open {name}: no manual handle route")
        return skills.open_articulated(self.rig, name, goal=goal)


class HandleClosePolicy(AtomicPolicy):
    """Push a handle-operated door or drawer to its closed joint value."""

    def execute(self, name):
        art = self.rig.ann.art(name)
        if not art.get("handle") or _powered(self.rig, name):
            raise SkillFailure(f"handle close {name}: no manual handle route")
        return skills.close_articulated(self.rig, name)


class PoweredDoorOpenPolicy(AtomicPolicy):
    """Press the microwave door button and drive its physical hinge open."""

    def execute(self, name):
        if not _powered(self.rig, name):
            raise SkillFailure(f"powered open {name}: no powered microwave route")
        return skills.open_microwave_door(self.rig, name)


class PoweredDoorClosePolicy(AtomicPolicy):
    """Drive a powered microwave hinge closed after moving clear."""

    def execute(self, name):
        if not _powered(self.rig, name):
            raise SkillFailure(f"powered close {name}: no powered microwave route")
        return skills.close_microwave_door(self.rig, name)


class OpenPolicy(AtomicPolicy):
    """Open one target, selecting the physical strategy from its annotation."""

    def execute(self, name, *, goal=None):
        art = self.rig.ann.art(name)
        if _powered(self.rig, name):
            if goal is not None and abs(goal - art["open_q"]) > 0.10:
                raise ValueError("powered microwave open policy only supports its annotated open target")
            return PoweredDoorOpenPolicy(self.rig).execute(name)
        return HandleOpenPolicy(self.rig).execute(name, goal=goal)


class ClosePolicy(AtomicPolicy):
    """Close one target, selecting the physical strategy from its annotation."""

    def execute(self, name):
        if _powered(self.rig, name):
            return PoweredDoorClosePolicy(self.rig).execute(name)
        return HandleClosePolicy(self.rig).execute(name)
