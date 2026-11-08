# 运动规划的分层设计（草案）

**状态：** 设计，未实现（2026-11-07）。代码现状见 `COLLISION_PLAN.md` 第 3 节和 6.2"pick / place 每段运动现在怎么做"；迁移顺序见本文第 9 节。

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
| `contact_segment` | 起点、方向、量好的长度、`Allow` | 不查碰撞的接触段（进入或离开） | `leave` / `_leave_contact`、`_approach` 的接触段 |

"还在碰"的判据写成具名函数（离周围不到 `LEAVE_GAP`；物体离开支撑面：再加"上升不到 `LEAVE_GAP`"；终点碰：不 free），不再各处手写。

## 6. 技能计划

**pick**（`plan_pick`，到达姿态是收起）：

| # | 段 | 原语 | Spec | State 推进 |
|---|---|---|---|---|
| 1 | 到达姿态 → 伸入段起点 | `free_leg` | FREE，手指查，物体是障碍物，手张到候选宽度 | — |
| 2 | 伸入段 → 抓取位姿 | `straight` | 同上 | — |
| 3 | 合爪 | 动作 | `closing(物体)` | `holding(物体, 按计划的抓取位姿)` |
| 4 | 抬起段 | `contact_extent` + `contact_segment` | `LEAVE_CONTACT`（物体离开支撑面） | — |
| 5 | 抬起终点 → 搬运姿态 | `free_leg`（搬运目标集合） | FREE，保持倾角 | — |

**place**（`plan_place`，到达姿态是搬运姿态）倒过来：自由段 → 放下段（`straight` 竖直，长度由 `contact_extent` 从"物体贴着支撑面"往上量）→ 松手（`released(物体, 落下 LEAVE_GAP 后的位姿)`）→ 抽出段（`straight` 沿夹爪轴；起点穿进物体时先 `contact_segment` 离开）→ `free_leg({收起, 下垂})`。

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
5. **按顺序构造计划**：`problem.build(state_at(state, park), k)`，第一个做出完整计划的胜出；有预算（最多 N 个或若干秒）；失败原因按类计数进 `diag`。
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

**静态审计（`tools/audit_collision.py`）暂停中**（11-07 起，本地开关 `.claude/audit_paused`，97b3f76）：重构会在文件之间搬计数点、新增审计还不认识的模块。恢复前要做：审计认识新原语（`free_leg`、`straight`、`contact_segment` 加进 `MOTIONS` / `TARGET_MOTIONS` / `MOVES`，`Spec(allow=...)` 按 `allow=` 查）；`run.py` 像 `rig.py` 一样算执行入口（`follow` 不计）、查询层像 `kinematics.py` 一样可以写 `coll_kw`；`find_park` 按顺序构造计划的循环不算重试；搬移的计数点用 `--update-baseline --allow-increase` 更新基线，提交说明写清楚搬了什么。然后删掉开关文件。

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
