"""EVALUATION_SPEC.md statistics from logged episodes (offline, no simulator).

    from benchmark.metrics import episode_facts, spec_summary
    facts = episode_facts(result, task, ctx)        # one episode: calls, events, success type, attribution
    summary = spec_summary([facts, ...])            # TSR, Planning Correctness, FSR, ERSR, Robustness, Efficiency

Input is what run_episode writes (result.json; calls.jsonl has the same rows).
Older logs lack per-call ``state_before`` and ``eval`` blocks; the state before
a call is then the previous call's ``state`` (or the start positions) and the
failed sub-step is parsed from the nested error text.  Whatever cannot be
established is ``unknown`` / ``undetermined`` and shows as N/A in ratios.

GT (states, removed objects, goal atoms) is read here for grading only; none of
it goes back to a planner.

Every ratio is a dict {"num", "den", "value"}; value is None (N/A) when den == 0.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from benchmark.eval_semantics import semantics_for

TICK_HZ = 120.0
OBSERVATION = {"NOT_OBSERVED", "NOT_IN_VIEW", "NOT_FOUND"}
PRECONDITION = {"PRECONDITION_FAILED", "NO_PATH"}
EXECUTION = {"POLICY_FAILED", "SUBSKILL_FAILED", "POSTCONDITION_FAILED"}
INVALID = {"BAD_CALL", "NOUN_INVALID", "BINDING"}
PERCEPTION = {"look", "inspect", "search", "explore", "identify", "measure", "count"}   # a failure = not observed
ROBOT_STATE_ATOMS = {"hand_empty", "holding", "hand_holding"}   # in the planner's robot observation
MOVE_M = 0.01             # an object moved (state change evidence)
BASE_MOVE_M = 0.05        # the base was repositioned
_CODE = re.compile(r"^([A-Z_]{4,}): (.*)$", re.S)
_SUB = re.compile(r"^SUBSKILL_FAILED: ([a-z_]+\(.*?\)): (.*)$", re.S)


def ratio(num, den):
    return {"num": num, "den": den, "value": (num / den) if den else None}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs)) if xs else None


# ------------------------------------------------------------------ one call
def failure_class(code):
    if code is None:
        return "unknown"
    if code in OBSERVATION:
        return "observation"
    if code in PRECONDITION:
        return "precondition"
    if code in EXECUTION:
        return "execution"
    if code in INVALID or code.startswith("INPUT_"):
        return "invalid"
    return "unknown"


def failed_substep(fb):
    """(chain of nested actions, leaf code, leaf message) of a failed call.

    The error code of the top call is only a clue: SUBSKILL_FAILED of hide_object
    may really be the pick inside its fetch, or a refused precondition."""
    err = fb.get("error") or ""
    chain = [fb.get("action")]
    m = _SUB.match(err)
    while m:
        chain.append(m.group(1))
        err = m.group(2)
        m = _SUB.match(err)
    code = fb.get("error_code") if len(chain) == 1 else None
    c = _CODE.match(err)
    if c and failure_class(c.group(1)) != "unknown":
        code, err = c.group(1), c.group(2)
    elif len(chain) > 1:
        code = "POLICY_FAILED" if err else None      # a leaf without a code prefix is the controller's message
    return chain, code, err


def call_eval(res):
    """Evaluation-only record of a SkillResult (object or asdict()): the chain down to the
    deepest failed nested call, its code, message and false checks.  Logged next to the
    planner feedback in calls.jsonl, never shown to the planner."""
    d = res if isinstance(res, dict) else res.asdict()
    if d.get("success"):
        return {"failed_substep": [], "leaf_code": None, "leaf_error": None, "failed_checks": []}
    chain, node = [d.get("action")], d
    while True:
        bad = [ch for ch in (node.get("children") or []) if isinstance(ch, dict) and not ch.get("success")]
        if not bad:
            break
        node = bad[-1]
        chain.append(node.get("action"))
    checks = [x.get("atom") for x in (node.get("preconditions") or []) + (node.get("postconditions") or [])
              if isinstance(x, dict) and not x.get("holds")]
    code, err = node.get("error_code"), node.get("error")
    if len(chain) == 1 and err:
        chain, code2, err2 = failed_substep({"action": d.get("action"), "error": err, "error_code": code})
        code, err = code2 or code, err2
    return {"failed_substep": chain, "leaf_code": code, "leaf_error": err, "failed_checks": checks}


def key_of(skill, args):
    """A call's identity for "the same operation again" (placement hints left out)."""
    return (skill, tuple(sorted((k, str(v)) for k, v in (args or {}).items() if not k.startswith("hint"))))


def arg_values(args):
    out = set()
    for v in (args or {}).values():
        if isinstance(v, list):
            out |= {x for x in v if isinstance(x, str)}
        elif isinstance(v, str):
            out.add(v)
    return out


