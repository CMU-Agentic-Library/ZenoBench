# 运动代码删除清单（2026-11-01）

配合 `COLLISION_PLAN.md` 使用：这里列的是代码里要删掉或改写的"特殊实现"，每条标了归哪一步。第 1、2 节只列还没动的条目，按函数名定位；第 3 节的行号 2026-11-02 按 `67b377c` 刷新过；第 4–7 节的行号仍以 `a0a9574` 加当时未提交改动的工作区为准，动代码之前先按函数名重新定位。

**来源：** 逐个阅读 `zeno_skills/` 下 248 处运动调用（`move_to`、`move_left_to`、`joint_path`、`follow*`、`drive_base`、`tuck`、`_back_off`、`held_vertical_move`、`_carry_pose`、`_clear_for_tuck`）的上下文，加上 skill 内部的重试循环、变体列表和按家具分支。分类是读代码判断的，个别条目可能归错；第 9 节的几条还没回到代码核实。

## 分类

| 类 | 含义 | 处理 | 步骤 |
|---|---|---|---|
| R | 中继位姿：任务决定的位姿 | 保留 | — |
| C | 接触段：手沿规定方向碰目标 | 保留，改用 `Allow` 预设 | 4 |
| T | 任务轨迹：运动本身就是任务（摇、挥、倒、搅、擦） | 保留，只加检查 | 4 |
| W | 避障路点：只为绕开障碍的中间点 | 删 | 3 |
| B | 底盘盲动：不是去任务目标的底盘移动 | 删 | 2 |
| F | 自写退路和重试：变体列表、失败换路径、失败后关检查、吞异常继续 | 删 | 3 |
| K | 约束伪装成路点：为了不甩、不倾斜、IK 分支连续而拆的段或参数 | 改成规划约束 | 1 |
| S | 场景特例：按物体、家具类型分出不同编排 | 逐条判断：任务差异保留，避障删 | 见第 6 节 |
| X | 碰撞配置、临时改状态、其他写死处理 | 清理 | 5 |

R 类不列。下面只列要动的。

## 1. 入口层（`rig.py`、`planner.py`，步骤 1）

**状态（2026-11-01，步骤 1 已完成）：** `move_to` 的旧退路链 L2–L5 和"整条链关掉检查重跑"都已收敛进 `_motion_path`（直线 → `plan_to`，退路是不查碰撞的直线），`_joint_path` 的倾斜检查和 `joint_from_contact`、`tuck` 的候选列表和夹爪判断、`follow` 的慢速平滑都处理完了，现状见 `COLLISION_PLAN.md` 步骤 1。下面只列还没动的。

| 位置 | 内容 | 类 | 处理 |
|---|---|---|---|
| rig.py `_left_path` | 直线失败 → `ik_global` → 有时 cuRobo、有时直接插值；左臂没有 `plan_to`，也没有持物碰撞 | F | 步骤 5，左臂走同一套入口 |
| rig.py `follow_both` | 双臂只有直线插值，按 `max(3, n//8)` 个样本稀疏检查 | X | 步骤 5，双臂要有规划或至少逐点检查 |
| rig.py `joint_path_via` | 直接插值，不做任何检查 | X | 步骤 5，`follow` 只收检查过的路径 |
| rig.py `tuck` | `coll_kw = {"ignore_fingers": True}` | X | 已改（11-04，提前做）：查手指（`_fingers_checked`） |
| planner.py `_ik_sequence` | 正向链失败就反向链（为了 IK 分支连续） | K | 改成种子；手写 park 删掉时再看（步骤 3） |
| planner.py `_chain` | park 搜索用直线判可达，执行时直线不通还会规划，两边判据不一致 | X | 手写 park 删掉时一起看（步骤 3） |
| planner.py `find_park` | `near` 是三元组时 cost=-1，跳过收臂姿态、展开、可达路径三项检查；`_move_articulated` 和 `place` 用它探测手写 park | X | 手写 park 删掉后这条路径一起删 |

## 2. 底盘（B 类，步骤 2）

**状态（2026-11-02，步骤 2 已完成）：** B 类和底盘规划器本身的问题（`relax`、`Grid` 只查底盘圆、`R_BASE`、开车时不查手臂、原地转身只查终点）都已删掉或改成整机规划，现状见 `COLLISION_PLAN.md` 步骤 2。`BackOffWithLoadPolicy` 保留为任务级原语，改成整机检查的直线后退。下面只列还没动的。

| 位置 | 内容 | 处理 |
|---|---|---|
| policies/hand.py:411-453 | flip：手臂推不动时改用底盘推（`footprint_clear` + `drive_base`，同时是 F） | 步骤 4（接触动作）；换策略部分 3b 删 |
| policies/tooluse.py:157 | wipe 的底盘推（擦拭行程） | 步骤 4 |
| skills.py `clear_microwave_door_sweep` | 开到写死的 `(5.1, 1.6, 150)` 给门让路，再收臂 | 3c（场景特例） |
| policies/mobile.py 三处 `drive_base` | 边走边伸手 / 抓 / 放：路径来自 `plan_drive`，但行驶中手臂在动，没有逐点整机检查 | 已停用（`mobile.DISABLED`，调用即 `SkillFailure`）；整机规划之前不恢复 |

