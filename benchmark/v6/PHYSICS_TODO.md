# Physics validation to do

* 0 variants are PHYSICS_VALIDATED (10/10 seeds passed in the v5 grid with the current hash and route).
* 1280 episodes remain (440 of the 44 new variants): `batches/physics_todo.json`; the new variants alone: `batches/physics_v6_new.json`.
* Run: `$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval` (~43 episodes / hour with 2 simulators).
* Order: (1) new variants without a skill dependency (`depends on` -), (2) after each skill fix the variants that depend on it, (3) re-run T11 `h_action_grasp_and_ik` (failure-injection fix 019e517; it passed in the smoke run), (4) the v5 variants below 10/10 after each skill fix.

| task | variant | category | physics now | depends on |
|---|---|---|---|---|
| T01 | overhang_ready | control | 0/0 of 10 | - |
| T01 | no_overhang | action | 0/0 of 10 | - |
| T01 | table_seats | task | 0/0 of 10 | - |
| T01 | seat_slot_blocked | action_task | 0/0 of 10 | - |
| T01 | which_table | action_task | 0/0 of 10 | - |
| T01 | x6_dr_block_on_book__block | action | 0/0 of 10 | - |
| T01 | x6_dr_block_on_book__sponge | action | 0/0 of 10 | - |
| T02 | clear | control | 0/0 of 10 | - |
| T02 | crowded | action | 0/0 of 10 | - |
| T02 | edge_base | action | 0/0 of 10 | - |
| T02 | third_toy_elsewhere | task | 0/0 of 10 | - |
| T02 | tower_for_kid | task | 0/0 of 10 | - |
| T02 | tower_for_kid_duck | task | 0/0 of 10 | - |
| T02 | block_put_away | action_task | 0/0 of 10 | low cabinet doors |
| T03 | large_only | control | 0/0 of 10 | - |
| T03 | far_small_and_large | task | 0/0 of 10 | - |
| T03 | h_dynamic_pin_taken | task | 0/0 of 10 | - |
| T03 | mug_or_bedroom_bin | task | 0/0 of 10 | - |
| T03 | three_containers_bedroom | task | 0/0 of 10 | - |
| T04 | cup_available | control | 0/0 of 10 | - |
| T04 | no_cup | task | 0/0 of 10 | - |
| T04 | no_cup_mug_away | task | 0/0 of 10 | - |
| T04 | h_task_spot_taken | task | 0/0 of 10 | - |
| T04 | x6_gd_cup_in_cabinets | task | 0/0 of 10 | low cabinet doors |
| T04 | x6_dr_spot_filled_dynamic__bowl | task | 0/0 of 10 | - |
| T04 | x6_dr_spot_filled_dynamic__block | task | 0/0 of 10 | - |
| T04 | cup_taken_mug_in_living_room | task | 0/0 of 10 | - |
| T05 | e1_pencil_asked | control | 0/0 of 10 | - |
| T05 | no_pen_pencil_away | task | 0/0 of 10 | - |
| T05 | h_task_pencil_in_cabinet | action_task | 0/0 of 10 | low cabinet doors |
| T05 | h_dynamic_pencil_taken | action_task | 0/0 of 10 | low cabinet doors |
| T05 | x6_gd_pencil_other_cabinet | task | 0/0 of 10 | low cabinet doors |
| T05 | x6_gd_pen_or_pencil_cabinets | task | 0/0 of 10 | low cabinet doors |
| T06 | free | control | 0/0 of 10 | - |
| T06 | occupied | task | 0/0 of 10 | - |
| T06 | occupied_block_away | task | 0/0 of 10 | - |
| T06 | display_hidden | task | 0/0 of 10 | - |
| T06 | h_dynamic_cabinet_filled | task | 0/0 of 10 | - |
| T06 | x6_gd_two_displays_event | task | 0/0 of 10 | - |
| T07 | microwave_works | control | 0/0 of 10 | - |
| T07 | microwave_broken | task | 0/0 of 10 | - |
| T07 | broken_oatmeal_away | task | 0/0 of 10 | - |
| T07 | microwave_holds_pot | task | 0/0 of 10 | - |
| T07 | h_dynamic_door_opened | action_task | 0/0 of 10 | - |
| T07 | x6_sr_microwave_taken | task | 0/0 of 10 | - |
| T07 | x6_pp_door_opened_after_heat | action | 0/0 of 10 | - |
| T08 | sponge_on_island | control | 0/0 of 10 | wipe reach |
| T08 | sponge_on_tv_stand | task | 0/0 of 10 | wipe reach |
| T08 | far_sponge_tv | task | 0/0 of 10 | wipe reach |
| T08 | island_cluttered | action | 0/0 of 10 | wipe reach |
| T08 | h_dynamic_sponge_taken | action_task | 0/0 of 10 | wipe reach |
| T08 | x6_pp_sponge_taken_after_wipe | task | 0/0 of 10 | wipe reach |
| T09 | lid_off | control | 0/0 of 10 | - |
| T09 | lid_on | action | 0/0 of 10 | - |
| T09 | lid_on_spoon_away | action_task | 0/0 of 10 | - |
| T09 | h_dynamic_spoon_taken | task | 0/0 of 10 | - |
| T09 | x6_gd_tomato_elsewhere | task | 0/0 of 10 | - |
| T09 | x6_pp_lid_taken_after_stir | task | 0/0 of 10 | search of the pot lid |
| T09 | x6_pp_tomato_taken_out__tomato2 | action | 0/0 of 10 | - |
| T09 | x6_pp_tomato_taken_out__tomato1 | action | 0/0 of 10 | - |
| T09 | x6_pp_tomato_taken_out__tomato2_after_stir | action | 0/0 of 10 | - |
| T09 | pot_in_dining_room | task | 0/0 of 10 | - |
| T10 | can_on_island | control | 0/0 of 10 | - |
| T10 | can_in_dining_room | task | 0/0 of 10 | - |
| T10 | far_can_far | task | 0/0 of 10 | - |
| T10 | h_task_can_in_microwave | action | 0/0 of 10 | pick from the microwave cavity |
| T10 | h_dynamic_can_moved | action_task | 0/0 of 10 | pick from the microwave cavity |
| T10 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T11 | fruits_on_table | control | 0/0 of 10 | - |
| T11 | basket_missing | task | 0/0 of 10 | - |
| T11 | basket_gone_bowl_there | task | 0/0 of 10 | - |
| T11 | h_dynamic_basket_taken | task | 0/0 of 10 | - |
| T11 | x6_gd_fruits_event | task | 0/0 of 10 | - |
| T12 | toys_out | control | 0/0 of 10 | - |
| T12 | duck_in_study | task | 0/0 of 10 | - |
| T12 | toys_everywhere | task | 0/0 of 10 | - |
| T12 | h_dynamic_duck_taken | task | 0/0 of 10 | - |
| T12 | x6_gd_bins_capacity | task | 0/0 of 10 | - |
| T12 | x6_pp_duck_moved | task | 0/0 of 10 | - |
| T13 | dishes_on_tv_stand | control | 0/0 of 10 | - |
| T13 | no_cup | task | 0/0 of 10 | - |
| T13 | bowl_on_cabinet | task | 0/0 of 10 | - |
| T13 | no_cup_bowl_on_cabinet | task | 0/0 of 10 | - |
| T13 | no_cup_spoon_boxed_in | action_task | 0/0 of 10 | - |
| T13 | h_dynamic_mug_taken | action_task | 0/0 of 10 | - |
| T13 | x6_pp_spoon_moved__early | action | 0/0 of 10 | - |
| T13 | x6_pp_spoon_moved__table_end | action | 0/0 of 10 | - |
| T13 | x6_pp_spoon_moved__tv_stand | task | 0/0 of 10 | - |
| T13 | x6_gd_bowl_put_away | task | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T13 | x6_gd_two_settings | task | 0/0 of 10 | - |
| T15 | book_free | control | 0/0 of 10 | - |
| T15 | book_out_of_view | task | 0/0 of 10 | - |
| T15 | h_task_block_on_book | action | 0/0 of 10 | - |
| T15 | h_dynamic_book_moved | action | 0/0 of 10 | - |
| T16 | pin_free | control | 0/0 of 10 | - |
| T16 | pin_out_of_view | task | 0/0 of 10 | - |
| T16 | h_task_bowl_behind | action | 0/0 of 10 | - |
| T16 | h_dynamic_bowl_put_behind | action | 0/0 of 10 | - |
| T17 | lid_off | control | 0/0 of 10 | - |
| T17 | lid_on | action | 0/0 of 10 | - |
| T17 | block_crowded | action | 0/0 of 10 | - |
| T17 | lid_on_crowded | action | 0/0 of 10 | - |
| T17 | h_task_lid_elsewhere | task | 0/0 of 10 | - |
| T17 | h_dynamic_lid_put_on | action_task | 0/0 of 10 | - |
| T17 | x6_pp_lid_lifted | task | 0/0 of 10 | search of the pot lid |
| T17 | x6_gd_hide_both_event | task | 0/0 of 10 | - |
| T18 | at_island | control | 0/0 of 10 | low cabinet doors |
| T18 | m_door_left_open | action | 0/0 of 10 | low cabinet doors |
| T18 | h_task_two_cabinets | task | 0/0 of 10 | low cabinet doors |
| T18 | h_dynamic_door_closed | action_task | 0/0 of 10 | low cabinet doors |
| T18 | x6_gd_bowl_elsewhere__two_places | task | 0/0 of 10 | low cabinet doors |
| T18 | x6_gd_bowl_elsewhere__three_places | task | 0/0 of 10 | low cabinet doors |
| T18 | x6_pp_door_reopened | action | 0/0 of 10 | low cabinet doors |
| T19 | bin_on_bookcase | control | 0/0 of 10 | - |
| T19 | m_can_in_dining_room | task | 0/0 of 10 | - |
| T19 | lookalike_bin | task | 0/0 of 10 | - |
| T19 | h_dynamic_cube_moved | task | 0/0 of 10 | - |
| T19 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors |
| T20 | bottle_on_cabinet | control | 0/0 of 10 | juice bottle grasp |
| T20 | m_bottle_on_tv_stand | task | 0/0 of 10 | juice bottle grasp |
| T20 | table_full | action | 0/0 of 10 | juice bottle grasp |
| T20 | h_dynamic_bottle_taken | action_task | 0/0 of 10 | juice bottle grasp |
| T20 | x6_gd_bottle_put_away | task | 0/0 of 10 | juice bottle grasp, low cabinet doors |
| T14 | e1_book_ready | control | 0/0 of 10 | - |
| T14 | book_on_desk | action | 0/0 of 10 | - |
| T14 | shelf_taken | action | 0/0 of 10 | - |
| T14 | h_dynamic_shelf_taken | action | 0/0 of 10 | - |
| T14 | x6_gd_book_put_away | task | 0/0 of 10 | low cabinet doors |
