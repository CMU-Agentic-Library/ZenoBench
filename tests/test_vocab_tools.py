"""The benchmark-wide object vocabulary, the constrained tool schemas and the surface names in the prompt (11-26)."""
import json

from baseline.parse import parse_call
from baseline.prompt import render_places, system_prompt
from baseline.tools import call_text, tool_schemas
from benchmark.vocab import kinds_for, registry, vocabulary_text


def test_kind_words_are_loose():
    assert kinds_for("rolling_pin") == ["rolling_pin"]
    assert kinds_for("Rolling Pin") == ["rolling_pin"]
    assert kinds_for("rolling-pins") == ["rolling_pin"]
    assert kinds_for("spoon") == ["breakfast_spoon"]
    assert kinds_for("spoons") == ["breakfast_spoon"]
    assert set(kinds_for("bin")) == {"small_storage_bin", "wide_storage_bin"}      # the kinds named *_bin
    assert "toy_box" in kinds_for("bins", ["toy_box", "breakfast_mug"])            # subcategory when no kind is
    assert set(kinds_for("tomatoes")) == {"cherry_tomato", "big_tomato"}
    assert kinds_for("tableware")                                                  # a category
    assert kinds_for("spaceship") == []


def test_vocabulary_is_the_whole_registry():
    text = vocabulary_text()
    assert all(k in text for k in registry())


def test_system_prompt_has_vocabulary_not_scene():
    sp = system_prompt([], 60)
    assert "rolling_pin" in sp and "Object kinds" in sp


PLACES = {"living_room_0_0": {"kind": "room"},
          "kitchen_island": {"kind": "furniture", "category": "KitchenIsland", "room": "living_room_0_0"},
          "kitchen_island/top": {"kind": "support", "furniture": "kitchen_island", "z": 0.86,
                                 "room": "living_room_0_0"},
          "tv_stand_2": {"kind": "furniture", "room": "living_room_0_0"},
          "tv_stand_2/top": {"kind": "support", "furniture": "tv_stand_2", "z": 0.48, "room": "living_room_0_0"},
          "tv_stand_2/shelf_0": {"kind": "support", "furniture": "tv_stand_2", "z": 0.1, "room": "living_room_0_0"}}


def test_places_list_surfaces_under_furniture():
    text = render_places(PLACES)
    assert "kitchen_island [furniture, KitchenIsland] surfaces: kitchen_island/top (z=0.86)" in text
    assert "tv_stand_2/shelf_0" in text and "tv_stand_2/top" in text


def test_tool_enums_from_observation_only():
    skills = [{"name": "place", "parameters": {"object": {"type": "object_ref", "required": True},
                                               "receptacle": {"type": "receptacle_ref", "required": True}}},
              {"name": "search", "parameters": {"object": {"type": "object_ref", "required": True},
                                                "region": {"type": "room_ref"}}}]
    obs = {"known_places": PLACES, "visible_objects": [{"name": "wide_storage_bin_1"}],
           "robot": {"held_right": "rolling_pin_1"}}
    tools = {t["function"]["name"]: t["function"] for t in tool_schemas(skills, obs)}
    rec = tools["place"]["parameters"]["properties"]["receptacle"]
    assert rec["enum"] == ["kitchen_island/top", "tv_stand_2/shelf_0", "tv_stand_2/top", "rolling_pin_1",
                           "wide_storage_bin_1"]
    assert "enum" not in tools["search"]["parameters"]["properties"]["object"]     # kind words stay free
    assert tools["search"]["parameters"]["properties"]["region"]["enum"] == ["living_room_0_0"]
    assert tools["place"]["parameters"]["required"] == ["object", "receptacle"]
    assert "finish" in tools


def test_tool_call_reads_as_the_text_answer():
    assert parse_call(call_text("place", {"object": "a_1", "receptacle": "kitchen_island/top"})) == \
        {"skill": "place", "args": {"object": "a_1", "receptacle": "kitchen_island/top"}}
    assert parse_call("Thought: done\n" + call_text("finish", {"reason": "ok"})) is None
    assert json.loads(call_text("finish", {}))["finish"] is True
