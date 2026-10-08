"""Bound class API for Zeno House atomic GT policies.

Use ``policies = PolicySuite(rig)`` after runtime.make_rig. All policies
operate on the same live rig and preserve the legacy functions in skills.py.
"""

from __future__ import annotations

from .appliance import (ClickPolicy, MicrowaveButtonApproachPolicy, MicrowaveButtonPressPolicy,
                        MicrowaveButtonRetractPolicy, MicrowaveDoorClearPolicy, MicrowaveDoorCycle,
                        MicrowaveHingeDrivePolicy, MicrowaveStartPolicy)
from .articulation import (ClosePolicy, HandleClosePolicy, HandleOpenPolicy,
                           OpenPolicy, PoweredDoorClosePolicy, PoweredDoorOpenPolicy)
from .base import AtomicPolicy
from ..interface_ids import POLICY_PUBLIC_IDS
from .bimanual import (BimanualBoxLiftPolicy, BimanualCarryPolicy, BimanualFlatPickPolicy,
                       HandoverRightToLeftPolicy, OpenDoorWhileLeftHoldsPolicy)
from .embedded import (GraspArticulatedHandlePolicy, OpenPrismaticDrawerPolicy,
                       OpenRevoluteDoorPolicy, PickFromCavityPolicy, PrepareFloorReachPolicy,
                       ReleaseArticulatedHandlePolicy, SlideToEdgePolicy)
from .handle_grasp import PickCupHandlePolicy
from .manipulation import (ContainerPlacePolicy, EdgePickPolicy, EdgePlacePolicy,
                           FloorCornerPickPolicy, MicrowaveCavityInsertPolicy,
                           MicrowaveCavityReleasePolicy, MicrowaveCavityWithdrawPolicy,
                           MicrowavePlacePolicy, PickPolicy,
                           PlacePolicy, PushPolicy, PushFromBehindPolicy, TopDragPolicy, RectRimPickPolicy,
                           RoundRimPickPolicy, SurfacePlacePolicy, TopPinchPickPolicy)
from .mobile import PickWhileMovingPolicy, PlaceWhileMovingPolicy, ReachWhileMovingPolicy
from .navigation import (BackOffWithLoadPolicy, BaseRotateInPlacePolicy, BaseTranslateLocalPolicy,
                         CarryHeightAdjustPolicy, CarryNavigatePolicy,
                         EmptyHandNavigatePolicy, NavigatePolicy, PickAndCarryPolicy)
from .primitives import (RightGripperClosePolicy, RightGripperOpenPolicy, RightJointMovePolicy,
                         RightTcpMovePolicy)
from .orientation import UprightObjectPolicy
from .thermal_wait import WaitForTemperaturePolicy
from .extra import (ShakeHeldPolicy, WaitPolicy, WaveHandPolicy, NodHeadPolicy, KnockPanelPolicy, TouchObjectPolicy, PlanSquareYawPolicy, SweepTogetherPolicy, IdentifyObjectPolicy, MeasureObjectPolicy, CountCategoryPolicy, DipUtensilPolicy, SidestepPolicy, HoverOverPolicy)
from .plan_helpers import (PlanHeadingPolicy, PlanHomePolicy, PlanPointPolicy, PlanReachPolicy,
                           PlanRetreatPolicy, PlanStandoffPolicy)
