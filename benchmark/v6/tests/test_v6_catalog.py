"""v6 catalog: generation, v5 preservation, tier rule, capability targets, seed manifests, checker negatives."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from benchmark.scene import episode_config  # noqa: E402
from benchmark.v6 import hypotheses as H  # noqa: E402
from benchmark.v6.define_tasks_v6 import SEEDS, seed_cases  # noqa: E402

DOC = json.loads((ROOT / "benchmark/v6/tasks.json").read_text())
TASKS = {t["task_id"]: t for t in DOC["tasks"]}
CORE_TARGET = {"variants": 20, "tasks": 8}


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
        for fam, info in t["v6_families"].items():
            seeds = {int(k): v for k, v in info["seeds"].items()}
            assert sorted(seeds) == SEEDS
            if info["origin"] == "v6":
                assert seeds == seed_cases(tid, fam, info["cases"])
                c = Counter(seeds.values())
                assert set(c) == set(info["cases"]) and max(c.values()) - min(c.values()) <= 1
            for s, v in list(seeds.items())[:2]:
                assert episode_config(t, s, v)["config_hash"] == episode_config(t, s, v)["config_hash"]


def test_cases_differ_in_decision():
    for t in TASKS.values():
        for fam, info in t["v6_families"].items():
            if len(info["cases"]) > 1:
                routes = {json.dumps(t["routes"][t["oracle"][v]]["steps"], sort_keys=True) for v in info["cases"]}
                assert len(routes) == len(info["cases"]), fam
                assert info.get("factor"), fam


def test_new_families_agree_with_the_tier_rule():
    for t in TASKS.values():
        assert t["v6_design_problems"] == [], t["task_id"]
        for fam, info in t["v6_families"].items():
            if info["origin"] != "v6":
                continue
            for v in info["cases"]:
                a = t["v6_audit"][v]
                assert a["tier_rule"] == info["tier"], (fam, v)
                assert a["rejected"] == [], (fam, v)
                if info["tier"] == "hard":
                    assert a["core"] and not a["retry_solvable"], (fam, v)


def test_hard_tier_means_task_level_replanning():
    for t in TASKS.values():
        for fam in t["v6_formal"]["hard"]:
            for v in t["v6_families"][fam]["cases"]:
                a = t["v6_audit"][v]
                assert a["core"] and not a["retry_solvable"], (t["task_id"], fam)
        for fam in t["v6_formal"]["easy"]:
            for v in t["v6_families"][fam]["cases"]:
                assert not t["variants"][v].get("failures"), (t["task_id"], fam)


def test_core_capability_targets():
    n, tasks = Counter(), defaultdict(set)
    for tid, t in TASKS.items():
        for fam in t["v6_formal"]["hard"]:
            for cap in t["v6_families"][fam]["capabilities"]:
                n[cap] += 1
                tasks[cap].add(tid)
    for cap in H.CORE:
        assert n[cap] >= CORE_TARGET["variants"] and len(tasks[cap]) >= CORE_TARGET["tasks"], (cap, n[cap], len(tasks[cap]))


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
    assert st["problems"] == [] and st["static_ok"] == st["episodes"] == 10 * st["families"]


# ----------------------------------------------------------------- the checker rejects what it should
def _ctx(tid, vid, mutate=None):
    t = copy.deepcopy(TASKS[tid])
    if mutate:
        mutate(t)
    return t, H.Ctx(t, vid)


def test_a_transient_failure_is_not_cross_level():
    def transient(t):
        for f in t["variants"]["x6_cl_block_a_unholdable__b_island"]["failures"]:
            f.pop("persist", None)
    _, c = _ctx("T06_block_destination_occupied", "x6_cl_block_a_unholdable__b_island", transient)
    h = c.v["v6"]["hypotheses"][0]
    assert any("not persistent" in r for r in H.check_CL(c, h))


def test_dr_needs_a_cause_naming_the_blocker():
    _, c = _ctx("T01_book_to_dining_table", "x6_dr_block_on_book__block")
    h = dict(c.v["v6"]["hypotheses"][0], blocker="rolling_pin")
    assert H.check_DR(c, h)


def test_pp_needs_progress_before_the_event():
    _, c = _ctx("T13_breakfast_setup", "x6_pp_spoon_moved__table_end")
    h = dict(c.v["v6"]["hypotheses"][0], kept={"atom": ["on", "cup", "dining_table_2/top"],
                                              "by": {"skill": "place", "args": {"object": "spoon"}}})
    assert any("not achieved before" in r or "never achieves" in r for r in H.check_PP(c, h))


def test_sr_needs_a_different_procedure():
    _, c = _ctx("T07_heat_oatmeal", "x6_cl_microwave_door_stuck__oatmeal_island")
    h = next(x for x in c.v["v6"]["hypotheses"] if x["cap"] == "SR")
    same = dict(h, replacement=h["nominal"])
    assert H.check_SR(c, same)


def test_a_variant_without_constraints_is_retry_solvable():
    _, c = _ctx("T06_block_destination_occupied", "x6_m_grasp_block_a")
    assert H.retry_solvable(c)
    _, c = _ctx("T06_block_destination_occupied", "x6_cl_block_a_unholdable__b_island")
    assert not H.retry_solvable(c)


@pytest.mark.parametrize("tid", sorted(TASKS))
def test_every_hard_family_has_a_control_in_the_task(tid):
    t = TASKS[tid]
    for fam, info in t["v6_families"].items():
        if info["origin"] == "v6":
            assert info["control"] in t["variants"], fam
