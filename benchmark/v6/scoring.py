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
    # T03 large_only (control): the wide bin on the TV stand is the only open container
    ("T03", "large_only"): only("the rolling pin and the spoon both in the wide bin",
                                "one left out, put in a cabinet or drawer instead, still held or dropped"),
    # T03 utensils_apart: the spoon out of view in another room, the wide bin in the bedroom the only open
    # container; carrying the bin over first is fine (the goal only asks for the contents)
    ("T03", "utensils_apart"): only("the rolling pin and the spoon both in the wide bin, the hand empty",
                                    "one left out (the spoon not found); in a cabinet, drawer or on a table; "
                                    "still held or dropped"),
    # T04 cup_available (control): a glass cup and a mug side by side on the island; a mug is a cup too (no_cup
    # tests the mug as the stand-in), so either one, or both, is the task done
    ("T04", "cup_available"): only("the glass cup or a mug upright on the low cabinet's drinks corner, the hand empty",
                                   "lying or upside down; on another cabinet, counter or table; still held or dropped"),
    # T04 no_cup: no glass cup; the mug (island, TV stand or dining table) or any other mug in the house
    ("T04", "no_cup"): only("any mug upright on the drinks corner, the hand empty (the detour is SPL's business)",
                            "a non-cup (the juice bottle) instead; lying or upside down; elsewhere; no cup found; "
                            "still held or dropped"),
    # T05 e1_pencil_asked (control): the pen removed, the pencil on the bedroom bookcase
    ("T05", "e1_pencil_asked"): only("the pencil on the study desk, the hand empty",
                                     "the pencil elsewhere; something else brought instead; still held or dropped"),
    # T05 no_pen_pencil_away: no pen, the pencil on the dining table out of view; a search, no substitution
    ("T05", "no_pen_pencil_away"): only("the pencil on the study desk, the hand empty",
                                        "the pencil not found; left elsewhere; something else brought instead; "
                                        "still held or dropped"),
    # T05 all_pens: 2-4 pens and pencils over the house, the count unstated; missing one is the task not done.
    # Something else brought along does not cost
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


# T02 block_put_away: two blocks on the island (A 5 mm over the edge, no base), the third in one of two closed
# low cabinets; the instruction asks to close the doors after the search
BLOCK_PUT_AWAY = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "three blocks in one tower on the island, the base 5 cm from the edge, both cabinet doors closed"},
    {"name": "second", "score": 0.6, "goal": {"drop": ["away_from_edge"]},
     "why": "the tower done and the doors closed, but on the edge (block A used as the base where it lay)"},
    {"name": "worst", "score": 0.3, "goal": {"drop": ["away_from_edge", "is_closed"]},
     "why": "the tower done, but a cabinet door left open (the instruction asks to close them)"}],
    "not_ok": "two blocks only (the third not found); no stack; a block dropped"}
SCORING[("T02", "block_put_away")] = BLOCK_PUT_AWAY

# T03 small_bin_or_bedroom_bin: a small bin (two toy blocks in it) that holds the spoon but not the 22 cm rolling
# pin, near or beside the wide bin in the bedroom.  ``inside`` is lenient (the centre within the rim, at most 3 cm
# above it): a pin slanted into the small bin can count, one lying across its rim with its centre too high
# cannot; the mug never counts (user 11-11)
_P, _S, _W, _SB = "rolling_pin", "breakfast_spoon", "wide_storage_bin", "small_storage_bin"
_BLOCKS_IN = [["inside", "small_bin_block_1", _SB], ["inside", "small_bin_block_2", _SB]]
SCORING[("T03", "small_bin_or_bedroom_bin")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "both in the wide bin in the bedroom, the small bin's blocks untouched"},
    {"name": "second", "score": 0.6,
     "goal": {"all": [["inside", _P, _SB], ["inside", _S, _SB], *_BLOCKS_IN, ["hand_empty", "right"]]},
     "why": "both in the small bin (the pin slanted in, sticking out), its blocks still in it: put away after a "
            "fashion"},
    {"name": "worst", "score": 0.3,
     "goal": {"all": [["hand_empty", "right"]],
              "any": [[["inside", _P, _W], ["inside", _S, _W]], [["inside", _P, _SB], ["inside", _S, _SB]]]},
     "why": "both in one bin, but the small bin's blocks taken out or moved"}],
    "not_ok": "the spoon and the pin in different containers; in the mug; one left out; the small bin itself put "
              "into the wide one; still held"}


