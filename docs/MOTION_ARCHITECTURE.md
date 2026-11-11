# 运动规划的分层设计

## 1. 规则

1. 每个技能只给必要的中继位姿（停车点、伸入段起点、抓取位姿、搬运姿态、把手前、任务轨迹起点、收臂姿态）。中继位姿之间的自由空间运动由规划器生成，不写中间路点、不写变体列表。
2. 每个决定只有一个出处：技能的 `build`。停车点搜索和执行用同一个 `build`、同样的约束；执行照搜索做出的计划走，要重做也只用这个 `build`。别处只能做两件事：比 `build` 宽松的预筛（只用来排除候选），或者用和计划时同一套判据复核已有的计划（第 8 节）。
3. 没有 fallback：计划做不出来，搜索时不要这个停车点，执行时技能失败。不改走不查碰撞的路，不跳过某段，不缩短重试。同样约束下换一种做法（`free_leg` 的直线 → 关节规划 → 位姿规划）或换目标集合里的另一个目标，不算 fallback。
4. 接触段：方向由任务定，长度由碰撞模型量，允许碰什么用 `Spec.touch` / `Allow` 写明。
5. 持物：手指和手里的物体都在碰撞模型里；要保持倾角时保持，限速。
6. 每段向接触监视声明 `Allow`，意外接触只记指标。
7. 一次只迁一块：每步单独提交，先针对性检查再全量，基线变化分得清来源。
8. 决定早做，轨迹晚做（第 8.1 节）：把几段绑在一起的决定（停车点、目标组、接触位姿的 IK 分支、搬运目标）在搜索时做（收臂姿态是计划最后一段，不绑别的段，每次构造都按"收起优先"重新选），做的时候往后看完整份计划；轨迹（过渡段的路径、接触直线的路点）在执行时可以从实测状态沿已定的分支重新生成。
9. 误差分三层处理（第 8.2、8.3 节）：计划按假设加余量；误差进来的时刻（锚点）复核，复核按实测状态、零余量，通过就原样执行；超出余量就从这里用同一个 `build` 重做到底，旧决定先原样复用，不行再当种子；还做不出来，技能失败。
10. 依赖只能向下（第 2.5 节）：原语和 `build` 不碰 `rig`，停车点搜索只用 `kin` / `world` / `state` / `log` 和传进来的 `base`（`BaseModel`），仿真副作用全在 `run` 的 `observe` 和 `execute` 里，且只通过 `Actuator`。阈值常数只有一处出处（第 4.5 节）。

## 2. 分层

**读法**：第 2–8 节写的是目标设计。标〔待加〕的还没有实现（在 9.3 的哪一步做写在旁边），没标的是现在代码里的样子；逐项的现状见 9.1。

| 层 | 在哪 | 负责 | 不负责 |
|---|---|---|---|
| ① 运动原语 | `primitives.py` | 从给定 `State` 和关节角出发生成一段运动（`Segment`），做不出来返回 `Failure(why)`；要做决定的（`decide_ik`）先试给它的旧决定；判断一段已有的运动在给定 `State` 里是否还成立（`holds`，8.4：`run` 和复用 `prior` 的段的 `build` 都用它） | 不知道是哪个技能，不知道是搜索还是执行 |
| ② 技能计划（`build`） | `skill_plans/`（按形状分文件，9.4） | 按技能顺序把原语和动作串成 `Plan`，每段从上一段的实际终点出发，动作之间用小函数推进 `State`；目标从 `State` 推出（`motion_state.Aim` / `aim_pose`，第 6 节）；`prior` 里还成立的运动段原样拿来（`_kept`），其余的先试 `prior` 的决定（接触位姿的解、目标集合的选择） | 不选停车点，不执行 |
| ③ 停车点搜索（`find_park`） | `park_search.py` | 底盘候选、批量便宜过滤、排序，按顺序调用 `build`，返回（停车点，目标组，计划） | 手臂运动细节 |
| ④ 执行（`run`） | `run.py` | 每段前复核这一段，到锚点复核剩下的整份；不成立就用 `build` 重做剩下的；执行，读回状态，监视，日志 | 发明运动，另写判断 |
| ⑤ 技能（`Skill` + `run_skill`） | 每个技能一份 `Skill`；`run_skill` 一个 | 技能参数 → 目标集合、`build`、hooks、失败出口；`run_skill` 依次调 ③、开车、④ | 运动细节、重做判断（都在 ①–④） |

层之间只传三种数据：`State`（机器人和世界现在的样子，或者假设的样子）、`Spec`（这一段按什么规则查碰撞）、`Segment` / `Plan`（运动本身）。

### 2.1 搜索和执行都只通过 `build` 碰原语

复核和重做是同一次调用（第 8.3 节）：

```
find_park                                        run（锚点，或某段不成立）
 └─ build(state_at(park), k, prior=排序 IK)        └─ build(当前状态, k, prior=当前计划, start=这一段)
      ├─ free_leg / straight / drive                    └─ 同样的原语；prior 里还成立的段原样返回
      ├─ decide_ik（5.7）
      ├─ contact_extent / contact_segment
      └─ scripted（5.5）
```

签名：搜索调 `build(s, k, prior)`，`prior = {problem.relay: 排序 IK 解}`（只有决定，没有段可复用）；执行时 `rebuild(state, 段名, prior)`，`prior` 是 `run` 手上当前的计划（段和 `decisions`），由 job 包住同一个 `plan_pick` / `plan_place` / `plan_navigate`（catalog 的 `template`，2.3）。

### 2.2 一个技能从头到尾：pick

```
PickPolicy.execute
└─ run_skill(rig, SKILLS["pick"], args)                     ⑤
   ├─ skill.problem(rig, args, state)                        目标集合：抓取候选（物体框里）
   │    = Problem(goals, build=plan_pick, relay=PICK_RELAY, arrive=收起, travel=收起, near=当前位置)
   ├─ find_park(kin, world, problem, state, log, base)       ③
   │    ├─ 底盘候选 → 预筛（够得着、底盘柱体、行驶姿态整机、开得到）
   │    ├─ rank_ik：批量运动学 IK，排序，结果当 prior
   │    └─ 按顺序 plan_pick(state_at(park), k, prior)        ②
   │         ├─ 到达                   锚点（pick_arrive）
   │         ├─ 张手                   动作，State 手张到候选宽度
   │         ├─ decide_ik → free_leg    ① 到伸入段起点
   │         ├─ straight                ① 伸入
   │         ├─ 合爪                   动作，State 记上持物
   │         ├─ 握上                   锚点（pick_held）
   │         ├─ contact_extent + contact_segment   ① 抬起
   │         └─ free_leg(PoseSet)       ① 去搬运姿态
   │       → Found(停车点, k, plan)
   ├─ 不在停车点：run(plan_navigate(...))                    开车（2.3）
   └─ run(act, plan, plan_pick, skill.hooks)                 ④
        锚点：plan_pick(prior=plan, start=下一段) 复核剩下的整份；其余每段 holds；
        不成立就 plan_pick(prior=plan, start=这一段)；hook 判失败就跑失败出口（8.6）
```

`plan_pick` 只有一个：搜索时用它证明"在这个停车点能做完"，执行时用它复核、从当前状态重做剩下的。

`PICK_STAGES` 是 8 段（`pick_arrive`、`pick_open`、`pick_reach`、`pick_grasp`、`pick_close`、`pick_held`、`pick_lift`、`carry_in`），两个锚点（`PICK_ANCHORS`）；`PLACE_STAGES` 也是 8 段，锚点 `place_arrive`、`place_landed`（`PLACE_ANCHORS`）。`plan_navigate` 末尾的 `arrive` 锚点后面没有段，`run` 在那里不复核什么。

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
2. 要选停车点的，`find_park`（`travel` / `arrive` 姿态取 catalog 的；在现在的位置上，手臂就是现在的样子）；不选的（姿态类、感知类的头部动作），只在原地 `build`，停车点就是现在的位置；
3. 不在停车点，就构造并执行 navigate 的计划（`plan_navigate`，第 6 节）；离停车点在 `AT_PARK_M` / `AT_PARK_DEG`（2 cm / 2°）以内、不开车的，用同一个 `build` 在现在的底盘位置重做一次计划（`park_here`，找到的计划当 `prior`：接触位姿段的终点在这个底盘下没多偏的原样留下——pick 按 `PICK_TOL` 1 mm、place 按 `PLACE_TOL` 5 mm，8.4——其余重做），做不出来就开过去；
4. `run(rig, plan, problem.build, skill.hooks)`（`rig` 就是 `Actuator`）；hook 判失败时执行 `build_clear` 再抛 `SkillFailure`。

`AtomicPolicy.execute` 只剩 `run_skill(self.rig, SKILLS[name], args)`。迁一个技能 = 给它写 `problem`（目标集合）和 `build`（尽量用下表的模板），hooks 照搬，然后不再调旧入口。

**过渡形式（`zeno_skills/motion_skills.py`）**：技能的 Python 部分是一个 `job(rig, args, state, skill) -> Job`（`skill.build` 是 catalog 的 `template`，job 用它构造计划），`Job` 按 `run_skill` 的步骤给回调：`problem`（没有就原地做，如 navigate）、`no_park(diag)`、`found(found)`（日志）、`travel`（开到停车点时给 navigate 的参数，如 `min_bottom_z`）、`ready(found) -> (plan, build, hooks)`（只交出找到的计划、重做用的 `build` 和 hooks，不重新测量、不重做）、`failed(exc)`、`done()`。日志和结果判断挪走以后，`Job` 收缩成上面的三样。现在走 `run_skill` 的是 navigate、pick、place；它们的 policy 照旧调 `skills.navigate / pick / place`，这三个函数内部转到 `run_skill`。

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

