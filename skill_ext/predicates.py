"""The predicates a user skill may name in its preconditions and effects: the built-in GT predicates
(zeno_skills.predicates.REGISTRY, the ones every Contract uses) and the goal-only verifiers
(episode.goal_predicates).  Both import without Isaac Sim."""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def predicate_table() -> dict:
    from episode.goal_predicates import GOAL_PREDICATES
    from zeno_skills.predicates import REGISTRY
    return {**REGISTRY, **GOAL_PREDICATES}


def predicate_names() -> set[str]:
    return set(predicate_table())


def evaluate_atoms(rig, atoms, values, ctx) -> tuple[list[dict], list[str]]:
    """Evaluate parsed atoms ({"pred", "args", "negated"}, ``$param`` references) on live GT state.
    Returns (rows {"atom", "holds", "detail"}, failure texts)."""
    from skill_ext.schema import atom_text
    table = predicate_table()
    rows, failed = [], []
    for a in atoms:
        args = {k: (values.get(v[1:]) if isinstance(v, str) and v.startswith("$") else v)
                for k, v in a["args"].items()}
        bound = dict(a, args=args)
        text = atom_text(bound)
        if any(v is None for v in args.values()):
            rows.append({"atom": text, "holds": False, "detail": "unbound argument"})
            failed.append(f"{text} unbound")
            continue
        pred = table[a["pred"]]
        try:
            ok, detail = pred.evaluate(rig, ctx, **args)
        except Exception as exc:                       # a malformed argument is the skill author's error
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        ok = bool(ok) != bool(a.get("negated"))
        rows.append({"atom": text, "holds": ok, "detail": str(detail)})
        if not ok:
            failed.append(f"{text} is false ({detail})")
    return rows, failed
