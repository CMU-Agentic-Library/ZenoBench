"""The posture jobs (skill_jobs/posture.py, docs 9.3 step 5): the plan made where the robot stands, the grasp
checks after the leg, the result judged against where the joint was sent; nothing tried instead."""

from types import SimpleNamespace

import numpy as np
import pytest

from tests.test_posture_plan import Left, Right, _state
from zeno_skills.motion_state import Held
from zeno_skills.rig import SkillFailure
from zeno_skills.skill_jobs.posture import body_job, tuck_job

LO = np.r_[-0.54, 0.0, np.full(7, -3.0)]
HI = np.r_[0.0, 0.69, np.full(7, 3.0)]


def _rig(q=None, held=None, left_held=None, **kin):
    r, l = Right(**kin), Left()
    for k_, rest in ((r, np.r_[0.0, 0.0, np.full(7, -0.4)]), (l, np.r_[0.0, 0.0, np.full(7, -0.7)])):
        k_.lo, k_.hi, k_.rest = LO.copy(), HI.copy(), rest
    q = np.r_[0.0, 0.0, np.full(7, 0.3)] if q is None else np.asarray(q, float)
    logs = []
    return SimpleNamespace(kin=r, left_kin=l, held=held, left_held=left_held, q=lambda: q,
                           left_q=lambda: np.r_[q[:2], np.full(7, -0.7)], log=lambda *a, **k: logs.append((a, k)),
                           logs=logs)


def test_a_crouch_plans_the_torso_alone_and_judges_where_it_went():
    rig = _rig(q=np.r_[-0.53, 0.0, np.full(7, 0.3)])
    job = body_job(rig, {"joint": "torso_lift_joint", "target": -0.54}, _state())
    plan, build, hooks = job.ready(None)
    (leg,) = plan.segments
    assert leg.name == "torso_lift_joint" and leg.spec.joints == ("torso_lift_joint",)
    assert np.isclose(leg.q_end[0], -0.54) and "after" in hooks["torso_lift_joint"]
    assert job.done() == pytest.approx(-0.53)                 # within TORSO_AT
    assert rig.logs[-1][0] == ("posture_joint",)
    stalled = _rig(q=np.r_[-0.38, 0.0, np.full(7, 0.3)])      # 11-16: the yaw-180 stall's reading
    with pytest.raises(SkillFailure, match="actual -0.380, target -0.540"):
        body_job(stalled, {"joint": "torso_lift_joint", "target": -0.54}, _state()).done()


def test_a_target_out_of_the_limits_is_refused_before_anything_moves():
    with pytest.raises(ValueError, match="waist_pitch_joint target 0.900"):
        body_job(_rig(), {"joint": "waist_pitch_joint", "target": 0.9}, _state())


def test_a_posture_that_cannot_be_made_here_fails_the_skill():
    rig = _rig(seg_free=False, plan=(None, "GRAPH_FAIL"))
    with pytest.raises(SkillFailure, match="waist_pitch_joint: .*GRAPH_FAIL"):
        body_job(rig, {"joint": "waist_pitch_joint", "target": 0.3}, _state()).ready(None)


def test_a_tuck_of_a_loaded_hand_is_refused_and_a_left_tuck_opens_its_fingers_first():
    with pytest.raises(SkillFailure, match="holds cup"):
        tuck_job(_rig(held={"name": "cup"}), {"hand": "right"}, _state(right=Held("cup", np.eye(4))))
    rig = _rig()
    plan, _, hooks = tuck_job(rig, {"hand": "left"}, _state()).ready(None)
    assert [sg.name for sg in plan.segments] == ["left_fold_open", "left_fold"] and set(hooks) == {"left_fold"}
    assert tuck_job(rig, {"hand": "left"}, _state()).done() == pytest.approx(0.0)
