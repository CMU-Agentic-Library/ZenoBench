"""Observation-limited execution for an upper-level planner (VLM).

The planner sees what the robot's head camera saw, never the hidden GT scene:

* ``Observer`` keeps the robot's observation cache (last seen pose, support /
  container, tick of every object that was ever visible), the set of objects
  visible in the latest view, the static layout (rooms, furniture, supports,
  doors, appliances, buttons) and first-person images.  Visibility is the
  GT-assisted detector of ``zeno_skills.perception`` (frustum, range, static
  line of sight) with dynamic occlusion switched on (closed doors, lids,
  container walls, other objects).
* ``GatedRunner`` is a SkillContractRunner whose every call - top level and
  every nested Contract of a multi-object skill - passes the same permission
  check before anything moves:

  - an object argument must be in the observation cache (or held); a hidden
    object and a name that does not exist get the same refusal, and nothing
    moves;
  - a contact skill (pick, push, place into, stir ...) additionally needs its
    object arguments in the current view or in the hand: a pick does not track
    an object that left the view;
  - navigate / approach to an object drive to its *cached* position (the GT
    pose of an object that moved out of sight is never used); look-type skills
    at a stale object first glance at the cached position;
  - support / container lists inside multi-object skills (clear, empty) are
    restricted to observed objects;
  - search accepts any name (that is what search is for); for a name that is
    not in the scene it runs the same static sweep and returns the same
    failure as for a hidden object.

  The runner is built without automatic repair (no nested separate/expose
  retry), without the automatic slide-to-edge inside pick and with the
  feasibility estimates grasp_clearance / edge_overhang advisory, so a pick
  that cannot work fails physically and the caller decides what to do next.

The GT runner (``zeno_skills.skill_runtime.SkillContractRunner`` as used by
``tools/verify_skills.py``) is unchanged and stays the trusted physical
acceptance entry.
"""

from __future__ import annotations

import contextlib
import re
from pathlib import Path

import numpy as np

from zeno_skills.skill_runtime import SkillContractRunner, SkillResult, ContractError
from zeno_skills import skill_runtime as _sr

OBJECT_SLOTS = {"object_ref", "container_ref", "lid_ref", "tool_ref"}
MIXED_SLOTS = {"receptacle_ref", "entity_ref", "place_ref"}       # object or static place
LIST_SLOTS = {"object_list"}

# verbs whose object arguments are touched: they need the object in view or in hand
CONTACT_VERBS = {"pick", "place", "drop", "stack", "release", "handover", "lift", "lower", "rotate", "regrasp",
                 "brace", "flip", "push", "pull", "expose", "separate", "center", "roll", "tip", "upright",
                 "wipe", "stir", "pour", "cover", "uncover", "present", "shake", "hover", "square", "touch",
                 "sweep", "dip"}
MANIPULATED_SLOTS = {"object", "objects", "a", "b", "tool", "lid", "source"}
MANIPULATED_EXTRA = {("uncover", "container"), ("brace", "object")}
# verbs that only move the base / head toward a known (possibly cached) place
MOTION_VERBS = {"navigate", "approach"}
LOOK_VERBS = {"look", "face", "point", "identify", "measure", "inspect"}

STALE_M = 0.03
REFUSAL = "'{name}' is not a known place or an observed object"
ADVISORY = ("grasp_clearance", "edge_overhang")
NO_AUTO_STEPS = {("pick", "flat_edge"): {"policy_045"}}            # the automatic slide-to-edge (= expose)


