# 底层策略的代码地图（`90a2a31`，2026-11-13）

这篇讲**代码怎么组织**：一个技能调用从哪里进来、经过哪几层、每一段运动在哪个函数里决定查不查碰撞，以及哪些还是旧的写死路径。物理上每一步做什么见同目录的各篇（[README](README.md)），为什么这样改、计划做什么见 [`../COLLISION_PLAN.md`](../COLLISION_PLAN.md)。

按 `90a2a31`（2026-11-13）核对过：模块、函数、常量、调用关系、数字和迁移表。行号对应 `90a2a31`，之后会漂移，**以函数名为准**。每次改动后，凡是改到下面某张表的内容，同一个提交里一起更新这篇。

---

## 1. 分层

调用只往下走，下层不调用上层。

```
episode/episode.py                 一次 episode：把规划器的调用交给合约执行器
  │
  ▼
skill_runtime.py  SkillContractRunner     合约（contract_library/skill_contracts.json，70 个动词）：
  │                                       绑定名词、检查前置条件、选一条 policy_plan 路径、
  │                                       逐个执行 policy、检查后置条件；sticky 的补救钩子也在这里
  ▼
policies/*.py     PolicySuite → XxxPolicy.execute     115 个原子策略（catalog.json），合约用到其中 101 个
  │        │                                          （另 14 个退役：skill_contracts.json 的 retired_policies）
  │        └───────────────┐  约一半的策略直接调 rig，不经过 skills（见第 5 节）
  ▼                        │
skills.py         技能本体：pick / place / navigate / 开关门 / 微波炉…
  │                        │  决定"中继位姿是什么、停车点在哪、接触段往哪个方向走"
  │   navigate / pick / place / open / close / push（MOTION_ARCHITECTURE 的五层，catalog 的 6 个 motion_skills）：
  │   motion_skills.py  ⑤ run_skill(rig, SKILLS[名], args)：头回正 → job → find_park → 开过去 → run；
  │                       SKILLS 读 skill_library/catalog.json 的 "motion_skills"
  │   skill_jobs/       ⑤ 每个技能的 job（目标集合、hooks、结果判断）：navigate / pick / place / door（open、close）/
  │                       slide（push：slide_job，和任务层一段段推的 push_object）；
  │                       base（RigBase：整机底盘模型）、carry（搬运判据、carry_posture）
  │   park_search.py    ③ find_park(kin, world, Problem, state, log, base)：底盘候选、便宜过滤、排序，
  │                       按顺序调技能的 build
  │   skill_plans/      ② plan_pick / plan_place / plan_navigate / plan_door / plan_push / plan_slide（build）：
  │                       原语串成整份计划，State 在段间推进；plan_clear（失败出口：张手、竖直退出接触）
  │   primitives.py     ① free_leg / straight / contact_extent / contact_segment / drive / drive_straight /
  │                       scripted（任务段：Script + 耦合 hinge / slider / still / pushed，ride_base）/ decide_ik；holds（复核一段：run 和 build 复用旧段都用它）
  │   run.py            ④ observe / execute / run：逐段复核、锚点复核剩下的整份、不成立就用 build 重做剩下的、执行；
  │                       只经过 Actuator（Rig 实现）碰仿真；锚点记实测偏差（anchor 事件 off），接触位姿段记 aim_off；
  │                       手臂跟完一段（hooks 之后）TCP 停在离指令超过 TARGET_TOL 处就失败（偏差是 follow 的返回值：
  │                       Rig._settle 量的，也记在 rig.last_off 给 hooks 用）；
  │                       失败出口：异常带 motion_state.clearing 时 run(…, clear=) → run_clear 先跑 clear 做的计划
  │                       （skill_plans.plan_clear），再抛
  │   motion_state.py   State / Spec / Segment / Plan / Failure（纯数据）；协议 Actuator、BaseModel；state_offset
  │   tolerances.py     误差上限、复核判据、接触几何、碰撞模型和接触监视、技能成败判据的阈值，各带单位和来源（TOLS）；primitives / skill_plans 从这里导入
  ▼                        ▼
rig.py            Rig：机器人运动的执行入口 follow / grip / clear（监视），实现 Actuator（snapshot / arm_kin /
  │                    declare / contact_allow / ride / wait / drive_base / swing）；_settle 返回 TCP 停在离指令多远
  │                    （rig.last_off）；每个物理步前 _payload_feedforward：手里东西的重量按 payload_torques 加到
  │                    关节力矩上（双手抬各一半，躯干和腰取两边之和；质心离 TCP 超过 PAYLOAD_REACH 的不算）；
  │                    旧入口 move_to / joint_path / tuck / swing / drive_base 还给没迁移的技能用
  │                    （move_to_any、leave 已没有调用方，只剩测试）
  ▼
motion.py         Motion：cuRobo 封装（IK、轨迹规划、碰撞世界、目标豁免、手持物体的碰撞球）；每条手臂自己一张
                  自碰撞表（arm_self_collision：共享表里和这条手臂有关的对，加这只手的持物对躯干和头 HELD_SELF_BODY，
                  另一只手的持物不在表里），动作开始时已经在躯干 / 头里的持物球关掉（_held_off_body）；
                  机器人自己的底盘是第二个碰撞环境（body_collision）
kinematics.py     ArmKin：正运动学 + 把逆运动学和碰撞查询转给 motion
scene_geometry.py PhysX 碰撞体 → cuRobo 障碍物
```

