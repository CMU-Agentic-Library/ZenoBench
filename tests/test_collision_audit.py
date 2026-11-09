"""Ratchet on the collision checklist (docs/COLLISION_PLAN.md section 1): the counts of
tools/audit_collision.py per file and kind may only go down from tests/fixtures/collision_audit_baseline.json."""

import warnings
from pathlib import Path

import pytest

from tools.audit_collision import KINDS, compare, counts, load_baseline, sites

# tools/stop_check.py: while .claude/audit_paused exists (committed, so a fresh checkout skips too) the ratchet is
# off -- a switch for refactors that move sites between files; absent since 2026-11-08
PAUSED = Path(__file__).resolve().parents[1] / ".claude" / "audit_paused"


@pytest.mark.skipif(PAUSED.exists(), reason="collision audit paused (.claude/audit_paused)")
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


def _kinds(tmp_path, rel, src):
    from tools.audit_collision import _file_sites
    f = tmp_path / "m.py"
    f.write_text(src)
    return sorted((s[2], s[3]) for s in _file_sites(f, rel))


def test_a_spec_relaxing_the_collision_rules_counts_as_on_a_move_to(tmp_path):
    src = ("a = Spec(allow=LEGACY)\nb = Spec(allow=unchecked('x'))\nc = Spec(exempt=True)\n"
           "d = Spec(fingers=False)\ne = Spec(fingers=True, exempt=False, allow=FREE)\n")
    assert [k for _, k in _kinds(tmp_path, "zeno_skills/skill_plans/x.py", src)] == \
        ["LEGACY", "exempt", "ignore_fingers", "unchecked"]


def test_the_execution_moves_the_robot_and_the_query_layer_writes_the_spec(tmp_path):
    moves = "def f(act, rig):\n    act.follow([])\n    rig.drive_base([])\n    rig.move_to(p, R)\n"
    assert _kinds(tmp_path, "zeno_skills/run.py", moves) == []      # run.py calls only act.* (tests/test_layering.py)
    assert ("f", "old_entry") in _kinds(tmp_path, "zeno_skills/policies/x.py", moves)
    assert _kinds(tmp_path, "zeno_skills/rig.py", moves) == [("f", "drive_base")]
    query = ("class Motion:\n    def query(self, kin):\n        kin.coll_kw = {'ignore_fingers': True}\n"
             "    def other(self, kin):\n        kin.coll_kw = {}\n")
    assert _kinds(tmp_path, "zeno_skills/motion.py", query) == [("Motion.other", "coll_kw")]
