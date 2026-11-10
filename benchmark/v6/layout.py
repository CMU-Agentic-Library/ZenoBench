"""Seed layout generator: where the objects stand and where the robot starts.

A variant fixes the task design (scene conditions, events, substitutes, goal, and the placements a challenge is
made of); the seed draws the rest of the layout:

* **objects**: every cluster of task objects on an open support (objects closer than ``CLUSTER_GAP_M``, a stack,
  a crowded group) is shifted as a whole to a random free place on the same support.  An axis on which the
  cluster is within ``EDGE_LOCK_M`` of the support edge does not move (an overhang stays), the cluster never goes
  deeper from the edge it is reached from than it was (or ``DEPTH_FREE_M``), it keeps out of the places the
  oracle route or an event puts objects on, and objects on those places, in closed furniture or on an appliance
  do not move.  On a top (``/top``) with an edge the base can stand at (``reach_edges``) the cluster goes anywhere
  on the top where each of its objects lies within ``REACH_DEPTH_M`` (20 cm) of such an edge (``reachable``);
* **start**: a random free, reachable cell of the variant's start room (``start_cells.json``) and a random yaw;
  when the variant hides an item (a search condition) the item is not in the start view, and the route's first
  ``look`` target is not behind a wall.

``layout_spec`` (define time) writes a variant's ``layout`` block; ``apply_layout`` (``benchmark.scene``
``episode_config``) draws one layout from the seed.  A draw that cannot be placed keeps the variant's own pose,
which is collision-free by construction.

    python benchmark/v6/layout.py      # rebuilds start_cells.json (needs zeno_skills; about two minutes)
"""
from __future__ import annotations

import json
import math
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from zeno_skills.predicates import VIEW_RANGE_M  # noqa: E402  the look skill's range (5 m), not a copy
CELLS = ROOT / "benchmark/v6/start_cells.json"

CLUSTER_GAP_M = 0.03     # objects closer than this on one support move together
EDGE_LOCK_M = 0.04       # a cluster this close to a support edge does not move across it
DEPTH_FREE_M = 0.15      # a cluster may always lie this deep from the edge it is reached from
CLEAR_M = 0.01           # clearance between a moved cluster and anything else on the support
CELL_M = 0.2             # start-cell grid
VIEW_HALF_DEG = 45.0     # half the start view (head camera, head straight)
FLOOR_CLEAR_M = 0.45     # no start this close to an object on the floor (bottom below FLOOR_Z_M), as v5 checks
FLOOR_Z_M = 0.15
DESIGN_NEAR_M = 0.15     # an object this close to a design object is the other side of its relation
EVENT_NEAR_M = 0.3       # objects this close to where an event puts something stay (the event is about them)
TRIES = 40
REACH_DEPTH_M = 0.20     # a cluster on a top lies within this of an edge the base can stand at (its far side)...
REACH_NEAR_M = 0.08      # ...or its near side this close to that edge (a big thing set at the edge)
REACH_LATERAL_M = 0.25   # ...and its centre at most this far along the edge past where the base can stand
REACH_TRIES = 200
EDGE_STEP_M = 0.05       # reach edges: samples along each edge of a top
STANDOFFS_M = (0.30, 0.35, 0.40, 0.45)   # base centre from the edge (the column is 0.244 + 0.046 m); 0.20 m in
                                         # from 0.45 out is still well inside the arm's 0.78 m
SEARCH_TYPES = ("search_target", "search_tool")


# ----------------------------------------------------------------- scene data
@lru_cache(maxsize=None)
def _ann(base):
    return json.loads((ROOT / base / "annotation.json").read_text())


@lru_cache(maxsize=None)
def _assets():
    return json.loads((ROOT / "annotations/assets.json").read_text())


@lru_cache(maxsize=None)
def _walls(base):
    return tuple(tuple(o["aabb"][:2] + o["aabb"][3:5]) for o in _ann(base)["obstacles"] if o["kind"] == "wall")


def _sups(base):
    return {s["name"]: s for s in _ann(base)["supports"]}


def _fixed_support(base, name):
    """Closed furniture (a cabinet shelf, the microwave) or an appliance: objects there do not move."""
    a = _ann(base)
    s = _sups(base).get(name)
    if s is None:
        return True
    appliances = {x["name"] for x in a.get("appliances", [])}
    if s["furniture"] in appliances or name.split("/")[0] in appliances:
        return True                                     # a pot stays on its burner
    return s["furniture"] in {x["name"] for x in a["articulated"]} and not name.endswith("/top")


