"""search, explore_room and explore_furniture (policies/perceive.py), simulator-free: the task layer on the look
skill -- where they decide to stand (one goal set, decided first), that a failed drive fails them (no next
pose), what counts as seen and what the failure says -- and look's plan (skill_plans/look.py)."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import evaluator, perception
from zeno_skills.motion_state import Failure, Plan, Segment, Spec
from zeno_skills.policies import base_motion as BM
from zeno_skills.policies import perceive as PC
from zeno_skills.rig import SkillFailure
from zeno_skills.skill_plans import look as LK


# ------------------------------------------------------------------ stand-ins
class World:
    """Where the robot stands, what it drove to, the looks it ran; ``sees(pose, point) -> bool``."""

    def __init__(self, sees=lambda pose, p: True, fail_at=()):
        self.pose, self.went, self.looks, self.sees, self.fail_at = (0.0, 0.0, 0.0), [], [], sees, set(fail_at)
        self.aim = None

    def navigate(self, rig, pose, **kw):
        if tuple(pose) in self.fail_at:
            raise SkillFailure(f"navigate {pose}: no base path")
        self.went.append(tuple(pose))
        self.pose = tuple(pose)

    def look(self, rig, aims, face=None, label="look", on_view=None):
        self.looks.append((label, list(aims), face))
        if face is not None:
            self.pose = (self.pose[0], self.pose[1], face)
        for a in aims:
            self.aim = np.asarray(a[2], float) if a[0] == "point" else None
            if on_view is not None:
                on_view(rig, a[1] if a[0] == "point" else None)

    def visible(self, p):
        """In the camera now: the head aimed at it (a point aim), from where the robot stands."""
        return self.aim is not None and np.allclose(self.aim, p) and self.sees(self.pose, p)


def _patch(monkeypatch, w, poses, reachable=lambda p: True, in_view=lambda place, p: True):
    monkeypatch.setattr(evaluator, "room_of", lambda rooms, xy: "room")
    monkeypatch.setattr(BM, "standoff_poses", lambda rig, place: list(poses.get(place, [])))
    monkeypatch.setattr(BM.skills, "base_reachable", lambda rig, ps: [reachable(p) for p in ps])
    monkeypatch.setattr(BM, "_in_view_poses", lambda rig, place, ps: [p for p in ps if in_view(place, p)])
    monkeypatch.setattr(BM.skills, "navigate", w.navigate)
    monkeypatch.setattr(PC, "look", w.look)
    monkeypatch.setattr(PC, "record_view", lambda rig: [])
    monkeypatch.setattr(PC, "memory", lambda rig: rig.memory.setdefault("m", {"observed": {}, "explored": {}}))
    monkeypatch.setattr(PC, "rig_head_pose", lambda rig: (np.zeros(3), np.eye(3)))
    monkeypatch.setattr(PC, "project_to_head_camera", lambda rig, p, exclude=None: (w.visible(p), ""))
    monkeypatch.setattr(perception, "project_from", lambda rig, cam, R, p: (w.visible(p), ""))


def _rig(supports, objects=(), held=None, static=True):
    ann = SimpleNamespace(supports=supports, rooms={"room": {}}, objects={n: {} for n in objects}, articulated=[],
                          appliances=[])
    centres = {n: np.array(c, float) for n, c in dict(objects).items()} if objects else {}
    w = SimpleNamespace(ann=ann, log=lambda *a, **k: None, tick=0, memory={}, state=lambda: {}, held=held,
                        static_explore=static, caption="")
    w.geo = SimpleNamespace(centre=lambda n, st: centres.get(n, np.array([99.0, 99.0, 99.0])),
                            support_under=lambda n, st: None)
    return w


def _support(name, furniture, x, z=0.8):
    return {"name": name, "furniture": furniture, "aabb_xy": [x, 0.0, x + 0.4, 0.4], "z": z}


# ------------------------------------------------------------------ search
SUPPORTS = [_support("a/top", "a", 1.0), _support("b/top", "b", 2.0), _support("c/top", "c", 3.0)]
STAND = {"a": [(1.2, -0.6, 90.0)], "b": [(2.2, -0.6, 90.0)], "c": [(3.2, -0.6, 90.0)]}


def _search(monkeypatch, w, rig, **kw):
    _patch(monkeypatch, w, STAND, **kw)
    rig.base_pose = lambda: w.pose
    return PC.SearchObjectPolicy(rig).execute("cup")


def test_search_reports_the_furniture_visited_in_order(monkeypatch):
    w = World()
    rig = _rig(SUPPORTS, objects={"cup": (2.2, 0.2, 0.8)})
    w.sees = lambda pose, p: True
    rig.geo.centre = lambda n, st: np.array([2.2, 0.2, 0.8])
    PC_vis = w.visible
    w.visible = lambda p: PC_vis(p) or (w.pose == STAND["b"][0] and np.allclose(p, [2.2, 0.2, 0.8]))
    out = _search(monkeypatch, w, rig)
    assert out["visited"] == ["a", "b"] and w.went == [STAND["a"][0], STAND["b"][0]]


def test_search_names_what_it_could_not_see_or_reach(monkeypatch):
    """1116: search stood behind the wall from bookcase_2 and listed it as visited; now a piece seen from no
    reachable stand-off is not driven to, and one not in the camera from its stand-off is not visited."""
    w = World(sees=lambda pose, p: pose != STAND["a"][0])
    with pytest.raises(SkillFailure) as exc:
        _search(monkeypatch, w, _rig(SUPPORTS), reachable=lambda p: p != STAND["c"][0])
    msg = str(exc.value)
    assert msg.startswith("search cup: not seen at ['b']")
    assert "not in view from where the base stood: ['a']" in msg
    assert "no stand-off the base can get to sees: ['c']" in msg
    assert STAND["c"][0] not in w.went


def test_a_drive_that_fails_fails_the_search(monkeypatch):
    w = World(fail_at=[STAND["a"][0]])
    with pytest.raises(SkillFailure, match="no base path"):
        _search(monkeypatch, w, _rig(SUPPORTS))
    assert w.went == []                                    # not on to the next piece


# ------------------------------------------------------------------ explore_room
def _explore(monkeypatch, w, rig, poses, predicted, **kw):
    _patch(monkeypatch, w, poses, **kw)
    rig.base_pose = lambda: w.pose
    monkeypatch.setattr(PC, "_travel_tw", lambda rig: {})
    monkeypatch.setattr(PC, "_predicted", lambda rig, pose, targets, tw:
                        {k: targets[k][0][0] for k in predicted.get(pose, ()) if k in targets})
    return PC.ExploreRoomPolicy(rig).execute("room")


ROOM_SUPPORTS = [_support("a/top", "a", 1.0), _support("b/top", "b", 5.0), _support("c/top", "c", 9.0)]


def test_explore_picks_the_fewest_viewpoints_that_cover_the_room(monkeypatch):
    spots = [(0.0, 1.0, 0.0), (5.0, 1.0, 0.0), (9.0, 1.0, 0.0)]
    pred = {spots[0]: ["furniture:a"], spots[1]: ["furniture:a", "furniture:b", "furniture:c"],
            spots[2]: ["furniture:c"]}
    w = World()
    out = _explore(monkeypatch, w, _rig(ROOM_SUPPORTS), {"room": spots}, pred)
    assert w.went == [spots[1]] and out["coverage"] == 1.0
    labels = [lb for lb, _, _ in w.looks]
    assert any("back" in lb for lb in labels)              # the look the other way (VIEW_TURNS)


def test_a_room_reached_only_by_its_door_is_explored_from_its_furniture_stand_offs(monkeypatch):
    """1116 T26 two_bedrooms: the base gets into bedroom_0_0 only by its door (59 of 1780 free cells), where no
    ring spot lies; the furniture's stand-offs are in the same goal set."""
    spots = [(0.0, 1.0, 0.0), (5.0, 1.0, 0.0)]
    fa, fb, fc = (1.2, -0.6, 90.0), (5.2, -0.6, 90.0), (9.2, -0.6, 90.0)
    pred = {fa: ["furniture:a"], fb: ["furniture:b"], fc: ["furniture:c"], spots[0]: ["furniture:a", "furniture:b"]}
    w = World()
    out = _explore(monkeypatch, w, _rig(ROOM_SUPPORTS), {"room": spots, "a": [fa], "b": [fb], "c": [fc]}, pred,
                   reachable=lambda p: p not in spots)
    assert set(w.went) == {fa, fb, fc} and out["coverage"] == 1.0


