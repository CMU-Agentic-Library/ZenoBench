# 替换统计（按摆法）

已审过的变体里一共 286 个摆法，其中 182 个要做替换，104 个不用替换（理想的东西在、眼前也没有诱惑，作对照）。五类平均每类应有约 36.4 个。由 `python benchmark/v6/substitution_stats.py` 生成。

## 每类替换的摆法数

| 类别 | 摆法数 | 和平均的差 |
|---|---|---|
| 缺失 | 45 | +8.6 |
| 被占用 | 42 | +5.6 |
| 能力不足 | 23 | -13.4 |
| 看着像但不能用 | 30 | -6.4 |
| 去处替换 | 42 | +5.6 |

## 理想物在不在（不在时，原来的次好——最好的替代——就是这个摆法的理想，算好）

| 理想物 | 摆法数 |
|---|---|
| 在 | 83 |
| 不在 | 99 |

## 类别 × 理想物在不在

| 类别 | 在 | 不在 |
|---|---|---|
| 缺失 | 4 | 41 |
| 被占用 | 14 | 28 |
| 能力不足 | 5 | 18 |
| 看着像但不能用 | 24 | 6 |
| 去处替换 | 36 | 6 |

## 每个摆法（理想：ideals.py 里逐个定的；理想物不在时，括号里的替代就是这个摆法的理想，算好 1.0，后面的依次 0.6、0.3；没列的摆法不用替换，理想就是最好那档）

