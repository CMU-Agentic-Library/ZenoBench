"""Graded outcomes of the v6 designs (11-11): one task, several ways to finish it, different scores.

Each reviewed design (``v6_variants`` key) gets a ``scoring`` entry, copied onto every layout of the design
(``variants[lid]["scoring"]``) so an episode carries it like its goal (episode.catalog.VARIANT_OVERRIDES):

- ``D``: 1 when the task forks (more than one acceptable way to finish it, scored differently), else 0.
- ``tiers``: best first; each ``{"name", "score", "goal", "why"}``.  ``goal`` is a goal in the usual form
  (``{"all": [...], "any": [...]}``), or None for the layout's own goal.  The episode scores the first tier
  whose goal holds on the final state; none holds -> ``not_ok`` (score 0).
  A ``goal`` may also be ``{"by_layout": {lid: goal}}`` when the right spot depends on the layout, or
  ``{"drop": [kind, ...]}``: the layout's goal without its atoms of those kinds (a looser tier).
- ``not_ok``: what does not count at all (documentation; scored 0 because no tier holds).

D = 0 means there is no substitution: the single tier is the layout's goal.

Success (11-11, user): every tier counts as task success (episode.Episode.check); only the score differs.
``not_ok`` is failure.

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
    # T01 table_seats: breakfast set for three along the east edge of dining_table_2; free slots: one too
    # narrow between two seats, one wide at the far end away from every seat, one wide beside a seat; the
    # west half empty.  Exposing a flat book first is a required step, not a fork
    ("T01", "table_seats"): {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "the wide slot beside a seat: easy to read while eating, 5 cm clear of the dishes, nothing moved"},
        {"name": "second", "score": 0.6, "goal": {"drop": ["near_any"]},
         "why": "on the set table, clear of the dishes, nothing moved, but beside no seat (the far end or the "
                "west half): out of the way, the guest has to reach for it"},
        {"name": "worst", "score": 0.3, "goal": {"drop": ["near_any", "clear_of"]},
         "why": "squeezed into the narrow slot against the dishes, though nothing moved or tipped"}],
        "not_ok": "on the other, unset dining table (dining_table_1); a dish moved or tipped to make room; "
                  "anywhere else or still held"},
    # T01 which_table: breakfast is set on one of the two dining tables (seed), the other holds toys; finding
    # the guests' table is the point.  On their table the tiers are table_seats'; the toy table does not count
    ("T01", "which_table"): {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "the guests' table, the wide slot beside a seat, clear of the dishes, nothing moved"},
        {"name": "second", "score": 0.6, "goal": {"drop": ["near_any"]},
         "why": "the guests' table, clear of the dishes, nothing moved, beside no seat"},
        {"name": "worst", "score": 0.3, "goal": {"drop": ["near_any", "clear_of"]},
         "why": "the guests' table, squeezed against the dishes, nothing moved or tipped"}],
        "not_ok": "the toy table (the wrong table); a dish moved or tipped; anywhere else or still held"},
    # T01 which_book: three books (the island's, the guest's in the room the instruction names, one in the
    # other room); the guest's book is the point.  No middle tier: the wrong book is not the task done
    ("T01", "which_book"): {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "only the guest's book on a dining table, the other two untouched"},
        {"name": "worst", "score": 0.3, "goal": {"drop": ["near_start"]},
         "why": "the guest's book on a dining table, but another book brought along or moved too"}],
        "not_ok": "the guest's book not on a dining table (the wrong book, or none); still held"},
    # T02 clear (control): two free blocks on the island; either on the other is the same
    ("T02", "clear"): only("one block on the other, the hand empty", "no stack, or a block dropped"),
}


def _no_room_fallback(task: dict) -> dict:
    """T01 no_room_fallback: the tiers depend on whether the layout has a suitable slot (on the table: the
    layout's goal) or not (full_*: a bookcase is the layout's goal)."""
    lays = task["v6_variants"]["no_room_fallback"]["layouts"]
    goals = {lid: task["variants"][lid]["goal"] for lid in lays}
    table = next(g for g in goals.values() if not g.get("any"))
    on_table = next(a for a in table["all"] if a[0] == "on")
    clear = next(a for a in table["all"] if a[0] == "clear_of")
    shelves = next(g["any"] for g in goals.values() if g.get("any"))
    kept = lambda g: [a for a in g["all"] if a[0] in ("near_start", "upright", "hand_empty")]   # nothing moved
    second, worst = {}, {}
    for lid, g in goals.items():
        if g.get("any"):                         # no suitable slot: the bookcase is best
            second[lid] = {"all": kept(g) + [on_table, clear]}
            worst[lid] = {"all": kept(g) + [on_table]}
        else:                                    # a slot beside a seat: the bookcase is giving up too early
            second[lid] = {"all": kept(g) + [on_table, clear]}
            worst[lid] = {"all": kept(g), "any": [[on_table]] + shelves}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "a slot beside a seat: there, clear of the dishes, nothing moved; no such slot (full_*): a bookcase, "
                "the fallback the instruction names (any bookcase, any shelf)"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "on the set table, clear of the dishes, nothing moved, beside no seat (with no suitable slot: "
                "the instruction's fallback skipped, the meal not disturbed)"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "squeezed against the dishes or the cereal, nothing moved or tipped; or, with a suitable slot "
                "free, put away in a bookcase (gave up too early)"}],
        "not_ok": "a dish or the cereal moved or tipped to make room; anywhere else or still held"}


def _reader_seat(task: dict) -> dict:
    """T01 reader_seat: a wide slot beside every seat; the book goes beside the seat with the mug."""
    lays = task["v6_variants"]["reader_seat"]["layouts"]
    second, worst = {}, {}
    for lid in lays:
        g = task["variants"][lid]["goal"]["all"]
        kept = [a for a in g if a[0] in ("near_start", "upright", "hand_empty")]
        on = next(a for a in g if a[0] == "on")
        clear = next(a for a in g if a[0] == "clear_of")
        near = next(a for a in g if a[0] == "near_any")
        far = next(a for a in g if a[0] == "not near_any")
        plates = sorted({x for x in near[2] + far[2] if not x.startswith("mug")})   # one plate or bowl per seat
        second[lid] = {"all": kept + [on, clear, ["not near_any", on[1], plates, near[3]]]}
        worst[lid] = {"all": kept + [on]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "beside the seat with the mug, clear of the dishes, nothing moved"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "on the table, clear of the dishes, nothing moved, beside no seat: the reader not found, but a "
                "neutral spot anyone can reach"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "on the table, nothing moved or tipped, but beside another guest (the wrong reader) or against "
                "the dishes"}],
        "not_ok": "a dish moved or tipped; anywhere else (the other dining table too) or still held"}


def _crowded_use_another(task: dict) -> dict:
    """T02 crowded_use_another: block B wedged against the full oatmeal bowl (tight_*) -> the block in another
    room; loose: any two.  Pulling B out anyway, the bowl untouched, is the worst tier."""
    lays = task["v6_variants"]["crowded_use_another"]["layouts"]
    blocks = ("wooden_block_a", "wooden_block_b", "floor_block")
    any_pair = [[["on_top_of", x, y]] for x in blocks for y in blocks if x != y]
    worst = {}
    for lid in lays:
        g = task["variants"][lid]["goal"]
        worst[lid] = {"all": [a for a in g["all"] if a[1] != "wooden_block_b"], "any": any_pair}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "tight: block A with the block from the other room (either on the other), B, the bowl and the "
                "rolling pin untouched; loose: any two blocks, the bowl and the pin untouched"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "tight: B pulled out from beside the bowl and stacked anyway (against the instruction), the bowl "
                "and the pin unmoved, the bowl upright"}],
        "not_ok": "the bowl or the rolling pin moved, the bowl tipped; no stack"}


def _tower_orders(items, top_only=()) -> list:
    """Every three-level tower of ``items`` on the island (an item in ``top_only`` has no flat top)."""
    from itertools import permutations
    return [[["on_top_of", m, b], ["on_top_of", t, m], ["on", b, "kitchen_island/top"]]
            for b, m, t in permutations(items) if b not in top_only and m not in top_only]


def _third_toy_elsewhere(task: dict) -> dict:
    """T02 third_toy_elsewhere: two blocks on the island, a block-sized sponge beside them (no toy), the third
    toy in another room."""
    lays = task["v6_variants"]["third_toy_elsewhere"]["layouts"]
    a, b = "wooden_block_a", "wooden_block_b"
    two = {lid: {"all": [["near_start", "kitchen_sponge", 0.03], ["hand_empty", "right"]],
                 "any": [[["on_top_of", a, b], ["on", b, "kitchen_island/top"]],
                         [["on_top_of", b, a], ["on", a, "kitchen_island/top"]]]} for lid in lays}
    sponge = {lid: {"all": [["hand_empty", "right"]], "any": _tower_orders((a, b, "kitchen_sponge"))}
              for lid in lays}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "three toys on the island, the third one fetched from the other room"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": two},
         "why": "the two blocks stacked on the island, the sponge untouched: two levels only, nothing misused"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": sponge},
         "why": "three levels with the kitchen sponge (no toy, a dish sponge) for the third"}],
        "not_ok": "no stack, or the tower not on the island"}


# designs whose tiers are built from their layouts' goals
BUILT = {("T02", "third_toy_elsewhere"): _third_toy_elsewhere, ("T02", "crowded_use_another"): _crowded_use_another, ("T01", "no_room_fallback"): _no_room_fallback, ("T01", "reader_seat"): _reader_seat}


def scoring_for(task_id: str, design: str, task: dict | None = None) -> dict | None:
    s = next((s for (tid, d), s in SCORING.items() if task_id.startswith(tid) and d == design), None)
    if s is None and task is not None:
        f = next((f for (tid, d), f in BUILT.items() if task_id.startswith(tid) and d == design), None)
        s = f(task) if f else None
    return s


def attach_scoring(out: dict) -> int:
    """Copy each reviewed design's scoring onto its layouts; returns how many designs are reviewed."""
    import copy
    n = 0
    for t in out["tasks"]:
        for design, info in t["v6_variants"].items():
            s = scoring_for(t["task_id"], design, t)
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
    if "drop" in g:
        base = task["goal"]
        return {k: [a for a in base.get(k, []) if not (isinstance(a, list) and a and a[0] in g["drop"])]
                for k in ("all", "any") if k in base}
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
