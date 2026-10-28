"""Episode profiles: which execution and observation features an episode runs with.

A profile is a YAML file merged over ``DEFAULTS``.  ``episode/profiles/`` has one folder per
sticky-hands level, each with a ``gt`` and a ``benchmark`` profile:

    physical/      no assist (sticky_hands: false); named by the file alone: gt, benchmark, oracle
    sticky/        held objects welded to the gripper while carried (carry): sticky/gt, sticky/benchmark
    sticky_snap/   carry + a failed pick / place snapped to success (snap): sticky_snap/gt, ...

Every key is checked: unknown keys, wrong types and combinations that leak GT state
to a gated planner are refused when the profile is loaded, not while an episode runs.

    execution    runner and rig switches (gate, automatic recovery, feedback masking ...)
    observation  the fields an observation carries
    evaluation   how check() turns the goal into success
    limits       contract call budget
    allow_leak   accept a gated profile that still shows GT state (debugging only)

No simulator imports: the HTTP server loads profiles with any Python 3 that has PyYAML.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import yaml

PROFILE_DIR = Path(__file__).resolve().parent / "profiles"
CAMERAS = ("head", "left_wrist", "right_wrist")
PHYSICAL_DIR = PROFILE_DIR / "physical"         # the default level: its profiles go by their bare name
TEMPERATURES = ("none", "observed", "all")
STICKY = (False, "carry", "snap")

# the defaults reproduce the GT interface env_service had before profiles existed
DEFAULTS = {
    "execution": {
        "gate": False,                    # object arguments must be observed; contact needs the object in view
        "nested_repair": False,           # repair fallback + one retry for a failed nested call of a composite skill
        "auto_recovery": True,            # policy-internal recovery: expose, door retry, pick -> push
        "slide_to_edge": True,            # the automatic slide-to-edge step inside pick (flat_edge path)
        "advisory": [],                   # feasibility predicates only recorded, the action is attempted
        "mask_feedback": False,           # names of never-observed objects -> <unobserved> in results
        "occlusion": False,               # dynamic occlusion in visibility tests
        "static_explore": False,          # explore covers the static layout only
        "edge_pinch_upright_waist": False,
        "sticky_hands": False,            # false | carry: weld while held | snap: carry + snap a failed pick / place
    },
    "observation": {
        "cameras": list(CAMERAS),
        "image_size": [480, 640],         # [height, width] of every robot camera
        "focal_length_mm": 10.0,          # 10: 92 x 76 deg at 640 x 480; shorter = wider
        "gt_objects": True,               # the task's entities with GT positions
        "visible_objects": False,
        "observation_cache": False,
        "known_places": False,
        "robot": {"base_pose": True, "held": True, "room": False, "temperatures": "none"},
        "task_status": True,              # every goal clause, true or false now
        "last_result": False,             # the previous contract result, repeated
    },
    "evaluation": {
        "drops_fail": False,              # a watched object that ended on the floor fails the task
    },
    "limits": {
        "max_calls": 40,                  # an int, or "task": the task's max_calls (default 60)
    },
    "allow_leak": False,
}
TASK_DEFAULT_MAX_CALLS = 60


class ProfileError(ValueError):
    pass


def resolve_path(spec) -> Path:
    """A profile name (``benchmark``: physical/, ``sticky/gt``) or a path to a YAML file."""
    p = Path(spec)
    if p.suffix in (".yaml", ".yml") or p.is_file():
        return p
    if "/" not in str(spec):
        return PHYSICAL_DIR / f"{spec}.yaml"
    return PROFILE_DIR / f"{spec}.yaml"


def profile_name(path: Path) -> str:
    """``gt`` for physical/gt.yaml, ``sticky/gt`` for sticky/gt.yaml, the stem for any other file."""
    path = path.resolve()
    if path.parent == PHYSICAL_DIR:
        return path.stem
    if path.parent.parent == PROFILE_DIR:
        return f"{path.parent.name}/{path.stem}"
    return path.stem


def load_profile(spec) -> dict:
    path = resolve_path(spec)
    if not path.exists():
        raise ProfileError(f"no profile {spec!r} ({path})")
    raw = yaml.safe_load(path.read_text()) or {}
    prof = _merge(DEFAULTS, raw, ())
    prof.pop("name", None)
    _validate(prof)
    prof = {"name": raw.get("name") or profile_name(path), **prof}
    prof["hash"] = profile_hash(prof)
    return prof


def _merge(base, over, where):
    if not isinstance(over, dict):
        raise ProfileError(f"{'.'.join(where) or 'profile'}: expected a mapping")
    out = copy.deepcopy(base)
    for k, v in over.items():
        if k == "name" and not where:
            out[k] = v
            continue
        if k not in base:
            raise ProfileError(f"unknown key {'.'.join(where + (k,))}")
        out[k] = _merge(base[k], v, where + (k,)) if isinstance(base[k], dict) else v
    return out


def _validate(p):
    ex, ob = p["execution"], p["observation"]
    for sect in ("execution", "observation", "evaluation"):
        for k, v in p[sect].items():
            if isinstance(DEFAULTS[sect][k], bool) and not isinstance(v, bool) and k != "sticky_hands":
                raise ProfileError(f"{sect}.{k}: expected true/false, got {v!r}")
    for k, v in ob["robot"].items():
        if k != "temperatures" and not isinstance(v, bool):
            raise ProfileError(f"observation.robot.{k}: expected true/false, got {v!r}")
    if ob["robot"]["temperatures"] is False:          # YAML reads a bare `off` / `no` as false
        ob["robot"]["temperatures"] = "none"
    if ob["robot"]["temperatures"] not in TEMPERATURES:
        raise ProfileError(f"observation.robot.temperatures: one of {TEMPERATURES}")
    if not isinstance(ob["cameras"], list) or not set(ob["cameras"]) <= set(CAMERAS):
        raise ProfileError(f"observation.cameras: a list of {CAMERAS}")
    size = ob["image_size"]
    if not (isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) and v > 0 for v in size)):
        raise ProfileError("observation.image_size: [height, width] in pixels")
    if isinstance(ob["focal_length_mm"], bool) or not isinstance(ob["focal_length_mm"], (int, float)) \
            or ob["focal_length_mm"] <= 0:
        raise ProfileError("observation.focal_length_mm: a positive number")
    if not isinstance(ex["advisory"], list):
        raise ProfileError("execution.advisory: a list of predicate names")
    mc = p["limits"]["max_calls"]
    if mc != "task" and (isinstance(mc, bool) or not isinstance(mc, int) or mc <= 0):
        raise ProfileError('limits.max_calls: a positive int or "task"')
    if not isinstance(p["allow_leak"], bool):
        raise ProfileError("allow_leak: expected true/false")
    if ex["sticky_hands"] is not False and ex["sticky_hands"] not in STICKY[1:]:
        raise ProfileError('execution.sticky_hands: false, "carry" or "snap"')
    if ex["gate"] and not p["allow_leak"]:
        leaks = [k for k, on in (("observation.gt_objects", ob["gt_objects"]),
                                 ("observation.task_status", ob["task_status"]),
                                 ('observation.robot.temperatures: "all"', ob["robot"]["temperatures"] == "all"),
                                 ("execution.mask_feedback: false", not ex["mask_feedback"])) if on]
        if leaks:
            raise ProfileError("execution.gate hides unobserved objects, but " + ", ".join(leaks) +
                               " shows them; set allow_leak: true to run it anyway")


def profile_hash(prof) -> str:
    """Hash of everything that changes an episode (not the profile's name)."""
    body = {k: v for k, v in prof.items() if k not in ("name", "hash")}
    return hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]


