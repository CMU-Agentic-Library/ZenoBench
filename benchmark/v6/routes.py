"""Small helpers over oracle routes and goals, shared by the v6 scripts."""
from __future__ import annotations

ACTION_KINDS = ("grasp", "slip", "placement", "ik")
MANIP = {"place", "drop", "stack", "collect", "hide", "heat", "cover", "flip", "roll", "wipe", "inspect", "stir",
         "fetch", "clear", "close", "pick", "open", "uncover", "push", "separate", "expose", "pull", "regrasp",
         "tip", "upright", "center", "lift", "lower", "rotate", "knock"}
SUBJ = {"on", "inside", "fully_inside", "on_top_of", "flipped", "object_rolled", "hidden", "covered",
        "temperature_at_least", "observed", "stirred", "wiped", "grouped", "is_closed"}


def ok(s):
    return s.get("expect") != "fail"


def vals(step):
    out = set()
    for v in step["args"].values():
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, str):
                out.add(x)
    return out


def holding(steps, i):
    """(object held, two-handed) before step i (only steps that succeed change the hand)."""
    held, two = None, False
    for s in steps[:i]:
        if not ok(s):
            if s["skill"] == "navigate":
                held, two = None, False             # a carry that fails is a slip: the object is on its support again
            continue
        if s["skill"] == "pick":
            held, two = s["args"]["object"], s["args"].get("hands") == "both"
        elif s["skill"] in ("place", "drop", "stack", "hide") and s["args"].get("object") == held:
            held, two = None, False
    return held, two


def trig_hits(steps, f):
    """Indices of the route steps a failure's trigger matches (every call, nth ignored)."""
    t = f.get("trigger") or {}
    out = []
    for i, s in enumerate(steps):
        if s["skill"] != t.get("skill"):
            continue
        if any(s["args"].get(k) != v for k, v in (t.get("args") or {}).items()):
            continue
        if t.get("while_holding"):
            h, two = holding(steps, i)
            if h != t["while_holding"] or (t.get("one_handed") and two):
                continue
        out.append(i)
    return out


def goal_atoms(goal):
    return list(goal.get("all", [])) + [a for g in goal.get("any", []) for a in g]


def subjects(goal):
    out = set()
    for a in goal_atoms(goal):
        if a[0] in SUBJ and len(a) > 1:
            for x in (a[1] if isinstance(a[1], list) else [a[1]]):
                if isinstance(x, str):
                    out.add(x)
    return out
