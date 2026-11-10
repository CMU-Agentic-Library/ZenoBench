"""Skill plans and their execution (docs/MOTION_ARCHITECTURE.md sections 6, 8): the segments in the
skill's order, each from where the one before ends, the State moved on between them; run checks
each segment before it and builds the rest again from here when it no longer holds."""

from types import SimpleNamespace

import numpy as np
import pytest

from tests.test_primitives import IKKin as FakeKin, _q
from zeno_skills import run as RUN
from zeno_skills.motion_state import Failure, Hand, Held, Plan, Segment, Spec, State
from zeno_skills.primitives import PoseSet
from zeno_skills.rig import SkillFailure
from zeno_skills.skill_plans import PICK_STAGES, plan_pick, plan_place

GRASP = {"name": "cup", "p": np.array([0.5, 0.0, 0.10]), "R": np.eye(3), "pre_open": 0.03, "kind": "pinch"}
DOWN = np.array([0.0, 0.0, -1.0])


def _state(q, held=None, objects=None):
    return State(base=(0.0, 0.0, 0.0), q_right=np.asarray(q, float), q_left=np.zeros(7),
                 hands={"right": Hand(width=0.03, held=held)}, objects=objects or {})


def _carry(seen):
    def goals(state, q):
        seen.append(state)
        return PoseSet(((np.array([0.3, 0.0, 0.40]), np.eye(3)),)), {"steps_per_wp": 4}
    return goals


def test_a_pick_is_planned_in_order_and_holds_the_load_after_closing():
    seen = []
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])          # the lift touches up to 12 cm
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, DOWN, 0.07, _carry(seen))
    assert isinstance(plan, Plan) and tuple(s.name for s in plan.segments) == PICK_STAGES
    reach, grasp, lift = plan.segments[1], plan.segments[2], plan.segments[4]
    assert np.allclose(grasp.q_from, reach.q_end)                   # the straight from where the leg ends
    assert np.allclose(reach.q_end[:3], GRASP["p"] - 0.07 * DOWN)
    assert lift.spec.allow.from_contact and lift.info["touching"] == "off_support"
    assert seen and seen[0].held("right").name == "cup"            # the carry is planned with the load held


def test_a_pick_from_a_later_stage_starts_there():
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    held = Held("cup", np.eye(4))
    plan = plan_pick(kin, _state(GRASP["p"].tolist() + [0] * 6, held=held), GRASP, DOWN, 0.07, _carry([]),
                     start="pick_lift")
    assert [s.name for s in plan.segments] == ["pick_lift", "carry_in"]


def test_a_ranking_solution_off_the_reach_ins_start_only_seeds_its_solve_in_the_collision_model():
    # the TCP straight to the reach-in's start is blocked: the leg goes to its solution
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)], wall=lambda p: 0.39 < p[0] < 0.41 and p[2] > 0.25)
    rank = np.full(9, 0.7)                                   # kinematic, its TCP not at the start: a seed
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, DOWN, 0.07,
                     _carry([]), prior={"pick_reach": rank})
    assert isinstance(plan, Plan), plan
    assert ("ik_global", 2) in kin.calls                     # rank first among the seeds, then the arm's
    assert plan.segments[1].info["decided"] == {"pick_reach": "solved"}
    assert np.allclose(plan.segments[1].q_end[:3], GRASP["p"] - 0.07 * DOWN)


def test_no_collision_free_solution_of_the_reach_ins_start_fails_the_plan():
    kin = FakeKin(wall=lambda p: abs(p[2] - 0.17) < 1e-6)
    out = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, DOWN, 0.07, _carry([]))
    assert isinstance(out, Failure) and out.segment == "pick_reach" and "IK" in out.why


def test_a_pick_that_cannot_be_made_says_which_segment():
    kin = FakeKin(wall=lambda p: p[2] < 0.12, plan_to=(None, "IK_FAIL"))    # the grasp pose is in the table
    out = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, DOWN, 0.07, _carry([]))
    assert isinstance(out, Failure) and out.segment == "pick_grasp"


def _place_kin(**kw):
    # the load on the support below z = 0.10: within LEAVE_GAP of the world under 0.10 + a bit
    return FakeKin(near_z=0.115, **kw)


