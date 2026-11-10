"""The motion primitives and the State they plan for (docs/MOTION_ARCHITECTURE.md sections 4, 5)."""

import numpy as np
import pytest

from zeno_skills import primitives as P
from zeno_skills.clearance import LEAVE_CONTACT
from zeno_skills.motion_state import (Failure, Hand, Held, Segment, Spec, State, at_base, holding, released,
                                      with_arm, with_width)


class FakeKin:
    """TCP = q[:3], orientation fixed.  ``wall(p)``: TCP positions in collision; ``reach_z``: no IK
    above it; ``near_z``: within LEAVE_GAP of the world below it.  plan / plan_to / ik_set answer
    what the test sets."""
    side = "right"
    motion = None

    def __init__(self, wall=lambda p: False, reach_z=10.0, near_z=-1.0, seg_free=True, plan=None,
                 plan_to=None, ik=None):
        self.scene = object()
        self.wall, self.reach_z, self.near_z, self.seg_free = wall, reach_z, near_z, seg_free
        self.plan_result, self.plan_to_result, self.ik = plan, plan_to, ik
        self.calls = []

    def tcp(self, q):
        return np.asarray(q, float)[:3].copy(), np.eye(3)

    def cart_path(self, q0, p, R, step=0.01):
        q0 = np.asarray(q0, float)
        self.calls.append(("cart_path", tuple(np.round(q0[:4], 3)), self.scene is not None))
        p0 = q0[:3]
        n = max(2, int(np.ceil(np.linalg.norm(np.asarray(p) - p0) / step)) + 1)
        out = []
        for u in np.linspace(0, 1, n)[1:]:
            q = q0.copy()
            q[:3] = p0 + (np.asarray(p) - p0) * u
            if q[2] > self.reach_z or (self.scene is not None and self.wall(q[:3])):
                return out, False
            out.append(q)
        return out, True

    def segment_free(self, qa, qb):
        return self.seg_free

    def plan(self, q0, q1, carry=False):
        self.calls.append(("plan", carry))
        return self.plan_result

    def plan_to(self, q0, p, R, carry=False, q_goal=None):
        self.calls.append(("plan_to", carry, None if q_goal is None else tuple(np.round(q_goal[:3], 3))))
        return self.plan_to_result

    def ik_set(self, goals, q0, weights=None):
        return self.ik

    def near(self, q, gap):
        return q[2] < self.near_z

    def free(self, q):
        return not self.wall(np.asarray(q)[:3])

    def path_free(self, qs):
        return all(self.free(q) for q in qs)

    def path_free_only(self, qs, names):
        return True


def _state(q=None):
    q = np.zeros(9) if q is None else np.asarray(q, float)
    return State(base=(0.0, 0.0, 0.0), q_right=q, q_left=np.zeros(7), hands={"right": Hand(width=0.04)})


def _q(x, y, z):
    q = np.zeros(9)
    q[:3] = (x, y, z)
    return q


FREE_SPEC = Spec()


# --------------------------------------------------------------------------- State
def test_a_state_is_never_changed_in_place():
    s = _state()
    s2 = released(holding(with_width(at_base(s, (1, 2, 90)), "right", 0.02), "right", Held("cup", np.eye(4))),
                  "right", "cup", np.eye(4))
    assert s.base == (0.0, 0.0, 0.0) and s.hands["right"].width == 0.04 and "cup" not in s.objects
    assert s2.base == (1.0, 2.0, 90.0) and s2.hands["right"].width == 0.02
    assert s2.held() is None and "cup" in s2.objects


def test_holding_is_what_the_hand_holds():
    s = holding(_state(), "right", Held("cup", np.eye(4), "pinch"))
    assert s.held("right").name == "cup" and s.held("left") is None


def test_the_left_arm_shares_the_torso_and_waist():
    s = with_arm(_state(np.arange(9.0)), np.r_[7.0, 8.0, np.full(7, 1.0)], side="left")
    assert np.allclose(s.q_right[:2], [7, 8]) and np.allclose(s.q_left, 1.0)
    assert np.allclose(s.q("left"), np.r_[7.0, 8.0, np.full(7, 1.0)])


