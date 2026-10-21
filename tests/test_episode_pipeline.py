"""The shared episode pipeline without Isaac Sim: profiles, catalogs, hashes, the call path."""
from types import SimpleNamespace

import pytest

from benchmark.scene import episode_config
from episode.catalog import DEFAULT_CATALOGS, base_sha1, episode_hash, load_catalog, public_task
from episode.episode import Episode, flat_goal
from episode.profile import (ProfileError, load_profile, max_calls, needs_observer, observation_fields,
                             run_profile_current)


def write(tmp_path, text, name="p.yaml"):
    f = tmp_path / name
    f.write_text(text)
    return f


def test_shipped_profiles_load():
    gt, oracle, bench = (load_profile(n) for n in ("gt", "oracle", "benchmark"))
    assert not needs_observer(gt) and not needs_observer(oracle) and needs_observer(bench)
    assert observation_fields(gt) == ["images", "objects", "robot", "task_status"]
    assert observation_fields(bench) == ["images", "visible_objects", "observation_cache", "known_places", "robot",
                                         "last_result"]
    assert bench["execution"]["gate"] and not bench["execution"]["auto_recovery"]
    assert oracle["execution"]["nested_repair"] and not gt["execution"]["nested_repair"]
    assert len({gt["hash"], oracle["hash"], bench["hash"]}) == 3


def test_unknown_keys_and_bad_values_are_refused(tmp_path):
    for text in ("execution: {gaet: true}", "observation: {cameras: [nose]}", "limits: {max_calls: 0}",
                 "observation: {robot: {temperatures: hot}}", "execution: {gate: yes please}"):
        with pytest.raises(ProfileError):
            load_profile(write(tmp_path, text))
    assert load_profile(write(tmp_path, "observation: {robot: {temperatures: off}}"))["observation"]["robot"][
        "temperatures"] == "none"


def test_gate_with_gt_state_is_a_leak(tmp_path):
    with pytest.raises(ProfileError, match="gt_objects"):
        load_profile(write(tmp_path, "execution: {gate: true, mask_feedback: true}\nobservation: {task_status: false}"))
    with pytest.raises(ProfileError, match="mask_feedback"):
        load_profile(write(tmp_path, "execution: {gate: true}\nobservation: {gt_objects: false, task_status: false}"))
    ok = load_profile(write(tmp_path, "execution: {gate: true}\nallow_leak: true"))
    assert ok["execution"]["gate"] and ok["observation"]["gt_objects"]


def test_profile_hash_ignores_the_name_only(tmp_path):
    a = load_profile(write(tmp_path, "name: a\nlimits: {max_calls: 9}", "a.yaml"))
    b = load_profile(write(tmp_path, "name: b\nlimits: {max_calls: 9}", "b.yaml"))
    c = load_profile(write(tmp_path, "limits: {max_calls: 10}", "c.yaml"))
    assert a["hash"] == b["hash"] != c["hash"] and a["name"] == "a"
    assert max_calls(a, {}) == 9 and max_calls(load_profile("benchmark"), {"max_calls": 25}) == 25
    assert max_calls(load_profile("benchmark"), {}) == 60


def test_run_profile_current():
    bench = load_profile("benchmark")
    assert run_profile_current({})                                       # before profiles
    assert run_profile_current({"profile": "benchmark", "profile_hash": bench["hash"]})
    assert not run_profile_current({"profile": "benchmark", "profile_hash": "0" * 12})
    assert not run_profile_current({"profile": "no_such_profile", "profile_hash": "x"})


def test_both_catalogs_in_one_shape():
    legacy = load_catalog("skill_library/tasks.json")
    bench = load_catalog("benchmark/v3/tasks.json")
    assert set(DEFAULT_CATALOGS) == {"skill_library/tasks.json", "benchmark/v3/tasks.json"}
    for t in list(legacy.values()) + list(bench.values()):
        assert {"task_id", "instruction", "scene", "variants", "goal", "routes", "oracle"} <= set(t)
        assert set(t["goal"]) <= {"all", "any"}
    cf = legacy["collect_fruits"]
    assert list(cf["variants"]) == ["default"] and cf["scene"] == {"base": "tasks/collect_fruits"}
    assert cf["oracle"] == {"default": "nominal"} and cf["routes"]["nominal"]["steps"][0]["skill"] == "navigate"
    assert public_task(cf) == {"task_id": "collect_fruits", "name": "collect_fruits",
                               "description": "Collect both fruits into the basket on the bookcase."}


def test_one_variant_task_ignores_the_seed():
    t = load_catalog("skill_library/tasks.json")["count_tomatoes"]
    cfgs = [episode_config(t, s) for s in (0, 3, 17)]
    assert len({c["config_hash"] for c in cfgs}) == 1 and cfgs[0]["variant"] == "default"
    assert cfgs[0]["remove"] == [] and cfgs[0]["move"] == {} and cfgs[0]["start"] is None


def test_episode_hash_separates_profiles_and_scenes():
    t = load_catalog("benchmark/v3/tasks.json")["T01_book_to_dining_table"]
    cfg = episode_config(t, 10, "no_overhang")
    b = base_sha1(cfg["base"])
    gt, bench = load_profile("gt"), load_profile("benchmark")
    assert episode_hash(cfg["config_hash"], gt["hash"], b) != episode_hash(cfg["config_hash"], bench["hash"], b)
    assert episode_hash(cfg["config_hash"], gt["hash"], b) != episode_hash(cfg["config_hash"], gt["hash"], "x")
    assert base_sha1("tasks/collect_fruits") != base_sha1("tasks/kitchen_skills")


def test_flat_goal():
    goal = {"all": [{"atom": "a(x)", "holds": True, "detail": ""}],
            "any": [[{"atom": "b(x)", "holds": False, "detail": "d"}], [{"atom": "c(x)", "holds": True, "detail": ""}]]}
    assert flat_goal(goal) == [{"atom": "a(x)", "holds": True}, {"atom": "b(x)", "holds": False},
                               {"atom": "c(x)", "holds": True}]


def test_masked_result_for_the_planner_unmasked_record_for_the_log():
    ep = object.__new__(Episode)
    ep.profile = load_profile("benchmark")
    ep.runner = SimpleNamespace(contract=lambda key: {"inputs": {}}, run=lambda verb, args: SimpleNamespace(
        success=False, error_code="PRECONDITION_FAILED", error="reachable(target=hidden_bowl) is false",
        preconditions=[{"atom": "reachable(target=hidden_bowl)", "holds": False}], postconditions=[], outputs={},
        children=[], action="pick_object(object=mug)", selected_path=None))
    ep.observer = SimpleNamespace(mask=lambda value, allow: __import__("json").loads(
        __import__("json").dumps(value).replace("hidden_bowl", "<unobserved>")))
    public, record = ep.call({"contract": "pick", "args": {"object": "mug"}})
    assert "hidden_bowl" not in str(public) and "<unobserved>" in public["error"]
    assert "hidden_bowl" in record["error"] and record["action"] == "pick_object(object=mug)"
    assert ep.last_result == public
