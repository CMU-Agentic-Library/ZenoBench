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

from env_service.server import Config, ExpManager, make_handler
from env_service.worker import public_result

FAKE = Path(__file__).parent / "fixtures" / "fake_env_worker.py"
TASKS = {t: {"id": t, "description": f"do {t}", "goal": [], "entities": []} for t in ("t1", "t2", "t3", "crash_task")}


class Service:
    def __init__(self, tmp_path, fail_push=0, **cfg):
        self.pushed, self.fail_push = [], fail_push
        self.cfg = Config(worker_argv=[sys.executable, str(FAKE)], log_dir=tmp_path,
                          callback_retry_s=0.05, **cfg)
        self.manager = ExpManager(self.cfg, TASKS, push=self._push)
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.manager))
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"

    def _push(self, payload):
        if self.fail_push:
            self.fail_push -= 1
            raise RuntimeError("planner down")
        self.pushed.append(payload)

    def post(self, path, body):
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def wait_pushed(self, n, timeout=10):
        t0 = time.time()
        while len(self.pushed) < n:
            assert time.time() - t0 < timeout, f"only {len(self.pushed)} callbacks"
            time.sleep(0.02)

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
    assert status == 200 and body["exp_id"].startswith("t1-")
    exp = body["exp_id"]
    service.wait_pushed(1)
    push = service.pushed[0]
    assert push["exp_id"] == exp and push["status"] == "ready"
    assert push["task"] == {"task_id": "t1", "name": "t1", "description": "do t1"}
    assert "goal" not in json.dumps(push["task"])
    # a single call object is a list of one
    status, body = service.post("/do_contract", {"exp_id": exp, "calls": {"contract": "pick", "args": {"object": "apple"}}})
    assert status == 200 and [r["success"] for r in body["results"]] == [True]
    assert body["observation"]["task_status"][0]["holds"] is True
    status, body = service.post("/check_task", {"exp_id": exp})
    assert status == 200 and body["success"] is True
    assert service.post("/do_contract", {"exp_id": exp, "calls": [{"contract": "pick", "args": {}}]})[0] == 410


def test_stops_at_first_failure(service):
    exp = service.post("/initial_task", {"task_id": "t1"})[1]["exp_id"]
    service.wait_pushed(1)
    calls = [{"contract": "navigate", "args": {"destination": "x"}}, {"contract": "pick", "args": {"object": "fail_cup"}},
             {"contract": "pick", "args": {"object": "apple"}}]
    body = service.post("/do_contract", {"exp_id": exp, "calls": calls})[1]
    assert [r["success"] for r in body["results"]] == [True, False]
    assert body["results"][1]["error_code"] == "PRECONDITION_FAILED"


def test_all_tasks_queue_behind_two_simulators(service):
    status, body = service.post("/initial_task", {})
    assert status == 200 and len(body["exp_ids"]) == len(TASKS)
    service.wait_pushed(2)
    time.sleep(0.3)
    assert len(service.pushed) == 2            # the rest wait for a free simulator
    assert service.manager.running == 2
    first = service.pushed[0]["exp_id"]
    queued = next(e for e in body["exp_ids"] if e not in {p["exp_id"] for p in service.pushed})
    assert service.post("/do_contract", {"exp_id": queued, "calls": [{"contract": "pick"}]})[0] == 409
    service.post("/check_task", {"exp_id": first})
    service.wait_pushed(3)


def test_call_limit(tmp_path):
    s = Service(tmp_path, max_calls=3)
    try:
        exp = s.post("/initial_task", {"task_id": "t1"})[1]["exp_id"]
        s.wait_pushed(1)
        body = s.post("/do_contract", {"exp_id": exp, "calls": [{"contract": "wave", "args": {}}] * 5})[1]
        assert [r["success"] for r in body["results"]] == [True, True, True, False]
        assert body["results"][-1]["error_code"] == "LIMIT_EXCEEDED"
        assert s.post("/check_task", {"exp_id": exp})[0] == 200
    finally:
        s.close()


def test_idle_release(tmp_path):
    s = Service(tmp_path, idle_timeout_s=0.2)
    try:
        exp = s.post("/initial_task", {"task_id": "t1"})[1]["exp_id"]
        s.wait_pushed(1)
        time.sleep(6)                          # the reaper checks every 5 s
        status, body = s.post("/check_task", {"exp_id": exp})
        assert status == 410 and "idle" in body["error"]
        assert s.manager.running == 0
    finally:
        s.close()


def test_callback_retries_then_releases(tmp_path):
    s = Service(tmp_path, fail_push=3)
    try:
        exp = s.post("/initial_task", {"task_id": "t1"})[1]["exp_id"]
        t0 = time.time()
        while s.manager.exps[exp].state != "released":
            assert time.time() - t0 < 10
            time.sleep(0.02)
        assert s.manager.exps[exp].release_reason == "callback_failed" and s.manager.running == 0
    finally:
        s.close()


def test_simulator_crash(service):
    exp = service.post("/initial_task", {"task_id": "crash_task"})[1]["exp_id"]
    service.wait_pushed(1)
    status, body = service.post("/do_contract", {"exp_id": exp, "calls": [{"contract": "pick", "args": {}}]})
    assert status == 500 and body["error_code"] == "SIM_CRASHED"
    assert service.post("/check_task", {"exp_id": exp})[0] == 410


def test_bad_requests(service):
    assert service.post("/initial_task", {"task_id": "nope"})[1]["error_code"] == "UNKNOWN_TASK"
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