## 3. 手臂：避障路点和自写退路（W、F 类，步骤 3）

**刷新于 2026-11-02（`67b377c`）：** 行号、函数名按现在的代码重新定位；"状态"一列说明步骤 1、2 之后这条还在不在。106 条里仍在 94、已改 11、已删 1。已改的主要是松手、离开接触的那一段改成了 `LEAVE_CONTACT`，以及餐桌、层板、微波炉取物的"退出去再开回"改成了 `relocate`；这些条目里的变体列表和吞异常大多还在，步骤 3 照样要删。3.10 是这次刷新新发现、原表里没有的。

按计划里的子步排：3.1–3.4 和 wipe 选带属于 3a；3b 剩下的按 11-05 定的顺序：3.5 pick（push 那行除外）先做（计划 6.1），然后 place 系（3.2 剩下的、3.3 `place_flat`、3.4、sticky 的 place，计划 6.2），再是 3.6、3.7、3.10（计划 6.3）；3.8、3.9 其余属于 3c（计划 6.4）（`COLLISION_PLAN.md` 步骤 3）。

### 3.1 `_carry_pose`（skills.py）

**状态（2026-11-03，3a）：** 下表除 `_carry_bottom_z`（policies/plan_helpers.py）和书本 edge +6 cm（留到 3c）外都已删掉，`_carry_pose` 改成一个目标集合（`COLLISION_PLAN.md` 第 4 节的 3a 提交）。行号是改动前的。

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| skills.py:56-68 | `_carry_pose` | `carry_stand_up` 失败吞掉，继续 | F | 已删（3a） |
| skills.py:76-81 | `_carry_pose` | `for allow in (FREE, LEGACY, +3cm LEGACY)`：带检查不行就关检查，再不行只抬 3 cm 也不查 | F | 已删（3a） |
| skills.py:75-78 | `_carry_pose` | `carry_up`：先竖直抬到高度再横移 | W | 已删（3a） |
| skills.py:87-111 | `_carry_pose` / `bring_in` | 搬运姿态的变体（xy、z 组合），IK 或执行失败就换下一个 | F | 已改（3a）：4 位置 × 3 高度 × 8 手腕朝向的目标集合（`move_to_any`） |
| skills.py:114-125 | `_carry_pose` | `carry_in_via`：tcp+8 cm、半路点、半路点+8 cm | W | 已删（3a） |
| skills.py:126 | `_carry_pose` | 收不回来只记 `carry_in_failed`，手伸在外面开车 | F | 已改（3a）：到不了时手臂不动开车（`carry_pose_kept`），底盘整机检查判断；根因在 pick，3b |
| skills.py:72-73 | `_carry_pose` | edge 抓法搬运时 `min_bottom_z` +6 cm（书下垂；清单第 6 节） | S | 仍在：3a 删后 T14 失败又恢复，挪到 3c |
| policies/plan_helpers.py:43-82（台面物体部分 66-81） | `_carry_bottom_z` | 搬运高度抬到台面上已有物体之上，用来避免持物扫倒东西 | W | 仍在：3b 第一项删过又恢复。删掉后搬运高度低 12 cm，T13 bowl_on_cabinet s10 带着杯子开往餐桌时底盘规划搜到上限（20 万次扩展）也没找到路，保留时 5.9 万次找到。底盘规划器拿着东西时只有当前一个搬运姿态，不会自己选高度；要先给它加这个能力再删（见 `COLLISION_PLAN.md` 第 4 节的 3b 提交） |

### 3.2 place 链（skills.py）

