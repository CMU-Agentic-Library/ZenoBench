"""Tool-use policies with a held object.

policy_084 WipeSurfacePolicy   press a held sponge on a support and sweep a strip; measure contact coverage
policy_085 StirContainerPolicy dip a held spoon into a container and circle it (the motion-layer "stir")
policy_086 PourIntoPolicy      tilt a held cup over a container so its loose contents fall in

Each policy writes its measured result into rig.memory (wiped / stirred) or
leaves it in the scene (poured items), so the Contract's GT predicates verify it.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from .base import AtomicPolicy
from .. import skills
from ..skill_jobs.carry import carry_posture
from ..clearance import FREE_ELSE_STRAIGHT, LEGACY, into_contact
from ..evaluator import quat_R
from ..planner import find_park, find_park_set
from ..predicates import memory, objects_inside
from ..rig import FINGERS_KW, Dropped, SkillFailure


def _park_diag():
    from ..planner import LAST_PARK_DIAG
    return {k: v for k, v in LAST_PARK_DIAG.items() if v}


class WipeSurfacePolicy(AtomicPolicy):
    """Wipe a free 30 cm strip along an edge of a support with a held sponge: the wipe skill (skill_jobs.wipe.wipe_job,
    skill_plans.plan_wipe; HAND_PLAN 9g) with the hand that holds it -- the sponge pressed WIPE_PRESS into the
    surface and stroked there and back by the arm (the old policy held the arm and drove the base).  ``passes``:
    kept for the call's signature; a wipe is one stroke and its return."""

    def execute(self, tool, support, *, length=0.30, passes=2):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["wipe"], {"tool": tool, "support": support, "length": float(length)})


class StirContainerPolicy(AtomicPolicy):
    """Dip a held spoon into the container and turn its tip round inside it: the catalog's "stir" on the
    motion layers (skill_jobs.stir.stir_job, skill_plans.plan_stir; docs/skills/stir.md).  ``turns`` 0
    is a dip (DipUtensilPolicy): the tip in and out, no circle."""

    def execute(self, tool, container, *, turns=1.25):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["stir"], {"tool": tool, "container": container, "turns": turns})


class PourIntoPolicy(AtomicPolicy):
    """Tilt a held cup over a container until its contents fall in: the pour skill (skill_jobs.pour.pour_job,
    skill_plans.plan_pour; HAND_PLAN 9h) with the hand that holds it."""

    def execute(self, source, target):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["pour"], {"source": source, "target": target})

