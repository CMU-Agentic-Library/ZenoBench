# 运动规划的分层设计（草案）

**状态：** 设计；第 9 节第 1–4 步已实现（2026-11-07 / 08），pick / place 在用（微波炉里取物、书的 `place_flat` 除外），第 5 步起未做。代码现状见 `COLLISION_PLAN.md` 第 3 节和 6.2"pick / place 每段运动现在怎么做"；迁移顺序见本文第 9 节。

## 1. 为什么要改

现在停车点搜索（`planner.find_park`）和执行（`Rig.move_to`、`_approach`、`leave`、`tuck` 等）各自构造运动：搜索证明"存在某种走法"，执行再用另一段代码重新造一遍，各自选 IK 分支、各自定退路顺序。任何一处选得不一样，验证就不保证执行。11-07 查到的例子：

- T20 bottle_on_cabinet：搜索从放下段起点的 IK 解查直线，执行按位姿规划停在另一个分支上（差 2.47 rad），往下走手肘撞桌子。
- T01 overhang_ready：抓取位姿的 IK 解压在两个关节限位上，搜索求出来一次，执行同样输入重求 4/4 求不出。
- T05 pen：同一个底盘位置检查多个目标，结果只按底盘位置存，选中的停车点拿到了别的目标的计划。

6.2 先在 pick 伸入段、place 放下段上做了"搜索做计划、执行照着走"（`rig.relay_approach`、`Rig.move_relay`，未提交），针对性检查 6/6、35/39。本文把这个做法推广成整套结构。

## 2. 要求（都已在 `COLLISION_PLAN.md` 定下）

1. 只保留必要的中继位姿，中间的运动由规划器生成；不加手写路点（第 1 节原则 1、第 9 节）。
2. 停车点搜索和执行用同一个函数、同样的约束；执行照搜索的计划走，计划不成立就用同一个函数从当前状态重做（6.2"验证和执行用同一份计划"）。
3. 接触段：方向由任务定，长度由碰撞模型量，碰撞规则用 `Allow` 写明（第 2 节）。
4. 没有 fallback：做不出来，搜索时不要这个停车点，执行时技能失败（原则 2；过渡期的 `FREE_ELSE_STRAIGHT` 只留在旧入口）。
5. 持物：保持倾角、限速，手指和手里的物体都在碰撞模型里。
6. 每段运动记碰撞规则，接触监视照旧（第 5 节）。

## 3. 分层

| 层 | 负责 | 不负责 |
|---|---|---|
| ① 运动原语 | 从给定状态和关节角出发生成一段运动：关节路点、这段的 `Spec`、量出来的长度；做不出来返回原因 | 不知道哪个技能，不知道是搜索还是执行 |
| ② 技能计划（`build`） | 按技能顺序把原语串成计划，每段从上一段的**实际终点**出发；中间夹不动手臂的动作（合爪、松手），用小函数推进 `State` | 不选停车点，不执行 |
| ③ 停车点搜索（`find_park`） | 底盘候选、批量的便宜过滤、排序，按顺序调用 `build`，返回（停车点，计划） | 手臂运动细节 |
| ④ 执行（`Rig.run`） | 逐段复核、不成立就用 `build` 从当前状态重做剩下的、执行、读回状态、监视、日志 | 发明运动 |

搜索和执行都只通过 `build` 碰原语：

```
find_park                                  Rig.run（计划不成立时）
 └─ problem.build(state_at(park), k)        └─ problem.build(当前状态, 从这一段起)
      ├─ free_leg / straight                     └─ 同样的原语
      └─ contact_extent / contact_segment
```

## 4. 数据

### 4.1 `State`：事实或假设，不可变，没有行为

```python
@dataclass(frozen=True)
class Held:
    name: str
    T_tcp_obj: np.ndarray        # 物体相对 TCP 的位姿（实测，或计划里假设的）
    kind: str                    # pinch / edge / corner / bimanual
    pad: float = 0.0             # m 碰撞球放大：计划推算的持法（pick 合爪前规划的搬运段，HELD_POSE_MARGIN）

@dataclass(frozen=True)
class Hand:
    width: float                 # 手指张开宽度（每指 m）
    held: Held | None

@dataclass(frozen=True)
class State:
    base: tuple                  # (x, y, yaw)
    q_right: np.ndarray          # 躯干、腰 + 右臂 7 个关节（指令姿态）
    q_left: np.ndarray           # 左臂 7 个关节
    head: np.ndarray
    hands: dict[str, Hand]       # "right" / "left"
    objects: dict[str, Pose]     # 物体位姿（实测，或假设：刚放下落在哪）
    parts: dict[str, float]      # 可动部件的关节值
```

- 执行时 `rig.observe()` 从仿真读出；搜索时从当前状态用小函数改出假设：`at_base`、`with_arm`、`with_width`、`holding`、`released`，每个返回新的 `State`。`state_at(park)` = `at_base` + `with_arm(到达姿态)`（原地不动的候选保持现在的手臂）。
- **完整性要求**：凡是影响碰撞查询的都在 `State` 里（头和左臂也影响碰撞），否则搜索的假设和执行读到的对不上。
- **不放进去的**：

