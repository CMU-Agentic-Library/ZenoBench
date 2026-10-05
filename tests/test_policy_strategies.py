"""Policy routing checks where an incorrect branch changes physical contact."""

from types import SimpleNamespace

import pytest

from zeno_skills import skills
from zeno_skills.policies import (CarryNavigatePolicy, OpenPolicy,
                                  RoundRimPickPolicy, TopPinchPickPolicy)
from zeno_skills.rig import SkillFailure


def test_cup_and_toy_select_different_grasp_contacts(monkeypatch):
    assets = {
        "cup": {"grasps": [{"type": "rim_pinch"}]},
        "toy": {"grasps": [{"type": "top_pinch"}]},
    }
    ann = SimpleNamespace(objects={k: {"asset": k} for k in assets},
                          asset_of=lambda obj: assets[obj["asset"]])
    rig = SimpleNamespace(ann=ann, held=None)
    calls = []
    monkeypatch.setattr(skills, "_pick_pinch", lambda rig, name, n, *, kinds: calls.append((name, kinds)))

    RoundRimPickPolicy(rig).execute("cup")
    TopPinchPickPolicy(rig).execute("toy")
    assert calls == [("cup", ("rim_pinch",)), ("toy", ("top_pinch",))]
    with pytest.raises(SkillFailure, match="no rim_pinch"):
        RoundRimPickPolicy(rig).execute("toy")


def test_open_routes_button_microwave_and_handle_door(monkeypatch):
    arts = {
        "oven": {"category": "microwave", "door_button": {}, "open_q": -1.4},
        "drawer": {"category": "drawer", "handle": {}, "open_q": 0.3},
    }
    # A real handle is a nonempty annotation; the button branch needs none.
    arts["drawer"]["handle"] = {"center": [0, 0, 0]}
    rig = SimpleNamespace(ann=SimpleNamespace(art=lambda name: arts[name]))
    calls = []
    monkeypatch.setattr(skills, "open_microwave_door", lambda rig, name: calls.append(("powered", name)))
    monkeypatch.setattr(skills, "open_articulated", lambda rig, name, *, goal=None:
                        calls.append(("handle", name, goal)))

    OpenPolicy(rig).execute("oven")
    OpenPolicy(rig).execute("drawer", goal=0.2)
    assert calls == [("powered", "oven"), ("handle", "drawer", 0.2)]


def test_carry_navigation_requires_the_correct_held_object(monkeypatch):
    rig = SimpleNamespace(held=None)
    policy = CarryNavigatePolicy(rig)
    with pytest.raises(SkillFailure, match="not holding"):
        policy.execute((1, 2, 0), name="book")
    rig.held = {"name": "cup"}
    with pytest.raises(SkillFailure, match="not holding book"):
        policy.execute((1, 2, 0), name="book")
    calls = []
    monkeypatch.setattr(skills, "navigate", lambda rig, pose, **kw: calls.append((pose, kw["label"])))
    monkeypatch.setattr(skills, "check_held", lambda rig, label: calls.append(label))
    policy.execute((1, 2, 0), name="cup")
    assert calls == [((1, 2, 0), "carry_navigate"), "carry_navigate_result"]
