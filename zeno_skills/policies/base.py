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


class RetiredPolicy(AtomicPolicy):
    """A policy whose id is retired (skill_library/check.py RETIRED_POLICIES): its class kept so the id, the catalog
    and the contract diagrams still name it, its body gone -- calling it says what replaced it (HAND_PLAN 9j)."""

    REPLACED_BY = "a skill on the motion layers"

    def execute(self, *args, **kwargs):
        from ..rig import SkillFailure
        raise SkillFailure(f"{type(self).__name__} is retired: {self.REPLACED_BY}")

