"""Base and whole-body policies that take a scene *noun* instead of a pose.

policy_092 NavigateToPlacePolicy   room / furniture / support / object -> free stand-off pose
policy_065 ApproachTargetPolicy    park where the right TCP reaches the target (IK-verified)
policy_066 FaceTargetPolicy        rotate the base in place toward a target
policy_067 RetreatFromPolicy       back the base away from a place, keeping any load
policy_091 LeftArmFoldPolicy       fold the empty left arm to its travel posture
"""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..physics import PHYSICS_HZ
from ..planner import find_park
from ..predicates import (NEAR_M, entity_footprint, entity_kind, entity_point, ik_reachable,
                          reach_targets)
from ..rig import SkillFailure


# Stand-off poses around a place (standoff_poses).  Inherited (32a2d66c), never measured:
# docs/COLLISION_PLAN.md §2.  The base column is checked as the base planner checks it (the
# footprint's default margin), the whole robot by skills.poses_clear.
STANDOFF_RING = (0.45, 0.55, 0.70, 0.85, 1.0)   # m out from the place's footprint
STANDOFF_DEG = 15.0                             # deg between stand-offs on a ring
STANDOFF_RING_W = 0.3                           # m of drive one m further out on the ring costs in the ranking
STANDOFF_NEAR_SLACK = 0.05                      # m inside NEAR_M every stand-off stays (base_near holds there)
ROOM_SPOT_STEP = 0.25                           # m between rings around a room's centroid...
ROOM_SPOT_MAX = 3.0                             # ...out to this far
ROOM_SPOT_DEG = 30.0                            # deg between spots on a ring
# Base turns and moves on request (inherited, 32a2d66c; unmeasured).
FACE_ERR_DEG = 5.0          # deg of heading a turn in place may still miss by before face fails
RETREAT_PAST = 0.03         # m a retreat goes past the distance asked for
RETREAT_MIN = 0.01          # m: a retreat shorter than this is not driven


def _park_diag():
    from ..planner import LAST_PARK_DIAG
    return {k: v for k, v in LAST_PARK_DIAG.items() if v}


def _box_dist(box, xy):
    dx = max(box[0] - xy[0], 0.0, xy[0] - box[2])
    dy = max(box[1] - xy[1], 0.0, xy[1] - box[3])
    return math.hypot(dx, dy)


def standoff_poses(rig, place, ring=STANDOFF_RING):
    """Free base poses around a place's footprint, facing it, nearest first: the base column clear
    of the annotated furniture, then the whole robot in its travel posture clear of the world
    (skills.poses_clear)."""
    rig.sync_world()
    kind, rec = entity_kind(rig.ann, place)
    world = rig.world
    x0, y0, _ = rig.base_pose()
    out = []
    if kind == "room":
        tris = np.asarray(rec["triangles"], float).reshape(-1, 3, 2)
        cents = tris.mean(axis=1)
        areas = 0.5 * np.abs(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]))
        c = (cents * areas[:, None]).sum(0) / max(areas.sum(), 1e-9)
        from ..evaluator import room_of
        for r in np.arange(0.0, ROOM_SPOT_MAX, ROOM_SPOT_STEP):
            for ang in np.radians(np.arange(0, 360, ROOM_SPOT_DEG)):
                x, y = c[0] + r * math.cos(ang), c[1] + r * math.sin(ang)
                if room_of(rig.ann.rooms, (x, y)) != place:
                    continue
                yaw = math.degrees(math.atan2(y - y0, x - x0))
                if world.footprint_clear(x, y, math.radians(yaw)):
                    out.append((r, x, y, yaw))
        out.sort()
        return skills.poses_clear(rig, [(x, y, yaw) for _, x, y, yaw in out])
    box = entity_footprint(rig, place)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    for d in ring:
        for ang in np.radians(np.arange(0, 360, STANDOFF_DEG)):
            ux, uy = math.cos(ang), math.sin(ang)
            # point on the box boundary in this direction, then d further out
            tx = (box[2] - cx) / ux if ux > 1e-9 else (box[0] - cx) / ux if ux < -1e-9 else math.inf
            ty = (box[3] - cy) / uy if uy > 1e-9 else (box[1] - cy) / uy if uy < -1e-9 else math.inf
            t = min(abs(tx), abs(ty))
            x, y = cx + ux * (t + d), cy + uy * (t + d)
            yaw = math.degrees(math.atan2(cy - y, cx - x))
            if not world.footprint_clear(x, y, math.radians(yaw)):
                continue
            if _box_dist(box, (x, y)) > NEAR_M - STANDOFF_NEAR_SLACK:
                continue
            out.append((math.hypot(x - x0, y - y0) + STANDOFF_RING_W * d, x, y, yaw))
    out.sort()
    return skills.poses_clear(rig, [(x, y, yaw) for _, x, y, yaw in out])