def test_a_place_lets_go_and_tucks_with_the_load_an_obstacle():
    q_p = _q(0.5, 0.0, 0.10)
    held = Held("cup", np.eye(4))
    kin = _place_kin()
    plan = plan_place(kin, _state(_q(0.3, 0.0, 0.40), held=held), q_p[:3], np.eye(3), 0.03, [0, 0, 1], 0.07,
                      (np.zeros(9),), prior={"place_reach": q_p})
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == ["place_reach", "place_down", "place_release", "place_pull_out", "tuck",
                                               "place_settle"]
    assert plan.segments[-1].action == ("wait", 90)                 # the 90 ticks _place_result used to step
    down = plan.segments[1]
    assert np.allclose(down.q_from, plan.segments[0].q_end) and np.allclose(down.q_end[:3], q_p[:3])
    assert plan.segments[0].info["set_down_m"] > 0


def test_the_pull_out_lets_the_fingers_touch_what_they_let_go():
    q = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    plan = plan_place(kin, _state(q, held=Held("cup", np.eye(4))), q[:3], np.eye(3), 0.03, [0, 0, 1], 0.07,
                      (_q(0.3, 0.0, 0.40),), start="place_release")
    pull = plan.segments[1]
    assert pull.name == "place_pull_out" and pull.spec.touch == ("cup",)
    assert pull.spec.allow.touch == ("cup",) and pull.spec.allow.links == "fingers"


# ------------------------------------------------------------------- decisions (docs 4.3, 5.7, 8.1)
def test_a_pick_records_its_decisions_and_a_rebuild_keeps_them():
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    st = _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)})
    plan = plan_pick(kin, st, GRASP, DOWN, 0.07, _carry([]))
    assert set(plan.decisions) == {"pick_reach", "carry_in"} and plan.decisions["carry_in"] == (0, 1)
    assert np.allclose(plan.decisions["pick_reach"][:3], GRASP["p"] - 0.07 * DOWN)
    kin.calls.clear()
    again = plan_pick(kin, st, GRASP, DOWN, 0.07, _carry([]), start="pick_reach", prior=plan)
    assert again.segments[0].info["decided"] == {"pick_reach": "prior"} and not any(c[0] == "ik_global" for c in kin.calls)
    assert np.array_equal(again.decisions["pick_reach"], plan.decisions["pick_reach"])


def test_a_place_records_its_decisions_and_a_rebuild_keeps_them():
    q_p = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    st = _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4)))
    rests = (np.zeros(9), _q(0.3, 0.0, 0.40))
    plan = plan_place(kin, st, q_p[:3], np.eye(3), 0.03, [0, 0, 1], 0.07, rests)
    assert set(plan.decisions) == {"place_reach"}                        # the tuck is chosen again every time
    assert np.allclose(plan.decisions["place_reach"][:3], q_p[:3])
    assert plan.segments[0].info["decided"] == {"set_down_start": "prior", "place_reach": "solved"}
    kin.calls.clear()
    again = plan_place(kin, st, q_p[:3], np.eye(3), 0.03, [0, 0, 1], 0.07, rests, prior=plan)
    assert again.segments[0].info["decided"]["place_reach"] == "prior" and not any(c[0] == "ik_global" for c in kin.calls)


def test_a_decision_no_longer_reaching_its_pose_seeds_the_new_solve():
    q_p = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    prior = {"place_reach": np.r_[0.52, 0.0, 0.10, np.full(6, 0.2)]}    # 2 cm off: the base stopped off its park
    plan = plan_place(kin, _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4))), q_p[:3], np.eye(3), 0.03,
                      [0, 0, 1], 0.07, (np.zeros(9),), prior=prior)
    assert plan.segments[0].info["decided"]["place_reach"] == "solved" and ("ik_global", 2) in kin.calls  # the prior first
    assert np.allclose(plan.decisions["place_reach"], plan.segments[1].q_end)   # recorded: where the set-down ends


