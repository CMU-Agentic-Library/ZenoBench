"""The park search (docs/MOTION_ARCHITECTURE.md section 7): candidates around the goals, the cheap
tests, a ranking, then the skill's builder in that order -- the first park whose plan is made wins."""

import math
from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import park_search as PS
from zeno_skills import skills
from zeno_skills.motion_state import Failure, Hand, Plan, State, chains


class Kin:
    side = "right"
    motion = None

    def __init__(self):
        self.scene, self.lo, self.hi = object(), np.full(9, -3.0), np.full(9, 3.0)
        self.base_p, self.base_R = np.zeros(3), np.eye(3)
        self.asked = []

    def set_base(self, xyz, yaw):
        self.base_p = np.asarray(xyz, float)
        self.base_R = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])

    def ik_set(self, goals, q0, weights=None):
        self.asked.append((self.scene, self.base_p.copy(), [p for p, _ in goals]))
        return [np.r_[p, np.zeros(6)] for p, _ in goals]

    def jac(self, q):
        return np.eye(6, 9), None, None


class Base:
    """motion_state.BaseModel: every park clear in the travel posture and drivable; ``reach`` says
    which the column reaches."""

    def __init__(self, reach=True):
        self.reach = reach

    def depths(self, state, poses):
        return [0.0] * len(poses)

    def reachable(self, state, poses):
        return [self.reach] * len(poses)

    def drivable(self, state, goal):
        return True


def _find(log, problem, state, reach=True):
    return PS.find_park(Kin(), SimpleNamespace(footprint_clear=lambda x, y, yaw: True), problem, state,
                        lambda ev, **kw: log.append((ev, kw)), base=Base(reach))


def _state():
    return State(base=(0.0, 0.0, 0.0), **chains(np.zeros(9), np.zeros(7)), hands={"right": Hand(width=0.04)})


def _problem(build, near=None, prefer=()):
    goal = np.array([1.0, 0.0, 0.8])
    return PS.Problem(goals=(((goal,), (goal, np.eye(3)), 0.0),), build=build, relay="pick_reach",
                      arrive=lambda x, y, yaw: np.zeros(9), travel=np.zeros(9), near=near, prefer=prefer)


def test_the_current_pose_and_the_preferred_ones_come_first():
    cands = PS.candidates(_problem(None, near=(0.2, 0.0, 0.0), prefer=((0.5, 0.5, 90.0),)))
    assert cands[0][1:4] == (0.2, 0.0, 0.0) and cands[1][1:4] == (0.5, 0.5, 90.0)
    assert all(a[0] <= b[0] for a, b in zip(cands[2:], cands[3:]))


def test_the_ranking_ik_takes_the_relay_pose_into_each_parks_base_frame_without_a_world():
    kin = Kin()
    cand = [(0.0, 1.0, 0.0, 90.0, 0)]                         # base at (1, 0) facing +y
    PS.rank_ik(kin, cand, _problem(None), np.zeros(9))
    scene, base, poses = kin.asked[0]
    assert scene is None and np.allclose(base, 0.0)
    assert np.allclose(poses[0], [0.0, 0.0, 0.8])             # the goal (1, 0, 0.8) is straight above the base
    assert kin.scene is not None                              # put back


def test_plans_are_built_in_rank_order_and_the_first_made_wins(monkeypatch):
    log, tried = [], []

    def build(state, k, prior):
        tried.append(state.base)
        return Failure("no straight", "pick_grasp") if len(tried) < 3 else Plan(())
    found, diag = _find(log, _problem(build), _state())
    assert found is not None and diag["built"] == 3 and diag["build_failed"] == {"pick_grasp: no straight": 2}
    assert found.pose == tried[-1] and log[-1][0] == "park_search"


def test_the_ranking_solution_is_the_builds_prior_for_the_relay_decision(monkeypatch):
    priors, rank = [], np.full(9, 0.25)
    monkeypatch.setattr(PS, "rank_ik", lambda kin, pool, problem, q0: [rank] * len(pool))
    found, _ = _find([], _problem(lambda s, k, prior: priors.append(prior) or Plan(())), _state())
    assert found is not None and list(priors[0]) == ["pick_reach"] and priors[0]["pick_reach"] is rank