# T03 which_bin_by_contents: two wide bins of one make, the toy bin (toy_storage_bin, two blocks) and the kitchen
# bin (wide_storage_bin, two spoons).  The wrong bin with nothing disturbed is the worst tier (user 11-11);
# carrying the kitchen bin over and filling it there is the best tier (the goal only asks for the contents)
_TOY = "toy_storage_bin"
_WHICH_KEPT = [["inside", "toy_bin_block_1", _TOY], ["inside", "toy_bin_block_2", _TOY],
               ["inside", "spoon_counter", _W], ["inside", "spoon_side_table", _W]]
SCORING[("T03", "which_bin_by_contents")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "both in the kitchen bin, the toys and the spoons left where they were"},
    {"name": "second", "score": 0.6,
     "goal": {"all": [["inside", _P, _W], ["inside", _S, _W], ["hand_empty", "right"]]},
     "why": "both in the kitchen bin, but a block or a spoon taken out or moved to another bin"},
    {"name": "worst", "score": 0.3,
     "goal": {"all": [["inside", _P, _TOY], ["inside", _S, _TOY], *_WHICH_KEPT, ["hand_empty", "right"]]},
     "why": "both in the toy bin (the wrong bin, not looked into), nothing disturbed"}],
    "not_ok": "the toy bin with its contents disturbed; the two in different bins; one left out; still held or "
              "dropped"}


def _no_bin_substitute(task: dict) -> dict:
    """T03 no_bin_substitute: no wide bin; the substitute (basket or tray, seed) in another room; the small bin
    (two blocks) holds the pin only slanted; the fruit basket holds an apple and an orange.  The fruit basket,
    fruit in it or taken out, is the worst tier (user 11-11)."""
    lays = task["v6_variants"]["no_bin_substitute"]["layouts"]
    both = lambda c: [["inside", _P, c], ["inside", _S, c]]
    fruit = [["inside", "apple", "fruit_basket"], ["inside", "orange", "fruit_basket"]]
    second, worst = {}, {}
    for lid in lays:
        x = next(a[2] for a in task["variants"][lid]["goal"]["all"] if a[:2] == ["inside", _P])
        second[lid] = {"all": [["hand_empty", "right"]],
                       "any": [both(x), both(_SB) + [["inside", "small_bin_block_1", _SB],
                                                     ["inside", "small_bin_block_2", _SB]] + fruit]}
        worst[lid] = {"all": [["hand_empty", "right"]], "any": [both(_SB), both("fruit_basket")]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "both in the substitute (basket or tray), the fruit and the small bin's blocks untouched"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "both in the substitute but the fruit or the blocks disturbed; or both in the small bin (the pin "
                "slanted in), its blocks still in it, the fruit untouched"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "both in the small bin with its blocks taken out (or the fruit disturbed); or both in the fruit "
                "basket, with the fruit in it or taken out"}],
        "not_ok": "the two in different containers; one left out; in a cabinet or drawer; still held or dropped"}

# T04 clear_the_drinks_spot: the oatmeal bowl and the pot lid fill the drinks spot; tidy them to the kitchen and set
# out a cup.  Off the cabinet but outside the kitchen is the worst tier (user 11-11).  For now the fridge and the
# kitchen cabinets' insides are not kitchen spots in the goal (they fall to the worst tier)
_SPOT = "kitchen_cabinet_6/top"
_CUP_ON_SPOT = [[["on", x, _SPOT], ["upright", x]]
                for x in ("cup_counter_b", "mug", "mug_dining_cabinet", "mug_shelf", "mug_counter")]
