# 碰撞与运动规划：执行计划

只写要做什么、按什么顺序、做到什么算完，以及维护时必须知道的现有机制。相关文档：

- `COLLISION_AUDIT.md`：最初的现状盘点和问题来源（历史，"审计 x.y"指它的章节）。
- `COLLISION_CLEANUP.md`：要删的东西逐条列表，每条标了类别（W、F、C、K、S、B、X）和归哪一步。
- `skills/`：每个技能现在在物理上一步一步做什么。改了技能就同步改那里。
- `CONTAINER_COLLIDERS.md`：容器碰撞体和真实网格对不上（马克杯、锅），先不修。

代码：分支 `remove-handcoded-motion`。最近一次全量是 `0c7eb90`（119/170），之后的提交里有好几组会改变基线（第 5 节）。

## 1. 目标、原则和检查清单

**目标：** 每个技能只保留必要的中继位姿，中继位姿之间的运动全部由规划器生成。

- 手臂：cuRobo MotionGen，手里的物体算进碰撞模型，需要时加约束（不能倾斜、不能甩、IK 分支连续）。
- 底盘：在 (x, y, 朝向) 上规划，可行性用整机碰撞检查判断（底盘占地 + 两只手臂当前姿态 + 手里的物体）。

**原则：**

1. **碰撞了就补规划器缺的东西，不加路点。** 修法是给规划器碰撞模型、约束或目标区域，不是加中间点、底盘挪动或备选路径。缺规划器就先把规划器做出来。
2. **退路只有一条，只在运动入口里。** 查碰撞的运动规划不出来时，从当前姿态直线走到这次的目标，记一条 `clearance_fallback`（审计第 6 节决定 1）。删掉的路点连代码一起删，不许挪进 fallback 分支；技能里不许有自己写的退路（`for coll in (FREE, LEGACY)`、"带检查不行就关掉检查重试"、"规划失败换一条手写路径"）。fallback 是迁移期的安全网，数量要随步骤下降；某段运动反复退回，就回到原则 1。
3. **意外接触只当指标。** `contacts`、`disturbed` 不算任务失败（决定 2），监视器在所有 profile 默认打开（决定 3）。
4. **每一步单独提交，不跨步骤。** 倒退可以接受，前提是查清楚不是代码写错（第 5 节）。
5. **常数要有名字、有出处，不按场景调。** 目标不是消除常数，而是消除常数背后的路点、退路和场景特例：W、F、S 类的常数随它们的条目一起删。留下来的常数（碰撞模型和约束的参数、搜索预算和偏好、结果判断的阈值、任务允许的范围）满足三条：
   - 是模块级的具名常量，不是调用处的字面量；同一个含义只写一处。
   - 注释里写出处：几何推导（从哪些量算出来，最好直接用那些量算）、实验数据（哪次运行、什么分布；全量后复查）或任务定义。
   - 不为某个任务、某个场景单独改值，也不为让某个 episode 通过去调它。资产的抓取标注（高度、张开宽度）按资产定，算数据，不算按场景调。

   不满足的登记在第 8 节。

**每个技能"做完了没有"的检查清单。** 对技能里的**每一段运动**逐个问：

1. **这一段的目标是中继位姿吗？** 中继位姿是任务本身要求的位置：抓取位姿、放下位姿、按钮位置、把手位置、任务动作的轨迹点（shake、wave、倾倒、搅拌画圈，T 类）。为了避障、为了方便插进去的点都是 W 类，**不管它有没有数字**：用记下来的姿态当路点（"回到进桶前的位置"）、按几何拼出来的点（"先抬到最高邻物的高度"）、有名字有出处的常数偏移（"把手前 12 cm"）都算。
2. **这一段是接触段吗？** 接触段的方向由任务决定（支撑面法向、接近方向），长度由碰撞模型决定，不是写死的距离。
3. **这一段的碰撞规则有没有放宽？** 不查碰撞（`LEGACY`、`unchecked`）、不查手指（`ignore_fingers`）、目标豁免、关掉某些连杆。每一处放宽都要说得出为什么物理上这里允许接触。
4. **这一段失败之后有没有别的路？** 重试、换策略、换参数、吞异常，都是 F 类。

全部答完、清单里该技能的条目清零，这个技能才算做完。`move_to` 的目标里出现字面量偏移是第 1 问的强信号，但没有字面量不代表干净；原则 5 管的是留下来的常数，不能代替这张清单。

## 2. 已经定下的做法

**F 类分三种：**

| 种类 | 例子 | 处理 |
|---|---|---|
| 候选列表，本质是目标区域 | 搬运姿态变体、手腕朝向变体、handover 展示位姿、站位候选 | 改成目标集合，一次评估（第 3 节"目标集合"），不逐个试 |
| 换策略 | pinch 不行改 `pick_flat`、拖不动改推、空中转腕不行改 hang、推门找不到停车点改拉、开门失败换停车点、`pick_flat` 换边、flip 的"弧推 → 直推 → 底盘推"、separate 换方向、pick 放开腰限重试 | 全部删掉，包括 `auto_recovery` 管着的。动手之前按可行性在几种做法里挑一个（推还是拖、手腕朝向）属于目标采样，不算换策略 |
| 关检查重试、吞异常、降低任务参数 | `pick_grasp_fix`、`try ... except: pass`、pour 倾角 110° → 40°、stir 缩小半径、wave 举手 3 档、圆上不可达的点跳过 | 删掉。降参数的改成"任务允许的范围"作为目标区域，范围内规划不出来就失败；每个任务的下限改到它时定 |

**目标采样的范围由任务几何决定，不由机器人当前站位决定。** 先在整个任务几何上采样（整个支撑面上的空带、整圈接近方向），再给选中的目标找停车点。

**离开接触：方向由任务决定，长度由碰撞模型决定，然后直接规划到下一个中继位姿。** 抓起是离开支撑面（竖直向上，侧抓也一样）；松手后是沿放入方向的反方向。退完之后再抬、再横移的都是 W。

**push 不按固定段长分段。** 选"沿推动方向能推得最远"的停车点，推到够不着为止，需要时换停车点继续。每段推完重新测、重新对准保留（推动过程唯一的反馈）。推歪的修法是推的时候监测侧向偏移（步骤 4），不是写死段长。

**手里有东西时不做目标豁免。** 手去的是物体要去的地方，不是去碰那里的东西。

