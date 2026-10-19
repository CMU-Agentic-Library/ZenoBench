"""Static checks of the v3 task registry, seed variation and evaluation matrix (no simulator).

    python -m pytest -q benchmark/tests/test_matrix.py
"""

from __future__ import annotations

import itertools
import json
import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmark"))
from benchmark import matrix  # noqa: E402
from benchmark.scene import config_hash, difficulty_of, episode_config  # noqa: E402

V2 = json.loads((ROOT / "benchmark/tasks.json").read_text())
V3 = json.loads((ROOT / "benchmark/v3/tasks.json").read_text())
SEEDS = list(range(10, 20))


def graded(doc):
    for t in doc["tasks"]:
        if t.get("kind") == "probe":
            continue
        for v, var in t["variants"].items():
            if difficulty_of(var) in ("easy", "medium", "hard"):
                yield t, v, var


def legacy_config(task, seed, variant):
    """scene.episode_config as of v2 (10b08a4), without the hash."""
    rng = random.Random(f"{task['task_id']}:{seed}")
    v = task["variants"][variant]
    scene = task["scene"]
    remove = list(scene.get("remove", [])) + list(v.get("remove", []))
    move = dict(scene.get("move", {}))
    move.update(v.get("move", {}))
    pool = [d for d in scene.get("distractors", []) if d not in remove and d not in move]
    k = rng.randint(0, len(pool)) if pool else 0
    dropped = sorted(rng.sample(pool, k)) if pool else []
    return {"task_id": task["task_id"], "seed": seed, "variant": variant, "variant_note": v.get("note", ""),
            "difficulty": difficulty_of(v), "conditions": list(v.get("conditions", [])),
            "base": scene["base"], "remove": sorted(set(remove) | set(dropped)), "distractors_removed": dropped,
            "move": move, "start": v.get("start", scene.get("start")),
            "thermal_sources": v.get("thermal_sources", scene.get("thermal_sources")),
            "thermal_override": v.get("thermal_override", {})}


def test_v2_configs_unchanged():
    for t in V2["tasks"]:
        for v in t["variants"]:
            for seed in (0, 1, 2, 3, 10, 11):
                cfg = episode_config(t, seed, v)
                assert {k: x for k, x in cfg.items() if k != "config_hash"} == legacy_config(t, seed, v)


def test_v3_file_is_generated_from_source():
    import define_tasks_v3
    tasks = define_tasks_v3.build()
    assert [t["task_id"] for t in tasks] == [t["task_id"] for t in V3["tasks"] if t.get("kind") != "probe"]
    assert json.loads(json.dumps(tasks)) == [t for t in V3["tasks"] if t.get("kind") != "probe"]


def test_config_deterministic_and_hashed():
    for t, v, _ in graded(V3):
        for seed in SEEDS:
            a, b = episode_config(t, seed, v), episode_config(t, seed, v)
            assert a == b
            assert a["config_hash"] == config_hash(a)


def test_hash_ignores_labels_only():
    t = next(t for t in V3["tasks"] if t["task_id"].startswith("T01"))
    cfg = episode_config(t, 10, "no_overhang")
    other = dict(cfg, seed=99, variant="x", task_id="y", variant_note="z")
    assert config_hash(other) == cfg["config_hash"]
    moved = json.loads(json.dumps(cfg))
    moved["move"]["paperback_book"]["xy"][0] += 0.01
    assert config_hash(moved) != cfg["config_hash"]


def test_tier_matches_condition_count():
    for t, v, var in graded(V3):
        n = len(var.get("conditions", []))
        assert difficulty_of(var) == {0: "easy", 1: "medium", 2: "hard"}[n], (t["task_id"], v)
        for c in var.get("conditions", []):
            assert c in V3["condition_registry"], (t["task_id"], v, c)
        assert len(var["condition_types"]) == n


def test_every_graded_variant_has_an_oracle_route_and_an_acceptance_route():
    for t, v, _ in graded(V3):
        r = t["oracle"].get(v)
        assert r in t["routes"] and v in t["routes"][r]["variants"], (t["task_id"], v)
        acc = [n for n, x in t["routes"].items() if v in x["variants"] and x["kind"] not in ("diagnostic", "negative")
               and not n.startswith("oracle")]
        assert acc, (t["task_id"], v)


