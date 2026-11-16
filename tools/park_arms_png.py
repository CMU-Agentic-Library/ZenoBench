"""All candidate arms of one park search, overlaid, as a PNG: a top view, a view along the approach
(from behind the bases, towards the goals) and a view across it.

The dump (zeno_skills.park_search, env ZB_PARK_DUMP) keeps the first ranked candidates' arms at their
ranking solution ("ranked_arms": collision spheres, depth > 0 where one penetrates the world) and the
colliders near the goals ("world").  Every sphere is a half-transparent disc on top of the others:
grey clear, red penetrating; colliders as their outlines (the target object orange, a moving part
teal, other objects blue); the bases as arrows (green: the arm clear, red: it penetrates); the
goals (relay poses) as yellow dots.  Tools/park_arms_view.py draws the same in 3D (WebGL).

usage: $ISAACLAB_PYTHON tools/park_arms_png.py <dump.json> <out.png> [title] [target object]
"""
import collections
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import EllipseCollection, PolyCollection
from scipy.spatial import ConvexHull

dump_p, out_p = sys.argv[1:3]
title = sys.argv[3] if len(sys.argv) > 3 else "candidate arms"
target = sys.argv[4] if len(sys.argv) > 4 else None
D = json.load(open(dump_p))
arms = D.get("ranked_arms", [])
goals = np.asarray([g[:3] for g in D.get("goals", [])], float)
c = goals.mean(0) if len(goals) else np.zeros(3)
bases = np.asarray([a["base"] for a in arms], float) if arms else np.zeros((0, 3))
# the approach: from the bases' mean towards the goals (u), across it (v)
d = (c[:2] - bases[:, :2].mean(0)) if len(bases) else np.array([1.0, 0.0])
u = d / (np.linalg.norm(d) or 1.0)
v = np.array([-u[1], u[0]])

S, pen = [], []
for a in arms:
    sp = np.asarray([s[:5] for s in a["spheres"]], float)
    S.append(sp)
    pen.append(bool((sp[:, 4] > 0).any()))
S_all = np.vstack(S) if S else np.zeros((0, 5))
hit = S_all[:, 4] > 0

COL = {"static": "#8a8f96", "object": "#5b8bd6", "target": "#e58b2a", "part": "#2f9aa3"}


def kind(w):
    if w["owner"].startswith("object:"):
        return "target" if target and w["owner"] == f"object:{target}" else "object"
    return "part" if w["owner"].startswith("part:") else "static"