def _box(asset, m):
    a = _assets()[asset]
    sx, sy = a["size"][0] / 2, a["size"][1] / 2
    c, s = abs(math.cos(math.radians(m.get("yaw_deg", 0.0)))), abs(math.sin(math.radians(m.get("yaw_deg", 0.0))))
    hx, hy = sx * c + sy * s, sx * s + sy * c         # the box of the yawed footprint (any yaw)
    return [m["xy"][0] - hx, m["xy"][1] - hy, m["xy"][0] + hx, m["xy"][1] + hy]


def _overlap(a, b, gap=0.0):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def _union(bs):
    return [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)]


def _asset_of(base, name, add):
    if name in add:
        return add[name]["asset"]
    return {o["name"]: o for o in _ann(base)["objects"]}[name]["asset"]


# ----------------------------------------------------------------- reach edges (define time)
@lru_cache(maxsize=None)
def _world(base):
    from zeno_skills.annotations import SceneAnnotations
    from zeno_skills.collision import WorldModel
    return WorldModel(SceneAnnotations(ROOT / base / "annotation.json"))


@lru_cache(maxsize=None)
def reach_edges(base, sup):
    """Where the base can stand at a top: [[k, s, E, l0, l1, depth], ...], each a stretch of the edge at
    coordinate E on axis k (s = +1: the max edge, -1: the min edge) from l0 to l1 along the other axis, with the
    base column clear (facing the top) at the nearest standoff that is; depth = how deep from that edge it
    reaches (REACH_DEPTH_M).  A side against a wall or other furniture has none."""
    world = _world(base)
    a = _sups(base)[sup]["aabb_xy"]
    out = []
    for k in (0, 1):
        j = 1 - k
        for sgn in (1, -1):
            E = a[k + 2] if sgn > 0 else a[k]
            n = max(1, int(round((a[j + 2] - a[j]) / EDGE_STEP_M)))
            run = None
            for i in range(n + 1):
                t = a[j] + (a[j + 2] - a[j]) * i / n
                depth = None
                for off in STANDOFFS_M:
                    p = [0.0, 0.0]
                    p[k], p[j] = E + sgn * off, t
                    yaw = math.atan2(-sgn if k else 0.0, -sgn if not k else 0.0)
                    if world.footprint_clear(p[0], p[1], yaw):
                        depth = REACH_DEPTH_M
                        break
                if run and depth == run[5]:
                    run[4] = round(t, 3)
                    continue
                if run:
                    out.append(run)
                run = [k, sgn, round(E, 4), round(t, 3), round(t, 3), depth] if depth is not None else None
            if run:
                out.append(run)
    return out


def reachable(b, edges):
    """Box b ([x0, y0, x1, y1]) within reach of one of the ``edges`` (reach_edges)."""
    for k, sgn, E, l0, l1, depth in edges:
        j = 1 - k
        c = (b[j] + b[j + 2]) / 2
        if not l0 - REACH_LATERAL_M <= c <= l1 + REACH_LATERAL_M:
            continue
        far = E - b[k] if sgn > 0 else b[k + 2] - E
        near = E - b[k + 2] if sgn > 0 else b[k] - E
        if far <= depth or near <= REACH_NEAR_M:
            return True
    return False


HINT_STEP_M = 0.02       # grid of the places a hint may move to
HINT_CLEAR_M = 0.02      # a moved hint keeps this from the support's edge and from what stands there


def _relations_ok(n, b, goal, where, before=None):
    """The goal relations about ``n`` that can be judged now hold with ``n`` at box ``b`` (others where they stand)."""
    def box(k):
        return where[k][1] if k in where else None

    def gap(p, q):
        return math.hypot(max(0.0, max(p[0], q[0]) - min(p[2], q[2])), max(0.0, max(p[1], q[1]) - min(p[3], q[3])))
    for a in _atoms(goal):
        kind = a[0]
        if kind in ("near_any", "not near_any", "clear_of") and a[1] == n:
            bs = [box(k) for k in a[2] if k != n and box(k)]
            if not bs:
                continue
            g = min(gap(b, q) for q in bs)
            if (kind == "near_any" and g > a[3]) or (kind == "not near_any" and g < a[3]) or \
                    (kind == "clear_of" and g < a[3]):
                return False
        elif kind in ("clear_of",) and n in a[2] and box(a[1]):
            if gap(b, box(a[1])) < a[3]:
                return False
        elif kind == "near_any" and n in a[2] and box(a[1]) and before is not None:
            if gap(before, box(a[1])) <= a[3] < gap(b, box(a[1])):
                return False                           # the hint was what kept the subject near one of them
        elif kind == "grouped" and n in a[1]:
            c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            for k in a[1]:
                q = box(k) if k != n else None
                if q and math.hypot((q[0] + q[2]) / 2 - c[0], (q[1] + q[3]) / 2 - c[1]) > a[3]:
                    return False
        elif kind == "same_arrangement" and n in _names(a[1:]):
            return False                               # an exact copy of a layout: never moved
    return True


