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
    assert leave_tier(out, [0.0, 0.2, 0.98]) == 0             # lifted off: no turn