**pick 和 place 的接近、离开、搬运查手指**（步骤 5 的例外，提前做了）；其他技能的 `ignore_fingers` 留到步骤 5。

## 3. 现在的机制

### 运动入口（`rig.py`）

- `move_to`、`move_to_any`、`joint_path`、`move_left_to` 共用 `_motion_path`：不查碰撞（或没有 world）就走直线；查碰撞就在 `_planning` 里规划；fallback 类的 Allow 规划不出来、或起点已在碰撞里，就走直线并记 `clearance_fallback`；其他的抛 `SkillFailure`。
- `move_to` 的规划：直线（`cart_path`）→ `plan_to`（持物时保持倾角的位姿约束，否则以直线接近收尾）→ 规划到关节目标。关节目标这一档必须保留：不持物时位姿约束的规划几乎总是失败（3a 全量 231 段成功 6 段）。
- 关节目标（`_goal`）：有 `q_hint`（停车点搜索验证过的解）时，它的 TCP 离目标 1 mm、0.01 rad 以内且无碰撞就用它本身（`HINT_REACH`、`HINT_TURN`：底盘停在搜索给的位置上，就规划到搜索验证过的那个目标）；否则沿它的分支重解；再不行就没有关节目标，不换 IK 分支。没有 `q_hint` 时取当前姿态附近的 IK 解。
- 不查碰撞的直线（`_straight_move`）：直线没有 IK 时关节插值到 IK 解；朝 `q_hint` 摆动超过 1 rad 的仍然规划（前臂扫过垃圾桶）。
- 手里的物体进碰撞模型（`Motion.scope`）：每次查碰撞的运动把它的包围盒球挂到该臂的 held link 上。起点时还贴着东西、又不是离开接触的运动，这一段不带它。
- 持物约束（K 类）：手里有东西时一律平滑跟随，手臂关节限速 0.5 rad/s（沿口捏着的容器 0.25）；规划器里保持倾角，直线关节插值用 `tips_over` 检查；`q_hint` 保持 IK 分支连续。
- 规划器里的头和手指按仿真里的实际值锁定（两根手指取张得更开的那根）；停车点搜索查抓取时，模型里的手指张到候选的宽度（`Motion.hand_open`）。

### 接近与离开（`Rig._approach`、`Rig.leave`）

物理上怎么走见 `skills/approach_leave.md`。要点：

- **接近**：技能给中继位姿、方向 u、直线长度 L。自由段规划到直线起点，再沿直线进去，手指和目标物体都是障碍物（`FREE_SPACE_KW`）。
  - `Allow` 不查碰撞时（place 的 `place_down` 等，`into_contact`）：接触段长度由碰撞模型往回量（多走 `LEAVE_MARGIN`，最长 `LEAVE_MAX`），直线起点在中继位姿往回 max(L, 接触段) 处，接触段不查碰撞。
  - `Allow` 查碰撞时（pick 的 `pick_grasp`）：终点本身必须无碰撞，没有接触段，规划不出来就失败，不退回直线。
- **离开**：技能只给方向。沿方向走到机器人（含手指、手里的物体）离开周围 5 mm 以上再多 1 cm，最多 6 cm（终点没 IK 就减半）；抬起时（`lifts_off`）至少升高 `LEAVE_GAP`。判据用间隙不用穿透：手里物体的碰撞球内切在包围盒里，平放时穿透深度正好是 0。
- 接触段不整段规划的原因：cuRobo 拒绝从碰撞中的起点规划；关掉起点检查让优化器自己挤出去，方向不受控。

### pick（两段式，`_pick_pinch_core`）

物理上怎么走见 `skills/pick.md`。

1. **张开的手到抓取位姿**：一次查碰撞的运动（`pick_grasp`），最后一个手指长度加 1 cm（约 7.3 cm，`pick_approach`，11-06 起）沿夹爪轴直线，要抓的物体是障碍物，不做目标豁免。停车点验证用同一条规则：接近起点和抓取位姿按自由空间查，模型里的手指张到候选的宽度；抬起 3 cm（`PICK_LEAVE_CHECK`）那一项照旧（那时物体算在手里）。
2. **合爪**：只动手指，`closing(name)`（这只手的手指可以碰这个物体）。然后竖直离开接触，再规划到搬运姿态。

抓取高度：顶部捏取张开的指垫最低那个角至少比物体下面的表面高 `PAD_FLOOR_GAP`，按这次夹爪朝向算，表面取它所在的支撑面或包围盒最低点（`_surface_under`）；掌心、相机不碰物体的最低高度由 `tools/prepare_assets.py` 按碰撞球对物体网格推导，写在抓取标注里。

### 目标集合

- `Rig.move_to_any`：一次批量 IK 算完整组目标（手里物体在模型里），按"最大关节移动量 + 调用方的代价"选一个，只对它做一次运动。选定后的失败就是这次运动的失败，不换下一个。
- `planner.find_park_set`：停车点搜索里的目标集合。每组是一串目标位姿，每组各自的名额（共享名额时最近一圈占满，别的组没机会）。目标可以带自己的 `coll_kw`（`_chain`），展开检查用第一个目标的。
- 用在：搬运姿态（`_carry_pose`，4 位置 × 3 高度 × 8 朝向）、放置（空位 × 摆正 / 吊着 × 8 手腕朝向）、drop / hover（8 手腕朝向）、wipe（8 条带 × 4 海绵朝向）、站位（`base_reachable` 距离场筛选后取最近）、收臂（{收起, 下垂}）。

### 目标豁免（`Motion._targets_allow`）

TCP 目标点落在某物体真实包围盒加 `TARGET_PAD`（3 cm）里，这个物体的整个碰撞体在这段运动里对整个机器人都不存在。手里有东西、或 `coll_kw` 里 `exempt_targets` 为 False 时不做（`FREE_SPACE_KW`；pick 全程这样）。还在用的：place 停车点搜索里的接近起点（`FINGERS_KW`）和步骤 4 之前的其他技能。这是粗放的规则：手腕、小臂也能穿过目标物体的其他部位。只有带 TCP 目标点的查询会豁免：`ik` / `ik_global`（目标点）、`ik_set`、`cart_path`（起点和终点都算）、`plan_to`（起点和终点）、`clearance`；`free`、`near`、`segment_free`、关节空间的 `plan`、`explain` 不带目标点，不豁免。所以同一个姿态，用 IK 解出来时"不碰"、再用 `free` 查可能"碰"。各技能在步骤 4 改成 `Allow` 预设时取消。

