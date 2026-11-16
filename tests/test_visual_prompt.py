"""Visual prompting for place (zeno_skills.visual_prompt, skill mark_spots, docs/skills/mark_spots.md):
spread-out free spots, projected with the rendering camera's own intrinsics and drawn as numbered discs;
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


def test_spread_keeps_the_best_spot_and_covers_the_support():
    grid = [(x, y) for x in np.arange(0.0, 1.01, 0.05) for y in np.arange(0.0, 0.51, 0.05)]
    out = VP.spread(grid, k=6, min_sep=0.12)
    assert out[0] == grid[0] and len(out) == 6
    d = [math.dist(a, b) for i, a in enumerate(out) for b in out[i + 1:]]
    assert min(d) >= 0.12
    xs = [p[0] for p in out]
    assert max(xs) - min(xs) > 0.9                       # both ends of the 1 m support, not one corner


def test_spread_stops_when_nothing_is_far_enough():
    assert VP.spread([(0, 0), (0.05, 0), (0.08, 0)], k=6, min_sep=0.12) == [(0, 0)]
    assert VP.spread([], k=6) == []


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
        patch = out[v - 4:v + 5, u - 9:u - 6]             # left part of the disc (the number is in the middle)
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
    close, _, _ = VP.view_coverage(rig, TABLE, (-0.35, 0.0, 0.0), UP)     # 0.35 m from the long side
    far, yaw, pitch = VP.view_coverage(rig, TABLE, (-1.2, 0.0, 0.0), UP)
    assert close < 1.0
    assert far == 1.0 and abs(yaw) < 0.05 and pitch > 0.0                # aimed straight ahead, looking down


def test_furniture_on_the_line_of_sight_hides_the_table():
    wall = [-0.8, -2.0, 0.0, -0.7, 2.0, 2.0]               # a 2 m board between the base and the table
    assert VP.view_coverage(_view_rig([wall]), TABLE, (-1.2, 0.0, 0.0), UP)[0] < 0.5


def test_best_view_takes_the_first_full_view_else_the_most():
    rig = _view_rig()
    poses = [(-0.35, 0.0, 0.0), (-1.2, 0.0, 0.0), (-1.25, 0.0, 0.0)]
    pose, cov, _, _ = VP.best_view(rig, TABLE, poses, UP)
    assert pose == poses[1] and cov == 1.0
    pose, cov, _, _ = VP.best_view(rig, TABLE, poses[:1], UP)
    assert pose == poses[0] and cov < 1.0
    assert VP.best_view(rig, TABLE, [], UP) is None


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


def test_mark_spots_numbers_spread_visible_spots_on_the_rendered_frame(monkeypatch):
    from zeno_skills import perception, skills
    table = {"name": "t/top", "category": "table", "z": 0.7, "aabb_xy": [0.6, -0.8, 1.6, 0.8]}
    rig = _spot_rig({})
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
    out = VP.mark_spots(rig, "held", "t/top")
    spots = out["spots"]
    assert 2 <= len(spots) <= VP.MAX_SPOTS
    assert min(math.dist(a, b) for i, a in enumerate(spots) for b in spots[i + 1:]) >= VP.MIN_SEP_M
    uv, z = VP.project(K, CAM_POS, CAM_R, [[x, y, 0.705] for x, y in spots])
    assert VP.in_image(uv, z, 640, 480, VP.EDGE_FRAC * 640).all()
    img = out["image"]
    for u, v in uv.round().astype(int):                  # a red disc at each spot
        assert img[v, u - 8, 0] > 200 and img[v, u - 8, 1] < 80


def test_the_numbered_image_reaches_the_next_observation_once():
    from episode.episode import Episode
    frame = np.zeros((48, 64, 3), np.uint8)
    drawn = np.full((48, 64, 3), 200, np.uint8)
    ep = Episode.__new__(Episode)
    ep.cameras, ep.n_obs, ep.image_dir = ["head"], 0, None
    ep.rig = SimpleNamespace(get_camera_images=lambda: {"head": frame},
                             memory={"visual_prompt": {"camera": "head", "overlay": "place_spots", "image": drawn}})
    first = ep._images("base64", None)
    assert [(e["camera"], e.get("overlay")) for e in first] == [("head", None), ("head", "place_spots")]
    assert [e.get("overlay") for e in ep._images("base64", None)] == [None]


def test_thinning_keeps_every_part_of_a_long_support():
    # free_spots ranks by distance to the robot: its first 400 of a 2.5 m table sat in the near half (T20 11-15)
    pts = [(x, y) for x in np.arange(0.0, 2.5, 0.03) for y in np.arange(0.0, 1.0, 0.03)]
    pts.sort(key=lambda p: p[0])                           # nearest the robot first
    out = VP.thin(pts, 0.06)
    assert out[0] == pts[0] and max(p[0] for p in out) > 2.4
    assert len(out) < len(pts) / 3
