"""User rule (11-17, rechecked 11-20): the best a seed offers always scores 1.0 -- with only one way, or only
substitutes, the best of them is the top tier.  Every seed's reference route is replayed symbolically
(oracle_check.World) and scored with the seed's own tiers the way Episode.check does (the episode task carries
the layout's goal); atoms only geometry can decide count as holding."""
import json
from pathlib import Path

from benchmark.v6.oracle_check import World, trig_hits
from benchmark.v6.scoring import score

TASKS = Path(__file__).resolve().parents[1] / "tasks.json"


def _final_world(task, lid):
    w = World(task, lid, False)
    v = task["variants"][lid]
    steps = task["routes"][task["oracle"][lid]]["steps"]
    fires = {}
    for f in v.get("failures") or []:
        if f.get("when") == "dynamic" and f.get("event"):
            hits = trig_hits(steps, f)
            if hits:
                fires.setdefault(hits[0], []).append(f)
    for i, s in enumerate(steps):
        if s.get("expect") != "fail":
            w.step(i, s)
        for f in fires.get(i, []):
            w.event(f)
    return w


def _holds(w):
    def h(g):
        if any(w.holds(a) is False for a in g.get("all", [])):
            return False
        groups = g.get("any") or []
        return not groups or any(all(w.holds(a) is not False for a in grp) for grp in groups)
    return h


def test_every_seed_tops_at_one():
    bad = []
    for t in json.loads(TASKS.read_text())["tasks"]:
        for lid, v in t["variants"].items():
            s = v.get("scoring")
            if not s:
                continue
            if s["tiers"][0]["score"] != 1.0:
                bad.append((t["task_id"], lid, "top tier not 1.0"))
                continue
            got = score(s, {**t, "goal": v.get("goal") or t["goal"]}, lid, _holds(_final_world(t, lid)))
            if got["score"] != 1.0:
                bad.append((t["task_id"], lid, got["tier"], got["score"]))
    assert not bad, bad
