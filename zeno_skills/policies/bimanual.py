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
        if ok:
            return q
        # the default seed set is small and fixed; with torso and waist locked
        # the solver misses reachable poses, so retry with fresh random seeds
        rng = np.random.default_rng(int(abs(hash(tuple(np.round(position, 3)))) % 2**31))
        for _ in range(3):
            q, ok = kin.ik_global(np.asarray(position, float), rotation,
                                  seeds=[current] + [rng.uniform(kin.lo, kin.hi) for _ in range(12)])
            if ok:
                return q
        return None
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
        if slip > 0.06 or float(fingers.sum()) < 0.004:
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
        # Side-wall end grasps first: both hands approach horizontally along
        # two opposite walls and pinch each wall's near end across its
        # thickness, fingers pointing forward.  Fingers-down rim pinches on a
        # box this wide have arm IK only in a narrow window (left arm almost
        # never), while forward-pointing grasps sit in the arm's best range.
        pairs = _grip_bar_pairs(rig, asset, pos, quat) + _side_end_pairs(rig, name, asset, pos, quat)
        if groups:
            ordered = sorted(groups.values(),
                             key=lambda group: -np.linalg.norm(group[0][0]["p"]-group[0][1]["p"]))
            for tilt_index in range(max(map(len, ordered))):
                pairs.extend(group[tilt_index] for group in ordered if tilt_index < len(group))
        if not pairs:
            raise SkillFailure(f"bimanual box lift: {name} has no two separated rim contacts")
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


def _grip_bar_pairs(rig, asset, pos, quat):
    """Two end grip bars (annotated extra handle colliders): each hand slides
    its horizontal fingers along a bar and closes vertically on it.  The hands
    stay outside the box, so no wall lies between the wrist and the contact."""
    bars = (asset.get("container") or {}).get("extra_handle_colliders") or []
    if len(bars) < 2:
        return []
    from ..evaluator import quat_R
    Rb = quat_R(quat)
    centres = [np.asarray(pos, float) + Rb @ np.asarray(b["center"], float) for b in bars[:2]]
    axis = Rb @ np.array([0.0, 1.0, 0.0])
    axis = np.array([axis[0], axis[1], 0.0])
    axis /= max(1e-9, np.linalg.norm(axis))
    out = []
    half = 0.5 * float(bars[0]["size"][1])
    for appr, cz in ((axis, -1.0), (-axis, -1.0), (axis, 1.0), (-axis, 1.0)):   # either end, either wrist roll
        R = gripper_rot(appr, [0.0, 0.0, cz])
        pair = []
        for c in centres:
            p = c - appr * (half - 0.025)           # 2.5 cm in from the bar's near end
            # 6 mm out from the wall: the 2.8 cm pads centred on the 2.5 cm bar
            # rubbed the wall face while sliding in and dragged the bin 3-5 cm
            out_dir = np.r_[(c - np.asarray(pos, float))[:2], 0.0]
            p = p + 0.006 * out_dir / max(1e-9, np.linalg.norm(out_dir))
            # 2 cm open per finger (4 cm gap on the 2 cm bar): opened 3 cm the
            # upper finger slid in at rim height and caught the bin's rim lip
            pair.append({"p": p, "R": R, "pre_open": 0.02, "pre": p - appr * 0.045, "kind": "grip_bar"})
        out.append(tuple(pair))
    return out


