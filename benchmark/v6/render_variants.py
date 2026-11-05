"""Isaac Sim pictures of each v6 variant's start scene: a few views that show what the variant is about.

    $ISAACLAB_PYTHON benchmark/v6/render_variants.py --task T01 [--out ~/Pictures]

One Isaac process per picture set (task, variant, layout; the layout's first seed).  Views, written to
<out>/<task_id>/<variant>/<n>_<view>.png with a caption bar (variant, category, view, situation):

* ``first_person`` - the robot's head camera at the start (what the planner sees first);
* ``<object>``     - a close-up of each object the reference route picks up, where it starts;
* ``<support>``    - an overhead view of each support the route places things on, and of a large one that holds
  watched objects but is no place target (e.g. the table nobody eats at).

Only the start scene is rendered (no skill runs); a variant with several layouts gets one set per layout.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
RES = (720, 1280)
CAT = {"control": "对照", "action": "Action", "task": "Task", "action_task": "Action + Task"}


def _doc():
    return json.loads((HERE / "tasks.json").read_text())


def plan_views(task, lid):
    """[(kind, name)] from the reference route: picked objects, then supports placed on."""
    steps = task["routes"][task["oracle"][lid]]["steps"]
    objs, sups = [], []
    for s in steps:
        if s["skill"] == "pick" and s["args"]["object"] not in objs:
            objs.append(s["args"]["object"])
        r = s["args"].get("receptacle") or s["args"].get("container")
        if s["skill"] in ("place", "drop") and r and r not in sups:
            sups.append(r)
    return [("object", o) for o in objs] + [("support", s) for s in sups]


def caption(img, lines):
    from PIL import Image, ImageDraw, ImageFont
    big, small = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 20)
    head = textwrap.wrap(lines[0], 52)
    body = head[1:] + [w for line in lines[1:] for w in textwrap.wrap(line, 62)]
    lines = head[:1]
    h = 48 + 30 * len(body)
    out = Image.new("RGB", (img.width, img.height + h), (24, 26, 30))
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    d.text((18, img.height + 10), lines[0], font=big, fill=(255, 255, 255))
    for i, line in enumerate(body):
        d.text((18, img.height + 46 + 30 * i), line, font=small, fill=(210, 210, 210))
    return out


def place_hints(task, lid):
    """[(support, xy, label)] of the reference route's place calls with a hint, in order."""
    steps = task["routes"][task["oracle"][lid]]["steps"]
    hints = [(s["args"]["receptacle"], s["args"]["hint_xy"], s["args"]["object"]) for s in steps
             if s["skill"] == "place" and s["args"].get("hint_xy")]
    return [(r, xy, f"{i} {o}" if len(hints) > 1 else f"{o} 放这里") for i, (r, xy, o) in enumerate(hints, 1)]


def star(img, marks):
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 24)
    for uv, label in marks:
        if uv is None or not (0 <= uv[0] < img.width and 0 <= uv[1] < img.height):
            continue
        u, v = uv
        pts = [(u + (18 if k % 2 == 0 else 8) * math.sin(k * math.pi / 5),
                v - (18 if k % 2 == 0 else 8) * math.cos(k * math.pi / 5)) for k in range(10)]
        d.polygon(pts, fill=(255, 205, 40), outline=(90, 60, 0))
        w = d.textlength(label, font=font)
        x = u + 20 if u + 20 + w < img.width - 8 else u - 20 - w      # left of the star near the right edge
        d.text((x, v - 30), label, font=font, fill=(255, 225, 80), stroke_width=3, stroke_fill=(0, 0, 0))