旁路模块：

| 模块 | 谁调它 | 做什么 |
|---|---|---|
| `park_search.py` | `motion_skills.run_skill`（pick、place、open、close、push） | **新的停车点搜索** `find_park(kin, world, Problem, state, log, base)`：能做出技能整份计划的停车点，连计划一起返回；不碰 rig，整机底盘的查询问传进来的 `base`（`MOTION_ARCHITECTURE.md` 第 7 节）|
| `planner.py` | skills、policies | **旧的停车点搜索** `find_park` / `find_park_set`（微波炉取物和其他技能还在用）：在哪个底盘位姿，手臂能无碰撞地走完给定的一串目标位姿。另有 `joint_reachable`、`_whole_body`、`_drivable`（只剩旧搜索用；行驶姿态取 `skill_plans.travel_chain`；没有整机模型时不查，由开车决定）。旧的网格路径 `plan_path` 11-10 删了 |
| `base_planner.py` | `skills._base_steps`（经 `skill_jobs.base.RigBase.plan`；`_base_plan` 只是给 `plan_drive` 的包装）、`planner._drivable`、`RigBase.straight`（`segment`） | **底盘路径规划**：在 (x, y, yaw) 网格上做 A*，同时考虑手臂姿态链（收臂 → 下垂 → 收臂）|
| `clearance.py` | rig、skills、policies、primitives、skill_plans、motion_state | `Allow`：一段运动允许碰什么（第 3 节）；`rig.clear`：接触监视器、fallback 计数 |
| `collision.py` | `runtime`（建 `WorldModel`，经 `rig.world` 给 planner、park_search、base_planner、`RigBase`）、`scene_geometry.body_world` | 底盘的世界：占地检查和内切圆放宽，对静态场景（PhysX 碰撞体按底盘两层的高度切成的带，`StaticBands`；没有 stage 时用标注包围盒）和活动部件。手臂的 IK 和碰撞不查这些框，但底盘两层的形状（`BASE_HALF`、`COLUMN_*`、`LOW_*`）是手臂规划的第二个环境（下一行） |
| `body_collision.py` | `motion.Motion`、`_Arm` | 机器人自己的底盘（`scene_geometry.body_world`，形状来自 `collision.py`）作为碰撞检查器的第二个环境：每个查世界的 cuRobo rollout 多一个代价项和一个约束项，查它时身体和另一条手臂的球关掉（`MOTION_ARCHITECTURE.md` 4.4） |
| `held_spheres.py` | `motion`（`_cached_fit`，按内容缓存到盘上） | 手持物体的碰撞球（`fit`）：按它的碰撞体（长方体、凸包）贪心拟合大小不等的球，表面每个采样点离某个球不超过 `HELD_SPHERE_GAP`，球伸出物体不超过 `HELD_SPHERE_OUT`；挂在手的 held link 上 |
| `sticky.py` | skill_runtime（`snap_pick`、`after_pick`、`snap_place`）、skills、`skill_jobs/pick`（`note_grasp`）、`skill_jobs/place`（`rest_R`）、`episode/profile`（`StickyHands`） | sticky hands（焊接、snap），只是执行辅助 |
| `physx_contacts.py` | clearance | 读 PhysX 的真实接触 |
| `annotations.py` / `predicates.py` / `scene_geometry.py` | 各层 | 场景和资产的真值、谓词、碰撞体 |

