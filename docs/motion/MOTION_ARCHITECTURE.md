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

9.3 第 1 步以后，pick / place / navigate 都走 `motion_skills.run_skill`（2.3）：`skills.pick` → `_pick_pinch_core` → `run_skill(SKILLS["pick"])`，`skill_jobs/pick.py` 的 `pick_job` 给出 `Problem`（`_pick_problem`）、开到以后的计划和 hooks（`_pick_ready`）、结果判断（`_pick_judged`）；place 是 `_set_down` → `run_skill(SKILLS["place"])`，`skill_jobs/place.py`；navigate 是 `skill_jobs/navigate.py`（`plan_navigate`）。之后迁过来的：开门、关门（`skills.open_articulated` / `close_articulated` → `skill_jobs/door.py` 的 `open_job` / `close_job`，9.3 第 6、6b 步），推桌上的物体（`skill_jobs/slide.py` 的 `push_object` → `slide_job`，第 7 步），姿态类（crouch / stand / bend / straighten / tuck：`policies/posture.py` → `skill_jobs/posture.py` 的 `body_job` / `tuck_job`，第 5 步）。其余技能（微波炉的开关门、`drop_into`、`place_flat`、倒、搅拌、翻书……）还不走 ①–④，直接调 `rig.move_to` / `joint_path` 等旧入口。

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
0. 头转回正前方（`HEAD_STRAIGHT`，yaw、pitch 都是 0，explore / search 结束时就停在这里），再读规划用的状态。look 会把头留在它看的方向，近处、低处的目标会让头压到俯仰下限（往下 18°）；手臂规划把头当成锁在当前角度，一弯腰头就压到手和工作台上（T07，11-14：head_link 插进刚看过的托盘 40 mm）。这样每个技能都对着同一个头规划、保持姿态。观测受限 benchmark 的门在调用开始前就查完了（`GatedRunner.run`），look 看到的视野照样算数；
1. `problem = skill.problem(...)`；
2. 要选停车点的，`find_park`（`travel` / `arrive` 姿态取 catalog 的；在现在的位置上，手臂就是现在的样子）；不选的（姿态类、感知类的头部动作），只在原地 `build`，停车点就是现在的位置；
3. 不在停车点，就构造并执行 navigate 的计划（`plan_navigate`，第 6 节）；离停车点在 `AT_PARK_M` / `AT_PARK_DEG`（2 cm / 2°）以内、不开车的，用同一个 `build` 在现在的底盘位置重做一次计划（`park_here`，找到的计划当 `prior`：接触位姿段的终点在这个底盘下没多偏的原样留下——pick 按 `PICK_TOL` 1 mm、place 按 `PLACE_TOL` 5 mm，8.4——其余重做），做不出来就开过去；
4. `run(rig, plan, problem.build, skill.hooks)`（`rig` 就是 `Actuator`）；hook 判失败时执行 `build_clear` 再抛 `SkillFailure`。

`AtomicPolicy.execute` 只剩 `run_skill(self.rig, SKILLS[name], args)`。（这条管的是运动层技能。感知类在运动层之上还有一层**任务层**：search、explore_room、explore_furniture、view_support、count 决定站哪、看哪、看到了什么、下一步去哪——这些决定依赖途中看到的东西，不放进一份计划；它们动机器人只经 `run_skill`（navigate、look），自己不调任何运动入口，`tests/test_layering.py` 守住。"站哪看得见"的判据只有一个出处：`zeno_skills/viewpoints.py`。）迁一个技能 = 给它写 `problem`（目标集合）和 `build`（尽量用下表的模板），hooks 照搬，然后不再调旧入口。

**过渡形式（`zeno_skills/motion_skills.py`）**：技能的 Python 部分是一个 `job(rig, args, state, skill) -> Job`（`skill.build` 是 catalog 的 `template`，job 用它构造计划），`Job` 按 `run_skill` 的步骤给回调：`problem`（没有就原地做，如 navigate）、`no_park(diag)`、`found(found)`（日志）、`travel`（开到停车点时给 navigate 的参数，如 `min_bottom_z`）、`ready(found) -> (plan, build, hooks)`（只交出找到的计划、重做用的 `build` 和 hooks，不重新测量、不重做）、`failed(exc)`、`done()`。日志和结果判断挪走以后，`Job` 收缩成上面的三样。现在走 `run_skill` 的是 catalog 里的 6 个：navigate、pick、place、open、close、push（之后又加了 drop、stir、look、inspect，和姿态类的 crouch、stand、bend、straighten、tuck）；它们的 policy 照旧调原来的函数（`skills.navigate / pick / place`、`open_articulated` / `close_articulated`、`push_object`），这些函数内部转到 `run_skill`。

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
  follow(qs, steps_per_wp, smooth, side)   # 那只手的规划链路点，持物时限速、平滑起停，按那只手的 TCP 判到位；
                                           # 两只手同一套执行（旧入口的 Rig.left_follow 留给旧代码）
  ride(part, base_at, s_from, s_to, label, lead, rate, done)   # 底盘带部件的任务段的闭环：底盘在 base_at(指令值)，指令跟着实测部件值（5.5）
  grip(width, steps, gradual, side)    # 那只手的夹爪
  drive_base(path, **kw)               # 底盘沿路点（allow、速度）
  swing(posture, label)                # 躯干和两臂同时关节直线到行驶姿态 Posture（底盘规划器定的换姿态）
  declare(name, allow, side, follows)  # 向接触监视声明这一段（rig.clear.motion）
  contact_allow(kin, allow)            # 从接触出发时，按现在碰着什么收紧 Allow
  wait(ticks)                          # 什么都不动，让世界停稳若干物理步
  aim_head(yaw, pitch, steps)          # 头的两个关节到 (yaw, pitch)，最多 steps 个物理步（不叫 head：Rig.head 是关节下标）
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
    body: np.ndarray             # 躯干升降、腰（q_body：两条手臂都挂在上面；指令姿态）
    arms: Mapping[str, np.ndarray]   # "right" / "left" -> 那条手臂的 7 个关节（指令姿态）
    head: Mapping[str, float]
    hands: Mapping[str, Hand]    # "right" / "left"
    objects: Mapping[str, np.ndarray]   # 物体框的世界位姿：实测，或假设（刚放下落在哪）
    parts: Mapping[str, float]   # 可动部件的关节值
```

- 执行时 `run.observe(act)`（`Actuator.snapshot`）从仿真读出。搜索时用小函数从当前状态改出假设：`at_base`、`with_arm`、`with_width`、`holding`、`released`、`with_object`，每个都返回新的 `State`。`state_at(park)` = `at_base` + `with_arm(到达姿态)`。
- **完整性**：凡是影响碰撞查询的都在 `State` 里（头、左臂、手指宽度、部件值）。
- `Held(kind="part")`：手握着部件的把手。握着时，那只手的手指对这个部件不算障碍物（和持物一样），松开就恢复。它取代技能里设了不恢复的 `hand_touches_part`。
- `Held.T_tcp_obj` 是"手里的东西在 TCP 里的位姿"的唯一表示。实测的握法按**实测**关节角下的 TCP 量（`Rig.snapshot`，8.2）：焊住（sticky）时它不随姿态、下垂、接触顶偏而变，不焊（physical）时变的就是手里真的滑动，两种模式同一个口径。工具的工作点（勺尖、海绵底面）是它的直接延伸：`T_tcp_tool = T_tcp_obj · T_obj_tool`，其中 `T_obj_tool` 是标注里的 `tool_frame`（第 6 节接触类技能）。
- **已改**（9.3 第 6a 步，从第 5 步提前；11-11，bdc2a23）：腰和躯干两条链共用，拆成 `body`（躯干、腰，文中叫 q_body）+ `arms`（`{"right": 7 维, "left": 7 维}`）。`State.q(side)` 照旧拼出那只手的规划链（9 维），规划器给出的 9 维解照旧用 `with_arm(state, q, side)` 写回。新层全部改用新字段，不留 `q_right` / `q_left` 的别名。
  - **两条手臂都挂在躯干上**：q_body 一动，另一条手臂和它手里的东西跟着动（腰弯 39° 够柜门时把左手的擀面杖撞掉过，`skills._move_with_retry` 因此在左手拿着东西时把腰压在 0.25 rad 以内；`policies/bimanual._lock_shared_posture`、`policies/hand.py` 的 steady 都锁住 q_body；导航的 `left_fold` 也只动左臂 7 个关节）。规则：**另一只手拿着东西时，这只手的段锁住 q_body**（`Spec.joints` 的最小版，6a）；需要动 q_body 的，单独一段只动 q_body，手臂相对躯干不动，不和手臂在同一段里一起动。
  - **姿态目标的 q_body 只在 q_body 能动时生效**：收臂、下垂、行驶、arrive 这些姿态带着 q_body（`kin.rest` / `kin.drive` 是 9 维、q_body 是 (0, 0)：两手都空时收臂顺手把身体扶正，这是要的），但另一只手拿着东西时只动手臂、q_body 保持——不然一只手收臂会把躯干升到顶、腰扳直，另一只手跟着动。实现两处：`free_leg` 的 `Joint` / `JointSet` 目标在 q_body 锁住时把 q_body 换成起点的（`primitives._keep_body`）；`motion_state.with_posture(state, posture)` 只在没被点到的手都空着时才用姿态的 q_body（`find_park` 的 arrive / travel 都走它）。整机姿态是 `motion_state.Posture(body, arms)`（`arms` 只写它动的手），用在 `swing`、`BaseModel.plan` 的 chain 和 steps、drive 段（`q_from` / `qs` 是 `Posture.vec()`：body + 右臂 + 左臂 16 维，`holds` 查两只手都在起点）。
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
    joints: tuple | None = None  # 这段允许动的关节，其余锁在起点；None = 默认规则：另一只手拿着东西时锁 q_body（locked_body）
    arms_still: bool = False     # 两条手臂相对底盘都不动（底盘带门的任务段）：另一只手的东西挂在它的 held link 上（4.4）
    margin: float = 0.0          # m 计划时要求的余量：不在 touch / exempt 里的部位离世界至少这么远（待加）
```

- `touch` 的每一项写成（名字，部位），部位是 `fingers` / `hand` / `load`：手指碰刚放下的物体，手碰门板，持物碰锅或台面。`Allow` 的允许接触由 `touch` 推出，不另写一份。现在实现了 `fingers` 和 `hand`（`motion_state.touch_entries`：只写名字 = 手指），名字是物体或部件（`Motion.touch_owner`：先找物体，再找部件）；手握着的部件（`Held(kind="part")`）不用写进 `touch`，`motion_state.touches` 把它按 `PART_HOLD`（手指）加进去，`Motion.query` 和 `primitives.free_path` 用同一份。`load` 和"`Allow` 由 `touch` 推出"还没做。
- `hold_tilt` 保持的是起点倾角。倾角要变（勺子倾进锅、翻书），就在任务段里变，或者在 `hold_tilt=False` 的过渡段里变（持物照样查碰撞）。
- `joints` 取代改 `kin.lo / kin.hi` 和 `_lock_shared_posture`。`joints=None` 是默认规则（9.3 第 6a 步，11-11）：另一只手拿着东西（含握着把手）时锁 q_body，手臂不锁（`motion_state.kept`，4.1）。写了 `joints` 的（9.3 第 5 步，11-16）：按关节名写这段允许动的关节，链上其余关节（q_body 和手臂 7 个）都钉在起点；`ARM` 代表这条链的全部手臂关节。姿态段只写一个 q_body 关节（下蹲：`("torso_lift_joint",)`），两条手臂相对躯干不动；6b 推门的 `push_body` 段同样只动躯干（之前只看 q_body 的两个关节：关节直线走不通转规划时，手臂 7 个关节规划器可以动），算它高度的那次 IK 写 `("torso_lift_joint", ARM)`（躯干和手臂能动、腰锁住）。`Motion.query` 把锁住的关节钉在 `State` 里那条链的值上，退出时复原；钉关节只有一处实现 `kinematics.kept_joints`（改 `kin.lo / kin.hi`，`_Arm.prepare` 给钉住的关节留 ±PIN 带），查询层、`free_leg` 的关节目标（`primitives._keep_body`）、`decide_ik` 的 prior 和停车点搜索的排序 IK 都用它（排序 IK 只看 q_body：`locked_body`）。
- `arms_still`（6a 加）：这段里两条手臂相对底盘都不动（底盘带门的任务段的采样点，`primitives.scripted` 自己填），另一只手的东西挂到它的 held link 上（4.4）。
- `margin` 只在计划时用（`Kinematics.near(q, margin)` 判碰）；复核用实测状态、零余量（第 8.2 节）。现在唯一的余量是持物的 `Held.pad`；`margin` 留给任务段：底盘带门时门比底盘慢最多约一个 `lead`，手和门的相对位置跟着变，意外接触报告里出现手臂蹭门板再按 `ride_end` 的落后量定。
- 执行参数（速度、`smooth`、`steps_per_wp`）放在 `Segment.info`，不进 `Spec`。

### 4.3 `Segment` 和 `Plan`

- `Segment`：名字（`pick_grasp`、`carry_in`…）、`Spec`、起点关节角 `q_from`、路点 `qs`、种类 `kind`、这段的目标 `target`（位姿或关节角，复核用）、动作 `action`、原语量出或选出的东西 `info`（长度、做法、方向 u、判据名）。
- `kind`：`move`（手臂路点）、`drive`（底盘路径，手臂不动）、`scripted`（任务段：轨迹函数 `Script` 加执行器名，见 5.5）、`action`（不动手臂：`grip`、`wait`、`drive_part`、`toggle`）、`anchor`（锚点：误差进来的时刻，读回状态、复核剩下的计划，见 8.2；`skill_plans._common.anchor` 做，`info["assumed"]` 是计划在这一刻假设的 `State`，`info["watch"]` 是技能瞄准的物体 / 部件，`run` 在这里读回 `State` 后把偏差记进 `anchor` 事件，9.3 第 2.1 步）。
- 接触位姿所在的段（`pick_reach`、`pick_grasp`、`place_reach`、`place_down`）的 `info` 另记 `aim`（`motion_state.Aim`：目标怎么从 `State` 推出）、`aimed`（建这段时推出的位姿）、`end`（建这段时终点的 TCP）、`tol`（终点比建时多偏多少还算成立：`PICK_TOL` / `PLACE_TOL`），由 `skill_plans._common._aimed` 填，`holds` 复核（8.4）。
- `Plan`：段的元组、服务的目标组 `goal`（现在没人填，目标组在 `Found.k`）、决定 `decisions`、构造耗时 `info["stage_s"]`（`plan_pick`、`plan_place` 都填，失败时在 `Failure.info` 里）。
- `Plan.decisions`：{名字: 值}，`build` 做的、把几段绑在一起的决定（8.1），名字就是段名：接触位姿的关节角，记的是计划实际走到的解（`pick_reach` 是伸入段起点的解 = `pick_reach` 段的终点，`place_reach` 是放下位姿的解 = `place_down` 段的终点）——不是 `decide_ik` 给 `free_leg` 的解：TCP 直线走得通时腿停在直线自己的解上，后面的段从那里做（约一半的伸入段起点和放下段起点是这样）；搬运目标的选择（`carry_in`），记 (序号, 集合大小)；收臂姿态不算决定：它是最后一段，不绑别的段，每次构造按 `JointSet` 的顺序（收起优先）重新选，也不作为段复用。重做时作为 `prior` 传回 `build`（`motion_state.decisions_of` 把 `Plan` 或 {名字: 值} 统一成字典）；目标集合的选择经 `free_leg(first=)` 复用：集合大小一样（从 `State` 做出来的集合会随状态变样：`skills._carry_goals` 每个点 2 层或 3 层高度，同一个序号就是另一个目标）、那个目标还够得着（`PoseSet`）/ 还不碰（`JointSet`）就用它，否则重新选。
- `Failure(why, segment, info)`：原语或计划做不出来的原因。搜索按类计数，技能用它报错。

### 4.4 碰撞查询层 `Motion.query(state, spec)`

`Motion.query` 把 `State` + `Spec` 翻译成一次 cuRobo 查询：
- 锁定底盘、另一只手臂、头和手指宽度；
- 把手里的东西挂到夹爪上（`pad` 放大），握着的部件对那只手不算障碍物。6a 之前只挂进拿着它的那条手臂的模型；另一条手臂查询时，它是碰撞世界里一个不动的障碍物，停在同步时的位置（停车点搜索换了底盘它不跟着走：原地留一个幽灵，新位置没人查；腰、躯干一动也对不上）。现在按下面的两种表示查。

  **另一只手的东西怎么进查询**（9.3 第 6a 步，已做：`Motion.query` 里 `_tcp_of` 推位置、`_attach_cross` 挂 held link）：每个手臂模型里两只手各有一个 held link；另一只手的 held link 在这条手臂的模型里不参与自碰撞（下面的"每条手臂的自碰撞表"）。所以挂在 held link 上只查得到"它 vs 世界"，查不到"这条手臂 vs 它"；它也不能同时是世界障碍物（held link 上的球会和它自己撞）。两种情况各用一种表示，由这段的 `Spec` 定：
  - 这条手臂在动、另一只手不动（另一只手拿着东西时 q_body 锁住，4.1）：它是世界障碍物，位置**从 `State` 推**（另一只手的 TCP × `Held.T_tcp_obj`，在 `State.base` 下），不用同步时的位置；另一只手的整只手（手指、夹爪、相机）在这些查询里不查（`Motion._query`，`other_hand_off`）：它握着这个东西、不动，它碰着的是自己手里的东西（11-12 T30：碗沿捏取时右手夹爪离碗 3 mm，左手的每个解都被它挡掉），它在世界里的位置由底盘模型的整机检查管。
  - 两条手臂相对底盘都不动、整机在动（底盘带门的任务段的采样点、停车点上的整机检查）：挂在另一只手的 held link 上，关掉世界里那份。"这条手臂 vs 它"这时是刚性的，不会变。

  同一个缺口也在反方向：一只手拿着东西在动时，它对另一条手臂也查不到（现在左臂平时收在底盘柱体里，没出过事）。手臂和 q_body 一起动、另一只手又拿着东西的段没有完整的查法，所以 4.1 的规则不让这种段出现。

  手里的东西是一组半径不等的球（`Motion.held_spheres` → `held_spheres.fit`）：贴着它的碰撞体拟合（容器取凸包，开口填实：装在里面的东西跟着手走），任何地方多出物体不超过 `OUT` 4 mm（小于 `LEAVE_GAP`，放下段终点不判碰），表面任一点离球不超过 `GAP` 6 mm（超过球数预算时按 ×1.25 放宽，日志写明）。预算 `HELD_SPHERES` 右手 140、左手 60：自碰撞只查它对躯干和头（下面的"每条手臂的自碰撞表"），但 cuRobo 的自碰撞内核每个球至少一个线程、球对缓冲只够 512 个线程，整个模型超过 512 个球就越界读（CUDA illegal memory access，11-11 试 160 / 160 时崩过）；机器人本身 305 个球，剩 207 个，迁过来的 pick / place 都用右手。球按几何缓存在磁盘上（`ZENO_CACHE`，大物体第一次拟合要十几秒）；增加的开销是和世界的查询；
