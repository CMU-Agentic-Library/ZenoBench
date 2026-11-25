"""Independent entry points for action stages previously buried in larger skills."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy
from .posture import LowerTorsoPolicy, SetWaistPitchPolicy
from .. import skills
from ..clearance import FREE_ELSE_STRAIGHT, LEGACY, lifting
from ..kinematics import gripper_rot
from ..physics import PHYSICS_HZ
from ..rig import SkillFailure


class PrepareFloorReachPolicy(AtomicPolicy):
    """Lower the torso, lean, and reach a measured pre-grasp above a floor item."""

    def execute(self, name, *, clearance_m=0.10):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("prepare floor reach: right hand must be empty")
        if name not in rig.ann.objects:
            raise SkillFailure(f"prepare floor reach: unknown object {name}")
        st = rig.state()
        bottom = rig.geo.bottom(name, st)
        if bottom[2] >= 0.05:
            raise SkillFailure(f"prepare floor reach: {name} is not on the floor")
        size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
        bx, by, _ = rig.base_pose()
        away = np.array([bx, by]) - bottom[:2]
        norm = np.linalg.norm(away)
        if norm < 1e-6:
            raise SkillFailure("prepare floor reach: base is directly over the object")
        away /= norm
        side = max(size[:2]) / 2
        LowerTorsoPolicy(rig).execute()
        idx = rig.kin.names.index("waist_pitch_joint")
        SetWaistPitchPolicy(rig).execute(min(0.30, float(rig.kin.hi[idx])))
        rig.sync_world()
        # A floor pregrasp is above the item. The earlier fixed 13 cm target
        # can put the palm through the floor at the lowered torso posture.
        # Search collision-checked clearances, then drive the reachable pose.
        chosen = None
        distances = (side + clearance_m, side + 0.06, side + 0.02)
        heights = (bottom[2] + 0.18, bottom[2] + 0.24,
                   bottom[2] + 0.30, bottom[2] + 0.38)
        for distance in distances:
            for height in heights:
                target = np.r_[bottom[:2] + away * distance, height]
                for pitch in (-0.3, -0.6, 0.0, 0.3):
                    R = gripper_rot(np.r_[-away, pitch], [0, 0, 1])
                    q, ok = rig.kin.ik_global(target, R, seeds=[rig.q_cmd])
                    if ok:
                        chosen = (target, R, q)
                        break
                if chosen is not None:
                    break
            if chosen is not None:
                break
        if chosen is None:
            raise SkillFailure(f"prepare floor reach: no clear pregrasp above {name}")
        target, R, q = chosen
        rig.move_to(target, R, label="prepare_floor_reach", q_hint=q)
        tcp, _ = rig.kin.tcp(rig.q())
        error = float(np.linalg.norm(tcp - target))
        if error > 0.03:
            raise SkillFailure(f"prepare floor reach: TCP missed by {error:.3f} m")
        rig.log("floor_reach_ready", obj=name, error_m=round(error, 4))
        return error


class SlideToEdgePolicy(AtomicPolicy):
    """Move a flat item into a measured graspable overhang without grasping it."""

    def execute(self, name):
        from ..skill_jobs.slide import push_object
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("slide to edge: right hand must be empty")
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


class GraspArticulatedHandlePolicy(AtomicPolicy):
    """Hold a manual handle with the right gripper, checking finger contact."""

    def execute(self, name):
        rig = self.rig
        art = rig.ann.art(name)
        if rig.held is not None or getattr(rig, "_handle_grasp", None) is not None:
            raise SkillFailure("grasp handle: right hand is occupied")
        if not art.get("handle") or "door_button" in art:
            raise SkillFailure(f"grasp handle: {name} has no manual handle route")
        q = rig.joint(name)
        rig.sync_world()
        old_coll_kw = rig.kin.coll_kw
        rig.kin.coll_kw = {"hand_touches_part": True}
        candidates = [("side", False, 0.0)]
        if art["type"] == "prismatic" or art["handle"].get("flip_ok"):
            candidates.append(("side", True, 0.0))
        if art["handle"].get("pre_open") is not None:
            candidates.append(("front", False, 0.0))
        for grasp, flip, tilt in candidates:
            _, _, _, targets = skills._handle_targets(rig, art, q, flip, tilt, grasp)
            park = skills.find_park(rig.kin, rig.world, targets, near=rig.base_pose(),
                                    q_start=rig.q_cmd, travel_q=skills._travel_q(rig), max_tries=120)
            if park is not None:
                break
        else:
            rig.kin.coll_kw = old_coll_kw
            raise SkillFailure(f"grasp handle {name}: no reachable handle path")
        skills._goto_park(rig, park)
        thickness = float(art["handle"].get("thickness", 0.025))
        pre_open = float(art["handle"].get("pre_open", 0.04))
        rig.grip(pre_open, 30)
        for k_, (target, label, hint) in enumerate(zip(targets, ("handle_pre_high", "handle_pre", "handle_contact"),
                                                         park[3])):
            if k_ == 0 and hint is not None:
                # onto the planned joint branch first: a straight line from the
                # compact tuck reached the pre-pose on another branch, from
                # which the short move to the handle had no joint path
                try:
                    rig.sync_world()
                    rig.follow(rig.joint_path(np.asarray(hint), label))
                    continue
                except SkillFailure as exc:
                    rig.log("handle_pre_branch_short", reason=str(exc))
            rig.move_to(*target, label=label, q_hint=hint)
        fingers = rig.grip(0.0, PHYSICS_HZ)
        if fingers.min() <= min(0.004, 0.3*thickness):
            rig.kin.coll_kw = old_coll_kw
            raise SkillFailure(f"grasp handle {name}: no finger contact")
        rig._handle_grasp = {"name": name, "pre_open": pre_open, "q": rig.joint(name),
                             "coll_kw": old_coll_kw}
        rig.log("handle_grasped", name=name, fingers=fingers.tolist())
        return fingers


class ReleaseArticulatedHandlePolicy(AtomicPolicy):
    """Release a handle grasp and confirm both fingers opened."""

    def execute(self, name):
        rig = self.rig
        held = getattr(rig, "_handle_grasp", None)
        if held is None or held["name"] != name:
            raise SkillFailure(f"release handle {name}: no matching handle grasp")
        fingers = rig.grip(max(0.025, held["pre_open"]), 90)
        if fingers.min() < 0.02:
            raise SkillFailure(f"release handle {name}: fingers did not open")
        rig._handle_grasp = None
        rig.kin.coll_kw = held.get("coll_kw", {})
        rig.log("handle_released", name=name, fingers=fingers.tolist())
        return fingers


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
