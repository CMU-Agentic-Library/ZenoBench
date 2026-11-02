# 运动代码删除清单（2026-11-01）

配合 `COLLISION_PLAN.md` 使用：这里列的是代码里要删掉或改写的"特殊实现"，每条标了归哪一步。行号以 `a0a9574` 加未提交改动的工作区为准；动代码之前先按函数名重新定位。

**来源：** 逐个阅读 `zeno_skills/` 下 248 处运动调用（`move_to`、`move_left_to`、`joint_path`、`follow*`、`drive_base`、`tuck`、`_back_off`、`held_vertical_move`、`_carry_pose`、`_clear_for_tuck`）的上下文，加上 skill 内部的重试循环、变体列表和按家具分支。分类是读代码判断的，个别条目可能归错；第 9 节列的几条已经回到代码核实过。

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

## 1. 入口层（`rig.py`、`planner.py`）

这一层不先收拾，后面删路点时退路的行为就不对。**放进步骤 1。**

**状态（2026-11-01，步骤 1）：** L2 并进 `Motion.cart_path`；L4、L5 并进 `Motion.plan_to` 的关节目标一档（`q_hint` 重解为目标和种子，查碰撞）；退路改为 `_straight_move`（不查碰撞的直线，没有 IK 时关节插值，朝 `q_hint` 摆动 >1 rad 仍规划）；`_joint_path` 的倾斜检查改用 `kinematics.tips_over`，`joint_from_contact` 删除；`tuck` 改为直接规划 `q → rest`，候选列表和夹爪判断删除（夹爪判断移到 `_move_with_retry_impl`）；`follow` 的慢速、平滑按持物统一处理。`_left_path`、`follow_both`、`joint_path_via` 留给步骤 5；`planner.py` 三项暂不动，理由见 `COLLISION_PLAN.md` 步骤 1 实施记录。

**`move_to` 现在的各级退路：**

| 级 | 位置 | 内容 | 处理 |
|---|---|---|---|
| L0 | rig.py:350 | 起点在碰撞中就不规划，直接走退路 | 保留；步骤 1 用 `held_on` 处理后应很少触发 |
| L1 | rig.py:371 | 直线 `cart_path` | 保留 |
| L2 | rig.py:372-381 | 步长改 0.02 重算同一条直线，再加密 | 并进 `cart_path` |
| L3 | rig.py:382-388 | `plan_to` 约束规划 | 保留，作为唯一的规划器 |
| L4 | rig.py:389-396 | `joint_path(q_hint)`；摆动 >1 rad 时强制查碰撞 | `q_hint` 改成 L3 的种子或目标 |
| L5 | rig.py:397-401 | `ik_global` 换分支后走关节空间 | 删；接触段在这里会变成不沿直线的关节插值 |
| 退路 | rig.py:359 | `plan(LEGACY)`：把 L1–L5 整条链关掉检查再跑一遍 | **和计划原则 2 不符**，收敛成"不查碰撞的 L1" |

**其他入口：**

