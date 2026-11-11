"""Task segments and a held part (docs/MOTION_ARCHITECTURE.md 2.4, 3.1, 4.1, 4.2, 5.5, 8.4, 8.6):
primitives.Script / couplings / scripted, Spec.touch on parts and with the hand, Held(kind="part"),
holds and run.execute of a task segment, Rig.ride's closed loop.  No simulator."""

from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import primitives as P
from zeno_skills import run as RUN
from zeno_skills.motion_state import (Failure, Hand, Held, Segment, SkillFailure, Spec, State, holding, released,
                                      touch_entries, touches, with_part)

DOOR = "kitchen_cabinet_4"
HINGE = np.array([1.0, 0.0, 0.0])            # the door's vertical hinge axis passes here


def door_pose(v):
    """The part frame at joint value v: turned v about the hinge axis (identity at 0)."""
    c, s = np.cos(v), np.sin(v)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, HINGE - R @ HINGE
    return T


class WorldMotion:
    """The collision backend's part of Motion.query: the queries inside see the State."""

    @contextmanager
    def query(self, kin, state, spec):
        saved, kin.state = getattr(kin, "state", None), state
        try:
            yield
        finally:
            kin.state = saved


class DoorKin:
    """TCP = q[:3], orientation fixed, the base ignored.  ``blocked(state, q)``: the robot collides
    in that state (the door at its value); cart_path interpolates q[:3] (kinematic, never blocked)."""
    side = "right"

    def __init__(self, blocked=lambda st, q: False):
        self.motion, self.blocked, self.state, self.scene = WorldMotion(), blocked, None, object()
        self.only = []

    def tcp(self, q):
        return np.asarray(q, float)[:3].copy(), np.eye(3)

    def cart_path(self, q0, p, R, step=0.01):
        q0 = np.asarray(q0, float)
        n = max(2, int(np.ceil(np.linalg.norm(np.asarray(p) - q0[:3]) / step)) + 1)
        out = []
        for u in np.linspace(0, 1, n)[1:]:
            q = q0.copy()
            q[:3] = q0[:3] + (np.asarray(p) - q0[:3]) * u
            out.append(q)
        return out, True

    def free(self, q):
        return not self.blocked(self.state, np.asarray(q, float))

    def path_free(self, qs):
        return all(self.free(q) for q in qs)

    def path_free_only(self, qs, names):
        self.only.append(tuple(names))
        return True


class FakeBase:
    def __init__(self, ok=lambda st, pose: True):
        self.ok, self.asked = ok, []

    def clear(self, state, poses):
        self.asked += [(dict(state.parts), tuple(p)) for p in poses]
        return [self.ok(state, p) for p in poses]


def _state(q=None, base=(0.0, 0.0, 0.0), door=0.0, held=None, objects=None):
    q = np.zeros(9) if q is None else np.asarray(q, float)
    return State(base=base, q_right=q, q_left=np.zeros(7), hands={"right": Hand(width=0.0, held=held)},
                 parts={DOOR: door}, objects=objects or {})


TRACK = dict(lead=0.03, rate=0.25, done=0.58)
HELD = Held(DOOR, np.eye(4), "part")
RIDE = P.Script(P.hinge(DOOR, door_pose), 0.0, 0.6, step=0.15)          # samples 0, .15, .3, .45, .6


def _ride(kin=None, base=None, state=None, **kw):
    return P.scripted(kin or DoorKin(), state or holding(_state(), "right", HELD), Spec(), kw.pop("script", RIDE),
                      "open_ride", base=base or FakeBase(), track=kw.pop("track", TRACK), **kw)


# --------------------------------------------------------------------------- touch
def test_a_touch_entry_names_what_and_with_which_links():
    assert touch_entries(("cup", ("door", "hand"))) == (("cup", "fingers"), ("door", "hand"))
    with pytest.raises(ValueError):
        touch_entries((("door", "elbow"),))


def test_a_held_part_is_touched_by_the_fingers_without_being_listed():
    st = holding(_state(), "right", HELD)
    assert touches(st, Spec(), "right") == ((DOOR, "fingers"),)
    assert touches(st, Spec(touch=((DOOR, "hand"),)), "right") == ((DOOR, "hand"), (DOOR, "fingers"))
    assert touches(st, Spec(), "left") == ()
    assert touches(holding(_state(), "right", Held("cup", np.eye(4))), Spec(), "right") == ()   # a load is no touch


