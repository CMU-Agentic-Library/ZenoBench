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
from ..planner import find_park
from ..predicates import lid_on, tilt_deg
from ..rig import SkillFailure


def _park_diag():
    from ..planner import LAST_PARK_DIAG
    return {k: v for k, v in LAST_PARK_DIAG.items() if v}


def _require_held(rig, name, action):
    if rig.held is None or rig.held["name"] != name:
        raise SkillFailure(f"{action} {name}: not right-held")
    skills.check_held(rig, f"{action}_start")


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
    """Hold the object 5 cm above the container rim, centred, and let go."""

    def execute(self, name, container, *, clearance_m=0.05):
        rig = self.rig
        _require_held(rig, name, "drop")
        ca = rig.ann.asset_of(rig.ann.objects[container]).get("container")
        if not ca:
            raise SkillFailure(f"drop {name}: {container} is not a container")
        st = rig.state()
        cb = np.asarray(rig.geo.bottom(container, st), float)
        rim_z = float(cb[2] + ca["rim_height"])
        # already held over the opening (after hover): just let go
        fp = rig.geo.footprint(name, st)
        inner = float(ca.get("rim_radius", 0.0)) or 0.5 * float(min(rig.ann.asset_of(rig.ann.objects[container])["size"][:2]))
        centre = np.array([(fp[0] + fp[2]) / 2, (fp[1] + fp[3]) / 2])
        low = float(skills._lowest_z(rig, name, st))
        if np.linalg.norm(centre - cb[:2]) < 0.6 * inner and rim_z < low < rim_z + 0.25:
            rig.log("drop_in_place", obj=name, container=container, height_above_rim=round(low - rim_z, 3))
            rig.caption = f"DROP {name} into {container}"
            return self._release(name, container)
        from .tooluse import stow_load
        stow_load(rig)
        st = rig.state()
        tcp, R = rig.kin.tcp(rig.q_cmd)
        body, _ = rig.obj_pose(name)
        hang = float(body[2] - skills._lowest_z(rig, name, st))
        off = tcp - body
        body_goal = np.array([cb[0], cb[1], rim_z + clearance_m + hang])
        legs = [(body_goal + off + np.array([0, 0, 0.06]), R), (body_goal + off, R)]
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        park = find_park(rig.kin, rig.world, legs, near=rig.base_pose(), max_tries=150, q_start=rig.q_cmd,
                         travel_q=skills._travel_q(rig))
        if park is None:
            raise SkillFailure(f"drop {name}: no base pose above {container} (rejected: {_park_diag()})")
        skills._goto_park(rig, park)
        # rise first so the load never sweeps through the rim
        low = float(rig.geo.bottom(name, rig.state())[2])
        if low < rim_z + clearance_m:
            t, R1 = rig.kin.tcp(rig.q_cmd)
            rig.move_to(t + np.array([0, 0, rim_z + clearance_m + 0.04 - low]), R1, step=0.005,
                        label="drop_prelift", collision=False)
        rig.caption = f"DROP {name} into {container}"
        for p, Rg in legs:
            rig.move_to(p, Rg, step=0.005, steps_per_wp=5, label="drop_above", collision=False, smooth=True)
        skills.check_held(rig, "drop_above")
        return self._release(name, container)

    def _release(self, name, container):
        rig = self.rig
        rig.grip(rig.held.get("pre_open", 0.04), 40)
        rig.held = None
        t, R1 = rig.kin.tcp(rig.q_cmd)
        try:
            rig.move_to(t + np.array([0, 0, 0.06]), R1, step=0.01, label="drop_retreat", collision=False)
        except SkillFailure as exc:
            rig.log("drop_retreat_short", reason=str(exc))
        rig.step(120)
        ok, why = rig.geo.inside(name, container, rig.state())
        rig.log("drop_result", obj=name, container=container, inside=bool(ok), detail=why)
        if not ok:
            raise SkillFailure(f"drop {name} into {container}: {why}")
        return True


