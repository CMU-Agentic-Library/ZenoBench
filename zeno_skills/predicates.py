"""Parameterized state predicates shared by SkillNodes, Contracts and the planner.

Every precondition and postcondition in the verb-based SkillNode library is a
predicate from this registry with explicit, typed arguments, for example
``holding(hand="right", object="$object")``.  Each predicate declares

* ``args``: ordered (name, type) pairs.  Types are the SkillNode argument types
  (``object_ref``, ``support_ref``, ``hand`` ...).
* ``kind``:
    - ``fluent``   — a state that holds or not in the live scene; usable as a
                     precondition, a postcondition and a planner goal.
    - ``memory``   — a fact the robot recorded (an object it saw, a surface it
                     wiped); persists until a listed skill invalidates it.
    - ``relative`` — measured against the state captured when the Contract
                     started (``object_moved``); usable only as a postcondition.
* ``evaluate(rig, ctx, **args) -> (bool, detail)``: the live check that the
  ContractRunner calls.  ``ctx`` carries the before-state snapshot and the
  robot's memory.

The module imports no simulator code, so the static checker and the symbolic
planner can use the registry offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Callable

import numpy as np

HANDS = ("right", "left")

# --------------------------------------------------------------------- types
# Argument types of SkillNode inputs/outputs and predicate arguments.  A value of
# type T may be passed where a predicate expects a type listed in COMPATIBLE[T].
REF_TYPES = {
    "object_ref": "a movable annotated scene object",
    "container_ref": "an object annotated as an open container",
    "lid_ref": "an object tagged as a lid",
    "tool_ref": "an object tagged as a hand tool (sponge, spoon)",
    "support_ref": "an annotated horizontal support surface",
    "receptacle_ref": "a support surface or an open container",
    "articulated_ref": "an annotated door, drawer or appliance door",
    "appliance_ref": "an articulated appliance with a thermal role (microwave, refrigerator)",
    "button_ref": "an annotated appliance button, written <appliance>/<button>",
    "room_ref": "an annotated room",
    "place_ref": "a room, furniture, support, articulated part or object used as a destination",
    "entity_ref": "any annotated object, support, articulated part or button",
}
VALUE_TYPES = {
    "hand": "\"right\" or \"left\"",
    "number": "a finite number",
    "positive_number": "a number > 0",
    "unit_vec2": "a horizontal unit vector [x, y]",
    "xy": "a world position [x, y] in metres",
    "object_list": "a non-empty list of object refs",
    "category_map": "an object tag -> container ref mapping",
    "tag": "an asset tag or asset name, e.g. \"fruit\", \"toy\", \"cherry_tomato\"",
}
ALL_TYPES = {**REF_TYPES, **VALUE_TYPES}

# T -> set of predicate argument types it satisfies
COMPATIBLE = {
    "object_ref": {"object_ref", "entity_ref", "place_ref"},
    "container_ref": {"container_ref", "object_ref", "receptacle_ref", "entity_ref", "place_ref"},
    "lid_ref": {"lid_ref", "object_ref", "entity_ref", "place_ref"},
    "tool_ref": {"tool_ref", "object_ref", "entity_ref", "place_ref"},
    "support_ref": {"support_ref", "receptacle_ref", "entity_ref", "place_ref"},
    "receptacle_ref": {"receptacle_ref", "entity_ref", "place_ref"},
    "articulated_ref": {"articulated_ref", "entity_ref", "place_ref"},
    "appliance_ref": {"appliance_ref", "articulated_ref", "entity_ref", "place_ref"},
    "button_ref": {"button_ref", "entity_ref"},
    "room_ref": {"room_ref", "place_ref"},
    "place_ref": {"place_ref"},
    "entity_ref": {"entity_ref", "place_ref"},
    "hand": {"hand"},
    "number": {"number"},
    "positive_number": {"positive_number", "number"},
    "unit_vec2": {"unit_vec2"},
    "xy": {"xy"},
    "object_list": {"object_list"},
    "category_map": {"category_map"},
    "tag": {"tag"},
}


def type_satisfies(value_type: str, wanted: str) -> bool:
    return wanted in COMPATIBLE.get(value_type, {value_type})


# --------------------------------------------------------------------- thresholds
UPRIGHT_DEG = 20.0
LYING_DEG = 60.0
REACH_OFFSET = 0.10           # reach test: TCP this far above the target point
NEAR_M = 1.30                 # base_near: base centre to target footprint
FACING_DEG = 20.0
GRASP_GAP_M = 0.035           # finger thickness + clearance beside an object
HEAD_HFOV_DEG = 92.0          # 10 mm focal length, 20.955 mm aperture
HEAD_VFOV_DEG = 76.0
VIEW_RANGE_M = 5.0


@dataclass(frozen=True)
class Predicate:
    name: str
    args: tuple[tuple[str, str], ...]
    kind: str
    doc: str
    evaluate: Callable = field(compare=False, repr=False)

    @property
    def arg_names(self):
        return tuple(a for a, _ in self.args)


REGISTRY: dict[str, Predicate] = {}


def predicate(name, args, kind, doc):
    if kind not in ("fluent", "memory", "relative"):
        raise ValueError(kind)

    def wrap(fn):
        REGISTRY[name] = Predicate(name, tuple(args), kind, doc, fn)
        return fn
    return wrap


# --------------------------------------------------------------------- helpers
def _yaw_of_quat(q):
    w, x, y, z = q
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def _quat_R(q):
    from .evaluator import quat_R
    return quat_R(q)


def tilt_deg(q):
    R = _quat_R(q)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(R[2, 2])))))


def _state(rig, ctx):
    if ctx is not None and ctx.get("_state_cache") is not None:
        return ctx["_state_cache"]
    st = rig.state()
    if ctx is not None:
        ctx["_state_cache"] = st
    return st


def memory(rig):
    mem = getattr(rig, "memory", None)
    if mem is None:
        mem = {"observed": {}, "wiped": {}, "stirred": {}, "explored": {}, "initial_support": {}}
        try:
            rig.memory = mem
        except Exception:
            pass
    return mem


def entity_kind(ann, name):
    """Resolve a name to (kind, record).  Order: object, articulated, button,
    support, furniture, room."""
    if name in ann.objects:
        return "object", ann.objects[name]
    for a in ann.articulated:
        if a["name"] == name:
            return "articulated", a
    for a in getattr(ann, "appliances", []):
        if a["name"] == name:
            return "appliance", a
    if "/" in name:
        app, button = name.rsplit("/", 1)
        for a in list(ann.articulated) + list(getattr(ann, "appliances", [])):
            if a["name"] == app and button in a and isinstance(a[button], dict) and "center" in a[button]:
                return "button", dict(a[button], appliance=app, button=button)
    for s in ann.supports:
        if s["name"] == name:
            return "support", s
    sup = [s for s in ann.supports if s.get("furniture") == name]
    if sup:
        return "furniture", sup
    if name in ann.rooms:
        return "room", ann.rooms[name]
    raise KeyError(name)


def entity_point(rig, name, st=None):
    """A representative world point of an entity (object centre, handle, button,
    support centre at its height, furniture top centre)."""
    ann = rig.ann
    kind, rec = entity_kind(ann, name)
    if kind == "object":
        st = st or rig.state()
        return np.asarray(rig.geo.centre(name, st), float)
    if kind == "articulated":
        h = rec.get("handle")
        if h:
            return np.asarray(ann.handle_pose(rec, rig.joint(name))[0], float)
        b = rec["body_aabb"]
        return np.array([(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2])
    if kind == "appliance":
        return np.asarray(rec["burner"]["center"], float)
    if kind == "button":
        return np.asarray(rec["center"], float)
    if kind == "support":
        x0, y0, x1, y1 = rec["aabb_xy"]
        return np.array([(x0 + x1) / 2, (y0 + y1) / 2, rec["z"]])
    if kind == "furniture":
        top = max(rec, key=lambda s: s["z"])
        x0, y0, x1, y1 = top["aabb_xy"]
        return np.array([(x0 + x1) / 2, (y0 + y1) / 2, top["z"]])
    tris = np.asarray(rec["triangles"], float).reshape(-1, 2)
    return np.r_[tris.mean(axis=0), 0.8]


def entity_footprint(rig, name, st=None):
    """World xy box of an entity, used for proximity tests."""
    ann = rig.ann
    kind, rec = entity_kind(ann, name)
    if kind == "object":
        return np.asarray(rig.geo.footprint(name, st or rig.state()), float)
    if kind in ("articulated", "appliance"):
        b = rec["body_aabb"]
        return np.array([b[0], b[1], b[3], b[4]], float)
    if kind == "button":
        c = np.asarray(rec["center"], float)
        return np.array([c[0] - 0.02, c[1] - 0.02, c[0] + 0.02, c[1] + 0.02])
    if kind == "support":
        return np.asarray(rec["aabb_xy"], float)
    if kind == "furniture":
        b = np.array([s["aabb_xy"] for s in rec], float)
        return np.array([b[:, 0].min(), b[:, 1].min(), b[:, 2].max(), b[:, 3].max()])
    tris = np.asarray(rec["triangles"], float).reshape(-1, 2)
    return np.array([tris[:, 0].min(), tris[:, 1].min(), tris[:, 0].max(), tris[:, 1].max()])


def _box_dist(box, xy):
    dx = max(box[0] - xy[0], 0.0, xy[0] - box[2])
    dy = max(box[1] - xy[1], 0.0, xy[1] - box[3])
    return math.hypot(dx, dy)


def held_name(rig, hand):
    h = rig.held if hand == "right" else rig.left_held
    return None if h is None else h.get("name")


def reach_targets(rig, name, st=None):
    """TCP poses whose IK solvability defines ``reachable``."""
    from .kinematics import gripper_rot
    st = st or rig.state()
    kind, rec = entity_kind(rig.ann, name)
    down = gripper_rot([0, 0, -1.0], [1.0, 0.0, 0.0])
    if kind == "object":
        top = np.asarray(rig.geo.bottom(name, st), float)
        top[2] += rig.ann.asset_of(rec)["size"][2]
        return [(top + np.array([0, 0, REACH_OFFSET]), down)]
    if kind == "articulated" and rec.get("handle"):
        c, R, approach = rig.ann.handle_pose(rec, rig.joint(name))
        return [(np.asarray(c) - 0.06 * np.asarray(approach), R)]
    if kind == "button":
        c = np.asarray(rec["center"], float)
        out = np.asarray(rec["outward"], float)
        return [(c + 0.08 * out, gripper_rot(-out, [0, 0, 1.0]))]
    p = entity_point(rig, name, st)
    if kind in ("support", "furniture"):
        # nearest point of the surface, 5 cm inside its edge
        x, y, _ = rig.base_pose()
        box = entity_footprint(rig, name, st)
        q = np.array([min(max(x, box[0] + 0.05), box[2] - 0.05),
                      min(max(y, box[1] + 0.05), box[3] - 0.05), p[2]])
        return [(q + np.array([0, 0, REACH_OFFSET]), down)]
    return [(p + np.array([0, 0, REACH_OFFSET]), down)]


def ik_reachable(rig, targets):
    """IK from the *current* base pose (torso and waist free), collision
    checked with the finger pads ignored."""
    kin = rig.kin
    rig.sync_world()
    saved = kin.coll_kw
    kin.coll_kw = {"ignore_fingers": True}
    try:
        for p, R in targets:
            _, ok = kin.ik_global(np.asarray(p, float), R, seeds=[rig.q_cmd])
            if ok:
                return True, [round(float(v), 3) for v in p]
    finally:
        kin.coll_kw = saved
    return False, [round(float(v), 3) for v in targets[0][0]]


# --------------------------------------------------------------------- robot body
@predicate("hand_empty", [("hand", "hand")], "fluent", "The given gripper holds nothing.")
def _hand_empty(rig, ctx, hand):
    name = held_name(rig, hand)
    return name is None, f"{hand} holds {name}"


@predicate("holding", [("hand", "hand"), ("object", "object_ref")], "fluent",
           "The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.")
def _holding(rig, ctx, hand, object):
    name = held_name(rig, hand)
    if name != object:
        return False, f"{hand} holds {name}"
    h = rig.held if hand == "right" else rig.left_held
    kin = rig.kin if hand == "right" else rig.left_kin
    q = rig.q() if hand == "right" else rig.left_q()
    tcp, _ = kin.tcp(q)
    body, _ = rig.obj_pose(object)
    slip = abs(float(np.linalg.norm(tcp - body)) - float(np.linalg.norm(h["tcp_minus_body"])))
    fingers = rig.fingers() if hand == "right" else rig.left_fingers()
    ok = slip <= 0.05 and float(np.min(fingers)) > 0.002
    return ok, f"slip {slip:.3f} m, fingers {np.round(fingers, 4).tolist()}"


@predicate("arm_stowed", [("hand", "hand")], "fluent", "The arm is folded at its travel posture.")
def _arm_stowed(rig, ctx, hand):
    if hand == "right":
        err = float(np.max(np.abs(rig.q()[2:] - rig.kin.rest[2:])))
    else:
        err = float(np.max(np.abs(rig.left_q()[2:] - rig.left_kin.rest[2:])))
    return err < 0.10, f"max joint error {err:.3f} rad"


def _joint(rig, name):
    return float(rig.q()[rig.kin.names.index(name)])


@predicate("torso_lowered", [], "fluent", "Torso lift within 3 cm of its lowest position (floor reach).")
def _torso_lowered(rig, ctx):
    i = rig.kin.names.index("torso_lift_joint")
    v = float(rig.q()[i])
    return v <= rig.kin.lo[i] + 0.03, f"torso {v:.3f} m"


@predicate("torso_at", [("height_m", "number")], "fluent",
           "Torso lift joint within 2 cm of the requested position (0 = top, -0.54 = bottom).")
def _torso_at(rig, ctx, height_m):
    i = rig.kin.names.index("torso_lift_joint")
    v = float(rig.q()[i])
    return abs(v - float(height_m)) <= 0.02, f"torso {v:.3f} m"


@predicate("torso_raised", [], "fluent", "Torso lift within 3 cm of its highest position (travel height).")
def _torso_raised(rig, ctx):
    i = rig.kin.names.index("torso_lift_joint")
    v = float(rig.q()[i])
    return v >= rig.kin.hi[i] - 0.03, f"torso {v:.3f} m"


@predicate("waist_bent", [("min_pitch_rad", "positive_number")], "fluent",
           "Waist pitched forward by at least the given angle.")
def _waist_bent(rig, ctx, min_pitch_rad):
    v = _joint(rig, "waist_pitch_joint")
    return v >= float(min_pitch_rad) - 0.035, f"waist {v:.3f} rad"


@predicate("waist_straight", [], "fluent", "Waist pitch within 0.05 rad of upright.")
def _waist_straight(rig, ctx):
    v = _joint(rig, "waist_pitch_joint")
    return abs(v) <= 0.05, f"waist {v:.3f} rad"


@predicate("base_near", [("place", "place_ref")], "fluent",
           "Base centre within 1.3 m of the place's footprint (inside the room for a room).")
def _base_near(rig, ctx, place):
    x, y, _ = rig.base_pose()
    kind, rec = entity_kind(rig.ann, place)
    if kind == "room":
        from .evaluator import room_of
        r = room_of(rig.ann.rooms, (x, y))
        return r == place, f"base in {r}"
    d = _box_dist(entity_footprint(rig, place, _state(rig, ctx)), (x, y))
    return d <= NEAR_M, f"distance {d:.2f} m"


@predicate("base_clear_of", [("place", "place_ref"), ("distance_m", "positive_number")], "fluent",
           "Base centre at least the given distance from the place's footprint.")
def _base_clear_of(rig, ctx, place, distance_m):
    x, y, _ = rig.base_pose()
    d = _box_dist(entity_footprint(rig, place, _state(rig, ctx)), (x, y))
    return d >= float(distance_m) - 0.02, f"distance {d:.2f} m"


@predicate("reachable", [("target", "entity_ref")], "fluent",
           "From the current base pose the right TCP has a collision-free IK solution 10 cm above the target "
           "(handle pre-grasp for doors, 8 cm in front of a button).")
def _reachable(rig, ctx, target):
    return ik_reachable(rig, reach_targets(rig, target, _state(rig, ctx)))


@predicate("facing", [("target", "entity_ref")], "fluent", "Base heading within 20 deg of the target bearing.")
def _facing(rig, ctx, target):
    x, y, yaw = rig.base_pose()
    p = entity_point(rig, target, _state(rig, ctx))
    bearing = math.degrees(math.atan2(p[1] - y, p[0] - x))
    err = abs((bearing - yaw + 180) % 360 - 180)
    return err <= FACING_DEG, f"bearing error {err:.1f} deg"


@predicate("in_view", [("target", "entity_ref")], "fluent",
           "Target point inside the head camera frustum, within 5 m, line of sight not blocked by furniture boxes.")
def _in_view(rig, ctx, target):
    from .perception import project_to_head_camera
    p = entity_point(rig, target, _state(rig, ctx))
    ok, detail = project_to_head_camera(rig, p, exclude=target)
    return ok, detail


@predicate("observed", [("target", "entity_ref")], "memory",
           "The robot saw the target in its head camera during this episode (set by look, search, inspect, explore).")
def _observed(rig, ctx, target):
    seen = memory(rig)["observed"].get(target)
    return seen is not None, f"last seen at tick {seen}"


@predicate("pointing_at", [("target", "entity_ref")], "fluent",
           "The right finger axis points at the target within 8 deg.")
def _pointing_at(rig, ctx, target):
    tcp, R = rig.kin.tcp(rig.q())
    d = entity_point(rig, target, _state(rig, ctx)) - tcp
    ang = math.degrees(math.acos(max(-1.0, min(1.0, float((-R[:, 2]) @ d / max(1e-9, np.linalg.norm(d)))))))
    return ang <= 8.0, f"angle {ang:.1f} deg"


@predicate("presenting", [("object", "object_ref")], "fluent",
           "The right-held object is in front of the body at 0.9-1.4 m height and in the head camera view.")
def _presenting(rig, ctx, object):
    if held_name(rig, "right") != object:
        return False, "not right-held"
    x, y, yaw = rig.base_pose()
    c = rig.geo.centre(object, _state(rig, ctx))
    fwd = (c[0] - x) * math.cos(math.radians(yaw)) + (c[1] - y) * math.sin(math.radians(yaw))
    from .perception import project_to_head_camera
    vis, _ = project_to_head_camera(rig, c, exclude=object)
    ok = 0.35 <= fwd <= 0.85 and 0.9 <= c[2] <= 1.4 and vis
    return ok, f"forward {fwd:.2f} m, height {c[2]:.2f} m, visible {vis}"


@predicate("room_explored", [("room", "room_ref")], "memory",
           "At least 75 % of the room's head-camera viewpoints were covered.")
def _room_explored(rig, ctx, room):
    cov = memory(rig)["explored"].get(room, 0.0)
    return cov >= 0.75, f"coverage {cov:.2f}"


# --------------------------------------------------------------------- object state
def _support_names(rig, place):
    kind, rec = entity_kind(rig.ann, place)
    if kind == "support":
        return [rec["name"]]
    if kind == "furniture":
        return [s["name"] for s in rec]
    return []


@predicate("on", [("object", "object_ref"), ("support", "support_ref")], "fluent",
           "Object bottom within -2..+5 cm of the support height with its centre over the support box.")
def _on(rig, ctx, object, support):
    return rig.geo.on(object, support, _state(rig, ctx))


@predicate("inside", [("object", "object_ref"), ("container", "container_ref")], "fluent",
           "Object centre inside the container's wall profile, between its floor and 3 cm above the rim.")
def _inside(rig, ctx, object, container):
    return rig.geo.inside(object, container, _state(rig, ctx))


@predicate("on_burner", [("object", "object_ref"), ("appliance", "appliance_ref")], "fluent",
           "Object bottom on the stove's burner disc (3 cm radial and height tolerance).")
def _on_burner(rig, ctx, object, appliance):
    kind, rec = entity_kind(rig.ann, appliance)
    if kind != "appliance":
        return False, f"{appliance} has no burner"
    from .thermal import burners_of
    b = rig.geo.bottom(object, _state(rig, ctx))
    best = min(burners_of(rec), key=lambda bu: math.hypot(b[0] - bu["center"][0], b[1] - bu["center"][1]))
    c = best["center"]
    r = math.hypot(b[0] - c[0], b[1] - c[1])
    ok = r <= best["radius"] + 0.03 and abs(b[2] - c[2]) <= 0.03
    return ok, f"{best.get('name', 'burner')}: radial {r:.3f} m, dz {b[2] - c[2]:.3f} m"


@predicate("in_cookware_on_burner", [("food", "object_ref"), ("appliance", "appliance_ref")], "fluent",
           "Food is inside a container whose bottom rests on the stove burner disc (or on the disc itself).")
def _in_cookware_on_burner(rig, ctx, food, appliance):
    from .thermal import on_burner_vessel
    kind, rec = entity_kind(rig.ann, appliance)
    if kind != "appliance":
        return False, f"{appliance} has no burner"
    vessel = on_burner_vessel(rig, food, rec)
    return vessel is not None, f"vessel {vessel}"


@predicate("in_appliance", [("object", "object_ref"), ("appliance", "appliance_ref")], "fluent",
           "Object centre inside the appliance cavity box (microwave) or body box (refrigerator).")
def _in_appliance(rig, ctx, object, appliance):
    a = rig.ann.art(appliance)
    b = a.get("cavity_aabb") or a["body_aabb"]
    c = rig.geo.centre(object, _state(rig, ctx))
    ok = all(b[i] < c[i] < b[i + 3] for i in range(3))
    return ok, f"centre {np.round(c, 3).tolist()}"


def _top_of(rig, name, st):
    b = np.asarray(rig.geo.bottom(name, st), float)
    R = _quat_R(st["objects"][name]["quat"])
    size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
    return b + R @ np.array([0, 0, size[2]])


@predicate("on_top_of", [("object", "object_ref"), ("base", "object_ref")], "fluent",
           "Object rests on the base object's top face: bottom within 2 cm of it, centre over its footprint.")
def _on_top_of(rig, ctx, object, base):
    st = _state(rig, ctx)
    top = _top_of(rig, base, st)
    b = rig.geo.bottom(object, st)
    fp = rig.geo.footprint(base, st)
    dz = float(b[2] - top[2])
    over = fp[0] - 0.005 <= b[0] <= fp[2] + 0.005 and fp[1] - 0.005 <= b[1] <= fp[3] + 0.005
    return abs(dz) <= 0.02 and over, f"dz {dz:.3f} m, over footprint {over}"


@predicate("top_clear", [("object", "object_ref")], "fluent", "No other object rests on the object's top face.")
def _top_clear(rig, ctx, object):
    st = _state(rig, ctx)
    for other in rig.ann.objects:
        if other == object:
            continue
        ok, _ = _on_top_of(rig, ctx, other, object)
        if ok:
            return False, f"{other} on top"
    return True, "clear"


@predicate("on_floor", [("object", "object_ref")], "fluent", "Object bottom below 5 cm.")
def _on_floor(rig, ctx, object):
    z = float(rig.geo.bottom(object, _state(rig, ctx))[2])
    return z < 0.05, f"bottom z {z:.3f} m"


@predicate("upright", [("object", "object_ref")], "fluent", "Object z axis within 20 deg of vertical.")
def _upright(rig, ctx, object):
    t = tilt_deg(_state(rig, ctx)["objects"][object]["quat"])
    return t <= UPRIGHT_DEG, f"tilt {t:.1f} deg"


def lying_state(rig, name, st):
    """Longest body axis horizontal and the vertical extent at most 60 % of it."""
    R = _quat_R(st["objects"][name]["quat"])
    size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
    k = int(np.argmax(size))
    axis_z = abs(float(R[2, k]))
    vertical = float(np.abs(R[2, :]) @ size)
    return axis_z < 0.5 and vertical <= 0.6 * float(size[k]), axis_z, vertical


@predicate("lying", [("object", "object_ref")], "fluent",
           "Object on its side: longest axis within 60 deg of horizontal and vertical extent <= 60 % of its length.")
def _lying(rig, ctx, object):
    ok, axis_z, vertical = lying_state(rig, object, _state(rig, ctx))
    return ok, f"long-axis z {axis_z:.2f}, vertical extent {vertical:.3f} m"


@predicate("held_above", [("object", "object_ref"), ("height_m", "positive_number")], "fluent",
           "Right-held object's bottom at or above the given world height (2 cm tolerance).")
def _held_above(rig, ctx, object, height_m):
    z = float(rig.geo.bottom(object, _state(rig, ctx))[2])
    return held_name(rig, "right") == object and z >= float(height_m) - 0.02, f"bottom z {z:.3f} m"


@predicate("held_below", [("object", "object_ref"), ("height_m", "positive_number")], "fluent",
           "Right-held object's bottom at or below the given world height (2 cm tolerance).")
def _held_below(rig, ctx, object, height_m):
    z = float(rig.geo.bottom(object, _state(rig, ctx))[2])
    return held_name(rig, "right") == object and z <= float(height_m) + 0.02, f"bottom z {z:.3f} m"


def edge_overhang(rig, name, st):
    """Overhang of a flat object beyond its support's nearest open edge."""
    from . import skills
    s = rig.geo.support_under(name, st)
    if s is None:
        return None, None
    size = np.asarray(rig.ann.asset_of(rig.ann.objects[name])["size"], float)
    b = rig.geo.bottom(name, st)
    yaw = skills._yaw(st["objects"][name]["quat"])
    best = None
    for n in [np.array(d, float) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))]:
        half = skills._half_along(size, yaw, n)
        over = float(n @ b[:2]) + half - skills._edge_coord(s, n)
        if best is None or over > best[0]:
            best = (over, half)
    return best


