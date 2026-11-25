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
from ..clearance import FREE, FREE_ELSE_STRAIGHT, LEGACY
from ..evaluator import quat_R
from ..kinematics import gripper_rot
from ..perception import project_to_head_camera
from ..physics import PHYSICS_HZ
from ..planner import find_park
from ..predicates import entity_kind, entity_point, memory
from ..rig import SkillFailure
from ..tolerances import COUNT_YAWS


def _park_diag():
    from ..planner import LAST_PARK_DIAG
    return {k: v for k, v in LAST_PARK_DIAG.items() if v}


def _mem(rig, key):
    return memory(rig).setdefault(key, {})


class ShakeHeldPolicy(AtomicPolicy):
    def execute(self, name, *, cycles=3, amplitude=0.02):
        rig = self.rig
        skills.right_hand_only(rig, name, "shake")
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
                rig.move_to(tcp + s * amplitude * lat, R, step=0.004, steps_per_wp=3, label="shake",
                            allow=FREE_ELSE_STRAIGHT)
            skills.check_held(rig, "shake")
            done += 1
        rig.move_to(tcp, R, step=0.004, label="shake_end", allow=FREE_ELSE_STRAIGHT)
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
        self.rig.step(int(round(s * PHYSICS_HZ)))
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
                rig.move_to(centre + sgn * 0.10 * lat, R, step=0.01, steps_per_wp=2, label="wave_swing",
                            allow=FREE_ELSE_STRAIGHT)
            n += 1
        _mem(rig, "gestures")["wave"] = n
        rig.log("wave_result", swings=n)
        rig.tuck()
        return {"swings": n}


class NodHeadPolicy(AtomicPolicy):
    def execute(self, *, times=2, depth=0.35):
        from ..skill_jobs.look import drive_head
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
    """Tap the closed panel of a door / drawer ``taps`` times beside its handle: the knock skill
    (skill_jobs.press.knock_job, plan_press; HAND_PLAN 9g) once per tap, with the empty hand."""

    def execute(self, name, *, taps=2):
        from ..motion_skills import SKILLS, run_skill
        for _ in range(int(taps)):
            run_skill(self.rig, SKILLS["knock"], {"name": name})
        return {"taps": int(taps)}


class TouchObjectPolicy(AtomicPolicy):
    """Touch an object's top with the closed fingertips: the touch skill (skill_jobs.press.touch_job, plan_press;
    HAND_PLAN 9g) with the empty hand."""

    def execute(self, name):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["touch"], {"name": name})


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
        from ..skill_jobs.slide import push_object
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
                push_object(rig, n, s, [(d / dist, dist - radius_m * 0.4, None)], label="SWEEP")
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
        from .perceive import look
        rig = self.rig
        seen = set()

        def count(r, what):
            st = r.state()
            for n, o in r.ann.objects.items():
                tags = set(r.ann.asset_of(o).get("tags", [])) | {o["asset"]}
                if category in tags and project_to_head_camera(r, r.geo.centre(n, st), exclude=n)[0]:
                    seen.add(n)
        look(rig, [("head", yaw, 0.25, 60) for yaw in COUNT_YAWS], label=f"count_{category}", on_view=count)
        look(rig, [("head", 0.0, 0.0, 40)], label=f"count_{category}_home")
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
        if rig.held is not None:
            skills.check_held(rig, "sidestep_start")
            skills.straight_base_move(rig, (tx, ty, yaw), "sidestep")
            skills.check_held(rig, "sidestep_end")
        else:
            skills.straight_base_move(rig, (tx, ty, yaw), "sidestep")
        return {"base_pose": list(rig.base_pose())}


class HoverOverPolicy(AtomicPolicy):
    """Hold the carried object centred 6 cm above a target's top: the hover skill (skill_jobs.drop.hover_job,
    skill_plans.plan_hover -- the drop without the release; HAND_PLAN 9e) with the hand that holds it."""

    def execute(self, name, target):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["hover"], {"name": name, "target": target})
