"""Strict static checks for the verb-based SkillNode library.

``check_library(skills)`` returns a list of error strings (empty = valid) for
the compiled skill records produced by tools/build_skill_library.py:

* verbs are unique and no two verbs fall in the same synonym group;
* every input/output type is known; every ``$slot`` / ``@noun.field`` /
  ``#step.key`` reference resolves; predicate argument names and types match the
  predicate registry; relative predicates are never preconditions;
* every path condition names a known noun field; every policy step binds to the
  policy's real ``execute`` signature; every nested Skill call supplies the
  callee's required inputs;
* relations are consistent with the pre/postconditions:
    sequence A->B     some postcondition of A matches a precondition of B
                      (same predicate, arguments consistent with ``bind``),
    fallback repair   B ensures the predicate it ``repairs`` and A requires it,
    fallback subst.   B shares a postcondition predicate with A,
    alternative       A and B share a postcondition predicate;
* every public low-level policy is used by at least one path, every skill has
  a previous or next step and at least one fallback/alternative link.
"""

from __future__ import annotations

import inspect
import re

from zeno_skills.predicates import ALL_TYPES, HANDS, REGISTRY, type_satisfies

# Verbs that mean the same physical act for this robot.  At most one member of a
# group may be a library verb.
SYNONYM_GROUPS = [
    {"pick", "grasp", "grab", "take", "acquire", "clasp", "clamp", "grip", "pinch", "seize", "retrieve",
     "scoop", "intercept", "snatch", "collect_one"},
    {"place", "put", "set", "deposit", "lay", "position", "align", "load", "insert", "deliver", "plant"},
    {"drop", "toss", "throw", "dump", "discard"},
    {"navigate", "go", "move", "travel", "drive", "walk", "transport", "convoy", "head"},
    {"approach", "near", "reach", "park"},
    {"face", "turn", "pivot", "rotate_base", "orient_base", "spin"},
    {"retreat", "withdraw", "back", "reverse"},
    {"crouch", "squat", "duck", "descend"},
    {"stand", "rise", "ascend", "elevate", "stand_up"},
    {"bend", "lean", "pitch", "stoop"},
    {"straighten", "unbend"},
    {"tuck", "fold", "stow"},
    {"reset", "home", "initialize"},
    {"look", "gaze", "glance", "watch", "view", "observe"},
    {"inspect", "examine", "check", "peek"},
    {"search", "find", "seek", "locate", "hunt"},
    {"explore", "scan", "survey", "patrol", "sweep_room"},
    {"point", "indicate", "gesture"},
    {"present", "show", "display", "offer"},
    {"release", "let_go", "unhand", "ungrip"},
    {"handover", "transfer", "pass", "hand"},
    {"lift", "raise", "hoist", "heave", "boost"},
    {"lower", "sink"},
    {"rotate", "twist", "spin_object", "orient", "reorient", "turn_object"},
    {"regrasp", "readjust", "regrip"},
    {"brace", "steady", "hold", "stabilize", "support"},
    {"flip", "invert", "overturn", "turn_over"},
    {"push", "shove", "nudge", "slide", "drag", "press_along"},
    {"pull", "draw", "tug", "haul", "yank"},
    {"expose", "cantilever", "overhang"},
    {"separate", "detach", "split", "spread"},
    {"center", "recenter", "secure"},
    {"roll", "trundle"},
    {"tip", "topple", "knock_over", "fell"},
    {"upright", "right", "erect"},
    {"wipe", "clean", "scrub", "mop", "dust", "swab"},
    {"stir", "mix", "whisk", "blend"},
    {"pour", "decant", "spill", "tip_out"},
    {"open", "unfold", "extend", "swing", "unlatch"},
    {"close", "shut", "slam", "fasten"},
    {"press", "push_button", "click", "trigger", "tap", "start"},
    {"heat", "warm", "cook", "attain", "microwave", "boil"},
    {"chill", "cool", "refrigerate", "freeze"},
    {"cover", "cap", "seal", "lid"},
    {"uncover", "uncap", "unseal", "unlid"},
    {"fetch", "bring", "carry", "deliver_to", "get"},
    {"collect", "gather", "assemble", "pack"},
    {"sort", "classify", "categorize", "group_by"},
    {"clear", "declutter", "tidy"},
    {"empty", "unload", "unpack", "evacuate"},
    {"arrange", "organize", "lay_out", "group"},
    {"restore", "return", "replace", "put_back"},
    {"swap", "exchange", "switch_places"},
    {"stack", "pile", "heap", "nest"},
    {"sidestep", "strafe", "shuffle"},
    {"wait", "pause", "idle", "linger"},
    {"identify", "recognize", "classify_one", "label"},
    {"measure", "gauge", "size_up"},
    {"count", "tally", "enumerate"},
    {"wave", "beckon", "salute"},
    {"nod", "bow"},
    {"shake", "jiggle", "rattle", "agitate"},
    {"hover", "hold_above", "poise"},
    {"square", "align_yaw", "true_up"},
    {"touch", "contact", "feel", "poke"},
    {"knock", "rap", "bang"},
    {"sweep", "gather_push", "brush"},
    {"stop", "halt", "switch_off", "turn_off"},
    {"dip", "dunk", "immerse"},
    {"hide", "conceal", "stash"},
]

