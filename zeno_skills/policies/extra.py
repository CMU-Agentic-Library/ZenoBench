"""Policies for the gesture, timing, probing and arrangement verbs.

policy_102 ShakeHeldPolicy        oscillate a held object sideways; count cycles while it stays held
policy_103 WaitPolicy             let simulated time pass
policy_104 WaveHandPolicy         raise the empty right hand and swing it
policy_105 NodHeadPolicy          pitch the head down and up
policy_106 KnockPanelPolicy       tap a closed door/drawer panel twice with closed fingertips
policy_107 TouchObjectPolicy      bring the closed fingertips onto an object's top and back off
policy_108 PlanSquareYawPolicy    yaw correction that aligns an object with its support's axes (no motion)
policy_109 SweepTogetherPolicy    push objects toward their centroid until they form a cluster
policy_110 IdentifyObjectPolicy   look at an object and record its category
policy_111 MeasureObjectPolicy    look at an object and record its size
policy_112 CountCategoryPolicy    sweep the head and count visible objects of a category
policy_113 DipUtensilPolicy       lower a held spoon tip into a container and lift it out
policy_114 SidestepPolicy         move the base sideways, also with a load
policy_115 HoverOverPolicy        hold the carried object just above a target without releasing it
"""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..evaluator import quat_R
from ..kinematics import gripper_rot
from ..perception import project_to_head_camera
from ..planner import find_park
from ..predicates import entity_kind, entity_point, memory
from ..rig import SkillFailure


def _park_diag():
    from ..planner import LAST_PARK_DIAG
    return {k: v for k, v in LAST_PARK_DIAG.items() if v}


def _mem(rig, key):
    return memory(rig).setdefault(key, {})


class ShakeHeldPolicy(AtomicPolicy):
    def execute(self, name, *, cycles=3, amplitude=0.02):
        rig = self.rig
        if rig.held is None or rig.held["name"] != name:
            raise SkillFailure(f"shake {name}: not right-held")
        tcp, R = rig.kin.tcp(rig.q_cmd)
        x, y, yaw = rig.base_pose()
        # shake along the closing axis: the pads take the inertial load in
        # compression instead of shear (a sideways shake rolled a block in the pinch)
        lat = R[:, 1].copy()
        lat[2] = 0.0
        if np.linalg.norm(lat) < 0.3:
            lat = np.array([-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0.0])
        lat /= np.linalg.norm(lat)
        gap0 = float(rig.fingers().sum())
        done = 0
        for _ in range(int(cycles)):
            for s in (1, -1):
                rig.move_to(tcp + s * amplitude * lat, R, step=0.004, steps_per_wp=3, label="shake", collision=False)
            skills.check_held(rig, "shake")
            done += 1
        rig.move_to(tcp, R, step=0.004, label="shake_end", collision=False)
        rig.step(30)
        gap1 = float(rig.fingers().sum())
        rig.log("shake_grip", obj=name, gap_before=round(gap0, 4), gap_after=round(gap1, 4))
        if gap0 - gap1 > 0.008:
            raise SkillFailure(f"shake {name}: the pinch closed {gap0 - gap1:.3f} m (object turned in the hand)")
        _mem(rig, "shaken")[name] = _mem(rig, "shaken").get(name, 0) + done
        rig.log("shake_result", obj=name, cycles=done)
        return {"cycles": done}


class WaitPolicy(AtomicPolicy):
    def execute(self, seconds):
        s = float(seconds)
        if not math.isfinite(s) or s <= 0 or s > 600:
            raise ValueError("wait: seconds must be in (0, 600]")
        self.rig.caption = f"WAIT {s:.0f} s"
        self.rig.step(int(round(s * 120)))
        return {"elapsed_s": s}


class WaveHandPolicy(AtomicPolicy):
    def execute(self, *, swings=3):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("wave: the right hand holds an object")
        x, y, yaw = rig.base_pose()
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        centre = np.array([x + 0.35 * c + 0.25 * s, y + 0.35 * s - 0.25 * c, 1.25])
        lat = np.array([-s, c, 0.0])
        R = gripper_rot([0, 0, 1.0], [c, s, 0.0])          # fingers up, palm forward
        rig.grip(0.04, 20)
        last = None
        for z in (1.25, 1.15, 1.05):
            centre[2] = z
            try:
                rig.move_to(centre, R, label="wave_raise", smooth=True)
                break
            except SkillFailure as exc:
                last = exc
        else:
            raise last
        n = 0
        for _ in range(int(swings)):
            for sgn in (1, -1):
                rig.move_to(centre + sgn * 0.10 * lat, R, step=0.01, steps_per_wp=2, label="wave_swing", collision=False)
            n += 1
        _mem(rig, "gestures")["wave"] = n
        rig.log("wave_result", swings=n)
        rig.tuck()
        return {"swings": n}


