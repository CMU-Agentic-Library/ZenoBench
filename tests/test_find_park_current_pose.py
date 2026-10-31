"""find_park: the current base pose competes with the other parks instead of being kept whenever it works."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import planner

TARGETS = [(np.array([1.0, 0.0, 0.9]), np.eye(3))]
HERE = (0.5, 0.0, 0.0)          # 0.5 m from the target, facing it


@pytest.fixture
def fake(monkeypatch):
    monkeypatch.setattr(planner, "_ik_sequence", lambda kin, targets, q0=None: [np.zeros(9)])
    monkeypatch.setattr(planner, "plan_path", lambda world, a, b: [a, b])
    kin = SimpleNamespace(set_base=lambda *a: None, coll_kw={})
    world = SimpleNamespace(footprint_clear=lambda x, y, yaw, **k: True)
    return kin, world


def test_a_clearly_better_park_beats_the_current_pose(fake, monkeypatch):
    kin, world = fake
    calls = []

    def quality(kin_, qs, targets):
        calls.append(1)
        # the first evaluated park is the current pose: joints at a limit, low manipulability
        return ({"margin": 0.0, "manip": 0.2, "clear": 0.02} if len(calls) == 1
                else {"margin": 0.5, "manip": 1.0, "clear": 0.10})
    monkeypatch.setattr(planner, "park_quality", quality)
    park = planner.find_park(kin, world, TARGETS, near=HERE, max_tries=50)
    assert park is not None and (park[0], park[1]) != HERE[:2]


def test_an_equally_good_current_pose_is_kept(fake, monkeypatch):
    kin, world = fake
    monkeypatch.setattr(planner, "park_quality", lambda k, qs, t: {"margin": 0.5, "manip": 1.0, "clear": 0.10})
    park = planner.find_park(kin, world, TARGETS, near=HERE, max_tries=50)
    assert (park[0], park[1], park[2]) == HERE


def test_one_try_probes_only_the_given_pose(fake, monkeypatch):
    kin, world = fake
    monkeypatch.setattr(planner, "park_quality", lambda k, qs, t: pytest.fail("a probe ranks nothing"))
    park = planner.find_park(kin, world, TARGETS, near=HERE, max_tries=1)
    assert (park[0], park[1], park[2]) == HERE


def test_a_skill_score_also_compares_the_current_pose(fake):
    kin, world = fake
    # lowest score wins: the current pose scores worst
    park = planner.find_park(kin, world, TARGETS, near=HERE, max_tries=50, n_best=3,
                             score=lambda x, y, yaw, qs: 1.0 if (x, y) == HERE[:2] else 0.5)
    assert (park[0], park[1]) != HERE[:2]
