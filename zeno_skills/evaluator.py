"""Scene geometry on a state dict: supports, containment, uprightness, rooms.

state = {"objects": {name: {"pos": [x, y, z], "quat": [w, x, y, z]}},
         "joints":  {articulated_name: q}}

Pure Python (numpy only).  The GT predicates (predicates.py), the skills and the
observation-limited benchmark use these definitions; task goals are scored by
episode.episode.evaluate_goal over the predicates.
"""

from __future__ import annotations

import math

import numpy as np


def quat_R(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def tilt_deg(q):
    R = quat_R(q)
    return math.degrees(math.acos(max(-1.0, min(1.0, R[2, 2]))))


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
        """The highest annotated surface the object rests on (None = floor/unknown).

        Uses the lowest point of the rotated box, so a bottle lying on its side
        still rests on its table."""
        o = st["objects"][name]
        R = quat_R(o["quat"])
        c = self.centre(name, st)
        size = np.asarray(self._asset(name)["size"], float)
        b = np.array([c[0], c[1], c[2] - 0.5 * float(np.abs(R[2, :]) @ size)])
        best = None
        for s in self.ann.supports:
            x0, y0, x1, y1 = s["aabb_xy"]
            if x0 - 0.01 <= b[0] <= x1 + 0.01 and y0 - 0.01 <= b[1] <= y1 + 0.01 and -0.03 <= b[2] - s["z"] <= 0.03:
                if best is None or s["z"] > best["z"]:
                    best = s
        return best

    def room(self, xy):
        return room_of(self.ann.rooms, xy)


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
