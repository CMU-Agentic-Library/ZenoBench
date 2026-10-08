"""Symbolic planner over the exported SkillNode pre/postconditions.

It shows that tasks decompose into the library: the initial state is built by
evaluating the *same* GT predicates on the annotated scene (no simulator), each
SkillNode is applied through its requires / path requires / ensures /
invalidates, and A* searches for a sequence that makes the goal atoms true.

The result is a schema-2 skill subgraph with grounded ``value`` arguments that
skill_library.graph validates and skill_library.runtime executes.

    python -m skill_library.planner --task-catalog skill_library/tasks.json --all
"""

from __future__ import annotations

import argparse
import heapq
import itertools
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


# ----------------------------------------------------------------- offline scene
class OfflineRig:
    """Rig-shaped view of an annotation file: objects at their annotated poses,
    articulated parts closed, robot at its start pose with the arm folded."""

    def __init__(self, annotation_path, task=None):
        from zeno_skills.annotations import SceneAnnotations
        from zeno_skills.evaluator import Geometry
        from zeno_skills.kinematics import ArmKin
        self.ann = SceneAnnotations(ROOT / annotation_path)
        self.geo = Geometry(self.ann)
        self.kin = ArmKin()
        self.left_kin = ArmKin(side="left")
        self.held = self.left_held = None
        self.thermal = None
        self.events = []
        self.tick = 0
        self.memory = {"observed": {}, "wiped": {}, "stirred": {}, "explored": {},
                       "initial_support": {n: o.get("support") for n, o in self.ann.objects.items()}}
        placed = (task or {}).get("placed_objects", {})
        self._state = {"objects": {}, "joints": {a["name"]: a["closed_q"] for a in self.ann.articulated}}
        for n, o in self.ann.objects.items():
            yaw = placed.get(n, {}).get("yaw", 0.0)
            self._state["objects"][n] = {"pos": list(o["position"]),
                                         "quat": [math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]}
        r = self.ann.data.get("robot", {})
        start = (task or {}).get("robot_start") or [*r.get("xy", [0, 0]), r.get("yaw_deg") or 0.0]
        self._base = tuple(float(v) for v in start)

    def state(self):
        return self._state

    def obj_pose(self, name):
        o = self._state["objects"][name]
        return np.asarray(o["pos"], float), np.asarray(o["quat"], float)

    def joint(self, name):
        return self._state["joints"][name]

    def base_pose(self):
        return self._base

    def q(self):
        return self.kin.rest.copy()

    def left_q(self):
        return self.left_kin.rest.copy()


# ----------------------------------------------------------------- symbolic state
def _resolve(v, binding, attrs):
    if isinstance(v, str) and v.startswith("$"):
        return binding.get(v[1:])
    if isinstance(v, str) and v.startswith("@"):
        noun, fld = v[1:].split(".", 1)
        return attrs.get(noun, {}).get(fld)
    return v


def _key(v):
    if isinstance(v, list):
        return tuple(_key(x) for x in v)
    if isinstance(v, dict):
        return tuple(sorted((k, _key(x)) for k, x in v.items()))
    if isinstance(v, float):
        return round(v, 3)
    return v


def ground_atom(atom, binding, attrs, pred_args):
    vals = []
    for name in pred_args[atom["pred"]]:
        v = _resolve(atom["args"][name], binding, attrs)
        if v is None:
            return None
        vals.append(_key(v))
    return (atom["pred"], *vals)


