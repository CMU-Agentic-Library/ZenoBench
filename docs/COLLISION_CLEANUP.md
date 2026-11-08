# 运动代码删除清单

配合 `COLLISION_PLAN.md` 使用：这里只列代码里**还没删、还没改**的"特殊实现"，每条标了类别和归哪一步（计划第 6 节的 6.x）。做完一条就把它从表里删掉，不留"已删"记录（历史在 git 里）。位置按文件和函数名给，不写行号。

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

R 类不列。

## 1. 入口层（`rig.py`、`planner.py`）

| 位置 | 内容 | 类 | 处理 |
|---|---|---|---|
| rig.py `_left_path` | 直线失败 → `ik_global` → 有时 cuRobo、有时直接插值；左臂没有 `plan_to`，也没有持物碰撞 | F | 步骤 5，左臂走同一套入口 |
| rig.py `follow_both` | 双臂只有直线插值，按 `max(3, n//8)` 个样本稀疏检查 | X | 步骤 5，双臂要有规划或至少逐点检查 |
| rig.py `joint_path_via` | 直接插值，不做任何检查 | X | 步骤 5，`follow` 只收检查过的路径 |
| planner.py `_ik_sequence` | 正向链失败就反向链（为了 IK 分支连续） | K | 改成种子；手写 park 删掉时再看（6.4） |
| planner.py `_chain` | park 搜索用直线判可达，执行时直线不通还会规划，两边判据不一致 | X | pick / place 11-08 已不用（`park_search.find_park` + 技能的计划构造函数，搜索和执行同一套，`MOTION_ARCHITECTURE.md`）；其余技能迁到新分层时一起删（6.3、6.4） |
| planner.py `find_park` | `near` 是三元组时 cost=-1，跳过收臂姿态、展开、可达路径三项检查；`_move_articulated` 和 `place` 用它探测手写 park | X | 手写 park 删掉后这条路径一起删 |

## 2. 底盘（B 类）

| 位置 | 内容 | 处理 |
|---|---|---|
| policies/hand.py `FlipFlatPolicy` | 手臂推不动时改用底盘推（`footprint_clear` + `drive_base`，同时是 F） | 步骤 4；换策略部分 6.3 删 |
| policies/tooluse.py `WipeSurfacePolicy` | wipe 的底盘推（擦拭行程） | 步骤 4 |
| skills.py `clear_microwave_door_sweep` | 开到写死的 `(5.1, 1.6, 150)` 给门让路，再收臂 | 6.4 |
| policies/mobile.py 三处 `drive_base` | 边走边伸手 / 抓 / 放：行驶中手臂在动，没有逐点整机检查 | 已停用（`mobile.DISABLED`）；整机规划之前不恢复 |

## 3. 手臂：避障路点和自写退路（W、F 类）

顺序按计划：3.2–3.4（place 系）在 6.2；3.6、3.7、3.10 在 6.3；3.8、3.9 和第 6 节在 6.4。

### 3.1 搬运姿态

| 位置 | 内容 | 类 | 处理 |
|---|---|---|---|
| policies/plan_helpers.py `_carry_bottom_z` | 搬运高度抬到目的地台面上已有物体之上（最多 12 cm），用来避免持物扫倒东西 | W | 先给底盘规划器加"换搬运高度"再删（计划第 7 节）；删掉时 T13 bowl_on_cabinet 开往餐桌搜到上限 |
| skills.py `_carry_pose` | 夹在边上的书搬运时 `min_bottom_z` +6 cm（书下垂） | S | 下垂进持物碰撞模型；随 6.2 书的放置 |
| skills.py `_carry_pose` | `carry_in` 走 `FREE_ELSE_STRAIGHT`：规划不出来就不查碰撞的直线（11-07 全量 5 次）；一个搬运目标都没有 IK 就留在原处带着开（`carry_pose_kept`，11-07 全量 11 次） | F | pick 里 11-08 已删（去搬运姿态进了 pick 的计划，`skill_plans.plan_pick`）；navigate 出发前、place / drop / hover 等选停车点前那一处还在，等这些技能迁到新分层 |

### 3.2 place（skills.py `place`、`place_on`）

计划 6.2 重写 `place()`，下面这些随重写删掉。

| 位置 | 内容 | 类 |
|---|---|---|
| `place` | 柜里层板：按门轴位置猜开口朝向，`search_near` 加手写偏置；离目标超过 1 m 就不按距离排序 | S |
| `place` | `kind == "corner"` 的分支（corner 捏取已删，死代码） | — |
| `place` | `free_spots` 的 3 cm 网格、邻物余量 7 / 4.5 / 2 cm 和柜台内缩 4 cm 拍定（放下高度、`PLACE_APPROACH` 已不用） | 常数 |

