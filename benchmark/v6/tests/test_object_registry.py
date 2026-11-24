"""The object and furniture registry (11-24): complete, closed vocabulary, roles that match tasks.json, and the
hand-written loosening tables all legal by it."""
from __future__ import annotations

import json

import pytest

from benchmark.v6 import affordance_check as A
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
    assert all(R.surface(s)["affordances"] for s in surfaces)


def test_every_surface_has_a_room_but_the_microwave():
    assert {n for n, s in R.surfaces().items() if s["geometry"]["room"] is None} <= {
        "kitchen_microwave/inside_floor", "kitchen_microwave/top"}


def test_geometry_from_spawn_source():
    assert R.covers("pot_lid", "handled_cooking_pot") and R.covers("breakfast_plate", "handled_cooking_pot")
    assert not R.covers("book_blue", "handled_cooking_pot")          # 14 cm across a 23 cm opening
    assert R.fits("breakfast_bowl", "apple") and R.fits("trash_can", "soda_can")
    assert not R.fits("breakfast_mug", "teddy_bear")
    assert R.appliance_ok("kitchen_stove", "soup_pot") and not R.appliance_ok("kitchen_microwave", "soup_pot")
    assert R.appliance_ok("kitchen_microwave", "oatmeal_bowl") and not R.appliance_ok("kitchen_stove", "oatmeal_bowl")


@pytest.mark.parametrize("role", R.roles(), ids=lambda r: r["id"])
def test_role_designs_exist_and_capture(role):
    tasks = {t["task_id"][:3]: t for t in R.tasks_json()["tasks"]}
    for prefix, designs in role["tasks"].items():
        assert prefix in tasks, prefix
        have = set(tasks[prefix].get("v6_variants", {}))
        assert "*" in designs or set(designs) <= have, (role["id"], set(designs) - have)
    data = A.run()
    rec = next(r for r in data["roles"] if r["id"] == role["id"])
    assert rec["layouts"], f"{role['id']} captures nothing"


@pytest.mark.parametrize("role", [r for r in R.roles() if r["kind"] == "object"], ids=lambda r: r["id"])
def test_ideal_kind_legal(role):
    for k in role["ideal"]:
        assert not R._legal(role, R.obj(k)), (role["id"], k)


@pytest.mark.parametrize("role", [r for r in R.roles() if r["kind"] == "place"], ids=lambda r: r["id"])
def test_ideal_surface_legal(role):
    for s in role["ideal"]:
        assert R.assess_place(role, s)[0] == R.IDEAL_LEVEL, (role["id"], s)


def test_loosen_tables_legal_by_registry():
    """Every stand-in kind, place and storage alternative loosen_1124 adds by hand is legal by the registry."""
    rows = A.run()["loosen_tables"]
    n = sum(len(k) for t in L.SUBSTITUTE_KINDS.values() for k in t.values())
    assert sum(r["table"] == "SUBSTITUTE_KINDS" for r in rows) == n
    assert [r for r in rows if r["ok"] is not True] == []


def test_report_up_to_date():
    assert A.main(["--check"]) == 0


def test_agent_card_lists_every_kind():
    card = R.agent_card()
    assert all(f"- {k} (" in card for k in R.objects_yaml()["objects"])
    json.dumps(R.obj("breakfast_bowl"))                             # serialisable facts


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
