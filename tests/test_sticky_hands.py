"""Sticky hands (execution.sticky_hands): profile switch, weld bookkeeping, the pick snap hook.
No simulator: the USD joint writes and the PhysX link pose are stubbed."""

from types import SimpleNamespace

import numpy as np
import pytest

from episode.profile import DEFAULTS, ProfileError, apply_rig_flags, load_profile
from zeno_skills import skill_runtime as sr
from zeno_skills import skills, sticky
from zeno_skills.rig import SkillFailure
from zeno_skills.sticky import StickyHands, failure_reason


# ----------------------------------------------------------------- profile
def test_switch_is_on_only_in_gt_sticky():
    assert DEFAULTS["execution"]["sticky_hands"] is False
    for name in ("gt", "benchmark", "oracle"):
        assert load_profile(name)["execution"]["sticky_hands"] is False
    gt, sticky = load_profile("gt"), load_profile("gt_sticky")
    assert sticky["execution"]["sticky_hands"] is True and sticky["hash"] != gt["hash"]
    # everything else is gt
    sticky["execution"]["sticky_hands"] = False
    assert {k: v for k, v in sticky.items() if k not in ("name", "hash")} == \
        {k: v for k, v in gt.items() if k not in ("name", "hash")}


def test_switch_changes_the_profile_hash_and_is_refused_with_the_gate(tmp_path):
    on = tmp_path / "gt_sticky.yaml"
    on.write_text("execution:\n  nested_repair: false\n  sticky_hands: true\n")
    off = tmp_path / "gt_plain.yaml"
    off.write_text("execution:\n  nested_repair: false\n")
    assert load_profile(on)["execution"]["sticky_hands"] is True
    assert load_profile(on)["hash"] != load_profile(off)["hash"]
    gated = tmp_path / "gated.yaml"
    gated.write_text("execution:\n  gate: true\n  mask_feedback: true\n  sticky_hands: true\n"
                     "observation:\n  gt_objects: false\n  task_status: false\n")
    with pytest.raises(ProfileError, match="sticky_hands"):
        load_profile(gated)
    bad = tmp_path / "bad.yaml"
    bad.write_text("execution:\n  sticky_hands: 1\n")
    with pytest.raises(ProfileError, match="true/false"):
        load_profile(bad)


def test_rig_flag(tmp_path):
    on = tmp_path / "on.yaml"
    on.write_text("execution:\n  sticky_hands: true\n")
    rig = SimpleNamespace()
    apply_rig_flags(rig, load_profile(on))
    assert isinstance(rig.sticky, StickyHands)
    apply_rig_flags(rig, load_profile("gt"))
    assert rig.sticky is None


# ----------------------------------------------------------------- weld bookkeeping
class FakeRig:
    def __init__(self):
        self.ann = SimpleNamespace(objects={"apple": {"body": "/World/Tasks/apple/Asset/apple"},
                                            "pin": {"body": "/World/Tasks/pin/Asset/pin"}})
        self.held = self.left_held = None
        self.grip_cmd = self.left_grip_cmd = 0.04
        self.finger_pos = np.array([0.03, 0.03])
        self.events = []

    def obj_pose(self, name):
        return np.array([0.5, 0.0, 0.9]), np.array([1.0, 0.0, 0.0, 0.0])

    def fingers(self):
        return self.finger_pos

    def left_fingers(self):
        return self.finger_pos

    def log(self, label, **kw):
        self.events.append((label, kw))


@pytest.fixture
def hands(monkeypatch):
    rig = FakeRig()
    s = StickyHands(rig)
    joints = {}
    monkeypatch.setattr(s, "link_pose", lambda hand: (np.array([0.5, 0.0, 1.0]), np.eye(3)))
    monkeypatch.setattr(s, "_add_joint", lambda hand, body, p, R: joints.__setitem__(hand, (body, p)))
    monkeypatch.setattr(s, "_remove_joint", lambda hand: joints.pop(hand))
    return rig, s, joints


def labels(rig):
    return [e[0] for e in rig.events]


def test_grasp_welds_at_the_current_relative_pose_and_opening_releases(hands):
    rig, s, joints = hands
    s.on_hold("right", {"name": "apple"})
    assert s.welded("right", "apple") and joints["right"][0].endswith("/apple")
    assert np.allclose(joints["right"][1], [0.0, 0.0, -0.1])        # body in the link frame
    s.on_open("right", 0.0)                                        # closing harder: still held
    s.on_open("right", 0.025)                                      # a lighter grip inside the contact
    assert s.welded("right")
    s.on_open("right", 0.04)                                       # wider than the fingers stand
    assert not s.welded("right") and "right" not in joints
    assert labels(rig) == ["sticky_weld", "sticky_release"]
    assert rig.events[-1][1]["why"] == "fingers_open"
    s.on_hold("right", None)                                       # nothing left to release
    assert labels(rig) == ["sticky_weld", "sticky_release"]


def test_clearing_the_hand_releases_and_episode_end_cleans_up(hands):
    rig, s, joints = hands
    s.on_hold("right", {"name": "apple"})
    s.on_hold("right", None)
    assert not joints and rig.events[-1][1]["why"] == "hand_cleared"
    s.on_hold("left", {"name": "pin"})
    s.close()
    assert not joints and rig.events[-1][1]["why"] == "episode_end"


