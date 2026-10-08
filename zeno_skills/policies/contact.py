"""Non-prehensile contact policies (closed fingers, no grasp).

policy_079 PullTowardBasePolicy      drag an object toward the robot (pads pressed on its top)
policy_080 SeparateFromNeighbourPolicy  push an object away from its closest neighbour
policy_081 RollCylinderPolicy        roll a lying cylinder by pushing above its axis
policy_082 TipOverPolicy             push a standing object near its top so it lies down
policy_083 CenterOnSupportPolicy     push an object back from the support edges
"""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..kinematics import gripper_rot
from ..planner import find_park
from ..predicates import finger_slots_free, neighbour_gap, tilt_deg, GRASP_GAP_M
from ..rig import SkillFailure


def _park_diag():
    from ..planner import LAST_PARK_DIAG
    return {k: v for k, v in LAST_PARK_DIAG.items() if v}


def _support(rig, name):
    s = rig.geo.support_under(name, rig.state())
    if s is None:
        raise SkillFailure(f"{name}: not resting on an annotated support")
    return s


def _room_along(rig, name, s, n, margin=0.02):
    """Distance the object footprint may travel along n before leaving s."""
    st = rig.state()
    fp = rig.geo.footprint(name, st)
    x0, y0, x1, y1 = s["aabb_xy"]
    lim = []
    if n[0] > 1e-6:
        lim.append((x1 - margin - fp[2]) / n[0])
    if n[0] < -1e-6:
        lim.append((x0 + margin - fp[0]) / n[0])
    if n[1] > 1e-6:
        lim.append((y1 - margin - fp[3]) / n[1])
    if n[1] < -1e-6:
        lim.append((y0 + margin - fp[1]) / n[1])
    return max(0.0, min(lim)) if lim else 0.0


class PullTowardBasePolicy(AtomicPolicy):
    """Drag an object horizontally toward the base with the pads on its top."""

    def execute(self, name, distance_m):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("pull: the right hand must be empty")
        s = _support(rig, name)
        x, y, _ = rig.base_pose()
        b = rig.geo.bottom(name, rig.state())
        n = np.array([x, y]) - b[:2]
        n /= np.linalg.norm(n)
        # snap to the nearest support axis so the drag stays on the surface
        n = np.array([np.sign(n[0]), 0.0]) if abs(n[0]) >= abs(n[1]) else np.array([0.0, np.sign(n[1])])
        d = min(float(distance_m), _room_along(rig, name, s, n))
        if d < 0.02:
            raise SkillFailure(f"pull {name}: already at the near edge")
        try:
            moved = skills.push(rig, name, s, n, d, label="PULL", mode="drag")
        except SkillFailure as exc:
            # pads slide over round or slippery tops: hook the far side instead
            # (fingers down behind the object, pushing toward the base)
            if "did not move" not in str(exc) or rig.held is not None:
                raise
            rig.log("pull_hook", obj=name, reason=str(exc))
            moved = skills.push(rig, name, s, n, d, label="PULL", mode="push")
        rig.log("pull_result", obj=name, moved_m=round(moved, 3))
        return moved


class SeparateFromNeighbourPolicy(AtomicPolicy):
    """Push the object straight away from its nearest neighbour until the gap
    admits a finger (3.5 cm + 1 cm), staying on the support."""

    def execute(self, name, *, target_gap=GRASP_GAP_M + 0.01):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("separate: the right hand must be empty")
        s = _support(rig, name)
        gap0, _ = neighbour_gap(rig, name, rig.state())
        for attempt in range(3):          # a neighbour dragged along by friction: re-measure, push again
            st = rig.state()
            gap, other = neighbour_gap(rig, name, st)
            free, _ = finger_slots_free(rig, name, st)
            if other is None or free or (free is None and gap >= target_gap):
                break
            st = rig.state()
            away = rig.geo.bottom(name, st)[:2] - rig.geo.bottom(other, st)[:2]
            away /= max(1e-9, np.linalg.norm(away))
            choices = []
            for ang in (0, 30, -30, 60, -60, 90, -90):
                c, si = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                n = np.array([c * away[0] - si * away[1], si * away[0] + c * away[1]])
                need = (target_gap - gap) / max(0.3, float(n @ away)) + 0.01
                if _room_along(rig, name, s, n) >= need:
                    choices.append((abs(ang), n, need))
            if not choices:
                raise SkillFailure(f"separate {name}: no room on {s['name']} to move away from {other}")
            _, n, need = sorted(choices, key=lambda t: t[0])[0]
            skills.push(rig, name, s, n, need, label="SEPARATE")
        st = rig.state()
        gap2, other2 = neighbour_gap(rig, name, st)
        free2, why = finger_slots_free(rig, name, st)
        rig.log("separate_result", obj=name, before_gap=round(gap0, 3), gap=round(gap2, 3), neighbour=other2,
                pushes=attempt + 1, finger_slots=why,
                obj_fp=np.round(rig.geo.footprint(name, st), 3).tolist(),
                neighbour_fp=(np.round(rig.geo.footprint(other2, st), 3).tolist() if other2 else None))
        if not (free2 or (free2 is None and gap2 >= GRASP_GAP_M)):
            raise SkillFailure(f"separate {name}: {why if free2 is not None else f'gap {gap2:.3f} m to {other2}'}")
        return gap2


