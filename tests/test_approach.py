"""Approach into a contact and leave out of one (docs/COLLISION_PLAN.md 3b item 2): the contact
segment's length from the collision model, the free motion before it planned with the fingers
to end straight along the approach; the park search checks each target with its own coll_kw."""

from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills.clearance import FREE_ELSE_STRAIGHT, LEAVE_CONTACT, into_contact
from zeno_skills.rig import LEAVE_MARGIN, Rig

DOWN = np.array([0.0, 0.0, -1.0])


class LineKin:
    """A TCP at height q[0] (x = y = 0); the robot touches the world below ``contact`` m."""

    def __init__(self, contact=0.02):
        self.scene, self.side, self.contact = object(), "right", contact
        self.motion = SimpleNamespace(robot_contacts=lambda rig: [], exempt=[])
        self.coll_kw = {"ignore_fingers": True}
        self.lines = []

    def tcp(self, q):
        return np.array([0.0, 0.0, float(q[0])]), np.eye(3)

    def ik_global(self, p, R, seeds=None):
        return np.full(9, float(p[2])), True

    def ik(self, p, R, q0):
        return np.full(9, float(p[2])), True

    def cart_path(self, q0, p, R, step=0.01):
        z0, z1 = float(q0[0]), float(p[2])
        if self.scene is not None:
            self.lines.append((round(z0, 4), round(z1, 4), dict(self.coll_kw)))
        n = max(1, int(round(abs(z1 - z0) / 0.002)))
        return [np.full(9, z0 + (z1 - z0) * k / n) for k in range(1, n + 1)], True

    def free(self, q):
        return float(q[0]) >= self.contact

    def near(self, q, gap):
        return float(q[0]) < self.contact


def _rig(kin, z=0.3, held=None):
    rig = SimpleNamespace(kin=kin, q_cmd=np.full(9, z), held=held, logged=[], motions=[], ran=[])
    rig.log = lambda ev, **kw: rig.logged.append((ev, kw))
    rig.clear = SimpleNamespace(motion=lambda label, allow: rig.motions.append((label, allow)),
                                planned=lambda label: None, fallback=lambda *a: None)
    rig._planning = lambda kin, start, keep_held=False: nullcontext()
    rig.sync_world = lambda: None
    rig._exit_length, rig._exits_contact, rig._dense = Rig._exit_length, Rig._exits_contact, Rig._dense
    for name in ("_approach_path", "_fingers_checked", "_ik_unchecked", "_line_unchecked", "_into_contact",
                 "_motion_path", "_start", "_carrying", "joint_path_via", "_move_path", "_goal", "_straight_move",
                 "_lifting", "_leave_contact", "_from_contact"):
        setattr(rig, name, getattr(Rig, name).__get__(rig))

    def follow(qs):
        rig.ran.append(list(qs))
        rig.q_cmd = np.asarray(qs[-1], float) if len(qs) else rig.q_cmd
    return rig, follow


def _approach(rig, follow, L=0.04):
    Rig._approach(rig, np.zeros(3), np.eye(3), (DOWN, L), 0.002, "pick_grasp", None,
                  into_contact(touch=("mug",)), FREE_ELSE_STRAIGHT, follow)


def test_an_approach_goes_to_its_line_start_then_straight_into_the_contact():
    kin = LineKin(contact=0.02)
    rig, follow = _rig(kin)
    _approach(rig, follow)
    (z0, z_s, kw0), (z_s2, z_c, kw1) = kin.lines
    assert z_c == pytest.approx(0.02 + LEAVE_MARGIN, abs=0.0021)       # a margin past the first clear point
    assert z_s == z_s2 == pytest.approx(0.04) and z0 == 0.3            # the last L straight, contact included
    for kw in (kw0, kw1):                                              # free space: fingers, the target too
        assert "ignore_fingers" not in kw and kw["exempt_targets"] is False
    assert kin.coll_kw == {"ignore_fingers": True}
    free, entry = rig.ran
    assert float(entry[0][0]) < z_c and float(entry[-1][0]) == 0.0     # then straight into the contact
    (l1, a1), (l2, a2) = rig.motions
    assert a1 is FREE_ELSE_STRAIGHT and a2.to_contact and a2.hand == "right" and a2.touch == ("mug",)
    ev = dict(rig.logged)["contact_entry"]
    assert ev["clear"] and ev["entry_m"] == pytest.approx(z_c, abs=1e-6)
    assert [kw["how"] for e, kw in rig.logged if e == "planned_leg"] == ["line_start"]