- 把 `objects` 和 `parts` 同步到碰撞世界；
- 按 `Spec` 开关手指碰撞球、目标豁免、`touch`。

只改和同步时不同的，退出时全部复原。6a 起是直接实现，不再包旧的上下文管理器；旧的按用途分的那几个（`Motion.scope`、`hand_open`、`carrying`、`released`，`Rig._planning`、`_fingers_checked`）还留给旧入口用，第 10 步删。`touch` 的"其余部位照查"由 `Motion.path_free_only` / `Kinematics.path_free_only` 另查一遍，`primitives.free_path` 把两次查询合起来。

**每条手臂的自碰撞表（11-12 加，`motion.arm_self_collision`、`HELD_SELF_BODY`）**：两条手臂的 cuRobo 模型各从同一份配置拷贝，自碰撞表按手臂裁：
- 留下共用表（`zeno_malo.yml`，左右对称，16171 对）里有这条手臂的对：它对身体（升降滑块、躯干、头底座、头、头上相机）、它自己内部、它对另一条手臂；
- 去掉另一条手臂内部、另一条手臂对身体（规划这条手臂时另一条锁住、挂在躯干上，距离只对滑块随弯腰变），身体之间本来就不查；
- 加上这只手的东西对躯干、头底座、头、头上相机（`HELD_SELF_BODY`，43 个球）；对滑块放不下（右手 140 × 20 = 2800 对）；另一只手的 held link 不参与。
右臂模型 9360 + 140 × 43 = 15380 对，左臂模型 9360 + 60 × 43 = 11940 对，都在快速内核的 16384 以内（`arm_self_collision` 断言）。起点就有东西的球压进躯干或头（之前没查过的搬运姿态）时，那几个球关掉、记 `held_collision ... in the body`（`Motion._held_off_body`，`scope` 和 `query` 里），不然每条规划都因起点自碰撞失败；同样的思路见上面"还碰着东西时关掉"。
查不到的：手里的东西对滑块、对两条手臂（另一条手臂在动时把它当世界障碍物避开）；一只手的手指对另一条手臂（双手交接）；另一条手臂对滑块。

**机器人自己的底盘（11-12 加，`zeno_skills/body_collision.py`、`scene_geometry.body_world`）**：手臂模型里只有升降滑块、躯干、头和两条手臂有碰撞球，底盘（底座和上面的立柱）没有，所以手臂、手、手里的东西都查不到它。T05 homework_ready 里，焊在手上的作业本在去 `flat_pre` 的路上卡在立柱上，两个腕关节被顶到限位，旧代码的全量里也是这样。做成机器人的球放不下：快速自碰撞内核最多 16384 对、共用表用了 16171 对，整个模型最多 512 个球、现在 505 个；通用内核又太慢。所以底盘是同一个碰撞检查器的第二个环境（`BODY_ENV`）：
- 形状就是底盘规划量出来的两层（`collision.py`）：立柱一个长方体；底座的圆角方形用 4 个长方体拼（每个的角落在圆角弧上，最多比真形状少 1.2 cm）。不用网格：cuRobo 只在网格表面附近找，底座里面 12 cm 的点读成不碰。
- 它跟着底盘走：`_Arm.prepare` 按这次查询的底盘位姿原地更新（`place_body`，两条手臂共用一份，CUDA graph 里也成立）。
- 每个查世界的 rollout（`MotionGen` 里的 IK、图搜索、轨迹优化、精调，共 24 个）多一个代价项和一个约束项查 `BODY_ENV`（`body_collision.attach`；`ArmBase.cost_fn` / `constraint_fn` 的补丁，在求解器捕获 CUDA graph 之前装上）。检查器、权重、扫掠和世界那一项相同，激活距离多 `BODY_GAP`（= `LEAVE_GAP`：零余量时，贴着立柱搬运的作业本在下一段起点读成压进立柱 0.6 mm、被从模型里拿掉，接着就穿过立柱，T05 homework_ready 11-12）。只查这条手臂、它的手和手里东西的球（`body_collision.kept` + `index_select`）；身体（`BODY_LINKS`：升降滑块套在立柱上、躯干和头贴着它，本来就算碰）和另一条手臂（这一段里不动）不查。只动 q_body 的段（姿态，第 6 节）里另一条手臂跟着身体动：`plan_posture` 用另一只手的链按同样的身体值再查一遍，它自己的模型查它对世界和底盘（11-16：躯干降到最低时，收起的左臂压进底盘）。起初是把整组球拷一份、把不查的球半径设成 −1（cuRobo 跳过负半径的球），每个仿真多占 3.8 GB 显存（T29 several，11-12），改成只取要查的球。这样是规划器自己绕开底盘，不是事后拒绝。
- 我们自己的检查走同一个判据：`free` / `path_free` 经 `check_constraints` 用的就是 rollout 的约束；`near`、`contact_extent`、`explain` 用的 `_sphere_depths` 也查一遍 `BODY_ENV`（这里是把不查的球半径设成 −1 再查，`body_collision.masked`）。
- 手里的东西是 held link 上的球，和手臂一样查底盘。另一只手里的东西照旧（上面两种表示）。
- 没覆盖：停车点和开车的整机检查（`base_depths`）不查它（底盘和立柱随底盘一起动，手臂相对底盘不动时它们之间的关系不变）。
- 检查：`tools/check_body_collision.py`（GPU，不起仿真）：立柱、底座的位置对；收起、下垂、行驶姿态离立柱 7–8 cm、可行；随机采样到手臂伸进立柱 3 cm 以上、去掉底盘就可行的姿态，加上底盘全都不可行。

### 4.5 阈值常数：一处出处（`tolerances.py`）

迁移前散在十来个文件加一份文档（下表是 11-11 第一批之前的样子；搬过以后的现状见表后的两批和"后来加的"）：

| 在哪 | 有什么 |
|---|---|
| `rig.py` 顶部 | 约 20 个：`BIG_SWING`、`CARRY_VEL`、`RIM_VEL`、`SETTLE_*`、`DRIVE_*`、`HELD_CHECK_EVERY`（inherited, unmeasured）…… |
| `primitives.py`（复核） | `PLAN_AT_START`、`EXTENT_TOL`、`TARGET_TOL`、`TARGET_TURN`（`holds` 的判据） |
| `primitives.py` | 9 个：`LEAVE_GAP`、`LEAVE_MARGIN`、`LEAVE_MAX`、`ON_LINE`、`ON_LINE_TURN`、`JOINT_GOAL_TOL`、`DENSE`、`HINT_REACH`、`HINT_TURN`（`rig.py` 再导出后两个） |
| `kinematics.py` | `REST_TOL`、`STOWED_TOL`、`CARRY_TILT` |
| `skills.py` | `CARRY_Z`、`PICK_REACH_TOL`（= `TARGET_TOL`）、`APPROACH_STEP`、`PICK_LEAVE_CHECK`、`AT_PARK_M` / `AT_PARK_DEG`（inherited, unmeasured）、`CARRY_SPOTS`、`PLACE_*` 代价…… |
| `skill_plans/` | `HELD_POSE_MARGIN`、`PICK_TOL`（= `HINT_REACH` / `HINT_TURN`，`pick.py`）、`PLACE_TOL`（= `TARGET_TOL` / `TARGET_TURN`，`place.py`）、`SETTLE_TICKS`（`place.py`）、`SAME_POSTURE`（`navigate.py`） |
| `skill_jobs/` | `CARRY_FRONT_X/Y`、`CARRY_LOW_TOL`、`CARRY_LOW_COST`（`carry.py`）、`PICK_CAND_COST`（`pick.py`）、`FRONT_SEED_M`（`door_access.py`） |
| `park_search.py` | `RADII`、`YAW_OFFSETS`、`REACH_XY`、`MAX_PER_GOAL`、`BUILD_S`、`BUILD_MAX`…… |
| `base_planner.py`、`collision.py` | `DEPTH_TOL`、`FOOTPRINT_MARGIN`（inherited, unmeasured）…… |
| `COLLISION_PLAN.md` 第 8 节 | 力的几何替身（`PRESS_DEPTH`、`WIPE_PRESS`、`TOUCH_DEPTH`……） |
| 还没有 | 任务段的余量（8.2）；`TARGET_TOL` 5 mm、`PICK_TOL` 1 mm 都没有实测（8.4） |

**已做第一批（11-11，9.3 第 2.1 步）**：`zeno_skills/tolerances.py` 收了锚点误差上限、复核判据和原语的接触几何——`LEAVE_GAP`、`LEAVE_MARGIN`、`LEAVE_MAX`、`ON_LINE`、`ON_LINE_TURN`、`JOINT_GOAL_TOL`、`HINT_REACH`、`HINT_TURN`、`BASE_TOL`（还没有代码用）、`HELD_POSE_MARGIN`、`HOLD_DRIFT`（`None`，待测）、`PLAN_AT_START`、`EXTENT_TOL`、`TARGET_TOL`、`TARGET_TURN`、`PICK_TOL`、`PLACE_TOL`、`DOOR_TOL`。每个是 `_t(名字, 值, 单位, src)`，登记在 `TOLS`；`primitives`、`skill_plans` 从这里导入，原来的名字照旧能用（`primitives.TARGET_TOL` 等）。上表其余的（旧代码的、执行参数、搜索预算和代价）随迁移它们的那一步再搬。

**已做第二批（11-11，值都没变）**：新架构代码在用、还散在别处的判据和余量也收进来，各带来源，写了两遍的同一个量合成一个名字：
- 复核和判同：`SAME_POSTURE`（原 `skill_plans/navigate.py`）、`SAME_PARK`（`motion_skills._same_pose` 写死的 1e-4 m / 1e-2°）、`NUMERIC_M`（`skill_plans/_common.py` 两处写死的 1e-3 m）、`MOVED_MM`（`motion_state`）、`REST_TOL` / `STOWED_TOL`（`kinematics`）；`plan_navigate` 判手臂已在休息姿态的写死 1e-3 rad 并进 `PLAN_AT_START`。
- 规划器的碰撞模型（4.4）：`POS_TOL` / `ROT_TOL` / `ACTIVATION`（`motion.py`，cuRobo 的阈值）、`DEPTH_TOL`（`base_planner`；`park_search` 里写死的同值 1e-4 并进来）、`FOOTPRINT_MARGIN`（`collision`）、`HELD_SPHERE_OUT` / `HELD_SPHERE_GAP` / `HELD_SPHERE_GAP_MAX`（`held_spheres` 的 `OUT` / `GAP` / `GAP_MAX`，原名照旧可用，缓存键不变）、`CARRY_TILT`、`CARRY_LOW_TOL`、`CARRY_SUPPORT_Z`（`skill_jobs/carry.py` 写了两遍的 0.3–1.0 m）、`FLOOR_Z`（`skill_jobs/pick.py` 写了两遍的 0.05 m）。
- 接触监视：`MIN_DEPTH`、`MOVED_M`、`MOVED_TILT`、`CARRIED_M`、`APPROACH_MOVED_M`、`APPROACH_TURN`（`clearance`）、`SNAP_NEAR`（原 `sticky.NEAR`）。
- 技能 hook 的成败判据：`SHUT`（`sticky`；`_pick_judged` 写死的同值 0.003 并进来）、`GRIP_CLOSED_BY`、`PICK_RISE_MIN` / `PICK_LIFT_FRAC`（`_pick_judged`）、`HELD_SLIP` / `HELD_SHIFT_MAX` / `HELD_SHIFT_GAP` / `HELD_LOST_GAP`（`check_held`、`check_left_held`、`policies/bimanual.py` 两处同一条"掉了"的规则）、`PLACE_LEVEL_MIN`、`PLACE_XY_TOL` / `PLACE_XY_TOL_CORNER`（place 的 `done`，10 / 12 cm：任务的容差，不是运动的 `PLACE_TOL`）、`HANDLE_FINGER_MIN` / `HANDLE_GAP`（握上把手：`skill_jobs.door.handle_closed_on`，`open_job` 和旧开关门路径共用）、`HAND_OPENED_FRAC`、`DOOR_OPEN_TOL` / `DRAWER_OPEN_FRAC` / `DOOR_CLOSED_TOL`（开门结果，新旧两处）、`RIDE_DONE_REV` / `RIDE_DONE_PRIS` / `RIDE_OVERSHOOT`（原 `skill_jobs/door.py` 的 `DONE_REV` / `DONE_PRIS` / `OVERSHOOT`）。
- 执行的到了 / 停了：`SETTLE_TCP`、`SETTLE_STILL`、`RIDE_STALL`、`RIDE_SLIP_LEADS`（`rig`）。
- `skills.PICK_REACH_TOL` 删掉（它就是 `TARGET_TOL`），`skill_jobs` 直接用 `TARGET_TOL`。

原模块里的名字照旧导入着（`clearance.MIN_DEPTH`、`base_planner.DEPTH_TOL`、`kinematics.REST_TOL` 等），改名的只有上面括号里写明的几个。仍不在这里的：执行参数、搜索预算和代价、`predicates.py` 的任务判定（评测层），以及旧代码（`skills`、`policies`）自己的阈值——随迁移再搬。

**后来加的（11-11 以后，随迁移的那一步）**：开关门的 `DOOR_LEAVE`（第 6 步）；推门的 `PUSH_ABOVE`、`PUSH_PRE`、`PUSH_TIP_GAP`、`PUSH_TRACK`、`BODY_SAME`（6b）；推桌上的物体的 `SLIDE_GAP`、`SLIDE_PAD_GAP`、`DRAG_RIM`、`DRAG_PRESS`、`DRAG_SKID`、`SLIDE_TOL`、`PUSH_DONE_TOL`、`PUSH_MOVED_MIN`（第 7 步）；机器人自己的底盘的 `BODY_GAP`（4.4）；探索的判据 `COVER_MIN_AREA`、`COVER_Z`、`COVER_MIN_CLEARANCE`、`COVER_OK`（第 3 步，11-16，都是 inherited, unmeasured；扫视的角度、步数和 `VIEW_TRIES` 是执行参数和预算，留在 `perceive.py`）。

原来的目标：新架构用到的阈值集中到 `tolerances.py`，按**属于哪一层 / 哪一类误差**分组，每个带单位和**来源标记**：

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
- "倾斜超标"各处是同一条规则（`kinematics.carry_tilt_allowed`，11-14 起）：持物的一次移动里，物体相对起点的倾斜最多比目标本身的倾斜多 `CARRY_TILT`（0.15 rad）。关节直线（`tips_over`）、关节规划（`_plan_js`）、位姿规划（`plan_to`）都按它查。目标离起点不超过 `CARRY_TILT` 的（`holds_level`），超标了才保持倾角重新规划；cuRobo 的保持倾角（`Arm.tilt_metric`）从第一步起就保持**目标**的倾角，所以完美保持的轨迹本来就倾斜了目标那么多。以前 `_plan_js` 从起点算 0.15，T23 放勺子目标本身就离起点 0.11，只剩 0.04。目标本身倾斜更多的（侧放的盒子）是有意转动物体，同样按这条规则限住路径，只是没有倾角可保持。
- cuRobo 位姿规划失败时，只要开着 finetune，状态一律报 `FINETUNE_TRAJOPT_FAIL`，第一轮轨迹优化根本没有可行种子、finetune 没跑也一样（`finetune_time` 为 0）；这种情况改报 `TRAJOPT_FAIL (no feasible seed)`（`motion.plan_status`）。
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

`primitives.drive(base, state, goal, chain, name)` 和 `drive_straight(base, state, target, name)`，`base` 是 `motion_state.BaseModel`（2.5）。产出一段 `kind="drive"`：`info["steps"]` 是开车和换姿态的序列，`q_from` / `qs` 是起点和每次换姿态后的整机姿态（`Posture.vec()`：body + 右臂 + 左臂 16 维，4.1；所以 `q_end` 是开完以后的姿态）。`run.execute` 交给 `Actuator.drive_base` / `swing`；`holds` 只查整机姿态在起点（路径是 navigate 计划时从同一个状态做的）。`skills.relocate` 和 `straight_base_move` 都改成"构造这一段 + `run.execute`"。

两种：
- **规划的**：从 `State.base` 到目标底盘位姿。包现在的 `_base_plan`（`base_planner`）：整机碰撞，手里的东西也算，手臂从 `State` 里的姿态出发；路上折叠放不下的地方换成下垂，在哪换由底盘规划器定（`travel_postures` / `posture_sets`），换姿态是一次查过碰撞的关节直线（`Rig.swing`）。一段 `drive` 就是规划器给出的这一串（开车，换姿态，开车……），执行照旧交给 `drive_base` / `swing`。用于 navigate。
- **直线**：沿给定方向退开到离障碍物 d。方向由任务给（离开障碍物外框上最近的点），整机沿直线查碰撞，挡住就 Failure，不动。包现在的 `straight_base_move`。用于 retreat，属于进出接触段（第 3 节）。