def test_a_reach_leg_made_straight_records_where_it_ends_not_the_solution_it_was_given():
    # the ranking solution reaches the start free and is kept, but the TCP straight from the arm gets
    # there first on its own solution: the one pick_grasp starts from is the decision
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    rank = np.r_[GRASP["p"] - 0.07 * DOWN, np.full(6, 0.7)]
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, DOWN, 0.07,
                     _carry([]), prior={"pick_reach": rank})
    reach = plan.segments[1]
    assert reach.info["decided"] == {"pick_reach": "prior"} and reach.info["how"] == "straight"
    assert np.allclose(plan.decisions["pick_reach"], reach.q_end) and not np.allclose(plan.decisions["pick_reach"], rank)
    assert np.allclose(plan.segments[2].q_from, plan.decisions["pick_reach"])


def test_a_place_records_where_its_set_down_ends_not_the_solution_it_was_given():
    q_p = np.r_[0.5, 0.0, 0.10, np.full(6, 0.2)]                         # kept: at the pose, free
    plan = plan_place(_place_kin(), _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4))), q_p[:3], np.eye(3),
                      0.03, [0, 0, 1], 0.07, (np.zeros(9),), prior={"place_reach": q_p})
    down = plan.segments[1]
    assert plan.segments[0].info["decided"]["place_reach"] == "prior"
    assert np.allclose(plan.decisions["place_reach"], down.q_end) and np.allclose(down.q_end[3:], 0.0)


def test_a_pick_keeps_its_carry_goal_only_from_a_set_laid_out_the_same():
    def carry(state, q):
        return PoseSet(((np.array([0.3, 0.0, 0.40]), np.eye(3)), (np.array([0.3, 0.0, 0.60]), np.eye(3)))), {}
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40), _q(0.3, 0.0, 0.60)])
    st = _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)})
    assert plan_pick(kin, st, GRASP, DOWN, 0.07, carry).decisions["carry_in"] == (0, 2)          # the cheaper
    assert plan_pick(kin, st, GRASP, DOWN, 0.07, carry, prior={"carry_in": (1, 2)}).decisions["carry_in"] == (1, 2)
    # decided in a set of 3 (skills._carry_goals: another number of heights): its index means another goal here
    assert plan_pick(kin, st, GRASP, DOWN, 0.07, carry, prior={"carry_in": (1, 3)}).decisions["carry_in"] == (0, 2)


# ------------------------------------------------------------------------------- run
class FakeRig:
    """A motion_state.Actuator: the arm goes where it is told, the State is read off it (observe is
    patched in the tests)."""

    def __init__(self, kin, q):
        self.kin, self.q_cmd, self.events, self.ran, self.declared = kin, np.asarray(q, float), [], [], []

    def log(self, ev, **kw):
        self.events.append((ev, kw))

    def arm_kin(self, side="right"):
        return self.kin

    def declare(self, name, allow, side="right", follows=True):
        self.declared.append((name, side))

    def contact_allow(self, kin, allow):
        return allow

    def follow(self, qs, steps_per_wp=3, smooth=False, side="right"):
        self.ran.append(len(qs))
        self.q_cmd = np.asarray(qs[-1], float)


def _seg(name, q0, q1):
    return Segment(name, Spec(), np.asarray(q0, float), (np.asarray(q1, float),))


def test_run_takes_the_plan_as_it_is_while_it_holds(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    plan = Plan((_seg("a", np.zeros(9), np.full(9, 0.1)), _seg("b", np.full(9, 0.1), np.full(9, 0.2))))
    done = RUN.run(rig, plan, rebuild=lambda s, n, prior: pytest.fail("rebuilt"))
    assert [s.name for s in done] == ["a", "b"] and np.allclose(rig.q_cmd, 0.2)


def test_run_builds_the_rest_again_when_a_segment_no_longer_holds(monkeypatch):
    rig = FakeRig(FakeKin(seg_free=True), np.zeros(9))
    rig.kin.path_free = lambda qs: False                            # the world changed: "a" collides now
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    asked = []

    def rebuild(state, name, prior):
        asked.append(name)
        return Plan((_seg("a2", state.q_right, np.full(9, 0.3)),))
    rig.kin.path_free = lambda qs: len(asked) > 0                   # the rebuilt one is free
    done = RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.1)),)), rebuild)
    assert asked == ["a"] and [s.name for s in done] == ["a2"]