**名字容易混的两个**：`park_search.find_park` / `planner.find_park` 回答"停在哪"，`base_planner.plan` 回答"怎么开过去"。`skills.navigate` 只用后者；pick、place、open、close、push 先用前者（`park_search`）选停车点，再用后者开过去（`run_skill` → navigate 的 `run_skill` → `plan_navigate` 的 `drive` 段）。

---

## 2. 文件规模和 `skills.py` 内部分块

行数只给量级（会漂移，精确数用 `wc -l`）：

| 文件 | 行数（`90a2a31`） | 本分支相对 main |
|---|---|---|
| `skills.py` | 约 2000（job 在 `skill_jobs/` 约 1300 行，计划在 `skill_plans/` 约 1000 行） | +727 / −1450 |
| `motion.py` | 约 2000 | +1252 / −150 |
| `rig.py` | 约 1400 | +859 / −192 |
| `policies/*.py` | 约 5400（22 个文件） | 19 个文件改过 |
| `base_planner.py` | 约 500 | 新增 |

`skills.py` 里其实混着 7 块互不相关的内容：

行号区间对应 `90a2a31`，会漂移，按函数名找：

| 行（90a2a31） | 块 | 主要函数 |
|---|---|---|
| 55–496 | 搬运目标、导航、收臂 | `_carry_goals`、`_carry_goal_set`、`_carry_floor`、`check_held`、`held_vertical_move`、`navigate`（→ `run_skill`）、`relocate` / `straight_base_move`（→ `drive` 段 + `run.execute`）、`_base_plan`、`fold_where_possible`、`_fold_left`（搬运判据和 `carry_posture` 在 `skill_jobs/carry.py`）|
| 498–796 | 开关门（铰链 / 抽屉）| `open_articulated`、`close_articulated`（转到 `run_skill`；微波炉——close 还有没把手的部件——转 `_move_with_retry`）、`_move_articulated`、`_ride`、`_ride_check`（只剩微波炉用） |
| 797–910 | 扁平物体和支撑面的几何工具 | `_open_edges`、`_free_beyond`、`_overlaps_objects`、`_half_along`、`_edge_coord` |
| 911–1110 | pick | `pick`、`_pick_pinch`、`_pick_pinch_core`（现在只是转到 `run_skill`，pick 的 job 在 `skill_jobs/pick.py`）、`_grasp_approach` / `pick_approach`、`_pinch_candidates`、`_pads_clear_of`、`contact_obstacles`、`edge_held`（`push` 11-12 删了：`skill_jobs/slide.py` 的 `push_object`） |
| 1111–1296 | 微波炉腔体放取 | `insert_microwave_cavity`、`release_…`、`withdraw_…`、`place_microwave` |
| 1297–1762 | place | `place`（分派：托盘 / 台面转 `_set_down` → `run_skill`，job 在 `skill_jobs/place.py`；托盘以外的容器转 `drop_into`）、`park_over`、`free_spots`、`place_on`、`place_flat`（183 行）|
| 1763–1992 | 微波炉按钮和电动门 | `approach_microwave_button`、`press_…`、`open_microwave_door`、`_set_microwave_hinge` |

---

## 3. 一段运动在 `rig.py` 里怎么走

技能层只调这几个入口：