# Registered policies that no SkillNode path may use, with the measured reason.
RETIRED_POLICIES = {
    "policy_014": "Floor corner pinch: with parallel jaws the closing axis across a 2.9 cm flat object lying on "
                  "the floor runs nearly horizontally over its top face, so the upper pad never presses the top "
                  "and the lower pad would have to sit below the floor; it held nothing in any of 11 Isaac Sim "
                  "attempts (notebook, books, toy car). Flat objects on the floor have no pick path.",
}

NOUN_FIELDS = {
    "object": {"instance", "kind", "asset", "tags", "grasp_types", "support", "support_category", "on_floor",
               "location", "appliance", "in_container", "held_by", "held_kind", "flat", "tall", "lying", "wide_box",
               "handle_collider", "near_closed_edge", "edge_ready", "is_container", "is_lid", "lid", "contents",
               "initial_support", "xy", "bearing_abs_deg", "buffer_xy", "sort_target", "aside_support"},
    "support": {"instance", "kind", "category", "furniture", "z", "objects", "is_microwave_cavity", "appliance",
                "bearing_abs_deg", "free_xy", "burner_xy", "roomiest_xy"},
    "articulated": {"instance", "kind", "type", "category", "has_handle", "powered", "is_open", "power_button", "wide_open_q",
                    "bearing_abs_deg"},
    "appliance": {"instance", "kind", "category", "power_button", "type", "has_handle", "powered", "is_open", "wide_open_q",
                  "bearing_abs_deg"},
    "button": {"instance", "kind", "appliance", "button", "appliance_category", "bearing_abs_deg"},
    "room": {"instance", "kind", "bearing_abs_deg"},
    "robot": {"right_held", "left_held", "right_object", "left_object", "right_kind", "both_hold_same",
              "right_arm_stowed"},
}
TYPE_FIELDS = {
    "object_ref": "object", "container_ref": "object", "lid_ref": "object", "tool_ref": "object",
    "support_ref": "support", "articulated_ref": "articulated", "appliance_ref": "appliance",
    "button_ref": "button", "room_ref": "room",
}


def noun_fields(type_):
    if type_ in TYPE_FIELDS:
        return NOUN_FIELDS[TYPE_FIELDS[type_]]
    # receptacle / place / entity: union of what the bound kind can expose
    return set().union(*NOUN_FIELDS.values())


def field_type(type_, fld):
    """Type of a noun attribute when it is used as a value."""
    table = {"support": "support_ref", "initial_support": "support_ref", "lid": "lid_ref",
             "appliance": "appliance_ref", "power_button": "button_ref", "contents": "object_list",
             "objects": "object_list", "xy": "xy", "buffer_xy": "xy", "free_xy": "xy", "burner_xy": "xy", "sort_target": "receptacle_ref",
             "instance": type_, "right_object": "object_ref", "left_object": "object_ref",
             "in_container": "container_ref"}
    return table.get(fld)


def _ref_type(value, inputs, outputs_of=None, loop_vars=None):
    loop_vars = loop_vars or {}
    if isinstance(value, str) and value.startswith("$"):
        name = value[1:]
        if name in loop_vars:
            return loop_vars[name]
        if name in inputs:
            return inputs[name]["type"]
        return None
    if isinstance(value, str) and value.startswith("@"):
        noun, fld = value[1:].split(".", 1)
        if noun == "robot":
            return field_type("robot", fld) or "any"
        t = loop_vars.get(noun) or (inputs[noun]["type"] if noun in inputs else None)
        if t is None:
            return None
        return field_type(t, fld) or "any"
    return "literal"


