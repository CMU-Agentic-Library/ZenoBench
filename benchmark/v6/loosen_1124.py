"""11-24 loosening of every v6 success condition (user, after the first VLM baseline review): the object state
decides, never how the robot ends up, and every reasonable reading of the instruction counts.

Applied by define_tasks_v6.build() after scoring.attach_scoring, to the task goal, every layout's goal and every
tier goal:

1. ``hand_empty`` goes: an object put where it belongs counts even while the gripper still touches it.
2. ``near_start`` ("left where it was") allows at least 10 cm, so a nudge from the arm passing by does not fail;
   only moving a thing away on purpose does.
3. ``is_closed`` (a door shut again) stays only when the instruction asks to close it.
4. A substitute that is one named object counts for every object of its kind in the house (SUBSTITUTE_KINDS):
   any plate covers the pot, any free bowl carries the apple.  Only the stand-in that is chosen widens, never the
   object the task is about (another spoon on the counter does not pick up the dropped one).
5. A place the instruction leaves open counts for every place that fits it (PLACES): "the dining table" is
   either dining table, "bring a bowl over" for the soup also reaches the dining tables, the guest's drink
   either TV stand, an apple put away also into a cabinet or the fridge (ATOM_ALTERNATIVES).
6. Tier texts: the generic labels of 11-20 and the best tier's text of every layout without the ideal are
   rewritten from the goal itself; every tier carries ``check``, the goal in short.

benchmark/v6/LOOSEN_1124_zh.md records the decision, the checks and the per-layout stand-ins.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NEAR_START_MIN = 0.10
POSITIVE = {"on", "on_any", "inside", "fully_inside", "covered", "upright", "grouped", "count_on_at_least",
            "on_top_of", "near_any", "hidden", "temperature_at_least", "stirred", "wiped"}

# task prefix -> {named stand-in: asset kinds whose free objects stand in as well}
SUBSTITUTE_KINDS = {
    "T09": {"lid_plate": ["breakfast_plate"]},
    "T13": {"bowl": ["breakfast_bowl"], "cup": ["breakfast_cup"], "mug": ["breakfast_mug"]},
    "T15": {"plate_counter_a": ["breakfast_plate"], "plate_counter_b": ["breakfast_plate"]},
    "T16": {"spare_bowl": ["breakfast_bowl"]},
    "T17": {"cover_plate": ["breakfast_plate"]},
    # a clean bowl from elsewhere in the house serves soup better than the glass box or a mug
    "T18": {"spare_mug": ["breakfast_mug", "breakfast_bowl"], "glass_box": ["breakfast_bowl"]},
}
# names of a kind that hold food or are in use: never a free stand-in
IN_USE = ("oatmeal", "used", "soup", "full", "leftover", "example", "stew", "kid")

DINING = {"dining_table_2/top": ["dining_table_1/top"], "dining_table_1/top": ["dining_table_2/top"]}
# (task prefix, design or "*") -> {support: more supports that fit the instruction}
PLACES = {
    ("T13", "dishes_on_tv_stand"): DINING, ("T13", "no_cup"): DINING,
    ("T18", "*"): DINING, ("T20", "*"): DINING,
    ("T21", "tissue_on_tv_stand"): DINING, ("T21", "no_tissue"): DINING,
    ("T30", "*"): {"kitchen_island/top": ["dining_table_1/top", "dining_table_2/top"]},
    **{("T25", d): {"tv_stand_2/top": ["tv_stand_1/top"]}
       for d in ("drink_on_island", "cup_elsewhere", "cold_one", "drink_in_fridge", "two_guests", "little_guest")},
}
_CABINETS = [f"kitchen_cabinet_{k}/{s}" for k in (1, 2, 4, 5, 6) for s in ("inside_shelf", "inside_bottom")]
_KITCHEN_STORE = ["breakfast_fridge/inside_shelf", "kitchen_cabinet_4/inside_shelf", "kitchen_cabinet_6/inside_shelf"]
# (task prefix, design) -> [(atom, alternative atoms)]: "put away" reaches every storage place for it
ATOM_ALTERNATIVES = {
    ("T11", "fruits_on_table"): [(["inside", "apple", "serving_tray"], [["on_any", "apple", _CABINETS]])],
    ("T11", "basket_missing"): [(["inside", "apple", "serving_tray"], [["on_any", "apple", _CABINETS]])],
    # T22 tray_elsewhere: its basket_missing layout keeps the apple in the fruit tray instead of the west tray
    ("T22", "tray_elsewhere"): [(["fully_inside", "bought_apple", "west_tray"], [["on_any", "bought_apple", _KITCHEN_STORE]]),
                                (["inside", "bought_apple", "fruit_tray"], [["on_any", "bought_apple", _KITCHEN_STORE]])],
}


# -- goal plumbing --------------------------------------------------------------------------------------------
def _branches(g):
    """A goal as a list of conjunctions (all + each any-branch)."""
    alls = list(g.get("all", []))
    return [alls + list(b) for b in g["any"]] if g.get("any") else [alls]


def _from_branches(brs):
    """Conjunctions back to {"all", "any"}: atoms shared by every branch go to all."""
    uniq, seen = [], set()
    for b in brs:
        bb, s = [], set()
        for a in b:
            k = json.dumps(a)
            if k not in s:
                s.add(k)
                bb.append(a)
        key = json.dumps(sorted(json.dumps(a) for a in bb))
        if key not in seen:
            seen.add(key)
            uniq.append(bb)
    if not uniq:
        return {"all": []}
    common = [a for a in uniq[0] if all(json.dumps(a) in {json.dumps(x) for x in b} for b in uniq[1:])]
    ck = {json.dumps(a) for a in common}
    rest = [[a for a in b if json.dumps(a) not in ck] for b in uniq]
    out = {"all": common}
    if len(uniq) > 1 and all(rest):
        out["any"] = rest
    return out


def _sub_name(x, old, new):
    if isinstance(x, str):
        return new if x == old else x
    if isinstance(x, list):
        return [_sub_name(y, old, new) for y in x]
    return x


def _sub_atom(a, old, new):
    return [a[0], *(_sub_name(x, old, new) for x in a[1:])] if a[0] in POSITIVE else a


def _mentions(a, name):
    return a[0] in POSITIVE and name in json.dumps(a[1:])


def _holds_at_start(a, start):
    """A placement atom the layout's start already satisfies (an alternative must not make the goal free)."""
    if a[0] == "on":
        return start.get(a[1]) == a[2]
    if a[0] == "on_any":
        objs = [a[1]] if isinstance(a[1], str) else a[1]
        return any(start.get(o) in a[2] for o in objs)
    if a[0] == "count_on_at_least":
        return sum(start.get(o) == a[2] for o in a[1]) >= a[3]
    return False