做完推进 `State.base`。路径是轨迹（8.1）：搜索时只证明开得到，执行时由 navigate 的计划用同一个函数、同一组行驶姿态重新规划。技能自己的计划不含 `drive`，从停车点开始，第一段是到达锚点；任务过程中要动底盘的（开门时底盘跟着门、推一段），是 `scripted` 段的 `carry="base"`：底盘位姿是任务量的函数（`ride_base`，5.5），不是 `drive`。

### 5.5 `scripted`：任务段（9.3 第 6 步加；开门、关门、推桌上的物体在用）

任务段的出处是技能的轨迹函数 `traj`（2.3、9.4：和它的 `build` 同一个文件）。它给出的是**函数和区间**（3.1），不是一串路点：`traj(state, params) -> Script`。

```python
Script(coupling, s0, s1, step, tcp=None, carry="base" | "arm")      # primitives.py
```

- `s0` → `s1`：任务量的区间（铰链角、抽屉位移、画圈相位……），第 3.1 节的三条由这个形状保证：段里只有 `s` 的函数，没有可以手挑的关节角。
- `coupling`（耦合）：`s` 变的时候什么跟着动、工作点写在哪个坐标系里。和"还在碰"的判据一样是具名的（`primitives.COUPLINGS`），每个有三个方法：`value(state)`（`State` 里现在的 `s`，不动东西的耦合给 None）、`moved(state, s)`（`s` 处的 `State`）、`frame(state, s)`（坐标系在 `s` 处的世界位姿）。现在有：
  - `hinge(部件, pose)` / `slider(部件, pose)`：手握把手，部件关节值就是 `s`（`PartAt`）。`pose(v)` 是部件框在关节值 v 的世界位姿（标注的 `part_pose`），由技能的 job 传下来，②③ 层不碰标注和 rig；
  - `still(物体)`：什么都不动，坐标系是 `State` 里的那个物体（搅拌的锅、擦的桌子）。
  - `pushed(物体, T0, n, lag)`（推桌上的物体，11-12 加）：`s` 是手沿水平方向 `n` 走了多远，坐标系是手的（`T0` 平移 `s`），所以 `tcp` 为 None（刚性）就是手顶着物体走。物体比手晚 `lag`（死区：推开始时手指离物体还有这么远）：`moved` 把物体放在 `T0` 平移 `max(0, s − lag)`、不转——这是计划的预测，推完的锚点读实测。`value` 是物体沿 `n` 离 `T0` 的位移（不是 `s`；`part_start` 按它判能不能开始：开始时是 0）。`frame` 和 `moved` 分开，正是因为手和物体差一个死区。
  - `rolled` / `pivot`（滚、翻）随第 7 步加。推门不用 `pushed`：门板是刚体，只绕铰链转，推和握的区别只在手不握（没有 `Held`）、`touch` 写明哪个部位贴门，耦合照样是 `hinge`（第 6 节关门）。`pushed` 留给推桌上的物体（会滑、会转）。
- `tcp(s)`：TCP 在这个坐标系里的位姿。None = 刚性：保持 `s0` 时手和坐标系的相对位姿（握着把手）。有工具坐标系以后换成工作点（`T_tcp_tool`，第 6 节接触类）。
- `carry`：机器人怎么跟。
  - `"base"`：手臂不动，底盘和坐标系刚性地一起动（底盘带门）：`ride_base(script, base0, s) = F(s) · F(s0)⁻¹ · base0`，`F` 是 `coupling.frame`。只用于 `PartAt` 且 `tcp` 为 None；
  - `"arm"`：底盘不动，手臂跟着 TCP 走：从起点的关节角起，相邻两个采样之间用运动学直线（`cart_path`，不查碰撞）接着解 IK，分支连续（"关节侧沿 `s` 连续跟"，3.1）。
- `step`：计划查碰撞的 `s` 步长（按角度或位移，2.4）。执行按自己的控制步长对同一个函数求值。

`scripted(kin, state, spec, script, name, base=None, track=None, reach=False)` 产出 `kind="scripted"` 的段：

- **起点**（`part_start`）：底盘带门的，部件的实测值在 `[s0 − lead, s1]` 里（指令值从实测值起步、不出 `[s0, s1]`，比 `s0` 再往回一个 `lead` 底盘就一开始跟不上）；手臂跟的，离 `s0` 不超过 `TARGET_TOL`（手和部件从 `s0` 起刚性）；给了 `tcp` 的，手臂的 TCP 离 `F(s0) · tcp(s0)` 不超过 `ON_LINE` / `ON_LINE_TURN`。不满足返回 Failure。
- **查碰撞（搜索和执行同一个函数）**：在 `script.samples()` 的每个 `s` 上，按 `coupling.moved` 把部件 / 物体挪到位，按 `Spec` 查（`touch` 和手握的部件只对指定部位放开，其余部位另查）。`carry="base"`：底盘在 `ride_base` 处，`BaseModel.clear` 查底盘本体（对静态世界和这一刻的部件），`free_at` 查整机；`carry="arm"`：查两个采样之间那段 IK 延续的手臂运动（部件在后一个采样处）。有一处不通就返回 Failure：全有或全无，不跳点。`reach=True`（只给 `carry="arm"`）：IK 延续解不出的地方，段结束在前一个采样（手臂能走多远就走多远：推到够不着为止，段长是量出来的），`info["script"]` 换成到那里为止的 `Script`；碰撞照样全有或全无。门扫过的扇形对家具（2.4 表第三行）还没查。
- **段里存什么**：`info["script"]`（函数本身）、`base0`（构造时的底盘）、`rel`（`s0` 时 TCP 在坐标系里的位姿）、`executor`、`track`；`carry="arm"` 时 `qs` 是 IK 延续出的手臂轨迹（和 `straight` 的路点一样是轨迹，8.1），`s_at` 是每个路点对应的 `s`；`carry="base"` 时 `qs` 为空（手臂不动）。
- **执行器**：
  - `follow`（`carry="arm"`）：照 `qs` 开环走，用于推桌上的物体（`pushed`）、画圈、擦条带、转腕，以及手臂走门的圆弧；
  - `ride`（`carry="base"`，`Actuator.ride` / `Rig.ride`）：闭环，底盘跟着实测开度走。每个物理步对**同一个函数** `ride_base` 在指令值 `cmd` 处求值，不在计划的采样点之间插值，也不出 `[s0, s1]`；`cmd` 以不超过 `rate` 的速度追"实测值 + `lead`"。部件到 `done` 算完成；卡住（`RIDE_STALL`）、超时、或者突然落到 `cmd` 后面 `RIDE_SLIP_LEADS`（2）个 `lead` 以上（把手滑脱、门弹回）就停下，`run.execute` 抛 `SkillFailure`。正常跟着走时，落后量按构造不超过 `lead` + `rate` / `PHYSICS_HZ`（指令往两个方向都追实测值），所以这条线不用实测来定，只用来认出"滑脱"；没开到位由卡住判据和技能的结果检查接住。闭环只调节怎么跟，不改几何。`ride` / `ride_end` 事件记落后量和底盘离指令的距离（任务段余量的数据，8.2）；`lead` / `rate` / `done`（`TRACK_KW`）由技能的 `build` 给。旧的 `skills._ride` 没改，开关门迁过来以后只剩微波炉在用，第 8 步删。
- 任务段后面跟一个锚点（8.2），用实测的部件值 / 物体位姿推进 `State`。

### 5.6 动作

不动手臂、推进 `State` 的段：
- `grip(width)`：合爪 → `holding`，松手 → `released`；
- `wait(ticks)`：物体停稳，什么都不动（`place_settle`）；
- `head(yaw, pitch, steps)`：转头（`perceive.head_segment`，感知类和 `run_skill` 开头的头摆正都经它，11-16）；手臂、底盘、手里的东西都不动，所以不向接触监视声明，前一段的 `Allow` 照旧；
- `drive_part(部件, 值)`：电机开关门（`Actuator.drive_part` → `Rig.drive_part`：关节目标在 300 个物理步里匀速给到、再等一秒，离目标超过 `DOOR_OPEN_TOL` 技能失败），开门键按键计划里的一个动作（8b，11-24）；
- `toggle(电器, on/off)`：电器的热源开 / 关（`Actuator.toggle` → `Rig.toggle`，任务级的 `thermal.py`），按键计划在手按到按钮以后的一个动作（8a，11-24）。

现在有 `grip`、`wait`、`head`、`toggle`、`drive_part`；`run.execute` 遇到别的动作抛 `ValueError`。

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
- `prior`：搜索时是排序 IK 给的 {决定名: 关节角}；执行时重做是当前 `Plan`。每个运动段先看 `prior` 里同名的段从现在的起点是否还成立（`holds`，8.4），成立就原样拿来（`skill_plans._common._kept`）：动作和锚点在哪都成立，每次重做（复用一个为别的起点做的会把那个起点带下去）；搬运段按构造时的规则查（合爪前假设的握法带 `HELD_POSE_MARGIN`）；收臂段不复用（每次按收起优先重新选）；底盘带的任务段（骑门）也不复用：它的底盘轨迹相对起步时的部件值（`ride_base`），部件在 `lead` 以内动过时它仍然成立，保留旧段会把旧的起点带下去（和动作、锚点同一个理由），推这种手臂带的任务段照常复用。可复用的段的种类只有一处定义（`motion_state.KEPT_KINDS`，`_kept` 和 `run` 的锚点日志共用）。不成立再用原语做，要做决定的（`decide_ik`、目标集合的序号）先试 `prior.decisions` 里的值。
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

navigate(x) 只负责开到 x 那一带，停车点由后面的技能自己选（2.3、第 10 节）。x 是物体、支撑面或家具时（11-16 起后两种也算，见 ../skills/navigate.md），"那一带"里先取头部相机看得到它的站位（`NavigateToPlacePolicy` 的 `_in_view_poses`：到达姿态的躯干和腰、按 look 的瞄法把头对准它，`perception.in_view_from` 判视锥和家具盒视线，和 look 同一判据；不算动态遮挡，观测受限的 benchmark 里没见过的物体不能左右底盘停哪）；能到的站位一个都看不到才取最近的，这时 look 如实失败。look 和 benchmark 的观测门（navigate 后看一眼，接触技能要物体在视野里）都要它看得见：头最多低 18°，地上的物体离底盘不到 0.60 m（7.5 mm 镜头）/ 0.81 m（10 mm）就出了视锥（11-14 T23 belongs_on_floor），站位也可能被家具挡住视线（T23 dropped_out_of_view 的盆栽）。

**retreat**：一段直线 `drive`（5.4），挡住就失败。

**开门**（`skill_plans/door.py` 的 `plan_door`，job 在 `skill_jobs/door.py`，到达姿态是收起；11-10 迁移，11-11 跑仿真后的修正见 9.3 第 6 步；物理步骤见 `../skills/open.md`）：

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
| 10 | 离开（`door_leave`） | `straight` 沿接近方向反着退固定的 `DOOR_LEAVE`（17 cm，从骑门结束时手的位置算）。`contact_extent` 在门上量出 0 m（张开的钩子离把手比接触间隙远），11-11 弃用（f418f58、cbf8eec） | 手指可碰部件 | — |
| 11 | 收臂 | `free_leg(JointSet{收起, 下垂})`，不复用 | `FREE_HAND` | — |
| 12 | 停稳 | 动作 `wait` 60 帧 | — | — |

抓法变体（侧钩不倾斜 / 10° / 20°、两端、正面捏）是 `Problem.goals`。停车点只按通用排序（第 7 节）：旧代码按力矩比挑停车点（`planner.find_park(score=torque_ratio)`），第 7 节不要 `score` 这类开关，迁移时去掉了；要是仿真里出现停车点选得腕关节拉不动门，改成 `build` 里的约束（握把手的解上力矩比超过关节上限就不要这个停车点，底盘带门时整段受力方向不变，算一次就够）。中继位姿是把手前那一点（`DOOR_RELAY` = `door_reach`）。整个过程只握一次。

还没做：手臂走圆弧（`carry="arm"`）作为目标集合里的另一种做法（第 10 节）；微波炉（第 8 步）。一只手拿着东西时用另一只手开门在第 6b 步做了（`skill_jobs.door.door_hand`：只有一只手空就用那只，两只都空用右手），v6 里没有这种集，还没在仿真里跑到。

**关门**（9.3 第 6b 步，11-12，a33d852）：`skills.close_articulated` → `run_skill(SKILLS["close"])`，job 是 `skill_jobs/door.py` 的 `close_job`，推门的计划是 `skill_plans/door.py` 的 `plan_push`（catalog 的 `template`），握把手关是同一个 `plan_door`。微波炉和没有把手的部件还走旧的 `_move_with_retry`（第 8 步）。迁移前是：铰链门先推（`_push_close`），找不到推的停车点再 `try/except` 换成握把手（`_move_articulated`，两次抓的老路径）；合约的 `handle_push`、`dispatch` 两条路径都要求 `hand_empty(hand=right)`。

v6 批次（153 集）里的 44 次关门：柜门空手 12、柜门右手拿着东西 10、冰箱空手 11、冰箱右手拿着东西 3、微波炉 8；没有抽屉，也没有左手拿着东西的。右手拿着东西的 13 次都是"柜里 pick → 退开 → 关门"，现在全被 `hand_empty(hand=right)` 拒掉（11-11 侧面捏取以后，T02、T19、T25 都停在这里）。

```
close(部件)
├─ 已经关着（差 RIDE_DONE_REV 以内）→ 不动
├─ 微波炉 → 旧代码（第 8 步）
└─ 有把手的门 / 抽屉 → close 技能：一次停车点搜索，目标集合 = 空着的手 × 做法
       做法：推（合拢的指尖按门板外侧）、握把手骑着关（只有右手空时）
       两只手都拿着东西 → 失败
```

- **手和做法都是目标集合的维度**（第 7 节"哪只手"）：不是先试推、推不了再握，也不是先试右手、不行再换左手。代价：推在握前，同一种做法右手在前，排名每靠后一位加 `VARIANT_COST`。这只是弱偏好：`score` 里候选代价乘 `PARK_DIST_W`（0.5），一位 `VARIANT_COST`（0.05 m）只值 0.025，可操作度那一项是 0–1 的量级，两只手都空时左右实际按可操作度选。接受这一点（哪只手手臂状态好用哪只）；要真的右手优先，得在排序里按（手，score）分层，第 7 节。
- 右手拿着东西时只剩左手推。右手空时左手推也在集合里：机器人站在门轴那一侧时，可能右手够不着、左手够得着。
- 拿着东西的那只手不动：推的那只手的段锁住 q_body（4.1），所以另一只手和它手里的东西在世界里静止，作为世界障碍物、位置从 `State` 推（4.4），推的手臂对它照查；底盘带门那一段两条手臂相对底盘都不动，它挂在 held link 上随底盘查对世界（11-12 仿真里查到过"右手的罐子撞柜子"被这样拒掉）。
- 锁了 q_body 推不到低处的柜门：另一只手拿着东西时，推之前先单独一段 `push_body` 只动躯干（升降不倾斜，手里的东西保持水平；腰锁住），高度不是手写的，是推点前那一点在"躯干可动、腰锁住"下的 IK 解里的躯干值（先用停车点排序的解）。停车点搜索的排序 IK 也按同样的锁解（`Problem.body_free`，第 7 节），不然排出来的停车点都要靠弯腰，构造预算全花在用不上的点上（11-12：T20 柜门 6 排序不锁时 43 次"够不着"，锁了以后第 10 个就成了）。
- 握把手关只给右手：就是 `plan_door`，`s1` 换成关着的值（关节到不了关着再过一点，所以 `s1 = closed_q`，`done` 在它前面 `RIDE_DONE_REV`）；握法照开门的 `_ways`。左手握把手先不放进集合：右手拿着东西的 13 次用左手推就够，要加时是同一个 `plan_door` 换成左手的 `kin`（6a 以后不用另写）。
- 推门关（`plan_push`，和 `plan_door` 同一个文件）：

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达（`push_arrive`） | 锚点：底盘、部件值 | — | 实测 |
| 2 | 合爪 | 动作 `grip(0, side)` | — | `with_width(0)` |
| 2b | 躯干（`push_body`，只在另一只手拿着东西时） | `free_leg(Joint)` 只动躯干到推点前那一点 IK 解的高度，平滑 | `joints=("torso_lift_joint",)`、`arms_still` | 躯干 |
| 3 | 到推点前（`push_reach`） | `free_leg` 到门板外 `PUSH_PRE`（10 cm），起点的解由 `decide_ik` 定（`_reach`）；容差 `DOOR_TOL` | `FREE_HAND` | — |
| 4 | 贴上门板（`push_in`） | `straight`；容差 `DOOR_TOL` | 手指可碰部件（`touch_part`） | — |
| 5 | 推（`push_ride`） | `scripted(Script(hinge(部件, part_pose), 现在的值, closed_q, carry="base"))`，执行器 `ride` | 手指可碰部件 | `with_part(closed_q)`、底盘到 `ride_base` |
| 6 | 关上（`push_moved`） | 锚点：部件值 | — | 实测 |
| 7 | 离开（`push_leave`） | `straight` 沿门板法向退 `DOOR_LEAVE` | 手指可碰部件 | — |
| 8 | 收臂 | 推的那只手 `free_leg(JointSet{收起, 下垂})`，只到手臂的 7 维、q_body 保持（4.1），不复用 | `FREE_HAND` | — |
| 9 | 停稳 | 动作 `wait` 60 帧 | — | — |

  - 推点和手的朝向写在部件坐标系里（`Aim(frame=part_pose)`），由标注推出，沿用旧 `_push_targets` 的规则：门板外侧（把手那一面）、把手上方 `PUSH_ABOVE`，合拢的手指沿铰链轴排开。门开着时外侧朝门轴那边，所以机器人站在门轴一侧推。推点在把手上方和下方各一个（`PUSH_HEIGHTS`，目标集合里的两个做法）：台面下的柜门，上方那个快关上时夹爪和相机会撞台面（11-12 仿真）。
  - 推的时候整只手（手指、夹爪、相机）都可以碰这扇门（`Spec.touch` 写 `(门, "hand")`），手臂其余部分照查；旧代码是整只手对整个世界都不查。
  - 和开门只差两条：不握（没有 `Held(kind="part")`，`touch` 写明手指可碰这扇门），推点不是把手。耦合照样是 `hinge`，执行器照样是 `ride`：指令值以 `rate` 追"实测 + `lead`"，手在门前面最多一个 `lead`；门被推得往前多摆（实测超前）不算滑脱，推不动时手最多压进门板一个 `lead`，然后按卡住停下。所以不加 `pushed` 耦合（5.5）。
  - 旧代码按力矩比挑推的停车点、最近不许近过 `PUSH_MIN_R`，都去掉：停车点只按通用排序（第 7 节），手臂贴身推不了的由 `build` 的 IK 和碰撞判定拒掉。仿真里要是推不动，按开门那条处理（力矩比做成 `build` 里的约束）。
