"""The motion record (zeno_skills/clearance.py Clearance.motion / executing, result.json
``contacts.segments``) and its signature diff (tools/motion_signature.py)."""

import json
from types import SimpleNamespace

from tools.motion_signature import compare, signature, to_json
from zeno_skills.clearance import (BASE_DRIVE, FREE, FREE_ELSE_STRAIGHT, LEAVE_CONTACT, LEGACY, Clearance,
                                   allow_kind, into_contact, lifting, unchecked)


def _rig(relaxed=None):
    relaxed = relaxed if relaxed is not None else {}
    motion = SimpleNamespace(take_relaxed=lambda side: relaxed.pop(side, set()))
    rig = SimpleNamespace(kin=SimpleNamespace(motion=motion, coll_kw={}), left_kin=None, tick=0,
                          held=None, left_held=None, log=lambda ev, **kw: None)
    rig.clear = Clearance(rig)
    return rig


def test_allow_kinds_name_the_rule_a_motion_runs_under():
    assert allow_kind(FREE) == "free"
    assert allow_kind(FREE_ELSE_STRAIGHT) == "planned"
    assert allow_kind(LEGACY) == "legacy"
    assert allow_kind(LEGACY, fell_back=True) == "fallback"
    assert allow_kind(BASE_DRIVE) == "base_drive"
    assert allow_kind(LEAVE_CONTACT) == "leave_contact"
    assert allow_kind(lifting("mug")) == "lifting"
    assert allow_kind(into_contact(touch=("mug",))) == "into_contact"
    assert allow_kind(unchecked("swing: the posture switch was checked")) == "unchecked: swing"


def test_each_motion_is_a_row_with_its_skill_arm_load_and_relaxations():
    relaxed = {"right": {"exempt", "fingers"}}
    rig = _rig(relaxed)
    with rig.clear.skill("place"):
        rig.held = {"name": "mug"}
        rig.clear.motion("place_down", FREE_ELSE_STRAIGHT)
        rig.clear.executing()
    seg, = rig.clear.segments
    assert seg["skill"] == "place" and seg["leg"] == "place_down" and seg["side"] == "right"
    assert seg["allow"] == "planned" and seg["holding"] and seg["relaxed"] == ["exempt", "fingers"]
    rig.clear.motion("tuck", FREE)                           # relaxations are taken once
    assert rig.clear.segments[-1]["relaxed"] == []
    assert rig.clear.summary()["segments"] == rig.clear.segments


def test_a_fallback_is_recorded_as_such_and_only_once():
    rig = _rig()
    rig.clear.fallback("carry", "no path")
    rig.clear.motion("carry", LEGACY)
    rig.clear.motion("tuck", LEGACY)
    assert [s["allow"] for s in rig.clear.segments] == ["fallback", "legacy"]


def test_waypoints_followed_with_no_motion_declared_are_a_raw_row():
    rig = _rig()
    rig.clear.motion("pick_lift", FREE)
    rig.clear.executing()                                    # declared: no extra row
    rig.clear.executing()                                    # a second follow of nothing declared
    rig.clear.motion("drive_base", BASE_DRIVE, side="base", follows=False)
    rig.clear.executing()                                    # a drive runs its own loop: a follow after it is raw
    assert [(s["leg"], s["allow"]) for s in rig.clear.segments] == [
        ("pick_lift", "free"), ("pick_lift", "raw"), ("drive_base", "base_drive"), ("drive_base", "raw")]


def _run(tmp_path, name, segs):
    d = tmp_path / name / "T01" / "s10@sticky_gt"
    d.mkdir(parents=True)
    (d / "result.json").write_text(json.dumps({"contacts": {"segments": segs}}))
    return tmp_path / name


def test_signature_diff_shows_motions_that_appear_or_disappear_not_fallback_noise(tmp_path):
    seg = lambda leg, allow, relaxed=(): {"skill": "pick", "leg": leg, "side": "right", "allow": allow,
                                          "holding": False, "relaxed": list(relaxed)}
    before = _run(tmp_path, "before", [seg("pick_approach", "planned", ["exempt"]), seg("tuck", "free")])
    after = _run(tmp_path, "after", [seg("pick_approach", "fallback"), seg("tuck", "free", ["fingers"])])
    snap = to_json(*signature([before]))
    added, gone, moved = compare(to_json(*signature([after])), snap)
    assert [(r["leg"], r["relaxed"]) for r in added] == [("pick_approach", "-"), ("tuck", "fingers")]
    assert [(r["leg"], r["relaxed"]) for r in gone] == [("pick_approach", "exempt"), ("tuck", "-")]
    assert moved == []
    same = _run(tmp_path, "same", [seg("pick_approach", "fallback", ["exempt"]), seg("tuck", "free")])
    added, gone, moved = compare(to_json(*signature([same])), snap)
    assert added == [] and gone == [] and [(a["fallback"], b["fallback"]) for a, b in moved] == [(0, 1)]
