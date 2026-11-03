"""Seed layout generator: where the objects stand and where the robot starts.

A variant fixes the task design (scene conditions, events, substitutes, goal, and the placements a challenge is
made of); the seed draws the rest of the layout:

* **objects**: every cluster of task objects on an open support (objects closer than ``CLUSTER_GAP_M``, a stack,
  a crowded group) is shifted as a whole to a random free place on the same support.  An axis on which the
  cluster is within ``EDGE_LOCK_M`` of the support edge does not move (an overhang stays), the cluster never goes
  deeper from the edge it is reached from than it was (or ``DEPTH_FREE_M``), it keeps out of the places the
  oracle route or an event puts objects on, and objects on those places, in closed furniture or on an appliance
  do not move;
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
CELLS = ROOT / "benchmark/v6/start_cells.json"

CLUSTER_GAP_M = 0.03     # objects closer than this on one support move together
EDGE_LOCK_M = 0.04       # a cluster this close to a support edge does not move across it
DEPTH_FREE_M = 0.15      # a cluster may always lie this deep from the edge it is reached from
CLEAR_M = 0.01           # clearance between a moved cluster and anything else on the support
CELL_M = 0.2             # start-cell grid
VIEW_HALF_DEG = 45.0     # half the start view (head camera, head straight)
VIEW_RANGE_M = 6.0
FLOOR_CLEAR_M = 0.45     # no start this close to an object on the floor (bottom below FLOOR_Z_M), as v5 checks
FLOOR_Z_M = 0.15
TRIES = 40
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
    hx, hy = a["size"][0] / 2, a["size"][1] / 2
    if abs(math.sin(math.radians(m.get("yaw_deg", 0.0)))) > 0.7:
        hx, hy = hy, hx
    return [m["xy"][0] - hx, m["xy"][1] - hy, m["xy"][0] + hx, m["xy"][1] + hy]


def _overlap(a, b, gap=0.0):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def _union(bs):
    return [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)]


def _asset_of(base, name, add):
    if name in add:
        return add[name]["asset"]
    return {o["name"]: o for o in _ann(base)["objects"]}[name]["asset"]


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


def layout_spec(task, vid, registry):
    """The ``layout`` block of one concrete variant; ``registry``: the condition registry (condition -> type)."""
    v = task["variants"][vid]
    scene, base = task["scene"], task["scene"]["base"]
    sups = _sups(base)
    removed = set(scene.get("remove", [])) | set(v.get("remove", []))
    move = {**scene.get("move", {}), **v.get("move", {})}
    add = {**scene.get("add", {}), **v.get("add", {})}
    placed = {**move, **add}
    steps = task["routes"][task["oracle"][vid]]["steps"]
    keep_out = reserved(task, vid, steps)
    boxes = {n: _box(_asset_of(base, n, add), m) for n, m in placed.items() if m.get("xy")}
    # stacked objects (no support) go with the object they stand on
    under = {}
    for n, m in placed.items():
        if not m.get("support") and n in boxes:
            below = [k for k, b in boxes.items() if k != n and placed[k].get("support") and _overlap(b, boxes[n])]
            if below:
                under[n] = below[0]
    movable = {}
    for n, m in placed.items():
        sup = m.get("support")
        if n in under or n not in boxes:
            continue
        if sup not in sups or _fixed_support(base, sup) or \
                any(_overlap(boxes[n], r) for r in keep_out.get(sup, [])):
            continue
        movable.setdefault(sup, []).append(n)
    clusters = []
    for sup, names in sorted(movable.items()):
        groups = [[n] for n in sorted(names)]
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
            for ax, lo_k, hi_k in (("dx", "x0", "x1"), ("dy", "y0", "y1")):
                if min(dist[lo_k], dist[hi_k]) < EDGE_LOCK_M:
                    continue
                lo, hi = -dist[lo_k] + CLEAR_M, dist[hi_k] - CLEAR_M
                depth = max(dist[near], DEPTH_FREE_M)
                if near == lo_k:
                    hi = min(hi, depth - dist[lo_k])
                elif near == hi_k:
                    lo = max(lo, dist[hi_k] - depth)
                lo, hi = math.ceil(lo * 100) / 100, math.floor(hi * 100) / 100
                if hi - lo >= 0.01:
                    rng[ax] = [min(lo, 0.0), max(hi, 0.0)]
            if rng:
                clusters.append({"names": g, "support": sup, "box": [round(x, 4) for x in B], **rng})
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
    return {"clusters": clusters, "static": static,
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
    for i in order:
        c = spec["clusters"][i]
        others = list(spec["static"].get(c["support"], [])) + \
            [current[k] for k, o in enumerate(spec["clusters"]) if k != i and o["support"] == c["support"]]
        dx = dy = 0.0
        for _ in range(TRIES):
            tx = _grid(rng, c["dx"]) if "dx" in c else 0.0
            ty = _grid(rng, c["dy"]) if "dy" in c else 0.0
            b = [c["box"][0] + tx, c["box"][1] + ty, c["box"][2] + tx, c["box"][3] + ty]
            if not any(_overlap(b, o, CLEAR_M) for o in others):
                dx, dy = tx, ty
                break
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
