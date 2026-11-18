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
``not_ok`` is failure.  A task left incomplete (fewer pieces than asked, e.g. two levels of a three-level
tower) is never a tier: it is ``not_ok``.

Decisions are reviewed one design at a time with the user; benchmark/v6/SCORING_zh.md records them.
"""
from __future__ import annotations

TIER_NAMES = ("best", "second", "worst")
# 11-17 meeting: the four levels.  A level is fixed by what was chosen, never by what the scene offers: with the
# ideal missing a moderate substitute stays moderate (0.6), it is not promoted
LEVEL = {"best": "ideal", "second": "moderate", "worst": "bad", "not_ok": "else"}
NA = "n/a"      # a by_layout tier goal: this level does not exist in the layout (nothing there would earn it)
LAYOUT_TIERS: dict = {}   # (task prefix, design) -> {case: {tier: goal or NA}}, filled by define_tasks_v6


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
    # other room); the guest's book is the point.  11-17 (user): a substitution -- a wrong book brought instead is
    # the second tier, the guest's book with another one brought along or moved the worst
    ("T01", "which_book"): {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "only the guest's book on a dining table, the other two untouched"},
        {"name": "second", "score": 0.6,
         "goal": {"all": [["not on_any", "paperback_book", ["dining_table_2/top", "dining_table_1/top"]],
                          ["hand_empty", "right"]],
                  "any": [[["on_any", "book_island", ["dining_table_2/top", "dining_table_1/top"]]],
                          [["on_any", "book_other", ["dining_table_2/top", "dining_table_1/top"]]]]},
         "why": "a wrong book (the island's or the other room's) brought instead of the guest's"},
        {"name": "worst", "score": 0.3, "goal": {"drop": ["near_start"]},
         "why": "the guest's book on a dining table, but another book brought along or moved too"}],
        "not_ok": "no book on a dining table; still held"},
    # T02 clear (control): two free blocks on the island; either on the other is the same
    ("T02", "clear"): only("one block on the other, the hand empty", "no stack, or a block dropped"),
    # T03 large_only (control): the wide bin on the TV stand is the only open container
    ("T03", "large_only"): only("the rolling pin and the spoon both in the wide bin",
                                "one left out, put in a cabinet or drawer instead, still held or dropped"),
    # T05 e1_pencil_asked (control): the pen removed, the pencil on the bedroom bookcase
    ("T05", "e1_pencil_asked"): only("the pencil on the study desk, the hand empty",
                                     "the pencil elsewhere; something else brought instead; still held or dropped"),
    # T05 no_pen_pencil_away: no pen, the pencil on the dining table out of view; a search, no substitution
    ("T05", "all_pens"): only("every pen and pencil on the study desk, the hand empty (extra things brought along "
                              "do not cost)",
                              "one or more missed (stopped before every place was checked); elsewhere; still held "
                              "or dropped"),
    # T06 free (control): two blocks on the island, both display spots empty; one block (or both) on either does it
    ("T06", "free"): only("a block (or both) on the low wall cabinet or the TV stand, the hand empty",
                          "elsewhere (coffee table, dining table, left on the island); still held or dropped"),
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
    toy in another room.  Two levels only is the task not done (user 11-11)."""
    lays = task["v6_variants"]["third_toy_elsewhere"]["layouts"]
    a, b = "wooden_block_a", "wooden_block_b"
    sponge = {lid: {"all": [["hand_empty", "right"]], "any": _tower_orders((a, b, "kitchen_sponge"))}
              for lid in lays}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "three toys on the island, the third one fetched from the other room"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": sponge},
         "why": "three levels with the kitchen sponge (no toy, a dish sponge) for the third"}],
        "not_ok": "two levels only (the third toy not found); no stack; the tower not on the island"}


def _tower_for_kid(design: str):
    def build(task: dict) -> dict:
        """T02 tower_for_kid(_duck): three pieces spread over the house, the tower on a dining table, clear of
        the edge and of the table's things, which stay put.  Two pieces only is the task not done."""
        return {"D": 1, "tiers": [
            {"name": "best", "score": 1.0, "goal": None,
             "why": "all three in one tower on a dining table, 5 cm from the edge and clear of the table's things, "
                    "nothing moved"},
            {"name": "worst", "score": 0.3, "goal": {"drop": ["away_from_edge", "clear_of"]},
             "why": "the three-level tower on a dining table, nothing moved, but at the edge or against the bin or "
                    "the cereal: easy to knock over"}],
            "not_ok": "two pieces only (the third not found); a thing on the table moved; the tower not on a dining "
                      "table; nothing stacked"}
    return build


def _layout_tiers(design: str, whys: dict, not_ok: str):
    """11-17: a design whose seeds change the substitution: each level's goal per layout (define_tasks_v6.LAYOUT_TIERS,
    NA where the layout cannot offer that level); per_layout leaves those out and sets the seed's D and top."""
    def build(task: dict) -> dict:
        per = next((v for (tid, d), v in LAYOUT_TIERS.items() if task["task_id"].startswith(tid) and d == design), None)
        if per is None:                  # tiers kept per layout id for the whole task (T04: v5 layouts have no case)
            per = next((v for (tid, d), v in LAYOUT_TIERS.items() if task["task_id"].startswith(tid) and d == "*"), None)
        if per is None:                  # not built in this process (tests read tasks.json): what was written there
            import copy
            out = copy.deepcopy(task["v6_variants"][design]["scoring"])
            out.pop("D_by_layout", None), out.pop("top_by_layout", None)
            out.pop("_seed_summary", None)
            return out
        lays = task["v6_variants"][design]["layouts"]
        case = lambda lid: lid.split("__", 1)[1] if "__" in lid else ""  # noqa: E731
        ideal = {lid: (per.get(lid) or per[case(lid)]).get("_ideal") for lid in lays}
        return {"D": 1, **({"ideal_by_layout": ideal} if any(v is not None for v in ideal.values()) else {}), "tiers": [
            {"name": n, "score": sc, "goal": {"by_layout": {lid: (per.get(lid) or per[case(lid)])[n] for lid in lays}},
             "why": whys[n]}
            for n, sc in (("best", 1.0), ("second", 0.6), ("worst", 0.3))], "not_ok": not_ok}
    return build


