"""Scene specs: loading and place aliases.

A scene spec is one JSON file in ``task_specs/`` (or ``scene_specs/``).
``tools/build_tasks.py`` samples a layout of it into ``tasks/<name>/`` (scene.usd,
annotation.json, task.json).  task.json describes the scene only (USD, annotation,
robot start, thermal state, placed objects); the tasks that run on a scene and their
goals live in the task catalogs (skill_library/tasks.json, benchmark/*/tasks.json).

Vocabulary
----------
place   an alias from task_specs/places.json, a support name from the scene
        annotation (``supports[].name``), a furniture name (= any of its
        support surfaces), ``floor`` or ``floor:<alias>``.
role    a named group of object instances (``roles`` + ``existing``).
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