class NavigateToPlacePolicy(AtomicPolicy):
    """Drive to a collision-free stand-off pose near a room, furniture, support or object."""

    def execute(self, place):
        rig = self.rig
        entity_kind(rig.ann, place)                     # KeyError for an unknown noun
        min_bottom_z = None
        if rig.held is not None:
            # the load's bottom clear of the destination surface (W: plan_helpers._carry_bottom_z,
            # until the base planner changes the carry height itself, docs/COLLISION_PLAN.md §7)
            from .plan_helpers import _carry_bottom_z
            min_bottom_z = _carry_bottom_z(rig, place)
            # the carry posture the drive will use, before the stand-offs are checked in it
            # (navigate re-takes it; a pick that ended short of it changed it there, P15)
            skills._carry_pose(rig, min_bottom_z=min_bottom_z)
        poses = standoff_poses(rig, place)
        if not poses:
            raise SkillFailure(f"navigate to {place}: no free stand-off pose")
        # the stand-off poses are one goal set: the nearest one the base can get to from here (one
        # field over all of them, skills.base_reachable), then one navigate -- not tried in turn
        ok = skills.base_reachable(rig, poses)
        reach = [p for p, o in zip(poses, ok) if o]
        rig.log("navigate_place_goals", place=place, goals=len(poses), reachable=len(reach))
        if not reach:
            raise SkillFailure(f"navigate to {place}: no base path to any of {len(poses)} stand-off poses "
                               "(even the column's inscribed circle cannot get there)")
        pose = reach[0]
        rig.caption = f"NAVIGATE to {place}"
        skills.navigate(rig, pose, label=f"navigate_{place}", min_bottom_z=min_bottom_z)
        rig.log("navigate_place", place=place, pose=[round(v, 3) for v in pose])
        return tuple(rig.base_pose())


class ApproachTargetPolicy(AtomicPolicy):
    """Park the base where the right TCP has an IK solution at the target's
    reach pose (10 cm above an object or support, handle pre-grasp, 8 cm in
    front of a button), then verify it from the reached pose."""

    def execute(self, target, *, max_tries=160):
        rig = self.rig
        targets = reach_targets(rig, target)
        ok, _ = ik_reachable(rig, targets)
        if ok:
            rig.log("approach_already", target=target)
            return tuple(rig.base_pose())
        rig.sync_world()
        saved = rig.kin.coll_kw
        rig.kin.coll_kw = {"ignore_fingers": True}
        try:
            park = None
            for p, R in targets:
                park = find_park(rig.kin, rig.world, [(p, R)], near=rig.base_pose()[:2], max_tries=max_tries,
                                 travel_q=skills._travel_q(rig))
                if park:
                    break
        finally:
            rig.kin.coll_kw = saved
        if park is None:
            raise SkillFailure(f"approach {target}: no base pose reaches it (rejected: {_park_diag()})")
        x, y, yaw, _ = park
        rig.caption = f"APPROACH {target}"
        skills.navigate(rig, (x, y, yaw), label=f"approach_{target}")
        ok, where = ik_reachable(rig, reach_targets(rig, target))
        rig.log("approach_result", target=target, park=[round(x, 3), round(y, 3), round(yaw, 1)], reachable=ok)
        if not ok:
            raise SkillFailure(f"approach {target}: parked but IK fails at {where}")
        return tuple(rig.base_pose())