def test_explore_aims_at_the_targets_a_viewpoint_was_chosen_for(monkeypatch):
    spot = (5.0, 1.0, 0.0)
    w = World()
    _explore(monkeypatch, w, _rig(ROOM_SUPPORTS), {"room": [spot]},
             {spot: ["furniture:a", "furniture:b", "furniture:c"]})
    first = w.looks[0][1]
    assert [a[1] for a in first if a[0] == "point"] == ["furniture:a", "furniture:b", "furniture:c"]


def test_a_drive_that_fails_fails_the_exploration(monkeypatch):
    spots = [(0.0, 1.0, 0.0), (9.0, 1.0, 0.0)]
    pred = {spots[0]: ["furniture:a", "furniture:b"], spots[1]: ["furniture:c"]}
    w = World(fail_at=[spots[0]])
    with pytest.raises(SkillFailure, match="no base path"):
        _explore(monkeypatch, w, _rig(ROOM_SUPPORTS), {"room": spots}, pred)
    assert w.went == []                                    # not on to the next viewpoint


def test_explore_with_no_reachable_viewpoint_says_so(monkeypatch):
    spots = [(0.0, 1.0, 0.0)]
    w = World()
    with pytest.raises(SkillFailure, match="no viewpoint the base can get to sees any of it"):
        _explore(monkeypatch, w, _rig(ROOM_SUPPORTS), {"room": spots}, {spots[0]: ["furniture:a"]},
                 reachable=lambda p: False)