- 合约（做成了另一种样子）：不合并 `handle_push` / `dispatch`，在它们前面加一条 `loaded`（有把手且右手拿着东西：只调 policy_023，不先收臂——policy_003 只收右臂，右手拿着东西时它拒绝；前提 `hand_empty(hand=left)`）。右手空的照旧走 `handle_push`（先收臂再关，job 里两只手都在目标集合里），这样空手关门的路径不变；微波炉的 `powered` / `powered_loaded` 不变。开门 `contract_048` 同样加 `refrigerator_loaded` / `loaded`（右手拿着东西：左手开），删掉 `left_holds_load`（policy_060 退役，`skill_library/check.py` 的 `RETIRED_POLICIES`）：左手拿着东西时照常走 `refrigerator` / `drawer` / `hinged_door`，右手开、q_body 锁住。
- 结果判据沿用 `DOOR_CLOSED_TOL`（铰链 0.10 rad、抽屉 4 cm）。
- 删了 `_push_close`、`_push_targets`（搬进 `skill_jobs.door.push_target`，写在部件坐标系里）、`_NoPushPark` 和旧的 `PUSH_*` 常数（`PUSH_ABOVE`、`PUSH_PRE` 留下，进了 `tolerances.py`；`PUSH_MIN_R`、`PUSH_OUT`、`PUSH_SPREAD` 不要了）。`skills._ride` / `_ride_check` / `_move_articulated` / `_move_with_retry` 还留着：微波炉的开关门还在用，跟第 8 步走。
- 检查：空手关柜门、右手拿着东西关门的 T02 block_put_away、T19 can_put_away、T25 cold_one、T05 pen_in_6、T20 bottle_put_away（`/data/zenobench/close6b_1112`）。v6 里没有能走到空手关冰箱的集（11-12 全量的冰箱关门全是右手拿着东西的）。结果见 9.3 第 6b 步。
- 推门的常数（`PUSH_ABOVE`、`PUSH_PRE`、`PUSH_TIP_GAP`、`PUSH_TRACK`、`BODY_SAME`）在 `tolerances.py`，各带来源。
- 诊断（11-12 加）：直线撞了写出撞到哪个物体（`primitives._who`，`Motion.contacts_by_owner`），IK 解不出写明是够不着还是撞了（`ik_why`），停车点搜索的 `diag["build_examples"]` 每类失败留一条完整原因。

**接触类技能**（roll、flip、expose、sweep 待做；push 11-12、stir 11-15、press 11-24、touch / knock / wipe 11-25 已做）都是同一个形状：到达（锚点）→ 过渡段 → 进入段（`straight`，深度常数）→ 任务段（`scripted`）→ 锚点 → 撤出段（`straight` 或离开段）→ 收臂。工具的工作点（勺尖、海绵底面）是标注里的具名坐标系 `tool_frame`（和 `grasps` 一样写在 `annotations/assets.json` 的资产条目里），由一个函数统一解析成 `T_tcp_tool = Held.T_tcp_obj · T_obj_tool`（4.1），轨迹函数只拿这个矩阵。不要让 10 个接触技能各自从标注换算一遍：那是未来重复代码的主要来源，也是最容易和标注失配的地方。新加一个工具 = 加一条标注，不是加一段代码。跨多个停车点的任务（长推、sweep 逐个物体）每段做一次 `find_park`，段与段之间看实测结果决定下一段。这是任务层的闭环，不是运动的退路。长推每段推多远不写死（`COLLISION_PLAN.md` 第 2 节）：选沿推的方向能推得最远的停车点，推到够不着为止，再换停车点接着推（11-12 已做，见下面推桌上的物体）。

**推桌上的物体**（`plan_slide`，`skill_plans/contact.py`；catalog 的 `push`，job 是 `skill_jobs/slide.py` 的 `slide_job`；11-12，2d2aff1，第 7 步里先做的一项；物理步骤见 `../skills/push.md`）：推到桌边（policy_045 `SlideToEdgePolicy`）走它，抓伸出去的那条边是普通的 pick（policy_013 → `plan_pick`，`thickness_pinch` 候选），两者不合成一个 `build`：推完物体停在哪只预测得到厘米级（8.5），抓伸出去的边要按实测的位姿选抓法，合起来搜索时证明不了后面的抓；两步的停车点也不同。它们在任务层串（2.3 复合技能）。旧的 `skills.push` 删了（11-12）：push、push_from_behind、top_drag、pull、separate、center、sweep 也都走 `push_object`（这 7 个策略在 v6 里一次都没用到，11-12 全量的日志）。

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达（`slide_arrive`） | 锚点：底盘、物体 | — | 实测 |
| 2 | 合爪（`slide_close_hand`） | 动作 | — | 手宽 0 |
| 3 | 到下落起点上方（`slide_reach`） | `free_leg`，解由 `decide_ik` 定（`_reach`），种子是停车点排序解的推的终点（推不完时是排序量出的最远点）的 IK（relay `slide_end`：只排下落起点时，T05 记事本 15 个停车点里 14 个推到半路没有 IK）；容差 `SLIDE_TOL` | `FREE_HAND` | — |
| 4 | 下落（`slide_down`） | `straight` 竖直向下 `pick_approach()`（和 pick 的伸入段同一条规则：伸进去的是手指，手指长度 6.3 cm + `LEAVE_MARGIN`），落在推点后方 `LEAVE_MARGIN`（拖：直接落在推点上） | `FREE_HAND`（拖：手指可碰物体） | — |
| 5 | 贴上（`slide_in`，拖没有） | `straight` 沿 `n` 到推点 | 手指可碰物体 | — |
| 6 | 推（`slide_push`） | `scripted(Script(pushed(物体, T0, n, lag), 0, d + lag, carry="arm"), reach=True)`，执行器 `follow`：手推到手臂够不着为止，最多 `d + lag`（段长是量出来的，5.5） | 手指可碰物体，手臂其余部分照查（物体按每个采样的 `s` 挪到位，比手晚 `lag`） | 物体到 `s1 − lag`（预测）|
| 7 | 推完（`slide_moved`） | 锚点：物体 | — | 实测 |
| 8 | 离开（`slide_leave`） | `contact_extent(near_world)` + `contact_segment`：方向是离开推的那一面和支撑面（−n 和向上的角平分线，斜 45°；拖：竖直向上），长度量到离开 `LEAVE_GAP` 再走 `LEAVE_MARGIN`；什么都没碰着就没有这一段 | `LEAVE_CONTACT` | — |
| 9 | 收臂 | `free_leg(JointSet{收起, 下垂})`，不复用 | `FREE_HAND` | — |
| 10 | 张手（`slide_open_hand`） | 动作，留给下一个技能 | — | 手宽 0.04 |

- 推点写在物体的箱体框里（`Aim`），由 job 推出：从后面推，合拢的手指离后表面 `SLIDE_GAP`，高度用 top pinch 指垫的规则（`skills._pads_clear_of`），指垫要离开的表面也和 pick 一样取 `_surface_under`（支撑面和物体箱体最低点中较高的），但离台面 `SLIDE_PAD_GAP` 5 mm 而不是 2 mm（2 mm 时，同一位姿把剩下的计划重做一遍，退开的直线在路点之间碰台面：推的 IK 延续重做出来略有不同，T05 记事本 11-12）；推的段还成立时原样保留（`_kept` 也收 `scripted` 段），推进 `State` 用它自己的 `Script`；拖，按在顶面前沿往里 `DRAG_RIM`、TCP 高出顶面 `DRAG_PRESS`。
- 死区 `lag`：手要先走这么远才碰到物体，物体从 `s = lag` 起才跟着动（`pushed` 的 `lag`，5.5）。推：`SLIDE_GAP` + 规划器手指盒沿 `n` 比真指垫多出的部分（按手指朝向 2.7 / 4.2 mm，共 7.7 / 9.2 mm）；拖：`DRAG_SKID`（指尖在顶面打滑）。手最多走 `d + lag`，预测的落点就是要推的距离。slide_1112 实测死区平均 10.7 mm（18 次推，9–14 mm），几何解释了 8–9 mm，余下约 2 mm 没解释（可能是控制器顶着摩擦落后，或物体碰撞体比标注的箱体小）。原来的 `SLIDE_SHORT` 11 mm 是在推长已经含 `SLIDE_GAP` 的情况下量的"比指令短多少"，再加 `SLIDE_GAP` 就把 5 mm 算了两遍（加上以后每次推多走 4–7 mm），删了。
- 进出按 pick 的规矩（`COLLISION_PLAN.md` 第 2 节）：进入的长度按手指几何（下落 `pick_approach()`，落点在推点后 `LEAVE_MARGIN`），离开的长度按碰撞模型实测（`contact_extent`）。原来继承的 `SLIDE_ABOVE` 10 cm、`DRAG_ABOVE` 8 cm、`SLIDE_BACK` 2.5 cm 和推完先退 2.5 cm 再竖直抬 10 cm 的两段直线都删了。
- 目标集合 = 方向 × 做法 × 合拢手指的 4 个朝向（旧代码的 `R_options`）。调用方给出物体可以走的每个方向和要推多远，第一段的那一次搜索里每个方向都是目标，代价是这个方向要推的距离（弱偏好，第 7 节），选中的方向后面几段照用。做法按调用方给的顺序分层（`Problem.tiers`，第 7 节）：默认所有推的停车点构造完才轮到拖，pull 反过来先拖。只按排序时可操作度占主导，`VARIANT_COST` 压不住，能推的地方也选了拖，而拖会把物体甩飞（T01 平装书要 4.5 cm 走了 40 cm、转 98°，T29 table_book，11-12；拖本身的问题还没查）。朝向是否改成绕竖直轴自由（`PoseSet`）待定：会改变已成功的推，单独做。
- 长推不写死段长（`COLLISION_PLAN.md` 第 2 节，11-12）：每段要推的都是剩下的全部距离，推到手臂够不着为止（第 6 段，`plan_slide` 量出来；推不动物体、少于 `min(要推的, PUSH_MOVED_MIN)` 的停车点算失败）。停车点按能推多远排：先解推的终点，有停车点推得完就和以前一样；一个都解不出终点时，排序沿推的方向二分出每个候选能推多远（分辨率 `SLIDE_STEP`），剩得少的在前（`Problem.relay_from`，第 7 节）。`push_object` 在任务层一段一段做（每段一次 `run_skill`），段之间按实测的位移决定还推不推（`enough`、`PUSH_DONE_TOL`）；一段推得比计划预测的 `PUSH_MOVED_MIN` 还少就失败。推歪：段长了侧向偏移会更大，推的时候监测侧向偏移（`COLLISION_PLAN.md` 第 2 节）还没做，每段推完的锚点读实测。
- 和旧代码的差别：手指在碰撞模型里（旧代码推的几段 `ignore_fingers` + `LEGACY` 不查），邻近物体不再另挂成临时障碍（所有物体本来就在碰撞模型里）。推多远、推完的伸出量判据（0.45 m、扫过的地方无物体）还在 `SlideToEdgePolicy`。伸出量（11-13 改）：只推到边缘捏取要的 `EDGE_MIN_OVERHANG`（瞄准多 5 mm，但不超过重心限），重心至少留在台面里 `COM_MARGIN` 1.5 cm（原来 3.5 cm，目标伸出 `min(8 cm, 半长 − COM_MARGIN)`：短于 18 cm 的物体——纸巾盒、米盒——没有一条边能用）；推完超过重心限就失败，不再多给 1.5 cm 余量。
- 换方向、换做法都只在搜索里（第 1 节第 3 条，`COLLISION_PLAN.md` 第 2 节的 F 类）：推到桌边的所有边是一次搜索的目标，推完伸出量不合格就失败，不再换下一条边（旧代码对最多 3 条边逐条 `try/except`，推了一半失败以后，下一条边还用推之前算的距离）；pull 的拖和推是同一次搜索的两层，拖打滑就失败，不再改推（旧的 `pull_hook`）；separate 的 7 个方向都是目标（旧代码找不到停车点就换下一个方向，`separate_direction_blocked`）。

**姿态类技能**（`skill_plans/posture.py` 的 `plan_posture`，job 在 `skill_jobs/posture.py`；9.3 第 5 步，11-16；物理步骤见 `../skills/posture.md`）：crouch、stand、bend、straighten 是 `body_job`（一个身体关节），tuck 是 `tuck_job`（收一条空手臂）。不选停车点，在原地构造，没有锚点：计划就是从执行前读回的 `State` 做的，`run` 每段前照常 `holds` 复核，不成立就重做。

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 张手（`{名}_open`，只有左手收臂） | 动作 `grip(0.04)` | — | 手宽 0.04 |
| 2 | 姿态（段名是关节名，或 `tuck_arm` / `left_fold`） | 身体：`free_leg(Joint)`，目标只改那一个关节；收臂：`free_leg(JointSet{收起})` | `FREE_HAND`，这只手拿着东西时 `FREE_LOAD`；身体姿态 `joints=(那个关节,)`、`arms_still`；左手收臂 `joints=(ARM,)`；右手收臂 `joints=None`（默认规则） | — |

- 身体姿态只动一个关节（`Spec.joints`，4.2）：两条手臂相对躯干不动、手里的东西挂在各自的 held link 上跟着身体走。每条手臂的模型只查自己这条手臂对底盘（4.4），所以这一段再用另一只手的链按同样的身体值查一遍（`_other_arm`）。
- **"能走多远走多远"**（`reach`）：不给具体值的请求——crouch 的 lowest、stand、bend 的 full、explore_furniture 的下蹲——目标是走到多远，段终点是沿关节直线两条手臂都不碰的最后一点（`_extent`），长度由碰撞模型量，和推的 `scripted(reach=True)` 一样，不是缩短重试。给了具体高度、角度的照旧：到不了就失败，失败写明在什么身体值、撞到什么（`Kinematics.explain`）。起因：第一次检查（11-16，`posture_1116/runs3`）里每一次 explore 下蹲都被另一条手臂拒掉——左臂收着时手在 0.8 m 左右、整条手臂在底盘柱子以内，躯干降到下限 -0.54 之前左手就压进底盘（顶面 0.27 m）；旧代码照样降下去，仿真里机器人自碰撞是关的，左手穿过去了。
- 收臂只到收起姿态：技能保证 `arm_stowed`（收起姿态 `STOWED_TOL` 以内），下垂不算。右手收臂两手都空时躯干和腰一起回 (0, 0)（`kin.rest` 的 q_body，4.1），左手拿着东西时只动右臂；左手收臂只动左臂。导航第一段和 place、开关门最后一段的收臂仍是 {收起, 下垂}（行驶姿态，不是这个技能）。
- 做不出来就失败（规则 3）：删掉的是旧 `_move_posture_joint` 的"先收臂再试、再挪底盘到关节能直着动"、它把 `coll_kw` 清空（手指不在模型里）、`fold_where_possible` 的"收不起来就挪底盘"、左手收臂不查碰撞的关节直线。开门、关门、inspect 的路线不再先收臂（它们的计划从手臂现在的样子出发，导航第一段收臂），floor_top 不再先 approach_target + prepare_floor_reach（pick 自己蹲，规划链里有躯干和腰）。
- 结果判断（job 的 `done`）：身体关节离计划送到的位置 `TORSO_AT` / `WAIST_AT` 以内（沿用旧值，没实测）；收臂离收起姿态 `STOWED_TOL` 以内。hooks 在姿态段之后查两只手里的东西还在（`check_held` / `check_left_held`）。
- 还没做（第 5 步移出去的）：`skills._move_with_retry` 左手拿着东西时把腰的上限压到 0.25（只剩微波炉在用）随第 8 步删；`policies/bimanual.py` 的 `_lock_shared_posture` / `_fixed_torso_ik`、`hand.py` steady 改 `left_kin.lo / hi` 随第 9 步删；wave（摆动相位为参数的 `scripted`）、nod（已经是 head 段，差进 catalog）没做。

**微波炉**：电机开门前，`Problem` 加一项检查：部件扫过它的范围时整机不碰（在 `State` 里取几个部件值查）。腔体里的取放是普通的 `straight`，腔体和开着的门都在 `State` 里。电器状态由动作推进。

**v6 没用到的接触 / 手势技能（HAND_PLAN 9h，11-25 设计）**：每个都按拿着东西的手（手势用空着的手，右手优先），旧代码里依次重试的候选点一律并成一个目标集合，"够不着就换一种做法"的退路全删；检查用 v3 的 P01 / P03 / P04 / P05 / P07 / P17（11-08 旧代码：P01、P07 成，P03、P04、P05、P17 两个种子都败）。