### 底盘规划器（`base_planner.py`）

- **状态**：(x, y, 朝向) 格点，5 cm、15°，加一维"手臂姿态"，调用方给姿态链（navigate 是"出发 → 收起 → 下垂 → 到达"；拿着东西时下垂就是搬运姿态）。
- **格子可行**：底盘占地不碰标注盒子、地上物体和门（`footprints_clear`，和 `find_park` 同一判据）；该姿态下两只手臂、躯干、头和手里物体不碰真实碰撞体（`Motion.base_depths`）。第一个姿态允许不比起点陷得更深。
- **底盘用标注盒子、不用真实碰撞体**：房间外壳网格在门洞底部有约 0.3 m 高的伪影，有的门洞按网格算不到 0.4 m 宽；仿真里底盘碰撞体本来就关着。
- **块懒惰计算**：8×8 格 × 24 朝向一块，第一次问到时整块交给 GPU。姿态完全相同的共用缓存。
- **姿态切换**：只在格子上原地切，抽样检查，执行是检查过的直线插值（`Rig.swing`）；相同姿态之间不用切，所以下垂只在收起过不去的那段用。
- **代价**：距离，转向每弧度 1 m，每次切换 0.3 m。
- **终点**：先查精确终点在到达姿态下可行；到达条件是终点格或离它一格一档、能直线开到精确终点的格（停车点贴着家具，吸附到格点后可能已经碰了）。没有目标时找最近能完成最后一次切换的位姿。
- **搜索**：加权 A*（启发 × 2.5，扩展上限 20 万），启发是底盘内切圆在标注盒子上的测地距离，到不了的格子剪掉。
- **惰性边检查**：路径逐边按 2 cm 密集检查，某边不通就把它所在块里同方向的边一次查完再重搜。
- **执行**：底盘是固定基座的 x、y、yaw 关节，位置驱动。**不要改回拖动浮动基座**（以前腰被拖到限位前倾 40°）；改底盘控制后要看开车时腰的偏差。yaw 目标保持在 (−π, π]，超界会被拒收。速度上限只在 `Rig.drive_base` 一处，按手里的东西定。
- **接入方式**：完整规划（`relocate`、`navigate`）；固定路径整机检查（转身、平移、后退，不通就失败）；规划器给路径、调用方自己开（双手搬运）；停车点和站位按整机筛。

## 4. 已完成

| 提交 | 内容 |
|---|---|
| `ef01cb1`、`a0a9574`、`ca5a550` | `clearance.py`（`Allow` 等）、技能作用域、监视器（意外接触、被碰动的物体）、`tools/audit_collision.py`；63 处空中运动改 `FREE_ELSE_STRAIGHT`；收起姿态恢复肘外 |
| `83d097b`、`d8cfef8`、`9af5c0c` | 步骤 1：入口收敛、手里物体进碰撞模型、离开接触段按碰撞模型定长、持物限速平滑；边走边伸手 / 抓 / 放停用 |
| `ea47359`、`348d5c8`；main `91276e7`、`8cdd32d`、`b850b79`；`f15cb3d`、`e495350` | 步骤 2：整机底盘规划器、B 类删除、底盘关节、yaw 范围、惰性边检查、下垂按需绕行 |
| main `c583120` | 录像只留跟随相机、15 fps |
| `f5779ab`、`0909b03`、`9b1ce93` | 3a：目标集合（`move_to_any`、`find_park_set`）；搬运姿态、放置链、drop、hover、站位、wipe 选带的变体和退路删掉 |
| `3e6fdf4` | 3b 第 1 项：豁免盒子用真实包围盒（托盘不再对规划器不可见）；站位可达性按整个场景算 |
| `5372541`、`0c7eb90` | 3b 第 2 项：入口的接近和离开；pick、place、drop、wipe 的预备点、写死的抬起 / 退出终点和吞异常删掉；收臂可选下垂 |
| `519cd78`、`99d02f1`、`b81bdfa`、`9614253` | 原则 5；导航常数：开车速度上限收到 `drive_base`，站位的占地余量改成和底盘规划器一致，站位不再只取前 6 个 |
| `16f7276`、`39bca85`、`dccf75c` | pick：sticky 焊住也要手指没合到底才算拿住；抓取位姿接触测量（`grasp_contacts`）；top_pinch 的高度按掌心碰撞球推导 |
| `a3b8aa6`、`e8925a1`、`32f445b` | 手指碰撞球改成指垫方块上的三排；躯干、头少几个球（守住 cuRobo 快速自碰撞内核）；规划器的头和手指按实际值锁定；退回直线、接近直线碰撞时记下位置和对象 |
| `6466347`、`f5081e9` | pick 两段式；顶部捏取的指垫高度按夹爪朝向和支撑面推导 |
| `a99d8e7` | 左臂收起姿态 `LEFT_ARM_FOLD` 改到底盘柱子以内（步骤 5 的一项提前做）；`build_curobo_robot.py --links`（不带参数）只更新默认姿态和自碰撞对 |
| `281cf99` | 真实接触（PhysX 接触报告）和 pick 接近时逐 tick 盯住目标物体（第 5 节） |
| `ba9fd99` | `_goal` 一条规则：验证过的解还到得了就用它，否则沿分支重解，不换分支 |

## 5. 回归方法

**每一步**：单元测试、`build_skill_library --check`，加上这一步动到的技能对应的几个 episode（只单独重跑相关的，不整批反复跑）。第 1 节清单能静态数的部分由 `tests/test_collision_audit.py` 卡住：`tools/audit_collision.py` 按文件统计 `LEGACY` / `unchecked`、目标豁免、`ignore_fingers`、目标里的字面量偏移、`except` 和吞异常、遍历备选的重试循环等，任何一项比 `tests/fixtures/collision_audit_baseline.json` 高就失败（`--sites --kind <类>` 看具体位置）；降下来了就用 `--update-baseline` 把基线一起降下来提交。

静态计数清零只是必要条件（`while` 换点、用返回值换策略、按几何拼的避障点数不出来），所以还有这几样：