def test_explore_carrying_takes_the_carry_posture_before_the_viewpoints(monkeypatch):
    from zeno_skills.skill_jobs import carry
    order, spot = [], (5.0, 1.0, 0.0)
    w = World()
    monkeypatch.setattr(carry, "carry_posture", lambda rig, min_bottom_z=None: order.append("carry"))
    _patch(monkeypatch, w, {})
    monkeypatch.setattr(BM, "standoff_poses", lambda rig, place: order.append(place) or ([spot] if place == "room" else []))
    monkeypatch.setattr(PC, "_travel_tw", lambda rig: {})
    monkeypatch.setattr(PC, "_predicted", lambda rig, pose, targets, tw: {k: v[0][0] for k, v in targets.items()})
    rig = _rig(ROOM_SUPPORTS, held={"name": "living_car"})
    rig.base_pose = lambda: w.pose
    PC.ExploreRoomPolicy(rig).execute("room")
    assert order[:2] == ["carry", "room"]


# ------------------------------------------------------------------ explore_furniture
LAYERS = [_support("shelf/top", "shelf", 1.0, z=1.0), _support("shelf/shelf_0", "shelf", 1.0, z=0.5)]


def _furniture(monkeypatch, w, poses, **kw):
    _patch(monkeypatch, w, {"shelf": poses}, **kw)
    monkeypatch.setattr(PC, "entity_footprint", lambda rig, name: [1.0, 0.0, 1.4, 0.4])
    monkeypatch.setattr(PC, "_board_blocks", lambda cam, q, layers: False)
    rig = _rig(LAYERS)
    rig.base_pose = lambda: w.pose
    rig.held = {"name": "x"}                                # no crouch in these tests
    from zeno_skills.skill_jobs import carry
    monkeypatch.setattr(carry, "carry_posture", lambda rig, min_bottom_z=None: None)
    return PC.ExploreFurniturePolicy(rig).execute("shelf")


def test_explore_furniture_drives_only_to_reachable_stand_offs_it_is_in_view_from(monkeypatch):
    poses = [(1.2, -2.5, 90.0), (1.2, -3.0, 90.0), (1.2, -3.5, 90.0)]
    w = World(sees=lambda pose, p: pose == poses[2])
    out = _furniture(monkeypatch, w, poses, reachable=lambda p: p != poses[0],
                     in_view=lambda place, p: p == poses[2])
    assert w.went == [poses[2]] and out["layers"] == ["shelf/shelf_0", "shelf/top"]


def test_a_drive_that_fails_fails_explore_furniture(monkeypatch):
    poses = [(1.2, -2.5, 90.0), (1.2, -3.5, 90.0)]
    w = World(sees=lambda pose, p: pose != (0.0, 0.0, 0.0), fail_at=[poses[0]])
    with pytest.raises(SkillFailure, match="no base path"):
        _furniture(monkeypatch, w, poses)
    assert w.went == []


# ------------------------------------------------------------------ look's plan
class _S:
    """A State as plan_look reads it: the base, the body, the right arm's q."""

    def __init__(self, base):
        self.base, self.body = base, np.zeros(2)

    def q(self, side="right"):
        return np.zeros(9)


