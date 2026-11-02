# ZenoBench v5 baseline report (2026-10-31)

Baseline for the physics-fix phase: the full 180 x 10 = 1,800-episode oracle grid with the code and catalog of
tag `v5-baseline-2026-10-31`. Numbers come from `PHYSICS.json` (`validate.py report`, newest valid result per
episode; results from older routes or configuration hashes are ignored). Raw runs: `benchmark/runs/v5_*`
(not in git). Static checks: `STATIC.json`; per-episode table: [VALIDATION.md](VALIDATION.md); capabilities:
[CAPABILITIES.md](CAPABILITIES.md).

## Summary

| | episodes | passed | rate |
|---|---|---|---|
| static configuration checks | 1,800 | 1,800 | 100 % (not physics) |
| physics, all | 1,800 run | **1,032** | 57.3 % |
| Easy | 400 | 269 | 67.3 % |
| Medium | 600 | 374 | 62.3 % |
| Hard | 800 | 389 | 48.6 % |
| Hard / task | 200 | 97 | 48.5 % |
| Hard / action | 200 | 76 | 38.0 % |
| Hard / mixed | 200 | 114 | 57.0 % |
| Hard / dynamic | 200 | 102 | 51.0 % |

Statuses of the 768 not passed: stopped 742 (a skill failed where the route expects success), goal_failed 18,
route_violation 6, failure_not_triggered 2. `passed` = route ran to its end, every expected failure failed,
every declared failure fired and manifested, the GT goal holds, nothing dropped. No goal or physics check was
relaxed; no sticky grasps.

## Why episodes fail

First unexpected failing call of each non-passed episode (`stop_call`), classified by its error text.
About 94 % are low-level physical execution (grasp, slip, reach, articulation, placement), not task design.

| cause | easy | medium | hard | total |
|---|---|---|---|---|
| grasp miss | 42 | 88 | 113 | 243 |
| carry slip | 45 | 57 | 90 | 192 |
| IK / reach | 14 | 24 | 108 | 146 |
| other skill error | 9 | 26 | 23 | 58 |
| placement / manipulation result | 8 | 10 | 22 | 40 |
| articulation | 1 | 1 | 34 | 36 |
| perception / search | 12 | 18 | 3 | 33 |
| goal check (all steps ok) | 0 | 0 | 13 | 13 |
| collateral (object dropped) | 0 | 2 | 3 | 5 |
| failure not triggered | 0 | 0 | 2 | 2 |

## Per task

| task | Easy | Medium | Hard | all | main failures |
|---|---|---|---|---|---|
| T01_book_to_dining_table | 4/20 | 16/30 | 21/40 | 41/90 | carry slip (navigate) 41; other skill error (expose) 5 |
| T02_stack_blocks | 12/20 | 15/30 | 40/40 | 67/90 | grasp miss (separate) 10; grasp miss (pick) 9 |
| T03_utensils_one_container | 20/20 | 22/30 | 29/40 | 71/90 | other skill error (lift) 3; IK / reach (look) 3 |
| T04_cup_or_mug_to_cabinet | 7/20 | 17/30 | 21/40 | 45/90 | carry slip (place) 25; carry slip (navigate) 8 |
| T05_pen_or_pencil_to_desk | 20/20 | 30/30 | 0/40 | 50/90 | grasp miss (open) 26; IK / reach (open) 6 |
| T06_block_destination_occupied | 18/20 | 25/30 | 38/40 | 81/90 | carry slip (place) 6; IK / reach (look) 2 |
| T07_heat_oatmeal | 20/20 | 24/30 | 38/40 | 82/90 | other skill error (pick) 7; placement / manipulation result (place) 1 |
| T08_wipe_island | 13/20 | 4/30 | 0/40 | 17/90 | IK / reach (wipe) 23; carry slip (wipe) 17 |
| T09_tomato_soup | 10/20 | 13/30 | 35/40 | 58/90 | grasp miss (pick) 11; grasp miss (uncover) 9 |
| T10_trash_the_can | 17/20 | 28/30 | 10/40 | 55/90 | IK / reach (approach) 20; IK / reach (pick) 10 |
| T11_collect_fruits | 13/20 | 30/30 | 30/40 | 73/90 | IK / reach (place) 8; carry slip (navigate) 6 |
| T12_tidy_toys | 20/20 | 27/30 | 16/40 | 63/90 | goal check (all steps ok) (-) 7; carry slip (drop) 7 |
| T13_breakfast_setup | 10/20 | 3/30 | 4/40 | 17/90 | grasp miss (pick) 45; carry slip (navigate) 9 |
| T14_shelve_the_book | 0/20 | 4/30 | 4/40 | 8/90 | carry slip (navigate) 43; grasp miss (regrasp) 10 |
| T15_book_face_up | 15/20 | 19/30 | 18/40 | 52/90 | IK / reach (flip) 13; other skill error (flip) 13 |
| T16_rolling_pin_at_edge | 18/20 | 28/30 | 35/40 | 81/90 | placement / manipulation result (place) 4; other skill error (roll) 2 |
| T17_hide_and_seek_block | 10/20 | 9/30 | 16/40 | 35/90 | perception / search (search) 10; grasp miss (uncover) 10 |
| T18_check_cabinet_dishes | 20/20 | 20/30 | 0/40 | 40/90 | articulation (open) 25; grasp miss (open) 15 |
| T19_recycling | 20/20 | 30/30 | 23/40 | 73/90 | IK / reach (drop) 10; grasp miss (pick) 7 |
| T20_juice_back_to_table | 2/20 | 10/30 | 11/40 | 23/90 | grasp miss (pick) 58; articulation (pick) 4 |