def _nearest_free(base, sup, asset, xy, others, ok=lambda b: True):
    """The grid place nearest ``xy`` on ``sup`` where an ``asset`` lies in reach, inside the top and clear of
    ``others`` (boxes), and ``ok``; None if there is none."""
    A, edges = _sups(base)[sup]["aabb_xy"], reach_edges(base, sup)
    best = None
    for ix in range(int((A[2] - A[0]) / HINT_STEP_M) + 1):
        for iy in range(int((A[3] - A[1]) / HINT_STEP_M) + 1):
            p = [round(A[0] + ix * HINT_STEP_M, 3), round(A[1] + iy * HINT_STEP_M, 3)]
            d = math.hypot(p[0] - xy[0], p[1] - xy[1])
            if best is not None and d >= best[0]:
                continue
            b = _box(asset, {"xy": p})
            if b[0] < A[0] + HINT_CLEAR_M or b[1] < A[1] + HINT_CLEAR_M or b[2] > A[2] - HINT_CLEAR_M \
                    or b[3] > A[3] - HINT_CLEAR_M or not reachable(b, edges) \
                    or any(_overlap(b, o, HINT_CLEAR_M) for o in others) or not ok(b):
                continue
            best = (d, p)
    return best[1] if best else None


def poses_in_reach(task):
    """Each variant's own pose of an object its route picks from a top, moved as little as it needs into reach of a
    free edge, clear of what else stands there (the seed then draws from it; a pose the seed keeps -- the design --
    is in reach too).  An object on an appliance, stacked, one of a group, or with no free place stays.
    Returns [(variant, object, old, new)]."""
    base = task["scene"]["base"]
    sups = _sups(base)
    ann = {o["name"]: o for o in _ann(base)["objects"]}
    out = []
    for lid, rname in task["oracle"].items():
        v = task["variants"].get(lid)
        if v is None or rname not in task["routes"]:
            continue
        steps = task["routes"][rname]["steps"]
        picked = {s["args"].get("object") for s in steps if s["skill"] == "pick"}
        removed = set(task["scene"].get("remove", [])) | set(v.get("remove", []))
        add = {**task["scene"].get("add", {}), **v.get("add", {})}
        placed = {**task["scene"].get("move", {}), **add, **v.get("move", {})}
        boxes = {}
        for n, o in ann.items():
            if n not in removed and n not in placed and o.get("support"):
                boxes[n] = (o["support"], o["aabb"][:2] + o["aabb"][3:5])
        for n, m in placed.items():
            if n not in removed and m.get("xy") and m.get("support"):
                try:
                    boxes[n] = (m["support"], _box(_asset_of(base, n, add), m))
                except KeyError:
                    pass
        stacked = {k for k, m in placed.items() if m.get("xy") and not m.get("support")}
        for n in sorted(picked & set(placed) - removed):   # a relation judges where it ends up, not where it starts
            m = placed[n]
            sup = m.get("support")
            if not m.get("xy") or not sup or not sup.endswith("/top") or sup not in sups or not reach_edges(base, sup):
                continue
            b = boxes[n][1]
            if reachable(b, reach_edges(base, sup)) or _fixed_support(base, sup):
                continue                               # in reach already, or on an appliance (a lid on its pot)
            if any(_overlap(b, _box(_asset_of(base, k, add), placed[k]), CLUSTER_GAP_M) for k in stacked) or \
                    any(k != n and _overlap(b, q, CLUSTER_GAP_M) for k, (_s, q) in boxes.items()):
                continue                               # stacked, or one of a group: the seed moves the group
            others = [q for k, (s_, q) in boxes.items() if s_ == sup and k != n]
            p = _nearest_free(base, sup, _asset_of(base, n, add), m["xy"], others)
            if p is None:
                continue
            where = v.setdefault("move", {}) if n in v.get("move", {}) or n not in v.get("add", {}) else v["add"]
            new = dict(m, xy=p)
            where[n] = new
            boxes[n] = (sup, _box(_asset_of(base, n, add), new))
            out.append((lid, n, m["xy"], p))
    return out


