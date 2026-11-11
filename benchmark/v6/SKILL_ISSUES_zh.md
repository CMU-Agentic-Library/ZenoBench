# v6 技能侧问题清单（给 muqingj）

整理：2026-11-10。来源：

- `v6full_1109`：muqingj 11-09 晚的全量回归，代码 `1c5b98d`，任务是 bench 的 `8d5c68f`（153 个 episode、全部 s10、`sticky_snap/gt`），结果在 `/data/zenobench/v6full_1109/runs`。
- `benchmark/runs/v6_gtfix_bench`、`v6_reach_fix`、`v6_fix_1110`：11-10 bench 这边的验证（任务版本见各节）。

只列技能侧的问题。bench 侧的问题（GT 路线、goal、布局）都已经在 bench 里修掉，最后一节列出了改过什么，方便对照。每条都有报错原文、受影响的 episode 和复现方法。

复现一个 episode：

```bash
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json --task <TASK> --seed <SEED> \
  --variant <LAYOUT> --route <ROUTE> --planner scripted --profile sticky_snap/gt --out benchmark/runs/repro
```

（`<ROUTE>` 是 `tasks.json` 里 `oracle[<LAYOUT>]` 的值。）

---

## 1. 导航把机器人困住，之后哪儿也去不了（影响最大）

- **报错**：`navigate to <X>: no base path to any of N stand-off poses (even the column's inscribed circle cannot get there)`；`explore_room` 报 `coverage 0.00`。
- **现象**：`navigate(kitchen_island/top)` 成功，停在 **(5.57, 1.26, 15°)**（岛台西侧约 1 m）。下一次 navigate 去任何地方都找不到路，连立柱的内切圆都过不去，说明规划器认为起点被围死了。
  - v6full 里停在这个位姿的 25 次中有 18 次，后面所有导航都失败；停在 (5.54, 1.75)、(5.57, 2.24) 这些位姿的都正常。
  - 能开进去、却规划不出离开的路，怀疑是停车位姿和起点格子的占据/膨胀不一致。
- **影响的 episode（v6full，17 个）**：T01 no_room_fallback / which_book__bedroom / which_table__far_a_flat，T04 clear_the_drinks_spot / x6_gd_cup_in_cabinets__cup_in_4，T06 display_spot_or_tv / free，T08 sponge_on_island / which_surface，T09 lid_off / pot_in_dining_room / tomato_in_fridge / x6_gd_tomato_elsewhere，T10 can_in_dining_room / can_on_island（explore 覆盖 0），T15 book_free，T26 two_bedrooms__room_south（explore bedroom_0_0 覆盖 0）。
- **11-10 复现**：`v6_reach_fix` 里 T09 pot_in_use__in_use s10、T18 enough_for_dinner__two_short s10；`v6_gtfix_bench` 里 T26 two_bedrooms__room_south s10 / s11 / s17。
- **最快复现**：T15 book_free s10（route `nominal`），第 3 步就失败。

## 2. 导航把站位选在墙的另一边

- **报错**：`look at <X>: line of sight blocked (h 0, v 0 deg)`；`search <X>: not seen at [...]`。
- **现象**：`navigate(bookcase_2/top)` 停在 **(0.69, 0.73)**，这是 y = 0 那堵墙的**北侧**，而 bookcase_2 在墙南侧（y −0.62 到 −0.24）。`base_near` 只按距离判断所以通过了，但隔着墙什么也看不到。search 到 bookcase_2 也是同样情况，所以书架上的东西永远找不到。
- **影响的 episode**：
  - look 被挡：T11 fruits_on_table / basket_gone_bowl_there，T13 finish_the_table__adult_seat / no_cup_alternative（v6full）；T13 copy_the_setting（`v6_reach_fix`，看 kitchen_counter_2）；T28 which_bed__east（`v6_gtfix_bench`，看 mattress_2）。
  - search 找不到书架上的东西：T03 utensils_apart，T11 leave_one_for_kid，T15 flip_on_the_shelf，T24 fruit_out_of_view（v6full，目标都在 bookcase_2 上）。
  - T14 往 bookcase_2/top 上放书时报 `no free edge spot`（next_in_series、whose_book），可能也是这个原因，未确认。
- **建议**：选站位时检查站位和目标之间有没有墙（视线或同一房间），或者用 bench 的 `layout.reach_edges` 那样只取能站的边。

## 3. `rotate` 只转手腕，手里的物体不跟着转（11-10 新发现）

- **报错**：`square_object(object=floor_block)`：`POSTCONDITION_FAILED: squared(object=floor_block) is false (yaw off axis 44.9 deg)`。
- **现象**：`square` 里的 `policy_075`（rotate）日志是 `rotate_result requested 0.113 rad, yaw_change 0.0`，三块积木都是 0。前两块本来偏差就小，所以 `square` 判成功了，其实一块都没转。
- **影响的 episode**：T06 display_row__spread s10（`v6_fix_1110`）。goal 和指令都要求摆正，GT 路线是每放一块就 `square` 一次。