def test_a_contact_longer_than_the_approach_is_the_whole_straight_part():
    kin = LineKin(contact=0.04)
    rig, follow = _rig(kin)
    _approach(rig, follow)
    assert len(kin.lines) == 1 and kin.lines[0][1] == pytest.approx(0.05, abs=0.0021)   # planned to its start


def test_a_goal_clear_of_the_world_has_no_contact_segment():
    kin = LineKin(contact=-1.0)
    rig, follow = _rig(kin)
    _approach(rig, follow)
    assert kin.lines[-1][1] == 0.0 and len(rig.ran) == 1 and len(rig.motions) == 1


def test_on_the_approach_line_already_the_move_is_straight():
    kin = LineKin(contact=0.02)
    rig, follow = _rig(kin, z=0.035)                                   # within L of the goal, on the line
    _approach(rig, follow)
    assert len(kin.lines) == 1 and ("straight_leg", {"target": "pick_grasp", "exempt": []}) in rig.logged


def test_leaving_goes_along_the_direction_as_far_as_the_contact_lasts():
    kin = LineKin(contact=0.32)
    rig, follow = _rig(kin, z=0.30)
    rig.follow_smooth = lambda qs, spw: follow(qs)
    Rig.leave(rig, [0, 0, 1], "place_retreat", LEAVE_CONTACT)
    assert len(rig.ran) == 1 and float(rig.ran[0][-1][0]) == pytest.approx(0.32 + LEAVE_MARGIN, abs=0.0021)
    assert kin.coll_kw == {"ignore_fingers": True}
    ev = [kw for e, kw in rig.logged if e == "leave_contact_exit"][-1]
    assert ev["target"] == "place_retreat" and ev["clear"]


def test_the_park_chain_checks_each_target_with_its_own_coll_kw():
    from zeno_skills.planner import _chain
    seen = []
    kin = SimpleNamespace(coll_kw={"ignore_fingers": True})
    kin.ik_global = lambda p, R: (seen.append(("ik", dict(kin.coll_kw))) or (np.zeros(9), True))
    kin.cart_path = lambda q, p, R, step: (seen.append(("line", dict(kin.coll_kw))) or ([np.ones(9)], True))
    qs = _chain(kin, [(np.zeros(3), np.eye(3), {}), (np.ones(3), np.eye(3))], None)
    assert len(qs) == 2 and seen == [("ik", {}), ("line", {"ignore_fingers": True})]
    assert kin.coll_kw == {"ignore_fingers": True}


def test_the_carry_goal_set_spans_spots_heights_and_turns_in_the_base_frame():
    from zeno_skills.skills import CARRY_RISE, CARRY_SPOTS, CARRY_YAWS, _carry_goals
    goals, cost = _carry_goals((1.0, 2.0, 90.0), np.array([0.0, 0.0, 0.9]), np.eye(3), 0.7)
    assert len(goals) == len(CARRY_SPOTS) * 3 * CARRY_YAWS
    lx, ly = CARRY_SPOTS[0]
    assert np.allclose(goals[0][0], [1.0 - ly, 2.0 + lx, 0.7]) and cost[0] == 0.0     # yawed 90 deg
    assert sorted({round(float(p[2]), 3) for p, _ in goals}) == sorted([0.7, 0.9, round(0.7 + CARRY_RISE, 3)])


def test_a_lift_off_a_support_leaves_at_least_the_contact_gap_whatever_the_model_says():
    from zeno_skills.rig import LEAVE_GAP
    kin = LineKin(contact=-1.0)                                       # the model sees no contact at all
    rig, follow = _rig(kin, z=0.30)
    rig.follow_smooth = lambda qs, spw: follow(qs)
    Rig.leave(rig, [0, 0, 1], "pick_lift", LEAVE_CONTACT, lifts_off=True)
    assert float(rig.ran[0][-1][0]) == pytest.approx(0.30 + LEAVE_GAP + LEAVE_MARGIN, abs=0.0021)
