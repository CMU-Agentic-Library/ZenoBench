# open（拉开门或抽屉，2026-11-10 起走运动分层）

用把手拉开一扇铰链门（柜门、冰箱门）或一个抽屉：**只握一次**，握住以后手臂不动，底盘跟着门（抽屉）走，开到位松手、退开、收臂。

还走旧代码（`skills._move_with_retry`）的：左手拿着东西时（腰的上限要等 `Spec.joints`，`../MOTION_ARCHITECTURE.md` 9.3 第 5 步）、微波炉（第 8 步）。close 全部还是旧代码（推门关要等第 7 步的 `pushed_part` 耦合）。

入口：`skills.open_articulated` → `motion_skills.run_skill(SKILLS["open"])` → `skill_jobs/door.py` 的 `open_job` + `skill_plans/door.py` 的 `plan_door`。合约路径 `refrigerator`、`drawer`、`hinged_door` 都是 tuck（policy_003）+ policy_022；以前 `hinged_door` / `drawer` 先用 policy_046 抓一次、policy_049 / 050 里再抓一次，这四个策略（046、047、049、050）已退役（`skill_library/check.py` 的 `RETIRED_POLICIES`）。

已经在目标开度（铰链差 `DONE_REV` 0.02 rad、抽屉差 `DONE_PRIS` 6 mm 以内）就什么都不做。

## 步骤

**选握法和停车点**（`open_job` → `park_search.find_park`）

1. **握法是目标集合**（`_ways`，沿用旧代码的顺序）：侧钩（一指插到门板和把手之间，拉的时候靠手指的法向力）不倾斜、倾斜 10°、20°；抽屉和标了 `flip_ok` 的把手两端都能钩；导入资产（标了 `pre_open`）的把手再加一个正面捏。每种握法一个目标，排名每靠后一位代价加 `VARIANT_COST`（5 cm）。以前是"一种握法调一次 `find_park`"的循环。
2. 每个目标给出：手要够到的点（把手前 `TCP_BACKOFF` 12 cm、把手），排序用的中继位姿（把手前那一点）。握法写在**部件坐标系**里（`T_part_tcp`），门在哪个开度，把手位姿就从那里推出来（`Aim(frame=part_pose)`）。
3. **排序**只用停车点搜索的通用排序（关节余量、可操作度、候选代价）。旧代码在可行的停车点里挑沿把手运动方向拉 20 N 时关节力矩最小的（`planner.torque_ratio`；腕关节只有 3 N·m），这里去掉了。
4. **按顺序做整份计划**（`plan_door`），第一个做得出来的胜出：

| # | 段 | 做法 | 查碰撞 |
|---|---|---|---|
| 1 | `door_arrive` | 锚点：底盘、门的开度 | — |
| 2 | `door_open_hand` | 张到 `pre_open` | — |
| 3 | `door_reach` | 到把手前 12 cm：TCP 直线，不通就走到 `decide_ik` 定的解 | 查，手指在模型里 |
| 4 | `door_grasp` | 沿接近方向直线到把手（4 mm 一个路点） | 查；手指可以碰这扇门（`Spec.touch`），手臂其余部分对门照查 |
| 5 | `door_close_hand` | 合爪；计划里手握着门（`Held(kind="part")`） | — |
| 6 | `door_held` | 锚点：握法按实测关节角量 | — |
| 7 | `door_ride` | 任务段：`Script(hinge / slider, 现在的开度 → 目标 + 0.02, carry="base")`，底盘和门刚性地一起动（`ride_base`） | 每 0.1 rad（抽屉 3 cm）一个点：门挪到那个开度，底盘本体对静态世界和门（`BaseModel.clear`），整机（手指可碰门） |
| 8 | `door_moved` | 锚点：门实际开到哪 | — |
| 9 | `door_release` | 张到 `pre_open`，松开 | 手指可碰门 |
| 10 | `door_leave` | 沿接近方向反着退，量到离开接触（`contact_extent`，`near_world`，最多 6 cm） | 接触段，不查 |
| 11 | `tuck` | 收起或下垂，先试收起 | 查 |
| 12 | `door_settle` | 等 60 帧 | — |

**执行**（`run.run`）

- 每段之前复核（`holds`）；三个锚点处重做剩下的整份，还成立的段原样留下。门被碰动、底盘停偏，伸入段终点比构造时多偏 1 mm / 0.01 rad 以上（`DOOR_TOL`）就从那里重做。
- **合爪后判握住没有**（hook）：两指都被把手挡住（宽度和把手厚度对得上，和旧代码同一个判据）。没握住：张到 `pre_open`、退出接触，技能失败。握住了就登记（`rig._handle_grasp`），之后 `Rig.snapshot` 读出来的状态里手握着门。
- **骑门**（`Rig.ride`）：每个物理步按指令开度对 `ride_base` 求值、把底盘放过去；指令开度以不超过 `rate` 的速度追"实测开度 + `lead`"（侧钩 0.03 rad、0.25 /s；正面捏只靠摩擦，0.01、0.12）。门到"目标 − 0.02"算完成。门卡住、突然掉到指令后面两个 `lead`（滑脱）或超时就停下，技能失败：张开、退出接触（失败出口）。
- 松手后清掉登记。
- 结果：等 60 帧后读开度。铰链门差 0.10 rad 以内、抽屉开到 60% 以上算成功（同旧代码）。

## 和旧代码的差别

- 只握一次（旧 `hinged_door` 路径握两次，v6 基线柜门 open 8 次失败里 6 次出在这两次抓上）。
- 去把手前不再先到"把手前上方 8 cm"那个手写的点：自由段由规划器决定。
- 退开不再是"退 14 / 8 / 4 cm 哪个能走用哪个，再往上抬 12 cm"：沿接近方向量到离开接触为止。
- 骑门的整段在搜索时就按 0.1 rad 一个点查过整机和底盘（旧的 `_ride_check` 只查 7 个点的底盘占地和手臂）。
- 失败后不再换个停车点重来一次（旧 `_move_with_retry_impl`）。
- 不再按力矩比挑停车点。仿真里要是出现"门拉不动"，先看是不是停车点让腕关节吃力。
- 握着门时只有手指可以碰这扇门（旧的 `hand_touches_part` 是整只手对整个世界都不查）。侧钩时手掌如果也贴着把手，会被当成碰撞：第一次跑仿真要看这一点。

**还没跑过仿真。**
