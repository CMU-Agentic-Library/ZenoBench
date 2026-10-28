"""Planner entry points for the evaluation (no VLM planner is implemented here).

All planners act through episode.episode.Episode with profiles/physical/benchmark.yaml
(observation-limited, no automatic recovery) except the GT oracle, which
run_episode executes with profiles/physical/oracle.yaml (the original GT runner).

* fixed     - run_episode --planner fixed: the nominal plan, stop at the first failure
* retry     - run_episode --planner retry: the nominal plan, repeat a failed call up to 2 times
* recovery  - run_episode --planner recovery --policy module:Class: a closed-loop Planner
* oracle    - run_episode --planner oracle: GT runner + the route that fits the variant

A recovery planner implements::

    class MyPlanner(Planner):
        def reset(self, task_instruction, skills=None): ...
        def next_call(self, observation) -> {"skill": str, "args": dict} | None

``observation`` is Episode.observation("path"): the head image as a PNG path
(``images``), visible objects, observation cache, known static places, robot
state and the last call's result (``last_result``, unobserved names masked) -
the fields of the episode's profile, the same as an HTTP planner gets.
"""

from __future__ import annotations

import importlib


class Planner:
    def reset(self, task_instruction, skills=None):
        self.instruction = task_instruction

    def next_call(self, observation):
        raise NotImplementedError


def load_policy(spec):
    if not spec or ":" not in spec:
        raise ValueError("--policy module:Class")
    mod, cls = spec.split(":", 1)
    return getattr(importlib.import_module(mod), cls)()