| 东西 | 放在哪 |
|---|---|
| 碰撞规则（查不查手指、豁免、允许碰什么） | 每段的 `Spec` |
| cuRobo 对象、碰撞世界缓存 | `Motion`（查询层） |
| 运动学模型 `kin` | 原语的参数 |
| sticky 焊点、接触监视记录、日志、画面标题 | `Rig`（只在执行时有） |
| 计划 | `Plan` |
| 家具、静态场景 | `WorldModel` |

### 4.2 `Spec`：一段运动按什么规则做

```python
@dataclass(frozen=True)
class Spec:
    allow: Allow                 # FREE / LEAVE_CONTACT / closing(...) 等（clearance.py）
    fingers: bool                # 手指进不进碰撞模型
    exempt: tuple = ()           # 豁免的目标（持物时恒为空）
    hold_tilt: bool = False      # 持物保持倾角
    touch: tuple = ()            # 手指可以碰的物体：对手指不算障碍物，手臂其余部分另外查（11-08，place 抽出段）
```

由 `build` 给出、存进计划的每一段；`run` 执行时照它向接触监视声明。

### 4.3 `Segment` 和 `Plan`

- `Segment`：名字（`pick_grasp`、`pick_lift`…）、`Spec`、关节路点（动作段没有）、起点关节角、这段要到的目标（位姿或目标集合，复核用）、动作（合爪 / 松手宽度）、构造时量出的长度。
- `Plan`：`Segment` 的列表、目标组 k、构造它的 `build` 和参数（重做用）。

### 4.4 碰撞查询层 `Motion.query(state, spec)`

把 `State` + `Spec` 翻译成一次 cuRobo 查询：锁定关节（底盘、另一只手臂、头、手指宽度）、把手里的物体挂到夹爪上、把 `objects` 同步成障碍物、开关手指碰撞球、目标豁免。取代现在的 `_planning`、`_fingers_checked`、`_carrying`、`hand_open`、`released`、`scope`。静态场景不变，物体按版本缓存，只同步 `State` 里变了的部分。

## 5. 运动原语

签名统一为 `primitive(kin, state, spec, ...) -> Segment | Failure(why)`。

| 原语 | 输入 | 做什么 | 取代现在的 |
|---|---|---|---|
| `free_leg` | 起点关节角；目标是关节角、位姿或位姿集合 | 自由空间运动：关节直线 / TCP 直线，不通就规划（位姿；再不通到目标的 IK 解）；集合用批量 IK 选关节走得最少的；`hold_tilt` 时保持倾角 | `_move_path`、`move_to_any`、`joint_path`、`tuck` 的规划部分 |
| `straight` | 起点关节角、终点位姿 | 查碰撞的 TCP 直线，从给定的关节角出发 | `cart_path` 的各种包装、`_approach_path` 的直线部分 |
| `contact_extent` | 起点、方向 u、"还在碰"的判据 | 沿 u 量接触持续多远：离开周围 `LEAVE_GAP` 再加 `LEAVE_MARGIN`，最多 `LEAVE_MAX` | `_exit_length` 的三种用法、`set_down_length` |
| `contact_segment` | `contact_extent` 量出的接触（`Extent`）、`Spec`（其 `allow` 是接触的 Allow） | 不查碰撞的接触段（进入或离开） | `leave` / `_leave_contact`、`_approach` 的接触段 |

"还在碰"的判据写成具名函数，签名都是 `(kin, q_from) -> touching(q)`：`near_world`（离周围不到 `LEAVE_GAP`）、`off_support`（物体离开支撑面：再加"上升不到 `LEAVE_GAP`"）、`in_world`（终点碰：不 free），不再各处手写。`contact_extent` 沿 u 求运动学直线到 IK 求得到的地方（最多 `LEAVE_MAX`），在上面量；到头还碰就是 Failure（不减半、不跳过）。

## 6. 技能计划

**pick**（`plan_pick`，到达姿态是收起）：

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达姿态 → 伸入段起点 | `free_leg` | FREE，手指查，物体是障碍物，手张到候选宽度 | — |
| 2 | 伸入段 → 抓取位姿 | `straight` | 同上 | — |
| 3 | 合爪 | 动作 | `closing(物体)` | `holding(物体, 按计划的抓取位姿)` |
| 4 | 抬起段 | `contact_extent` + `contact_segment` | `LEAVE_CONTACT`（物体离开支撑面） | — |
| 5 | 抬起终点 → 搬运姿态 | `free_leg`（搬运目标集合） | FREE，保持倾角 | — |

**place**（`plan_place`，到达姿态是搬运姿态）倒过来：自由段 → 放下段（`straight` 竖直，长度由 `contact_extent` 从"物体贴着支撑面"往上量）→ 松手（`released(物体, 落下 LEAVE_GAP 后的位姿)`）→ 抽出段（`straight` 沿夹爪轴，刚放下的物体在 `Spec.touch` 里：手指可以碰，手臂其余部分不能）→ `free_leg({收起, 下垂})`。

