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
| 3b 第 1 项 `3e6fdf4`（11-03） | 目标物体豁免按碰撞体的真实包围盒算（托盘不再对规划器不可见）；每段查碰撞的运动记 `exempt`；`base_reachable` 按整个场景算距离场 | 第 4 节步骤 3，3b 实施记录 |
| 3b 第 2 项（11-04） | 入口的接近（`approach`、`into_contact`）和离开（`leave`）；pick、place、drop、wipe 的预备点、写死的抬起 / 退出终点和吞异常删掉；手里有东西或接近的自由段不做目标豁免；搬运和收臂查手指，收臂可选下垂；停车点按目标各自的 `coll_kw` 验证 | 第 4 节步骤 3，3b 实施记录 |

**已知还没解决的问题：**

| 问题 | 例子 | 归到哪一步 |
|---|---|---|
| 同样输入，cuRobo 规划结果会分叉 | P07 s10 连跑两次，一次成功一次 "no IK for shake" | 不单独处理，见第 3 节 |
| 离开接触的段（`LEAVE_CONTACT`）的目标位姿仍是手写的：`{verb}_back` 最长 14 cm、`close_push_back` 12 cm、`flat_up` 横 12 cm 加高 6 cm 等。pick、place、drop 的已改成 `Rig.leave`（3b 第 2 项） | — | 3b 其余、3c（`place_flat`） |
| 底盘规划慢：惰性边检查每轮都从头重搜，窄处绕开被禁的边要好几轮 | T13 s10 规划合计 129 s，拿着东西开车单次最长 52 s | 待定：重搜时复用上一轮的搜索树；捷径分批检查 |
| 底盘规划无路可走时，要把能到的区域搜完才报错（几十秒） | 极紧的停车点 | 待定：搜索前先查终点附近能否接上 |
| 边走边伸手 / 抓 / 放（`mobile.py`）：底盘路径按出发时的手臂姿态规划，行驶中手臂在动，只逐步查手臂（抓、放不查手指），没有整机检查。**已停用**（2026-11-02）：三个 policy 一调用就报 `SkillFailure`；没有 benchmark 任务用到（`pick` / `place` 的 `pass_by`） | — | 待定：整机规划之前不恢复 |
| 左臂收起姿态的手指伸出底盘，靠近台面的停车点被整机检查拒掉；放东西时躯干下降，左臂 `link_5` 压到桌面（3b 第 2 项起竖直下放查碰撞，这里落到 fallback） | 11-02 全量里 P19 ×2、T09 lid_on 抓锅盖停得太远；3b 针对性检查里 T20 table_full s10 被顶住（11 mm），`place_down` fallback 6 次 | 步骤 5 |
| 左臂收臂直接插值，不经过任何检查 | `LeftArmFoldPolicy` 的 `link_7` 压进岛台 46 mm；P07 s11 碰倒杯子 | 步骤 5 |
| `ignore_fingers` 让带检查的动作不查手指（pick / place 的接近、离开、搬运已改成查，3b 第 2 项） | `tuck` 和其余 skill 的手指压进台面 | 步骤 4、5 |
| ~~规划出来的 `place_above` 推走了托盘~~ | T12 s11 | 已修（3b 第 1 项）：是目标物体豁免，见 3b 实施记录 |
| 搬运姿态到不了时手臂留在原处开车（`carry_pose_kept`）：pick 把手臂留在了另一个 IK 分支上。3b 第 2 项试过在停车点搜索里检查，比执行严格、误拒能走通的停车点（T12 s11），去掉了 | T10 s10 | 待定：停车点搜索里做和执行一致的位姿目标规划（要解决 CUDA graph 重录的开销） |
| `_carry_bottom_z`（搬运高度抬过台面上已有物体，W 类）删不掉：底盘规划器拿着东西时不会自己换搬运高度 | T13 bowl_on_cabinet s10：删掉后开往餐桌搜到上限 | 待定：底盘规划器的姿态链里加搬运高度 |
| 竖着吊放的细长物体（勺子）松手后倒下，落点离目标 9–12 cm，容差 10 cm | T09 lid_off s10 | 3b 其余（放置关系的选择）或 3c |
| 书在夹爪里下垂 65–74°，带进碰撞模型后 `flat_pre` 压进书架 | T14 | 3c（`place_flat` / 书架） |
| 11-02（`ea47359`）之后新出的两个确定性失败，`a323805` 上就有（3a 全量里 T07 仍失败，P06 这次成功）：P06 s10 `handover_present_across` 规划成功、左手却没有 IK（11-02 是规划失败退直线、碰巧接住）；T07 microwave_works s10 `microwave_button_pre` 换了 IK 分支，按键直线没有 IK（11-02 按键就差 2.4 cm） | 连跑 3 次结果相同，不是随机性 | 下一次全量时看是哪一个提交引入的（步骤 2 补丁或合并进来的 main） |
| 11-02 全量的 6 个新失败没细查 | T13 no_cup ×2、no_cup_bowl_on_cabinet ×2、T14 shelf_taken s11、T02 far_crowded s11 | 3a 全量里都成功了，不再查 |
| 3a 全量里没查清的分叉：T18 开柜门前导航停的位置、T15 翻书选的路径都和 11-02 不同 | T18 at_island ×2、T15 book_out_of_view ×2 | 3b（open、flip）时一起看 |

