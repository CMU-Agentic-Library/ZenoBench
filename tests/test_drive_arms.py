"""The one arrival rule (run.arrived): an arm sent to a pose that stopped short fails the skill; an arm a
contact pushed off a travel posture on a drive is commanded where it stands (Actuator.hold_arm), so the
State -- the commanded joints -- has it where it is and the next plan starts from it (s10 T03
utensils_apart 11-26: the right arm pushed 0.59 m off its fold by the wall beside bookcase_2, found only
at the next tuck).  And the margin DRIVE_GAP the base checks keep."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import run as RUN
from zeno_skills import tolerances as T
from zeno_skills.motion_state import SkillFailure
from zeno_skills.rig import Rig


def _seg(kind, name="seg"):
    return SimpleNamespace(kind=kind, name=name, info={})


def _act():
    held = []
    return SimpleNamespace(hold_arm=lambda side, label, off: held.append((side, label, off))), held


def test_a_drive_takes_an_arm_pushed_off_as_it_stands():
    act, held = _act()
    RUN.arrived(act, _seg("drive", "navigate_bin"), {"right": 0.59, "left": 0.001})
    assert held == [("right", "navigate_bin", 0.59)]


def test_a_drive_whose_arms_are_back_holds_nothing():
    act, held = _act()
    RUN.arrived(act, _seg("drive"), {"right": T.TARGET_TOL, "left": 0.0})
    assert held == []


def test_an_arm_sent_to_a_pose_that_stopped_short_fails_and_one_that_arrived_does_not():
    act, held = _act()
    with pytest.raises(SkillFailure, match="tuck: the arm stopped 0.591 m short"):
        RUN.arrived(act, _seg("move", "tuck"), 0.591)
    RUN.arrived(act, _seg("move", "tuck"), T.TARGET_TOL)
    RUN.arrived(act, _seg("action"), None)
    assert held == []


def _rig(q_r, q_l):
    logs = []
    r = SimpleNamespace(q_cmd=np.r_[0.1, -0.05, np.full(7, 0.3)], left_q_cmd=np.full(7, -0.3), _drive_from=40,
                        clear=SimpleNamespace(physx_records=[
                            {"tick": 10, "link": "right_arm_link_5", "entity": "wall_1"},       # an earlier drive
                            {"tick": 50, "link": "right_arm_link_5", "entity": "wall_586"},
                            {"tick": 60, "link": "left_gripper_link", "entity": "wall_366"}]),
                        log=lambda label, **kw: logs.append((label, kw)))
    r.q = lambda: np.asarray(q_r, float)
    r.left_q = lambda: np.asarray(q_l, float)
    return r, logs


def test_holding_an_arm_commands_it_where_it_stands_and_keeps_the_body():
    q_r = np.r_[0.12, -0.04, 0.27, 0.56, -0.15, 0.0, -0.43, 0.02, -1.09]      # T03: the right arm 0.59 m off
    r, logs = _rig(q_r, np.zeros(9))
    body = r.q_cmd[:2].copy()
    Rig.hold_arm(r, "right", "navigate_bin", 0.59)
    assert np.allclose(r.q_cmd[2:], q_r[2:]) and np.allclose(r.q_cmd[:2], body) and np.allclose(r.left_q_cmd, -0.3)
    (label, kw), = logs
    assert label == "drive_pushed" and kw["side"] == "right" and kw["off"] == 0.59
    assert kw["contacts"] == ["right_arm_link_5 / wall_586"]        # this drive's, this arm's


def test_holding_the_left_arm_keeps_the_body_and_the_right_arm():
    q_l = np.r_[0.3, 0.2, np.full(7, 0.7)]
    r, logs = _rig(np.zeros(9), q_l)
    right = r.q_cmd.copy()
    Rig.hold_arm(r, "left", "navigate", 0.2)
    assert np.allclose(r.left_q_cmd, 0.7) and np.array_equal(r.q_cmd, right)
    assert logs[0][1]["contacts"] == ["left_gripper_link / wall_366"]


def test_the_drive_margin_is_two_centimetres():
    assert T.DRIVE_GAP == 0.02 and T.DRIVE_GAP > T.DEPTH_TOL