class Domain:
    def __init__(self, rig, skills, relevant, atomic_only=True):
        from zeno_skills.predicates import REGISTRY
        from zeno_skills.skill_runtime import entity_attrs, object_attrs, support_attrs, robot_attrs
        self.rig = rig
        self.R = REGISTRY
        self.pred_args = {n: p.arg_names for n, p in REGISTRY.items()}
        self.skills = [s for s in skills.values() if not (atomic_only and s["group"] == "multi_object")]
        self.contracts = {c["skill_id"]: c for c in
                          json.loads((ROOT / "contract_library/skill_contracts.json").read_text())["contracts"]}
        self.relevant = relevant
        st = rig.state()
        self.static = {}
        for name in relevant["entities"]:
            try:
                self.static[name] = entity_attrs(rig, name, st)
            except Exception:
                pass
        self.robot0 = robot_attrs(rig)
        self.group = {}
        for name in relevant["entities"]:
            self.group[name] = self._group(name)

    def _group(self, name):
        from zeno_skills.predicates import entity_kind
        kind, rec = entity_kind(self.rig.ann, name)
        if kind == "support":
            f = rec.get("furniture")
            return name if not f or f == "SupportRepair" else f
        if kind == "furniture":
            return name
        if kind == "button":
            return rec["appliance"]
        if kind == "object":
            return None              # follows the object's support (dynamic)
        return name

    # ---------------------------------------------------------- derived facts
    def object_group(self, s, name, seen=()):
        for a in s:
            if a[0] == "on" and a[1] == name and a[2]:
                return self.group.get(a[2]) or self._group(a[2])
            if a[0] == "inside" and a[1] == name and a[2] not in seen:
                return self.object_group(s, a[2], seen + (name,))
            if a[0] == "holding" and a[2] == name and ("steadied", name) not in s:
                return "robot"
        g = self.static.get(name, {}).get("appliance")
        return g or ("floor:" + name)

    def holds(self, s, atom):
        """Closed-world truth with derived predicates."""
        p = atom[0]
        if p == "base_near":
            near = next((a[1] for a in s if a[0] == "_at"), None)
            tgt = atom[1]
            gt = self.object_group(s, tgt) if self._kind(tgt) == "object" else (self.group.get(tgt) or self._group(tgt))
            return near is not None and (near == gt or gt == "robot")
        if p == "uncovered":
            return not any(a[0] == "covered" and a[1] == atom[1] for a in s)
        if p == "container_empty":
            return not any(a[0] == "inside" and a[2] == atom[1] for a in s)
        if p == "support_clear":
            return not any(a[0] == "on" and a[2] == atom[1] for a in s)
        if p == "top_clear":
            return not any(a[0] == "on_top_of" and a[2] == atom[1] for a in s)
        if p == "at_initial_place":
            s0 = self.rig.memory["initial_support"].get(atom[1])
            return ("on", atom[1], s0) in s
        if p == "all_inside":
            return all(("inside", o, atom[2]) in s for o in atom[1])
        if p == "in_cookware_on_burner":
            return any(a[0] == "inside" and a[1] == atom[1] and ("on_burner", a[2], atom[2]) in s for a in s)
        if p == "in_appliance":
            return atom in s or any(a[0] == "on" and a[1] == atom[1] and a[2].startswith(atom[2] + "/inside")
                                    for a in s)
        if p == "temperature_at_least":
            return any(a[0] == p and a[1] == atom[1] and a[2] >= atom[2] for a in s)
        if p == "temperature_at_most":
            return any(a[0] == p and a[1] == atom[1] and a[2] <= atom[2] for a in s)
        if p == "sorted_by_category":
            rule = dict(atom[2])
            return all(any(("inside", o, rule[t]) in s or ("on", o, rule[t]) in s
                           for t in self.static.get(o, {}).get("tags", []) if t in rule)
                       for o in atom[1])
        return atom in s

    def _kind(self, name):
        from zeno_skills.predicates import entity_kind
        try:
            return entity_kind(self.rig.ann, name)[0]
        except KeyError:
            return None

    # ---------------------------------------------------------- noun attributes in a symbolic state
    def attrs(self, s, skill, binding):
        key = (id(s), skill["skill_id"], tuple(sorted((k, _key(v)) for k, v in binding.items())))
        cache = getattr(self, "_attr_cache", None)
        if cache is None or cache[0] is not s:
            self._attr_cache = cache = (s, {})
        hit = cache[1].get(key)
        if hit is None:
            hit = cache[1][key] = self._attrs(s, skill, binding)
        return hit

    def _attrs(self, s, skill, binding):
        out = {"robot": dict(self.robot0), "args": dict(binding)}
        right = next((a for a in s if a[0] == "holding" and a[1] == "right"), None)
        left = next((a for a in s if a[0] == "holding" and a[1] == "left"), None)
        out["robot"].update(right_held=right is not None, left_held=left is not None,
                            right_object=right[2] if right else None, left_object=left[2] if left else None,
                            right_kind=next((a[2] for a in s if a[0] == "_kind" and right and a[1] == right[2]), None),
                            both_hold_same=bool(right and left and right[2] == left[2]),
                            right_arm_stowed=("arm_stowed", "right") in s)
        for slot, meta in skill["inputs"].items():
            v = binding.get(slot)
            if not isinstance(v, str) or v not in self.static:
                continue
            a = dict(self.static[v])
            if a.get("kind") == "object":
                sup = next((x[2] for x in s if x[0] == "on" and x[1] == v), None)
                inside = next((x[2] for x in s if x[0] == "inside" and x[1] == v), None)
                held = any(x[0] == "holding" and x[1] == "right" and x[2] == v for x in s) and ("steadied", v) not in s
                in_mw = any(x[0] == "in_appliance" and x[1] == v and x[2] == "kitchen_microwave" for x in s) or \
                    (sup or "").startswith("kitchen_microwave/inside")
                sup_rec = next((x for x in self.rig.ann.supports if x["name"] == sup), None) if sup else None
                arts = {x["name"]: x for x in self.rig.ann.articulated}
                in_art = sup_rec is not None and sup_rec.get("furniture") in arts and \
                    sup_rec.get("category") == "cabinet_inside" and not in_mw
                art_loc = ("refrigerator" if arts[sup_rec["furniture"]].get("category") == "refrigerator"
                           else "cabinet") if in_art else None
                a.update(support=sup, on_floor=("on_floor", v) in s,
                         location="held" if held else "microwave_cavity" if in_mw else "container" if inside else
                         art_loc if art_loc else "support" if sup else "floor" if ("on_floor", v) in s
                         else a.get("location"),
                         edge_ready=("edge_overhang", v) in s, lying=("lying", v) in s,
                         lid=next((x[2] for x in s if x[0] == "covered" and x[1] == v), None),
                         contents=[x[1] for x in s if x[0] == "inside" and x[2] == v],
                         appliance="kitchen_microwave" if in_mw else sup_rec["furniture"] if in_art else a.get("appliance"))
                if isinstance(binding.get("rule"), dict):
                    a["sort_target"] = next((binding["rule"][t] for t in a.get("tags", []) if t in binding["rule"]), None)
            elif a.get("kind") == "support":
                a["objects"] = [x[1] for x in s if x[0] == "on" and x[2] == v]
            elif a.get("kind") == "articulated":
                a["is_open"] = ("is_open", v) in s
            out[slot] = a
        return out

    # ---------------------------------------------------------- actions
    def candidates(self, skill):
        doms = []
        for slot, meta in skill["inputs"].items():
            t = meta["type"]
            if not meta["required"] and slot not in ("hand",):
                base = [None] if "default" not in meta else [meta["default"]]
                if t.endswith("_ref") and t in self.relevant["domains"]:
                    base = base + list(self.relevant["domains"][t])
                doms.append(base)
                continue
            doms.append(self.relevant["domains"].get(t, [meta.get("default")]) if t not in ("hand",) else
                        ["right"] if skill["verb"] != "release" else ["right", "left"])
        for combo in itertools.product(*doms):
            yield dict(zip(skill["inputs"], combo))

    def applicable(self, s, skill, binding):
        c = self.contracts[skill["skill_id"]]
        attrs = self.attrs(s, skill, binding)
        from zeno_skills.skill_runtime import condition_holds
        for a in c["requires"]:
            g = ground_atom(a, binding, attrs, self.pred_args)
            if g is None or self.holds(s, g) == bool(a.get("negated")):
                return None
        path = next((p for p in c["policy_plan"]["paths"] if all(condition_holds(w, attrs) for w in p["when"])), None)
        if path is None:
            return None
        for a in path.get("requires", []):
            g = ground_atom(a, binding, attrs, self.pred_args)
            if g is None or self.holds(s, g) == bool(a.get("negated")):
                return None
        return path, attrs

    def apply(self, s, skill, binding, path, attrs):
        c = self.contracts[skill["skill_id"]]
        s = set(s)
        for pat in c["invalidates"]:
            name, _, rest = pat.partition("(")
            args = [x.strip() for x in rest.rstrip(")").split(",") if x.strip()]
            vals = [None if x == "*" else _key(_resolve(x, binding, attrs)) for x in args]
            if name == "base_near":
                s = {a for a in s if a[0] != "_at"}
                continue
            s = {a for a in s if not (a[0] == name and all(v is None or (i + 1 < len(a) and a[i + 1] == v)
                                                            for i, v in enumerate(vals)))}
        for a in list(c["ensures"]) + list(path.get("ensures", [])):
            g = ground_atom(a, binding, attrs, self.pred_args)
            if g is None:
                continue
            if a.get("negated"):
                s.discard(g)
            elif g[0] == "base_near":
                s = {x for x in s if x[0] != "_at"}
                tgt = g[1]
                grp = self.object_group(s, tgt) if self._kind(tgt) == "object" else (self.group.get(tgt) or self._group(tgt))
                s.add(("_at", grp))
            else:
                s.add(g)
            if g[0] == "holding" and skill["verb"] == "brace":
                s.discard(("hand_empty", g[1]))
            elif g[0] == "holding":
                s.discard(("hand_empty", g[1]))
                s = {x for x in s if not (x[0] in ("on", "inside", "on_floor", "on_top_of") and x[1] == g[2])}
                kind = "edge" if path["path_id"] in ("flat_edge", "flat_overhang_ready") else "pinch"
                s.add(("_kind", g[2], kind))
            if g[0] in ("on", "inside", "on_top_of") and a.get("negated") is None:
                s = {x for x in s if not (x[0] == "holding" and x[2] == g[1])}
            if g[0] == "hand_empty":
                for x in [x for x in s if x[0] == "holding" and x[1] == g[1]]:
                    s.discard(x)
                    s.discard(("steadied", x[2]))
            if g[0] == "is_open":
                s.discard(("is_closed", g[1]))
            if g[0] == "is_closed":
                s.discard(("is_open", g[1]))
            if g[0] == "covered":
                s = {x for x in s if not (x[0] == "holding" and x[2] == g[2])}
            if g[0] == "temperature_at_least":
                s = {x for x in s if not (x[0] == "temperature_at_most" and x[1] == g[1])}
        if skill["verb"] == "uncover" and attrs.get("container", {}).get("lid"):
            lid = attrs["container"]["lid"]
            s = {x for x in s if not (x[0] == "covered" and x[1] == binding["container"])}
            if attrs["container"].get("support"):
                s.add(("on", lid, attrs["container"]["support"]))
        if skill["verb"] == "pour":
            for x in list(s):
                if x[0] == "inside" and x[2] == binding["source"]:
                    s.discard(x)
                    s.add(("inside", x[1], binding["target"]))
        return frozenset(s)


