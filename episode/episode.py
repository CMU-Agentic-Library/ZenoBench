"""One simulated episode, for every task catalog and every profile.

    task = load_catalog("benchmark/v3/tasks.json")["T01_book_to_dining_table"]
    cfg = episode_config(task, seed=10, variant="no_overhang")
    ep = Episode(task, cfg, load_profile("benchmark"), out_dir)
    obs = ep.observation()
    result, record = ep.call({"contract": "pick", "args": {"object": "paperback_book"}})
    ep.check()

The env_service worker (an HTTP planner) and benchmark/run_episode.py (scripted routes,
the fixed / retry / recovery planners, the GT oracle) both drive this class; they differ
only in who chooses the calls.  What the episode does is fixed by its profile
(episode/profiles/*/*.yaml): the runner (GT or gated), automatic recovery, feedback masking
and the observation fields.

Simulator imports happen inside the methods; ``public_result`` and the goal helpers work
without Isaac Sim.
"""
from __future__ import annotations

import base64
import io
import json
import math
import re
import traceback
from pathlib import Path

from episode.catalog import ROOT, atom_text, base_sha1, entities, episode_hash
from episode.profile import apply_rig_flags, needs_observer

_PATH_PREFIX = re.compile(r"^path \S+: ")


# ----------------------------------------------------------------- planner-facing contract results
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


def error_result(call, code: str, message: str) -> dict:
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
        return round(value, 4) if math.isfinite(value) else None
    return value


# ----------------------------------------------------------------- goal and final state
def evaluate_goal(rig, goal, start_snapshot):
    """{"all": [atom], "any": [[atom...], ...]}: every ``all`` atom and at
    least one ``any`` group must hold on the final GT state."""
    from episode.goal_predicates import GOAL_PREDICATES
    from zeno_skills.predicates import REGISTRY
    ctx = {"before": start_snapshot}

    def atom(a):
        names = [y for x in a[1:] for y in (x if isinstance(x, list) else [x])]      # list args: grouped(objects, ...)
        missing = [x for x in names if isinstance(x, str) and x in start_snapshot.get("_removed", ())]
        if missing:
            return {"atom": atom_text(a), "holds": False, "detail": f"{missing[0]} is not in this episode"}
        neg = a[0].startswith("not ")
        name = a[0][4:] if neg else a[0]
        pred = GOAL_PREDICATES.get(name) or REGISTRY[name]       # goal-only verifiers first
        try:
            ok, detail = pred.evaluate(rig, ctx, **dict(zip(pred.arg_names, a[1:])))
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        ok = bool(ok) != neg
        return {"atom": atom_text(a), "holds": ok, "detail": str(detail)}
    rows = [atom(a) for a in goal.get("all", [])]
    groups = [[atom(a) for a in g] for g in goal.get("any", [])]
    ok = all(r["holds"] for r in rows) and (not groups or any(all(r["holds"] for r in g) for g in groups))
    return ok, {"all": rows, "any": groups}


def flat_goal(goal: dict) -> list[dict]:
    """Goal rows as {"atom", "holds"}: the ``all`` atoms, then every ``any`` atom."""
    return [{"atom": r["atom"], "holds": bool(r["holds"])}
            for r in goal["all"] + [r for g in goal["any"] for r in g]]


def floor_drops(rig, task, start_snapshot):
    """Task objects that ended on the floor although they did not start there."""
    out = []
    st = rig.state()
    for n in task.get("watch", []):
        if n not in rig.ann.objects or n not in start_snapshot["objects"]:
            continue
        z0 = start_snapshot["objects"][n]["pos"][2]
        # the centre, not the bottom: a mug lying on its side has its "bottom" 5 cm up
        low = min(float(rig.geo.bottom(n, st)[2]), float(rig.geo.centre(n, st)[2]))
        in_container = any(rig.geo.inside(n, c, st)[0] for c, o in rig.ann.objects.items()
                           if c != n and rig.ann.asset_of(o).get("container"))
        if low < 0.08 and z0 > 0.3 and not in_container and n not in task.get("may_end_on_floor", []):
            out.append(n)
    return out


