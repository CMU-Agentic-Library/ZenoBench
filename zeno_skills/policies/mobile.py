"""Synchronized base and right-arm actions.

The base anchor and right-arm drive targets are updated in the same physics
step.  A measured TCP and base pose are checked after the motion.  These
policies never substitute a stop-then-reach sequence for concurrent motion.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from .base import AtomicPolicy
from ..kinematics import vel_limits
from ..planner import plan_path
from ..rig import SkillFailure


def _rotation(yaw_deg):
    return Rotation.from_euler("z", math.radians(yaw_deg)).as_matrix()


def _path(rig, base_path):
    rig.sync_world()
    if len(base_path) == 3 and np.isscalar(base_path[0]):
        path = plan_path(rig.world, rig.base_pose(), tuple(float(v) for v in base_path))
        if path is None:
            raise SkillFailure(f"synchronized motion: no base path to {base_path}")
    else:
        path = [tuple(float(v) for v in pose) for pose in base_path]
    if not path:
        raise ValueError("synchronized motion needs a nonempty base path")
    start = rig.base_pose()
    last = start
    moved = 0.0
    for pose in path:
        if len(pose) != 3:
            raise ValueError("base path waypoints must be (x, y, yaw_deg)")
        distance = math.hypot(pose[0]-last[0], pose[1]-last[1])
        moved += distance + 0.2*abs(math.radians(pose[2]-last[2]))
        for u in np.linspace(0, 1, max(2, math.ceil(distance/0.03)+1)):
            x = last[0]+u*(pose[0]-last[0])
            y = last[1]+u*(pose[1]-last[1])
            yaw = last[2]+u*(pose[2]-last[2])
            if not rig.world.footprint_clear(x, y, math.radians(yaw)):
                raise SkillFailure("synchronized motion: base path crosses an obstacle")
        last = pose
    if moved < 0.04:
        raise ValueError("synchronized motion needs at least 4 cm of base movement")
    return path


class ReachWhileMovingPolicy(AtomicPolicy):
    """Reach a world-frame TCP pose while the base follows a collision-free path."""

    def execute(self, position, rotation, base_path, *, speed=0.08, tolerance=0.04):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("reach while moving: right hand must be empty")
        target = np.asarray(position, float)
        R_goal = np.asarray(rotation, float)
        if target.shape != (3,) or R_goal.shape != (3, 3) or not np.isfinite(target).all():
            raise ValueError("reach target must be a 3D position and 3x3 rotation")
        path = _path(rig, base_path)
        rig.sync_world()
        bx, by, yaw = rig.base_pose()
        start_tcp, start_R = rig.kin.tcp(rig.q_cmd)
        local = _rotation(yaw).T @ (start_tcp-np.array([bx, by, 0.0]))
        last_update = rig.tick
        arm_travel = 0.0
        updates = 0
        max_vel = 0.6*vel_limits(rig.kin.names)

        def update(progress, pose):
            nonlocal last_update, arm_travel, updates
            if rig.tick-last_update < 12 and progress < 0.999:
                return
            dt = max(1, rig.tick-last_update)/120.0
            last_update = rig.tick
            x, y, a = pose
            R_base = _rotation(a)
            p_follow = np.array([x, y, 0.0])+R_base @ local
            R_follow = _rotation(a-yaw) @ start_R
            alpha = min(1.0, max(0.0, (progress-0.10)/0.85))
            alpha = alpha*alpha*(3-2*alpha)
            p_des = (1-alpha)*p_follow+alpha*target
            delta = Rotation.from_matrix(R_goal @ R_follow.T).as_rotvec()
            R_des = Rotation.from_rotvec(alpha*delta).as_matrix() @ R_follow
            q, ok = rig.kin.ik(p_des, R_des, rig.q_cmd, iters=90)
            if not ok:
                q, ok = rig.kin.ik_global(p_des, R_des, seeds=[rig.q_cmd])
            if not ok:
                rig.log("reach_while_moving_ik_failed", progress=round(progress, 3),
                        desired_tcp=p_des.round(3).tolist(), base_pose=list(pose))
                raise SkillFailure(f"reach while moving: IK lost at progress {progress:.2f}")
            step = np.clip(q-rig.q_cmd, -max_vel*dt, max_vel*dt)
            command = rig.q_cmd+step
            if not rig.kin.free(command):
                raise SkillFailure(f"reach while moving: arm collision at progress {progress:.2f}")
            arm_travel += float(np.max(np.abs(step[2:])))
            rig.q_cmd = command
            updates += 1

        rig.drive_base(path, speed=speed, turn=0.35, ramp=0.4, on_step=update)
        tcp, R = rig.kin.tcp(rig.q())
        err = float(np.linalg.norm(tcp-target))
        rot_err = float(np.linalg.norm(Rotation.from_matrix(R_goal @ R.T).as_rotvec()))
        rig.log("reach_while_moving_result", tcp_err_m=round(err, 4), rot_err_rad=round(rot_err, 4),
                arm_travel_rad=round(arm_travel, 4), updates=updates)
        if updates < 2 or arm_travel < 0.02 or err > tolerance or rot_err > 0.15:
            raise SkillFailure(f"reach while moving: TCP error {err:.3f} m, orientation error {rot_err:.3f} rad")
        return err


def _track_tcp(rig, position, rotation, dt):
    """One bounded arm update while the base anchor continues to move."""
    q, ok = rig.kin.ik(np.asarray(position, float), rotation, rig.q_cmd, iters=90)
    if not ok:
        q, ok = rig.kin.ik_global(np.asarray(position, float), rotation, seeds=[rig.q_cmd])
    if not ok:
        raise SkillFailure("moving contact: no arm IK at current base pose")
    max_step = 0.6*vel_limits(rig.kin.names)*dt
    next_q = rig.q_cmd+np.clip(q-rig.q_cmd, -max_step, max_step)
    if not rig.kin.free(next_q):
        raise SkillFailure("moving contact: arm path intersects scene")
    rig.q_cmd = next_q


class PickWhileMovingPolicy(AtomicPolicy):
    """Close on an annotated grasp and lift while the base is still driving."""

    def execute(self, name, base_path, *, speed=0.02):
        rig = self.rig
        if rig.held is not None or rig.left_held is not None:
            raise SkillFailure("pick while moving: both hands must be empty")
        if name not in rig.ann.objects:
            raise SkillFailure(f"pick while moving: unknown object {name}")
        path = _path(rig, base_path)
        obj = rig.ann.objects[name]
        p0, quat = rig.obj_pose(name)
        grasps = [g for g in rig.ann.grasp_poses(obj, p0, quat)
                  if g["kind"] in ("top_pinch", "rim_pinch", "rim_pinch_rect")]
        if not grasps:
            raise SkillFailure(f"pick while moving: {name} has no supported pinch annotation")
        rig.sync_world()
        grasp = None
        for g in grasps:
            pre = g["p"]+0.08*g["R"][:, 2]+np.array([0, 0, 0.04])
            q, ok = rig.kin.ik_global(pre, g["R"], seeds=[rig.q_cmd])
            if ok:
                grasp = g
                break
        if grasp is None:
            raise SkillFailure("pick while moving: no pregrasp from current base pose")
        R = grasp["R"]
        contact = grasp["p"]
        pre = contact+0.08*R[:, 2]+np.array([0, 0, 0.04])
        rig.grip(grasp["pre_open"], 30)
        rig.move_to(pre, R, label="moving_pick_pre")
        state = {"last": rig.tick, "closed": False, "arm_updates": 0,
                 "close_tick": None, "lift_tick": None}
        old_coll_kw = rig.kin.coll_kw
        rig.kin.coll_kw = {"ignore_fingers": True}

        def update(progress, _pose):
            if progress < 0.4:
                target = pre+(contact-pre)*min(1.0, progress/0.35)
            elif progress < 0.65:
                target = contact
            else:
                target = contact+np.array([0, 0, 0.07*min(1.0, (progress-0.65)/0.3)])
            if rig.tick-state["last"] >= 6 or progress >= 0.999:
                dt = max(1, rig.tick-state["last"])/120.0
                state["last"] = rig.tick
                _track_tcp(rig, target, R, dt)
                state["arm_updates"] += 1
            if progress >= 0.43 and not state["closed"]:
                tcp, _ = rig.kin.tcp(rig.q())
                contact_error = float(np.linalg.norm(tcp-contact))
                if contact_error > 0.025:
                    rig.log("moving_pick_contact_miss", progress=round(progress, 3),
                            tcp_err_m=round(contact_error, 4))
                    raise SkillFailure("pick while moving: TCP missed contact before closure")
                rig.grip_cmd = 0.0
                state["closed"] = True
                state["close_tick"] = rig.tick
            if progress >= 0.7 and state["lift_tick"] is None:
                state["lift_tick"] = rig.tick

        try:
            rig.drive_base(path, speed=speed, turn=0.25, ramp=0.3, on_step=update)
        finally:
            rig.kin.coll_kw = old_coll_kw
        p1, _ = rig.obj_pose(name)
        fingers = rig.fingers()
        if not state["closed"] or state["lift_tick"] is None or p1[2]-p0[2] < 0.015 or fingers.min() < 0.003:
            raise SkillFailure("pick while moving: measured two-finger lift failed")
        tcp, measured_R = rig.kin.tcp(rig.q())
        rig.held = {"name": name, "kind": "pinch", "tcp_minus_body": tcp-p1,
                    "R": measured_R, "pre_open": grasp["pre_open"]}
        rig.log("pick_while_moving_result", obj=name, lift_m=round(float(p1[2]-p0[2]), 4),
                close_tick=state["close_tick"], lift_tick=state["lift_tick"],
                base_end_tick=rig.tick-20, arm_updates=state["arm_updates"])
        return p1[2]-p0[2]


class PlaceWhileMovingPolicy(AtomicPolicy):
    """Lower and release a right-held item on a support during base travel."""

    def execute(self, name, support, base_path, *, xy=None, speed=0.02):
        rig = self.rig
        held = rig.held
        if held is None or held["name"] != name or held["kind"] != "pinch":
            raise SkillFailure(f"place while moving: right hand must pinch {name}")
        from ..skills import check_held, free_spots
        s = rig.ann.support(support)
        if s.get("furniture") == "kitchen_microwave":
            raise SkillFailure("place while moving: narrow appliance cavity requires static insertion")
        path = _path(rig, base_path)
        if xy is None:
            spots = free_spots(rig, name, support)
            if not spots:
                raise SkillFailure(f"place while moving: no free location on {support}")
            xy = spots[0]
        asset = rig.ann.asset_of(rig.ann.objects[name])
        body = np.array([xy[0], xy[1], s["z"]-asset["origin_to_bottom_center"][2]+0.012])
        target = body+held["tcp_minus_body"]
        pre = target+np.array([0, 0, 0.08])
        R = held["R"]
        rig.move_to(pre, R, label="moving_place_pre")
        check_held(rig, "moving_place_pre")
        state = {"last": rig.tick, "released": False, "release_tick": None,
                 "arm_updates": 0}
        old_coll_kw = rig.kin.coll_kw
        rig.kin.coll_kw = {"ignore_fingers": True}

        def update(progress, _pose):
            if progress < 0.55:
                target_now = pre+(target-pre)*min(1.0, progress/0.5)
            elif progress < 0.7:
                target_now = target
            else:
                target_now = target+np.array([0, 0, 0.10*min(1.0, (progress-0.7)/0.25)])
            if rig.tick-state["last"] >= 6 or progress >= 0.999:
                dt = max(1, rig.tick-state["last"])/120.0
                state["last"] = rig.tick
                _track_tcp(rig, target_now, R, dt)
                state["arm_updates"] += 1
            if progress >= 0.58 and not state["released"]:
                tcp, _ = rig.kin.tcp(rig.q())
                if np.linalg.norm(tcp-target) > 0.025:
                    raise SkillFailure("place while moving: TCP missed release pose")
                rig.grip_cmd = held["pre_open"]
                state["released"] = True
                state["release_tick"] = rig.tick
                rig.held = None

        try:
            rig.drive_base(path, speed=speed, turn=0.25, ramp=0.3, on_step=update)
        finally:
            rig.kin.coll_kw = old_coll_kw
        rig.step(50)
        p, _ = rig.obj_pose(name)
        bottom = rig.geo.bottom(name, rig.state())
        x0, y0, x1, y1 = s["aabb_xy"]
        placed = (state["released"] and rig.fingers().min() > 0.02 and
                  x0 < p[0] < x1 and y0 < p[1] < y1 and
                  abs(bottom[2]-s["z"]) < 0.06)
        rig.log("place_while_moving_result", obj=name, support=support,
                release_tick=state["release_tick"], base_end_tick=rig.tick-70,
                bottom_error_m=round(float(bottom[2]-s["z"]), 4), placed=bool(placed))
        if not placed:
            raise SkillFailure(f"place while moving: {name} did not settle on {support}")
        return tuple(float(v) for v in p)
