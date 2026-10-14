"""HTTP environment service (standard library only).

    python -m env_service.server --callback-url http://<planner-host>:<port>/<path> [--port 8800]

Endpoints (JSON in, JSON out):

* ``POST /initial_task``  {"task_id": "collect_fruits"} -> {"exp_id": ...};
  {} or "task_id": "" -> {"exp_ids": [...]} (one exp per task).  Returns at once;
  each exp waits for a simulator slot, starts, and is pushed to the callback URL.
* ``POST /do_contract``   {"exp_id", "calls": [{"contract", "args"}, ...]} (a single
  call object is a list of one) -> {"exp_id", "results": [...], "observation"}.
  Calls run in order and stop at the first failure.
* ``POST /check_task``    {"exp_id"} -> {"exp_id", "success", "goal"}; then the exp is released.

Workers run under ``--worker-python`` (default: $ISAACLAB_PYTHON, else this Python).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from env_service.tasks import ROOT, load_tasks, public_task


class ServiceError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code = status, code


class Config:
    def __init__(self, **kw):
        self.callback_url = kw.get("callback_url")
        self.max_sims = kw.get("max_sims", 2)
        self.idle_timeout_s = kw.get("idle_timeout_s", 600)
        self.max_calls = kw.get("max_calls", 40)
        self.max_duration_s = kw.get("max_duration_s", 1800)
        self.callback_retries = kw.get("callback_retries", 3)
        self.callback_retry_s = kw.get("callback_retry_s", 5)
        self.start_timeout_s = kw.get("start_timeout_s", 900)
        self.wrist_cameras = kw.get("wrist_cameras", True)
        python = kw.get("worker_python") or os.environ.get("ISAACLAB_PYTHON") or sys.executable
        self.worker_argv = kw.get("worker_argv") or [python, "-m", "env_service.worker"]
        self.log_dir = Path(kw.get("log_dir") or ROOT / "runs" / "env_service")


class Worker:
    """A worker process with a request/response pipe pair."""

    def __init__(self, cfg: Config, exp_id: str, task_id: str):
        cmd_r, cmd_w = os.pipe()
        resp_r, resp_w = os.pipe()
        log_dir = cfg.log_dir / exp_id
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = log_dir / "worker.log"
        argv = cfg.worker_argv + ["--task-id", task_id,
                "--cmd-fd", str(cmd_r), "--resp-fd", str(resp_w)] + (["--wrist-cameras"] if cfg.wrist_cameras else [])
        with open(self.log_path, "w") as log:
            self.proc = subprocess.Popen(argv, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log,
                                         stderr=subprocess.STDOUT, pass_fds=(cmd_r, resp_w))
        os.close(cmd_r)
        os.close(resp_w)
        self.cmd = os.fdopen(cmd_w, "w")
        self.resp = os.fdopen(resp_r, "r")

    def read(self):
        line = self.resp.readline()
        if not line:
            raise ServiceError(HTTPStatus.INTERNAL_SERVER_ERROR, "SIM_CRASHED",
                               f"simulator process exited (code {self.proc.poll()}); see {self.log_path}")
        msg = json.loads(line)
        if "error" in msg and msg.get("type") != "error":
            raise ServiceError(HTTPStatus.INTERNAL_SERVER_ERROR, "SIM_ERROR", msg["error"])
        return msg

    def request(self, op, **kw):
        try:
            self.cmd.write(json.dumps({"op": op, **kw}) + "\n")
            self.cmd.flush()
        except (BrokenPipeError, ValueError):
            raise ServiceError(HTTPStatus.INTERNAL_SERVER_ERROR, "SIM_CRASHED",
                               f"simulator process is gone; see {self.log_path}")
        return self.read()

    def close(self):
        try:
            self.cmd.write(json.dumps({"op": "close"}) + "\n")
            self.cmd.flush()
        except (BrokenPipeError, ValueError):
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        for f in (self.cmd, self.resp):
            try:
                f.close()
            except OSError:
                pass


class Exp:
    def __init__(self, exp_id, task):
        self.exp_id, self.task = exp_id, task
        self.state = "queued"         # queued -> starting -> ready -> released
        self.worker: Worker | None = None
        self.lock = threading.Lock()  # one request at a time per simulator
        self.calls = 0
        self.ready_at = None
        self.last_activity = None
        self.release_reason = None


class ExpManager:
    def __init__(self, cfg: Config, tasks: dict, push=None):
        self.cfg, self.tasks = cfg, tasks
        self.push = push or self._post_callback
        self.exps: dict[str, Exp] = {}
        self.queue: collections.deque[Exp] = collections.deque()
        self.lock = threading.Lock()
        self.running = 0
        self._stop = threading.Event()
        threading.Thread(target=self._reaper, daemon=True).start()

    # -- interface 1 ------------------------------------------------------------------
    def initial_task(self, task_id):
        if task_id in (None, ""):
            ids = list(self.tasks)
        elif task_id in self.tasks:
            ids = [task_id]
        else:
            raise ServiceError(HTTPStatus.BAD_REQUEST, "UNKNOWN_TASK", f"no task {task_id!r} in skill_library/tasks.json")
        exps = []
        with self.lock:
            for tid in ids:
                exp = Exp(f"{tid}-{uuid.uuid4().hex[:8]}", self.tasks[tid])
                self.exps[exp.exp_id] = exp
                self.queue.append(exp)
                exps.append(exp.exp_id)
            self._schedule()
        return {"exp_id": exps[0]} if task_id else {"exp_ids": exps}

    def _schedule(self):          # holds self.lock
        while self.queue and self.running < self.cfg.max_sims:
            exp = self.queue.popleft()
            if exp.state != "queued":
                continue
            exp.state = "starting"
            self.running += 1
            threading.Thread(target=self._start, args=(exp,), daemon=True).start()

    def _start(self, exp: Exp):
        try:
            exp.worker = Worker(self.cfg, exp.exp_id, exp.task["id"])
            msg = _with_timeout(exp.worker.read, self.cfg.start_timeout_s)
            if msg.get("type") != "ready":
                raise RuntimeError(msg.get("error", "simulator failed to start"))
        except Exception as exc:
            self._log(exp, f"start failed: {exc}")
            self._try_push({"exp_id": exp.exp_id, "status": "failed", "task": public_task(exp.task),
                            "error": f"simulator failed to start: {exc}"})
            self.release(exp, "start_failed")
            return
        with exp.lock:
            if exp.state != "starting":       # released (shutdown) meanwhile
                return
            # ready before the push: the planner may call back as soon as it has the exp_id
            exp.state = "ready"
            exp.ready_at = exp.last_activity = time.time()
        payload = {"exp_id": exp.exp_id, "status": "ready", "task": public_task(exp.task),
                   "observation": msg["observation"]}
        if not self._try_push(payload):
            self.release(exp, "callback_failed")
            return
        with exp.lock:
            if exp.calls == 0:                # idle and duration limits count from the successful push
                exp.ready_at = exp.last_activity = time.time()

    def _try_push(self, payload):
        for attempt in range(self.cfg.callback_retries):
            try:
                self.push(payload)
                return True
            except Exception as exc:
                self._log(None, f"callback {payload['exp_id']} attempt {attempt + 1} failed: {exc}")
                if attempt + 1 < self.cfg.callback_retries:
                    time.sleep(self.cfg.callback_retry_s)
        return False

    def _post_callback(self, payload):
        if not self.cfg.callback_url:
            raise RuntimeError("no --callback-url configured")
        req = urllib.request.Request(self.cfg.callback_url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status >= 300:
                raise RuntimeError(f"HTTP {r.status}")

    # -- interfaces 2 and 3 -------------------------------------------------------------
    def _ready(self, exp_id) -> Exp:
        exp = self.exps.get(exp_id)
        if exp is None:
            raise ServiceError(HTTPStatus.NOT_FOUND, "UNKNOWN_EXP", f"no exp {exp_id!r}")
        if exp.state == "released":
            raise ServiceError(HTTPStatus.GONE, "EXP_RELEASED", f"exp {exp_id} was released ({exp.release_reason})")
        if exp.state != "ready":
            raise ServiceError(HTTPStatus.CONFLICT, "EXP_NOT_READY", f"exp {exp_id} is {exp.state}; wait for its callback")
        return exp

    def do_contract(self, exp_id, calls):
        if isinstance(calls, dict):
            calls = [calls]
        if not isinstance(calls, list) or not calls:
            raise ServiceError(HTTPStatus.BAD_REQUEST, "BAD_REQUEST", '"calls" must be a call object or a non-empty list')
        exp = self._ready(exp_id)
        with exp.lock:
            if exp.state != "ready":
                raise ServiceError(HTTPStatus.GONE, "EXP_RELEASED", f"exp {exp_id} was released ({exp.release_reason})")
            results = []
            try:
                for call in calls:
                    limit = self._limit(exp)
                    if limit:
                        results.append(_failure(call, "LIMIT_EXCEEDED", limit))
                        break
                    exp.calls += 1
                    res = exp.worker.request("contract", call=call)["result"]
                    results.append(res)
                    exp.last_activity = time.time()
                    if not res["success"]:
                        break
                obs = exp.worker.request("observe")["observation"]
            except ServiceError as exc:
                self._release_locked(exp, "sim_crashed")
                raise exc
            exp.last_activity = time.time()
        return {"exp_id": exp_id, "results": results, "observation": obs}

    def _limit(self, exp):
        if exp.calls >= self.cfg.max_calls:
            return f"this exp already ran {exp.calls} contract calls (limit {self.cfg.max_calls})"
        if time.time() - exp.ready_at >= self.cfg.max_duration_s:
            return f"this exp has run for more than {self.cfg.max_duration_s // 60} minutes"
        return None

    def check_task(self, exp_id):
        exp = self._ready(exp_id)
        with exp.lock:
            if exp.state != "ready":
                raise ServiceError(HTTPStatus.GONE, "EXP_RELEASED", f"exp {exp_id} was released ({exp.release_reason})")
            try:
                res = exp.worker.request("check")
            finally:
                self._release_locked(exp, "checked")
        return {"exp_id": exp_id, "success": res["success"], "goal": res["goal"]}

    # -- release ----------------------------------------------------------------------
    def release(self, exp, reason):
        with exp.lock:
            self._release_locked(exp, reason)

    def _release_locked(self, exp, reason):
        if exp.state == "released":
            return
        held_slot = exp.state in ("starting", "ready")
        exp.state, exp.release_reason = "released", reason
        if exp.worker is not None:
            exp.worker.close()
        self._log(exp, f"released ({reason}) after {exp.calls} calls")
        if held_slot:
            with self.lock:
                self.running -= 1
                self._schedule()

    def _reaper(self):
        while not self._stop.wait(5):
            now = time.time()
            for exp in list(self.exps.values()):
                if exp.state == "ready" and now - exp.last_activity > self.cfg.idle_timeout_s \
                        and exp.lock.acquire(blocking=False):
                    try:
                        if exp.state == "ready" and now - exp.last_activity > self.cfg.idle_timeout_s:
                            self._release_locked(exp, "idle")
                    finally:
                        exp.lock.release()

    def shutdown(self):
        self._stop.set()
        for exp in list(self.exps.values()):
            self.release(exp, "shutdown")

    def _log(self, exp, text):
        print(f"[env_service] {exp.exp_id + ': ' if exp else ''}{text}", flush=True)


def _failure(call, code, message):
    return {"contract": call.get("contract") if isinstance(call, dict) else None,
            "args": call.get("args", {}) if isinstance(call, dict) else {}, "success": False,
            "error_code": code, "error": message, "preconditions": [], "postconditions": [], "outputs": {}}


def _with_timeout(fn, seconds):
    box = {}

    def run():
        try:
            box["value"] = fn()
        except Exception as exc:
            box["error"] = exc
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive():
        raise TimeoutError(f"no answer within {seconds} s")
    if "error" in box:
        raise box["error"]
    return box["value"]


def make_handler(manager: ExpManager):
    routes = {
        "/initial_task": lambda body: manager.initial_task(body.get("task_id")),
        "/do_contract": lambda body: manager.do_contract(_need(body, "exp_id"), body.get("calls")),
        "/check_task": lambda body: manager.check_task(_need(body, "exp_id")),
    }

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self):
            route = routes.get(self.path.rstrip("/"))
            try:
                if route is None:
                    raise ServiceError(HTTPStatus.NOT_FOUND, "NOT_FOUND", f"no endpoint {self.path}")
                n = int(self.headers.get("Content-Length") or 0)
                try:
                    body = json.loads(self.rfile.read(n) or b"{}")
                except json.JSONDecodeError as exc:
                    raise ServiceError(HTTPStatus.BAD_REQUEST, "BAD_REQUEST", f"invalid JSON: {exc}")
                if not isinstance(body, dict):
                    raise ServiceError(HTTPStatus.BAD_REQUEST, "BAD_REQUEST", "body must be a JSON object")
                self._send(HTTPStatus.OK, route(body))
            except ServiceError as exc:
                self._send(exc.status, {"error_code": exc.code, "error": str(exc)})
            except Exception as exc:
                traceback.print_exc()
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error_code": "INTERNAL_ERROR", "error": str(exc)})

        def _send(self, status, payload):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            print(f"[http] {self.address_string()} {fmt % args}", flush=True)

    return Handler


def _need(body, key):
    if not body.get(key):
        raise ServiceError(HTTPStatus.BAD_REQUEST, "BAD_REQUEST", f'missing "{key}"')
    return body[key]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8800)
    ap.add_argument("--callback-url", default=os.environ.get("ZENO_CALLBACK_URL"),
                    help="planner endpoint that receives each started exp (default: $ZENO_CALLBACK_URL)")
    ap.add_argument("--max-sims", type=int, default=2)
    ap.add_argument("--no-wrist-cameras", action="store_true")
    ap.add_argument("--worker-python")
    ap.add_argument("--log-dir")
    args = ap.parse_args()
    if not args.callback_url:
        ap.error("--callback-url (or $ZENO_CALLBACK_URL) is required")
    cfg = Config(callback_url=args.callback_url, max_sims=args.max_sims, wrist_cameras=not args.no_wrist_cameras,
                 worker_python=args.worker_python, log_dir=args.log_dir)
    manager = ExpManager(cfg, load_tasks())
    server = ThreadingHTTPServer((args.host, args.port), make_handler(manager))
    print(f"[env_service] listening on {args.host}:{args.port}, callback {cfg.callback_url}, "
          f"{cfg.max_sims} simulators", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        manager.shutdown()


if __name__ == "__main__":
    main()
