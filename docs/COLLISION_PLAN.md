# 碰撞与运动规划：执行计划（2026-11-01）

本文是 `COLLISION_AUDIT.md` 的执行版：只写要做什么、按什么顺序、做到什么算完。现状盘点、问题来源和历史记录仍以 `COLLISION_AUDIT.md` 为准，文中的"审计 x.y"指那份文档的章节。

代码基线：`a0a9574` 加未提交的收起姿态修复和监视器扩展（见第 2 节）。

## 1. 目标和原则

**目标：** 每个 skill 只保留必要的中继位姿，中继位姿之间的运动全部由规划器生成：

- 手臂：cuRobo MotionGen，手里的物体算进碰撞模型，需要时加约束（不能倾斜、不能甩、IK 分支连续）。
- 底盘：在 (x, y, 朝向) 空间里规划，可行性用整机碰撞检查判断（底盘占地 + 手臂当前姿态 + 手里的物体）。

**原则：**

1. **碰撞了就补规划器缺的东西，不加路点。** 修法是给规划器碰撞模型、约束或目标区域，而不是加中间点、底盘挪动或备选路径列表。缺规划器，就先把规划器做出来。
2. **规划不出来不让 skill 失败，但退路只有一条，而且只在运动入口里。** 退路就是从当前姿态直线走到这次要去的中继位姿，并记一条 `clearance_fallback`（审计第 6 节决定 1）。它是 `rig` 运动入口里唯一的通用逻辑，不是给每段运动保留旧代码：
   - 删掉的路点连同代码一起删，不能挪进 fallback 分支里留着。规划失败时直接走直线到下一个中继位姿，不再按旧路点链走。
   - skill 和 policy 里不允许出现自己写的退路，例如 `for coll in (FREE, LEGACY)`、"带检查的不行就关掉检查重试"、"规划失败就换一条手写路径"。
   - fallback 是迁移期的安全网，不是常态。`fallbacks` 数要随步骤下降；某段运动反复退回，说明规划器还缺东西（碰撞模型、约束、目标区域），要回到原则 1 去补，而不是在这段运动上加东西。
3. **意外接触只当指标。** `contacts`、`disturbed` 不算任务失败、不扣分（决定 2）；监视器在所有 profile 默认打开（决定 3）。
4. **每一步单独提交。** 倒退可以接受，前提是查清楚不是代码写错（见第 3 节）。

## 2. 当前状态

| 状态 | 内容 | 位置 |
|---|---|---|
| `ef01cb1` | 原阶段 0、1：`clearance.py`（`Allow`、`FREE`、`unchecked`、`LEGACY`）、`rig.clear` 技能作用域（修掉 `coll_kw` 泄漏）、`unexpected_contact` 监视器、`tools/audit_collision.py`、防退化测试 | 审计 7.1、7.2 |
| `a0a9574` | 原阶段 2：第 1 类空中运动 63 处改成 `FREE_ELSE_STRAIGHT`；`LEGACY` 111 → 48 | 审计 7.3 |
| `ca5a550` | 收起姿态修复（`kin.rest` 恢复肘外姿态，下垂姿态只在开车时用）；监视器把手里的物体算进机器人，并记录被推动、碰倒的物体（`disturbed_object`） | 审计 7.5、7.6 |
| 步骤 1 完成：`83d097b`、`d8cfef8` | 手臂入口收敛、手里的物体进碰撞模型、离开接触改成接触段直线（`LEAVE_CONTACT`）、持物限速平滑 | 第 4 节步骤 1 实施记录 |
| 步骤 2 完成：`ea47359`、`348d5c8` | 整机底盘规划器（`base_planner.py`）、B 类删除、第一次全量回归 117/170 | 第 4 节步骤 2 实施记录 |
| 已删除 | 原阶段 4 第一版：`Motion.sweep` / `Rig.drive_clear`、navigate 的手写备选路径、按方向挑选的 `_back_off` | 审计 8.4 |

以上都在分支 `remove-handcoded-motion` 上，没有推送。

**已知还没解决的问题：**

