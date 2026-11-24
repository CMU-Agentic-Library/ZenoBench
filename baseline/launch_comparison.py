"""Dispatch the paired local model matrix across loopback simulation services."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
from pathlib import Path
import signal
import subprocess
import sys
from threading import Event, Lock

from baseline.comparison import ABLATIONS, METHODS, MODELS, episodes, representatives, result_path


def pending(out, first_row=0):
    jobs = episodes()
    subset = representatives(jobs)
    for index in range(first_row, len(jobs)):
        for method in METHODS:
            rows = subset if method in ABLATIONS else jobs
            if index >= len(rows):
                continue
            for model in MODELS:
                if not (result_path(out, model, method, rows[index]) / "result.json").exists():
                    yield model, method, index, len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, required=True, help="contains native/ and planner/")
    ap.add_argument("--sim-version", required=True)
    ap.add_argument("--servers", nargs="+", required=True, metavar="PORT=SLOTS")
    ap.add_argument("--vlm-ports", nargs=3, type=int, default=(8101, 8102, 8103),
                    help="Qwen 4B, Qwen 27B, InternVL 8B")
    ap.add_argument("--graph-bin", default="graph-manager-run")
    ap.add_argument("--first-row", type=int, default=0,
                    help="start at this zero-based index when earlier rows are dispatched separately")
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
    logs = root / "dispatch"
    logs.mkdir(parents=True, exist_ok=True)
    out = root / "planner"
    jobs = pending(out, args.first_row)
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
                model, method, index, total = job
                cmd = [sys.executable, "-m", "baseline.comparison", "--model", model, "--method", method,
                       "--shards", str(total), "--shard", str(index), "--out", str(out),
                       "--native-dir", str(root / "native"), "--sim-version", args.sim_version,
                       "--vlm-url", f"http://127.0.0.1:{endpoints[model]}/v1",
                       "--server", f"http://127.0.0.1:{port}", "--graph-bin", args.graph_bin]
                print(f"START {model} {method} [{index}/{total}] sim={port}", file=log)
                rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
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