| 技能 | 形状 | 计划 | 删掉的 |
|---|---|---|---|
| wave | 姿态（原地） | 张手 → `free_leg` 到举手位姿的目标集合（身前、手那一侧，三个高度）→ 任务段：TCP 沿横向 ±10 cm 正弦摆 `swings` 个周期（`scripted`，世界坐标系 `Still`，`carry="arm"`）→ 收臂 | 三个高度依次重试、`FREE_ELSE_STRAIGHT` 的摆动 |
| point | 姿态（原地） | `free_leg` 到"肩到目标的射线上、离肩 0.30–0.52 m"的目标集合，手指朝目标；目标在身后时任务层先转身（`FaceTargetPolicy`，不在技能里递归） | 4 个距离依次重试 |
| shake | 姿态（原地） | 任务段：TCP 沿合爪轴（水平分量）±`amplitude` 正弦摆 `cycles` 个周期，保持倾角 → 回到起点 | 每半周一个 `move_to` |
| roll | 接触（push 的拖） | `push_object(..., modes=("drag",))`：合拢的指垫压在顶上、垂直于长轴拖；结果判据不变（转过 45° 以上，否则是滑不是滚） | `_contact_sweep` 的手写四点 |
| tip | 接触（push 的一种新方式 `poke`） | `plan_slide`，推点在物体高度的 `TIP_HEIGHT`（80%）、手指沿推的方向伸出（合拢的指尖在前）；一条腿（不走 `push_object` 的多腿循环：倒下以后不再推）；结果判据不变（倾角 > 60° 且还在支撑面上） | `_contact_sweep(side_ok)` |
| flip | 接触（持物的绕轴任务段） | 任务段：被夹住的近边绕远边（支撑面上的枢轴）转，手跟着转（`scripted`，`carry="arm"`，`reach`：转到手臂够不着为止，量出来），倾角不保持 → 松手 → 没过竖直（`PAST_VERTICAL`）时：张开的手沿同一圆弧接着推（第二个任务段，手指可碰物体）→ 退出（`contact_extent`）→ 收臂；判据：翻过来（上表面朝下） | 直线推三档、底盘前开推两档、退出失败吞掉、补推 |
| pour | 取放（有停车点搜索） | 目标集合：杯口在目标开口上方（手绕竖直轴的转角 × 杯口往机器人一侧的偏移；把手捏取多两种侧倒方向）；计划：到达锚点 → `free_leg`（保持倾角）到倒的起点 → 任务段：杯子绕"手和杯口之间的中点"那条水平轴转（`reach`：转到够不着为止，最少 `POUR_MIN_TILT` 否则这个停车点不要）→ 停 → 任务段转回 → 回到到达时的姿态；判据：里面的东西进了目标 | 7 档倾角 × 10 个转角依次找停车点、`held_vertical_move` 抬高、实测后重算位姿再退回计划位姿、逐 20° 的 `move_to` |

**双臂（HAND_PLAN 9i，11-25 设计）**：两只手同时拿着一个东西时**手臂不动**，只动身体（躯干、腰）和底盘——这样不需要闭链规划（两条手臂通过物体刚性耦合，现有的按臂规划做不了，第 9 步原文"闭链约束另议"）。

| 技能 | 计划 | 删掉的 |
|---|---|---|
| brace（左手扶住） | 指定手（左）的 pick，捏法只取 rim / rim_rect / top / handle，`plan_pick(stop="pick_held")`：到达、张手、伸入、合爪、锚点，**不抬、不搬**；结果：那只手拿着它、它还在支撑面上没挪（1.5 cm） | 先原地 IK 两点、不行再重新停车（两级）、`move_left_to` 的 LEGACY 伸入 |
| handover（右手交左手） | 左手 pick 右手正拿着的东西（同样抓住就停；右臂和它手里的东西都在碰撞模型里，离右手太近的抓法由碰撞检查排除，不再写死 6 cm）→ 右手 release（`plan_release`：张开、沿夹爪轴退出） | 手写的 6 cm 间隔、IK 逐个试、左右各自 `move_to` |
| 两手搬（pick hands=both、bimanual carry） | 一对抓法（左右各一）是停车点搜索的一个目标，构造里先建右手到合爪、再建左手到合爪（右手和物体都在模型里）；之后两手都拿着：抬 = 躯干上升（`plan_posture` 只动身体关节，两条手臂各自查碰撞）；搬 = navigate 手臂姿态不变；放 = 躯干下降 + 两手各自 release | `_lock_shared_posture`、`_fixed_torso_ik`、成对 IK、torso 档位 × 抓法对的循环、`follow_both` |

## 7. 停车点搜索（`park_search.py`）

```
find_park(kin, world, problem, state, log, base=None) -> (Found(x, y, yaw, k, plan) | None, diag)
Problem(goals, build, relay, arrive, travel, near, prefer, label, hand, body_free, tiers, relay_from, reach_step)
        # relay 必填；arrive / travel 由 run_skill 按 catalog 填
```

| 字段 | 含义 | pick | place |
|---|---|---|---|
| `goals` | 若干组目标，每组 =（够得着预检用的 TCP 点，排序用的中继位姿，代价） | 每个抓取候选一组（`PICK_CAND_COST`） | 每个"空位 × 物体姿态 × 手腕朝向"一组 |
| `build` | 技能的计划构造函数 | `plan_pick` | `plan_place` |
| `arrive` | 停车点上的手臂姿态（catalog 的 `arrive`；就地的候选是现在的姿态） | 收起 | 搬运姿态 |
| `travel` | 开车时的手臂姿态 | 收起 | 搬运姿态 |
| `near` / `prefer` | 离谁近更好 / 先试的底盘位姿 | 当前位置；门后的物体（`annotations.behind_door`：`inside_` 支撑面上、腔体或冰箱柜体里）先试门自由边前方的停车点（`door_access.front_of`，由标注算） | 当前位置（离目标 1 m 以上时不加“近”的代价）；放到门后的层板上和 pick 一样先试门自由边前方 |
| `relay_free` | 排序解在停车点的状态里不碰的先构造（查碰撞不占构造预算，最多 `FREE_CHECKS` 个） | 门后的取物（`FREE_HAND`） | 门后的放置（`FREE_LOAD`）：11-13 排序把手臂排进开着的门板 |
| `tiers` | 每组目标的层（`Problem.tier`）：低层的候选全部构造完才轮到高层，不看 score。严格偏好；代价只是弱偏好（见第 3 步） | — | — |
| `relay_from` / `reach_step` | 每组目标可以声明中继位姿是沿一条直线（姿态不变）从哪一点到达的：这组目标可以只做一部分（推：手臂能推多远推多远）。见第 3 步 | — | — |

1. **候选**：围绕每组目标的中心按半径（`RADII`）、角度（`ANGLE_STEP`）取点，每点取多个朝向（`YAW_OFFSETS`），再加上 `prefer` 和"原地不动"。
2. **便宜过滤**：
   - 够得着：肩到目标的水平距离和高度；
   - 底盘柱体不碰（逐个 `world.footprint_clear`，0.07 ms 一个；批量的 `footprints_clear` 在候选聚在目标周围时反而慢一倍多），每个目标最多留 `MAX_PER_GOAL` 个；
   - 行驶姿态下整机不碰：批量 `Motion.base_depths`；
   - 开得到：从当前位置算一次可达场 `base_reachable`，查表。
3. **批量 IK（排序，并作为 `build` 的 prior）**：把中继位姿换到各候选的底盘系，批量求运动学 IK，不查碰撞。没有解的候选直接去掉。例外是声明了 `relay_from` 的目标：一个候选都解不出任何中继位姿时（要推的距离比一个停车点够得着的长），对每个候选沿那条直线二分出手臂能解到多远（`reach_ik`，到 `reach_step` 为止，每轮一次批量 IK），解到的最远点的解作为 prior，剩下没推的长度记下来；只要有候选解得出中继位姿，就不量，和以前一样快。有解的按（层，剩下没做的长度，不在原地，score）排：先按 `tiers`，同一层里剩得少的在前（不量的时候都是 0），再原地不动的，再按 score（越小越好）= 关节离限位不到 `LIMIT_CLEAR` 的部分 + 可操作度比最好的差多少（0–1）+ `PARK_DIST_W`（0.5）× 候选代价比最便宜的多多少。所以代价是弱偏好：一位 `VARIANT_COST`（0.05 m）只值 0.025，压不过可操作度；要严格偏好就用 `tiers`。层的代价是构造预算（第 4 步）：低层的候选先花预算，低层构造失败多时高层可能轮不到（推的 job 里拖排在所有推后面，就是这样）。解作为 `prior` 传给 `build`，由 `decide_ik` 在碰撞模型里确认，或换成附近的解（5.7）；它不直接当目标。
4. **按顺序构造计划**：`build(state_at(park), k, prior={problem.relay: 解})`，第一个做出完整计划的胜出，`Found` 带着它（`decisions` 是计划实际走到的解，执行时重做的 `prior`）。预算是 `BUILD_S`（20 s）和 `BUILD_MAX`（60 个），失败原因按类计数进 `diag`。
5. **精确底盘路径**：只对胜出者规划（`base.drivable`）；做不出来就回第 4 步取下一个。路径不留：它是轨迹，执行时 `plan_navigate` 重新规划（5.4）。两边是同一个函数（`RigBase.plan`）、同一组行驶姿态（`skill_plans.travel_chain`，9.3 第 1.4 步）。
`diag["filter_s"]` 记构造之前每一步的耗时（候选和够得着 / 柱体、行驶姿态、开得到、排序 IK、打分），`diag["stage_s"]` 记构造里每段的耗时。

**`relay`**（必填）：排序 IK 的解交给 `build` 时用的键。两种用法，`build` 都只把它当 prior（5.7：在碰撞模型里确认或当种子），从不当检查：
- 通常是这个中继位姿对应的决定：`PICK_RELAY` = `pick_reach`、`PLACE_RELAY` = `place_reach`、`DOOR_RELAY` = `door_reach`，和 builder 的段名由单测绑在一起，`build` 拿解当这个决定的 prior；
- 也可以是某个决定的种子：中继位姿不是那个决定的位姿，而是排序时更能说明问题的那个。推的 `SLIDE_RELAY` = `slide_end` 是推的终点（手臂伸得最远的地方；只排下落起点时，T05 记事本 15 个停车点里 14 个推到半路没有 IK），`plan_slide` 拿它的解当 `slide_reach` 求 IK 的第一个种子（同一个分支）。关门的目标集合里推和握把手共用一个 relay（`DOOR_RELAY`），`plan_push` 把以这个名字传来的解当 `push_reach`（`PUSH_RELAY`）这个决定的 prior。
哪种用法写在 builder 的 `*_RELAY` 旁边。

计划按（停车点，目标组 k）存。技能要查的东西都在自己的 `build` 里，搜索不再有 `check`、`ride`、`score`、`carry` 之类的开关。任务的不同做法都进 `goals`，不按变体各调一次 `find_park`。

**哪只手**（9.3 第 6a 步）：6a 之前搜索写死右臂：够得着预检用右肩（`SHOULDER` (0.09, −0.18)），朝向偏好让右臂那一侧朝目标（`FACE_LEFT`）。对称以后每组目标带自己的手（`side`），肩的位置和偏好按手镜像（y 取反、偏好的符号取反），排序 IK 和 `build` 用那只手的 `kin`：`find_park` 收两只手的 `kin`，不再只收一个。同一个问题里可以有两只手的目标（关门）；pick / place 现在只给右手的目标（6a 末尾）。已做（11-11）：目标组的第 4 项是手（`Problem.side(k)`，缺省 `Problem.hand`），`park_search.shoulder(side)` / `face_off(side)` 镜像，`find_park` 收 `{side: kin}`。随之改的：
- `arrive` / `travel` 是整机姿态 `(q_body, arms)`，不是"那只手的 9 维"：`travel` 用在 `base.depths` 的整机检查上，对所有目标只做一次，不能随目标的手变；`arrive` 只换要干活的那只手的手臂（4.1：姿态目标只给手臂），另一只手、q_body 照现在的样子。`motion_skills.posture` 同改。
- 排序 IK 一次只用一个 `kin`（`rank_ik` 的批量调用）：候选按手分两批算，`score` 照旧放在一起排（两只手的限位、可操作度镜像相同）。
- 镜像只镜像底盘系里的量（肩的位置、朝向偏好）。关节值不能直接拿来用：URDF 里两臂的关节 3、5、6 轴相同，镜像一个姿态要把这三个取反（`q_左 = (+, +, −, +, −, −, +) · q_右`）；左右的收臂、种子姿态本来就是各自的数据（左手的 `LEFT_ARM_FOLD` 是单独搜的），不互相镜像。
- 两只手的偏好只是弱偏好（第 6 节关门）。
- 排序 IK 和构造用同样的锁（6b 加）：一只手的目标、另一只手拿着东西时，排序 IK 把 q_body 钉在 `State` 的值上，`Problem.body_free` 里的关节除外（推门：躯干，`push_body` 会动它）；锁哪些关节由同一个 `motion_state.locked_body` 定，钉的是同一个 `kinematics.kept_joints`。不锁的话，排出来的停车点要靠弯腰才够得到，构造时腰一锁全都够不着。

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

**握法按实测关节角量**：`State` 里的握法（`Rig.snapshot`）、`place_job` 求放下位姿用的握法、`held_offset` 日志都相对于**实测**关节角下的 TCP（`rig.q()`），不是指令 TCP（`q_cmd`）。持物的手臂会下垂（`q - q_cmd` 中位 0.004 rad、最多 0.013 rad；这是加重力前馈之前量的，见下一段），接触会把手臂顶偏；相对指令 TCP 量的"握法"把这些都读成物体在手里动了，而且随姿态变（同一个焊住的物体，搬运姿态和放下段起点量出来不一样）。按实测量，焊住时握法不变，不焊时变的就是真的滑动，sticky 和 physical 同一个口径。代价：指令 TCP 照这个握法推出的位姿去，手臂还会下垂，物体比计划低约一个下垂量（毫米级，放下段终点离支撑面留着 `LEAVE_GAP`；有了重力前馈以后边夹抬起只差约 1 mm）。

**手里东西的重量由手臂扛**（11-12，b1862b0）：仿真里机器人自己的连杆不受重力（手臂控制器的补偿），手里的东西却只靠位置驱动顶着：边夹抬起后 TCP 比指令低 5–9 mm、物体倾 1.5–2.5°，这时已经没有接触，关节上是静态的 0.4–1.5 N·m，正好是负载的 `Jᵀ m g`（liftdbg_1112）；T01 / T07 / T26 的 `pick_lift` 因此超过 `TARGET_TOL` 失败。现在 `Rig` 在每个物理步之前给每只手的负载加重力前馈（`Rig._payload_feedforward`、`payload_torques`：`J_comᵀ (0, 0, m g)`，质量和质心从 PhysX 读；双手抱的一边一半，躯干和腰取两边之和；质心离 TCP 超过 `PAYLOAD_REACH` 0.4 m 的不算在手里）。加了以后抬起误差约 1 mm、倾角 0.2–0.7°，这三集都成功。这是 `Actuator` 的实现，计划层不变。

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
  - place `PLACE_TOL` = `TARGET_TOL` / `TARGET_TURN`（5 mm / 0.01 rad）：放下段执行后按 `TARGET_TOL`（同一个 5 mm）判有没有被挡住，偏得比这少只是放偏几毫米，不重做（重做只能从放下段本身做，放下段只有 1–2 cm 长，偏几毫米的新直线就明显不竖直了）。
  两个都还没有实测数据（2.1 步的记录已加：`segment` 事件的 `aim_off`，等全量跑完用 `tools/anchor_stats.py` 第 2 节定）；仿真里底盘停下的偏差在日志精度 1 mm 以内、朝向 0.02° 以内；
- 路点在现在的世界里不碰：按这段的 `Spec`，含 `touch`，零余量；
- 离开段：用 `contact_extent` 从当前姿态重量，长度和计划差超过 `EXTENT_TOL`（`LEAVE_MARGIN` 的一半：终点仍至少留半个余量离开接触，多走的不查碰撞部分也不超过它）就不成立；
- 任务段：`carry="base"` 的底盘离构造时不超过 `TARGET_TOL` / `TARGET_TURN`；耦合的部件在能起步的范围里（`part_start`，同 5.5）；按实测的物体 / 部件重查机器人——`carry="base"` 用同一个函数从构造时的底盘重算，`carry="arm"` 查存下的 `qs`，每段的部件在它的 `s` 处（底盘本体搜索时对静态世界查过，`holds` 没有 `BaseModel`，不重查）；
- 动作段总是成立；锚点不复核自己，它触发复核剩下的。

执行完以后，判"被挡住"比的是实测 TCP 和这段送去的指令 TCP（`q_cmd`），差过 `TARGET_TOL` 就是停在半路。这个距离由 `Rig._settle` 在手臂停下时量一次（`follow` 返回它，`rig.last_off`）：`run` 对每段手臂跟随的运动（move 段、`follow` 执行器的任务段）都判，在这段自己的 hook 之后（`after_grasp`、`after_down` 先用同一个值做自己的判断和失败出口）。11-12 之前只有这两个 hook 判，其余段停偏了也照样往下走：T05 取书后的 `carry_in` 手腕没转过去，书偏了 25 cm 一路带到书桌，放书时才出事（`_settle` 只认 TCP 不再动就算停下）；目标对不对已经在这段之前由 `holds` 查过，不在这里再混进来。

### 8.5 推完的落点是预测的，预测不了的才截止

推完一段之后的锚点是预测的：`pushed` 耦合给出推完物体在哪（5.5），搜索拿这个位置证明后面的离开、收臂做得出来；执行到锚点读实测，复核剩下的整份（8.3），不成立就从实测状态用同一个 `build` 重做，做不出来技能失败。这比在锚点截止强：截止的话，搜索证明不了推完以后的任何一段。前提是预测得准：耦合里有死区（手先走 `lag` 物体才动，第 6 节推桌上的物体）。加死区之前，slide_1112 的 18 个推完的锚点上，预测都比实测远 9.4–13.9 mm（11-12），复核都还成立；加了以后 slide_review_1112 的 8 个是 1.2–3.4 mm。