class NodHeadPolicy(AtomicPolicy):
    def execute(self, *, times=2, depth=0.35):
        from .perceive import drive_head
        rig = self.rig
        yaw0 = rig.head_q()["head_yaw_joint"]
        n = 0
        for _ in range(int(times)):
            drive_head(rig, yaw0, depth, steps=60)
            down = rig.head_q()["head_pitch_joint"]
            drive_head(rig, yaw0, -0.15, steps=60)
            up = rig.head_q()["head_pitch_joint"]
            if down - up >= 0.2:
                n += 1
        drive_head(rig, yaw0, 0.0, steps=40)
        _mem(rig, "gestures")["nod"] = n
        rig.log("nod_result", cycles=n)
        return {"cycles": n}


class KnockPanelPolicy(AtomicPolicy):
    """Tap the closed panel of a door/drawer twice, 7 cm beside its handle."""

    def execute(self, name, *, taps=2):
        rig = self.rig
        a = rig.ann.art(name)
        if rig.held is not None:
            raise SkillFailure("knock: the right hand holds an object")
        h = a.get("handle")
        if not h:
            raise SkillFailure(f"knock {name}: no annotated panel frame")
        out = np.asarray(h["outward"], float)
        along = np.asarray(h["along"], float)
        hc = np.asarray(h["center"], float)
        bar = float(np.abs(np.asarray(h.get("bar_size", [0.02, 0.02, 0.02]), float)) @ np.abs(out))
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        park, panel, pre, R = None, None, None, None
        # tap beside or above the handle, on the panel plane behind the bar
        for da, dz in ((0.07, 0.0), (-0.07, 0.0), (0.0, 0.08), (0.0, -0.08), (0.10, 0.05)):
            cand = hc + da * along + np.array([0.0, 0.0, dz]) - out * max(bar, 0.015)
            cpre = cand + out * 0.10
            for close in ((0, 0, 1.0), along):
                Rc = gripper_rot(-out, close)
                park = find_park(rig.kin, rig.world, [(cpre, Rc), (cand + out * 0.004, Rc)], near=rig.base_pose(),
                                 max_tries=80, q_start=rig.q_cmd, travel_q=rig.kin.rest)
                if park is not None:
                    panel, pre, R = cand, cpre, Rc
                    break
            if park is not None:
                break
        if park is None:
            raise SkillFailure(f"knock {name}: no reach to the panel (rejected: {_park_diag()})")
        skills._goto_park(rig, park)
        rig.grip(0.0, 30)
        rig.move_to(pre, R, label="knock_pre", q_hint=park[3][0])
        q0 = rig.joint(name)
        hits = 0
        for _ in range(int(taps)):
            rig.move_to(panel + out * 0.004, R, step=0.004, label="knock_tap", collision=False)
            tcp, _ = rig.kin.tcp(rig.q())
            gap = float((tcp - panel) @ out)
            if gap < 0.02:
                hits += 1
                rig.log("knock_contact", articulated=name, gap_m=round(gap, 4))
            rig.move_to(panel + out * 0.06, R, step=0.006, label="knock_back", collision=False)
        rig.move_to(pre, R, label="knock_retract", collision=False)
        rig.grip(0.04, 60)
        moved = abs(rig.joint(name) - q0)
        rig.log("knock_result", articulated=name, hits=hits, joint_moved=round(moved, 4))
        if hits < int(taps) or moved > 0.05:
            raise SkillFailure(f"knock {name}: {hits} contacts, joint moved {moved:.3f}")
        return {"taps": hits}


