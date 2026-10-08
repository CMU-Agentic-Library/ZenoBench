"""Base-motion policies for empty-handed and object-carrying travel."""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..rig import SkillFailure


class NavigatePolicy(AtomicPolicy):
    """Move to a base pose; select empty-hand or carry behavior from rig state."""

    def execute(self, pose, *, label="navigate", min_bottom_z=None):
        return skills.navigate(self.rig, pose, label=label, min_bottom_z=min_bottom_z)


class EmptyHandNavigatePolicy(AtomicPolicy):
    """Navigate after collision-checked arm tucking."""

    def execute(self, pose):
        if self.rig.held is not None:
            raise SkillFailure("empty-hand navigate: release the held object first")
        return skills.navigate(self.rig, pose, label="empty_hand_navigate")


class CarryNavigatePolicy(AtomicPolicy):
    """Carry a grasped object while the base moves; detect any slip."""

    def execute(self, pose, *, name=None, min_bottom_z=None):
        held = self.rig.held
        if held is None or (name is not None and held["name"] != name):
            raise SkillFailure(f"carry navigate: not holding {name or 'an object'}")
        result = skills.navigate(self.rig, pose, label="carry_navigate", min_bottom_z=min_bottom_z)
        skills.check_held(self.rig, "carry_navigate_result")
        return result


class CarryHeightAdjustPolicy(AtomicPolicy):
    """Lift a held object vertically to a measured minimum bottom height."""

    def execute(self, min_bottom_z=skills.CARRY_Z, *, tolerance=0.02):
        held = self.rig.held
        if held is None:
            raise SkillFailure("carry height adjust: no held object")
        target = float(min_bottom_z)
        if not np.isfinite(target) or target < 0 or tolerance <= 0:
            raise ValueError("carry height target must be finite and nonnegative")
        name = held["name"]
        bottom = float(self.rig.geo.bottom(name, self.rig.state())[2])
        if bottom < target - tolerance:
            skills.held_vertical_move(self.rig, target - bottom, "carry_height_adjust")
        skills.check_held(self.rig, "carry_height_adjust")
        actual = float(self.rig.geo.bottom(name, self.rig.state())[2])
        if actual < target - tolerance:
            raise SkillFailure(f"carry height adjust: object bottom {actual:.3f} m below {target:.3f} m")
        return actual


class BackOffWithLoadPolicy(AtomicPolicy):
    """Reverse the base while holding an object, then check travel and grasp."""

    def execute(self, distance=0.35, *, min_distance=0.1):
        if self.rig.held is None:
            raise SkillFailure("back off with load: no held object")
        distance, min_distance = float(distance), float(min_distance)
        if not np.isfinite(distance) or not np.isfinite(min_distance) or distance <= 0 or not 0 < min_distance <= distance:
            raise ValueError("backoff distance must be positive and at least min_distance")
        moved = skills._back_off(self.rig, distance)
        skills.check_held(self.rig, "back_off_with_load")
        if moved < min_distance - 0.01:
            raise SkillFailure(f"back off with load: reversed only {moved:.3f} m")
        return moved


def _require_tucked_empty_base(rig, action):
    if rig.held is not None:
        raise SkillFailure(f"{action}: release the held object first")
    if np.max(np.abs(rig.q() - rig.kin.rest)) > 0.05:
        raise SkillFailure(f"{action}: tuck the arm before direct base motion")


class BaseRotateInPlacePolicy(AtomicPolicy):
    """Turn the tucked, empty robot in place after checking its footprint arc."""

    def execute(self, delta_yaw_deg, *, tolerance_deg=2.0):
        delta = float(delta_yaw_deg)
        if not np.isfinite(delta) or not 0 < abs(delta) <= 90:
            raise ValueError("in-place rotation must be nonzero and within 90 degrees")
        _require_tucked_empty_base(self.rig, "base rotate")
        x, y, yaw = self.rig.base_pose()
        for offset in np.linspace(0, delta, max(3, math.ceil(abs(delta) / 5) + 1)):
            if not self.rig.world.footprint_clear(x, y, math.radians(yaw + offset)):
                raise SkillFailure("base rotate: occupied footprint on turn arc")
        target = yaw + delta
        self.rig.drive_base([(x, y, target)])
        bx, by, actual = self.rig.base_pose()
        angle_error = abs((actual - target + 180) % 360 - 180)
        if math.hypot(bx - x, by - y) > 0.02 or angle_error > tolerance_deg:
            raise SkillFailure("base rotate: measured base pose missed target")
        return actual


class BaseTranslateLocalPolicy(AtomicPolicy):
    """Move a short straight local xy vector with a tucked, empty arm."""

    def execute(self, forward_m, left_m=0.0, *, tolerance_m=0.03):
        forward, left = float(forward_m), float(left_m)
        distance = math.hypot(forward, left)
        if not np.isfinite(distance) or not 0 < distance <= 0.5:
            raise ValueError("local translation must be nonzero and within 0.5 m")
        _require_tucked_empty_base(self.rig, "base translate")
        x, y, yaw = self.rig.base_pose()
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        dx, dy = c * forward - s * left, s * forward + c * left
        for u in np.linspace(0, 1, max(3, math.ceil(distance / 0.05) + 1)):
            if not self.rig.world.footprint_clear(x + u * dx, y + u * dy, math.radians(yaw)):
                raise SkillFailure("base translate: occupied footprint on straight path")
        self.rig.drive_base([(x + dx, y + dy, yaw)])
        bx, by, actual_yaw = self.rig.base_pose()
        error = math.hypot(bx - x - dx, by - y - dy)
        if error > tolerance_m or abs((actual_yaw - yaw + 180) % 360 - 180) > 2:
            raise SkillFailure("base translate: measured base pose missed target")
        return (bx, by, actual_yaw)


class PickAndCarryPolicy:
    """Composite: finish a pick, then navigate while holding the object."""

    def __init__(self, rig):
        from .manipulation import PickPolicy
        self.pick = PickPolicy(rig)
        self.carry = CarryNavigatePolicy(rig)

    def execute(self, name, pose, *, min_bottom_z=None):
        self.pick.execute(name)
        return self.carry.execute(pose, name=name, min_bottom_z=min_bottom_z)
