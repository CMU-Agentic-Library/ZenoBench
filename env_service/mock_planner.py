"""A stand-in planner for end-to-end tests of the environment service.

    python -m env_service.mock_planner --service http://127.0.0.1:8800 --listen 127.0.0.1:8801 \\
        --task collect_fruits [hide_block ...] [--out DIR]

It serves the callback endpoint, starts each task, replays its skill subgraph
(``skill_library/plans/<task>.skill_subgraph.json``) as contract calls and checks
the task; several tasks run concurrently.  Consecutive nodes go in one ``do_contract``
request; a node that needs an earlier node's output (``{"from": "n3.key"}``)
starts a new request once that output is back.  Start the service with
``--callback-url http://<listen>/callback``.  Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from env_service.tasks import ROOT


def post(url, body, timeout=1800):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"http_status": e.code, **json.loads(e.read())}


class Inbox:
    """Callback payloads by exp_id (a push may arrive before initial_task has returned)."""

    def __init__(self):
        self.items, self.cond = {}, threading.Condition()

    def put(self, payload):
        with self.cond:
            self.items[payload["exp_id"]] = payload
            self.cond.notify_all()

    def get(self, exp_id):
        with self.cond:
            self.cond.wait_for(lambda: exp_id in self.items)
            return self.items.pop(exp_id)


def callback_server(listen):
    host, port = listen.rsplit(":", 1)
    inbox = Inbox()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            inbox.put(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *a):
            pass
    server = ThreadingHTTPServer((host, int(port)), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return inbox


def batches(graph):
    """Plan nodes as do_contract batches; a ``from`` argument waits for its source's output."""
    batch, ids = [], set()
    for n in graph["nodes"]:
        sources = {v["from"].split(".", 1)[0] for v in n["args"].values() if "from" in v}
        if sources & ids:
            yield batch
            batch, ids = [], set()
        batch.append(n)
        ids.add(n["id"])
    if batch:
        yield batch


def save_images(obs, out: Path, tag):
    for img in obs.get("images", []):
        if img.get("png_base64"):
            (out / f"{tag}_{img['camera']}.png").write_bytes(base64.b64decode(img["png_base64"]))


def run_task(service, task, inbox, out: Path):
    graph = json.loads((ROOT / f"skill_library/plans/{task}.skill_subgraph.json").read_text())
    out.mkdir(parents=True, exist_ok=True)

    def log(text):
        print(f"[{task}] {text}", flush=True)

    t0 = time.time()
    exp_id = post(f"{service}/initial_task", {"task_id": task})["exp_id"]
    log(f"initial_task -> {exp_id} ({time.time() - t0:.2f} s)")
    push = inbox.get(exp_id)
    log(f"callback {push['status']} after {time.time() - t0:.0f} s: {push['task']}")
    if push["status"] != "ready":
        log(push.get("error"))
        return False
    obs = push["observation"]
    save_images(obs, out, "00_start")
    log("objects: " + json.dumps(obs["objects"]))
    log("task_status: " + json.dumps(obs["task_status"]))
    report = {"exp_id": exp_id, "callback": {k: v for k, v in push.items() if k != "observation"}, "requests": []}
    outputs, failed = {}, False
    for i, batch in enumerate(batches(graph), 1):
        calls = [{"contract": n["skill"], "args": {k: (outputs.get(v["from"].split(".")[0], {}).get(v["from"].split(".", 1)[1])
                                                       if "from" in v else next(iter(v.values())))
                                                   for k, v in n["args"].items()}} for n in batch]
        t1 = time.time()
        body = post(f"{service}/do_contract", {"exp_id": exp_id, "calls": calls})
        if "results" not in body:
            log(f"do_contract error: {body}")
            failed = True
            break
        save_images(body["observation"], out, f"{i:02d}")
        report["requests"].append({"calls": calls, "results": body["results"],
                                   "task_status": body["observation"]["task_status"],
                                   "wall_s": round(time.time() - t1, 1)})
        for n, r in zip(batch, body["results"]):
            log(f"  {'OK ' if r['success'] else 'FAIL'} {r['contract']}({r['args']}) "
                f"{r['error_code'] or ''} {r['error'] or ''}")
            outputs[n["id"]] = r["outputs"]
        if len(body["results"]) < len(calls) or not body["results"][-1]["success"]:
            failed = True
            break
    check = post(f"{service}/check_task", {"exp_id": exp_id})
    report["check"] = check
    report["wall_s"] = round(time.time() - t0, 1)
    (out / "report.json").write_text(json.dumps(report, indent=1))
    log(f"check_task -> {check} ({'plan failed' if failed else 'plan done'}, {report['wall_s']} s)")
    return bool(check.get("success"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--service", default="http://127.0.0.1:8800")
    ap.add_argument("--listen", default="127.0.0.1:8801")
    ap.add_argument("--task", nargs="+", required=True)
    ap.add_argument("--out", default=str(ROOT / "runs/env_service/mock_planner"))
    args = ap.parse_args()
    inbox = callback_server(args.listen)
    ok = {}
    threads = [threading.Thread(target=lambda t=t: ok.__setitem__(t, run_task(args.service, t, inbox, Path(args.out) / t)))
               for t in args.task]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    print("summary:", {t: ok.get(t) for t in args.task})
    return 0 if all(ok.get(t) for t in args.task) else 1


if __name__ == "__main__":
    sys.exit(main())
