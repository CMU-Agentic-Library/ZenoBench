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
| 已提交 `ef01cb1` | 原阶段 0、1：`clearance.py`（`Allow`、`FREE`、`unchecked`、`LEGACY`）、`rig.clear` 技能作用域（修掉 `coll_kw` 泄漏）、`unexpected_contact` 监视器、`tools/audit_collision.py`、防退化测试 | 审计 7.1、7.2 |
| 已提交 `a0a9574` | 原阶段 2：第 1 类空中运动 63 处改成 `FREE_ELSE_STRAIGHT`；`LEGACY` 111 → 48 | 审计 7.3 |
| **未提交** | 收起姿态修复：`kin.rest` 恢复肘外姿态，下垂姿态 `DRIVE_Q` 只在 navigate 开车时用（`_hang_while_driving`） | 审计 7.5 |
| **未提交** | 监视器把手里的物体算进机器人（`held:<物体>`），并记录被推动、碰倒的物体（`disturbed_object`） | 审计 7.6 |
| 步骤 1（分支 `remove-handcoded-motion`） | 入口收敛、手里的物体进碰撞模型、`LEAVE_CONTACT`（接触段直线）、持物限速平滑 | 第 4 节步骤 1 实施记录 |
| 已删除 | 原阶段 4 第一版：`Motion.sweep` / `Rig.drive_clear`、navigate 的手写备选路径、按方向挑选的 `_back_off` | 审计 8.4 |

两项未提交的改动单元测试已过，直接提交，不单独做一轮验证；效果随第一次全量回归一起看。

**已知还没解决的问题：**

| 问题 | 例子 | 归到哪一步 |
|---|---|---|
| 同样输入，cuRobo 规划结果会分叉 | P07 s10 连跑两次，一次成功一次 "no IK for shake" | 不单独处理，见第 3 节 |
| 开到终点附近时手臂和底盘不检查（`plan_path` 的 `relax`） | T03 s11 垂着的手臂碰倒 `juice_bottle` | 步骤 2 |
| 到 park 后抬不回收起姿态 | 收起姿态修复冒烟测试里 5 次 `drive_raise_blocked` | 步骤 2 |
| ~~刚夹住时起点就在碰撞中，只能退回直线~~ | 步骤 1 改成接触段 `LEAVE_CONTACT`，不再从接触状态规划 | 步骤 1 |
| `ignore_fingers` 让带检查的动作不查手指 | `pick_grasp`、`pick_pre_far`、`tuck` 的手指压进台面 | 步骤 4、5 |
| 左臂收臂直接插值，不经过任何检查 | `LeftArmFoldPolicy` 的 `link_7` 压进岛台 46 mm | 步骤 5 |

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

### 步骤 2：底盘规划器

**目的：** 用整机可行性的底盘规划器替换 `plan_path`，删掉所有底盘盲动。

- [x] (x, y, 朝向) 格点搜索：一次批量算出起点到终点附近所有格子的整机可行性（底盘占地 + 手臂当前姿态 + 手里的物体），在上面做 A*。不再有终点附近 0.4 m 不检查的放宽（`relax`）。
- [x] 目标可以是一个区域，例如"收起姿态无碰撞的位置"，用来取代 `_clear_for_tuck`。
- [x] 开车时的手臂姿态：下垂姿态（`DRIVE_Q`）只要沿路可行就用；在终点附近什么时候换回收起姿态，由规划器决定，取代 `_hang_while_driving` 的"到了再抬"（顺带解决 `drive_raise_blocked`）。
- [x] navigate 和其他 `drive_base` 调用（边走边放、wipe 和 flip 的底盘推、handover 时开车、perceive 时转身）都走这套整机检查。
- [x] 删掉清单里的 B 类（`_back_off`、`navigate_back_from_door`、"退出去再开回"、`_clear_for_tuck` 等）。

**针对性检查：** T03 s11（`juice_bottle`）、P07 s11、P12 s11。

**完成标准：** B 类清零；全量回归的倒退都能归类。

**实施记录（2026-11-02，分支 `remove-handcoded-motion`）：**

- **规划器**（`zeno_skills/base_planner.py`）：(x, y, 朝向) 格点，5 cm × 15°，状态里再加一维手臂姿态模式。模式是一条链，例如空手开车是"当前 → 收起 → 下垂 → 收起"。一个格子在某模式下可行，要同时满足两条：
  - 底盘占地不碰标注盒子（`WorldModel.footprints_clear`，和 `find_park` 选停车点同一个判据）；
  - 两只手臂在该姿态下、以及手里的物体，不碰场景的真实碰撞体（`Motion.base_depths`：碰撞球按底盘位姿批量平移旋转，一次查一块 8×8 格 × 24 个朝向）。
  
  模式切换 m → m+1 只允许在"两个姿态之间直线关节插值全程无碰撞"的格子上做。在哪里切由搜索决定，执行时就是这段检查过的直线插值（`Rig.swing`）。A* 用加权启发（×2.5，不重开已关闭节点）。启发是标注盒子上底盘内切圆的 2D 测地距离（静态部分按场景缓存，门和地上物体每次补算），松弛到不了的格子直接剪掉。终点附近不再有任何放宽。起点允许"不比现在陷得更深"（机器人已经站在那里），起点格子不受占地检查约束。没有目标时（`goal=None`），搜索最近的、能完成最后一次切换的位姿，用来代替 `_clear_for_tuck` 和躯干动作前的后撤。