def test_letting_go_of_a_handle_leaves_the_objects_alone():
    st = released(holding(_state(), "right", HELD), "right", DOOR)
    assert st.held() is None and DOOR not in st.objects
    assert with_part(st, DOOR, 0.4).parts[DOOR] == 0.4 and st.parts[DOOR] == 0.0


def test_the_rest_of_the_arm_is_checked_against_a_held_part():
    kin = DoorKin()
    assert P.free_path(kin, holding(_state(), "right", HELD), Spec(), [np.zeros(9), np.full(9, 0.1)])
    assert kin.only == [((DOOR, "fingers"),)]


# --------------------------------------------------------------------------- Script, couplings
def test_a_script_is_a_function_over_an_interval_sampled_by_its_step():
    assert RIDE.samples() == pytest.approx([0.0, 0.15, 0.3, 0.45, 0.6])
    assert P.Script(P.still("pot"), 0.0, -0.1, step=0.04).samples() == pytest.approx([0, -1 / 30, -2 / 30, -0.1])
    assert P.COUPLINGS["hinge"](DOOR, door_pose).kind == "hinge" and P.COUPLINGS["slider"](DOOR, door_pose).kind == "slider"


def test_the_base_rides_rigid_with_the_door():
    # base at the origin, the hinge 1 m ahead: turning the door by s swings the base about the hinge
    for s in (0.0, 0.3, 0.6):
        x, y, yaw = P.ride_base(RIDE, (0.0, 0.0, 0.0), s)
        assert (x, y, yaw) == pytest.approx((1 - np.cos(s), -np.sin(s), np.degrees(s)))


# --------------------------------------------------------------------------- scripted
def test_a_ride_is_checked_with_the_door_and_the_base_where_each_s_puts_them():
    kin, base = DoorKin(), FakeBase()
    seg = _ride(kin, base)
    assert isinstance(seg, Segment) and seg.kind == "scripted" and seg.qs == () and seg.target == ("s", 0.6)
    assert seg.info["executor"] == "ride" and seg.info["track"] == TRACK and seg.info["script"] is RIDE
    assert [a[0][DOOR] for a in base.asked] == pytest.approx(list(RIDE.samples()))
    assert [a[1] for a in base.asked] == [pytest.approx(P.ride_base(RIDE, (0, 0, 0), s)) for s in RIDE.samples()]
    assert kin.only and all(o == ((DOOR, "fingers"),) for o in kin.only)    # the arm, not its fingers, vs the door


def test_one_sample_that_collides_fails_the_whole_segment():
    # the forearm meets the door panel past 0.4 rad: all or nothing, nothing skipped
    seg = _ride(DoorKin(blocked=lambda st, q: st.parts[DOOR] > 0.4))
    assert isinstance(seg, Failure) and "the robot collides at s=0.450" in seg.why
    seg = _ride(base=FakeBase(ok=lambda st, pose: pose[0] < 0.02))
    assert isinstance(seg, Failure) and "the base collides at s=0.300" in seg.why


def test_a_ride_starts_anywhere_along_its_interval_and_up_to_its_lead_short_of_it():
    for door, ok in ((0.1, True), (0.6, True), (-0.03, True), (-0.04, False), (0.61, False)):
        seg = _ride(state=holding(_state(door=door), "right", HELD))
        assert isinstance(seg, Segment) == ok, (door, seg)
    assert "is at -0.0400, the task segment starts at 0.0000" in _ride(state=holding(_state(door=-0.04), "right", HELD)).why


def test_a_ride_holds_a_part_it_tracks_with_the_arm_still():
    with pytest.raises(ValueError):
        _ride(track={k: v for k, v in TRACK.items() if k != "lead"})
    with pytest.raises(ValueError):          # a ride keeps the TCP rigid in the part frame
        _ride(script=P.Script(P.hinge(DOOR, door_pose), 0.0, 0.6, 0.15, tcp=lambda s: np.eye(4)))
    with pytest.raises(ValueError):          # nothing to ride on
        _ride(script=P.Script(P.still("pot"), 0.0, 0.6, 0.15))
    with pytest.raises(ValueError):
        _ride(script=P.Script(P.hinge(DOOR, door_pose), 0.0, 0.6, 0.15, carry="teleport"))


