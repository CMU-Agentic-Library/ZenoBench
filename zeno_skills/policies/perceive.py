"""Head-camera policies: the task layer over the look skill (no motion entry of its own:
tests/test_layering.py).  Gestures: gestures.py.

policy_068 LookAtPolicy        aim head yaw/pitch at a target (the look skill); record what is in view
policy_069 ExploreRoomPolicy   visit stand-off poses in a room and sweep the head; counts furniture
policy_116 ExploreFurniturePolicy  aim the head at every support layer (shelf, top) of one piece of furniture
policy_117 ViewSupportPolicy  stand where one head camera frame holds a whole support surface, aim at it
policy_118 MarkSpotsPolicy    number free spots for the held object on the support in view (visual prompting)
policy_070 SearchObjectPolicy  visit candidate supports/cabinets in order until the object is seen
policy_088 InspectReceptaclePolicy  look into a container, cabinet or appliance and list contents (the inspect skill)

Visibility is the geometric test in perception.project_to_head_camera; with
``first_person=True`` the policies also store the RGB frame in the event log
directory (rig.memory["frames"]).
"""

from __future__ import annotations

import math

import numpy as np

from .base import AtomicPolicy
from .. import skills
from ..perception import project_to_head_camera, rig_head_pose
from ..predicates import entity_footprint, entity_kind, entity_point, memory
from .. import viewpoints
from ..rig import SkillFailure
from ..tolerances import (COVER_MIN_AREA, COVER_MIN_CLEARANCE, COVER_OK, COVER_Z, LOOK_STEPS, SEARCH_AIM_SPACING_M,
                          SEARCH_STEPS, SWEEP_PITCH, SWEEP_STEPS, SWEEP_YAWS, VIEW_TURNS)

# Exploration and search: what counts, when it succeeds, and the sweep's angles and ticks are in tolerances
# (inherited, unmeasured: docs/motion/COLLISION_PLAN.md §8).  Every head motion here is a look (run_skill: the look
# skill's plan of head segments, skill_plans/look.py); these policies are the task layer that chooses where
# to stand and what to aim at, and judges what was seen.
DRIVE_TRIES = 3            # stand-offs of one piece viewpoints.drivable is asked about (each plans a drive): a budget
SWEEP = tuple(("head", y, SWEEP_PITCH, SWEEP_STEPS) for y in SWEEP_YAWS)
HEAD_HOME = (("head", 0.0, 0.0, LOOK_STEPS),)


def look(rig, aims, face=None, label="look", on_view=None):
    """Run the look skill (motion_skills.run_skill): [the base turned to heading ``face``], then the head at
    each of ``aims`` (skill_plans.look.head_aims); ``on_view(rig, what)`` after each head segment."""
    from ..motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS["look"], {"aims": list(aims), "face": face, "label": label, "on_view": on_view})


def torso(rig, skill, target, as_far=False):
    """Run a posture skill on the torso lift (crouch down, stand back up: motion_skills.run_skill) to ``target``
    m -- or (``as_far``) as far toward it as both arms ride the body free -- the arms riding the body as they
    are; SkillFailure where it cannot be made."""
    from ..motion_skills import SKILLS, run_skill
    return run_skill(rig, SKILLS[skill], {"joint": "torso_lift_joint", "target": float(target), "as_far": as_far})


def aim_at(name, p, steps=LOOK_STEPS):
    return ("point", name, [float(v) for v in p], int(steps))


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
    if getattr(rig, "first_person_camera", None) is not None and not getattr(rig, "observer", None):
        mem.setdefault("frames", []).append({"tick": rig.tick, "image": rig.get_first_person_image()})
    if getattr(rig, "observer", None) is not None:
        rig.observer.on_view(seen)      # the observation-limited benchmark keeps its own cache
    return seen


class LookAtPolicy(AtomicPolicy):
    """Aim the head camera at a target: the look skill (skill_jobs.look.look_job -- the base turned toward
    it first when its bearing is past the head's yaw range, the result judged and recorded there)."""

    def execute(self, target):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["look"], {"target": target})


