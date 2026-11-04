"""Ratchet on the collision checklist (docs/COLLISION_PLAN.md section 1): the counts of
tools/audit_collision.py per file and kind may only go down from tests/fixtures/collision_audit_baseline.json."""

import warnings

from tools.audit_collision import KINDS, compare, counts, load_baseline, sites


def test_collision_audit_counts_only_go_down():
    now = counts()
    up, down = compare(now, load_baseline())
    if down:
        warnings.warn("collision audit counts went down, lower the baseline with "
                      "`python tools/audit_collision.py --update-baseline`: "
                      + "; ".join(f"{f} {k} {b} -> {n}" for f, k, n, b in down))
    if up:
        rows = sites()
        msg = []
        for f, k, n, b in up:
            msg.append(f"{f} {k}: {b} -> {n}")
            msg += [f"    {f}:{line} {fn} {label}" for f_, line, fn, k_, label in rows if f_ == f and k_ == k]
        raise AssertionError("collision audit counts went up (checklist of docs/COLLISION_PLAN.md section 1): "
                             "remove the new site rather than raising the baseline\n" + "\n".join(msg))


def test_baseline_knows_only_current_kinds():
    assert {k for c in load_baseline().values() for k in c} <= set(KINDS)