class TouchObjectPolicy(AtomicPolicy):
    def execute(self, name):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("touch: the right hand holds an object")
        st = rig.state()
        b = rig.geo.bottom(name, st)
        top = b[2] + rig.ann.asset_of(rig.ann.objects[name])["size"][2]
        c = rig.geo.centre(name, st)
        # closed pad tips sit ~1.8 cm below the TCP
        contact = np.array([c[0], c[1], top + 0.016])
        pre = contact + np.array([0, 0, 0.08])
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        park = None
        for d in ((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)):
            R = gripper_rot([0, 0, -1.0], [d[0], d[1], 0.0])
            park = find_park(rig.kin, rig.world, [(pre, R), (contact, R)], near=rig.base_pose(), max_tries=80,
                             q_start=rig.q_cmd, travel_q=skills._travel_q(rig))
            if park is not None:
                break
        if park is None:
            raise SkillFailure(f"touch {name}: no reach above it (rejected: {_park_diag()})")
        skills._goto_park(rig, park)
        rig.grip(0.0, 30)
        p0 = rig.obj_pose(name)[0]
        rig.move_to(pre, R, label="touch_pre", q_hint=park[3][0])
        rig.move_to(contact, R, step=0.002, steps_per_wp=4, label="touch_down", collision=False)
        tcp, _ = rig.kin.tcp(rig.q())
        rig.log("touch_contact", obj=name, tcp_above_top=round(float(tcp[2] - top), 4))
        rig.move_to(pre, R, step=0.006, label="touch_up", collision=False)
        rig.grip(0.04, 60)
        moved = float(np.linalg.norm(rig.obj_pose(name)[0] - p0))
        return {"moved_m": moved}


class PlanSquareYawPolicy(AtomicPolicy):
    def execute(self, name):
        st = self.rig.state()
        w, x, y, z = st["objects"][name]["quat"]
        yaw = math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
        err = (yaw + 45) % 90 - 45
        b = self.rig.geo.bottom(name, st)
        return {"degrees": float(-err), "xy": [float(b[0]), float(b[1])]}


class SweepTogetherPolicy(AtomicPolicy):
    """Push each listed object toward the group centroid (farthest first)."""

    def execute(self, names, *, radius_m=0.12, rounds=2):
        rig = self.rig
        if rig.held is not None:
            raise SkillFailure("sweep: the right hand holds an object")
        names = list(names)
        for _ in range(int(rounds)):
            st = rig.state()
            pts = {n: rig.geo.bottom(n, st)[:2] for n in names}
            c = np.mean(list(pts.values()), axis=0)
            far = sorted(names, key=lambda n: -np.linalg.norm(pts[n] - c))
            if np.linalg.norm(pts[far[0]] - c) <= radius_m * 0.8:
                break
            for n in far:
                d = c - pts[n]
                dist = float(np.linalg.norm(d))
                if dist <= radius_m * 0.6:
                    continue
                s = rig.geo.support_under(n, rig.state())
                if s is None:
                    raise SkillFailure(f"sweep: {n} is not on a support")
                skills.push(rig, n, s, d / dist, dist - radius_m * 0.4, label="SWEEP")
        st = rig.state()
        pts = np.array([rig.geo.bottom(n, st)[:2] for n in names])
        worst = float(np.max(np.linalg.norm(pts - pts.mean(axis=0), axis=1)))
        rig.log("sweep_result", objects=names, max_from_centroid=round(worst, 3))
        return {"max_from_centroid_m": worst}


def _look(rig, target):
    from .perceive import LookAtPolicy
    return LookAtPolicy(rig).execute(target)


class IdentifyObjectPolicy(AtomicPolicy):
    def execute(self, name):
        _look(self.rig, name)
        a = self.rig.ann.asset_of(self.rig.ann.objects[name])
        rec = {"asset": self.rig.ann.objects[name]["asset"], "tags": a.get("tags", [])}
        _mem(self.rig, "identified")[name] = rec
        self.rig.log("identify_result", obj=name, **rec)
        return {"category": rec["asset"], "tags": rec["tags"]}


class MeasureObjectPolicy(AtomicPolicy):
    def execute(self, name):
        rig = self.rig
        _look(rig, name)
        st = rig.state()
        R = quat_R(st["objects"][name]["quat"])
        size = np.abs(R) @ np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
        rec = {"size_m": [round(float(v), 4) for v in size]}
        _mem(rig, "measured")[name] = rec
        rig.log("measure_result", obj=name, **rec)
        return rec