from .base_motion import ApproachTargetPolicy
from .base_motion import FaceTargetPolicy
from .base_motion import RetreatFromPolicy
from .perceive import LookAtPolicy
from .perceive import ExploreRoomPolicy
from .perceive import SearchObjectPolicy
from .perceive import PointAtPolicy
from .perceive import PresentHeldPolicy
from .hand import DropIntoPolicy
from .hand import StackOnPolicy
from .hand import RotateHeldPolicy
from .hand import RegraspPolicy
from .hand import LeftSteadyPolicy
from .hand import FlipFlatPolicy
from .contact import PullTowardBasePolicy
from .contact import SeparateFromNeighbourPolicy
from .contact import RollCylinderPolicy
from .contact import TipOverPolicy
from .contact import CenterOnSupportPolicy
from .tooluse import WipeSurfacePolicy
from .tooluse import StirContainerPolicy
from .tooluse import PourIntoPolicy
from .hand import CoverWithLidPolicy
from .perceive import InspectReceptaclePolicy
from .appliance_generic import WaitCoolPolicy
from .appliance_generic import WaitHeatPolicy
from .base_motion import LeftArmFoldPolicy
from .base_motion import NavigateToPlacePolicy
from .hand import SetHeldHeightPolicy
from .appliance_generic import PressButtonPolicy
from .hand import ReleaseInPlacePolicy
from .posture import (LeanForwardPolicy, LowerTorsoPolicy, RaiseTorsoPolicy, SetTorsoHeightPolicy,
                      SetWaistPitchPolicy, StraightenWaistPolicy, TuckArmPolicy)


