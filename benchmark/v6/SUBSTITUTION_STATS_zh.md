# 替换统计（按摆法）

已审过的变体里一共 83 个摆法，其中 54 个要做替换，29 个不用替换（理想的东西在、眼前也没有诱惑，作对照）。五类平均每类应有约 10.8 个。由 `python benchmark/v6/substitution_stats.py` 生成。

## 每类替换的摆法数

| 类别 | 摆法数 | 和平均的差 |
|---|---|---|
| 缺失 | 17 | +6.2 |
| 被占用 | 12 | +1.2 |
| 能力不足 | 8 | -2.8 |
| 看着像但不能用 | 11 | +0.2 |
| 去处替换 | 6 | -4.8 |

## 理想物在不在（不在时，最好的替代算好）

| 理想物 | 摆法数 |
|---|---|
| 在 | 27 |
| 不在 | 27 |

## 类别 × 理想物在不在

| 类别 | 在 | 不在 |
|---|---|---|
| 缺失 | 6 | 11 |
| 被占用 | 3 | 9 |
| 能力不足 | 5 | 3 |
| 看着像但不能用 | 11 | 0 |
| 去处替换 | 2 | 4 |

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
