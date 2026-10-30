"""v5 task suite: generated file, formal counts, Hard categories, static validity of all 1,800 episodes,
v3 configurations unchanged, hidden state.  No simulator.

    python -m pytest -q benchmark/v5/tests
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from benchmark.v5 import validate as V  # noqa: E402

DOC = V.load()


def test_file_is_generated_from_source():
    r = subprocess.run([sys.executable, str(ROOT / "benchmark/v5/define_tasks_v5.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_v3_file_untouched_by_v5():
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "benchmark/v3/tasks.json"], cwd=ROOT)
    assert r.returncode == 0


def test_twenty_tasks_nine_formal_variants_each():
    assert len(DOC["tasks"]) == 20
    for t in DOC["tasks"]:
        assert {k: len(v) for k, v in t["v5_formal"].items()} == {"easy": 2, "medium": 3, "hard": 4}
        cats = sorted(t["variants"][v]["v5"]["hard_category"] for v in t["v5_formal"]["hard"])
        assert cats == ["action", "dynamic", "mixed", "task"], (t["task_id"], cats)
    assert sum(1 for _ in V.formal(DOC)) == 180


@pytest.fixture(scope="module")
def static():
    return V.static(DOC)


def test_static_validation_of_1800_episodes(static):
    assert static["episodes"] == 1800 and static["variants"] == 180
    assert static["problems"] == [], static["problems"][:20]
    assert static["static_ok"] == 1800


def test_failure_coverage():
    from failure_injection.spec import mode
    kinds, modes = set(), set()
    for t, tier, vid in V.formal(DOC):
        for f in t["variants"][vid].get("failures", []):
            kinds.add(f["kind"])
            modes.add(mode(f))
    assert kinds == {"grasp", "slip", "placement", "ik", "capacity", "destination", "resource", "dependency"}
    assert modes == {"action", "initial", "dynamic"}


def test_classification_rules():
    assert V.classify({"crash": "x"}) == "crash"
    assert V.classify({"route_violations": ["x"], "task_success": True}) == "route_violation"
    fi = {"declared": ["a"], "fired": [], "manifested": [], "not_fired": ["a"], "log": []}
    assert V.classify({"failure_injection": fi, "task_success": True}) == "failure_not_triggered"
    fi = {"declared": ["a"], "fired": ["a"], "manifested": ["a"], "not_fired": [], "log": [{"id": "a", "manifested": True}]}
    assert V.classify({"failure_injection": fi, "task_success": True}) == "passed"
    assert V.classify({"task_success": False}) == "goal_failed"
    assert V.classify({"stopped_at": 3, "task_success": False}) == "stopped"
    assert V.classify({"stopped_at": 3, "failure_injection": fi}) == "stopped"


def test_configurations_frozen():
    """After the freeze only oracle routes may change: every episode's configuration hash is as frozen."""
    from benchmark.scene import episode_config
    frozen = json.loads((ROOT / "benchmark/v5/FREEZE.json").read_text())["episodes"]
    now = {}
    for t in DOC["tasks"]:
        for v in [x for ids in t["v5_formal"].values() for x in ids] + t.get("v5_study", []):
            for s in range(10, 20):
                now[f"{t['task_id']}/{v}/{s}"] = episode_config(t, s, v)["config_hash"]
    assert now == frozen


def test_skill_coverage_of_oracle_routes():
    used = {s["skill"] for t in DOC["tasks"] for ids in t["v5_formal"].values() for v in ids
            for s in t["routes"][t["oracle"][v]]["steps"]}
    assert len(used) >= 55, sorted(used)
