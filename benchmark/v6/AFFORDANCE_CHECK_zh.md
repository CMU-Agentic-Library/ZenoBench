# 功能可供性对照检查（物体 + 家具注册表 vs 手写 tier）

由 `python benchmark/v6/affordance_check.py` 生成，不要手改。注册表在 `benchmark/v6/registry/`，判定代码在 `benchmark/v6/object_registry.py`，设计说明见 `OBJECT_REGISTRY_zh.md`。

等级：0 不合法；1 合法但被占用；2+k 合法且空闲、满足 k 个加分项；10 理想物且空闲。手工分是该物体（或台面）第一次出现在角色位置上的那个 tier 的分数，0 表示没有 tier 接受它。

## 总览

- 物体 47 种，家具 45 件（支撑面 116 个），角色 34 个，对照了 154 个（角色, 布局）。
- 发现：illegal_scored 21，order 4，specific_partial 17
- loosen_1124 手写表 61 条：不合法 0，没有角色覆盖 0。

## 手工给了分，但注册表判为不合法（按原标准保留，不改分）

| 角色 | 任务 | 设计 | 内容 | 布局数 |
|---|---|---|---|---:|
| pot_cover | T09 | lid_on_spoon_away | cover_book 得 0.3：does not cover handled_cooking_pot | 1 |
| pot_cover | T09 | lid_on_spoon_away | cover_book 得 0.6：does not cover handled_cooking_pot | 1 |
| pot_cover | T15 | lid_elsewhere | cover_book 得 0.3：does not cover handled_cooking_pot | 1 |
| pot_cover | T15 | no_lid | cover_book 得 0.6：does not cover handled_cooking_pot | 1 |
| soup_bowl_extra | T30 | bowls_in_cabinet | plate_counter_a 得 0.3：lacks hold_liquid | 2 |
| soup_bowl_extra | T30 | bowls_in_cabinet | plate_counter_b 得 0.3：lacks hold_liquid | 2 |
| soup_bowl_extra | T30 | how_many | plate_counter_a 得 0.3：lacks hold_liquid | 2 |
| soup_bowl_extra | T30 | how_many | plate_counter_b 得 0.3：lacks hold_liquid | 2 |
| soup_bowl_one | T30 | bowl_not_plate | spare_plate 得 0.3：lacks hold_liquid | 1 |
| soup_bowl_one | T30 | bowl_put_away | plate_counter_a 得 0.3：lacks hold_liquid | 2 |
| soup_bowl_one | T30 | bowl_put_away | plate_counter_b 得 0.3：lacks hold_liquid | 2 |
| soup_bowl_one | T30 | bowl_put_away | stored_plate 得 0.3：lacks hold_liquid | 1 |
| soup_bowl_one | T30 | no_bowl | spare_plate 得 0.6：lacks hold_liquid | 1 |
| soup_vessel | T18 | one_bowl | plate_counter_a 得 0.6：lacks hold_liquid | 2 |

## 排序和功能等级相反（按原标准保留）

| 角色 | 任务 | 设计 | 内容 | 布局数 |
|---|---|---|---|---:|
| guest_glass | T04 | x6_gd_cup_in_cabinets | mug_counter（合法 3）得 0.6 < kid_cup（合法 2）得 1.0 | 1 |
| guest_glass | T04 | x6_gd_cup_in_cabinets | mug_dining_cabinet（合法 3）得 0.6 < kid_cup（合法 2）得 1.0 | 1 |
| guest_glass | T04 | x6_gd_cup_in_cabinets | mug_shelf（合法 3）得 0.6 < kid_cup（合法 2）得 1.0 | 1 |
| guest_glass | T04 | x6_gd_cup_in_cabinets | mug（合法 3）得 0.6 < kid_cup（合法 2）得 1.0 | 1 |

## 点名要的东西，别的东西仍拿部分分（设计如此，记录）

| 角色 | 任务 | 设计 | 内容 | 布局数 |
|---|---|---|---|---:|
| asked_book | T01 | which_book | book_island 得 0.6 | 2 |
| asked_book | T01 | which_book | book_other 得 0.6 | 2 |
| his_cup | T28 | where_his_cup_is | counter_mug 得 0.6 | 2 |
| his_cup | T28 | where_his_cup_is | cup_counter_b 得 0.6 | 2 |
| next_book | T14 | next_in_series | blue_book_case 得 0.3 | 3 |
| next_book | T14 | next_in_series | green_book_case 得 0.3 | 3 |
| next_book | T14 | next_in_series | paperback_shelf 得 0.3 | 3 |

