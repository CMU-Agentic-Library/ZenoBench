"""Environment service without Isaac Sim: HTTP endpoints, scheduling, limits, release, result filtering."""
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from env_service.server import Config, ExpManager, load_registry, make_handler
from env_service.worker import public_result
from episode.catalog import legacy_task
from episode.profile import load_profile

FAKE = Path(__file__).parent / "fixtures" / "fake_env_worker.py"


def _entry(t, profile="gt", **extra):
    task = legacy_task({"id": t, "description": f"do {t}", "goal": [], "entities": [], "task_json": f"tasks/{t}/task.json"})
    task.update(extra)
    return {"task": task, "catalog": "fake.json", "profile": dict(load_profile(profile), path=profile)}


TASKS = {t: _entry(t) for t in ("t1", "t2", "t3", "crash_task", "bad_start", "slow_start")}
TASKS["b1"] = _entry("b1", "benchmark", variants={"easy": {}, "hard": {}}, max_calls=7)


class Service:
    def __init__(self, tmp_path, **cfg):
        self.cfg = Config(worker_argv=[sys.executable, str(FAKE)], log_dir=tmp_path, **cfg)
        self.manager = ExpManager(self.cfg, TASKS)
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.manager))
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"

    def post(self, path, body):
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def start(self, task_id="t1"):
        status, body = self.post("/initial_task", {"task_id": task_id})
        assert status == 200, body
        return body["exp_id"]

    def close(self):
        self.http.shutdown()
        self.manager.shutdown()


@pytest.fixture
def service(tmp_path):
    s = Service(tmp_path)
    yield s
    s.close()


def test_full_episode(service):
    status, body = service.post("/initial_task", {"task_id": "t1"})
    assert status == 200 and set(body) == {"exp_id", "task", "profile", "observation"}
    exp = body["exp_id"]
    assert exp.startswith("t1-")
    assert body["task"] == {"task_id": "t1", "name": "t1", "description": "do t1"}
    assert body["profile"] == {"name": "gt", "observation": ["images", "objects", "robot", "task_status"],
                               "max_calls": 40}
    assert body["observation"]["task_status"][0]["holds"] is False
    # a single call object is a list of one
    status, body = service.post("/do_contract", {"exp_id": exp, "calls": {"contract": "pick", "args": {"object": "apple"}}})
    assert status == 200 and [r["success"] for r in body["results"]] == [True]
    assert body["observation"]["task_status"][0]["holds"] is True
    status, body = service.post("/check_task", {"exp_id": exp})
    assert status == 200 and body["success"] is True
    assert body["goal"] == [{"atom": "holding(right, apple)", "holds": True}] and body["dropped"] == []
    assert body["episode"]["profile"] == "gt"
    assert service.post("/do_contract", {"exp_id": exp, "calls": [{"contract": "pick", "args": {}}]})[0] == 410
    assert service.manager.running == 0


def test_stops_at_first_failure(service):
    exp = service.start()
    calls = [{"contract": "navigate", "args": {"destination": "x"}}, {"contract": "pick", "args": {"object": "fail_cup"}},
             {"contract": "pick", "args": {"object": "apple"}}]
    body = service.post("/do_contract", {"exp_id": exp, "calls": calls})[1]
    assert [r["success"] for r in body["results"]] == [True, False]
    assert body["results"][1]["error_code"] == "PRECONDITION_FAILED"


def test_busy_beyond_two_simulators(service):
    first, _ = service.start("t1"), service.start("t2")
    status, body = service.post("/initial_task", {"task_id": "t3"})
    assert status == 503 and body["error_code"] == "BUSY"
    assert service.manager.running == 2 and "t3" not in {e.task["task_id"] for e in service.manager.exps.values()}
    service.post("/check_task", {"exp_id": first})
    assert service.start("t3").startswith("t3-")


def test_starting_simulator_counts_as_running(service):
    service.start("t1")
    box = {}
    slow = threading.Thread(target=lambda: box.setdefault("r", service.post("/initial_task", {"task_id": "slow_start"})))
    slow.start()
    time.sleep(1)
    status, body = service.post("/initial_task", {"task_id": "t2"})
    assert status == 503 and body["error_code"] == "BUSY"
    slow.join()
    assert box["r"][0] == 200


