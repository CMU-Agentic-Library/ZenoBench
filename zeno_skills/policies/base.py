"""A policy instance binds one physical skill to one simulator rig."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AtomicPolicy(ABC):
    """Common interface for one target-parameterized, state-checked action."""

    def __init__(self, rig):
        self.rig = rig

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Run the action; raise SkillFailure if its outcome check fails."""
