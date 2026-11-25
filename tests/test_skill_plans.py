"""Skill plans and their execution (docs/motion/MOTION_ARCHITECTURE.md sections 6, 8): the segments in the
skill's order, each from where the one before ends, the State moved on between them; run checks
each segment before it and builds the rest again from here when it no longer holds."""

from types import SimpleNamespace

import numpy as np
import pytest

from tests.test_primitives import IKKin as FakeKin, _q
from zeno_skills import primitives as P, run as RUN
from zeno_skills.motion_state import Failure, Hand, Held, Plan, Segment, Spec, State, chains, with_arm
from zeno_skills.primitives import PoseSet
from zeno_skills.rig import SkillFailure
from zeno_skills.skill_plans import DROP_STAGES, PICK_STAGES, plan_drop, plan_pick, plan_place

GRASP_P = np.array([0.5, 0.0, 0.10])
DOWN = np.array([0.0, 0.0, -1.0])


def _at(p, R=np.eye(3)):
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, p
    return T


# the cup's box frame at the origin (objects={"cup": np.eye(4)}): its grasp at GRASP_P in the world
GRASP = {"name": "cup", "T_obj_tcp": _at(GRASP_P), "u": DOWN, "L": 0.07, "pre_open": 0.03, "kind": "pinch"}


def _named(plan, name):
    return next(sg for sg in plan.segments if sg.name == name)


def _state(q, held=None, objects=None):
    return State(base=(0.0, 0.0, 0.0), **chains(np.asarray(q, float), np.zeros(7)),
                 hands={"right": Hand(width=0.03, held=held)}, objects=objects or {})


def _carry(seen):
    def goals(state, q):
        seen.append(state)
        return PoseSet(((np.array([0.3, 0.0, 0.40]), np.eye(3)),)), {"steps_per_wp": 4}
    return goals


def test_a_pick_is_planned_in_order_and_holds_the_load_after_closing():
    seen = []
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])          # the lift touches up to 12 cm
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, _carry(seen))
    assert isinstance(plan, Plan) and tuple(s.name for s in plan.segments) == PICK_STAGES
    reach, grasp, lift = (_named(plan, n) for n in ("pick_reach", "pick_grasp", "pick_lift"))
    assert np.allclose(grasp.q_from, reach.q_end)                   # the straight from where the leg ends
    assert np.allclose(reach.q_end[:3], GRASP_P - 0.07 * DOWN)
    assert lift.spec.allow.from_contact and lift.info["touching"] == "off_support"
    assert seen and seen[0].held("right").name == "cup"            # the carry is planned with the load held


def test_a_pick_from_a_later_stage_starts_there():
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    held = Held("cup", np.eye(4))
    plan = plan_pick(kin, _state(GRASP_P.tolist() + [0] * 6, held=held), GRASP, _carry([]),
                     start="pick_lift")
    assert [s.name for s in plan.segments] == ["pick_lift", "carry_in"]


def test_a_ranking_solution_off_the_reach_ins_start_only_seeds_its_solve_in_the_collision_model():
    # the TCP straight to the reach-in's start is blocked: the leg goes to its solution
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)], wall=lambda p: 0.39 < p[0] < 0.41 and p[2] > 0.25)
    rank = np.full(9, 0.7)                                   # kinematic, its TCP not at the start: a seed
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP,
                     _carry([]), prior={"pick_reach": rank})
    assert isinstance(plan, Plan), plan
    assert ("ik_global", 2) in kin.calls                     # rank first among the seeds, then the arm's
    assert _named(plan, "pick_reach").info["decided"] == {"pick_reach": "solved"}
    assert np.allclose(_named(plan, "pick_reach").q_end[:3], GRASP_P - 0.07 * DOWN)


def test_no_collision_free_solution_of_the_reach_ins_start_fails_the_plan():
    kin = FakeKin(wall=lambda p: abs(p[2] - 0.17) < 1e-6)
    out = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, _carry([]))
    assert isinstance(out, Failure) and out.segment == "pick_reach" and "IK" in out.why


def test_a_pick_that_cannot_be_made_says_which_segment():
    kin = FakeKin(wall=lambda p: p[2] < 0.12, plan_to=(None, "IK_FAIL"))    # the grasp pose is in the table
    out = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, _carry([]))
    assert isinstance(out, Failure) and out.segment == "pick_grasp"


def _place_kin(**kw):
    # the load on the support below z = 0.10: within LEAVE_GAP of the world under 0.10 + a bit
    return FakeKin(near_z=0.115, **kw)


def test_a_place_lets_go_and_tucks_with_the_load_an_obstacle():
    q_p = _q(0.5, 0.0, 0.10)
    held = Held("cup", np.eye(4))
    kin = _place_kin()
    plan = plan_place(kin, _state(_q(0.3, 0.0, 0.40), held=held), _at(q_p[:3]), 0.03, 0.07,
                      (np.zeros(9),), prior={"place_reach": q_p})
    assert isinstance(plan, Plan), plan
    assert [s.name for s in plan.segments] == ["place_arrive", "place_reach", "place_down", "place_release",
                                               "place_landed", "place_pull_out", "tuck", "place_settle"]
    assert [s.name for s in plan.segments if s.kind == "anchor"] == ["place_arrive", "place_landed"]
    assert plan.segments[-1].action == ("wait", 90)                 # the 90 ticks _place_result used to step
    down = _named(plan, "place_down")
    assert np.allclose(down.q_from, _named(plan, "place_reach").q_end) and np.allclose(down.q_end[:3], q_p[:3])
    assert _named(plan, "place_reach").info["set_down_m"] > 0


def test_the_pull_out_lets_the_fingers_touch_what_they_let_go():
    q = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    plan = plan_place(kin, _state(q, held=Held("cup", np.eye(4))), _at(q[:3]), 0.03, 0.07,
                      (_q(0.3, 0.0, 0.40),), start="place_release")
    pull = _named(plan, "place_pull_out")
    assert pull.name == "place_pull_out" and pull.spec.touch == ("cup",)
    assert pull.spec.allow.touch == ("cup",) and pull.spec.allow.links == "fingers"


def test_a_place_in_a_cavity_pulls_out_only_off_the_load_then_leaves_through_the_opening(monkeypatch):
    # the cup's box frame at the TCP, its box 4 cm above it: let go it falls LEAVE_GAP -- the pull-out (up, the
    # gripper axis) only as far as the fingertips need to pass its top by LEAVE_MARGIN, not a finger's length;
    # then out of the cavity (open towards +x at x = 0.6) as far as the arm's spheres inside need
    from zeno_skills.kinematics import finger_model_box
    from zeno_skills.tolerances import LEAVE_GAP, LEAVE_MARGIN
    q_p = _q(0.5, 0.0, 0.10)
    r = 0.02
    monkeypatch.setattr(P, "robot_spheres", lambda kin, state, spec, q: [[*kin.tcp(q)[0], r, 0.0, "gripper_link"]])
    cavity = {"box": (0.2, -0.2, 0.0, 0.6, 0.2, 0.5), "out": (1.0, 0.0),
              "load": (np.array([-0.03, -0.03, -0.05]), np.array([0.03, 0.03, 0.04]))}
    plan = plan_place(_place_kin(), _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4))), _at(q_p[:3]), 0.03,
                      0.07, (np.zeros(9),), prior={"place_reach": q_p}, obj="cup", cavity=cavity)
    assert isinstance(plan, Plan), plan
    names = [sg.name for sg in plan.segments]
    assert names[names.index("place_pull_out"):] == ["place_pull_out", "place_exit", "tuck", "place_settle"]
    pull, out = _named(plan, "place_pull_out"), _named(plan, "place_exit")
    rise = pull.q_end[2] - pull.q_from[2]
    assert rise == pytest.approx(0.04 - LEAVE_GAP + finger_model_box()[3] + LEAVE_MARGIN, abs=1e-6)
    assert out.q_end[0] == pytest.approx(0.6 + r + LEAVE_MARGIN, abs=1e-6)
    assert np.allclose(out.q_end[1:3], pull.q_end[1:3])                 # horizontal, out of the opening
    # in the open: a finger's length up, no exit
    plain = plan_place(_place_kin(), _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4))), _at(q_p[:3]), 0.03,
                       0.07, (np.zeros(9),), prior={"place_reach": q_p}, obj="cup")
    assert "place_exit" not in [sg.name for sg in plain.segments]
    p = _named(plain, "place_pull_out")
    assert p.q_end[2] - p.q_from[2] == pytest.approx(0.07, abs=1e-6)