真正预测不了的落点（drop：物体从手里掉下去停在哪）才用 `predict=False`：锚点之后计划截止，搜索只证明锚点之前的部分，之后的段执行时从实测状态用 `build` 做出来（没有 `prior`），做不出来技能失败。还没实现：新层上还没有技能要它（drop 还走旧代码，9.3 第 4 步）。

跨多个停车点的任务（长推、sweep 逐个物体）每段是一次 `run_skill`，段之间在任务层按实测决定下一段（第 6 节接触类技能），不是同一份计划里的锚点。

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

意外接触只当指标（PhysX 真实接触 `physx_contact`，含手里的东西碰外界，记成 `held:<物体>`；规划器碰撞球的 `unexpected_contact`）。搬运中掉了，抛 `Dropped` 给上层。

### 8.7 旧入口

`Rig.move_to` 只留给还没迁移的技能，等于"一段 `free_leg` 的计划 + 执行"。过渡期的 `FREE_ELSE_STRAIGHT` 只在旧入口（`Rig.move_to`、`joint_path`、`move_left_to`）里起作用。每迁完一个技能，就少一个调用方。

### 8.8 外部产出的计划：`rebuild=None`

`Plan` / `Segment` 不该只有 `build` 能产出。`State` 是干净的快照、`Plan` 是干净的运动表示、`holds` + 接触监视是一套独立的校验，合起来意味着：**任何能产出 `Plan` 的东西，都能免费拿到碰撞复核、接触监视、持物限速和失败分类。** 外部策略（学出来的、别人写的）只要产出 `Plan`，`run` 就能执行并校验它；`find_park` 也能拿 `problem.build` 给它打分。

`run(act, plan, rebuild, hooks)` 里 `rebuild=None` 合法，含义是"不重做"：某段 `holds` 不成立就按失败退出，锚点处不复核剩下的（没有 `build` 可调）。`carry_posture` 已经这样用（它的计划是刚从现在的状态做的，不成立就失败）。有了它，④ 就从"pick / place 的执行器"变成"任意 `Plan` 的执行与校验器"，这是第 1 节第 3 条（没有 fallback）唯一合理的放宽方式：外部策略不会重做，但它也不会偷偷走不查碰撞的路。

配套的是 4.6：外部策略要观测，观测走 `Observation`，不进 `State`。

## 9. 现状和下一步

### 9.1 已实现

- 数据：`State`、`Hand`、`Held`、`Spec`（`allow`、`fingers`、`exempt`、`hold_tilt`、`touch`）、`Segment`（`move` / `action` / `drive` / `scripted` / `anchor`）、`Plan`（含 `decisions`）、`Failure`、`Aim` / `aim_pose`，以及推进 `State` 的小函数；协议 `Actuator`、`BaseModel`（2.5）。实测握法按实测关节角量（8.2）。
- 查询层：`Motion.query`（包一层）、`path_free_only`；手里物体的碰撞球按碰撞体拟合（`held_spheres`，4.4）。
- 原语：`free_leg`（`Joint`、`Pose`、`PoseSet`、`JointSet`）、`straight`、`contact_extent`、`contact_segment`，三个"还在碰"判据，`exit_length`；`drive`、`drive_straight`（5.4）；`scripted`（任务段，耦合 `hinge` / `slider` / `still` / `pushed`（带死区），手臂带的可以 `reach`：走到够不着为止，5.5）；`decide_ik`（5.7）；`holds`（8.4）。
- 计划：`plan_pick`、`plan_place`、`set_down_length`、`plan_navigate`、`travel_chain`、`Carry`、`plan_door`（开门，11-10）、`plan_push`（推门关，11-12）、`plan_slide`（推桌上的物体，11-12）、`plan_drop`（扔进容器，11-14）、`plan_look`（11-16）、`plan_posture`（姿态，11-16）、`plan_clear`（手握部件时松开）；目标从 `State` 推出（第 6 节）；锚点 `pick_arrive` / `pick_held` / `place_arrive` / `place_landed`；`prior` 是 `Plan` 时还成立的运动段原样复用（`_kept`，收臂除外）；`HELD_POSE_MARGIN` 5 mm，`PICK_TOL` 1 mm，`PLACE_TOL` 5 mm。
- 第 ⑤ 层：`motion_skills`（`Skill`、`Job`、`run_skill`、`posture`，`SKILLS` 从 `skill_library/catalog.json` 的 `motion_skills` 加载，`template` / `park` / `arrive` / `travel` 都起作用，2.3）；navigate、pick、place、drop、open、close、push、stir、look、inspect 和姿态类（crouch、stand、bend、straighten、tuck）走它，它们的 job 在 `zeno_skills/skill_jobs/`（`navigate`、`pick`、`place`、`drop`、`door`（open、close）、`slide`（push，和任务层一段段推的 `push_object`）、`stir`、`look`（look、inspect）、`posture`（`body_job`、`tuck_job`），加上 `base` 的 `RigBase`、`carry` 的搬运判据）。
- 搜索：`park_search.find_park(kin, world, problem, state, log, base)`、`Problem`（目标带手、`body_free`、`tiers`、`relay_from`，第 7 节），pick / place / open / close / push 在用；门后（柜子 / 冰箱 `inside_` 支撑面上）的取放，种子停车点由标注推出（`door_access.front_of`）。微波炉腔体里取物不走这里：合约路由到 `PickFromCavity`（policy_048，旧实现，第 8 步）。
- 执行：`run.observe`、`execute`、`run(act, plan, rebuild, hooks, clear)`（每段 `holds`、锚点复核剩下的整份，`rebuild=None` 合法，8.8；失败出口 `run_clear`，8.6）。
- 单测（假的 kin / 底盘 / 执行器，不起仿真）：`tests/test_primitives.py`、`test_skill_plans.py`、`test_park_search.py`、`test_navigate_plan.py`、`test_layering.py`、`test_motion_skills.py`、`test_scripted.py`、`test_door_plan.py`、`test_symmetry.py`、`test_slide_plan.py`、`test_push_object.py`、`test_posture_plan.py`、`test_posture_job.py`；碰撞模型的构造：`test_held_collision.py`（手里东西的球、每条手臂的自碰撞表）、`test_body_collision.py`（底盘环境；GPU 那一侧是 `tools/check_body_collision.py`）；`test_payload_feedforward.py`（重力前馈）。
- 基线：全量跑 v6（`COLLISION_PLAN.md` 第 5 节）。`1c5b98d` 69/153（11-10，`/data/zenobench/v6full_1109`）→ `c096313` 82/153（11-11，`v6full_1111`）→ `bdc2a23` 87/153（11-12，`v6full_1112`，现在的基线）；6b（`a33d852`）以后还没跑全量。
- 静态审计：`tools/audit_collision.py`，`tests/test_collision_audit.py` 是棘轮，`tools/stop_check.py` 每轮也跑。它认识 `Spec`（`Spec(allow=LEGACY / unchecked(...))`、`Spec(exempt=...)`、`Spec(fingers=False)` 和写在 `move_to` 上一样算）；执行入口（`EXECUTION`：`run.py`、`rig.py`）和查询层（`QUERY_LAYER`：`Motion.query`、`Motion.path_free_only`）里的 follow / 豁免不算，这些放宽在写 `Spec` 的地方已经算过；`find_park` 按顺序调 `build` 不算重试。另有 `old_entry` 一类（9.3"只降不升的计数"）。

### 9.2 pick / place 还没解决的

| 问题 | 例子 | 怎么解决 |
|---|---|---|
| 构造预算用完：收臂失败每次约 10 s | T06 s10、T01 s10 | 9.3 第 2.7 步 |
| 持物在手里滑动没有余量，按实测复核判碰就得重做 | — | 开车前的 place 计划带 `HOLD_DRIFT` 余量（8.2，2.5 步）；`HOLD_DRIFT` 要在 `physical` 下按实测滑动定（握法按实测关节角量，sticky 下它不变） |
| 持物去搬运姿态的规划慢（保持倾角按位姿规划单次 0.6–8.4 s） | pick 构造时间的大头（`carry_in` 约占 77%） | 不涉及；pick 锚点处重做（`PICK_TOL` 1 mm）常碰上它会更慢（第 10 节） |
| place 搜索的时间大多花在构造之前 | place 搜索中位 16.3 s 里 11.6 s；候选中位 11 万个，构造中位只做 1 份。候选 + 够得着 0.7 s，柱体约 3.5 s，其余在行驶姿态 / 排序 IK（`diag["filter_s"]`） | 先按 `filter_s` 找大头，再考虑分批排序或同一空位的手腕朝向共用底盘候选（第 10 节） |
| 翻书走旧 `FlipFlat`（书的放置 11-14 已进 `plan_place`） | T15 s10/s11 | 2.7 步 |

第 1 节第 2 条（每个决定一个出处）在 pick / place / navigate 里已经没有重复的出处。

### 9.3 迁移顺序

按"覆盖多少 v6 路线步数、依赖谁"排（2.3 的表）：

1. **框架（第 ⑤ 层，已完成 11-08）**：`Skill`、`run_skill`、`drive`（包 `_base_plan` 和 `straight_base_move`）、`plan_navigate`；pick / place 改走 `run_skill`；`skill_plans.py` 拆成包（9.4），`Actuator` 协议（2.5），`SKILLS` 进 catalog（2.3），`plan_navigate` 第 1 段按约束复核持物姿态（删 `_carry_pose` 和它的 `FREE_ELSE_STRAIGHT`），`_drivable` 和 `plan_navigate` 用同一组行驶姿态（`travel_chain`）。navigate 一项就覆盖 1099 步。和计划的出入：`find_park` 多一个参数 `base`；协议方法叫 `arm_kin`；技能接口是过渡形式 `Job`；`min_bottom_z` 是"能抬就抬"不是约束（第 6 节）。
2. **pick / place 收尾**，每项单独提交：
   1. 先只记录不改行为：到达、握上、落下时的实测偏差（底盘、握法、漂移、终点 TCP 离目标多远）写进日志（锚点的 `info`，4.3），跑一次定 `BASE_TOL`、`HOLD_DRIFT`、`TARGET_TOL` / `PICK_TOL`；同一次提交里建 `tolerances.py`（4.5），把散落的阈值搬进去、补上来源标记。
      **记录已加（11-11，c096313）**：
      - 锚点段带 `info["assumed"]`（计划在这一刻假设的 `State`）和 `info["watch"]`（pick：目标物体；place：放下的物体；开门：部件）。`run` 每个锚点都记一条 `anchor` 事件（以前只在复核时记），`off` = `motion_state.state_offset(假设, 读回)`：`base` [mm, °]（停车偏差）、`arm`（指令关节角和计划差多少）、`hold_<side>` {mm, °, 握法类别, 计划时的 `pad`}（`pick_held`：合爪前假设的握法对实测；`place_arrive` / `arrive`：开车这一路握法变了多少 = 漂移）、`watch`（瞄准的物体 [mm, °] / 部件关节值差；`place_landed` 是落点对预测）、`moved`（其它物体离假设超过 5 mm 的，最多 5 个：被碰动）。复核时 `why_rebuilt` 记每个重做的段为什么不成立（`holds` 的原因，或"起点变了"）。
      - 接触位姿所在的段（带 `aim`）执行前的 `segment` 事件加 `aim_off` = [比建时多偏 mm, °, 目标自己挪了 mm]（`primitives.aim_excess`，和 `holds` 同一个算法）：`PICK_TOL` / `PLACE_TOL` 切的就是这个量。
      - `tools/anchor_stats.py RUN_DIR`（只用标准库）汇总：各锚点的偏差分布和超过几个候选阈值的个数、`aim_off` 分布、`held_offset` 按握法、锚点复核 kept / rebuilt / 失败和原因、段的重做、`decide_ik` 的 prior / solved、停车点搜索各阶段耗时和 `filter_s`、构造失败原因——第 10 节几个"先看数据"的问题（锚点处重做做不出来有多少、pick 到达锚点是不是几乎每次重做、搬运段和 place 搜索构造前的耗时）也从这里读。
      - `tolerances.py`（4.5）第一批建好。
      - 数据：11-11、11-12 两次全量都写了 `ANCHOR_STATS.md`（`/data/zenobench/v6full_1111/runs/`、`v6full_1112/runs/`）；`BASE_TOL`、`HOLD_DRIFT`、`PICK_TOL`、`PLACE_TOL` 还没据此定值（`tolerances.py` 里仍标着没实测）。
   2. **已做（11-09，376b692）**：`decide_ik`（5.7）、`Plan.decisions`（4.3）、`build` 的 `prior`。和计划的出入：`Problem.relay` 告诉 `find_park` 排序 IK 解属于哪个决定；搬运目标的选择也复用（(序号, 集合大小)）；`Plan.decisions` 记计划实际走到的解。针对性对照新 4/8、旧 3/8（T20 bottle_on_cabinet 改好：放下段起点的解原样用，不再被 `Motion.ik` 的可操作度项换掉）；
   3. **已做（11-10，c21cb48）**：目标从 `State` 推出（`Aim`，第 6 节），删 `_pick_ready` / `_place_ready` 开头的整份重做和 place 开车后的重新测量，`plan_place` 去掉 `u_out`。sticky/gt 下 5 集事件日志和旧代码逐条相同；
   4. **已做（11-10，83a4209、43eaa13，审计修正 38ca97c）**：`holds` 挪进 `primitives`；锚点段，`run` 在锚点复核剩下的整份（`anchor` 事件记 `kept` / `rebuilt` / `seconds`）；`build` 原样复用 `prior` 里还成立的运动段（`_kept`）。针对性对照 5 集成败同旧代码，31 个锚点没有一次重做，每次 0.04–0.35 s。
      审计后修正（11-10）：收臂段不复用（之前 `_kept` 会把搜索时选的下垂原样留下，违反第 1 节第 8 条）；握法改按实测关节角量（8.2，之前相对指令 TCP，sticky 下手臂下垂、被接触顶偏会读成"目标挪了"，T09 两次 place 失败都是这样触发的）；目标检查和底盘终点检查合成一个判据，容差按技能：pick `PICK_TOL` 1 mm、place `PLACE_TOL` 5 mm（之前物体位移 1 mm、底盘位移 5 mm，两个技能一样）；`after_grasp` / `after_down` 判被挡住改为比实测 TCP 和指令 TCP（之前比执行后重推的目标，接触中目标跟着变，混进了目标的位移）。`anchor` 事件的 `rebuilt` 只列路点变了的运动段（收臂每次重做，做出来一样的不算）。验证（v6 sticky/gt，8 集，`/data/zenobench/verify_1110`）：5/8 成功（T02、T05、T09 pot_in_use、T24、T25）。T09 是这一系列改动里第一次成功（之前各版本都在放锅时失败：目标被读成"挪了"后重做，或重做后停短）；T24 在 2.2 对照里放苹果失败、这次成功。失败的三集和以前同处：T13 的 look 视线被挡、T04 一只杯子始终倒着（倾角 81.3°，各版本相同）、T17 放锅盖时手臂离指令 14 cm（旧代码在同一处报"目标挪了 11 cm / 41°"，是同一件事：手臂没跟上 `place_reach`）。69 个锚点（pick 38 个，`PICK_TOL` 1 mm 下一次也没重做），段的重做 0 次；伸入后实测 TCP 离指令中位 0.9 mm、最多 1.0 mm；松手前物体离支撑面的间隙中位 5.8 mm（之前 6.0 mm），握法改按实测关节角以后看不出下垂的影响。
      对照方法：锚点多出的复核查询（`contact_extent` 等调 cuRobo IK）会改变求解器的调用历史，之后的排序 IK 跟着变，五集都在某次停车点搜索处和旧代码分开——没有单独做实验证明。以后的对照不再要求事件日志逐条相同，比锚点 / 段的重做、成败和失败类别；
   5. 余量：place 计划带 `HOLD_DRIFT`；
   6. **已做（11-09）**：hooks 不动机器人，失败出口是 `run` 执行的计划（`clearing` + `plan_clear`，8.6）；
   7. 9.2 第一张表里剩下的：收臂预算、搬运慢、书进 `plan_place`（删 `place_flat`）。**书已进（11-14）**：捏边的东西走 `place_job`，目标集合是边缘（`_edge_goals`），`plan_place` 加 `place_clear`（松手后指垫离书不够 `EDGE_PAD_CLEAR` 才挪，挪到够为止，和抽出一样不许碰书），悬出量给下指尖留 2 cm，放完用 `push_object` 推进去；`place_flat` 删了，叠书时底下那本书不再挡住所有空位。见 `../skills/place.md`。
   8. **手里物体的碰撞球（11-11，7e82e60）**：原来的 `box_spheres` 是包围盒里等大的内切球，离物体表面中位 6–19 mm、最多 15–28 mm（锅盖底边、mug 侧边整片没盖住），圆物体的盒子四角又多出约 4 cm。T17 掀锅盖放到灶台时锅盖边压上锅沿、手臂被卡 14 cm，T04 拿着 mug 开车擦倒柜面上的杯子，规划和复核都看不见，接触监视也不看手里的东西。改成按碰撞体拟合的变半径球（4.4），`HELD_SPHERES` 32 / 32 → 右手 140 / 左手 60；PhysX 接触监视加上手里的东西碰外界。离线核过（预算 140）：锅盖 127 个球、mug 39、杯子 41、书 101、带把手的锅 130（放宽到 7.5 mm），多出都 ≤ 4.0 mm，其余表面离球 ≤ 6.3 mm；自碰撞对数不变（当时 16271；90a2a31 把共用表改成左右对称以后是 16171，4.4），球总数 505 ≤ 512。接触监视的 PhysX 实体按接触点所在的标注家具命名（`Motion.entity_of_contact`，和球模型的命名一致：之前同一张桌子一边叫 `desk_1`、一边叫 `SupportRepairs/desk_1__top`，放行对不上）；松手时物体碰它被放到的东西放行（`release_spec(on=)`，`place_job` 由支撑面得出）。针对性对照（v6 sticky/gt，旧 = `9f6dc08`，各一个仿真，`/data/zenobench/held_spheres_1111`）：T04 two_guests 新成功、旧失败（mug 擦倒杯子：所有版本里第一次没倒），T17 hide_both 新成功（旧侧显存不够崩了），T02 crowded 两边成功（挤着的方块照样拿得起来），T14 shelve_the_book 两边成功（新侧第一次两个仿真同时跑显存不够崩了，单独重跑成功）。停车点搜索总耗时 334 → 345 s（+3%）。新的手持物接触里剩下的是真实接触：T14 搬书时擦到铅笔，以及还没迁移的旧 `place_flat`（`flat_lower`）。