# ----------------------------------------------------------------- static layout
def static_places(ann) -> dict:
    """Named places the robot knows from the static floor plan."""
    from zeno_skills.evaluator import room_of
    out = {}
    for r in ann.rooms:
        out[r] = {"kind": "room"}
    for s in ann.supports:
        x0, y0, x1, y1 = s["aabb_xy"]
        c = [(x0 + x1) / 2, (y0 + y1) / 2]
        out[s["name"]] = {"kind": "support", "category": s.get("category"), "furniture": s.get("furniture"),
                          "z": s["z"], "center": [round(c[0], 3), round(c[1], 3)], "room": room_of(ann.rooms, c),
                          "size": [round(x1 - x0, 3), round(y1 - y0, 3)]}
        f = s.get("furniture")
        if f and f not in out:
            out[f] = {"kind": "furniture", "category": s.get("category"), "room": room_of(ann.rooms, c)}
    for a in ann.articulated:
        rec = out.setdefault(a["name"], {"kind": "furniture"})
        rec.update({"articulated": True, "category": a.get("category") or rec.get("category"), "joint": a["type"]})
        for b in ("door_button", "start_button"):
            if isinstance(a.get(b), dict):
                out[f"{a['name']}/{b}"] = {"kind": "button", "appliance": a["name"]}
    for a in getattr(ann, "appliances", []):
        out.setdefault(a["name"], {}).update({"kind": "appliance", "category": a.get("category")})
        if isinstance(a.get("power_button"), dict):
            out[f"{a['name']}/power_button"] = {"kind": "button", "appliance": a["name"]}
    return out


