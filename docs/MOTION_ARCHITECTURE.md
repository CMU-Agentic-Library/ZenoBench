# 运动规划的分层设计

## 1. 规则

1. 每个技能只给必要的中继位姿（停车点、伸入段起点、抓取位姿、搬运姿态、把手前、任务轨迹起点、收臂姿态）。中继位姿之间的自由空间运动由规划器生成，不写中间路点、不写变体列表。
2. 每个决定只有一个出处：技能的 `build`。停车点搜索和执行用同一个 `build`、同样的约束；执行照搜索做出的计划走，要重做也只用这个 `build`。别处只能做两件事：比 `build` 宽松的预筛（只用来排除候选），或者用和计划时同一套判据复核已有的计划（第 8 节）。
3. 没有 fallback：计划做不出来，搜索时不要这个停车点，执行时技能失败。不改走不查碰撞的路，不跳过某段，不缩短重试。同样约束下换一种做法（`free_leg` 的直线 → 关节规划 → 位姿规划）或换目标集合里的另一个目标，不算 fallback。
4. 接触段：方向由任务定，长度由碰撞模型量，允许碰什么用 `Spec.touch` / `Allow` 写明。
5. 持物：手指和手里的物体都在碰撞模型里；要保持倾角时保持，限速。
6. 每段向接触监视声明 `Allow`，意外接触只记指标。
7. 一次只迁一块：每步单独提交，先针对性检查再全量，基线变化分得清来源。
8. 决定早做，轨迹晚做（第 8.1 节）：把几段绑在一起的决定（停车点、目标组、接触位姿的 IK 分支、搬运目标、收臂姿态）在搜索时做，做的时候往后看完整份计划；轨迹（过渡段的路径、接触直线的路点）在执行时可以从实测状态沿已定的分支重新生成。
9. 误差分三层处理（第 8.2、8.3 节）：计划按假设加余量；误差进来的时刻（锚点）复核，复核按实测状态、零余量，通过就原样执行；超出余量就从这里用同一个 `build` 重做到底，旧决定先原样复用，不行再当种子；还做不出来，技能失败。
10. 依赖只能向下（第 2.5 节）：原语和 `build` 不碰 `rig`，停车点搜索只用 `kin` / `world` / `log`，仿真副作用全在 `run` 的 `observe` 和 `execute` 里，且只通过 `Actuator`。阈值常数只有一处出处（第 4.5 节）。

## 2. 分层

| 层 | 在哪 | 负责 | 不负责 |
|---|---|---|---|
| ① 运动原语 | `primitives.py` | 从给定 `State` 和关节角出发生成一段运动（`Segment`），做不出来返回 `Failure(why)`；要做决定的（`decide_ik`）先试给它的旧决定 | 不知道是哪个技能，不知道是搜索还是执行 |
| ② 技能计划（`build`） | `skill_plans/`（按形状分文件，9.4） | 按技能顺序把原语和动作串成 `Plan`，每段从上一段的实际终点出发，动作之间用小函数推进 `State`；目标从 `State` 推出；`prior` 里还成立的段原样拿来 | 不选停车点，不执行 |
| ③ 停车点搜索（`find_park`） | `park_search.py` | 底盘候选、批量便宜过滤、排序，按顺序调用 `build`，返回（停车点，目标组，计划） | 手臂运动细节 |
| ④ 执行（`run`） | `run.py` | 每段前复核这一段，到锚点复核剩下的整份；不成立就用 `build`（`prior` = 当前计划）重做剩下的；执行，读回状态，监视，日志 | 发明运动，另写判断 |
| ⑤ 技能（`Skill` + `run_skill`） | 每个技能一份 `Skill`；`run_skill` 一个 | 技能参数 → 目标集合、`build`、hooks、失败出口；`run_skill` 依次调 ③、开车、④ | 运动细节、重做判断（都在 ①–④） |

层之间只传三种数据：`State`（机器人和世界现在的样子，或者假设的样子）、`Spec`（这一段按什么规则查碰撞）、`Segment` / `Plan`（运动本身）。

### 2.1 搜索和执行都只通过 `build` 碰原语

复核和重做是同一次调用（第 8.3 节）：

```
find_park                                        run（锚点，或某段不成立）
 └─ build(state_at(park), k, prior=排序 IK)        └─ build(当前状态, k, prior=当前计划, start=这一段)
      ├─ free_leg / straight / drive                    └─ 同样的原语；prior 里还成立的段原样返回
      ├─ decide_ik
      ├─ contact_extent / contact_segment
      └─ scripted
```

### 2.2 一个技能从头到尾：pick

```
PickPolicy.execute
└─ run_skill(rig, SKILLS["pick"], args)                     ⑤
   ├─ skill.problem(rig, args, state)                        目标集合：抓取候选（物体框里）
   │    = Problem(goals, build=plan_pick, arrive=收起, travel=收起, near=当前位置)
   ├─ find_park(kin, world, problem, state, log, base)       ③
   │    ├─ 底盘候选 → 预筛（够得着、底盘柱体、行驶姿态整机、开得到）
   │    ├─ rank_ik：批量运动学 IK，排序，结果当 prior
   │    └─ 按顺序 plan_pick(state_at(park), k, prior)        ②
   │         ├─ 到达                   锚点
   │         ├─ 张手                   动作
   │         ├─ decide_ik → free_leg    ① 到伸入段起点
   │         ├─ straight                ① 伸入
   │         ├─ 合爪                   动作，State 记上持物
   │         ├─ 握上                   锚点
   │         ├─ contact_extent + contact_segment   ① 抬起
   │         └─ free_leg(PoseSet)       ① 去搬运姿态
   │       → Found(停车点, k, plan)
   ├─ 不在停车点：run(plan_navigate(...))                    开车（2.3）
   └─ run(act, plan, plan_pick, skill.hooks)                 ④
        锚点：plan_pick(prior=plan) 复核剩下的整份；其余每段 holds；
        不成立就 plan_pick(prior=plan, start=这一段)；hook 判失败就跑 build_clear
```

`plan_pick` 只有一个：搜索时用它证明"在这个停车点能做完"，执行时用它复核、从当前状态重做剩下的。

9.3 第 1 步以后，pick / place / navigate 都走 `motion_skills.run_skill`（2.3）：`skills.pick` → `_pick_pinch_core` → `run_skill(SKILLS["pick"])`，`skill_jobs/pick.py` 的 `pick_job` 给出 `Problem`（`_pick_problem`）、开到以后的计划和 hooks（`_pick_ready`）、结果判断（`_pick_judged`）；place 是 `_set_down` → `run_skill(SKILLS["place"])`，`skill_jobs/place.py`；navigate 是 `skill_jobs/navigate.py`（`plan_navigate`）。其余技能还不走 ①–④，直接调 `rig.move_to` / `joint_path` 等旧入口。

### 2.3 第 ⑤ 层：所有技能的统一形式

每个技能只写一份 `Skill`：

```
Skill(
  name,
  problem(rig, args, state) -> Problem,      # 目标集合（物体框里）、build、arrive / travel、near、prefer
  hooks(rig, args) -> {段名: before / after / around},   # 只做判断和登记，不动机器人（8.6）
  build_clear(state) -> Plan | None,          # 判失败后退出接触的计划（8.6）
)
```

`run_skill(rig, skill, args)` 只有一个：
1. `problem = skill.problem(...)`；
2. 要选停车点的，`find_park`；不选的（姿态类、感知类的头部动作），只在原地 `build`，停车点就是现在的位置；
3. 不在停车点，就构造并执行 navigate 的计划（`plan_navigate`，第 6 节）；
4. `run(rig, plan, problem.build, skill.hooks)`（`rig` 就是 `Actuator`）；hook 判失败时执行 `build_clear` 再抛 `SkillFailure`。

`AtomicPolicy.execute` 只剩 `run_skill(self.rig, SKILLS[name], args)`。迁一个技能 = 给它写 `problem`（目标集合）和 `build`（尽量用下表的模板），hooks 照搬，然后不再调旧入口。

**过渡形式（9.3 第 1 步，`zeno_skills/motion_skills.py`）**：技能的 Python 部分是一个 `job(rig, args, state) -> Job`，`Job` 按 `run_skill` 的步骤给回调：`problem`（没有就原地做，如 navigate）、`no_park(diag)`、`found(found)`（日志）、`travel`（开到停车点时给 navigate 的参数，如 `min_bottom_z`）、`ready(found) -> (plan, build, hooks)`、`failed(exc)`、`done()`。开到以后的"重新测量、整份重做"现在在 `ready` 里，9.3 第 2.3 步删；hooks 里动机器人的部分 2.6 步换成 `build_clear`。到那时 `Job` 就收缩成上面的三样。现在走 `run_skill` 的是 navigate、pick、place；它们的 policy 照旧调 `skills.navigate / pick / place`，这三个函数内部转到 `run_skill`。

形状相同的技能共用一个 `build` 模板（括号里是 v6 路线里的步数，共 2992 步）：