def state_diff(a, b):
    """Watched objects that moved / changed support, hand changes, base move (m); None if a state is missing."""
    if not a or not b:
        return None
    moved = []
    for n, s in b.items():
        if n in ("base", "held", "temp_c") or not isinstance(s, dict):
            continue
        s0 = a.get(n)
        if not isinstance(s0, dict) or "pos" not in s0 or "pos" not in s:
            continue
        d = math.dist(s0["pos"], s["pos"])
        if d > MOVE_M or (s0.get("on") is not None and s.get("on") is not None and s0.get("on") != s.get("on")):
            moved.append(n)
    held = a.get("held") != b.get("held") if "held" in a and "held" in b else False
    base = math.dist(a["base"][:2], b["base"][:2]) if a.get("base") and b.get("base") else None
    temp = sorted(k for k, v in (b.get("temp_c") or {}).items() if abs(v - (a.get("temp_c") or {}).get(k, v)) > 1.0)
    return {"moved": moved, "held": held, "base_m": base, "temp": temp}


def plan_label(fb, chain_code, failed_checks):
    """Planning Correctness of one call: valid / invalid / undetermined, with the evidence."""
    if fb.get("success"):
        return "valid", "ran with its preconditions holding"
    cls = failure_class(chain_code)
    if cls == "invalid":
        return "invalid", f"interface error {chain_code}"
    if cls == "precondition":
        robot = [a for a in failed_checks if a.split("(")[0] in ROBOT_STATE_ATOMS]
        if robot:
            return "invalid", f"{robot[0]} is false and the hand state is in the observation"
        return "undetermined", "a state precondition the observations may not have shown"
    if cls == "execution":
        pre = [a for a in failed_checks if a.split("(")[0] in ROBOT_STATE_ATOMS]
        if pre:
            return "invalid", f"{pre[0]} is false and the hand state is in the observation"
        return "valid", "arguments and preconditions held; the controller failed"
    if cls == "observation":
        return "undetermined", "refused by the observation gate (probe or missing look)"
    if fb.get("action", "").split("_")[0] in PERCEPTION:
        return "valid", "a perception call that did not find its target"
    return "undetermined", "no error code"


# ------------------------------------------------------------------ one episode
def _rows(r):
    return r.get("calls") or []


def _states(r, rows):
    """State before and after each call (logged ``state_before`` wins; else the previous call's state)."""
    init = None
    if r.get("initial_positions"):
        init = {n: {"pos": p} for n, p in r["initial_positions"].items()}
        robot = (r.get("initial_observation") or {}).get("robot") or {}
        if robot.get("base_pose"):
            init["base"] = robot["base_pose"]
        init["held"] = [robot.get("right_hand"), robot.get("left_hand")] if robot else None
        if init["held"] is None:
            del init["held"]
    before, after = [], []
    prev, src = init, "initial_positions" if init else None
    for c in rows:
        if c.get("state_before") is not None:
            before.append((c["state_before"], "logged"))
        else:
            before.append((prev, src))
        after.append(c.get("state"))
        prev, src = c.get("state") or prev, "previous_call_state" if c.get("state") else src
    return before, after


def _goal_objects(task):
    names = []
    goal = task.get("goal", {})
    atoms = goal.get("all", []) + [a for g in goal.get("any", [])[:1] for a in g]
    for a in atoms:
        if a[0] in ("hand_empty", "not heating", "is_closed", "observed", "wiped", "grouped", "covered", "stirred"):
            continue
        if len(a) > 1 and isinstance(a[1], str) and a[1] not in names:
            names.append(a[1])
    return names


def room_of(rooms, xy):
    x, y = float(xy[0]), float(xy[1])
    for name, r in (rooms or {}).items():
        a = r.get("aabb_xy")
        if a and not (a[0] <= x <= a[2] and a[1] <= y <= a[3]):
            continue
        for (x1, y1), (x2, y2), (x3, y3) in r.get("triangles", []):
            d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(d) < 1e-12:
                continue
            l1 = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d
            l2 = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d
            if l1 >= -1e-6 and l2 >= -1e-6 and 1 - l1 - l2 >= -1e-6:
                return name
    return None


def _option_holds(opt, r, rows):
    goal = r.get("goal") or {}
    groups = goal.get("any") or []
    for i in opt.get("groups", []):
        if i < len(groups) and groups[i] and all(x["holds"] for x in groups[i]):
            return True
    for verb, val in opt.get("calls", []):
        if any(c["skill"] == verb and c["feedback"].get("success") and val in arg_values(c.get("args"))
               for c in rows):
            return True
    return False


