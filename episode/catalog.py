"""Task catalogs.

Every catalog is a JSON file ``{"schema_version", "kind", "tasks": [...]}`` whose tasks share one
shape: ``task_id``, ``instruction``, ``scene`` (a base scene directory plus an optional overlay),
``variants``, ``goal`` {"all", "any"} of GT predicate atoms, ``routes`` / ``nominal`` / ``oracle``
and ``watch``.  Two catalogs exist:

* ``skill_library/tasks.json``: one task per SkillNode family on a built scene, a single variant
  ``default`` (no overlay; the seed changes nothing), the planner subgraph as route ``nominal``;
* ``benchmark/tasks.json`` / ``benchmark/v3/tasks.json``: condition variants, declared routes.

Standard library only (the HTTP server reads catalogs with any Python 3).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# catalog -> the profile its tasks run with unless the caller names another
DEFAULT_CATALOGS = {"skill_library/tasks.json": "gt", "benchmark/v3/tasks.json": "benchmark"}


def load_catalog(path) -> dict[str, dict]:
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    doc = json.loads(path.read_text())
    return {t["task_id"]: dict(t, catalog_kind=doc.get("kind")) for t in doc["tasks"]}


def public_task(task: dict) -> dict:
    """What the planner is told about a task: its name and instruction, never the goal or the variant."""
    return {"task_id": task["task_id"], "name": task["task_id"], "description": task["instruction"]}


def entities(task: dict) -> list[str]:
    """The task's relevant names (the GT ``objects`` observation)."""
    return list(task.get("entities") or task.get("watch") or [])


def atom_text(atom) -> str:
    return f"{atom[0]}({', '.join(map(str, atom[1:]))})"


def base_sha1(base: str) -> str:
    """Content hash of the base scene files an episode is built from."""
    h = hashlib.sha1()
    for name in ("scene.usd", "annotation.json", "task.json"):
        f = ROOT / base / name
        h.update(name.encode())
        h.update(f.read_bytes() if f.exists() else b"")
    return h.hexdigest()[:12]


def episode_hash(scene_hash: str, profile_hash: str, base_hash: str) -> str:
    """One episode configuration: the scene overlay (``config_hash``), the base scene files and the profile.
    Two runs with one episode hash are repeats of the same episode."""
    return hashlib.sha1(f"{scene_hash}:{base_hash}:{profile_hash}".encode()).hexdigest()[:12]
