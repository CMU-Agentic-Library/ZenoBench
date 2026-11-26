# 选手和旧技能迁移计划（MOTION_ARCHITECTURE 9.3 第 9 步及剩下的旧技能）

写于 2026-11-24，起因：第 8c / 8d 步（微波炉腔体取放）改走 pick / place 以后，从腔体里取碗 29 次构造全失败（`/data/zenobench/cavitydbg_1124`，停车点搜索的转储）：碗在腔体最前沿，门开到 −80° 挡住左侧，右侧是控制面板，正前方能停的窄带上右手的肘撞控制面板 / 机身、躯干撞门。旧代码靠写死的停车点和手腕转角从右前方斜着伸进去。用户 11-24 决定：pick / place 选手（左手从正前方伸进去，肘在远离控制面板的一侧），只认右手的旧技能也一起迁移，都按 MOTION_ARCHITECTURE 第 1 节的规则做。

本文件是计划：做什么、按什么顺序、每步怎么查、做到什么算完。每步的检查结果记在 MOTION_ARCHITECTURE 9.3；本文件第 7 节只记做到哪了、下一步从哪接。

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
| 9b | 契约按物体（3.2）：手的取值加 `any`（任一只）/ `both`（两只都空）；评分的 `["hand_empty", "right"]` 改成 `"both"`；已经用空手的技能（open 的电机门、press、heat、stop、inspect）的契约改成 `hand_empty(any)`。pick / place 一族的契约随 9c 和代码一起改，旧技能的随各自迁移改（每次提交契约都如实） | 同 9a 的集（契约只换写法，行为不变）；`build_skill_library.py --check` | 83 处改完；v6 路线静态检查（bench 的 1510/1510）仍过 |
| 9c | pick 选手（3.1）：目标集合 × 空着的手；place / drop / stack / cover 用拿着的那只手 | 强制左手开关（诊断，不进基线）跑 3 集左手 pick + place；不强制跑 T07 broken_oatmeal_away 前半、T20、T25 看选到哪只手 | 左手 pick → place 整集成功至少 2/3；右手为主的集成败不变或变好 |
| 9c 后 | 9c 做完、9d 之前：pick 可能选左手，而路线后面的微波炉放入还是旧代码只认右手（T07 microwave_works 11-25）——明确报错，9d 解决 | — | — |
| 9d | 微波炉腔体取放（第 8c / 8d 步，3.5）：取出 stash，改走 pick / place，退役 018–021、048，删旧腔体代码和 `microwave_retrieval_q` | T07 microwave_works、broken_oatmeal_away、two_portions__counter | 三集里的腔体放入、取出都成；需要的话加 3.5 的穿过开口 |
| 9e | 取放家族的旧技能：lift / lower、hover、present | v6 里用到它们的集（lift 13、hover 11 次所在的集，挑 ≤ 30 分钟的） | `CarryHeightAdjust`、`SetHeldHeight`、`HoverOver`、`PresentHeld` 只调 `run_skill`；`held_vertical_move` 删 |
| 9f | 转向和摆正：rotate、square、upright、regrasp、release | square (6)、rotate (4) 所在的集 | `orientation.py`、`hand.py` 里这几个的 `old_entry` 归零 |
| 9g | 接触类：wipe、touch、knock | wipe (11)、touch (2) 所在的集 | `WIPE_PRESS`、`TOUCH_DEPTH` 登记；`tooluse.WipeSurfacePolicy`、`extra.TouchObjectPolicy`、`KnockPanelPolicy` 只调 `run_skill` |
| 9h | v6 没用到的接触 / 手势：roll、tip（`_contact_sweep`）、flip、pour、wave、point、shake | 每个技能一个最小场景（`tools/run_skills.py`），各自 ≤ 5 分钟 | 这些文件的 `old_entry` 归零 |
| 9i | 双臂：handover、brace、双手搬（第 9 步原文：两手一起搬的物体进碰撞模型，闭链约束另议） | v6 的双手搬集（如有）+ handover 最小场景 | `bimanual.py` 的 `old_entry` 归零 |
| 9j 收尾 | 剩下的旧入口：reset、point 的原语、`_move_articulated`、`_swing_arm`、sticky 的 snap / place；文档 | 本次涉及的集 | `old_entry` = 0、`LEGACY` = 0（做到一部分，见第 7 节） |
| — | 全量（v6 种子 10，151 集）作为新基线 | — | 和 v6full_1123（136/151）对比，掉的逐集归类 |

