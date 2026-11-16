"""navigate to an object stops where the head camera sees it (base_motion.NavigateToPlacePolicy,
perception.in_view_from): look_target and the benchmark's gate want the object in view next.  A floor object
near the base is below the frustum (the head pitches 18 deg down at most: T23 belongs_on_floor, 0.54 m away,
v -48 deg), and furniture on the line of sight hides it (T23 dropped_out_of_view, a plant pot)."""

from types import SimpleNamespace

import numpy as np

from zeno_skills import perception as P
from zeno_skills.policies import base_motion as BM
from zeno_skills.predicates import head_fov_deg

FLOOR = [-50, -50, -1.0, 50, 50, 0.0]          # WorldModel.B ends with the floor; the line of sight skips it
GT, BENCH = head_fov_deg(7.5, 720, 960), head_fov_deg(10.0, 480, 640)   # the profiles' lenses
UP = {"torso_lift_joint": 0.0, "waist_pitch_joint": 0.0}
SPOON = np.array([0.0, 0.0, 0.01])
POT = [-0.6, -0.3, 0.0, -0.2, 0.3, 1.0]           # a 1 m box between a base 1.05 m away and the spoon


def _facing(d):
    """The base d m from the spoon on its -x side, facing it."""
    return (-d, 0.0, 0.0)


def _rig(boxes=(), fov=GT, held=None, torso=0.0):
    names = ["torso_lift_joint", "waist_pitch_joint"] + [f"right_arm_joint_{i}" for i in range(1, 8)]
    rest = np.r_[0.0, 0.0, np.zeros(7)]
    ann = SimpleNamespace(objects={"spoon": {}}, articulated=[], appliances=[], rooms={"kitchen": {}},
                          supports=[{"name": "counter/top", "furniture": "counter", "aabb_xy": [0, 0, 1, 1], "z": 0.9}])
    return SimpleNamespace(head_fov_deg=fov, world=SimpleNamespace(B=np.array([*boxes, FLOOR], float)), ann=ann,
                           held=held, left_held=None, kin=SimpleNamespace(names=names, rest=rest),
                           left_kin=SimpleNamespace(rest=np.zeros(9)), q_cmd=np.r_[torso, 0.0, np.zeros(7)],
                           log=lambda *a, **k: None, base_pose=lambda: (0.0, 0.0, 0.0))


def test_a_floor_object_half_a_metre_from_the_base_is_below_the_frustum():
    ok, why = P.in_view_from(_rig(), _facing(0.54), SPOON, UP)
    assert not ok and why.startswith("outside frustum")
    assert P.in_view_from(_rig(), _facing(1.05), SPOON, UP)[0]


def test_the_benchmark_lens_needs_the_base_farther():
    assert P.in_view_from(_rig(fov=GT), _facing(0.70), SPOON, UP)[0]
    assert not P.in_view_from(_rig(fov=BENCH), _facing(0.70), SPOON, UP)[0]
    assert P.in_view_from(_rig(fov=BENCH), _facing(0.90), SPOON, UP)[0]


def test_furniture_on_the_line_of_sight_hides_it():
    ok, why = P.in_view_from(_rig([POT]), _facing(1.05), SPOON, UP)
    assert not ok and why.startswith("line of sight blocked")


def test_the_current_head_pose_is_judged_the_same_way(monkeypatch):
    rig = _rig()
    yaw, pitch = P.look_angles(rig, SPOON, base_pose=_facing(0.54), torso_waist=UP)
    pose = P.head_camera_pose(_facing(0.54), dict(UP, head_yaw_joint=yaw, head_pitch_joint=pitch))
    monkeypatch.setattr(P, "rig_head_pose", lambda r: pose)
    assert P.project_to_head_camera(rig, SPOON, exclude="spoon") == P.in_view_from(rig, _facing(0.54), SPOON, UP)


