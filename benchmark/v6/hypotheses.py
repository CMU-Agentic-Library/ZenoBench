"""Capability hypotheses: independent rule checks and the tier rule shared by v5 and v6 variants.

A capability claim is accepted only when three things hold, each checked from the configuration (never from
the presence of an operation in the oracle route alone):

1. **cause**     - a declared cause exists in the variant: an injected failure (``failure:<id>``), an overlay
                   difference from the control variant (``overlay:<object>``), a goal the variant changes
                   (``goal``) or a thermal override (``thermal:<food>``);
2. **necessity** - the cause blocks the task's nominal plan at the step the capability is about (the nominal
                   route contains that step, and the cause names its objects / place / appliance, or a
                   persistent failure matches it);
3. **oracle**    - the reference route recovers in the way the capability describes (and not by the blocked
                   nominal step again).

Per capability:

* **DR** dependency replanning - ``blocker`` (not a goal subject, never touched by the nominal plan) is
  manipulated before the ``blocked`` step succeeds; the cause names the blocker (or the place inside it).
* **GD** goal decomposition - ``inspection``: the oracle inspects every listed place, the nominal plan fewer;
  ``decomposition``: the goal requires the listed subgoals, the nominal plan achieves fewer, the oracle all;
  ``split``: a batch step of the nominal plan is replaced by one achieving step per part; ``allocation``:
  >= 2 goal objects go to >= 2 receptacles, differently from the nominal plan.
* **SR** strategy replacement - the ``nominal`` procedure (skill + role arguments) does not succeed after the
  cause applies, the ``replacement`` (another skill, appliance, base or hand use) does.
* **CL** cross-level recovery - a persistent action failure (a retry cannot help) on a nominal step, and the
  oracle changes the object, destination, appliance or procedure, or inserts a subgoal (``until_moved``).
* **PP** partial-progress preservation - a goal atom is achieved before a dynamic event / persistent failure,
  and the oracle never redoes or touches it afterwards; the goal has >= 2 subgoals.
* **AF** alternative / fallback - ``task``: a substitute the goal allows, or a search / explore recovery;
  ``local``: a transient failure retried.

Tier rule (``tier_rule``): Hard = >= 1 verified core capability (DR, GD, SR, CL, PP) and not solvable by
retrying the nominal plan (``retry_solvable``); Medium = an adaptation (failure, condition, or an overlay that
touches the nominal plan) without a core capability; Easy = otherwise.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ("DR", "GD", "SR", "CL", "PP")
CAPS = CORE + ("AF",)
ACTION_KINDS = ("grasp", "slip", "placement", "ik")
# achieving skills: (subject argument, destination / tool argument)
ACH = {"place": ("object", "receptacle"), "drop": ("object", "container"), "stack": ("object", "base"),
       "collect": ("objects", "container"), "hide": ("object", "receptacle"), "heat": ("food", "appliance"),
       "cover": ("container", "lid"), "flip": ("object", None), "roll": ("object", None),
       "wipe": ("surface", "tool"), "inspect": ("receptacle", None), "stir": ("container", "tool"),
       "fetch": ("object", "receptacle"), "clear": ("support", "receptacle"), "close": ("articulated", None)}
MANIP = set(ACH) | {"pick", "open", "uncover", "push", "separate", "expose", "pull", "regrasp", "tip", "upright",
                    "center", "lift", "lower", "rotate", "knock"}
INSPECT = {"inspect", "explore_furniture"}
SUBJ = {"on", "inside", "fully_inside", "on_top_of", "flipped", "object_rolled", "hidden", "covered",
        "temperature_at_least", "observed", "stirred", "wiped", "grouped", "is_closed"}
SEARCH = {"search", "explore_room", "explore_furniture"}
DEFAULTS = {"hands": "right"}
ROLE_ARGS = ("appliance", "base", "hands", "container", "receptacle")


# ----------------------------------------------------------------- small helpers
def ok(s):
    return s.get("expect") != "fail"


def vals(step):
    out = set()
    for v in step["args"].values():
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, str):
                out.add(x)
    return out


def related(a, b):
    """Entity names that denote the same thing or a part of it (kitchen_microwave ~ kitchen_microwave/inside_floor)."""
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def touches(ents, names):
    return any(related(e, n) for e in ents for n in names)


def match(step, proc):
    if step["skill"] != proc["skill"]:
        return False
    return all(step["args"].get(k, DEFAULTS.get(k)) == v for k, v in (proc.get("args") or {}).items())


def holding(steps, i):
    """(object held, two-handed) before step i (only steps that succeed change the hand)."""
    held, two = None, False
    for s in steps[:i]:
        if not ok(s):
            if s["skill"] == "navigate":
                held, two = None, False             # a carry that fails is a slip: the object is on its support again
            continue
        if s["skill"] == "pick":
            held, two = s["args"]["object"], s["args"].get("hands") == "both"
        elif s["skill"] in ("place", "drop", "stack", "hide") and s["args"].get("object") == held:
            held, two = None, False
    return held, two


def trig_hits(steps, f):
    """Indices of the route steps a failure's trigger matches (every call, nth ignored)."""
    t = f.get("trigger") or {}
    out = []
    for i, s in enumerate(steps):
        if s["skill"] != t.get("skill"):
            continue
        if any(s["args"].get(k) != v for k, v in (t.get("args") or {}).items()):
            continue
        if t.get("while_holding"):
            h, two = holding(steps, i)
            if h != t["while_holding"] or (t.get("one_handed") and two):
                continue
        out.append(i)
    return out


