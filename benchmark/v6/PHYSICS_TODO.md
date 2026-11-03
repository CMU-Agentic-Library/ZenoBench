# Physics validation to do

* 51 families are PHYSICS_VALIDATED (10/10 seeds passed in the v5 grid with the current hash and route).
* 1870 episodes remain (580 of the 58 new families): `batches/physics_todo.json`; the new families alone: `batches/physics_v6_new.json`.
* Run: `$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval` (~43 episodes / hour with 2 simulators).
* Order: (1) new families without a skill dependency (`depends on` -), (2) after each skill fix the families that depend on it, (3) re-run T11 `h_action_grasp_and_ik` (failure-injection fix 019e517; it passed in the smoke run), (4) the v5 families below 10/10 after each skill fix.

| task | family | tracks | physics now | depends on |
|---|---|---|---|---|
| T01 | overhang_ready | control | 1/10 of 10 | - |
| T01 | e2_from_dining_room | control | 3/10 of 10 | - |
| T01 | no_overhang | action | 6/10 of 10 | - |
| T01 | far_no_overhang | action, task | 5/10 of 10 | - |
| T01 | m_ik_pick | action | 5/10 of 10 | - |
| T01 | table_set | task | 0/10 of 10 | - |
| T01 | h_action_ik_pick_and_place | action, task | 4/10 of 10 | - |
| T01 | h_mixed_table_set_ik | action, task | 9/10 of 10 | - |
| T01 | h_dynamic_pushed_back | task | 8/10 of 10 | - |
| T01 | x6_sr_two_hand_carry | action, task | 0/0 of 10 | bimanual flat pick (long side along an overhanging edge) |
| T01 | x6_m_slip_book | action | 0/0 of 10 | - |
| T01 | x6_dr_block_on_book | task | 0/0 of 10 | - |
| T02 | e2_from_wall_cabinet | control | 2/10 of 10 | - |
| T02 | crowded | action | 4/10 of 10 | - |
| T02 | far_crowded | action, task | 1/10 of 10 | - |
| T02 | x6_cl_base_a_unreachable | action, task | 0/0 of 10 | - |
| T02 | x6_cl_block_b_unholdable | action, task | 0/0 of 10 | - |
| T02 | x6_gd_tower_with_event | task | 0/0 of 10 | - |
| T03 | far_small_and_large | task | 2/10 of 10 | - |
| T03 | three_containers | task | 9/10 of 10 | - |
| T03 | h_action_slip_and_miss | action, task | 6/10 of 10 | - |
| T03 | h_dynamic_pin_taken | task | 2/5 of 10 | - |
| T04 | cup_available | control | 6/10 of 10 | - |
| T04 | e2_from_dining_room | control | 1/10 of 10 | - |
| T04 | no_cup | task | 5/10 of 10 | - |
| T04 | no_cup_mug_away | task | 4/5 of 10 | - |
| T04 | m_ik_cup | action | 3/10 of 10 | - |
| T04 | h_task_spot_taken | task | 9/10 of 10 | - |
| T04 | h_action_ik_and_grasp | action, task | 2/10 of 10 | - |
| T04 | h_mixed_spot_taken_ik | action, task | 6/10 of 10 | - |
| T04 | h_dynamic_cup_taken | task | 4/10 of 10 | - |
| T04 | x6_gd_cup_in_cabinets | task | 0/0 of 10 | low cabinet doors |
| T04 | x6_cl_cup_unusable | action, task | 0/0 of 10 | - |
| T04 | x6_dr_spot_filled_dynamic | task | 0/0 of 10 | - |
| T05 | h_task_pencil_in_cabinet | task | 0/10 of 10 | low cabinet doors |
| T05 | h_action_grasp_and_ik | action, task | 0/10 of 10 | low cabinet doors |
| T05 | h_mixed_cabinet_ik | action, task | 0/10 of 10 | low cabinet doors |
| T05 | h_dynamic_pencil_taken | task | 0/5 of 10 | low cabinet doors |
| T05 | x6_cl_pen_unholdable | action, task | 0/0 of 10 | - |
| T05 | x6_gd_pencil_other_cabinet | task | 0/0 of 10 | low cabinet doors |
| T05 | x6_gd_pen_or_pencil_cabinets | task | 0/0 of 10 | low cabinet doors |
| T06 | free | control | 9/10 of 10 | - |
| T06 | e2_from_dining_room | control | 9/10 of 10 | - |
| T06 | occupied | task | 9/10 of 10 | - |
| T06 | occupied_block_away | task | 3/5 of 10 | - |
| T06 | m_slip_block | action | 8/10 of 10 | - |
| T06 | h_dynamic_cabinet_filled | task | 8/10 of 10 | - |
| T06 | x6_cl_block_a_unholdable | action, task | 0/0 of 10 | - |
| T06 | x6_m_grasp_block_a | action | 0/0 of 10 | - |
| T06 | x6_cl_cabinet_unreachable | action, task | 0/0 of 10 | - |
| T06 | x6_m_ik_place_cabinet | action | 0/0 of 10 | - |
| T06 | x6_gd_two_displays_event | task | 0/0 of 10 | - |
| T07 | broken_oatmeal_away | task | 2/5 of 10 | - |
| T07 | h_action_ik_and_slip | action, task | 8/10 of 10 | - |
| T07 | x6_cl_microwave_door_stuck | action, task | 0/0 of 10 | - |
| T07 | x6_m_ik_open_microwave | action | 0/0 of 10 | - |
| T07 | x6_sr_microwave_taken | task | 0/0 of 10 | - |
| T07 | x6_pp_door_opened_after_heat | task | 0/0 of 10 | - |
| T08 | sponge_on_island | control | 7/10 of 10 | wipe reach |
| T08 | e2_from_dining_room | control | 6/10 of 10 | wipe reach |
| T08 | sponge_on_tv_stand | task | 0/10 of 10 | wipe reach |
| T08 | far_sponge_tv | task | 0/5 of 10 | wipe reach |
| T08 | m_grasp_sponge | action | 3/10 of 10 | wipe reach |
| T08 | island_cluttered | task | 0/10 of 10 | wipe reach |
| T08 | h_action_grasp_and_ik | action, task | 0/10 of 10 | wipe reach |
| T08 | h_mixed_cluttered_grasp | action, task | 0/10 of 10 | wipe reach |
| T08 | h_dynamic_sponge_taken | task | 0/5 of 10 | wipe reach |
| T08 | x6_cl_sponge_behind_mug | task | 0/0 of 10 | wipe reach |
| T08 | x6_pp_sponge_taken_after_wipe | task | 0/0 of 10 | wipe reach |
| T09 | e2_from_dining_room | control | 0/10 of 10 | - |
| T09 | lid_on | task | 5/10 of 10 | - |
| T09 | lid_on_spoon_away | task | 0/5 of 10 | - |
| T09 | m_grasp_spoon | action | 8/10 of 10 | - |
| T09 | cookware_choice | task | 8/10 of 10 | - |
| T09 | h_action_grasp_and_ik | action, task | 9/10 of 10 | - |
| T09 | h_mixed_cookware_grasp | action, task | 8/10 of 10 | - |
| T09 | h_dynamic_spoon_taken | task | 5/5 of 10 | - |
| T09 | x6_cl_spoon_unholdable | action, task | 0/0 of 10 | - |
| T09 | x6_sr_collect_refused | action, task | 0/0 of 10 | - |
| T09 | x6_gd_tomato_elsewhere | task | 0/0 of 10 | - |
| T09 | x6_m_ik_collect | action | 0/0 of 10 | - |
| T09 | x6_pp_lid_taken_after_stir | task | 0/0 of 10 | search of the pot lid |
| T09 | x6_pp_tomato_taken_out | task | 0/0 of 10 | - |
| T10 | can_on_island | control | 9/10 of 10 | - |
| T10 | e2_from_dining_room | control | 8/10 of 10 | - |
| T10 | can_in_dining_room | task | 5/5 of 10 | - |
| T10 | far_can_far | task | 5/5 of 10 | - |
| T10 | m_ik_can | action | 9/10 of 10 | - |
| T10 | h_task_can_in_microwave | task | 0/10 of 10 | pick from the microwave cavity |
| T10 | h_action_ik_pick_and_drop | action, task | 0/10 of 10 | pick from the microwave cavity |
| T10 | h_mixed_microwave_ik | action, task | 0/10 of 10 | pick from the microwave cavity |
| T10 | h_dynamic_can_moved | task | 5/5 of 10 | pick from the microwave cavity |
| T10 | x6_cl_can_behind_bottle | task | 0/0 of 10 | juice bottle grasp |
| T10 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T10 | x6_sr_drop_refused | action, task | 0/0 of 10 | - |
| T10 | x6_m_ik_drop | action | 0/0 of 10 | - |
| T11 | e2_from_kitchen | control | 3/10 of 10 | - |
| T11 | h_action_grasp_and_ik | action, task | 0/10 of 10 | - ; failure-injection fix 019e517 (pinned IK block) |
| T11 | x6_gd_fruits_event | task | 0/0 of 10 | - |
| T11 | x6_cl_apple_rolls_out | action, task | 0/0 of 10 | - |
| T11 | x6_m_apple_rolls_out_once | action | 0/0 of 10 | - |
| T12 | duck_in_study | task | 5/5 of 10 | - |
| T12 | m_grasp_car | action | 9/10 of 10 | - |
| T12 | toys_everywhere | task | 1/5 of 10 | - |
| T12 | h_action_grasp_and_ik | action, task | 2/5 of 10 | - |
| T12 | h_mixed_everywhere_ik | action, task | 2/5 of 10 | - |
| T12 | h_dynamic_duck_taken | task | 1/5 of 10 | - |
| T12 | x6_gd_bins_capacity | task | 0/0 of 10 | - |
| T12 | x6_cl_basket_unreachable | action, task | 0/0 of 10 | - |
| T12 | x6_pp_duck_moved | task | 0/0 of 10 | - |
| T13 | dishes_on_tv_stand | control | 8/10 of 10 | - |
| T13 | e2_from_kitchen | control | 2/10 of 10 | - |
| T13 | no_cup | task | 0/10 of 10 | - |
| T13 | bowl_on_cabinet | task | 3/5 of 10 | - |
| T13 | no_cup_bowl_on_cabinet | task | 0/5 of 10 | - |
| T13 | no_cup_spoon_boxed_in | task | 0/10 of 10 | - |
| T13 | h_action_ik_and_grasp | action, task | 0/10 of 10 | - |
| T13 | h_mixed_boxed_in_ik | action, task | 0/10 of 10 | - |
| T13 | h_dynamic_mug_taken | task | 2/5 of 10 | - |
| T13 | x6_cl_cup_slips | action, task | 0/0 of 10 | - |
| T13 | x6_m_slip_cup | action | 0/0 of 10 | - |
| T13 | x6_pp_spoon_moved | task | 0/0 of 10 | - |
| T13 | x6_gd_bowl_put_away | task | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T13 | x6_gd_two_settings | task | 0/0 of 10 | - |
| T15 | book_free | control | 9/10 of 10 | - |
| T15 | e2_from_dining_room | control | 6/10 of 10 | - |
| T15 | book_out_of_view | task | 5/10 of 10 | - |
| T15 | m_ik_flip | action | 9/10 of 10 | - |
| T15 | m_start_dining_away | task | 5/10 of 10 | - |
| T15 | h_task_block_on_book | task | 3/10 of 10 | - |
| T15 | h_action_ik_twice | action, task | 5/10 of 10 | - |
| T15 | h_mixed_block_on_book_ik | action, task | 8/10 of 10 | - |
| T15 | h_dynamic_book_moved | task | 2/10 of 10 | - |
| T16 | e2_from_dining_room | control | 8/10 of 10 | - |
| T16 | m_start_dining_away | task | 8/10 of 10 | - |
| T16 | h_action_ik_twice | action, task | 9/10 of 10 | - |
| T16 | h_dynamic_bowl_put_behind | task | 6/10 of 10 | - |
| T17 | e2_from_dining_room | control | 0/10 of 10 | search of the pot lid |
| T17 | lid_on | task | 5/10 of 10 | - |
| T17 | block_crowded | action | 2/10 of 10 | - |
| T17 | lid_on_crowded | action, task | 2/10 of 10 | - |
| T17 | h_task_lid_elsewhere | task | 5/10 of 10 | - |
| T17 | h_action_ik_twice | action, task | 7/10 of 10 | - |
| T17 | h_mixed_lid_elsewhere_ik | action, task | 3/10 of 10 | - |
| T17 | h_dynamic_lid_put_on | task | 1/10 of 10 | - |
| T17 | x6_sr_hide_refused | action, task | 0/0 of 10 | - |
| T17 | x6_m_ik_hide | action | 0/0 of 10 | - |
| T17 | x6_pp_lid_lifted | task | 0/0 of 10 | search of the pot lid |
| T17 | x6_gd_hide_both_event | task | 0/0 of 10 | - |
| T18 | m_door_left_open | task | 0/10 of 10 | low cabinet doors |
| T18 | h_task_two_cabinets | task | 0/10 of 10 | low cabinet doors |
| T18 | h_action_ik_open_and_close | action, task | 0/10 of 10 | low cabinet doors |
| T18 | h_mixed_two_cabinets_ik | action, task | 0/10 of 10 | low cabinet doors |
| T18 | h_dynamic_door_closed | task | 0/10 of 10 | low cabinet doors |
| T18 | x6_gd_bowl_elsewhere | task | 0/0 of 10 | low cabinet doors |
| T18 | x6_pp_door_reopened | task | 0/0 of 10 | low cabinet doors |
| T19 | m_can_in_dining_room | task | 5/5 of 10 | - |
| T19 | lookalike_bin | task | 5/5 of 10 | - |
| T19 | h_action_grasp_and_miss | action, task | 2/5 of 10 | - |
| T19 | h_mixed_lookalike_ik | action, task | 5/5 of 10 | - |
| T19 | h_dynamic_cube_moved | task | 0/5 of 10 | - |
| T19 | x6_gd_can_put_away | task | 0/0 of 10 | low cabinet doors |
| T19 | x6_sr_cube_drop_refused | action, task | 0/0 of 10 | - |
| T19 | x6_m_ik_drop_cube | action | 0/0 of 10 | - |
| T20 | bottle_on_cabinet | control | 2/10 of 10 | juice bottle grasp |
| T20 | e2_from_bedroom_hall | control | 0/10 of 10 | juice bottle grasp |
| T20 | m_ik_pick | action | 0/10 of 10 | juice bottle grasp |
| T20 | m_ik_place | action | 0/10 of 10 | juice bottle grasp |
| T20 | m_bottle_on_tv_stand | task | 5/5 of 10 | juice bottle grasp |
| T20 | table_full | task | 0/10 of 10 | juice bottle grasp |
| T20 | h_action_ik_pick_and_place | action, task | 0/10 of 10 | juice bottle grasp |
| T20 | h_mixed_table_full_ik | action, task | 1/10 of 10 | juice bottle grasp |
| T20 | h_dynamic_bottle_taken | task | 5/5 of 10 | juice bottle grasp |
| T20 | x6_cl_bottle_behind_mug | task | 0/0 of 10 | juice bottle grasp |
| T20 | x6_gd_bottle_put_away | task | 0/0 of 10 | juice bottle grasp, low cabinet doors |
| T14 | e1_book_ready | control | 0/10 of 10 | - |
| T14 | e2_book_ready_far | control | 0/10 of 10 | - |
| T14 | book_on_desk | action | 2/10 of 10 | - |
| T14 | m_ik_place | action | 0/10 of 10 | - |
| T14 | m_ik_pick | action | 2/10 of 10 | - |
| T14 | shelf_taken | task | 0/10 of 10 | - |
| T14 | h_action_ik_pick_and_place | action, task | 0/10 of 10 | - |
| T14 | h_mixed_shelf_taken_ik | action, task | 3/10 of 10 | - |
| T14 | h_dynamic_shelf_taken | action, task | 1/10 of 10 | - |
| T14 | x6_gd_book_put_away | task | 0/0 of 10 | low cabinet doors |
| T14 | x6_sr_two_hand_carry | action, task | 0/0 of 10 | bimanual flat pick (long side along an overhanging edge) |
| T14 | x6_m_slip_book | action | 0/0 of 10 | - |
