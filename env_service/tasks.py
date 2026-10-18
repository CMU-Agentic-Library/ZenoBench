"""Task catalog access shared by the server and the worker (no simulator imports)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "skill_library" / "tasks.json"


def load_tasks(path=CATALOG) -> dict[str, dict]:
    return {t["id"]: t for t in json.loads(Path(path).read_text())["tasks"]}


def public_task(task: dict) -> dict:
    """What the planner is told about a task: its name and content, never the goal."""
    return {"task_id": task["id"], "name": task["id"], "description": task["description"]}


def atom_text(atom) -> str:
    return f"{atom[0]}({', '.join(map(str, atom[1:]))})"