**`SKILLS` 是数据，不是 Python 字典。** 上表 7 个形状覆盖约 40 个技能，彼此的差别在数据里是：用哪个 `build` 模板、选不选停车点、`arrive` / `travel` 姿态（将来加几个 `Spec` 常数）；代码部分是 `job`（目标采样、hooks、失败出口）和轨迹函数 `traj`。这些字段都是实际起作用的：`template` → `Skill.build`，job 拿它构造计划；`park` → 有没有停车点搜索；`arrive` / `travel` → `run_skill` 交给 `find_park` 的两个姿态（`motion_skills.posture`：`fold` = `kin.rest`，`carry` = 现在手里拿着东西的姿态，`fold_or_carry` 看手里有没有东西）。不选停车点的技能（navigate）写的是它自己的计划实际用的姿态（`travel_chain`），没人读；`shape` 是上表的行，给覆盖率统计用。数据写进 `skill_library/catalog.json` 的 `motion_skills` 块（schema 1，每条带同一动词的 SkillNode 的 `skill_id`）。那份索引是 `tools/build_skill_library.py` 生成的，所以数据的出处是生成器里的 `MOTION_SKILLS`，手改 catalog 会被下次生成覆盖；生成器顺带检查每条都有同名动词的 SkillNode。`motion_skills.load` 加载时逐条校验（字段和类型、形状、姿态、模板是 `skill_plans` 里的构造函数、`job` 能 import），`SKILLS[name]` 第一次用时组装。

这样做的理由：
- 覆盖率、静态审计、v6 步数统计可以直接读 catalog，不用解析 Python，也不会再出现"文档说 116 个策略、代码里是另一个数"；
- 接新任务的新 policy，和已有技能同形状时，`build`、姿态、选不选停车点都是一行数据，要写的只有 job（目标采样、hooks、结果判断），不是一个新类；
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

"整段不查"只在几何完全由两端决定、中间是单调插值时成立：抽屉直线接近这种（纯平移，手臂锁住时中间不冒出新碰撞），铰链圆弧不是（门板扫出一片扇形）。另外整段不查的话，闭环执行器"照计划的函数跟、不改几何"的规则也失去依据——它成立的前提正是计划里的构型被证明过安全。

### 2.5 依赖方向：`Actuator` 和 rig-free（第 1 节第 10 条）

各层对 `Rig` 的依赖：

| 层 | `rig.` 引用 | 规则 |
|---|---|---|
| ① `primitives.py` | 0 | 不许 import `rig`。只认 `kin`（`kinematics.ArmKin`，含 `kin.motion`）、`State`、`Spec`；底盘段另认传进来的 `base`（`BaseModel`） |
| ② `skill_plans/` | 0 | 同上 |
| ③ `park_search.py` | 0 | `find_park(kin, world, problem, state, log, base)`：整机在行驶姿态下的深度、底盘可达场、开得到，都问传进来的 `base` |
| ④ `run.py` | 0，也不 import `rig`（`SkillFailure` / `Dropped` 在 `motion_state`，`rig` 照旧导出） | 仿真副作用只在 `observe` 和 `execute` 里，且只通过 `Actuator` |
| ⑤ `Skill` + `run_skill` | 允许 | 绑定层：技能参数、标注、当前状态都要从 `rig` 来 |

这个形状由 `tests/test_layering.py` 守住：①②③ 和 `run.py` 的 import 图（模块级和函数内的都算）不出现 `rig`、`skills`、`planner`、`motion_skills`；`run.py` 只调 `act.` 的协议方法，传的关键字协议里都有；`Rig` 的方法收得下协议写的每个参数（`follow` 的 `side` 原来协议里没写）；`Rig` 没有和协议方法同名的实例属性（`Rig.arm` 是关节下标张量，第一版的 `Actuator.arm` 就被它遮住了，所以叫 `arm_kin`）。

"不碰 rig" 是 import 层面的：真实的碰撞后端 `kin.motion`（`Motion`）手里有 `rig`，`Motion.query` 读 `rig.held` 来撤掉同步时挂上的持物、换成 `State` 里的。结果只由 `State` 决定，但后端不是 rig-free 的；①②③ 能脱离 Isaac 跑靠的是 FakeKin 这类后端。

底盘的整机模型（球模型、`base_planner`）现在靠 `Rig` 读手里物体的位置，做不到 rig-free。做法和 `kin` 一样：协议 `motion_state.BaseModel`（`plan` / `straight` / `depths` / `reachable` / `drivable` / `clear`），由 `skill_jobs/base.py` 的 `RigBase` 在 rig 上实现，作为参数传给 ① 的 `drive` / `drive_straight` 和 ③ 的 `find_park`。它从"机器人现在的样子"规划（`state` 是现在的状态，或者现在的状态换了手臂姿态），换机器人时要重写的是它和 `Actuator`。

`Actuator` 是 ④ 唯一能碰的仿真接口：

```
Actuator:
  # 写：execute 用
  follow(qs, steps_per_wp, smooth, side)   # 手臂路点，持物时限速；side="left" 是左臂
  ride(part, base_at, s_from, s_to, label, lead, rate, done)   # 底盘带部件的任务段的闭环：底盘在 base_at(指令值)，指令跟着实测部件值（5.5）
  grip(width, steps, gradual)
  drive_base(path, **kw)               # 底盘沿路点（allow、速度）
  swing(q_right, q_left, label)        # 两臂同时关节直线到行驶姿态（底盘规划器定的换姿态）
  declare(name, allow, side, follows)  # 向接触监视声明这一段（rig.clear.motion）
  contact_allow(kin, allow)            # 从接触出发时，按现在碰着什么收紧 Allow
  wait(ticks)                          # 什么都不动，让世界停稳若干物理步
  # 读：observe 用，拼出一个 State（4.1）
  snapshot() -> State                  # sync_world + 底盘 + 指令关节角 + 头 + 手指宽度 + 握法
                                       # （实测关节角下的 TCP，4.1）+ 物体框 + 部件值
  arm_kin(side) -> ArmKin              # 不叫 kin / arm：Rig.kin 是右臂对象，Rig.arm 是关节下标
  log(label, **kw)
```

`Rig` 实现它。`run.observe` 就是 `act.snapshot()`：拼 `State` 的逻辑属于"这个机器人怎么报告自己的状态"，换机器人时要重写的正是这一个方法。

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
    T_tcp_obj: np.ndarray        # 物体框（部件：把手）在 TCP 里的位姿：实测（实测关节角下的 TCP），或计划里假设的
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
- `Held.T_tcp_obj` 是"手里的东西在 TCP 里的位姿"的唯一表示。实测的握法按**实测**关节角下的 TCP 量（`Rig.snapshot`，8.2）：焊住（sticky）时它不随姿态、下垂、接触顶偏而变，不焊（physical）时变的就是手里真的滑动，两种模式同一个口径。工具的工作点（勺尖、海绵底面）是它的直接延伸：`T_tcp_tool = T_tcp_obj · T_obj_tool`，其中 `T_obj_tool` 是标注里的 `tool_frame`（第 6 节接触类技能）。
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

- `touch` 的每一项写成（名字，部位），部位是 `fingers` / `hand` / `load`：手指碰刚放下的物体，手碰门板，持物碰锅或台面。`Allow` 的允许接触由 `touch` 推出，不另写一份。现在实现了 `fingers` 和 `hand`（`motion_state.touch_entries`：只写名字 = 手指），名字是物体或部件（`Motion.touch_owner`：先找物体，再找部件）；手握着的部件（`Held(kind="part")`）不用写进 `touch`，`motion_state.touches` 把它按 `PART_HOLD`（手指）加进去，`Motion.query` 和 `primitives.free_path` 用同一份。`load` 和"`Allow` 由 `touch` 推出"还没做。
- `hold_tilt` 保持的是起点倾角。倾角要变（勺子倾进锅、翻书），就在任务段里变，或者在 `hold_tilt=False` 的过渡段里变（持物照样查碰撞）。
- `joints` 取代改 `kin.lo / kin.hi` 和 `_lock_shared_posture`：只动腰、锁腰、左手持物时压腰都用它表达。
- `margin` 只在计划时用（`Kinematics.near(q, margin)` 判碰）；复核用实测状态、零余量（第 8.2 节）。现在唯一的余量是持物的 `Held.pad`；`margin` 留给任务段：底盘带门时门比底盘慢最多约一个 `lead`，手和门的相对位置跟着变，意外接触报告里出现手臂蹭门板再按 `ride_end` 的落后量定。
- 执行参数（速度、`smooth`、`steps_per_wp`）放在 `Segment.info`，不进 `Spec`。

### 4.3 `Segment` 和 `Plan`

- `Segment`：名字（`pick_grasp`、`carry_in`…）、`Spec`、起点关节角 `q_from`、路点 `qs`、种类 `kind`、这段的目标 `target`（位姿或关节角，复核用）、动作 `action`、原语量出或选出的东西 `info`（长度、做法、方向 u、判据名）。
- `kind`：`move`（手臂路点）、`drive`（底盘路径，手臂不动）、`scripted`（任务段：轨迹函数 `Script` 加执行器名，见 5.5）、`action`（不动手臂：`grip`、`wait`、`drive_part`、`toggle`）、`anchor`（锚点：误差进来的时刻，读回状态、复核剩下的计划，见 8.2；〔待加，9.3 第 2.1 步：`info` 记这一刻计划假设的值，日志里记实测偏差〕）。
- 接触位姿所在的段（`pick_reach`、`pick_grasp`、`place_reach`、`place_down`）的 `info` 另记 `aim`（`motion_state.Aim`：目标怎么从 `State` 推出）、`aimed`（建这段时推出的位姿）、`end`（建这段时终点的 TCP）、`tol`（终点比建时多偏多少还算成立：`PICK_TOL` / `PLACE_TOL`），由 `skill_plans._common._aimed` 填，`holds` 复核（8.4）。
- `Plan`：段的元组、服务的目标组 `goal`（现在没人填，目标组在 `Found.k`）、决定 `decisions`、构造耗时 `info["stage_s"]`（`plan_pick`、`plan_place` 都填，失败时在 `Failure.info` 里）。
- `Plan.decisions`：{名字: 值}，`build` 做的、把几段绑在一起的决定（8.1），名字就是段名：接触位姿的关节角，记的是计划实际走到的解（`pick_reach` 是伸入段起点的解 = `pick_reach` 段的终点，`place_reach` 是放下位姿的解 = `place_down` 段的终点）——不是 `decide_ik` 给 `free_leg` 的解：TCP 直线走得通时腿停在直线自己的解上，后面的段从那里做（约一半的伸入段起点和放下段起点是这样）；搬运目标的选择（`carry_in`），记 (序号, 集合大小)；收臂姿态不算决定：它是最后一段，不绑别的段，每次构造按 `JointSet` 的顺序（收起优先）重新选，也不作为段复用。重做时作为 `prior` 传回 `build`（`motion_state.decisions_of` 把 `Plan` 或 {名字: 值} 统一成字典）；目标集合的选择经 `free_leg(first=)` 复用：集合大小一样（从 `State` 做出来的集合会随状态变样：`skills._carry_goals` 每个点 2 层或 3 层高度，同一个序号就是另一个目标）、那个目标还够得着（`PoseSet`）/ 还不碰（`JointSet`）就用它，否则重新选。
- `Failure(why, segment, info)`：原语或计划做不出来的原因。搜索按类计数，技能用它报错。

