"""Substitution statistics (11-17, user: keep the kinds of substitution balanced).

Every seed (layout) of a reviewed design gets the kind of substitution it asks for (``KIND``, by the meeting's
categories) and the best level it can offer (``top_by_layout`` from tasks.json: ideal / moderate / bad).  Writes
SUBSTITUTION_STATS_zh.md: the counts per kind, per top level, per kind x level, and the list per task.

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
    ("T03", "utensils_apart"): {"bin_free": None, "bin_full_tray": "被占用", "bin_full_basket": "被占用",
                                "bin_full_fruit": "被占用"},
}
LEVEL_ZH = {"ideal": "好", "moderate": "次好", "bad": "最不好"}


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
                kind = kinds.get(base, kinds.get("*"))
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
    out += ["", "## 最高能拿到哪一档", "", "| 最高档 | 摆法数 |", "|---|---|"]
    out += [f"| {LEVEL_ZH[lv]} | {by_top[lv]} |" for lv in ("ideal", "moderate", "bad")]
    out += ["", "## 类别 × 最高档", "", "| 类别 | 好 | 次好 | 最不好 |", "|---|---|---|---|"]
    out += [f"| {k} | " + " | ".join(str(by_both[(k, lv)]) for lv in ("ideal", "moderate", "bad")) + " |" for k in KINDS]
    out += ["", "## 每个摆法", "", "| 任务 | 变体 | 摆法 | 类别 | 最高档 | D |", "|---|---|---|---|---|---|"]
    out += [f"| {a} | {b} | {c or '—'} | {k or '不用替换'} | {LEVEL_ZH[top]} | {d} |" for a, b, c, k, top, d in rows]
    (HERE / "SUBSTITUTION_STATS_zh.md").write_text("\n".join(out) + "\n")
    print(f"wrote SUBSTITUTION_STATS_zh.md: {len(rows)} seeds, {len(sub)} with a substitution; "
          + ", ".join(f"{k} {by_kind[k]}" for k in KINDS))


if __name__ == "__main__":
    main()