抬起段、搬运段、抽出段、收臂都在计划里，`COLLISION_PLAN.md` 6.2 表下"还对不上的"四处在这个结构下不存在；`carry_pose_kept`、`carry_in` 的 `FREE_ELSE_STRAIGHT`、抬起段减半 / 不抬这些退路随之删掉。

## 7. 停车点搜索

```
find_park(problem, state) -> (park, k, plan) | Failure(diag)
problem = (goals, build, arrive)
```

| 字段 | pick | place |
|---|---|---|
| `goals`：若干组中继位姿（目标集合），每组带代价 | 每个抓取候选一组（取代 `for g in cands`，`COLLISION_CLEANUP` 3.5、6.1 第 8 项） | 每个"空位 × 物体姿态 × 手腕朝向"一组 |
| `build` | `plan_pick` | `plan_place` |
| `arrive` | 收起 | 搬运姿态 |

1. **候选**（`base_candidates`）：围绕每组目标的中心按半径、角度取点，每点多个朝向；加"原地不动"。
2. **批量便宜过滤**：够得着（肩到目标距离、高度）；底盘柱体不碰（`world.footprints_clear`）；到达姿态下整机不碰（`Motion.base_depths`）；从当前位置算一次底盘可达场（`base_reachable` 那套），查表得"开得到吗、多远"，取代每个候选一次完整底盘规划（`_drivable`）。
3. **批量 IK（只排序）**：中继位姿换到底盘坐标系，纯运动学批量 IK，得到有没有解、关节余量、可操作度。不查碰撞（cuRobo 的碰撞世界随底盘变，不能跨底盘位置成批）；碰撞留给第 5 步。批大小固定，避免 CUDA graph 重录。这一步不是验证，可以去掉（见第 10 节）。
4. **排序**：开车距离 + 目标组代价 + IK 质量，对全部通过的候选排序（现在是凑够 4 个就停、只在这 4 个里排）。
5. **按顺序构造计划**：`problem.build(state_at(state, park), k, q_rank)`，第一个做出完整计划的胜出；有预算（`BUILD_S` 20 s、`BUILD_MAX` 60 个）；失败原因按类计数进 `diag`。
6. **精确底盘路径**：只对胜出者做 `base_planner.plan`；做不出来（可达场是近似）回第 5 步取下一个。

`check`、`ride`、`score`、`unfold`、`carry`、`q_start` 这些开关不再需要：技能要查的东西都在自己的 `build` 里（开门跟随部件也在开门的 `build` 里）。

计划按（停车点，目标组 k）存，不只按底盘位置存（T05 pen 的教训）。

## 8. 执行

```
Rig.run(plan, state):
  for seg in plan:
     why = seg.holds(state)          # 复核
     if why: plan = plan.build(state, from=seg)    # 用同一个函数重做剩下的整段计划
             做不出来 -> SkillFailure(原因)
     execute(seg)                    # 向接触监视声明 seg.spec.allow，按手里的东西限速，跟随
     state = observe()               # 动作段后按仿真结果更新（抓没抓到、放下的物体落在哪）
```

**复核**（`seg.holds`）：手臂在这段的起点（`PLAN_AT_START`）；这段的目标没变（重新测量、底盘误差在 `HINT_REACH` / `HINT_TURN` 内）；路点在现在的世界里不碰；接触段用 `contact_extent` 从当前姿态重量，和计划的一致。

**重做的范围**：从出问题的那一段到计划末尾（后面的段都从前一段的实际终点出发）。

**失败只有两类**：计划做不出来（原语返回原因）；仿真结果不对（被挡住停在半路、没夹住、物体没跟上来）。意外接触只当指标；搬运中掉了抛 `Dropped` 给上层。

**pick 到位后的分支**：

| 段 | 复核不成立的典型原因 | 失败出口 |
|---|---|---|
| 1 自由段 | 开车碰动了物体；底盘停偏；原地没开车手臂不在行驶姿态 | 重做做不出来 |
| 2 伸入段 | （第 1 段原样执行时总成立） | 停在半路（> `PICK_REACH_TOL`）→ 沿夹爪轴退出，失败；碰动物体只记 `approach_moved` |
| 3 合爪 | — | 没夹住 → 张开、竖直离开，失败 |
| 4 抬起段 | 实际握法和计划不同，重量的长度不一致 | 量不出来（6 cm 内一直碰、没 IK）→ 失败 |
| 5 搬运段 | 带着物体的路点现在碰 | 重做做不出来 → 失败（不再留在原处） |
| 收尾 | — | 物体没跟上来 → 放开登记，失败 |

**旧入口**：`move_to` 只留给还没迁移的技能，等于"一段 `free_leg` 的计划 + `run`"；过渡期的 `FREE_ELSE_STRAIGHT` 只留在这里，迁完一个技能少一个调用方。

## 9. 迁移