def initial_state(dom: Domain):
    rig = dom.rig
    s = set()
    st = rig.state()
    ctx = {"_state_cache": st, "before": {"objects": st["objects"], "events": 0, "contents": {}, "bottoms": {},
                                          "base_pose": rig.base_pose()}}
    ents = dom.relevant["entities"]
    objs = [e for e in ents if e in rig.ann.objects]
    sups = [e for e in ents if any(x["name"] == e for x in rig.ann.supports)]
    arts = [a["name"] for a in rig.ann.articulated if a["name"] in ents]
    R = dom.R
    for o in objs:
        for spred in sups:
            if R["on"].evaluate(rig, ctx, object=o, support=spred)[0] and \
                    rig.geo.support_under(o, st) and rig.geo.support_under(o, st)["name"] == spred:
                s.add(("on", o, spred))
        for c in objs:
            if c != o and rig.ann.asset_of(rig.ann.objects[c]).get("container") and R["inside"].evaluate(rig, ctx, object=o, container=c)[0]:
                s.add(("inside", o, c))
        for name in ("on_floor", "upright", "lying", "grasp_clearance", "edge_overhang"):
            if R[name].evaluate(rig, ctx, object=o)[0]:
                s.add((name, o))
        for c in objs:
            if "lid" in rig.ann.asset_of(rig.ann.objects[o]).get("tags", []) and rig.ann.asset_of(rig.ann.objects[c]).get("container") \
                    and R["covered"].evaluate(rig, ctx, container=c, lid=o)[0]:
                s.add(("covered", c, o))
        for app in dom.relevant["domains"].get("appliance_ref", []):
            if dom._kind(app) == "appliance" and R["on_burner"].evaluate(rig, ctx, object=o, appliance=app)[0]:
                s.add(("on_burner", o, app))
            if dom._kind(app) == "articulated" and R["in_appliance"].evaluate(rig, ctx, object=o, appliance=app)[0]:
                s.add(("in_appliance", o, app))
        for t in dom.relevant.get("thermal", {}).get(o, []):
            s.add(t)
    for a in arts:
        s.add(("is_closed", a))
    s |= {("hand_empty", "right"), ("hand_empty", "left"), ("arm_stowed", "right"), ("arm_stowed", "left"),
          ("torso_raised",), ("waist_straight",)}
    return frozenset(s)


