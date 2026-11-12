"""Side pinches: the hand above the TCP, a box pinched across the faces that fit, the TCP no deeper
inside the near face than the palm allows, and a low object dipped (tools/prepare_assets.side_pinches)."""

import sys
from pathlib import Path

import numpy as np

from zeno_skills.annotations import SceneAnnotations, side_pinch_rot

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import prepare_assets  # noqa: E402


def _ann(asset):
    ann = SceneAnnotations.__new__(SceneAnnotations)
    ann.assets = {"a": asset}
    return ann


def test_level_side_pinch_comes_in_along_minus_d_with_the_palm_up():
    R = side_pinch_rot([1.0, 0.0, 0.0], 0.0)
    assert np.allclose(R[:, 2], [1.0, 0.0, 0.0])        # the TCP z points back along the hand
    assert np.allclose(R[:, 0], [0.0, 0.0, 1.0])        # the palm / camera side (palm_spheres x) up
    assert abs(R[2, 1]) < 1e-9                          # the fingers close horizontally


def test_dipped_side_pinch_comes_in_from_above():
    R = side_pinch_rot([1.0, 0.0, 0.0], 0.3)
    assert R[2, 2] > 0 and np.isclose(np.arcsin(R[2, 2]), 0.3)


def test_box_tcp_stays_depth_inside_the_near_face():
    g = {"type": "side_pinch", "width": 0.06, "offset_xy": [0.0, 0.0], "pre_open": 0.04, "azimuths_deg": [90, 270],
         "round": False, "tilt": 0.0, "height": 0.09, "depth": 0.024}
    ann = _ann({"size": [0.06, 0.11, 0.17], "origin_to_bottom_center": [0.0, 0.0, 0.0], "grasps": [g]})
    poses = ann.grasp_poses({"asset": "a"}, [1.0, 2.0, 0.5], [1.0, 0.0, 0.0, 0.0])
    assert [c["azimuth"] for c in poses] == [90, 270]
    assert np.allclose(poses[0]["p"], [1.0, 2.0 + 0.055 - 0.024, 0.59])
    assert np.allclose(poses[1]["p"], [1.0, 2.0 - 0.055 + 0.024, 0.59])


def test_round_tcp_on_the_axis_when_the_palm_allows():
    g = {"type": "side_pinch", "width": 0.04, "offset_xy": [0.0, 0.0], "pre_open": 0.032, "azimuths_deg": [0],
         "round": True, "tilt": 0.0, "height": 0.05, "depth": 0.03}
    ann = _ann({"size": [0.04, 0.04, 0.1], "origin_to_bottom_center": [0.0, 0.0, 0.0], "grasps": [g]})
    (c,) = ann.grasp_poses({"asset": "a"}, [0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0])
    assert np.allclose(c["p"], [0.0, 0.0, 0.05])


def test_low_block_is_dipped_tall_objects_level():
    block = prepare_assets.side_pinches(np.array([0.04, 0.04, 0.04]), 0.04)
    assert [g["azimuths_deg"] for g in block] == [[0, 180], [90, 270]]
    assert all(g["tilt"] > 0 for g in block)
    assert all(g["height"] <= 0.04 - 0.5 * 0.014 for g in block)
    bottle = prepare_assets.side_pinches(np.array([0.058, 0.058, 0.18]), 0.18, round_width=0.058)
    assert len(bottle) == 1 and bottle[0]["tilt"] == 0.0 and bottle[0]["height"] == 0.099


def test_box_face_wider_than_the_gripper_is_left_out():
    carton = prepare_assets.side_pinches(np.array([0.06, 0.11, 0.17]), 0.17)
    assert [g["azimuths_deg"] for g in carton] == [[90, 270]]
