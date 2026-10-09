"""Execute verb-based Skill Contracts (schema 2) on a live rig.

A Contract call:

1. validates the typed inputs and fills defaults;
2. binds every noun slot to GT attributes (asset tags, grasp annotation, the
   support under it, whether it is inside an appliance or container, the lid
   on it ...) plus the robot's hand state;
3. evaluates every precondition on the live simulator state and refuses to move
   if one is false (``PRECONDITION_FAILED``, with each measured predicate);
4. selects the first policy path whose noun conditions hold, checks the path's
   extra preconditions, then runs its steps in order.  A step is a low-level
   policy, a nested Skill Contract, or a loop over a list;
5. evaluates every postcondition (skill-level and path-level) on GT state; the
   action is reported only if all of them hold (``POSTCONDITION_FAILED``
   otherwise);
6. returns measured outputs, the selected path and all predicate measurements.
   A failed call stops; nothing is retried.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .predicates import (REGISTRY, atom_text, before_snapshot, entity_kind, entity_point, held_name,
                         lid_on, lids, lying_state, objects_inside, objects_on_support, tilt_deg, type_satisfies)
from .rig import SkillFailure

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "contract_library" / "skill_contracts.json"


class ContractError(SkillFailure):
    def __init__(self, code, message, report=None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.report = report or {}


def load_contracts(path=CATALOG):
    data = json.loads(Path(path).read_text())
    if data.get("schema_version") != 2 or data.get("kind") != "skill_contract_catalog":
        raise ValueError("expected a schema_version 2 skill_contract_catalog")
    by_id = {c["contract_id"]: c for c in data["contracts"]}
    by_verb = {c["verb"]: c for c in data["contracts"]}
    return by_id, by_verb


# ----------------------------------------------------------------- noun attributes
def _object_location(rig, name, st):
    c = rig.geo.centre(name, st)
    for a in rig.ann.articulated:
        box = a.get("cavity_aabb")
        if box and all(box[i] < c[i] < box[i + 3] for i in range(3)):
            return ("microwave_cavity" if a.get("category") == "microwave" else "appliance_cavity"), a["name"]
        if a.get("category") == "refrigerator":
            b = a["body_aabb"]
            if all(b[i] < c[i] < b[i + 3] for i in range(3)):
                return "refrigerator", a["name"]
    for other, o in rig.ann.objects.items():
        if other != name and rig.ann.asset_of(o).get("container") and rig.geo.inside(name, other, st)[0]:
            return "container", other
    s = rig.geo.support_under(name, st)
    if s is not None:
        f = s.get("furniture")
        if f and any(a["name"] == f for a in rig.ann.articulated) and s.get("category") == "cabinet_inside":
            return "cabinet", f
        return "support", None
    if float(rig.geo.bottom(name, st)[2]) < 0.05:
        return "floor", None
    return "unknown", None


def _near_closed_edge(rig, name, st):
    from . import skills
    s = rig.geo.support_under(name, st)
    if s is None:
        return False
    fp = rig.geo.footprint(name, st)
    try:
        open_dirs = [tuple(np.round(d, 3)) for d in skills._open_edges(rig, s)]
    except Exception:
        open_dirs = []
    x0, y0, x1, y1 = s["aabb_xy"]
    edges = {(1.0, 0.0): x1 - fp[2], (-1.0, 0.0): fp[0] - x0, (0.0, 1.0): y1 - fp[3], (0.0, -1.0): fp[1] - y0}
    return any(gap < 0.06 and d not in open_dirs for d, gap in edges.items())


def _edge_ready(rig, name, st):
    from .predicates import REGISTRY
    try:
        return bool(REGISTRY["edge_overhang"].evaluate(rig, {"_state_cache": st}, object=name)[0])
    except Exception:
        return False


def _bearing(rig, name, st):
    x, y, yaw = rig.base_pose()
    try:
        p = entity_point(rig, name, st)
    except Exception:
        return 0.0
    return abs((math.degrees(math.atan2(p[1] - y, p[0] - x)) - yaw + 180) % 360 - 180)


def _handle_collider(rig, obj):
    stage = getattr(rig, "stage", None)
    if stage is None:
        return bool(rig.ann.asset_of(obj).get("container", {}).get("handle_collider"))
    try:
        return bool(stage.GetPrimAtPath(obj["body"] + "/handle_collider").IsValid())
    except Exception:
        return False


def object_attrs(rig, name, st, values=None):
    ann = rig.ann
    obj = ann.objects[name]
    asset = ann.asset_of(obj)
    tags = list(asset.get("tags", []))
    grasp_types = [g["type"] for g in asset.get("grasps", [])]
    size = np.asarray(asset["size"], float)
    sup = rig.geo.support_under(name, st)
    bottom = rig.geo.bottom(name, st)
    loc, where = _object_location(rig, name, st)
    held = rig.held if rig.held and rig.held.get("name") == name else None
    lid = None
    contents = []
    if asset.get("container"):
        lid = next((l for l in lids(rig) if l != name and lid_on(rig, name, l, st)[0]), None)
        contents = objects_inside(rig, name, st)
    t = tilt_deg(st["objects"][name]["quat"])
    attrs = {
        "instance": name, "kind": "object", "asset": obj["asset"], "tags": tags + [obj["asset"]],
        "grasp_types": grasp_types, "support": sup["name"] if sup else None,
        "support_category": sup.get("category") if sup else None,
        "on_floor": bool(bottom[2] < 0.05), "location": loc,
        "appliance": where if loc in ("microwave_cavity", "appliance_cavity", "refrigerator", "cabinet") else None,
        "in_container": where if loc == "container" else None,
        "held_by": "right" if held else ("left" if rig.left_held and rig.left_held.get("name") == name else None),
        "held_kind": held.get("kind") if held else None,
        "flat": "flat" in tags or (bool(grasp_types) and set(grasp_types) == {"edge_pinch_after_push"}),
        "tall": bool(size[2] >= 1.3 * min(size[:2]) and t <= 20),
        "lying": bool(lying_state(rig, name, st)[0]),
        "wide_box": bool("rim_pinch_rect" in grasp_types and max(size[:2]) >= 0.22),
        "handle_collider": _handle_collider(rig, obj),
        "near_closed_edge": _near_closed_edge(rig, name, st),
        "edge_ready": _edge_ready(rig, name, st),
        "is_container": bool(asset.get("container")), "is_lid": "lid" in tags,
        "lid": lid, "contents": contents,
        "initial_support": (getattr(rig, "memory", {}) or {}).get("initial_support", {}).get(name) or obj.get("support"),
        "xy": [float(bottom[0]), float(bottom[1])], "bearing_abs_deg": _bearing(rig, name, st),
    }
    if sup is not None:
        attrs["buffer_xy"] = _free_xy(rig, name, sup["name"], avoid=[attrs["xy"]])
    if lid:
        attrs["aside_support"] = _aside_support(rig, lid, sup["name"] if sup else None, bottom[:2])
    if values and isinstance(values.get("rule"), dict):
        attrs["sort_target"] = next((values["rule"][t_] for t_ in attrs["tags"] if t_ in values["rule"]), None)
    return attrs


def _roomiest_xy(rig, support, st, ignore=()):
    """The point of a support farthest from every object on it except
    ``ignore`` (the objects being gathered), kept 10 cm from the edges and
    biased to the robot's side; stable while the gathered objects move."""
    s = rig.ann.support(support)
    x0, y0, x1, y1 = s["aabb_xy"]
    others = [rig.geo.footprint(o, st) for o in objects_on_support(rig, support, st) if o not in ignore]
    bx, by, _ = rig.base_pose()
    best, best_score = None, -1e9
    for x in np.linspace(x0 + 0.10, x1 - 0.10, max(2, int((x1 - x0) / 0.03))):
        for y in np.linspace(y0 + 0.10, y1 - 0.10, max(2, int((y1 - y0) / 0.03))):
            clear = min([math.hypot(max(f[0] - x, 0, x - f[2]), max(f[1] - y, 0, y - f[3])) for f in others] or [1.0])
            score = min(clear, 0.25) - 0.02 * math.hypot(x - bx, y - by)
            if score > best_score:
                best, best_score = [float(x), float(y)], score
    return best


