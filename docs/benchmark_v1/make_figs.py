"""Generate the benchmark-v1 overview SVGs (data taken from origin/benchmark-v1)."""
from pathlib import Path
from html import escape

OUT = Path("/home/muqingj/Projects/ZenoBench/docs/benchmark_v1")
OUT.mkdir(parents=True, exist_ok=True)

FONT = "'Noto Sans CJK SC','Noto Sans SC','PingFang SC','Microsoft YaHei',sans-serif"
MONO = "'DejaVu Sans Mono','Menlo','Consolas',monospace"
INK, MUTED, LINE, BG, PANEL = "#1f2328", "#59636e", "#d0d7de", "#ffffff", "#f6f8fa"
BLUE, BLUE_BG = "#0969da", "#ddf4ff"
GREEN, GREEN_BG = "#1a7f37", "#dafbe1"
RED, RED_BG = "#cf222e", "#ffebe9"
AMBER, AMBER_BG = "#9a6700", "#fff8c5"
PURPLE, PURPLE_BG = "#8250df", "#fbefff"
GRAY, GRAY_BG = "#57606a", "#eaeef2"
PLANNER = {"fixed": "#6e7781", "retry": "#bc4c00", "oracle": "#1a7f37", "scripted": "#8250df"}


def tw(s, fs, mono=False):
    """Rough text width."""
    w = 0.0
    for ch in s:
        w += fs if ord(ch) > 0x2e80 else fs * (0.61 if mono else (0.6 if ch.isupper() else 0.53))
    return w


class SVG:
    def __init__(self, w, h, title):
        self.w, self.h, self.parts = w, h, []
        self.title = title

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill=PANEL, stroke=LINE, r=8, sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, fs=13, fill=INK, weight=400, anchor="start", mono=False, italic=False):
        fam = MONO if mono else FONT
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{fs}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"{st}>{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=MUTED, sw=1.5, arrow=True, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arr)"' if arrow else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}{m}/>')

    def path(self, d, stroke=MUTED, sw=1.5, arrow=True, dash=None, fill="none"):
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arr)"' if arrow else ""
        self.add(f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}"{ds}{m}/>')

    def chip(self, x, y, s, fg, bg, fs=12, mono=True, pad=7, h=22):
        w = tw(s, fs, mono) + 2 * pad
        self.rect(x, y, w, h, fill=bg, stroke=fg, r=5, sw=1)
        self.text(x + pad, y + h / 2 + fs * 0.36, s, fs=fs, fill=fg, mono=mono)
        return w

    def header(self, title, sub):
        self.text(32, 44, title, fs=24, weight=700)
        self.text(32, 70, sub, fs=13.5, fill=MUTED)

    def save(self, name):
        defs = ('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker></defs>')
        body = "\n".join(self.parts)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}"><title>{escape(self.title)}</title>{defs}'
               f'<rect width="100%" height="100%" fill="{BG}"/>\n{body}\n</svg>\n')
        (OUT / name).write_text(svg)


def bullets(s, x, y, items, fs=12.5, gap=19, mono_first=False, color=INK):
    for i, it in enumerate(items):
        if isinstance(it, tuple):
            k, v = it
            s.text(x, y + i * gap, k, fs=fs, mono=True, fill=BLUE)
            s.text(x + tw(k, fs, True) + 10, y + i * gap, v, fs=fs, fill=color)
        else:
            s.text(x, y + i * gap, it, fs=fs, fill=color)


