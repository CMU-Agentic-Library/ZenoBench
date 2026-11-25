"""The push's layer-5 side (skill_jobs.slide; docs/motion/MOTION_ARCHITECTURE.md section 6, contact, and 7):
every direction and way one goal of one park search, the direction it went kept for the later legs, no
direction or way tried after a failure -- slide_job's goal set, push_object's legs and the policies on
top (slide to edge).  No simulator: run_skill and the plan are stand-ins."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import skills
from zeno_skills.park_search import VARIANT_COST
from zeno_skills.policies import SlideToEdgePolicy
from zeno_skills.rig import SkillFailure
from zeno_skills.skill_jobs import slide
from zeno_skills.skill_jobs.slide import MODES, push_object, slide_job

X, Y = np.array([1.0, 0.0]), np.array([0.0, 1.0])


class _Book:
    """A rig with one object whose bottom centre moves where the stand-in push leaves it."""

    def __init__(self, at=(0.8, 0.75, 0.75)):
        self.at = np.array(at, float)
        self.events = []
        self.held = None
        self.geo = SimpleNamespace(bottom=lambda name, st: self.at.copy(), support_under=lambda name, st: _TABLE,
                                   footprint=lambda name, st: np.r_[self.at[:2] - 0.1, self.at[:2] + 0.1])
        self.ann = SimpleNamespace(objects={"book": {}}, asset_of=lambda obj: {"size": [0.2, 0.2, 0.02]})

    def state(self):
        return {"objects": {"book": {"quat": [1.0, 0.0, 0.0, 0.0]}}}

    def held_by(self, side="right"):
        return None

    def arm_kin(self, side="right"):
        return self.kin if side == "right" else getattr(self, "left_kin", self.kin)

    def log(self, label, **kw):
        self.events.append((label, kw))


_TABLE = {"name": "table", "aabb_xy": [0.0, 0.0, 1.0, 1.0], "z": 0.75}


def _legs(monkeypatch, rig, went=0, moves=None, planned=None):
    """run_skill as a stand-in: records each leg's args, moves the book along the direction ``went`` of the
    first leg (then the only one) by all that is left that way (or by ``moves`` in turn: as far as the arm
    got), the plan having predicted that (or ``planned``)."""
    calls = []
    moves = list(moves) if moves is not None else None

    def run_skill(rig_, skill, args):
        calls.append(args)
        j = went if len(calls) == 1 else 0
        n, d, _ = args["dirs"][j]
        step = moves.pop(0) if moves is not None else d
        rig.at[:2] += step * np.asarray(n)
        return j, step, step if planned is None else planned
    monkeypatch.setattr("zeno_skills.motion_skills.run_skill", run_skill)
    return calls


def test_every_leg_asks_for_all_that_is_left_and_the_first_one_for_every_direction(monkeypatch):
    rig = _Book(at=(0.2, 0.2, 0.75))
    calls = _legs(monkeypatch, rig, went=1, moves=[0.22, 0.08])            # the arm got 22 cm from the first park
    n, moved = push_object(rig, "book", _TABLE, [(X, 0.40, None), (Y, 0.30, None)], label="T")
    assert len(calls[0]["dirs"]) == 2 and calls[0]["modes"] == MODES
    (n0, d0, c0), (n1, d1, c1) = calls[0]["dirs"]
    assert np.allclose(n0, X) and np.allclose(n1, Y)
    assert (d0, c0) == (0.40, 0.40) and (d1, c1) == (0.30, 0.30)          # no set leg; cost: the distance
    assert [len(c["dirs"]) for c in calls[1:]] == [1] and np.allclose(calls[1]["dirs"][0][0], Y)
    assert calls[1]["dirs"][0][1] == pytest.approx(0.30 - 0.22)           # the next park: the rest
    assert np.allclose(n, Y) and moved == pytest.approx(0.30)


def test_a_leg_that_does_not_move_it_fails_with_no_other_direction_or_way_after_it(monkeypatch):
    rig = _Book(at=(0.2, 0.2, 0.75))
    calls = _legs(monkeypatch, rig, moves=[0.002], planned=0.10)
    with pytest.raises(SkillFailure, match="did not move"):
        push_object(rig, "book", _TABLE, [(X, 0.10, None), (Y, 0.10, None)], modes=("drag", "push"))
    assert len(calls) == 1 and calls[0]["modes"] == ("drag", "push")


def test_enough_ends_it_before_the_distance(monkeypatch):
    rig = _Book(at=(0.2, 0.2, 0.75))
    calls = _legs(monkeypatch, rig, moves=[0.25])
    n, moved = push_object(rig, "book", _TABLE, [(X, 0.40, 0.2)])
    assert len(calls) == 1 and moved == pytest.approx(0.25)


def test_an_unknown_way_is_refused():
    with pytest.raises(ValueError, match="mode"):
        push_object(_Book(), "book", _TABLE, [(X, 0.1, None)], modes=("shove",))


def test_the_job_has_every_direction_and_way_as_goals_each_mode_a_tier(monkeypatch):
    def ways(rig, name, T_obj, n, d, modes=MODES):
        return [(m, i, {"obj": name, "T_obj_tcp": np.eye(4), "n": np.r_[n, 0.0], "d": d, "back": 0.02,
                        "above": 0.1}) for m in modes for i in range(4)]
    monkeypatch.setattr(slide, "slide_ways", ways)
    rig = _Book(at=(0.2, 0.2, 0.75))
    rig.sync_world = lambda: None
    rig.kin = SimpleNamespace(rest=np.zeros(9), drive=np.zeros(9))
    rig.base_pose = lambda: (0.0, 0.0, 0.0)
    state = SimpleNamespace(objects={"book": np.eye(4)})
    job = slide_job(rig, {"name": "book", "support": _TABLE, "dirs": [(X, 0.1, 0.3), (Y, 0.1, 0.1)],
                          "modes": ("push", "drag")}, state, skill=SimpleNamespace(build=lambda *a, **k: None))
    goals, tiers, starts = job.problem.goals, job.problem.tiers, job.problem.relay_from
    assert len(goals) == 2 * 2 * 4
    assert [g[2] for g in goals[:8]] == pytest.approx([0.3 + VARIANT_COST * i for i in range(4)] * 2)
    assert [g[2] for g in goals[8:]] == pytest.approx([0.1 + VARIANT_COST * i for i in range(4)] * 2)
    assert list(tiers) == ([0] * 4 + [1] * 4) * 2                          # every push before any drag
    # each relay (the push's end) reached from the push point: a leg may stop short of it
    assert len(starts) == len(goals) and all(np.allclose(p, 0.0) for p in starts) and job.problem.reach_step > 0
    job.found(SimpleNamespace(k=8 + 4 + 2, x=0.0, y=0.0, yaw=0.0, plan=None))  # Y, a drag, the third turn
    rig.at[:2] += 0.07 * Y
    j, travel, planned = job.done()
    assert j == 1 and travel == pytest.approx(0.07) and planned == 0.0


def _edges(monkeypatch):
    monkeypatch.setattr(skills, "_open_edges", lambda rig, s: [X, Y])
    monkeypatch.setattr(skills, "_overlaps_objects", lambda *a, **k: False)


def test_slide_to_edge_pushes_once_with_every_free_edge_and_no_edge_after_a_failure(monkeypatch):
    _edges(monkeypatch)
    rig, calls = _Book(), []

    def failing(rig_, name, s, ways, label="PUSH", modes=MODES):
        calls.append(ways)
        raise SkillFailure(f"push {name}: object did not move")
    monkeypatch.setattr(slide, "push_object", failing)
    with pytest.raises(SkillFailure, match="did not move"):
        SlideToEdgePolicy(rig).execute("book")
    # +x: EDGE_MIN_OVERHANG 0.055 m wanted, the book 0.1 m inside (need 0.155, aimed 5 mm past); +y: 0.15 m
    # inside (need 0.205)
    assert len(calls) == 1 and len(calls[0]) == 2
    (n0, d0, e0), (n1, d1, e1) = calls[0]
    assert np.allclose(n0, X) and (d0, e0) == pytest.approx((0.160, 0.155))
    assert np.allclose(n1, Y) and (d1, e1) == pytest.approx((0.210, 0.205))


def test_slide_to_edge_judges_the_overhang_along_the_edge_the_push_went(monkeypatch):
    _edges(monkeypatch)
    rig = _Book()

    def pushing(rig_, name, s, ways, label="PUSH", modes=MODES):
        n, d, _ = ways[1]
        rig.at[:2] += d * n
        return n, d
    monkeypatch.setattr(slide, "push_object", pushing)
    out = SlideToEdgePolicy(rig).execute("book")
    assert out["direction"] == [0.0, 1.0] and out["overhang_m"] == pytest.approx(0.06)


def test_slide_to_edge_keeps_a_short_object_s_centre_of_mass_on_the_top(monkeypatch):
    # a 14 cm tissue box: half 0.07, so at most 0.055 m out (its centre of mass COM_MARGIN 0.015 on the top) --
    # exactly what the edge pinch needs, no 5 mm extra; pushed past that it is refused
    from zeno_skills import skills
    _edges(monkeypatch)
    rig = _Book()
    rig.ann.asset_of = lambda obj: {"size": [0.14, 0.14, 0.06]}
    seen = []

    def pushing(rig_, name, s, ways, label="PUSH", modes=MODES):
        seen.extend(ways)
        n, d, _ = ways[0]
        rig.at[:2] += d * n
        return n, d
    monkeypatch.setattr(slide, "push_object", pushing)
    out = SlideToEdgePolicy(rig).execute("book")
    assert all(d == pytest.approx(e) for _, d, e in seen)                 # no aim past the centre-of-mass limit
    assert out["overhang_m"] == pytest.approx(skills.EDGE_MIN_OVERHANG)

    def overshooting(rig_, name, s, ways, label="PUSH", modes=MODES):
        n, d, _ = ways[0]
        rig_.at[:2] += (d + 0.004) * n                                 # 4 mm past: under 1.5 cm on the top
        return n, d
    rig2 = _Book()
    rig2.ann.asset_of = lambda obj: {"size": [0.14, 0.14, 0.06]}
    monkeypatch.setattr(slide, "push_object", overshooting)
    with pytest.raises(SkillFailure, match="centre of mass"):
        SlideToEdgePolicy(rig2).execute("book")