def hints_in_reach(task):
    """Route ``place`` hints on a top moved, as little as they need, to where the object lies within reach of a free
    edge (``reachable``) and clear of what stands on the top then; a hint already in reach, on a top with no free
    edge, or with no such place nearby stays.  Returns [(route, step, old, new)]."""
    base = task["scene"]["base"]
    sups = _sups(base)
    ann = {o["name"]: o for o in _ann(base)["objects"]}
    out, done = [], set()
    for lid, rname in task["oracle"].items():
        v = task["variants"].get(lid)
        if v is None or rname not in task["routes"] or rname in done:
            continue
        done.add(rname)
        removed = set(task["scene"].get("remove", [])) | set(v.get("remove", []))
        add = {**task["scene"].get("add", {}), **v.get("add", {})}
        placed = {**task["scene"].get("move", {}), **add, **v.get("move", {})}
        where = {}                                  # object -> (support, box) as the route goes
        for n, o in ann.items():
            if n not in removed and n not in placed and o.get("support"):
                where[n] = (o["support"], o["aabb"][:2] + o["aabb"][3:5])
        for n, m in placed.items():
            if n not in removed and m.get("xy") and m.get("support"):
                try:
                    where[n] = (m["support"], _box(_asset_of(base, n, add), m))
                except KeyError:
                    pass
        for i, st in enumerate(task["routes"][rname]["steps"]):
            a = st["args"]
            if st["skill"] == "pick":
                where.pop(a.get("object"), None)
                continue
            if st["skill"] != "place" or not a.get("object"):
                continue
            n, sup, h = a["object"], a.get("receptacle"), a.get("hint_xy")
            if not h or not sup or not sup.endswith("/top") or sup not in sups or not reach_edges(base, sup):
                continue
            try:
                asset = _asset_of(base, n, add)
            except KeyError:
                continue
            edges = reach_edges(base, sup)
            others = [b for k, (s_, b) in where.items() if s_ == sup and k != n]
            if reachable(_box(asset, {"xy": h}), edges):
                where[n] = (sup, _box(asset, {"xy": h}))
                continue
            goal = v.get("goal") or task.get("goal") or {}
            hb = _box(asset, {"xy": h})
            p = _nearest_free(base, sup, asset, h, others, lambda b: _relations_ok(n, b, goal, where, hb))
            if p:
                a["hint_xy"] = p
                out.append((rname, i, h, p))
            where[n] = (sup, _box(asset, {"xy": p or h}))
    return out


# ----------------------------------------------------------------- start cells (define time)
def start_cells(bases):
    """{base: {room: [[x, y], ...]}}: cells where the robot base is free at every yaw, reachable from the base
    scene's robot start over cells free at 0 or 90 deg (a doorway is passed straight)."""
    sys.path.insert(0, str(ROOT))
    import numpy as np
    from zeno_skills.annotations import SceneAnnotations
    from zeno_skills.collision import WorldModel
    from zeno_skills.evaluator import room_of
    out = {}
    for base in sorted(bases):
        ann = SceneAnnotations(ROOT / base / "annotation.json")
        world = WorldModel(ann)
        x0, y0, _ = json.loads((ROOT / base / "task.json").read_text())["robot_start"]
        pts = np.concatenate([np.asarray(r["triangles"]).reshape(-1, 2) for r in ann.rooms.values()])
        lo, hi = pts.min(0), pts.max(0)
        nx, ny = int((hi[0] - lo[0]) / CELL_M) + 1, int((hi[1] - lo[1]) / CELL_M) + 1
        xy = lambda i, j: (round(float(lo[0] + i * CELL_M), 3), round(float(lo[1] + j * CELL_M), 3))  # noqa: E731
        free, start_ok = {}, set()
        for i in range(nx):
            for j in range(ny):
                x, y = xy(i, j)
                room = room_of(ann.rooms, (x, y))
                if not room:
                    continue
                if world.footprint_clear(x, y, 0.0, margin=0.03) or world.footprint_clear(x, y, math.pi / 2, margin=0.03):
                    free[(i, j)] = room
                    if all(world.footprint_clear(x, y, a, margin=0.08) for a in (0.0, math.pi / 4)):
                        start_ok.add((i, j))
        s = min(start_ok, key=lambda ij: math.hypot(xy(*ij)[0] - x0, xy(*ij)[1] - y0))
        seen, todo = {s}, [s]
        while todo:
            i, j = todo.pop()
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    n = (i + di, j + dj)
                    if n in free and n not in seen:
                        seen.add(n)
                        todo.append(n)
        rooms = {}
        for ij in sorted(seen & start_ok):
            rooms.setdefault(free[ij], []).append(list(xy(*ij)))
        out[base] = rooms
    return out


