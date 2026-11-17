"""Where the robot can stand to see something: the one source of the view criteria navigate, search,
explore_room, explore_furniture and view_support stand by (docs/MOTION_ARCHITECTURE.md 9.3 step 3).

A stand-off sees a place when, with the base there in the posture navigate arrives in (skills._rest_posture:
its torso and waist place the camera) and the head aimed as look aims it, a point of the place is in the head
camera's frustum and no static box -- a wall, a piece of furniture -- is on the line of sight
(perception.in_view_from).  No dynamic occluders: where the base goes must not depend on objects the
observation-limited benchmark has not shown the robot.

* view_points / in_view_poses: which stand-offs see a place (navigate prefers them; search and
  explore_furniture stand only there);
* reachable_in_view: the same for several places at once, the stand-offs first filtered by one
  base_reachable field;
* predicted / cover_views: which targets a viewpoint sees, and the fewest viewpoints that see them all
  (explore_room);
* view_coverage / best_view: how much of a support's top one frame holds (view_support, mark_spots) --
  defined in visual_prompt, beside the image geometry they share with the spots, and only re-exported here.
"""

from __future__ import annotations

import math

import numpy as np

from .perception import in_view_from
from .predicates import entity_kind, entity_point
from .visual_prompt import best_view, view_coverage  # noqa: F401  (re-exported: one module to look in)

IN_VIEW_KINDS = ("object", "support", "furniture")   # navigate prefers stand-offs these are in view from


def travel_tw(rig):
    """Torso and waist the base arrives with (skills._rest_posture): where a stand-off's camera will be."""
    from . import skills
    return dict(zip(rig.kin.names[:2], (float(q) for q in skills._rest_posture(rig)[0][:2])))


def layer_point(layer):
    """Where objects stand on a support layer: above its centre, 10 cm or half its clearance."""
    x0, y0, x1, y1 = layer["aabb_xy"]
    return np.array([(x0 + x1) / 2, (y0 + y1) / 2, layer["z"] + min(0.10, layer.get("clearance", 1.0) / 2)])


def view_points(rig, place):
    """The points a stand-off must see for ``place`` to be in view: an object or a support -- the point look
    aims at (entity_point); a piece of furniture -- that point (its top) or the space above any of its support
    layers (layer_point, what explore_furniture and search look at).  None for anything else (a room: being
    in it is the point; articulated parts and appliances: not measured yet)."""
    kind, rec = entity_kind(rig.ann, place)
    if kind not in IN_VIEW_KINDS:
        return None
    pts = [entity_point(rig, place)]
    if kind == "furniture":
        pts += [layer_point(s) for s in rec]
    return pts


def in_view_poses(rig, place, poses):
    """The poses of ``poses`` (in their order) that see ``place`` (any of its view_points); all of them for a
    place with no view points (a room)."""
    pts = view_points(rig, place)
    if pts is None or not poses:
        return list(poses)
    tw = travel_tw(rig)
    return [pose for pose in poses if any(in_view_from(rig, pose, p, tw)[0] for p in pts)]


def reachable_in_view(rig, stand):
    """{place: (reachable, seeing)} for ``stand`` {place: [stand-off pose]}: the poses the base can get to
    from here -- one base_reachable field over all of them -- and, of those, the ones that see the place
    (in_view_poses), each in its given order."""
    from . import skills
    flat = [(place, p) for place, poses in stand.items() for p in poses]
    ok = skills.base_reachable(rig, [p for _, p in flat]) if flat else []
    out = {}
    for place in stand:
        reach = [p for (q, p), o in zip(flat, ok) if o and q == place]
        out[place] = (reach, in_view_poses(rig, place, reach))
    return out


def predicted(rig, pose, targets, tw):
    """{target: its first point in view from ``pose``} for ``targets`` {name: [(point, owner)]}."""
    out = {}
    for k, pts in targets.items():
        for p, _ in pts:
            if in_view_from(rig, pose, p, tw)[0]:
                out[k] = p
                break
    return out


def cover_views(rig, cands, targets, max_views):
    """The viewpoints of ``cands`` (stand-offs the base can get to) that together see the most of
    ``targets``, chosen greedily before the robot moves: each time the one that adds the most targets not
    covered yet, the nearer to the last one (the robot first) on a tie, until none adds any or
    ``max_views``.  Returns (chosen, {pose: predicted targets}) -- only the cands that see something."""
    tw = travel_tw(rig)
    pred = {p: predicted(rig, p, targets, tw) for p in cands}
    pred = {p: v for p, v in pred.items() if v}
    chosen, covered = [], set()
    x, y, _ = rig.base_pose()
    while pred and len(chosen) < max_views:
        best = max(pred, key=lambda p: (len(set(pred[p]) - covered), -math.hypot(p[0] - x, p[1] - y)))
        if not set(pred[best]) - covered:
            break
        chosen.append(best)
        covered |= set(pred[best])
        x, y = best[0], best[1]
    return chosen, pred
