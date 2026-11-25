# 姿态：下蹲、站起、弯腰、直腰、收臂；举高、放低、举到头前、转向、竖起、松手

2026-11-16 起走运动分层（`skill_plans/posture.py` 的 `plan_posture`，job 在 `skill_jobs/posture.py`；`../motion/MOTION_ARCHITECTURE.md` 第 6 节、9.3 第 5 步）：在机器人现在站的地方做一段关节运动，不选停车点，不挪底盘。

## crouch / stand / bend / straighten（一个身体关节）

1. **目标**：躯干升降（crouch 到给定高度，stand 到上限），或腰的俯仰（bend 到给定角度，straighten 到 0）。不给值的（crouch 的"最低"、stand、bend 的"最大"、explore 的下蹲）是"能走多远走多远"：沿关节直线走到两条手臂都不碰的最后一点为止，长度由碰撞模型量；给了值的到不了就失败。目标超出关节范围直接拒绝，机器人不动。
2. **只动这一个关节**（`Spec.joints`）：两条手臂相对躯干不动，跟着身体一起降、一起弯；两只手里的东西也跟着走。
3. **查碰撞**：整段先用右臂的模型查（右臂、右手、右手里的东西对世界和机器人自己的底盘），再用左臂的模型按同样的身体值查一遍（左臂、左手里的东西对世界和底盘）：每条手臂的模型只查自己这条手臂对底盘，身体一动两条手臂都在动。手指在模型里。
4. **做不出来就失败**：关节直线不通、规划也不通，技能失败，机器人不动。旧代码（`_move_posture_joint`）在这里先收臂再试、再挪底盘，两级退路都删了。
5. **执行**：任一只手拿着东西时平滑起停、放慢（和推门前的 `push_body` 一样）。做完检查两只手里的东西还在，关节实测离目标在 2 cm（躯干）/ 0.035 rad（腰）以内才算成功（`TORSO_AT` / `WAIST_AT`，沿用旧值，没实测）。

## tuck（收一条空手臂）

1. 这只手拿着东西：拒绝（拿着东西开车用搬运姿态，见[搬运姿态](carry.md)）。
2. 右臂：目标是收起姿态（`kin.rest`）。左手空着时躯干和腰一起回到 (0, 0)；左手拿着东西时身体不动，只动右臂（`MOTION_ARCHITECTURE.md` 4.1）。
3. 左臂：先张开左手，再只动左臂到它的收起姿态，身体不动。
4. 收起姿态在这里会碰、或者走不过去：失败。旧代码挪底盘再收（`fold_where_possible`），左臂是不查碰撞的关节直线，都删了。下垂不算收好：技能保证的 `arm_stowed` 要求收起姿态。
5. 结果：手臂关节离收起姿态 0.10 rad 以内（`STOWED_TOL`）。

## lift / lower（手里的东西竖直上下）

HAND_PLAN 9e（11-25）：`CarryHeightAdjustPolicy` / `SetHeldHeightPolicy` → `run_skill(SKILLS["lift" / "lower"])`，job 是 `skill_jobs/held.py`，计划是 `plan_held_move`。

1. 拿着这个物体的手（哪只都行）；物体底面已经够高（lift）/ 够低（lower，2 cm 以内，`HEIGHT_TOL`）就不动。
2. **一条直线**：TCP 从现在的位置竖直走到让物体底面到达给定高度的那个高度，手的朝向不变（物体倾角保持），`FREE_LOAD` 查碰撞。
3. **做不出来就失败**：旧代码 `held_vertical_move` 在直线没 IK 时先把物体往身体拉 8–30 cm 的 5 个中间点再抬，`CarryHeightAdjustPolicy` 还按实测底面闭环重试 3 次，都删了（规则 3）。物体被卡住跟不上手，结果判定失败。
4. 结果：实测底面 ≥ 目标 − 2 cm（lift）/ ≤ 目标 + 2 cm（lower）。

## present（把手里的东西举到头前）

HAND_PLAN 9e：`PresentHeldPolicy` → `run_skill(SKILLS["present"])`，job 是 `skill_jobs/held.py` 的 `present_job`，计划是 `plan_posture` 加一个转头段。

1. 物体中心在身前的 4 个位置（`PRESENT_AT`，左手的横向镜像）组成**一个目标集合**，手的朝向不变；自由段到第一个能到的（旧代码是 4 个依次 `move_to` 重试）。
2. 头转向自由段终点处的物体（`present_look`），再记录视野（`record_view`）。

## rotate / upright（手里的东西原地转向）

HAND_PLAN 9f（11-25）：`RotateHeldPolicy` / `UprightObjectPolicy` → `run_skill(SKILLS["rotate" / "upright"])`，job 在 `skill_jobs/held.py`，计划是 `plan_posture`（一个自由段到一个目标集合），用拿着东西的那只手。square 不再用 rotate：路线是 pick → place(square=True)，摆正的转角在 place 的目标集合里（见 [place](place.md)）。

