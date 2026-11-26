"""navigate on the motion layers (docs/motion/MOTION_ARCHITECTURE.md 6, navigate; 5.4 drive; 9.3 step 1):
plan_navigate's arm stage, the drive segment, its execution, the travel chain the park search shares,
and the catalog run_skill reads."""

import json
from types import SimpleNamespace

import numpy as np
import pytest

from tests.test_primitives import FakeKin, _q
from zeno_skills import motion_skills as MS
from zeno_skills import primitives as P
from zeno_skills import run as RUN
from zeno_skills.motion_state import Failure, Hand, Held, Plan, Posture, State, chains
from zeno_skills.primitives import PoseSet
from zeno_skills.skill_plans import Carry, plan_navigate, travel_chain

REST, DRIVE = _q(0.2, 0.0, 0.3), _q(0.1, -0.3, 0.2)
LREST, LDRIVE = np.r_[0.0, 0.0, np.full(7, 0.5)], np.r_[0.0, 0.0, np.full(7, -0.5)]


class Kin(FakeKin):
    def __init__(self, side="right", **kw):
        super().__init__(**kw)
        self.side, self.rest, self.drive = side, (REST if side == "right" else LREST), (DRIVE if side == "right" else LDRIVE)


class Base:
    """motion_state.BaseModel: one drive to the goal, a swing per posture of the chain that differs
    from the start; ``blocked``: no plan."""

    def __init__(self, blocked=None):
        self.blocked, self.asked = blocked, []

    def plan(self, state, goal, chain, label, quiet=False):
        self.asked.append((tuple(state.base), goal, [n for n, _ in chain]))
        if self.blocked:
            return None, f"{label}: {self.blocked}"
        steps = [("drive", [tuple(goal)], "start")]
        for name, p in chain:
            if np.max(np.abs(p.q("right") - state.q("right"))) > 0.02:
                steps.append(("swing", name, p))
        return steps, None

    def straight(self, state, target, label):
        return [tuple(target)], None


def _state(q=REST, ql=np.full(7, 0.5), held=None):
    return State(base=(0.0, 0.0, 0.0), **chains(np.asarray(q, float), np.asarray(ql, float)),
                 hands={"right": Hand(0.0, held), "left": Hand(0.0)})


def _nav(state, **kw):
    return plan_navigate(Kin(), Kin("left"), state, (1.0, 2.0, 90.0), kw.pop("base", Base()), **kw)


def test_an_empty_folded_arm_drives_as_it_is_and_arrives():
    plan = _nav(_state())
    assert isinstance(plan, Plan) and [(s.name, s.kind) for s in plan.segments] == [("navigate", "drive"),
                                                                                  ("arrive", "anchor")]


def test_an_empty_arm_out_tucks_first_to_the_first_free_of_fold_and_hanging():
    plan = _nav(_state(q=_q(0.5, 0.0, 0.5)))
    tuck = plan.segments[0]
    assert tuck.name == "tuck" and np.allclose(tuck.q_end, REST) and tuck.info["chosen"] == 0
    assert plan.segments[1].kind == "drive" and np.allclose(Posture.from_vec(plan.segments[1].q_from).q("right"), REST)
    # the fold collides where it stands: hanging at the side
    k = Kin(wall=lambda p: np.allclose(p, REST[:3]))
    plan = plan_navigate(k, Kin("left"), _state(q=_q(0.5, 0.0, 0.5)), (1.0, 2.0, 90.0), Base())
    assert plan.segments[0].info["chosen"] == 1 and np.allclose(plan.segments[0].q_end, DRIVE)


def test_no_tuck_leaves_the_switch_to_the_base_plan():
    k = Kin(wall=lambda p: np.allclose(p, REST[:3]) or np.allclose(p, DRIVE[:3]))
    plan = plan_navigate(k, Kin("left"), _state(q=_q(0.5, 0.0, 0.5)), (1.0, 2.0, 90.0), Base())
    assert plan.segments[0].kind == "drive" and "tuck" in plan.info["skipped"]


def test_an_empty_left_arm_out_folds_as_a_left_segment():
    plan = _nav(_state(ql=np.zeros(7)))
    left = plan.segments[0]
    assert left.name == "left_fold" and left.info["side"] == "left"
    assert np.allclose(left.q_end[2:], LREST[2:]) and np.allclose(left.q_end[:2], REST[:2])     # torso and waist kept