**状态（2026-11-03，3a）：** 逐行见状态列。变体列表和越障中间点都已删掉，空位、朝向、放平 / 倾斜改成停车点搜索里的一个目标集合（`find_park_set`）。还在的：`slots_blocked`（目标集合的筛选，手指进碰撞模型后删）。上方 6 cm 的预备点、不查碰撞的 5 cm 下放、退到上方 6 cm 的终点和 `retreat_short` 吞异常已在 3b 第一项删掉：放下是一次带竖直接近约束的运动（`place_down`），松手后只走离开接触段（`place_retreat`）。行号是改动前的。

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| skills.py:1821-1837；循环在 1896、1941-1946 | `place` | 先试"放平"关系，够不到回退到实测倾斜关系 | F | 已改（3a）：两种都进停车点目标集合，放平优先 |
| skills.py:1880-1894（定义），1902-1905（使用） | `place` / `slots_blocked` | `slots_blocked`：手写指缝和邻物的碰撞过滤 | F | 已改（3a）：改成目标集合的筛选，不算放置面所属的物体；手指进碰撞模型后删（步骤 5 / 3b 第一项） |
| skills.py:1898（1931 也有一份） | `place` | 手腕朝向 8 个变体 | F | 已改（3a）：停车点目标集合（`find_park_set`） |
| skills.py:1875-1876（`clear_z0`），1906-1910（park 搜索的腿），2074-2077（执行） | `place` | 越过最高邻物 +3 cm 的点（`place_over_neighbours`） | W | 已删（3a） |
| skills.py:1927-1940 | `place` | 没 park 就去掉越障点、8 个 yaw 重来（`place_clearance_dropped`） | F | 已删（3a） |
| skills.py:1945-1946 | `place` | `place_level_dropped` | F | 已删（3a） |
| skills.py:1952-1953 | `place` | 重测后丢掉越障腿重算 | W | 已删（3a） |
| skills.py:1966-1982 | `place` | 餐桌整段：退 0.40 m → `table_staging` → `table_pre_lift` → 开回 | B/W | 已改：步骤 2 换成一次 `relocate`，到达姿态是 `table_pre_lift`（IK 抬高 dz）；后撤、`table_staging`、开回都删了。`table_pre_lift` 在 3a（`f5779ab`）随放置链改目标集合删掉 |
| skills.py:2003-2011 | `place` | 越障点高度按 `k in (1.0, 0.7, 0.4)` 试 IK | W/F | 已删（3a） |
| skills.py:2024-2041 | `place` | `container_pre_lift`，记下 `container_exit_pose` | W | 已删（3a） |
| skills.py:2043-2067 | `place` | 贴边时选净空最大的一侧退出（`place_back_from_edge`），距离 `(need, 0.04)` + try/except | W/F | 已删（3a） |
| skills.py:2068-2073 | `place` | `place_rise`：先竖直抬再平移 | W | 已删（3a） |
| skills.py:2088-2100 | `place` | 层板：直线不通就换"倒车 → 预整形 → 开回"，再失败重新导航 | F/B | 已删（3a）：`place_preshape` 也删了 |
| skills.py:2109-2120 | `place` | `place_remeasure_fallback`：失败改用重测前的目标 | F | 已删（3a） |
| skills.py:2148-2154 | `place` | `place_lower_to_contact`：`held_vertical_move` 下放，失败只记日志 | F | 已改（3a）：失败不再吞掉；下放本身是接触段（步骤 4），`held_vertical_move` 在 3b |
| skills.py:2173-2192（列表 2176-2178） | `place` | 松手后退出方向的变体（`retreat_back`、`retreat_base`） | F | 已改（3a）：只留一个方向（层板向外，其余向上）。3b 第一项：终点 6 cm 和 `retreat_short` 吞异常删掉，只走离开接触段 |
| skills.py:2179-2183，2191-2192 | `place` | 层板退出 22 cm → 14 cm，全失败只记日志 | F | 已改（3a）：只留 22 cm 一档。3b 第一项：22 cm 和 `retreat_short` 删掉，沿放入方向的反向离开接触 |
| skills.py:2193-2202 | `place` | `container_exit`：回到桶外 staging 点 | W | 已删（3a） |
| skills.py:2297-2317 | `place_on` | 放置点重试 4 次 | F | 已改（3a）：空位进停车点目标集合，不再重试 |

### 3.3 `place_flat`（skills.py）

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| skills.py:2415 | `place_flat` | 内层板时加大 `pre`，让书在外侧整本降下来 | W | 仍在 |
| skills.py:2418-2506 | `place_flat` | `while True` + 最多 2 次被挡、每轮最多 6 个候选点 | F | 仍在 |
| skills.py:2436-2444 | `place_flat` | 带推入的够不到，就丢掉推入目标重找 park | F | 仍在 |
| skills.py:2499-2506 | `place_flat` | `flat_back_out`：被挡后退回再换点 | F | 仍在 |
| skills.py:2520-2530 | `place_flat` | 整段松手、推入失败都吞掉 | F | 已改：`flat_retreat`、`flat_up` 改成 `LEAVE_CONTACT`；吞异常还在 |

### 3.4 drop、hover（policies/hand.py、extra.py）

**状态（2026-11-03，3a）：** 下表都已删掉：drop、hover 各只留一个中继位姿（物体在目标正上方），手腕朝向是停车点的目标集合（`skills.park_over`）。另外 3.9 的 `NavigateToPlacePolicy` 候选列表、3.10 的 wipe 擦拭带和海绵朝向、`stow_load` 带进来的搬运变体也在 3a 改完（`COLLISION_PLAN.md` 第 4 节的 3a 提交）。

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| policies/hand.py:99-104 | `DropIntoPolicy.execute` | `drop_prelift`：先抬到沿口上方再平移 | W | 已删（3a） |
| policies/hand.py:91，106-107 | `DropIntoPolicy.execute` | `drop_above`：松手位姿上方再高 6 cm 的点 | W | 已删（3a）：只留一个中继位姿（沿口上方 5 cm） |
| policies/extra.py:381-385 | `HoverOverPolicy.execute` | `hover_lift` | W | 已删（3a） |
| policies/extra.py:376（park 搜索的腿），386-387 | `HoverOverPolicy.execute` | `hover_above`：悬停位姿上方 5 cm | W | 已删（3a）：只留悬停位姿本身 |