views = [  # (name, horizontal axis, vertical axis, axis labels)
    ("top view", lambda P: P[:, 0], lambda P: P[:, 1], ("x (m)", "y (m)")),
    ("along the approach (from behind the bases)", lambda P: P[:, :2] @ v, lambda P: P[:, 2],
     ("across the approach (m)", "z (m)")),
    ("across the approach (side)", lambda P: P[:, :2] @ u, lambda P: P[:, 2], ("along the approach (m)", "z (m)")),
]
fig, axs = plt.subplots(1, 3, figsize=(21, 8), dpi=110)
for ax, (name, H, V, lab) in zip(axs, views):
    # colliders: their outline in this view (the convex hull of the projected vertices)
    polys = {k: [] for k in COL}
    for w in D.get("world", []):
        P = np.asarray(w["v"], float)
        Q = np.c_[H(P), V(P)]
        try:
            h = ConvexHull(Q)
            polys[kind(w)].append(Q[h.vertices])
        except Exception:
            pass
    for k in ("static", "object", "part", "target"):
        if polys[k]:
            ax.add_collection(PolyCollection(polys[k], facecolors=COL[k], edgecolors=COL[k],
                                             alpha=0.9 if k == "target" else 0.10, linewidths=0.6))
            ax.add_collection(PolyCollection(polys[k], facecolors="none", edgecolors=COL[k],
                                             alpha=0.5, linewidths=0.5))
    # arm spheres: clear first, penetrating on top
    for mask, colr, al in ((~hit, "#7d8794", 0.012), (hit, "#e0402a", 0.04)):
        P = S_all[mask]
        if len(P):
            r2 = 2 * P[:, 3]
            ax.add_collection(EllipseCollection(r2, r2, np.zeros(len(P)), units="xy",
                                                offsets=np.c_[H(P[:, :3]), V(P[:, :3])],
                                                transOffset=ax.transData, facecolors=colr, edgecolors="none",
                                                alpha=al))
    if len(goals):
        ax.scatter(H(goals), V(goals), s=14, c="#f2c230", edgecolors="#8a6d00", linewidths=0.4, zorder=5)
    if name == "top view" and len(bases):
        for b, p in zip(bases, pen):
            t = np.radians(b[2])
            ax.arrow(b[0], b[1], 0.10 * np.cos(t), 0.10 * np.sin(t), width=0.004, head_width=0.03,
                     color="#e0402a" if p else "#3aa35a", alpha=0.35, length_includes_head=True)
    if name == "top view":       # the base poses rejected before any arm, by reason
        for why, colr in (("out_of_reach", "#9aa0a6"), ("footprint", "#8e5bc4"), ("travel_pose", "#3f8fd1"),
                          ("ik", "#c98a12")):
            L = np.asarray([c_[:3] for c_ in D.get("rejected", {}).get(why, [])], float)
            if len(L):
                ax.scatter(L[:, 0], L[:, 1], s=3, c=colr, alpha=0.35, linewidths=0,
                           label=f"rejected: {why} ({len(L)})")
        ax.legend(loc="upper right", fontsize=8, markerscale=3)
    if name != "top view":
        ax.axhline(0.0, color="#555", lw=0.8)
    # limits: the goals and the arms
    pts = np.vstack([goals, S_all[:, :3]]) if len(S_all) else goals
    hx, vy = H(pts), V(pts)
    if name == "top view" and len(bases):
        hx, vy = np.r_[hx, bases[:, 0]], np.r_[vy, bases[:, 1]]
    if name == "top view" and not len(bases):   # no arm: frame the rejected bases near the goals
        RB = np.asarray([c_[:2] for L in D.get("rejected", {}).values() for c_ in L], float)
        if len(RB):
            RB = RB[np.linalg.norm(RB - c[:2], axis=1) < 1.5]
            hx, vy = np.r_[hx, RB[:, 0]], np.r_[vy, RB[:, 1]]
    pad = 0.25
    ax.set_xlim(hx.min() - pad, hx.max() + pad)
    ax.set_ylim(min(vy.min() - pad, 0.0 if name != "top view" else vy.min() - pad), vy.max() + pad)
    ax.set_aspect("equal")
    ax.set_title(name)
    ax.set_xlabel(lab[0])
    ax.set_ylabel(lab[1])
    ax.grid(alpha=0.2)

rej = D.get("rejected", {})
hits = collections.Counter(l for a in arms for l in {s[5] for s in a["spheres"] if s[4] > 0})
built = collections.Counter(b[4].split(" (")[0] for b in D.get("built", []))
txt = (f"{D.get('label')}: found {D.get('found')} | candidates rejected: out of reach {len(rej.get('out_of_reach', []))}, "
       f"footprint {len(rej.get('footprint', []))}, travel pose {len(rej.get('travel_pose', []))}, "
       f"no IK {len(rej.get('ik', []))} | with IK {len(D.get('ranked', []))}, drawn {len(arms)} "
       f"(clear {pen.count(False)}, penetrating {pen.count(True)})\n"
       f"links penetrating (arms): {', '.join(f'{k} {n}' for k, n in hits.most_common(8)) or '-'}\n"
       f"built {len(D.get('built', []))}: {'; '.join(f'{k} x{n}' for k, n in built.most_common(3)) or '-'}")
fig.suptitle(title, fontsize=14, x=0.01, ha="left")
fig.text(0.01, 0.01, txt, fontsize=9, family="monospace", va="bottom")
fig.tight_layout(rect=(0, 0.07, 1, 0.96))
fig.savefig(out_p)
print(out_p, f"{len(arms)} arms, {len(S_all)} spheres ({int(hit.sum())} penetrating)")
