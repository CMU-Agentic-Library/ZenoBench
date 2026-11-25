# 选手和旧技能迁移计划（MOTION_ARCHITECTURE 9.3 第 9 步及剩下的旧技能）

写于 2026-11-24，起因：第 8c / 8d 步（微波炉腔体取放）改走 pick / place 以后，从腔体里取碗 29 次构造全失败（`/data/zenobench/cavitydbg_1124`，停车点搜索的转储）：碗在腔体最前沿，门开到 −80° 挡住左侧，右侧是控制面板，正前方能停的窄带上右手的肘撞控制面板 / 机身、躯干撞门。旧代码靠写死的停车点和手腕转角从右前方斜着伸进去。用户 11-24 决定：pick / place 选手（左手从正前方伸进去，肘在远离控制面板的一侧），只认右手的旧技能也一起迁移，都按 MOTION_ARCHITECTURE 第 1 节的规则做。

本文件是计划：做什么、按什么顺序、每步怎么查、做到什么算完。每步做完在 MOTION_ARCHITECTURE 9.3 记结果，本文件只改计划本身。

## 1. 规则在这件事上的意思

| 规则（MOTION_ARCHITECTURE 第 1 节） | 落到选手和旧技能迁移上 |
|---|---|
| 1 只给必要的中继位姿 | 每个旧技能迁移时删掉它写死的停车点、路点、手腕转角列表、"先抬 10 cm 再……"这类中间位姿；只留停车点、接触段起点、任务轨迹起点、收臂姿态 |
| 2 每个决定只有一个出处 | 用哪只手是一个决定，出处是技能的 `build`（停车点搜索在每个候选上建整份计划）。不在 job 里先选手、也不在路线里替技能选手（路线只能写"必须用某只手"这种任务约束，见 3.2） |
| 3 没有 fallback | 不是"先试右手、不行再换左手"：两只手都是目标集合里的目标，同一次搜索里比。做不出来就失败，不换成不查碰撞的路、不缩短重试 |
| 4 接触段：方向由任务定，长度由碰撞模型量 | 旧技能里固定长度的"抬 6 cm""退 10 cm"换成 `straight` / `contact_extent`；深度常数（`WIPE_PRESS`、`TOUCH_DEPTH` 等）登记在 COLLISION_PLAN 第 8 节 |
| 5 持物在碰撞模型里 | 左手的持物和右手一样：手指、held link、碰撞球（`held_spheres`）、保持倾角、限速 |
| 6 每段声明 `Allow` | 迁移后不再有 `LEGACY` / `unchecked`；每个接触段写明哪只手的哪部分可以碰什么 |
| 7 一次只迁一块 | 下面第 4 节每一步单独提交，先针对性检查（≤ 30 分钟，一个仿真），全部做完再跑一次全量作为新基线 |
| 8 决定早做，轨迹晚做 | 手、抓法、停车点在搜索时定；收臂等过渡段的轨迹走到时再按实测建（11-24 已做的 `run._late_tuck`） |
| 9 误差分三层 | 每个迁移后的技能有锚点（到达、握上 / 接触、松手）和按技能的容差（`tolerances.py`），超出就从这里用同一个 `build` 重做 |
| 10 依赖只能向下 | 新的 `build` 不碰 `rig`；"哪只手"在 `State` / `Hand` / `kin.side` 里，不在全局变量里 |

## 2. 现状

### 2.1 写死右手的地方

- **契约**：`skill_library/definitions.py` 83 处前后条件写死右手（`holding(hand=right, X)`、`hand_empty(hand=right)`）。左手拿起的东西，后面的 place、drop、stack、cover、collect 都不认。
- **代码**：`rig.held` 148 处引用（右手的持物），`rig.left_held` 另有一套；`skills.check_held` / `check_left_held` 两个函数（左手的少了 `held_shift` 重锚、掉了张手）；`sticky` 的焊接、`carry_posture`、pick / place / drop 的 job 都按右手写。
- **已经对称的**（第 6a 步，11-11）：`State` 的 `body` + `arms`、`Actuator` 按 `side`、`park_search` 每组目标带手（`Problem.goals` 第 4 项、`find_park` 收两只手的 `kin`、肩和朝向偏好镜像）、`Motion.query` 里另一只手的东西、`open` / `close` / `press` 用空着的手。
- **评分**：v6 `tasks.json` 的目标里 `["hand_empty", "right"]` 出现 2256 次。物体最后都放下了，右手空这一条照样成立；但语义上应是"两只手都空"，要和 bench 作者商量（第 6 节问题 2）。