class ExploreRoomPolicy(AtomicPolicy):
    """Cover a room: coverage = fraction of the room's furniture (and, outside the benchmark, objects)
    seen.  A piece of furniture counts once, as soon as one of its support layers is in view; every layer
    is explore_furniture's job.

    The viewpoints are decided first, from one goal set: the room's own spots and the stand-offs of its
    furniture (base_motion.standoff_poses), those the base can get to (one base_reachable field), each with
    the targets predicted in view from it; then a greedy cover (viewpoints.cover_views) -- the viewpoint that adds the
    most targets not covered yet, the nearer on a tie -- up to ``max_views``.  At each: navigate there, a
    look at the targets it was chosen for and a sweep (SWEEP), and a look the other way (VIEW_TURNS: the
    base turned, a sweep).  Before each drive and each turn, viewpoints.drivable: a viewpoint navigate cannot
    get to is replaced, for the targets only it was to see, by the best other one of the goal set (cover_views
    again, the rest excluded); a turn it cannot make is not looked from (the coverage decides).  A drive or a
    turn that fails fails the exploration."""

    def execute(self, room, *, max_views=6):
        rig = self.rig
        from ..evaluator import room_of
        from .base_motion import standoff_poses
        kind, _ = entity_kind(rig.ann, room)
        if kind != "room":
            raise SkillFailure(f"explore {room}: not a room")
        st = rig.state()
        # target -> [(point, name the point belongs to)]: a piece of furniture is seen when any of
        # its visible horizontal surfaces (support layers between 0.3 and 1.6 m) is, an object when its centre is
        targets = {}
        for s_ in rig.ann.supports:
            x0, y0, x1, y1 = s_["aabb_xy"]
            c = ((x0 + x1) / 2, (y0 + y1) / 2)
            if room_of(rig.ann.rooms, c) == room and (x1 - x0) * (y1 - y0) > COVER_MIN_AREA and COVER_Z[0] <= s_["z"] <= COVER_Z[1] \
                    and s_.get("clearance", 1.0) >= COVER_MIN_CLEARANCE:
                targets.setdefault("furniture:" + s_["furniture"], []).append(
                    (np.array([c[0], c[1], s_["z"]]), s_["name"]))
        if not getattr(rig, "static_explore", False):
            # (the observation-limited benchmark covers the static layout only:
            # the hidden object list must not shape the route or the coverage)
            for n in rig.ann.objects:
                c = rig.geo.centre(n, st)
                if room_of(rig.ann.rooms, c[:2]) == room:
                    targets[n] = [(c, n)]
        if not targets:
            raise SkillFailure(f"explore {room}: nothing annotated in the room")
        if rig.held is not None:
            # the viewpoints are checked in the posture the drives carry the load in (as navigate_place does)
            from ..skill_jobs.carry import carry_posture
            carry_posture(rig, min_bottom_z=None)
        # one goal set: the room's spots and its furniture's stand-offs (1116 T26 two_bedrooms: the base gets
        # into bedroom_0_0 only by its door, 59 of its 1780 free cells, where none of the ring spots lies but
        # furniture stand-offs do)
        furn = sorted({k.split(":", 1)[1] for k in targets if k.startswith("furniture:")})
        cands = list(dict.fromkeys(list(standoff_poses(rig, room)) + [p for f in furn for p in standoff_poses(rig, f)]))
        if not cands:
            raise SkillFailure(f"explore {room}: no free viewpoint")
        ok = skills.base_reachable(rig, cands)
        reach = [p for p, o in zip(cands, ok) if o]
        # the greedy cover, decided before the robot moves (docs rule 8)
        chosen, pred = viewpoints.cover_views(rig, reach, targets, max_views)
        rig.log("explore_goals", room=room, goals=len(cands), reachable=len(reach), seeing=len(pred))
        if not chosen:
            raise SkillFailure(f"explore {room}: no viewpoint the base can get to sees any of it "
                               f"({len(reach)} of {len(cands)} reachable)")
        covered = set().union(*(set(pred[p]) for p in chosen))
        rig.log("explore_views", room=room, views=[[round(v, 2) for v in p] for p in chosen],
                predicted=len(covered), targets=len(targets))
        seen, viewed = set(), set()

        def mark(r, what):
            viewed.update(record_view(r))
            for k, pts in targets.items():
                if k not in seen and any(project_to_head_camera(r, p, exclude=n)[0] for p, n in pts):
                    seen.add(k)

        queue, visited, skipped = list(chosen), [], []
        while queue and len(visited) < max_views:
            pose = queue.pop(0)
            if not viewpoints.drivable(rig, pose):
                # another viewpoint of the goal set for what only this one was to see (rule 3: not a fallback)
                skipped.append(pose)
                later = set().union(*(set(pred[q]) for q in queue))
                missing = {k: targets[k] for k in pred[pose] if k not in seen and k not in later}
                rest = [q for q in reach if q not in skipped and q not in visited and q not in queue]
                budget = max_views - len(visited) - len(queue)
                alt, apred = viewpoints.cover_views(rig, rest, missing, budget) \
                    if missing and budget > 0 and len(skipped) <= 2 * max_views else ([], {})
                rig.log("explore_skip", room=room, pose=[round(v, 2) for v in pose], reason="no base path",
                        instead=[[round(v, 2) for v in q] for q in alt])
                pred.update(apred)
                queue[:0] = alt
                continue
            i = len(visited)
            visited.append(pose)
            skills.navigate(rig, pose, label=f"explore_{room}", raise_load=rig.held is None)
            aims = [aim_at(k, p) for k, p in pred[pose].items() if k not in seen]
            look(rig, aims + list(SWEEP), label=f"explore_{room}_{i}", on_view=mark)
            x, y, heading = rig.base_pose()
            for t, turn in enumerate(VIEW_TURNS[1:]):
                if not viewpoints.drivable(rig, (x, y, heading + turn)):
                    rig.log("explore_skip", room=room, pose=[round(x, 2), round(y, 2), round(heading + turn, 1)],
                            reason="no base path to turn round")
                    continue
                look(rig, SWEEP, face=heading + turn, label=f"explore_{room}_{i}_back{t}", on_view=mark)
        look(rig, HEAD_HOME, label=f"explore_{room}_home")
        cov = len(seen) / len(targets)
        memory(rig)["explored"][room] = max(cov, memory(rig)["explored"].get(room, 0.0))
        furniture = sorted(k.split(":", 1)[1] for k in seen if k.startswith("furniture:"))
        rig.log("explore_result", room=room, coverage=round(cov, 3), views=len(visited), targets=len(targets),
                furniture=furniture)
        if cov < COVER_OK:
            raise SkillFailure(f"explore {room}: coverage {cov:.2f}")
        # every object that came into view (the coverage targets hold no objects in the benchmark)
        objects = viewed | {k for k in seen if not k.startswith("furniture:")}
        return {"coverage": cov, "seen": sorted(objects),
                "furniture": furniture}


