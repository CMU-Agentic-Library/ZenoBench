"""The object and furniture registry (11-24; for classification since 11-25): complete and closed vocabulary."""
from __future__ import annotations

import json

from benchmark.v6 import loosen_1124 as L
from benchmark.v6 import object_registry as R


def _goal_names(g, out):
    if isinstance(g, dict):
        for v in g.values():
            _goal_names(v, out)
    elif isinstance(g, list):
        for x in g:
            _goal_names(x, out)
    elif isinstance(g, str) and "/" in g:
        out.add(g)


def test_vocabulary_closed():
    assert R.check_vocab() == []


def test_every_v6_asset_kind_registered():
    kinds = set()
    for t in R.tasks_json()["tasks"]:
        for lid, v in t["variants"].items():
            kinds |= {o["kind"] for o in R.layout_objects(t, v).values()}
    assert kinds - set(R.objects_yaml()["objects"]) == set()
    assert set(R.objects_yaml()["objects"]) <= set(R.assets_json())


def test_every_goal_surface_registered():
    named = set()
    for t in R.tasks_json()["tasks"]:
        _goal_names(t.get("goal"), named)
        for v in t["variants"].values():
            _goal_names(v.get("goal"), named)
            for tr in (v.get("scoring") or {}).get("tiers", []):
                _goal_names(tr.get("goal"), named)
    surfaces = {n for n in named if n.split("/", 1)[1].split("/")[0] in
                ("top", "inside_shelf", "inside_bottom", "inside_floor") or "/shelf_" in n}
    assert surfaces - set(R.surfaces()) == set()


def test_every_surface_has_a_room_but_the_microwave():
    assert {n for n, s in R.surfaces().items() if s["room"] is None} <= {
        "kitchen_microwave/inside_floor", "kitchen_microwave/top"}


def test_categories():
    assert R.obj("breakfast_bowl")["taxonomy"] == {"category": "tableware", "subcategory": "dish"}
    assert R.surface("kitchen_microwave/top")["taxonomy"]["category"] == "appliance"


def test_loosen_keys_name_real_designs():
    """PLACES / ATOM_ALTERNATIVES keys name a design (or "*"), never a layout id that no design is called; every
    atom an alternative replaces occurs in that design before loosening (an entry that matches nothing is dead)."""
    from benchmark.v6.tests.conftest import pre_loosen
    pre = {t["task_id"][:3]: t for t in pre_loosen()["tasks"]}
    for table in (L.PLACES, L.ATOM_ALTERNATIVES):
        for prefix, design in table:
            assert design == "*" or design in pre[prefix]["v6_variants"], (prefix, design)
    for (prefix, design), pairs in L.ATOM_ALTERNATIVES.items():
        t = pre[prefix]
        text = json.dumps([t["variants"][lid] for lid in t["v6_variants"][design]["layouts"]])
        for atom, _ in pairs:
            assert json.dumps(atom) in text, (prefix, design, atom)
