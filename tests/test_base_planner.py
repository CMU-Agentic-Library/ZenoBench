"""Whole-body base planner on a lattice of (x, y, yaw) with posture modes (zeno_skills/base_planner.py)."""

import math

import numpy as np

from zeno_skills import base_planner as bp


def _sets(*ids):
    """Sphere sets standing for postures: set p is recognised by its id in [p, 0, 0]."""
    return np.array([[[float(i), 0.0, 0.0, 0.1]] for i in ids])


def _oracle(blocked):
    """depths(poses, sets) from blocked(x, y, yaw_rad, posture_id) -> penetration m."""
    def depths(poses, sets):
        return np.array([[blocked(x, y, yaw, int(s[0, 0])) for x, y, yaw in poses] for s in sets])
    return depths


def _drives(steps):
    return [p for st in steps if st.kind == "drive" for p in st.path]


def test_open_floor_drives_to_the_exact_goal():
    steps, lat = bp.plan(_oracle(lambda *a: 0.0), (0.0, 0.0, 0.0), (1.0, 0.3, 30.0), _sets(0), [], [1.0])
    assert [st.kind for st in steps] == ["drive"]
    assert steps[0].path[0] == (0.0, 0.0, 0.0) and steps[0].path[-1] == (1.0, 0.3, 30.0)
    assert len(steps[0].path) <= 4                     # shortcut to a few waypoints


def test_a_wall_is_passed_through_its_gap_only():
    wall = lambda x, y, yaw, p: 0.05 if 0.45 <= x <= 0.55 and not 0.35 <= y <= 0.65 else 0.0
    steps, lat = bp.plan(_oracle(wall), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), _sets(0), [], [1.0])
    path = _drives(steps)
    crossing = [p for a, b in zip(path[:-1], path[1:]) for p in [a, b] if a[0] < 0.5 <= b[0]]
    assert crossing
    for a, b in zip(path[:-1], path[1:]):
        if a[0] < 0.5 <= b[0]:
            u = (0.5 - a[0]) / (b[0] - a[0])
            assert 0.35 <= a[1] + u * (b[1] - a[1]) <= 0.65


def test_the_posture_switches_where_it_is_clear_and_late_when_the_arrival_posture_costs_more():
    # posture 1 (tucked) collides for x < 0.6; along the switch (ids 10..) the same
    blocked = lambda x, y, yaw, p: 0.05 if p >= 1 and x < 0.6 else 0.0
    sets = _sets(0, 1)
    switches = [_sets(*[10 + k for k in range(bp.SWITCH_SAMPLES)])]
    steps, lat = bp.plan(_oracle(blocked), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), sets, switches, [1.0, 1.5])
    kinds = [st.kind for st in steps]
    assert kinds == ["drive", "switch", "drive"] or kinds == ["drive", "switch"]
    sw = next(st for st in steps if st.kind == "switch")
    assert sw.mode == 0 and sw.path[0][0] >= 0.6 - 1e-9


def test_without_a_goal_the_nearest_pose_where_the_switch_is_clear():
    blocked = lambda x, y, yaw, p: 0.05 if p >= 10 and math.hypot(x, y) < 0.3 else 0.0
    switches = [_sets(*[10 + k for k in range(bp.SWITCH_SAMPLES)])]
    steps, lat = bp.plan(_oracle(blocked), (0.0, 0.0, 0.0), None, _sets(0, 1), switches, [1.0, 1.0])
    sw = next(st for st in steps if st.kind == "switch")
    assert 0.3 <= math.hypot(*sw.path[0][:2]) <= 0.4
    assert steps[-1].kind == "switch"                  # nothing to drive after it


def test_the_start_posture_may_not_sink_deeper_than_where_it_starts():
    # touching 1 cm at the start, deeper towards +x, clear towards -x
    depth = lambda x, y, yaw, p: max(0.0, 0.01 + 0.05 * x)
    steps, lat = bp.plan(_oracle(depth), (0.0, 0.0, 0.0), (-0.5, 0.0, 0.0), _sets(0), [], [1.0])
    assert steps is not None and abs(lat.tol0 - 0.01) < 1e-9
    steps, lat = bp.plan(_oracle(depth), (0.0, 0.0, 0.0), (0.3, 0.0, 0.0), _sets(0), [], [1.0])
    assert steps is None


def test_a_goal_pose_that_collides_in_the_arrival_posture_has_no_plan():
    blocked = lambda x, y, yaw, p: 0.02 if p == 1 and x > 0.9 else 0.0
    switches = [_sets(*[10 + k for k in range(bp.SWITCH_SAMPLES)])]
    steps, lat = bp.plan(_oracle(blocked), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), _sets(0, 1), switches, [1.0, 1.0])
    assert steps is None and "goal" in lat.why


def test_the_low_footprint_blocks_like_the_world_but_not_where_the_robot_stands():
    # the start pose's footprint is tight (exempt), a band at x in [0.3, 0.4] is closed below 0.35 m
    low = lambda poses: ~((poses[:, 0] >= 0.3) & (poses[:, 0] <= 0.4) & (np.abs(poses[:, 1]) < 0.5)) & \
        ~((np.abs(poses[:, 0]) < 1e-9) & (np.abs(poses[:, 1]) < 1e-9))
    steps, lat = bp.plan(_oracle(lambda *a: 0.0), (0.0, 0.0, 0.0), (0.8, 0.0, 0.0), _sets(0), [], [1.0], footprint=low)
    assert steps is not None
    path = _drives(steps)
    for a, b in zip(path[:-1], path[1:]):
        if a[0] < 0.35 <= b[0]:
            u = (0.35 - a[0]) / (b[0] - a[0])
            assert abs(a[1] + u * (b[1] - a[1])) >= 0.5 - 1e-6