def test_observe(service):
    exp = service.start()
    status, body = service.post("/observe", {"exp_id": exp})
    assert status == 200 and body["state"] == "ready" and body["calls_used"] == 0
    assert body["observation"]["task_status"][0]["holds"] is False
    box = {}
    t = threading.Thread(target=lambda: box.setdefault("r", service.post(
        "/do_contract", {"exp_id": exp, "calls": [{"contract": "slow", "args": {}}]})))
    t.start()
    time.sleep(0.5)
    t0 = time.time()
    status, body = service.post("/observe", {"exp_id": exp})
    assert time.time() - t0 < 0.5                           # not blocked by the running contract
    assert status == 200 and body == {"exp_id": exp, "state": "running", "calls_used": 1, "observation": None}
    t.join(5)
    assert box["r"][0] == 200
    service.post("/check_task", {"exp_id": exp})
    status, body = service.post("/observe", {"exp_id": exp})
    assert status == 200 and body["state"] == "released" and body["observation"] is None
    assert service.post("/observe", {"exp_id": "nope"})[1]["error_code"] == "UNKNOWN_EXP"


def test_observe_is_not_activity(tmp_path):
    s = Service(tmp_path, idle_timeout_s=0.5)
    try:
        exp = s.start()
        for _ in range(12):                                  # polling does not keep the exp alive
            s.post("/observe", {"exp_id": exp})
            time.sleep(0.5)
        assert s.post("/observe", {"exp_id": exp})[1]["state"] == "released"
    finally:
        s.close()


def test_default_limits():
    cfg = Config()
    assert (cfg.max_calls, cfg.idle_timeout_s, cfg.max_duration_s) == (None, 1200, 3600)
    assert cfg.start_timeout_s < 900                        # answers before the planner's 15 min timeout


def test_benchmark_task_profile_variant_and_budget(service):
    status, body = service.post("/initial_task", {"task_id": "b1", "variant": "hard", "seed": 12})
    assert status == 200 and body["profile"]["name"] == "benchmark" and body["profile"]["max_calls"] == 7
    assert "objects" not in body["profile"]["observation"] and "task_status" not in body["profile"]["observation"]
    argv = (service.cfg.log_dir / "b1" / body["exp_id"] / "argv.json").read_text()
    assert '"--variant", "hard"' in argv and '"--seed", "12"' in argv and "benchmark" in argv
    assert service.post("/initial_task", {"task_id": "b1", "variant": "nope"})[1]["error_code"] == "UNKNOWN_VARIANT"
    assert service.post("/initial_task", {"task_id": "b1", "seed": "x"})[1]["error_code"] == "BAD_REQUEST"
    assert service.post("/initial_task", {"task_id": "b1", "difficulty": "insane"})[1]["error_code"] == "BAD_REQUEST"


def test_default_registry_loads_both_catalogs(tmp_path):
    reg = load_registry({"skill_library/tasks.json": "gt", "benchmark/v3/tasks.json": "benchmark"})
    assert reg["collect_fruits"]["profile"]["name"] == "gt"
    assert reg["collect_fruits"]["task"]["variants"] == {"default": {"note": "the task's own scene, no overlay"}}
    assert reg["T01_book_to_dining_table"]["profile"]["name"] == "benchmark"
    with pytest.raises(ValueError):
        copy = tmp_path / "tasks.json"
        copy.write_text((Path(__file__).parents[1] / "skill_library/tasks.json").read_text())
        load_registry({"skill_library/tasks.json": "gt", str(copy): "gt"})     # a task id in two catalogs


def test_enum_values_are_checked():
    from episode.episode import Episode
    ran = []
    ep = object.__new__(Episode)
    contracts = {"pick": {"inputs": {"object": {"type": "object_ref"}, "grasp": {"type": "tag", "enum": ["handle", "rim"]}}}}

    def contract(key):
        return contracts[key]
    ep.runner = SimpleNamespace(contract=contract, run=lambda verb, args: ran.append(args) or SimpleNamespace(
        success=True, error_code=None, error=None, preconditions=[], postconditions=[], outputs={}, children=[],
        action="pick_object(object=mug)", selected_path="p"))
    ep.profile = load_profile("gt")
    ep.observer = None
    out, record = ep.call({"contract": "pick", "args": {"object": "mug", "grasp": "spoon"}})
    assert out["error_code"] == "INPUT_UNKNOWN" and "grasp" in out["error"] and not ran
    out, record = ep.call({"contract": "pick", "args": {"object": "mug", "grasp": "rim"}})
    assert out["success"] and record["path"] == "p" and "path" not in out
    assert ep.call({"contract": "jump", "args": {}})[0]["error_code"] == "UNKNOWN_CONTRACT"
    assert ep.call(["pick"])[0]["error_code"] == "BAD_CALL"


