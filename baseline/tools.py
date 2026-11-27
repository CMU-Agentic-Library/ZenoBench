"""The skill menu as OpenAI tool definitions, for a local vLLM server's constrained decoding (11-26).

baseline/serve_qwen.sh starts vLLM with ``--tool-strict-level=parameter``: every tool's argument schema is
enforced while decoding.  The schemas pin the name slots whose valid values the planner already knows from
its observation: surfaces (``receptacle_ref`` / ``support_ref``: the exact ``<furniture>/<surface>`` names of
the known places, plus the observed objects for a receptacle), containers (observed objects), rooms.  Object
slots stay free text (a search takes a kind word, an object can be named before its next sighting).  The
menu text in the system prompt is unchanged; ``finish`` is one more tool.

    tools = tool_schemas(skills, observation)
    text, usage = client.chat(system, user, images, tools=tools)   # tool call -> {"skill", "args"} JSON text
"""
from __future__ import annotations

FINISH = {"type": "function", "function": {
    "name": "finish", "description": "End the episode: the task is done, or it cannot be done.",
    "parameters": {"type": "object", "properties": {"reason": {"type": "string"}},
                   "required": ["reason"], "additionalProperties": False}}}

_NUM = {"type": "number"}
_SCHEMA = {"number": _NUM, "positive_number": _NUM,
           "xy": {"type": "array", "items": _NUM, "minItems": 2, "maxItems": 2},
           "unit_vec2": {"type": "array", "items": _NUM, "minItems": 2, "maxItems": 2},
           "pose2d": {"type": "array", "items": _NUM, "minItems": 3, "maxItems": 3},
           "object_list": {"type": "array", "items": {"type": "string"}, "minItems": 1},
           "category_map": {"type": "object"}}


def known_names(observation: dict) -> dict:
    """{"surfaces", "objects", "rooms"} the observation names (nothing beyond it)."""
    places = observation.get("known_places") or {}
    objs = [o["name"] for o in (observation.get("visible_objects") or []) + (observation.get("observation_cache") or [])]
    robot = observation.get("robot") or {}
    objs += [robot[k] for k in ("held_right", "held_left") if isinstance(robot.get(k), str)]
    return {"surfaces": sorted(n for n, r in places.items() if r.get("kind") == "support"),
            "objects": sorted(set(objs)),
            "rooms": sorted(n for n, r in places.items() if r.get("kind") == "room")}


def _param(spec: dict, names: dict) -> dict:
    t = spec.get("type")
    out = dict(_SCHEMA.get(t, {"type": "string"}))
    enum = spec.get("enum")
    if not enum:
        enum = {"receptacle_ref": names["surfaces"] + names["objects"], "support_ref": names["surfaces"],
                "container_ref": names["objects"], "room_ref": names["rooms"]}.get(t)
    if enum:
        out["enum"] = list(dict.fromkeys(enum))
    if spec.get("description"):
        out["description"] = spec["description"]
    return out


def tool_schemas(skills, observation) -> list[dict]:
    names = known_names(observation)
    tools = []
    for s in skills:
        params = s.get("parameters") or {}
        tools.append({"type": "function", "function": {
            "name": s["name"], "description": (s.get("description") or "")[:1024],
            "parameters": {"type": "object", "properties": {p: _param(sp, names) for p, sp in params.items()},
                           "required": [p for p, sp in params.items() if sp.get("required")],
                           "additionalProperties": False},
            "strict": True}})
    return tools + [FINISH]


def call_text(name: str, args: dict) -> str:
    """A tool call as the JSON answer the text parser reads."""
    import json
    if name == "finish":
        return json.dumps({"finish": True, "reason": (args or {}).get("reason", "")})
    return json.dumps({"skill": name, "args": args or {}})
