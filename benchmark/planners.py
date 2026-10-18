"""Planner entry points for the evaluation (no VLM planner is implemented here).

All planners act through LimitedSession (observation-limited, no automatic
recovery) except the GT oracle, which run_episode executes with the original
GT runner.

* fixed     - run_episode --planner fixed: the nominal plan, stop at the first failure
* retry     - run_episode --planner retry: the nominal plan, repeat a failed call up to 2 times
* recovery  - run_episode --planner recovery --policy module:Class: a closed-loop Planner
* oracle    - run_episode --planner oracle: GT runner + the route that fits the variant

A recovery planner implements::

    class MyPlanner(Planner):
        def reset(self, task_instruction, skills=None): ...
        def next_call(self, observation) -> {"skill": str, "args": dict} | None

``observation`` is LimitedSession.observe(): first-person image path, visible
objects, observation cache, known static places, robot state and the last
call's feedback.
"""

from __future__ import annotations

import importlib


class Planner:
    def reset(self, task_instruction, skills=None):
        self.instruction = task_instruction

    def next_call(self, observation):
        raise NotImplementedError


class ReplayPlanner(Planner):
    """Replays a fixed call list (debugging the closed loop)."""

    def __init__(self, calls):
        self.calls = list(calls)

    def next_call(self, observation):
        return self.calls.pop(0) if self.calls else None


def load_policy(spec):
    if not spec or ":" not in spec:
        raise ValueError("--policy module:Class")
    mod, cls = spec.split(":", 1)
    return getattr(importlib.import_module(mod), cls)()
