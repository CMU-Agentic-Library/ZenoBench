"""Object and furniture registry (11-24; classification only since 11-25).

registry/objects.yaml and registry/furniture.yaml give the category and subcategory of every movable asset kind
and every furniture type of v6.  Surfaces get their room from the scene annotations.  Used by taxonomy.py (the
object-category axis) and substitution_eval.py (layout_objects).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REG = HERE / "registry"


# -- loading -----------------------------------------------------------------------------------------------
@lru_cache(None)
def objects_yaml() -> dict:
    return yaml.safe_load((REG / "objects.yaml").read_text())


@lru_cache(None)
def furniture_yaml() -> dict:
    return yaml.safe_load((REG / "furniture.yaml").read_text())


@lru_cache(None)
def assets_json() -> dict:
    return json.loads((ROOT / "annotations" / "assets.json").read_text())


@lru_cache(None)
def tasks_json() -> dict:
    return json.loads((HERE / "tasks.json").read_text())


@lru_cache(None)
def scene_bases() -> tuple:
    return tuple(sorted({t["scene"]["base"] for t in tasks_json()["tasks"]}))


@lru_cache(None)
def annotation(base: str) -> dict:
    return json.loads((ROOT / base / "annotation.json").read_text())


# -- object facts --------------------------------------------------------------------------------------------
@lru_cache(None)
def obj(kind: str) -> dict:
    """Registry entry of an asset kind."""
    return {"kind": kind, "taxonomy": dict(objects_yaml()["objects"][kind])}


# -- furniture facts -----------------------------------------------------------------------------------------
def _in_tri(p, tri) -> bool:
    (x, y), (a, b, c) = p, tri
    if abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) < 1e-9:
        return False                                     # a degenerate triangle of the room mesh
    def s(p1, p2):
        return (x - p2[0]) * (p1[1] - p2[1]) - (p1[0] - p2[0]) * (y - p2[1])
    d1, d2, d3 = s(a, b), s(b, c), s(c, a)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def _room(rooms: dict, xy) -> str | None:
    for name, r in rooms.items():
        if any(_in_tri(xy, tri) for tri in r.get("triangles", [])):
            return name
    return None


def _type_spec(furniture: str, ftype: str) -> dict:
    spec = furniture_yaml()["types"][ftype]
    if "same_as" in spec:
        spec = furniture_yaml()["types"][spec["same_as"]]
    inst = spec.get("instances") or {}
    for prefix in sorted(inst, key=len, reverse=True):
        if furniture.startswith(prefix):
            return inst[prefix]
    return {"category": spec["category"], "subcategory": spec["subcategory"]}


@lru_cache(None)
def surfaces() -> dict:
    """Every support surface of every v6 scene: name -> facts (the first scene that has it gives the geometry)."""
    out = {}
    for base in scene_bases():
        a = annotation(base)
        for s in a["supports"]:
            if s["name"] in out:
                continue
            furn, part = s["name"].split("/", 1)
            x0, y0, x1, y1 = s["aabb_xy"]
            out[s["name"]] = {"surface": s["name"], "furniture": furn, "type": s["category"],
                              "taxonomy": dict(_type_spec(furn, s["category"])),
                              "room": _room(a["rooms"], ((x0 + x1) / 2, (y0 + y1) / 2))}
    return out


def surface(name: str) -> dict:
    return surfaces()[name]


def room_type(room: str | None) -> str | None:
    return room.rsplit("_", 2)[0] if room else None


# -- layouts -------------------------------------------------------------------------------------------------
def layout_objects(t: dict, v: dict) -> dict:
    """Object name -> {kind, support, xy} at the layout's start (removed objects left out)."""
    out = {}
    for o in annotation(t["scene"]["base"])["objects"]:
        out[o["name"]] = {"kind": o["asset"], "support": o.get("support"), "xy": o["position"][:2]}
    for src in (t["scene"].get("add") or {}, v.get("add") or {}):
        for k, x in src.items():
            out[k] = {"kind": x["asset"], "support": x.get("support"), "xy": x.get("xy")}
    for src in (t["scene"].get("move") or {}, v.get("move") or {}):
        for k, x in src.items():
            if k in out and isinstance(x, dict):
                upd = {f: x[f] for f in ("support", "xy") if x.get(f) is not None}
                if x.get("xy") is not None and "support" in x and x["support"] is None:
                    upd["support"] = None                # placed by position: it rests on another object
                out[k] = {**out[k], **upd}
    for k in set(t["scene"].get("remove", [])) | set(v.get("remove", [])):
        out.pop(k, None)
    return out


# -- check ---------------------------------------------------------------------------------------------------
CATEGORIES = {"tableware", "cookware", "food_container", "container", "food", "stationery", "toy", "cleaning",
              "furniture", "appliance"}


def check_vocab() -> list[str]:
    """Every category is one of CATEGORIES and every entry has a subcategory; returns problems."""
    entries = [(k, v) for k, v in objects_yaml()["objects"].items()]
    for t, spec in furniture_yaml()["types"].items():
        if "same_as" not in spec:
            entries.append((t, spec))
            entries += list((spec.get("instances") or {}).items())
    return [k for k, v in entries if v.get("category") not in CATEGORIES or not v.get("subcategory")]