def _commit_indices(opt, rows):
    """Successful calls that commit to this option (pick the substitute, place into it, heat on it ...)."""
    out = []
    for i, c in enumerate(rows):
        if c["feedback"].get("success") and any(c["skill"] == verb and val in arg_values(c.get("args"))
                                                for verb, val in opt.get("commit", []) + opt.get("calls", [])):
            out.append(i)
    return out


def substitution(r, task, objects, extra_semantics=None):
    """Which option the episode used, whether that was legal, and whether the variant needs a substitute."""
    sem = semantics_for(r["task_id"], extra_semantics)
    rows = _rows(r)
    var = (task.get("variants") or {}).get(r.get("variant"), {})
    conds = var.get("conditions") or []
    out = {"declared": sem is not None, "kind": sem["kind"] if sem else None, "used": [], "legal": True,
           "illegal_reason": None, "required": False, "substitutes": [], "selected": None, "selected_at": None,
           "commit_indices": [],
           "used_substitution": False}
    if sem is None:
        return out
    removed = set(r.get("_removed") or [])
    present = (lambda n: n in objects and n not in removed) if objects else (lambda n: n not in removed)
    out["used"] = [name for name, opt in sem["options"].items() if _option_holds(opt, r, rows)]
    if sem["kind"] == "prefer":
        for name in out["used"]:
            need = sem["options"][name].get("allowed_if_absent") or []
            if any(present(n) for n in need):
                out["legal"] = False
                out["illegal_reason"] = f"{name} used although {', '.join(n for n in need if present(n))} " \
                                        "is in the episode"
        if out["used"] and sem.get("preferred") in out["used"]:
            out["legal"], out["illegal_reason"] = True, None      # the preferred branch also holds
    subs = sorted({o for c in conds for o in sem.get("substitute", {}).get(c, [])})
    out["required"] = bool(subs)
    out["substitutes"] = subs
    if subs:
        idx = sorted({i for o in subs for i in _commit_indices(sem["options"][o], rows)})
        out["selected"] = bool(idx)
        out["selected_at"] = idx[0] if idx else None
        out["commit_indices"] = idx
        out["used_substitution"] = any(o in out["used"] for o in subs)
    elif sem["kind"] == "prefer":
        out["used_substitution"] = bool(out["used"]) and sem.get("preferred") not in out["used"]
    return out


def call_records(r, task):
    """Per call: skill, args, result, actual failed sub-step, state before / after, planning label."""
    rows = _rows(r)
    before, after = _states(r, rows)
    recs = []
    for i, c in enumerate(rows):
        fb = c.get("feedback") or {}
        ev = c.get("eval") or {}
        if fb.get("success"):
            chain, code, leaf = [fb.get("action")], None, None
        elif ev.get("failed_substep"):
            chain, code, leaf = ev["failed_substep"], ev.get("leaf_code"), ev.get("leaf_error")
            code = code or fb.get("error_code")
        else:
            chain, code, leaf = failed_substep(fb)
        failed_checks = [x["atom"] for x in fb.get("checks", []) if not x.get("holds")]
        failed_checks += [x for x in ev.get("failed_checks") or [] if x not in failed_checks]
        label, why = plan_label(fb, code or fb.get("error_code"), failed_checks)
        recs.append({"index": i, "skill": c.get("skill"), "args": c.get("args", {}), "success": bool(fb.get("success")),
                     "error_code": fb.get("error_code"),
                     "class": None if fb.get("success") else "observation" if c.get("skill") in PERCEPTION
                     else failure_class(code),
                     "failed_substep": chain[1:] if len(chain) > 1 else [], "leaf_code": code, "leaf_error": leaf,
                     "failed_checks": failed_checks, "expected_failure": c.get("expect") == "fail",
                     "role": c.get("role", ""), "state_before": before[i][0], "state_before_source": before[i][1],
                     "state_after": after[i], "tick": c.get("tick"), "planner_s": c.get("planner_s"),
                     "plan": label, "plan_reason": why, "now_visible": fb.get("now_visible") or []})
    return recs