## 3. 回归方法

**每一步：** 单元测试、`build_skill_library --check`，加上这一步动到的 skill 对应的几个 episode。

**全量（T、P 全部任务的所有 variation，种子 10、11，共 170 个 episode）：** 批次 `benchmark/batches/v3_sticky_gt_2seeds_video.json`（`sticky/gt`，录像）。只在这几个节点跑：步骤 2 完成后（已跑）、3a 完成后、3c 完成后（即步骤 3 完成）、步骤 5 完成后。和上一次全量比四个数：成功数、`contacts`、`disturbed`、`fallbacks`。

**3a 之后的全量**（2026-11-03）用三个种子：`benchmark/batches/v3_sticky_gt_3seeds_video.json`（255 个，种子 10、11、12），输出 `benchmark/runs/v3_sticky_gt_1103_3seeds/`，驱动脚本 `/data/zenobench/bench_1103/drive.sh`（`COMPARE.md` 里种子 10、11 和 11-02 逐个对比，种子 12 只计成功数）。

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
| **3b 拿取、开关和持物动作** | **第一项：pick 和 place 的接近与离开**（见下面"3b 第一项"）；pick（3.5，含"选抓取姿态时连上搬运姿态"，见 3a 实施记录）、open / close（3.6）、`held_vertical_move`、rotate、flip、stir、pour、wave、upright（3.7）；各处手传的 `step`、`steps_per_wp`、`smooth`（步骤 1 留下的）；push 改成推到够不着为止 | 针对性检查 |
| **3c 场景特例和其余** | 微波炉（3.8）、`place_flat` / 书架（3.3，T14 书下垂）、S 类写死的常数（清单第 6 节）、`clear_microwave_door_sweep`；双手、sticky、contact、perceive 等（3.9） | 针对性检查 + 全量（即步骤 3 完成） |

`planner._chain` 的"park 搜索只认直线"（步骤 1 留下的）在手写 park 删掉时一起看，归它所在的子步。

#### 3b 第一项：pick 和 place 的接近与离开（2026-11-03 定）

3a 之后 pick 和 place 还是旧结构："写死的预备点 + 直线进去"和"直线出来 + 写死的终点"，而且这些几厘米的短段只要直线不撞就走直线，规划器很少出手：

| | 预备点 / 进去 | 出来 / 终点 |
|---|---|---|
| pick（`_grasp_legs`、`_lift_height`） | `pick_pre_far` 后退 8 cm 抬 4 cm → `pick_pre` 前 4 cm → `pick_grasp`（不查手指，目标物体豁免） → 误差大时 `pick_grasp_fix`（不查碰撞） | `pick_lift`：离开支撑面那段直线，剩下规划到上方 7 cm（高处 4.5 cm） |
| place | `place_above` 上方 6 cm → `place_lower` 竖直 5 cm，不查碰撞 → `place_lower_to_contact` | `place_retreat_up`：离开接触那段直线，剩下规划到上方 6 cm |

按"只留中继位姿"，pick 的中继位姿是抓取位姿，place 的是物体放在支撑面上的位姿，其余的距离都是路点。**改法：**
1. **接近：** 从当前姿态直接规划到中继位姿，约束最后一段沿接近方向（pick 沿夹爪方向，place 竖直向下）走直线。入口的 `plan_to` 已有这种约束（`approach_metric`，最后一段沿目标的某个轴走直线），只是现在的调用方式是先到预备点再直线进去。要补的是：接近方向和最后一段的长度由调用方给，而不是按起点到终点的方向猜；以及最后贴近那一两厘米（手指合上前、物体碰到支撑面前后）作为接触段（步骤 4 的 `grasp` / `set_down` 预设）。
2. **离开：** 离开接触后直接规划到下一个中继位姿（见上面"离开接触之后"那条），不再去写死的 7 cm / 6 cm 终点。
3. 先查 T12 s11 托盘为什么对规划器不可见（第 2 节），否则换成规划约束后照样会推走托盘。

drop、hover 的"上方 5–6 cm"是任务本身（在上方松手、悬停），保留。

#### 3b 的顺序（2026-11-03）

