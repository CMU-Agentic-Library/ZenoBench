# 暂时排除出统计的 v6 episode（物理 policy 做不到）

2026-11-15 整理，11-16 更新（bench 侧改布局 / 设计后 sim 重跑）。依据：v6 全量跑 1109 / 1111 / 1112 / 1113 / 1115（1115 跑到 102/153 停止，
`/data/zenobench/v6full_1115/runs`），以及 11-14 的候选手臂图（`/data/zenobench/nograsp_1114/png`）。

这些 variation 失败的原因是**物体的摆放或物体本身超出了当前物理 policy 的能力**（柜内空间、
高度、夹爪开口、缺抓取方式），不是规划或感知代码的 bug。在 policy 补上对应能力之前，从 v6 成功率
统计里排除；能力补上后逐条放回并重跑。

历史一列按 1109 / 1111 / 1112 / 1113 / 1115 的顺序，空格后是 11-16 改动后的重跑，O = 成功，x = 失败。profile 都是 `sticky_gt`，seed 10。

## A. 柜内 / 冰箱内 / 高处：空间受限，够不到

| # | episode | 失败步骤 | 物体与几何 | 历史 |
|---|---|---|---|---|
| A1 | `T04_cup_or_mug_to_cabinet/s10_x6_gd_cup_in_cabinets__cup_in_4_v6_x6_gd_cup_in_cabinets__cup_in_4` | pick cup_counter_b：no reachable grasp from any base pose | 杯子在 kitchen_cabinet_4/inside_shelf（z 0.31，上方净空 0.30 m）。breakfast_cup 只有从上方捏杯沿的抓法，600/600 个候选手臂的 link5-7 和夹爪都撞到柜顶板（z 0.6–0.7）。杯底直径 7.3 cm，大于 PINCH_MAX 6.8 cm，没有侧捏。11-16 把杯子挪到层板前沿（y 0.42 → 0.50）：构建出 12 个（原来 0），仍然失败在 pick_grasp 撞 link_7 / lift 时还碰着（excl_fix_1115） | xxxxx x |
| A2 | `T25_drink_for_guest/s10_cups_for_two__one_there_v6_cups_for_two__one_there` | pick stock_cup_1：同上 | 同一层板，同 A1；挪到前沿后同样失败。同样的失败：`cups_for_two__none_two_inside` | xxxxx x |
| A3 | `T21_bring_tissues/s10_tissue_put_away__in_4_v6_tissue_put_away__in_4` | pick tissue：同上 | 同一层板（净空 0.30 m），69 个候选在预抓取姿态全部撞固定物体（手指、link5-7）。11-16 纸巾挪到层板前沿（y 0.50），**未验证**：zihan 机器上这条第一步 tuck 就撞窗（见下“机器差异”），要在 muqingj 的机器上跑 | xxxxx |
| A5 | `T18_check_cabinet_dishes/s10_enough_for_dinner__two_short_v6_enough_for_dinner__two_short` | place bowl_kitchen_cabinet → kitchen_cabinet_6/inside_shelf：no spot of 4 reachable | 11-16 已修取碗：备用碗从 kitchen_cabinet_3/top（z 1.17，没有 IK）挪到 kitchen_cabinet_4/top，pick 成功；设计改成“两个人吃饭、柜里要 2 个碗”（3 个 17.8 cm 的碗把 56 cm 的层板占满，第三个没有空位）。剩下的是往柜内层板（净空 0.38 m）放：只有 x 3.50 附近放进去过，3.38 / 3.62 / 3.685 都没有可达的空位；空柜子时 3.52 也失败过一次（excl_fix_1116b）。`enough`、`one_short` 已成功 | xxxxx x |

## B. 物体超出夹爪能力 / 放不下