def test_an_edge_place_moves_its_open_pads_clear_of_the_load_only_as_far_as_needed():
    # the book's box frame at the TCP, its box 1 cm off along the closing axis (Y_link); the hand opens 4 cm a
    # finger.  A thin book (half 2.2 cm along Y): both pads clear it by EDGE_PAD_CLEAR already -- no move.
    # A thick one (half 3.3 cm): the near pad 3 mm into it -- the least move that clears both, 8 mm
    q_p = _q(0.5, 0.0, 0.10)

    def plan(half):
        box = (np.array([-0.1, 0.01 - half, -0.1]), np.array([0.1, 0.01 + half, 0.1]))
        return plan_place(_place_kin(), _state(_q(0.3, 0.0, 0.40), held=Held("book", np.eye(4))), _at(q_p[:3]), 0.04,
                          0.07, (np.zeros(9),), prior={"place_reach": q_p}, obj="book", edge_box=box)
    thin, thick = plan(0.022), plan(0.033)
    assert isinstance(thin, Plan) and isinstance(thick, Plan), (thin, thick)
    assert "place_clear" not in [sg.name for sg in thin.segments]
    names = [sg.name for sg in thick.segments]
    assert names[names.index("place_landed") + 1:names.index("place_landed") + 3] == ["place_clear", "place_pull_out"]
    clear, pull = _named(thick, "place_clear"), _named(thick, "place_pull_out")
    assert np.allclose(clear.q_end[:3] - clear.q_from[:3], [0.0, 0.008, 0.0], atol=1e-3)
    assert pull.spec.touch == () and not pull.spec.allow.touch               # a touch drags the book out


# ------------------------------------------------------------------- drop (docs/skills/drop_hover.md)
def test_a_drop_reaches_over_the_opening_lets_go_waits_and_tucks():
    q_p = _q(0.5, 0.0, 0.30)
    plan = plan_drop(FakeKin(), _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4))), _at(q_p[:3]), 0.03,
                     (np.zeros(9),), "bin", 0.2, prior={"drop_reach": q_p})
    assert isinstance(plan, Plan), plan
    assert tuple(s.name for s in plan.segments) == DROP_STAGES
    assert [s.name for s in plan.segments if s.kind == "anchor"] == ["drop_arrive"]   # where it lands: not predicted
    reach, release, fall = (_named(plan, n) for n in ("drop_reach", "drop_release", "drop_fall"))
    assert np.allclose(reach.q_end[:3], q_p[:3]) and reach.spec.hold_tilt and reach.info["tol"]
    assert release.action == ("grip", 0.03, 40, False) and fall.action == ("wait", 120)
    assert release.spec.allow.touch == ("cup",) and release.spec.allow.held_on == ("bin",)
    assert np.allclose(plan.decisions["drop_reach"], reach.q_end)


def test_a_hover_is_the_drops_reach_with_nothing_let_go():
    from zeno_skills.skill_plans import HOVER_STAGES, plan_hover
    q_p = _q(0.5, 0.0, 0.30)
    plan = plan_hover(FakeKin(), _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4))), _at(q_p[:3]),
                      prior={"hover_reach": q_p})
    assert isinstance(plan, Plan), plan
    assert tuple(s.name for s in plan.segments) == HOVER_STAGES
    reach = _named(plan, "hover_reach")
    assert np.allclose(reach.q_end[:3], q_p[:3]) and reach.spec.hold_tilt and reach.info["tol"]
    assert np.allclose(plan.decisions["hover_reach"], reach.q_end)
    out = plan_hover(FakeKin(), _state(_q(0.3, 0.0, 0.40)), _at(q_p[:3]))
    assert isinstance(out, Failure) and "nothing in the hand to hover" in out.why


def test_a_lift_moves_the_load_straight_up_to_the_height_and_nothing_else():
    from zeno_skills.skill_plans import plan_held_move
    q0 = _q(0.4, -0.1, 0.80)
    st = _state(q0, held=Held("cup", np.eye(4)))
    plan = plan_held_move(FakeKin(), st, 0.95, name="lift")
    assert isinstance(plan, Plan) and [sg.name for sg in plan.segments] == ["lift"]
    up = plan.segments[0]
    assert np.allclose(up.q_end[:3], [0.4, -0.1, 0.95]) and up.spec.hold_tilt
    assert all(abs(q[0] - 0.4) < 1e-9 and abs(q[1] + 0.1) < 1e-9 for q in up.qs)      # straight up
    assert plan_held_move(FakeKin(), st, 0.80, name="lift").segments == ()            # there already
    blocked = plan_held_move(FakeKin(wall=lambda p: p[2] > 0.9), st, 0.95, name="lift")
    assert isinstance(blocked, Failure) and blocked.segment == "lift"                 # nothing tried instead
    assert isinstance(plan_held_move(FakeKin(), _state(q0), 0.95), Failure)            # nothing held


def test_a_release_opens_where_it_is_and_pulls_out_back_along_the_gripper_axis():
    from zeno_skills.skill_plans import RELEASE_STAGES, plan_release
    q = _q(0.5, 0.0, 0.30)
    # the cup's world within LEAVE_GAP of the hand up to z 0.33: the pull-out (TCP +z: back) as far as that, then
    # LEAVE_MARGIN -- measured, not a finger's length
    plan = plan_release(FakeKin(near_z=0.33), _state(q, held=Held("cup", np.eye(4))), 0.03, 0.07)
    assert isinstance(plan, Plan) and tuple(s.name for s in plan.segments) == RELEASE_STAGES
    opened, out = plan.segments
    assert opened.action == ("grip", 0.03, 60, True) and opened.spec.allow.touch == ("cup",)
    assert 0.33 < out.q_end[2] <= 0.33 + 0.004 + 0.011 and out.spec.allow.touch == ("cup",)   # one 4 mm step
    blocked = plan_release(FakeKin(near_z=0.33, reach_z=0.32), _state(q, held=Held("cup", np.eye(4))), 0.03, 0.07)
    assert isinstance(blocked, Failure) and blocked.segment == "release_pull_out"   # built before the hand opens
    assert isinstance(plan_release(FakeKin(), _state(q), 0.03, 0.07), Failure)


