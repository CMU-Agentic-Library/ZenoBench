# 底层策略的代码地图（`a588fd0`，2026-11-05）

这篇讲**代码怎么组织**：一个技能调用从哪里进来、经过哪几层、每一段运动在哪个函数里决定查不查碰撞，以及哪些还是旧的写死路径。物理上每一步做什么见同目录的各篇（[README](README.md)），为什么这样改、计划做什么见 [`../COLLISION_PLAN.md`](../COLLISION_PLAN.md)。

行号对应 `a588fd0`，之后会漂移，**以函数名为准**。每次改动后，凡是改到下面某张表的内容，同一个提交里一起更新这篇。

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
policies/*.py     PolicySuite → XxxPolicy.execute     115 个原子策略（catalog.json），合约用到其中 106 个
  │        │
  │        └───────────────┐  约一半的策略直接调 rig，不经过 skills（见第 5 节）
  ▼                        │
skills.py         技能本体：pick / place / navigate / 开关门 / push / 微波炉…
  │                        │  决定"中继位姿是什么、停车点在哪、接触段往哪个方向走"
  ▼                        ▼
rig.py            Rig：机器人运动的唯一入口 move_to / move_to_any / leave / joint_path /
  │                    tuck / swing / drive_base / grip；决定每一段是规划、直线还是 fallback
  ▼
motion.py         Motion：cuRobo 封装（IK、轨迹规划、碰撞世界、目标豁免、手持物体的碰撞球）
kinematics.py     ArmKin：正运动学 + 把逆运动学和碰撞查询转给 motion
scene_geometry.py PhysX 碰撞体 → cuRobo 障碍物
```

旁路模块：

| 模块 | 谁调它 | 做什么 |
|---|---|---|
| `planner.py` | skills、policies | **手臂视角的停车点搜索** `find_park` / `find_park_set`：在哪个底盘位姿，手臂能无碰撞地走完给定的一串目标位姿。另有旧的网格路径 `plan_path` |
| `base_planner.py` | `skills._base_plan` | **底盘路径规划**：在 (x, y, yaw) 网格上做 A*，同时考虑手臂姿态链（收臂 → 下垂 → 收臂）|
| `clearance.py` | rig、skills、policies | `Allow`：一段运动允许碰什么（第 3 节）；`rig.clear`：接触监视器、fallback 计数 |
| `collision.py` | planner | 标注包围盒，只给底盘的占地检查和网格用；手臂不用 |
| `sticky.py` | skill_runtime | sticky hands（焊接、snap），只是执行辅助 |
| `physx_contacts.py` | clearance | 读 PhysX 的真实接触 |
| `annotations.py` / `predicates.py` / `scene_geometry.py` | 各层 | 场景和资产的真值、谓词、碰撞体 |

**名字容易混的两个**：`planner.find_park` 回答"停在哪"，`base_planner.plan` 回答"怎么开过去"。`skills.navigate` 只用后者；pick、place 这类先用前者选停车点，再用后者开过去（`_goto_park → navigate → relocate`）。

---

## 2. 文件规模和 `skills.py` 内部分块

| 文件 | 行数 | 本分支相对 main |
|---|---|---|
| `skills.py` | 2420 | 改动约 1600 行 |
| `motion.py` | 1476 | +779 |
| `rig.py` | 1140 | +755 |
| `policies/*.py` | 约 3500 | 共 19 个文件都改过 |
| `base_planner.py` | 497 | 新增 |

`skills.py` 里其实混着 7 块互不相关的内容：

| 行 | 块 | 主要函数 |
|---|---|---|
| 64–480 | 搬运姿态、导航、收臂 | `_carry_pose`、`check_held`、`held_vertical_move`、`navigate`、`relocate`、`_base_plan`、`straight_base_move`、`fold_where_possible`、`_fold_left` |
| 482–862 | 开关门（铰链 / 抽屉）| `_move_articulated`（137 行）、`_ride`、`_ride_check`、`open_articulated`、`close_articulated`、`_push_close` |
| 865–1035 | 扁平物体和支撑面的几何工具 | `_open_edges`、`_free_beyond`、`_overlaps_objects`、`_grasp_targets`、`_pads_clear_of` |
| 1040–1400 | pick 和 push | `pick`、`_pick_pinch`、`_pick_pinch_core`（169 行）、`contact_obstacles`、`push`、`edge_held` |
| 1417–1600 | 微波炉腔体放取 | `insert_microwave_cavity`、`release_…`、`withdraw_…`、`place_microwave` |
| 1609–2190 | place | `place`（268 行）、`park_over`、`free_spots`、`place_on`、`place_flat`（183 行）|
| 2191–2420 | 微波炉按钮和电动门 | `approach_microwave_button`、`press_…`、`open_microwave_door`、`_set_microwave_hinge` |

---

## 3. 一段运动在 `rig.py` 里怎么走

技能层只调这几个入口：

| 入口 | 用途 |
|---|---|
| `move_to(p, R, allow=, approach=, q_hint=)` | 手（TCP）到一个位姿。最主要的入口 |
| `move_to_any(goals, …)` | 先批量求 IK、挑代价最小的目标，再交给 `move_to`。搬运姿态用它 |
| `leave(u, label, allow)` | 沿方向 u 离开接触，**没有终点**：碰撞模型判断不再接触就停（最多 `LEAVE_MAX`）|
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
| `into_contact(touch, held_on)` | 自由段查，接触段不查 | — | place 下放（`approach=`）|
| `LEAVE_CONTACT` / `lifting(name)` | 不查，按碰撞模型判断何时结束 | — | 抓完、放完之后离开 |
| `LEGACY` | **不查** | — | 旧的写死路径，还没迁移（第 4 节）|
| `BASE_DRIVE`（`drive_base` 的默认值）| 底盘走的时候不查手臂 | — | 没传 `allow=FREE` 的 `drive_base` |

碰撞模型里的开关（`kin.coll_kw`、`_fingers_checked`、`Motion.scope` 里的目标豁免、`hand_open`、手持物体的碰撞球）都在 `rig._planning → Motion.scope` 里生效。技能层设置的只有 `rig.kin.coll_kw` 和 `_fingers_checked` / `_hand_opened` 这两个 context。

---

## 4. 主要技能的调用链

### pick（`skills.pick → _pick_pinch → _pick_pinch_core`）

```
_pick_pinch_core
  候选抓取（annotation） → planner.find_park(_grasp_targets(g))  选停车点和抓取
  relocate / _goto_park → navigate → relocate → base_planner.plan + drive_base(FREE) + swing
  grip(pre_open)
  with _fingers_checked, _watching:  move_to(g.p, g.R, allow=FREE, approach=_grasp_approach(g))
                                     → rig._approach（自由段 + 接触段）
  grip(0)  → 没抓到：leave(up, LEAVE_CONTACT)，SkillFailure
  leave(up, LEAVE_CONTACT, lifts_off=True)
  (微波炉里) move_to 往外撤
  _carry_pose → move_to_any(_carry_goals, FREE_ELSE_STRAIGHT)
```

### place（`skills.place`，台面 / 浅容器 / 深容器 / 层板）

```
place
  edge 持法（书）且放到台面 → place_flat（旧的写死路径，见第 5 节）
  微波炉 → place_microwave
  _carry_pose
  候选位置 legs_at / free_spots → planner.find_park_set  选停车点和放置点
  _goto_park(min_bottom_z) → navigate
  "in:" 容器：move_to(drop pose, allow=free)
  其他：move_to(下放位姿, allow=into_contact(held_on=支撑面), approach=…)
  held_vertical_move（补最后几毫米）
  grip(pre_open) → leave(-u, LEAVE_CONTACT) → tuck
```

### navigate（`skills.navigate`）

```
navigate
  空手：rig.tuck()；拿着东西：_carry_pose + check_held
  _fold_left
  relocate(pose, travel_postures)
     _base_plan → posture_sets → base_planner.plan（A*，姿态链）
     每一步：drive_base(path, allow=FREE) 或 swing(姿态切换)
```

`_goto_park(rig, park)` 就是 `navigate(park[:3], arrive=park 的关节解)`。几乎所有"先停车再动手"的流程都经过它。

### 开关门（`open_articulated` / `close_articulated`）

```
_move_with_retry → _move_with_retry_impl → _move_articulated
  find_park(_handle_targets, 随门转动)  →  _goto_park
  move_to 握把手（默认 FREE）→ grip → _ride（底盘跟着门走的闭环）
  move_to(LEAVE_CONTACT) → move_to(FREE_ELSE_STRAIGHT)
close_articulated：铰链门改为推外表面 → _push_close（contact 段是 LEGACY）
```

---

## 5. 迁移状态：还没改成"中继位姿 + 规划"的地方

判断依据：代码里显式写了 `allow=LEGACY` 的运动（不查碰撞的写死路径），以及策略层自己拼的路径点。下面按文件列出。

### `skills.py`（13 处 LEGACY）

| 函数 | LEGACY 的段 | 计划里归哪 |
|---|---|---|
| `push` | 接触、推、退，3 段 | 6.5 接触动作 |
| `_push_close` | 推门的接触段 | 6.5 |
| `place_flat` | 4 段（放书的边沿路径）| 6.2 / 6.4 |
| `insert_microwave_cavity` | 插入那一段 | 6.4 |
| `approach_microwave_button` / `press_…` / `retract_…` | 按按钮 | 6.5 |

已经迁移的：`_pick_pinch_core`、`place`（台面 / 容器）、`_carry_pose`、`navigate` / `relocate`、`held_vertical_move`、`_move_articulated` 的抓握和离开、`withdraw_microwave_cavity`。

### `policies/` 里自己动手臂的策略

下面这些 `execute` 直接调 `rig.move_to` / `follow` / `drive_base`，物理逻辑写在策略层，**不在 `skills.py` 里**：

| 文件 | 策略 | LEGACY 数 | 备注 |
|---|---|---|---|
| `tooluse.py` | Pour、Stir、Wipe | 4 | Wipe 的下压已改（`into_contact` + `approach`），擦完抬起 `wipe_lift` 仍是 LEGACY，擦的过程是 `drive_base` 不查手臂；Stir 的 3 段是 LEGACY；Pour 没有 LEGACY，但是自己拼的路径点 |
| `orientation.py` | UprightObject（`_turn_in_air`、`_hang_upright`、`_set_down_upright`）| 8 | 全部旧的 |
| `hand.py` | DropInto、FlipFlat、LeftSteady、Regrasp、ReleaseInPlace、RotateHeld | 6 | DropInto 已改（`park_over`）；FlipFlat 占 4 处 LEGACY，LeftSteady 1 处 |
| `extra.py` | Touch、Knock、Hover、Shake、Wave | 6 | Hover 已改（`park_over`）；Knock、Touch 是 LEGACY |
| `contact.py` | `_contact_sweep`（TipOver、Roll）| 3 | |
| `appliance_generic.py` | PressButton | 3 | |
| `embedded.py` | GraspArticulatedHandle、PickFromCavity、PrepareFloorReach | 1 | |
| `bimanual.py` | Handover、双手抬 / 搬、OpenDoorWhileLeftHolds | 0 | 用 `follow_both`、`move_left_to`；`drive_base` 不查手臂 |
| `mobile.py` | Pick / Place / ReachWhileMoving | 0 | 自己拼底盘和手臂的轨迹，`drive_base` 不查手臂 |
| `handle_grasp.py` | PickCupHandle | 0 | 三段 `move_to`，最后一段 `lifting` |
| `perceive.py`、`primitives.py`、`posture.py`、`base_motion.py`、`navigation.py` | — | 0 | 主要是转发或单段运动 |

---

## 6. 结构上的问题（供讨论，暂不动）

1. **技能逻辑分在两层。** 上表约一半的策略在 `policies/` 里自己写运动，所以"底层 policy 的代码"并不都在 `skills.py`。改一个公共机制（比如 fallback 的规则）时，要连同这些策略一起查。
2. **策略层在用 `skills.py` 的私有函数**：`_goto_park`（6 个文件）、`_travel_q`、`_pick_pinch`、`_carry_pose`、`_lowest_z`、`_overlaps_objects`、`_half_along`、`_edge_coord`、`_open_edges`、`_yaw`、`_handle_targets`、`_set_microwave_hinge`、`_press_microwave_door_control`。这些函数实际上已经是公共接口，改签名之前要先 grep `policies/`。
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