@predicate("edge_overhang", [("object", "object_ref")], "fluent",
           "A flat object overhangs a support edge enough for an edge pinch (>= 5.5 cm) while its centre "
           "of mass stays 3.5 cm inside the edge.")
def _edge_overhang(rig, ctx, object):
    from . import skills
    over, half = edge_overhang(rig, object, _state(rig, ctx))
    if over is None:
        return False, "not on a support"
    ok = skills.EDGE_MIN_OVERHANG - 0.01 <= over <= half - skills.COM_MARGIN + 0.015
    return ok, f"overhang {over:.3f} m"


@predicate("away_from_edge", [("object", "object_ref"), ("margin_m", "positive_number")], "fluent",
           "Object footprint at least the margin inside every edge of its support.")
def _away_from_edge(rig, ctx, object, margin_m):
    st = _state(rig, ctx)
    s = rig.geo.support_under(object, st)
    if s is None:
        return False, "not on a support"
    fp = rig.geo.footprint(object, st)
    x0, y0, x1, y1 = s["aabb_xy"]
    m = min(fp[0] - x0, fp[1] - y0, x1 - fp[2], y1 - fp[3])
    return m >= float(margin_m) - 0.005, f"edge margin {m:.3f} m"


def neighbour_gap(rig, name, st):
    """Smallest footprint gap to another object on the same support."""
    fp = rig.geo.footprint(name, st)
    s = rig.geo.support_under(name, st)
    gap, who = math.inf, None
    a = rig.ann.asset_of(rig.ann.objects[name])
    for other in rig.ann.objects:
        if other == name:
            continue
        # the object's own contents and lid, and a container holding it, are not neighbours
        if a.get("container") and (rig.geo.inside(other, name, st)[0] or lid_on(rig, name, other, st)[0]):
            continue
        oa = rig.ann.asset_of(rig.ann.objects[other])
        if oa.get("container") and rig.geo.inside(name, other, st)[0]:
            continue
        if s is not None and (rig.geo.support_under(other, st) or {}).get("name") != s["name"]:
            continue
        if s is None and abs(float(rig.geo.bottom(other, st)[2]) - float(rig.geo.bottom(name, st)[2])) > 0.05:
            continue
        o = rig.geo.footprint(other, st)
        dx = max(o[0] - fp[2], fp[0] - o[2], 0.0)
        dy = max(o[1] - fp[3], fp[1] - o[3], 0.0)
        d = math.hypot(dx, dy) if dx > 0 and dy > 0 else max(dx, dy)
        if d < gap:
            gap, who = d, other
    return gap, who