def test_a_rest_that_cannot_be_built_fails_the_skill(monkeypatch):
    rig = FakeRig(FakeKin(), np.full(9, 0.5))                       # not where the segment starts
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    with pytest.raises(SkillFailure, match="not where the segment starts.*no way"):
        RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.1)),)), lambda s, n, prior: Failure("no way", n))


def test_run_hands_the_plan_as_it_stands_to_a_rebuild_its_decisions_kept(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    rig.kin.path_free = lambda qs: not any(np.allclose(q, 0.9) for q in qs)     # 0.9: in the way now
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    priors = []

    def rebuild(state, name, prior):
        priors.append((name, [s.name for s in prior.segments], prior.decisions))   # kept as handed over
        if name == "a":
            return Plan((_seg("a2", state.q_right, np.full(9, 0.3)), _seg("b2", np.full(9, 0.3), np.full(9, 0.9))),
                        decisions={"a_reach": 2})
        return Plan((_seg("b3", state.q_right, np.full(9, 0.4)),))
    plan = Plan((_seg("a", np.zeros(9), np.full(9, 0.9)),), decisions={"a_reach": 1, "tuck": 0})
    done = RUN.run(rig, plan, rebuild)
    assert [s.name for s in done] == ["a2", "b3"]
    assert priors == [("a", ["a"], {"a_reach": 1, "tuck": 0}), ("b2", ["a2", "b2"], {"a_reach": 2, "tuck": 0})]
    assert plan.decisions == {"a_reach": 1, "tuck": 0}                     # the plan run is not changed either


def test_a_rebuild_logs_how_the_segment_run_now_was_decided(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    rig.kin.path_free = lambda qs: not any(np.allclose(q, 0.9) for q in qs)
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    a2 = Segment("a2", Spec(), np.zeros(9), (np.full(9, 0.3),), info={"decided": {"a_reach": "prior"}})
    RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.9)),)), lambda s, n, prior: Plan((a2,)))
    ev = [kw for e, kw in rig.events if e == "segment"]
    assert ev == [{"target": "a", "reused": False, "why": ev[0]["why"], "rebuilt": ["a2"], "decided": {"a_reach": "prior"}}]


def test_the_place_tuck_is_chosen_again_the_fold_first_whatever_the_plan_chose():
    q = _q(0.5, 0.0, 0.10)
    rests = (_q(0.5, 0.0, 0.15), _q(0.3, 0.0, 0.40))
    plan = plan_place(_place_kin(), _state(q), q[:3], np.eye(3), 0.03, [0, 0, 1], 0.07, rests, start="tuck", obj="cup",
                      prior={"tuck": (1, 2)})
    assert plan.segments[0].info["chosen"] == 0 and "tuck" not in plan.decisions


def test_the_relay_decisions_are_the_builders_stage_names():
    from zeno_skills.skill_plans import PICK_RELAY, PLACE_RELAY, PLACE_STAGES
    assert PICK_RELAY in PICK_STAGES and PLACE_RELAY in PLACE_STAGES
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, DOWN, 0.07, _carry([]))
    assert PICK_RELAY in plan.decisions


# ------------------------------------------------------------------- the jobs' whole re-plans (skill_jobs)
def _job_rig():
    kin = FakeKin()
    kin.rest, kin.drive = np.zeros(9), np.full(9, 0.1)
    return SimpleNamespace(kin=kin, log=lambda *a, **k: None)


def test_a_pick_made_again_after_the_drive_takes_the_found_plans_decisions(monkeypatch):
    from zeno_skills.skill_jobs import pick as PJ
    g = {"p": GRASP["p"], "R": np.eye(3), "pre_open": 0.03, "kind": "pinch"}
    calls = []

    def plan_pick_(kin, state, grasp, u, L, carry_goals, start="pick_open", prior=None, step=0.003):
        calls.append((start, prior))
        return Plan(())
    monkeypatch.setattr(PJ, "observe", lambda rig: _state(np.zeros(9)))

    def found(dx):
        return Plan((Segment("pick_grasp", Spec(), np.zeros(9), target=("pose", GRASP["p"] + [dx, 0.0, 0.0], np.eye(3))),),
                    decisions={"pick_reach": np.ones(9)})
    here = found(0.0005)                                              # within HINT_REACH: run as it is
    plan, rebuild, hooks = PJ._pick_ready(_job_rig(), "cup", g, here, None, {}, plan_pick_)
    assert plan is here and not calls
    moved = found(0.002)                                              # the grasp re-read 2 mm off
    plan, rebuild, hooks = PJ._pick_ready(_job_rig(), "cup", g, moved, None, {}, plan_pick_)
    assert calls[0][0] == "pick_open" and calls[0][1] is moved
    rebuild(_state(np.zeros(9)), "carry_in", plan)                    # run's rebuild: the plan as it stands
    assert calls[1][0] == "carry_in" and calls[1][1] is plan