def test_a_wipe_presses_strokes_there_and_back_and_lifts_off():
    from zeno_skills.skill_plans import WIPE_STAGES, plan_wipe
    q0 = _q(0.4, 0.0, 0.40)
    wipe = {"support": "table", "p": np.array([0.5, 0.0, 0.10]), "R": np.eye(3), "d": np.array([0.2, 0.0, 0.0]),
            "above": 0.016}
    plan = plan_wipe(FakeKin(), _state(q0, held=Held("sponge", np.eye(4))), wipe)
    assert isinstance(plan, Plan), plan
    assert tuple(sg.name for sg in plan.segments) == WIPE_STAGES
    press, stroke, back_ = (_named(plan, n) for n in ("wipe_press", "wipe_stroke", "wipe_return"))
    assert np.allclose(press.q_end[:3], [0.5, 0.0, 0.10]) and press.spec.touch == (("table", "held"),)
    assert stroke.kind == "scripted" and np.allclose(stroke.q_end[:3], [0.7, 0.0, 0.10])     # along d, on the surface
    assert plan.info["stroke_m"] == pytest.approx(0.2) and np.allclose(back_.q_end[:3], [0.5, 0.0, 0.10])
    assert np.allclose(_named(plan, "wipe_leave").q_end[:3], [0.5, 0.0, 0.116])
    assert np.allclose(plan.segments[-1].q_end, q0)                                      # back where it arrived
    assert isinstance(plan_wipe(FakeKin(), _state(q0), wipe), Failure)                    # nothing to wipe with
    # rule 2: a stroke shorter than the job's need fails the build -- at the park and in run's rebuild alike
    st = _state(q0, held=Held("sponge", np.eye(4)))
    short = plan_wipe(FakeKin(), st, {**wipe, "need": 0.25})
    assert isinstance(short, Failure) and short.segment == "wipe_stroke" and "0.250 m needed" in short.why
    again = plan_wipe(FakeKin(), _state(press.q_end, held=Held("sponge", np.eye(4))), {**wipe, "need": 0.25},
                      start="wipe_stroke", prior=plan)
    assert isinstance(again, Failure) and again.segment == "wipe_stroke"


def test_a_wipe_aims_its_press_through_the_hold_the_state_has():
    # docs 6 / rule 9: the press pose is the sponge's, the TCP derived from the hold in the State -- a sponge that slid
    # in the hand on the way makes the press no longer hold (WIPE_TOL), and a rebuild aims through the new hold
    from zeno_skills.motion_state import Aim
    from zeno_skills.primitives import holds
    from zeno_skills.skill_plans import plan_wipe
    q0 = _q(0.4, 0.0, 0.40)
    T_sponge = np.eye(4)
    T_sponge[:3, 3] = [0.5, 0.0, 0.05]                                  # the sponge's box frame where it presses
    hold = np.eye(4)
    hold[:3, 3] = [0.0, 0.0, -0.05]                                     # held 5 cm below the TCP
    wipe = {"support": "table", "aim": Aim("sponge", T_sponge, held=True), "d": np.array([0.2, 0.0, 0.0]),
            "above": 0.016}
    plan = plan_wipe(FakeKin(), _state(q0, held=Held("sponge", hold)), wipe)
    assert isinstance(plan, Plan), plan
    press = _named(plan, "wipe_press")
    assert np.allclose(press.q_end[:3], [0.5, 0.0, 0.10]) and press.info["aim"] is wipe["aim"]
    slid = hold.copy()
    slid[2, 3] = -0.047                                                  # 3 mm up in the pinch
    assert holds(FakeKin(), _state(press.q_from, held=Held("sponge", hold)), press) is None
    assert holds(FakeKin(), _state(press.q_from, held=Held("sponge", slid)), press) is not None
    again = plan_wipe(FakeKin(), _state(q0, held=Held("sponge", slid)), wipe)
    assert np.allclose(_named(again, "wipe_press").q_end[:3], [0.5, 0.0, 0.097])


def test_a_gesture_reaches_its_goal_set_swings_about_where_it_got_and_folds():
    from zeno_skills.primitives import JointSet, PoseSet
    from zeno_skills.skill_plans import plan_gesture
    q0, rest = _q(0.3, 0.0, 0.40), _q(0.2, -0.2, 0.30)
    goals = PoseSet(((np.array([0.4, 0.1, 0.9]), np.eye(3)),))
    plan = plan_gesture(FakeKin(ik=[_q(0.4, 0.1, 0.9)]), _state(q0), "wave", goals=goals, swing=((0.0, 1.0, 0.0), 0.1, 2),
                        open_hand=0.04,
                        back=JointSet((rest,)), hold_tilt=False)
    assert isinstance(plan, Plan), plan
    assert [sg.name for sg in plan.segments] == ["wave_open", "wave_reach", "wave_swing", "wave_back"]
    swing = _named(plan, "wave_swing")
    ys = [q[1] for q in swing.qs]
    assert swing.kind == "scripted" and max(ys) == pytest.approx(0.2, abs=1e-3) and min(ys) == pytest.approx(0.0, abs=1e-3)
    assert np.allclose(swing.q_end[:3], [0.4, 0.1, 0.9], atol=1e-6)                     # ends where it started
    assert np.allclose(plan.segments[-1].q_end, rest)
    shake = plan_gesture(FakeKin(), _state(q0, held=Held("cup", np.eye(4))), "shake", swing=((1.0, 0.0, 0.0), 0.02, 3))
    assert [sg.name for sg in shake.segments] == ["shake_swing"] and shake.segments[0].spec.hold_tilt


def test_a_pour_tilts_about_its_pivot_as_far_as_the_arm_goes_and_back():
    from zeno_skills.skill_plans import POUR_STAGES, plan_pour
    q0 = _q(0.4, 0.0, 0.40)
    pour = {"source": "cup", "target": "pot", "p": np.array([0.5, 0.0, 0.40]), "R": np.eye(3),
            "pivot": np.array([0.55, 0.0, 0.40]), "axis": np.array([0.0, 0.0, 1.0]), "tilt": np.radians(90.0)}
    # (the test kin turns about the vertical only: the arc's geometry the same about any axis)
    plan = plan_pour(FakeKin(), _state(q0, held=Held("cup", np.eye(4))), pour)
    assert isinstance(plan, Plan), plan
    assert tuple(sg.name for sg in plan.segments) == POUR_STAGES
    tilt, untilt = _named(plan, "pour_tilt"), _named(plan, "pour_untilt")
    assert tilt.kind == "scripted" and not tilt.spec.hold_tilt and plan.info["tilt_rad"] == pytest.approx(np.radians(90))
    assert np.allclose(tilt.q_end[:3], [0.55, -0.05, 0.40], atol=1e-6)                 # turned about the pivot
    assert np.allclose(untilt.q_end[:3], [0.5, 0.0, 0.40], atol=1e-6)                   # back where it started
    assert np.allclose(plan.segments[-1].q_end, q0)
    # rule 2: short of the least tilt the build fails, the first and a rebuild from the tilt alike
    st = _state(q0, held=Held("cup", np.eye(4)))
    assert isinstance(plan_pour(FakeKin(), st, {**pour, "min_tilt": np.radians(100.0)}), Failure)
    again = plan_pour(FakeKin(), _state(_named(plan, "pour_reach").q_end, held=Held("cup", np.eye(4))),
                      {**pour, "min_tilt": np.radians(100.0)}, start="pour_tilt", prior=plan)
    assert isinstance(again, Failure) and again.segment == "pour_tilt"


def test_a_flip_turns_the_held_edge_over_the_pivot_lets_go_pushes_on_and_leaves():
    from zeno_skills.skill_plans import plan_flip
    q0 = _q(0.5, 0.0, 0.10)
    flip = {"obj": "book", "support": "table", "pivot": np.array([0.6, 0.0, 0.10]), "axis": np.array([0.0, -1.0, 0.0]),
            "release": np.radians(80.0), "past": np.radians(95.0), "push_to": np.radians(120.0), "pre_open": 0.03}
    plan = plan_flip(FakeKin(), _state(q0, held=Held("book", np.eye(4))), flip, (np.zeros(9),))
    assert isinstance(plan, Plan), plan
    names = [sg.name for sg in plan.segments]
    assert names[:4] == ["flip_arrive", "flip_arc", "flip_release", "flip_push"] and names[-1] == "flip_settle"
    assert plan.info["arc_rad"] == pytest.approx(np.radians(80.0))              # short of past: the open hand pushes on
    assert _named(plan, "flip_arc").spec.touch == (("table", "held"),)
    assert _named(plan, "flip_release").action[:2] == ("grip", 0.03)
    # docs 8.3: run's rebuild at the arrival keeps the arc that still holds; rule 2: short of the least arc the
    # build fails there as at the park
    st = _state(q0, held=Held("book", np.eye(4)))
    again = plan_flip(FakeKin(), st, flip, (np.zeros(9),), start="flip_arc", prior=plan)
    assert isinstance(again, Plan) and _named(again, "flip_arc") is _named(plan, "flip_arc")
    short = plan_flip(FakeKin(), st, {**flip, "min_arc": np.radians(85.0)}, (np.zeros(9),), start="flip_arc", prior=plan)
    assert isinstance(short, Failure) and short.segment == "flip_arc"