1. `State`、`Spec`、`Segment`、`Plan` 数据结构；`Motion.query` 先包一层，内部按 `State` 调现在的上下文管理器。
2. 四个原语，复用现在的实现（`relay_approach` 拆成 `free_leg` + `straight`；`_exit_length` → `contact_extent`；`leave` → `contact_segment`）。
3. `plan_pick`、`plan_place`、`Rig.run`；pick、place 切过去（含抬起段、搬运段、抽出段、收臂），删 `carry_pose_kept`、`carry_in` 的 fallback、抬起段减半。
4. `find_park` 新接口（第 7 节），pick、place 用；旧接口留给其他技能。
5. 针对性检查（11-07 的 6 个 + 6.2 的 39 个）、全量，定新基线。
6. 其他技能改到时（`COLLISION_PLAN.md` 6.3、6.4）逐个迁；全部迁完删旧入口和 `_find_park` 的开关；`Motion.query` 里的上下文管理器换成直接实现。

不一次全改：基线整体变，倒退分不清来源（原则 4）。

**进度（11-07）：** 第 1、2 步已做：`zeno_skills/motion_state.py`（`State`、`Hand`、`Held`、`Spec`、`Segment`、`Failure`、`Plan` 和 `at_base`、`with_arm`、`with_width`、`holding`、`released`、`with_object`）；`zeno_skills/primitives.py`（四个原语、`Joint` / `Pose` / `PoseSet` 目标、`Extent`、三个"还在碰"判据、`exit_length`；`LEAVE_GAP`、`LEAVE_MARGIN`、`LEAVE_MAX`、`ON_LINE` 从 `rig.py` 搬来，`rig.py` 从这里 import，`Rig._exit_length` 转调 `exit_length`）；`Motion.query`（包一层：底盘、另一只手臂、头和手指的锁定值、手里的东西挂上 / 不当障碍、物体和部件按 State 挪、`coll_kw` 由 Spec 给，退出全部复原；`Motion.object_frames`、`_held_owners`、`_part_poses`）；`zeno_skills/run.py` 先有 `observe(rig)`。单测 `tests/test_primitives.py`（15 个）。仿真里对比过（`/data/zenobench/statequery`，T20 s10 第一次 pick 后拿着瓶子）：按观测状态、手张开、瓶子放下、底盘挪开四种情况，`query` 和原来的上下文各 150 个姿态的 `free`、`near` 0 处不一致，查完全部复原；左手持物、部件挪动还没对比过。

第 3 步已做（11-08）：`zeno_skills/skill_plans.py`（`plan_pick`：张手 → 到伸入段起点 → 伸入 → 合爪（`holding`）→ 抬起（`off_support`）→ 去搬运姿态（`PoseSet`，保持倾角）；`plan_place`：到放下段起点 → 放下 → 松手（`released`，手张到抓取宽度）→ 抽出（起点在物体里时先 `place_pull_out_contact`）→ 收臂（收起，碰就下垂）；`set_down_length` 用原语重写）；`run.py`（`holds`、`execute`、`run`：每段前 `observe`、复核、不成立就用技能给的 `rebuild` 从这段重做剩下的，做不出来 SkillFailure；技能自己的步骤挂 hooks）。`skills.py`：pick 的停车点检查 `_pick_plan_check`、执行 `_pick_run`（hooks：伸入时盯物体、到位检查、合爪判断和登记持物、搬运后 `check_held`），结果判断拆成 `_pick_judged`；place 的检查 `_place_plan_check`、执行 `_place_run`（重新测量偏 > `HINT_REACH` 就从当前状态重做整份计划，取代原来"偏 2 cm 整套重做"）。删了 `_place_check`、`rig.set_down_length`；`_relay_check` / `Rig.move_relay` / `relay_approach` 只剩微波炉里取物用（6.4）。抬起段不再减半 / 不抬，搬运段不再 `FREE_ELSE_STRAIGHT` / `carry_pose_kept`（pick 里；navigate / place 前的 `_carry_pose` 还是旧的）。单测 `tests/test_skill_plans.py`（8 个）。

针对性检查（11-08，`/data/zenobench/plan1107`，11-07 全量的 6 个直线失败）：5/6。98 段里 91 段原样走计划，7 段执行时重做、都成：T01 抬起段重量 2.0 cm（计划 3.0）、接着搬运段碰了重做；T13、T20 ×2 物体在手里偏 3.9–4.6 mm 整份 place 重做；T20 ×2 松手后手指真卡在瓶子里，重量出 1.9 cm 的离开段，接着抽出。T01 s11 失败在书的旧 `place_flat`：搬运姿态由计划选、和以前不同，`place_flat` 换了停车点，它不查碰撞的 `flat_push` 卡住差 16 cm，书倒（52°）——书进新流程是待办。查出并修了一处建模错误：松手后模型里的手没张开（还是拿着时的宽度），手指"穿进"刚放下的物体，计划里多出 3–6 cm 的离开段、执行时再撤掉；修后重跑 T09 s11 28/28 段原样、T20 s10 11/11 段原样（重新测量偏 4.6 mm 先重做了一次），都成。