| 问题 | 例子 | 归到哪一步 |
|---|---|---|
| 同样输入，cuRobo 规划结果会分叉 | P07 s10 连跑两次，一次成功一次 "no IK for shake" | 不单独处理，见第 3 节 |
| 底盘规划不留安全余量，开车时会刮到轻的物体 | 11-02 全量里 26 次扰动记在 `drive_base` 上（果汁瓶倾斜 50°、擀面杖 92°） | 待定：给手臂和手里物体的碰撞球加余量 |
| 左臂收起姿态的手指伸出底盘，靠近台面的停车点被整机检查拒掉 | 11-02 全量里 P19 ×2、T09 lid_on 抓锅盖停得太远 | 步骤 5 |
| 左臂收臂直接插值，不经过任何检查 | `LeftArmFoldPolicy` 的 `link_7` 压进岛台 46 mm；P07 s11 碰倒杯子 | 步骤 5 |
| `ignore_fingers` 让带检查的动作不查手指 | `pick_grasp`、`pick_pre_far`、`tuck` 的手指压进台面 | 步骤 4、5 |
| 搬运姿态仍是手写路点（`_carry_pose`） | 5 个搬运姿态变体、`carry_in_via` | 步骤 3 |
| wipe 只在机器人附近选擦拭带，依赖到达时站在哪一侧 | 11-02 全量里 T08 ×3 | 步骤 3 |
| 底盘规划无路可走时，要把能到的区域搜完才报错（几十秒） | 极紧的停车点 | 待定：搜索前先查终点附近能否接上 |
| ~~开到终点附近时手臂和底盘不检查（`relax`）~~ | 步骤 2 删掉 | — |
| ~~到 park 后抬不回收起姿态（`drive_raise_blocked`）~~ | 步骤 2：在哪里抬回由规划器决定 | — |
| ~~刚夹住时起点就在碰撞中，只能退回直线~~ | 步骤 1：接触段 `LEAVE_CONTACT` | — |

## 3. 回归方法

**每一步：** 单元测试、`build_skill_library --check`，加上这一步动到的 skill 对应的几个 episode。

**全量（T、P 全部任务的所有 variation，种子 10、11，共 170 个 episode）：** 批次 `benchmark/batches/v3_sticky_gt_2seeds_video.json`（`sticky/gt`，录像）。只在三个节点跑：步骤 2 完成后、步骤 3 完成后、步骤 5 完成后。和上一次全量比四个数：成功数、`contacts`、`disturbed`、`fallbacks`。第一次的对照是 11-01 那一轮（`benchmark/runs/v3_sticky_gt_1101_2seeds/`，`a0a9574`，108/170；138/170 是 10-31 的数），它不含收起姿态修复。

**倒退怎么处理：** 不要求每一步都不倒退。每个新失败看日志和录像，归到下面三类之一：

| 类别 | 怎么判断 | 怎么办 |
|---|---|---|
| 代码写错 | 删错了中继位姿、`allow` 声明错、参数传错 | 必须修好再往下走 |
| 规划器能力不够 | 记到 `clearance_fallback`，或者退回的直线撞了 | 记下来，可以先接受；之后按原则 1 补规划器缺的东西 |
| 规划随机性 | 同一提交重跑 2–3 次，结果会翻 | 接受 |

**规划随机性不去消除。** cuRobo 的随机种子可以固定，但 GPU 上的原子累加和并行归约本身不确定，`PLAN_TIMEOUT` 按时间截止也受机器负载影响，完全复现不现实（审计 7.4）。所以只用"重跑几次看会不会翻"来区分噪声。

**跑的时候注意：** 24 GB 显卡上最多同时 2 个仿真。

## 4. 步骤

依赖关系：

```
1 手臂规划前提 ──► 3 手臂按 skill 合并 ──► 4 接触动作 ──► 5 左臂和清理
2 底盘规划器（独立）
```

步骤 2 和其他步骤互不依赖，可以并行开发，分开提交。

要删的东西逐条列在 `COLLISION_CLEANUP.md`，每条标了归哪一步。下面每一步的"删掉"只写大类，具体以那份清单为准。