def goal_atoms(goal, group=None):
    atoms = list(goal.get("all", []))
    anys = goal.get("any", [])
    if anys:
        atoms += anys[group] if group is not None else [a for g in anys for a in g]
    return atoms


def subjects(goal):
    out = set()
    for a in goal_atoms(goal):
        if a[0] in SUBJ and len(a) > 1:
            for x in (a[1] if isinstance(a[1], list) else [a[1]]):
                if isinstance(x, str):
                    out.add(x)
    return out


def achieved_subjects(goal):
    """Subjects of achievement atoms (not of restore constraints such as is_closed)."""
    keep = lambda atoms: [x for x in atoms if x[0] != "is_closed"]  # noqa: E731
    return subjects({"all": keep(goal.get("all", [])), "any": [keep(g) for g in goal.get("any", [])]})


def goal_entities(goal):
    out = set()
    for a in goal_atoms(goal):
        for x in a[1:]:
            for n in (x if isinstance(x, list) else [x]):
                if isinstance(n, str):
                    out.add(n)
    return out


def atom_in_goal(atom, goal):
    for a in goal_atoms(goal):
        if a[0] == atom[0] and [x for x in a[1:len(atom)]] == list(atom[1:]):
            return True
        if a[0] == atom[0] == "grouped" and set(a[1]) == set(atom[1]):
            return True
    return False


def n_subgoals(goal, group=0):
    atoms = goal_atoms(goal, group if goal.get("any") else None)
    return sum(1 for a in atoms if a[0] in SUBJ)