def test_a_place_made_again_after_the_drive_takes_the_found_plans_decisions(monkeypatch):
    from zeno_skills.skill_jobs import place as LJ
    p, calls = np.array([0.5, 0.0, 0.10]), []

    def plan_place_(kin, state, p, R, pre_open, u_out, out_len, rest_goals, start="place_reach", prior=None,
                    step=0.003, obj=None):
        calls.append((start, prior))
        return Plan(())
    monkeypatch.setattr(LJ, "observe", lambda rig: _state(np.zeros(9)))
    turned = Plan((Segment("place_down", Spec(), np.zeros(9), target=("pose", p, LJ.quat_R([0.9999, 0.0, 0.0, 0.0141]))),))
    plan, rebuild, hooks = LJ._place_ready(_job_rig(), "cup", {}, p, np.eye(3), 0.03, turned, plan_place_)
    assert calls[0][0] == "place_reach" and calls[0][1] is turned       # turned ~1.6 deg in the pinch: made again
    rebuild(_state(np.zeros(9)), "tuck", plan)
    assert calls[1][0] == "tuck" and calls[1][1] is plan


# ------------------------------------------------------------------- the State the same at every build
def test_a_pull_out_built_again_after_the_release_still_lets_the_fingers_touch_what_they_let_go():
    # run builds the rest again from the State read after the release: the hand holds nothing then
    # (the release hook has cleared rig.held); the object set down is given, not read off the hand
    q = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    planned = plan_place(kin, _state(q, held=Held("cup", np.eye(4))), q[:3], np.eye(3), 0.03, [0, 0, 1], 0.07,
                         (_q(0.3, 0.0, 0.40),), start="place_release")
    rebuilt = plan_place(kin, _state(q), q[:3], np.eye(3), 0.03, [0, 0, 1], 0.07, (_q(0.3, 0.0, 0.40),),
                         start="place_pull_out", obj="cup")
    assert planned.segments[1].spec.touch == rebuilt.segments[0].spec.touch == ("cup",)
    assert planned.segments[0].spec.allow.touch == ("cup",)        # the release declares it too
    assert "place_pull_out" in planned.info["stage_s"]


def test_the_place_tuck_takes_the_first_free_of_its_goals_as_a_joint_set():
    q = _q(0.5, 0.0, 0.10)
    kin = _place_kin(wall=lambda p: p[2] < 0.06)                    # the fold (low) collides here
    plan = plan_place(kin, _state(q), q[:3], np.eye(3), 0.03, [0, 0, 1], 0.07,
                      (_q(0.5, 0.0, 0.05), _q(0.3, 0.0, 0.40)), start="tuck", obj="cup")
    assert plan.segments[0].info["chosen"] == 1 and np.allclose(plan.segments[0].q_end, _q(0.3, 0.0, 0.40))


def test_a_pick_opens_the_hand_in_its_own_state_for_every_later_stage():
    # the search and a rebuild alike: plan_pick moves the State's hand to pre_open itself
    seen = []
    st = State(base=(0.0, 0.0, 0.0), q_right=_q(0.3, 0.0, 0.40), q_left=np.zeros(7),
               hands={"right": Hand(width=0.0)}, objects={"cup": np.eye(4)})
    plan = plan_pick(FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)]), st, GRASP, DOWN, 0.07, _carry(seen))
    assert isinstance(plan, Plan) and seen and seen[0].hands["right"].width == GRASP["pre_open"]


