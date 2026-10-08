# Policy 物理验证记录（2026-10-01 至 2026-10-02）

> 本文是 `policy_001`–`policy_064` 单步验证的历史记录。动词 SkillNode 库新增的 policy（`policy_065` 起）通过 Skill Contract 场景验证，前后条件在 GT 状态上测量，结果见 [skill_library/verification/STATUS.md](../skill_library/verification/STATUS.md)。

本轮从 **32/60 已验证、28/60 待验证** 开始。用 Isaac Sim 的刚体、关节和夹爪实际读数判定动作，不把 Python 类可调用或运动规划成功等同于物理动作成功。当前为 **54/60 在至少一个明确场景通过单步物理验证、6/60 仍待验证**。这里的 `verified` 只说明列出的场景和动作通过，不是跨物品或多种初态的可靠性保证。权威状态见 [POLICY_CATALOG.md](POLICY_CATALOG.md) 与 [catalog.json](../zeno_skills/policies/catalog.json)。

## 本轮通过的 20 项

| 实测动作 | 新通过的 policy | 本地运行记录 |
|---|---|---|
| 空手移动、持物抬高、负载后退；底盘目标、物体底部高度和后退距离均实测 | `empty_navigate`, `carry_height_adjust`, `back_off_with_load` | `runs/verify_callable_toy_chain/result.json` |
| 右臂关节移动与 TCP 平移；TCP 位置误差 3.9 mm | `right_joint_move`, `right_tcp_move` | `runs/verify_callable_arm_v4/result.json` |
| 微波炉按钮开门、关门、启动；铰链读回和加热状态通过 | `open_powered`, `close_powered`, `microwave_start` | `runs/verify_callable_microwave/result.json` |
| 托盘右手沿抓抬升 2.93 cm；随后搬运滑脱，所以仅抓取本身通过 | `pick_rect_rim` | `runs/verify_callable_rect_tray_v3/result.json` |
| 苹果落在桌面且支撑关系为真，目标 XY 误差 1.39 cm | `place_surface` | `runs/verify_callable_surface_apple/result.json` |
| 苹果在底盘停止前释放，最终仍在桌面支撑上 | `place_while_moving` | `runs/verify_callable_place_while_moving_apple_v2/result.json` |
| 苹果放入果篮，径向偏移 7.5 cm，小于容器有效半径 14.3 cm | `place_container` | `runs/verify_callable_container_apple/result.json` |
| 书本后推 5.68 cm；顶部接触拖动 5.7 cm | `push_from_behind`, `top_drag` | `runs/verify_callable_push_drag/result.json`, `runs/verify_callable_top_drag_v4/result.json` |
| 边缘持书后放回标注桌面，支撑关系为真，倾角 1.1° | `place_edge` | `runs/verify_callable_place_edge/result.json` |
| 手动柜门开到 −1.379 rad，关回 −0.011 rad | `open_handle`, `close_handle` | `runs/verify_callable_handle_cabinet/result.json` |
| 抽屉把手带动关节从 0 到 −0.130 m，满足该抽屉开放判定 | `open_prismatic_drawer` | `runs/verify_callable_drawer/result.json` |
| 抓持积木先物理倾斜 29.1°，再扶正至 0.95° | `upright_object` | `runs/verify_callable_upright/result.json` |
| 杯子从柜顶抓起，经开启的炉门放入炉腔；腔体支撑关系为真、倾角 0° | `place_microwave` | `runs/verify_callable_microwave_cycle_cup/result.json` |

`top_drag` 的手指目标高度和滑移补偿已按实测调整。验证脚本新增独立 route、启动状态检查和物理倾斜夹具。`runs/` 按仓库规则不纳入 Git；可用 [微波炉测试场景定义](../tests/fixtures/policy_microwave_cup.json) 和 [地面书本测试场景定义](../tests/fixtures/policy_floor_book.json) 重建对应场景。

## 本轮进一步修复并通过的 2 项

| policy | 修复与实测证据 | 适用边界 |
|---|---|---|
| `pick_cup_handle` | 给 `breakfast_mug` 标注并重建实际杯柄碰撞体，杯柄外侧 TCP 避开杯壁。在原始 `breakfast_setup` 场景夹持后抬升 **2.26 cm**，两侧手指分别保持 **1.22 cm / 1.03 cm** 开度；`runs/final_mug_handle/result.json`。 | 仅该杯型完成物理验证；直接 Python 初始化须用 `make_rig(..., handle_objects=("mug",))`。`breakfast_cup` 没有杯柄。 |
| `pick_from_cavity` | 保存同一 rig 放置时的实测杯子、TCP 和底盘位姿，回到可达站位反向接近。`open.v1/powered → pick.v1/round_rim → place.v1/microwave → pick.v1/cavity` 四步 contract 顺序通过；回取杯子抬升 **7.42 cm**，退出炉口 **4.7 cm**；`runs/final_contract_microwave/result.json`。 | 限于同一 rig 刚放入的杯子；预置碗的通用腔内抓取未通过。上方中间位曾有 **18.2 cm** TCP 瞬态偏差，最终接触误差 **7.5 mm**；该路线还需要更稳健的轨迹控制。 |