def _long_axis(rig, name):
    st = rig.state()
    from ..evaluator import quat_R
    R = quat_R(st["objects"][name]["quat"])
    size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
    axis = R[:, int(np.argmax(size))]
    return axis, size


def _contact_sweep(rig, name, start_xy, n, z_tcp, travel, label, side_ok=False):
    """Closed fingers pointing down, TCP at z_tcp: approach behind the object,
    sweep ``travel`` along n, lift.  Returns the measured object displacement."""
    lat = np.array([-n[1], n[0]])
    rig.sync_world()
    rig.kin.coll_kw = {"ignore_fingers": True}
    park, legs = None, None
    options = []
    for d in (lat, -lat, n, -n):            # closed fingers pointing down: any closing direction pushes
        R = gripper_rot([0, 0, -1.0], [d[0], d[1], 0.0])
        options.append([(np.r_[start_xy, z_tcp + 0.05], R), (np.r_[start_xy, z_tcp], R),
                        (np.r_[start_xy + n * travel, z_tcp], R), (np.r_[start_xy + n * travel, z_tcp + 0.05], R)])
    if side_ok:
        # fingers pointing along the push (a poke): easier near shoulder height;
        # the closed tips sit ~2 cm ahead of the TCP, so start 2 cm further back
        back = np.r_[start_xy - n * 0.02, z_tcp - 0.018]
        for close in ((0, 0, 1.0), (lat[0], lat[1], 0.0)):
            R = gripper_rot([n[0], n[1], 0.0], close)
            options.append([(back - np.r_[n * 0.08, 0.0], R), (back, R), (back + np.r_[n * travel, 0.0], R),
                            (back + np.r_[n * (travel - 0.06), 0.0], R)])
    for legs in options:
        park = find_park(rig.kin, rig.world, legs, near=rig.base_pose(), max_tries=80, q_start=rig.q_cmd,
                         travel_q=skills._travel_q(rig))
        if park is not None:
            break
    if park is None:
        raise SkillFailure(f"{label} {name}: no base pose reaches the contact sweep (rejected: {_park_diag()})")
    skills._goto_park(rig, park)
    rig.kin.coll_kw = {"ignore_fingers": True}
    rig.grip(0.0, 30)
    p0 = rig.obj_pose(name)[0]
    rig.move_to(*legs[0], step=0.02, label=f"{label}_above", q_hint=park[3][0])
    rig.move_to(*legs[1], step=0.005, steps_per_wp=4, label=f"{label}_down", collision=False)
    rig.move_to(*legs[2], step=0.003, steps_per_wp=4, label=f"{label}_sweep", collision=False)
    rig.move_to(*legs[3], step=0.01, label=f"{label}_up", collision=False)
    rig.grip(0.04, 60)
    rig.step(90)
    return rig.obj_pose(name)[0] - p0