# --------------------------------------------------------------------------- free_leg
def test_a_joint_goal_free_in_a_straight_move_needs_no_planner():
    kin = FakeKin(seg_free=True)
    seg = P.free_leg(kin, _state(), FREE_SPEC, P.Joint(np.full(9, 0.1)), "tuck")
    assert isinstance(seg, Segment) and seg.info["how"] == "joint" and np.allclose(seg.q_end, 0.1)
    assert not any(c[0] == "plan" for c in kin.calls)


def test_a_tilt_held_trajectory_must_end_at_the_joint_goal():
    # the planner held the tilt to the goal's pose and ended on another solution, unjoinable
    kin = FakeKin(seg_free=False, plan=([np.full(9, 0.5)], None))
    seg = P.free_leg(kin, _state(), Spec(hold_tilt=True), P.Joint(np.full(9, 0.1)), "carry")
    assert isinstance(seg, Failure) and "off the joint goal" in seg.why and ("plan", True) in kin.calls


def test_a_pose_goal_goes_straight_when_it_can_else_to_its_solution():
    seg = P.free_leg(FakeKin(), _state(), FREE_SPEC, P.Pose(np.array([0.1, 0, 0]), np.eye(3)), "to")
    assert seg.info["how"] == "straight"
    hint = _q(0.1, 0, 0)
    kin = FakeKin(wall=lambda p: 0.04 < p[0] < 0.06, seg_free=False, plan=([hint], None))
    seg = P.free_leg(kin, _state(), FREE_SPEC, P.Pose(np.array([0.1, 0, 0]), np.eye(3), hint), "to")
    assert seg.info["how"] == "joint" and ("plan", False) in kin.calls
    assert not any(c[0] == "plan_to" for c in kin.calls)
    # no solution: the planner to the pose
    kin = FakeKin(wall=lambda p: 0.04 < p[0] < 0.06, plan_to=([_q(0.1, 0, 0)], "pose"))
    seg = P.free_leg(kin, _state(), FREE_SPEC, P.Pose(np.array([0.1, 0, 0]), np.eye(3)), "to")
    assert seg.info["how"] == "pose" and kin.calls[-1] == ("plan_to", False, None)


def test_a_load_with_a_goal_solution_is_planned_to_it_with_the_tilt_held():
    hint = _q(0.1, 0, 0)
    kin = FakeKin(wall=lambda p: 0.04 < p[0] < 0.06, seg_free=False, plan=([hint], None))
    seg = P.free_leg(kin, _state(), Spec(hold_tilt=True), P.Pose(np.array([0.1, 0, 0]), np.eye(3), hint), "carry")
    assert seg.info["how"] == "planned (tilt held)" and ("plan", True) in kin.calls
    assert not any(c[0] == "plan_to" for c in kin.calls)


def test_a_goal_set_takes_the_cheapest_reachable_goal():
    goals = ((np.array([0.1, 0, 0]), np.eye(3)), (np.array([0.0, 0.1, 0]), np.eye(3)), (np.zeros(3), np.eye(3)))
    kin = FakeKin(ik=[_q(0.1, 0, 0), _q(0, 0.1, 0) * 0.5, None])
    seg = P.free_leg(kin, _state(), FREE_SPEC, P.PoseSet(goals), "carry_in")
    assert seg.info["chosen"] == 1 and seg.info["goals"] == 3
    assert isinstance(P.free_leg(FakeKin(ik=[None] * 3), _state(), FREE_SPEC, P.PoseSet(goals), "carry_in"),
                      Failure)


