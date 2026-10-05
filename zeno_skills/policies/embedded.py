"""Independent entry points for action stages previously buried in larger skills."""

from __future__ import annotations

import numpy as np

from .base import AtomicPolicy
from .posture import LowerTorsoPolicy, SetWaistPitchPolicy
from .. import skills
from ..kinematics import gripper_rot
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
            target_overhang = min(0.08, half - skills.COM_MARGIN)
            if target_overhang < skills.EDGE_MIN_OVERHANG:
                continue
            current = float(direction @ b[:2]) + half - skills._edge_coord(support, direction)
            choices.append((max(0.0, target_overhang-current), direction, target_overhang))
        if not choices:
            raise SkillFailure(f"slide to edge: no graspable free edge of {support['name']}")
        choices.sort(key=lambda item: item[0])
        last = None
        for need, direction, target_overhang in choices[:3]:
            try:
                if need > 0.012:
                    skills.push(rig, name, support, direction, need + 0.005,
                                label="SLIDE_TO_EDGE", enough=need)
                st = rig.state()
                b = rig.geo.bottom(name, st)
                half = skills._half_along(size, skills._yaw(st["objects"][name]["quat"]), direction)
                overhang = float(direction @ b[:2]) + half - skills._edge_coord(support, direction)
                if overhang < skills.EDGE_MIN_OVERHANG - 0.01:
                    raise SkillFailure(f"slide to edge: only {overhang:.3f} m overhang")
                if overhang > half - skills.COM_MARGIN + 0.015:
                    raise SkillFailure("slide to edge: centre of mass may leave the support")
                rig.log("slide_to_edge_result", obj=name, support=support["name"],
                        overhang_m=round(overhang, 4), direction=direction.tolist())
                return {"support": support["name"], "direction": direction.tolist(),
                        "overhang_m": overhang}
            except SkillFailure as exc:
                last = exc
                rig.log("slide_to_edge_retry", obj=name, reason=str(exc))
        raise last


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
        for target, label, hint in zip(targets, ("handle_pre_high", "handle_pre", "handle_contact"), park[3]):
            rig.move_to(*target, label=label, q_hint=hint)
        fingers = rig.grip(0.0, 120)
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
    """Pick an object in an open annotated cavity, then withdraw beyond its mouth."""

    def execute(self, name, cavity="kitchen_microwave", *, max_candidates=12):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("pick from cavity: right hand is occupied")
        art = rig.ann.art(cavity)
        bounds = art.get("cavity_aabb")
        if bounds is None:
            raise SkillFailure(f"pick from cavity: {cavity} has no cavity annotation")
        pos, _ = rig.obj_pose(name)
        if not all(bounds[i] < pos[i] < bounds[i+3] for i in range(3)):
            raise SkillFailure(f"pick from cavity: {name} is outside {cavity}")
        if abs(rig.joint(cavity)-art["open_q"]) > 0.10:
            raise SkillFailure(f"pick from cavity: {cavity} is closed")
        outward = np.asarray(art.get("handle", {}).get("outward", [0, -1, 0]), float)
        axis = int(np.argmax(np.abs(outward[:2])))
        sign = float(np.sign(outward[axis]))
        if sign == 0:
            raise SkillFailure(f"pick from cavity: {cavity} has no annotated front direction")
        stage = getattr(rig, "_microwave_retrieval_stage", None)
        if stage and stage.get("name") == name and stage.get("phase") == "released":
            # Reverse the measured insertion approach. Generic rim samples can
            # be unreachable through the narrow open door even when the pose
            # that loaded this exact object is reachable.
            rig.sync_world()
            rig.kin.coll_kw = {"ignore_fingers": True}
            rig.follow(rig.joint_path(rig.microwave_retrieval_q, "cavity_return_safe"))
            rig.drive_base([stage["release_base"]], speed=0.12)
            rig.sync_world()
            before, _ = rig.obj_pose(name)
            target = stage["release_tcp"] + before-stage["release_body"]
            R = stage["R"]
            rig.grip(stage["pre_open"], 40)
            front_err = rig.move_to(target+np.array([0, -0.10, 0.06]), R,
                                    label="cavity_pick_front", collision=False)
            if front_err > 0.02:
                raise SkillFailure(f"pick from cavity {name}: front approach missed by {front_err:.3f} m")
            above_err = rig.move_to(target+np.array([0, 0, 0.045]), R,
                                    label="cavity_pick_above", collision=False)
            if above_err > 0.20:
                raise SkillFailure(f"pick from cavity {name}: upper approach missed by {above_err:.3f} m")
            if above_err > 0.02:
                rig.log("cavity_intermediate_tracking", obj=name,
                        tcp_error_m=round(float(above_err), 4))
            err = rig.move_to(target, R, step=0.003, steps_per_wp=5,
                              label="cavity_pick_contact", collision=False)
            if err > 0.02:
                # A measured insertion-reversal pose may be kinematically valid
                # yet blocked by the shell in dynamics. Replan a different
                # annotated rim contact before attempting to close the fingers.
                rig.log("cavity_retrieval_replan", obj=name,
                        contact_error_m=round(float(err), 4))
                result = skills._pick_pinch(rig, name, max_candidates=max_candidates)
                body, _ = rig.obj_pose(name)
                mouth = bounds[axis] if sign < 0 else bounds[axis+3]
                if rig.held is None or rig.held["name"] != name or sign*(body[axis]-mouth) < 0.02:
                    raise SkillFailure(f"pick from cavity {name}: fallback did not withdraw through the front")
                skills.check_held(rig, "pick_from_cavity_replan")
                return result
            fingers = rig.grip(0.0, 120)
            rig.move_to(target+np.array([0, 0, 0.07]), R, step=0.003,
                        steps_per_wp=5, label="cavity_pick_lift", collision=False)
            rig.step(40)
            after, _ = rig.obj_pose(name)
            if after[2]-before[2] < 0.015 or fingers.min() < 0.003:
                raise SkillFailure(f"pick from cavity {name}: did not lift after contact")
            tcp, actual_R = rig.kin.tcp(rig.q())
            rig.held = {"name": name, "kind": "pinch", "tcp_minus_body": tcp-after,
                        "R": actual_R, "pre_open": stage["pre_open"]}
            for y in (bounds[1]-0.10, bounds[1]-0.23):
                tcp, _ = rig.kin.tcp(rig.q())
                front = tcp.copy()
                front[1] = y
                rig.move_to(front, actual_R, label="cavity_pick_withdraw")
                skills.check_held(rig, "cavity_pick_withdraw")
                body, _ = rig.obj_pose(name)
                rig.log("cavity_withdraw_check", obj=name,
                        body=body.round(3).tolist(), mouth=float(bounds[1]))
                if body[1] < bounds[1]-0.02:
                    break
            result = True
        else:
            result = skills._pick_pinch(rig, name, max_candidates=max_candidates)
        pos, _ = rig.obj_pose(name)
        mouth = bounds[axis] if sign < 0 else bounds[axis+3]
        if rig.held is None or rig.held["name"] != name or sign*(pos[axis]-mouth) < 0.02:
            raise SkillFailure(f"pick from cavity {name}: did not withdraw through the front")
        skills.check_held(rig, "pick_from_cavity")
        return result


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