def render_one(tid, vid, lid, seed, out_dir, situation):
    import numpy as np
    import torch
    from PIL import Image
    from benchmark.run_episode import PLANNER_PROFILES
    from benchmark.scene import episode_config
    from episode.catalog import resolve_task
    from episode.episode import Episode
    from episode.profile import load_profile
    from zeno_skills.runtime import _clear

    doc = _doc()
    task = next(t for t in doc["tasks"] if t["task_id"] == tid)
    cat = CAT[task["v6_tracks"][vid]["category"]]
    cfg = episode_config(task, seed, lid)
    rtask = resolve_task(task, lid)
    tmp = Path(tempfile.mkdtemp(prefix="v6render_"))
    ep = Episode(rtask, cfg, load_profile(PLANNER_PROFILES["oracle"]), tmp, video=True, images=True,
                 video_res=RES)
    rig = ep.rig
    cam = rig.cams["follow"]
    f32 = torch.float32

    view = {}

    def shot(eye, tgt):
        cam.set_world_poses_from_view(torch.tensor([eye], dtype=f32), torch.tensor([tgt], dtype=f32))
        view.update(eye=np.asarray(eye, float), tgt=np.asarray(tgt, float))
        for _ in range(6):
            rig.sim.render()
        return rig._read(cam)

    def project(p):
        """World point -> pixel of the last shot (None behind the camera)."""
        f = view["tgt"] - view["eye"]
        f /= np.linalg.norm(f)
        r = np.cross(f, [0.0, 0.0, 1.0])
        r /= np.linalg.norm(r)
        dn = np.cross(f, r)
        q = np.asarray(p, float) - view["eye"]
        x, y, z = q @ r, q @ dn, q @ f
        if z <= 0.05:
            return None
        K = cam.data.intrinsic_matrices[0].cpu().numpy()
        return float(K[0, 0] * x / z + K[0, 2]), float(K[1, 1] * y / z + K[1, 2])

    def around(tgt, dist, height):
        """A clear eye on a circle around the target, the robot's side first."""
        bx, by, _ = rig.base_pose()
        a0 = math.atan2(by - tgt[1], bx - tgt[0])
        for k in (0, 1, -1, 2, -2, 3, -3, 4):
            a = a0 + k * math.pi / 4
            eye = [tgt[0] + dist * math.cos(a), tgt[1] + dist * math.sin(a), tgt[2] + height]
            if _clear(rig.world, eye, tgt):
                return eye
        return [tgt[0] + 0.05, tgt[1], tgt[2] + dist + height]

    st = rig.state()
    views = [("first_person", None, rig.get_first_person_image(), "机器人开局第一视角")]
    place_sups = {n for k, n in plan_views(task, lid) if k == "support"}
    picked = {cfg["move"].get(n, {}).get("support") for k, n in plan_views(task, lid) if k == "object"}
    other = []                  # a table with watched objects that is no place target (the table nobody eats at)
    for n in rtask.get("watch") or []:
        sup = cfg["move"].get(n, {}).get("support")
        if sup and sup not in place_sups | picked | set(other):
            b = rig.ann.support(sup)["aabb_xy"]
            if max(b[2] - b[0], b[3] - b[1]) > 0.9:
                other.append(sup)
    # a watched container the route neither picks nor fills (the toy bin next to the kitchen bin, the fruit basket)
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    used = {n for _, n in plan_views(task, lid)}
    for n in rtask.get("watch") or []:
        o = rig.ann.objects.get(n)
        if o and n not in used and n in st["objects"] and assets.get(o.get("asset"), {}).get("container") \
                and not (cfg["move"].get(n, {}).get("support") or "").endswith("/inside_shelf"):
            other.append(n)
    for kind, name in plan_views(task, lid) + [("other", s) for s in other]:
        if kind == "object":
            if name not in st["objects"] or (cfg["move"].get(name, {}).get("support") in place_sups and
                                              not any(k == "object" and n == name for k, n in plan_views(task, lid)[:1])
                                              and name != (task.get("watch") or [None])[0]):
                continue                         # seen in the overhead view of its support
            p = [float(v) for v in st["objects"][name]["pos"]]
            sup = cfg["move"].get(name, {}).get("support") or ""
            if sup.endswith("/inside_shelf"):    # in closed furniture: the furniture from the room, the item starred
                b = rig.ann.support(sup)["aabb_xy"]
                c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, p[2]]
                img = shot(around(c, 1.6, 0.7), c)
                views.append((name, [(project(p), f"{name} 在里面")], img,
                              f"要拿的 {name} 在关着的 {sup.split('/')[0]} 里（从外面看，★ 是它的位置）"))
                continue
            views.append((name, None, shot(around(p, 0.75, 0.55), p), f"要拿的 {name}（开局位置）"))
        elif name in st["objects"]:              # a container object (a bin, a basket, a tray): from above at an angle
            p = [float(v) for v in st["objects"][name]["pos"]]
            img = shot(around(p, 0.7, 0.8), p)
            views.append((name, None, img, f"放进 {name}（开局位置）" if kind == "support" else
                          f"{name}（开局位置）：相关的容器，但不是放置处"))
        else:
            s = rig.ann.support(name)
            b = s["aabb_xy"]
            c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, s["z"]]
            span = max(b[2] - b[0], b[3] - b[1])
            if min(b[2] - b[0], b[3] - b[1]) < 0.5:   # a narrow top along a wall: from its room side at an angle
                from benchmark.v6.layout import room_of
                ax = (0, 1) if b[2] - b[0] > b[3] - b[1] else (1, 0)     # across the long side
                room = room_of(cfg["base"], c)
                eyes = [[c[0] + k * 1.2 * ax[0], c[1] + k * 1.2 * ax[1], c[2] + 0.8] for k in (1, -1)]
                eye = next((e for e in eyes if room_of(cfg["base"], e) == room), eyes[0])
            elif span > 0.9:                     # a long table from above, slightly tilted
                eye = [c[0] + 0.25, c[1] - 0.05, c[2] + 0.75 * span + 0.3]
                if not _clear(rig.world, eye, c):
                    eye = around(c, 0.8, 0.75 * span)
            else:
                eye = around(c, 0.9, 0.8)
            img = shot(eye, c)
            hints = [h for h in place_hints(task, lid) if h[0] == name]
            marks = [(project([h[1][0], h[1][1], s["z"] + 0.03]), h[2]) for h in hints]
            print(f"[marks] {name} {marks}", flush=True)
            views.append((name.replace("/", "_"), marks, img, (f"放置处 {name}（俯视）" if kind == "support" else
                                                               f"{name}（俯视）：上面有相关物体，但不是放置处")
                          + ("，★ 参考路线的放置点（按顺序）" if marks else "")))
    viewer = (task["variants"][lid].get("v6") or {}).get("viewer")
    if viewer:                                   # what a person sees from where they are (e.g. lying in bed)
        for sup in viewer["targets"]:
            s = rig.ann.support(sup)
            b = s["aabb_xy"]
            views.append((f"view_{sup.replace('/', '_')}", None,
                          shot(viewer["eye"], [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, s["z"] + 0.05]),
                          f"{viewer['label']}：看向 {sup}"))
    out_dir.mkdir(parents=True, exist_ok=True)
    lay = f" · 摆法 {lid.split('__', 1)[1]}" if lid != vid else ""
    for i, (tag, marks, img, label) in enumerate(views, 1):
        im = Image.fromarray(np.asarray(img, dtype=np.uint8))
        if im.width < RES[1]:
            im = im.resize((RES[1], round(im.height * RES[1] / im.width)))
        if marks:
            star(im, marks)
        im = caption(im, [f"{tid.split('_')[0]} · {vid}（{cat}）{lay} · seed {seed} · {label}", situation])
        path = out_dir / f"{(lid.split('__', 1)[1] + '_') if lid != vid else ''}{i}_{tag}.png"
        im.save(path)
        print(f"[render] {path}", flush=True)
    ep.close()
    os._exit(0)                                  # Isaac Sim does not shut down by itself


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", help="task id prefix, e.g. T01")
    ap.add_argument("--variant", help="only this variant")
    ap.add_argument("--out", default=str(Path.home() / "Pictures"))
    ap.add_argument("--one", nargs=4, metavar=("TASK", "VARIANT", "LAYOUT", "SEED"), help=argparse.SUPPRESS)
    a = ap.parse_args()
    from benchmark.v6.success_routes import situations
    sit = situations()
    if a.one:
        tid, vid, lid, seed = a.one
        try:
            render_one(tid, vid, lid, int(seed), Path(a.out) / tid / vid, sit.get((tid.split("_")[0], vid), ""))
        except BaseException:
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(1)                          # Isaac Sim would hang on a normal exit after an error
        return
    py = os.environ.get("ISAACLAB_PYTHON", sys.executable)
    for t in _doc()["tasks"]:
        if not t["task_id"].startswith(a.task or ""):
            continue
        for vid, info in t["v6_variants"].items():
            if a.variant and vid != a.variant:
                continue
            for lid in info["layouts"]:
                seed = min(int(s) for s, x in info["seeds"].items() if x == lid)
                cmd = [py, __file__, "--out", a.out, "--one", t["task_id"], vid, lid, str(seed)]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
                except subprocess.TimeoutExpired:
                    print(f"{t['task_id']} {lid} s{seed}: TIMEOUT", flush=True)
                    continue
                done = [x for x in r.stdout.splitlines() if x.startswith("[render]")]
                print("\n".join(x for x in r.stdout.splitlines() if x.startswith("[marks]")), flush=True)
                print(f"{t['task_id']} {lid} s{seed}: {len(done)} pictures" +
                      ("" if r.returncode == 0 and done else f" FAILED\n{r.stderr[-2000:]}{r.stdout[-1500:]}"),
                      flush=True)


if __name__ == "__main__":
    main()