class Observer:
    """Observation cache and current view of one rig (installs itself on it)."""

    def __init__(self, rig, image_dir=None):
        self.rig = rig
        self.cache: dict[str, dict] = {}
        self.view: set[str] = set()
        self.places = static_places(rig.ann)
        self.image_dir = Path(image_dir) if image_dir else None
        self.images: list[str] = []
        self.n_snap = 0
        self.gated = True               # GatedRunner(gate=False) clears it: lists inside skills stay unfiltered
        rig.observer = self
        # the rig switches of the benchmark (occlusion, static explore, no automatic recovery) come from
        # the episode profile: episode.profile.apply_rig_flags

    # ------------------------------------------------------------- state
    def held(self):
        r = self.rig
        return {(r.held or {}).get("name"), (getattr(r, "left_held", None) or {}).get("name")} - {None}

    def visible(self, name, st=None):
        from zeno_skills.perception import project_to_head_camera
        st = st or self.rig.state()
        return bool(project_to_head_camera(self.rig, self.rig.geo.centre(name, st), exclude=name)[0])

    def _record(self, name, st):
        rig = self.rig
        sup = rig.geo.support_under(name, st)
        inside = next((c for c, o in rig.ann.objects.items() if c != name and rig.ann.asset_of(o).get("container")
                       and rig.geo.inside(name, c, st)[0]), None)
        o = st["objects"][name]
        self.cache[name] = {"pos": [round(float(v), 4) for v in o["pos"]], "quat": [float(v) for v in o["quat"]],
                            "support": sup["name"] if sup else None, "inside": inside,
                            "on_floor": bool(rig.geo.bottom(name, st)[2] < 0.05), "tick": rig.tick}

    def on_view(self, seen):
        """Hook called by the skills' own record_view (look, search, explore ...)."""
        st = self.rig.state()
        for n in seen:
            self._record(n, st)

    def snapshot(self, tag=None, image=False):
        """Detect the objects visible from the current head pose; update the cache."""
        rig = self.rig
        st = rig.state()
        vis = [n for n in rig.ann.objects if self.visible(n, st)]
        self.view = set(vis) | self.held()
        for n in self.view:
            self._record(n, st)
        if image and self.image_dir is not None and getattr(rig, "first_person_camera", None) is not None:
            import cv2
            self.image_dir.mkdir(parents=True, exist_ok=True)
            self.n_snap += 1
            path = self.image_dir / f"{self.n_snap:03d}_{re.sub(r'[^A-Za-z0-9_]+', '_', tag or 'view')[:60]}.jpg"
            cv2.imwrite(str(path), rig.get_first_person_image()[..., ::-1])
            self.images.append(str(path))
        return sorted(vis)

    def known(self, name):
        return name in self.cache or name in self.held()

    def fresh(self, name):
        return name in self.view or name in self.held()

    def stale(self, name):
        """Cached pose differs from GT and the object is not in view: the
        planner's belief is out of date (the GT pose must not be used)."""
        if name not in self.cache or self.fresh(name):
            return False
        p = np.asarray(self.rig.obj_pose(name)[0], float)
        return float(np.linalg.norm(p - np.asarray(self.cache[name]["pos"]))) > STALE_M

    def known_point(self, name):
        """A world point of a known place or of an object's cached pose."""
        from zeno_skills.predicates import entity_point
        if name in self.rig.ann.objects:
            st = self.belief_state()
            return np.asarray(self.rig.geo.centre(name, st), float)
        return np.asarray(entity_point(self.rig, name), float)

    def belief_state(self, names=None):
        """rig.state() with the given (default: every stale) object at its cached pose."""
        st = self.rig.state()
        for n in (names if names is not None else [k for k in self.cache if self.stale(k)]):
            if n in self.cache and n in st["objects"]:
                st["objects"][n] = {"pos": list(self.cache[n]["pos"]), "quat": list(self.cache[n]["quat"])}
        return st

    @contextlib.contextmanager
    def believed(self, names):
        """Temporarily show the planner/IK the cached pose of ``names``."""
        if not names:
            yield
            return
        rig = self.rig
        orig = rig.state
        cached = {n: dict(self.cache[n]) for n in names}

        def state():
            st = orig()
            for n, c in cached.items():
                st["objects"][n] = {"pos": list(c["pos"]), "quat": list(c["quat"])}
            return st
        rig.state = state
        rig.log("belief_override", objects=sorted(names))
        try:
            yield
        finally:
            rig.state = orig

    def glance(self, name, tag=None, image=False):
        """Aim the head (no base motion) at a known place / cached object position."""
        try:
            p = self.known_point(name)
        except Exception:
            return self.snapshot(tag, image)
        return self.glance_point(p, tag, image)

    def glance_point(self, p, tag=None, image=False):
        from zeno_skills.perception import look_angles
        from zeno_skills.policies.perceive import drive_head
        yaw, pitch = look_angles(self.rig, p)
        drive_head(self.rig, yaw, pitch, steps=60)
        return self.snapshot(tag, image)

    def scan(self, place, tag=None, image=False):
        """Head-only scan along a long support (a 1.7 m island seen from 0.5 m
        does not fit one view): both ends, then back to the centre."""
        rec = self.places.get(place) or {}
        sups = [s for s in self.rig.ann.supports if s["name"] == place or
                (rec.get("kind") == "furniture" and s.get("furniture") == place)]
        if not sups:
            return self.snapshot(tag, image)
        top = max(sups, key=lambda s: s["z"])
        x0, y0, x1, y1 = top["aabb_xy"]
        if max(x1 - x0, y1 - y0) < 0.6:
            return self.snapshot(tag, image)
        c = np.array([(x0 + x1) / 2, (y0 + y1) / 2, top["z"]])
        ax = np.array([1.0, 0.0, 0.0]) if x1 - x0 >= y1 - y0 else np.array([0.0, 1.0, 0.0])
        half = 0.5 * max(x1 - x0, y1 - y0) - 0.12
        for f in (-1.0, 1.0):
            self.glance_point(c + ax * f * half)
        seen = set(self.view)
        out = self.glance_point(c, tag, image)
        self.view |= {n for n in seen if self.visible(n)}
        return sorted(self.view)

    # ------------------------------------------------------------- planner-facing
    def describe(self, name):
        rig = self.rig
        o = rig.ann.objects[name]
        a = rig.ann.asset_of(o)
        c = self.cache.get(name, {})
        return {"name": name, "category": o["asset"], "tags": list(a.get("tags", [])),
                "in_view": name in self.view, "held": name in self.held(),
                "last_seen_position": c.get("pos"), "last_seen_on": c.get("support"), "last_seen_in": c.get("inside"),
                "last_seen_tick": c.get("tick")}

    def mask(self, value, allow=()):
        """Replace names of objects the robot never observed in a feedback value
        (names in ``allow`` - the planner's own arguments - are kept)."""
        hidden = [n for n in self.rig.ann.objects if not self.known(n) and n not in allow]
        if not hidden:
            return value
        pat = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(re.escape(n) for n in sorted(hidden, key=len, reverse=True))
                         + r")(?![A-Za-z0-9_])")

        def m(v):
            if isinstance(v, str):
                return pat.sub("<unobserved>", v)
            if isinstance(v, dict):
                return {m(k): m(x) for k, x in v.items()}
            if isinstance(v, (list, tuple)):
                return [m(x) for x in v if not (isinstance(x, str) and x in hidden)]
            return v
        return m(value)


