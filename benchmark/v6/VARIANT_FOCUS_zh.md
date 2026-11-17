# v6 variant 的侧重

每个 variant 按“主要考什么”归到一类。依据是 `tasks.json` 里每个 variant 的 `v6_tracks`（`tracks.py` 标的细标签）：
一个 variant 有多个标签时，按 替代 > 推断 > 数量 > 多步 > 摆放 > 打开找 > 找东西 的顺序取最主要的一个；
`not_in_view`（要先去找）几乎到处都有，只在没有别的标签时才算“找东西”。
例外：T25 `cups_for_two`、T30 `bowls_in_cabinet` 虽带 `resource_absent`，主要考的是数清已有的再补齐，归“数量与目标”。“动作级”一列是工作位置上要临时换做法的（Action + Task）。

| 侧重 | 含义 | variant 数 | episode 数（10 seed） |
|---|---|---|---|
| 对照 | 正常流程能做完，作为其他类别的参照 | 30 | 300 |
| 找东西 | 要拿的东西或要去的地方一开始不在视野里，要先去别处找 | 16 | 160 |
| 打开找 / 放进去 | 东西在柜子、冰箱里，要打开才看得到，或者要放进关着的地方 | 12 | 120 |
| 替代 | 要用的东西没有、坏了、被占着或放不下，要换一个东西 / 地方 / 做法 | 30 | 300 |
| 数量与目标 | 指令没说具体几件、哪几件，要从场景里数出来、补齐，或者看出已经做完了 | 21 | 210 |
| 推断指代 / 规则 | 要从线索判断是哪个、谁的、该放哪，或者按什么规则分 | 36 | 360 |
| 摆放 | 放在哪个位置合适、怎么摆 | 4 | 40 |
| 多件 / 多步安排 | 几件东西或几件事，要安排顺序、顺路一起做 | 4 | 40 |
| 合计 | | 153 | 1530 |

## 按任务

| 任务 | 对照 | 找东西 | 打开找 / 放进去 | 替代 | 数量与目标 | 推断指代 / 规则 | 摆放 | 多件 / 多步安排 |
|---|---|---|---|---|---|---|---|---|
| T01 | 1 |  |  | 1 |  | 3 | 1 |  |
| T02 | 1 | 1 |  | 3 |  |  | 1 |  |
| T03 | 1 | 1 |  | 2 |  | 1 |  |  |
| T04 | 1 |  |  | 3 | 1 |  |  |  |
| T05 | 1 | 1 |  | 1 | 4 |  |  | 1 |
| T06 | 1 |  |  | 1 |  | 1 | 1 |  |
| T07 | 1 |  |  | 4 |  |  |  |  |
| T08 | 1 |  | 1 | 1 |  | 2 |  |  |
| T09 | 1 | 1 | 1 | 3 |  |  |  |  |
| T10 | 1 | 1 |  | 1 | 1 | 3 |  |  |
| T11 | 1 |  |  | 1 |  | 1 |  | 1 |
| T12 | 1 | 1 |  | 1 | 1 | 1 |  |  |
| T13 | 1 |  |  | 1 |  | 2 |  |  |
| T14 | 1 |  |  | 1 |  | 3 |  | 1 |
| T15 | 1 | 1 |  |  |  |  | 1 |  |
| T16 | 1 | 1 |  |  | 1 |  |  |  |
| T17 | 1 |  | 1 | 1 |  |  |  | 1 |
| T18 | 1 |  | 1 |  | 1 |  |  |  |
| T19 | 1 | 1 |  | 1 |  | 1 |  |  |
| T20 | 1 | 1 |  | 1 |  |  |  |  |
| T21 | 1 | 1 | 1 | 1 |  | 2 |  |  |
| T22 | 1 |  | 1 | 1 | 2 | 1 |  |  |
| T23 | 1 | 1 | 1 |  | 2 | 1 |  |  |
| T24 | 1 | 1 |  |  | 1 | 3 |  |  |
| T25 | 1 | 1 | 1 |  | 2 | 2 |  |  |
| T26 | 1 |  | 2 |  | 1 | 2 |  |  |
| T27 | 1 | 1 |  |  | 1 | 1 |  |  |
| T28 | 1 | 1 |  |  | 1 | 2 |  |  |
| T29 | 1 |  | 1 |  |  | 3 |  |  |
| T30 | 1 |  | 1 | 1 | 2 | 1 |  |  |