| 形状 | 技能 | `build` 模板 |
|---|---|---|
| 开车 | navigate (1099)、retreat (30)、face / sidestep | `plan_navigate`；retreat 是沿给定方向的查碰撞底盘直线（5.4） |
| 感知 | look (355)、search (121)、explore_furniture / explore_room (79)、measure (19)、inspect (11)、identify、count | navigate + 头部动作；手臂不动，不需要新原语 |
| 取放 | pick (443)、place (359)、drop (47)、stack (26)、lift (13)、hover (11)、cover (10)、present | `plan_pick` / `plan_place`，换目标集合（drop = 放在容器开口上方松手，后面是不预测的锚点） |
| 部件 | open (85)、close (90)、微波炉、heat 里的开关门 | 到把手前 → 伸到把手 → 握上 → `scripted` → 松开 → 离开（第 6 节开关门） |
| 姿态 | bend / straighten (41 / 41)、升降躯干、wave、nod | `free_leg(Joint / JointSet)` + `Spec.joints` |
| 接触 | wipe (10)、stir (10)、expose (7)、roll (5)、press (4)、flip (4)、rotate (4)、touch、sweep、pour | 过渡段 → 进入 → `scripted` → 锚点 → 撤出（第 6 节接触类） |
| 双臂 | bimanual、handover | 拆 `q_body` 以后 |

复合技能（drop、heat、collect）在任务层把几个 `run_skill` 串起来；两个技能之间天然是一个锚点（下一个技能的"到达"）。

**`SKILLS` 是数据，不是 Python 字典。** 上表 7 个形状覆盖约 40 个技能，彼此的差别在数据里是：用哪个 `build` 模板、选不选停车点、`arrive` / `travel` 姿态（将来加几个 `Spec` 常数）；代码部分是 `job`（目标采样、hooks、失败出口）和轨迹函数 `traj`。数据写进 `skill_library/catalog.json` 的 `motion_skills` 块（schema 1，每条带同一动词的 SkillNode 的 `skill_id`）。那份索引是 `tools/build_skill_library.py` 生成的，所以数据的出处是生成器里的 `MOTION_SKILLS`，手改 catalog 会被下次生成覆盖；生成器顺带检查每条都有同名动词的 SkillNode。`motion_skills.load` 加载时逐条校验（字段和类型、形状、姿态、模板是 `skill_plans` 里的构造函数、`job` 能 import），`SKILLS[name]` 第一次用时组装。

这样做的理由：
- 覆盖率、静态审计、v6 步数统计可以直接读 catalog，不用解析 Python，也不会再出现"文档说 116 个策略、代码里是另一个数"；
- 接新任务的新 policy，多数情况是加一行数据而不是加一个类；
- 形状相同的技能共用模板这件事，在数据里是显式的（`template: plan_pick`），在 Python 里只能靠看代码确认。

### 2.4 任务段查什么碰撞（预计设计，以开关门为例）

上表"部件"行里的 `scripted` 段，定死的是 **TCP 的位姿序列，不是手臂构型**：抓法定了以后铰链圆弧把 6 维轨迹完全确定，但 9 维冗余加底盘可动，同一条弧有无穷多条关节解，前臂 / 肘撞门板、门框、柜体是开门最常见的失败方式。所以这一段查碰撞的用途不是改轨迹（全有或全无，改不了），而是给上游的决定当判据：停车点、抓法变体、手臂走圆弧还是底盘带门（第 10 节）。现在的 `_ride_check` 就是 `find_park` 对开门唯一的筛选信号，整段不查，搜索就没有判据，停车点只能退回写死。

按对象分三类：

| 对象 | 查不查 | 为什么 |
|---|---|---|
| 握着部件的那只手（含手指）↔ 该部件 | 豁免 | 按构造一定接触。写成 `Held(kind="part")` + `Spec.touch`，不是"不查"——允许碰什么用 `Allow` 写明（第 1 节第 4 条） |
| 机器人其余部分 ↔ 世界（含按耦合挪过的部件 / 物体） | 查 | 冗余没被定死；这是停车点和抓法能不能用的判据 |
| 被带动的部件 / 物体 ↔ 世界其余部分 | 查，采样更稀 | 门撞到椅子是任务层的失败，应当换停车点 / 换开度，而不是执行到一半被挡住 |

省的是采样密度，不是判据：这一段的几何是单参数族（部件开度 / 推的位移），连续、无突变，按角度或弧长步长取点查即可，不必每个执行路点都查。第 6 节微波炉那条"在 `State` 里取几个部件值查整机"已经是这个写法。

"整段不查"只在几何完全由两端决定、中间是单调插值时成立：抽屉直线接近这种（纯平移，手臂锁住时中间不冒出新碰撞），铰链圆弧不是（门板扫出一片扇形）。另外整段不查的话，`_ride` 偏出 `TRACK_TOL` 就停下的规则也失去依据——它成立的前提正是计划里的构型被证明过安全。

### 2.5 依赖方向：`Actuator` 和 rig-free（第 1 节第 10 条）

现在各层对 `Rig` 的实际依赖（11-08 数的）：

| 层 | `rig.` 引用 | 规则 |
|---|---|---|
| ① `primitives.py` | 0 | 不许 import `rig`。只认 `kin`（`kinematics.ArmKin`，含 `kin.motion`）、`State`、`Spec`；底盘段另认传进来的 `base`（`BaseModel`） |
| ② `skill_plans/` | 0 | 同上 |
| ③ `park_search.py` | 0（第 1 步以前 3 个，外加经 `planner._drivable` 的 `kin.motion.rig`） | `find_park(kin, world, problem, state, log, base)`：整机在行驶姿态下的深度、底盘可达场、开得到，都问传进来的 `base` |
| ④ `run.py` | 0（第 1 步以前 19 个，含私有的 `rig._from_contact`） | 仿真副作用只在 `observe` 和 `execute` 里，且只通过 `Actuator` |
| ⑤ `Skill` + `run_skill` | 允许 | 绑定层：技能参数、标注、当前状态都要从 `rig` 来 |

这个形状由 `tests/test_layering.py` 守住：①②③ 的 import 图（模块级和函数内的都算）不出现 `rig`、`skills`、`planner`、`motion_skills`；`run.py` 只调 `act.` 的协议方法；`Rig` 没有和协议方法同名的实例属性（`Rig.arm` 是关节下标张量，第一版的 `Actuator.arm` 就被它遮住了，所以叫 `arm_kin`）。

底盘的整机模型（球模型、`base_planner`）现在靠 `Rig` 读手里物体的位置，做不到 rig-free。做法和 `kin` 一样：协议 `motion_state.BaseModel`（`plan` / `straight` / `depths` / `reachable` / `drivable`），由 `skill_jobs/base.py` 的 `RigBase` 在 rig 上实现，作为参数传给 ① 的 `drive` / `drive_straight` 和 ③ 的 `find_park`。它从"机器人现在的样子"规划（`state` 是现在的状态，或者现在的状态换了手臂姿态），换机器人时要重写的是它和 `Actuator`。

`Actuator` 是 ④ 唯一能碰的仿真接口：

```
Actuator:
  # 写：execute 用
  follow(qs, steps_per_wp, smooth, side)   # 手臂路点，持物时限速；side="left" 是左臂
  grip(width, ticks, gradual)
  drive_base(path) / swing(side, q)    # 底盘、换行驶姿态
  declare(name, allow, side=None)      # 向接触监视声明这一段（现在的 rig.clear.motion）
  contact_allow(kin, allow)            # 从接触出发时，按现在碰着什么收紧 Allow（现在的私有 rig._from_contact）
  # 读：observe 用，拼出一个 State（4.1）
  snapshot() -> State                  # 现在 run.observe 里那一段：sync_world + 底盘 + q_cmd +
                                       # 头 + 手指宽度 + held_in_tcp + 物体框 + 部件值
  arm_kin(side) -> ArmKin              # 不叫 kin / arm：Rig.kin 是右臂对象，Rig.arm 是关节下标
  log(label, **kw)
```

`Rig` 实现它。两点说明：

- `rig._from_contact` 这种私有方法被 ④ 调用的情况，提升成协议方法 `contact_allow`。
- `observe` 现在直接读 `rig.q_cmd` / `rig.held` / `rig.ann.articulated` 等 13 个属性，拼 `State` 的那段逻辑其实属于"这个机器人怎么报告自己的状态"，搬进 `snapshot()`，④ 就只剩 `state = act.snapshot()`。换机器人时要重写的正是这一个方法。

为什么值得做：
1. **①②③ 可以脱离 Isaac 跑。** `tests/test_primitives.py` 的 FakeKin 已经证明可行，但没有规则保证它不退化。固化之后，停车点搜索和计划质量可以进 CI 回归——按现在的约束（24 GB GPU 最多 2 个 sim，170 集全量要跑一夜），这是唯一能把"计划层的回归"从过夜降到分钟级的办法。现在改一次 `free_leg` 就得全量，成本高到会抑制重构。
2. **换机器人、换仿真器只要换 `Actuator` 和 `kin`。** 接别的 policy 时（第 8.8 节）同理。

## 3. 三种运动

技能里的每段运动属于下面一种，决定它由谁生成：

| 种类 | 是什么 | 谁生成 | 例子 |
|---|---|---|---|
| 过渡段 | 中继位姿之间的自由空间运动（手臂或底盘） | 规划器（`free_leg`、`drive`） | 到伸入段起点、去搬运姿态、到把手前、收臂、开到停车点、带物开车 |
| 进出接触段 | 从中继位姿沿任务给定方向进入或离开接触 | `straight`（进入、撤出）、`contact_extent` + `contact_segment`（离开时长度由碰撞模型量）、`drive` 的直线（底盘退开） | 伸入、放下、抬起、抽出、按钮按下、勺子伸进锅、retreat |
| 任务段 | 任务本身规定的轨迹，写在物体 / 部件坐标系里 | 技能的轨迹函数（`scripted`） | 开关门的圆弧、搅拌画圈、擦桌子的条带、翻书、原地转腕、推一段 |

任务段可以写死，因为它就是任务的定义。但它必须满足第 1 节第 2、3 条：搜索和执行用同一个轨迹函数和参数；搜索时整段查碰撞，全有或全无；执行照走，不跳点。

