# 碰撞检查：现状盘点与统一方案（2026-10-31）

代码基线：`b0bbcdd`（fix-grip-criteria-push-crash-restore-xy）。行号以这个提交为准。

## 0. 为什么要做

10-31 三种子 `sticky/gt` 全量测试里，P07 和 P12 的失败都是机器人撞到家具，但每次的原因都不一样：

| 现象 | 直接原因 | 落在哪一层 |
|---|---|---|
| P07 s10：右手放积木时，左手压进台面 1 cm，躯干倾不下去，报 "hand blocked above support" | `place_above` 放到台面上时用 `collision=False` | skill 自己关掉了检查 |
| P07 s11/s12：开去扶杯 park 的路上，右臂一路刮着岛台，腰被顶到限位，左手扶杯时夹空 | `drive_base` 不检查手臂，`plan_path` 只避让底盘方柱 | 底盘移动根本不查手臂 |
| P12 s11/s12：开去开门 park 的路上，收起的手把柜门碰开到 -0.36 rad | 同上 | 同上 |

第二、三行已经由 `b0bbcdd` 缓解：收起姿态改成下垂，手臂收在底盘方柱以内。第一行，以及下面列出的其他漏洞都还在。

这几处漏洞的共同点是：每个 skill 自己决定检查什么、关掉什么，而"检查什么"散在 6 种不同的机制里，其中好几种是会漏到后续 skill 的全局状态。

## 1. 现在有哪几层检查

| 层 | 代码 | 检查什么 | 对象 |
|---|---|---|---|
| A. 底盘占地 | `collision.py` `WorldModel.footprint_clear`（:94） | 0.52 m 方柱，只在 z=0.15 m 和 0.6 m 两个高度取点，对象是标注里的静态盒子、活动部件，以及落地的散物（`base_only`） | 底盘 |
| B. 底盘路径 | `planner.py` `plan_path`（:292），网格 A*，`R_BASE = 0.28` | 在 A 的基础上加 `margin`；起点和终点附近 0.4 m 内不检查（`relax`，:299） | 底盘 |
| C. 手臂 cuRobo | `motion.py` `Motion._query`（:701）及 `ik` / `cart_path` / `free` / `segment_free` / `plan` / `plan_to` / `clearance` / `penetration` | 机器人全部碰撞球，对象是场景中所有 PhysX collider（含散物、活动部件），2.5 m 以外的剔除（`CULL`） | 一只手臂加躯干，另一只手臂锁住 |
| D. 选 park | `planner.py` `find_park`（:123） | 依次检查：底盘占地 → 收起姿态（`travel_q`）在 park 处是否自由（:198）→ IK → 从收起姿态展开 → `ride` / `check` 回调 | 只看 park 这一个点 |
| E. 物理结果 | 各 skill | TCP 误差（`hand blocked`、`TCP missed`）、`check_held` 滑移、关节角变化（开门前检测门被碰动）、`knock_contact` 的距离判断 | 事后判断，全部基于几何，项目里没有 PhysX 接触传感 |

真正检查碰撞的只有 C。A 和 B 只管底盘，D 只看终点，E 是出事之后才发现。

## 2. C 层的开关：现在有六种写法

### 2.1 `collision=` / `check=` 布尔开关（113 处）

`rig.move_to(..., collision=False)` 和 `rig.move_left_to(..., collision=False)` 会把 `kin.scene` 置为 `None`（`rig.py:327`、`:522`），等于对整台机器人关掉检查，而不只是手。

- 105 处 `collision=False`
- 6 处动态值：`collision=bool(container)`、`collision=coll`、`lab != 'contact'` 等
- 3 处 `joint_path(check=False)`

附录 A 按 skill 列出全部位置；生成清单的 AST 脚本在 `/data/zenobench/tuck_1031/audit.py`。

### 2.2 `kin.coll_kw`：挂在 ArmKin 上的全局状态（61 处写入）

`coll_kw` 有两个开关：
- `ignore_fingers`：关掉自己的两个手指。
- `hand_touches_part`：关掉手指、夹爪和腕部相机。

问题在于它是 `ArmKin` 的属性，写进去之后，所有后续查询都会受影响。

- 48 处直接赋一个预设值，只有 11 处保存并恢复原值。
- `skill_runtime` / `contract_runtime` 在 skill 之间不会重置它。
- 结果：
  - `skills.py` 里有 17 处把它设成 `ignore_fingers`（pick、place、push 等的入口），只有 `_clear_for_tuck` 那一处会恢复。
  - open / close（`skills.py` 中 `_move_articulated`、`_push_close`）结束时还停在 `hand_touches_part`。下一个没有自己设置 `coll_kw` 的 skill，会在"整只手都不算"的状态下规划，直到某个 skill 重新赋值为止。
- 类似的隐式状态还有两处：
  - `kin.set_base` 有 22 处直接调用：规划时移动 kin 的底盘，靠下一次 `sync_world` 复原。
  - `kin.lo` / `kin.hi` 有 18 处被临时改写（比如固定躯干），各自用 `try/finally` 恢复。

### 2.3 Motion 内部的自动豁免

