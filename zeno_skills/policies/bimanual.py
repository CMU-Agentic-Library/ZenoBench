"""Two-hand grasps built on independent arm IK and paired joint control."""

from __future__ import annotations

import math
import time
from contextlib import contextmanager

import numpy as np

from .base import AtomicPolicy
from .embedded import SlideToEdgePolicy
from .. import skills
from ..kinematics import gripper_rot
from ..planner import plan_path
from ..rig import SkillFailure, Dropped


@contextmanager
def _lock_shared_posture(rig):
    """Keep both 7-DOF solves on the same physically commanded torso pose."""
    saved = [(kin, kin.lo.copy(), kin.hi.copy()) for kin in (rig.kin, rig.left_kin)]
    posture = rig.q_cmd[:2].copy()
    try:
        for kin, _, _ in saved:
            kin.lo[:2] = kin.hi[:2] = posture
        yield
    finally:
        for kin, lo, hi in saved:
            kin.lo[:], kin.hi[:] = lo, hi


def _fixed_torso_ik(kin, position, rotation, current):
    """Solve the seven arm joints without asking the two arms to move the torso differently."""
    lo, hi = kin.lo.copy(), kin.hi.copy()
    try:
        kin.lo[:2] = kin.hi[:2] = current[:2]
        q, ok = kin.ik_global(np.asarray(position, float), rotation, seeds=[current])
        return q if ok else None
    finally:
        kin.lo[:], kin.hi[:] = lo, hi


def check_bimanual_hold(rig, name, label):
    right, left = rig.held, rig.left_held
    if right is None or left is None or right["name"] != name or left["name"] != name:
        raise SkillFailure(f"{label}: {name} is not recorded in both hands")
    body, _ = rig.obj_pose(name)
    for side, held, kin, q, fingers in (
        ("right", right, rig.kin, rig.q(), rig.fingers()),
        ("left", left, rig.left_kin, rig.left_q(), rig.left_fingers()),
    ):
        tcp, _ = kin.tcp(q)
        slip = abs(np.linalg.norm(tcp-body)-np.linalg.norm(held["tcp_minus_body"]))
        if slip > 0.06 or fingers.min() < 0.002:
            rig.log("bimanual_slip", side=side, obj=name, slip_m=round(float(slip), 4),
                    fingers=fingers.tolist())
            raise SkillFailure(f"{label}: {side} grasp slipped from {name}")


def _two_grasps(rig, name, flat):
    obj = rig.ann.objects[name]
    asset = rig.ann.asset_of(obj)
    pos, quat = rig.obj_pose(name)
    if not flat:
        if max(asset["size"][:2]) < 0.22:
            raise SkillFailure("bimanual box lift: object is too narrow for two grippers")
        candidates = [g for g in rig.ann.grasp_poses(obj, pos, quat)
                      if g["kind"] == "rim_pinch_rect"]
        groups = {}
        for a in candidates:
            for b in candidates:
                gap = np.linalg.norm(a["p"][:2]-b["p"][:2])
                if gap <= 0.18:
                    continue
                # Group by the two physical contact locations. Repeated tilt
                # variants must not hide the other rim edges in the search.
                key = tuple(sorted((tuple(np.round(a["p"], 3)),
                                    tuple(np.round(b["p"], 3)))))
                groups.setdefault(key, []).append((a, b))
        if not groups:
            raise SkillFailure(f"bimanual box lift: {name} has no two separated rim contacts")
        ordered = sorted(groups.values(),
                         key=lambda group: -np.linalg.norm(group[0][0]["p"]-group[0][1]["p"]))
        pairs = []
        for tilt_index in range(max(map(len, ordered))):
            pairs.extend(group[tilt_index] for group in ordered if tilt_index < len(group))
        return pairs
    support = rig.geo.support_under(name, rig.state())
    if support is None:
        raise SkillFailure(f"bimanual flat pick: {name} has no annotated support")
    size = np.asarray(asset["size"], float)
    if max(size[:2]) < 0.18 or size[2] > 0.09:
        raise SkillFailure(f"bimanual flat pick: {name} is not a wide flat object")
    yaw = skills._yaw(quat)
    bottom = rig.geo.bottom(name, rig.state())
    result = []
    for direction in skills._open_edges(rig, support):
        half = skills._half_along(size, yaw, direction)
        overhang = float(direction @ bottom[:2])+half-skills._edge_coord(support, direction)
        if overhang < skills.EDGE_MIN_OVERHANG-0.01:
            continue
        tangent = np.array([-direction[1], direction[0]])
        length = skills._half_along(size, yaw, tangent)
        if length < 0.09:
            continue
        R = gripper_rot(np.r_[-direction, 0.0], [0, 0, 1])
        tilt = math.radians(30)
        tilted_R = gripper_rot(np.r_[-direction, 0.0],
                               np.r_[-math.sin(tilt)*tangent, math.cos(tilt)])
        centre = bottom+np.r_[direction*(half-0.025), size[2]/2]
        left_offset = min(length-0.01, max(0.071, length*0.70))
        right_offset = min(length-0.018, max(0.07, length*0.75))
        left_p = centre-np.r_[tangent*left_offset+direction*0.003, 0.0]
        right_p = centre+np.r_[tangent*right_offset, 0.0]
        pair = []
        for p, grasp_R in ((left_p, tilted_R), (right_p, R)):
            p = p + np.r_[direction*0.01, 0.0]
            pair.append({"p": p, "R": grasp_R, "pre_open": 0.04,
                         "pre": p+np.r_[direction*0.10, 0.0]})
        result.append(tuple(pair))
    if not result:
        raise SkillFailure(f"bimanual flat pick: {name} needs a safe overhanging edge")
    return result


