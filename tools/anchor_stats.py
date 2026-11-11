"""The errors and re-plans of a set of episodes (docs/MOTION_ARCHITECTURE.md 9.3 step 2.1): what the
error bounds of 8.2 / 8.4 (BASE_TOL, HOLD_DRIFT, HELD_POSE_MARGIN, PICK_TOL, PLACE_TOL) are set from,
and the counts the open questions of section 10 wait on, read from the events every result.json has.

    python tools/anchor_stats.py RUN_DIR [RUN_DIR ...] [--out ANCHOR_STATS.md]

Sections:
  1. anchors: how the State read back stands off the one the plan assumed there (run's ``anchor``
     event, ``off``: motion_state.state_offset) -- the base, the hold, the watched objects / parts,
     objects knocked (``moved``)
  2. contact poses: how much further off its target a contact pose's segment stood than built when
     it ran (``segment`` events, ``aim_off``: primitives.aim_excess) -- what PICK_TOL / PLACE_TOL cut
  3. the hold planned before the close against the one measured (``held_offset``, by grasp kind)
  4. re-plans: the anchors' checks (kept / rebuilt / failed, why each was rebuilt, seconds) and the
     segments that no longer held (run's rebuild, why)
  5. decisions: how each was made (prior kept / solved again: decide_ik)
  6. park search: time, time per stage built, time before building (filter_s), why builds failed
Standard library only (runs on the host)."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def episodes(dirs):
    for d in dirs:
        for f in sorted(Path(d).glob("**/result.json")):
            try:
                r = json.loads(f.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            yield str(f.parent.relative_to(d)), r


def dist(xs, unit=""):
    """n, median, p90, max of xs."""
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return "n 0"
    p90 = xs[min(len(xs) - 1, int(round(0.9 * (len(xs) - 1))))]
    return f"n {len(xs)}, median {statistics.median(xs):.2f}{unit}, p90 {p90:.2f}{unit}, max {xs[-1]:.2f}{unit}"


def over(xs, cuts):
    """How many of xs exceed each cut."""
    xs = [x for x in xs if x is not None]
    return ", ".join(f">{c}: {sum(x > c for x in xs)}" for c in cuts)


def bucket(why):
    """A reason with its numbers taken out (to count alike reasons together)."""
    return re.sub(r"-?\d+(\.\d+)?", "#", str(why))[:110]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()

    n_ep = 0
    anchors = defaultdict(list)          # anchor name -> [(episode, off)]
    aims = defaultdict(list)             # segment name -> [[mm, deg, moved_mm]]
    held_off = defaultdict(list)         # grasp kind -> [(mm, deg)]
    checks = defaultdict(Counter)        # anchor -> kept / rebuilt / failed / unchecked
    check_s = []
    why_rebuilt, anchor_fail, seg_why, seg_fail = Counter(), Counter(), Counter(), Counter()
    rebuilt_where = Counter()
    decided = defaultdict(Counter)
    ps_s, ps_build_s, stage_s, filter_s, build_failed = [], [], Counter(), Counter(), Counter()
    ps_none = 0
    for ep, r in episodes(a.dirs):
        n_ep += 1
        for e in r.get("events") or []:
            lab = e.get("label")
            if lab == "anchor":
                name = e.get("target")
                if "off" in e:
                    anchors[name].append((ep, e["off"]))
                if "kept" not in e:
                    checks[name]["unchecked"] += 1
                elif e["kept"] is None:
                    checks[name]["failed"] += 1
                    anchor_fail[bucket(e.get("why"))] += 1
                else:
                    checks[name]["rebuilt" if e.get("rebuilt") else "kept"] += 1
                    for s in e.get("rebuilt") or []:
                        rebuilt_where[f"{name} -> {s}"] += 1
                    for s, w in (e.get("why_rebuilt") or {}).items():
                        why_rebuilt[f"{s}: {bucket(w)}"] += 1
                if e.get("seconds") is not None:
                    check_s.append(e["seconds"])
            elif lab == "segment":
                if e.get("aim_off"):
                    aims[e["target"]].append(e["aim_off"])
                for d, how in (e.get("decided") or {}).items():
                    decided[d][how] += 1
                if e.get("reused") is False:
                    if e.get("rebuilt") is None:
                        seg_fail[f"{e.get('target')}: {bucket(e.get('why'))}"] += 1
                    else:
                        seg_why[f"{e.get('target')}: {bucket(e.get('why'))}"] += 1
            elif lab == "held_offset":
                held_off[e.get("kind", "?")].append((e.get("offset_m", 0.0) * 1000.0, e.get("turn_deg")))
            elif lab == "park_search":
                if e.get("seconds") is not None:
                    ps_s.append(e["seconds"])
                if e.get("build_seconds") is not None:
                    ps_build_s.append(e["build_seconds"])
                if e.get("found") is None:
                    ps_none += 1
                stage_s.update(e.get("stage_s") or {})
                filter_s.update(e.get("filter_s") or {})
                for why, k in (e.get("build_failed") or {}).items():
                    build_failed[bucket(why)] += k if isinstance(k, (int, float)) else 1

    L = [f"# Anchor / re-plan statistics ({n_ep} episodes)", "", "Directories: " + ", ".join(a.dirs), ""]

    L += ["## 1. Anchors: the State read back against the one assumed", ""]
    for name in sorted(anchors):
        offs = [o for _, o in anchors[name]]
        L.append(f"### {name} ({len(offs)})")
        L.append(f"- base mm: {dist([o['base'][0] for o in offs])}; {over([o['base'][0] for o in offs], (1, 3, 7))}")
        L.append(f"- base deg: {dist([o['base'][1] for o in offs])}")
        arm = [o.get("arm") for o in offs]
        if any(arm):
            L.append(f"- commanded arm off the plan's, rad: {dist(arm)}")
        for side in ("right", "left"):
            hs = [o[f"hold_{side}"] for o in offs if f"hold_{side}" in o]
            same = [h for h in hs if "mm" in h]
            if same:
                L.append(f"- hold {side} mm: {dist([h['mm'] for h in same])}; {over([h['mm'] for h in same], (1, 2, 5, 10))}")
                L.append(f"- hold {side} deg: {dist([h['deg'] for h in same])}")
                kinds = Counter(h["kind"] for h in same)
                if len(kinds) > 1:
                    for k in sorted(kinds):
                        L.append(f"  - {k}: mm {dist([h['mm'] for h in same if h['kind'] == k])}")
            other = [h for h in hs if "mm" not in h]
            if other:
                changed = Counter("%s -> %s" % (h["assumed"], h["now"]) for h in other)
                L.append(f"- hold {side} changed: {changed.most_common(5)}")
        w_obj = [v for o in offs for v in (o.get("watch") or {}).values() if isinstance(v, list)]
        w_part = [v for o in offs for v in (o.get("watch") or {}).values() if isinstance(v, (int, float))]
        w_gone = sum(v is None for o in offs for v in (o.get("watch") or {}).values())
        if w_obj:
            L.append(f"- watched object mm: {dist([v[0] for v in w_obj])}; {over([v[0] for v in w_obj], (1, 5, 10, 20))}")
            L.append(f"- watched object deg: {dist([v[1] for v in w_obj])}")
        if w_part:
            L.append(f"- watched part (rad / m): {dist([abs(v) for v in w_part])}")
        if w_gone:
            L.append(f"- watched not in the State: {w_gone}")
        moved = [(ep, n, d) for ep, o in anchors[name] for n, d in (o.get("moved") or {}).items()]
        if moved:
            L.append(f"- others knocked > 5 mm since the plan: {len(moved)} in {len({m[0] for m in moved})} episodes")
            for ep, n, d in sorted(moved, key=lambda m: -m[2][0])[:8]:
                L.append(f"  - {n} {d[0]:.0f} mm {d[1]:.1f} deg ({ep})")
        L.append("")

    L += ["## 2. Contact poses: further off the target than built, when run", "",
          "| segment | n | mm | deg | mm over | target moved mm |", "|---|---|---|---|---|---|"]
    for name in sorted(aims):
        xs = aims[name]
        L.append(f"| {name} | {len(xs)} | {dist([x[0] for x in xs])} | {dist([x[1] for x in xs])} | "
                 f"{over([x[0] for x in xs], (1, 2, 5))} | {dist([x[2] for x in xs if len(x) > 2])} |")
    L.append("")

    L += ["## 3. Hold planned before the close vs measured (held_offset)", ""]
    for k in sorted(held_off):
        xs = held_off[k]
        L.append(f"- {k}: mm {dist([x[0] for x in xs])}; {over([x[0] for x in xs], (2, 5, 10))}; "
                 f"deg {dist([x[1] for x in xs])}")
    L.append("")

    L += ["## 4. Re-plans", "", "| anchor | kept | rebuilt | failed | unchecked |", "|---|---|---|---|---|"]
    for name in sorted(checks):
        c = checks[name]
        L.append(f"| {name} | {c['kept']} | {c['rebuilt']} | {c['failed']} | {c['unchecked']} |")
    L.append("")
    L.append(f"- anchor check seconds: {dist(check_s, ' s')}")
    for title, cnt in (("rebuilt at an anchor", rebuilt_where), ("why rebuilt at an anchor", why_rebuilt),
                       ("an anchor's rest could not be built", anchor_fail),
                       ("a segment no longer held, built again", seg_why), ("...and could not be built", seg_fail)):
        if cnt:
            L.append(f"- {title}:")
            L += [f"  - {k}: {v}" for k, v in cnt.most_common(15)]
    L.append("")

    L += ["## 5. Decisions (decide_ik)", ""]
    for d in sorted(decided):
        L.append(f"- {d}: {dict(decided[d])}")
    L.append("")

    tot = sum(stage_s.values())
    L += ["## 6. Park search", "",
          f"- searches {len(ps_s)} (none found {ps_none}): {dist(ps_s, ' s')}, total {sum(ps_s):.0f} s; "
          f"building {sum(ps_build_s):.0f} s"]
    if tot:
        L.append("- time per stage built: " + ", ".join(f"{k} {v:.0f} s ({100 * v / tot:.0f}%)"
                                                        for k, v in stage_s.most_common() if v >= 0.5))
    if filter_s:
        L.append("- before building (filter_s): " + ", ".join(f"{k} {v:.0f} s" for k, v in filter_s.most_common()))
    if build_failed:
        L.append("- builds failed:")
        L += [f"  - {k}: {v}" for k, v in build_failed.most_common(12)]
    L.append("")

    text = "\n".join(L)
    if a.out:
        Path(a.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