### 3.1 `scripted` 的准入条件

任务段写死的是"任务的定义"，不是"这次凑出来的一串点"。能写成 `scripted` 的，必须三条都满足：

1. **单参数族**：整段的任务空间轨迹是一个标量的函数 `T(s)`，`s` 单调走过一个区间；
2. **写在物体 / 部件坐标系里**：函数给的是工作点（勺尖、海绵底面、把手）在物体框里的位姿，TCP 由 `State` 推出：`TCP(s) = T_world_obj(state) · T_obj_tool(s) · T_tool_tcp⁻¹`；
3. **`s` 是任务量，不是机器人量**：铰链角、抽屉位移、画圈相位、条带弧长、绕棱转角、推的位移。不能是关节角、路点序号这类机器人侧的量。

所以轨迹函数给的是**函数和区间**，不是一串点；路点由 `s` 的离散化生成，步长是实现细节。现有的任务段都满足：开门 θ、抽屉 d、搅拌相位 φ、擦条带弧长、翻书绕棱角 α、转腕腕角、推一段 d。

**卡掉的是**：一串挑出来的手臂关节角——9 维空间里没有生成规则的点列，没有任何任务量能从第 k 个点推出第 k+1 个。现在逐点 `move_to` 的代码正是这个形态；没有这一条，它可以原样搬进轨迹函数，第 1 节第 1 条（不写中间路点、不写变体列表）就在事实上被绕过，只是换了个文件。

三个推论：

- **拆段的判据**：一段需要两个独立参数，就该拆成两段，或者第二个参数其实是常数。擦桌子的"沿条带走 + 压深"看着像两个，但压深是 `WIPE_PRESS` 常数，压下去那一下是单独的进入段。
- **变体不是段内的自由度**：多条条带、搅拌的 4 个朝向、抓把手的 3 种抓法都在 `Problem.goals` 里（第 6 节），搜索挑定以后这一段只剩一个参数。段内没有自由度可搜索，正是"全有或全无、不跳点"能成立的前提。
- **采样密度是实现细节**：计划按几何步长采样查碰撞，执行按控制步长采样跟踪，两边仍然是同一条轨迹（2.4）。若段是一串路点，"搜索和执行用同一个轨迹函数和参数"就退化成"同一串点"，两边只能同密度。

单参数族说的是**任务空间**，不是关节空间：同一个 `s`，TCP 位姿唯一，手臂构型不唯一（冗余）。关节侧由 `decide_ik` 定分支、沿 `s` 连续跟——这也是 2.4 里"机器人其余部分 ↔ 世界必须查"的原因。

## 4. 数据（`motion_state.py`）

### 4.1 `State`：事实或假设，不可变，没有行为

```python
@dataclass(frozen=True)
class Held:
    name: str                    # 物体，或部件（kind="part"）
    T_tcp_obj: np.ndarray        # 物体框（部件：把手）在 TCP 里的位姿：实测，或计划里假设的
    kind: str = "pinch"          # pinch / edge / corner / bimanual / part
    pad: float = 0.0             # m 碰撞球放大：计划假设的持法（合爪前规划的搬运段，HELD_POSE_MARGIN）

@dataclass(frozen=True)
class Hand:
    width: float                 # 每指 m
    held: Held | None = None

@dataclass(frozen=True)
class State:
    base: tuple                  # (x, y, yaw_deg)
    q_right: np.ndarray          # 躯干、腰 + 右臂 7 个关节（指令姿态）
    q_left: np.ndarray           # 左臂 7 个关节
    head: Mapping[str, float]
    hands: Mapping[str, Hand]    # "right" / "left"
    objects: Mapping[str, np.ndarray]   # 物体框的世界位姿：实测，或假设（刚放下落在哪）
    parts: Mapping[str, float]   # 可动部件的关节值
```

- 执行时 `run.observe(act)`（`Actuator.snapshot`）从仿真读出。搜索时用小函数从当前状态改出假设：`at_base`、`with_arm`、`with_width`、`holding`、`released`、`with_object`，每个都返回新的 `State`。`state_at(park)` = `at_base` + `with_arm(到达姿态)`。
- **完整性**：凡是影响碰撞查询的都在 `State` 里（头、左臂、手指宽度、部件值）。
- `Held(kind="part")`：手握着部件的把手。握着时，那只手的手指对这个部件不算障碍物（和持物一样），松开就恢复。它取代技能里设了不恢复的 `hand_touches_part`。
- `Held.T_tcp_obj` 是"手里的东西在 TCP 里的位姿"的唯一表示。工具的工作点（勺尖、海绵底面）是它的直接延伸：`T_tcp_tool = T_tcp_obj · T_obj_tool`，其中 `T_obj_tool` 是标注里的 `tool_frame`（第 6 节接触类技能）。
- **要改**（和 `Spec.joints` 一起，9.3 第 5 步）：腰和躯干两条链共用，拆成 `q_body` / `q_right` / `q_left`，`State.q(side)` 照旧拼出规划链。
- 不在 `State` 里的：

| 东西 | 放在哪 |
|---|---|
| 碰撞规则 | 每段的 `Spec` |
| cuRobo 对象、碰撞世界缓存 | `Motion`（查询层） |
| 运动学模型 `kin` | 原语的参数 |
| sticky 焊点、接触监视记录、日志 | `Rig`（只在执行时有） |
| 家具、静态场景 | `WorldModel` |
| 观测（图像、点云、检测结果） | 单独的 `Observation`（4.6），**不进 `State`** |

最后一行是硬规则：`State` 必须能是**假设的**——`at_base`、`holding`、`with_object` 推演出来的 `State` 没有对应的观测，一旦把观测塞进去，`build` 就不能再在搜索时推演状态，②③ 两层的整个做法就塌了。

### 4.2 `Spec`：一段运动按什么规则查碰撞

```python
@dataclass(frozen=True)
class Spec:
    allow: Allow = FREE          # 向接触监视声明的接触规则（clearance.py）
    fingers: bool = True         # 手指进碰撞模型
    exempt: bool = False         # TCP 目标处碰到的可以碰（后端按目标位置豁免；持物时恒 False）
    hold_tilt: bool = False      # 手里的东西保持这段起点的倾角
    touch: tuple = ()            # 可以碰的物体 / 部件：对指定部位不算障碍物，其余部位照查
    joints: tuple | None = None  # 这段允许动的关节，其余锁在起点；None = 规划链全部（待加）
    margin: float = 0.0          # m 计划时要求的余量：不在 touch / exempt 里的部位离世界至少这么远（待加）
```

- `touch` 的每一项写成（名字，部位），部位是 `fingers` / `hand` / `load`：手指碰刚放下的物体，手碰门板，持物碰锅或台面。`Allow` 的允许接触由 `touch` 推出，不另写一份。现在的实现只有手指一种，名字是物体。
- `hold_tilt` 保持的是起点倾角。倾角要变（勺子倾进锅、翻书），就在任务段里变，或者在 `hold_tilt=False` 的过渡段里变（持物照样查碰撞）。
- `joints` 取代改 `kin.lo / kin.hi` 和 `_lock_shared_posture`：只动腰、锁腰、左手持物时压腰都用它表达。
- `margin` 只在计划时用（`Kinematics.near(q, margin)` 判碰）；复核用实测状态、零余量（第 8.2 节）。现在唯一的余量是持物的 `Held.pad`；`margin` 留给任务段的 `TRACK_TOL`。
- 执行参数（速度、`smooth`、`steps_per_wp`）放在 `Segment.info`，不进 `Spec`。

### 4.3 `Segment` 和 `Plan`

- `Segment`：名字（`pick_grasp`、`carry_in`…）、`Spec`、起点关节角 `q_from`、路点 `qs`、种类 `kind`、这段的目标 `target`（位姿或关节角，复核用）、动作 `action`、原语量出或选出的东西 `info`（长度、做法、方向 u、判据名）。
- `kind`：`move`（手臂路点）、`drive`（底盘路径，手臂不动）、`scripted`（任务段：路点加执行器名，见 5.5）、`action`（不动手臂：`grip`、`wait`、`drive_part`、`toggle`）、`anchor`（锚点：误差进来的时刻，读回状态、复核剩下的计划，见 8.2；`info` 记这一刻计划假设的值，只用于日志里的偏差）。
- `Plan`：段的元组、服务的目标组 `goal`、决定 `decisions`、构造耗时 `info["stage_s"]`。
- `Plan.decisions`：{名字: 值}，`build` 做的、把几段绑在一起的决定（8.1）：接触位姿的关节角（`pick_reach`、`place_reach`）、搬运目标的序号、收臂姿态的序号。重做时作为 `prior` 传回 `build`。
- `Failure(why, segment, info)`：原语或计划做不出来的原因。搜索按类计数，技能用它报错。

### 4.4 碰撞查询层 `Motion.query(state, spec)`

`Motion.query` 把 `State` + `Spec` 翻译成一次 cuRobo 查询：
- 锁定底盘、另一只手臂、头和手指宽度；
- 把手里的东西挂到夹爪上（`pad` 放大），握着的部件对那只手不算障碍物；
- 把 `objects` 和 `parts` 同步到碰撞世界；
- 按 `Spec` 开关手指碰撞球、目标豁免、`touch`。

退出时全部复原。现在是包一层：内部调旧的上下文管理器（`_planning`、`_fingers_checked`、`_carrying` 等）。全部技能迁完后改成直接实现。`touch` 的"其余部位照查"由 `Motion.path_free_only` / `Kinematics.path_free_only` 另查一遍，`primitives.free_path` 把两次查询合起来。

