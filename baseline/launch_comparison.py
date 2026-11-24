"""Dispatch the paired local model matrix across loopback simulation services."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import fcntl
from pathlib import Path
import signal
import subprocess
import sys
from threading import Event, Lock

from baseline.comparison import ABLATIONS, METHODS, MODELS, episodes, representatives, result_is_current, result_path


def pending(out, first_row=0, models=MODELS, methods=METHODS, first_layout_per_task=False):
    jobs = episodes()
    subset = representatives(jobs)
    first = {}
    if first_layout_per_task:
        for job in jobs:
            first.setdefault(job["task"], job)
    for index in range(first_row, len(jobs)):
        for method in methods:
            rows = subset if method in ABLATIONS else jobs
            if index >= len(rows):
                continue
            row = rows[index]
            if first_layout_per_task and row != first[row["task"]]:
                continue
            for model in models:
                directory = result_path(out, model, method, row)
                if not result_is_current(directory, model, method):
                    yield model, method, index, len(rows), directory


@contextmanager
def claim_episode(directory, model=None, method=None):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".dispatch.lock").open("a") as claim:
        try:
            fcntl.flock(claim, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield None
            return
        yield None if result_is_current(directory, model, method) else claim


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, required=True, help="contains native/ and planner/")
    ap.add_argument("--sim-version", required=True)
    ap.add_argument("--servers", nargs="+", required=True, metavar="PORT=SLOTS")
    ap.add_argument("--dispatch-dir", type=Path,
                    help="per-dispatcher log directory when adding concurrent workers to the same run")
    ap.add_argument("--model", choices=MODELS, action="append", help="limit this worker group to the named model(s)")
    ap.add_argument("--method", choices=METHODS, action="append", help="limit this worker group to the named method(s)")
    ap.add_argument("--vlm-ports", nargs=3, type=int, default=(8101, 8102, 8103),
                    help="Qwen 4B, Qwen 27B, InternVL 8B")
    ap.add_argument("--graph-bin", default="graph-manager-run")
    ap.add_argument("--first-row", type=int, default=0,
                    help="start at this zero-based index when earlier rows are dispatched separately")
    ap.add_argument("--first-layout-per-task", action="store_true",
                    help="run only the first declared episode of each task, retaining its full-batch shard index")
    args = ap.parse_args()
    if not 0 <= args.first_row < len(episodes()):
        ap.error("--first-row must be a valid main-batch index")
    slots = []
    for spec in args.servers:
        port, count = map(int, spec.split("="))
        if count < 1:
            ap.error(f"slot count must be positive in {spec}")
        slots.extend([port] * count)
    endpoints = dict(zip(MODELS, args.vlm_ports))
    root = args.run_dir.resolve()
    logs = args.dispatch_dir.resolve() if args.dispatch_dir else root / "dispatch"
    logs.mkdir(parents=True, exist_ok=True)
    out = root / "planner"
    jobs = pending(out, args.first_row, args.model or MODELS, args.method or METHODS, args.first_layout_per_task)
    # A stopped dispatcher drains active episodes. A restart scans receipts again.
    stop = Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    lock = Lock()
    interrupted = set()

    def work(slot, port):
        with (logs / f"slot-{slot}.log").open("a", buffering=1) as log:
            while not stop.is_set():
                with lock:
                    job = next((j for j in jobs if j[:2] not in interrupted), None)
                if job is None:
                    return
                model, method, index, total, directory = job
                cmd = [sys.executable, "-m", "baseline.comparison", "--model", model, "--method", method,
                       "--shards", str(total), "--shard", str(index), "--out", str(out),
                       "--native-dir", str(root / "native"), "--sim-version", args.sim_version,
                       "--vlm-url", f"http://127.0.0.1:{endpoints[model]}/v1",
                       "--server", f"http://127.0.0.1:{port}", "--graph-bin", args.graph_bin]
                with claim_episode(directory, model, method) as claim:
                    if claim is None:
                        continue
                    print(f"START {model} {method} [{index}/{total}] sim={port}", file=log)
                    # The running child keeps the episode locked even if its dispatcher exits.
                    rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT,
                                        pass_fds=(claim.fileno(),)).returncode
                print(f"EXIT {rc} {model} {method} [{index}/{total}]", file=log)
                if rc:
                    # Preserve the first infrastructure failure and continue unrelated cells.
                    with lock:
                        interrupted.add((model, method))
                    print(f"{model} {method} interrupted; see {log.name}", flush=True)

    with (logs / "campaign.lock").open("a") as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with ThreadPoolExecutor(max_workers=len(slots)) as pool:
            futures = [pool.submit(work, slot, port) for slot, port in enumerate(slots)]
            for future in futures:
                future.result()
    if interrupted or stop.is_set():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