- **底盘为什么用标注盒子、不用真实碰撞体：** 房子的房间外壳碰撞网格在门洞底部有约 0.3 m 高的伪影，有的门洞按真实网格算不到 0.4 m 宽。仿真里底盘的碰撞体本来就是关掉的，以前机器人一直是"穿"过这些地方的。手臂和手里的物体才会真的碰倒东西，所以只有它们用真实碰撞体。
- **接入点：**
  - `navigate`：先用手臂规划器就地收臂。收不了时把"收起"放进模式链，由规划器找能收的位置。空手时双臂下垂开车，到终点前由规划器决定在哪里抬回；拿着东西时手臂保持搬运姿态。`relocate(goal, postures)` 是通用形式，`drive_to` 和 `plan_drive` 是它的特例。
  - "退出去、摆好手臂、再开回来"类的编排改成带到达姿态的规划：餐桌抬碗、冰箱层板预整形、双手抓取降躯干伸双臂、微波炉取物的安全姿态、`cavity_return_safe`。微波炉放入的"后退 45 cm 再直线开进"和放入后的倒车删掉，由整机规划绕开开着的门。
  - 原地转身、侧移、平移、后退、`BackOffWithLoadPolicy`（第 8 节问题 3：保留为任务级原语）这些固定路径的动作，改成 `straight_base_move`：沿路整机检查，不通就失败，不重新采样。
  - `find_park`：候选停车点用整机检查（行驶姿态 + 手里的物体 + 占地）一次批量筛；"能不能开到"用新规划器。`standoff_poses`（`navigate_place`、探索视点）同样批量筛。
- **删掉的：** `_back_off`、`_clear_for_tuck`、`_load_near_furniture`、`navigate_back_from_door`、`tuck_after_back_off`、`margin in (0.15, 0.10, 0.06)`、`_hang_while_driving`、`stow_load` 的倒车、posture 里的两次后撤、微波炉的直线开进 / 倒车 / 底盘微调。`plan_path` 只在没有 cuRobo 时（单元测试）还用。
- **没动的：** wipe 和 flip 的底盘推（接触动作，步骤 4）；边走边放（`mobile.py`）的路径已经是整机规划的，但行驶中手臂在动，没有逐点检查；`clear_microwave_door_sweep` 开到写死位姿给门让路（场景特例，步骤 3）；`NavigateToPlacePolicy` 的候选列表（F 类，步骤 3）。
- **针对性检查：**
  - 计划指定的三个：T03 s11 开车途中不再碰倒物体，成功；P12 s11 成功；P07 s11 失败。P07 的杯子是 `LeftArmFoldPolicy` 不查碰撞的左臂插值碰倒的（步骤 5），这次停车位置和 11-01 不同。
  - 用最终代码复查 16 个 episode（上面三个，加上走过被替换编排的 T07 microwave_works、P13、T19 bin_on_bookcase、P17、P08、P22，以及覆盖探索、转身、侧移、递交的 P01–P04、P06、T12 ×2、T13 dishes_on_tv_stand）：成功 13/16，11-01 同一批为 8/16。新成功 5 个，没有新失败；失败的 P17、P03、P04 在 11-01 也是同样原因失败。结果在 `benchmark/runs/step2_targeted_c/`，前几轮（`step2_targeted`、`_b`、`step2_probe*`）是中途版本。
  - 底盘规划单次 1–12 s（扩展几十到几千个状态），一个 episode 加起来几十秒。
- **第一次全量回归**（`ea47359`，`benchmark/runs/v3_sticky_gt_1102_2seeds/`，`COMPARE.md`）：

  | | 11-01（`a0a9574`） | 11-02（`ea47359`） |
  |---|---|---|
  | 成功 | 108/170 | 117/170（新成功 31，新失败 22） |
  | `fallbacks` | 87 | 5 |
  | `contacts`（unexpected） | 982 | 1040 |
  | `disturbed` | 没有这个指标 | 175，其中 26 次记在 `drive_base` 上 |

  22 个新失败的归类：

  | 类别 | episode | 原因 | 处理 |
  |---|---|---|---|
  | 代码写错 | T01 overhang_ready ×2、T01 table_set ×2、T13 no_cup_spoon_boxed_in ×2、P15 s11、T05 pen_available s11（8 个） | 底盘搜索达到上限。终点格子是离精确终点最近的格点，`find_park` 选的停车点贴着家具，吸附后的格点已经碰了，终点格子永远到不了 | 已修：一格、一个朝向以内、直线到精确终点可行的格点就算到达（`Lattice.reaches`）。这 4 个 episode 重跑全部成功，46 次底盘规划全部找到（`benchmark/runs/step2_fix_goal/`） |
  | 模型更严格 | P19 ×2、T09 lid_on s10（抓锅盖），大概率还有 P05 flip ×2 | `find_park` 的整机检查按到达姿态算左臂收起姿态，它的手指伸出底盘、碰到岛台，近处的停车点被拒。停得远了，伸手被岛台挡住 | 归步骤 5（`LEFT_ARM_FOLD` 和左臂运动） |
  | 选点差异 | T08 sponge_on_tv_stand、far_sponge_tv、island_cluttered s10 | `navigate_place` 的站位现在按整机筛，站到了岛台另一侧；wipe 只在机器人附近 ±0.4 m 选擦拭带，那一侧有东西 | wipe 选带依赖站位是 F 类问题，归步骤 3 |
  | 未细查 | T13 no_cup ×2、no_cup_bowl_on_cabinet ×2、T14 shelf_taken s11、T02 far_crowded s11 | 失败在 pick / place 环节（"not held"、目标不可达），推测是停车点或站位变化引起 | 下一次全量后再看 |

  **开车时的扰动：** 26 次记在 `drive_base` 上，有真碰倒的（果汁瓶倾斜 50°、擀面杖 92°）。规划用零余量，格点之间只按 5 cm / 15° 吸附检查，执行时手臂还有跟踪误差，贴着东西开过去会刮到轻的物体。应该给手臂和手里物体的碰撞球加安全余量，还没做。

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
