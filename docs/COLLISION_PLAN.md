# 碰撞与运动规划：执行计划（2026-11-01）

本文是 `COLLISION_AUDIT.md` 的执行版：只写要做什么、按什么顺序、做到什么算完。现状盘点、问题来源和历史记录仍以 `COLLISION_AUDIT.md` 为准，文中的"审计 x.y"指那份文档的章节。

代码基线：分支 `remove-handcoded-motion`，`a323805`（步骤 1、2 和步骤 2 补丁都在上面，main 的底盘关节和单相机录像已合并进来）。

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

| 提交 | 内容 | 位置 |
|---|---|---|
| `ef01cb1` | `clearance.py`（`Allow`、`FREE`、`unchecked`、`LEGACY`）、`rig.clear` 技能作用域、`unexpected_contact` 监视器、`tools/audit_collision.py`、防退化测试 | 审计 7.1、7.2 |
| `a0a9574` | 第 1 类空中运动 63 处改成 `FREE_ELSE_STRAIGHT`；`LEGACY` 111 → 48 | 审计 7.3 |
| `ca5a550` | 收起姿态恢复肘外姿态；监视器把手里的物体算进机器人，记录被推动、碰倒的物体（`disturbed_object`） | 审计 7.5、7.6 |
| `83d097b`、`d8cfef8` | 步骤 1 | 第 4 节步骤 1 |
| `ea47359`、`348d5c8` | 步骤 2 | 第 4 节步骤 2 |
| main `91276e7`、`8cdd32d`、`b850b79`；`f15cb3d`、`e495350` | 步骤 2 补丁：底盘关节、yaw 目标范围、惰性边检查、下垂姿态按需绕行 | 第 4 节步骤 2 |
| main `c583120` | 录像只留跟随相机、15 fps（`Rig.step` 每帧 7.4 → 3.9 ms） | 第 3 节 |
| 步骤 1 补丁 `9af5c0c` | 离开接触段按碰撞模型定长、抓起时被抓物体跟手（`lifting`）；边走边伸手 / 抓 / 放停用 | 第 4 节步骤 1 |

**已知还没解决的问题：**

| 问题 | 例子 | 归到哪一步 |
|---|---|---|
| 同样输入，cuRobo 规划结果会分叉 | P07 s10 连跑两次，一次成功一次 "no IK for shake" | 不单独处理，见第 3 节 |
| 离开接触的段（`LEAVE_CONTACT`）的目标位姿仍是手写的：`pick_lift` 抬 7 cm、`pick_fail_clear` 8 cm、`{verb}_back` 最长 14 cm、`close_push_back` 12 cm、`flat_up` 横 12 cm 加高 6 cm、冰箱层板的 `place_retreat_out` 水平 22 cm。入口已经只把离开接触的那一小段走成直线，其余规划（步骤 1 补丁），但规划的终点还是这些手写位姿 | — | 步骤 3（离开接触后直接规划到下一个中继位姿） |
| 底盘规划慢：惰性边检查每轮都从头重搜，窄处绕开被禁的边要好几轮 | T13 s10 规划合计 129 s，拿着东西开车单次最长 52 s | 待定：重搜时复用上一轮的搜索树；捷径分批检查 |
| 底盘规划无路可走时，要把能到的区域搜完才报错（几十秒） | 极紧的停车点 | 待定：搜索前先查终点附近能否接上 |
| 边走边伸手 / 抓 / 放（`mobile.py`）：底盘路径按出发时的手臂姿态规划，行驶中手臂在动，只逐步查手臂（抓、放不查手指），没有整机检查。**已停用**（2026-11-02）：三个 policy 一调用就报 `SkillFailure`；没有 benchmark 任务用到（`pick` / `place` 的 `pass_by`） | — | 待定：整机规划之前不恢复 |
| 左臂收起姿态的手指伸出底盘，靠近台面的停车点被整机检查拒掉 | 11-02 全量里 P19 ×2、T09 lid_on 抓锅盖停得太远 | 步骤 5 |
| 左臂收臂直接插值，不经过任何检查 | `LeftArmFoldPolicy` 的 `link_7` 压进岛台 46 mm；P07 s11 碰倒杯子 | 步骤 5 |
| `ignore_fingers` 让带检查的动作不查手指 | `pick_grasp`、`pick_pre_far`、`tuck` 的手指压进台面 | 步骤 4、5 |
| 搬运姿态仍是手写路点（`_carry_pose`） | 5 个搬运姿态变体、`carry_in_via` | 3a |
| wipe 只在机器人附近选擦拭带，依赖到达时站在哪一侧 | 11-02 全量里 T08 ×3 | 3a |
| 书在夹爪里下垂 65–74°，带进碰撞模型后 `flat_pre` 压进书架 | T14 | 3c（`place_flat` / 书架） |
| 11-02（`ea47359`）之后新出的两个确定性失败，`a323805` 上就有：P06 s10 `handover_present_across` 规划成功、左手却没有 IK（11-02 是规划失败退直线、碰巧接住）；T07 microwave_works s10 `microwave_button_pre` 换了 IK 分支，按键直线没有 IK（11-02 按键就差 2.4 cm） | 连跑 3 次结果相同，不是随机性 | 下一次全量时看是哪一个提交引入的（步骤 2 补丁或合并进来的 main） |
| 11-02 全量的 6 个新失败没细查 | T13 no_cup ×2、no_cup_bowl_on_cabinet ×2、T14 shelf_taken s11、T02 far_crowded s11 | 下一次全量后归类 |

