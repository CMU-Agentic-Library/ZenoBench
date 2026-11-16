"""Top-down view of one park search dump (zeno_skills.park_search, env ZB_PARK_DUMP) as a standalone HTML page.

usage: python3 tools/park_search_view.py <dump.json> <annotation.json> <door name> <door q> <out.html> [title]
"""
import json
import math
import sys

dump_p, ann_p, door_name, door_q, out_p = sys.argv[1:6]
title = sys.argv[6] if len(sys.argv) > 6 else "Park search"
door_q = float(door_q)
D = json.load(open(dump_p))
A = json.load(open(ann_p))

# ---------------------------------------------------------------- what each park position reached
STAGES = ["out_of_reach", "footprint", "travel_pose", "drive", "ik", "ranked", "collides", "free", "built", "found"]
LABEL = {"out_of_reach": "arm can't reach (distance)", "footprint": "base footprint hits furniture",
         "travel_pose": "robot in travel posture collides", "drive": "can't drive there",
         "ik": "no kinematic IK", "ranked": "ranked, not collision-checked", "collides": "ranking solution collides",
         "free": "ranking solution free", "built": "plan built, failed", "found": "chosen park"}
COLOR = {"out_of_reach": "#d9d9d9", "footprint": "#bdbdbd", "travel_pose": "#9e9e9e", "drive": "#7b7b7b",
         "ik": "#c7b3e6", "ranked": "#8fb3e8", "collides": "#e8746a", "free": "#3fb06f", "built": "#f0a830",
         "found": "#111111"}
best = {}


def mark(x, y, stage):
    key = (round(float(x), 3), round(float(y), 3))
    if STAGES.index(stage) > STAGES.index(best.get(key, "out_of_reach")) or key not in best:
        best[key] = stage


for st in ("out_of_reach", "footprint"):
    for c in D["rejected"].get(st, []):
        mark(c[0], c[1], st)
for st in ("travel_pose", "drive", "ik"):
    for c in D["rejected"].get(st, []):
        mark(c[0], c[1], st)
for c in D.get("ranked", []):
    mark(c[0], c[1], "ranked")
for c in D.get("free_checked", []):
    mark(c[0], c[1], "free" if c[4] else "collides")
built = D.get("built", [])
for c in built:
    mark(c[0], c[1], "built")
if D.get("found"):
    mark(D["found"][0], D["found"][1], "found")
counts = {s: sum(1 for v in best.values() if v == s) for s in STAGES}

# ---------------------------------------------------------------- the scene around the goals
gx = [g[0] for g in D["goals"]]
gy = [g[1] for g in D["goals"]]
cx, cy = sum(gx) / len(gx), sum(gy) / len(gy)
R = 1.6                                     # m around the goals' centre
x0, x1, y0, y1 = cx - R, cx + R, cy - R, cy + R
W = 760
s = W / (x1 - x0)


def P(x, y):
    return (x - x0) * s, (y1 - y) * s       # +y up on screen


def rect(b, **kw):
    ax, ay = P(b[0], b[3])
    bx, by = P(b[2], b[1])
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<rect x="{ax:.1f}" y="{ay:.1f}" width="{bx - ax:.1f}" height="{by - ay:.1f}" {attrs}/>'


def poly(pts, **kw):
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return '<polygon points="' + " ".join("%.1f,%.1f" % P(*p) for p in pts) + f'" {attrs}/>'


def inside(b):
    return b[2] > x0 and b[0] < x1 and b[3] > y0 and b[1] < y1


layers = {"scene": [], "parks": [], "built": [], "goals": []}
for o in A.get("obstacles", []):
    bb = o.get("aabb")
    if not bb or len(bb) != 6 or bb[5] < 0.05:
        continue
    b = [bb[0], bb[1], bb[3], bb[4]]
    if inside(b):
        layers["scene"].append(rect(b, fill="#efe9dc", stroke="#b9ad93", stroke_width="0.6", opacity="0.8")
                               .replace("/>", f'><title>{o.get("name", "")}</title></rect>'))
door = next(a for a in A["articulated"] if a["name"] == door_name)
bb = door["body_aabb"]
layers["scene"].append(rect([bb[0], bb[1], bb[3], bb[4]], fill="none", stroke="#6b4f2a", stroke_width="2")
                       .replace("/>", f"><title>{door_name} body</title></rect>"))
