"""Bound class API for Zeno House atomic GT policies.

Use ``policies = PolicySuite(rig)`` after runtime.make_rig. All policies
operate on the same live rig and preserve the legacy functions in skills.py.
"""

from __future__ import annotations

from .appliance import MicrowaveDoorCycle, MicrowaveStartPolicy
from .articulation import ClosePolicy, OpenPolicy
from .base import AtomicPolicy
from .manipulation import PickPolicy, PlacePolicy, PushPolicy
from .navigation import NavigatePolicy


class PolicySuite:
    """One bound instance of each reusable policy family for a simulator rig."""

    def __init__(self, rig):
        self.navigate = NavigatePolicy(rig)
        self.open = OpenPolicy(rig)
        self.close = ClosePolicy(rig)
        self.pick = PickPolicy(rig)
        self.place = PlacePolicy(rig)
        self.push = PushPolicy(rig)
        self.microwave_start = MicrowaveStartPolicy(rig)
        self.microwave_door_cycle = MicrowaveDoorCycle(rig)


__all__ = ["AtomicPolicy", "PolicySuite", "NavigatePolicy", "OpenPolicy", "ClosePolicy",
           "PickPolicy", "PlacePolicy", "PushPolicy", "MicrowaveStartPolicy", "MicrowaveDoorCycle"]
