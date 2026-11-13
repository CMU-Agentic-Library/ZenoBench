"""One rule for what stands behind a door (annotations.behind_door): a support inside the carcass
(category cabinet_inside), else a point in a cavity or a refrigerator's body -- never a top."""

from types import SimpleNamespace

import numpy as np

from zeno_skills.annotations import SceneAnnotations, ROOT, behind_door, opening

CAB = {"name": "cab", "type": "revolute", "category": "cabinet_door", "handle": {"outward": [1.0, 0.0, 0.0]},
       "body_aabb": [0.0, 0.0, 0.0, 0.5, 0.6, 0.8]}
FRIDGE = {"name": "fridge", "type": "revolute", "category": "refrigerator", "handle": {"outward": [0.0, -2.0, 0.0]},
          "body_aabb": [2.0, 0.0, 0.0, 2.6, 0.6, 1.4]}
OVEN = {"name": "oven", "type": "revolute", "category": "microwave", "handle": {"outward": [0.0, 1.0, 0.0]},
        "body_aabb": [4.0, 0.0, 0.9, 4.5, 0.4, 1.2], "cavity_aabb": [4.05, 0.05, 0.92, 4.4, 0.35, 1.15]}
ANN = SimpleNamespace(articulated=[CAB, FRIDGE, OVEN])


def test_a_shelf_inside_is_behind_its_door_and_the_top_is_not():
    assert behind_door(ANN, {"name": "cab/inside_shelf", "furniture": "cab", "category": "cabinet_inside"}) is CAB
    # the top of the same cabinet is in the open (the old place hint took any support of a hinged cabinet)
    assert behind_door(ANN, {"name": "cab/top", "furniture": "cab", "category": "cabinet_top"}, (0.2, 0.3, 0.85)) is None
    # a cabinet has no cavity box: its body counts only through its inside supports
    assert behind_door(ANN, None, (0.2, 0.3, 0.4)) is None


def test_a_point_in_a_cavity_or_in_the_fridge_body_is_behind_that_door():
    assert behind_door(ANN, None, (4.2, 0.2, 1.0)) is OVEN
    assert behind_door(ANN, None, (4.2, 0.2, 1.3)) is None              # on the microwave's top
    assert behind_door(ANN, None, (2.3, 0.3, 0.9)) is FRIDGE
    assert behind_door(ANN, {"name": "table/top", "category": "table"}, (2.3, 0.3, 0.9)) is FRIDGE


def test_the_opening_is_the_handles_outward_normal_made_unit_and_horizontal():
    assert np.allclose(opening(FRIDGE), [0.0, -1.0])
    assert opening({"name": "x", "handle": {"center": [0, 0, 0]}}) is None


def test_every_inside_support_of_the_scenes_is_behind_its_articulated_and_no_top_is():
    import glob
    n = 0
    for f in sorted(glob.glob(str(ROOT / "tasks" / "*" / "annotation*.json"))):
        ann = SceneAnnotations(f)
        for s in ann.supports:
            a = behind_door(ann, s)
            if s.get("category") == "cabinet_inside":
                assert a is not None and a["name"] == s["furniture"], s["name"]
                assert opening(a) is not None, a["name"]
                n += 1
            else:
                assert a is None, s["name"]
    assert n > 0


def test_spots_behind_a_door_come_frontmost_first(monkeypatch):
    from zeno_skills import skills
    shelf = {"name": "cab/inside_shelf", "furniture": "cab", "category": "cabinet_inside", "z": 0.3,
             "aabb_xy": [0.0, 0.0, 0.5, 0.4]}
    asset = {"size": [0.06, 0.06, 0.1], "grasps": []}
    ann = SimpleNamespace(articulated=[CAB], support=lambda n: shelf, asset_of=lambda o: asset,
                          objects={"block": {"asset": "block"}})
    rig = SimpleNamespace(ann=ann, state=lambda: {"objects": {}}, base_pose=lambda: (1.2, 0.35, 180.0))
    monkeypatch.setattr(skills, "_open_edges", lambda rig_, s: [])
    spots = skills.free_spots(rig, "block", "cab/inside_shelf")
    xs = [x for x, _ in spots]
    assert xs[0] == max(xs) and xs[0] > 0.4                 # the opening is +x: the front row first
    assert all(xs[i] >= xs[i + 1] - 1e-9 for i in range(len(xs) - 1))