Failures concentrate in a few skill problems:

* **T20** juice bottle: the side pinch for tall round objects knocks it off `kitchen_cabinet_6` (grasp miss 58);
  older runs with `top_pinch` passed.
* **T05 / T18 Hard**: opening `kitchen_cabinet_4` / `kitchen_cabinet_6` (no finger contact on the handle,
  joint does not move): every cabinet Hard is 0/10.
* **T13** mug rim pinch misses (45); **T01 / T14** books slip while carrying (41 / 43).
* **T08** wipe: no base pose reaches the strip, sponge slips (17/90).
* **T10** 3 Hards with the can inside the microwave cavity: no grasp reaches it (0/30).
* T06, T07, T16, T11, T19, T03, T02 Hard are stable (>= 75 %).

## Variants by seeds passed

| variant pass count | easy | medium | hard | total |
|---|---|---|---|---|
| 10/10 | 17 | 21 | 21 | 59 |
| 8-9/10 | 7 | 11 | 11 | 29 |
| 5-7/10 | 4 | 8 | 7 | 19 |
| 0-4/10 | 12 | 20 | 41 | 73 |

**10/10** (59): `T02/clear`, `T02/edge_base`, `T02/h_action_grasp_and_ik`, `T02/h_dynamic_base_moved_to_edge`, `T02/h_mixed_edge_base_grasp`, `T02/m_grasp_b`, `T03/e2_from_dining_room`, `T03/h_mixed_three_containers_ik`, `T03/large_only`, `T03/m_grasp_spoon`, `T03/small_and_large`, `T05/e1_pencil_asked`, `T05/e2_pencil_asked_far`, `T05/m_grasp_pencil`, `T05/no_pen`, `T05/no_pen_pencil_away`, `T06/display_hidden`, `T06/h_action_slip_and_ik`, `T06/h_mixed_hidden_grasp`, `T07/e2_from_dining_room`, `T07/h_dynamic_door_opened`, `T07/h_mixed_pot_inside_grasp`, `T07/m_ik_oatmeal`, `T07/microwave_broken`, `T07/microwave_holds_pot`, `T07/microwave_works`, `T09/h_dynamic_spoon_taken`, `T09/lid_off`, `T10/can_in_dining_room`, `T10/h_dynamic_can_moved`, `T11/basket_gone_bowl_there`, `T11/basket_missing`, `T11/fruits_on_table`, `T11/h_dynamic_basket_taken`, `T11/h_mixed_bowl_there_grasp`, `T11/m_grasp_apple`, `T11/m_ik_basket`, `T12/e2_from_kitchen`, `T12/m_ik_duck_place`, `T12/toys_out`, `T16/h_mixed_bowl_behind_ik`, `T16/h_task_bowl_behind`, `T16/m_ik_roll`, `T16/pin_free`, `T16/pin_out_of_view`, `T17/lid_off`, `T18/at_island`, `T18/e2_from_dining_room`, `T18/m_ik_close`, `T18/m_ik_open`, `T19/bin_on_bookcase`, `T19/e2_from_kitchen`, `T19/h_mixed_lookalike_ik`, `T19/lookalike_bin`, `T19/m_can_in_dining_room`, `T19/m_grasp_can`, `T19/m_ik_cube`, `T20/h_dynamic_bottle_taken`, `T20/m_bottle_on_tv_stand`