### 3.3 `place_flat`（skills.py）

计划 6.2 把书并进 `place()`，整个函数删掉。

| 内容 | 类 |
|---|---|
| 内层板时加大 `pre`，让书在外侧整本降下来 | W |
| `while True` + 最多 2 次被挡、每轮最多 6 个候选点 | F |
| 带推入的够不到，就丢掉推入目标重找 park | F |
| `flat_turn`：先用直线转手腕到放置朝向 | W |
| `flat_back_out`：被挡后退回再换点 | F |
| `R_fix`：按书的下垂补偿手腕 | K |
| 松手后下沉 1.5 cm、退 10 cm、合指、推满、上抬，整段 `LEGACY`，异常吞掉（`retreat_short`） | W/F/C |

### 3.4 drop、hover（policies/hand.py、extra.py）

| 位置 | 内容 | 类 |
|---|---|---|
| `HoverOverPolicy.execute` | 停车点验证不看之后能不能收臂（drop 已查，`_drop_check`） | — |

### 3.5 pick（skills.py）

| 位置 | 内容 | 类 | 处理 |
|---|---|---|---|
| `_pick_pinch_core` | 候选逐个找停车点（`for g in cands`） | F | 11-08 已改：所有候选一个目标集合（`park_search.find_park`）；微波炉里取物还是逐个（6.4） |
| rig.py `Rig.leave`（`pick_lift`） | 抬起段 6 cm 求不出 IK 就减半，到 `LEAVE_MARGIN` 还不行就不抬直接进下一段；停车点搜索只查往上 `PICK_LEAVE_CHECK`（3 cm）有 IK，不是执行的那条线 | F | pick 里 11-08 已删（抬起段进了计划，`primitives.contact_extent`：到头还碰就失败）；`Rig.leave` 本身还给 `pick_fail_clear`、微波炉取物、开关门用 |

pick 里的微波炉取物在 3.8，冰箱层板、微波炉的停车点种子在第 6 节。

### 3.6 open / close（skills.py）

| 位置 | 内容 | 类 |
|---|---|---|
| `_handle_targets` / `_move_articulated` | `{verb}_pre_high`：把手前位姿上方 +8 cm | W |
| `_push_close` | 推门的 `pre_high` +4 cm | W |
| `_move_articulated` / `score` | 失败过的 park 打 1e9 分排到最后 | F |
| `_move_articulated` | 把手抓法：倾斜 {0, 10°, 20°} × 翻转 + front pinch 依次试 | F |
| `_move_articulated` / `_push_close` | 到达后发现门被底盘碰动 → 重解或重找 park | F |
| `_move_articulated` | `{verb}_back` 后撤 `(0.14, 0.08, 0.04)` 三档、`{verb}_up` +0.12 再 +0.08，全失败吞掉 | F/W |
| `_move_with_retry_impl` | 失败后记 park、tuck、再调一次 `_move_articulated` | F |
| `close_articulated` | 推门找不到 park → 换拉把手 | F |
| `_push_close` | `close_push_back` 后撤 `(0.12, 0.06)` 两档 | F |

### 3.7 `held_vertical_move` 和其他持物运动

| 位置 | 内容 | 类 |
|---|---|---|
| skills.py `held_vertical_move` | 往身体拉回 `(0, .08, .15, .22, .30)` 的变体 + `{label}_stage` 过渡点 + 重试，带 1.2 / 1.0 rad 阈值 | F/W |
| policies/hand.py `RotateHeldPolicy.execute` | rotate：4 组 `(pull, up)` staging 变体 + `rotate_clear` | F/W |
| policies/hand.py `FlipFlatPolicy.execute` | flip：沿弧推 → 直推 3 档 → 底盘推 3 档 → 补推 3 档 → 底盘补推 2 档 | F |
| policies/hand.py `FlipFlatPolicy.execute` | `flip_clear` 高度变体，全失败也继续 | W |
| policies/tooluse.py `StirContainerPolicy.execute` | stir：限腰失败 → 放开腰限整套重跑 | F |
| policies/tooluse.py `StirContainerPolicy._stir` | 找不到 park 就缩小搅拌半径；`stir_raise` 失败跳过；圆上某点不可达就跳过 | F/W |
| policies/tooluse.py `PourIntoPolicy.execute` | 倾角从 110° 降到 40°，最后只规划竖直位姿；`pour_raise` 先竖直抬、失败跳过；实测位姿和计划位姿二选一；笛卡尔倾斜或回正走不通换关节空间 | F/W |
| policies/extra.py `WaveHandPolicy.execute` | 举手高度 3 档 | F |
| policies/orientation.py `UprightObjectPolicy.execute` / `_hang_upright` | 在空中转失败 → 改 hang；pivot 不到 80° → 改 hang | F |
| policies/orientation.py `_turn_in_air` | `upright_clear` 高度 3 档 | W |
| policies/orientation.py `_set_down_upright` | 放下点 5 个变体（d = 0–0.20） | F |
| policies/orientation.py `_set_down_upright` / `_hang_upright` | `upright_release_clear` 方向和高度变体（`LEGACY`） | W/F |
| policies/orientation.py `_hang_upright` | 先找 pivot 的 park，失败找 hang 的；`upright_pivot_out` 距离 2 档 | F |
| policies/navigation.py `CarryHeightAdjustPolicy.execute` | 最多 3 次闭环 | F |

