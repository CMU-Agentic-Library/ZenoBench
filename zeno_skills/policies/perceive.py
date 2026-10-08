"""Head-camera and gesture policies.

policy_068 LookAtPolicy        aim head yaw/pitch at a target; record what is in view
policy_069 ExploreRoomPolicy   visit stand-off poses in a room and sweep the head
policy_070 SearchObjectPolicy  visit candidate supports/cabinets in order until the object is seen
policy_071 PointAtPolicy       point the closed right fingers at a target
policy_072 PresentHeldPolicy   hold the carried object in front of the head camera
policy_088 InspectReceptaclePolicy  look into a container, cabinet or appliance and list contents

Visibility is the geometric test in perception.project_to_head_camera; with
``first_person=True`` the policies also store the RGB frame in the event log
directory (rig.memory["frames"]).
"""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..kinematics import gripper_rot
from ..perception import HEAD_LIMITS, look_angles, project_to_head_camera
from ..predicates import (entity_footprint, entity_kind, entity_point, memory, objects_inside,
                          objects_on_support)
from ..rig import SkillFailure


def drive_head(rig, yaw, pitch, steps=90):
    rig.head_cmd = np.array([float(yaw), float(pitch)])
    for _ in range(steps // 10):
        rig.step(10)
        hq = rig.head_q()
        if abs(hq["head_yaw_joint"] - yaw) < 0.02 and abs(hq["head_pitch_joint"] - pitch) < 0.02:
            break


def record_view(rig):
    """Mark every annotated object, support and articulated part in view as observed."""
    mem = memory(rig)
    st = rig.state()
    seen = []
    for name in rig.ann.objects:
        if project_to_head_camera(rig, rig.geo.centre(name, st), exclude=name)[0]:
            mem["observed"][name] = rig.tick
            seen.append(name)
    for a in rig.ann.articulated:
        if project_to_head_camera(rig, entity_point(rig, a["name"], st), exclude=a["name"])[0]:
            mem["observed"][a["name"]] = rig.tick
    if getattr(rig, "first_person_camera", None) is not None:
        mem.setdefault("frames", []).append({"tick": rig.tick, "image": rig.get_first_person_image()})
    return seen


class LookAtPolicy(AtomicPolicy):
    """Aim the head camera at a target; turn the base first if the bearing
    exceeds the head yaw range."""

    def execute(self, target):
        rig = self.rig
        p = entity_point(rig, target)
        yaw, pitch = look_angles(rig, p)
        if abs(yaw) >= HEAD_LIMITS["head_yaw_joint"][1] - 0.02:
            from .base_motion import FaceTargetPolicy
            FaceTargetPolicy(rig).execute(target)
            yaw, pitch = look_angles(rig, p)
        drive_head(rig, yaw, pitch)
        ok, detail = project_to_head_camera(rig, p, exclude=target)
        seen = record_view(rig)
        rig.log("look_result", target=target, visible=ok, detail=detail, seen=seen)
        if not ok:
            raise SkillFailure(f"look at {target}: {detail}")
        memory(rig)["observed"][target] = rig.tick
        return {"visible": True, "seen": seen}


class ExploreRoomPolicy(AtomicPolicy):
    """Cover a room: from up to ``max_views`` stand-off poses sweep the head
    left/centre/right; coverage = fraction of the room's supports and objects seen."""

    def execute(self, room, *, max_views=6, min_spacing=1.6):
        rig = self.rig
        from ..evaluator import room_of
        from .base_motion import standoff_poses
        kind, _ = entity_kind(rig.ann, room)
        if kind != "room":
            raise SkillFailure(f"explore {room}: not a room")
        st = rig.state()
        targets = {}
        # visible horizontal surfaces (furniture tops between 0.3 and 1.6 m) and every object
        for s_ in rig.ann.supports:
            x0, y0, x1, y1 = s_["aabb_xy"]
            c = ((x0 + x1) / 2, (y0 + y1) / 2)
            if room_of(rig.ann.rooms, c) == room and (x1 - x0) * (y1 - y0) > 0.05 and 0.3 <= s_["z"] <= 1.6 \
                    and s_.get("clearance", 1.0) >= 0.3:
                targets["support:" + s_["name"]] = np.array([c[0], c[1], s_["z"]])
        for n in rig.ann.objects:
            c = rig.geo.centre(n, st)
            if room_of(rig.ann.rooms, c[:2]) == room:
                targets[n] = c
        if not targets:
            raise SkillFailure(f"explore {room}: nothing annotated in the room")
        poses = standoff_poses(rig, room)
        if not poses:
            raise SkillFailure(f"explore {room}: no free viewpoint")
        # farthest-point sampling over free poses spreads the viewpoints
        chosen = [poses[0]]
        while len(chosen) < max_views:
            best = max(poses, key=lambda p: min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in chosen))
            if min(math.hypot(best[0] - q[0], best[1] - q[1]) for q in chosen) < min_spacing:
                break
            chosen.append(best)
        # visit in a greedy nearest-next order
        x, y, _ = rig.base_pose()
        order, rest = [], list(chosen)
        while rest:
            nxt = min(rest, key=lambda p: math.hypot(p[0] - x, p[1] - y))
            order.append(nxt)
            rest.remove(nxt)
            x, y = nxt[0], nxt[1]
        seen = set()
        visited = 0
        for pose in order:
            try:
                skills.navigate(rig, pose, label=f"explore_{room}")
            except SkillFailure as exc:
                rig.log("explore_skip", pose=[round(v, 2) for v in pose], reason=str(exc))
                continue
            visited += 1
            for turn in (0.0, 180.0):           # look both ways from each viewpoint
                if turn:
                    bx, by, byaw = rig.base_pose()
                    rig.sync_world()
                    if not rig.world.footprint_clear(bx, by, math.radians(byaw + turn)):
                        continue
                    rig.drive_base([(bx, by, byaw + turn)])
                for yaw in (-1.0, -0.5, 0.0, 0.5, 1.0):
                    drive_head(rig, yaw, 0.3, steps=50)       # positive pitch looks down
                    record_view(rig)
                    for k, p in targets.items():
                        if k not in seen and project_to_head_camera(rig, p, exclude=k.split(":", 1)[-1])[0]:
                            seen.add(k)
        drive_head(rig, 0.0, 0.0)
        cov = len(seen) / len(targets)
        memory(rig)["explored"][room] = max(cov, memory(rig)["explored"].get(room, 0.0))
        rig.log("explore_result", room=room, coverage=round(cov, 3), views=visited, targets=len(targets))
        if cov < 0.75:
            raise SkillFailure(f"explore {room}: coverage {cov:.2f}")
        return {"coverage": cov, "seen": sorted(k for k in seen if not k.startswith("support:"))}


