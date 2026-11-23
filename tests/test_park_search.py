"""The park search (docs/motion/MOTION_ARCHITECTURE.md section 7): candidates around the goals, the cheap
tests, a ranking, then the skill's builder in that order -- the first park whose plan is made wins."""

import math
from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import park_search as PS
from zeno_skills import skills
from zeno_skills.motion_state import Failure, Hand, Plan, Spec, State, chains


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
    return PS.find_park(Kin(), SimpleNamespace(footprints_clear=lambda poses: np.ones(len(poses), bool)), problem, state,
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


def test_behind_a_door_the_parks_whose_ranking_solution_is_free_are_built_first():
    # the ranking solution carries the goal in the park's frame (Kin.ik_set): "free" at about half the
    # parks (by that), the others put a forearm through a door the ranking cannot see
    kin, built = Kin(), []
    ok = lambda q: int(round(float(q[0]) * 1000)) % 2 == 0     # noqa: E731
    kin.free = ok
    goal = np.array([1.0, 0.0, 0.8])
    problem = PS.Problem(goals=(((goal,), (goal, np.eye(3)), 0.0),),
                         build=lambda s, k, prior: built.append(ok(prior["pick_reach"])) or Failure("no", "x"),
                         relay="pick_reach", arrive=lambda x, y, yaw: np.zeros(9), travel=np.zeros(9),
                         relay_free=Spec())
    _, diag = PS.find_park(kin, SimpleNamespace(footprints_clear=lambda poses: np.ones(len(poses), bool)), problem, _state(),
                           lambda ev, **kw: None, base=Base())
    n_free = diag["relay_free"][1]
    assert 0 < n_free < diag["relay_free"][0]
    assert built[:min(n_free, len(built))] == [True] * min(n_free, len(built))   # the free ones first
    assert diag["built"] == len(built)


def test_without_relay_free_the_order_is_the_rankings():
    kin = Kin()
    kin.free = lambda q: (_ for _ in ()).throw(AssertionError("checked"))
    found, diag = PS.find_park(kin, SimpleNamespace(footprints_clear=lambda poses: np.ones(len(poses), bool)),
                               _problem(lambda s, k, prior: Plan(())), _state(), lambda ev, **kw: None, base=Base())
    assert found is not None and "relay_free" not in diag


def test_a_search_records_its_candidates_only_when_asked(monkeypatch, tmp_path):
    monkeypatch.setenv("ZB_PARK_DUMP", str(tmp_path))
    monkeypatch.setenv("ZB_PARK_DUMP_MATCH", "park")
    built = []
    found, _ = _find([], _problem(lambda s, k, prior: built.append(1) or (Plan(()) if len(built) > 1 else
                                                                          Failure("no", "x"))), _state())
    rec = [__import__("json").loads(p.read_text()) for p in tmp_path.glob("*.json")]
    assert len(rec) == 1 and rec[0]["found"][:3] == [found.x, found.y, found.yaw]
    assert len(rec[0]["built"]) == 2 and rec[0]["built"][0][4].startswith("x: no") and rec[0]["ranked"]
    monkeypatch.setenv("ZB_PARK_DUMP_MATCH", "place")                    # another label: nothing written
    _find([], _problem(lambda s, k, prior: Plan(())), _state())
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_the_batched_footprint_keeps_the_one_candidate_at_a_time_result(monkeypatch):
    # the footprint is tested FOOTPRINT_CHUNK candidates per call; the pool, the counts and the park must be
    # the ones a test per candidate (chunk 1, as before 11-23) gives
    world = SimpleNamespace(footprints_clear=lambda poses: (np.floor(np.asarray(poses)[:, 0] * 37) % 3) != 0)
    goal = np.array([1.0, 0.0, 0.8])
    problem = PS.Problem(goals=(((goal,), (goal, np.eye(3)), 0.0), ((goal + [0.3, 0.2, 0.0],), (goal, np.eye(3)), 0.1)),
                         build=lambda s, k, relay: Plan(()), relay="pick_reach", arrive=lambda x, y, yaw: np.zeros(9),
                         travel=np.zeros(9), near=(0.2, 0.0, 0.0))
    runs = []
    for chunk in (1, PS.FOOTPRINT_CHUNK):
        monkeypatch.setattr(PS, "FOOTPRINT_CHUNK", chunk)
        found, diag = PS.find_park(Kin(), world, problem, _state(), lambda ev, **kw: None, base=Base())
        runs.append(((found.x, found.y, found.yaw, found.k), {k: diag[k] for k in ("out_of_reach", "footprint", "pool")}))
    assert runs[0] == runs[1]
    assert runs[0][1]["footprint"] > 0