| # | episode | 失败步骤 | 物体与几何 | 历史 |
|---|---|---|---|---|
| B3 | `T27_leftovers_to_fridge/s10_still_eating_v6_still_eating` | pick leftover_rice：carry_in: the arm stopped 0.207 m short | 11-16 饭盒挪到桌子东侧（3.45, 6.70），推到桌边成功（伸出 6 cm）、夹住成功；收回时底盘正对桌子（朝向 180°），手里的饭盒和头都碰到桌面，两次都停在 0.207 m。同样位置的 soup_on_table 拿起来了（底盘斜着）。是 carry_in 的路径没有考虑手里的东西 | xxxxx xx |
| B6 | `T27_leftovers_to_fridge/s10_two_leftovers__soup_on_table…`、`s10_two_leftovers__soup_on_stove…` | place → breakfast_fridge/inside_shelf：no free spot / push: no base pose reaches a push | 11-16 汤锅加了 rim_pinch（捏锅沿，深 2.5 cm，在汤面以上），**抓汤锅已修**：两条都抓起来了。剩下的是冰箱层板（54 × 52 cm）放不下 30 cm 宽（含把手）的锅加 18 cm 的饭盒：并排时放置检查要求锅中心 x ≤ 6.018、饭盒被推到 5.87；饭盒放后排（y 3.46）时 push 找不到底盘位置 | xxxxx xx |
| B7 | `T07_heat_oatmeal/s10_two_portions__counter_v6_two_portions__counter` | place soup_pot → kitchen_stove/top：tuck: no collision-free trajectory (INVALID_START_STATE_WORLD_COLLISION) | 汤锅从吊柜下的台面上抓起来了（B6 已修）；放上灶台松手后锅偏 13 mm、倾 4°，tuck 起点手指嵌进 9 mm，规划不出路径 | xxxxx x |
| B8 | `T07_heat_oatmeal/s10_two_portions__dining_v6_two_portions__dining` | press kitchen_microwave/start_button：no IK for microwave_button_press | 前 14 步全部成功（汤锅抓、放灶台、开灶、碗进微波炉、关门）；按微波炉启动键没有 IK。和汤锅无关 | x |

## 机器差异：zihan 机器上第一步 tuck 失败（不排除，待在 muqingj 机器上验证）

zihan 的机器上 `rig.tuck` 一开局就判折叠姿态（rest）碰撞，改走“垂在身侧”，`base_plan` 的 postures 是
`[start, hang, arrive]`，tuck 走 128 个路点；muqingj 的机器上是 `[start, fold, hang, arrive]`，tuck 只走 2 个路点。
两边 zeno_skills 运动代码、scene.usd、assets.json 相同（除这次的汤锅），11-09 以来 zihan 的所有 run 都这样，所以是
两台机器之间的差异（cuRobo 碰撞模型或缓存），不是任务的问题。下面几条在 zihan 机器上第一步就撞（窗户 / 桌子），
11-16 的改动只能在 muqingj 机器上验证：

- `T21 tissue_put_away__in_4`（A3，撞窗）、`T07 vessel_decides_appliance__in_pot`、`T14 stack_them_stably__blue_green`
- `T09 pot_in_use__in_use`：zihan 机器上 carry_in 停在 0.294 m；muqingj 的 1113 / 1115 都成功，任务没改过

## 可修、已移出排除