### 2.2 还走旧代码的技能

碰撞审计的 `old_entry`（直接调 `rig.move_to` / `joint_path` / `follow` / `grip` 这些旧入口）现在 154 处。按技能分（v6 路线里的调用次数在括号里，0 是 v6 没用到）：

| 形状 | 技能（v6 次数） | 旧代码在哪 | 迁成什么 |
|---|---|---|---|
| 取放家族 | lift (13)、lower (0) | `skills.held_vertical_move`（`CarryHeightAdjustPolicy`、`SetHeldHeightPolicy`） | 持物的直线（`straight`，保持倾角），目标是高度；`carry_posture` 的一部分 |
| 取放家族 | hover (11) | `extra.HoverOverPolicy` | `plan_drop` 去掉松手（开口上方的中继位姿 + 保持倾角的自由段） |
| 取放家族 | present (1) | `gestures.PresentHeldPolicy` | 持物到"给人看"的姿态：一个中继位姿的自由段 |
| 取放家族 | 微波炉腔体取放（heat 路线里，约 10 次） | `skills.insert / release / withdraw_microwave_cavity`、`embedded.PickFromCavityPolicy` | `plan_place` / `plan_pick`（8c / 8d），靠选手（第 3.5 节） |
| 取放家族 | release、regrasp、upright、square / rotate 的放下部分 (6 / 4) | `hand.ReleaseInPlacePolicy`、`RegraspPolicy`、`orientation.UprightObjectPolicy`、`hand.RotateHeldPolicy` | `plan_place` / `plan_pick` 换目标集合（转一个角度再放 = 放的目标集合里加转角） |
| 接触类 | wipe (11) | `tooluse.WipeSurfacePolicy` | stir 的形状：到达 → 下压 `straight`（`WIPE_PRESS`）→ 擦的条带 `scripted`（`still`）→ 锚点 → 抬起 |
| 接触类 | touch (2)、knock (0) | `extra.TouchObjectPolicy`、`KnockPanelPolicy` | press 的形状：进入 `straight`（`TOUCH_DEPTH`）→ 锚点 → 退出（`contact_extent`） |
| 接触类 | roll、tip（v6 0） | `contact._contact_sweep` | slide 的形状（`pushed` / 第 6 节的 `rolled` / `pivot` 耦合） |
| 接触类 | flip (0)、pour (0) | `hand.FlipFlatPolicy`、`tooluse.PourIntoPolicy` | 持物绕轴转的 `scripted`（`carry="arm"`），pour 的倾倒角是任务量 |
| 姿态 / 手势 | wave、point、shake (0) | `extra.WaveHandPolicy`、`gestures.PointAtPolicy`、`extra.ShakeHeldPolicy` | 姿态类：摆动相位为参数的 `scripted`（第 5 步留下的）；point 是一个中继位姿 |
| 双臂 | handover、brace (0)、双手搬（navigate 的 bimanual 路径） | `bimanual.py`、`hand.LeftSteadyPolicy` | 第 9 步原文：两手一起搬的物体进碰撞模型；handover 是右手放、左手取的两段计划 |
| 取放的旁路 | pick / place while moving (0)、pick cup_handle (0) | `mobile.py`、`handle_grasp.PickCupHandlePolicy` | pick / place 的目标集合（把手捏取是一种抓法）；边走边取放另议（第 6 节问题 4） |
| 其他 | reset、point 用的 `Right*Policy`（旧原语）、`skills._move_articulated`（无把手 / 非电机的门）、`_swing_arm`、`sticky` 的 snap / place | — | 原语删掉；`_move_articulated` 并进 open / close；sticky 的瞬移（snap 级）不是运动，按 `Actuator` 的写操作处理 |

v6 用到的旧技能一共约 60 次调用（lift 13、hover 11、wipe 11、腔体取放约 10、square 6、rotate 4、touch 2、present 1），其余是 v6 没用到、但目录里有的技能。

## 3. 设计

### 3.1 手是目标集合的一个维度

