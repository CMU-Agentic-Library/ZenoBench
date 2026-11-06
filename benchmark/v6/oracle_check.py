"""Symbolic check of every v6 oracle route: replay the route on a symbolic state and test the goal.

The static checks (validate_v6.py) look at each step on its own: the skill exists, the inputs are well typed,
the objects are there.  This file runs the route as a plan:

* the state: where each object is (on a support, in or on another object, in the hand), which doors are open,
  which lid covers which container, the food temperatures, what was wiped / stirred / hidden / observed, and
  where the robot is (the place it last navigated to);
* before each step, the skill's preconditions (from the skill contracts, plus the physical ones the contracts
  leave to the geometry: an item in closed furniture needs the door open, a covered container takes nothing,
  a stack base must be clear, the robot must be near what it handles);
* after each step, its effects; a dynamic event fires after the step its trigger matches;
* at the end, the goal: every ``all`` atom and one ``any`` group.  Atoms that only geometry can decide
  (upright, grouped, clear_of, away_from_edge, front_visible, squared, visible_from) are counted as unchecked;
  near_start / near_any are judged from the route's place points.

    python benchmark/v6/oracle_check.py            # all routes; writes ORACLE_CHECK.json, exits 1 on a problem
    python benchmark/v6/oracle_check.py --task T09 # one task, printed
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmark.v6.routes import trig_hits  # noqa: E402

HERE = Path(__file__).resolve().parent
NEAR_M = 1.6            # base_near: the robot within reach of the place (the contracts use 1.3 m from the base
                        # centre; the place it navigated to is a point at the support, not the base)
NEAR_START_M = 0.15
GEOMETRIC = {"same_arrangement", "upright", "grouped", "clear_of", "away_from_edge", "front_visible", "squared", "visible_from"}


@lru_cache(maxsize=None)
def scene(base):
    from zeno_skills.annotations import SceneAnnotations
    ann = SceneAnnotations(ROOT / base / "annotation.json")
    raw = json.loads((ROOT / base / "annotation.json").read_text())
    return ann, raw


class World:
    def __init__(self, task, lid):
        self.task, self.lid = task, lid
        self.ann, raw = scene(task["scene"]["base"])
        v = task["variants"][lid]
        self.supports = {s["name"]: s for s in raw["supports"]}
        self.articulated = {a["name"] for a in raw["articulated"]}
        self.appliances = {a["name"]: a for a in raw["appliances"]}
        self.rooms = raw["rooms"]
        self.obst = {}
        for o in raw["obstacles"]:
            self.obst.setdefault(o["name"].split("/")[0], []).append(o["aabb"])
        for a in raw["appliances"]:
            self.obst.setdefault(a["name"], []).append(a["body_aabb"])
        # objects: name -> {asset, xy, z, sup}
        self.obj = {}
        for o in raw["objects"]:
            self.obj[o["name"]] = dict(asset=o["asset"], xy=list(o["position"][:2]), z=o["position"][2],
                                      sup=o.get("support"))
        removed = set(task["scene"].get("remove") or []) | set(v.get("remove") or [])
        for src in (task["scene"].get("add") or {}, task["scene"].get("move") or {}, v.get("add") or {},
                    v.get("move") or {}):
            for n, m in src.items():
                o = self.obj.setdefault(n, dict(asset=m.get("asset"), xy=None, z=None, sup=None))
                if m.get("asset"):
                    o["asset"] = m["asset"]
                o["xy"] = list(m["xy"])
                o["sup"] = m.get("support")
                o["z"] = m.get("z") if m.get("z") is not None else (
                    self.supports[m["support"]]["z"] if m.get("support") in self.supports else None)
                removed.discard(n)
        for n in removed:
            self.obj.pop(n, None)
        self.start = {n: list(o["xy"]) for n, o in self.obj.items()}
        # where each object is: ("sup", support) | ("in", container) | ("top", base object) | ("hand",)
        self.loc = {}
        self.covered = {}                       # container -> lid
        for n, o in self.obj.items():
            self.loc[n] = ("sup", o["sup"]) if o["sup"] else self._resting_on(n)
        for n in list(self.loc):                        # a lid resting on a container covers it
            if "lid" not in self.tags(n):
                continue
            o = self.obj[n]
            for c, p in self.obj.items():
                if c != n and "lid" not in self.tags(c) and p["xy"] and o["xy"] and p["z"] is not None \
                        and o["z"] is not None and p["z"] < o["z"] and math.dist(p["xy"], o["xy"]) < 0.04 \
                        and (o["sup"] is None or o["sup"] == p["sup"]) \
                        and ("container" in self.tags(c) or "pot" in self.tags(c)):
                    self.loc[n] = ("top", c)
                    self.covered[c] = n
        self.open = set()
        for f in v.get("failures") or []:
            ev = f.get("event") or {}
            if f.get("when") == "initial" and ev.get("type") == "set_joint":
                (self.open.add if ev["value"] == "open" else self.open.discard)(ev["articulated"])
        self.hand = None
        self.at = None                          # xy of the place the robot last went to
        self.at_name = None
        self.temp = {}
        self.heating = set()
        self.flags = set()                      # ("wiped", s), ("stirred", c), ("hidden", o), ("observed", x), ...
        self.problems = []

    # ------------------------------------------------------------------ helpers
    def tags(self, n):
        o = self.obj.get(n)
        if not o or not o["asset"]:
            return set()
        a = self.ann.assets.get(o["asset"]) or {}
        t = set(a.get("tags") or [])
        if a.get("container"):
            t.add("container")
        return t

    def half(self, n):
        a = self.ann.assets.get(self.obj[n]["asset"] or "") or {}
        sz = a.get("size") or [0.1, 0.1]
        return max(sz[0], sz[1]) / 2

    def _resting_on(self, n):
        """An object with no support (z given): in or on the nearest lower object under it."""
        o = self.obj[n]
        best = None
        for m, p in self.obj.items():                   # a container whose footprint holds it
            if m == n or "container" not in self.tags(m) or not p["xy"] or not o["xy"] or p["z"] is None \
                    or o["z"] is None or p["z"] > o["z"] + 0.01:
                continue
            d = math.dist(o["xy"], p["xy"])
            if d < self.half(m) and (best is None or self.half(m) < best[0]):   # the innermost container
                best = (self.half(m), m)
        if best:
            return ("in", best[1])
        for m, p in self.obj.items():
            if m == n or not p["xy"] or not o["xy"] or p["z"] is None or o["z"] is None or p["z"] >= o["z"] - 0.005:
                continue
            d = math.dist(o["xy"], p["xy"])
            key = (round(d, 2), -p["z"])               # the nearest, and of a stack the one just below
            if d < 0.16 and (best is None or key < best[0]):
                best = (key, m)
        if not best:
            return ("sup", None)
        m = best[1]
        return ("in", m) if "container" in self.tags(m) else ("top", m)

    def support_of(self, n):
        """The support (a furniture surface) an object finally rests on, through containers and stacks."""
        seen = set()
        while n in self.loc and n not in seen:
            seen.add(n)
            k, *rest = self.loc[n]
            if k == "sup":
                return rest[0]
            if k == "hand":
                return None
            n = rest[0]
        return None

    def chain(self, n):
        """n, then what holds it: [n, container, ..., support]."""
        out = [n]
        while out[-1] in self.loc:
            k, *rest = self.loc[out[-1]]
            if k == "hand" or not rest or rest[0] in out:
                break
            out.append(rest[0])
        return out

    def xy(self, name):
        if name in self.obj:
            if self.loc.get(name, ("",))[0] == "hand":
                return self.at
            return self.obj[name]["xy"]
        if name in self.supports:
            b = self.supports[name]["aabb_xy"]
            return [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]
        base = name.split("/")[0]
        if base in self.obst:
            bs = self.obst[base]
            return [(min(b[0] for b in bs) + max(b[3] for b in bs)) / 2, (min(b[1] for b in bs) + max(b[4] for b in bs)) / 2]
        if base in self.supports:
            return self.xy(base)
        sup = [s for s in self.supports if s.startswith(base + "/")]
        if sup:
            return self.xy(sup[0])
        return None

    def footprint(self, name):
        if name in self.supports:
            return self.supports[name]["aabb_xy"]
        base = name.split("/")[0]
        if base in self.obst:
            bs = self.obst[base]
            return [min(b[0] for b in bs), min(b[1] for b in bs), max(b[3] for b in bs), max(b[4] for b in bs)]
        p = self.xy(name)
        return [p[0], p[1], p[0], p[1]] if p else None

    def near(self, name):
        if self.at is None:
            return False
        if self.at_name and (self.at_name == name or self.at_name in self.chain(name)
                             or (self.support_of(name) or "").split("/")[0] == self.at_name.split("/")[0]
                             or name.split("/")[0] == self.at_name.split("/")[0]):
            return True
        fp = self.footprint(name) if name not in self.obj else None
        p = self.xy(name)
        if fp:
            dx = max(fp[0] - self.at[0], 0, self.at[0] - fp[2])
            dy = max(fp[1] - self.at[1], 0, self.at[1] - fp[3])
            return math.hypot(dx, dy) <= NEAR_M
        return p is not None and math.dist(p, self.at) <= NEAR_M

    def closed_around(self, n):
        """The closed furniture or appliance an object (or support) is in, if any."""
        names = self.chain(n) if n in self.obj else [n]
        sup = self.support_of(n) if n in self.obj else n
        for x in names + [sup or ""]:
            f = (x or "").split("/")[0]
            if "/inside" in (x or "") and f in self.articulated and f not in self.open:
                return f
        return None

    def see(self, t):
        """A look at a place: it and what stands there in plain sight (not in closed furniture, not under a lid)."""
        self.flags.add(("observed", t))
        for n in self.obj:
            if n == t or self.closed_around(n) or any(c in self.covered for c in self.chain(n)[1:]):
                continue
            if t in self.chain(n)[1:] or (self.support_of(n) or "").split("/")[0] == t.split("/")[0] and (
                    "/" not in t or self.support_of(n) == t):
                self.flags.add(("observed", n))

    def bad(self, i, step, msg):
        self.problems.append({"step": i, "skill": step["skill"], "problem": msg})

    def need_near(self, i, s, name):
        if name and not self.near(name):
            self.bad(i, s, f"not near {name} (last went to {self.at_name})")

    def need_hold(self, i, s, n):
        if self.hand != n:
            self.bad(i, s, f"not holding {n} (holding {self.hand})")

    def need_empty(self, i, s):
        if self.hand:
            self.bad(i, s, f"hand not empty (holding {self.hand})")

    def need_reach(self, i, s, n):
        f = self.closed_around(n)
        if f:
            self.bad(i, s, f"{n} is inside closed {f}")
        for c, lid in self.covered.items():
            if n in self.obj and c in self.chain(n)[1:] and lid != n:
                self.bad(i, s, f"{n} is in {c}, covered by {lid}")

    def put(self, n, where, xy=None):
        self.loc[n] = where
        if xy is None and where[0] != "hand":
            xy = self.xy(where[1])
        if xy is not None and n in self.obj:
            self.obj[n]["xy"] = list(xy)
        if where[0] != "hand":
            for c, lid in list(self.covered.items()):
                if lid == n:
                    del self.covered[c]

    # ------------------------------------------------------------------ steps
    def step(self, i, s):
        a, k = s["args"], s["skill"]
        if k == "navigate":
            d = a["destination"]
            self.at, self.at_name = self.xy(d), d
            if self.at is None:
                self.bad(i, s, f"unknown destination {d}")
        elif k in ("search",):
            o = a.get("object")
            if o in self.obj:
                self.at, self.at_name = self.xy(o), o
                self.flags.add(("observed", o))
        elif k == "explore_furniture":
            f = a["furniture"]
            self.at, self.at_name = self.xy(f), f
            was = f in self.open                   # the skill looks inside; it leaves the door as it found it
            self.open.add(f) if f in self.articulated else None
            self.see(f)
            if not was:
                self.open.discard(f)
        elif k == "explore_room":
            self.at, self.at_name = None, None
        elif k in ("look", "inspect", "identify", "measure"):
            t = a.get("target") or a.get("receptacle") or a.get("object")
            if k == "inspect":
                self.need_near(i, s, t)
            self.see(t)
        elif k == "approach":
            self.need_near(i, s, a["target"])
        elif k == "pick":
            n = a["object"]
            self.need_empty(i, s)
            if n not in self.obj:
                return self.bad(i, s, f"{n} is not in the scene")
            self.need_near(i, s, n)
            self.need_reach(i, s, n)
            on = [m for m, w in self.loc.items() if w == ("top", n) and self.covered.get(n) != m]
            if on:
                self.bad(i, s, f"{', '.join(on)} lies on {n}")
            self.put(n, ("hand",))
            self.hand = n
        elif k in ("place", "drop", "stack"):
            n = a["object"]
            tgt = a.get("receptacle") or a.get("container") or a.get("base")
            self.need_hold(i, s, n)
            self.need_near(i, s, tgt)
            if tgt in self.obj:
                self.need_reach(i, s, tgt)
                if self.covered.get(tgt):
                    self.bad(i, s, f"{tgt} is covered by {self.covered[tgt]}")
                if k == "stack":
                    on = [m for m, w in self.loc.items() if w == ("top", tgt)]
                    if on:
                        self.bad(i, s, f"top of {tgt} not clear ({', '.join(on)})")
                where = ("top", tgt) if k == "stack" or "container" not in self.tags(tgt) else ("in", tgt)
                xy = self.xy(tgt)
            else:
                f = self.closed_around(tgt)
                if f:
                    self.bad(i, s, f"{tgt} is inside closed {f}")
                if tgt not in self.supports:
                    self.bad(i, s, f"unknown receptacle {tgt}")
                where, xy = ("sup", tgt), a.get("hint_xy") or self.xy(tgt)
            self.put(n, where, xy)
            if self.obj.get(n):
                self.obj[n]["placed_at"] = list(xy) if xy else None
            self.hand = None
        elif k == "hide":
            n, c, lid = a["object"], a["receptacle"], a.get("lid")
            self.need_empty(i, s)
            self.need_near(i, s, n)
            if self.covered.get(c) and self.covered[c] != lid:
                self.bad(i, s, f"{c} is covered by {self.covered[c]}, not {lid}")
            if self.covered.get(c) == lid:              # the skill lifts its own lid off first
                del self.covered[c]
            self.need_reach(i, s, n)
            self.put(n, ("in", c))
            if lid:
                self.put(lid, ("top", c))
                self.covered[c] = lid
            self.flags.add(("hidden", n))
        elif k in ("open", "close"):
            art = a["articulated"]
            self.need_near(i, s, art)
            if art not in self.articulated:
                self.bad(i, s, f"{art} does not open")
            (self.open.add if k == "open" else self.open.discard)(art)
            if k == "close" and self.hand and self.closed_around(self.hand) == art:
                self.bad(i, s, f"closing {art} on the held {self.hand}")
        elif k == "uncover":
            c = a["container"]
            self.need_empty(i, s)
            self.need_near(i, s, c)
            lid = self.covered.pop(c, None)
            if not lid:
                self.bad(i, s, f"{c} is not covered")
            else:                               # the skill sets the lid down next to the container
                self.put(lid, ("sup", self.support_of(c)), self.xy(c))
        elif k == "cover":
            c, lid = a["container"], a["lid"]
            self.need_hold(i, s, lid)
            self.need_near(i, s, c)
            if self.covered.get(c):
                self.bad(i, s, f"{c} already covered by {self.covered[c]}")
            self.put(lid, ("top", c))
            self.covered[c] = lid
            self.hand = None
        elif k == "stir":
            self.need_hold(i, s, a["tool"])
            self.need_near(i, s, a["container"])
            if self.covered.get(a["container"]):
                self.bad(i, s, f"{a['container']} is covered")
            self.flags.add(("stirred", a["container"]))
        elif k == "wipe":
            self.need_hold(i, s, a["tool"])
            self.need_near(i, s, a["surface"])
            self.flags.add(("wiped", a["surface"]))
        elif k == "collect":
            self.need_empty(i, s)
            c = a["container"]
            if self.covered.get(c):
                self.bad(i, s, f"{c} is covered")
            for n in a["objects"]:
                self.need_reach(i, s, n)
                self.put(n, ("in", c))
        elif k in ("heat", "stop", "press"):
            app = a.get("appliance") or a["button"].split("/")[0]
            self.need_empty(i, s)
            self.need_near(i, s, app)
            if k == "heat":
                if a["food"] not in self.on_appliance(app):
                    self.bad(i, s, f"{a['food']} is not in / on {app}")
                self.warm(app, float(a["temp_c"]))
                self.heating.discard(app)
            elif k == "stop":
                if app in self.heating:
                    self.warm(app, 100.0)
                self.heating.discard(app)
                if app in self.articulated:            # the microwave stops when its door is opened
                    self.open.add(app)
            else:
                self.heating.add(app)
        elif k == "wait":
            for app in self.heating:
                self.warm(app, 100.0)
        elif k == "flip":
            self.need_empty(i, s)
            self.need_near(i, s, a["object"])
            self.flags.add(("flipped", a["object"]))
        elif k == "roll":
            self.need_empty(i, s)
            self.need_near(i, s, a["object"])
            self.flags.add(("object_rolled", a["object"]))
        elif k in ("expose", "separate", "push", "touch"):
            self.need_empty(i, s)
            self.need_near(i, s, a["object"])
        elif k in ("rotate", "lift", "hover", "present"):
            self.need_hold(i, s, a["object"])
        # retreat, bend, straighten, wait, nod, count, sweep: no state the goal reads

    def on_appliance(self, app):
        """What stands in or on an appliance (through pots and bowls)."""
        return [n for n in self.obj if self.loc[n][0] != "hand"
                and (self.support_of(n) or "").split("/")[0] == app]

    def warm(self, app, t):
        for n in self.on_appliance(app):
            self.temp[n] = max(self.temp.get(n, 20.0), t)

    def event(self, f):
        ev = f.get("event") or {}
        if ev.get("type") == "set_joint":
            (self.open.add if ev["value"] == "open" else self.open.discard)(ev["articulated"])
        elif ev.get("type") == "move_object":
            n, to = ev["object"], ev.get("to") or {}
            if ev.get("onto") and "lid" in self.tags(n):
                self.put(n, ("top", ev["onto"]), to.get("xy"))
                self.covered[ev["onto"]] = n
            elif ev.get("onto"):
                self.put(n, ("in" if "container" in self.tags(ev["onto"]) else "top", ev["onto"]), to.get("xy"))
            elif to.get("support"):
                self.put(n, ("sup", to["support"]), to.get("xy"))

    # ------------------------------------------------------------------ goal
    def holds(self, at):
        neg = at[0].startswith("not ")
        p = at[0][4:] if neg else at[0]
        r = self._holds(p, at[1:])
        if r is None:
            return None
        return r != neg

    def _in(self, n, c):
        ch = self.chain(n)
        if c in ch[1:]:
            return True
        sup = self.support_of(n) or ""
        return sup == c or sup.split("/")[0] == c

    def _holds(self, p, args):
        many = lambda x: x if isinstance(x, list) else [x]  # noqa: E731
        if p in GEOMETRIC:
            return None
        if p == "hand_empty":
            return self.hand is None
        if p in ("on",):
            n, sup = args[0], args[1]
            s = self.support_of(n)
            return s == sup or (s or "").split("/")[0] == sup or (s or "") == sup + "/top" or self._in(n, sup)
        if p in ("inside", "fully_inside"):
            return all(self._in(n, args[1]) for n in many(args[0]))
        if p == "on_top_of":
            return self.loc.get(args[0]) == ("top", args[1]) or args[1] in self.chain(args[0])[1:]
        if p == "covered":
            return self.covered.get(args[0]) == (args[1] if len(args) > 1 else self.covered.get(args[0])) \
                and args[0] in self.covered
        if p == "is_closed":
            return args[0] not in self.open
        if p == "is_open":
            return args[0] in self.open
        if p == "heating":
            return args[0] in self.heating
        if p == "temperature_at_least":
            return self.temp.get(args[0], 20.0) >= float(args[1])
        if p in ("wiped", "stirred", "hidden", "flipped", "object_rolled", "observed"):
            return (p, args[0]) in self.flags
        if p == "on_floor":
            return (self.support_of(args[0]) or "").startswith("floor")
        if p == "near_start":
            return all(n in self.obj and self.obj[n]["xy"] is not None and self.loc[n][0] != "hand"
                       and math.dist(self.obj[n]["xy"], self.start[n]) <= NEAR_START_M for n in many(args[0]))
        if p == "near_any":
            n, refs = args[0], args[1]
            dist = float(args[2]) if len(args) > 2 else 0.3
            if n not in self.obj or self.obj[n]["xy"] is None:
                return False
            return any(r in self.obj and math.dist(self.obj[n]["xy"], self.obj[r]["xy"]) - self.half(n) - self.half(r)
                       <= dist for r in refs)
        if p == "count_on_at_least":
            objs, sup, k = many(args[0]), args[1], int(args[2])
            return sum(1 for n in objs if n in self.obj and self._holds("on", [n, sup])) >= k
        return None

    def goal(self, g):
        rows = [(a, self.holds(a)) for a in g.get("all", [])]
        groups = [[(a, self.holds(a)) for a in grp] for grp in g.get("any", [])]
        fails = [a for a, h in rows if h is False]
        any_ok = not groups or any(all(h is not False for _, h in grp) for grp in groups)
        unchecked = sum(1 for _, h in rows if h is None) + sum(1 for grp in groups for _, h in grp if h is None)
        checked = sum(1 for _, h in rows if h is not None) + sum(1 for grp in groups for _, h in grp if h is not None)
        return fails, any_ok, groups, checked, unchecked


def check(task, lid):
    w = World(task, lid)
    v = task["variants"][lid]
    steps = task["routes"][task["oracle"][lid]]["steps"]
    fires = {}
    for f in v.get("failures") or []:
        if f.get("when") == "dynamic" and f.get("event"):
            hits = trig_hits(steps, f)
            if hits:
                fires.setdefault(hits[0], []).append(f)
    for i, s in enumerate(steps):
        if s.get("expect") != "fail":              # a call the route expects to fail changes nothing
            w.step(i, s)
        for f in fires.get(i, []):
            w.event(f)
    g = v.get("goal") or task.get("goal") or {}
    fails, any_ok, groups, checked, unchecked = w.goal(g)
    probs = list(w.problems)
    for a in fails:
        probs.append({"step": None, "skill": "goal", "problem": f"goal atom false at the end: {a}"})
    if not any_ok:
        probs.append({"step": None, "skill": "goal", "problem": "no any-group holds: " + " | ".join(
            ", ".join(f"{a}={h}" for a, h in grp) for grp in groups)})
    return {"task": task["task_id"], "layout": lid, "steps": len(steps), "atoms_checked": checked,
            "atoms_geometric": unchecked, "problems": probs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task")
    ap.add_argument("--tasks", default=str(HERE / "tasks.json"))
    args = ap.parse_args()
    doc = json.loads(Path(args.tasks).read_text())
    out = []
    for t in doc["tasks"]:
        if args.task and not t["task_id"].startswith(args.task):
            continue
        for vid, info in t["v6_variants"].items():
            for lid in info["layouts"]:
                r = check(t, lid)
                r["variant"] = vid
                out.append(r)
    bad = [r for r in out if r["problems"]]
    for r in bad:
        print(f"{r['task']} {r['layout']}:")
        for p in r["problems"]:
            print(f"   step {p['step']} {p['skill']}: {p['problem']}")
    n_at = sum(r["atoms_checked"] for r in out)
    n_geo = sum(r["atoms_geometric"] for r in out)
    print(f"{len(out)} routes, {len(out) - len(bad)} ok, {len(bad)} with problems; goal atoms checked "
          f"symbolically {n_at}, left to geometry {n_geo}")
    if not args.task:
        (HERE / "ORACLE_CHECK.json").write_text(json.dumps(
            {"routes": len(out), "ok": len(out) - len(bad), "results": out}, indent=1, ensure_ascii=False) + "\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