第 4 步已做（11-08）：`zeno_skills/park_search.py`（`Problem`（goals、build、arrive、travel、near、prefer）、`find_park`：候选 → 够得着 + 底盘柱体（逐个，每个目标最多 `MAX_PER_GOAL`）→ 行驶姿态整机（批量 `base_depths`）→ 可达场（`base_reachable`，一次）→ 批量运动学 IK 排序（中继位姿换到各候选底盘系、不查碰撞，按关节余量、可操作度、代价）→ 按顺序 `build`，第一个做出整份计划的胜出（`BUILD_S` 20 s、`BUILD_MAX` 60）→ 胜出者 `_drivable` 精确底盘路径；日志 `park_search` 带每项计数、构造失败原因和每段耗时 `stage_s`）。pick 的所有抓取候选合成一个目标集合（每个排名 `PICK_CAND_COST`），取代逐个候选找停车点（`COLLISION_CLEANUP` 3.5、`COLLISION_PLAN` 6.1 第 8 项）；冰箱层板的种子停车点走 `prefer`。place 的 `find_park_set` 换成同一个 `Problem`。删了 `_pick_plan_check`、`_place_plan_check`；旧的 `planner.find_park` 留给微波炉取物和其他技能。

搬运段余量（11-08）：`Held.pad` 放大手里物体的碰撞球；pick 计划里合爪前就规划的搬运段带 `HELD_POSE_MARGIN`（5 mm），执行时从实测持物重做的不带，抬起段不带（只给搬运段加，用户定）。起因 T01 s11：搜索出的搬运路径余量为 0，执行前复核在第 34/75 个路点"手里的书 0 mm 碰"，从当前状态重做 cuRobo `FINETUNE_TRAJOPT_FAIL`。`held_offset` 日志（计划假设的持物 vs 合爪后实测）在 sticky 下是 0–0.2 mm、0–0.15°（合爪即焊住），所以那次碰撞不是持物偏了，更像规划器查轨迹和执行前 `path_free` 按 0.05 rad 插值查之间的差；余量留出这层缓冲。`physical`（不焊）下要按实测偏差再定。

第 4 步针对性检查（`/data/zenobench/park1108`）：第一轮 3/6——T20 ×2 找不到停车点（构造预算 8 个太少，前 8 个里 5 个伸入段直线进柜子会碰）、T01 搬运段如上；预算改按时间、加搬运余量后重跑 T20 s10、T01 s11 都成（T20 构造 14 个找到）。T09、T13、T12 第一轮就成；T20 s11 改后没重跑。搜索耗时：pick 18–22 s（旧版 T20 约 9 s），`stage_s` 显示大头是持物去搬运姿态的规划（单次 8–14 s），待查。

持物自由段的规划顺序（11-08）：拿着东西、有目标的 IK 解时，`free_leg` 先关节规划到解，倾斜超标或失败再按位姿保持倾角规划（`Kinematics.plan(carry=True)`），不再走 `plan_to` 的"按位姿保持倾角 → 关节 → 再按位姿保持倾角"（第三次和第一次是同一个问题，等于藏起来的重试）。逐次计时（`/data/zenobench/carrytime`）：保持倾角按位姿规划本身单次 0.6–8.4 s、失败时用满尝试次数约 6–8 s，关节规划约 2 s 但几乎总让物体倾斜超标——搜索没有明显变快（pick 4–26 s），慢的问题留着，全量后再定（调小保持倾角规划的尝试次数，或让搬运目标优先选关节直走倾斜不超标的）。

撤手段手指可以碰刚放下的物体（11-08，用户定）：`Spec.touch`——这些物体对手指不算障碍物（`Motion.query` 里加进 `_query` 的豁免），手臂除手指外另外查不能碰它们（`Motion.path_free_only` / `Kinematics.path_free_only`，`primitives.free_path` 合两次，`straight` 和执行前复核都用）；`Allow(touch=(物体,), links="fingers")` 让监视器记成允许的接触。撤手段于是总是一条直线，删了起点在物体里时的离开段（`place_pull_out_contact`）；撤手开始时模型里手指在物体里记 `place_pull_out_touching`。

这一轮 6 个（`/data/zenobench/park1108/run4`）：5/6，T13 s10 松手后杯子靠到手指上、沿夹爪轴只能退 2 cm 就没 IK、还碰着杯子而失败；改成撤手段手指可碰后重跑 T13 s10、T20 s10 都成（T13 撤手开始手指在杯子里 1 mm，照计划走完，杯子离目标 1.9 cm）。

**静态审计（`tools/audit_collision.py`）暂停中**（11-07 起，开关文件 `.claude/audit_paused`，97b3f76；11-08 起提交进仓库，干净的 checkout 也跳过）：重构会在文件之间搬计数点、新增审计还不认识的模块。恢复前要做：审计认识新原语（`free_leg`、`straight`、`contact_segment` 加进 `MOTIONS` / `TARGET_MOTIONS` / `MOVES`，`Spec(allow=...)` 按 `allow=` 查）；`run.py` 像 `rig.py` 一样算执行入口（`follow` 不计）、查询层像 `kinematics.py` 一样可以写 `coll_kw`；`find_park` 按顺序构造计划的循环不算重试；搬移的计数点用 `--update-baseline --allow-increase` 更新基线，提交说明写清楚搬了什么。然后在一次提交里删掉开关文件。

