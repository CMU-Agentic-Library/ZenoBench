"""ZenoBench-Sub (11-25): graded substitution metrics on v6 episodes, read from the simulator's own results.

The design (docs: ZenoBench-Sub 分级替代评测设计): the instruction names the means (the ideal); a pair of designs
of one task keeps the instruction and changes the scene -- A, the ideal there (do not switch), B, the ideal missing,
taken or broken (switch, and to the best grade there is).  Every candidate has a fixed grade for its task:
ideal, moderate, bad; anything else is ``else``.

What the planner chose is read from the outcome, not from a declaration: the scored alternative of the tier that
held (``score.branch_atoms``, benchmark/v6/scoring.py), else the tier's goal; for an episode that failed, the
last candidate it held.  Destinations (T03's bin, T11's basket) are never held, so a failed episode there has no
known choice.

    python -m benchmark.v6.substitution_eval --pairs                    # the A/B table
    python -m benchmark.v6.substitution_eval --batch benchmark/v6/batches/substitution_pairs.json
    python -m benchmark.v6.substitution_eval --run ReAct@qwen=baseline/runs/ReAct@qwen3.5-4b \\
        --native $ZB_RUN/native [--run ...] [--k 3] [--out baseline/results/substitution.md] [--json rows.jsonl]

``--run LABEL=DIR``: every result.json under DIR.  A simulator result (``calls``) is read as it is; a planner
result (``exp_id``, no ``calls``) is looked up in ``--native`` as <native>/<task>/<exp_id>/result.json.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE / "tasks.json"
GRADES = ("ideal", "moderate", "bad")
RANK = {"ideal": 3, "moderate": 2, "bad": 1}

# ------------------------------------------------------------------------------------------------ the pairs
# task prefix -> the designs that keep the task's instruction and differ in whether the ideal can be used.  Each
# layout is A or B by its own ``scoring.ideal_present`` (benchmark/v6/ideals.py); a design listed under
# ``hidden`` puts the ideal out of view (a closed cabinet, another room): its A layouts are the hard A side.
PAIRS = {
    "T03": {"designs": ["large_only", "no_bin_substitute"]},
    "T04": {"designs": ["cup_available", "no_cup"]},
    "T07": {"designs": ["microwave_works", "microwave_broken", "microwave_holds_pot"]},
    "T11": {"designs": ["fruits_on_table", "basket_missing"]},
    "T13": {"designs": ["dishes_on_tv_stand", "no_cup"]},
    "T15": {"designs": ["lid_by_pot", "lid_elsewhere", "no_lid", "lid_in_use"], "hidden": ["lid_elsewhere"]},
    "T16": {"designs": ["box_on_counter", "box_in_cabinet", "no_box", "box_in_use"], "hidden": ["box_in_cabinet"]},
    "T18": {"designs": ["bowls_in_cabinet", "bowls_apart", "one_bowl", "bowl_in_use"], "hidden": ["bowls_apart"]},
    "T21": {"designs": ["tissue_on_tv_stand", "no_tissue"]},
    "T30": {"designs": ["bowl_on_cabinet", "bowl_put_away", "no_bowl"], "hidden": ["bowl_put_away"]},
}
# left out: T09 pot_in_use (the ideal, the empty pot, is there; the test is not to cook in yesterday's soup);
# T18 door_stuck (clean bowls wait in the other cabinet: the source changes, not the thing; the stuck door is not yet
# in the simulator).

# ------------------------------------------------------------------------------------------------ the grades
# task prefix -> grade -> object kinds (object_registry.layout_objects) or names; a name ending in "/" is a place
# prefix (T11's kitchen cabinet shelves).  The grade belongs to the thing and the task, never to the scene.
GRADE = {
    "T03": {"ideal": {"wide_storage_bin"}, "moderate": {"storage_basket", "serving_tray", "shallow_sorting_tray"},
            "bad": {"small_storage_bin", "fruit_basket"}},
    "T04": {"ideal": {"breakfast_cup"}, "moderate": {"breakfast_mug"}, "bad": {"plastic_cup"}},
    "T07": {"ideal": {"kitchen_microwave"}, "moderate": {"kitchen_stove"}, "bad": set()},
    "T11": {"ideal": {"fruit_basket"}, "moderate": {"serving_tray", "kitchen_cabinet_1/", "kitchen_cabinet_4/",
                                                    "kitchen_cabinet_6/"}, "bad": {"breakfast_bowl"}},
    "T13": {"ideal": {"breakfast_cup"}, "moderate": {"breakfast_mug"}, "bad": {"plastic_cup"}},
    "T15": {"ideal": {"pot_lid"}, "moderate": {"breakfast_plate"}, "bad": {"book_blue", "paperback_book"}},
    "T16": {"ideal": {"snack_box"}, "moderate": {"breakfast_bowl"}, "bad": {"wide_storage_bin"}},
    "T18": {"ideal": {"breakfast_bowl", "oatmeal_bowl"}, "moderate": {"glass_food_container", "breakfast_mug"},
            "bad": {"breakfast_plate"}},
    "T21": {"ideal": {"tissue_box"}, "moderate": {"kitchen_sponge"}, "bad": set()},
    "T30": {"ideal": {"breakfast_bowl"}, "moderate": {"breakfast_mug", "breakfast_cup", "glass_food_container"},
            "bad": {"breakfast_plate"}},
}
# the atoms that say what was used: (predicate, position of the used thing, {position: required value}); a value
# ending in "*" is a prefix, and a list argument matches when one of its members does
SLOT = {
    "T03": [("inside", 2, {1: "rolling_pin"}), ("fully_inside", 2, {1: "rolling_pin"})],
    "T04": [("on", 1, {2: "kitchen_cabinet_6/top"}), ("on_any", 1, {})],
    "T11": [("inside", 2, {1: "apple"}), ("fully_inside", 2, {1: "apple"}), ("on_any", 2, {1: "apple"}),
            ("on", 2, {1: "apple"})],
    "T13": [("on", 1, {2: "dining_table*"}), ("on_any", 1, {2: "dining_table*"})],
    "T15": [("covered", 2, {1: "handled_cooking_pot"})],
    "T16": [("inside", 2, {1: "school_apple"})],
    "T18": [("on", 1, {2: "dining_table*"}), ("on_any", 1, {2: "dining_table*"})],
    "T21": [("on", 1, {2: "dining_table*"}), ("on_any", 1, {2: "dining_table*"})],
    "T30": [("count_on_at_least", 1, {}), ("on", 1, {})],
}
# T07: the appliance is read from the tier (design -> tier name -> what heated)
TIER_USE = {
    "microwave_works": {"best": "kitchen_microwave", "second": "kitchen_stove"},
    "microwave_broken": {"best": "kitchen_stove"},
    "microwave_holds_pot": {"best": "kitchen_stove", "second": "kitchen_microwave"},
}
# layout -> the ideal-kind things in use there (taking one is a grab, not a hit)
IN_USE = {
    ("T07", "microwave_holds_pot"): {"kitchen_microwave"},
    ("T15", "lid_in_use"): {"pot_lid"},
    ("T15", "lid_elsewhere__covering_bowl"): {"pot_lid"},
    ("T16", "box_in_use"): {"snack_box"},
    ("T16", "box_in_cabinet__box_full"): {"snack_box"},
    ("T18", "bowl_in_use__tomatoes"): {"dinner_bowl_2"},
    ("T18", "bowl_in_use__oatmeal"): {"dinner_bowl_2"},
}
# a used thing that also appears in a "left in place" atom of the same alternative is not the one used
KEEP = ("covered",)


# why an episode ended (planner results, baseline/run_http.py and the planners' stop_reason) -> how a missed
# substitution looks: gave up, searched until the budget ran out, claimed done, or broke off on an error
GIVE_UP = re.compile(r"cannot|can't|can not|unable|impossible|could ?n[o']t|not (available|possible|found|there|"
                     r"present|in the house)|no \w+ (available|anywhere|in the house)|does ?n[o']t exist|missing|"
                     r"there is no|there are no", re.I)


def missed_kind(stop: str | None) -> str:
    s = (stop or "").strip()
    if s.startswith(("budget", "search_budget", "service_limit")):
        return "预算用完"
    if s.startswith("finish"):
        return "放弃" if GIVE_UP.search(s) else "自称完成"
    if s.startswith(("program_done", "plan_done")):
        return "自称完成"
    if s.startswith(("parse_error", "call_failed", "program_error")):
        return "出错中断"
    return "未知"


def catalog() -> dict:
    return {t["task_id"]: t for t in json.loads(TASKS.read_text())["tasks"]}


def design_of(task: dict, layout: str) -> str | None:
    return next((d for d, info in task["v6_variants"].items() if layout in info["layouts"]), None)


def reason_of(task: dict, design: str, layout: str) -> str | None:
    from benchmark.v6.substitution_stats import KIND
    kinds = KIND.get((task["task_id"][:3], design)) or {}
    case = layout[len(design) + 2:] if layout.startswith(design + "__") else layout
    return kinds.get(case, kinds.get("*"))


def side(task: dict, layout: str) -> str | None:
    """'A', 'A_hidden', 'B' or None (not part of a pair)."""
    p = PAIRS.get(task["task_id"][:3])
    design = design_of(task, layout)
    if not p or design not in p["designs"]:
        return None
    present = task["variants"][layout]["scoring"].get("ideal_present", True)
    if not present:
        return "B"
    return "A_hidden" if design in p.get("hidden", ()) else "A"


def grade_of(tid: str, name: str, objs: dict) -> str | None:
    g = GRADE[tid]
    kind = (objs.get(name) or {}).get("kind")
    for level in GRADES:
        for tok in g[level]:
            if name == tok or kind == tok or (tok.endswith("/") and name.startswith(tok)):
                return level
    return None


def _fits(arg, want: str) -> bool:
    vals = arg if isinstance(arg, list) else [arg]
    return any(isinstance(x, str) and (x.startswith(want[:-1]) if want.endswith("*") else x == want) for x in vals)


def used(tid: str, atoms: list) -> list[str]:
    """The things the atoms say were used (SLOT), in order."""
    out = []
    for a in atoms:
        if not isinstance(a, list) or not a:
            continue
        for pred, pos, fixed in SLOT.get(tid, ()):
            if a[0] != pred or len(a) <= pos or not all(len(a) > i and _fits(a[i], v) for i, v in fixed.items()):
                continue
            vals = a[pos] if isinstance(a[pos], list) else [a[pos]]
            out += [v for v in vals if isinstance(v, str)]
    return out


def choice_from_atoms(tid: str, objs: dict, atoms: list, in_use: set) -> tuple[str | None, str | None]:
    """(name, grade) of what the alternative used: the lowest grade among the used things -- in T18 the second
    container beside the ideal first bowl decides; a count over a list of one grade gives that grade."""
    names = [n for n in used(tid, atoms) if grade_of(tid, n, objs)]
    if not names:
        return None, None
    graded = [(n, grade_of(tid, n, objs)) for n in names]
    grabs = [(n, g) for n, g in graded if n in in_use]
    if grabs:
        return grabs[0][0], "in_use"
    lists = [a for a in atoms if isinstance(a, list) and a and a[0] == "count_on_at_least"]
    if lists and len({g for _, g in graded}) > 1:
        return None, None                      # a count over mixed grades does not say which
    return min(graded, key=lambda x: RANK[x[1]])


def episode_row(r: dict, task: dict) -> dict | None:
    from benchmark.v6 import object_registry as R
    from benchmark.v6.scoring import tier_goal
    tid, layout = task["task_id"][:3], r["variant"]
    s = side(task, layout)
    if s is None:
        if task["variants"][layout].get("scoring", {}).get("ideal_present", True) is False:
            return open_row(r, task, layout)
        return None
    v = task["variants"][layout]
    design = design_of(task, layout)
    objs = R.layout_objects(task, v)
    in_use = IN_USE.get((tid, layout)) or IN_USE.get((tid, design)) or set()
    tiers = {t["name"]: t for t in v["scoring"]["tiers"]}

    # the best the layout offers: the 1.0 tier's own alternatives (the review chose it as the best there is)
    if tid == "T07":
        best = "ideal" if TIER_USE[design]["best"] == "kitchen_microwave" else "moderate"
    else:
        g0 = tier_goal(v["scoring"]["tiers"][0], task, layout)
        levels = []
        for alt in g0.get("any") or [[]]:
            atoms = (g0.get("all") or []) + alt
            if all(n in objs or "/" in n for n in used(tid, atoms)):      # an alternative of things in the scene
                levels.append(choice_from_atoms(tid, objs, atoms, in_use)[1])
        levels = [lv for lv in levels if lv in RANK]
        best = max(levels, key=RANK.get) if levels else None

    sc = r.get("score") or {}
    success = bool(r.get("task_success")) and not r.get("incomplete") and not r.get("crash")
    name = grade = None
    source = None
    if success and sc.get("tier") in tiers:
        if tid == "T07":
            name = TIER_USE[design].get(sc["tier"])
            grade = "in_use" if name in in_use else grade_of(tid, name, {}) if name else None
        else:
            g = tier_goal(tiers[sc["tier"]], task, layout)
            atoms = (g.get("all") or []) + (sc.get("branch_atoms") or ((g.get("any") or [[]])[0]
                                                                       if len(g.get("any") or []) <= 1 else []))
            name, grade = choice_from_atoms(tid, objs, atoms, in_use)
        source = "outcome"
    if grade is None:                          # failed (or a count over mixed grades): the last candidate held
        for c in reversed(r.get("calls") or []):
            held = [h for h in ((c.get("state") or {}).get("held") or []) if h]
            hit = [(h, grade_of(tid, h, objs)) for h in held if grade_of(tid, h, objs)]
            if hit:
                name, grade = hit[0]
                grade = "in_use" if name in in_use else grade
                source = "last_held"
                break
    task_items = {n for alt in (tier_goal(v["scoring"]["tiers"][0], task, layout).get("any") or [[]])
                  for a in alt + (tier_goal(v["scoring"]["tiers"][0], task, layout).get("all") or [])
                  if isinstance(a, list) for n in a[1:] if isinstance(n, str)}
    other = None
    if grade is None:
        for c in reversed(r.get("calls") or []):
            held = [h for h in ((c.get("state") or {}).get("held") or []) if h and h not in task_items]
            if held:
                other = held[0]
                break
    route = task["routes"].get(task["oracle"].get(layout) or "", {}).get("steps") or []
    a_ref = sum(1 for st in route if st.get("expect", "ok") != "fail" and st.get("role") != "unwind") or None
    calls = r.get("skill_calls", len(r.get("calls") or []))
    switched = grade in ("moderate", "bad") or (grade is None and other is not None)
    row = {"task": task["task_id"], "design": design, "layout": layout, "seed": r.get("seed"), "side": s,
           "reason": reason_of(task, design, layout) if s == "B" else None,
           "success": success, "score": sc.get("score", 0.0) if success else 0.0, "tier": sc.get("tier"),
           "chosen": name, "grade": grade, "chosen_from": source, "else_held": other if grade is None else None,
           "best_available": best, "calls": calls, "a_ref": a_ref, "stop": r.get("_stop"),
           "E": (a_ref / max(calls, a_ref)) if success and a_ref else 0.0}
    if s.startswith("A"):
        row["false_switch"] = switched
        row["right"] = grade == "ideal"
    else:
        row["missed_switch"] = grade is None and other is None
        row["missed_kind"] = missed_kind(r.get("_stop")) if row["missed_switch"] else None
        row["grab"] = grade == "in_use"
        row["hit"] = grade is not None and grade == best
        row["bad"] = grade == "bad"
        row["else"] = grade is None and other is not None
        row["right"] = row["hit"]
    row["strict"] = success and row["right"]
    return row


def open_row(r: dict, task: dict, layout: str) -> dict:
    """A layout where the ideal cannot be used but no grade table covers the task (``B_open``): read by tier alone --
    the 1.0 tier is the best substitute the layout offers (the review set it), a lower tier a poorer one."""
    v = task["variants"][layout]
    design = design_of(task, layout)
    sc = r.get("score") or {}
    success = bool(r.get("task_success")) and not r.get("incomplete") and not r.get("crash")
    score_ = sc.get("score", 0.0) if success else 0.0
    route = task["routes"].get(task["oracle"].get(layout) or "", {}).get("steps") or []
    a_ref = sum(1 for st in route if st.get("expect", "ok") != "fail" and st.get("role") != "unwind") or None
    calls = r.get("skill_calls", len(r.get("calls") or []))
    hit = success and score_ == 1.0
    return {"task": task["task_id"], "design": design, "layout": layout, "seed": r.get("seed"), "side": "B_open",
            "reason": reason_of(task, design, layout), "ideal": v["scoring"].get("ideal_zh"),
            "success": success, "score": score_, "tier": sc.get("tier"), "chosen": None, "grade": None,
            "chosen_from": "tier", "else_held": None, "best_available": None, "calls": calls, "a_ref": a_ref,
            "stop": r.get("_stop"), "E": (a_ref / max(calls, a_ref)) if success and a_ref else 0.0,
            "missed_switch": not success, "missed_kind": missed_kind(r.get("_stop")) if not success else None,
            "grab": False, "hit": hit, "bad": success and 0 < score_ < 1.0, "else": False,
            "right": hit, "strict": hit}


# ------------------------------------------------------------------------------------------------ reading runs
def results(root: Path, native: Path | None):
    for path in sorted(root.rglob("result.json")):
        try:
            r = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(r, dict) or "task_id" not in r:
            continue
        stop = r.get("stop_reason")
        if stop == "planner_done":                 # the planner's own reason (baseline/report.py does the same)
            stop = (r.get("planner_summary") or {}).get("stop_reason") or stop
        if "calls" not in r and native is not None and r.get("exp_id"):
            n = native / r["task_id"] / r["exp_id"] / "result.json"
            if not n.is_file():
                continue
            r = json.loads(n.read_text())
        r["_stop"] = stop if stop and stop != "planner_done" else None
        if "calls" in r and "variant" in r:
            yield path, r


def pass_at(n: int, c: int, k: int) -> tuple[float | None, float | None]:
    if n < k:
        return None, None
    return 1 - comb(n - c, k) / comb(n, k), comb(c, k) / comb(n, k)


def ratio(rows, key) -> str:
    n = len(rows)
    return f"{sum(bool(r[key]) for r in rows)}/{n} ({sum(bool(r[key]) for r in rows) / n:.0%})" if n else "—"


def summarize(label: str, rows: list[dict], k: int) -> list[str]:
    out = [f"## {label}", ""]
    a = [r for r in rows if r["side"] == "A"]
    ah = [r for r in rows if r["side"] == "A_hidden"]
    b = [r for r in rows if r["side"] == "B"]
    out += ["| 侧 | 局数 | 误替代率 | 漏替代率 | 抢占率 | 命中率 | bad 率 | else 率 | 完成率 | 严格成功率 | 平均 E |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    mean_e = lambda rs: f"{sum(r['E'] for r in rs) / len(rs):.2f}" if rs else "—"  # noqa: E731
    for name, rs in (("A 原物体在", a), ("A 原物体藏着", ah)):
        out.append(f"| {name} | {len(rs)} | {ratio(rs, 'false_switch')} | — | — | — | — | — | {ratio(rs, 'success')} | "
                   f"{ratio(rs, 'strict')} | {mean_e(rs)} |")
    out.append(f"| B 原物体用不了 | {len(b)} | — | {ratio(b, 'missed_switch')} | {ratio(b, 'grab')} | {ratio(b, 'hit')} | "
               f"{ratio(b, 'bad')} | {ratio(b, 'else')} | {ratio(b, 'success')} | {ratio(b, 'strict')} | {mean_e(b)} |")
    kinds = defaultdict(int)
    for r in b:
        if r.get("missed_kind"):
            kinds[r["missed_kind"]] += 1
    if kinds:
        out += ["", "漏替代细分（按结束原因；只读原生结果时没有原因，记为未知）：" +
                "，".join(f"{k} {v}" for k, v in sorted(kinds.items(), key=lambda x: -x[1]))]
    bo = [r for r in rows if r["side"] == "B_open"]
    if bo:
        out += ["", "其余替代局（不在配对表里，只按档判：1.0 档 = 这个布局最好的替代，0.3–0.6 档 = 次一档的替代，"
                "失败 = 没替代成）：", "",
                "| 局数 | 失败（漏替代或做砸） | 1.0 档替代 | 次一档替代 | 完成率 | 平均 E |", "|---|---|---|---|---|---|",
                f"| {len(bo)} | {ratio(bo, 'missed_switch')} | {ratio(bo, 'hit')} | {ratio(bo, 'bad')} | "
                f"{ratio(bo, 'success')} | {mean_e(bo)} |"]
        b = b + bo
    out += ["", "B 按不可用原因：", "", "| 原因 | 局数 | 漏替代率 | 抢占率 | 命中率 | 完成率 | 严格成功率 |", "|---|---|---|---|---|---|---|"]
    by = defaultdict(list)
    for r in b:
        by[r["reason"] or "—"].append(r)
    for reason, rs in sorted(by.items()):
        out.append(f"| {reason} | {len(rs)} | {ratio(rs, 'missed_switch')} | {ratio(rs, 'grab')} | {ratio(rs, 'hit')} | "
                   f"{ratio(rs, 'success')} | {ratio(rs, 'strict')} |")
    groups = defaultdict(list)
    for r in rows:
        groups[r["task"][:3], r["design"]].append(r["strict"])
    out += ["", f"稳定性（同一设计的各 seed 算重复，严格成功；k = {k}）：", "",
            "| 任务 | 设计 | n | pass@1 | pass@k | pass^k |", "|---|---|---|---|---|---|"]
    for (t, d), xs in sorted(groups.items()):
        n, c = len(xs), sum(xs)
        pk, pk_all = pass_at(n, c, k)
        f = lambda x: "—" if x is None else f"{x:.2f}"  # noqa: E731
        out.append(f"| {t} | {d} | {n} | {c / n:.2f} | {f(pk)} | {f(pk_all)} |")
    unknown = [r for r in rows if r["grade"] is None and not r["success"] and r["task"][:3] in ("T03", "T11")]
    if unknown:
        out += ["", f"T03/T11 失败局里有 {len(unknown)} 局看不出选了哪个容器（容器不会被拿起），计入漏替代或 else 时有偏差。"]
    return out + [""]


def pairs_table(cat: dict) -> list[str]:
    out = ["| 任务 | 设计 | 布局 | 侧 | 原因 | 本布局最好一档 | 指令 |", "|---|---|---|---|---|---|---|"]
    for t in cat.values():
        if t["task_id"][:3] not in PAIRS:
            continue
        for d in PAIRS[t["task_id"][:3]]["designs"]:
            for lid in t["v6_variants"][d]["layouts"]:
                row = episode_row({"variant": lid, "calls": [], "task_success": False}, t)
                ins = t["variants"][lid].get("instruction") or t["instruction"]
                out.append(f"| {t['task_id'][:3]} | {d} | {lid} | {row['side']} | {row['reason'] or ''} | "
                           f"{row['best_available']} | {ins} |")
    return out


def batch(cat: dict) -> list[dict]:
    jobs = []
    for t in cat.values():
        p = PAIRS.get(t["task_id"][:3])
        if not p:
            continue
        for d in p["designs"]:
            for seed, lid in sorted(t["v6_variants"][d]["seeds"].items(), key=lambda x: int(x[0])):
                jobs.append({"task": t["task_id"], "variant": lid, "seed": int(seed), "v6_variant": d,
                             "side": side(t, lid)})
    return jobs


# the first substitution run (11-25, user: "pick the episodes that have a substitution, like T03"): layouts whose
# instruction names the thing (or the place it goes), the thing cannot be used -- missing, taken, too small -- and
# another kind of thing does the job.  Too small or full (11-25, user: more of these): T03's small bin, T04's plastic
# cup for an iced drink, T10's and T12's full bins, T16's full box, T23's and T29's full toy box.  Left out: the ideal not named (T07 "what you used", T24 "something to eat",
# T26 "where his toys are kept"), a table or shelf that is full (a place, not a thing), T18 door_stuck.
SUBSTITUTION_LAYOUTS = {
    "T02": ["block_put_away__gone_toy_block", "block_put_away__gone_duck"],
    "T03": ["no_bin_substitute__basket", "no_bin_substitute__tray", "utensils_apart__bin_full_tray",
            "utensils_apart__bin_full_basket", "utensils_apart__bin_full_fruit",
            "small_bin_or_bedroom_bin__basket_in_bedroom"],
    "T04": ["no_cup", "no_cup_mug_away", "no_cup_kid", "two_guests__mug", "two_guests__kid_cup",
            "x6_gd_cup_in_cabinets__plastic_only"],
    "T05": ["no_pen_pencil_in_use", "check_desk_first__pen_in_use", "x6_gd_pen_or_pencil_cabinets__pen_in_use"],
    "T09": ["lid_missing", "tomato_in_fridge__big_tomato", "pot_in_dining_room__spare_pot"],
    "T10": ["trash_moved__trash_full"],
    "T11": ["basket_missing", "basket_gone_bowl_there"],
    "T12": ["bins_capacity__side_left_full", "bins_capacity__apart_full_on_tv", "bins_capacity__half_bin_and_tray"],
    "T13": ["no_cup"],
    "T15": ["no_lid", "lid_in_use", "lid_elsewhere__covering_bowl"],
    "T16": ["no_box", "box_in_use", "box_in_cabinet__box_full"],
    "T17": ["hide_lid_in_use"],
    "T18": ["one_bowl__glass_box", "one_bowl__mug", "bowl_in_use__tomatoes", "bowl_in_use__oatmeal"],
    "T21": ["no_tissue"],
    "T22": ["basket_missing", "tray_elsewhere__orange_in_it", "tray_elsewhere__bowls_in_it"],
    "T23": ["by_kind__bin_full", "belongs_on_floor__bin_full"],
    "T25": ["cups_for_two__none_one_inside"],
    "T28": ["where_his_cup_is__no_kid_cup"],
    "T29": ["belongs_on_table__no_toy_box", "several__bin_full"],
    "T30": ["no_bowl", "bowl_put_away__mug_inside", "how_many__two_bowls", "bowls_in_cabinet__one_inside"],
}
SUBSET_PER_LAYOUT = 2


def subset(cat: dict) -> list[dict]:
    """The substitution layouts, each on its lowest SUBSET_PER_LAYOUT seeds."""
    jobs = []
    for t in cat.values():
        for lid in SUBSTITUTION_LAYOUTS.get(t["task_id"][:3], ()):
            d = design_of(t, lid)
            seeds = sorted(int(s) for s, x in t["v6_variants"][d]["seeds"].items() if x == lid)
            for seed in seeds[:SUBSET_PER_LAYOUT]:
                jobs.append({"task": t["task_id"], "variant": lid, "seed": seed, "v6_variant": d,
                             "side": side(t, lid) or "B_open", "reason": reason_of(t, d, lid),
                             "ideal": t["variants"][lid]["scoring"].get("ideal_zh")})
    return jobs


def check_pairs(cat: dict) -> list[str]:
    """Problems with the tables: a design that is not there, a pair whose texts differ, a B layout with no
    graded best, a candidate named in a grade that no layout has."""
    bad = []
    for tid, p in PAIRS.items():
        t = next(x for x in cat.values() if x["task_id"][:3] == tid)
        texts = set()
        sides = set()
        for d in p["designs"]:
            if d not in t["v6_variants"]:
                bad.append(f"{tid}: no design {d}")
                continue
            for lid in t["v6_variants"][d]["layouts"]:
                texts.add(t["variants"][lid].get("instruction") or t["instruction"])
                row = episode_row({"variant": lid, "calls": [], "task_success": False}, t)
                sides.add(row["side"][0])
                if row["best_available"] is None:
                    bad.append(f"{tid} {lid}: the best tier names no graded candidate")
                if row["side"] == "A" and row["best_available"] != "ideal":
                    bad.append(f"{tid} {lid}: an A layout whose best is {row['best_available']}")
                if row["side"] == "B" and row["best_available"] == "ideal":
                    bad.append(f"{tid} {lid}: a B layout whose best is the ideal")
        if len(texts) != 1:
            bad.append(f"{tid}: the pair's instructions differ: {sorted(texts)}")
        if sides != {"A", "B"}:
            bad.append(f"{tid}: sides {sorted(sides)}")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pairs", action="store_true", help="print the A/B table and check it")
    ap.add_argument("--batch", help="write the run_http batch of every pair layout and seed to this path")
    ap.add_argument("--subset", help="write the substitution-only batch (SUBSTITUTION_LAYOUTS) here")
    ap.add_argument("--run", action="append", default=[], help="LABEL=DIR of results (repeatable)")
    ap.add_argument("--native", help="the simulator's native results, for planner results without calls")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--out", help="write the markdown report here")
    ap.add_argument("--json", help="write one JSON row per episode here")
    a = ap.parse_args(argv)
    cat = catalog()
    if a.pairs:
        print("\n".join(pairs_table(cat)))
        problems = check_pairs(cat)
        print("\n".join(problems) if problems else "\npairs ok")
        return 1 if problems else 0
    if a.batch:
        jobs = batch(cat)
        Path(a.batch).write_text(json.dumps(jobs, indent=1) + "\n")
        print(f"wrote {a.batch}: {len(jobs)} episodes")
        return 0
    if a.subset:
        jobs = subset(cat)
        Path(a.subset).write_text(json.dumps(jobs, indent=1) + "\n")
        print(f"wrote {a.subset}: {len(jobs)} episodes")
        return 0
    if not a.run:
        ap.error("--pairs, --batch, --subset or --run")
    lines = ["# ZenoBench-Sub 替代指标", "", "由 `python -m benchmark.v6.substitution_eval` 生成。", ""]
    rows_out = []
    for spec in a.run:
        label, _, d = spec.partition("=")
        seen, rows = set(), []
        for _, r in results(Path(d), Path(a.native) if a.native else None):
            t = cat.get(r["task_id"])
            key = (r["task_id"], r["variant"], r.get("seed"), r.get("exp_id"))
            if t is None or key in seen:
                continue
            seen.add(key)
            row = episode_row(r, t)
            if row is not None:
                rows.append({**row, "run": label})
        lines += summarize(f"{label}（{len(rows)} 局）", rows, a.k)
        rows_out += rows
    text = "\n".join(lines)
    if a.out:
        Path(a.out).write_text(text + "\n")
    print(text)
    if a.json:
        Path(a.json).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
