# v6 成功条件统一放宽（2026-11-24）

第一轮 VLM 基线复查后，用户定的标准：只看物体状态，不看机器人最后的姿态；凡是合理理解指令的做法都算对。实现在 `benchmark/v6/loosen_1124.py`，由 `define_tasks_v6.build()` 在 11-20 的放宽之后调用，作用于任务目标、每个布局的目标和每个得分档。

| 规则 | 内容 | 受影响的布局 |
|---|---|---:|
| 1 | 删除 `hand_empty`（结束时手是否空着不再计入） | 311 |
| 2 | `near_start`（别的东西没被挪动）容差至少 10 cm，只抓故意挪开的情况 | 129 |
| 3 | `is_closed`（门要关上）只在指令写了 close 时保留 | 55 |
| 4 | 替代物只认某一个具体物体的，改为同类的空闲物体都算（见下表） | 23 |
| 5 | 指令没限定的目的地，所有合适的地方都算：两张餐桌；T30 的碗送到岛台或餐桌；T25 两个电视柜；T11/T22 苹果放进柜子或冰箱也算收好 | 43 |
| 6 | 11-20 的通用说明文字，以及 ideal 不在场的布局的满分说明，按实际条件重写；每个得分档新增 `check` 字段，给出条件的简写 | 316 |

规则 4、5 有两道保护：
- 只放宽"拿来替代的东西"（容器、盖子、餐具），不放宽任务本身要处理的物体。例如掉在地上的那把勺子，不会因为柜台上本来就有别的勺子而算完成。
- 新加的一种做法如果在开局状态下就已经满足，就不加。例如 T30 有一个碗开局就在餐桌上，所以"碗在餐桌上"这种做法只对另外几个碗成立。

## 检查结果（全部通过）

- **只放宽、没收紧**：放宽前的每一种成功方式，在新条件下仍然成立（逐个布局、逐个得分档核对）。
- **规则执行到位**：没有残留的 `hand_empty`；没有指令不要求时的 `is_closed`；没有小于 10 cm 的 `near_start`。新增测试 `test_loosen_1124_rules` 守住这三条。
- **没有低档和高档重合**：没有哪个低档在放宽后和高档条件变得一样。
- **满分可达**：所有满分档引用的物体在种子 10–19 的场景里都存在。
- **静态校验**：`validate_v6.py`，151 个设计、1,510 局，0 问题。
- **符号回放**：`oracle_check.py` 回放 316 条参考路线，全部通过。
- **测试**：`benchmark/v6/tests` 加 `benchmark/tests` 共 709 个通过（同日接入注册表后为 782 个）。新增 `test_loosen_1124_applied`，断言 `tasks.json` 等于"放宽前的生成结果再过一遍 loosen_1124"。原来比较评分源的测试，改为对放宽前的那一步断言。
- **替代路线不越级**：`test_ideal_outscores_substitute` 仍然通过，即 ideal 在场时，走替代路线拿不到满分。

## 同日补正：T22 `basket_missing` 漏放宽

接入物体注册表时，新测试 `test_loosen_keys_name_real_designs` 发现规则 5 有一条没生效：`basket_missing` 是 T22 设计 `tray_elsewhere` 下的一个布局名，不是设计名，按设计匹配时这条永远匹配不上。现在把它的条件 `inside(bought_apple, fruit_tray)` 并到 `tray_elsewhere` 下面，这个布局的苹果放进冰箱或柜子也算收好。T11 那条同样写成了布局名，但所在设计已经覆盖，删掉后生成结果不变。重新生成后只有这一个布局变了；单调性、静态校验和符号回放都重新跑过，全部通过。

## 各布局放宽后的替代物

| 任务 | 布局 | 原来只认 | 现在也算 |
|---|---|---|---|
| T09 | `lid_on_spoon_away` | `lid_plate` | `plate_counter_a`, `plate_counter_b`, `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T09 | `lid_missing` | `lid_plate` | `plate_counter_a`, `plate_counter_b`, `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T13 | `dishes_on_tv_stand` | `bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T13 | `dishes_on_tv_stand` | `cup` | `cup_counter_b`, `cup_kitchen_cabinet`, `cup_side_table` |
| T13 | `dishes_on_tv_stand` | `mug` | `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T13 | `no_cup` | `bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T13 | `no_cup` | `cup` | `cup_counter_b`, `cup_kitchen_cabinet`, `cup_side_table` |
| T13 | `no_cup` | `mug` | `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T13 | `copy_the_setting__bowl_cup` | `bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T13 | `copy_the_setting__bowl_cup` | `cup` | `cup_counter_b`, `cup_kitchen_cabinet`, `cup_side_table` |
| T13 | `copy_the_setting__bowl_cup` | `mug` | `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T13 | `copy_the_setting__plate_bowl_mug_left` | `bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T13 | `copy_the_setting__plate_bowl_mug_left` | `cup` | `cup_counter_b`, `cup_kitchen_cabinet`, `cup_side_table` |
| T13 | `copy_the_setting__plate_bowl_mug_left` | `mug` | `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T13 | `copy_the_setting__no_cup` | `bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T13 | `copy_the_setting__no_cup` | `mug` | `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T13 | `finish_the_table__adult_seat` | `bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T13 | `finish_the_table__adult_seat` | `mug` | `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T13 | `finish_the_table__kid_seat` | `bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T13 | `finish_the_table__kid_seat` | `mug` | `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T13 | `finish_the_table__adult_and_kid` | `bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T13 | `finish_the_table__adult_and_kid` | `mug` | `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T15 | `lid_elsewhere__dining` | `plate_counter_a` | `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T15 | `lid_elsewhere__dining` | `plate_counter_b` | `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T15 | `lid_elsewhere__covering_bowl` | `plate_counter_a` | `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T15 | `lid_elsewhere__covering_bowl` | `plate_counter_b` | `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T15 | `no_lid` | `plate_counter_a` | `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T15 | `no_lid` | `plate_counter_b` | `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T15 | `lid_in_use` | `plate_counter_a` | `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T15 | `lid_in_use` | `plate_counter_b` | `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T16 | `box_in_cabinet__in_cabinet` | `spare_bowl` | `bowl_dining_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T16 | `box_in_cabinet__box_full` | `spare_bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T16 | `no_box` | `spare_bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T16 | `box_in_use` | `spare_bowl` | `bowl_dining_cabinet`, `bowl_inside_kitchen_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T17 | `hide_lid_in_use` | `cover_plate` | `plate_counter_a`, `plate_counter_b`, `plate_dining_cabinet`, `plate_inside_kitchen_cabinet` |
| T18 | `one_bowl__glass_box` | `glass_box` | `bowl_dining_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T18 | `one_bowl__mug` | `spare_mug` | `bowl_dining_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table`, `mug_counter`, `mug_dining_cabinet`, `mug_shelf` |
| T18 | `bowl_in_use__tomatoes` | `glass_box` | `bowl_dining_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |
| T18 | `bowl_in_use__oatmeal` | `glass_box` | `bowl_dining_cabinet`, `bowl_kitchen_cabinet`, `bowl_side_table` |

## 注意

- 评分是在仿真结束时按 `tasks.json` 判定的。在这次改动之前跑完的结果（包括 Jeong 那批 Sim 6 的 253 局、muqingj 的全量）用的是旧标准，需要按新的 `tasks.json` 重新判定，或者重跑。
- `drops_fail`（相关物体掉到地上就算失败）属于物体状态，没有改。