## 10. 待定

| 问题 | 倾向 |
|---|---|
| ~~执行时重做不出来，要不要回去重新搜停车点~~ | **定了（11-07）：直接失败** |
| 搜索第 5 步：第一个做出计划就选，还是做 N 个按计划质量选 | 第一个；排序保证质量，构造计划最贵 |
| 构造计划的预算 | 先定 8 个或 15 s，按 6.2 那 39 个量 |
| 搜索第 3 步的批量 IK 要不要（不查碰撞，只排序，是另一套判据） | 先留，量排序准不准；不准就去掉，手臂质量从做好的计划里算 |
| 接触段执行时重量（放下后杯子转到手指上，模型预测不到） | 复核里重量，不一致就从当前状态重做剩下的计划 |
| ~~pick 的计划包含去搬运姿态~~ | **定了（11-07）：包含**（停车点会变、搜索多一次持物规划） |
| `Motion.query` 直接实现还是先包一层 | 先包一层，pick / place 迁完再换 |

## 11. 其余技能要的原语扩展（草案，11-08）

**来源：** 11-08 对 pick / place 以外各技能现在怎么动的盘点（开关门和电器、工具和接触、搬运 / 姿态 / 左臂三组，代码 c13fb18），以及 v6 路线用到它们的次数（`COLLISION_PLAN.md` 6.2–6.6）。目标不变（第 2 节）：只留中继位姿，中间由规划器生成；搜索和执行用同一个 `build`；没有 fallback；接触段方向由任务定、长度由碰撞模型量、规则用 `Allow` 写明。

### 11.1 现在的四个原语表达不了的

| # | 需求 | 技能（v6 episode 数） | 现在怎么凑的 |
|---|---|---|---|
| a | **底盘运动是计划的一段**：开到停车点、带着东西开、直线退开；底盘就是任务动作（擦桌子沿条带平移、门跟着底盘转） | navigate（全部）、retreat 162、wipe 50、开关门 409 | `navigate` / `relocate` / `drive_base` 在计划外；搬运姿态在开车前单独定（`_carry_pose`，`carry_pose_kept` 退路）；擦桌子只查底盘占地 |
| b | **部件跟着手动**：部件关节值随这段变，手的路径被铰链圆弧 / 抽屉直线约束；目标是部件开度（`wide_open_q`），不是手的位姿 | open / close 409、hide 的柜子 | 手臂不动、底盘每拍按实测开度跟着部件转（`_ride`）；`_ride_check` 单独查；没声明 Allow |
| c | **物体被推着动**：推、拖、滚、翻，物体位姿在这段里变；扫过的体积没人查 | expose 16、roll 30、flip 30、sweep 10、推门关 | 目标豁免把物体整个拿掉；推完量位移 |
| d | **沿表面走的接触段**（切向）和**任务给定深度的进入**（按钮按 5 mm、海绵压 1 mm、指尖压 2 mm） | wipe、stir 60、press 10、touch 10、push、roll、heat / stop | `LEGACY` 直线 |
| e | **任务轨迹**：画圈（循环）、翻书绕棱转 105°、原地转手腕、擦条带 | stir、flip、rotate 23、wipe | 逐点 `move_to`，到不了的点跳过 |
| f | **工具坐标系的目标**：勺尖在锅里、海绵底面贴台面 | stir、wipe | 在技能里手算 TCP |
| g | **持物故意改变倾角**（勺子倾 50°、翻书）和"保持倾角"冲突 | stir、flip | 规划不出来时走直线退路 |
| h | **部分关节的目标、关节目标集合、锁关节**：只动腰（bend / straighten）、收臂 {折叠, 下垂}、腰上限压 0.25 / 0.3 | bend / straighten 138、所有收臂、左手持物开门 | 整个 9 维向量凑；`rest_goals` 在原语外挑；改 `kin.hi` |
| i | **抓的是部件**（把手）：手指可以碰部件，松开不用抬离 | open / close | `coll_kw={hand_touches_part}` 设了不恢复 |
| j | **不动手臂的动作**：等待、电机开门、加热开关 | heat 110、stop 30、微波炉开关 | 技能里直接调 |
| k | **放下后物体位置不确定**（drop 掉下去），后面的段要等看到再做 | drop 210 | `released` 假设落下 5 mm |
| l | **另一个机构让部件扫过一片空间**（电机开微波炉门），机器人要先让开 | 微波炉相关 | 写死底盘位置 (5.1, 1.6, 150) |
| m | **左臂、两臂一起** | 双手搬、交接、左手持物 | 左臂直接插值不查；`follow_both`；两手搬的物体不在碰撞模型里 |

### 11.2 `State` 的改动

