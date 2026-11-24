"""Code-as-Policies baseline: the VLM writes one Python program over the same skills; the program
branches on call results and on what the robot sees.

    --planner recovery --policy baseline.code_policy:CodeAsPolicies --profile sticky/benchmark

The skills are not replaced: every skill is a Python function that hands the call to the
environment.  The program runs in a thread; each skill call pauses it, run_episode executes the
call through next_call, and the program resumes with the result.  The program ends -> the episode
ends.  An exception (or a runaway loop) ends the program; the VLM may then write one new program
that continues from the current state (REGENERATIONS), which costs a VLM query, not a skill call.

Sandbox: no imports, a small set of builtins, a line budget per program.
"""

from __future__ import annotations

import queue
import re
import sys
import threading

from baseline.base import BaselinePlanner
from baseline.prompt import image_paths, system_prompt, user_prompt

ANSWER = """\
Write a Python program that carries out the instruction. Each skill is a Python function: call it \
with keyword arguments, for example navigate(destination="kitchen_island/top"). Every call runs on \
the robot and returns a result r with r.success (bool), r.error_code, r.error (text), r.outputs \
(dict) and r.now_visible (names that became visible).
You can also call observe(), which returns the current observation as a dict (keys \
visible_objects, observation_cache, robot, known_places; each object has name, category, \
last_seen_on, last_seen_in), and find(text), which returns the names of observed objects whose \
category contains the text.
Use if / for / while on results and observations to handle failures and what the robot finds. No \
imports. When the program ends, the episode ends.
Answer format: one or two short sentences starting with "Thought:", then the whole program in one \
```python code block. If nothing should be done, the program is just `pass`."""

REGENERATIONS = 1          # new programs after an exception
LINE_BUDGET = 200_000      # executed lines per program (stops runaway loops)
WAIT_S = 120               # longest wait for the program's next call


class _Stop(BaseException):
    """Raised inside the program thread to end it (not catchable by `except Exception`)."""


class Result:
    def __init__(self, res):
        res = res or {}
        self.success = bool(res.get("success"))
        self.error_code = res.get("error_code")
        self.error = res.get("error") or ""
        self.outputs = res.get("outputs") or {}
        self.now_visible = list(res.get("now_visible") or [])

    def __bool__(self):
        return self.success

    def __repr__(self):
        return f"Result(success={self.success}, error_code={self.error_code!r}, error={self.error[:80]!r})"


SAFE_BUILTINS = {n: __builtins__[n] if isinstance(__builtins__, dict) else getattr(__builtins__, n) for n in (
    "len", "range", "enumerate", "zip", "min", "max", "sum", "sorted", "reversed", "any", "all", "abs", "round",
    "str", "int", "float", "bool", "list", "dict", "set", "tuple", "isinstance", "Exception", "ValueError",
    "KeyError", "IndexError", "RuntimeError", "StopIteration")}


def extract_code(text: str) -> str:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text or "", re.S)
    return blocks[-1] if blocks else ""