## 3. 回归方法

**每一步：** 单元测试、`build_skill_library --check`，加上这一步动到的 skill 对应的几个 episode。

**全量（T、P 全部任务的所有 variation，种子 10、11，共 170 个 episode）：** 批次 `benchmark/batches/v3_sticky_gt_2seeds_video.json`（`sticky/gt`，录像）。只在这几个节点跑：步骤 2 完成后（已跑）、3a 完成后、3c 完成后（即步骤 3 完成）、步骤 5 完成后。和上一次全量比四个数：成功数、`contacts`、`disturbed`、`fallbacks`。

**下一次全量的对照**是 11-02 那一轮（`benchmark/runs/v3_sticky_gt_1102_2seeds/`，`ea47359`，117/170）。注意三点：

- 中间隔着步骤 2 补丁（底盘关节、惰性边检查、下垂按需绕行）。11-02 那一轮开车时的扰动大部分来自腰被拖弯，`disturbed`、`contacts` 以下一次为新基线。
- 录像已改成单相机、15 fps，耗时不能直接和 11-02 比（单 episode 估计快 20–25%）。
- `fallbacks` 的口径变过两次，和 11-02 都不能直接比：步骤 1 起 `LEAVE_CONTACT` 段整段不查、不计数（11-02 的 5 次是这个口径）；步骤 1 补丁起只有离开接触那一小段不计，其余是规划的，规划失败或到 `LEAVE_MAX` 还没离开接触都计 fallback。

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

要删的东西逐条列在 `COLLISION_CLEANUP.md`，每条标了归哪一步。下面每一步的"删掉"只写大类，具体以那份清单为准。

### 步骤 1：手臂规划的前提（已完成）

**目的：** 让 cuRobo 掌握它规划所需的全部信息，后面才能放心删路点。

**完成标准：** 所有空中运动都带着手里的物体规划；`pick_lift` 不再因为起点碰撞而退回直线。达到了，但 `pick_lift` 是靠改成接触段（不查碰撞的直线）达到的，见下面"离开接触"。

**现在的入口**（`rig.py`：`move_to`、`joint_path`、`move_left_to` 共用 `_motion_path`）：

- 不查碰撞（或没有 world）就走 `straight()`；查碰撞就在 `_planning` 里 `plan()`；fallback 类的 Allow 规划不出来、或起点已在碰撞中，就走 `straight()` 并记 `clearance_fallback`；其他的抛 `SkillFailure`。
- `move_to` 的 `plan()`：直线 `cart_path`（0.02 m 步长重算再加密已并进 `cart_path`）→ `Motion.plan_to`。`plan_to` 先按位姿约束规划（持物保持倾角、否则以直线接近收尾），不行再规划到关节目标 `_goal`：`q_hint` 在实际底盘位姿下沿它的分支重解，不行就用 `q_hint`/当前姿态做种子的全局 IK，最后才用 `q_hint` 本身。关节目标这一档必须保留：11-01 全量里 `pick_pre_far` 有 188 次约束规划失败后靠它走通。
- `move_to` 的 `straight()`（`_straight_move`）：不查碰撞的直线；直线没有 IK 时，不查碰撞地关节插值到 IK 解。朝 `q_hint` 摆动超过 1 rad 的关节插值仍然要规划（防止前臂扫过垃圾桶）。
- `tuck` 是 `joint_path(rest)`：直线关节插值无碰撞就走，否则 cuRobo 规划，否则返回 False。握着把手时收臂的调用方（`_move_with_retry_impl`）先松手再收。

**手里的物体进碰撞模型。** `Motion.scope` 在每次查碰撞的入口运动里把手里物体的包围盒球挂到该臂的 held link 上，运动规划完就卸下。两个例外：起点时物体还贴着东西、又没声明离开接触的，这一段不带它（记 `held_collision ... (touching: off)`）；`find_park` 等运动入口之外的查询不带（放下位姿本来就贴着支撑面）。

**离开接触（`LEAVE_CONTACT`，`Allow.from_contact`）。** 11-01 全量的 87 次"starts in collision"撞的全是手部连杆（`gripper_link`、腕部相机）压进支撑面，没有一次是手里的物体，所以只声明 `held_on` 消不掉。现在的做法：

