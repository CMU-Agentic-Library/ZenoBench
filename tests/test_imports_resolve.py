"""Every `from <repo module> import name` in the repo -- at module level or inside a function -- names something
the module defines.  The imports inside functions run only in the simulator: when ee9b82f moved drive_head
from policies/perceive.py to skill_jobs/look.py, benchmark/observation.py's glance still imported it from
perceive, and every sticky/benchmark episode died at its first gated navigate with an ImportError (11-16)."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("zeno_skills", "benchmark", "episode")
SKIP = {"__pycache__", ".git", "runs", ".claude", "docker"}


def _module_file(mod):
    p = ROOT.joinpath(*mod.split("."))
    for c in (p.with_suffix(".py"), p / "__init__.py"):
        if c.is_file():
            return c
    return None


def _defined(path, cache={}):
    """(top-level names of the module, whether anything else can supply names: * import, __getattr__)."""
    if path not in cache:
        names, open_ = set(), False
        for node in ast.parse(path.read_text()).body:
            for n in ([node] + list(ast.walk(node)) if isinstance(node, (ast.If, ast.Try)) else [node]):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(n.name)
                    open_ |= n.name == "__getattr__"
                elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                        names.update(x.id for x in ast.walk(t) if isinstance(x, ast.Name))
                elif isinstance(n, (ast.Import, ast.ImportFrom)):
                    for a in n.names:
                        open_ |= a.name == "*"
                        names.add((a.asname or a.name).split(".")[0])
        cache[path] = (names, open_)
    return cache[path]


def _imports():
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if SKIP & set(rel.parts):
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        pkg = list(rel.parts[:-1])
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level:
                mod = ".".join(pkg[:len(pkg) - node.level + 1] + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            if mod.split(".")[0] in PACKAGES:
                yield rel, node.lineno, mod, [a.name for a in node.names]


def test_every_import_from_the_repo_resolves():
    stale = []
    for rel, line, mod, names in _imports():
        target = _module_file(mod)
        if target is None:
            continue
        defined, open_ = _defined(target)
        if open_:
            continue
        stale += [f"{rel}:{line}: from {mod} import {n}" for n in names
                  if n != "*" and n not in defined and _module_file(f"{mod}.{n}") is None]
    assert not stale, "names the module does not define:\n" + "\n".join(stale)