# =========================================================================== 1. interface
def fig_interface():
    s = SVG(1240, 900, "Benchmark 对外接口")
    s.header("1 · Benchmark 对外接口", "planner 只通过 LimitedSession 与仿真交互（benchmark/session.py、observation.py、planners.py）；进程内 Python 调用，没有 HTTP")

    # Planner box
    s.rect(32, 100, 330, 250, fill=BLUE_BG, stroke=BLUE, sw=1.5)
    s.text(50, 128, "你的 Planner（VLM 接在这里）", fs=15, weight=700, fill=BLUE)
    s.text(50, 148, "class MyPlanner(Planner)", fs=12.5, mono=True, fill=INK)
    s.rect(50, 162, 294, 72, fill=BG, stroke=LINE, r=6)
    s.text(62, 184, "reset(task_instruction,", fs=12.5, mono=True)
    s.text(62, 202, "      skills=None)", fs=12.5, mono=True)
    s.text(62, 222, "← 每个 episode 开始时调用一次", fs=12, fill=MUTED)
    s.rect(50, 244, 294, 92, fill=BG, stroke=LINE, r=6)
    s.text(62, 266, "next_call(observation)", fs=12.5, mono=True)
    s.text(62, 286, '→ {"skill": str, "args": dict}', fs=12.5, mono=True, fill=GREEN)
    s.text(62, 306, "→ None  表示结束 episode", fs=12.5, mono=True, fill=GREEN)
    s.text(62, 326, "每步调用一次，最多 max_calls=60 步", fs=12, fill=MUTED)

    # Session box
    s.rect(430, 100, 420, 250, fill=PANEL, stroke=INK, sw=1.5)
    s.text(448, 128, "LimitedSession(rig, image_dir)", fs=15, weight=700, mono=True)
    rows = [("observe()", "→ observation dict"),
            ("call(skill, args)", "→ feedback dict"),
            ("run_planner(planner, task,", ""),
            ("  max_calls=60)", "→ 闭环跑完整个 episode")]
    bullets(s, 448, 156, rows, fs=12.5, gap=20)
    s.rect(448, 240, 186, 96, fill=BG, stroke=LINE, r=6)
    s.text(460, 262, "Observer", fs=13, weight=700, mono=True)
    for i, t in enumerate(["观测缓存 cache", "当前视野 view", "静态布局 places", "打码未观测名字"]):
        s.text(460, 282 + i * 16, "· " + t, fs=11.5, fill=MUTED)
    s.rect(646, 240, 188, 96, fill=BG, stroke=LINE, r=6)
    s.text(658, 262, "GatedRunner", fs=13, weight=700, mono=True)
    for i, t in enumerate(["继承 SkillContractRunner", "auto_repair=False", "每次调用先过权限检查", "可行性谓词仅记录"]):
        s.text(658, 282 + i * 16, "· " + t, fs=11.5, fill=MUTED)

    # Sim box
    s.rect(918, 100, 290, 250, fill=GRAY_BG, stroke=GRAY, sw=1.5)
    s.text(936, 128, "Isaac Sim rig（GT 状态）", fs=15, weight=700, fill=GRAY)
    for i, t in enumerate(["launch() / make_rig(first_person=True)", "70 个 SkillNode / Contract", "头部相机 RGB（无手腕相机）",
                           "rig.occlusion = True", "rig.static_explore = True", "rig.auto_recovery = False"]):
        s.text(936, 156 + i * 22, ("· " if i < 3 else "  ") + t, fs=12, fill=INK if i < 3 else MUTED, mono=i >= 3)

    # arrows between
    s.line(362, 200, 428, 200, stroke=BLUE)
    s.text(395, 192, "action", fs=11, fill=BLUE, anchor="middle")
    s.line(428, 280, 364, 280, stroke=GREEN)
    s.text(396, 272, "obs", fs=11, fill=GREEN, anchor="middle")
    s.line(850, 200, 916, 200)
    s.line(916, 280, 852, 280)
    s.text(883, 192, "run", fs=11, fill=MUTED, anchor="middle")
    s.text(883, 272, "GT", fs=11, fill=MUTED, anchor="middle")

    # Observation panel
    y0 = 380
    s.rect(32, y0, 380, 300, fill=GREEN_BG, stroke=GREEN)
    s.text(50, y0 + 28, "observation（observe() 返回）", fs=15, weight=700, fill=GREEN)
    obs = [("image", "头部相机 PNG 的路径"),
           ("visible_objects", "当前视野里的物体"),
           ("observation_cache", "见过的物体：位姿/支撑/容器/tick"),
           ("known_places", "房间、家具、支撑面、门、按钮"),
           ("robot.base_pose", "[x, y, yaw]"),
           ("robot.room", "所在房间"),
           ("robot.right/left_hand", "手里拿的物体"),
           ("robot.temperatures_c", "只含已观测物体"),
           ("last_feedback", "上一步的 feedback")]
    bullets(s, 50, y0 + 58, obs, fs=12, gap=22)
    s.text(50, y0 + 270, "不给：GT 物体列表、goal 子句状态、未见物体位姿", fs=12, fill=RED)

    # Feedback panel
    s.rect(430, y0, 400, 300, fill=AMBER_BG, stroke=AMBER)
    s.text(448, y0 + 28, "feedback（call() 返回）", fs=15, weight=700, fill=AMBER)
    fb = [("action, success", ""),
          ("error_code, error", "错误码 + 文本"),
          ("checks", "实测前/后置条件 atom/holds/detail"),
          ("outputs", "skill 的输出"),
          ("path", "选中的 policy 路径 ⚠"),
          ("substeps", "嵌套步骤 action/success/error ⚠"),
          ("image, now_visible", "调用后的图像与视野")]
    bullets(s, 448, y0 + 58, fb, fs=12, gap=22)
    s.text(448, y0 + 222, "未观测的物体名统一替换成 <unobserved>", fs=12, fill=MUTED)
    s.text(448, y0 + 246, "⚠ env_service 刻意隐藏 path 与嵌套调用，", fs=12, fill=RED)
    s.text(448, y0 + 266, "   这里却返回了，两套接口不一致", fs=12, fill=RED)

    # Rules panel
    s.rect(848, y0, 360, 300, fill=RED_BG, stroke=RED)
    s.text(866, y0 + 28, "权限规则（GatedRunner）", fs=15, weight=700, fill=RED)
    rules = ["物体参数必须已观测或在手上",
             "  未见 = 不存在：同一个拒绝，机器人不动",
             "接触类 skill 要求物体在当前视野",
             "  （pick/push/stir/盖子…）",
             "放置目标只需观测过，位姿取自缓存",
             "navigate/approach 去缓存位姿",
             "search 接受任意名字",
             "explore 只按静态布局算覆盖",
             "关闭：嵌套修复、pick 内推到桌边、",
             "  pick→push、开门换位重试"]
    for i, t in enumerate(rules):
        s.text(866, y0 + 58 + i * 22, ("· " if not t.startswith("  ") else "  ") + t.strip(), fs=12,
               fill=INK if not t.startswith("  ") else MUTED)

    # Error codes strip
    y1 = 706
    s.text(32, y1 + 4, "错误码", fs=15, weight=700)
    x = 32
    y = y1 + 18
    groups = [("门控拒绝（不动）", RED, RED_BG, ["NOT_OBSERVED", "NOT_IN_VIEW", "NOT_FOUND"]),
              ("调用写错", PURPLE, PURPLE_BG, ["BAD_CALL"]),
              ("物理执行失败", AMBER, AMBER_BG, ["PRECONDITION_FAILED", "POLICY_FAILED", "NO_PATH",
                                          "SUBSKILL_FAILED", "POSTCONDITION_FAILED"])]
    for label, fg, bg, codes in groups:
        s.text(x, y + 30, label, fs=12, fill=fg, weight=700)
        xx = x
        for c in codes:
            xx += s.chip(xx, y + 40, c, fg, bg, fs=11.5) + 8
        x = xx + 24
    s.text(32, y1 + 120, "启动方式", fs=15, weight=700)
    s.rect(32, y1 + 132, 1176, 40, fill=PANEL, stroke=LINE, r=6)
    s.text(48, y1 + 158, "$ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --difficulty hard --seed 5 "
           "--planner recovery --policy mypkg.planner:MyPlanner", fs=12, mono=True)
    s.save("01_interface.svg")