3. **感知类**：look、search、explore_furniture / explore_room、inspect、measure、identify、count。navigate + 头部动作，只依赖第 1 步。
   **已做（11-16）**：look 和 inspect 是技能（catalog `look` / `inspect`，形状 perceive，`skill_plans/look.py` 的 `plan_look` + `skill_jobs/look.py` 的 `look_job` / `inspect_job`；`LookAtPolicy` / `InspectReceptaclePolicy` 只调 `run_skill`，瞄哪、要不要转身由 job 定，看没看见、看到什么在 job 的 `done` 里判）：不选停车点；要转身时是 navigate 到同一处新朝向的计划（收臂、开车、`arrive` 锚点），锚点处按实测底盘重算头角；然后每个瞄准点或固定头角一个 head 动作段（`run.execute` → `Actuator.aim_head`，向接触监视声明，和 `wait` 一样）；hooks 只记录看到了什么。头角的几何（`perception.look_angles`）在 job 里算、以函数交给 `plan_look`：perception 引用 predicates，build 不能引用。`run_skill` 对 perceive 形状不做开头的头摆正。
   其余感知技能是 look 之上的任务层（`policies/perceive.py`）：identify / measure（经 look）、count / view_support 各一次或几次 look；search、explore_room、explore_furniture 先定站位（一个目标集合：能开到的 `base_reachable` ∩ 看得见的 `_in_view_poses`；explore_room 的候选 = 房间的点 ∪ 房里家具的站位，按预测看得见的目标贪心覆盖），再逐个 navigate + look。开车前、回头看要转身前，先用 `viewpoints.drivable` 问一次 navigate 开车那段的整机底盘规划（`RigBase.drivable`，停车点搜索查停车点用的同一个）：可达场放过、整机规划不出来的站位或朝向（11-22 餐厅 3 号柜从西边的两个站位 0/4；11-19 T05、T27 视点上转身回看，到达姿态碰撞）换目标集合里的下一个——search 换这件家具下一个看得见它的站位（最多 `DRIVE_TRIES` 个），explore_room 为只有它看得见的目标重新选一个视点，explore_furniture 换下一个站位，转不过去的回看不看（覆盖率决定成败）——这是第 1 节第 3 条的"换目标集合里的另一个目标"，不是 fallback；开车本身失败技能照旧失败。face 用 navigate 的计划转身（不再调 `rig.tuck`）。"站哪看得见"的判据（`view_points` / `in_view_poses`、一次可达场的 `reachable_in_view`、explore_room 的 `predicted` / `cover_views`、view_support 的 `view_coverage` / `best_view`）集中在 `zeno_skills/viewpoints.py`（后两个定义在 `visual_prompt`，和标点的图像几何放在一起，这里转出）；手势（point_at、present_held，仍是 `rig.move_to`）挪到 `policies/gestures.py`，`drive_head` 挪到 `skill_jobs/look.py`，`perceive.py` 里只剩任务层。sweep 的头角、步数在 `tolerances.py`。扫视（`SWEEP_YAWS` 五个偏航角、`VIEW_TURNS` 回头 180°）和 count 的 `COUNT_YAWS` 是任务定义的看法——探索要看的方向，不是连接中继位姿的手写路点（第 1 节第 1 条管的是手臂和底盘在中继位姿之间的运动，转身本身是 navigate 的计划）。还没迁的：explore_furniture 的下蹲（`LowerTorsoPolicy` / `SetTorsoHeightPolicy`，姿态类，第 5 步；下蹲失败探索就失败，不再记 `explore_crouch_skip` 吞掉）；present、nod 的转头仍是单独的 head 段（`drive_head`）。
4. **取放家族**：drop、stack、lift、hover、cover、present；collect 在任务层串。在 `plan_pick` / `plan_place` 上换目标集合。
   **drop 已迁（11-14）**：`skill_jobs/drop.py` 的 `drop_job` + `plan_drop`（`plan_place` 的形状：到达锚点 → 保持倾角的自由段到开口上方 → 空中松手 → 等落下 → 收臂；没有放下段、抽出段和落地锚点，落点预测不了，8.5），`place(name, "in:<容器>")`（托盘除外）也走它；旧的 `drop_into` 主体和 `_drop_check` 删了，`park_over` 留给 hover。已经举在开口上方的（先 hover 的）目标集合只有现在的位姿，现在的底盘位置先试。
5. **姿态类**：`Spec.joints`（`q_body` 和锁 q_body 这一种用法在第 6a 步做；`JointSet` 第 1 步已加）（`joints` 按关节名写，不按规划链的下标）。bend / straighten、升降躯干、wave、nod；删改 `kin.lo / hi` 和 `_lock_shared_posture` 的地方。
   **已做（11-16）**：`Spec.joints` 按关节名管整条链（5c433e5，4.2）；`plan_posture`（05fda01）；crouch / stand / bend / straighten / tuck 进 catalog、走 `run_skill`，旧的两级退路和不查碰撞的左手收臂删了（e574f83，`old_entry` 172 → 167）；explore_furniture 的下蹲走 crouch / stand（c7b55aa）；floor_top 只走 pick，policy_042 / policy_065 退役（3474505）；开门、关门、inspect 的路线去掉前置的 policy_003（672c966）；"能走多远走多远"（40acf90，第 6 节姿态类）。第 6 节写了做法和移出这一步的几项（`_move_with_retry` 的腰上限 → 第 8 步，`_lock_shared_posture`、steady → 第 9 步，wave / nod 没做）。
   **检查**（`/data/zenobench/posture_1116`，v6 sticky/gt，一个仿真）：runs1 @5c433e5 T19 x6_gd_can_put_away in_4、T22 juice_on_table、T10 x6_gd_can_put_away in_cabinet 3/3 整集成功（T19 在 1116 失败；三集都是左手推门关，`push_body` 没触发）。runs3 @c7b55aa：T02、T20、T30 的 explore 下蹲全被另一条手臂拒掉（左臂收起姿态压进底盘）→ 40acf90。runs4b @3474505（floor_top 只走 pick）：T26 nominal（sticky/benchmark）、T12 bins_capacity、T23 belongs_on_floor 整集成功；T23 by_kind 两次地上的抓取都成，死在后面 explore_room 原地转身（左臂第一节压进 wall_627 4 cm；1116 死在放勺子）。runs4c @672c966（不先收臂）：T22 eat_now（1116 是挪底盘 20 cm 才收起来的那集）、T25 drink_in_fridge 整集成功；T18 at_island 关门换成原地右手握把手（1116：先收臂，开到别处左手推），`door_held` 锚点重做最后的收臂 TRAJOPT_FAIL（任务仍判成功，第 10 节"锚点处重做做不出来"）。runs3b @40acf90：T02、T20、T30 整集成功，下蹲量到 -0.466（左臂收起姿态在这里碰到底盘），三个柜子的三层（含最下层）都看到；T05 pen_in_6 开门的停车点换了（2d882ab：(1.5, 1.046, -105°) 正面捏；现在 (0.896, 1.078, -30°) 侧钩 20°，候选和过滤计数相同，构造顺序不同），开门最后的收臂执行前 `holds` 不成立（106/249 路点手指压进 2 mm），重做 TRAJOPT_FAIL。原因是建段的关节直线按 0.05 rad 抽样（`Motion._segments_free`），`holds` 逐个路点查：两边判据不一样（第 1 节第 2 条）。改法是 `free_leg` 的关节直线也查它交出的那些路点，会改所有关节直线段，没在这一步做。
6. **部件类 + retreat**：`scripted` + `Held(kind="part")` + `touch` 扩到部件和部位。开关门，`_ride` 变成闭环执行器，删 `hand_touches_part`；retreat 用直线 `drive`。
   **框架已做（11-10，9f6dc08；11-11 随开门跑了仿真）**：`Script` + 耦合（`hinge` / `slider` / `still`）、`scripted` 段（`carry` 底盘 / 手臂）和 `run.execute` 的两种执行器、`Actuator.ride`（`Rig.ride`）、`BaseModel.clear`（`RigBase.clear`）、`Held(kind="part")`（`Rig.snapshot` 从 `_handle_grasp` 读出，`Motion.query` 不挂盒子、只放开手指对这个部件）、`Spec.touch` 写部件和 `hand`；FakeKin 单测 `tests/test_scripted.py`。
   **开门已迁（11-10；11-11 跑仿真后修了 f418f58、30c4278、cbf8eec，柜门和冰箱开门都过了）**：`plan_door` + `open_job`（第 6 节），`skills.open_articulated` 转到 `run_skill`（微波炉还走旧代码；左手拿着东西时当时也走旧代码，6b 起改成用空着的手）；合约 `hinged_door` / `drawer` 路径改成和冰箱一样的 policy_003 + policy_022，只握一次，policy_046 / 047 / 049 / 050 退役；`Aim` 可以写在部件坐标系里（`frame`）；`plan_clear` 能松开把手；旧代码按力矩比挑停车点，去掉了（第 6 节开门）。单测 `tests/test_door_plan.py`。关门见 6b。还没做：手臂走圆弧、门扫过的扇形对家具、`Spec.margin`、`Allow` 由 `touch` 推出；删 `skills._ride` / `_ride_check` / `_move_articulated` 要等关门也迁完。
   **6a. 左右对称（从第 5、9 步提前，关门的前提；11-11，bdc2a23，仿真检查见下）**：机器人本身左右镜像（URDF 两臂 7 个关节上下限、力矩都一样，关节原点 y 取反，关节 3、5、6 镜像时取反，第 7 节；两只夹爪都有腕部相机），代码不对称是先写右臂留下的：`q_right` 9 维、`q_left` 7 维，`held` / `left_held`、`grip` / `left_grip`、`follow` / `left_follow` 两套，停车点搜索写死右肩。新层其实已经大多按手走（`State.q(side)`、`with_arm(side)`、原语用 `kin.side`、`run` 用 `info["side"]`、`Actuator.follow / declare / arm_kin(side)`、`Aim.side`、`touches(side)`），左手推门缺的是三样：**两条手臂共用躯干的规则**（4.1）、另一只手的东西怎么进查询（4.4）、按手搜停车点（第 7 节）。这一步做这三样和它们要的接口，右手技能的行为不变：
      1. `State` 拆成 `body` + `arms`（4.1）；姿态目标的 q_body 只在 q_body 能动时生效（`with_posture`、`free_leg` 的 `_keep_body`）；整机姿态 `Posture(body, arms)` 用在 `swing`、`BaseModel.plan`、drive 段（现在 drive 段的 `q_from` / `qs` 只记右臂，开完车 `_plan_navigate` 只推进右臂，`holds` 也只查右臂在起点）；
      2. 共用躯干的规则：另一只手拿着东西时，这只手的段锁住 q_body（`Spec.joints` 的最小版，4.2）；
      3. `Motion.query` 里另一只手的东西：手臂在动的段是世界障碍物、位置从 `State` 推；整机在动、手臂相对底盘不动的检查挂在它的 held link 上（4.4）；
      4. `Actuator` 的方法都按 `side`（`grip` 加 `side`），`Rig` 加按手取的读写给新层用（`snapshot` 也用它，左手握把手也读出 `Held(kind="part")`），名字实现时定；`follow(side="left")` 和右手同一套执行：持物限速（看这一段动到的所有东西：q_body 动时也算另一只手的东西）、平滑起停、按那只手的 TCP 判到位（`_settle`）。导航的 `left_fold` 已经走 `follow(side="left")`，它的时序会变，成败不该变。旧代码用的 `held` / `left_held`、`left_grip`、`left_follow` 等先留着，第 10 步删（`old_entry` 棘轮照旧只降不升）；
      5. 原语产出的段都带 `info["side"]`（现在只有锚点、`scripted` 和导航的 `left_fold` 带，`run` 默认右手）；
      6. `park_search`：每组目标带自己的手，肩和朝向偏好按手镜像，`find_park` 收两只手的 `kin`，排序 IK 按手分批，`arrive` / `travel` 是整机姿态（第 7 节"哪只手"）；
      7. 第 ⑤ 层和 job 里写死右手的：`motion_skills.posture`、`run_skill` 的 `find_park(rig.kin, ...)` 和失败出口 `plan_clear(rig.kin, ...)`（要用找到的那组目标的手，不然左手推门失败时退不出来）、`open_job` 的 `rig.kin` / `rig.fingers()` / `_handle_grasp` 登记，都按 `side`。
      不在这一步：pick / place 选手（"用哪只手"进它们的目标集合，每次取放的候选都变，等于换基线，等有了全量基线单独做）；一只手拿着东西时用另一只手开门（第 6b 步）；`check_held` / `check_left_held` 合并（左手会多出 `held_shift` 重锚和掉了张手，旧代码左手的行为跟着变，随第 10 步或左手第一次取放）；两手一起搬的闭链（第 9 步）；`HELD_SPHERES` 右 140 / 左 60 不变（cuRobo 整个模型 512 个球的上限下的分配，4.4；左手将来拿大东西时拟合会粗一些，第 9 步选手时再看）。
      检查：
      - FakeKin 单测补左手的版本（`tests/test_symmetry.py`）。FakeKin 的 TCP 是 `q[:3]`，和共用的 q_body 重叠，所以左手的单测只比关节值（q_body 保持、段带 `side`、停车点镜像和按手的 kin），不比 TCP；补的单测：另一只手拿着东西时段里 q_body 不动、姿态目标不改 q_body、停车点搜索按手。（另一只手的东西两种表示要 cuRobo，只在仿真里查。）
      - 右手不变：针对性对照 4–5 集（含一集旧代码用左手的），成败、锚点和段的重做、失败类别和改之前一样；
      - 左手能用：一个诊断开关，强制用左手跑已经迁好的 open（空手开冰箱、柜门 2–3 集），单独判，不进基线。6b 之前左手的新路径（`grip(side)`、左手的把手登记、按手搜停车点、按手的执行）要在仿真里跑过，不然 6b 失败时分不清是对称化的问题还是关门设计的问题。
      **检查结果（11-11，`/data/zenobench/sym6a_1111`，v6 sticky/gt，HEAD 68dd48f + 未提交改动，单测 379 个、stop_check 都过）**：
      - 右手不变（对照 `sidepinch_1111`）：T02 block_put_away、T25 cold_one 的 21 / 8 个调用逐条相同，停车点和构造次数相同（T02 取方块 38 次、T25 取果汁 14 次），锚点 24 / 10 个、重做 0；两集都停在旧关门的 `hand_empty(hand=right)`，和改之前一样。
      - 左手能用（`ZENO_OPEN_SIDE=left`）：3 次左手开门都成功——T25 冰箱（正面捏，-1.036 / -1.05）、T05 柜门 4（侧钩 20°）、柜门 6（侧钩）；停车点换到了左手那一侧（柜门 6：右手 (2.872, 0.833, −30°)，左手 (2.827, 0.492, −30°)），握上、底盘带门、松手、收臂都走新路径（`left_grip`、左手的 `_handle_grasp`）。后面的调用和对照（T05 `maxdt_1111/runs3`）逐条相同，PhysX 接触和意外接触的条数也相同。
      - 没查到的：另一只手拿着东西时锁 q_body、另一只手的东西两种表示——这 4 集里干活的手对面都是空的，要到 6b 右手拿着东西、左手推门时才第一次用上。
   **6b. 关门，开门用空着的手（11-12，a33d852，见第 6 节关门）**：第 6 节关门（目标集合 = 空着的手 × {推，握把手}，推门 `plan_push` 复用 `hinge` + `ride`）。同一步把开门也改成用空着的手：只有一只手空时用那只手（`open_job` 的 `side`），两只手都空时照旧右手（不换基线）；合约 `contract_048` 的 `hinged_door` / `refrigerator` / `drawer` 前提从 `hand_empty(hand=right)` 改成至少一只手空，`left_holds_load`（旧 `_move_with_retry` 压腰）退役，微波炉不动（第 8 步）。11-11 全量的 31 次开门里没有一只手拿着东西去开的，所以开门这一半靠关门的 13 次（右手拿着东西、左手干活）验证锁 q_body 和另一只手的东西两种表示，再放开。
      **检查结果（11-12，`/data/zenobench/close6b_1112/runs_final` + `runs_final_t20`，v6 sticky/gt，单测 382 个、stop_check 都过）**：
      - 右手拿着东西、左手关门 5 次全成功：T25 冰箱（把手下方推）、T20 柜门 6、T19 柜门 6 和柜门 4（都是把手上方推；柜门 4 先 `push_body` 降躯干）。T25 cold_one、T20 bottle_put_away 两集整集成功（改之前都停在关门的 `hand_empty(hand=right)`）；T19 关完门以后停在看书架的视线被挡（原有的 look 那一类）。
      - 空手关门 4 次全成功：T02、T20 右手握把手，T05、T19 左手推。右手推这几扇柜门在快关上时夹爪、相机撞台面（"static"），所以选了别的做法。
      - 连锁变化：T02 block_put_away、T05 pen_in_6 关门以后的取物（层板上的 `floor_block`、`pen`）失败了："找不到够得着的抓法"，60 / 48 次构造都没成。改之前这两次取物也很勉强（T02 第 38 次构造才成），关门方式变了、机器人之后的停车点跟着变，就没取到。这是取物那一侧的问题，不是关门的。
      - 两个仿真同时跑时 T20 在关柜门 6 时 CUDA 显存不够，单独重跑整集成功。
      - 一只手拿着东西时用另一只手开门：v6 里没有这种集，没在仿真里跑到。