| 任务 | 变体 | 摆法 | 类别 | 理想 | 理想物 | D |
|---|---|---|---|---|---|---|
| T01 | which_book | living | 看着像但不能用 | 指令要的那本书（旁边有本像的） | 在 | 1 |
| T01 | which_book | bedroom | 看着像但不能用 | 指令要的那本书（旁边有本像的） | 在 | 1 |
| T02 | crowded_use_another | tight_tv | 被占用 | 碗旁那块积木 B（被占着，用别屋的积木） | 不在 | 1 |
| T02 | crowded_use_another | tight_dining | 被占用 | 碗旁那块积木 B（被占着，用别屋的积木） | 不在 | 1 |
| T02 | crowded_use_another | loose | 不用替换 | 按指令（tight: block A with the block from the other room (either on the other), B, the bowl and the rolling pin untouched; loose: any two blocks, the bowl and the pin untouched） | 在 | 1 |
| T02 | third_toy_elsewhere | duck | 缺失 | 第三块积木（没有，去别屋拿小鸭） | 不在 | 1 |
| T02 | third_toy_elsewhere | toy_block | 缺失 | 第三块积木（没有，去别屋拿玩具积木） | 不在 | 1 |
| T02 | tower_for_kid | counter | 不用替换 | 按指令（three blocks in one tower on the near dining table (the kid's), nothing moved） | 在 | 1 |
| T02 | tower_for_kid | study | 不用替换 | 按指令（three blocks in one tower on the near dining table (the kid's), nothing moved） | 在 | 1 |
| T02 | tower_for_kid | near_full | 去处替换 | 近处那张餐桌（摆满了，用另一张餐桌） | 不在 | 1 |
| T02 | tower_for_kid | both_full | 去处替换 | 餐桌（两张都满，只能放别的台面） | 不在 | 0 |
| T02 | tower_for_kid_duck | counter | 缺失 | 第三块积木（没有，用小鸭放最上面） | 不在 | 1 |
| T02 | tower_for_kid_duck | study | 缺失 | 第三块积木（没有，用小鸭放最上面） | 不在 | 1 |
| T02 | block_put_away | in_4 | 缺失 | 第三块木块（收在 4 号矮柜里） | 在 | 1 |
| T02 | block_put_away | in_6 | 缺失 | 第三块木块（收在 6 号矮柜里） | 在 | 1 |
| T02 | block_put_away | gone_toy_block | 缺失 | 第三块木块（家里没有了，用玩具积木代） | 不在 | 1 |
| T02 | block_put_away | gone_duck | 缺失 | 第三块木块（家里没有了，用小鸭代） | 不在 | 1 |
| T03 | small_bin_or_bedroom_bin | wide_in_bedroom | 能力不足 | 宽储物箱（在卧室） | 在 | 1 |
| T03 | small_bin_or_bedroom_bin | basket_in_bedroom | 能力不足 | 宽储物箱（没有，用卧室的收纳筐） | 不在 | 1 |
| T03 | which_bin_by_contents | toys_near | 看着像但不能用 | 装玩具的那个箱子 | 在 | 1 |
| T03 | which_bin_by_contents | kitchen_bin_full | 被占用 | 厨房用品箱（满了） | 不在 | 1 |
| T03 | no_bin_substitute | basket | 缺失 | 储物箱（没有，用收纳筐） | 不在 | 1 |
| T03 | no_bin_substitute | tray | 缺失 | 储物箱（没有，用托盘） | 不在 | 1 |
| T03 | utensils_apart | bin_free | 不用替换 | 按指令（both in the wide bin (the proper storage bin), nothing of anyone else's moved） | 在 | 1 |
| T03 | utensils_apart | bin_full_tray | 被占用 | 空的收纳箱（满了，用托盘） | 不在 | 1 |
| T03 | utensils_apart | bin_full_basket | 被占用 | 空的收纳箱（满了，用收纳筐） | 不在 | 1 |
| T03 | utensils_apart | bin_full_fruit | 被占用 | 空的收纳箱（满了，只有果篮） | 不在 | 0 |
| T04 | cup_available | — | 不用替换 | 按指令（the glass (two for two guests) upright where it belongs） | 在 | 1 |
| T04 | no_cup | — | 缺失 | 玻璃杯（没有，用马克杯） | 不在 | 1 |
| T04 | no_cup | — | 缺失 | 玻璃杯（没有，用收起来的马克杯） | 不在 | 1 |
| T04 | no_cup | alt_dining_table_2 | 缺失 | 玻璃杯（没有，用餐桌上的马克杯） | 不在 | 1 |
| T04 | no_cup | — | 缺失 | 玻璃杯（没有，只有孩子的塑料杯） | 不在 | 0 |
| T04 | clear_the_drinks_spot | spot_dishes | 不用替换 | 按指令（the glass (two for two guests) upright where it belongs） | 在 | 1 |
| T04 | clear_the_drinks_spot | spot_kid_toys | 去处替换 | 放饮料的老地方 | 在 | 1 |
| T04 | two_guests | glass_in_cabinet | 不用替换 | 按指令（the glass (two for two guests) upright where it belongs） | 在 | 1 |
| T04 | two_guests | mug | 缺失 | 两个玻璃杯（只有一个，补马克杯） | 不在 | 1 |
| T04 | two_guests | kid_cup | 缺失 | 两个玻璃杯（只有一个，补塑料杯） | 不在 | 0 |
| T04 | x6_gd_cup_in_cabinets | cup_in_4 | 能力不足 | 玻璃杯（在另一个矮柜里） | 在 | 1 |
| T04 | x6_gd_cup_in_cabinets | plastic_only | 能力不足 | 玻璃杯（没有，只有塑料杯） | 不在 | 1 |
| T05 | no_pen_pencil_away | — | 不用替换 | 按指令（the best the seed offers: what was asked for when it is free, else the stand-in, nothing anyone is using taken, the mug where it belongs） | 在 | 1 |
| T05 | no_pen_pencil_away | — | 被占用 | 铅笔（奶奶正用着，用卧室的笔） | 不在 | 1 |
| T05 | check_desk_first | pen_on_desk | 不用替换 | 按指令（the best the seed offers: what was asked for when it is free, else the stand-in, nothing anyone is using taken, the mug where it belongs） | 在 | 1 |
| T05 | check_desk_first | pencil_on_desk | 看着像但不能用 | 书桌上已有的铅笔 | 在 | 1 |
| T05 | check_desk_first | pen_in_use | 被占用 | 笔（正被用着） | 不在 | 1 |
| T05 | homework_ready | single | 看着像但不能用 | 孩子的作业本 | 在 | 1 |
| T05 | homework_ready | several | 看着像但不能用 | 孩子的作业本 | 在 | 1 |
| T05 | homework_ready | notebook_in_use | 被占用 | 作业本（正被用着） | 不在 | 1 |
| T05 | errand_combined | pen_bedroom | 不用替换 | 按指令（the best the seed offers: what was asked for when it is free, else the stand-in, nothing anyone is using taken, the mug where it belongs） | 在 | 1 |
| T05 | errand_combined | pen_in_use | 被占用 | 笔（正被用着） | 不在 | 1 |
| T05 | x6_gd_pen_or_pencil_cabinets | pen_in_4 | 看着像但不能用 | 笔（在 4 号柜顶上） | 在 | 1 |
| T05 | x6_gd_pen_or_pencil_cabinets | pen_in_use | 被占用 | 笔（正被用着） | 不在 | 1 |
| T06 | free | — | 不用替换 | 按指令（a block (or both) on the low wall cabinet or the TV stand, the hand empty） | 在 | 0 |
| T06 | display_row | cab_free | 不用替换 | 按指令（the best the seed offers: all three in one row on the low cabinet when it has room, else on the TV stand or the other low cabinet; the family's things untouched） | 在 | 1 |
| T06 | display_row | cab_short | 能力不足 | 矮柜顶一排摆开（太短，放不下） | 不在 | 1 |
| T06 | display_spot_or_tv | front_taken | 去处替换 | 矮柜正面那块地方（被占了） | 不在 | 1 |
| T06 | display_spot_or_tv | front_free | 不用替换 | 按指令（the best the seed offers, in view from the room: the cabinet front when free, else the TV stand or the other low cabinet (the other low cabinet when the TV stand is full too); nothing moved） | 在 | 1 |
| T06 | display_spot_or_tv | front_taken_tv_full | 去处替换 | 矮柜正面那块地方（被占了，电视柜也满） | 不在 | 1 |
| T06 | display_spot_or_tv | front_free_block_away | 不用替换 | 按指令（the best the seed offers, in view from the room: the cabinet front when free, else the TV stand or the other low cabinet (the other low cabinet when the TV stand is full too); nothing moved） | 在 | 1 |
| T06 | seen_from_bed | boxes_middle | 不用替换 | 按指令（on the bedside bookcase (its top when it has room, else a lower shelf), the kid's things untouched） | 在 | 1 |
| T06 | seen_from_bed | bookcase_full | 去处替换 | 床头书架顶（被孩子的东西占满，放下层或床边书桌） | 不在 | 1 |
| T07 | microwave_works | — | 不用替换 | 按指令（warmed to 40 C in the microwave only, both off） | 在 | 1 |
| T07 | microwave_broken | — | 看着像但不能用 | 微波炉（坏了，用灶台） | 不在 | 0 |
| T07 | microwave_broken | — | 看着像但不能用 | 微波炉（坏了，用灶台） | 不在 | 0 |
| T07 | microwave_broken | alt_dining_table_2 | 看着像但不能用 | 微波炉（坏了，用灶台） | 不在 | 0 |
| T07 | microwave_holds_pot | — | 被占用 | 微波炉（里面放着锅，用灶台） | 不在 | 1 |
| T07 | vessel_decides_appliance | in_ceramic_bowl | 不用替换 | 按指令（the right appliance from the start, warmed to 40 C, both off） | 在 | 1 |
| T07 | vessel_decides_appliance | in_glass_box | 不用替换 | 按指令（the right appliance from the start, warmed to 40 C, both off） | 在 | 1 |
| T07 | vessel_decides_appliance | in_pot | 能力不足 | 按容器选对的电器 | 在 | 1 |
| T07 | vessel_decides_appliance | in_steel_box | 能力不足 | 按容器选对的电器 | 在 | 1 |
| T07 | vessel_decides_appliance | in_foil_tray | 能力不足 | 按容器选对的电器 | 在 | 1 |
| T07 | two_portions | dining | 不用替换 | 按指令（both at 40 C at the end, each in its own appliance from the start, both off） | 在 | 1 |
| T07 | two_portions | counter | 不用替换 | 按指令（both at 40 C at the end, each in its own appliance from the start, both off） | 在 | 1 |
| T08 | sponge_on_island | — | 不用替换 | 按指令（the island wiped, the sponge back on the island） | 在 | 0 |
| T08 | far_sponge_tv | — | 不用替换 | 按指令（the best the seed offers: the island wiped with the sponge (the spare when the usual one is gone), the sponge back on the island, the kid's cube untouched） | 在 | 1 |
| T08 | far_sponge_tv | — | 看着像但不能用 | 海绵（在电视柜上，岛台上有个像的泡沫块） | 在 | 1 |
| T08 | far_sponge_tv | — | 缺失 | 常用海绵（没有，用托盘里的备用海绵） | 不在 | 1 |
| T08 | wipe_and_sort | blocks | 不用替换 | 按指令（the toys in the toy box, the kitchen things where they were and standing, the island wiped, the sponge on it） | 在 | 1 |
| T08 | wipe_and_sort | duck | 不用替换 | 按指令（the toys in the toy box, the kitchen things where they were and standing, the island wiped, the sponge on it） | 在 | 1 |
| T08 | return_sponge_home | dining | 不用替换 | 按指令（the island wiped, the sponge in the tray, the spare sponge still in it） | 在 | 1 |
| T08 | return_sponge_home | study | 不用替换 | 按指令（the island wiped, the sponge in the tray, the spare sponge still in it） | 在 | 1 |
| T08 | return_sponge_home | far_dining | 不用替换 | 按指令（the island wiped, the sponge in the tray, the spare sponge still in it） | 在 | 1 |
| T08 | which_surface | island | 不用替换 | 按指令（only the used surface wiped, the sponge on the island） | 在 | 1 |
| T08 | which_surface | dining | 不用替换 | 按指令（only the used surface wiped, the sponge on the island） | 在 | 1 |
| T09 | lid_off | — | 不用替换 | 按指令（the tomatoes in the pot at 60 C, stirred, the lid on, the stove off） | 在 | 0 |
| T09 | lid_on_spoon_away | — | 不用替换 | 按指令（the best the seed offers (what is asked for when it is there, else the stand-in: the plate for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 C, stirred, covered, the stove off） | 在 | 1 |
| T09 | lid_on_spoon_away | — | 缺失 | 锅盖（没有，用同样大的盘子盖） | 不在 | 1 |
| T09 | pot_in_use | in_use | 被占用 | 灶上那口锅（装着昨天的汤，用空锅） | 不在 | 1 |
| T09 | pot_in_use | free | 不用替换 | 按指令（the soup in the empty pot, every step done, the full pot untouched） | 在 | 1 |
| T09 | tomato_in_fridge | in_fridge | 不用替换 | 按指令（the best the seed offers (what is asked for when it is there, else the stand-in: the plate for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 C, stirred, covered, the stove off） | 在 | 1 |
| T09 | tomato_in_fridge | big_tomato | 缺失 | 第三颗小番茄（没有，用大番茄） | 不在 | 0 |
| T09 | x6_gd_tomato_elsewhere | dining | 不用替换 | 按指令（the best the seed offers (what is asked for when it is there, else the stand-in: the plate for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 C, stirred, covered, the stove off） | 在 | 1 |
| T09 | x6_gd_tomato_elsewhere | on_plate | 被占用 | 番茄（在别人盘子里） | 不在 | 1 |
| T09 | pot_in_dining_room | pot_away | 不用替换 | 按指令（the best the seed offers (what is asked for when it is there, else the stand-in: the plate for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 C, stirred, covered, the stove off） | 在 | 1 |
| T09 | pot_in_dining_room | spare_pot | 缺失 | 常用的汤锅（不在，用备用锅） | 不在 | 0 |
| T10 | can_on_island | — | 不用替换 | 按指令（the can in the trash can, the hand empty） | 在 | 0 |
| T10 | can_in_dining_room | — | 不用替换 | 按指令（the can found and in the trash can） | 在 | 0 |
| T10 | can_in_dining_room | alt_tv_stand_2 | 不用替换 | 按指令（the can found and in the trash can） | 在 | 0 |
| T10 | keep_kids_can | kid_desk | 被占用 | 喝完的那罐扔掉，孩子的不动 | 在 | 1 |
| T10 | keep_kids_can | kid_island | 被占用 | 喝完的那罐扔掉，孩子的不动 | 在 | 1 |
| T10 | trash_moved | dining | 不用替换 | 按指令（the can in the trash can that has room: the moved one (dining room); when the one by the island is full, the bathroom's, the full one untouched） | 在 | 1 |
| T10 | trash_moved | trash_full | 能力不足 | 垃圾桶（满了） | 不在 | 0 |
| T10 | after_dinner_clear | rubbish_leftovers | 去处替换 | 每样东西各回各处 | 在 | 1 |
| T10 | after_dinner_clear | leftovers_mug | 去处替换 | 每样东西各回各处 | 在 | 1 |
| T10 | after_dinner_clear | rubbish_mug | 去处替换 | 每样东西各回各处 | 在 | 1 |
| T10 | guests_coming | can_mug_block | 去处替换 | 每样东西各回各处 | 在 | 1 |
| T10 | guests_coming | can_block | 去处替换 | 每样东西各回各处 | 在 | 1 |
| T10 | guests_coming | can_mug | 去处替换 | 每样东西各回各处 | 在 | 1 |
| T10 | x6_gd_can_put_away | in_cabinet | 不用替换 | 按指令（the empty can found and in the trash, the unopened can in the fridge untouched） | 在 | 1 |
| T10 | x6_gd_can_put_away | fridge_drink | 看着像但不能用 | 喝完的那罐（冰箱里有罐没开的） | 在 | 1 |
| T11 | fruits_on_table | — | 不用替换 | 按指令（the apple in the fruit basket） | 在 | 1 |
| T11 | basket_missing | — | 缺失 | 果篮（没有，用托盘） | 不在 | 1 |
| T11 | basket_missing | — | 看着像但不能用 | 果篮（没有，原处是个用过的碗） | 不在 | 1 |
| T11 | leave_one_for_kid | apple_orange | 去处替换 | 留一个给孩子，其余拿走 | 在 | 1 |
| T11 | leave_one_for_kid | orange_banana | 去处替换 | 留一个给孩子，其余拿走 | 在 | 1 |
| T11 | leave_one_for_kid | all_three | 去处替换 | 留一个给孩子，其余拿走 | 在 | 1 |
| T11 | fruit_plate_for_guests | tray_in_study | 不用替换 | 按指令（the best the seed offers: a free tray (the small one when it is empty, else the serving tray) with the apple and the orange in front of the guests, the kid's homework untouched） | 在 | 1 |
| T11 | fruit_plate_for_guests | tray_in_use | 被占用 | 托盘（正被用着） | 不在 | 1 |
| T12 | toys_out | — | 不用替换 | 按指令（the car and the duck in the storage basket） | 在 | 0 |
| T12 | duck_in_study | — | 不用替换 | 按指令（both toys in the basket, the duck found） | 在 | 0 |
| T12 | duck_in_study | alt_dining_table_2 | 不用替换 | 按指令（both toys in the basket, the duck found） | 在 | 0 |
| T12 | bins_capacity | side_left_full | 能力不足 | 能装下所有玩具的收纳筐（没有，分到放得下的箱子里） | 不在 | 1 |
| T12 | bins_capacity | side_right_full | 能力不足 | 能装下所有玩具的收纳筐（没有，分到放得下的箱子里） | 不在 | 1 |
| T12 | bins_capacity | apart_full_on_tv | 能力不足 | 能装下所有玩具的收纳筐（没有，分到放得下的箱子里） | 不在 | 1 |
| T12 | bins_capacity | apart_empty_on_desk | 能力不足 | 能装下所有玩具的收纳筐（没有，分到放得下的箱子里） | 不在 | 1 |
| T12 | bins_capacity | half_bin_and_tray | 能力不足 | 能装下所有玩具的收纳筐（没有，分到放得下的箱子里） | 不在 | 1 |
| T12 | bins_capacity | half_bin_and_tray_duck_dining | 能力不足 | 能装下所有玩具的收纳筐（没有，分到放得下的箱子里） | 不在 | 1 |
| T12 | castle_stays | tall_two_loose | 被占用 | 散玩具进筐，城堡不动 | 在 | 1 |
| T12 | castle_stays | short_one_loose | 被占用 | 散玩具进筐，城堡不动 | 在 | 1 |
| T12 | castle_stays | tall_none_loose | 被占用 | 散玩具进筐，城堡不动 | 在 | 1 |
| T13 | dishes_on_tv_stand | — | 不用替换 | 按指令（bowl, cup and spoon together on the dining table, upright） | 在 | 1 |
| T13 | no_cup | — | 缺失 | 杯子（没有，用马克杯） | 不在 | 1 |
| T13 | copy_the_setting | bowl_cup | 去处替换 | 照样摆的那几样 | 在 | 1 |
| T13 | copy_the_setting | plate_bowl_mug_left | 去处替换 | 照样摆的那几样 | 在 | 1 |
| T13 | copy_the_setting | no_cup | 缺失 | 杯子（没有，用马克杯） | 不在 | 1 |
| T13 | finish_the_table | adult_seat | 去处替换 | 缺的那份摆齐 | 在 | 1 |
| T13 | finish_the_table | kid_seat | 去处替换 | 缺的那份摆齐 | 在 | 1 |
| T13 | finish_the_table | adult_and_kid | 去处替换 | 缺的那份摆齐 | 在 | 1 |
| T15 | lid_by_pot | — | 不用替换 | 按指令（the pot covered with its lid） | 在 | 0 |
| T15 | lid_elsewhere | dining | 不用替换 | 按指令（the best the seed offers: the lid when it is free, else a plate from the counter (the lid left on the stew or on someone's bowl)） | 在 | 1 |
| T15 | lid_elsewhere | covering_bowl | 被占用 | 锅盖（盖着别的碗，用盘子） | 不在 | 1 |
| T15 | no_lid | — | 缺失 | 锅盖（没有，用盘子） | 不在 | 1 |
| T15 | lid_in_use | — | 被占用 | 锅盖（正盖着别的锅，用盘子） | 不在 | 1 |
| T16 | box_on_counter | — | 不用替换 | 按指令（the apple in the snack box on his desk） | 在 | 0 |
| T16 | box_in_cabinet | in_cabinet | 不用替换 | 按指令（the best the seed offers: the apple in the snack box on his desk when the box is free, else in the bowl, the box's contents untouched） | 在 | 1 |
| T16 | box_in_cabinet | box_full | 能力不足 | 饭盒（满了） | 不在 | 1 |
| T16 | no_box | — | 缺失 | 饭盒（没有） | 不在 | 1 |
| T16 | box_in_use | — | 被占用 | 饭盒（正被用着） | 不在 | 1 |
| T17 | lid_off | — | 不用替换 | 按指令（hidden in the pot on the stove, the lid on） | 在 | 1 |
| T17 | h_task_lid_elsewhere | — | 不用替换 | 按指令（the best the seed offers: hidden in the empty pot under its lid (a plate when the lid is on the stew); with no lid at hand anywhere out of sight but not in an appliance） | 在 | 1 |
| T17 | h_task_lid_elsewhere | — | 被占用 | 锅盖（盖着炖菜，用盘子） | 不在 | 1 |
| T17 | hide_both | tv_stand | 不用替换 | 按指令（the best the seed offers: hidden in the empty pot under its lid (a plate when the lid is on the stew); with no lid at hand anywhere out of sight but not in an appliance） | 在 | 1 |
| T17 | hide_both | two_pots | 看着像但不能用 | 能藏住的地方（两口锅一样） | 在 | 1 |
| T17 | hide_somewhere | pot_ready | 不用替换 | 按指令（the best the seed offers: hidden in the empty pot under its lid (a plate when the lid is on the stew); with no lid at hand anywhere out of sight but not in an appliance） | 在 | 1 |
| T17 | hide_somewhere | lid_away | 去处替换 | 盖上盖的空锅（盖子被收走了，藏进矮柜） | 不在 | 0 |
| T18 | bowls_in_cabinet | — | 不用替换 | 按指令（two bowls from the low wall cabinet and two spoons on the dining table） | 在 | 0 |
| T18 | bowls_apart | — | 不用替换 | 按指令（both bowls found (the second in the other cabinet) and set with the spoons） | 在 | 0 |
| T18 | one_bowl | glass_box | 缺失 | 两个碗（只有一个，用玻璃盒） | 不在 | 1 |
| T18 | one_bowl | mug | 缺失 | 两个碗（只有一个，用马克杯） | 不在 | 1 |
| T18 | bowl_in_use | tomatoes | 被占用 | 两个干净碗（一个装着剩番茄，用玻璃盒） | 不在 | 1 |
| T18 | bowl_in_use | oatmeal | 被占用 | 两个干净碗（一个装着燕麦，用玻璃盒） | 不在 | 1 |
| T18 | door_stuck | — | 看着像但不能用 | 柜子里的碗（门卡住） | 不在 | 0 |
| T19 | bin_on_bookcase | — | 不用替换 | 按指令（the can and the cube in the recycling bin） | 在 | 0 |
| T19 | m_can_in_dining_room | — | 不用替换 | 按指令（the finished can and the cube in the recycling bin, what is in use or unopened left alone） | 在 | 1 |
| T19 | m_can_in_dining_room | — | 被占用 | 喝完的那罐（旁边那罐有人在喝） | 在 | 1 |
| T19 | lookalike_bin | — | 看着像但不能用 | 回收箱（旁边有个像的箱子） | 在 | 1 |
| T19 | lookalike_bin | alt_tv_stand_2 | 看着像但不能用 | 回收箱（旁边有个像的箱子） | 在 | 1 |
| T19 | x6_gd_can_put_away | in_4 | 不用替换 | 按指令（the finished can and the cube in the recycling bin, what is in use or unopened left alone） | 在 | 1 |
| T19 | x6_gd_can_put_away | juice_full | 看着像但不能用 | 喝完的罐（旁边果汁是满的） | 在 | 1 |
| T20 | bottle_on_cabinet | — | 不用替换 | 按指令（the bottle standing on the breakfast table） | 在 | 0 |
| T20 | m_bottle_on_tv_stand | — | 不用替换 | 按指令（the breakfast bottle standing on the dining table, the bottle in use and the stock left alone） | 在 | 1 |
| T20 | m_bottle_on_tv_stand | — | 被占用 | 早饭那瓶（另一瓶有人在用） | 在 | 1 |
| T20 | x6_gd_bottle_put_away | on_tv_stand | 看着像但不能用 | 早饭那瓶 | 在 | 1 |
| T20 | x6_gd_bottle_put_away | in_bedroom | 看着像但不能用 | 早饭那瓶 | 在 | 1 |
| T14 | e1_book_ready | — | 不用替换 | 按指令（the book on the kid's bookcase） | 在 | 1 |
| T14 | within_kids_reach | set_on_large_shelf_4 | 去处替换 | 孩子够得着的那层 | 在 | 1 |
| T14 | within_kids_reach | set_on_large_shelf_5 | 去处替换 | 孩子够得着的那层 | 在 | 1 |
| T14 | homework_stays | — | 被占用 | 书上架、杯子回厨房，作业不动 | 在 | 1 |
| T14 | whose_book | blue_book | 去处替换 | 他的书 | 在 | 1 |
| T14 | whose_book | paperback | 去处替换 | 他的书 | 在 | 1 |
| T14 | whose_book | both | 去处替换 | 他的书 | 在 | 1 |
| T14 | next_in_series | on_bookcase | 看着像但不能用 | 同一套书的下一本 | 在 | 1 |
| T14 | next_in_series | on_other_bookcase | 看着像但不能用 | 同一套书的下一本 | 在 | 1 |
| T14 | next_in_series | on_tall_shelf | 看着像但不能用 | 同一套书的下一本 | 在 | 1 |
| T21 | tissue_on_tv_stand | — | 不用替换 | 按指令（the tissues on the dining table） | 在 | 0 |
| T21 | which_table | east | 去处替换 | 洒了汤的那张桌 | 在 | 1 |
| T21 | which_table | west | 去处替换 | 洒了汤的那张桌 | 在 | 1 |
| T21 | no_tissue | — | 缺失 | 纸巾（没有，用干海绵） | 不在 | 0 |
| T21 | the_kids_side | kid_north | 去处替换 | 孩子那一侧 | 在 | 1 |
| T21 | the_kids_side | kid_south | 去处替换 | 孩子那一侧 | 在 | 1 |
| T22 | juice_on_table | — | 不用替换 | 按指令（the juice standing in the fridge, a cabinet or on a counter） | 在 | 0 |
| T22 | by_kind | — | 去处替换 | 每样各放各处 | 在 | 1 |
| T22 | eat_now | desk_free | 去处替换 | 他书桌上作业旁边 | 在 | 1 |
| T22 | eat_now | desk_corner | 被占用 | 他书桌上作业旁边（只剩一角空着） | 在 | 1 |
| T22 | not_shopping | — | 看着像但不能用 | 只收买回来的东西 | 在 | 1 |
| T22 | two_spots | — | 去处替换 | 冰的进冰箱，常温的进柜子 | 在 | 1 |
| T22 | tray_elsewhere | orange_in_it | 缺失 | 果篮（没有，用托盘，托盘里有个橙子） | 不在 | 0 |
| T22 | tray_elsewhere | bowls_in_it | 被占用 | 果篮（没有，用托盘，托盘上压着书） | 不在 | 0 |
| T22 | tray_elsewhere | — | 缺失 | 果篮（没有，用岛台上的托盘） | 不在 | 0 |
| T23 | spoon_on_floor | — | 不用替换 | 按指令（the spoon on a kitchen counter or the island） | 在 | 0 |
| T23 | by_kind | toy_box | 去处替换 | 勺子回厨房、积木进玩具箱 | 在 | 1 |
| T23 | by_kind | bin_full | 能力不足 | 玩具盒（满了，用旁边托盘） | 不在 | 1 |
| T23 | belongs_on_floor | no_toy_box | 缺失 | 玩具箱（没有，用托盘） | 不在 | 1 |
| T23 | belongs_on_floor | bin_full | 能力不足 | 玩具盒（满了，用旁边托盘） | 不在 | 1 |
| T23 | dropped_out_of_view | counter_full | 被占用 | 小厨房台面（摆满了，放别的台面） | 不在 | 1 |
| T23 | dropped_out_of_view | no_room_for_bowl | 能力不足 | 小厨房台面（空隙放不下碗，放别的台面） | 不在 | 1 |
| T23 | only_this_room | cabinet_room | 不用替换 | 按指令（the cup with his cups in cabinet 4 -- or, the cabinet full, in the other low cabinet or on a worktop;, the car left） | 在 | 1 |
| T23 | only_this_room | cabinet_full | 能力不足 | 4 号矮柜柜顶他放杯子的地方（满了，放台面或别的矮柜） | 不在 | 1 |
| T23 | dropped_in_two_rooms | shelf_room | 不用替换 | 按指令（the spoon to the kitchen, the book on his bookcase -- or, the bookcase full, on another bookcase or a desk, his books left as they are） | 在 | 1 |
| T23 | dropped_in_two_rooms | shelf_full | 能力不足 | 他的书架（每层都满，小熊放别的书架或床上） | 不在 | 1 |
| T24 | apple_on_table | — | 不用替换 | 按指令（the apple on the study desk） | 在 | 0 |
| T24 | no_apples_for_him | apple_free | 不用替换 | 按指令（something nobody is eating on the desk: the apple when free, else the banana from the basket, someone's plate left alone） | 在 | 1 |
| T24 | no_apples_for_him | apple_in_use | 被占用 | 苹果（在别人盘子里，用果篮的香蕉） | 不在 | 1 |
| T24 | dinner_soon | apple | 看着像但不能用 | 水果（不是零食） | 在 | 1 |
| T24 | dinner_soon | banana | 看着像但不能用 | 水果（不是零食） | 在 | 1 |
| T24 | fruit_out_of_view | apple_in_basket | 不用替换 | 按指令（the fruit found (the apple in the basket, else the banana) on the desk） | 在 | 1 |
| T24 | fruit_out_of_view | basket_empty | 缺失 | 果篮里的水果（空了，用台面上的香蕉） | 不在 | 1 |
| T24 | where_is_he | study | 去处替换 | 有作业的那张书桌 | 在 | 1 |
| T24 | where_is_he | bedroom | 去处替换 | 有作业的那张书桌 | 在 | 1 |
| T24 | two_kids | apple_banana | 不用替换 | 按指令（one thing to eat by each kid's homework, not on it: on his desk, or on the bookcase beside a desk that has no room） | 在 | 1 |
| T24 | two_kids | apple_snacks | 缺失 | 两样水果（只有一个苹果，另一样用零食） | 不在 | 1 |
| T24 | two_kids | desk3_covered | 被占用 | 卧室那个孩子的书桌（摊满作业，放旁边矮书架） | 不在 | 1 |
| T25 | drink_on_island | — | 不用替换 | 按指令（the juice and a cup (or a mug) by the guest） | 在 | 0 |
| T25 | cup_elsewhere | counter_cup | 不用替换 | 按指令（the juice and a cup fit to drink from by the guest: the counter's cup, or a mug when the only cup holds the kid's blocks (that cup left alone)） | 在 | 0 |
| T25 | cup_elsewhere | only_mugs | 缺失 | 能喝的杯子（没有普通杯子，马克杯一样好，11-20） | 在 | 0 |
| T25 | cup_elsewhere | blocks_in_cup | 被占用 | 能喝的杯子（台面杯子装着积木，马克杯一样好，11-20） | 在 | 1 |
| T25 | cold_one | cold_juice | 不用替换 | 按指令（the cold juice from the fridge and a cup by the guest, the warm bottle left） | 在 | 1 |
| T25 | cold_one | cold_soda | 缺失 | 冰果汁（没有，用冰汽水） | 不在 | 1 |
| T25 | drink_in_fridge | juice | 不用替换 | 按指令（the juice from the fridge and a cup by the guest） | 在 | 1 |
| T25 | drink_in_fridge | soda_only | 缺失 | 果汁（冰箱里没有，用汽水） | 不在 | 0 |
| T25 | cups_for_two | one_there | 不用替换 | 按指令（two plain cups by the guests in all (the ones there kept), none extra） | 在 | 1 |
| T25 | cups_for_two | none_one_inside | 缺失 | 两个普通杯子（台面上只有一个，补马克杯） | 不在 | 1 |
| T25 | cups_for_two | none_two_inside | 不用替换 | 按指令（two plain cups by the guests in all (the ones there kept), none extra） | 在 | 1 |
| T25 | cups_for_two | two_there | 不用替换 | 按指令（two plain cups by the guests in all (the ones there kept), none extra） | 在 | 1 |
| T25 | two_guests | two_cups | 不用替换 | 按指令（the juice and two cups by the guests） | 在 | 0 |
| T25 | two_guests | one_cup | 缺失 | 两个能喝的杯子（一个杯子加一个马克杯，一样好，11-20） | 在 | 0 |
| T25 | little_guest | — | 不用替换 | 按指令（the juice and the plastic cup for the child） | 在 | 1 |
| T26 | car_in_living_room | — | 不用替换 | 按指令（the car in his toy basket） | 在 | 0 |
| T26 | whose | shelf_room | 不用替换 | 按指令（his picture book to his bookcase (the one by his bed when his is full), the novel left） | 在 | 1 |
| T26 | whose | shelf_full | 能力不足 | 他的书架（每层都满，放床边那个书架） | 不在 | 1 |
| T26 | scattered | basket | 不用替换 | 按指令（all three in what holds his toys (the basket; or, no basket, his toy bin)） | 在 | 1 |
| T26 | scattered | no_basket | 缺失 | 玩具筐（没有，用书架上的小玩具盒） | 不在 | 1 |
| T26 | where_in_room | basket | 不用替换 | 按指令（the car in the toy basket (no basket: onto his bookcase), the book on his bookcase） | 在 | 1 |
| T26 | where_in_room | waste_bin | 看着像但不能用 | 玩具筐（没有，原处是垃圾桶；小车放书架） | 不在 | 1 |
| T26 | bear_to_bed | top_free | 不用替换 | 按指令（the teddy on his bed or the bookcase by it (a lower level when its top is covered)） | 在 | 1 |
| T26 | bear_to_bed | top_covered | 被占用 | 床边书架顶（摆满书，放他另一个书架顶或床上） | 不在 | 1 |
| T26 | two_bedrooms | room_east | 去处替换 | 有他玩具筐的那间 | 在 | 1 |
| T26 | two_bedrooms | room_south | 去处替换 | 有他玩具筐的那间 | 在 | 1 |
| T27 | rice_on_table | — | 不用替换 | 按指令（every leftover in the fridge） | 在 | 0 |
| T27 | which_is_leftover | — | 看着像但不能用 | 只有剩饭（旁边空外卖盒像剩菜） | 在 | 1 |
| T27 | which_is_leftover | — | 不用替换 | 按指令（only the rice in the fridge, the rest left (empty tray, fruit and cereal, the bowl someone eats from)） | 在 | 1 |
| T27 | which_is_leftover | — | 被占用 | 只有剩饭（那碗有人在吃） | 在 | 1 |
| T27 | two_leftovers | soup_at_seat | 被占用 | 剩饭进冰箱（汤有人在吃，不收） | 在 | 1 |
| T27 | two_leftovers | soup_on_table | 不用替换 | 按指令（the leftovers in the fridge (the soup too, unless someone is eating it)） | 在 | 0 |
| T27 | two_leftovers | soup_on_stove | 不用替换 | 按指令（the leftovers in the fridge (the soup too, unless someone is eating it)） | 在 | 0 |
| T27 | fridge_out_of_view | fridge_free | 不用替换 | 按指令（the rice in the fridge's free part, the stored food left） | 在 | 0 |
| T27 | fridge_out_of_view | fridge_crowded | 被占用 | 冰箱层板（左半边占了，右边还空着） | 在 | 1 |
| T28 | cup_on_counter | — | 不用替换 | 按指令（his cup standing by his bed） | 在 | 0 |
| T28 | which_bed | east | 去处替换 | 有小熊那张床的床边 | 在 | 1 |
| T28 | which_bed | south | 去处替换 | 有小熊那张床的床边 | 在 | 1 |
| T28 | where_his_cup_is | on_counter | 不用替换 | 按指令（his cup by his bed (with no cup of his, a cup of the house), the rest left） | 在 | 1 |
| T28 | where_his_cup_is | in_cabinet | 不用替换 | 按指令（his cup by his bed (with no cup of his, a cup of the house), the rest left） | 在 | 1 |
| T28 | where_his_cup_is | no_kid_cup | 缺失 | 他的塑料杯（家里没有，用家里的杯子） | 不在 | 0 |
| T28 | cup_out_of_view | cup_found | 不用替换 | 按指令（his cup found and by his bed (a lower level or the desk when the top is covered)） | 在 | 1 |
| T28 | cup_out_of_view | side_covered | 被占用 | 床边书架顶（摆满书，放书桌或下一层） | 不在 | 1 |
| T28 | already_there | his_cup | 不用替换 | 按指令（seen it is already there and left it） | 在 | 0 |
| T28 | already_there | wrong_cup | 看着像但不能用 | 他的塑料杯（床边那个是瓷杯） | 在 | 1 |
| T29 | car_on_table | — | 不用替换 | 按指令（the toy car in his toy box） | 在 | 1 |
| T29 | belongs_on_table | — | 不用替换 | 按指令（what does not belong taken away, the bowl and spoon set for the meal left (nothing at all if nothing to clear)） | 在 | 1 |
| T29 | belongs_on_table | no_toy_box | 缺失 | 玩具箱（没有，用托盘） | 不在 | 1 |
| T29 | belongs_on_table | — | 不用替换 | 按指令（what does not belong taken away, the bowl and spoon set for the meal left (nothing at all if nothing to clear)） | 在 | 1 |
| T29 | homework_on_table | desk_free | 不用替换 | 按指令（the homework on a free desk (the study desk; covered: his own desk or bookcase)） | 在 | 1 |
| T29 | homework_on_table | desk_covered | 被占用 | 书房书桌（摊满别人的书，放他卧室书桌） | 不在 | 1 |
| T29 | several | toy_box | 不用替换 | 按指令（the car in the toy box, the can in the trash, the book on a bookcase or shelf） | 在 | 1 |
| T29 | several | bin_full | 能力不足 | 玩具箱（没有，玩具盒满了，用旁边托盘） | 不在 | 1 |
| T29 | which_table | east | 去处替换 | 要吃饭的那张桌 | 在 | 1 |
| T29 | which_table | west | 去处替换 | 要吃饭的那张桌 | 在 | 1 |
| T30 | bowl_on_cabinet | — | 不用替换 | 按指令（a clean bowl on the island by the stove） | 在 | 0 |
| T30 | how_many | three_bowls | 不用替换 | 按指令（three bowls on the island (three spoons at the table)） | 在 | 1 |
| T30 | how_many | two_bowls | 缺失 | 三个碗（只有两个，补马克杯） | 不在 | 1 |
| T30 | bowls_in_cabinet | two_inside | 不用替换 | 按指令（three for the three spoons: bowls (a mug only when the bowls run out)） | 在 | 1 |
| T30 | bowls_in_cabinet | one_inside | 缺失 | 三个碗（只有两个，补马克杯） | 不在 | 1 |
| T30 | bowl_put_away | bowl_inside | 不用替换 | 按指令（a bowl from the cabinet on the island） | 在 | 1 |
| T30 | bowl_put_away | mug_inside | 缺失 | 碗（家里没有，柜里只有盘子和马克杯，用马克杯） | 不在 | 1 |
| T30 | no_bowl | — | 缺失 | 碗（没有，用马克杯） | 不在 | 1 |
| T30 | bowl_not_plate | — | 看着像但不能用 | 干净的碗（旁边是盘子） | 在 | 1 |
| T30 | bowl_not_plate | — | 被占用 | 干净的碗（旁边那碗装着燕麦） | 在 | 1 |