SCORING[("T04", "clear_the_drinks_spot")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "the bowl and the lid back in the kitchen (island, stove or a counter), the bowl upright, a cup upright "
            "on the drinks spot"},
    {"name": "worst", "score": 0.3,
     "goal": {"all": [["not on", "oatmeal", _SPOT], ["not on", "pot_lid", _SPOT], ["upright", "oatmeal"],
                      ["hand_empty", "right"]], "any": _CUP_ON_SPOT},
     "why": "the spot cleared and a cup set out, but the bowl or the lid left outside the kitchen (the dining "
            "table, the coffee table, another cabinet)"}],
    "not_ok": "only one of the two taken off the cabinet (the cup squeezed in); pushed aside on the cabinet; the "
              "bowl tipped; no cup set out, or lying; still held or dropped"}

# T04 two_guests: one glass cup (island), the mug in another room; any two of the cup and the mugs count (two mugs
# too, user 11-11).  Touching or closer than 3 cm, against "not touching each other", is the worst tier
SCORING[("T04", "two_guests")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "two cups (the glass cup and a mug, or two mugs) upright on the drinks spot, at least 3 cm apart"},
    {"name": "worst", "score": 0.3, "goal": {"drop": ["clear_of"]},
     "why": "two cups upright on the spot, but touching or closer than 3 cm (the instruction says apart)"}],
    "not_ok": "one cup only (the second not found); a non-cup (the juice bottle) for the second; lying or upside "
              "down; elsewhere; still held or dropped"}

# T04 x6_gd_cup_in_cabinets: a cup without a handle asked for, the glass cup in one of two closed low cabinets, the
# mug in plain view.  A door left open is the second tier, the mug (a handle) the worst (user 11-11)
SCORING[("T04", "x6_gd_cup_in_cabinets")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "the glass cup upright on the drinks spot, both cabinet doors closed"},
    {"name": "second", "score": 0.6, "goal": {"drop": ["is_closed"]},
     "why": "the glass cup upright on the spot, but a cabinet door left open"},
    {"name": "worst", "score": 0.3,
     "goal": {"all": [["hand_empty", "right"]], "any": [g for g in _CUP_ON_SPOT if g[0][1] != "cup_counter_b"]},
     "why": "a mug (with a handle) set out instead: the visible substitute ended the search"}],
    "not_ok": "no cup set out (the glass cup not found); lying or upside down; elsewhere; still held or dropped"}

# T05 check_desk_first: a pen asked for; on the desk the pen already (stop) or only a pencil (fetch the pen).
# Extra moves are the second tier; the pencil left standing in for the pen the worst (user 11-11)
SCORING[("T05", "check_desk_first")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "the pen on the desk, nothing else moved: stopped at once when the pen was there, fetched it when only "
            "the pencil was"},
    {"name": "second", "score": 0.6, "goal": {"all": [["on", "pen", "desk_1/top"], ["hand_empty", "right"]]},
     "why": "the pen on the desk, but wasted moves: the pen shifted, the pencil taken away, moved or brought too"},
    {"name": "worst", "score": 0.3, "goal": {"all": [["on", "pencil", "desk_1/top"], ["hand_empty", "right"]]},
     "why": "no pen on the desk, the pencil there in its place (stopped at the pencil)"}],
    "not_ok": "neither the pen nor the pencil on the desk; still held or dropped"}


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
SCORING[("T05", "errand_combined")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "the pen on the desk, the mug upright on a kitchen counter"},
    {"name": "second", "score": 0.6,
     "goal": {"all": [["on", "pen", _DESK], ["on_any", _MUG, ["kitchen_island/top", "kitchen_stove/top",
                                                               "kitchen_counter_1/top", "kitchen_counter_2/top"]],
                      ["upright", _MUG], ["hand_empty", "right"]]},
     "why": "the pen on the desk, the mug upright in the kitchen but not on a counter (the island or the stove)"},
    {"name": "worst", "score": 0.3,
     "goal": {"all": [["not on", _MUG, _DESK], ["upright", _MUG], ["hand_empty", "right"]],
              "any": [[["on", "pen", _DESK]], [["on", "pencil", _DESK]]]},
     "why": "the mug taken off the desk but left outside the kitchen; or the pencil brought for the pen"}],
    "not_ok": "one errand only (no pen or pencil on the desk, or the mug still on it); the mug lying; still held or "
              "dropped"}