- **运动记录。** 每段运动在入口（`Clearance.motion`）记一行，写进 `result.json` 的 `contacts.segments`：技能、段名、哪只手臂、碰撞规则（free / planned / fallback / leave_contact / into_contact / lifting / legacy / unchecked / base_drive；`follow` 前没声明运动的记 raw）、手里有没有东西、这段之前的碰撞查询放宽了什么（`exempt` 目标豁免、`fingers` / `hand` 不查这只手）。`tools/motion_signature.py RUN --save <快照>` 存一份，之后 `--compare <快照>` 列出新出现、消失的行：每一行要么是这一步想要的，要么是漏改的。fallback 次数受规划随机性影响，只显示，不算差异。**还没存过快照**：6.1 的验证批次跑完后存第一份（`tests/fixtures/motion_signature_approach_leave.json`）。只记这只手自己的放宽，"另一只手的手指一律不查"是常开的，不记（步骤 5 删）。
- **真实接触**（`physx_contacts.py`）：监视器打开时（所有 profile 默认打开），每个 tick 读 PhysX 接触报告（机器人躯干以上的连杆挂 `PhysxContactReportAPI`；Isaac Lab 默认关掉接触处理，`make_rig` 里打开，不改仿真，耗时多 2–3%）。当前运动的 `Allow` 不允许的新接触记一条 `physx_contact`，写进 `contacts` 的 `physx_unexpected`、`physx_by_leg`、`physx_records`；手里拿着的东西不算。pick 的接近（`pick_grasp`）逐 tick 盯住目标物体（`Clearance.watch`），记 `approach_watch` 和 `contacts.approach`，推动 1 mm 或转 1° 以上算动了（`approach_moved`）。监视器原来的检查（`unexpected`、`disturbed`）用的是规划器的碰撞球、每 30 tick 一次、阈值 2 cm / 20°，还会丢掉被抓物体的记录，漏掉了 T04 手指打杯子（4 mm、2.9°）：**以真实接触为准**。
- **覆盖率。** `ZB_COVERAGE=1` 跑针对性 episode，`tools/skill_coverage.py RUN --file zeno_skills/skills.py` 列出这批 episode 一次都没进去的函数：没跑到的路径，回归通过也说明不了它对，要么补 episode，要么在完成标准里写明没验证。
- **Stop 钩子**（`.claude/settings.json` → `tools/stop_check.py`）：Claude 每轮结束前，`zeno_skills/`、`tools/`、`tests/` 有改动时检查改过的 Python 能编译、审计计数没超基线，不过就不让结束；没改动直接放行。单元测试要在容器里跑半分多钟，不放进钩子。

**全量**（T、P 全部 variation，种子 10、11，170 个）：批次 `benchmark/batches/v3_sticky_gt_2seeds_video.json`（`sticky/gt`，录像），驱动脚本参考 `/data/zenobench/bench_1104/drive.sh`。只在这些节点跑：pick 和 place 修完后（6.2 结束，重新定基线）、3b 完成后、3c 完成后、步骤 5 完成后。和上一次全量比：成功数、`contacts`、`disturbed`、`fallbacks`、`physx_unexpected`、`approach_moved`，逐个对比写在 `COMPARE.md`。

**基线**：3a（`0909b03`）139/170，`benchmark/runs/v3_sticky_gt_1103_3seeds/`；3b 第 2 项（`0c7eb90`）119/170，`benchmark/runs/v3_sticky_gt_1104_2seeds/`。之后这些提交会改变停车点、IK 解、目标选择，暴露出原有的弱点，下一次全量的倒退要先按它们分：导航常数（`99d02f1` 等）、标注高度（`dccf75c`）、碰撞模型和锁定（`a3b8aa6`、`e8925a1`）、pick 两段式（`6466347`、`f5081e9`）、左臂收起姿态（`a99d8e7`）、`_goal`（`ba9fd99`）。最近的针对性结果：`benchmark/runs/twophase_1105`（`6466347`，approach_leave 14 个 + T13 no_cup + P14，s10，12/16）。

**倒退怎么处理**：每个新失败看日志和录像，归到三类之一：

| 类别 | 怎么判断 | 怎么办 |
|---|---|---|
| 代码写错 | 删错了中继位姿、`allow` 声明错、参数传错 | 修好再往下走 |
| 规划器能力不够 | 记到 `clearance_fallback`，或退回的直线撞了 | 记下来，可以先接受；之后按原则 1 补 |
| 规划随机性 | 同一提交重跑 2–3 次结果会翻 | 接受 |

规划随机性不去消除：GPU 上的归约本身不确定，`PLAN_TIMEOUT` 按时间截止也受负载影响（审计 7.4）。

**注意**：24 GB 显卡上最多同时 2 个仿真；全量跑的时候不要改这个 checkout 的代码（每个 episode 是单独进程，会混进不同版本）。

## 6. 待办（按顺序）

```
1 手臂规划前提 ✓ ──► 3 手臂按技能合并 ──► 4 接触动作 ──► 5 左臂和清理
2 底盘规划器 ✓
3a ✓ ──► 3b 第 1、2 项 ✓ ──► pick 两段式 ✓ ──► 6.1 pick（暂停）──► 6.2 place 修完 ──► 6.3 3b 其余 ──► 6.4 3c
```

**现在在哪（2026-11-06）**：6.1 pick 暂停（已知问题见 6.1，过程归档在 `archive/PICK_6_1_2026-11-06.md`），进入 6.2 place，先做 6.2 第 0 项"放完收不回臂"。基线是 11-06 全量（`543f600`）124/170（`benchmark/runs/v3_sticky_gt_1106_2seeds`，失败最后一帧拼图 `FAILURES_last_frame.png`）；之后的 `9e7d6cb`、`ba99d7c` 只做过针对性运行。不属于 pick / place、要在 6.3 之前查的：P06 双手交接（左臂新收起姿态到 `handover_left_pre` 出 `GRAPH_FAIL`，`benchmark/runs/left_fold_1105`）；导航原地摆臂擦墙（T13 no_cup `navigate_bookcase_2` 的 hang / arrive 摆臂，底盘规划器按 2 cm 采样检查摆臂，`/data/zenobench/approach_moved/run_fix`）；P15 `search_object` 没看见垃圾桶。

### 6.1 pick 修完（暂停，2026-11-06）

**范围**同前：`pick` 从选停车点到抓起后到达搬运姿态为止；微波炉腔体取物和双手平抬留在 6.4。过程记录（每批结果、每个问题怎么查到的）归档在 `archive/PICK_6_1_2026-11-06.md`，物理步骤见 `skills/pick.md`。