def _neighbour_boxes(rig, name, st):
    """[(name, (x0, y0, z0, x1, y1, z1))] of the objects that count as
    neighbours of ``name`` (same exclusions as neighbour_gap)."""
    s = rig.geo.support_under(name, st)
    a = rig.ann.asset_of(rig.ann.objects[name])
    out = []
    for other in rig.ann.objects:
        if other == name:
            continue
        if a.get("container") and (rig.geo.inside(other, name, st)[0] or lid_on(rig, name, other, st)[0]):
            continue
        oa = rig.ann.asset_of(rig.ann.objects[other])
        if oa.get("container") and rig.geo.inside(name, other, st)[0]:
            continue
        if s is not None and (rig.geo.support_under(other, st) or {}).get("name") != s["name"]:
            continue
        if s is None and abs(float(rig.geo.bottom(other, st)[2]) - float(rig.geo.bottom(name, st)[2])) > 0.05:
            continue
        fp = rig.geo.footprint(other, st)
        b = float(rig.geo.bottom(other, st)[2])
        out.append((other, (fp[0], fp[1], b, fp[2], fp[3], b + float(oa["size"][2]))))
    return out


def finger_slots_free(rig, name, st):
    """(free, detail): is there an annotated pinch of ``name`` whose two finger
    slots (2.8 cm pad x 1.2 cm finger, from the object's bottom up to 4 cm above
    the contact, at the pre-grasp opening) are clear of every neighbour?  None
    when the object has no pinch annotation."""
    obj = rig.ann.objects[name]
    o = st["objects"][name]
    try:
        cands = rig.ann.grasp_poses(obj, np.asarray(o["pos"], float), o["quat"],
                                    kinds=("top_pinch", "rim_pinch", "rim_pinch_rect"))
    except Exception:
        return None, "no pinch annotation"
    if not cands:
        return None, "no pinch annotation"
    boxes = _neighbour_boxes(rig, name, st)
    worst = None
    for g in cands:
        hit = slot_blocker(rig, name, g, st, boxes)
        if hit is None:
            return True, f"pinch at {np.round(np.asarray(g['p'])[:2], 3).tolist()} has both finger slots free"
        worst = hit
    return False, f"every annotated pinch has a finger slot blocked (e.g. by {worst})"