def test_every_action_is_declared_to_the_contact_monitor(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    rig.grip = lambda *a, **k: None
    seg = Segment("pick_open", Spec(), np.zeros(9), kind="action", action=("grip", 0.03, 40, False))
    RUN.execute(rig, seg)
    assert rig.declared == [("pick_open", "right")]


def test_a_contact_exit_measured_again_within_half_the_margin_holds(monkeypatch):
    from zeno_skills import primitives as P
    seg = Segment("pick_lift", Spec(allow=P_LEAVE()), np.zeros(9), (np.full(9, 0.01),),
                  info={"u": np.array([0, 0, 1.0]), "touching": "near_world", "step": 0.002, "length": 0.016})
    for measured, holds in ((0.018, True), (0.014, True), (0.016 + RUN.EXTENT_TOL + 0.001, False)):
        monkeypatch.setattr(RUN, "contact_extent", lambda *a, m=measured, **k: P.Extent(np.zeros(9), (), m, True))
        assert (RUN.holds(FakeKin(), _state(np.zeros(9)), seg) is None) == holds, measured


def P_LEAVE():
    from zeno_skills.clearance import LEAVE_CONTACT
    return LEAVE_CONTACT



# ------------------------------------------------------------------- the failure exit (docs 8.6)
def test_the_failure_exit_opens_an_empty_hand_and_backs_out_of_the_contact_straight_up():
    from zeno_skills.skill_plans import plan_clear
    kin = FakeKin(near_z=0.12)                                       # touching below 12 cm
    plan = plan_clear(kin, _state(_q(0.5, 0.0, 0.10)), open_width=0.04)
    assert [s.name for s in plan.segments] == ["fail_clear_open", "fail_clear"]
    assert plan.segments[0].action[:2] == ("grip", 0.04) and plan.segments[1].spec.allow.from_contact
    assert plan.segments[1].q_end[2] > 0.12                          # clear of the contact
    assert plan_clear(kin, _state(_q(0.5, 0.0, 0.10)), leave=False, open_width=None) is None   # nothing asked
    held = _state(_q(0.5, 0.0, 0.10), held=Held("cup", np.eye(4)))
    assert plan_clear(kin, held, open_width=0.04) is None            # opening would drop the load


def test_a_hook_failure_that_asks_for_the_exit_has_it_run_before_it_is_raised(monkeypatch):
    from zeno_skills.motion_state import clearing
    rig = FakeRig(FakeKin(), np.zeros(9))
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    asked = []
    exit_plan = Plan((_seg("fail_clear", np.full(9, 0.1), np.full(9, 0.3)),))

    def hook(act):
        raise clearing(SkillFailure("not pinched"), 0.04)
    with pytest.raises(SkillFailure, match="not pinched"):
        RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.1)),)), None, {"a": {"after": hook}},
                clear=lambda st, what: asked.append(what) or exit_plan)
    assert asked == [{"open_width": 0.04, "leave": True, "ticks": 60}] and np.allclose(rig.q_cmd, 0.3)
    with pytest.raises(SkillFailure):                                # not asked: no exit
        RUN.run(rig, Plan((_seg("b", rig.q_cmd, np.full(9, 0.4)),)), None,
                {"b": {"after": lambda a: (_ for _ in ()).throw(SkillFailure("plain"))}},
                clear=lambda st, what: pytest.fail("ran an exit nobody asked for"))


def test_a_wait_segment_lets_the_world_settle_through_the_actuator():
    rig = FakeRig(FakeKin(), np.zeros(9))
    waited = []
    rig.wait = waited.append
    RUN.execute(rig, Segment("place_settle", Spec(), np.zeros(9), kind="action", action=("wait", 90)))
    assert waited == [90] and rig.declared == [("place_settle", "right")]


def test_the_skill_jobs_hooks_do_not_move_the_robot():
    # docs 8.6: hooks and results judge, register and log; the motion is a plan run.run makes
    import ast
    from pathlib import Path
    moves = {"grip", "leave", "step", "move_to", "follow", "drive_base", "swing", "tuck", "_planning",
             "_fingers_checked", "joint_path"}
    for f in (Path(__file__).resolve().parents[1] / "zeno_skills" / "skill_jobs").glob("*.py"):
        calls = [n for n in ast.walk(ast.parse(f.read_text())) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                 and n.func.value.id in ("rig", "r") and n.func.attr in moves]
        assert not calls, (f.name, [(c.lineno, c.func.attr) for c in calls])