- 离开接触的这一小段是接触段（C 类），不查碰撞、走直线、不规划，也不记 `clearance_fallback`。
- **这一段有多长由入口按碰撞模型决定**（步骤 1 补丁，`Rig._leave_contact`）：沿原来那条直线逐点用 `kin.near` 检查（带着手里的物体，即使它起点还贴着支撑面，`Motion.scope(keep_held=True)`），走到第一个离世界超过 `LEAVE_GAP`（5 mm）的点再多走 `LEAVE_MARGIN`（1 cm，这 1 cm 全程超过 5 mm），最多 `LEAVE_MAX`（6 cm）的 TCP 行程。判据是间隙而不是穿透：手里物体的碰撞球内切在包围盒里，物体平放在支撑面上时穿透深度正好是 0，按 `kin.free` 判永远"已经离开"（`Motion.near` 用 cuRobo 的激活距离把球放大 5 mm）。起点本来就不碰时没有这一段。日志记 `leave_contact_exit`（`exit_m`、`clear`）。
- **抓起时被抓的物体跟着手走**（`clearance.lifting(name)`，`Allow.lifts`）：`pick_lift`、`corner_lift`、`edge_lift`、`edge_pull`、`handle_pick_lift`、`cavity_pick_lift` 时物体还没登记成 `held`（抬起来验证过才登记），以前它在碰撞模型里是留在原地的障碍物。这几处声明 `lifting(name)`，整个运动（接触段加后面的规划）里它像手里的物体一样挂在手上、不算障碍（`motion.load`），所以接触段在物体底部离开支撑面后才结束。手指的接触在这些动作里看不到（`ignore_fingers`，步骤 4、5），不声明的话起点几乎总是"不碰"，接触段长度为 0。
- 剩下的部分是一次普通的 `FREE_ELSE_STRAIGHT` 运动（同一个 label）：从离开接触的点规划到原来的目标，规划不出来走直线并记 fallback；到 `LEAVE_MAX` 还没离开接触，就从那里走直线并记 "starts in collision"。
- 运动开始时用监视器同一套 `robot_contacts` 看手和手里物体碰着什么，解析成这一段 Allow 的 `touch` / `held_on`，只给监视器判断接触用（记 `leave_contact` 事件）。
- 为什么不整段规划：cuRobo 拒绝从碰撞中的起点规划；关掉起点检查让优化器自己挤出去，方向不受控（可能拖着物体在台面上滑），是放宽再拒绝（第 5 节）。方向是任务决定的（支撑面法向、放入方向的反向），所以接触段走直线。
- 用在：`pick_lift`、`pick_fail_clear`、`corner_lift`、`edge_lift`、`edge_pull`、`handle_pick_lift`、`cavity_pick_lift`、`place_retreat_*`、`flat_retreat`、`flat_up`、`regrasp_clear`、`release_back`、`left_release_back`、`drop_retreat`、`microwave_release_up`、`{verb}_back`、`close_push_back`、`dip_out`、`stir_out`、`flip_withdraw`。
- 还剩的：这些动作的目标位姿（抬 7 cm、退 14 cm 等）仍是手写的，步骤 3 删（见步骤 3 规则）。
- **检查**（单元测试 179 个通过，`build_skill_library --check` 通过；11-02 成功过的 8 个 episode，种子 10，`benchmark/batches/leave_contact_exit.json`）：

  | | 11-02（`ea47359`） | 第一版（按穿透判断，无 `lifting`） | 最终版 |
  |---|---|---|---|
  | 成功 | 8/8 | 6/8 | 6/8 |
  | 意外接触 / 碰动物体 | 48 / 4 | 42 / 3 | 41 / 3 |
  | `fallbacks` / 规划的段 | 1 / 14 | 2 / 38 | 0 / 40 |
  | 合计耗时 | 2506 s | 1389 s | 1409 s |

  - 结果在 `benchmark/runs/leave_contact_exit/`（第一版）、`leave_contact_exit_b/`（最终版）。
  - 最终版 26 次离开接触里 12 次有接触段：`pick_lift` 11 次 1.2–2.9 cm，`edge_lift` 1 次 1.6 cm；其余起点就离世界 5 mm 以上（松手后的退出，手指不查）。没有一次走到 `LEAVE_MAX`。
  - 第一版暴露了两个问题，最终版已修：被抓的物体留在原地（`edge_lift` 判为离开后同步世界、书回到夹爪里，剩下部分 "starts in collision" 退直线）→ `lifting`；按穿透判断时 26 次里 24 次长度为 0 → 按间隙判断（`LEAVE_GAP`）。
  - 失败的 P06、T07 不在离开接触段上，而且在不含这些改动的 `a323805` 上同样失败（`/data/zenobench/leave_contact_exit/control/`），见第 2 节。

**K 类约束。**

- 持物不甩：手里有东西（非双手）时 `follow` 一律走 `follow_smooth`，手臂关节速度上限 0.5 rad/s，沿口捏着的容器 0.25 rad/s。各处手传的 `step`、`steps_per_wp`、`smooth` 还在（只会更慢），3b 删。
- 持物不倾斜：位姿约束规划（`tilt_metric`）和关节规划的倾角保持在规划器里；直线关节插值的倾角检查是 `kinematics.tips_over`，`planner.joint_reachable` 和入口共用。
- IK 分支连续：`q_hint` 是规划的关节目标和 IK 种子，pour、handover 都走这条路。skill 里为此拆的半程点和关节变化阈值（`held_vertical_move` 的 1.2 rad 等）是步骤 3 要删的路点。

**留到后面的：** `planner._ik_sequence` 的反向链和 `_chain` 的"park 搜索只认直线"（park 搜索选出的 `qs` 就是执行时的 `q_hint`，两边已由"直线，否则规划到 `q_hint`"连起来；手写 park 删掉时再看，步骤 3）。`_left_path`、`follow_both`、`joint_path_via` 属于步骤 5。

### 步骤 2：底盘规划器（已完成）

**目的：** 用整机可行性的底盘规划器替换 `plan_path`，删掉所有底盘盲动。

**完成标准：** B 类清零；全量回归的倒退都能归类。B 类除下面"没动的"以外已清零；11-02 全量还有 6 个新失败没归类（第 2 节）。

#### 规划器（`zeno_skills/base_planner.py`）