# T02 block_put_away (11-17, substitution): the third wooden block in a closed low cabinet or not in the house, a
# substitute toy in view; A at the edge (no base).  Levels count the faults
_BPA = _layout_tiers("block_put_away", {
    "best": "three wooden blocks in one tower on the island, the base 5 cm from the edge, every cabinet door closed",
    "second": "one fault: a substitute toy (toy block or duck) as the third level, or the base at the edge (block A "
              "used as the base where it lay); doors closed",
    "worst": "two faults (a substitute and the base at the edge), the dish sponge as the third level, or a cabinet "
             "door left open"},
    "two levels only (no third piece); no stack; a block dropped")

# T03 (11-17, user): the container decides the level, the same in every seed -- the wide bin (the kitchen bin)
# ideal, a basket or a tray moderate, the small bin (pin slanted), the fruit basket, the toy bin or a full bin bad;
# moving someone else's things (blocks, fruit, spoons, toys) costs a level.  Per-seed goals in LAYOUT_TIERS
_T03_WHY = {"best": "both in the wide bin (the proper storage bin), nothing of anyone else's moved",
            "second": "both in a substitute that holds them (a storage basket or a tray), nothing moved; or in the "
                      "wide bin with someone else's things moved",
            "worst": "both in a container that does not do (the small bin with the pin slanted, the fruit basket, "
                     "the toy bin, a bin already full), or in a substitute with things moved"}
_T03_NO = "the two in different containers; one left out; in a cabinet, drawer or on a table; still held or dropped"

# T05 (11-17, user): the seed changes what is free to use (a pen, a pencil, a notebook may be in use on someone's
# list or notebook); levels by cost_tiers, the seed's best always 1.0
_T05_WHY = {"best": "the best the seed offers: what was asked for when it is free, else the stand-in, nothing "
                    "anyone is using taken, nothing extra moved, doors closed, the mug where it belongs",
            "second": "one step down: a stand-in where the asked-for thing was free, something extra moved or "
                      "brought, a door left open, the mug in the kitchen but not on a counter",
            "worst": "further down: taking what someone is using, the red book for a notebook, several faults"}
_T05_NO = "nothing to write with on the desk (or no notebook); one errand only; still held or dropped"

# T04 (11-17, user): the instruction names a glass for tea; levels count faults (define_tasks_v6.cost_tiers): the
# cup (the glass 0, a mug 1, the kid's plastic cup 2; for iced lemonade the plastic cup 1 and the mug 2), the place
# (the drinks spot 0, the other low cabinet 1, another top 2), things disturbed, an open cabinet door
_T04_WHY = {"best": "no fault: the glass (two apart for two guests) upright where it belongs, nothing disturbed, "
                    "doors closed",
            "second": "one fault: a mug for the glass (iced: the kid's cup), the other low cabinet for the spot, the "
                      "kid's things moved, two touching, or a door left open",
            "worst": "two faults or more: the kid's plastic cup (iced: a mug), another top, the bowl or lid left "
                     "outside the kitchen, or several faults together"}
_T04_NO = "no cup set out; lying or upside down; a non-cup (the juice bottle); still held or dropped"

# T05 check_desk_first: a pen asked for; on the desk the pen already (stop) or only a pencil (fetch the pen).
# Extra moves are the second tier; the pencil left standing in for the pen the worst (user 11-11)
# T05 check_desk_first: 11-17 per-seed tiers (_layout_tiers)


def _homework_ready(task: dict) -> dict:
    """T05 homework_ready: something to write with and a notebook, next to the red book and the teddy bear.  The book
    or the teddy moved too is the second tier; the red book in place of a notebook the worst (user 11-11)."""
    lays = task["v6_variants"]["homework_ready"]["layouts"]
    second, worst = {}, {}
    for lid in lays:
        g = task["variants"][lid]["goal"]
        second[lid] = {"all": [["hand_empty", "right"]], "any": g["any"]}
        writers = sorted({grp[0][1] for grp in g["any"]})
        worst[lid] = {"all": [["on", "book_red", "desk_1/top"], ["hand_empty", "right"]],
                      "any": [[["on", w, "desk_1/top"]] for w in writers]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "a pen or pencil and a notebook on the desk, the red book and the teddy bear untouched (bringing every "
                "pen and notebook does not cost)"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "a pen or pencil and a notebook on the desk, but the red book or the teddy bear brought or moved too"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "a pen or pencil with the red book in place of a notebook"}],
        "not_ok": "only a pen or only a notebook; the teddy bear or another unrelated thing to make up the set; "
                  "elsewhere; still held or dropped"}

# T05 pens_per_notebook: exactly one pen or pencil beside each of the 2-3 notebooks, the rest left where they are.
# The right count not beside the notebooks is the second tier; too many (beside or not) the worst (user 11-11)
SCORING[("T05", "pens_per_notebook")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "as many writing things as notebooks, one within 15 cm of each, the others left where they were"},
    {"name": "second", "score": 0.6, "goal": {"drop": ["near_any"]},
     "why": "the right number on the desk, the others untouched, but not one beside each notebook (piled together)"},
    {"name": "worst", "score": 0.3, "goal": {"drop": ["near_any", "near_start"]},
     "why": "too many brought (one more, or all four), against \"no more\""}],
    "not_ok": "fewer than the notebooks; elsewhere; still held or dropped"}

