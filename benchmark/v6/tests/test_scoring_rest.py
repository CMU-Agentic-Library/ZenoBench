"""Every v6 design is scored (T01-T09 with the user, T10-T30 from the precedents, scoring_rest.py), every tier goal
uses known predicates and objects of its layout (or ones the layout's own goal already names)."""
import json
from pathlib import Path

from benchmark.v6.scoring import NOT_OK_ZH, check_spec, tier_goal
from episode.goal_predicates import GOAL_PREDICATES
from zeno_skills.predicates import REGISTRY

ROOT = Path(__file__).resolve().parents[3]


def _objects(task, lid, cache={}):
    base = task["scene"]["base"]
    if base not in cache:
        a = json.loads((ROOT / base / "annotation.json").read_text())
        cache[base] = set(a["objects"]) if isinstance(a["objects"], dict) else {o["name"] for o in a["objects"]}
    v = task["variants"][lid]
    return (cache[base] - set(task["scene"].get("remove") or [])) | set(v.get("add") or {}) - set(v.get("remove") or [])


def _flat(g):
    return g.get("all", []) + [a for grp in g.get("any", []) for a in grp]


def _names(g):
    return {y for a in _flat(g) for x in a[1:] for y in (x if isinstance(x, list) else [x])
            if isinstance(y, str) and "/" not in y}


def test_every_design_scored_and_tiers_sound():
    doc = json.loads((ROOT / "benchmark/v6/tasks.json").read_text())
    for t in doc["tasks"]:
        for design, info in t["v6_variants"].items():
            sc = info.get("scoring")
            assert sc, (t["task_id"], design)
            assert not check_spec(sc), (t["task_id"], design, check_spec(sc))
            assert any(t["task_id"].startswith(k[0]) and k[1] == design for k in NOT_OK_ZH), (t["task_id"], design)
            for lid in info["layouts"]:
                own = t["variants"][lid].get("goal") or t["goal"]
                known = _objects(t, lid) | _names(own) | {"right", "left"}
                for tier in sc["tiers"]:
                    g = tier_goal(tier, dict(t, goal=own), lid)
                    for a in _flat(g):
                        p = a[0][4:] if a[0].startswith("not ") else a[0]
                        assert p in GOAL_PREDICATES or p in REGISTRY, (lid, tier["name"], p)
                    extra = {n for n in _names(g) - known if not n.startswith(("kitchen_", "breakfast_fridge", "trash"))}
                    assert not extra, (lid, tier["name"], extra)
