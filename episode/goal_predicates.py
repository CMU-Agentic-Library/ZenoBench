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
* ``count_on_at_most(objects, support, k)``: at most k of them on the support (exactly two cups for two
  guests, with count_on_at_least; T25);
* ``count_inside_at_most(objects, container, k)``: at most k of the listed objects are inside the
  container;
* ``fully_inside(object, container)``: inside and not sticking out over the rim (a container's real
  capacity, T12);
* ``near_any(object, others, max_dist_m)``: next to at least one of the listed objects (a book by a
  place setting, T01);
* ``visible_from(object, eye, min_fraction)``: seen from a person's eye point: at least ``min_fraction`` of
  sample points on the object's top have a line of sight to the eye that no other object blocks (a toy seen
  from the bed, T06);
* ``same_arrangement(objects, examples, anchor, example_anchor, facing, example_facing, tol_m)``: each object stands
  where its example stands, relative to the anchor, in the frame of the person it is for (a place setting copied
  across the table, T13);
* ``never_picked(objects)``: a process requirement: none of them was held at any time in the episode (the castle
  stays built the whole time, not taken apart and built again; T12, T14, T27);
* ``on_any(object, supports)``: on one of several supports that all do what the person asked (T23, T28).
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
    p0 = (ctx.get("before") or {}).get("objects", {}).get(object, {}).get("pos")
    if p0 is None:
        return False, "no start pose"
    if s0:
        ok, why = rig.geo.on(object, s0, st)
    else:
        # no support: on the floor, or stacked on another object (a block of the castle); either way it is where
        # it started when its height has not changed (the floor test alone failed every block above the bottom)
        dz = abs(float(st["objects"][object]["pos"][2]) - float(p0[2]))
        ok, why = dz <= max(float(tol_m), 0.02), f"height {dz:+.3f} m from its start"
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


@goal_predicate("count_on_at_most", ["objects", "support", "k"],
                "At most k of the listed objects rest on the support (no more than was asked for).")
def _count_on_at_most(rig, ctx, objects, support, k):
    st = _state(rig, ctx)
    on = [o for o in objects if o in st["objects"] and rig.geo.on(o, support, st)[0]]
    return len(on) <= int(k), f"{len(on)} on {support}: {on}"


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


@goal_predicate("never_picked", ["objects"],
                "A process requirement, not an end state: the robot never held any of the objects during the "
                "episode (a castle taken apart and built again, or homework lifted and put back, does not count).")
def _never_picked(rig, ctx, objects):
    names = objects if isinstance(objects, list) else [objects]
    start = (ctx.get("before") or {}).get("events", 0)
    held = sorted({e.get("obj") for e in rig.events[start:]
                   if e.get("label") == "pick_result" and e.get("obj") in names and e.get("held")})
    return not held, f"picked up: {', '.join(held)}" if held else "never picked up"


@goal_predicate("on_any", ["object", "supports"],
                "The object is on at least one of the listed supports (several places would do what the person "
                "asked, e.g. the bookcase or the desk beside the bed).")
def _on_any(rig, ctx, object, supports):
    from zeno_skills.predicates import REGISTRY
    why = []
    for s in supports:
        ok, d = REGISTRY["on"].evaluate(rig, ctx, object=object, support=s)
        if ok:
            return True, f"on {s}"
        why.append(f"{s}: {d}")
    return False, "; ".join(why)


def _segment_hits_box(p0, p1, box, t_max=0.97):
    """Does the segment p0 -> p1 (up to t_max of its length) pass through the 3D box [x0, y0, z0, x1, y1, z1]?"""
    d = p1 - p0
    t0, t1 = 0.0, t_max
    for i in range(3):
        if abs(d[i]) < 1e-9:
            if p0[i] < box[i] or p0[i] > box[i + 3]:
                return False
            continue
        a, b = (box[i] - p0[i]) / d[i], (box[i + 3] - p0[i]) / d[i]
        if a > b:
            a, b = b, a
        t0, t1 = max(t0, a), min(t1, b)
        if t0 > t1:
            return False
    return True


@goal_predicate("visible_from", ["object", "eye", "min_fraction"],
                "At least min_fraction of nine points on the object's top have a line of sight to the eye point "
                "that no other object's box blocks (the person's own bed and the walls are not checked).")
def _visible_from(rig, ctx, object, eye, min_fraction=0.5):
    st = _state(rig, ctx)
    eye = np.asarray(eye, float)

    def box3(o):
        fp = rig.geo.footprint(o, st)
        z0 = float(rig.geo.bottom(o, st)[2])
        return np.array([fp[0], fp[1], z0, fp[2], fp[3], z0 + float(rig.ann.asset_of(rig.ann.objects[o])["size"][2])])
    b = box3(object)
    z = b[5] - 0.005
    pts = [np.array([x, y, z]) for x in np.linspace(b[0] + 0.01, b[3] - 0.01, 3)
           for y in np.linspace(b[1] + 0.01, b[4] - 0.01, 3)]
    others = [box3(o) for o in st["objects"] if o != object and o in rig.ann.objects]
    seen = [not any(_segment_hits_box(eye, p, ob) for ob in others) for p in pts]
    frac = sum(seen) / len(seen)
    return frac >= float(min_fraction), f"{frac:.2f} of the top in view"


@goal_predicate("same_arrangement", ["objects", "examples", "anchor", "example_anchor", "facing", "example_facing",
                                     "tol_m"],
                "Each object's centre, taken relative to the anchor in the frame of a person facing ``facing``, is "
                "within tol_m of its example's centre relative to example_anchor in the frame facing "
                "``example_facing`` (forward and left of the person).")
def _same_arrangement(rig, ctx, objects, examples, anchor, example_anchor, facing, example_facing, tol_m=0.07):
    st = _state(rig, ctx)

    def centre(o):
        fp = rig.geo.footprint(o, st)
        return (fp[0] + fp[2]) / 2, (fp[1] + fp[3]) / 2

    def local(o, a, fc):
        (x, y), (ax, ay) = centre(o), centre(a)
        fx, fy = fc
        n = math.hypot(fx, fy)
        fx, fy = fx / n, fy / n
        dx, dy = x - ax, y - ay
        return dx * fx + dy * fy, -dx * fy + dy * fx           # forward, left
    worst = 0.0
    for o, e in zip(objects, examples):
        if o not in st["objects"]:
            return False, f"{o} missing"
        a, b = local(o, anchor, facing), local(e, example_anchor, example_facing)
        worst = max(worst, math.hypot(a[0] - b[0], a[1] - b[1]))
    return worst <= float(tol_m), f"largest offset error {worst:.3f} m"


@goal_predicate("heated_by", ["object", "appliance", "min_c"],
                "The appliance raised the food's temperature by at least min_c over the episode "
                "(episode.heat_log; the stove when the food sat on a lit burner, else the microwave).")
def _heated_by(rig, ctx, object, appliance, min_c=0.5):
    got = float(rig.memory.get("heated_by", {}).get(object, {}).get(appliance, 0.0))
    return got >= float(min_c), f"{got:.1f} C from {appliance}"


@goal_predicate("exposed_in", ["object", "appliance", "min_s"],
                "The object spent at least min_s seconds in the running appliance (on a lit burner; in the shut, "
                "running microwave), whether it warmed or not (episode.heat_log).")
def _exposed_in(rig, ctx, object, appliance, min_s=1.0):
    got = float(rig.memory.get("exposed_in", {}).get(object, {}).get(appliance, 0.0))
    return got >= float(min_s), f"{got:.1f} s in {appliance}"
