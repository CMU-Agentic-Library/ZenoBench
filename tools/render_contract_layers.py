"""Render the eight contract cards and all 60 catalog policy references.

    python3 tools/render_contract_layers.py
    python3 tools/render_contract_layers.py --check

The SVG is generated from the importable ContractSpec registry, its explicit
support-policy references, and the policy catalog. PNG preview rendering uses
local headless Chrome when present.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zeno_skills.contracts import policy_contract_relations
from zeno_skills.interface_ids import CONTRACT_PUBLIC_IDS
CATALOG = ROOT / "zeno_skills/policies/catalog.json"
SVG = ROOT / "docs/contract_layers.svg"
PNG = ROOT / "docs/contract_layers_preview.png"

ORDER = ("navigate.v1", "pick.v1", "place.v1", "open.v1",
         "close.v1", "push.v1", "click.v1", "set_posture.v1")
META = {
    "navigate.v1": ("底盘移动与持物导航", "pose / object?", "路径可通行；持物匹配", "base_at(pose)", "到位 / 阻挡 / 滑脱", "空手 / 持物 / 双手携带", "底盘位姿与抓持"),
    "pick.v1": ("按物品标注选择右手抓取", "object / route?", "空手；接触点可达", "held(object) + lifted", "抓稳 / 移位 / 滑脱", "顶捏 / 杯沿 / 杯把 / 腔内 / 移动中", "物体抬升与夹爪"),
    "place.v1": ("将右手物品放到目标", "object / target", "已持物；目标可达", "on / inside", "落稳 / 落偏 / 掉落", "表面 / 容器 / 微波炉 / 移动中", "最终几何与空手"),
    "open.v1": ("打开门或抽屉", "articulated", "关节标注；路线可达", "joint_open_enough", "打开 / 部分打开", "手柄 / 动力 / 铰链 / 抽屉", "实测关节开度"),
    "close.v1": ("关闭门或抽屉", "articulated", "关闭路径无阻挡", "closed(articulated)", "关上 / 部分关闭", "手柄 / 动力", "实测关节闭合"),
    "push.v1": ("沿支撑面推动物体", "object / direction", "物体在支撑面上", "measured displacement", "移动 / 跌落 / 未动", "背推 / 顶部拖动", "动作前后位移"),
    "click.v1": ("按下电器按钮", "appliance / button", "按钮可达；启动前置满足", "button_pressed", "按下 / 未触达", "微波炉门 / 启动", "本次接触与电器状态"),
    "set_posture.v1": ("调整机器人躯干与右臂", "component / target", "关节限位；路径无碰撞", "joint_at(target)", "到位 / 中途阻挡", "收臂 / 躯干 / 腰部", "实测关节或 TCP"),
}

WIDTH = 2080
COL_WIDTH = 490
GAP = 24
CARD_H = 262
PILL_H = 26
PILL_GAP = 4
PANEL_HEAD = 49
POLICY_GAP = 44
ROW_GAP = 42
ROW_TOP = 147


def esc(value):
    return html.escape(str(value), quote=True)


def tag(kind, attrs=None, content=""):
    attrs = attrs or {}
    fields = " ".join(f'{key}="{esc(value)}"' for key, value in attrs.items())
    return f"<{kind}{' ' + fields if fields else ''}>{content}</{kind}>"


def text(x, y, value, cls, **attrs):
    return tag("text", {"x": x, "y": y, "class": cls, **attrs}, esc(value))


def rect(x, y, w, h, fill, stroke="none", radius=0, **attrs):
    return tag("rect", {"x": x, "y": y, "width": w, "height": h, "rx": radius,
                        "fill": fill, "stroke": stroke, **attrs})


def render(catalog):
    # Historical family-contract view: only the original 64 entries; newer
    # policies are reached through the verb Skill Contracts (POLICY_COVERAGE.md).
    rows = [row for row in catalog["policies"]
            if row["id"] != "wait_for_temperature" and int(row["policy_id"].split("_")[1]) <= 64]
    if len(rows) != 63 or len({row["id"] for row in rows}) != 63:
        raise ValueError("contract diagram requires the 63 unique policy catalog entries")
    relations = policy_contract_relations(rows)
    by_id = {row["id"]: row for row in rows}
    counts = Counter(row["status"] for row in rows)
    if set(counts) - {"verified", "callable"}:
        raise ValueError("diagram only represents independent callable entries")
    layout = []
    cursor = ROW_TOP
    for group in (ORDER[:4], ORDER[4:]):
        largest = max(len(relations[c]["direct"]) + len(relations[c]["support"]) for c in group)
        panel_h = PANEL_HEAD + largest * (PILL_H + PILL_GAP) + 12
        layout.append((cursor, panel_h, group))
        cursor += CARD_H + POLICY_GAP + panel_h + ROW_GAP
    height = cursor + 76
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title desc">',
           tag("title", {"id": "title"}, "八个兼容 family contract 与六十三个底层 policy 的实现关系"),
           tag("desc", {"id": "desc"}, "图展示第三层 Contract 与第四层底层 Policy。实心方块是 ContractSpec.executor 的直接类绑定；空心圆是不会自动执行的支撑动作引用。绿色点表示至少一个 Isaac Sim 场景已验证，蓝色点表示独立入口仍待物理验证。上层 Skill 子图已有静态编译接口，自动规划器尚未实现。"),
           '''<defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="9" markerHeight="9" orient="auto"><path d="M0 10 L5 0 L10 10 Z" fill="#7350b8"/></marker></defs>''',
           '''<style>text{font-family:Inter,"Noto Sans CJK SC","Microsoft YaHei",Arial,sans-serif;fill:#263047}.title{font-size:31px;font-weight:750}.subtitle{font-size:18px;fill:#5b6574}.lane{font-size:20px;font-weight:750}.card-title{font-size:23px;font-weight:700;fill:#fff}.card-desc{font-size:17px;font-weight:650}.key{font-size:14px;font-weight:700;fill:#b45324}.value{font-size:14px;fill:#39465a}.panel-title{font-size:18px;font-weight:700;fill:#6744a6}.policy{font-size:16px;font-weight:550}.legend{font-size:17px;fill:#536071}</style>''',
           rect(0, 0, WIDTH, height, "#fff"),
           text(34, 51, "第3层 Contract ↔ 第4层底层 Policy", "title"),
           text(34, 83, f"8 个兼容 family contract · 63 个底层 policy · {counts['verified']} verified / {counts['callable']} callable · 38 direct / 25 support", "subtitle"),
           text(34, 112, "第三层 Contract → 第四层 Policy；实心方块＝直接绑定，空心圆＝支撑引用（不自动执行）；上层技能子图尚待扩展", "subtitle")]
    for row_index, (top, panel_h, group) in enumerate(layout):
        panel_top = top + CARD_H + POLICY_GAP
        out += [rect(16, top-31, WIDTH-32, CARD_H+48, "#fff5ee", radius=16),
                rect(16, panel_top-31, WIDTH-32, panel_h+46, "#f6f2fc", radius=16),
                rect(16, top-31, 7, CARD_H+48, "#c75e2d", radius=3),
                rect(16, panel_top-31, 7, panel_h+46, "#764dc0", radius=3),
                text(38, top-5, f"第3层 Contract · 第 {row_index+1} 组", "lane", style="fill:#a94c22"),
                text(38, panel_top-6, f"第4层 Policy · 引用关系第 {row_index+1} 组", "lane", style="fill:#6841a8")]
        for col, contract_id in enumerate(group):
            x = 32 + col * (COL_WIDTH + GAP)
            direct = relations[contract_id]["direct"]
            support = relations[contract_id]["support"]
            meta = META[contract_id]
            out += [rect(x, top, COL_WIDTH, CARD_H, "#fffdfb", "#c56130", 12, **{"stroke-width": 2}),
                    rect(x, top, COL_WIDTH, 43, "#bf592b", radius=12),
                    rect(x, top+30, COL_WIDTH, 13, "#bf592b"),
                    text(x+COL_WIDTH/2, top+29,
                         f"{CONTRACT_PUBLIC_IDS[contract_id]} · {contract_id}",
                         "card-title", **{"text-anchor": "middle"}),
                    text(x+15, top+68, meta[0], "card-desc")]
            for idx, (key, value) in enumerate(zip(("inputs", "requires", "achieves", "outcomes", "executor", "verifier"), meta[1:])):
                y = top+97+idx*27
                out += [text(x+16, y, key, "key"), text(x+101, y, value, "value")]
            out += [tag("path", {"d": f"M {x+COL_WIDTH/2} {panel_top-5} L {x+COL_WIDTH/2} {top+CARD_H+6}",
                                  "fill": "none", "stroke": "#7350b8", "stroke-width": 2.6,
                                  "marker-end": "url(#arrow)"})]
            out += [rect(x, panel_top, COL_WIDTH, panel_h, "#fff", "#9270cf", 13,
                         **{"stroke-width": 2, "stroke-dasharray": "7 5"}),
                    text(x+15, panel_top+31, f"{CONTRACT_PUBLIC_IDS[contract_id]} · {len(direct)} direct / {len(support)} support", "panel-title")]
            for n, policy_id in enumerate((*direct, *support)):
                row = by_id[policy_id]
                y = panel_top+PANEL_HEAD+n*(PILL_H+PILL_GAP)
                is_direct = n < len(direct)
                out.append(rect(x+12, y, COL_WIDTH-24, PILL_H,
                                "#f1eafd" if is_direct else "#fff",
                                "#916fc8" if is_direct else "#bdadd8", 9,
                                **({} if is_direct else {"stroke-dasharray": "4 3"})))
                if is_direct:
                    out.append(rect(x+22, y+8, 10, 10, "#7048b4", radius=2))
                else:
                    out.append(tag("circle", {"cx": x+27, "cy": y+13, "r": 5,
                                                      "fill": "#fff", "stroke": "#8165b0", "stroke-width": 1.6}))
                out.append(text(x+43, y+18.5, f"{row['policy_id']} · {policy_id}", "policy"))
                color = "#218456" if row["status"] == "verified" else "#3677bb"
                out.append(tag("circle", {"cx": x+COL_WIDTH-24, "cy": y+13, "r": 6,
                                                 "fill": color},
                               tag("title", content=f"{esc(policy_id)} · {esc(row['status'])}")))
    footer_y = layout[-1][0] + CARD_H + POLICY_GAP + layout[-1][1] + 54
    out += [rect(31, footer_y-22, WIDTH-62, 68, "#f8fafc", radius=10),
            rect(53, footer_y, 11, 11, "#7048b4", radius=2),
            text(74, footer_y+11, "直接 executor", "legend"),
            tag("circle", {"cx": 280, "cy": footer_y+5.5, "r": 6, "fill": "#fff", "stroke": "#8165b0", "stroke-width": 1.6}),
            text(297, footer_y+11, "支撑动作", "legend"),
            tag("circle", {"cx": 500, "cy": footer_y+5.5, "r": 6, "fill": "#218456"}),
            text(517, footer_y+11, "verified · 场景物理通过", "legend"),
            tag("circle", {"cx": 775, "cy": footer_y+5.5, "r": 6, "fill": "#3677bb"}),
            text(792, footer_y+11, "callable · 待物理验证", "legend"),
            text(1124, footer_y+11, "ContractRunner 已执行直接路线及共用实测检查；图不代表自动规划", "legend"),
            "</svg>"]
    return "\n".join(out) + "\n", WIDTH, height


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    svg, width, height = render(json.loads(CATALOG.read_text()))
    if args.check:
        if not SVG.exists() or SVG.read_text() != svg:
            raise SystemExit(f"stale SVG: {SVG}")
        return
    SVG.write_text(svg)
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome:
        cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu",
               "--disable-dev-shm-usage", "--hide-scrollbars", "--force-device-scale-factor=1",
               f"--window-size={width},{height}", f"--screenshot={PNG}", SVG.as_uri()]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError(f"Chrome SVG preview failed: {result.stderr[-1000:]}")
    print(f"{SVG}\n{PNG}")


if __name__ == "__main__":
    main()
