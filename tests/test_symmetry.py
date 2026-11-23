"""Left and right arm alike (docs/motion/MOTION_ARCHITECTURE.md 4.1, 4.2, 7, 9.3 step 6a): the State's
body and arms, the body kept while the other hand holds something, segments that name their arm,
the park search's goals of either hand."""

from types import SimpleNamespace

import numpy as np

from tests.test_park_search import Base, Kin as ParkKin
from tests.test_primitives import FakeKin
from zeno_skills import park_search as PS
from zeno_skills import primitives as P
from zeno_skills.motion_state import (ARM, Hand, Held, Plan, Posture, Spec, State, body_locked, chains, kept,
                                     with_arm, with_posture)
from zeno_skills.primitives import Joint, JointSet


class LeftKin(FakeKin):
    side = "left"


def _state(qr=None, ql=None, right=None, left=None):
    qr = np.r_[0.1, 0.2, np.full(7, 0.3)] if qr is None else np.asarray(qr, float)
    return State(base=(0.0, 0.0, 0.0), **chains(qr, np.full(7, 0.6) if ql is None else ql),
                 hands={"right": Hand(0.0, right), "left": Hand(0.0, left)})


def test_the_state_has_one_body_both_chains_ride_on():
    s = _state()
    assert np.allclose(s.q("right")[:2], s.q("left")[:2]) and np.allclose(s.q("left")[2:], 0.6)
    t = with_arm(s, np.r_[0.5, 0.4, np.full(7, 0.9)], "left")          # a left solution moves the body
    assert np.allclose(t.body, [0.5, 0.4]) and np.allclose(t.q("right")[2:], 0.3) and np.allclose(t.arms["left"], 0.9)
    p = t.posture()
    assert np.allclose(Posture.from_vec(p.vec()).vec(), p.vec()) and np.allclose(p.q("left"), t.q("left"))


def test_a_posture_goal_moves_the_body_only_where_no_other_hand_holds_something():
    fold = Posture(np.array([0.0, 0.0]), {"left": np.full(7, -0.5)})
    assert np.allclose(with_posture(_state(), fold).body, 0.0)
    held = _state(right=Held("can", np.eye(4)))
    out = with_posture(held, fold)
    assert np.allclose(out.body, [0.1, 0.2]) and np.allclose(out.arms["left"], -0.5)   # the can's body stays


def test_the_body_is_locked_while_the_other_hand_holds_something_unless_the_spec_says():
    s = _state(right=Held("can", np.eye(4)))
    assert body_locked(s, Spec(), "left") and not body_locked(s, Spec(), "right")
    assert not body_locked(_state(), Spec(), "left")
    assert not body_locked(s, Spec(joints=("torso_lift_joint", "waist_pitch_joint")), "left")
    assert body_locked(_state(), Spec(joints=()), "right")


NAMES = ("torso_lift_joint", "waist_pitch_joint") + tuple(f"right_arm_joint{i}" for i in range(1, 8))


class NamedKin(FakeKin):
    names = list(NAMES)


def test_spec_joints_names_what_moves_every_other_joint_of_the_chain_kept():
    s = _state(right=Held("can", np.eye(4)))
    assert list(kept(s, Spec(), "left", NAMES)) == [True, True] + [False] * 7          # the rule: the body
    assert not kept(_state(), Spec(), "right", NAMES).any()
    torso = kept(_state(), Spec(joints=("torso_lift_joint",)), "right", NAMES)
    assert list(torso) == [False] + [True] * 8                                         # a posture segment
    assert list(kept(_state(), Spec(joints=("torso_lift_joint", ARM)), "right", NAMES)) == [False, True] + [False] * 7
    assert kept(_state(), Spec(joints=()), "right", NAMES).all()
    assert list(kept(_state(), Spec(joints=("torso_lift_joint",)), "right")) == [False, True]   # locked_body's


def test_a_joint_goal_keeps_the_joints_the_spec_leaves_out_and_so_does_decide_ik():
    s = _state()
    goal = np.r_[-0.5, 0.6, np.full(7, 0.9)]
    seg = P.free_leg(NamedKin(), s, Spec(joints=("torso_lift_joint",)), Joint(goal), "crouch")
    assert np.allclose(seg.q_end, np.r_[-0.5, 0.2, np.full(7, 0.3)])                  # only the torso went
    assert all(np.allclose(q[1:], np.r_[0.2, np.full(7, 0.3)]) for q in seg.qs)
    both = P.free_leg(NamedKin(), s, Spec(joints=("torso_lift_joint", ARM)), Joint(goal), "reach")
    assert np.allclose(both.q_end, np.r_[-0.5, 0.2, np.full(7, 0.9)])                 # the waist kept
    q, how = P.decide_ik(NamedKin(), s, Spec(joints=("torso_lift_joint", ARM)), np.r_[0.4, 0.2, 0.3], np.eye(3),
                         prior=np.r_[0.4, 0.9, 0.3, np.full(6, 0.7)])
    assert how == "prior" and np.isclose(q[1], 0.2) and np.allclose(q[3:], 0.7)        # its waist the state's