def _aside_support(rig, lid, own, xy):
    """Where a lifted lid can be set down: the container's own support if it
    has a free spot for the lid, else the nearest table-height support within
    1.2 m that has one (the counter next to a crowded hob)."""
    cands = []
    for s in rig.ann.supports:
        if s.get("category") in ("floor", "rim") or not 0.4 <= s["z"] <= 1.2:
            continue
        x0, y0, x1, y1 = s["aabb_xy"]
        d = math.hypot(max(x0 - xy[0], 0, xy[0] - x1), max(y0 - xy[1], 0, xy[1] - y1))
        if s["name"] == own or d < 1.2:
            cands.append((0.0 if s["name"] == own else d, s["name"]))
    from . import skills
    for _, name in sorted(cands):
        try:
            if skills.free_spots(rig, lid, name, k=1):
                return name
        except Exception:
            continue
    return own


def _free_xy(rig, name, support, avoid=()):
    from . import skills
    try:
        spots = skills.free_spots(rig, name, support, k=12)
    except Exception:
        spots = []
    spots = [p for p in spots if all(math.hypot(p[0] - a[0], p[1] - a[1]) > 0.12 for a in avoid)]
    if spots:
        return [float(spots[0][0]), float(spots[0][1])]
    s = rig.ann.support(support)
    x0, y0, x1, y1 = s["aabb_xy"]
    return [(x0 + x1) / 2, (y0 + y1) / 2]


