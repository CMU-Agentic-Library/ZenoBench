"""Sticky hands (execution.sticky_hands: carry / snap): profile levels, weld bookkeeping, the pick snap hook.
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
LEVELS = {"physical": False, "sticky": "carry", "sticky_snap": "snap"}


def _body(p):
    return {k: v for k, v in p.items() if k not in ("name", "hash")}


def test_three_levels_each_with_gt_and_benchmark():
    assert DEFAULTS["execution"]["sticky_hands"] is False
    assert load_profile("oracle")["execution"]["sticky_hands"] is False
    base = {"gt": load_profile("gt"), "benchmark": load_profile("benchmark")}
    assert load_profile("physical/gt")["name"] == "gt"                    # physical/ goes by the bare name
    for level, value in LEVELS.items():
        for kind in ("gt", "benchmark"):
            prof = load_profile(kind if level == "physical" else f"{level}/{kind}")
            assert prof["name"] == (kind if level == "physical" else f"{level}/{kind}")
            assert prof["execution"]["sticky_hands"] == value
            # everything else is the physical profile's
            prof["execution"]["sticky_hands"] = False
            assert _body(prof) == _body(base[kind])
    hashes = {load_profile(f"{lv}/{k}")["hash"] for lv in LEVELS for k in ("gt", "benchmark")}
    assert len(hashes) == 6


def test_switch_values_and_hash(tmp_path):
    files = {}
    for v in ("false", "carry", "snap"):
        files[v] = tmp_path / f"{v}.yaml"
        files[v].write_text(f"execution:\n  nested_repair: false\n  sticky_hands: {v}\n")
    assert [load_profile(f)["execution"]["sticky_hands"] for f in files.values()] == [False, "carry", "snap"]
    assert len({load_profile(f)["hash"] for f in files.values()}) == 3
    for bad in ("true", "1", "weld"):
        f = tmp_path / "bad.yaml"
        f.write_text(f"execution:\n  sticky_hands: {bad}\n")
        with pytest.raises(ProfileError, match="sticky_hands"):
            load_profile(f)


def test_rig_flag():
    rig = SimpleNamespace()
    apply_rig_flags(rig, load_profile("sticky/gt"))
    assert isinstance(rig.sticky, StickyHands) and rig.sticky.snap_on is False
    apply_rig_flags(rig, load_profile("sticky_snap/benchmark"))
    assert isinstance(rig.sticky, StickyHands) and rig.sticky.snap_on is True
    apply_rig_flags(rig, load_profile("gt"))
    assert rig.sticky is None


def test_carry_level_never_snaps():
    exc = SkillFailure("pick apple: not held (lift 0.000 m)")
    rig = SimpleNamespace(sticky=SimpleNamespace(snap_on=False), held=None, ann=SimpleNamespace(objects={"apple": {}}))
    assert sticky.snap_pick(rig, "apple", exc) is False
    assert sticky.snap_place(rig, "apple", "table/top", None, {}, "x") is False
    rig.held = {"name": "apple"}
    assert sticky.snap_pick(rig, "apple", exc) is False                   # a later pick leg failed: stays failed


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
    rig = SimpleNamespace(sticky=SimpleNamespace(snap_on=True), held={"name": "apple"}, ann=SimpleNamespace(objects={"apple": {}}),
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


# ----------------------------------------------------------------- place
def _quat(R):
    return sticky._wxyz(R)


def test_rest_orientation_levels_the_axis_nearest_vertical_and_keeps_its_sign():
    from scipy.spatial.transform import Rotation
    tilted = Rotation.from_euler("xz", [15, 40], degrees=True).as_matrix()       # drooped 15 deg in the hand
    R = sticky.rest_R(_quat(tilted))
    assert np.allclose(R[:, 2], [0, 0, 1], atol=1e-9)
    assert abs(np.degrees(np.arctan2(R[1, 0], R[0, 0])) - 40) < 1.0             # yaw kept
    face_down = Rotation.from_euler("xz", [170, -20], degrees=True).as_matrix()
    assert np.allclose(sticky.rest_R(_quat(face_down))[:, 2], [0, 0, -1], atol=1e-9)   # stays face down
    on_side = Rotation.from_euler("x", 80, degrees=True).as_matrix()
    assert np.allclose(sticky.rest_R(_quat(on_side))[:, 1], [0, 0, 1], atol=1e-9)


@pytest.fixture
def place_runner(monkeypatch):
    rig = SimpleNamespace(caption="", events=[], held=None, log=lambda label, **kw: None, step=lambda n=1: None)
    monkeypatch.setattr(sr, "before_snapshot", lambda rig: {"objects": {}})
    monkeypatch.setattr(sr, "bind_nouns", lambda rig, c, values: {
        "receptacle": {"kind": "support", "category": "TableDining"}, "robot": {"right_kind": "pinch"},
        "args": dict(values)})
    runner = sr.SkillContractRunner(rig, nested_repair=False)
    monkeypatch.setattr(runner, "_outputs", lambda *a: {})
    placed = []
    monkeypatch.setattr(sticky, "snap_place", lambda rig, name, rec, hint, before, err:
                        placed.append((name, rec, hint, str(err))) or True)
    return runner, placed


def test_runner_completes_a_physically_failed_place(place_runner, monkeypatch):
    runner, placed = place_runner

    def fail(*a):
        raise SkillFailure("place book on table/top: bottom at (1.36, -0.65, 0.116), tilt 60 deg")
    monkeypatch.setattr(runner, "_run_steps", fail)
    monkeypatch.setattr(runner, "_check", lambda atoms, values, nouns, ctx, sink, advisory=(): [])
    res = runner.run("place", {"object": "book", "receptacle": "table/top", "hint_xy": [1.0, 2.0]})
    assert res.success and res.error is None and res.selected_path == "surface"
    assert placed == [("book", "table/top", [1.0, 2.0], "place book on table/top: bottom at (1.36, -0.65, 0.116), "
                                                        "tilt 60 deg")]
    assert res.policy_steps[-1]["sticky"] == "place"


def test_runner_places_again_when_the_object_ended_off_the_receptacle(place_runner, monkeypatch):
    runner, placed = place_runner
    monkeypatch.setattr(runner, "_run_steps", lambda *a: None)
    calls = []

    def check(atoms, values, nouns, ctx, sink, advisory=()):
        if not any(a["pred"] == "on" for a in atoms):
            return []
        calls.append(1)
        return ["on(object=book, support=table/top) is false"] if len(calls) == 1 else []
    monkeypatch.setattr(runner, "_check", check)
    res = runner.run("place", {"object": "book", "receptacle": "table/top"})
    assert res.success and len(calls) == 2
    assert placed and placed[0][3] == "on(object=book, support=table/top) is false"


def test_place_failure_stays_a_failure_without_sticky_hands(monkeypatch):
    rig = SimpleNamespace(sticky=None, ann=SimpleNamespace(objects={"book": {}}))
    assert sticky.snap_place(rig, "book", "table/top", None, {}, "x") is False