# --------------------------------------------------------------------------- straight
def test_the_straight_starts_from_the_given_solution_and_says_why_it_fails():
    q_from = _q(0, 0, 0.3)
    kin = FakeKin()
    seg = P.straight(kin, _state(), FREE_SPEC, np.array([0, 0, 0.25]), np.eye(3), "place_down", q_from=q_from)
    assert np.allclose(seg.q_from, q_from) and abs(seg.info["length"] - 0.05) < 1e-9
    hit = P.straight(FakeKin(wall=lambda p: p[2] < 0.27), _state(), FREE_SPEC, np.array([0, 0, 0.25]), np.eye(3),
                     "place_down", q_from=q_from)
    assert isinstance(hit, Failure) and "collides" in hit.why
    no_ik = P.straight(FakeKin(reach_z=0.2), _state(_q(0, 0, 0.1)), FREE_SPEC, np.array([0, 0, 0.3]), np.eye(3), "x")
    assert "no IK" in no_ik.why


# --------------------------------------------------------------------------- contact_extent / contact_segment
def test_a_contact_is_measured_to_the_margin_past_where_it_comes_clear():
    kin = FakeKin(near_z=0.02)                      # within LEAVE_GAP of the world below z = 2 cm
    ext = P.contact_extent(kin, _state(), FREE_SPEC, [0, 0, 1], P.near_world, "lift")
    step = 0.004                                    # contact_extent's waypoint spacing
    assert ext.clear and 0.02 + P.LEAVE_MARGIN - step <= ext.length <= 0.02 + P.LEAVE_MARGIN + 2 * step
    seg = P.contact_segment(Spec(allow=LEAVE_CONTACT), ext, "pick_lift")
    assert seg.spec.allow is LEAVE_CONTACT and seg.qs == ext.qs and seg.target is None


def test_a_start_out_of_contact_has_no_contact():
    ext = P.contact_extent(FakeKin(near_z=-1.0), _state(), FREE_SPEC, [0, 0, 1], P.near_world, "lift")
    assert ext.length == 0.0 and ext.qs == ()


def test_still_touching_at_the_end_of_the_exit_is_a_failure_not_a_shorter_lift():
    assert isinstance(P.contact_extent(FakeKin(near_z=1.0), _state(), FREE_SPEC, [0, 0, 1], P.near_world, "lift"),
                      Failure)
    # the arm runs out of IK 1 cm up while still touching: no halving, no lift without its exit
    out = P.contact_extent(FakeKin(near_z=0.03, reach_z=0.01), _state(), FREE_SPEC, [0, 0, 1], P.near_world, "lift")
    assert isinstance(out, Failure) and "IK only 0.008" in out.why


def test_a_load_lifted_off_its_support_rises_the_gap_whatever_the_model_says():
    kin = FakeKin(near_z=-1.0)                      # the model reads it clear at once
    ext = P.contact_extent(kin, _state(), FREE_SPEC, [0, 0, 1], P.off_support, "pick_lift")
    assert ext.length >= P.LEAVE_GAP + P.LEAVE_MARGIN - 0.005


def test_exit_length_is_the_one_measure_rig_uses():
    from zeno_skills.rig import Rig
    kin = FakeKin(near_z=0.02)
    line, _ = kin.cart_path(np.zeros(9), np.array([0, 0, 0.06]), np.eye(3), step=0.004)
    assert Rig._exit_length(kin, np.zeros(9), line) == P.exit_length(kin, np.zeros(9), line)


@pytest.mark.parametrize("touching", [P.near_world, P.in_world, P.off_support])
def test_touching_predicates_take_kin_and_the_start(touching):
    assert callable(touching(FakeKin(), np.zeros(9)))


# ------------------------------------------------------------------- decisions (docs 5.7, 8.1)
class IKKin(FakeKin):
    """FakeKin with a collision-aware IK (kinematic with no scene): its first seed with the TCP moved
    to p; none into the wall.  (test_skill_plans' FakeKin.)"""

    def ik_global(self, p, R, seeds=None):
        self.calls.append(("ik_global", len(seeds or [])))
        q = np.asarray((seeds or [np.zeros(9)])[0], float).copy()
        q[:3] = p
        return q, not (self.scene is not None and self.wall(np.asarray(p, float)))


