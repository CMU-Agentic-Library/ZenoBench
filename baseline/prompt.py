"""Text the VLM planners share: the skill menu, the observation, the call history.

Only what the episode's observation holds goes into the prompt (sticky/benchmark: head image,
visible objects, observation cache, known places, robot state, last result; names anonymized).
Nothing here reads the task's goal, variant or GT state.
"""

from __future__ import annotations

import json

SYSTEM_TEMPLATE = """\
You control a household mobile robot with two arms through a fixed set of skills.
You are given a household instruction. Carry it out by calling skills, one call at a time.

Each turn you see: the instruction, the robot's current observation (a head-camera image, the \
objects it can see now, the objects it has seen before and where, the static places it knows, \
its own state) and the calls made so far with their results.

Rules:
- Objects you have observed are named <category>_<k> (for example mug_1). Use only names that \
appear in the observation or the known places; an object the robot has not observed yet cannot be \
used until it is found (move to or look at places to find things).
- A call can fail; read its error and decide what to do next.
- You have at most {max_calls} skill calls in total, failed and refused calls included.
- When the instruction is done, or you decide it cannot be done, finish.
{extra}
Answer format: first one or two short sentences of reasoning starting with "Thought:", then a \
single JSON object on its own, either
{{"skill": "<skill name>", "args": {{"<parameter>": <value>, ...}}}}
or
{{"finish": true, "reason": "<short reason>"}}

Skills (name(parameters) - description; pre: preconditions; eff: effects; "?" marks an optional \
parameter):
{menu}
"""

SUBSTITUTION_HINT = """\
- If something the instruction asks for is not available or cannot be done, you may complete the \
request in another reasonable way that serves the same purpose (for example a similar object or \
place). Prefer exactly what was asked whenever it is possible; do not change the request without \
a reason.
"""


def render_menu(skills) -> str:
    lines = []
    for s in skills:
        params = []
        for p, spec in (s.get("parameters") or {}).items():
            opt = "" if spec.get("required") else "?"
            dflt = f"={json.dumps(spec['default'])}" if "default" in spec else ""
            params.append(f"{p}{opt}: {spec.get('type', 'any')}{dflt}")
        line = f"- {s['name']}({', '.join(params)}) - {s.get('description', '').strip()}"
        pdesc = [f"{p}: {spec['description']}" for p, spec in (s.get("parameters") or {}).items()
                 if spec.get("description")]
        if pdesc:
            line += " Params: " + "; ".join(pdesc) + "."
        if s.get("preconditions"):
            line += " pre: " + ", ".join(s["preconditions"]) + "."
        if s.get("effects"):
            line += " eff: " + ", ".join(s["effects"]) + "."
        lines.append(line)
    return "\n".join(lines)


def system_prompt(skills, max_calls, substitution_hint=False) -> str:
    return SYSTEM_TEMPLATE.format(max_calls=max_calls, menu=render_menu(skills),
                                  extra=SUBSTITUTION_HINT if substitution_hint else "")


def _j(v) -> str:
    return json.dumps(v, separators=(",", ":"), ensure_ascii=False, default=str)


def _obj(o) -> str:
    where = [f"on {o['last_seen_on']}" if o.get("last_seen_on") else "",
             f"in {o['last_seen_in']}" if o.get("last_seen_in") else ""]
    pos = o.get("last_seen_position")
    bits = [o["name"], f"({o.get('category')})" if o.get("category") else "",
            " ".join(w for w in where if w),
            f"at {[round(float(x), 2) for x in pos]}" if pos else "",
            "HELD" if o.get("held") else ""]
    return "- " + " ".join(b for b in bits if b)


def render_places(places) -> str:
    rooms: dict[str, list[str]] = {}
    for name, rec in sorted((places or {}).items()):
        kind = rec.get("kind", "")
        if kind == "room":
            rooms.setdefault(name, [])
            continue
        extra = [kind, rec.get("category") or ""]
        if "z" in rec:
            extra.append(f"z={rec['z']:.2f}")
        if rec.get("articulated"):
            extra.append(f"opens ({rec.get('joint')})")
        rooms.setdefault(rec.get("room") or "?", []).append(f"{name} [{', '.join(e for e in extra if e)}]")
    return "\n".join(f"- {r}: " + "; ".join(v) for r, v in rooms.items())


def render_observation(obs: dict) -> str:
    out = []
    if "robot" in obs:
        out.append("Robot: " + _j(obs["robot"]))
    vis = obs.get("visible_objects") or []
    out.append("Visible now:\n" + ("\n".join(_obj(o) for o in vis) if vis else "- (nothing)"))
    vis_names = {o["name"] for o in vis}
    seen = [o for o in obs.get("observation_cache") or [] if o["name"] not in vis_names]
    if seen:
        out.append("Seen before (last known):\n" + "\n".join(_obj(o) for o in seen))
    if "objects" in obs:                                   # privileged profile only (GT object list)
        out.append("All task objects (ground truth):\n" + "\n".join(
            f"- {o['name']} ({o.get('kind')}) at {o.get('position')}" for o in obs["objects"]))
    if "task_status" in obs:
        out.append("Goal status: " + _j(obs["task_status"]))
    if obs.get("known_places"):
        out.append("Known places by room:\n" + render_places(obs["known_places"]))
    return "\n\n".join(out)


def result_line(res, limit=300) -> str:
    if not res:
        return "(no result)"
    if res.get("success"):
        s = "OK"
        outs = res.get("outputs")
        if outs:
            s += " " + _j(outs)[:limit]
        if res.get("now_visible"):
            s += " now visible: " + ", ".join(map(str, res["now_visible"]))
        return s
    return f"FAILED {res.get('error_code')}: {str(res.get('error'))[:limit]}"


def render_history(history, keep_full=8) -> str:
    """history: [{"skill", "args", "result"}]; the last ``keep_full`` calls in full, older ones short."""
    if not history:
        return "(no calls yet)"
    lines = []
    cut = max(0, len(history) - keep_full)
    for i, h in enumerate(history):
        call = f"{i + 1}. {h['skill']}({_j(h.get('args', {}))[1:-1]})"
        res = h.get("result")
        if i < cut:
            lines.append(f"{call} -> {'OK' if res and res.get('success') else 'FAILED ' + str((res or {}).get('error_code'))}")
        else:
            lines.append(f"{call} -> {result_line(res)}")
    return "\n".join(lines)


def user_prompt(instruction, obs, history, calls_used, max_calls, note="") -> str:
    parts = [f"Instruction: {instruction}",
             f"Calls used: {calls_used} of {max_calls}",
             "Calls so far:\n" + render_history(history),
             "Current observation (the image is the head camera now):\n" + render_observation(obs)]
    if note:
        parts.append(note)
    parts.append("What is the next call?")
    return "\n\n".join(parts)


def image_paths(obs) -> list[str]:
    return [im["path"] for im in obs.get("images") or [] if im.get("path")]