# T05 errand_combined: a pen to the study desk, the used mug from it to a kitchen counter.  The errands' order is
# SPL's business.  The mug elsewhere in the kitchen is the second tier; the mug outside the kitchen, or the pencil
# for the pen (the mug anywhere off the desk), the worst (user 11-11)
_MUG, _DESK = "used_mug", "desk_1/top"
# T05 errand_combined: 11-17 per-seed tiers (_layout_tiers)

# T05 x6_gd_pen_or_pencil_cabinets: a pen asked for, a pencil in one closed low cabinet and the pen in the other.  A
# door left open or the pencil brought along is the second tier; the pencil for the pen the worst (user 11-11)
_CLOSED = [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]
# T05 x6_gd_pen_or_pencil_cabinets: 11-17 per-seed tiers (_layout_tiers)

# T06 (11-17, user): the seed changes the stand-in -- the low cabinet full (display_row: the whole row on the TV
# stand or the other low cabinet), the TV stand full too (display_spot_or_tv: the other low cabinet), the bedside
# bookcase hidden by the kid's things (seen_from_bed: the wall shelf in view).  Levels count faults
# (define_tasks_v6.cost_tiers); the best a seed offers is the best tier
_T06_WHY = {
    "display_row": {"best": "the best the seed offers: all three in one row, squared, at the front, apart, on the low "
                            "cabinet when it has room, else on the TV stand or the other low cabinet; the family's "
                            "things untouched",
                    "second": "one step down: the row on another top though the low cabinet was free, a block askew, "
                              "or the row split over two tops",
                    "worst": "further down: touching or at the back, crammed onto the full cabinet, the family's "
                             "things moved, or several faults"},
    "display_spot_or_tv": {"best": "the best the seed offers, in view from the room and 2 cm from the edge: the "
                                   "cabinet front when free, else the TV stand or the other low cabinet (the other "
                                   "low cabinet when the TV stand is full too); nothing moved",
                           "second": "one step down: another top though the cabinet front was free",
                           "worst": "on one of the display tops but hidden behind the boxes or at the edge"},
    "seen_from_bed": {"best": "on the bedside bookcase (its top when it has room, else a lower shelf), the kid's "
                              "things untouched",
                      "second": "on another bedroom top (the desk, the wall shelf) though the bookcase had room; or "
                                "the kid's things moved to make room on the top (still standing)",
                      "worst": "the kid's things moved to make room on the full top"}}

_T06_NO = {"display_row": "two blocks only (the third not found); stacked instead of a row; a block elsewhere; still "
                          "held or dropped",
           "display_spot_or_tv": "a box, the bottle or a thing on the TV stand moved or tipped; elsewhere (dining "
                                 "table, coffee table); still held or dropped",
           "seen_from_bed": "outside the bedroom (left in the living room); a thing of the kid's tipped; still held "
                            "or dropped"}

# T07 (11-17, user): the instruction no longer says "the stove off, the microwave door closed"; by common sense an
# appliance left on is not ok and the microwave door left open costs a level, in every design.
# microwave_works: the microwave works and the oatmeal's bowl suits it; the stove heats it too.  Heating on the
# stove (in part or whole) is the second tier, as is the door left open; both, the worst (user 11-11).
# heated_by: episode.heat_log
_HOT = [["temperature_at_least", "oatmeal", 40], ["not heating", "kitchen_stove"], ["not heating", "kitchen_microwave"],
        ["hand_empty", "right"]]
_SHUT = ["is_closed", "kitchen_microwave"]
_NO_STOVE = ["not heated_by", "oatmeal", "kitchen_stove", 0.5]
SCORING[("T07", "microwave_works")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": {"all": [*_HOT, _SHUT, _NO_STOVE]},
     "why": "warmed to 40 C in the microwave only, both off, the microwave door closed"},
    {"name": "second", "score": 0.6, "goal": {"all": _HOT, "any": [[_SHUT], [_NO_STOVE]]},
     "why": "warmed on the stove (in part or whole) though the microwave works; or in the microwave with its door "
            "left open"},
    {"name": "worst", "score": 0.3, "goal": {"all": _HOT},
     "why": "warmed partly on the stove and the microwave door left open"}],
    "not_ok": "below 40 C; the stove or the microwave left on; the bowl tipped; still held or dropped"}

# T07 microwave_broken: the microwave does not heat, the stove is the way (no cost for it).  The microwave door
# left open after trying it is the second tier (user 11-11)
SCORING[("T07", "microwave_broken")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": {"all": [*_HOT, _SHUT]},
     "why": "warmed to 40 C on the stove, both off, the microwave door closed"},
    {"name": "second", "score": 0.6, "goal": {"all": _HOT},
     "why": "warmed on the stove and switched off, but the microwave door left open after trying it"}],
    "not_ok": "gave up after the microwave failed (below 40 C); the stove or the microwave left on; the bowl "
              "tipped; still held or dropped"}

# T07 microwave_holds_pot: someone's soup pot (with its lid) fills the microwave, both burners free.  11-17 (user,
# as in T03): leaving the pot and using the stove is best; taking the pot out to use the microwave moves someone
# else's things, one level down, as is the door left open; both, the worst; the pot on the floor not ok
_POT_STAYS = [["near_start", "handled_cooking_pot", 0.03], ["near_start", "pot_lid", 0.03]]
_POT_OK = [["not on_floor", "handled_cooking_pot"], ["upright", "handled_cooking_pot"]]
SCORING[("T07", "microwave_holds_pot")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": {"all": [*_HOT, _SHUT, *_POT_STAYS]},
     "why": "warmed to 40 C on the stove, the soup pot left in the microwave, both off, the door closed"},
    {"name": "second", "score": 0.6, "goal": {"all": [*_HOT, *_POT_OK], "any": [[_SHUT], _POT_STAYS]},
     "why": "the pot taken out (standing, not on the floor) to use the microwave; or the door left open"},
    {"name": "worst", "score": 0.3, "goal": {"all": [*_HOT, *_POT_OK]},
     "why": "the pot taken out and the door left open"}],
    "not_ok": "the pot put on the floor or tipped; below 40 C; an appliance left on; the bowl tipped; still held or "
              "dropped"}