## 加热电器和容器材质不配

无。

## 合法但没有 tier 接受（只记录，不应用；按原标准）

| 角色 | 任务 | 设计 | 候选（等级） | 布局数 |
|---|---|---|---|---:|
| bedside_spot | T06 | seen_from_bed | large_shelf_4/shelf_0（合法 2）, large_shelf_4/shelf_4（合法 2） | 2 |
| cup_return | T23 | only_this_room | kitchen_cabinet_1/inside_bottom（合法 2）, kitchen_cabinet_1/inside_shelf（合法 2）, kitchen_cabinet_1/top（合法 2）, kitchen_cabinet_2/inside_bottom（合法 2）, kitchen_cabinet_2/inside_shelf（合法 2）, kitchen_cabinet_2/top（合法 2）, kitchen_cabinet_3/inside_bottom（合法 2）, kitchen_cabinet_3/inside_shelf（合法 2） 等 14 个 | 2 |
| dining_place | T02 | tower_for_kid | dining_table_2/top（合法 2） | 1 |
| display_spot | T06 | display_row | cabinet_2/top（合法 2） | 2 |
| display_spot | T06 | display_spot_or_tv | cabinet_2/top（合法 2） | 4 |
| fruit_holder | T11 | basket_missing | bowl_dining_cabinet（合法 3）, bowl_inside_kitchen_cabinet（合法 3）, bowl_kitchen_cabinet（合法 3）, bowl_side_table（合法 3） | 1 |
| fruit_holder | T11 | basket_missing | bowl_dining_cabinet（合法 3）, bowl_inside_kitchen_cabinet（合法 3）, bowl_side_table（合法 3） | 1 |
| fruit_holder | T11 | fruits_on_table | bowl_dining_cabinet（合法 3）, bowl_inside_kitchen_cabinet（合法 3）, bowl_kitchen_cabinet（合法 3）, bowl_side_table（合法 3） | 1 |
| fruit_put_away | T11 | basket_missing | breakfast_fridge/inside_shelf（合法 2）, kitchen_cabinet_3/inside_bottom（合法 2）, kitchen_cabinet_3/inside_shelf（合法 2） | 2 |
| fruit_put_away | T11 | fruits_on_table | breakfast_fridge/inside_shelf（合法 2）, kitchen_cabinet_3/inside_bottom（合法 2）, kitchen_cabinet_3/inside_shelf（合法 2） | 1 |
| fruit_put_away | T22 | tray_elsewhere | kitchen_cabinet_1/inside_bottom（合法 2）, kitchen_cabinet_1/inside_shelf（合法 2）, kitchen_cabinet_2/inside_bottom（合法 2）, kitchen_cabinet_2/inside_shelf（合法 2）, kitchen_cabinet_3/inside_bottom（合法 2）, kitchen_cabinet_3/inside_shelf（合法 2）, kitchen_cabinet_4/inside_bottom（合法 2）, kitchen_cabinet_5/inside_bottom（合法 2） 等 10 个 | 3 |
| kid_book_shelf | T26 | whose | bookcase_2/shelf_0（合法 3）, bookcase_2/shelf_1（合法 3）, bookcase_2/top（理想）, cell_shelf_5/shelf_0（合法 3）, cell_shelf_5/top（合法 3） | 1 |
| kid_book_shelf | T26 | whose | cell_shelf_5/shelf_0（合法 3）, cell_shelf_5/top（合法 3）, desk_3/top（合法 2）, large_shelf_4/shelf_0（合法 3）, large_shelf_4/shelf_1（合法 3）, large_shelf_4/shelf_2（合法 3）, large_shelf_4/shelf_3（合法 3）, large_shelf_4/shelf_4（合法 3） 等 12 个 | 1 |
| kid_drink_vessel | T25 | little_guest | cup_counter_b（合法 2）, cup_kitchen_cabinet（合法 2）, cup_side_table（合法 2）, mug_counter（合法 2）, mug_dining_cabinet（合法 2）, mug_shelf（合法 2） | 1 |
| kid_shelf | T14 | within_kids_reach | cell_shelf_1/shelf_0（合法 3）, cell_shelf_1/top（合法 3）, cell_shelf_2/shelf_0（合法 3）, cell_shelf_2/top（合法 3）, cell_shelf_3/shelf_0（合法 3）, cell_shelf_3/shelf_1（合法 3）, cell_shelf_3/shelf_2（合法 2）, cell_shelf_3/top（合法 2） 等 13 个 | 2 |
| kitchen_top_return | T23 | dropped_out_of_view | kitchen_cabinet_1/top（合法 2）, kitchen_cabinet_2/top（合法 2）, kitchen_cabinet_3/top（合法 2）, kitchen_cabinet_4/top（合法 2）, kitchen_cabinet_5/top（合法 2）, kitchen_cabinet_6/top（合法 2） | 1 |
| pot_cover | T17 | h_task_lid_elsewhere | plate_counter_a（合法 3）, plate_counter_b（合法 3）, plate_dining_cabinet（合法 3）, plate_inside_kitchen_cabinet（合法 3） | 1 |
| soup_bowl_extra | T30 | bowls_in_cabinet | cup_counter_b（合法 2）, cup_kitchen_cabinet（合法 2）, cup_side_table（合法 2）, mug_counter（合法 2）, mug_dining_cabinet（合法 2）, mug_shelf（合法 2） | 1 |
| soup_bowl_extra | T30 | how_many | cup_counter_b（合法 2）, cup_kitchen_cabinet（合法 2）, cup_side_table（合法 2）, mug_counter（合法 2）, mug_dining_cabinet（合法 2）, mug_shelf（合法 2） | 1 |
| soup_bowl_one | T30 | bowl_not_plate | cup_counter_b（合法 2）, cup_kitchen_cabinet（合法 2）, cup_side_table（合法 2）, mug_counter（合法 2）, mug_dining_cabinet（合法 2）, mug_shelf（合法 2） | 2 |
| soup_bowl_one | T30 | bowl_put_away | cup_counter_b（合法 2）, cup_kitchen_cabinet（合法 2）, cup_side_table（合法 2）, mug_counter（合法 2）, mug_dining_cabinet（合法 2）, mug_shelf（合法 2） | 1 |
| soup_vessel | T18 | bowl_in_use | cup_counter_b（合法 2）, cup_kitchen_cabinet（合法 2）, cup_side_table（合法 2）, mug_counter（合法 2）, mug_dining_cabinet（合法 2）, mug_shelf（合法 2） | 2 |
| soup_vessel | T18 | one_bowl | cup_counter_b（合法 2）, cup_kitchen_cabinet（合法 2）, cup_side_table（合法 2） | 1 |
| soup_vessel | T18 | one_bowl | cup_counter_b（合法 2）, cup_kitchen_cabinet（合法 2）, cup_side_table（合法 2）, mug_counter（合法 2）, mug_dining_cabinet（合法 2）, mug_shelf（合法 2） | 1 |

