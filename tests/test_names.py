"""Anonymous object names (episode/names.py, profile observation.anonymize_names)."""
from types import SimpleNamespace

import pytest

from episode.episode import Episode
from episode.names import NameMap
from episode.profile import load_profile

OBJECTS = {"spare_mug": "mug", "mug_shelf": "mug", "his_cup": "plastic_cup", "west_tray": "serving_tray",
           "cup_1": "cup", "stock_cup_1": "cup"}


def test_aliases_are_category_numbers_that_hide_the_instance_name():
    nm = NameMap(OBJECTS, "abc", reserved={"kitchen_counter_1/top"})
    assert sorted(nm.alias[n] for n in ("spare_mug", "mug_shelf")) == ["mug_1", "mug_2"]
    assert nm.alias["his_cup"] == "plastic_cup_1" and nm.alias["west_tray"] == "serving_tray_1"
    assert nm.alias["stock_cup_1"] != "cup_1" or nm.alias["cup_1"] == "cup_1"      # no alias takes another's name
    assert len(set(nm.alias.values())) == len(OBJECTS)
    # the numbering follows the episode hash, not the instance name
    assert {NameMap(OBJECTS, s).alias["spare_mug"] for s in map(str, range(20))} == {"mug_1", "mug_2"}


def test_a_category_spelled_like_an_instance_stays_a_category():
    nm = NameMap({"handled_cooking_pot": "handled_cooking_pot"}, "abc")
    assert nm.public({"name": "handled_cooking_pot", "category": "handled_cooking_pot"}) == \
        {"name": "handled_cooking_pot_1", "category": "handled_cooking_pot"}


def test_public_and_private_round_trip():
    nm = NameMap(OBJECTS, "abc")
    pub = nm.public({"error": "reachable(target=spare_mug) is false", "spare_mug": ["west_tray/inside", 3]})
    assert "spare_mug" not in str(pub) and "west_tray" not in str(pub)
    tray = nm.alias["west_tray"]
    assert pub["error"] == f"reachable(target={nm.alias['spare_mug']}) is false"
    assert pub[nm.alias["spare_mug"]] == [f"{tray}/inside", 3]
    assert nm.private({"object": nm.alias["his_cup"], "target": f"{tray}/inside", "objects": [nm.alias["spare_mug"]],
                       "place": "kitchen_counter_1/top"}) == \
        {"object": "his_cup", "target": "west_tray/inside", "objects": ["spare_mug"], "place": "kitchen_counter_1/top"}
    with pytest.raises(KeyError):                     # a guessed instance name is not a name the planner has
        nm.private({"object": "spare_mug"})


def test_benchmark_profiles_anonymize_and_a_gated_profile_must():
    for name in ("benchmark", "sticky/benchmark", "sticky_snap/benchmark"):
        assert load_profile(name)["observation"]["anonymize_names"]
    assert not load_profile("gt")["observation"]["anonymize_names"]


def _episode(run):
    ep = object.__new__(Episode)
    ep.profile = load_profile("benchmark")
    ep.names = NameMap(OBJECTS, "abc")
    ep.runner = SimpleNamespace(contract=lambda key: {"inputs": {}}, run=run)
    ep.observer = SimpleNamespace(view=set(), mask=lambda value, allow: value)
    return ep


def test_a_planner_call_is_mapped_back_and_its_result_anonymized():
    seen = {}

    def run(verb, args):
        seen.update(args)
        return SimpleNamespace(success=False, error_code="PRECONDITION_FAILED",
                               error="clear(west_tray) is false: spare_mug is on it", preconditions=[],
                               postconditions=[], outputs={}, children=[], action=f"pick(object={args['object']})",
                               selected_path=None)
    ep = _episode(run)
    alias = ep.names.alias
    public, record = ep.call({"contract": "pick", "args": {"object": alias["his_cup"]}})
    assert seen == {"object": "his_cup"}                               # executed on the real object
    assert public["args"] == {"object": alias["his_cup"]}
    assert "spare_mug" not in str(public) and "west_tray" not in str(public) and "his_cup" not in str(public)
    assert record["args"] == {"object": "his_cup"} and record["planner_args"] == {"object": alias["his_cup"]}
    assert ep.last_result == public


def test_a_guessed_instance_name_is_refused_and_a_route_call_runs_as_written():
    ran = []

    def run(verb, args):
        ran.append(args)
        return SimpleNamespace(success=True, error_code=None, error=None, preconditions=[], postconditions=[],
                               outputs={}, children=[], action="pick", selected_path=None)
    ep = _episode(run)
    public, _ = ep.call({"contract": "pick", "args": {"object": "spare_mug"}})
    assert public["error_code"] == "INPUT_UNKNOWN" and public["args"] == {"object": "<unknown>"} and not ran
    assert not set(ep.names.real) & set(str(public).replace("'", " ").split())     # no alias revealed
    ep.call({"contract": "pick", "args": {"object": "spare_mug"}}, internal=True)      # the harness's own route
    assert ran == [{"object": "spare_mug"}]