def _park_for_pair(rig, pair, origin, torso_target=None, deadline=None):
    """Find one base pose from which both arms reach their separate contacts."""
    centre = 0.5*(pair[0]["p"][:2]+pair[1]["p"][:2])
    bx, by, _ = origin
    base_angles = [math.atan2(by-centre[1], bx-centre[0])]
    base_angles += [a for a in np.linspace(-math.pi, math.pi, 12, endpoint=False)]
    # Sample each direction at a useful reach before refining nearby radii;
    # the shared-pose search must remain bounded for a graph-level planner.
    for radius in (0.38, 0.48, 0.58, 0.68):
        for ang in base_angles:
            x, y = centre+radius*np.array([math.cos(ang), math.sin(ang)])
            face = math.degrees(math.atan2(centre[1]-y, centre[0]-x))
            for yaw in (face, face-20, face+20):
                if deadline is not None and time.monotonic() >= deadline:
                    return None
                if not rig.world.footprint_clear(x, y, math.radians(yaw)):
                    continue
                rig.kin.set_base((x, y, 0), math.radians(yaw))
                rig.left_kin.set_base((x, y, 0), math.radians(yaw))
                for right, left in (pair, pair[::-1]):
                    rg = right.get("pre", right["p"]+np.array([0, 0, 0.08]))
                    lg = left.get("pre", left["p"]+np.array([0, 0, 0.08]))
                    right_seed = rig.q_cmd.copy()
                    left_seed = np.r_[rig.q_cmd[:2], rig.left_q_cmd]
                    if torso_target is not None:
                        right_seed[:2] = [torso_target, 0.0]
                        left_seed[:2] = [torso_target, 0.0]
                    qr = _fixed_torso_ik(rig.kin, rg, right["R"], right_seed)
                    if qr is None:
                        continue
                    ql = _fixed_torso_ik(rig.left_kin, lg, left["R"], left_seed)
                    if ql is None:
                        continue
                    old_r, old_l = rig.world.right_q, rig.world.left_q
                    try:
                        rig.world.right_q, rig.world.left_q = qr, ql
                        good = rig.kin.free(qr) and rig.left_kin.free(ql)
                        for r_target, l_target in ((right["p"], left["p"]),
                                                   (right["p"]+np.array([0, 0, 0.04]),
                                                    left["p"]+np.array([0, 0, 0.04]))):
                            if not good:
                                break
                            next_r = _fixed_torso_ik(rig.kin, r_target, right["R"], qr)
                            if next_r is None:
                                good = False
                                break
                            rig.world.right_q = next_r
                            next_l = _fixed_torso_ik(rig.left_kin, l_target, left["R"], ql)
                            if next_l is None:
                                good = False
                                break
                            rig.world.left_q = next_l
                            good = rig.kin.free(next_r) and rig.left_kin.free(next_l)
                            qr, ql = next_r, next_l
                    finally:
                        rig.world.right_q, rig.world.left_q = old_r, old_l
                    if good:
                        return (float(x), float(y), float(yaw)), right, left
    return None