def _navigate(monkeypatch, rig, place, poses, reachable=None):
    went = []
    monkeypatch.setattr(BM, "standoff_poses", lambda r, p: list(poses))
    monkeypatch.setattr(BM.skills, "base_reachable", lambda r, ps: reachable or [True] * len(ps))
    monkeypatch.setattr(BM.skills, "navigate", lambda r, pose, **kw: went.append(pose))
    monkeypatch.setattr(BM, "entity_point", lambda r, name, st=None: SPOON)
    BM.NavigateToPlacePolicy(rig).execute(place)
    return went


def test_navigate_to_an_object_stops_where_it_is_in_view(monkeypatch):
    near, far = _facing(0.54), _facing(1.05)
    assert _navigate(monkeypatch, _rig(), "spoon", [near, far]) == [far]


def test_only_stand_offs_the_base_can_get_to_count(monkeypatch):
    near, far = _facing(0.54), _facing(1.05)
    assert _navigate(monkeypatch, _rig(), "spoon", [near, far], reachable=[True, False]) == [near]


def test_seen_from_none_the_nearest_as_before(monkeypatch):
    near, far = _facing(0.54), _facing(1.05)
    assert _navigate(monkeypatch, _rig([POT]), "spoon", [near, far]) == [near]


def test_a_room_keeps_the_nearest(monkeypatch):
    near, far = _facing(0.54), _facing(1.05)
    assert _navigate(monkeypatch, _rig(), "kitchen", [near, far]) == [near]


def test_a_support_stops_where_it_is_in_view(monkeypatch):
    """entity_point is patched to the spoon's point: the support is judged at the point look aims at."""
    near, far = _facing(0.54), _facing(1.05)
    assert _navigate(monkeypatch, _rig(), "counter/top", [near, far]) == [far]


WALL = [-0.80, -1.0, 0.0, -0.75, 1.0, 2.5]     # a wall between a base 1.05 m away and the point; 0.70 m is in front


def test_a_stand_off_behind_a_wall_is_passed_over(monkeypatch):
    """1116: navigate to bookcase_2 stopped in the living room, 1 m from the bookcase behind the wall
    (wall_274), and search / look saw nothing; a stand-off the place is in view from comes first."""
    behind, front = _facing(1.05), _facing(0.70)
    assert P.in_view_from(_rig([WALL]), front, SPOON, UP)[0]
    assert not P.in_view_from(_rig([WALL]), behind, SPOON, UP)[0]
    assert _navigate(monkeypatch, _rig([WALL]), "counter/top", [behind, front]) == [front]
    assert _navigate(monkeypatch, _rig([WALL]), "counter", [behind, front]) == [front]


def test_furniture_counts_as_in_view_when_any_layer_is(monkeypatch):
    """A piece of furniture: its top (entity_point) or the space above any support layer (_layer_point)."""
    rig = _rig([WALL])
    monkeypatch.setattr(BM, "entity_point", lambda r, name, st=None: np.array([5.0, 5.0, 0.9]))   # out of view
    behind, front = _facing(1.05), _facing(0.70)
    from zeno_skills.policies import perceive
    monkeypatch.setattr(perceive, "_layer_point", lambda layer: SPOON)
    assert BM._in_view_poses(rig, "counter", [behind, front]) == [front]
    monkeypatch.setattr(perceive, "_layer_point", lambda layer: np.array([5.0, 5.0, 0.9]))
    assert BM._in_view_poses(rig, "counter", [behind, front]) == []


def test_a_loaded_arrival_keeps_its_torso_height(monkeypatch):
    """Carrying, navigate arrives with the body as it is (skills._rest_posture): a torso lowered to its limit
    puts the camera 0.54 m lower, and the spoon 0.54 m away comes into view."""
    monkeypatch.setattr(BM, "entity_point", lambda r, name, st=None: SPOON)
    near = _facing(0.54)
    assert BM._in_view_poses(_rig(), "spoon", [near]) == []
    assert BM._in_view_poses(_rig(held={"name": "cup"}, torso=-0.54), "spoon", [near]) == [near]