def narrowed_inputs(inputs, when):
    """A receptacle/entity slot is narrowed by a path condition on its kind."""
    out = dict(inputs)
    for c in when:
        if c["field"] == "kind" and c["op"] == "equals" and c["noun"] in inputs:
            t = {"object": "container_ref" if inputs[c["noun"]]["type"] == "receptacle_ref" else "object_ref",
                 "support": "support_ref", "articulated": "articulated_ref"}.get(c["value"])
            if t:
                out[c["noun"]] = dict(inputs[c["noun"]], type=t)
    return out


def check_atom(atom, inputs, where, errors, allow_relative=True):
    pred = REGISTRY.get(atom["pred"])
    if pred is None:
        errors.append(f"{where}: unknown predicate {atom['pred']}")
        return
    if not allow_relative and pred.kind == "relative":
        errors.append(f"{where}: relative predicate {pred.name} cannot be a precondition")
    if set(atom["args"]) != set(pred.arg_names):
        errors.append(f"{where}: {pred.name} needs args {pred.arg_names}, got {sorted(atom['args'])}")
        return
    for (name, want) in pred.args:
        v = atom["args"][name]
        t = _ref_type(v, inputs)
        if t is None:
            errors.append(f"{where}: {pred.name}.{name}={v} does not resolve")
        elif t == "literal":
            if want == "hand" and v not in HANDS:
                errors.append(f"{where}: {pred.name}.{name}={v!r} is not a hand")
            if want in ("number", "positive_number") and not isinstance(v, (int, float)):
                errors.append(f"{where}: {pred.name}.{name}={v!r} is not a number")
            if want.endswith("_ref") and not isinstance(v, str):
                errors.append(f"{where}: {pred.name}.{name}={v!r} is not a scene name")
        elif t != "any" and not type_satisfies(t, want):
            errors.append(f"{where}: {pred.name}.{name} gets {t}, needs {want}")


def _policy_suite():
    from zeno_skills.policies import PolicySuite
    from zeno_skills.interface_ids import POLICY_PUBLIC_IDS
    return PolicySuite(None), set(POLICY_PUBLIC_IDS.values())


def check_steps(steps, skill, by_verb, where, errors, used, loop_vars=None, names=None):
    suite, pids = _policy_suite() if not hasattr(check_steps, "_cache") else check_steps._cache
    check_steps._cache = (suite, pids)
    inputs = skill["inputs"]
    loop_vars = dict(loop_vars or {})
    names = set(names or ())
    for k, step in enumerate(steps):
        w = f"{where}.step{k}"
        if "foreach" in step:
            t = _ref_type(step["foreach"], inputs, loop_vars=loop_vars)
            if t not in ("object_list", "any"):
                errors.append(f"{w}: foreach over {step['foreach']} ({t}) is not a list")
            check_steps(step["steps"], skill, by_verb, w, errors, used, dict(loop_vars, **{step["as"]: "object_ref"}),
                        names)
            continue
        refs = list(step["args"].values()) if "call" in step else list(step["args"]) + list(step["kwargs"].values())
        for v in refs:
            if isinstance(v, str) and v.startswith("#"):
                if v[1:].split(".", 1)[0] not in names:
                    errors.append(f"{w}: {v} refers to no earlier step output")
            elif isinstance(v, str) and v[:1] in "$@":
                if _ref_type(v, inputs, loop_vars=loop_vars) is None:
                    errors.append(f"{w}: {v} does not resolve")
                if v.startswith("@"):
                    noun, fld = v[1:].split(".", 1)
                    t = "robot" if noun == "robot" else loop_vars.get(noun) or inputs.get(noun, {}).get("type")
                    allowed = NOUN_FIELDS["robot"] if noun == "robot" else noun_fields(t)
                    if fld not in allowed:
                        errors.append(f"{w}: noun field {v} is not computed")
        if "call" in step:
            callee = by_verb.get(step["call"])
            if callee is None:
                errors.append(f"{w}: calls unknown skill {step['call']}")
            else:
                need = {k for k, m in callee["inputs"].items() if m["required"]}
                if not need <= set(step["args"]) or not set(step["args"]) <= set(callee["inputs"]):
                    errors.append(f"{w}: call {step['call']} args {sorted(step['args'])} vs inputs "
                                  f"{sorted(callee['inputs'])} (required {sorted(need)})")
                for k2, v in step["args"].items():
                    t = _ref_type(v, inputs, loop_vars=loop_vars)
                    want = callee["inputs"].get(k2, {}).get("type")
                    if t not in (None, "any", "literal") and want and not type_satisfies(t, want) \
                            and not (want == "receptacle_ref" and t in ("support_ref", "container_ref")):
                        errors.append(f"{w}: call {step['call']}.{k2} gets {t}, needs {want}")
                used.setdefault("calls", set()).add(step["call"])
            if step.get("as"):
                names.add(step["as"])
            continue
        pid = step["policy"]
        if pid not in pids:
            errors.append(f"{w}: unknown policy {pid}")
            continue
        used.setdefault("policies", set()).add(pid)
        try:
            inspect.signature(getattr(suite, pid).execute).bind(*step["args"], **step["kwargs"])
        except TypeError as exc:
            errors.append(f"{w}: {pid} call does not bind: {exc}")
        if step.get("as"):
            names.add(step["as"])