class SearchObjectPolicy(AtomicPolicy):
    """Look for an object at candidate places in order of distance until it is
    seen.  Candidates are the supports and container interiors of the region
    (a room, or the robot's room).  Closed cabinets are opened, inspected and
    closed again."""

    def execute(self, name, region=None, *, max_places=8):
        rig = self.rig
        from ..evaluator import room_of
        from .base_motion import NavigateToPlacePolicy
        x, y, _ = rig.base_pose()
        room = region or room_of(rig.ann.rooms, (x, y))
        st = rig.state()
        furniture = {}
        for s in rig.ann.supports:
            x0, y0, x1, y1 = s["aabb_xy"]
            c = ((x0 + x1) / 2, (y0 + y1) / 2)
            if room_of(rig.ann.rooms, c) == room:
                f = s.get("furniture") or s["name"]
                furniture.setdefault(f, []).append(s)
        order = sorted(furniture, key=lambda f: min(
            math.hypot((s["aabb_xy"][0] + s["aabb_xy"][2]) / 2 - x, (s["aabb_xy"][1] + s["aabb_xy"][3]) / 2 - y)
            for s in furniture[f]))
        visited = []
        for f in order[:max_places]:
            visited.append(f)
            try:
                NavigateToPlacePolicy(rig).execute(f if f in {s.get("furniture") for s in rig.ann.supports}
                                                   else furniture[f][0]["name"], max_tries=3)
            except SkillFailure as exc:
                rig.log("search_skip", place=f, reason=str(exc))
                continue
            for s in sorted(furniture[f], key=lambda s: -s["z"]):
                x0, y0, x1, y1 = s["aabb_xy"]
                p = np.array([(x0 + x1) / 2, (y0 + y1) / 2, s["z"]])
                yaw, pitch = look_angles(rig, p)
                drive_head(rig, yaw, pitch, steps=60)
                record_view(rig)
                c = rig.geo.centre(name, rig.state())
                if project_to_head_camera(rig, c, exclude=name)[0]:
                    found = rig.geo.support_under(name, rig.state())
                    found_on = found["name"] if found else None
                    memory(rig)["observed"][name] = rig.tick
                    rig.log("search_result", obj=name, found_on=found_on, visited=visited)
                    return {"found_on": found_on, "visited": visited}
        raise SkillFailure(f"search {name}: not seen at {visited}")


