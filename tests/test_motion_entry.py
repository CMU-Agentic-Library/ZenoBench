"""Rig's arm motion entry (docs/COLLISION_PLAN.md step 1): straight line, else one planner; the
unchecked move is the straight one; a load in the hand is moved slowly and smoothly."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills.clearance import LEAVE_CONTACT
from zeno_skills.rig import BIG_SWING, CARRY_VEL, LEAVE_MARGIN, LEAVE_MAX, RIM_VEL, Rig, SkillFailure


class FakeKin:
    names = ["torso_lift_joint", "waist_pitch_joint"] + [f"right_arm_joint_{i}" for i in range(1, 8)]

    def __init__(self, line=True, ik_local=True, goal=None, plan=None):
        self.scene, self.side, self.motion = object(), "right", None
        self.line, self.ik_local, self.goal, self.plan_result = line, ik_local, goal, plan
        self.calls = []

    def cart_path(self, q0, p, R, step=0.01):
        self.calls.append(("cart_path", self.scene is not None))
        return ([np.asarray(q0) + 0.01], True) if self.line else ([], False)

    def ik(self, p, R, q0):
        self.calls.append(("ik", tuple(np.round(q0, 3))))
        return np.asarray(q0) + 0.002, self.ik_local

    def ik_global(self, p, R, seeds=None):
        self.calls.append(("ik_global", len(seeds or []), self.scene is not None))
        return (self.goal, True) if self.goal is not None else (np.zeros(9), False)

    def free(self, q):
        return True

    def plan_to(self, q0, p, R, carry=False, q_goal=None):
        self.calls.append(("plan_to", None if q_goal is None else tuple(np.round(q_goal, 3))))
        return self.plan_result


def _rig(kin, held=None):
    rig = SimpleNamespace(kin=kin, q_cmd=np.zeros(9), held=held, logged=[])
    rig.log = lambda ev, **kw: rig.logged.append(ev)
    for name in ("_goal", "_carrying", "joint_path_via", "_joint_path", "_motion_path", "_start"):
        setattr(rig, name, getattr(Rig, name).__get__(rig))
    rig._dense = Rig._dense
    return rig


def test_the_straight_line_needs_no_planner():
    kin = FakeKin(line=True)
    qs = Rig._move_path(_rig(kin), np.ones(3), np.eye(3), 0.01, "pick_pre", None)
    assert len(qs) == 1 and [c[0] for c in kin.calls] == ["cart_path"]


def test_a_blocked_line_is_planned_to_the_hint_re_solved_at_the_actual_base():
    hint = np.full(9, 0.3)
    kin = FakeKin(line=False, plan=([np.full(9, 0.302)], "joint"))
    rig = _rig(kin)
    qs = Rig._move_path(rig, np.ones(3), np.eye(3), 0.01, "pick_pre_far", hint)
    assert ("ik", tuple(np.round(hint, 3))) in kin.calls            # seeded on the hint's branch
    assert kin.calls[-1] == ("plan_to", tuple(np.round(hint + 0.002, 3)))
    assert np.allclose(qs[-1], 0.302) and "planned_leg" in rig.logged


def test_no_path_fails_the_checked_leg():
    kin = FakeKin(line=False, ik_local=False, goal=None, plan=(None, "IK_FAIL"))
    with pytest.raises(SkillFailure, match="no collision-free path"):
        Rig._move_path(_rig(kin), np.ones(3), np.eye(3), 0.01, "carry_in", None)
    assert kin.calls[-1] == ("plan_to", None)


def test_without_a_hint_the_goal_is_an_ik_solution_near_the_current_posture():
    kin = FakeKin(goal=np.full(9, 0.1))
    assert np.allclose(Rig._goal(_rig(kin), np.ones(3), np.eye(3), None), 0.1)
    assert kin.calls == [("ik_global", 1, True)]


def test_the_unchecked_move_is_the_kinematic_straight_line():
    kin = FakeKin(line=True)
    qs = Rig._straight_move(_rig(kin), np.ones(3), np.eye(3), 0.01, "place_lower", None)
    assert len(qs) == 1 and kin.calls == [("cart_path", False)] and kin.scene is not None


def test_no_ik_along_the_line_takes_the_straight_joint_move_unless_it_swings_far():
    kin = FakeKin(line=False, goal=np.full(9, 0.5))
    qs = Rig._straight_move(_rig(kin), np.ones(3), np.eye(3), 0.01, "knock_tap", None)
    assert np.allclose(qs[-1], 0.5) and ("ik_global", 1, False) in kin.calls
    far = FakeKin(line=False, goal=np.full(9, BIG_SWING + 0.2))
    rig = _rig(far)
    planned = []
    rig._joint_path = lambda q, label, allow: (planned.append(allow) or [q], allow)
    Rig._straight_move(rig, np.ones(3), np.eye(3), 0.01, "knock_tap", None)
    assert planned == []                                            # no hint: the straight joint move
    Rig._straight_move(rig, np.ones(3), np.eye(3), 0.01, "knock_tap", np.zeros(9))
    assert planned and planned[0].checked                           # towards a hint a big swing is planned


def test_a_load_in_the_hand_caps_the_arm_speed_and_smooths_the_path():
    ann = SimpleNamespace(objects={"mug": {}, "bowl": {}},
                          asset_of=lambda o: {"container": o is ann.objects["bowl"]})
    rig = SimpleNamespace(kin=FakeKin(), ann=ann, held=None)
    for name in ("_carrying", "_held_container"):
        setattr(rig, name, getattr(Rig, name).__get__(rig))
    free = Rig._vmax(rig)
    rig.held = {"name": "mug", "kind": "pinch"}
    mug = Rig._vmax(rig)
    rig.held = {"name": "bowl", "kind": "pinch"}
    bowl = Rig._vmax(rig)
    assert np.all(mug[2:] <= CARRY_VEL) and np.all(bowl[2:] <= RIM_VEL) and np.all(free[2:] > CARRY_VEL)
    assert np.allclose(mug[:2], free[:2])                            # torso and waist unchanged
    smooth = []
    rig.follow_smooth = lambda qs, *a: smooth.append(len(qs))
    Rig.follow(rig, [np.zeros(9)])
    assert smooth == [1]


class LiftKin:
    """A TCP that rises with q[0]; ``touching(z)``: still in contact at that height."""

    def __init__(self, touching):
        self.scene, self.motion, self.side, self.touching = object(), None, "right", touching

    def tcp(self, q):
        return np.array([0.0, 0.0, float(q[0])]), np.eye(3)

    def near(self, q, gap):
        return self.touching(float(q[0]))


def _lift(top, step=0.002):
    return [np.full(9, z) for z in np.arange(step, top + 1e-9, step)]


def test_a_contact_exit_ends_a_margin_past_where_the_robot_comes_clear():
    kin = LiftKin(lambda z: z < 0.02)
    n, clear = Rig._exit_length(kin, np.zeros(9), _lift(0.07))
    assert clear and kin.tcp(_lift(0.07)[n - 1])[0][2] == pytest.approx(0.02 + LEAVE_MARGIN, abs=0.0021)


def test_a_contact_exit_needs_the_whole_margin_clear():
    kin = LiftKin(lambda z: z < 0.01 or 0.014 < z < 0.02)           # clear, touching again, clear
    n, clear = Rig._exit_length(kin, np.zeros(9), _lift(0.07))
    assert clear and kin.tcp(_lift(0.07)[n - 1])[0][2] == pytest.approx(0.02 + LEAVE_MARGIN, abs=0.0021)


def test_a_clear_start_has_no_contact_segment():
    assert Rig._exit_length(LiftKin(lambda z: False), np.zeros(9), _lift(0.07)) == (0, True)


def test_a_contact_that_lasts_ends_the_segment_at_its_longest():
    qs = _lift(0.10)
    n, clear = Rig._exit_length(LiftKin(lambda z: True), np.zeros(9), qs)
    assert not clear and float(qs[n - 1][0]) <= LEAVE_MAX < float(qs[n][0])


def test_a_short_exit_is_all_contact_segment():
    qs = _lift(0.03)
    assert Rig._exit_length(LiftKin(lambda z: z < 0.025), np.zeros(9), qs) == (len(qs), True)
    assert Rig._exit_length(LiftKin(lambda z: True), np.zeros(9), qs) == (len(qs), False)


def test_leaving_a_contact_runs_the_segment_and_leaves_the_rest_to_the_caller():
    kin = LiftKin(lambda z: z < 0.02)
    rig = SimpleNamespace(kin=kin, q_cmd=np.zeros(9), held=None, logged=[], motions=[])
    rig.log = lambda ev, **kw: rig.logged.append((ev, kw))
    rig.clear = SimpleNamespace(motion=lambda label, allow: rig.motions.append((label, allow)))
    for name in ("_start", "_planning", "_from_contact"):
        setattr(rig, name, getattr(Rig, name).__get__(rig))
    rig._exit_length = Rig._exit_length
    ran = []
    ahead = Rig._leave_contact(rig, "pick_lift", LEAVE_CONTACT, kin, lambda: _lift(0.07), ran.append)
    assert ahead and len(ran) == 1 and float(ran[0][-1][0]) == pytest.approx(0.03, abs=0.0021)
    assert rig.motions == [("pick_lift", LEAVE_CONTACT)]
    ev, kw = rig.logged[-1]
    assert ev == "leave_contact_exit" and kw["clear"] and kw["exit_m"] == pytest.approx(0.03, abs=0.0021)
    ran.clear()
    assert not Rig._leave_contact(rig, "release_back", LEAVE_CONTACT, kin, lambda: _lift(0.015), ran.append)
    assert len(ran[0]) == len(_lift(0.015))                         # all of a short exit, nothing ahead


def test_a_lift_carries_the_object_it_closed_on_until_the_lift_ends():
    from zeno_skills.clearance import lifting
    from zeno_skills.motion import load
    synced = []
    rig = SimpleNamespace(held=None, left_held=None, sync_world=lambda: synced.append(load(rig, "right")))
    allow = lifting("book_red")
    assert allow.from_contact and not allow.checked and allow.lifts == "book_red"
    with Rig._lifting(rig, SimpleNamespace(side="right"), allow):
        assert load(rig, "right")["name"] == "book_red" and load(rig, "left") is None
    assert load(rig, "right") is None
    assert [s and s["name"] for s in synced] == ["book_red", None]   # the world re-synced both ways
    with Rig._lifting(rig, SimpleNamespace(side="right"), LEAVE_CONTACT):
        assert load(rig, "right") is None                              # a plain exit carries nothing new


def _goal_rig(solutions):
    from contextlib import nullcontext
    kin = SimpleNamespace(ik_set=lambda goals, q0: list(solutions))
    rig = SimpleNamespace(kin=kin, q_cmd=np.zeros(9), logged=[], moved=[])
    rig.log = lambda ev, **kw: rig.logged.append((ev, kw))
    rig.sync_world = lambda: None
    rig._planning = lambda kin, q: nullcontext()
    rig.move_to = lambda p, R, step, spw, label, allow, q_hint=None, smooth=False: rig.moved.append((p, q_hint))
    return rig


def test_a_goal_set_moves_once_to_the_cheapest_reachable_goal():
    goals = [(np.full(3, float(i)), np.eye(3)) for i in range(4)]
    rig = _goal_rig([None, np.full(9, 0.6), np.full(9, 0.2), np.full(9, 0.3)])
    assert Rig.move_to_any(rig, goals, label="carry_in") == 2                 # least joint travel
    assert len(rig.moved) == 1 and np.allclose(rig.moved[0][0], 2.0) and np.allclose(rig.moved[0][1], 0.2)
    rig = _goal_rig([None, np.full(9, 0.6), np.full(9, 0.2), np.full(9, 0.3)])
    assert Rig.move_to_any(rig, goals, label="carry_in", cost=[0, 0, 0.5, 0]) == 3   # the caller's cost counts
    ev, kw = rig.logged[-1]
    assert ev == "goal_set" and (kw["goals"], kw["reachable"], kw["chosen"]) == (4, 3, 3)
    assert kw["score"][0] is None and np.allclose(kw["q_goal"], 0.3)


def test_a_goal_set_with_no_reachable_goal_fails_without_moving():
    rig = _goal_rig([None, None])
    with pytest.raises(SkillFailure, match="no goal of 2 reachable"):
        Rig.move_to_any(rig, [(np.zeros(3), np.eye(3))] * 2, label="carry_in")
    assert rig.moved == []