def slot_blocker(rig, name, g, st, boxes=None):
    """Name of the neighbour in one of grasp ``g``'s two finger slots, or None."""
    boxes = _neighbour_boxes(rig, name, st) if boxes is None else boxes
    z0 = float(rig.geo.bottom(name, st)[2]) + 0.003
    close = np.asarray(g["R"][:, 1], float)
    along = np.asarray(g["R"][:, 0], float)
    p = np.asarray(g["p"], float)
    z1 = float(p[2]) + 0.04
    for side in (1.0, -1.0):
        c = p + side * close * (float(g.get("pre_open", 0.04)) + 0.006)
        pts = [c + u * along * 0.014 + v * close * 0.006 for u in (-1, 1) for v in (-1, 1)]
        lo, hi = np.min(pts, axis=0), np.max(pts, axis=0)
        for other, bx in boxes:
            if lo[0] < bx[3] and bx[0] < hi[0] and lo[1] < bx[4] and bx[1] < hi[1] and z0 < bx[5] and bx[2] < z1:
                return other
    return None


@predicate("grasp_clearance", [("object", "object_ref")], "fluent",
           "Some annotated pinch of the object has both finger slots (2.8 x 1.2 cm, at the pre-grasp opening) "
           "free of neighbours; objects without a pinch need 3.5 cm of free footprint gap.")