| 规则 | 位置 | 说明 |
|---|---|---|
| 目标附近的物体不算障碍 | `_targets_allow`（:688），`TARGET_PAD = 0.03` | TCP 目标点落在某物体包围盒外扩 3 cm 以内时，这个物体对整台机器人都不算障碍，而不只是对手 |
| 手里拿着的东西不算障碍 | `sync`（:546 起） | 对拿着它的那只手不算；对另一只手，手离它 5 cm 以内时也不算（`HAND_AT_HELD`） |
| 另一只手的手指一律不查 | `_query`（:705–709） | 规划一只手臂时，另一只手的两个手指连杆每次都关掉 |
| 已经碰到场景的连杆不查 | `other_touching`（:566–589） | 另一只手臂中，同步时已经穿透场景的连杆会被排除。一旦碰上，就再也检查不到它 |
| 拿着的物体作为碰撞球 | `held_collision()` 上下文（`rig.py:373`）+ `_attach_held` | 只在 `_carry_pose` 和 posture 两处用到；物体还贴着支撑面时自动关掉 |

### 2.4 失败后的退路：各写各的

同一种"先查，查不过就不查"的逻辑，至少有 4 种写法：

- `move_to`（`rig.py:318`）：直线 → 加密直线 → 带约束的 cuRobo 规划 → 跳到 `q_hint`（摆动大于 1 rad 时强制检查）→ 全局 IK 加 `joint_path`。
- `_carry_pose`（`skills.py:83`）：`for coll in (True, False)`，带检查的不行就关掉检查重试。
- `rig.tuck`（`rig.py:547`）：几种直线后撤 → 直接收臂 → cuRobo 规划，自己的手指全程不算。
- `_clear_for_tuck`（`skills.py:189`）：唯一一处沿底盘位移采样、检查手臂的代码，但只在收不回手时才会用到。

### 2.5 不经过任何开关、天然不检查的运动

| 运动 | 位置 | 后果 |
|---|---|---|
| `rig.follow` / `follow_smooth` / `left_follow` 执行原始插值 | 例：`LeftArmFoldPolicy`（`base_motion.py:197`，tuck(hand=left)）直接插值，不检查 | 左臂收臂可能扫过家具 |
| `rig.drive_base` | 29 处调用，涉及 navigate、face、retreat、sidestep、`_back_off`、边走边放、wipe 的底盘行程、flip 的底盘推、handover 时开车、perceive 时转身 | 手臂和手里的物体都不检查。空手收起时已经由下垂姿态覆盖，拿着东西或手伸在外面时仍然不检查 |
| `_back_off`（`skills.py:174`） | 只查底盘占地 | 注释写着"避免转身时把拿着的东西扫进家具"，但实际只检查了底盘 |

### 2.6 死代码和失效的标志

- `WorldModel.temp_obstacles`（`collision.py:80`）是空操作，`place` 仍然把它当作临时障碍的保护在用（`skills.py` 放进容器的分支）。
- `world.active` 从来没有被赋值；`world.left_active` 有 8 处写入，但没有任何地方读取。

## 3. 问题归纳

1. **开关粒度不对。** skill 想说的是"这只手可以碰 X"，但能用的只有"整台机器人不检查"（2.1），或者"这只手碰什么都行"（`hand_touches_part`）。
2. **状态是隐式的，还会泄漏。** `coll_kw`、kin 的底盘位姿、关节限位、`world.right_q` / `left_q` 都靠调用方自己设、自己恢复，而 `coll_kw` 在 skill 之间根本没人恢复（2.2）。
3. **入口太多。** `move_to`、`move_left_to`、`joint_path`、`follow`、`left_follow`、`follow_both`、`drive_base` 七个入口各自检查或不检查，查不过之后的退路也各写各的（2.4）。
4. **底盘移动不检查手臂**（2.5）。
5. **事后发现不了。** 不管 P07 和 P12 是撞到台面还是碰开柜门，`result.json` 里都看不出来，要靠人看录像（1 的 E 层）。

## 4. 目标设计：独立的碰撞策略模块

新模块定名为 `zeno_skills/clearance.py`。

### 4.1 用声明代替开关：`Allow`

```python
@dataclass(frozen=True)
class Allow:
    """一次运动允许碰到什么；没列出来的，整台机器人都要检查。"""
    hand: str | None = None          # "right" / "left"：允许接触的那只手
    links: str = "fingers"           # "fingers" | "hand"（手指 + 夹爪 + 腕部相机）
    touch: tuple[str, ...] = ()      # 这只手可以碰的实体：物体、活动部件、支撑面
    held_on: tuple[str, ...] = ()    # 手里的物体可以碰的实体（落下时的支撑面、容器）
    reason: str = ""                 # 允许任何接触时必须写明理由

FREE = Allow()                       # 默认：什么都不能碰
def grasp(hand, obj):        ...     # 最后夹取那一下：手指可以碰 obj
def handle(hand, part):      ...     # 握把手、推门：整只手可以碰这个活动部件
def press(hand, part):       ...     # 按按钮、敲门
def sweep(hand, support, obj=None): ...  # push / wipe / stir：手可以碰支撑面和被推的物体
def set_down(hand, support): ...     # place 落下、放入：手里的物体可以碰支撑面
def unchecked(reason):       ...     # 逃生口，替代现在的 collision=False
```