def test_every_candidate_of_a_lower_tier_is_built_before_any_of_a_higher_one():
    goal = np.array([1.0, 0.0, 0.8])
    ks = []
    # goal 1 (tier 0) costs more than goal 0 (tier 1): the tier, not the cost, decides
    problem = PS.Problem(goals=(((goal,), (goal, np.eye(3)), 0.0), ((goal,), (goal, np.eye(3)), 0.5)),
                         build=lambda s, k, prior: ks.append(k) or Failure("no", "x"),
                         relay="pick_reach", arrive=lambda x, y, yaw: np.zeros(9), travel=np.zeros(9), tiers=(1, 0))
    _find([], problem, _state())
    assert ks and ks == sorted(ks, reverse=True) and ks[0] == 1        # goal 1's candidates first, then goal 0's


def test_where_no_park_reaches_the_relay_the_one_getting_farthest_along_it_is_built_first(monkeypatch):
    start, end = np.array([1.0, 0.0, 0.8]), np.array([1.4, 0.0, 0.8])

    def rank(kin, cands, problem, q0, poses=None):
        if poses is None:                                   # nowhere reaches the end
            return [None] * len(cands)
        # parks on +y get 30 cm along the straight, the others 10 cm
        return [np.r_[p, np.zeros(6)] if p[0] - start[0] <= (0.3 if c[2] > 0 else 0.1) + 1e-9 else None
                for c, (p, _) in zip(cands, poses)]
    monkeypatch.setattr(PS, "rank_ik", rank)
    built = []
    problem = PS.Problem(goals=(((start, end), (end, np.eye(3)), 0.0),),
                         build=lambda s, k, prior: built.append(prior["slide_end"]) or Plan(()),
                         relay="slide_end", arrive=lambda x, y, yaw: np.zeros(9), travel=np.zeros(9),
                         relay_from=(start,), reach_step=0.02)
    found, diag = _find([], problem, _state())
    assert found is not None and found.y > 0                    # a park that gets 30 cm along, whatever its score
    assert 0.3 - 0.02 <= built[0][0] - start[0] <= 0.3          # the build's prior: the farthest point solved
    assert diag["reach"]["least_left"] == pytest.approx(0.1, abs=0.02)


def test_a_relay_some_park_reaches_is_ranked_as_ever(monkeypatch):
    start, end = np.array([1.0, 0.0, 0.8]), np.array([1.4, 0.0, 0.8])
    asked = []

    def rank(kin, cands, problem, q0, poses=None):
        asked.append(poses is None)
        return [np.r_[end, np.zeros(6)] if c[2] > 0 else None for c in cands]
    monkeypatch.setattr(PS, "rank_ik", rank)
    problem = PS.Problem(goals=(((start, end), (end, np.eye(3)), 0.0),), build=lambda s, k, prior: Plan(()),
                         relay="slide_end", arrive=lambda x, y, yaw: np.zeros(9), travel=np.zeros(9),
                         relay_from=(start,), reach_step=0.02)
    found, diag = _find([], problem, _state())
    assert found is not None and found.y > 0 and asked == [True] and "reach" not in diag   # no measuring


def test_the_build_budget_ends_the_search(monkeypatch):
    found, diag = _find([], _problem(lambda s, k, q: Failure("never", "x")), _state())
    assert found is None and (diag["built"] == PS.BUILD_MAX or diag["build_seconds"] >= PS.BUILD_S)


def test_parks_the_base_cannot_drive_to_are_not_built(monkeypatch):
    found, diag = _find([], _problem(lambda s, k, q: Plan(())), _state(), reach=False)
    assert found is None and diag["built"] == 0 and diag["drive"] > 0



def test_the_cheapest_yaw_puts_the_goal_on_the_right_arms_side():
    # yaw = face + off puts the goal at bearing -off: the cost prefers off = +FACE_LEFT (goal on the
    # right, -y, where the right arm is; 89% of the 11-08 grasps were there)
    goal = np.array([2.0, 0.0, 0.8])
    prob = PS.Problem(goals=(((goal,), (goal, np.eye(3)), 0.0),), build=None, relay="pick_reach")
    cost, x, y, yaw, k = PS.candidates(prob)[0]
    face = np.degrees(np.arctan2(goal[1] - y, goal[0] - x))
    bearing = (face - yaw + 180) % 360 - 180
    assert abs(bearing + PS.FACE_LEFT) < 1e-6