7. **接触类**：推桌上的物体已先做（11-12，2d2aff1，第 6 节）：推到桌边和旧 `skills.push` 的其余 7 个调用方都走 `push_object`，`skills.push` 删了；原则审查后（11-12）：选边、pull、separate 的重试换成一次搜索的目标；进入按 pick 的规则、离开按 `contact_extent` 实测；耦合加死区；段长不写死（`scripted` 的 `reach`、`Problem.relay_from`）；骑门段不复用。
   **检查结果（11-12，`/data/zenobench/slide_review_1112`，v6 sticky/gt，HEAD 88efcbf + 未提交改动，单测 402 个、stop_check 都过；对照 `slide_1112`）**：
   - 8 集的推全部成功，都是从后面推。推完的锚点上预测和实测差 1.2–3.4 mm（加死区之前 9.4–13.9 mm）；实际推的距离比要求的少 1–3 mm（几何没解释的那约 2 mm；之前因为 `SLIDE_SHORT` 重复算，多推 4–7 mm）。离开段 8–9 个路点、约 2.5 cm（之前退 2.5 cm 再抬 10 cm，34 个路点），锚点处都原样保留。T26 要推 45 cm，一段推完（之前 25 + 20.5 cm 两段）。
   - 没触发的：每次都有停车点能一次推完，段在够不着处截短（`reach`）和按能推多远二分排序都没在仿真里用上，只有单测。
   - 整集 5/8，对照 5/8：T01、T07、T26、T29 several 照旧成功；T15 book_free 由失败变成功（推完以后的翻书成了）；T15 book_out_of_view（翻书）、T29 homework（取作业本）照旧在推完以后失败；T05 由成功变失败。
   - T05：推、取都成了，放书走旧的 `place_flat`，手臂去 `flat_pre` 时停在离指令 35.7 cm 处，两个腕关节被顶到限位（关节 6 在 +0.785、关节 7 在 −1.571，指令是反方向），`place_flat` 再拿指令 TCP 和实测的书比，误报成"it turned in the grip"（sticky 的焊接一直在，到达锚点上书相对手只偏 0.01–0.09 mm）。单独重跑逐位相同；旧代码全量（v6full_1112）里这一集是同一个失败（34.3 cm、同样卡在两个限位）。推完的伸出量变了（7.47 cm，之前 8.24 cm），后面的搬运和放书的停车点跟着变，这一集在旧 `place_flat` 上时好时坏，归 2.7 步（书进 `plan_place`）。
   - T29 several 第一次是两个仿真同时跑时取书的停车点搜索里 CUDA 显存不够（11.8 + 10.3 GiB），单独重跑成功。
   - 代价：两条边都能伸出的集（T01、T05、T15），推的停车点搜索从 10–14 s 变成 16–24 s：16 组目标各自生成一圈候选、各自查底盘占地（`candidates_reach_footprint` 9.5 → 18.9 s），排序 IK 只多约 1 s。同一位置的几组目标共用底盘候选是第 10 节已有的一项。其余按 v6 用量排，依次是 stir、wipe、roll / flip、expose、press / touch、push、sweep、pour。先加 `tool_frame` 标注和它的解析（第 6 节接触类技能），再迁第一个技能，否则 9 个技能各写一遍换算。删 `LEGACY` 直线和"到不了的点跳过"。
   **stir（11-15，见第 6 节接触类和 `../skills/stir.md`）**：先加了 `tool_frame`（勺子两端 `bowl` / `handle`，`tools/prepare_assets.TOOL_FRAMES`）和它唯一的解析 `skill_jobs/tool.py` 的 `tool_in_tcp`，伸进锅里的是离手远的那一端（`free_end`：勺子捏在勺碗那头，搅的是勺柄，和旧代码一样）；`plan_stir` / `stir_job` 按接触类的形状：到达 → 自由段（勺子已倾斜）→ 下勺 `straight` → 画圈 `scripted`（`Still(锅)`，整圈要么全过要么失败，删了"到不了的点跳过"）→ 锚点 → 向上 `straight` → 回到进来时的姿态。两个自由段用 `FREE_HAND`，不保持倾角：4a48b66 的倾角规则在旧层由 `rig._carrying()` 对一切手里的东西打开，勺子转到 50° 的路上超过 1.02 rad，v6full_1115 的 T09 lid_off、tomato_elsewhere 因此失败；规则本身不改，按段的 `Spec` 不再套到工具上。勺子碰锅：`Spec.touch` 加了 `(名字, "held")`（手指和 held link 可碰，手臂其余部分照查）。圈数仍按勺尖实测（`Rig.tick_watchers`，每 4 个物理步一次）。`tooluse.py` 的 `old_entry` 17 → 11。
   **检查结果（11-15，`/data/zenobench/stir_1115`、`stir2_1115`，v6 sticky/gt，单测 462 个都过）**：第一轮只标了勺碗，勺尖离 TCP 3 cm（勺子捏在勺碗那头），T09 lid_off、tomato_elsewhere 停车点全部建不出来（画圈、下勺撞），pot_in_use 搅成了 1.25 圈。改成标两端、用离手远的一端（勺柄，`t_tool` 13.9 cm）以后：lid_off nominal、tomato_elsewhere dining 都在第一个停车点上一次建成，搅 1.25 圈，整集成功（1115 两集都是倾角失败）。没查到的：pot_in_use 第二轮被 30 分钟上限截在搅拌之前；tomato_in_fridge、pot_in_dining_room、lid_on_spoon_away 没跑；去掉的腰 0.3 rad 限制在这两集里没出问题。
8. **微波炉和电器动作**：`drive_part`、`toggle`、电机开门前让开的检查。删 `withdraw_microwave_cavity` 记的 `microwave_retrieval_q`（pick 已经不读；`policies/embedded.py` 的 `PickFromCavity` 还在用）。
   **8a 按键已迁（11-24）**：catalog `press`（形状 contact，`skill_jobs/press.py` 的 `press_job` + `skill_plans/contact.py` 的 `plan_press`）：到达锚点 → 自由段到按钮前 `PRESS_APPROACH`（10 cm）→ 在那里合爪（在原地合，刚放到灶上的锅被夹住，T07 microwave_holds_pot）→ 直线按进去，指尖压进按钮碰撞体正面 `PRESS_DEPTH`（3 mm）→ `toggle` 动作 → 锚点 → 按 `contact_extent` 量出来的直线退出 → 收臂。按钮的碰撞体有了自己的 owner（`scene_geometry.buttons`：`button:<电器>/<键>`，`Spec.touch` 只放开它；底盘占地、支撑面、监视仍把它当静态，`is_static`），监视还认按钮自己的标注障碍物盒（`kitchen_microwave/body/door_button`），不放开整台电器。停车点搜索：按的终点、手绕按的方向转 0 / 90 / -90 / 180° 四个目标；删了写死的首选站位（75°）和"首选站位不行就退到不查按的搜索"（T07 microwave_works 失败的原因，01ea02cc 的补丁随旧函数一起删）。微波炉开门键、启动键、灶的电源键（policy_032 / 033 / 094）都调 `skills.press_button`；分步的 027 / 028 / 029 退役，press 的启动键路径改成 policy_032。
   检查（`/data/zenobench/press8a_1124/runs2`，v6 sticky/gt，单测 533）：T07 microwave_works、microwave_holds_pot（灶）、T09 lid_off（灶开、关）整集成功；按键 8 次，7 次一次成功，1 次在 `press_pressed` 锚点重做收臂时 cuRobo TRAJOPT_FAIL（和 T02 / T19 关柜门同一类，收臂每个锚点都重做）。T07 two_portions、vessel_decides_appliance 在按键之前、往灶上放东西时失败：两集的第一次停车点搜索计数和 v6full_1123 一样（占地、碰撞相同）、选中的停车点不同，是 cuRobo IK 历史（这次是进程里第一集），不是按键的改动。
   **8b 开关门都按开门键（11-24，用户：不再"隔空"关门）**：微波炉的门只由它的开门键动：`plan_press` 在收臂以后多 `press_door`（门从现在的值转到目标的一路上，每 `PRESS_DOOR_STEP` 0.1 rad 查底盘 `BaseModel.clear` 和手臂 `free_at`（两臂都不动，和 ride 的查法一样），都让得开才排一个 `drive_part` 动作）和 `press_door_moved` 锚点。停车点搜索在每个候选上建整份计划，所以选出来的停车点既按得到键、又让得开门：删了写死的让开位置 (5.1, 1.6, 150°)、`clear_microwave_door_sweep`、`_set_microwave_hinge`（进了 `Rig.drive_part`）和它的固定机位。按键用空着的手（两只都空用右手；右手拿着东西时左手按，v6 里没有这种集，没在仿真里跑过）。policy_030（开到让开位置）、031（不按键直接转门）退役；close 的 `powered_loaded` 路径和 retreat 的 `microwave_door_sweep` 路径删了，都走 policy_025 / 067。单独的 `press(door_button)` 仍只按、不动门（开关门是 open / close）。
   **收臂晚做（11-24，第 1 节第 8 条）**：锚点（或某段不成立）处从这里重做剩下的计划时，如果只有收臂做不出来（cuRobo TRAJOPT_FAIL），保留前面重做好的各段（builder 的 `Failure.info["partial"]`），收臂留到手臂真走到那里再按实测状态建（`run._late_tuck`，事件 `late`）；那时还建不出来技能失败（第 3 条）。停车点搜索仍要求整份计划连收臂都能建。T19 x6_gd_can_put_away__in_4 的关柜门因此过了（`door_moved` 锚点收臂重做失败，走到时建成），T02 gone_toy_block、T07 microwave_holds_pot 照旧成功（`/data/zenobench/latetuck_1124`）。
   检查（`/data/zenobench/door8b_1124`，单测 535）：T07 microwave_works、microwave_holds_pot、two_portions__counter、T10 x6_gd_can_put_away__in_cabinet 整集成功，10 次按键开关门全到位（-1.399 / -0.001）；T07 broken_oatmeal_away 失败在旧的腔体取物（`PickFromCavity` 读 `microwave_retrieval_q`，8d）。
   **9a–9c（11-24 / 25，[HAND_PLAN.md](HAND_PLAN.md)）**：9a 持物状态按手（033f3791：`Rig.held_by` / `set_held` / `hand_of`，一个按手的 `check_held`，左手补上重锚和掉了张手；旧技能遇左手持物明确报错 `right_hand_only`）。9b 契约和评分（a2288b35：手的取值加 `any` / `both`；v6 评分的 `["hand_empty", "right"]` 2256 处改成 `"both"`；已经用空手的 open 电机门、press、heat、stop、inspect 改成 `hand_empty(any)`）。9c pick 选手：目标集合 = 空着的手 × 抓法（左手每个目标多 `VARIANT_COST`，弱偏好），build 用那只手的 `kin`、搬运目标（左手的搬运点和"在身前"的范围按 y 镜像）、收臂；抓住后按手登记、焊接、检查；place / drop / stir / stack / cover 用拿着那个物体的手；`plan_navigate` 的搬运段按手（左手的 `left_carry_in`）；pick / place 一族的契约改成 `any`，放下的结果是"这个物体不在手里"；`skill_runtime` 的 `held_by` / `held_kind` 认两只手。检查（`/data/zenobench/hand9c_1124`）：强制左手（诊断开关 `ZENO_PICK_SIDE=left`，不进基线）T11 basket_gone_bowl_there、T04 cup_in_4、T22 by_kind 3/3 整集成功（T22 三次左手取放，含冰箱层板）；不强制 T09 lid_off 全用右手成功，T07 microwave_works 拿燕麦选了左手，放进微波炉还是旧代码只认右手 -> 失败（9d 迁过去以前都会这样）。
   **9d（11-25，部分做完）**：第一次（`/data/zenobench/hand9d_1125`，0/3）失败在收臂和抽出。之后先修了左手放下的收臂起点碰撞（8cba9d98，规划器两指各按实测值，`/data/zenobench/fingers_1125` 5/5）；再加腔体的抽出长度（`_off_load`）和 `place_exit`（沿开口出来），检查 `/data/zenobench/hand9d2_1125` 2/4：two_portions__counter 左手放进微波炉整集成功、microwave_holds_pot 成功；microwave_works、broken_oatmeal_away 失败在抽出（往上时左前臂进开口上方的机身框 1–2 mm）和收臂，`place_exit` 没触发（手在开口外）。取出没在仿真里跑过。用户 11-25：先提交，进 9e。详见 HAND_PLAN 第 7 节。
   **9e（11-25）**：lift / lower（`plan_held_move`，原地竖直一条直线）、hover（`plan_hover` = `plan_drop` 去掉松手）、present（`plan_posture` 到身前目标集合 + 转头段）走 `run_skill`，按拿着的那只手；检查 `/data/zenobench/hand9e_1125` 5/6（after_dinner 败在 pick takeout_tray，1125 也是）。`held_vertical_move` 随 9f 删。详见 HAND_PLAN 第 7 节。
   **9f（11-25）**：rotate / upright（`plan_posture` 到目标集合，upright 不保持倾角）、release（`plan_release`）、regrasp（place + pick）走 `run_skill`，按手；square 的摆正转角放进 place 的目标集合（`square=True`），不再 pick 后单独 rotate（pick 前量的转角随搬运漂）。检查：T02 rotate 2/2（一集左手）、T06 display_row 1/1（1125 败在左手 rotate）。详见 HAND_PLAN 第 7 节。
   **9g（11-25）**：touch / knock 走 `plan_press`（`TOUCH_DEPTH`）；wipe 走 `plan_wipe`（压下 `WIPE_PRESS` → 手臂擦的任务段，长度量出来 → 擦回 → 抬起），静态家具可以进 `Spec.touch`（`Motion._touch_key`）。检查 `/data/zenobench/hand9g_1125` 6/6，强制左手 wipe 成功；右手擦 12–16 cm（覆盖率 0.6–0.73），左手擦满 30 cm。详见 HAND_PLAN 第 7 节。
   **9h–9j（11-25）**：手势、tip、roll、flip、pour、brace、handover 迁到运动分层（roll / flip / pour 的检查仍失败），两手搬跳过；9j 收尾删了 `skills.py` 的旧开关门链和死函数，退役一批原语，旧入口 52 -> 21（剩两手搬、边走边取放、`check_held` 张手、sticky 瞬移）。详见 HAND_PLAN 第 7 节。
   **8c / 8d 腔体取放（11-24，没成）**：路由改到 pick / place（policy_015 / 061）以后放入 1/2、取出 0/1（`/data/zenobench/cavity8c_1124`）；停车点搜索的转储（`/data/zenobench/cavitydbg_1124`）：碗在腔体最前沿，门开到 −80° 挡住左侧、控制面板在右侧，正前方的窄带上右手的肘撞面板 / 机身、躯干撞门，29 次构造全失败。改动在 `git stash`（"9.3 step 8c/8d attempt 11-24"），旧腔体代码仍在用。用户定：先做选手（HAND_PLAN 9a–9c），再回来做（9d）。
9. **两臂**（计划见 [HAND_PLAN.md](HAND_PLAN.md)，11-24：pick / place 选手、剩下的旧技能一起迁，步骤 9a–9j）：两手一起搬的物体进碰撞模型（闭链约束另议）；pick / place 选手（6a 末尾）。手臂对称、`q_body`、共用躯干的规则、另一只手的东西进查询已在第 6a 步做；两只手一起动时手里的东西对另一条手臂查不到（held link 只对躯干和头有自碰撞，4.4），两手搬要另想办法。
10. **收尾**：删 `Rig.move_to` / `move_to_any` / `joint_path` / `move_left_to` / `leave`、旧的 `planner.find_park`，以及旧的按用途分的碰撞上下文（`Motion.scope` / `hand_open` / `carrying` / `released`、`Rig._planning` / `_fingers_checked`；`Motion.query` 6a 起已经是直接实现，4.4）。

每步单独提交，先针对性检查再全量（全量跑 v6，`COLLISION_PLAN.md` 第 5 节）。

**只降不升的计数**：静态审计的 `old_entry` 一类（棘轮，按文件计）：执行入口（`run.py`、`rig.py`）以外直接调 rig 旧运动入口的地方（`OLD_ENTRIES`：`move_to`、`move_to_any`、`joint_path`、`joint_path_via`、`move_left_to`、`leave`、`tuck`、`swing`、`follow` / `follow_smooth` / `left_follow` / `follow_both`、`drive_base`、`grip`）。现在 167 处（11-16 姿态类迁走以后；`skills.py` 25、`orientation.py` 24、`hand.py` 19、`extra.py` 18、`bimanual.py` 17、`embedded.py` 14、`tooluse.py` 11、`sticky.py` 8……；`skill_jobs/` 0）。每步迁移必须让它下降，第 10 步到 0。每个新 `build` 有 FakeKin 单测（`tests/test_skill_plans.py` 的写法）。

### 9.4 代码放哪

`skills.py` 约 2000 行，`policies/` 另有约 5400 行（量级，精确数用 `wc -l`）。迁移有 10 步，新的 `Skill` / `build` 要是继续往 `skills.py` 里加、旧的又注释着不删，它会长期背着死代码，同时还在变长。

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
| `BASE_TOL`、`HOLD_DRIFT`、`PICK_TOL`、`PLACE_TOL` 的值 | 9.3 第 2.1 步先记录实测偏差再定（记录已加；11-11、11-12 两次全量的 `ANCHOR_STATS.md` 已经有了，还没据此定值）；现在 `PICK_TOL` 取 `HINT_REACH` 1 mm、`PLACE_TOL` 取 `TARGET_TOL` 5 mm（8.4） |
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
