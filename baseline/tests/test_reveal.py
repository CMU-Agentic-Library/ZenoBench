"""SHIFT_REVEAL (baseline/reveal.py): off by default and then the prompts are unchanged; on, only kind-level
facts of observed kinds (and, in full, surface uses) - never unobserved objects, instance state or task roles."""
from __future__ import annotations

import pytest

from baseline import prompt, reveal

OBS = {
    "robot": {"room": "kitchen_0_1"},
    "visible_objects": [{"name": "breakfast_plate_1", "category": "breakfast_plate", "last_seen_on": "kitchen_counter_2/top"}],
    "observation_cache": [{"name": "handled_cooking_pot_1", "category": "handled_cooking_pot",
                           "last_seen_on": "kitchen_stove/top"}],
    "known_places": {"kitchen_0_1": {"kind": "room"},
                     "dining_table_1/top": {"kind": "support", "category": "TableDining", "z": 0.71,
                                            "room": "dining_room_0_0"}},
}


@pytest.fixture
def mode(monkeypatch):
    def set_(m):
        if m is None:
            monkeypatch.delenv("SHIFT_REVEAL", raising=False)
        else:
            monkeypatch.setenv("SHIFT_REVEAL", m)
    return set_


def test_default_off_changes_nothing(mode):
    mode(None)
    assert reveal.mode() == "off"
    text = prompt.render_observation(OBS)
    assert "Object facts" not in text and "dining table" not in text
    assert "registry" not in prompt.system_prompt([], 60)
    mode("off")
    assert prompt.render_observation(OBS) == text


def test_objects_reveals_observed_kinds_only(mode):
    mode("objects")
    text = prompt.render_observation(OBS)
    assert "Object facts (per kind observed):" in text
    assert "- breakfast_plate (tableware/dish):" in text and "- handled_cooking_pot (cookware/pot):" in text
    assert "opening 23x23 cm" in text                       # container geometry from the spawn source
    assert "breakfast_bowl" not in text                     # a kind not observed is not revealed
    assert "dining table" not in text                       # surfaces only in full
    assert "registry" in prompt.system_prompt([], 60)


def test_full_adds_surface_uses(mode):
    mode("full")
    text = prompt.render_observation(OBS)
    assert "dining_table_1/top [support, TableDining, z=0.71, things rest on it, dining table" in text


def test_never_reveals_roles_or_judgements(mode):
    mode("full")
    text = prompt.render_observation(OBS) + prompt.system_prompt([], 60)
    for word in ("ideal", "substitute", "stand-in", "legal", "in use", "required", "role"):
        assert word not in text.lower(), word


def test_bad_mode_refused(mode):
    mode("everything")
    with pytest.raises(ValueError):
        reveal.mode()


def test_every_registry_kind_renders():
    from benchmark.v6 import object_registry as R
    for k in R.objects_yaml()["objects"]:
        assert reveal.kind_line(k).startswith(f"- {k} (")


def test_card_up_to_date():
    """baseline/reveal_card.json (vendored by Graph Manager) matches the registry."""
    assert reveal.main(["--check"]) == 0
    c = reveal.card()
    assert c["objects"]["breakfast_plate"] == reveal.kind_line("breakfast_plate")
    assert c["surfaces"]["dining_table_1/top"].startswith("things rest on it, dining table")
