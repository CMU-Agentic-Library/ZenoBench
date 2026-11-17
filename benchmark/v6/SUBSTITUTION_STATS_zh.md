# 替换统计（按摆法）

已审过的变体里一共 27 个摆法，其中 23 个要做替换，4 个不用替换（理想的东西在、眼前也没有诱惑，作对照）。五类平均每类应有约 4.6 个。由 `python benchmark/v6/substitution_stats.py` 生成。

## 每类替换的摆法数

| 类别 | 摆法数 | 和平均的差 |
|---|---|---|
| 缺失 | 10 | +5.4 |
| 被占用 | 6 | +1.4 |
| 能力不足 | 2 | -2.6 |
| 看着像但不能用 | 3 | -1.6 |
| 去处替换 | 2 | -2.6 |

## 最高能拿到哪一档

| 最高档 | 摆法数 |
|---|---|
| 好 | 12 |
| 次好 | 9 |
| 最不好 | 2 |

## 类别 × 最高档

| 类别 | 好 | 次好 | 最不好 |
|---|---|---|---|
| 缺失 | 6 | 4 | 0 |
| 被占用 | 2 | 3 | 1 |
| 能力不足 | 1 | 1 | 0 |
| 看着像但不能用 | 3 | 0 | 0 |
| 去处替换 | 0 | 1 | 1 |

## 每个摆法

| 任务 | 变体 | 摆法 | 类别 | 最高档 | D |
|---|---|---|---|---|---|
| T01 | which_book | living | 看着像但不能用 | 好 | 1 |
| T01 | which_book | bedroom | 看着像但不能用 | 好 | 1 |
| T02 | crowded_use_another | tight_tv | 被占用 | 好 | 1 |
| T02 | crowded_use_another | tight_dining | 被占用 | 好 | 1 |
| T02 | crowded_use_another | loose | 不用替换 | 好 | 1 |
| T02 | third_toy_elsewhere | duck | 缺失 | 好 | 1 |
| T02 | third_toy_elsewhere | toy_block | 缺失 | 好 | 1 |
| T02 | tower_for_kid | counter | 不用替换 | 好 | 1 |
| T02 | tower_for_kid | study | 不用替换 | 好 | 1 |
| T02 | tower_for_kid | near_full | 去处替换 | 次好 | 1 |
| T02 | tower_for_kid | both_full | 去处替换 | 最不好 | 0 |
| T02 | tower_for_kid_duck | counter | 缺失 | 好 | 1 |
| T02 | tower_for_kid_duck | study | 缺失 | 好 | 1 |
| T02 | block_put_away | in_4 | 缺失 | 好 | 1 |
| T02 | block_put_away | in_6 | 缺失 | 好 | 1 |
| T02 | block_put_away | gone_toy_block | 缺失 | 次好 | 1 |
| T02 | block_put_away | gone_duck | 缺失 | 次好 | 1 |
| T03 | small_bin_or_bedroom_bin | wide_in_bedroom | 能力不足 | 好 | 1 |
| T03 | small_bin_or_bedroom_bin | basket_in_bedroom | 能力不足 | 次好 | 1 |
| T03 | which_bin_by_contents | toys_near | 看着像但不能用 | 好 | 1 |
| T03 | which_bin_by_contents | kitchen_bin_full | 被占用 | 次好 | 1 |
| T03 | no_bin_substitute | basket | 缺失 | 次好 | 1 |
| T03 | no_bin_substitute | tray | 缺失 | 次好 | 1 |
| T03 | utensils_apart | bin_free | 不用替换 | 好 | 0 |
| T03 | utensils_apart | bin_full_tray | 被占用 | 次好 | 1 |
| T03 | utensils_apart | bin_full_basket | 被占用 | 次好 | 1 |
| T03 | utensils_apart | bin_full_fruit | 被占用 | 最不好 | 0 |
