"""Scene specs load and every place alias resolves to an annotated surface or
floor area.   python -m pytest tests/"""

import json
from pathlib import Path

import pytest

from zeno_skills.tasks import SPECS, load_places, load_spec, resolve_place

ROOT = Path(__file__).resolve().parents[1]
SPEC_FILES = sorted(p for p in SPECS.rglob("*.json") if p.name != "places.json")


@pytest.mark.parametrize("path", SPEC_FILES, ids=[p.stem for p in SPEC_FILES])
def test_spec(path):
    spec = load_spec(path)
    places = load_places()
    annotation = json.loads((ROOT / spec.get("base_annotation", "annotations/zeno_house.json")).read_text())
    supports = {s["name"] for s in annotation["supports"]} | {s.get("furniture") for s in annotation["supports"]}
    for o in spec.get("objects", {}).values():
        for p in o["supports"]:
            r = resolve_place(p, places)
            assert isinstance(r, dict) or r in supports, f"{p} -> {r}"