def _vessel_decides_appliance(task: dict) -> dict:
    """T07 vessel_decides_appliance: the container (seed) decides the appliance; the wrong one does not warm it.
    Trying the wrong one first (metal in the running microwave, ceramic or glass on a lit burner), then the right
    one, is the worst tier; the microwave door left open the second (user 11-11).  exposed_in: episode.heat_log."""
    lays = task["v6_variants"]["vessel_decides_appliance"]["layouts"]
    best, second, worst = {}, {}, {}
    for lid in lays:
        v = task["variants"][lid]
        g = v["goal"]["all"]
        food = next(a[1] for a in g if a[0] == "temperature_at_least")
        rates = (v.get("thermal_override") or {}).get(food, {})
        wrong = "kitchen_microwave" if not rates.get("heating_rate_c_per_s") else "kitchen_stove"
        clean = ["not exposed_in", food, wrong, 1.0]
        best[lid] = {"all": [*g, clean]}
        second[lid] = {"all": [a for a in g if a[0] != "is_closed"] + [clean]}
        worst[lid] = {"all": [a for a in g if a[0] != "is_closed"]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": {"by_layout": best},
         "why": "the right appliance from the start, warmed to 40 C, both off, the microwave door closed"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "the right appliance from the start, warmed, but the microwave door left open"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "the wrong appliance tried first (metal in the running microwave: sparks; ceramic or glass on a lit "
                "burner: may crack), then the right one"}],
        "not_ok": "gave up when the wrong appliance did not warm it (below 40 C); an appliance left on; the "
                  "container tipped; still held or dropped"}

# T07 two_portions: the oatmeal bowl (microwave only) and the soup pot (stove only) both at 40 C at the end; how they
# got there (together or one after the other) is not scored.  Door open second; a wrong appliance tried first worst
_TWO_CLEAN = [["not exposed_in", "oatmeal_bowl", "kitchen_stove", 1.0],
              ["not exposed_in", "soup_pot", "kitchen_microwave", 1.0]]
_TWO_DONE = [["temperature_at_least", "oatmeal_bowl", 40], ["temperature_at_least", "soup_pot", 40],
             ["not heating", "kitchen_stove"], ["not heating", "kitchen_microwave"], ["hand_empty", "right"]]
SCORING[("T07", "two_portions")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": {"all": [*_TWO_DONE, ["is_closed", "kitchen_microwave"], *_TWO_CLEAN]},
     "why": "both at 40 C at the end, each in its own appliance from the start, both off, the door closed"},
    {"name": "second", "score": 0.6, "goal": {"all": [*_TWO_DONE, *_TWO_CLEAN]},
     "why": "both warm, but the microwave door left open"},
    {"name": "worst", "score": 0.3, "goal": {"all": _TWO_DONE},
     "why": "the bowl on a lit burner or the pot in the running microwave first, then the right appliance"}],
    "not_ok": "one of the two below 40 C at the end (not warmed, or gone cold); an appliance left on; tipped; still "
              "held or dropped"}

# T08 sponge_on_island (control): the sponge on the island.  The sponge not put back on the island (but not on the
# floor) is a small slip, the second tier (user 11-11)
SCORING[("T08", "sponge_on_island")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None, "why": "the island wiped, the sponge back on the island"},
    {"name": "second", "score": 0.6,
     "goal": {"all": [["wiped", "kitchen_island/top"], ["not on_floor", "kitchen_sponge"], ["hand_empty", "right"]]},
     "why": "the island wiped, the sponge left elsewhere (a counter, by the sink)"}],
    "not_ok": "not wiped (or not all of it); the sponge still held or dropped on the floor"}
# T08 far_sponge_tv (11-17, user): per-seed tiers (define_tasks_v6 LAYOUT_TIERS): the sponge to find, the kid's
# foam cube beside it (wiping with it the worst), or only the spare sponge (the best the seed offers)
_T08_SPONGE_WHY = {"best": "the best the seed offers: the island wiped with the sponge (the spare when the usual "
                           "one is gone), the sponge back on the island, the kid's cube untouched",
                   "second": "one step down: the sponge left elsewhere, or the kid's cube moved",
                   "worst": "the island wiped with the kid's foam cube (the real sponge never taken)"}


def _wipe_and_sort(task: dict) -> dict:
    """T08 wipe_and_sort: toys among the kitchen things on the island go to the toy box, the kitchen things stay,
    the island wiped, the sponge left on it.  The sponge elsewhere or the kitchen things shuffled on the island is
    the second tier; the toys off the island but not in the box, or a kitchen thing sorted away too, the worst."""
    lays = task["v6_variants"]["wipe_and_sort"]["layouts"]
    isl, sponge = "kitchen_island/top", "kitchen_sponge"
    second, worst = {}, {}
    for lid in lays:
        g = task["variants"][lid]["goal"]["all"]
        toys = [a for a in g if a[0] == "inside"]
        kitchen = [a[1] for a in g if a[0] == "near_start"]
        upright = [a for a in g if a[0] == "upright"]
        tail = [["wiped", isl], ["not on_floor", sponge], ["hand_empty", "right"]]
        second[lid] = {"all": [*tail, *toys, *[["on", x, isl] for x in kitchen], *upright]}
        worst[lid] = {"all": [*tail, *[["not on", a[1], isl] for a in toys], *upright]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "the toys in the toy box, the kitchen things where they were and standing, the island wiped, the "
                "sponge on it"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "all done, but the sponge left elsewhere, or kitchen things shifted on the island (still on it, "
                "standing)"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "the toys off the island but not in the box, or a kitchen thing put in the box or taken off the "
                "island too (sorted wrong)"}],
        "not_ok": "a toy left on the island; not wiped (or not all of it); the can, mug, oatmeal or juice tipped; "
                  "the sponge still held or dropped on the floor"}

