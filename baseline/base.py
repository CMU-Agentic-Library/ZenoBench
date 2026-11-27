"""What every baseline planner shares: the skill menu, the call history, VLM usage accounting.

Settings come from the environment, because run_episode builds the planner with no arguments:

* SHIFT_MODEL      - model name for baseline.vlm.make_client (default claude-opus-5-5)
* SHIFT_MAX_CALLS  - the call budget the planner is told (default 60, the benchmark budget)
"""

from __future__ import annotations

import os

from benchmark.planners import Planner

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_MAX_CALLS = 60


def default_menu():
    """The Fixed-track skill menu (71 verbs) when the runner passes none."""
    from skill_ext import SkillRegistry
    return SkillRegistry.default().menu("fixed")


class BaselinePlanner(Planner):
    name = "baseline"

    def __init__(self, model=None, max_calls=None, client=None):
        from baseline.vlm import load_env
        load_env()                        # SHIFT_MODEL / SHIFT_MAX_CALLS may live in baseline/.env
        self.model = model or os.environ.get("SHIFT_MODEL", DEFAULT_MODEL)
        self.max_calls = int(max_calls or os.environ.get("SHIFT_MAX_CALLS", DEFAULT_MAX_CALLS))
        self._client = client

    @property
    def client(self):
        if self._client is None:
            from baseline.vlm import make_client
            self._client = make_client(self.model)
        return self._client

    def reset(self, task_instruction, skills=None):
        self.instruction = task_instruction
        self.skills = list(skills) if skills else default_menu()
        self.skill_names = {s["name"] for s in self.skills}
        self.history = []                 # [{"skill", "args", "result"}], result filled from the next observation
        self.usage = {"vlm_queries": 0, "input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0,
                      "latency_s": 0.0, "parse_errors": 0}
        self.stop_reason = None
        self.trace = []                   # every VLM query since the last emitted call: prompt, raw answer, usage
        self.system_logged = None

    def observe(self, obs):
        """Attach the last call's result (the observation's last_result) to the history."""
        if self.history and "result" not in self.history[-1]:
            self.history[-1]["result"] = obs.get("last_result")

    def ask(self, system, user, images=(), tools=None):
        text, u = self.client.chat(system, user, images, **({"tools": tools} if tools else {}))
        q = {"user": user, "images": [str(i) for i in images], "answer": text, "usage": u}
        if tools:
            q["tools"] = [t["function"]["name"] for t in tools]
        if system != self.system_logged:  # the system prompt is logged once, and again whenever it changes
            q["system"], self.system_logged = system, system
        self.trace.append(q)
        self.usage["vlm_queries"] += 1
        for k in ("input_tokens", "output_tokens", "cached_input_tokens"):
            self.usage[k] += int(u.get(k) or 0)
        self.usage["latency_s"] = round(self.usage["latency_s"] + float(u.get("latency_s") or 0), 2)
        return text, u

    def emit(self, call, note="", usage=None):
        self.history.append({"skill": call["skill"], "args": call.get("args", {})})
        trace, self.trace = self.trace, []
        return {"skill": call["skill"], "args": call.get("args", {}), "note": note, "usage": usage, "trace": trace}

    def tools_for(self, observation):
        """The menu as constrained tools when the backend decodes them (local vLLM), else None."""
        if not getattr(self.client, "native_tools", False):
            return None
        from baseline.tools import tool_schemas
        return tool_schemas(self.skills, observation)

    def summary(self) -> dict:
        """Written to result.json["planner"] by run_episode (totals include the finishing query)."""
        return {"name": self.name, "model": self.model, "max_calls": self.max_calls,
                "stop_reason": self.stop_reason, **self.usage,
                "final_trace": getattr(self, "trace", [])}   # queries after the last call (finish, parse errors)
