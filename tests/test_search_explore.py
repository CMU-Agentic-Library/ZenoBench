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


def _explore_rig(held=None):
    ann = SimpleNamespace(objects={}, articulated=[], appliances=[], rooms={"room": {}},
                          supports=[{"name": "t/top", "furniture": "t", "aabb_xy": [1.0, 1.0, 1.5, 1.5], "z": 0.7}])
    return SimpleNamespace(ann=ann, base_pose=lambda: (0.0, 0.0, 0.0), log=lambda *a, **k: None, memory={},
                           state=lambda: {}, static_explore=True, held=held)


@pytest.fixture
def explore(monkeypatch):
    went = []
    cfg = {"poses": [(0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (0.0, 3.0, 0.0), (3.0, 3.0, 0.0)], "ok": None}
    monkeypatch.setattr(evaluator, "room_of", lambda rooms, xy: "room")
    monkeypatch.setattr(BM, "standoff_poses", lambda rig, place: list(cfg["poses"]))
    monkeypatch.setattr(BM.skills, "base_reachable", lambda rig, ps: cfg["ok"] or [True] * len(ps))
    monkeypatch.setattr(BM.skills, "navigate", lambda rig, pose, **kw: went.append(pose))
    monkeypatch.setattr(BM.skills, "straight_base_move", lambda *a, **k: None)
    monkeypatch.setattr(PC, "drive_head", lambda *a, **k: None)
    monkeypatch.setattr(PC, "record_view", lambda rig: [])
    monkeypatch.setattr(PC, "project_to_head_camera", lambda rig, p, exclude=None: (True, ""))
    monkeypatch.setattr(PC, "memory", lambda rig: rig.memory.setdefault("m", {"explored": {}}))
    cfg["went"] = went
    return cfg


def test_explore_drives_only_to_viewpoints_the_base_can_get_to(explore):
    """1116 T26 two_bedrooms: the 5 viewpoints were picked from every free pose and the base could get to
    none of them (coverage 0); the field over all of them comes first now."""
    explore["ok"] = [True, False, True, False]
    out = PC.ExploreRoomPolicy(_explore_rig()).execute("room", min_spacing=0.5)
    assert out["coverage"] == 1.0
    assert set(explore["went"]) == {(0.0, 0.0, 0.0), (0.0, 3.0, 0.0)}


def test_explore_with_no_reachable_viewpoint_says_so(explore):
    explore["ok"] = [False] * 4
    with pytest.raises(SkillFailure, match="no base path to any of 4 viewpoints"):
        PC.ExploreRoomPolicy(_explore_rig()).execute("room")
    assert explore["went"] == []


def test_explore_carrying_takes_the_carry_posture_before_the_viewpoints(explore, monkeypatch):
    from zeno_skills.skill_jobs import carry
    order = []
    monkeypatch.setattr(carry, "carry_posture", lambda rig, min_bottom_z=None: order.append("carry"))
    monkeypatch.setattr(BM, "standoff_poses", lambda rig, place: order.append("poses") or list(explore["poses"]))
    PC.ExploreRoomPolicy(_explore_rig(held={"name": "living_car"})).execute("room", min_spacing=0.5)
    assert order[:2] == ["carry", "poses"]


def _furniture_rig(near=False):
    layers = [{"name": "shelf/top", "furniture": "shelf", "aabb_xy": [1.0, 1.0, 1.5, 1.5], "z": 1.0},
              {"name": "shelf/shelf_0", "furniture": "shelf", "aabb_xy": [1.0, 1.0, 1.5, 1.5], "z": 0.5}]
    ann = SimpleNamespace(objects={}, articulated=[], appliances=[], rooms={}, supports=layers)
    pose = (0.0, 0.0, 0.0) if not near else (1.2, 0.8, 90.0)
    return SimpleNamespace(ann=ann, base_pose=lambda: pose, log=lambda *a, **k: None, memory={}, held=None,
                           state=lambda: {})


def test_explore_furniture_drives_only_to_reachable_stand_offs_it_is_in_view_from(monkeypatch):
    """The hand-written wall test (head straight ahead, every layer behind a wall) is the in-view goal set of
    navigate_place now; unreachable stand-offs are not tried either."""
    went, seen_from = [], {(2.0, 0.0, 0.0)}
    poses = [(0.5, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (3.0, 0.0, 0.0)]
    monkeypatch.setattr(BM, "standoff_poses", lambda rig, place: list(poses))
    monkeypatch.setattr(BM.skills, "base_reachable", lambda rig, ps: [p != (1.0, 0.0, 0.0) for p in ps])
    monkeypatch.setattr(BM, "_in_view_poses", lambda rig, place, ps: [p for p in ps if p in seen_from])
    monkeypatch.setattr(BM.skills, "navigate", lambda rig, pose, **kw: went.append(pose))
    monkeypatch.setattr(BM, "entity_footprint", lambda rig, name: [1.0, 1.0, 1.5, 1.5])
    monkeypatch.setattr(PC, "entity_footprint", lambda rig, name: [1.0, 1.0, 1.5, 1.5])
    monkeypatch.setattr(PC, "drive_head", lambda *a, **k: None)
    monkeypatch.setattr(PC, "record_view", lambda rig: [])
    monkeypatch.setattr(PC, "look_angles", lambda rig, p: (0.0, 0.0))
    monkeypatch.setattr(PC, "rig_head_pose", lambda rig: (np.zeros(3), np.eye(3)))
    monkeypatch.setattr(PC, "project_to_head_camera", lambda rig, p, exclude=None: (bool(went), ""))
    monkeypatch.setattr(PC, "_board_blocks", lambda cam, q, layers: False)
    monkeypatch.setattr(PC, "memory", lambda rig: rig.memory.setdefault("m", {"explored": {}}))
    out = PC.ExploreFurniturePolicy(_furniture_rig()).execute("shelf")
    assert went == [(2.0, 0.0, 0.0)]
    assert out["layers"] == ["shelf/shelf_0", "shelf/top"]


def test_the_head_moves_through_the_actuator_as_a_segment():
    """drive_head is a head action segment run by run.execute (Actuator.aim_head), not a write to the rig; it
    declares nothing to the contact monitor (the arms, base and hands do not move)."""
    calls = []
    act = SimpleNamespace(q=lambda: np.zeros(9), aim_head=lambda *a: calls.append(("head", *a)),
                          declare=lambda *a, **k: calls.append(("declare",)))
    seg = PC.head_segment(act, 0.3, -0.1, steps=60)
    assert seg.kind == "action" and seg.action == ("head", 0.3, -0.1, 60)
    PC.drive_head(act, 0.3, -0.1, steps=60)
    assert calls == [("head", 0.3, -0.1, 60)]


def test_a_room_reached_only_in_a_corner_is_explored_from_its_furniture_stand_offs(explore, monkeypatch):
    """1116 T26 two_bedrooms: bedroom_0_0's ring spots all lie where the base cannot get (59 of 1780 free
    cells reachable, by the door); the stand-offs of its furniture the base gets to and sees it from are the
    viewpoints then."""
    spots, corner = list(explore["poses"]), [(9.0, 0.0, 0.0), (9.0, 1.0, 0.0)]
    monkeypatch.setattr(BM, "standoff_poses", lambda rig, place: list(spots if place == "room" else corner))
    monkeypatch.setattr(BM.skills, "base_reachable", lambda rig, ps: [p in corner[:1] for p in ps])
    monkeypatch.setattr(BM, "_in_view_poses", lambda rig, place, ps: list(ps))
    out = PC.ExploreRoomPolicy(_explore_rig()).execute("room")
    assert explore["went"] == [corner[0]] and out["coverage"] == 1.0


def test_from_the_furniture_stand_offs_each_unseen_piece_gets_its_own_view(explore, monkeypatch):
    """Spread viewpoints left 3 of bedroom_0_0's 8 targets unseen (coverage 0.62): from the furniture's
    stand-offs, the nearest one of a piece not seen yet, each time."""
    ann = SimpleNamespace(objects={}, articulated=[], appliances=[], rooms={"room": {}},
                          supports=[{"name": "a/top", "furniture": "a", "aabb_xy": [1.0, 1.0, 1.5, 1.5], "z": 0.7},
                                    {"name": "b/top", "furniture": "b", "aabb_xy": [5.0, 1.0, 5.5, 1.5], "z": 0.7}])
    at = [None]
    rig = SimpleNamespace(ann=ann, base_pose=lambda: at[0] or (0.0, 0.0, 0.0), log=lambda *a, **k: None,
                          memory={}, state=lambda: {}, static_explore=True, held=None)
    stand = {"a": [(1.2, 0.5, 90.0), (1.4, 0.5, 90.0)], "b": [(5.2, 0.5, 90.0)]}
    monkeypatch.setattr(BM, "standoff_poses", lambda r, place: list(stand.get(place, [(9.0, 9.0, 0.0)])))
    monkeypatch.setattr(BM.skills, "base_reachable", lambda r, ps: [p[1] < 1.0 for p in ps])
    monkeypatch.setattr(BM, "_in_view_poses", lambda r, place, ps: list(ps))
    went = explore["went"]
    monkeypatch.setattr(BM.skills, "navigate", lambda r, pose, **kw: (went.append(pose), at.__setitem__(0, pose)))
    monkeypatch.setattr(PC, "project_to_head_camera",
                        lambda r, p, exclude=None: (abs(p[0] - (at[0] or (99,))[0]) < 1.0, ""))
    out = PC.ExploreRoomPolicy(rig).execute("room")
    assert went == [(1.2, 0.5, 90.0), (5.2, 0.5, 90.0)] and out["coverage"] == 1.0