# T05 x6_gd_pen_or_pencil_cabinets: a pen asked for, a pencil in one closed low cabinet and the pen in the other.  A
# door left open or the pencil brought along is the second tier; the pencil for the pen the worst (user 11-11)
_CLOSED = [["is_closed", "kitchen_cabinet_6"], ["is_closed", "kitchen_cabinet_4"]]
SCORING[("T05", "x6_gd_pen_or_pencil_cabinets")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0,
     "goal": {"all": [["on", "pen", _DESK], ["not on", "pencil", _DESK], *_CLOSED, ["hand_empty", "right"]]},
     "why": "the pen on the desk, the pencil left behind, both cabinet doors closed"},
    {"name": "second", "score": 0.6, "goal": {"all": [["on", "pen", _DESK], ["hand_empty", "right"]]},
     "why": "the pen on the desk, but a cabinet door left open or the pencil brought along too"},
    {"name": "worst", "score": 0.3, "goal": {"all": [["on", "pencil", _DESK], ["hand_empty", "right"]]},
     "why": "only the pencil on the desk (the pencil for the pen), doors open or closed"}],
    "not_ok": "no pen or pencil on the desk; still held or dropped"}

# T06 display_row: three blocks in a row on the low cabinet, squared, at the front, apart.  Not squared is the
# second tier; touching or at the back (squared or not) the worst (user 11-11)
SCORING[("T06", "display_row")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "all three on the cabinet, squared to its edge, at the front, at least 3 cm apart"},
    {"name": "second", "score": 0.6, "goal": {"drop": ["squared"]},
     "why": "all three at the front and apart, but one or more askew"},
    {"name": "worst", "score": 0.3, "goal": {"drop": ["squared", "front_visible", "clear_of"]},
     "why": "all three on the cabinet, but touching or at the back"}],
    "not_ok": "two blocks only (the third not found); stacked instead of a row; a block elsewhere; still held or "
              "dropped"}


def _display_spot_or_tv(task: dict) -> dict:
    """T06 display_spot_or_tv: the boxes and the bottle on the low cabinet, along the back (front_free*: the cabinet
    front is the spot) or in the front row (front_taken*: the TV stand or the other low cabinet).  front_free with the
    block elsewhere in view is the second tier (no second tier for front_taken: its best is already the fallback);
    the block on one of the three but hidden or at the edge, the worst (user 11-11)."""
    lays = task["v6_variants"]["display_spot_or_tv"]["layouts"]
    A, sups = "wooden_block_a", ("kitchen_cabinet_6/top", "tv_stand_2/top", "kitchen_cabinet_4/top")
    second, worst = {}, {}
    for lid in lays:
        g = task["variants"][lid]["goal"]
        stay = [a for a in g["all"] if a[0] in ("near_start", "upright", "hand_empty")]
        shown = lambda sup: [["on", A, sup], ["front_visible", A], ["away_from_edge", A, 0.02]]  # noqa: E731
        second[lid] = g if g.get("any") else {"all": stay, "any": [shown(sups[1]), shown(sups[2])]}
        worst[lid] = {"all": stay, "any": [[["on", A, sup]] for sup in sups]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "front free: on the cabinet front in view; front taken: on the TV stand or the other low cabinet in "
                "view; 2 cm from the edge, the boxes and the bottle untouched"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "front free: on the TV stand or the other low cabinet in view, the preferred cabinet front unused"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "on one of the three, the boxes untouched, but hidden from the room (behind the boxes) or at the edge"}],
        "not_ok": "a box or the bottle moved or tipped; elsewhere (dining table, coffee table); still held or dropped"}


