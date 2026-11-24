"""Shared: the v6 catalog before the 11-24 loosening (built once per test session)."""
from __future__ import annotations

import functools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


@functools.lru_cache(maxsize=1)
def pre_loosen() -> dict:
    """benchmark/v6/tasks.json as define_tasks_v6 builds it before loosen_1124 (the reviewed designs as written)."""
    from benchmark.v6.define_tasks_v6 import build
    return build(loosen=False)