# ----------------------------------------------------------------- gated runner
def _filtered_bind(orig):
    def bind_nouns(rig, contract, values):
        nouns = orig(rig, contract, values)
        obs = getattr(rig, "observer", None)
        if obs is not None and obs.gated:
            for d in nouns.values():
                if isinstance(d, dict):
                    for key in ("objects", "contents"):
                        if isinstance(d.get(key), list):
                            d[key] = [n for n in d[key] if obs.known(n)]
        return nouns
    bind_nouns._gated = True
    return bind_nouns


if not getattr(_sr.bind_nouns, "_gated", False):
    _sr.bind_nouns = _filtered_bind(_sr.bind_nouns)


class GatedRunner(SkillContractRunner):
    """``gate=False`` keeps the observation cache up to date (the head looks where the
    robot worked, perception outputs are recorded) but refuses nothing and uses GT poses."""

    def __init__(self, rig, observer=None, *, capture_images=True, gate=True, **kw):
        kw.setdefault("auto_repair", False)
        kw.setdefault("advisory", ADVISORY)
        kw.setdefault("skip_steps", NO_AUTO_STEPS)
        super().__init__(rig, **kw)
        self.obs = observer or getattr(rig, "observer", None) or Observer(rig)
        self.gate = gate
        self.obs.gated = gate
        self.capture_images = capture_images
        self.calls: list[dict] = []

    # ------------------------------------------------------------- permission check
    def _object_args(self, c, args):
        """(slot, name, contact) for every argument that names a scene object
        or an unknown name in a place/entity slot."""
        out = []
        contact = c["verb"] in CONTACT_VERBS
        for slot, meta in c["inputs"].items():
            v = args.get(slot)
            if v is None:
                continue
            t = meta["type"]
            # the object being manipulated needs the current view (or the hand); a destination
            # (receptacle, stacking base, stirred pot ...) only needs to be known, like a navigation goal
            touched = contact and (slot in MANIPULATED_SLOTS or (c["verb"], slot) in MANIPULATED_EXTRA)
            if t in OBJECT_SLOTS:
                out.append((slot, v, touched))
            elif t in LIST_SLOTS:
                out += [(slot, x, touched) for x in (v or [])]
            elif t in MIXED_SLOTS:
                if v in self.rig.ann.objects or v not in self.obs.places:
                    out.append((slot, v, False))
        return out

    def check(self, c, args):
        """None, or (code, message) of a refusal.  Same text for hidden and non-existent objects."""
        verb = c["verb"]
        for slot, name, contact in self._object_args(c, args):
            if verb == "search" and slot == "object":
                continue
            if not isinstance(name, str) or not self.obs.known(name):
                return "NOT_OBSERVED", REFUSAL.format(name=name)
            if contact and not self.obs.fresh(name):
                return "NOT_IN_VIEW", f"'{name}' is not in the current view (last seen at tick " \
                                      f"{self.obs.cache[name]['tick']}); look at it first"
        for slot in ("receptacle", "support", "surface", "destination", "obstacle", "target", "region", "room",
                     "furniture", "articulated", "appliance", "button"):
            v = args.get(slot)
            if isinstance(v, str) and slot in c["inputs"] and v not in self.rig.ann.objects \
                    and v not in self.obs.places:
                return "NOT_OBSERVED", REFUSAL.format(name=v)
        return None

    def _refused(self, c, args, code, msg, depth):
        action = f"{c['action_predicate']['name']}(" + ", ".join(
            f"{k}={args[k]}" for k in c["action_predicate"]["arguments"] if args.get(k) is not None) + ")"
        res = SkillResult(c["contract_id"], c["skill_id"], action, False, None, [], [], [], {}, {},
                          error=f"{code}: {msg}", error_code=code)
        self.rig.log("gate_refused", action=action, code=code, depth=depth)
        self.trace.append(res.asdict())
        return res

    # ------------------------------------------------------------- run
    def run(self, key, args, depth=0):
        c = self.contract(key)
        verb = c["verb"]
        rig = self.rig
        if not self.gate:
            res = super().run(key, args, depth)
            self._after(c, args, res, depth)
            return res
        refusal = self.check(c, args)
        if refusal:
            res = self._refused(c, args, *refusal, depth)
            self._log_call(c, args, res, depth)
            return res
        if verb == "search" and args.get("object") not in rig.ann.objects:
            res = self._phantom_search(c, args, depth)
            self._after(c, args, res, depth)
            return res
        names = [n for _, n, _ in self._object_args(c, args) if n in rig.ann.objects]
        stale = [n for n in names if self.obs.stale(n)]
        if stale and verb in LOOK_VERBS:
            # aim where the robot believes the object is; if it is not there the
            # look fails without the GT pose ever steering the head
            for n in stale:
                self.obs.glance(n)
            missing = [n for n in stale if not self.obs.fresh(n)]
            if missing:
                res = self._refused(c, args, "NOT_FOUND", f"'{missing[0]}' is not visible at its last "
                                    "observed position", depth)
                self._after(c, args, res, depth)
                return res
            stale = []
        ctx = self.obs.believed(stale) if verb in MOTION_VERBS else contextlib.nullcontext()
        with ctx:
            res = super().run(key, args, depth)
        self._after(c, args, res, depth)
        return res

    def _after(self, c, args, res, depth):
        verb = c["verb"]
        tag = f"{depth}_{verb}_{'ok' if res.success else 'fail'}"
        image = self.capture_images and depth == 0
        dest = args.get("destination") or args.get("target")
        if verb in MOTION_VERBS and isinstance(dest, str):
            self.obs.glance(dest, tag, image)          # arriving robots look where they went
        elif verb == "look" and res.success and isinstance(dest, str) and dest in self.obs.places:
            self.obs.scan(dest, tag, image)            # a long support is scanned end to end
        elif verb in CONTACT_VERBS and self._work_target(c, args):
            # keep the eyes on the workspace: the cached (pre-call) position of
            # the object worked on, never its GT pose after the call
            self.obs.glance(self._work_target(c, args), tag, image)
        else:
            self.obs.snapshot(tag, image)
        for key in ("seen", "objects", "contents"):     # perception outputs are observations too
            v = (res.outputs or {}).get(key)
            if isinstance(v, list):
                self.obs.on_view([n for n in v if n in self.rig.ann.objects])
        self._log_call(c, args, res, depth)

    def _work_target(self, c, args):
        for slot in ("object", "container", "base", "receptacle", "surface", "objects"):
            v = args.get(slot)
            v = v[0] if isinstance(v, list) and v else v
            if isinstance(v, str) and (v in self.obs.cache or v in self.obs.places) and v not in self.obs.held():
                return v
        return None

    def _log_call(self, c, args, res, depth):
        self.calls.append({"depth": depth, "verb": c["verb"], "args": args, "success": res.success,
                           "error_code": res.error_code, "error": res.error, "path": res.selected_path,
                           "tick": self.rig.tick, "view": sorted(self.obs.view),
                           "image": self.obs.images[-1] if (depth == 0 and self.obs.images) else None})

    def _phantom_search(self, c, args, depth):
        """The static sweep of search for a name that is not in the scene: the
        same route and the same failure text a hidden object produces."""
        from zeno_skills.policies.perceive import SearchObjectPolicy
        from zeno_skills.rig import SkillFailure
        name = args["object"]
        rig = self.rig
        action = f"{c['action_predicate']['name']}(" + ", ".join(
            f"{k}={args[k]}" for k in c["action_predicate"]["arguments"] if args.get(k) is not None) + ")"
        res = SkillResult(c["contract_id"], c["skill_id"], action, False, "room_sweep", [], [], [], {}, {})
        geo = rig.geo
        orig_centre = geo.centre

        def centre(n, st):
            return np.array([1e4, 1e4, -1e3]) if n == name else orig_centre(n, st)
        geo.centre = centre
        rig.log("contract_start", contract=c["contract_id"], action=action, depth=depth)
        try:
            SearchObjectPolicy(rig).execute(name, args.get("region"))
            res.error, res.error_code = f"search {name}: not seen", "POLICY_FAILED"
        except SkillFailure as exc:
            res.error, res.error_code = str(exc), "POLICY_FAILED"
        finally:
            geo.centre = orig_centre
        rig.log("contract_end", contract=c["contract_id"], action=action, success=False, path="room_sweep",
                error=res.error)
        self.trace.append(res.asdict())
        return res