@lru_cache(maxsize=None)
def _cells():
    return json.loads(CELLS.read_text())


def room_of(base, xy):
    x, y = float(xy[0]), float(xy[1])
    for name, r in _ann(base)["rooms"].items():
        a = r["aabb_xy"]
        if not (a[0] <= x <= a[2] and a[1] <= y <= a[3]):
            continue
        for (x1, y1), (x2, y2), (x3, y3) in r["triangles"]:
            d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(d) < 1e-12:
                continue
            l1 = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d
            l2 = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d
            if l1 >= -1e-9 and l2 >= -1e-9 and 1 - l1 - l2 >= -1e-9:
                return name
    return None


# ----------------------------------------------------------------- spec (define time)
def reserved(task, vid, steps):
    """Footprints the oracle route (``hint_xy``) or an event puts objects on, per support."""
    base = task["scene"]["base"]
    add = {**task["scene"].get("add", {}), **task["variants"][vid].get("add", {})}
    out = {}
    for s in steps:
        h = s["args"].get("hint_xy")
        if h and s["args"].get("receptacle") and s["args"].get("object"):
            out.setdefault(s["args"]["receptacle"], []).append(
                _box(_asset_of(base, s["args"]["object"], add), {"xy": h}))
    for f in task["variants"][vid].get("failures") or []:
        ev = f.get("event") or {}
        to = ev.get("to")
        if isinstance(to, dict) and to.get("support") and to.get("xy") and ev.get("object"):
            out.setdefault(to["support"], []).append(_box(_asset_of(base, ev["object"], add), to))
    return out


RELATIONS = ("grouped", "near_any", "not near_any", "clear_of", "same_arrangement")


def _atoms(g):
    if isinstance(g, dict):
        for x in g.values():
            yield from _atoms(x)
    elif isinstance(g, list):
        if g and isinstance(g[0], str):
            yield g
        else:
            for x in g:
                yield from _atoms(x)


def _names(x):
    return [x] if isinstance(x, str) else [n for y in x for n in _names(y)] if isinstance(x, list) else []


def relation_anchors(goal, steps):
    """Objects the route leaves where they are that a goal relation (grouped, near_any, clear_of,
    same_arrangement) ties to an object the route sets down at a fixed hint_xy: the seed keeps them, or the
    hint lands away from them (T13: the bowl and cup set by a spoon moved 1.7 m away)."""
    hinted = {s["args"]["object"] for s in steps if s["skill"] == "place" and s["args"].get("hint_xy")}
    moved = {s["args"].get("object") for s in steps if s["skill"] in ("pick", "place")}
    out = set()
    for a in _atoms(goal):
        if a[0] in RELATIONS:
            ns = set(_names(a[1:])) - {x for x in a[1:] if isinstance(x, str) and "/" in x}
            if ns & hinted:
                out |= ns - moved
    return out


def _same_pose(a, b):
    return a.get("support") == b.get("support") and round(a.get("yaw_deg", 0.0)) == round(b.get("yaw_deg", 0.0)) \
        and all(abs(x - y) < 0.01 for x, y in zip(a.get("xy") or [], b.get("xy") or []))


