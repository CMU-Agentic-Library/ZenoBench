# 替换统计（按摆法）

已审过的变体里一共 226 个摆法，其中 154 个要做替换，72 个不用替换（理想的东西在、眼前也没有诱惑，作对照）。五类平均每类应有约 30.8 个。由 `python benchmark/v6/substitution_stats.py` 生成。

## 每类替换的摆法数

| 类别 | 摆法数 | 和平均的差 |
|---|---|---|
| 缺失 | 33 | +2.2 |
| 被占用 | 34 | +3.2 |
| 能力不足 | 22 | -8.8 |
| 看着像但不能用 | 29 | -1.8 |
| 去处替换 | 36 | +5.2 |

## 理想物在不在（不在时，最好的替代算好）

| 理想物 | 摆法数 |
|---|---|
| 在 | 112 |
| 不在 | 42 |

## 类别 × 理想物在不在

| 类别 | 在 | 不在 |
|---|---|---|
| 缺失 | 17 | 16 |
| 被占用 | 19 | 15 |
| 能力不足 | 16 | 6 |
| 看着像但不能用 | 29 | 0 |
| 去处替换 | 31 | 5 |

## 每个摆法

| 任务 | 变体 | 摆法 | 类别 | 理想物 | D |
|---|---|---|---|---|---|
| T01 | which_book | living | 看着像但不能用 | 在 | 1 |
| T01 | which_book | bedroom | 看着像但不能用 | 在 | 1 |
| T02 | crowded_use_another | tight_tv | 被占用 | 在 | 1 |
| T02 | crowded_use_another | tight_dining | 被占用 | 在 | 1 |
| T02 | crowded_use_another | loose | 不用替换 | 在 | 1 |
| T02 | third_toy_elsewhere | duck | 缺失 | 在 | 1 |
| T02 | third_toy_elsewhere | toy_block | 缺失 | 在 | 1 |
| T02 | tower_for_kid | counter | 不用替换 | 在 | 1 |
| T02 | tower_for_kid | study | 不用替换 | 在 | 1 |
| T02 | tower_for_kid | near_full | 去处替换 | 不在 | 1 |
| T02 | tower_for_kid | both_full | 去处替换 | 不在 | 0 |
| T02 | tower_for_kid_duck | counter | 缺失 | 在 | 1 |
| T02 | tower_for_kid_duck | study | 缺失 | 在 | 1 |
| T02 | block_put_away | in_4 | 缺失 | 在 | 1 |
| T02 | block_put_away | in_6 | 缺失 | 在 | 1 |
| T02 | block_put_away | gone_toy_block | 缺失 | 不在 | 1 |
| T02 | block_put_away | gone_duck | 缺失 | 不在 | 1 |
| T03 | small_bin_or_bedroom_bin | wide_in_bedroom | 能力不足 | 在 | 1 |
| T03 | small_bin_or_bedroom_bin | basket_in_bedroom | 能力不足 | 不在 | 1 |
| T03 | which_bin_by_contents | toys_near | 看着像但不能用 | 在 | 1 |
| T03 | which_bin_by_contents | kitchen_bin_full | 被占用 | 不在 | 1 |
| T03 | no_bin_substitute | basket | 缺失 | 不在 | 1 |
| T03 | no_bin_substitute | tray | 缺失 | 不在 | 1 |
| T03 | utensils_apart | bin_free | 不用替换 | 在 | 0 |
| T03 | utensils_apart | bin_full_tray | 被占用 | 不在 | 1 |
| T03 | utensils_apart | bin_full_basket | 被占用 | 不在 | 1 |
| T03 | utensils_apart | bin_full_fruit | 被占用 | 不在 | 0 |
| T04 | cup_available | — | 不用替换 | 在 | 1 |
| T04 | no_cup | — | 缺失 | 不在 | 0 |
| T04 | no_cup | — | 缺失 | 不在 | 0 |
| T04 | no_cup | alt_dining_table_2 | 缺失 | 不在 | 0 |
| T04 | no_cup | — | 缺失 | 不在 | 0 |
| T04 | clear_the_drinks_spot | spot_dishes | 不用替换 | 在 | 1 |
| T04 | clear_the_drinks_spot | spot_kid_toys | 去处替换 | 在 | 1 |
| T04 | two_guests | glass_in_cabinet | 不用替换 | 在 | 1 |
| T04 | two_guests | mug | 缺失 | 不在 | 1 |
| T04 | two_guests | kid_cup | 缺失 | 不在 | 1 |
| T04 | x6_gd_cup_in_cabinets | cup_in_4 | 能力不足 | 在 | 1 |
| T04 | x6_gd_cup_in_cabinets | plastic_only | 能力不足 | 不在 | 1 |
| T05 | no_pen_pencil_away | — | 不用替换 | 在 | 0 |
| T05 | no_pen_pencil_away | — | 被占用 | 不在 | 1 |
| T05 | check_desk_first | pen_on_desk | 不用替换 | 在 | 1 |
| T05 | check_desk_first | pencil_on_desk | 看着像但不能用 | 在 | 1 |
| T05 | check_desk_first | pen_in_use | 被占用 | 不在 | 1 |
| T05 | homework_ready | single | 看着像但不能用 | 在 | 1 |
| T05 | homework_ready | several | 看着像但不能用 | 在 | 1 |
| T05 | homework_ready | notebook_in_use | 被占用 | 不在 | 1 |
| T05 | errand_combined | pen_bedroom | 不用替换 | 在 | 1 |
| T05 | errand_combined | pen_in_use | 被占用 | 不在 | 1 |
| T05 | x6_gd_pen_or_pencil_cabinets | pen_in_4 | 看着像但不能用 | 在 | 1 |
| T05 | x6_gd_pen_or_pencil_cabinets | pen_in_use | 被占用 | 不在 | 1 |
| T06 | free | — | 不用替换 | 在 | 0 |
| T06 | display_row | cab_free | 不用替换 | 在 | 1 |
| T06 | display_row | cab_short | 能力不足 | 不在 | 1 |
| T06 | display_spot_or_tv | front_taken | 去处替换 | 不在 | 1 |
| T06 | display_spot_or_tv | front_free | 不用替换 | 在 | 1 |
| T06 | display_spot_or_tv | front_taken_tv_full | 去处替换 | 不在 | 1 |
| T06 | display_spot_or_tv | front_free_block_away | 不用替换 | 在 | 1 |
| T06 | seen_from_bed | boxes_middle | 不用替换 | 在 | 1 |
| T06 | seen_from_bed | bookcase_full | 去处替换 | 在 | 1 |
| T07 | microwave_works | — | 不用替换 | 在 | 1 |
| T07 | microwave_broken | — | 看着像但不能用 | 在 | 1 |
| T07 | microwave_broken | — | 看着像但不能用 | 在 | 1 |
| T07 | microwave_broken | alt_dining_table_2 | 看着像但不能用 | 在 | 1 |
| T07 | microwave_holds_pot | — | 被占用 | 在 | 1 |
| T07 | vessel_decides_appliance | in_ceramic_bowl | 不用替换 | 在 | 1 |
| T07 | vessel_decides_appliance | in_glass_box | 不用替换 | 在 | 1 |
| T07 | vessel_decides_appliance | in_pot | 能力不足 | 在 | 1 |
| T07 | vessel_decides_appliance | in_steel_box | 能力不足 | 在 | 1 |
| T07 | vessel_decides_appliance | in_foil_tray | 能力不足 | 在 | 1 |
| T07 | two_portions | dining | 不用替换 | 在 | 1 |
| T07 | two_portions | counter | 不用替换 | 在 | 1 |
| T08 | sponge_on_island | — | 不用替换 | 在 | 1 |
| T08 | far_sponge_tv | — | 不用替换 | 在 | 1 |
| T08 | far_sponge_tv | — | 看着像但不能用 | 在 | 1 |
| T08 | far_sponge_tv | — | 缺失 | 不在 | 1 |
| T08 | wipe_and_sort | blocks | 不用替换 | 在 | 1 |
| T08 | wipe_and_sort | duck | 不用替换 | 在 | 1 |
| T08 | return_sponge_home | dining | 不用替换 | 在 | 1 |
| T08 | return_sponge_home | study | 不用替换 | 在 | 1 |
| T08 | return_sponge_home | far_dining | 不用替换 | 在 | 1 |
| T08 | which_surface | island | 不用替换 | 在 | 1 |
| T08 | which_surface | dining | 不用替换 | 在 | 1 |
| T09 | lid_off | — | 不用替换 | 在 | 1 |
| T09 | lid_on_spoon_away | — | 不用替换 | 在 | 1 |
| T09 | lid_on_spoon_away | — | 缺失 | 不在 | 1 |
| T09 | pot_in_use | in_use | 被占用 | 在 | 1 |
| T09 | pot_in_use | free | 不用替换 | 在 | 1 |
| T09 | tomato_in_fridge | in_fridge | 不用替换 | 在 | 1 |
| T09 | tomato_in_fridge | big_tomato | 缺失 | 不在 | 1 |
| T09 | x6_gd_tomato_elsewhere | dining | 不用替换 | 在 | 1 |
| T09 | x6_gd_tomato_elsewhere | on_plate | 被占用 | 不在 | 1 |
| T09 | pot_in_dining_room | pot_away | 不用替换 | 在 | 1 |
| T09 | pot_in_dining_room | spare_pot | 缺失 | 不在 | 1 |
| T10 | can_on_island | — | 不用替换 | 在 | 0 |
| T10 | can_in_dining_room | — | 不用替换 | 在 | 0 |
| T10 | can_in_dining_room | alt_tv_stand_2 | 不用替换 | 在 | 0 |
| T10 | keep_kids_can | kid_desk | 被占用 | 在 | 1 |
| T10 | keep_kids_can | kid_island | 被占用 | 在 | 1 |
| T10 | trash_moved | dining | 不用替换 | 在 | 0 |
| T10 | trash_moved | trash_full | 能力不足 | 不在 | 1 |
| T10 | after_dinner_clear | rubbish_leftovers | 去处替换 | 在 | 1 |
| T10 | after_dinner_clear | leftovers_mug | 去处替换 | 在 | 1 |
| T10 | after_dinner_clear | rubbish_mug | 去处替换 | 在 | 1 |
| T10 | guests_coming | can_mug_block | 去处替换 | 在 | 1 |
| T10 | guests_coming | can_block | 去处替换 | 在 | 1 |
| T10 | guests_coming | can_mug | 去处替换 | 在 | 1 |
| T10 | x6_gd_can_put_away | in_cabinet | 不用替换 | 在 | 1 |
| T10 | x6_gd_can_put_away | fridge_drink | 看着像但不能用 | 在 | 1 |
| T11 | fruits_on_table | — | 不用替换 | 在 | 1 |
| T11 | basket_missing | — | 缺失 | 在 | 1 |
| T11 | basket_missing | — | 看着像但不能用 | 在 | 1 |
| T11 | leave_one_for_kid | apple_orange | 去处替换 | 在 | 1 |
| T11 | leave_one_for_kid | orange_banana | 去处替换 | 在 | 1 |
| T11 | leave_one_for_kid | all_three | 去处替换 | 在 | 1 |
| T11 | fruit_plate_for_guests | tray_in_study | 不用替换 | 在 | 1 |
| T11 | fruit_plate_for_guests | tray_in_use | 被占用 | 不在 | 1 |
| T12 | toys_out | — | 不用替换 | 在 | 0 |
| T12 | duck_in_study | — | 不用替换 | 在 | 0 |
| T12 | duck_in_study | alt_dining_table_2 | 不用替换 | 在 | 0 |
| T12 | bins_capacity | side_left_full | 能力不足 | 在 | 1 |
| T12 | bins_capacity | side_right_full | 能力不足 | 在 | 1 |
| T12 | bins_capacity | apart_full_on_tv | 能力不足 | 在 | 1 |
| T12 | bins_capacity | apart_empty_on_desk | 能力不足 | 在 | 1 |
| T12 | bins_capacity | half_bin_and_tray | 能力不足 | 在 | 1 |
| T12 | bins_capacity | half_bin_and_tray_duck_dining | 能力不足 | 在 | 1 |
| T12 | find_all_toys | car_duck | 看着像但不能用 | 在 | 1 |
| T12 | find_all_toys | car_duck_bear | 看着像但不能用 | 在 | 1 |
| T12 | find_all_toys | all_four | 看着像但不能用 | 在 | 1 |
| T12 | castle_stays | tall_two_loose | 被占用 | 在 | 1 |
| T12 | castle_stays | short_one_loose | 被占用 | 在 | 1 |
| T12 | castle_stays | tall_none_loose | 被占用 | 在 | 1 |
| T13 | dishes_on_tv_stand | — | 不用替换 | 在 | 1 |
| T13 | no_cup | — | 缺失 | 在 | 0 |
| T13 | copy_the_setting | bowl_cup | 去处替换 | 在 | 1 |
| T13 | copy_the_setting | plate_bowl_mug_left | 去处替换 | 在 | 1 |
| T13 | copy_the_setting | no_cup | 缺失 | 在 | 1 |
| T13 | finish_the_table | adult_seat | 去处替换 | 在 | 1 |
| T13 | finish_the_table | kid_seat | 去处替换 | 在 | 1 |
| T13 | finish_the_table | adult_and_kid | 去处替换 | 在 | 1 |
| T15 | lid_by_pot | — | 不用替换 | 在 | 0 |
| T15 | lid_elsewhere | dining | 不用替换 | 在 | 0 |
| T15 | lid_elsewhere | covering_bowl | 被占用 | 不在 | 1 |
| T15 | no_lid | — | 缺失 | 不在 | 1 |
| T15 | lid_in_use | — | 被占用 | 不在 | 1 |
| T16 | box_on_counter | — | 不用替换 | 在 | 0 |
| T16 | box_in_cabinet | in_cabinet | 不用替换 | 在 | 1 |
| T16 | box_in_cabinet | box_full | 能力不足 | 不在 | 1 |
| T16 | no_box | — | 缺失 | 不在 | 1 |
| T16 | box_in_use | — | 被占用 | 不在 | 1 |
| T17 | lid_off | — | 不用替换 | 在 | 1 |
| T17 | h_task_lid_elsewhere | — | 不用替换 | 在 | 1 |
| T17 | h_task_lid_elsewhere | — | 被占用 | 不在 | 1 |
| T17 | hide_both | tv_stand | 不用替换 | 在 | 1 |
| T17 | hide_both | two_pots | 看着像但不能用 | 在 | 1 |
| T17 | hide_somewhere | pot_ready | 不用替换 | 在 | 0 |
| T17 | hide_somewhere | lid_away | 去处替换 | 不在 | 0 |
| T18 | bowls_in_cabinet | — | 不用替换 | 在 | 1 |
| T18 | bowls_apart | — | 不用替换 | 在 | 1 |
| T18 | one_bowl | glass_box | 缺失 | 在 | 1 |
| T18 | one_bowl | mug | 缺失 | 在 | 1 |
| T18 | bowl_in_use | tomatoes | 被占用 | 在 | 1 |
| T18 | bowl_in_use | oatmeal | 被占用 | 在 | 1 |
| T18 | door_stuck | — | 看着像但不能用 | 在 | 0 |
| T19 | bin_on_bookcase | — | 不用替换 | 在 | 0 |
| T19 | m_can_in_dining_room | — | 不用替换 | 在 | 0 |
| T19 | m_can_in_dining_room | — | 被占用 | 在 | 1 |
| T19 | lookalike_bin | — | 看着像但不能用 | 在 | 1 |
| T19 | lookalike_bin | alt_tv_stand_2 | 看着像但不能用 | 在 | 1 |
| T19 | x6_gd_can_put_away | in_4 | 不用替换 | 在 | 1 |
| T19 | x6_gd_can_put_away | juice_full | 看着像但不能用 | 在 | 1 |
| T20 | bottle_on_cabinet | — | 不用替换 | 在 | 1 |
| T20 | m_bottle_on_tv_stand | — | 不用替换 | 在 | 1 |
| T20 | m_bottle_on_tv_stand | — | 被占用 | 在 | 1 |
| T20 | x6_gd_bottle_put_away | on_tv_stand | 看着像但不能用 | 在 | 1 |
| T20 | x6_gd_bottle_put_away | in_bedroom | 看着像但不能用 | 在 | 1 |
| T14 | e1_book_ready | — | 不用替换 | 在 | 1 |
| T14 | within_kids_reach | set_on_large_shelf_4 | 去处替换 | 在 | 1 |
| T14 | within_kids_reach | set_on_large_shelf_5 | 去处替换 | 在 | 1 |
| T14 | stack_them_stably | room | 不用替换 | 在 | 1 |
| T14 | stack_them_stably | narrow_top | 能力不足 | 不在 | 1 |
| T14 | homework_stays | — | 被占用 | 在 | 1 |
| T14 | whose_book | blue_book | 去处替换 | 在 | 1 |
| T14 | whose_book | paperback | 去处替换 | 在 | 1 |
| T14 | whose_book | both | 去处替换 | 在 | 1 |
| T14 | next_in_series | on_bookcase | 看着像但不能用 | 在 | 1 |
| T14 | next_in_series | on_other_bookcase | 看着像但不能用 | 在 | 1 |
| T14 | next_in_series | on_tall_shelf | 看着像但不能用 | 在 | 1 |
| T21 | tissue_on_tv_stand | — | 不用替换 | 在 | 0 |
| T21 | which_table | east | 去处替换 | 在 | 0 |
| T21 | which_table | west | 去处替换 | 在 | 0 |
| T21 | no_tissue | — | 缺失 | 在 | 0 |
| T21 | the_kids_side | kid_north | 去处替换 | 在 | 1 |
| T21 | the_kids_side | kid_south | 去处替换 | 在 | 1 |
| T22 | juice_on_table | — | 不用替换 | 在 | 1 |
| T22 | by_kind | — | 去处替换 | 在 | 1 |
| T22 | eat_now | desk_free | 去处替换 | 在 | 1 |
| T22 | eat_now | desk_corner | 被占用 | 在 | 1 |
| T22 | not_shopping | — | 看着像但不能用 | 在 | 1 |
| T22 | two_spots | — | 去处替换 | 在 | 1 |
| T22 | tray_elsewhere | orange_in_it | 缺失 | 在 | 1 |
| T22 | tray_elsewhere | books_on_it | 被占用 | 在 | 1 |
| T22 | tray_elsewhere | — | 缺失 | 在 | 1 |
| T23 | spoon_on_floor | — | 不用替换 | 在 | 0 |
| T23 | by_kind | toy_box | 去处替换 | 在 | 1 |
| T23 | by_kind | bin_full | 能力不足 | 在 | 1 |
| T23 | belongs_on_floor | no_toy_box | 缺失 | 在 | 1 |
| T23 | belongs_on_floor | bin_full | 能力不足 | 在 | 1 |
| T23 | dropped_out_of_view | counter_full | 被占用 | 在 | 1 |
| T23 | dropped_out_of_view | no_room_for_plate | 能力不足 | 在 | 1 |
| T23 | only_this_room | cabinet_room | 不用替换 | 在 | 1 |
| T23 | only_this_room | cabinet_full | 能力不足 | 在 | 1 |
| T23 | dropped_in_two_rooms | shelf_room | 不用替换 | 在 | 1 |
| T23 | dropped_in_two_rooms | shelf_full | 能力不足 | 在 | 1 |
| T24 | apple_on_table | — | 不用替换 | 在 | 0 |
| T24 | no_apples_for_him | apple_free | 不用替换 | 在 | 0 |
| T24 | no_apples_for_him | apple_in_use | 被占用 | 在 | 1 |
| T24 | dinner_soon | apple | 看着像但不能用 | 在 | 1 |
| T24 | dinner_soon | banana | 看着像但不能用 | 在 | 1 |
| T24 | fruit_out_of_view | apple_in_basket | 不用替换 | 在 | 1 |
| T24 | fruit_out_of_view | basket_empty | 缺失 | 在 | 1 |
| T24 | where_is_he | study | 去处替换 | 在 | 0 |
| T24 | where_is_he | bedroom | 去处替换 | 在 | 0 |
| T24 | two_kids | apple_banana | 不用替换 | 在 | 1 |
| T24 | two_kids | apple_snacks | 缺失 | 在 | 1 |
| T24 | two_kids | desk3_covered | 被占用 | 在 | 1 |