## loosen_1124 手写表 vs 注册表

| 表 | 任务 | 从 / 设计 | 到 | 角色 | 合法 | 原因 |
|---|---|---|---|---|---|---|
| SUBSTITUTE_KINDS | T09 | lid_plate | breakfast_plate | pot_cover | 是 |  |
| SUBSTITUTE_KINDS | T13 | bowl | breakfast_bowl | table_bowl | 是 |  |
| SUBSTITUTE_KINDS | T13 | cup | breakfast_cup | table_drink_vessel | 是 |  |
| SUBSTITUTE_KINDS | T13 | mug | breakfast_mug | table_drink_vessel | 是 |  |
| SUBSTITUTE_KINDS | T15 | plate_counter_a | breakfast_plate | pot_cover | 是 |  |
| SUBSTITUTE_KINDS | T15 | plate_counter_b | breakfast_plate | pot_cover | 是 |  |
| SUBSTITUTE_KINDS | T16 | spare_bowl | breakfast_bowl | lunch_container | 是 |  |
| SUBSTITUTE_KINDS | T17 | cover_plate | breakfast_plate | pot_cover | 是 |  |
| SUBSTITUTE_KINDS | T18 | spare_mug | breakfast_mug | soup_vessel | 是 |  |
| SUBSTITUTE_KINDS | T18 | spare_mug | breakfast_bowl | soup_vessel | 是 |  |
| SUBSTITUTE_KINDS | T18 | glass_box | breakfast_bowl | soup_vessel | 是 |  |
| PLACES | T13 | dishes_on_tv_stand | dining_table_1/top | dining_place | 是 |  |
| PLACES | T13 | dishes_on_tv_stand | dining_table_2/top | dining_place | 是 |  |
| PLACES | T13 | no_cup | dining_table_1/top | dining_place | 是 |  |
| PLACES | T13 | no_cup | dining_table_2/top | dining_place | 是 |  |
| PLACES | T18 | * | dining_table_1/top | soup_table | 是 |  |
| PLACES | T18 | * | dining_table_2/top | soup_table | 是 |  |
| PLACES | T20 | * | dining_table_1/top | dining_place | 是 |  |
| PLACES | T20 | * | dining_table_2/top | dining_place | 是 |  |
| PLACES | T21 | tissue_on_tv_stand | dining_table_1/top | dining_place | 是 |  |
| PLACES | T21 | tissue_on_tv_stand | dining_table_2/top | dining_place | 是 |  |
| PLACES | T21 | no_tissue | dining_table_1/top | dining_place | 是 |  |
| PLACES | T21 | no_tissue | dining_table_2/top | dining_place | 是 |  |
| PLACES | T30 | * | dining_table_1/top | soup_serving_place | 是 |  |
| PLACES | T30 | * | dining_table_2/top | soup_serving_place | 是 |  |
| PLACES | T30 | * | kitchen_island/top | soup_serving_place | 是 |  |
| PLACES | T25 | drink_on_island | tv_stand_1/top | guest_drink_place | 是 |  |
| PLACES | T25 | drink_on_island | tv_stand_2/top | guest_drink_place | 是 |  |
| PLACES | T25 | cup_elsewhere | tv_stand_1/top | guest_drink_place | 是 |  |
| PLACES | T25 | cup_elsewhere | tv_stand_2/top | guest_drink_place | 是 |  |
| PLACES | T25 | cold_one | tv_stand_1/top | guest_drink_place | 是 |  |
| PLACES | T25 | cold_one | tv_stand_2/top | guest_drink_place | 是 |  |
| PLACES | T25 | drink_in_fridge | tv_stand_1/top | guest_drink_place | 是 |  |
| PLACES | T25 | drink_in_fridge | tv_stand_2/top | guest_drink_place | 是 |  |
| PLACES | T25 | two_guests | tv_stand_1/top | guest_drink_place | 是 |  |
| PLACES | T25 | two_guests | tv_stand_2/top | guest_drink_place | 是 |  |
| PLACES | T25 | little_guest | tv_stand_1/top | guest_drink_place | 是 |  |
| PLACES | T25 | little_guest | tv_stand_2/top | guest_drink_place | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_1/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_1/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_2/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_2/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_4/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_4/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_5/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_5/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_6/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | fruits_on_table | kitchen_cabinet_6/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_1/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_1/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_2/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_2/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_4/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_4/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_5/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_5/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_6/inside_bottom | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T11 | basket_missing | kitchen_cabinet_6/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T22 | tray_elsewhere | breakfast_fridge/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T22 | tray_elsewhere | kitchen_cabinet_4/inside_shelf | fruit_put_away | 是 |  |
| ATOM_ALTERNATIVES | T22 | tray_elsewhere | kitchen_cabinet_6/inside_shelf | fruit_put_away | 是 |  |

