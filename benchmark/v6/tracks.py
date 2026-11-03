"""Four categories of v6 variants: control, Action-Level, Task-Level, Action + Task.

* **Action-Level** (``action``): a short fallback at the work spot - a few skills combined, then the task goes
  on as planned.  The scene makes it necessary (``LOCAL_CONDITIONS`` / ``local_failure``): a flat book pushed
  over the edge before the pick, a crowded block pulled apart, the pot lid taken off, an object lying on the
  target or a closed door opened first, clutter moved aside before wiping, a full destination cleared; or a
  dynamic event put right where the robot works (``event_is_local``: a book pushed back, a tomato taken out of the
  pot, a door opened again).  No injected action failure.
* **Task-Level** (``task``): the plan itself changes over a longer horizon - an absent object and its substitute,
  a search in another place or room, a capacity split, another destination / appliance / cookware, an object an
  event takes elsewhere.
* **Action + Task** (``action_task``): both in one variant.
* **Control** (``control``): neither; the nominal plan works.

Injected action failures (an IK refusal, a grasp miss, a slip or a placement miss forced on a call, once or every
time) are not part of the design anywhere: ``strip_injected`` removes them from every layout and, in its route,
each call they failed with the repair up to the successful retry.  A variant built on a failure that never goes
away is dropped, one left with nothing is dropped, one left equal to another variant is merged into it
(``v6_dropped`` per task says which and why).

    python benchmark/v6/tracks.py          # TRACKS.md and one batch per category (tasks.json must be current)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmark.v6.routes import ACTION_KINDS, trig_hits  # noqa: E402

CATEGORIES = {
    "control": {"title": "Control", "profile": "benchmark",
                "measures": "the nominal plan works: the reference for the other categories"},
    "action": {"title": "Action-Level", "profile": "benchmark",
               "measures": "a short fallback at the work spot: a few skills combined, then the plan goes on"},
    "task": {"title": "Task-Level", "profile": "sticky_snap/gt",
             "measures": "the plan changes over a longer horizon (substitute, search, split, another place or "
                         "procedure, a dynamic event)"},
    "action_task": {"title": "Action + Task", "profile": "benchmark",
                    "measures": "both a short fallback at the work spot and a longer-horizon change of plan"},
}
ORDER = ("control", "action", "task", "action_task")

# scene conditions whose fallback is a few skills at the work spot -> what the robot does
LOCAL_CONDITIONS = {
    "no_overhang": "expose the flat object over the edge, then pick it",
    "crowded": "separate the crowded object, then pick it",
    "lid_on": "take the lid off, then put in",
    "state_differs": "deal with the state as found (e.g. close the door left open)",
    "surface_cluttered": "move the objects off the work strip, work, put them back",
    "anchor_boxed_in": "move the boxed-in anchor to where the setting fits",
    "destination_full": "move what fills the destination to a legal place, then place",
    "unstable_base": "move the base in from the edge (or stack on the other one)",
}


# designs the rules above cannot tell apart: (task, variant) -> the variant it is the same design as
SAME_DESIGN = {
    # its extra dependency only states that block A stands on the island, i.e. the unstable_base condition
    ("T02_stack_blocks", "h_action_grasp_and_ik"): "edge_base",
    ("T02_stack_blocks", "h_mixed_edge_base_grasp"): "edge_base",
}


def injected(f):
    """An injected action failure: an IK refusal, a grasp miss, a slip or a placement miss forced on a call, once
    or every time (``persist``, ``until_moved``).  None is part of the design."""
    return f["kind"] in ACTION_KINDS


def declares_condition(v, f):
    """An initial resource / destination / capacity failure next to a scene condition only states that condition
    as checkable facts (the v5 Hards carry both): it is not a challenge of its own."""
    return bool(v.get("conditions")) and f.get("when", "initial") == "initial" and \
        f["kind"] in ("resource", "destination", "capacity")


def local_failure(f):
    """A declared scene fact handled at the work spot: something on / in front of the target or a closed door at
    the start, or a reach blocked until an object in front is moved."""
    if f["kind"] == "dependency" and f.get("when", "initial") == "initial":
        return "clear the object on the target / open the door first"
    return None


SEARCH = ("search", "explore_room", "explore_furniture")
PLACE_SKILLS = ("navigate", "open", "inspect", "explore_furniture")


@lru_cache(maxsize=None)
def _objects(base):
    return {o["name"]: o for o in json.loads((ROOT / base / "annotation.json").read_text())["objects"]}


def _furniture(task, lid, name):
    """The piece of furniture an object stands on (or a place / support name belongs to)."""
    v = task["variants"][lid]
    for src in (v.get("move", {}), v.get("add", {}), task["scene"].get("move", {})):
        if name in src and src[name].get("support"):
            return src[name]["support"].split("/")[0]
    for f in v.get("failures") or []:                     # an object an event brings in
        ev = f.get("event") or {}
        if ev.get("object") == name and (ev.get("to") or {}).get("support"):
            return ev["to"]["support"].split("/")[0]
    o = _objects(task["scene"]["base"]).get(name)
    return (o.get("support") or name).split("/")[0] if o else str(name).split("/")[0]


def _places(task, lid, steps):
    out = set()
    for s in steps:
        a = s["args"]
        n = a.get("destination") or a.get("target") or a.get("articulated") or a.get("furniture")
        if s["skill"] in PLACE_SKILLS and n:
            out.add(_furniture(task, lid, n))
    return out


def _control(task):
    return next((info["layouts"][0] for vid, info in task["v6_variants"].items()
                 if all(not a and not b for a, b in (_content(task, x, False) for x in info["layouts"]))), None)


def event_is_local(task, lid, f):
    """A dynamic event the robot repairs where it works anyway: a door opened / closed again, or an object moved
    to a place the robot works at (a book pushed back, a tomato taken out of the pot, a bowl pushed into the
    path), with no search for it and no new place afterwards.  An object taken elsewhere (searched for), or a
    repair at another place (another display, the stove, another cabinet) is a longer-horizon change."""
    ev = f.get("event") or {}
    if ev.get("type") == "set_joint":
        return True
    steps = task["routes"][task["oracle"][lid]]["steps"]
    hits = trig_hits(steps, f)
    if not hits or ev.get("type") != "move_object":
        return False
    i = hits[0]
    after = steps[i + 1:]
    if any(s["skill"] in SEARCH and s["args"].get("object") in (ev.get("object"), None) for s in after):
        return False
    ctl = _control(task)
    known = _places(task, lid, steps[:i + 1]) | (_places(task, ctl, task["routes"][task["oracle"][ctl]]["steps"])
                                                if ctl else set())
    to = (ev.get("to") or {}).get("support") or (ev.get("onto") and _furniture(task, lid, ev["onto"]))
    return bool(to) and to.split("/")[0] in known and not (_places(task, lid, after) - known)


def content(task, lid):
    return _content(task, lid, True)


def _content(task, lid, events=True):
    """``(local, longer)``: why one layout is Action-Level / Task-Level (lists of reasons)."""
    v = task["variants"][lid]
    local, longer = [], []
    for f in v.get("failures") or []:
        if injected(f) or declares_condition(v, f):
            continue
        why = local_failure(f)
        if why:
            local.append(why)
        elif f.get("when") == "dynamic":
            if events and event_is_local(task, lid, f):
                local.append("someone changed things at the work spot: put it right there")
            else:
                longer.append(f"event: {f['kind']}")
        else:
            longer.append(f"{f['kind']}")
    for c in v.get("conditions") or []:
        (local if c in LOCAL_CONDITIONS else longer).append(LOCAL_CONDITIONS.get(c, c))
    # a goal of its own (close the door again, leave the block on the island) states how the fallback ends;
    # it is not a change of plan by itself
    return sorted(set(local)), sorted(set(longer))


def category(local, longer):
    return {(False, False): "control", (True, False): "action", (False, True): "task",
            (True, True): "action_task"}[(bool(local), bool(longer))]


def project_route(steps, drop):
    """The route without the calls the dropped failures make fail: each such call and the repair after it, up
    to the next call of the same skill with the same arguments (its retry), which stays."""
    hit = sorted({i for f in drop for i in trig_hits(steps, f) if steps[i].get("expect") == "fail"})
    out, skip_to = [], -1
    for i, s in enumerate(steps):
        if i < skip_to:
            continue
        if i in hit:
            j = next((k for k in range(i + 1, len(steps)) if steps[k]["skill"] == s["skill"] and
                      steps[k]["args"] == s["args"] and steps[k].get("expect") != "fail"), i + 1)
            skip_to = j
            continue
        out.append(s)
    return out


OBJECT_ARGS = ("object", "objects", "food", "tool", "lid")
# calls that only polish or check a route (steady the pot, line things up, show, measure): not the design
AUXILIARY = ("arrange", "brace", "release", "present", "square", "press", "wait", "lower", "lift", "hover", "crouch",
             "stand", "nod", "wave", "point", "shake", "regrasp", "center", "measure", "count", "identify", "touch",
             "rotate")


def design_key(task, lid):
    """What a layout asks of the robot, without where things stand or where it starts (the seed's part) and
    without how a route words it: its conditions, failures (kind, timing, trigger, event), goal, instruction and
    the objects the route handles (which object is cleared, which substitute is used)."""
    v = task["variants"][lid]
    fails = sorted(json.dumps({k: f.get(k) for k in ("kind", "persist", "until_moved", "when", "trigger", "event")},
                              sort_keys=True) for f in v.get("failures") or [] if not declares_condition(v, f))
    handled = set()
    for s in task["routes"][task["oracle"][lid]]["steps"]:
        if s.get("expect") == "fail" or s["skill"] in AUXILIARY:
            continue
        for k in OBJECT_ARGS:
            x = s["args"].get(k)
            handled |= set(x) if isinstance(x, list) else {x} if isinstance(x, str) else set()
    return json.dumps([sorted(v.get("conditions") or []), fails, v.get("goal"), v.get("instruction"),
                       sorted(handled)], sort_keys=True)


def strip_injected(doc):
    """Remove injected transient action failures from every layout; drop / merge what is left empty or equal."""
    for t in doc["tasks"]:
        dropped, changed = {}, set()
        for vid, info in t["v6_variants"].items():
            for lid in info["layouts"]:
                v = t["variants"][lid]
                drop = [f for f in v.get("failures") or [] if injected(f)]
                if not drop:
                    continue
                changed.add(vid)
                if any(f.get("persist") for f in drop):
                    # the route works around a failure that never goes away (another object, procedure or
                    # place); without it the design has no reason to exist
                    dropped[vid] = "built on an injected action failure that never goes away"
                rname = t["oracle"][lid]
                t["routes"][rname] = dict(t["routes"][rname],
                                          steps=project_route(t["routes"][rname]["steps"], drop))
                keep = [f for f in v["failures"] if not injected(f)]
                if keep:
                    v["failures"] = keep
                else:
                    v.pop("failures")
                v["injected_removed"] = [f["id"] for f in drop]
        # one design, one variant: unchanged variants first, so a stripped one merges into the original design
        seen = {}
        for vid in sorted(t["v6_variants"], key=lambda x: x in changed):
            if vid in dropped:
                continue
            info = t["v6_variants"][vid]
            kinds = [content(t, lid) for lid in info["layouts"]]
            if vid in changed and not any(a or b for a, b in kinds):
                dropped[vid] = "only injected action failures"
                continue
            same = SAME_DESIGN.get((t["task_id"], vid))
            if same in t["v6_variants"]:
                dropped[vid] = f"same as {same} (SAME_DESIGN)"
                continue
            key = tuple(sorted(design_key(t, lid) for lid in info["layouts"]))
            if key in seen:
                dropped[vid] = f"same as {seen[key]}" + (" without its injected action failures" if vid in changed
                                                         else " but for the layout (object poses / start)")
                continue
            seen[key] = vid
        controls = [vid for vid in t["v6_variants"] if vid not in dropped and
                    all(not a and not b for a, b in (content(t, lid) for lid in t["v6_variants"][vid]["layouts"]))]
        for vid in dropped:
            for lid in t["v6_variants"].pop(vid)["layouts"]:
                t["variants"].pop(lid, None)
                t["routes"].pop(t["oracle"].pop(lid, None), None)
        for vid, info in t["v6_variants"].items():
            c = info.get("control")
            while c in dropped and dropped[c].startswith("same as "):
                c = dropped[c][len("same as "):].split(" ")[0]
            if c in dropped or (c is not None and c not in t["variants"]):
                c = controls[0] if controls and controls[0] != vid else None
            info["control"] = c
        t["v6_dropped"] = dropped
        # configurations no variant uses (v5's study / supplementary ones) are not part of v6
        used = {lid for info in t["v6_variants"].values() for lid in info["layouts"]}
        for lid in [x for x in t["variants"] if x not in used]:
            t["variants"].pop(lid)
            t["oracle"].pop(lid, None)
        keep = set(t["oracle"].values()) | {t.get("nominal")}
        for r in [r for r in t["routes"] if r not in keep]:
            t["routes"].pop(r)
    return doc


def apply_tracks(doc):
    """Per task ``v6_tracks``: variant -> {category, local, longer}; doc-level ``categories``."""
    doc["categories"] = CATEGORIES
    for t in doc["tasks"]:
        out = {}
        for vid, info in t["v6_variants"].items():
            local, longer = set(), set()
            for lid in info["layouts"]:
                a, b = content(t, lid)
                local |= set(a)
                longer |= set(b)
            out[vid] = {"category": category(local, longer), "local": sorted(local), "longer": sorted(longer)}
        t["v6_tracks"] = out
    return doc


def short(tid):
    return tid.split("_")[0]


def report(doc):
    """TRACKS.md (definitions, counts per task, every variant) and batches/category_<name>.json (oracle routes)."""
    out = ROOT / "benchmark/v6"
    tasks = doc["tasks"]
    n = Counter(x["category"] for t in tasks for x in t["v6_tracks"].values())
    md = ["# ZenoBench v6 categories", "",
          "Generated by `python benchmark/v6/tracks.py` from `tasks.json` (`v6_tracks` per task).  A variant is "
          "one task design; its ten seeds (10-19) vary the layout.  Static only: physics status is in "
          "`PHYSICS_TODO.md`.", "",
          "| category | what the variant needs | variants | episodes |", "|---|---|---|---|"]
    for k in ORDER:
        md.append(f"| {CATEGORIES[k]['title']} | {CATEGORIES[k]['measures']} | {n[k]} | {10 * n[k]} |")
    md += ["", "Variants per task:", "", "| category | " + " | ".join(short(t["task_id"]) for t in tasks) + " |",
           "|---|" + "---|" * len(tasks)]
    for k in ORDER:
        md.append(f"| {CATEGORIES[k]['title']} | " + " | ".join(
            str(sum(x["category"] == k for x in t["v6_tracks"].values()) or "") for t in tasks) + " |")
    n_drop = Counter(r.split(" ")[0] for t in tasks for r in t["v6_dropped"].values())
    md += ["", f"Removed with the injected action failures: {sum(n_drop.values())} variants "
           f"({n_drop.get('only', 0)} had nothing else, {n_drop.get('same', 0)} equal another variant without them; "
           "`v6_dropped` per task).", "", "## Variants", "",
           "| task | variant | category | local fallback | longer-horizon change | layouts |", "|---|---|---|---|---|---|"]
    for t in tasks:
        for k in ORDER:
            for vid, x in t["v6_tracks"].items():
                if x["category"] == k:
                    md.append(f"| {short(t['task_id'])} | {vid} | {CATEGORIES[k]['title']} | {'; '.join(x['local']) or '-'} | "
                              f"{'; '.join(x['longer']) or '-'} | {len(t['v6_variants'][vid]['layouts'])} |")
    (out / "TRACKS.md").write_text("\n".join(md) + "\n")
    (out / "batches").mkdir(exist_ok=True)
    for old in ("track_task_scripted.json", "track_action_scripted.json"):
        (out / "batches" / old).unlink(missing_ok=True)
    jobs = {}
    for k in ORDER:
        jobs[k] = [{"task": t["task_id"], "seed": int(s), "variant": lid, "route": t["oracle"][lid],
                    "planner": "scripted", "profile": CATEGORIES[k]["profile"], "category": k, "v6_variant": vid}
                   for t in tasks for vid, x in t["v6_tracks"].items() if x["category"] == k
                   for s, lid in sorted(t["v6_variants"][vid]["seeds"].items(), key=lambda kv: int(kv[0]))]
        (out / f"batches/category_{k}.json").write_text(json.dumps(jobs[k], indent=0))
    return n, jobs


def main():
    doc = json.loads((ROOT / "benchmark/v6/tasks.json").read_text())
    n, jobs = report(doc)
    print({k: n[k] for k in ORDER}, "episodes:", {k: len(v) for k, v in jobs.items()},
          "-> TRACKS.md, batches/category_*.json")


if __name__ == "__main__":
    main()