### 步骤 1：手臂规划的前提

**目的：** 让 cuRobo 掌握它规划所需的全部信息，后面才能放心删路点。

- [x] 入口收敛（清单第 1 节）：`move_to` 只留"直线 → `plan_to`"两级，`q_hint` 改成规划种子，删掉加密重算和 `ik_global` 换分支；退路改成真正的"不查碰撞的直线"，现在是把整条链关掉检查重跑一遍，和原则 2 不符。`_joint_path` 里不记日志的 `joint_from_contact` 也并进这条退路。
- [x] 手里的物体在所有空中运动的规划里都算进碰撞模型。现在只有 `_carry_pose` 和带东西的躯干运动用了 `held_collision()`。
- [x] 起点就贴着支撑面的运动（刚抓起、刚放下）：用 `Allow.held_on` 声明只允许碰这个支撑面，不再整段关掉检查。这能消掉 `pick_lift` 的"起点已在碰撞中"退回。
- [x] 把路点里隐含的约束改写成规划约束（清单里的 K 类）：
  - 手里的东西不能甩：关节一次最多变 1.2 rad、慢速、平滑 → 速度上限 / 平滑约束；
  - 手里的东西不能倾斜 → 姿态约束；
  - IK 分支要连续（pour、handover）→ IK 种子。

**完成标准：** 所有空中运动都带着手里的物体规划；`pick_lift` 不再因为起点碰撞而退回直线。

**实施记录（2026-11-01，分支 `remove-handcoded-motion`）：**

- **入口收敛。** `rig.py` 的三个手臂入口（`move_to`、`joint_path`、`move_left_to`）共用 `_motion_path`：不查碰撞（或没有 world）就走 `straight()`；查碰撞就在 `_planning` 里 `plan()`，规划结果再做第二次查询（见下）；fallback 类的 Allow 规划不出来、或起点已在碰撞中，就走 `straight()` 并记 `clearance_fallback`；其他的抛 `SkillFailure`。
  - `move_to` 的 `plan()`：直线 `cart_path` → `Motion.plan_to`。`plan_to` 先按位姿约束规划（持物保持倾角、否则以直线接近收尾），不行再规划到关节目标 `_goal`：`q_hint` 在实际底盘位姿下沿它的分支重解，不行就用 `q_hint`/当前姿态做种子的全局 IK，最后才用 `q_hint` 本身。原来的 L4（直接插值到 `q_hint`）和 L5（`ik_global` 换分支后插值）都并进这里，而且都是查碰撞、带目标物体豁免的规划。11-01 全量里 `pick_pre_far` 有 188 次约束规划失败后靠 L4 走通，所以关节目标这一档必须保留。
  - L2（0.02 m 步长重算再加密）并进 `Motion.cart_path`，对所有调用方生效。
  - `move_to` 的 `straight()`（`_straight_move`）：不查碰撞的直线；直线没有 IK 时，不查碰撞地关节插值到 IK 解。朝 `q_hint` 摆动超过 1 rad 的关节插值仍然要规划（原来 L4 的规则，防止前臂扫过垃圾桶；没有 `q_hint` 时和原来的 L5 一样不规划）。退路不再把整条链关掉检查重跑。
  - `joint_from_contact` 删掉（11-01 全量里一次都没触发）。
  - `tuck` 改成 `joint_path(rest)`：直线关节插值无碰撞就走，否则 cuRobo 规划，否则返回 False。四种手写前置后撤、单元素候选列表、"夹爪闭着不规划"都删了；唯一可能握着把手时收臂的调用方（`_move_with_retry_impl`）先松手再收。