- **状态：** (x, y, 朝向) 格点，xy 每格 5 cm，朝向每档 15°（24 档），格点原点在机器人当前位置。另加一维"手臂姿态"：调用方给一条姿态链。`navigate` 的链是"收起 → 下垂 → 到达"（`travel_postures`）；拿着东西时"下垂"就是当前的搬运姿态，等于没有绕行。
- **格子可行**，两条都要满足：
  1. 底盘占地不碰标注盒子、地上的散落物体和门这类活动部件，留 3 cm 余量（`WorldModel.footprints_clear`，和 `find_park` 选停车点同一个判据）。
  2. 该姿态下的两只手臂、躯干、头和手里的物体，不碰场景的真实碰撞体（`Motion.base_depths`）。每个姿态先算一次相对底盘的碰撞球（连杆的球来自 cuRobo 机器人模型，手里的物体用包围盒球挂在 TCP 上），再按候选的 (x, y, 朝向) 旋转平移过去查最大穿透深度。要求为 0，链上第一个姿态允许不超过起点本来的深度。
- **底盘为什么用标注盒子、不用真实碰撞体：** 房子的房间外壳碰撞网格在门洞底部有约 0.3 m 高的伪影，有的门洞按真实网格算不到 0.4 m 宽；仿真里底盘的碰撞体本来就是关掉的。手臂和手里的物体才会真的碰倒东西，所以只有它们用真实碰撞体。
- **块：** 可行性按块懒惰计算，一块是 8×8 个 xy 格子（0.4 m × 0.4 m）× 24 个朝向 = 1536 个位姿。A* 第一次问到某块里的状态，就把整块一次交给 GPU 算完并缓存。缓存三类：每个姿态一份；每次姿态切换一份；占地一份（和姿态无关）。两个姿态完全相同时（收起和到达）共用一份格点缓存（`Lattice.canon`）。日志里的 `poses_checked` 是算过的块数 × 1536。
- **姿态切换：** 只能在格子上原地切。格点上抽 `SWITCH_SAMPLES`（6）个插值姿态判断；路径选定后按 `DENSE` 密集校验（`SWITCH_FINE` 抽样后由 `dense_sets` 取）。执行时是这段检查过的直线插值（`Rig.swing`）。两个姿态完全相同时，前一个可以不动手臂直接转到后一个（`Lattice.skip`），所以下垂只在收起姿态过不去的那段才用。
- **代价：** 行驶距离，转向每弧度 1 m，每次切换 0.3 m。没有姿态权重，也没有离障碍的距离代价（剩下的开车接触都有具体原因，没有因为离得太近而刮到的）。
- **起点：** 机器人已经站在那里。起点格子不受占地约束，第一个姿态允许"不比起点陷得更深"。
- **终点：** 先检查精确终点在到达姿态下可行，不行直接失败。到达条件是：到了终点格子，或到了离它一格、一个朝向以内、能直线开到精确终点的格子（`Lattice.reaches`）。只认终点格子不行：`find_park` 的停车点贴着家具、几乎零余量，吸附到最近格点（最多差 2.5 cm、7.5°）后可能已经碰了。
- **没有目标时**（`goal=None`）：搜索最近的、能完成最后一次姿态切换的位姿。收臂恢复和躯干动作前的挪位用它。
- **搜索：** 加权 A*（启发乘 2.5，不重开已关闭节点，扩展上限 20 万）。邻居是 8 方向平移、左右转一档、切到下一个姿态。启发是底盘内切圆（半径 0.26 m）在标注盒子上的 2D 测地距离：静态盒子的栅格按场景缓存，门和地上物体每次补算。圆到不了终点的格子直接剪掉，起点到不了就立即失败。
- **惰性边检查：** 格点之间机器人也在动（转 15° 时伸出 0.7 m 的手扫过 18 cm）。搜索出的路径逐条边、逐次姿态切换按 `DENSE`（2 cm：平移距离加碰撞球最远半径乘转角）密集检查。某条边不通，就把它所在块里所有节点同一个方向的边一次批量查完，再重新搜索（最多 `LAZY_ROUNDS` 轮）。一次查整块所有方向会让规划耗时涨 4 倍，所以只查出过问题的方向。
- **结果：** 按姿态切成开车段，中间插姿态切换。每段做捷径平滑（按 `DENSE` 检查），首尾补上精确的起点和终点。

#### 底盘的执行

- **底盘是关节结构（main `91276e7`）。** `physics.base_joints` 在加载场景时（`make_rig`，`prepare` 之后）把底盘改成固定基座的关节结构：世界 → `base_root_link` → x 平移 → y 平移 → 绕 z 转动 → `base_link`，位置驱动；`base_anchor` 停用，只留作起始位姿的记录。`Rig.base_pose` / `set_base` 读写这三个关节。以前用 `base_anchor` 把浮动基座拖着走，0.35 m/s 前进时腰（`waist_pitch_joint`）被拖到上限前倾 40°、手压到台面上，停车后自己恢复，日志里看不出来（诊断在 `/data/zenobench/drive_diag_1102/`）。不要改回拖动的方式；改底盘控制后要看开车时腰的偏差（现在 ≤ 0.0001 rad）。
- **yaw 目标的范围（main `8cdd32d`、`b850b79`）。** yaw 关节的驱动目标只接受 ±2π，读数会一直累积。目标保持在 (−π, π]，读数超过 π 就把关节位置原地减一圈（姿态不变），目标取读数加减半圈以内。超界时目标被拒收，底盘停在错误的朝向，手臂按规划的位置摆就会扫过家具。

#### 接入点

