"""Load the exported SkillNode catalog (``catalog.json`` + every ``skill.json``)."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text())


def load_skills(library_dir: str | Path = HERE) -> dict[str, dict]:
    """skill_id -> exported skill.json."""
    root = Path(library_dir)
    index = read_json(root / "catalog.json")
    if index.get("schema_version") != 2 or index.get("kind") != "skill_catalog":
        raise ValueError("catalog must be a schema_version 2 skill_catalog")
    skills = {}
    for entry in index["skills"]:
        spec = read_json(root / entry["definition"])
        skills[spec["skill_id"]] = spec
    if len({s["verb"] for s in skills.values()}) != len(skills):
        raise ValueError("verbs must be unique")
    return skills