def layout_spec(task, vid, registry, control=None):
    """The ``layout`` block of one concrete variant; ``registry``: the condition registry (condition -> type);
    ``control``: the layout of the variant's control.  Objects this variant places differently from its control
    are its design (a crowd, a set table, a bowl in the rolling path): on one support they move as one group, and
    stay where they are when any of them has to."""
    v = task["variants"][vid]
    scene, base = task["scene"], task["scene"]["base"]
    sups = _sups(base)
    removed = set(scene.get("remove", [])) | set(v.get("remove", []))
    move = {**scene.get("move", {}), **v.get("move", {})}
    add = {**scene.get("add", {}), **v.get("add", {})}
    placed = {**move, **add}
    steps = task["routes"][task["oracle"][vid]]["steps"]
    picked = {s["args"].get("object") for s in steps if s["skill"] == "pick"}
    keep_out = reserved(task, vid, steps)
    boxes = {n: _box(_asset_of(base, n, add), m) for n, m in placed.items() if m.get("xy")}
    # stacked objects (no support) go with the object they stand on
    under = {}
    for n, m in placed.items():
        if not m.get("support") and n in boxes:
            below = [k for k, b in boxes.items() if k != n and placed[k].get("support") and _overlap(b, boxes[n])]
            if below:
                under[n] = below[0]
    ctl = {}
    if control:
        cv = task["variants"][control]
        ctl = {**scene.get("move", {}), **cv.get("move", {}), **scene.get("add", {}), **cv.get("add", {})}
    design = {n for n, m in placed.items() if n not in ctl or not _same_pose(m, ctl[n])} if control else set()
    grow = True
    while grow:                                        # the bowl in the pin's path brings the pin along
        near = {n for n, m in placed.items() if n not in design and n in boxes and any(
            k in boxes and placed[k].get("support") == m.get("support") and _overlap(boxes[n], boxes[k], DESIGN_NEAR_M)
            for k in design)}
        grow = bool(near)
        design |= near
    events = [(ev["to"]["support"], ev["to"]["xy"]) for f in v.get("failures") or []
              for ev in [f.get("event") or {}] if isinstance(ev.get("to"), dict) and ev["to"].get("xy")]
    fixed = set()
    for n, m in placed.items():
        sup = m.get("support")
        if n in under or n not in boxes:
            continue
        cx, cy = (boxes[n][0] + boxes[n][2]) / 2, (boxes[n][1] + boxes[n][3]) / 2
        if sup not in sups or _fixed_support(base, sup) or (n in design and sup in v.get("keep_design", [])) or \
                any(_overlap(boxes[n], r) for r in keep_out.get(sup, [])) or \
                any(es == sup and math.hypot(cx - ex[0], cy - ex[1]) < EVENT_NEAR_M for es, ex in events):
            fixed.add(n)
    fixed |= relation_anchors(v.get("goal") or task.get("goal") or {}, steps)
    movable = {}
    for n, m in placed.items():
        sup = m.get("support")
        if n in under or n not in boxes or n in fixed:
            continue
        if n in design and any(placed[k].get("support") == sup for k in design & fixed):
            continue                                   # a design object on a support where the design is pinned
        movable.setdefault(sup, []).append(n)
    clusters = []
    for sup, names in sorted(movable.items()):
        own = sorted(n for n in names if n in design)
        groups = ([own] if own else []) + [[n] for n in sorted(names) if n not in design]
        merged = True
        while merged:
            merged = False
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    if any(_overlap(boxes[a], boxes[b], CLUSTER_GAP_M) for a in groups[i] for b in groups[j]):
                        groups[i] += groups.pop(j)
                        merged = True
                        break
                if merged:
                    break
        A = sups[sup]["aabb_xy"]
        for g in groups:
            g = sorted(g + [k for k, b in under.items() if b in g])
            B = _union([boxes[n] for n in g])
            rng = {}
            dist = {"x0": B[0] - A[0], "x1": A[2] - B[2], "y0": B[1] - A[1], "y1": A[3] - B[3]}
            near = min(dist, key=dist.get)                   # the edge the cluster is reached from
            top = sup.endswith("/top") and bool(reach_edges(base, sup))   # anywhere within reach of a free edge
            for ax, lo_k, hi_k in (("dx", "x0", "x1"), ("dy", "y0", "y1")):
                if min(dist[lo_k], dist[hi_k]) < EDGE_LOCK_M:
                    continue
                lo, hi = -dist[lo_k] + CLEAR_M, dist[hi_k] - CLEAR_M
                depth = max(dist[near], DEPTH_FREE_M)
                if top:
                    pass
                elif near == lo_k:
                    hi = min(hi, depth - dist[lo_k])
                elif near == hi_k:
                    lo = max(lo, dist[hi_k] - depth)
                lo, hi = math.ceil(lo * 100) / 100, math.floor(hi * 100) / 100
                if hi - lo >= 0.01:
                    rng[ax] = [min(lo, 0.0), max(hi, 0.0)]
            if rng:
                pk = sorted(set(g) & picked)
                clusters.append({"names": g, "support": sup, "box": [round(x, 4) for x in B], **rng,
                                 **({"pick": pk} if pk else {})})
    # what stands on those supports and does not move: base-scene objects, other task objects, reserved places
    in_cluster = {n for c in clusters for n in c["names"]}
    static = {}
    for o in _ann(base)["objects"]:
        if o["name"] in removed or o["name"] in placed or o.get("support") not in movable:
            continue
        static.setdefault(o["support"], []).append([round(x, 4) for x in o["aabb"][:2] + o["aabb"][3:5]])
    for n in placed:
        sup = placed[n].get("support") or placed.get(under.get(n), {}).get("support")
        if n in boxes and n not in in_cluster and sup in movable:
            static.setdefault(sup, []).append([round(x, 4) for x in boxes[n]])
    for sup, rs in keep_out.items():
        if sup in movable:
            static.setdefault(sup, []).extend([round(x, 4) for x in r] for r in rs)
    # start: the room of the variant's start, items it hides, the route's first look target
    s0 = v.get("start", scene.get("start")) or json.loads((ROOT / base / "task.json").read_text())["robot_start"]
    hide = []
    if any((registry.get(c) or {}).get("type") in SEARCH_TYPES for c in v.get("conditions") or []):
        for i, s in enumerate(steps):
            if s["skill"] == "search" and s["args"].get("object"):
                hide.append(s["args"]["object"])
            elif s["skill"] == "explore_room":
                nxt = next((x for x in steps[i + 1:] if x["skill"] == "pick"), None)
                if nxt:
                    hide.append(nxt["args"]["object"])
    look = [steps[0]["args"]["target"]] if steps and steps[0]["skill"] == "look" else []
    reach = {c["support"]: reach_edges(base, c["support"]) for c in clusters
             if c["support"].endswith("/top") and reach_edges(base, c["support"])}
    return {"clusters": clusters, "static": static, "reach": reach,
            "start": {"room": room_of(base, s0[:2]), "hide": sorted(set(hide)), "look": look}}