def test_a_drop_needs_a_load_and_one_built_after_the_release_only_waits_and_tucks():
    out = plan_drop(FakeKin(), _state(_q(0.3, 0.0, 0.40)), _at([0.5, 0.0, 0.3]), 0.03, (np.zeros(9),), "bin", 0.2)
    assert isinstance(out, Failure) and "nothing in the hand" in out.why
    after = plan_drop(FakeKin(), _state(_q(0.5, 0.0, 0.30)), _at([0.5, 0.0, 0.3]), 0.03, (np.zeros(9),), "bin", 0.2,
                      start="drop_fall")
    assert [s.name for s in after.segments] == ["drop_fall", "tuck"]


# ------------------------------------------------------------------- decisions (docs 4.3, 5.7, 8.1)
def test_a_pick_records_its_decisions_and_a_rebuild_keeps_them():
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    st = _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)})
    plan = plan_pick(kin, st, GRASP, _carry([]))
    assert set(plan.decisions) == {"pick_reach", "carry_in"} and plan.decisions["carry_in"] == (0, 1)
    assert np.allclose(plan.decisions["pick_reach"][:3], GRASP_P - 0.07 * DOWN)
    kin.calls.clear()
    # the decisions alone (a search's prior): the reach built again on the decided solution
    again = plan_pick(kin, st, GRASP, _carry([]), start="pick_reach", prior=dict(plan.decisions))
    assert again.segments[0].info["decided"] == {"pick_reach": "prior"} and not any(c[0] == "ik_global" for c in kin.calls)
    assert np.array_equal(again.decisions["pick_reach"], plan.decisions["pick_reach"])
    # the plan (run's rebuild) from where it was built: every motion kept as it is, its decisions with them
    kept = plan_pick(kin, st, GRASP, _carry([]), start="pick_reach", prior=plan)
    assert all(a is b for a, b in zip((sg for sg in kept.segments if sg.kind == "move"),
                                      (sg for sg in plan.segments if sg.kind == "move")))
    assert np.array_equal(kept.decisions["pick_reach"], plan.decisions["pick_reach"])
    assert kept.decisions["carry_in"] == plan.decisions["carry_in"]


def test_a_place_records_its_decisions_and_a_rebuild_keeps_them():
    q_p = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    st = _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4)))
    rests = (np.zeros(9), _q(0.3, 0.0, 0.40))
    plan = plan_place(kin, st, _at(q_p[:3]), 0.03, 0.07, rests)
    assert set(plan.decisions) == {"place_reach"}                        # the tuck is chosen again every time
    assert np.allclose(plan.decisions["place_reach"][:3], q_p[:3])
    assert _named(plan, "place_reach").info["decided"] == {"set_down_start": "prior", "place_reach": "solved"}
    kin.calls.clear()
    again = plan_place(kin, st, _at(q_p[:3]), 0.03, 0.07, rests, prior=dict(plan.decisions))
    assert _named(again, "place_reach").info["decided"]["place_reach"] == "prior"
    assert not any(c[0] == "ik_global" for c in kin.calls)
    kept = plan_place(kin, st, _at(q_p[:3]), 0.03, 0.07, rests, prior=plan)
    assert all(_named(kept, n) is _named(plan, n) for n in ("place_reach", "place_down", "place_pull_out"))
    assert _named(kept, "tuck") is not _named(plan, "tuck")              # made again, never kept


def test_a_rebuild_tucks_to_the_fold_once_it_is_free_whatever_the_plan_chose():
    # the search found the fold blocked and tucked hanging; at the landed anchor the fold is free:
    # the tuck is chosen again, the fold first (docs 1.8), not kept from the plan
    fold, hang, q = _q(0.2, -0.2, 0.30), _q(0.1, -0.3, 0.20), _q(0.5, 0.0, 0.17)
    blocked = _place_kin(wall=lambda p: np.allclose(p, fold[:3]))
    plan = plan_place(blocked, _state(q), _at(q[:3]), 0.03, 0.07, (fold, hang), start="place_pull_out", obj="cup")
    assert _named(plan, "tuck").info["chosen"] == 1
    again = plan_place(_place_kin(), _state(q), _at(q[:3]), 0.03, 0.07, (fold, hang), start="place_pull_out",
                       obj="cup", prior=plan)
    assert _named(again, "tuck").info["chosen"] == 0
    assert _named(again, "place_pull_out") is _named(plan, "place_pull_out")


def test_a_decision_no_longer_reaching_its_pose_seeds_the_new_solve():
    q_p = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    prior = {"place_reach": np.r_[0.52, 0.0, 0.10, np.full(6, 0.2)]}    # 2 cm off: the base stopped off its park
    plan = plan_place(kin, _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4))), _at(q_p[:3]), 0.03,
                      0.07, (np.zeros(9),), prior=prior)
    assert _named(plan, "place_reach").info["decided"]["place_reach"] == "solved" and ("ik_global", 2) in kin.calls
    assert np.allclose(plan.decisions["place_reach"], _named(plan, "place_down").q_end)   # where the set-down ends


def test_a_reach_leg_made_straight_records_where_it_ends_not_the_solution_it_was_given():
    # the ranking solution reaches the start free and is kept, but the TCP straight from the arm gets
    # there first on its own solution: the one pick_grasp starts from is the decision
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    rank = np.r_[GRASP_P - 0.07 * DOWN, np.full(6, 0.7)]
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP,
                     _carry([]), prior={"pick_reach": rank})
    reach = _named(plan, "pick_reach")
    assert reach.info["decided"] == {"pick_reach": "prior"} and reach.info["how"] == "straight"
    assert np.allclose(plan.decisions["pick_reach"], reach.q_end) and not np.allclose(plan.decisions["pick_reach"], rank)
    assert np.allclose(_named(plan, "pick_grasp").q_from, plan.decisions["pick_reach"])


def test_a_place_records_where_its_set_down_ends_not_the_solution_it_was_given():
    q_p = np.r_[0.5, 0.0, 0.10, np.full(6, 0.2)]                         # kept: at the pose, free
    plan = plan_place(_place_kin(), _state(_q(0.3, 0.0, 0.40), held=Held("cup", np.eye(4))), _at(q_p[:3]),
                      0.03, 0.07, (np.zeros(9),), prior={"place_reach": q_p})
    down = _named(plan, "place_down")
    assert _named(plan, "place_reach").info["decided"]["place_reach"] == "prior"
    assert np.allclose(plan.decisions["place_reach"], down.q_end) and np.allclose(down.q_end[3:], 0.0)


