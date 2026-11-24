import fcntl
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import urllib.request
from unittest.mock import patch
import pytest

from baseline import run_http
from baseline.comparison import MAIN, MODELS, episodes, graph_library, representatives, result_is_current, result_path, run_graph
from baseline.graph_profile import isolated_workspace
from baseline.harness_usage import recorded_usage
from baseline.launch_comparison import claim_episode, pending
from baseline.report import graph_attempt_table, read_outcome, reference_table
from baseline.sim6.startup_queue import install


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


def test_resume_interrupted_ablation_keeps_the_original_rows(tmp_path):
    model, method = "internvl3.5-8b", "ReActPrivileged"
    jobs = list(pending(tmp_path, first_row=1, models=[model], methods=[method]))
    assert [(m, policy, i, total) for m, policy, i, total, _ in jobs] == [
        (model, method, i, 316) for i in range(1, 316)]
    directory = jobs[0][-1]
    directory.mkdir(parents=True)
    (directory / "result.json").write_text("{}")
    assert next(pending(tmp_path, 1, [model], [method])) == jobs[1]


def test_reference_table_matches_native_layout_and_distinguishes_missing_from_zero(tmp_path):
    task, variant, seed = "T24_snack_for_kid", "apple_on_table", 10
    directory = tmp_path / task / "scripted"
    directory.mkdir(parents=True)
    run_http.write_report(directory / "config.json", {"code": {"commit": "7846509", "dirty_files": []}})
    run_http.write_report(directory / "result.json", {
        "task_id": task, "variant": variant, "seed": seed, "route": "nominal", "planner": "scripted",
        "profile": MAIN, "config_hash": "layout", "episode_hash": "initial", "calls": [],
        "score": {"score": 1.0}, "task_success": True})
    scores = {("ReAct", model): {} for model in MODELS}
    peer = {"score": 0.0, "success": False, "config_hash": "layout", "episode_hash": "initial"}
    key = task, variant, seed
    jobs = [{"task": task, "variant": variant, "seed": seed}]
    scores["ReAct", "qwen3.5-27b"][key] = peer
    partial = "\n".join(reference_table([tmp_path], scores, jobs))
    assert "| 1.0 成功 | — | 0.0 失败 | — |" in partial
    assert "| 脚本至少一次成功 | 0 | — | — | — |" in partial
    scores["ReAct", "qwen3.5-4b"][key] = {**peer, "score": 1.0, "success": True}
    scores["ReAct", "internvl3.5-8b"][key] = peer.copy()
    assert "| 脚本至少一次成功 | 1 | 1/1 | 0/1 | 0/1 |" in "\n".join(reference_table([tmp_path], scores, jobs))
    other_layout_first = [{**jobs[0], "variant": "other_layout"}, *jobs]
    assert "| 脚本至少一次成功 | 0 | — | — | — |" in "\n".join(reference_table([tmp_path], scores, other_layout_first))
    peer["episode_hash"] = "another initial state"
    with pytest.raises(ValueError, match="scripted/ReAct episode mismatch"):
        reference_table([tmp_path], scores)


def test_graph_first_error_survives_a_scored_retry(tmp_path):
    model = "qwen3.5-4b"
    job = {"task": "T28_cup_to_bedside", "variant": "already_there__wrong_cup", "seed": 10}
    directory = result_path(tmp_path, model, "GraphManager", job)
    for name, status, code in [("100", "failure", None), ("200", "error", "MODEL_ERROR"),
                               ("300", "failure", "CLIENT_TIMEOUT"), ("400", "error", "PLANNER_ERROR")]:
        attempt = directory / "graph" / name
        raw_dir = attempt / job["task"] / MAIN / job["variant"] / "seed_10"
        raw_dir.mkdir(parents=True)
        run_http.write_report(raw_dir / "result.json", {
            "status": status, "attempts": [{"error_code": code}] if code else []})
        run_http.write_report(attempt / "local-provider.json", {
            "model": model, "context_window": 32768, "max_tokens": 4096,
            "workspace": "/tmp/zenobench-graph-neutral" if name != "100" else str(directory)})
    run_http.write_report(directory / "result.json", {"graph_attempt": str(directory / "graph/300")})
    scores = {("GraphManager", m): {} for m in MODELS}
    scores["GraphManager", model][job["task"], job["variant"], job["seed"]] = {"score": 0}
    lines = graph_attempt_table(tmp_path, [job], scores)
    assert "| qwen3.5-4b | 1 | 0/1 | 1 | 1 | 2 | `CLIENT_TIMEOUT` × 1，`MODEL_ERROR` × 1 |" in lines


