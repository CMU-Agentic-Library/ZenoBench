"""Success checker: scores a task's goal (task.json) against simulator state.

    ev = TaskEvaluator(task_json, SceneAnnotations(annotation_json))
    report = ev.evaluate(state)        # state = rig_state(rig) or any dict below
    report["success"], report["progress"], report["conditions"]

state = {"objects": {name: {"pos": [x, y, z], "quat": [w, x, y, z]}},
         "joints":  {articulated_name: q}}

Pure Python (numpy only): runs inside a rollout, on a saved state, or in a
unit test.  Every condition reads simulator or task state, never the policy action log.

Conditions (``goal = {"all": [...]}``), slots as in tasks.py:
  on          {"on": slots, "support": place|[places], "upright": bool}
              bottom of the object on the surface (-2..+5 cm, so resting
              on a thin item such as a plate still counts) and its
              footprint centre inside the surface's xy box
  inside      {"inside": slots, "container": slot, "bind": name}
              object centre inside the container's wall profile, between
              its floor and 3 cm above the rim; one container must hold
              every slot; the container used is bound for later conditions
  upright     {"upright": slots, "max_tilt_deg": 20}
  near        {"near": slots, "max_dist": m, "support": place}
              one instance per slot (on that support), pairwise within
              max_dist
  heated      {"heated": slots, "appliance": name, "min_temp_c": C}
  closed      {"closed": "all" | [articulated names], "tol": rad or m}
  not_dropped {"not_dropped": "all"}  no object that started above 10 cm
              lies on the floor (unless it is inside a container)
"""

from __future__ import annotations

import itertools
import math

import numpy as np

from .tasks import Slots, place_name, task_roles

UPRIGHT_DEG = 20.0