9a–9d 是让微波炉取放能做的最短路径；9e–9g 是 v6 用到的旧技能（约 50 次调用）；9h–9j 是 v6 没用到、但目录里有的。9h、9i 每个技能的设计在动手前写进 MOTION_ARCHITECTURE 第 6 节，和之前关门的做法一样。

## 5. 基线

9c 起停车点和手都会变，等于换基线：9c、9d 以后各跑一次针对性检查，9g 以后（v6 用到的都迁完）跑一次全量作为新基线；9h–9j 不影响 v6（没用到），只跑针对性检查。

## 6. 用户的决定（11-24）

1. **路线里的手**：v6 路线不依赖"东西在右手"。3.2 的契约改动以后照常跑 bench 的静态检查即可。
2. **评分里的 `["hand_empty", "right"]`**：改成"两只手都空"（随 9b 做：评分的谓词和 v6 生成器里写它的地方；生成器在 `benchmark/v6/` 下，是 bench 作者的代码，改的时候在交接文档里写明）。
3. **左手持物限速、搬运姿态**：直接镜像右手的值。
4. **边走边取放**（`mobile.py`）：先放着，不在 9a–9j 里；9j 收尾时它仍走旧入口的话单独列出来。

## 7. 进度（11-25）

| 步 | 状态 | 提交 / 位置 |
|---|---|---|
| 9a 持物状态按手 | 做完，检查 4/4（右手不变） | 033f3791 |
| 9b 契约和评分（`any` / `both`） | 做完，检查 4/4（评分 best 1.0，`hand_empty(both)` 都成立） | a2288b35 |
| 9c pick 选手 | 做完；强制左手 3/3 整集成功（T11、T04、T22，含冰箱层板） | fe321f67 |
| 左手放下的收臂起点碰撞（9c 的后续） | 做完：规划器按两根手指各自的实测值（`Hand.fingers`），不再都取较宽的那根；定向 5/5 | 8cba9d98 |
| 9d 微波炉腔体取放 | 部分做完（用户 11-25：先提交，进 9e）：放入走 place，检查 2/4；microwave_works、broken_oatmeal_away 仍建不出（见下）；取出走 pick 没在仿真里跑过，也没有单测走到腔体里的 pick（v6 种子 10 的路线没有从腔体取出） | d5a360ba；`/data/zenobench/hand9d2_1125` |
| 9e 取放家族的旧技能：lift / lower、hover、present | 做完，检查 5/6（唯一失败 after_dinner 在 pick takeout_tray，1125 也败在这里）；`held_vertical_move` 还没删：upright、regrasp、pour 还在用（9h 删） | 9b4f1353；`/data/zenobench/hand9e_1125` |
| 9f 转向和摆正：rotate、square、upright、regrasp、release | 做完，检查 T02 rotate 2/2（一集左手）、T06 display_row square 1/1（三块都摆正，这次都是右手；强制左手见下）；upright、regrasp、release 在 v6 没用到，只有单测；`held_vertical_move` 还剩 pour 在用（9h） | 794771bd；`/data/zenobench/hand9f_1125`、`hand9f3_1125` |
| 9g 接触类：wipe、touch、knock | 做完，检查 6/6（T08 wipe ×5、T19 touch）+ 强制左手 T08 wipe 成功；knock 在 v6 没用到，只有单测 | 2a4e45f4；`/data/zenobench/hand9g_1125` |
| 9h v6 没用到的接触 / 手势 | 迁完（每个都走 `run_skill`、按手），但 roll、flip、pour 的检查仍失败（见下）；wave、point、shake、tip 成功 | bef85df6、94b60272、10dc6efc；`/data/zenobench/hand9h_1125` |
| 9i 双臂 | brace、handover 做完（P07、P06 成功）；两手搬没做（用户 11-25 定跳过） | b9a267f4、6ab73c05；`/data/zenobench/hand9i_1125` |
| 9j 收尾 | 做了一部分：旧入口 52 -> 21，LEGACY 0（剩下的见下） | 202bc7a9；`/data/zenobench/hand9j_1125` |
| 规则审查的修改（11-25） | 第九阶段对照第 1 节和 MOTION_ARCHITECTURE 第 1 节的规则逐条查出来的问题，都改了（见下"规则审查"） | 13ccf93a 起；`/data/zenobench/rules_1125` |

9a–9j 已推送（origin 到 202bc7a9，11-25）；规则审查的修改没推送。

