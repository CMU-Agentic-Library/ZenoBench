"""Which levels a table layout can offer a book (11-17, T01): a static sweep over book poses on the table.

The levels match T01's tiers:

- ideal: on the seats' side (``near_edge`` east, EDGE_M), beside a seat (within NEAR_M of a plate or bowl) and
  CLEAR_M clear of everything on the table;
- moderate: CLEAR_M clear of everything, not ideal (the far end, the west half, across from a plate);
- bad: fits without touching anything, but closer than CLEAR_M to something (squeezed against the dishes).

A seed's top level is fixed by the layout, so the tiers it cannot offer are left out of its scoring
(scoring.per_layout); tests/test_t01_slots.py checks every T01 layout against what its design says.
"""
from __future__ import annotations

import math

from benchmark.v6.layout import _assets

BOOK = "paperback_book"
NEAR_M, CLEAR_M, EDGE_M = 0.15, 0.05, 0.20
OVERHANG_M = 0.03        # a book may stick out this far over the table edge and still count as on it


def box(asset: str, xy, yaw_deg: float = 0.0):
    a = _assets()[asset]
    sx, sy = a["size"][0] / 2, a["size"][1] / 2
    c, s = abs(math.cos(math.radians(yaw_deg))), abs(math.sin(math.radians(yaw_deg)))
    hx, hy = sx * c + sy * s, sx * s + sy * c
    return (xy[0] - hx, xy[1] - hy, xy[0] + hx, xy[1] + hy)


def gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def levels(table, things: dict, plates, step: float = 0.01) -> dict:
    """{level: an (x, y, yaw) that earns it} for a book on ``table`` (x0, y0, x1, y1).  ``things``: name ->
    (asset, xy, yaw_deg) of everything on the table; ``plates``: the names that make a seat."""
    boxes = {n: box(a, xy, yaw) for n, (a, xy, yaw) in things.items()}
    x0, y0, x1, y1 = table
    out = {}
    for yaw in (0.0, 90.0):
        bx = box(BOOK, (0.0, 0.0), yaw)
        hx, hy = bx[2], bx[3]
        nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
        for i in range(nx):
            for j in range(ny):
                x, y = x0 + i * step, y0 + j * step
                fp = (x - hx, y - hy, x + hx, y + hy)
                if fp[0] < x0 - OVERHANG_M or fp[2] > x1 + OVERHANG_M or fp[1] < y0 - OVERHANG_M or \
                        fp[3] > y1 + OVERHANG_M:
                    continue
                gaps = {n: gap(fp, b) for n, b in boxes.items()}
                if any(overlap(fp, b) for b in boxes.values()):
                    continue
                clear = min(gaps.values(), default=math.inf) >= CLEAR_M
                ideal = clear and x1 - fp[2] <= EDGE_M and min((gaps[p] for p in plates if p in gaps),
                                                                 default=math.inf) <= NEAR_M
                lv = "ideal" if ideal else "moderate" if clear else "bad"
                out.setdefault(lv, (round(x, 3), round(y, 3), yaw))
    return out