# ----------------------------------------------------------------- variant context
class Ctx:
    def __init__(self, task, vid):
        from episode.catalog import resolve_task
        self.task, self.vid = task, vid
        self.v = task["variants"][vid]
        self.goal = resolve_task(task, vid)["goal"]
        self.route = task["routes"][task["oracle"][vid]]["steps"]
        self.fails = {f["id"]: f for f in self.v.get("failures", [])}
        self.control = self._control()
        # the reference plan a capability must be necessary against: the control variant's plan (its successful
        # steps), i.e. what the planner would do if the one differing factor were absent; else the task's nominal
        # the goal without the differing factor: atoms a variant adds about an obstruction ("leave the block on
        # the island") are constraints on it, not reasons to handle it
        self.control_goal = resolve_task(task, self.control)["goal"] if self.control else self.goal
        if self.control and self.control != vid and self.control in task["oracle"]:
            self.nominal = [s for s in task["routes"][task["oracle"][self.control]]["steps"] if ok(s)]
        else:
            self.nominal = task["routes"][task["nominal"]]["steps"]

    def _control(self):
        meta = self.v.get("v6") or {}
        if meta.get("control") in self.task["variants"]:
            return meta["control"]
        easy = (self.task.get("v5_formal") or {}).get("easy") or []
        return easy[0] if easy else None

    def overlay_diff(self):
        """object -> its overlay entry (or None when removed) where the variant differs from its control."""
        c = self.task["variants"].get(self.control, {}) if self.control else {}
        out = {}
        for key in ("move", "add"):
            mine, theirs = self.v.get(key, {}), c.get(key, {})
            for n, m in mine.items():
                o = theirs.get(n)
                if o is None or o.get("support") != m.get("support") or \
                        any(abs(a - b) > 0.01 for a, b in zip(o.get("xy", []), m.get("xy", []))) or \
                        abs((o.get("z") or 0) - (m.get("z") or 0)) > 0.01:
                    out[n] = m
        for n in set(self.v.get("remove", [])) - set(c.get("remove", [])):
            out[n] = None
        return out

    def cause_ents(self, cause):
        """The names a cause touches, or None when the cause does not exist in this variant."""
        kind, _, ref = cause.partition(":")
        if kind == "failure":
            f = self.fails.get(ref)
            if not f:
                return None
            ents = set()
            t = f.get("trigger") or {}
            for v in list((t.get("args") or {}).values()) + [t.get("while_holding")]:
                for x in (v if isinstance(v, list) else [v]):
                    if isinstance(x, str):
                        ents.add(x)
            for a in f.get("check", []) + f.get("report", []):
                ents |= {x for x in a[1:] if isinstance(x, str)}
            ev = f.get("event") or {}
            for k in ("object", "container", "articulated", "onto"):
                if isinstance(ev.get(k), str):
                    ents.add(ev[k])
            if (ev.get("to") or {}).get("support"):
                ents.add(ev["to"]["support"])
            if f.get("until_moved"):
                ents.add(f["until_moved"])
            for k in ("receptacle", "to"):
                if isinstance(f.get(k), dict) and f[k].get("support"):
                    ents.add(f[k]["support"])
            return ents
        if kind == "overlay":
            d = self.overlay_diff()
            if ref not in d:
                return None
            m = d[ref]
            return {ref} | ({m["support"]} if m and m.get("support") else set())
        if kind == "goal":
            if self.goal == self.task["goal"]:
                return None
            return subjects(self.goal)
        if kind == "thermal":
            return {ref} if ref in (self.v.get("thermal_override") or {}) else None
        if kind == "condition":
            return set() if ref in self.v.get("conditions", []) else None
        return None

    def causes(self):
        out = [f"failure:{i}" for i in self.fails]
        out += [f"overlay:{n}" for n in self.overlay_diff()]
        out += [f"thermal:{n}" for n in (self.v.get("thermal_override") or {})]
        if self.goal != self.task["goal"]:
            out.append("goal")
        return out

    def onset(self, cause):
        """Route index from which the cause applies (-1: from the start)."""
        kind, _, ref = cause.partition(":")
        if kind != "failure":
            return -1
        f = self.fails[ref]
        hits = trig_hits(self.route, f)
        if f["kind"] in ACTION_KINDS:
            bad = [i for i in hits if not ok(self.route[i])]
            return max(bad) if bad else (hits[0] if hits else -1)
        if f.get("when", "initial") == "dynamic":
            good = [i for i in hits if ok(self.route[i])]
            n = int(f["trigger"].get("nth", 1))
            return good[n - 1] if len(good) >= n else -1
        return -1

    def nominal_hit(self, ents):
        return any(touches(vals(s), ents) for s in self.nominal)


# ----------------------------------------------------------------- per-capability checks
def check_DR(c: Ctx, h):
    r = []
    B, bl = h["blocker"], h["blocked"]
    if B in achieved_subjects(c.goal) and B in achieved_subjects(c.control_goal):
        r.append(f"{B} is a goal subject (fetching it is not an inserted precondition)")
    ents = c.cause_ents(h["cause"])
    if ents is None:
        r.append(f"cause {h['cause']} not in the variant")
    elif not touches(ents, {B}):
        r.append(f"cause {h['cause']} does not name {B}")
    if not any(s["skill"] == bl["skill"] and bl["target"] in vals(s) for s in c.nominal):
        r.append(f"the nominal plan has no {bl['skill']}({bl['target']})")
    if any(s["skill"] in MANIP and B in vals(s) for s in c.nominal):
        r.append(f"the nominal plan already manipulates {B}")
    ks = [i for i, s in enumerate(c.route) if ok(s) and s["skill"] == bl["skill"] and bl["target"] in vals(s)]
    if not ks:
        r.append(f"the oracle never succeeds at {bl['skill']}({bl['target']})")
    elif not any(ok(s) and s["skill"] in MANIP and B in vals(s) for s in c.route[:ks[-1]]):
        r.append(f"the oracle does not manipulate {B} before {bl['skill']}({bl['target']})")
    return r


def _inspects(steps, place):
    return any(ok(s) and ((s["skill"] in INSPECT and place in vals(s)) or
                          (s["skill"] == "look" and related(s["args"].get("target", ""), place)
                           and s["args"].get("target") != place + "/top")) for s in steps)


