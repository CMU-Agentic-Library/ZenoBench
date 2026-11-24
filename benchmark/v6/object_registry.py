"""Object and furniture registry with affordance-based substitution (11-24, after Katia's suggestion).

Data (hand-written, benchmark/v6/registry/):
  objects.yaml    every movable asset kind: taxonomy, affordances, attributes
  furniture.yaml  every furniture type and appliance: taxonomy, affordances per surface kind
  roles.yaml      every substitution layout: what the stand-in must afford (task-dependent)

Geometry is never written by hand: objects from annotations/assets.json (the spawn source: size, mass, the
container opening and depth, graspability), surfaces from the scene annotations (height, size, headroom, room,
behind a door or not).

A stand-in o' is legal for a role g when  A_required(g) ⊆ A(o')  (``requires``; ``requires_any`` needs one of
its list) and it meets the role's geometric constraints (``fits``, ``covers``, ``room_of``, ``kid_reach``,
appliance compatibility).  Legal stand-ins rank by how many ``prefer`` items they meet; the ideal ranks top; a
thing in use (holding something, or named as used/full) ranks below every free legal one.

    level 0      illegal
    level 1      legal but in use
    level 2+k    legal and free, k preferences met
    level 10     the ideal, free

affordance_check.py compares these levels with the hand-written tiers of tasks.json.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REG = HERE / "registry"
SLACK = 1.05                      # fit tolerance on openings
IDEAL_LEVEL = 10
IN_USE_WORDS = ("oatmeal", "used", "full", "leftover", "example", "stew")
APPLIANCE_AFFORD = {"kitchen_microwave": "heat_microwave", "kitchen_stove": "heat_stove"}
APPLIANCE_SAFE = {"heat_microwave": "microwave_safe", "heat_stove": "stove_safe"}


# -- loading -----------------------------------------------------------------------------------------------
@lru_cache(None)
def objects_yaml() -> dict:
    return yaml.safe_load((REG / "objects.yaml").read_text())


@lru_cache(None)
def furniture_yaml() -> dict:
    return yaml.safe_load((REG / "furniture.yaml").read_text())


@lru_cache(None)
def roles() -> list:
    out = yaml.safe_load((REG / "roles.yaml").read_text())["roles"]
    for r in out:                                        # a bare YAML ``on`` reads as True
        assert all(isinstance(x, str) for pat in r["slot"] for x in pat), f"role {r['id']}: quote the slot atoms"
    return out


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


def fits(container: str, thing: str) -> bool:
    """``thing`` goes into ``container``: lying flat or standing in it (5 % slack on the opening)."""
    c, t = obj(container)["geometry"], obj(thing)["geometry"]
    if "opening_m" not in c:
        return False
    a, b, h = sorted(t["size_m"], reverse=True)
    w, n = c["opening_m"]
    flat = a <= w * SLACK and b <= n * SLACK
    upright = b <= w * SLACK and h <= n * SLACK and a <= 2 * c["depth_m"]
    return flat or upright


def covers(cover: str, target: str) -> bool:
    """``cover`` resting on ``target``'s rim closes its opening: its narrow side spans the opening."""
    t = obj(target)["geometry"]
    if "opening_m" not in t:
        return False
    return min(obj(cover)["geometry"]["size_m"][:2]) >= t["opening_m"][0] * 0.95


def _meets(item: str, facts: dict) -> bool:
    """A ``prefer`` item: an affordance, an attribute, "not:<attribute>", "taxonomy:<subcategory>", "portable"."""
    if item.startswith("taxonomy:"):
        return facts["taxonomy"].get("subcategory") == item.split(":", 1)[1]
    if item.startswith("not:"):
        return not facts["attributes"].get(item[4:], False)
    if item == "portable":
        return facts["geometry"].get("portable", False)
    return item in facts["affordances"] or bool(facts["attributes"].get(item, False))


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


def in_use(name: str, objs: dict) -> str | None:
    """Why ``name`` is not free at the start: something lies in it, or its name says it is used/full."""
    if any(w in name for w in IN_USE_WORDS):
        return "named in use"
    o = objs[name]
    facts = obj(o["kind"])
    if not o.get("xy"):
        return None
    if "contain_solid" not in facts["affordances"]:      # it lies on or in a holder (a lid on a pot, an apple on a plate)
        for k, x in objs.items():
            if k == name or not x.get("xy") or x.get("support") is None:
                continue
            holder = {"contain_solid", "support_items"} & set(obj(x["kind"])["affordances"])
            if o.get("support") not in (None, x["support"]) or not holder:
                continue
            r = max(obj(x["kind"])["geometry"]["size_m"][:2]) / 2
            if ((o["xy"][0] - x["xy"][0]) ** 2 + (o["xy"][1] - x["xy"][1]) ** 2) ** 0.5 <= r:
                return f"sits in/on {k}"
    if "contain_solid" not in facts["affordances"]:
        return None
    reach = max(facts["geometry"]["size_m"][:2]) / 2
    for k, x in objs.items():
        if k != name and x.get("support") is None and x.get("xy"):
            dx, dy = x["xy"][0] - o["xy"][0], x["xy"][1] - o["xy"][1]
            if (dx * dx + dy * dy) ** 0.5 <= reach:
                return f"holds {k}"
    return None


# -- roles ---------------------------------------------------------------------------------------------------
def role_for(task_id: str, design: str) -> list:
    out = []
    for r in roles():
        for p, ds in r["tasks"].items():
            if task_id.startswith(p) and ("*" in ds or design in ds or any(design.startswith(d + "__") for d in ds)):
                out.append(r)
    return out


