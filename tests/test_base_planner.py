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
    steps, lat = bp.plan(_oracle(lambda *a: 0.0), (0.0, 0.0, 0.0), (1.0, 0.3, 30.0), _sets(0), [])
    assert [st.kind for st in steps] == ["drive"]
    assert steps[0].path[0] == (0.0, 0.0, 0.0) and steps[0].path[-1] == (1.0, 0.3, 30.0)
    assert len(steps[0].path) <= 4                     # shortcut to a few waypoints


def test_a_wall_is_passed_through_its_gap_only():
    wall = lambda x, y, yaw, p: 0.05 if 0.45 <= x <= 0.55 and not 0.35 <= y <= 0.65 else 0.0
    steps, lat = bp.plan(_oracle(wall), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), _sets(0), [])
    path = _drives(steps)
    crossing = [p for a, b in zip(path[:-1], path[1:]) for p in [a, b] if a[0] < 0.5 <= b[0]]
    assert crossing
    for a, b in zip(path[:-1], path[1:]):
        if a[0] < 0.5 <= b[0]:
            u = (0.5 - a[0]) / (b[0] - a[0])
            assert 0.35 <= a[1] + u * (b[1] - a[1]) <= 0.65


def test_the_posture_switches_where_it_is_clear():
    # posture 1 (tucked) collides for x < 0.6; along the switch (ids 10..) the same
    blocked = lambda x, y, yaw, p: 0.05 if p >= 1 and x < 0.6 else 0.0
    sets = _sets(0, 1)
    switches = [_sets(*[10 + k for k in range(bp.SWITCH_SAMPLES)])]
    steps, lat = bp.plan(_oracle(blocked), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), sets, switches)
    kinds = [st.kind for st in steps]
    assert kinds == ["drive", "switch", "drive"] or kinds == ["drive", "switch"]
    sw = next(st for st in steps if st.kind == "switch")
    assert sw.mode == 0 and sw.path[0][0] >= 0.6 - 1e-9


def test_without_a_goal_the_nearest_pose_where_the_switch_is_clear():
    blocked = lambda x, y, yaw, p: 0.05 if p >= 10 and math.hypot(x, y) < 0.3 else 0.0
    switches = [_sets(*[10 + k for k in range(bp.SWITCH_SAMPLES)])]
    steps, lat = bp.plan(_oracle(blocked), (0.0, 0.0, 0.0), None, _sets(0, 1), switches)
    sw = next(st for st in steps if st.kind == "switch")
    assert 0.3 <= math.hypot(*sw.path[0][:2]) <= 0.4
    assert steps[-1].kind == "switch"                  # nothing to drive after it


def test_the_start_posture_may_not_sink_deeper_than_where_it_starts():
    # touching 1 cm at the start, deeper towards +x, clear towards -x
    depth = lambda x, y, yaw, p: max(0.0, 0.01 + 0.05 * x)
    steps, lat = bp.plan(_oracle(depth), (0.0, 0.0, 0.0), (-0.5, 0.0, 0.0), _sets(0), [])
    assert steps is not None and abs(lat.tol0 - 0.01) < 1e-9
    steps, lat = bp.plan(_oracle(depth), (0.0, 0.0, 0.0), (0.3, 0.0, 0.0), _sets(0), [])
    assert steps is None


def test_a_goal_pose_that_collides_in_the_arrival_posture_has_no_plan():
    blocked = lambda x, y, yaw, p: 0.02 if p == 1 and x > 0.9 else 0.0
    switches = [_sets(*[10 + k for k in range(bp.SWITCH_SAMPLES)])]
    steps, lat = bp.plan(_oracle(blocked), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), _sets(0, 1), switches)
    assert steps is None and "goal" in lat.why