def test_a_load_whose_posture_meets_the_carry_constraints_rides_as_it_is():
    held = Held("cup", np.eye(4))
    q = _q(0.4, -0.2, 0.9)
    carry = Carry(check=lambda s: None, goals=lambda s, q: pytest.fail("decided again"))
    plan = _nav(_state(q=q, held=held), carry=carry)
    assert [s.kind for s in plan.segments] == ["drive", "anchor"] and plan.info["carry"] == "kept"


def test_a_load_that_does_not_meet_them_is_planned_to_the_carry_goal_set_or_the_skill_fails():
    held = Held("cup", np.eye(4))
    goal = (np.array([0.4, -0.2, 1.0]), np.eye(3))
    carry = Carry(check=lambda s: "the load's bottom is too low",
                  goals=lambda s, q: (PoseSet((goal,)), {"step": 0.01, "steps_per_wp": 6, "smooth": True}))
    k = Kin()
    k.ik = [_q(0.4, -0.2, 1.0)]
    plan = plan_navigate(k, Kin("left"), _state(q=_q(0.4, -0.2, 0.9), held=held), (1.0, 2.0, 90.0), Base(), carry=carry)
    assert plan.segments[0].name == "carry_in" and plan.segments[0].info["smooth"]
    assert np.allclose(Posture.from_vec(plan.segments[1].q_from).q("right"), plan.segments[0].q_end)
    k.ik = [None]
    out = plan_navigate(k, Kin("left"), _state(q=_q(0.4, -0.2, 0.9), held=held), (1.0, 2.0, 90.0), Base(), carry=carry)
    assert isinstance(out, Failure) and out.segment == "carry_in" and "too low" in out.why


def test_a_load_in_each_hand_has_each_its_own_carry_posture():
    # HAND_PLAN 3.3 / 3.4: every hand that holds a load is checked against its carry constraints and planned to its
    # carry goal set when it fails them (until the rule audit of 11-25 the right's only, the left's load unchecked)
    goal_r = (np.array([0.4, -0.2, 1.0]), np.eye(3))
    goal_l = (np.array([0.4, 0.2, 1.0]), np.eye(3))
    low = lambda goal: Carry(check=lambda s: "the load's bottom is too low",
                             goals=lambda s, q: (PoseSet((goal,)), {"step": 0.01}))
    right, left = Kin(), Kin("left")
    right.ik, left.ik = [_q(0.4, -0.2, 1.0)], [np.r_[0.4, 0.2, 1.0, np.zeros(6)]]
    st = State(base=(0.0, 0.0, 0.0), **chains(_q(0.4, -0.2, 0.9), np.r_[0.4, 0.2, 0.9, np.zeros(4)]),
               hands={"right": Hand(0.0, Held("cup", np.eye(4))), "left": Hand(0.0, Held("pen", np.eye(4)))})
    carries = (Carry(**{**low(goal_r).__dict__, "side": "right"}), Carry(**{**low(goal_l).__dict__, "side": "left"}))
    plan = plan_navigate(right, left, st, (1.0, 2.0, 90.0), Base(), carry=carries)
    assert [s.name for s in plan.segments][:2] == ["carry_in", "left_carry_in"], plan
    assert plan.info["carry_by_side"] == {"right": "the load's bottom is too low", "left": "the load's bottom is too low"}
    # one Carry still takes its own side only
    one = plan_navigate(right, left, st, (1.0, 2.0, 90.0), Base(), carry=carries[1])
    assert [s.name for s in one.segments][0] == "left_carry_in" and "carry_in" not in [s.name for s in one.segments]


def test_a_blocked_drive_fails_the_plan():
    out = _nav(_state(), base=Base(blocked="no path"))
    assert isinstance(out, Failure) and "no path" in out.why


def test_the_travel_chain_hangs_only_empty_handed_and_keeps_a_load_as_it_is():
    chain = travel_chain(Kin(), Kin("left"), _state(q=_q(0.5, 0.0, 0.5)))
    assert [n for n, _ in chain] == ["fold", "hang", "arrive"]
    assert np.allclose(chain[0][1].q("right"), REST) and np.allclose(chain[1][1].q("right"), DRIVE) and \
        np.allclose(chain[1][1].arms["left"], LDRIVE[2:])
    q = _q(0.4, -0.2, 0.9)
    chain = travel_chain(Kin(), Kin("left"), _state(q=q, held=Held("cup", np.eye(4))))
    assert all(np.allclose(p.q("right"), q) for _, p in chain)