def test_matrix_enumerates_every_variant_seed_and_planner():
    seeds, rows = matrix.enumerate_matrix(V3)
    assert seeds == SEEDS
    want = {(t["task_id"], v, s) for t in V3["tasks"] if t.get("kind") != "probe" for v in t["variants"] for s in SEEDS}
    assert {(r["task"], r["variant"], r["seed"]) for r in rows} == want
    jobs = matrix.eval_jobs(V3, seeds, accepted=None, policy="m:P")
    cells = {}
    for j in jobs:
        cells.setdefault((j["task"], j["variant"], j["seed"]), set()).add(j["planner"])
    assert set(cells) == {(t["task_id"], v, s) for t, v, _ in graded(V3) for s in SEEDS}
    assert all(p == {"fixed", "retry", "oracle", "recovery"} for p in cells.values())
    assert all("variant" in j and "difficulty" not in j for j in jobs)        # enumerated, never sampled


def test_eval_scope_follows_acceptance():
    seeds, _ = matrix.enumerate_matrix(V3)
    t = next(t for t in V3["tasks"] if t["task_id"].startswith("T01"))
    jobs = matrix.eval_jobs(V3, seeds, accepted={(t["task_id"], "no_overhang")})
    assert {(j["task"], j["variant"]) for j in jobs} == {(t["task_id"], "no_overhang")}
    assert len(jobs) == len(seeds) * len(matrix.PLANNERS)


def _check_groups(doc):
    for t, v, var in graded(doc):
        groups = (var.get("vary") or {}).get("groups", [])
        base = episode_config(t, SEEDS[0], v)["move"]
        for seed in SEEDS:
            mv = episode_config(t, seed, v)["move"]
            for g in groups:
                for a, b in itertools.combinations(g["names"], 2):
                    d0 = math.dist(base[a]["xy"], base[b]["xy"])
                    d1 = math.dist(mv[a]["xy"], mv[b]["xy"])
                    assert abs(d0 - d1) < 1e-6 or g.get("dyaw"), (t["task_id"], v, a, b)
                for n in g["names"]:
                    assert abs(mv[n]["xy"][0] - t["variants"][v].get("move", {}).get(n, t["scene"].get("move", {}).get(n))["xy"][0]) <= g["dx"] + 1e-9
                    assert abs(mv[n]["xy"][1] - t["variants"][v].get("move", {}).get(n, t["scene"].get("move", {}).get(n))["xy"][1]) <= g["dy"] + 1e-9


def test_vary_groups_keep_relative_geometry():
    _check_groups(V3)


@pytest.mark.parametrize("path", ["benchmark/v3/tasks.json"])
def test_layouts_clean(path, capsys):
    from benchmark import check_layouts
    sys.argv = ["check_layouts", "--tasks", str(ROOT / path)]
    check_layouts.main()
    assert "layout conflicts: 0" in capsys.readouterr().out


def test_conditions_counts_only_matching_configurations(tmp_path):
    from benchmark import conditions
    t = next(t for t in V3["tasks"] if t["task_id"].startswith("T01"))
    good = episode_config(t, 10, "no_overhang")["config_hash"]
    for seed, h, ok in ((10, good, True), (11, "0" * 12, True), (12, None, True), (13, None, False)):
        d = tmp_path / "runs" / t["task_id"] / f"s{seed}_no_overhang_fallback_expose"
        d.mkdir(parents=True)
        (d / "config.json").write_text(json.dumps({"config_hash": h, "code": {"commit": "abc", "diff_sha1": "def"}}))
        (d / "result.json").write_text(json.dumps({
            "task_id": t["task_id"], "seed": seed, "variant": "no_overhang", "planner": "scripted",
            "route": "fallback_expose", "task_success": ok, "calls": []}))
    sys.argv = ["conditions", "--runs", str(tmp_path / "runs"), "--tasks", str(ROOT / "benchmark/v3/tasks.json"),
                "--md", str(tmp_path / "r.md"), "--json", str(tmp_path / "c.json")]
    conditions.main()
    out = json.loads((tmp_path / "c.json").read_text())
    assert out["summary"]["episodes_run"] == 1 and out["summary"]["not_counted_runs"] == 3
    c = next(c for c in out["conditions"] if c["task"] == t["task_id"] and c["variant"] == "no_overhang")
    assert c["status"] == "preliminary"
