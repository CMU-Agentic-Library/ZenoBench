"""Opening a door by its handle (docs/MOTION_ARCHITECTURE.md section 6, open / close):
skill_plans.plan_door -- one grasp, the base riding the part, one release -- and the failure exit
letting go of a handle.  FakeKin: no simulator."""

import numpy as np
import pytest

from tests.test_scripted import DOOR, DoorKin, FakeBase, door_pose
from zeno_skills import primitives as P
from zeno_skills.motion_state import Failure, Hand, Held, Plan, Segment, State, holding, with_part
from zeno_skills.skill_plans import DOOR_RELAY, DOOR_STAGES, plan_clear, plan_door
from zeno_skills.tolerances import DOOR_LEAVE


class PlanKin(DoorKin):
    """DoorKin for whole plans: nothing near the world (a contact exit is empty), every straight joint
    move free, IK the seed itself."""

    def near(self, q, gap):
        return False

    def segment_free(self, qa, qb):
        return self.free(qa) and self.free(qb)

    def ik_global(self, p, R, seeds=()):
        q = np.asarray(seeds[0], float).copy()
        q[:3] = p
        return q, True


HANDLE = np.array([0.6, -0.3, 0.9])           # the handle at the closed door (part frame = world at 0)


def _grip(s1=0.62):
    T = np.eye(4)
    T[:3, 3] = HANDLE
    return {"part": DOOR, "kind": "hinge", "pose": door_pose, "T_part_tcp": T, "u": np.array([1.0, 0.0, 0.0]),
            "L": 0.12, "pre_open": 0.04, "s1": s1, "ride_step": 0.2,
            "track": {"lead": 0.03, "rate": 0.25, "done": s1 - 0.04}}


def _q(p):
    return np.r_[p, np.zeros(6)]


PRE = _q(HANDLE - [0.12, 0.0, 0.0])
FOLD = _q([0.2, -0.2, 0.6])
RESTS = (FOLD, _q([0.1, -0.3, 0.4]))


def _state(q=None, door=0.0, held=None):
    return State(base=(0.0, 0.0, 0.0), q_right=_q([0.3, -0.3, 0.7]) if q is None else q, q_left=np.zeros(7),
                 hands={"right": Hand(width=0.0, held=held)}, parts={DOOR: door})


def test_a_door_is_opened_with_one_grasp_and_the_base_riding_it():
    kin, base = PlanKin(), FakeBase()
    plan = plan_door(kin, _state(), _grip(), RESTS, base=base, prior={DOOR_RELAY: PRE})
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == list(DOOR_STAGES)
    closes = [s for s in plan.segments if s.kind == "action" and s.action[0] == "grip" and s.action[1] == 0.0]
    assert len(closes) == 1                                   # one grasp
    seg = {s.name: s for s in plan.segments}
    assert np.allclose(seg["door_reach"].q_end, PRE) and np.allclose(plan.decisions[DOOR_RELAY], PRE)
    assert np.allclose(seg["door_grasp"].q_end[:3], HANDLE)
    ride = seg["door_ride"]
    assert ride.kind == "scripted" and ride.info["executor"] == "ride" and ride.target == ("s", 0.62)
    assert [a[0][DOOR] for a in base.asked] == pytest.approx(list(np.linspace(0.0, 0.62, 5)))   # <= 0.2 apart
    assert ((DOOR, "fingers"),) in kin.only                   # held: the arm, not its fingers, vs the door
    assert seg["door_release"].action == ("grip", 0.04, 70, False) and np.allclose(seg["tuck"].q_end, FOLD)
    # the ride, the leave and the tuck from the arm on the handle, not from the posture the State started in
    assert np.allclose(ride.q_from, seg["door_grasp"].q_end)
    leave = seg["door_leave"]
    assert np.allclose(leave.q_from, ride.q_end) and leave.qs and leave.info["length"] == pytest.approx(DOOR_LEAVE)
    assert np.allclose(seg["tuck"].q_from, leave.q_end)


def test_the_door_sweeping_into_the_robot_fails_the_plan_at_the_ride():
    kin = PlanKin(blocked=lambda st, q: st.parts[DOOR] > 0.3)
    plan = plan_door(kin, _state(), _grip(), RESTS, base=FakeBase(), prior={DOOR_RELAY: PRE})
    assert isinstance(plan, Failure) and plan.segment == "door_ride" and "s=0.310" in plan.why


def test_the_rest_after_the_hold_rides_from_where_the_door_stands():
    held = Held(DOOR, np.eye(4), "part")
    st = _state(_q(HANDLE), door=0.01, held=held)
    plan = plan_door(PlanKin(), st, _grip(), RESTS, base=FakeBase(), start="door_ride")
    assert isinstance(plan, Plan) and plan.segments[0].name == "door_ride"
    assert plan.segments[0].info["script"].s0 == pytest.approx(0.01)


def test_a_handle_that_moved_has_the_reach_built_again():
    kin = PlanKin()
    plan = plan_door(kin, _state(), _grip(), RESTS, base=FakeBase(), prior={DOOR_RELAY: PRE})
    reach = next(s for s in plan.segments if s.name == "door_reach")
    assert P.holds(kin, _state(), reach) is None
    why = P.holds(kin, with_part(_state(), DOOR, 0.01), reach)    # the door nudged 0.01 rad: the bar 6 mm off
    assert why is not None and "further off its target than built" in why


def test_the_failure_exit_lets_go_of_a_handle_and_keeps_a_load():
    kin = PlanKin()
    st = _state(_q(HANDLE), held=Held(DOOR, np.eye(4), "part"))
    exit_ = plan_clear(kin, st, open_width=0.04)
    assert exit_ is not None and exit_.segments[0].action[:2] == ("grip", 0.04)
    assert plan_clear(kin, holding(_state(), "right", Held("cup", np.eye(4))), open_width=0.04) is None


def test_a_ride_that_stops_short_asks_for_letting_go_and_backing_out():
    from tests.test_scripted import RideAct
    from zeno_skills import run as RUN
    from zeno_skills.motion_state import SkillFailure
    plan = plan_door(PlanKin(), _state(), _grip(), RESTS, base=FakeBase(), prior={DOOR_RELAY: PRE})
    ride = next(s for s in plan.segments if s.name == "door_ride")
    with pytest.raises(SkillFailure) as e:
        RUN.execute(RideAct(done=False), ride)
    assert e.value.clear == {"open_width": 0.04, "leave": True, "ticks": 60}
