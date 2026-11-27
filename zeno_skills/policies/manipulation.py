"""Object manipulation policies; each grasp route uses annotated contact geometry."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..rig import SkillFailure


def _require_grasp(rig, name, kind):
    left = getattr(rig, "left_held", None)
    if rig.held is not None and left is not None:              # a free hand picks (HAND_PLAN 9c)
        raise SkillFailure(f"pick {name}: both hands hold something ({rig.held['name']}, {left['name']})")
    if name in {h["name"] for h in (rig.held, left) if h is not None}:
        raise SkillFailure(f"pick {name}: already holding it")
    obj = rig.ann.objects.get(name)
    if obj is None:
        raise SkillFailure(f"pick {name}: object is not annotated")
    kinds = [g["type"] for g in rig.ann.asset_of(obj)["grasps"]]
    if kind not in kinds:
        raise SkillFailure(f"pick {name}: no {kind} grasp annotation")


class PickPolicy(AtomicPolicy):
    """Choose pinch or push-then-edge grasp from the concrete object's annotation."""

    def execute(self, name, *, max_candidates=12, grasp=None, hand=None):
        return skills.pick(self.rig, name, max_candidates=max_candidates, grasp=grasp, hand=hand)


class TopPinchPickPolicy(AtomicPolicy):
    """Pinch an annotated top contact, e.g. a toy's body or a duck's offset top."""

    def execute(self, name, *, max_candidates=12, hand=None):
        _require_grasp(self.rig, name, "top_pinch")
        return skills._pick_pinch(self.rig, name, max_candidates, kinds=("top_pinch",), hand=hand)


class RoundRimPickPolicy(AtomicPolicy):
    """Pinch a round vessel wall below its annotated rim, e.g. a cup or mug."""

    def execute(self, name, *, max_candidates=12, hand=None):
        _require_grasp(self.rig, name, "rim_pinch")
        return skills._pick_pinch(self.rig, name, max_candidates, kinds=("rim_pinch",), hand=hand)


class RectRimPickPolicy(AtomicPolicy):
    """Pinch one annotated side of a rectangular tray or box rim."""

    def execute(self, name, *, max_candidates=12, hand=None):
        _require_grasp(self.rig, name, "rim_pinch_rect")
        return skills._pick_pinch(self.rig, name, max_candidates, kinds=("rim_pinch_rect",), hand=hand)


class EdgePickPolicy(AtomicPolicy):
    """Pinch a flat object across its thickness at a side that overhangs its support (the
    pinch flow, thickness_pinch candidates; sliding it to the edge is expose / slide_to_edge)."""

    def execute(self, name, *, max_candidates=12, hand=None):
        _require_grasp(self.rig, name, "thickness_pinch")
        if self.rig.geo.support_under(name, self.rig.state()) is None:
            raise SkillFailure(f"edge pick {name}: not on an annotated support")
        return skills._pick_pinch(self.rig, name, max_candidates, kinds=("thickness_pinch",), hand=hand)


class PlacePolicy(AtomicPolicy):
    """Dispatch placement by target and currently held grasp."""

    def execute(self, name, support, xy=None):
        return skills.place(self.rig, name, support, xy)

    def on(self, name, support, *, hint=None, tries=4):
        """Find a free spot on a named support and place there."""
        return skills.place_on(self.rig, name, support, hint=hint, tries=tries)


class SurfacePlacePolicy(AtomicPolicy):
    """Choose a free spot and place the held object on an annotated surface."""

    def execute(self, name, support, *, hint=None, tries=4, square=False):
        """``square``: set it down with its edges along the support's axes -- the turn that squares it, as the
        hold has it now, is in the place's goal set (skill_jobs.place; HAND_PLAN 9f), not a rotate before."""
        if support.startswith("in:"):
            raise ValueError("surface place needs a support name, not a container")
        rig = self.rig
        if skills._hand_of(rig, name) is None:
            # already set down by the previous policy (upright stands the
            # object back itself): verify instead of placing again
            on, why = rig.geo.on(name, support, rig.state())
            if on:
                rig.log("place_already_on", obj=name, support=support)
                return True
            raise SkillFailure(f"place {name}: not held and not on {support} ({why})")
        return skills.place_on(rig, name, support, hint=hint, tries=tries, square=square)


class ContainerPlacePolicy(AtomicPolicy):
    """Place the held object inside an annotated container."""

    def execute(self, name, container):
        if container.startswith("in:"):
            container = container[3:]
        if container not in self.rig.ann.objects:
            raise SkillFailure(f"container place: {container} is not an annotated object")
        if not self.rig.ann.asset_of(self.rig.ann.objects[container]).get("container"):
            raise SkillFailure(f"container place: {container} is not a container")
        return skills.place(self.rig, name, "in:" + container)