**语义要点：** "这只手可以碰 X"是成对的约束，cuRobo 一次查询表达不出来：
- 关掉 X，整台机器人都能碰 X。
- 关掉手指，手能碰任何东西。

所以接触类的检查要拆成两次查询，两次都通过才算通过：
1. 关掉允许接触的那几个手部连杆，X 照常算障碍：检查手臂、躯干和另一只手，包括它们不能碰 X。
2. 打开手部连杆，只关掉 X：检查手不能碰 X 以外的东西。

规划（MotionGen）只能带一套设置，所以用第 2 种设置来规划，再用第 1 种设置逐段校验得到的轨迹。只有接触那一段需要两次查询，空中移动仍然是一次。

### 4.2 统一的查询入口：`rig.clear`

- `with rig.clear.scope(allow): ...`：进入时设置查询上下文，退出时恢复，取代直接写 `coll_kw`，泄漏问题也就没了。
- 所有运动入口都改成接受 `allow=`，不再接受 `collision=`：`move_to`、`move_left_to`、`joint_path`、`follow_both`、`drive_base`。
- `follow` / `left_follow` 只接受经过检查的路径。比如加一个 `Checked` 包装类型，原始插值必须先经过 `rig.clear.check_path(qs, allow)`。
- 失败后的退路只保留一条：带检查的直线 → cuRobo 规划 → 都不行时，像现在一样不检查、直接走直线，不让 skill 失败（决定 1）。每次退回都记一条 `clearance_fallback` 事件，内容包括动作标签、`allow`，以及直线上会碰到的连杆和障碍物。
- `drive_base(path, allow=FREE)` 沿路径采样底盘位姿（每 5 cm、5°），用当前的手臂姿态和手里的物体做批量检查。不通过时，加大 `margin` 重新规划路径；还不行就按原路径走，同样记一条 `clearance_fallback`。这把 `_clear_for_tuck` 的做法推广成默认行为。
- `contract_runtime` 每次进入一个 skill 时，把查询上下文重置为 `FREE`。

### 4.3 运行时监视器：`unexpected_contact`

每 30 tick，用实际关节角和实际底盘位姿，检查机器人碰撞球对场景的穿透。超出当前 `allow` 的接触，记一条事件：连杆、最近的障碍物、穿透深度，以及当时的 skill 和动作标签。

- 用 `profile` 开关控制（`execution.contact_monitor`），所有 profile 默认打开（决定 3）。
- **必须没有副作用。** 10-31 的诊断探针调用了 `arm.prepare` 和 `_apply`，会改动规划用的锁定值、关闭的连杆和剔除中心。正式版改用独立的全身运动学模型来算碰撞球；障碍物位姿和启用状态在检查前临时改动，检查后原样恢复，剔除中心不碰。
  - 当时同一个 P12 s11 换了 park、变成了成功，我曾归因于探针的副作用。这个归因不成立：见 7.4，规划本身在相同输入下就会分叉。
- 意外接触只作为指标，不影响任务成败（决定 2）。评估脚本新增两项：每个 episode 的意外接触次数，以及 `clearance_fallback` 次数，并按 skill 汇总。

### 4.4 清理

- 删掉 `world.active`、`world.left_active`、`WorldModel.temp_obstacles`。
- 删掉"另一只手的手指一律不查"（`_query`）和 `other_touching` 的永久排除。改成只在 `allow` 里显式声明时才不查，比如 handover 时两只手都要接触物体。
- 底盘位姿和关节限位的临时修改，改成 `rig.clear` 提供的上下文管理器（`at_base(...)`、`pinned_torso()`），不再到处手写 `try/finally`。

## 5. 迁移计划

> **2026-11-01：本节的阶段 3–5 已被第 8 节的修订计划取代。** 阶段 0–2 已完成（7.1–7.3）。

原则：每一步先只记录、不改变行为，确认影响面之后，再切换成"先规划无碰撞路径"。每一步跑同一组回归：
- 单元测试
- `build_skill_library --check`
- 每个任务一个 variation 的 41 个 episode（`v3_sticky_gt_one_variant.json`）
- P07、P12 的针对性重跑

和 `b0bbcdd` 的结果对比。