POT = np.eye(4)
POT[:3, 3] = (0.3, 0.0, 0.4)


def stir(s, r=0.02):
    """The TCP on a circle of radius r in the pot frame at phase s."""
    T = np.eye(4)
    T[:3, 3] = (r * np.cos(s), r * np.sin(s), 0.0)
    return T


STIR = P.Script(P.still("pot"), 0.0, np.pi, step=np.pi / 4, tcp=stir, carry="arm")


def _stir_state(q=None):
    return _state(np.r_[0.32, 0.0, 0.4, np.zeros(6)] if q is None else q, objects={"pot": POT})


def test_the_arm_follows_a_script_by_ik_continued_from_where_it_is():
    seg = P.scripted(DoorKin(), _stir_state(), Spec(), STIR, "stir")
    assert isinstance(seg, Segment) and seg.info["executor"] == "follow"
    ends = [q for q, s, s_next in zip(seg.qs, seg.info["s_at"], list(seg.info["s_at"][1:]) + [None]) if s != s_next]
    assert [tuple(np.round(q[:3], 4)) for q in ends] == \
        [tuple(np.round(POT[:3, 3] + stir(s)[:3, 3], 4)) for s in STIR.samples()[1:]]
    assert len(seg.qs) == len(seg.info["s_at"])
    off = P.scripted(DoorKin(), _stir_state(np.r_[0.35, 0.0, 0.4, np.zeros(6)]), Spec(), STIR, "stir")
    assert isinstance(off, Failure) and "not at the task's start" in off.why


def test_the_arm_s_motion_collides_and_fails_the_segment():
    kin = DoorKin(blocked=lambda st, q: q[1] > 0.019)          # the far side of the circle is in the way
    seg = P.scripted(kin, _stir_state(), Spec(), STIR, "stir")
    assert isinstance(seg, Failure) and "the robot collides by s=" in seg.why


# --------------------------------------------------------------------------- holds
def test_a_ride_holds_while_the_base_and_the_door_are_where_it_was_built():
    st = holding(_state(), "right", HELD)
    seg = _ride(state=st)
    assert P.holds(DoorKin(), st, seg) is None
    assert P.holds(DoorKin(), with_part(st, DOOR, 0.05), seg) is None               # along the interval
    assert "the task segment starts at" in P.holds(DoorKin(), with_part(st, DOOR, -0.05), seg)   # behind the lead
    assert "off where the task segment was built" in P.holds(DoorKin(), _state(base=(0.01, 0.0, 0.0), held=HELD), seg)
    blocked = DoorKin(blocked=lambda s, q: s.parts[DOOR] > 0.5)                     # a chair in the sweep now
    assert "the task segment now: the robot collides at s=0.600" in P.holds(blocked, st, seg)


def test_an_arm_task_holds_while_its_motion_is_free_now():
    seg = P.scripted(DoorKin(), _stir_state(), Spec(), STIR, "stir")
    assert P.holds(DoorKin(), _stir_state(), seg) is None
    assert "the robot collides by s=" in P.holds(DoorKin(blocked=lambda st, q: q[1] > 0.019), _stir_state(), seg)


# --------------------------------------------------------------------------- run.execute
class RideAct:
    def __init__(self, done=True):
        self.done, self.rides, self.declared, self.follows = done, [], [], []

    def declare(self, name, allow, side="right", follows=True):
        self.declared.append(name)

    def ride(self, part, base_at, s_from, s_to, label, lead, rate, done):
        self.rides.append((part, base_at, s_from, s_to, label, lead, rate, done))
        return {"done": True} if self.done else {"done": False, "why": f"{part} stalled at 0.210"}

    def follow(self, qs, steps_per_wp=3, smooth=False, side="right"):
        self.follows.append(len(qs))