def _board_blocks(cam, point, layers, thick=0.02):
    """A board of the furniture (top or bottom face of a layer) between the camera and ``point``.
    project_to_head_camera ignores the furniture's own boards: a shelf seen through the shelf
    above it, or a top above the camera seen from below, would count otherwise."""
    for layer in layers:
        x0, y0, x1, y1 = layer["aabb_xy"]
        for z in (layer["z"], layer["z"] - thick):
            if (cam[2] - z) * (point[2] - z) >= 0:
                continue
            t = (cam[2] - z) / (cam[2] - point[2])
            x, y = cam[0] + t * (point[0] - cam[0]), cam[1] + t * (point[1] - cam[1])
            if x0 < x < x1 and y0 < y < y1:
                return True
    return False


class ExploreFurniturePolicy(AtomicPolicy):
    """Look at every support layer of one piece of furniture (each shelf, the top,
    a cabinet's inside shelves): a look at each layer not seen yet from where the robot stands when it is
    already near, else from up to ``max_views`` stand-off poses the base can get to and the furniture is in
    view from (navigate_place's goal set, viewpoints.reachable_in_view), at least ``min_spacing`` apart, and
    again with the torso lowered (empty hand only) for the layers still hidden, e.g. a bottom shelf behind
    the front edge of the shelf above it.  A layer is seen when the space just above its board is in the
    head camera and no board of the furniture is in the way.  Succeeds only when every layer was seen; a
    closed cabinet door hides its inside layers.  A stand-off viewpoints.drivable rejects is passed over for the
    next (rule 3: another goal of the set); a drive that fails fails it."""

    def execute(self, furniture, *, max_views=3, min_spacing=0.4):
        rig = self.rig
        from .base_motion import standoff_poses
        from ..predicates import NEAR_M
        layers = sorted((s_ for s_ in rig.ann.supports if s_.get("furniture") == furniture), key=lambda s_: s_["z"])
        if not layers:
            raise SkillFailure(f"explore {furniture}: no support layers annotated")
        targets = {s_["name"]: viewpoints.layer_point(s_) for s_ in layers}
        seen, objects = set(), set()

        def mark(r, what):
            objects.update(record_view(r))
            cam = rig_head_pose(r)[0]
            seen.update(n for n, q in targets.items() if n not in seen
                        and project_to_head_camera(r, q, exclude=n)[0] and not _board_blocks(cam, q, layers))

        def look_once(label):
            aims = [aim_at(n, p) for n, p in targets.items() if n not in seen]
            if aims:
                look(rig, aims, label=label, on_view=mark)

        def sweep(label):
            look_once(label)
            if len(seen) == len(targets) or rig.held is not None:
                return
            # the crouch: the posture skills (9.3 step 5), the torso as low as it goes -- toward its limit, as far as
            # both arms ride the body free (the left arm's fold meets the chassis first) -- and back to where it
            # was.  A crouch that cannot be made here fails the exploration (docs rule 3; it used to be logged as
            # explore_crouch_skip and the layers left unseen)
            idx = rig.kin.names.index("torso_lift_joint")
            q0 = min(max(float(rig.q()[idx]), float(rig.kin.lo[idx])), float(rig.kin.hi[idx]))   # measured: may sit past a limit
            try:
                torso(rig, "crouch", rig.kin.lo[idx], as_far=True)
                look_once(label + "_low")
            finally:
                look(rig, HEAD_HOME, label=label + "_home")
                torso(rig, "stand", q0)

        box = entity_footprint(rig, furniture)
        x, y, _ = rig.base_pose()
        here = math.hypot(max(box[0] - x, 0.0, x - box[2]), max(box[1] - y, 0.0, y - box[3])) <= NEAR_M
        views = []
        if here:
            sweep(f"explore_{furniture}_here")
            views.append((x, y))
        if len(seen) < len(targets):
            if rig.held is not None:
                # the stand-offs are checked in the posture the drives carry the load in (as navigate_place)
                from ..skill_jobs.carry import carry_posture
                carry_posture(rig, min_bottom_z=None)
            # the views are one goal set, as navigate_place has it: the stand-offs the base can get to (one
            # base_reachable field) the furniture is in view from (its top or any layer, the head aimed as look
            # aims it: walls and furniture boxes), nearest first
            poses = standoff_poses(rig, furniture)
            reach, cands = viewpoints.reachable_in_view(rig, {furniture: poses})[furniture]
            rig.log("explore_furniture_goals", furniture=furniture, goals=len(poses), reachable=len(reach),
                    in_view=len(cands))
        else:
            cands = []
        skipped = 0
        for pose in cands:
            if len(seen) == len(targets) or len(views) - here >= max_views:
                break
            if any(math.hypot(pose[0] - vx, pose[1] - vy) < min_spacing for vx, vy in views):
                continue
            if skipped >= 2 * max_views:
                break
            if not viewpoints.drivable(rig, pose):
                # the next stand-off of the goal set (rule 3: not a fallback)
                skipped += 1
                rig.log("explore_skip", furniture=furniture, pose=[round(v, 2) for v in pose], reason="no base path")
                continue
            skills.navigate(rig, pose, label=f"explore_{furniture}", raise_load=rig.held is None)
            views.append(tuple(rig.base_pose()[:2]))
            sweep(f"explore_{furniture}_{len(views)}")
        look(rig, HEAD_HOME, label=f"explore_{furniture}_end")
        cov = len(seen) / len(targets)
        memory(rig)["explored"][furniture] = max(cov, memory(rig)["explored"].get(furniture, 0.0))
        missing = [n for n in targets if n not in seen]
        rig.log("explore_furniture_result", furniture=furniture, layers=len(targets), seen=sorted(seen),
                missing=missing, views=len(views))
        if missing:
            raise SkillFailure(f"explore {furniture}: layers not seen {missing}")
        return {"seen": sorted(objects), "layers": sorted(seen)}