for sp in A["supports"]:
    if sp.get("furniture") == door_name and sp.get("category") == "cabinet_inside":
        layers["scene"].append(rect(sp["aabb_xy"], fill="#f6dfa9", stroke="#c08a1e", stroke_width="1",
                                    opacity="0.7").replace("/>", f"><title>{sp['name']} (z {sp['z']})</title></rect>"))
# the door leaf at its open angle: part_frame turned about the hinge axis by q - closed_q
F = door["part_frame"]
px, py = door["pivot"][0], door["pivot"][1]
t = door_q - door["closed_q"]
c, sn = math.cos(t), math.sin(t)
for lo, hi in door.get("part_boxes") or [door["part_box"]]:
    corners = []
    for (u, v) in ((lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])):
        wx = F[0][0] * u + F[0][1] * v + F[0][3]
        wy = F[1][0] * u + F[1][1] * v + F[1][3]
        dx, dy = wx - px, wy - py
        corners.append((px + c * dx - sn * dy, py + sn * dx + c * dy))
    layers["scene"].append(poly(corners, fill="#8a5a2b", stroke="#4d3115", stroke_width="1")
                           .replace("/>", f"><title>{door_name} door at q {door_q:.3f}</title></polygon>"))
hx, hy = P(px, py)
layers["scene"].append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="4" fill="#4d3115"><title>hinge</title></circle>')

# ---------------------------------------------------------------- parks
r = max(1.6, 0.03 * s * 0.45)
order = sorted(best.items(), key=lambda kv: STAGES.index(kv[1]))
for (x, y), st in order:
    if not (x0 < x < x1 and y0 < y < y1):
        continue
    X, Y = P(x, y)
    layers["parks"].append(f'<circle class="st-{st}" cx="{X:.1f}" cy="{Y:.1f}" r="{r:.1f}" fill="{COLOR[st]}">'
                           f'<title>({x:.2f}, {y:.2f}) {LABEL[st]}</title></circle>')
for i, (x, y, yaw, k, why) in enumerate(built):
    X, Y = P(x, y)
    a = math.radians(yaw)
    ex, ey = P(x + 0.18 * math.cos(a), y + 0.18 * math.sin(a))
    layers["built"].append(f'<line x1="{X:.1f}" y1="{Y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#b36b00" '
                           f'stroke-width="1.4"/><circle cx="{X:.1f}" cy="{Y:.1f}" r="{r + 1.5:.1f}" fill="none" '
                           f'stroke="#b36b00" stroke-width="1.4"><title>build #{i + 1} at ({x:.2f}, {y:.2f}, {yaw:.0f} deg) '
                           f'goal {k}: {why}</title></circle>')
for g in D["goals"]:
    X, Y = P(g[0], g[1])
    layers["goals"].append(f'<path d="M{X - 5:.1f},{Y - 5:.1f} L{X + 5:.1f},{Y + 5:.1f} M{X - 5:.1f},{Y + 5:.1f} '
                           f'L{X + 5:.1f},{Y - 5:.1f}" stroke="#1f4fbf" stroke-width="2"><title>set-down TCP '
                           f'({g[0]:.3f}, {g[1]:.3f}, {g[2]:.3f})</title></path>')
for p in D.get("prefer", []):
    X, Y = P(p[0], p[1])
    a = math.radians(p[2])
    ex, ey = P(p[0] + 0.3 * math.cos(a), p[1] + 0.3 * math.sin(a))
    layers["goals"].append(f'<rect x="{X - 6:.1f}" y="{Y - 6:.1f}" width="12" height="12" fill="#ffffff" '
                           f'stroke="#7a1fbf" stroke-width="2.5"><title>seed in front of the free edge '
                           f'({p[0]:.2f}, {p[1]:.2f}, {p[2]:.0f} deg)</title></rect><line x1="{X:.1f}" y1="{Y:.1f}" '
                           f'x2="{ex:.1f}" y2="{ey:.1f}" stroke="#7a1fbf" stroke-width="2.5"/>')