class TurnKin(IKKin):
    """IKKin with the TCP turned about z by q[3]."""

    def tcp(self, q):
        q = np.asarray(q, float)
        c, s = np.cos(q[3]), np.sin(q[3])
        return q[:3].copy(), np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def test_a_decided_solution_still_reaching_its_pose_free_is_kept_as_it_is():
    kin = IKKin()
    prior = np.r_[0.5, 0.0, 0.2, np.full(6, 0.3)]
    q, how = P.decide_ik(kin, _state(), Spec(), prior[:3], np.eye(3), prior)
    assert how == "prior" and np.array_equal(q, prior) and not kin.calls


def test_a_decided_solution_off_its_pose_seeds_the_solve_and_none_free_fails():
    kin = IKKin()
    prior = np.r_[0.5, 0.0, 0.2, np.full(6, 0.3)]
    off = prior[:3] + [0.0, 0.0, 2 * P.HINT_REACH]               # the base stopped off its park
    q, how = P.decide_ik(kin, _state(), Spec(), off, np.eye(3), prior, seeds=(np.zeros(9),))
    assert how == "solved" and kin.calls == [("ik_global", 2)]   # the prior first, then the given seeds
    assert np.allclose(q[:3], off) and np.allclose(q[3:], 0.3)   # solved from the prior (the fake's IK keeps its seed)
    kin = IKKin(wall=lambda p: p[2] < 0.25)                       # the pose itself in the world now
    assert P.decide_ik(kin, _state(), Spec(), prior[:3], np.eye(3), prior) is None


def test_a_decided_solution_turned_off_its_pose_is_solved_again():
    prior = np.r_[0.5, 0.0, 0.2, 0.5 * P.HINT_TURN, np.zeros(5)]
    assert P.decide_ik(TurnKin(), _state(), Spec(), prior[:3], np.eye(3), prior)[1] == "prior"
    prior[3] = 2 * P.HINT_TURN                                    # at its point, turned 0.02 rad off
    assert P.decide_ik(TurnKin(), _state(), Spec(), prior[:3], np.eye(3), prior)[1] == "solved"
    assert not P.near_pose(prior[:3], np.eye(3), prior[:3] + [0.0, 0.0, 2 * P.HINT_REACH], np.eye(3))


def test_a_goal_set_keeps_the_goal_decided_before_while_it_can():
    a, b = np.r_[0.3, 0.0, 0.4, np.zeros(6)], np.r_[0.6, 0.0, 0.4, np.zeros(6)]
    kin = FakeKin(ik=[a, b])
    st = _state(np.r_[0.3, 0.0, 0.39, np.zeros(6)])
    goals = P.PoseSet(((a[:3], np.eye(3)), (b[:3], np.eye(3))))
    assert P.free_leg(kin, st, Spec(), goals, "carry_in").info["chosen"] == 0           # the cheaper one
    assert P.free_leg(kin, st, Spec(), goals, "carry_in", first=(1, 2)).info["chosen"] == 1  # the one decided
    # decided in a set of another size (a set made from the state laid out otherwise): chosen again
    assert P.free_leg(kin, st, Spec(), goals, "carry_in", first=(1, 3)).info["chosen"] == 0
    kin = FakeKin(ik=[a, None])                                   # the decided one has no IK now: chosen again
    assert P.free_leg(kin, st, Spec(), goals, "carry_in", first=(1, 2)).info["chosen"] == 0
    kin = FakeKin()
    rest = P.JointSet((np.zeros(9), np.full(9, 0.1)))
    assert P.free_leg(kin, st, Spec(), rest, "tuck", first=(1, 2)).info["chosen"] == 1
    kin = FakeKin(wall=lambda p: p[0] > 0.05)                    # the decided one collides now: chosen again
    assert P.free_leg(kin, st, Spec(), rest, "tuck", first=(1, 2)).info["chosen"] == 0