def _expand(brs, old, alts, start=None):
    """Every branch that places ``old`` again with each alternative in its place (consistently in the branch);
    an alternative whose placement already holds at the start is left out."""
    out = []
    for b in brs:
        out.append(b)
        if any(_mentions(a, old) for a in b):
            for n in alts:
                nb = [_sub_atom(a, old, n) for a in b]
                changed = [x for x, y in zip(nb, b) if x != y]
                if not any(_holds_at_start(x, start or {}) for x in changed):
                    out.append(nb)
    return out


def _atom_alt(brs, atom, alts):
    k = json.dumps(atom)
    out = []
    for b in brs:
        out.append(b)
        if any(json.dumps(a) == k for a in b):
            out += [[x for a in b for x in ([alt] if json.dumps(a) == k else [a])] for alt in alts]
    return out


def _referenced(goals):
    names = set()
    for g in goals:
        for b in _branches(g):
            for a in b:
                for x in a[1:]:
                    names |= {x} if isinstance(x, str) else ({y for y in x if isinstance(y, str)}
                                                             if isinstance(x, list) else set())
    return names


# -- the rules ------------------------------------------------------------------------------------------------
def _basic(g, instruction):
    keep_closed = "close" in instruction.lower()
    def fix(a):
        if a[0] == "hand_empty" or (a[0] == "is_closed" and not keep_closed):
            return None
        if a[0] == "near_start":
            a = [a[0], a[1], max(float(a[2]), NEAR_START_MIN), *([max(float(a[3]), NEAR_START_MIN)] if len(a) > 3 else [])]
        return a
    brs = [[x for x in (fix(a) for a in b) if x is not None] for b in _branches(g)]
    return [[]] if any(not b for b in brs) else brs     # a branch left empty holds always (checked: none is)


def _kinds(t, v, cache={}):
    base = t["scene"]["base"]
    if base not in cache:
        cache[base] = {o["name"]: o["asset"] for o in json.loads((ROOT / base / "annotation.json").read_text())["objects"]}
    kinds = dict(cache[base])
    for src in (t["scene"].get("add") or {}, v.get("add") or {}):
        kinds.update({k: x["asset"] for k, x in src.items()})
    gone = set(t["scene"].get("remove", [])) | set(v.get("remove", [])) | set(t["scene"].get("distractors", []))
    return {n: k for n, k in kinds.items() if n not in gone}


def _starts(t, v, cache={}):
    """Object -> the support it starts on in this layout (the layout draw keeps every object on its support)."""
    base = t["scene"]["base"]
    if base not in cache:
        cache[base] = {o["name"]: o.get("support") for o in json.loads((ROOT / base / "annotation.json").read_text())["objects"]}
    out = dict(cache[base])
    for src in (t["scene"].get("add") or {}, t["scene"].get("move") or {}, v.get("add") or {}, v.get("move") or {}):
        out.update({k: x.get("support") for k, x in src.items() if isinstance(x, dict) and x.get("support")})
    return out


def _match(table, tid, design):
    for (p, d), x in table.items():
        if tid.startswith(p) and (d == "*" or d == design or design.startswith(d + "__") or design == d):
            yield x