def test_a_fold_of_one_arm_keeps_the_body_where_the_other_holds_something():
    s = _state(right=Held("can", np.eye(4)))
    rest, hang = np.r_[0.0, 0.0, np.full(7, 0.5)], np.r_[0.0, 0.0, np.full(7, -0.5)]
    seg = P.free_leg(LeftKin(), s, Spec(), JointSet((rest, hang)), "tuck")
    assert seg.info["side"] == "left" and seg.info["chosen"] == 0
    assert np.allclose(seg.q_end[:2], [0.1, 0.2]) and np.allclose(seg.q_end[2:], 0.5)
    assert all(np.allclose(q[:2], [0.1, 0.2]) for q in seg.qs)
    free = P.free_leg(LeftKin(), _state(), Spec(), Joint(rest), "tuck")     # nothing held: the fold's body
    assert np.allclose(free.q_end, rest)


def test_every_segment_of_a_primitive_names_its_arm():
    s = _state()
    seg = P.straight(LeftKin(), s, Spec(), np.array([0.1, 0.2, 0.5]), np.eye(3), "in")
    assert seg.info["side"] == "left"
    ext = P.contact_extent(LeftKin(near_z=0.32), s, Spec(), [0.0, 0.0, 1.0], P.near_world, "out")
    assert P.contact_segment(Spec(), ext, "out").info["side"] == "left"


class LeftParkKin(ParkKin):
    side = "left"


def _problem(build, hand="right", goal=(1.0, 0.0, 0.8)):
    g = np.asarray(goal, float)
    return PS.Problem(goals=(((g,), (g, np.eye(3)), 0.0),), build=build, relay="door_reach",
                      arrive=lambda x, y, yaw: np.zeros(9), travel=np.zeros(9), hand=hand)


def test_the_park_search_mirrors_the_shoulder_and_the_facing_for_a_left_goal():
    assert PS.shoulder("left") == (PS.SHOULDER[0], -PS.SHOULDER[1]) and PS.face_off("left") == -PS.FACE_LEFT
    goal = np.array([0.0, 0.0, 0.8])
    # base at the origin facing +x: the goal 0.85 m to the left is in the left arm's reach, not the right's
    cand = [(0.0, 0.0, -0.85, 0.0, 0)]
    right = _problem(None, "right", goal)
    left = _problem(None, "left", goal)
    assert PS.reachable(cand, left) == [True] and PS.reachable(cand, right) == [False]
    best = lambda pr: min((c for c in PS.candidates(pr) if abs(c[1] - 0.6) < 1e-9 and abs(c[2]) < 1e-9), key=lambda c: c[0])
    # from the same spot (facing the goal: 180 deg) the right arm turns the goal to its right, the left to its left
    assert np.isclose(best(right)[3], 180.0 + PS.FACE_LEFT) and np.isclose(best(left)[3], 180.0 - PS.FACE_LEFT)


def test_each_goal_is_ranked_and_built_with_its_hands_kinematics():
    right, left = ParkKin(), LeftParkKin()
    built = []
    goal = np.array([1.0, 0.0, 0.8])

    def build(s, k, prior):
        built.append((k, s.q("left").copy()))
        return Plan(())
    problem = PS.Problem(goals=(((goal,), (goal, np.eye(3)), 0.0, "right"), ((goal,), (goal, np.eye(3)), 0.0, "left")),
                         build=build, relay="door_reach",
                         arrive=lambda x, y, yaw: Posture(np.zeros(2), {"left": np.full(7, 0.25)}),
                         travel=Posture(np.zeros(2), {"right": np.zeros(7), "left": np.zeros(7)}))
    log = []
    found, diag = PS.find_park({"right": right, "left": left}, SimpleNamespace(footprint_clear=lambda *a: True),
                               problem, _state(), lambda ev, **kw: log.append(ev), base=Base())
    assert right.asked and left.asked                              # one batched ranking IK per hand
    assert len(right.asked[0][2]) + len(left.asked[0][2]) == diag["pool"]
    assert found is not None and problem.side(found.k) in ("right", "left")
    assert built and all(np.allclose(q[2:], 0.25) for _, q in built)   # built at the park in the arrive posture


def test_the_ranking_ik_keeps_the_body_joints_the_build_keeps():
    seen = []

    class Rank(LeftParkKin):
        def ik_set(self, goals, q0, weights=None):
            seen.append((self.lo[:2].copy(), self.hi[:2].copy(), np.asarray(q0, float)[:2].copy()))
            return super().ik_set(goals, q0, weights)
    goal = np.array([1.0, 0.0, 0.8])
    st = _state(right=Held("can", np.eye(4)))                         # the right hand holds: the body is kept
    problem = PS.Problem(goals=(((goal,), (goal, np.eye(3)), 0.0, "left"),), build=lambda s, k, p: Plan(()),
                         relay="door_reach", arrive=lambda x, y, yaw: np.zeros(9), travel=np.zeros(9), hand="left",
                         body_free=("torso_lift_joint",))
    kin = Rank()
    PS.find_park({"left": kin}, SimpleNamespace(footprint_clear=lambda *a: True), problem, st, lambda *a, **k: None,
                 base=Base())
    lo, hi, seed = seen[0]
    assert lo[1] == hi[1] == st.body[1] and seed[1] == st.body[1]     # the waist pinned where the state has it
    assert lo[0] < hi[0]                                              # the torso free (body_free)
    assert np.allclose(kin.lo, -3.0) and np.allclose(kin.hi, 3.0)     # put back
