"""The closed loop logs GT state and the failed sub-step for the evaluation, not in the planner's view."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from benchmark.planners import ReplayPlanner  # noqa: E402
from benchmark.session import LimitedSession  # noqa: E402


class _Res:
    def __init__(self, ok):
        self.d = {"action": "pick_object(object=b)", "success": ok, "error_code": None if ok else "SUBSKILL_FAILED",
                  "error": None if ok else "x", "children": [] if ok else [
                      {"action": "fetch(b)", "success": False, "error_code": "POLICY_FAILED", "error": "not held",
                       "children": [], "preconditions": [{"atom": "grasp_clearance(b)", "holds": False}]}]}

    def asdict(self):
        return self.d


class _Runner:
    def __init__(self):
        self.n = 0

    def run(self, skill, args):
        self.n += 1
        return _Res(self.n > 1)

    def feedback(self, res, args):
        d = res.asdict()
        return {"action": d["action"], "success": d["success"], "error_code": d["error_code"], "error": d["error"],
                "checks": [], "substeps": []}


def test_run_planner_logs_state_and_eval(monkeypatch):
    s = object.__new__(LimitedSession)
    s.runner, s.history, s.last_eval = _Runner(), [], None
    s.observer = type("O", (), {"images": [], "view": set()})()
    s.rig = type("R", (), {"tick": 7})()
    seen = []
    monkeypatch.setattr(LimitedSession, "observe", lambda self, image_tag=None: seen.append(
        self.history[-1]["feedback"] if self.history else None) or {"last_feedback": seen[-1]})
    calls = [{"skill": "pick", "args": {"object": "b"}}] * 2
    states = iter([{"b": {"pos": [0, 0, 0]}}, {"b": {"pos": [0, 0, 0]}}, {"b": {"pos": [1, 0, 0]}},
                   {"b": {"pos": [1, 0, 1]}}])
    rows = s.run_planner(ReplayPlanner(calls), {"instruction": "x"}, max_calls=5, state_fn=lambda: next(states))
    assert rows[0]["eval"]["failed_substep"] == ["pick_object(object=b)", "fetch(b)"]
    assert rows[0]["eval"]["failed_checks"] == ["grasp_clearance(b)"]
    assert rows[1]["state_before"] == {"b": {"pos": [1, 0, 0]}} and rows[1]["state"] == {"b": {"pos": [1, 0, 1]}}
    assert rows[0]["planner_s"] is not None and rows[0]["tick"] == 7
    # the planner-facing feedback carries neither the state nor the eval block
    assert all("eval" not in fb and "state" not in fb for fb in seen if fb)