| 入口 | 用途 |
|---|---|
| `move_to(p, R, allow=, approach=, q_hint=)` | 手（TCP）到一个位姿。最主要的入口 |
| `run.run(act, plan, rebuild, hooks, clear=)` | 运动分层上的技能（`run_skill`：navigate / pick / place / open / close / push）和 `carry_posture`：按计划逐段执行（复核、重做、`follow` / `grip` / `wait` / `drive_base` / `swing` / `ride`、监视声明），只经过 `Actuator`；手臂跟完一段 TCP 离指令超过 `TARGET_TOL` 就失败；异常带 `clearing` 时先跑失败出口 `clear`（`plan_clear`）。技能自己的步骤挂 hooks；`relocate`、`straight_base_move` 用它的 `execute` 跑一段 `drive` |
| `move_to_any(goals, …)` | 先批量求 IK、挑代价最小的目标，再交给 `move_to`。已没有调用方（搬运姿态 11-08 起不用它了），只剩 `tests/test_motion_entry.py` |
| `leave(u, label, allow)` | 沿方向 u 离开接触，**没有终点**：碰撞模型判断不再接触就停（最多 `LEAVE_MAX`）。已没有调用方，只剩 `tests/test_approach.py`（pick 抓空后的离开现在是失败出口 `plan_clear`）|
| `joint_path(q)` / `joint_path_via` + `follow` | 关节空间运动 |
| `tuck()` / `swing()` | 收臂；双臂一起在关节空间移动 |
| `drive_base(path, allow=)` | 底盘沿路径走 |
| `move_left_to` / `left_follow` / `follow_both` | 左臂、双臂 |

`move_to` 内部按 `allow` 和 `approach` 分三条路：

```
move_to
 ├─ 有 approach，并且 allow 是 to_contact 或 checked
 │     → _approach：先规划自由段（_approach_path，最后 L 长度走直线），
 │       再走一段不查碰撞的接触段（长度 = _exit_length 测出的仍在接触的那段）
 ├─ allow 是 from_contact（LEAVE_CONTACT、lifting）
 │     → _leave_contact：直线离开，到不再接触为止，剩下的部分改用 FREE_ELSE_STRAIGHT 重新 move_to
 └─ 其他
       → _motion_path(plan = _move_path, straight = _straight_move)
            allow 不查碰撞 → 直接走直线
            allow 查碰撞   → _move_path：直线可行就走直线，否则 Motion.plan_to
                 规划失败：allow.fallback → 直线 + 记 clearance_fallback
                           否则         → SkillFailure
```

`Allow` 的几种取值（`clearance.py`）：

| 名字 | 查碰撞 | 规划失败时 | 用在哪 |
|---|---|---|---|
| `FREE`（`move_to` 的默认值）| 查整个机器人 | SkillFailure | 不允许退路的自由段 |
| `FREE_ELSE_STRAIGHT` | 查 | 直线 + `clearance_fallback` | 大多数自由段（`approach` 前那一段默认也是它）|
| `into_contact(touch, held_on)` | 自由段查，接触段不查 | — | wipe 按压（`approach=`）|
| `LEAVE_CONTACT` / `lifting(name)` | 不查，按碰撞模型判断何时结束 | — | 抓完、放完之后离开 |
| `LEGACY` | **不查** | — | 旧的写死路径，还没迁移（第 4 节）|
| `BASE_DRIVE`（`drive_base` 的默认值）| 底盘走的时候不查手臂 | — | 没传 `allow=FREE` 的 `drive_base` |

碰撞模型里的开关（`kin.coll_kw`、`_fingers_checked`、`Motion.scope` 里的目标豁免、`hand_open`、手持物体的碰撞球）都在 `rig._planning → Motion.scope` 里生效。旧入口上技能层设置的是 `rig.kin.coll_kw` 和 `_fingers_checked`（`skills.fingers_checked`）这个 context，停车点检查函数里另有 `Motion.part_at` / `empty_hand` / `hand_open`；运动分层上由 `primitives.query(kin, state, spec)` → `Motion.query` 按 `State` / `Spec` 设。

---

## 4. 主要技能的调用链

### 共同的外壳：`motion_skills.run_skill(rig, skill, args)`

