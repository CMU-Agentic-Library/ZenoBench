"""Layer 5 (docs/motion/MOTION_ARCHITECTURE.md 2.3): the catalog is what runs -- the job builds with the
catalog's template, the park search takes the catalog's postures -- and a park close enough not to
drive to has its plan made again where the base stands."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import motion_skills as MS
from zeno_skills import skill_plans
from zeno_skills.motion_skills import Job, Skill
from zeno_skills.motion_state import Hand, Plan, Segment, Spec, State, chains
from zeno_skills.park_search import Found, Problem


def _rig(held=None, base=(0.0, 0.0, 0.0)):
    return SimpleNamespace(kin=SimpleNamespace(rest=np.full(9, 0.2), side="right"), q_cmd=np.full(9, 0.7),
                           held=held, world=None, log=lambda *a, **k: None, base_pose=lambda: base)


def _state(rig):
    return State(base=tuple(rig.base_pose()), **chains(rig.q_cmd.copy(), np.zeros(7)),
                 hands={"right": Hand(0.0)})


def _skill(job, arrive="fold", travel="fold"):
    return Skill("pick", "pick_place", "plan_pick", True, arrive, travel, job)


def test_a_skill_builds_with_the_template_its_catalog_entry_names():
    skills = MS.load()
    assert skills["pick"].build is skill_plans.plan_pick and skills["place"].build is skill_plans.plan_place
    assert skills["navigate"].build is skill_plans.plan_navigate and skills["drop"].build is skill_plans.plan_drop


def test_the_catalog_postures_are_the_park_searchs(monkeypatch):
    rig, seen = _rig(), {}
    plan = Plan((Segment("a", Spec(), rig.q_cmd, kind="anchor"),))

    def job(rig_, args, state, skill):
        assert skill.build is skill_plans.plan_pick
        return Job(problem=Problem(goals=(), build=lambda *a: plan, relay="pick_reach"), ready=lambda f: (plan, None, {}))

    def find_park(kin, world, problem, state, log, base=None):
        seen["travel"], seen["arrive_far"] = problem.travel, problem.arrive(5.0, 5.0, 0.0)
        seen["arrive_here"] = problem.arrive(0.0, 0.0, 0.0)
        return Found(0.0, 0.0, 0.0, 0, plan), {}
    monkeypatch.setattr(MS, "find_park", find_park)
    monkeypatch.setattr(MS, "observe", _state)
    monkeypatch.setattr(MS, "run", lambda *a, **k: [])
    monkeypatch.setattr("zeno_skills.skill_jobs.base.RigBase", lambda rig: None)
    MS.run_skill(rig, _skill(job), {})
    assert np.allclose(seen["travel"].q("right"), rig.kin.rest) and np.allclose(seen["arrive_far"].q("right"), rig.kin.rest)
    assert set(seen["travel"].arms) == {"right"}                      # the right arm's posture: the left as it is
    assert np.allclose(seen["arrive_here"].q("right"), rig.q_cmd)     # no drive: the arm as it stands
    with pytest.raises(ValueError, match="nothing in the right hand"):
        MS.posture(rig, "carry")
    rig.held = {"name": "cup"}
    assert np.allclose(MS.posture(rig, "fold_or_carry").q("right"), rig.q_cmd)


def test_a_park_too_close_to_drive_to_has_its_plan_made_again_where_the_base_stands(monkeypatch):
    rig = _rig(base=(0.005, 0.0, 0.5))                                 # 5 mm, half a degree off the park
    old = Plan((Segment("old", Spec(), rig.q_cmd, kind="anchor"),))
    new = Plan((Segment("new", Spec(), rig.q_cmd, kind="anchor"),))
    built, ran, priors = [], [], []

    def job(rig_, args, state, skill):
        def build(s, k, prior):
            built.append(tuple(s.base))
            priors.append(prior)
            return new
        return Job(problem=Problem(goals=(), build=build, relay="pick_reach"), ready=lambda f: (f.plan, None, {}))
    monkeypatch.setattr(MS, "find_park", lambda *a, **k: (Found(0.0, 0.0, 0.0, 0, old), {}))
    monkeypatch.setattr(MS, "observe", _state)
    monkeypatch.setattr(MS, "run", lambda rig_, plan, build, hooks, clear=None: ran.append(plan))
    monkeypatch.setattr("zeno_skills.skill_jobs.base.RigBase", lambda rig: None)
    MS.run_skill(rig, _skill(job), {})
    assert built == [(0.005, 0.0, 0.5)] and ran == [new]
    assert priors == [old]                                             # the found plan's decisions: the prior


def test_a_skill_plans_with_the_head_straight_ahead(monkeypatch):
    """A look leaves the head where it aimed (T07 11-14: at its 18 deg down limit over the tray it had
    looked at): run_skill turns it straight ahead before it reads the state it plans from, and leaves a
    head already there as it is."""
    rig, head, logs, seen = _rig(), {"head_yaw_joint": 0.3, "head_pitch_joint": 0.314}, [], []

    def aim_head(yaw, pitch, steps=90):                                # the head reaches its command at once
        head["head_yaw_joint"], head["head_pitch_joint"] = float(yaw), float(pitch)
    rig.aim_head, rig.head_q, rig.q = aim_head, lambda: dict(head), lambda: rig.q_cmd
    rig.declare = lambda *a, **k: None
    rig.log = lambda label, **k: logs.append((label, k))
    plan = Plan((Segment("a", Spec(), rig.q_cmd, kind="anchor"),))
    monkeypatch.setattr(MS, "observe", lambda rig_: seen.append(rig_.head_q()) or _state(rig_))
    monkeypatch.setattr(MS, "run", lambda *a, **k: [])
    monkeypatch.setattr("zeno_skills.skill_jobs.base.RigBase", lambda rig: None)
    navigate = Skill("navigate", "drive", "plan_navigate", False, "fold", "fold",
                     lambda rig_, args, state, skill: Job(ready=lambda f: (plan, None, {})))
    MS.run_skill(rig, navigate, {})
    assert seen == [{"head_yaw_joint": 0.0, "head_pitch_joint": 0.0}]
    assert logs == [("head_straight", {"skill": "navigate", "was": [0.3, 0.314]})]
    MS.run_skill(rig, navigate, {})                                    # straight already: not driven again
    assert len(logs) == 1


def test_a_pick_behind_a_door_is_seeded_in_front_of_its_free_edge_from_the_annotation():
    from zeno_skills.annotations import behind_door
    from zeno_skills.skill_jobs.door_access import front_of
    door = {"name": "fridge", "type": "revolute", "closed_q": 0.0, "pivot": [5.615, 3.003, 0.69],
            "part_frame": np.eye(4).tolist(), "part_box": [[0.0, -0.1075, -0.62], [0.57, 0.0175, 0.62]],
            "handle": {"center": [6.13, 2.908, 0.74], "outward": [0.0, -1.0, 0.0]}}
    door["part_frame"][0][3], door["part_frame"][1][3], door["part_frame"][2][3] = 5.615, 3.003, 0.69
    ann = SimpleNamespace(articulated=[door], part_pose=lambda a, q: np.asarray(a["part_frame"], float))
    rig = SimpleNamespace(ann=ann)
    shelf = {"name": "fridge/inside_shelf", "furniture": "fridge", "category": "cabinet_inside"}
    top = {"name": "fridge/top", "furniture": "fridge", "category": "cabinet_top"}
    assert behind_door(ann, shelf, (5.9, 3.3, 0.85)) is door
    assert behind_door(ann, top, (5.9, 3.3, 1.4)) is None                     # on it, not in it
    x, y, yaw = front_of(rig, door, (5.9, 3.3, 0.85))
    # the hand-placed seed it replaces: (6.246, 2.337, 135)
    assert abs(x - 6.246) < 0.1 and abs(y - 2.337) < 0.1 and abs(yaw - 135.0) < 3.0