class ViewSupportPolicy(AtomicPolicy):
    """See a whole support surface clearly in one or two head camera frames: of the stand-off poses navigate
    uses (base_motion.standoff_poses: within base_near of it) the base can get to, and the pose the robot stands
    at, the views visual_prompt.support_views picks (one that resolves the most of its top, a second for what
    is still unseen: a long table's far half), judged with the torso up (each view is taken standing: stand,
    as high as both arms ride it free).  At each view: drive there (a load carried as navigate carries it),
    stand, aim the head at the view's point (look), and keep the frame with its camera (rig.memory
    ["view_frames"]: mark_spots draws on these).  Ends at the last view, the head aimed (its frame is the
    next observation's plain head image).  A task layer: the robot moves only by run_skill (navigate, stand,
    look)."""

    def execute(self, support):
        rig = self.rig
        from .base_motion import _box_dist, standoff_poses
        from ..predicates import NEAR_M
        from ..skill_jobs.carry import _carry_bottom_z
        from ..viewpoints import support_views, travel_tw
        from ..visual_prompt import camera_frame
        s = rig.ann.support(support)
        min_bottom_z = _carry_bottom_z(rig, support) if rig.held is not None else None
        idx = rig.kin.names.index("torso_lift_joint")
        top = float(rig.kin.hi[idx])
        tw = dict(travel_tw(rig), torso_lift_joint=top)          # where the camera will be: standing
        here = tuple(rig.base_pose())
        poses = standoff_poses(rig, support)
        ok = skills.base_reachable(rig, poses) if poses else []
        reach = [p for p, o in zip(poses, ok) if o]
        near = _box_dist(entity_footprint(rig, support), here[:2]) <= NEAR_M
        views, seen = support_views(rig, s, reach, tw, here=here if near else None)
        rig.log("view_support_goals", support=support, goals=len(poses), reachable=len(reach), seen=round(seen, 3),
                views=[{"pose": [round(v, 3) for v in p], "aim": np.round(a, 3).tolist(), "sees": int(m.sum())}
                       for p, a, m in views])
        if not views:
            raise SkillFailure(f"view {support}: no base path to any stand-off pose")
        mem = memory(rig)
        mem["view_frames"] = []
        for k, (pose, aim, _) in enumerate(views):
            if k > 0 or pose != here:
                rig.caption = f"VIEW {support}"
                skills.navigate(rig, pose, label=f"view_{support}", min_bottom_z=min_bottom_z,
                                raise_load=rig.held is None)
            torso(rig, "stand", top, as_far=True)
            look(rig, [aim_at(support, aim)], label=f"view_{support}")
            record_view(rig)
            frame = camera_frame(rig)
            if frame is not None:
                mem["view_frames"].append(dict(zip(("image", "K", "pos", "R_ros"), frame)))
            rig.log("view_support", support=support, view=k + 1, pose=[round(v, 3) for v in rig.base_pose()],
                    torso=round(float(rig.q()[idx]), 3), head=[round(v, 3) for v in rig.head_q().values()])
        return {"coverage": round(seen, 3)}


