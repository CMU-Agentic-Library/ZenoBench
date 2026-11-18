"""Substitution statistics (11-17, user: keep the kinds of substitution balanced).

Every seed (layout) of a reviewed design gets the kind of substitution it asks for (``KIND``, by the meeting's
categories) and whether the ideal thing is in the scene (``top_by_layout`` from tasks.json; 11-17, user: without
it the best substitute scores 1.0 all the same).  Writes SUBSTITUTION_STATS_zh.md: the counts per kind, ideal
present or not, kind x that, and the list per task.

    python benchmark/v6/substitution_stats.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

KINDS = ("缺失", "被占用", "能力不足", "看着像但不能用", "去处替换")
# (task prefix, design) -> {case: kind} ("*": every case); None: the seed asks for no substitution (the ideal is
# there and nothing in view tempts) -- counted apart.  Only designs reviewed with the user are listed.
KIND = {
    ("T01", "which_book"): {"*": "看着像但不能用"},
    ("T02", "crowded_use_another"): {"tight_tv": "被占用", "tight_dining": "被占用", "loose": None},
    ("T02", "third_toy_elsewhere"): {"*": "缺失"},
    ("T02", "tower_for_kid"): {"counter": None, "study": None, "near_full": "去处替换", "both_full": "去处替换"},
    ("T02", "tower_for_kid_duck"): {"*": "缺失"},
    ("T02", "block_put_away"): {"in_4": "缺失", "in_6": "缺失", "gone_toy_block": "缺失", "gone_duck": "缺失"},
    ("T03", "small_bin_or_bedroom_bin"): {"*": "能力不足"},
    ("T03", "which_bin_by_contents"): {"toys_near": "看着像但不能用", "kitchen_bin_full": "被占用"},
    ("T03", "no_bin_substitute"): {"*": "缺失"},
    ("T04", "cup_available"): {"*": None},
    ("T04", "no_cup"): {"*": "缺失"},
    ("T04", "two_guests"): {"glass_in_cabinet": None, "mug": "缺失", "kid_cup": "缺失"},
    ("T04", "x6_gd_cup_in_cabinets"): {"*": "能力不足"},
    ("T04", "clear_the_drinks_spot"): {"spot_dishes": None, "spot_kid_toys": "去处替换"},
    ("T05", "no_pen_pencil_away"): {"no_pen_pencil_away": None, "no_pen_pencil_in_use": "被占用"},
    ("T05", "check_desk_first"): {"pen_on_desk": None, "pencil_on_desk": "看着像但不能用", "pen_in_use": "被占用"},
    ("T05", "homework_ready"): {"single": "看着像但不能用", "several": "看着像但不能用", "notebook_in_use": "被占用"},
    ("T05", "errand_combined"): {"pen_bedroom": None, "pen_in_use": "被占用"},
    ("T05", "x6_gd_pen_or_pencil_cabinets"): {"pen_in_4": "看着像但不能用", "pen_in_use": "被占用"},
    ("T06", "free"): {"*": None},
    ("T06", "display_row"): {"cab_free": None, "cab_short": "能力不足"},
    ("T06", "display_spot_or_tv"): {"front_free": None, "front_free_block_away": None, "front_taken": "去处替换",
                                    "front_taken_tv_full": "去处替换"},
    ("T06", "seen_from_bed"): {"boxes_middle": None, "bookcase_full": "去处替换"},
    ("T07", "microwave_works"): {"*": None},
    ("T07", "microwave_broken"): {"*": "看着像但不能用"},
    ("T07", "microwave_holds_pot"): {"*": "被占用"},
    ("T07", "vessel_decides_appliance"): {"in_ceramic_bowl": None, "in_glass_box": None, "in_pot": "能力不足",
                                          "in_steel_box": "能力不足", "in_foil_tray": "能力不足"},
    ("T07", "two_portions"): {"*": None},
    ("T08", "sponge_on_island"): {"*": None},
    ("T08", "far_sponge_tv"): {"far_sponge_tv": None, "far_sponge_foam_cube": "看着像但不能用",
                               "far_sponge_spare_only": "缺失"},
    ("T08", "wipe_and_sort"): {"*": None},
    ("T08", "return_sponge_home"): {"*": None},
    ("T08", "which_surface"): {"*": None},
    ("T09", "lid_off"): {"*": None},
    ("T09", "lid_on_spoon_away"): {"lid_on_spoon_away": None, "lid_missing": "缺失"},
    ("T09", "pot_in_dining_room"): {"pot_away": None, "spare_pot": "缺失"},
    ("T09", "x6_gd_tomato_elsewhere"): {"dining": None, "on_plate": "被占用"},
    ("T09", "pot_in_use"): {"in_use": "被占用", "free": None},
    ("T09", "tomato_in_fridge"): {"in_fridge": None, "big_tomato": "缺失"},
    ("T10", "can_on_island"): {"*": None},
    ("T10", "can_in_dining_room"): {"*": None},
    ("T10", "keep_kids_can"): {"*": "被占用"},
    ("T10", "trash_moved"): {"dining": None, "trash_full": "能力不足"},
    ("T10", "after_dinner_clear"): {"*": "去处替换"},
    ("T10", "guests_coming"): {"*": "去处替换"},
    ("T10", "x6_gd_can_put_away"): {"in_cabinet": None, "fridge_drink": "看着像但不能用"},
    ("T11", "fruits_on_table"): {"*": None},
    ("T11", "basket_missing"): {"basket_missing": "缺失", "basket_gone_bowl_there": "看着像但不能用"},
    ("T11", "leave_one_for_kid"): {"*": "去处替换"},
    ("T11", "fruit_plate_for_guests"): {"tray_in_study": None, "tray_in_use": "被占用"},
    ("T12", "toys_out"): {"*": None},
    ("T12", "duck_in_study"): {"*": None},
    ("T12", "bins_capacity"): {"*": "能力不足"},
    ("T12", "find_all_toys"): {"*": "看着像但不能用"},
    ("T12", "castle_stays"): {"*": "被占用"},
    ("T13", "dishes_on_tv_stand"): {"*": None},
    ("T13", "no_cup"): {"*": "缺失"},
    ("T13", "copy_the_setting"): {"bowl_cup": "去处替换", "plate_bowl_mug_left": "去处替换", "no_cup": "缺失"},
    ("T13", "finish_the_table"): {"*": "去处替换"},
    ("T14", "e1_book_ready"): {"*": None},
    ("T14", "within_kids_reach"): {"*": "去处替换"},
    ("T14", "stack_them_stably"): {"room": None, "narrow_top": "能力不足"},
    ("T14", "homework_stays"): {"*": "被占用"},
    ("T14", "whose_book"): {"*": "去处替换"},
    ("T14", "next_in_series"): {"*": "看着像但不能用"},
    ("T15", "lid_by_pot"): {"*": None},
    ("T15", "lid_elsewhere"): {"dining": None, "covering_bowl": "被占用"},
    ("T15", "no_lid"): {"*": "缺失"},
    ("T15", "lid_in_use"): {"*": "被占用"},
    ("T16", "box_on_counter"): {"*": None},
    ("T16", "box_in_cabinet"): {"in_cabinet": None, "box_full": "能力不足"},
    ("T16", "no_box"): {"*": "缺失"},
    ("T16", "box_in_use"): {"*": "被占用"},
    ("T03", "utensils_apart"): {"bin_free": None, "bin_full_tray": "被占用", "bin_full_basket": "被占用",
                                "bin_full_fruit": "被占用"},
}
IDEAL_ZH = {"ideal": "在", "moderate": "不在", "bad": "不在"}


def main():
    doc = json.loads((HERE / "tasks.json").read_text())
    rows = []
    for t in doc["tasks"]:
        for design, info in t["v6_variants"].items():
            kinds = next((k for (tid, d), k in KIND.items() if t["task_id"].startswith(tid) and d == design), None)
            if kinds is None:
                continue
            sc = info.get("scoring") or {}
            for lid in info["layouts"]:
                case = lid.split("__", 1)[1] if "__" in lid else ""
                base = case[:-5] if case.endswith("_flat") else case
                kind = kinds.get(base, kinds.get(lid, kinds.get("*")))
                top = (sc.get("top_by_layout") or {}).get(lid) or "ideal"
                d = (sc.get("D_by_layout") or {}).get(lid, sc.get("D"))
                rows.append((t["task_id"][:3], design, case, kind, top, d))
    sub = [r for r in rows if r[3]]
    by_kind = Counter(r[3] for r in sub)
    by_top = Counter(r[4] for r in sub)
    by_both = Counter((r[3], r[4]) for r in sub)
    mean = len(sub) / len(KINDS) if sub else 0
    out = ["# 替换统计（按摆法）", "",
           f"已审过的变体里一共 {len(rows)} 个摆法，其中 {len(sub)} 个要做替换，{len(rows) - len(sub)} 个不用替换"
           "（理想的东西在、眼前也没有诱惑，作对照）。五类平均每类应有约 "
           f"{mean:.1f} 个。由 `python benchmark/v6/substitution_stats.py` 生成。", "",
           "## 每类替换的摆法数", "", "| 类别 | 摆法数 | 和平均的差 |", "|---|---|---|"]
    out += [f"| {k} | {by_kind[k]} | {by_kind[k] - mean:+.1f} |" for k in KINDS]
    present = Counter("在" if r[4] == "ideal" else "不在" for r in sub)
    out += ["", "## 理想物在不在（不在时，最好的替代算好）", "", "| 理想物 | 摆法数 |", "|---|---|"]
    out += [f"| {k} | {present[k]} |" for k in ("在", "不在")]
    out += ["", "## 类别 × 理想物在不在", "", "| 类别 | 在 | 不在 |", "|---|---|---|"]
    out += [f"| {k} | {by_both[(k, 'ideal')]} | {by_both[(k, 'moderate')] + by_both[(k, 'bad')]} |" for k in KINDS]
    out += ["", "## 每个摆法", "", "| 任务 | 变体 | 摆法 | 类别 | 理想物 | D |", "|---|---|---|---|---|---|"]
    out += [f"| {a} | {b} | {c or '—'} | {k or '不用替换'} | {IDEAL_ZH[top]} | {d} |" for a, b, c, k, top, d in rows]
    (HERE / "SUBSTITUTION_STATS_zh.md").write_text("\n".join(out) + "\n")
    print(f"wrote SUBSTITUTION_STATS_zh.md: {len(rows)} seeds, {len(sub)} with a substitution; "
          + ", ".join(f"{k} {by_kind[k]}" for k in KINDS))


if __name__ == "__main__":
    main()
