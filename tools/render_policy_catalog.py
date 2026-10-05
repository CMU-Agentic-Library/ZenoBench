"""Render the human-readable policy inventory from its JSON source.

    python tools/render_policy_catalog.py          # update docs/POLICY_CATALOG.md
    python tools/render_policy_catalog.py --check  # fail if the document is stale
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "zeno_skills/policies/catalog.json"
OUTPUT = ROOT / "docs/POLICY_CATALOG.md"
GROUPS = {
    "navigation": "导航与携物移动",
    "posture": "躯干与姿态",
    "grasp": "抓取",
    "placement": "放置",
    "articulation": "门与抽屉",
    "contact": "推动与接触",
    "appliance": "按钮与电器",
    "arm": "右臂运动",
    "gripper": "右夹爪",
    "mobile_manipulation": "移动中操作",
    "manipulation": "物体姿态修正",
    "bimanual": "双臂协作",
}


def render(catalog):
    rows = catalog["policies"]
    counts = Counter(row["status"] for row in rows)
    text = [
        "# Zeno House policy 能力目录",
        "",
        f"本目录列出 **{len(rows)} 个目标能力**。状态记录的是当前代码与物理验证程度，",
        "独立代码入口不等于在目标场景物理通过。通用分发入口 `pick/place/open/close/navigate`",
        "以及顺序组合 `pick_and_carry`、`microwave_door_cycle` 不计入本目录。",
        "",
        f"- `verified`（{counts['verified']}）：可调用，且对应物理动作通过过 Isaac Sim smoke run。",
        f"- `callable`（{counts['callable']}）：有独立 OOP 入口，但尚无该入口成功通过 Isaac Sim 的物理验证；部分路线正在调试。",
        f"- `embedded`（{counts['embedded']}）：动作片段已在较大 policy 内执行，尚无独立入口和结果检查。",
        f"- `planned`（{counts['planned']}）：当前没有完成该动作的控制器。",
        "",
        "`pick_while_moving` 已在 Isaac Sim 中抓起 toy_block：闭爪与抬起均发生在底盘运动期间。",
        "`pick_and_carry` 则是先抓取后移动。`place_while_moving` 已在底盘继续移动时释放苹果并验证桌面支撑。",
        "`bimanual_flat_pick` 曾在 Isaac Sim 中短时抬起书本，但左手在后续携带中滑脱，稳定抓持仍在调试。",
        "",
        "机器可读源文件：[catalog.json](../zeno_skills/policies/catalog.json)。",
        "`input` 和 `effect` 是能力摘要，后续 contract 的 `requires/achieves/verifier`",
        "需要逐项细化，不能直接把本目录当作可执行 contract。",
        "",
    ]
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["group"]].append(row)
    for group, group_rows in grouped.items():
        text.extend([f"## {GROUPS[group]}", "", "| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |", "|---|---|---|---|---|---|"])
        for row in group_rows:
            route = row.get("executor") or row.get("basis") or row.get("gap", "")
            if row.get("caveat"):
                route += "；" + row["caveat"]
            route = route.replace("|", "\\|")
            text.append(f"| `{row['id']}` | {row['description']} | `{row['input']}` | `{row['effect']}` | `{row['status']}` | {route} |")
        text.append("")
    text.extend(["## 验证记录", "", "本地仿真 smoke 记录（日期和动作；`runs/` 默认不纳入 Git）：", ""])
    for row in rows:
        if row.get("verification"):
            text.append(f"- `{row['id']}`：{row['verification']}")
    text.append("")
    return "\n".join(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog = json.loads(SOURCE.read_text())
    rendered = render(catalog)
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != rendered:
            raise SystemExit(f"stale catalog document: {OUTPUT}")
    else:
        OUTPUT.write_text(rendered)
        print(OUTPUT)


if __name__ == "__main__":
    main()
