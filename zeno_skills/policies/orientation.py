"""Correct the orientation of an already grasped object."""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from .base import AtomicPolicy
from .. import skills
from ..evaluator import quat_R
from ..rig import SkillFailure


class UprightObjectPolicy(AtomicPolicy):
    """Lift and rotate a right-held object's local up axis to world vertical."""

    def execute(self, name, *, max_tilt_deg=15.0):
        rig = self.rig
        if rig.held is None or rig.held["name"] != name or rig.left_held is not None:
            raise SkillFailure(f"upright {name}: requires a right-only grasp of this object")
        skills.check_held(rig, "upright_start")
        body, quat = rig.obj_pose(name)
        body_R = quat_R(quat)
        tilt = math.degrees(math.acos(np.clip(body_R[2, 2], -1.0, 1.0)))
        if tilt <= max_tilt_deg:
            rig.log("upright_result", obj=name, tilt_deg=round(tilt, 3))
            return tilt
        if tilt > 45.0:
            # lying objects are now pinched at their centre (weight at the pinch):
            # turn it in the air near the body first; set it down and pivot or
            # hang it only if that turn has no IK or the object slips
            try:
                return self._turn_in_air(name, max_tilt_deg, body_R, tilt)
            except SkillFailure as exc:
                if rig.held is None or rig.held["name"] != name:
                    raise
                rig.log("upright_turn_in_air_failed", reason=str(exc))
            return self._hang_upright(name, max_tilt_deg)
        return self._turn_in_air(name, max_tilt_deg, body_R, tilt)

    def _turn_in_air(self, name, max_tilt_deg, body_R, tilt):
        rig = self.rig
        axis = body_R[:2, 0]
        if np.linalg.norm(axis) < 0.2:
            axis = np.array([body_R[1, 1], -body_R[0, 1]])
        yaw0 = math.atan2(axis[1], axis[0])
        lift = max(0.12, 0.5*max(rig.ann.asset_of(rig.ann.objects[name])["size"]))
        # clear of the surface; the staging move below raises it further
        for dz in (lift, 0.08, 0.05):
            try:
                skills.held_vertical_move(rig, dz, "upright_clear")
                break
            except SkillFailure:
                if rig.held is None or rig.held["name"] != name:
                    raise
        else:
            raise SkillFailure(f"upright {name}: cannot lift it clear of the surface")
        tcp, R_now = rig.kin.tcp(rig.q_cmd)
        x, y, byaw = rig.base_pose()
        cb, sb = math.cos(math.radians(byaw)), math.sin(math.radians(byaw))
        toward = np.array([x, y]) - tcp[:2]
        toward /= max(1e-9, np.linalg.norm(toward))
        # stage points: around the current hand (pulled in / raised), then a
        # grid in front of the chest where the wrist has the most range
        stages = [tcp + np.r_[toward * pull, up] for pull in (0.0, 0.08, 0.15, 0.22) for up in (0.0, 0.08, 0.15)]
        stages += [np.array([x + cb * fx - sb * ly, y + sb * fx + cb * ly, z])
                   for fx in (0.45, 0.38, 0.52, 0.32) for ly in (-0.15, -0.05, -0.25, 0.05, 0.15)
                   for z in (1.0, 1.1, 0.92, 1.2)]
        half_len = 0.5 * float(max(rig.ann.asset_of(rig.ann.objects[name])["size"]))

        def over_surface(pt):
            # the upright object hangs half its length below the hand
            for sup in rig.ann.supports:
                x0, y0, x1, y1 = sup["aabb_xy"]
                if x0 - 0.05 <= pt[0] <= x1 + 0.05 and y0 - 0.05 <= pt[1] <= y1 + 0.05 and \
                        pt[2] - half_len - 0.03 < sup["z"] < pt[2] + 0.1:
                    return True
            return False
        # and clear of the robot's own chest (a stage 4 cm in front of the base
        # centre knocked the bottle out of the pinch against the torso)
        stages = [p_ for p_ in stages if not over_surface(p_)
                  and (p_[0] - x) * cb + (p_[1] - y) * sb >= 0.25]
        # nearest to the hand first
        stages = sorted(stages, key=lambda p_: float(np.linalg.norm(p_ - tcp)))[:30]
        stage = None
        # the upright bottle's heading about the vertical is free
        # the hand may also turn the lying bottle about the vertical on the way
        # to the stage (the wrist facing the robot had almost no stage IK)
        combos_ = [(phi, dyaw) for phi in (0.0, 90.0, -90.0, 45.0, -45.0, 180.0)
                   for dyaw in (0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0)]
        q1_cache = {}
        cnt = {"q1": 0, "q1_far": 0, "qm": 0, "qd": 0}
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        for phi, dyaw in combos_:
            R_st = Rotation.from_euler("z", math.radians(phi)).as_matrix() @ R_now
            desired_body_R = Rotation.from_euler("z", yaw0 + math.radians(dyaw)).as_matrix()
            desired_tcp_R = desired_body_R @ body_R.T @ R_now
            rv = Rotation.from_matrix(desired_tcp_R @ R_st.T).as_rotvec()
            mid_R = Rotation.from_rotvec(0.5 * rv).as_matrix() @ R_st
            for ci, cand in enumerate(stages):
                if (phi, ci) not in q1_cache:
                    # locally from the current joints first (the global solver's
                    # first answer came from another branch, > 2 rad away)
                    ql, okl = rig.kin.ik(cand, R_st, rig.q_cmd)
                    if okl and not rig.kin.free(ql):
                        cnt["q1_coll"] = cnt.get("q1_coll", 0) + 1
                        okl = False
                    q1_cache[(phi, ci)] = (ql, True) if okl else rig.kin.ik_global(cand, R_st, seeds=[rig.q_cmd])
                q1, ok1 = q1_cache[(phi, ci)]
                if not ok1:
                    continue
                cnt["q1"] += 1
                # the pick can leave the arm on another IK branch than every
                # stage: a collision-checked slow joint move re-configures it
                if float(np.max(np.abs(np.asarray(q1) - rig.q_cmd))) > 3.5:
                    if cnt["q1_far"] == 0:
                        rig.log("upright_far_example", q_cmd=np.round(rig.q_cmd, 3).tolist(),
                                q1=np.round(np.asarray(q1), 3).tolist())
                    cnt["q1_far"] += 1
                    continue
                # a continuous wrist turn: each solution seeded from the last and
                # close to it (a straight Cartesian turn jumped IK branches and
                # flung the bottle 3 m)
                qm, okm = rig.kin.ik(cand, mid_R, q1)
                if not (okm and rig.kin.free(qm)):
                    qm, okm = rig.kin.ik_global(cand, mid_R, seeds=[q1])
                if not okm or float(np.max(np.abs(np.asarray(qm) - np.asarray(q1)))) > 1.2:
                    continue
                cnt["qm"] += 1
                qd, okd = rig.kin.ik(cand, desired_tcp_R, qm)
                if not (okd and rig.kin.free(qd)):
                    qd, okd = rig.kin.ik_global(cand, desired_tcp_R, seeds=[qm])
                cnt["qd"] += int(bool(okd))
                if okd and float(np.max(np.abs(np.asarray(qd) - np.asarray(qm)))) <= 1.2:
                    stage = cand
                    break
            if stage is not None:
                break
        if stage is None:
            rig.log("upright_stage_none", n_stages=len(stages), tcp=np.round(tcp, 3).tolist(), **cnt)
            raise SkillFailure(f"upright {name}: no staging pose allows the wrist turn")
        rig.log("upright_stage_choice", stage=np.round(stage, 3).tolist(), dyaw=dyaw, hand_yaw=phi)
        if np.linalg.norm(stage - tcp) > 1e-3:
            # slowly in joint space (a fast straight-line move threw the bottle)
            rig.sync_world()
            rig.follow(rig.joint_path(np.asarray(q1), "upright_stage"), steps_per_wp=16)
            skills.check_held(rig, "upright_stage")
        rig.follow(rig.joint_path_via([np.asarray(qm)]), steps_per_wp=8)
        skills.check_held(rig, "upright_rotate_half")
        rig.follow(rig.joint_path_via([np.asarray(qd)]), steps_per_wp=8)
        skills.check_held(rig, "upright_rotate")
        body, quat = rig.obj_pose(name)
        actual_R = quat_R(quat)
        actual = math.degrees(math.acos(np.clip(actual_R[2, 2], -1.0, 1.0)))
        # closed loop: the object turns a little in the pads during the turn;
        # turn the wrist on by the measured residual (17 deg were left once)
        for _ in range(2):
            if actual <= 0.6 * max_tilt_deg:
                break
            bz = actual_R[:, 2]
            ax = np.cross(bz, [0.0, 0.0, 1.0])
            if np.linalg.norm(ax) < 1e-6:
                break
            Rc = Rotation.from_rotvec(ax / np.linalg.norm(ax) * math.radians(actual)).as_matrix()
            tcp_c, R_c = rig.kin.tcp(rig.q_cmd)
            qc, okc = rig.kin.ik_global(tcp_c, Rc @ R_c, seeds=[rig.q_cmd])
            if not okc or float(np.max(np.abs(np.asarray(qc) - rig.q_cmd))) > 0.8:
                break
            rig.follow(rig.joint_path_via([np.asarray(qc)]), steps_per_wp=10)
            skills.check_held(rig, "upright_correct")
            rig.step(30)
            body, quat = rig.obj_pose(name)
            actual_R = quat_R(quat)
            actual = math.degrees(math.acos(np.clip(actual_R[2, 2], -1.0, 1.0)))
            rig.log("upright_correct", obj=name, tilt_deg=round(actual, 2))
        tcp, tcp_R = rig.kin.tcp(rig.q())
        rig.held["tcp_minus_body"] = tcp-body
        rig.held["R"] = tcp_R
        rig.log("upright_result", obj=name, before_deg=round(tilt, 3), tilt_deg=round(actual, 3))
        if actual > max_tilt_deg:
            raise SkillFailure(f"upright {name}: remaining tilt {actual:.1f} degrees")
        return actual

    def _hang_upright(self, name, max_tilt_deg):
        """A lying object turned upright in a mid pinch spins about the
        closing axis (only torsional pad friction resists).  Use that instead:
        set it down, pinch it across its diameter near the top end, and lift
        slowly; it swings down to hang vertically from the pinch."""
        from ..kinematics import gripper_rot
        from ..planner import find_park
        rig = self.rig
        st = rig.state()
        s = rig.geo.support_under(name, st)
        low = float(skills._lowest_z(rig, name, st))
        surface = float(s["z"]) if s is not None else low
        skills.held_vertical_move(rig, surface + 0.004 - low, "upright_set_down", step=0.003)
        rig.grip(rig.held.get("pre_open", 0.04), 60, gradual=True)
        rig.held = None
        t, R = rig.kin.tcp(rig.q_cmd)
        for d in (np.array([0, 0, 0.08]), np.array([0, 0, 0.04]), R[:, 2] * 0.06):
            try:
                rig.move_to(t + d, R, step=0.005, label="upright_release_clear", collision=False)
                break
            except SkillFailure as exc:
                rig.log("upright_release_clear_short", reason=str(exc))
        rig.step(60)
        _, quat = rig.obj_pose(name)
        body = np.asarray(rig.geo.centre(name, rig.state()), float)
        body_R = quat_R(quat)
        up = body_R[:, 2]
        size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
        h, radius = float(size[2]), 0.5 * float(min(size[:2]))
        axis = np.array([up[0], up[1], 0.0])
        axis /= max(1e-9, np.linalg.norm(axis))
        top = body + axis * (0.5 * h - 0.06)                # 6 cm in from the top end: below a tapered neck
        p = np.array([top[0], top[1], float(body[2]) + 0.25 * radius])
        close = np.cross([0.0, 0.0, 1.0], axis)               # across the diameter, horizontal
        R = gripper_rot([0.0, 0.0, -1.0], close)
        legs = [(p + np.array([0, 0, 0.10]), R), (p + np.array([0, 0, 0.03]), R), (p, R)]
        lift_h = 0.5 * h + 0.06
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        # the pivot arc (about the base end, wrist turning along) is part of the
        # base search: parked for the grasp alone, the arc lost IK at 40 deg
        pivot_pt = np.array([*(body - axis * (0.5 * h))[:2], float(rig.geo.bottom(name, rig.state())[2])])
        k_ax = np.cross(axis, [0.0, 0.0, 1.0])
        k_ax /= max(1e-9, np.linalg.norm(k_ax))
        arc = [(pivot_pt + Rotation.from_rotvec(k_ax * math.radians(d)).as_matrix() @ (p - pivot_pt),
                Rotation.from_rotvec(k_ax * math.radians(d)).as_matrix() @ R) for d in (45.0, 70.0, 90.0)]
        park = find_park(rig.kin, rig.world, legs + arc, near=rig.base_pose(),
                         max_tries=150, q_start=rig.q_cmd, travel_q=rig.kin.rest)
        if park is None:
            park = find_park(rig.kin, rig.world, legs + [(p + np.array([0, 0, lift_h]), R)], near=rig.base_pose(),
                             max_tries=150, q_start=rig.q_cmd, travel_q=rig.kin.rest)
        else:
            rig.log("upright_pivot_planned")
        if park is None:
            raise SkillFailure(f"upright {name}: no base pose reaches the top end")
        skills._goto_park(rig, park)
        rig.grip(min(0.04, radius + 0.015), 40)
        for (tp, tR), lab in zip(legs, ("upright_top_pre", "upright_top_in", "upright_top_grasp")):
            rig.move_to(tp, tR, step=0.004, steps_per_wp=4, label=lab, collision=False, smooth=True)
        rig.grip(0.0, 120, gradual=True)
        f_full = rig.fingers().copy()
        # pivot on the base end: the hand (firm grip) travels on an arc around
        # the base end with the wrist turning along, so the bottle rotates up
        # about its base and stands; the hang swing alone was held back by the
        # pads' friction about the closing axis
        base_end = body - axis * (0.5 * h)
        pivot = np.array([base_end[0], base_end[1], float(rig.geo.bottom(name, rig.state())[2])])
        k = np.cross(axis, [0.0, 0.0, 1.0])            # rotation axis: top end rises
        k /= max(1e-9, np.linalg.norm(k))
        tcp0, R0 = rig.kin.tcp(rig.q_cmd)
        v0 = tcp0 - pivot
        reached = 0.0
        for deg in np.arange(10.0, 91.0, 10.0):
            Rot = Rotation.from_rotvec(k * math.radians(deg)).as_matrix()
            try:
                rig.move_to(pivot + Rot @ v0, Rot @ R0, step=0.004, steps_per_wp=4, label="upright_pivot",
                            collision=False, smooth=True)
            except SkillFailure as exc:
                rig.log("upright_pivot_limit", deg=float(deg), reason=str(exc))
                break
            reached = float(deg)
            if rig.fingers().sum() < 0.004:
                raise SkillFailure(f"upright {name}: lost the grip while pivoting")
        if reached >= 80.0:
            rig.step(60)
            rig.grip(0.04, 60, gradual=True)
            t, Rn = rig.kin.tcp(rig.q_cmd)
            for d in (0.06, 0.03):
                try:
                    rig.move_to(t + Rn[:, 2] * d, Rn, step=0.004, label="upright_pivot_out", collision=False)
                    break
                except SkillFailure:
                    continue
            rig.step(120)
            tilt = math.degrees(math.acos(np.clip(quat_R(rig.obj_pose(name)[1])[2, 2], -1.0, 1.0)))
            rig.log("upright_pivot_result", obj=name, arc_deg=reached, tilt_deg=round(tilt, 2))
            if tilt > max_tilt_deg:
                raise SkillFailure(f"upright {name}: stands at {tilt:.0f} deg after the pivot")
            # stood up in place: pick it again so the path's place step can run
            from .. import skills as _sk
            _sk.pick(rig, name)
            return tilt
        rig.log("upright_pivot_short", arc_deg=reached)
        # slow lift with a light grip (fingers 1.5 mm inside the measured contact):
        # enough to carry, little torsional friction, so the object swings under the pinch
        light = max(0.0, float(f_full.mean()) - 0.0015)
        rig.grip(light, 40)
        for k in range(1, 7):
            rig.move_to(p + np.array([0, 0, lift_h * k / 6]), R, step=0.003, steps_per_wp=6,
                        label="upright_hang_lift", collision=False, smooth=True)
            rig.step(30)
        rig.step(150)
        rig.grip(0.0, 80, gradual=True)               # clamp again once it hangs
        f = rig.fingers()
        body, quat = rig.obj_pose(name)
        tilt = math.degrees(math.acos(np.clip(quat_R(quat)[2, 2], -1.0, 1.0)))
        rig.log("upright_hang", obj=name, tilt_deg=round(tilt, 2), fingers=f.round(4).tolist())
        if f.min() < 0.003:
            raise SkillFailure(f"upright {name}: lost the top-end pinch")
        tcp, tcp_R = rig.kin.tcp(rig.q())
        rig.held = {"name": name, "kind": "pinch", "tcp_minus_body": tcp - body, "R": tcp_R, "pre_open": 0.04}
        if min(tilt, 180.0 - tilt) > max_tilt_deg:
            raise SkillFailure(f"upright {name}: hangs at {tilt:.0f} deg after the lift")
        if tilt > 90.0:
            raise SkillFailure(f"upright {name}: hangs upside down (pinched at the bottom end)")
        return tilt