| 阶段 | 内容 | 行为变化 | 怎么算完成 |
|---|---|---|---|
| 0 | 把 AST 审计脚本放进 `tools/`；加 `unexpected_contact` 监视器（4.3），不改任何检查 | 无 | 跑一轮 41 个 episode 拿到第一份"实际意外接触"清单，并和第 2 节的静态清单对照 |
| 1 | 加 `clearance.py`：定义 `Allow`、`rig.clear.scope`；`contract_runtime` 每个 skill 开始时重置上下文；`coll_kw` 只经过 `scope` 写入；所有 `collision=False` 机械地换成 `unchecked(reason=原标签)`；加单元测试：禁止出现裸的 `collision=False`，`unchecked` 必须带理由 | 只有修复 `coll_kw` 泄漏这一项会改变行为 | 回归测试中失败数不增加；监视器记录的意外接触数不增加 |
| 2 | 空中移动（附录 A 第 1 类）改成 `FREE_ELSE_STRAIGHT`：先规划无碰撞路径，规划不出来就退回直线并记日志 | 只在"直线会撞、而规划器能找到别的路"时改变行为。原计划的 `measure` 一步省掉了：退回直线时行为和以前完全一样，`clearance_fallback` 日志已经记下了"带检查过不去"的每一处 | P07 s10 在打开监视器时没有意外接触；回归不变差 |
| 3 | 接触动作（附录 A 第 2 类）改成 `grasp` / `handle` / `press` / `sweep` / `set_down`，用两次查询的语义 | 同上，先 measure 再 plan | 监视器只剩 `allow` 范围内的接触 |
| 4 | `drive_base` 沿路径检查手臂和手里的物体；`_back_off`、边走边放、wipe 和 flip 的底盘推、handover 时开车，都传入各自的 `allow` | 同上 | 搬运类任务（T10、T12、T13、T20）回归不变差 |
| 5 | 左臂统一：`LeftArmFoldPolicy` 和左臂的运动都走 `rig.clear`；删掉另一只手手指的豁免和 `other_touching`；做 4.4 的清理 | 有变化 | 涉及双手的任务（P06、P07、handover）回归不变差 |

阶段 0 和 1 没有行为风险，可以直接做。2 到 5 每一步都要跑完回归才能进入下一步。

## 6. 已定的决定（2026-10-31）

1. **规划不出无碰撞路径时，不让 skill 失败。** 像现在一样不检查、直接走直线，并记一条 `clearance_fallback` 日志（见 4.2）。所以从阶段 2 起，"改变行为"指的是：能规划出无碰撞路径时改走规划的路径，规划不出来时行为和现在一样。
2. **意外接触只当指标**，不算任务失败，也不扣分（见 4.3）。
3. **监视器在所有 profile 里默认打开**，包括 `physical/*`、`sticky/*`、`sticky_snap/*`。阶段 0 要实测它的时间开销，写进本文档。
4. **模块名为 `zeno_skills/clearance.py`**，类和函数名用 `Allow`、`rig.clear`、`unexpected_contact`、`clearance_fallback`。

还没定的只剩一项：`Allow` 的几个预设是否覆盖了所有 skill。这要等阶段 0 的监视器数据。

## 7. 进度

### 7.1 阶段 0 和 1：已完成（2026-10-31，提交 `ef01cb1`）

| 内容 | 位置 |
|---|---|
| `Allow`、`FREE`、`unchecked(reason)`、`LEGACY`、`BASE_DRIVE`、`Clearance`（技能作用域、当前动作、监视器） | `zeno_skills/clearance.py` |
| `rig.clear`；`move_to` / `move_left_to` / `joint_path` 的 `collision=` / `check=` 改成 `allow=`；`follow_both`、`tuck`、`drive_base` 也会登记当前动作 | `zeno_skills/rig.py` |
| 每个 skill 都在 `rig.clear.skill(verb)` 作用域里运行：进入时两只手臂的 `coll_kw` 清空，退出时恢复调用方的值。`coll_kw` 不再泄漏到下一个 skill，这是这两个阶段里唯一会改变行为的一处 | `zeno_skills/skill_runtime.py` |
| 监视器的查询 `Motion.robot_contacts`；`sync` 中读取真实位姿的部分拆成 `_live_poses` / `_put_poses`，两边共用 | `zeno_skills/motion.py` |
| 113 处布尔开关机械替换：`allow=LEGACY` 111 处（其中 4 处由原来的动态写法改成条件表达式），`_carry_pose` 里的重试循环改用 `FREE` / `LEGACY` 二元组；`tools/run_skills.py` 的测试夹具改为 `unchecked("test fixture: ...")` | 各 skill 和 policy 文件 |
| `execution.contact_monitor`：默认打开，不计入 profile hash（`NOT_HASHED`），所以已有 run 的 hash 不变（`sticky/gt` 仍为 `c52e0cc65be8`） | `episode/profile.py` |
| `result.json` 新增 `contacts` 字段；`EVALUATION.md` 新增 `contacts` 列和"Unexpected contacts by skill"表 | `benchmark/run_episode.py`、`env_service/worker.py`、`benchmark/evaluate.py` |
| 审计工具：按文件统计 `LEGACY`、`unchecked`、`coll_kw` 写入、`drive_base` 和原始 `follow` 调用 | `tools/audit_collision.py` |
| 防退化测试：禁止再给运动入口传 `collision=` / `check=`；`LEGACY` 数量只能减少（`LEGACY_BUDGET = 111`）；`Allow` 的语义；技能作用域；监视器去重；开关不改变 hash | `tests/test_clearance.py` |

单元测试 220 个全部通过，`build_skill_library --check` 通过。

阶段 0 的"跑一轮 41 个 episode 拿到第一份清单"还没做，要先征得同意再跑。

### 7.2 监视器实测