| 位置 | 内容 | 类 | 处理 |
|---|---|---|---|
| rig.py:455-459 | `_joint_path`：直线无碰撞但持物倾斜超 `CARRY_TILT` 才改用 carry 规划 | K | 不倾斜写成规划约束 |
| rig.py:461-465 | `_joint_path`：起点碰撞、终点不碰时直接关节插值，不查，也不记 `clearance_fallback` | F | 并进入口退路 |
| rig.py:584-596 | `_left_path`：直线失败 → `ik_global` → 有时 cuRobo、有时直接插值；左臂没有 `plan_to`，也没有持物碰撞 | F | 步骤 5，左臂走同一套入口 |
| rig.py:609-622 | `tuck`：`ignore_fingers`；4 种手写前置后撤（+0.15 z、后退再抬、+0.30 z）依次试 | W/F | 直接规划 `q → rest` |
| rig.py:623 | `for target in (self.kin.rest,)`：只剩一个元素的候选列表 | X | 删 |
| rig.py:635 | 夹爪闭着就不允许规划收臂 | X | 移到调用方 |
| rig.py:519-557 | `follow_both`：双臂只有直线插值，按 `max(3, n//8)` 个样本稀疏检查 | X | 步骤 5，双臂要有规划或至少逐点检查 |
| rig.py:282-320 | `follow`：0.6×URDF 速度上限，`smooth=` 由调用方开关 | K | 慢速和平滑交给规划器的时间参数化 |
| rig.py:426 | `joint_path_via`：直接插值，不做任何检查 | X | 步骤 5，`follow` 只收检查过的路径 |
| planner.py:27-37 | `_ik_sequence`：正向链失败就反向链（为了 IK 分支连续） | K | 改成种子 |
| planner.py:48 | `_chain`：park 搜索用直线判可达，执行时还有 L3–L5，两边判据不一致 | X | 入口收敛后两边统一 |
| planner.py:160-219 | `find_park`：`near` 是三元组时 cost=-1，跳过收臂姿态、展开、可达路径三项检查；skills.py:566 和 :1912 用它探测手写 park | X | 手写 park 删掉后这条路径一起删 |

## 2. 底盘（B 类，步骤 2）

**状态（2026-11-02）：** 除 hand.py 的 flip 底盘推（接触动作，步骤 4）和 skills.py 的 `clear_microwave_door_sweep`（场景特例，步骤 3）外都已删掉或改成整机规划；`BackOffWithLoadPolicy` 保留为任务级原语，改成整机检查的直线后退。底盘规划器本身的几项（`relax`、`Grid` 只查底盘圆、`R_BASE`、开车时不查手臂、原地转身只查终点）由 `base_planner.py` 解决，见 `COLLISION_PLAN.md` 步骤 2 实施记录。

| 位置 | 内容 |
|---|---|
| skills.py:160-186 | `_load_near_furniture` + `_back_off`：沿 −yaw 盲退，距离变体 `(dist, 0.2, 0.1)`，只查占地 |
| skills.py:196-227 | `_clear_for_tuck`：手写底盘候选格（4 距离 × 8 方向 × 7 dyaw），临时 `set_base`，写死 0.06 m 穿透阈值 |
| skills.py:295-310 | navigate：离打开的转动门 <0.75 m 先退 0.30 m（`navigate_back_from_door`） |
| skills.py:311-319 | navigate：tuck → 失败退 0.35 m 再 tuck → 再 `_clear_for_tuck` 再 tuck（三层，同时是 F） |
| skills.py:326-327 | navigate：持物在支撑面上方时先 `_back_off` |
| skills.py:337-343 | navigate：`margin in (0.15, 0.10, 0.06)` 依次放宽，用加宽 margin 代替持物的碰撞模型（F） |
| skills.py:1628-1638 | 微波炉放入：停到 park 后方 0.45 m，再直线慢速开进去 |
| skills.py:1663 | 微波炉放入的退路里，底盘直接挪 <0.25 m |
| skills.py:1736 | 微波炉撤出：`_back_off(0.35)` |
| skills.py:1967, 1986 | 放餐桌：退 0.40 m，伸手、抬高，再开回原位 |
| skills.py:2099-2104 | 放层板：退 0.40 m，预整形手臂，再开回去 |
| skills.py:2694-2705 | `clear_microwave_door_sweep`：开到写死的 `(5.1, 1.6, 150)` 给门让路，再收臂 |
| tooluse.py:38-39 | `stow_load`：每次 re-park 前都倒车 0.25 m 并收到搬运姿态（Drop、Hover、Wipe、Stir、Pour 都调用） |
| posture.py:19-33 | `TuckArmPolicy`：tuck 失败 → 退 0.30 m → `_clear_for_tuck` |
| posture.py:63-75 | 躯干/腰运动规划失败 → 退 0.35 m 或先收臂再退 |
| bimanual.py:318-343 | 双手抓取：先停在 park 后方 0.35 m，降躯干、伸双臂，再带着伸出的手臂直线开进去 |
| embedded.py:235 | 微波炉取物：直接 `drive_base` 到放入时记下的底盘位姿，不规划、不查占地 |
| hand.py:411-453 | flip：手臂推不动时改用底盘推（同时是 F） |
| navigation.py:80 | `BackOffWithLoadPolicy`：给上层直接调用的 `_back_off`，**要定去留** |