def _lift_together(rig, right_p, right_R, left_p, left_R, height):
    qr = _fixed_torso_ik(rig.kin, right_p+np.array([0, 0, height]), right_R, rig.q_cmd)
    ql = _fixed_torso_ik(rig.left_kin, left_p+np.array([0, 0, height]), left_R,
                         np.r_[rig.q_cmd[:2], rig.left_q_cmd])
    if qr is None or ql is None:
        raise SkillFailure("bimanual lift: no paired IK for lift height")
    rig.follow_both(qr, ql, label="bimanual_lift")


def _grasp_both(rig, name, pairs, label):
    if rig.held is not None or rig.left_held is not None:
        raise SkillFailure(f"{label}: both hands must be empty")
    rig.sync_world()
    rig.world.left_active = True
    park = None
    lowest_contact = min(float(g["p"][2]) for pair in pairs for g in pair)
    torso_target = -0.15 if label == "bimanual_flat_pick" or lowest_contact < 0.55 else None
    deadline = time.monotonic() + 45.0
    for pair in pairs[:8]:
        if time.monotonic() >= deadline:
            break
        park = _park_for_pair(rig, pair, rig.base_pose(), torso_target=torso_target,
                              deadline=deadline)
        if park is not None:
            break
    if park is None:
        rig.sync_world()
        rig.log("bimanual_no_park", obj=name, search_budget_s=45,
                contacts=[[g["p"].round(3).tolist() for g in pair] for pair in pairs[:3]])
        raise SkillFailure(f"{label}: no collision-free shared base pose")
    pose, right, left = park
    rig.sync_world()
    skills.navigate(rig, pose, label=label+"_park")
    if torso_target is not None:
        from .posture import SetTorsoHeightPolicy, SetWaistPitchPolicy
        SetTorsoHeightPolicy(rig).execute(torso_target)
        SetWaistPitchPolicy(rig).execute(0.0)
    rig.sync_world()
    p0, _ = rig.obj_pose(name)
    rig.log("bimanual_grasp_targets", obj=name, body=p0.round(4).tolist(),
            right=right["p"].round(4).tolist(), left=left["p"].round(4).tolist())
    right_open = rig.grip(right["pre_open"], 120)
    rig.log("bimanual_right_open", obj=name, fingers=right_open.round(4).tolist(),
            tcp=rig.kin.tcp(rig.q())[0].round(4).tolist())
    if right_open.min() < right["pre_open"]-0.008:
        raise SkillFailure(f"{label}: right fingers could not open at shared stance")
    rig.left_grip(left["pre_open"], 60)
    rp = right.get("pre", right["p"]+np.array([0, 0, 0.08]))
    lp = left.get("pre", left["p"]+np.array([0, 0, 0.08]))
    with _lock_shared_posture(rig):
        rig.move_to(rp, right["R"], label=label+"_right_pre")
        rig.move_left_to(lp, left["R"], label=label+"_left_pre")
        right_q = _fixed_torso_ik(rig.kin, right["p"], right["R"], rig.q_cmd)
        left_q = _fixed_torso_ik(rig.left_kin, left["p"], left["R"],
                                 np.r_[rig.q_cmd[:2], rig.left_q_cmd])
        if right_q is None or left_q is None:
            raise SkillFailure(f"{label}: paired contact IK changed after parking")
        rig.follow_both(right_q, left_q, label=label+"_paired_contact")
        body_contact, _ = rig.obj_pose(name)
        rig.log("bimanual_before_close", obj=name, body=body_contact.round(4).tolist(),
                right_tcp=rig.kin.tcp(rig.q())[0].round(4).tolist(),
                left_tcp=rig.left_kin.tcp(rig.left_q())[0].round(4).tolist())
        rig.grip_cmd = rig.left_grip_cmd = 0.0
        rig.step(120)
        rig.log("bimanual_contact_posture", torso=rig.q_cmd[:2].round(4).tolist(),
                right_q=rig.q_cmd.round(3).tolist(),
                left_q=np.r_[rig.q_cmd[:2], rig.left_q_cmd].round(3).tolist())
        _lift_together(rig, right["p"], right["R"], left["p"], left["R"], 0.04)
    rig.step(120)  # prove both fingers keep contact after the object has settled
    p1, _ = rig.obj_pose(name)
    rf, lf = rig.fingers(), rig.left_fingers()
    rig.log("bimanual_lift_check", obj=name, lift_m=round(float(p1[2]-p0[2]), 4),
            right_fingers=rf.round(4).tolist(), left_fingers=lf.round(4).tolist())
    if p1[2]-p0[2] < 0.025 or rf.min() < 0.004 or lf.min() < 0.004:
        raise SkillFailure(f"{label}: two-hand lift/contact check failed")
    rtcp, rR = rig.kin.tcp(rig.q())
    ltcp, lR = rig.left_kin.tcp(rig.left_q())
    rig.held = {"name": name, "kind": "bimanual", "tcp_minus_body": rtcp-p1,
                "R": rR, "pre_open": right["pre_open"]}
    rig.left_held = {"name": name, "tcp_minus_body": ltcp-p1,
                     "R": lR, "pre_open": left["pre_open"]}
    check_bimanual_hold(rig, name, label)
    rig.log(label+"_result", obj=name, lift_m=round(float(p1[2]-p0[2]), 4),
            right_fingers=rf.tolist(), left_fingers=lf.tolist())
    return p1[2]-p0[2]