def test_simulators_start_one_at_a_time(service):
    box = {}
    threads = [threading.Thread(target=lambda t=t: box.setdefault(t, (service.post("/initial_task", {"task_id": t}), time.time())))
               for t in ("slow_start", "t1")]
    t0 = time.time()
    threads[0].start()
    time.sleep(0.5)
    threads[1].start()
    for th in threads:
        th.join(10)
    assert box["slow_start"][0][0] == 200 and box["t1"][0][0] == 200
    assert box["t1"][1] >= box["slow_start"][1] - 0.1        # t1 started only after slow_start was up
    assert box["t1"][1] - t0 >= 3


def test_start_failure(service):
    status, body = service.post("/initial_task", {"task_id": "bad_start"})
    assert status == 500 and body["error_code"] == "SIM_ERROR" and "scene failed to load" in body["error"]
    assert service.manager.running == 0


def test_start_timeout(tmp_path):
    s = Service(tmp_path, start_timeout_s=0.5)
    try:
        status, body = s.post("/initial_task", {"task_id": "slow_start"})
        assert status == 500 and body["error_code"] == "SIM_ERROR"
        assert s.manager.running == 0
    finally:
        s.close()


def test_call_limit(tmp_path):
    s = Service(tmp_path, max_calls=3)
    try:
        exp = s.start()
        body = s.post("/do_contract", {"exp_id": exp, "calls": [{"contract": "wave", "args": {}}] * 5})[1]
        assert [r["success"] for r in body["results"]] == [True, True, True, False]
        assert body["results"][-1]["error_code"] == "LIMIT_EXCEEDED"
        assert s.post("/check_task", {"exp_id": exp})[0] == 200
    finally:
        s.close()


def test_idle_release(tmp_path):
    s = Service(tmp_path, idle_timeout_s=0.2)
    try:
        exp = s.start()
        time.sleep(6)                          # the reaper checks every 5 s
        status, body = s.post("/check_task", {"exp_id": exp})
        assert status == 410 and "idle" in body["error"]
        assert s.manager.running == 0
    finally:
        s.close()


def test_undelivered_initial_task_releases(service):
    exp = service.manager.initial_task({"task_id": "t1"})["exp_id"]
    service.manager.abandon(exp)
    assert service.manager.exps[exp].state == "released" and service.manager.running == 0


def test_simulator_crash(service):
    exp = service.start("crash_task")
    status, body = service.post("/do_contract", {"exp_id": exp, "calls": [{"contract": "pick", "args": {}}]})
    assert status == 500 and body["error_code"] == "SIM_CRASHED"
    assert service.post("/check_task", {"exp_id": exp})[0] == 410


def test_bad_requests(service):
    assert service.post("/initial_task", {"task_id": "nope"})[1]["error_code"] == "UNKNOWN_TASK"
    for body in ({}, {"task_id": ""}):
        status, out = service.post("/initial_task", body)
        assert status == 400 and out["error_code"] == "BAD_REQUEST"
    assert service.post("/do_contract", {"exp_id": "nope", "calls": [{}]})[1]["error_code"] == "UNKNOWN_EXP"
    assert service.post("/check_task", {})[1]["error_code"] == "BAD_REQUEST"
    assert service.post("/nowhere", {})[0] == 404


def test_public_result_hides_internals():
    child = {"success": False, "action": "place_object(object=apple)", "error_code": "PRECONDITION_FAILED",
             "preconditions": [{"atom": "uncovered(container=pot)", "holds": False, "detail": "lid on"}],
             "postconditions": [], "children": []}
    res = SimpleNamespace(success=False, error_code="SUBSKILL_FAILED", error="path to_container: place failed",
                          preconditions=[{"atom": "hand_empty(hand=right)", "holds": True, "detail": "x"}],
                          postconditions=[], outputs={}, selected_path="to_container", policy_steps=[1],
                          bound_nouns={"a": 1}, recovery=[{"verb": "uncover"}],
                          children=[{"success": True, "action": "pick_object(object=apple)"}, child])
    out = public_result({"contract": "fetch", "args": {"object": "apple"}}, res)
    assert set(out) == {"contract", "args", "success", "error_code", "error", "preconditions", "postconditions",
                        "outputs", "failed_step"}
    assert out["error"] == "place failed"
    assert out["preconditions"] == [{"atom": "hand_empty(hand=right)", "holds": True}]
    assert out["failed_step"]["action"] == "place_object(object=apple)"
    text = json.dumps(out)
    assert "to_container" not in text and '"verb"' not in text and "detail" not in text