```
run_skill
  state = observe(rig)
  job = skill.job(rig, args, state, skill)          skill_jobs/<技能>.py；skill.build = catalog 的 template；
                                                    catalog 的 park 说要不要选停车点
  job.problem + catalog 的 travel / arrive 姿态（motion_skills.posture，problem.hand 那只手）
     → park_search.find_park({side: ArmKin}, world, problem, observe(rig), log, base=RigBase(rig))
     找不到 → job.no_park(diag)
     job.found(found)（日志、字幕；开车之前）
     不在停车点 → run_skill(SKILLS["navigate"], {pose, **job.travel})
     2 cm / 2° 以内不开车、又不是正好在那 → 在现在的位置 problem.build 重做（做不出来就开过去）
  clear = plan_clear（计划用的那只手）               失败出口（skill_plans/_common.py）
  plan, build, hooks = job.ready(found)             开到以后：重新测量、要重做就重做（第 2.3 步删）
  run.run(rig, plan, build, hooks, clear=clear)     job.failed 可以换掉抛出的异常（pick：Dropped → SkillFailure）
     每段：holds 复核 → before → execute → after → 手臂跟的段停在离指令超过 TARGET_TOL 处（follow 返回的偏差）就失败
     异常带 clearing（hook 抛的、段 info["clear"] 的）→ run_clear 先跑 clear 的计划（张手、竖直退出接触），再抛
  job.done()                                        结果判断；它抛异常时也先 run_clear
```

### pick（`skills.pick → _pick_pinch → _pick_pinch_core → run_skill(SKILLS["pick"])`）

```
skill_jobs/pick.py  pick_job
  候选抓取（annotation）；门后的（annotations.behind_door：inside_ 支撑面上、腔体或冰箱柜体里）朝开口排序，prefer = door_access.front_of（门自由边前）
  _pick_problem：所有候选 = 一个目标集合 → Problem(goals, build, PICK_RELAY, near, prefer)
     build = skill.build（plan_pick）(state_at_park, 候选(物体框里), _carry_goal_set)：pick_arrive（锚点）→ pick_open（State 手张开）
             → pick_reach（free_leg）→ pick_grasp（straight）→ pick_close（holding）→ pick_held（锚点）
             → pick_lift（contact_extent off_support）→ carry_in（free_leg PoseSet，持物碰撞球放大 HELD_POSE_MARGIN）
             接触位姿段的容差 PICK_TOL（1 mm）
  ready：记 pick_target、note_grasp（抓取 = 物体现在的位姿 × T_obj_tcp）；_pick_ready 交出找到的计划，
         rebuild = plan_pick(start=段名, prior=run 手上的计划：还成立的段原样复用)
     hooks：pick_reach / pick_grasp 盯物体（_watching）；pick_grasp 后实测 TCP 对指令 TCP 的到位检查（被挡 → 失败出口竖直离开）；
            pick_close 后判断夹没夹住、登记 rig.held、记 held_offset；carry_in 后 check_held
  done：_pick_judged（拿住了没有）
  （微波炉腔体里取物不走这条：合约路由到 PickFromCavity，policy_048，旧实现）
```

### place（`skills.place`，台面 / 浅容器 / 深容器 / 层板）

```
place
  "in:" 非托盘容器 → drop_into；微波炉 → place_microwave（柜门后层板、冰箱层板走下面的 _set_down）
  edge 持法（书） → place_flat（旧的写死路径，见第 5 节）
  其他（台面 / 托盘底板） → _set_down → run_skill(SKILLS["place"])
skill_jobs/place.py  place_job
  carry_posture(min_bottom_z)：搬运判据满足就不动，不满足就规划到搬运目标集合，做不出来失败；
                               min_bottom_z 是"能抬就抬"（skill_jobs/carry.py）
  目标集合：空位 × 持法（吊着 / 摆正） × 手腕转角 → Problem
     build = skill.build（plan_place）(state_at_park, 物体的放置位姿, prior, obj)：place_arrive（锚点）
             → place_reach（q_p 由 decide_ik 定 → set_down_length → free_leg，持物先关节规划）→ place_down（straight）
             → place_release（released，手张开，手指可碰 obj）→ place_landed（锚点）→ place_pull_out（straight，Spec.touch obj）
             → tuck（free_leg JointSet{收起, 下垂}，每次重选、不复用）→ place_settle（wait）
             接触位姿段的容差 PLACE_TOL（5 mm）；TCP 放下位姿 = 物体位姿 × State 握法⁻¹（握法按实测关节角量）
  travel = {min_bottom_z, raise_load: False}：开过去时 navigate 按同一套判据复核，不再试抬高
  ready：_place_ready 交出找到的计划，rebuild = plan_place(start=段名, prior=run 手上的计划：还成立的段原样复用)
     hooks：place_down 后实测 TCP 对指令 TCP 的到位检查、check_held；place_release 后 rig.held = None；
            place_pull_out 前手指在物体里就记 place_pull_out_touching
  done：_place_result（在支撑面上 / 托盘里、离目标点多远）
```

