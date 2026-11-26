"""Which hand (docs/motion/HAND_PLAN.md 3.1, rule 2): the hand is a dimension of a skill's goal set, ranked with
the rest of it -- the right first only by VARIANT_COST -- never chosen by the job before the search.  A park search
carries it in Problem.goals (touch / knock here; pick, push: their own tests); an in-place skill ranks the hands'
goal sets by free_leg's own score (skill_jobs.held._either_hand)."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills.motion_state import Failure, Plan, Segment, Spec
from zeno_skills.park_search import VARIANT_COST
from zeno_skills.primitives import PoseSet, pose_set_scores
from zeno_skills.skill_jobs import held as H


class _Arm:
    """An arm whose IK of a goal (p, R) is the 9-vector p[0] repeated (None past ``reach`` in x)."""

    def __init__(self, side, reach=1.0):
        self.side, self.reach, self.motion = side, reach, None

    def ik_set(self, goals, q0, weights=None):
        return [None if p[0] > self.reach else np.full(9, float(p[0])) for p, _ in goals]


def _state(q=0.0):
    return SimpleNamespace(q=lambda side: np.full(9, q))


def _rig(reach=None):
    arms = {sd: _Arm(sd, (reach or {}).get(sd, 1.0)) for sd in ("right", "left")}
    return SimpleNamespace(arm_kin=lambda side: arms[side])


def _goals(*xs):
    return PoseSet(tuple((np.array([x, 0.0, 1.0]), np.eye(3)) for x in xs))


def _plan(side):
    return Plan((Segment("wave_reach", Spec(), np.zeros(9), info={"side": side}),))


def test_free_leg_and_the_hand_choice_rank_a_goal_set_by_the_same_score():
    score, sols = pose_set_scores(_Arm("right"), _state(0.1), Spec(), _goals(0.5, 0.3, 2.0))
    assert score[:2] == pytest.approx([0.4, 0.2]) and np.isinf(score[2]) and sols[2] is None


def test_the_cheaper_hand_is_built_first_and_the_right_wins_only_a_tie():
    built = []

    def build_for(sd):
        built.append(sd)
        return _plan(sd)
    # the left's best goal is the cheaper by more than VARIANT_COST: the left
    goals = {"right": _goals(0.5), "left": _goals(0.2)}
    plan = H._either_hand(_rig(), _state(), ("right", "left"), goals.get, lambda sd: Spec(), build_for)
    assert built == ["left"] and H._plan_hand(plan) == "left"
    # a tie: VARIANT_COST puts the right first (a weak preference, not "the right, then the left")
    built.clear()
    goals = {"right": _goals(0.2), "left": _goals(0.2 + VARIANT_COST / 2)}
    H._either_hand(_rig(), _state(), ("right", "left"), goals.get, lambda sd: Spec(), build_for)
    assert built == ["right"]


def test_a_hand_whose_plan_does_not_build_gives_way_to_the_next_and_none_reaching_is_a_failure():
    goals = {"right": _goals(0.2), "left": _goals(0.3)}
    plan = H._either_hand(_rig(), _state(), ("right", "left"), goals.get, lambda sd: Spec(),
                          lambda sd: Failure("the tuck collides", "wave_back") if sd == "right" else _plan(sd))
    assert H._plan_hand(plan) == "left"
    out = H._either_hand(_rig({"right": 0.0, "left": 0.0}), _state(), ("right", "left"), goals.get,
                         lambda sd: Spec(), lambda sd: pytest.fail("built with no goal reachable"))
    assert isinstance(out, Failure) and "right: no goal" in out.why and "left: no goal" in out.why


def test_a_touch_has_every_target_with_every_empty_hand_in_one_park_search(monkeypatch):
    from zeno_skills.skill_jobs import press as P
    kin = SimpleNamespace(rest=np.zeros(9))
    rig = SimpleNamespace(held_by=lambda side="right": None, arm_kin=lambda side: kin, base_pose=lambda: (0.0, 0.0, 0.0),
                          state=lambda: {}, obj_pose=lambda name: (np.zeros(3), np.array([1.0, 0, 0, 0])),
                          geo=SimpleNamespace(bottom=lambda name, st: np.zeros(3), centre=lambda name, st: np.zeros(3)),
                          ann=SimpleNamespace(objects={"cup": {}}, asset_of=lambda o: {"size": [0.1, 0.1, 0.1]}))
    job = P.touch_job(rig, {"name": "cup"}, None, skill=SimpleNamespace(build=lambda *a, **k: None))
    goals = job.problem.goals
    n = len(P.TOUCH_CLOSES)
    assert [g[3] for g in goals] == ["right"] * n + ["left"] * n
    assert [g[2] for g in goals[n:]] == pytest.approx([g[2] + VARIANT_COST for g in goals[:n]])
    rig.held_by = lambda side="right": {"name": "pen"} if side == "right" else None
    job = P.touch_job(rig, {"name": "cup"}, None, skill=SimpleNamespace(build=lambda *a, **k: None))
    assert {g[3] for g in job.problem.goals} == {"left"} and job.problem.hand == "left"


def test_a_picks_goal_set_has_every_empty_hand_and_the_route_may_name_one(monkeypatch):
    # HAND_PLAN 3.1 / 3.2: each grasp candidate with each empty hand one goal (the left VARIANT_COST behind); the
    # route's hands "right" / "left" keeps only that one, "any" / "both" / none both; a full hand never
    from zeno_skills.skill_jobs import pick as PJ
    rig = SimpleNamespace(held=None, left_held=None, kin=SimpleNamespace(side="right"), left_kin=SimpleNamespace(side="left"))
    assert PJ.pick_hands(rig, "cup") == ("right", "left") == PJ.pick_hands(rig, "cup", "any") == PJ.pick_hands(rig, "cup", "both")
    assert PJ.pick_hands(rig, "cup", "left") == ("left",)
    rig.held = {"name": "pen"}
    assert PJ.pick_hands(rig, "cup") == ("left",)
    with pytest.raises(Exception, match="no empty hand"):
        PJ.pick_hands(rig, "cup", "right")
    monkeypatch.setattr(PJ, "_carry_goal_set", lambda rig, name, side="right": f"carry-{side}")
    monkeypatch.setattr(PJ, "_grasp_of", lambda name, g, T: g)
    monkeypatch.setattr(PJ, "_grasp_approach", lambda g: (np.array([0.0, 0.0, -1.0]), 0.07))
    cands = [{"p": np.array([0.5, 0.0, 0.8]), "R": np.eye(3)}, {"p": np.array([0.5, 0.1, 0.8]), "R": np.eye(3)}]
    problem, carry, grasps, which = PJ._pick_problem(rig, "cup", cands, np.eye(4), (0.0, 0.0), sides=("right", "left"))
    assert [g[3] for g in problem.goals] == ["right", "right", "left", "left"] and which == [0, 1, 0, 1]
    assert [g[2] for g in problem.goals[2:]] == pytest.approx([g[2] + VARIANT_COST for g in problem.goals[:2]])
    assert carry == {"right": "carry-right", "left": "carry-left"} and problem.side(2) == "left"


def test_a_handover_offers_the_taking_hand_side_grasps_of_a_lying_loads_top_pinch():
    # HAND_PLAN 9i: a top pinch whose fingers close horizontally gives two side pinches, in along that closing
    # direction either way, the fingers closing vertically; a top pinch closing vertically gives none
    from zeno_skills.skill_jobs.pick import side_variants
    flat = {"kind": "top_pinch", "R": np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, -1.0]]),
            "p": np.zeros(3)}
    out = side_variants([flat, {"kind": "rim_pinch", "R": np.eye(3), "p": np.zeros(3)}])
    assert [g["kind"] for g in out] == ["side_pinch", "side_pinch"]
    for g in out:
        R = np.asarray(g["R"])
        assert abs(R[2, 2]) < 1e-9 and abs(abs(R[2, 1]) - 1.0) < 1e-9      # in horizontally, closing vertically
    assert np.allclose(np.asarray(out[0]["R"])[:, 2], -np.asarray(out[1]["R"])[:, 2])   # either way
    upright = {"kind": "top_pinch", "R": np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]]), "p": np.zeros(3)}
    assert side_variants([upright]) == []


def test_a_square_place_turns_the_object_onto_an_axis_from_its_yaw_in_the_hand():
    # HAND_PLAN 9f: the squaring turn is in place's goal set, measured from the hold at the place (not before the pick)
    import math
    from zeno_skills.skill_jobs.place import square_yaws
    for yaw in (0.0, 30.0, -44.0, 135.0, 181.0):
        a = math.radians(yaw) / 2
        turns = square_yaws((math.cos(a), 0.0, 0.0, math.sin(a)))
        for k in turns:
            after = (yaw + k) % 90.0
            assert min(after, 90.0 - after) < 1e-6, (yaw, k)
        assert len(set(round((yaw + k) % 360.0, 3) for k in turns)) == 4          # the four axes