class StackOnPolicy(AtomicPolicy):
    """Place a held object centred on another object's top face."""

    def execute(self, name, base):
        rig = self.rig
        _require_held(rig, name, "stack")
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
    """Rotate the held object about the vertical axis through the TCP.

    The wrist turn is tried at a few staging poses closer to the body and
    higher, where the arm has more orientation range."""

    def execute(self, name, degrees):
        rig = self.rig
        _require_held(rig, name, "rotate")
        q0 = rig.obj_pose(name)[1]
        tcp, R = rig.kin.tcp(rig.q_cmd)
        steps = max(1, int(math.ceil(abs(float(degrees)) / 15.0)))
        x, y, _ = rig.base_pose()
        toward = np.array([x, y]) - tcp[:2]
        dist = float(np.linalg.norm(toward))
        unit = toward / dist if dist > 1e-6 else np.zeros(2)
        last = None
        done = False
        for pull, up in ((0.15, 0.06), (0.25, 0.12), (0.05, 0.04), (0.30, 0.20)):
            stage = tcp + np.r_[unit * min(pull, max(0.0, dist - 0.35)), up]
            Rs = [rz(math.radians(float(degrees)) * k / steps) @ R for k in range(1, steps + 1)]
            if not all(rig.kin.ik_global(stage, Rk, seeds=[rig.q_cmd])[1] for Rk in Rs[-1:]):
                continue                     # the final orientation has no IK here
            try:
                rig.move_to(stage, R, step=0.005, label="rotate_clear", collision=False)
                for Rk in Rs:
                    rig.move_to(stage, Rk, step=0.005, steps_per_wp=4, label="rotate_held", collision=False,
                                smooth=True)
                    skills.check_held(rig, "rotate_held")
                done = True
                break
            except SkillFailure as exc:
                last = exc
                if rig.held is None:
                    raise
        if not done:
            raise last or SkillFailure(f"rotate {name}: no staging pose allows a {degrees:.0f} deg wrist turn")
        tcp1, R1 = rig.kin.tcp(rig.q())
        body, q1 = rig.obj_pose(name)
        rig.held["tcp_minus_body"] = tcp1 - body
        rig.held["R"] = R1

        def yaw(q):
            w, x_, y_, z = q
            return math.degrees(math.atan2(2 * (w * z + x_ * y_), 1 - 2 * (y_ * y_ + z * z)))
        change = (yaw(q1) - yaw(q0) + 180) % 360 - 180
        rig.log("rotate_result", obj=name, requested=float(degrees), yaw_change=round(change, 1))
        if abs((change - float(degrees) + 180) % 360 - 180) > 10:
            raise SkillFailure(f"rotate {name}: yaw changed {change:.1f} deg")
        return change


class RegraspPolicy(AtomicPolicy):
    """Put the object down on a support and pick it again with a fresh grasp."""

    def execute(self, name, support):
        rig = self.rig
        _require_held(rig, name, "regrasp")
        before = rig.held.get("kind")
        # set it down where the arm is: the support point nearest the base, 12 cm in
        s = rig.ann.support(support)
        x0, y0, x1, y1 = s["aabb_xy"]
        st = rig.state()
        fp = rig.geo.footprint(name, st)
        if fp[0] > x0 + 0.02 and fp[2] < x1 - 0.02 and fp[1] > y0 + 0.02 and fp[3] < y1 - 0.02 and \
                not skills._overlaps_objects(rig, [fp[0], fp[1], s["z"] + 0.005, fp[2], fp[3], s["z"] + 0.3],
                                             {name}, st, margin=0.01):
            # already over a free patch of the support: set it straight down
            # (no wrist turn, no re-park: a pinched cylinder rolls out of both)
            low = float(skills._lowest_z(rig, name, st))
            skills.held_vertical_move(rig, s["z"] + 0.006 - low, "regrasp_set_down", step=0.003)
            rig.grip(rig.held.get("pre_open", 0.04), 60, gradual=True)
            rig.held = None
            t, R = rig.kin.tcp(rig.q_cmd)
            rig.move_to(t + np.array([0, 0, 0.06]), R, step=0.005, label="regrasp_clear", collision=False)
        else:
            x, y, _ = rig.base_pose()
            hint = (min(max(x, x0 + 0.12), x1 - 0.12), min(max(y, y0 + 0.12), y1 - 0.12))
            skills.place_on(rig, name, support, hint=hint)
        rig.step(60)
        skills.pick(rig, name)
        kind = rig.held["kind"] if rig.held else None
        rig.log("regrasp_result", obj=name, before=before, after=kind)
        if rig.held is None or rig.held["name"] != name:
            raise SkillFailure(f"regrasp {name}: not held after the second grasp")
        return kind