def quat_R(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def tilt_deg(q):
    R = quat_R(q)
    return math.degrees(math.acos(max(-1.0, min(1.0, R[2, 2]))))


def rig_state(rig):
    """Snapshot of every annotated object and articulated joint of a Rig."""
    objs = {}
    for name in rig.ann.objects:
        p, q = rig.obj_pose(name)
        objs[name] = {"pos": [float(v) for v in p], "quat": [float(v) for v in q]}
    return {"objects": objs, "joints": {a["name"]: rig.joint(a["name"]) for a in rig.ann.articulated}}


class Geometry:
    """Object/support/container geometry from annotations + a state dict."""

    def __init__(self, ann):
        self.ann = ann

    def _asset(self, name):
        return self.ann.asset_of(self.ann.objects[name])

    def bottom(self, name, st):
        """World bottom-centre of the object's box (object frame -> world)."""
        o = st["objects"][name]
        R = quat_R(o["quat"])
        return np.asarray(o["pos"], float) + R @ np.asarray(self._asset(name)["origin_to_bottom_center"], float)

    def centre(self, name, st):
        o = st["objects"][name]
        R = quat_R(o["quat"])
        a = self._asset(name)
        c = np.asarray(a["origin_to_bottom_center"], float) + np.array([0, 0, a["size"][2] / 2])
        return np.asarray(o["pos"], float) + R @ c

    def footprint(self, name, st, margin=0.0):
        """World xy box [x0, y0, x1, y1] of the object's (yawed) footprint."""
        o = st["objects"][name]
        R = quat_R(o["quat"])
        sx, sy, _ = self._asset(name)["size"]
        c = self.centre(name, st)
        hx = abs(R[0, 0]) * sx / 2 + abs(R[0, 1]) * sy / 2 + margin
        hy = abs(R[1, 0]) * sx / 2 + abs(R[1, 1]) * sy / 2 + margin
        return np.array([c[0] - hx, c[1] - hy, c[0] + hx, c[1] + hy])

    def surfaces(self, place):
        """Support dicts a raw place stands for ([] for floor places)."""
        if isinstance(place, list):
            return [s for p in place for s in self.surfaces(p)]
        if isinstance(place, dict) or place == "floor" or place.startswith("floor"):
            return []
        out = [s for s in self.ann.supports if s["name"] == place]
        return out or [s for s in self.ann.supports if s.get("furniture") == place]

    def on(self, name, place, st):
        b = self.bottom(name, st)
        places = place if isinstance(place, list) else [place]
        for p in places:
            if isinstance(p, dict) or p == "floor":
                room = p.get("floor") if isinstance(p, dict) else None
                if b[2] < 0.05 and (room is None or self.room(b[:2]) == room):
                    return True, f"on floor ({self.room(b[:2])})"
                continue
            for s in self.surfaces(p):
                x0, y0, x1, y1 = s["aabb_xy"]
                if x0 - 0.02 <= b[0] <= x1 + 0.02 and y0 - 0.02 <= b[1] <= y1 + 0.02 \
                        and -0.02 <= b[2] - s["z"] <= 0.05:
                    return True, s["name"]
        return False, f"bottom at ({b[0]:.2f}, {b[1]:.2f}, {b[2]:.3f})"

    def inside(self, name, cont, st):
        if name == cont:
            return False, "is the container"
        ca = self._asset(cont)
        prof = ca.get("container")
        if not prof:
            return False, f"{cont} is not a container"
        cb = self.bottom(cont, st)
        R = quat_R(st["objects"][cont]["quat"])
        local = R.T @ (self.centre(name, st) - cb)
        top = prof["rim_height"] + 0.03
        if not (-0.01 <= local[2] <= top):
            return False, f"height {local[2]:.3f} m outside [0, {top:.3f}]"
        if prof["shape"] == "round":
            r = float(np.hypot(local[0], local[1]))
            lim = max(b[2] for b in prof["bands"]) + 0.01
            return r <= lim, f"r {r:.3f} / {lim:.3f}"
        _, _, hx, hy = prof["bands"][0]
        ok = abs(local[0]) <= hx + 0.01 and abs(local[1]) <= hy + 0.01
        return ok, f"local ({local[0]:.3f}, {local[1]:.3f}) / ({hx:.3f}, {hy:.3f})"

    def support_under(self, name, st):
        """The highest annotated surface the object rests on (None = floor/unknown)."""
        b = self.bottom(name, st)
        best = None
        for s in self.ann.supports:
            x0, y0, x1, y1 = s["aabb_xy"]
            if x0 - 0.01 <= b[0] <= x1 + 0.01 and y0 - 0.01 <= b[1] <= y1 + 0.01 and -0.03 <= b[2] - s["z"] <= 0.03:
                if best is None or s["z"] > best["z"]:
                    best = s
        return best

    def room(self, xy):
        return room_of(self.ann.rooms, xy)


class TaskEvaluator(Geometry):
    def __init__(self, task, ann, initial_state=None):
        super().__init__(ann)
        self.task = task
        self.goal = task["goal"]
        self.slots = Slots(task_roles(task), ann.objects.keys())
        self.initial = initial_state

    # ------------------------------------------------------------ evaluation
    def evaluate(self, st):
        bindings, rows = {}, []
        for cond in self.goal["all"]:
            rows.append(self._cond(cond, st, bindings))
        n_ok = sum(r["n_ok"] for r in rows)
        n = sum(r["n"] for r in rows)
        return {"task": self.task["task"], "success": all(r["ok"] for r in rows),
                "progress": round(n_ok / max(n, 1), 3), "bindings": bindings, "conditions": rows}

    def _cond(self, c, st, bindings):
        kind = next(k for k in ("heated", "on", "inside", "upright", "near", "closed", "not_dropped") if k in c)
        fn = getattr(self, "_c_" + kind)
        row = fn(c, st, bindings)
        row["type"] = kind
        row["ok"] = row["n_ok"] == row["n"]
        return row

    def _c_heated(self, c, st, bindings):
        limit = float(c["min_temp_c"])
        temps = st.get("temperatures_c", {})
        items = []
        for label, cands in self.slots.expand(c["heated"], bindings):
            hit = next((name for name in cands if temps.get(name, float("-inf")) >= limit), None)
            detail = f"{hit}: {temps[hit]:.1f} C" if hit else \
                ", ".join(f"{name}: {temps.get(name, float('nan')):.1f} C" for name in cands)
            items.append({"slot": label, "instance": hit, "ok": hit is not None, "detail": detail})
        return {"desc": f"{', '.join(c['heated'])} heated to at least {limit:.0f} C",
                "items": items, "n": len(items), "n_ok": sum(i["ok"] for i in items)}

    def _c_on(self, c, st, bindings):
        items = []
        for label, cands in self.slots.expand(c["on"], bindings):
            hit, why = None, "not in the scene"
            for i in cands:
                ok, why = self.on(i, c["support"], st)
                if ok and c.get("upright"):
                    t = tilt_deg(st["objects"][i]["quat"])
                    ok, why = t <= c.get("max_tilt_deg", UPRIGHT_DEG), f"{why}, tilt {t:.0f} deg"
                if ok:
                    hit = i
                    break
            items.append({"slot": label, "instance": hit, "ok": hit is not None,
                          "detail": why if hit is None else f"{hit}: {why}"})
        sup = c["support"]
        desc = f"{', '.join(c['on'])} on {', '.join(place_name(p) for p in (sup if isinstance(sup, list) else [sup]))}"
        return {"desc": desc + (" (upright)" if c.get("upright") else ""), "items": items,
                "n": len(items), "n_ok": sum(i["ok"] for i in items)}

    def _c_inside(self, c, st, bindings):
        slots = self.slots.expand(c["inside"], bindings)
        conts = self.slots.expand([c["container"]], bindings)[0][1]
        best = None
        for cont in conts:
            items = []
            for label, cands in slots:
                hit, why = None, "not in the scene"
                for i in cands:
                    ok, why = self.inside(i, cont, st)
                    if ok:
                        hit = i
                        break
                items.append({"slot": label, "instance": hit, "ok": hit is not None,
                              "detail": f"in {cont}" if hit else why})
            score = sum(i["ok"] for i in items)
            if best is None or score > best[0]:
                best = (score, cont, items)
        if best is None:
            items = [{"slot": l, "instance": None, "ok": False, "detail": "no container present"} for l, _ in slots]
            best = (0, None, items)
        if c.get("bind") and best[1]:
            bindings[c["bind"]] = best[1]
        return {"desc": f"{', '.join(c['inside'])} inside {c['container']}", "container": best[1],
                "items": best[2], "n": len(best[2]), "n_ok": best[0]}

    def _c_upright(self, c, st, bindings):
        items = []
        lim = c.get("max_tilt_deg", UPRIGHT_DEG)
        for label, cands in self.slots.expand(c["upright"], bindings):
            hit, why = None, "not in the scene"
            for i in cands:
                t = tilt_deg(st["objects"][i]["quat"])
                why = f"{i}: tilt {t:.0f} deg"
                if t <= lim:
                    hit = i
                    break
            items.append({"slot": label, "instance": hit, "ok": hit is not None, "detail": why})
        return {"desc": f"{', '.join(c['upright'])} upright (<= {lim:.0f} deg)", "items": items,
                "n": len(items), "n_ok": sum(i["ok"] for i in items)}

    def _c_near(self, c, st, bindings):
        cand_lists = []
        for label, cands in self.slots.expand(c["near"], bindings):
            if c.get("support") is not None:
                cands = [i for i in cands if self.on(i, c["support"], st)[0]]
            cand_lists.append(cands)
        best = None
        if all(cand_lists):
            for combo in itertools.product(*cand_lists):
                if len(set(combo)) < len(combo):
                    continue
                pts = [self.bottom(i, st)[:2] for i in combo]
                d = max((float(np.linalg.norm(a - b)) for a, b in itertools.combinations(pts, 2)), default=0.0)
                if best is None or d < best[0]:
                    best = (d, combo)
        ok = best is not None and best[0] <= c["max_dist"]
        detail = "a slot has no instance on the support" if best is None else \
            f"{', '.join(best[1])}: max pairwise {best[0]:.2f} m"
        return {"desc": f"{', '.join(c['near'])} within {c['max_dist']} m of each other", "items":
                [{"slot": "setting", "ok": ok, "detail": detail}], "n": 1, "n_ok": int(ok)}

    def _c_closed(self, c, st, bindings):
        arts = self.ann.articulated if c["closed"] == "all" else [self.ann.art(n) for n in c["closed"]]
        items = []
        for a in arts:
            q = st["joints"].get(a["name"], a["closed_q"])
            tol = c.get("tol", 0.10 if a["type"] == "revolute" else 0.04)
            ok = abs(q - a["closed_q"]) <= tol
            items.append({"slot": a["name"], "ok": ok, "detail": f"q {q:.3f}"})
        bad = [i["slot"] for i in items if not i["ok"]]
        # one aggregate item: a benchmark cares whether the house is left closed
        return {"desc": "every door and drawer closed" if c["closed"] == "all" else "listed parts closed",
                "items": [{"slot": "articulated", "ok": not bad,
                           "detail": "all closed" if not bad else f"open: {bad}"}], "n": 1, "n_ok": int(not bad)}

    def _c_not_dropped(self, c, st, bindings):
        init = self.initial or st
        dropped = []
        conts = [n for n in self.ann.objects if self._asset(n).get("container") and n in st["objects"]]
        for n in self.ann.objects:
            if n not in st["objects"] or n not in init["objects"]:
                continue
            if self.bottom(n, init)[2] < 0.10 or self.bottom(n, st)[2] >= 0.05:
                continue
            if any(self.inside(n, k, st)[0] for k in conts if k != n):
                continue
            dropped.append(n)
        return {"desc": "no object dropped on the floor", "items":
                [{"slot": "objects", "ok": not dropped, "detail": "none" if not dropped else f"on the floor: {dropped}"}],
                "n": 1, "n_ok": int(not dropped)}


def room_of(rooms, xy):
    x, y = float(xy[0]), float(xy[1])
    for name, r in rooms.items():
        a = r["aabb_xy"]
        if not (a[0] <= x <= a[2] and a[1] <= y <= a[3]):
            continue
        for t in r["triangles"]:
            (x1, y1), (x2, y2), (x3, y3) = t
            d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(d) < 1e-12:
                continue
            l1 = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d
            l2 = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d
            if l1 >= -1e-6 and l2 >= -1e-6 and 1 - l1 - l2 >= -1e-6:
                return name
    return None


def format_report(rep):
    lines = [f"{rep['task']}: {'SUCCESS' if rep['success'] else 'FAIL'}  progress {rep['progress']:.0%}"]
    for r in rep["conditions"]:
        lines.append(f"  [{'x' if r['ok'] else ' '}] {r['desc']}")
        for i in r["items"]:
            lines.append(f"        {'ok ' if i['ok'] else '-- '}{i['slot']}: {i['detail']}")
    return "\n".join(lines)