def support_attrs(rig, name, st, values=None):
    s = rig.ann.support(name)
    objs = objects_on_support(rig, name, st)
    attrs = {"instance": name, "kind": "support", "category": s.get("category"), "furniture": s.get("furniture"),
             "z": s["z"], "objects": objs, "is_microwave_cavity": s.get("furniture") == "kitchen_microwave"
             and s.get("category") == "cabinet_inside",
             "appliance": s.get("furniture") if any(a["name"] == s.get("furniture") for a in
                                                     list(rig.ann.articulated) + list(getattr(rig.ann, "appliances", [])))
             else None,
             "bearing_abs_deg": _bearing(rig, name, st)}
    stove = next((a for a in getattr(rig.ann, "appliances", []) if a["name"] == s.get("furniture")), None)
    attrs["burner_xy"] = None
    if stove:
        from .thermal import burners_of
        occupied = [rig.geo.bottom(n, st)[:2] for n in objects_on_support(rig, name, st)]
        free = [bu for bu in burners_of(stove)
                if all(math.hypot(p[0] - bu["center"][0], p[1] - bu["center"][1]) > bu["radius"] + 0.05 for p in occupied)]
        attrs["burner_xy"] = list((free or burners_of(stove))[0]["center"][:2])
    probe = None
    if values:
        for key in ("objects", "object"):
            v = values.get(key)
            probe = v[0] if isinstance(v, list) and v else v if isinstance(v, str) else probe
    attrs["roomiest_xy"] = _roomiest_xy(rig, name, st, ignore=set(values.get("objects") or []) if values else set())
    if probe in rig.ann.objects:
        attrs["free_xy"] = _free_xy(rig, probe, name)
    else:
        attrs["free_xy"] = [(s["aabb_xy"][0] + s["aabb_xy"][2]) / 2, (s["aabb_xy"][1] + s["aabb_xy"][3]) / 2]
    return attrs


def entity_attrs(rig, name, st, values=None):
    kind, rec = entity_kind(rig.ann, name)
    if kind == "object":
        return object_attrs(rig, name, st, values)
    if kind == "support":
        return support_attrs(rig, name, st, values)
    base = {"instance": name, "kind": kind, "bearing_abs_deg": _bearing(rig, name, st)}
    if kind == "articulated":
        q = rig.joint(name)
        span = abs(rec["open_q"] - rec["closed_q"])
        base.update({"type": rec["type"], "category": rec.get("category"), "has_handle": bool(rec.get("handle")),
                     "powered": "door_button" in rec, "is_open": abs(q - rec["closed_q"]) / max(span, 1e-9) >= 0.6,
                     "wide_open_q": rec["closed_q"] + (0.75 if rec.get("category") == "refrigerator" else 0.65)
                     * (rec["open_q"] - rec["closed_q"]),
                     "power_button": None})
    elif kind == "appliance":
        base.update({"category": rec.get("category"), "power_button": f"{name}/power_button"})
    elif kind == "button":
        app_kind, app = entity_kind(rig.ann, rec["appliance"])
        base.update({"appliance": rec["appliance"], "button": rec["button"],
                     "appliance_category": app.get("category")})
    return base


def appliance_attrs(rig, name, st, values=None):
    kind, rec = entity_kind(rig.ann, name)
    attrs = entity_attrs(rig, name, st, values)
    if kind not in ("articulated", "appliance"):
        raise SkillFailure(f"{name} is not an appliance")
    return attrs