**做了什么**（都在 `remove-handcoded-motion`，没推送）：两段式接近（`6466347`）；删掉 pick 里的 F、W 类重试、腰限和"不管附近物体"（`7da5df2`）；edge / corner 捏取删掉，平板物体改夹厚度 `thickness_pinch`（`7da5df2`）；手指碰撞球包住指垫（`0c87cee`）；合爪前查到位、两指都合拢才算夹住、用实测手位姿（`a6e5254`）；规划器右手指跟随左手指（mimic）、整机模型的头和手指按实际值（`543f600`）；地上物体的表面算上脚下的静态碰撞体（地毯，`9e7d6cb`）；接近段 = 手指长度 + `LEAVE_MARGIN`（`ba99d7c`）。

**结果**：11-06 全量（`543f600`）直接调用的 pick 148/162（91.4%），14 次失败里 10 次之后修好并重跑验证（T12 玩具车 ×6、P11 ×2、T04 no_cup ×2）；接近时推动要抓的物体 240 次里 1 次（T13 s11 bowl_on_cabinet，见下 2）。修好后的针对性运行（`/data/zenobench/approach73`，29 个 episode）：pick 36/36，44 次接近都没推动物体，`pick_grasp` 无真实接触，接近自由段直线 30/36。**所有验证都在 `sticky/gt` 下。**

**已知问题（暂停时还开着的）：**

1. **到位检查误判"被挡住"**（T06 s10 木块差 6.8 mm、T10 s11 易拉罐差 7.9 mm，同一张桌子 (3.7, 6.3)）：物体没动、没有真实接触、模型里抓取位姿也不碰。`follow` 收尾在关节误差 < 0.01 rad 就停（手臂 0.8 m 上约 8 mm），到位检查门槛是 5 mm（`PICK_REACH_TOL`），手还在收敛就被判失败。修法方向：等到 TCP 误差 < 门槛或关节不再动，停住了还超门槛才算被挡。11-06 定：先不改。
2. **T13 s11 no_cup_bowl_on_cabinet 真被挡住**：差 5.8 cm，马克杯被推 1.66 mm / 1.9°，左手指和杯子有真实接触（`v3_sticky_gt_1106_2seeds`）。没查。
3. **找不到停车点**：T02 s11 far_crowded（木块 b，前置条件 `grasp_clearance` 也不满足）；P16 两个种子 empty 里拿樱桃番茄（11-04 起就失败）。没查。
4. **翻书**（T15 book_free ×2、P05）：`FlipFlatPolicy` 按旧 edge 抓取的收尾写的，现在 pick 抓完去搬运姿态、书整本离开桌面。需要把 pick 拆成"抓住"和"拿起"两段，翻书只用前一段。随 6.2（`place_flat`、翻书）一起做。
5. **抓取质量被 sticky 掩盖**：合爪后物体焊在手上，`physical` profile 下 pick 没测过。已经看到的：T20 table_full s10 沿口捏的碗搬运中在手里移了 6.1 cm（6.2 第 0 项）；T03 far_small_and_large 擀面杖 pick 成功，后面 `lift_object` 时已不在手里（离手 0.62 m），没查。
6. **搬运姿态去不了**（`carry_pose_kept`）：11-04 全量 75 次，11-06 全量 19 次；pick 后手臂在另一个 IK 分支上要翻转（T10）。原第 f 项，没做。
7. **停车点验证的抬起长度 3 cm（`PICK_LEAVE_CHECK`）和执行不一致**：11-06 全量离开段中位 1.7 cm、最长 4.0 cm，执行上限 6 cm（终点没 IK 就减半）。原第 f 项，连同第 10 节"离开接触段提前停下"。
8. **候选逐个找停车点**（`for g in cands`）还是"候选列表"型 F 类：要改成目标集合，`find_park_set` 先支持每组自己的手指张开宽度。原第 e 项。
9. **常数**（第 8 节）：`PICK_LEAVE_CHECK`、`PAD_FLOOR_GAP` 里的 0.022（`prepare_assets.py` 里还有一份）、`slot_blocker` / `GRASP_GAP_M`（手指已在碰撞模型里，pick 里删了，`predicates.grasp_clearance` 还在用）、`check_held` 的阈值、候选排序的 `0.3 × along_rank`、`PICK_REACH_TOL` 5 mm 和 `GRIP_CLOSED_BY` 3 mm（11-05 新加，依据是一批数据）。停车点打分的关节余量只算手臂 7 个关节，不算躯干和腰（cuRobo 轨迹优化在限位 0.05 内重罚，IK 只在 0.001 内）。原第 g 项。
10. **抓取高度的参照面**：有标注支撑面用支撑面高度，没有用包围盒最低点和脚下静态碰撞体顶面（`static_top`，按包围盒）。待定：统一成"物体脚下碰撞几何的最高点"（静态、可动部件、别的物体，网格只取脚下那部分），先离线对比所有支撑面标注和碰撞几何。
11. **测量工具的坑**：cuRobo `get_sphere_distance` 带 gap 或放大球半径时把多个碰撞体的贡献加在一起，不是到单个碰撞体的距离；`Motion.clearance`（停车点打分的 `clear`）用的就是放大半径，可能被低估，没查。接触监视器在合爪时（`pick_close`，11-06 全量 112 条）因碰撞球比指垫大最多 4.2 mm 而误报，真实接触以 PhysX 为准。
12. **完成标准还没达到**：上面 1–3、6–9 没做；针对性检查（含 `physical` profile）和第一份运动记录快照没做；`COLLISION_CLEANUP.md` 3.5 里 pick 的行已清零（push 那行按规则保留）。

### 6.2 place 修完

**范围：** `place`、`place_on`、`place_flat`（书架、平放）、drop、hover，以及 sticky 的 place，从拿着东西选放置停车点到松手离开、收臂为止。微波炉里放（`place_microwave`）留在 6.4。

**要做的：**

0. **放完收不回臂（11-06 发现，先做）**：T13 no_cup s10 把碗放到餐桌后同样收臂失败、底盘开不走（`/data/zenobench/approach73`）。T12 toys_everywhere 两个种子把玩具车放进书架上的托盘后，松手没碰东西（离开段 0），手臂停在托盘上方；收臂失败（s10 收起姿态在这个停车点本身穿进场景 8.3 mm，s11 收起姿态不碰但从松手姿态规划不过去），手臂伸着时底盘一步也走不了，接着找小黄鸭的两个地方都被跳过。place 的停车点验证只看放得下去，没看下一个中继位姿（收起 / 下垂）回得去——和 pick 的 `carry_pose_kept`（6.1 f）同一类。修法方向：停车点验证加"松手姿态 → 收起或下垂"，用和执行一致的检查（第 9 节：不在停车点搜索里做规划级检查）。T12 toys_out 两个种子把车放进储物篮时 `place_drop` 规划失败，一起看（`/data/zenobench/t12_car/rerun`）。

   **搬运中碗在手里滑动**：T20 table_full s10 沿口捏起 `party_bowl_1` 后，放之前重新测量碗在手里移了 6.1 cm（`place_remeasure shift_m 0.061`），`place_down` 规划失败（`/data/zenobench/approach73`；接近段改长后抓取停车点变了一点，间接诱因）。

