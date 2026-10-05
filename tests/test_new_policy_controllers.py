"""Numerical checks for the new dual-arm and moving-base controllers."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills.annotations import SceneAnnotations
from zeno_skills.collision import WorldModel
from zeno_skills.kinematics import ArmKin
from zeno_skills.policies import AtomicPolicy, PolicySuite
from zeno_skills.policies.bimanual import _fixed_torso_ik
from zeno_skills.policies.mobile import _path


NEW_ROUTES = (
    "prepare_floor_reach", "slide_to_edge", "grasp_articulated_handle",
    "release_articulated_handle", "pick_from_cavity", "open_revolute_door",
    "open_prismatic_drawer", "reach_while_moving", "pick_while_moving",
    "place_while_moving", "upright_object", "pick_cup_handle",
    "bimanual_flat_pick", "bimanual_box_lift", "bimanual_carry",
    "handover_right_to_left", "open_door_while_left_holds",
)


def test_all_seventeen_routes_bind_to_independent_policy_objects():
    suite = PolicySuite(SimpleNamespace())
    assert len(NEW_ROUTES) == 17
    assert all(isinstance(getattr(suite, name), AtomicPolicy) for name in NEW_ROUTES)


def test_left_arm_tcp_jacobian_matches_finite_difference():
    kin = ArmKin(side="left")
    q = np.clip(kin.rest + np.array([-0.12, 0.04, 0.08, 0.06, -0.04, -0.07, 0.05, 0.02, -0.03]),
                kin.lo+0.02, kin.hi-0.02)
    kin.set_base((1.2, -0.4, 0), 0.3)
    J, p, _ = kin.jac(q)
    assert np.allclose(p, kin.tcp(q)[0], atol=1e-10)
    eps = 1e-5
    for i in range(len(q)):
        moved = q.copy()
        moved[i] += eps
        numeric = (kin.tcp(moved)[0]-p)/eps
        assert np.allclose(J[:3, i], numeric, atol=3e-5)


def test_both_arms_have_clear_folded_pose_and_common_torso_solution():
    ann = SceneAnnotations("tasks/shelve_books/annotation.json")
    world = WorldModel(ann)
    right, left = ArmKin(), ArmKin(side="left")
    for kin in (right, left):
        kin.scene = world
        kin.set_base((-1.24, -6.758, 0.0), np.pi/2)
    world.right_kin, world.left_kin = right, left
    world.right_q, world.left_q = right.rest, left.rest
    world.left_active = True
    assert world.clearance(right, right.rest) > 0
    assert world.clearance(left, left.rest) > 0
    from zeno_skills.kinematics import gripper_rot
    R = gripper_rot([0, 1, 0], [0, 0, 1])
    seed = left.rest.copy()
    seed[:2] = [-0.15, 0.0]
    q = _fixed_torso_ik(left, np.array([-1.316, -6.478, 0.724]), R, seed)
    assert q is not None
    assert np.allclose(q[:2], seed[:2], atol=1e-5)
    assert np.linalg.norm(left.tcp(q)[0]-[-1.316, -6.478, 0.724]) < 0.01


def test_synchronized_motion_rejects_stationary_and_blocked_base_paths():
    world = SimpleNamespace(footprint_clear=lambda x, y, yaw: x <= 0.08)
    rig = SimpleNamespace(sync_world=lambda: None, world=world,
                          base_pose=lambda: (0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="at least 4 cm"):
        _path(rig, [(0.01, 0.0, 0.0)])
    with pytest.raises(Exception, match="crosses an obstacle"):
        _path(rig, [(0.1, 0.0, 0.0)])