def recovery_events(recs, sub):
    """One event per failed call (EVALUATION_SPEC 2.4): local recovery, its evidence, or why not."""
    events = []
    for i, c in enumerate(recs):
        if c["success"] or c["class"] in ("invalid", "unknown"):
            continue
        k = key_of(c["skill"], c["args"])
        j = next((j for j in range(i + 1, len(recs)) if key_of(recs[j]["skill"], recs[j]["args"]) == k
                  and recs[j]["success"]), None)
        ev = {"index": i, "action": f"{c['skill']}({', '.join(f'{a}={v}' for a, v in c['args'].items())})",
              "class": c["class"], "error_code": c["error_code"], "leaf_code": c["leaf_code"],
              "failed_substep": c["failed_substep"], "failed_checks": c["failed_checks"],
              "expected_failure": c["expected_failure"], "recovered_at": j, "helpers": [], "evidence": [],
              "outcome": None}
        if j is None:
            if any(x > i for x in sub.get("commit_indices", [])):
                ev["outcome"] = "resolved_by_alternative"
            else:
                ev["outcome"] = "not_recovered"
            events.append(ev)
            continue
        helpers = [h for h in recs[i + 1:j] if h["success"] and key_of(h["skill"], h["args"]) != k]
        ev["helpers"] = [h["skill"] for h in helpers]
        if not helpers:
            ev["outcome"] = "retry_only"
            events.append(ev)
            continue
        names = arg_values(c["args"])
        if c["class"] == "observation":
            seen = [n for h in helpers for n in h["now_visible"] if n in names]
            if seen:
                ev["evidence"].append(f"{seen[0]} became visible after {helpers[-1]['skill']}")
        flipped = [a for a in c["failed_checks"]
                   if any(x["atom"] == a and x["holds"] for x in recs[j].get("_checks", []))]
        ev["evidence"] += [f"{a} false -> true" for a in flipped]
        d = state_diff(c["state_after"], recs[j]["state_before"])
        if d is not None:
            if d["moved"]:
                ev["evidence"].append("moved: " + ", ".join(d["moved"]))
            if d["held"]:
                ev["evidence"].append("hand state changed")
            if d["base_m"] is not None and d["base_m"] > BASE_MOVE_M:
                ev["evidence"].append(f"base repositioned {d['base_m']:.2f} m")
            if d["temp"]:
                ev["evidence"].append("temperature changed: " + ", ".join(d["temp"]))
        ev["outcome"] = "local_recovery" if ev["evidence"] else "mechanism_unverified"
        events.append(ev)
    return events


