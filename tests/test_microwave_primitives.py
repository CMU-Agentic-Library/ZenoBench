"""Microwave stage guards must prevent pressing or moving a hinge out of order."""

from types import SimpleNamespace

import numpy as np
import pytest

from zeno_skills import skills
from zeno_skills.policies import MicrowaveHingeDrivePolicy
from zeno_skills.rig import SkillFailure


def test_the_door_moves_only_by_its_key_the_clearance_and_hinge_policies_are_retired():
    # 9.3 step 8b: the door key's press parks clear of the swing and drives the door (plan_press press_door)
    from zeno_skills.policies import MicrowaveDoorClearPolicy
    with pytest.raises(SkillFailure, match="retired"):
        MicrowaveHingeDrivePolicy(object()).execute("oven", target="close")
    with pytest.raises(SkillFailure, match="retired"):
        MicrowaveDoorClearPolicy(object()).execute("oven")


def test_the_microwave_set_down_stages_are_retired():
    # 9.3 step 8c: the microwave's floor is a support behind a door, set down by place's one path
    from zeno_skills.policies import MicrowaveCavityReleasePolicy, MicrowavePlacePolicy
    for P in (MicrowaveCavityReleasePolicy, MicrowavePlacePolicy):
        with pytest.raises(SkillFailure, match="retired"):
            P(object()).execute("oatmeal")