## 对照（30）

正常流程能做完，作为其他类别的参照。

| 任务 | variant | 细标签 | 动作级 |
|---|---|---|---|
| T01 | `overhang_ready` | - |  |
| T02 | `clear` | - |  |
| T03 | `large_only` | - |  |
| T04 | `cup_available` | - |  |
| T05 | `e1_pencil_asked` | - |  |
| T06 | `free` | - |  |
| T07 | `microwave_works` | - |  |
| T08 | `sponge_on_island` | - |  |
| T09 | `lid_off` | - |  |
| T10 | `can_on_island` | - |  |
| T11 | `fruits_on_table` | - |  |
| T12 | `toys_out` | - |  |
| T13 | `dishes_on_tv_stand` | - |  |
| T14 | `e1_book_ready` | - |  |
| T15 | `book_free` | - |  |
| T16 | `pin_free` | - |  |
| T17 | `lid_off` | - |  |
| T18 | `at_island` | - |  |
| T19 | `bin_on_bookcase` | - |  |
| T20 | `bottle_on_cabinet` | - |  |
| T21 | `tissue_on_tv_stand` | - |  |
| T22 | `juice_on_table` | - |  |
| T23 | `spoon_on_floor` | - |  |
| T24 | `apple_on_table` | - |  |
| T25 | `drink_on_island` | - |  |
| T26 | `car_in_living_room` | - |  |
| T27 | `rice_on_table` | - |  |
| T28 | `cup_on_counter` | - |  |
| T29 | `car_on_table` | - |  |
| T30 | `bowl_on_cabinet` | - |  |

## 找东西（16）

要拿的东西或要去的地方一开始不在视野里，要先去别处找。

| 任务 | variant | 细标签 | 动作级 |
|---|---|---|---|
| T02 | `block_put_away` | not_in_view | 是 |
| T03 | `utensils_apart` | item_out_of_view, not_in_view |  |
| T05 | `no_pen_pencil_away` | not_in_view |  |
| T09 | `lid_on_spoon_away` | not_in_view | 是 |
| T10 | `can_in_dining_room` | not_in_view |  |
| T12 | `duck_in_study` | not_in_view |  |
| T15 | `book_out_of_view` | start_elsewhere |  |
| T16 | `pin_out_of_view` | start_elsewhere |  |
| T19 | `m_can_in_dining_room` | not_in_view |  |
| T20 | `m_bottle_on_tv_stand` | not_in_view |  |
| T21 | `tissue_out_of_view` | not_in_view |  |
| T23 | `dropped_out_of_view` | not_in_view |  |
| T24 | `fruit_out_of_view` | not_in_view |  |
| T25 | `cup_elsewhere` | not_in_view |  |
| T27 | `fridge_out_of_view` | not_in_view |  |
| T28 | `cup_out_of_view` | not_in_view |  |

## 打开找 / 放进去（12）

东西在柜子、冰箱里，要打开才看得到，或者要放进关着的地方。

| 任务 | variant | 细标签 | 动作级 |
|---|---|---|---|
| T08 | `return_sponge_home` | not_in_view, storage_place |  |
| T09 | `tomato_in_fridge` | not_in_view, storage_place | 是 |
| T17 | `hide_somewhere` | storage_place |  |
| T18 | `dishes_spread` | item_put_away |  |
| T21 | `tissue_put_away` | item_put_away |  |
| T22 | `by_kind` | multi_object_goal, storage_place |  |
| T23 | `by_kind` | multi_object_goal, storage_place |  |
| T25 | `drink_in_fridge` | not_in_view, storage_place |  |
| T26 | `bear_to_bed` | storage_place |  |
| T26 | `where_in_room` | multi_object_goal, storage_place |  |
| T29 | `homework_on_table` | multi_object_goal, storage_place |  |
| T30 | `bowl_put_away` | item_put_away |  |

