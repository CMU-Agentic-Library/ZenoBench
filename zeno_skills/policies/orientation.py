"""Correct the orientation of an already grasped object."""

from __future__ import annotations

from .base import AtomicPolicy


class UprightObjectPolicy(AtomicPolicy):
    """Turn a held object's own up axis to world vertical: the upright skill (skill_jobs.held.upright_job,
    HAND_PLAN 9f) with the hand that holds it -- one free leg to a goal set, the old turn-in-air search and its
    set-down / hang fallbacks gone."""

    def execute(self, name, *, max_tilt_deg=15.0):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["upright"], {"name": name, "max_tilt_deg": float(max_tilt_deg)})
