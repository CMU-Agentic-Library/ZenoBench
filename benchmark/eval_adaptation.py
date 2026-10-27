"""Proactive adaptation opportunities of the v4 Hard variants (protocol metric PASR), evaluation side only.

Like eval_semantics.py, the planner never sees this file.  Each entry is one pre-registered,
observable opportunity per episode: the constraint is in the scene from the start and can be seen
before any call fails.  It says what state change shows that the planner adapted, never which
skills it must call:

  moved         a successful call that names one of these objects moves it (> 1 cm or a new support):
                the obstacle / anchor / occupant was dealt with
  objects,      a successful call that names one of the objects puts it on / into one of the
  destinations  destinations (logged support or a measured Contract postcondition): the resource that
                fits was chosen
  local         what must hold at the end for the adaptation to count: "goal" (every final goal atom)
                or [predicate, subject] pairs looked up in the logged goal rows

The adaptation is proactive when it happens before the first execution or precondition failure of
the episode (observation refusals do not count as failures here).  Variants not listed here but with a
registered substitute condition (eval_semantics.substitute) are opportunities too; the substitute's
selection is their adaptation.
"""

from __future__ import annotations

CAB = "kitchen_cabinet_6/top"
TV = "tv_stand_2/top"
ISLAND_ITEMS = ["rolling_pin", "wooden_block_a", "soda_can", "wooden_block_b", "mug", "oatmeal",
                "paperback_book", "breakfast_spoon", "juice_bottle"]
PARTY_ITEMS = ["buffet_tray_1", "buffet_tray_2", "party_plate_3", "party_plate_4", "party_plate_5", "buffet_tray_6",
               "buffet_tray_7", "party_plate_8", "party_plate_9", "party_plate_10", "buffet_tray_11",
               "buffet_tray_12", "party_bowl_1", "party_bowl_2", "party_bowl_3", "party_bowl_4"]

ADAPTATION = {
    # spot_quality: the first placement already respects the place settings
    ("T01_book_to_dining_table", "table_set"): {
        "objects": ["paperback_book"], "destinations": ["dining_table_2/top"],
        "local": [["on", "paperback_book"], ["clear_of", "paperback_book"], ["near_any", "paperback_book"]]},
    # unstable_base: block A (at the edge) is moved in or stacked on B instead of being the base
    ("T02_stack_blocks", "edge_base"): {"moved": ["wooden_block_a"], "local": "goal"},
    # joint_capacity: the first item goes into a container other than the small bin
    ("T03_utensils_one_container", "three_containers"): {
        "objects": ["rolling_pin", "breakfast_spoon"], "destinations": ["wide_storage_bin", "mug"], "local": "goal"},
    # spot_quality: the first placement of a block is a visible display spot
    ("T06_block_destination_occupied", "display_hidden"): {
        "objects": ["wooden_block_a", "wooden_block_b"], "destinations": [CAB, TV], "local": "goal"},
    # appliance_occupied: the stove instead of the taken microwave, or the microwave cleared first
    ("T07_heat_oatmeal", "microwave_holds_pot"): {
        "objects": ["oatmeal"], "destinations": ["kitchen_stove/top"], "moved": ["handled_cooking_pot"],
        "local": "goal"},
    # surface_cluttered: an object on the island is moved before the wipe
    ("T08_wipe_island", "island_cluttered"): {"moved": ISLAND_ITEMS, "local": "goal"},
    # cookware_choice: the tomatoes go into the pot
    ("T09_tomato_soup", "cookware_choice"): {
        "objects": ["cherry_tomato_1", "cherry_tomato_2"], "destinations": ["handled_cooking_pot"], "local": "goal"},
    # decoy_destination: the apple goes onto the allowed tray, not into the bowl at the basket's place
    ("T11_collect_fruits", "basket_gone_bowl_there"): {
        "objects": ["apple"], "destinations": ["serving_tray"], "local": "goal"},
    # joint_capacity: the car goes to the tray (the small bin only has room for the duck)
    ("T12_tidy_toys", "toys_everywhere"): {"objects": ["toy_car"], "destinations": ["toy_tray"], "local": "goal"},
    # anchor_boxed_in (+ no_cup): the spoon is moved to where the setting fits
    ("T13_breakfast_setup", "no_cup_spoon_boxed_in"): {"moved": ["spoon"], "local": "goal"},
    # destination_full: an occupant of the shelf is moved before the book is placed
    ("T14_shelve_the_book", "shelf_taken"): {
        "moved": ["mug_shelf", "shelf_blocker"], "local": [["on", "book_red"]]},
    # decoy_destination: the items go into the instructed bin, not the look-alike toy bin
    ("T19_recycling", "lookalike_bin"): {
        "objects": ["soda_can", "foam_cube"], "destinations": ["wide_storage_bin"], "local": "goal"},
    # destination_full: a few party items are moved to make room for the bottle
    ("T20_juice_back_to_table", "table_full"): {"moved": PARTY_ITEMS, "local": "goal"},
}


def adaptation_for(task_id, variant, extra=None):
    """The registered opportunity of a (task, variant), or None (``extra`` overrides, e.g. candidates)."""
    if extra and (task_id, variant) in extra:
        return extra[(task_id, variant)]
    return ADAPTATION.get((task_id, variant))