## 每个角色

| 角色 | 类型 | 必需 | 加分 | 约束 | 理想 | 家里合法的物体种类 | 对照布局数 |
|---|---|---|---|---|---|---|---:|
| tower_piece | object | stack_top | play, stack_on |  | wooden_block | wooden_block, toy_block, foam_cube, rubber_duck, kitchen_sponge | 8 |
| utensil_storage | object | contain_solid 之一：store_items/carry_multiple | store_items | fits=rolling_pin | wide_storage_bin | fruit_basket, storage_basket, small_storage_bin, wide_storage_bin, toy_box, serving_tray, shallow_sorting_tray | 8 |
| guest_glass | object | drink_from | not:for_kids |  | breakfast_cup | breakfast_cup, breakfast_mug, plastic_cup | 10 |
| writing_tool | object | write |  |  | pen, pencil | pen, pencil | 4 |
| wiper | object | wipe |  |  | kitchen_sponge | kitchen_sponge, tissue_box | 3 |
| pot_cover | object | cover_opening | food_safe, not:breakable | covers=handled_cooking_pot | pot_lid | breakfast_plate, pot_lid, serving_tray, shallow_sorting_tray, book_red, book_green, book_blue, paperback_book, notebook | 8 |
| cooking_pot | object | cook_in |  | fits=cherry_tomato_1 | handled_cooking_pot | handled_cooking_pot, soup_pot | 4 |
| soup_ingredient | object | edible |  | taxonomy_any=['vegetable'] | cherry_tomato | cherry_tomato, big_tomato | 2 |
| rubbish_bin | object | dispose |  | fits=soda_can | trash_can | trash_can, big_trash_can | 2 |
| fruit_holder | object | contain_solid 之一：carry_multiple/serve_food/store_items | carry_multiple, food_safe | fits=apple | fruit_basket | breakfast_bowl, oatmeal_bowl, glass_food_container, fruit_basket, storage_basket, small_storage_bin, wide_storage_bin, toy_box, serving_tray, shallow_sorting_tray | 3 |
| table_drink_vessel | object | drink_from | not:for_kids |  | breakfast_cup | breakfast_cup, breakfast_mug, plastic_cup | 2 |
| table_bowl | object | serve_food, contain_solid |  |  | breakfast_bowl | breakfast_bowl, oatmeal_bowl, glass_food_container | 2 |
| lunch_container | object | contain_solid 之一：store_items/serve_food | portable, food_safe | fits=school_apple | small_storage_bin | breakfast_bowl, oatmeal_bowl, glass_food_container, storage_basket, small_storage_bin, wide_storage_bin, toy_box, shallow_sorting_tray | 4 |
| soup_vessel | object | hold_liquid 之一：serve_food/drink_from | serve_food, taxonomy:dish |  | breakfast_bowl | breakfast_bowl, oatmeal_bowl, breakfast_cup, breakfast_mug, plastic_cup, glass_food_container | 4 |
| soup_bowl_extra | object | hold_liquid 之一：serve_food/drink_from | serve_food, taxonomy:dish |  | breakfast_bowl | breakfast_bowl, oatmeal_bowl, breakfast_cup, breakfast_mug, plastic_cup, glass_food_container | 4 |
| soup_bowl_one | object | hold_liquid 之一：serve_food/drink_from | serve_food, taxonomy:dish |  | breakfast_bowl | breakfast_bowl, oatmeal_bowl, breakfast_cup, breakfast_mug, plastic_cup, glass_food_container | 5 |
| snack | object | edible | taxonomy:fruit |  | apple | apple, banana, orange, cherry_tomato, big_tomato, cereal_box, snack_carton | 4 |
| kid_drink_vessel | object | drink_from | not:breakable |  | plastic_cup | breakfast_cup, breakfast_mug, plastic_cup | 1 |
| toy_storage | object | store_items |  | fits=living_car | storage_basket | storage_basket, small_storage_bin, wide_storage_bin, toy_box, shallow_sorting_tray | 2 |
| dining_place | place | dining_surface |  |  |  |  | 12 |
| soup_table | place | dining_surface |  |  |  |  | 7 |
| soup_serving_place | place | serve_meal |  |  | kitchen_island/top |  | 10 |
| guest_drink_place | place | living_serve |  |  |  |  | 11 |
| fruit_put_away | place |  之一：kitchen_storage/store_food_cold |  |  |  |  | 6 |
| display_spot | place | display |  | room_of=kitchen_cabinet_4/top |  |  | 6 |
| bedside_spot | place |  之一：support_items/store_open | display | near=['bookcase_3/top', 3.2] | bookcase_3/top |  | 2 |
| kid_shelf | place | store_books | kid_reach |  |  |  | 2 |
| kitchen_top_return | place | food_prep |  | ideal_unavailable=['counter_full', 'no_room_for_bowl'] | kitchen_counter_2/top |  | 1 |
| cup_return | place |  之一：food_prep/kitchen_storage |  | ideal_unavailable=['cabinet_full'] | kitchen_cabinet_4/top |  | 2 |
| kid_book_shelf | place |  之一：store_books/work_surface | store_books | room_of=bookcase_2/top | bookcase_2/top |  | 2 |
| heating_appliance | appliance |  之一：heat_microwave/heat_stove |  |  |  |  | 5 |
| asked_book | specific |  |  |  | paperback_book |  | 2 |
| his_cup | specific |  |  |  | plastic_cup |  | 3 |
| next_book | specific |  |  |  | book_red |  | 3 |