- **手里的物体进碰撞模型。** `Motion.scope` 在每次查碰撞的入口运动里把手里物体的包围盒球挂到该臂的 held link 上，运动规划完就卸下。`Rig.held_collision` 和 `Motion.sync` 里按开关挂载的逻辑删掉，`_carry_pose`、posture 的包装随之删掉。起点时物体还贴着东西、又没声明离开接触的，照旧这一段不带它，记 `held_collision ... (touching: off)`。`find_park` 等运动入口之外的查询不带手里的物体（放下位姿本来就贴着支撑面）。
- **起点贴着支撑面：和计划的出入。** 11-01 全量的 87 次 `clearance_fallback` 里 87 次都是"starts in collision"（`pick_lift` 34、`edge_lift`/`edge_pull` 各 20、`flat_retreat` 8、`place_retreat_up` 3、`flat_up` 2），撞的全是**手部连杆**（`gripper_link`、腕部相机）压进支撑面（island、desk、tv_stand、dining_table），个别是墙，没有一次是手里的物体。所以只声明 `held_on` 消不掉这些退回。改成新的预设 `LEAVE_CONTACT`（`Allow.from_contact`）：离开接触的这一小段是接触段（C 类），不查碰撞、走直线，不规划；之后的自由空间运动从这一段的终点开始规划，那里已经离开接触，用完整的世界，不需要任何豁免。运动开始时用监视器同一套 `robot_contacts` 看手（手指、夹爪、腕部相机）和手里物体碰着什么，解析成这一段 Allow 的 `touch` / `held_on`，只给监视器判断接触用（记 `leave_contact` 事件）。第一版曾用审计 4.1 的两次查询让规划器从接触状态出发（规划时整台机器人关掉这些碰撞体，事后校验手臂其余部分，不过就走退路），那是放宽问题再拒绝的做法，已删除。用在刚抓起、刚松手和离开接触段的动作上：`pick_lift`、`pick_fail_clear`、`corner_lift`、`edge_lift`、`edge_pull`、`handle_pick_lift`、`cavity_pick_lift`、`place_retreat_*`、`flat_retreat`、`flat_up`、`regrasp_clear`、`release_back`、`left_release_back`、`drop_retreat`、`microwave_release_up`、`{verb}_back`、`close_push_back`、`dip_out`、`stir_out`、`flip_withdraw`。这些动作原来是 `FREE_ELSE_STRAIGHT`，起点无碰撞时会规划；现在一律走直线（几厘米的退出或抬起）。
- **K 类约束。**
  - 持物不甩：入口的时间参数化统一处理。手里有东西（非双手）时 `follow` 一律走 `follow_smooth`（平滑起停），手臂关节速度上限 0.5 rad/s，沿口捏着的容器 0.25 rad/s。各处手传的 `step`、`steps_per_wp`、`smooth` 暂时保留（只会更慢），步骤 3 合并到哪个 skill 就删到哪。
  - 持物不倾斜：位姿约束规划（`tilt_metric`）和关节规划的倾角保持原来就在规划器里；直线关节插值的倾角检查合并成 `kinematics.tips_over`，`planner.joint_reachable` 和入口共用。
  - IK 分支连续：`q_hint` 现在是规划的关节目标和 IK 种子（见上），pour、handover 传的 `q_hint` 都走这条路。skill 里为此拆的半程点和关节变化阈值（`held_vertical_move` 的 1.2 rad 等）属于步骤 3 删除的路点。
- **针对性检查**（用的是两次查询的第一版，改成接触段之后没有重跑；种子 10，`sticky/gt`，`benchmark/runs/step1_targeted_1101/`，对照 11-01 同一批条目）：成功 4/6（11-01 为 3/6：P06 新成功，T14、P16 两次都失败）；`clearance_fallback` 9 → 2，"starts in collision" 全部消失（P05 5 → 0、T14 3 → 0、P16 1 → 0）。剩下两次是规划器解不出来（`handover_present_across` GRAPH_FAIL、`hover_above` FINETUNE_TRAJOPT_FAIL），归"规划器能力不够"。T14 的失败点从放下后倾斜 30° 变成 `flat_pre` 无路可走：书在夹爪里下垂 65–74°，带进碰撞模型后目标位姿压进书架，原来 L5 不带物体的 IK 能到。手臂跟踪偏差（place 前 `carry_up` 的 `right_arm_joint_5` 差 1.3–1.4 rad）11-01 就有。`benchmark/runs/step1_targeted_1101_mixed/` 是中途改代码前后混跑的一轮，不作数。
- **没动、留到后面的：** `planner._ik_sequence` 的反向链和 `_chain` 的"park 搜索只认直线"。park 搜索里加规划代价太高，而它选出的 `qs` 正是执行时的 `q_hint`，两边已经由"直线，否则规划到 `q_hint`"连起来；手写 park 删掉时（步骤 3）再看。`_left_path`、`follow_both`、`joint_path_via` 属于步骤 5。