# ----------------------------------------------------------------- draw (episode time)
def _grid(rng, lohi):
    lo, hi = lohi
    return rng.randint(int(round(lo * 100)), int(round(hi * 100))) / 100


def _point(base, cfg, name):
    for where in (cfg.get("move") or {}, cfg.get("add") or {}):
        if name in where and where[name].get("xy"):
            return where[name]["xy"]
    o = {o["name"]: o for o in _ann(base)["objects"]}.get(name)
    if o:
        return [(o["aabb"][0] + o["aabb"][3]) / 2, (o["aabb"][1] + o["aabb"][4]) / 2]
    s = _sups(base).get(name)
    if s:
        a = s["aabb_xy"]
        return [(a[0] + a[2]) / 2, (a[1] + a[3]) / 2]
    return None


def _blocked(base, p, q):
    """A wall between p and q (2-D slab test against each wall box)."""
    for b in _walls(base):
        t0, t1, ok = 0.0, 1.0, True
        for k in (0, 1):
            d = q[k] - p[k]
            if abs(d) < 1e-9:
                if not b[k] <= p[k] <= b[k + 2]:
                    ok = False
                    break
                continue
            a, c = (b[k] - p[k]) / d, (b[k + 2] - p[k]) / d
            t0, t1 = max(t0, min(a, c)), min(t1, max(a, c))
            if t0 > t1:
                ok = False
                break
        if ok and t1 > 0.02 and t0 < 0.98:
            return True
    return False


def _in_view(base, x, y, yaw, p):
    d = math.hypot(p[0] - x, p[1] - y)
    ang = (math.degrees(math.atan2(p[1] - y, p[0] - x)) - yaw + 180) % 360 - 180
    return d <= VIEW_RANGE_M and abs(ang) <= VIEW_HALF_DEG and not _blocked(base, (x, y), p)


def _floor_boxes(cfg):
    base = cfg["base"]
    sups = _sups(base)
    add = cfg.get("add") or {}
    out = []
    for o in _ann(base)["objects"]:
        if o["name"] not in cfg["remove"] and o["name"] not in (cfg.get("move") or {}) and o["aabb"][2] < FLOOR_Z_M:
            out.append(o["aabb"][:2] + o["aabb"][3:5])
    for where in (cfg.get("move") or {}, add):
        for n, m in where.items():
            s = sups.get(m.get("support"))
            z = s["z"] if s else m.get("z")
            if m.get("xy") and n not in cfg["remove"] and (z is None or z < FLOOR_Z_M):
                out.append(_box(_asset_of(base, n, add), m))
    return out