def test_a_set_down_behind_a_door_whose_way_out_leaves_through_the_opening_is_tried_first():
    from zeno_skills.skill_jobs.door_access import leave_tier
    out = FRIDGE                                             # opening -y
    assert leave_tier(out, [0.0, -1.0, 0.0]) == 0             # straight out
    assert leave_tier(out, [0.7071, -0.7071, 0.0]) == 1
    assert leave_tier(out, [1.0, 0.0, 0.0]) == 2
    assert leave_tier(out, [0.0, 1.0, 0.0]) == 4              # into the back wall
    assert leave_tier(out, [0.0, 0.0, 1.0]) == 2              # lifted off: still inside


def test_a_box_behind_a_door_may_go_in_on_another_face():
    from zeno_skills.kinematics import gripper_rot
    from zeno_skills.skill_jobs.place import _lies_on_a_face, _on_side
    carton = {"size": [0.06, 0.11, 0.17], "origin_to_bottom_center": [0.0, 0.0, -0.085], "tags": ["box"],
              "grasps": [{"type": "top_pinch"}, {"type": "side_pinch", "round": False}]}
    assert _lies_on_a_face(carton)
    assert not _lies_on_a_face({"size": [0.06] * 3, "grasps": [{"type": "side_pinch", "round": True}]})
    assert not _lies_on_a_face({"size": [0.06] * 3, "grasps": [], "container": {"rim_height": 0.05}})
    # a top pinch across the 6 cm (x), the TCP 2.6 cm below the top
    R_tcp = gripper_rot([0.0, 0.0, -1.0], [1.0, 0.0, 0.0])
    off = np.array([0.0, 0.0, 0.085 - 0.026])                 # TCP minus origin (the box centre)
    for sign in (1.0, -1.0):
        # about the closing axis: the fingers stay on its sides, the 11 cm stands up
        off_n, R_n, label, hang = _on_side(carton, np.eye(3), np.eye(3), off, R_tcp, 1, sign)
        assert abs(R_n[2, 2]) < 1e-9 and np.allclose(R_n[:, 1], R_tcp[:, 1])
        assert abs(hang - 0.055) < 1e-9 and abs(off_n[2]) < 1e-9
        # across it: closing vertical (a finger under it: the collision check's), the 6 cm stands up
        off_n, R_n, label, hang = _on_side(carton, np.eye(3), np.eye(3), off, R_tcp, 0, sign)
        assert abs(R_n[2, 2]) < 1e-9 and abs(abs(R_n[2, 1]) - 1.0) < 1e-9 and abs(hang - 0.03) < 1e-9
    # a spoon lying flat, top-pinched across its width (y): about the closing axis its length stands up
    # (offered: the collision check and the search decide), about the other on its edge
    spoon = {"size": [0.18, 0.04, 0.02], "origin_to_bottom_center": [0.0, 0.0, -0.01], "grasps": []}
    R_sp = gripper_rot([0.0, 0.0, -1.0], [0.0, 1.0, 0.0])
    assert abs(_on_side(spoon, np.eye(3), np.eye(3), np.zeros(3), R_sp, 1, 1.0)[3] - 0.09) < 1e-9
    assert abs(_on_side(spoon, np.eye(3), np.eye(3), np.zeros(3), R_sp, 0, 1.0)[3] - 0.02) < 1e-9
    # a cube: any face
    cube = {"size": [0.04] * 3, "origin_to_bottom_center": [0.0, 0.0, -0.02], "grasps": []}
    assert all(_on_side(cube, np.eye(3), np.eye(3), np.zeros(3), R_sp, a, 1.0) is not None for a in (0, 1))


