"""Task specs: loading, place aliases and object slots.

A task is one JSON file in ``task_specs/`` (see task_specs/README in the
repository README, section "Define your own task").  ``tools/build_tasks.py``
samples a variant of it into ``tasks/<task>/task.json``; the evaluator
(evaluator.py) and the scripted policy (task_policy.py) read that file.

Vocabulary
----------
place   an alias from task_specs/places.json, a support name from the scene
        annotation (``supports[].name``), a furniture name (= any of its
        support surfaces), ``floor`` or ``floor:<alias>``.
role    a named group of object instances (``roles`` + ``existing``).
slot    one required object in a goal condition:
          "apple"                 that instance (or role: any instance of it)
          "plate|bowl"            the first alternative that is present
          "all:fruit"             one slot per instance of the role
          "$container"            the instance bound by an earlier condition
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "task_specs"


def load_places(path=SPECS / "places.json"):
    d = json.loads(Path(path).read_text())
    return {k: v for k, v in d.items() if not k.startswith("_")}


def load_spec(name_or_path):
    p = Path(name_or_path)
    if not p.suffix:
        p = SPECS / f"{name_or_path}.json"
    spec = json.loads(p.read_text())
    spec.setdefault("task", p.stem)
    return spec


def resolve_place(place, places):
    """Alias -> raw place: a support/furniture name (str) or a floor area
    ({"floor": room, "xy": [x0, y0, x1, y1]})."""
    if isinstance(place, (list, tuple)):
        return [resolve_place(p, places) for p in place]
    if isinstance(place, dict):
        return place
    v = places.get(place, place)
    if isinstance(v, dict):
        return {"floor": v["room"], "xy": v["xy"], "alias": place}
    return v


def place_name(place):
    """Printable name of a raw place (floor areas keep their alias)."""
    if isinstance(place, str):
        return place
    alias = place.get("alias", place["floor"])
    return alias if alias.startswith("floor") else "floor:" + alias


def resolve_goal(goal, places):
    """Replace place aliases inside the goal tree by raw places."""
    if isinstance(goal, dict):
        out = {}
        for k, v in goal.items():
            out[k] = resolve_place(v, places) if k == "support" else resolve_goal(v, places)
        return out
    if isinstance(goal, list):
        return [resolve_goal(g, places) for g in goal]
    return goal


class Slots:
    """Expands slot strings against the roles and the instances present."""

    def __init__(self, roles, present):
        self.roles = roles
        self.present = set(present)

    def instances(self, alt):
        """Instances (present in the scene) an alternative token stands for."""
        if alt in self.roles:
            return [i for i in self.roles[alt] if i in self.present]
        return [alt] if alt in self.present else []

    def expand(self, slots, bindings=None):
        """-> list of (slot_label, [candidate instances in preference order])."""
        bindings = bindings or {}
        out = []
        for s in slots:
            if s.startswith("all:"):
                for i in self.roles.get(s[4:], []):
                    out.append((i, [i] if i in self.present else []))
            elif s.startswith("$"):
                b = bindings.get(s[1:])
                out.append((s, [b] if b else []))
            else:
                cands = []
                for alt in s.split("|"):
                    cands += [i for i in self.instances(alt) if i not in cands]
                out.append((s, cands))
        return out


def task_roles(task):
    roles = {k: list(v) for k, v in task.get("existing_objects", {}).items()}
    for k, v in task.get("roles", {}).items():
        roles[k] = list(v)
    return roles