def _legal(role: dict, facts: dict) -> list[str]:
    """Reasons a stand-in is illegal for the role on affordances alone (empty: legal)."""
    why = [f"lacks {a}" for a in role.get("requires", []) if a not in facts["affordances"]]
    any_ = role.get("requires_any")
    if any_ and not any(a in facts["affordances"] for a in any_):
        why.append("lacks any of " + "/".join(any_))
    return why


def assess_object(role: dict, name: str, objs: dict) -> tuple[int, list[str]]:
    o = objs.get(name)
    if o is None:
        return 0, ["not in the layout"]
    kind = o["kind"]
    facts = obj(kind)
    why = _legal(role, facts)
    if role.get("fits") and role["fits"] in objs and not fits(kind, objs[role["fits"]]["kind"]):
        why.append(f"{role['fits']} does not fit in it")
    if role.get("covers") and role["covers"] in objs and not covers(kind, objs[role["covers"]]["kind"]):
        why.append(f"does not cover {role['covers']}")
    if role.get("taxonomy_any") and facts["taxonomy"]["subcategory"] not in role["taxonomy_any"]:
        why.append(f"not a {'/'.join(role['taxonomy_any'])}")
    if why:
        return 0, why
    busy = in_use(name, objs)
    if busy and busy.split()[-1] in (role.get("covers"), role.get("fits")):
        busy = None                                      # the lid already on the pot it is for
    if busy:
        return 1, [busy]
    if kind in role.get("ideal", []):
        return IDEAL_LEVEL, ["ideal"]
    met = [p for p in role.get("prefer", []) if _meets(p, facts)]
    return 2 + len(met), [f"+{p}" for p in met]


def _centre(name: str):
    for base in scene_bases():
        for s in annotation(base)["supports"]:
            if s["name"] == name:
                x0, y0, x1, y1 = s["aabb_xy"]
                return (x0 + x1) / 2, (y0 + y1) / 2
    return None


def assess_place(role: dict, name: str, layout: str = "") -> tuple[int, list[str]]:
    """In a layout the role lists under ``ideal_unavailable`` the ideal place is full or taken: in use."""
    if name not in surfaces():
        return 0, ["unknown surface"]
    s = surface(name)
    why = _legal(role, s)
    if role.get("near"):
        ref, metres = role["near"]
        a, b = _centre(name), _centre(ref)
        if ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 > metres:
            why.append(f"more than {metres} m from {ref}")
    if role.get("room_of"):
        want = surface(role["room_of"])["geometry"]["room"]
        if s["geometry"]["room"] != want:
            why.append(f"in {s['geometry']['room']}, not {want}")
    if why:
        return 0, why
    if name in role.get("ideal", []):
        if any(x in layout for x in role.get("ideal_unavailable", [])):
            return 1, ["the ideal place, full or taken in this layout"]
        return IDEAL_LEVEL, ["ideal"]
    reach = s["geometry"]["height_m"] <= furniture_yaml()["kid_reach_m"]
    met = [p for p in role.get("prefer", []) if p in s["affordances"] or (p == "kid_reach" and reach)]
    return 2 + len(met), [f"+{p}" for p in met]


def appliance_ok(appliance: str, vessel_kind: str) -> bool:
    """The dish may be heated by this appliance (microwave: microwave_safe; stove: stove_safe)."""
    aff = APPLIANCE_AFFORD.get(appliance)
    return bool(aff) and bool(obj(vessel_kind)["attributes"].get(APPLIANCE_SAFE[aff], False))


def stand_in_kinds(role: dict, at_least: int) -> list[str]:
    """Every asset kind legal for an object role whose free level reaches ``at_least`` (geometry against the
    role's named objects is checked per layout, not here)."""
    out = []
    for kind in objects_yaml()["objects"]:
        facts = obj(kind)
        if _legal(role, facts) or (role.get("taxonomy_any") and facts["taxonomy"]["subcategory"] not in role["taxonomy_any"]):
            continue
        lvl = IDEAL_LEVEL if kind in role.get("ideal", []) else 2 + sum(_meets(p, facts) for p in role.get("prefer", []))
        if lvl >= at_least:
            out.append(kind)
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
    for r in roles():
        vocab = fv if r["kind"] in ("place", "appliance") else ov["affordances"]
        for a in r.get("requires", []) + r.get("requires_any", []):
            if a not in vocab:
                bad.append(f"role {r['id']}: {a}")
        for p in r.get("prefer", []):
            base = p.split(":", 1)[1] if ":" in p else p
            if not (p.startswith("taxonomy:") or base in vocab or base in ov["attributes"]
                    or base in ("portable", "kid_reach")):
                bad.append(f"role {r['id']}: prefer {p}")
    return bad


def agent_card(kinds: list[str] | None = None) -> str:
    """The registry as text, for the ablation where the planner is given it (not used by default)."""
    lines = []
    for k in kinds or sorted(objects_yaml()["objects"]):
        f = obj(k)
        attrs = ", ".join(f"{a}={v}" for a, v in sorted(f["attributes"].items()))
        lines.append(f"- {k} ({f['taxonomy']['category']}/{f['taxonomy']['subcategory']}): "
                     f"{', '.join(f['affordances']) or '-'}; {attrs}; size {f['geometry']['size_m']} m")
    return "\n".join(lines)