def state_summary(rig, task):
    st = rig.state()
    out = {"base": [round(v, 3) for v in rig.base_pose()],
           "held": [(rig.held or {}).get("name"), (getattr(rig, "left_held", None) or {}).get("name")]}
    for n in task.get("watch", []):
        if n in st["objects"]:
            sup = rig.geo.support_under(n, st)
            q = st["objects"][n]["quat"]
            yaw = math.degrees(math.atan2(2 * (q[0] * q[3] + q[1] * q[2]), 1 - 2 * (q[2] ** 2 + q[3] ** 2)))
            out[n] = {"pos": [round(v, 3) for v in st["objects"][n]["pos"]], "yaw_deg": round(yaw, 1),
                      "on": sup["name"] if sup else None}
    if rig.thermal is not None:
        out["temp_c"] = {k: round(v, 1) for k, v in rig.thermal.temperatures_c.items()
                         if k in task.get("watch", [])}
    return out


# ----------------------------------------------------------------- the episode
class Episode:
    def __init__(self, task: dict, cfg: dict, profile: dict, out_dir, *, video=False, images=True,
                 image_dir=None, video_path=None, video_res=(540, 960), video_stride=4):
        """``cfg``: benchmark.scene.episode_config(task, seed, variant).  ``out_dir`` receives the
        episode annotation; ``image_dir`` (optional) the first-person image of every top-level call.

        Video (a third-person debug record, never an observation): ``video=True`` keeps the frames in
        memory for ``rig.write_video``; ``video_path`` streams them to that MP4 as they are rendered
        (env_service.recording.VideoRecorder), closed by ``close()``."""
        import numpy as np
        from benchmark.scene import build_annotation, make_prepare
        from zeno_skills.runtime import launch, make_rig
        from zeno_skills.skill_runtime import before_snapshot
        self.task, self.cfg, self.profile = task, cfg, profile
        ob = profile["observation"]
        self.cameras = list(ob["cameras"]) if images else []
        out_dir = Path(out_dir)
        ann_path = build_annotation(cfg, out_dir / "annotation.json")
        video = bool(video or video_path)
        self.app = launch(video, first_person=images)
        self.rig = rig = make_rig(self.app, f"{cfg['base']}/scene.usd", str(ann_path), video=video,
                                  res=tuple(video_res), stride=video_stride,
                                  handle_objects=tuple(task.get("handle_objects", ())), prepare=make_prepare(cfg),
                                  first_person=images, first_person_res=tuple(ob["image_size"]),
                                  first_person_focal_length=float(ob["focal_length_mm"]),
                                  wrist_cameras=bool({"left_wrist", "right_wrist"} & set(self.cameras)))
        self.video_recorder = None
        if video_path:
            from env_service.recording import VideoRecorder
            self.video_recorder = VideoRecorder(video_path, fps=120 / rig.stride)
            rig.frames = self.video_recorder          # frames go to disk as they are rendered
        rig.caption = task["task_id"]
        apply_rig_flags(rig, profile)
        # thermal state only for the foods that exist in this episode (removed objects have no body)
        base_task = json.loads((ROOT / cfg["base"] / "task.json").read_text())
        base_task = dict(base_task, thermal={k: v for k, v in (base_task.get("thermal") or {}).items()
                                             if k not in cfg["remove"]})
        for food, over in (cfg.get("thermal_override") or {}).items():
            if food in base_task["thermal"]:
                base_task["thermal"][food] = dict(base_task["thermal"][food], **over)
        if cfg.get("thermal_sources") is not None:
            base_task = dict(base_task, thermal_sources=cfg["thermal_sources"])
        rig.configure_thermal(base_task)
        rig.step(30)
        if cfg.get("start"):
            x0, y0, yaw0 = rig.base_pose()
            x1, y1, yaw1 = cfg["start"]
            dyaw = (yaw1 - yaw0 + 180) % 360 - 180
            n = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) / 0.02), int(abs(dyaw) / 2))
            for u in np.linspace(0, 1, n + 1)[1:]:
                rig.set_base(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, yaw0 + dyaw * u)
                rig.step(1)
        rig.step(120)
        self.start = before_snapshot(rig)                 # relative goal predicates compare to the start
        self.start["_removed"] = cfg["remove"]
        # where each object settled at t0: restore() puts an object back on this spot,
        # not just back on the same support
        rig.memory["initial_xy"] = {n: [float(b[0]), float(b[1])] for n, b in self.start["bottoms"].items()}
        self.initial_positions = {n: [round(v, 3) for v in self.start["objects"][n]["pos"]]
                                  for n in task.get("watch", []) if n in self.start["objects"]}
        self.runner, self.observer = self._make_runner(image_dir)
        self.last_result = None
        self.n_obs = 0
        self.image_dir = Path(image_dir) if image_dir else None

    def _make_runner(self, image_dir):
        from zeno_skills.skill_runtime import SkillContractRunner
        from benchmark.observation import NO_AUTO_STEPS
        ex = self.profile["execution"]
        kw = {"nested_repair": ex["nested_repair"], "auto_repair": ex["nested_repair"],
              "advisory": tuple(ex["advisory"]), "skip_steps": None if ex["slide_to_edge"] else NO_AUTO_STEPS}
        if not needs_observer(self.profile):
            return SkillContractRunner(self.rig, **kw), None
        from benchmark.observation import GatedRunner, Observer
        obs = Observer(self.rig, image_dir=image_dir)
        runner = GatedRunner(self.rig, obs, gate=ex["gate"], capture_images=image_dir is not None, **kw)
        obs.snapshot("start", image=False)
        return runner, obs

    # -- identity -----------------------------------------------------------------
    def metadata(self) -> dict:
        cfg, prof = self.cfg, self.profile
        b = base_sha1(cfg["base"])
        return {"task_id": self.task["task_id"], "catalog_kind": self.task.get("catalog_kind"),
                "seed": cfg["seed"], "variant": cfg["variant"], "difficulty": cfg.get("difficulty"),
                "conditions": cfg.get("conditions", []), "config_hash": cfg["config_hash"],
                "base_sha1": b, "profile": prof["name"], "profile_hash": prof["hash"],
                "episode_hash": episode_hash(cfg["config_hash"], prof["hash"], b)}

    # -- observation ----------------------------------------------------------------
    def observation(self, encode="base64", tag=None) -> dict:
        """The fields the profile turns on.  ``encode``: "base64" (PNG in the JSON) or "path"
        (PNG files under ``image_dir``)."""
        ob = self.profile["observation"]
        obs = self.observer
        if obs is not None:
            obs.snapshot()                                # the current view, not the one of the last call
        out = {}
        if self.cameras:
            out["images"] = self._images(encode, tag)
        if ob["gt_objects"]:
            out["objects"] = self._gt_objects()
        if ob["visible_objects"]:
            out["visible_objects"] = [obs.describe(n) for n in sorted(obs.view)]
        if ob["observation_cache"]:
            out["observation_cache"] = [obs.describe(n) for n in sorted(obs.cache)]
        if ob["known_places"]:
            out["known_places"] = obs.places if obs is not None else self._places()
        robot = self._robot()
        if robot:
            out["robot"] = robot
        if ob["task_status"]:
            out["task_status"] = self.goal_status()
        if ob["last_result"]:
            out["last_result"] = self.last_result
        return out

    def _images(self, encode, tag):
        from PIL import Image
        frames = self.rig.get_camera_images()
        self.n_obs += 1
        out = []
        for name in self.cameras:
            if name not in frames:
                continue
            img = Image.fromarray(frames[name])
            if encode == "path" and self.image_dir is not None:
                self.image_dir.mkdir(parents=True, exist_ok=True)
                path = self.image_dir / f"obs{self.n_obs:03d}_{re.sub(r'[^A-Za-z0-9_]+', '_', tag or 'view')[:40]}_{name}.png"
                img.save(path)
                out.append({"camera": name, "path": str(path)})
            else:
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                out.append({"camera": name, "png_base64": base64.b64encode(buf.getvalue()).decode()})
        return out

    def _gt_objects(self):
        from zeno_skills.predicates import entity_kind, entity_point
        st = self.rig.state()
        rows = []
        for name in entities(self.task):
            try:
                kind, _ = entity_kind(self.rig.ann, name)
            except Exception:
                continue                                  # removed in this episode
            row = {"name": name, "kind": kind}
            try:
                row["position"] = [round(float(v), 3) for v in entity_point(self.rig, name, st)]
            except Exception:
                pass
            rows.append(row)
        return rows

    def _places(self):
        from benchmark.observation import static_places
        return static_places(self.rig.ann)

    def _robot(self):
        r = self.profile["observation"]["robot"]
        rig = self.rig
        out = {}
        if r["base_pose"]:
            out["base_pose"] = [round(float(v), 3) for v in rig.base_pose()]
        if r["held"]:
            out["held_right"] = (rig.held or {}).get("name")
            out["held_left"] = (getattr(rig, "left_held", None) or {}).get("name")
        if r["room"]:
            from zeno_skills.evaluator import room_of
            x, y, _ = rig.base_pose()
            out["room"] = room_of(rig.ann.rooms, (x, y))
        if r["temperatures"] != "none" and rig.thermal is not None:
            known = self.observer.known if r["temperatures"] == "observed" else (lambda k: True)
            out["temperatures_c"] = {k: round(v, 1) for k, v in rig.thermal.temperatures_c.items() if known(k)}
        return out

    def goal_status(self):
        return flat_goal(evaluate_goal(self.rig, self.task["goal"], self.start)[1])

    # -- calls ----------------------------------------------------------------------
    def call(self, call) -> tuple[dict, dict]:
        """(result for the planner, record for the log).  The record is the unmasked result plus,
        for the evaluation only: the action text, the selected policy path, every measured check,
        the objects in view after the call and ``eval`` (benchmark.metrics.call_eval: the chain
        down to the deepest failed nested call)."""
        from benchmark.metrics import call_eval
        from zeno_skills.skill_runtime import ContractError
        res = None
        if not isinstance(call, dict) or not isinstance(call.get("contract"), str) \
                or not isinstance(call.get("args", {}), dict):
            out = error_result(call, "BAD_CALL", 'expected {"contract": "<verb>", "args": {...}}')
        else:
            out = self._validate(call)
            if out is None:
                try:
                    res = self.runner.run(call["contract"], dict(call.get("args", {})))
                    out = public_result(call, res)
                except ContractError as exc:          # input checks raise before the runner's own handler
                    out = error_result(call, exc.code, str(exc).split(": ", 1)[-1])
                except Exception as exc:
                    traceback.print_exc()
                    out = error_result(call, "INTERNAL_ERROR", f"{type(exc).__name__}: {exc}")
        action = res.action if res is not None else f"{out['contract']}({json.dumps(out['args'], default=str)})"
        record = dict(out, action=action, path=res.selected_path if res is not None else None,
                      checks=[{"atom": a["atom"], "holds": bool(a["holds"])}
                              for a in (res.preconditions + res.postconditions if res is not None else [])],
                      now_visible=sorted(self.observer.view) if self.observer is not None else [],
                      eval=call_eval(res.asdict() if hasattr(res, "asdict") else vars(res)) if res is not None else
                      {"failed_substep": [action], "leaf_code": out["error_code"], "leaf_error": out["error"],
                       "failed_checks": []})
        public = out
        if self.profile["execution"]["mask_feedback"] and self.observer is not None:
            allow = set()
            for v in (call.get("args") or {}).values() if isinstance(call, dict) else ():
                allow |= set(v) if isinstance(v, list) else {v} if isinstance(v, str) else set()
            public = self.observer.mask(out, allow)
        self.last_result = public
        return public, record

    def _validate(self, call):
        verb = call["contract"]
        try:
            c = self.runner.contract(verb)
        except KeyError:
            return error_result(call, "UNKNOWN_CONTRACT", f"no contract named {verb!r}")
        for slot, value in call.get("args", {}).items():      # the runtime does not check enum values itself
            enum = c["inputs"].get(slot, {}).get("enum")
            if enum and value is not None and value not in enum:
                return error_result(call, "INPUT_UNKNOWN", f"{verb}: {slot}={value!r} is not one of {enum}")
        return None

    # -- end --------------------------------------------------------------------------
    def check(self) -> dict:
        """Settle, then judge the goal on the GT state.  ``success`` also requires that no watched
        object fell to the floor when the profile says so (evaluation.drops_fail)."""
        self.rig.step(60)
        ok, goal = evaluate_goal(self.rig, self.task["goal"], self.start)
        drops = floor_drops(self.rig, self.task, self.start)
        fail_on_drop = self.profile["evaluation"]["drops_fail"]
        return {"success": bool(ok and not (drops and fail_on_drop)), "goal_ok": bool(ok), "goal": goal,
                "dropped": drops, "final_state": state_summary(self.rig, self.task), "sim_ticks": int(self.rig.tick)}

    def close(self):
        """Finish the streamed video, if any (call once, also after a crash)."""
        sticky = getattr(getattr(self, "rig", None), "sticky", None)
        if sticky is not None:
            sticky.close()                                # no sticky-hands weld outlives the episode
        if self.video_recorder is not None:
            self.video_recorder.close()
            print(f"[video] saved {self.video_recorder.path} ({self.video_recorder.frame_count} frames)", flush=True)