### open / close（`skills.open_articulated` → `run_skill(SKILLS["open"])`，`close_articulated` → `run_skill(SKILLS["close"])`；微波炉走下面的旧路径；close 见 `close.md`）

```
open_articulated：已在目标（RIDE_DONE_REV / RIDE_DONE_PRIS 以内）就不动
skill_jobs/door.py  open_job
  手：door_hand（空着的手，两只都空用右手）；另一只手拿着东西时身体不动（motion_state.body_locked）
  goals：每种握法一个（_ways：侧钩 0 / 10 / 20°、两端、正面捏），握法在部件坐标系（door_grips）
  plan_door(kin, state, grip, rests, base=RigBase)（skill_plans/door.py）
     door_arrive 锚点 → 张手 → door_reach（_reach）→ door_grasp（straight，touch 部件）→ 合爪（Held part）
     → door_held 锚点 → door_ride（scripted，Script(hinge/slider)，carry="base"）→ door_moved 锚点
     → 松开 → door_leave（straight，沿伸入方向反着退 DOOR_LEAVE 17 cm）→ tuck → door_settle
  run.run：door_ride 由 execute 交给 Rig.ride(part, ride_base, …)
     hooks：door_grasp 前 caption；合爪后判握住（不住 → clearing 张开退出），登记 rig._handle_grasp；松开后清登记
  done：开度（铰链 0.10 rad、抽屉 60%）
skill_jobs/door.py  close_job：每只空着的手 × {推门板（plan_push，铰链门），握把手骑着关（plan_door，右手）} 一次停车点搜索
```

### push（`skill_jobs/slide.py` 的 `push_object` → `run_skill(SKILLS["push"])`）

```
调用方：Push / PushFromBehind / TopDrag（manipulation）、PullTowardBase / SeparateFromNeighbour / CenterOnSupport
        （contact）、SlideToEdge（embedded）、SweepTogether（extra）
push_object(rig, name, s, ways, label, modes)   任务层：一段段推，每段从上一段留下的位置起、推到手臂够不着为止；
                                                第一段的停车点搜索把所有方向都当目标，之后沿走了的那个方向；
                                                离要的距离 PUSH_DONE_TOL 以内或推够 enough 就停；
                                                一段实测推得比 min(1 cm, 计划这段的 0.3)（PUSH_MOVED_MIN）少就失败
skill_jobs/slide.py  slide_job（一段；右手空着）
  goals：方向 × 做法（push：合拢的手指在背面后 SLIDE_GAP、离支撑面 SLIDE_PAD_GAP；drag：压在顶上、离前沿 DRAG_RIM）
         × 手指转 4 个朝向（slide_ways），推点在物体坐标系；Problem.tiers：按 modes 的顺序，一种做法的目标
         全排在下一种之前（默认 push 先于 drag）；relay 是推的终点，没有停车点够到终点时按能推多远排（relay_from）
  plan_slide(kin, state, push, rests)（skill_plans/contact.py）
     slide_arrive 锚点 → 合爪 → slide_reach（_reach）→ slide_down（straight）→ slide_in（straight 到推点；drag 没有）
     → slide_push（scripted，Script(pushed)，carry="arm"，reach=True：走到手臂 IK 到头为止）→ slide_moved 锚点
     → slide_leave（contact_extent near_world，向上并离开被推的面）→ tuck → 张手（SLIDE_OPEN）
     接触位姿段的容差 SLIDE_TOL
  run.run：slide_push 由 execute 按 follow 执行；hooks：slide_push 前 caption
  done：（走了 dirs 里哪个方向，沿它实测推了多远，计划预测的）
```