def _grasp_clearance(rig, ctx, object):
    st = _state(rig, ctx)
    free, why = finger_slots_free(rig, object, st)
    if free is not None:
        return free, why
    gap, who = neighbour_gap(rig, object, st)
    return gap >= GRASP_GAP_M, f"gap {gap:.3f} m to {who}"


@predicate("steadied", [("object", "object_ref")], "fluent",
           "The left gripper pinches the object while it still rests on its support.")
def _steadied(rig, ctx, object):
    if held_name(rig, "left") != object:
        return False, "not in the left hand"
    st = _state(rig, ctx)
    s = rig.geo.support_under(object, st)
    return s is not None, f"support {None if s is None else s['name']}"


def lid_on(rig, container, lid, st):
    cb = np.asarray(rig.geo.bottom(container, st), float)
    rim = rig.ann.asset_of(rig.ann.objects[container])["container"]["rim_height"]
    lb = np.asarray(rig.geo.bottom(lid, st), float)
    dxy = float(np.linalg.norm(lb[:2] - cb[:2]))
    dz = float(lb[2] - (cb[2] + rim))
    t = tilt_deg(st["objects"][lid]["quat"])
    return (dxy <= 0.03 and -0.03 <= dz <= 0.03 and t <= 12.0), f"xy {dxy:.3f} m, dz {dz:.3f} m, tilt {t:.1f}"


def lids(rig):
    return [n for n, o in rig.ann.objects.items() if "lid" in rig.ann.asset_of(o).get("tags", [])]


@predicate("covered", [("container", "container_ref"), ("lid", "lid_ref")], "fluent",
           "The lid rests centred on the container rim (3 cm xy, 3 cm height, 12 deg tilt).")
def _covered(rig, ctx, container, lid):
    return lid_on(rig, container, lid, _state(rig, ctx))


@predicate("uncovered", [("container", "container_ref")], "fluent", "No lid rests on the container rim.")
def _uncovered(rig, ctx, container):
    st = _state(rig, ctx)
    for lid in lids(rig):
        if lid != container and lid_on(rig, container, lid, st)[0]:
            return False, f"{lid} on rim"
    return True, "open"


def objects_inside(rig, container, st):
    return [n for n in rig.ann.objects if n != container and rig.geo.inside(n, container, st)[0]
            and "lid" not in rig.ann.asset_of(rig.ann.objects[n]).get("tags", [])]


@predicate("container_empty", [("container", "container_ref")], "fluent",
           "No annotated object is inside the container.")
def _container_empty(rig, ctx, container):
    inside = objects_inside(rig, container, _state(rig, ctx))
    return not inside, f"contains {inside}"


def objects_on_support(rig, support, st):
    names = _support_names(rig, support)
    out = []
    for n in rig.ann.objects:
        s = rig.geo.support_under(n, st)
        if s is not None and s["name"] in names:
            out.append(n)
    return out


@predicate("all_inside", [("objects", "object_list"), ("container", "container_ref")], "fluent",
           "Every listed object is inside the container.")
def _all_inside(rig, ctx, objects, container):
    st = _state(rig, ctx)
    out = [n for n in objects if not rig.geo.inside(n, container, st)[0]]
    return not out, f"outside: {out}"


@predicate("support_clear", [("support", "support_ref")], "fluent", "No annotated object rests on the support.")
def _support_clear(rig, ctx, support):
    on = objects_on_support(rig, support, _state(rig, ctx))
    return not on, f"objects {on}"


@predicate("grouped", [("objects", "object_list"), ("support", "support_ref"), ("max_dist_m", "positive_number")],
           "fluent", "Every listed object is on the support and pairwise within the distance.")
def _grouped(rig, ctx, objects, support, max_dist_m):
    st = _state(rig, ctx)
    pts = []
    for n in objects:
        ok, _ = rig.geo.on(n, support, st)
        if not ok:
            return False, f"{n} not on {support}"
        pts.append(rig.geo.bottom(n, st)[:2])
    worst = max((float(np.linalg.norm(a - b)) for i, a in enumerate(pts) for b in pts[i + 1:]), default=0.0)
    return worst <= float(max_dist_m), f"largest pair distance {worst:.3f} m"


@predicate("at_initial_place", [("object", "object_ref")], "fluent",
           "Object is back on the support it occupied when the episode started.")
def _at_initial_place(rig, ctx, object):
    s0 = memory(rig)["initial_support"].get(object) or rig.ann.objects[object].get("support")
    if not s0:
        ok, why = _on_floor(rig, ctx, object)
        return ok, f"initially on the floor; {why}"
    return rig.geo.on(object, s0, _state(rig, ctx))


