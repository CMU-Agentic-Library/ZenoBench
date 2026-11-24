"""Run baseline planners against env_service over HTTP: the model side and the simulator run in
different places (as Graph Manager does).  The simulator machine runs

    $ISAACLAB_PYTHON -m env_service.server --port 8800 --max-sims 2 \
        --catalog benchmark/v6/tasks.json=sticky/benchmark

and the planner side (any Python with the planner dependencies, no Isaac) runs

    SHIFT_MODEL=claude-opus-5-5 python -m baseline.run_http --server http://SIM_HOST:8800 \
        --policy baseline.react:ReAct --task T28_cup_to_bedside --variant <variant> --seed 10
    python -m baseline.run_http --server ... --policy baseline.react:ReAct \
        --batch benchmark/v6/batches/category_control.json --limit 3 --jobs 2

Every episode asks for ``--profile`` (default sticky/benchmark) and the profile's call budget; the
planner sees exactly the observation the service returns (images are saved next to the log and
handed over as paths).  Output per episode: <out>/<method>@<model>/<task>/s<seed>_<variant>/
config.json, calls.jsonl, result.json (score from check_task, planner_summary), images/.
An episode with a result.json is skipped, so a batch can be resumed.  Standard library only
(plus whatever the chosen model's SDK needs).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "baseline/runs"


class ServiceError(RuntimeError):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body}")
        self.status, self.body = status, body


def post(server, path, body, timeout=3600):
    req = urllib.request.Request(server.rstrip("/") + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ServiceError(e.code, e.read().decode(errors="replace")[:2000]) from None


def save_images(obs, img_dir: Path, counter: list, tag: str):
    """png_base64 images -> files; the planner gets {"camera", "path"} as in-process."""
    if not obs:
        return obs
    out = []
    for im in obs.get("images") or []:
        if "png_base64" in im:
            counter[0] += 1
            img_dir.mkdir(parents=True, exist_ok=True)
            suffix = im["camera"] + (f"_{im['overlay']}{im.get('view', '')}" if im.get("overlay") else "")
            p = img_dir / f"obs{counter[0]:03d}_{tag}_{suffix}.png"
            p.write_bytes(base64.b64decode(im["png_base64"]))
            im = {k: v for k, v in im.items() if k != "png_base64"} | {"path": str(p)}
        out.append(im)
    return dict(obs, images=out)


def code_version():
    def git(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"commit": git("rev-parse", "HEAD"), "dirty_files": len(git("status", "--short", "--", "baseline",
                                                                        "benchmark", "episode").splitlines())}


def run_dir(out_root, policy, model, job):
    method = policy.rsplit(":", 1)[-1]
    return Path(out_root) / f"{method}@{model}" / job["task"] / f"s{job['seed']}_{job['variant']}"


def write_report(path, report):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(report, indent=1, default=str))
    temp.replace(path)


def prepare_attempt(out, profile):
    result = out / "result.json"
    if result.is_file():
        saved = json.loads(result.read_text())
        if saved.get("profile") != profile:
            raise ValueError(f"{out} contains another observation profile; choose a separate --out")
        if not (saved.get("crash") or saved.get("check_error")):
            return saved
    out.mkdir(parents=True, exist_ok=True)
    previous = [out / name for name in ("config.json", "images", "calls.jsonl", "failed.json", "result.json")
                if (out / name).exists()]
    if previous:
        archive = out / "attempts" / str(time.time_ns())
        archive.mkdir(parents=True)
        for p in previous:
            shutil.move(str(p), archive / p.name)
    return None


def run_one(server, job, policy, profile, out_root, model, menu):
    from benchmark.planners import load_policy
    out = run_dir(out_root, policy, model, job)
    saved = prepare_attempt(out, profile)
    if saved is not None:
        return saved
    os.environ.setdefault("SHIFT_MODEL", model)
    report = {"task_id": job["task"], "variant": job["variant"], "seed": job["seed"], "policy": policy,
              "model": model, "profile": profile, "calls": [], "started": time.time()}
    counter, exp_id = [0], None
    calls_f = open(out / "calls.jsonl", "w")
    try:
        body = {"task_id": job["task"], "variant": job["variant"], "seed": job["seed"], "profile": profile}
        for k in range(120):                                   # BUSY: all simulators taken, wait for one
            try:
                init = post(server, "/initial_task", body)
                break
            except ServiceError as e:
                if e.status != 503:
                    raise
                time.sleep(30)
        else:
            raise RuntimeError("env_service stayed BUSY for an hour")
        exp_id = init["exp_id"]
        budget = int(init["profile"]["max_calls"])
        report.update(exp_id=exp_id, max_calls=budget, profile_info=init["profile"], task=init["task"],
                      episode=None)
        (out / "config.json").write_text(json.dumps({**{k: report[k] for k in (
            "task_id", "variant", "seed", "policy", "model", "profile", "exp_id", "max_calls")},
            "server": server, "code": code_version(), "task": init["task"],
            "started": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=1))
        obs = save_images(init["observation"], out / "images", counter, "initial")
        report["initial_observation"] = obs
        pol = load_policy(policy)
        pol.max_calls = budget                                 # the service's budget is the one that counts
        pol.reset(task_instruction=init["task"]["description"], skills=menu)
        report["stop_reason"] = "budget"
        for i in range(budget):
            t0 = time.time()
            act = pol.next_call(obs)
            planner_s = round(time.time() - t0, 2)
            if act is None:
                report["stop_reason"] = "planner_done"
                break
            t1 = time.time()
            resp = post(server, "/do_contract", {"exp_id": exp_id,
                                                 "calls": [{"contract": act["skill"], "args": act.get("args", {})}]})
            res = (resp.get("results") or [{}])[0]
            obs = save_images(resp.get("observation"), out / "images", counter, f"step{i}")
            row = {"index": i, "skill": act["skill"], "args": act.get("args", {}), "feedback": res,
                   "planner_note": act.get("note", ""), "planner_s": planner_s, "planner_usage": act.get("usage"),
                   "wall_s": round(time.time() - t1, 1)}
            report["calls"].append(row)
            calls_f.write(json.dumps(row, default=str) + "\n")
            calls_f.flush()
            print(f"[{job['task']} s{job['seed']}] {i} {act['skill']} "
                  f"{'OK' if res.get('success') else 'FAIL ' + str(res.get('error_code'))}", flush=True)
            if res.get("error_code") == "LIMIT_EXCEEDED":
                report["stop_reason"] = "service_limit"
                break
        if hasattr(pol, "summary"):
            report["planner_summary"] = pol.summary()
    except Exception as exc:                                    # noqa: BLE001 - recorded, the batch goes on
        report["crash"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print(f"[{job['task']} s{job['seed']}] CRASH {report['crash']}", flush=True)
    finally:
        calls_f.close()
        if exp_id is not None:
            try:
                chk = post(server, "/check_task", {"exp_id": exp_id})
                report.update(success=chk["success"], score=chk.get("score"), goal=chk.get("goal"),
                              dropped=chk.get("dropped"), episode=chk.get("episode"))
            except Exception as exc:                            # noqa: BLE001
                report["check_error"] = f"{type(exc).__name__}: {exc}"
        report["skill_calls"] = len(report["calls"])
        report["wall_s"] = round(time.time() - report["started"], 1)
        complete = exp_id is not None and "check_error" not in report and "crash" not in report
        write_report(out / ("result.json" if complete else "failed.json"), report)
        sc = report.get("score") or {}
        print(f"RESULT {job['task']} s{job['seed']} {job['variant']} score={sc.get('score')} tier={sc.get('tier')} "
              f"calls={report['skill_calls']} stop={report.get('stop_reason')}", flush=True)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", default=os.environ.get("SHIFT_ENV_SERVER", "http://localhost:8800"))
    ap.add_argument("--policy", required=True, help="module:Class, e.g. baseline.react:ReAct")
    ap.add_argument("--model", help="model name (default: SHIFT_MODEL or claude-opus-5-5)")
    ap.add_argument("--profile", default="sticky/benchmark")
    ap.add_argument("--task")
    ap.add_argument("--variant")
    ap.add_argument("--seed", type=int, default=10)
    ap.add_argument("--batch", help="JSON list of {task, variant, seed} (e.g. benchmark/v6/batches/category_*.json)")
    ap.add_argument("--only-tasks", help="comma-separated task ids to keep from --batch")
    ap.add_argument("--limit", type=int, help="first N episodes of the batch")
    ap.add_argument("--jobs", type=int, default=1, help="episodes at once (the service runs --max-sims simulators)")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    from baseline.vlm import load_env
    load_env()
    model = a.model or os.environ.get("SHIFT_MODEL", "claude-opus-5-5")
    os.environ["SHIFT_MODEL"] = model
    from baseline.base import default_menu
    menu = default_menu()
    if a.batch:
        jobs = [{"task": j["task"], "variant": j["variant"], "seed": j["seed"]} for j in json.loads(Path(a.batch).read_text())]
        if a.only_tasks:
            keep = set(a.only_tasks.split(","))
            jobs = [j for j in jobs if j["task"] in keep]
        jobs = jobs[:a.limit] if a.limit else jobs
    else:
        if not (a.task and a.variant):
            ap.error("--task and --variant (or --batch)")
        jobs = [{"task": a.task, "variant": a.variant, "seed": a.seed}]
    queue, lock = list(jobs), threading.Lock()

    def worker():
        while True:
            with lock:
                if not queue:
                    return
                job = queue.pop(0)
            run_one(a.server, job, a.policy, a.profile, a.out, model, menu)
    threads = [threading.Thread(target=worker) for _ in range(max(1, a.jobs))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
