"""The one tilt rule of a held object (kinematics.carry_tilt_allowed, docs/motion/MOTION_ARCHITECTURE.md 6):
CARRY_TILT beyond the goal's own tilt, for the straight joint move, the joint plan and the pose plan
alike; and cuRobo's pose planner's status said as it is (motion.plan_status)."""

import enum
from types import SimpleNamespace

import numpy as np

from zeno_skills.kinematics import CARRY_TILT, carry_tilt_allowed, holds_level, tilts_too_far, tips_over


def _rx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


class _Kin:
    """A TCP that tilts about x by angle(q)."""

    def __init__(self, angle):
        self.angle = angle

    def tcp(self, q):
        return np.zeros(3), _rx(self.angle(np.asarray(q, float)))


def test_a_held_object_may_tilt_carry_tilt_beyond_its_goals_own_tilt():
    kin = _Kin(lambda q: float(q[0]))
    R0, R1 = _rx(0.0), _rx(0.11)                                 # T23's place: the goal 0.11 off the start
    assert np.isclose(carry_tilt_allowed(R0, R1), CARRY_TILT + 0.11)
    assert not tilts_too_far(kin, R0, R1, [[0.05], [0.19], [0.11]])     # the tilt-held plan of 11-14: 0.19
    assert tilts_too_far(kin, R0, R1, [[0.27], [0.11]])
    assert holds_level(R0, R1) and not holds_level(R0, _rx(CARRY_TILT + 0.01))


def test_a_straight_move_tips_over_only_past_the_same_bound():
    # the tilt bulges on the way: q[1] swings out and back, q[0] goes to the goal's 0.11
    bulge = lambda c: _Kin(lambda q: float(q[0] + c * q[1] * (1.0 - q[1])))
    qa, qb = [0.0, 0.0], [0.11, 1.0]
    assert not tips_over(bulge(0.8), qa, qb)                    # peak ~0.257: past 0.15, inside 0.26
    assert tips_over(bulge(1.0), qa, qb)                        # peak ~0.31


def test_a_turn_of_the_load_is_bounded_too():
    # a goal 1 rad off (a box set down on its side): no tilt to hold, the path still bounded
    bulge = lambda c: _Kin(lambda q: float(q[0] + c * q[1] * (1.0 - q[1])))
    qa, qb = [0.0, 0.0], [1.0, 1.0]
    assert not holds_level(_rx(0.0), _rx(1.0))
    assert not tips_over(bulge(0.0), qa, qb)
    assert tips_over(bulge(3.0), qa, qb)                        # overshoots to ~1.33 > 1.15


def test_a_pose_plan_without_a_feasible_seed_is_said_so():
    from zeno_skills.motion import plan_status
    S = enum.Enum("MotionGenStatus", ["IK_FAIL", "TRAJOPT_FAIL", "FINETUNE_TRAJOPT_FAIL"])
    said = lambda status, t: plan_status(SimpleNamespace(status=status, finetune_time=t))
    assert said(S.FINETUNE_TRAJOPT_FAIL, 0.0) == "MotionGenStatus.TRAJOPT_FAIL (no feasible seed)"
    assert said(S.FINETUNE_TRAJOPT_FAIL, 0.4) == "MotionGenStatus.FINETUNE_TRAJOPT_FAIL"    # it ran and failed
    assert said(S.IK_FAIL, 0.0) == "MotionGenStatus.IK_FAIL"