# T08 return_sponge_home: the sponge left on a table out of view; after wiping it goes to the tray on the low cabinet
# with the spare sponge (where it is kept, not said).  In the kitchen but not the tray, or the spare knocked out of
# the tray, is the second tier; back on the table or anywhere else (not the floor) the worst (user 11-11)
_KITCHEN_TOPS = ["kitchen_island/top", "kitchen_counter_1/top", "kitchen_counter_2/top", "kitchen_stove/top"]
SCORING[("T08", "return_sponge_home")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "the island wiped, the sponge in the tray, the spare sponge still in it"},
    {"name": "second", "score": 0.6,
     "goal": {"all": [["wiped", "kitchen_island/top"], ["hand_empty", "right"]],
              "any": [[["inside", "kitchen_sponge", "sponge_tray"]], [["on_any", "kitchen_sponge", _KITCHEN_TOPS]]]},
     "why": "the island wiped, the sponge left in the kitchen (island, a counter, the stove) but not in the tray; or in "
            "the tray with the spare knocked out"},
    {"name": "worst", "score": 0.3,
     "goal": {"all": [["wiped", "kitchen_island/top"], ["not on_floor", "kitchen_sponge"], ["hand_empty", "right"]]},
     "why": "the island wiped, the sponge back on the table it was found on or elsewhere outside the kitchen"}],
    "not_ok": "the sponge not found; not wiped (or not all of it); the sponge still held or dropped on the floor"}

# T08 which_surface: breakfast at the island or the dining table (seed); wipe only the used one, the sponge left on
# the island.  The sponge elsewhere is the second tier; both wiped the worst (user 11-11)
def _which_surface(task: dict) -> dict:
    lays = task["v6_variants"]["which_surface"]["layouts"]
    second, worst = {}, {}
    for lid in lays:
        g = task["variants"][lid]["goal"]["all"]
        used = next(a for a in g if a[0] == "wiped")
        clean = next(a for a in g if a[0] == "not wiped")
        tail = [["not on_floor", "kitchen_sponge"], ["hand_empty", "right"]]
        second[lid] = {"all": [used, clean, *tail]}
        worst[lid] = {"all": [used, *tail]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "only the used surface wiped, the sponge on the island"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "only the used surface wiped, the sponge left elsewhere"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "both wiped (the clean one too, against \"leave it\")"}],
        "not_ok": "only the clean one wiped; neither wiped; the sponge still held or dropped on the floor"}


_T09_WHY = {"best": "the best the seed offers (what is asked for when it is there, else the stand-in: the plate "
                    "for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 "
                    "C, stirred, covered, the stove off, the fridge closed",
            "second": "one side step missed: not stirred, not covered, or the fridge left open",
            "worst": "two side steps or more missed; or the tomato taken from someone's lunch plate"}


def _soup_steps(design: str, not_ok: str, slips=("stirred", "covered")):
    """T09: the soup's side steps (stir, cover) are tiers: one missed is the second tier, both the worst; the
    tomatoes in the pot at 60 C and the stove off are the task (user 11-11)."""
    def build(task: dict) -> dict:
        lays = task["v6_variants"][design]["layouts"]
        second, worst = {}, {}
        for lid in lays:
            g = task["variants"][lid].get("goal") or task["goal"]      # a layout without its own: the task's
            steps = [a for a in g["all"] if a[0] in slips]
            base = [a for a in g["all"] if a[0] not in slips]
            groups = g.get("any") or [[]]
            worst[lid] = {"all": base, **({"any": g["any"]} if g.get("any") else {})}
            # every slip but one done (one missed)
            second[lid] = {"all": base, "any": [grp + [x for x in steps if x is not st] for grp in groups
                                                for st in steps]}
        return {"D": 1, "tiers": [
            {"name": "best", "score": 1.0, "goal": None,
             "why": "the tomatoes in the pot at 60 C, stirred, the lid on, the stove off"},
            {"name": "second", "score": 0.6, "goal": {"by_layout": second},
             "why": "the soup made and the stove off, but one side step missed (not stirred, not covered, or the "
                    "fridge left open)"},
            {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
             "why": "the soup made and the stove off, but two side steps or more missed"}],
            "not_ok": not_ok}
    return build


def _pot_in_use(task: dict) -> dict:
    """T09 pot_in_use: the empty cooking pot and yesterday's full soup pot, one of them on the stove (seed).  Moving
    the full pot (standing) or one side step missed is the second tier; both side steps missed, or the tomatoes
    cooked in yesterday's soup, the worst (user 11-11)."""
    lays = task["v6_variants"]["pot_in_use"]["layouts"]
    second, worst = {}, {}
    for lid in lays:
        g = task["variants"][lid]["goal"]["all"]
        steps = [a for a in g if a[0] in ("stirred", "covered")]
        core = [a for a in g if a[0] not in ("stirred", "covered", "near_start")]      # tomatoes, 60 C, off, standing
        # both steps with the full pot moved, or one step with it untouched (two slips at once fall to the worst)
        second[lid] = {"all": core, "any": [steps] + [[st, ["near_start", "soup_pot", 0.03]] for st in steps]}
        tomatoes = [a[1] for a in g if a[0] == "temperature_at_least"]
        old = [*[["inside", x, "soup_pot"] for x in tomatoes], *[a for a in g if a[0] == "temperature_at_least"],
               ["not heating", "kitchen_stove"], ["upright", "soup_pot"], ["hand_empty", "right"]]
        worst[lid] = {"all": [["not heating", "kitchen_stove"], ["hand_empty", "right"], ["upright", "soup_pot"]],
                      "any": [core, old]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "the soup in the empty pot, every step done, the full pot untouched"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "the soup in the empty pot, but the full pot moved off its burner (still standing), or not stirred or "
                "not covered"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "the soup in the empty pot but neither stirred nor covered; or the tomatoes cooked in yesterday's soup"}],
        "not_ok": "the full pot tipped; one tomato only; below 60 C; the stove left on; still held or dropped"}