- **rotate**：手的朝向绕竖直轴转给定角度；位置是现在的 TCP，或往底盘拉回、抬高的 4 个点（`ROTATE_AT`，旧代码的中间点），都在一个目标集合里。保持物体倾角（绕竖直轴转不改倾角）。结果：物体朝向变化和要求差 10° 以内（`ROTATE_TOL_DEG`），握法重新记下。旧代码按 15° 一步、每个中间点依次试，删了。
- **upright**：倾角已在 `max_tilt_deg` 内就不动。否则目标集合 = 让物体竖起来的手的朝向（绕竖直轴 8 个朝向，`UPRIGHT_YAWS`）× 位置（原地抬高 12 cm 或半个最长边，或胸前 8 个点，`UPRIGHT_FRONT`，左手镜像）；自由段**不保持倾角**（`plan_posture(hold_tilt=False)`），物体照样在碰撞模型里。结果：倾角在限内。旧代码约 100 个中间点的网格、IK 连续性搜索、以及"放下再撬起"/"挂直"两级退路都删了。

## release（原地松手）

HAND_PLAN 9f：`ReleaseInPlacePolicy` → `run_skill(SKILLS["release"])`，计划 `plan_release`：张开到抓取时的宽度（手指可以碰它放开的东西），再沿夹爪轴退一个手指长度。两段都在动之前建好：退不出来就失败，手还没张开（旧代码先张开、退不出来只记一笔）。

regrasp（`RegraspPolicy`）现在是 place（支撑面上离底盘最近、往里 12 cm 的点）加 pick，都走运动分层；旧的"已经在空地上方就直接竖直放下"分支删了。

## wave / point / shake（手势）

HAND_PLAN 9h（11-25）：`WaveHandPolicy` / `PointAtPolicy` / `ShakeHeldPolicy` → `run_skill(SKILLS["wave" / "point" / "shake"])`，job 在 `skill_jobs/held.py`，计划是 `plan_gesture`：[张手] → [自由段到一个目标集合] → [摆动任务段：TCP 沿水平方向 `amp · sin(s)`，世界坐标系 `Still`，`carry="arm"`] → [收回]。

- **wave**：空着的手（右手优先）张开，举到身前、手那一侧 0.35 / 0.25 m、三个高度之一（一个目标集合，旧代码依次试），横向 ±10 cm 摆 `swings` 次，收臂。
- **point**：从手那一侧的"肩"（身前 0.09、侧 0.18、高 1.05 m）到目标的射线上，离肩 0.30–0.52 m 四个位置组成一个目标集合，合拢的手指沿射线；结果：手指轴离目标 8° 以内。目标不在前方时 `PointAtPolicy` 先转身（任务层）。技能的两条路径都调它；旧的原语串（policy_041 → 101 → 038）退役。
- **shake**：拿着东西的手沿合爪轴的水平方向摆 `cycles` 次、幅度 `amplitude`，保持倾角，回到起点；结果：合爪宽度收窄不超过 8 mm（物体没在手里转）。

## 谁在用

- **explore_furniture**：站着看不全的层（下层被上一层的板挡住），能蹲多低蹲多低再看一遍，然后站回原来的高度（crouch、stand 技能）。蹲不下去，探索失败。
- **x6_gd 路线**：bend → explore_furniture → straighten。
- **开门、关门、inspect** 不再先收臂（11-16 去掉了路线里的 policy_003）：它们是 `run_skill` 技能，导航第一段把手臂收到行驶姿态（收起或下垂），停车点上的计划从手臂当时的样子出发。
- **地上的物体**：pick 自己蹲。规划链里有躯干和腰，停车点由 pick 自己选；floor_top 路线不再先 approach_target、prepare_floor_reach（policy_065、policy_042 退役）。

## 已知问题

- **下蹲最低到 -0.466 左右**（11-16 检查，T02 / T20 / T30 都是这个值）：左臂收起时手在 0.8 m 左右、整条手臂在底盘柱子以内，躯干再往下左手就压进底盘（顶面 0.27 m）。旧代码降到 -0.54，是因为仿真里机器人自碰撞是关的，左手穿过去了。这个高度下三个柜子的三层都还看得到；要蹲得更低得先把左臂挪开，没做。crouch 技能的"降到最低"路径保证的 `torso_lowered`（下限 3 cm 以内）因此做不到，v6 路线里没有直接调它的。
- **建段和复核的判据不一样**：关节直线建段时按 0.05 rad 抽样查碰撞，`run` 执行前的 `holds` 逐个路点查。T05 pen_in_6 开门最后的收臂（开门计划自己的，不是这个技能）在第 106 / 249 个路点手指压进 2 mm，建段没查出来，执行前被拒，重做又规划不出来。所有关节直线段都有这个问题，改法是建段也查交出的路点，会改所有收臂段，单独做。
- **开关门不再先收臂以后**，关门的停车点和做法跟着开门结束时手臂的样子变：T18 at_island 换成原地右手握把手，抓上以后 `door_held` 锚点重做最后的收臂规划失败（任务仍判成功）。
