"""Hand policies on a held (or about-to-be-held) object.

policy_073 DropIntoPolicy        release a held object above a container opening
policy_074 StackOnPolicy         set a held object on another object's top face
policy_075 RotateHeldPolicy      turn a held object about the vertical axis
policy_076 RegraspPolicy         set the object down on a support and grasp it again
policy_077 LeftSteadyPolicy      pinch a resting container with the left gripper
policy_078 FlipFlatPolicy        turn an edge-held flat object over and lay it back
policy_087 CoverWithLidPolicy    lay a held lid centred on a container rim
policy_093 SetHeldHeightPolicy   raise or lower a held object to a bottom height
policy_096 ReleaseInPlacePolicy  open one gripper where the object already rests
"""

from __future__ import annotations

import math
from contextlib import contextmanager

import numpy as np
from scipy.spatial.transform import Rotation

from .base import AtomicPolicy
from .. import skills
from ..annotations import rz
from ..clearance import FREE_ELSE_STRAIGHT, LEAVE_CONTACT, LEGACY
from ..physics import PHYSICS_HZ
from ..predicates import lid_on, tilt_deg
from ..rig import SkillFailure


def _require_held(rig, name, action):
    skills.right_hand_only(rig, name, action)
    if rig.held is None or rig.held["name"] != name:
        raise SkillFailure(f"{action} {name}: not right-held")
    skills.check_held(rig, f"{action}_start")


def _require_held_any(rig, name, action):
    """``name`` in either hand, checked (the skills on the motion layers that set it down: HAND_PLAN 9c)."""
    side = skills._hand_of(rig, name)
    if side is None:
        raise SkillFailure(f"{action} {name}: not held")
    skills.check_held(rig, f"{action}_start", side=side)


@contextmanager
def virtual_support(rig, name, z, box, category="object_top"):
    """Temporarily expose a horizontal face (an object's top, a rim plane) as
    an annotated support so the measured placement routine can target it."""
    s = {"name": name, "furniture": None, "category": category, "z": float(z),
         "aabb_xy": [float(v) for v in box], "clearance": 1.0}
    rig.ann.supports.append(s)
    try:
        yield s
    finally:
        rig.ann.supports.remove(s)


def object_top(rig, name, st=None):
    st = st or rig.state()
    b = np.asarray(rig.geo.bottom(name, st), float)
    size = rig.ann.asset_of(rig.ann.objects[name])["size"]
    return float(b[2] + size[2] * math.cos(math.radians(min(90.0, tilt_deg(st["objects"][name]["quat"])))))


class DropIntoPolicy(AtomicPolicy):
    """Let the held object go over a container's opening (skills.drop_into)."""

    def execute(self, name, container):
        _require_held_any(self.rig, name, "drop")
        return skills.drop_into(self.rig, name, container)


class StackOnPolicy(AtomicPolicy):
    """Place a held object centred on another object's top face."""

    def execute(self, name, base):
        rig = self.rig
        _require_held_any(rig, name, "stack")
        st = rig.state()
        top = object_top(rig, base, st)
        fp = rig.geo.footprint(base, st)
        c = rig.geo.bottom(base, st)
        with virtual_support(rig, f"top:{base}", top, fp) as s:
            skills.place(rig, name, s["name"], (float(c[0]), float(c[1])))
        from ..predicates import REGISTRY
        ok, why = REGISTRY["on_top_of"].evaluate(rig, None, object=name, base=base)
        rig.log("stack_result", obj=name, base=base, ok=bool(ok), detail=why)
        if not ok:
            raise SkillFailure(f"stack {name} on {base}: {why}")
        return True


class RotateHeldPolicy(AtomicPolicy):
    """Rotate the held object about the vertical: the rotate skill (skill_jobs.held.rotate_job, HAND_PLAN 9f) with
    the hand that holds it."""

    def execute(self, name, degrees):
        from ..motion_skills import SKILLS, run_skill
        _require_held_any(self.rig, name, "rotate")
        return run_skill(self.rig, SKILLS["rotate"], {"name": name, "degrees": float(degrees)})


