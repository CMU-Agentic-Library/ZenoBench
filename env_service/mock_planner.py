"""A stand-in planner for end-to-end tests of the environment service.

    python -m env_service.mock_planner --service http://127.0.0.1:8800 \\
        --task collect_fruits [hide_block ...] [--out DIR]

It starts each task, replays a known plan as contract calls and checks the task;
several tasks run concurrently, and a task that gets 503 BUSY retries until a
simulator is free.  The plan of an original task is its skill subgraph
(``skill_library/plans/<task>.skill_subgraph.json``); a benchmark task needs
``--variant`` and replays the route the catalog maps that variant to, including
its expected failures (sent alone; the route goes on when they fail).
Consecutive nodes go in one ``do_contract`` request; a node that needs an
earlier node's output (``{"from": "n3.key"}``) starts a new request once that
output is back.  Standard library only.

    python -m env_service.mock_planner --task T01_book_to_dining_table --variant no_overhang --seed 10
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
from pathlib import Path

from episode.catalog import DEFAULT_CATALOGS, ROOT, load_catalog


def post(url, body, timeout=1800):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"http_status": e.code, **json.loads(e.read())}


def batches(graph):
    """Plan nodes as do_contract batches; a ``from`` argument waits for its source's output, and
    a node expected to fail goes alone."""
    batch, ids = [], set()
    for n in graph["nodes"]:
        sources = {v["from"].split(".", 1)[0] for v in n["args"].values() if "from" in v}
        if sources & ids or (batch and n.get("expect") == "fail"):
            yield batch
            batch, ids = [], set()
        batch.append(n)
        ids.add(n["id"])
        if n.get("expect") == "fail":
            yield batch
            batch, ids = [], set()
    if batch:
        yield batch


def load_plan(task, variant):
    """The skill subgraph of an original task, or the route a benchmark task maps ``variant`` to."""
    plan = ROOT / f"skill_library/plans/{task}.skill_subgraph.json"
    if plan.exists():
        return json.loads(plan.read_text())
    for path in DEFAULT_CATALOGS:
        t = load_catalog(path).get(task)
        if t is None:
            continue
        if variant is None:
            raise SystemExit(f"{task}: --variant is required (one of {sorted(t['variants'])})")
        steps = t["routes"][t["oracle"][variant]]["steps"]
        return {"nodes": [{"id": f"n{i}", "skill": st["skill"], "expect": st.get("expect", "ok"),
                           "args": {k: {"value": v} for k, v in st.get("args", {}).items()}}
                          for i, st in enumerate(steps, 1)]}
    raise SystemExit(f"no plan for task {task!r}")


def save_images(obs, out: Path, tag):
    for img in obs.get("images", []):
        if img.get("png_base64"):
            (out / f"{tag}_{img['camera']}.png").write_bytes(base64.b64decode(img["png_base64"]))


def run_task(service, task, out: Path, retry_s=30, variant=None, seed=0):
    graph = load_plan(task, variant)
    out.mkdir(parents=True, exist_ok=True)

    def log(text):
        print(f"[{task}] {text}", flush=True)

    t0 = time.time()
    while True:
        start = post(f"{service}/initial_task", {"task_id": task, "seed": seed,
                                                 **({"variant": variant} if variant else {})}, timeout=900)
        if start.get("error_code") != "BUSY":
            break
        time.sleep(retry_s)
    if "exp_id" not in start:
        log(f"initial_task error after {time.time() - t0:.0f} s: {start}")
        return False
    exp_id = start["exp_id"]
    log(f"initial_task -> {exp_id} after {time.time() - t0:.0f} s: {start['task']} profile {start.get('profile')}")
    obs = start["observation"]
    save_images(obs, out, "00_start")
    for key in ("objects", "visible_objects", "task_status"):
        if key in obs:
            log(f"{key}: " + json.dumps([o.get("name", o) if isinstance(o, dict) and "name" in o else o
                                         for o in obs[key]]))
    report = {"exp_id": exp_id, "task": start["task"], "requests": []}
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
                                   "task_status": body["observation"].get("task_status"),
                                   "wall_s": round(time.time() - t1, 1)})
        for n, r in zip(batch, body["results"]):
            expect = n.get("expect", "ok")
            log(f"  {'OK ' if r['success'] else 'FAIL'} {r['contract']}({r['args']}) "
                f"{r['error_code'] or ''} {r['error'] or ''}" + (" (expected to fail)" if expect == "fail" else ""))
            outputs[n["id"]] = r["outputs"]
        last = body["results"][-1]
        if len(body["results"]) < len(calls) or last["success"] != (batch[-1].get("expect", "ok") != "fail"):
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
    ap.add_argument("--task", nargs="+", required=True)
    ap.add_argument("--variant", help="benchmark tasks: the condition (the same for every --task)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(ROOT / "runs/env_service/mock_planner"))
    args = ap.parse_args()
    ok = {}
    threads = [threading.Thread(target=lambda t=t: ok.__setitem__(
        t, run_task(args.service, t, Path(args.out) / t, variant=args.variant, seed=args.seed))) for t in args.task]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    print("summary:", {t: ok.get(t) for t in args.task})
    return 0 if all(ok.get(t) for t in args.task) else 1


if __name__ == "__main__":
    sys.exit(main())
