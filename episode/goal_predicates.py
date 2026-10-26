"""Goal-only predicates of the benchmark verifiers (benchmark v4 Hard variants).

They judge the final GT state of an episode like zeno_skills.predicates.REGISTRY does, but they
are not Contract conditions: no SkillNode, no exported skill file and no planner-facing contract
names them, so the skill library and its public interface stay unchanged.  episode.evaluate_goal
looks a goal atom up here first, then in the skill registry.

* ``near_start(object, tol_m[, untouched_tol_m])``: back on the support it started on, within ``tol_m`` of its start
  xy (a layout restored after a temporary move, T08);
* ``clear_of(object, others, min_gap_m)``: the object's footprint keeps ``min_gap_m`` to every
  listed object (a book that does not crowd the place settings, T01);
* ``front_visible(object)``: on its support with no taller object between it and an open edge
  (a toy on display, not hidden behind boxes, T06);
* ``count_on_at_least(objects, support, k)``: at least k of the listed objects are on the support
  (the table was not cleared to make room, T20);
* ``count_inside_at_most(objects, container, k)``: at most k of the listed objects are inside the
  container;
* ``fully_inside(object, container)``: inside and not sticking out over the rim (a container's real
  capacity, T12);
* ``near_any(object, others, max_dist_m)``: next to at least one of the listed objects (a book by a
  place setting, T01).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class GoalPredicate:
    name: str
    arg_names: tuple
    doc: str
    evaluate: Callable = field(compare=False, repr=False)


GOAL_PREDICATES: dict[str, GoalPredicate] = {}


def goal_predicate(name, args, doc):
    def wrap(fn):
        GOAL_PREDICATES[name] = GoalPredicate(name, tuple(args), doc, fn)
        return fn
    return wrap


def _state(rig, ctx):
    from zeno_skills.predicates import _state as st
    return st(rig, ctx)


def _gap(a, b):
    """Gap between two xy boxes [x0, y0, x1, y1] (0 when they overlap)."""
    dx = max(0.0, float(max(a[0], b[0]) - min(a[2], b[2])))
    dy = max(0.0, float(max(a[1], b[1]) - min(a[3], b[3])))
    return math.hypot(dx, dy)


@goal_predicate("near_start", ["object", "tol_m", "untouched_tol_m"],
                "Object on the support it started on, its xy within tol_m of the start; one the robot never "
                "picked up within untouched_tol_m (when given): pushed aside is not put back.")
def _near_start(rig, ctx, object, tol_m, untouched_tol_m=None):
    from zeno_skills.predicates import memory
    st = _state(rig, ctx)
    s0 = memory(rig)["initial_support"].get(object) or rig.ann.objects[object].get("support")
    ok, why = rig.geo.on(object, s0, st) if s0 else (float(rig.geo.bottom(object, st)[2]) < 0.05, "floor")
    p0 = (ctx.get("before") or {}).get("objects", {}).get(object, {}).get("pos")
    if p0 is None:
        return False, "no start pose"
    d = math.hypot(st["objects"][object]["pos"][0] - p0[0], st["objects"][object]["pos"][1] - p0[1])
    tol, how = float(tol_m), ""
    if untouched_tol_m is not None:
        start = (ctx.get("before") or {}).get("events", 0)
        picked = any(e.get("label") == "pick_result" and e.get("obj") == object and e.get("held")
                     for e in rig.events[start:])
        tol, how = (tol, ", picked up") if picked else (float(untouched_tol_m), ", never picked up")
    return bool(ok) and d <= tol, f"{why}; {d:.3f} m from its start{how}"


@goal_predicate("clear_of", ["object", "others", "min_gap_m"],
                "The object's footprint keeps min_gap_m to the footprint of every listed object.")
def _clear_of(rig, ctx, object, others, min_gap_m):
    st = _state(rig, ctx)
    fp = rig.geo.footprint(object, st)
    worst, who = math.inf, None
    for o in others:
        if o == object or o not in st["objects"]:
            continue
        g = _gap(fp, rig.geo.footprint(o, st))
        if g < worst:
            worst, who = g, o
    return worst >= float(min_gap_m) - 0.003, f"closest {who} at {worst:.3f} m"


@goal_predicate("front_visible", ["object"],
                "The object rests on a support and no object taller than it stands between it and an open "
                "edge of that support (seen from the room).")
def _front_visible(rig, ctx, object):
    from zeno_skills import skills
    st = _state(rig, ctx)
    s = rig.geo.support_under(object, st)
    if s is None:
        return False, "not on a support"
    fp = rig.geo.footprint(object, st)
    top = float(rig.geo.bottom(object, st)[2]) + float(rig.ann.asset_of(rig.ann.objects[object])["size"][2])
    blockers = {}
    for n in skills._open_edges(rig, s):
        e = skills._edge_coord(s, n)
        # the corridor from the object's front face to the edge, as wide as the object
        if abs(n[0]) > 0.5:
            box = [fp[2], fp[1], e, fp[3]] if n[0] > 0 else [-e, fp[1], fp[0], fp[3]]
        else:
            box = [fp[0], fp[3], fp[2], e] if n[1] > 0 else [fp[0], -e, fp[2], fp[1]]
        hit = []
        for o in st["objects"]:
            if o == object or o not in rig.ann.objects:
                continue
            ofp = rig.geo.footprint(o, st)
            if _gap(box, ofp) > 0 or min(box[2], ofp[2]) - max(box[0], ofp[0]) <= 0.005 \
                    or min(box[3], ofp[3]) - max(box[1], ofp[1]) <= 0.005:
                continue
            otop = float(rig.geo.bottom(o, st)[2]) + float(rig.ann.asset_of(rig.ann.objects[o])["size"][2])
            if otop > top + 0.01 and float(rig.geo.bottom(o, st)[2]) < top:
                hit.append(o)
        if not hit:
            return True, f"open towards {tuple(int(v) for v in np.round(n))}"
        blockers[tuple(int(v) for v in np.round(n))] = hit
    return False, f"hidden: {blockers or 'no open edge'}"


@goal_predicate("count_on_at_least", ["objects", "support", "k"],
                "At least k of the listed objects rest on the support.")
def _count_on_at_least(rig, ctx, objects, support, k):
    st = _state(rig, ctx)
    on = [o for o in objects if o in st["objects"] and rig.geo.on(o, support, st)[0]]
    return len(on) >= int(k), f"{len(on)} on {support}: {on}"


@goal_predicate("count_inside_at_most", ["objects", "container", "k"],
                "At most k of the listed objects are inside the container.")
def _count_inside_at_most(rig, ctx, objects, container, k):
    st = _state(rig, ctx)
    inside = [o for o in objects if o in st["objects"] and rig.geo.inside(o, container, st)[0]]
    return len(inside) <= int(k), f"{len(inside)} inside {container}: {inside}"


@goal_predicate("fully_inside", ["object", "container"],
                "Inside the container and nothing of it above the rim (1 cm tolerance): put away, not perched on top.")
def _fully_inside(rig, ctx, object, container):
    st = _state(rig, ctx)
    ok, why = rig.geo.inside(object, container, st)
    if not ok:
        return False, why
    prof = rig.ann.asset_of(rig.ann.objects[container])["container"]
    rim = float(rig.geo.bottom(container, st)[2]) + float(prof["rim_height"])
    size = np.asarray(rig.ann.asset_of(rig.ann.objects[object])["size"], float)
    from zeno_skills.predicates import _quat_R
    top = float(rig.geo.centre(object, st)[2]) + 0.5 * float(np.abs(_quat_R(st["objects"][object]["quat"])[2, :]) @ size)
    return top <= rim + 0.01, f"top {top - rim:+.3f} m to the rim"


@goal_predicate("near_any", ["object", "others", "max_dist_m"],
                "The object's footprint comes within max_dist_m of at least one listed object's footprint.")
def _near_any(rig, ctx, object, others, max_dist_m):
    st = _state(rig, ctx)
    fp = rig.geo.footprint(object, st)
    d = min((_gap(fp, rig.geo.footprint(o, st)) for o in others if o in st["objects"] and o != object),
            default=math.inf)
    return d <= float(max_dist_m), f"nearest at {d:.3f} m"