1. **手可以握部件**：`Held` 加 `kind="part"`，`name` 是部件，`T_tcp_obj` 是把手在 TCP 里的位姿。`holding` / `released` 照用。取代 `rig._handle_grasp` 和 `hand_touches_part`（握着时那只手的手指对这个部件不算障碍物，像持物一样）。
2. **持物带工具坐标系**：`Held.tool`（工具工作点在物体框里的位姿：勺尖、海绵底面中心），从资产标注来；目标可以写在工具坐标系里（11.4 的 `Frame`）。书的下垂也属于持物模型：执行时 `T_tcp_obj` 是实测（已经是），计划时用假设 + `pad`，不再在 `place_flat` 里补 `R_fix` / +6 cm。
3. **不确定的物体**：`objects[name] = None` 表示"位置待观察"：不是障碍物，后面要用它的段不能在这之前做（11.6 的观察断点）。
4. **两手持同一物体**：`hands["right"].held` 和 `hands["left"].held` 同名、`kind="bimanual"`，查询层把它挂在右手链上、对左手链不算障碍物（6.6 再做）。
5. 部件 `parts` 已在 `State` 里，`Motion.query` 已按它挪部件；这里只是开始真用。

### 11.3 `Spec` 的改动

| 字段 | 现在 | 改成 |
|---|---|---|
| `touch` | 手指可以碰的物体 | 可以碰的**物体和部件**，加 `by`：`fingers` / `hand` / `load`（持物可以碰：海绵碰台面、勺子碰锅、翻书时书碰支撑面） |
| `hold_tilt: bool` | 保持倾角 | `load: "free" / "level" / "path"`：`level` = 现在的保持倾角；`path` = 倾角跟着任务轨迹走（11.4 的 `path` 原语自己插值），不再和"保持倾角"打架 |
| （新）`joints` | 无 | 这段允许动的关节（默认右臂链全部）：只动腰、锁腰、左手持物时腰上限。取代改 `kin.lo / kin.hi` 和 `_lock_shared_posture` |
| （新）`moves` | 无 | 这段里跟着手动的东西：`Coupling`（11.4），查询时按路点把物体 / 部件挪到对应位置 |
| `allow` | `FREE` / `LEAVE_CONTACT` / `closing` | 加 6.5 的接触预设：`grasp`、`handle`、`press`、`sweep`、`set_down`；`LEGACY` 清零 |

执行参数（速度、`smooth`、`steps_per_wp`）留在 `Segment.info`，不进 `Spec`（它们不改变碰撞查询）。

### 11.4 原语的改动

一共五个原语加一类动作；现有四个里 `straight` 并进 `path`，`contact_extent` 扩成两个方向。

| 原语 | 变化 | 覆盖 |
|---|---|---|
| `free_leg` | 目标加 `JointSet`（任意一个，最便宜的）和 `Joint(q, mask)`（只给部分关节，其余保持起点）；"区域"目标（物体底面 ≥ h、在开口上方任意处）由技能采样成 `PoseSet`，不加区域求解器 | 收臂 {折叠, 下垂}、bend / straighten、lift、hover、drop 上方 |
| `path`（取代 `straight`） | TCP（或 `Frame` 指定的工具点）依次经过给定位姿序列，全段查碰撞，**全有或全无**（不跳点）；位姿之间直线插值位置、球面插值姿态；`closed=True` 首尾相接（画圈）；`Spec.moves` 给出时每个路点按耦合挪物体 / 部件再查 | 伸入、放下、抽出（两个位姿的 `path` 就是现在的 `straight`）；画圈、擦条带、翻书绕棱、原地转腕、开门圆弧、抽屉直线、按钮按下 |
| `contact_extent` | 判据加**进入**：沿 u 走到开始碰（`until_contact(实体)`）再走任务给定的深度（按钮 `PRESS_DEPTH`、海绵 `WIPE_PRESS`、指尖 `TOUCH_DEPTH`，具名常数登记在 `COLLISION_PLAN` 第 8 节，是力的几何替身）；离开不变 | 按钮、触碰、海绵下压、推之前贴上去、放下（现在的 `set_down_length` 就是反过来的离开） |
| `contact_segment` | 不变，跑 `contact_extent` 量出的段 | — |
| `drive`（新） | 底盘一段：从 `State.base` 到目标（或直线退开 d），`base_planner` 在给定手臂姿态（或姿态链）下规划，整机查碰撞（手里的东西、`Spec.moves` 的部件也算）；`State.base` 往前推；`Spec.moves` 给出时底盘带着部件 / 物体走 | 去停车点、带物开车、retreat、擦条带平移、门跟着底盘转、底盘推 |
| 动作 | `grip` 之外加 `wait(s)`、`drive_part(部件, 目标值)`（电机）、`toggle(电器, on/off)`、`observe`（观察断点）；动作也推进 `State`（部件值、电器状态） | heat / stop、微波炉门、drop 之后 |

**耦合 `Coupling`**（`Spec.moves` 的元素）：路点 → 被带着的东西的新位姿，几种写成具名函数，像"还在碰"的判据一样：