class MarkSpotsPolicy(AtomicPolicy):
    """Number free spots for the held object on a support in the views view_support took (rig.memory
    ["view_frames"]; without them, the head camera's current view): visual_prompt.mark_spots.  The drawn frames
    wait in rig.memory["visual_prompt"] for the next observation (episode.Episode.observation adds them to the
    images, once).  Fails when no free spot is in view."""

    def execute(self, object, support):
        rig = self.rig
        from ..visual_prompt import mark_spots
        mem = memory(rig)
        mem.pop("visual_prompt", None)
        out = mark_spots(rig, object, support, frames=mem.pop("view_frames", None))
        rig.log("mark_spots", object=object, support=support, spots=out["spots"], near=out.get("near"),
                images=len(out["images"]))
        if not out["spots"]:
            raise SkillFailure(f"mark spots on {support}: no free spot for {object} in view")
        if out["images"]:
            mem["visual_prompt"] = [{"camera": "head", "overlay": "place_spots", "view": v + 1, "image": img}
                                    for v, img in enumerate(out["images"])]
        return {"spots": out["spots"]}


def _search_aims(support, base_xy):
    """Points search aims the head at on one support: its centre for a short one; along a long one, the centres
    of equal parts at most SEARCH_AIM_SPACING_M long, nearest the base first."""
    x0, y0, x1, y1 = support["aabb_xy"]
    lx, ly = x1 - x0, y1 - y0
    n = max(1, math.ceil(max(lx, ly) / SEARCH_AIM_SPACING_M - 1e-9))
    pts = [np.array([x0 + (i + 0.5) / n * lx, (y0 + y1) / 2, support["z"]]) if lx >= ly else
           np.array([(x0 + x1) / 2, y0 + (i + 0.5) / n * ly, support["z"]]) for i in range(n)]
    return sorted(pts, key=lambda p: math.hypot(p[0] - base_xy[0], p[1] - base_xy[1]))


