"""Bounded task-level thermal wait after physical appliance activation."""

from __future__ import annotations

import math

from .base import AtomicPolicy
from ..rig import SkillFailure


class WaitForTemperaturePolicy(AtomicPolicy):
    """Advance the live simulator until a configured food reaches a target."""

    def execute(self, name, min_temp_c, *, max_wait_s=60.0):
        rig = self.rig
        target = float(min_temp_c)
        timeout = float(max_wait_s)
        if not math.isfinite(target) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("thermal target and timeout must be finite")
        thermal = getattr(rig, "thermal", None)
        if thermal is None or name not in thermal.temperatures_c:
            raise SkillFailure(f"wait for temperature: {name} has no configured thermal state")
        # 120 simulation steps correspond to one simulated second in this rig.
        for _ in range(math.ceil(timeout)):
            actual = float(thermal.temperatures_c[name])
            if actual >= target:
                thermal.active = False
                rig.log("microwave_stop", food=name, temp_c=round(actual, 1))
                return actual
            if not thermal.active:
                raise SkillFailure("wait for temperature: heating stopped before target")
            rig.step(120)
        actual = float(thermal.temperatures_c[name])
        if actual < target:
            raise SkillFailure(f"wait for temperature: {actual:.1f} C below {target:.1f} C")
        thermal.active = False
        rig.log("microwave_stop", food=name, temp_c=round(actual, 1))
        return actual
