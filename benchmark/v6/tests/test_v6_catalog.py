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
    """v5 variants keep their configuration, except the injected action failures removed (or the variant dropped)."""
    v5 = {t["task_id"]: t for t in json.loads((ROOT / "benchmark/v5/tasks.json").read_text())["tasks"]}
    frozen = json.loads((ROOT / "benchmark/v5/FREEZE.json").read_text())["episodes"]
    for tid, t in TASKS.items():
        for vid in [x for ids in v5[tid]["v5_formal"].values() for x in ids]:
            if vid in t["v6_dropped"]:
                assert vid not in t["variants"]
                continue
            if "conditions_ignored" in t["variants"][vid]:
                continue
            if "injected_removed" in t["variants"][vid]:
                old = v5[tid]["variants"][vid]
                assert sorted(f["id"] for f in old.get("failures", []) if f["id"] not in
                              t["variants"][vid]["injected_removed"]) == \
                    sorted(f["id"] for f in t["variants"][vid].get("failures", []))
                continue
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
def test_every_variant_has_its_category():
    from benchmark.v6.tracks import ORDER, category, content, injected
    for tid, t in TASKS.items():
        assert set(t["v6_tracks"]) == set(t["v6_variants"]), tid
        for vid, info in t["v6_variants"].items():
            local, longer = set(), set()
            for lid in info["layouts"]:
                assert not any(injected(f) for f in t["variants"][lid].get("failures") or []), (tid, lid)
                a, b = content(t, lid)
                local |= set(a)
                longer |= set(b)
            assert t["v6_tracks"][vid]["category"] == category(local, longer) in ORDER, (tid, vid)


def test_local_fallbacks_are_action_level():
    """A few skills at the work spot: expose / separate before the pick, the lid off, the object on the book."""
    cat = lambda tid, vid: TASKS[tid]["v6_tracks"][vid]["category"]  # noqa: E731
    for tid, vid in (("T01_book_to_dining_table", "no_overhang"), ("T02_stack_blocks", "crowded"),
                     ("T09_tomato_soup", "lid_on"), ("T01_book_to_dining_table", "x6_dr_block_on_book__block"),
                     ("T15_book_face_up", "h_task_block_on_book")):
        assert cat(tid, vid) == "action", (tid, vid)
    # a search next to the local fallback: both
    assert cat("T01_book_to_dining_table", "far_no_overhang") == "action_task"
    # a substitute, never a local fallback: Task-Level
    assert cat("T04_cup_or_mug_to_cabinet", "no_cup") == "task"


def test_no_injected_action_failure_anywhere():
    """No IK refusal, grasp miss, slip or placement miss is forced on any call, once or every time."""
    for tid, t in TASKS.items():
        for vid, v in t["variants"].items():
            assert not [f for f in v.get("failures") or [] if f["kind"] in ("ik", "grasp", "slip", "placement")], \
                (tid, vid)
    src = (ROOT / "benchmark/v6/define_tasks_v6.py").read_text()
    for helper in ("f_ik(", "f_grasp(", "f_slip(", "with_ik(", "with_grasp(", "with_slip(", "persist"):
        assert helper not in src, helper


def test_events_put_right_at_the_work_spot_are_action_level():
    cat = lambda tid, vid: TASKS[tid]["v6_tracks"][vid]["category"]  # noqa: E731
    for tid, vid in (("T09_tomato_soup", "x6_pp_tomato_taken_out__tomato1"), ("T16_rolling_pin_at_edge",
                     "h_dynamic_bowl_put_behind"), ("T18_check_cabinet_dishes", "x6_pp_door_reopened"),
                     ("T13_breakfast_setup", "x6_pp_spoon_moved__table_end")):
        assert cat(tid, vid) == "action", (tid, vid)
    # taken to another room: searched for, Task-Level
    assert cat("T13_breakfast_setup", "x6_pp_spoon_moved__tv_stand") == "task"
    assert cat("T12_tidy_toys", "x6_pp_duck_moved") == "task"


def test_injected_only_variants_are_dropped():
    t = TASKS["T01_book_to_dining_table"]
    assert t["v6_dropped"]["m_ik_pick"] == "only injected action failures"
    t = TASKS["T15_book_face_up"]
    assert t["v6_dropped"]["h_mixed_block_on_book_ik"].startswith("same as h_task_block_on_book")
    for tid, t in TASKS.items():
        for info in t["v6_variants"].values():
            assert info["control"] is None or info["control"] in t["variants"], tid


def test_category_batches_name_their_profile():
    from benchmark.v6.tracks import CATEGORIES
    for k, cfg in CATEGORIES.items():
        jobs = json.loads((ROOT / f"benchmark/v6/batches/category_{k}.json").read_text())
        assert jobs and all(j["category"] == k and j["profile"] == cfg["profile"] for j in jobs)
        assert len(jobs) == 10 * sum(x["category"] == k for t in TASKS.values() for x in t["v6_tracks"].values())
