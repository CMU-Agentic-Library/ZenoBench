"""Base-motion atomic policy."""

from __future__ import annotations

from .base import AtomicPolicy
from .. import skills


class NavigatePolicy(AtomicPolicy):
    """Move to a base pose, accounting for a currently held object."""

    def execute(self, pose, *, label="navigate", min_bottom_z=None):
        return skills.navigate(self.rig, pose, label=label, min_bottom_z=min_bottom_z)