- **频率：** 每 30 tick 检查一次；如果距上次检查以来，机器人的底盘、两只手臂和手指都没动（变化小于 `STILL` = 1e-3），就跳过。
- **开销：**
  - 每次检查 15–22 ms（P12 s11、P07 s10）。P12 s11 整个 episode 多 5.6 秒，墙钟时间多约 3%（76.6 秒 vs 74.3 秒）。
  - 最初每次要 37–55 ms，其中 24 ms 花在逐个读回全场物体的位姿上。现在只读底盘 1.6 m 以内（`MONITOR_NEAR`）的物体和部件，用到的障碍物集合会缓存，直到底盘移动超过 `RECULL` 或者手里拿的东西变了。
- **接触对象的命名：** 物体和部件直接用名字。静态场景是一整块合并的网格（prim 叫 `World/mesh`），所以按标注里家具的包围盒归属：先找包含接触点的最小包围盒，找不到就取 25 cm 以内最近的。
- **冒烟测试中首批抓到的接触：** 都是代码审计找不到的、"带检查的动作"里发生的接触。

| episode | skill | 动作 | 是否带检查 | 接触 |
|---|---|---|---|---|
| P07 s10 | pick | `pick_pre_far` | 是 | 右手手指压进 `kitchen_island` 8.7 mm |
| P07 s10 | navigate | `tuck` | 是 | 右手手指压进 `kitchen_island` 17.5 mm |
| P07 s10 | tuck(left) | `LeftArmFoldPolicy` 直接插值收臂（它不经过运动入口，所以记录里沿用了上一个动作标签 `left_release_back`） | 否 | 左臂 `link_7` 压进 `kitchen_island` 46 mm |
| P12 s11 | open | `tuck` | 是 | 右手手指压进 `kitchen_cabinet_6` 的柜体 20 mm |
| P12 s11 | close | `close_push_contact` | 否 | 推门时手指接触柜体（预期的接触，阶段 3 会改成 `handle` 预设） |

前两行和第四行发生在"带检查"的动作里，原因是 `ignore_fingers`（2.2 节）：这些动作检查时不算自己的手指。

### 7.3 阶段 2：已完成（2026-11-01）

- **新的 `Allow`：** `FREE_ELSE_STRAIGHT`（`Allow.fallback`）。
- **实现：** `Rig._checked_else_straight` 被 `move_to`、`move_left_to`、`joint_path` 共用，流程是：
  1. 起点不在碰撞中时，先按 `FREE` 规划，依次尝试直线、约束规划、`q_hint`、全局 IK。
  2. 规划失败，或者起点已经处于碰撞中，就按 `LEGACY` 走原来那条直线。
  3. 退回时调用 `clear.fallback` 记一条 `clearance_fallback`：写明规划失败的原因，以及直线路径上第一处碰撞的连杆（新增的 `ArmKin.explain` / `Motion.explain`）。
- **迁移范围：** 第 1 类 63 处，其中 60 处 `move_to` / `move_left_to`、3 处 `joint_path`。`LEGACY` 从 111 降到 48（`LEGACY_BUDGET = 48`），剩下的都是第 2 类接触动作。
- **评估指标：** `result.json` 的 `contacts` 里新增 `planned` / `fallback` / `fallback_by_leg` / `fallbacks`；`EVALUATION.md` 新增 `fallbacks` 列和"Clearance fallbacks by motion"表。
- **测试：** 223 个全部通过；`build_skill_library --check` 通过。

**冒烟测试**（seed 10，各任务第一个 variation，sticky/gt，不录像，和 10-31 三种子测试中 seed 10 的同一批 episode 对比）：

| episode | 结果 | 10-31 | 规划成功 / 退回直线 | 意外接触 |
|---|---|---|---|---|
| P07 present_and_brace | 成功 | 失败 | 12 / 0 | 2 |
| P17 pour | 失败（"0/3 items reached"，已知的能力缺口） | 失败 | 25 / 0 | 2 |
| P19 spoon_dip | 成功 | 成功 | 10 / 0 | 5 |
| T09 tomato_soup | 成功 | 成功 | 14 / 0 | 8 |
| T10 trash_the_can | 成功 | 成功 | 4 / 1 | 2 |
| T13 breakfast_setup | 成功 | 成功 | 6 / 2 | 3 |

- 没有出现新的失败。P07 这次成功，可能来自 `b0bbcdd` 的下垂收起姿态，也可能是 7.4 说的规划随机性，单次结果分不清。
- **3 次退回直线**都是 `pick_lift`，原因是"起点已经处于碰撞中"：刚夹住物体时，夹爪本体（`gripper_link`）贴着物体或支撑面 2–27 mm。这类情况要等阶段 3 用 `grasp` 预设声明"可以碰被抓的物体"，届时就不必再退回。
- **剩下的意外接触**几乎都发生在已经带检查的 pick 动作里：`pick_grasp` 10 次、`pick_pre_far` 9 次，另有 `place_above` 1 次。原因是这些动作用了 `ignore_fingers`，手指不参与检查。这也是阶段 3 的范围。

### 7.4 新发现：同样的输入，规划结果不确定

同一个 P07 s10、同样的代码、同样关掉监视器，连跑两次：一次 `present` 的约束规划给出 32 个路点并成功，另一次给出 60 个路点，接着 `shake` 报 "no IK for shake" 而失败。物理过程在 tick 2695 之前逐事件完全一致，分叉就出现在这一次 cuRobo 规划上。开监视器时也是两种结果都出现过，所以和监视器无关。