def relevant_skills(dom: Domain, goal):
    """Backward relevance: skills whose (path) postconditions can produce a goal
    predicate, closed over their (path) preconditions."""
    want = {g[0] for g in goal}
    derived = {"in_cookware_on_burner": {"inside", "on_burner"}, "all_inside": {"inside"},
               "uncovered": {"uncovered", "covered"}, "container_empty": {"inside", "container_empty"},
               "support_clear": {"on", "support_clear"}, "at_initial_place": {"on"}, "base_near": {"base_near"},
               "in_appliance": {"on", "in_appliance"}, "top_clear": {"top_clear"},
               "sorted_by_category": {"inside", "on", "sorted_by_category"}}
    chosen = []
    changed = True
    while changed:
        changed = False
        for sk in dom.skills:
            if sk in chosen:
                continue
            c = dom.contracts[sk["skill_id"]]
            req_all = {a["pred"] for a in c["requires"] if not a.get("negated")} | \
                {a["pred"] for p in c["policy_plan"]["paths"] for a in p.get("requires", []) if not a.get("negated")}
            # achievers add a fact they did not need already (rotate keeps "holding", it does not create it)
            ens = ({a["pred"] for a in c["ensures"]} | {a["pred"] for p in c["policy_plan"]["paths"]
                                                         for a in p.get("ensures", [])}) - req_all
            if sk["verb"] == "uncover":
                ens.add("uncovered")
            if ens & set().union(*[derived.get(w, {w}) for w in want]):
                chosen.append(sk)
                req = {a["pred"] for a in c["requires"] if not a.get("negated")} | \
                    {a["pred"] for p in c["policy_plan"]["paths"] for a in p.get("requires", []) if not a.get("negated")}
                if not req <= want:
                    want |= req
                    changed = True
    return chosen


