"""Layer 5 (docs/MOTION_ARCHITECTURE.md 2.3): the catalog is what runs -- the job builds with the
catalog's template, the park search takes the catalog's postures -- and a park close enough not to
drive to has its plan made again where the base stands."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import motion_skills as MS
from zeno_skills import skill_plans
from zeno_skills.motion_skills import Job, Skill
from zeno_skills.motion_state import Hand, Plan, Segment, Spec, State
from zeno_skills.park_search import Found, Problem


def _rig(held=None, base=(0.0, 0.0, 0.0)):
    return SimpleNamespace(kin=SimpleNamespace(rest=np.full(9, 0.2), side="right"), q_cmd=np.full(9, 0.7),
                           held=held, world=None, log=lambda *a, **k: None, base_pose=lambda: base)


def _state(rig):
    return State(base=tuple(rig.base_pose()), q_right=rig.q_cmd.copy(), q_left=np.zeros(7),
                 hands={"right": Hand(0.0)})


def _skill(job, arrive="fold", travel="fold"):
    return Skill("pick", "pick_place", "plan_pick", True, arrive, travel, job)


def test_a_skill_builds_with_the_template_its_catalog_entry_names():
    skills = MS.load()
    assert skills["pick"].build is skill_plans.plan_pick and skills["place"].build is skill_plans.plan_place
    assert skills["navigate"].build is skill_plans.plan_navigate


def test_the_catalog_postures_are_the_park_searchs(monkeypatch):
    rig, seen = _rig(), {}
    plan = Plan((Segment("a", Spec(), rig.q_cmd, kind="anchor"),))

    def job(rig_, args, state, skill):
        assert skill.build is skill_plans.plan_pick
        return Job(problem=Problem(goals=(), build=lambda *a: plan), ready=lambda f: (plan, None, {}))

    def find_park(kin, world, problem, state, log, base=None):
        seen["travel"], seen["arrive_far"] = problem.travel, problem.arrive(5.0, 5.0, 0.0)
        seen["arrive_here"] = problem.arrive(0.0, 0.0, 0.0)
        return Found(0.0, 0.0, 0.0, 0, plan), {}
    monkeypatch.setattr(MS, "find_park", find_park)
    monkeypatch.setattr(MS, "observe", _state)
    monkeypatch.setattr(MS, "run", lambda *a, **k: [])
    monkeypatch.setattr("zeno_skills.skill_jobs.base.RigBase", lambda rig: None)
    MS.run_skill(rig, _skill(job), {})
    assert np.allclose(seen["travel"], rig.kin.rest) and np.allclose(seen["arrive_far"], rig.kin.rest)
    assert np.allclose(seen["arrive_here"], rig.q_cmd)                # no drive: the arm as it stands
    with pytest.raises(ValueError, match="nothing in the hand"):
        MS.posture(rig, "carry")
    rig.held = {"name": "cup"}
    assert np.allclose(MS.posture(rig, "fold_or_carry"), rig.q_cmd)


def test_a_park_too_close_to_drive_to_has_its_plan_made_again_where_the_base_stands(monkeypatch):
    rig = _rig(base=(0.005, 0.0, 0.5))                                 # 5 mm, half a degree off the park
    old = Plan((Segment("old", Spec(), rig.q_cmd, kind="anchor"),))
    new = Plan((Segment("new", Spec(), rig.q_cmd, kind="anchor"),))
    built, ran = [], []

    def job(rig_, args, state, skill):
        def build(s, k, q_rank):
            built.append(tuple(s.base))
            return new
        return Job(problem=Problem(goals=(), build=build), ready=lambda f: (f.plan, None, {}))
    monkeypatch.setattr(MS, "find_park", lambda *a, **k: (Found(0.0, 0.0, 0.0, 0, old), {}))
    monkeypatch.setattr(MS, "observe", _state)
    monkeypatch.setattr(MS, "run", lambda rig_, plan, build, hooks, clear=None: ran.append(plan))
    monkeypatch.setattr("zeno_skills.skill_jobs.base.RigBase", lambda rig: None)
    MS.run_skill(rig, _skill(job), {})
    assert built == [(0.005, 0.0, 0.5)] and ran == [new]


def test_a_pick_behind_a_door_is_seeded_in_front_of_its_free_edge_from_the_annotation():
    from zeno_skills.skill_jobs.pick import _behind_door, _front_of
    door = {"name": "fridge", "type": "revolute", "closed_q": 0.0, "pivot": [5.615, 3.003, 0.69],
            "part_frame": np.eye(4).tolist(), "part_box": [[0.0, -0.1075, -0.62], [0.57, 0.0175, 0.62]],
            "handle": {"center": [6.13, 2.908, 0.74], "outward": [0.0, -1.0, 0.0]}}
    door["part_frame"][0][3], door["part_frame"][1][3], door["part_frame"][2][3] = 5.615, 3.003, 0.69
    ann = SimpleNamespace(articulated=[door], part_pose=lambda a, q: np.asarray(a["part_frame"], float))
    rig = SimpleNamespace(ann=ann)
    assert _behind_door(rig, {"support": "fridge/inside_shelf"}, (5.9, 3.3, 0.85)) is door
    assert _behind_door(rig, {"support": "fridge/top"}, (5.9, 3.3, 1.4)) is None          # on it, not in it
    x, y, yaw = _front_of(rig, door, (5.9, 3.3, 0.85))
    # the hand-placed seed it replaces: (6.246, 2.337, 135)
    assert abs(x - 6.246) < 0.1 and abs(y - 2.337) < 0.1 and abs(yaw - 135.0) < 3.0
