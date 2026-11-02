"""Put a SkillRegistry in front of an Episode's Contract runner.

    from skill_ext import SkillRegistry
    from skill_ext.dispatch import install
    reg = SkillRegistry.default(); reg.load_dir("my_skills")
    install(ep, reg, track="open")            # ep: episode.episode.Episode

Built-in verbs go to the original runner unchanged (same GT policies, same gate, same feedback).
A user skill runs as: observation gate on its object arguments (gated profiles) -> declared
preconditions on GT -> executor -> declared effects on GT.  Its result is a
``zeno_skills.skill_runtime.SkillResult``, so ``Episode.public_result``, feedback masking and the
evaluation logs treat it like any other call.  In the Fixed-Skill track a user skill is an unknown
contract, exactly as before.
"""
from __future__ import annotations

from skill_ext.executors import Outcome
from skill_ext.predicates import evaluate_atoms

OBJECT_TYPES = {"object_ref", "container_ref", "tool_ref", "lid_ref", "receptacle_ref", "entity_ref"}


class SkillContext:
    """What an executor may use.  ``call`` runs any skill of the track through the same runner (so a
    nested built-in is gated and verified as a top-level one); ``observe`` returns only what the
    profile shows a planner, plus proprioception."""

    def __init__(self, runner, spec, instruction=""):
        self._runner, self.spec, self.instruction = runner, spec, instruction
        self.rig = runner.rig if spec.executor.get("privileged") else None
        self.trace: list[dict] = []

    def call(self, skill: str, args: dict) -> dict:
        res = self._runner.run(skill, dict(args), depth=self._runner._depth + 1)
        row = {"contract": skill, "args": dict(args), "success": bool(res.success), "error_code": res.error_code,
               "error": res.error}
        self.trace.append(row)
        return row

    def observe(self, fields=("robot", "proprio", "instruction"), args=None) -> dict:
        from skill_ext.actions import proprio
        rig, out = self._runner.rig, {}
        ep = self._runner.episode
        if ep is not None and ({"images", "robot", "visible_objects"} & set(fields)):
            full = ep.observation("base64" if "images" in fields else "path", tag=f"skill_{self.spec.name}") \
                if "images" in fields else {"robot": ep._robot(), **({"visible_objects": [
                    ep.observer.describe(n) for n in sorted(ep.observer.view)]} if ep.observer else {})}
            out.update({k: v for k, v in full.items() if k in fields})
        if "proprio" in fields:
            out["proprio"] = proprio(rig)
        if "instruction" in fields:
            out["instruction"] = self.instruction
        if self.rig is not None and args:             # privileged scripted baselines only
            st = rig.state()
            out["gt_objects"] = {v: st["objects"][v]["pos"] for v in args.values()
                                 if isinstance(v, str) and v in st["objects"]}
        return out

    def act(self, space: str, action: dict) -> dict:
        from skill_ext.actions import execute
        return execute(self._runner.rig, space, action, self.call)