def plan(dom: Domain, s0, goal, max_expansions=60000, weight=5.0):
    """Weighted A* (f = g + w * #unsatisfied goal atoms) over the relevant skills."""
    def h(s):
        return sum(1 for g in goal if not dom.holds(s, g))
    counter = itertools.count()
    frontier = [(weight * h(s0), next(counter), s0, [])]
    seen = {s0: 0}
    actions = [(sk, b) for sk in relevant_skills(dom, goal) for b in dom.candidates(sk)]
    expansions = 0
    while frontier and expansions < max_expansions:
        f, _, s, path = heapq.heappop(frontier)
        if all(dom.holds(s, g) for g in goal):
            dom.last_state = s
            return path, expansions
        expansions += 1
        for sk, b in actions:
            r = dom.applicable(s, sk, b)
            if r is None:
                continue
            p, attrs = r
            s2 = dom.apply(s, sk, b, p, attrs)
            if s2 == s:
                continue
            g2 = len(path) + 1
            if seen.get(s2, 1e9) <= g2:
                continue
            seen[s2] = g2
            heapq.heappush(frontier, (g2 + weight * h(s2), next(counter), s2, path + [(sk, b, p["path_id"])]))
    return None, expansions


def plan_by_subgoals(dom: Domain, s0, goal, max_expansions=60000):
    """Achieve the goal atoms one at a time (in the listed order), keeping the
    ones already achieved true; fall back to one joint search if a segment fails."""
    steps, total, s = [], 0, s0
    for i in range(len(goal)):
        seg, n = plan(dom, s, goal[:i + 1], max_expansions=max_expansions)
        total += n
        if seg is None:
            joint, n2 = plan(dom, s0, goal, max_expansions=max_expansions)
            return joint, total + n2
        steps += seg
        s = dom.last_state
    return steps, total