**底盘规划器本身要解决的：**

- planner.py:299-309：`relax`，起点和终点 0.4 m 内的检查放宽（T03 s11 碰倒 `juice_bottle` 来自这里）；
- planner.py:250-281：`Grid` 只取 z<1.0 的盒子，只查底盘圆，门只在 z=0.4 采样；
- rig.py:683-706：`drive_base` 每段边平移边插值 yaw，但 `R_BASE=0.28` 假设底盘朝路径方向；
- rig.py:666：开车时 `BASE_DRIVE`，手臂和持物完全不查；
- mobile.py:25-52：边走边做的 policy 绕过底盘规划器，直接用调用方给的路径点；
- bimanual.py:442：`BimanualCarryPolicy` 自己调 `plan_path(margin=0.18)` + `drive_base`，不经 navigate；
- base_motion.py:150-157、perceive.py:142-148：原地转身只查终点占地，不查转动弧和手臂；
- skills.py:415-422 `_hang_while_driving`：只有在 rest 的手臂才下垂；`drive_raise` 失败只记日志，手臂一直垂着。

## 3. 手臂：避障路点和自写退路（W、F 类，步骤 3）

按计划里的合并顺序排。

### 3.1 `_carry_pose`（skills.py）

| 位置 | 内容 | 类 |
|---|---|---|
| :71-74 | `carry_stand_up` 失败吞掉，继续 | F |
| :82-87 | `for allow in (FREE, LEGACY, +3cm LEGACY)`：带检查不行就关检查，再不行只抬 3 cm 也不查 | F |
| :84 | `carry_up`：先竖直抬到高度再横移 | W |
| :93-116 | 搬运姿态的 5 个变体（xy、z 组合），IK 或执行失败就换下一个 | F |
| :121-131 | `carry_in_via`：tcp+8 cm、半路点、半路点+8 cm | W |
| :132 | 收不回来只记 `carry_in_failed`，手伸在外面开车 | F |
| plan_helpers.py:284-299 | `_carry_bottom_z`：搬运高度抬到台面上已有物体之上，用来避免持物扫倒东西 | W |

### 3.2 place 链（skills.py）

| 位置 | 内容 | 类 |
|---|---|---|
| :1816-1831 | 先试"放平"关系，够不到回退到实测倾斜关系 | F |
| :1874-1899 | `slots_blocked`：手写指缝和邻物的碰撞过滤（因为 `ignore_fingers` 不查手指） | F |
| :1892 | 手腕朝向 8 个变体 | F |
| :1901-1904, :2079-2082 | 越过最高邻物 +3 cm 的点（`place_over_neighbours`） | W |
| :1921-1934 | 没 park 就去掉越障点、8 个 yaw 重来（`place_clearance_dropped`） | F |
| :1939-1940 | `place_level_dropped` | F |
| :1946-1947 | 重测后丢掉越障腿重算 | W |
| :1960-1986 | **餐桌整段**：退 0.40 m → `table_staging` → `table_pre_lift` → 开回 | B/W |
| :2008-2016 | 越障点高度按 `k in (1.0, 0.7, 0.4)` 试 IK | W/F |
| :2029-2046 | `container_pre_lift`，记下 `container_exit_pose` | W |
| :2048-2072 | 贴边时选净空最大的一侧退出（`place_back_from_edge`），距离 `(need, 0.04)` + try/except | W/F |
| :2074-2078 | `place_rise`：先竖直抬再平移 | W |
| :2093-2111 | 层板：直线不通就换"倒车 → 预整形 → 开回"，再失败重新导航 | F/B |
| :2120-2131 | `place_remeasure_fallback`：失败改用重测前的目标 | F |
| :2188-2189 | 松手后退出方向的变体（`retreat_back`、`retreat_base`） | F |
| :2190-2203 | 层板退出 22 cm → 14 cm，全失败只记日志 | F |
| :2204-2213 | `container_exit`：回到桶外 staging 点 | W |
| :2320-2328 | `place_on`：放置点重试 4 次 | F |