def test_a_load_in_the_left_hand_keeps_the_body_as_it_is_while_the_right_arm_folds():
    # docs 4.1, either hand alike: the body moves the left load too (s11 T23 11-26)
    q, ql = _q(0.4, -0.2, 0.9), np.full(7, 0.3)
    s = _state(q=q, ql=ql)
    s = State(base=s.base, body=s.body, arms=s.arms,
              hands={"right": Hand(0.0), "left": Hand(0.0, Held("spoon", np.eye(4)))})
    chain = travel_chain(Kin(), Kin("left"), s)
    for _, p in chain:
        assert np.allclose(p.body, q[:2]) and np.allclose(p.arms["right"], REST[2:]) and np.allclose(p.arms["left"], ql)


def test_a_drive_segment_runs_its_drives_and_swings_through_the_actuator(monkeypatch):
    seg = P.drive(Base(), _state(q=_q(0.5, 0.0, 0.5)), (1.0, 2.0, 90.0), travel_chain(Kin(), Kin("left"), _state()),
                  "navigate", speed=0.1)
    assert seg.kind == "drive" and np.allclose(Posture.from_vec(seg.q_end).q("right"), REST)
    ran = []
    act = SimpleNamespace(log=lambda *a, **k: None, drive_base=lambda path, **kw: ran.append(("drive", path, kw)),
                          swing=lambda posture, label: ran.append(("swing", label)))
    RUN.execute(act, seg)
    assert ran[0][0] == "drive" and ran[0][2]["speed"] == 0.1 and ("swing", "navigate_fold") in ran
    assert P.holds(Kin(), _state(q=_q(0.5, 0.0, 0.5)), seg) is None
    assert P.holds(Kin(), _state(q=_q(0.9, 0.0, 0.5)), seg) is not None       # the arm is not where it starts
    assert P.holds(Kin(), _state(q=_q(0.5, 0.0, 0.5), ql=np.full(7, 0.9)), seg) is not None   # nor the left


def test_the_catalog_names_each_skill_once_with_a_builder_and_a_job(tmp_path):
    skills = MS.load()
    assert set(skills) >= {"navigate", "pick", "place"}
    assert skills["pick"].park and not skills["navigate"].park and skills["place"].template == "plan_place"
    assert skills["navigate"].skill_id == "skill_001"
    bad = json.loads(MS.CATALOG.read_text())
    bad["motion_skills"]["skills"][0]["template"] = "plan_nothing"
    (tmp_path / "c.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="no builder"):
        MS.load(tmp_path / "c.json")
    bad["motion_skills"]["skills"][0].update(template="plan_navigate", shape="dance")
    (tmp_path / "c.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="shape"):
        MS.load(tmp_path / "c.json")


def test_a_higher_ride_asked_is_taken_when_reachable_else_the_load_rides_as_it_is():
    held = Held("cup", np.eye(4))
    goal = (np.array([0.4, -0.2, 1.4]), np.eye(3))
    carry = Carry(check=lambda s: None, goals=lambda s, q: pytest.fail("the constraints hold"),
                  want=lambda s: "below the rim asked",
                  raise_goals=lambda s, q: (PoseSet((goal,)), {"step": 0.01}))
    k = Kin()
    k.ik = [_q(0.4, -0.2, 1.4)]
    plan = plan_navigate(k, Kin("left"), _state(q=_q(0.4, -0.2, 0.9), held=held), (1.0, 2.0, 90.0), Base(), carry=carry)
    assert plan.segments[0].name == "carry_in" and np.allclose(plan.segments[0].q_end[:3], [0.4, -0.2, 1.4])
    k.ik = [None]                                            # out of reach: no failure, no motion
    plan = plan_navigate(k, Kin("left"), _state(q=_q(0.4, -0.2, 0.9), held=held), (1.0, 2.0, 90.0), Base(), carry=carry)
    assert [s.kind for s in plan.segments] == ["drive", "anchor"] and plan.info["carry"].startswith("kept: below")


def test_navigates_rebuild_takes_the_prior_run_hands_it():
    # run.run calls rebuild(state, segment name, prior) (docs 8): navigate's must take it too
    from zeno_skills.skill_jobs.navigate import navigate_job
    built = []

    def plan_nav(kin, left_kin, st, pose, base, carry=None, arrive=None, label=None, start="arm"):
        built.append(start)
        return Plan(())
    rig = SimpleNamespace(held=None, left_held=None, held_by=lambda side="right": None, kin=None, left_kin=None,
                          log=lambda *a, **k: None)
    job = navigate_job(rig, {"pose": (1.0, 2.0, 90.0)}, _state(), SimpleNamespace(build=plan_nav))
    plan, rebuild, hooks = job.ready(None)
    assert isinstance(rebuild(_state(), "tuck", plan), Plan) and built == ["arm", "arm"]
