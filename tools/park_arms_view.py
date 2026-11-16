"""All candidate arms of one park search, overlaid in 3D: the data file of tools/park_arms_view.html.

The dump (zeno_skills.park_search, env ZB_PARK_DUMP) keeps the first ranked candidates' arms at their
ranking solution ("ranked_arms": collision spheres, depth > 0 where one penetrates the world) and the
colliders near the goals ("world").  Every arm is drawn half transparent on top of the others: grey
spheres clear, red spheres penetrating; the bases as arrows on the floor (green: the arm clear,
red: it penetrates), the goals (relay poses) as yellow dots.

usage: python3 tools/park_arms_view.py <dump.json> <dir> <id> [title] [target object] [png]
  writes <dir>/data/<id>.json and adds the episode to <dir>/data/index.json (copies the png to
  <dir>/data/<id>.png); open <dir>/index.html (a copy of tools/park_arms_view.html) over http.
"""
import collections
import json
import os
import shutil
import sys

dump_p, out_dir, ep_id = sys.argv[1:4]
title = sys.argv[4] if len(sys.argv) > 4 else ep_id
target = sys.argv[5] if len(sys.argv) > 5 else None
png = sys.argv[6] if len(sys.argv) > 6 else None
D = json.load(open(dump_p))

arms = D.get("ranked_arms", [])
world = []
for w in D.get("world", []):
    kind = "static"
    if w["owner"].startswith("object:"):
        kind = "target" if target and w["owner"] == f"object:{target}" else "object"
    elif w["owner"].startswith("part:"):
        kind = "part"
    world.append({"k": kind, "v": w["v"], "f": w["f"]})

# per link: in how many arms it penetrates; per arm: penetrating at all
hits = collections.Counter()
clear = 0
A = []
for a in arms:
    sp = a["spheres"]
    pen = sorted({s[5] for s in sp if s[4] > 0.0})
    hits.update(pen)
    clear += not pen
    A.append({"b": a["base"], "s": [[round(s[0], 3), round(s[1], 3), round(s[2], 3), round(s[3], 3),
                                     1 if s[4] > 0 else 0, 1 if s[5].startswith(("torso", "head")) else 0]
                                    for s in sp], "p": int(bool(pen))})

rej = D.get("rejected", {})
stats = {
    "label": D.get("label"),
    "found": D.get("found"),
    "goals": len(D.get("goals", [])),
    "out_of_reach": len(rej.get("out_of_reach", [])),
    "footprint": len(rej.get("footprint", [])),
    "travel_pose": len(rej.get("travel_pose", [])),
    "ik": len(rej.get("ik", [])),
    "ranked": len(D.get("ranked", [])),
    "drawn": len(arms),
    "clear": clear,
    "built": len(D.get("built", [])),
    "built_why": collections.Counter(b[4].split(" (")[0] for b in D.get("built", [])).most_common(4),
    "hits": hits.most_common(10),
}
goals = [g[:3] for g in D.get("goals", [])]

# the candidates rejected before any arm (their base poses), at most REJ_MAX per reason, evenly spread
REJ_MAX = 1500
rej_bases = {}
for why in ("out_of_reach", "footprint", "travel_pose", "ik"):
    L = rej.get(why, [])
    step = max(1, -(-len(L) // REJ_MAX))
    rej_bases[why] = [[round(c[0], 3), round(c[1], 3), round(c[2], 1)] for c in L[::step]]
data_dir = os.path.join(out_dir, "data")
os.makedirs(data_dir, exist_ok=True)
with open(os.path.join(data_dir, f"{ep_id}.json"), "w") as f:
    json.dump({"title": title, "target": target, "stats": stats, "world": world, "arms": A, "goals": goals,
               "rejected": rej_bases}, f,
              separators=(",", ":"))
if png:
    shutil.copy(png, os.path.join(data_dir, f"{ep_id}.png"))
idx_p = os.path.join(data_dir, "index.json")
idx = json.load(open(idx_p)) if os.path.exists(idx_p) else []
idx = [e for e in idx if e["id"] != ep_id] + [{"id": ep_id, "title": title, "png": bool(png),
                                               "arms": len(A), "clear": clear, "found": stats["found"]}]
json.dump(idx, open(idx_p, "w"), indent=1)
print(os.path.join(data_dir, f"{ep_id}.json"), f"{len(A)} arms ({clear} clear), {len(world)} colliders")