### 4.4 碰撞查询层 `Motion.query(state, spec)`

`Motion.query` 把 `State` + `Spec` 翻译成一次 cuRobo 查询：
- 锁定底盘、另一只手臂、头和手指宽度；
- 把手里的东西挂到夹爪上（`pad` 放大），握着的部件对那只手不算障碍物；
- 把 `objects` 和 `parts` 同步到碰撞世界；
- 按 `Spec` 开关手指碰撞球、目标豁免、`touch`。

退出时全部复原。现在是包一层：内部调旧的上下文管理器（`_planning`、`_fingers_checked`、`_carrying` 等）。全部技能迁完后改成直接实现。`touch` 的"其余部位照查"由 `Motion.path_free_only` / `Kinematics.path_free_only` 另查一遍，`primitives.free_path` 把两次查询合起来。

### 4.5 阈值常数：一处出处（`tolerances.py`，待加）

现在散在十来个文件加一份文档：

| 在哪 | 有什么 |
|---|---|
| `rig.py` 顶部 | 约 20 个：`BIG_SWING`、`CARRY_VEL`、`RIM_VEL`、`SETTLE_*`、`DRIVE_*`、`HELD_CHECK_EVERY`（inherited, unmeasured）…… |
| `primitives.py`（复核） | `PLAN_AT_START`、`EXTENT_TOL`、`TARGET_TOL`、`TARGET_TURN`（`holds` 的判据） |
| `primitives.py` | 9 个：`LEAVE_GAP`、`LEAVE_MARGIN`、`LEAVE_MAX`、`ON_LINE`、`ON_LINE_TURN`、`JOINT_GOAL_TOL`、`DENSE`、`HINT_REACH`、`HINT_TURN`（`rig.py` 再导出后两个） |
| `kinematics.py` | `REST_TOL`、`STOWED_TOL`、`CARRY_TILT` |
| `skills.py` | `CARRY_Z`、`PICK_REACH_TOL`（= `TARGET_TOL`）、`APPROACH_STEP`、`PICK_LEAVE_CHECK`、`AT_PARK_M` / `AT_PARK_DEG`（inherited, unmeasured）、`CARRY_SPOTS`、`PLACE_*` 代价…… |
| `skill_plans/` | `HELD_POSE_MARGIN`、`PICK_TOL`（= `HINT_REACH` / `HINT_TURN`，`pick.py`）、`PLACE_TOL`（= `TARGET_TOL` / `TARGET_TURN`，`place.py`）、`SETTLE_TICKS`（`place.py`）、`SAME_POSTURE`（`navigate.py`） |
| `skill_jobs/` | `CARRY_FRONT_X/Y`、`CARRY_LOW_TOL`、`CARRY_LOW_COST`（`carry.py`）、`PICK_CAND_COST`、`FRONT_SEED_M`（`pick.py`） |
| `park_search.py` | `RADII`、`YAW_OFFSETS`、`REACH_XY`、`MAX_PER_GOAL`、`BUILD_S`、`BUILD_MAX`…… |
| `base_planner.py`、`collision.py` | `DEPTH_TOL`、`FOOTPRINT_MARGIN`（inherited, unmeasured）…… |
| `COLLISION_PLAN.md` 第 8 节 | 力的几何替身（`PRESS_DEPTH`、`WIPE_PRESS`、`TOUCH_DEPTH`……） |
| 还没有 | `BASE_TOL`、`HOLD_DRIFT`、任务段的余量（8.2）；`TARGET_TOL` 5 mm、`PICK_TOL` 1 mm 都没有实测（8.4） |

目标：新架构用到的阈值集中到 `tolerances.py`，按**属于哪一层 / 哪一类误差**分组，每个带单位和**来源标记**：

