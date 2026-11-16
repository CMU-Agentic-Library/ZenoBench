"""The robot's own base as a second environment of the world checker (zeno_skills.body_collision,
scene_geometry.body_world; docs/MOTION_ARCHITECTURE.md 4.4): which spheres are switched off against it,
its boxes from the base planner's shapes, the switch-off itself.  The GPU side: tools/check_body_collision.py."""

import numpy as np
import pytest

from zeno_skills import body_collision as B
from zeno_skills import collision as C
from zeno_skills import scene_geometry as G


def test_the_body_and_the_other_arm_are_off_against_the_base_this_arm_and_its_load_are_not():
    links = {"torso_lift_link", "torso_link", "head_yaw_link", "head_link", "stereo_camera_link",
             "right_arm_link_1", "right_gripper_link", "right_gripper_left_finger_link", "right_held_object",
             "left_arm_link_7", "left_gripper_link", "left_held_object"}
    off = B.off_links(links, "right")
    assert off == set(B.BODY_LINKS) | {"left_arm_link_7", "left_gripper_link", "left_held_object"}
    assert B.off_links(links, "left") == set(B.BODY_LINKS) | {"right_arm_link_1", "right_gripper_link",
                                                              "right_gripper_left_finger_link", "right_held_object"}


def test_the_base_boxes_are_the_base_planners_two_layers():
    boxes = {n: (ctr, dims) for n, ctr, dims in G._body_boxes()}
    ctr, dims = boxes[G.BODY_COLUMN]
    x0, y0, x1, y1 = C.COLUMN_XY
    assert np.allclose(ctr[:2], [(x0 + x1) / 2, (y0 + y1) / 2]) and np.allclose(dims[:2], [x1 - x0, y1 - y0])
    assert ctr[2] - dims[2] / 2 == pytest.approx(C.LOW_TOP) and ctr[2] + dims[2] / 2 == pytest.approx(C.COLUMN_TOP)
    chassis = [(c, d) for n, c, d in G._body_boxes() if n.startswith(G.BODY_CHASSIS)]
    assert len(chassis) == len(G.BODY_ARC_STEPS)
    c, r = C.BASE_HALF - C.LOW_CORNER, C.LOW_CORNER
    for (ctr, (dx, dy, dz)), a in zip(chassis, G.BODY_ARC_STEPS):
        assert np.allclose(ctr[:2], 0.0) and dz == pytest.approx(C.LOW_TOP - C.LOW_BOTTOM)
        # each rectangle's corner on its corner arc: inside the rounded square, never beyond it
        assert np.hypot(dx / 2 - c, dy / 2 - c) == pytest.approx(r)
        assert max(dx, dy) / 2 == pytest.approx(C.BASE_HALF) or 0 < a < 90


def test_the_base_moves_with_the_base_pose():
    T = G._base_T((2.0, 1.0, 90.0))
    ctr, _ = dict((n, (c, d)) for n, c, d in G._body_boxes())[G.BODY_COLUMN]
    world = G._at(T, ctr)[:3, 3]
    assert np.allclose(world[:2], [2.0 - ctr[1], 1.0 + ctr[0]])


def test_a_switched_off_sphere_gets_a_negative_radius_and_the_rest_keep_theirs_and_their_gradient():
    torch = pytest.importorskip("torch")
    s = torch.tensor([[[[0.0, 0.0, 0.5, 0.05], [0.1, 0.0, 0.5, 0.04], [0.2, 0.0, 0.5, 0.03]]]], requires_grad=True)
    m = B.masked(s, torch.tensor([False, True, False]))
    assert m[..., 1, 3].item() == -1.0 and m[..., 0, 3].item() == pytest.approx(0.05)
    assert torch.equal(m[..., :3], s[..., :3])
    m[..., 0, 3].sum().backward()
    assert s.grad[0, 0, 0, 3].item() == 1.0 and s.grad[0, 0, 1, 3].item() == 0.0


def test_the_base_query_takes_only_the_spheres_left_on():
    torch = pytest.importorskip("torch")
    mask = torch.tensor([True, False, True, False])
    assert B.kept(mask).tolist() == [1, 3]
    s = torch.arange(2 * 1 * 4 * 4, dtype=torch.float32).view(2, 1, 4, 4)
    assert torch.equal(s.index_select(-2, B.kept(mask)), s[:, :, [1, 3]])