### 3.5 pick（skills.py）

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| skills.py:957-964（`_grasp_legs`），1218-1220（`f"pick_{lab}"`） | `_grasp_legs` / `_pick_pinch_core` | `pick_pre_far`：pre 之外再后退、再抬高的接近点 | W | 已删（3b 第一项）：`pick_pre_far`、`pick_pre` 都删了，抓取是一次带接近约束（沿夹爪轴 4 cm 直线）的运动 `pick_grasp`；`_lift_height` 的 7 cm 也删了，离开接触后直接规划到搬运姿态 |
| skills.py:978-986 | `pick` | pinch 失败 → `pick_flat` | F | 已删（11-05）：`pick_flat` 删掉，平板物体改成标注里的夹厚度捏取（`thickness_pinch`），和其他捏取同一个流程 |
| skills.py:1002-1019 | `_pick_pinch` | 失败 → 放开腰限重试 → 关掉邻居障碍重试 | F | 已删（11-05）：腰不设限；邻居盒子进的是空操作 `temp_obstacles`，`_pick_pinch_impl` 删掉 |
| skills.py:1175-1188 | `_pick_pinch_core` | 找不到 park 后追加旋转的 top pinch | F | 已改（11-05）：一开始就排在标注候选后面 |
| skills.py:1221-1222 | `_pick_pinch_core` | 误差 >8 mm 就 `pick_grasp_fix`，同一目标不查再走一次 | F | 已删（`6466347`，pick 两段式） |
| skills.py:1235-1244 | `_pick_pinch_core` | `pick_fail_clear`：抓空后抬 8 cm，失败吞掉 | W | 已删（3b 第一项）：只走离开接触段，不吞异常 |
| skills.py:1430/1455（corner），1538/1554（edge） | `_corner_pinch` / `_edge_pinch_impl` | corner、edge 的 `pre_far` 额外 +3 cm | W | 已删（11-05）：corner、edge 捏取整个删掉 |
| skills.py:1459-1461 | `_corner_pinch` | `corner_grasp_retry` | F | 已删（11-05） |
| skills.py:1503-1516 | `_edge_pinch` | edge：限腰 → 失败放开重试 | F | 已删（11-05）：edge 捏取整个删掉 |
| skills.py:1278，1303-1314 | `push` | push：4 个腕部朝向 × push/drag 两种编排 | F | 仍在（包在 `contact_obstacles` 里）。按步骤 3 的规则：动作前按可行性挑朝向和推/拖，算目标采样，保留 |
| skills.py:1377-1393 | `pick_flat` | 换边重试 | F | 已删（11-05）：`pick_flat` 删掉 |

### 3.6 open / close（skills.py）

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| skills.py:466-469（`_handle_targets`），647-650 | `_handle_targets` / `_move_articulated` | `{verb}_pre_high`：把手前位姿上方 +8 cm | W | 仍在 |
| skills.py:794，814-815（腿），818-821 | `_push_close` | 推门的 `pre_high` +4 cm | W | 仍在 |
| skills.py:565-572 | `_move_articulated` / `score` | 失败过的 park 打 1e9 分排到最后 | F | 仍在 |
| skills.py:574-583 | `_move_articulated` | 把手抓法：倾斜 {0, 10°, 20°} × 翻转 + front pinch | F | 仍在 |
| skills.py:619-637，811-816 | `_move_articulated` / `_push_close` | 到达后发现门被底盘碰动 → 重解或重找 park | F | 仍在 |
| skills.py:666-679 | `_move_articulated` | 后撤 `(0.14, 0.08, 0.04)` → `{verb}_up` +0.12 → for-else 再 +0.08，全失败吞掉 | F/W | 已改：`{verb}_back` 改成 `LEAVE_CONTACT`；`{verb}_up` 仍是 `FREE_ELSE_STRAIGHT`，结构不变 |
| skills.py:710-729 | `_move_with_retry_impl` | 失败后记 park、tuck、再调一次 `_move_articulated` | F | 仍在（tuck 前先松手，步骤 1 加的） |
| skills.py:737-746 | `close_articulated` | 推门找不到 park → 换拉把手 | F | 仍在 |
| skills.py:828-833 | `_push_close` | 推门后撤 `(0.12, 0.06)` | F | 已改：`close_push_back` 改成 `LEAVE_CONTACT`，两档还在 |

