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


def test_v5_designs_unchanged():
    """A v5 variant keeps its design (conditions, goal, instruction, failures other than the injected action ones);
    where things stand and where the robot starts are the seed's (layout.py)."""
    v5 = {t["task_id"]: t for t in json.loads((ROOT / "benchmark/v5/tasks.json").read_text())["tasks"]}
    for tid, t in TASKS.items():
        for vid in [x for ids in v5[tid]["v5_formal"].values() for x in ids]:
            if vid in t["v6_dropped"]:
                assert vid not in t["variants"]
                continue
            old, new = v5[tid]["variants"][vid], t["variants"][vid]
            assert old.get("goal") == new.get("goal") and old.get("instruction") == new.get("instruction"), vid
            if "conditions_ignored" not in new:
                assert old.get("conditions") == new.get("conditions"), vid
            removed = set(new.get("injected_removed", []))
            assert [f for f in old.get("failures", []) if f["id"] not in removed] == new.get("failures", []), vid


def test_seeds_keep_what_the_variant_tests():
    """Objects a variant places for its challenge keep their relative positions on every seed (the bowl stays in
    the pin's path, the crowd around block B stays tight), and a boxed-in or full place stays as designed."""
    from benchmark.scene import episode_config

    def rel(cfg, a, b):
        return [round(cfg["move"][a]["xy"][k] - cfg["move"][b]["xy"][k], 3) for k in (0, 1)]
    for tid, vid, a, b in (("T16_rolling_pin_at_edge", "h_task_bowl_behind", "oatmeal", "rolling_pin"),
                           ("T02_stack_blocks", "crowded", "wooden_block_b", "oatmeal"),
                           ("T01_book_to_dining_table", "x6_dr_block_on_book__block", "wooden_block_a",
                            "paperback_book")):
        t = TASKS[tid]
        assert len({tuple(rel(episode_config(t, s, vid), a, b)) for s in SEEDS}) == 1, (tid, vid)
    for tid, vid in (("T13_breakfast_setup", "no_cup_spoon_boxed_in"), ("T20_juice_back_to_table", "table_full")):
        t = TASKS[tid]
        design = {n: m for n, m in t["variants"][vid]["move"].items() if n not in ("bowl", "juice_bottle")}
        for s in SEEDS:
            cfg = episode_config(t, s, vid)
            assert all(cfg["move"][n]["xy"] == m["xy"] for n, m in design.items()), (tid, s)


def test_seeds_draw_different_layouts():
    """Ten seeds of a variant put the robot and the movable objects in different places."""
    from benchmark.scene import episode_config
    for tid, vid in (("T01_book_to_dining_table", "overhang_ready"), ("T13_breakfast_setup", "dishes_on_tv_stand")):
        t = TASKS[tid]
        starts = {tuple(episode_config(t, s, vid)["start"]) for s in SEEDS}
        poses = {json.dumps(episode_config(t, s, vid)["move"], sort_keys=True) for s in SEEDS}
        assert len(starts) >= 8 and len(poses) >= 8, (tid, len(starts), len(poses))
        assert all(episode_config(t, s, vid) == episode_config(t, s, vid) for s in (10, 15))


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


def test_every_layout_has_its_route():
    for tid, t in TASKS.items():
        for info in t["v6_variants"].values():
            for lid in info["layouts"]:
                assert t["oracle"][lid] in t["routes"], (tid, lid)


def test_in_place_choices_are_redesigned_at_a_longer_horizon():
    """The substitute / container / pot is in another room; the in-place variant left v6."""
    for tid, old, new in (("T03_utensils_one_container", "small_and_large", "mug_or_bedroom_bin"),
                          ("T03_utensils_one_container", "three_containers", "three_containers_bedroom"),
                          ("T04_cup_or_mug_to_cabinet", "h_dynamic_cup_taken", "cup_taken_mug_in_living_room"),
                          ("T09_tomato_soup", "cookware_choice", "pot_in_dining_room")):
        t = TASKS[tid]
        assert old not in t["v6_variants"] and new in t["v6_variants"], (tid, old)
        assert t["v6_tracks"][new]["category"] == "task"
        assert any(s["skill"] == "search" for s in t["routes"][t["oracle"][new]]["steps"])
    assert "no_pen" not in TASKS["T05_pen_or_pencil_to_desk"]["v6_variants"]


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


def _t01_suitable(cfg):
    """Centres y (1 cm steps) along the east edge of the dining table where a book (12 x 18 cm, either way along
    the edge) is clear of the tableware by 5 cm and within 15 cm of a plate or bowl (the table_seats goal)."""
    import math
    from benchmark.v6 import layout as L
    boxes = {n: L._box(L._asset_of(cfg["base"], n, {}), m) for n, m in cfg["move"].items()
             if m.get("support") == "dining_table_2/top"}

    def gap(a, b):
        return math.hypot(max(0, max(a[0], b[0]) - min(a[2], b[2])), max(0, max(a[1], b[1]) - min(a[3], b[3])))
    ok = set()
    for along, across in ((0.12, 0.18), (0.18, 0.12)):
        for i in range(250):
            y = 5.495 + along / 2 + i * 0.01
            if y + along / 2 > 7.955:
                break
            bk = [3.859 - across, y - along / 2, 3.859, y + along / 2]
            if min(gap(bk, b) for b in boxes.values()) >= 0.05 and \
                    min(gap(bk, boxes[n]) for n in ("bowl_side_table", "plate_counter_a", "plate_counter_b")) <= 0.15:
                ok.add(round(y, 2))
    return ok


def test_t01_one_suitable_slot_per_setting():
    """T01 table_seats: in every setting and seed the edge has one suitable slot (the route's), and it differs
    between the settings; seat_slot_blocked has none until the cereal box is moved."""
    t = TASKS["T01_book_to_dining_table"]
    slots = {}
    for s, lid in t["v6_variants"]["table_seats"]["seeds"].items():
        ok = _t01_suitable(episode_config(t, int(s), lid))
        hint = [x for x in t["routes"][t["oracle"][lid]]["steps"] if x["skill"] == "place"][-1]["args"]["hint_xy"]
        assert ok and max(ok) - min(ok) < 0.2, (lid, s, sorted(ok))        # one slot, not several
        assert min(ok) - 0.02 <= hint[1] <= max(ok) + 0.02, (lid, s, hint)
        slots[lid] = round(hint[1], 2)
    assert len(set(slots.values())) == 3
    for s in SEEDS:
        assert not _t01_suitable(episode_config(t, s, "seat_slot_blocked"))
