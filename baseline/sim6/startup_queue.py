"""Queue loopback environment startups before the simulation server begins its startup timeout."""

import fcntl
from functools import wraps
from pathlib import Path
import urllib.request


def install(directory, port_to_gpu):
    """Install in a dedicated planner interpreter before its environment clients are imported."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    locks = {f"http://127.0.0.1:{port}/initial_task": directory / f"gpu-{gpu}.lock"
             for port, gpu in port_to_gpu.items()}
    original = getattr(urllib.request.urlopen, "_zenobench_unqueued", urllib.request.urlopen)

    @wraps(original)
    def queued(url, *args, **kwargs):
        path = locks.get(getattr(url, "full_url", None))
        if path is None or url.get_method() != "POST":
            return original(url, *args, **kwargs)
        with path.open("a") as slot:
            fcntl.flock(slot, fcntl.LOCK_EX)
            return original(url, *args, **kwargs)

    queued._zenobench_unqueued = original
    urllib.request.urlopen = queued