def test_model_usage_includes_harness_compaction_and_excludes_partial_sessions():
    directory = "/tmp/zenobench-graph-example"
    events = [{"type": "session", "id": "s", "cwd": directory},
              {"type": "assistant/message", "data": {"usage": {"totalTokens": 100, "outputTokens": 10}}},
              {"type": "tool/result", "data": {}},
              {"type": "compaction/summary", "data": {"usage": {"totalTokens": 1100, "outputTokens": 100}}}]
    assert recorded_usage(map(json.dumps, events), "s", directory) == {
        "vlm_queries": 2, "input_tokens": 1090, "output_tokens": 110}
    events.append({"type": "assistant/message", "data": {"interrupted": True}})
    assert recorded_usage(map(json.dumps, events), "s", directory) is None
    with pytest.raises(ValueError, match="identity mismatch"):
        recorded_usage(map(json.dumps, events), "another", directory)


def test_first_layout_per_task_uses_existing_main_and_ablation_shards(tmp_path):
    main = episodes()
    subset = representatives(main)
    first = {}
    for row in main:
        first.setdefault(row["task"], row)
    assert len(first) == 30
    for method, catalog in [("ReAct", main), ("ReActHint", subset)]:
        jobs = list(pending(tmp_path, models=["qwen3.5-4b"], methods=[method], first_layout_per_task=True))
        assert len(jobs) == 30
        assert all(total == len(catalog) for _, _, _, total, _ in jobs)
        assert {catalog[index]["task"]: catalog[index] for _, _, index, _, _ in jobs} == first


