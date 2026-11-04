"""Per variant: the success conditions (goal atoms, in Chinese) and the reference skill call order (oracle route).

    python benchmark/v6/success_routes.py      # SUCCESS_ROUTES_zh.md (tasks.json and VARIANTS_zh.md must be current)

The situation of each variant is taken from VARIANTS_zh.md; a variant with several layouts lists one route per
layout (the seed picks the layout).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAT = {"control": "对照", "action": "Action", "task": "Task", "action_task": "Action + Task"}


def _names(x):
    return "、".join(f"`{n}`" for n in x) if isinstance(x, list) else f"`{x}`"


ATOMS = {
    "on": lambda o, s: f"{_names(o)} 在 `{s}` 上",
    "upright": lambda o: f"{_names(o)} 立着",
    "inside": lambda o, c: f"{_names(o)} 在 `{c}` 里",
    "fully_inside": lambda o, c: f"{_names(o)} 完全在 `{c}` 里（没有露出边沿）",
    "near_start": lambda o, tol, *u: f"{_names(o)} 没被挪动（离开局位置不超过 {round(tol * 100)} cm）",
    "is_closed": lambda a: f"`{a}` 关着",
    "grouped": lambda kinds, s, d: f"{'、'.join(kinds)} 在 `{s}` 上摆在一起（彼此不超过 {round(d * 100)} cm）",
    "temperature_at_least": lambda o, c: f"{_names(o)} 温度至少 {c} °C",
    "on_top_of": lambda a, b: f"{_names(a)} 叠在 {_names(b)} 上",
    "covered": lambda p, lid: f"{_names(p)} 盖着 {_names(lid)}",
    "not heating": lambda a: f"`{a}` 已经停止加热",
    "away_from_edge": lambda o, d: f"{_names(o)} 离台面边缘至少 {round(d * 100)} cm",
    "stirred": lambda o: f"{_names(o)} 搅拌过",
    "observed": lambda o: f"看到过 {_names(o)}",
    "hidden": lambda o: f"{_names(o)} 藏好了（从房间里看不到）",
    "wiped": lambda s: f"`{s}` 擦过",
    "not on_floor": lambda o: f"{_names(o)} 不在地上",
    "clear_of": lambda o, others, d: f"{_names(o)} 离这些东西都至少 {round(d * 100)} cm：{_names(others)}",
    "near_any": lambda o, others, d: f"{_names(o)} 离其中至少一个不超过 {round(d * 100)} cm：{_names(others)}",
    "front_visible": lambda o: f"{_names(o)} 从房间里看得见（前面没有更高的东西挡着）",
    "flipped": lambda o: f"{_names(o)} 翻过面",
    "object_rolled": lambda o: f"{_names(o)} 滚过",
    "count_on_at_least": lambda objs, s, k: f"这 {len(objs)} 件中至少 {k} 件还在 `{s}` 上：{_names(objs)}",
    "hand_empty": lambda h: "手里空着",
}


def atom(a):
    f = ATOMS.get(a[0])
    try:
        return f(*a[1:]) if f else f"`{json.dumps(a, ensure_ascii=False)}`"
    except TypeError:
        return f"`{json.dumps(a, ensure_ascii=False)}`"


def goal_lines(g, depth=0):
    pad = "  " * depth
    if isinstance(g, dict):                       # {"all": [atom | goal], "any": [[atom, ...], ...]}
        out, merged = [], {}
        for x in g.get("all", []):          # one line for "these stay put" / "these stand upright"
            if isinstance(x, list) and x[0] in ("near_start", "upright") and isinstance(x[1], str):
                key = (x[0], *x[2:])
                if key not in merged:
                    merged[key] = [x[0], [], *x[2:]]
                    out.append(merged[key])
                merged[key][1].append(x[1])
            else:
                out.append(x)
        out = [line for x in out for line in goal_lines(x, depth)]
        if g.get("any"):
            out.append(f"{pad}- 满足下面任意一组：")
            for i, group in enumerate(g["any"], 1):
                out.append(f"{pad}  - 第 {i} 组：")
                for x in group:
                    out += goal_lines(x, depth + 2)
        return out
    return [f"{pad}- {atom(g)}"]


def step(s):
    def val(x):
        if isinstance(x, list):
            return "[" + ", ".join(val(v) for v in x) + "]"
        return str(round(x, 3)) if isinstance(x, float) else str(x)
    args = ", ".join(f"{k}={val(x)}" for k, x in s["args"].items())
    role = {"recover": "（补救）", "alternative": "（换做法）"}.get(s.get("role"), "")
    return f"`{s['skill']}({args})`{role}"


def situations():
    """variant -> situation text, from the VARIANTS_zh.md tables."""
    out, task = {}, None
    for line in (HERE / "VARIANTS_zh.md").read_text().splitlines():
        m = re.match(r"## (T\d+)", line)
        if m:
            task = m.group(1)
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("| ") else []
        if task and len(cells) >= 3 and cells[0] not in ("variant", "记号") and not cells[0].startswith("-"):
            out[(task, cells[0])] = cells[2]
    return out


def main():
    doc = json.loads((HERE / "tasks.json").read_text())
    sit = situations()
    lines = ["# ZenoBench v6：每个 variant 的成功条件和参考调用顺序", "",
             "由 `python benchmark/v6/success_routes.py` 从 `tasks.json` 生成。",
             "",
             "- **成功条件**：一局结束时由 GT 状态判定，全部满足才算成功；中间怎么做不限。",
             "- **参考调用顺序**：oracle 路线，即按技能 contract 调用、能走通的一种做法，不是唯一解。"
             "标\"（补救）\"的是发现情况后多做的一步。机器人只会右手。",
             "- 有多种摆法的 variant 每种摆法列一条路线，seed 决定用哪种摆法。",
             "- 物体名保留代码里的 id。", ""]
    for t in doc["tasks"]:
        tid = t["task_id"].split("_")[0]
        lines += ["---", "", f"## {t['task_id']}", "", f"> {t.get('instruction_zh') or t['instruction']}", ""]
        for vid, info in t["v6_variants"].items():
            cat = CAT[t["v6_tracks"][vid]["category"]]
            v0 = t["variants"][info["layouts"][0]]
            lines += [f"### {vid}（{cat}）", ""]
            if (tid, vid) in sit:
                lines += [f"**情况**：{sit[(tid, vid)]}", ""]
            instr = v0.get("instruction_zh") or v0.get("instruction")
            if instr and instr != (t.get("instruction_zh") or t["instruction"]) and instr != t["instruction"]:
                lines += [f"**指令**：{instr}", ""]
            goals = {json.dumps(t["variants"][lid].get("goal") or t["goal"]) for lid in info["layouts"]}
            lines += ["**成功条件**：", ""]
            for g in sorted(goals):
                if len(goals) > 1:
                    lines.append("- 摆法不同，条件也不同：")
                lines += goal_lines(json.loads(g), 1 if len(goals) > 1 else 0)
            lines += ["", "**参考调用顺序**：", ""]
            for lid in info["layouts"]:
                steps = t["routes"][t["oracle"][lid]]["steps"]
                tag = f"摆法 `{lid.split('__', 1)[-1]}`：" if len(info["layouts"]) > 1 else ""
                lines.append(f"{'- ' + tag if tag else ''}" + " → ".join(
                    f"{i}. {step(s)}" for i, s in enumerate(steps, 1)))
            lines.append("")
    (HERE / "SUCCESS_ROUTES_zh.md").write_text("\n".join(lines) + "\n")
    print(f"wrote SUCCESS_ROUTES_zh.md: {sum(len(t['v6_variants']) for t in doc['tasks'])} variants")


if __name__ == "__main__":
    main()