def to_subgraph(task_id, steps):
    nodes = []
    for i, (sk, b, _) in enumerate(steps):
        args = {k: {"value": v} for k, v in b.items() if v is not None}
        nodes.append({"id": f"n{i + 1}", "skill": sk["verb"], "args": args, "depends_on": [f"n{i}"] if i else []})
    return {"schema_version": 2, "kind": "skill_subgraph", "subgoal_id": task_id, "nodes": nodes}


def relevant_from_task(rig, task):
    ents = set(task.get("entities", []))
    # whatever already sits inside or on a named object belongs to the problem
    # (emptying a mug needs its tomatoes; uncovering a pot needs its lid)
    st = rig.state()
    for name in sorted(ents):
        if name not in rig.ann.objects:
            continue
        a = rig.ann.asset_of(rig.ann.objects[name])
        if not a.get("container"):
            continue
        for o in rig.ann.objects:
            if o != name and o not in ents and (rig.geo.inside(o, name, st)[0]
                                                or "lid" in rig.ann.asset_of(rig.ann.objects[o]).get("tags", [])
                                                and _lid_rests_on(rig, name, o, st)):
                ents.add(o)
    domains = {}
    for name in sorted(ents):
        from zeno_skills.predicates import entity_kind
        kind, rec = entity_kind(rig.ann, name)
        if kind == "object":
            a = rig.ann.asset_of(rec)
            domains.setdefault("object_ref", []).append(name)
            domains.setdefault("entity_ref", []).append(name)
            domains.setdefault("place_ref", []).append(name)
            if a.get("container"):
                domains.setdefault("container_ref", []).append(name)
                domains.setdefault("receptacle_ref", []).append(name)
            if "lid" in a.get("tags", []):
                domains.setdefault("lid_ref", []).append(name)
            if {"wiping_tool", "utensil", "sponge"} & set(a.get("tags", [])):
                domains.setdefault("tool_ref", []).append(name)
        elif kind == "support":
            for t in ("support_ref", "receptacle_ref", "entity_ref", "place_ref"):
                domains.setdefault(t, []).append(name)
        elif kind == "articulated":
            for t in ("articulated_ref", "entity_ref", "place_ref"):
                domains.setdefault(t, []).append(name)
            if rec.get("category") in ("microwave", "refrigerator"):
                domains.setdefault("appliance_ref", []).append(name)
        elif kind == "appliance":
            for t in ("appliance_ref", "entity_ref", "place_ref"):
                domains.setdefault(t, []).append(name)
        elif kind == "button":
            for t in ("button_ref", "entity_ref"):
                domains.setdefault(t, []).append(name)
        elif kind == "room":
            domains.setdefault("room_ref", []).append(name)
            domains.setdefault("place_ref", []).append(name)
    for k, v in task.get("values", {}).items():
        domains[k] = v
    return {"entities": sorted(ents), "domains": domains,
            "thermal": {k: [tuple(x) for x in v] for k, v in task.get("initial_facts", {}).items()}}