### 3.8 微波炉（skills.py、policies/embedded.py、policies/appliance_generic.py）

| 位置 | 内容 | 类 |
|---|---|---|
| skills.py `insert_microwave_cavity` | 4 个写死的候选 park × 碗朝向 8 个变体 | F/S |
| skills.py `insert_microwave_cavity` | 重测后：写死 park → 近邻搜索 → 沿用原入口，三级退路 | F |
| skills.py `insert_microwave_cavity` | `microwave_insert` 无条件 `LEGACY` | F |
| skills.py `withdraw_microwave_cavity` | `microwave_retreat` 是 `FREE_ELSE_STRAIGHT`，撤出失败吞掉 | F |
| skills.py `withdraw_microwave_cavity` / `_pick_pinch_core` / `PickFromCavityPolicy.execute` | 撤出时记下 `microwave_retrieval_q`，取物时作为到达姿态回放 | W |
| skills.py `_pick_pinch_core` | 取物后沿世界 −y 退到腔体口外 10 cm、23 cm | W |
| skills.py `approach_microwave_button`；按键 policy | 按键前位姿上方 +6 cm 的点 | W |
| skills.py `approach_microwave_button` | 优选 park 用 `scene=None` 验证，失败再搜 160 次 | F |
| policies/embedded.py `PickFromCavityPolicy.execute` | `cavity_pick_front`：前方 10 cm、高 6 cm，世界 −y 写死；接触误差 > 2 cm → 通用重抓；撤出按 y 分 4 段，失败就下一段 | W/F |

### 3.9 双手、sticky、其余 policy

| 位置 | 内容 | 类 |
|---|---|---|
| policies/bimanual.py `_fixed_torso_ik` | 固定躯干 IK：3 轮 × 12 个随机种子 | F |
| policies/bimanual.py `_lift_together` | 配对 IK 失败 → 改抬躯干 | F |
| policies/bimanual.py `_grasp_both` | 跟随被推动的物体，比例 `(1.0, 0.8, 0.6)` | F |
| policies/bimanual.py `BimanualFlatPickPolicy.execute` | 报 "overhanging edge" → 插一个 `SlideToEdgePolicy` 再重来 | F |
| policies/bimanual.py `HandoverRightToLeftPolicy.execute` | 4 个展示位姿依次试；`handover_right_clear` 2 档 | F |
| policies/bimanual.py `_present_for_horizontal_left` | 先把躯干升顶、腰放直，让写死的展示位姿可达；3 个轴角 × 4 个位置共 12 个候选依次执行 | W/F |
| sticky.py `StickyHands.drop_caught` / `StickyHands.place` | `sticky_clear` 上抬 3 档 / 2 档 | F |
| sticky.py `StickyHands._reach` | pre → above → 6 个机身系写死候选 | F |
| policies/embedded.py `PrepareFloorReachPolicy.execute` | 48 个预抓取候选 | F |
| policies/embedded.py `GraspArticulatedHandlePolicy.execute` | `handle_pre_high` +8 cm；`joint_path` 失败 → `move_to(q_hint)`；把手抓法候选（侧钩、翻转、front pinch） | W/F |
| policies/embedded.py `SlideToEdgePolicy.execute` | 失败换方向 | F |
| policies/contact.py 拉取 policy（`PULL`） | drag 不动 → 改 push | F |
| policies/contact.py `SeparateFromNeighbourPolicy.execute` | 最多 3 次 push × 7 个方向 | F |
| policies/handle_grasp.py 杯柄抓取 policy | 无条件先 `tuck()` | W |
| policies/perceive.py `PointAtPolicy.execute` / `PresentHeldPolicy.execute` | 位姿 4 档 | F |
| policies/perceive.py `ExploreRoomPolicy` / `ExploreFurniturePolicy` / `SearchObjectPolicy` | 视点不可达就跳到下一个 | F |