def loosen_goal(g, t, v, design, instruction, stand_ins=None):
    """One goal through rules 1-5.  ``stand_ins``: {name: [alternatives]} for rule 4 (computed per layout)."""
    if g is None or not isinstance(g, dict) or "by_layout" in g or "drop" in g:
        return g
    brs = _basic(g, instruction)
    start = _starts(t, v)
    for old, alts in (stand_ins or {}).items():
        brs = _expand(brs, old, alts, start)
    for places in _match(PLACES, t["task_id"], design):
        for sup, more in places.items():
            brs = _expand(brs, sup, more, start)
    for pairs in _match(ATOM_ALTERNATIVES, t["task_id"], design):
        for atom, alts in pairs:
            brs = _atom_alt(brs, atom, alts)
    return _from_branches(brs)


def stand_ins_for(t, v, goals):
    table = next((x for p, x in SUBSTITUTE_KINDS.items() if t["task_id"].startswith(p)), {})
    if not table:
        return {}
    kinds = _kinds(t, v)
    used = _referenced(goals)
    out = {}
    for name, ks in table.items():
        if name not in used:
            continue
        alts = sorted(n for n, k in kinds.items() if k in ks and n != name and n not in used
                      and not any(w in n for w in IN_USE))
        if alts:
            out[name] = alts
    return out


# -- tier texts -----------------------------------------------------------------------------------------------
def _short(a):
    def s(x):
        if isinstance(x, list):
            return "[" + "|".join(map(str, x[:6])) + ("|..." if len(x) > 6 else "") + "]"
        return str(x)
    return f"{a[0]}({', '.join(s(x) for x in a[1:])})"


def check_text(g):
    """The goal in short: what must hold (stay-put atoms summed up)."""
    if not g:
        return ""
    brs = _branches(g)
    stay = sorted({a[1] if isinstance(a[1], str) else "+".join(a[1]) for b in brs for a in b if a[0] == "near_start"})
    def body(b):
        return " & ".join(_short(a) for a in b if a[0] != "near_start")
    common = {json.dumps(a) for a in brs[0] if a[0] != "near_start"}
    for b in brs[1:]:
        common &= {json.dumps(a) for a in b}
    head = [json.loads(k) for k in sorted(common)]
    parts = [" & ".join(_short(a) for a in head)] if head else []
    rest = list(dict.fromkeys(body([a for a in b if json.dumps(a) not in common]) for b in brs))
    rest = [r for r in rest if r]
    if rest:
        shown = rest[:4] + ([f"... {len(rest) - 4} more ways"] if len(rest) > 4 else [])
        parts.append("one of: " + " || ".join(shown))
    if stay:
        parts.append(f"left in place (10 cm): {', '.join(stay[:8])}" + (" ..." if len(stay) > 8 else ""))
    return "; ".join(parts)


_HAND = re.compile(r",?\s*(and\s+)?(with\s+)?the hand (is\s+)?empty", re.I)


def _stale(tier, design_best_why, ideal_present):
    w = tier.get("why", "")
    return "(11-20)" in w or (not ideal_present and tier["score"] == 1.0)   # the ideal's words, the ideal gone


# -- entry ----------------------------------------------------------------------------------------------------
def apply(out: dict) -> list:
    """Loosen every goal of the benchmark in place; returns [(task, layout, what changed)]."""
    log = []
    for t in out["tasks"]:
        design_of = {lid: d for d, info in t.get("v6_variants", {}).items() for lid in info["layouts"]}
        if t.get("goal"):
            t["goal"] = loosen_goal(t["goal"], t, {}, "", t["instruction"])
        for lid, v in t["variants"].items():
            design = design_of.get(lid, lid)
            instruction = v.get("instruction") or t["instruction"]
            sc = v.get("scoring") or {}
            goals = [v["goal"]] if v.get("goal") else []
            goals += [tr["goal"] for tr in sc.get("tiers", []) if isinstance(tr.get("goal"), dict)]
            subs = stand_ins_for(t, v, goals)
            before = json.dumps([v.get("goal"), [tr.get("goal") for tr in sc.get("tiers", [])]])
            if v.get("goal"):
                v["goal"] = loosen_goal(v["goal"], t, v, design, instruction, subs)
            info = t.get("v6_variants", {}).get(design, {})
            best_why = ((info.get("scoring") or {}).get("tiers") or [{}])[0].get("why")
            for tr in sc.get("tiers", []):
                tr["goal"] = loosen_goal(tr["goal"], t, v, design, instruction, subs)
                g = tr["goal"] if isinstance(tr["goal"], dict) and "drop" not in tr["goal"] else v.get("goal")
                tr["check"] = check_text(g)
                if _stale(tr, best_why, sc.get("ideal_present", True)):
                    tr["why"] = tr["check"]
                else:
                    tr["why"] = _HAND.sub("", tr["why"]).strip(" ,;")
            if sc:
                sc["loosened"] = "11-24"
                if subs:
                    sc["stand_ins"] = subs
            after = json.dumps([v.get("goal"), [tr.get("goal") for tr in sc.get("tiers", [])]])
            if before != after:
                log.append((t["task_id"], lid, subs))
    return log