### 3.3 `place_flat`（skills.py）

| 位置 | 内容 | 类 |
|---|---|---|
| :2426 | 内层板时加大 `pre`，让书在外侧整本降下来 | W |
| :2429-2517 | `while True` + 最多 2 次被挡、每轮最多 6 个候选点 | F |
| :2451 | 带推入的够不到，就丢掉推入目标重找 park | F |
| :2513 | `flat_back_out`：被挡后退回再换点 | F |
| :2540-2541 | 整段松手、推入失败都吞掉 | F |

### 3.4 drop、hover（policies/hand.py、extra.py）

| 位置 | 内容 | 类 |
|---|---|---|
| hand.py:100-104 | `drop_prelift`：先抬到沿口上方再平移 | W |
| hand.py:91, :106-107 | `drop_above`：松手位姿上方再高 6 cm 的点 | W |
| extra.py:385-389 | `hover_lift` | W |
| extra.py:390-391 | `hover_above`：悬停位姿上方 5 cm | W |

### 3.5 pick（skills.py）

| 位置 | 内容 | 类 |
|---|---|---|
| :935, :1192 | `pick_pre_far`：pre 之外再后退、再抬高的接近点 | W |
| :949-957 | pinch 失败 → `pick_flat` | F |
| :976-990 | 失败 → 放开腰限重试 → 关掉邻居障碍重试 | F |
| :1146-1159 | 找不到 park 后追加旋转的 top pinch | F |
| :1193-1194 | 误差 >8 mm 就 `pick_grasp_fix`，同一目标不查再走一次 | F |
| :1211-1216 | `pick_fail_clear`：抓空后抬 8 cm，失败吞掉 | W |
| :1402/:1427, :1510/:1526 | corner、edge 的 `pre_far` 额外 +3 cm | W |
| :1431-1433 | `corner_grasp_retry` | F |
| :1475-1488 | edge：限腰 → 失败放开重试 | F |
| :1250, :1275-1289 | push：4 个腕部朝向 × push/drag 两种编排 | F |
| :1350-1365 | `pick_flat`：换边重试 | F |

### 3.6 open / close（skills.py）

| 位置 | 内容 | 类 |
|---|---|---|
| :440, :622 | `{verb}_pre_high`：把手前位姿上方 +8 cm | W |
| :765, :785 | 推门的 `pre_high` +4 cm | W |
| :537-541 | 失败过的 park 打 1e9 分排到最后 | F |
| :550-555 | 把手抓法：倾斜 {0, 10°, 20°} × 翻转 + front pinch | F |
| :593-609, :782-787 | 到达后发现门被底盘碰动 → 重解或重找 park | F |
| :639-651 | 后撤 `(0.14, 0.08, 0.04)` → `{verb}_up` +0.12 → for-else 再 +0.08，全失败吞掉 | F/W |
| :686-700 | 失败后记 park、tuck、再调一次 `_move_articulated` | F |
| :715-717 | 推门找不到 park → 换拉把手 | F |
| :799-804 | 推门后撤 `(0.12, 0.06)` | F |

### 3.7 `held_vertical_move` 和其他持物运动