### 步骤 2：底盘规划器（已完成）

**目的：** 用整机可行性的底盘规划器替换 `plan_path`，删掉所有底盘盲动。

- [x] (x, y, 朝向) 格点搜索：整机可行性（底盘占地 + 手臂当前姿态 + 手里的物体）按块批量计算，在上面做 A*。不再有终点附近 0.4 m 不检查的放宽（`relax`）。
- [x] 目标可以是一个区域，例如"收起姿态无碰撞的位置"，用来取代 `_clear_for_tuck`。
- [x] 开车时的手臂姿态：下垂姿态（`DRIVE_Q`）只要沿路可行就用；在终点附近什么时候换回收起姿态，由规划器决定，取代 `_hang_while_driving` 的"到了再抬"（顺带解决 `drive_raise_blocked`）。
- [x] navigate 和其他 `drive_base` 调用都走这套整机检查。例外：wipe 和 flip 的底盘推是接触动作，留给步骤 4；边走边放的路径是规划的，但行驶中手臂在动，没有逐点检查。
- [x] 删掉清单里的 B 类（`_back_off`、`navigate_back_from_door`、"退出去再开回"、`_clear_for_tuck` 等）。例外：`clear_microwave_door_sweep` 的写死让路位姿（场景特例，步骤 3）。

**针对性检查：** T03 s11（`juice_bottle`）、P07 s11、P12 s11。

**完成标准：** B 类清零；全量回归的倒退都能归类。

#### 实施记录（2026-11-02，`ea47359`、`348d5c8`）

**规划器**（`zeno_skills/base_planner.py`）

- **状态：** (x, y, 朝向) 格点，xy 每格 5 cm，朝向每档 15°（24 档），格点原点在机器人当前位置。另加一维"手臂姿态"：调用方给一条姿态链，例如空手开车是"当前 → 收起 → 下垂 → 收起"，相邻相同的合并。每个姿态带一个开车代价权重（伸着手臂开车 2.0、收起 1.5、下垂 1.0），所以规划器尽早切到下垂、尽量晚抬回。
- **格子可行**，两条都要满足：
  1. 底盘占地不碰标注盒子、地上的散落物体和门这类活动部件，留 3 cm 余量（`WorldModel.footprints_clear`，和 `find_park` 选停车点同一个判据）。
  2. 该姿态下的两只手臂、躯干、头和手里的物体，不碰场景的真实碰撞体（`Motion.base_depths`）。每个姿态先算一次相对底盘的碰撞球：连杆的球来自 cuRobo 机器人模型；手里的物体用包围盒球，挂在 TCP 上。再把这组球按候选的 (x, y, 朝向) 旋转平移过去，查最大穿透深度。要求为 0，链上第一个姿态允许不超过起点本来的深度。