1. **先查 T12 s11 托盘为什么对规划器不可见**（已完成：目标物体豁免的盒子太大，见 3b 实施记录）：给每段规划运动记下被豁免的物体（`_targets_allow`），单独重跑 T12 s11。按结果修碰撞模型：放进容器时不豁免容器本身，或手里物体的碰撞球盖住包围盒的角。不先修，改成规划约束后照样推走托盘。
2. **3b 第一项**（上一节），同时收掉 3a 复盘里归到"3b 第一项"的条目：
   1. 入口支持接近方向约束：调用方给接近方向和最后一段的长度，`plan_to` 直接规划到中继位姿；删掉 `pick_pre_far`、`pick_pre`、`place_above`、`place_lower`。
   2. 入口支持"离开接触后直接去下一个中继位姿"：删掉 `pick_lift` 7 cm、`place_retreat_up` / `drop_retreat` 6 cm 和它们的吞异常。
   3. 手指检查前后一致：接近、离开都查手指，只有最后贴近的接触段不查；停车点验证 IK、检查到达姿态用同一规则（见第 6 节，提前做步骤 5 的一部分）。
   4. `_carry_bottom_z`；pick 选抓取姿态时连上搬运姿态（`carry_pose_kept`）。
   5. 单元测试：`find_park_set`、放置目标集合、接近约束。
   6. 做完跑一次两种子全量（它改的是几乎每个任务都走的路径）。
3. **3b 其余**：open / close、`held_vertical_move`、rotate、flip、stir、pour、wave、upright、push 推到够不着为止、各处手传的 `step` / `smooth`；T18（开门）、T15（翻书）的分叉在对应 skill 时一起查。

#### 3b 实施记录

**第 1 项：托盘为什么对规划器不可见（2026-11-03，已完成）。**
- **原因是目标物体豁免。** `Motion._targets_allow` 把"TCP 目标点落在包围盒 + `TARGET_PAD`（3 cm）里"的物体当成要碰的目标，不算障碍。包围盒（`_owner_box`）用的是每个碰撞体"中心 ± 外接球半径"：托盘 0.27 × 0.2 × 0.055 m 的外接球半径 0.17 m，盒子高约 0.34 m，`place_above` 的目标点（托盘上方约 6 cm）落在里面，整段规划里托盘不存在。加了日志后重跑 T12 s11（`/data/zenobench/step3b/t12_exempt/`）：`place_above` 的 `exempt` 是 `["toy_car", "toy_tray"]`，托盘照样被推开 0.20 m，和全量一致。手里物体的碰撞球没有问题。
- **修法：** `_owner_box` 改成碰撞体 8 个角点变换后的真实 AABB（`Motion.box_corners`）。同一个盒子还用在"拿着的容器里的东西跟着走"和"另一只手抓着的物体"，这两处也跟着变准。豁免规则本身（目标点落在盒子 + 3 cm 里就豁免）没改，步骤 5 换成 `allow` 里显式声明时再删。
- **日志：** 每段查碰撞的 `move_to` 记 `exempt`（直线段记在 `straight_leg`，规划段记在 `planned_leg`）。
- **以前被豁免掉的不只托盘。** 大容器（桶、锅、托盘）在 drop、pour、放进容器的"上方"那段里都看不见。T19 bin_on_bookcase s10 在 3a 全量里成功，是因为 `drop_above` 规划失败（保持倾角做不到）后，fallback 的关节运动穿过了看不见的桶；修好后桶是障碍物，fallback 也规划不出来，这个 episode 失败。归"规划器能力不够"，不是倒退：3a 全量的 6 次 fallback 里本来就有 2 次是 `drop_above`。
- **顺带修的 3a 错误：** `skills.base_reachable`（站位能否开到）的距离场只算"起点和站位的外包框 + 2 m"，底盘规划器算的是整个场景（`scene_area`）。从书架到 desk_1 要从框外绕门洞，3 个站位全被误判为开不到，`search_object` 直接跳过 desk_1（T12 s11 放好之后卡在这里；11-02 同一处正常开到了）。改成和规划器一样用整个场景。
- **检查：** 单元测试 183 个通过（新增扁平物体的豁免盒子）。T12 s11：放置成功，托盘位移 0；修 `base_reachable` 后 desk_1 3/3 可达，整个 episode 成功（`/data/zenobench/step3b/t12_reach/`；3a 全量里 s11 失败在放置）。针对性检查 `benchmark/batches/target_exempt_box.json`（10 个，种子 10，3a 全量里放置 / drop / 盖盖 / 叠方块 / 搅拌成功过的，加 T12 s10），`benchmark/runs/target_exempt_box/`：8/10。T12 s10 和 3a 全量一样 `place_above` 规划失败（第 2 项会把这一段整个换掉），T19 如上。成功的 8 个，`contacts`、`disturbed` 和 3a 全量基本一样，没有 fallback。

