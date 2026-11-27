"""Human reference: a person plays the episode through the same interface as the VLM planners.

Each step prints exactly the text a VLM planner gets (instruction, calls so far, observation) and
the head-camera image path(s); the person types one call.  Same skills, same budget, same profile.

    $ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --task T28_cup_to_bedside \
        --seed 10 --planner recovery --policy baseline.human:Human --profile sticky/benchmark

Run one episode at a time (not --batch: the batch runner has no terminal).  Input:

    pick object=mug_1                      skill with key=value args (values are JSON if they parse)
    {"skill": "pick", "args": {...}}       or the JSON the VLMs answer with
    menu  |  help <skill>                  list the skills / show one skill
    finish                                 end the episode
"""

from __future__ import annotations

import json
import shlex
import sys
import time

from baseline.base import BaselinePlanner
from baseline.parse import ParseError, parse_call
from baseline.prompt import image_paths, render_menu, user_prompt


def parse_line(line: str) -> dict | None | str:
    """A call dict, None for finish, or a command string ("menu", "help <skill>")."""
    line = line.strip()
    if not line:
        return ""
    if line.startswith("{"):
        return parse_call(line)
    head = line.split(None, 1)[0]
    if head in ("finish", "done", "quit"):
        return None
    if head in ("menu", "help"):
        return line
    toks = shlex.split(line, posix=False)     # keep quotes: values are parsed as JSON below
    args = {}
    for t in toks[1:]:
        if "=" not in t:
            raise ParseError(f"argument {t!r} is not key=value")
        k, v = t.split("=", 1)
        try:
            args[k] = json.loads(v)
        except json.JSONDecodeError:
            args[k] = v
    return {"skill": toks[0], "args": args}


class Human(BaselinePlanner):
    name = "human"

    def __init__(self, stdin=None, stdout=None):
        super().__init__(model="human")
        self.stdin, self.stdout = stdin or sys.stdin, stdout or sys.stdout

    def _say(self, s=""):
        print(s, file=self.stdout, flush=True)

    def next_call(self, observation):
        self.observe(observation)
        if len(self.history) >= self.max_calls:
            self.stop_reason = "budget"
            return None
        self._say("\n" + "=" * 80)
        self._say(user_prompt(self.instruction, observation, self.history, len(self.history), self.max_calls))
        for p in image_paths(observation):
            self._say(f"[image] {p}")
        t0 = time.time()
        while True:
            print("> ", end="", file=self.stdout, flush=True)
            line = self.stdin.readline()
            if line == "":                             # EOF
                self.stop_reason = "eof"
                return None
            try:
                act = parse_line(line)
            except ParseError as exc:
                self._say(f"? {exc}")
                continue
            if act == "":
                continue
            if act is None:
                self.stop_reason = "finish"
                self.usage["latency_s"] = round(self.usage["latency_s"] + time.time() - t0, 2)
                return None
            if isinstance(act, str):
                parts = act.split()
                chosen = [s for s in self.skills if len(parts) == 1 or s["name"] == parts[1]]
                self._say(render_menu(chosen) if chosen else f"? no skill {parts[1]!r}")
                continue
            if act["skill"] not in self.skill_names:
                self._say(f"? no skill {act['skill']!r} (type menu)")
                continue
            dt = round(time.time() - t0, 2)
            self.usage["latency_s"] = round(self.usage["latency_s"] + dt, 2)
            return self.emit(act, "human", {"latency_s": dt})