| 位置 | 内容 | 类 |
|---|---|---|
| skills.py:243-268 | 往身体拉回 `(0, .08, .15, .22, .30)` 的变体 + `{label}_stage` 过渡点 + 重试 | F/W |
| hand.py:166-184 | rotate：4 组 `(pull, up)` staging 变体 + `rotate_clear` | F/W |
| hand.py:382-453 | flip：沿弧推 → 直推 3 档 → 底盘推 3 档 → 补推 3 档 → 底盘补推 2 档 | F |
| hand.py:455-461 | `flip_clear` 高度变体，全失败也继续 | W |
| tooluse.py:184-190 | stir：限腰失败 → 放开腰限整套重跑 | F |
| tooluse.py:234 | stir：找不到 park 就缩小搅拌半径 | F |
| tooluse.py:252-257 | `stir_raise`，失败跳过 | W |
| tooluse.py:283-288 | 圆上某点不可达就跳过 | F |
| tooluse.py:387-390 | pour：倾角从 110° 降到 40°，最后只规划竖直位姿 | F |
| tooluse.py:426-434 | `pour_raise` 先竖直抬，失败跳过 | W |
| tooluse.py:435-455 | 实测位姿和计划位姿二选一 | F |
| tooluse.py:473-490, :525-530 | 笛卡尔倾斜或回正走不通 → 换关节空间 | F |
| extra.py:100-108 | wave：举手高度 3 档 | F |
| orientation.py:39-49, :356 | upright：在空中转失败 → 改 hang；pivot 不到 80° → 改 hang | F |
| orientation.py:60-68 | `upright_clear` 高度 3 档 | W |
| orientation.py:215-231 | 放下点 6 个变体 | F |
| orientation.py:243-249, :270-275 | `upright_release_clear` 方向和高度变体 | W/F |
| orientation.py:298-306 | 先找 pivot 的 park，失败找 hang 的 | F |
| orientation.py:341-346 | `upright_pivot_out` 距离 2 档 | F |
| navigation.py:56-63 | `CarryHeightAdjustPolicy` 最多 3 次闭环 | F |

### 3.8 微波炉（skills.py、embedded.py、appliance_generic.py）

| 位置 | 内容 | 类 |
|---|---|---|
| skills.py:1603-1613 | 放入：碗朝向 8 个变体 | F |
| skills.py:1654-1669 | 重测后：写死 park → 近邻搜索 → 沿用原入口，三级退路 | F |
| skills.py:1674-1677 | 插入段带检查走不通，就整段 `LEGACY` | F |
| skills.py:1731-1732 | 撤出失败吞掉 | F |
| skills.py:1735 / skills.py:1172 / embedded.py:234 | 撤出时记下 `microwave_retrieval_q`，取物时回放这个"安全"姿态 | W |
| skills.py:1220-1229 | 取物后沿世界 −y 退 0.10、0.23 | W |
| skills.py:2591/:2617, appliance_generic.py:58/:70 | 按键前位姿上方 +6 cm 的点 | W |
| skills.py:2598-2609 | 优选 park 用 `scene=None` 验证，失败再搜 160 次 | F |
| embedded.py:241-242 | `cavity_pick_front`：前方 10 cm、高 6 cm，世界 −y 写死 | W |
| embedded.py:254-266 | 接触误差 >2 cm → 通用重抓 | F |
| embedded.py:280-296 | 撤出按 y 分 4 段，失败就下一段 | F |

### 3.9 双手、sticky、其余 policy