class Program:
    """One generated program running in its own thread, one skill call at a time."""

    def __init__(self, code, skills, obs):
        self.code, self.obs = code, obs
        self.to_planner: queue.Queue = queue.Queue()
        self.to_program: queue.Queue = queue.Queue()
        self.printed: list[str] = []
        ns = {"__builtins__": dict(SAFE_BUILTINS, print=self._print), "observe": self._observe, "find": self._find}
        for s in skills:
            ns[s["name"]] = self._skill(s["name"], list((s.get("parameters") or {}).keys()))
        self.ns = ns
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _print(self, *a, **_):
        self.printed.append(" ".join(map(str, a))[:300])

    def _observe(self):
        return {k: v for k, v in self.obs.items() if k != "images"}

    def _find(self, text):
        names = []
        for key in ("visible_objects", "observation_cache"):
            for o in self.obs.get(key) or []:
                if str(text).lower() in str(o.get("category", "")).lower() and o["name"] not in names:
                    names.append(o["name"])
        return names

    def _skill(self, name, params):
        def call(*args, **kwargs):
            if len(args) > len(params):
                raise TypeError(f"{name}() takes at most {len(params)} positional arguments")
            kwargs = {**dict(zip(params, args)), **kwargs}
            self.to_planner.put(("call", {"skill": name, "args": kwargs}))
            msg = self.to_program.get()
            if msg is None:
                raise _Stop()
            res, self.obs = msg
            return Result(res)
        call.__name__ = name
        return call

    def _run(self):
        lines = [0]

        def tracer(frame, event, arg):
            if event == "line":
                lines[0] += 1
                if lines[0] > LINE_BUDGET:
                    raise RuntimeError(f"the program ran more than {LINE_BUDGET} lines (a loop that never ends?)")
            return tracer
        sys.settrace(tracer)
        try:
            exec(compile(self.code, "<program>", "exec"), self.ns)
            self.to_planner.put(("done", None))
        except _Stop:
            pass
        except BaseException as exc:                          # noqa: BLE001 - reported to the VLM
            self.to_planner.put(("error", f"{type(exc).__name__}: {exc}"))
        finally:
            sys.settrace(None)

    def start(self):
        self.thread.start()
        return self.wait()

    def resume(self, result, obs):
        self.to_program.put((result, obs))
        return self.wait()

    def wait(self):
        try:
            return self.to_planner.get(timeout=WAIT_S)
        except queue.Empty:
            return ("error", f"the program made no skill call for {WAIT_S} s")

    def stop(self):
        if self.thread.is_alive():
            self.to_program.put(None)


class CodeAsPolicies(BaselinePlanner):
    name = "code_policy"

    def reset(self, task_instruction, skills=None):
        super().reset(task_instruction, skills)
        self.system = system_prompt(self.skills, self.max_calls, answer=ANSWER)
        self.program = None
        self.programs = []                 # generated code, for the log
        self.regenerations_left = REGENERATIONS

    def next_call(self, observation):
        self.observe(observation)
        usage = None
        if self.program is None:
            self.program, usage = self._new_program(observation, error="")
            if self.program is None:
                return None
            ev = self.program.start()
        else:
            ev = self.program.resume(observation.get("last_result"), observation)
        while True:
            kind, val = ev
            if kind == "call":
                if len(self.history) >= self.max_calls:
                    self.program.stop()
                    self.stop_reason = "budget"
                    return None
                return self.emit(val, f"program {len(self.programs)}", usage)
            if kind == "done":
                self.stop_reason = "program_done"
                return None
            # kind == "error": one new program from the current state, if allowed
            self.program.stop()
            if self.regenerations_left <= 0:
                self.stop_reason = f"program_error: {val}"[:300]
                return None
            self.regenerations_left -= 1
            self.program, usage = self._new_program(observation, error=val)
            if self.program is None:
                return None
            ev = self.program.start()

    def _new_program(self, observation, error):
        note = ""
        if error:
            note = (f"Your previous program stopped with an error: {error}\n"
                    "Write a new program that continues from the current state (the calls above already ran).")
        user = user_prompt(self.instruction, observation, self.history, len(self.history), self.max_calls, note)
        user = user.replace("What is the next call?", "Write the program.")
        for attempt in range(2):
            text, usage = self.ask(self.system, user, image_paths(observation))
            code = extract_code(text)
            if not code.strip():
                self.usage["parse_errors"] += 1
                user += "\n\nYour answer had no ```python block. Answer again in the format."
                continue
            try:
                compile(code, "<program>", "exec")
            except SyntaxError as exc:
                self.usage["parse_errors"] += 1
                user += f"\n\nYour program has a syntax error ({exc}). Answer again."
                continue
            self.programs.append(code)
            return Program(code, self.skills, observation), usage
        self.stop_reason = "parse_error"
        return None, None

    def summary(self):
        return {**super().summary(), "programs": self.programs}