微波炉的四步计划既检查每个 policy 的物理结果，也检查 contract 的关节、抓持、支撑和再次抬升后置条件。`ContractRunner` 只执行**显式指定**的路线；选路线、重规划和完整领域谓词属于后续研究扩展。

## 仍未通过的 6 项

| policy | 最新物理试验与阻碍 |
|---|---|
| `pick_floor_corner` | 旧地面书本接触误差 **6.8 cm**，薄 `notebook` 降至 **1.42 cm**，但闭爪后抬升仍为 **0 m**；`runs/repair_floor_notebook_v1/result.json`。先单独降低躯干的试验在关节路径上碰撞；`runs/repair_floor_notebook_v2/result.json`。需要物体边缘翻起或更合适的地面夹爪接触控制。**已退役**：几何上平行夹爪在平地上无法夹住平放物体（见 [PHYSICS_AUDIT.md](PHYSICS_AUDIT.md)），SkillNode 不再使用。 |
| `bimanual_flat_pick` | `book_red` 可找到共享站位；同步接触后书本偏移 **3.4 cm**，双手闭合到零、抬升 **0 m**；`runs/repair_bimanual_book_v7/result.json`。接触点再内移 **3.5 cm** 后共享站位因碰撞不可达（v8）。旧试验短时抬起 **3.7 cm**，随后左手在携带时滑脱。 |
| `bimanual_box_lift` | `serving_tray` 和地面轻篮的双臂接触搜索在 **45 s** 上限内均未找到无碰撞共享站位；`runs/repair_bimanual_box_v3/result.json`、`runs/repair_bimanual_basket_v3/result.json`。搜索现在有明确时间上限，不会无限阻塞任务。 |
| `bimanual_carry` | 曾在书本双手短时抬起后发生左手滑脱；`runs/bimanual_carry_new_policy/result.json`。当前没有稳定的双手持物前置状态，不能称为已验证的携带。 |
| `handover_right_to_left` | 积木太窄。碗的右手杯沿抓取抬升 **6.14 cm**，但 **15 个**独立左手预抓候选均超出该姿态下左臂的关节可达性，排除碰撞检测后仍不可达；反向夹爪姿态的 **30 个**候选也不可达；`runs/repair_handover_bowl_v3/result.json`、`runs/repair_handover_bowl_v5/result.json`。 |
| `open_door_while_left_holds` | 需要稳定左手持物；换手尚未通过，因此没有合法前置状态来验证左手持物开门。 |

这 6 项保留独立 OOP 入口，但状态为 `callable`，上层图规划不应把它们当作已验证的 building block。`bimanual_carry` 和 `open_door_while_left_holds` 的未验证属于前置动作链缺口，不能靠调用其类本身消除。其余 **54 项**也只对记录的代表性场景作出成功声明；新物品、新站位仍应重新物理验证。

## 复现

```bash
cd zeno-house
export OMNI_KIT_ACCEPT_EULA=YES
export ISAACLAB_PYTHON=/home/all/miniforge3/envs/isaaclab/bin/python
$ISAACLAB_PYTHON tools/build_tasks.py --spec tests/fixtures/policy_microwave_cup.json --out runs/verify_microwave_fixture/task --seed 0 --no-reach-check
$ISAACLAB_PYTHON tools/settle_scene.py runs/verify_microwave_fixture/task/scene.usd --seconds 2
$ISAACLAB_PYTHON tools/annotate_scene.py runs/verify_microwave_fixture/task/scene.usd runs/verify_microwave_fixture/task/annotation.json
$ISAACLAB_PYTHON tools/run_skills.py --scene runs/verify_microwave_fixture/task/scene.usd --ann runs/verify_microwave_fixture/task/annotation.json --out runs/microwave_recheck --no-video --plan 'open_powered kitchen_microwave' 'pick_round_rim cup' 'place_microwave cup'
```

四步 contract 复现：

```bash
$ISAACLAB_PYTHON tools/run_contracts.py --scene runs/verify_microwave_fixture/task/scene.usd --ann runs/verify_microwave_fixture/task/annotation.json --plan tests/fixtures/contract_microwave_cycle.json --out runs/contract_microwave_recheck
```

杯柄原始场景复现：

```bash
$ISAACLAB_PYTHON tools/run_skills.py --scene tasks/breakfast_setup/scene.usd --ann tasks/breakfast_setup/annotation.json --out runs/mug_handle_recheck --no-video --plan "pick_cup_handle mug"
```

以上 smoke 使用 `--no-video`，判定依据是结果 JSON 的动作成功标记、物体位置、接触和关节读数。已有任务视频不等同于本轮逐项验证视频。