def test_the_low_footprint_blocks_like_the_world_but_not_where_the_robot_stands():
    # the start pose's footprint is tight (exempt), a band at x in [0.3, 0.4] is closed below 0.35 m
    low = lambda poses: ~((poses[:, 0] >= 0.3) & (poses[:, 0] <= 0.4) & (np.abs(poses[:, 1]) < 0.5)) & \
        ~((np.abs(poses[:, 0]) < 1e-9) & (np.abs(poses[:, 1]) < 1e-9))
    steps, lat = bp.plan(_oracle(lambda *a: 0.0), (0.0, 0.0, 0.0), (0.8, 0.0, 0.0), _sets(0), [], footprint=low)
    assert steps is not None
    path = _drives(steps)
    for a, b in zip(path[:-1], path[1:]):
        if a[0] < 0.35 <= b[0]:
            u = (0.35 - a[0]) / (b[0] - a[0])
            assert abs(a[1] + u * (b[1] - a[1])) >= 0.5 - 1e-6


def test_a_tight_goal_off_the_lattice_is_reached_from_a_neighbouring_node():
    # a park 2 cm short of a wall (x > 0.995): its nearest lattice node (x = 1.00) is inside the wall,
    # the exact goal and the node before it (x = 0.95) are clear
    wall = lambda x, y, yaw, p: 0.01 if x > 0.995 else 0.0
    steps, lat = bp.plan(_oracle(wall), (0.0, 0.0, 0.0), (0.98, 0.0, 0.0), _sets(0), [])
    assert steps is not None and steps[-1].path[-1] == (0.98, 0.0, 0.0)


def _executed(path, reach_step=0.001):
    """Every pose Rig.drive_base passes along ``path`` (straight x, y, yaw between waypoints, the
    yaw the short way), at most 1 mm / 0.1 deg apart."""
    out = []
    for a, b in zip(path[:-1], path[1:]):
        a = np.array([a[0], a[1], math.radians(a[2])])
        b = np.array([b[0], b[1], math.radians(b[2])])
        b[2] = a[2] + (b[2] - a[2] + math.pi) % (2 * math.pi) - math.pi
        n = int(max(math.hypot(*(b[:2] - a[:2])) / reach_step, abs(b[2] - a[2]) / math.radians(0.1))) + 2
        out += list(a + (b - a) * np.linspace(0, 1, n)[:, None])
    return np.array(out)


def test_a_wall_thinner_than_a_cell_is_not_driven_through_between_nodes():
    # the wall sits between the lattice columns x = 0.50 and 0.55: every node is clear, the edge is not
    wall = lambda x, y, yaw, p: 0.05 if 0.515 <= x <= 0.535 and not 0.35 <= y <= 0.65 else 0.0
    steps, lat = bp.plan(_oracle(wall), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), _sets(0), [])
    assert steps is not None
    for x, y, yaw in _executed(_drives(steps)):
        assert wall(x, y, yaw, 0) == 0.0


def test_a_turn_does_not_sweep_the_hand_through_a_post_between_two_headings():
    # the hand 0.7 m ahead of the base centre; a post where the hand is at 7.5 deg, between the
    # 0 and 15 deg lattice headings: turning in place from 0 to 30 deg the short way hits it
    hand = np.array([[[0.7, 0.0, 0.0, 0.03]]])
    post = (0.7 * math.cos(math.radians(7.5)), 0.7 * math.sin(math.radians(7.5)))

    def depths(poses, sets):
        hx = poses[:, 0] + 0.7 * np.cos(poses[:, 2])
        hy = poses[:, 1] + 0.7 * np.sin(poses[:, 2])
        return np.where(np.hypot(hx - post[0], hy - post[1]) < 0.04, 0.02, 0.0)[None].repeat(len(sets), 0)

    steps, lat = bp.plan(depths, (0.0, 0.0, 0.0), (0.0, 0.0, 30.0), hand, [])
    assert steps is not None and lat.rounds >= 1
    poses = _executed(_drives(steps))
    assert not np.any(depths(poses, hand)[0] > 0)


def test_dense_sets_keep_the_ends_and_a_set_every_dense_step():
    fine = np.zeros((65, 1, 4))
    fine[:, 0, 0] = np.linspace(0.0, 0.3, 65)              # one sphere sliding 0.3 m
    kept = bp.dense_sets(fine)
    assert kept[0, 0, 0] == 0.0 and kept[-1, 0, 0] == 0.3
    assert np.all(np.diff(kept[:, 0, 0]) <= bp.DENSE + 1e-9)
    assert len(kept) < len(fine)
