"""A held spoon stirred round inside a pot (docs/MOTION_ARCHITECTURE.md section 6, contact; docs/skills/stir.md):
skill_plans.plan_stir -- the free leg over the pot with the spoon tilted (its tilt not held: a tool turned on
purpose), the dip straight down, the circle a task segment in the pot's frame checked whole, the leave back up,
back to the posture it arrived in.  FakeKin: no simulator."""

import numpy as np
import pytest

from tests.test_door_plan import PlanKin
from zeno_skills.motion_state import Hand, Held, Plan, State, chains, touch_entries
from zeno_skills.skill_plans import STIR_RELAY, STIR_STAGES, plan_stir, stir_tcp

POT, SPOON, TOMATO = "handled_cooking_pot", "breakfast_spoon", "cherry_tomato_1"
AT = np.array([0.6, -0.2, 0.8])                # the pot's box frame origin (upright)
C = np.array([0.0, 0.0, 0.05])                 # the tip's circle centre in that frame
T_TOOL = np.array([0.1, 0.0, -0.05])           # the tip in the TCP frame
R_ = 0.03                                      # the circle's radius
ABOVE = 0.09                                   # the dip's straight


def _T(p):
    T = np.eye(4)
    T[:3, 3] = p
    return T


def _q(p):
    return np.r_[p, np.zeros(6)]


CARRY = _q([0.3, -0.3, 1.0])                   # the posture it arrives in (the carry)


def _stir(turns=1.25, r=R_):
    return {"pot": POT, "c": C, "r": r, "R": np.eye(3), "t_tool": T_TOOL, "turns": turns, "above": ABOVE,
            "touch": (POT, TOMATO)}


def _state(q=CARRY, held=True):
    return State(base=(0.0, 0.0, 0.0), **chains(q, np.zeros(7)),
                 hands={"right": Hand(width=0.008, held=Held(SPOON, np.eye(4)) if held else None)},
                 objects={POT: _T(AT)})


def _tcp_at(a, r=R_):
    return AT + C + r * np.array([np.cos(a), np.sin(a), 0.0]) - T_TOOL


def test_a_stir_reaches_over_the_pot_dips_circles_in_its_frame_leaves_and_goes_back():
    kin = PlanKin()
    plan = plan_stir(kin, _state(), _stir(), prior={STIR_RELAY: _q(_tcp_at(0.0) + [0, 0, ABOVE])})
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == list(STIR_STAGES)
    seg = {s.name: s for s in plan.segments}
    assert np.allclose(seg["stir_reach"].q_end[:3], _tcp_at(0.0) + [0.0, 0.0, ABOVE])
    assert np.allclose(seg["stir_dip"].q_end[:3], _tcp_at(0.0))
    circle = seg["stir_circle"]
    assert circle.kind == "scripted" and circle.info["executor"] == "follow"
    assert circle.target == ("s", pytest.approx(2 * np.pi * 1.25))
    assert np.allclose(circle.q_end[:3], _tcp_at(2 * np.pi * 1.25))                 # a quarter past a whole turn
    tips = [kin.tcp(q)[0] + T_TOOL for q in circle.qs]                              # the tip stays on the circle
    assert all(abs(np.linalg.norm(t[:2] - AT[:2]) - R_) < 1e-3 and abs(t[2] - (AT + C)[2]) < 1e-9 for t in tips)
    assert np.allclose(seg["stir_leave"].q_end[:3], _tcp_at(2 * np.pi * 1.25) + [0.0, 0.0, ABOVE])
    assert np.allclose(seg["stir_back"].q_end, CARRY) and np.allclose(plan.decisions["stir_back"], CARRY)
    # in the pot the spoon (the fingers and the held link) may touch the pot and what is in it, the arm not
    for name in ("stir_dip", "stir_circle", "stir_leave"):
        assert seg[name].spec.touch == ((POT, "held"), (TOMATO, "held"))
        assert seg[name].spec.allow.held_on == (POT, TOMATO)
    assert ((POT, "held"), (TOMATO, "held")) in kin.only
    # the free legs carry the spoon without holding its tilt (the tilt rule is a carry's, not a tool's)
    assert not seg["stir_reach"].spec.hold_tilt and not seg["stir_back"].spec.hold_tilt
    assert seg["stir_reach"].info["aim"].obj == POT and seg["stir_dip"].info["aim"].obj == POT
    assert all(s.info.get("side") == "right" for s in plan.segments)


def test_a_dip_has_no_circle():
    plan = plan_stir(PlanKin(), _state(), _stir(turns=0.0))
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == [n for n in STIR_STAGES if n != "stir_circle"]
    leave = next(s for s in plan.segments if s.name == "stir_leave")
    assert np.allclose(leave.q_end[:3], _tcp_at(0.0) + [0.0, 0.0, ABOVE])


def test_a_circle_the_arm_cannot_make_free_all_round_fails_the_plan_none_of_it_skipped():
    # something in the way at the far side of the circle: the old stir skipped such points and counted on
    kin = PlanKin(blocked=lambda st, q: q[0] < (_tcp_at(np.pi))[0] + 0.005)
    plan = plan_stir(kin, _state(), _stir())
    assert not isinstance(plan, Plan) and plan.segment == "stir_circle" and "collides" in plan.why


def test_rebuilt_after_the_circle_it_still_goes_back_to_where_it_arrived():
    kin = PlanKin()
    first = plan_stir(kin, _state(), _stir())
    here = _q(_tcp_at(2 * np.pi * 1.25))
    plan = plan_stir(kin, _state(q=here), _stir(), start="stir_leave", prior=first)
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == ["stir_leave", "stir_back"]
    assert np.allclose(plan.segments[-1].q_end, CARRY)


def test_nothing_in_the_hand_fails_the_plan():
    plan = plan_stir(PlanKin(), _state(held=False), _stir())
    assert not isinstance(plan, Plan) and "nothing in the hand" in plan.why


def test_the_circle_is_level_in_a_turned_pot_frame():
    # the pot's frame turned 90 deg about x: the world's x and y written in it keep the circle level
    Rx = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])
    stir = {**_stir(), "axes": (Rx.T @ [1.0, 0.0, 0.0], Rx.T @ [0.0, 1.0, 0.0])}
    pts = [(Rx @ stir_tcp(stir, a)[:3, 3]) for a in np.linspace(0, 2 * np.pi, 9)]
    assert np.ptp([p[2] for p in pts]) < 1e-12


def test_held_is_a_touch_link():
    assert touch_entries(((POT, "held"), TOMATO)) == ((POT, "held"), (TOMATO, "fingers"))