def _atoms(skill, kind):
    out = list(skill[kind])
    for p in skill["policy_plan"]["paths"]:
        out += p.get(kind, [])
    return out


def _arg_consistent(a_atom, b_atom, bind):
    """B's atom argument "$y" with bind {y: "$x"} must equal A's "$x"."""
    for k, vb in b_atom["args"].items():
        va = a_atom["args"].get(k)
        if isinstance(vb, str) and vb.startswith("$") and vb[1:] in bind:
            if va != bind[vb[1:]]:
                return False
        elif not (isinstance(vb, str) and vb[:1] in "$@") and not (isinstance(va, str) and va[:1] in "$@"):
            if va != vb:
                return False
    return True


def sequence_type(a, rel, b):
    """``enables`` when a postcondition of A matches a precondition of B under
    the relation's argument binding, else ``then`` (loose order)."""
    a_ens, b_req = _atoms(a, "ensures"), _atoms(b, "requires")
    ok = any(x["pred"] == y["pred"] and bool(x.get("negated")) == bool(y.get("negated"))
             and _arg_consistent(x, y, rel["bind"]) for x in a_ens for y in b_req)
    return "enables" if ok else "then"


def check_relation(a, rel, b, errors):
    w = f"{a['verb']}->{rel['kind']}->{b['verb']}"
    for k, v in rel["bind"].items():
        if k not in b["inputs"]:
            errors.append(f"{w}: bind key {k} is not an input of {b['verb']}")
        if isinstance(v, str) and v.startswith("$") and v[1:] not in a["inputs"]:
            errors.append(f"{w}: bind value {v} is not an input of {a['verb']}")
    a_ens, b_req = _atoms(a, "ensures"), _atoms(b, "requires")
    a_names = {x["pred"] for x in a_ens if not x.get("negated")}
    b_ens_names = {x["pred"] for x in _atoms(b, "ensures") if not x.get("negated")}
    a_req_names = {x["pred"] for x in _atoms(a, "requires") if not x.get("negated")}
    kind = rel["kind"]
    if kind == "sequence":
        rel["sequence_type"] = sequence_type(a, rel, b)
        if rel["sequence_type"] == "then" and not (rel["bind"] or rel.get("reason")):
            errors.append(f"{w}: loose next step needs a shared noun (bind) or a reason; no postcondition of "
                          f"{a['verb']} matches a precondition of {b['verb']}")
    elif kind == "fallback":
        ftype = rel.get("fallback_type")
        if ftype == "repair":
            rep = rel.get("repairs")
            if rep:
                if rep not in b_ens_names:
                    errors.append(f"{w}: repair fallback does not ensure {rep}")
                if rep not in a_req_names:
                    errors.append(f"{w}: {a['verb']} does not require {rep}")
            elif not (b_ens_names & a_req_names) and not b["group"] == "base_and_body":
                errors.append(f"{w}: repair fallback ensures none of {a['verb']}'s preconditions")
        elif ftype == "recover":
            if not rel.get("reason"):
                errors.append(f"{w}: recover fallback needs a reason")
        elif ftype == "substitute":
            if not (b_ens_names & a_names) and not b["group"] in ("perception_and_gesture",):
                errors.append(f"{w}: substitute fallback shares no postcondition with {a['verb']}")
        else:
            errors.append(f"{w}: fallback needs fallback_type repair|recover|substitute")
    elif kind == "alternative":
        if not (b_ens_names & a_names) and a["group"] != b["group"]:
            errors.append(f"{w}: alternative shares no postcondition and no capability group")
    else:
        errors.append(f"{w}: unknown relation kind")