class PointAtPolicy(AtomicPolicy):
    """Point the closed right fingers at a target from in front of the chest."""

    def execute(self, target):
        rig = self.rig
        p = entity_point(rig, target)
        x, y, yaw = rig.base_pose()
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        shoulder = np.array([x + 0.09 * c + 0.18 * s, y + 0.09 * s - 0.18 * c, 1.05])
        d = p - shoulder
        d /= np.linalg.norm(d)
        if d[:2] @ np.array([c, s]) < 0.2:
            from .base_motion import FaceTargetPolicy
            FaceTargetPolicy(rig).execute(target)
            return self.execute(target)
        side = np.cross(d, [0, 0, 1.0])
        side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-6 else np.array([0, 1.0, 0])
        R = gripper_rot(d, side)
        if rig.held is None:
            rig.grip(0.0, 40)
        last = None
        for reach in (0.45, 0.38, 0.52, 0.30):
            tcp = shoulder + d * reach
            try:
                rig.move_to(tcp, R, label="point", smooth=True)
                break
            except SkillFailure as exc:
                last = exc
        else:
            raise last
        tcp, R2 = rig.kin.tcp(rig.q())
        v = p - tcp
        ang = math.degrees(math.acos(np.clip((-R2[:, 2]) @ v / np.linalg.norm(v), -1, 1)))
        rig.log("point_result", target=target, angle_deg=round(ang, 2))
        if ang > 8.0:
            raise SkillFailure(f"point at {target}: {ang:.1f} deg off")
        return ang


class PresentHeldPolicy(AtomicPolicy):
    """Bring the right-held object in front of the body at eye level."""

    def execute(self, name):
        rig = self.rig
        if rig.held is None or rig.held["name"] != name:
            raise SkillFailure(f"present {name}: not right-held")
        x, y, yaw = rig.base_pose()
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        tcp, R = rig.kin.tcp(rig.q_cmd)
        body, _ = rig.obj_pose(name)
        off = tcp - body
        last = None
        for fwd, lat, z in ((0.55, -0.05, 1.10), (0.50, -0.15, 1.05), (0.60, 0.0, 1.00), (0.45, -0.10, 0.95)):
            goal = np.array([x + c * fwd - s * lat, y + s * fwd + c * lat, z]) + off
            try:
                rig.move_to(goal, R, step=0.005, steps_per_wp=5, label="present", smooth=True)
                break
            except SkillFailure as exc:
                last = exc
        else:
            raise last
        skills.check_held(rig, "present")
        centre = rig.geo.centre(name, rig.state())
        yaw_h, pitch_h = look_angles(rig, centre)
        drive_head(rig, yaw_h, pitch_h)
        record_view(rig)
        rig.log("present_result", obj=name, centre=np.round(centre, 3).tolist())
        return centre.tolist()


class InspectReceptaclePolicy(AtomicPolicy):
    """Look into a container, an open cabinet or an appliance and return what is inside."""

    def execute(self, receptacle):
        rig = self.rig
        kind, rec = entity_kind(rig.ann, receptacle)
        st = rig.state()
        if kind == "object":
            if not rig.ann.asset_of(rec).get("container"):
                raise SkillFailure(f"inspect {receptacle}: not a container")
            b = rig.geo.bottom(receptacle, st)
            p = np.array([b[0], b[1], b[2] + rig.ann.asset_of(rec)["container"]["rim_height"]])
            inside = objects_inside(rig, receptacle, st)
        elif kind == "articulated":
            box = rec.get("cavity_aabb") or rec.get("body_aabb")
            p = np.array([(box[0] + box[3]) / 2, (box[1] + box[4]) / 2, (box[2] + box[5]) / 2])
            inside = [n for n in rig.ann.objects
                      if all(box[i] < rig.geo.centre(n, st)[i] < box[i + 3] for i in range(3))]
            sups = [s["name"] for s in rig.ann.supports if s.get("furniture") == receptacle]
            for sname in sups:
                inside += [n for n in objects_on_support(rig, sname, st) if n not in inside]
        elif kind in ("support", "furniture", "appliance"):
            p = entity_point(rig, receptacle, st)
            inside = objects_on_support(rig, receptacle if kind != "appliance" else receptacle + "/top", st)
        else:
            raise SkillFailure(f"inspect {receptacle}: unsupported receptacle kind {kind}")
        yaw, pitch = look_angles(rig, p)
        if abs(yaw) >= HEAD_LIMITS["head_yaw_joint"][1] - 0.02:
            from .base_motion import FaceTargetPolicy
            FaceTargetPolicy(rig).execute(receptacle)
            yaw, pitch = look_angles(rig, p)
        drive_head(rig, yaw, pitch)
        ok, detail = project_to_head_camera(rig, p, exclude=receptacle)
        record_view(rig)
        visible = [n for n in inside if project_to_head_camera(rig, rig.geo.centre(n, rig.state()), exclude=n)[0]]
        mem = memory(rig)
        for n in visible:
            mem["observed"][n] = rig.tick
        mem["observed"][receptacle] = rig.tick
        mem.setdefault("contents", {})[receptacle] = visible
        rig.log("inspect_result", receptacle=receptacle, visible=ok, contents=visible, hidden=sorted(set(inside) - set(visible)))
        if not ok:
            raise SkillFailure(f"inspect {receptacle}: {detail}")
        return {"contents": visible}