**左手放下的收臂起点碰撞**（v6full_1125 的 4 集由成功变失败：T01 seats_c、T14 e1_book_ready、T14 blue_book、T18 bowl_in_use__oatmeal）：State 每只手只记较宽那根手指的宽度，规划器两指都放在那里；左手 edge place 松手后两指实测 0.036 / 0.029 m（命令 0.032），模型里加宽的右指压进刚放下的书 4–5 mm，收臂起点被 cuRobo 拒绝。8cba9d98：`Rig.snapshot` 记两指各自的值（`Hand.fingers`），`with_width`（计划的张开）清掉它，`Motion.query` / `live_locks` 两个指轴各设各的。检查 `/data/zenobench/fingers_1125` 5/5（加 T29 toy_box）。T29 里还有一次左手收臂起点 4 mm 碰撞，两指读数几乎相同，是另一个原因，没查（整集恢复成功）。

**9d 做到哪**（11-25 第二次，`/data/zenobench/hand9d2_1125`，T07 四集）：stash 的改动（微波炉放入 / 取出改走 place / pick，退役 018–021、048，删旧腔体代码）加上 3.5 的两段，只对标注了 `cavity_aabb` 的腔体（`plan_place(cavity=...)`）：
- 抽出的长度按模型量（`_off_load`：指尖越过放下的物体的顶 `LEAVE_MARGIN`），不是固定一个手指长；
- 抽出之后 `place_exit`：沿开口水平出来，长度量到手臂在腔体盒子里的碰撞球都出了开口面 `LEAVE_MARGIN`（`_out_of_cavity`），再收臂。

结果：microwave_holds_pot、two_portions__counter 成功（后者左手把碗放进微波炉，整集成功）；microwave_works、broken_oatmeal_away 失败（停车点搜索 7 / 15 次构造都不成）。转储：碗放在腔体最前沿，手跨在门槛外夹碗沿（手在 y 2.29–2.33，开口面 2.345），所以 `place_exit` 一次都没触发；失败在抽出（沿夹爪轴往上约 8 cm，末端左前臂 `left_arm_link_5` 进开口上方的机身框 1–2 mm）和收臂（TRAJOPT）。这两集 1125 也是失败（当时是旧代码只认右手、直接拒绝），不算回退。取出走 pick 没在仿真里跑过。

**以后接着做 9d**：碗沿捏取在门后的抽出方向（现在只能沿夹爪轴往上；要么让放的目标里有夹爪轴更朝开口的，要么抽出先上到指尖过碗沿、再朝开口），以及找一集从腔体取出的场景验证 pick。

**9e 做了什么**（11-25）：lift / lower = `plan_held_move`（原地，TCP 竖直一条直线到目标高度，手的朝向不变，`FREE_LOAD`；旧代码往身体拉回的 5 个中间点和 3 次闭环重试删了）；present = `plan_posture` 到身前 4 个位置组成的一个目标集合（左手横向镜像）+ 转头段 `present_look`；hover = `plan_hover`（`plan_drop` 只留 arrive / reach，停车点搜索同 drop，物体底面在目标顶面上方 6 cm）。job 在 `skill_jobs/held.py`、`skill_jobs/drop.py:hover_job`，catalog 加 lift / lower / present / hover；policy_034 / 093 / 115 / 072 只调 `run_skill`；契约 `holding(any)`，谓词 `held_above` / `held_below` / `presenting` / `hovering_over` 认任一只手。检查 `/data/zenobench/hand9e_1125`：T10 trash_moved__dining（1125 败在 lift 只认右手）、can_on_island、keep_kids_can（左手 lift + hover）、guests_coming，T05 e1_pencil_asked（左手 present）成功；after_dinner 败在 pick takeout_tray（no reachable grasp，1125 同一个 pick 失败）。lower 在 v6 没用到，只有单测。

**9f 做了什么**（11-25）：rotate = `plan_posture` 到一个目标集合（手的朝向绕竖直轴转给定角度，位置是现在的 TCP 或旧代码的 4 个往底盘拉回 / 抬高的点，保持倾角）；upright = `plan_posture(hold_tilt=False)` 到"物体竖直"的目标集合（8 个朝向 × 原地抬高或胸前 8 个点），旧代码的大网格、IK 连续性搜索和放下撬起 / 挂直两级退路删了；release = `plan_release`（张开 + 沿夹爪轴退一个手指长，动之前都建好）；regrasp = place + pick（都走运动分层），旧的"直接竖直放下"分支删了。square 不再 pick 之后单独 rotate：**摆正的转角放进 place 的目标集合**（`place(square=True)`：按放下那一刻手里物体的朝向算出摆正需要的转角，加 0 / ±90 / 180），因为 pick 之前量的转角会随搬运姿态漂（检查里第一次左手放下选了 135° 转角，块偏 44°；改成 rotate 后只许 90° 倍数仍偏 44°，就是这个漂移）。路线 id `pick_rotate_place` 保留（覆盖、验证数据引用它），步骤里已经没有 rotate。强制左手（`ZENO_PICK_SIDE=left`，诊断，不进基线）T06 display_row 整集成功，6 次 pick 都是左手，三块都摆正（`/data/zenobench/hand9f3_1125/runs_left`）。`orientation.py` 的旧入口 24 -> 0，`hand.py` 19 -> 12（剩下的是 flip、LeftSteady 等，9h / 9i）。

