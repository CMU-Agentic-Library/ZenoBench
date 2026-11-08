"""What of zeno_skills/ a set of episodes ran (docs/COLLISION_PLAN.md section 5): a skill path no
episode ran is not checked by a regression that passed, whatever its result.

    ZB_COVERAGE=1 $ISAACLAB_PYTHON benchmark/run_episode.py --batch B --out RUN ...   # collect
    $ISAACLAB_PYTHON tools/skill_coverage.py RUN                    # per file: lines, functions never entered
    $ISAACLAB_PYTHON tools/skill_coverage.py RUN --file zeno_skills/skills.py   # that file's unrun functions
    $ISAACLAB_PYTHON tools/skill_coverage.py RUN --html RUN/coverage/html       # line by line

RUN/coverage/.coverage.* (one per episode process, benchmark/run_episode.py start_coverage) are
combined into RUN/coverage/.coverage.  A function counts as entered when any line of its body ran.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(run):
    import coverage
    d = Path(run) / "coverage"
    parts = list(d.glob(".coverage.*"))
    cov = coverage.Coverage(data_file=str(d / ".coverage"))
    if parts:
        cov.combine([str(p) for p in parts], keep=True)
        cov.save()
    cov.load()
    return cov


def functions(path):
    """(qualified name, first line, set of body lines) of every function in ``path``."""
    tree = ast.parse(Path(path).read_text())
    out = []

    def walk(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + ch.name
                body = ch.body[1:] if (ch.body and isinstance(ch.body[0], ast.Expr)
                                       and isinstance(getattr(ch.body[0], "value", None), ast.Constant)) else ch.body
                lines = {n.lineno for b in body for n in ast.walk(b) if hasattr(n, "lineno")}
                out.append((name, ch.lineno, lines))
                walk(ch, name + ".")
            elif isinstance(ch, ast.ClassDef):
                walk(ch, prefix + ch.name + ".")
    walk(tree, "")
    return out


def report(cov, only=None):
    rows = []
    data = cov.get_data()
    for f in sorted(data.measured_files()):
        rel = Path(f).resolve().relative_to(ROOT) if Path(f).resolve().is_relative_to(ROOT) else Path(f)
        if only and str(rel) != only:
            continue
        _, stmts, _, missing, _ = cov.analysis2(f)
        ran = set(stmts) - set(missing)
        unrun = [(n, l) for n, l, body in functions(f) if body and not (body & ran)]
        rows.append((str(rel), len(stmts), len(ran), unrun))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--file", help="list the functions of this file (repo-relative) no episode entered")
    ap.add_argument("--html", help="write coverage's line-by-line HTML report here")
    a = ap.parse_args()
    cov = load(a.run)
    if a.html:
        cov.html_report(directory=a.html)
        print("html:", a.html)
    rows = report(cov, a.file)
    if a.file:
        for f, n, r, unrun in rows:
            print(f"{f}: {r}/{n} lines ran; {len(unrun)} functions never entered")
            for name, line in unrun:
                print(f"  {f}:{line} {name}")
        return 0
    print("| file | lines ran | functions never entered |\n|---|---|---|")
    for f, n, r, unrun in rows:
        print(f"| {f} | {r}/{n} ({100 * r // max(n, 1)}%) | {len(unrun)} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
