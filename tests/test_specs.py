"""Task specs load, every place alias resolves to an annotated surface or floor
area, and goals only use known conditions and roles.   python -m pytest tests/"""

import json
from pathlib import Path

import pytest

from zeno_skills.tasks import SPECS, load_places, load_spec, resolve_goal, resolve_place

ROOT = Path(__file__).resolve().parents[1]
ANN = json.loads((ROOT / "annotations/zeno_house.json").read_text())
SUPPORTS = {s["name"] for s in ANN["supports"]} | {s.get("furniture") for s in ANN["supports"]}
CONDITIONS = ("on", "inside", "upright", "near", "closed", "not_dropped")   # evaluator's priority order
SPEC_FILES = sorted(p for p in SPECS.rglob("*.json") if p.name != "places.json")


def _places_of(goal):
    if isinstance(goal, dict):
        for k, v in goal.items():
            if k == "support":
                yield from (v if isinstance(v, list) else [v])
            else:
                yield from _places_of(v)
    elif isinstance(goal, list):
        for g in goal:
            yield from _places_of(g)


@pytest.mark.parametrize("path", SPEC_FILES, ids=[p.stem for p in SPEC_FILES])
def test_spec(path):
    spec = load_spec(path)
    places = load_places()
    for o in spec.get("objects", {}).values():
        for p in o["supports"]:
            r = resolve_place(p, places)
            assert isinstance(r, dict) or r in SUPPORTS, f"{p} -> {r}"
    goal = resolve_goal(spec["goal"], places)
    for p in _places_of(goal):
        assert isinstance(p, dict) or p in SUPPORTS, p
    roles = set(spec.get("roles", {})) | set(spec.get("existing", {}))
    names = set(spec.get("objects", {})) | {i for v in spec.get("existing", {}).values() for i in v}
    for c in goal["all"]:
        kind = next((k for k in CONDITIONS if k in c), None)    # "upright": true may ride on "on"
        assert kind, c
        slots = c[kind] if isinstance(c[kind], list) else []
        if "container" in c:
            slots = slots + [c["container"]]
        for s in slots:
            if s.startswith("$"):
                continue
            for alt in s.removeprefix("all:").split("|"):
                assert alt in roles or alt in names, f"unknown slot {alt}"