### 3.7 `held_vertical_move` 和其他持物运动

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| skills.py:154-191 | `held_vertical_move` | 往身体拉回 `(0, .08, .15, .22, .30)` 的变体 + `{label}_stage` 过渡点 + 重试 | F/W | 仍在（还带 1.2 / 1.0 rad 阈值） |
| policies/hand.py:166-184 | `RotateHeldPolicy.execute` | rotate：4 组 `(pull, up)` staging 变体 + `rotate_clear` | F/W | 仍在 |
| policies/hand.py:369-453 | `FlipFlatPolicy.execute` | flip：沿弧推 → 直推 3 档 → 底盘推 3 档 → 补推 3 档 → 底盘补推 2 档 | F | 仍在（底盘推还是 `footprint_clear` + `drive_base`；`flip_withdraw` 已是 `LEAVE_CONTACT`） |
| policies/hand.py:455-461 | `FlipFlatPolicy.execute` | `flip_clear` 高度变体，全失败也继续 | W | 仍在 |
| policies/tooluse.py:182-193 | `StirContainerPolicy.execute` | stir：限腰失败 → 放开腰限整套重跑 | F | 仍在 |
| policies/tooluse.py:237-249 | `StirContainerPolicy._stir` | stir：找不到 park 就缩小搅拌半径 | F | 仍在 |
| policies/tooluse.py:255-260 | `StirContainerPolicy._stir` | `stir_raise`，失败跳过 | W | 仍在 |
| policies/tooluse.py:282-291 | `StirContainerPolicy._stir` | 圆上某点不可达就跳过 | F | 仍在 |
| policies/tooluse.py:390-393 | `PourIntoPolicy.execute` | pour：倾角从 110° 降到 40°，最后只规划竖直位姿 | F | 仍在 |
| policies/tooluse.py:429-437 | `PourIntoPolicy.execute` | `pour_raise` 先竖直抬，失败跳过 | W | 仍在 |
| policies/tooluse.py:438-458 | `PourIntoPolicy.execute` | 实测位姿和计划位姿二选一 | F | 仍在 |
| policies/tooluse.py:476-493，528-533 | `PourIntoPolicy.execute` | 笛卡尔倾斜或回正走不通 → 换关节空间 | F | 仍在 |
| policies/extra.py:100-108 | `WaveHandPolicy.execute` | wave：举手高度 3 档 | F | 仍在 |
| policies/orientation.py:39-49，356-366 | `UprightObjectPolicy.execute` / `_hang_upright` | upright：在空中转失败 → 改 hang；pivot 不到 80° → 改 hang | F | 仍在 |
| policies/orientation.py:60-68 | `_turn_in_air` | `upright_clear` 高度 3 档 | W | 仍在 |
| policies/orientation.py:215-231 | `_set_down_upright` | 放下点的变体 | F | 仍在（实际 5 个：d = 0–0.20） |
| policies/orientation.py:243-249，270-275 | `_set_down_upright` / `_hang_upright` | `upright_release_clear` 方向和高度变体 | W/F | 仍在（仍是 `LEGACY`，没改 `LEAVE_CONTACT`） |
| policies/orientation.py:300-306 | `_hang_upright` | 先找 pivot 的 park，失败找 hang 的 | F | 仍在 |
| policies/orientation.py:341-346 | `_hang_upright` | `upright_pivot_out` 距离 2 档 | F | 仍在 |
| policies/navigation.py:55-63 | `CarryHeightAdjustPolicy.execute` | 最多 3 次闭环 | F | 仍在 |

### 3.8 微波炉（skills.py、embedded.py、appliance_generic.py）

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| skills.py:1614-1615 | `insert_microwave_cavity` | 4 个写死的候选 park，套在碗朝向外层 | F/S | 仍在（原表在第 6 节） |
| skills.py:1630-1641 | `insert_microwave_cavity` | 放入：碗朝向 8 个变体 | F | 仍在 |
| skills.py:1664-1679 | `insert_microwave_cavity` | 重测后：写死 park → 近邻搜索 → 沿用原入口，三级退路 | F | 已改：三级还在，近邻 park 的挪位从 `drive_base` 改成 `drive_to`（整机规划） |
| skills.py:1681-1689 | `insert_microwave_cavity` | 插入段带检查走不通，就整段 `LEGACY` | F | 仍在（`microwave_insert` 无条件用 `LEGACY`） |
| skills.py:1736-1742 | `withdraw_microwave_cavity` | 撤出失败吞掉 | F | 已改：`microwave_release_up` 改成 `LEAVE_CONTACT`；`microwave_retreat` 仍是 `FREE_ELSE_STRAIGHT`，吞异常还在 |
| skills.py:1745（记录）；1146-1153、1169-1172、1199-1201；policies/embedded.py:227-235 | `withdraw_microwave_cavity` / `_pick_pinch_core` / `PickFromCavityPolicy.execute` | 撤出时记下 `microwave_retrieval_q`，取物时回放这个"安全"姿态 | W | 已改：回放改成 `relocate` 的到达姿态（`microwave_pick_safe` / `cavity_return_safe`）；记下来的姿态还在用 |
| skills.py:1248-1257 | `_pick_pinch_core` | 取物后沿世界 −y 退 0.10、0.23 | W | 仍在 |
| skills.py:2580，2606；policies/appliance_generic.py:58，70 | `approach_microwave_button` / 按键 policy | 按键前位姿上方 +6 cm 的点 | W | 仍在 |
| skills.py:2584-2598 | `approach_microwave_button` | 优选 park 用 `scene=None` 验证，失败再搜 160 次 | F | 仍在 |
| policies/embedded.py:241-244 | `PickFromCavityPolicy.execute` | `cavity_pick_front`：前方 10 cm、高 6 cm，世界 −y 写死 | W | 仍在 |
| policies/embedded.py:254-266 | `PickFromCavityPolicy.execute` | 接触误差 >2 cm → 通用重抓 | F | 仍在 |
| policies/embedded.py:277-296 | `PickFromCavityPolicy.execute` | 撤出按 y 分 4 段，失败就下一段 | F | 仍在 |

### 3.9 双手、sticky、其余 policy