class PolicySuite:
    """One bound instance of each reusable policy family for a simulator rig."""

    def __init__(self, rig):
        # General dispatchers preserve the existing task and manual-plan API.
        self.navigate = NavigatePolicy(rig)
        self.open = OpenPolicy(rig)
        self.close = ClosePolicy(rig)
        self.pick = PickPolicy(rig)
        self.place = PlacePolicy(rig)
        self.push = PushPolicy(rig)
        self.microwave_start = MicrowaveStartPolicy(rig)
        self.click = ClickPolicy(rig)
        self.microwave_button_approach = MicrowaveButtonApproachPolicy(rig)
        self.microwave_button_press = MicrowaveButtonPressPolicy(rig)
        self.microwave_button_retract = MicrowaveButtonRetractPolicy(rig)
        self.microwave_door_clear = MicrowaveDoorClearPolicy(rig)
        self.microwave_hinge_drive = MicrowaveHingeDrivePolicy(rig)
        self.microwave_cavity_insert = MicrowaveCavityInsertPolicy(rig)
        self.microwave_cavity_release = MicrowaveCavityReleasePolicy(rig)
        self.microwave_cavity_withdraw = MicrowaveCavityWithdrawPolicy(rig)
        self.prepare_floor_reach = PrepareFloorReachPolicy(rig)
        self.slide_to_edge = SlideToEdgePolicy(rig)
        self.grasp_articulated_handle = GraspArticulatedHandlePolicy(rig)
        self.release_articulated_handle = ReleaseArticulatedHandlePolicy(rig)
        self.pick_from_cavity = PickFromCavityPolicy(rig)
        self.open_revolute_door = OpenRevoluteDoorPolicy(rig)
        self.open_prismatic_drawer = OpenPrismaticDrawerPolicy(rig)
        self.reach_while_moving = ReachWhileMovingPolicy(rig)
        self.pick_while_moving = PickWhileMovingPolicy(rig)
        self.place_while_moving = PlaceWhileMovingPolicy(rig)
        self.upright_object = UprightObjectPolicy(rig)
        self.wait_for_temperature = WaitForTemperaturePolicy(rig)
        self.pick_cup_handle = PickCupHandlePolicy(rig)
        self.bimanual_flat_pick = BimanualFlatPickPolicy(rig)
        self.bimanual_box_lift = BimanualBoxLiftPolicy(rig)
        self.bimanual_carry = BimanualCarryPolicy(rig)
        self.handover_right_to_left = HandoverRightToLeftPolicy(rig)
        self.open_door_while_left_holds = OpenDoorWhileLeftHoldsPolicy(rig)
        self.right_gripper_open = RightGripperOpenPolicy(rig)
        self.right_gripper_close = RightGripperClosePolicy(rig)
        self.right_tcp_move = RightTcpMovePolicy(rig)
        self.right_joint_move = RightJointMovePolicy(rig)
        self.carry_height_adjust = CarryHeightAdjustPolicy(rig)
        self.back_off_with_load = BackOffWithLoadPolicy(rig)
        self.base_rotate_in_place = BaseRotateInPlacePolicy(rig)
        self.base_translate_local = BaseTranslateLocalPolicy(rig)
        self.push_from_behind = PushFromBehindPolicy(rig)
        self.top_drag = TopDragPolicy(rig)

        # Explicit strategies let a skill graph or manual plan select a route.
        self.empty_navigate = EmptyHandNavigatePolicy(rig)
        self.carry_navigate = CarryNavigatePolicy(rig)
        self.tuck_arm = TuckArmPolicy(rig)
        self.set_torso_height = SetTorsoHeightPolicy(rig)
        self.lower_torso = LowerTorsoPolicy(rig)
        self.raise_torso = RaiseTorsoPolicy(rig)
        self.set_waist_pitch = SetWaistPitchPolicy(rig)
        self.lean_forward = LeanForwardPolicy(rig)
        self.straighten_waist = StraightenWaistPolicy(rig)
        self.pick_top = TopPinchPickPolicy(rig)
        self.pick_round_rim = RoundRimPickPolicy(rig)
        self.pick_rect_rim = RectRimPickPolicy(rig)
        self.pick_edge = EdgePickPolicy(rig)
        self.pick_floor_corner = FloorCornerPickPolicy(rig)
        self.place_surface = SurfacePlacePolicy(rig)
        self.place_container = ContainerPlacePolicy(rig)
        self.place_edge = EdgePlacePolicy(rig)
        self.place_microwave = MicrowavePlacePolicy(rig)
        self.open_handle = HandleOpenPolicy(rig)
        self.close_handle = HandleClosePolicy(rig)
        self.open_powered = PoweredDoorOpenPolicy(rig)
        self.close_powered = PoweredDoorClosePolicy(rig)

        # Skill library v2 policies (noun-addressed, GT-verified)
        self.approach_target = ApproachTargetPolicy(rig)
        self.face_target = FaceTargetPolicy(rig)
        self.retreat_from = RetreatFromPolicy(rig)
        self.look_at = LookAtPolicy(rig)
        self.explore_room = ExploreRoomPolicy(rig)
        self.search_object = SearchObjectPolicy(rig)
        self.point_at = PointAtPolicy(rig)
        self.present_held = PresentHeldPolicy(rig)
        self.drop_into = DropIntoPolicy(rig)
        self.stack_on = StackOnPolicy(rig)
        self.rotate_held = RotateHeldPolicy(rig)
        self.regrasp = RegraspPolicy(rig)
        self.left_steady = LeftSteadyPolicy(rig)
        self.flip_flat = FlipFlatPolicy(rig)
        self.pull_toward_base = PullTowardBasePolicy(rig)
        self.separate_from_neighbour = SeparateFromNeighbourPolicy(rig)
        self.roll_cylinder = RollCylinderPolicy(rig)
        self.tip_over = TipOverPolicy(rig)
        self.center_on_support = CenterOnSupportPolicy(rig)
        self.wipe_surface = WipeSurfacePolicy(rig)
        self.stir_container = StirContainerPolicy(rig)
        self.pour_into = PourIntoPolicy(rig)
        self.cover_with_lid = CoverWithLidPolicy(rig)
        self.inspect_receptacle = InspectReceptaclePolicy(rig)
        self.wait_cool = WaitCoolPolicy(rig)
        self.wait_heat = WaitHeatPolicy(rig)
        self.left_arm_fold = LeftArmFoldPolicy(rig)
        self.navigate_to_place = NavigateToPlacePolicy(rig)
        self.set_held_height = SetHeldHeightPolicy(rig)
        self.press_button = PressButtonPolicy(rig)
        self.release_in_place = ReleaseInPlacePolicy(rig)

        self.plan_home = PlanHomePolicy(rig)
        self.plan_standoff = PlanStandoffPolicy(rig)
        self.plan_reach = PlanReachPolicy(rig)
        self.plan_heading = PlanHeadingPolicy(rig)
        self.plan_retreat = PlanRetreatPolicy(rig)
        self.plan_point = PlanPointPolicy(rig)

        self.shake_held = ShakeHeldPolicy(rig)
        self.wait_seconds = WaitPolicy(rig)
        self.wave_hand = WaveHandPolicy(rig)
        self.nod_head = NodHeadPolicy(rig)
        self.knock_panel = KnockPanelPolicy(rig)
        self.touch_object = TouchObjectPolicy(rig)
        self.plan_square_yaw = PlanSquareYawPolicy(rig)
        self.sweep_together = SweepTogetherPolicy(rig)
        self.identify_object = IdentifyObjectPolicy(rig)
        self.measure_object = MeasureObjectPolicy(rig)
        self.count_category = CountCategoryPolicy(rig)
        self.dip_utensil = DipUtensilPolicy(rig)
        self.sidestep_base = SidestepPolicy(rig)
        self.hover_over = HoverOverPolicy(rig)

        # Composites are convenience sequences, not atomic policies.
        self.pick_and_carry = PickAndCarryPolicy(rig)
        self.microwave_door_cycle = MicrowaveDoorCycle(rig)

        # Public stable IDs coexist with historical descriptive attributes.
        for legacy_id, public_id in POLICY_PUBLIC_IDS.items():
            setattr(self, public_id, getattr(self, legacy_id))