class LeftSteadyPolicy(AtomicPolicy):
    """Pinch a resting container's rim (or an object's top) with the left
    gripper so the right hand can work in it without the object sliding."""

    def execute(self, name):
        rig = self.rig
        if rig.left_held is not None:
            raise SkillFailure("steady: the left hand is occupied")
        obj = rig.ann.objects[name]
        pos, quat = rig.obj_pose(name)
        cands = rig.ann.grasp_poses(obj, pos, quat, kinds=("rim_pinch", "rim_pinch_rect", "top_pinch", "handle_pinch"))
        if not cands:
            raise SkillFailure(f"steady {name}: no annotated pinch contact")
        x, y, yaw = rig.base_pose()
        left_dir = np.array([-math.sin(math.radians(yaw)), math.cos(math.radians(yaw))])
        cands.sort(key=lambda g: -float((g["p"][:2] - pos[:2]) @ left_dir))
        rig.sync_world()
        rig.world.left_active = True
        start = np.r_[rig.q_cmd[:2], rig.left_q_cmd]
        lo, hi = rig.left_kin.lo.copy(), rig.left_kin.hi.copy()
        chosen = None
        try:
            rig.left_kin.lo[:2] = rig.left_kin.hi[:2] = rig.q_cmd[:2]
            for g in cands[:16]:
                pre = g["p"] + np.array([0, 0, 0.08])
                q1, ok1 = rig.left_kin.ik_global(pre, g["R"], seeds=[start])
                q2, ok2 = rig.left_kin.ik_global(g["p"], g["R"], seeds=[q1])
                if ok1 and ok2:
                    chosen = g
                    break
        finally:
            rig.left_kin.lo[:], rig.left_kin.hi[:] = lo, hi
        if chosen is None:
            # Re-park the base for the left arm (torso free; the right hand is idle).
            for g in cands[:8]:
                targets = [(g["p"] + np.array([0, 0, 0.08]), g["R"]), (g["p"], g["R"])]
                park = find_park(rig.left_kin, rig.world, targets, near=rig.base_pose()[:2], max_tries=150,
                                 shoulder=(0.09, 0.18))
                if park is not None:
                    chosen = g
                    if not rig.tuck():
                        raise SkillFailure(f"steady {name}: cannot fold the right arm before re-parking")
                    skills.navigate(rig, park[:3], label="steady_park")
                    rig.sync_world()
                    rig.world.left_active = True
                    break
            if chosen is None:
                raise SkillFailure(f"steady {name}: no base pose lets the left arm reach a contact (rejected: {_park_diag()})")
        rig.caption = f"STEADY {name} with the left hand"
        rig.left_grip(chosen["pre_open"], 30)
        rig.move_left_to(chosen["p"] + np.array([0, 0, 0.08]), chosen["R"], label="steady_pre")
        rig.move_left_to(chosen["p"], chosen["R"], label="steady_grasp", collision=False)
        rig.left_grip(0.0, 100)
        f = rig.left_fingers()
        after, _ = rig.obj_pose(name)
        if float(f.sum()) < 0.004:
            rig.left_grip(0.04, 30)
            raise SkillFailure(f"steady {name}: left fingers closed on nothing")
        tcp, R = rig.left_kin.tcp(rig.left_q())
        rig.left_held = {"name": name, "kind": "steady", "tcp_minus_body": tcp - after, "R": R,
                         "pre_open": chosen["pre_open"]}
        rig.log("steady_result", obj=name, kind=chosen["kind"], fingers=f.round(4).tolist(),
                shift_m=round(float(np.linalg.norm(after - pos)), 4))
        return chosen["kind"]


