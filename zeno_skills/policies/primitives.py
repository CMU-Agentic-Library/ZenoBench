"""Small measured actuator policies for the right hand and arm."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy, RetiredPolicy
from .. import skills
from ..kinematics import FINGER_OPEN
from ..rig import SkillFailure


def _width(width):
    value = float(width)
    if not np.isfinite(value) or not 0.0 <= value <= FINGER_OPEN:
        raise ValueError(f"finger position must be in [0, {FINGER_OPEN}] m per finger")
    return value


class RightGripperOpenPolicy(RetiredPolicy):
    """Retired (HAND_PLAN 9j): every skill opens its hand as a segment of its own plan (policy_040)."""

    REPLACED_BY = "every skill opens its hand as a segment of its own plan (policy_040)"


class RightGripperClosePolicy(RetiredPolicy):
    """Retired (HAND_PLAN 9j): a push closes its hand in its own plan (plan_slide's slide_close_hand; policy_041)."""

    REPLACED_BY = "a push closes its hand in its own plan (plan_slide's slide_close_hand; policy_041)"


class RightTcpMovePolicy(RetiredPolicy):
    """Retired (HAND_PLAN 9j): point is the point skill (policy_071; policy_038)."""

    REPLACED_BY = "point is the point skill (policy_071; policy_038)"


class RightJointMovePolicy(RetiredPolicy):
    """Retired (HAND_PLAN 9j): reset is the tuck, raise and straighten skills (policy_039)."""

    REPLACED_BY = "reset is the tuck, raise and straighten skills (policy_039)"