def _seen_from_bed(task: dict) -> dict:
    """T06 seen_from_bed: the block on the bedside bookcase where the kid sees it from the pillow, the kid's cereal
    boxes (middle or corner) left standing.  Moving the boxes (not forbidden) or another bedroom surface in view is
    the second tier; on the bookcase hidden behind the boxes the worst (user 11-11)."""
    lays = task["v6_variants"]["seen_from_bed"]["layouts"]
    second, worst = {}, {}
    for lid in lays:
        g = task["variants"][lid]["goal"]["all"]
        on = next(a for a in g if a[0] == "on")
        vis = next(a for a in g if a[0] == "visible_from")
        upright = [a for a in g if a[0] == "upright"]
        kept = [a for a in g if a[0] == "near_start"] + upright
        hand = [["hand_empty", "right"]]
        second[lid] = {"all": hand, "any": [[on, vis, *upright], [vis, *kept]]}
        worst[lid] = {"all": [on, *kept, *hand]}
    return {"D": 1, "tiers": [
        {"name": "best", "score": 1.0, "goal": None,
         "why": "on the bedside bookcase in view of the pillow, the boxes untouched"},
        {"name": "second", "score": 0.6, "goal": {"by_layout": second},
         "why": "in view of the pillow, but the boxes moved to make room (still standing), or on another bedroom "
                "surface the kid sees, the boxes untouched"},
        {"name": "worst", "score": 0.3, "goal": {"by_layout": worst},
         "why": "on the bedside bookcase, the boxes untouched, but hidden behind them"}],
        "not_ok": "out of the kid's sight elsewhere (left in the living room); a box tipped; still held or dropped"}

# T07 microwave_works: the microwave works and the oatmeal's bowl suits it; the stove heats it too.  Heating on the
# stove (in part or whole) is the second tier, as is the microwave door left open; both, the worst.  The stove left
# on is not ok (user 11-11).  heated_by: episode.heat_log
_HOT = [["temperature_at_least", "oatmeal", 40], ["not heating", "kitchen_stove"], ["hand_empty", "right"]]
_NO_STOVE = ["not heated_by", "oatmeal", "kitchen_stove", 0.5]
SCORING[("T07", "microwave_works")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": {"all": [*_HOT, ["is_closed", "kitchen_microwave"], _NO_STOVE]},
     "why": "warmed to 40 C in the microwave only, the stove off, the microwave door closed"},
    {"name": "second", "score": 0.6,
     "goal": {"all": _HOT, "any": [[["is_closed", "kitchen_microwave"]], [_NO_STOVE]]},
     "why": "warmed on the stove (in part or whole) though the microwave works, the stove off; or in the microwave "
            "with its door left open"},
    {"name": "worst", "score": 0.3, "goal": {"all": _HOT},
     "why": "warmed partly on the stove and the microwave door left open"}],
    "not_ok": "below 40 C; the stove left on; the bowl tipped; still held or dropped"}

# T07 microwave_broken: the microwave does not heat, the stove is the way (no cost for it).  The microwave door
# left open after trying it is the second tier, 0.6 as elsewhere (user 11-11)
SCORING[("T07", "microwave_broken")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "warmed to 40 C on the stove, the stove off, the microwave door closed"},
    {"name": "second", "score": 0.6, "goal": {"drop": ["is_closed"]},
     "why": "warmed on the stove and switched off, but the microwave door left open after trying it"}],
    "not_ok": "gave up after the microwave failed (below 40 C); the stove left on; the bowl tipped; still held or "
              "dropped"}

# T07 microwave_holds_pot: the soup pot fills the microwave, both burners free.  Taking the pot out and using the
# microwave, or leaving it and using the stove, are both best; the microwave door left open the second tier; the
# pot on the floor not ok (user 11-11)
SCORING[("T07", "microwave_holds_pot")] = {"D": 1, "tiers": [
    {"name": "best", "score": 1.0, "goal": None,
     "why": "warmed to 40 C, in the microwave after taking the pot out or on the stove with the pot left in; the "
            "stove off, the microwave door closed, the pot not on the floor"},
    {"name": "second", "score": 0.6, "goal": {"drop": ["is_closed"]},
     "why": "warmed either way, but the microwave door left open"}],
    "not_ok": "the pot put on the floor; below 40 C; the stove left on; the bowl tipped; still held or dropped"}


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
# T08 far_sponge_tv: the sponge on the TV stand or the dining table, found first; tiers as the control (back where it
# was found is elsewhere too: the instruction says the island)
SCORING[("T08", "far_sponge_tv")] = {**SCORING[("T08", "sponge_on_island")],
                                     "not_ok": "the sponge not found; not wiped (or not all of it); the sponge still "
                                               "held or dropped on the floor"}

