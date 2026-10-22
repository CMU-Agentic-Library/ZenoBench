"""Every call logs the failed sub-step chain for the evaluation, never in the planner's view."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from episode.episode import Episode  # noqa: E402
from episode.profile import load_profile  # noqa: E402


class _Res:
    def __init__(self, ok):
        self.d = {"action": "pick_object(object=b)", "success": ok, "error_code": None if ok else "SUBSKILL_FAILED",
                  "error": None if ok else "x", "selected_path": None, "outputs": {}, "preconditions": [],
                  "postconditions": [], "children": [] if ok else [
                      {"action": "fetch(b)", "success": False, "error_code": "POLICY_FAILED", "error": "not held",
                       "children": [], "preconditions": [{"atom": "grasp_clearance(b)", "holds": False}],
                       "postconditions": []}]}
        for k, v in self.d.items():
            setattr(self, k, v)

    def asdict(self):
        return self.d


def _episode(ok):
    ep = object.__new__(Episode)
    ep.profile = load_profile("benchmark")
    ep.runner = SimpleNamespace(contract=lambda key: {"inputs": {}}, run=lambda verb, args: _Res(ok))
    ep.observer = SimpleNamespace(view={"b"}, mask=lambda value, allow: value)
    return ep


def test_call_logs_the_failed_substep_chain():
    public, record = _episode(False).call({"contract": "pick", "args": {"object": "b"}})
    assert record["eval"]["failed_substep"] == ["pick_object(object=b)", "fetch(b)"]
    assert record["eval"]["failed_checks"] == ["grasp_clearance(b)"]
    assert record["now_visible"] == ["b"] and record["action"] == "pick_object(object=b)"
    # the planner-facing result carries neither the eval block nor the evaluation-only fields
    assert not {"eval", "checks", "now_visible", "action", "path"} & set(public)


def test_bad_call_has_an_eval_block_too():
    _, record = _episode(True).call(["pick"])
    assert record["eval"]["leaf_code"] == "BAD_CALL" and record["eval"]["failed_substep"]