__all__ = [
    "PrepareFloorReachPolicy", "SlideToEdgePolicy", "GraspArticulatedHandlePolicy",
    "ReleaseArticulatedHandlePolicy", "PickFromCavityPolicy", "OpenRevoluteDoorPolicy",
    "OpenPrismaticDrawerPolicy", "ReachWhileMovingPolicy", "PickWhileMovingPolicy",
    "PlaceWhileMovingPolicy", "UprightObjectPolicy", "WaitForTemperaturePolicy", "PickCupHandlePolicy",
    "BimanualFlatPickPolicy",
    "BimanualBoxLiftPolicy", "BimanualCarryPolicy", "HandoverRightToLeftPolicy",
    "OpenDoorWhileLeftHoldsPolicy",
    "AtomicPolicy", "PolicySuite", "NavigatePolicy", "EmptyHandNavigatePolicy", "CarryNavigatePolicy",
    "PickAndCarryPolicy", "TuckArmPolicy", "SetTorsoHeightPolicy", "LowerTorsoPolicy", "RaiseTorsoPolicy",
    "SetWaistPitchPolicy", "LeanForwardPolicy", "StraightenWaistPolicy", "ClickPolicy",
    "OpenPolicy", "ClosePolicy", "HandleOpenPolicy", "HandleClosePolicy", "PoweredDoorOpenPolicy",
    "PoweredDoorClosePolicy", "PickPolicy", "TopPinchPickPolicy", "RoundRimPickPolicy", "RectRimPickPolicy",
    "EdgePickPolicy", "FloorCornerPickPolicy", "PlacePolicy", "SurfacePlacePolicy", "ContainerPlacePolicy",
    "EdgePlacePolicy", "MicrowavePlacePolicy", "PushPolicy", "PushFromBehindPolicy", "TopDragPolicy",
    "RightGripperOpenPolicy", "RightGripperClosePolicy", "RightTcpMovePolicy", "RightJointMovePolicy",
    "CarryHeightAdjustPolicy", "BackOffWithLoadPolicy", "BaseRotateInPlacePolicy",
    "BaseTranslateLocalPolicy", "MicrowaveStartPolicy", "MicrowaveButtonApproachPolicy",
    "MicrowaveButtonPressPolicy", "MicrowaveButtonRetractPolicy", "MicrowaveDoorClearPolicy",
    "MicrowaveHingeDrivePolicy", "MicrowaveCavityInsertPolicy", "MicrowaveCavityReleasePolicy",
    "MicrowaveCavityWithdrawPolicy", "MicrowaveDoorCycle",
]