def _achieves(steps, atom):
    """Index of the oracle step that achieves a goal atom, or None."""
    p, subj = atom[0], atom[1]
    for i, s in enumerate(steps):
        if not ok(s) or s["skill"] not in ACH:
            continue
        a = s["args"]
        if p == "grouped":
            continue
        if p == "on_top_of" and s["skill"] == "stack" and a.get("object") == subj and a.get("base") == atom[2]:
            return i
        if p in ("on", "inside", "fully_inside") and a.get("object") == subj and \
                (len(atom) < 3 or related(a.get("receptacle") or a.get("container") or "", atom[2])):
            return i
        if p in ("hidden",) and a.get("object") == subj and s["skill"] in ("hide", "drop"):
            return i
        if p in ("hidden",) and s["skill"] == "drop" and a.get("object") == subj:
            return i
        if p == "temperature_at_least" and s["skill"] == "heat" and a.get("food") == subj:
            return i
        if p in ("covered", "stirred", "wiped", "observed", "flipped", "object_rolled") and subj in vals(s):
            return i
    return None


def check_GD(c: Ctx, h):
    r = []
    kind = h["kind"]
    ents = c.cause_ents(h["cause"])
    if ents is None:
        r.append(f"cause {h['cause']} not in the variant")
        ents = set()
    if kind == "inspection":
        places = h["places"]
        if len(places) < 2:
            r.append("fewer than two places")
        miss = [p for p in places if not _inspects(c.route, p)]
        if miss:
            r.append(f"the oracle does not inspect {miss}")
        if sum(_inspects(c.nominal, p) for p in places) >= len(places):
            r.append("the nominal plan already inspects every place")
        if ents and not touches(ents, set(places)):
            r.append(f"cause {h['cause']} does not concern the inspected places")
    elif kind == "decomposition":
        sub = h["subgoals"]
        if len(sub) < 2:
            r.append("fewer than two subgoals")
        if h["cause"] == "goal" and ents == set():
            r.append("no goal override")
        missing = [a for a in sub if not atom_in_goal(a, c.goal)]
        if missing:
            r.append(f"subgoals not in the goal: {missing}")
        def done(steps, a):
            if a[0] == "grouped":
                return all(any(ok(s) and s["skill"] == "place" and s["args"].get("object") == m for s in steps)
                           for m in a[1][:-1])
            return _achieves(steps, a) is not None
        if sum(done(c.nominal, a) for a in sub) >= len(sub):
            r.append("the nominal plan already achieves as many subgoals")
        for a in sub:
            if not done(c.route, a):
                r.append(f"the oracle never achieves {a}")
    elif kind == "split":
        batch = h["batch"]
        if not any(match(s, batch) for s in c.nominal):
            r.append("the nominal plan has no batch step")
        t0 = c.onset(h["cause"])
        if any(ok(s) and match(s, batch) for s in c.route[t0 + 1:]):
            r.append("the oracle still runs the batch step")
        for p in h["parts"]:
            if not any(ok(s) and s["skill"] in ACH and not match(s, batch) and
                       (s["args"].get("object") == p or p in (s["args"].get("objects") or [])) for s in c.route[t0 + 1:]):
                r.append(f"no separate achieving step for {p}")
        if ents and not touches(ents, vals({"args": batch["args"]})):
            r.append("cause does not concern the batch step")
    elif kind == "allocation":
        alloc = h["allocation"]
        if len(alloc) < 2:
            r.append("needs >= 2 objects to allocate")
        for o, rec in alloc.items():
            if not any(ok(s) and s["skill"] in ACH and s["args"].get(ACH[s["skill"]][0]) == o and
                       related(s["args"].get(ACH[s["skill"]][1]) or "", rec) for s in c.route):
                r.append(f"the oracle does not put {o} into {rec}")
        nom = {s["args"].get(ACH[s["skill"]][0]): s["args"].get(ACH[s["skill"]][1]) for s in c.nominal
               if ok(s) and s["skill"] in ACH and ACH[s["skill"]][1]}
        if all(nom.get(o) == rec for o, rec in alloc.items()):
            r.append("the nominal plan already allocates this way")
        if ents and not touches(ents, set(alloc) | set(alloc.values()) | {x for x in nom.values() if x}):
            r.append("cause does not concern the allocation")
    else:
        r.append(f"unknown GD kind {kind}")
    return r