bn = D.get("base_now")
if bn and x0 < bn[0] < x1 and y0 < bn[1] < y1:
    X, Y = P(bn[0], bn[1])
    layers["goals"].append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="7" fill="none" stroke="#000" stroke-dasharray="3 2">'
                           f'<title>robot now</title></circle>')

# scale bar
sx, sy = P(x0 + 0.1, y0 + 0.1)
scale = f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{sx + 0.5 * s:.1f}" y2="{sy:.1f}" stroke="var(--fg)" stroke-width="2"/>' \
        f'<text x="{sx:.1f}" y="{sy - 6:.1f}" font-size="11" fill="var(--fg)">50 cm</text>'

why_counts = {}
for b in built:
    key = b[4].split(" (")[0]
    why_counts[key] = why_counts.get(key, 0) + 1
legend = "".join(
    f'<label><input type="checkbox" checked data-st="{st}"> <span class="sw" style="background:{COLOR[st]}"></span>'
    f'{LABEL[st]} <b>{counts[st]}</b></label>' for st in STAGES if counts[st])
examples = "".join(f"<li><code>{k}</code> × {v}</li>" for k, v in sorted(why_counts.items(), key=lambda kv: -kv[1]))
fc = D.get("free_checked", [])
summary = (f"{len(D['goals'])} goals · {len(best)} distinct park positions (all yaws and goals merged; a dot shows "
           f"the furthest any of them got) · ranking solutions checked {len(fc)}, free {sum(1 for c in fc if c[4])} · "
           f"built {len(built)} · found {'yes' if D.get('found') else 'no'}")

html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Park search view</title>
<style>
:root {{ --bg:#ffffff; --fg:#1d1d1f; --muted:#666; --card:#f6f6f4; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#18181a; --fg:#ececec; --muted:#aaa; --card:#232326; }} }}
:root[data-theme="dark"] {{ --bg:#18181a; --fg:#ececec; --muted:#aaa; --card:#232326; }}
body {{ background:var(--bg); color:var(--fg); font:14px/1.45 system-ui,sans-serif; margin:0; padding:16px; }}
h1 {{ font-size:18px; margin:0 0 4px; }} .muted {{ color:var(--muted); }}
.wrap {{ display:flex; gap:16px; flex-wrap:wrap; align-items:flex-start; }}
svg {{ background:var(--card); border-radius:8px; max-width:100%; height:auto; }}
.side {{ min-width:260px; max-width:420px; }}
.side label {{ display:block; margin:3px 0; cursor:pointer; }}
.sw {{ display:inline-block; width:11px; height:11px; border-radius:50%; vertical-align:middle; margin-right:4px; }}
code {{ font-size:12px; }} ul {{ padding-left:18px; }}
</style></head><body>
<h1>{title}</h1><div class="muted">{summary}</div>
<div class="wrap"><svg viewBox="0 0 {W} {W}" width="{W}" height="{W}">
<g id="scene">{''.join(layers['scene'])}</g><g id="parks">{''.join(layers['parks'])}</g>
<g id="built">{''.join(layers['built'])}</g><g id="goals">{''.join(layers['goals'])}</g>{scale}</svg>
<div class="side"><b>Park positions</b> (hover a dot for details)<div id="legend">{legend}</div>
<p><label><input type="checkbox" checked id="tg-built"> builds (orange ring + base heading)</label>
<label><input type="checkbox" checked id="tg-goals"> set-down TCPs (blue ×), seed (purple square), robot now (dashed)</label></p>
<b>Why the builds failed</b><ul>{examples or '<li>none built</li>'}</ul>
<p class="muted">Brown: {door_name} body, its door leaf at q = {door_q:.3f} rad, hinge dot. Yellow: its inside shelves. Beige: other furniture boxes.</p></div></div>
<script>
document.querySelectorAll('#legend input').forEach(cb => cb.addEventListener('change', () =>
  document.querySelectorAll('.st-' + cb.dataset.st).forEach(e => e.style.display = cb.checked ? '' : 'none')));
document.getElementById('tg-built').addEventListener('change', e => document.getElementById('built').style.display = e.target.checked ? '' : 'none');
document.getElementById('tg-goals').addEventListener('change', e => document.getElementById('goals').style.display = e.target.checked ? '' : 'none');
</script></body></html>"""
open(out_p, "w").write(html)
print(out_p, summary)