**9g 做了什么**（11-25）：touch / knock 直接用 `plan_press`（指尖沿 u 压进被碰的面 `TOUCH_DEPTH` 2 mm，锚点，按测量退出，收臂；touch 是物体顶面，4 个合爪方向；knock 是门板上把手旁的 5 个点 × 2 个合爪方向，`KnockPanelPolicy` 每敲一次跑一次技能），job 在 `skill_jobs/press.py`，记 `touch_contact` / `knock_contact`。wipe = `plan_wipe`（`skill_plans/contact.py`，stir 的形状）：到达 → 自由段到按压位姿上方 → 直线压下 `WIPE_PRESS` → 任务段沿带子擦（`scripted`，世界坐标系的 `Still`，`carry="arm"`，`reach`：能擦多长量出来）→ 擦回 → 锚点 → 抬起 → 回到来时的姿态；擦不到半条带子的停车点在构造里拒掉；覆盖率在两段任务段执行时每 4 个物理步采一次。旧代码是手臂不动、底盘平移，按压有接近段，抬起是写死的 8 cm 不查碰撞，都删了。为此加了两样东西：静态家具能按名字放进 `Spec.touch`（`Motion._touch_key`：静态碰撞体按所属家具记作 `furniture:<名字>`，和接触监控报的名字同一条规则），`Still(None)` 是世界坐标系。检查：右手 5 次 wipe 手臂擦 12–16 cm，覆盖率 0.6–0.73（旧代码平移底盘擦满 30 cm）；强制左手那次擦满 30 cm，覆盖率 1.0。`extra.py` 的旧入口 17 -> 6，`tooluse.py` 11 -> 8（剩下的是 pour 等，9h）。

**9h 第二部分**（11-25）：tip = push 的新方式 `poke`（合拢的指尖朝推的方向，在物体高度 `TIP_HEIGHT` 80% 处推，一条腿），P04 瓶子倒下 92°、仍在台面上。roll = push 的拖（`drag`），两个方向都作为目标（往机器人外侧那个排前）。push（`slide_job`）改成用空着的手（右手优先；原来右手拿着东西就拒绝），契约 `hand_empty(any)`。任务段的碰撞失败现在写出撞到哪个部位、哪个物体（`_script_path`）。`contact.py` 旧入口 6 -> 0，`_contact_sweep` 删了。

**roll 卡在哪**：P03 擀面杖。往外拖时手指在约 9 cm 处撞到前面的 oatmeal（旧代码的扫动不查碰撞）；换成往里拖以后规划成功，执行时 `slide_down` 停在离目标 1.4 cm 处：拖的 TCP 在顶面上方 `DRAG_PRESS` 6 mm，合拢的指尖在 TCP 下方约 2 cm，等于按设计压进物体约 1.4 cm，刚性的擀面杖顶住了手（`run` 的"停在目标前"判据）。这是 push 的 drag 本身的压深，v6 的拖（T01、T29 的书）也走它；改 `DRAG_PRESS` 会动基线，等用户定。

**9h 第三部分**（11-25）：flip = `plan_flip`（`skill_plans/contact.py`）：被夹住的近边绕远边的圆弧任务段（`reach`：转到手臂够不着为止），松手，没过竖直时张开的手沿圆弧接着推，`contact_extent` 退出，收臂，等它落定；转不到 60° 的计划在构造里拒掉。pour = `plan_pour` + `skill_jobs/pour.py`：停车点搜索（6 个手腕转角 × 2 个杯口偏移 × 倒的方向），到倒的起点，绕"手和杯口中点"的水平轴倾倒（`reach`，最多 110°，不到 60° 拒掉），停，沿原弧倒回，回到到达时的姿态。`held_vertical_move` 删了（最后一个用户是 pour）。