| 方式 | 用在哪里 |
|---|---|
| 完整规划（`relocate`，`navigate` 是它的一种用法） | `navigate` 及其全部调用方（停车点、`navigate_place`、`approach`、探索、双手抓取、`steady_park`）；带到达姿态的规划：餐桌抬碗、冰箱层板预整形、双手抓取降躯干伸双臂、微波炉取物的安全姿态、`cavity_return_safe`、微波炉重测后的停车点微调；收臂和躯干动作挪位（`goal=None`） |
| 固定路径整机检查（`straight_base_move`），不通就失败，不重新采样 | 原地转身（`face`、`base rotate`、探索转 180°）、平移（`base translate`、`sidestep`）、后退（`retreat`、`BackOffWithLoadPolicy`，任务级原语） |
| 规划器给路径、调用方自己开（`plan_drive`） | 双手搬运（双臂固定，全程检查过）；边走边伸手 / 抓 / 放已停用（第 2 节） |
| 目标位姿筛选 | `find_park`：候选停车点按行驶姿态做整机检查（一次批量），"能不能开到"用同样的姿态链（`travel_postures`、`posture_sets`）；`standoff_poses`：按到达姿态整机筛 |

`navigate`：空手先用手臂规划器原地收臂，收不了就交给底盘规划器（链上第一个姿态是收起）；拿着东西时先 `_carry_pose`，手臂保持搬运姿态、开得慢一些。`plan_path` 只在没有 cuRobo 时（单元测试）还用。

**没动的：** wipe 和 flip 的底盘推（接触动作，步骤 4）；`clear_microwave_door_sweep` 开到写死位姿 `(5.1, 1.6, 150)` 给门让路（场景特例，3c）；`NavigateToPlacePolicy` 的候选列表（F 类，3a）。

#### 检查结果

- **针对性检查用的 episode：** T03 s11（`juice_bottle`）、P07 s11、P12 s11；走过被替换编排的 T07 microwave_works、P13、T19 bin_on_bookcase、P17、P08、P22；覆盖探索、转身、侧移、递交的 P01–P04、P06、T12 ×2、T13 dishes_on_tv_stand。补丁前结果 13/16（`benchmark/runs/step2_targeted_c/`），P17、P03、P04 在 11-01 也是同样原因失败。
- **补丁后**（`benchmark/runs/detour_2eps/`、`detour_3eps/`，`e495350`）：11-02 开车时碰过东西的 7 个加上用过下垂姿态的 4 个任务各一个，成功 8/11 → 10/11；开车时碰动的物体 17 → 1（wipe 擦拭行程里的易拉罐，步骤 4）；yaw 目标拒收 0。下垂只在餐厅一带用（T19、T13、T20、T11、T06 各 1–2 次）。整局耗时多数更短（T07 852 → 696 s，T13 1208 → 1106 s，T19 723 → 642 s），但窄处底盘规划慢了约一倍（第 2 节）。
- **11-02 全量**（`ea47359`，`benchmark/runs/v3_sticky_gt_1102_2seeds/`，逐个对比在 `COMPARE.md`）：

| | 11-01（`a0a9574`） | 11-02（`ea47359`） |
|---|---|---|
| 成功 | 108/170 | 117/170（新成功 31，新失败 22） |
| `fallbacks` | 87 | 5 |
| `contacts`（unexpected） | 982 | 1040 |
| `disturbed` | 没有这个指标 | 175，其中 26 次记在 `drive_base` 上 |

22 个新失败的归类：

| 类别 | episode | 原因 | 处理 |
|---|---|---|---|
| 代码写错 | T01 overhang_ready ×2、T01 table_set ×2、T13 no_cup_spoon_boxed_in ×2、P15 s11、T05 pen_available s11（8 个） | 终点吸附到格点后已经碰了，终点格子永远到不了 | `348d5c8` 已修（`Lattice.reaches`），4 个重跑全部成功（`benchmark/runs/step2_fix_goal/`） |
| 模型更严格 | P19 ×2、T09 lid_on s10，大概率还有 P05 flip ×2 | `find_park` 按到达姿态检查左臂收起姿态，近处的停车点被拒；停得远了，伸手被岛台挡住 | 步骤 5 |
| 选点差异 | T08 sponge_on_tv_stand、far_sponge_tv、island_cluttered s10 | `navigate_place` 的站位按整机筛，站到了岛台另一侧；wipe 只在附近选擦拭带 | 3a |
| 未细查 | T13 no_cup ×2、no_cup_bowl_on_cabinet ×2、T14 shelf_taken s11、T02 far_crowded s11 | 失败在 pick / place 环节（"not held"、目标不可达），推测是停车点或站位变化引起 | 下一次全量后再看 |

### 步骤 3：手臂按 skill 合并

**目的：** 每个 skill 把空中的中间点合并成"从当前姿态规划到下一个中继位姿"，删掉清单里的 W 类（避障路点）和 F 类（skill 自己写的退路和重试）。

shake、wave、倾倒、搅拌画圈这类路点本身就是任务动作（T 类），保留，只加检查。

**完成标准：** 每个 skill 里的 W、F 类条目清零，删掉的路点没有以任何形式（fallback 分支、备选列表、条件开关）留在代码里；它的运动只剩"规划到下一个中继位姿"和接触段。

#### 定下来的规则（2026-11-02）

**F 类分三种，处理不同：**

