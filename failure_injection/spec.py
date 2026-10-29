"""Failure specs: taxonomy, validation, seeded parameters.  Standard library only.

A variant lists its failures under ``"failures"``.  Each failure is one of

* **action-level** (the skill's physical outcome is changed at a declared call):
  * ``grasp``     - the pick runs; the object then slips from the fingers before the lift is verified
                    (the hand opens, the object falls back onto its support); the pick reports ``not held``.
  * ``slip``      - the object is lost at the start of the carry: the next ``navigate`` while holding it
                    releases it over the support it was picked from and reports ``slipped out of the hand``.
  * ``placement`` - the place runs; the object then ends ``tipped`` (on its side, same spot) or
                    ``displaced`` to an authored landing pose (e.g. beside the bin); the call reports the
                    authored ``report`` atoms that no longer hold.
  * ``ik``        - the manipulation is refused before any motion with ``no IK solution from this base
                    pose`` and stays refused until the base is moved by a base skill (re-park).
* **task-level** (``capacity``, ``destination``, ``resource``, ``dependency``):
  * ``initial`` - the constraint is in the scene overlay (move / add / remove); ``check`` atoms must
                  hold at the start (the trigger is verified, nothing is changed at run time);
  * ``dynamic`` - an ``event`` fires after a declared call: ``move_object`` (someone put something
                  there / took the resource away), ``into`` (something was put into the container),
                  ``set_joint`` (someone closed the door again).
* **mixed / coupled**: a variant with action- and task-level failures; ``"after_fired": <id>``
  makes one fire only when another one fired (a coupled cascade).

Triggers count top-level calls deterministically: ``{"skill", "args": {subset}, "nth"}``; the
same call sequence gives the same failures, independent of wall time or physics noise.  Seeded
values (``seeded``) come from ``random.Random(f"{task}:{variant}:{seed}:{id}")``.
"""
from __future__ import annotations

import random

ACTION_KINDS = ("grasp", "slip", "placement", "ik")
TASK_KINDS = ("capacity", "destination", "resource", "dependency")
KINDS = ACTION_KINDS + TASK_KINDS
EVENTS = ("move_object", "into", "set_joint")
BASE_SKILLS = ("navigate", "approach", "retreat", "sidestep", "face", "reset")
PLACEMENT_MODES = ("tipped", "displaced")
# the skills each action-level failure attaches to
ACTION_SKILLS = {"grasp": ("pick",), "slip": ("navigate",), "placement": ("place", "drop", "stack"),
                 "ik": ("pick", "place", "open", "close", "drop", "stack", "press", "wipe", "uncover", "expose",
                        "separate", "push", "flip", "roll", "stir", "regrasp")}


class FailureSpecError(ValueError):
    pass


def level(f: dict) -> str:
    return "action" if f["kind"] in ACTION_KINDS else "task"


def mode(f: dict) -> str:
    """action | initial | dynamic"""
    if f["kind"] in ACTION_KINDS:
        return "action"
    return "initial" if f.get("when", "initial") == "initial" else "dynamic"


def category(failures: list[dict]) -> set[str]:
    """The Hard coverage categories a failure list exercises: action, task, mixed, dynamic."""
    levels = {level(f) for f in failures}
    out = set(levels)
    if levels == {"action", "task"}:
        out.add("mixed")
    if any(mode(f) == "dynamic" for f in failures):
        out.add("dynamic")
    return out