检查（v3，种子 10）：P17 左手倒到 110°，3 个番茄倒出 1 个（11-08 旧代码 0/3），仍失败——旧代码卡住时"晃一晃"的补救没搬（退路）；P05 flip 只转得到约 15°（`no IK along the task at s=0.349`）：flip 没有自己的停车点搜索，从 pick 留下的手臂姿态按碰撞模型延续 IK 转不过去；旧代码不查碰撞、每步全局 IK 跳解，转到 90° 但书也没翻过去（z dot −0.56）。要修 flip，得把圆弧放进 pick（或 flip 自己）的停车点 / 抓法选择里——设计上的事，没做。

**9i 做到哪**（11-25）：brace = 左手的 pick，只取 rim / rim_rect / top / handle 捏法，`plan_pick(stop="pick_held")` 抓住就停（不抬、不搬），结果判据：那只手拿着、物体没挪（1.5 cm）；P07 整集成功（杯子只动了 0.7 mm，之后左手 release、收臂也成），11-08 旧代码这一步败在 TRAJOPT。`hand.py` 旧入口 3 -> 0。

**handover**（11-25）：`skill_jobs.pick.handover_job`（catalog 的 `handover`，不找停车点：东西在给的那只手里，底盘一动它跟着动）。目标 = 给的手递到胸前的位置（`HANDOVER_AT`，旧代码的 6 个）× 朝向（长物体转到长轴和正前方成 50 / 60 / 70°、两头都行，夹爪绕自身轴转半圈的等价朝向也算；其他物体 0 / ±90 / 180°）× 接的手的抓法（标注的 pinch，加上 `side_variants`：每个手指水平合拢的 top pinch 派生两个从侧面水平伸入、手指上下合拢的抓法——只给 handover，普通 pick 的目标集合不变）。在原地按代价顺序建：给的手到递出位置的自由段（每个位置建一次），再在东西的新位置上建接的手的 pick（抓住就停）；第一个建得出来的执行，然后给的手 release。`plan_release` 的抽出改成按 `contact_extent` 量（离开 `LEAVE_GAP` 再走 `LEAVE_MARGIN`），不是一个手指长：P06 右手松开时一个手指长的直线没有 IK。检查：P06 接住（侧向抓法，第 25 个递出位姿，试了 444 组）、右手松开，整集 OK（后面开柜门失败，和 11-08 一样）；P07 再跑一次也 OK，但这次 brace 没抓成：停车点搜索的构造预算这次只建了 3 个（上次第 6 个成），是已知的预算问题，不是这次改动。

**9j 做了什么**（11-25）：
- reset 改成 tuck → stand（policy_006）→ straighten（policy_009），都是运动分层的技能；push / pull 的路径去掉开头的合爪（policy_041：推的计划自己合爪）；杯把手 pick（policy_055）改成 pick 只取 `handle_pinch`，握法记作 handle。
- 退役：policy_039 / 040 / 041 / 095（reset 和合爪的原语）；类改成 `RetiredPolicy`（调用时说明被什么取代，id、目录、契约图都还在）：Right* 四个原语、PlanHome、PlanPoint、PrepareFloorReach、抓 / 放门把手、ReachWhileMoving、ApproachTarget。
- `skills.py` 删掉 `_swing_arm`、`_fold_left`、`_move_with_retry(_impl)`、`_move_articulated`、`_ride`、`_ride_check`、`park_over`；微波炉在 `skills.open_articulated` / `close_articulated` 里改成按门键（`press_button(door=...)`，v6 的路线本来就走 powered 路径）；各策略文件里不再用的 `find_park` 导入和 `_park_diag` 删了。
- 检查（v3 种子 10）：P09 整集 OK（其中 push 从后面推没找到停车点——11-08 用的还是迁移前的旧 push，不能对比）；P01 的 reset 排在 crouch 之后，没跑到。

**还剩的旧入口（21 处）**：
- 两手搬（`bimanual.py` 7：flat pick、box lift、carry）——用户 11-25 定跳过；
- 边走边取放（`mobile.py` 5）——策略本来就是关闭的，用户 11-24 定先放着（第 6 节问题 4）；
- `check_held` 里掉落时张手（`skills.py` 1）——钩子里的副作用，还没变成段；
- sticky 的 snap 级瞬移、接住掉落（`sticky.py` 8）——计划里说按 Actuator 的写操作处理，还没做。
所以 `Rig.move_to` / `joint_path` / `follow_both` 等旧入口、旧的 `planner.find_park`（`tools/build_tasks.py` 和它自己的单测还在用）都还不能删。

**要告诉 bench 作者的**：评分的 `["hand_empty", "right"]` 改成了 `"both"`（9b：`benchmark/v6/define_tasks_v6.py` 的 `both_hands_empty` 和几个生成器文件里的字面量，`tasks.json` / `STATIC.json` 重新生成）。