def episode_facts(r, task, ctx=None):
    """Everything the spec reports about one episode.  ``ctx``: {"objects": names in the episode,
    "rooms": annotation rooms, "feasible": set of (task, variant) with a passing scripted route,
    "alt_feasible": set of (task, variant) with a passing alternative route, "ref_len": int or None,
    "semantics": optional overrides}."""
    ctx = ctx or {}
    rows = _rows(r)
    recs = call_records(r, task)
    for rec, c in zip(recs, rows):
        rec["_checks"] = (c.get("feedback") or {}).get("checks", [])
    incomplete = bool(r.get("incomplete") or r.get("crash"))
    stopped = r.get("planner") == "scripted" and r.get("stopped_at") is not None
    physical = bool(r.get("task_success")) and not incomplete and not stopped
    sub = substitution(r, task, ctx.get("objects") or set(), ctx.get("semantics"))
    events = recovery_events(recs, sub)
    success = physical and sub["legal"]
    var = (task.get("variants") or {}).get(r.get("variant"), {})
    conds = var.get("conditions") or []
    decisions = set(var.get("decisions") or [])
    tv = (r["task_id"], r.get("variant"))
    f = {"task": r["task_id"], "variant": r.get("variant"), "seed": r.get("seed"), "planner": r.get("planner"),
         "route": r.get("route"), "dir": r.get("_dir"), "incomplete": incomplete,
         "physical_success": physical, "task_success": success, "substitution": sub,
         "conditions": conds, "decisions": sorted(decisions), "feasible": tv in (ctx.get("feasible") or set()),
         "alt_feasible": tv in (ctx.get("alt_feasible") or set()),
         "log_version": r.get("eval_log_version", 1)}
    # ---- facts kept apart (spec 3)
    cls = Counter(e["class"] for e in events)
    f["failures"] = dict(cls)
    f["had_failure"] = bool(events)
    f["local_recovery"] = sum(e["outcome"] == "local_recovery" for e in events)
    f["used_substitution"] = sub["used_substitution"]
    f["events"] = events
    # ---- success type
    mech = sorted({e["class"] for e in events if e["outcome"] == "local_recovery"})
    loose = [e for e in events if e["outcome"] in ("retry_only", "mechanism_unverified")]
    open_ = [e for e in events if e["outcome"] == "not_recovered"]
    if not success:
        f["success_type"] = None
    elif not events and not sub["used_substitution"]:
        f["success_type"] = "direct"
    elif len(mech) >= 2 or (mech and sub["used_substitution"]):
        f["success_type"] = "combined"
    elif mech and not loose and not open_:
        f["success_type"] = "fallback"
    elif sub["used_substitution"] and not mech and not loose and not open_:
        f["success_type"] = "alternative"
    elif loose and not open_ and not mech:
        f["success_type"] = "recovered_unverified"          # retry_only / mechanism_unverified: not a verified fallback
    elif mech and (loose or open_):
        f["success_type"] = "fallback"
    else:
        f["success_type"] = "undetermined"
    f["fallback_subtypes"] = mech
    # ---- planning correctness
    pl = Counter(c["plan"] for c in recs)
    f["plan"] = {"valid": pl["valid"], "invalid": pl["invalid"], "undetermined": pl["undetermined"]}
    # ---- efficiency
    recovery_calls = set()
    for e in events:
        end = e["recovered_at"] if e["recovered_at"] is not None else (
            min(x for x in sub["commit_indices"] if x > e["index"]) if e["outcome"] == "resolved_by_alternative"
            else None)
        if end is not None:
            recovery_calls.update(range(e["index"], end))
        else:
            recovery_calls.add(e["index"])
    repeats, repeats_unverified = 0, 0
    for i in range(1, len(recs)):
        p, c = recs[i - 1], recs[i]
        if p["success"] or key_of(p["skill"], p["args"]) != key_of(c["skill"], c["args"]):
            continue
        d = state_diff(p["state_after"], c["state_before"]) if c["state_before_source"] == "logged" else \
            ({"moved": [], "held": False, "base_m": 0.0, "temp": []} if p["state_after"] is not None else None)
        if d is None:
            repeats_unverified += 1
        elif not (d["moved"] or d["held"] or d["temp"] or (d["base_m"] or 0) > BASE_MOVE_M):
            repeats += 1                         # the same call again with nothing changed in between
    poses = [c["state_before"]["base"] for c in recs[:1] if c["state_before"] and c["state_before"].get("base")]
    poses += [c["state_after"]["base"] for c in recs if c["state_after"] and c["state_after"].get("base")]
    nav = sum(math.dist(a[:2], b[:2]) for a, b in zip(poses, poses[1:])) if len(poses) >= 2 else None
    rooms = [room_of(ctx.get("rooms"), p[:2]) for p in poses] if ctx.get("rooms") else []
    rooms = [x for x in rooms if x]
    trans = sum(a != b for a, b in zip(rooms, rooms[1:])) if rooms else None
    ticks = r.get("sim_ticks") or max((c.get("tick") or 0 for c in rows), default=0)
    ps = [c["planner_s"] for c in recs if c["planner_s"] is not None]
    f["efficiency"] = {"calls": len(recs), "recovery_calls": len(recovery_calls), "invalid_repeats": repeats,
                       "repeats_unverified": repeats_unverified, "nav_m_lower_bound": nav,
                       "room_transitions": trans, "rooms_visited": len(set(rooms)) if rooms else None,
                       "sim_s": ticks / TICK_HZ if ticks else None, "wall_s": r.get("wall_s"),
                       "planner_s": sum(ps) if ps else None}
    # ---- robustness grouping (predefined complexity + actual room transitions)
    nobj = len(_goal_objects(task))
    L = ctx.get("ref_len")
    f["groups"] = {"challenges": "normal" if not conds else "single" if len(conds) == 1 else "combined",
                   "objects": str(nobj) if nobj < 3 else "3+",
                   "length": None if L is None else "short (<=8)" if L <= 8 else "medium (9-15)" if L <= 15
                   else "long (>15)",
                   "rooms": None if trans is None else "0 transitions" if trans == 0 else
                   "1-2 transitions" if trans <= 2 else "3+ transitions"}
    # ---- failure attribution
    f["attribution"], f["attribution_detail"] = attribute(f, r, task, recs, events, sub, ctx)
    for rec in recs:
        rec.pop("_checks", None)
    f["calls"] = [{k: rec[k] for k in ("index", "skill", "args", "success", "error_code", "class", "failed_substep",
                                       "leaf_code", "leaf_error", "failed_checks", "expected_failure", "role", "plan",
                                       "plan_reason", "state_before_source")} for rec in recs]
    return f


