"""ReAct / tool-use baseline: every step the VLM sees the instruction, the observation and the
history, writes a short thought, and gives one skill call or finishes.

    SHIFT_MODEL=claude-opus-5-5 $ISAACLAB_PYTHON benchmark/run_episode.py \
        --tasks benchmark/v6/tasks.json --task T28_cup_to_bedside --seed 10 \
        --planner recovery --policy baseline.react:ReAct --profile sticky/benchmark

Classes:

* ReAct            - the main-table baseline.
* ReActHint        - ablation: the system prompt also allows reasonable substitutes ("prefer what
                     was asked").  Tests whether prompting alone solves SHIFT.
* ReAct with ``--profile sticky/privileged`` - upper bound: the same planner also sees every task
  object with its position (GT), no goal status.

All models get the same text and the same JSON answer format, so the backends differ only in the model.
A local vLLM model also gets the menu as tools whose name slots are pinned (baseline/tools.py, decoded
under --tool-strict-level=parameter); its tool call is read as the same JSON answer.
"""

from __future__ import annotations

from baseline.base import BaselinePlanner
from baseline.parse import ParseError, parse_call, thought
from baseline.prompt import image_paths, system_prompt, user_prompt

PARSE_RETRIES = 2        # extra VLM queries after an unparseable answer (not skill calls)


class ReAct(BaselinePlanner):
    name = "react"
    substitution_hint = False
    keep_full = 8

    def reset(self, task_instruction, skills=None):
        super().reset(task_instruction, skills)
        self.system = system_prompt(self.skills, self.max_calls, self.substitution_hint)

    def next_call(self, observation):
        self.observe(observation)
        if len(self.history) >= self.max_calls:
            self.stop_reason = "budget"
            return None
        note = ""
        for _ in range(PARSE_RETRIES + 1):
            user = user_prompt(self.instruction, observation, self.history, len(self.history), self.max_calls, note)
            text, usage = self.ask(self.system, user, image_paths(observation), self.tools_for(observation))
            try:
                call = parse_call(text)
            except ParseError as exc:
                self.usage["parse_errors"] += 1
                note = (f"Your previous answer could not be used ({exc}). Answer again: one short Thought, "
                        "then exactly one JSON object.")
                continue
            if call is None:
                self.stop_reason = "finish: " + thought(text, 200)
                return None
            return self.emit(call, thought(text), usage)
        self.stop_reason = "parse_error"
        return None


class ReActHint(ReAct):
    name = "react_hint"
    substitution_hint = True