class EdgePlacePolicy(AtomicPolicy):
    """Slide an edge-held flat object onto a support and verify it settled."""

    def execute(self, name, support, *, hint=None):
        side = skills._hand_of(self.rig, name)
        held = None if side is None else self.rig.held if side == "right" else self.rig.left_held
        if held is None or held["kind"] != "edge":
            raise SkillFailure(f"edge place {name}: object is not edge-held")
        return skills.place(self.rig, name, support, hint)


class _RetiredCavity(AtomicPolicy):
    """The old microwave set-down (hand-written parks and front point, insert / release / withdraw as calls of
    their own): the microwave's floor is a support behind a door like a cabinet's shelf now, set down by place's
    one path (policy_015, skill_plans.plan_place; docs 9.3 step 8c) -- retired (skill_library/check.py), the id
    kept."""

    def execute(self, *args, **kwargs):
        raise SkillFailure(f"{type(self).__name__} is retired: place into the microwave with place (policy_015)")


class MicrowavePlacePolicy(_RetiredCavity):
    """Retired (policy_021)."""


class MicrowaveCavityInsertPolicy(_RetiredCavity):
    """Retired (policy_018)."""


class MicrowaveCavityReleasePolicy(_RetiredCavity):
    """Retired (policy_019)."""


class MicrowaveCavityWithdrawPolicy(_RetiredCavity):
    """Retired (policy_020)."""


class PushPolicy(AtomicPolicy):
    """Push or drag one object along its current annotated support."""

    def execute(self, name, support, direction, distance, *, label="PUSH", enough=None):
        if len(skills.loaded_hands(self.rig)) == 2:            # push_object pushes with an empty hand, either
            raise SkillFailure("push: both hands hold something")
        surface = self.rig.ann.support(support) if isinstance(support, str) else support
        actual = self.rig.geo.support_under(name, self.rig.state())
        if surface is None or actual is None:
            # the support binding is None when the object rests on nothing annotated
            raise SkillFailure(f"push {name}: object is not on an annotated support")
        if actual["name"] != surface["name"]:
            raise SkillFailure(f"push {name}: object is not on {surface['name']}")
        n = np.asarray(direction, dtype=float)
        if n.shape != (2,) or not np.isfinite(n).all() or not np.isclose(np.linalg.norm(n), 1.0, atol=1e-3):
            raise ValueError("push direction must be a horizontal unit vector")
        if not np.isfinite(distance) or distance <= 0:
            raise ValueError("push distance must be positive")
        from ..skill_jobs.slide import push_object
        return push_object(self.rig, name, surface, [(n, float(distance), enough)], label=label)[1]


def _contact_direction(rig, name, support, direction, distance):
    if len(skills.loaded_hands(rig)) == 2:                      # push_object pushes with an empty hand, either
        raise SkillFailure("contact motion: both hands hold something")
    if name not in rig.ann.objects:
        raise SkillFailure(f"contact motion: unknown object {name}")
    surface = rig.ann.support(support) if isinstance(support, str) else support
    actual = rig.geo.support_under(name, rig.state())
    if surface is None or actual is None:
        raise SkillFailure(f"contact motion {name}: object is not on an annotated support")
    if actual["name"] != surface["name"]:
        raise SkillFailure(f"contact motion {name}: object is not on {surface['name']}")
    n = np.asarray(direction, dtype=float)
    if n.shape != (2,) or not np.all(np.isfinite(n)) or not np.isclose(np.linalg.norm(n), 1.0, atol=1e-3):
        raise ValueError("contact direction must be a horizontal unit vector")
    if not np.isfinite(distance) or distance <= 0:
        raise ValueError("contact distance must be positive")
    return surface, n


class PushFromBehindPolicy(AtomicPolicy):
    """Use only the rear-contact push route; report measured displacement."""

    def execute(self, name, support, direction, distance, *, enough=None):
        surface, n = _contact_direction(self.rig, name, support, direction, distance)
        from ..skill_jobs.slide import push_object
        return push_object(self.rig, name, surface, [(n, distance, enough)], label="PUSH_FROM_BEHIND",
                           modes=("push",))[1]


class TopDragPolicy(AtomicPolicy):
    """Use only fingertip contact on top of an object; report displacement."""

    def execute(self, name, support, direction, distance, *, enough=None):
        surface, n = _contact_direction(self.rig, name, support, direction, distance)
        # The paired push Contract accepts at least half the requested motion.
        # Stop after that measured progress: extra contact legs can slip an
        # already moved object while re-parking the base.
        minimum = enough if enough is not None else max(0.01, float(distance) * 0.5)
        from ..skill_jobs.slide import push_object
        return push_object(self.rig, name, surface, [(n, distance, minimum)], label="TOP_DRAG",
                           modes=("drag",))[1]