| 种类 | 例子 | 处理 |
|---|---|---|
| 候选列表：本质是目标区域 | 搬运姿态 5 个变体、手腕朝向 8 个变体、handover 4 个展示位姿、`NavigateToPlacePolicy` 的候选位姿 | 改成目标集合，交给入口一次规划（见 3a 第一项），不再逐个试 |
| 换策略：一种做法不行换另一种 | pinch 不行改 `pick_flat`、drag 拖不动改从后面推、空中转腕不行改 hang、推门找不到停车点改拉把手、开门失败换停车点、`pick_flat` 换边、flip 的"弧推 → 直推 → 底盘推"、separate 换方向 | **全部删掉**，包括 `auto_recovery` 管着的那几处。删完后 `auto_recovery` 只剩 expose，到时候再定这个开关留不留 |
| 关检查重试、吞异常、降低任务参数 | `(up, FREE), (up, LEGACY), +3cm LEGACY`、`try ... except: pass`、pour 倾角 110° → 40°、stir 缩小半径、wave 举手 3 档、圆上不可达的点跳过 | 删掉。降参数的改成"任务允许的范围"作为目标区域，范围内规划不出来就失败；每个任务的下限在改到它时定，写进代码常量和这里 |

动手之前在几种候选里按可行性挑一个（推还是拖、手腕朝哪个方向），属于下面的目标采样，不算换策略。

**目标采样保留，但采样范围由任务几何决定，不由机器人当前站位决定**（删除清单第 8 节第 5 条）。wipe 的擦拭带、knock/touch 的接触点、stir 的接近方向、pour 的腕角和沿口偏移、upright 的转腕位置都按这个改。wipe 的做法：先在整个支撑面上找空的擦拭带，再给选中的带找停车点（11-02 全量 T08 ×3 失败就是站到了岛台另一侧，只在附近找带）。

**`pick_lift` 是离开支撑面，方向取支撑面法向（竖直向上），侧抓也一样**（删除清单第 8 节第 2 条）。`corner_lift`、`edge_lift` 同样处理。

**离开接触之后直接规划到下一个中继位姿。** 入口已经只把离开接触那一小段（按碰撞模型判断，最多 6 cm）走成直线（步骤 1 补丁）。步骤 3 要做的是删掉 `LEAVE_CONTACT` 动作手写的目标位姿：`pick_lift` 的 `_lift_height`（7 cm / 4.5 cm）、`pick_fail_clear` 的 8 cm、`{verb}_back` 的 `(0.14, 0.08, 0.04)`、`close_push_back` 的 `(0.12, 0.06)`、`place_retreat_*` 的变体列表、`flat_up`、`drop_retreat`、`regrasp_clear` 等。这些动作只给方向，入口沿这个方向离开接触，然后直接规划到 skill 的下一个中继位姿（比如搬运姿态、收起姿态）。为此入口要能接受"只给方向、没有终点"的离开接触，和下一个目标连在一次调用里。

**push 不再按固定的 `PUSH_SEG`（0.25 m）分段**（删除清单第 8 节第 4 条）。选停车点时挑"沿推动方向能推得最远"的那个，从那里推到够不着为止（最多推到剩余距离），需要时再换停车点继续推。每段推完重新测物体位置、重新对准的做法保留：这是推动过程中唯一的反馈。如果推长了物体会被推歪，修法是推的时候监测侧向偏移（接触动作，步骤 4），不是把段长再写死。

**`regrasp_clear`、`release_back` 这类松手后沿放入方向退出的段是接触段（C 类）**（删除清单第 8 节第 1 条），步骤 1 已经改成 `LEAVE_CONTACT`。退完之后再抬、再横移的才是 W，按上一条删。

#### 拆成三步

每一步一个提交（不是每个 skill 一个）；3a 和 3c 之后各跑一次全量（第 3 节）。删除清单第 3 节已按 `67b377c` 刷新（106 条里仍在 94、已改 11、已删 1，另补了 3.10 的 13 条）。

| 子步 | 内容 | 回归 |
|---|---|---|
| **3a 搬运和放置** | 入口加目标集合；`_carry_pose`（`carry_stand_up`、最多 9 个变体、`carry_up` / `carry_in_via`、`_carry_bottom_z`、书本 edge +6 cm），连同经 `stow_load` 调它的 drop / hover / wipe / stir / pour；place 链（含 `place()` 里微波炉分支的死代码，直接删）；drop、hover；`NavigateToPlacePolicy` 的候选列表；wipe 选擦拭带和海绵朝向 | 针对性检查 + 全量 |
| **3b 拿取、开关和持物动作** | pick（3.5，含"选抓取姿态时连上搬运姿态"，见 3a 实施记录）、open / close（3.6）、`held_vertical_move`、rotate、flip、stir、pour、wave、upright（3.7）；各处手传的 `step`、`steps_per_wp`、`smooth`（步骤 1 留下的）；push 改成推到够不着为止 | 针对性检查 |
| **3c 场景特例和其余** | 微波炉（3.8）、`place_flat` / 书架（3.3，T14 书下垂）、S 类写死的常数（清单第 6 节）、`clear_microwave_door_sweep`；双手、sticky、contact、perceive 等（3.9） | 针对性检查 + 全量（即步骤 3 完成） |

`planner._chain` 的"park 搜索只认直线"（步骤 1 留下的）在手写 park 删掉时一起看，归它所在的子步。

#### 3a 第一项：入口的目标集合

现在的入口一次只规划到一个目标（`Motion.plan` 用 `plan_single_js`，`Motion.plan_to` 用 `plan_single`）。F 类里的候选列表要变成"一次规划到集合里任一个可行的目标"，入口要支持目标集合：`move_to` 接受一组位姿（或 `joint_path` 接受一组关节目标），一次调用里选出能到的那个，返回选中的是哪一个。实现上首选 cuRobo 的 `plan_goalset`（`MotionGen.warmup` 要传 `n_goalset`，集合大小因此是固定上限）；如果它不合适，另一种实现是"整组批量 IK、按可行性和代价选一个、再规划到它"。两种都必须是一次调用里同时评估，不能逐个试。