class RollCylinderPolicy(AtomicPolicy):
    """Roll a lying cylinder (rolling pin, bottle on its side) the way a hand
    does: closed pads press on its top and move perpendicular to its axis, so
    the rubber pads turn it and its centre travels half as far as the hand."""

    def execute(self, name, distance_m=0.10):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("roll: the right hand must be empty")
        s = _support(rig, name)
        q0 = rig.obj_pose(name)[1]
        from ..predicates import lying_state
        if not lying_state(rig, name, rig.state())[0]:
            raise SkillFailure(f"roll {name}: object is not lying on its side")
        axis, size = _long_axis(rig, name)
        n = np.array([-axis[1], axis[0]])
        n /= max(1e-9, np.linalg.norm(n))
        x, y, _ = rig.base_pose()
        b = rig.geo.bottom(name, rig.state())
        if n @ (b[:2] - np.array([x, y])) < 0:
            n = -n                                         # roll away from the robot
        if _room_along(rig, name, s, n) < 0.6 * float(distance_m):
            n = -n
        d = min(float(distance_m), _room_along(rig, name, s, n))
        if d < 0.03:
            raise SkillFailure(f"roll {name}: no room on {s['name']}")
        dia = float(sorted(size)[1])
        top = s["z"] + dia
        start = b[:2] - n * 0.01
        # the TCP sits ~2 cm above the closed pad tips: tips press ~1 cm into the top
        z_tcp = top + 0.010
        _contact_sweep(rig, name, start, n, z_tcp, 2.0 * d, "roll")
        from ..predicates import _rot_angle
        ang = _rot_angle(q0, rig.obj_pose(name)[1])
        moved = float((rig.geo.bottom(name, rig.state())[:2] - b[:2]) @ n)
        rig.log("roll_result", obj=name, moved_m=round(moved, 3), rotation_deg=round(ang, 1))
        if ang < 45.0:
            raise SkillFailure(f"roll {name}: rotated only {ang:.0f} deg (slid instead of rolling)")
        return ang


class TipOverPolicy(AtomicPolicy):
    """Push a standing object 80 % up its height so it falls onto its side on
    the same support (toward the support's interior)."""

    def execute(self, name):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("tip: the right hand must be empty")
        s = _support(rig, name)
        size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
        if tilt_deg(rig.obj_pose(name)[1]) > 20:
            raise SkillFailure(f"tip {name}: already not upright")
        if size[2] < 1.3 * min(size[:2]):
            raise SkillFailure(f"tip {name}: too squat to topple")
        st = rig.state()
        b = rig.geo.bottom(name, st)
        x0, y0, x1, y1 = s["aabb_xy"]
        centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        bx, by, _ = rig.base_pose()
        away = b[:2] - np.array([bx, by])
        away = np.array([np.sign(away[0]), 0.0]) if abs(away[0]) >= abs(away[1]) else np.array([0.0, np.sign(away[1])])
        inward = centre - b[:2]
        inward = np.array([np.sign(inward[0]), 0.0]) if abs(inward[0]) >= abs(inward[1]) else np.array([0.0, np.sign(inward[1])])
        # prefer pushing away from the robot (a forward poke); it must land on the support
        n = next((d for d in (away, inward, -away) if _room_along(rig, name, s, d) >= size[2] * 0.8), None)
        if n is None:
            raise SkillFailure(f"tip {name}: not enough room on {s['name']} to lie down")
        half = skills._half_along(size, skills._yaw(st["objects"][name]["quat"]), n)
        start = b[:2] - n * (half + 0.03)
        z_tcp = s["z"] + 0.80 * size[2] + 0.018
        _contact_sweep(rig, name, start, n, z_tcp, half + 0.09, "tip", side_ok=True)
        t = tilt_deg(rig.obj_pose(name)[1])
        on, _ = rig.geo.on(name, s["name"], rig.state())
        rig.log("tip_result", obj=name, tilt_deg=round(t, 1), on_support=bool(on))
        if t < 60 or not on:
            raise SkillFailure(f"tip {name}: tilt {t:.0f} deg, on support {on}")
        return t


class CenterOnSupportPolicy(AtomicPolicy):
    """Push the object toward the support centre until every edge margin is met."""

    def execute(self, name, margin_m=0.08):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("center: the right hand must be empty")
        s = _support(rig, name)
        st = rig.state()
        fp = rig.geo.footprint(name, st)
        x0, y0, x1, y1 = s["aabb_xy"]
        margins = {(1.0, 0.0): fp[0] - x0, (-1.0, 0.0): x1 - fp[2], (0.0, 1.0): fp[1] - y0, (0.0, -1.0): y1 - fp[3]}
        # push away from the edge with the smallest margin
        (dx, dy), m = min(margins.items(), key=lambda kv: kv[1])
        need = float(margin_m) - m
        if need <= 0.005:
            return m
        n = np.array([dx, dy])
        skills.push(rig, name, s, n, need + 0.01, label="CENTER")
        from ..predicates import REGISTRY
        ok, why = REGISTRY["away_from_edge"].evaluate(rig, None, object=name, margin_m=margin_m)
        rig.log("center_result", obj=name, ok=bool(ok), detail=why)
        if not ok:
            raise SkillFailure(f"center {name}: {why}")
        return True
