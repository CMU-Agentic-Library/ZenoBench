"""Instruction semantics of the alternatives (EVALUATION_SPEC.md 2.3), evaluation side only.

The planner never sees this file: neither the session, the observation gate nor
run_episode imports it.  It says which goal branch (``goal.any`` group) or
method each option of a task is, which option the instruction prefers and when
a non-preferred option is allowed.  The GT start state of the episode decides
"allowed" (an object removed from the episode is absent); what the planner had
observed plays no part, so "not yet seen" never counts as "absent".

Per task:
  kind       prefer  - "a cup; if there is no cup, a mug": the substitute only when ``allowed_if_absent`` holds
             either  - the instruction allows every option ("on the cabinet or on the TV stand")
             fit     - "one container that fits": any option that physically satisfies the goal
  options    name -> {"groups": [goal.any indices]}  and/or  {"calls": [[verb, arg value]]} (a method: the
             option is used when such a call succeeded); "commit": [[verb, arg value]] = a successful call
             that shows the planner chose this option, even if the episode then failed
  preferred  the option the instruction names first (prefer only)
  substitute condition (tasks.json condition_registry name) -> the options that are the legal substitute when
             the variant has that condition: these variants form the FSR denominator
"""

from __future__ import annotations

CAB = "KitchenCabinetFactory_7025538_spawn_asset_6631478/top"
TV = "TVStandFactory_6305370_spawn_asset_6627927/surface_1"

SEMANTICS = {
    "T02_stack_blocks": {
        "kind": "either",
        "options": {"b_on_a": {"groups": [0]}, "a_on_b": {"groups": [1]}},
        "substitute": {},
    },
    "T03_utensils_one_container": {
        "kind": "fit",
        "options": {"storage_bin": {"groups": [0], "commit": [["place", "wide_storage_bin"], ["drop", "wide_storage_bin"]]},
                    "mug": {"groups": [1], "commit": [["place", "mug"], ["drop", "mug"]]}},
        "substitute": {"small_container_present": ["storage_bin"]},
    },
    "T04_cup_or_mug_to_cabinet": {
        "kind": "prefer", "preferred": "cup",
        "options": {"cup": {"groups": [0], "commit": [["pick", "cup_counter_b"]]},
                    "mug": {"groups": [1], "commit": [["pick", "mug"]], "allowed_if_absent": ["cup_counter_b"]}},
        "substitute": {"no_cup": ["mug"]},
    },
    "T05_pen_or_pencil_to_desk": {
        "kind": "prefer", "preferred": "pen",
        "options": {"pen": {"groups": [0], "commit": [["pick", "pen"]]},
                    "pencil": {"groups": [1], "commit": [["pick", "pencil"]], "allowed_if_absent": ["pen"]}},
        "substitute": {"no_pen": ["pencil"]},
    },
    "T06_block_destination_occupied": {
        "kind": "either",
        "options": {"cabinet": {"groups": [0, 2], "commit": [["place", CAB]]},
                    "tv_stand": {"groups": [1, 3], "commit": [["place", TV]]}},
        "substitute": {"destination_occupied": ["tv_stand"]},
    },
    "T07_heat_oatmeal": {
        "kind": "either",
        "options": {"microwave": {"calls": [["heat", "kitchen_microwave"]]},
                    "stove": {"calls": [["heat", "kitchen_stove"]], "commit": [["place", "kitchen_stove/top"],
                                                                                 ["heat", "kitchen_stove"]]}},
        "substitute": {"microwave_broken": ["stove"]},
    },
    "T11_collect_fruits": {
        "kind": "prefer", "preferred": "basket",
        "options": {"basket": {"groups": [0], "commit": [["place", "fruit_basket"], ["drop", "fruit_basket"]]},
                    "tray": {"groups": [1], "commit": [["place", "serving_tray"], ["drop", "serving_tray"]],
                             "allowed_if_absent": ["fruit_basket"]}},
        "substitute": {"container_absent": ["tray"]},
    },
    "T13_breakfast_setup": {
        "kind": "prefer", "preferred": "cup",
        "options": {"cup": {"groups": [0], "commit": [["pick", "cup"]]},
                    "mug": {"groups": [1], "commit": [["pick", "mug"]], "allowed_if_absent": ["cup"]}},
        "substitute": {"no_cup": ["mug"]},
    },
}


def semantics_for(task_id, extra=None):
    """The entry for a task (``extra`` overrides, e.g. candidate tasks); None = no alternatives declared."""
    if extra and task_id in extra:
        return extra[task_id]
    return SEMANTICS.get(task_id)
