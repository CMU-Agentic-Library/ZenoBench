"""Turn a VLM answer into a call: the last JSON object with "skill" or "finish"."""

from __future__ import annotations

import json


class ParseError(ValueError):
    pass


def json_objects(text: str):
    dec = json.JSONDecoder()
    i = text.find("{")
    while i != -1:
        try:
            obj, end = dec.raw_decode(text, i)
        except json.JSONDecodeError:
            i = text.find("{", i + 1)
            continue
        if isinstance(obj, dict):
            yield obj
        i = text.find("{", end)


def parse_call(text: str) -> dict | None:
    """{"skill", "args"} for a call, None for finish; ParseError if neither is there."""
    found = [o for o in json_objects(text or "") if "skill" in o or "finish" in o]
    if not found:
        raise ParseError("no JSON object with \"skill\" or \"finish\"")
    obj = found[-1]
    if obj.get("finish"):
        return None
    skill = obj.get("skill")
    args = obj.get("args", {})
    if not isinstance(skill, str) or not skill:
        raise ParseError('"skill" must be a skill name')
    if not isinstance(args, dict):
        raise ParseError('"args" must be an object')
    return {"skill": skill, "args": args}


def thought(text: str, limit=400) -> str:
    t = (text or "").split("{", 1)[0].strip()
    return t.removeprefix("Thought:").strip()[:limit]
