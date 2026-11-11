"""Graded outcomes of the v6 designs (11-11): one task, several ways to finish it, different scores.

Each reviewed design (``v6_variants`` key) gets a ``scoring`` entry, copied onto every layout of the design
(``variants[lid]["scoring"]``) so an episode carries it like its goal (episode.catalog.VARIANT_OVERRIDES):

- ``D``: 1 when the task forks (more than one acceptable way to finish it, scored differently), else 0.
- ``tiers``: best first; each ``{"name", "score", "goal", "why"}``.  ``goal`` is a goal in the usual form
  (``{"all": [...], "any": [...]}``), or None for the layout's own goal.  The episode scores the first tier
  whose goal holds on the final state; none holds -> ``not_ok`` (score 0).
  A ``goal`` may also be ``{"by_layout": {lid: goal}}`` when the right spot depends on the layout.
- ``not_ok``: what does not count at all (documentation; scored 0 because no tier holds).

D = 0 means there is no substitution: the single tier is the layout's goal.

Decisions are reviewed one design at a time with the user; benchmark/v6/SCORING_zh.md records them.
"""
from __future__ import annotations

TIER_NAMES = ("best", "second", "worst")


def only(why: str, not_ok: str) -> dict:
    """D = 0: one acceptable outcome, the layout's goal."""
    return {"D": 0, "tiers": [{"name": "best", "score": 1.0, "goal": None, "why": why}], "not_ok": not_ok}


SCORING: dict[tuple[str, str], dict] = {
    # T01 overhang_ready (control): the book overhangs the island, a pick takes it as it is; both dining
    # tables are dining tables (the nearer one only saves a walk, which SPL-c already measures)
    ("T01", "overhang_ready"): only(
        "the book on either dining table, the hand empty",
        "the book anywhere else (coffee table, island, counter, floor) or still held"),
}


def scoring_for(task_id: str, design: str) -> dict | None:
    return next((s for (tid, d), s in SCORING.items() if task_id.startswith(tid) and d == design), None)


def attach_scoring(out: dict) -> int:
    """Copy each reviewed design's scoring onto its layouts; returns how many designs are reviewed."""
    import copy
    n = 0
    for t in out["tasks"]:
        for design, info in t["v6_variants"].items():
            s = scoring_for(t["task_id"], design)
            if s is None:
                continue
            n += 1
            info["scoring"] = copy.deepcopy(s)
            for lid in info["layouts"]:
                t["variants"][lid]["scoring"] = copy.deepcopy(s)
    return n


def tier_goal(tier: dict, task: dict, layout: str | None):
    g = tier.get("goal")
    if g is None:
        return task["goal"]
    if "by_layout" in g:
        return g["by_layout"][layout]
    return g


def score(scoring: dict | None, task: dict, layout: str | None, holds) -> dict | None:
    """The first tier whose goal holds (``holds(goal) -> bool``), as {tier, score, D}; None if not reviewed."""
    if not scoring:
        return None
    for tier in scoring["tiers"]:
        if holds(tier_goal(tier, task, layout)):
            return {"tier": tier["name"], "score": tier["score"], "D": scoring["D"]}
    return {"tier": "not_ok", "score": 0.0, "D": scoring["D"]}


def check_spec(s: dict) -> list[str]:
    """Problems with one scoring entry (tests/test_scoring.py)."""
    bad = []
    tiers = s.get("tiers") or []
    if s.get("D") not in (0, 1):
        bad.append("D must be 0 or 1")
    if not tiers:
        bad.append("no tiers")
    if s.get("D") == 0 and len(tiers) != 1:
        bad.append("D = 0 has exactly one tier")
    if s.get("D") == 1 and len(tiers) < 2:
        bad.append("D = 1 needs at least two tiers")
    scores = [t.get("score") for t in tiers]
    if tiers and scores[0] != 1.0:
        bad.append("the best tier scores 1.0")
    if any(not (0 < (x or 0) <= 1) for x in scores) or scores != sorted(scores, reverse=True):
        bad.append(f"scores must fall in (0, 1], best first: {scores}")
    if [t.get("name") for t in tiers] != list(TIER_NAMES[:len(tiers)]) and len(tiers) != 2:
        bad.append("tier names: best, second, worst")
    if len(tiers) == 2 and [t.get("name") for t in tiers] != ["best", "worst"]:
        bad.append("two tiers are best and worst")
    if not s.get("not_ok"):
        bad.append("say what does not count (not_ok)")
    return bad