1. **删掉 place 里剩下的 W、F 类：**
   - `held_vertical_move` / `place_lower_to_contact`（落到支撑面前再往下放到差 6 mm）：改成放下运动本身就到位，或按第 2 节的接触段处理；
   - `slots_blocked`（手指已在碰撞模型里，应该删）；
   - `place_flat`（清单 3.3）：内层板加大 `pre`、`while True` 换点、丢掉推入目标重找停车点、`flat_back_out`、吞异常；书在夹爪里下垂的 `R_fix` 补偿和搬运时书本 edge +6 cm（清单 3.1、清单第 6 节）；
   - sticky 的 `sticky_clear` 上抬 3 档 / 2 档（清单 3.9）。
   - 下游还按 `rig.held["kind"] == "edge"` 认"夹在边上的书"（`EdgePlacePolicy`、`place_flat`、搬运时书本 +6 cm、`hand.py` 的翻书）：抓法统一以后改成看持物的几何（夹在哪条边、多深），不看 kind。不焊时书在指间转、竖直抬不离支撑面（`physical` profile）的问题也在这里定。
   - place 停车点搜索里接近起点的目标豁免（`FINGERS_KW`）：和 pick 一样改成自由空间。
2. **已知的 place 失败：**
   - P18 floor_pick s10 `place_down` 带倾角 `IK_FAIL`（第 7 节）；
   - T09 lid_off 竖着吊放的细长物体松手倒下（第 7 节，放置关系的选择）；
   - T03 far_small_and_large s11 擀面杖放进杯子找不到停车点；
   - T19 bin_on_bookcase ×2：桶不再被豁免后 `drop_above` 带倾角规划不出来（以前 fallback 从看不见的桶中间穿过去）；T10 `hover_above` 带倾角规划失败（第 7 节）；
   - 左臂收起姿态改了以后（`a99d8e7`），在全部 place 上复查 `place_down` 的 fallback（以前大多是左臂压到桌面）；
   - T02 edge_base s11、P12 s10：放完收臂的问题（`Rig.tuck` 查手指之后，s10 已好，这两个没复查）。
3. **常数**（第 8 节里标 6.2 的）：`PLACE_APPROACH`、`SHELF_APPROACH`、`PLACE_*_COST`。

**针对性检查：** 上面列到的 episode 加用到 `place_flat`、drop、hover、sticky place 的（T14、T15 书架等），种子 10、11，加覆盖率。

**完成标准：** place 系每段运动按第 1 节清单答完；`COLLISION_CLEANUP.md` 3.2–3.4 和 sticky place 的行清零；失败都归了类；`skills/place.md`、`skills/drop_hover.md` 同步。做完跑全量，重新定基线。

### 6.3 3b 其余

open / close、rotate、flip、stir、pour、wave、upright、push 推到够不着为止、各处手传的 `step` / `steps_per_wp` / `smooth`（只会更慢，持物限速已在入口）；其他技能 `LEAVE_CONTACT` 动作手写的终点（`{verb}_back` 最长 14 cm、`close_push_back` 12 cm 等）。逐条见 `COLLISION_CLEANUP.md` 3.6、3.7、3.10。改到对应技能时一起查：T18（开门停车位分叉）、T15（翻书路径分叉）、T08 sponge_on_island（`wipe_press` 带倾角规划失败）、T02 far_crowded s10（separate 没推动）。

做完跑全量。

### 6.4 3c 场景特例和其余

微波炉（清单 3.8，包括 pick 里水平退出腔体的写死点、`clear_microwave_door_sweep` 开到写死位姿、`place_microwave`）、S 类写死的常数（清单第 6 节）、双手、contact、perceive 等（清单 3.9）。`planner._chain` 的"停车点搜索只认直线"在手写 park 删掉时一起看。做完即步骤 3 完成，跑全量。

### 6.5 步骤 4：接触动作

接触段（清单 C 类）改用 `Allow` 预设，`LEGACY` 清零。接触段是任务规定方向的直线，不规划、不查碰撞，接触由监视器按 `Allow` 记录；自由段从离开接触后的无碰撞点开始规划。

| 预设 | 动作 |
|---|---|
| `grasp` | `steady_grasp`、flip / upright 的抓握段（corner / edge 在 6.1） |
| `handle` | `close_push_contact`；门和推门逐段切换 `coll_kw` 的写法 |
| `press` | 按钮的 align / press / retract（含微波炉）、`knock_*`、`touch_*`（`button_align` 其实是空中段，改成中继位姿 + 规划） |
| `sweep` | push / pull / center / separate / sweep 的 down、slide、up；`wipe_lift`；`stir_dip`、`stir_circle`；`flat_push*` |
| `set_down` | `flat_lower`、`flat_release_down`、`microwave_insert`、`upright_lower` |

还有：拆成两段的接近（`upright_top_in`）合成一段；wipe 和 flip 的底盘推；其余技能的目标豁免换成预设里的显式声明。预设不够就加预设，不要退回 `unchecked`。

**完成标准：** `LEGACY` = 0；真实接触里的接触都在 `allow` 范围内（现在按开关、按钮的 `button_press` 就会记成意外，T09）。

### 6.6 步骤 5：左臂和清理

- `LeftArmFoldPolicy` 和所有左臂运动走同一套规划，不再直接插值（P07 ×2：停车位置变了，左臂收臂卡在岛台上）。
- `follow` / `left_follow` 只接受检查过的路径。
- 删掉：`ignore_fingers`、"另一只手的手指一律不查"、`other_touching` 的永久排除、`world.active`、`world.left_active`、`WorldModel.temp_obstacles`（空操作）。两只手都碰物体时（handover）在 `allow` 里显式声明。
- `kin.set_base`、`kin.lo` / `kin.hi` 的临时改写换成上下文管理器。