### 3.10 其他

| 位置 | 内容 | 类 | 归哪一步 |
|---|---|---|---|
| policies/tooluse.py `WipeSurfacePolicy.execute` | `wipe_lift` 8 cm（`LEGACY`） | C | 步骤 4 |
| policies/extra.py `KnockPanelPolicy.execute` | 敲击点 5 个位置 × 2 种合指方向依次试 | F | 6.3（目标采样，按任务几何） |
| policies/extra.py `TouchObjectPolicy.execute` | 4 个腕部朝向依次试 park | F | 6.3（目标集合） |
| policies/orientation.py `_turn_in_air` | 手写 staging 点网格（手边 12 个 + 胸前 80 个，取最近 30 个）× 48 个 (phi, dyaw) 组合，外加 1.2 / 3.5 rad 阈值 | W/F | 6.3 |
| policies/posture.py `_move_posture_joint` | 躯干 / 腰运动失败 → tuck → 再试 → `relocate`，三级 | F | 6.3 |
| policies/hand.py `LeftSteadyPolicy.execute` | 左手 IK 不行 → 8 个候选逐个找 park + tuck + 重新导航 | F | 6.4 或步骤 5 |
| policies/bimanual.py `_grasp_both` / `_park_for_pair` | 4 种躯干 / 腰姿态 × 4–8 对接触，150 s 预算；park 用手写的半径 × 角度 × yaw ±20° 网格 | F | 6.4 |
| policies/navigation.py `BackOffWithLoadPolicy.execute` | `distance` 不通就退 `min_distance` | F | 6.4（任务级原语保留，两档改成一档） |

## 4. 约束伪装成路点（K 类）

持物不甩、不倾斜、`q_hint` 保持分支已经在入口和规划器里（计划第 3 节）。下面是还留在技能里的写法，改到哪个技能删到哪。

| 约束 | 还留着的写法 | 位置 | 归哪一步 |
|---|---|---|---|
| 持物不甩（慢速、平滑） | 每处手传 `step`、`steps_per_wp`、`smooth`（只会更慢）；按容器或左手负载降速 | skills.py、hand.py、tooluse.py、orientation.py、handle_grasp.py、perceive.py、bimanual.py | 6.3 |
| 持物不大幅换 IK 分支 | 关节变化 > 1.2 / 1.0 / 3.5 / 0.8 rad 就拒 | skills.py `held_vertical_move`；orientation.py `_turn_in_air` | 6.3 |
| IK 分支连续 | 拆半程点、反向链、先 `joint_path` 到 park 解 | tooluse.py；orientation.py；planner.py `_ik_sequence`；embedded.py；bimanual.py | 6.3、6.4 |
| 搬运高度下限 | 作为 `_goto_park` 参数传 `min_bottom_z`，各处取值不一致（pour 里 rim + 0.03 和 rim + 0.12） | skills.py；tooluse.py | 6.2、6.3 |
| 躯干、腰固定或限位 | 临时改 `kin.lo` / `kin.hi` | hand.py；bimanual.py；tooluse.py | 步骤 5 |

## 5. 接触段（C 类，步骤 4）的补充

计划 6.5 的预设表之外：

- **`button_align` 不是接触段**（appliance_generic.py、skills.py）：它是到按钮前 12 cm 的空中段，应改成中继位姿 + 规划。
- **接近段被拆成两段**：`upright_top_in` + `upright_top_grasp`（orientation.py），合并成一段。
- **`upright_top_pre` 是空中段却用 `LEGACY`**（orientation.py）。
- **左臂的接触段不沿直线**：`handover_left_contact` 走 `_left_path`（步骤 5，左臂走同一套入口后解决）。
- **门和推门的 `coll_kw` 逐段切换**（skills.py `_move_articulated`、`_push_close`；embedded.py 存进 `rig._handle_grasp` 跨技能生效）：换成 `handle` 预设。

## 6. 场景特例（S 类）

**任务差异，保留：**

| 位置 | 内容 |
|---|---|
| skills.py `close_articulated` | 有把手的转动门：推门而不是拉把手 |
| skills.py `_move_articulated` | 圆形拉手不能勾 |
| extra.py `HoverOverPolicy` | hover："上方"的高度怎么定义 |
| tooluse.py `PourIntoPolicy` | 把手抓法时侧倒（夹持扭矩） |
| articulation.py | 微波炉电动门走按键 |
| mobile.py | 微波炉不支持边走边放 |