def test_a_pick_keeps_its_carry_goal_only_from_a_set_laid_out_the_same():
    def carry(state, q):
        return PoseSet(((np.array([0.3, 0.0, 0.40]), np.eye(3)), (np.array([0.3, 0.0, 0.60]), np.eye(3)))), {}
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40), _q(0.3, 0.0, 0.60)])
    st = _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)})
    assert plan_pick(kin, st, GRASP, carry).decisions["carry_in"] == (0, 2)          # the cheaper
    assert plan_pick(kin, st, GRASP, carry, prior={"carry_in": (1, 2)}).decisions["carry_in"] == (1, 2)
    # decided in a set of 3 (skills._carry_goals: another number of heights): its index means another goal here
    assert plan_pick(kin, st, GRASP, carry, prior={"carry_in": (1, 3)}).decisions["carry_in"] == (0, 2)


# ------------------------------------------------------------------------------- run
class FakeRig:
    """A motion_state.Actuator: the arm goes where it is told, the State is read off it (observe is
    patched in the tests)."""

    def __init__(self, kin, q):
        self.kin, self.q_cmd, self.events, self.ran, self.declared = kin, np.asarray(q, float), [], [], []

    def log(self, ev, **kw):
        self.events.append((ev, kw))

    def arm_kin(self, side="right"):
        return self.kin

    def declare(self, name, allow, side="right", follows=True):
        self.declared.append((name, side))

    def contact_allow(self, kin, allow):
        return allow

    def follow(self, qs, steps_per_wp=3, smooth=False, side="right"):
        self.ran.append(len(qs))
        self.q_cmd = np.asarray(qs[-1], float)


def _seg(name, q0, q1):
    return Segment(name, Spec(), np.asarray(q0, float), (np.asarray(q1, float),))


def test_run_takes_the_plan_as_it_is_while_it_holds(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    plan = Plan((_seg("a", np.zeros(9), np.full(9, 0.1)), _seg("b", np.full(9, 0.1), np.full(9, 0.2))))
    done = RUN.run(rig, plan, rebuild=lambda s, n, prior: pytest.fail("rebuilt"))
    assert [s.name for s in done] == ["a", "b"] and np.allclose(rig.q_cmd, 0.2)


def test_run_builds_the_rest_again_when_a_segment_no_longer_holds(monkeypatch):
    rig = FakeRig(FakeKin(seg_free=True), np.zeros(9))
    rig.kin.path_free = lambda qs: False                            # the world changed: "a" collides now
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    asked = []

    def rebuild(state, name, prior):
        asked.append(name)
        return Plan((_seg("a2", state.q("right"), np.full(9, 0.3)),))
    rig.kin.path_free = lambda qs: len(asked) > 0                   # the rebuilt one is free
    done = RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.1)),)), rebuild)
    assert asked == ["a"] and [s.name for s in done] == ["a2"]


def test_a_segment_the_arm_stopped_short_on_fails_after_its_own_hook(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    plan = Plan((_seg("a", np.zeros(9), np.full(9, 0.1)), _seg("b", np.full(9, 0.1), np.full(9, 0.2))))
    follow = rig.follow
    rig.follow = lambda qs, *a, **k: follow(qs) or 0.25                # stopped 25 cm off (a T05 carry)
    seen = []
    with pytest.raises(SkillFailure, match="a: the arm stopped 0.250 m short"):
        RUN.run(rig, plan, None, {"a": {"after": lambda act: seen.append("hook")}})
    assert seen == ["hook"]                                         # the skill's own judgement came first
    rig.follow = lambda qs, *a, **k: follow(qs) or 0.002              # within TARGET_TOL: arrived
    assert [s.name for s in RUN.run(rig, Plan((_seg("c", rig.q_cmd, np.full(9, 0.3)),)), None)] == ["c"]


def test_a_rest_that_cannot_be_built_fails_the_skill(monkeypatch):
    rig = FakeRig(FakeKin(), np.full(9, 0.5))                       # not where the segment starts
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    with pytest.raises(SkillFailure, match="not where the segment starts.*no way"):
        RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.1)),)), lambda s, n, prior: Failure("no way", n))


def test_run_hands_the_plan_as_it_stands_to_a_rebuild_its_decisions_kept(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    rig.kin.path_free = lambda qs: not any(np.allclose(q, 0.9) for q in qs)     # 0.9: in the way now
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    priors = []

    def rebuild(state, name, prior):
        priors.append((name, [s.name for s in prior.segments], prior.decisions))   # kept as handed over
        if name == "a":
            return Plan((_seg("a2", state.q("right"), np.full(9, 0.3)), _seg("b2", np.full(9, 0.3), np.full(9, 0.9))),
                        decisions={"a_reach": 2})
        return Plan((_seg("b3", state.q("right"), np.full(9, 0.4)),))
    plan = Plan((_seg("a", np.zeros(9), np.full(9, 0.9)),), decisions={"a_reach": 1, "tuck": 0})
    done = RUN.run(rig, plan, rebuild)
    assert [s.name for s in done] == ["a2", "b3"]
    assert priors == [("a", ["a"], {"a_reach": 1, "tuck": 0}), ("b2", ["a2", "b2"], {"a_reach": 2, "tuck": 0})]
    assert plan.decisions == {"a_reach": 1, "tuck": 0}                     # the plan run is not changed either


def test_a_rebuild_logs_how_the_segment_run_now_was_decided(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    rig.kin.path_free = lambda qs: not any(np.allclose(q, 0.9) for q in qs)
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    a2 = Segment("a2", Spec(), np.zeros(9), (np.full(9, 0.3),), info={"decided": {"a_reach": "prior"}})
    RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.9)),)), lambda s, n, prior: Plan((a2,)))
    ev = [kw for e, kw in rig.events if e == "segment"]
    assert ev == [{"target": "a", "reused": False, "why": ev[0]["why"], "rebuilt": ["a2"], "decided": {"a_reach": "prior"}}]


def test_the_place_tuck_is_chosen_again_the_fold_first_whatever_the_plan_chose():
    q = _q(0.5, 0.0, 0.10)
    rests = (_q(0.5, 0.0, 0.15), _q(0.3, 0.0, 0.40))
    plan = plan_place(_place_kin(), _state(q), _at(q[:3]), 0.03, 0.07, rests, start="tuck", obj="cup",
                      prior={"tuck": (1, 2)})
    assert plan.segments[0].info["chosen"] == 0 and "tuck" not in plan.decisions


def test_the_relay_decisions_are_the_builders_stage_names():
    from zeno_skills.skill_plans import PICK_RELAY, PLACE_RELAY, PLACE_STAGES
    assert PICK_RELAY in PICK_STAGES and PLACE_RELAY in PLACE_STAGES
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": np.eye(4)}), GRASP, _carry([]))
    assert PICK_RELAY in plan.decisions


# ------------------------------------------------------------------- targets from the State (docs 6, 8.3)
def test_a_pick_takes_its_grasp_from_where_the_state_has_the_object():
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    moved = _at([0.02, 0.0, 0.0])                                   # the cup 2 cm along x
    plan = plan_pick(kin, _state(_q(0.3, 0.0, 0.40), objects={"cup": moved}), GRASP, _carry([]))
    reach, grasp = _named(plan, "pick_reach"), _named(plan, "pick_grasp")
    assert np.allclose(grasp.q_end[:3], GRASP_P + [0.02, 0.0, 0.0])
    assert np.allclose(reach.q_end[:3], GRASP_P + [0.02, 0.0, 0.0] - 0.07 * DOWN)
    for seg in (reach, grasp):                                      # what run checks again
        assert seg.info["aim"].obj == "cup" and np.allclose(seg.info["aimed"][0], GRASP_P + [0.02, 0.0, 0.0])
    # not in the State: the reach cannot be made; the stages after the close need no grasp pose
    assert isinstance(plan_pick(kin, _state(_q(0.3, 0.0, 0.40)), GRASP, _carry([])), Failure)