后果：benchmark 的单次结果不能直接比较，一个 episode 的成败可能只是这次规划落在了哪个分支上。这需要单独排查（cuRobo 的随机种子、CUDA 的不确定性，或者 `PLAN_TIMEOUT` 下尝试次数的差异），不在本计划范围内。

### 7.5 11-01 回归：下垂收起姿态的回退和修复（2026-11-01）

**结果：** `a0a9574` 两种子全量（170 个 episode）138 → 108，新失败 41 个，新成功 11 个（`benchmark/runs/v3_sticky_gt_1101_2seeds/COMPARE.md`）。基线是 10-31 的 `e124cd4`，所以差别里还包括一直没回归过的 `b0bbcdd`。

**主因是 `b0bbcdd` 把下垂姿态当成了常驻收起姿态（`kin.rest`）：**

| 现象 | episode |
|---|---|
| 地上取物要先降躯干，手臂下垂时手碰到地面（`torso_lift_joint` 报 `GRAPH_FAIL`） | T12 ×5、P18 ×2 |
| 从台面或层板上方往下收手臂，路径被挡（"cannot fold the arm"） | T19 ×4、T09、P14 |
| 从下垂姿态出发的带检查运动规划失败（`pick_pre_far`、`close_push_pre_high`、左臂 `handover_left_pre`） | 约 9 个 |
| `find_park` 几乎所有候选都因 IK 被拒（`'ik': 120`） | T09、T17 |

**修复（未提交）：** `kin.rest` 恢复成 10-31 的肘外姿态，左臂 `LEFT_ARM_FOLD` 也恢复。下垂姿态改名为 `DRIVE_Q`（`kin.drive`），只在 navigate 开车时使用：`skills._hang_while_driving` 在 `drive_base` 前把处于收起姿态的空手垂下来，到达后再抬回收起姿态。事件为 `drive_hang` / `drive_raise`，两种都做不到时记 `*_blocked`，手臂保持原样。

只跑了两个 episode 就停了：T12 duck_in_study 恢复成功；T09 lid_on_spoon_away 越过了原来的 `find_park` 失败，最后差 5 mm 没放进锅。有 5 次 `drive_raise_blocked`：到了 park 抬不回收起姿态，手臂只能继续垂着。

**仍然存在：** 开去 pick 的 park 时，垂着的手臂把岛台上的 `juice_bottle` 碰倒了（T03 s11）。`plan_path` 在终点 0.4 m 范围内不检查（`relax`），底盘方柱连同垂着的手臂可以伸进岛台的范围。这属于阶段 4（`drive_base` 沿路检查手臂）。

### 7.6 监视器：手里的物体和被推动的物体（2026-11-01）

- **手里的物体：** `robot_contacts` 把手里物体的包围盒（`box_spheres`，用实时位姿）当作机器人的一部分，接触报成 `held:<物体>`，由 `Allow.held_on` 判断是否允许。
- **被推动的物体：** 实测发现，轻的可动物体一碰就被推走，碰撞球压进去的深度始终到不了 `MIN_DEPTH`。T03 里勺子扫倒瓶子、container 被推开，接触监视器一条都没记到。所以监视器另外盯着底盘附近没被拿着的物体：移动超过 2 cm，或者竖直轴倾斜超过 20°（绕竖直轴转动不算），就记一条 `disturbed_object`，附上当时的 skill 和动作。以下情况不算：
  - 当前 `Allow` 允许接触的物体；
  - 刚松手 2 秒内的物体（还在落下或滚动）；
  - 和手里的物体一起移动的物体（装在里面或放在上面）；
  - 2 秒内被拿到手里的物体（正在被抓起的那个）。

  同一个物体报过一次后，有 2 秒的静置时间，滚动不会重复报。
- **评估：** `result.json` 的 `contacts` 里新增 `disturbed` / `disturbed_by_skill` / `disturbed_by_leg` / `disturbances`；`EVALUATION.md` 新增 `disturbed` 列和"Disturbed objects by motion"表。
- **T03 s11 实测：** 瓶子被碰倒（`drive_base`，移动 2.8 cm、倾斜 17.6°，之后又在 `pick_lift` 时被碰到一次）；放擀面杖时压动了容器里的勺子（`place_retreat_up`、`container_exit`）。

## 8. 修订后的计划（2026-11-01）

> 逐步执行的清单见 `COLLISION_PLAN.md`。

### 8.1 目标

每个 skill 只保留**必要的中继位姿**，中继位姿之间的运动全部由规划器生成，不再写死：

- 手臂：cuRobo MotionGen，手里的物体算进碰撞模型；需要时加姿态约束（例如手里的东西不能倾斜）。
- 底盘：在 (x, y, 朝向) 空间里规划，可行性用整机碰撞检查判断：底盘占地 + 手臂姿态 + 手里的物体。

规划不出来时，仍按决定 1 退回原来的直线运动，并记 `clearance_fallback`。

**为什么改：** 原计划的阶段 2 给每一段运动单独加检查（`FREE_ELSE_STRAIGHT`），但没有删掉任何路点，每段反而多了一层"规划，不行就走直线"的逻辑，代码更复杂了。阶段 4 的第一版也走偏了：底盘沿路检查出碰撞以后，靠手写的备选路径去绕（原地转、退出来转身再进），每多一个场景就多一种手写路径。这一版已经整体删掉。

