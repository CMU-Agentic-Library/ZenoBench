"""search and explore_room bookkeeping (policies/perceive.py), simulator-free: what counts as visited, what the
failure says, which viewpoints an exploration drives to."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import evaluator, perception
from zeno_skills.policies import base_motion as BM
from zeno_skills.policies import perceive as PC
from zeno_skills.rig import SkillFailure


def _support(name, furniture, x):
    return {"name": name, "furniture": furniture, "aabb_xy": [x, 0.0, x + 0.4, 0.4], "z": 0.8}


def _search_rig(supports):
    ann = SimpleNamespace(supports=supports, rooms={})
    pose = [0.0, 0.0, 0.0]
    return SimpleNamespace(ann=ann, base_pose=lambda: tuple(pose), log=lambda *a, **k: None, tick=0,
                           memory={}, state=lambda: {}, _pose=pose,
                           geo=SimpleNamespace(centre=lambda n, st: np.array([9.0, 9.0, 9.0]),
                                               support_under=lambda n, st: None))


@pytest.fixture
def search(monkeypatch):
    """Patch the simulator out of search: navigate goes or raises per furniture, an aim point is in view per
    furniture, the object is seen at one furniture or none."""
    cfg = {"unreachable": set(), "unviewable": set(), "found_at": None, "at": None}

    class Nav:
        def __init__(self, rig):
            self.rig = rig

        def execute(self, place):
            f = place.split("/")[0]
            if f in cfg["unreachable"]:
                raise SkillFailure(f"navigate to {place}: no base path")
            cfg["at"] = f

    monkeypatch.setattr(BM, "NavigateToPlacePolicy", Nav)
    monkeypatch.setattr(evaluator, "room_of", lambda rooms, xy: "room")
    monkeypatch.setattr(PC, "drive_head", lambda *a, **k: None)
    monkeypatch.setattr(PC, "record_view", lambda rig: [])
    monkeypatch.setattr(PC, "look_angles", lambda rig, p: (0.0, 0.0))
    monkeypatch.setattr(PC, "rig_head_pose", lambda rig: (np.zeros(3), np.eye(3)))
    monkeypatch.setattr(perception, "project_from",
                        lambda rig, cam, R, p: (cfg["at"] not in cfg["unviewable"], ""))
    monkeypatch.setattr(PC, "project_to_head_camera",
                        lambda rig, p, exclude=None: (cfg["at"] == cfg["found_at"], ""))
    monkeypatch.setattr(PC, "memory", lambda rig: rig.memory.setdefault("m", {"observed": {}}))
    return cfg


SUPPORTS = [_support("a/top", "a", 1.0), _support("b/top", "b", 2.0), _support("c/top", "c", 3.0)]


def test_found_reports_the_furniture_visited_in_order(search):
    search["found_at"] = "b"
    out = PC.SearchObjectPolicy(_search_rig(SUPPORTS)).execute("cup")
    assert out["visited"] == ["a", "b"]


def test_a_furniture_not_in_view_from_the_stand_off_is_not_visited(search):
    """1116: search stood behind the wall from bookcase_2 and listed it as visited ('not seen at
    ['bookcase_2', ...]') although no point of it was in the head camera."""
    search["unviewable"] = {"a"}
    search["unreachable"] = {"c"}
    with pytest.raises(SkillFailure) as exc:
        PC.SearchObjectPolicy(_search_rig(SUPPORTS)).execute("cup")
    msg = str(exc.value)
    assert msg.startswith("search cup: not seen at ['b']")
    assert "not in view from where the base stood: ['a']" in msg
    assert "no base path to: ['c']" in msg


def test_everything_seen_and_nothing_found_keeps_the_old_text(search):
    with pytest.raises(SkillFailure) as exc:
        PC.SearchObjectPolicy(_search_rig(SUPPORTS)).execute("cup")
    assert str(exc.value) == "search cup: not seen at ['a', 'b', 'c']"
