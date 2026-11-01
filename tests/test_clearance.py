"""Collision policy of robot motions (zeno_skills/clearance.py, docs/COLLISION_AUDIT.md)."""

from types import SimpleNamespace

import numpy as np
import pytest

from tools.audit_collision import bool_switches, sites
from zeno_skills.clearance import FREE, FREE_ELSE_STRAIGHT, LEGACY, Allow, Clearance, unchecked

# motions still passed allow=LEGACY (unchecked, not migrated).  Lower it as they move to a real
# Allow; it must never go up.
LEGACY_BUDGET = 48


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
    with pytest.raises(ValueError):
        Allow(fallback=True)
    with pytest.raises(ValueError):
        Allow(checked=False, fallback=True, reason="x")
    assert FREE_ELSE_STRAIGHT.checked and FREE_ELSE_STRAIGHT.fallback and not FREE_ELSE_STRAIGHT.permits(
        "right_gripper_left_finger_link", "mug")


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


def test_what_a_hand_holds_may_touch_only_its_held_on_entities():
    down = Allow(hand="right", held_on=("kitchen_island",), reason="set down")
    assert down.permits("held:mug", "kitchen_island/top")
    assert not down.permits("held:mug", "juice_bottle")
    assert not down.permits("right_gripper_link", "kitchen_island")       # the hand itself: not listed
    assert not FREE.permits("held:mug", "kitchen_island")
    assert not Allow(hand="right", touch=("mug",), reason="grasp").permits("held:mug", "mug")


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


def _fallback_rig(start_free=True):
    from zeno_skills.rig import Rig
    logged = []
    kin = SimpleNamespace(free=lambda q: start_free if np.allclose(q, 0) else float(q[0]) < 0.5,
                          explain=lambda q: f"world right_arm_link_6 at {float(q[0]):.1f}")
    rig = SimpleNamespace(q_cmd=np.zeros(9), left_q_cmd=np.zeros(7), kin=kin, tick=7,
                          log=lambda ev, **kw: logged.append((ev, kw)))
    rig.clear = Clearance(rig)
    rig.clear.skills = ["place"]
    return Rig, rig, kin, logged


def test_free_else_straight_takes_the_checked_path_when_there_is_one():
    Rig, rig, kin, logged = _fallback_rig()
    asked = []
    qs, allow = Rig._checked_else_straight(rig, "place_above", lambda a: asked.append(a) or ["checked"], kin)
    assert qs == ["checked"] and allow is FREE and asked == [FREE]
    assert rig.clear.counts["planned"] == 1 and rig.clear.counts["fallback"] == 0 and logged == []


def test_free_else_straight_falls_back_to_the_straight_move_and_says_why():
    from zeno_skills.rig import SkillFailure
    Rig, rig, kin, logged = _fallback_rig()

    def plan(a):
        if a is FREE:
            raise SkillFailure("joint move to place_above: no collision-free trajectory")
        return [np.full(9, x) for x in (0.2, 0.4, 0.6, 0.8)]
    qs, allow = Rig._checked_else_straight(rig, "place_above", plan, kin)
    assert allow is LEGACY and len(qs) == 4
    s = rig.clear.summary()
    assert s["fallback"] == 1 and s["fallback_by_leg"] == {"place_above": 1}
    rec = s["fallbacks"][0]
    assert rec["skill"] == "place" and "no collision-free" in rec["why"] and rec["hit"] == "world right_arm_link_6 at 0.8"
    assert logged[0][0] == "clearance_fallback"


def test_free_else_straight_does_not_plan_from_a_colliding_start():
    Rig, rig, kin, logged = _fallback_rig(start_free=False)
    asked = []
    qs, allow = Rig._checked_else_straight(rig, "release_back", lambda a: asked.append(a) or [np.zeros(9)], kin)
    assert asked == [LEGACY] and allow is LEGACY
    assert rig.clear.fallbacks[0]["why"].startswith("starts in collision")


def test_monitor_logs_objects_pushed_away_unless_held_let_go_carried_or_allowed():
    logged = []
    poses = {"juice_bottle": [7.65, 1.66, 0.95], "mug": [7.95, 1.66, 0.92], "spoon": [7.40, 1.70, 0.87],
             "tomato": [7.0, 1.0, 0.9]}
    upright = np.array([1.0, 0.0, 0.0, 0.0])
    motion = SimpleNamespace(robot_contacts=lambda rig, depth: [],
                             _mon_near={"object:juice_bottle", "object:mug", "object:spoon", "object:tomato",
                                        "part:kitchen_cabinet_6"})
    pose = [0.0]
    rig = SimpleNamespace(kin=SimpleNamespace(motion=motion, coll_kw={}), tick=0, held=None, left_held=None,
                          log=lambda ev, **kw: logged.append((ev, kw)),
                          obj_pose=lambda n: (np.array(poses[n], float), upright),
                          base_pose=lambda: (pose[0], 0.0, 0.0), q=lambda: np.zeros(9), left_q=lambda: np.zeros(9),
                          fingers=lambda: np.zeros(2), left_fingers=lambda: np.zeros(2))
    clear = Clearance(rig)
    clear.skills = ["navigate"]

    def tick(n=30):
        rig.tick += n
        pose[0] += 0.01
        clear.tick()
    rig.held = {"name": "spoon"}
    clear.motion("drive_base", FREE)
    tick()                                                   # first look: references only
    poses["juice_bottle"][0] += 0.05                         # knocked over by the carried spoon
    poses["spoon"][0] += 0.3                                 # held: rides along
    tick()
    poses["spoon"][0] += 0.05                                # held: rides along...
    poses["tomato"][0] += 0.05                               # ...and so does what sits in it
    tick()
    rig.held = None                                          # let go of the spoon: it settles
    tick()
    poses["spoon"][2] -= 0.1
    tick()
    clear.motion("push_slide", Allow(hand="right", touch=("mug",), reason="push"))
    poses["mug"][0] += 0.1                                   # the push target moves: allowed
    tick(SETTLE := 300)
    poses["spoon"][0] += 0.05                                # long settled: now a disturbance
    tick()
    poses["tomato"][0] += 0.05                               # pushed by the hand that then picks it up
    tick()
    rig.held = {"name": "tomato"}
    tick()
    s = clear.summary()
    assert s["disturbed"] == 2 and s["disturbed_by_leg"] == {"drive_base": 1, "push_slide": 1}
    objs = [o["object"] for ev, kw in logged if ev == "disturbed_object" for o in kw["objects"]]
    assert objs == ["juice_bottle", "spoon"]
    assert s["disturbances"][0]["objects"] == [{"object": "juice_bottle", "moved_m": 0.05, "tilt_deg": 0.0}]