class ReleaseInPlacePolicy(AtomicPolicy):
    """Open one gripper without moving the object first, then back the fingers off."""

    def execute(self, name, hand="right"):
        rig = self.rig
        if hand == "right":
            if rig.held is None or rig.held["name"] != name:
                raise SkillFailure(f"release {name}: not right-held")
            rig.grip(rig.held.get("pre_open", 0.04), 60, gradual=True)
            rig.held = None
            t, R = rig.kin.tcp(rig.q_cmd)
            try:
                rig.move_to(t + 0.06 * R[:, 2], R, step=0.005, label="release_back", collision=False)
            except SkillFailure as exc:
                rig.log("release_back_short", reason=str(exc))
        else:
            if rig.left_held is None or rig.left_held["name"] != name:
                raise SkillFailure(f"release {name}: not left-held")
            rig.left_grip(0.04, 60)
            rig.left_held = None
            t, R = rig.left_kin.tcp(rig.left_q())
            try:
                rig.move_left_to(t + 0.06 * R[:, 2], R, label="left_release_back", collision=False)
            except SkillFailure as exc:
                rig.log("left_release_back_short", reason=str(exc))
        rig.step(60)
        rig.log("release_result", obj=name, hand=hand)
        return True


class FlipFlatPolicy(AtomicPolicy):
    """Turn an edge-held flat object over by pivoting it about its far edge:
    the gripped near edge travels up and over on an arc (the hand pitches with
    it) until the object passes vertical, then the fingers open and it falls
    onto its other face, one object-length further onto the support."""

    def execute(self, name, *, release_deg=105.0, step_deg=10.0):
        rig = self.rig
        _require_held(rig, name, "flip")
        if rig.held.get("kind") != "edge":
            raise SkillFailure(f"flip {name}: needs an edge pinch (pick it from an overhang first)")
        st = rig.state()
        tcp0, R0 = rig.kin.tcp(rig.q_cmd)
        approach = -R0[:, 2]
        a = np.array([approach[0], approach[1], 0.0])
        a /= max(1e-9, np.linalg.norm(a))
        size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
        body, quat = rig.obj_pose(name)
        from ..evaluator import quat_R
        Rb = quat_R(quat)
        length = float(np.abs(Rb[:2, :2].T @ a[:2]) @ size[:2])     # extent along the approach
        bottom = rig.geo.bottom(name, st)
        # pivot: the far edge of the object on the support surface
        pivot = np.r_[bottom[:2] + a[:2] * length / 2, bottom[2]]
        s = rig.geo.support_under(name, st)
        if s is not None:
            from .contact import _room_along
            if _room_along(rig, name, s, a[:2]) < length * 0.9:
                raise SkillFailure(f"flip {name}: no room on {s['name']} to land it turned over")
        k = np.cross(-a, [0.0, 0.0, 1.0])
        k /= np.linalg.norm(k)
        v0 = tcp0 - pivot
        rig.caption = f"FLIP {name}: pivot over the far edge"
        reached = 0.0
        for deg in np.arange(step_deg, release_deg + 1e-6, step_deg):
            Rot = Rotation.from_rotvec(k * math.radians(deg)).as_matrix()
            try:
                rig.move_to(pivot + Rot @ v0, Rot @ R0, step=0.004, steps_per_wp=4, label="flip_arc", collision=False,
                            smooth=True)
            except SkillFailure as exc:
                rig.log("flip_arc_limit", deg=float(deg), reason=str(exc))
                break
            reached = float(deg)
        if reached < 60.0:
            raise SkillFailure(f"flip {name}: the arc stopped at {reached:.0f} deg")
        rig.grip(rig.held.get("pre_open", 0.04), 50)
        rig.held = None
        if reached < 90.0:
            # the wrist ran out of pitch before vertical: open, keep the hand
            # orientation, and carry on along the arc so the open fingers push
            # the raised edge over the pivot
            R_end = Rotation.from_rotvec(k * math.radians(reached)).as_matrix() @ R0
            pushed = reached
            for deg in np.arange(reached + step_deg, release_deg + 15.0 + 1e-6, step_deg):
                Rot = Rotation.from_rotvec(k * math.radians(deg)).as_matrix()
                try:
                    rig.move_to(pivot + Rot @ v0 + a * 0.01, R_end, step=0.004, steps_per_wp=4, label="flip_push",
                                collision=False, smooth=True)
                except SkillFailure as exc:
                    rig.log("flip_push_limit", deg=float(deg), reason=str(exc))
                    break
                pushed = float(deg)
            if pushed < 95.0:
                # finish with a straight horizontal push of the raised edge over the pivot
                t, R1 = rig.kin.tcp(rig.q_cmd)
                for d in (0.12, 0.08, 0.05):
                    try:
                        rig.move_to(t + a * d, R1, step=0.004, steps_per_wp=4, label="flip_push_straight",
                                    collision=False)
                        pushed = 100.0
                        break
                    except SkillFailure as exc:
                        rig.log("flip_push_straight_short", d=d, reason=str(exc))
                if pushed < 95.0:
                    # the arm is at its limit: the holonomic base carries the open hand forward
                    bx, by, byaw = rig.base_pose()
                    rig.sync_world()
                    for d in (0.10, 0.07, 0.04):
                        if all(rig.world.footprint_clear(bx + a[0] * u, by + a[1] * u, math.radians(byaw))
                               for u in np.linspace(0.02, d, 4)):
                            rig.drive_base([(bx + a[0] * d, by + a[1] * d, byaw)], speed=0.06, ramp=0.3)
                            rig.log("flip_push_base", d=d)
                            pushed = 100.0
                            break
                rig.step(120)
                up = quat_R(rig.obj_pose(name)[1])[:, 2]
                pushed = pushed if up[2] < -0.5 else min(pushed, 94.0)
            rig.log("flip_push", released_deg=reached, pushed_deg=pushed)
            if pushed < 95.0:
                raise SkillFailure(f"flip {name}: the open-hand push stopped at {pushed:.0f} deg")
            reached = pushed
        t, R1 = rig.kin.tcp(rig.q_cmd)
        try:
            rig.move_to(t - 0.08 * (-R1[:, 2]), R1, step=0.005, label="flip_withdraw", collision=False)
        except SkillFailure as exc:
            rig.log("flip_withdraw_short", reason=str(exc))
        rig.step(150)
        if quat_R(rig.obj_pose(name)[1])[2, 2] > -0.5:
            # still leaning on the fingers: push the raised edge on over the pivot
            t, R1 = rig.kin.tcp(rig.q_cmd)
            pushed = False
            for d in (0.10, 0.06, 0.03):
                try:
                    rig.move_to(t + a * d, R1, step=0.004, steps_per_wp=4, label="flip_finish_push", collision=False)
                    pushed = True
                    break
                except SkillFailure as exc:
                    rig.log("flip_finish_push_short", d=d, reason=str(exc))
            if not pushed:
                bx, by, byaw = rig.base_pose()
                rig.sync_world()
                for d in (0.10, 0.06):
                    if all(rig.world.footprint_clear(bx + a[0] * u, by + a[1] * u, math.radians(byaw))
                           for u in np.linspace(0.02, d, 4)):
                        rig.drive_base([(bx + a[0] * d, by + a[1] * d, byaw)], speed=0.06, ramp=0.3)
                        break
            rig.step(150)
            t, R1 = rig.kin.tcp(rig.q_cmd)
            for up in (0.08, 0.04):
                try:
                    rig.move_to(t + np.array([0, 0, up]), R1, step=0.005, label="flip_clear", collision=False)
                    break
                except SkillFailure:
                    continue
            rig.step(90)
        rig.log("flip_result", obj=name, arc_deg=reached, up_z=round(float(quat_R(rig.obj_pose(name)[1])[2, 2]), 3))
        return reached


class CoverWithLidPolicy(AtomicPolicy):
    """Set a held lid centred on a container's rim plane."""

    def execute(self, lid, container):
        rig = self.rig
        _require_held(rig, lid, "cover")
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
    """Move the held object vertically until its bottom is at ``height_m``."""

    def execute(self, name, height_m, *, tolerance=0.02):
        rig = self.rig
        _require_held(rig, name, "set height")
        bottom = float(rig.geo.bottom(name, rig.state())[2])
        dz = float(height_m) - bottom
        if abs(dz) <= tolerance:
            return bottom
        skills.held_vertical_move(rig, dz, "held_height")
        skills.check_held(rig, "held_height")
        bottom = float(rig.geo.bottom(name, rig.state())[2])
        rig.log("held_height_result", obj=name, bottom_z=round(bottom, 3), target=float(height_m))
        if abs(bottom - float(height_m)) > tolerance + 0.01:
            raise SkillFailure(f"set held height: bottom at {bottom:.3f} m")
        return bottom