# =========================================================================== 2. tasks
TASKS = [
    ("T01", "书拿到餐桌", "书已探出岛台边缘", "不探出 → fallback: Pick 失败→Expose→Pick", "起点在餐厅 + 不探出"),
    ("T02", "叠两块积木", "积木周围空旷", "B 被碗和擀面杖夹住 → fallback: Separate / Push", "起点背对 + 被夹住"),
    ("T03", "擀面杖和勺子收进同一容器", "只有收纳箱", "还有马克杯 → alternative: 放不进杯→收纳箱", "背对 + 有马克杯"),
    ("T04", "杯子放到矮柜（没有就马克杯）", "岛台上有杯子", "没有杯子 → alternative: 马克杯", "没杯子 + 马克杯在电视柜"),
    ("T05", "钢笔拿到书桌（没有就铅笔）", "（钢笔路线不稳，仅诊断）", "没有钢笔 → alternative: 铅笔", "没钢笔 + 铅笔在餐厅"),
    ("T06", "积木摆到矮柜或电视柜上", "柜顶空", "柜顶满 → alternative: Place 失败→电视柜", "柜顶满 + 积木在餐厅"),
    ("T07", "燕麦热到 ≥40°C，关火关门", "微波炉正常", "微波炉不加热 → alternative: 改用灶台", "微波炉坏 + 燕麦在矮柜"),
    ("T08", "用海绵擦岛台，海绵留在岛台", "海绵在岛台", "海绵在电视柜 → 先取海绵", "起点在餐厅 + 海绵不在"),
    ("T09", "番茄汤：入锅、搅拌、盖盖、60°C、关火", "锅盖没盖", "锅盖盖着 → fallback: Uncover", "盖着 + 勺子在电视柜"),
    ("T10", "易拉罐扔进垃圾桶", "易拉罐在岛台", "罐在餐厅 → fallback: 先 Search", "起点在餐厅 + 罐在电视柜"),
]
PROBES = [("P01", "挥手/点头/姿态"), ("P02", "识别/测量/计数/探索"), ("P03", "滚擀面杖"), ("P04", "瓶子放倒再立起"),
          ("P05", "翻书"), ("P06", "双手：左手持物开关柜"), ("P07", "展示积木/扶马克杯"), ("P08", "积木对齐与叠放"),
          ("P09", "扫拢积木"), ("P11", "灶台开关"), ("P12", "敲门/看/开关柜"), ("P13", "微波炉按钮"),
          ("P14", "复位与交换"), ("P15", "归组与分类"), ("P16", "倒空马克杯"), ("P17", "倾倒"),
          ("P18", "从地上捡积木"), ("P19", "勺子蘸汤"), ("P20", "把积木藏进锅"), ("P21", "清空柜顶"),
          ("P22", "冰箱冷却燕麦")]
PROBE_FAIL = {"P04", "P06", "P07", "P09", "P14", "P16", "P17"}


