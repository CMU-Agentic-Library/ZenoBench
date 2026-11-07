"""VLM planner: image + instruction in, one skill call out, every step.

    $ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --task T30_bowls_for_soup \\
        --variant bowl_on_cabinet --seed 10 --planner recovery --policy benchmark.vlm.planner:VLMPlanner
    $ISAACLAB_PYTHON benchmark/vlm/run_vlm.py ...          # the same, several episodes, with a summary

``VLMPlanner`` is the Planner run_episode's ``recovery`` loop drives (benchmark/planners.py).  Each step it turns the
episode observation into one user turn - the head-camera image(s), the visible objects, the places it knows, the
robot state and the result of the last call - sends the conversation to a *backend*, and parses the reply into
``{"skill", "args"}`` (or ``None`` when the model says the task is done).  A reply that is not a valid call is sent
back with the reason, up to ``VLM_MAX_REPAIRS`` times, then the episode stops (``planner_error``).

The planner sees only what the profile exposes: the instruction, the skill menu and the observation.  It never sees
the variant, the goal, the oracle route or GT positions.

Backends (``VLM_BACKEND``):

* ``replay`` - a stand-in for the VLM: it answers with the calls listed in ``VLM_REPLAY`` (a JSON list of
  ``{"skill", "args"}``), one per step, then "done".  It exercises the whole chain without a model; it is not a
  planner result.
* ``claude`` - Claude through the Anthropic SDK (``pip install anthropic``; ``ANTHROPIC_API_KEY`` or ``ant auth
  login``).  ``VLM_MODEL`` (default ``claude-opus-5-5``), ``VLM_EFFORT`` (default ``medium``).  Not exercised yet.

A new backend is a class with ``decide(system: str, messages: list) -> str`` (the raw reply text).  ``messages``
uses a neutral format: ``{"role": "user"|"assistant", "content": [{"type": "text", "text"} | {"type": "image",
"path"}]}``.

Every step is logged to ``<run dir>/vlm_steps.jsonl``: the text the model was given, the image paths, the raw reply,
the parsed call or the parse error, the backend and the seconds it took.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path

from benchmark.planners import Planner

SYSTEM = """You control a household robot (one arm, a mobile base, a head camera) in a house.
You are given a task from a person, the camera image(s) and a text summary of what the robot has seen.
Each turn, choose exactly ONE skill call from the skill list, or say the task is done.

Reply with a single JSON object and nothing else:
  {"skill": "<skill name>", "args": {<argument>: <value>, ...}, "note": "<short reason>"}
or, when the task is complete (or cannot be completed):
  {"done": true, "note": "<short reason>"}

Rules:
- Use only skill names and argument names from the skill list.
- Object arguments must name objects you have seen (they appear in "visible objects" or "seen before").
  Places (rooms, furniture, surfaces) come from "known places".