def check_SR(c: Ctx, h):
    r = []
    nom, rep = h["nominal"], h["replacement"]
    if nom == rep or (nom["skill"] == rep["skill"] and all(rep["args"].get(k) == v for k, v in nom["args"].items()
                                                            if k in ROLE_ARGS) and nom["skill"] != "stack"):
        r.append("the replacement does not change the procedure (same skill and role arguments)")
    ents = c.cause_ents(h["cause"])
    if ents is None:
        r.append(f"cause {h['cause']} not in the variant")
    else:
        if not any(match(s, nom) for s in c.nominal):
            r.append("the nominal plan does not use the nominal procedure")
        elif ents and not any(match(s, nom) and touches(vals(s), ents) for s in c.nominal):
            r.append(f"cause {h['cause']} does not concern the nominal procedure")
        t0 = c.onset(h["cause"])
        if any(ok(s) and match(s, nom) for s in c.route[t0 + 1:]):
            r.append("the oracle still uses the nominal procedure after the cause")
        if not any(ok(s) and match(s, rep) for s in c.route[t0 + 1:]):
            r.append("the oracle never uses the replacement")
    return r


def check_CL(c: Ctx, h):
    r = []
    f = c.fails.get(h["failure"])
    if not f:
        return [f"no failure {h['failure']}"]
    if f["kind"] not in ACTION_KINDS:
        r.append("not an action-level failure")
    if not f.get("persist") or (f["kind"] == "ik" and f.get("until", "base_skill") != "never"):
        r.append("not persistent: a retry could succeed")
    if not trig_hits(c.nominal, f):
        r.append("the nominal plan never makes the failing call")
    hits = trig_hits(c.route, f)
    bad = [i for i in hits if not ok(c.route[i])]
    if not bad:
        return r + ["the oracle never meets the failure"]
    last = max(bad)
    after = [i for i in hits if ok(c.route[i]) and i > last]
    ch, to = h["change"], h["to"]
    if f.get("until_moved"):
        if ch != "subgoal" or to != f["until_moved"]:
            r.append("an until_moved failure is recovered by moving that object (change subgoal)")
        nxt = after[0] if after else len(c.route)
        if not any(ok(s) and s["skill"] in MANIP and to in vals(s) for s in c.route[last + 1:nxt]):
            r.append(f"the oracle does not move {to} before retrying")
        if not after:
            r.append("the oracle never completes the blocked call")
        return r
    if after:
        r.append("the oracle repeats the failing call successfully (the failure is not persistent for it)")
    tail = c.route[last + 1:]
    ge = goal_entities(c.goal)
    if ch == "object":
        if not any(ok(s) and s["skill"] == "pick" and s["args"]["object"] == to for s in tail):
            r.append(f"the oracle does not pick {to}")
        if any(s["skill"] == "pick" and s["args"].get("object") == to for s in c.nominal):
            r.append(f"the nominal plan already uses {to}")
        if to not in ge and not any(ok(s) and s["skill"] in ("stir", "wipe") and to in vals(s) for s in tail):
            r.append(f"{to} is not allowed by the goal")
    elif ch == "destination":
        if not any(ok(s) and s["skill"] in ACH and ACH[s["skill"]][1] and s["args"].get(ACH[s["skill"]][1]) == to
                   for s in tail):
            r.append(f"the oracle does not use {to}")
        if any(s["skill"] in ACH and ACH[s["skill"]][1] and s["args"].get(ACH[s["skill"]][1]) == to for s in c.nominal):
            r.append(f"the nominal plan already uses {to}")
        if to not in ge:
            r.append(f"{to} is not allowed by the goal")
    elif ch == "appliance":
        if not any(ok(s) and s["skill"] == "heat" and s["args"].get("appliance") == to for s in tail):
            r.append(f"the oracle does not heat with {to}")
        if any(s["skill"] == "heat" and s["args"].get("appliance") == to for s in c.nominal):
            r.append(f"the nominal plan already uses {to}")
    elif ch == "procedure":
        skill, _, kv = to.partition(":")
        proc = {"skill": skill, "args": dict([kv.split("=")]) if kv else {}}
        if not any(ok(s) and match(s, proc) for s in tail):
            r.append(f"the oracle does not use {to}")
        if any(match(s, proc) for s in c.nominal):
            r.append(f"the nominal plan already uses {to}")
    else:
        r.append(f"unknown change {ch}")
    return r