- pick 的目标集合 = {空着的手} × {抓法}。每个目标带手（`Problem.goals` 第 4 项，已支持），`build(s, k, prior)` 用目标 k 的手的 `kin`、那只手的收臂姿态、那只手的搬运目标。排序用已有的弱偏好：右手的目标在前（每靠后一位加 `VARIANT_COST`），由 `score`（可操作度、离限位）决定，不是先右后左。
- place / drop / stack / cover 等"手里有东西"的技能：手就是拿着这个物体的那只（没有选择）；`build` 用那只手的 `kin`。
- 只有一只手空时，pick 只有那只手的目标（`door_hand` 的规则）。
- 搜索代价：目标数翻倍，排序 IK 已按手分批（6a）。要量 pick 停车点搜索的时间，超过现在的 1.5 倍就先做第 7 节"同一位置的几组目标共用底盘候选"。

### 3.2 契约：按物体说，需要时再说手

- `holding(object=X)`：任一只手拿着 X（谓词已有 `held_name(rig, hand)`，加一个不带手的版本）；`hand_empty()`：至少一只手空。pick 的前提改成"有一只手空"，输出 `hand`（哪只手拿起的）；place / drop / ... 的前提改成 `holding(object=X)`。
- 任务确实要求某只手时（另一只手要留着干别的、双手协作的分工），路线给 pick 传 `hand=`：这是任务约束，缩小目标集合，不是替技能做决定（规则 2）。
- 改动在 `definitions.py`（83 处）、`predicates.py`、`contract_runtime` 的复核，`tools/build_skill_library.py` 重新生成。v6 的路线和评分要和 bench 作者对一遍（第 6 节问题 1、2）。

### 3.3 持物状态按手

- `rig.held` / `rig.left_held` 收成 `rig.held_by(side)`（读）和按手的登记 / 释放；`check_held` / `check_left_held` 合成一个按手的版本（左手补上 `held_shift` 重锚、掉了张手——这会改变旧代码左手的行为，所以和第一个左手取物一起做）。
- `sticky` 的焊接、`carry_posture`、`Rig.snapshot` 的 `Held` 都按手；`motion_skills.posture("carry", side)` 已按手。
- 只认右手的调用点（148 处 `rig.held`）按文件逐个改：新层里的直接改按手；旧技能里的随该技能迁移一起改（第 4 节），迁移前遇到左手持物明确报错（"<技能> 只认右手，还没迁移"），不静默用错手。

### 3.4 什么算一只手"能做"

和右手完全一样的判据，没有左手专用的常数：同样的 `Spec`、同样的容差、同样的锚点。两臂是镜像的（URDF 关节限位、力矩一致，6a 已核对），左手的抓法、TCP 约定和右手相同（`gripper_rot` 不分手，6a 强制左手开门 3/3 已验证）。

### 3.5 微波炉腔体（第 8c / 8d 步）

- 先做 3.1–3.4 让 pick / place 能选左手，再把微波炉取放改走 pick / place（11-24 的尝试在 `git stash`："9.3 step 8c/8d attempt 11-24"：路由改到 policy_015 / 061，退役 018–021、048）。
- 如果选手以后腔体放入仍有"保持倾角伸进腔体"的 TRAJOPT 失败（11-24 放入 1/2），再加"穿过开口"的进入段：开口外的中继位姿 + 沿开口法向的 `straight`（方向由开口定，长度到腔体前沿，规则 4），只对标注了 `cavity_aabb`（五面封闭、只开一面）的腔体用。先不做，等选手以后的数据。

### 3.6 旧技能迁移的共同做法

每个旧技能迁移都按已迁技能的样子（stir、press、slide）：`skill_jobs/<技能>.py` 的 job（目标集合、hooks、结果判断）+ `skill_plans/` 的 `plan_<技能>`（原语串起来），catalog `MOTION_SKILLS` 加一项，policy 只调 `run_skill`；每个 `build` 有 FakeKin 单测；`old_entry` 计数只降不升；技能文档（`docs/skills/<技能>.md`）跟着写。迁移时一并按手（规则见 3.1、3.3），不先迁右手版再补左手。

## 4. 步骤

每步：单独提交；单测全过；针对性检查一个仿真、≤ 30 分钟（先放该步改到的、之前失败的集，再放几集之前成功的看回归）；结果写进 MOTION_ARCHITECTURE 9.3。

