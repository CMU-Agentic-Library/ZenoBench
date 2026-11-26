# 11-25 起 GT 路线全量检查：给 muqingj 的技能问题清单

整理：2026-11-25 夜开始，边跑边补。以 `main` 为准（已含你的 remove-handcoded-motion，HAND_PLAN 9a-9j）。

## 1. 在跑什么

- `--profile sticky/gt --jobs 1`，参考路线（scripted planner）。11-25 20:08 起不录像，每个 episode 约 4–5 分钟；两个并行在 zihan 机器上会爆显存（24 GB 卡，11-25 T08 OOM）。
- 批次 1：`benchmark/v6/batches/gt_check_1125.json`，55 个从没在全量里成功过的布局 → `benchmark/runs/gt_check_1125`。
- 批次 2：`gt_check_1125b.json`，剩下 118 个没成功过的布局 → `benchmark/runs/gt_check_1125b`。
- 批次 3：`gt_check_all.json`，其余 1194 个 episode，先每个布局第二个种子，再其余种子 → `benchmark/runs/gt_check_all`。
- 布局问题我直接改 `define_tasks_v6.py` / `new_tasks_v6.py` 并推到 main；下面只列**技能侧**的。

## 2. 技能侧问题（不是布局能绕开的）

| 任务 / 布局 / 种子 | 失败的步骤 | 报错 | 我的判断 |
|---|---|---|---|
| T07 `two_portions__dining` s11 | #5 `place(soup_pot, kitchen_stove/top)` | `place_arrive: no collision-free IK at the set-down pose (out of reach)` | 站位选在了灶台远的一侧，没换另一边再试。 |
| T08 `wipe_and_sort__duck` s12 | #15 `wipe(kitchen_island/top, kitchen_sponge)` | `wipe_stroke: the arm stopped 0.007 m short of where it was sent` | 前 15 步都成功，只差 7 mm 就判失败，擦拭的到位容差太紧。合进你 11-25 晚的 wipe 改动（76bde0b2 等）后重跑，还是差 6 mm。 |
| T10 `after_dinner_clear__leftovers_mug` s14 | #16 `place(leftovers, breakfast_fridge/inside_shelf)` | `tuck: its path collides now at 1/243: world left_gripper_right_finger_link 6 mm ... INVALID_START_STATE_WORLD_COLLISION` | 在冰箱里放下后，收臂起点手指已经和冰箱碰上 6 mm，退出失败。 |
| T22 `tray_elsewhere__books_on_it` s11 | #7 `place(bought_juice, breakfast_fridge/inside_shelf)` | `place_arrive: no collision-free IK at the set-down pose (its solution collides: part:breakfast_fridge head_link 83 mm, torso_link 39 mm)` | 同一个放的点在别的 T22 设计里（nominal、by_kind、two_spots…）都成功；这次站位离冰箱太近，头撞门框。站位应该退后或者换角度再试。 |
| T23 `by_kind__toy_box` s12 | #7 `place(dropped_spoon, kitchen_island/top)` | `place_arrive: no collision-free straight (no IK along it)` | 勺子放岛台在其他 T23 设计成功很多次；`by_kind__bin_full` 你的三次全量里也是一过两败。直线下放没有 IK 时没换站位。 |
| T09 `x6_gd_tomato_elsewhere__on_plate` s11 | #26 `pick(pot_lid)` | `pick_arrive: no collision-free IK at the straight's start (out of reach)` | 前 25 步都成功。去锅盖的停车点 [8.415, 1.135] 的路径绕岛台东侧贴墙走，右臂在行驶姿态下撞墙和窗（wall_609/610、WindowFactory_3015），手臂被撞偏（q_err 2.84），底座停在 [9.50, 1.28]，离停车点 1.1 m，navigate 却算到达，接着 pick 就够不着。同样尾段的 `__dining` 三次全量都过。 |
| T18 `bowl_in_use__tomatoes` s11 | #17 `place(glass_box, dining_table_2/top)` | `place_pull_out: the arm stopped 0.005 m short of where it was sent` | 放下以后抽手差 5 mm 判失败，和 T08 wipe 差 7 mm 是同一类：到位容差太紧。 |
| T09 `lid_missing` s11 | #16 `cover(handled_cooking_pot, lid_plate)` | `place lid_plate: no free edge spot on rim:handled_cooking_pot` | 盘子当锅盖：11-21 交接第 4 节已记（cover 走捏边放置，在锅沿上找空边），还在。 |
| T18 `one_bowl__glass_box` s11 | #17 `place(glass_box, dining_table_2/top)` | `tuck: its path collides now at 1/242: world left_gripper_right_finger_link 5 mm ... INVALID_START_STATE_WORLD_COLLISION` | 玻璃盒走 `edge_held_flat`（捏边平放），松手抽手后左手指还贴着盒子（physx 接触 glass_box），收臂起点就碰撞。上面 T18 `bowl_in_use__tomatoes` 抽手差 5 mm 是同一个放置点、同一类：捏边平放的抽手间隙不够。T14 `next_in_series__on_tall_shelf` s11、`next_in_series__on_other_bookcase` s13（开局改好后重跑）放红书到 `bookcase_2/top` 也一样（edge_held_flat，左手指贴着刚放下的 book_red 5 mm）。**这是这次检查里最常见的一类。** |
| T17 `hide_lid_in_use` s11 | #4 `hide(wooden_block_b, handled_cooking_pot, lid=cover_plate)` | `cover_container: place cover_plate: no free edge spot on rim:handled_cooking_pot` | 同 T09 `lid_missing`：盘子当锅盖找锅沿空边。 |
| T19 `lookalike_bin` s11 | #5 `pick(soda_can)` | `pick_arrive: no collision-free path to the pose (MotionGenStatus.TRAJOPT_FAIL)` | 你的三次全量 s10 都过。这次罐子在餐桌西沿（离边 4 cm），选了左手捏顶，轨迹优化失败；没换手/换站位再试。 |
| T14 `next_in_series__on_other_bookcase` s13 | #0 `navigate` 的第一次 tuck | `tuck: the arm stopped 0.025 m short` | 开局第一次收臂，同 T25 / T27。 |
| T22 `eat_now__desk_corner` s11 | #5 `pick(bought_juice)` | `carry_in: the arm stopped 0.048 m short` | 果汁在餐桌西沿（离边 7 cm），底座在西南 [2.49, 5.85, 15°]；抓起后收到搬运姿势时 right_arm_link_7 撞桌沿（physx 接触 dining_table_2，leg carry_in）。carry_in 这段没避开桌子。 |
| T07 `microwave_broken` s11 | #14 `heat(oatmeal, kitchen_stove)`（微波炉那步按设计失败后改用灶台） | `press_reach: the arm stopped 0.540 m short` | 按灶台开关（停车 [8.452, 1.087, 60°]，按钮 [8.77, 1.455]）时右手一路刮东墙 wall_607（physx 接触 10 次，leg press_reach），press 的路径没避开墙。 |
| T09 `tomato_in_fridge__big_tomato` s11 | #11 `pick(big_tomato)`（冰箱里） | `pick_arrive: no collision-free path to the pose (MotionGenStatus.TRAJOPT_FAIL)` | 冰箱内取物；`tomato_in_fridge__in_fridge` 你三次全量过两次。 |
| T12 `bins_capacity__apart_full_on_tv` s11 | #10 `place(toy_car, toy_bin_small_2)` | `tuck: its path collides now at 1/113: world right_gripper_left_finger_link 12 mm ... INVALID_START_STATE_WORLD_COLLISION` | 放进小收纳盒后收臂起点手指已卡进 12 mm；和 T10 冰箱、T18 玻璃盒同类：放下后退出的起点在碰撞里，没有先退出来。 |
| T10 `after_dinner_clear__rubbish_mug` s11（重跑） | #17 `pick(used_mug)` | `pick used_mug: no reachable grasp from any base pose`（round_rim） | 同一布局（两次 annotation 完全相同）第一次跑这步成功，第二次失败：pick 的结果不稳定。 |
| T19 `x6_gd_can_put_away__juice_full` s11 | #17 `drop(soda_can, wide_storage_bin)` | `tuck: the arm stopped 0.333 m short`（27 tick 内，无 physx 接触） | 停车点算到 [1.684, -0.435, 195°]，但 drop 第一段 tuck 在导航停下的位置 [2.259, -0.428, 180°]（右侧 0.43 m 是墙）就没收回来，底座还没开往停车点。`__in_4` 你三次全量过两次。 |
| T03 `no_bin_substitute__tray` s11 | #15 `place(breakfast_spoon, serving_tray)` | `place breakfast_spoon: no free spot in serving_tray` | 前一步擀面杖（22 cm）放进 42×36 cm 托盘时落在正中、斜 45°，占满了托盘，勺子没处放。放进开口容器时应靠一边、顺容器长边放（place 没有朝向参数，托盘随种子移动，bench 给不了跟着托盘走的放置点）。 |
| T07 `vessel_decides_appliance__in_pot` s16 | #0 `navigate` 的第一次 tuck | `tuck: the arm stopped 0.499 m short` | 开局第一次收臂，同 T25 / T27 / T14。 |
| T12 `bins_capacity__half_bin_and_tray` s17 | #9 `place(toy_car, toy_tray)` | `no spot of 4 on in:toy_tray reachable`（60 次构建：`its solution collides: object:toy_tray right_gripper_link 47 mm`） | 托盘 27×20 cm、边高 5.5 cm，在 `bookcase_2/top` 上；车往里放时手爪下到托盘边以下撞边。容器内放置的落点/手爪朝向没避开容器壁。 |
| T13 `finish_the_table__kid_seat` s11 | #11 `place(kid_cup, dining_table_2/top)` | `place_reach: no collision-free path to the pose (carry tilt held: TRAJOPT_FAIL (no feasible seed))` | 端杯子保持水平的约束下轨迹优化没有可行种子（只构建了 2 次）；放置点在餐桌西沿 11 cm。 |
| T07 `vessel_decides_appliance__in_pot` s16（开局改好后重跑）、T10 `after_dinner_clear__rubbish_mug` s11（第三次跑） | #7 `place(soup_pot, kitchen_stove/top)` / #15 `drop(takeout_tray, kitchen_trash)` | `PRECONDITION_FAILED: holding(hand=any, object=…) is false (slip 0.009 m / 0.004 m, fingers [0.0, 0.0])` | sticky 焊着、滑动很小，但 holding 看手指读数判成没拿着；同 11-21 交接第 4 节的铅笔。holding 检查在 sticky 时应信焊接。 |
| T27 `two_leftovers__soup_on_table` s16（开局改好后重跑） | #9 `pick(leftover_soup)` | `tuck: the arm stopped 0.008 m short` | 左手拿着剩饭（9c 以后两只手都用），右手拿汤后收臂，左手爪碰餐桌（physx：left_gripper_link–dining_table_2，leg tuck / drive_base）。另一只手拿着东西时的收臂没避开桌子。 |
| T27 `two_leftovers__soup_on_table` s16 | #0 `navigate` 的第一次 tuck | `tuck: the arm stopped 0.172 m short` | 开局站在墙角，第一次收臂碰墙。跟 11-16 记的“zihan 机器第一次收臂”一类；开局生成器按用户 11-17 的规定不动。 |
| T25 `cups_for_two__none_one_inside` s11 | #0 `navigate` 的第一次 tuck | `tuck: the arm stopped 0.356 m short`（开局 [-4.47, -3.88, -135°]） | 同上一行，开局靠墙角的第一次收臂。 |