# designs whose tiers are built from their layouts' goals
BUILT = {("T02", "tower_for_kid"): _tower_for_kid("tower_for_kid"),
         ("T02", "tower_for_kid_duck"): _tower_for_kid("tower_for_kid_duck"),
         ("T02", "third_toy_elsewhere"): _third_toy_elsewhere, ("T02", "crowded_use_another"): _crowded_use_another, ("T01", "no_room_fallback"): _no_room_fallback, ("T01", "reader_seat"): _reader_seat,
         ("T03", "no_bin_substitute"): _no_bin_substitute,
         ("T05", "homework_ready"): _homework_ready,
         ("T06", "display_spot_or_tv"): _display_spot_or_tv,
         ("T06", "seen_from_bed"): _seen_from_bed,
         ("T07", "vessel_decides_appliance"): _vessel_decides_appliance}


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
    ("T01", "which_book"): "客人那本没到餐桌（拿错或没拿）；还拿在手里",
    ("T02", "clear"): "没叠上，或积木掉了",
    ("T02", "crowded_use_another"): "碗或擀面杖动了、碗倒了；没叠上",
    ("T02", "third_toy_elsewhere"): "只叠了两层（没找到第三件）；没叠上；塔不在岛台上",
    ("T02", "tower_for_kid"): "只叠了两块（没找齐）；挪了桌上的东西；塔不在餐桌上；没叠上",
    ("T02", "tower_for_kid_duck"): "只叠了两层；挪了桌上的东西；塔不在餐桌上；没叠上",
    ("T02", "block_put_away"): "只叠了两块（没找到第三块）；没叠上；积木掉了",
    ("T03", "large_only"): "只收了一样；放进柜子、抽屉；还拿着或掉了",
    ("T03", "small_bin_or_bedroom_bin"): "两样不在同一个容器；插进马克杯；只收了一样；把小箱子整个放进大箱子；还拿在手里",
    ("T03", "no_bin_substitute"): "两样分在两个容器；只收了一样；放进柜子或抽屉；还拿着或掉了",
    ("T03", "utensils_apart"): "只收了一样（勺子没找到）；放进柜子、抽屉或随手放桌上；还拿着或掉了",
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
    ("T06", "display_spot_or_tv"): "挪了或碰倒盒子、瓶子；放到别处（餐桌、茶几等）；还拿着或掉了",
    ("T06", "seen_from_bed"): "放在别处、从床上看不见（比如留在客厅）；碰倒了盒子；还拿着或掉了",
    ("T07", "microwave_works"): "没热到 40 度；灶台没关火；碗打翻；还拿着或掉了",
    ("T07", "microwave_broken"): "微波炉不热就放弃了（没到 40 度）；灶台没关火；碗打翻；还拿着或掉了",
    ("T07", "microwave_holds_pot"): "汤锅放在地上；没到 40 度；灶台没关火；碗打翻；还拿着或掉了",
    ("T07", "vessel_decides_appliance"): "用错电器热不起来就放弃了（没到 40 度）；电器没关；容器打翻；还拿着或掉了",
    ("T07", "two_portions"): "结束时有一样不到 40 度（没热或凉了）；电器没关；打翻；还拿着或掉了",
    ("T08", "sponge_on_island"): "没擦或没擦完；海绵还拿着或掉在地上",
    ("T08", "far_sponge_tv"): "没找到海绵；没擦或没擦完；海绵还拿着或掉在地上",
    ("T03", "which_bin_by_contents"): "放进玩具箱且动了里面的积木或勺子；两样分在两个箱子；只收了一样；还拿着或掉了",
}