def test_a_place_takes_its_set_down_pose_from_the_hold_the_state_has():
    q_p = _q(0.5, 0.0, 0.10)
    goal = _at(q_p[:3])                                             # the cup's box frame put here
    # held 1 cm below the TCP: the TCP sets it down 1 cm higher
    st = _state(_q(0.3, 0.0, 0.40), held=Held("cup", _at([0.0, 0.0, -0.01])))
    plan = plan_place(_place_kin(), st, goal, 0.03, 0.07, (np.zeros(9),))
    down = _named(plan, "place_down")
    assert np.allclose(down.q_end[:3], q_p[:3] + [0.0, 0.0, 0.01])
    assert down.info["aim"].held and np.allclose(down.info["aimed"][0], q_p[:3] + [0.0, 0.0, 0.01])
    assert isinstance(plan_place(_place_kin(), _state(_q(0.3, 0.0, 0.40)), goal, 0.03, 0.07, (np.zeros(9),)),
                      Failure)                                      # nothing in the hand to set down


def test_a_segment_whose_target_the_state_no_longer_gives_does_not_hold():
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    q0 = _q(0.3, 0.0, 0.40)
    plan = plan_pick(kin, _state(q0, objects={"cup": np.eye(4)}), GRASP, _carry([]))
    reach = _named(plan, "pick_reach")
    assert P.holds(kin, _state(q0, objects={"cup": _at([0.0005, 0.0, 0.0])}), reach) is None   # within HINT_REACH
    why = P.holds(kin, _state(q0, objects={"cup": _at([0.002, 0.0, 0.0])}), reach)
    assert why is not None and "target moved 0.0020 m" in why
    assert "not in the state" in P.holds(kin, _state(q0), reach)
    # a set-down: the load turned in the pinch ~1.6 deg about z
    from zeno_skills.evaluator import quat_R
    q_p = _q(0.5, 0.0, 0.10)
    st = _state(q0, held=Held("cup", np.eye(4)))
    down = _named(plan_place(_place_kin(), st, _at(q_p[:3]), 0.03, 0.07, (np.zeros(9),)), "place_reach")
    turned = _state(q0, held=Held("cup", _at([0.0, 0.0, 0.0], quat_R([0.9999, 0.0, 0.0, 0.0141]))))
    assert P.holds(_place_kin(), st, down) is None and "turned 1.6" in P.holds(_place_kin(), turned, down)
    # ...shifted in the pinch: within PLACE_TOL (5 mm) it still sets the load down, past it not
    assert P.holds(_place_kin(), _state(q0, held=Held("cup", _at([0.003, 0.0, 0.0]))), down) is None
    assert "target moved 0.0060 m" in P.holds(_place_kin(), _state(q0, held=Held("cup", _at([0.006, 0.0, 0.0]))), down)