class SearchObjectPolicy(AtomicPolicy):
    """Look for an object at candidate places in order of distance until it is seen.  Candidates are the
    supports of the region (a room, or the robot's room), grouped by furniture.  Where to stand is decided
    first, as one goal set: per piece, the first stand-off navigate_place would take -- one the base can get
    to the furniture is in view from (viewpoints.reachable_in_view: one base_reachable field over all of them);
    a piece with none is not driven to and the failure names it.  At each piece a look per aim point (every
    support, highest first; along a long one several points, _search_aims), until the object is seen.  Before
    the drive, viewpoints.drivable: the first of the piece's seeing stand-offs (at most DRIVE_TRIES) navigate
    can get to; a piece with none is skipped and the failure names it (another goal of the set, rule 3).  A
    drive that fails fails the search.  A piece counts as visited when some aim point was in the head camera
    there (walls and furniture boxes, no dynamic occluders)."""

    def execute(self, name, region=None):
        rig = self.rig
        from ..evaluator import room_of
        from ..perception import project_from
        from .base_motion import standoff_poses
        x, y, _ = rig.base_pose()
        room = region or room_of(rig.ann.rooms, (x, y))
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
        named = {s.get("furniture") for s in rig.ann.supports}
        place = {f: (f if f in named else furniture[f][0]["name"]) for f in order}
        if rig.held is not None:
            # the stand-offs are checked in the posture the drives carry the load in (as navigate_place)
            from ..skill_jobs.carry import carry_posture
            carry_posture(rig, min_bottom_z=None)
        seen_from = viewpoints.reachable_in_view(rig, {place[f]: standoff_poses(rig, place[f]) for f in order})
        goal, unreachable = {}, []
        for f in order:
            seeing = seen_from[place[f]][1]
            if seeing:
                goal[f] = seeing[0]
            else:
                unreachable.append(f)
        rig.log("search_goals", obj=name, furniture=len(order), reachable_in_view=len(goal), none=unreachable)
        visited, unviewable, undriven = [], [], []
        for f in order:
            if f not in goal:
                continue
            rig.caption = f"SEARCH {name}: {f}"
            # the field passes stand-offs navigate has no path to (v6 dining room: kitchen_cabinet_3's from the
            # west, "search limit", 0 of 4): the next one that sees the piece, else the next piece
            tries = seen_from[place[f]][1][:DRIVE_TRIES]
            pose = next((p for p in tries if viewpoints.drivable(rig, p)), None)
            if pose is None:
                undriven.append(f)
                rig.log("search_skip", place=f, reason="no base path to a stand-off that sees it",
                        poses=[[round(v, 2) for v in p] for p in tries])
                continue
            skills.navigate(rig, pose, label=f"search_{f}", raise_load=rig.held is None)
            in_view, found = [False], [None]

            def check(r, p):
                record_view(r)
                in_view[0] = in_view[0] or project_from(r, *rig_head_pose(r), p)[0]
                if project_to_head_camera(r, r.geo.centre(name, r.state()), exclude=name)[0]:
                    found[0] = True

            for s in sorted(furniture[f], key=lambda s: -s["z"]):
                for p in _search_aims(s, rig.base_pose()[:2]):
                    look(rig, [aim_at(s["name"], p, SEARCH_STEPS)], label=f"search_{f}",
                         on_view=lambda r, what, p=p: check(r, p))
                    if found[0]:
                        sup = rig.geo.support_under(name, rig.state())
                        found_on = sup["name"] if sup else None
                        memory(rig)["observed"][name] = rig.tick
                        visited.append(f)
                        rig.log("search_result", obj=name, found_on=found_on, visited=visited)
                        return {"found_on": found_on, "visited": visited}
            if in_view[0]:
                visited.append(f)
            else:
                unviewable.append(f)
                rig.log("search_skip", place=f, reason="no aim point in view from the stand-off",
                        pose=[round(v, 2) for v in rig.base_pose()])
        why = f"search {name}: not seen at {visited}"
        if unviewable:
            why += f"; not in view from where the base stood: {unviewable}"
        if unreachable:
            why += f"; no stand-off the base can get to sees: {unreachable}"
        if undriven:
            why += f"; no base path to a stand-off of: {undriven}"
        raise SkillFailure(why)


class InspectReceptaclePolicy(AtomicPolicy):
    """Look into a container, an open cabinet or an appliance and return what is inside: the inspect skill
    (skill_jobs.look.inspect_job)."""

    def execute(self, receptacle):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["inspect"], {"receptacle": receptacle})