### 4.5 阈值常数：一处出处（`tolerances.py`，待加）

现在散在四个文件加一份文档，而且层次是反的：

| 在哪 | 有什么 |
|---|---|
| `rig.py` 顶部 | 约 20 个：`BIG_SWING`、`CARRY_VEL`、`RIM_VEL`、`HINT_REACH`、`HINT_TURN`、`PLAN_AT_START`、`SETTLE_*`、`DRIVE_*`…… |
| `primitives.py` | 6 个：`LEAVE_GAP`、`LEAVE_MARGIN`、`LEAVE_MAX`、`ON_LINE`、`JOINT_GOAL_TOL`、`DENSE` |
| `kinematics.py` | `REST_TOL`、`STOWED_TOL` |
| `COLLISION_PLAN.md` 第 8 节 | 力的几何替身（`PRESS_DEPTH`、`WIPE_PRESS`、`TOUCH_DEPTH`……） |
| 还没有 | `BASE_TOL`、`HOLD_DRIFT`、`TARGET_TOL`、`TRACK_TOL`（8.2） |

`PLAN_AT_START` 是层次反了的例子：它是 ④ 的复核判据，却定义在 `rig.py`（基础设施层），由 `run.py` 反着 import。

目标：新架构用到的阈值集中到 `tolerances.py`，按**属于哪一层 / 哪一类误差**分组，每个带单位和**来源标记**：

```python
# 误差上限（8.2 的锚点表）
BASE_TOL    = Tol(0.007, "m",   src="估：COLLISION_PLAN 第 8 节，没细测")
HOLD_DRIFT  = Tol(None,  "m",   src="待测：9.3 第 2.1 步")
TARGET_TOL  = Tol(None,  "m",   src="待定：按抓取能容忍的偏差，不按底盘误差")
# 复核判据（8.4）
PLAN_AT_START = Tol(1e-3, "rad", src="指令对指令，实际是精确比较")
```

来源标记是重点：现在翻四个文件也看不出哪些数测过、哪些是继承下来没验证的（例如 `HELD_CHECK_EVERY` 的注释就写着 inherited, unmeasured）。8.2 那张锚点表就是这个表的雏形——让它在代码里成为单一出处，文档引用它而不是复述它。

执行参数（速度、`smooth`、`steps_per_wp`）不属于这里，它们在 `Segment.info`（4.2）。

### 4.6 `Observation`：观测（待加，只在接外部策略时需要）

`State` 只放 GT（4.1）。将来要接感知驱动的策略时，图像 / 点云 / 检测结果走一个平行的 `Observation`，和 `State` 一起读出、分开返回：

```
Actuator.snapshot() -> State                       # 2.5，GT，build 和原语只拿这个
Actuator.sense()    -> Observation | None          # 相机、点云、检测结果
run.observe(act)    -> (State, Observation | None)
```

`Observation` 只给第 ⑤ 层和外部策略（8.8）。现在没有使用方，不在迁移顺序里，写在这里是为了挡住"把观测塞进 `State`"这条路。

## 5. 运动原语（`primitives.py`）

签名统一为 `primitive(kin, state, spec, ...) -> Segment | Failure`。

### 5.1 `free_leg`：自由空间的手臂运动

目标有四种：
- `Joint(q)`：一组关节角；
- `Pose(p, R, q_hint)`：一个位姿；
- `PoseSet(goals, cost, prefer, weights)`：一组位姿，任意一个都行；
- `JointSet`：一组关节角，按给的顺序取第一个在原地不碰的，再按 `Joint` 走，例如收臂 {折叠, 下垂}（折叠优先，和 `Rig.tuck`、place 的 `tuck` 一样）。

做法：
- 能走直线就走直线：关节目标走关节直线，位姿目标走 TCP 直线；直线不通就规划。
- 位姿目标直线不通、有 `q_hint`（这个位姿的、查过碰撞的 IK 解：`decide_ik` 定的分支，或位姿集合的批量 IK 解）时，按关节目标走到 `q_hint`：关节直线，不通就关节规划；持物时倾斜超标或失败，再按位姿保持倾角规划（`Kinematics.plan(carry=True)`）。终点就是定下的分支。
- 没有 `q_hint` 才按位姿规划（空手最后一段沿轴直线进入，持物全程保持倾角）。
- 位姿集合用批量 IK 选最便宜的，再按单个位姿（带它的解）做。
- `Spec.joints` 给出时，只动这些关节。

"区域"目标（物体底面高于 h、开口上方任意处）由技能采样成 `PoseSet`，不另做区域求解器。

### 5.2 `straight`：查碰撞的 TCP 直线

从给定关节角出发，不从同一起点位姿的另一个 IK 解出发。按 `Spec` 查碰撞，`touch` 里的东西只对指定部位放开。用于伸入、放下、抽出、按下这类进入和撤出段。进入接触的深度（按钮按 `PRESS_DEPTH`、海绵压 `WIPE_PRESS`、指尖压 `TOUCH_DEPTH`）是终点位姿的一部分，由技能从接触面位姿加具名常数算出。这些常数是力的几何替身，统一登记在 `COLLISION_PLAN.md` 第 8 节。

### 5.3 `contact_extent` + `contact_segment`：从接触里出来

`contact_extent(u, touching)` 沿 u 量接触持续多远：先求沿 u 的运动学直线（最多 `LEAVE_MAX`，到没有 IK 为止），在上面用 `exit_length` 量到离开周围 `LEAVE_GAP` 处，再加 `LEAVE_MARGIN`。到头还碰就返回 Failure：不减半，不跳过。

"还在碰"的判据是具名函数，签名为 `(kin, q_from) -> touching(q)`：
- `near_world`：离周围不到 `LEAVE_GAP`；
- `off_support`：物体还没离开支撑面，即上升不到 `LEAVE_GAP`；
- `in_world`：终点还碰。

`contact_segment(spec, extent)` 把量出的段原样作为一段，不查碰撞，按 `spec.allow`（`LEAVE_CONTACT` 等）向监视声明。只用于"从接触里出来"，长度不超过 `LEAVE_MAX`。进入接触一律用查碰撞的 `straight` 加 `touch`。

### 5.4 `drive`：底盘一段（9.3 第 1 步）

`primitives.drive(base, state, goal, chain, name)` 和 `drive_straight(base, state, target, name)`，`base` 是 `motion_state.BaseModel`（2.5）。产出一段 `kind="drive"`：`info["steps"]` 是开车和换姿态的序列，`qs` 是每次换姿态后的右臂姿态（所以 `q_end` 是开完以后的手臂）。`run.execute` 交给 `Actuator.drive_base` / `swing`；`holds` 只查手臂在起点（路径是 navigate 计划时从同一个状态做的）。`skills.relocate` 和 `straight_base_move` 都改成"构造这一段 + `run.execute`"。

两种：
- **规划的**：从 `State.base` 到目标底盘位姿。包现在的 `_base_plan`（`base_planner`）：整机碰撞，手里的东西也算，手臂从 `State` 里的姿态出发；路上折叠放不下的地方换成下垂，在哪换由底盘规划器定（`travel_postures` / `posture_sets`），换姿态是一次查过碰撞的关节直线（`Rig.swing`）。一段 `drive` 就是规划器给出的这一串（开车，换姿态，开车……），执行照旧交给 `drive_base` / `swing`。用于 navigate。
- **直线**：沿给定方向退开到离障碍物 d。方向由任务给（离开障碍物外框上最近的点），整机沿直线查碰撞，挡住就 Failure，不动。包现在的 `straight_base_move`。用于 retreat，属于进出接触段（第 3 节）。

做完推进 `State.base`。路径是轨迹（8.1）：搜索时只证明开得到，执行时由 navigate 的计划用同一个函数、同一组行驶姿态重新规划。技能自己的计划不含 `drive`，从停车点开始，第一段是到达锚点；任务过程中要动底盘的（开门时底盘跟着门、推一段），是 `scripted` 段里带底盘路点。

### 5.5 `scripted`：任务段（待加）

任务段由技能的轨迹函数生成：`traj(kin, state, params) -> 路点`。路点可以是手臂关节角，也可以带底盘位姿。函数还可以给出每个路点处物体 / 部件的预测值，比如门开到多少度、被推的物体到了哪。

- **构造（搜索和执行同一个）**：按预测值挪物体和部件，整段查碰撞（`touch` 放开允许的接触）。有一个点不通就返回 Failure：全有或全无，不跳点。
- **执行器**：
  - `follow`：照路点开环走，用于画圈、擦条带、转腕；
  - 技能自己的闭环执行器：开门时底盘跟着实测开度走（现在的 `_ride`）。闭环执行器只能偏离计划路点 `TRACK_TOL` 以内，超出就停下、技能失败。它只调节怎么跟，不改几何。
- 任务段后面跟一个锚点（8.2），用实测的部件值 / 物体位姿推进 `State`。

### 5.6 动作

不动手臂、推进 `State` 的段：
- `grip(width)`：合爪 → `holding`，松手 → `released`；
- `wait(s)`；
- `drive_part(部件, 值)`：电机开关门；
- `toggle(电器, on/off)`。

锚点不是动作，是单独的段种类（4.3、8.2）。

### 5.7 `decide_ik`：接触位姿的分支（待加）

`decide_ik(kin, state, spec, p, R, prior) -> q | Failure`，按顺序：
1. `prior` 本身：TCP 离 (p, R) 在 `HINT_REACH` / `HINT_TURN` 以内，并且按 `spec` 不碰 → 原样用；
2. 否则 `ik_global`，`prior` 是第一个种子（取离它最近、离限位有余量的解）；
3. 否则 Failure。