@predicate("sorted_by_category", [("objects", "object_list"), ("rule", "category_map")], "fluent",
           "Each listed object is inside the container (or on the support) mapped to one of its tags.")
def _sorted(rig, ctx, objects, rule):
    st = _state(rig, ctx)
    for n in objects:
        tags = rig.ann.asset_of(rig.ann.objects[n]).get("tags", []) + [rig.ann.objects[n]["asset"]]
        dest = next((rule[t] for t in tags if t in rule), None)
        if dest is None:
            return False, f"no rule for {n}"
        ok = rig.geo.inside(n, dest, st)[0] if dest in rig.ann.objects else rig.geo.on(n, dest, st)[0]
        if not ok:
            return False, f"{n} not in/on {dest}"
    return True, "all sorted"


# --------------------------------------------------------------------- tool / contents memory
@predicate("wiped", [("support", "support_ref")], "memory",
           "A held wiping tool stayed in contact with at least 50 % of the requested strip of the support.")
def _wiped(rig, ctx, support):
    cov = memory(rig)["wiped"].get(support, 0.0)
    return cov >= 0.5, f"coverage {cov:.2f}"


@predicate("stirred", [("container", "container_ref")], "memory",
           "A held utensil tip completed one full circle inside the container below its rim.")
def _stirred(rig, ctx, container):
    turns = memory(rig)["stirred"].get(container, 0.0)
    return turns >= 1.0, f"turns {turns:.2f}"


# --------------------------------------------------------------------- articulated / thermal
def _art_open(rig, name):
    a = rig.ann.art(name)
    q = rig.joint(name)
    span = abs(a["open_q"] - a["closed_q"])
    frac = abs(q - a["closed_q"]) / max(span, 1e-9)
    return frac, q


@predicate("is_open", [("articulated", "articulated_ref")], "fluent",
           "Joint at least 60 % of the way from closed to its annotated open value.")
def _is_open(rig, ctx, articulated):
    frac, q = _art_open(rig, articulated)
    return frac >= 0.6, f"q {q:.3f} ({frac:.0%} open)"


@predicate("is_closed", [("articulated", "articulated_ref")], "fluent",
           "Joint within 0.10 rad (doors) or 4 cm (drawers) of closed.")
def _is_closed(rig, ctx, articulated):
    a = rig.ann.art(articulated)
    q = rig.joint(articulated)
    tol = 0.10 if a["type"] == "revolute" else 0.04
    return abs(q - a["closed_q"]) <= tol, f"q {q:.3f}"


@predicate("heating", [("appliance", "appliance_ref")], "fluent",
           "The appliance's heat source is on (microwave cycle or stove burner).")
def _heating(rig, ctx, appliance):
    th = getattr(rig, "thermal", None)
    ok = th is not None and bool(th.on.get(appliance))
    return ok, f"on {ok}"


@predicate("temperature_at_least", [("object", "object_ref"), ("temp_c", "number")], "fluent",
           "Task-level food temperature at or above the threshold.")
def _temp_ge(rig, ctx, object, temp_c):
    th = getattr(rig, "thermal", None)
    if th is None or object not in th.temperatures_c:
        return False, "no thermal state"
    t = float(th.temperatures_c[object])
    return t >= float(temp_c), f"{t:.1f} C"


@predicate("temperature_at_most", [("object", "object_ref"), ("temp_c", "number")], "fluent",
           "Task-level food temperature at or below the threshold.")
def _temp_le(rig, ctx, object, temp_c):
    th = getattr(rig, "thermal", None)
    if th is None or object not in th.temperatures_c:
        return False, "no thermal state"
    t = float(th.temperatures_c[object])
    return t <= float(temp_c), f"{t:.1f} C"


# --------------------------------------------------------------------- relative (vs. Contract start)
def _before_pos(ctx, name):
    return np.asarray(ctx["before"]["objects"][name]["pos"], float)


@predicate("object_moved", [("object", "object_ref"), ("direction_xy", "unit_vec2"), ("distance_m", "positive_number")],
           "relative", "Object displaced along the direction by at least half the requested distance.")
def _object_moved(rig, ctx, object, direction_xy, distance_m):
    d = np.asarray(direction_xy, float)
    moved = float((rig.obj_pose(object)[0] - _before_pos(ctx, object))[:2] @ d)
    return moved >= max(0.01, 0.5 * float(distance_m)), f"moved {moved:.3f} m"


@predicate("moved_toward_base", [("object", "object_ref"), ("distance_m", "positive_number")], "relative",
           "Object's horizontal distance to the base decreased by at least half the requested distance.")
def _moved_toward_base(rig, ctx, object, distance_m):
    x, y, _ = rig.base_pose()
    x0, y0, _ = ctx["before"]["base_pose"]
    d0 = float(np.linalg.norm(_before_pos(ctx, object)[:2] - np.array([x0, y0])))
    d1 = float(np.linalg.norm(rig.obj_pose(object)[0][:2] - np.array([x, y])))
    return d0 - d1 >= 0.5 * float(distance_m), f"closer by {d0 - d1:.3f} m"


def _rot_angle(q0, q1):
    R = _quat_R(q1) @ _quat_R(q0).T
    return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2))))


@predicate("object_rolled", [("object", "object_ref")], "relative",
           "Object rotated at least 45 deg about a horizontal axis while staying on its side.")
def _object_rolled(rig, ctx, object):
    q0 = ctx["before"]["objects"][object]["quat"]
    q1 = rig.obj_pose(object)[1]
    ang = _rot_angle(q0, q1)
    lying, _, _ = lying_state(rig, object, _state(rig, ctx))
    return ang >= 45.0 and lying, f"rotation {ang:.1f} deg, lying {lying}"


@predicate("yaw_rotated", [("object", "object_ref"), ("degrees", "number")], "relative",
           "Object yaw changed by the requested angle within 10 deg.")
def _yaw_rotated(rig, ctx, object, degrees):
    y0 = math.degrees(_yaw_of_quat(ctx["before"]["objects"][object]["quat"]))
    y1 = math.degrees(_yaw_of_quat(rig.obj_pose(object)[1]))
    err = abs((y1 - y0 - float(degrees) + 180) % 360 - 180)
    return err <= 10.0, f"yaw change {((y1 - y0 + 180) % 360 - 180):.1f} deg"


@predicate("flipped", [("object", "object_ref")], "relative",
           "Object's local z axis now points opposite to its direction at the start (dot <= -0.7).")
def _flipped(rig, ctx, object):
    z0 = _quat_R(ctx["before"]["objects"][object]["quat"])[:, 2]
    z1 = _quat_R(rig.obj_pose(object)[1])[:, 2]
    dot = float(z0 @ z1)
    return dot <= -0.7, f"z dot {dot:.2f}"


@predicate("button_pressed", [("button", "button_ref")], "relative",
           "A measured press of this button happened during the Contract.")
def _button_pressed(rig, ctx, button):
    app, which = button.rsplit("/", 1)
    label = {"start_button": "microwave_start", "door_button": "microwave_door_button"}.get(which)
    events = [e for e in rig.events[ctx["before"]["events"]:]
              if e.get("label") == label or (e.get("label") == "button_press" and e.get("button") == button)]
    return bool(events), f"{len(events)} measured press events"


@predicate("poured_into", [("source", "container_ref"), ("target", "container_ref")], "relative",
           "At least half of the items that were inside the source are now inside the target.")