def robot_attrs(rig):
    r = held_name(rig, "right")
    l = held_name(rig, "left")
    stowed = float(np.max(np.abs(rig.q()[2:] - rig.kin.rest[2:]))) < 0.10
    return {"right_held": r is not None, "left_held": l is not None, "right_object": r, "left_object": l,
            "right_kind": rig.held.get("kind") if rig.held else None, "both_hold_same": r is not None and r == l,
            "right_arm_stowed": stowed}


SLOT_VALIDATORS = {
    "object_ref": lambda rig, n: n in rig.ann.objects,
    "container_ref": lambda rig, n: n in rig.ann.objects and bool(rig.ann.asset_of(rig.ann.objects[n]).get("container")),
    "lid_ref": lambda rig, n: n in rig.ann.objects and "lid" in rig.ann.asset_of(rig.ann.objects[n]).get("tags", []),
    "tool_ref": lambda rig, n: n in rig.ann.objects and bool({"wiping_tool", "utensil", "sponge"} &
                                                             set(rig.ann.asset_of(rig.ann.objects[n]).get("tags", []))),
    "support_ref": lambda rig, n: any(s["name"] == n for s in rig.ann.supports),
    "receptacle_ref": lambda rig, n: any(s["name"] == n for s in rig.ann.supports) or (
        n in rig.ann.objects and bool(rig.ann.asset_of(rig.ann.objects[n]).get("container"))),
    "articulated_ref": lambda rig, n: any(a["name"] == n for a in rig.ann.articulated),
    "appliance_ref": lambda rig, n: n in {a["name"] for a in rig.ann.articulated
                                          if a.get("category") in ("microwave", "refrigerator")}
    | {a["name"] for a in getattr(rig.ann, "appliances", [])},
    "button_ref": lambda rig, n: _is_kind(rig, n, "button"),
    "room_ref": lambda rig, n: n in rig.ann.rooms,
    "place_ref": lambda rig, n: _is_kind(rig, n, None),
    "entity_ref": lambda rig, n: _is_kind(rig, n, None) and not _is_kind(rig, n, "room"),
}


def _is_kind(rig, name, want):
    try:
        kind, _ = entity_kind(rig.ann, name)
    except KeyError:
        return False
    return want is None or kind == want


def bind_nouns(rig, contract, values):
    st = rig.state()
    nouns = {}
    for slot, meta in contract["inputs"].items():
        t = meta["type"]
        v = values.get(slot)
        if v is None or not t.endswith("_ref"):
            continue
        if not SLOT_VALIDATORS[t](rig, v):
            raise ContractError("NOUN_INVALID", f"{slot}={v!r} is not a valid {t} in this scene")
        if t in ("object_ref", "container_ref", "lid_ref", "tool_ref"):
            nouns[slot] = object_attrs(rig, v, st, values)
        elif t == "support_ref":
            nouns[slot] = support_attrs(rig, v, st, values)
        elif t == "receptacle_ref":
            nouns[slot] = object_attrs(rig, v, st, values) if v in rig.ann.objects else support_attrs(rig, v, st, values)
        elif t == "appliance_ref":
            nouns[slot] = appliance_attrs(rig, v, st, values)
        else:
            nouns[slot] = entity_attrs(rig, v, st, values)
    nouns["robot"] = robot_attrs(rig)
    nouns["args"] = {k: v for k, v in values.items()}
    return nouns


# ----------------------------------------------------------------- value resolution
def resolve_value(v, values, nouns, outputs):
    if isinstance(v, str):
        if v.startswith("$"):
            return values.get(v[1:])
        if v.startswith("@"):
            noun, fld = v[1:].split(".", 1)
            if noun not in nouns:
                raise ContractError("BINDING", f"unknown noun {noun} in {v}")
            return nouns[noun].get(fld)
        if v.startswith("#"):
            step, key = v[1:].split(".", 1)
            return outputs.get(step, {}).get(key)
    if isinstance(v, dict):
        return {k: resolve_value(x, values, nouns, outputs) for k, x in v.items()}
    return v


def condition_holds(cond, nouns):
    noun = nouns.get(cond["noun"], {})
    val = noun.get(cond["field"])
    op, ref = cond["op"], cond["value"]
    if op == "equals":
        return val == ref
    if op == "in":
        return val in ref
    if op == "contains":
        return isinstance(val, (list, tuple)) and ref in val
    if op == "gte":
        return val is not None and val >= ref
    if op == "lte":
        return val is not None and val <= ref
    if op == "truthy":
        return bool(val)
    if op == "falsy":
        return not val
    raise ValueError(op)


