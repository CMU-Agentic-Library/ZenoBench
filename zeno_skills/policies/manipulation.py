"""Object manipulation policies; geometry and control live in skills.py."""

from __future__ import annotations

from .base import AtomicPolicy
from .. import skills


class PickPolicy(AtomicPolicy):
    """Select an annotated grasp route for the concrete target object."""

    def execute(self, name, *, max_candidates=12):
        return skills.pick(self.rig, name, max_candidates=max_candidates)


class PlacePolicy(AtomicPolicy):
    """Place the held object on a surface or inside a container."""

    def execute(self, name, support, xy=None):
        return skills.place(self.rig, name, support, xy)

    def on(self, name, support, *, hint=None, tries=4):
        """Find a free spot on a named support and place there."""
        return skills.place_on(self.rig, name, support, hint=hint, tries=tries)


class PushPolicy(AtomicPolicy):
    """Push or drag one object along its current annotated support."""

    def execute(self, name, support, direction, distance, *, label="PUSH", enough=None):
        return skills.push(self.rig, name, support, direction, distance, label=label, enough=enough)
