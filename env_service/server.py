"""HTTP environment service (standard library only).

    python -m env_service.server [--port 8800]

Endpoints (JSON in, JSON out):

* ``POST /initial_task``  {"task_id", "variant"?, "seed"?, "difficulty"?}
  -> {"exp_id", "task", "profile", "observation"}.
  Blocks until the simulator is up; 503 BUSY when all simulators are taken (no queue).
* ``POST /do_contract``   {"exp_id", "calls": [{"contract", "args"}, ...]} (a single
  call object is a list of one) -> {"exp_id", "results": [...], "observation"}.
  Calls run in order and stop at the first failure.
* ``POST /check_task``    {"exp_id"} -> {"exp_id", "success", "goal", "dropped", "episode"}; then the
  exp is released.
* ``POST /observe``       {"exp_id"} -> {"exp_id", "state", "calls_used", "observation"}; never
  waits for a running ``do_contract`` (state "running", observation null) and does
  not count as activity for the idle limit.

Tasks come from one or more catalogs (``--catalog PATH=PROFILE``, default: the original tasks
with the ``gt`` profile and benchmark v3 with the ``benchmark`` profile); the profile of a
task's catalog fixes its execution switches, observation fields and call budget
(episode/profiles/*.yaml).  The planner cannot choose it.

Workers run under ``--worker-python`` (default: $ISAACLAB_PYTHON, else this Python).
Standard library plus PyYAML.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from episode.catalog import DEFAULT_CATALOGS, ROOT, load_catalog, public_task
from episode.episode import flat_goal
from episode.profile import load_profile, max_calls, observation_fields


class ServiceError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code = status, code


class Config:
    def __init__(self, **kw):
        self.max_sims = kw.get("max_sims", 2)
        self.idle_timeout_s = kw.get("idle_timeout_s", 1200)
        self.max_calls = kw.get("max_calls")          # None: the task's profile decides (limits.max_calls)
        self.max_duration_s = kw.get("max_duration_s", 3600)
        # below the planner's 15 min client timeout, so it gets SIM_ERROR instead of a dropped connection
        self.start_timeout_s = kw.get("start_timeout_s", 780)
        self.record_video = kw.get("record_video", False)
        python = kw.get("worker_python") or os.environ.get("ISAACLAB_PYTHON") or sys.executable
        self.worker_argv = kw.get("worker_argv") or [python, "-m", "env_service.worker"]
        self.log_dir = Path(kw.get("log_dir") or ROOT / "runs" / "env_service")


class Worker:
    """A worker process with a request/response pipe pair."""

    def __init__(self, cfg: Config, exp: "Exp"):
        cmd_r, cmd_w = os.pipe()
        resp_r, resp_w = os.pipe()
        log_dir = cfg.log_dir / exp.task["task_id"] / exp.exp_id      # <runs>/<task>/<run>: benchmark/evaluate.py layout
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = log_dir / "worker.log"
        argv = cfg.worker_argv + ["--task-id", exp.task["task_id"], "--catalog", str(exp.entry["catalog"]),
                                  "--profile", exp.entry["profile"]["path"], "--seed", str(exp.seed),
                                  "--out-dir", str(log_dir), "--cmd-fd", str(cmd_r), "--resp-fd", str(resp_w)]
        for k in ("variant", "difficulty"):
            if getattr(exp, k) is not None:
                argv += [f"--{k}", getattr(exp, k)]
        if cfg.record_video:
            argv += ["--video-path", str(log_dir / "run.mp4")]
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
            try:
                code = self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                code = None
            hint = " (killed: out of memory?)" if code == -9 else ""
            raise ServiceError(HTTPStatus.INTERNAL_SERVER_ERROR, "SIM_CRASHED",
                               f"simulator process exited (code {code}){hint}; see {self.log_path}")
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
    def __init__(self, exp_id, entry, variant=None, seed=0, difficulty=None, max_calls=40):
        self.exp_id, self.entry, self.task = exp_id, entry, entry["task"]
        self.variant, self.seed, self.difficulty, self.max_calls = variant, seed, difficulty, max_calls
        self.episode = None           # episode metadata from the worker (hashes, variant, profile)
        self.state = "starting"       # starting -> ready -> released
        self.worker: Worker | None = None
        self.lock = threading.Lock()  # one request at a time per simulator
        self.calls = 0
        self.ready_at = None
        self.last_activity = None
        self.release_reason = None


def load_registry(catalogs: dict) -> dict:
    """{task_id: {"task", "catalog", "profile"}} over every catalog; a task id must be unique."""
    out = {}
    for path, spec in catalogs.items():
        prof = load_profile(spec)
        prof["path"] = str(spec)
        for tid, task in load_catalog(path).items():
            if tid in out:
                raise ValueError(f"task {tid!r} is in both {out[tid]['catalog']} and {path}")
            out[tid] = {"task": task, "catalog": path, "profile": prof}
    return out


class ExpManager:
    def __init__(self, cfg: Config, tasks: dict):
        """``tasks``: load_registry(...)."""
        self.cfg, self.tasks = cfg, tasks
        self.exps: dict[str, Exp] = {}
        self.lock = threading.Lock()
        # one simulator starts at a time: a starting Isaac process peaks at ~11 GB of RAM
        self.start_lock = threading.Lock()
        self.running = 0              # starting or ready simulators
        self._stop = threading.Event()
        threading.Thread(target=self._reaper, daemon=True).start()

    # -- interface 1 ------------------------------------------------------------------
    def initial_task(self, body):
        """Start a simulator and block until it is ready (503 BUSY when none is free).
        ``variant`` / ``difficulty`` pick the condition (default: the seed picks one), ``seed`` the
        episode's random overlay (default 0); a task with one variant ignores both."""
        task_id = body.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ServiceError(HTTPStatus.BAD_REQUEST, "BAD_REQUEST", 'missing "task_id"')
        if task_id not in self.tasks:
            raise ServiceError(HTTPStatus.BAD_REQUEST, "UNKNOWN_TASK", f"no task {task_id!r}")
        entry = self.tasks[task_id]
        variant, seed, difficulty = body.get("variant"), body.get("seed", 0), body.get("difficulty")
        if variant is not None and variant not in entry["task"]["variants"]:
            raise ServiceError(HTTPStatus.BAD_REQUEST, "UNKNOWN_VARIANT",
                               f"task {task_id} has no variant {variant!r}")
        if difficulty is not None and difficulty not in ("easy", "medium", "hard"):
            raise ServiceError(HTTPStatus.BAD_REQUEST, "BAD_REQUEST", '"difficulty": easy, medium or hard')
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ServiceError(HTTPStatus.BAD_REQUEST, "BAD_REQUEST", '"seed" must be an integer')
        budget = self.cfg.max_calls or max_calls(entry["profile"], entry["task"])
        with self.lock:
            if self.running >= self.cfg.max_sims:
                raise ServiceError(HTTPStatus.SERVICE_UNAVAILABLE, "BUSY",
                                   f"{self.running} simulators are running (limit {self.cfg.max_sims}); retry later")
            exp = Exp(f"{task_id}-{uuid.uuid4().hex[:8]}", entry, variant, seed, difficulty, budget)
            self.exps[exp.exp_id] = exp
            self.running += 1
        deadline = time.time() + self.cfg.start_timeout_s
        try:
            if not self.start_lock.acquire(timeout=self.cfg.start_timeout_s):
                raise TimeoutError(f"another simulator was still starting after {self.cfg.start_timeout_s} s")
            try:
                exp.worker = Worker(self.cfg, exp)
                msg = _with_timeout(exp.worker.read, max(1.0, deadline - time.time()))
            finally:
                self.start_lock.release()
            if msg.get("type") != "ready":
                raise RuntimeError(msg.get("error", "simulator failed to start"))
        except Exception as exc:
            self._log(exp, f"start failed: {exc}")
            self.release(exp, "start_failed")
            raise ServiceError(HTTPStatus.INTERNAL_SERVER_ERROR, "SIM_ERROR", f"simulator failed to start: {exc}")
        with exp.lock:
            if exp.state != "starting":       # released (shutdown) meanwhile
                raise ServiceError(HTTPStatus.INTERNAL_SERVER_ERROR, "SIM_ERROR",
                                   f"exp released while starting ({exp.release_reason})")
            exp.state = "ready"
            # idle and duration limits count from the moment initial_task returns
            exp.ready_at = exp.last_activity = time.time()
            exp.episode = msg.get("episode")
        prof = entry["profile"]
        return {"exp_id": exp.exp_id, "task": public_task(exp.task),
                "profile": {"name": prof["name"], "observation": observation_fields(prof), "max_calls": exp.max_calls},
                "observation": msg["observation"]}

    def abandon(self, exp_id):
        """initial_task's answer could not be delivered: the planner never learns this exp_id."""
        exp = self.exps.get(exp_id)
        if exp is not None and exp.calls == 0:
            self.release(exp, "initial_task_undelivered")

    # -- interfaces 2 and 3 -------------------------------------------------------------
    def _ready(self, exp_id) -> Exp:
        exp = self.exps.get(exp_id)
        if exp is None:
            raise ServiceError(HTTPStatus.NOT_FOUND, "UNKNOWN_EXP", f"no exp {exp_id!r}")
        if exp.state == "released":
            raise ServiceError(HTTPStatus.GONE, "EXP_RELEASED", f"exp {exp_id} was released ({exp.release_reason})")
        if exp.state != "ready":              # still inside its initial_task call
            raise ServiceError(HTTPStatus.NOT_FOUND, "UNKNOWN_EXP", f"no exp {exp_id!r}")
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
        if exp.calls >= exp.max_calls:
            return f"this exp already ran {exp.calls} contract calls (limit {exp.max_calls})"
        if time.time() - exp.ready_at >= self.cfg.max_duration_s:
            return f"this exp has run for more than {self.cfg.max_duration_s // 60} minutes"
        return None

    def observe(self, exp_id):
        """Exp state without waiting: a running do_contract keeps the lock, so the answer is "running"."""
        exp = self.exps.get(exp_id)
        if exp is None or exp.state == "starting":
            raise ServiceError(HTTPStatus.NOT_FOUND, "UNKNOWN_EXP", f"no exp {exp_id!r}")
        out = {"exp_id": exp_id, "state": "released", "calls_used": exp.calls, "observation": None}
        if exp.state == "released" or not exp.lock.acquire(blocking=False):
            return out if exp.state == "released" else dict(out, state="running")
        try:
            if exp.state != "ready":
                return out
            try:
                obs = exp.worker.request("observe")["observation"]
            except ServiceError:
                self._release_locked(exp, "sim_crashed")
                raise
        finally:
            exp.lock.release()
        return dict(out, state="ready", calls_used=exp.calls, observation=obs)

    def check_task(self, exp_id):
        exp = self._ready(exp_id)
        with exp.lock:
            if exp.state != "ready":
                raise ServiceError(HTTPStatus.GONE, "EXP_RELEASED", f"exp {exp_id} was released ({exp.release_reason})")
            try:
                res = exp.worker.request("check")
            finally:
                self._release_locked(exp, "checked")
        return {"exp_id": exp_id, "success": res["success"], "goal": flat_goal(res["goal"]),
                "dropped": res.get("dropped", []), "episode": exp.episode}

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
        "/initial_task": manager.initial_task,
        "/do_contract": lambda body: manager.do_contract(_need(body, "exp_id"), body.get("calls")),
        "/check_task": lambda body: manager.check_task(_need(body, "exp_id")),
        "/observe": lambda body: manager.observe(_need(body, "exp_id")),
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
                payload = route(body)
            except ServiceError as exc:
                self._send(exc.status, {"error_code": exc.code, "error": str(exc)})
            except Exception as exc:
                traceback.print_exc()
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error_code": "INTERNAL_ERROR", "error": str(exc)})
            else:
                try:
                    self._send(HTTPStatus.OK, payload)
                except OSError:
                    if "exp_id" in payload and self.path.rstrip("/") == "/initial_task":
                        manager.abandon(payload["exp_id"])
                    raise

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
    ap.add_argument("--max-sims", type=int, default=2)
    ap.add_argument("--catalog", action="append", metavar="PATH=PROFILE",
                    help="task catalog and the profile (name or YAML path) its tasks run with; repeatable "
                         f"(default: {' '.join(f'{k}={v}' for k, v in DEFAULT_CATALOGS.items())})")
    ap.add_argument("--record-video", action="store_true",
                    help="stream a third-person debug video to each exp's directory (run.mp4)")
    ap.add_argument("--worker-python")
    ap.add_argument("--log-dir")
    args = ap.parse_args()
    catalogs = dict(c.split("=", 1) for c in args.catalog) if args.catalog else dict(DEFAULT_CATALOGS)
    cfg = Config(max_sims=args.max_sims, record_video=args.record_video, worker_python=args.worker_python,
                 log_dir=args.log_dir)
    manager = ExpManager(cfg, load_registry(catalogs))
    server = ThreadingHTTPServer((args.host, args.port), make_handler(manager))
    print(f"[env_service] listening on {args.host}:{args.port}, {cfg.max_sims} simulators, "
          f"{len(manager.tasks)} tasks from {', '.join(f'{k} ({v})' for k, v in catalogs.items())}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        manager.shutdown()


if __name__ == "__main__":
    main()