def fig_tasks():
    s = SVG(1240, 960, "Benchmark 支持的任务")
    s.header("2 · 支持的任务", "benchmark/tasks.json：10 个任务（T01–T10，各 3 个难度档）+ 21 个单场景 probe（P01–P22，无 P10）。"
             "指令三档相同，只有场景不同")
    cols = [(32, 64, "任务"), (96, 270, "目标（指令简述）"), (366, 190, "easy"), (556, 400, "medium（条件 → 声明的路线）"),
            (956, 252, "hard（叠加条件）")]
    y = 96
    s.rect(32, y, 1176, 34, fill=GRAY_BG, stroke=LINE, r=6)
    for x, w, t in cols:
        s.text(x + 10, y + 22, t, fs=13, weight=700)
    for i, row in enumerate(TASKS):
        yy = y + 34 + i * 40
        if i % 2:
            s.rect(32, yy, 1176, 40, fill=PANEL, stroke="none", r=0)
        for (x, w, _), val in zip(cols, row):
            fill, wt = INK, 400
            if x == 32:
                fill, wt = BLUE, 700
            elif x == 366:
                fill = GREEN
            elif x == 556:
                fill = AMBER if "fallback" in val else (PURPLE if "alternative" in val else AMBER)
            elif x == 956:
                fill = RED
            s.text(x + 10, yy + 25, val, fs=12.5, fill=fill, weight=wt, mono=(x == 32))
    yb = y + 34 + 10 * 40
    s.line(32, yb, 1208, yb, stroke=LINE, arrow=False)
    s.text(32, yb + 26, "颜色：", fs=12, fill=MUTED)
    xx = 76
    for lab, fg, bg in [("easy：无失败条件", GREEN, GREEN_BG), ("medium：fallback / alternative 一个条件", AMBER, AMBER_BG),
                        ("hard：再叠加起点远或物体不在视野", RED, RED_BG)]:
        xx += s.chip(xx, yb + 11, lab, fg, bg, fs=11.5, mono=False) + 10
    s.text(32, yb + 56, "fallback = 真实失败 → 辅助 skill 修复状态 → 重试同一动作；alternative = 换另一个合法的物体 / 工具 / 目的地达成同一目标",
           fs=12, fill=MUTED)

    # probes
    yp = yb + 92
    s.text(32, yp, "Probe（覆盖塞不进 10 个任务的 SkillNode，单场景、单路线）", fs=16, weight=700)
    s.text(32, yp + 22, "最终一轮 14/21 通过；红框为未通过", fs=12, fill=MUTED)
    cw, ch, per = 230, 44, 5
    for i, (pid, desc) in enumerate(PROBES):
        cx = 32 + (i % per) * (cw + 6.5)
        cy = yp + 38 + (i // per) * (ch + 8)
        bad = pid in PROBE_FAIL
        s.rect(cx, cy, cw, ch, fill=RED_BG if bad else PANEL, stroke=RED if bad else LINE, r=6)
        s.text(cx + 12, cy + 27, pid, fs=13, weight=700, mono=True, fill=RED if bad else BLUE)
        s.text(cx + 54, cy + 27, desc, fs=12.5)
    s.save("02_tasks.svg")


# =========================================================================== 3. variants (T02)
def kitchen_map(s, x, y, w, h, variant):
    """Schematic top view of the kitchen (annotation coordinates, x 3.0-9.1 m, y 0-2.8 m)."""
    s.rect(x, y, w, h, fill="#fbfaf7", stroke=LINE, r=6)
    X0, X1, Y0, Y1 = 3.0, 9.1, -0.05, 2.85

    def px(wx):
        return x + (wx - X0) / (X1 - X0) * w

    def py(wy):
        return y + h - (wy - Y0) / (Y1 - Y0) * h

    def area(x0, y0, x1, y1, label, fill, stroke, fs=10, lab_dy=0, col=None):
        s.rect(px(x0), py(y1), px(x1) - px(x0), py(y0) - py(y1), fill=fill, stroke=stroke, r=3)
        if label:
            s.text((px(x0) + px(x1)) / 2, (py(y0) + py(y1)) / 2 + 4 + lab_dy, label, fs=fs, fill=col or stroke,
                   anchor="middle")
    broken = variant != "microwave_works"
    area(6.54, 1.515, 8.26, 1.985, "岛台", "#f3ead9", "#b08d57")
    area(8.26, 1.472, 8.86, 1.985, "灶台", "#fde2d6", "#bc4c00")
    area(4.24, 2.191, 4.76, 2.69, "微波炉", RED_BG if broken else GREEN_BG, RED if broken else GREEN, fs=9.5)
    area(3.202, 0.2, 3.798, 0.52, "", "#eef1f4", GRAY, fs=9.5)
    s.text(px(3.798) + 5, py(0.36) + 4, "墙边矮柜", fs=9.5, fill=GRAY)
    area(6.64, 0.197, 8.379, 0.502, "电视柜", "#eef1f4", GRAY, fs=9.5)
    if broken:
        s.text(px(4.76) + 6, py(2.44) + 4, "不加热（外观看不出来）", fs=9.5, fill=RED)
    # oatmeal
    ox, oy = (3.5, 0.36) if variant == "broken_oatmeal_away" else (6.69, 1.83)
    s.add(f'<circle cx="{px(ox)}" cy="{py(oy)}" r="7" fill="#fff" stroke="{AMBER}" stroke-width="2"/>')
    s.add(f'<circle cx="{px(ox)}" cy="{py(oy)}" r="3" fill="{AMBER}"/>')
    if variant == "broken_oatmeal_away":
        s.text(px(ox), py(oy) - 12, "燕麦", fs=10, fill=AMBER, weight=700, anchor="middle")
    else:
        s.text(px(ox) - 10, py(oy) - 9, "燕麦", fs=10, fill=AMBER, weight=700, anchor="end")
    # robot start (7.5, 1.0) facing +x
    rx, ry = px(7.5), py(1.0)
    s.add(f'<polygon points="{rx+9},{ry} {rx-6},{ry-7} {rx-6},{ry+7}" fill="{BLUE}"/>')
    s.text(rx - 10, ry + 4, "起点", fs=9.5, fill=BLUE, anchor="end")


ROLE = {"failure": (RED, RED_BG), "recovery": (AMBER, AMBER_BG), "retry_after_recovery": (BLUE, BLUE_BG),
        "alternative": (PURPLE, PURPLE_BG), "search": (AMBER, AMBER_BG), "": (GRAY, "#ffffff")}
ROLE_LABEL = {"failure": "预期失败", "recovery": "修复", "retry_after_recovery": "修复后重试",
              "alternative": "换方案", "search": "找物体"}


def route(s, x, y, name, kind, steps, result, tag=None, width=280, res_color=GREEN):
    s.text(x, y, name, fs=13, weight=700, mono=True)
    k = s.chip(x + tw(name, 13, True) + 8, y - 15, kind, PURPLE if kind == "alternative" else GREEN,
               PURPLE_BG if kind == "alternative" else GREEN_BG, fs=10.5, h=19, pad=5)
    s.text(x + width, y, result, fs=12, fill=res_color, anchor="end", weight=700)
    if tag:
        s.text(x, y + 18, tag, fs=11, fill=MUTED)
        y += 16
    yy = y + 10
    for i, (lab, role) in enumerate(steps):
        fg, bg = ROLE[role]
        s.rect(x, yy, width, 21, fill=bg, stroke=fg if role else LINE, r=4)
        s.text(x + 7, yy + 15, f"{i+1:>2}. {lab}", fs=11, mono=True, fill=INK)
        if role:
            s.text(x + width - 7, yy + 15, ROLE_LABEL[role], fs=10.5, fill=fg, anchor="end")
        yy += 23
    return yy


def fig_variants():
    s = SVG(1240, 920, "T07 热燕麦的变体")
    s.header("3 · 变体示例：T07_heat_oatmeal（家电 + 隐藏状态 + 换方案）",
             "指令：Warm up the leftover oatmeal for breakfast (at least 40 C). When you are done, the stove must be off "
             "and the microwave door closed.")
    s.text(32, 92, "goal：temperature_at_least(oatmeal, 40) ∧ not heating(kitchen_stove) ∧ is_closed(kitchen_microwave) "
           "∧ hand_empty(right)", fs=12.5, mono=True, fill=INK)
    cols = [(32, "microwave_works", "easy", GREEN, GREEN_BG, "微波炉正常，燕麦在岛台上", "无失败条件"),
            (432, "microwave_broken", "medium", AMBER, AMBER_BG, "微波炉照常运转但不加热（燕麦加热速率被设为 0）",
             "条件：microwave_broken。外观和观测里都看不出来"),
            (832, "broken_oatmeal_away", "hard", RED, RED_BG, "微波炉不加热，燕麦被留在墙边矮柜上",
             "条件：microwave_broken + not_in_view")]
    for x, name, tier, fg, bg, d1, d2 in cols:
        s.rect(x, 108, 376, 262, fill=bg, stroke=fg, sw=1.5)
        s.text(x + 16, 136, name, fs=15, weight=700, mono=True, fill=fg)
        s.chip(x + 16 + tw(name, 15, True) + 10, 120, tier, fg, "#ffffff", fs=11.5, h=21, pad=6)
        s.text(x + 16, 160, d1, fs=12)
        s.text(x + 16, 179, d2, fs=11.5, fill=MUTED)
        kitchen_map(s, x + 16, 192, 344, 162, name)

    s.text(32, 400, "声明的路线（tasks.json → routes），右上角为最终一轮的回放结果", fs=16, weight=700)
    mw = [("navigate(kitchen_microwave)", ""), ("open(kitchen_microwave)", ""), ("look(kitchen_island/top)", ""),
          ("navigate(oatmeal)", ""), ("pick(oatmeal)", ""), ("navigate(microwave/inside_floor)", ""),
          ("place(oatmeal, microwave/inside)", ""), ("close(kitchen_microwave)", "")]
    tail = [("stop(kitchen_microwave)", "alternative"), ("pick(oatmeal)", "alternative"),
            ("navigate(kitchen_stove/top)", "alternative"), ("place(oatmeal, stove/top)", "alternative"),
            ("heat(oatmeal, stove, 40)", "alternative"), ("navigate(kitchen_microwave)", ""),
            ("close(kitchen_microwave)", "")]
    nominal = mw + [("heat(oatmeal, microwave, 40)", "")]
    alt = mw + [("heat(oatmeal, microwave, 40)", "failure")] + tail
    hard = mw[:2] + [("search(oatmeal, living_room)", "search")] + mw[3:] + \
        [("heat(oatmeal, microwave, 40)", "failure")] + tail
    oracle = [("look(kitchen_island/top)", ""), ("navigate(oatmeal)", ""), ("pick(oatmeal)", ""),
              ("navigate(kitchen_stove/top)", ""), ("place(oatmeal, stove/top)", ""),
              ("heat(oatmeal, stove, 40)", "")]
    y0 = 436
    gap = (1176 - 4 * 280) / 3
    xs = [32 + i * (280 + gap) for i in range(4)]
    route(s, xs[0], y0, "nominal", "nominal", nominal, "2/2 通过", tag="变体 microwave_works；oracle 也选它")
    route(s, xs[1], y0, "alternative_stove", "alternative", alt, "2/2 通过", tag="变体 microwave_broken（scripted 回放）")
    route(s, xs[2], y0, "oracle_stove", "alternative", oracle, "oracle 1/1", tag="变体 microwave_broken（oracle 专用）")
    route(s, xs[3], y0, "hard_search_stove", "alternative", hard, "2/2 通过", tag="变体 broken_oatmeal_away；oracle 也选它")
    for x, c in [(xs[0], GREEN), (xs[1], AMBER), (xs[3], RED)]:
        pass
    # notes under nominal / oracle
    ny = y0 + 26 + 9 * 23 + 30
    s.text(xs[0], ny, "medium 下 fixed / retry 也跑这条：", fs=12, fill=MUTED)
    s.text(xs[0], ny + 18, "第 9 步 heat 失败（温度不升）后，", fs=12, fill=MUTED)
    s.text(xs[0], ny + 36, "fixed 停止；retry 原样再 heat 2 次", fs=12, fill=MUTED)
    s.text(xs[0], ny + 54, "→ 两者 GC 都是 0.75（燕麦没热）", fs=12, fill=MUTED)
    oy = y0 + 26 + 6 * 23 + 30
    s.text(xs[2], oy, "oracle 知道微波炉是坏的：", fs=12, fill=MUTED)
    s.text(xs[2], oy + 18, "直接跳过微波炉，用灶台加热，", fs=12, fill=MUTED)
    s.text(xs[2], oy + 36, "6 步完成，这就是 SPL-c 的 L_ref", fs=12, fill=MUTED)
    s.text(xs[2], oy + 54, "受限 planner 必须先试一次微波炉", fs=12, fill=MUTED)
    s.text(xs[2], oy + 72, "才能发现它坏了", fs=12, fill=MUTED)

    # legend
    ly = oy + 108
    s.text(xs[2], ly, "步骤角色", fs=13, weight=700)
    for i, role in enumerate(["failure", "alternative", "search"]):
        fg, bg = ROLE[role]
        s.rect(xs[2], ly + 12 + i * 24, 16, 16, fill=bg, stroke=fg, r=3)
        s.text(xs[2] + 24, ly + 25 + i * 24, {"failure": "预期失败（scripted 检查它确实失败）",
                                               "alternative": "换方案：停微波炉、取出、改用灶台",
                                               "search": "找物体（hard：燕麦不在视野）"}[role], fs=12)

    s.text(32, 868, "为什么选它：失败原因是隐藏的家电状态（不是抓取几何）；goal 带收尾约束（关火、关门）；换方案后还要回头关微波炉门。",
           fs=12, fill=MUTED)
    s.text(32, 890, "诊断：曾有 microwave_occupied 变体（腔内放一碗剩菜），但燕麦仍能放在它前面，条件没有挡住微波炉路线，已删除（tasks.json → diagnostics）",
           fs=12, fill=MUTED)
    s.save("03_variants_T07.svg")


# =========================================================================== 4. pipeline
def box(s, x, y, w, h, title, lines, fg=INK, bg=PANEL, mono_title=True, fs=11.5):
    s.rect(x, y, w, h, fill=bg, stroke=fg if fg != INK else LINE, sw=1.3)
    s.text(x + 12, y + 22, title, fs=13, weight=700, mono=mono_title, fill=fg)
    for i, t in enumerate(lines):
        s.text(x + 12, y + 42 + i * 17, t, fs=fs, fill=MUTED if fg == INK else INK)


def fig_pipeline():
    s = SVG(1240, 960, "Benchmark 使用流水线")
    s.header("4 · 用这个 benchmark 评测一个 planner 的流水线", "从任务定义到指标报告；Isaac 进程最多同时 2 个（--jobs 2）")
    # stage labels
    stages = [(100, "① 准备"), (300, "② 生成批次"), (440, "③ 逐 episode 运行（Isaac Sim）"), (800, "④ 离线评测")]
    for y, t in stages:
        if y == 440:
            s.text(1208, y, t, fs=14, weight=700, fill=BLUE, anchor="end")
        else:
            s.text(32, y, t, fs=14, weight=700, fill=BLUE)

    # stage 1
    box(s, 32, 112, 270, 92, "define_tasks.py", ["Python 里的任务定义", "→ 写出 benchmark/tasks.json"])
    box(s, 340, 112, 270, 92, "check_layouts.py", ["静态检查场景叠加改动", "不需要仿真器"])
    box(s, 648, 112, 270, 92, "pytest benchmark/tests", ["test_gate.py：权限规则（假 rig）", "sim_permissions.py：仿真内 17 项"])
    box(s, 956, 112, 252, 92, "实现 Planner", ["mypkg/planner.py:MyPlanner", "reset() / next_call()"], fg=BLUE, bg=BLUE_BG)
    s.line(302, 158, 338, 158)
    s.line(610, 158, 646, 158)

    # stage 2
    box(s, 32, 312, 420, 100, "make_batches.py --policy mypkg.planner:MyPlanner",
        ["每个任务 × 难度档 × seed {10, 11}", "planner ∈ fixed / retry / oracle（+ recovery）", "→ batches/eval.json（每个 planner 58 个 episode）"])
    s.path("M 1082 204 L 1082 260 L 240 260 L 240 310", stroke=BLUE)
    s.line(452, 362, 500, 362)
    box(s, 502, 312, 706, 100, "run_episode.py --batch batches/eval.json --jobs 2 --out runs/eval",
        ["每个 episode 起一个子进程，最多同时 2 个", "也可单跑：--task T07_heat_oatmeal --difficulty hard --seed 5 --planner recovery --policy …"])

    # stage 3: per-episode chain
    y3 = 456
    chain = [("scene.py", ["episode_config(seed)", "seed 选该档的变体", "随机删掉一部分干扰物"]),
             ("build_annotation", ["base 标注 − 删除物体", "+ 移动物体", "make_prepare 改 USD"]),
             ("launch / make_rig", ["first_person=True", "热学状态覆盖", "（如微波炉不加热）"]),
             ("LimitedSession", ["Observer + GatedRunner", "初始 observe()", "存首张图像"]),
             ("planner 闭环", ["obs → next_call()", "→ call() → feedback", "直到 None 或 60 步"]),
             ("收尾判定", ["evaluate_goal：all/any", "floor_drops：掉地", "stop_reason, sim_ticks"])]
    bw, gap = 180, 19.2
    for i, (t, ls) in enumerate(chain):
        x = 32 + i * (bw + gap)
        hl = i == 4
        box(s, x, y3, bw, 112, t, ls, fg=BLUE if hl else INK, bg=BLUE_BG if hl else PANEL,
            mono_title=True)
        if i < len(chain) - 1:
            s.line(x + bw, y3 + 56, x + bw + gap - 1, y3 + 56)
    s.path("M 855 412 L 855 436 L 122 436 L 122 454")
    # outputs
    y4 = 600
    s.rect(32, y4, 1176, 150, fill=GRAY_BG, stroke=GRAY, dash="5 4")
    s.text(48, y4 + 24, "runs/<out>/<task>/<seed>_<planner>/   每个 episode 的输出", fs=13, weight=700, mono=True, fill=GRAY)
    outs = [("config.json", "任务、变体、seed、改动、删掉的干扰物、git commit 与 diff 哈希"),
            ("annotation.json", "这一轮实际使用的场景标注"),
            ("calls.jsonl", "每次调用：skill、args、feedback、状态摘要、tick"),
            ("images/", "每次顶层调用后的第一人称图像"),
            ("result.json", "goal 原子、掉落物体、观测缓存、门控日志、最后 300 条事件、stop_reason")]
    bullets(s, 48, y4 + 50, outs, fs=12, gap=20)
    s.path("M 1114 568 L 1114 598")

    # stage 4
    y5 = 812
    box(s, 32, y5, 560, 110, "report.py --runs DIR",
        ["每条声明路线是否跑通，覆盖了哪些 SkillNode", "→ RESULTS.md、coverage.json（以及 README 里的结果表）"])
    box(s, 648, y5, 560, 110, "evaluate.py --runs DIR --group planner,tier", [
        "SR、GC、pass^k、SPL-c、unseen / ghost / not_in_view / invalid、",
        "phys、recov、repeat、drops、side、budget",
        "→ EVALUATION.md、metrics.json"], fg=GREEN, bg=GREEN_BG)
    s.path("M 312 750 L 312 810")
    s.path("M 928 750 L 928 810")
    s.save("04_pipeline.svg")


# =========================================================================== 5. baseline pipeline
def fig_baselines():
    s = SVG(1240, 860, "Baseline 运行流水线")
    s.header("5 · Baseline 怎么跑（run_episode.py 里的分支）",
             "同一个 episode 准备流程；区别在：谁决定下一步、用哪个 runner、失败后怎么办。代码里没有 VLM planner")
    # common prep
    s.rect(32, 96, 1176, 58, fill=PANEL, stroke=LINE)
    s.text(48, 122, "共同准备", fs=14, weight=700)
    s.text(48, 142, "tasks.json → episode_config(seed, variant/difficulty) → 场景叠加改动 → launch / make_rig → before_snapshot",
           fs=12.5, fill=MUTED)
    cols = [
        ("scripted", "脚本回放（非 planner）", PURPLE, PURPLE_BG,
         ["输入：--route 指定的声明路线", "runner：LimitedSession（受限）", "按步执行，检查 expect：",
          "  · 预期失败的步骤必须失败", "  · 其余步骤失败就停", "用途：证明路线物理上可行"], "可行性上限"),
        ("fixed", "固定计划", PLANNER["fixed"], GRAY_BG,
         ["输入：任务的 nominal 路线", "runner：LimitedSession（受限）", "每步 1 次", "第一个失败就停", "",
          "不看反馈，不换方案"], "下界"),
        ("retry", "盲目重试", PLANNER["retry"], "#fff1e5",
         ["输入：任务的 nominal 路线", "runner：LimitedSession（受限）", "每步最多 3 次", "原样重复失败的调用",
          "3 次都失败才停", "不看反馈，不换方案"], "下界"),
        ("oracle", "GT 上限", PLANNER["oracle"], GREEN_BG,
         ["输入：oracle[variant] 对应路线", "runner：原始 SkillContractRunner", "  完整 GT 状态，无观测限制",
          "  自动嵌套修复照常开启", "跳过预期失败和撤销步骤", "相当于知道答案"], "上限（不公平）"),
        ("recovery", "闭环 planner", BLUE, BLUE_BG,
         ["输入：--policy module:Class", "runner：LimitedSession（受限）", "run_planner()：", "  observe → next_call → call",
          "直到 None 或 max_calls=60", "VLM 接在这里"], "⚠ 尚未实现"),
    ]
    cw, gap = 224, 14
    for i, (name, sub, fg, bg, lines, tag) in enumerate(cols):
        x = 32 + i * (cw + gap)
        s.path(f"M {620} 154 L {620} 176 L {x + cw/2} 176 L {x + cw/2} 196", stroke=MUTED)
        dash = "6 4" if name == "recovery" else None
        s.rect(x, 198, cw, 300, fill=bg, stroke=fg, sw=1.8, dash=dash)
        s.text(x + 14, 226, name, fs=17, weight=700, mono=True, fill=fg)
        s.text(x + 14, 248, sub, fs=12.5, fill=fg)
        for j, t in enumerate(lines):
            s.text(x + 14, 278 + j * 22, t, fs=12, fill=INK if not t.startswith("  ") else MUTED)
        s.chip(x + 14, 460, tag, fg, "#ffffff", fs=12, mono=False)
        s.line(x + cw / 2, 498, x + cw / 2, 528)
    # per-step loop illustration
    s.rect(32, 530, 1176, 70, fill=PANEL, stroke=LINE)
    s.text(48, 556, "收尾（所有 planner 相同）", fs=14, weight=700)
    s.text(48, 580, "rig.step(60) → evaluate_goal（GT goal：all 全成立且 any 至少一组成立）→ floor_drops → 写 result.json / calls.jsonl / images/",
           fs=12.5, fill=MUTED)
    s.line(620, 600, 620, 626)
    s.rect(32, 628, 1176, 62, fill=GREEN_BG, stroke=GREEN)
    s.text(48, 654, "evaluate.py", fs=14, weight=700, mono=True, fill=GREEN)
    s.text(48, 676, "按 planner × 难度档汇总；scripted 行的失败是设计出来的，只作为可行性上限，不参与排名", fs=12.5)

    # timeline example
    y = 720
    s.text(32, y, "同一场景下的行为对比：T02 crowded（medium），nominal 第 3 步 pick 会失败", fs=14, weight=700)
    rows = [("fixed", ["look", "navigate", "pick ✗"], "停 → SR 0，GC 0.50"),
            ("retry", ["look", "navigate", "pick ✗", "pick ✗", "pick ✗"], "停 → SR 0，GC 0.50"),
            ("oracle", ["look", "navigate", "separate", "pick", "rotate", "navigate", "approach", "stack ✗"], "SR 0（这一轮 stack 失败）")]
    for i, (name, steps, res) in enumerate(rows):
        yy = y + 18 + i * 32
        s.text(32, yy + 16, name, fs=12.5, weight=700, mono=True, fill=PLANNER[name])
        x = 110
        for st in steps:
            bad = "✗" in st
            x += s.chip(x, yy, st, RED if bad else PLANNER[name], RED_BG if bad else "#ffffff", fs=11, h=22) + 6
        s.text(x + 10, yy + 16, res, fs=12, fill=MUTED)
    s.save("05_baseline_pipeline.svg")


# =========================================================================== 6. results
SUMMARY = {  # planner: n, SR, GC, pass^k, SPL-c, ghost/ep, phys/ep, recov, repeat
    "fixed": (10, 20, 54, 20, 0.19, 0.20, 0.60, "0% (6)", "0%"),
    "retry": (10, 20, 54, 20, 0.19, 0.60, 1.70, "0% (6)", "71%"),
    "oracle": (10, 90, 90, 90, 0.90, 0.00, 0.10, "0% (1)", "0%"),
    "scripted": (62, 95, 96, 80, 0.87, 0.06, 0.53, "90% (30)", "0%"),
}
PER_TASK = {  # task: variant, tier, fixed(S,GC,calls), retry, oracle, L_ref
    "T01": ("no_overhang", "M", (0, .50, 4), (0, .50, 6), (1, 1.0, 6), 6),
    "T02": ("crowded", "M", (0, .50, 3), (0, .50, 9), (0, 0.0, 8), 8),
    "T03": ("far_small_and_large", "H", (1, 1.0, 12), (1, 1.0, 12), (1, 1.0, 13), 13),
    "T04": ("no_cup", "M", (0, .75, 2), (0, .75, 4), (1, 1.0, 6), 6),
    "T05": ("no_pen", "M", (0, .50, 3), (0, .50, 5), (1, 1.0, 6), 6),
    "T06": ("occupied", "M", (0, 0.0, 5), (0, 0.0, 7), (1, 1.0, 6), 6),
    "T07": ("microwave_broken", "M", (0, .75, 9), (0, .75, 11), (1, 1.0, 6), 6),
    "T08": ("sponge_on_tv_stand", "M", (0, 0.0, 5), (0, 0.0, 7), (1, 1.0, 7), 7),
    "T09": ("lid_on", "M", (0, .38, 2), (0, .38, 4), (1, 1.0, 16), 16),
    "T10": ("can_in_dining_room", "M", (1, 1.0, 8), (1, 1.0, 8), (1, 1.0, 7), 7),
}


def gc_color(v):
    # white -> green
    import colorsys
    if v <= 0:
        return "#ffebe9"
    l = 0.93 - 0.40 * v
    r, g, b = colorsys.hls_to_rgb(0.37, l, 0.55)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def fig_results():
    s = SVG(1240, 960, "Baseline 结果")
    s.header("6 · Baseline 结果（benchmark/runs/final，来自 EVALUATION.md）",
             "注意：每个 planner 只有 n=10（每任务 1 个 seed，9 个 medium + 1 个 hard），完整的 58 episode 网格（batches/eval.json）还没跑")
    # bar chart SR & GC
    x0, y0, w, h = 80, 120, 520, 300
    s.text(32, 108, "SR 与 GC（%）", fs=15, weight=700)
    for v in range(0, 101, 25):
        yy = y0 + h - v / 100 * h
        s.line(x0, yy, x0 + w, yy, stroke="#eaeef2", sw=1, arrow=False)
        s.text(x0 - 8, yy + 4, str(v), fs=11, fill=MUTED, anchor="end")
    s.line(x0, y0 + h, x0 + w, y0 + h, stroke=MUTED, sw=1, arrow=False)
    names = list(SUMMARY)
    gw = w / len(names)
    for i, n in enumerate(names):
        d = SUMMARY[n]
        cx = x0 + i * gw + gw / 2
        for j, (val, op) in enumerate([(d[1], 1.0), (d[2], 0.45)]):
            bx = cx - 38 + j * 40
            bh = val / 100 * h
            s.add(f'<rect x="{bx}" y="{y0 + h - bh}" width="36" height="{bh}" rx="3" fill="{PLANNER[n]}" fill-opacity="{op}"/>')
            s.text(bx + 18, y0 + h - bh - 6, f"{val}", fs=12, weight=700, anchor="middle", fill=PLANNER[n])
        s.text(cx, y0 + h + 22, n, fs=13, weight=700, mono=True, anchor="middle", fill=PLANNER[n])
        s.text(cx, y0 + h + 40, f"n={d[0]}", fs=11, fill=MUTED, anchor="middle")
    s.rect(x0 + 20, y0 - 4, 14, 14, fill=GRAY, stroke="none", r=2)
    s.text(x0 + 40, y0 + 8, "SR", fs=12)
    s.add(f'<rect x="{x0 + 80}" y="{y0 - 4}" width="14" height="14" rx="2" fill="{GRAY}" fill-opacity="0.45"/>')
    s.text(x0 + 100, y0 + 8, "GC（浅色）", fs=12)
    s.text(x0 + gw * 3.5, y0 + h + 58, "scripted = 回放声明路线，可行性上限，不参与排名", fs=11, fill=PURPLE, anchor="middle")

    # summary table
    tx, ty = 650, 108
    s.text(tx, ty, "汇总指标", fs=15, weight=700)
    hdr = ["planner", "SR", "GC", "pass^k", "SPL-c", "ghost/ep", "phys/ep", "recov", "repeat"]
    cxs = [tx, tx + 88, tx + 136, tx + 184, tx + 246, tx + 302, tx + 372, tx + 440, tx + 512]
    s.rect(tx - 8, ty + 12, 574, 30, fill=GRAY_BG, stroke=LINE, r=5)
    for c, t in zip(cxs, hdr):
        s.text(c, ty + 32, t, fs=11.5, weight=700)
    for i, n in enumerate(names):
        d = SUMMARY[n]
        yy = ty + 66 + i * 30
        vals = [n, f"{d[1]}%", f"{d[2]}%", f"{d[3]}%", f"{d[4]:.2f}", f"{d[5]:.2f}", f"{d[6]:.2f}", d[7], d[8]]
        for k, (c, t) in enumerate(zip(cxs, vals)):
            hot = (n == "retry" and k == 8)
            s.text(c, yy, t, fs=12, mono=(k == 0), weight=700 if k == 0 or hot else 400,
                   fill=PLANNER[n] if k == 0 else (RED if hot else INK))
    notes = ["fixed 和 retry 的 SR / GC 完全相同：都执行 nominal 计划，不换方案",
             "retry 的差别只有：71% 的物理失败后原样重试，ghost 也更多",
             "oracle 用 GT runner、无观测限制、自动修复开着，是宽松上限",
             "recov = 遇到物理失败的 episode 中最终成功的比例（括号内为数量）"]
    for i, t in enumerate(notes):
        s.text(tx, ty + 200 + i * 20, "· " + t, fs=11.5, fill=MUTED)

    # per-task heatmap
    hy = 520
    s.text(32, hy, "逐任务结果（每格：成功 ✓/✗ · GC · 调用数 / oracle 参考调用数 L_ref）", fs=15, weight=700)
    colx = [32, 96, 270, 330, 520, 710, 900]
    heads = ["任务", "变体", "档", "fixed", "retry", "oracle"]
    s.rect(32, hy + 14, 1060, 30, fill=GRAY_BG, stroke=LINE, r=5)
    for c, t in zip(colx, heads):
        fill = PLANNER.get(t, INK)
        s.text(c + 10, hy + 34, t, fs=12.5, weight=700, mono=t in PLANNER, fill=fill)
    for i, (tid, (var, tier, f, r, o, lref)) in enumerate(PER_TASK.items()):
        yy = hy + 48 + i * 34
        s.text(42, yy + 21, tid, fs=12.5, weight=700, mono=True, fill=BLUE)
        s.text(106, yy + 21, var, fs=11.5, mono=True)
        s.text(280, yy + 21, {"M": "medium", "H": "hard"}[tier], fs=11.5, fill=AMBER if tier == "M" else RED)
        for c, (ok, gc, calls) in zip(colx[3:], (f, r, o)):
            s.rect(c + 4, yy + 2, 182, 28, fill=gc_color(gc), stroke=GREEN if ok else RED, r=4, sw=1.4 if ok else 1)
            s.text(c + 14, yy + 21, "✓" if ok else "✗", fs=13, weight=700, fill=GREEN if ok else RED)
            s.text(c + 36, yy + 21, f"GC {gc:.2f}", fs=12, mono=True)
            s.text(c + 176, yy + 21, f"{calls} / {lref}", fs=11.5, mono=True, fill=MUTED, anchor="end")
    # legend
    lx, ly = 1110, hy + 60
    s.text(lx, ly, "GC", fs=12, weight=700)
    for k, v in enumerate([1.0, 0.75, 0.5, 0.38, 0.0]):
        s.rect(lx, ly + 10 + k * 26, 22, 20, fill=gc_color(v), stroke=LINE, r=3)
        s.text(lx + 30, ly + 25 + k * 26, f"{v:.2f}", fs=11, mono=True)
    s.text(32, hy + 48 + 10 * 34 + 26,
           "fixed / retry 只在 T03（hard，但 nominal 恰好可行）和 T10 成功；oracle 唯一失败是 T02 crowded（separate 后 stack 失败）",
           fs=12, fill=MUTED)
    s.save("06_baseline_results.svg")


for f in (fig_interface, fig_tasks, fig_variants, fig_pipeline, fig_baselines, fig_results):
    f()
print("ok", sorted(p.name for p in OUT.iterdir()))
