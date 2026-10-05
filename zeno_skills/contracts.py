"""Semantic contract metadata and real atomic-policy route bindings.

``bind`` only constructs a policy. ``ContractRunner`` in contract_runtime.py
adds measured shared pre/postconditions and a trace for requested routes.
Route-specific execute arguments remain explicit; this registry does not
choose a route or plan a skill graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .policies import (
    AtomicPolicy, CarryNavigatePolicy, ClickPolicy, ClosePolicy, ContainerPlacePolicy,
    EdgePickPolicy, EdgePlacePolicy, EmptyHandNavigatePolicy, FloorCornerPickPolicy,
    HandleClosePolicy, HandleOpenPolicy, LeanForwardPolicy, LowerTorsoPolicy,
    MicrowavePlacePolicy, MicrowaveStartPolicy, NavigatePolicy, OpenPolicy,
    PickPolicy, PoweredDoorClosePolicy, PoweredDoorOpenPolicy, PushFromBehindPolicy,
    PushPolicy, RaiseTorsoPolicy, RectRimPickPolicy, RoundRimPickPolicy,
    SetTorsoHeightPolicy, SetWaistPitchPolicy, StraightenWaistPolicy,
    SurfacePlacePolicy, TopDragPolicy, TopPinchPickPolicy, TuckArmPolicy,
    PlacePolicy, BimanualCarryPolicy, PickCupHandlePolicy, PickFromCavityPolicy,
    PickWhileMovingPolicy, PlaceWhileMovingPolicy, OpenRevoluteDoorPolicy,
    OpenPrismaticDrawerPolicy, OpenDoorWhileLeftHoldsPolicy, PolicySuite,
)


@dataclass(frozen=True)
class ContractSpec:
    """Eight-field semantic interface; executor routes reference real policy classes."""

    id: str
    description: str
    inputs: tuple[str, ...]
    requires: tuple[str, ...]
    achieves: tuple[str, ...]
    outcomes: Mapping[str, str]
    executor: Mapping[str, type[AtomicPolicy]]
    verifier: str

    def bind(self, rig, route: str = "auto") -> AtomicPolicy:
        """Select an existing atomic policy for this contract and one live rig."""
        try:
            policy_type = self.executor[route]
        except KeyError as exc:
            raise ValueError(f"{self.id}: unknown policy route {route!r}") from exc
        return policy_type(rig)


def _spec(id, description, inputs, requires, achieves, outcomes, executor, verifier):
    return ContractSpec(
        id=id,
        description=description,
        inputs=tuple(inputs),
        requires=tuple(requires),
        achieves=tuple(achieves),
        outcomes=MappingProxyType(dict(outcomes)),
        executor=MappingProxyType(dict(executor)),
        verifier=verifier,
    )


CONTRACTS: Mapping[str, ContractSpec] = MappingProxyType({
    "navigate.v1": _spec(
        "navigate.v1", "Move the base to a target pose, preserving any grasp.",
        ("pose", "carried_object?", "min_bottom_z_m?"),
        ("target navigable", "held state matches carried_object"),
        ("base_at(pose)", "held(carried_object) if supplied"),
        {"success": "arrived", "failure": "may stop partway or drop object"},
        {"auto": NavigatePolicy, "empty": EmptyHandNavigatePolicy, "carry": CarryNavigatePolicy,
         "two_hand_carry": BimanualCarryPolicy},
        "base_pose tolerance; check_held or two-hand hold when carrying",
    ),
    "pick.v1": _spec(
        "pick.v1", "Grasp and lift one annotated object with the right hand.",
        ("object", "grasp_route?", "base_path?", "cavity?"),
        ("right hand empty", "object annotated and reachable"),
        ("held(object)", "object lifted"),
        {"success": "object held", "failure": "object may have moved during attempt"},
        {"auto": PickPolicy, "top": TopPinchPickPolicy, "round_rim": RoundRimPickPolicy,
         "rect_rim": RectRimPickPolicy, "edge": EdgePickPolicy, "floor_corner": FloorCornerPickPolicy,
         "cup_handle": PickCupHandlePolicy, "cavity": PickFromCavityPolicy,
         "moving": PickWhileMovingPolicy},
        "held object identity, lift and stable grasp",
    ),
    "place.v1": _spec(
        "place.v1", "Release a held object onto a support or into a container.",
        ("object", "target", "hint_xy_m?", "base_path?"),
        ("object held", "target annotated and accessible"),
        ("on(object, target) or inside(object, target)", "hand empty"),
        {"success": "object at target", "failure": "object may be released elsewhere"},
        {"auto": PlacePolicy, "surface": SurfacePlacePolicy, "container": ContainerPlacePolicy,
         "edge": EdgePlacePolicy, "microwave": MicrowavePlacePolicy,
         "moving": PlaceWhileMovingPolicy},
        "Geometry.on or Geometry.inside; hand empty",
    ),
    "open.v1": _spec(
        "open.v1", "Open one annotated door or drawer.",
        ("articulated", "required_access_to?", "left_held_object?"),
        ("joint annotated", "handle or powered route reachable"),
        ("joint_open_enough(articulated)", "accessible(object) when requested"),
        {"success": "opening sufficient", "failure": "joint may be partly open"},
        {"auto": OpenPolicy, "handle": HandleOpenPolicy, "powered": PoweredDoorOpenPolicy,
         "revolute": OpenRevoluteDoorPolicy, "prismatic": OpenPrismaticDrawerPolicy,
         "while_left_holds": OpenDoorWhileLeftHoldsPolicy},
        "measured joint opening; target access when requested",
    ),
    "close.v1": _spec(
        "close.v1", "Close one annotated door or drawer.",
        ("articulated",),
        ("joint annotated", "closure path clear"),
        ("closed(articulated)",),
        {"success": "joint closed", "failure": "joint may be partly closed"},
        {"auto": ClosePolicy, "handle": HandleClosePolicy, "powered": PoweredDoorClosePolicy},
        "measured joint against closed_q",
    ),
    "push.v1": _spec(
        "push.v1", "Move an object along its support by contact.",
        ("object", "support", "direction_xy", "distance_m", "min_progress_m"),
        ("right hand empty", "object on annotated support"),
        ("displacement_along(object, direction_xy) >= min_progress_m",),
        {"success": "measured progress", "failure": "object may have moved or fallen"},
        {"auto": PushPolicy, "behind": PushFromBehindPolicy, "top_drag": TopDragPolicy},
        "compare pre/post object positions along direction",
    ),
    "click.v1": _spec(
        "click.v1", "Press one annotated appliance button.",
        ("appliance", "button"),
        ("hand empty", "button reachable", "start requires food, closed door, thermal model"),
        ("button_pressed_this_call", "heating_active if start"),
        {"success": "button action confirmed", "failure": "press or retreat may be partial"},
        {"auto": ClickPolicy, "start": MicrowaveStartPolicy},
        "fresh button event and thermal.active for start",
    ),
    "set_posture.v1": _spec(
        "set_posture.v1", "Set measured right-arm, torso or waist posture.",
        ("component", "target?"),
        ("hand empty", "target in joint limits", "collision-free route"),
        ("arm_tucked() if tuck", "joint_at(component, target) otherwise"),
        {"success": "joint settled", "failure": "arm may stop at intermediate posture"},
        {"tuck": TuckArmPolicy, "torso": SetTorsoHeightPolicy,
         "lower": LowerTorsoPolicy, "raise": RaiseTorsoPolicy,
         "waist": SetWaistPitchPolicy, "lean": LeanForwardPolicy,
         "straighten": StraightenWaistPolicy},
        "read measured q against selected joint target",
    ),
})


# Supporting actions appear in the contract-policy diagram but are not
# ContractSpec.executor routes. They may be stages, preparation, or recovery
# steps; referencing one here does not claim that a contract runner invokes it.
CONTRACT_SUPPORT_POLICY_IDS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "navigate.v1": (
        "carry_height_adjust", "back_off_with_load", "base_rotate_in_place",
        "base_translate_local", "reach_while_moving", "tuck_arm",
    ),
    "pick.v1": (
        "prepare_floor_reach", "slide_to_edge", "right_tcp_move",
        "right_joint_move", "right_gripper_open", "right_gripper_close",
        "reach_while_moving", "bimanual_flat_pick", "bimanual_box_lift",
        "handover_right_to_left",
    ),
    "place.v1": (
        "microwave_cavity_insert", "microwave_cavity_release",
        "microwave_cavity_withdraw", "upright_object", "right_tcp_move",
        "right_joint_move", "right_gripper_open", "right_gripper_close",
    ),
    "open.v1": (
        "grasp_articulated_handle", "release_articulated_handle",
        "microwave_button_approach", "microwave_button_press",
        "microwave_button_retract", "microwave_door_clear",
        "microwave_hinge_drive", "right_tcp_move", "right_joint_move",
        "right_gripper_open", "right_gripper_close",
    ),
    "close.v1": (
        "grasp_articulated_handle", "release_articulated_handle",
        "microwave_door_clear", "microwave_hinge_drive", "right_tcp_move",
        "right_joint_move", "right_gripper_open", "right_gripper_close",
    ),
    "push.v1": ("slide_to_edge", "right_tcp_move", "right_joint_move"),
    "click.v1": (
        "microwave_button_approach", "microwave_button_press",
        "microwave_button_retract", "right_tcp_move", "right_joint_move",
    ),
    "set_posture.v1": (
        "prepare_floor_reach", "right_tcp_move", "right_joint_move",
    ),
})


def policy_contract_relations(catalog: list[dict]) -> Mapping[str, Mapping[str, tuple[str, ...]]]:
    """Return real executor bindings and explicitly labeled support references.

    The catalog determines which class maps to a policy ID. Exact class identity
    avoids silently treating a subclass as an additional executor binding.
    """
    ids = {row["id"] for row in catalog}
    suite = PolicySuite(None)
    class_to_id = {type(getattr(suite, row["executor"])): row["id"]
                   for row in catalog if row.get("executor")}
    relations = {}
    for contract_id, spec in CONTRACTS.items():
        direct = tuple(dict.fromkeys(class_to_id[cls] for cls in spec.executor.values()
                                     if cls in class_to_id))
        support = CONTRACT_SUPPORT_POLICY_IDS[contract_id]
        if not set(support) <= ids:
            raise ValueError(f"{contract_id}: support policy missing from catalog")
        if set(direct) & set(support):
            raise ValueError(f"{contract_id}: policy marked direct and support")
        relations[contract_id] = MappingProxyType({"direct": direct, "support": support})
    covered = {policy_id for groups in relations.values()
               for names in groups.values() for policy_id in names}
    if covered != ids:
        raise ValueError(f"contract mapping does not cover catalog: {sorted(ids-covered)}")
    return MappingProxyType(relations)


__all__ = ["ContractSpec", "CONTRACTS", "CONTRACT_SUPPORT_POLICY_IDS",
           "policy_contract_relations"]
