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


def test_cavity_pick_checks_open_door_and_withdrawal(monkeypatch):
    box=[0,0,0,1,1,1]
    pos=[0.5,0.5,0.5]
    rig=SimpleNamespace(held=None, ann=SimpleNamespace(art=lambda name: {"cavity_aabb":box,"open_q":1.0}),
                        joint=lambda name:1.0, obj_pose=lambda name:(np.array(pos),None))
    def pick(rig,name,max_candidates):
        rig.held={"name":name}
        pos[1]=-0.1
        return True
    monkeypatch.setattr(skills,"_pick_pinch",pick)
    monkeypatch.setattr(skills,"check_held",lambda *a:None)
    assert PickFromCavityPolicy(rig).execute("bowl")
    pos[1]=0.5
    rig.held=None
    rig.joint=lambda name:0.0
    with pytest.raises(SkillFailure,match="closed"):
        PickFromCavityPolicy(rig).execute("bowl")


def test_release_handle_requires_recorded_grasp_and_open_fingers():
    rig=SimpleNamespace(_handle_grasp=None, grip=lambda width,steps:np.array([width,width]),
                        kin=SimpleNamespace(coll_kw={"hand_touches_part": True}), log=lambda *a,**k:None)
    with pytest.raises(SkillFailure,match="no matching"):
        ReleaseArticulatedHandlePolicy(rig).execute("drawer")
    rig._handle_grasp={"name":"drawer","pre_open":0.04}
    assert np.min(ReleaseArticulatedHandlePolicy(rig).execute("drawer")) >=0.02
    assert rig._handle_grasp is None


def test_slide_to_edge_requires_free_hand_and_annotated_support():
    rig=SimpleNamespace(held={"name":"cup"})
    with pytest.raises(SkillFailure,match="empty"):
        SlideToEdgePolicy(rig).execute("book")
    rig=SimpleNamespace(held=None,ann=SimpleNamespace(objects={"book":{}}),
                        state=lambda:{},geo=SimpleNamespace(support_under=lambda name,st:None))
    # The caller must provide an object asset before the support check.
    rig.ann.asset_of=lambda obj:{"size":[0.2,0.1,0.02]}
    with pytest.raises(SkillFailure,match="annotated support"):
        SlideToEdgePolicy(rig).execute("book")


def test_floor_reach_rejects_non_floor_target():
    rig=SimpleNamespace(held=None,ann=SimpleNamespace(objects={"toy":{}}),state=lambda:{},
                        geo=SimpleNamespace(bottom=lambda name,st:np.array([0,0,0.3])))
    with pytest.raises(SkillFailure,match="not on the floor"):
        PrepareFloorReachPolicy(rig).execute("toy")
