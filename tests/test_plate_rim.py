"""A plate's rim pinch (tools/prepare_assets.plate_rim_pinch) and a lid's seat on a rim (policies.hand.lid_seat):
a plate laid on a pot as a lid overhangs the pot's rim by under a centimetre, so it is held at its outer rim from
above, no pad under it, and set down resting on the rim by its own rim, its foot hanging inside the pot (T15 /
T09 / T17 cover, 11-27)."""

import json
import math
from pathlib import Path

import numpy as np

from zeno_skills.annotations import SceneAnnotations
from zeno_skills.policies.hand import lid_seat

ROOT = Path(__file__).resolve().parents[1]
ASSETS = json.loads((ROOT / "annotations" / "assets.json").read_text())


def _plate_rim():
    return next(g for g in ASSETS["breakfast_plate"]["grasps"] if g["type"] == "rim_pinch")


def test_the_plate_keeps_its_thickness_pinch_and_gets_a_rim_pinch_above_its_rim():
    kinds = [g["type"] for g in ASSETS["breakfast_plate"]["grasps"]]
    assert kinds == ["thickness_pinch", "rim_pinch"]
    g = _plate_rim()
    assert g["depth"] < 0                                   # the TCP above the rim's top
    assert g["radius"] > 0.5 * max(ASSETS["breakfast_plate"]["size"][:2])     # ...and outside its edge


def test_plate_rim_candidates_come_from_above_and_outside_at_the_edge():
    ann = SceneAnnotations.__new__(SceneAnnotations)
    ann.assets = {"breakfast_plate": ASSETS["breakfast_plate"]}
    pos = np.array([1.0, 2.0, 0.9])
    poses = ann.grasp_poses({"asset": "breakfast_plate"}, pos, [1.0, 0.0, 0.0, 0.0], kinds=("rim_pinch",))
    g = _plate_rim()
    assert len(poses) == len(g["azimuths_deg"]) * len(g["tilts"])
    bottom = pos + np.asarray(ASSETS["breakfast_plate"]["origin_to_bottom_center"], float)
    for c in poses:
        d = c["p"][:2] - bottom[:2]
        assert math.isclose(float(np.linalg.norm(d)), g["radius"], abs_tol=1e-6)
        assert math.isclose(float(c["p"][2] - bottom[2]), g["rim_height"] - g["depth"], abs_tol=1e-6)
        approach = -c["R"][:, 2]
        assert approach[2] < 0 and float(approach[:2] @ d) < 0      # down and in: the hand above and outside


def test_a_pot_lid_rests_on_its_lowest_ring_and_a_plate_on_its_rim_2_cm_up():
    pot = ASSETS["handled_cooking_pot"]["container"]["rim_radius"]
    assert lid_seat(ASSETS["pot_lid"], pot) < 0.002
    assert 0.015 < lid_seat(ASSETS["breakfast_plate"], pot) < 0.025


def test_a_lid_without_a_collider_has_no_seat():
    assert lid_seat({"name": "nothing", "origin_to_bottom_center": [0.0, 0.0, 0.0]}, 0.1) == 0.0
