"""Interface test planners for the live smoke test of the recovery entry.

They exercise the closed loop only (budget exit, crash -> incomplete); they are
not planners and their runs are never a recovery result.

    run_episode.py --planner recovery --policy benchmark.tests.smoke_planners:BudgetPlanner --max-calls 3
    run_episode.py --planner recovery --policy benchmark.tests.smoke_planners:CrashPlanner
"""

from benchmark.planners import Planner


class BudgetPlanner(Planner):
    """Never ends the episode: nods until the call budget is used up."""

    def next_call(self, observation):
        return {"skill": "nod", "args": {}, "note": "smoke test: budget exit"}


class CrashPlanner(Planner):
    """One valid call, then an exception inside the planner (harness error -> incomplete)."""

    def reset(self, task_instruction, skills=None):
        super().reset(task_instruction, skills)
        self.n = 0

    def next_call(self, observation):
        self.n += 1
        if self.n > 1:
            raise RuntimeError("smoke test: planner crash")
        return {"skill": "nod", "args": {}}
