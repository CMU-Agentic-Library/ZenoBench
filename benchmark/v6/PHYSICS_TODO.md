# Physics validation to do

* 51 families are PHYSICS_VALIDATED (10/10 seeds passed in the v5 grid with the current hash and route).
* 1830 episodes remain (540 of the 54 new families): `batches/physics_todo.json`; the new families alone: `batches/physics_v6_new.json`.
* Run: `$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval` (~43 episodes / hour with 2 simulators).
* Order: (1) new families without a skill dependency (`depends on` -), (2) after each skill fix the families that depend on it, (3) re-run T11 `h_action_grasp_and_ik` (failure-injection fix 019e517; it passed in the smoke run), (4) the v5 families below 10/10 after each skill fix.

| task | family | tier | physics now | depends on |
|---|---|---|---|---|
| T01 | overhang_ready | easy | 1/10 of 10 | - |
| T01 | e2_from_dining_room | easy | 3/10 of 10 | - |
| T01 | no_overhang | medium | 6/10 of 10 | - |
| T01 | far_no_overhang | medium | 5/10 of 10 | - |
| T01 | m_ik_pick | medium | 5/10 of 10 | - |
| T01 | table_set | medium | 0/10 of 10 | - |
| T01 | h_action_ik_pick_and_place | medium | 4/10 of 10 | - |
| T01 | h_mixed_table_set_ik | medium | 9/10 of 10 | - |
| T01 | h_dynamic_pushed_back | medium | 8/10 of 10 | - |
| T01 | x6_sr_two_hand_carry | hard | 0/0 of 10 | bimanual flat pick (long side along an overhanging edge) |
| T01 | x6_m_slip_book | medium | 0/0 of 10 | - |
| T01 | x6_dr_block_on_book | hard | 0/0 of 10 | - |
| T02 | e2_from_wall_cabinet | easy | 2/10 of 10 | - |
| T02 | crowded | medium | 4/10 of 10 | - |
| T02 | far_crowded | medium | 1/10 of 10 | - |
| T02 | x6_cl_base_a_unreachable | hard | 0/0 of 10 | - |
| T02 | x6_cl_block_b_unholdable | hard | 0/0 of 10 | - |
| T02 | x6_gd_tower_with_event | hard | 0/0 of 10 | - |
| T03 | far_small_and_large | medium | 2/10 of 10 | - |
| T03 | three_containers | medium | 9/10 of 10 | - |
| T03 | h_action_slip_and_miss | medium | 6/10 of 10 | - |
| T03 | h_dynamic_pin_taken | hard | 2/5 of 10 | - |
| T04 | cup_available | easy | 6/10 of 10 | - |
| T04 | e2_from_dining_room | easy | 1/10 of 10 | - |
| T04 | no_cup | medium | 5/10 of 10 | - |
| T04 | no_cup_mug_away | medium | 4/5 of 10 | - |
| T04 | m_ik_cup | medium | 3/10 of 10 | - |
| T04 | h_task_spot_taken | hard | 9/10 of 10 | - |
| T04 | h_action_ik_and_grasp | hard | 2/10 of 10 | - |
| T04 | h_mixed_spot_taken_ik | hard | 6/10 of 10 | - |
| T04 | h_dynamic_cup_taken | medium | 4/10 of 10 | - |
| T04 | x6_gd_cup_in_cabinets | hard | 0/0 of 10 | low cabinet doors |
| T04 | x6_cl_cup_unusable | hard | 0/0 of 10 | - |
| T04 | x6_dr_spot_filled_dynamic | hard | 0/0 of 10 | - |
| T05 | h_task_pencil_in_cabinet | hard | 0/10 of 10 | low cabinet doors |
| T05 | h_action_grasp_and_ik | hard | 0/10 of 10 | low cabinet doors |
| T05 | h_mixed_cabinet_ik | hard | 0/10 of 10 | low cabinet doors |
| T05 | h_dynamic_pencil_taken | hard | 0/5 of 10 | low cabinet doors |
| T05 | x6_cl_pen_unholdable | hard | 0/0 of 10 | - |
| T05 | x6_gd_pencil_other_cabinet | hard | 0/0 of 10 | low cabinet doors |
| T05 | x6_gd_pen_or_pencil_cabinets | hard | 0/0 of 10 | low cabinet doors |
| T06 | free | easy | 9/10 of 10 | - |
| T06 | e2_from_dining_room | easy | 9/10 of 10 | - |
| T06 | occupied | medium | 9/10 of 10 | - |
| T06 | occupied_block_away | medium | 3/5 of 10 | - |
| T06 | m_slip_block | medium | 8/10 of 10 | - |
| T06 | h_dynamic_cabinet_filled | medium | 8/10 of 10 | - |
| T06 | x6_cl_block_a_unholdable | hard | 0/0 of 10 | - |
| T06 | x6_m_grasp_block_a | medium | 0/0 of 10 | - |
| T06 | x6_cl_cabinet_unreachable | hard | 0/0 of 10 | - |
| T06 | x6_m_ik_place_cabinet | medium | 0/0 of 10 | - |
| T06 | x6_gd_two_displays_event | hard | 0/0 of 10 | - |
| T07 | broken_oatmeal_away | hard | 2/5 of 10 | - |
| T07 | h_action_ik_and_slip | hard | 8/10 of 10 | - |
| T07 | x6_cl_microwave_door_stuck | hard | 0/0 of 10 | - |
| T07 | x6_m_ik_open_microwave | medium | 0/0 of 10 | - |
| T07 | x6_sr_microwave_taken | hard | 0/0 of 10 | - |
| T07 | x6_pp_door_opened_after_heat | hard | 0/0 of 10 | - |
| T08 | sponge_on_island | easy | 7/10 of 10 | wipe reach |
| T08 | e2_from_dining_room | easy | 6/10 of 10 | wipe reach |
| T08 | sponge_on_tv_stand | medium | 0/10 of 10 | wipe reach |
| T08 | far_sponge_tv | medium | 0/5 of 10 | wipe reach |
| T08 | m_grasp_sponge | medium | 3/10 of 10 | wipe reach |
| T08 | island_cluttered | hard | 0/10 of 10 | wipe reach |
| T08 | h_action_grasp_and_ik | hard | 0/10 of 10 | wipe reach |
| T08 | h_mixed_cluttered_grasp | hard | 0/10 of 10 | wipe reach |
| T08 | h_dynamic_sponge_taken | hard | 0/5 of 10 | wipe reach |
| T08 | x6_pp_sponge_taken_after_wipe | hard | 0/0 of 10 | wipe reach |
| T09 | e2_from_dining_room | easy | 0/10 of 10 | - |
| T09 | lid_on | medium | 5/10 of 10 | - |
| T09 | lid_on_spoon_away | medium | 0/5 of 10 | - |
| T09 | m_grasp_spoon | medium | 8/10 of 10 | - |
| T09 | cookware_choice | medium | 8/10 of 10 | - |
| T09 | h_action_grasp_and_ik | medium | 9/10 of 10 | - |
| T09 | h_mixed_cookware_grasp | medium | 8/10 of 10 | - |
| T09 | h_dynamic_spoon_taken | hard | 5/5 of 10 | - |
| T09 | x6_cl_spoon_unholdable | hard | 0/0 of 10 | - |
| T09 | x6_sr_collect_refused | hard | 0/0 of 10 | - |
| T09 | x6_gd_tomato_elsewhere | hard | 0/0 of 10 | - |
| T09 | x6_m_ik_collect | medium | 0/0 of 10 | - |
| T09 | x6_pp_lid_taken_after_stir | hard | 0/0 of 10 | search of the pot lid |
| T09 | x6_pp_tomato_taken_out | hard | 0/0 of 10 | - |
| T10 | can_on_island | easy | 9/10 of 10 | - |
| T10 | e2_from_dining_room | easy | 8/10 of 10 | - |
| T10 | can_in_dining_room | medium | 5/5 of 10 | - |
| T10 | far_can_far | medium | 5/5 of 10 | - |
| T10 | m_ik_can | medium | 9/10 of 10 | - |
| T10 | h_task_can_in_microwave | hard | 0/10 of 10 | pick from the microwave cavity |
| T10 | h_action_ik_pick_and_drop | hard | 0/10 of 10 | pick from the microwave cavity |
| T10 | h_mixed_microwave_ik | hard | 0/10 of 10 | pick from the microwave cavity |
| T10 | h_dynamic_can_moved | hard | 5/5 of 10 | pick from the microwave cavity |
| T10 | x6_gd_can_put_away | hard | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T10 | x6_sr_drop_refused | hard | 0/0 of 10 | - |
| T10 | x6_m_ik_drop | medium | 0/0 of 10 | - |
| T11 | e2_from_kitchen | easy | 3/10 of 10 | - |
| T11 | h_action_grasp_and_ik | hard | 0/10 of 10 | - ; failure-injection fix 019e517 (pinned IK block) |
| T11 | x6_gd_fruits_event | hard | 0/0 of 10 | - |
| T11 | x6_cl_apple_rolls_out | hard | 0/0 of 10 | - |
| T11 | x6_m_apple_rolls_out_once | medium | 0/0 of 10 | - |
| T12 | duck_in_study | medium | 5/5 of 10 | - |
| T12 | m_grasp_car | medium | 9/10 of 10 | - |
| T12 | toys_everywhere | hard | 1/5 of 10 | - |
| T12 | h_action_grasp_and_ik | hard | 2/5 of 10 | - |
| T12 | h_mixed_everywhere_ik | hard | 2/5 of 10 | - |
| T12 | h_dynamic_duck_taken | hard | 1/5 of 10 | - |
| T12 | x6_gd_bins_capacity | hard | 0/0 of 10 | - |
| T12 | x6_cl_basket_unreachable | hard | 0/0 of 10 | - |
| T12 | x6_pp_duck_moved | hard | 0/0 of 10 | - |
| T13 | dishes_on_tv_stand | easy | 8/10 of 10 | - |
| T13 | e2_from_kitchen | easy | 2/10 of 10 | - |
| T13 | no_cup | medium | 0/10 of 10 | - |
| T13 | bowl_on_cabinet | medium | 3/5 of 10 | - |
| T13 | no_cup_bowl_on_cabinet | medium | 0/5 of 10 | - |
| T13 | no_cup_spoon_boxed_in | medium | 0/10 of 10 | - |
| T13 | h_action_ik_and_grasp | hard | 0/10 of 10 | - |
| T13 | h_mixed_boxed_in_ik | medium | 0/10 of 10 | - |
| T13 | h_dynamic_mug_taken | hard | 2/5 of 10 | - |
| T13 | x6_cl_cup_slips | hard | 0/0 of 10 | - |
| T13 | x6_m_slip_cup | medium | 0/0 of 10 | - |
| T13 | x6_pp_spoon_moved | hard | 0/0 of 10 | - |
| T13 | x6_gd_bowl_put_away | hard | 0/0 of 10 | low cabinet doors, pick from the microwave cavity |
| T13 | x6_gd_two_settings | hard | 0/0 of 10 | - |
| T15 | book_free | easy | 9/10 of 10 | - |
| T15 | e2_from_dining_room | easy | 6/10 of 10 | - |
| T15 | book_out_of_view | medium | 5/10 of 10 | - |
| T15 | m_ik_flip | medium | 9/10 of 10 | - |
| T15 | m_start_dining_away | medium | 5/10 of 10 | - |
| T15 | h_task_block_on_book | hard | 3/10 of 10 | - |
| T15 | h_action_ik_twice | hard | 5/10 of 10 | - |
| T15 | h_mixed_block_on_book_ik | hard | 8/10 of 10 | - |
| T15 | h_dynamic_book_moved | hard | 2/10 of 10 | - |
| T16 | e2_from_dining_room | easy | 8/10 of 10 | - |
| T16 | m_start_dining_away | medium | 8/10 of 10 | - |
| T16 | h_action_ik_twice | hard | 9/10 of 10 | - |
| T16 | h_dynamic_bowl_put_behind | hard | 6/10 of 10 | - |
| T17 | e2_from_dining_room | easy | 0/10 of 10 | search of the pot lid |
| T17 | lid_on | medium | 5/10 of 10 | - |
| T17 | block_crowded | medium | 2/10 of 10 | - |
| T17 | lid_on_crowded | medium | 2/10 of 10 | - |
| T17 | h_task_lid_elsewhere | medium | 5/10 of 10 | - |
| T17 | h_action_ik_twice | medium | 7/10 of 10 | - |
| T17 | h_mixed_lid_elsewhere_ik | medium | 3/10 of 10 | - |
| T17 | h_dynamic_lid_put_on | medium | 1/10 of 10 | - |
| T17 | x6_sr_hide_refused | hard | 0/0 of 10 | - |
| T17 | x6_m_ik_hide | medium | 0/0 of 10 | - |
| T17 | x6_pp_lid_lifted | hard | 0/0 of 10 | search of the pot lid |
| T17 | x6_gd_hide_both_event | hard | 0/0 of 10 | - |
| T18 | m_door_left_open | medium | 0/10 of 10 | low cabinet doors |
| T18 | h_task_two_cabinets | hard | 0/10 of 10 | low cabinet doors |
| T18 | h_action_ik_open_and_close | hard | 0/10 of 10 | low cabinet doors |
| T18 | h_mixed_two_cabinets_ik | hard | 0/10 of 10 | low cabinet doors |
| T18 | h_dynamic_door_closed | hard | 0/10 of 10 | low cabinet doors |
| T18 | x6_gd_bowl_elsewhere | hard | 0/0 of 10 | low cabinet doors |
| T18 | x6_pp_door_reopened | hard | 0/0 of 10 | low cabinet doors |
| T19 | m_can_in_dining_room | medium | 5/5 of 10 | - |
| T19 | lookalike_bin | medium | 5/5 of 10 | - |
| T19 | h_action_grasp_and_miss | medium | 2/5 of 10 | - |
| T19 | h_mixed_lookalike_ik | medium | 5/5 of 10 | - |
| T19 | h_dynamic_cube_moved | hard | 0/5 of 10 | - |
| T19 | x6_sr_cube_drop_refused | hard | 0/0 of 10 | - |
| T19 | x6_m_ik_drop_cube | medium | 0/0 of 10 | - |
| T20 | bottle_on_cabinet | easy | 2/10 of 10 | juice bottle grasp |
| T20 | e2_from_bedroom_hall | easy | 0/10 of 10 | juice bottle grasp |
| T20 | m_ik_pick | medium | 0/10 of 10 | juice bottle grasp |
| T20 | m_ik_place | medium | 0/10 of 10 | juice bottle grasp |
| T20 | m_bottle_on_tv_stand | medium | 5/5 of 10 | juice bottle grasp |
| T20 | table_full | hard | 0/10 of 10 | juice bottle grasp |
| T20 | h_action_ik_pick_and_place | hard | 0/10 of 10 | juice bottle grasp |
| T20 | h_mixed_table_full_ik | hard | 1/10 of 10 | juice bottle grasp |
| T20 | h_dynamic_bottle_taken | hard | 5/5 of 10 | juice bottle grasp |
| T20 | x6_cl_bottle_behind_mug | hard | 0/0 of 10 | juice bottle grasp |
| T20 | x6_gd_bottle_put_away | hard | 0/0 of 10 | juice bottle grasp, low cabinet doors |
| T14 | e1_book_ready | easy | 0/10 of 10 | - |
| T14 | e2_book_ready_far | easy | 0/10 of 10 | - |
| T14 | book_on_desk | medium | 2/10 of 10 | - |
| T14 | m_ik_place | medium | 0/10 of 10 | - |
| T14 | m_ik_pick | medium | 2/10 of 10 | - |
| T14 | shelf_taken | hard | 0/10 of 10 | - |
| T14 | h_action_ik_pick_and_place | hard | 0/10 of 10 | - |
| T14 | h_mixed_shelf_taken_ik | hard | 3/10 of 10 | - |
| T14 | h_dynamic_shelf_taken | hard | 1/10 of 10 | - |
| T14 | x6_sr_two_hand_carry | hard | 0/0 of 10 | bimanual flat pick (long side along an overhanging edge) |
| T14 | x6_m_slip_book | medium | 0/0 of 10 | - |