**避障或调出来的常数，规划器到位后删（6.4）：**

| 位置 | 内容 |
|---|---|
| skills.py `_move_articulated` | 微波炉开门 park：`−0.555·along −0.25·outward`、yaw+15°；`n_best`：冰箱 1、微波炉 3、其他 10 |
| skills.py `_pick_pinch_core` | `"breakfast_fridge/"` → 停车点种子 `(6.246, 2.337, 135)`；`"kitchen_microwave"` → `(4.8, 1.7, 150)`；按场景改 `max_tries`、`q_start`、`travel_q` |
| skills.py `insert_microwave_cavity` | 微波炉放入的 4 个写死世界坐标 park |
| skills.py `place` / `_behind_door_hint` | 门后层板：`search_near` +0.75 m、yaw+30°；角点内缩（6.2 重写时删） |
| skills.py `approach_microwave_button` | 按键的写死 park 偏移 |
| skills.py `clear_microwave_door_sweep` 等 | 给门让路的写死位姿 `(5.1, 1.6, 150)` |
| skills.py `place_flat` | 书架：中段加分、短边 +0.4（6.2 删） |
| skills.py `free_spots` | 微波炉 −0.004、柜台内缩 4 cm、`"breakfast_fridge"` 的 margin |
| skills.py `_carry_pose` | 夹在边上的书搬运时 +6 cm（同 3.1） |
| skills.py `place` | 深容器在沿口上方松手（用松手高度避开两壁） |
| embedded.py `PickFromCavityPolicy` | 微波炉取物整套"把放入倒过来"的编排；只适用于开口朝 −y |

**拿不准，要看：**

| 位置 | 内容 | 疑问 |
|---|---|---|
| skills.py `place` | 深桶目标点偏向机器人一侧 | 可达性，不是避障 |
| hand.py regrasp | 已在空位上方就直接放下（避免转腕让圆柱滚出） | 夹持力学 |
| bimanual.py `_grasp_both` | 双手抓取的姿态搜索顺序按抓法和高度切换 | 可达性，数值手调 |

## 7. 碰撞配置和临时状态（X 类，步骤 5）

| 内容 | 位置 |
|---|---|
| `coll_kw = {"ignore_fingers": True}` 在技能入口整体设置，不恢复 | skills.py（place、place_flat、push、open/close、微波炉）；hand.py；extra.py；tooluse.py；orientation.py；sticky.py；embedded.py；contact.py；appliance_generic.py；rig.py |
| `coll_kw = {}` 清空，会冲掉正在生效的 `hand_touches_part` | skills.py `_carry_pose`；posture.py |
| 选 park 时临时改 `coll_kw` | skills.py；planner.py；base_motion.py；mobile.py |
| 临时改腰的上限避障 | skills.py（open/close、stir 等） |
| 只为检查临时 `kin.set_base` | skills.py |
| `temp_obstacles`（空操作）仍在用 | skills.py `contact_obstacles`；contact.py |
| `world.left_active` 只写不读 | hand.py；bimanual.py |
| `LeftArmFoldPolicy` 直接插值收左臂；和 `skills._fold_left` 重复 | base_motion.py |
| `move_left_to` 误差 > 0.03 抛错，`move_to` 只记日志 | rig.py |

## 8. 归类的结论

1. 松手后沿放入方向退出接触的段是 C 类（`LEAVE_CONTACT`）；退完之后再抬、再横移的才是 W。
2. 抓起后竖直离开支撑面，方向取支撑面法向，侧抓也一样；直线段只到刚离开支撑面，之后交给规划器。
3. `BackOffWithLoadPolicy` 保留为任务级原语（整机检查的直线后退）。
4. push 不固定分段，推到够不着为止再换停车点；动手前按可行性挑腕部朝向和推 / 拖，算目标采样，保留。
5. 目标采样（wipe 的擦拭带和朝向、knock / touch 的接触点和朝向、stir 的接近方向、pour 的腕角和沿口偏移、upright 的转腕位置）保留，但采样范围由任务几何决定，不由站位决定。
6. F 类里的换策略全部删掉。

## 9. 顺手发现的问题

没核实，来自阅读：

- `PickFromCavityPolicy` 的前方、撤出方向全部写死世界 −y，没用算好的 `axis` / `sign`。
- `check_held` 在滑移 0.05–0.08 且指缝 > 8 mm 时静默重锚，等于把"滑了"当成没滑。
- `stow_load` 的 `min_bottom_z` 在 pour 里前后不一致（rim + 0.03 和 rim + 0.12）。