class CountCategoryPolicy(AtomicPolicy):
    def execute(self, category):
        from .perceive import drive_head
        rig = self.rig
        seen = set()
        for yaw in (-0.9, -0.3, 0.3, 0.9):
            drive_head(rig, yaw, 0.25, steps=60)
            st = rig.state()
            for n, o in rig.ann.objects.items():
                tags = set(rig.ann.asset_of(o).get("tags", [])) | {o["asset"]}
                if category in tags and project_to_head_camera(rig, rig.geo.centre(n, st), exclude=n)[0]:
                    seen.add(n)
        drive_head(rig, 0.0, 0.0, steps=40)
        _mem(rig, "counted")[category] = {"count": len(seen), "objects": sorted(seen)}
        for n in seen:
            memory(rig)["observed"][n] = rig.tick
        rig.log("count_result", category=category, count=len(seen), objects=sorted(seen))
        return {"count": len(seen), "objects": sorted(seen)}


class DipUtensilPolicy(AtomicPolicy):
    """Reuse the stirring geometry: put the tip at the container centre below
    the rim, hold, and lift it out."""

    def execute(self, tool, container):
        from .tooluse import StirContainerPolicy
        rig = self.rig
        res = StirContainerPolicy(rig).execute(tool, container, turns=0.0)
        return res

    # StirContainerPolicy with turns=0 dips without circling; it records the
    # inside-below-rim samples used to set memory["dipped"].


class SidestepPolicy(AtomicPolicy):
    def execute(self, left_m):
        rig = self.rig
        x, y, yaw = rig.base_pose()
        d = float(left_m)
        tx, ty = x - math.sin(math.radians(yaw)) * d, y + math.cos(math.radians(yaw)) * d
        rig.sync_world()
        for u in np.linspace(0.1, 1.0, 6):
            if not rig.world.footprint_clear(x + (tx - x) * u, y + (ty - y) * u, math.radians(yaw)):
                raise SkillFailure("sidestep: the way is blocked")
        if rig.held is not None:
            skills.check_held(rig, "sidestep_start")
            rig.drive_base([(tx, ty, yaw)], speed=0.12, turn=0.3, ramp=1.0)
            skills.check_held(rig, "sidestep_end")
        else:
            rig.drive_base([(tx, ty, yaw)], speed=0.2)
        return {"base_pose": list(rig.base_pose())}


class HoverOverPolicy(AtomicPolicy):
    """Hold the carried object centred 6 cm above a target's top."""

    def execute(self, name, target, *, clearance_m=0.06):
        rig = self.rig
        if rig.held is None or rig.held["name"] != name:
            raise SkillFailure(f"hover {name}: not right-held")
        from .tooluse import stow_load
        stow_load(rig)
        st = rig.state()
        kind, rec = entity_kind(rig.ann, target)
        if kind == "object":
            t = np.asarray(rig.geo.bottom(target, st), float)
            a = rig.ann.asset_of(rec)
            top = t[2] + (a["container"]["rim_height"] if a.get("container") else a["size"][2])
            c = t[:2]
        else:
            p = entity_point(rig, target, st)
            top, c = p[2], p[:2]
        tcp, R = rig.kin.tcp(rig.q_cmd)
        body, _ = rig.obj_pose(name)
        hang = float(body[2] - skills._lowest_z(rig, name, st))
        b_now = rig.geo.bottom(name, st)
        off = tcp - np.r_[b_now[:2], b_now[2]]
        goal = np.r_[c, top + clearance_m] + off
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        park = find_park(rig.kin, rig.world, [(goal + np.array([0, 0, 0.05]), R), (goal, R)], near=rig.base_pose(),
                         max_tries=150, q_start=rig.q_cmd, travel_q=skills._travel_q(rig))
        if park is None:
            raise SkillFailure(f"hover {name}: no base pose above {target} (rejected: {_park_diag()})")
        skills._goto_park(rig, park)
        low = float(rig.geo.bottom(name, rig.state())[2])
        if low < top + clearance_m:
            t0, R0 = rig.kin.tcp(rig.q_cmd)
            rig.move_to(t0 + np.array([0, 0, top + clearance_m + 0.05 - low]), R0, step=0.005, label="hover_lift",
                        collision=False)
        rig.move_to(goal + np.array([0, 0, 0.05]), R, step=0.005, label="hover_above", collision=False, smooth=True)
        rig.move_to(goal, R, step=0.004, label="hover_settle", collision=False, smooth=True)
        skills.check_held(rig, "hover")
        rig.step(30)
        return {"bottom_above_target_m": float(rig.geo.bottom(name, rig.state())[2] - top), "hang_m": hang}