```python
# 误差上限（8.2 的锚点表）
BASE_TOL    = Tol(0.007, "m",   src="估：COLLISION_PLAN 第 8 节，没细测")
HOLD_DRIFT  = Tol(None,  "m",   src="待测：9.3 第 2.1 步")
TARGET_TOL  = Tol(0.005, "m",   src="定：执行后判被挡住的 PICK_REACH_TOL；没实测")
PICK_TOL    = Tol(0.001, "m",   src="定：decide_ik 的 HINT_REACH，pick 是一串精细动作；没实测")
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

做完推进 `State.base`。路径是轨迹（8.1）：搜索时只证明开得到，执行时由 navigate 的计划用同一个函数、同一组行驶姿态重新规划。技能自己的计划不含 `drive`，从停车点开始，第一段是到达锚点；任务过程中要动底盘的（开门时底盘跟着门、推一段），是 `scripted` 段的 `carry="base"`：底盘位姿是任务量的函数（`ride_base`，5.5），不是 `drive`。

### 5.5 `scripted`：任务段（框架已加，9.3 第 6 步；还没有技能用）

任务段的出处是技能的轨迹函数 `traj`（2.3、9.4：和它的 `build` 同一个文件）。它给出的是**函数和区间**（3.1），不是一串路点：`traj(state, params) -> Script`。

```python
Script(coupling, s0, s1, step, tcp=None, carry="base" | "arm")      # primitives.py
```

- `s0` → `s1`：任务量的区间（铰链角、抽屉位移、画圈相位……），第 3.1 节的三条由这个形状保证：段里只有 `s` 的函数，没有可以手挑的关节角。
- `coupling`（耦合）：`s` 变的时候什么跟着动、工作点写在哪个坐标系里。和"还在碰"的判据一样是具名的（`primitives.COUPLINGS`），每个有三个方法：`value(state)`（`State` 里现在的 `s`，不动东西的耦合给 None）、`moved(state, s)`（`s` 处的 `State`）、`frame(state, s)`（坐标系在 `s` 处的世界位姿）。现在有：
  - `hinge(部件, pose)` / `slider(部件, pose)`：手握把手，部件关节值就是 `s`（`PartAt`）。`pose(v)` 是部件框在关节值 v 的世界位姿（标注的 `part_pose`），由技能的 job 传下来，②③ 层不碰标注和 rig；
  - `still(物体)`：什么都不动，坐标系是 `State` 里的那个物体（搅拌的锅、擦的桌子）。
  - `pushed` / `rolled` / `pivot`（推、滚、翻）随第 7 步加。
- `tcp(s)`：TCP 在这个坐标系里的位姿。None = 刚性：保持 `s0` 时手和坐标系的相对位姿（握着把手）。有工具坐标系以后换成工作点（`T_tcp_tool`，第 6 节接触类）。
- `carry`：机器人怎么跟。
  - `"base"`：手臂不动，底盘和坐标系刚性地一起动（底盘带门）：`ride_base(script, base0, s) = F(s) · F(s0)⁻¹ · base0`，`F` 是 `coupling.frame`。只用于 `PartAt` 且 `tcp` 为 None；
  - `"arm"`：底盘不动，手臂跟着 TCP 走：从起点的关节角起，相邻两个采样之间用运动学直线（`cart_path`，不查碰撞）接着解 IK，分支连续（"关节侧沿 `s` 连续跟"，3.1）。
- `step`：计划查碰撞的 `s` 步长（按角度或位移，2.4）。执行按自己的控制步长对同一个函数求值。

`scripted(kin, state, spec, script, name, base=None, track=None)` 产出 `kind="scripted"` 的段：

- **起点**（`part_start`）：底盘带门的，部件的实测值在 `[s0 − lead, s1]` 里（指令值从实测值起步、不出 `[s0, s1]`，比 `s0` 再往回一个 `lead` 底盘就一开始跟不上）；手臂跟的，离 `s0` 不超过 `TARGET_TOL`（手和部件从 `s0` 起刚性）；给了 `tcp` 的，手臂的 TCP 离 `F(s0) · tcp(s0)` 不超过 `ON_LINE` / `ON_LINE_TURN`。不满足返回 Failure。
- **查碰撞（搜索和执行同一个函数）**：在 `script.samples()` 的每个 `s` 上，按 `coupling.moved` 把部件 / 物体挪到位，按 `Spec` 查（`touch` 和手握的部件只对指定部位放开，其余部位另查）。`carry="base"`：底盘在 `ride_base` 处，`BaseModel.clear` 查底盘本体（对静态世界和这一刻的部件），`free_at` 查整机；`carry="arm"`：查两个采样之间那段 IK 延续的手臂运动（部件在后一个采样处）。有一处不通就返回 Failure：全有或全无，不跳点。门扫过的扇形对家具（2.4 表第三行）还没查。
- **段里存什么**：`info["script"]`（函数本身）、`base0`（构造时的底盘）、`rel`（`s0` 时 TCP 在坐标系里的位姿）、`executor`、`track`；`carry="arm"` 时 `qs` 是 IK 延续出的手臂轨迹（和 `straight` 的路点一样是轨迹，8.1），`s_at` 是每个路点对应的 `s`；`carry="base"` 时 `qs` 为空（手臂不动）。
- **执行器**：
  - `follow`（`carry="arm"`）：照 `qs` 开环走，用于画圈、擦条带、转腕，以及手臂走门的圆弧；
  - `ride`（`carry="base"`，`Actuator.ride` / `Rig.ride`）：闭环，底盘跟着实测开度走。每个物理步对**同一个函数** `ride_base` 在指令值 `cmd` 处求值，不在计划的采样点之间插值，也不出 `[s0, s1]`；`cmd` 以不超过 `rate` 的速度追"实测值 + `lead`"。部件到 `done` 算完成；卡住（`RIDE_STALL`）、超时、或者突然落到 `cmd` 后面 `RIDE_SLIP_LEADS`（2）个 `lead` 以上（把手滑脱、门弹回）就停下，`run.execute` 抛 `SkillFailure`。正常跟着走时，落后量按构造不超过 `lead` + `rate` / `PHYSICS_HZ`（指令往两个方向都追实测值），所以这条线不用实测来定，只用来认出"滑脱"；没开到位由卡住判据和技能的结果检查接住。闭环只调节怎么跟，不改几何。`ride` / `ride_end` 事件记落后量和底盘离指令的距离（任务段余量的数据，8.2）；`lead` / `rate` / `done`（`TRACK_KW`）由技能的 `build` 给。旧的 `skills._ride` 没改，门的技能迁移时删。
- 任务段后面跟一个锚点（8.2），用实测的部件值 / 物体位姿推进 `State`。

### 5.6 动作

不动手臂、推进 `State` 的段：
- `grip(width)`：合爪 → `holding`，松手 → `released`；
- `wait(ticks)`：物体停稳，什么都不动（`place_settle`）；
- `drive_part(部件, 值)`：电机开关门〔待加，第 8 步〕；
- `toggle(电器, on/off)`〔待加，第 8 步〕。

现在有 `grip` 和 `wait`；`run.execute` 遇到别的动作抛 `ValueError`。

锚点不是动作，是单独的段种类（4.3、8.2）。

### 5.7 `decide_ik`：接触位姿的分支（`primitives.py`）

`decide_ik(kin, state, spec, p, R, prior, seeds=()) -> (q, "prior" | "solved") | None`，按顺序：
1. `prior` 本身：TCP 离 (p, R) 在 `HINT_REACH` / `HINT_TURN` 以内，并且按 `spec` 不碰 → 原样用；
2. 否则 `ik_global`，`prior` 是第一个种子、`seeds`（现在的手臂姿态）在后。这是 `Motion.ik` 的全局选法，不是在 `prior` 的分支上就近重解：按离第一个种子的距离、离限位的余量和可操作度（`IK_MANIP_W` 0.3）打分，结果可以离 `prior` 约 0.3 rad（T20）。`Rig._goal` 的第 2 步是局部 IK（`kin.ik`，留在 `q_hint` 的分支上），两者只有第 1 步相同。目标或底盘偏出 1 mm 以上的重做（`run` 的重做、锚点处重做、`run_skill` 原地重做）都走这一步；要真正保持分支，先在 `prior` 上做局部 IK 再全局（改行为，要重跑）；
3. 否则 None（哪个位姿没有解由调用方写进它的 Failure）。

搜索时 `prior` 是排序用的批量 IK 解（运动学，没查碰撞，第 7 节第 3 步），执行时重做用的是 `Plan.decisions` 里的值。第 1 步让重做时分支不变，也避开规划随机性：同一个查询算两次结果会不同（`COLLISION_PLAN.md` 第 140、169 行），重新求出的解即使只偏 0.6 mrad，腰离限位 1 mrad，也会从四次规划成功四次变成一次（T04，`Rig._goal` 的注释）。`_reach`（伸入段、放下段起点）和 place 的 `q_p` 都用它；用了哪一步记在段的 `info["decided"]` = {决定名: "prior" | "solved"}（`pick_reach` 段：`pick_reach`；`place_reach` 段：`place_reach` 是 `q_p`，`set_down_start` 是放下段起点），`run` 的 `segment` 日志原样带上它（重做时记在重做那条事件里，那一段没有自己的事件）；它说的是 `decide_ik` 给出的解，腿走直线时计划并没经过它（`Plan.decisions` 记的是实际走到的解，4.3）。判据是 `primitives.near_pose`（`HINT_REACH` / `HINT_TURN`，转角 `primitives.turn`），`decide_ik` 和 `Rig._goal` 的第 1 步共用。

## 6. 技能计划（`skill_plans/`，9.4）

每个技能的 `build(state, k, prior, start=...)` 按下表的顺序构造：
- `k`：目标组。目标写在物体框里，TCP 位姿由 `build` 从 `State` 推出：pick 的抓取候选在物体框里，用 `State.objects` 换到世界；place 的目标是物体的放置位姿，TCP 位姿用 `State` 里的握法（`Held.T_tcp_obj`）推出。物体动了、握法变了，从实测状态做出来的就是新目标，job 里不另写"目标偏了就整份重做"。
  `motion_state.Aim(obj, T, held)` 说怎么推——`held=False` 是物体碰撞框框架里的 TCP 位姿（pick：`skills._grasp_of` 给 `T_obj_tcp`，伸入方向 `u` 在 TCP 框里），`held=True` 是持物框架在世界里的目标位姿（place：`place_job` 用搜索前实测的握法把每个放下位姿换成物体位姿），`aim_pose(state, aim)` 给出 TCP 位姿。`plan_pick(kin, state, grasp, carry_goals, ...)`、`plan_place(kin, state, goal, pre_open, out_len, rests, ...)` 只拿这些；接触位姿所在的段记下 `aim` / `aimed` / `end` / `tol`（4.3），`holds` 拿它复核（8.4）。抽出段沿放下位姿的夹爪轴；从抽出段起重做时（手里已经没东西、推不出放下位姿）沿松手时的夹爪轴。
- `prior`：搜索时是排序 IK 给的 {决定名: 关节角}；执行时重做是当前 `Plan`。每个运动段先看 `prior` 里同名的段从现在的起点是否还成立（`holds`，8.4），成立就原样拿来（`skill_plans._common._kept`）：动作和锚点在哪都成立，每次重做（复用一个为别的起点做的会把那个起点带下去）；搬运段按构造时的规则查（合爪前假设的握法带 `HELD_POSE_MARGIN`）；收臂段不复用（每次按收起优先重新选）。不成立再用原语做，要做决定的（`decide_ik`、目标集合的序号）先试 `prior.decisions` 里的值。
- `start`：从哪一段开始，执行时重做剩下的计划用。

**pick**（`plan_pick`，到达姿态是收起）：

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达（`pick_arrive`） | 锚点：底盘、物体 | — | 实测 |
| 2 | 张手 | 动作 | — | `with_width(候选宽度)` |
| 3 | 到伸入段起点 | `free_leg`，起点的解由 `decide_ik` 定（`_reach`），直线走不通时腿走到它；决定 `pick_reach` 记这段的终点；容差 `PICK_TOL` | `FREE_HAND` | — |
| 4 | 伸入到抓取位姿 | `straight`；容差 `PICK_TOL` | `FREE_HAND`，不豁免（`exempt=False`：张开的手到抓取位姿也不许碰物体） | — |
| 5 | 合爪 | 动作 | `closing(物体)` | `holding(物体, 计划的抓取位姿)` |
| 6 | 握上（`pick_held`） | 锚点：握法 | — | 实测的 `T_tcp_obj` 替换假设的 |
| 7 | 抬起 | `contact_extent(off_support)` + `contact_segment` | `LEAVE_CONTACT` | — |
| 8 | 去搬运姿态 | `free_leg(PoseSet)`（决定：搬运目标序号） | `FREE_LOAD`，持物 `pad = HELD_POSE_MARGIN` | — |

**place**（`plan_place`，到达姿态是搬运姿态）：

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达（`place_arrive`） | 锚点：底盘、握法 | — | 实测 |
| 2 | 到放下段起点 | `free_leg`，`q_p` 由 `decide_ik` 定；起点的解从 `q_p` 沿直线往上推出，再经 `decide_ik` 确认（`_reach`）；决定 `place_reach` 记第 3 段放下的终点；容差 `PLACE_TOL` | `FREE_LOAD`，持物 `pad = HOLD_DRIFT`〔待加，2.5 步〕 | — |
| 3 | 放下 | `straight`（竖直，长度由 `set_down_length` 从"物体贴着支撑面"往上量）；容差 `PLACE_TOL` | `FREE_LOAD` | — |
| 4 | 松手 | 动作 | 手指可碰放下的物体（`release_spec`，向监视声明） | `released(物体, 落下 LEAVE_GAP 后)`，手张到抓取宽度 |
| 5 | 落下（`place_landed`） | 锚点：物体落点 | — | 实测 |
| 6 | 抽出 | `straight`（沿夹爪轴） | `touch=(物体,)`，手指可碰；物体名是 `plan_place(obj=)` 的参数（从这一段起重做时手里已经没东西，不能从 `State` 里的持物推） | — |
| 7 | 收臂 | `free_leg(JointSet{收起, 下垂})`，每次构造都重新选、不复用 `prior` 的段（不是决定：最后一段，不绑别的段），选了哪个记在 `info["chosen"]` | `FREE_HAND` | — |
| 8 | 停稳 | 动作 `wait`（`SETTLE_TICKS` 90 帧） | — | — |

锚点为什么在这几处、每处误差用余量还是重做，见 8.2。

扁平物体（书）也走 `plan_place`。下垂是持物模型的一部分：计划里用假设的位姿加 `pad`，执行时用实测的 `T_tcp_obj`。技能里不再手补姿态。

**navigate**（`skill_plans/navigate.py` 的 `plan_navigate`，9.3 第 1 步）：

| # | 段 | 原语 |
|---|---|---|
| 1 | 到行驶姿态 | 空手：`free_leg(JointSet{折叠, 下垂})`（现在的 `tuck`），已在就省掉。持物：先用同一套判据复核当前姿态（物体在身体前方、底面不低于 `CARRY_Z` 和 `min_bottom_z`、行驶姿态下整机不碰 `poses_clear`），满足就省掉；不满足才 `free_leg(搬运目标集合)`，`FREE_LOAD` |
| 2 | 开过去 | `drive`（规划的，含路上换下垂） |
| 3 | 到达 | 锚点 |

持物时第 1 段是复核加按需决定：pick 的 `carry_in` 已经定了搬运姿态，满足就原样用，不重新决定（第 1 节第 2 条）。只有 place 才知道的要求（容器边沿高度 `min_bottom_z`）不满足时才动。

实现：判据在 `skill_jobs/carry.py` 的 `_carry`，三条——TCP 在底盘系里落在 `CARRY_SPOTS` 外扩 10 cm 的范围（`CARRY_FRONT_X` 0.25–0.55 m、`CARRY_FRONT_Y` −0.40–0 m）；物体底面不低于 `CARRY_Z` 减 `CARRY_LOW_TOL` 1 cm；整机在这个姿态下原地不碰（`RigBase.depths` ≤ `DEPTH_TOL`）。不满足就 `free_leg(搬运目标集合)`（要求的高度优先），做不出来技能失败（没有不查碰撞的直线）。`min_bottom_z`（`_carry_floor`：目的地的边沿高度，边夹的书再加 6 cm）不是约束而是"能抬就抬"：够得着那个高度的搬运目标就抬上去，够不着就原样带着走，日志写明原因——带物开车的整机底盘规划本来就查物体和世界的碰撞（当成约束的话，v6 T07 / T23 要的 1.15–1.18 m 够不着，navigate 直接失败）。`carry_posture(rig, min_bottom_z)` 是这第 1 段单独跑：place 在停车点搜索之前（这样搜索假设的搬运姿态就是开车时的姿态）、drop、去停靠点前的检查、`stow_load` 用它。空手的 `tuck`、左臂收起做不出来就省掉，由底盘规划在路上换。

navigate(x) 只负责开到 x 那一带，停车点由后面的技能自己选（2.3、第 10 节）。

**retreat**：一段直线 `drive`（5.4），挡住就失败。

**开门**（`skill_plans/door.py` 的 `plan_door`，job 在 `skill_jobs/door.py`，到达姿态是收起；11-10，未跑仿真；物理步骤见 `skills/open.md`）：

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达（`door_arrive`） | 锚点：底盘、部件值 | — | 实测 |
| 2 | 张手 | 动作 | — | `with_width(pre_open)` |
| 3 | 到把手前（`door_reach`） | `free_leg`，起点的解由 `decide_ik` 定（`_reach`）；容差 `DOOR_TOL`（1 mm / 0.01 rad） | `FREE_HAND` | — |
| 4 | 伸到把手 | `straight`；容差 `DOOR_TOL` | 手指可碰部件（`touch_part`） | — |
| 5 | 握上 | 动作 `grip` | `closing(部件)` | `holding(Held(部件, kind="part"))` |
| 6 | 握上（`door_held`） | 锚点：握法 | — | 实测 |
| 7 | 开（`door_ride`） | `scripted(Script(hinge / slider(部件, part_pose), 现在的值, 目标 + 0.02, carry="base"))`，执行器 `ride`；停下时的失败出口写在段里（`clear`：张开、退出接触） | 手指可碰部件 | `with_part(目标 + 0.02)`、底盘到 `ride_base` |
| 8 | 开完（`door_moved`） | 锚点：部件值 | — | 实测 |
| 9 | 松开 | 动作 `grip` | 手指可碰部件 | `released` |
| 10 | 离开 | `contact_extent(near_world)` + `contact_segment`，沿接近方向反着退 | `LEAVE_CONTACT` | — |
| 11 | 收臂 | `free_leg(JointSet{收起, 下垂})`，不复用 | `FREE_HAND` | — |
| 12 | 停稳 | 动作 `wait` 60 帧 | — | — |

抓法变体（侧钩不倾斜 / 10° / 20°、两端、正面捏）是 `Problem.goals`。停车点只按通用排序（第 7 节）：旧代码按力矩比挑停车点（`planner.find_park(score=torque_ratio)`），第 7 节不要 `score` 这类开关，迁移时去掉了；要是仿真里出现停车点选得腕关节拉不动门，改成 `build` 里的约束（握把手的解上力矩比超过关节上限就不要这个停车点，底盘带门时整段受力方向不变，算一次就够）。中继位姿是把手前那一点（`DOOR_RELAY` = `door_reach`）。整个过程只握一次。

还没做：手臂走圆弧（`carry="arm"`）作为目标集合里的另一种做法（第 10 节）；左手拿着东西时开门（等 `Spec.joints`，第 5 步）；微波炉（第 8 步）。

**关门**（待做，还是旧代码）：握把手关是上表把 `s1` 换成关着的值；推门关是 `free_leg` 到推的起点，再接 `scripted` 推（耦合 `pushed_part`，第 7 步加；`touch=((部件, hand),)`）。两种进同一个目标集合，不是先试推、推不了再握。

**接触类技能**（press、touch、stir、wipe、push、roll、flip、expose、sweep，待做）都是同一个形状：到达（锚点）→ 过渡段 → 进入段（`straight`，深度常数）→ 任务段（`scripted`）→ 锚点 → 撤出段（`straight` 或离开段）→ 收臂。工具的工作点（勺尖、海绵底面）是标注里的具名坐标系 `tool_frame`（和 `grasps` 一样写在 `annotations/assets.json` 的资产条目里），由一个函数统一解析成 `T_tcp_tool = Held.T_tcp_obj · T_obj_tool`（4.1），轨迹函数只拿这个矩阵。不要让 10 个接触技能各自从标注换算一遍：那是未来重复代码的主要来源，也是最容易和标注失配的地方。新加一个工具 = 加一条标注，不是加一段代码。跨多个停车点的任务（推每段 25 cm、sweep 逐个物体）每段做一次 `find_park`，段与段之间看实测结果决定下一段。这是任务层的闭环，不是运动的退路。

**姿态类技能**：bend / straighten 是 `free_leg(Joint)`，`Spec.joints` 只放腰。收臂是 `free_leg(JointSet{折叠, 下垂})`。

**微波炉**：电机开门前，`Problem` 加一项检查：部件扫过它的范围时整机不碰（在 `State` 里取几个部件值查）。腔体里的取放是普通的 `straight`，腔体和开着的门都在 `State` 里。电器状态由动作推进。

## 7. 停车点搜索（`park_search.py`）

```
find_park(kin, world, problem, state, log, base=None) -> (Found(x, y, yaw, k, plan) | None, diag)
Problem(goals, build, relay, arrive, travel, near, prefer, label)   # relay 必填；arrive / travel 由 run_skill 按 catalog 填
```

| 字段 | 含义 | pick | place |
|---|---|---|---|
| `goals` | 若干组目标，每组 =（够得着预检用的 TCP 点，排序用的中继位姿，代价） | 每个抓取候选一组（`PICK_CAND_COST`） | 每个"空位 × 物体姿态 × 手腕朝向"一组 |
| `build` | 技能的计划构造函数 | `plan_pick` | `plan_place` |
| `arrive` | 停车点上的手臂姿态（catalog 的 `arrive`；就地的候选是现在的姿态） | 收起 | 搬运姿态 |
| `travel` | 开车时的手臂姿态 | 收起 | 搬运姿态 |
| `near` / `prefer` | 离谁近更好 / 先试的底盘位姿 | 当前位置；门后的物体（腔体里、`inside_` 支撑面上）先试门自由边前方的停车点（`_front_of`，由标注算） | 当前位置（离目标 1 m 以上时不加“近”的代价） |

1. **候选**：围绕每组目标的中心按半径（`RADII`）、角度（`ANGLE_STEP`）取点，每点取多个朝向（`YAW_OFFSETS`），再加上 `prefer` 和"原地不动"。
2. **便宜过滤**：
   - 够得着：肩到目标的水平距离和高度；
   - 底盘柱体不碰（逐个 `world.footprint_clear`，0.07 ms 一个；批量的 `footprints_clear` 在候选聚在目标周围时反而慢一倍多），每个目标最多留 `MAX_PER_GOAL` 个；
   - 行驶姿态下整机不碰：批量 `Motion.base_depths`；
   - 开得到：从当前位置算一次可达场 `base_reachable`，查表。
3. **批量 IK（排序，并作为 `build` 的 prior）**：把中继位姿换到各候选的底盘系，批量求运动学 IK，不查碰撞。按有没有解、关节离限位的余量、可操作度、代价排序。解作为 `prior` 传给 `build`，由 `decide_ik` 在碰撞模型里确认，或换成附近的解（5.7）；它不直接当目标。
4. **按顺序构造计划**：`build(state_at(park), k, prior={problem.relay: 解})`（`relay` 必填，是中继位姿对应的决定名：`skill_plans.PICK_RELAY`（`pick_reach`）、`PLACE_RELAY`（`place_reach`），和 builder 的段名由单测绑在一起），第一个做出完整计划的胜出，`Found` 带着它（`decisions` 是计划实际走到的解，执行时重做的 `prior`）。预算是 `BUILD_S`（20 s）和 `BUILD_MAX`（60 个），失败原因按类计数进 `diag`。
5. **精确底盘路径**：只对胜出者规划（`base.drivable`）；做不出来就回第 4 步取下一个。路径不留：它是轨迹，执行时 `plan_navigate` 重新规划（5.4）。两边是同一个函数（`RigBase.plan`）、同一组行驶姿态（`skill_plans.travel_chain`，9.3 第 1.4 步）。
`diag["filter_s"]` 记构造之前每一步的耗时（候选和够得着 / 柱体、行驶姿态、开得到、排序 IK、打分），`diag["stage_s"]` 记构造里每段的耗时。

计划按（停车点，目标组 k）存。技能要查的东西都在自己的 `build` 里，搜索不再有 `check`、`ride`、`score`、`carry` 之类的开关。任务的不同做法都进 `goals`，不按变体各调一次 `find_park`。

## 8. 执行（`run.py`）

```
run(act, plan, build, hooks):          # act: Actuator（2.5）；build 可为 None（8.8）
  i = 0
  while i < len(plan):
     seg, state = plan[i], observe(act)
     if holds(kin, state, seg) 不成立:            # 每段之前只复核这一段（动作、锚点总成立）
         build 是 None -> SkillFailure
         rest = build(state, seg.name, prior=plan)   # Failure -> SkillFailure
         plan = plan[:i] + rest; seg = plan[i]
     if seg 是锚点 and build 不是 None and 后面还有段:   # 误差进来的时刻：复核剩下的整份
         rest = build(state, plan[i+1].name, prior=plan)   # Failure -> SkillFailure
         plan = plan[:i+1] + rest                # 还成立的运动段在 rest 里原样出现（anchor 事件记 kept / rebuilt）
     hooks.before; execute(act, seg) [在 hooks.around 里]; hooks.after
     i += 1