def test_execute_hands_the_ride_the_script_s_own_function():
    seg = _ride()
    act = RideAct()
    RUN.execute(act, seg)
    part, base_at, s_from, s_to, label, lead, rate, done = act.rides[0]
    assert act.declared == ["open_ride"] and (part, s_from, s_to, label) == (DOOR, 0.0, 0.6, "open_ride")
    assert (lead, rate, done) == (0.03, 0.25, 0.58)
    for s in (0.0, 0.123, 0.6):                               # any s, not only the plan's samples
        assert base_at(s) == pytest.approx(P.ride_base(RIDE, (0.0, 0.0, 0.0), s))
    with pytest.raises(SkillFailure, match="open_ride: kitchen_cabinet_4 stalled"):
        RUN.execute(RideAct(done=False), seg)


def test_execute_follows_an_arm_task():
    seg = P.scripted(DoorKin(), _stir_state(), Spec(), STIR, "stir")
    act = RideAct()
    RUN.execute(act, seg)
    assert act.follows == [len(seg.qs)] and act.rides == []


# --------------------------------------------------------------------------- Rig.ride (the closed loop)
class RideRig:
    """What Rig.ride reads and writes: a door the base drags along -- each tick it closes ``pull`` of
    the way to the value the commanded base stands for (x = 0.1 s), or does not move (``stuck``),
    or springs back ``back`` once past 0.3."""

    def __init__(self, pull=0.5, stuck=False, back=0.0):
        self.s, self.bx, self.pull, self.stuck, self.back = 0.0, 0.0, pull, stuck, back
        self.events = []
        self.clear = SimpleNamespace(executing=lambda: None)

    def joint(self, name):
        return self.s

    def set_base(self, x, y, yaw):
        self.bx = x

    def base_pose(self):
        return self.bx, -2.0 * self.bx, 100.0 * self.bx

    def step(self, n=1):
        if not self.stuck:
            self.s += self.pull * (self.bx / 0.1 - self.s)
        if self.back and self.s > 0.3:
            self.s -= self.back
            self.back = 0.0

    def fingers(self):
        return np.zeros(2)

    def log(self, ev, **kw):
        self.events.append((ev, kw))


def _rig_ride(rig, **kw):
    from zeno_skills.rig import Rig
    return Rig.ride(rig, DOOR, lambda s: (0.1 * s, -0.2 * s, 10.0 * s), 0.0, 0.6, "open_ride",
                    **{**TRACK, **kw})


def test_a_ride_follows_the_door_on_the_planned_function_to_done():
    rig = RideRig()
    out = _rig_ride(rig)
    assert out["done"] and out["s"] >= 0.58 and out["lag_max"] <= 0.03 + 1e-9
    assert rig.bx <= 0.06 + 1e-9                             # never past the script's end
    assert rig.events[-1][0] == "ride_end" and rig.events[-1][1]["done"]


def test_a_stuck_door_stalls_the_ride_and_one_springing_back_slipped():
    out = _rig_ride(RideRig(stuck=True))
    assert not out["done"] and "stalled" in out["why"]
    out = _rig_ride(RideRig(back=0.1))
    assert not out["done"] and "slipped" in out["why"]
    out = _rig_ride(RideRig(back=0.04))                      # back less than two leads: followed on, not a slip
    assert out["done"]


# --------------------------------------------------------------------------- the rig's side
def test_the_base_model_checks_the_base_with_the_parts_where_the_state_has_them():
    from zeno_skills.skill_jobs.base import RigBase
    seen = []
    world = SimpleNamespace(joint_q={DOOR: 0.0})
    world.set_joint = lambda k, v: world.joint_q.__setitem__(k, v)
    world.footprints_clear = lambda poses: (seen.append(dict(world.joint_q)), [p[0] < 1 for p in poses])[1]
    base = RigBase(SimpleNamespace(world=world))
    assert base.clear(_state(door=0.7), [(0.5, 0, 0), (2.0, 0, 90)]) == [True, False]
    assert seen == [{DOOR: 0.7}] and world.joint_q == {DOOR: 0.0}        # put back after


def test_a_touch_name_is_an_object_else_a_part():
    from zeno_skills.motion import Motion
    m = SimpleNamespace(by_owner={"object:cup": [1]}, ann=SimpleNamespace(objects={"cup": {}}, articulated=[{"name": DOOR}]))
    assert Motion.touch_owner(m, "cup") == "object:cup" and Motion.touch_owner(m, DOOR) == f"part:{DOOR}"
    with pytest.raises(KeyError):
        Motion.touch_owner(m, "ghost")