class BaseKin(FakeKin):
    """FakeKin whose TCP stands at the State's base: q[:3] offset by base x, y inside a query
    (primitives.query, as kin.tcp at the queried State's base)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.offset = np.zeros(3)
        kin = self

        class Motion:
            @staticmethod
            def query(k, state, spec):
                from contextlib import contextmanager

                @contextmanager
                def at():
                    old = kin.offset
                    kin.offset = np.array([state.base[0], state.base[1], 0.0])
                    try:
                        yield
                    finally:
                        kin.offset = old
                return at()
        self.motion = Motion()

    def tcp(self, q):
        p, R = super().tcp(q)
        return p + self.offset, R


def test_a_contact_segment_whose_end_the_base_has_moved_off_its_target_does_not_hold():
    # a pick's segments by PICK_TOL (1 mm), a set-down's by PLACE_TOL (5 mm): the base stopped off its
    # park counts as the object moving does
    from zeno_skills.skill_plans import PICK_TOL, PLACE_TOL
    assert PICK_TOL[0] < PLACE_TOL[0]
    kin = BaseKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    q0 = _q(0.3, 0.0, 0.40)
    st = _state(q0, objects={"cup": np.eye(4)})
    plan = plan_pick(kin, st, GRASP, _carry([]))
    reach, grasp = _named(plan, "pick_reach"), _named(plan, "pick_grasp")
    assert np.allclose(grasp.info["end"][0], GRASP_P)                # recorded at the base it was built at
    from dataclasses import replace
    for seg in (reach, grasp):
        at = with_arm(st, seg.q_from)                       # the arm where it starts
        assert P.holds(kin, replace(at, base=(0.0005, 0.0, 0.0)), seg) is None      # within PICK_TOL
        why = P.holds(kin, replace(at, base=(0.0, 0.002, 0.0)), seg)                 # 2 mm off
        assert why is not None and "0.0020 m, 0.00 deg further off its target" in why
    q_p = _q(0.5, 0.0, 0.10)
    sd = _state(q0, held=Held("cup", np.eye(4)))
    down = _named(plan_place(BaseKin(near_z=0.115), sd, _at(q_p[:3]), 0.03, 0.07, (np.zeros(9),)), "place_down")
    at = with_arm(sd, down.q_from)
    assert P.holds(BaseKin(near_z=0.115), replace(at, base=(0.003, 0.0, 0.0)), down) is None
    assert "0.0060 m" in P.holds(BaseKin(near_z=0.115), replace(at, base=(0.0, 0.006, 0.0)), down)
    # the end's own offset from the pose (an IK solution's, a planner's) is what it was: not judged
    off = Segment("pick_grasp", Spec(), grasp.q_from, (grasp.q_end + np.r_[0.004, np.zeros(8)],),
                  info={**grasp.info, "end": (GRASP_P + [0.004, 0.0, 0.0], np.eye(3))})
    assert P.holds(kin, with_arm(st, grasp.q_from), off) is None


def test_run_builds_a_pick_again_where_the_object_now_stands(monkeypatch):
    # the drive knocked the cup 2 cm: at the anchor where the pick arrives the rest is built again
    # from the State read now, the found plan its prior -- no separate re-plan in the job (docs 8.3)
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    q0 = _q(0.3, 0.0, 0.40)
    plan = plan_pick(kin, _state(q0, objects={"cup": np.eye(4)}), GRASP, _carry([]))
    rig = FakeRig(kin, q0)
    rig.grip = lambda *a, **k: None
    cup = _at([0.02, 0.0, 0.0])
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd, objects={"cup": cup}))
    rebuilt = []

    def rebuild(state, frm, prior):
        rebuilt.append((frm, prior.decisions["pick_reach"]))
        return plan_pick(kin, state, GRASP, _carry([]), start=frm, prior=prior)
    done = RUN.run(rig, plan, rebuild)
    assert rebuilt[0][0] == "pick_open" and np.array_equal(rebuilt[0][1], plan.decisions["pick_reach"])
    grasp = next(sg for sg in done if sg.name == "pick_grasp")
    assert np.allclose(grasp.q_end[:3], GRASP_P + [0.02, 0.0, 0.0])
    assert [sg.name for sg in done] == list(PICK_STAGES)              # the rest of the pick, built from there
    arrive = next(kw for e, kw in rig.events if e == "anchor" and kw["target"] == "pick_arrive")
    assert arrive["kept"] == [] and arrive["rebuilt"] == ["pick_reach", "pick_grasp", "pick_lift", "carry_in"]
    # the error logged (9.3 step 2.1): the cup 20 mm off where the plan assumed it; why each was rebuilt
    assert arrive["off"]["watch"]["cup"] == [20.0, 0.0] and arrive["off"]["base"] == [0.0, 0.0]
    assert "further off its target" in arrive["why_rebuilt"]["pick_reach"]


def test_an_anchor_keeps_the_rest_as_it_is_while_it_holds(monkeypatch):
    kin = FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)])
    q0 = _q(0.3, 0.0, 0.40)
    st = _state(q0, objects={"cup": np.eye(4)})
    plan = plan_pick(kin, st, GRASP, _carry([]))
    rig = FakeRig(kin, q0)
    rig.grip = lambda *a, **k: None
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd, objects={"cup": np.eye(4)}))
    done = RUN.run(rig, plan, lambda state, frm, prior: plan_pick(kin, state, GRASP, _carry([]), start=frm,
                                                                  prior=prior))
    moves = [sg for sg in plan.segments if sg.kind == "move"]
    assert all(any(d is m for d in done) for m in moves)               # the very segments the search made
    arrive = next(kw for e, kw in rig.events if e == "anchor" and kw["target"] == "pick_arrive")
    assert arrive["rebuilt"] == [] and arrive["kept"] == [m.name for m in moves]
    assert not any(e == "segment" and kw.get("reused") is False for e, kw in rig.events)
    assert "why_rebuilt" not in arrive and arrive["off"]["watch"] == {"cup": [0.0, 0.0]}
    # the arm a plan assumes at an anchor is where its segments leave it (not where the plan began)
    held = next(kw for e, kw in rig.events if e == "anchor" and kw["target"] == "pick_held")
    assert held["off"]["arm"] == 0.0
    # the contact pose's segments log how much further off their target they stand than built: nothing
    reach = next(kw for e, kw in rig.events if e == "segment" and kw["target"] == "pick_grasp")
    assert reach["aim_off"] == [0.0, 0.0, 0.0]
    # no rebuild (a plan from elsewhere, docs 8.8): an anchor checks nothing ahead, only logs the error
    rig2 = FakeRig(kin, q0)
    rig2.grip = lambda *a, **k: None
    RUN.run(rig2, plan, None)
    assert all("kept" not in kw and "off" in kw for e, kw in rig2.events if e == "anchor")


def test_a_place_anchor_logs_no_rebuild_for_a_tuck_made_again_the_same(monkeypatch):
    # the tuck is never kept, but made again the same it is no rebuild in the anchor event
    q_p = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    q0 = _q(0.3, 0.0, 0.40)
    plan = plan_place(kin, _state(q0, held=Held("cup", np.eye(4))), _at(q_p[:3]), 0.03, 0.07, (np.zeros(9),),
                      obj="cup")
    rig = FakeRig(kin, q0)
    rig.grip = rig.wait = lambda *a, **k: None
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd, held=Held("cup", np.eye(4))))
    RUN.run(rig, plan, lambda state, frm, prior: plan_place(kin, state, _at(q_p[:3]), 0.03, 0.07, (np.zeros(9),),
                                                           start=frm, prior=prior, obj="cup"))
    arrive = next(kw for e, kw in rig.events if e == "anchor" and kw["target"] == "place_arrive")
    assert arrive["kept"] == ["place_reach", "place_down", "place_pull_out"] and arrive["rebuilt"] == []


def _job_rig():
    kin = FakeKin()
    kin.rest, kin.drive = np.zeros(9), np.full(9, 0.1)
    return SimpleNamespace(kin=kin, log=lambda *a, **k: None)


def test_the_jobs_run_the_found_plan_and_rebuild_from_the_same_target():
    from zeno_skills.skill_jobs import pick as PJ, place as LJ
    calls = []

    def plan_pick_(kin, state, grasp, carry_goals, start="pick_open", prior=None, step=0.003, stop=None):
        calls.append(("pick", grasp, start, prior))
        return Plan(())

    def plan_place_(kin, state, goal, pre_open, out_len, rest_goals, start="place_reach", prior=None, step=0.003,
                    obj=None, on=None, edge_box=None, cavity=None):
        calls.append(("place", goal, start, prior, on))
        return Plan(())
    found = Plan((Segment("pick_grasp", Spec(), np.zeros(9)),))
    plan, rebuild, hooks = PJ._pick_ready(_job_rig(), "cup", {"kind": "top_pinch", "pre_open": 0.03}, GRASP, found,
                                          None, {}, plan_pick_)
    assert plan is found and not calls                                 # nothing re-measured, nothing made again
    rebuild(_state(np.zeros(9)), "pick_reach", plan)
    assert calls[-1][1] is GRASP and calls[-1][2:] == ("pick_reach", plan)
    goal = _at([0.5, 0.0, 0.10])
    plan, rebuild, hooks = LJ._place_ready(_job_rig(), "cup", {"name": "kitchen_cabinet_6/top"}, goal, 0.03, found,
                                           plan_place_)
    assert plan is found and len(calls) == 1
    rebuild(_state(np.zeros(9)), "tuck", plan)
    # the release lets the load touch what it is set down on (release_spec)
    assert calls[-1][1] is goal and calls[-1][2:] == ("tuck", plan, "kitchen_cabinet_6")
    assert LJ._set_down_on({"name": "rim:handled_cooking_pot"}) == "handled_cooking_pot"


def test_a_reach_in_is_judged_stopped_short_against_where_it_sent_the_hand():
    # after the reach-in: how far the hand stopped off where the reach-in sent it (Rig._settle's measure,
    # rig.last_off), whatever the object did -- whether its grasp still stood was checked before it ran
    from zeno_skills.motion_state import SkillFailure
    from zeno_skills.skill_jobs import pick as PJ
    rig = _job_rig()
    rig.q_cmd = _q(0.3, 0.0, 0.40)
    _, _, hooks = PJ._pick_ready(rig, "cup", {"kind": "top_pinch", "pre_open": 0.03}, GRASP, Plan(()), None, {},
                                 lambda *a, **k: Plan(()))
    rig.last_off = 0.003                                             # 3 mm off: reached
    hooks["pick_grasp"]["after"](rig)
    rig.last_off = 0.010                                             # 1 cm off: blocked
    with pytest.raises(SkillFailure, match="stopped 0.010 m short"):
        hooks["pick_grasp"]["after"](rig)


# ------------------------------------------------------------------- the State the same at every build
def test_a_pull_out_built_again_after_the_release_still_lets_the_fingers_touch_what_they_let_go():
    # run builds the rest again from the State read after the release: the hand holds nothing then
    # (the release hook has cleared rig.held); the object set down is given, not read off the hand
    q = _q(0.5, 0.0, 0.10)
    kin = _place_kin()
    planned = plan_place(kin, _state(q, held=Held("cup", np.eye(4))), _at(q[:3]), 0.03, 0.07,
                         (_q(0.3, 0.0, 0.40),), start="place_release")
    rebuilt = plan_place(kin, _state(q), _at(q[:3]), 0.03, 0.07, (_q(0.3, 0.0, 0.40),),
                         start="place_pull_out", obj="cup")
    assert _named(planned, "place_pull_out").spec.touch == _named(rebuilt, "place_pull_out").spec.touch == ("cup",)
    assert _named(planned, "place_release").spec.allow.touch == ("cup",)        # the release declares it too
    assert "place_pull_out" in planned.info["stage_s"]


def test_the_place_tuck_takes_the_first_free_of_its_goals_as_a_joint_set():
    q = _q(0.5, 0.0, 0.10)
    kin = _place_kin(wall=lambda p: p[2] < 0.06)                    # the fold (low) collides here
    plan = plan_place(kin, _state(q), _at(q[:3]), 0.03, 0.07,
                      (_q(0.5, 0.0, 0.05), _q(0.3, 0.0, 0.40)), start="tuck", obj="cup")
    assert plan.segments[0].info["chosen"] == 1 and np.allclose(plan.segments[0].q_end, _q(0.3, 0.0, 0.40))


def test_a_pick_opens_the_hand_in_its_own_state_for_every_later_stage():
    # the search and a rebuild alike: plan_pick moves the State's hand to pre_open itself
    seen = []
    st = State(base=(0.0, 0.0, 0.0), **chains(_q(0.3, 0.0, 0.40), np.zeros(7)),
               hands={"right": Hand(width=0.0)}, objects={"cup": np.eye(4)})
    plan = plan_pick(FakeKin(near_z=0.12, ik=[_q(0.3, 0.0, 0.40)]), st, GRASP, _carry(seen))
    assert isinstance(plan, Plan) and seen and seen[0].hands["right"].width == GRASP["pre_open"]


def test_every_action_is_declared_to_the_contact_monitor(monkeypatch):
    rig = FakeRig(FakeKin(), np.zeros(9))
    rig.grip = lambda *a, **k: None
    seg = Segment("pick_open", Spec(), np.zeros(9), kind="action", action=("grip", 0.03, 40, False))
    RUN.execute(rig, seg)
    assert rig.declared == [("pick_open", "right")]


def test_a_contact_exit_measured_again_within_half_the_margin_holds(monkeypatch):
    seg = Segment("pick_lift", Spec(allow=P_LEAVE()), np.zeros(9), (np.full(9, 0.01),),
                  info={"u": np.array([0, 0, 1.0]), "touching": "near_world", "step": 0.002, "length": 0.016})
    for measured, holds in ((0.018, True), (0.014, True), (0.016 + P.EXTENT_TOL + 0.001, False)):
        monkeypatch.setattr(P, "contact_extent", lambda *a, m=measured, **k: P.Extent(np.zeros(9), (), m, True))
        assert (P.holds(FakeKin(), _state(np.zeros(9)), seg) is None) == holds, measured


def P_LEAVE():
    from zeno_skills.clearance import LEAVE_CONTACT
    return LEAVE_CONTACT



# ------------------------------------------------------------------- the failure exit (docs 8.6)
def test_the_failure_exit_opens_an_empty_hand_and_backs_out_of_the_contact_straight_up():
    from zeno_skills.skill_plans import plan_clear
    kin = FakeKin(near_z=0.12)                                       # touching below 12 cm
    plan = plan_clear(kin, _state(_q(0.5, 0.0, 0.10)), open_width=0.04)
    assert [s.name for s in plan.segments] == ["fail_clear_open", "fail_clear"]
    assert plan.segments[0].action[:2] == ("grip", 0.04) and plan.segments[1].spec.allow.from_contact
    assert plan.segments[1].q_end[2] > 0.12                          # clear of the contact
    assert plan_clear(kin, _state(_q(0.5, 0.0, 0.10)), leave=False, open_width=None) is None   # nothing asked
    held = _state(_q(0.5, 0.0, 0.10), held=Held("cup", np.eye(4)))
    assert plan_clear(kin, held, open_width=0.04) is None            # opening would drop the load


def test_a_hook_failure_that_asks_for_the_exit_has_it_run_before_it_is_raised(monkeypatch):
    from zeno_skills.motion_state import clearing
    rig = FakeRig(FakeKin(), np.zeros(9))
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    asked = []
    exit_plan = Plan((_seg("fail_clear", np.full(9, 0.1), np.full(9, 0.3)),))

    def hook(act):
        raise clearing(SkillFailure("not pinched"), 0.04)
    with pytest.raises(SkillFailure, match="not pinched"):
        RUN.run(rig, Plan((_seg("a", np.zeros(9), np.full(9, 0.1)),)), None, {"a": {"after": hook}},
                clear=lambda st, what: asked.append(what) or exit_plan)
    assert asked == [{"open_width": 0.04, "leave": True, "ticks": 60, "side": None}] and np.allclose(rig.q_cmd, 0.3)
    with pytest.raises(SkillFailure):                                # not asked: no exit
        RUN.run(rig, Plan((_seg("b", rig.q_cmd, np.full(9, 0.4)),)), None,
                {"b": {"after": lambda a: (_ for _ in ()).throw(SkillFailure("plain"))}},
                clear=lambda st, what: pytest.fail("ran an exit nobody asked for"))


def test_a_wait_segment_lets_the_world_settle_through_the_actuator():
    rig = FakeRig(FakeKin(), np.zeros(9))
    waited = []
    rig.wait = waited.append
    RUN.execute(rig, Segment("place_settle", Spec(), np.zeros(9), kind="action", action=("wait", 90)))
    assert waited == [90] and rig.declared == [("place_settle", "right")]


def test_the_skill_jobs_hooks_do_not_move_the_robot():
    # docs 8.6: hooks and results judge, register and log; the motion is a plan run.run makes
    import ast
    from pathlib import Path
    moves = {"grip", "leave", "step", "move_to", "follow", "drive_base", "swing", "tuck", "_planning",
             "_fingers_checked", "joint_path"}
    for f in (Path(__file__).resolve().parents[1] / "zeno_skills" / "skill_jobs").glob("*.py"):
        calls = [n for n in ast.walk(ast.parse(f.read_text())) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                 and n.func.value.id in ("rig", "r") and n.func.attr in moves]
        assert not calls, (f.name, [(c.lineno, c.func.attr) for c in calls])


def test_the_skill_jobs_held_checks_ask_for_the_exit_rather_than_open_the_hand():
    # docs 8.6: a drop found by a job's check (a hook, or before its plan) is a clearing that run's failure exit
    # opens the hand for -- check_held's own grip (open_hand=True) is the old entries' (HAND_PLAN 7)
    import ast
    from pathlib import Path
    for f in (Path(__file__).resolve().parents[1] / "zeno_skills" / "skill_jobs").glob("*.py"):
        for n in ast.walk(ast.parse(f.read_text())):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)):
                continue
            assert n.func.id != "check_left_held", (f.name, n.lineno)
            if n.func.id in ("check_held", "check_both_held"):
                kw = {k.arg: k.value for k in n.keywords}
                assert isinstance(kw.get("open_hand"), ast.Constant) and kw["open_hand"].value is False, \
                    (f.name, n.lineno)


def test_a_rest_failing_only_at_the_tuck_runs_and_makes_the_tuck_when_the_arm_gets_there(monkeypatch):
    # docs 1 rule 8: the tuck's trajectory is made late -- an anchor's rebuild that makes everything but it
    # keeps what it made; the tuck is built from the State when it is reached, and fails the skill then
    from zeno_skills.skill_plans._common import anchor
    rig = FakeRig(FakeKin(), np.zeros(9))
    monkeypatch.setattr(RUN, "observe", lambda rig: _state(rig.q_cmd))
    plan = Plan((anchor("held", np.zeros(9), _state(np.zeros(9))), _seg("ride", np.zeros(9), np.full(9, 0.1)),
                 _seg("tuck", np.full(9, 0.1), np.full(9, 0.2))))
    asked = []

    def rebuild(state, name, prior):
        asked.append(name)
        if name == "ride":                      # at the anchor: the ride made again, its tuck not (TRAJOPT_FAIL)
            return Failure("TRAJOPT_FAIL", "tuck", {"partial": Plan((_seg("ride", state.q("right"), np.full(9, 0.15)),))})
        return Plan((_seg("tuck", state.q("right"), np.full(9, 0.2)),))
    done = RUN.run(rig, plan, rebuild)
    assert asked == ["ride", "tuck"] and [s.name for s in done] == ["held", "ride", "tuck"]
    assert np.allclose(done[1].q_end, 0.15) and np.allclose(done[2].q_from, 0.15)
    assert any(ev == "late" and kw["segment"] == "tuck" for ev, kw in rig.events)
    rig = FakeRig(FakeKin(), np.zeros(9))
    no_tuck = lambda state, name, prior: Failure("TRAJOPT_FAIL", "tuck", {"partial": Plan(
        (_seg("ride", state.q("right"), np.full(9, 0.15)),) if name == "ride" else ())})
    with pytest.raises(SkillFailure, match="tuck.*TRAJOPT_FAIL"):      # reached and still not made: the skill fails
        RUN.run(rig, plan, no_tuck)
