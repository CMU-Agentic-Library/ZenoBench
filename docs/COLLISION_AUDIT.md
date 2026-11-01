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
  - 当时同一个 P12 s11 换了 park、变成了成功，我曾归因于探针的副作用。这个归因不成立：见 7.3，规划本身在相同输入下就会分叉。
- 意外接触只作为指标，不影响任务成败（决定 2）。评估脚本新增两项：每个 episode 的意外接触次数，以及 `clearance_fallback` 次数，并按 skill 汇总。

### 4.4 清理

- 删掉 `world.active`、`world.left_active`、`WorldModel.temp_obstacles`。
- 删掉"另一只手的手指一律不查"（`_query`）和 `other_touching` 的永久排除。改成只在 `allow` 里显式声明时才不查，比如 handover 时两只手都要接触物体。
- 底盘位姿和关节限位的临时修改，改成 `rig.clear` 提供的上下文管理器（`at_base(...)`、`pinned_torso()`），不再到处手写 `try/finally`。

## 5. 迁移计划

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
| 2 | 空中移动（附录 A 第 1 类）改成 `FREE` 加统一退路，先改 `place`，再改 pick 的抬起、`held_vertical_move`、drop、hover、pour、stir、release、open 和 close 之后的后撤 | 分两步：先开 `mode="measure"`，照旧走直线，只记录"带检查会不会通过"；跑一轮回归后，再按类切换成 `mode="plan"`，即先规划无碰撞路径，规划不出来就退回直线并记日志 | P07 s10 在打开监视器时没有意外接触；回归不变差 |
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

### 7.1 阶段 0 和 1：代码已完成（2026-10-31，未提交）

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

### 7.3 新发现：同样的输入，规划结果不确定

同一个 P07 s10、同样的代码、同样关掉监视器，连跑两次：一次 `present` 的约束规划给出 32 个路点并成功，另一次给出 60 个路点，接着 `shake` 报 "no IK for shake" 而失败。物理过程在 tick 2695 之前逐事件完全一致，分叉就出现在这一次 cuRobo 规划上。开监视器时也是两种结果都出现过，所以和监视器无关。

后果：benchmark 的单次结果不能直接比较，一个 episode 的成败可能只是这次规划落在了哪个分支上。这需要单独排查（cuRobo 的随机种子、CUDA 的不确定性，或者 `PLAN_TIMEOUT` 下尝试次数的差异），不在本计划范围内。

## 附录 A：关掉检查的位置（按 skill）

**第 1 类：在空中移动却不检查（手不需要碰任何东西）**

| skill | 动作标签 | 位置 |
|---|---|---|
| place / stack / cover / 放进容器 | `place_above`（只有放进容器时才检查）、`place_rise`、`place_back_from_edge`、`place_over_neighbours`、`table_staging`、`table_pre_lift`、`container_pre_lift`、`microwave_pre_lift`、`container_exit`、`place_insert`、`place_lower` | `skills.py` `place`（:1727 起） |
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
| wipe | `wipe_above`、`wipe_press`、`wipe_lift` | `sweep` |
| stir | `stir_dip`、`stir_circle` | `sweep` |
| close（推门） | `close_push_contact` | `handle` |
| pick 最后夹取那一下 | `pick_grasp_fix`、`edge_pre`、`edge_grasp`、`corner_pre`、`corner_grasp`、`corner_grasp_retry` | `grasp` |
| brace | `steady_grasp` | `grasp` |
| flip、upright | `flip_arc`、`flip_push*`、`upright_pivot*`、`upright_lower`、`upright_hang_lift`、`upright_release_clear` | `grasp` 或 `set_down` |
| 沿边放下扁平物体 | `flat_lower`、`flat_release_down`、`flat_push_down`、`flat_push` | `set_down` 或 `sweep` |
| 微波炉放入 | `microwave_insert` | `set_down` |