**第 2 项：pick、place 的接近与离开（2026-11-03/04，已完成，提交见第 2 节）。**
- **入口的接近（`Rig.move_to(..., approach=(u, L[, q_line]), allow=into_contact(...), free=...)`）。** 调用方只给中继位姿（抓取位姿、放下位姿）、接近方向 u 和直线长度 L，直线起点由入口算，不是 skill 里写的点：
  1. 接触段：中继位姿的关节解先按接触段自己的规则查碰撞（调用方的 `coll_kw`：不查手指、目标豁免），只有找不到时才用不查碰撞的解（第一版直接用不查碰撞的解，解出来的夹爪本体压在岛台里，接触段把夹爪开进了岛台，差 2 cm 没到抓取点：T10、P15）。从这个解沿 -u 往回走，按碰撞模型（带手指、带手里的物体）算机器人什么时候不再碰，和离开接触同一套（`_exit_length`，多走 `LEAVE_MARGIN`，最长 `LEAVE_MAX`）。这一段不规划、不查碰撞，在 `into_contact` 下走直线（新 Allow：`to_contact`，可以碰 `touch` / `held_on`）。日志 `contact_entry`（`entry_m`）。起点本来就不碰时没有这一段。
  2. 自由段：从当前姿态到接触段起点，手指在碰撞模型里，目标物体也不豁免（`FREE_SPACE_KW`：只有接触段可以碰它；T20 第一版豁免了目标，规划出来的路径把要抓的瓶子碰歪了 18°）。做法和 cuRobo 0.7 的 `plan_grasp` 一样：先规划到直线起点（中继位姿往回 max(L, 接触段长度)：最后 L 走直线，接触段本身算在里面，第一版是 L + 接触段，易拉罐的接触段有 4.5 cm，直线起点推到 8.5 cm 外就够不着了；停车点搜索验证过的那个关节解 `q_line` 作 `_move_path` 的 hint，它在实际底盘位置上没有 IK 时就用它本身，和 3a 之前的 `place_above` 一样），再沿直线查碰撞走到接触段起点。手已经在这条直线上时直接走直线。
  3. 规划不出来按 `free`：放进容器是 `FREE`（失败），其余 `FREE_ELSE_STRAIGHT`（从当前位置直线到接触段起点，记 fallback）。
  - 试过、去掉了的：把直线当约束放进一条轨迹（cuRobo 的 offset 约束，`create_grasp_approach_metric` 那种，约束占最后 20%）。它只是代价项，轨迹末端不严格沿直线：T20 抓碗时手指从侧面碰到碗沿，碗被推开 2.5 cm、手停在 4.4 cm 外；P15 抓易拉罐停在 2.5 cm 外，后面的搬运也卡住了。持物时它和倾角约束只能二选一，冒烟测试里倾角都超了。旧的 `approach_metric`（约束占 50%）在 3a 全量里不持物的 231 段只成功 6 段。