# ----------------------------------------------------------------- runner
@dataclass
class SkillResult:
    contract_id: str
    action: str
    success: bool
    selected_path: str | None
    preconditions: list
    postconditions: list
    policy_steps: list
    outputs: dict
    bound_nouns: dict
    children: list = field(default_factory=list)
    error: str | None = None
    error_code: str | None = None

    def asdict(self):
        return dict(self.__dict__)


class SkillContractRunner:
    def __init__(self, rig, catalog=CATALOG):
        self.rig = rig
        self.by_id, self.by_verb = load_contracts(catalog)
        self.trace: list[dict] = []

    def contract(self, key):
        return self.by_id.get(key) or self.by_verb.get(key) or \
            (_ for _ in ()).throw(KeyError(key))

    # -------------------------------------------------------------
    def run(self, key, args: dict, depth=0) -> SkillResult:
        c = self.contract(key)
        rig = self.rig
        values = {}
        for slot, meta in c["inputs"].items():
            if slot in args and args[slot] is not None:
                values[slot] = args[slot]
            elif "default" in meta:
                values[slot] = meta["default"]
            elif meta.get("required"):
                raise ContractError("INPUT_MISSING", f"{c['verb']}: missing input {slot}")
            else:
                values[slot] = None
        unknown = set(args) - set(c["inputs"])
        if unknown:
            raise ContractError("INPUT_UNKNOWN", f"{c['verb']}: unknown inputs {sorted(unknown)}")
        action = f"{c['action_predicate']['name']}(" + ", ".join(
            f"{k}={values[k]}" for k in c["action_predicate"]["arguments"] if values.get(k) is not None) + ")"
        res = SkillResult(c["contract_id"], action, False, None, [], [], [], {}, {})
        rig.caption = action
        rig.log("contract_start", contract=c["contract_id"], action=action, depth=depth)
        ctx = {"before": before_snapshot(rig)}
        try:
            nouns = bind_nouns(rig, c, values)
            res.bound_nouns = {k: {f: v for f, v in d.items() if not isinstance(v, (list, dict)) or len(str(v)) < 300}
                               for k, d in nouns.items() if k != "args"}
            failed = self._check(c["requires"], values, nouns, ctx, res.preconditions)
            if failed:
                raise ContractError("PRECONDITION_FAILED", "; ".join(failed))
            path = next((p for p in c["policy_plan"]["paths"] if all(condition_holds(w, nouns) for w in p["when"])),
                        None)
            if path is None:
                raise ContractError("NO_PATH", "no policy path matches the bound nouns and robot state")
            res.selected_path = path["path_id"]
            failed = self._check(path.get("requires", []), values, nouns, ctx, res.preconditions)
            if failed:
                raise ContractError("PRECONDITION_FAILED", f"path {path['path_id']}: " + "; ".join(failed))
            outputs = {}
            self._run_steps(path["steps"], values, nouns, outputs, res, depth)
            rig.step(30)
            ctx.pop("_state_cache", None)
            failed = self._check(list(c["ensures"]) + list(path.get("ensures", [])), values, nouns, ctx,
                                 res.postconditions)
            if failed:
                raise ContractError("POSTCONDITION_FAILED", "; ".join(failed))
            res.outputs = self._outputs(c, outputs, values, nouns, ctx)
            res.success = True
        except ContractError as exc:
            res.error, res.error_code = str(exc), exc.code
        except SkillFailure as exc:
            res.error, res.error_code = str(exc), "POLICY_FAILED"
        rig.log("contract_end", contract=c["contract_id"], action=action, success=res.success,
                path=res.selected_path, error=res.error)
        self.trace.append(res.asdict())
        return res

    def run_or_raise(self, key, args, depth=0):
        r = self.run(key, args, depth)
        if not r.success:
            raise ContractError(r.error_code or "FAILED", r.error or "failed", r.asdict())
        return r

    # -------------------------------------------------------------
    def _check(self, atoms, values, nouns, ctx, sink):
        failed = []
        for atom in atoms:
            args = {k: resolve_value(v, values, nouns, {}) for k, v in atom["args"].items()}
            if any(v is None for v in args.values()):
                sink.append({"atom": atom_text(atom), "holds": False, "detail": "unbound argument", "args": args})
                failed.append(f"{atom_text(atom)} unbound")
                continue
            ok, detail = REGISTRY[atom["pred"]].evaluate(self.rig, ctx, **args)
            ok = bool(ok) != bool(atom.get("negated"))
            text = ("not " if atom.get("negated") else "") + atom["pred"] + "(" + ", ".join(
                f"{k}={v}" for k, v in args.items()) + ")"
            sink.append({"atom": text, "holds": ok, "detail": detail})
            if not ok:
                failed.append(f"{text} is false ({detail})")
        return failed

    def _run_steps(self, steps, values, nouns, outputs, res, depth):
        from .policies import PolicySuite
        suite = PolicySuite(self.rig)
        for i, step in enumerate(steps):
            if "foreach" in step:
                items = resolve_value(step["foreach"], values, nouns, outputs) or []
                for item in list(items):
                    sub_values = dict(values, **{step["as"]: item})
                    sub_nouns = dict(nouns)
                    if item in self.rig.ann.objects:
                        sub_nouns[step["as"]] = object_attrs(self.rig, item, self.rig.state(), values)
                    self._run_steps(step["steps"], sub_values, sub_nouns, outputs, res, depth)
                continue
            if "call" in step:
                sub_args = {k: resolve_value(v, values, nouns, outputs) for k, v in step["args"].items()}
                sub_args = {k: v for k, v in sub_args.items() if v is not None}
                child = self.run(step["call"], sub_args, depth + 1)
                res.children.append(child.asdict())
                res.policy_steps.append({"call": step["call"], "args": sub_args, "success": child.success,
                                         "path": child.selected_path})
                if not child.success:
                    raise ContractError("SUBSKILL_FAILED", f"{child.action}: {child.error}")
                if step.get("as"):
                    outputs[step["as"]] = child.outputs
                continue
            pid = step["policy"]
            args = [resolve_value(a, values, nouns, outputs) for a in step["args"]]
            kwargs = {k: resolve_value(v, values, nouns, outputs) for k, v in step.get("kwargs", {}).items()}
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            while args and args[-1] is None:
                args.pop()
            record = {"policy": pid, "args": [a if isinstance(a, (str, int, float, bool)) else "<value>" for a in args]}
            res.policy_steps.append(record)
            self.rig.log("policy_start", policy=pid)
            out = getattr(suite, pid).execute(*args, **kwargs)
            record["success"] = True
            if step.get("as"):
                outputs[step["as"]] = out if isinstance(out, dict) else {"value": out}
            if isinstance(out, dict):
                outputs.setdefault("_last", {}).update(out)

    def _outputs(self, c, outputs, values, nouns, ctx):
        rig = self.rig
        res = {}
        last = outputs.get("_last", {})
        for name in c.get("outputs", {}):
            if name in last:
                v = last[name]
            elif name == "base_pose":
                v = [float(x) for x in rig.base_pose()]
            elif name == "base_yaw_deg":
                v = float(rig.base_pose()[2])
            elif name == "moved_m":
                x0, y0, _ = ctx["before"]["base_pose"]
                x1, y1, _ = rig.base_pose()
                obj = values.get("object")
                if obj and obj in rig.ann.objects:
                    v = float(np.linalg.norm(rig.obj_pose(obj)[0][:2] - np.asarray(ctx["before"]["objects"][obj]["pos"][:2])))
                else:
                    v = float(math.hypot(x1 - x0, y1 - y0))
            elif name == "joint":
                v = float(rig.joint(values["articulated"]))
            elif name == "temp_c":
                v = float(rig.thermal.temperatures_c[values["food"]])
            elif name == "lift_m":
                o = values["object"]
                v = float(rig.obj_pose(o)[0][2] - ctx["before"]["objects"][o]["pos"][2])
            elif name == "grasp":
                v = rig.held.get("kind") if rig.held else None
            elif name == "position":
                v = [float(x) for x in rig.geo.bottom(values["object"], rig.state())[:2]]
            elif name == "lid":
                v = nouns.get("container", {}).get("lid")
            elif name == "moved":
                v = [n for n in (nouns.get("support", {}).get("objects") or nouns.get("container", {}).get("contents") or [])]
            elif name in ("contents", "seen", "visited", "found_on", "coverage", "turns"):
                v = last.get(name)
            else:
                v = None
            res[name] = v
        return res