def test_two_handed_hold_has_one_weld_and_a_handover_moves_it(hands):
    rig, s, joints = hands
    rig.held = {"name": "pin"}
    s.on_hold("right", rig.held)
    rig.left_held = {"name": "pin"}
    rig.left_grip_cmd = 0.0                                        # left hand closed on it
    s.on_hold("left", rig.left_held)
    assert set(joints) == {"right"}
    s.on_open("right", 0.04)                                       # right lets go: the left keeps it
    assert set(joints) == {"left"} and s.welded("left", "pin")
    assert rig.events[-1] == ("sticky_weld", {"hand": "left", "obj": "pin", "why": "handover",
                                              "link_to_body_m": 0.1})


def test_welded_object_is_never_reported_dropped():
    rig = SimpleNamespace(held={"name": "apple", "tcp_minus_body": np.zeros(3)},
                          sticky=SimpleNamespace(welded=lambda hand, name=None: hand == "right"))
    skills.check_held(rig, "carry")                 # would need the kinematics if it measured
    assert rig.held["name"] == "apple"


# ----------------------------------------------------------------- snap
@pytest.mark.parametrize("msg, reason", [
    ("pick orange: not held (lift -0.000 m)", "not_held"),
    ("corner pinch book: not held (lift 0.001 m)", "not_held"),
    ("pick apple: no reachable grasp from any base pose", "no_park"),
    ("corner pinch book: no base pose reaches any side", "no_park"),
    ("edge pinch book: overhang only 0.020 m", "no_park"),
    ("no IK for pick_pre", "ik"),
    ("joint move to pick_grasp: every joint-space path collides", "ik"),
    ("pick apple: microwave door is closed", "other"),
])
def test_failure_reason(msg, reason):
    assert failure_reason(msg) == reason


def test_snap_hook_needs_sticky_hands_and_keeps_an_object_already_held():
    exc = SkillFailure("no IK for microwave_pick_clear")
    rig = SimpleNamespace(sticky=None, held=None, ann=SimpleNamespace(objects={"apple": {}}))
    assert sticky.snap_pick(rig, "apple", exc) is False
    events = []
    rig = SimpleNamespace(sticky=object(), held={"name": "apple"}, ann=SimpleNamespace(objects={"apple": {}}),
                          log=lambda label, **kw: events.append(label))
    assert sticky.snap_pick(rig, "apple", exc) is True and events == ["sticky_keep"]
    rig.held = {"name": "pear"}
    assert sticky.snap_pick(rig, "apple", exc) is False


@pytest.fixture
def pick_runner(monkeypatch):
    rig = SimpleNamespace(caption="", events=[], held=None, log=lambda label, **kw: None, step=lambda n=1: None)
    monkeypatch.setattr(sr, "before_snapshot", lambda rig: {})
    monkeypatch.setattr(sr, "bind_nouns", lambda rig, c, values: {
        "object": {"grasp_types": ["top_pinch"]}, "robot": {}, "args": dict(values)})
    runner = sr.SkillContractRunner(rig, nested_repair=False)
    monkeypatch.setattr(runner, "_outputs", lambda *a: {})
    snaps = []
    monkeypatch.setattr(sticky, "snap_pick", lambda rig, name, exc: snaps.append((name, str(exc))) or True)

    def fail(*a):
        raise SkillFailure("pick apple: not held (lift 0.000 m)")
    monkeypatch.setattr(runner, "_run_steps", fail)
    return runner, snaps


def test_runner_completes_a_physically_failed_pick(pick_runner, monkeypatch):
    runner, snaps = pick_runner
    monkeypatch.setattr(runner, "_check", lambda atoms, values, nouns, ctx, sink, advisory=(): [])
    res = runner.run("pick", {"object": "apple"})
    assert res.success and res.error is None
    assert snaps == [("apple", "pick apple: not held (lift 0.000 m)")]
    assert res.policy_steps[-1]["sticky"] == "snap"


def test_runner_never_snaps_a_precondition_failure(pick_runner, monkeypatch):
    runner, snaps = pick_runner
    monkeypatch.setattr(runner, "_check", lambda atoms, values, nouns, ctx, sink, advisory=():
                        ["hand_empty(hand=right) is false (right holds pear)"] if sink is not None and
                        any(a["pred"] == "hand_empty" for a in atoms) else [])
    res = runner.run("pick", {"object": "apple"})
    assert not res.success and res.error_code == "PRECONDITION_FAILED" and snaps == []


def test_caught_neighbour_is_the_container_lifted_along_not_the_load():
    now = {"apple": [0.9, -0.36, 0.80], "basket": [0.92, -0.43, 0.79], "lid": [0.9, -0.36, 0.86],
           "orange": [0.93, -0.40, 0.75], "bowl": [3.0, 1.0, 0.80]}
    before = {"bottoms": {"apple": [0.9, -0.36, 0.76], "basket": [0.92, -0.43, 0.75],
                          "lid": [0.9, -0.36, 0.82], "orange": [0.93, -0.40, 0.75], "bowl": [3.0, 1.0, 0.75]}}
    rig = SimpleNamespace(q=lambda: None, kin=SimpleNamespace(tcp=lambda q: (np.array([0.9, -0.36, 0.85]), np.eye(3))),
                          geo=SimpleNamespace(bottom=lambda o, st: np.array(now[o]),
                                              centre=lambda o, st: np.array(now[o]) + [0, 0, 0.04]))
    st = {"objects": {o: {} for o in now}}
    # the basket rose 4 cm with the apple; the lid on it is its load; the orange stayed; the bowl is far away
    assert sticky.caught_neighbours(rig, "apple", before, st) == [("basket", 0.04)]