def test_look_plans_one_head_segment_per_aim(monkeypatch):
    from zeno_skills.skill_jobs import look as LJ
    monkeypatch.setattr(LJ, "look_angles", lambda rig, p, base_pose=None, torso_waist=None: (0.25 * p[0], -0.2))
    aims = [("point", "cup", [3.0, 0.0, 0.8], 90), ("head", 0.5, 0.3, 50)]
    plan = LK.plan_look(None, None, _S((0.0, 0.0, 0.0)), None, lambda s: LJ.head_aims(s, aims))
    assert [s.name for s in plan.segments] == ["look_0", "look_1"]
    assert plan.segments[0].action == ("head", 0.75, -0.2, 90) and plan.segments[0].info["looks_at"] == "cup"
    assert plan.segments[1].action == ("head", 0.5, 0.3, 50)


def test_a_look_that_turns_is_navigate_then_heads_rebuilt_from_the_measured_base(monkeypatch):
    """The turn is navigate's plan (its arrive anchor); the head angles are computed for the heading it
    assumes, and run's rebuild from the first head segment computes them again from the base it measures."""
    got = []
    heads = lambda s: got.append(tuple(s.base)) or [(0.0, 0.0, 90, "cup")]
    nav = Plan((Segment("look_turn", Spec(), np.zeros(9), kind="drive"),
                Segment("arrive", Spec(), np.zeros(9), kind="anchor")))
    monkeypatch.setattr(LK, "plan_navigate", lambda *a, **k: nav)
    plan = LK.plan_look(None, None, _S((1.0, 2.0, 0.0)), None, heads, face=90.0)
    assert [s.name for s in plan.segments] == ["look_turn", "arrive", "look_0"] and got == [(1.0, 2.0, 90.0)]
    again = LK.plan_look(None, None, _S((1.0, 2.0, 87.0)), None, heads, face=90.0, start="look_0")
    assert [s.name for s in again.segments] == ["look_0"] and got[-1] == (1.0, 2.0, 87.0)


def test_a_turn_that_cannot_be_made_fails_the_look(monkeypatch):
    monkeypatch.setattr(LK, "plan_navigate", lambda *a, **k: Failure("no base path", "look_turn"))
    assert isinstance(LK.plan_look(None, None, _S((0.0, 0.0, 0.0)), None, lambda s: [], face=90.0), Failure)


def test_the_head_moves_through_the_actuator_as_a_segment():
    """drive_head is a head action segment run by run.execute (Actuator.aim_head), declared to the contact
    monitor like a wait (the arms, base and hands do not move)."""
    calls = []
    act = SimpleNamespace(q=lambda: np.zeros(9), aim_head=lambda *a: calls.append(("head", *a)),
                          declare=lambda name, allow, side="right", follows=True: calls.append(("declare", follows)))
    seg = PC.head_segment(act, 0.3, -0.1, steps=60)
    assert seg.kind == "action" and seg.action == ("head", 0.3, -0.1, 60)
    PC.drive_head(act, 0.3, -0.1, steps=60)
    assert calls == [("declare", False), ("head", 0.3, -0.1, 60)]


# ------------------------------------------------------------------ the look / inspect skills (jobs)
def test_look_at_is_only_the_look_skill(monkeypatch):
    """docs 2.3: AtomicPolicy.execute is run_skill and nothing else; the job decides the turn and judges."""
    from zeno_skills import motion_skills as MS
    calls = []
    monkeypatch.setattr(MS, "run_skill", lambda rig, skill, args: calls.append((skill.name, args)) or {"visible": True})
    assert PC.LookAtPolicy(SimpleNamespace()).execute("cup") == {"visible": True}
    assert calls == [("look", {"target": "cup"})]
    calls.clear()
    PC.InspectReceptaclePolicy(SimpleNamespace()).execute("cabinet")
    assert calls == [("inspect", {"receptacle": "cabinet"})]


def _job_rig():
    return SimpleNamespace(held=None, kin=None, left_kin=None, log=lambda *a, **k: None, tick=7, memory={},
                           base_pose=lambda: (0.0, 0.0, 0.0))