- **块：** 可行性按块懒惰计算，一块是 8×8 个 xy 格子（0.4 m × 0.4 m）× 24 个朝向 = 1536 个位姿，对应一个姿态。A* 第一次问到某块里的状态，就把整块一次交给 GPU 算完并缓存。缓存分三类，各有自己的块：每个姿态一份；每次姿态切换一份（每个位姿查 6 个插值姿态）；占地一份（和姿态无关）。日志里的 `poses_checked` 是算过的块数 × 1536。
- **姿态切换：** 只能在格子上原地切，条件是两个姿态之间等分的 6 个插值姿态在这里全部无碰撞。在哪里切由搜索决定，执行时就是这段检查过的直线插值（`Rig.swing`）。
- **起点：** 机器人已经站在那里。起点格子不受占地约束，第一个姿态允许"不比起点陷得更深"。
- **终点：** 先检查精确终点在到达姿态下可行（手臂、手里物体和占地），不行直接失败。到达条件是：到了终点格子，或到了离它一格、一个朝向以内、能直线开到精确终点的格子（`Lattice.reaches`，见下面全量回归里的吸附问题）。规划结果的最后一段就是这段检查过的直线。
- **没有目标时**（`goal=None`）：搜索最近的、能完成最后一次姿态切换的位姿。收臂恢复和躯干动作前的挪位用它，代替 `_clear_for_tuck` 和后撤。
- **搜索：** A*。邻居是 8 方向平移、左右转一档、切到下一个姿态。代价是距离 × 姿态权重，转向每弧度 1 m，每次切换 0.3 m。启发是底盘内切圆（半径 0.26 m）在标注盒子上的 2D 测地距离：静态盒子的栅格按场景缓存，门和地上物体每次补算。圆到不了终点的格子直接剪掉，起点到不了就立即失败。启发乘 2.5，不重开已关闭节点，扩展上限 20 万。
- **结果：** 按姿态切成开车段，中间插姿态切换。每段做捷径平滑（中间按格点检查），首尾补上精确的起点和终点。

**底盘为什么用标注盒子、不用真实碰撞体：** 房子的房间外壳碰撞网格在门洞底部有约 0.3 m 高的伪影，有的门洞按真实网格算不到 0.4 m 宽。仿真里底盘的碰撞体本来就是关掉的，以前机器人一直是"穿"过这些地方的。手臂和手里的物体才会真的碰倒东西，所以只有它们用真实碰撞体。

**接入点**

| 方式 | 用在哪里 |
|---|---|
| 完整规划（`relocate`，`navigate` 是它的一种用法） | `navigate` 及其全部调用方（停车点、`navigate_place`、`approach`、探索、双手抓取、`steady_park`）；"退出去、摆好手臂、再开回来"的编排改成带到达姿态的规划：餐桌抬碗、冰箱层板预整形、双手抓取降躯干伸双臂、微波炉取物的安全姿态、`cavity_return_safe`、微波炉重测后的停车点微调；收臂和躯干动作挪位（`goal=None`） |
| 固定路径整机检查（`straight_base_move`），不通就失败，不重新采样 | 原地转身（`face`、`base rotate`、探索转 180°）、平移（`base translate`、`sidestep`）、后退（`retreat`、`BackOffWithLoadPolicy`，第 8 节问题 3：保留为任务级原语） |
| 规划器给路径、调用方自己开（`plan_drive`） | 双手搬运（双臂固定，全程检查过）、边走边伸手 / 放置（行驶中手臂在动，没有逐点检查） |
| 目标位姿筛选 | `find_park`：候选停车点按行驶姿态做整机检查（一次批量），"能不能开到"用新规划器（按下垂姿态）；`standoff_poses`：按到达姿态整机筛 |

`navigate` 本身：空手先用手臂规划器原地收臂，收不了就把"收起"放进姿态链交给规划器；空手时双臂下垂开车，到终点前由规划器决定在哪里抬回；拿着东西时先 `_carry_pose`，手臂保持搬运姿态、开得慢一些。

**删掉的：** `_back_off`、`_clear_for_tuck`、`_load_near_furniture`、`navigate_back_from_door`、`tuck_after_back_off`、`margin in (0.15, 0.10, 0.06)`、`_hang_while_driving`、`stow_load` 的倒车、posture 里的两次后撤、微波炉的直线开进 / 倒车 / 底盘微调。`plan_path` 只在没有 cuRobo 时（单元测试）还用。

**没动的：** wipe 和 flip 的底盘推（接触动作，步骤 4）；`clear_microwave_door_sweep` 开到写死位姿给门让路（场景特例，步骤 3）；`NavigateToPlacePolicy` 的候选列表（F 类，步骤 3）。

**针对性检查**