def attribute(f, r, task, recs, events, sub, ctx):
    """Primary cause of a failed episode (spec 4); the per-event direct causes stay in ``events``."""
    if f["task_success"]:
        return None, None
    if f["incomplete"]:
        return "system_error", r.get("crash") or "incomplete"
    for e in events:
        c = recs[e["index"]]
        e["cause"] = ("observation" if e["class"] == "observation" else
                      "planning" if c["plan"] == "invalid" else
                      "low_level_execution" if e["class"] == "execution" else "undetermined")
    if f["physical_success"] and not sub["legal"]:
        return "substitution_failure", sub["illegal_reason"]
    detail = None
    cause = None
    open_ = [e for e in events if e["outcome"] == "not_recovered" and e["class"] != "observation"]
    invalid = [c for c in recs if c["plan"] == "invalid"]
    if open_:
        e = open_[-1]
        c = recs[e["index"]]
        later = recs[e["index"] + 1:]
        same = [x for x in later if key_of(x["skill"], x["args"]) == key_of(c["skill"], c["args"])]
        tried_aux = any(x["success"] for x in later)
        deciding = f["planner"] not in ("scripted", "oracle")      # replayed routes make no decisions
        # a feasible recovery exists for this very failure: a passing fallback route of this condition
        # fails the same call on purpose
        fallback_declared = deciding and any(
            rt.get("kind") == "fallback" and (f["task"], f["variant"], name) in (ctx.get("feasible_routes") or set())
            and any(st.get("expect") == "fail" and key_of(st["skill"], st.get("args")) == key_of(c["skill"], c["args"])
                    for st in rt.get("steps", []))
            for name, rt in (task.get("routes") or {}).items())
        if c["plan"] == "invalid":
            cause, detail = "planning_failure", f"{e['action']}: {c['plan_reason']}"
        elif deciding and sub["required"] and not sub["selected"] and ctx.get("alt_feasible") and \
                (f["task"], f["variant"]) in ctx["alt_feasible"]:
            cause, detail = "substitution_failure", f"{e['action']} failed; the legal substitute " \
                                                    f"{'/'.join(sub['substitutes'])} was not used"
        elif deciding and e["class"] == "execution" and same and not tried_aux:
            cause, detail = "recovery_failure", f"{e['action']} repeated without a state change"
        elif e["class"] == "execution" and fallback_declared and not later:
            cause, detail = "recovery_failure", f"{e['action']} failed and the episode ended without a recovery " \
                                                "attempt (a fallback is declared for this condition)"
        elif e["class"] == "execution":
            cause, detail = "low_level_execution_failure", f"{e['action']}: {c['leaf_error'] or e['error_code']}"
        elif e["class"] == "precondition" and fallback_declared and not tried_aux:
            cause, detail = "recovery_failure", f"{e['action']} refused ({', '.join(c['failed_checks'])}) and " \
                                                "not resolved"
        else:
            cause, detail = "undetermined", f"{e['action']} {e['error_code']}"
    elif invalid:
        cause, detail = "planning_failure", f"{invalid[-1]['skill']}: {invalid[-1]['plan_reason']}"
    if cause is None:
        cache = set(r.get("observation_cache") or {})
        objects = ctx.get("objects") or set()
        removed = set(r.get("_removed") or [])
        unseen = [n for n in _goal_objects(task) if (not objects or n in objects) and n not in removed
                  and cache and n not in cache]
        if unseen:
            cause, detail = "exploration_failure", f"{unseen[0]} was never observed"
        elif sub["required"] and not sub["selected"] and f["planner"] not in ("scripted", "oracle"):
            cause, detail = "substitution_failure", f"the legal substitute {'/'.join(sub['substitutes'])} was not used"
        elif r.get("dropped"):
            cause, detail = "undetermined", f"{', '.join(r['dropped'])} ended on the floor"
        elif r.get("stop_reason") == "budget":
            cause, detail = "undetermined", "call budget reached"
        else:
            false = [g["atom"] for g in (r.get("goal") or {}).get("all", []) if not g["holds"]]
            cause, detail = "undetermined", "goal atoms false: " + ", ".join(false[:3]) if false else "goal false"
    if not f["feasible"] and cause in ("low_level_execution_failure", "undetermined"):
        return "feasibility_unverified", f"no passing scripted route for this condition in the evaluated runs; " \
                                         f"direct cause: {cause} ({detail})"
    return cause, detail