**8-9/10** (29): `T01/h_dynamic_pushed_back` 8, `T01/h_mixed_table_set_ik` 9, `T03/three_containers` 9, `T04/h_task_spot_taken` 9, `T04/no_cup_mug_away` 9, `T06/e2_from_dining_room` 9, `T06/free` 9, `T06/h_dynamic_cabinet_filled` 8, `T06/m_slip_block` 8, `T06/occupied` 9, `T06/occupied_block_away` 8, `T07/h_action_ik_and_slip` 8, `T09/cookware_choice` 8, `T09/h_action_grasp_and_ik` 9, `T09/h_mixed_cookware_grasp` 8, `T09/m_grasp_spoon` 8, `T10/can_on_island` 9, `T10/e2_from_dining_room` 8, `T10/far_can_far` 9, `T10/m_ik_can` 9, `T12/duck_in_study` 8, `T12/m_grasp_car` 9, `T13/dishes_on_tv_stand` 8, `T15/book_free` 9, `T15/h_mixed_block_on_book_ik` 8, `T15/m_ik_flip` 9, `T16/e2_from_dining_room` 8, `T16/h_action_ik_twice` 9, `T16/m_start_dining_away` 8

**5-7/10** (19): `T01/far_no_overhang` 5, `T01/m_ik_pick` 5, `T01/no_overhang` 6, `T03/h_action_slip_and_miss` 6, `T04/cup_available` 6, `T04/h_mixed_spot_taken_ik` 6, `T04/no_cup` 5, `T08/e2_from_dining_room` 6, `T08/sponge_on_island` 7, `T09/lid_on` 5, `T12/h_mixed_everywhere_ik` 6, `T15/book_out_of_view` 5, `T15/e2_from_dining_room` 6, `T15/h_action_ik_twice` 5, `T15/m_start_dining_away` 5, `T16/h_dynamic_bowl_put_behind` 6, `T17/h_action_ik_twice` 7, `T17/h_task_lid_elsewhere` 5, `T17/lid_on` 5

**0-4/10** (73): `T01/e2_from_dining_room` 3, `T01/h_action_ik_pick_and_place` 4, `T01/overhang_ready` 1, `T01/table_set` 0, `T02/crowded` 4, `T02/e2_from_wall_cabinet` 2, `T02/far_crowded` 1, `T03/far_small_and_large` 2, `T03/h_dynamic_pin_taken` 4, `T04/e2_from_dining_room` 1, `T04/h_action_ik_and_grasp` 2, `T04/h_dynamic_cup_taken` 4, `T04/m_ik_cup` 3, `T05/h_action_grasp_and_ik` 0, `T05/h_dynamic_pencil_taken` 0, `T05/h_mixed_cabinet_ik` 0, `T05/h_task_pencil_in_cabinet` 0, `T07/broken_oatmeal_away` 4, `T08/far_sponge_tv` 1, `T08/h_action_grasp_and_ik` 0, `T08/h_dynamic_sponge_taken` 0, `T08/h_mixed_cluttered_grasp` 0, `T08/island_cluttered` 0, `T08/m_grasp_sponge` 3, `T08/sponge_on_tv_stand` 0, `T09/e2_from_dining_room` 0, `T09/lid_on_spoon_away` 0, `T10/h_action_ik_pick_and_drop` 0, `T10/h_mixed_microwave_ik` 0, `T10/h_task_can_in_microwave` 0, `T11/e2_from_kitchen` 3, `T11/h_action_grasp_and_ik` 0, `T12/h_action_grasp_and_ik` 3, `T12/h_dynamic_duck_taken` 4, `T12/toys_everywhere` 3, `T13/bowl_on_cabinet` 3, `T13/e2_from_kitchen` 2, `T13/h_action_ik_and_grasp` 0, `T13/h_dynamic_mug_taken` 4, `T13/h_mixed_boxed_in_ik` 0, `T13/no_cup` 0, `T13/no_cup_bowl_on_cabinet` 0, `T13/no_cup_spoon_boxed_in` 0, `T14/book_on_desk` 2, `T14/e1_book_ready` 0, `T14/e2_book_ready_far` 0, `T14/h_action_ik_pick_and_place` 0, `T14/h_dynamic_shelf_taken` 1, `T14/h_mixed_shelf_taken_ik` 3, `T14/m_ik_pick` 2, `T14/m_ik_place` 0, `T14/shelf_taken` 0, `T15/h_dynamic_book_moved` 2, `T15/h_task_block_on_book` 3, `T17/block_crowded` 2, `T17/e2_from_dining_room` 0, `T17/h_dynamic_lid_put_on` 1, `T17/h_mixed_lid_elsewhere_ik` 3, `T17/lid_on_crowded` 2, `T18/h_action_ik_open_and_close` 0, `T18/h_dynamic_door_closed` 0, `T18/h_mixed_two_cabinets_ik` 0, `T18/h_task_two_cabinets` 0, `T18/m_door_left_open` 0, `T19/h_action_grasp_and_miss` 3, `T19/h_dynamic_cube_moved` 0, `T20/bottle_on_cabinet` 2, `T20/e2_from_bedroom_hall` 0, `T20/h_action_ik_pick_and_place` 0, `T20/h_mixed_table_full_ik` 1, `T20/m_ik_pick` 0, `T20/m_ik_place` 0, `T20/table_full` 0