def check_PP(c: Ctx, h):
    r = []
    kept, f = h["kept"], c.fails.get(h["event"])
    if not f:
        return [f"no failure {h['event']}"]
    dynamic = f["kind"] not in ACTION_KINDS and f.get("when", "initial") == "dynamic"
    if not dynamic and not (f["kind"] in ACTION_KINDS and f.get("persist")):
        r.append("the event is neither dynamic nor a persistent failure (a retry keeps progress trivially)")
    if not atom_in_goal(kept["atom"], c.goal):
        r.append(f"{kept['atom']} is not a goal atom")
    if n_subgoals(c.goal) < 2:
        r.append("the goal has fewer than two subgoals")
    by = [i for i, s in enumerate(c.route) if ok(s) and match(s, kept["by"])]
    t0 = c.onset(f"failure:{h['event']}")
    if not by:
        r.append("the oracle never achieves the kept atom")
    elif t0 < 0 or by[0] > t0 or (by[0] == t0 and not dynamic):
        r.append("the kept atom is not achieved before the event")
    subj = kept["atom"][1] if isinstance(kept["atom"][1], str) else None
    later = c.route[t0 + 1:] if t0 >= 0 else []
    if any(ok(s) and match(s, kept["by"]) for s in later):
        r.append("the oracle redoes the kept subgoal")
    if subj and any(ok(s) and s["skill"] in MANIP - {"close", "inspect"} and s["args"].get("object") == subj for s in later):
        r.append(f"the oracle handles {subj} again")
    ev = f.get("event") or {}
    if subj and ev.get("object") == subj:
        r.append("the event moves the kept object itself")
    return r


def check_AF(c: Ctx, h):
    r = []
    if h["level"] == "local":
        tr = [f for f in c.fails.values() if f["kind"] in ACTION_KINDS and not f.get("persist")]
        if not tr:
            r.append("no transient action failure")
        for f in tr:
            hits = trig_hits(c.route, f)
            if not any(not ok(c.route[i]) for i in hits) or not any(ok(c.route[i]) for i in hits):
                r.append(f"{f['id']}: not failed and then retried")
        return r
    nom_objs = {x for s in c.nominal for x in vals(s)}
    subst = [x for s in c.route if ok(s) and s["skill"] in set(ACH) | {"pick"} for x in vals(s)
             if x not in nom_objs and x in goal_entities(c.goal) | goal_entities(c.task["goal"])]
    subst += [s["args"].get(k) for s in c.route if ok(s) and s["skill"] in ("stir", "wipe", "cover")
              for k in ("tool", "lid") if s["args"].get(k) and s["args"][k] not in nom_objs]
    srch = [s for s in c.route if s["skill"] in SEARCH and s.get("role") in ("recover", "recovery", "alternative")]
    dec = set(c.v.get("decisions", [])) & {"explore", "alternative", "fallback"}
    if not (subst or srch or dec):
        r.append("no substitute, search recovery or v4 alternative decision")
    return r


CHECK = {"DR": check_DR, "GD": check_GD, "SR": check_SR, "CL": check_CL, "PP": check_PP, "AF": check_AF}


# ----------------------------------------------------------------- retry solvability
def retry_solvable(c: Ctx):
    """True when retrying the nominal plan would do: every failure is a transient action failure, and no
    task-level constraint, overlay difference, goal change or thermal override touches the nominal plan."""
    for fid, f in c.fails.items():
        if f["kind"] in ACTION_KINDS and not f.get("persist"):
            continue
        if f["kind"] in ACTION_KINDS:
            if trig_hits(c.nominal, f):
                return False
            continue
        ents = c.cause_ents(f"failure:{fid}")
        if c.nominal_hit(ents):
            return False
    for n in c.overlay_diff():
        if c.nominal_hit(c.cause_ents(f"overlay:{n}")):
            return False
    if c.goal != c.task["goal"] and not set(map(json.dumps, goal_atoms(c.goal))) <= \
            set(map(json.dumps, goal_atoms(c.task["goal"]))):
        return False
    if any(c.nominal_hit({n}) for n in (c.v.get("thermal_override") or {})):
        return False
    return True


