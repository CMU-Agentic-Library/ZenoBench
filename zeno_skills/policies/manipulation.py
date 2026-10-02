"""Object manipulation policies; each grasp route uses annotated contact geometry."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..rig import SkillFailure


def _require_grasp(rig, name, kind):
    if rig.held is not None:
        raise SkillFailure(f"pick {name}: already holding {rig.held['name']}")
    obj = rig.ann.objects.get(name)
    if obj is None:
        raise SkillFailure(f"pick {name}: object is not annotated")
    kinds = [g["type"] for g in rig.ann.asset_of(obj)["grasps"]]
    if kind not in kinds:
        raise SkillFailure(f"pick {name}: no {kind} grasp annotation")


class PickPolicy(AtomicPolicy):
    """Choose pinch or push-then-edge grasp from the concrete object's annotation."""

    def execute(self, name, *, max_candidates=12):
        return skills.pick(self.rig, name, max_candidates=max_candidates)


class TopPinchPickPolicy(AtomicPolicy):
    """Pinch an annotated top contact, e.g. a toy's body or a duck's offset top."""

    def execute(self, name, *, max_candidates=12):
        _require_grasp(self.rig, name, "top_pinch")
        return skills._pick_pinch(self.rig, name, max_candidates, kinds=("top_pinch",))


class RoundRimPickPolicy(AtomicPolicy):
    """Pinch a round vessel wall below its annotated rim, e.g. a cup or mug."""

    def execute(self, name, *, max_candidates=12):
        _require_grasp(self.rig, name, "rim_pinch")
        return skills._pick_pinch(self.rig, name, max_candidates, kinds=("rim_pinch",))


class RectRimPickPolicy(AtomicPolicy):
    """Pinch one annotated side of a rectangular tray or box rim."""

    def execute(self, name, *, max_candidates=12):
        _require_grasp(self.rig, name, "rim_pinch_rect")
        return skills._pick_pinch(self.rig, name, max_candidates, kinds=("rim_pinch_rect",))


class EdgePickPolicy(AtomicPolicy):
    """Push a flat object to a free support edge and pinch the overhang."""

    def execute(self, name):
        _require_grasp(self.rig, name, "edge_pinch_after_push")
        if self.rig.geo.support_under(name, self.rig.state()) is None:
            raise SkillFailure(f"edge pick {name}: not on an annotated support")
        return skills.pick_flat(self.rig, name)


class FloorCornerPickPolicy(AtomicPolicy):
    """Pinch the side and top corner of a flat object resting on the floor."""

    def execute(self, name):
        _require_grasp(self.rig, name, "edge_pinch_after_push")
        if float(self.rig.geo.bottom(name, self.rig.state())[2]) >= 0.05:
            raise SkillFailure(f"floor corner pick {name}: object is not on the floor")
        return skills._corner_pinch(self.rig, name)


class PlacePolicy(AtomicPolicy):
    """Dispatch placement by target and currently held grasp."""

    def execute(self, name, support, xy=None):
        return skills.place(self.rig, name, support, xy)

    def on(self, name, support, *, hint=None, tries=4):
        """Find a free spot on a named support and place there."""
        return skills.place_on(self.rig, name, support, hint=hint, tries=tries)


class SurfacePlacePolicy(AtomicPolicy):
    """Choose a free spot and place the held object on an annotated surface."""

    def execute(self, name, support, *, hint=None, tries=4):
        if support.startswith("in:"):
            raise ValueError("surface place needs a support name, not a container")
        return skills.place_on(self.rig, name, support, hint=hint, tries=tries)


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
        held = self.rig.held
        if held is None or held["name"] != name or held["kind"] != "edge":
            raise SkillFailure(f"edge place {name}: object is not edge-held")
        return skills.place_flat(self.rig, name, support, hint)


class MicrowavePlacePolicy(AtomicPolicy):
    """Insert a held item through the front of the microwave cavity."""

    def execute(self, name, support="kitchen_microwave/inside_floor"):
        if self.rig.ann.support(support).get("furniture") != "kitchen_microwave":
            raise SkillFailure(f"microwave place: {support} is not a microwave support")
        return skills.place_microwave(self.rig, name, support)


class MicrowaveCavityInsertPolicy(AtomicPolicy):
    """Move a held object through the microwave's front opening without releasing it."""

    def execute(self, name, support="kitchen_microwave/inside_floor"):
        if self.rig.ann.support(support).get("furniture") != "kitchen_microwave":
            raise SkillFailure(f"microwave insert: {support} is not a microwave support")
        return skills.insert_microwave_cavity(self.rig, name, support)


class MicrowaveCavityReleasePolicy(AtomicPolicy):
    """Open the fingers only after a measured cavity insertion."""

    def execute(self, name):
        return skills.release_microwave_cavity(self.rig, name)


class MicrowaveCavityWithdrawPolicy(AtomicPolicy):
    """Withdraw from a released object and check its final cavity support."""

    def execute(self, name):
        return skills.withdraw_microwave_cavity(self.rig, name)


class PushPolicy(AtomicPolicy):
    """Push or drag one object along its current annotated support."""

    def execute(self, name, support, direction, distance, *, label="PUSH", enough=None):
        return skills.push(self.rig, name, support, direction, distance, label=label, enough=enough)


def _contact_direction(rig, name, direction, distance):
    if rig.held is not None:
        raise SkillFailure("contact motion: release the held object first")
    if name not in rig.ann.objects:
        raise SkillFailure(f"contact motion: unknown object {name}")
    n = np.asarray(direction, dtype=float)
    if n.shape != (2,) or not np.all(np.isfinite(n)) or not np.isclose(np.linalg.norm(n), 1.0, atol=1e-3):
        raise ValueError("contact direction must be a horizontal unit vector")
    if not np.isfinite(distance) or distance <= 0:
        raise ValueError("contact distance must be positive")
    return n


class PushFromBehindPolicy(AtomicPolicy):
    """Use only the rear-contact push route; report measured displacement."""

    def execute(self, name, support, direction, distance, *, enough=None):
        n = _contact_direction(self.rig, name, direction, distance)
        return skills.push(self.rig, name, support, n, distance, label="PUSH_FROM_BEHIND",
                           enough=enough, mode="push")


class TopDragPolicy(AtomicPolicy):
    """Use only fingertip contact on top of an object; report displacement."""

    def execute(self, name, support, direction, distance, *, enough=None):
        n = _contact_direction(self.rig, name, direction, distance)
        return skills.push(self.rig, name, support, n, distance, label="TOP_DRAG",
                           enough=enough, mode="drag")