# ------------------------------------------------------------------ aggregation
def spec_summary(facts, planned=None):
    """The six metrics over a set of episodes (usually one planner)."""
    started = len(facts)
    sys_err = [x for x in facts if x["attribution"] == "system_error"]
    valid = [x for x in facts if x["attribution"] != "system_error"]
    ok = [x for x in valid if x["task_success"]]
    by_task, by_cond = defaultdict(list), defaultdict(list)
    for x in valid:
        by_task[x["task"]].append(x["task_success"])
        by_cond[(x["task"], x["variant"])].append(x["task_success"])
    out = {"counts": {"planned": planned, "started": started, "valid": len(valid), "system_error": len(sys_err)}}
    out["TSR"] = {"overall": ratio(len(ok), len(valid)),
                  "physical_only": ratio(sum(x["physical_success"] for x in valid), len(valid)),
                  "task_equal": {"value": mean([mean(v) for v in by_task.values()]), "n_tasks": len(by_task)},
                  "condition_equal": {"value": mean([mean(v) for v in by_cond.values()]), "n_conditions": len(by_cond)},
                  "illegal_substitution": sum(x["physical_success"] and not x["substitution"]["legal"] for x in valid)}
    v = sum(x["plan"]["valid"] for x in valid)
    iv = sum(x["plan"]["invalid"] for x in valid)
    und = sum(x["plan"]["undetermined"] for x in valid)
    out["planning"] = {"correctness": ratio(v, v + iv), "valid": v, "invalid": iv, "undetermined": und,
                       "coverage": ratio(v + iv, v + iv + und)}
    need = [x for x in valid if x["substitution"]["required"]]
    verified = [x for x in need if x.get("alt_feasible")]
    out["FSR"] = {"rate": ratio(sum(x["task_success"] and x["substitution"]["used_substitution"] for x in verified),
                                len(verified)),
                  "selection": ratio(sum(bool(x["substitution"]["selected"]) for x in verified), len(verified)),
                  "selected_but_failed": sum(bool(x["substitution"]["selected"]) and not x["task_success"]
                                             for x in verified),
                  "proactive": sum(bool(x["substitution"]["selected"]) and not any(
                      e["index"] < x["substitution"]["selected_at"] and e["class"] != "observation"
                      for e in x["events"]) for x in verified),
                  "excluded_no_verified_alternative": len(need) - len(verified)}
    rec = {}
    for cl in ("execution", "precondition", "observation"):
        hit = [x for x in valid if x["failures"].get(cl)]
        evs = [e for x in valid for e in x["events"] if e["class"] == cl]
        oc = Counter(e["outcome"] for e in evs)
        rec[cl] = {"episodes_with_failure": ratio(len(hit), len(valid)),
                   "task_success_after_failure": ratio(sum(x["task_success"] for x in hit), len(hit)),
                   "events": len(evs),
                   "local_recovery": ratio(oc["local_recovery"], len(evs)),
                   "retry_only": oc["retry_only"], "mechanism_unverified": oc["mechanism_unverified"],
                   "resolved_by_alternative": oc["resolved_by_alternative"], "not_recovered": oc["not_recovered"],
                   "local_recovery_but_task_failed": sum(
                       1 for x in hit if not x["task_success"] and any(
                           e["class"] == cl and e["outcome"] == "local_recovery" for e in x["events"]))}
    out["ERSR"] = rec["execution"]["task_success_after_failure"]
    out["recovery"] = rec
    fault = [x for x in valid if "fallback" in x["decisions"]]
    out["recovery_fault_conditions_TSR"] = ratio(sum(x["task_success"] for x in fault), len(fault))
    rob = {}
    for g in ("challenges", "objects", "length", "rooms"):
        cell = defaultdict(list)
        for x in valid:
            cell[x["groups"][g] or "unknown"].append(x["task_success"])
        rob[g] = {k: ratio(sum(vs), len(vs)) for k, vs in sorted(cell.items())}
    out["robustness"] = rob
    eff = {}
    for name, sel in (("success", ok), ("failed", [x for x in valid if not x["task_success"]])):
        eff[name] = {"n": len(sel)}
        for k in ("calls", "recovery_calls", "invalid_repeats", "nav_m_lower_bound", "room_transitions", "sim_s",
                  "wall_s", "planner_s"):
            vals = [x["efficiency"][k] for x in sel if x["efficiency"][k] is not None]
            eff[name][k] = {"mean": mean(vals), "n": len(vals)}
    out["efficiency"] = eff
    out["success_types"] = dict(Counter(x["success_type"] for x in ok))
    out["fallback_subtypes"] = dict(Counter(s for x in ok if x["success_type"] in ("fallback", "combined")
                                            for s in x["fallback_subtypes"]))
    out["attribution"] = dict(Counter(x["attribution"] for x in facts if not x["task_success"]))
    return out


# ------------------------------------------------------------------ markdown
def _r(x, pct=True):
    if x is None:
        return "N/A"
    if isinstance(x, dict) and "den" in x:
        if not x["den"]:
            return "N/A (0/0)"
        return f"{100 * x['value']:.0f}% ({x['num']}/{x['den']})" if pct else f"{x['value']:.2f} ({x['num']}/{x['den']})"
    if isinstance(x, float):
        return f"{x:.2f}"
    return str(x)


def _m(x):
    return "N/A" if x["mean"] is None else f"{x['mean']:.1f} (n={x['n']})"