搜索时 `prior` 是排序用的批量 IK 解（运动学，没查碰撞，第 7 节第 3 步），执行时重做用的是 `Plan.decisions` 里的值。第 1 步让重做时分支不变，也避开规划随机性：同一个查询算两次结果会不同（`COLLISION_PLAN.md` 第 140、169 行），重新求出的解即使只偏 0.6 mrad，腰离限位 1 mrad，也会从四次规划成功四次变成一次（T04，`Rig._goal` 的注释）。`_reach`（伸入段、放下段起点）和 place 的 `q_p` 都用它。现在 `_reach` 直接调 `ik_global`，没有第 1 步。

## 6. 技能计划（`skill_plans/`，9.4）

每个技能的 `build(state, k, prior, start=...)` 按下表的顺序构造：
- `k`：目标组。目标写在物体框里，TCP 位姿由 `build` 从 `State` 推出：pick 的抓取候选在物体框里，用 `State.objects` 换到世界；place 的目标是物体的放置位姿，TCP 位姿用 `State` 里的握法（`Held.T_tcp_obj`）推出。物体动了、握法变了，从实测状态做出来的就是新目标，不另写"目标偏了就整份重做"。
- `prior`：搜索时是排序 IK 给的 {决定名: 关节角}；执行时重做是当前 `Plan`。每一段先看 `prior` 里同名的段从现在的起点是否还成立（`holds`，8.4），成立就原样拿来；不成立再用原语做，要做决定的（`decide_ik`）先试 `prior.decisions` 里的值。
- `start`：从哪一段开始，执行时重做剩下的计划用。

**pick**（`plan_pick`，到达姿态是收起）：

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达 | 锚点：底盘、物体 | — | 实测 |
| 2 | 张手 | 动作 | — | `with_width(候选宽度)` |
| 3 | 到伸入段起点 | `free_leg`，分支由 `decide_ik` 定（决定 `pick_reach`） | `FREE_HAND` | — |
| 4 | 伸入到抓取位姿 | `straight` | `FREE_HAND`，`exempt` | — |
| 5 | 合爪 | 动作 | `closing(物体)` | `holding(物体, 计划的抓取位姿)` |
| 6 | 握上 | 锚点：握法 | — | 实测的 `T_tcp_obj` 替换假设的 |
| 7 | 抬起 | `contact_extent(off_support)` + `contact_segment` | `LEAVE_CONTACT` | — |
| 8 | 去搬运姿态 | `free_leg(PoseSet)`（决定：搬运目标序号） | `FREE_LOAD`，持物 `pad = HELD_POSE_MARGIN` | — |

**place**（`plan_place`，到达姿态是搬运姿态）：

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达 | 锚点：底盘、握法 | — | 实测 |
| 2 | 到放下段起点 | `free_leg`，`q_p` 由 `decide_ik` 定（决定 `place_reach`） | `FREE_LOAD`，持物 `pad = HOLD_DRIFT` | — |
| 3 | 放下 | `straight`（竖直，长度由 `set_down_length` 从"物体贴着支撑面"往上量） | `FREE_LOAD` | — |
| 4 | 松手 | 动作 | — | `released(物体, 落下 LEAVE_GAP 后)`，手张到抓取宽度 |
| 5 | 落下 | 锚点：物体落点 | — | 实测 |
| 6 | 抽出 | `straight`（沿夹爪轴） | `touch=(物体,)`，手指可碰 | — |
| 7 | 收臂 | `free_leg`（收起，碰就下垂；决定：收臂姿态序号） | `FREE_HAND` | — |

锚点为什么在这几处、每处误差用余量还是重做，见 8.2。

扁平物体（书）也走 `plan_place`。下垂是持物模型的一部分：计划里用假设的位姿加 `pad`，执行时用实测的 `T_tcp_obj`。技能里不再手补姿态。

**navigate**（`skill_plans/navigate.py` 的 `plan_navigate`，9.3 第 1 步）：

| # | 段 | 原语 |
|---|---|---|
| 1 | 到行驶姿态 | 空手：`free_leg(JointSet{折叠, 下垂})`（现在的 `tuck`），已在就省掉。持物：先用同一套判据复核当前姿态（物体在身体前方、底面不低于 `CARRY_Z` 和 `min_bottom_z`、行驶姿态下整机不碰 `poses_clear`），满足就省掉；不满足才 `free_leg(搬运目标集合)`，`FREE_LOAD` |
| 2 | 开过去 | `drive`（规划的，含路上换下垂） |
| 3 | 到达 | 锚点 |

持物时第 1 段是复核加按需决定：pick 的 `carry_in` 已经定了搬运姿态，满足就原样用，不重新决定（第 1 节第 2 条）。只有 place 才知道的要求（容器边沿高度 `min_bottom_z`）不满足时才动。第 1 步以前的 `_carry_pose` 按"离某个目标点 1 cm、0.05 rad 以内"判断已在搬运姿态，几乎总判不在，11-08 全量里又动了约 169 次手臂，还有 1 次退成不查碰撞的直线（T19 s10，`FREE_ELSE_STRAIGHT`）。

实现（9.3 第 1 步）：判据在 `skill_jobs/carry.py` 的 `_carry`，三条——TCP 在底盘系里落在 `CARRY_SPOTS` 外扩 10 cm 的范围（`CARRY_FRONT_X` 0.25–0.55 m、`CARRY_FRONT_Y` −0.40–0 m）；物体底面不低于 `CARRY_Z` 减 `CARRY_LOW_TOL` 1 cm；整机在这个姿态下原地不碰（`RigBase.depths` ≤ `DEPTH_TOL`）。不满足就 `free_leg(搬运目标集合)`（要求的高度优先），做不出来技能失败（不再 `carry_pose_kept`，不再不查碰撞的直线）。`min_bottom_z`（`_carry_floor`：目的地的边沿高度，边夹的书再加 6 cm）不是约束而是"能抬就抬"：够得着那个高度的搬运目标就抬上去，够不着就原样带着走，日志写明原因——带物开车的整机底盘规划本来就查物体和世界的碰撞。第一版把它当约束，v6 T07 microwave_works / T23 spoon_on_floor 要的 1.15–1.18 m 够不着，navigate 直接失败，而旧代码在那里是保持原姿态（f6d16de 改正）。`carry_posture(rig, min_bottom_z)` 是这第 1 段单独跑：place 在停车点搜索之前（这样搜索假设的搬运姿态就是开车时的姿态）、drop、去停靠点前的检查、`stow_load` 用它。空手的 `tuck`、左臂收起做不出来就省掉，由底盘规划在路上换（和以前的 `Rig.tuck` / `_fold_left` 一样）。

navigate(x) 只负责开到 x 那一带，停车点由后面的技能自己选（2.3、第 10 节）。

**retreat**：一段直线 `drive`（5.4），挡住就失败。

**开关门**（待做）：

| # | 段 | 原语 |
|---|---|---|
| 1 | 到把手前 | `free_leg`；抓法变体（钩 / 翻转 / 正面）是目标集合 |
| 2 | 伸到把手 | `straight`，`touch=((部件, fingers),)` |
| 3 | 握上 | `grip` → `holding(部件, kind="part")` |
| 4 | 开 / 关 | `scripted`：铰链圆弧或抽屉直线，预测部件值；执行器是底盘跟着部件走（`_ride`） |
| 5 | 松开 | `grip` → `released` |
| 6 | 离开 | `contact_extent(near_world)` + `contact_segment` |
| 7 | 收臂 | `free_leg` |

推门关：`free_leg` 到推的起点，再接 `scripted` 推（`touch=((部件, hand),)`）。整个过程只握一次。

**接触类技能**（press、touch、stir、wipe、push、roll、flip、expose、sweep，待做）都是同一个形状：到达（锚点）→ 过渡段 → 进入段（`straight`，深度常数）→ 任务段（`scripted`）→ 锚点 → 撤出段（`straight` 或离开段）→ 收臂。工具的工作点（勺尖、海绵底面）是标注里的具名坐标系 `tool_frame`（和 `grasps` 一样写在 `annotations/assets.json` 的资产条目里），由一个函数统一解析成 `T_tcp_tool = Held.T_tcp_obj · T_obj_tool`（4.1），轨迹函数只拿这个矩阵。不要让 10 个接触技能各自从标注换算一遍：那是未来重复代码的主要来源，也是最容易和标注失配的地方。新加一个工具 = 加一条标注，不是加一段代码。跨多个停车点的任务（推每段 25 cm、sweep 逐个物体）每段做一次 `find_park`，段与段之间看实测结果决定下一段。这是任务层的闭环，不是运动的退路。

**姿态类技能**：bend / straighten 是 `free_leg(Joint)`，`Spec.joints` 只放腰。收臂是 `free_leg(JointSet{折叠, 下垂})`。

**微波炉**：电机开门前，`Problem` 加一项检查：部件扫过它的范围时整机不碰（在 `State` 里取几个部件值查）。腔体里的取放是普通的 `straight`，腔体和开着的门都在 `State` 里。电器状态由动作推进。

## 7. 停车点搜索（`park_search.py`）

```
find_park(kin, world, problem, state, log, base=None) -> (Found(x, y, yaw, k, plan, q_rank) | None, diag)
Problem(goals, build, arrive, travel, near, prefer, label)
```