def _side_end_pairs(rig, name, asset, pos, quat):
    g = next((g for g in asset["grasps"] if g["type"] == "rim_pinch_rect"), None)
    if g is None:
        return []
    yaw = skills._yaw(quat)
    bottom = rig.geo.bottom(name, rig.state())
    ex = np.array([math.cos(yaw), math.sin(yaw)])
    ey = np.array([-ex[1], ex[0]])
    out = []
    for a, n, half_a, half_n in ((ex, ey, g["half_x"], g["half_y"]), (-ex, ey, g["half_x"], g["half_y"]),
                                 (ey, ex, g["half_y"], g["half_x"]), (-ey, ex, g["half_y"], g["half_x"])):
        if 2 * half_n < 0.24:
            continue                     # the hands need room side by side
        z = float(bottom[2] + g["rim_height"] - 0.02)     # pads (2.8 cm) just below the rim
        R = gripper_rot(np.r_[a, 0.0], np.r_[n, 0.0])
        pair = []
        for side in (1.0, -1.0):
            # 7.5 cm along the wall: the palm behind the fingers then clears the
            # front wall (at 3.5 cm the hand sat on the front wall and stalled)
            p = np.r_[bottom[:2] + side * n * half_n - a * (half_a - 0.075), z]
            # lowered onto the wall from above: coming in horizontally, the inner
            # finger would have to pass through the front wall
            pair.append({"p": p, "R": R, "pre_open": 0.04, "pre": p + np.array([0.0, 0.0, 0.04]),
                         "kind": "side_end"})
        out.append(tuple(pair))
    return out


def _park_for_pair(rig, pair, origin, torso_target=None, deadline=None, waist_target=0.0):
    """Find one base pose from which both arms reach their separate contacts."""
    centre = 0.5*(pair[0]["p"][:2]+pair[1]["p"][:2])
    bx, by, _ = origin
    base_angles = [math.atan2(by-centre[1], bx-centre[0])]
    base_angles += [a for a in np.linspace(-math.pi, math.pi, 12, endpoint=False)]
    # Sample each direction at a useful reach before refining nearby radii;
    # the shared-pose search must remain bounded for a graph-level planner.
    for radius in (0.38, 0.43, 0.45, 0.46, 0.47, 0.48, 0.53, 0.58, 0.63, 0.68):
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
                        right_seed[:2] = [torso_target, waist_target]
                        left_seed[:2] = [torso_target, waist_target]
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
        # raise the torso instead: both arms keep their joints and the load
        # goes straight up with the chest
        from ..kinematics import _limits
        t_hi = float(_limits(rig.kin.names)[1][0])     # the true limit (the shared posture is locked)
        if rig.q_cmd[0] + height > t_hi + 1e-6:
            raise SkillFailure("bimanual lift: no paired IK for lift height")
        qr = rig.q_cmd.copy()
        qr[0] += height
        ql = np.r_[qr[:2], rig.left_q_cmd]
        rig.log("bimanual_lift_by_torso", height=round(float(height), 3))
    rig.follow_both(qr, ql, label="bimanual_lift")


