"""Isaac Sim pictures of each v6 variant's start scene: a few views that show what the variant is about.

    $ISAACLAB_PYTHON benchmark/v6/render_variants.py --task T01 [--out ~/Pictures]

One Isaac process per variant (its first layout and seed; ``--all-layouts`` for every layout), at most three
pictures: what is taken, where it goes, and what the variant turns on.  Only what the task is
about is shown - every asset the reference route or the goal names - each starred with its role, written to
<out>/<task_id>/<variant>/<n>_<asset>.png with a caption bar (variant, category, view, situation):

* what the robot takes (or stacks on): a close-up where it starts (in closed furniture: the furniture, starred);
* where things go: the support or container, the route's place points starred, what must stay there named;
* furniture to open and appliances to run;
* a support with things that must stay or with look-alikes the challenge is built on, each starred.

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


def accepted_spots(goal_atoms, cfg, sup, aabb, step=0.02):
    """Where on ``sup`` the goal accepts the placed object: every (x, y) of a grid whose footprint (either way
    round) is inside the support and meets the goal's clear_of / near_any / not near_any atoms, judged on the
    footprints as the goal predicates do.  [] when the goal has no such atom for an object on ``sup``."""
    import benchmark.v6.layout as L
    on = [a for a in goal_atoms if a[0] == "on" and len(a) > 2 and a[2] == sup]
    if not on:
        return []
    obj = on[0][1]
    rules = [a for a in goal_atoms if a[0] in ("clear_of", "near_any", "not near_any") and a[1] == obj]
    if not rules:
        return []
    add, move = cfg.get("add") or {}, cfg.get("move") or {}
    names = {n for a in rules for n in a[2]}
    boxes = {n: L._box(L._asset_of(cfg["base"], n, add), move.get(n) or add[n]) for n in names
             if (move.get(n) or add.get(n) or {}).get("support") == sup}
    asset = L._asset_of(cfg["base"], obj, add)

    def gap(p, q):
        return math.hypot(max(0.0, max(p[0], q[0]) - min(p[2], q[2])), max(0.0, max(p[1], q[1]) - min(p[3], q[3])))

    def fits(bk):
        if bk[0] < aabb[0] or bk[1] < aabb[1] or bk[2] > aabb[2] or bk[3] > aabb[3]:
            return False
        for a in rules:
            near = [gap(bk, boxes[n]) for n in a[2] if n in boxes]
            d = float(a[3])
            if a[0] == "clear_of" and near and min(near) < d - 0.003:
                return False
            if a[0] == "near_any" and (not near or min(near) > d):
                return False
            if a[0] == "not near_any" and near and min(near) <= d:
                return False
        return True
    out = []
    x = aabb[0]
    while x <= aabb[2]:
        y = aabb[1]
        while y <= aabb[3]:
            if any(fits(L._box(asset, {"xy": [x, y], "yaw_deg": yaw})) for yaw in (0.0, 90.0)):
                out.append((x, y))
            y += step
        x += step
    return out


def paint_spots(img, pixels, r=6):
    """Translucent green dots on an image array at the given pixels."""
    import numpy as np
    from PIL import Image, ImageDraw
    im = Image.fromarray(np.asarray(img, dtype=np.uint8)).convert("RGBA")
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for p in pixels:
        if p is not None and 0 <= p[0] < im.width and 0 <= p[1] < im.height:
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(40, 220, 90, 110))
    return np.asarray(Image.alpha_composite(im, layer).convert("RGB"))


def star(img, marks):
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 24)
    marks = [m for m in marks if m[0] is not None and 0 <= m[0][0] < img.width and 0 <= m[0][1] < img.height]
    for (u, v), _ in marks:
        pts = [(u + (18 if k % 2 == 0 else 8) * math.sin(k * math.pi / 5),
                v - (18 if k % 2 == 0 else 8) * math.cos(k * math.pi / 5)) for k in range(10)]
        d.polygon(pts, fill=(255, 205, 40), outline=(90, 60, 0))
    boxes = []                                   # labels already drawn: a new one moves down until it is free
    for (u, v), label in marks:
        w = d.textlength(label, font=font)
        x = u + 20 if u + 20 + w < img.width - 8 else u - 20 - w      # left of the star near the right edge
        y = v - 30
        while any(x < b[2] and b[0] < x + w and y < b[3] and b[1] < y + 30 for b in boxes):
            y += 32
        if y > v - 10:                           # moved off its star: a thin leader line back to it
            d.line([(u, v), (x if x > u else x + w, y + 15)], fill=(255, 225, 80), width=2)
        boxes.append((x, y, x + w, y + 30))
        d.text((x, y), label, font=font, fill=(255, 225, 80), stroke_width=3, stroke_fill=(0, 0, 0))


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

    def robot_clear(eye, tgt):
        """The line of sight does not pass through the robot's body (a column 0.45 m round its base, 1.7 m high)."""
        bx, by, _ = rig.base_pose()
        e, t = np.asarray(eye, float), np.asarray(tgt, float)
        for u in np.linspace(0.0, 1.0, 40):
            q = e + (t - e) * u
            if q[2] < 1.7 and math.hypot(q[0] - bx, q[1] - by) < 0.45:
                return False
        return True

    def around(tgt, dist, height):
        """A clear eye on a circle around the target (no furniture and not the robot in between); the side the
        robot comes from first, else any side, else straight above."""
        bx, by, _ = rig.base_pose()
        a0 = math.atan2(by - tgt[1], bx - tgt[0])
        for k in (0, 1, -1, 2, -2, 3, -3, 4):
            a = a0 + k * math.pi / 4
            eye = [tgt[0] + dist * math.cos(a), tgt[1] + dist * math.sin(a), tgt[2] + height]
            if _clear(rig.world, eye, tgt) and robot_clear(eye, tgt):
                return eye
        return [tgt[0] + 0.05, tgt[1], tgt[2] + dist + height]

    st = rig.state()
    objs = st["objects"]
    adds = cfg.get("add") or {}

    def sup_of(n):
        return ((cfg.get("move") or {}).get(n) or adds.get(n) or {}).get("support") or \
            (rig.ann.objects.get(n) or {}).get("support") or ""

    def pos(n):
        return [float(v) for v in objs[n]["pos"]]

    def furniture_box(name):
        """[x0, y0, z0, x1, y1, z1] of a piece of furniture or an appliance (its body parts)."""
        boxes = [o["aabb"] for o in rig.ann.obstacles if o["name"] == name or o["name"].startswith(name + "/")]
        boxes += [a["body_aabb"] for a in rig.ann.appliances if a["name"] == name]
        if not boxes:
            return None
        return [min(b[k] for b in boxes) for k in range(3)] + [max(b[k] for b in boxes) for k in range(3, 6)]

    def inside_eye(sp, z):
        """An item in closed furniture: an eye in front of a face of the furniture (in a room, a clear sight line
        to that face), aimed at the item's place inside."""
        from benchmark.v6.layout import room_of
        b = rig.ann.support(sp)["aabb_xy"]
        c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, z]
        box = furniture_box(sp.split("/")[0]) or [b[0], b[1], 0, b[2], b[3], z]
        faces = [([box[0] - 0.02, c[1]], (-1, 0)), ([box[3] + 0.02, c[1]], (1, 0)),
                 ([c[0], box[1] - 0.02], (0, -1)), ([c[0], box[4] + 0.02], (0, 1))]
        for (fx, fy), (dx, dy) in faces:
            for d in (1.6, 1.2, 2.0):
                eye = [fx + d * dx + 0.3 * dy, fy + d * dy + 0.3 * dx, z + 0.6]
                if room_of(cfg["base"], eye) and _clear(rig.world, eye, [fx, fy, z]) and robot_clear(eye, c):
                    return eye, c
        return around(c, 1.6, 0.7), c

    def support_eye(name):
        sp = rig.ann.support(name)
        b = sp["aabb_xy"]
        c = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, sp["z"]]
        span = max(b[2] - b[0], b[3] - b[1])
        if min(b[2] - b[0], b[3] - b[1]) < 0.5:   # a narrow top along a wall: from its room side at an angle
            from benchmark.v6.layout import room_of
            ax = (0, 1) if b[2] - b[0] > b[3] - b[1] else (1, 0)
            room = room_of(cfg["base"], c)
            along = (1 - ax[0], 1 - ax[1])
            eyes = [[c[0] + k * 1.2 * ax[0] + m * along[0], c[1] + k * 1.2 * ax[1] + m * along[1], c[2] + 0.8]
                    for m in (0.0, 0.6, -0.6) for k in (1, -1)]
            ok = [e for e in eyes if room_of(cfg["base"], e) == room]
            return next((e for e in ok if robot_clear(e, c)), ok[0] if ok else eyes[0]), c
        if span > 0.9:                           # a long table from above, slightly tilted
            eye = [c[0] + 0.25, c[1] - 0.05, c[2] + 0.75 * span + 0.3]
            return (eye if _clear(rig.world, eye, c) and robot_clear(eye, c) else around(c, 0.8, 0.75 * span)), c
        return around(c, 0.9, 0.8), c

    # ---- what the task is about: every asset the reference route or the goal names, with its role
    steps = task["routes"][task["oracle"][lid]]["steps"]
    role = {}                                    # asset -> role, in first-mention order

    def mark(n, r):
        if n and n not in role:
            role[n] = r
    for stp in steps:
        a, k = stp["args"], stp["skill"]
        if k == "pick":
            mark(a["object"], "take")
        elif k in ("place", "drop", "hide"):
            mark(a.get("receptacle") or a.get("container"), "place")
        elif k == "stack":
            mark(a["base"], "base")
        elif k in ("cover", "uncover", "stir"):
            mark(a["container"], "use")
            mark(a.get("lid") or a.get("tool"), "take")
        elif k == "wipe":
            mark(a["surface"], "place")
        elif k in ("open", "close", "explore_furniture"):
            mark(a.get("articulated") or a.get("furniture"), "open")
        elif k in ("heat", "stop"):
            mark(a["appliance"], "appliance")
        elif k == "press":
            mark(a["button"].split("/")[0], "appliance")
    goal = rtask.get("goal") or task.get("goal") or {}

    def atoms(g):
        if isinstance(g, dict):
            for x in g.get("all", []):
                yield from atoms(x)
            for grp in g.get("any", []):
                for x in grp:
                    yield from atoms(x)
        else:
            yield g
    PUT = ("on", "inside", "fully_inside", "on_top_of", "temperature_at_least", "covered")
    names = lambda x: [x] if isinstance(x, str) else list(x)  # noqa: E731
    stay = {n for at in atoms(goal) if at[0] == "near_start" for n in names(at[1])}
    for at in atoms(goal):                       # the goal allows it, the route uses another (another mug)
        if at[0] in PUT and not set(names(at[1])) & stay:     # a castle block on another one stays put
            for n in names(at[1]):
                if n in objs and n not in role:     # already where the goal wants it: it stays (the juice in the fridge)
                    role[n] = "keep" if at[0] == "on" and len(at) > 2 and sup_of(n) == at[2] else "alt"
    for at in atoms(goal):                       # what the place is judged against (the coffee drinker's mug)
        if at[0] == "near_any":
            for n in at[2]:
                if n in objs and n not in role:
                    role[n] = "ref"
    keep = set()
    for at in atoms(goal):
        if at[0] in ("near_start", "upright", "count_on_at_least"):
            keep.update(names(at[1]))
        elif at[0] in ("clear_of", "not near_any"):
            keep.update(at[2])
    for n in sorted(keep):
        if n in objs and n not in role:
            role[n] = "keep"
    for n in rtask.get("watch") or []:          # watched, never used: the look-alikes the challenge is built on
        if n in objs and n not in role:
            role[n] = "other"
    LABEL = {"take": "要拿", "base": "叠在它上面", "keep": "别动", "other": "相关", "use": "要用",
             "alt": "也可以用", "ref": "参照"}
    views, shown = [], set()

    def stars(names):
        return [(project(pos(n)), f"{LABEL[role[n]]}：{n}") for n in names if n in objs]

    kind = []                                   # per view: take / place / point (what the variant is about)
    # 1) what the robot takes (or stacks on): a close-up; in closed furniture, the furniture with the item starred
    for n, r in role.items():
        if r not in ("take", "base", "use") or n not in objs or n in shown:
            continue
        sp = sup_of(n)
        if sp.endswith("/inside_shelf"):
            eye, c = inside_eye(sp, pos(n)[2])
            img = shot(eye, c)
            shown.add(sp.split("/")[0])           # the furniture to open: this picture shows it
            views.append((n, [(project(pos(n)), f"{LABEL[r]}：{n}（在里面）")], img,
                          f"{LABEL[r]}的 {n}：在关着的 {sp.split('/')[0]} 里（从外面看，★ 是它的位置）"))
        else:
            img = shot(around(pos(n), 0.75, 0.55), pos(n))
            views.append((n, stars([n]), img, f"{LABEL[r]}的 {n}（开局位置）"))
        shown.add(n)
    kind += ["take"] * (len(views) - len(kind))
    # 2) where things go: the support or container, the route's place points starred, what must stay listed
    for n, r in role.items():
        if r != "place" or n in shown:
            continue
        if n in objs:                            # a container object (a bin, a basket, a pot): from above
            img = shot(around(pos(n), 0.7, 0.8), pos(n))
            views.append((n, None, img, f"放进 {n}（开局位置）"))
            shown.add(n)
            continue
        if n.endswith("/inside_shelf"):           # inside closed furniture: the furniture from outside
            eye, c = inside_eye(n, rig.ann.support(n)["z"] + 0.05)
            shown.add(n.split("/")[0])            # the same furniture needs no second picture to open it
        else:
            eye, c = support_eye(n)
        img = shot(eye, c)
        z = rig.ann.support(n)["z"]
        spots = [] if n.endswith("/inside_shelf") else accepted_spots(list(atoms(goal)), cfg, n,
                                                                      rig.ann.support(n)["aabb_xy"])
        if spots:                                # every place the goal accepts, not only the route's
            img = paint_spots(img, [project([x, y, z + 0.005]) for x, y in spots])
        marks = [(project([h[1][0], h[1][1], z + 0.03]), h[2]) for h in place_hints(task, lid) if h[0] == n]
        stay = [x for x, rr in role.items() if rr in ("keep", "other", "ref", "alt") and sup_of(x) == n]
        if not marks and n.endswith("/inside_shelf"):
            marks = [(project(c), f"放进 {n.split('/')[0]} 里")]
        marks += stars([x for x in stay if role[x] in ("other", "ref", "alt")])
        kept = [x for x in stay if role[x] == "keep"]
        shown.update([n, *stay])
        views.append((n.replace("/", "_"), marks, img, f"放置处 {n}" + ("；绿色：判定会通过的所有位置" if spots else "")
                      + ("，★ 参考路线的放置点" if any(
            h[0] == n for h in place_hints(task, lid)) else "") + (
            "" if not kept else f"；上面其余 {len(kept)} 件东西都别动" if len(kept) > 3 else f"；{'、'.join(kept)} 别动")))
    kind += ["place"] * (len(views) - len(kind))
    # 3) furniture to open and appliances to run
    for n, r in role.items():
        if r not in ("open", "appliance") or n in shown:
            continue
        box = furniture_box(n)
        if not box:
            continue
        c = [(box[0] + box[3]) / 2, (box[1] + box[4]) / 2, (box[2] + box[5]) / 2]
        img = shot(around(c, 1.4, 0.6), c)
        views.append((n, [(project([c[0], c[1], box[5]]), n)], img,
                      ("要打开再关好的 " if r == "open" else "要用的电器 ") + n))
        shown.add(n)
    kind += ["point"] * (len(views) - len(kind))
    # 4) supports with things that must stay or look-alikes, not shown yet: the support, each thing starred
    by_sup = {}
    for n, r in role.items():
        if r in ("keep", "other", "alt", "ref") and n not in shown and n in objs \
                and not sup_of(n).endswith("/inside_shelf"):
            by_sup.setdefault(sup_of(n), []).append(n)
    for sp, names in by_sup.items():
        if sp:
            try:
                eye, c = support_eye(sp)
            except Exception:
                p0 = pos(names[0])
                eye, c = around(p0, 0.8, 0.6), p0
        else:                                    # on the floor (a block castle): around them, what lies near too
            pts = [pos(n) for n in names]
            c = [sum(p[k] for p in pts) / len(pts) for k in range(3)]
            eye = around(c, 1.0, 0.9)
            names = names + [n for n, r in role.items() if r == "take" and n in objs and not sup_of(n)
                             and n not in names and math.dist(pos(n)[:2], c[:2]) < 0.8]
        img = shot(eye, c)
        kinds = sorted({LABEL[role[n]] for n in names})
        where = sp or "地上"
        views.append(((sp or "floor_" + names[0]).replace("/", "_"), stars(names), img,
                      f"{where} 的{'、'.join(kinds)}的东西：{'、'.join(names)}"))
        shown.update(names)
    for at in atoms(goal):                       # a surface that must be left alone (the clean table: not wiped)
        if at[0] == "not wiped" and at[1] not in shown:
            eye, c = support_eye(at[1])
            views.append((at[1].replace("/", "_"), None, shot(eye, c), f"别擦的 {at[1]}"))
            shown.add(at[1])
    kind += ["point"] * (len(views) - len(kind))
    viewer = (task["variants"][lid].get("v6") or {}).get("viewer")
    if viewer:                                   # what a person sees from where they are (e.g. lying in bed)
        for sup in viewer["targets"]:
            s = rig.ann.support(sup)
            b = s["aabb_xy"]
            views.append((f"view_{sup.replace('/', '_')}", None,
                          shot(viewer["eye"], [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2, s["z"] + 0.05]),
                          f"{viewer['label']}：看向 {sup}"))
    kind += ["view"] * (len(views) - len(kind))
    # a few pictures that show the variant: what is taken, where it goes, and what the variant turns on (a person's
    # view, a look-alike, the thing that must stay, the furniture to open); at most three
    in_goal = {x for at in atoms(goal) for a in at[1:] for x in (a if isinstance(a, list) else [a])
               if isinstance(x, str)}
    takes = [i for i, x in enumerate(kind) if x == "take"]
    searched = {s["args"].get("object") for s in steps if s["skill"] == "search"}
    found = [i for i in takes if views[i][0] in searched]      # what the robot had to find (the duck): shown too
    pick = (found + [i for i in takes if i not in found])[:3]          # up to three things to take (all of a sort)
    places = [i for i, x in enumerate(kind) if x == "place"]
    places.sort(key=lambda i: views[i][0].replace("_", "/") not in {g.replace("_", "/") for g in in_goal})
    goal_places = [i for i in places if views[i][0].replace("_", "/") in {g.replace("_", "/") for g in in_goal}]
    pick += sorted(places[:max(2, min(3, len(goal_places)))])  # the goal's destinations first (tray, toy box)
    pick += [i for i, x in enumerate(kind) if x in ("view", "point")][:max(0, 4 - len(pick))]
    views = [views[i] for i in sorted(pick)]
    out_dir.mkdir(parents=True, exist_ok=True)
    tag_l = lid.split('__', 1)[1] if '__' in lid else lid           # a merged v5 variant keeps its own name
    lay = f" · 摆法 {tag_l}" if lid != vid else ""
    for i, (tag, marks, img, label) in enumerate(views, 1):
        im = Image.fromarray(np.asarray(img, dtype=np.uint8))
        if im.width < RES[1]:
            im = im.resize((RES[1], round(im.height * RES[1] / im.width)))
        if marks:
            star(im, marks)
        im = caption(im, [f"{tid.split('_')[0]} · {vid}（{cat}）{lay} · seed {seed} · {label}", situation])
        path = out_dir / f"{(tag_l + '_') if lid != vid else ''}{i}_{tag}.png"
        im.save(path)
        print(f"[render] {path}", flush=True)
    ep.close()
    os._exit(0)                                  # Isaac Sim does not shut down by itself


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", help="task id prefix, e.g. T01")
    ap.add_argument("--variant", help="only this variant")
    ap.add_argument("--out", default=str(Path.home() / "Pictures"))
    ap.add_argument("--all-layouts", action="store_true", help="one picture set per layout (default: the first)")
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
            for lid in info["layouts"][:1] if not a.all_layouts else info["layouts"]:
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