class RegraspPolicy(AtomicPolicy):
    """Put the object down on a support and pick it again with a fresh grasp: the place (at the support point
    nearest the base, 12 cm in) and the pick, both on the motion layers (HAND_PLAN 9f; the old straight set-down
    where it hung is gone)."""

    def execute(self, name, support):
        rig = self.rig
        side = skills._hand_of(rig, name)
        if side is None:
            raise SkillFailure(f"regrasp {name}: not held")
        before = rig.held_by(side).get("kind")
        x0, y0, x1, y1 = rig.ann.support(support)["aabb_xy"]
        x, y, _ = rig.base_pose()
        skills.place_on(rig, name, support, hint=(min(max(x, x0 + 0.12), x1 - 0.12), min(max(y, y0 + 0.12), y1 - 0.12)))
        skills.pick(rig, name)
        side = skills._hand_of(rig, name)
        kind = None if side is None else rig.held_by(side).get("kind")
        rig.log("regrasp_result", obj=name, before=before, after=kind, hand=side)
        if side is None:
            raise SkillFailure(f"regrasp {name}: not held after the second grasp")
        return kind


class LeftSteadyPolicy(AtomicPolicy):
    """Pinch a resting container's rim (or an object's top or handle) with the left gripper so the right hand can work
    in it without the object sliding: the pick on the motion layers with the left hand, those pinches only, held where
    it stands -- no lift, no carry (pick_job hold, plan_pick stop="pick_held"; HAND_PLAN 9i)."""

    STEADY_KINDS = ("rim_pinch", "rim_pinch_rect", "top_pinch", "handle_pinch")

    def execute(self, name):
        from ..motion_skills import SKILLS, run_skill
        rig = self.rig
        if rig.held_by("left") is not None:
            raise SkillFailure("steady: the left hand is occupied")
        kind = run_skill(rig, SKILLS["pick"], {"name": name, "hand": "left", "kinds": self.STEADY_KINDS, "hold": True})
        held = rig.held_by("left")
        held["kind"] = "steady"
        rig.log("steady_result", obj=name, kind=kind, fingers=np.round(rig.left_fingers(), 4).tolist())
        return kind


class ReleaseInPlacePolicy(AtomicPolicy):
    """Open one gripper without moving the object first, then back the fingers off: the release skill
    (skill_jobs.held.release_job, skill_plans.plan_release; HAND_PLAN 9f)."""

    def execute(self, name, hand="right"):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["release"], {"name": name, "hand": hand})


class FlipFlatPolicy(AtomicPolicy):
    """Turn an edge-held flat object over by pivoting it about its far edge: the flip skill (skill_jobs.held.flip_job,
    skill_plans.plan_flip; HAND_PLAN 9h) with the hand that holds it."""

    def execute(self, name):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["flip"], {"name": name})


class CoverWithLidPolicy(AtomicPolicy):
    """Set a held lid centred on a container's rim plane."""

    def execute(self, lid, container):
        rig = self.rig
        _require_held_any(rig, lid, "cover")
        ca = rig.ann.asset_of(rig.ann.objects[container]).get("container")
        if not ca:
            raise SkillFailure(f"cover: {container} is not a container")
        st = rig.state()
        cb = np.asarray(rig.geo.bottom(container, st), float)
        rim = float(cb[2] + ca["rim_height"])
        fp = rig.geo.footprint(container, st)
        with virtual_support(rig, f"rim:{container}", rim, fp, category="rim"):
            skills.place(rig, lid, f"rim:{container}", (float(cb[0]), float(cb[1])))
        ok, why = lid_on(rig, container, lid, rig.state())
        rig.log("cover_result", lid=lid, container=container, ok=bool(ok), detail=why)
        if not ok:
            raise SkillFailure(f"cover {container} with {lid}: {why}")
        return True


class SetHeldHeightPolicy(AtomicPolicy):
    """Move the held object straight down (``down_only``), or up or down, until its bottom is at ``height_m``:
    the lower / lift skill (skill_jobs.held, HAND_PLAN 9e) with the hand that holds it."""

    def execute(self, name, height_m, *, down_only=False):
        from ..motion_skills import SKILLS, run_skill
        rig = self.rig
        _require_held_any(rig, name, "set height")
        up = not down_only and float(height_m) > float(rig.geo.bottom(name, rig.state())[2])
        return run_skill(rig, SKILLS["lift" if up else "lower"], {"name": name, "height": float(height_m)})