**完成标准（3a）：** 搬运、放置、drop、hover、wipe 选带里的 W、F 类条目清零；全量回归的倒退都能归类。

#### 3a 实施记录（2026-11-03，进行中）

**入口的目标集合（`Rig.move_to_any`）。** 没用 `plan_goalset`：它的集合大小要在 warmup 时固定，换目标类型会重录 CUDA graph；入口的约束（持物保持倾角、直线接近收尾）是按单个目标算的，套不进去。做法是第二种：
1. `Motion.ik_set` 一次算完整组目标：批量运动学 IK（`_Arm.ik_batch`，按 `PATH_BATCH` 补齐，CUDA graph 形状固定）→ 一次检查全部解的碰撞（手里的物体在 `scope` 里）→ 解都碰的目标再做一次批量的带碰撞 IK。每个目标取离当前姿态最近、离关节限位够远的解。
2. 按"最大关节移动量 + 调用方给的代价"选一个，只对它调 `move_to`（以它的 IK 解作关节目标）。选定之后的失败就是这一次运动的失败，不换下一个目标。
3. 日志 `goal_set` 记每个目标的得分、起点和选中的关节解；`plan_failed` 记规划失败的原因（以前只剩退路的报错）。

**`_carry_pose`。** 4 个搬运位置（机身系 (0.35, −0.10) 首选，其余按离它的距离加代价 `CARRY_SPOT_COST`）× 3 个高度（最低允许、当前、再高 `CARRY_RISE`）× 8 个绕竖直轴的手部朝向（`CARRY_YAWS`：竖着的物体朝哪边无所谓）= 96 个目标，一次 `move_to_any`。删掉：`carry_stand_up`、先竖直抬（`carry_up`）、`(FREE, LEGACY, +3cm LEGACY)`、9 个变体逐个试、`carry_in_via`、`carry_in_failed` 后继续。沿书边抓的书 +6 cm 暂时保留（书下垂，3c）。
- **一个都到不了时，手臂留在原处开车**（`carry_pose_kept`，2026-11-03 定）：运动在规划阶段就失败、手臂还没动，开车时底盘规划器本来就做整机检查（手臂和手里的物体都算），伸着的手臂能不能过由它判断。这是搬运姿态的语义（"能收就收"），不是 skill 里的退路；留下的情况要在 3b 消掉，见下一条。
- **根本原因在 pick**（T10 s10）：罐子在岛台上从上往下抓起后肩关节 j1 = 2.24 rad，从这个姿态到任何一个搬运目标都要翻到另一个 IK 分支（最小关节移动 2.05 rad，手部朝向放开之前是 2.30 rad），翻的过程中罐子保持不了竖直，规划失败。11-02 旧代码在同一处也失败（`carry_in_failed`），全量里共 12 次、6 个 episode。**3b 的目标：** pick 选停车点和抓取 IK 分支时，要保证能连到搬运姿态（相邻的中继位姿一起选）。
- 检查：`benchmark/batches/carry_goal_set.json`（8 个，种子 10：P18 地上捡起、T10、T09 沿口抓、T11、T03、T04、P08、T14 沿书边抓）。
  - 第一版（固定朝向、到不了就失败）5/8，`benchmark/runs/carry_goal_set/`：T10 如上；T14 删了书本 +6 cm，书下垂后底部低于要求、放的时候在夹爪里转了（已恢复）；T04 见下。
  - 现在的版本 7/8，`benchmark/runs/carry_goal_set_b/`：T10 走 `carry_pose_kept`，手臂留在原处开车，成功。
  - T04 cup_available 两次都失败：放置时 `place_above` 之后杯子在手里翻了（135–146°，`place_level_dropped`），几次 `place_retry` 都在同一个放置点附近、"hand blocked above support"。在不含 3a 改动的 `9af5c0c` 上同样翻了两次，第三次重试换了放置点才成功（`/data/zenobench/leave_contact_exit/t04_base/`）。归到放置链（3a 下一项）：翻转是放置链本来的问题，搬运改动只改变了重试走向哪个放置点。