## 替代（30）

要用的东西没有、坏了、被占着或放不下，要换一个东西 / 地方 / 做法。

| 任务 | variant | 细标签 | 动作级 |
|---|---|---|---|
| T01 | `no_room_fallback` | infeasible_fallback, spot_quality | 是 |
| T02 | `crowded_use_another` | infeasible_fallback, not_in_view |  |
| T02 | `third_toy_elsewhere` | missing_piece, not_in_view |  |
| T02 | `tower_for_kid_duck` | item_out_of_view, missing_piece, spot_quality |  |
| T03 | `no_bin_substitute` | container_absent, decoy_destination, not_in_view, small_container_present |  |
| T03 | `small_bin_or_bedroom_bin` | not_in_view, small_container_present |  |
| T04 | `no_cup` | no_cup, not_in_view |  |
| T04 | `two_guests` | missing_piece, not_in_view |  |
| T04 | `x6_gd_cup_in_cabinets` | no_cup |  |
| T05 | `x6_gd_pen_or_pencil_cabinets` | no_pen |  |
| T06 | `display_spot_or_tv` | infeasible_fallback, spot_quality |  |
| T07 | `microwave_broken` | microwave_broken, not_in_view |  |
| T07 | `microwave_holds_pot` | appliance_occupied |  |
| T07 | `two_portions` | appliance_compatibility, multi_object_goal |  |
| T07 | `vessel_decides_appliance` | appliance_compatibility |  |
| T08 | `far_sponge_tv` | start_elsewhere, tool_away_from_surface |  |
| T09 | `pot_in_dining_room` | cookware_choice, not_in_view |  |
| T09 | `pot_in_use` | not_in_view, resource_in_use |  |
| T09 | `x6_gd_tomato_elsewhere` | resource |  |
| T10 | `x6_gd_can_put_away` | resource |  |
| T11 | `basket_missing` | container_absent, decoy_destination |  |
| T12 | `bins_capacity` | joint_capacity |  |
| T13 | `no_cup` | no_cup |  |
| T14 | `within_kids_reach` | agent_ability |  |
| T17 | `h_task_lid_elsewhere` | resource |  |
| T19 | `x6_gd_can_put_away` | resource |  |
| T20 | `x6_gd_bottle_put_away` | resource |  |
| T21 | `no_tissue` | resource_absent |  |
| T22 | `tray_elsewhere` | container_absent, dependent_decisions, not_in_view, storage_place | 是 |
| T30 | `no_bowl` | resource_absent |  |

## 数量与目标（21）

指令没说具体几件、哪几件，要从场景里数出来、补齐，或者看出已经做完了。

| 任务 | variant | 细标签 | 动作级 |
|---|---|---|---|
| T04 | `clear_the_drinks_spot` | destination_occupied, goal_items_unstated |  |
| T05 | `all_pens` | not_in_view, unknown_count |  |
| T05 | `check_desk_first` | goal_already_met |  |
| T05 | `homework_ready` | goal_items_unstated, not_in_view |  |
| T05 | `pens_per_notebook` | count_from_scene, not_in_view |  |
| T10 | `guests_coming` | goal_items_unstated, multi_object_goal |  |
| T12 | `find_all_toys` | goal_items_unstated, multi_object_goal, not_in_view |  |
| T16 | `everything_near_the_edge` | goal_items_unstated, multi_object_goal |  |
| T18 | `enough_for_dinner` | count_against_need |  |
| T22 | `not_shopping` | goal_items_unstated |  |
| T22 | `two_spots` | goal_items_unstated, not_in_view |  |
| T23 | `belongs_on_floor` | goal_items_unstated |  |
| T23 | `dropped_in_two_rooms` | goal_items_unstated, not_in_view |  |
| T24 | `two_kids` | count_from_scene, multi_object_goal |  |
| T25 | `cups_for_two` | count_from_scene, dependent_decisions, item_put_away, resource_absent |  |
| T25 | `two_guests` | count_from_scene, multi_object_goal |  |
| T26 | `scattered` | goal_items_unstated, multi_object_goal |  |
| T27 | `two_leftovers` | goal_items_unstated, multi_object_goal |  |
| T28 | `already_there` | goal_already_met |  |
| T30 | `bowls_in_cabinet` | count_from_scene, dependent_decisions, item_put_away, resource_absent |  |
| T30 | `how_many` | count_from_scene, multi_object_goal |  |