def _grasp_both(rig, name, pairs, label):
    if rig.held is not None or rig.left_held is not None:
        raise SkillFailure(f"{label}: both hands must be empty")
    rig.sync_world()
    rig.world.left_active = True
    park = None
    lowest_contact = min(float(g["p"][2]) for pair in pairs for g in pair)
    first = -0.15 if label == "bimanual_flat_pick" or lowest_contact < 0.55 else None
    deadline = time.monotonic() + 150.0
    # the torso height is part of the search: horizontal grip-bar contacts at
    # table height are shared-reachable only with the torso lowered ~0.35
    torso_target, waist_target = first, 0.0
    # grip-bar pairs first come with the lowered posture that reaches them
    bar_first = any(p[0].get("kind") == "grip_bar" for p in pairs[:1])
    postures = (((-0.30, 0.05), (first, 0.0), (-0.20, 0.0), (-0.35, 0.0)) if bar_first else
                ((first, 0.0), (-0.30, 0.05), (-0.20, 0.0), (-0.35, 0.0)))
    for torso_target, waist_target in postures:
        for pair in (pairs[:4] if bar_first and torso_target is not first else pairs[:8]):
            if time.monotonic() >= deadline:
                break
            park = _park_for_pair(rig, pair, rig.base_pose(), torso_target=torso_target,
                                  deadline=deadline, waist_target=waist_target)
            if park is not None:
                break
        if park is not None:
            break
    if park is None:
        rig.sync_world()
        rig.log("bimanual_no_park", obj=name, search_budget_s=150,
                contacts=[[g["p"].round(3).tolist() for g in pair] for pair in pairs[:3]])
        raise SkillFailure(f"{label}: no collision-free shared base pose")
    pose, right, left = park
    rig.sync_world()
    if torso_target is None:
        skills.navigate(rig, pose, label=label+"_park")
    else:
        # lower the torso 35 cm back from the park, in free space (lowered at
        # the park the tucked arm reached over the table and the tuck stalled),
        # then roll straight in without re-tucking
        from .posture import SetTorsoHeightPolicy, SetWaistPitchPolicy
        yaw_r = math.radians(pose[2])
        pre = (pose[0] - 0.35 * math.cos(yaw_r), pose[1] - 0.35 * math.sin(yaw_r), pose[2])
        skills.navigate(rig, pre, label=label+"_pre_park")
        SetTorsoHeightPolicy(rig).execute(torso_target)
        SetWaistPitchPolicy(rig).execute(waist_target)
        # joints are base-relative: solve both pre-grasps for the park pose and
        # take them here, so the hands ride in at grasp height above the table
        rig.kin.set_base((pose[0], pose[1], 0.0), yaw_r)
        rig.left_kin.set_base((pose[0], pose[1], 0.0), yaw_r)
        rp = right.get("pre", right["p"] + np.array([0, 0, 0.08]))
        lp = left.get("pre", left["p"] + np.array([0, 0, 0.08]))
        qr = _fixed_torso_ik(rig.kin, rp, right["R"], rig.q_cmd)
        ql = _fixed_torso_ik(rig.left_kin, lp, left["R"], np.r_[rig.q_cmd[:2], rig.left_q_cmd])
        rig.sync_world()
        if qr is None or ql is None:
            raise SkillFailure(f"{label}: pre-grasps not solvable at the lowered posture")
        rig.follow_both(qr, ql, label=label + "_arms_ready")
        rig.sync_world()
        if not all(rig.world.footprint_clear(pre[0] + (pose[0] - pre[0]) * u, pre[1] + (pose[1] - pre[1]) * u, yaw_r)
                   for u in np.linspace(0.0, 1.0, 6)):
            raise SkillFailure(f"{label}: straight approach to the shared park is blocked")
        rig.drive_base([pose], speed=0.08, turn=0.3, ramp=0.6)
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
        rig.log("bimanual_after_pre", obj=name, body=rig.obj_pose(name)[0].round(4).tolist())
        right_q = _fixed_torso_ik(rig.kin, right["p"], right["R"], rig.q_cmd)
        left_q = _fixed_torso_ik(rig.left_kin, left["p"], left["R"],
                                 np.r_[rig.q_cmd[:2], rig.left_q_cmd])
        if right_q is None or left_q is None:
            raise SkillFailure(f"{label}: paired contact IK changed after parking")
        rig.follow_both(right_q, left_q, label=label+"_paired_contact")
        body_contact, _ = rig.obj_pose(name)
        shift = np.r_[(body_contact - p0)[:2], 0.0]
        if np.linalg.norm(shift) > 0.008:
            # the approach nudged the object (a 3 cm push left the right pads
            # on the bar's edge): follow it before closing
            for frac in (1.0, 0.8, 0.6):
                sh = shift * frac
                rq2 = _fixed_torso_ik(rig.kin, right["p"] + sh, right["R"], rig.q_cmd)
                lq2 = _fixed_torso_ik(rig.left_kin, left["p"] + sh, left["R"],
                                      np.r_[rig.q_cmd[:2], rig.left_q_cmd])
                if rq2 is not None and lq2 is not None:
                    rig.follow_both(rq2, lq2, label=label+"_follow_shift")
                    right, left = dict(right, p=right["p"] + sh), dict(left, p=left["p"] + sh)
                    rig.log("bimanual_contact_shift", obj=name, shift=sh.round(4).tolist())
                    break
            else:
                rig.log("bimanual_contact_shift_no_ik", obj=name, shift=shift.round(4).tolist())
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
    if p1[2]-p0[2] < 0.02 or float(rf.sum()) < 0.006 or float(lf.sum()) < 0.006:
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
                # the arm-arm collision check below rejects grippers that clash;
                # 6 cm keeps the pads off each other on a centre-held rolling pin
                if np.linalg.norm(candidate["p"]-right_tcp) < 0.06:
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
            found = self._present_for_horizontal_left(name)
        if found is None:
            raise SkillFailure(f"handover: no independent left contact on {name}")
        g, pre = found
        rig.log("handover_left_target", obj=name, contact=g["p"].round(3).tolist(),
                pre=pre.round(3).tolist())
        rig.left_grip(g["pre_open"], 30)
        rig.move_left_to(pre, g["R"], label="handover_left_pre")
        rig.move_left_to(g["p"], g["R"], label="handover_left_contact")
        fingers = rig.left_grip(0.0, 120)
        if float(fingers.sum()) < 0.005:
            raise SkillFailure("handover: left fingers did not contact object")
        before, _ = rig.obj_pose(name)
        ltcp, lR = rig.left_kin.tcp(rig.left_q())
        rig.left_held = {"name": name, "tcp_minus_body": ltcp-before,
                         "R": lR, "pre_open": g["pre_open"]}
        rig.grip(rig.held["pre_open"], 70)
        rig.held = None
        rtcp, rR = rig.kin.tcp(rig.q_cmd)
        for d in (0.06, 0.03):
            try:
                rig.move_to(rtcp + np.array([0, 0, d]), rR, step=0.004, label="handover_right_clear", collision=False)
                break
            except SkillFailure:
                continue
        # close the left hand again now that the right gripper is out of the
        # way: its upper finger had been blocked by the right gripper above
        lf = rig.left_grip(0.0, 80)
        rig.log("handover_left_regrip", fingers=np.round(lf, 4).tolist())
        rig.move_left_to(ltcp+np.array([0, 0, 0.05]), lR, label="handover_left_lift")
        rig.step(60)
        after, _ = rig.obj_pose(name)
        ltcp2, _ = rig.left_kin.tcp(rig.left_q())
        # held in the left pads: the grip-point distance is kept and the
        # fingers are not shut (a handle-held pin pivots, so its centre rises
        # less than the hand)
        slip = abs(float(np.linalg.norm(ltcp2-after)) - float(np.linalg.norm(rig.left_held["tcp_minus_body"])))
        lf2 = rig.left_fingers()
        rig.log("handover_lift_check", obj=name, lift_m=round(float(after[2]-before[2]), 4),
                slip_m=round(slip, 4), fingers=np.round(lf2, 4).tolist())
        if float(lf2.sum()) < 0.005 or slip > 0.03 or after[2]-before[2] < -0.02:
            rig.left_held = None
            raise SkillFailure("handover: object did not move with left hand")
        rig.left_held["tcp_minus_body"] = ltcp2-after
        rig.log("handover_result", obj=name, lift_m=round(float(after[2]-before[2]), 4))
        return after[2]-before[2]


    def _present_for_horizontal_left(self, name):
        """Long object pinched fingers-down by the right hand: turn it ~60 deg
        across the body in front of the chest (base frame x 0.38-0.40, y -0.08,
        z ~1.0) and let the left hand come in horizontally from the front,
        closing vertically on it 7 cm from the right pinch.  Fingers-down
        contacts that close for both hands have no common IK (offline search)."""
        rig = self.rig
        from ..evaluator import quat_R
        size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
        if max(size[:2]) < 0.15:
            return None
        # the presentation poses were found with the torso up and the waist straight
        if abs(rig.q_cmd[0] - rig.kin.hi[0]) > 0.02 or abs(rig.q_cmd[1]) > 0.02:
            # torso up and waist straight with the object held: the arm joints
            # stay fixed, so the load just rises and comes back with the chest
            q_goal = rig.q_cmd.copy()
            q_goal[0], q_goal[1] = float(rig.kin.hi[0]), 0.0
            try:
                rig.follow(rig.joint_path(q_goal, "handover_posture"))
            except SkillFailure as exc:
                rig.log("handover_posture_short", reason=str(exc))
            skills.check_held(rig, "handover_posture")
        bx, by, yaw = rig.base_pose()
        c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        to_world = lambda v: np.array([c * v[0] - sn * v[1], sn * v[0] + c * v[1], v[2]])
        counts = {"right_ik": 0, "left_ik": 0}
        for axis_deg in (60.0, 50.0, 70.0):
            for fwd, lat, h in ((0.40, -0.08, 1.02), (0.40, -0.10, 0.98), (0.35, -0.10, 1.02), (0.40, -0.05, 1.06)):
                ax = to_world(np.array([math.cos(math.radians(axis_deg)), math.sin(math.radians(axis_deg)), 0.0]))
                close = -np.cross([0.0, 0.0, 1.0], ax)
                R = gripper_rot([0.0, 0.0, -1.0], close)
                tcp_goal = np.array([bx, by, 0.0]) + to_world(np.array([fwd, lat, 0.0])) + np.array([0, 0, h])
                qr = _fixed_torso_ik(rig.kin, tcp_goal, R, rig.q_cmd)
                if qr is None:
                    counts["right_ik"] += 1
                    continue
                appr = np.cross(ax, [0.0, 0.0, 1.0])
                if appr @ to_world(np.array([1.0, 0, 0])) < 0:
                    appr = -appr
                left_dir = to_world(np.array([0.0, 1.0, 0.0]))
                pl = tcp_goal + ax * 0.07 * (1.0 if ax @ left_dir > 0 else -1.0)
                RL = gripper_rot(appr, [0.0, 0.0, 1.0])
                ql = _fixed_torso_ik(rig.left_kin, pl - appr * 0.08, RL, np.r_[rig.q_cmd[:2], rig.left_q_cmd])
                if ql is None or _fixed_torso_ik(rig.left_kin, pl, RL, ql) is None:
                    counts["left_ik"] += 1
                    continue
                try:
                    # follow the planned joints exactly: a free IK re-solve bent the
                    # waist and left the left arm's plan (same torso) unreachable
                    rig.follow(rig.joint_path(qr, "handover_present_across", check=False), steps_per_wp=6)
                    skills.check_held(rig, "handover_present_across")
                except Dropped:
                    raise
                except SkillFailure as exc:
                    rig.log("handover_present_across_short", reason=str(exc))
                    continue
                # re-measure the object's long axis and centre after the turn
                st = rig.state()
                Rb = quat_R(st["objects"][name]["quat"])
                ax_now = Rb[:, int(np.argmax(size))]
                ax_now = np.array([ax_now[0], ax_now[1], 0.0])
                ax_now /= max(1e-9, np.linalg.norm(ax_now))
                tcp_now, _ = rig.kin.tcp(rig.q())
                centre = np.asarray(rig.geo.centre(name, st), float)
                sgn = 1.0 if ax_now @ left_dir > 0 else -1.0
                along = float((tcp_now - centre)[:2] @ ax_now[:2])
                # at least 7 cm from the right pinch, and on the handle (~0.39 L
                # from the centre, short of the end): 7 cm from a centre pinch
                # landed on the barrel/handle step and the pin slid out
                L = float(max(size))
                off = sgn * min(max(along * sgn + 0.07, 0.39 * L), 0.5 * L - 0.02)
                pl = centre + ax_now * off
                pl[2] = centre[2]
                appr = np.cross(ax_now, [0.0, 0.0, 1.0])
                if appr @ to_world(np.array([1.0, 0, 0])) < 0:
                    appr = -appr
                RL = gripper_rot(appr, [0.0, 0.0, 1.0])
                rig.sync_world()
                rig.world.left_active = True
                ql = _fixed_torso_ik(rig.left_kin, pl - appr * 0.08, RL, np.r_[rig.q_cmd[:2], rig.left_q_cmd])
                if ql is None or _fixed_torso_ik(rig.left_kin, pl, RL, ql) is None:
                    rig.log("handover_across_left_no_ik", contact=pl.round(3).tolist())
                    continue
                rig.log("handover_present_across", axis_deg=axis_deg, right=tcp_goal.round(3).tolist())
                return {"p": pl, "R": RL, "pre_open": 0.04}, pl - appr * 0.08
        rig.log("handover_across_none", torso=np.round(rig.q_cmd[:2], 3).tolist(), **counts)
        return None


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
