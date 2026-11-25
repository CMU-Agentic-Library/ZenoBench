"""An appliance's button pressed by the closed fingertips (docs/motion/MOTION_ARCHITECTURE.md section 6,
contact; 9.3 step 8): skill_plans.plan_press -- the reach to the straight's start, the straight in with only
the button touchable, the switch an action, the way back out measured, the tuck.  FakeKin: no simulator."""

import numpy as np
import pytest

from tests.test_door_plan import PlanKin
from zeno_skills.motion_state import Hand, Plan, State, chains
from zeno_skills.policies import MicrowaveButtonPressPolicy
from zeno_skills.rig import SkillFailure
from zeno_skills.skill_plans import PRESS_RELAY, PRESS_STAGES, plan_press
from zeno_skills.tolerances import LEAVE_GAP, LEAVE_MARGIN

BUTTON = "kitchen_microwave/start_button"
U = np.array([0.0, 1.0, 0.0])                  # the press goes in along +y
END = np.array([0.5, 0.4, 0.9])                # the TCP where the press ends
FACE_Y = END[1] - 0.003                        # the hand is near the button from here on (its tips on its face)


class PressKin(PlanKin):
    """PlanKin with the button's face to leave: the hand is near the world past FACE_Y - gap along y."""

    def near(self, q, gap):
        return q[1] > FACE_Y - gap


def _q(p):
    return np.r_[p, np.zeros(6)]


FOLD = _q([0.2, -0.2, 0.6])
RESTS = (FOLD, _q([0.1, -0.3, 0.4]))


def _press(toggle=("kitchen_microwave", True)):
    return {"button": BUTTON, "p": END, "R": np.eye(3), "u": U, "approach": 0.10, "toggle": toggle}


def _state(q=None):
    return State(base=(0.0, 0.0, 0.0), **chains(_q([0.3, -0.3, 1.0]) if q is None else q, np.zeros(7)),
                 hands={"right": Hand(width=0.04)})


def test_a_press_comes_straight_in_switches_and_backs_out_as_far_as_it_touches():
    kin = PressKin()
    plan = plan_press(kin, _state(), _press(), RESTS, prior={PRESS_RELAY: _q(END)})
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == [n for n in PRESS_STAGES if not n.startswith("press_door")]
    seg = {s.name: s for s in plan.segments}
    assert seg["press_close_hand"].action[:2] == ("grip", 0.0)
    assert np.allclose(seg["press_reach"].q_end[:3], END - 0.10 * U)     # the straight's start
    assert np.allclose(plan.decisions["press_reach"], seg["press_reach"].q_end)
    assert np.allclose(seg["press_in"].q_from, seg["press_reach"].q_end) and np.allclose(seg["press_in"].q_end[:3], END)
    assert (BUTTON,) in [tuple(n for n, _ in t) for t in kin.only]        # the fingers may touch it, the arm not
    assert seg["press_in"].spec.allow.touch == (BUTTON,)
    assert seg["press_toggle"].kind == "action" and seg["press_toggle"].action == ("toggle", "kitchen_microwave", True)
    leave = seg["press_leave"]
    way = leave.q_end[:3] - leave.q_from[:3]
    assert np.allclose(way / np.linalg.norm(way), -U)                    # straight back out
    assert leave.info["length"] == pytest.approx(0.003 + LEAVE_GAP + LEAVE_MARGIN, abs=0.004)
    assert np.allclose(seg["tuck"].q_from, leave.q_end) and np.allclose(seg["tuck"].q_end, FOLD)
    assert all(s.info.get("side") == "right" for s in plan.segments)


def test_a_press_that_switches_nothing_has_no_toggle_and_a_rebuild_starts_where_asked():
    kin = PressKin()
    plan = plan_press(kin, _state(), _press(toggle=None), RESTS)
    assert "press_toggle" not in [s.name for s in plan.segments]
    at_end = plan_press(kin, _state(_q(END)), _press(), RESTS, start="press_pressed")
    assert [s.name for s in at_end.segments] == ["press_pressed", "press_leave", "tuck"]


class Clear:
    """A BaseModel whose base collides with the door from ``blocked_from`` on (None: never)."""

    def __init__(self, blocked_from=None):
        self.blocked_from, self.asked = blocked_from, []

    def clear(self, state, poses):
        v = state.parts["kitchen_microwave"]
        self.asked.append(v)
        return [self.blocked_from is None or v < self.blocked_from]


def test_a_door_key_drives_the_door_only_where_the_robot_is_clear_of_its_swing():
    press = dict(_press(toggle=None), door={"part": "kitchen_microwave", "to": 1.4})
    st = State(base=(0.0, 0.0, 0.0), **chains(_q([0.3, -0.3, 1.0]), np.zeros(7)), hands={"right": Hand(width=0.04)},
               parts={"kitchen_microwave": 0.0})
    base = Clear()
    plan = plan_press(PressKin(), st, press, RESTS, base=base)
    assert isinstance(plan, Plan), plan
    seg = {s.name: s for s in plan.segments}
    assert [s.name for s in plan.segments][-3:] == ["tuck", "press_door", "press_door_moved"]
    assert seg["press_door"].action == ("drive_part", "kitchen_microwave", 1.4)
    assert seg["press_door_moved"].info["assumed"].parts["kitchen_microwave"] == pytest.approx(1.4)
    assert base.asked[0] == 0.0 and base.asked[-1] == pytest.approx(1.4) and len(base.asked) >= 15   # every 0.1 rad
    out = plan_press(PressKin(), st, press, RESTS, base=Clear(blocked_from=0.75))
    assert not isinstance(out, Plan) and out.segment == "press_door" and "base is in its way at 0.80" in out.why


def test_the_staged_press_policies_are_retired():
    with pytest.raises(SkillFailure, match="retired"):
        MicrowaveButtonPressPolicy(object()).execute("kitchen_microwave", button="start")
