"""VLM open-loop baseline: one VLM query at the start writes the whole call list from the
instruction and the initial observation; the list is then executed as written.  No VLM query
after that: the episode ends at the first failed call or at the end of the list.

    --planner recovery --policy baseline.open_loop:OpenLoop --profile sticky/benchmark

Expected: objects the robot has not seen at the start are refused (NOT_OBSERVED), so many Task
variants end near 0 - the point of the row is that closed-loop feedback is needed.
"""

from __future__ import annotations

from baseline.base import BaselinePlanner
from baseline.parse import ParseError, parse_plan, thought
from baseline.prompt import image_paths, system_prompt, user_prompt

ANSWER = """\
You will not see any feedback: write the whole plan now. It is executed in order and stops at the \
first failed call.
Answer format: one or two short sentences of reasoning starting with "Thought:", then a single \
JSON object on its own:
{"plan": [{"skill": "<skill name>", "args": {"<parameter>": <value>, ...}}, ...]}
or, if nothing should be done, {"finish": true, "reason": "<short reason>"}"""

PARSE_RETRIES = 2


class OpenLoop(BaselinePlanner):
    name = "open_loop"

    def reset(self, task_instruction, skills=None):
        super().reset(task_instruction, skills)
        self.system = system_prompt(self.skills, self.max_calls, answer=ANSWER)
        self.plan = None

    def next_call(self, observation):
        self.observe(observation)
        usage = note = None
        if self.plan is None:                              # the only VLM query of the episode
            self.plan, usage, note = self._make_plan(observation)
        elif self.history and not (self.history[-1].get("result") or {}).get("success"):
            self.stop_reason = "call_failed"
            return None
        if not self.plan:
            self.stop_reason = self.stop_reason or "plan_done"
            return None
        if len(self.history) >= self.max_calls:
            self.stop_reason = "budget"
            return None
        return self.emit(self.plan.pop(0), note or "", usage)

    def _make_plan(self, observation):
        note = ""
        for _ in range(PARSE_RETRIES + 1):
            user = user_prompt(self.instruction, observation, [], 0, self.max_calls, note)
            user = user.replace("What is the next call?", "Write the whole plan.")
            text, usage = self.ask(self.system, user, image_paths(observation))
            try:
                plan = parse_plan(text)
            except ParseError as exc:
                self.usage["parse_errors"] += 1
                note = f"Your previous answer could not be used ({exc}). Answer again in the format."
                continue
            if plan is None:
                self.stop_reason = "finish: " + thought(text, 200)
                return [], usage, ""
            self.usage["plan_length"] = len(plan)
            return plan, usage, thought(text)
        self.stop_reason = "parse_error"
        return [], None, ""