| episode | 原来的编号 | 结论 |
|---|---|---|
| `T09_tomato_soup/s10_tomato_in_fridge__in_fridge_v6_tomato_in_fridge__in_fridge` | A7 | **已修**（88197712）：番茄从 y 3.30（冰箱正面往里 29 cm）挪到 y 3.14（离层板前沿 10 cm），pick 成功（sim 检查 fridgetomato_1115）。门开到 80° 或 92° 都没用 |
| `T22_put_away_shopping/s10_juice_on_table_nominal`（及 T22 所有把果汁放进冰箱的 variant） | A8 | **已修**（11-16）：冰箱里的位置 (5.78, 3.18) → (5.90, 3.12)：往前挪，并离开冰箱左壁（x 5.78 时放下后 tuck 擦到左壁把瓶子碰倒）。excl_fix_1116：juice_on_table 成功；by_kind、two_spots 成功 |
| `T22_put_away_shopping/s10_two_spots_v6_two_spots` | A6 | **已修**（11-16）：零食放进 kitchen_cabinet_6/inside_shelf 的目标点 (3.60, 0.36) → (3.45, 0.42)（靠前、离铰链远）；关冰箱后先走到岛台再看（原地转身撞冰箱）。excl_fix_1116 整条成功（1730 s） |
| `T25_drink_for_guest/s10_cup_elsewhere_v6_cup_elsewhere` | A4 | **已修**（11-16）：杯子从吊柜下面挪到 kitchen_counter_2 前沿（x -0.45）。excl_fix_1115 整条成功 |
| `T18_check_cabinet_dishes/s10_enough_for_dinner__one_short…`、`__enough…` | A5 | **已修**（11-16）：备用碗挪到 kitchen_cabinet_4/top，改成 2 个碗（见 A5）。excl_fix_1116 / 1116b 成功；`two_short` 还在 A5 |
| `T27_leftovers_to_fridge/s10_two_leftovers__soup_on_table…` 的取饭盒 | B3 | 饭盒挪到桌子东侧（3.45, 6.70）后推、抓都成功；这条现在卡在冰箱放不下锅（B6），`still_eating` 在 B3 |
| `T14_shelve_the_book/s10_stack_them_stably__*` | C1 | **已修**（11-16）：设计改成两本大小不同的书摞成一摞（红+蓝 / 绿+平装 / 蓝+绿），不再三本连摞。excl_fix_1115b：red_blue、green_paperback 整条成功；blue_green 待 muqingj 机器验证 |
| `T26_kids_things_to_room/s10_where_in_room_v6_where_in_room` | B5 | **已修**（e3dcbb8）：书沿 14 cm 那边只能伸出 5.495 cm，比要求的 5.5 cm 差 0.05 mm；-x 端要推 46.5 cm，超过 45 cm 上限。在 new_tasks_v6.py 里把书转 90°（长边朝前沿）后，前沿只需推 6.9 cm，sim 检查 bookrot_1115 整条 episode 成功（11 步，700 s） |
| `T27_leftovers_to_fridge/s10_rice_on_table_nominal`、`s10_which_is_leftover…`、`s10_fridge_out_of_view…` | B1、B2、B4 | **已修**（4e89016）：饭盒 16 × 11 × 7 → 18 × 16 × 5 cm。边缘抓取要伸出 ≥ 5.5 cm 且重心留在桌面内 1.5 cm，所以朝桌边那条边至少 14 cm；原来 11 cm 的一边永远不行，7 cm 高时夹爪上下只剩约 5 mm。sim 检查 ricebox_1115：rice_on_table、which_is_leftover、fridge_out_of_view、fruit_stays_out 整条成功 |

11-16 的 sim 检查都在 zihan 机器上：`benchmark/runs/v6_excl_fix_1115`（22 条，2 并行，大部分因别人的进程占显存 OOM）、
`v6_excl_fix_1115b`（16 条重跑，1 并行）、`v6_excl_fix_1116`、`v6_excl_fix_1116b`。一条 episode 约占 13 GB 显存，
这台机器上只能 `--jobs 1`。

## 放回统计的条件

- A1–A3：杯子类容器需要从侧面斜着捏杯沿，或者支持侧捏；纸巾需要在 0.30 m 净空里能伸进去的预抓取姿态。
- A5：在柜内层板上放置，要能找到可用的空位（kitchen_cabinet_6 只有中间一块放得进去）。
- B3：carry_in 的路径考虑手里的物体（边缘抓取后收回时别把物体拖过桌面）。
- B6：冰箱层板放下锅 + 饭盒（任务侧可再改：只放锅，或换小一点的汤容器）。
- B7：放下后 tuck 的起点允许手指贴着刚放下的物体（或先往上抬出）。
- B8：微波炉启动键的按压 IK。

每补上一项能力，就把对应条目移出本文档，并对这些 episode 做一次定向重跑。

## 没有列入的失败

下面这些失败**留在统计里**，因为它们是可以修的软件问题，物理上做得到：

- 感知：`bookcase_2/top`（只有 0.71 m 高）视线被挡、看地面物体、search 漏看位置、explore 覆盖率 0。
- T14 书放到书架顶面报 `no free edge spot`：edge-place 空位生成的问题。
- 以前成功过、这次失败的：T09 stir ×2（倾斜规则）、T01 no_room_fallback、T08 wipe_and_sort、T03 no_bin_substitute、T23 belongs_on_floor、T14 homework_stays、T29 several。
- 规划或执行问题：T13 copy_the_setting、T10 rubbish_leftovers lift、T08 return_sponge wipe、T05 pen_in_6 close。
- 灵巧操作：T15 book_free_nominal flip、T06 display_row__spread square。这两条暂时也留在统计里，以后再决定要不要排除。
