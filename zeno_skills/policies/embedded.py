"""Independent entry points for action stages previously buried in larger skills."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy, RetiredPolicy
from .posture import LowerTorsoPolicy, SetWaistPitchPolicy
from .. import skills
from ..clearance import FREE_ELSE_STRAIGHT, LEGACY, lifting
from ..kinematics import gripper_rot
from ..physics import PHYSICS_HZ
from ..rig import SkillFailure


class PrepareFloorReachPolicy(RetiredPolicy):
    """Retired (HAND_PLAN 9j): pick lowers the body itself for a floor object (policy_042)."""

    REPLACED_BY = "pick lowers the body itself for a floor object (policy_042)"


class SlideToEdgePolicy(AtomicPolicy):
    """Move a flat item into a measured graspable overhang without grasping it."""

    def execute(self, name):
        from ..skill_jobs.slide import push_object
        rig = self.rig
        if len(skills.loaded_hands(rig)) == 2:                  # push_object pushes with an empty hand, either
            raise SkillFailure("slide to edge: both hands hold something")
        obj = rig.ann.objects.get(name)
        if obj is None:
            raise SkillFailure(f"slide to edge: unknown object {name}")
        size = np.asarray(rig.ann.asset_of(obj)["size"], float)
        st = rig.state()
        support = rig.geo.support_under(name, st)
        if support is None:
            raise SkillFailure(f"slide to edge: {name} is not on an annotated support")
        b = rig.geo.bottom(name, st)
        yaw = skills._yaw(st["objects"][name]["quat"])
        choices = []
        for direction in skills._open_edges(rig, support):
            half = skills._half_along(size, yaw, direction)
            # just what the edge pinch needs (EDGE_MIN_OVERHANG), its centre of mass at least COM_MARGIN on the top
            most = half - skills.COM_MARGIN
            if most < skills.EDGE_MIN_OVERHANG:
                continue
            current = float(direction @ b[:2]) + half - skills._edge_coord(support, direction)
            need = max(0.0, skills.EDGE_MIN_OVERHANG - current)
            aim = min(need + 0.005, most - current)
            if need > 0.45:
                continue                     # a long slide sweeps through everything on the way
            # the swept footprint must be free of other objects
            fp = rig.geo.footprint(name, st)
            dx, dy = direction * need
            box = [min(fp[0], fp[0] + dx), min(fp[1], fp[1] + dy), max(fp[2], fp[2] + dx),
                   max(fp[3], fp[3] + dy), support["z"] + 0.005, support["z"] + size[2]]
            if need > 0.012 and skills._overlaps_objects(rig, box, {name}, st, margin=0.01):
                continue
            choices.append((need, direction, aim))
        if not choices:
            raise SkillFailure(f"slide to edge: no graspable free edge of {support['name']}")
        need, direction, _ = min(choices, key=lambda item: item[0])
        if need > 0.012:
            # every free edge one goal of one push search, its cost how far it goes (docs/motion/MOTION_ARCHITECTURE.md
            # 7: every way of the task a goal -- no search per edge, no other edge after a failure)
            direction, _ = push_object(rig, name, support, [(n, a, k) for k, n, a in choices],
                                       label="SLIDE_TO_EDGE")
        # (else it already hangs over the nearest edge far enough: no push)
        st = rig.state()
        b = rig.geo.bottom(name, st)
        half = skills._half_along(size, skills._yaw(st["objects"][name]["quat"]), direction)
        overhang = float(direction @ b[:2]) + half - skills._edge_coord(support, direction)
        if overhang < skills.EDGE_MIN_OVERHANG - 0.01:
            raise SkillFailure(f"slide to edge: only {overhang:.3f} m overhang")
        if overhang > half - skills.COM_MARGIN:
            raise SkillFailure(f"slide to edge: centre of mass {half - overhang:.3f} m inside the edge, under "
                               f"{skills.COM_MARGIN} m")
        rig.log("slide_to_edge_result", obj=name, support=support["name"],
                overhang_m=round(overhang, 4), direction=direction.tolist())
        return {"support": support["name"], "direction": direction.tolist(),
                "overhang_m": overhang}


class GraspArticulatedHandlePolicy(RetiredPolicy):
    """Retired (HAND_PLAN 9j): open / close grasp the handle in their own plan (policy_046)."""

    REPLACED_BY = "open / close grasp the handle in their own plan (policy_046)"


class ReleaseArticulatedHandlePolicy(RetiredPolicy):
    """Retired (HAND_PLAN 9j): open / close let go of the handle in their own plan (policy_047)."""

    REPLACED_BY = "open / close let go of the handle in their own plan (policy_047)"


class PickFromCavityPolicy(AtomicPolicy):
    """Retired (policy_048): picked back out of the microwave through the arm pose its old set-down recorded.
    The cavity is a support behind a door like a cabinet's, picked by pick's one path (policy_061,
    skill_plans.plan_pick; docs 9.3 step 8d)."""

    def execute(self, name, cavity="kitchen_microwave", **kwargs):
        raise SkillFailure("PickFromCavityPolicy is retired: pick from the microwave with pick (policy_061)")


class OpenRevoluteDoorPolicy(AtomicPolicy):
    """Open only a manual revolute door, with measured joint readback."""

    def execute(self, name):
        art = self.rig.ann.art(name)
        if art["type"] != "revolute" or not art.get("handle") or "door_button" in art:
            raise SkillFailure(f"open revolute door: {name} is not a manual hinged door")
        return skills.open_articulated(self.rig, name)


class OpenPrismaticDrawerPolicy(AtomicPolicy):
    """Open only a manual prismatic drawer, with measured joint readback."""

    def execute(self, name):
        art = self.rig.ann.art(name)
        if art["type"] != "prismatic" or not art.get("handle"):
            raise SkillFailure(f"open prismatic drawer: {name} is not a manual drawer")
        return skills.open_articulated(self.rig, name)