class BimanualFlatPickPolicy(AtomicPolicy):
    """Slide a wide flat object to a free edge and lift it with two contacts."""

    def execute(self, name):
        rig = self.rig
        try:
            pairs = _two_grasps(rig, name, flat=True)
        except SkillFailure as exc:
            if "overhanging edge" not in str(exc):
                raise
            SlideToEdgePolicy(rig).execute(name)
            pairs = _two_grasps(rig, name, flat=True)
        return _grasp_both(rig, name, pairs, "bimanual_flat_pick")


class BimanualBoxLiftPolicy(AtomicPolicy):
    """Lift a wide box/container by two separately verified rim pinches."""

    def execute(self, name):
        return _grasp_both(self.rig, name, _two_grasps(self.rig, name, flat=False),
                           "bimanual_box_lift")


class BimanualCarryPolicy(AtomicPolicy):
    """Drive the base while maintaining and checking both object contacts."""

    def execute(self, name, pose):
        rig = self.rig
        check_bimanual_hold(rig, name, "bimanual_carry_start")
        rig.sync_world()
        path = plan_path(rig.world, rig.base_pose(), pose, margin=0.18)
        if path is None:
            raise SkillFailure(f"bimanual carry: no base path to {pose}")
        counter = 0
        def check_step(_progress, _pose):
            nonlocal counter
            counter += 1
            if counter % 60 == 0:
                check_bimanual_hold(rig, name, "bimanual_carry")
        rig.drive_base(path, speed=0.12, turn=0.25, ramp=1.2, on_step=check_step)
        check_bimanual_hold(rig, name, "bimanual_carry_end")
        x, y, yaw = rig.base_pose()
        error = math.hypot(x-pose[0], y-pose[1])
        if error > 0.05 or abs((yaw-pose[2]+180)%360-180) > 3:
            raise SkillFailure(f"bimanual carry: base missed target by {error:.3f} m")
        return (x, y, yaw)


