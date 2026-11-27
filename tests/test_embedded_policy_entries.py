"""New atomic entries preserve physical guards and measured postconditions."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills.policies import (GraspArticulatedHandlePolicy, OpenPrismaticDrawerPolicy,
                                  OpenRevoluteDoorPolicy, PickFromCavityPolicy,
                                  PrepareFloorReachPolicy, ReleaseArticulatedHandlePolicy,
                                  SlideToEdgePolicy)
from zeno_skills.rig import SkillFailure
from zeno_skills import skills


def test_typed_open_rejects_wrong_joint_type(monkeypatch):
    calls = []
    rig = SimpleNamespace(ann=SimpleNamespace(art=lambda name: {"type": "revolute", "handle": {"center": [0, 0, 0]}}))
    monkeypatch.setattr(skills, "open_articulated", lambda rig, name: calls.append(name) or 1.0)
    assert OpenRevoluteDoorPolicy(rig).execute("cabinet") == 1.0
    assert calls == ["cabinet"]
    with pytest.raises(SkillFailure, match="manual drawer"):
        OpenPrismaticDrawerPolicy(rig).execute("cabinet")


def test_the_cavity_pick_is_retired_pick_takes_the_microwave_like_a_cabinet():
    with pytest.raises(SkillFailure, match="retired"):
        PickFromCavityPolicy(object()).execute("bowl")


def test_slide_to_edge_requires_free_hand_and_annotated_support():
    # push_object pushes with either empty hand: refused only when both hold something
    rig=SimpleNamespace(held={"name":"cup"},left_held={"name":"mug"})
    with pytest.raises(SkillFailure,match="both hands"):
        SlideToEdgePolicy(rig).execute("book")
    rig=SimpleNamespace(held=None,ann=SimpleNamespace(objects={"book":{}}),
                        state=lambda:{},geo=SimpleNamespace(support_under=lambda name,st:None))
    # The caller must provide an object asset before the support check.
    rig.ann.asset_of=lambda obj:{"size":[0.2,0.1,0.02]}
    with pytest.raises(SkillFailure,match="annotated support"):
        SlideToEdgePolicy(rig).execute("book")


def test_the_retired_handle_and_floor_reach_entries_say_so():
    for cls in (ReleaseArticulatedHandlePolicy, PrepareFloorReachPolicy):
        with pytest.raises(SkillFailure, match="retired"):
            cls(object()).execute("drawer")

