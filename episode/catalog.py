"""Task catalogs in one shape.

Two catalog formats exist:

* ``skill_library/tasks.json`` (the original tasks): one prebuilt scene per task,
  ``goal`` a list of atoms, ``entities``, ``description``;
* ``benchmark/tasks.json`` / ``benchmark/v3/tasks.json``: a base scene plus an overlay,
  condition ``variants``, ``goal`` {"all", "any"}, ``instruction``, ``routes``.

``load_catalog`` returns every task in the benchmark shape.  An original task becomes a
task with a single variant ``default`` and an empty overlay on its own scene directory
(the seed then changes nothing); its skill subgraph (``skill_library/plans``) becomes the
``nominal`` route and the oracle route of that variant.

Standard library only (the HTTP server reads catalogs with any Python 3).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = "skill_library/tasks.json"
DEFAULT_VARIANT = "default"
# catalog -> the profile its tasks run with unless the caller names another
DEFAULT_CATALOGS = {LEGACY: "gt", "benchmark/v3/tasks.json": "benchmark"}


def load_catalog(path) -> dict[str, dict]:
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    doc = json.loads(path.read_text())
    tasks = doc["tasks"]
    if tasks and "task_id" not in tasks[0]:
        return {t["id"]: legacy_task(t) for t in tasks}
    return {t["task_id"]: dict(t, catalog_kind="benchmark") for t in tasks}


def legacy_task(t: dict) -> dict:
    """An original task in the benchmark shape."""
    plan = ROOT / "skill_library/plans" / f"{t['id']}.skill_subgraph.json"
    routes, oracle = {}, {}
    if plan.exists():
        steps = [{"skill": n["skill"], "args": {k: v["value"] for k, v in n["args"].items()}}
                 for n in json.loads(plan.read_text())["nodes"]]
        routes["nominal"] = {"kind": "nominal", "variants": [DEFAULT_VARIANT], "steps": steps,
                             "source": str(plan.relative_to(ROOT))}
        oracle[DEFAULT_VARIANT] = "nominal"
    return {
        "task_id": t["id"],
        "exp_id": t["id"],
        "catalog_kind": "legacy",
        "source": [LEGACY],
        "instruction": t["description"],
        "scene": {"base": str(Path(t["task_json"]).parent)},
        "variants": {DEFAULT_VARIANT: {"note": "the task's own scene, no overlay"}},
        "goal": {"all": [list(a) for a in t["goal"]]},
        "entities": list(t["entities"]),
        "watch": list(t["entities"]),       # non-objects (supports) are skipped where watch is read
        "nominal": "nominal" if routes else None,
        "routes": routes,
        "oracle": oracle,
    }


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