## 推断指代 / 规则（36）

要从线索判断是哪个、谁的、该放哪，或者按什么规则分。

| 任务 | variant | 细标签 | 动作级 |
|---|---|---|---|
| T01 | `reader_seat` | referent_clue, spot_quality | 是 |
| T01 | `homework_on_island` | unsuitable_at_hand, not_in_view |  |
| T01 | `which_table` | destination_unnamed, spot_quality | 是 |
| T03 | `which_bin_by_contents` | decoy_destination, not_in_view |  |
| T06 | `seen_from_bed` | not_in_view, viewer_place |  |
| T08 | `which_surface` | referent_clue |  |
| T08 | `wipe_and_sort` | category_rule, not_in_view |  |
| T10 | `after_dinner_clear` | disposal_by_state, multi_object_goal |  |
| T10 | `keep_kids_can` | not_in_view, referent_clue |  |
| T10 | `trash_moved` | destination_unnamed, not_in_view |  |
| T11 | `leave_one_for_kid` | multi_object_goal, preference_allocation, storage_place |  |
| T12 | `castle_stays` | multi_object_goal, relational_exception |  |
| T13 | `copy_the_setting` | goal_by_example |  |
| T13 | `finish_the_table` | referent_clue, rule_induction |  |
| T14 | `homework_stays` | category_rule, multi_object_goal |  |
| T14 | `next_in_series` | not_in_view, referent_clue |  |
| T14 | `whose_book` | referent_clue, storage_place |  |
| T19 | `lookalike_bin` | decoy_destination, item_out_of_view |  |
| T21 | `the_kids_side` | referent_clue |  |
| T21 | `which_table` | destination_unnamed |  |
| T22 | `eat_now` | preference_allocation |  |
| T23 | `only_this_room` | referent_clue |  |
| T24 | `dinner_soon` | preference_allocation |  |
| T24 | `no_apples_for_him` | preference_allocation |  |
| T24 | `where_is_he` | referent_clue |  |
| T25 | `cold_one` | preference_allocation |  |
| T25 | `little_guest` | preference_allocation |  |
| T26 | `two_bedrooms` | not_in_view, referent_clue |  |
| T26 | `whose` | referent_clue |  |
| T27 | `which_is_leftover` | category_rule, disposal_by_state, referent_clue |  |
| T28 | `where_his_cup_is` | dependent_decisions, item_put_away, referent_clue |  |
| T28 | `which_bed` | referent_clue |  |
| T29 | `belongs_on_table` | category_rule, goal_already_met |  |
| T29 | `several` | category_rule, multi_object_goal |  |
| T29 | `which_table` | destination_unnamed |  |
| T30 | `bowl_not_plate` | referent_clue |  |

## 摆放（4）

放在哪个位置合适、怎么摆。

| 任务 | variant | 细标签 | 动作级 |
|---|---|---|---|
| T01 | `table_seats` | spot_quality | 是 |
| T02 | `tower_for_kid` | item_out_of_view, spot_quality |  |
| T06 | `display_row` | arrangement |  |
| T15 | `flip_on_the_shelf` | not_in_view, workspace_choice |  |

## 多件 / 多步安排（4）

几件东西或几件事，要安排顺序、顺路一起做。

| 任务 | variant | 细标签 | 动作级 |
|---|---|---|---|
| T05 | `errand_combined` | errands_combined |  |
| T11 | `fruit_plate_for_guests` | not_in_view, subgoal_order |  |
| T14 | `stack_them_stably` | multi_object_goal, subgoal_order |  |
| T17 | `hide_both` | multi_object_goal, not_in_view |  |