## 4. 长家具只在一个站位找

- **报错**：`search cup_counter_b: not seen at ['kitchen_cabinet_5', 'kitchen_counter_2', ...]`。
- **现象**：`SearchObjectPolicy` 对每件家具只导航到一个站位，然后转头看 `_search_aims` 的几个点。kitchen_counter_2 长 2.5 m，杯子离北端 23 cm，从这个站位看不到（T25 cup_elsewhere s10，`v6_gtfix_bench`）。
- bench 这边已经让 seed 不把 search 目标放到长台面两端 0.4 m 以内（`layout.SEARCH_END_M`），所以 bench 不再触发这个问题。但真实场景里东西放在台面尽头，还是会找不到。
- 我试过在 search 里多走一个站位，被 `tools/stop_check.py` 的碰撞审计拦下（COLLISION_PLAN 第 1 节：技能里不许在循环里自己换站位重试），已经撤回（`2a10178`）。这件事需要在规划器层面设计。

## 5. 抓不住柜门把手

- **报错**：`grasp handle kitchen_cabinet_4: no finger contact`；`open kitchen_cabinet_4: handle not grasped, fingers [0.0024, 0.025]`；`no collision-free path to handle_contact: MotionGenStatus.IK_FAIL`；`no collision-free path to open_pre_high: ... DT_EXCEPTION`。
- **影响的 episode（v6full，8 个）**：T02 block_put_away__in_4，T05 x6_gd_pen_or_pencil_cabinets__pen_in_6，T17 hide_somewhere__lid_away，T18 enough_for_dinner__two_short（cabinet_6），T19 x6_gd_can_put_away__in_4，T20 x6_gd_bottle_put_away__in_cabinet_6，T25 cups_for_two__one_there，T30 bowl_put_away。多数是 kitchen_cabinet_4。
- **11-10 复现（`v6_fix_1110`）**：T21 tissue_put_away__in_4 s10、T25 cups_for_two__none_one_inside s11，都是第 7 步 `open(kitchen_cabinet_4)` 报 `no finger contact`。这两条的 bench 侧问题（拿着东西关门）已经修掉，现在只差开柜门。

## 6. thickness_pinch "推到边缘再抓"找不到空的边

- **报错**：`slide to edge: no graspable free edge of <support>`。
- **影响的 episode（v6full，10 个）**：T21 纸巾盒（tissue_box）×4：tissue_on_tv_stand、which_table__east、the_kids_side__kid_north（tv_stand_2）、tissue_out_of_view（desk_1）；T27 剩饭盒（glass_food_container）×4（dining_table_2）；T26 where_in_room 的 kid_book（tv_stand_2）；T13 copy_the_setting 的盘子（kitchen_counter_2，当时离边 38 cm，bench 已挪进可达范围）。
- bench 已经让要拿的东西离能站的边 ≤ 20 cm，四周至少留 3 cm 空隙（`layout.FINGER_M`），但推的方向上要有一段空边，这一点 bench 现在不保证。如果需要，请告诉我推需要多长的空边，我在 seed 里留出来。

## 7. 放不进有门的隔层

- **报错**：`place bought_juice: onto a shelf behind a door is not supported yet (set down from the open side, docs/COLLISION_PLAN.md 6.2)`。
- **影响的 episode**：T22 全部 6 个（果汁放冰箱）。全部 GT 路线里放进冰箱或柜子隔层的约 20 条：T22 8、T27 7、T18 2、T10 2、T17 1。

## 8. 拿得到却报 "no reachable grasp"

- **报错**：`pick <X>: no reachable grasp from any base pose`。
- **台面上的**（bench 静态检查都在离能站的边 20 cm 以内）：T11 fruit_plate_for_guests 的 fruit_tray，T20 bottle_on_cabinet 的 juice_bottle，T24 no_apples_for_him / two_kids 的 snack_banana，T29 several 的 table_book。
- **柜子或冰箱里的**：T10 x6_gd_can_put_away__in_cabinet 的 soda_can，T21 tissue_put_away__in_4 的 tissue，T25 cold_one / drink_in_fridge 的 cold_juice（v6full 时冰箱只开到 75%；`37e2492` 改到 90% 后，11-10 的 T25 cold_one 已经能从冰箱里拿出来，见第 11 节）。
- **地上的**：T23 dropped_out_of_view 的 dropped_spoon。

## 9. 放下时的碰撞和精度