- 计划指定的三个：T03 s11 开车途中不再碰倒物体，成功；P12 s11 成功；P07 s11 在中间版本失败过一次（`LeftArmFoldPolicy` 不查碰撞的左臂插值碰倒杯子，步骤 5），最终复查成功。
- 最终复查 16 个 episode：上面三个，加上走过被替换编排的 T07 microwave_works、P13、T19 bin_on_bookcase、P17、P08、P22，以及覆盖探索、转身、侧移、递交的 P01–P04、P06、T12 ×2、T13 dishes_on_tv_stand。结果：成功 13/16（11-01 同一批 8/16），新成功 5 个，没有新失败；失败的 P17、P03、P04 在 11-01 也是同样原因失败。结果在 `benchmark/runs/step2_targeted_c/`；`step2_targeted`、`_b`、`step2_probe*` 是中途版本。
- 底盘规划单次 1–20 s（扩展几十到几千个状态），一个 episode 合计几十秒。

**第一次全量回归**（`ea47359`，`benchmark/runs/v3_sticky_gt_1102_2seeds/`，逐个对比在 `COMPARE.md`）

| | 11-01（`a0a9574`） | 11-02（`ea47359`） |
|---|---|---|
| 成功 | 108/170 | 117/170（新成功 31，新失败 22） |
| `fallbacks` | 87 | 5 |
| `contacts`（unexpected） | 982 | 1040 |
| `disturbed` | 没有这个指标 | 175，其中 26 次记在 `drive_base` 上 |

22 个新失败的归类：

| 类别 | episode | 原因 | 处理 |
|---|---|---|---|
| 代码写错 | T01 overhang_ready ×2、T01 table_set ×2、T13 no_cup_spoon_boxed_in ×2、P15 s11、T05 pen_available s11（8 个） | 吸附问题：终点格子是离停车点最近的格点（最多差 2.5 cm、7.5°）。`find_park` 的停车点贴着家具、几乎零余量，吸附后的格点已经碰了，终点格子永远到不了，搜索把能到的状态全部展开后撞上上限。两个种子成对出现，T01 两个种子检查的位姿数都是 491520 | `348d5c8` 修复：一格、一个朝向以内、能直线开到精确终点的格点就算到达。4 个 episode 重跑全部成功，46 次底盘规划全部找到（`benchmark/runs/step2_fix_goal/`） |
| 模型更严格 | P19 ×2、T09 lid_on s10（抓锅盖），大概率还有 P05 flip ×2 | `find_park` 按到达姿态检查左臂收起姿态，它的手指伸出底盘、碰到岛台，近处的停车点被拒；停得远了，伸手被岛台挡住 | 步骤 5（`LEFT_ARM_FOLD` 和左臂运动） |
| 选点差异 | T08 sponge_on_tv_stand、far_sponge_tv、island_cluttered s10 | `navigate_place` 的站位按整机筛，站到了岛台另一侧；wipe 只在机器人附近 ±0.4 m 选擦拭带，那一侧有东西 | 步骤 3（wipe 选带依赖站位是 F 类问题） |
| 未细查 | T13 no_cup ×2、no_cup_bowl_on_cabinet ×2、T14 shelf_taken s11、T02 far_crowded s11 | 失败在 pick / place 环节（"not held"、目标不可达），推测是停车点或站位变化引起 | 下一次全量后再看 |

**开车时的扰动：** 26 次记在 `drive_base` 上，其中有真碰倒的（果汁瓶倾斜 50°、擀面杖 92°）。原因：规划不留余量；格点之间只按 5 cm / 15° 检查；执行时手臂有跟踪误差。贴着东西开过去就会刮到轻的物体。修法是给手臂和手里物体的碰撞球加安全余量，还没做（见第 2 节）。

### 步骤 3：手臂按 skill 合并

**目的：** 每个 skill 把空中的中间点合并成"从当前姿态规划到下一个中继位姿"，删掉清单里的 W 类（避障路点）和 F 类（skill 自己写的退路和重试）。每合并一个 skill 提交一次。