**放置链（`place`、`place_on`）。** 中继位姿只留三个：放置点上方（层板是开口外侧）、放下（接触段）、松手后离开（接触段，层板向外、其余向上）。
- **目标集合在停车点搜索这一层**（`planner.find_park_set`）：空位（`free_spots` 的前 `tries` 个）× 物体姿态（摆正 / 按手里的倾斜，2026-11-03 定两种都允许，摆正优先）× 手腕绕竖直轴 8 个朝向，每组是一串目标位姿。每个"候选停车点 × 一组目标"是同一次搜索里的一个候选，代价加上这组的代价（`PLACE_SPOT_COST`、`PLACE_YAW_COST`、`PLACE_TILTED_COST`），一起排序、一起按 `park_quality` 比较，选出停车点和那一组。`max_tries` 是每组各自的名额（共享名额时离目标最近的一圈占满了名额，T20 一个停车点都没找到）。`find_park` 是单组的特例。
- **删掉：** `place_on` 依次试 4 个空位（`place_retry`）、手腕 8 个朝向逐个找停车点、越过最高邻物的中间点（`place_over_neighbours`、`_tallest_near`、三档抬高）、找不到停车点就去掉越障点重来、重测失败改用旧目标、餐桌预抬（`table_pre_lift`）、贴边后退再升、层板预摆姿态（`place_preshape`）、深桶预抬（`container_pre_lift`）和放完回桶外（`container_exit`）、微波炉死代码、松手后的多方向退出。`place_lower_to_contact` 失败不再吞掉。
- **保留：** 到达后重测物体在手里的姿态、重算目标（反馈）；`slots_blocked` 作为目标集合的筛选（手指不查碰撞，步骤 5 再删）；松手后退出失败只记 `retreat_short`（物体已经放好，手臂留给下一个 skill）。
- 11-02 全量里这些分支的触发次数（139 次放置）：重试 16、按倾斜放 8、越障抬高 51、去掉越障点 33、朝向非 0° 22、`container_exit` 39；餐桌预抬、层板预摆、深桶预抬、贴边后退、重测回退都是 0。
- `slots_blocked` 不把放置面所属的物体（`rim:<锅>` 的锅、`top:<方块>` 的方块）算成邻物：以前盖锅盖时 8 个朝向全被锅本身挡掉，旧代码是靠"去掉越障点重来"那条退路里不做这个筛选才成功的（T17）。容器里的东西（锅里的方块）仍会挡掉一些朝向，可以再收紧。
- 门后层板放置（`shelf_front`）在 benchmark 里没有任务用到，没测到。
- 检查：`benchmark/batches/place_goal_set.json`（9 个，种子 10：T04、T06、T11、T02 叠方块、T20 餐桌、T03 容器、T19 深桶、T09 灶台、T17 盖锅盖），`benchmark/runs/place_goal_set_b/`，最终 8/9：
  - T04 一次放好（选了另一个停车位、手腕转 90°、先摆正），之前的翻杯和重试没有了。
  - T20 第一版失败：共享停车点名额（见上），改成每组各自的名额后成功。
  - T17 第一版失败：盖锅盖 0 个候选（见上），修后成功（`/data/zenobench/leave_contact_exit/t17_own/`）。
  - T09 lid_off 失败在搅拌：放番茄时选的停车位不同，之后拿勺子的搬运姿态也不同，`stir` 自己找停车位时 39–52 个候选因"搬运姿态停在那里会碰"被拒，缩小半径重试也不行。归 3b（stir 的停车点搜索和缩半径退路）。之前搬运那批里同一个 episode 成功过两次。
  - 松手后往上 6 cm 的退出点有时没有 IK（T06），记 `retreat_short`，物体已放好，不影响结果。

**待定：** T10 的标准路线（`define_tasks.py` nominal）在开车前 `lift(soda_can, 0.95)`，是为高度和避障写的，按新规范由搬运姿态和底盘规划器负责；`search_first` 路线没有这一步也成功。改 benchmark 路线要先问。

### 步骤 4：接触动作

**目的：** 原阶段 3。接触段（清单里的 C 类）改用 `Allow` 预设，`LEGACY` 清零。

**做法：** 和步骤 1 的 `LEAVE_CONTACT` 一样。接触段是任务规定方向的直线，不规划、不查碰撞，接触只由监视器按 `Allow` 记录；自由空间段从离开接触后的无碰撞点开始规划。

- [ ] 按预设迁移：

| 预设 | 动作 |
|---|---|
| `grasp` | `pick_grasp_fix`、`edge_pre`、`edge_grasp`、`corner_pre`、`corner_grasp*`、`steady_grasp`、flip / upright 的抓握段 |
| `handle` | `close_push_contact` |
| `press` | 按钮的 align / press / retract（含微波炉）、`knock_*`、`touch_*` |
| `sweep` | push / pull / center / separate / sweep 的 down、slide、up；`wipe_press`、`wipe_lift`；`stir_dip`、`stir_circle`；`flat_push*` |
| `set_down` | `place_insert`、`place_lower`、`flat_lower`、`flat_release_down`、`microwave_insert`、`upright_lower` |

- [ ] 清单第 5 节的补充：`button_align` 其实是空中段，改成中继位姿 + 规划；被拆成两段的接近（`corner_pre`、`edge_pre`、`upright_top_in`）合成一段；门和推门逐段切换 `coll_kw` 的写法换成 `handle` 预设。
- [ ] wipe 和 flip 的底盘推（步骤 2 没动的）。
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

- 不加手写的中间点、底盘挪动或"原地转 / 退出来再进"这类备选路径（原阶段 4 第一版 `Motion.sweep` / `Rig.drive_clear` 就是因此被删掉的）。
- 不把旧路点、旧底盘动作留作 fallback。删就是删，退路只有入口里那一条直线（原则 2）。
- 不用"两次查询"让规划器从接触状态出发（审计 4.1：规划时关掉接触的碰撞体，事后再校验手臂其余部分）。这是放宽问题再拒绝，步骤 1 试过后删掉了；接触段一律按 `LEAVE_CONTACT` 的做法。
- 不为了消除规划随机性单独花工夫。
- 不在一个提交里跨步骤改动。

## 6. 还没定的问题

| 问题 | 什么时候定 |
|---|---|
| ~~步骤 2 补丁之后、3a 之前要不要先跑一次全量~~ | 不跑（2026-11-02）：3a 之后的全量同时含补丁、`9af5c0c` 和 3a 的改动，倒退归类时要先排除前两者 |
| 降低任务参数改成任务范围后，每个任务的下限（pour 最少倾斜多少、stir 最小半径） | 3b 改到它们时 |
| 删掉换策略后 `auto_recovery` 只剩 expose，这个开关留不留 | 3b 结束时 |
| `Allow` 的五个预设是否覆盖所有 skill | 步骤 4 迁移时 |
