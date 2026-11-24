import json
import subprocess
import sys
from unittest.mock import patch
import pytest

from baseline import run_http
from baseline.comparison import MAIN, episodes, graph_library, representatives
from baseline.graph_profile import configure
from baseline.launch_comparison import claim_episode
from baseline.report import read_outcome


def test_paired_catalog_and_local_graph_library(tmp_path):
    jobs = episodes()
    assert len(jobs) == len({(j["task"], j["variant"], j["seed"]) for j in jobs}) == 1510
    subset = representatives(jobs)
    assert len(subset) == len({(j["task"], j["variant"]) for j in jobs}) == 316
    graph_library(tmp_path)
    index = json.loads((tmp_path / "tasks.json").read_text())["tasks"]
    assert len(index) == 30
    assert set(index[0]) == {"task_id", "variants", "catalog", "default_profile"}
    assert set(index[0]["variants"]) >= {j["variant"] for j in jobs if j["task"] == index[0]["task_id"]}
    assert len(list((tmp_path / "skills").glob("*/skill.json"))) == 71


def test_dispatchers_share_episode_ownership_while_a_child_is_alive(tmp_path):
    directory = tmp_path / "episode"
    with claim_episode(directory) as first:
        assert first is not None
        child = subprocess.Popen([sys.executable, "-c", "import sys; sys.stdin.read()"],
                                 stdin=subprocess.PIPE, pass_fds=(first.fileno(),))
    try:
        with claim_episode(directory) as duplicate:
            assert duplicate is None
    finally:
        child.communicate()
    with claim_episode(directory) as retry:
        assert retry is not None
        (directory / "result.json").write_text("{}")
    with claim_episode(directory) as completed:
        assert completed is None


def test_harness_compacts_against_the_served_context_window(tmp_path):
    import yaml
    patch_file = tmp_path / "provider.yml"
    template = run_http.ROOT / "baseline/graph_manager/examples/harness-local-vlm.patch.yml"
    patch_file.write_text(template.read_text())
    configure(patch_file, tmp_path)
    config = yaml.safe_load(patch_file.read_text())[0]["config"]["providers"]["lab-vlm"]
    model, = config["models"]
    assert (model["contextWindow"], model["maxTokens"], model["input"]) == (32768, 4096, ["text", "image"])
    assert json.loads((tmp_path / "local-provider.json").read_text())["model"] == "qwen3.5-4b"


def test_checked_after_model_crash_remains_retryable(tmp_path):
    job = {"task": "test", "variant": "v", "seed": 10}
    policy = "baseline.react:ReAct"

    def post(server, path, body):
        if path == "/initial_task":
            return {"exp_id": "exp", "task": {"description": "bring a cup"}, "observation": {},
                    "profile": {"name": MAIN, "max_calls": 60}}
        assert path == "/check_task"
        return {"success": False, "score": {"score": 0}, "goal": []}

    with patch.object(run_http, "post", post), patch("benchmark.planners.load_policy", side_effect=ConnectionError):
        r = run_http.run_one("", job, policy, MAIN, tmp_path, "local", [])
    directory = run_http.run_dir(tmp_path, policy, "local", job)
    assert r["score"]["score"] == 0 and (directory / "failed.json").is_file()
    assert not (directory / "result.json").exists()
    assert read_outcome(directory, tmp_path, "local", "ReAct", job) == ("interrupted", None)
    assert run_http.prepare_attempt(directory, MAIN) is None
    assert len(list(directory.glob("attempts/*/failed.json"))) == 1


@pytest.mark.parametrize(("tier", "value", "success", "best_success"),
                         [("second", 0.6, False, False), ("best", 1.0, False, False),
                          ("second", 0.6, True, False), ("best", 1.0, True, True)])
def test_execution_failure_and_task_score_use_native_verdict(tmp_path, tier, value, success, best_success):
    job = {"task": "test", "variant": "v", "seed": 10}
    planner = tmp_path / "planner"
    native = tmp_path / "native" / "test" / "exp"
    for p in (planner, native):
        p.mkdir(parents=True)
    meta = {"profile": MAIN, "task_id": "test", "variant": "v", "seed": 10, "exp_id": "exp"}
    runtime = {"isaacsim": "6.0.0.1", "lab_compat_sha256": "abc"}
    score = {"score": value, "tier": tier}
    run_http.write_report(planner / "result.json", {**meta, "model": "local", "policy": "baseline.react:ReAct",
                          "max_calls": 60, "episode": {"episode_hash": "id", "config_hash": "layout", "runtime": runtime},
                          "success": success, "score": score, "wall_s": 5,
                          "stop_reason": "service_limit" if tier == "second" else "planner_done",
                          "planner_summary": {"vlm_queries": 2, "stop_reason": "finish: the model says it is done"}})
    run_http.write_report(native / "result.json", {**meta, "episode_hash": "id", "incomplete": False,
                          "task_success": success, "score": score, "skill_calls": 3, "runtime": runtime,
                          "calls": [{"eval": {"leaf_code": "POLICY_FAILED"}},
                                    {"eval": {"leaf_code": "NOT_OBSERVED"}},
                                    {"feedback": {"success": True}, "eval": {"leaf_code": None}}]})
    status, r = read_outcome(planner, tmp_path / "native", "local", "ReAct", job, "6.0.0.1")
    assert status == "scored"
    assert r["score"] == value and r["success"] == success and r["execution"]
    assert r["best_success"] == best_success
    assert r["failure_classes"] == {"execution", "observation"}
    assert r["stop_reason"] == ("service_limit" if tier == "second" else "finish")
    with pytest.raises(ValueError, match="simulator version mismatch"):
        read_outcome(planner, tmp_path / "native", "local", "ReAct", job, "5.1.0.0")