class HandoverRightToLeftPolicy(AtomicPolicy):
    """Transfer a right-held object to the left gripper and prove it stays there."""

    def execute(self, name):
        rig = self.rig
        if rig.held is None or rig.held["name"] != name or rig.left_held is not None:
            raise SkillFailure(f"handover: right must hold {name} and left must be empty")
        obj = rig.ann.objects[name]
        rig.sync_world()
        rig.world.left_active = True

        def left_contact():
            body, quat = rig.obj_pose(name)
            right_tcp, _ = rig.kin.tcp(rig.q())
            grasps = rig.ann.grasp_poses(obj, body, quat)
            grasps.sort(key=lambda candidate: -np.linalg.norm(candidate["p"]-right_tcp))
            counts = {"too_close": 0, "pre_ik": 0, "contact_ik": 0}
            for candidate in grasps:
                if np.linalg.norm(candidate["p"]-right_tcp) < 0.12:
                    counts["too_close"] += 1
                    continue
                pre = candidate["p"]+0.10*candidate["R"][:, 2]
                ql = _fixed_torso_ik(rig.left_kin, pre, candidate["R"], rig.left_q())
                if ql is None:
                    counts["pre_ik"] += 1
                    continue
                old_left = rig.world.left_q
                try:
                    rig.world.left_q = ql
                    qcontact = _fixed_torso_ik(rig.left_kin, candidate["p"],
                                                candidate["R"], ql)
                    if qcontact is not None:
                        return candidate, pre
                    counts["contact_ik"] += 1
                finally:
                    rig.world.left_q = old_left
            rig.log("handover_left_search", obj=name, body=body.round(3).tolist(),
                    right_tcp=right_tcp.round(3).tolist(), candidates=len(grasps), **counts)
            return None

        found = left_contact()
        if found is None:
            # Present the held object in the shared workspace, clear of the
            # shelf where it was picked. Both poses are IK-checked before any
            # move, then the object is remeasured after moving the right arm.
            p, _ = rig.obj_pose(name)
            right_tcp, right_R = rig.kin.tcp(rig.q())
            bx, by, yaw = rig.base_pose()
            c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            for forward, left, height in ((0.38, 0.0, 0.90), (0.45, 0.0, 0.95),
                                          (0.40, 0.10, 0.95), (0.50, 0.10, 0.85)):
                body_goal = np.array([bx+c*forward-sn*left,
                                      by+sn*forward+c*left, height])
                tcp_goal = right_tcp+body_goal-p
                qr = _fixed_torso_ik(rig.kin, tcp_goal, right_R, rig.q_cmd)
                if qr is None:
                    continue
                try:
                    rig.move_to(tcp_goal, right_R, label="handover_present",
                                q_hint=qr)
                    skills.check_held(rig, "handover_present")
                except Dropped:
                    raise
                except SkillFailure:
                    if rig.held is None or rig.held["name"] != name:
                        raise
                    continue
                rig.sync_world()
                rig.world.left_active = True
                found = left_contact()
                if found is not None:
                    break
        if found is None:
            raise SkillFailure(f"handover: no independent left contact on {name}")
        g, pre = found
        rig.log("handover_left_target", obj=name, contact=g["p"].round(3).tolist(),
                pre=pre.round(3).tolist())
        rig.left_grip(g["pre_open"], 30)
        rig.move_left_to(pre, g["R"], label="handover_left_pre")
        rig.move_left_to(g["p"], g["R"], label="handover_left_contact")
        fingers = rig.left_grip(0.0, 120)
        if fingers.min() < 0.003:
            raise SkillFailure("handover: left fingers did not contact object")
        before, _ = rig.obj_pose(name)
        ltcp, lR = rig.left_kin.tcp(rig.left_q())
        rig.left_held = {"name": name, "tcp_minus_body": ltcp-before,
                         "R": lR, "pre_open": g["pre_open"]}
        rig.grip(rig.held["pre_open"], 70)
        rig.held = None
        rig.move_left_to(ltcp+np.array([0, 0, 0.05]), lR, label="handover_left_lift")
        after, _ = rig.obj_pose(name)
        if after[2]-before[2] < 0.02 or rig.left_fingers().min() < 0.003:
            rig.left_held = None
            raise SkillFailure("handover: object did not move with left hand")
        rig.log("handover_result", obj=name, lift_m=round(float(after[2]-before[2]), 4))
        return after[2]-before[2]


class OpenDoorWhileLeftHoldsPolicy(AtomicPolicy):
    """Open a manual door with the right arm while the left hand retains a load."""

    def execute(self, object_name, door_name):
        rig = self.rig
        if rig.left_held is None or rig.left_held["name"] != object_name or rig.held is not None:
            raise SkillFailure("open door while left holds: left load and free right hand required")
        a = rig.ann.art(door_name)
        if a["type"] != "revolute" or not a.get("handle") or "door_button" in a:
            raise SkillFailure("open door while left holds: manual hinged door required")
        q = skills.open_articulated(rig, door_name)
        left = rig.left_held
        body, _ = rig.obj_pose(object_name)
        tcp, _ = rig.left_kin.tcp(rig.left_q())
        slip = abs(np.linalg.norm(tcp-body)-np.linalg.norm(left["tcp_minus_body"]))
        if slip > 0.06 or rig.left_fingers().min() < 0.002:
            raise SkillFailure("open door while left holds: left grasp slipped")
        return q