- **入口的离开（`Rig.leave(u, label, allow, lifts_off=)`）。** 只给方向，沿 u 走离开接触段（按碰撞模型定长，手指也查），没有终点。直线只算一次，终点没有 IK 就把长度减半（手伸到远处时往上 6 cm 没有 IK：T13；先查一次 IK 再另算直线，两次随机种子的 IK 结果不一致：T09）。`lifts_off`（pick）：物体立在支撑面上，手没升高 `LEAVE_GAP` 之前都算还在接触——手里物体的碰撞球内切在包围盒里，模型常常一开始就说"不碰"（9af5c0c 之后 252 次抬起有 65 次离开段长度为 0），这时直接去搬运姿态，第一段若是横着走，就把罐子拖住了（T10）。下一个中继位姿由下一段运动（或下一个 skill）从这里规划。没有做成"和下一个目标合成一次调用"：pick 要在两者之间登记 held，两次调用连着发效果一样。
- **手里有东西时不做目标豁免**（`Motion._query`）：手去的是物体要去的地方，不是去碰那里的东西。放进托盘时托盘一直是障碍物（第 1 项的托盘问题在新结构下不会再出现）。
- **pick（`_pick_pinch_core`）。** 中继位姿只剩抓取位姿：`pick_pre_far`、`pick_pre` 删掉，抓取是一次 `move_to(抓取位姿, approach=(夹爪轴, PICK_APPROACH 4 cm))`。原来对高处顶部捏取（锅盖旋钮）的特例（接近 2.5 cm）也删了：统一 4 cm 在旧代码对旋钮验证过的高度以内（旧的旋钮 `pre_far` 是 5 cm），而 2.5 cm 把岛台上的易拉罐（中心 0.92 m）也算成了旋钮，接近起点贴在罐顶上，停车点全被拒（P15）。合上夹爪后：手指合到底就是没抓到（只走离开接触段，不吞异常）；否则先登记 held，`leave` 竖直向上离开接触，然后直接规划到下一个中继位姿——搬运姿态（`_carry_pose`，目标集合），到了再判断物体有没有跟上来：sticky 焊住了就算拿住（和 `check_held` 一样；3a 里 T10 的罐子其实只跟着升了 2.7 cm，是焊住的），否则手指没合到底、物体上升量至少是手上升量的一半，加上 `check_held` 的滑移。`_lift_height`（7 cm / 4.5 cm）删掉。搬运姿态的规划改成查手指（以前 `ignore_fingers`：抓完罐子横着去搬运位置时手指在岛台里拖了 4.3 cm 深，P15）。
- **pick 选停车点时连上搬运姿态：试过、去掉了。** 作为 `find_park` 的 `check`：从抬起位姿到搬运目标集合里最便宜的那个，局部 IK 加 `joint_reachable`（倾角保持）。两个问题：用批量 IK（`ik_set`）时每次调用都切换 cuRobo 的目标类型、重录 CUDA graph（P15 一次停车点搜索里 39 次，每次约 6 s）；改成逐个局部 IK 后，它又比执行时严格——执行是"规划到位姿目标、保持倾角"，可以任选 IK 解，检查是对一个固定的关节解做关节规划，T12 s11 抓鸭子时把能走通的停车点拒了，pick 直接失败。和执行一致就得在停车点搜索里做位姿目标规划，又会来回切换目标类型。用关节移动量做阈值也不行：3a 全量里成功的搬运有 14 次超过 2.0 rad，失败的在 1.4–2.1 rad。T10 那种抓取后手臂在另一个 IK 分支上的情况仍由 `carry_pose_kept` 兜着，没有解决。
- **place。** 中继位姿只剩放下位姿（物体底部离支撑面约 1 cm，层板同样）：`place_above`、`place_lower`、`place_insert` 删掉，放下是一次 `move_to(放下位姿, approach=(竖直向下 5 cm，层板是水平伸入 16 cm))`。深容器的 drop 只有松手位姿（`place_drop`）。容器的临时障碍盒（`temp_obstacles`，"容器不在碰撞模型里"）删掉：现在容器在。松手后 `leave` 沿接近的反方向离开接触，然后直接规划到下一个中继位姿——行驶姿态（`Rig.tuck`）；`place_retreat_up` 的 6 cm、层板的 22 cm 和 `retreat_short` 吞异常删掉。只离开接触就停下不够：张开的手留在原地，竖着放的勺子靠在手指上没倒下（T09），手停在托盘正上方时底盘一步都开不出去（T12 s11）。`place_lower_to_contact` 还在（`held_vertical_move`，3b 其余）。
- **收臂（`Rig.tuck`）的目标是行驶姿态集合 {收起, 下垂}**，在当前位置不碰的里面优先收起，选定后一次规划。T12 s11 放完小车，收起姿态在书架边本身就碰（4.5 mm），以前只能交给底盘规划器，而它在手伸在托盘上方时一步都动不了。要求一定收起的两处（`fold_where_possible`、微波炉门轴）用 `tuck(hang=False)`。
- **drop、wipe、navigate_place。** `drop_retreat` 改成 `leave`（6 cm 和吞异常删掉）。wipe 的"擦拭带上方 6 cm"删掉，按压是一次带竖直接近的运动（`wipe_press`）。`navigate_place` 拿着东西时先摆好搬运姿态再选站位（和 3a 给 `place` 做的一样）：站位按当时的手臂姿态检查，开车前 `navigate` 换了姿态就会在站位上撞（P15：pick 的搬运没走到位）。
- **停车点验证和执行同一规则**（第 6 节第 2 条，作为例外提前做）：`find_park` 的目标可以带自己的 `coll_kw`（`planner._chain`）。接近起点查手指（`FINGERS_KW`，目标物体仍豁免：接触段从哪里开始，执行时由碰撞模型定），抓取位姿、放下位姿和离开段不查手指（接触段）。drop、hover 的目标按 `FREE_SPACE_KW` 查。
- **`_carry_bottom_z` 没删成。** 删掉"抬过台面上已有物体"之后，T13 bowl_on_cabinet s10 拿着杯子开往餐桌时，搬运高度从 0.998 m 降到 0.877 m，底盘规划搜到上限（20 万次扩展）也没找到路；保留时 5.9 万次找到。底盘规划器拿着东西时姿态链只有当前一个搬运姿态，不会自己换高度。要删它，先要让底盘规划器能在搬运高度之间切换（和空手时的"下垂"绕行一样），这是规划器缺的能力，待定。
- **检查：** 单元测试 191 个通过（`tests/test_approach.py`：接近的直线起点和接触段、接触段比 L 长、手已在直线上、离开按碰撞模型定长、抬起至少离开 `LEAVE_GAP`、停车点逐目标的 `coll_kw`、搬运目标集合）。针对性检查 `benchmark/batches/approach_leave.json`（14 个，种子 10，T12 用 s11：pick / 放台面 / 进容器 / drop / 叠方块 / 盖盖 / 地上捡起 / T10 搬运），按问题逐个单独重跑修好后，最终代码整批确认一次（`benchmark/runs/approach_leave/`）：10/14。基线是 12/14（3a 全量里这 14 个只有 T12 s11 失败，第 1 项之后 T19 也失败）。
  - T19：`drop_above` 带倾角规划不出来，第 1 项之后就有（规划器能力不够）。
  - T12 s11：小车放进托盘时规划到直线起点失败（容器不给 fallback）。第 1 项之后的运行里同一步成功过，3a 全量的 T12 s10 也在这一步失败（规划器能力不够 / 随机性）。
  - T20（新失败）：竖直下放时躯干下降，收在身侧的左臂 `link_5` 压到餐桌 11 mm，顶住了，手差 4 cm。旧代码的 `place_lower` 不查碰撞，看不出来；现在这段查碰撞，落到 fallback。归步骤 5（左臂收起姿态，第 2 节已知问题）。
  - T09（新失败）：勺子按吊着的姿态竖着放下，松手倒下后离目标 0.100 m，容差 0.10 m（前一轮 0.115，3a 是 0.094）。放法本身带随机性，卡在边上。
  - fallback 0 → 6，全是 `place_down` 的竖直下放段，能看出碰撞对象的都是左臂 `link_5`（2–11 mm），同上归步骤 5。`contacts`、`disturbed` 和 3a 逐个对比基本持平。

