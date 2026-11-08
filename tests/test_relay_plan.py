"""A relay pose entered straight (COLLISION_PLAN 6.2): the park search and the execution make the
motion the same way (rig.relay_approach) -- the straight checked from where the leg to its start
really ends -- and the execution runs the search's plan while it still holds (Rig._plan_off)."""

from types import SimpleNamespace

import numpy as np

from zeno_skills.rig import HINT_REACH, PLAN_AT_START, Rig, relay_approach


class FakeKin:
    """TCP = q[:3], orientation fixed; a straight TCP line ends at q with q[:3] = the goal and
    q[3] the start's; the planner ends its leg on the solution ``plan_end`` (q[3] = 1: another one)."""

    def __init__(self, straight_ok=True, plan_end=1.0, line_ok_from=None, free=True):
        self.scene, self.straight_ok, self.plan_end = object(), straight_ok, plan_end
        self.line_ok_from, self.free_now = line_ok_from, free
        self.calls = []

    def tcp(self, q):
        return np.asarray(q, float)[:3].copy(), np.eye(3)

    def cart_path(self, q0, p, R, step=0.01):
        q0 = np.asarray(q0, float)
        self.calls.append(("cart_path", tuple(np.round(q0, 3)), tuple(np.round(p, 3)), self.scene is not None))
        q = q0.copy()
        q[:3] = p
        to_start = not np.allclose(p, GOAL)
        if to_start:
            return ([q], True) if self.straight_ok else ([], False)
        ok = self.line_ok_from is None or np.isclose(q0[3], self.line_ok_from)
        return ([q], True) if ok else ([], False)

    def plan_to(self, q0, p, R, carry=False, q_goal=None):
        self.calls.append(("plan_to", carry))
        q = np.asarray(q0, float).copy()
        q[:3], q[3] = p, self.plan_end
        return [q], "pose"

    def path_free(self, qs):
        return self.free_now


GOAL = np.array([1.0, 0.0, 0.5])
DOWN = np.array([0.0, 0.0, -1.0])


def test_the_straight_is_checked_from_where_the_planned_leg_ends():
    kin = FakeKin(straight_ok=False, plan_end=1.0, line_ok_from=0.0)
    plan, why = relay_approach(kin, np.zeros(9), GOAL, np.eye(3), DOWN, 0.05, carry=True)
    # the planner ended on another solution (q[3] = 1): the straight from there is the one checked
    assert plan is None and "straight" in why
    assert ("plan_to", True) in kin.calls
    line_starts = [c[1] for c in kin.calls if c[0] == "cart_path" and np.allclose(c[2], GOAL)]
    assert line_starts and all(s[3] == 1.0 for s in line_starts)


def test_a_plan_keeps_its_legs():
    kin = FakeKin(straight_ok=False, plan_end=0.0)
    plan, why = relay_approach(kin, np.zeros(9), GOAL, np.eye(3), DOWN, 0.05)
    assert why is None and plan["how"] == "planned"
    assert np.allclose(plan["free"][-1][:3], GOAL + 0.05 * np.array([0, 0, 1]))
    assert np.allclose(plan["line"][-1][:3], GOAL)


def test_on_the_straight_already_no_leg_to_its_start():
    q0 = np.zeros(9)
    q0[:3] = GOAL + np.array([0, 0, 0.02])            # 2 cm up the 5 cm set-down straight
    kin = FakeKin()
    plan, _ = relay_approach(kin, q0, GOAL, np.eye(3), DOWN, 0.05)
    assert plan["free"] == [] and len(plan["line"]) == 1
    assert not any(c[0] == "plan_to" for c in kin.calls)


def _rig(kin, q_cmd):
    rig = SimpleNamespace(kin=kin, q_cmd=np.asarray(q_cmd, float))
    rig._plan_off = Rig._plan_off.__get__(rig)
    return rig


def _plan(q_from):
    end = np.zeros(9)
    end[:3] = GOAL
    return {"q_from": np.asarray(q_from, float), "free": [end + [0, 0, 0.05, 0, 0, 0, 0, 0, 0]], "line": [end],
            "how": "planned"}


def test_the_search_plan_is_run_as_it_is_while_it_holds():
    rig = _rig(FakeKin(), np.zeros(9))
    assert rig._plan_off(_plan(np.zeros(9)), GOAL, np.eye(3)) is None


def test_the_search_plan_does_not_hold_when_anything_it_was_made_for_changed():
    plan = _plan(np.zeros(9))
    q_off = np.zeros(9)
    q_off[4] = 2 * PLAN_AT_START
    assert "arm" in _rig(FakeKin(), q_off)._plan_off(plan, GOAL, np.eye(3))
    assert "off the target" in _rig(FakeKin(), np.zeros(9))._plan_off(plan, GOAL + [2 * HINT_REACH, 0, 0], np.eye(3))
    assert "collides" in _rig(FakeKin(free=False), np.zeros(9))._plan_off(plan, GOAL, np.eye(3))
    assert _rig(FakeKin(), np.zeros(9))._plan_off(None, GOAL, np.eye(3)) == "no plan"
