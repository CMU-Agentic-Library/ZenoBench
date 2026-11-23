"""An object pushed or dragged across its support (docs/motion/MOTION_ARCHITECTURE.md section 6, contact):
primitives.Pushed and skill_plans.plan_slide -- the closed hand down behind it (or onto it), the push a
task segment with the object moving along from where the fingers meet it, as far as the arm reaches,
checked whole; the way out measured.  FakeKin: no simulator."""

import numpy as np
import pytest

from tests.test_door_plan import PlanKin
from zeno_skills import primitives as P
from zeno_skills.motion_state import Hand, Plan, State, chains, with_object
from zeno_skills.skill_plans import SLIDE_RELAY, SLIDE_STAGES, SLIDE_STEP, plan_slide, slide_travel
from zeno_skills.tolerances import LEAVE_GAP, LEAVE_MARGIN

BOOK = "paperback_book"
N = np.array([1.0, 0.0, 0.0])                  # pushed toward +x
AT = np.array([0.5, -0.3, 0.75])               # the book's box frame origin
PUSH_AT = np.array([-0.1, 0.0, 0.02])          # the push point in that frame: behind it, low
LAG = 0.008                                    # the hand runs this far before the book moves


class SlideKin(PlanKin):
    """PlanKin with something to leave and an arm that runs out: below ``floor`` (and within LEAVE_GAP
    above it) the hand is near the world; the arm's IK goes no further along x than ``reach``."""

    def __init__(self, floor=None, reach=None, **kw):
        super().__init__(**kw)
        self.floor, self.reach = floor, reach

    def near(self, q, gap):
        return self.floor is not None and q[2] < self.floor + gap

    def cart_path(self, q0, p, R, step=0.01):
        line, ok = super().cart_path(q0, p, R, step)
        if self.reach is None:
            return line, ok
        kept = [q for q in line if q[0] <= self.reach + 1e-9]
        return kept, len(kept) == len(line)


def _T(p):
    T = np.eye(4)
    T[:3, 3] = p
    return T


def _q(p):
    return np.r_[p, np.zeros(6)]


FOLD = _q([0.2, -0.2, 0.6])
RESTS = (FOLD, _q([0.1, -0.3, 0.4]))
LOW = (AT + PUSH_AT)[2] + 1e-6                 # the push's height: the support just under the fingers


def _push(back=0.01, d=0.12, above=0.073, at=PUSH_AT, lag=LAG, least=0.01):
    return {"obj": BOOK, "T_obj_tcp": _T(at), "n": N, "d": d, "lag": lag, "least": least, "above": above,
            "back": back}


def _state(book=AT, q=None):
    return State(base=(0.0, 0.0, 0.0), **chains(_q([0.3, -0.3, 1.0]) if q is None else q, np.zeros(7)),
                 hands={"right": Hand(width=0.04)}, objects={BOOK: _T(book)})


def _top(back=0.01, above=0.073):
    return _q(AT + PUSH_AT - back * N + [0.0, 0.0, above])


def _book_after(plan):
    return next(s for s in plan.segments if s.name == "slide_moved").info["assumed"].objects[BOOK][:3, 3]


def test_a_push_comes_down_behind_the_object_moves_it_and_backs_out_away_from_it_and_the_support():
    kin = SlideKin(floor=LOW)
    plan = plan_slide(kin, _state(), _push(), RESTS, prior={SLIDE_RELAY: _top()})
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == list(SLIDE_STAGES)
    seg = {s.name: s for s in plan.segments}
    assert seg["slide_close_hand"].action[:2] == ("grip", 0.0)
    assert np.allclose(seg["slide_reach"].q_end, _top()) and np.allclose(plan.decisions["slide_reach"], _top())
    assert np.allclose(seg["slide_down"].q_end[:3], AT + PUSH_AT - 0.01 * N)
    assert np.allclose(seg["slide_in"].q_end[:3], AT + PUSH_AT)
    push = seg["slide_push"]
    assert push.kind == "scripted" and push.info["executor"] == "follow" and push.target == ("s", 0.12)
    assert np.allclose(push.q_end[:3], AT + PUSH_AT + 0.12 * N)          # the hand: the whole of d
    assert np.allclose(_book_after(plan), AT + (0.12 - LAG) * N)           # the book: LAG behind it
    assert slide_travel(plan) == pytest.approx(0.12 - LAG)
    assert (BOOK,) in [tuple(n for n, _ in t) for t in kin.only]          # the fingers may touch it, the arm not
    # out at 45 deg up and back off the face, as far as it is near the world and LEAVE_MARGIN on
    leave = seg["slide_leave"]
    way = leave.q_end[:3] - leave.q_from[:3]
    assert np.allclose(way / np.linalg.norm(way), np.array([-1.0, 0.0, 1.0]) / np.sqrt(2.0))
    assert LEAVE_GAP * np.sqrt(2.0) + LEAVE_MARGIN - 0.004 <= leave.info["length"] <= LEAVE_GAP * np.sqrt(2.0) + LEAVE_MARGIN + 0.004
    assert np.allclose(seg["tuck"].q_from, leave.q_end) and np.allclose(seg["tuck"].q_end, FOLD)
    assert seg["slide_open_hand"].action[:2] == ("grip", 0.04)
    for name in ("slide_reach", "slide_down", "slide_in"):                # the push point from the State
        assert seg[name].info["aim"].obj == BOOK
    assert all(s.info.get("side") == "right" for s in plan.segments)


