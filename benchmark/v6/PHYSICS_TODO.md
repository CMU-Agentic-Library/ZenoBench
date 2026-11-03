# Physics validation to do

* 31 variants are PHYSICS_VALIDATED (10/10 seeds passed in the v5 grid with the current hash and route).
* 1650 episodes remain (580 of the 58 new variants): `batches/physics_todo.json`; the new variants alone: `batches/physics_v6_new.json`.
* Run: `$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval` (~43 episodes / hour with 2 simulators).
* Order: (1) new variants without a skill dependency (`depends on` -), (2) after each skill fix the variants that depend on it, (3) re-run T11 `h_action_grasp_and_ik` (failure-injection fix 019e517; it passed in the smoke run), (4) the v5 variants below 10/10 after each skill fix.

| task | variant | category | physics now | depends on |
|---|---|---|---|---|
| T01 | overhang_ready | control | 1/10 of 10 | - |
| T01 | e2_from_dining_room | control | 3/10 of 10 | - |
| T01 | no_overhang | action | 6/10 of 10 | - |
| T01 | far_no_overhang | action_task | 5/10 of 10 | - |
| T01 | table_set | task | 0/10 of 10 | - |
| T01 | h_action_ik_pick_and_place | task | 0/0 of 10 | - |
| T01 | h_dynamic_pushed_back | task | 8/10 of 10 | - |
| T01 | x6_sr_two_hand_carry | task | 0/0 of 10 | bimanual flat pick (long side along an overhanging edge) |
| T01 | x6_dr_block_on_book__block | action | 0/0 of 10 | - |
| T01 | x6_dr_block_on_book__sponge | action | 0/0 of 10 | - |
| T02 | e2_from_wall_cabinet | control | 2/10 of 10 | - |
| T02 | crowded | action | 4/10 of 10 | - |
| T02 | far_crowded | action_task | 1/10 of 10 | - |
| T02 | h_action_grasp_and_ik | action | 0/0 of 10 | - |
| T02 | x6_cl_base_a_unreachable | task | 0/0 of 10 | - |
| T02 | x6_cl_block_b_unholdable__grasp | task | 0/0 of 10 | - |
| T02 | x6_cl_block_b_unholdable__ik | task | 0/0 of 10 | - |
| T02 | x6_gd_tower_with_event | action_task | 0/0 of 10 | - |
| T03 | far_small_and_large | task | 2/10 of 10 | - |
| T03 | three_containers | task | 9/10 of 10 | - |
| T03 | h_action_slip_and_miss | task | 0/0 of 10 | - |
| T03 | h_dynamic_pin_taken | task | 2/5 of 10 | - |
| T04 | cup_available | control | 6/10 of 10 | - |
| T04 | e2_from_dining_room | control | 1/10 of 10 | - |
| T04 | no_cup | task | 5/10 of 10 | - |
| T04 | no_cup_mug_away | task | 4/5 of 10 | - |
| T04 | h_task_spot_taken | task | 9/10 of 10 | - |
| T04 | h_action_ik_and_grasp | task | 0/0 of 10 | - |
| T04 | h_mixed_spot_taken_ik | task | 0/0 of 10 | - |
| T04 | h_dynamic_cup_taken | task | 4/10 of 10 | - |
| T04 | x6_gd_cup_in_cabinets | task | 0/0 of 10 | low cabinet doors |
| T04 | x6_cl_cup_unusable__slip | task | 0/0 of 10 | - |
| T04 | x6_cl_cup_unusable__ik_mug_away | task | 0/0 of 10 | - |
| T04 | x6_dr_spot_filled_dynamic__bowl | task | 0/0 of 10 | - |
| T04 | x6_dr_spot_filled_dynamic__block | task | 0/0 of 10 | - |
| T05 | m_grasp_pencil | task | 0/0 of 10 | - |
| T05 | h_task_pencil_in_cabinet | action_task | 0/10 of 10 | low cabinet doors |
| T05 | h_mixed_cabinet_ik | action_task | 0/0 of 10 | low cabinet doors |
| T05 | h_dynamic_pencil_taken | action_task | 0/5 of 10 | low cabinet doors |
| T05 | x6_cl_pen_unholdable | task | 0/0 of 10 | - |
| T05 | x6_gd_pencil_other_cabinet | task | 0/0 of 10 | low cabinet doors |
| T05 | x6_gd_pen_or_pencil_cabinets | task | 0/0 of 10 | low cabinet doors |
| T06 | free | control | 9/10 of 10 | - |
| T06 | e2_from_dining_room | control | 9/10 of 10 | - |
| T06 | occupied | task | 9/10 of 10 | - |
| T06 | occupied_block_away | task | 3/5 of 10 | - |
| T06 | h_action_slip_and_ik | task | 0/0 of 10 | - |
| T06 | h_dynamic_cabinet_filled | task | 8/10 of 10 | - |
| T06 | x6_cl_block_a_unholdable | task | 0/0 of 10 | - |
| T06 | x6_cl_cabinet_unreachable | task | 0/0 of 10 | - |
| T06 | x6_gd_two_displays_event | task | 0/0 of 10 | - |
| T07 | broken_oatmeal_away | task | 2/5 of 10 | - |
| T07 | h_action_ik_and_slip | task | 0/0 of 10 | - |
| T07 | h_mixed_pot_inside_grasp | task | 0/0 of 10 | - |
| T07 | x6_cl_microwave_door_stuck | task | 0/0 of 10 | - |
| T07 | x6_sr_microwave_taken | task | 0/0 of 10 | - |
| T07 | x6_pp_door_opened_after_heat | task | 0/0 of 10 | - |
| T08 | sponge_on_island | control | 7/10 of 10 | wipe reach |
| T08 | e2_from_dining_room | control | 6/10 of 10 | wipe reach |
| T08 | sponge_on_tv_stand | task | 0/10 of 10 | wipe reach |
| T08 | far_sponge_tv | task | 0/5 of 10 | wipe reach |
| T08 | island_cluttered | action | 0/10 of 10 | wipe reach |
| T08 | h_action_grasp_and_ik | action_task | 0/0 of 10 | wipe reach |
| T08 | h_dynamic_sponge_taken | action_task | 0/5 of 10 | wipe reach |
| T08 | x6_cl_sponge_behind_mug | action_task | 0/0 of 10 | wipe reach |
| T08 | x6_pp_sponge_taken_after_wipe | task | 0/0 of 10 | wipe reach |
| T09 | e2_from_dining_room | control | 0/10 of 10 | - |
| T09 | lid_on | action | 5/10 of 10 | - |
| T09 | lid_on_spoon_away | action_task | 0/5 of 10 | - |
| T09 | cookware_choice | task | 8/10 of 10 | - |
| T09 | h_action_grasp_and_ik | task | 0/0 of 10 | - |
| T09 | h_dynamic_spoon_taken | task | 5/5 of 10 | - |
| T09 | x6_cl_spoon_unholdable__spoon_cabinet | task | 0/0 of 10 | - |
| T09 | x6_cl_spoon_unholdable__spoon_dining | task | 0/0 of 10 | - |
| T09 | x6_sr_collect_refused | task | 0/0 of 10 | - |
| T09 | x6_gd_tomato_elsewhere | task | 0/0 of 10 | - |
| T09 | x6_pp_lid_taken_after_stir | task | 0/0 of 10 | search of the pot lid |
| T09 | x6_pp_tomato_taken_out__tomato2 | task | 0/0 of 10 | - |
| T09 | x6_pp_tomato_taken_out__tomato1 | task | 0/0 of 10 | - |
| T09 | x6_pp_tomato_taken_out__tomato2_after_stir | task | 0/0 of 10 | - |
| T10 | can_on_island | control | 9/10 of 10 | - |
| T10 | e2_from_dining_room | control | 8/10 of 10 | - |
| T10 | can_in_dining_room | task | 5/5 of 10 | - |
| T10 | far_can_far | task | 5/5 of 10 | - |
| T10 | h_task_can_in_microwave | action | 0/10 of 10 | pick from the microwave cavity |
| T10 | h_mixed_microwave_ik | action | 0/0 of 10 | pick from the microwave cavity |
| T10 | h_dynamic_can_moved | action_task | 5/5 of 10 | pick from the microwave cavity |
| T10 | x6_cl_can_behind_bottle | action | 0/0 of 10 | juice bottle grasp |
| T10 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T10 | x6_sr_drop_refused | task | 0/0 of 10 | - |
| T11 | e2_from_kitchen | control | 3/10 of 10 | - |
| T11 | h_action_grasp_and_ik | task | 0/0 of 10 | - ; failure-injection fix 019e517 (pinned IK block) |
| T11 | h_mixed_bowl_there_grasp | task | 0/0 of 10 | - |
| T11 | x6_gd_fruits_event | task | 0/0 of 10 | - |
| T11 | x6_cl_apple_rolls_out | task | 0/0 of 10 | - |
| T12 | duck_in_study | task | 5/5 of 10 | - |
| T12 | toys_everywhere | task | 1/5 of 10 | - |
| T12 | h_action_grasp_and_ik | task | 0/0 of 10 | - |
| T12 | h_dynamic_duck_taken | task | 1/5 of 10 | - |
| T12 | x6_gd_bins_capacity | task | 0/0 of 10 | - |
| T12 | x6_cl_basket_unreachable | task | 0/0 of 10 | - |
| T12 | x6_pp_duck_moved | task | 0/0 of 10 | - |
| T13 | dishes_on_tv_stand | control | 8/10 of 10 | - |
| T13 | e2_from_kitchen | control | 2/10 of 10 | - |
| T13 | no_cup | task | 0/10 of 10 | - |
| T13 | bowl_on_cabinet | task | 3/5 of 10 | - |
| T13 | no_cup_bowl_on_cabinet | task | 0/5 of 10 | - |
| T13 | no_cup_spoon_boxed_in | action_task | 0/10 of 10 | - |
| T13 | h_action_ik_and_grasp | task | 0/0 of 10 | - |
| T13 | h_mixed_boxed_in_ik | action_task | 0/0 of 10 | - |
| T13 | h_dynamic_mug_taken | action_task | 2/5 of 10 | - |
| T13 | x6_cl_cup_slips | task | 0/0 of 10 | - |
| T13 | x6_pp_spoon_moved__early | task | 0/0 of 10 | - |
| T13 | x6_pp_spoon_moved__table_end | task | 0/0 of 10 | - |
| T13 | x6_pp_spoon_moved__tv_stand | task | 0/0 of 10 | - |
| T13 | x6_gd_bowl_put_away | task | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T13 | x6_gd_two_settings | task | 0/0 of 10 | - |
| T15 | book_free | control | 9/10 of 10 | - |
| T15 | e2_from_dining_room | control | 6/10 of 10 | - |
| T15 | book_out_of_view | task | 5/10 of 10 | - |
| T15 | m_start_dining_away | task | 5/10 of 10 | - |
| T15 | h_task_block_on_book | action | 3/10 of 10 | - |
| T15 | h_dynamic_book_moved | action_task | 2/10 of 10 | - |
| T16 | e2_from_dining_room | control | 8/10 of 10 | - |
| T16 | m_start_dining_away | task | 8/10 of 10 | - |
| T16 | h_dynamic_bowl_put_behind | task | 6/10 of 10 | - |
| T17 | e2_from_dining_room | control | 0/10 of 10 | search of the pot lid |
| T17 | lid_on | action | 5/10 of 10 | - |
| T17 | block_crowded | action | 2/10 of 10 | - |
| T17 | lid_on_crowded | action | 2/10 of 10 | - |
| T17 | h_task_lid_elsewhere | task | 5/10 of 10 | - |
| T17 | h_dynamic_lid_put_on | task | 1/10 of 10 | - |
| T17 | x6_sr_hide_refused | task | 0/0 of 10 | - |
| T17 | x6_pp_lid_lifted | task | 0/0 of 10 | search of the pot lid |
| T17 | x6_gd_hide_both_event | task | 0/0 of 10 | - |
| T18 | m_door_left_open | action | 0/10 of 10 | low cabinet doors |
| T18 | h_task_two_cabinets | task | 0/10 of 10 | low cabinet doors |
| T18 | h_dynamic_door_closed | task | 0/10 of 10 | low cabinet doors |
| T18 | x6_gd_bowl_elsewhere__two_places | task | 0/0 of 10 | low cabinet doors |
| T18 | x6_gd_bowl_elsewhere__three_places | task | 0/0 of 10 | low cabinet doors |
| T18 | x6_pp_door_reopened | task | 0/0 of 10 | low cabinet doors |
| T19 | m_can_in_dining_room | task | 5/5 of 10 | - |
| T19 | lookalike_bin | task | 5/5 of 10 | - |
| T19 | h_action_grasp_and_miss | task | 0/0 of 10 | - |
| T19 | h_dynamic_cube_moved | task | 0/5 of 10 | - |
| T19 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors |
| T19 | x6_sr_cube_drop_refused | task | 0/0 of 10 | - |
| T20 | bottle_on_cabinet | control | 2/10 of 10 | juice bottle grasp |
| T20 | e2_from_bedroom_hall | control | 0/10 of 10 | juice bottle grasp |
| T20 | m_bottle_on_tv_stand | task | 5/5 of 10 | juice bottle grasp |
| T20 | table_full | action | 0/10 of 10 | juice bottle grasp |
| T20 | h_action_ik_pick_and_place | action_task | 0/0 of 10 | juice bottle grasp |
| T20 | h_dynamic_bottle_taken | action_task | 5/5 of 10 | juice bottle grasp |
| T20 | x6_cl_bottle_behind_mug__mug | action | 0/0 of 10 | juice bottle grasp |
| T20 | x6_cl_bottle_behind_mug__bowl | action | 0/0 of 10 | juice bottle grasp |
| T20 | x6_gd_bottle_put_away | task | 0/0 of 10 | juice bottle grasp, low cabinet doors |
| T14 | e1_book_ready | control | 0/10 of 10 | - |
| T14 | e2_book_ready_far | control | 0/10 of 10 | - |
| T14 | book_on_desk | action | 2/10 of 10 | - |
| T14 | m_ik_place | action | 0/0 of 10 | - |
| T14 | shelf_taken | action | 0/10 of 10 | - |
| T14 | h_action_ik_pick_and_place | action_task | 0/0 of 10 | - |
| T14 | h_dynamic_shelf_taken | action_task | 1/10 of 10 | - |
| T14 | x6_gd_book_put_away | task | 0/0 of 10 | low cabinet doors |
| T14 | x6_sr_two_hand_carry | task | 0/0 of 10 | bimanual flat pick (long side along an overhanging edge) |