# ----------------------------------------------------------------- proposals for the v5 variants
def propose(c: Ctx):
    """Structured hypotheses for a variant that declares none (the v5 ones): candidates read off the route,
    to be accepted or rejected by the same checks as declared ones."""
    hs = []
    route, nominal = c.route, c.nominal
    nom_manip = {x for s in nominal if s["skill"] in MANIP for x in vals(s)}
    subj = achieved_subjects(c.goal) & achieved_subjects(c.control_goal)
    causes = c.causes()
    # CL: persistent action failures
    for fid, f in c.fails.items():
        if f["kind"] not in ACTION_KINDS or not f.get("persist"):
            continue
        hits = trig_hits(route, f)
        bad = [i for i in hits if not ok(route[i])]
        last = max(bad) if bad else len(route)
        tail = route[last + 1:]
        nom_vals = {x for s in nominal for x in vals(s)}
        cand = None
        for s in tail:
            if ok(s) and s["skill"] == "pick" and s["args"]["object"] not in nom_vals:
                cand = ("object", s["args"]["object"])
                break
            if ok(s) and s["skill"] == "heat":
                cand = ("appliance", s["args"]["appliance"])
                break
            if ok(s) and s["skill"] in ACH and ACH[s["skill"]][1] and s["args"].get(ACH[s["skill"]][1]) not in nom_vals:
                cand = ("destination", s["args"][ACH[s["skill"]][1]])
                break
        if f.get("until_moved"):
            cand = ("subgoal", f["until_moved"])
        if cand:
            hs.append({"cap": "CL", "failure": fid, "change": cand[0], "to": cand[1]})
    # DR: an object outside the goal, untouched by the nominal plan, manipulated before a nominal step
    for i, s in enumerate(route):
        if not ok(s) or s["skill"] not in MANIP or s["skill"] in ("inspect",):
            continue
        for e in vals(s) - nom_manip - subj:
            if e in (c.task["variants"][c.vid].get("handle_objects") or []):
                pass
            if "/" in e or e in ("right", "left"):
                continue
            for k in range(i + 1, len(route)):
                st = route[k]
                if ok(st) and st["skill"] in MANIP and any(match(st, {"skill": n["skill"], "args": {}}) and
                                                           (vals(st) & vals(n) - {e}) for n in nominal if n["skill"] in MANIP):
                    tgt = sorted((vals(st) & {x for n in nominal for x in vals(n)}) - {e})
                    if tgt:
                        for cs in causes:
                            hs.append({"cap": "DR", "blocker": e, "blocked": {"skill": st["skill"], "target": tgt[0]},
                                       "cause": cs})
                    break
    # SR: the achieving procedure changes (skill, appliance, base, hands) for the same goal subject
    for n in nominal:
        if n["skill"] not in ACH:
            continue
        sa = ACH[n["skill"]][0]
        for o in route:
            if not ok(o) or o["skill"] not in ACH or o == n:
                continue
            swap = n["skill"] == o["skill"] == "stack" and o["args"].get("object") == n["args"].get("base") \
                and o["args"].get("base") == n["args"].get("object")
            same_subj = o["args"].get(ACH[o["skill"]][0]) == n["args"].get(sa)
            role = [k for k in ("appliance", "hands") if o["args"].get(k, DEFAULTS.get(k)) != n["args"].get(k, DEFAULTS.get(k))]
            if swap or (same_subj and (o["skill"] != n["skill"] and o["skill"] not in ("close", "inspect")) or
                        (same_subj and role)):
                keys = [k for k in n["args"] if k in ROLE_ARGS + ("object", "food", "base")]
                nproc = {"skill": n["skill"], "args": {k: n["args"][k] for k in keys}}
                okeys = [k for k in o["args"] if k in ROLE_ARGS + ("object", "food", "base")]
                rproc = {"skill": o["skill"], "args": {k: o["args"][k] for k in okeys}}
                for cs in causes:
                    hs.append({"cap": "SR", "nominal": nproc, "replacement": rproc, "cause": cs})
    # GD: inspection of several places; allocation over several receptacles
    places = []
    for s in route:
        if ok(s) and s["skill"] in INSPECT:
            p = s["args"].get("receptacle") or s["args"].get("furniture")
            if p and p not in places:
                places.append(p)
    if len(places) >= 2:
        for cs in causes:
            hs.append({"cap": "GD", "kind": "inspection", "places": places, "cause": cs})
    alloc = {}
    for s in route:
        if ok(s) and s["skill"] in ("place", "drop") and s["args"].get("object") in subj:
            rec = s["args"].get("receptacle") or s["args"].get("container")
            if rec and any(a[0] in ("inside", "fully_inside") and a[1] == s["args"]["object"] for a in goal_atoms(c.goal)):
                alloc[s["args"]["object"]] = rec
    if len(set(alloc.values())) >= 2:
        for cs in causes:
            hs.append({"cap": "GD", "kind": "allocation", "allocation": alloc, "cause": cs})
    # PP: an atom achieved before a dynamic event / persistent failure
    for fid, f in c.fails.items():
        t0 = c.onset(f"failure:{fid}")
        if t0 < 0:
            continue
        dyn = f["kind"] not in ACTION_KINDS
        for a in goal_atoms(c.goal):
            if a[0] not in SUBJ or a[0] == "is_closed":
                continue
            i = _achieves(route[:t0 + 1] if dyn else route[:t0], a)
            if i is not None:
                s = route[i]
                key = ACH[s["skill"]][0]
                hs.append({"cap": "PP", "kept": {"atom": a, "by": {"skill": s["skill"], "args": {key: s["args"][key]}}},
                           "event": fid})
    # AF
    if any(f["kind"] in ACTION_KINDS and not f.get("persist") for f in c.fails.values()):
        hs.append({"cap": "AF", "level": "local"})
    hs.append({"cap": "AF", "level": "task"})
    return hs


