# Physics validation to do

* 0 variants are PHYSICS_VALIDATED (10/10 seeds passed in the v5 grid with the current hash and route).
* 1430 episodes remain (1070 of the 107 new variants): `batches/physics_todo.json`; the new variants alone: `batches/physics_v6_new.json`.
* Run: `$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval` (~43 episodes / hour with 2 simulators).
* Order: (1) new variants without a skill dependency (`depends on` -), (2) after each skill fix the variants that depend on it, (3) re-run T11 `h_action_grasp_and_ik` (failure-injection fix 019e517; it passed in the smoke run), (4) the v5 variants below 10/10 after each skill fix.

| task | variant | category | physics now | depends on |
|---|---|---|---|---|
| T01 | overhang_ready | control | 0/0 of 10 | - |
| T01 | table_seats | action_task | 0/0 of 10 | - |
| T01 | which_table | action_task | 0/0 of 10 | - |
| T01 | no_room_fallback | action_task | 0/0 of 10 | - |
| T01 | reader_seat | action_task | 0/0 of 10 | - |
| T01 | homework_on_island | task | 0/0 of 10 | - |
| T02 | clear | control | 0/0 of 10 | - |
| T02 | crowded_use_another | task | 0/0 of 10 | - |
| T02 | third_toy_elsewhere | task | 0/0 of 10 | - |
| T02 | tower_for_kid | task | 0/0 of 10 | - |
| T02 | tower_for_kid_duck | task | 0/0 of 10 | - |
| T02 | block_put_away | action_task | 0/0 of 10 | low cabinet doors |
| T03 | large_only | control | 0/0 of 10 | - |
| T03 | small_bin_or_bedroom_bin | task | 0/0 of 10 | - |
| T03 | which_bin_by_contents | task | 0/0 of 10 | - |
| T03 | no_bin_substitute | task | 0/0 of 10 | - |
| T03 | bin_full | task | 0/0 of 10 | - |
| T04 | cup_available | control | 0/0 of 10 | - |
| T04 | no_cup | task | 0/0 of 10 | - |
| T04 | clear_the_drinks_spot | task | 0/0 of 10 | - |
| T04 | two_guests | task | 0/0 of 10 | - |
| T04 | no_cup_in_cabinets | task | 0/0 of 10 | low cabinet doors |
| T04 | x6_gd_cup_in_cabinets | task | 0/0 of 10 | low cabinet doors |
| T05 | e1_pencil_asked | control | 0/0 of 10 | - |
| T05 | check_desk_first | task | 0/0 of 10 | - |
| T05 | no_pencil | task | 0/0 of 10 | - |
| T05 | pen_in_use | task | 0/0 of 10 | - |
| T05 | pens_for_two | task | 0/0 of 10 | - |
| T05 | homework_ready | task | 0/0 of 10 | - |
| T05 | pens_per_notebook | task | 0/0 of 10 | - |
| T05 | errand_combined | task | 0/0 of 10 | - |
| T05 | x6_gd_pen_or_pencil_cabinets | task | 0/0 of 10 | low cabinet doors |
| T06 | free | control | 0/0 of 10 | - |
| T06 | both_spots_full | task | 0/0 of 10 | - |
| T06 | display_spot_or_tv | task | 0/0 of 10 | - |
| T06 | seen_from_bed | task | 0/0 of 10 | - |
| T07 | microwave_works | control | 0/0 of 10 | - |
| T07 | microwave_broken | task | 0/0 of 10 | - |
| T07 | microwave_holds_pot | task | 0/0 of 10 | - |
| T07 | vessel_decides_appliance | task | 0/0 of 10 | - |
| T07 | two_portions | task | 0/0 of 10 | - |
| T08 | sponge_on_island | control | 0/0 of 10 | wipe reach |
| T08 | far_sponge_tv | task | 0/0 of 10 | wipe reach |
| T08 | wipe_and_sort | task | 0/0 of 10 | wipe reach |
| T08 | return_sponge_home | task | 0/0 of 10 | wipe reach |
| T08 | which_surface | task | 0/0 of 10 | wipe reach |
| T09 | lid_off | control | 0/0 of 10 | - |
| T09 | lid_on_spoon_away | action_task | 0/0 of 10 | - |
| T09 | pot_in_use | task | 0/0 of 10 | - |
| T09 | tomato_in_fridge | action_task | 0/0 of 10 | - |
| T09 | x6_gd_tomato_elsewhere | task | 0/0 of 10 | - |
| T09 | pot_in_dining_room | task | 0/0 of 10 | - |
| T10 | can_on_island | control | 0/0 of 10 | - |
| T10 | can_in_dining_room | task | 0/0 of 10 | - |
| T10 | keep_kids_can | task | 0/0 of 10 | - |
| T10 | trash_moved | task | 0/0 of 10 | - |
| T10 | trash_full | task | 0/0 of 10 | - |
| T10 | after_dinner_clear | task | 0/0 of 10 | - |
| T10 | guests_coming | task | 0/0 of 10 | - |
| T10 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T10 | clear_table_for_dinner | task | 0/0 of 10 | - |
| T11 | fruits_on_table | control | 0/0 of 10 | - |
| T11 | basket_missing | task | 0/0 of 10 | - |
| T11 | no_apple_for_kid | task | 0/0 of 10 | - |
| T11 | fruit_plate_for_guests | task | 0/0 of 10 | - |
| T12 | toys_out | control | 0/0 of 10 | - |
| T12 | bedtime_toy | task | 0/0 of 10 | - |
| T12 | bins_capacity | task | 0/0 of 10 | - |
| T12 | find_all_toys | task | 0/0 of 10 | - |
| T12 | castle_stays | task | 0/0 of 10 | - |
| T12 | his_things_whose | task | 0/0 of 10 | - |
| T12 | his_things_by_kind | task | 0/0 of 10 | - |
| T12 | his_room | task | 0/0 of 10 | - |
| T12 | cup_to_bedside | task | 0/0 of 10 | - |
| T12 | where_his_cup_is | task | 0/0 of 10 | low cabinet doors |
| T13 | dishes_on_tv_stand | control | 0/0 of 10 | - |
| T13 | no_cup | task | 0/0 of 10 | - |
| T13 | copy_the_setting | task | 0/0 of 10 | - |
| T13 | finish_the_table | task | 0/0 of 10 | - |
| T15 | lid_by_pot | control | 0/0 of 10 | - |
| T15 | lid_elsewhere | task | 0/0 of 10 | search of the pot lid |
| T15 | no_lid | task | 0/0 of 10 | - |
| T15 | lid_in_use | task | 0/0 of 10 | - |
| T16 | box_on_counter | control | 0/0 of 10 | - |
| T16 | box_in_cabinet | task | 0/0 of 10 | low cabinet doors |
| T16 | no_box | task | 0/0 of 10 | - |
| T16 | box_in_use | task | 0/0 of 10 | - |
| T17 | lid_off | control | 0/0 of 10 | - |
| T17 | h_task_lid_elsewhere | task | 0/0 of 10 | - |
| T17 | pot_in_use | task | 0/0 of 10 | - |
| T17 | no_pot | task | 0/0 of 10 | low cabinet doors |
| T18 | bowls_in_cabinet | control | 0/0 of 10 | low cabinet doors |
| T18 | bowls_apart | task | 0/0 of 10 | low cabinet doors |
| T18 | one_bowl | task | 0/0 of 10 | low cabinet doors |
| T18 | bowl_in_use | task | 0/0 of 10 | low cabinet doors |
| T18 | no_bowl | task | 0/0 of 10 | low cabinet doors |
| T18 | plate_not_bowl | task | 0/0 of 10 | low cabinet doors |
| T18 | door_stuck | task | 0/0 of 10 | low cabinet doors |
| T19 | bin_on_bookcase | control | 0/0 of 10 | - |
| T19 | lookalike_bin | task | 0/0 of 10 | - |
| T19 | recycle_bin_full | task | 0/0 of 10 | - |
| T19 | bin_out_of_reach | task | 0/0 of 10 | - |
| T20 | bottle_on_cabinet | control | 0/0 of 10 | juice bottle grasp |
| T20 | m_bottle_on_tv_stand | task | 0/0 of 10 | juice bottle grasp |
| T20 | juice_finished | task | 0/0 of 10 | - |
| T20 | juice_in_use | task | 0/0 of 10 | - |
| T20 | x6_gd_bottle_put_away | task | 0/0 of 10 | juice bottle grasp, low cabinet doors |
| T14 | e1_book_ready | control | 0/0 of 10 | - |
| T14 | within_kids_reach | task | 0/0 of 10 | - |
| T14 | kids_shelf_full | task | 0/0 of 10 | - |
| T14 | homework_stays | task | 0/0 of 10 | - |
| T14 | whose_book | task | 0/0 of 10 | - |
| T14 | no_second_red_book | task | 0/0 of 10 | - |
| T14 | next_in_series | task | 0/0 of 10 | - |
| T21 | tissue_on_tv_stand | control | 0/0 of 10 | - |
| T21 | tissue_out_of_view | task | 0/0 of 10 | - |
| T21 | which_table | task | 0/0 of 10 | - |
| T21 | no_tissue | task | 0/0 of 10 | - |
| T21 | tissue_put_away | task | 0/0 of 10 | low cabinet doors |
| T21 | the_kids_side | task | 0/0 of 10 | - |
| T21 | tissue_in_use | task | 0/0 of 10 | - |
| T22 | juice_on_table | control | 0/0 of 10 | - |
| T22 | by_kind | task | 0/0 of 10 | low cabinet doors |
| T22 | eat_now | task | 0/0 of 10 | - |
| T22 | not_shopping | task | 0/0 of 10 | - |
| T22 | two_spots | task | 0/0 of 10 | low cabinet doors |
| T22 | tray_elsewhere | action_task | 0/0 of 10 | - |
| T22 | basket_in_use | task | 0/0 of 10 | - |
| T22 | basket_out_of_reach | task | 0/0 of 10 | - |
| T23 | spoon_on_floor | control | 0/0 of 10 | - |
| T23 | by_kind | task | 0/0 of 10 | - |
| T23 | belongs_on_floor | task | 0/0 of 10 | - |
| T23 | toy_box_full | task | 0/0 of 10 | - |
| T23 | no_toy_box | task | 0/0 of 10 | - |
| T24 | apple_on_table | control | 0/0 of 10 | - |
| T24 | dinner_soon | task | 0/0 of 10 | - |
| T24 | where_is_he | task | 0/0 of 10 | - |
| T24 | apple_in_use | task | 0/0 of 10 | - |
| T24 | apple_on_floor | task | 0/0 of 10 | - |
| T25 | drink_on_island | control | 0/0 of 10 | - |
| T25 | cold_one | task | 0/0 of 10 | - |
| T25 | cups_for_two | task | 0/0 of 10 | low cabinet doors |
| T25 | little_guest | task | 0/0 of 10 | - |