### navigate（`skills.navigate → run_skill(SKILLS["navigate"])`）

```
skill_jobs/navigate.py  navigate_job（不选停车点）
  plan_navigate(kin, left_kin, state, pose, RigBase, carry)（skill_plans/navigate.py）
     arm：空手 → 已在收起就省掉，否则 free_leg(JointSet{收起, 下垂})，做不出来就省掉（日志 tuck_blocked）
          拿着东西 → 搬运判据（skill_jobs/carry.py 的 _carry）满足就不动；不满足 → free_leg(搬运目标集合)，
          做不出来 navigate 失败；只是够不着 min_bottom_z 的高度 → 原样带着走（日志 carry_posture）
     left_fold：左手空着又不在收起位 → free_leg(左臂收起)，做不出来就省掉
     drive：primitives.drive(RigBase, …, travel_chain)：RigBase.plan → skills._base_steps → posture_sets → base_planner.plan
     arrive：锚点
  run.run：drive 段由 execute 交给 drive_base(path, allow=FREE) / swing
     hooks：carry_in 后 check_held；drive 前记 carry_height、check_held(carry_up)；drive 后 check_held(carry)
```

`_goto_park(rig, park)` 就是"不在停车点就 `navigate(park[:3])`"，还给没迁移的技能用；pick / place / open / close / push 由 `run_skill` 自己开过去。

### 微波炉的门（旧路径：`open_articulated` / `close_articulated` 遇到微波炉；close 还有没把手的部件）

```
_move_with_retry → _move_with_retry_impl → _move_articulated（没把手的部件在开头就 SkillFailure）
  find_park(_handle_targets, 随门转动)  →  _goto_park
  move_to 握把手（默认 FREE）→ grip → _ride（底盘跟着门走的闭环）
  move_to(LEAVE_CONTACT) → move_to(FREE_ELSE_STRAIGHT)
```

---

## 5. 迁移状态：还没改成"中继位姿 + 规划"的地方

判断依据：代码里显式写了 `allow=LEGACY` 的运动（不查碰撞的写死路径），以及策略层自己拼的路径点。下面按文件列出。

### `skills.py`（8 处 LEGACY，11-12 删了 `push` 以后）

| 函数 | LEGACY 的段 | 计划里归哪 |
|---|---|---|
| `place_flat` | 4 段（放书的边沿路径）| 6.2 后半 |
| `insert_microwave_cavity` | 插入那一段 | 6.4 |
| `approach_microwave_button` / `press_…` / `retract_…` | 按按钮 | 6.5 |

没有 LEGACY 的（按上面的判据算"已迁移"）：`_pick_pinch_core`、`place`（台面、托盘底板：`_set_down`）、`carry_posture`（原 `_carry_pose`）、`navigate` / `relocate`、`open_articulated` / `close_articulated`（微波炉除外）、`push_object`（push）——这几个已经在新分层上（停车点搜索做整份计划、执行照着走，`MOTION_ARCHITECTURE.md`）——，以及 `drop_into`（托盘以外的容器：`park_over` → `planner.find_park_set`、`_goto_park`、`rig.move_to`、`rig.tuck`）、`_move_articulated` 的抓握和离开（只剩微波炉）、`withdraw_microwave_cavity`、`held_vertical_move`。后四个**不在新分层上**，还走 `rig.move_to` 这类旧入口；`held_vertical_move` 还显式带 `allow=FREE_ELSE_STRAIGHT`（规划不出来就走不查碰撞的直线），按 `MOTION_ARCHITECTURE.md` 第 1 节第 3 条它仍是待迁的。

### `policies/` 里自己动手臂的策略

下面这些 `execute` 直接调 `rig.move_to` / `follow` / `drive_base`，物理逻辑写在策略层，**不在 `skills.py` 里**：

