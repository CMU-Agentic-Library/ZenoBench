"""One object vocabulary for the whole benchmark (11-26), from the object registry
(benchmark/v6/registry/objects.yaml): every movable asset kind of v6 with its category and subcategory.

It is the same list in every episode, so it says nothing about which objects a scene has or lacks.  The
baseline prompt shows it (``vocabulary_text``); Episode resolves a search for a kind word against it
(``kinds_for``), so "rolling pin", "spoons", "Bin" find a rolling_pin, a breakfast_spoon, a storage bin.
"""
from __future__ import annotations

from functools import lru_cache


@lru_cache(None)
def registry() -> dict:
    """{asset kind: {"category", "subcategory"}}."""
    from benchmark.v6.object_registry import objects_yaml
    return dict(objects_yaml()["objects"])


def normalize(word: str) -> str:
    return "_".join(str(word).strip().lower().replace("-", " ").replace("_", " ").split())


def _forms(w: str) -> list[str]:
    out = [w]
    if w.endswith("ies"):
        out.append(w[:-3] + "y")
    if w.endswith("es"):
        out.append(w[:-2])
    if w.endswith("s"):
        out.append(w[:-1])
    return out


def kinds_for(word: str, kinds=None) -> list[str]:
    """The asset kinds a kind word names, best level first: the kind itself (breakfast_spoon), a kind it is
    the head or tail of ("spoon" -> breakfast_spoon, "tomato" -> cherry_tomato, big_tomato), a subcategory
    ("bin", "basket", "cutlery"), a category ("tableware").  Spaces, case, hyphens and plurals are loose.
    ``kinds``: the kinds to choose from (default: the registry's)."""
    reg = registry()
    kinds = sorted(kinds if kinds is not None else reg)
    for w in _forms(normalize(word)):
        if not w:
            continue
        for level in (lambda k: k == w,
                      lambda k: k.endswith("_" + w) or k.startswith(w + "_"),
                      lambda k: reg.get(k, {}).get("subcategory") == w,
                      lambda k: reg.get(k, {}).get("category") == w):
            hit = [k for k in kinds if level(k)]
            if hit:
                return hit
    return []


def vocabulary_text() -> str:
    """The vocabulary for a prompt: kinds by category, as one line each."""
    by: dict[str, list[str]] = {}
    for k, rec in sorted(registry().items()):
        by.setdefault(rec.get("category", "other"), []).append(k)
    return "\n".join(f"- {c}: {', '.join(ks)}" for c, ks in sorted(by.items()))