### 8.2 什么算必要的中继位姿

**算：** 任务本身决定的位姿，以及后面紧跟着接触动作、方向有规定的位姿。

| 类别 | 中继位姿 |
|---|---|
| 底盘 | park（`find_park` 选出）；开车时的手臂姿态（`DRIVE_Q`）；收起姿态（`kin.rest`） |
| pick | 抓取前位姿（沿抓取方向的起点）、抓取位姿；之后沿抓取方向抬起或退出，这一段是接触动作 |
| 搬运 | 搬运姿态（手收在身体前方，过门不刮） |
| place / drop | 目标上方的位姿、松手位姿；之后的后撤是接触动作 |
| open / close | 把手前位姿、把手位姿；拉门或推门沿门的轨迹走（`ride`） |
| press / wipe / push / stir 等 | 接触起点；接触段本身按规定方向走直线 |

**不算（要删）：** 只是为了绕开障碍物而写的中间点和底盘挪动，例如：
- "先抬 X cm 再横移"：`drop_prelift`、`place_rise`、`table_pre_lift`、`microwave_pre_lift`、`container_pre_lift`；
- "先退出来"：`place_back_from_edge`、`*_back` 之后接 `*_up`、`flat_back_out`；
- 中间过渡点：`carry_in_via`、`table_staging`、`rotate_clear`、`held_vertical_move` 先往身体方向拉回再抬；
- 底盘盲动：`_back_off` 的 11 处调用、`navigate_back_from_door`、放餐桌时退 0.4 m 再开回、放冰箱层板时退出去摆好手臂再开回、`_clear_for_tuck`。

**保留但改写成约束：** 一部分路点写的其实是规划器不知道的约束，例如手里的东西不能甩（关节一次最多变 1.2 rad、慢速、平滑）、IK 分支要连续（pour、handover）。这些不是避碰路点，要改成规划器的约束（速度上限、姿态约束、IK 种子），而不是删掉了事。

### 8.3 步骤

每一步单独提交、单独跑回归（41 个 episode 各任务一个 variation，加上针对性重跑），和上一步比较成功数、`contacts`、`disturbed`、`fallbacks`。

| 步骤 | 内容 | 完成标准 |
|---|---|---|
| 0. 基线 | 验证收起姿态修复（7.5）：11-01 新失败的 41 个加 P07 s10/s11、P12 s11；没有退步就提交 | 收起姿态相关的失败恢复，P07/P12 仍然成功 |
| 1. 规划可复现 | 查清 7.4 的不确定性来源（cuRobo 随机种子、CUDA 不确定性、`PLAN_TIMEOUT` 内的尝试次数），把规划结果固定下来；做不到的话，至少用同一提交跑两次，量出翻转率 | 同样的输入得到同样的轨迹，或者有一个已知的噪声水平可以对照 |
| 2. 手臂规划的前提 | 手里的物体在所有空中运动的规划里都算进碰撞模型（现在只有 `_carry_pose` 和带东西的躯干运动）；起点就贴着支撑面的情况（刚抓起、刚放下），用 `held_on` 声明只允许碰这个支撑面，不再整段关掉检查；"不能甩""不能倾斜"写成规划约束 | 空中运动都带着手里的物体规划 |
| 3. 底盘规划器 | 新写 (x, y, 朝向) 的格点搜索：一次批量算出起点到终点附近所有格子的整机可行性（底盘占地、手臂当前姿态、手里的物体），在上面做 A*；替换 `plan_path`，包括它在终点附近 0.4 m 不检查的放宽。目标可以是一个区域，例如"收起姿态无碰撞的位置"，用来取代 `_clear_for_tuck`。先只记录：和 `plan_path` 的结果并行算，统计两者不一致的次数 | 记录模式下跑完回归，确认新规划器在大多数情况下能给出路径 |
| 4. 底盘切换 | navigate 改用新规划器；删掉 `_back_off`、`navigate_back_from_door`、放餐桌和放冰箱层板的"退出去再开回"、`_clear_for_tuck`。开车时的手臂姿态（下垂）只要沿路可行就用，规划器在终点附近自己决定什么时候换回收起姿态 | 碰倒和推走物体的次数（`disturbed`）下降，回归不变差 |
| 5. 手臂按 skill 合并 | 每个 skill 把空中的中间点合并成"从当前姿态规划到下一个中继位姿"，删掉 8.2 里"不算"的那些路点。按经过次数排序：`_carry_pose` → place 那条链 → drop → pick 的抬起和退出 → open/close 之后的后撤 → `held_vertical_move` → 其他 | 每合并一个 skill，回归不变差，`FREE_ELSE_STRAIGHT` 的数量相应减少 |
| 6. 接触动作 | 原阶段 3：接触段用 `grasp` / `handle` / `press` / `sweep` / `set_down` 预设和两次查询的语义（4.1），`LEGACY` 清零 | 监视器只剩 `allow` 范围内的接触 |
| 7. 左臂和清理 | 原阶段 5：左臂走同一套规划；删掉 `coll_kw` 的 `ignore_fingers`、另一只手手指的豁免、`other_touching`、`temp_obstacles` 等（4.4） | 涉及双手的任务回归不变差 |