def test_start_queue_applies_only_until_initial_task_returns(tmp_path, monkeypatch):
    def probe(url, timeout):
        assert timeout == 42
        with (tmp_path / "gpu-1.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return "queued"
        return "immediate"

    monkeypatch.setattr(urllib.request, "urlopen", probe)
    install(tmp_path, {8871: 1})
    install(tmp_path, {8871: 1})
    base = "http://127.0.0.1:8871/"
    post = urllib.request.Request(base + "initial_task", data=b"{}")
    assert urllib.request.urlopen(post, timeout=42) == "queued"
    assert urllib.request.urlopen(urllib.request.Request(base + "do_contract", data=b"{}"), timeout=42) == "immediate"
    assert urllib.request.urlopen(urllib.request.Request(base + "initial_task"), timeout=42) == "immediate"
    assert urllib.request.urlopen(url="http://127.0.0.1:8101/v1/models", timeout=42) == "immediate"


def test_harness_compacts_against_the_served_context_window(tmp_path):
    import yaml
    patch_file = tmp_path / "provider.yml"
    template = run_http.ROOT / "baseline/graph_manager/examples/harness-local-vlm.patch.yml"
    patch_file.write_text(template.read_text())
    attempt = tmp_path / "s10_block_put_away__gone_toy_block"
    attempt.mkdir()
    with isolated_workspace(patch_file, attempt) as workspace:
        assert Path(workspace).is_dir() and Path(workspace).parent == Path("/tmp")
        assert Path(workspace).name.startswith("zenobench-graph-")
        assert attempt.name not in workspace
        receipt = json.loads((attempt / "local-provider.json").read_text())
        assert receipt["workspace"] == workspace
    assert not Path(workspace).exists()
    config = yaml.safe_load(patch_file.read_text())[0]["config"]["providers"]["lab-vlm"]
    model, = config["models"]
    assert (model["contextWindow"], model["maxTokens"], model["input"]) == (32768, 4096, ["text", "image"])
    assert receipt["model"] == "qwen3.5-4b"


def test_graph_with_layout_name_in_model_workspace_is_unscored(tmp_path):
    attempt = tmp_path / "graph" / "attempt"
    attempt.mkdir(parents=True)
    run_http.write_report(tmp_path / "result.json", {"graph_attempt": str(attempt)})
    provider = {"model": "qwen3.5-4b", "max_tokens": 4096, "context_window": 32768}
    for old in (provider, {**provider, "workspace": "/runs/s10_gone_toy_block/workspace"}):
        run_http.write_report(attempt / "local-provider.json", old)
        assert read_outcome(tmp_path, tmp_path, "qwen3.5-4b", "GraphManager", {}) == ("interrupted", None)
        assert not result_is_current(tmp_path, "qwen3.5-4b", "GraphManager")
    with claim_episode(tmp_path, "qwen3.5-4b", "GraphManager") as owner:
        assert owner is not None
        patch_file = tmp_path / "provider.yml"
        template = run_http.ROOT / "baseline/graph_manager/examples/harness-local-vlm.patch.yml"
        patch_file.write_text(template.read_text())
        args = SimpleNamespace(model="qwen3.5-4b", graph_bin="graph-manager-run", server="localhost",
                               out=tmp_path, native_dir=tmp_path / "native")
        job = {"task": "test", "variant": "gone_toy_block", "seed": 10}
        with patch("baseline.comparison.subprocess.run", return_value=SimpleNamespace(returncode=1)) as run:
            run_graph(args, job, tmp_path, tmp_path, patch_file)
        command = run.call_args.args[0]
        assert command[command.index("--workspace") + 1].startswith("/tmp/zenobench-graph-")
    assert json.loads(next((tmp_path / "excluded").glob("*/result.json")).read_text())["graph_attempt"] == str(attempt)
    failed = json.loads((tmp_path / "failed.json").read_text())
    native = args.native_dir / "test" / "exp"
    native.mkdir(parents=True)
    run_http.write_report(native / "result.json", {"incomplete": False, "episode_hash": "initial",
                                                  "score": {"score": 0}, "task_success": False, "dropped": []})

    def finish(command, **kwargs):
        raw = Path(command[command.index("--out") + 1]) / "test" / MAIN / "gone_toy_block" / "seed_10"
        raw.mkdir(parents=True)
        run_http.write_report(raw / "result.json", {"status": "failure", "episode": {
            "exp_id": "exp", "profile": {"max_calls": 60}, "env_episode": {"episode_hash": "initial"},
            "contract_calls": 0, "elapsed_s": 5, "reason": "model_gave_up", "model_turns": 3, "invalid_replies": 3}})
        return SimpleNamespace(returncode=0)

    with patch("baseline.comparison.subprocess.run", finish):
        assert run_graph(args, job, tmp_path, tmp_path, patch_file)["exp_id"] == "exp"
    assert not (tmp_path / "failed.json").exists()
    assert json.loads((Path(failed["graph_attempt"]) / "comparison-interruption.json").read_text()) == failed


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
                          "calls": [{"skill": "place", "feedback": {"success": False, "action": "place(apple, desk)"},
                                     "eval": {"failed_substep": ["place(apple, desk)", "tuck()"],
                                              "leaf_code": "POLICY_FAILED"}},
                                    {"skill": "pick", "feedback": {"success": False, "action": "pick(apple)"},
                                     "eval": {"failed_substep": ["pick(apple)"], "leaf_code": "NOT_OBSERVED"}},
                                    {"skill": "navigate", "feedback": {"success": True}, "eval": {"leaf_code": None}}]})
    status, r = read_outcome(planner, tmp_path / "native", "local", "ReAct", job, "6.0.0.1")
    assert status == "scored"
    assert r["score"] == value and r["success"] == success and r["execution"]
    assert r["best_success"] == best_success
    assert r["failure_classes"] == {"execution", "observation"}
    assert r["plan_labels"] == {"valid": 2, "undetermined": 1}
    assert r["valid_execution_failures"] == 1
    assert r["stop_reason"] == ("service_limit" if tier == "second" else "finish")
    with pytest.raises(ValueError, match="simulator version mismatch"):
        read_outcome(planner, tmp_path / "native", "local", "ReAct", job, "5.1.0.0")