| 字段 | 含义 | pick | place |
|---|---|---|---|
| `goals` | 若干组目标，每组 =（够得着预检用的 TCP 点，排序用的中继位姿，代价） | 每个抓取候选一组（`PICK_CAND_COST`） | 每个"空位 × 物体姿态 × 手腕朝向"一组 |
| `build` | 技能的计划构造函数 | `plan_pick` | `plan_place` |
| `arrive` | 停车点上的手臂姿态 | 收起 | 搬运姿态 |
| `travel` | 开车时的手臂姿态 | 收起 | 搬运姿态 |
| `near` / `prefer` | 离谁近更好 / 先试的底盘位姿 | 当前位置；冰箱层板的种子停车点 | 当前位置 |

1. **候选**：围绕每组目标的中心按半径（`RADII`）、角度（`ANGLE_STEP`）取点，每点取多个朝向（`YAW_OFFSETS`），再加上 `prefer` 和"原地不动"。
2. **便宜过滤**：
   - 够得着：肩到目标的水平距离和高度；
   - 底盘柱体不碰（`world.footprints_clear`），每个目标最多留 `MAX_PER_GOAL` 个；
   - 行驶姿态下整机不碰：批量 `Motion.base_depths`；
   - 开得到：从当前位置算一次可达场 `base_reachable`，查表。
3. **批量 IK（排序，并作为 `build` 的 prior）**：把中继位姿换到各候选的底盘系，批量求运动学 IK，不查碰撞。按有没有解、关节离限位的余量、可操作度、代价排序。解作为 `prior` 传给 `build`，由 `decide_ik` 在碰撞模型里确认，或换成附近的解（5.7）；它不直接当目标。
4. **按顺序构造计划**：`build(state_at(park), k, prior={中继位姿: 解})`，第一个做出完整计划的胜出。预算是 `BUILD_S`（20 s）和 `BUILD_MAX`（60 个），失败原因按类计数进 `diag`。
5. **精确底盘路径**：只对胜出者规划（`base.drivable`）；做不出来就回第 4 步取下一个。路径不留：它是轨迹，执行时 `plan_navigate` 重新规划（5.4）。两边是同一个函数（`RigBase.plan`）、同一组行驶姿态（`skill_plans.travel_chain`，9.3 第 1.4 步）。
计划按（停车点，目标组 k）存。技能要查的东西都在自己的 `build` 里，搜索不再有 `check`、`ride`、`score`、`carry` 之类的开关。任务的不同做法都进 `goals`，不按变体各调一次 `find_park`。

## 8. 执行（`run.py`）

```
run(act, plan, build, hooks):          # act: Actuator（2.5）；build 可为 None（8.8）
  i = 0
  while i < len(plan):
     seg, state = plan[i], observe(act)
     if seg.kind == "anchor" and i + 1 < len(plan):   # 误差进来的时刻：复核剩下的整份
         rest = build(state, plan.goal, prior=plan, start=plan[i+1].name); keep = i + 1
     elif holds(kin, state, seg) 不成立:         # 两个锚点之间：只复核这一段
         rest = build(state, plan.goal, prior=plan, start=seg.name); keep = i
     else:
         rest = None
     rest 是 Failure，或要重做而 build 是 None -> SkillFailure
     if rest: plan = plan[:keep] + rest          # 还成立的段在 rest 里原样出现
     seg = plan[i]
     hooks.before; execute(act, seg) [在 hooks.around 里]; hooks.after
     i += 1
```

### 8.1 决定和轨迹

| | 是什么 | 什么时候做 | 执行时 |
|---|---|---|---|
| 决定 | 停车点、目标组 `k`、接触位姿的 IK 分支、搬运目标、收臂姿态（`Plan.decisions`） | 搜索时，往后看完整份计划：`build` 整份做出来才算 | 复用：原样 → 当种子 → 失败（`decide_ik`，5.7） |
| 轨迹 | 过渡段的路径、接触直线的路点、离开段的长度 | 搜索时先做一份，证明做得出来 | 成立就原样走；不成立就从实测状态沿已定的分支重新生成 |

为什么这样分：几段之间靠接触位姿的分支绑在一起。pick 里伸入段起点的分支决定伸入、抬起、搬运做不做得了；place 里 `q_p` 的分支决定放下、抽出、收臂。
- 每段只规划自己是贪心：前一段的分支可能让后面做不下去（T20 s11 重做 place 后抽出没 IK）。
- 整份一次定死、不复核：搜索时的假设到执行时已经过时（8.2 的表）。
- 分开以后：决定有往后看的保证，轨迹用的是实测状态。轨迹带规划随机性也不要紧，换一条一样能走；决定原样复用，分支不受随机性影响。

### 8.2 锚点和余量

误差不沿计划累积：`State` 里是指令关节角，每段从上一段的指令终点出发；自由空间里世界不变，计划预测得准。误差只在下面几个时刻进来，每个时刻放一个锚点：

| 锚点 | 进来的误差 | 上限 | 用余量还是重做 |
|---|---|---|---|
| 到达停车点 | 底盘停下的误差 | 7 mm 以内（`COLLISION_PLAN.md` 第 8 节，没细测） | 重做：`holds` 的终点检查发现 TCP 到不了目标，就从这里重做，分支原样复用或就近重解，轨迹重新生成。不加余量：余量会拒掉层板、柜子里本来能用的停车点 |
| 握上（合爪后） | 实际握法和假设的不同 | `HELD_POSE_MARGIN` 5 mm | 余量：合爪前规划的搬运段，持物带 `pad`；锚点用实测握法复核搬运段 |
| 到达（持物开车之后） | 持物在手里漂移 | `HOLD_DRIFT`（待测；T17 是 2 mm） | 余量：开车前做的 place 计划，持物带 `pad = HOLD_DRIFT`；锚点用实测握法复核，TCP 目标从实测握法推出 |
| 落下（松手后） | 物体落在哪 | 计划假设下落 `LEAVE_GAP` | 抽出段用 `touch` 放开手指；落点预测不了的（drop）用不预测的锚点（8.5） |
| 任务段之后 | 部件 / 被推物体偏离预测 | `TRACK_TOL` | 余量：任务段 `Spec.margin = TRACK_TOL`；锚点用实测值复核 |

规则：**计划按假设加余量，复核按实测、零余量**。这样复核不会比计划严：误差在余量以内，复核一定通过，原样执行；超出余量才重做。T17（漂移 2 mm，复核判碰，重做失败）就是计划没留余量、复核又按实测查。

余量还是重做：误差上限小、事先知道、加了余量也不会拒掉多少候选的（握法、漂移），用余量；误差让目标本身变了的（底盘偏了，同样的关节角就到不了目标），用重做。

### 8.3 复核和重做是同一个 `build`

锚点处 `run` 不另写判断，直接 `build(state, k, prior=plan, start=下一段)`：
- `build` 对每一段先看 `prior` 里同名的段还成立不成立（8.4），成立就原样返回。所以误差在余量以内时，返回的就是原来的计划，代价只是剩下各段的碰撞查询。
- 某段不成立就用原语重新做，决定先原样复用；它后面的段起点变了，也跟着重做。
- 两个锚点之间只复核下一段：世界没变，只有意外（被挡住、碰动了东西）才会让它不成立。

只有这一处触发重做。`skill_jobs/pick.py` 的 `_pick_ready`、`skill_jobs/place.py` 的 `_place_ready` 开头"重新测量的目标偏了 `HINT_REACH` 就整份重做"那一套要删掉：目标由 `build` 从 `State` 推出以后（第 6 节），到达锚点做的就是这件事，而且会复用旧决定。

### 8.4 复核 `holds`

`holds(kin, state, seg, target)`，`target` 是 `build` 从现在的 `State` 推出的这一段的目标：
- 手臂在这段的起点（`PLAN_AT_START`）；
- 路点在现在的世界里不碰：按这段的 `Spec`，含 `touch`，零余量；
- 终点：有位姿目标的段，在实测底盘下，终点的 TCP 离 `target` 不超过 `TARGET_TOL`。底盘误差、物体被碰动都在这里发现；
- 离开段：用 `contact_extent` 从当前姿态重量，长度和计划差超过一个步长就不成立；
- 任务段：用实测的部件值 / 物体位姿重查；
- 动作段总是成立；锚点不复核自己，它触发复核剩下的。

### 8.5 不预测的锚点

物体落点预测不了的地方（drop 之后、推完一段之后），锚点带 `predict=False`，计划在这里截止。搜索只证明锚点之前的部分；之后的段，执行时从实测状态用 `build` 做出来（没有 `prior`），做不出来技能失败。跨多个停车点的任务，每段之间是这种锚点（第 6 节接触类技能）。

### 8.6 执行和失败

`execute` 按种类分：`move` 交给 `follow`，持物时限速；`drive` 交给底盘；`scripted` 交给它的执行器；`action` 做对应动作；`anchor` 不动。每段都向接触监视声明 `seg.spec.allow`。这些都是 `Actuator` 的方法（2.5）：`execute` 和 `observe` 是 ④ 仅有的两处仿真副作用，而且只通过这个协议，不直接碰 `Rig`。

技能自己的判断挂在 hooks 上：伸入时盯物体、合爪后判断和登记持物、搬运后 `check_held`。hooks 只读状态、做判断、登记、写日志，**不动机器人，不改碰撞模型**。判失败以后要退出接触（没夹住、半路被挡），由技能给一个失败出口的 `build_clear(state)`（张手 + `contact_extent(near_world)` + `contact_segment`），`run` 执行它再抛 `SkillFailure`。现在 `_pick_ready` 的 `after_grasp` / `after_close` 在 hook 里直接调 `rig.grip` 和 `rig.leave`，要改（9.3 第 2.6 步）。