| 位置 | 函数 | 内容 | 类 | 状态 |
|---|---|---|---|---|
| policies/bimanual.py:41-49 | `_fixed_torso_ik` | 固定躯干 IK：3 轮 × 12 个随机种子 | F | 仍在 |
| policies/bimanual.py:263-278 | `_lift_together` | 配对 IK 失败 → 改抬躯干 | F | 仍在 |
| policies/bimanual.py:359-374 | `_grasp_both` | 跟随被推动的物体，比例 `(1.0, 0.8, 0.6)` | F | 仍在 |
| policies/bimanual.py:406-415 | `BimanualFlatPickPolicy.execute` | 报 "overhanging edge" → 插一个 `SlideToEdgePolicy` 再重来 | F | 仍在 |
| policies/bimanual.py:492-519 | `HandoverRightToLeftPolicy.execute` | handover：4 个展示位姿依次试 | F | 仍在 |
| policies/bimanual.py:543-549 | `HandoverRightToLeftPolicy.execute` | `handover_right_clear` 2 档 | F | 仍在 |
| policies/bimanual.py:585-594 | `_present_for_horizontal_left` | 先把躯干升顶、腰放直，让写死的展示位姿可达 | W | 仍在 |
| policies/bimanual.py:599-632 | `_present_for_horizontal_left` | 3 个轴角 × 4 个位置，12 个手写候选依次执行 | F | 仍在 |
| sticky.py:251-256，421-427 | `StickyHands.drop_caught` / `StickyHands.place` | `sticky_clear` 上抬 3 档 / 2 档 | F | 仍在 |
| sticky.py:317-333 | `StickyHands._reach` | pre → above → 6 个机身系写死候选 | F | 仍在 |
| policies/embedded.py:43-59 | `PrepareFloorReachPolicy.execute` | 48 个预抓取候选 | F | 仍在 |
| policies/embedded.py:154，166-178（腿来自 skills.py:468） | `GraspArticulatedHandlePolicy.execute` | `handle_pre_high` +8 cm | W | 仍在 |
| policies/embedded.py:168-178 | `GraspArticulatedHandlePolicy.execute` | `joint_path` 失败 → `move_to(q_hint)` | F | 仍在 |
| policies/embedded.py:110-131 | `SlideToEdgePolicy.execute` | 失败换方向 | F | 仍在 |
| policies/contact.py:71-79 | 拉取 policy（`PULL`） | drag 不动 → 改 push | F | 仍在 |
| policies/contact.py:94-122 | `SeparateFromNeighbourPolicy.execute` | 最多 3 次 push × 7 个方向 | F | 仍在 |
| policies/handle_grasp.py:42-43 | 杯柄抓取 policy | 无条件先 `tuck()` | W | 仍在（`tuck` 本身步骤 1 改成直接规划 q → rest） |
| policies/base_motion.py:80-99 | `NavigateToPlacePolicy.execute` | 候选位姿逐个 navigate | F | 已改（3a）：一次可达性筛选（`base_reachable`），导航到最近的一个 |
| policies/base_motion.py:165-190 | `RetreatFromPolicy.execute` | retreat 距离 2 档 | F | 已删：步骤 2 改成一次 `straight_base_move`（need + 0.03，整机检查），不通就失败 |
| policies/perceive.py:343-351，374-382 | `PointAtPolicy.execute` / `PresentHeldPolicy.execute` | point、present：位姿 4 档 | F | 仍在 |
| policies/perceive.py:135-148，247-260，301-305 | `ExploreRoomPolicy` / `ExploreFurniturePolicy` / `SearchObjectPolicy` | 视点不可达就跳到下一个 | F | 仍在（探索里转 180° 改成 `straight_base_move`，失败照样跳过） |

### 3.10 原表里没有的（这次刷新发现）

| 位置 | 函数 | 内容 | 类 | 归哪一步 |
|---|---|---|---|---|
| skills.py:1983-1990 | `place` | `microwave_pre_lift`：先竖直抬到台面 +8 cm。死代码：1780 已把微波炉支撑面转给 `place_microwave`，`"in:"` 支撑面拼出来的 `s` 又没有 `furniture` 字段，走不到这里 | W | 直接删（3a） |
| skills.py:1846-1858，1915-1919，1962-1964 | `place` | 微波炉专用的 `search_near`、写死 park `(4.95, 2.18, 165)`、`min_bottom_z`。同样是死代码 | F/S | 直接删（3a） |
| policies/tooluse.py:81-100 | `WipeSurfacePolicy.execute` | 擦拭带：每条边 × 2 档内缩 × 9 个偏移，以机器人当前位置为中心依次试 | F | 已改（3a）：沿整个支撑面四条边采样，最便宜的 8 条进停车点目标集合。预备点上方 6 cm 在 3b 第一项删掉（`wipe_press` 是一次带竖直接近的运动）；`wipe_lift` 8 cm（`LEGACY`）还在，步骤 4 |
| policies/tooluse.py:123-134 | `WipeSurfacePolicy.execute` | 海绵 4 个 yaw 依次试 park | F | 已改（3a）：和擦拭带一起进停车点目标集合 |
| policies/hand.py:83-84，extra.py:362-363，tooluse.py:105、202、327 | Drop / Hover / Wipe / Stir / Pour | 重新停车前先 `stow_load` → `_carry_pose`，把 3.1 的全部变体和退路一起带进来（倒车步骤 2 已删） | W/F | 已改（3a）：`_carry_pose` 的变体和退路随 3.1 删掉；`stow_load` 保留（选停车位前先摆好搬运姿态） |
| policies/extra.py:159-171 | `KnockPanelPolicy.execute` | 敲击点 5 个位置 × 2 种合指方向 | F | 3b（目标采样，按任务几何） |
| policies/extra.py:210-216 | `TouchObjectPolicy.execute` | 4 个腕部朝向依次试 park | F | 3b（目标集合） |
| policies/orientation.py:76-150 | `_turn_in_air` | 手写 staging 点网格（手边 12 个 + 胸前 80 个，取最近 30 个）× 48 个 (phi, dyaw) 组合，外加 1.2 / 3.5 rad 阈值 | W/F | 3b |
| policies/posture.py:52-61 | `_move_posture_joint` | 躯干/腰运动失败 → tuck → 再试 → `relocate`，三级 | F | 3b |
| policies/hand.py:268-281 | `LeftSteadyPolicy.execute` | 左手 IK 不行 → 8 个候选逐个找 park + tuck + 重新导航 | F | 3c（或步骤 5 左臂） |
| policies/embedded.py:148-161 | `GraspArticulatedHandlePolicy.execute` | 把手抓法候选（侧钩、翻转、front pinch），和 3.6 的同一种 | F | 3b |
| policies/bimanual.py:290-306，210-221 | `_grasp_both` / `_park_for_pair` | 4 种躯干/腰姿态 × 4–8 对接触，150 s 预算；park 用手写的半径 × 角度 × yaw ±20° 网格 | F | 3c |
| policies/navigation.py:82-86 | `BackOffWithLoadPolicy.execute` | `distance` 不通就退 `min_distance` | F | 3c（任务级原语保留，两档改成一档） |

