"""v6 catalog: generation, v5 preservation, seed manifests, Action-Level / Task-Level tracks."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from benchmark.scene import episode_config  # noqa: E402
from benchmark.v6.define_tasks_v6 import SEEDS, seed_cases  # noqa: E402

DOC = json.loads((ROOT / "benchmark/v6/tasks.json").read_text())
TASKS = {t["task_id"]: t for t in DOC["tasks"]}


def test_catalog_is_up_to_date():
    r = subprocess.run([sys.executable, "benchmark/v6/define_tasks_v6.py", "--check"], cwd=ROOT, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_v5_configurations_and_routes_unchanged():
    v5 = {t["task_id"]: t for t in json.loads((ROOT / "benchmark/v5/tasks.json").read_text())["tasks"]}
    frozen = json.loads((ROOT / "benchmark/v5/FREEZE.json").read_text())["episodes"]
    for tid, t in TASKS.items():
        for vid in [x for ids in v5[tid]["v5_formal"].values() for x in ids]:
            assert t["variants"][vid] == v5[tid]["variants"][vid]
            assert t["routes"][t["oracle"][vid]] == v5[tid]["routes"][v5[tid]["oracle"][vid]]
            for s in (10, 15, 19):
                assert episode_config(t, s, vid)["config_hash"] == frozen[f"{tid}/{vid}/{s}"]


def test_every_family_has_ten_reproducible_seeds():
    for tid, t in TASKS.items():
        for fam, info in t["v6_variants"].items():
            seeds = {int(k): v for k, v in info["seeds"].items()}
            assert sorted(seeds) == SEEDS
            if info["origin"] == "v6" or len(info["layouts"]) > 1:
                assert seeds == seed_cases(tid, fam, info["layouts"])
                c = Counter(seeds.values())
                assert set(c) == set(info["layouts"]) and max(c.values()) - min(c.values()) <= 1
            for s, v in list(seeds.items())[:2]:
                assert episode_config(t, s, v)["config_hash"] == episode_config(t, s, v)["config_hash"]


def test_cases_differ_in_decision():
    for t in TASKS.values():
        for fam, info in t["v6_variants"].items():
            if len(info["layouts"]) > 1:
                routes = {json.dumps(t["routes"][t["oracle"][v]]["steps"], sort_keys=True) for v in info["layouts"]}
                assert len(routes) == len(info["layouts"]), fam
                assert info.get("factor"), fam


def test_planner_view_is_clean():
    from episode.catalog import public_task
    from failure_injection.spec import public_view_is_clean
    for t in TASKS.values():
        for v in t["variants"]:
            assert public_view_is_clean(public_task(t, v)), v


def test_static_report_is_current_and_clean():
    import hashlib
    st = json.loads((ROOT / "benchmark/v6/STATIC.json").read_text())
    assert st["tasks_sha1"] == hashlib.sha1((ROOT / "benchmark/v6/tasks.json").read_bytes()).hexdigest()
    assert st["problems"] == [] and st["static_ok"] == st["episodes"] == 10 * st["variants"]


@pytest.mark.parametrize("tid", sorted(TASKS))
def test_every_new_family_has_a_control_in_the_task(tid):
    t = TASKS[tid]
    for fam, info in t["v6_variants"].items():
        if info["origin"] == "v6":
            assert info["control"] in t["variants"], fam


# ----------------------------------------------------------------- tracks (benchmark/v6/tracks.py)
def test_every_family_is_placed_in_its_tracks():
    from benchmark.v6.tracks import SUBCATEGORIES, content, transient
    for tid, t in TASKS.items():
        tr = t["v6_tracks"]
        merged = {m for x in tr["task"].values() for m in x.get("merged", [])}
        placed = set(tr["task"]) | set(tr["action"]) | set(tr["controls"]) | merged
        assert placed == set(t["v6_variants"]), tid
        assert not set(tr["controls"]) & (set(tr["task"]) | set(tr["action"])), tid
        for fam, x in tr["action"].items():
            assert x["sub"] in SUBCATEGORIES, (tid, fam)
            assert x["action_failures"] or x["local_conditions"], (tid, fam)
        for fam, x in tr["task"].items():
            for v in x["layouts"]:
                assert not any(transient(f) for f in t["variants"][v].get("failures") or []), (tid, fam, v)
        for fam in tr["controls"]:
            for v in t["v6_variants"][fam]["layouts"]:
                assert content(t, v) == (False, False), (tid, fam, v)
                assert not t["variants"][v].get("failures"), (tid, fam, v)


def test_the_split_reads_only_the_configuration():
    from benchmark.v6.tracks import content
    t = TASKS["T06_block_destination_occupied"]
    assert content(t, "x6_m_grasp_block_a") == (False, True)                    # one transient grasp miss
    assert content(t, "x6_cl_block_a_unholdable__b_island")[0]                 # the grasp fails every time
    t5 = TASKS["T05_pen_or_pencil_to_desk"]
    assert content(t5, "m_grasp_pencil") == (True, True)                         # no pen (substitute) + a slip


def test_a_local_grasp_repair_is_action_level():
    """pick! -> expose / separate -> pick of the same object: several policies, one action."""
    for tid, fam in (("T01_book_to_dining_table", "no_overhang"), ("T02_stack_blocks", "crowded"),
                     ("T14_shelve_the_book", "book_on_desk"), ("T17_hide_and_seek_block", "block_crowded")):
        tr = TASKS[tid]["v6_tracks"]
        assert tr["action"][fam]["sub"] == "AL-GRASP" and tr["action"][fam]["local_conditions"] in (["no_overhang"], ["crowded"])
        assert fam not in tr["task"], (tid, fam)
    # with task-level content next to it (a search, a lid), the family is in both tracks
    for tid, fam in (("T01_book_to_dining_table", "far_no_overhang"), ("T17_hide_and_seek_block", "lid_on_crowded")):
        tr = TASKS[tid]["v6_tracks"]
        assert fam in tr["action"] and fam in tr["task"], (tid, fam)


def test_projection_drops_only_transient_failures():
    from benchmark.v6.tracks import transient
    n = 0
    for tid, t in TASKS.items():
        for fam, x in t["v6_tracks"]["task"].items():
            for v in x["layouts"]:
                p = t["variants"][v].get("track_projection")
                if not p:
                    continue
                n += 1
                src = t["variants"][p["of"]]
                assert [f for f in src["failures"] if not transient(f)] == (t["variants"][v].get("failures") or [])
                assert set(p["dropped"]) == {f["id"] for f in src["failures"] if transient(f)}
                steps = t["routes"][t["oracle"][v]]["steps"]
                assert len(steps) < len(t["routes"][t["oracle"][p["of"]]]["steps"])
    assert n > 0


def test_track_batches_name_their_profile():
    for name, track, profile in (("track_task_scripted", "task", "sticky_snap/gt"),
                                 ("track_action_scripted", "action", "benchmark")):
        jobs = json.loads((ROOT / f"benchmark/v6/batches/{name}.json").read_text())
        assert jobs and all(j["eval_track"] == track and j["profile"] == profile for j in jobs)
        assert "track" not in jobs[0]          # --track is the skill track of run_episode
        assert len(jobs) == 10 * sum(len(t["v6_tracks"][track]) for t in TASKS.values())