def test_a_drag_lands_on_the_object_with_no_push_in_and_leaves_straight_up():
    at = np.array([0.05, 0.0, 0.03])
    kin = SlideKin(floor=(AT + at)[2] + 1e-6)
    plan = plan_slide(kin, _state(), _push(back=0.0, at=at), RESTS)
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == [n for n in SLIDE_STAGES if n != "slide_in"]
    seg = {s.name: s for s in plan.segments}
    assert seg["slide_down"].spec.touch == ((BOOK, "fingers"),)          # it presses on the book
    way = seg["slide_leave"].q_end[:3] - seg["slide_leave"].q_from[:3]
    assert np.allclose(way / np.linalg.norm(way), [0.0, 0.0, 1.0])


def test_touching_nothing_after_the_push_there_is_no_way_out_to_make():
    plan = plan_slide(PlanKin(), _state(), _push(), RESTS, prior={SLIDE_RELAY: _top()})
    assert isinstance(plan, Plan) and "slide_leave" not in [s.name for s in plan.segments]


def test_the_leg_ends_where_the_arm_runs_out_and_the_object_is_predicted_there():
    start = (AT + PUSH_AT)[0]
    kin = SlideKin(reach=start + 0.07)
    plan = plan_slide(kin, _state(), _push(), RESTS, prior={SLIDE_RELAY: _top()})
    assert isinstance(plan, Plan), plan
    push = next(s for s in plan.segments if s.name == "slide_push")
    s1 = 0.06                                                              # the last sample (SLIDE_STEP apart) it reaches
    assert SLIDE_STEP == 0.02 and push.target == ("s", pytest.approx(s1)) and push.info["script"].s1 == pytest.approx(s1)
    assert np.allclose(push.q_end[:3], AT + PUSH_AT + s1 * N)
    assert np.allclose(_book_after(plan), AT + (s1 - LAG) * N)
    assert slide_travel(plan) == pytest.approx(s1 - LAG)


def test_a_leg_that_would_not_move_the_object_far_enough_fails_the_plan():
    kin = SlideKin(reach=(AT + PUSH_AT)[0] + 0.025)                       # to s = 0.02: the book 12 mm on
    plan = plan_slide(kin, _state(), _push(least=0.015), RESTS, prior={SLIDE_RELAY: _top()})
    assert not isinstance(plan, Plan) and plan.segment == "slide_push" and "only 0.012 m" in plan.why


def test_the_object_pushed_into_something_fails_the_plan_at_the_push():
    # the robot collides once the book is 5 cm along (something beyond it, in the State's world)
    kin = PlanKin(blocked=lambda st, q: st is not None and BOOK in st.objects and st.objects[BOOK][0, 3] > AT[0] + 0.05)
    plan = plan_slide(kin, _state(), _push(), RESTS, prior={SLIDE_RELAY: _top()})
    assert not isinstance(plan, Plan) and plan.segment == "slide_push" and "s=" in plan.why


def test_the_ranking_solution_of_the_push_end_seeds_the_descent_start():
    kin = PlanKin()
    end = _q(AT + PUSH_AT + 0.12 * N)
    plan = plan_slide(kin, _state(), _push(), RESTS, prior={SLIDE_RELAY: end})
    assert SLIDE_RELAY == "slide_end" and isinstance(plan, Plan), plan
    reach = next(s for s in plan.segments if s.name == "slide_reach")
    assert np.allclose(reach.q_end[:3], _top()[:3]) and reach.info["decided"] == {"slide_reach": "solved"}


def test_the_pushed_coupling_runs_the_object_lag_behind_the_hand():
    c = P.pushed(BOOK, _T(AT), N, lag=0.01)
    st = c.moved(_state(), 0.07)
    assert np.allclose(st.objects[BOOK][:3, 3], AT + 0.06 * N)               # the object: 7 cm less the lag
    assert np.allclose(c.frame(st, 0.07)[:3, 3], AT + 0.07 * N)               # the hand's frame: all of it
    assert c.value(st) == pytest.approx(0.06) and c.value(_state()) == pytest.approx(0.0)
    assert c.travel(0.005) == 0.0 and np.allclose(c.moved(_state(), 0.005).objects[BOOK], _T(AT))
    assert P.COUPLINGS["pushed"] is P.pushed


def test_a_push_whose_object_moved_no_longer_holds_and_is_built_from_where_it_is():
    kin = PlanKin()
    plan = plan_slide(kin, _state(), _push(), RESTS, prior={SLIDE_RELAY: _top()})
    push = next(s for s in plan.segments if s.name == "slide_push")
    nudged = with_object(_state(q=push.q_from), BOOK, _T(AT + 0.02 * N))   # it slid 2 cm before the push
    assert "starts at" in P.holds(kin, nudged, push)
    again = plan_slide(kin, nudged, _push(), RESTS, start="slide_reach", prior=plan)
    assert isinstance(again, Plan), again
    assert np.allclose(next(s for s in again.segments if s.name == "slide_push").q_end[:3],
                       AT + 0.02 * N + PUSH_AT + 0.12 * N)


def test_a_push_that_still_holds_is_kept_and_moves_the_state_by_its_own_script():
    kin = PlanKin()
    plan = plan_slide(kin, _state(), _push(), RESTS, prior={SLIDE_RELAY: _top()})
    old = {s.name: s for s in plan.segments}
    # nudged 2 mm along n, within the push's start (TARGET_TOL): the hand still ends where it did, and so
    # does the book it pushes -- not 2 mm further, as a script made from here would have it
    again = plan_slide(kin, _state(book=AT + 0.002 * N), _push(), RESTS, start="slide_close_hand", prior=plan)
    assert isinstance(again, Plan), again
    assert next(s for s in again.segments if s.name == "slide_push") is old["slide_push"]
    assert np.allclose(_book_after(again), AT + (0.12 - LAG) * N)
