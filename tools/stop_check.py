"""Claude Code Stop hook (.claude/settings.json): before Claude ends a turn, the checks of
docs/COLLISION_PLAN.md section 5 that take seconds, so "done" is not Claude's word alone.

    python3 tools/stop_check.py            # what the hook runs (reads the hook JSON on stdin)

Skipped when nothing under zeno_skills/, tools/, tests/ changed since the last pass (the
fingerprint of ``git diff HEAD`` and the untracked files there, kept in .claude/stop_check_ok):
a turn of talk costs nothing.  Otherwise: every changed .py file compiles, and the collision
audit (tools/audit_collision.py) is at or under its baseline.  A failure exits 2 with what
failed on stderr, which Claude Code hands back to Claude instead of ending the turn; a second
stop in the same turn (``stop_hook_active``) is let through, so a failure Claude cannot fix
ends with the failure reported, not a loop.

Plain python3, no simulator: the unit tests (minutes, in the container) stay a step of their own.
"""

from __future__ import annotations

import hashlib
import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCH = ("zeno_skills", "tools", "tests")
STAMP = ROOT / ".claude" / "stop_check_ok"


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def changed_files():
    """The .py files under WATCH that differ from HEAD or are untracked."""
    names = _git("diff", "--name-only", "HEAD", "--", *WATCH).split()
    names += _git("ls-files", "--others", "--exclude-standard", "--", *WATCH).split()
    return sorted({n for n in names if n.endswith(".py") and (ROOT / n).exists()})


def fingerprint():
    h = hashlib.sha256(_git("rev-parse", "HEAD").encode())
    h.update(_git("diff", "HEAD", "--", *WATCH).encode())
    for n in _git("ls-files", "--others", "--exclude-standard", "--", *WATCH).split():
        p = ROOT / n
        if p.is_file():
            h.update(n.encode() + p.read_bytes())
    return h.hexdigest()


def problems():
    out = []
    for n in changed_files():
        try:
            py_compile.compile(str(ROOT / n), doraise=True)
        except py_compile.PyCompileError as exc:
            out.append(f"{n} does not compile: {exc.msg.strip()}")
    sys.path.insert(0, str(ROOT))
    from tools.audit_collision import compare, counts, load_baseline, sites
    up, _ = compare(counts(), load_baseline())
    if up:
        rows = sites()
        out.append("collision audit counts went up (docs/COLLISION_PLAN.md section 1; remove the new site, "
                   "do not raise the baseline):")
        for f, k, n, b in up:
            out.append(f"  {f} {k}: {b} -> {n}")
            out += [f"    {f}:{line} {fn} {label}" for f_, line, fn, k_, label in rows if f_ == f and k_ == k]
    return out


def main():
    try:
        hook = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        hook = {}
    fp = fingerprint()
    if STAMP.exists() and STAMP.read_text().strip() == fp:
        return 0
    bad = problems()
    if not bad:
        STAMP.write_text(fp + "\n")
        return 0
    if hook.get("stop_hook_active"):
        print("stop_check still failing; ending the turn with it unfixed:\n" + "\n".join(bad), file=sys.stderr)
        return 0
    print("Before ending the turn (tools/stop_check.py):\n" + "\n".join(bad), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