#### 3a 第一项：入口的目标集合

现在的入口一次只规划到一个目标（`Motion.plan` 用 `plan_single_js`，`Motion.plan_to` 用 `plan_single`）。F 类里的候选列表要变成"一次规划到集合里任一个可行的目标"，入口要支持目标集合：`move_to` 接受一组位姿（或 `joint_path` 接受一组关节目标），一次调用里选出能到的那个，返回选中的是哪一个。实现上首选 cuRobo 的 `plan_goalset`（`MotionGen.warmup` 要传 `n_goalset`，集合大小因此是固定上限）；如果它不合适，另一种实现是"整组批量 IK、按可行性和代价选一个、再规划到它"。两种都必须是一次调用里同时评估，不能逐个试。

**完成标准（3a）：** 搬运、放置、drop、hover、wipe 选带里的 W、F 类条目清零；全量回归的倒退都能归类。

#### 3a 实施记录（2026-11-03，已完成：`f5779ab`、`0909b03`、`9b1ce93`）

**一句话：** 3a 消掉的是 F 类（逐个试、换路径、吞异常）和一部分 W 类（越障中间点、预抬、预摆、回桶外）；中继位姿本身怎么定义、接近和离开怎么走还是旧的写死方式，见"3b 第一项"。

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

**drop、hover（`DropIntoPolicy`、`HoverOverPolicy`）。** 都只有一个中继位姿：物体在目标正上方（drop：沿口上方 5 cm、居中；hover：目标顶面上方 6 cm）。手腕绕竖直轴 8 个朝向（经过物体参考点）是停车点搜索的一个目标集合（`skills.park_over` → `find_park_set`），到停车点后直接规划到这个位姿。删掉：到了先竖直抬（`drop_prelift`、`hover_lift`）、先到上方 5–6 cm 的点再降下来（`drop_above` 的两段、`hover_above` + `hover_settle`）。容器在规划里是障碍物：drop 的目标点比沿口高出 5 cm 以上，在目标物体豁免（`TARGET_PAD` 3 cm）之外。

**`NavigateToPlacePolicy`。** 依次导航到 `standoff_poses` 的前 6 个站位，改成一个目标集合：先用一个从机器人出发的距离场（`skills.base_reachable`，`base_planner.distance_field`，无向图，一次 Dijkstra）把底盘内切圆到不了的站位全部去掉，再导航到最近的那个，失败就是失败。11-02 全量 112 次里换站位 4 次，原因全是"内切圆到不了"，正是这个距离场判的。底盘规划器本身没有做多终点搜索：它的其他失败原因没有在换站位时出现过。

