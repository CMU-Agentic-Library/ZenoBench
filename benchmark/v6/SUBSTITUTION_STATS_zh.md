# 替换统计（按摆法）

已审过的变体里一共 39 个摆法，其中 32 个要做替换，7 个不用替换（理想的东西在、眼前也没有诱惑，作对照）。五类平均每类应有约 6.4 个。由 `python benchmark/v6/substitution_stats.py` 生成。

## 每类替换的摆法数

| 类别 | 摆法数 | 和平均的差 |
|---|---|---|
| 缺失 | 16 | +9.6 |
| 被占用 | 6 | -0.4 |
| 能力不足 | 4 | -2.4 |
| 看着像但不能用 | 3 | -3.4 |
| 去处替换 | 3 | -3.4 |

## 理想物在不在（不在时，最好的替代算好）

| 理想物 | 摆法数 |
|---|---|
| 在 | 14 |
| 不在 | 18 |

## 类别 × 理想物在不在

| 类别 | 在 | 不在 |
|---|---|---|
| 缺失 | 6 | 10 |
| 被占用 | 2 | 4 |
| 能力不足 | 2 | 2 |
| 看着像但不能用 | 3 | 0 |
| 去处替换 | 1 | 2 |

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