| episode | 报错 |
|---|---|
| T09 pot_in_use__in_use | `place_down: its path collides now at 1/5: world right_held_object 6 mm; ... no collision-free straight` |
| T17 hide_both__dining | uncover 放锅盖：`place_down: its path collides now at 5/5: world right_held_object 1 mm` |
| T02 tower_for_kid_duck__study | 鸭子叠到积木上：`xy err 0.096 m, on support False` |
| T04 two_guests__study | 杯子放下后倾斜 81.3°（goal 的 upright 失败） |
| T24 dinner_soon | 苹果放到 desk_1：`xy err 0.012 m, on support False (bottom at z 0.756)` |
| T01 reader_seat__mug_2 | 书（捏住边缘拿）放下时偏了 6.5 cm、转到 −117°，碰到旁边的碗（goal 的 clear_of 失败） |
| T23 dropped_in_two_rooms | `place dropped_spoon: no spot of 4 on kitchen_counter_2/top reachable` |
| T14 stack_them_stably | `place desk_book_blue: no free edge spot on top:desk_book_green` |

## 10. 其他

| episode | 报错 |
|---|---|
| T07 two_portions__counter | `pick soup_pot: no pinch grasp annotated`，但资产里有 `handle_pinch` 标注 |
| T08 return_sponge_home__study | `wipe kitchen_island/top: no base pose reaches any of 8 free strips` |
| T08 wipe_and_sort__blocks | `face tv_stand_2/top: blocked 4% of the way (base footprint)` |
| T10 after_dinner_clear | `push takeout_tray: object did not move` |
| T15 book_out_of_view | `flip paperback_book: no room on kitchen_island/top to land it turned over` |
| T29 homework_on_table | `push hw_notebook: no base pose reaches a push or a drag clear of its neighbours` |
| T09 lid_on_spoon_away（v5 时期多次） | uncover：`pick pot_lid: not held (lift ≈ 0)`，偶发；11-10 两个布局都成功了 |

## 11. 从冰箱拿出东西后进不了搬运姿态（11-10 新发现）

- **报错**：`navigate_place(tv_stand_2/top)`：`carry_in: the load's bottom at 0.523 m is below 0.550 m; to the carry pose: no collision-free path to the pose (carry tilt held: MotionGenStatus.INVALID_START_STATE_WORLD_COLLISION)`。
- **现象**：T25 cold_one s10（`v6_fix_1110`），`pick(cold_juice)` 从冰箱隔层成功拿起，接着导航时收回搬运姿态，起始状态就被判为碰撞（手还在冰箱里或贴着隔板），规划不出来。应该先沿拿取方向退出冰箱，再收到搬运姿态。

## 12. 地上的东西离得近时 `look` 看不到（11-10 新发现）

- **报错**：`look at living_car: outside frustum (h -0, v -39 deg, 1.4 m)`。
- **现象**：`navigate(living_car)` 停在玩具车旁边，车在地上，相机看它要低头 39°，超出了 `head_pitch_joint` 的限位，`look` 直接失败。在 `sticky_snap/benchmark`（有观测限制）下，看不到就不能 `pick`（NOT_IN_VIEW），所以地上的东西在 benchmark profile 下都拿不了。
- **影响的 episode**：T26 two_bedrooms__room_south s12、s19（`v6_fix_1110`）。凡是 GT 路线要捡地上东西的，换成 benchmark profile 都会碰到（T23 dropped_*、T26 等）。
- **建议**：`look` 遇到俯角超限时弯腰（torso/waist）或后退一步再看；或者 navigate 到地上物体时把站位放远一点，让头能看到。

---

## 附：bench 侧已经修掉的（对照用，不需要改技能）

- 关柜门或冰箱门时手里还拿着东西（24 条路线，如 T30 bowls_in_cabinet）：改成先放下、再回去关门；`oracle_check` 也会查这一条。
- 拿地上的东西前先 `look`（T26 two_bedrooms s12 / s19 的观测限制 NOT_IN_VIEW）。路线已经改了，但 `look` 本身看不到地上的东西，见第 12 节。
- 先看再拿、看另一个房间前先导航过去（T21、T24、T25、T26、T28、T30）。
- 要拿的东西离能站的边 ≤ 20 cm；要抓的东西四周留 3 cm；search 目标不放在长台面两端。
- T26 熊的 GT 改放书架（床架挡着，够不到床面）。T12 鸭子和车改成 `inside`。T05 笔离本子放宽到 15 cm。T17 勺子挪开，不再被锅盖压着。
- 炉灶锅盖（近侧离前沿 8.5 cm）物理上够得到，是静态规则的例外，不需要改。

## 附：11-10 修完后的验证（`benchmark/runs/v6_fix_1110`，12 个 episode）

- 成功 6 个：T05 pens_per_notebook__notebooks_3、T06 seen_from_bed__boxes_corner、T12 bins_capacity__side_left_full、T17 h_task_lid_elsewhere、T25 cup_elsewhere、T30 bowls_in_cabinet__one_inside。
- 失败 6 个，都在技能侧：T06 display_row__spread（第 3 节 rotate）；T21 tissue_put_away__in_4 和 T25 cups_for_two__none_one_inside s11（第 5 节 柜门把手）；T25 cold_one（第 11 节 冰箱搬运）；T26 two_bedrooms__room_south s12、s19（第 12 节 地上 look）。