class FaceTargetPolicy(AtomicPolicy):
    """Rotate the base in place until it faces the target (within 3 deg)."""

    def execute(self, target, *, tolerance_deg=3.0):
        rig = self.rig
        x, y, yaw = rig.base_pose()
        p = entity_point(rig, target)
        bearing = math.degrees(math.atan2(p[1] - y, p[0] - x))
        delta = (bearing - yaw + 180) % 360 - 180
        if abs(delta) <= tolerance_deg:
            return yaw
        if rig.held is None and rig.left_held is None:
            if not rig.tuck():
                raise SkillFailure(f"face {target}: cannot fold the arm before turning")
        skills.straight_base_move(rig, (x, y, bearing), f"face {target}")
        x2, y2, yaw2 = rig.base_pose()
        err = abs((bearing - yaw2 + 180) % 360 - 180)
        rig.log("face_result", target=target, yaw_deg=round(yaw2, 1), error_deg=round(err, 1))
        if err > max(tolerance_deg, FACE_ERR_DEG):
            raise SkillFailure(f"face {target}: heading error {err:.1f} deg")
        return yaw2


class RetreatFromPolicy(AtomicPolicy):
    """Back the base straight away from a place; a held object stays held."""

    def execute(self, place, distance_m=0.4):
        rig = self.rig
        rig.sync_world()
        box = entity_footprint(rig, place)
        x, y, yaw = rig.base_pose()
        nearest = np.array([min(max(x, box[0]), box[2]), min(max(y, box[1]), box[3])])
        away = np.array([x, y]) - nearest
        if np.linalg.norm(away) < 1e-6:
            away = -np.array([math.cos(math.radians(yaw)), math.sin(math.radians(yaw))])
        away /= np.linalg.norm(away)
        need = max(0.0, float(distance_m) - _box_dist(box, (x, y)))
        if need < RETREAT_MIN:
            return 0.0
        end = np.array([x, y]) + away * (need + RETREAT_PAST)
        if rig.held is not None:
            skills.check_held(rig, "retreat_start")
            skills.straight_base_move(rig, (end[0], end[1], yaw), f"retreat from {place}")
            skills.check_held(rig, "retreat_end")
        else:
            skills.straight_base_move(rig, (end[0], end[1], yaw), f"retreat from {place}")
        moved = float(np.linalg.norm(np.asarray(rig.base_pose()[:2]) - np.array([x, y])))
        rig.log("retreat_result", place=place, moved_m=round(moved, 3))
        return moved


class LeftArmFoldPolicy(AtomicPolicy):
    """Fold the empty left arm to its travel posture."""

    def execute(self):
        rig = self.rig
        if rig.left_held is not None:
            raise SkillFailure("fold left arm: the left hand holds an object")
        rig.left_grip(0.04, 30)
        goal = np.r_[rig.q_cmd[:2], rig.left_kin.rest[2:]]
        start = np.r_[rig.q_cmd[:2], rig.left_q_cmd]
        rig.left_follow(rig._dense(start, goal))
        err = float(np.max(np.abs(rig.left_q()[2:] - rig.left_kin.rest[2:])))
        if err > 0.08:
            rig.step(PHYSICS_HZ)          # let the slow wrist joints settle
            err = float(np.max(np.abs(rig.left_q()[2:] - rig.left_kin.rest[2:])))
        rig.log("left_fold", error_rad=round(err, 4))
        if err > 0.15:
            raise SkillFailure(f"fold left arm: joint error {err:.3f} rad")
        return err
