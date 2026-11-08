"""Skills removed from the library and what their route steps become in catalogs written before they left.

approach: the next skill chooses its own base park, so an approach right after a navigate to the same place is
dropped; any other approach still had to bring the base there and becomes that navigate (T08: approach the island
right after picking the sponge on the TV stand).  Used by benchmark/define_tasks_v3.py (routes it inherits from v2;
benchmark/tasks.json keeps them with its evidence) and benchmark/v6/define_tasks_v6.py (routes it inherits from v5
and its own designs).
"""
from __future__ import annotations

RETIRED_SKILLS = {"approach": ("navigate", "target", "destination")}


def _retired_step(step, prev):
    """None to drop a retired skill's step, else the step that replaces it."""
    skill, src, dst = RETIRED_SKILLS[step["skill"]]
    place = step["args"].get(src)
    if isinstance(prev, dict) and prev.get("skill") == skill and prev.get("args", {}).get(dst) == place:
        return None
    return {**step, "skill": skill, "args": {dst: place}}


def drop_retired_steps(x):
    """``x`` with every route step of a retired skill dropped or replaced (nested lists and dicts included)."""
    if isinstance(x, list):
        out = []
        for v in x:
            if isinstance(v, dict) and v.get("skill") in RETIRED_SKILLS and "args" in v:
                v = _retired_step(v, out[-1] if out else None)
                if v is not None:
                    out.append(v)
            else:
                out.append(drop_retired_steps(v))
        return out
    if isinstance(x, dict):
        return {k: drop_retired_steps(v) for k, v in x.items()}
    return x