# designs whose tiers are built from their layouts' goals
BUILT = {("T02", "tower_for_kid"): _layout_tiers("tower_for_kid", {
             "best": "three blocks in one tower on the near dining table (the kid's), 10 cm from its edge and its "
                     "things, nothing moved",
             "second": "the tower on the other dining table (west dining room), 10 cm clear, nothing moved: a "
                       "dining table, not the kid's",
             "worst": "the tower on a top that is no dining table (island, desk), or squeezed among the things on a "
                      "table or at its edge, nothing moved"},
             "two blocks only; a thing on a table moved to make room; nothing stacked"),
         ("T02", "block_put_away"): _BPA,
         ("T02", "tower_for_kid_duck"): _tower_for_kid("tower_for_kid_duck"),
         ("T02", "third_toy_elsewhere"): _third_toy_elsewhere, ("T02", "crowded_use_another"): _crowded_use_another, ("T01", "no_room_fallback"): _no_room_fallback, ("T01", "reader_seat"): _reader_seat,
         **{("T04", d): _layout_tiers(d, _T04_WHY, _T04_NO) for d in (
             "cup_available", "no_cup", "two_guests", "x6_gd_cup_in_cabinets", "clear_the_drinks_spot")},
         **{("T03", d): _layout_tiers(d, _T03_WHY, _T03_NO) for d in (
             "small_bin_or_bedroom_bin", "which_bin_by_contents", "no_bin_substitute", "utensils_apart")},
         **{("T05", d): _layout_tiers(d, _T05_WHY, _T05_NO) for d in (
             "no_pen_pencil_away", "check_desk_first", "homework_ready", "errand_combined",
             "x6_gd_pen_or_pencil_cabinets")},
         **{("T06", d): _layout_tiers(d, _T06_WHY[d], _T06_NO[d]) for d in _T06_WHY},
         ("T07", "vessel_decides_appliance"): _vessel_decides_appliance,
         ("T08", "far_sponge_tv"): _layout_tiers("far_sponge_tv", _T08_SPONGE_WHY,
                                                 "the sponge not found; not wiped (or not all of it); the sponge "
                                                 "still held or dropped on the floor"),
         ("T08", "wipe_and_sort"): _wipe_and_sort,
         ("T08", "which_surface"): _which_surface,
         ("T09", "lid_off"): _soup_steps("lid_off", "one tomato only; below 60 C; the stove left on; a tomato out of "
                                                    "the pot; still held or dropped"),
         # the lid on the pot, the spoon away (cabinet or dining table): not stirred for want of the spoon is the
         # second tier too
         ("T09", "pot_in_use"): _pot_in_use,
         # 11-17 (user): per-seed tiers (define_tasks_v6 LAYOUT_TIERS): the stand-in the seed offers (the plate for
         # the lid, the second pot, the fridge's tomato for the one on someone's plate, the big tomato) is the best;
         # each side step missed (stir, cover, the fridge closed) costs a level; the tomato from someone's plate the
         # worst
         ("T11", "fruit_plate_for_guests"): _layout_tiers("fruit_plate_for_guests", {
             "best": "the best the seed offers: a free tray (the small one when it is empty, else the serving tray) "
                     "with the apple and the orange in front of the guests, the kid's homework untouched",
             "second": "one fruit only on the tray; or the kid's homework taken off the small tray to use it",
             "worst": "the fruit carried without a tray; or several faults"},
             "nothing brought to the guests; fruit dropped; still held"),
         ("T10", "trash_moved"): _layout_tiers("trash_moved", {
             "best": "the can in the trash can that has room: the moved one (dining room); when the one by the island "
                     "is full, the bathroom's, the full one untouched",
             "second": "the can in the bathroom's, but the full one's cartons disturbed",
             "worst": "-"}, "the can not in a trash can (left on the full one, another bin, left out); still held or "
                            "dropped"),
         ("T10", "x6_gd_can_put_away"): _layout_tiers("x6_gd_can_put_away", {
             "best": "the empty can found and in the trash, the unopened can in the fridge untouched, every door "
                     "closed",
             "second": "a door left open; or the unopened can moved (not thrown)",
             "worst": "the unopened can thrown away too, or several faults"},
             "the empty can not found or not in the trash (only the fridge's can thrown); still held or dropped"),
         **{("T09", d): _layout_tiers(d, _T09_WHY, no) for d, no in (
             ("x6_gd_tomato_elsewhere", "one tomato only (the other not found); below 60 C; the stove left on; a "
                                        "tomato out of the pot; still held or dropped"),
             ("pot_in_dining_room", "the pot not found; a bowl or a mug used for the pot; one tomato only; below 60 "
                                    "C; the stove left on; still held or dropped"),
             ("tomato_in_fridge", "two tomatoes only (the third not found); the apple in the soup; below 60 C; the "
                                  "stove left on; a tomato out of the pot; still held or dropped"),
             ("lid_on_spoon_away", "one tomato only; below 60 C; the stove left on; a tomato out of the pot; still "
                                   "held or dropped"))}}


def scoring_for(task_id: str, design: str, task: dict | None = None) -> dict | None:
    s = next((s for (tid, d), s in SCORING.items() if task_id.startswith(tid) and d == design), None)
    if s is None and task is not None:
        f = next((f for (tid, d), f in BUILT.items() if task_id.startswith(tid) and d == design), None)
        s = f(task) if f else None
    if s is None and task is not None:                 # T10-T30: decided from the precedents (scoring_rest.py)
        from benchmark.v6.scoring_rest import scoring_for as rest
        s = rest(task_id, design, task)
    return s


