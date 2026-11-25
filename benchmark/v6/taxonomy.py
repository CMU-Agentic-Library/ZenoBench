"""ZenoBench v6 taxonomy (11-25): one label per layout on three axes, coverage counts, scores per label.

Axes: recovery strategy (what the best solution does differently from the nominal plan), reasoning basis (what
decides the right choice), object category (registry category of the thing substituted, or of the thing moved).
Strategy and basis come from rules over the layout's conditions and its substitution kind
(substitution_stats.KIND); OVERRIDE fixes the few layouts the rules misread.  Object categories are set by hand
(TASK_OBJECT, SUBSTITUTED_OBJECT, CONTAINER_PLACE), reviewed layout by layout on 11-25.

Read-only: tasks, scoring and what the planner sees are not changed.

    python -m benchmark.v6.taxonomy                               # TAXONOMY_LABELS.json + TAXONOMY_zh.md
    python -m benchmark.v6.taxonomy --run ReAct@qwen=DIR [--native DIR] [--rows rows.jsonl] [--out eval.md]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / "TAXONOMY_LABELS.json"
OUT_MD = HERE / "TAXONOMY_zh.md"

STRATEGY = {
    "nominal": "无需恢复（对照）",
    "substitute_object": "物体替换（含换电器）",
    "substitute_place": "去处替换",
    "search": "搜索不在眼前的东西",
    "discriminate": "辨别看着像的",
    "leave_in_use": "不动正在用的/已满足的",
    "clear_obstacle": "障碍移除/前置条件",
    "infer_goal": "推断目标（放哪、拿什么、几个）",
    "detour": "绕行",
}
BASIS = {
    "affordance": "功能可供性",
    "geometry": "形状与尺寸",
    "appearance": "外观相似",
    "spatial": "空间约束",
    "social": "归属与偏好",
    "context": "情境线索与规则",
}
OBJ_CAT = {"tableware": "餐具", "cookware": "厨具", "food_container": "食物容器", "container": "收纳容器",
           "food": "食品", "stationery": "文具与书", "toy": "玩具", "cleaning": "清洁用品",
           "furniture": "家具/放置面", "appliance": "电器"}
CAT_ZH = {"control": "对照", "task": "Task", "action_task": "Action+Task"}

# designs whose right choice depends on a person (whose thing, who sits where, who wants what)
SOCIAL = {
    "T01": {"table_seats", "reader_seat", "no_room_fallback"}, "T04": {"two_guests"}, "T10": {"keep_kids_can"},
    "T11": {"leave_one_for_kid"}, "T13": {"finish_the_table"}, "T14": {"within_kids_reach", "whose_book"},
    "T21": {"the_kids_side"}, "T22": {"eat_now"}, "T24": {"dinner_soon", "where_is_he", "two_kids"},
    "T25": {"little_guest", "cold_one"}, "T26": {"whose", "two_bedrooms"}, "T28": {"which_bed", "where_his_cup_is",
    "already_there"},
}
# what is substituted ("object" / "place") where the conditions alone would read it the other way
OVERRIDE = {
    ("T06", "display_row"): "place",                     # the cabinet top is too short: the TV stand instead
    ("T03", "utensils_apart"): "object",                 # the bin is full: a tray or basket instead
    ("T09", "tomato_in_fridge"): "object",               # a big tomato for the cherry tomatoes
    ("T07", "vessel_decides_appliance"): "object",       # metal / foil / pot: the stove instead of the microwave
    ("T18", "door_stuck"): "object",                     # clean bowls from another cabinet
    ("T21", "no_tissue"): "object",                      # the sponge for tissues
    ("T24", "two_kids__desk3_covered"): "place",         # the desk is covered
    ("T25", "cold_one"): "object",                       # cold soda for juice
    ("T25", "drink_in_fridge"): "object",
}
# object category, by hand.  The thing the task moves (layouts without substitution):
TASK_OBJECT = {"T01": "stationery", "T02": "toy", "T03": "cookware", "T04": "tableware", "T05": "stationery",
               "T06": "toy", "T07": "tableware", "T08": "cleaning", "T09": "food", "T10": "food", "T11": "food",
               "T12": "toy", "T13": "tableware", "T14": "stationery", "T15": "cookware", "T16": "food",
               "T17": "toy", "T18": "tableware", "T19": "food", "T20": "food", "T21": "cleaning", "T22": "food",
               "T23": "tableware", "T24": "food", "T25": "food", "T26": "toy", "T27": "food_container",
               "T28": "tableware", "T29": "toy", "T30": "tableware"}
TASK_OBJECT_DESIGN = {("T07", "vessel_decides_appliance__in_glass_box"): "food_container",
                      ("T26", "whose"): "stationery",            # the books to his bookcase
                      ("T29", "homework_on_table"): "stationery"}
# the thing substituted (object substitutions): per task, then per design / layout
SUBSTITUTED_OBJECT = {"T02": "toy", "T03": "container", "T04": "tableware", "T05": "stationery", "T07": "appliance",
                      "T08": "cleaning", "T09": "cookware", "T10": "container", "T11": "container",
                      "T13": "tableware", "T15": "cookware", "T16": "container", "T17": "cookware",
                      "T18": "tableware", "T21": "cleaning", "T23": "container", "T24": "food", "T25": "food",
                      "T26": "container", "T28": "tableware", "T29": "container", "T30": "tableware"}
SUBSTITUTED_DESIGN = {("T09", "tomato_in_fridge"): "food", ("T09", "x6_gd_tomato_elsewhere"): "food",
                      ("T25", "cups_for_two"): "tableware"}
# place substitutions where the place is a container (bin, basket, tray), not a piece of furniture
CONTAINER_PLACE = {("T12", "bins_capacity"), ("T22", "tray_elsewhere"), ("T22", "basket_missing"),
                   ("T23", "by_kind__bin_full"), ("T26", "where_in_room"), ("T29", "several__bin_full")}
SEARCH_C = {"not_in_view", "item_out_of_view", "item_put_away", "tool_away_from_surface", "start_elsewhere"}
GOAL_C = {"spot_quality", "destination_unnamed", "storage_place", "agent_ability", "referent_clue",
          "goal_items_unstated", "count_from_scene", "goal_by_example", "rule_induction", "category_rule",
          "disposal_by_state", "arrangement", "preference_allocation", "subgoal_order", "errands_combined",
          "dependent_decisions", "multi_object_goal", "appliance_compatibility"}
PLACE_GOAL_C = {"spot_quality", "destination_unnamed", "storage_place", "agent_ability"}


def label(task, design, info, lid, card) -> dict:
    from benchmark.v6.substitution_eval import reason_of
    tid, v = task["task_id"][:3], task["variants"][lid]
    conds = set(v.get("conditions") or [])
    cat = card["category"]
    present = (v.get("scoring") or {}).get("ideal_present", True) is not False
    kind = reason_of(task, design, lid) if cat != "control" else None
    over = OVERRIDE.get((tid, lid)) or OVERRIDE.get((tid, design))
    social = design in SOCIAL.get(tid, ())

    # recovery strategy
    if cat == "control":
        st = "nominal"
    elif over and kind:
        st = "substitute_" + over
    elif kind == "去处替换":
        st = "substitute_place"
    elif kind in ("缺失", "被占用", "能力不足", "看着像但不能用") and not present:
        place = conds & {"storage_place", "destination_full", "destination_occupied", "joint_capacity"}
        st = "substitute_place" if place else "substitute_object"
    elif kind == "看着像但不能用" or conds & {"decoy_destination", "unsuitable_at_hand"}:
        st = "discriminate"
    elif kind == "被占用" or conds & {"goal_already_met", "relational_exception"}:
        st = "leave_in_use"
    elif conds & {"closed_fridge", "lid_on", "no_overhang", "unstable_base"} or design == "clear_the_drinks_spot":
        st = "clear_obstacle"
    elif kind in ("缺失", "能力不足"):
        st = "search"                       # the ideal is there, put away / in another room
    elif conds & GOAL_C:
        st = "infer_goal"
    elif conds & SEARCH_C or cat != "control":
        st = "search"
    else:
        st = "nominal"

    # reasoning basis
    if st == "nominal":
        basis = None
    elif st == "substitute_object":
        basis = "geometry" if kind == "能力不足" and tid != "T07" else "affordance"
    elif st == "substitute_place":
        basis = "geometry" if kind == "能力不足" else "social" if social else "spatial"
    elif st == "discriminate":
        basis = "appearance"
    elif st == "leave_in_use":
        basis = "context" if "goal_already_met" in conds else "social"
    elif st == "clear_obstacle":
        basis = "geometry" if conds & {"no_overhang", "unstable_base"} else "spatial"
    elif st == "infer_goal":
        basis = ("social" if social else "affordance" if "appliance_compatibility" in conds else
                 "spatial" if conds & PLACE_GOAL_C and "referent_clue" not in conds else "context")
    else:
        basis = "spatial"

    # object category: what is substituted, else the thing the task moves
    def pick(table, default):
        return table.get((tid, lid), table.get((tid, design), default))
    if st == "substitute_place":
        obj_cat = "container" if (tid, lid) in CONTAINER_PLACE or (tid, design) in CONTAINER_PLACE else "furniture"
    elif st == "substitute_object":
        obj_cat = pick(SUBSTITUTED_DESIGN, SUBSTITUTED_OBJECT[tid])
    else:
        obj_cat = pick(TASK_OBJECT_DESIGN, TASK_OBJECT[tid])
    seeds = [int(s) for s, x in (info.get("seeds") or {}).items() if x == lid] or card.get("seeds") or []
    return {"task": task["task_id"], "design": design, "layout": lid, "category": cat, "episodes": len(seeds),
            "substitution_kind": kind, "strategy": st, "basis": basis, "object_category": obj_cat,
            "conditions": sorted(conds)}


def build() -> list[dict]:
    tasks = json.loads((HERE / "tasks.json").read_text())["tasks"]
    cards = json.loads((HERE / "variant_cards.json").read_text())
    return [label(t, d, info, lid, cards[t["task_id"] + "/" + lid])
            for t in tasks for d, info in t["v6_variants"].items() for lid in info["layouts"]]


# -- report ----------------------------------------------------------------------------------------------------
def _table(head, rows):
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + \
           ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]


def _coverage(rows, key, vocab):
    agg = defaultdict(lambda: [0, set(), set(), 0])
    for r in rows:
        a = agg[r[key]]
        a[0] += 1
        a[1].add((r["task"], r["design"]))
        a[2].add(r["task"][:3])
        a[3] += r["episodes"]
    keys = [k for k in vocab if k in agg or k == "detour"] + [k for k in agg if k not in vocab]
    return _table(["标签", "布局", "设计", "任务", "局"],
                  [(vocab.get(k, "—" if k is None else k), agg[k][0], len(agg[k][1]), len(agg[k][2]), agg[k][3])
                   if k in agg else (vocab[k], 0, 0, 0, 0) for k in keys])


def render(rows) -> str:
    nd = len({(r["task"], r["design"]) for r in rows})
    out = ["# ZenoBench 场景分类", "",
           f"`python -m benchmark.v6.taxonomy` 生成，逐布局标签见 `TAXONOMY_LABELS.json`。v6 全部 "
           f"{len({r['task'] for r in rows})} 个任务、{nd} 个设计、{len(rows)} 个布局、"
           f"{sum(r['episodes'] for r in rows)} 局，每个布局每个维度一个标签。任务、评分、模型输入都没改。", "",
           "## 三个维度", "",
           "- **恢复策略**：最好的做法和原计划比，要多做或换做什么。",
           "- **推理依据**：靠什么判断哪个选择对。",
           "- **物体类别**：被替换的东西的类别；不替换的布局记任务要搬的那件东西（逐布局手定）。", "",
           "## 覆盖", "", "### 恢复策略", ""]
    out += _coverage(rows, "strategy", STRATEGY) + ["", "### 推理依据（对照不计）", ""]
    out += _coverage([r for r in rows if r["basis"]], "basis", BASIS) + ["", "### 物体类别", ""]
    out += _coverage(rows, "object_category", OBJ_CAT) + [""]
    c = Counter((r["strategy"], r["object_category"]) for r in rows)
    cats = [k for k in OBJ_CAT if any(k == oc for _, oc in c)]
    sts = [k for k in STRATEGY if any(k == s for s, _ in c)]
    out += ["### 恢复策略 × 物体类别（布局数）", ""]
    out += _table([""] + [OBJ_CAT[k] for k in cats], [[STRATEGY[s]] + [c.get((s, k), 0) or "·" for k in cats]
                                                      for s in sts]) + [""]
    out += ["说明：绕行和大部分障碍移除是 11-05 有意去掉的（TAMPAgent 已覆盖“受阻→清障→继续”），v6 也不注入动作失败，"
            "论文里写成范围之外。", "", "## 逐设计", ""]
    by = defaultdict(list)
    for r in rows:
        by[(r["task"], r["design"])].append(r)
    j = lambda xs: " / ".join(dict.fromkeys(xs))                                   # noqa: E731
    out += _table(["任务", "设计", "布局数", "类别", "恢复策略", "推理依据", "物体类别"],
                  [(t[:3], d, len(rs), CAT_ZH[rs[0]["category"]], j(STRATEGY[r["strategy"]] for r in rs),
                    j(BASIS.get(r["basis"], "—") for r in rs), j(OBJ_CAT.get(r["object_category"], "—") for r in rs))
                   for (t, d), rs in by.items()])
    return "\n".join(out) + "\n"


# -- scores per label ------------------------------------------------------------------------------------------
def eval_rows(runs, native, extra) -> list[dict]:
    from benchmark.v6.substitution_eval import results
    out = []
    for name, root in runs:
        for _, r in results(root, native):
            sc = r.get("score") or {}
            out.append({"run": name, "task": r["task_id"], "layout": r["variant"], "seed": r.get("seed"),
                        "score": float(sc.get("score") or 0.0), "success": bool(r.get("task_success")),
                        "best": bool(r.get("task_success")) and sc.get("tier") == "best"})
    for p in extra:
        out += [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    return out


def render_eval(ep, labels) -> str:
    lab = {(r["task"], r["layout"]): r for r in labels}
    ep = [dict(e, _l=lab[(e["task"], e["layout"])]) for e in ep if (e["task"], e["layout"]) in lab]
    runs = list(dict.fromkeys(e["run"] for e in ep))
    out = ["# 分类型评测结果", "", f"{len(ep)} 局。每格：平均分 / 成功率 (局数)。", ""]

    def cell(es):
        return f"{sum(e['score'] for e in es) / len(es):.2f} / {sum(e['success'] for e in es) / len(es):.0%} " \
               f"({len(es)})" if es else "—"

    for title, key, vocab in (("恢复策略", "strategy", STRATEGY), ("推理依据", "basis", BASIS),
                              ("物体类别", "object_category", OBJ_CAT)):
        rows = [[vocab[k]] + [cell([e for e in ep if e["run"] == run and e["_l"][key] == k]) for run in runs]
                for k in vocab]
        out += [f"## {title}", ""] + _table(["标签"] + runs, [r for r in rows if any(c != "—" for c in r[1:])]) + [""]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", default=[], help="LABEL=DIR of result.json files")
    ap.add_argument("--native", type=Path, help="env_service --log-dir, for planner results without calls")
    ap.add_argument("--rows", action="append", type=Path, default=[], help="jsonl {run, task, layout, score, success}")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    labels = build()
    if a.run or a.rows:
        text = render_eval(eval_rows([tuple(x.split("=", 1)) for x in a.run], a.native, a.rows), labels)
        a.out.write_text(text) if a.out else print(text)
        return 0
    OUT_JSON.write_text(json.dumps(labels, ensure_ascii=False, indent=1) + "\n")
    OUT_MD.write_text(render(labels))
    print(f"{len(labels)} layouts -> {OUT_JSON.name}, {OUT_MD.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