顺序按经过次数：`_carry_pose` → place 那条链 → drop → pick 的抬起和退出 → open / close 之后的后撤 → `held_vertical_move` → 其他。

shake、wave、倾倒、搅拌画圈这类路点本身就是任务动作（T 类），保留，只加检查。

**完成标准：** 这个 skill 里的 W、F 类条目清零，删掉的路点没有以任何形式（fallback 分支、备选列表、条件开关）留在代码里；它的运动只剩"规划到下一个中继位姿"和接触段。

### 步骤 4：接触动作

**目的：** 原阶段 3。接触段（清单里的 C 类）改用 `Allow` 预设，`LEGACY` 清零。

- [ ] ~~实现两次查询的语义（审计 4.1）~~：步骤 1 试过、已删除（放宽问题再拒绝）。接触段是任务规定方向的直线，不规划，接触只由监视器按 `Allow` 记录；自由空间段从无碰撞的点开始规划。规划用第二种设置，再用第一种逐段校验。
- [ ] 按预设迁移：

| 预设 | 动作 |
|---|---|
| `grasp` | `pick_grasp_fix`、`edge_pre`、`edge_grasp`、`corner_pre`、`corner_grasp*`、`steady_grasp`、flip / upright 的抓握段 |
| `handle` | `close_push_contact` |
| `press` | 按钮的 align / press / retract（含微波炉）、`knock_*`、`touch_*` |
| `sweep` | push / pull / center / separate / sweep 的 down、slide、up；`wipe_press`、`wipe_lift`；`stir_dip`、`stir_circle`；`flat_push*` |
| `set_down` | `place_insert`、`place_lower`、`flat_lower`、`flat_release_down`、`microwave_insert`、`upright_lower` |

- [ ] 清单第 5 节的补充：`button_align` 其实是空中段，改成中继位姿 + 规划；被拆成两段的接近（`corner_pre`、`edge_pre`、`upright_top_in`）合成一段；门和推门逐段切换 `coll_kw` 的写法换成 `handle` 预设。
- [ ] 预设不够用就加预设，不要退回 `unchecked`。

**完成标准：** `LEGACY` = 0；监视器记到的接触都在 `allow` 范围内。

### 步骤 5：左臂和清理

**目的：** 原阶段 5 加审计 4.4。

- [ ] `LeftArmFoldPolicy` 和所有左臂运动走同一套规划，不再直接插值。
- [ ] `follow` / `left_follow` 只接受检查过的路径（`Checked` 包装）。
- [ ] 删掉：`coll_kw` 的 `ignore_fingers`、"另一只手的手指一律不查"、`other_touching` 的永久排除、`world.active`、`world.left_active`、`WorldModel.temp_obstacles`。需要两只手都碰物体时（handover）在 `allow` 里显式声明。
- [ ] `kin.set_base`、`kin.lo` / `kin.hi` 的临时改写，换成 `rig.clear` 的上下文管理器（`at_base(...)`、`pinned_torso()`）。

**针对性检查：** P06、P07、handover 相关任务。

**完成标准：** `tools/audit_collision.py` 里 `coll_kw` 直接写入和原始 `follow` 调用为 0；清单全部清零。

## 5. 不做的事

- 不加手写的中间点、底盘挪动或"原地转 / 退出来再进"这类备选路径（原阶段 4 第一版就是因此被删掉的）。
- 不把旧路点、旧底盘动作留作 fallback。删就是删，退路只有入口里那一条直线（原则 2）。
- 不为了消除规划随机性单独花工夫。
- 不在一个提交里跨步骤改动。

## 6. 还没定的问题

| 问题 | 什么时候定 |
|---|---|
| `COLLISION_CLEANUP.md` 第 8 节的五个归类问题 | 开始对应步骤前 |
| `Allow` 的五个预设是否覆盖所有 skill | 步骤 4 迁移时 |
| 底盘规划器的格点分辨率和整机检查的批量规模（时间开销） | 步骤 2 |
| 下垂开车姿态在终点附近换回收起姿态的时机，是作为规划目标区域还是作为一段单独的手臂规划 | 步骤 2 |