def _lid_rests_on(rig, container, lid, st):
    from zeno_skills.predicates import lid_on
    return lid_on(rig, container, lid, st)[0]


def goal_atoms(task):
    out = []
    for g in task["goal"]:
        out.append(tuple(_key(x) for x in g))
    return out


def solve_task(task, skills=None, atomic_only=True):
    from skill_library.graph import load_skills
    skills = skills or load_skills()
    rig = OfflineRig(task["annotation"], json.loads((ROOT / task["task_json"]).read_text()) if task.get("task_json") else None)
    rel = relevant_from_task(rig, task)
    dom = Domain(rig, skills, rel, atomic_only=atomic_only)
    s0 = initial_state(dom)
    for fact in task.get("initial_facts_extra", []):
        s0 = s0 | {tuple(_key(x) for x in fact)}
    for fact in task.get("initial_negated", []):
        s0 = s0 - {tuple(_key(x) for x in fact)}
    steps, n = plan_by_subgoals(dom, s0, goal_atoms(task), max_expansions=task.get("max_expansions", 60000))
    return steps, n, s0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task-catalog", default=str(HERE / "tasks.json"))
    ap.add_argument("--task")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--composite", action="store_true", help="also allow multi-object skills")
    ap.add_argument("--out", default=str(HERE / "plans"))
    args = ap.parse_args()
    catalog = json.loads(Path(args.task_catalog).read_text())
    from skill_library.graph import load_skills, validate_subgraph
    skills = load_skills()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = []
    for task in catalog["tasks"]:
        if not args.all and task["id"] != args.task:
            continue
        steps, n, _ = solve_task(task, skills, atomic_only=not (args.composite or task.get("composite")))
        ok = steps is not None
        row = {"task": task["id"], "solved": ok, "expansions": n, "length": len(steps) if ok else None}
        if ok and not steps:
            row["note"] = "goal already holds in the initial state"
        if ok and steps:
            g = to_subgraph(task["id"], steps)
            validate_subgraph(g, skills)
            (out / f"{task['id']}.skill_subgraph.json").write_text(json.dumps(g, indent=1) + "\n")
            row["verbs"] = [sk["verb"] + ("/" + p if p else "") for sk, _, p in steps]
        summary.append(row)
        print(json.dumps(row), flush=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    if args.all and not args.composite:
        readme = HERE.parent / "README.md"
        text = readme.read_text()
        a, b = "<!-- plans:start -->", "<!-- plans:end -->"
        solved = [r for r in summary if r["solved"]]
        rows = [f"**任务分解**：[tasks.json](skill_library/tasks.json) 中 {len(solved)}/{len(summary)} 个任务由符号规划器"
                "（同一套 GT 谓词与导出的前后条件）分解为 SkillNode 链，子图在 [plans/](skill_library/plans/)。", "",
                "| 任务 | 步数 | SkillNode 链（动词/路径） |", "|---|---|---|"]
        for r in summary:
            chain = " → ".join(r.get("verbs") or []) if r["solved"] else "未找到"
            rows.append(f"| `{r['task']}` | {r['length'] or '-'} | {chain} |")
        i, j = text.index(a), text.index(b)
        readme.write_text(text[:i + len(a)] + "\n" + "\n".join(rows) + "\n" + text[j:])


if __name__ == "__main__":
    main()
