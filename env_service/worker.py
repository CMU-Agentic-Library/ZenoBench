"""One exp = one simulator.  Run under Isaac Sim's Python by the server:

    $ISAACLAB_PYTHON -m env_service.worker --task-id collect_fruits --cmd-fd 5 --resp-fd 6

Line-delimited JSON over two pipes (stdout/stderr stay free for Isaac's logs).
The worker first answers ``{"type": "ready", "observation": ...}`` (or
``{"type": "error", ...}``), then serves requests ``{"op": ...}``:

* ``contract`` {"call": {"contract": verb, "args": {...}}} -> {"result": public contract result}
* ``observe``  -> {"observation": ...}
* ``check``    -> {"success": bool, "goal": [{"atom", "holds"}]}
* ``close``    -> exits
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import traceback

from env_service.tasks import ROOT, atom_text, load_tasks

sys.path.insert(0, str(ROOT))

_PATH_PREFIX = re.compile(r"^path \S+: ")


def _measured(rows):
    return [{"atom": r["atom"], "holds": bool(r["holds"])} for r in rows]


def _failed_step(children):
    """The innermost failed nested call of a composite skill."""
    child = next((c for c in reversed(children) if not c["success"]), None)
    if child is None:
        return None
    if child.get("error_code") == "SUBSKILL_FAILED" and child.get("children"):
        inner = _failed_step(child["children"])
        if inner is not None:
            return inner
    return {"action": child["action"], "error_code": child["error_code"],
            "preconditions": _measured(child["preconditions"]),
            "postconditions": _measured(child["postconditions"])}


def public_result(call: dict, res) -> dict:
    """What the planner sees of one contract: success, error code, measured
    pre/postconditions and declared outputs.  No path, policy steps, noun
    bindings, nested calls or fallback suggestions."""
    out = {"contract": call.get("contract"), "args": call.get("args", {}), "success": bool(res.success),
           # BINDING is a skill-definition bug, not a planner mistake
           "error_code": "INTERNAL_ERROR" if res.error_code == "BINDING" else res.error_code,
           "error": _PATH_PREFIX.sub("", res.error) if res.error else None,
           "preconditions": _measured(res.preconditions), "postconditions": _measured(res.postconditions),
           "outputs": _plain(res.outputs) if res.success else {}}
    if res.error_code == "SUBSKILL_FAILED":
        out["failed_step"] = _failed_step(res.children)
    return out


def error_result(call: dict, code: str, message: str) -> dict:
    return {"contract": call.get("contract") if isinstance(call, dict) else None,
            "args": call.get("args", {}) if isinstance(call, dict) else {}, "success": False,
            "error_code": code, "error": message, "preconditions": [], "postconditions": [], "outputs": {}}


def _plain(value):
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, float):
        return round(value, 4)
    return value


class Episode:
    def __init__(self, task: dict, wrist_cameras: bool, video_path=None):
        from zeno_skills.predicates import before_snapshot
        from zeno_skills.runtime import launch, make_rig
        from zeno_skills.skill_runtime import SkillContractRunner
        scene = json.loads((ROOT / task["task_json"]).read_text())
        self.task = task
        self.video_recorder = None
        self.app = launch(video=bool(video_path), first_person=True)
        # same start as the verified whole-task rollouts (tools/verify_skills.py)
        self.rig = make_rig(self.app, scene["scene_usd"], scene["annotation"], video=bool(video_path),
                            res=(360, 640), stride=8,
                            first_person=True, first_person_res=(720, 960), wrist_cameras=wrist_cameras,
                            first_person_focal_length=7.5)
        if video_path:
            from env_service.recording import VideoRecorder
            self.video_recorder = VideoRecorder(video_path, fps=120 / self.rig.stride)
            self.rig.frames = self.video_recorder
        self.rig.caption = task["id"]
        self.rig.configure_thermal(scene)
        self.rig.step(30)
        self.start = before_snapshot(self.rig)       # relative goal predicates compare to the start
        self.rig.step(90)
        self.runner = SkillContractRunner(self.rig, nested_repair=False)

    # -- observation ----------------------------------------------------------------
    def images(self):
        from PIL import Image
        out = []
        for name, frame in self.rig.get_camera_images().items():
            buf = io.BytesIO()
            Image.fromarray(frame).save(buf, format="PNG")
            out.append({"camera": name, "png_base64": base64.b64encode(buf.getvalue()).decode()})
        return out

    def objects(self):
        """Only the task's own entities (tasks.json ``entities``)."""
        from zeno_skills.predicates import entity_kind, entity_point
        st = self.rig.state()
        rows = []
        for name in self.task["entities"]:
            kind, _ = entity_kind(self.rig.ann, name)
            row = {"name": name, "kind": kind}
            try:
                row["position"] = [round(float(v), 3) for v in entity_point(self.rig, name, st)]
            except Exception:
                pass
            rows.append(row)
        return rows

    def goal_status(self):
        from zeno_skills.predicates import REGISTRY
        rows = []
        for atom in self.task["goal"]:
            pred = REGISTRY[atom[0]]
            try:
                ok, _ = pred.evaluate(self.rig, {"before": self.start}, **dict(zip(pred.arg_names, atom[1:])))
            except Exception:
                ok = False
            rows.append({"atom": atom_text(atom), "holds": bool(ok)})
        return rows

    def robot(self):
        from zeno_skills.predicates import held_name
        return {"base_pose": [round(float(v), 3) for v in self.rig.base_pose()],
                "held_right": held_name(self.rig, "right"), "held_left": held_name(self.rig, "left")}

    def observation(self):
        return {"images": self.images(), "objects": self.objects(), "robot": self.robot(),
                "task_status": self.goal_status()}

    # -- requests -------------------------------------------------------------------
    def contract(self, call):
        from zeno_skills.skill_runtime import ContractError
        if not isinstance(call, dict) or not isinstance(call.get("contract"), str) \
                or not isinstance(call.get("args", {}), dict):
            return error_result(call, "BAD_CALL", 'expected {"contract": "<verb>", "args": {...}}')
        verb = call["contract"]
        if verb not in self.runner.by_verb:
            return error_result(call, "UNKNOWN_CONTRACT", f"no contract named {verb!r}")
        for slot, value in call.get("args", {}).items():      # the runtime does not check enum values itself
            enum = self.runner.by_verb[verb]["inputs"].get(slot, {}).get("enum")
            if enum and value is not None and value not in enum:
                return error_result(call, "INPUT_UNKNOWN", f"{verb}: {slot}={value!r} is not one of {enum}")
        try:
            res = self.runner.run(verb, call.get("args", {}))
        except ContractError as exc:        # input checks raise before the runner's own handler
            return error_result(call, exc.code, str(exc).split(": ", 1)[-1])
        except Exception as exc:
            traceback.print_exc()
            return error_result(call, "INTERNAL_ERROR", f"{type(exc).__name__}: {exc}")
        return public_result(call, res)

    def check(self):
        self.rig.step(60)
        goal = self.goal_status()
        return {"success": all(g["holds"] for g in goal), "goal": goal}

    def close(self):
        if self.video_recorder is not None:
            self.video_recorder.close()
            print(f"[video] saved {self.video_recorder.path} ({self.video_recorder.frame_count} frames)", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--cmd-fd", type=int, required=True)
    ap.add_argument("--resp-fd", type=int, required=True)
    ap.add_argument("--wrist-cameras", action="store_true")
    ap.add_argument("--video-path")
    args = ap.parse_args()
    cmd = os.fdopen(args.cmd_fd, "r")
    resp = os.fdopen(args.resp_fd, "w")

    def send(msg):
        resp.write(json.dumps(msg, default=float) + "\n")
        resp.flush()

    try:
        ep = Episode(load_tasks()[args.task_id], args.wrist_cameras, args.video_path)
        send({"type": "ready", "observation": ep.observation()})
    except Exception as exc:
        traceback.print_exc()
        send({"type": "error", "error": f"{type(exc).__name__}: {exc}"})
        os._exit(1)
    try:
        for line in cmd:
            req = json.loads(line)
            op = req.get("op")
            try:
                if op == "contract":
                    send({"result": ep.contract(req.get("call"))})
                elif op == "observe":
                    send({"observation": ep.observation()})
                elif op == "check":
                    send(ep.check())
                elif op == "close":
                    break
                else:
                    send({"error": f"unknown op {op!r}"})
            except Exception as exc:
                traceback.print_exc()
                send({"error": f"{type(exc).__name__}: {exc}"})
    finally:
        ep.close()
    sys.stdout.flush()
    os._exit(0)          # Isaac's own shutdown can hang; the process is disposable


if __name__ == "__main__":
    main()
