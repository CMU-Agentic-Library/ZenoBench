# Physics validation to do

* 0 variants are PHYSICS_VALIDATED (10/10 seeds passed in the v5 grid with the current hash and route).
* 1590 episodes remain (1120 of the 112 new variants): `batches/physics_todo.json`; the new variants alone: `batches/physics_v6_new.json`.
* Run: `$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval` (~43 episodes / hour with 2 simulators).
* Order: (1) new variants without a skill dependency (`depends on` -), (2) after each skill fix the variants that depend on it, (3) re-run T11 `h_action_grasp_and_ik` (failure-injection fix 019e517; it passed in the smoke run), (4) the v5 variants below 10/10 after each skill fix.

| task | variant | category | physics now | depends on |
|---|---|---|---|---|
| T01 | overhang_ready | control | 0/0 of 10 | - |
| T01 | table_seats | action_task | 0/0 of 10 | - |
| T01 | which_table | action_task | 0/0 of 10 | - |
| T01 | no_room_fallback | action_task | 0/0 of 10 | - |
| T01 | reader_seat | action_task | 0/0 of 10 | - |
| T01 | which_book | task | 0/0 of 10 | - |
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
| T03 | utensils_apart | task | 0/0 of 10 | - |
| T04 | cup_available | control | 0/0 of 10 | - |
| T04 | no_cup | task | 0/0 of 10 | - |
| T04 | clear_the_drinks_spot | task | 0/0 of 10 | - |
| T04 | two_guests | task | 0/0 of 10 | - |
| T04 | x6_gd_cup_in_cabinets | task | 0/0 of 10 | low cabinet doors |
| T05 | e1_pencil_asked | control | 0/0 of 10 | - |
| T05 | no_pen_pencil_away | task | 0/0 of 10 | - |
| T05 | check_desk_first | task | 0/0 of 10 | - |
| T05 | all_pens | task | 0/0 of 10 | - |
| T05 | homework_ready | task | 0/0 of 10 | - |
| T05 | pens_per_notebook | task | 0/0 of 10 | - |
| T05 | errand_combined | task | 0/0 of 10 | - |
| T05 | x6_gd_pen_or_pencil_cabinets | task | 0/0 of 10 | low cabinet doors |
| T06 | free | control | 0/0 of 10 | - |
| T06 | display_row | task | 0/0 of 10 | - |
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
| T10 | after_dinner_clear | task | 0/0 of 10 | - |
| T10 | guests_coming | task | 0/0 of 10 | - |
| T10 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T11 | fruits_on_table | control | 0/0 of 10 | - |
| T11 | basket_missing | task | 0/0 of 10 | - |
| T11 | leave_one_for_kid | task | 0/0 of 10 | - |
| T11 | fruit_plate_for_guests | task | 0/0 of 10 | - |
| T12 | toys_out | control | 0/0 of 10 | - |
| T12 | duck_in_study | task | 0/0 of 10 | - |
| T12 | toys_everywhere | task | 0/0 of 10 | - |
| T12 | bins_capacity | task | 0/0 of 10 | - |
| T12 | find_all_toys | task | 0/0 of 10 | - |
| T12 | castle_stays | task | 0/0 of 10 | - |
| T13 | dishes_on_tv_stand | control | 0/0 of 10 | - |
| T13 | no_cup | task | 0/0 of 10 | - |
| T13 | copy_the_setting | task | 0/0 of 10 | - |
| T13 | finish_the_table | task | 0/0 of 10 | - |
| T15 | book_free | control | 0/0 of 10 | - |
| T15 | book_out_of_view | task | 0/0 of 10 | - |
| T15 | flip_on_the_shelf | task | 0/0 of 10 | - |
| T16 | pin_free | control | 0/0 of 10 | - |
| T16 | pin_out_of_view | task | 0/0 of 10 | - |
| T16 | everything_near_the_edge | task | 0/0 of 10 | - |
| T17 | lid_off | control | 0/0 of 10 | - |
| T17 | h_task_lid_elsewhere | task | 0/0 of 10 | - |
| T17 | hide_both | task | 0/0 of 10 | - |
| T17 | hide_somewhere | task | 0/0 of 10 | low cabinet doors |
| T18 | at_island | control | 0/0 of 10 | low cabinet doors |
| T18 | dishes_spread | task | 0/0 of 10 | low cabinet doors |
| T18 | enough_for_dinner | task | 0/0 of 10 | low cabinet doors |
| T19 | bin_on_bookcase | control | 0/0 of 10 | - |
| T19 | m_can_in_dining_room | task | 0/0 of 10 | - |
| T19 | lookalike_bin | task | 0/0 of 10 | - |
| T19 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors |
| T20 | bottle_on_cabinet | control | 0/0 of 10 | juice bottle grasp |
| T20 | m_bottle_on_tv_stand | task | 0/0 of 10 | juice bottle grasp |
| T20 | x6_gd_bottle_put_away | task | 0/0 of 10 | juice bottle grasp, low cabinet doors |
| T14 | e1_book_ready | control | 0/0 of 10 | - |
| T14 | within_kids_reach | task | 0/0 of 10 | - |
| T14 | stack_them_stably | task | 0/0 of 10 | - |
| T14 | homework_stays | task | 0/0 of 10 | - |
| T14 | whose_book | task | 0/0 of 10 | - |
| T14 | next_in_series | task | 0/0 of 10 | - |
| T21 | tissue_on_tv_stand | control | 0/0 of 10 | - |
| T21 | tissue_out_of_view | task | 0/0 of 10 | - |
| T21 | which_table | task | 0/0 of 10 | - |
| T21 | no_tissue | task | 0/0 of 10 | - |
| T21 | tissue_put_away | task | 0/0 of 10 | low cabinet doors |
| T21 | the_kids_side | task | 0/0 of 10 | - |
| T22 | juice_on_table | control | 0/0 of 10 | - |
| T22 | by_kind | task | 0/0 of 10 | low cabinet doors |
| T22 | eat_now | task | 0/0 of 10 | - |
| T22 | not_shopping | task | 0/0 of 10 | - |
| T22 | two_spots | task | 0/0 of 10 | low cabinet doors |
| T22 | tray_elsewhere | action_task | 0/0 of 10 | - |
| T23 | spoon_on_floor | control | 0/0 of 10 | - |
| T23 | by_kind | task | 0/0 of 10 | - |
| T23 | belongs_on_floor | task | 0/0 of 10 | - |
| T23 | dropped_out_of_view | task | 0/0 of 10 | - |
| T23 | only_this_room | task | 0/0 of 10 | - |
| T23 | dropped_in_two_rooms | task | 0/0 of 10 | - |
| T24 | apple_on_table | control | 0/0 of 10 | - |
| T24 | no_apples_for_him | task | 0/0 of 10 | - |
| T24 | dinner_soon | task | 0/0 of 10 | - |
| T24 | fruit_out_of_view | task | 0/0 of 10 | - |
| T24 | where_is_he | task | 0/0 of 10 | - |
| T24 | two_kids | task | 0/0 of 10 | - |
| T25 | drink_on_island | control | 0/0 of 10 | - |
| T25 | cup_elsewhere | task | 0/0 of 10 | - |
| T25 | cold_one | task | 0/0 of 10 | - |
| T25 | drink_in_fridge | task | 0/0 of 10 | - |
| T25 | cups_for_two | task | 0/0 of 10 | low cabinet doors |
| T25 | two_guests | task | 0/0 of 10 | - |
| T25 | little_guest | task | 0/0 of 10 | - |
| T26 | car_in_living_room | control | 0/0 of 10 | - |
| T26 | whose | task | 0/0 of 10 | - |
| T26 | scattered | task | 0/0 of 10 | - |
| T26 | where_in_room | task | 0/0 of 10 | - |
| T26 | bear_to_bed | task | 0/0 of 10 | - |
| T26 | two_bedrooms | task | 0/0 of 10 | - |
| T27 | rice_on_table | control | 0/0 of 10 | - |
| T27 | which_is_leftover | task | 0/0 of 10 | - |
| T27 | two_leftovers | task | 0/0 of 10 | - |
| T27 | still_eating | task | 0/0 of 10 | - |
| T27 | fridge_out_of_view | task | 0/0 of 10 | - |
| T27 | fruit_stays_out | task | 0/0 of 10 | - |
| T28 | cup_on_counter | control | 0/0 of 10 | - |
| T28 | cup_put_away | task | 0/0 of 10 | low cabinet doors |
| T28 | which_bed | task | 0/0 of 10 | - |
| T28 | where_his_cup_is | task | 0/0 of 10 | low cabinet doors |
| T28 | cup_out_of_view | task | 0/0 of 10 | - |
| T28 | already_there | task | 0/0 of 10 | - |
| T29 | car_on_table | control | 0/0 of 10 | - |
| T29 | belongs_on_table | task | 0/0 of 10 | - |
| T29 | homework_on_table | task | 0/0 of 10 | - |
| T29 | several | task | 0/0 of 10 | - |
| T29 | nothing_to_clear | task | 0/0 of 10 | - |
| T29 | which_table | task | 0/0 of 10 | - |
| T30 | bowl_on_cabinet | control | 0/0 of 10 | - |
| T30 | how_many | task | 0/0 of 10 | - |
| T30 | bowls_in_cabinet | task | 0/0 of 10 | low cabinet doors |
| T30 | clean_one | task | 0/0 of 10 | - |
| T30 | bowl_put_away | task | 0/0 of 10 | low cabinet doors |
| T30 | no_bowl | task | 0/0 of 10 | - |
| T30 | bowl_not_plate | task | 0/0 of 10 | - |