def _poured_into(rig, ctx, source, target):
    items = ctx["before"].get("contents", {}).get(source, [])
    if not items:
        return False, "source held no items at the start"
    st = _state(rig, ctx)
    moved = [n for n in items if rig.geo.inside(n, target, st)[0]]
    return len(moved) >= math.ceil(len(items) / 2), f"{len(moved)}/{len(items)} items in {target}"


@predicate("positions_swapped", [("a", "object_ref"), ("b", "object_ref")], "relative",
           "Each object now rests within 6 cm of the other's starting position on its starting support.")
def _positions_swapped(rig, ctx, a, b):
    st = _state(rig, ctx)
    pa0, pb0 = ctx["before"]["bottoms"][a], ctx["before"]["bottoms"][b]
    pa1 = rig.geo.bottom(a, st)
    pb1 = rig.geo.bottom(b, st)
    ea = float(np.linalg.norm(pa1[:2] - np.asarray(pb0[:2])))
    eb = float(np.linalg.norm(pb1[:2] - np.asarray(pa0[:2])))
    return max(ea, eb) <= 0.06 and abs(pa1[2] - pb0[2]) < 0.05 and abs(pb1[2] - pa0[2]) < 0.05, \
        f"errors {ea:.3f} / {eb:.3f} m"


# --------------------------------------------------------------------- helpers for callers
def before_snapshot(rig):
    """State captured when a Contract starts; relative predicates compare to it."""
    st = rig.state()
    contents = {}
    bottoms = {}
    for n, o in rig.ann.objects.items():
        bottoms[n] = [float(v) for v in rig.geo.bottom(n, st)]
        if rig.ann.asset_of(o).get("container"):
            contents[n] = objects_inside(rig, n, st)
    return {"objects": st["objects"], "joints": st["joints"], "base_pose": tuple(rig.base_pose()),
            "tick": rig.tick,
            "events": len(rig.events), "contents": contents, "bottoms": bottoms,
            "held": held_name(rig, "right"), "left_held": held_name(rig, "left")}


def evaluate_atom(rig, atom: dict, values: dict, ctx: dict):
    """Evaluate one contract atom ``{"pred", "args", "negated"?}`` with ``$slot``
    references bound from ``values``."""
    pred = REGISTRY[atom["pred"]]
    args = {k: resolve(v, values) for k, v in atom.get("args", {}).items()}
    ok, detail = pred.evaluate(rig, ctx, **args)
    if atom.get("negated"):
        ok = not ok
    return bool(ok), detail, args


def resolve(value, values):
    if isinstance(value, str) and value.startswith("$"):
        key = value[1:]
        if key not in values:
            raise KeyError(f"unbound slot {value}")
        return values[key]
    return value


def atom_text(atom: dict) -> str:
    args = ", ".join(f"{k}={v}" for k, v in atom.get("args", {}).items())
    return ("not " if atom.get("negated") else "") + f"{atom['pred']}({args})"


# --------------------------------------------------------------------- added verbs (shake ... hover)
def _mem(rig, key):
    return memory(rig).setdefault(key, {})


@predicate("shaken", [("object", "object_ref")], "memory",
           "The held object was oscillated at least three times with >= 2 cm amplitude without slipping.")
def _shaken(rig, ctx, object):
    n = _mem(rig, "shaken").get(object, 0)
    return n >= 3, f"{n} measured cycles"


@predicate("waited", [("seconds", "positive_number")], "relative",
           "At least the given simulated time passed during the Contract.")
def _waited(rig, ctx, seconds):
    dt = (rig.tick - ctx["before"].get("tick", rig.tick)) / 120.0
    return dt >= float(seconds) - 0.05, f"{dt:.2f} s elapsed"


@predicate("waved", [], "memory", "The right hand performed a measured wave (>= 2 lateral swings at head height).")
def _waved(rig, ctx):
    n = _mem(rig, "gestures").get("wave", 0)
    return n >= 2, f"{n} swings"


@predicate("nodded", [], "memory", "The head performed a measured nod (>= 2 pitch cycles of >= 0.2 rad).")
def _nodded(rig, ctx):
    n = _mem(rig, "gestures").get("nod", 0)
    return n >= 2, f"{n} cycles"


@predicate("knocked", [("articulated", "articulated_ref")], "relative",
           "Two measured fingertip contacts on the closed panel during the Contract; the joint moved < 0.05.")
def _knocked(rig, ctx, articulated):
    ev = [e for e in rig.events[ctx["before"]["events"]:] if e.get("label") == "knock_contact"
          and e.get("articulated") == articulated]
    q0 = ctx["before"]["joints"].get(articulated, rig.joint(articulated))
    moved = abs(rig.joint(articulated) - q0)
    return len(ev) >= 2 and moved < 0.05, f"{len(ev)} contacts, joint moved {moved:.3f}"


@predicate("touched", [("object", "object_ref")], "relative",
           "A measured fingertip contact with the object's top during the Contract; it moved < 1.5 cm.")
def _touched(rig, ctx, object):
    ev = [e for e in rig.events[ctx["before"]["events"]:] if e.get("label") == "touch_contact" and e.get("obj") == object]
    moved = float(np.linalg.norm(rig.obj_pose(object)[0] - _before_pos(ctx, object)))
    return bool(ev) and moved < 0.015, f"{len(ev)} contacts, moved {moved:.3f} m"


def _support_axes_err(rig, name, st):
    q = st["objects"][name]["quat"]
    yaw = math.degrees(_yaw_of_quat(q))
    return abs((yaw + 45) % 90 - 45)


@predicate("squared", [("object", "object_ref")], "fluent",
           "Object yaw within 5 deg of the support's axes (edges parallel), resting on a support.")
def _squared(rig, ctx, object):
    st = _state(rig, ctx)
    err = _support_axes_err(rig, object, st)
    s = rig.geo.support_under(object, st)
    return err <= 5.0 and s is not None, f"yaw off axis {err:.1f} deg"


@predicate("hidden", [("object", "object_ref")], "fluent",
           "Object is inside a lid-covered container or on a shelf inside a closed cabinet.")
def _hidden(rig, ctx, object):
    st = _state(rig, ctx)
    for c, o in rig.ann.objects.items():
        if c != object and rig.ann.asset_of(o).get("container") and rig.geo.inside(object, c, st)[0]:
            if any(lid_on(rig, c, l, st)[0] for l in lids(rig) if l != c):
                return True, f"in covered {c}"
    s = rig.geo.support_under(object, st)
    if s is not None and s.get("category") == "cabinet_inside":
        a = next((x for x in rig.ann.articulated if x["name"] == s.get("furniture")), None)
        if a is not None:
            tol = 0.10 if a["type"] == "revolute" else 0.04
            if abs(rig.joint(a["name"]) - a["closed_q"]) <= tol:
                return True, f"in closed {a['name']}"
    return False, "visible"


@predicate("clustered", [("objects", "object_list"), ("radius_m", "positive_number")], "fluent",
           "Every listed object's footprint centre lies within the radius of the group centroid, on one support.")
def _clustered(rig, ctx, objects, radius_m):
    st = _state(rig, ctx)
    pts = np.array([rig.geo.bottom(n, st)[:2] for n in objects])
    c = pts.mean(axis=0)
    worst = float(np.max(np.linalg.norm(pts - c, axis=1)))
    sups = {(rig.geo.support_under(n, st) or {}).get("name") for n in objects}
    return worst <= float(radius_m) and len(sups) == 1 and None not in sups, f"max {worst:.3f} m from centroid"