失败只有两类：
1. 计划做不出来（原语返回原因），包括锚点处重做不出来；
2. 仿真结果不对：被挡住停在半路、没夹住、物体没跟上来、闭环执行器偏出 `TRACK_TOL`。

意外接触只当指标。搬运中掉了，抛 `Dropped` 给上层。

### 8.7 旧入口

`Rig.move_to` 只留给还没迁移的技能，等于"一段 `free_leg` 的计划 + 执行"。过渡期的 `FREE_ELSE_STRAIGHT` 只在旧入口（`Rig.move_to`、`joint_path`、`move_left_to`）里起作用。每迁完一个技能，就少一个调用方。

### 8.8 外部产出的计划：`rebuild=None`

`Plan` / `Segment` 不该只有 `build` 能产出。`State` 是干净的快照、`Plan` 是干净的运动表示、`holds` + 接触监视是一套独立的校验，合起来意味着：**任何能产出 `Plan` 的东西，都能免费拿到碰撞复核、接触监视、持物限速和失败分类。** 外部策略（学出来的、别人写的）只要产出 `Plan`，`run` 就能执行并校验它；`find_park` 也能拿 `problem.build` 给它打分。

第 1 步以前 `run(rig, plan, rebuild, hooks)` 把 `rebuild` 当必需位置参数，而且 `holds` 不成立时无条件调用它——外部策略没有 `build`。9.3 第 1 步起 `run(act, plan, rebuild, hooks)` 里 `rebuild=None` 合法，含义是"不重做，不成立就按失败退出"：

```
why = holds(kin, state, seg)
if why is not None:
    if rebuild is None: -> SkillFailure（不重做）
    ...
```

`carry_posture` 已经这样用（它的计划是刚从现在的状态做的，不成立就失败）。有了它，④ 就从"pick / place 的执行器"变成"任意 `Plan` 的执行与校验器"，这是第 1 节第 3 条（没有 fallback）唯一合理的放宽方式：外部策略不会重做，但它也不会偷偷走不查碰撞的路。

配套的是 4.6：外部策略要观测，观测走 `Observation`，不进 `State`。

## 9. 现状和下一步

### 9.1 已实现

- 数据：`State`、`Hand`、`Held`、`Spec`（`allow`、`fingers`、`exempt`、`hold_tilt`、`touch`）、`Segment`（`move` / `action` / `drive` / `anchor`）、`Plan`、`Failure`，以及推进 `State` 的小函数；协议 `Actuator`、`BaseModel`（2.5）。
- 查询层：`Motion.query`（包一层）、`path_free_only`。
- 原语：`free_leg`（`Joint`、`Pose`、`PoseSet`、`JointSet`）、`straight`、`contact_extent`、`contact_segment`，三个"还在碰"判据，`exit_length`；`drive`、`drive_straight`（5.4）。
- 计划：`plan_pick`、`plan_place`、`set_down_length`；`HELD_POSE_MARGIN` 5 mm。
- 计划（续）：`plan_navigate`、`travel_chain`、`Carry`（`skill_plans/navigate.py`）。
- 第 ⑤ 层：`motion_skills`（`Skill`、`Job`、`run_skill`、`SKILLS` 从 `skill_library/catalog.json` 的 `motion_skills` 加载）；navigate、pick、place 走它，它们的 job 在 `zeno_skills/skill_jobs/`（`navigate`、`pick`、`place`，加上 `base` 的 `RigBase`、`carry` 的搬运判据）。
- 搜索：`park_search.find_park(kin, world, problem, state, log, base)`、`Problem`，pick / place 在用，微波炉里取物也是（cc2dbb2；写死的 `search_near` 和 `microwave_retrieval_q` 还在，9.3 第 8 步删）。
- 执行：`run.observe`、`holds`、`execute`、`run(act, plan, rebuild, hooks)`（`rebuild=None` 合法，8.8）；`skill_jobs.pick._pick_ready`、`skill_jobs.place._place_ready`。
- 单测：`tests/test_primitives.py`、`test_skill_plans.py`、`test_park_search.py`、`test_navigate_plan.py`、`test_layering.py`。
- 基线：v3 两个种子 140/170（11-08，`benchmark/runs/v3_sticky_gt_1108_2seeds`）。计划段 2045 段原样走、13 段执行时重做（2 段做不出来）。pick 搜索中位 8 s、p90 14 s；place 中位 16 s、p90 29 s。之后还没跑过的改动：`free_leg` 有 `q_hint` 时先走到它（空手也是），`_reach` 在碰撞模型里求伸入段 / 放下段起点（排序 IK 只当种子）。
- 静态审计（`tools/audit_collision.py`）暂停（开关文件 `.claude/audit_paused`）。恢复前要做：
  - 审计认识新原语和 `Spec(allow=...)`；
  - `run.py` 算执行入口，查询层可以写 `coll_kw`；`Actuator` 的实现（`Rig`）算执行入口，协议本身不算；
  - `find_park` 按顺序构造计划的循环不算重试；
  - 用 `--update-baseline --allow-increase` 更新基线，在同一次提交里删掉开关文件。

### 9.2 pick / place 还没解决的

| 问题 | 例子 | 第 8 节怎么解决 |
|---|---|---|
| 构造预算用完：收臂失败每次约 10 s | T06 s10、T01 s10 | 不涉及 |
| 重新测量后整份重做 place，做不出来 | T13 s10（倾角）、T20 s11（抽出没 IK） | 到达锚点重做，`q_p` 原样复用（8.3、5.7） |
| 持物 2 mm 漂移在严格复核下判碰、重做失败 | T17 s10 | 开车前的 place 计划带 `HOLD_DRIFT` 余量（8.2） |
| 持物去搬运姿态的规划慢（保持倾角按位姿规划单次 0.6–8.4 s） | 搜索耗时的大头 | 不涉及；锚点处重做要是常碰上它，会更慢（第 10 节） |
| 书还走旧 `place_flat`，翻书走旧 `FlipFlat` | T15 s10/s11 | 不涉及 |
| `physical`（不焊）下持物余量按实测偏差再定 | — | 就是 8.2 表里握法、漂移两行的数 |

同一个决定现在在几处做（违反第 1 节第 2 条）：

| 决定 | 唯一出处 | 现在的重复 | 怎么去掉 |
|---|---|---|---|
| 伸入段 / 放下段起点的分支 | `_reach` | 搜索和执行都走 `_reach`，但没有"原样复用"那一步 | `decide_ik`（5.7） |
| `q_p` 的分支 | `plan_place` | 搜索时 `q_seed = q_rank`，执行时重做和整份重做不带种子 | `decide_ik` + `prior` |
| 什么时候重做 | `run`（锚点 + `holds`） | `_pick_ready` / `_place_ready` 开头按 `HINT_REACH` 比较目标，偏了就整份重做，不带种子 | 目标从 `State` 推出，删掉开头那段（8.3） |
| TCP 到不到得了目标 | `holds` 的终点检查 | 没人查：底盘误差直接变成抓取 / 放下误差 | `holds` 加终点检查（8.4） |
| 搬运姿态 | `plan_pick` 的 `carry_in` | ~~navigate 和 place 之前又调旧的 `_carry_pose`~~ | 已去掉：`plan_navigate` 第 1 段按约束复核，满足就不动（9.3 第 1 步） |
| 开车时的行驶姿态 | `plan_navigate` | ~~搜索的 `_drivable` 和 `navigate` 给 `travel_postures` 的参数不同~~ | 已去掉：两边都取 `travel_chain`（9.3 第 1 步） |
| 失败后退出接触 | 失败出口的计划 | hook 里直接 `rig.grip` / `rig.leave` | `build_clear`（8.6） |

### 9.3 迁移顺序

按"覆盖多少 v6 路线步数、依赖谁"排（2.3 的表）：

1. **框架（第 ⑤ 层，已完成）**：`Skill`、`run_skill`、`drive`（包 `_base_plan` 和 `straight_base_move`）、`plan_navigate`；pick / place 改走 `run_skill`。分五次提交：
   1. 只换结构、行为不变：`skill_plans.py` 拆成 `skill_plans/` 包（9.4），`Actuator` 协议抽出来、④ 只对着它编程（2.5），加 import 图单测守住 ①② 不碰 `rig`，`find_park` 改成 `(kin, world, problem, state, log)`；`motion_signature --compare` 无差异；
   2. `SKILLS` 进 catalog（2.3）：pick / place 两条先进去，加载器 + schema 校验；
   3. `plan_navigate` 第 1 段按约束复核持物姿态，不满足才用 `FREE` 规划；删 `_carry_pose`、`carry_pose_kept` 和它的 `FREE_ELSE_STRAIGHT`（11-08 的 T07 ×2 失败出在这里）；
   4. `_drivable` 和 `plan_navigate` 用同一组行驶姿态；
   5. `drive` 包住两个底盘入口。
   
   navigate 一项就覆盖 1099 步。（原文说"四件事都是零行为改动"不对：1.3、1.4 本来就改行为，只有 1.1、1.2、1.5 是零行为。）

   **已完成（11-08，afaef2d、79f5ed5、f6d16de、2c600bc）。** 五项合成一次提交：它们都经过 `skills.py` 的 navigate / pick / place，拆开的中间状态跑不起来。和计划的出入：`find_park` 多一个参数 `base`（2.5）；协议方法叫 `arm_kin`；`run_skill` 的技能接口是过渡形式 `Job`（2.3）；`min_bottom_z` 是"能抬就抬"不是约束（第 6 节）。catalog 在 `skill_library/catalog.json`（经生成器，第 10 节），job 在 `skill_jobs/`，`skills.py` 2281 行（9.4）。
   验证（只跑针对性，v6 nominal，未跑全量）：单测 260 + benchmark 69 通过。v6 nominal 10 集（T02 s10/s11、T04、T06、T07、T10、T20、T21、T23、T29，后八个 s10）中 6 集成功（T02×2、T04、T07、T10、T20）。失败的 4 集在第 1 步之前的 38bc6e0 上同样失败、失败点相同：T06 / T29 的 face 原地转身判碰（11% 处 0 mm、67% 处 6 mm），T21 "slide to edge: no graspable free edge"，T23 place 找不到停车点；T07 在 38bc6e0 上失败（heat 的按钮没有 IK），第 1 步上成功。搬运姿态全部"保持"，没有多余的手臂动作；运动记录里 fallback 为 0。`motion_signature --compare`：(a) 第 1 步对 38bc6e0，同 5 集——新增的只有 T07 走得更远的 heat 按钮两行，少掉的是 4 行 `tuck`（旧 navigate 每次都调 `Rig.tuck`，手臂已在收起位也记一段零长度运动；`plan_navigate` 已在就省掉），都是 1.3 要的行为改动；(b) job 搬出 `skills.py`（2c600bc，零行为）前后，T02 s11、T04、T07 三集：无差异。结果在 `benchmark/runs/v6_step1_1108`、`v6_step1_carry_1108`（新）和 `v6_step1_old_1108`（38bc6e0）。