def test_a_load_hanging_a_little_off_level_is_turned_and_levelled_not_dropped():
    from scipy.spatial.transform import Rotation
    from zeno_skills.kinematics import gripper_rot
    from zeno_skills.skill_jobs.place import _on_side
    carton = {"size": [0.06, 0.11, 0.17], "origin_to_bottom_center": [0.0, 0.0, -0.085], "grasps": []}
    tilt = Rotation.from_rotvec([0.0, 0.0, 0.0] if False else [0.02, 0.04, 0.0]).as_matrix()    # ~2.6 deg off
    R_tcp = tilt @ gripper_rot([0.0, 0.0, -1.0], [1.0, 0.0, 0.0])
    r = _on_side(carton, np.eye(3), tilt, tilt @ np.array([0.0, 0.0, 0.059]), R_tcp, 1, 1.0)
    off_n, R_n, label, hang = r
    assert abs(hang - 0.055) < 1e-6                              # levelled: resting flat on the 6 x 17 face


def test_a_box_set_down_on_its_side_is_judged_by_the_face_it_lies_on():
    from scipy.spatial.transform import Rotation
    from zeno_skills.evaluator import Geometry
    from zeno_skills.skill_jobs.place import _place_result
    carton = {"size": [0.06, 0.11, 0.17], "origin_to_bottom_center": [0.0, 0.0, -0.085], "grasps": []}
    shelf = {"name": "cab/inside_shelf", "z": 0.412, "aabb_xy": [3.2, 0.2, 3.8, 0.52]}
    ann = SimpleNamespace(objects={"snack": {"asset": "snack_carton"}}, asset_of=lambda o: carton, supports=[shelf])
    q = Rotation.from_rotvec([0.5 * np.pi, 0.0, 0.0]).as_quat()        # x y z w: on its 6 x 17 face, 11 cm up
    st = {"objects": {"snack": {"pos": [3.6, 0.36, 0.412 + 0.055], "quat": [q[3], q[0], q[1], q[2]]}}}
    rig = SimpleNamespace(ann=ann, geo=Geometry(ann), state=lambda: st, log=lambda *a, **k: None, focus_z=0.4)
    assert _place_result(rig, "snack", shelf, (3.6, 0.36), "pinch", None) is True
    st["objects"]["snack"]["pos"][2] += 0.10                            # hanging in the air: not on it
    import pytest
    from zeno_skills.rig import SkillFailure
    with pytest.raises(SkillFailure):
        _place_result(rig, "snack", shelf, (3.6, 0.36), "pinch", None)


def test_on_reads_the_face_a_box_lies_on_and_the_floor_alike():
    from scipy.spatial.transform import Rotation
    from zeno_skills.evaluator import Geometry
    carton = {"size": [0.06, 0.11, 0.17], "origin_to_bottom_center": [0.0, 0.0, -0.085], "grasps": []}
    shelf = {"name": "cab/inside_shelf", "z": 0.412, "aabb_xy": [3.2, 0.2, 3.8, 0.52]}
    ann = SimpleNamespace(objects={"snack": {"asset": "x"}}, asset_of=lambda o: carton, supports=[shelf], rooms=[])
    g = Geometry(ann)
    up = {"objects": {"snack": {"pos": [3.5, 0.36, 0.412 + 0.085], "quat": [1.0, 0.0, 0.0, 0.0]}}}
    assert g.on("snack", "cab/inside_shelf", up)[0] and np.allclose(g.resting("snack", up), g.bottom("snack", up))
    q = Rotation.from_rotvec([0.5 * np.pi, 0.0, 0.0]).as_quat()
    side = {"objects": {"snack": {"pos": [3.5, 0.36, 0.412 + 0.055], "quat": [q[3], q[0], q[1], q[2]]}}}
    assert g.on("snack", "cab/inside_shelf", side)[0]
    assert g.support_under("snack", side) is shelf