## 3. 已经在 bench 侧改掉的

- T30 `how_many__three_bowls`：三只碗挨太近，中间那只没有抓取 → 两只放 6 号柜相隔 30 cm，第三只放 4 号柜顶（570f15b5）。
- T26 `bear_to_bed__top_covered` s14：书柜背后 22 cm 是墙，放的点离墙近，停车选了侧面，空着的右臂一路贴墙，place 差 26 cm → 三条放 `bookcase_2/top` 的路线放的点挪到离前沿 12 cm（9f615579），s14 重跑成功。
- T03 `utensils_apart__bin_full_fruit` s12：30 cm 高的果篮被种子挪到餐桌中间（离每条边 45 cm），丢勺子找不到站位 → 果篮贴北边放（离边 3 cm，种子不再往里挪，d6365bbd），s12 重跑成功。
- 种子之间太像（用户 11-25）：地上的东西在房间里挪、太像的种子重抽（f0a5f938，`layout.py` 的 `draw_distinct`）。同一设计的种子没有太像的了；6 个设计的东西在柜子里或角落里，只有开局不同。
- T13 `finish_the_table__adult_and_kid` s14：儿童杯在 `kitchen_counter_2`（吊柜下）8 次抓取轨迹全失败 → 挪到电视柜和碗放一起（3cebde7d），s14 重跑成功。
- T10 `after_dinner_clear`：杯子放岛台不给放置点时技能放到离北沿 7 cm 倒了 → 路线给放置点 [7.05, 1.70]（208d9ecb）。
- T23 地上的东西互相至少隔 0.3 m（bd8c2302），`belongs_on_floor__bin_full` s12 重跑成功。
- T22 `tray_elsewhere`：苹果放进浅托盘顶部高出托盘边 2.3 cm，`fully_inside` 判不过 → 改为 `inside`（同 T11 的苹果进托盘）。
- 生成器：路线要往里放东西的容器也必须够得着；能站人的边必须开得过去（`drive_cells.json`），T22 托盘不再被抽到餐桌西沿（2cf8f967）。
- T28 `which_bed__south`：杯子放 `cell_shelf_2` 的放置点从书架北端挪到中段（离西墙的角远一点）。
- T05 `homework_ready__several`：本子在矮电视柜上，expose 后机器人 0.8 m 处看它在视野下方 48°，look 失败 → 电视柜上的扁平物品 look 前后加 bend / straighten。
- 开局第一次收臂失败（T25、T27、T14、T07、T10，开局都离墙 0.40–0.51 m）→ 生成器的开局离墙和家具至少 0.6 m（3160 个开局全部满足）。这几行留在第 2 节备查：收臂时手臂扫到墙本身仍是技能侧的事。
- T14 `whose_book`：大人书架从 `large_shelf_2/shelf_2`（0.81 m，place 差 14 cm）改到 `shelf_1`（17a867e5），s12 重跑成功。