| 步 | 内容 | 针对性检查 | 完成标准 |
|---|---|---|---|
| 9a | 持物状态按手（3.3）：`held_by(side)`、合并 `check_held`；旧技能和还只认右手的新层 job（place、drop、stir）遇左手持物报错（`carry_posture` 按手随 9c：它是 `plan_navigate` 搬运段的右臂版；sticky、`snapshot` 已按手） | 右手不变：T07 microwave_works、T22 by_kind、T11 一集托盘、T09 lid_off（调用、停车点、锚点同改之前）；FakeKin 左手单测 | 右手行为不变；左手持物的状态读写有单测 |
| 9b | 契约按物体（3.2）：`holding(object)`、`hand_empty()`、pick 输出 `hand`、可选 `hand=`；skill 库重新生成 | 同 9a 的集（契约只换写法，行为不变）；`build_skill_library.py --check` | 83 处改完；v6 路线静态检查（bench 的 1510/1510）仍过 |
| 9c | pick 选手（3.1）：目标集合 × 空着的手；place / drop / stack / cover 用拿着的那只手 | 强制左手开关（诊断，不进基线）跑 3 集左手 pick + place；不强制跑 T07 broken_oatmeal_away 前半、T20、T25 看选到哪只手 | 左手 pick → place 整集成功至少 2/3；右手为主的集成败不变或变好 |
| 9d | 微波炉腔体取放（第 8c / 8d 步，3.5）：取出 stash，改走 pick / place，退役 018–021、048，删旧腔体代码和 `microwave_retrieval_q` | T07 microwave_works、broken_oatmeal_away、two_portions__counter | 三集里的腔体放入、取出都成；需要的话加 3.5 的穿过开口 |
| 9e | 取放家族的旧技能：lift / lower、hover、present | v6 里用到它们的集（lift 13、hover 11 次所在的集，挑 ≤ 30 分钟的） | `CarryHeightAdjust`、`SetHeldHeight`、`HoverOver`、`PresentHeld` 只调 `run_skill`；`held_vertical_move` 删 |
| 9f | 转向和摆正：rotate、square、upright、regrasp、release | square (6)、rotate (4) 所在的集 | `orientation.py`、`hand.py` 里这几个的 `old_entry` 归零 |
| 9g | 接触类：wipe、touch、knock | wipe (11)、touch (2) 所在的集 | `WIPE_PRESS`、`TOUCH_DEPTH` 登记；`tooluse.WipeSurfacePolicy`、`extra.TouchObjectPolicy`、`KnockPanelPolicy` 只调 `run_skill` |
| 9h | v6 没用到的接触 / 手势：roll、tip（`_contact_sweep`）、flip、pour、wave、point、shake | 每个技能一个最小场景（`tools/run_skills.py`），各自 ≤ 5 分钟 | 这些文件的 `old_entry` 归零 |
| 9i | 双臂：handover、brace、双手搬（第 9 步原文：两手一起搬的物体进碰撞模型，闭链约束另议） | v6 的双手搬集（如有）+ handover 最小场景 | `bimanual.py` 的 `old_entry` 归零 |
| 9j | 收尾（第 10 步）：删旧入口（`Rig.move_to` / `move_to_any` / `joint_path` / `move_left_to` / `leave`）、旧 `planner.find_park`、旧的碰撞上下文；`Right*Policy` 原语、`_move_articulated`、`_swing_arm`、pick / place while moving 的旧实现 | 单测 + 一组跨技能的集 | `old_entry` = 0，`LEGACY` = 0 |
| — | 全量（v6 种子 10，151 集）作为新基线 | — | 和 v6full_1123（136/151）对比，掉的逐集归类 |

9a–9d 是让微波炉取放能做的最短路径；9e–9g 是 v6 用到的旧技能（约 50 次调用）；9h–9j 是 v6 没用到、但目录里有的。9h、9i 每个技能的设计在动手前写进 MOTION_ARCHITECTURE 第 6 节，和之前关门的做法一样。

## 5. 基线

9c 起停车点和手都会变，等于换基线：9c、9d 以后各跑一次针对性检查，9g 以后（v6 用到的都迁完）跑一次全量作为新基线；9h–9j 不影响 v6（没用到），只跑针对性检查。

## 6. 用户的决定（11-24）

1. **路线里的手**：v6 路线不依赖"东西在右手"。3.2 的契约改动以后照常跑 bench 的静态检查即可。
2. **评分里的 `["hand_empty", "right"]`**：改成"两只手都空"（随 9b 做：评分的谓词和 v6 生成器里写它的地方；生成器在 `benchmark/v6/` 下，是 bench 作者的代码，改的时候在交接文档里写明）。
3. **左手持物限速、搬运姿态**：直接镜像右手的值。
4. **边走边取放**（`mobile.py`）：先放着，不在 9a–9j 里；9j 收尾时它仍走旧入口的话单独列出来。