def validate(failures, where="failures", objects=None, articulated=None, supports=None) -> list[dict]:
    """Return the list unchanged or raise FailureSpecError listing every problem.  ``objects`` /
    ``articulated`` / ``supports``: names of the episode's scene (checked when given)."""
    errs = []
    if not isinstance(failures, list):
        raise FailureSpecError(f"{where}: must be a list")
    ids = [f.get("id") for f in failures]
    if len(set(ids)) != len(ids) or None in ids:
        errs.append(f"{where}: every failure needs a unique id ({ids})")

    def known(kind, name, pool, path):
        if pool is not None and name not in pool:
            errs.append(f"{path}: unknown {kind} {name!r}")

    for i, f in enumerate(failures):
        p = f"{where}[{i}]({f.get('id')})"
        k = f.get("kind")
        if k not in KINDS:
            errs.append(f"{p}: kind {k!r} not in {KINDS}")
            continue
        trig = f.get("trigger")
        if k in ACTION_KINDS or mode(f) == "dynamic":
            if not isinstance(trig, dict) or "skill" not in trig:
                errs.append(f"{p}: needs trigger {{skill, args?, nth?}}")
            else:
                if k in ACTION_KINDS and trig["skill"] not in ACTION_SKILLS[k]:
                    errs.append(f"{p}: a {k} failure attaches to {ACTION_SKILLS[k]}, not {trig['skill']!r}")
                if int(trig.get("nth", 1)) < 1:
                    errs.append(f"{p}: nth counts from 1")
                for v in (trig.get("args") or {}).values():
                    if isinstance(v, str) and objects is not None and "/" not in v and v not in objects \
                            and (articulated is None or v not in articulated):
                        errs.append(f"{p}: trigger names unknown {v!r}")
            if f.get("after_fired") is not None and f["after_fired"] not in ids:
                errs.append(f"{p}: after_fired names no failure of this variant")
        if k == "slip" and not (trig or {}).get("while_holding"):
            errs.append(f"{p}: slip needs trigger.while_holding")
        if k == "placement":
            m = f.get("mode")
            if m not in PLACEMENT_MODES:
                errs.append(f"{p}: placement mode must be one of {PLACEMENT_MODES}")
            if m == "displaced":
                to = f.get("to") or {}
                if not {"support", "xy"} <= set(to):
                    errs.append(f"{p}: displaced needs to {{support, xy, yaw_deg?}}")
                else:
                    known("support", to["support"], supports, p)
            if not f.get("report"):
                errs.append(f"{p}: placement needs report atoms (what the planner sees fail)")
        if k in TASK_KINDS:
            w = f.get("when", "initial")
            if w not in ("initial", "dynamic"):
                errs.append(f"{p}: when must be initial or dynamic")
            if w == "initial" and not f.get("check"):
                errs.append(f"{p}: an initial constraint needs check atoms (verified at the start)")
            if w == "dynamic":
                ev = f.get("event") or {}
                if ev.get("type") not in EVENTS:
                    errs.append(f"{p}: event.type must be one of {EVENTS}")
                elif ev["type"] in ("move_object", "into"):
                    known("object", ev.get("object"), objects, p)
                    if ev["type"] == "move_object":
                        to = ev.get("to") or {}
                        if not {"support", "xy"} <= set(to):
                            errs.append(f"{p}: move_object needs to {{support, xy, yaw_deg?}}")
                        else:
                            known("support", to["support"], supports, p)
                    else:
                        known("object", ev.get("container"), objects, p)
                elif ev["type"] == "set_joint":
                    known("articulated", ev.get("articulated"), articulated, p)
                    if ev.get("value") not in ("closed", "open") and not isinstance(ev.get("value"), (int, float)):
                        errs.append(f"{p}: set_joint value is closed, open or a number")
        for a in f.get("check", []) + f.get("report", []):
            if not (isinstance(a, list) and a and isinstance(a[0], str)):
                errs.append(f"{p}: atoms are [pred, arg, ...] lists")
    if errs:
        raise FailureSpecError("; ".join(errs))
    return failures


def seeded(f: dict, task_id: str, variant: str, seed: int) -> dict:
    """Seed-dependent values of one failure, resolved once per episode (recorded in the config).
    ``jitter``: {"xy": half_range_m} shifts a displaced landing / moved object on a 1 cm grid."""
    rng = random.Random(f"{task_id}:{variant}:{seed}:{f['id']}")
    out = {}
    j = (f.get("jitter") or {}).get("xy")
    if j:
        n = int(round(j / 0.01))
        out["dxy"] = [rng.randint(-n, n) * 0.01, rng.randint(-n, n) * 0.01]
    return out


def public_view_is_clean(obj) -> bool:
    """True when nothing failure-related appears in ``obj`` (what a planner receives)."""
    import json
    blob = json.dumps(obj, default=str).lower()
    return not any(w in blob for w in ('"failures"', "inject", "after_fired", "failure_log", "trigger"))
