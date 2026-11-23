# Handoff 2026-10-30：http planner 跑 benchmark/v3 的失败分析与修改

## 这次 run

- 时间：2026-10-29 22:39 – 10-30 00:09（容器时间，UTC），env-service 容器 `zb-env-service`，
  镜像 `zenobench:isaaclab2.3-curobo07`，代码为 main `8df1ef2`（10-29 16:52 EDT 启动）。
- planner：远程 http planner（Graph_manager），本地没有 planner 端日志，下面的判断只来自
  env 端的 `result.json` / `calls.jsonl`，并对照 scripted 路线 `benchmark/runs/v3_sticky_gt_1029b`。
- profile：`sticky_snap/gt`，`task_status` 打开（planner 每步都能看到每条 goal 原句及真假），
  `gt_objects` 打开（能看到物体坐标）。
- catalog：`benchmark/v3/tasks.json`，41 个任务，**21 成功 / 20 失败**。
  20:46 那轮零散的 T16 / T17 / T18 不算在内。
- 原始记录：`runs/env_service/<task>/<exp_id>/`；失败视频已按归因复制到
  `runs/v3_http_1029_failures/`（文件名前缀 `planner__` / `policy__` / `mixed__`，附 `index.tsv`）。

## 失败归因（推测）

最终：**planner 12，policy 6，两边都有 2**。

### planner：contract 选错、参数错、不会变通或不知道该停（12）

| 任务 | 推测原因 |
|---|---|
| P05、P08、T17 | 0 次调用就 `planner_done`，contract 都存在；T17 在 20:46 那轮 9 步成功过，像是 planner 端不稳定或崩溃 |
| P01 | wave 做了，没调 `nod` |
| P02 | `explore_room` 用了 4 个不存在的房间名（应为 `living_room_0_0`）；`identify` / `measure` / `count` 都没调 |
| P13 | 第一次 `heat` 因距离被拒后放弃 heat；`place` 用了 `kitchen_microwave`（应为 `kitchen_microwave/inside_floor`）；没有 close / press / stop |
| T07 | 微波炉坏了的变体：把燕麦放上灶眼，另外搬了锅，但一次 `heat` 都没调。heat 描述写着 "in a pot on the stove burner"，有误导（已改，见下） |
| P22 | 第 2 次调用后两条 goal 已全部满足（燕麦被动冷却到 8 °C，门因为第一次 `open` 被拒而一直关着）；planner 继续开门取出燕麦，最后门开着 |
| P15 | 把 "group" 理解成叠放（`stack`），没把 `wooden_block_b` 放上灶台；`arrange` / `sort` 没用 |
| P19 | 没用 `uncover` / `dip`；`lower(height_m=0.1)` 把世界高度当相对位移 → no IK |
| T13 | 碗和杯子放在离勺子 ~1.9 m 处；没传 `hint_xy`，也没用 `arrange`（scripted 靠写死坐标通过） |
| T15 | `expose` → `flip` 后三条 goal 全部成立，planner 又 pick / place，把书弄到地上。不是 flip 判定问题 |

### policy：contract 对了但执行失败（6）

| 任务 | 推测原因 |
|---|---|
| T01 | 书的 edge grasp 后 `holding` 判为 false（两指 0.0007 / 0.0373），sticky 仍在手上，place / regrasp 都被前置条件拒绝。`796e514`（两指判断抓握）可能相关 |
| T08 | `wipe` 反复 "no base pose reaches the strip"，清空 island 后仍失败 |
| P03 | `roll` 两次 no base pose（scripted 能成功，基座搜索不稳定）；`pull` "object did not move" |
| P04 | `tip` 成功后无法 `upright`；scripted 也在 `upright` 报 NO_PATH，属于能力缺口 |
| P17 | `pour` 两次 "0/3 items reached"，scripted 也失败 |
| P14 | restore 只回到原支撑面、没回原点位，swap 以错误位置为基准；已在 `a6b0357` 修复 |

### 两边都有（2）