class OpenSkillRunner:
    """Proxy with the Contract runner's interface (``contract``, ``run``, everything else delegated)."""

    def __init__(self, base, registry, track="open", episode=None, instruction=""):
        self._base, self.registry, self.track = base, registry, track
        self.episode, self.instruction = episode, instruction
        self._depth = 0
        self.user_calls: list[dict] = []

    def __getattr__(self, name):
        return getattr(self._base, name)

    def _user(self, key):
        if self.track != "open" or self.registry.has(key, "fixed"):
            return None
        return self.registry.get(key, "open") if self.registry.has(key, "open") else None

    def contract(self, key):
        try:
            return self._base.contract(key)
        except KeyError:
            spec = self._user(key)
            if spec is None:
                raise
            return {"verb": spec.name, "contract_id": f"user:{spec.name}", "skill_id": f"user:{spec.name}",
                    "inputs": spec.parameters, "action_predicate": {"name": spec.name,
                                                                    "arguments": list(spec.parameters)}}

    def run(self, key, args, depth=0):
        spec = self._user(key)
        if spec is None:
            return self._base.run(key, args, depth)
        return self._run_user(spec, dict(args), depth)

    # ---------------------------------------------------------------------------
    def _run_user(self, spec, args, depth):
        from zeno_skills.skill_runtime import ContractError, SkillResult, before_snapshot
        from zeno_skills.rig import SkillFailure
        rig = self._base.rig
        values = {}
        for slot, meta in spec.parameters.items():
            if args.get(slot) is not None:
                values[slot] = args[slot]
            elif "default" in meta:
                values[slot] = meta["default"]
            elif meta.get("required"):
                raise ContractError("INPUT_MISSING", f"{spec.name}: missing input {slot}")
            else:
                values[slot] = None
        unknown = set(args) - set(spec.parameters)
        if unknown:
            raise ContractError("INPUT_UNKNOWN", f"{spec.name}: unknown inputs {sorted(unknown)}")
        action = f"{spec.name}(" + ", ".join(f"{k}={v}" for k, v in values.items() if v is not None) + ")"
        res = SkillResult(f"user:{spec.name}", f"user:{spec.name}", action, False, spec.executor["type"],
                          [], [], [], {}, {})
        rig.log("user_skill_start", skill=spec.name, action=action, depth=depth)
        refusal = self._gate(spec, values)
        if refusal:
            res.error_code, res.error = refusal
            res.error = f"{res.error_code}: {res.error}"
            rig.log("gate_refused", action=action, code=res.error_code, depth=depth)
            return self._done(spec, res, depth)
        ctx_pred = {"before": before_snapshot(rig)}
        rows, failed = evaluate_atoms(rig, spec.preconditions, values, ctx_pred)
        res.preconditions = rows
        if failed:
            res.error_code, res.error = "PRECONDITION_FAILED", "; ".join(failed)
            return self._done(spec, res, depth)
        sctx = SkillContext(self, spec, self.instruction)
        self._depth, saved = depth, self._depth
        try:
            out = spec.runner.run(sctx, values)
        except SkillFailure as exc:
            out = Outcome(False, "POLICY_FAILED", str(exc))
        except Exception as exc:
            out = Outcome(False, "INTERNAL_ERROR", f"{type(exc).__name__}: {exc}")
        finally:
            self._depth = saved
        res.children = [dict(c, action=f"{c['contract']}(...)", preconditions=[], postconditions=[], children=[])
                        for c in sctx.trace]
        res.policy_steps = out.steps
        if not out.success:
            res.error_code, res.error = out.error_code or "POLICY_FAILED", out.error or "executor failed"
            return self._done(spec, res, depth)
        rig.step(30)
        rows, failed = evaluate_atoms(rig, spec.effects, values, ctx_pred)
        res.postconditions = rows
        if failed:
            res.error_code, res.error = "POSTCONDITION_FAILED", "; ".join(failed)
            return self._done(spec, res, depth)
        res.success, res.outputs = True, dict(out.outputs)
        return self._done(spec, res, depth)

    def _gate(self, spec, values):
        base = self._base
        obs = getattr(base, "obs", None)
        if obs is None or not getattr(base, "gate", False):
            return None
        from benchmark.observation import REFUSAL
        for slot, meta in spec.parameters.items():
            v = values.get(slot)
            names = v if meta.get("type") == "object_list" and isinstance(v, list) else \
                [v] if meta.get("type") in OBJECT_TYPES else []
            for n in names:
                if isinstance(n, str) and not obs.known(n):
                    return "NOT_OBSERVED", REFUSAL.format(name=n)
        return None

    def _done(self, spec, res, depth):
        self._base.rig.log("user_skill_end", skill=spec.name, success=res.success, error=res.error)
        self._base.trace.append(res.asdict())
        self.user_calls.append({"skill": spec.name, "success": res.success, "error_code": res.error_code,
                                "depth": depth})
        return res


def install(episode, registry, track="open", instruction=None):
    """Wrap ``episode.runner`` (idempotent).  Returns the proxy."""
    if isinstance(episode.runner, OpenSkillRunner):
        episode.runner.registry, episode.runner.track = registry, track
        return episode.runner
    episode.runner = OpenSkillRunner(episode.runner, registry, track, episode,
                                     instruction if instruction is not None else episode.task.get("instruction", ""))
    return episode.runner