def test_the_look_job_turns_only_past_the_head_yaw_range_and_judges_the_view(monkeypatch):
    from zeno_skills import predicates
    from zeno_skills.skill_jobs import look as LJ
    rig = _job_rig()
    monkeypatch.setattr(predicates, "entity_point", lambda r, n, st=None: np.array([-2.0, 0.0, 0.8]))
    monkeypatch.setattr(LJ, "look_angles", lambda r, p, **k: (3.0, 0.0))           # behind: past the yaw range
    monkeypatch.setattr(PC, "record_view", lambda r: ["cup"])
    monkeypatch.setattr(predicates, "memory", lambda r: r.memory.setdefault("m", {"observed": {}}))
    seen = {"ok": False}
    monkeypatch.setattr(LJ, "project_to_head_camera", lambda r, p, exclude=None: (seen["ok"], "line of sight blocked"))
    got = {}
    monkeypatch.setattr(LJ, "_job", lambda r, st, sk, aims, face, label, on_view=None, done=None:
                        got.update(aims=aims, face=face, done=done) or "job")
    LJ.look_job(rig, {"target": "cup"}, None)
    assert got["face"] == pytest.approx(180.0) and got["aims"][0][1] == "cup"
    with pytest.raises(SkillFailure, match="look at cup: line of sight blocked"):
        got["done"]()
    seen["ok"] = True
    assert got["done"]() == {"visible": True, "seen": ["cup"]} and rig.memory["m"]["observed"]["cup"] == 7
    monkeypatch.setattr(LJ, "look_angles", lambda r, p, **k: (0.4, 0.0))           # within it: no turn
    LJ.look_job(rig, {"target": "cup"}, None)
    assert got["face"] is None


def test_the_inspect_job_records_the_contents_it_sees(monkeypatch):
    from zeno_skills import predicates
    from zeno_skills.skill_jobs import look as LJ
    rig = _job_rig()
    rig.ann = SimpleNamespace(supports=[{"name": "cab/top", "furniture": "cab"}], objects={"cup": {}, "bowl": {}})
    rig.state = lambda: {}
    rig.geo = SimpleNamespace(centre=lambda n, st: np.array([1.0, 0.0, 0.9]) if n == "cup" else np.array([9.0, 0.0, 0.9]))
    monkeypatch.setattr(predicates, "entity_kind", lambda ann, n: ("support", {}))
    monkeypatch.setattr(predicates, "entity_point", lambda r, n, st=None: np.array([1.0, 0.0, 0.9]))
    monkeypatch.setattr(predicates, "objects_on_support", lambda r, n, st: ["cup", "bowl"])
    monkeypatch.setattr(predicates, "memory", lambda r: r.memory.setdefault("m", {"observed": {}}))
    monkeypatch.setattr(PC, "record_view", lambda r: [])
    monkeypatch.setattr(LJ, "look_angles", lambda r, p, **k: (0.0, 0.0))
    monkeypatch.setattr(LJ, "project_to_head_camera", lambda r, p, exclude=None: (bool(p[0] < 5), ""))
    got = {}
    monkeypatch.setattr(LJ, "_job", lambda r, st, sk, aims, face, label, on_view=None, done=None:
                        got.update(done=done) or "job")
    LJ.inspect_job(rig, {"receptacle": "cab/top"}, None)
    assert got["done"]() == {"contents": ["cup"]} and rig.memory["m"]["contents"]["cab/top"] == ["cup"]


def test_a_crouch_that_fails_fails_explore_furniture(monkeypatch):
    """It was logged as explore_crouch_skip and the low layers left unseen (rule 3: no swallowed failure)."""
    from zeno_skills.policies import posture
    w = World(sees=lambda pose, p: p[2] > 0.9)                 # the top only, standing
    monkeypatch.setattr(posture.LowerTorsoPolicy, "execute", lambda self, height=None: (_ for _ in ()).throw(
        SkillFailure("torso_lift_joint: actual -0.380, target -0.540")))
    monkeypatch.setattr(posture.SetTorsoHeightPolicy, "execute", lambda self, h: h)
    _patch(monkeypatch, w, {"shelf": []})
    monkeypatch.setattr(PC, "entity_footprint", lambda rig, name: [0.0, 0.5, 0.4, 0.9])
    monkeypatch.setattr(PC, "_board_blocks", lambda cam, q, layers: False)
    rig = _rig(LAYERS)
    rig.base_pose = lambda: w.pose
    rig.kin = SimpleNamespace(names=["torso_lift_joint", "waist_pitch_joint"], lo=np.array([-0.54, 0.0]),
                              hi=np.array([0.0, 1.0]))
    rig.q = lambda: np.zeros(9)
    with pytest.raises(SkillFailure, match="torso_lift_joint"):
        PC.ExploreFurniturePolicy(rig).execute("shelf")
