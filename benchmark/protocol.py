"""Quantitative evaluation protocol: the 12 metrics of the task-level replanning redesign (2026-10-26).

    from benchmark.protocol import episode_protocol, protocol_summary, protocol_markdown
    f["protocol"] = episode_protocol(r, task, recs, events, sub, ctx, f)   # called by metrics.episode_facts
    summary = protocol_summary([facts, ...])                               # one planner (and tier)

  A  TSR   task success                    SCR  subgoal completion        CSR  constraint satisfaction
  B  OISR  oracle-independent success      OPS  oracle plan similarity    PFR  planning failure rate
  C  PASR  proactive adaptation success    RRSR reactive recovery success FSA  fallback selection accuracy
     RE    recovery efficiency
  D  SESR  skill execution success         RTSR robust task success (task -> variant -> seed means)

Offline, from what run_episode logs (result.json); the same facts as metrics.py, GT for grading only.
Pre-registered rules (README, *Quantitative protocol*):

* Constraints define the legal result, never the route: Success = GoalSatisfied AND HardConstraintsSatisfied.
  Every final goal atom (for ``any`` goals, the best group) is a hard constraint of one category:
  goal (the required end state), spatial (placement / space), preservation (restored or undisturbed
  state, devices off, non-target objects upright and off the floor); semantic is the instruction
  semantics (a legal substitute) and, for registered decoys (eval_semantics.DECOYS), the failed goal
  atom of an object left at a decoy, moved from goal to semantic (one atom, one count).  Floor drops, displaced non-goal objects and, from the per-call
  states, a transient floor drop are preservation constraints too.  Environment conditions (an
  occupied microwave, a full bin) decide feasibility only and are never scored as constraints.
* SCR counts the goal-category atoms other than ``hand_empty``, equal weights.
* A failure event is recovered when the same / an equivalent result is verified later, or when the task
  succeeds in the end by any legal path.  RE compares the calls from the failure to the end of a
  successful episode with the calls after the same failure in the declared fallback route.
* A path is the sequence of successful calls, each as (skill, arguments without ``hint*``), with
  immediate repeats collapsed.  The oracle set of a variant is every declared nominal / fallback /
  alternative / explore route of it, without its expected-failure and unwind steps.
* Repeated failures of the same call with no successful call in between are one failure event.
* Event metrics (PASR, RRSR, FSA, RE) are N/A when nothing is eligible, never 0 or 100 %.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict

from benchmark.eval_adaptation import adaptation_for
from benchmark.eval_outcomes import parse_atom
from benchmark.eval_semantics import decoys_for
from benchmark.metrics import MOVE_M, PERCEPTION, _goal_objects, arg_values, key_of, mean, ratio

PROTOCOL_VERSION = 1
SPATIAL_PREDICATES = {"clear_of", "near_any", "away_from_edge", "front_visible", "count_on_at_least"}
PRESERVATION_PREDICATES = {"near_start", "is_closed", "not heating"}
OBJECT_SAFETY = {"upright", "not on_floor"}     # goal for a target object, preservation for any other
CATEGORIES = ("goal", "spatial", "semantic", "preservation")
ORACLE_KINDS = {"nominal", "fallback", "alternative", "explore"}
PLANNING_CAUSES = {"planning_failure", "substitution_failure", "recovery_failure"}
RECOVERED = {"local_recovery", "retry_only", "mechanism_unverified", "resolved_by_alternative"}
FLOOR_Z = 0.08             # as episode.floor_drops: below 8 cm after starting above 30 cm
SIDE_EFFECT_M = 0.05       # as evaluate.py: a non-goal object displaced this far
BOOTSTRAP = 1000


def rate(num, den):
    """ratio() plus a Wilson 95 % interval."""
    out = ratio(num, den)
    if den:
        z, p = 1.96, num / den
        c = (p + z * z / (2 * den)) / (1 + z * z / den)
        h = z * math.sqrt(p * (1 - p) / den + z * z / (4 * den * den)) / (1 + z * z / den)
        out["ci95"] = [max(0.0, c - h), min(1.0, c + h)]
    else:
        out["ci95"] = None
    return out


# ------------------------------------------------------------------ goal rows
def _rows(goal):
    g = goal or {}
    plain = [(parse_atom(x["atom"]), bool(x["holds"])) for x in g.get("all", [])]
    groups = [[(parse_atom(x["atom"]), bool(x["holds"])) for x in grp] for grp in g.get("any", [])]
    return plain, groups


def _core(atom):
    return bool(atom) and atom[0] not in SPATIAL_PREDICATES | PRESERVATION_PREDICATES | OBJECT_SAFETY


def _targets(rows):
    out = set()
    for a, _ in rows:
        if _core(a) and a[0] != "hand_empty" and len(a) > 1:
            out |= set(a[1]) if isinstance(a[1], list) else {a[1]}
    return out


def category(atom, targets):
    name = atom[0] if atom else None
    if name in SPATIAL_PREDICATES:
        return "spatial"
    if name in PRESERVATION_PREDICATES:
        return "preservation"
    if name in OBJECT_SAFETY:
        return "goal" if len(atom) > 1 and atom[1] in targets else "preservation"
    return "goal"


def _best_group(groups):
    """The ``any`` group that went furthest: most core goal atoms, then most other atoms holding (first on ties)."""
    if not groups:
        return []
    key = lambda g: (sum(h for a, h in g if _core(a)), sum(h for a, h in g if not _core(a)))
    return max(groups, key=key)


def goal_constraints(goal):
    """[(atom, holds, category)] of the final goal rows (``any``: the best group)."""
    plain, groups = _rows(goal)
    rows = plain + _best_group(groups)
    targets = _targets(rows)
    return [(a, h, category(a, targets)) for a, h in rows]


def _local_holds(local, goal):
    """True / False / None (a pair not among the logged goal rows)."""
    plain, groups = _rows(goal)
    if local == "goal":
        if not plain and not groups:
            return None
        return all(h for _, h in plain) and (not groups or any(g and all(h for _, h in g) for g in groups))
    for name, subject in local:
        match = lambda a: a and a[0] == name and len(a) > 1 and a[1] == subject
        hits = [h for a, h in plain if match(a)] + [all(h for _, h in g) for g in groups if any(match(a) for a, _ in g)]
        if not hits:
            return None
        if not any(hits):
            return False
    return True


# ------------------------------------------------------------------ paths
def _token(skill, args):
    return (skill, tuple(sorted((k, v if isinstance(v, str) else json.dumps(v, sort_keys=True))
                                for k, v in (args or {}).items() if not k.startswith("hint"))))


def _collapse(seq):
    return [t for i, t in enumerate(seq) if i == 0 or t != seq[i - 1]]


def agent_path(recs):
    return _collapse([_token(c["skill"], c["args"]) for c in recs if c["success"]])


def oracle_paths(task, variant):
    out = {}
    for name, rt in (task.get("routes") or {}).items():
        if rt.get("kind") in ORACLE_KINDS and variant in (rt.get("variants") or []):
            out[name] = _collapse([_token(s["skill"], s.get("args")) for s in rt.get("steps", [])
                                   if s.get("expect") != "fail" and s.get("role") != "unwind"])
    return out


def lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def similarity(a, b):
    n = max(len(a), len(b))
    return lcs(a, b) / n if n else None


def reference_completion_costs(task, variant):
    """key of the failing call -> fewest calls after that failure to the end of a declared fallback route of
    the variant (C* of RE).  The route is one feasible reference, not the required way to recover."""
    out = {}
    for rt in (task.get("routes") or {}).values():
        if rt.get("kind") != "fallback" or variant not in (rt.get("variants") or []):
            continue
        steps = [s for s in rt.get("steps", []) if s.get("role") != "unwind"]
        for p, s in enumerate(steps):
            if s.get("expect") == "fail":
                k = key_of(s["skill"], s.get("args"))
                n = sum(x.get("expect") != "fail" for x in steps[p + 1:])
                if n:
                    out[k] = min(out.get(k, n), n)
    return out


# ------------------------------------------------------------------ state evidence
def _moved(before, after, name):
    s0, s1 = (before or {}).get(name), (after or {}).get(name)
    if not isinstance(s0, dict) or not isinstance(s1, dict) or "pos" not in s0 or "pos" not in s1:
        return False
    return math.dist(s0["pos"], s1["pos"]) > MOVE_M or (s0.get("on") != s1.get("on") and s1.get("on") is not None)


def _same_place(a, b):
    return a is not None and b is not None and (a == b or a.split("/")[0] == b.split("/")[0])


def _put(rec, name, dest):
    """The call left ``name`` on / in ``dest`` (logged support, or a measured postcondition)."""
    on1 = ((rec["state_after"] or {}).get(name) or {}).get("on")
    on0 = ((rec["state_before"] or {}).get(name) or {}).get("on")
    if _same_place(on1, dest) and not _same_place(on0, dest):
        return True
    for chk in rec.get("_post_checks") or []:
        atom = chk.get("atom")
        atom = atom if isinstance(atom, list) else parse_atom(atom)
        if atom and chk.get("holds") is True and not atom[0].startswith("not") and len(atom) >= 3 \
                and (atom[1] == name or isinstance(atom[1], list) and name in atom[1]) \
                and isinstance(atom[-1], str) and _same_place(atom[-1], dest):
            return True
    return False


def adaptation_index(spec, recs):
    for c in recs:
        if not c["success"]:
            continue
        names = arg_values(c["args"])
        for n in spec.get("moved", []):
            if n in names and _moved(c["state_before"], c["state_after"], n):
                return c["index"], f"{c['skill']} moved {n}"
        for n in spec.get("objects", []):
            if n in names:
                for d in spec.get("destinations", []):
                    if _put(c, n, d):
                        return c["index"], f"{c['skill']} put {n} on/in {d}"
    return None, None


# ------------------------------------------------------------------ one episode
def _failure_events(events, recs):
    """Execution / precondition failure events, a run of failures of the same call without a successful call
    in between merged into one (the outcome of its last)."""
    out = []
    for e in events:
        if e["class"] not in ("execution", "precondition"):
            continue
        k = key_of(recs[e["index"]]["skill"], recs[e["index"]]["args"])
        last = out[-1] if out else None
        if last and last["key"] == k and not any(c["success"] for c in recs[last["last"] + 1:e["index"]]):
            last.update(last=e["index"], outcome=e["outcome"], recovered_at=e["recovered_at"], merged=last["merged"] + 1)
            continue
        out.append({"key": k, "action": e["action"], "class": e["class"], "first": e["index"], "last": e["index"],
                    "outcome": e["outcome"], "recovered_at": e["recovered_at"], "merged": 1})
    return out


DESTINATION_ARGS = ("receptacle", "container", "base")


def decoy_placements(spec, recs):
    """object -> the decoy its last successful placement went to (None: not a decoy)."""
    out = {}
    for c in recs:
        if not c["success"]:
            continue
        names = arg_values(c["args"])
        dests = [c["args"][k] for k in DESTINATION_ARGS if isinstance(c["args"].get(k), str)]
        for o in spec["objects"]:
            if o in names and dests:
                d = dests[0]
                bad = d not in spec["allowed"] if spec["decoys"] == "any_other" else d in spec["decoys"]
                out[o] = d if bad else None
    return {o: d for o, d in out.items() if d}


def _constraints(r, task, sub, recs, rows):
    def c(name, cat, kind, scope, holds):
        return {"name": name, "category": cat, "kind": kind, "scope": scope, "holds": bool(holds)}
    out = [c(f"{a[0]}({a[1] if len(a) > 1 else ''})", cat, "hard", "final", h) for a, h, cat in rows]
    if sub.get("declared") and sub.get("used"):
        out.append(c("instruction_semantics", "semantic", "hard", "final", sub["legal"]))
    if "dropped" in r:
        out.append(c("no_floor_drop", "preservation", "hard", "final", not r.get("dropped")))
    start = r.get("initial_positions") or {}
    final = r.get("final_state") or {}
    if start and final:
        keep = set(_goal_objects(task)) | {x for g in (task.get("goal") or {}).get("any", []) for a in g
                                           for x in a[1:] if isinstance(x, str)}
        side = [n for n, p0 in start.items() if n not in keep and isinstance(final.get(n), dict)
                and "pos" in final[n] and math.dist(p0, final[n]["pos"]) > SIDE_EFFECT_M]
        out.append(c("no_side_displacement", "preservation", "soft", "final", not side))
        low = sorted({n for c in recs for n, s in (c["state_after"] or {}).items()
                      if n in start and isinstance(s, dict) and "pos" in s and start[n][2] > 0.3
                      and s["pos"][2] < FLOOR_Z and n not in ((c["state_after"] or {}).get("held") or [])})
        out.append(c("no_transient_floor_drop", "preservation", "soft", "trajectory", not low))
    return out


def episode_protocol(r, task, recs, events, sub, ctx, f):
    """The per-episode inputs of the 12 metrics (recs still carry their states and ``_post_checks``)."""
    variant = r.get("variant")
    p = {"protocol_version": PROTOCOL_VERSION, "tier": (r.get("_scene") or {}).get("difficulty")}
    # A: subgoals and constraints
    rows = goal_constraints(r.get("goal"))
    subgoals = [h for a, h, cat in rows if cat == "goal" and a and a[0] != "hand_empty"]
    p["subgoals"] = {"held": sum(subgoals), "n": len(subgoals)}
    p["SCR"] = sum(subgoals) / len(subgoals) if subgoals else None
    decoy = decoys_for(r["task_id"], variant, ctx.get("decoys"))
    if decoy:            # a failed goal atom of an object left at a decoy: the same atom, now semantic
        placed = decoy_placements(decoy, recs)
        rows = [(a, h, "semantic" if not h and cat == "goal" and len(a) > 1 and a[1] in placed else cat)
                for a, h, cat in rows]
        p["decoy_placements"] = placed
    p["constraints"] = _constraints(r, task, sub, recs, rows)
    # B: path versus the oracle set
    path, refs = agent_path(recs), oracle_paths(task, variant)
    p["oracle_routes"] = sorted(refs)
    if refs:
        p["matches_oracle"] = sorted(n for n, ref in refs.items() if ref == path)
        p["OISR"] = int(bool(f["task_success"]) and not p["matches_oracle"])
        p["OPS"] = max((similarity(path, ref) for ref in refs.values()), key=lambda x: -1 if x is None else x)
        names = [t[0] for t in path]
        p["OPS_skill"] = max((similarity(names, [t[0] for t in ref]) for ref in refs.values()),
                             key=lambda x: -1 if x is None else x)
    else:
        p.update(matches_oracle=None, OISR=None, OPS=None, OPS_skill=None)
    p["planning_failure"] = f["attribution"] in PLANNING_CAUSES
    # C: proactive adaptation
    spec = adaptation_for(r["task_id"], variant, ctx.get("adaptation"))
    fails = [e["index"] for e in events if e["class"] in ("execution", "precondition")]
    first_fail = min(fails) if fails else None
    if spec is not None:
        k, why = adaptation_index(spec, recs)
        local = _local_holds(spec.get("local", "goal"), r.get("goal"))
        p["adaptation"] = {"source": "registry", "adapted_at": k, "evidence": why, "local": local}
    elif sub.get("required"):
        k = sub.get("selected_at")
        local = bool(sub.get("used_substitution") and sub.get("legal"))
        p["adaptation"] = {"source": "substitution", "adapted_at": k,
                           "evidence": "substitute selected" if k is not None else None, "local": local,
                           "timing_unknown": bool(sub.get("selected")) and k is None}
    else:
        p["adaptation"] = None
    if p["adaptation"] is not None:
        a = p["adaptation"]
        a["proactive"] = a["adapted_at"] is not None and (first_fail is None or a["adapted_at"] < first_fail)
        a["reactive"] = a["adapted_at"] is not None and not a["proactive"]
        a["success"] = a["proactive"] and a["local"] is True
    # C: recovery events, fallback decisions, recovery cost
    ref_cost = reference_completion_costs(task, variant)
    task_ok = bool(f["task_success"])
    fevents = []
    for e in _failure_events(events, recs):
        local = e["outcome"] in RECOVERED
        recovered = local or task_ok                          # any legal path to the goal counts
        nxt = recs[e["last"] + 1] if e["last"] + 1 < len(recs) else None
        if nxt is None:
            decision, valid = "abandoned", None
        elif key_of(nxt["skill"], nxt["args"]) == e["key"]:
            decision, valid = "retry", None                   # a blind retry: right or lucky, not a fallback choice
        elif nxt["plan"] == "invalid":
            decision, valid = "fallback", False
        elif nxt["success"] and (task_ok or e["outcome"] in ("local_recovery", "resolved_by_alternative")):
            decision, valid = "fallback", True
        elif nxt["success"] and not recovered:
            decision, valid = "fallback", False
        else:
            decision, valid = "fallback", None
        c_ref = ref_cost.get(e["key"])
        cost = len(recs) - 1 - e["first"] if task_ok else None     # calls after the failure to the finished task
        fevents.append({"action": e["action"], "class": e["class"], "first": e["first"], "merged": e["merged"],
                        "outcome": e["outcome"], "recovered": recovered, "verified": e["outcome"] == "local_recovery",
                        "resolution": e["outcome"] if local else "task_completed" if task_ok else "not_recovered",
                        "local_cost": e["recovered_at"] - e["first"] if local and e["recovered_at"] is not None
                        else None,
                        "decision": decision, "decision_valid": valid, "cost": cost, "ref_cost": c_ref,
                        "RE": (c_ref / max(cost, c_ref)) if cost and c_ref else None,
                        "unrecovered_cost": None if recovered else len(recs) - 1 - e["first"]})
    p["failure_events"] = fevents
    # D: skill execution
    calls = Counter()
    for c in recs:
        if c["success"]:
            calls["verified"] += 1
        elif c["class"] == "invalid":
            calls["refused_interface"] += 1
        elif c["class"] == "precondition":
            calls["refused_precondition"] += 1
        elif c["class"] == "observation" and c["skill"] not in PERCEPTION:
            calls["refused_observation"] += 1
        else:
            calls["execution_failed"] += 1                # incl. a perception call that found nothing
    p["calls"] = dict(calls)
    return p


# ------------------------------------------------------------------ aggregation
def _mean_n(xs):
    xs = [x for x in xs if x is not None]
    return {"mean": mean(xs), "n": len(xs)}


def rtsr(eps, reps=BOOTSTRAP, seed=0):
    """Mean over tasks of the mean over variants of the mean over seeds, with a bootstrap over seeds."""
    cells = defaultdict(list)
    for x in eps:
        cells[(x["task"], x["variant"])].append(float(x["task_success"]))

    def value(c):
        by_task = defaultdict(list)
        for (t, _), ys in c.items():
            by_task[t].append(sum(ys) / len(ys))
        return mean([mean(v) for v in by_task.values()]), {t: mean(v) for t, v in sorted(by_task.items())}
    if not cells:
        return {"value": None, "ci95": None, "per_task": {}, "n_tasks": 0, "n_cells": 0}
    v, per = value(cells)
    rng = random.Random(seed)
    boots = sorted(value({k: [rng.choice(ys) for _ in ys] for k, ys in cells.items()})[0] for _ in range(reps))
    return {"value": v, "ci95": [boots[int(0.025 * reps)], boots[int(0.975 * reps) - 1]], "per_task": per,
            "n_tasks": len(per), "n_cells": len(cells)}


def protocol_summary(facts):
    """The 12 metrics over a set of episodes (one planner, or one planner and tier)."""
    valid = [x for x in facts if x["attribution"] != "system_error" and x.get("protocol")]
    P = [x["protocol"] for x in valid]
    out = {"protocol_version": PROTOCOL_VERSION, "episodes": len(valid),
           "system_error": sum(x["attribution"] == "system_error" for x in facts)}
    # A
    out["TSR"] = rate(sum(x["task_success"] for x in valid), len(valid))
    out["SCR"] = _mean_n([p["SCR"] for p in P])
    out["SCR_failed"] = _mean_n([p["SCR"] for x, p in zip(valid, P) if not x["task_success"]])
    cons = [c for p in P for c in p["constraints"]]
    hard = [c for c in cons if c["kind"] == "hard"]
    out["CSR"] = rate(sum(c["holds"] for c in cons), len(cons))
    out["CSR_hard"] = rate(sum(c["holds"] for c in hard), len(hard))
    for cat in CATEGORIES:
        sel = [c for c in cons if c.get("category") == cat]
        out[f"CSR_{cat}"] = rate(sum(c["holds"] for c in sel), len(sel))
    out["CSR_trajectory"] = rate(sum(c["holds"] for c in cons if c["scope"] == "trajectory"),
                                 sum(c["scope"] == "trajectory" for c in cons))
    out["constraint_violations"] = dict(Counter(f"{c.get('category')}/{c['name'].split('(')[0]}"
                                               for c in cons if not c["holds"]))
    out["hard_violation_episodes"] = sum(any(c["kind"] == "hard" and not c["holds"] for c in p["constraints"]) for p in P)
    # B
    with_oracle = [(x, p) for x, p in zip(valid, P) if p["OISR"] is not None]
    out["OISR"] = rate(sum(p["OISR"] for _, p in with_oracle), len(with_oracle))
    out["OISR_of_successes"] = rate(sum(p["OISR"] for x, p in with_oracle if x["task_success"]),
                                    sum(bool(x["task_success"]) for x, _ in with_oracle))
    out["no_oracle"] = len(valid) - len(with_oracle)
    out["OPS"] = _mean_n([p["OPS"] for p in P])
    out["OPS_skill"] = _mean_n([p["OPS_skill"] for p in P])
    out["PFR"] = rate(sum(p["planning_failure"] for p in P), len(valid))
    out["failure_split"] = dict(Counter(
        "planning" if x["attribution"] in PLANNING_CAUSES else
        "physical" if x["attribution"] == "low_level_execution_failure" else x["attribution"]
        for x in facts if not x["task_success"]))
    # C
    ad = [p["adaptation"] for p in P if p["adaptation"]]
    out["PASR"] = rate(sum(a["success"] for a in ad), len(ad))
    out["adaptation"] = {"opportunities": len(ad), "proactive": sum(a["proactive"] for a in ad),
                         "proactive_local_failed": sum(a["proactive"] and a["local"] is not True for a in ad),
                         "reactive": sum(a["reactive"] for a in ad),
                         "never": sum(a["adapted_at"] is None for a in ad),
                         "timing_unknown": sum(bool(a.get("timing_unknown")) for a in ad),
                         "by_source": dict(Counter(a["source"] for a in ad))}
    ev = [(x, e) for x, p in zip(valid, P) for e in p["failure_events"]]
    rec = [(x, e) for x, e in ev if e["recovered"]]
    out["RRSR"] = rate(len(rec), len(ev))
    out["RRSR_verified"] = rate(sum(e["verified"] for _, e in ev), len(ev))
    out["RRSR_then_task_success"] = rate(sum(bool(x["task_success"]) for x, _ in rec), len(rec))
    out["recovery_outcomes"] = dict(Counter(e["resolution"] for _, e in ev))
    out["merged_repeats"] = sum(e["merged"] - 1 for _, e in ev)
    dec = [e for _, e in ev if e["decision"] == "fallback"]
    out["FSA"] = rate(sum(e["decision_valid"] is True for e in dec), sum(e["decision_valid"] is not None for e in dec))
    out["fallback_decisions"] = {"total": len(dec), "undetermined": sum(e["decision_valid"] is None for e in dec),
                                 "blind_retry": sum(e["decision"] == "retry" for _, e in ev),
                                 "abandoned": sum(e["decision"] == "abandoned" for _, e in ev)}
    out["RE"] = _mean_n([e["RE"] for _, e in rec])
    finished = [e for x, e in rec if x["task_success"]]
    out["RE_coverage"] = rate(sum(e["RE"] is not None for e in finished), len(finished))
    out["recovery_cost"] = _mean_n([e["cost"] for _, e in rec])
    out["recovery_cost_no_ref"] = _mean_n([e["cost"] for _, e in rec if e["ref_cost"] is None])
    out["local_recovery_cost"] = _mean_n([e["local_cost"] for _, e in ev])
    out["unrecovered_cost"] = _mean_n([e["unrecovered_cost"] for _, e in ev if not e["recovered"]])
    # D
    calls = Counter()
    for p in P:
        calls.update(p["calls"])
    executed = calls["verified"] + calls["execution_failed"]
    total = sum(calls.values())
    out["SESR"] = rate(calls["verified"], executed)
    out["refusal_rate"] = rate(total - executed, total)
    out["calls"] = dict(calls)
    out["RTSR"] = rtsr(valid)
    return out


# ------------------------------------------------------------------ markdown
def _f(x, pct=True):
    if x is None:
        return "N/A"
    if "den" in x:
        if not x["den"]:
            return "N/A (0/0)"
        ci = x.get("ci95")
        v = f"{100 * x['value']:.0f}%" if pct else f"{x['value']:.2f}"
        return f"{v} ({x['num']}/{x['den']})" + (f" [{100 * ci[0]:.0f}–{100 * ci[1]:.0f}]" if ci and pct else "")
    if "mean" in x:
        return "N/A" if x["mean"] is None else f"{x['mean']:.2f} (n={x['n']})"
    if "per_task" in x:
        return "N/A" if x["value"] is None else \
            f"{100 * x['value']:.0f}% [{100 * x['ci95'][0]:.0f}–{100 * x['ci95'][1]:.0f}] ({x['n_tasks']} tasks)"
    return str(x)


MAIN = [("TSR", "TSR"), ("SCR", "SCR"), ("OISR", "OISR"), ("PASR", "PASR"), ("RRSR", "RRSR"), ("RTSR", "RTSR")]


def protocol_markdown(summaries, tiers=None):
    """summaries: {planner: protocol_summary}; tiers: {(planner, tier): protocol_summary} for the main metrics."""
    ps = sorted(summaries)
    S = summaries

    def row(name, fn, keys=ps, src=S):
        return f"| {name} | " + " | ".join(fn(src[k]) for k in keys) + " |"
    head, sep = "| Metric | " + " | ".join(ps) + " |", "|---|" + "---|" * len(ps)
    cnt = lambda d: ", ".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda kv: str(kv[0]))) or "-"
    md = ["## Quantitative protocol (12 metrics)", "",
          "Definitions and pre-registered rules: README, *Quantitative protocol*. Ratios: value (num/den) "
          "[Wilson 95 % CI]; RTSR: bootstrap over seeds. N/A = nothing eligible. `scripted` / `oracle` rows are "
          "feasibility evidence, not planner results.", "",
          "### Main table", "", head, sep] + [row(t, lambda s, k=k: _f(s[k])) for t, k in MAIN]
    md += ["", "### A · Task completion", "", head, sep,
           row("episodes (valid) / system error", lambda s: f"{s['episodes']} / {s['system_error']}"),
           row("SCR of failed episodes", lambda s: _f(s["SCR_failed"])),
           row("CSR (all constraints)", lambda s: _f(s["CSR"])),
           row("CSR (hard)", lambda s: _f(s["CSR_hard"])),
           *[row(f"CSR ({cat})", lambda s, cat=cat: _f(s[f"CSR_{cat}"])) for cat in CATEGORIES],
           row("CSR (trajectory)", lambda s: _f(s["CSR_trajectory"])),
           row("episodes with a hard violation", lambda s: str(s["hard_violation_episodes"])),
           row("violations by constraint", lambda s: cnt(s["constraint_violations"])),
           "", "### B · Planning and oracle", "", head, sep,
           row("OISR among successes", lambda s: _f(s["OISR_of_successes"])),
           row("episodes without an oracle (OISR N/A)", lambda s: str(s["no_oracle"])),
           row("OPS (calls)", lambda s: _f(s["OPS"])),
           row("OPS (skill names)", lambda s: _f(s["OPS_skill"])),
           row("PFR", lambda s: _f(s["PFR"])),
           row("failed episodes by cause", lambda s: cnt(s["failure_split"])),
           "", "### C · Adaptation and recovery", "", head, sep,
           row("opportunities / proactive / reactive / never", lambda s: "{opportunities} / {proactive} / "
               "{reactive} / {never}".format(**s["adaptation"])),
           row("proactive, local goal not met", lambda s: str(s["adaptation"]["proactive_local_failed"])),
           row("RRSR verified (state evidence)", lambda s: _f(s["RRSR_verified"])),
           row("recovered events in successful episodes", lambda s: _f(s["RRSR_then_task_success"])),
           row("recovery outcomes", lambda s: cnt(s["recovery_outcomes"])),
           row("repeated failures merged", lambda s: str(s["merged_repeats"])),
           row("FSA (first call after a failure ran, and the task was finished)", lambda s: _f(s["FSA"])),
           row("fallback decisions: total / undetermined / blind retry / abandoned",
               lambda s: "{total} / {undetermined} / {blind_retry} / {abandoned}".format(**s["fallback_decisions"])),
           row("RE (vs declared fallback route)", lambda s: _f(s["RE"])),
           row("RE coverage (recovered events in successful episodes with a reference)",
               lambda s: _f(s["RE_coverage"])),
           row("calls from failure to finished task", lambda s: _f(s["recovery_cost"])),
           row("... of events without a reference route", lambda s: _f(s["recovery_cost_no_ref"])),
           row("calls until local recovery (same / equivalent result)", lambda s: _f(s["local_recovery_cost"])),
           row("calls after an unrecovered failure", lambda s: _f(s["unrecovered_cost"])),
           "", "### D · Execution and robustness", "", head, sep,
           row("SESR", lambda s: _f(s["SESR"])),
           row("refusal rate (interface / precondition / gate)", lambda s: _f(s["refusal_rate"])),
           row("calls by result", lambda s: cnt(s["calls"])),
           row("RTSR per task", lambda s: ", ".join(f"{t[:3]} {100 * v:.0f}%" for t, v in s["RTSR"]["per_task"].items())
               or "-")]
    if tiers:
        keys = sorted(tiers, key=lambda k: (k[0], ["easy", "medium", "hard"].index(k[1])
                                            if k[1] in ("easy", "medium", "hard") else 9, str(k[1])))
        md += ["", "### Main metrics by tier", "", "| Planner | Tier | n | " + " | ".join(t for t, _ in MAIN) + " |",
               "|---|---|---|" + "---|" * len(MAIN)]
        for k in keys:
            s = tiers[k]
            md.append(f"| {k[0]} | {k[1]} | {s['episodes']} | " + " | ".join(_f(s[m]) for _, m in MAIN) + " |")
    return md
