"""Skill plans and their execution (docs/MOTION_ARCHITECTURE.md sections 6, 8): the segments in the
skill's order, each from where the one before ends, the State moved on between them; run checks
each segment before it and builds the rest again from here when it no longer holds."""

from types import SimpleNamespace

import numpy as np
import pytest

from tests.test_primitives import FakeKin as _FakeKin, _q
from zeno_skills import run as RUN
from zeno_skills.motion_state import Failure, Hand, Held, Plan, Segment, Spec, State
from zeno_skills.primitives import PoseSet
from zeno_skills.rig import SkillFailure
from zeno_skills.skill_plans import PICK_STAGES, plan_pick, plan_place

class FakeKin(_FakeKin):
    """test_primitives' FakeKin with a collision-aware IK: the TCP at p, unless p is in the wall."""

    def ik_global(self, p, R, seeds=None):
        self.calls.append(("ik_global", len(seeds or [])))
        q = np.asarray((seeds or [np.zeros(9)])[0], float).copy()
        q[:3] = p
        return q, not (self.scene is not None and self.wall(np.asarray(p, float)))


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


def test_the_reach_ins_start_is_solved_in_the_collision_model_the_rank_ik_only_a_seed():
    # the TCP straight to the reach-in's start is blocked: the leg goes to its solution
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)], wall=lambda p: 0.39 < p[0] < 0.41 and p[2] > 0.25)
    rank = np.full(9, 0.7)                                   # a kinematic solution, never checked
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, DOWN, 0.07,
                     _carry([]), q_seed=rank)
    assert isinstance(plan, Plan), plan
    assert ("ik_global", 2) in kin.calls                     # rank first among the seeds, then the arm's
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
                      (np.zeros(9),), q_p=q_p)
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
    done = RUN.run(rig, plan, rebuild=lambda s, n: pytest.fail("rebuilt"))
    assert [s.name for s in done] == ["a", "b"] and np.allclose(rig.q_cmd, 0.2)


def test_run_builds_the_rest_again_when_a_segment_no_longer_holds(monkeypatch):
    rig = FakeRig(FakeKin(seg_free=True), np.zeros(9))
    rig.kin.path_free = lambda qs: False                            # the world changed: "a" collides now
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    asked = []

    def rebuild(state, name):
        asked.append(name)
        return Plan((_seg("a2", state.q_right, np.full(9, 0.3)),))
    rig.kin.path_free = lambda qs: len(asked) > 0                   # the rebuilt one is free
    done = RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.1)),)), rebuild)
    assert asked == ["a"] and [s.name for s in done] == ["a2"]


def test_a_rest_that_cannot_be_built_fails_the_skill(monkeypatch):
    rig = FakeRig(FakeKin(), np.full(9, 0.5))                       # not where the segment starts
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    with pytest.raises(SkillFailure, match="not where the segment starts.*no way"):
        RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.1)),)), lambda s, n: Failure("no way", n))


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
