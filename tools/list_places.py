"""List what a task spec can refer to: support surfaces (with room, height,
size, headroom), place aliases, object instances and asset types.

    python tools/list_places.py                 # everything, grouped by room
    python tools/list_places.py --room bedroom  # filter by room name
    python tools/list_places.py --min-area 0.1  # skip tiny ledges

No simulator needed (reads annotations/zeno_house.json).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zeno_skills.evaluator import room_of  # noqa: E402
from zeno_skills.tasks import load_places  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ann", default="annotations/zeno_house.json")
    ap.add_argument("--room")
    ap.add_argument("--min-area", type=float, default=0.03)
    args = ap.parse_args()
    ann = json.loads((ROOT / args.ann).read_text())
    places = load_places()
    alias = {v: k for k, v in places.items() if isinstance(v, str)}
    rows = []
    for s in ann["supports"]:
        x0, y0, x1, y1 = s["aabb_xy"]
        area = (x1 - x0) * (y1 - y0)
        if area < args.min_area:
            continue
        room = room_of(ann["rooms"], ((x0 + x1) / 2, (y0 + y1) / 2)) or "?"
        if args.room and args.room not in room:
            continue
        rows.append((room, s["z"], s["name"], alias.get(s["name"], alias.get(s.get("furniture"), "")),
                     f"{x1 - x0:.2f} x {y1 - y0:.2f}", s.get("clearance", 0)))
    rows.sort()
    print(f"{'room':16} {'z':>5}  {'size m':11} {'headroom':>8}  support (alias)")
    for room, z, name, al, size, clr in rows:
        print(f"{room:16} {z:5.2f}  {size:11} {clr:8.2f}  {name}" + (f"  ({al})" if al else ""))
    print("\nfloor areas:")
    for k, v in places.items():
        if isinstance(v, dict):
            print(f"  {k:24} room {v['room']}, xy box {v['xy']}")
    print("\nobject instances in the base scene:")
    for o in ann["objects"]:
        print(f"  {o['name']:30} {o['asset']:16} {o['room'] or '?':16} on {o['support']}")
    assets = json.loads((ROOT / "annotations/assets.json").read_text())
    print("\nasset types (annotations/assets.json):")
    for k, a in assets.items():
        print(f"  {k:16} {'x'.join(f'{v:.2f}' for v in a['size'])} m  {a['mass']} kg  "
              f"grasps {[g['type'] for g in a['grasps']] or 'none'}  tags {a['tags']}")


if __name__ == "__main__":
    main()
