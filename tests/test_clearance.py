"""Collision policy of robot motions (zeno_skills/clearance.py, docs/COLLISION_AUDIT.md)."""

from types import SimpleNamespace

import numpy as np
import pytest

from tools.audit_collision import bool_switches, sites
from zeno_skills.clearance import FREE, LEGACY, Allow, Clearance, unchecked

# motions still passed allow=LEGACY (unchecked, not migrated).  Lower it as they move to a real
# Allow; it must never go up.
LEGACY_BUDGET = 111


def test_motions_take_allow_not_a_boolean_switch():
    assert bool_switches() == []


def test_legacy_motions_only_decrease():
    n = sum(1 for *_, kind, _ in sites() if kind == "LEGACY")
    assert n <= LEGACY_BUDGET, f"{n} LEGACY motions > budget {LEGACY_BUDGET}: give new motions a real Allow"


def test_contact_needs_a_reason():
    with pytest.raises(ValueError):
        unchecked("")
    with pytest.raises(ValueError):
        Allow(hand="right", touch=("mug",))
    assert FREE.checked and not LEGACY.checked and LEGACY.reason


def test_permits_only_the_listed_hand_links_and_entities():
    grip = Allow(hand="right", touch=("kitchen_cabinet_6",), reason="handle")
    assert grip.permits("right_gripper_left_finger_link", "kitchen_cabinet_6")
    assert not grip.permits("right_gripper_link", "kitchen_cabinet_6")          # fingers only
    assert not grip.permits("right_arm_link_6", "kitchen_cabinet_6")
    assert not grip.permits("left_gripper_left_finger_link", "kitchen_cabinet_6")
    assert not grip.permits("right_gripper_left_finger_link", "kitchen_island")
    hand = Allow(hand="right", links="hand", touch=("kitchen_island",), reason="wipe")
    assert hand.permits("right_gripper_link", "kitchen_island")
    assert hand.permits("right_gripper_camera_link", "kitchen_island/top")      # a support of it
    assert not FREE.permits("right_gripper_left_finger_link", "mug")
    assert not LEGACY.permits("right_gripper_left_finger_link", "mug")


def test_a_skill_starts_with_fresh_collision_settings_and_restores_the_callers():
    kin, left = SimpleNamespace(coll_kw={"hand_touches_part": True}), SimpleNamespace(coll_kw={"ignore_fingers": True})
    rig = SimpleNamespace(kin=kin, left_kin=left)
    clear = Clearance(rig)
    with clear.skill("place"):
        assert kin.coll_kw == {} and left.coll_kw == {} and clear.skills == ["place"]
        kin.coll_kw = {"ignore_fingers": True}               # the skill's own setting
        with clear.skill("pick"):
            assert kin.coll_kw == {} and clear.skills == ["place", "pick"]
            kin.coll_kw = {"hand_touches_part": True}
        assert kin.coll_kw == {"ignore_fingers": True}       # the nested skill's setting does not leak
    assert kin.coll_kw == {"hand_touches_part": True} and left.coll_kw == {"ignore_fingers": True}
    assert clear.skills == []


def test_monitor_logs_each_new_contact_once_and_skips_allowed_ones():
    logged = []
    hits = []
    motion = SimpleNamespace(robot_contacts=lambda rig, depth: list(hits))
    pose = [0.0]
    rig = SimpleNamespace(kin=SimpleNamespace(motion=motion, coll_kw={}), tick=0,
                          log=lambda ev, **kw: logged.append((ev, kw)),
                          base_pose=lambda: (pose[0], 0.0, 0.0), q=lambda: np.zeros(9), left_q=lambda: np.zeros(9),
                          fingers=lambda: np.zeros(2), left_fingers=lambda: np.zeros(2))
    clear = Clearance(rig)
    clear.monitor = True
    clear.skills = ["open"]
    clear.motion("open_handle", Allow(hand="right", touch=("kitchen_cabinet_6",), reason="handle"))
    hits[:] = [("right_gripper_left_finger_link", "kitchen_cabinet_6", 0.004),
               ("left_arm_link_5", "kitchen_island", 0.01)]
    def tick():
        pose[0] += 0.01                                      # the base moved: the check runs
        clear.tick()
    tick()
    tick()                                                   # the same contacts: nothing new
    hits[:] = []
    tick()
    hits[:] = [("left_arm_link_5", "kitchen_island", 0.008)]  # touching again: a new onset
    clear.tick()                                             # the robot did not move: not checked
    tick()
    s = clear.summary()
    assert s["checks"] == 4 and s["allowed"] == 1 and s["unexpected"] == 2
    assert s["by_skill"] == {"open": 2} and s["by_leg"] == {"open_handle": 2}
    assert [ev for ev, _ in logged] == ["unexpected_contact", "unexpected_contact"]
    assert logged[0][1]["contacts"] == [{"link": "left_arm_link_5", "entity": "kitchen_island", "depth_m": 0.01}]


def test_the_contact_monitor_switch_does_not_change_the_profile_hash(tmp_path):
    from episode.profile import load_profile
    on, off = tmp_path / "on.yaml", tmp_path / "off.yaml"
    on.write_text("execution:\n  contact_monitor: true\n")
    off.write_text("execution:\n  contact_monitor: false\n")
    a, b = load_profile(str(on)), load_profile(str(off))
    assert a["execution"]["contact_monitor"] and not b["execution"]["contact_monitor"]
    assert a["hash"] == b["hash"]
