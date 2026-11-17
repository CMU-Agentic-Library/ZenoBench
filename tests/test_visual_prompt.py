"""Visual prompting for place (zeno_skills.visual_prompt, skill mark_spots, docs/skills/mark_spots.md):
free spots beside each object, then spread over open space, projected with the rendering camera's own intrinsics and drawn as numbered discs;
the view that holds a whole support; the image reaching the observation once."""

import math
from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import visual_prompt as VP
from zeno_skills.predicates import head_fov_deg

BENCH = head_fov_deg(10.0, 480, 640)
FLOOR = [-50, -50, -1.0, 50, 50, 0.0]
K = np.array([[100.0, 0.0, 320.0], [0.0, 100.0, 240.0], [0.0, 0.0, 1.0]])


def test_one_spot_beside_each_object_then_another_side_then_open_space():
    # a 2 x 1 m table, a mug and a plate 0.5 m apart; the held object 0.1 m across
    grid = [(round(x, 3), round(y, 3)) for x in np.arange(0.05, 2.0, 0.03) for y in np.arange(0.05, 1.0, 0.03)]
    boxes = {"mug": [0.46, 0.46, 0.54, 0.54], "plate": [0.9, 0.4, 1.1, 0.6]}
    free = [p for p in grid if all(VP.box_gap(VP.square(p, 0.05), b) >= 0.07 for b in boxes.values())]
    rows = VP.beside(free, boxes, 0.05)
    for n, b in boxes.items():                            # the nearest ring: 7 cm off, within the 4 cm band
        gaps = [VP.box_gap(VP.square(p, 0.05), b) for p, _ in rows[n]]
        assert rows[n] and min(gaps) >= 0.07 and max(gaps) <= min(gaps) + VP.SPOT_BESIDE_BAND
    # the mug's best spot is the one farthest from the plate (beside the mug, not the plate)
    best_mug = rows["mug"][0][0]
    assert best_mug[0] < 0.5 and VP.box_gap(VP.square(best_mug, 0.05), boxes["plate"]) > 0.15
    centres = {n: np.array([(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]) for n, b in boxes.items()}

    def ok(p, taken, sep):
        return all(math.dist(p, t) >= sep for t in taken)
    out = VP.pick_spots(rows, centres, VP.thin(free), ok, k=8)
    who = [w for _, w in out]
    assert set(who[:2]) == {"mug", "plate"} and who[2:4] == ["mug", "plate"] and set(who[4:]) == {None}
    for n in boxes:                                       # the two spots of one object on different sides of it
        a, b = (np.asarray(p) - centres[n] for p, w in out if w == n)
        assert float(a @ b) <= 0.0
    pts = [p for p, _ in out]
    assert min(math.dist(a, b) for i, a in enumerate(pts) for b in pts[i + 1:]) >= 0.12


def test_open_space_alone_starts_at_the_best_spot_and_spreads():
    pts = [(x, y) for x in np.arange(0.0, 1.01, 0.05) for y in np.arange(0.0, 0.51, 0.05)]
    out = VP.pick_spots({}, {}, pts, lambda p, taken, sep: all(math.dist(p, t) >= sep for t in taken), k=6)
    assert out[0] == (pts[0], None) and len(out) == 6
    xs = [p[0] for p, _ in out]
    assert max(xs) - min(xs) > 0.9                       # both ends of the 1 m support, not one corner
    assert VP.pick_spots({}, {}, [(0, 0), (0.05, 0)], lambda p, t, sep: not t, k=6) == [((0, 0), None)]


def test_the_most_crowded_object_gets_its_spot_first():
    # a roomy spoon (nearer, first in order) has spots on both sides; the bowl has one, which the spoon's
    # clearest one would block: the bowl goes first and the spoon takes its other one
    rows = {"spoon": [((0.30, 0.0), 0.2), ((0.0, 0.3), 0.1)], "bowl": [((0.35, 0.0), 0.1)]}
    centres = {"spoon": np.array([0.15, 0.0]), "bowl": np.array([0.5, 0.0])}

    def ok(p, taken, sep):
        return all(math.dist(p, t) >= sep for t in taken)
    out = VP.pick_spots(rows, centres, [], ok, k=4)
    assert out[:2] == [((0.35, 0.0), "bowl"), ((0.0, 0.3), "spoon")]
    # a spot beside an object keeps sep_beside, one in open space sep_open
    out = VP.pick_spots({"bowl": [((0.35, 0.0), 0.1)]}, {"bowl": np.array([0.5, 0.0])}, [(0.5, 0.15), (0.9, 0.0)],
                        ok, k=4, sep_beside=0.12, sep_open=0.3)
    assert [p for p, _ in out] == [(0.35, 0.0), (0.9, 0.0)]


def test_resolution_is_finer_near_and_from_above():
    cam = np.array([0.0, 0.0, 1.3])
    near, far, grazing = VP.resolution(cam, [[0.5, 0.0, 0.7], [2.0, 0.0, 0.7], [2.0, 0.0, 1.29]], 92.0)
    assert near > 2 * far > 0 and grazing < far / 3
    assert VP.resolution(cam, [[1.0, 0.0, 1.4]], 92.0)[0] == 0.0         # above the camera


def _rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def test_projection_matches_a_pinhole_camera():
    # ROS camera frame: +z forward.  Identity: looking along world +z
    uv, z = VP.project(K, [0, 0, 0], np.eye(3), [[0.1, 0.2, 2.0]])
    assert np.allclose(uv, [[325.0, 250.0]]) and np.allclose(z, [2.0])
    # turned 90 deg about y: looking along world +x (camera x = world -z, camera y = world y)
    uv, z = VP.project(K, [0, 0, 0], _rot_y(math.pi / 2), [[2.0, 0.1, 0.2], [-2.0, 0.0, 0.0]])
    assert np.allclose(uv[0], [310.0, 245.0]) and z[0] == pytest.approx(2.0)
    assert z[1] < 0                                       # behind the camera
    assert list(VP.in_image(uv, z, 640, 480, 10)) == [True, False]


def test_the_rendering_camera_sits_on_the_head_chain_and_looks_along_it():
    # a point straight ahead of the head chain's camera link lands on the principal point; right / down
    # of it in the world is right / down in the image
    from zeno_skills.perception import head_camera_pose
    q = {"torso_lift_joint": -0.1, "waist_pitch_joint": 0.2, "head_yaw_joint": 0.3, "head_pitch_joint": 0.25}
    base = (1.0, -2.0, 40.0)
    p, R = head_camera_pose(base, q)
    pos, R_ros = VP.head_camera_ros(base, q)
    assert np.allclose(pos, p + VP.CAMERA_MOUNT * R[:, 0])
    assert np.allclose(R_ros.T @ R_ros, np.eye(3)) and np.linalg.det(R_ros) == pytest.approx(1.0)
    ahead = pos + 2.0 * R[:, 0]
    uv, z = VP.project(K, pos, R_ros, [ahead, ahead - 0.1 * R[:, 1], ahead - 0.1 * R[:, 2]])
    assert np.allclose(uv[0], [320.0, 240.0]) and z[0] == pytest.approx(2.0)
    assert uv[1][0] > 320.0 and uv[2][1] > 240.0           # to the right (-left), below (-up)


def test_discs_are_drawn_where_the_spots_project():
    img = np.zeros((480, 640, 3), np.uint8)
    out = VP.draw_spots(img, [[100.0, 200.0], [400.0, 300.0]])
    assert out.shape == img.shape
    for u, v in ((100, 200), (400, 300)):
        patch = out[v - 2:v + 3, u - 6:u - 4]             # left part of the disc (the number is in the middle)
        assert (patch[..., 0] > 200).any() and (patch[..., 1] < 80).any()
    assert out[20, 20].sum() == 0                         # elsewhere untouched
    assert img.sum() == 0                                 # a new array


def _view_rig(boxes=()):
    names = ["torso_lift_joint", "waist_pitch_joint"]
    return SimpleNamespace(head_fov_deg=BENCH, world=SimpleNamespace(B=np.array([*boxes, FLOOR], float)),
                           kin=SimpleNamespace(names=names))


TABLE = {"name": "dining_table_1/top", "aabb_xy": [0.0, -1.0, 1.05, 1.0], "z": 0.71}     # 1.05 x 2 m
UP = {"torso_lift_joint": 0.0, "waist_pitch_joint": 0.0}


def test_a_two_metre_table_fits_one_frame_only_from_far_enough_back():
    rig = _view_rig()
    centre = np.array([0.525, 0.0, 0.71])
    close, _, _ = VP.view_resolution(rig, TABLE, (-0.35, 0.0, 0.0), UP, centre)     # 0.35 m from the long side
    far, yaw, pitch = VP.view_resolution(rig, TABLE, (-1.2, 0.0, 0.0), UP, centre)
    assert (close == 0).any()
    assert (far > 0).all() and abs(yaw) < 0.05 and pitch > 0.0                 # aimed straight ahead, looking down


def test_furniture_on_the_line_of_sight_hides_the_table():
    wall = [-0.8, -2.0, 0.0, -0.7, 2.0, 2.0]               # a 2 m board between the base and the table
    res, _, _ = VP.view_resolution(_view_rig([wall]), TABLE, (-1.2, 0.0, 0.0), UP, np.array([0.525, 0.0, 0.71]))
    assert (res > 0).mean() < 0.5


SMALL = {"name": "t/top", "aabb_xy": [0.0, -0.4, 0.6, 0.4], "z": 0.71}           # 0.6 x 0.8 m
LONG = {"name": "t/top", "aabb_xy": [0.0, -1.5, 0.9, 1.5], "z": 0.71}            # 0.9 x 3 m


def test_a_small_table_takes_one_view_from_where_the_robot_stands():
    rig = _view_rig()
    here = (-0.6, 0.0, 0.0)
    views, seen = VP.support_views(rig, SMALL, [(-0.6, 0.5, 0.0), (0.3, -1.1, 90.0)], UP, here=here)
    assert len(views) == 1 and views[0][0] == here and seen == 1.0
    assert VP.support_views(rig, SMALL, [], UP) == ([], 0.0)


def test_a_long_table_takes_a_second_view_for_its_far_half():
    rig = _view_rig()
    ends = [(0.45, -2.3, 90.0), (0.45, 2.3, -90.0)]
    one, _, _ = VP.view_resolution(rig, LONG, ends[0], UP, np.array([0.45, 0.0, 0.71]))
    assert (one >= VP.VIEW_RES_MIN).mean() < 1.0           # from one end the far half is a few pixels
    views, seen = VP.support_views(rig, LONG, ends, UP)
    assert len(views) == 2 and {v[0] for v in views} == set(ends)
    assert seen > (one >= VP.VIEW_RES_MIN).mean() and seen > 0.9


def _spot_rig(objects_at):
    """A rig whose objects stand at objects_at {name: ((x, y), half-size)} on a counter at z 0.9."""
    from zeno_skills import skills  # noqa: F401  (the module under test imports it lazily)
    assets = {"cup": {"size": [0.08, 0.08, 0.1], "grasps": []}}
    objects = {n: {"asset": "cup"} for n in ["held", *objects_at]}
    ann = SimpleNamespace(articulated=[], asset_of=lambda o: assets[o["asset"]], objects=objects)

    def box(o):
        (x, y), h = objects_at.get(o, ((9.0, 9.0), 0.04))
        return x, y, h

    def bottom(o, st):
        x, y, _ = box(o)
        return np.array([x, y, 0.9])

    def footprint(o, st, margin=0.0):
        x, y, h = box(o)
        return [x - h - margin, y - h - margin, x + h + margin, y + h + margin]

    def centre(o, st):
        x, y, _ = box(o)
        return np.array([x, y, 0.95])
    geo = SimpleNamespace(bottom=bottom, resting=bottom, footprint=footprint, centre=centre)
    return SimpleNamespace(ann=ann, state=lambda: {}, geo=geo)


def test_a_spot_is_free_as_a_hint_when_place_takes_it_itself():
    from zeno_skills import skills
    counter = {"name": "c/top", "category": "counter", "z": 0.9, "aabb_xy": [0.0, 0.0, 1.0, 0.6]}
    rig = _spot_rig({"mug": ((0.5, 0.3), 0.04)})
    assert skills.hint_spot_free(rig, "held", counter, 0.2, 0.3)
    assert not skills.hint_spot_free(rig, "held", counter, 0.5, 0.3)          # on the mug
    assert not skills.hint_spot_free(rig, "held", counter, 0.06, 0.3)         # in the counter's 4 cm edge band
    table = dict(counter, category="table")
    assert skills.hint_spot_free(rig, "held", table, 0.06, 0.3)


class _T:
    def __init__(self, a):
        self.a = np.asarray(a, float)

    def cpu(self):
        return self

    def numpy(self):
        return self.a


# the camera of the mark_spots test: at (0, 0, 1.3) looking along world +x, 30 deg down (ROS columns)
_A = math.radians(30.0)
_FWD = np.array([math.cos(_A), 0.0, -math.sin(_A)])
CAM_POS, CAM_R = np.array([0.0, 0.0, 1.3]), np.column_stack([[0.0, -1.0, 0.0], np.cross(_FWD, [0.0, -1.0, 0.0]), _FWD])


def _mark_rig(monkeypatch, objects_at, z):
    from zeno_skills import perception, skills
    table = {"name": "t/top", "category": "table", "z": z, "aabb_xy": [0.6, -0.8, 1.6, 0.8]}
    rig = _spot_rig(objects_at)
    rig.ann.support = lambda n: table
    rig.world = SimpleNamespace(B=np.array([FLOOR], float))
    rig.first_person_camera = SimpleNamespace(data=SimpleNamespace(intrinsic_matrices=[_T(K)]))
    rig.get_first_person_image = lambda: np.zeros((480, 640, 3), np.uint8)
    rig.kin = SimpleNamespace(names=["torso_lift_joint", "waist_pitch_joint"])
    rig.q = lambda: np.zeros(9)
    rig.head_q = lambda: {"head_yaw_joint": 0.0, "head_pitch_joint": 0.0}
    rig.base_pose = lambda: (0.0, 0.0, 0.0)
    monkeypatch.setattr(VP, "head_camera_ros", lambda base, q: (CAM_POS, CAM_R))
    grid = [(round(x, 3), round(y, 3)) for x in np.arange(0.7, 1.55, 0.05) for y in np.arange(-0.7, 0.75, 0.05)]
    monkeypatch.setattr(skills, "free_spots", lambda rig_, name, support, k=8, **kw: grid[:k])
    monkeypatch.setattr(perception, "rig_head_pose", lambda rig_: (np.array([0.0, 0.0, 1.3]), np.eye(3)))
    return rig


def test_mark_spots_numbers_spread_visible_spots_on_the_rendered_frame(monkeypatch):
    out = VP.mark_spots(_mark_rig(monkeypatch, {}, 0.7), "held", "t/top")
    spots = out["spots"]
    assert 2 <= len(spots) <= VP.MAX_SPOTS and out["beside"] == [None] * len(spots) and len(out["images"]) == 1
    assert min(math.dist(a, b) for i, a in enumerate(spots) for b in spots[i + 1:]) >= VP.SPOT_MIN_SEP
    uv, z = VP.project(K, CAM_POS, CAM_R, [[x, y, 0.705] for x, y in spots])
    assert VP.in_image(uv, z, 640, 480, VP.SPOT_EDGE_FRAC * 640).all()
    assert list(uv[:, 0]) == sorted(uv[:, 0])            # numbered left to right
    r = VP.disc_radius(640)
    assert min(np.linalg.norm(a - b) for i, a in enumerate(uv) for b in uv[i + 1:]) >= VP.SPOT_PX_SEP * r
    img = out["images"][0]
    for u, v in uv.round().astype(int):                  # a red disc at each spot
        assert img[v, u - r + 2, 0] > 200 and img[v, u - r + 2, 1] < 80


def test_mark_spots_puts_a_spot_beside_each_object_on_the_support(monkeypatch):
    # two cups on the table (z 0.9: the test rig's objects rest at 0.9), one far off it
    objs = {"mug": ((1.0, -0.3), 0.04), "cup": ((1.2, 0.4), 0.04), "away": ((5.0, 5.0), 0.04)}
    out = VP.mark_spots(_mark_rig(monkeypatch, objs, 0.9), "held", "t/top")
    who = out["beside"]
    assert "mug" in who and "cup" in who and "away" not in who
    for (x, y), w in zip(out["spots"], who):
        if w is not None:
            (cx, cy), h = objs[w]
            gap = VP.box_gap(VP.square((x, y), 0.04), [cx - h, cy - h, cx + h, cy + h])
            assert 0.0 < gap <= VP.SPOT_BESIDE_MAX


def test_mark_spots_numbers_one_set_over_two_views(monkeypatch):
    # the second camera at the table's far side looking back (-x): each spot is numbered once, by the view
    # that sees it finer, and drawn on each image it is on
    rig = _mark_rig(monkeypatch, {}, 0.7)
    back = np.array([-_FWD[0], 0.0, _FWD[2]])
    R2 = np.column_stack([[0.0, 1.0, 0.0], np.cross(back, [0.0, 1.0, 0.0]), back])
    img = np.zeros((480, 640, 3), np.uint8)
    frames = [{"image": img, "K": K, "pos": CAM_POS, "R_ros": CAM_R},
              {"image": img, "K": K, "pos": np.array([2.2, 0.0, 1.3]), "R_ros": R2}]
    out = VP.mark_spots(rig, "held", "t/top", frames=frames)
    spots = out["spots"]
    assert len(out["images"]) == 2 and len(spots) >= 4
    d0 = [math.dist(p, CAM_POS[:2]) for p in spots]
    d1 = [math.dist(p, (2.2, 0.0)) for p in spots]
    home = [0 if a <= b else 1 for a, b in zip(d0, d1)]
    assert home == sorted(home) and set(home) == {0, 1}   # the first view's spots first, then the second's


def test_the_numbered_images_reach_the_next_observation_once():
    from episode.episode import Episode
    frame = np.zeros((48, 64, 3), np.uint8)
    drawn = np.full((48, 64, 3), 200, np.uint8)
    ep = Episode.__new__(Episode)
    ep.cameras, ep.n_obs, ep.image_dir = ["head"], 0, None
    ep.rig = SimpleNamespace(get_camera_images=lambda: {"head": frame},
                             memory={"visual_prompt": [{"camera": "head", "overlay": "place_spots", "view": v,
                                                        "image": drawn} for v in (1, 2)]})
    first = ep._images("base64", None)
    assert [(e["camera"], e.get("overlay"), e.get("view")) for e in first] == \
        [("head", None, None), ("head", "place_spots", 1), ("head", "place_spots", 2)]
    assert [e.get("overlay") for e in ep._images("base64", None)] == [None]


def test_thinning_keeps_every_part_of_a_long_support():
    # free_spots ranks by distance to the robot: its first 400 of a 2.5 m table sat in the near half (T20 11-15)
    pts = [(x, y) for x in np.arange(0.0, 2.5, 0.03) for y in np.arange(0.0, 1.0, 0.03)]
    pts.sort(key=lambda p: p[0])                           # nearest the robot first
    out = VP.thin(pts, 0.06)
    assert out[0] == pts[0] and max(p[0] for p in out) > 2.4
    assert len(out) < len(pts) / 3
