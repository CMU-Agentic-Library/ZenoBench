"""Executors of user skills.

Every executor gets a ``SkillContext`` and the bound arguments and returns an ``Outcome``.  The
dispatcher (skill_ext.dispatch) checks the declared preconditions before and the declared effects
after, on GT state, exactly as the built-in Contracts do; the executor only acts.

* ``scripted``          - a fixed chain of skill calls (built-in or other user skills), ``$param`` bound.
* ``python``            - ``entry`` names a function ``f(ctx, **args)`` or a class with ``run(ctx, args)``.
* ``vla`` / ``rl`` / ``scripted_policy`` - ``entry`` names a policy class:

      class MyPolicy:
          def __init__(self, config: dict): ...
          def reset(self, instruction: str, args: dict): ...
          def act(self, observation: dict) -> dict: ...      # one action, or {"terminate": True}

  run for at most ``max_steps`` steps through the action interface (skill_ext.actions):
  ``ee_delta`` {"ee_delta": [dx, dy, dz], "gripper": "open" | "close" | width},
  ``joint_delta`` {"joint_delta": [7 values], "gripper": ...}, or
  ``skill_calls`` {"skill": verb, "args": {...}} (a high-level policy over skills).

  The observation holds only what the episode profile lets a planner see (images, robot, visible
  objects), plus ``proprio`` (TCP pose, finger gap, arm joints) and ``instruction``.  GT object poses
  are never in it unless the skill is ``privileged`` (a scripted baseline, off the Open-Skill board).
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Outcome:
    success: bool
    error_code: str | None = None
    error: str | None = None
    outputs: dict = field(default_factory=dict)
    steps: list = field(default_factory=list)          # what ran, for the log (never shown to the planner)


def load_entry(entry: str, base_dir: Path):
    """``file.py:Name`` relative to the skill directory, or ``package.module:Name``."""
    mod_ref, _, attr = entry.rpartition(":")
    if mod_ref.endswith(".py"):
        path = (Path(base_dir) / mod_ref).resolve()
        if not path.is_file():
            raise ImportError(f"executor entry {entry!r}: {path} not found")
        name = f"skill_ext_user.{path.parent.name}.{path.stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    else:
        mod = importlib.import_module(mod_ref)
    try:
        return getattr(mod, attr)
    except AttributeError:
        raise ImportError(f"executor entry {entry!r}: {attr!r} not defined") from None


def bind(value, args):
    if isinstance(value, str) and value.startswith("$"):
        return args.get(value[1:])
    if isinstance(value, list):
        return [bind(v, args) for v in value]
    if isinstance(value, dict):
        return {k: bind(v, args) for k, v in value.items()}
    return value


class Executor:
    def __init__(self, spec: dict, base_dir: Path):
        self.spec, self.base_dir, self.ex = spec, Path(base_dir), spec["executor"]

    def run(self, ctx, args: dict) -> Outcome:
        raise NotImplementedError


class ScriptedExecutor(Executor):
    def run(self, ctx, args):
        steps = []
        for i, st in enumerate(self.ex["steps"]):
            call_args = {k: v for k, v in bind(st.get("args", {}), args).items() if v is not None}
            res = ctx.call(st["skill"], call_args)
            steps.append({"skill": st["skill"], "args": call_args, "success": res["success"],
                          "error_code": res.get("error_code")})
            if not res["success"] and not st.get("optional"):
                return Outcome(False, "SUBSKILL_FAILED", f"step {i} {st['skill']} failed: {res.get('error')}",
                               steps=steps)
        return Outcome(True, steps=steps)


class PythonExecutor(Executor):
    def __init__(self, spec, base_dir):
        super().__init__(spec, base_dir)
        self.target = load_entry(self.ex["entry"], base_dir)

    def run(self, ctx, args):
        fn = self.target
        if isinstance(fn, type):
            obj = fn(self.ex.get("config", {}))
            out = obj.run(ctx, dict(args))
        else:
            out = fn(ctx, **args)
        return _as_outcome(out)


class PolicyExecutor(Executor):
    """VLA / RL / scripted policy: observation -> action, through skill_ext.actions."""

    def __init__(self, spec, base_dir):
        super().__init__(spec, base_dir)
        self.cls = load_entry(self.ex["entry"], base_dir)
        self.space = self.ex.get("action_space", "ee_delta")
        self.max_steps = int(self.ex.get("max_steps", 50))
        self.fields = tuple(self.ex.get("observation", ("robot", "proprio", "instruction")))

    def run(self, ctx, args):
        policy = self.cls(dict(self.ex.get("config", {}), base_dir=str(self.base_dir)))
        policy.reset(ctx.instruction, dict(args))
        steps = []
        for i in range(self.max_steps):
            obs = ctx.observe(self.fields, args)
            action = policy.act(obs) or {}
            if action.get("terminate"):
                steps.append({"step": i, "terminate": True})
                break
            fb = ctx.act(self.space, action)
            steps.append({"step": i, "action": _short(action), "ok": fb.get("ok", True)})
            if fb.get("fatal"):
                return Outcome(False, "POLICY_FAILED", fb.get("error", "action failed"), steps=steps)
        else:
            steps.append({"step": self.max_steps, "budget": True})
        return Outcome(True, outputs={"policy_steps": len(steps)}, steps=steps)


def _short(action):
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in action.items() if k != "debug"}


def _as_outcome(out) -> Outcome:
    if isinstance(out, Outcome):
        return out
    if isinstance(out, bool) or out is None:
        return Outcome(bool(out) if out is not None else True)
    if isinstance(out, dict):
        return Outcome(bool(out.get("success", True)), out.get("error_code"), out.get("error"),
                       dict(out.get("outputs", {})), list(out.get("steps", [])))
    raise TypeError(f"executor returned {type(out).__name__}; expected Outcome, dict or bool")


EXECUTORS = {"scripted": ScriptedExecutor, "python": PythonExecutor, "vla": PolicyExecutor,
             "rl": PolicyExecutor, "scripted_policy": PolicyExecutor}


def make_executor(spec: dict, base_dir) -> Executor:
    return EXECUTORS[spec["executor"]["type"]](spec, Path(base_dir))