def check_library(skills: list[dict]) -> list[str]:
    errors: list[str] = []
    by_verb = {}
    for s in skills:
        if s["verb"] in by_verb:
            errors.append(f"duplicate verb {s['verb']}")
        by_verb[s["verb"]] = s
        if not re.fullmatch(r"[a-z]+", s["verb"]) or not re.fullmatch(r"[a-z_]+", s["noun"]):
            errors.append(f"{s['verb']}: verb/noun must be lowercase words")
    for group in SYNONYM_GROUPS:
        hit = sorted(set(by_verb) & group)
        if len(hit) > 1:
            errors.append(f"synonym verbs in one library: {hit}")
    used: dict = {}
    for s in skills:
        w = s["verb"]
        for name, m in list(s["inputs"].items()) + list(s["outputs"].items()):
            if m["type"] not in ALL_TYPES and m["type"] not in ("pose2d",):
                errors.append(f"{w}: unknown type {m['type']} for {name}")
        for a in s["requires"]:
            check_atom(a, s["inputs"], f"{w}.requires", errors, allow_relative=False)
        for a in s["ensures"]:
            check_atom(a, s["inputs"], f"{w}.ensures", errors)
        if not s["ensures"] and not any(p.get("ensures") for p in s["policy_plan"]["paths"]):
            errors.append(f"{w}: no postcondition")
        paths = s["policy_plan"]["paths"]
        if not paths:
            errors.append(f"{w}: no policy path")
        ids = [p["path_id"] for p in paths]
        if len(ids) != len(set(ids)):
            errors.append(f"{w}: duplicate path ids")
        for p in paths:
            pw = f"{w}.{p['path_id']}"
            for c in p["when"]:
                if c["noun"] == "args":
                    if c["field"] not in s["inputs"]:
                        errors.append(f"{pw}: condition on unknown input {c['field']}")
                    continue
                if c["noun"] == "robot":
                    allowed = NOUN_FIELDS["robot"]
                elif c["noun"] in s["inputs"]:
                    allowed = noun_fields(s["inputs"][c["noun"]]["type"])
                else:
                    errors.append(f"{pw}: condition on unknown noun {c['noun']}")
                    continue
                if c["field"] not in allowed:
                    errors.append(f"{pw}: noun field {c['noun']}.{c['field']} is not computed")
            narrowed = narrowed_inputs(s["inputs"], p["when"])
            for a in p.get("requires", []):
                check_atom(a, narrowed, f"{pw}.requires", errors, allow_relative=False)
            for a in p.get("ensures", []):
                check_atom(a, narrowed, f"{pw}.ensures", errors)
            check_steps(p["steps"], dict(s, inputs=narrowed), by_verb, pw, errors, used)
        for rel in s["relations"]:
            b = by_verb.get(rel["to"])
            if b is None:
                errors.append(f"{w}: relation to unknown verb {rel['to']}")
                continue
            check_relation(s, rel, b, errors)
    # graph shape
    incoming = {v: [] for v in by_verb}
    for s in skills:
        for rel in s["relations"]:
            if rel["to"] in incoming:
                incoming[rel["to"]].append((s["verb"], rel["kind"]))
    for s in skills:
        kinds_out = {r["kind"] for r in s["relations"]}
        kinds_in = {k for _, k in incoming[s["verb"]]}
        if "sequence" not in kinds_out | kinds_in:
            errors.append(f"{s['verb']}: no previous/next step relation")
        if not ({"fallback", "alternative"} & (kinds_out | kinds_in)):
            errors.append(f"{s['verb']}: no fallback or alternative relation")
    # coverage
    _, pids = _policy_suite()
    unused = sorted(pids - used.get("policies", set()) - set(RETIRED_POLICIES))
    stale = sorted(set(RETIRED_POLICIES) & used.get("policies", set()))
    if stale:
        errors.append(f"retired policies still used by a Skill path: {stale}")
    if unused:
        errors.append(f"policies used by no Skill path: {unused}")
    preds = {a["pred"] for s in skills for a in _atoms(s, "requires") + _atoms(s, "ensures")}
    unused_preds = sorted(set(REGISTRY) - preds)
    if unused_preds:
        errors.append(f"predicates used by no Skill: {unused_preds}")
    return errors
