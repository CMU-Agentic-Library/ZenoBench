"""Object and furniture registry (11-24; affordance judging removed 11-25: the registry is for classification).

Data (hand-written, benchmark/v6/registry/):
  objects.yaml    every movable asset kind: taxonomy (category / subcategory), uses and attributes
  furniture.yaml  every furniture type and appliance: taxonomy, uses per surface kind

Geometry is never written by hand: objects from annotations/assets.json (the spawn source: size, mass, the
container opening and depth, graspability), surfaces from the scene annotations (height, size, headroom, room,
behind a door or not).  Used by taxonomy.py (categories), substitution_eval.py (layout_objects) and the
SHIFT_REVEAL ablation (baseline/reveal.py).
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
def _opening(a: dict) -> tuple[float, float, float]:
    """(wide, narrow, depth) of a container's top opening, in metres."""
    c = a.get("container")
    sx, sy, sz = a["size"]
    if not c:
        return sx - 0.01, sy - 0.01, sz - 0.005          # a solid-collider box or tray: its walls are thin
    band = max(c["bands"], key=lambda b: b[1])
    if c["shape"] == "round":
        w = n = 2 * band[2]
    else:                                                # rect: half extents; ellipse: semi-axes
        w, n = sorted((2 * band[2], 2 * band[3]), reverse=True)
    return w, n, c.get("rim_height", sz)


@lru_cache(None)
def obj(kind: str) -> dict:
    """Registry entry of an asset kind with its geometry."""
    spec = objects_yaml()["objects"][kind]
    a = assets_json()[kind]
    size = [round(x, 4) for x in a["size"]]
    geo = {"size_m": size, "mass_kg": a["mass"], "graspable_by_zeno": a["graspable_by_zeno"],
           "min_pinch_width_m": round(a["min_pinch_width"], 4)}
    if "contain_solid" in spec["affordances"]:
        w, n, d = _opening(a)
        geo["opening_m"] = [round(w, 4), round(n, 4)]
        geo["depth_m"] = round(d, 4)
    geo["portable"] = bool(a["graspable_by_zeno"] and max(size) <= 0.26 and a["mass"] <= 1.0)
    return {"kind": kind, "taxonomy": spec["taxonomy"], "affordances": list(spec["affordances"]),
            "attributes": dict(spec.get("attributes") or {}), "geometry": geo}


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
    return spec


def _surface_kind(part: str) -> str:
    return "top" if part == "top" else ("inside" if part.startswith("inside") else "shelf")


@lru_cache(None)
def surfaces() -> dict:
    """Every support surface of every v6 scene: name -> facts (the first scene that has it gives the geometry)."""
    out = {}
    for base in scene_bases():
        a = annotation(base)
        doors = {x["name"] for x in a.get("articulated", [])}
        for s in a["supports"]:
            if s["name"] in out:
                continue
            furn, part = s["name"].split("/", 1)
            spec = _type_spec(furn, s["category"])
            x0, y0, x1, y1 = s["aabb_xy"]
            kind = _surface_kind(part)
            out[s["name"]] = {
                "surface": s["name"], "furniture": furn, "type": s["category"], "taxonomy": spec["taxonomy"],
                "affordances": list(spec["surfaces"].get(kind, [])), "attributes": {},
                "geometry": {"height_m": round(s["z"], 3), "size_m": [round(x1 - x0, 3), round(y1 - y0, 3)],
                             "clearance_m": s.get("clearance"), "behind_door": kind == "inside" and furn in doors,
                             "room": _room(a["rooms"], ((x0 + x1) / 2, (y0 + y1) / 2))}}
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


# -- vocabulary ----------------------------------------------------------------------------------------------
def check_vocab() -> list[str]:
    """Affordances and attributes used anywhere must be in the vocabularies; returns problems."""
    bad = []
    ov = objects_yaml()["vocabulary"]
    for k, spec in objects_yaml()["objects"].items():
        bad += [f"{k}: affordance {a}" for a in spec["affordances"] if a not in ov["affordances"]]
        bad += [f"{k}: attribute {a}" for a in (spec.get("attributes") or {}) if a not in ov["attributes"]]
    fv = furniture_yaml()["vocabulary"]["affordances"]
    for t, spec in furniture_yaml()["types"].items():
        if "same_as" in spec:
            continue
        for s in [spec, *(spec.get("instances") or {}).values()]:
            bad += [f"{t}: {a}" for afs in s["surfaces"].values() for a in afs if a not in fv]
    return bad