步骤 1 是后面所有对比的前提：规划结果不可复现，单次回归就分不清改动的影响和噪声。

### 8.4 当前状态（2026-11-01）

- **未提交：** 收起姿态修复（7.5）；监视器把手里的物体算进去，并记录被推动的物体（7.6）。单元测试通过。
- **已删除：** 阶段 4 的第一版（沿路检查 `Motion.sweep` / `Rig.drive_clear`、navigate 的手写备选路径、按方向挑选的 `_back_off`）。步骤 3 的底盘规划器需要类似的批量整机检查，届时按新规划器的需要重写。

## 附录 A：关掉检查的位置（按 skill）

**第 1 类：在空中移动却不检查（手不需要碰任何东西）**

| skill | 动作标签 | 位置 |
|---|---|---|
| place / stack / cover / 放进容器 | `place_above`（只有放进容器时才检查）、`place_rise`、`place_back_from_edge`、`place_over_neighbours`、`table_staging`、`table_pre_lift`、`container_pre_lift`、`microwave_pre_lift`、`container_exit`、松手后的后撤（`place_retreat_*`）。`place_insert`、`place_lower` 是把物体放到支撑面上，阶段 2 实施时移到第 2 类 | `skills.py` `place`（:1727 起） |
| 沿边放下扁平物体 | `flat_over`、`flat_back_out`、`flat_retreat`、`flat_up`（落下和推的那几步属于第 2 类） | `skills.py` `place_flat`（:2326 起） |
| pick 的抬起和退出 | `pick_lift`、`pick_fail_clear`、`edge_lift`、`edge_pull`、`corner_lift`、`handle_pick_lift`、从微波炉取物的 `cavity_pick_front` / `above` / `lift` | `_pick_pinch_core`、`_edge_pinch_impl`、`_corner_pinch`、`handle_grasp.py`、`embedded.py` |
| lower / lift / 调高度 | `held_vertical_move` 整段（pour、regrasp、upright 也在用） | `skills.py:231` |
| drop | `drop_prelift`、`drop_above`、`drop_retreat` | `hand.py` `DropIntoPolicy` |
| hover | `hover_lift`、`hover_above`、`hover_settle` | `extra.py` `HoverOverPolicy` |
| pour | `pour_over`、`pour_tilt`、`pour_rock`、`pour_return`，加两次 `joint_path(check=False)` | `tooluse.py` `PourIntoPolicy` |
| stir | `stir_raise`、`stir_above`、`stir_out`、`dip_out` | `tooluse.py` `StirContainerPolicy` |
| shake / wave | `shake`、`shake_end`、`wave_swing` | `extra.py` |
| rotate / square、regrasp、release、flip | `rotate_held`、`rotate_clear`、`regrasp_clear`、`release_back`、`left_release_back`、`flip_withdraw`、`flip_clear` | `hand.py` |
| open / close 之后 | `*_back`、`*_up`、`close_push_back` | `_move_articulated`、`_push_close` |
| handover | `handover_right_clear`，加一次 `joint_path(check=False)` | `bimanual.py` |
| 微波炉放入和取出 | `microwave_release_up`、`microwave_retreat` | `withdraw_microwave_cavity` |
| sticky 修正 | `sticky_clear` × 2 | `sticky.py` |
| 搬运姿态 | `carry_up`：带检查的不行就关掉检查重试 | `_carry_pose` |

**第 2 类：接触动作（手必须碰到目标，但现在整台机器人都不检查）**

| skill | 动作标签 | 对应的 `Allow` 预设 |
|---|---|---|
| press / heat / stop | `button_align`、`button_press`、`button_retract`，以及微波炉按钮的 align、press、release | `press` |
| knock、touch | `knock_tap`、`knock_back`、`knock_retract`、`touch_down`、`touch_up` | `press` |
| push / pull / center / separate / sweep | `*_down`、`push_slide`、`push_up`，以及 `_contact_sweep` 的 down、sweep、up | `sweep` |
| wipe | `wipe_press`、`wipe_lift`（`wipe_above` 只是移到台面上方，阶段 2 实施时移到第 1 类） | `sweep` |
| stir | `stir_dip`、`stir_circle` | `sweep` |
| close（推门） | `close_push_contact` | `handle` |
| pick 最后夹取那一下 | `pick_grasp_fix`、`edge_pre`、`edge_grasp`、`corner_pre`、`corner_grasp`、`corner_grasp_retry` | `grasp` |
| brace | `steady_grasp` | `grasp` |
| flip、upright | `flip_arc`、`flip_push*`、`upright_pivot*`、`upright_lower`、`upright_hang_lift`、`upright_release_clear` | `grasp` 或 `set_down` |
| 沿边放下扁平物体 | `flat_lower`、`flat_release_down`、`flat_push_down`、`flat_push` | `set_down` 或 `sweep` |
| 微波炉放入 | `microwave_insert` | `set_down` |
| place 落下 | `place_insert`、`place_lower`（阶段 2 实施时从第 1 类移来） | `set_down` |
