"""Motion signature of a set of episodes, and its diff against a snapshot (docs/COLLISION_PLAN.md
section 5): which motions each skill makes and under what collision rules, read from the
``contacts.segments`` the motion record (zeno_skills/clearance.py, Clearance.motion) writes
into every result.json.

    python tools/motion_signature.py RUN_DIR [RUN_DIR ...]                 # the table
    python tools/motion_signature.py RUN_DIR --save tests/fixtures/motion_signature_approach_leave.json
    python tools/motion_signature.py RUN_DIR --compare tests/fixtures/motion_signature_approach_leave.json

A row is one kind of executed motion: (skill, leg, arm, allow, holding, relaxed), with how many
times it ran and in how many episodes.  ``allow`` is the Allow it ran under (free, planned,
fallback, leave_contact, into_contact, lifting, legacy, unchecked: <reason>, base_drive, raw
when a follow ran with no motion declared before it); ``relaxed`` what the collision queries
made for it left out (``exempt`` -- a target exempted, ``fingers`` / ``hand`` -- that hand's
own links not checked), since the previous motion.

The diff is the review: after a change, rows that appear or disappear are what the change did
to the motions, and each one is either meant or a bug.  Counts move with planning randomness
(GPU reductions, PLAN_TIMEOUT) and are shown, not judged; ``fallback`` is kept out of the row
key for the same reason (a planned leg falls back now and then) and counted beside it.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

KEY = ("skill", "leg", "side", "allow", "holding", "relaxed")


def _row_allow(seg):
    """The row's allow: a fallback counts as the planned leg it was meant to be."""
    return "planned" if seg.get("allow") == "fallback" else seg.get("allow")


def episodes(dirs):
    """(episode id, segments) of every result.json under ``dirs`` that has a motion record."""
    for d in dirs:
        for f in sorted(Path(d).rglob("result.json")):
            try:
                r = json.loads(f.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            segs = (r.get("contacts") or {}).get("segments")
            if segs is None:
                continue
            yield str(f.parent.relative_to(d)), segs


def signature(dirs):
    """{row key: {"n", "fallback", "episodes"}} and the number of episodes read."""
    rows = defaultdict(lambda: {"n": 0, "fallback": 0, "episodes": set()})
    n_ep = 0
    for ep, segs in episodes(dirs):
        n_ep += 1
        for s in segs:
            key = (s.get("skill") or "-", s.get("leg") or "-", s.get("side") or "-", _row_allow(s),
                   bool(s.get("holding")), ",".join(s.get("relaxed") or ()) or "-")
            r = rows[key]
            r["n"] += 1
            r["fallback"] += s.get("allow") == "fallback"
            r["episodes"].add(ep)
    return rows, n_ep


def to_json(rows, n_ep):
    return {"episodes": n_ep,
            "rows": [dict(zip(KEY, k), n=v["n"], fallback=v["fallback"], in_episodes=len(v["episodes"]))
                     for k, v in sorted(rows.items(), key=lambda kv: tuple(map(str, kv[0])))]}


def _key(row):
    return tuple(row[k] for k in KEY)


def table(rows):
    out = ["| skill | leg | arm | allow | holding | relaxed | n | fallback | episodes |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| " + " | ".join(str(r[k]) for k in KEY) +
                   f" | {r['n']} | {r['fallback']} | {r['in_episodes']} |")
    return "\n".join(out)


def compare(now, snap):
    """(rows only in now, rows only in the snapshot, rows in both whose fallback count changed)."""
    a = {_key(r): r for r in now["rows"]}
    b = {_key(r): r for r in snap["rows"]}
    added = [a[k] for k in a if k not in b]
    gone = [b[k] for k in b if k not in a]
    moved = [(b[k], a[k]) for k in a if k in b and a[k]["fallback"] != b[k]["fallback"]]
    return added, gone, moved


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run directories (searched for result.json)")
    ap.add_argument("--save", help="write the signature to this snapshot file")
    ap.add_argument("--compare", help="diff against this snapshot; exit 1 when rows appear or disappear")
    a = ap.parse_args()
    rows, n_ep = signature(a.runs)
    now = to_json(rows, n_ep)
    if not n_ep:
        raise SystemExit("no result.json with contacts.segments under " + ", ".join(a.runs))
    if a.save:
        Path(a.save).write_text(json.dumps(now, indent=1) + "\n")
        print(f"saved {len(now['rows'])} rows from {n_ep} episodes to {a.save}")
    if not a.compare:
        if not a.save:
            print(f"{n_ep} episodes\n\n" + table(now["rows"]))
        return 0
    snap = json.loads(Path(a.compare).read_text())
    added, gone, moved = compare(now, snap)
    print(f"{n_ep} episodes now, {snap['episodes']} in {a.compare}")
    for title, rs in (("new motions (meant, or a bug?)", added), ("motions no longer made", gone)):
        print(f"\n{title}: {len(rs)}")
        if rs:
            print(table(rs))
    if moved:
        print(f"\nfallback counts changed (planning randomness, or a planner gap): {len(moved)}")
        for old, new in moved:
            print(f"  {old['skill']} {old['leg']} {old['allow']}: {old['fallback']} -> {new['fallback']}")
    return 1 if added or gone else 0


if __name__ == "__main__":
    raise SystemExit(main())