## Recovery capability coverage (formal set, from `capabilities.py`)

AF 129 variants / 20 tasks, DR 30 / 11, GD 15 / 6, SR 14 / 4, CL 9 / 5, PP 13 / 5. AF split: task-level fallback
(v4 explore / alternative / fallback decision, substitute object, or search / explore recovery) 67 (Hard 32),
local retry 62 (Hard 35). Hard categories: action / mixed / dynamic 20 each, all with injected failures;
task 20 (7 injected, 13 constraint-only). 38 of 40 Easy variants have no condition or failure.

## Changes in this round (after the grid)

* `T06 free`: pot lid spawned on the rim (inside-pot spawn threw it off the stove), FREEZE amendment.
* `T13 h_dynamic_mug_taken`: bowl hint 3 cm nearer (route only).
* `T18 m_ik_close`: library `knock` on the re-closed door (skill coverage 60).
* `ik_twice` Hards (T15/T16/T17): the second injected IK refusal was off by one (`after_fired` gates the count,
  `nth` 2 hit the third attempt): 0/30 -> 21/30 after `nth` 1, FREEZE amendment. Semantics unchanged.
* `validate.py report` keeps the newest valid result per episode; `capabilities.py` reports the AF split.

## Handoff for the physics-fix phase

Plan (user-approved): fix one low-level class per commit in the order T20 bottle grasp -> T05/T18 cabinet
doors -> T13 mug -> T01/T14 book carry -> T08 / T10; check representative seeds, then all affected
variants x 10 seeds, then a regression batch on the stable tasks. Do not change goals, tier definitions,
failure-injection semantics or success checks; record scene-config changes as FREEZE amendments (the catalog
test fails otherwise). The final formal set keeps a variant only if all 10 seeds pass (no per-seed
selection), Hard as the majority (fixes plus new task-level Hards on the stable tasks); this full 180-variant
result stays the reported baseline. Keep the DR / GD / SR / CL / PP variants when trimming.

Diagnostics that worked:

* `result.json` `initial_positions` vs the scene annotation (> 5 cm: displaced at reset, not a route bug).
* Episode log `pick_target`: `pos` (live object) far from `p` (planned pinch), or z on the floor, means the
  object was knocked over before the grasp.
* Rerun a subset: `validate.py batch --variants T/V ... --out b.json`, then `run_episode.py --batch b.json
  --jobs 2` (2 sims at once, ~43 episodes / hour); `validate.py report --runs <all v5 run dirs>`.

## Remaining limitations

* Oracle physics is not yet all-pass (above); per-seed jitter is small and there is one house.
* T10 cavity Hards are unsolvable with the current skills; cabinet Hards need the door skill fixed.
* The evaluation pipeline (12 metrics) has not been run on v5 episodes (the grid used `--no-eval`).
* The Open-Skill track is validated on the example skills only (`skill_ext/examples`).
* Code changes outside `benchmark/v5`: `run_episode.py` (`--track`, failure injection), `scene.py` (far-start
  spawn), `env_service/worker.py` (2 lines), one teammate-skill edit (`zeno_skills/policies/tooluse.py` wipe
  edge fallback). No scene, USD, annotation or asset changes.
