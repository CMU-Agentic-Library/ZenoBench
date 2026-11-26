"""HAND_PLAN 9a: what each hand holds, read and checked the same way for both (skills.check_held by side), and
the skills still on the old entries refusing a load in the left hand with a message that says so."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import skills
from zeno_skills.motion_state import Dropped
from zeno_skills.rig import SkillFailure


def _rig(tcp_r=(0.0, 0.0, 1.0), tcp_l=(0.0, 0.5, 1.0), body=(0.0, 0.5, 0.9), fingers_l=(0.02, 0.02)):
    grips = []
    rig = SimpleNamespace(held=None, left_held={"name": "cup", "tcp_minus_body": np.array([0.0, 0.0, 0.1])},
                          kin=SimpleNamespace(tcp=lambda q: (np.array(tcp_r, float), np.eye(3))),
                          left_kin=SimpleNamespace(tcp=lambda q: (np.array(tcp_l, float), np.eye(3))),
                          q=lambda: np.zeros(9), left_q=lambda: np.zeros(9),
                          fingers=lambda: np.array([0.02, 0.02]), left_fingers=lambda: np.array(fingers_l, float),
                          obj_pose=lambda name: (np.array(body, float), None), log=lambda *a, **k: None,
                          grip=lambda w, steps, side="right": grips.append((w, side)))
    return rig, grips


def test_the_left_hand_is_checked_as_the_right_is():
    rig, grips = _rig()
    skills.check_held(rig, "carry", side="left")                   # 0.1 m from the TCP as at the grasp: held
    rig, grips = _rig(body=(0.0, 0.5, 0.84))                       # shifted 6 cm in the pinch (HELD_SLIP..
    skills.check_held(rig, "carry", side="left")                   # HELD_SHIFT_MAX): re-anchored
    assert np.allclose(rig.left_held["tcp_minus_body"], [0.0, 0.0, 0.16]) and not grips
    rig, grips = _rig(body=(0.0, 0.5, 0.5))                        # gone: dropped, that hand opened
    with pytest.raises(Dropped, match="left hand"):
        skills.check_held(rig, "carry", side="left")
    assert rig.left_held is None and grips == [(0.04, "left")]


def test_an_old_skill_refuses_a_load_in_the_left_hand_and_says_so():
    rig, _ = _rig()
    with pytest.raises(SkillFailure, match="cup is in the left hand.*right hand only"):
        skills.right_hand_only(rig, "cup", "hover")
    rig.held, rig.left_held = {"name": "cup"}, None
    skills.right_hand_only(rig, "cup", "hover")                    # the right hand's: fine


def test_the_drive_cap_is_the_same_for_either_hand():
    # the user's 11-24 decision (HAND_PLAN 6.3): the left's limits mirror the right's -- a load in either hand drives
    # at DRIVE_LOADED, a container in a one-hand rim pinch in either hand at DRIVE_SWINGING
    from types import SimpleNamespace
    from zeno_skills.rig import DRIVE_EMPTY, DRIVE_LOADED, DRIVE_SWINGING, Rig

    def rig(right=None, left=None, containers=()):
        return SimpleNamespace(held=right, left_held=left, _held_container=lambda side="right": side in containers)
    assert Rig._drive_cap(rig()) == DRIVE_EMPTY
    assert Rig._drive_cap(rig(right={"name": "cup"})) == DRIVE_LOADED
    assert Rig._drive_cap(rig(left={"name": "cup"})) == DRIVE_LOADED
    assert Rig._drive_cap(rig(left={"name": "pot"}, containers=("left",))) == DRIVE_SWINGING
    assert Rig._drive_cap(rig(right={"name": "pen"}, left={"name": "pot"}, containers=("left",))) == DRIVE_SWINGING