def spec_markdown(summaries, scripted_note=True):
    """summaries: {planner: spec_summary}.  The tables of EVALUATION_SPEC 2-4."""
    ps = sorted(summaries)
    S = summaries
    head = "| Metric | " + " | ".join(ps) + " |"
    sep = "|---|" + "---|" * len(ps)

    def row(name, fn):
        return f"| {name} | " + " | ".join(fn(S[p]) for p in ps) + " |"
    md = ["## Evaluation-spec metrics", ""]
    if scripted_note:
        md += ["`scripted` replays declared routes (expected failures on purpose) and `oracle` uses GT: their rows "
               "are feasibility / capability evidence, not planner results (EVALUATION_SPEC 1).  Ratios show "
               "(numerator/denominator); N/A = no sample.", ""]
    md += ["### Episodes and TSR", "", head, sep,
           row("planned / started / valid / system error", lambda s: "{} / {} / {} / {}".format(
               s["counts"]["planned"] if s["counts"]["planned"] is not None else "N/A", s["counts"]["started"],
               s["counts"]["valid"], s["counts"]["system_error"])),
           row("TSR (instruction semantics)", lambda s: _r(s["TSR"]["overall"])),
           row("TSR (physical verifier only)", lambda s: _r(s["TSR"]["physical_only"])),
           row("TSR task-equal", lambda s: f"{100 * s['TSR']['task_equal']['value']:.0f}% "
               f"({s['TSR']['task_equal']['n_tasks']} tasks)" if s["TSR"]["task_equal"]["value"] is not None else "N/A"),
           row("TSR condition-equal", lambda s: f"{100 * s['TSR']['condition_equal']['value']:.0f}% "
               f"({s['TSR']['condition_equal']['n_conditions']} conditions)"
               if s["TSR"]["condition_equal"]["value"] is not None else "N/A"),
           row("illegal substitutions (physical pass, instruction violated)", lambda s: str(s["TSR"]["illegal_substitution"])),
           "", "### Planning Correctness", "", head, sep,
           row("valid / (valid + invalid)", lambda s: _r(s["planning"]["correctness"])),
           row("valid / invalid / undetermined calls", lambda s: "{} / {} / {}".format(
               s["planning"]["valid"], s["planning"]["invalid"], s["planning"]["undetermined"])),
           row("judged coverage", lambda s: _r(s["planning"]["coverage"])),
           "", "### Functional Substitution (FSR)", "", head, sep,
           row("FSR", lambda s: _r(s["FSR"]["rate"])),
           row("substitute selected", lambda s: _r(s["FSR"]["selection"])),
           row("selected, then failed end to end", lambda s: str(s["FSR"]["selected_but_failed"])),
           row("selected before any failure (proactive)", lambda s: str(s["FSR"]["proactive"])),
           row("excluded: no verified alternative route", lambda s: str(s["FSR"]["excluded_no_verified_alternative"])),
           "", "### Execution Recovery (ERSR) and other recovery", "", head, sep]
    for cl, title in (("execution", "physical execution"), ("precondition", "state precondition"),
                      ("observation", "observation")):
        md += [row(f"{title}: episodes with failure", lambda s, c=cl: _r(s["recovery"][c]["episodes_with_failure"])),
               row(f"{title}: task success after failure" + (" = **ERSR**" if cl == "execution" else ""),
                   lambda s, c=cl: _r(s["recovery"][c]["task_success_after_failure"])),
               row(f"{title}: events, local recovery (verified)",
                   lambda s, c=cl: f"{s['recovery'][c]['events']}, " + _r(s["recovery"][c]["local_recovery"])),
               row(f"{title}: retry_only / mechanism_unverified / by alternative / not recovered",
                   lambda s, c=cl: "{retry_only} / {mechanism_unverified} / {resolved_by_alternative} / "
                                   "{not_recovered}".format(**s["recovery"][c])),
               row(f"{title}: local recovery but task failed",
                   lambda s, c=cl: str(s["recovery"][c]["local_recovery_but_task_failed"]))]
    md += [row("TSR on fallback conditions", lambda s: _r(s["recovery_fault_conditions_TSR"])),
           "", "### Long-Horizon Robustness (TSR by group)", "", head, sep]
    for g, title in (("challenges", "challenges"), ("objects", "goal objects"), ("length", "reference length (calls)"),
                     ("rooms", "actual room transitions")):
        keys = sorted({k for p in ps for k in S[p]["robustness"][g]})
        md += [row(f"{title}: {k}", lambda s, g=g, k=k: _r(s["robustness"][g].get(k))) for k in keys]
    md += ["", "### Execution Efficiency (mean per episode, n = episodes with data)", "", head, sep]
    for name in ("success", "failed"):
        for k, title in (("calls", "skill calls"), ("recovery_calls", "extra recovery calls"),
                         ("invalid_repeats", "invalid repeats"), ("nav_m_lower_bound", "base travel m (lower bound)"),
                         ("room_transitions", "room transitions"), ("sim_s", "simulated s"),
                         ("wall_s", "wall-clock s"), ("planner_s", "planner response s")):
            md.append(row(f"{name} episodes: {title}", lambda s, n=name, k=k: _m(s["efficiency"][n][k])))
    md += ["", "### Success types and failure attribution", "", head, sep,
           row("success types", lambda s: ", ".join(f"{k} {v}" for k, v in sorted(s["success_types"].items(),
                                                                                    key=lambda kv: str(kv[0]))) or "-"),
           row("fallback subtypes", lambda s: ", ".join(f"{k} {v}" for k, v in sorted(s["fallback_subtypes"].items()))
               or "-"),
           row("failure attribution", lambda s: ", ".join(f"{k} {v}" for k, v in sorted(s["attribution"].items(),
                                                                                         key=lambda kv: str(kv[0])))
               or "-")]
    return md