**针对性检查：** P06、P07、handover 相关任务。**完成标准：** `tools/audit_collision.py` 里 `coll_kw` 直接写入和原始 `follow` 调用为 0；清单全部清零。做完跑全量。

## 7. 已知问题（不属于某一步的）

| 问题 | 例子 | 打算 |
|---|---|---|
| 同样输入，cuRobo 规划结果会分叉 | P07 s10 连跑两次一次成功一次 "no IK for shake" | 不单独处理，按第 5 节区分 |
| cuRobo 规划到贴着关节限位的目标很不稳：腰离下限 1 mrad 的目标 4 次成 1 次，往里 0.02 rad 就 4/4 | T04 no_cup 抓马克杯；T17 唯一的停车点关节离限位 5 mrad | 6.1 d：停车点搜索留最小余量或打分惩罚 |
| 手指碰撞球没包住仿真里的指垫方块（28 × 12 × 55 mm）：3 排球只在指尖面中心和方块底面相切，指尖棱边露出 2.3 mm、角 3.7 mm、侧棱 1.3 mm。规划器以为不碰的地方，指尖棱边会碰上 | T04 no_cup s10 接近时左手指指尖压在杯子碰撞壁顶面，杯子被推 4 mm（`/data/zenobench/pick63/t04_physx`） | 试验中（11-05，未提交）：球改成完全包住方块、抓取高度按球的外包围框算，接近时推动物体从 5/49 降到 1/15，笔照样夹住；T12 地上玩具车变失败待查（6.1 a） |
| 马克杯、带柄锅的容器碰撞体和真实网格对不上 | T04 no_cup 抓杯时手指捏在离真实杯壁约 2.2 cm 的碰撞壁上 | 见 `CONTAINER_COLLIDERS.md`；先不修 |
| 仿真里手指只有指垫方块参与碰撞：原网格是 L 形（手指 + 横跨夹爪的滑轨），凸分解成伸进两指之间的楔形，所以整个关掉了（`physics.py`）。指垫以上那段手指、滑轨两端（各伸出夹爪本体约 13 mm）在仿真里不碰任何东西 | — | 这个分支不动（改仿真接触）；以后可以把 L 形拆成几块凸体 |
| cuRobo 快速自碰撞内核上限 16384 对：超过后改用慢内核，单次 IK 约 25 ms → 0.8 s，停车点搜索在时间预算内找不到解 | 手指每根 18 个球、躯干和头不减时 18007 对 | 加球前先算对数（`build_curobo_robot.py` 打印）；现在 16271 对 |
| 搬运姿态到不了时手臂留在原处开车（`carry_pose_kept`，都是带倾角的规划失败）：pick 后手臂在另一个 IK 分支上 | 3a 全量 24 次、11-04 全量 75 次；T10 s10 抓完第 3 个关节 2.30 rad，去任何搬运姿态都要把易拉罐翻约 3 rad | 6.1 先查根因；如果要在停车点搜索里做和执行一致的位姿目标规划，要先解决 CUDA graph 重录的开销（第 9 节） |
| 竖着吊放的细长物体松手倒下，落点离目标 9–12 cm | T09 lid_off（容差 10 cm） | 6.2（放置关系的选择） |
| T10 can_on_island s10 在导航常数提交之后确定性失败：站位占地余量 5 → 3 cm（`99d02f1`）后开往易拉罐的站位变了，之后抓取姿态、垃圾桶旁的悬停停车点都不同，`hover_above` 带倾角规划失败 | T10 can_on_island s10（`benchmark/runs/t10_at_5df416b`） | 规划器能力不够，6.2 和 hover 一起看 |
| P18 floor_pick s10 在 11-04 全量之后确定性失败：去搬运姿态选中的姿态变了，放置停车朝向 0° → −90°，`place_down` 带倾角 IK_FAIL | P18 floor_pick s10（`benchmark/runs/p18_at_16f7276`） | 来自 `0c7eb90` 之后的提交，没二分；6.2 查 |
| 收臂偶尔报 `DT_EXCEPTION`（cuRobo 的时间参数化失败），手臂留在原处，底盘规划器从那个姿态开不出去 | T12 s11 放完玩具车（`approach_leave_e8925a1`）；11-04 全量 4 次 | 待查 |
| 离开接触段上方有东西时会直接顶上去（不查碰撞，最多 6 cm） | 柜子里、层板下面抓取 | 第 10 节 |
| 底盘规划慢：惰性边检查每轮从头重搜 | T13 s10 规划合计 129 s，拿着东西单次最长 52 s | 待定：复用上一轮的搜索树；捷径分批检查 |
| 底盘规划无路可走时要搜完能到的区域才报错 | 极紧的停车点，几十秒 | 待定：搜索前先查终点附近能否接上 |
| 底盘规划器拿着东西时不会自己换搬运高度 | 删掉 `_carry_bottom_z` 的避障抬高后 T13 bowl_on_cabinet 开往餐桌搜到上限 | 待定：姿态链里加搬运高度，之后才能删 `_carry_bottom_z` |
| 占地检查只在 0.15、0.6 m 两个高度取点（`COLUMN_Z`），0.6–1.05 m 之间的台面边漏查（餐桌面约 0.75 m） | — | 待定 |
| 边走边伸手 / 抓 / 放（`policies/mobile.py`）已停用：底盘路径按出发姿态规划，没有整机检查 | 没有任务用到 | 整机规划之前不恢复 |

## 8. 常数登记（不满足原则 5 的）