| 位置 | 内容 | 类 |
|---|---|---|
| bimanual.py:42-49 | 固定躯干 IK：3 轮 × 12 个随机种子 | F |
| bimanual.py:268-278 | 配对 IK 失败 → 改抬躯干 | F |
| bimanual.py:371-382 | 跟随被推动的物体，比例 `(1.0, 0.8, 0.6)` | F |
| bimanual.py:417-423 | 报 "overhanging edge" → 插一个 `SlideToEdgePolicy` 再重来 | F |
| bimanual.py:511-528 | handover：4 个展示位姿依次试 | F |
| bimanual.py:554-560 | `handover_right_clear` 2 档 | F |
| bimanual.py:596-605 | 先把躯干升顶、腰放直，让写死的展示位姿可达 | W |
| bimanual.py:610-639 | 3 个轴角 × 4 个位置，12 个手写候选依次执行 | F |
| sticky.py:251-256, :421-427 | `sticky_clear` 上抬 3 档 / 2 档 | F |
| sticky.py:317-333 | `_reach`：pre → above → 6 个机身系写死候选 | F |
| embedded.py:44-59 | `PrepareFloorReachPolicy`：48 个预抓取候选（为了不让手掌穿地） | F |
| embedded.py:166 | `handle_pre_high` +8 cm | W |
| embedded.py:176-178 | `joint_path` 失败 → `move_to(q_hint)` | F |
| embedded.py:111-131 | `SlideToEdgePolicy`：失败换方向 | F |
| contact.py:71-79 | drag 不动 → 改 push | F |
| contact.py:94-122 | separate：最多 3 次 push × 7 个方向 | F |
| handle_grasp.py:42 | 无条件先 `tuck()` | W |
| base_motion.py:88-99 | `NavigateToPlacePolicy`：候选位姿逐个 navigate | F |
| base_motion.py:182-190 | retreat 距离 2 档 | F |
| perceive.py:343-351, :374-382 | point、present：位姿 4 档 | F |
| perceive.py:137-140, :256-260, :300-305 | 视点不可达就跳到下一个（覆盖类任务，优先级低） | F |

## 4. 约束伪装成路点（K 类，步骤 1）

这些不能直接删，要先变成规划器认识的约束。

| 约束 | 现在的写法 | 位置 |
|---|---|---|
| 持物不甩（慢速、平滑） | 每处手传 `step`、`steps_per_wp`、`smooth`；按容器或左手负载降速 | skills.py:65-69, :102/:109, :258/:261, :352-359；rig.py:282-320, :667-674；hand.py:168-176；tooluse.py:520-524；orientation.py:158, :225；handle_grasp.py:57-60；perceive.py:377；bimanual.py:451 |
| 持物不大幅换 IK 分支 | 关节变化 >1.2 / 1.0 / 3.5 / 0.8 rad 就拒 | skills.py:249/:254；orientation.py:116-146, :179 |
| IK 分支连续 | 拆半程点、反向链、`q_hint` 种子、先 `joint_path` 到 park 解 | tooluse.py:468；orientation.py:160；planner.py:27-37；embedded.py:168-175；bimanual.py:633；skills.py:1411-1413 |
| 持物不倾斜 | 事后检查直线是否超 `CARRY_TILT`；`R_fix` 下垂补偿 | rig.py:455-459；skills.py:2468-2479 |
| 搬运高度下限 | 作为 `_goto_park` 参数传 `min_bottom_z`，各处取值不一致 | skills.py:1640, :1955-1958；tooluse.py:324 vs :423 |
| 躯干、腰固定或限位 | 临时改 `kin.lo` / `kin.hi` | hand.py:255-267；bimanual.py:20-38；tooluse.py:179-181 |
| 正对边缘 | 写成 park 打分 | skills.py:2442-2446 |
| 转腕段 | `cart_path` + 直接 `follow`，没有 clearance 标签 | skills.py:2485-2490 |

## 5. 接触段（C 类，步骤 4）的补充

计划步骤 4 的预设表之外，这次发现：