SCORES = (1.0, 0.6, 0.3)


def per_layout(s: dict, lid: str) -> dict:
    """The design's scoring as one layout (seed) sees it: the levels that layout cannot offer (by_layout goal NA)
    left out, ``D`` = 1 when more than one level is open there, else 0.  11-17 (user, over the meeting's "no
    promotion"): the best a seed offers is always the best tier -- with only substitutes there, the best substitute
    scores 1.0 and the rest follow in order (0.6, 0.3); ``raw`` keeps each tier's level by the design, ``top`` the
    raw level of the best one (ideal: the ideal thing is in the scene)."""
    import copy
    tiers = [copy.deepcopy(t) for t in s["tiers"]
             if not (isinstance(t.get("goal"), dict) and t["goal"].get("by_layout", {}).get(lid) == NA)]
    top = LEVEL[tiers[0]["name"]] if tiers else None
    if (s.get("ideal_by_layout") or {}).get(lid) is not None:  # cost_tiers ranks the seed's own totals
        top = "ideal" if s["ideal_by_layout"][lid] else "moderate"
    for i, t in enumerate(tiers):
        t["raw"] = t["name"]
        t["name"], t["score"] = TIER_NAMES[i], SCORES[i]
    out = {**copy.deepcopy(s), "tiers": tiers, "D": 1 if len(tiers) > 1 else 0, "top": top}
    out.pop("D_by_layout", None)
    out.pop("top_by_layout", None)
    out.pop("ideal_by_layout", None)
    return out


def attach_scoring(out: dict) -> int:
    """Copy each reviewed design's scoring onto its layouts (per seed: per_layout); returns how many designs are
    reviewed."""
    import copy
    n = 0
    for t in out["tasks"]:
        for design, info in t["v6_variants"].items():
            s = scoring_for(t["task_id"], design, t)
            if s is None:
                continue
            n += 1
            info["scoring"] = copy.deepcopy(s)
            per = {lid: per_layout(s, lid) for lid in info["layouts"]}
            if any(p["top"] != "ideal" or p["D"] != s["D"] for p in per.values()):
                info["scoring"]["D_by_layout"] = {lid: p["D"] for lid, p in per.items()}
                info["scoring"]["top_by_layout"] = {lid: p["top"] for lid, p in per.items()}
            for lid in info["layouts"]:
                t["variants"][lid]["scoring"] = per[lid]
    return n


def tier_goal(tier: dict, task: dict, layout: str | None):
    g = tier.get("goal")
    if g is None:
        return task["goal"]
    if "by_layout" in g:
        return g["by_layout"][layout]
    if "drop" in g:
        base, kinds = task["goal"], g["drop"]
        out = {"all": [a for a in base.get("all", []) if a[0] not in kinds]}
        if base.get("any"):
            out["any"] = [[a for a in grp if a[0] not in kinds] for grp in base["any"]]
        return out
    return g


def score(scoring: dict | None, task: dict, layout: str | None, holds) -> dict | None:
    """The first tier whose goal holds (``holds(goal) -> bool``), as {tier, score, D}; None if not reviewed."""
    if not scoring:
        return None
    for tier in scoring["tiers"]:
        g = tier_goal(tier, task, layout)
        if g == NA:                                   # the level does not exist in this layout
            continue
        if holds(g):
            return {"tier": tier["name"], "level": LEVEL[tier["name"]], "score": tier["score"], "D": scoring["D"]}
    return {"tier": "not_ok", "level": "else", "score": 0.0, "D": scoring["D"]}


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
    # two tiers: best and worst, or best and second when the lower one is a small slip (a door left open, T07
    # microwave_broken, user 11-11)
    if len(tiers) == 2 and [t.get("name") for t in tiers] not in (["best", "worst"], ["best", "second"]):
        bad.append("two tiers are best and worst (or best and second)")
    if not s.get("not_ok"):
        bad.append("say what does not count (not_ok)")
    return bad