2. **pick / place 收尾**，每项单独提交：
   1. 先只记录不改行为：到达、握上、落下时的实测偏差（底盘、握法、漂移、终点 TCP 离目标多远）写进日志，跑一次定 `BASE_TOL`、`HOLD_DRIFT`、`TARGET_TOL`；同一次提交里建 `tolerances.py`（4.5），把四处散落的阈值搬进去、补上来源标记；
   2. `decide_ik`、`Plan.decisions`、`build` 的 `prior`（取代 `plan_pick` / `plan_place` 的 `q_seed` 和 `build` 的 `q_rank` 参数；`free_leg` 的 `Pose.q_hint` 不变，它是定下的分支）；
   3. 目标从 `State` 推出（pick 的抓取候选放在物体框里，place 的目标是物体位姿），删 `_pick_ready` / `_place_ready` 开头的整份重做；
   4. 锚点段、`holds` 的终点检查、`run` 在锚点复核剩下的整份；
   5. 余量：place 计划带 `HOLD_DRIFT`；
   6. hooks 不动机器人：`build_clear`（`run` 的 `rebuild=None` 第 1 步已做，8.8）；
   7. 9.2 第一张表里剩下的：收臂预算、搬运慢、书进 `plan_place`（删 `place_flat`）。
3. **感知类**：look、search、explore_furniture / explore_room、inspect、measure、identify、count。navigate + 头部动作，只依赖第 1 步。
4. **取放家族**：drop、stack、lift、hover、cover、present；collect 在任务层串。在 `plan_pick` / `plan_place` 上换目标集合。
5. **姿态类**：`Spec.joints` + 拆 `q_body`（`JointSet` 第 1 步已加）（`joints` 按关节名写，不按 `q_right` 的下标）。bend / straighten、升降躯干、wave、nod；删改 `kin.lo / hi` 和 `_lock_shared_posture` 的地方。
6. **部件类 + retreat**：`scripted` + `Held(kind="part")` + `touch` 扩到部件和部位。开关门，`_ride` 变成闭环执行器，删 `hand_touches_part`；retreat 用直线 `drive`。
7. **接触类**：按 v6 用量排，依次是 stir、wipe、roll / flip、expose、press / touch、push、sweep、pour。先加 `tool_frame` 标注和它的解析（第 6 节接触类技能），再迁第一个技能，否则 9 个技能各写一遍换算。删 `LEGACY` 直线和"到不了的点跳过"。
8. **微波炉和电器动作**：`drive_part`、`toggle`、电机开门前让开的检查。删写死的底盘位置（`search_near`）和 `microwave_retrieval_q`。
9. **左臂和两臂**：两手搬的物体进碰撞模型（闭链约束另议）；`q_body` 已在第 5 步拆好。
10. **收尾**：删 `Rig.move_to` / `move_to_any` / `joint_path` / `move_left_to` / `leave`、旧的 `planner.find_park`；`Motion.query` 改成直接实现。

每步单独提交，先针对性检查再全量。

**只降不升的计数**：恢复静态审计（9.1）时，让它数 `run.py` 和原语执行器以外直接调旧运动入口的地方（`move_to`、`move_to_any`、`joint_path`、`move_left_to`、`follow`、`leave`、`swing`、`drive_base`、`tuck`、`straight_base_move`、`relocate`、`navigate`）。11-08 粗数约 190 处；第 1 步之后 180 处（`skills.py` 39、`hand.py` 17、`tooluse.py` 17、`extra.py` 15、`orientation.py` 14、`bimanual.py` 14……；粗数含注释里的，要按审计重数）。每步迁移必须让它下降，第 10 步到 0。每个新 `build` 有 FakeKin 单测（`tests/test_skill_plans.py` 的写法）。

### 9.4 代码放哪

`skills.py` 第 1 步以前 2666 行 114 个函数，第 1 步之后 2284 行 104 个函数（job 搬进了 `skill_jobs/`）；`policies/` 另有 5391 行。迁移有 10 步，如果新的 `Skill` / `build` 继续往 `skills.py` 里加、旧的又注释着不删（bd55037 / cc2dbb2 对 pick / place 就是这么做的），它会长期背着一大坨注释掉的死代码，同时还在变长。

规则：

| 放什么 | 放哪 |
|---|---|
| `build`（第 ② 层） | `skill_plans/` 包，**按 2.3 的形状分文件**：`pick.py`、`place.py`、`navigate.py`、`door.py`、`contact.py`、`posture.py`，共用部分在 `_common.py` |
| `Skill` 的数据部分 | `skill_library/catalog.json` 的 `motion_skills`，出处是 `tools/build_skill_library.py` 的 `MOTION_SKILLS`（2.3） |
| `Skill` 的代码部分里不碰 rig 的（轨迹函数 `traj`） | 和它的 `build` 同一个文件 |
| `Skill` 的 `job`（目标采样、hooks、结果判断：要读 rig 的标注和状态，属第 ⑤ 层）、`RigBase` | `zeno_skills/skill_jobs/`，一个技能一个文件。不能放进 `skill_plans/`（它不许碰 rig），也不放 `skills.py`（只减不增：第 1 步之后 2281 行，之前 2666 行） |
| 阈值常数 | `tolerances.py`（4.5） |
| `Actuator` 协议 | `motion_state.py`（和 `State` / `Spec` 一起，它也是层间接口） |
| 退役的旧实现 | **删掉**，靠 git 回退，不靠注释保留 |

`skills.py` 立下规矩：**只减不增**。bd55037 / cc2dbb2 注释掉的 pick / place 死代码，在 9.3 第 2 步收尾时删。这样"只降不升的计数"还能按文件看出每一步的进度，而不是只看一个总数。

## 10. 待定

| 问题 | 倾向 |
|---|---|
| 搜索第 3 步的批量 IK（不查碰撞，排序 + 当 `prior`）要不要 | 先留；量排序准不准，不准就去掉。去掉后 `decide_ik` 只是少一个种子，手臂质量从做好的计划里算 |
| 构造预算 | 按时间（`BUILD_S` 20 s）；收臂失败太慢的问题先解决，再看要不要调 |
| 持物去搬运姿态太慢 | 调小保持倾角规划的尝试次数，或让搬运目标优先选关节直走不倾斜超标的 |
| `BASE_TOL`、`HOLD_DRIFT`、`TARGET_TOL` 的值 | 9.3 第 2.1 步先记录实测偏差再定；`TARGET_TOL` 按抓取能容忍的偏差定，不按底盘误差定 |
| 底盘误差用重做还是余量 | 重做（8.2）。要是到达锚点几乎每次都重做，而且重做常碰上慢的搬运段规划，再考虑给 `free_leg` 加余量 |
| 锚点处重做做不出来，要不要换停车点再找一次 | 倾向任务层最多再找一次：约束不变，不算 fallback；要先看 9.3 第 2.1 步的记录里这种情况有多少 |
| 锚点处单独复核剩下的整份要多久 | 预计只是碰撞查询（各段 `path_free`），9.3 第 2.4 步做完时量 |
| 闭环执行器的 `TRACK_TOL` | 做开门时按 `_ride` 实测偏差定 |
| 开门：手臂走圆弧还是底盘带门 | 两种都作为目标集合里的做法，由搜索挑 |
| 力的几何替身够不够 | 先够；不够再加力反馈 |
| 两手搬的闭链 | 9.3 第 9 步再定 |
| ~~`SKILLS` 的 catalog 是独立一份还是并进 `skill_library/catalog.json`~~ | 定了：并进去，作为 `motion_skills` 块；因为 catalog 是生成的，数据放在生成器的 `MOTION_SKILLS` 里（9.3 第 1 步） |
| `Observation`（4.6）什么时候做 | 没有使用方就不做。第一个要接的外部策略出现时再定它的形状，现在只守住"不塞进 `State`" |
| 路线里 navigate(x) 选一次底盘位置，后面的技能又选一次停车点 | 两者目的不同：navigate 只开到 x 那一带，停车点由技能定，接受。另一种是 navigate(x) 后面紧跟技能时不动，会改路线语义 |
| 复合技能（drop、heat、collect）放在哪一层 | 任务层串几个 `run_skill`，每个子技能各有锚点。做成一个大 `build` 搜索时能往后看得更远，但计划长、重做范围大 |
