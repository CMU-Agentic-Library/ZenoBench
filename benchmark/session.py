"""The planner-facing session: observations in, skill calls out.

    session = LimitedSession(rig, image_dir=...)
    obs = session.observe()            # first-person image, visible objects, cache, places, robot, feedback
    fb = session.call("pick", {"object": "paperback_book"})

Every call goes through benchmark.observation.GatedRunner (permission check,
no automatic recovery).  Feedback carries the measured predicate checks and
outputs of the call with unobserved object names masked; it never carries
bound GT nouns or relation-graph recovery hints.
"""

from __future__ import annotations

import json
import time

from .metrics import call_eval
from .observation import GatedRunner, Observer


class LimitedSession:
    def __init__(self, rig, image_dir=None, capture_images=True):
        self.rig = rig
        self.observer = Observer(rig, image_dir=image_dir)
        self.runner = GatedRunner(rig, self.observer, capture_images=capture_images and image_dir is not None)
        self.history: list[dict] = []
        self.last_eval = None             # evaluation-only (failed sub-step chain); never in observe()
        self.observer.snapshot("start", image=False)

    # ------------------------------------------------------------- observation
    def observe(self, image_tag=None) -> dict:
        obs = self.observer
        rig = self.rig
        if image_tag:
            obs.snapshot(image_tag, image=True)
        from zeno_skills.evaluator import room_of
        x, y, yaw = rig.base_pose()
        return {
            "image": obs.images[-1] if obs.images else None,
            "visible_objects": [obs.describe(n) for n in sorted(obs.view)],
            "observation_cache": [obs.describe(n) for n in sorted(obs.cache)],
            "known_places": obs.places,
            "robot": {"base_pose": [round(x, 3), round(y, 3), round(yaw, 1)], "room": room_of(rig.ann.rooms, (x, y)),
                      "right_hand": (rig.held or {}).get("name"),
                      "left_hand": (getattr(rig, "left_held", None) or {}).get("name"),
                      "temperatures_c": {k: round(v, 1) for k, v in (rig.thermal.temperatures_c.items()
                                                                       if rig.thermal else []) if obs.known(k)}},
            "last_feedback": self.history[-1]["feedback"] if self.history else None,
        }

    # ------------------------------------------------------------- action
    def call(self, skill: str, args: dict) -> dict:
        try:
            res = self.runner.run(skill, dict(args))
            fb = self.runner.feedback(res, args)
            self.last_eval = call_eval(res)
        except Exception as exc:          # bad inputs (unknown slot, missing input): the planner's error
            fb = {"action": f"{skill}({json.dumps(args)})", "success": False, "error_code": "BAD_CALL",
                  "error": f"{type(exc).__name__}: {exc}", "path": None, "checks": [], "outputs": {}, "substeps": []}
            self.last_eval = {"failed_substep": [fb["action"]], "leaf_code": "BAD_CALL", "leaf_error": fb["error"],
                              "failed_checks": []}
        fb["image"] = self.observer.images[-1] if self.observer.images else None
        fb["now_visible"] = sorted(self.observer.view)
        self.history.append({"skill": skill, "args": args, "feedback": fb})
        return fb

    def run_planner(self, planner, task, max_calls=60, sink=None, state_fn=None) -> list:
        """Closed loop: the planner sees observations and feedback only.  state_fn (GT
        summary for the evaluation) is logged before and after each call, never shown."""
        rows = []
        self.stop_reason = "budget"           # max_calls reached without the planner ending the episode
        planner.reset(task_instruction=task["instruction"], skills=task.get("skill_menu"))
        for i in range(max_calls):
            obs = self.observe(image_tag=f"step{i}")
            t0 = time.time()
            act = planner.next_call(obs)
            planner_s = round(time.time() - t0, 2)
            if act is None:
                self.stop_reason = "planner_done"
                break
            before = state_fn() if state_fn else None
            t1 = time.time()
            fb = self.call(act["skill"], act.get("args", {}))
            row = {"index": i, "skill": act["skill"], "args": act.get("args", {}), "feedback": fb,
                   "planner_note": act.get("note", ""), "planner_s": planner_s,
                   "wall_s": round(time.time() - t1, 1), "tick": self.rig.tick, "state_before": before,
                   "state": state_fn() if state_fn else None, "eval": self.last_eval}
            rows.append(row)
            if sink is not None:
                sink.write(json.dumps(row, default=float) + "\n")
                sink.flush()
        return rows
