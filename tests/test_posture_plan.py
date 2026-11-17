"""plan_posture (docs/MOTION_ARCHITECTURE.md 6, 9.3 step 5): one free leg to a joint goal where the robot
stands -- a body posture moves one body joint, the arms riding it as they are and checked with both arms'
chains; nothing else is tried when the leg cannot be made."""

import numpy as np

from tests.test_primitives import FakeKin
from zeno_skills.motion_state import ARM, Failure, Hand, Held, State, chains
from zeno_skills.primitives import Joint, JointSet
from zeno_skills.skill_plans import plan_posture

RIGHT = ("torso_lift_joint", "waist_pitch_joint") + tuple(f"right_arm_joint{i}" for i in range(1, 8))
LEFT = ("torso_lift_joint", "waist_pitch_joint") + tuple(f"left_arm_joint{i}" for i in range(1, 8))


class Right(FakeKin):
    names = list(RIGHT)


class Left(FakeKin):
    side = "left"
    names = list(LEFT)


def _state(right=None, left=None, width=0.0):
    return State(base=(0.0, 0.0, 0.0), **chains(np.r_[0.0, 0.0, np.full(7, 0.3)], np.full(7, 0.6)),
                 hands={"right": Hand(width, right), "left": Hand(width, left)})


def _crouch(s, torso=-0.5):
    return Joint(np.r_[torso, np.asarray(s.q("right"))[1:]])


def test_a_crouch_moves_the_torso_alone_and_both_arms_ride_it():
    s = _state()
    plan = plan_posture(Right(), s, _crouch(s), joints=("torso_lift_joint",), other=Left(), name="crouch")
    (leg,) = plan.segments
    assert leg.name == "crouch" and leg.spec.joints == ("torso_lift_joint",) and leg.spec.arms_still
    assert np.allclose(leg.q_end, np.r_[-0.5, 0.0, np.full(7, 0.3)])
    assert all(np.allclose(q[1:], np.r_[0.0, np.full(7, 0.3)]) for q in leg.qs)
    assert not leg.spec.hold_tilt and "smooth" not in leg.info


def test_a_goal_off_the_named_joint_still_moves_that_joint_only():
    s = _state()
    goal = Joint(np.r_[-0.5, 0.4, np.full(7, 0.9)])                 # a waist and an arm the spec leaves out
    leg = plan_posture(Right(), s, goal, joints=("torso_lift_joint",), name="crouch").segments[0]
    assert np.allclose(leg.q_end, np.r_[-0.5, 0.0, np.full(7, 0.3)])


def test_the_other_arm_that_cannot_ride_the_body_fails_the_posture():
    s = _state()
    stuck = Left(wall=lambda p: p[0] < -0.2)                          # its chain's TCP (FakeKin: q[:3]) low
    out = plan_posture(Right(), s, _crouch(s), joints=("torso_lift_joint",), other=stuck, name="crouch")
    assert isinstance(out, Failure) and "left arm" in out.why


def test_no_tuck_and_no_base_move_when_the_leg_cannot_be_made():
    s = _state()
    kin = Right(seg_free=False, plan=(None, "GRAPH_FAIL"))
    out = plan_posture(kin, s, _crouch(s), joints=("torso_lift_joint",), name="crouch")
    assert isinstance(out, Failure) and "GRAPH_FAIL" in out.why
    assert [c for c in kin.calls if c[0] not in ("plan",)] == []        # one plan asked, nothing else


def test_at_the_goal_already_the_plan_is_empty():
    s = _state()
    assert plan_posture(Right(), s, _crouch(s, 0.0), joints=("torso_lift_joint",), name="stand").segments == ()


def test_a_load_rides_gently_and_keeps_its_tilt_checked():
    s = _state(right=Held("cup", np.eye(4)))
    leg = plan_posture(Right(), s, _crouch(s), joints=("torso_lift_joint",), other=Left(), name="crouch").segments[0]
    assert leg.spec.hold_tilt and leg.info["smooth"] and leg.info["steps_per_wp"] == 4
    other = _state(left=Held("plate", np.eye(4)))                      # the other hand's load rides it too
    leg = plan_posture(Right(), other, _crouch(other), joints=("torso_lift_joint",), name="crouch").segments[0]
    assert leg.spec.arms_still and leg.info["smooth"]


def test_a_right_tuck_folds_the_body_too_a_left_one_the_arm_alone():
    s = _state()
    rest = np.r_[0.0, 0.0, np.full(7, -0.4)]
    leg = plan_posture(Right(), _state(), JointSet((rest,)), name="tuck").segments[0]
    assert np.allclose(leg.q_end, rest)
    low = State(base=s.base, **chains(np.r_[-0.3, 0.2, np.full(7, 0.3)], np.full(7, 0.6)), hands=s.hands)
    left_rest = np.r_[0.0, 0.0, np.full(7, -0.7)]
    plan = plan_posture(Left(), low, JointSet((left_rest,)), joints=(ARM,), open_hand=0.04, name="tuck")
    grip, leg = plan.segments
    assert grip.kind == "action" and grip.action[:2] == ("grip", 0.04) and grip.info["side"] == "left"
    assert np.allclose(leg.q_end, np.r_[-0.3, 0.2, np.full(7, -0.7)])  # the body where it is
