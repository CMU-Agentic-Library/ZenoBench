"""Inventory of how robot motions are collision-checked (docs/COLLISION_AUDIT.md).

    python tools/audit_collision.py            # summary per file
    python tools/audit_collision.py --sites    # every unchecked motion: file:line, function, label

Counts, per file under zeno_skills/: motions passed ``allow=LEGACY`` (unchecked, not migrated),
other ``unchecked(...)`` allows, direct ``coll_kw`` writes, ``drive_base`` calls and raw
``follow`` / ``left_follow`` calls.  ``bool_switches()`` finds the boolean ``collision=`` /
``check=`` keywords that ``allow=`` replaced (tests/test_clearance.py keeps them out).
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTIONS = ("move_to", "move_left_to", "joint_path")
SCAN = ("zeno_skills", "tools", "benchmark", "env_service", "episode")


def _files(dirs=SCAN):
    for d in dirs:
        for f in sorted((ROOT / d).rglob("*.py")):
            if "__pycache__" not in f.parts:
                yield f


def _scopes(tree):
    parents = {ch: n for n in ast.walk(tree) for ch in ast.iter_child_nodes(n)}

    def scope(n):
        names = []
        while n in parents:
            n = parents[n]
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                names.append(n.name)
        return ".".join(reversed(names))
    return scope


def _label(call):
    kw = {k.arg: k.value for k in call.keywords if k.arg}
    return ast.unparse(kw["label"]) if "label" in kw else ""


def sites(dirs=("zeno_skills",)):
    """[(file, line, function, kind, label)]: kind LEGACY | unchecked | coll_kw | drive_base | follow."""
    out = []
    for f in _files(dirs):
        tree = ast.parse(f.read_text())
        scope = _scopes(tree)
        rel = str(f.relative_to(ROOT))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                name = n.func.attr
                if name in MOTIONS:
                    for k in n.keywords:
                        if k.arg != "allow":
                            continue
                        src = ast.unparse(k.value)
                        if "LEGACY" in src:
                            out.append((rel, n.lineno, scope(n), "LEGACY", _label(n)))
                        elif "unchecked(" in src:
                            out.append((rel, n.lineno, scope(n), "unchecked", _label(n)))
                elif name == "drive_base":
                    out.append((rel, n.lineno, scope(n), "drive_base", ""))
                elif name in ("follow", "follow_smooth", "left_follow") and f.name != "rig.py":
                    out.append((rel, n.lineno, scope(n), "follow", ""))
            elif isinstance(n, ast.Assign) and any(ast.unparse(t).endswith(".coll_kw") for t in n.targets):
                if f.name not in ("clearance.py", "kinematics.py"):
                    out.append((rel, n.lineno, scope(n), "coll_kw", ast.unparse(n.value)))
    return out


def bool_switches(dirs=SCAN):
    """[(file, line, keyword)] of ``collision=`` / ``check=`` passed to a motion (use ``allow=``)."""
    out = []
    for f in _files(dirs):
        for n in ast.walk(ast.parse(f.read_text())):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in MOTIONS:
                out += [(str(f.relative_to(ROOT)), n.lineno, k.arg) for k in n.keywords
                        if k.arg in ("collision", "check")]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sites", action="store_true", help="list every site instead of the per-file summary")
    a = ap.parse_args()
    rows = sites()
    if a.sites:
        for r in rows:
            print("\t".join(map(str, r)))
        return
    kinds = ("LEGACY", "unchecked", "coll_kw", "drive_base", "follow")
    per = {}
    for f, _, _, kind, _ in rows:
        per.setdefault(f, Counter())[kind] += 1
    print("| file | " + " | ".join(kinds) + " |")
    print("|---|" + "---|" * len(kinds))
    for f, c in sorted(per.items()):
        print(f"| {f} | " + " | ".join(str(c[k]) for k in kinds) + " |")
    tot = Counter(k for *_, k, _ in rows)
    print("| total | " + " | ".join(str(tot[k]) for k in kinds) + " |")
    left = bool_switches()
    if left:
        print("\nboolean collision= / check= still passed to a motion:")
        for f, line, k in left:
            print(f"  {f}:{line} {k}=")


if __name__ == "__main__":
    main()