- **`button_align` 不是接触段**（appliance_generic.py:71、skills.py:2618）：它是到按钮前 12 cm 的空中段，应改成中继位姿 + 规划。
- **接近段被拆成两段**：`corner_pre` + `corner_grasp`（skills.py:1428-1429）、`edge_pre` + `edge_grasp`（:1527-1528）、`upright_top_in` + `upright_top_grasp`（orientation.py:311-312），合并成一段。
- **`upright_top_pre` 是空中段却用 `LEGACY`**（orientation.py:311）。
- **接触段可能不沿直线**：左臂的 `handover_left_contact` 走 `_left_path`，`move_to` 的 L5 也会把接触段变成关节插值。入口收敛（第 1 节）后解决。
- **`pick_lift` 总是竖直抬**，不沿抓取方向；侧抓时和 C 的定义不一致，需要定（见第 8 节）。
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
| skills.py:1173 | 微波炉取物直接 `drive_base` 开到 park |
| skills.py:1853-1868 | 门后层板：search_near +0.75 m、yaw+30° |
| skills.py:2595 | 按键的写死 park 偏移 |
| skills.py:2694-2698, :2727-2729 | 给门让路的写死位姿 `(5.1, 1.6, 150)` |
| skills.py:2411-2417 | 书架：中段加分、短边 +0.4 |
| skills.py:2257-2290 | `free_spots`：微波炉 −0.004、柜台内缩 4 cm、`"breakfast_fridge"` 的 margin |
| skills.py:2361-2366 | `_behind_door_hint`：角点内缩 |
| skills.py:78-79 | edge 抓法搬运时 +6 cm（书下垂，应进持物碰撞模型） |
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
| 监视器的双重记录：L4 时内层 `joint_path` 和外层 `move_to` 各记一次动作 | rig.py |
| `move_left_to` 误差 >0.03 抛错，`move_to` 只记日志 | rig.py |

## 8. 要你定的

1. **`regrasp_clear`、`release_back` 这类松手后沿放入方向退出的段**：按定义是 C（保留），计划之前把 `regrasp_clear` 列为要删。倾向：沿放入方向退几厘米是 C；退完之后再抬、再横移的才是 W。
2. **`pick_lift` 竖直抬**：侧抓时不是沿抓取方向。改成沿抓取方向，还是承认"抓后竖直抬"也是 C？
3. **`BackOffWithLoadPolicy`**：它是给上层规划直接调用的原语。删 `_back_off` 时一起删，还是保留为任务级动作？
4. **push 按臂展分段、每段重新停车**（skills.py:1252-1256）：整机规划后是否还需要分段。
5. **目标采样**（wipe 的擦拭带和朝向、knock/touch 的接触点和朝向、stir 的接近方向、pour 的腕角和 lip 偏移、upright 的转腕位置）：这些是在运动前挑中继位姿，不是失败后的退路，倾向保留；以后可以统一成"目标区域交给规划器"。

**结论（2026-11-02）：** 1 是 C 类（步骤 1 已改成 `LEAVE_CONTACT`）；2 竖直抬，方向取支撑面法向，直线段缩短到刚离开支撑面；3 保留为任务级原语（步骤 2）；4 不再固定分段，推到够不着为止再换停车点；5 保留，但采样范围由任务几何决定，不由站位决定。另外 F 类里的换策略全部删掉。细节见 `COLLISION_PLAN.md` 步骤 3。

## 9. 顺手发现的问题

已经回到代码核实：

- **`place()` 里微波炉的分支是死代码。** skills.py:1774 遇到微波炉支撑面已经 `return place_microwave(...)`，而 `"in:"` 支撑面拼出来的 `s` 没有 `furniture` 字段，所以 :1840-1852、:1909-1913、:1956-1957 的微波炉部分、:1988-1995 都走不到。可以直接删。
- **`table_staging` 往世界 +x 伸手**（skills.py:1973-1974，`forward[0] += 0.20`），和机器人朝向无关。机器人不朝 +x 时方向是错的。这段整体属于第 2、3 节要删的餐桌编排。
- **入口退路重跑整条链**（rig.py:359），见第 1 节。

没核实，来自阅读：

- `PickFromCavityPolicy` 的前方、撤出方向全部写死世界 −y（embedded.py:241-296），没用算好的 `axis` / `sign`。
- `check_held` 在滑移 0.05–0.08 且指缝 >8 mm 时静默重锚（skills.py:147-151），等于把"滑了"当成没滑。
- `stow_load` 的 `min_bottom_z` 在 pour 里前后不一致（tooluse.py:324 用 rim+0.03，:423 用 rim+0.12）。
