"""Held-object spheres for carry planning (motion.box_spheres / add_held_links)."""

import copy

import numpy as np
import yaml

from zeno_skills.motion import HELD_SPHERES, ROBOT_CFG, add_held_links, box_spheres, held_link


def test_box_spheres_fill_the_box_and_stay_inside():
    for d in [(0.25, 0.25, 0.07), (0.2, 0.15, 0.03), (0.4, 0.05, 0.05), (0.07, 0.07, 0.12), (0.5, 0.01, 0.01)]:
        half = np.array(d) / 2
        b = box_spheres(-half, half)
        assert 1 <= len(b) <= HELD_SPHERES
        assert np.all(np.abs(b[:, :3]) + b[:, 3:4] <= half + 1e-9)
        # the long axis is covered end to end
        assert np.ptp(b[:, :3], axis=0)[np.argmax(d)] + 2 * b[0, 3] >= 0.8 * d[np.argmax(d)]


def test_box_spheres_offset_box():
    b = box_spheres([1.0, 2.0, 3.0], [1.1, 2.1, 3.1])
    assert np.all(b[:, :3] > [1.0, 2.0, 3.0]) and np.all(b[:, :3] < [1.1, 2.1, 3.1])


def test_held_links_on_the_tcp_and_out_of_self_collision():
    k = copy.deepcopy(yaml.safe_load(open(ROBOT_CFG))["robot_cfg"]["kinematics"])
    links = list(k["collision_link_names"])
    add_held_links(k)
    for s in ("right", "left"):
        h = held_link(s)
        assert k["extra_links"][h]["parent_link_name"] == k["extra_links"][f"{s}_tcp"]["parent_link_name"]
        assert k["extra_links"][h]["fixed_transform"] == k["extra_links"][f"{s}_tcp"]["fixed_transform"]
        assert k["extra_collision_spheres"][h] == HELD_SPHERES
        assert h in k["collision_link_names"]
        assert set(k["self_collision_ignore"][h]) >= set(links)
    assert k["mesh_link_names"] == links        # the yaml alias is not extended