**wipe 选擦拭带（`WipeSurfacePolicy`）。** 以前只在机器人附近 ±0.4 m、最近的那条边上找空带（11-02 全量 T08 ×3：站到了岛台另一侧）。现在按支撑面几何采样：四条边 × 两档内缩（`WIPE_INSETS` 8 / 4.5 cm）× 每 `WIPE_STEP`（10 cm）一条，去掉被物体占着的，按离机器人的距离（`WIPE_DIST_COST`）和内缩档排序，最便宜的 `WIPE_STRIPS`（8）条 × 海绵 4 个朝向 = 最多 32 组，作为停车点的目标集合；底盘推的那段行程按组检查（`find_park_set` 的 `ride_set`）。只取 8 条是为了控制最坏情况的计算量（每组 80 个名额）。

**同一晚的后续修改（检查中发现）：**
- **搬运时身体直立**：目标集合按"躯干抬到最高、腰伸直、手臂不动"这个参考姿态找 IK 解、算距离，躯干和腰的偏差权重 `CARRY_BODY_W`（3）。以前按当前姿态找，拿完东西弯着腰（腰 0.7 rad，几乎到限位）就弯着腰搬，岛台边的停车位全被"搬运姿态停在那里会碰"拒掉（T08 sponge_on_island）。现在腰多在 0.15–0.4 rad，比较低的搬运位置不弯一点够不着。
- **选停车位前先摆好搬运姿态**：`place` 在停车点搜索之前按开车时要用的高度调 `_carry_pose`，`_carry_pose` 在手已经处于某个搬运目标时直接返回。以前停车点按当时的姿态检查，`navigate` 出发前又换了一个搬运姿态，到了停车位撞书架（T12）。drop、hover、wipe 本来就是先 `stow_load` 再找停车位。
- **"上方"那段运动检查手指**（`skills.fingers_checked`）：`place_above`、`drop_above`、`hover_above` 不再 `ignore_fingers`。从侧面低低地规划过去时，张开的手指扫过了托盘和里面的积木（T12）；旧代码的"越过最高邻物"中间点其实是在替代这个检查。下放、松手这些贴着支撑面的段仍不查手指（步骤 4、5）。
- 检查：`benchmark/batches/drop_wipe_goal_set.json`（8 个）5/8，T08 cluttered、sponge_on_tv_stand 这两个 11-02 因"只在附近找带"失败的都成功了；`benchmark/batches/3a_recheck.json`（8 个，以上修改之后）6/8，`benchmark/runs/3a_recheck/`。
- **剩下的失败归类：**
  - T12 toys_everywhere（托盘在书架上）：见全量回归里的更正。
  - T08 far_sponge_tv：pick 的 `pick_pre_far` 是一次直线关节插值，手腕转 2 rad，不查手指，手指扫进墙、手臂被卡住。停车位因为前面的步骤和 11-02 不同而不同。归 3b（pick）/ 步骤 5（`ignore_fingers`）。
  - T08 island_cluttered：易拉罐在擦拭行程里被碰倒（步骤 4，补丁时就记过），时好时坏。

**3a 全量回归**（`0909b03`，`benchmark/runs/v3_sticky_gt_1103_3seeds/`，逐个对比在 `COMPARE.md`）。按三个种子启动，种子 10、11 跑完后停掉（2026-11-03 定：种子 12 不跑），所以和 11-02 是同样的 170 个：

| | 11-02（`ea47359`） | 11-03（`0909b03`） |
|---|---|---|
| 成功 | 117/170 | 139/170（新成功 32，新失败 10） |
| `contacts`（unexpected） | 1040 | 605 |
| `disturbed` | 175 | 163 |
| `fallbacks` | 5 | 6（`drop_above` 2、`handover_present_across` 2、`carry_in` 1、`place_retreat_up` 1） |
| 规划出来的运动段（`planned`） | 324 | 1089 |
| 合计耗时 | 16.7 h | 14.1 h |

两轮之间还隔着步骤 2 补丁、`9af5c0c` 和单相机录像。新成功集中在 T01 ×4、T17 ×5、T13 ×4、T09 ×3、T14 ×3、T08 ×3、P05 ×2、P15 ×2、T02 ×2。

10 个新失败的归类：

| episode | 原因 | 归类 |
|---|---|---|
| T12 toys_everywhere ×2 | s10：`place_above` 规划失败。s11：`place_above` 规划成功，但走完时托盘已被推开 19 cm、抬高 2 cm，接着不查碰撞的 `place_lower` 撞歪了积木。最初归成"规划器能力不够"是错的：规划出来的路径推走了托盘，说明规划时托盘不可见或模型对不上（目标物体豁免，或手里物体的内切碰撞球漏了角，没核实） | 碰撞模型问题 + 写死的"上方 6 cm + 不查碰撞的下放"结构：3b 第一项 |
| T08 far_sponge_tv s11 | `pick_pre_far` 直线关节插值不查手指，扫进墙 | 3b（pick）/ 步骤 5 |
| T08 island_cluttered s11 | 易拉罐在擦拭行程里被碰倒 | 步骤 4（wipe 底盘推），时好时坏 |
| T07 microwave_works s10 | 按键直线没有 IK | `a323805` 上就有（见第 2 节） |
| T18 at_island ×2 | 开柜门的停车位和 11-02 不同（11-02 前一步导航停在 (3.125, 1.043)，这次 (3.26, 1.05)），门只开到 −1.18（目标 −1.40） | 3b（open）；导航为什么停得不同没查清 |
| T15 book_out_of_view ×2 | 翻书走了"推到边再翻"（`edge_roll`），推的停车位找不到；11-02 走的是沿弧推（`flip_arc`） | 3b（flip / push）；路径为什么选得不同没查清 |
| T09 cookware_choice s11 | 夹勺子没夹住（手指合拢到 0），勺子之前没被碰动 | 3b（pick） |