| 任务 | 推测原因 |
|---|---|
| T04 | planner 先调 `place(mug → cup_counter_b)`（把杯子放进杯子），把 cup 碰到地上；最后正确的 place 到 `kitchen_cabinet_6/top` 时 mug 倒了（87°） |
| P18 | crouch 描述写 "for floor work"，planner 先调 `crouch(0)`；0 被当成"没传"走了最低路径，规划失败；planner 随即放弃。`pick` 本来会自己降躯干抓地面物体 |

### 观察

- planner 侧最常见：有对应 contract 不用而自己拼低层动作；名词写错；数值参数语义理解错；
  看不出任务已完成或还差哪一步（`task_status` 明明给了）。
- policy 侧集中在两类：基座位姿搜索失败（roll / wipe / approach / hover / brace）；
  抓握判定与 sticky 状态不一致（T01、P19、P22、T08）。
- 任务设计问题（未改）：P15 说明里的 group 不检查、"a block" 实际只认 `wooden_block_b`；
  P22 冷却是被动且很快的，"检查"和 `chill` 考不到；P19 说明写 "open pot" 但锅盖着。

## 这次的修改（`d34ffa0`，分支 `fix-grip-criteria-push-crash-restore-xy`，已推送）

1. **heat 描述（T07）**：不再说灶上必须用锅；食物自带的碗可直接放灶眼，锅只用于散装食物，不需要盖子。
   灶台路径的 note 和 alternative 关系同步修改。
2. **crouch bug（P18）**：路径条件从 `truthy` 改为新加的 `set`（参数是否给出），`crouch(0)` 不再跑到最低。
   0 是站直，此时后置条件 `not torso_raised` 会报 POSTCONDITION_FAILED。描述写明可用范围
   [-0.54, -0.03] m，并说明捡地面物体不需要先 crouch。
3. **`near` 参数**（`zeno_skills/skill_runtime.py: resolve_near`，在选执行路径之前换算）：
   - `place(..., near=X)`：X 的 xy 作为 `hint_xy`，`free_spots` 选离它最近的空位；与 `hint_xy` 同时给出返回 `INPUT_UNKNOWN`。
   - `lift` / `lower(..., height_m=h, near=X)`：`height_m` 变为 X 顶面以上 h，内部换算成世界高度
     （物体取包围盒顶，台面取台面高度，其他取代表点）。
   - 描述里补了"桌面约 0.9 m"的参照。
4. 重新生成 contract / skill 库导出（`tools/build_skill_library.py --check` 通过），
   `env_service/README.md` 错误表补充互斥参数，新增 `tests/test_skill_inputs.py`（6 个测试）；
   原有 121 个测试通过。

### 仿真验证（scripted，`sticky_snap/gt`，`benchmark/runs/near_check/`）

验证路线写在 `/data/zenobench/scratch/near_check/tasks.json`（复制的任务文件，原文件未改）。

- **P18 `verify_crouch_near`**：成功。`crouch(-0.3)` 走 `to_height` 到位 → `stand` → navigate → `pick`（`floor_top`）
  → `lift(0.15, near=island)` 换算 1.01 m 成立 → `lower(0.06, near=island)` 换算 0.92 m 成立 → `place(near=mug)` 离 mug ~12 cm。
- **T13 `verify_place_near`（`bowl_on_cabinet`）**：成功。cup 离勺子 ~0.18 m，bowl ~0.21 m，最远一对 0.39 m（要求 ≤ 0.5）。
- 未在仿真覆盖：`crouch(0)` 的行为（只有单元测试）。没开录像。

## 待办

- Graph_manager 的 `graph_manager/vendor/zenobench/skills/` 是 skill 描述副本，需同步后 planner 才能看到新参数和描述。
- pick 定义里的 fallback 关系 "物体在地上 / 低层架子 → crouch"（`skill_library/definitions.py` 约 499 行）
  与 pick 的实际行为相反，建议删除或改写。
- env-service 容器需用新代码重启后再跑一轮 http planner。
- 任务说明的歧义（P15、P19）和 P22 的被动冷却可考虑修。