## 4. 约束伪装成路点（K 类，步骤 1）

**状态（2026-11-01，步骤 1）：** 持物不甩的慢速和平滑已由入口的时间参数化统一处理（`follow_smooth`、0.5 / 0.25 rad/s），持物不倾斜已在规划器里（`tilt_metric`、`kinematics.tips_over`），`q_hint` 已是规划目标和 IK 种子。下面是规划器到位后仍留在 skill 里的写法，随步骤 3 删到哪个 skill 删到哪。

| 约束 | 还留着的写法 | 位置（行号以 `a0a9574` 为准） | 归哪一步 |
|---|---|---|---|
| 持物不甩（慢速、平滑） | 每处手传 `step`、`steps_per_wp`、`smooth`（只会更慢）；按容器或左手负载降速 | skills.py:65-69, :102/:109, :258/:261, :352-359；hand.py:168-176；tooluse.py:520-524；orientation.py:158, :225；handle_grasp.py:57-60；perceive.py:377；bimanual.py:451 | 3b |
| 持物不大幅换 IK 分支 | 关节变化 >1.2 / 1.0 / 3.5 / 0.8 rad 就拒 | skills.py `held_vertical_move`；orientation.py:116-146, :179 | 3b |
| IK 分支连续 | 拆半程点、反向链、先 `joint_path` 到 park 解 | tooluse.py:468；orientation.py:160；planner.py `_ik_sequence`；embedded.py:168-175；bimanual.py:633；skills.py:1411-1413 | 3b、3c |
| 持物不倾斜 | `R_fix` 下垂补偿 | skills.py `place_flat`（`R_fix`） | 3c |
| 搬运高度下限 | 作为 `_goto_park` 参数传 `min_bottom_z`，各处取值不一致 | skills.py:1640, :1955-1958；tooluse.py:324 vs :423 | 3a |
| 躯干、腰固定或限位 | 临时改 `kin.lo` / `kin.hi` | hand.py:255-267；bimanual.py:20-38；tooluse.py:179-181 | 步骤 5 |
| 正对边缘 | 写成 park 打分 | skills.py:2442-2446 | 3c |
| 转腕段 | `cart_path` + 直接 `follow`，没有 clearance 标签 | skills.py:2485-2490 | 3c |

## 5. 接触段（C 类，步骤 4）的补充

计划步骤 4 的预设表之外：

- **`button_align` 不是接触段**（appliance_generic.py:71、skills.py:2618）：它是到按钮前 12 cm 的空中段，应改成中继位姿 + 规划。
- **接近段被拆成两段**：`corner_pre` + `corner_grasp`（skills.py:1428-1429）、`edge_pre` + `edge_grasp`（:1527-1528）、`upright_top_in` + `upright_top_grasp`（orientation.py:311-312），合并成一段。
- **`upright_top_pre` 是空中段却用 `LEGACY`**（orientation.py:311）。
- **左臂的接触段不沿直线**：`handover_left_contact` 走 `_left_path`（步骤 5，左臂走同一套入口后解决）。
- **门和推门的 `coll_kw` 逐段切换**（skills.py:532/590/621/623、:763/781/790/793；embedded.py:146-184 存进 `rig._handle_grasp` 跨 skill 生效）：换成 `handle` 预设。

## 6. 场景特例（S 类）

**任务差异，保留：**

| 位置 | 内容 |
|---|---|
| skills.py:712-714 | 有把手的转动门：推门而不是拉把手 |
| skills.py:552-553 | 圆形拉手不能勾 |
| skills.py:1324-1325 | 地上的扁平物用 corner pinch |
| skills.py:1776-1777 | 边缘捏的物体走 `place_flat` |
| extra.py:363-371 | hover："上方"的高度怎么定义 |
| tooluse.py:334-375 | 把手抓法时侧倒（夹持扭矩） |
| articulation.py:10-12 | 微波炉电动门走按键 |
| mobile.py:219-220 | 微波炉不支持边走边放 |

**避障或调出来的常数，规划器到位后删：**

