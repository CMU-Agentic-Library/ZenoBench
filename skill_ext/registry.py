"""Skill Registry: the built-in SkillNodes (read-only) plus user skills loaded from SKILL.md files.

Built-ins come from contract_library/skill_contracts.json, the file the Contract runner executes, so the
registry describes exactly what runs.  They execute through the unchanged Contract runner and GT
policies (``executor.type == "builtin"``).  User skills are validated (skill_ext.schema), their
executors are loaded on registration (a broken entry fails at load time, not mid-episode), and they
can be added, replaced or removed while a process runs (``register`` / ``unregister`` / ``reload``).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from skill_ext.executors import make_executor
from skill_ext.schema import SkillSchemaError, validate_spec
from skill_ext.skill_md import SkillFileError, read_skill_md

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contract_library" / "skill_contracts.json"
TRACKS = ("fixed", "open")


@dataclass
class SkillSpec:
    name: str
    kind: str                       # "builtin" | "user"
    description: str
    parameters: dict
    preconditions: list
    effects: list
    executor: dict
    source: str = ""
    sha1: str = ""
    body: str = ""
    raw: dict = field(default_factory=dict, repr=False)
    runner: object = field(default=None, repr=False, compare=False)     # the loaded executor (user skills)

    @property
    def tracks(self) -> tuple[str, ...]:
        return TRACKS if self.kind == "builtin" else ("open",)

    def public(self) -> dict:
        """What a planner is told: never the executor, its entry, steps or source path."""
        return {"name": self.name, "kind": self.kind, "description": self.description,
                "parameters": {k: {kk: vv for kk, vv in v.items() if kk in ("type", "required", "description",
                                                                             "enum", "default")}
                               for k, v in self.parameters.items()},
                "preconditions": [_text(a) for a in self.preconditions],
                "effects": [_text(a) for a in self.effects]}


def _text(a):
    from skill_ext.schema import atom_text
    return atom_text(a)


class SkillRegistry:
    def __init__(self, builtins: dict[str, SkillSpec] | None = None):
        self._builtin = dict(builtins or {})
        self._user: dict[str, SkillSpec] = {}

    # -- construction ---------------------------------------------------------------
    @classmethod
    def default(cls, contracts=CONTRACTS) -> "SkillRegistry":
        doc = json.loads(Path(contracts).read_text())
        out = {}
        for c in doc["contracts"]:
            out[c["verb"]] = SkillSpec(
                name=c["verb"], kind="builtin", description=c.get("description", ""),
                parameters={k: {kk: vv for kk, vv in v.items() if kk != "attributes_from"} for k, v in c["inputs"].items()},
                preconditions=[{"pred": a["pred"], "args": dict(a.get("args", {})), "negated": bool(a.get("negated"))}
                               for a in c.get("requires", [])],
                effects=[{"pred": a["pred"], "args": dict(a.get("args", {})), "negated": bool(a.get("negated"))}
                         for a in c.get("ensures", [])],
                executor={"type": "builtin", "contract_id": c["contract_id"], "skill_id": c["skill_id"]},
                source=str(Path(contracts).relative_to(ROOT)) if Path(contracts).is_relative_to(ROOT) else str(contracts))
        return cls(out)

    @property
    def builtin_verbs(self) -> set[str]:
        return set(self._builtin)

    # -- user skills ----------------------------------------------------------------
    def register(self, path, *, replace=False) -> SkillSpec:
        """Load one SKILL.md (or its directory), validate it, load its executor, register it."""
        path = Path(path)
        md = path / "SKILL.md" if path.is_dir() else path
        try:
            raw, body, sha = read_skill_md(md)
        except SkillFileError as exc:
            raise SkillSchemaError(str(md), [str(exc)]) from None
        spec = validate_spec(raw, str(md), builtin_verbs=self.builtin_verbs)
        if spec["name"] in self._user and not replace:
            raise SkillSchemaError(str(md), [f"a user skill named {spec['name']!r} is already registered "
                                             f"({self._user[spec['name']].source})"])
        s = SkillSpec(name=spec["name"], kind="user", description=spec["description"],
                      parameters=spec.get("parameters", {}), preconditions=spec.get("preconditions", []),
                      effects=spec.get("effects", []), executor=spec["executor"], source=str(md), sha1=sha,
                      body=body, raw=raw)
        try:
            s.runner = make_executor(spec, md.parent)
        except Exception as exc:
            raise SkillSchemaError(str(md), [f"executor could not be loaded: {type(exc).__name__}: {exc}"]) from None
        self._user[s.name] = s
        return s

    def load_dir(self, root, *, strict=True) -> list[dict]:
        """Register every ``*/SKILL.md`` under ``root``.  ``strict``: raise on the first bad skill,
        else report it and go on.  Links between user skills are checked once all are loaded."""
        report = []
        for md in sorted(Path(root).glob("*/SKILL.md")):
            try:
                s = self.register(md.parent, replace=True)
                report.append({"skill": s.name, "source": str(md), "ok": True})
            except SkillSchemaError as exc:
                if strict:
                    raise
                report.append({"skill": None, "source": str(md), "ok": False, "errors": exc.errors})
        problems = self.check_links()
        if problems and strict:
            raise SkillSchemaError(str(root), problems)
        for p in problems:
            report.append({"skill": p.split(":", 1)[0], "ok": False, "errors": [p]})
        return report

    def unregister(self, name: str):
        if name in self._builtin:
            raise KeyError(f"{name!r} is a built-in skill; built-ins cannot be removed")
        self._user.pop(name)

    def reload(self, name: str) -> SkillSpec:
        return self.register(self._user[name].source, replace=True)

    def check_links(self) -> list[str]:
        """Every scripted step names a registered skill, and no user skill calls itself through others."""
        problems = []
        known = self.builtin_verbs | set(self._user)
        for s in self._user.values():
            for st in s.executor.get("steps", []):
                if st["skill"] not in known:
                    problems.append(f"{s.name}: step calls unknown skill {st['skill']!r}")

        def calls(n):
            return [st["skill"] for st in self._user[n].executor.get("steps", []) if st["skill"] in self._user]

        for n in self._user:
            seen, stack = set(), list(calls(n))
            while stack:
                m = stack.pop()
                if m == n:
                    problems.append(f"{n}: calls itself through other user skills")
                    break
                if m not in seen:
                    seen.add(m)
                    stack.extend(calls(m))
        return problems

    # -- lookup ---------------------------------------------------------------------
    def get(self, name: str, track: str = "open") -> SkillSpec:
        if track not in TRACKS:
            raise ValueError(f"track must be one of {TRACKS}")
        if name in self._builtin:
            return self._builtin[name]
        if track == "open" and name in self._user:
            return self._user[name]
        raise KeyError(name)

    def has(self, name, track="open") -> bool:
        try:
            self.get(name, track)
            return True
        except KeyError:
            return False

    def names(self, track: str = "open", kind: str | None = None) -> list[str]:
        out = list(self._builtin) + (list(self._user) if track == "open" else [])
        return sorted(n for n in out if kind is None or self.get(n, track).kind == kind)

    def menu(self, track: str = "open") -> list[dict]:
        return [self.get(n, track).public() for n in self.names(track)]

    def fingerprint(self, track: str = "open") -> str:
        """One hash for the skill set an episode ran with (recorded in config.json)."""
        h = hashlib.sha1(track.encode())
        h.update(hashlib.sha1(CONTRACTS.read_bytes()).hexdigest().encode())
        if track == "open":
            for n in sorted(self._user):
                h.update(f"{n}:{self._user[n].sha1}".encode())
        return h.hexdigest()[:12]