| 耦合 | 怎么算 | 用在 |
|---|---|---|
| `rigid(物体)` | 跟 TCP 刚性（就是持物） | 持物（已有，挪进来统一） |
| `hinge(部件)` / `slider(部件)` | 握着把手：TCP 在铰链圆弧 / 导轨上的位置 → 部件关节值 | 开关门、抽屉 |
| `pushed(物体, u)` | 接触后沿 u 平移，位移 = 手的位移 | 推、拖、expose、sweep、推门关（部件版本 `pushed_part`） |
| `rolled(物体, 轴)` | 中心走手的一半，转角 = 位移 / 半径 | roll |
| `pivot(物体, 棱)` | 绕支撑面上的棱转，转角 = 手绕棱的角度 | flip |

耦合给的是**计划用的预测**：查扫过的体积有没有碰邻居，长度和终点由它定。执行时以实测为准（11.7）。

### 11.5 技能计划和停车点搜索

- **抓法 / 手腕朝向变体都是目标集合**：把手的钩 / 翻转 / 正面、触碰和推的 4 个手腕朝向、搅拌的 4 个朝向、擦桌子的条带 × 朝向，都进 `Problem.goals`（和 pick 的抓取候选一样），取代"一个变体 `find_park` 一次"的循环。半径退到 0.022 / 0.012、撤掉腰上限再来一遍这类按参数重试删掉（F 类）。
- **navigate 进计划**：带物开车 = `free_leg`（搬运目标集合）+ `drive`；搬运姿态在 `build` 里按顺序试，第一个让 `drive` 做得出来的胜出（和停车点搜索一样的"按顺序构造"）。`carry_pose_kept` 删掉。pick 的计划已经停在搬运姿态，开车前多数不用再动手臂。
- **开关门的计划**：去停车点（`drive`）→ 到把手前（`free_leg`）→ 握上（`contact_extent` 进入 + `grip`，`holding(部件)`）→ 部件圆弧（`path` + `hinge`，够得着就手臂走）或底盘带门（`drive` + `hinge`，弧太长时）→ 松开（`grip`，`released`）→ 离开（`contact_extent` 离开）→ 收臂。只抓一次（现在 p046 抓了、p049 换停车点又抓，11-07 P12 日志）。
- **跨多个停车点的任务**（推每段 25 cm、sweep 逐个物体）：每段一次 `find_park`，段之间按实测结果决定下一段——这是任务层的闭环，不是运动的退路。
- **电机开门前让开**：`Problem` 里加一项检查"部件扫过它的范围时整机不碰"（`State` 里部件取几个值查），取代写死的 (5.1, 1.6, 150)。
- **微波炉里取放**：腔体和开着的门都在 `State` 里，水平伸入 / 退出是普通的 `path`；不再回放上次放进去时记下的姿态（`microwave_retrieval_q`），跨 contract 的状态标记（`_microwave_*`）只留电器状态，进 `State`。

### 11.6 执行

- `execute` 按段的种类：`follow`（已有）、`drive`（底盘）、`track`（带耦合的段：按实测部件值 / 物体位姿闭环跟踪，提前量、限速、卡住就停——`_ride` 现在做的那部分）、各种动作。
- `holds` 复核：带耦合的段用实测的部件值 / 物体位姿重新查；进入接触段从当前姿态重量。
- **观察断点**：`observe` 动作之后的段在执行时一定重做（计划里它们是按假设做的，只用来证明"存在"；drop 之后的收臂、推完一段之后的下一段）。

### 11.7 迁移顺序（按 v6 影响面）

1. `drive` + navigate 进计划（几乎所有 episode）；`JointSet` / `Joint(mask)` 顺带（收臂、bend / straighten）。
2. `Held(kind="part")`、`Spec.touch` 扩到部件、`Coupling.hinge / slider`、`path`、`track`：开关门（409）。
3. 扁平物体进 `plan_place`（持物模型带下垂，删 `place_flat`，130）；冰箱层板的放置（现在 `place()` 直接报"不支持"）。
4. 接触族：`contact_extent` 进入、`pushed / rolled / pivot`、`Spec.load="path"`、`Frame`：push / expose / roll / flip / touch / press / wipe / stir。
5. 微波炉和电器动作（11.5 最后两条）。
6. 左臂和两臂（6.6）。

每步单独提交、针对性检查再全量（原则 4）。`coll_kw` 设了不恢复的几处（开门、按钮、腔体取物、搬运姿态）随对应技能迁移消失。

### 11.8 待定

| 问题 | 倾向 |
|---|---|
| 开门：手臂走圆弧还是底盘带门 | 两种都留，按弧长选：手臂够得着整段就手臂走（底盘不动更稳），否则底盘带门 |
| 力的几何替身（压进去几 mm）够不够 | 先够：都是具名常数、按接触种类定一次；不够再加力反馈 |
| 推的耦合太理想（物体会转、会滑） | 只用来查扫过的体积和定长度；执行闭环看实测，偏了就重做下一段 |
| `path` 全有或全无会不会让画圈 / 擦条带太难找到停车点 | 画圈半径、条带是目标集合的一部分，搜索在集合里挑，不在执行时跳点 |
