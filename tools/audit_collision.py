"""Inventory of how robot motions are collision-checked (docs/COLLISION_AUDIT.md) and of what is
left of the checklist of docs/COLLISION_PLAN.md section 1 (categories of docs/COLLISION_CLEANUP.md).

    python tools/audit_collision.py                    # summary per file
    python tools/audit_collision.py --sites            # every site: file:line, function, kind, label
    python tools/audit_collision.py --sites --kind offset
    python tools/audit_collision.py --update-baseline  # write tests/fixtures/collision_audit_baseline.json

Kinds, per file under zeno_skills/ (static, by AST; a count is a site to look at, not a verdict):

  LEGACY, unchecked  a motion passed ``allow=LEGACY`` / another ``unchecked(...)`` (checklist 3)
  coll_kw            a direct ``coll_kw`` write (X)
  drive_base         a ``drive_base`` call (B)
  follow             a raw ``follow`` / ``left_follow`` call
  exempt             target exemption: a ``_targets_allow`` call, ``exempt_targets`` set to
                     anything but False (checklist 3; ``exempt_targets: False`` turns it off)
  ignore_fingers     ``ignore_fingers`` passed: a dict key, keyword or item set to anything but
                     False, and every use of a module-level dict that sets it (checklist 3)
  offset             a motion whose target (its own arguments, or the local assignments of the
                     names in them) computes with a numeric literal: the strong W signal (checklist 1)
  except             an ``except`` handler (F when it lets a skill carry on)
  swallow            one that catches everything / ``Exception`` / ``SkillFailure`` and does not
                     raise (``except: pass``, a retry) (F, checklist 4)
  retry              a ``for`` loop over alternatives that runs a motion and leaves it early
                     (break / continue / return) (F, checklist 4)
  old_entry          a direct call of an old motion entry of the rig (OLD_ENTRIES: move_to, joint_path,
                     leave, tuck, swing, follow, drive_base, grip ...): what a skill not yet on the motion layers
                     moves the robot with (docs/MOTION_ARCHITECTURE.md 9.3, "only goes down"; 0 at step 10)

The motion layers (docs/MOTION_ARCHITECTURE.md 2.5):
  - a segment's collision rules are a ``Spec``: ``Spec(allow=LEGACY / unchecked(...))`` counts as
    LEGACY / unchecked, ``Spec(exempt=...)`` (not False) as exempt, ``Spec(fingers=False)`` as
    ignore_fingers -- the same relaxations as on a move_to;
  - EXECUTION (run.py, through the Actuator; rig.py, the Actuator's implementation) is where the robot
    is moved: its follow / drive_base / old entries are not sites;
  - QUERY_LAYER (Motion.query, Motion.path_free_only) translates a Spec into the collision query: its
    coll_kw / exemption / finger settings are the Spec's, counted where the Spec is written;
  - the park search's loop over candidate parks builds plans (``build``), it moves nothing: no retry.

tests/test_collision_audit.py ratchets these counts against the baseline: they may only go down.
``bool_switches()`` finds the boolean ``collision=`` / ``check=`` keywords that ``allow=`` replaced
(tests/test_clearance.py keeps them out).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTIONS = ("move_to", "move_left_to", "joint_path")
SCAN = ("zeno_skills", "tools", "benchmark", "env_service", "episode")
BASELINE = ROOT / "tests" / "fixtures" / "collision_audit_baseline.json"
KINDS = ("LEGACY", "unchecked", "coll_kw", "drive_base", "follow", "exempt", "ignore_fingers", "offset",
         "except", "swallow", "retry", "old_entry")

# the arguments of a motion that are its target, and the motions they belong to
TARGET_ARGS = {"p", "R", "q_goal", "goals"}
TARGET_MOTIONS = MOTIONS + ("move_to_any",)
# calls that move the robot: a loop running one of them and leaving early tries alternatives
MOVES = TARGET_MOTIONS + ("_approach", "leave", "drive_base", "follow", "follow_smooth", "left_follow",
                          "relocate", "navigate", "swing")
# literals that are not offsets: unit vectors, signs, halves, doubling; below EPS a guard (norm + 1e-9)
TRIVIAL = {0, 1, 2, 0.5}
EPS = 1e-4
# exceptions that cover a skill failing
BROAD = {"Exception", "BaseException", "SkillFailure"}
# the rig's motion entries a skill not yet on the motion layers calls (old_entry)
OLD_ENTRIES = ("move_to", "move_to_any", "joint_path", "joint_path_via", "move_left_to", "leave", "tuck", "swing",
               "follow", "follow_smooth", "left_follow", "follow_both", "drive_base",
               "grip")   # the gripper too: on the motion layers it is an action segment (a hook that opens the
                         # hand -- check_held on a drop, a pinch judged empty -- is a side effect still to move)
# where the robot is moved: the execution of the motion layers (only through the Actuator) and the Actuator's
# implementation (with the old entries themselves)
EXECUTION = {"zeno_skills/run.py", "zeno_skills/rig.py"}
# (file, function) translating a segment's Spec into the collision query (docs/MOTION_ARCHITECTURE.md 4.4)
QUERY_LAYER = {("zeno_skills/motion.py", "Motion.query"), ("zeno_skills/motion.py", "Motion.path_free_only")}
QUERY_KINDS = {"coll_kw", "exempt", "ignore_fingers"}


def _files(dirs=SCAN):
    for d in dirs:
        for f in sorted((ROOT / d).rglob("*.py")):
            if "__pycache__" not in f.parts:
                yield f


def _parents(tree):
    return {ch: n for n in ast.walk(tree) for ch in ast.iter_child_nodes(n)}


def _scopes(tree, parents=None):
    parents = parents or _parents(tree)

    def scope(n):
        names = []
        while n in parents:
            n = parents[n]
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(n.name)
        return ".".join(reversed(names))
    return scope


def _label(call):
    kw = {k.arg: k.value for k in call.keywords if k.arg}
    return ast.unparse(kw["label"]) if "label" in kw else ""


def _short(src, n=60):
    src = " ".join(src.split())
    return src if len(src) <= n else src[:n - 3] + "..."


def _is_false(v):
    return isinstance(v, ast.Constant) and v.value is False


def _callee(call):
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def _function(n, parents):
    while n in parents:
        n = parents[n]
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return n
    return None


def _walk_own(node):
    """ast.walk without descending into nested functions, lambdas or classes."""
    todo = list(ast.iter_child_nodes(node))
    while todo:
        n = todo.pop()
        yield n
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            todo.extend(ast.iter_child_nodes(n))


def _literals(expr):
    """Numeric literals that take part in computing ``expr`` (not indices, not trivial ones)."""
    skip = set()
    for n in ast.walk(expr):
        if isinstance(n, ast.Subscript):
            skip.update(ast.walk(n.slice))
        elif isinstance(n, ast.keyword) and n.arg in ("axis", "dtype", "decimals", "ord"):
            skip.update(ast.walk(n.value))
    return [n for n in ast.walk(expr)
            if n not in skip and isinstance(n, ast.Constant) and type(n.value) in (int, float)
            and abs(n.value) not in TRIVIAL and abs(n.value) >= EPS]


def _assigned(fn, name):
    """Values assigned to the local ``name`` in function ``fn`` (plain, augmented, annotated)."""
    out = []
    for n in _walk_own(fn):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if any(isinstance(e, ast.Name) and e.id == name for e in ast.walk(t)):
                    out.append(n.value)
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)) and isinstance(n.target, ast.Name) \
                and n.target.id == name and n.value is not None:
            out.append(n.value)
    return out


def _target_literals(call, fn, depth=2):
    """Numeric literals in a motion's target: its target arguments, then (``depth`` levels) the local
    assignments of the names they use."""
    exprs = list(call.args) + [k.value for k in call.keywords if k.arg in TARGET_ARGS]
    found, seen = [], set()
    for _ in range(depth + 1):
        nxt = []
        for e in exprs:
            found += _literals(e)
            if fn is None:
                continue
            for nm in {x.id for x in ast.walk(e) if isinstance(x, ast.Name)} - seen:
                seen.add(nm)
                nxt += _assigned(fn, nm)
        exprs = nxt
    return found


def _ignore_fingers_dicts(tree):
    """Module-level names bound to a dict that sets ignore_fingers (APPROACH_KW)."""
    out = set()
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict) and any(
                isinstance(k, ast.Constant) and k.value == "ignore_fingers" and not _is_false(v)
                for k, v in zip(n.value.keys, n.value.values)):
            out |= {t.id for t in n.targets if isinstance(t, ast.Name)}
    return out


def _sets_key(n, key):
    """[value] that node ``n`` sets ``key`` to: a dict entry, a keyword or a subscript store."""
    if isinstance(n, ast.Dict):
        return [v for k, v in zip(n.keys, n.values) if isinstance(k, ast.Constant) and k.value == key]
    if isinstance(n, ast.keyword) and n.arg == key:
        return [n.value]
    if isinstance(n, ast.Assign):
        return [n.value for t in n.targets if isinstance(t, ast.Subscript)
                and isinstance(t.slice, ast.Constant) and t.slice.value == key]
    return []


def _handler_types(h):
    if h.type is None:
        return ["(bare)"]
    ts = h.type.elts if isinstance(h.type, ast.Tuple) else [h.type]
    return [t.attr if isinstance(t, ast.Attribute) else ast.unparse(t) for t in ts]


def _leaves_early(loop):
    """break / continue of ``loop`` itself, or a return from inside it."""
    todo = list(loop.body)
    while todo:
        n = todo.pop()
        if isinstance(n, (ast.Break, ast.Continue, ast.Return)):
            return True
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(n, (ast.For, ast.AsyncFor, ast.While)):
            todo += [x for x in ast.walk(n) if isinstance(x, ast.Return)]   # nested loops: return only
            continue
        todo.extend(ast.iter_child_nodes(n))
    return False


def _file_sites(f, rel):
    tree = ast.parse(f.read_text())
    parents = _parents(tree)
    scope = _scopes(tree, parents)
    fingers = _ignore_fingers_dicts(tree)
    out = []

    def add(n, kind, label=""):
        where = scope(n)
        if kind in QUERY_KINDS and (rel, where) in QUERY_LAYER:
            return
        out.append((rel, n.lineno, where, kind, label))

    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name = _callee(n)
            if isinstance(n.func, ast.Attribute):
                if name in MOTIONS:
                    for k in n.keywords:
                        if k.arg != "allow":
                            continue
                        src = ast.unparse(k.value)
                        if "LEGACY" in src:
                            add(n, "LEGACY", _label(n))
                        elif "unchecked(" in src:
                            add(n, "unchecked", _label(n))
                elif name == "drive_base" and rel != "zeno_skills/run.py":
                    add(n, "drive_base")
                elif name in ("follow", "follow_smooth", "left_follow") and rel not in EXECUTION:
                    add(n, "follow")
                if name in OLD_ENTRIES and rel not in EXECUTION and rel.startswith("zeno_skills/"):
                    add(n, "old_entry", name)
            if name == "Spec":
                kw = {k.arg: k.value for k in n.keywords if k.arg}
                if "allow" in kw:
                    src = ast.unparse(kw["allow"])
                    if "LEGACY" in src:
                        add(n, "LEGACY", "Spec")
                    elif "unchecked(" in src:
                        add(n, "unchecked", "Spec")
                if "exempt" in kw and not _is_false(kw["exempt"]):
                    add(n, "exempt", "Spec(exempt=" + _short(ast.unparse(kw["exempt"]), 30) + ")")
                if "fingers" in kw and _is_false(kw["fingers"]):
                    add(n, "ignore_fingers", "Spec(fingers=False)")
            if name == "_targets_allow":
                add(n, "exempt", "_targets_allow")
            if name in TARGET_MOTIONS and isinstance(n.func, ast.Attribute):
                lits = _target_literals(n, _function(n, parents))
                if lits:
                    vals = sorted({ast.unparse(x) for x in lits})
                    add(n, "offset", f"{name} {_label(n)} {','.join(vals)}".replace("  ", " "))
        elif isinstance(n, ast.Assign) and any(ast.unparse(t).endswith(".coll_kw") for t in n.targets):
            if f.name not in ("clearance.py", "kinematics.py"):
                add(n, "coll_kw", ast.unparse(n.value))
        elif isinstance(n, ast.ExceptHandler):
            types = _handler_types(n)
            body = "pass" if all(isinstance(s, ast.Pass) for s in n.body) else ""
            label = f"except {','.join(types)} {body}".strip()
            add(n, "except", label)
            if ({"(bare)"} | BROAD) & set(types) and not any(isinstance(x, ast.Raise) for x in _walk_own(n)):
                add(n, "swallow", label)
        elif isinstance(n, (ast.For, ast.AsyncFor)):
            moves = sorted({_callee(c) for c in _walk_own(n) if isinstance(c, ast.Call) and _callee(c) in MOVES})
            if moves and _leaves_early(n):
                add(n, "retry", f"for {_short(ast.unparse(n.target), 20)} in {_short(ast.unparse(n.iter), 40)}: "
                               + ",".join(moves))
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in fingers:
            add(n, "ignore_fingers", n.id)
        for v in _sets_key(n, "ignore_fingers"):
            if not _is_false(v):
                add(n, "ignore_fingers", _short(ast.unparse(v), 40))
        for v in _sets_key(n, "exempt_targets"):
            if not _is_false(v):
                add(n, "exempt", "exempt_targets=" + _short(ast.unparse(v), 40))
    return out


def sites(dirs=("zeno_skills",), kinds=KINDS):
    """[(file, line, function, kind, label)] for ``kinds`` (KINDS; module docstring), by file and line."""
    out = []
    for f in _files(dirs):
        out += [s for s in _file_sites(f, str(f.relative_to(ROOT))) if s[3] in kinds]
    return sorted(out, key=lambda s: (s[0], s[1], KINDS.index(s[3])))


def counts(rows=None):
    """{file: {kind: n}} of the non-zero counts."""
    per = {}
    for f, _, _, kind, _ in sites() if rows is None else rows:
        per.setdefault(f, Counter())[kind] += 1
    return {f: {k: c[k] for k in KINDS if c[k]} for f, c in sorted(per.items())}


def load_baseline(path=BASELINE):
    return json.loads(Path(path).read_text())["counts"]


def compare(now, base):
    """([(file, kind, now, base)] gone up, [...] gone down)."""
    up, down = [], []
    for f in sorted(set(now) | set(base)):
        for k in KINDS:
            n, b = now.get(f, {}).get(k, 0), base.get(f, {}).get(k, 0)
            if n > b:
                up.append((f, k, n, b))
            elif n < b:
                down.append((f, k, n, b))
    return up, down


def write_baseline(now, path=BASELINE):
    doc = ("Counts of tools/audit_collision.py per file and kind; tests/test_collision_audit.py fails "
           "when one goes up. Lower it with: python tools/audit_collision.py --update-baseline")
    rows = ",\n".join(f"  {json.dumps(f)}: {json.dumps(c)}" for f, c in now.items())   # one line per file
    Path(path).write_text(f'{{\n "_doc": {json.dumps(doc)},\n "counts": {{\n{rows}\n }}\n}}\n')


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
    ap.add_argument("--kind", action="append", choices=KINDS, help="only these kinds (repeatable)")
    ap.add_argument("--update-baseline", action="store_true",
                    help=f"write the current counts to {BASELINE.relative_to(ROOT)} (refused if one went up)")
    ap.add_argument("--allow-increase", action="store_true", help="with --update-baseline: accept counts that went up")
    a = ap.parse_args()
    kinds = tuple(a.kind or KINDS)
    if a.update_baseline:
        now = counts()
        up, down = compare(now, load_baseline()) if BASELINE.exists() else ([], [])
        if up and not a.allow_increase:
            for f, k, n, b in up:
                print(f"  {f} {k}: {b} -> {n}")
            sys.exit("counts went up (above); fix them, or pass --allow-increase if that is intended")
        write_baseline(now)
        for f, k, n, b in up + down:
            print(f"  {f} {k}: {b} -> {n}")
        print(f"wrote {BASELINE.relative_to(ROOT)}")
        return
    rows = sites(kinds=kinds)
    if a.sites:
        for f, line, fn, kind, label in rows:
            print(f"{f}:{line}\t{fn}\t{kind}\t{label}")
        return
    per = counts(rows)
    print("| file | " + " | ".join(kinds) + " |")
    print("|---|" + "---|" * len(kinds))
    for f, c in per.items():
        print(f"| {f} | " + " | ".join(str(c.get(k, 0)) for k in kinds) + " |")
    tot = Counter(k for *_, k, _ in rows)
    print("| total | " + " | ".join(str(tot[k]) for k in kinds) + " |")
    left = bool_switches()
    if left:
        print("\nboolean collision= / check= still passed to a motion:")
        for f, line, k in left:
            print(f"  {f}:{line} {k}=")


if __name__ == "__main__":
    main()