def needs_observer(prof) -> bool:
    """An observation cache is kept when anything reads it."""
    ex, ob = prof["execution"], prof["observation"]
    return bool(ex["gate"] or ex["mask_feedback"] or ob["visible_objects"] or ob["observation_cache"]
                or ob["robot"]["temperatures"] == "observed")


def max_calls(prof, task) -> int:
    mc = prof["limits"]["max_calls"]
    return int(task.get("max_calls", TASK_DEFAULT_MAX_CALLS)) if mc == "task" else int(mc)


def observation_fields(prof) -> list[str]:
    """The top-level observation fields a profile turns on (what a planner should expect)."""
    ob = prof["observation"]
    out = ["images"] if ob["cameras"] else []
    out += [k for k in ("gt_objects", "visible_objects", "observation_cache", "known_places")
            if ob[k]]
    out = ["objects" if k == "gt_objects" else k for k in out]
    if any(v not in (False, "none") for v in ob["robot"].values()):
        out.append("robot")
    out += [k for k in ("task_status", "last_result") if ob[k]]
    return out


def apply_rig_flags(rig, prof):
    """Rig switches read by the policies and the perception code."""
    ex = prof["execution"]
    rig.auto_recovery = ex["auto_recovery"]
    rig.occlusion = ex["occlusion"]
    rig.static_explore = ex["static_explore"]
    rig.edge_pinch_upright_waist = ex["edge_pinch_upright_waist"]
    rig.sticky = None
    if ex["sticky_hands"]:
        from zeno_skills.sticky import StickyHands
        rig.sticky = StickyHands(rig, snap=ex["sticky_hands"] == "snap")


def run_profile_current(cfg: dict) -> bool:
    """A run directory's config.json still matches its profile: the profile it names hashes
    to the recorded value today.  Runs from before profiles existed carry none and count."""
    if not cfg.get("profile_hash"):
        return True
    try:
        return load_profile(cfg.get("profile") or "").get("hash") == cfg["profile_hash"]
    except (ProfileError, OSError):
        return False