# the not_ok line in Chinese, for SUCCESS_ROUTES_zh.md (success_routes.py)
NOT_OK_ZH = {
    ("T01", "overhang_ready"): "书放在别处（茶几、岛台、台面、地上），或还拿在手里",
    ("T01", "table_seats"): "放到另一张没摆早餐的餐桌；为腾地方挪了或碰倒了餐具；放在别处或还拿在手里",
    ("T01", "which_table"): "放到放玩具的那张桌（找错桌）；挪了或碰倒餐具；放在别处或还拿在手里",
    ("T01", "no_room_fallback"): "挪了或碰倒餐具、麦片腾地方；放在别处或还拿在手里",
    ("T01", "reader_seat"): "挪了或碰倒餐具；放在别处（包括另一张餐桌）或还拿在手里",
    ("T01", "which_book"): "餐桌上一本书都没有；还拿在手里",
    ("T02", "clear"): "没叠上，或积木掉了",
    ("T02", "crowded_use_another"): "碗或擀面杖动了、碗倒了；没叠上",
    ("T02", "third_toy_elsewhere"): "只叠了两层（没找到第三件）；没叠上；塔不在岛台上",
    ("T02", "tower_for_kid"): "只有两块；为腾地方挪了桌上的东西；没叠",
    ("T02", "tower_for_kid_duck"): "只叠了两层；挪了桌上的东西；塔不在餐桌上；没叠上",
    ("T02", "block_put_away"): "只有两层（没有第三件）；没叠上；积木掉了",
    ("T03", "large_only"): "只收了一样；放进柜子、抽屉；还拿着或掉了",
    ("T03", "small_bin_or_bedroom_bin"): "两样不在同一个容器；只收了一样；把小箱子整个放进大箱子；还拿在手里",
    ("T03", "no_bin_substitute"): "两样分在两个容器；只收了一样；放进柜子或抽屉；还拿着或掉了",
    ("T03", "utensils_apart"): "两样不在同一个容器；只收了一样（勺子没找到）；放进柜子、抽屉或随手放桌上；还拿着或掉了",
    ("T04", "cup_available"): "杯子倒着或躺着；放到别的柜子、台面或餐桌；还拿着或掉了",
    ("T04", "no_cup"): "拿果汁瓶等不是杯子的东西顶替；马克杯倒着或躺着；放到别处；没找到杯子；还拿着或掉了",
    ("T04", "clear_the_drinks_spot"): "只拿走一样（硬塞杯子）；推到矮柜另一头；碗倒了；没放杯子或杯子倒着；还拿着或掉了",
    ("T04", "two_guests"): "只摆了一个杯子（没找到第二个）；拿果汁瓶等当第二个；杯子倒着或躺着；放到别处；还拿着或掉了",
    ("T04", "x6_gd_cup_in_cabinets"): "没摆杯子（没找到玻璃杯）；杯子倒着或躺着；放到别处；还拿着或掉了",
    ("T05", "e1_pencil_asked"): "铅笔放到别处；拿了别的东西当笔；还拿着或掉了",
    ("T05", "no_pen_pencil_away"): "没找到铅笔；铅笔放到别处；拿了别的东西当笔；还拿着或掉了",
    ("T05", "check_desk_first"): "书桌上既没有钢笔也没有铅笔；还拿着或掉了",
    ("T05", "all_pens"): "漏了一支或几支（没找全就停了）；笔放到别处；还拿着或掉了",
    ("T05", "homework_ready"): "只拿了笔或只拿了本子；拿泰迪熊等无关东西凑数；放到别处；还拿着或掉了",
    ("T05", "pens_per_notebook"): "拿少了（比作业本少）；笔放到别处；还拿着或掉了",
    ("T05", "errand_combined"): "只做了一件（笔没拿来，或杯子还在书桌上）；杯子倒着或躺着；还拿着或掉了",
    ("T05", "x6_gd_pen_or_pencil_cabinets"): "书桌上什么笔都没有；还拿着或掉了",
    ("T06", "free"): "放到别处（茶几、餐桌、岛台上没动）；还拿着或掉了",
    ("T06", "display_row"): "只摆了两块（第三块没找到）；叠成一摞而不是一排；有积木放到别处；还拿着或掉了",
    ("T06", "display_spot_or_tv"): "挪了或碰倒盒子、瓶子、电视柜上的东西；放到别处（餐桌、茶几等）；还拿着或掉了",
    ("T06", "seen_from_bed"): "没放进卧室（比如留在客厅）；碰倒了孩子的东西；还拿着或掉了",
    ("T07", "microwave_works"): "没热到 40 度；灶或微波炉没关；碗打翻；还拿着或掉了",
    ("T07", "microwave_broken"): "微波炉不热就放弃了（没到 40 度）；灶或微波炉没关；碗打翻；还拿着或掉了",
    ("T07", "microwave_holds_pot"): "汤锅放在地上或打翻；没到 40 度；灶或微波炉没关；碗打翻；还拿着或掉了",
    ("T07", "vessel_decides_appliance"): "用错电器热不起来就放弃了（没到 40 度）；电器没关；容器打翻；还拿着或掉了",
    ("T07", "two_portions"): "结束时有一样不到 40 度（没热或凉了）；电器没关；打翻；还拿着或掉了",
    ("T08", "sponge_on_island"): "没擦或没擦完；海绵还拿着或掉在地上",
    ("T08", "far_sponge_tv"): "没找到海绵（或备用海绵）；没擦或没擦完；海绵还拿着或掉在地上",
    ("T08", "wipe_and_sort"): "还有玩具留在岛台上；没擦或没擦完；碰倒了罐子、杯子、粥或果汁；海绵还拿着或掉在地上",
    ("T08", "return_sponge_home"): "没找到海绵；没擦或没擦完；海绵还拿着或掉在地上",
    ("T08", "which_surface"): "只擦了干净的那张；都没擦；海绵还拿着或掉在地上",
    ("T09", "lid_off"): "只放了一个番茄；没到 60 度；灶台没关火；番茄掉出锅外；还拿着或掉了",
    ("T09", "lid_on_spoon_away"): "只放了一个番茄；没到 60 度；灶台没关火；番茄掉出锅外；还拿着或掉了",
    ("T09", "pot_in_use"): "满锅打翻；只放了一个番茄；没到 60 度；灶台没关火；还拿着或掉了",
    ("T09", "tomato_in_fridge"): "只放了两颗（没找到冰箱里那颗或大番茄）；拿苹果凑数；没到 60 度；灶台没关火；番茄掉出锅外；还拿着或掉了",
    ("T11", "fruit_plate_for_guests"): "什么都没端过去；水果掉了；还拿着",
    ("T10", "trash_moved"): "罐子没进有空位的垃圾桶（压在满桶上、扔进别的箱子或没扔）；还拿着或掉了",
    ("T10", "x6_gd_can_put_away"): "空罐没找到或没扔（只扔了冰箱那罐）；还拿着或掉了",
    ("T09", "x6_gd_tomato_elsewhere"): "只放了一颗（没找到另一颗）；没到 60 度；灶台没关火；番茄掉出锅外；还拿着或掉了",
    ("T09", "pot_in_dining_room"): "用碗或马克杯代替锅；没找到锅；只放了一颗；没到 60 度；灶台没关火；还拿着或掉了",
    ("T03", "which_bin_by_contents"): "两样分在两个箱子；只收了一样；还拿着或掉了",
}


def _rest_not_ok_zh():
    from benchmark.v6.scoring_rest import REST
    for key, spec in REST.items():
        NOT_OK_ZH.setdefault(key, spec["zh"]["no"])


_rest_not_ok_zh()
