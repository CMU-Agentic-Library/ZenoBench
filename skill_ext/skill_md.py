"""Read a user skill's SKILL.md: YAML front matter (the spec) + Markdown body (documentation)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


class SkillFileError(ValueError):
    pass


def split_front_matter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillFileError("SKILL.md must start with a '---' YAML front-matter block")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise SkillFileError("SKILL.md front matter is not closed by '---'") from None
    try:
        spec = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError as exc:
        raise SkillFileError(f"front matter is not valid YAML: {exc}") from None
    if not isinstance(spec, dict):
        raise SkillFileError("front matter must be a mapping")
    return spec, "\n".join(lines[end + 1:]).strip()


def read_skill_md(path) -> tuple[dict, str, str]:
    """(spec, body, sha1 of the file)."""
    path = Path(path)
    if path.is_dir():
        path = path / "SKILL.md"
    if not path.exists():
        raise SkillFileError(f"{path}: no SKILL.md")
    text = path.read_text()
    spec, body = split_front_matter(text)
    return spec, body, hashlib.sha1(text.encode()).hexdigest()[:12]