def apply_layout(cfg, spec, rng):
    """Draw the seed's layout into ``cfg`` (``move`` / ``add`` poses and ``start``); records ``layout_applied``."""
    base = cfg["base"]
    applied = {}
    current = {i: list(c["box"]) for i, c in enumerate(spec["clusters"])}
    order = list(range(len(spec["clusters"])))
    rng.shuffle(order)
    # the largest first: on a top every cluster wants the strip along a free edge, and a small one placed
    # first can leave no room in it for a long one (T14: the red book before the mug, notebook and pencil)
    area = lambda i: (spec["clusters"][i]["box"][2] - spec["clusters"][i]["box"][0]) * \
        (spec["clusters"][i]["box"][3] - spec["clusters"][i]["box"][1])  # noqa: E731
    order.sort(key=lambda i: -area(i))
    for i in order:
        c = spec["clusters"][i]
        others = list(spec["static"].get(c["support"], [])) + \
            [current[k] for k, o in enumerate(spec["clusters"]) if k != i and o["support"] == c["support"]]
        dx = dy = 0.0
        edges = (spec.get("reach") or {}).get(c["support"])

        members = [_box(_asset_of(base, n, cfg.get("add") or {}), (cfg["move"].get(n) or cfg["add"][n]))
                   for n in c.get("pick") or c["names"]     # what the route picks must be in reach; the rest comes along
                   if (cfg["move"].get(n) or (cfg.get("add") or {}).get(n) or {}).get("xy")]

        every = [_box(_asset_of(base, n, cfg.get("add") or {}), (cfg["move"].get(n) or cfg["add"][n]))
                 for n in c["names"] if (cfg["move"].get(n) or (cfg.get("add") or {}).get(n) or {}).get("xy")] \
            or [c["box"]]

        def fits(tx, ty, each=True):
            sh = lambda r: [r[0] + tx, r[1] + ty, r[2] + tx, r[3] + ty]  # noqa: E731
            b = sh(c["box"])
            # each object against what stands there (the cluster's whole box takes in what lies between them)
            if any(_overlap(sh(m), o, CLEAR_M) for m in every for o in others):
                return False
            # every object of the cluster within reach; a cluster too deep for that: the cluster at the edge
            return edges is None or (all(reachable(sh(m), edges) for m in members) if each else reachable(b, edges))
        for _ in range(REACH_TRIES if edges is not None else TRIES):
            tx = _grid(rng, c["dx"]) if "dx" in c else 0.0
            ty = _grid(rng, c["dy"]) if "dy" in c else 0.0
            if fits(tx, ty):
                dx, dy = tx, ty
                break
        else:
            if edges is not None:                      # a crowded top: every free place in reach, one at random
                axis = lambda k: [round(c[k][0] + i * 0.02, 2) for i in range(int((c[k][1] - c[k][0]) / 0.02) + 1)] \
                    if k in c else [0.0]  # noqa: E731
                grid = [(tx, ty) for tx in axis("dx") for ty in axis("dy")]
                ok = [g for g in grid if fits(*g)] or [g for g in grid if fits(*g, each=False)]
                if ok:
                    dx, dy = rng.choice(ok)
        current[i] = [c["box"][0] + dx, c["box"][1] + dy, c["box"][2] + dx, c["box"][3] + dy]
        for n in c["names"]:
            where = cfg["move"] if n in cfg["move"] else cfg["add"]
            m = dict(where[n])
            m["xy"] = [round(m["xy"][0] + dx, 4), round(m["xy"][1] + dy, 4)]
            where[n] = m
        applied["+".join(c["names"])] = [round(dx, 2), round(dy, 2)]
    st = spec["start"]
    cells = _cells().get(base, {}).get(st["room"] or "", [])
    floor = _floor_boxes(cfg)
    for _ in range(TRIES * 2 if cells else 0):
        x, y = rng.choice(cells)
        yaw = float(rng.randrange(0, 360, 15))
        if any(b[0] - FLOOR_CLEAR_M < x < b[2] + FLOOR_CLEAR_M and b[1] - FLOOR_CLEAR_M < y < b[3] + FLOOR_CLEAR_M
               for b in floor):
            continue
        if any(_in_view(base, x, y, yaw, p) for p in (_point(base, cfg, n) for n in st["hide"]) if p):
            continue
        if any(math.hypot(p[0] - x, p[1] - y) > VIEW_RANGE_M or _blocked(base, (x, y), p)
               for p in (_point(base, cfg, n) for n in st["look"]) if p):
            continue
        cfg["start"] = [x, y, yaw]
        applied["start"] = [x, y, yaw]
        break
    cfg["layout_applied"] = applied


def main():
    doc = json.loads((ROOT / "benchmark/v6/tasks.json").read_text())
    cells = start_cells({t["scene"]["base"] for t in doc["tasks"]})
    CELLS.write_text(json.dumps(cells))
    for b, r in cells.items():
        print(b, {k: len(v) for k, v in r.items()})


if __name__ == "__main__":
    main()