| 文件 | 策略 | LEGACY 数 | 备注 |
|---|---|---|---|
| `tooluse.py` | Pour、Stir、Wipe | 3 | Wipe 的下压已改（`into_contact` + `approach`），擦完抬起 `wipe_lift` 仍是 LEGACY，擦的过程是 `drive_base` 不查手臂；Stir 的 2 处是 LEGACY（`stir_dip`、绕圈的 `stir_circle`）；Pour 没有 LEGACY，但是自己拼的路径点 |
| `orientation.py` | UprightObject（`_turn_in_air`、`_hang_upright`、`_set_down_upright`）| 7 | 全部旧的 |
| `hand.py` | DropInto、FlipFlat、LeftSteady、Regrasp、ReleaseInPlace、RotateHeld | 5 | DropInto 已改（`park_over`）；FlipFlat 占 4 处 LEGACY，LeftSteady 1 处 |
| `extra.py` | Touch、Knock、Hover、Shake、Wave | 5 | Hover 已改（`park_over`）；Knock（3 处）、Touch（2 处）是 LEGACY |
| `contact.py` | `_contact_sweep`（TipOver、Roll）| 3 | |
| `appliance_generic.py` | PressButton | 3 | |
| `embedded.py` | GraspArticulatedHandle、PickFromCavity、PrepareFloorReach | 1 | GraspArticulatedHandle（policy_046）已退役：没有合约路径到它，类还在 |
| `bimanual.py` | Handover、双手抬 / 搬、OpenDoorWhileLeftHolds | 0 | 用 `follow_both`、`move_left_to`；`drive_base` 不查手臂。OpenDoorWhileLeftHolds（policy_060）已退役：没有合约路径到它，类还在 |
| `mobile.py` | Pick / Place / ReachWhileMoving | 0 | 自己拼底盘和手臂的轨迹，`drive_base` 不查手臂。ReachWhileMoving（policy_051）已退役：没有合约路径到它，类还在 |
| `handle_grasp.py` | PickCupHandle | 0 | 三段 `move_to`，最后一段 `lifting` |
| `perceive.py`、`primitives.py`、`posture.py`、`base_motion.py`、`navigation.py` | — | 0 | 主要是转发或单段运动 |

---

## 6. 结构上的问题（供讨论，暂不动）

1. **技能逻辑分在两层。** 上表约一半的策略在 `policies/` 里自己写运动，所以"底层 policy 的代码"并不都在 `skills.py`。改一个公共机制（比如 fallback 的规则）时，要连同这些策略一起查。
2. **策略层和 `skill_jobs/` 在用 `skills.py` 的私有函数**（`skill_jobs/pick.py` 7 个，如 `_carry_goal_set`、`_grasp_approach`、`_pinch_candidates`；`place.py` 用 `_lowest_z`；`slide.py` 用 `_half_along`、`_pads_clear_of`、`_perp`、`_surface_under`、`_yaw`；`carry.py` 用 `_carry_floor`、`_carry_goal_set`；`base.py` 用 `_base_steps`、`_reachable`）。策略层用的：`_goto_park`（7 个文件）、`_travel_q`、`_pick_pinch`、`_lowest_z`、`_overlaps_objects`、`_half_along`、`_edge_coord`、`_open_edges`、`_yaw`、`_handle_targets`、`_set_microwave_hinge`、`_press_microwave_door_control`。这些函数实际上已经是公共接口，改签名之前要先 grep `policies/` 和 `skill_jobs/`。
3. **`skills.py` 混着 7 块**（第 2 节表）。按块拆成文件不会改行为，但会让 `git blame` 和大家记住的位置失效，要不要拆另外决定。
4. **`planner.py` 和 `base_planner.py` 名字太像**，见第 1 节末尾的说明。

---

## 7. 每次改动前后的检查清单

改之前先说清楚：

- 改哪个技能 / 策略，**在哪一层**：
  - skills 只负责中继位姿、接触方向、停车点目标；
  - rig 决定怎么走、何时 fallback；
  - motion 负责碰撞模型。
- 会不会改到第 3 节的公共机制。如果会，第 5 节表里的所有调用方都受影响。
- 预期的物理行为变化，以及要重跑哪些 episode。

改之后：

- `grep -rn '<改过的函数名>' zeno_skills/`：确认 policies 里的调用方也跟着改了。
- 在同一个提交里更新这篇的第 4、5 节和 `COLLISION_PLAN.md`。
