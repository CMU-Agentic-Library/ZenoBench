import json
from unittest.mock import patch

from baseline import run_http
from baseline.comparison import MAIN, episodes, graph_library, representatives
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


def test_execution_failure_and_task_score_use_native_verdict(tmp_path):
    job = {"task": "test", "variant": "v", "seed": 10}
    planner = tmp_path / "planner"
    native = tmp_path / "native" / "test" / "exp"
    for p in (planner, native):
        p.mkdir(parents=True)
    meta = {"profile": MAIN, "task_id": "test", "variant": "v", "seed": 10, "exp_id": "exp"}
    score = {"score": 0.6}
    run_http.write_report(planner / "result.json", {**meta, "model": "local", "policy": "baseline.react:ReAct",
                          "max_calls": 60, "episode": {"episode_hash": "id", "config_hash": "layout"},
                          "success": False, "score": score, "wall_s": 5, "planner_summary": {"vlm_queries": 2}})
    run_http.write_report(native / "result.json", {**meta, "episode_hash": "id", "incomplete": False,
                          "task_success": False, "score": score, "skill_calls": 1,
                          "calls": [{"eval": {"leaf_code": "POLICY_FAILED"}}]})
    status, r = read_outcome(planner, tmp_path / "native", "local", "ReAct", job)
    assert status == "scored"
    assert r["score"] == 0.6 and not r["success"] and r["execution"]
