"""Held-object spheres for carry planning (held_spheres.fit / motion.add_held_links)."""

import copy

import numpy as np
import pytest
import yaml

from zeno_skills import held_spheres as H
from zeno_skills.motion import HELD_SPHERES, ROBOT_CFG, ROBOT_SPHERES_MAX, add_held_links, held_link
from zeno_skills.primitives import LEAVE_GAP


def _cyl(r, h, n=24):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = np.c_[r * np.cos(a), r * np.sin(a)]
    return np.vstack([np.c_[ring, np.full(n, -h / 2)], np.c_[ring, np.full(n, h / 2)]])


def _T(x=0.0, y=0.0, z=0.0, yaw=0.0):
    T = np.eye(4)
    T[:2, :2] = [[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]]
    T[:3, 3] = x, y, z
    return T


SHAPES = {
    "flat lid": [H.hull(_cyl(0.125, 0.06))],
    "book": [H.cuboid([0.22, 0.15, 0.04])],
    "bent (three boxes)": [H.cuboid([0.07, 0.035, 0.035], _T(-0.06, 0.0, 0.0, 0.5)),
                           H.cuboid([0.07, 0.035, 0.035], _T(0.0, 0.02)),
                           H.cuboid([0.07, 0.035, 0.035], _T(0.06, 0.0, 0.0, -0.5))],
    "spoon (thin)": [H.cuboid([0.12, 0.012, 0.004], _T(0.03)), H.cuboid([0.05, 0.035, 0.012], _T(-0.06))],
}


@pytest.mark.parametrize("name", list(SHAPES))
def test_held_spheres_hug_the_object_both_ways(name):
    # sticking out by no more than OUT (a set-down's end, the load LEAVE_GAP above its support,
    # stays free) and leaving the surface no further than GAP (+ the sampling) from them -- the
    # old box_spheres fell short of a lid's edge by 2-3 cm (T17) and of a mug's side by 1.6 cm (T04)
    pieces = SHAPES[name]
    sph, gap = H.fit(pieces, n_max=HELD_SPHERES["right"])
    assert 1 <= len(sph) <= HELD_SPHERES["right"] and gap == H.GAP
    out, off = H.check(pieces, sph)
    assert out <= H.OUT + 1e-6 and H.OUT < LEAVE_GAP
    assert off <= H.GAP + H.SAMPLE


def test_held_spheres_widen_the_gap_rather_than_exceed_the_budget():
    pieces = SHAPES["flat lid"]
    sph, gap = H.fit(pieces, n_max=40)
    assert len(sph) <= 40 and gap > H.GAP
    assert H.check(pieces, sph)[1] <= gap + H.SAMPLE
    with pytest.raises(ValueError):
        H.fit(pieces, n_max=3, gap_max=H.GAP)


def test_a_hull_fills_a_containers_opening():
    # a container held is its convex hull: what stands in it rides along (Motion.held)
    cup = H.hull(_cyl(0.05, 0.12))
    sph, _ = H.fit([cup], n_max=HELD_SPHERES["right"])
    centre = np.zeros(3)
    assert np.min(np.linalg.norm(sph[:, :3] - centre, axis=1) - sph[:, 3]) < 0


def test_held_links_on_the_tcp_and_out_of_self_collision():
    k = copy.deepcopy(yaml.safe_load(open(ROBOT_CFG))["robot_cfg"]["kinematics"])
    links = list(k["collision_link_names"])
    add_held_links(k)
    for s in ("right", "left"):
        h = held_link(s)
        assert k["extra_links"][h]["parent_link_name"] == k["extra_links"][f"{s}_tcp"]["parent_link_name"]
        assert k["extra_links"][h]["fixed_transform"] == k["extra_links"][f"{s}_tcp"]["fixed_transform"]
        assert k["extra_collision_spheres"][h] == HELD_SPHERES[s]
        assert h in k["collision_link_names"]
        assert set(k["self_collision_ignore"][h]) >= set(links)
    assert k["mesh_link_names"] == links        # the yaml alias is not extended


def test_the_robot_model_stays_within_curobos_self_collision_kernel():
    # cuRobo's self-collision kernel runs at least one thread per sphere of the model, and its pair
    # buffer holds ROBOT_SPHERES_MAX threads: more spheres read out of bounds (illegal memory access)
    k = copy.deepcopy(yaml.safe_load(open(ROBOT_CFG))["robot_cfg"]["kinematics"])
    add_held_links(k)
    robot = sum(len(v) for v in k["collision_spheres"].values())
    assert robot + sum(k["extra_collision_spheres"].values()) <= ROBOT_SPHERES_MAX


def test_a_target_above_a_flat_object_leaves_it_an_obstacle():
    from zeno_skills.motion import TARGET_PAD, Motion
    from zeno_skills.scene_geometry import Collider
    T = np.eye(4)
    T[:3, 3] = [1.0, 0.0, 0.76]
    tray = Collider("tray", "object:tray", "cuboid", "/tray", np.eye(4), dims=np.array([0.27, 0.2, 0.055]))
    m = Motion.__new__(Motion)
    m.by_owner = {"object:tray": [tray]}
    m.body_pose = {"/tray": T}
    m._corners = {"tray": Motion.box_corners(tray)}
    lo, hi = m._owner_box("object:tray")
    assert np.allclose(lo, [0.865, -0.1, 0.7325]) and np.allclose(hi, [1.135, 0.1, 0.7875])
    above = np.array([1.0, 0.0, hi[2] + TARGET_PAD + 0.02])          # place_above, T12
    assert m._targets_allow([above]) == set()
    assert m._targets_allow([np.array([1.0, 0.0, 0.77])]) == {"object:tray"}