- If something you need is not in view, look, explore a room or furniture, or search for it.
- After each call you get its result; if it failed, read the error and adapt."""


def _skill_line(s):
    params = s.get("parameters") or {}
    args = ", ".join(f"{k}{'' if p.get('required') else '?'}: {p.get('type', 'any')}" for k, p in params.items())
    return f"- {s['name']}({args}): {s.get('description', '').strip()}"


def _short(v, n=600):
    t = json.dumps(v, default=str, ensure_ascii=False)
    return t if len(t) <= n else t[:n] + "..."


def observation_text(obs: dict, step: int) -> str:
    """The non-image observation fields as text for the model."""
    out = [f"Step {step}."]
    r = obs.get("robot")
    if r:
        out.append("Robot: " + _short(r, 400))
    lr = obs.get("last_result")
    if lr:
        keep = {k: lr.get(k) for k in ("contract", "args", "success", "error_code", "error", "outputs") if k in lr}
        out.append("Result of your last call: " + _short(keep, 800))
    vis = obs.get("visible_objects")
    if vis is not None:
        rows = [f"{o['name']} ({o.get('category')})"
                + (f" on {o['last_seen_on']}" if o.get("last_seen_on") else "")
                + (f" in {o['last_seen_in']}" if o.get("last_seen_in") else "")
                + (" [held]" if o.get("held") else "") for o in vis]
        out.append("Visible objects now: " + ("; ".join(rows) if rows else "none"))
    cache = obs.get("observation_cache")
    if cache is not None:
        seen = [f"{o['name']} ({o.get('category')}) last seen on {o.get('last_seen_on') or o.get('last_seen_in') or '?'}"
                for o in cache if not o.get("in_view")]
        if seen:
            out.append("Seen before (not in view now): " + "; ".join(seen))
    return "\n".join(out)


def places_text(places: dict) -> str:
    rooms = sorted(k for k, v in places.items() if v.get("kind") == "room")
    furn = sorted(f"{k} [{v.get('category')}, {v.get('room')}]" for k, v in places.items()
                  if v.get("kind") == "furniture")
    sups = sorted(k for k, v in places.items() if v.get("kind") == "support")
    return (f"Rooms: {', '.join(rooms)}\nFurniture: {'; '.join(furn)}\nSurfaces (furniture/part): {', '.join(sups)}")


def parse_reply(text: str, skills: dict):
    """-> ("call", {"skill", "args", "note"}) | ("done", note) | ("error", why)"""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return "error", "no JSON object in the reply"
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        return "error", f"invalid JSON: {exc}"
    if d.get("done"):
        return "done", str(d.get("note", ""))
    name, args = d.get("skill"), d.get("args", {})
    if name not in skills:
        return "error", f"unknown skill {name!r}"
    if not isinstance(args, dict):
        return "error", "args must be an object"
    params = skills[name].get("parameters") or {}
    unknown = sorted(set(args) - set(params))
    if unknown:
        return "error", f"{name} has no argument(s) {unknown}; it takes {sorted(params)}"
    missing = sorted(k for k, p in params.items() if p.get("required") and k not in args and "default" not in p)
    if missing:
        return "error", f"{name} needs argument(s) {missing}"
    return "call", {"skill": name, "args": args, "note": str(d.get("note", ""))}


# ---------------------------------------------------------------------------------------------------- backends
class ReplayBackend:
    """Stand-in for a VLM: answers with a fixed list of calls, then done (pipeline test only)."""
    name = "replay"

    def __init__(self, path=None):
        path = path or os.environ.get("VLM_REPLAY")
        if not path:
            raise ValueError("VLM_BACKEND=replay needs VLM_REPLAY=<json list of {skill, args}>")
        self.calls = json.loads(Path(path).read_text())
        self.i = 0

    def decide(self, system, messages):
        if self.i >= len(self.calls):
            return json.dumps({"done": True, "note": "replay finished"})
        c = self.calls[self.i]
        self.i += 1
        return json.dumps({"skill": c["skill"], "args": c.get("args", {}), "note": "replay"})


class ClaudeBackend:
    """Claude through the Anthropic SDK (vision input, one JSON call per reply).  Not exercised yet."""
    name = "claude"

    def __init__(self):
        import anthropic                                  # pip install anthropic
        self.client = anthropic.Anthropic()               # ANTHROPIC_API_KEY or `ant auth login`
        self.model = os.environ.get("VLM_MODEL", "claude-opus-5-5")
        self.effort = os.environ.get("VLM_EFFORT", "medium")

    @staticmethod
    def _content(blocks):
        out = []
        for b in blocks:
            if b["type"] == "image":
                data = base64.standard_b64encode(Path(b["path"]).read_bytes()).decode("utf-8")
                out.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}})
            else:
                out.append({"type": "text", "text": b["text"]})
        return out

    def decide(self, system, messages):
        msgs = [{"role": m["role"], "content": self._content(m["content"]) if m["role"] == "user" else m["content"]}
                for m in messages]
        resp = self.client.beta.messages.create(
            model=self.model, max_tokens=16000, system=system, messages=msgs,
            thinking={"type": "adaptive"}, output_config={"effort": self.effort},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        if resp.stop_reason == "refusal":
            return json.dumps({"done": True, "note": "model refused"})
        return "".join(b.text for b in resp.content if b.type == "text")


BACKENDS = {"replay": ReplayBackend, "claude": ClaudeBackend}


# ---------------------------------------------------------------------------------------------------- planner
class VLMPlanner(Planner):
    def __init__(self, backend=None):
        self.backend = backend or BACKENDS[os.environ.get("VLM_BACKEND", "replay")]()
        self.max_repairs = int(os.environ.get("VLM_MAX_REPAIRS", "2"))
        self.keep_images = int(os.environ.get("VLM_KEEP_IMAGES", "2"))   # past turns that keep their image
        self.log_path = None

    def attach(self, run_dir):
        """run_episode passes the run directory: the step log goes there"""
        self.log_path = Path(run_dir) / "vlm_steps.jsonl"
        self.log_path.write_text("")

    def reset(self, task_instruction, skills=None):
        self.instruction = task_instruction
        self.skills = {s["name"]: s for s in (skills or [])}
        self.messages, self.step, self.places_sent = [], 0, False
        self.error = None

    def _log(self, row):
        if self.log_path is not None:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(row, default=str, ensure_ascii=False) + "\n")

    def _user_turn(self, obs):
        blocks = []
        if self.step == 0:
            blocks.append({"type": "text", "text": f"Task: {self.instruction}\n\nSkills:\n"
                           + "\n".join(_skill_line(s) for s in self.skills.values())})
        if not self.places_sent and obs.get("known_places"):
            blocks.append({"type": "text", "text": "Known places:\n" + places_text(obs["known_places"])})
            self.places_sent = True
        for im in obs.get("images") or []:
            if im.get("path"):
                blocks.append({"type": "text", "text": f"Camera '{im.get('camera')}':"})
                blocks.append({"type": "image", "path": im["path"]})
        blocks.append({"type": "text", "text": observation_text(obs, self.step)})
        return {"role": "user", "content": blocks}

    def _trim_images(self):
        """keep the image of the last few user turns only (the text history stays)"""
        users = [m for m in self.messages if m["role"] == "user"]
        for m in users[:-self.keep_images] if self.keep_images else users:
            m["content"] = [b if b["type"] != "image" else {"type": "text", "text": "[earlier image omitted]"}
                            for b in m["content"]]

    def next_call(self, observation):
        self.messages.append(self._user_turn(observation))
        self._trim_images()
        for attempt in range(self.max_repairs + 1):
            t0 = time.time()
            try:
                reply = self.backend.decide(SYSTEM, self.messages)
            except Exception as exc:                      # the backend itself failed (network, quota, ...)
                self.error = f"backend error: {type(exc).__name__}: {exc}"
                self._log({"step": self.step, "attempt": attempt, "error": self.error})
                return None
            kind, val = parse_reply(reply, self.skills)
            self._log({"step": self.step, "attempt": attempt, "backend": self.backend.name,
                       "seconds": round(time.time() - t0, 2),
                       "user_text": "\n".join(b["text"] for b in self.messages[-1]["content"] if b["type"] == "text")
                       if attempt == 0 else None,
                       "images": [b["path"] for b in self.messages[-1]["content"] if b["type"] == "image"]
                       if attempt == 0 else None,
                       "reply": reply, "parsed": kind, "value": val})
            self.messages.append({"role": "assistant", "content": reply})
            if kind == "call":
                self.step += 1
                return val
            if kind == "done":
                self.step += 1
                return None
            self.messages.append({"role": "user", "content": [{"type": "text", "text":
                                  f"That reply was not a valid call: {val}. Reply with one JSON object."}]})
        self.error = f"no valid call after {self.max_repairs + 1} replies"
        return None