| 常数 | 问题 | 什么时候处理 |
|---|---|---|
| `PLACE_APPROACH` 5 cm、`SHELF_APPROACH` 16 cm | 沿用旧的 `place_lower`、层板插入距离，没有出处（pick 的已改成手指长度 + `LEAVE_MARGIN`，11-06） | 6.2（接近直线保留，11-05 定） |
| `PICK_LEAVE_CHECK` 3 cm | 依据是 9af5c0c 时抬起离开段最长 2.9 cm，11-04 全量里最长 4.7 cm；执行时上限是 `LEAVE_MAX` 6 cm，两边不一致。倾向：验证到 `LEAVE_MAX`，pick 抬起去掉减半（place 保留） | 6.1 |
| `LEAVE_GAP` 5 mm、`LEAVE_MARGIN` 1 cm、`LEAVE_MAX` 6 cm、`ON_LINE` 5 mm | 步骤 1 补丁时拍定 | 离开段改提前停止时（第 10 节） |
| `TARGET_PAD` 3 cm | 豁免盒子的边距；豁免本身要取消 | 随豁免一起删（步骤 4，6.5） |
| 顶部捏取指垫至少高出底面 0.022 m | `f5081e9` 改成 `PAD_FLOOR_GAP = 0.022 - PAD_TIP`，0.022 本身还是字面量，edge 捏取（`skills.py` 里 `a * 0.022`）和 `tools/prepare_assets.py` 里还各有一份 | 6.1，从夹爪几何推导 |
| 手指槽偏移（张开宽度外 6 mm、沿夹爪 ±1.4 cm、底面上 3 mm 到抓取点上 4 cm，`slot_blocker`）；`GRASP_GAP_M` 3.5 cm | 字面量，两处的手指厚度没关联；手指进碰撞模型后这个筛选应该删；place 的 `slots_blocked` 同理 | 6.1（place 的在 6.2） |
| `check_held` 的滑移 5 / 8 cm、手指间隙 4 / 8 mm | 没有出处 | 6.1 |
| pick 候选排序的 `0.3 × along_rank` | 拍定 | 同上 |
| `CARRY_SPOTS`（4 个位置）、`CARRY_RISE`、`CARRY_BODY_W`、`CARRY_SPOT_COST`；`PLACE_*_COST`；`WIPE_*` | 3a 拍定 | 搬运的在 6.1，`PLACE_*` 在 6.2，`WIPE_*` 在 6.3 |
| `DRIVE_EMPTY` / `DRIVE_LOADED` / `DRIVE_SWINGING` | 继承的，没测过 | 测一次拿着容器开车、转身时物体的晃动 |
| `STANDOFF_*`、`ROOM_SPOT_*`、`SAME_POSTURE`、`AT_PARK_*`、`FACE_ERR_DEG`、`RETREAT_*`、`BACK_OFF_SLACK`、`DEPTH_TOL`、`PHYSICS_HZ` 相关的"等一秒"、`REST_TOL` / `STOWED_TOL`、`HELD_CHECK_EVERY`、`BLOCKED_PROBE_M` | 有名字，没出处 | 改到所在技能时 |
| 探索的 `COVER_*`、`VIEW_TURNS`、`SWEEP_*`、`VIEW_TRIES`，以及 `max_views` / `min_spacing` 的默认值（`perceive.py`） | 继承的，没测过 | 6.4（和清单 3.9 的"视点不可达就跳过"一起） |
| `FOOTPRINT_MARGIN` 4.6 cm（原来两层余量之和）、`FOOTPRINT_GRID`、`COLUMN_Z` | 值没测过（已知的一项：11-04 全量 2409 次开车，终点误差都在 7 mm 以内，即日志的厘米舍入；开车途中的跟踪误差没记）；`COLUMN_Z` 漏查（第 7 节） | 待定，改了要针对性检查站位和路径 |
| `base_planner` 的 `TURN_COST`、`SWITCH_COST`、`GREEDY`、`MAX_EXPAND` | 偏好和预算，没有数据 | 底盘规划提速时 |
| 停车点搜索次数（pick 120、push 60、`ApproachTargetPolicy` 160） | 各处不同 | 改到所在技能时 |
| `planner.Grid` / `plan_path` 的 `R_BASE` 0.28 m | 没有 cuRobo 时的旧规划，回归不走 | 步骤 5 清理 |

没动的：接触段里的底盘推速度（wipe 0.05、`hand.py` 0.06 m/s，步骤 4）、微波炉的 0.06 / 0.2 m/s（6.4）、bimanual 0.12 m/s（6.4）。

## 9. 试过、不要再做的

- **手写中间点、底盘挪动、"原地转 / 退出来再进"的备选路径**（原阶段 4 第一版 `Motion.sweep` / `Rig.drive_clear`）。
- **把旧路点、旧底盘动作留作 fallback。**
- **"两次查询"让规划器从接触状态出发**（规划时关掉接触的碰撞体，事后再校验其余部分）：放宽再拒绝，接触段一律按离开接触的做法。
- **把接近直线当约束放进单条 cuRobo 轨迹**（`PoseCostMetric` 的 offset 约束，`create_grasp_approach_metric` 那种）：只是代价项，末端不严格沿直线，T20 抓碗时手指从侧面推开了碗。它的语义：误差是"当前位姿 − 目标位姿 + offset"，`project_to_goal_frame=True` 时在目标坐标系里算（直线只能沿夹爪的某根轴），False 时在世界坐标系里算（只能沿世界的某根轴）；约束只在 `offset_tstep_fraction` 之后的时间步生效，之前完全没有位姿代价，所以没法同时"全程保持倾角 + 最后走直线"，持物时只能二选一。用"规划到直线起点 + 查碰撞的直线"，和 cuRobo 0.7 自己的 `plan_grasp` 一样。
- **cuRobo 的 `plan_goalset` 做目标集合**：集合大小要在 warmup 时固定，换目标类型会重录 CUDA graph，入口的约束也套不进去。用批量 IK 选一个再规划。
- **在停车点搜索里做批量 IK 或和执行不一致的规划检查**：批量 IK 和单个 IK 交替会每次重录 CUDA graph（P15 一次搜索 39 次，每次约 6 s）；对固定关节解做关节规划又比执行严格，误拒能走通的停车点（T12 s11 抓鸭子）。用关节移动量做阈值也分不开（成功的搬运有 14 次超过 2.0 rad，失败的在 1.4–2.1 rad）。
- **先删 `_carry_bottom_z` 的避障抬高**：底盘规划器先要能换搬运高度（第 7 节）。
- **高处顶部捏取的 2.5 cm 接近特例**：把岛台上的易拉罐也算成旋钮，接近起点贴在罐顶上（P15）。
- **用拖动浮动基座的方式开底盘**：腰被拖到限位（第 3 节）。
- **为消除规划随机性单独花工夫。**

## 10. 还没定的问题

| 问题 | 什么时候定 |
|---|---|
| 离开接触段要不要在逐点检查时，碰到"一开始就在碰的东西"以外的任何东西就提前停下，交给后面的规划 | 6.1 |
| 降低任务参数改成任务范围后，每个任务的下限（pour 最少倾斜多少、stir 最小半径） | 6.3 改到它们时 |
| 删掉换策略后 `auto_recovery` 只剩 expose，这个开关留不留 | 6.3 结束时 |
| `Allow` 的五个预设是否覆盖所有技能 | 步骤 4（6.5） |