**全量之后的修正：** `skills.base_reachable` 判断站位能否开到时，没像底盘规划器那样把终点格子算作可通行，站位紧贴家具时会被误判为开不到（全量里 124 次站位选择有 4 次少了候选）。改成终点格子或它的 8 个邻格能到就算（`reached_cells`），没有重跑全量。

**3a 复盘（2026-11-03）：没完成的和有缺口的。**

3a 范围里列了、没做完的：

| 项 | 现状 | 归到 |
|---|---|---|
| `_carry_bottom_z`（搬运高度抬过台面上已有物体） | 范围里点名要删，没动，`place` 还用它定搬运高度 | 3b 第一项 |
| 书本 edge +6 cm | 删了又恢复（T14） | 3c |
| 放置的上方 6 cm 预备点、不查碰撞的 5 cm 下放、退到上方 6 cm | 当成中继位姿留下了，按规范是写死的路点 | 3b 第一项 |
| 步骤 3 规则"离开接触后直接规划到下一个中继位姿" | 3a 的 skill 一个没做：`place_retreat_up`、`drop_retreat` 还是写死的 6 cm 终点 | 3b 第一项 |
| wipe 的预备点（擦拭带上方 6 cm）、`wipe_lift` 8 cm（`LEGACY`） | 只改了选带 | 预备点 3b 第一项，`wipe_lift` 步骤 4 |
| 离开失败只记日志（`retreat_short`、`drop_retreat_short`） | 按"物体已放好"保留，形式上仍是吞异常 | 3b 第一项 |

完成标准："W、F 类条目清零"没满足（上表）；"倒退都能归类"部分满足：T12 根因没核实，T18、T15 的分叉没查清。

做了但有已知缺陷的：
- 目标集合只按 IK 选、不看路径能不能规划：选中的可能规划不过去而别的可以（T10），现在靠 `carry_pose_kept` 兜着。
- 手指检查前后不一致：选停车位时验证 IK、检查到达姿态都不查手指，"上方"那段运动和底盘规划器却查（T12 撞书架、目标一开始就和手指相碰）。
- 搬运时腰仍在 0.15–0.4 rad；常数是拍定的（4 个搬运位置、`CARRY_BODY_W`、`PLACE_*_COST`、`WIPE_*`、wipe 只取 8 条带）。
- 停车点搜索按组分配名额，最坏情况放置 64 组 × 120 ≈ 7700 次 IK 评估，没单独测过。
- 站位选择只做了可达性筛选，底盘规划器没有多终点搜索。
- 容器放置里的 `temp_obstacles` 还在（空操作，步骤 5）。

验证和文档的缺口：单元测试只覆盖 `move_to_any` 和 `reached_cells`（`find_park_set`、`park_over`、放置目标集合的构造、wipe 选带没有）；门后层板放置没有任务用到；`9b1ce93` 的站位修复和 T10 删 `lift` 没进过全量；种子 12 没跑。

**T10 标准路线去掉开车前的 `lift(soda_can, 0.95)`**（2026-11-03 定）：它是为高度和避障写的，按新规范由搬运姿态和底盘规划器负责。重跑 T10 s10 成功（`/data/zenobench/leave_contact_exit/t10_nolift/`）；搬运姿态仍然够不着（`carry_pose_kept`，pick 的 IK 分支，3b）。

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
| ~~3b 第一项要"手指检查前后一致"，等于把步骤 5（删 `ignore_fingers`）的一部分提前~~ | 定了（2026-11-03）：作为明确的例外提前做，只限 pick / place 的接近、离开和停车点的 IK 验证、到达姿态检查；其他 skill 的 `ignore_fingers` 留到步骤 5 |
| 降低任务参数改成任务范围后，每个任务的下限（pour 最少倾斜多少、stir 最小半径） | 3b 改到它们时 |
| 删掉换策略后 `auto_recovery` 只剩 expose，这个开关留不留 | 3b 结束时 |
| `Allow` 的五个预设是否覆盖所有 skill | 步骤 4 迁移时 |