| 位置 | 内容 |
|---|---|
| skills.py:558-574 | 微波炉开门 park：`−0.555·along −0.25·outward`、yaw+15° |
| skills.py:577 | `n_best`：冰箱 1、微波炉 3、其他 10 |
| skills.py:1111-1143 | `"breakfast_fridge/"` → `(6.246, 2.337, 135)`；`"kitchen_microwave"` → `(4.8, 1.7, 150)`；按场景改 `max_tries`、`q_start`、`travel_q` |
| skills.py:1586-1587 | 微波炉放入的 4 个写死世界坐标 park |
| skills.py:1853-1868 | 门后层板：search_near +0.75 m、yaw+30° |
| skills.py:2595 | 按键的写死 park 偏移 |
| skills.py:2694-2698, :2727-2729 | 给门让路的写死位姿 `(5.1, 1.6, 150)` |
| skills.py:2411-2417 | 书架：中段加分、短边 +0.4 |
| skills.py:2257-2290 | `free_spots`：微波炉 −0.004、柜台内缩 4 cm、`"breakfast_fridge"` 的 margin |
| skills.py:2361-2366 | `_behind_door_hint`：角点内缩 |
| skills.py:78-79 | edge 抓法搬运时 +6 cm（书下垂，应进持物碰撞模型；同 3.1） |
| skills.py:1790-1791 | 深容器在沿口上方松手（用松手高度避开两壁） |
| embedded.py:227-297 | 微波炉取物整套"把放入倒过来"的编排；只适用于开口朝 −y |

**拿不准，要看：**

| 位置 | 内容 | 疑问 |
|---|---|---|
| skills.py:56-57 | 物体低于 0.30 m 才先站起 | 任务差异还是可达性 |
| skills.py:931, :939 | 高处 top pinch 缩短接近和抬起距离 | 可达性特例 |
| skills.py:1797-1807 | 深桶目标点偏向机器人一侧 | 可达性，不是避障 |
| hand.py:212-226 | regrasp 已在空位上方就直接放下（避免转腕让圆柱滚出） | 夹持力学 |
| bimanual.py:289-307 | 双手抓取的姿态搜索顺序按抓法和高度切换 | 可达性，数值手调 |

## 7. 碰撞配置和临时状态（X 类，步骤 5）

| 内容 | 位置 |
|---|---|
| `coll_kw = {"ignore_fingers": True}` 在 skill 入口整体设置，不恢复 | skills.py:76, :1105/:1177, :1273/:1295, :1408/:1425, :1514/:1524, :1596/:1643, :1833, :1959, :2428/:2465, :2594；hand.py:93；extra.py:156/:208/:379；tooluse.py:111/:229/:363；orientation.py:105/:292；sticky.py:316；embedded.py:233；contact.py:150/:175；appliance_generic.py:60；rig.py:609 |
| `coll_kw = {}` 清空，会冲掉正在生效的 `hand_touches_part` | posture.py:56-57 |
| 选 park 时临时改 `coll_kw` | skills.py:196-227, :453-458；planner.py:194-196；base_motion.py:115-116；mobile.py:164/:236 |
| 临时改腰的上限避障 | skills.py:673-679, :971-973, :1475 |
| 只为检查临时 `kin.set_base` | skills.py:216, :478, :543, :769, :2598-2606 |
| `temp_obstacles`（空操作）仍在用 | skills.py:1072-1076, :1278, :2085-2092；contact.py:165 |
| `world.left_active` 只写不读 | hand.py:253, :280 |
| `LeftArmFoldPolicy` 直接插值收左臂；和 `skills._fold_left` 重复 | base_motion.py:204-208 |
| `move_left_to` 误差 >0.03 抛错，`move_to` 只记日志 | rig.py |

## 8. 归类问题的结论（2026-11-02）

1. 松手后沿放入方向退几厘米的段（`regrasp_clear`、`release_back`）是 C 类，步骤 1 已改成 `LEAVE_CONTACT`；退完之后再抬、再横移的才是 W。
2. `pick_lift` 竖直抬，方向取支撑面法向，侧抓也一样；直线段缩短到刚离开支撑面，之后交给规划器。
3. `BackOffWithLoadPolicy` 保留为任务级原语（步骤 2 已改成整机检查的直线后退）。
4. push 不再固定分段，推到够不着为止再换停车点。
5. 目标采样（wipe 的擦拭带和朝向、knock/touch 的接触点和朝向、stir 的接近方向、pour 的腕角和沿口偏移、upright 的转腕位置）保留，但采样范围由任务几何决定，不由站位决定。

另外 F 类里的换策略全部删掉。细节见 `COLLISION_PLAN.md` 步骤 3。

## 9. 顺手发现的问题

没核实，来自阅读：

- `PickFromCavityPolicy` 的前方、撤出方向全部写死世界 −y（embedded.py:241-296），没用算好的 `axis` / `sign`。
- `check_held` 在滑移 0.05–0.08 且指缝 >8 mm 时静默重锚（skills.py:147-151），等于把"滑了"当成没滑。
- `stow_load` 的 `min_bottom_z` 在 pour 里前后不一致（tooluse.py:324 用 rim+0.03，:423 用 rim+0.12）。

`place()` 里微波炉分支的死代码见 3.10。