# ----------------------------------------------------------------- audit
def audit_variant(task, vid):
    c = Ctx(task, vid)
    declared = (c.v.get("v6") or {}).get("hypotheses")
    hyps = declared if declared is not None else propose(c)
    verified, rejected, evidence = [], [], {}
    for h in hyps:
        reasons = CHECK[h["cap"]](c, h)
        if reasons:
            rejected.append({**h, "reasons": reasons})
        else:
            if h["cap"] not in verified:
                verified.append(h["cap"])
            evidence.setdefault(h["cap"], h)
    rs = retry_solvable(c)
    core = [x for x in verified if x in CORE]
    adapt = bool(c.v.get("failures") or c.v.get("conditions") or
                 any(c.nominal_hit(c.cause_ents(f"overlay:{n}")) for n in c.overlay_diff()) or c.goal != task["goal"])
    tier = "hard" if core and not rs else "medium" if adapt or core else "easy"
    return {"source": "declared" if declared is not None else "proposed", "verified": sorted(verified),
            "core": sorted(core), "evidence": evidence,
            "rejected": rejected if declared is not None else [], "retry_solvable": rs, "tier_rule": tier,
            "control": c.control}


def apply_audit(doc):
    """Writes per task ``v6_audit`` (variant -> verdicts) and ``v6_formal`` (tier -> families).  A v6 family's
    tier is its design tier and must agree with the rule in every case (``problems`` otherwise); a v5 family
    takes the rule's tier (re-tiered when it disagrees with its v5 tier)."""
    for t in doc["tasks"]:
        aud, formal, problems = {}, {"easy": [], "medium": [], "hard": []}, []
        for fam, info in t["v6_families"].items():
            tiers = set()
            for vid in info["cases"]:
                a = audit_variant(t, vid)
                aud[vid] = a
                tiers.add(a["tier_rule"])
            if info["origin"] == "v6":
                tier = info["design_tier"]
                bad = [vid for vid in info["cases"] if aud[vid]["tier_rule"] != tier]
                if bad:
                    problems.append({"family": fam, "problem": f"design tier {tier}, rule gives "
                                     f"{ {v: aud[v]['tier_rule'] for v in bad} }",
                                     "rejected": {v: aud[v]["rejected"] for v in bad}})
                for vid in info["cases"]:
                    if aud[vid]["rejected"]:
                        problems.append({"family": fam, "variant": vid, "problem": "rejected hypotheses",
                                         "rejected": aud[vid]["rejected"]})
            else:
                tier = next(iter(tiers))
                info["v5_tier"] = info["design_tier"]
                if tier != info["design_tier"]:
                    info["retiered"] = f"{info['design_tier']} -> {tier}"
                v = t["variants"][fam]
                if tier == "hard":
                    from failure_injection.spec import category
                    cats = category(v.get("failures", []))
                    info["hard_category"] = (v.get("v5") or {}).get("hard_category") or \
                        ("mixed" if "mixed" in cats else "dynamic" if "dynamic" in cats else
                         "action" if cats == {"action"} else "task")
            info["tier"] = tier
            info["capabilities"] = sorted(set.intersection(*[set(aud[v]["verified"]) for v in info["cases"]]))
            formal[tier].append(fam)
        t["v6_audit"] = aud
        t["v6_formal"] = formal
        t["v6_design_problems"] = problems
    return doc
