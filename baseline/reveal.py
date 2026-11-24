"""Reveal the object/furniture registry to the planner (ablation switch, 11-24).

    SHIFT_REVEAL=off       default: the planner sees no registry facts (main results)
    SHIFT_REVEAL=objects   facts about every KIND of object the robot has observed so far
    SHIFT_REVEAL=full      the same, plus what each known surface is for (furniture affordances, headroom)

What is revealed is kind-level registry knowledge only, gated by the observation:
- only kinds of objects already in the observation (visible now or seen before): nothing about objects the
  robot has not found, nor where anything is;
- what a kind is (category), what it can be used for (affordances), its material facts and size, a
  container's opening and depth, and whether the robot can grasp it;
- never instance state (which one is in use or full), never the task's requirements, the ideal, a role,
  a stand-in, or whether something is a legal substitute: deciding that is still the planner's job.

The facts come from benchmark/v6/registry (object_registry.py), the same registry the evaluation's affordance
check uses.  Every planner logs the mode in result.json (BaselinePlanner.summary).
"""
from __future__ import annotations

import os
from pathlib import Path

MODES = ("off", "objects", "full")

# short readable phrases for the registry's affordance tokens (registry/objects.yaml, furniture.yaml)
PHRASE = {
    "contain_solid": "holds small items inside", "hold_liquid": "holds liquid", "serve_food": "eaten from",
    "drink_from": "drunk from", "cover_opening": "can lie flat over an opening", "support_items": "things rest on it",
    "carry_multiple": "carries several items at once", "store_items": "storage box", "dispose": "rubbish goes in",
    "cook_in": "cooks food on the stove", "scoop": "eats or stirs", "wipe": "wipes spills", "write": "writes",
    "write_on": "written in", "read": "read", "stack_on": "another piece can stand on it",
    "stack_top": "can stand on top of a stack", "play": "a toy", "edible": "food", "drinkable": "a drink",
    "wipe_tissue": "tissues",
    "dining_surface": "dining table", "serve_meal": "people sit at it to eat", "food_prep": "kitchen work top",
    "work_surface": "work or study top", "display": "on show to the room", "living_serve": "within reach of a seated guest",
    "store_open": "open shelf", "store_books": "books are kept here", "store_closed": "storage behind a door",
    "kitchen_storage": "kitchen storage (dishes, dry food)", "store_food_cold": "keeps food cold",
    "heat_stove": "heats a pot set on it", "heat_microwave": "heats a dish put inside", "sleep": "a bed",
}
ATTR = {"breakable": ("breakable", "unbreakable"), "food_safe": ("food-safe", "not for food"),
        "microwave_safe": ("microwave-safe", "not for the microwave"), "stove_safe": ("stove-safe", "not for the stove"),
        "for_kids": ("made for children", None), "has_handle": ("has a handle", None), "lidded": ("has its own lid", None)}

SYSTEM_NOTE = {
    "objects": "- Object facts: for each kind of object you have observed, the observation also lists what that "
               "kind is, what it can be used for, its material and its size (from a household object registry).\n",
    "full": "- Object and place facts: for each kind of object you have observed, the observation also lists "
            "what that kind is, what it can be used for, its material and its size; each known surface also "
            "says what it is for (from a household object and furniture registry).\n",
}


def mode() -> str:
    m = (os.environ.get("SHIFT_REVEAL") or "off").strip().lower()
    if m not in MODES:
        raise ValueError(f"SHIFT_REVEAL={m!r}: one of {', '.join(MODES)}")
    return m


def _registry():
    from benchmark.v6 import object_registry
    return object_registry


def _cm(x: float) -> str:
    return f"{round(x * 100)}"


def kind_line(kind: str) -> str | None:
    R = _registry()
    if kind not in R.objects_yaml()["objects"] or kind not in R.assets_json():
        return None
    f = R.obj(kind)
    t, g, a = f["taxonomy"], f["geometry"], f["attributes"]
    uses = ", ".join(PHRASE.get(x, x.replace("_", " ")) for x in f["affordances"]) or "no particular use"
    attrs = [a["material"]] if a.get("material") else []
    for k, (yes, no) in ATTR.items():
        if k in a:
            s = yes if a[k] else no
            if s:
                attrs.append(s)
    size = "x".join(_cm(x) for x in g["size_m"]) + " cm"
    if "opening_m" in g:
        size += f", opening {_cm(g['opening_m'][0])}x{_cm(g['opening_m'][1])} cm, {_cm(g['depth_m'])} cm deep"
    grasp = "" if g["graspable_by_zeno"] else "; the robot cannot grasp it"
    return f"- {kind} ({t['category']}/{t['subcategory']}): {uses}; {', '.join(attrs)}; {size}{grasp}"


def object_section(obs: dict) -> str:
    """Facts for every kind among the observed objects ('' when the switch is off or nothing is observed)."""
    if mode() == "off":
        return ""
    kinds = []
    for o in (obs.get("visible_objects") or []) + (obs.get("observation_cache") or []):
        k = o.get("category")
        if k and k not in kinds:
            kinds.append(k)
    lines = [x for x in (kind_line(k) for k in sorted(kinds)) if x]
    return ("Object facts (per kind observed):\n" + "\n".join(lines)) if lines else ""


def place_tags(name: str) -> str:
    """What a known surface is for, in mode full ('' otherwise or for a non-surface)."""
    return surface_tags(name) if mode() == "full" else ""


def surface_tags(name: str) -> str:
    R = _registry()
    s = R.surfaces().get(name)
    if not s:
        return ""
    g = s["geometry"]
    uses = ", ".join(PHRASE.get(x, x) for x in s["affordances"]) or "-"
    bits = [uses, f"{g['size_m'][0]:.2f}x{g['size_m'][1]:.2f} m"]
    if g.get("clearance_m") is not None and g["clearance_m"] < 1.0:
        bits.append(f"headroom {g['clearance_m']:.2f} m")
    if g.get("behind_door"):
        bits.append("behind a door")
    return "; ".join(bits)


def system_note() -> str:
    return SYSTEM_NOTE.get(mode(), "")


# -- the card: the same text as a static file, for planners outside this repo (Graph Manager vendors it) --
CARD = Path(__file__).resolve().parent / "reveal_card.json"


def card() -> dict:
    R = _registry()
    return {"schema_version": 1, "kind": "reveal_card",
            "note": "generated by python -m baseline.reveal from benchmark/v6/registry; do not edit",
            "system_note": SYSTEM_NOTE,
            "objects": {k: kind_line(k) for k in sorted(R.objects_yaml()["objects"])},
            "surfaces": {n: surface_tags(n) for n in sorted(R.surfaces())}}


def main(argv=None) -> int:
    import json
    import sys
    argv = sys.argv[1:] if argv is None else argv
    text = json.dumps(card(), indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        ok = CARD.exists() and CARD.read_text() == text
        print("reveal card up to date" if ok else "stale: python -m baseline.reveal")
        return 0 if ok else 1
    CARD.write_text(text)
    print(f"wrote {CARD.name}: {len(card()['objects'])} kinds, {len(card()['surfaces'])} surfaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