```

### 8.1 决定和轨迹

| | 是什么 | 什么时候做 | 执行时 |
|---|---|---|---|
| 决定 | 停车点、目标组 `k`、接触位姿的 IK 分支、搬运目标（`Plan.decisions`；收臂姿态每次重选） | 搜索时，往后看完整份计划：`build` 整份做出来才算 | 复用：原样 → 当种子 → 失败（`decide_ik`，5.7） |
| 轨迹 | 过渡段的路径、接触直线的路点、离开段的长度 | 搜索时先做一份，证明做得出来 | 成立就原样走；不成立就从实测状态沿已定的分支重新生成 |

为什么这样分：几段之间靠接触位姿的分支绑在一起。pick 里伸入段起点的分支决定伸入、抬起、搬运做不做得了；place 里 `q_p` 的分支决定放下、抽出、收臂。
- 每段只规划自己是贪心：前一段的分支可能让后面做不下去（T20 s11 重做 place 后抽出没 IK）。
- 整份一次定死、不复核：搜索时的假设到执行时已经过时（8.2 的表）。
- 分开以后：决定有往后看的保证，轨迹用的是实测状态。轨迹带规划随机性也不要紧，换一条一样能走；决定原样复用，分支不受随机性影响。

### 8.2 锚点和余量

误差不沿计划累积：`State` 里是指令关节角，每段从上一段的指令终点出发；自由空间里世界不变，计划预测得准。误差只在下面几个时刻进来，每个时刻放一个锚点：

| 锚点 | 进来的误差 | 上限 | 用余量还是重做 |
|---|---|---|---|
| 到达停车点 | 底盘停下的误差 | 7 mm 以内（`COLLISION_PLAN.md` 第 8 节，没细测；仿真里 1 mm 以内） | 重做：`holds` 按实测底盘查接触位姿段的终点（8.4），pick 多偏 `PICK_TOL`（1 mm）、place 多偏 `PLACE_TOL`（5 mm）以上就从这里重做，决定先原样复用，不行再当种子（5.7），轨迹重新生成。不加余量：余量会拒掉层板、柜子里本来能用的停车点 |
| 握上（合爪后） | 实际握法和假设的不同 | `HELD_POSE_MARGIN` 5 mm | 余量：合爪前规划的搬运段，持物带 `pad`；锚点用实测握法、零余量复核抬起和搬运段 |
| 到达（持物开车之后） | 持物在手里滑动 | `HOLD_DRIFT`（待测） | 余量〔待加，2.5 步〕：开车前做的 place 计划，持物带 `pad = HOLD_DRIFT`；锚点用实测握法复核，放下位姿从实测握法推出，多偏 `PLACE_TOL` 以上才重做 |
| 落下（松手后） | 物体落在哪 | 计划假设下落 `LEAVE_GAP` | 抽出段用 `touch` 放开手指；落点预测不了的（drop）用不预测的锚点（8.5） |
| 任务段之后 | 部件 / 被推物体偏离预测 | 底盘带门：门比底盘慢最多约一个 `lead` | 余量〔待加，看意外接触再定〕：任务段的 `Spec.margin`；锚点用实测值复核 |

规则：**计划按假设加余量，复核按实测、零余量**。这样复核不会比计划严：误差在余量以内，复核一定通过，原样执行；超出余量才重做。

余量还是重做：误差上限小、事先知道、加了余量也不会拒掉多少候选的（握法、漂移），用余量；误差让目标本身变了的（底盘偏了，同样的关节角就到不了目标），用重做。

**握法按实测关节角量**：`State` 里的握法（`Rig.snapshot`）、`place_job` 求放下位姿用的握法、`held_offset` 日志都相对于**实测**关节角下的 TCP（`rig.q()`），不是指令 TCP（`q_cmd`）。持物的手臂会下垂（`q - q_cmd` 中位 0.004 rad、最多 0.013 rad），接触会把手臂顶偏；相对指令 TCP 量的"握法"把这些都读成物体在手里动了，而且随姿态变（同一个焊住的物体，搬运姿态和放下段起点量出来不一样）。按实测量，焊住时握法不变，不焊时变的就是真的滑动，sticky 和 physical 同一个口径。代价：指令 TCP 照这个握法推出的位姿去，手臂还会下垂，物体比计划低约一个下垂量（毫米级，放下段终点离支撑面留着 `LEAVE_GAP`）。

### 8.3 复核和重做是同一个 `build`

锚点处 `run` 不另写判断，直接 `build(state, 下一段, prior=plan)`：
- `build` 对每个运动段先看 `prior` 里同名的段还成立不成立（8.4），成立就原样返回。所以误差在余量以内时，返回的就是原来的计划，代价只是剩下各段的碰撞查询（0.04–0.35 s，中位 0.12 s）。
- 某段不成立就用原语重新做，决定先原样复用；它后面的段起点变了，也跟着重做。
- 两个锚点之间只复核下一段：世界没变，只有意外（被挡住、碰动了东西）才会让它不成立，不成立就是 `run` 普通的重做——从这一段起，复用旧决定。

只有这一处触发重做；job（`_pick_ready` / `_place_ready`）只交出找到的计划，不重新测量、不另写"目标偏了就重做"。

### 8.4 复核 `holds`

`holds(kin, state, seg)`（`primitives.py`，`run` 和 `_kept` 共用）：
- 手臂在这段的起点（`PLAN_AT_START`）；
- 接触位姿所在的段（带 `info["aim"]`）：在现在的底盘下这段终点的 TCP（`query` 里的 `kin.tcp(seg.q_end)`）离从现在的 `State` 推出的目标（`aim_pose`），比建这段时（`info["end"]` 离 `info["aimed"]`）多偏不超过这段的 `info["tol"]`，不成立记 `its end is ... further off its target than built (the target moved ...)`；目标物体不在 `State` 里（不在手里）也不成立。一个判据管三种误差：物体被碰动、物体在手里转了或滑了、底盘停偏。比的是"多偏了多少"而不是"离目标多远"：伸入段的终点本来就不在接触位姿上（在直线起点），IK 解、规划器的终点自己也有残差（cuRobo `POS_TOL` 4 mm / `ROT_TOL` 0.04 rad），那是建这段时已经接受的。容差按技能：
  - pick `PICK_TOL` = `HINT_REACH` / `HINT_TURN`（1 mm / 0.01 rad）：伸入、合爪、抬起是一串叠在抓取位姿上的精细动作，偏了就按实测状态重做（重做时 `decide_ik` 也是这个判据，超过它就重新求解）；
  - place `PLACE_TOL` = `TARGET_TOL` / `TARGET_TURN`（5 mm / 0.01 rad）：放下段执行后按 `PICK_REACH_TOL`（同一个 5 mm）判有没有被挡住，偏得比这少只是放偏几毫米，不重做（重做只能从放下段本身做，放下段只有 1–2 cm 长，偏几毫米的新直线就明显不竖直了）。
  两个都没有实测数据（2.1 跳过）；仿真里底盘停下的偏差在日志精度 1 mm 以内、朝向 0.02° 以内；
- 路点在现在的世界里不碰：按这段的 `Spec`，含 `touch`，零余量；
- 离开段：用 `contact_extent` 从当前姿态重量，长度和计划差超过 `EXTENT_TOL`（`LEAVE_MARGIN` 的一半：终点仍至少留半个余量离开接触，多走的不查碰撞部分也不超过它）就不成立；
- 任务段：`carry="base"` 的底盘离构造时不超过 `TARGET_TOL` / `TARGET_TURN`；耦合的部件在能起步的范围里（`part_start`，同 5.5）；按实测的物体 / 部件重查机器人——`carry="base"` 用同一个函数从构造时的底盘重算，`carry="arm"` 查存下的 `qs`，每段的部件在它的 `s` 处（底盘本体搜索时对静态世界查过，`holds` 没有 `BaseModel`，不重查）；
- 动作段总是成立；锚点不复核自己，它触发复核剩下的。

执行完以后，hook 判"被挡住"（`after_grasp`、`after_down`）比的是实测 TCP 和这段送去的指令 TCP（`q_cmd`），差过 `PICK_REACH_TOL` 就是停在半路；目标对不对已经在这段之前由 `holds` 查过，不在这里再混进来。

### 8.5 不预测的锚点

物体落点预测不了的地方（drop 之后、推完一段之后），锚点带 `predict=False`，计划在这里截止。搜索只证明锚点之前的部分；之后的段，执行时从实测状态用 `build` 做出来（没有 `prior`），做不出来技能失败。跨多个停车点的任务，每段之间是这种锚点（第 6 节接触类技能）。

### 8.6 执行和失败

`execute` 按种类分：`move` 交给 `follow`，持物时限速；`drive` 交给底盘；`scripted` 交给它的执行器（`follow` 照走 `qs`；`ride` 把 `ride_base` 这个函数交给 `Actuator.ride`，没走到 `done` 就失败）；`action` 做对应动作；`anchor` 不动。除锚点（不动，不声明）以外每段都向接触监视声明 `seg.spec.allow`（松手声明"手指可碰放下的物体"）。这些都是 `Actuator` 的方法（2.5）：`execute` 和 `observe` 是 ④ 仅有的两处仿真副作用，而且只通过这个协议，不直接碰 `Rig`。

技能自己的判断挂在 hooks 上：伸入时盯物体、合爪后判断和登记持物、搬运后 `check_held`。hooks 只读状态、做判断、登记、写日志，**不动机器人，不改碰撞模型**。判失败以后要退出接触（没夹住、半路被挡），由技能给一个失败出口的 `build_clear(state)`（张手 + `contact_extent(near_world)` + `contact_segment`），`run` 执行它再抛 `SkillFailure`。做法：hook 判失败时抛的异常用 `motion_state.clearing(exc, open_width, leave, ticks)` 标明要什么退出（张手到多宽、要不要竖直退出接触），`run`（以及 `run_skill` 判结果失败时）用 `skill_plans.plan_clear` 从现在的 `State` 做出这份计划、原样执行，再把原来的异常抛出去；手里还有东西时不张手（`plan_clear` 返回 None）。退出本身失败就往上抛，原来的失败在异常链里。各处要的退出：
- `after_grasp` 被挡住 → 只退出接触；
- `after_close` 没夹住 → 张到 4 cm、退出接触；
- `check_held` 作为 hook（pick 的 `carry_in`、navigate 开车前后、`carry_posture`、place 的 `place_down` 后）发现掉了 → 张开、不退（旧入口的调用方照旧 `open_hand=True`，在 `check_held` 里张开）；
- `_pick_judged` 没拿住 → 张开、不退。

`place_settle`（`wait` 动作）是 place 计划的最后一段；`before_pull_out` 只按现在的 `State` 做一次 `primitives.query` 记录手指碰着什么。`tests/test_skill_plans.py` 守住：`skill_jobs/` 里不直接调 `rig` 的运动入口（`grip`、`leave`、`step`、`move_to`……）。

失败只有两类：
1. 计划做不出来（原语返回原因），包括锚点处重做不出来；
2. 仿真结果不对：被挡住停在半路、没夹住、物体没跟上来、闭环执行器停下（卡住、滑脱、超时）。

意外接触只当指标。搬运中掉了，抛 `Dropped` 给上层。

### 8.7 旧入口

`Rig.move_to` 只留给还没迁移的技能，等于"一段 `free_leg` 的计划 + 执行"。过渡期的 `FREE_ELSE_STRAIGHT` 只在旧入口（`Rig.move_to`、`joint_path`、`move_left_to`）里起作用。每迁完一个技能，就少一个调用方。

### 8.8 外部产出的计划：`rebuild=None`

`Plan` / `Segment` 不该只有 `build` 能产出。`State` 是干净的快照、`Plan` 是干净的运动表示、`holds` + 接触监视是一套独立的校验，合起来意味着：**任何能产出 `Plan` 的东西，都能免费拿到碰撞复核、接触监视、持物限速和失败分类。** 外部策略（学出来的、别人写的）只要产出 `Plan`，`run` 就能执行并校验它；`find_park` 也能拿 `problem.build` 给它打分。

`run(act, plan, rebuild, hooks)` 里 `rebuild=None` 合法，含义是"不重做"：某段 `holds` 不成立就按失败退出，锚点处不复核剩下的（没有 `build` 可调）。`carry_posture` 已经这样用（它的计划是刚从现在的状态做的，不成立就失败）。有了它，④ 就从"pick / place 的执行器"变成"任意 `Plan` 的执行与校验器"，这是第 1 节第 3 条（没有 fallback）唯一合理的放宽方式：外部策略不会重做，但它也不会偷偷走不查碰撞的路。

配套的是 4.6：外部策略要观测，观测走 `Observation`，不进 `State`。

## 9. 现状和下一步

### 9.1 已实现

- 数据：`State`、`Hand`、`Held`、`Spec`（`allow`、`fingers`、`exempt`、`hold_tilt`、`touch`）、`Segment`（`move` / `action` / `drive` / `anchor`）、`Plan`（含 `decisions`）、`Failure`、`Aim` / `aim_pose`，以及推进 `State` 的小函数；协议 `Actuator`、`BaseModel`（2.5）。实测握法按实测关节角量（8.2）。
- 查询层：`Motion.query`（包一层）、`path_free_only`。
- 原语：`free_leg`（`Joint`、`Pose`、`PoseSet`、`JointSet`）、`straight`、`contact_extent`、`contact_segment`，三个"还在碰"判据，`exit_length`；`drive`、`drive_straight`（5.4）；`decide_ik`（5.7）；`holds`（8.4）。
- 计划：`plan_pick`、`plan_place`、`set_down_length`、`plan_navigate`、`travel_chain`、`Carry`、`plan_door`（开门，11-10）、`plan_clear`（手握部件时松开）；目标从 `State` 推出（第 6 节）；锚点 `pick_arrive` / `pick_held` / `place_arrive` / `place_landed`；`prior` 是 `Plan` 时还成立的运动段原样复用（`_kept`，收臂除外）；`HELD_POSE_MARGIN` 5 mm，`PICK_TOL` 1 mm，`PLACE_TOL` 5 mm。
- 第 ⑤ 层：`motion_skills`（`Skill`、`Job`、`run_skill`、`posture`，`SKILLS` 从 `skill_library/catalog.json` 的 `motion_skills` 加载，`template` / `park` / `arrive` / `travel` 都起作用，2.3）；navigate、pick、place、open 走它，它们的 job 在 `zeno_skills/skill_jobs/`（`navigate`、`pick`、`place`、`door`，加上 `base` 的 `RigBase`、`carry` 的搬运判据）。
- 搜索：`park_search.find_park(kin, world, problem, state, log, base)`、`Problem`，pick / place 在用；门后物体（柜子 / 冰箱 `inside_` 支撑面上）的种子停车点由标注推出（`_front_of`）。微波炉腔体里取物不走这里：合约路由到 `PickFromCavity`（policy_048，旧实现，第 8 步）。
- 执行：`run.observe`、`execute`、`run(act, plan, rebuild, hooks, clear)`（每段 `holds`、锚点复核剩下的整份，`rebuild=None` 合法，8.8；失败出口 `run_clear`，8.6）。
- 单测：`tests/test_primitives.py`、`test_skill_plans.py`、`test_park_search.py`、`test_navigate_plan.py`、`test_layering.py`、`test_motion_skills.py`（FakeKin，不起仿真）。
- 基线：全量跑 v6（`COLLISION_PLAN.md` 第 5 节）。最后一次全量是 `1c5b98d` 的 69/153（11-10）；`6938eac` 以后（底盘分层、9.3 第 2.3、2.4 步）还没跑全量。
- 静态审计：`tools/audit_collision.py`，`tests/test_collision_audit.py` 是棘轮，`tools/stop_check.py` 每轮也跑。它认识 `Spec`（`Spec(allow=LEGACY / unchecked(...))`、`Spec(exempt=...)`、`Spec(fingers=False)` 和写在 `move_to` 上一样算）；执行入口（`EXECUTION`：`run.py`、`rig.py`）和查询层（`QUERY_LAYER`：`Motion.query`、`Motion.path_free_only`）里的 follow / 豁免不算，这些放宽在写 `Spec` 的地方已经算过；`find_park` 按顺序调 `build` 不算重试。另有 `old_entry` 一类（9.3"只降不升的计数"）。

### 9.2 pick / place 还没解决的

| 问题 | 例子 | 怎么解决 |
|---|---|---|
| 构造预算用完：收臂失败每次约 10 s | T06 s10、T01 s10 | 9.3 第 2.7 步 |
| 持物在手里滑动没有余量，按实测复核判碰就得重做 | — | 开车前的 place 计划带 `HOLD_DRIFT` 余量（8.2，2.5 步）；`HOLD_DRIFT` 要在 `physical` 下按实测滑动定（握法按实测关节角量，sticky 下它不变） |
| 持物去搬运姿态的规划慢（保持倾角按位姿规划单次 0.6–8.4 s） | pick 构造时间的大头（`carry_in` 约占 77%） | 不涉及；pick 锚点处重做（`PICK_TOL` 1 mm）常碰上它会更慢（第 10 节） |
| place 搜索的时间大多花在构造之前 | place 搜索中位 16.3 s 里 11.6 s；候选中位 11 万个，构造中位只做 1 份。候选 + 够得着 0.7 s，柱体约 3.5 s，其余在行驶姿态 / 排序 IK（`diag["filter_s"]`） | 先按 `filter_s` 找大头，再考虑分批排序或同一空位的手腕朝向共用底盘候选（第 10 节） |
| 书还走旧 `place_flat`，翻书走旧 `FlipFlat` | T15 s10/s11 | 2.7 步 |

第 1 节第 2 条（每个决定一个出处）在 pick / place / navigate 里已经没有重复的出处。

### 9.3 迁移顺序

按"覆盖多少 v6 路线步数、依赖谁"排（2.3 的表）：

1. **框架（第 ⑤ 层，已完成 11-08）**：`Skill`、`run_skill`、`drive`（包 `_base_plan` 和 `straight_base_move`）、`plan_navigate`；pick / place 改走 `run_skill`；`skill_plans.py` 拆成包（9.4），`Actuator` 协议（2.5），`SKILLS` 进 catalog（2.3），`plan_navigate` 第 1 段按约束复核持物姿态（删 `_carry_pose` 和它的 `FREE_ELSE_STRAIGHT`），`_drivable` 和 `plan_navigate` 用同一组行驶姿态（`travel_chain`）。navigate 一项就覆盖 1099 步。和计划的出入：`find_park` 多一个参数 `base`；协议方法叫 `arm_kin`；技能接口是过渡形式 `Job`；`min_bottom_z` 是"能抬就抬"不是约束（第 6 节）。
2. **pick / place 收尾**，每项单独提交：
   1. 〔没做，跳过了〕先只记录不改行为：到达、握上、落下时的实测偏差（底盘、握法、漂移、终点 TCP 离目标多远）写进日志（锚点的 `info`，4.3），跑一次定 `BASE_TOL`、`HOLD_DRIFT`、`TARGET_TOL` / `PICK_TOL`；同一次提交里建 `tolerances.py`（4.5），把散落的阈值搬进去、补上来源标记；
   2. **已做（11-09，376b692）**：`decide_ik`（5.7）、`Plan.decisions`（4.3）、`build` 的 `prior`。和计划的出入：`Problem.relay` 告诉 `find_park` 排序 IK 解属于哪个决定；搬运目标的选择也复用（(序号, 集合大小)）；`Plan.decisions` 记计划实际走到的解。针对性对照新 4/8、旧 3/8（T20 bottle_on_cabinet 改好：放下段起点的解原样用，不再被 `Motion.ik` 的可操作度项换掉）；
   3. **已做（11-10，c21cb48）**：目标从 `State` 推出（`Aim`，第 6 节），删 `_pick_ready` / `_place_ready` 开头的整份重做和 place 开车后的重新测量，`plan_place` 去掉 `u_out`。sticky/gt 下 5 集事件日志和旧代码逐条相同；
   4. **已做（11-10，83a4209、43eaa13，审计修正未提交）**：`holds` 挪进 `primitives`；锚点段，`run` 在锚点复核剩下的整份（`anchor` 事件记 `kept` / `rebuilt` / `seconds`）；`build` 原样复用 `prior` 里还成立的运动段（`_kept`）。针对性对照 5 集成败同旧代码，31 个锚点没有一次重做，每次 0.04–0.35 s。
      审计后修正（11-10）：收臂段不复用（之前 `_kept` 会把搜索时选的下垂原样留下，违反第 1 节第 8 条）；握法改按实测关节角量（8.2，之前相对指令 TCP，sticky 下手臂下垂、被接触顶偏会读成"目标挪了"，T09 两次 place 失败都是这样触发的）；目标检查和底盘终点检查合成一个判据，容差按技能：pick `PICK_TOL` 1 mm、place `PLACE_TOL` 5 mm（之前物体位移 1 mm、底盘位移 5 mm，两个技能一样）；`after_grasp` / `after_down` 判被挡住改为比实测 TCP 和指令 TCP（之前比执行后重推的目标，接触中目标跟着变，混进了目标的位移）。`anchor` 事件的 `rebuilt` 只列路点变了的运动段（收臂每次重做，做出来一样的不算）。验证（v6 sticky/gt，8 集，`/data/zenobench/verify_1110`）：5/8 成功（T02、T05、T09 pot_in_use、T24、T25）。T09 是这一系列改动里第一次成功（之前各版本都在放锅时失败：目标被读成"挪了"后重做，或重做后停短）；T24 在 2.2 对照里放苹果失败、这次成功。失败的三集和以前同处：T13 的 look 视线被挡、T04 一只杯子始终倒着（倾角 81.3°，各版本相同）、T17 放锅盖时手臂离指令 14 cm（旧代码在同一处报"目标挪了 11 cm / 41°"，是同一件事：手臂没跟上 `place_reach`）。69 个锚点（pick 38 个，`PICK_TOL` 1 mm 下一次也没重做），段的重做 0 次；伸入后实测 TCP 离指令中位 0.9 mm、最多 1.0 mm；松手前物体离支撑面的间隙中位 5.8 mm（之前 6.0 mm），握法改按实测关节角以后看不出下垂的影响。
      对照方法：锚点多出的复核查询（`contact_extent` 等调 cuRobo IK）会改变求解器的调用历史，之后的排序 IK 跟着变，五集都在某次停车点搜索处和旧代码分开——没有单独做实验证明。以后的对照不再要求事件日志逐条相同，比锚点 / 段的重做、成败和失败类别；
   5. 余量：place 计划带 `HOLD_DRIFT`；
   6. **已做（11-09）**：hooks 不动机器人，失败出口是 `run` 执行的计划（`clearing` + `plan_clear`，8.6）；
   7. 9.2 第一张表里剩下的：收臂预算、搬运慢、书进 `plan_place`（删 `place_flat`）。
3. **感知类**：look、search、explore_furniture / explore_room、inspect、measure、identify、count。navigate + 头部动作，只依赖第 1 步。
4. **取放家族**：drop、stack、lift、hover、cover、present；collect 在任务层串。在 `plan_pick` / `plan_place` 上换目标集合。
5. **姿态类**：`Spec.joints` + 拆 `q_body`（`JointSet` 第 1 步已加）（`joints` 按关节名写，不按 `q_right` 的下标）。bend / straighten、升降躯干、wave、nod；删改 `kin.lo / hi` 和 `_lock_shared_posture` 的地方。
6. **部件类 + retreat**：`scripted` + `Held(kind="part")` + `touch` 扩到部件和部位。开关门，`_ride` 变成闭环执行器，删 `hand_touches_part`；retreat 用直线 `drive`。
   **框架已做（11-10，未跑仿真）**：`Script` + 耦合（`hinge` / `slider` / `still`）、`scripted` 段（`carry` 底盘 / 手臂）和 `run.execute` 的两种执行器、`Actuator.ride`（`Rig.ride`）、`BaseModel.clear`（`RigBase.clear`）、`Held(kind="part")`（`Rig.snapshot` 从 `_handle_grasp` 读出，`Motion.query` 不挂盒子、只放开手指对这个部件）、`Spec.touch` 写部件和 `hand`；FakeKin 单测 `tests/test_scripted.py`。
   **开门已迁（11-10，未跑仿真）**：`plan_door` + `open_job`（第 6 节），`skills.open_articulated` 转到 `run_skill`（左手拿着东西、微波炉还走旧代码）；合约 `hinged_door` / `drawer` 路径改成和冰箱一样的 policy_003 + policy_022，只握一次，policy_046 / 047 / 049 / 050 退役；`Aim` 可以写在部件坐标系里（`frame`）；`plan_clear` 能松开把手；旧代码按力矩比挑停车点，去掉了（第 6 节开门）。单测 `tests/test_door_plan.py`。关门还是旧代码。还没做：关门（推门要 `pushed_part`）、手臂走圆弧、门扫过的扇形对家具、`Spec.margin`、`Allow` 由 `touch` 推出；删 `skills._ride` / `_ride_check` / `_move_articulated` 要等关门也迁完。
7. **接触类**：按 v6 用量排，依次是 stir、wipe、roll / flip、expose、press / touch、push、sweep、pour。先加 `tool_frame` 标注和它的解析（第 6 节接触类技能），再迁第一个技能，否则 9 个技能各写一遍换算。删 `LEGACY` 直线和"到不了的点跳过"。
8. **微波炉和电器动作**：`drive_part`、`toggle`、电机开门前让开的检查。删 `withdraw_microwave_cavity` 记的 `microwave_retrieval_q`（pick 已经不读；`policies/embedded.py` 的 `PickFromCavity` 还在用）。
9. **左臂和两臂**：两手搬的物体进碰撞模型（闭链约束另议）；`q_body` 已在第 5 步拆好。
10. **收尾**：删 `Rig.move_to` / `move_to_any` / `joint_path` / `move_left_to` / `leave`、旧的 `planner.find_park`；`Motion.query` 改成直接实现。

每步单独提交，先针对性检查再全量（全量跑 v6，`COLLISION_PLAN.md` 第 5 节）。

**只降不升的计数**：静态审计的 `old_entry` 一类（棘轮，按文件计）：执行入口（`run.py`、`rig.py`）以外直接调 rig 旧运动入口的地方（`OLD_ENTRIES`：`move_to`、`move_to_any`、`joint_path`、`joint_path_via`、`move_left_to`、`leave`、`tuck`、`swing`、`follow` / `follow_smooth` / `left_follow` / `follow_both`、`drive_base`、`grip`）。现在 203 处（`skills.py` 50、`orientation.py` 24、`hand.py` 19、`extra.py` 18、`bimanual.py` 17、`tooluse.py` 17、`embedded.py` 14……；`skill_jobs/` 0）。每步迁移必须让它下降，第 10 步到 0。每个新 `build` 有 FakeKin 单测（`tests/test_skill_plans.py` 的写法）。

### 9.4 代码放哪

`skills.py` 约 2200 行，`policies/` 另有约 5400 行（量级，精确数用 `wc -l`）。迁移有 10 步，新的 `Skill` / `build` 要是继续往 `skills.py` 里加、旧的又注释着不删，它会长期背着死代码，同时还在变长。

规则：

| 放什么 | 放哪 |
|---|---|
| `build`（第 ② 层） | `skill_plans/` 包，**按 2.3 的形状分文件**：`pick.py`、`place.py`、`navigate.py`、`door.py`、`contact.py`、`posture.py`，共用部分在 `_common.py` |
| `Skill` 的数据部分 | `skill_library/catalog.json` 的 `motion_skills`，出处是 `tools/build_skill_library.py` 的 `MOTION_SKILLS`（2.3） |
| `Skill` 的代码部分里不碰 rig 的（轨迹函数 `traj`） | 和它的 `build` 同一个文件 |
| `Skill` 的 `job`（目标采样、hooks、结果判断：要读 rig 的标注和状态，属第 ⑤ 层）、`RigBase` | `zeno_skills/skill_jobs/`，一个技能一个文件。不能放进 `skill_plans/`（它不许碰 rig），也不放 `skills.py`（只减不增） |
| 阈值常数 | `tolerances.py`（4.5） |
| `Actuator` 协议 | `motion_state.py`（和 `State` / `Spec` 一起，它也是层间接口） |
| 退役的旧实现 | **删掉**，靠 git 回退，不靠注释保留 |

`skills.py` 立下规矩：**只减不增**。这样"只降不升的计数"还能按文件看出每一步的进度，而不是只看一个总数。

## 10. 待定

| 问题 | 倾向 |
|---|---|
| 搜索第 3 步的批量 IK（不查碰撞，排序 + 当 `prior`）要不要 | 先留；量排序准不准，不准就去掉。去掉后 `decide_ik` 只是少一个种子，手臂质量从做好的计划里算 |
| 构造预算 | 按时间（`BUILD_S` 20 s）；收臂失败太慢的问题先解决，再看要不要调 |
| 持物去搬运姿态太慢 | 调小保持倾角规划的尝试次数，或让搬运目标优先选关节直走不倾斜超标的 |
| `BASE_TOL`、`HOLD_DRIFT`、`PICK_TOL`、`PLACE_TOL` 的值 | 9.3 第 2.1 步先记录实测偏差再定；现在 `PICK_TOL` 取 `HINT_REACH` 1 mm、`PLACE_TOL` 取 `PICK_REACH_TOL` 5 mm（8.4） |
| 底盘误差用重做还是余量 | 重做（8.2）。要是 pick 的到达锚点（`PICK_TOL` 1 mm）几乎每次都重做，而且重做常碰上慢的搬运段规划，再考虑放宽或给 `free_leg` 加余量 |
| 锚点处重做做不出来，要不要换停车点再找一次 | 倾向任务层最多再找一次：约束不变，不算 fallback；要先看 9.3 第 2.1 步的记录里这种情况有多少 |
| 任务段的余量（`Spec.margin`） | 底盘带门的停止线不用实测（5.5，`RIDE_SLIP_LEADS`）；余量等门迁移后看意外接触，有手臂蹭门板再按 `ride_end` 的落后量定 |
| 开门：手臂走圆弧还是底盘带门 | 两种都作为目标集合里的做法，由搜索挑 |
| 力的几何替身够不够 | 先够；不够再加力反馈 |
| 两手搬的闭链 | 9.3 第 9 步再定 |
| `Observation`（4.6）什么时候做 | 没有使用方就不做。第一个要接的外部策略出现时再定它的形状，现在只守住"不塞进 `State`" |
| 路线里 navigate(x) 选一次底盘位置，后面的技能又选一次停车点 | 两者目的不同：navigate 只开到 x 那一带，停车点由技能定，接受。另一种是 navigate(x) 后面紧跟技能时不动，会改路线语义 |
| place 搜索构造之前的耗时 | 先看 `filter_s` 的大头；候选可以先按空位（不按手腕朝向）取，8 个朝向共用底盘的检查 |
| 复合技能（drop、heat、collect）放在哪一层 | 任务层串几个 `run_skill`，每个子技能各有锚点。做成一个大 `build` 搜索时能往后看得更远，但计划长、重做范围大 |