@predicate("identified", [("object", "object_ref")], "memory",
           "The robot recorded the object's category while it was in the head camera view.")
def _identified(rig, ctx, object):
    rec = _mem(rig, "identified").get(object)
    return rec is not None, f"{rec}"


@predicate("measured", [("object", "object_ref")], "memory",
           "The robot recorded the object's size from a view with the object in the head camera.")
def _measured(rig, ctx, object):
    rec = _mem(rig, "measured").get(object)
    return rec is not None, f"{rec}"


@predicate("counted", [("category", "tag")], "memory",
           "The robot recorded how many objects of the category it sees from its current place.")
def _counted(rig, ctx, category):
    rec = _mem(rig, "counted").get(category)
    return rec is not None, f"{rec}"


@predicate("dipped", [("container", "container_ref")], "memory",
           "A held utensil tip entered the container below its rim and came back out.")
def _dipped(rig, ctx, container):
    ok = bool(_mem(rig, "dipped").get(container))
    return ok, f"dipped {ok}"


@predicate("sidestepped", [("distance_m", "number")], "relative",
           "Base moved sideways by the signed distance (left > 0) within 3 cm, heading unchanged within 3 deg.")
def _sidestepped(rig, ctx, distance_m):
    x0, y0, yaw0 = ctx["before"]["base_pose"]
    x1, y1, yaw1 = rig.base_pose()
    lat = -(x1 - x0) * math.sin(math.radians(yaw0)) + (y1 - y0) * math.cos(math.radians(yaw0))
    ok = abs(lat - float(distance_m)) <= 0.03 and abs((yaw1 - yaw0 + 180) % 360 - 180) <= 3
    return ok, f"lateral {lat:.3f} m"


@predicate("hovering_over", [("object", "object_ref"), ("target", "entity_ref")], "fluent",
           "The right-held object's bottom is 3-15 cm above the target's top, centred within 4 cm.")
def _hovering_over(rig, ctx, object, target):
    if held_name(rig, "right") != object:
        return False, "not right-held"
    st = _state(rig, ctx)
    b = rig.geo.bottom(object, st)
    kind, rec = entity_kind(rig.ann, target)
    if kind == "object":
        t = np.asarray(rig.geo.bottom(target, st), float)
        a = rig.ann.asset_of(rec)
        top = t[2] + (a["container"]["rim_height"] if a.get("container") else a["size"][2])
        c = t[:2]
    else:
        p = entity_point(rig, target, st)
        top, c = p[2], p[:2]
    dxy = float(np.linalg.norm(b[:2] - c))
    dz = float(b[2] - top)
    return dxy <= 0.04 and 0.03 <= dz <= 0.15, f"xy {dxy:.3f} m, above by {dz:.3f} m"


# --------------------------------------------------------------------- GT provenance
# Which ground-truth signals each predicate's evaluator reads (exported with the
# SkillNode JSON so a planner knows what a verified fact rests on).
GT_SOURCES = {
    "hand_empty": ["gripper_state"], "holding": ["gripper_state", "finger_joints", "object_pose", "arm_fk"],
    "arm_stowed": ["arm_joints"], "torso_lowered": ["torso_joint"], "torso_at": ["torso_joint"], "torso_raised": ["torso_joint"],
    "waist_bent": ["waist_joint"], "waist_straight": ["waist_joint"],
    "base_near": ["base_pose", "scene_annotation"], "base_clear_of": ["base_pose", "scene_annotation"],
    "reachable": ["base_pose", "arm_ik", "collision_model", "object_pose", "grasp_annotation"],
    "facing": ["base_pose", "scene_annotation"], "in_view": ["base_pose", "head_joints", "head_fk", "collision_model"],
    "observed": ["robot_memory"], "pointing_at": ["arm_fk", "scene_annotation"],
    "presenting": ["object_pose", "base_pose", "head_fk"], "room_explored": ["robot_memory", "room_annotation"],
    "on": ["object_pose", "asset_annotation", "support_annotation"],
    "inside": ["object_pose", "container_profile"], "in_appliance": ["object_pose", "appliance_annotation"],
    "on_burner": ["object_pose", "appliance_annotation"],
    "in_cookware_on_burner": ["object_pose", "container_profile", "appliance_annotation"],
    "on_top_of": ["object_pose", "asset_annotation"], "top_clear": ["object_pose", "asset_annotation"],
    "on_floor": ["object_pose", "asset_annotation"], "upright": ["object_pose"], "lying": ["object_pose", "asset_annotation"],
    "held_above": ["object_pose", "gripper_state"], "held_below": ["object_pose", "gripper_state"],
    "edge_overhang": ["object_pose", "asset_annotation", "support_annotation"],
    "away_from_edge": ["object_pose", "support_annotation"], "grasp_clearance": ["object_pose", "asset_annotation"],
    "steadied": ["left_gripper_state", "object_pose"], "covered": ["object_pose", "container_profile"],
    "uncovered": ["object_pose", "container_profile", "asset_tags"],
    "container_empty": ["object_pose", "container_profile"], "all_inside": ["object_pose", "container_profile"],
    "support_clear": ["object_pose", "support_annotation"], "grouped": ["object_pose", "support_annotation"],
    "at_initial_place": ["object_pose", "initial_scene_annotation"],
    "sorted_by_category": ["object_pose", "asset_tags", "container_profile"],
    "wiped": ["robot_memory (tool-bottom contact samples)"], "stirred": ["robot_memory (tool-tip samples)"],
    "is_open": ["articulation_joint", "articulation_annotation"], "is_closed": ["articulation_joint", "articulation_annotation"],
    "heating": ["thermal_state"], "temperature_at_least": ["thermal_state"], "temperature_at_most": ["thermal_state"],
    "object_moved": ["object_pose (before/after)"], "moved_toward_base": ["object_pose (before/after)", "base_pose"],
    "object_rolled": ["object_pose (before/after)"], "yaw_rotated": ["object_pose (before/after)"],
    "flipped": ["object_pose (before/after)"], "button_pressed": ["event_log (measured fingertip contact)"],
    "poured_into": ["object_pose (before/after)", "container_profile"],
    "positions_swapped": ["object_pose (before/after)"],
    "shaken": ["robot_memory (TCP oscillation + hold checks)"], "waited": ["sim_clock"],
    "waved": ["robot_memory (TCP swing samples)"], "nodded": ["robot_memory (head joint samples)"],
    "knocked": ["event_log (fingertip contact)", "articulation_joint"],
    "touched": ["event_log (fingertip contact)", "object_pose (before/after)"],
    "squared": ["object_pose", "support_annotation"],
    "hidden": ["object_pose", "container_profile", "articulation_joint", "support_annotation"],
    "clustered": ["object_pose", "support_annotation"], "identified": ["robot_memory", "asset_annotation"],
    "measured": ["robot_memory", "asset_annotation", "object_pose"], "counted": ["robot_memory", "head_fk"],
    "dipped": ["robot_memory (tool-tip samples)"], "sidestepped": ["base_pose (before/after)"],
    "hovering_over": ["object_pose", "gripper_state", "asset_annotation"],
}
missing = set(REGISTRY) - set(GT_SOURCES)
if missing:
    raise RuntimeError(f"GT provenance missing for {sorted(missing)}")
