# 交接：support 碰撞板抽查、explore 拆分、碰撞体调试录像（2026-10-24）

本文记录 2026-10-24 一次会话做过的所有事情、现在的状态和没解决的问题，供下一个会话接手。**所有改动都没有提交**，叠在工作区里已有的未提交改动上（主要是 2026-10-23 那次会话的 support 碰撞板改动）。

## 0. 背景：2026-10-23 的 support 碰撞板改动

那次会话是 CLI 会话 `056186d1-9ca7-4c35-ad27-c72a0f7bda7a`（transcript 在 `~/.claude/projects/-home-muqingj-Projects-ZenoBench/056186d1-….jsonl`），做了这些事：

- **新的 support 定义**：Infinigen 静态家具原来的 215 个 `surface_N` 是从碰撞网格聚类出来的，和渲染出来的板差 1–5 cm。现在改成手工列出的支撑层 [annotations/support_layers.json](../annotations/support_layers.json)，覆盖 26 件家具，命名为 `shelf_0`、`shelf_1`…、`top`。
- **铺碰撞板**：[tools/fit_support_repairs.py](../tools/fit_support_repairs.py) 在每一层渲染出来的板面上铺一块 2 cm 厚、渲染不可见的碰撞板（`/World/SupportRepairs/<家具>__<层>`），并删掉板上方空间里的非竖直碰撞面。
- **标注改从碰撞板读**：[tools/annotate_scene.py](../tools/annotate_scene.py) 改成直接从这些板读 support；`house_static.json` 不再存 supports。
- **改名和重新生成**：39 个文件里的旧名字按高度换成了新名字，所有任务场景都重新 settle 并重新标注。
- **备份**：改动前的场景和标注备份在 `/tmp/claude-1000/-home-muqingj-Projects-ZenoBench/056186d1-…/scratchpad/backup/`（在 /tmp 里，可能被清掉）。注意这份备份里的 `sim/zeno_house.usd` 已经带了新碰撞板，不是真正的改动前版本。真正的改动前基线是 git HEAD。

## 1. 抽查涉及台面的 benchmark 任务

- **跑了哪些**：v3 里起点或终点在这 26 件家具上的任务，共 9 个：T01、T05、T06、T11、T12、T13、T14、T19、T20。每条评分路线跑一次，seed 10，一共 20 个回合。
- **任务清单**：`/data/zenobench/support_layers/spotcheck/batch.json`。
- **第一轮**：只有 8/20 通过（结果在 `spotcheck/runs/`）。
- **HEAD 对照**：在 HEAD 的 worktree `/data/zenobench/support_layers/baseline_head` 上重跑失败的 12 个，**12/12 全部通过**（`spotcheck/baseline_runs/`）。说明失败全部来自未提交的改动。

### 1.1 根因一：墙的碰撞体被弄坏了（已修）

- **问题出在哪**：`fit_support_repairs.py` 最后有个循环，会清空**所有**不在 support 表里的碰撞网格的面列表。3 面房间外墙（`bedroom_0_1`、`living_room_0_0`、`living_room_0_1` 的 `*_exterior_collision_openroof_wideopen/World/mesh`）也被清了。
- **后果**：这 3 面墙带着 `tools/cut_doorway.py` 开门洞时写的覆盖层，点坐标是裁剪过的。清掉面列表后，裁剪过的点配上原始网格的面索引，碰撞几何变成一堆错乱的三角形。机器人穿过门洞时会被撞倒，第一人称画面是歪的。往 `bookcase_2` 和书房方向走的路线全部因此失败。
- **修复**：
  - **脚本**：现在只重置 `annotations/furniture_names.json` 里列出的家具的碰撞网格（[fit_support_repairs.py:222](../tools/fit_support_repairs.py)）。
  - **数据**：把这 3 个网格的 `faceVertexCounts` 和 `faceVertexIndices` 从 HEAD 拷回 `sim/zeno_house.usd`。点数和 HEAD 完全一致。
  - **备份**：修复前 `/data/zenobench/support_layers/zeno_house.before_doorway_restore.usd`，修复后 `zeno_house.after_restore.usd`。
  - **验证**：用修好的脚本再跑一遍，房屋文件逐个 spec 对比没有任何变化，说明脚本是幂等的，也不再动墙。
- **没做**：墙坏掉的那段时间里，任务场景是在这种状态下 settle 的，之后**没有重新 settle**。场景层和改动前只差物体位姿的微小变化，重跑的结果看起来没有受影响。

### 1.2 修墙之后的重跑（`spotcheck/rerun_runs/`）

- **修好的**：T01、T11 两条、T13 两条通过了。
- **之后通过的**：T12 两条和 T19 卡在 `explore living_room` 覆盖率 0.67。原因是新 support 让客厅的 explore 目标从 7 个变成 9 个（多了 large_shelf_2 的三层内隔板）。这个通过第 2 节的 explore 拆分解决了。
- **还没解决的 4 个**（HEAD 上都能过）：
  1. **T05 `alternative_pencil`**：铅笔放到 `desk_1/top` 后，place 报告成功，但铅笔在桌面上滑了约 10 cm 到桌沿（x = -1.409），最后掉到地上。新板的 z 是 0.700，HEAD 是 0.694；support_layers 里给的高度是 0.686，被就近对齐抬高了 1.4 cm。要确认 0.700 到底是渲染出来的桌面，还是桌沿。
     - **水平相机对照**（`/data/zenobench/support_layers/level_cam/`，HEAD 在 `baseline_head`，相机代码一样）：这次 HEAD 通过，当前版本失败，和之前一致。对比视频 `T05_compare_place.mp4`（只截 place 段）和 `T05_compare_full.mp4`（整段）：上面是 HEAD，下面是当前版本；左边跟拍，右边水平。
       - **台面高度没问题**：渲染出来的桌面前沿上边缘约在 0.698。新板 0.700 只高 2 mm，HEAD 的 0.694 低了 4 mm。铅笔倒平后底边正好贴着桌面，没有悬空也没有陷进去。
       - **两个版本的铅笔都在滚**：两边都是斜着夹（倾斜约 40°），笔尖先碰到桌面，笔身中心在桌面以上约 4 cm 处松手，倒平后往 -x 桌沿（机器人这一侧）匀速滚。截图里笔身红黄两色交替，说明在绕长轴转。HEAD 约 1.5–2.6 cm/s，回合结束时还在动，中心离桌沿约 5 cm；当前版本约 4 cm/s，松手后约 3 s 从桌沿滚下去。
       - **判断**：铅笔碰撞体近似圆柱，没有滚动阻力，倒平时又带着转动，所以会一直滚。HEAD 能过是因为回合先结束了，不是碰撞板造成的回归。当前版本的放置点离真实桌沿近了 1.5 cm，滚得也更快一点，就越过了门槛。
  2. **T05 `hard_search_pencil`**：search 在 `dining_table_2` 没看到铅笔。HEAD 是从旧的伪家具 "SupportRepair" 那个视角看到的，现在换了站位，桌上的麦片盒可能挡住了铅笔 (3.70, 6.30)。
  3. **T14 `nominal` 和 `fallback_expose`**：书放到 `bookcase_2/top` 上掉了下去。support 中心移动了约 1.5 cm，停车位从 (0.772, -1.082, 60°) 变成 (0.664, -1.022, 45°)。在新位置，`flat_pre` 动作中手臂碰到东西（`joint_from_contact`，q_err 0.63）。
     - **水平相机对照（只跑了 `nominal`）**：结果和之前一样，HEAD 通过，当前版本失败，当前版本的事件和上次一模一样。对比视频 `level_cam/T14_compare_place.mp4`，两边都从 place 开始对齐。
       - **板子高度没问题**：当前版本的 0.709 和渲染出来的书架顶面差不到 1 mm，HEAD 的 0.706 低了约 3 mm。
       - **当前版本怎么失败的**：
         - **停车位和手臂构型**：find_park 选的停车位是 45°，配的 IK 解是另一组构型（第 4 关节约 3.11），书被举在机器人头顶上方搬过去。到了停车位，规划器判定起始构型已经在碰撞里，于是走了 `joint_from_contact`，不做碰撞检查，直接在关节空间里插值到 `flat_pre`。
         - **书被压到侧面**：水平视角里，书被甩到书架顶面以下，压在书架前侧面上（第 2400–2449 帧），卡住后在夹爪里转了一下。
         - **后果**：之后的 `flat_over` 因为书往下垂了，被抬高了 21 cm。书在顶面上方约 1.5 cm 处松开，夹爪后撤时把书带翻，掉到书架旁边的地上。
         - **没有调平**：HEAD 到位后先 `flat_level`（下垂 10.6°）再去 `flat_pre`，当前版本没有 `flat_level` 这一步。
       - **HEAD 本身也不太稳**：回合结束时书的一端搭在夹爪上，底面比顶面高约 4.8 cm（`final_state` 里 `on` 是 None），只是 `on()` 判定放过了。
       - **根因（已查清）**：support 的改动只是导火索，真正的问题是 place_flat 这条链上有好几个不稳的选择，HEAD 每一个都碰巧选对了。证据：仿真日志、离线 IK 复现，以及 `level_cam/park_probe.py`（拦截 find_park，打印候选；`SQUARE_FIX=1` 把 square 的符号翻过来）。
         1. **抓取朝向变了**：`desk_1/top` 的边往外挪了 1 cm、高了 6 mm，expose/pick 选的停车位跟着变了（pick 时 -270° → -285°）。抓到手里的书相对机器人多转了 15–18°；运到书架前时，书相对机器人的朝向是 42°，HEAD 是 5°。
         2. **抬手时 IK 跳到了另一组解**：place_flat 里 `_goto_park` → `navigate` → `_carry_pose`，不管书是不是已经举高了，都会再往上抬至少 6 cm。这时手臂已经到了够不着的边缘（躯干在上限，腰快到上限），直线路径走不通，于是退回 `ik_global`。`ik_global` 返回的是固定随机种子里第一个不碰撞的解，不看离当前姿态有多远。HEAD 碰巧用第 1 个随机种子拿到一个只差 0.17 rad 的解；当前版本拿到的是差 2.85 rad 的那组：躯干降到最低，第 2 关节 3.11 rad。离线跑 `ArmKin` 可以精确复现这两个解。
         3. **停车位检查用错了姿态**：find_park 检查的 travel_q 是抬手**之前**的姿态，不是机器人到达时实际的姿态。
         4. **`square` 打分符号反了**（[skills.py](../zeno_skills/skills.py) `place_flat` 里的 `def square`）：它返回 `-abs(yaw - face)`，而 find_park 是按升序取第一个的，所以选到的是**最歪**的停车位，和注释"要正对书架边"的意思正好相反。HEAD 的候选是 60/75/90/75/90°，选了 60°；当前版本的候选里多出一个 45°，就选了 45°。
         5. **跳过碰撞检查把书撞进书架**：在 45° 停车位上，翻转后的姿态被判成已经在碰撞里，走了 `joint_from_contact`，不做碰撞检查直接插值，书被扫进了书架前侧面。
         6. **只翻符号也不够**：`SQUARE_FIX=1` 选了 90°，`flat_pre` 很顺利，书也放平了，但 `flat_push` 没有 IK 解，书还悬在边沿外面，还是失败。原因是 find_park 只检查了 legs 和 retreat 两段，没把 push 这一段的目标算进去。
       - **相关的疑点（没验证）**：开门停车位的 score 对已经失败过的停车位返回 `-1e9`，升序排序后反而会优先选它们，可能是同一类符号错误。
- **排除了物理材质的原因**：房屋的碰撞网格和碰撞板都没有绑定物理材质，用的都是场景默认值（摩擦 0.5/0.5），所以不是摩擦变了。
- **交接卡片**：已经给这 4 个问题建了会话卡片 `task_46c40a69`（"Fix T05/T14 regressions on new support slabs"），还没开始。

## 2. explore 拆成 explore_room 和 explore_furniture

用户的要求：room 级的 explore 看到家具就算成功；furniture 级的要看到所有能放东西的隔板；拆成两个不同的 skill，并把现有 route 都换成新的 explore。

### 2.1 设计

| | `explore_room`（原来的 `explore` 改名） | `explore_furniture`（新增） |
|---|---|---|
| 编号 | 沿用 skill_014、contract_022、policy_069 | 加在末尾：skill_071、contract_079、policy_116。已有编号都不变 |
| 输入 | `room`（`room_ref`） | `furniture`（新类型 `furniture_ref`：所有 support 的 `furniture` 字段等于这个名字的家具，柜子也算） |
| 成功条件 | 房间里 ≥ 75% 的**家具**被看到。一件家具只要有一层（0.3–1.6 m 高、面积 > 0.05、净空 ≥ 0.3）进入视野就算看到。不在 benchmark 里时，物体也算目标 | 这件家具的**每一层**都看到 |
| 后置条件 | `room_explored(room)` | 新谓词 `furniture_explored(furniture)`。两个都存在 `memory["explored"]` 里，用名字区分 |

`explore_furniture` 的策略（[perceive.py](../zeno_skills/policies/perceive.py) 里的 `ExploreFurniturePolicy`）：

- **怎么算看到一层**：看板面上方放东西的那块空间，取板面中心往上 10 cm 或净空的一半（`_layer_point`）。这个点要在头部相机视野里，而且不能被**这件家具自己的板**挡住（`_board_blocks`）。原有的可见性检测会忽略家具自身的板，不加这条，低层会被当成透过上面的板看到，相机高度以上的顶面也会被当成从下面看到。
- **站位和次数**：机器人已经在家具附近就先原地扫一遍，否则从最多 3 个站位里扫。和家具之间隔着墙的站位会跳过（用 `_segment_blocked` 检查）。
- **低层蹲下看**：站着看不到的层，会把躯干降到最低（相机从 1.32 m 降到约 0.78 m）再扫一遍，看完升回原高度。手里拿着东西时不蹲。躯干升回时，目标值会先夹在关节限位内：实测躯干位置可能略微超出上限，不夹会抛范围错误。
- **限制**：头部相机最高只有 1.32 m（躯干只能往下降），俯视角最多约 18°。

### 2.2 改了哪些地方

- **谓词、类型、运行时**：
  - [predicates.py](../zeno_skills/predicates.py)：新增 `furniture_ref` 和 `furniture_explored`，改了 `room_explored` 的说明文字。
  - [skill_runtime.py](../zeno_skills/skill_runtime.py)：给 `furniture_ref` 加了校验器。
- **策略和编号**：
  - [perceive.py](../zeno_skills/policies/perceive.py)：`ExploreRoomPolicy` 改成按家具计数，新增 `ExploreFurniturePolicy`。
  - [policies/__init__.py](../zeno_skills/policies/__init__.py)、[policies/catalog.json](../zeno_skills/policies/catalog.json)、[interface_ids.json](../zeno_skills/interface_ids.json)：注册 `explore_furniture`，编号 `policy_116`。
- **SkillNode 定义和检查**：
  - [definitions.py](../skill_library/definitions.py)：`explore` 改名为 `explore_room`，新增 `explore_furniture`，补了 relations、USE_WHEN、DISTINCT。
  - [check.py](../skill_library/check.py)：动词规则放宽为 `[a-z]+(_[a-z]+)?`；同义词组拆成 `explore_room…` 和 `explore_furniture…` 两组；加上 `furniture` 名词。
  - [build_skill_library.py](../tools/build_skill_library.py)：新增 `node_name()`。动词已经包含名词时不再重复，所以 SKILL.md 的 name 是 `explore-room` / `explore-furniture`，action 名是 `explore_room` / `explore_furniture`。房间那个的 action 字符串和以前一样是 `explore_room(room=…)`。
- **按动作名找动词的地方**：
  - [verify_summary.py](../tools/verify_summary.py)：改成优先匹配最长的动词。
  - [benchmark/metrics.py](../benchmark/metrics.py)：`PERCEPTION` 换成两个新动词，并修了按 `_` 拆动作名的逻辑。
- **Benchmark 的权限检查**：[observation.py](../benchmark/observation.py) 里，`furniture` 参数必须是已知的静态地点。
- **Route**：
  - [define_tasks.py](../benchmark/define_tasks.py)、[define_tasks_v3.py](../benchmark/define_tasks_v3.py)、[v3_candidates.py](../benchmark/v3_candidates.py) 里所有 `S("explore", …)` 换成 `explore_room`，然后重新生成。`benchmark/tasks.json` 改了 4 处，`v3/tasks.json` 改了 9 处，`v3/candidates/tasks.json` 改了 15 处，diff 里只有这些。
  - 路线**类型** `"kind": "explore"`（一种决策类别）保持不变。
  - config_hash 只覆盖场景叠加层，不包含 route 步骤，所以以前的验收 run 仍然有效。
- **skill_library 侧**：
  - `explore_living_room` 的 plan 用符号规划器重新生成，`tasks.json` 里对应的 route 步骤也跟着改了。
  - 跑单个任务时规划器会把 `plans/summary.json` 覆盖成只有一行，已经恢复，只改了那一行。
  - `verification/scenarios.json` 里改了名，并在 `k_perceive` 末尾加了 `explore_furniture large_shelf_2` 和 `tv_stand_2` 两步。
  - `verification/status.json` 和 `STATUS.md` 是**手动**更新的（66/71 个动词、98/121 条路径），因为 `runs/skillv2/verify` 不在这台机器上，没法重新生成。
- **测试和文档**：
  - [benchmark/tests/sim_permissions.py](../benchmark/tests/sim_permissions.py) 改成按家具数统计目标。
  - `test_library_v2.py` 里的动词总数改成 71。
  - README、benchmark/README、benchmark/v3/README、episode/README 里讲 explore 的地方和数量都更新了。
- **重新生成的导出文件**：`build_skill_library.py`、`export_interface_libraries.py`、`render_policy_catalog.py`、`render_contract_layers.py` 四个都已重新生成，`--check` 全部通过。

### 2.3 验证

- **单元测试**：145 个通过。剩下 1 个失败是 `test_env_recording`，原因是 venv 里没装 `imageio`，以前就有。
- **Isaac GT runner**（`/data/zenobench/support_layers/explore_check/verify3`）：
  - `k_perceive` 通过：`explore_room` 客厅覆盖率 0.86，`explore_furniture` 的 large_shelf_2 是 4/4 层（用了 2 个站位），tv_stand_2 是 2/2。
  - `explore_furniture` 在 bookcase_2、bookcase_3、cell_shelf_3、cell_shelf_4、large_shelf_6、desk_1 上都通过。书架和置物架都要蹲下再扫一遍才能看全。
  - cell_shelf_4 一开始失败过，因为站位选到了墙的另一侧，后来加了墙的判断才修好。
- **Benchmark profile**（`explore_check/runs`）：T12 两条、T19、P02 都通过。客厅覆盖率是 4/5 = 0.80，P02 所在的厨房场景是 7/9 = 0.78，**刚刚超过 0.75 的门槛**。
- **还没用上**：现有 route 都不需要逐层查看，所以没有 route 用到 `explore_furniture`。

## 3. 碰撞体调试录像（三个视角）

### 3.1 新增的选项（只影响调试，默认运行不受影响）

```bash
docker/run.sh '$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v3/tasks.json \
    --task T05_pen_or_pencil_to_desk --seed 10 --variant no_pen --route alternative_pencil \
    --views --show-colliders --out /data/zenobench/support_layers/rollouts/runs'
```

- **`--views`**：每个相机单独输出一个 MP4 到回合目录：`video_follow.mp4`（肩后跟拍）和 `video_level.mp4`（水平相机，见下）。视频边渲染边写到磁盘（`Episode(video_views=…)` → `rig.view_frames`），不会把整段视频放在内存里。（最早是 follow / wide / head 三个视角，后来改成了这两个。普通的 `--video` 仍然是 follow + wide。）
- **水平相机 `level`**（[runtime.py](../zeno_skills/runtime.py) 里的 `_level_view`）：相机高度等于支撑面顶部 z，水平看过台面，看的是机器人够得到的那一段。从和机器人朝向垂直、不在机器人身后、到台沿之间没有墙或家具挡着的那一侧拍，距离台沿 0.6 / 0.35 / 0.15 m，按顺序选第一个可用的。看哪块支撑面：`--level-support <支撑面或家具名>` 指定（家具名取最高一层）；不指定时取机器人正在 pick/place 的那块（`rig.focus_z` 附近、机器人前方），没有 pick/place 时保持上一块不变。
- **`--video-stride N`**：每 N 个物理步出一帧，默认 4，也就是 30 fps；12 对应 10 fps。物理仍然是 120 Hz。
- **`--show-colliders`**：碰撞板渲染成**品红**；有 support 层的 26 件家具的碰撞网格渲染成**青色**（[runtime.py](../zeno_skills/runtime.py) 里的 `show_colliders`）。闪烁表示碰撞面和渲染面重合；青色明显凸出，说明碰撞几何在看得见的表面外面。只改渲染材质，物理不变。开了之后头部相机图像里也会出现这些颜色，所以不能用于计分的 run。
- **为什么是不透明色**：用 `/data/zenobench/support_layers/collider_look_test.py` 实测过，在 RTX 实时渲染下，UsdPreviewSurface 的 opacity < 1 和 OmniGlass 都完全看不见，所以只能用不透明色。

### 3.2 顺带修的相机问题（会影响以后所有 `--video`）

- **wide 相机**：原来是固定在机器人后方 2.2 m、旁边 1.2 m、高 2.4 m 的位置，在室内经常卡在墙里。现在改成从 6 个候选位置（`WIDE`）里挑没有遮挡的那个，高度 3.0–3.6 m，在墙顶以上（房子没有屋顶），往下看工作区。
- **`_clear` 墙遮挡检测**：原来在约 1.5 m 的线段上只取 12 个点，点距约 12 cm，会跨过 4 cm 厚的墙，所以 follow 相机有时会停在墙后面，画面全灰。现在每 2 cm 采一个点，在 T01 餐桌那个位姿验证过。

### 3.3 跑出来的结果

- **已完成**：只跑完了 T01 两个回合，都通过，三视角拼接视频（`video_triptych.mp4`）已经发给用户。
  - `/data/zenobench/support_layers/rollouts/runs/T01_book_to_dining_table/s10_overhang_ready_nominal/`
  - `/data/zenobench/support_layers/rollouts/runs/T01_book_to_dining_table/s10_far_no_overhang_hard_search_expose/`
- **剩下的**：用户让停下来了。剩余 18 个回合的任务清单在 `rollouts/batch_rest.json`，第一项是已经跑完的 T01 hard，重跑前要删掉。
- **拼接脚本**：`/data/zenobench/support_layers/make_triptych.py`，要用 `$ISAACLAB_PYTHON` 运行，镜像里的系统 python3 没有 imageio。
- **抽帧看到的情况**：
  - **餐桌**：品红板和青色碰撞网格只差几毫米，中间有一片闪烁过渡，没有问题。
  - **cell_shelf_4**：各个格子里品红和青色互相交错，值得仔细看。
  - **bookcase_2**：三块板的位置对得上，两端和侧板外表面齐平。
  - **T01 曾经失败的那次**：书落在 x = 3.87，已经超出餐桌边缘（3.839），所以翻了。是放得太靠边，不是碰撞的问题。

### 3.4 为什么慢、怎么提速

- **为什么慢**：
  - **动作本身长**：一个回合在仿真里就要 100–160 秒，物理在 CPU 上以 120 Hz 计算，大致和真实时间一样快，所以不录视频也要 2–4 分钟。
  - **录视频慢一倍**：三个相机每 4 步渲染一次，技能调用部分的耗时大约翻倍（T01 nominal 从 115 秒变成 218 秒）。
  - **只能一个一个跑**：带三个相机时每个进程约占 11 GB 内存，机器只有 30 GB，两个一起跑会被 OOM 杀掉（已经发生过一次）。
- **可以提速的办法（还没做）**：
  - 渲染间隔改成每 8 步一次（15 fps），渲染开销大约减半。
  - 分辨率降到 640×360。
  - 去掉头部相机，内存可能因此降到能两个并行。
  - 只跑关心的回合。

## 4. 其他已知问题

- **`benchmark/v3/matrix.json` 已经过期（和这次改动无关）**：2026-10-23 改 support 名字时，T03、T04 等一些变体的场景叠加层变了，config_hash 也跟着变，但 matrix 没有重新生成。结果是 `conditions.py` 不会再把这些变体以前的验收 run 算进去。重新生成 matrix 后，可能还需要重跑这些变体的验收。这次我把重新生成出来的 matrix 恢复回原样了，没有改动它。
- **生成的结果文档还是旧数字**：`benchmark/RESULTS.md`、`benchmark/v3/RESULTS.md`、`benchmark/README.md` 的结果行仍然写着 64/70 之类的数字。它们来自 run 数据，要等下次重跑验收才会更新。
- **explore_room 在 P02 场景余量很小**：覆盖率 0.78，只比 0.75 的门槛高一点。
- **两套可见性规则不一致**：`look` 和 `explore_room` 仍然用原来的检测，不考虑家具自身的板挡视线；只有 `explore_furniture` 考虑了。
- **还没清理的东西**：
  - HEAD 对照 worktree `/data/zenobench/support_layers/baseline_head`。它被 git 记录为一个 worktree，不需要时用 `git worktree remove /data/zenobench/support_layers/baseline_head` 删除。
- **memory 更新**：`isaac-sim-no-wide-parallel` 里补了一条：带 `--views` 时用 `--jobs 1`。

## 5. 运行环境备忘

- **怎么跑 Isaac**：只能通过 docker，用 `docker/run.sh '<命令>'`，镜像是 `zenobench:isaaclab2.3`。要换 checkout 就设 `ZENO_REPO`。`/tmp` 没有挂载进容器，脚本要放在 `/data/zenobench` 下面。
- **主机上跑 Python**：主机自带的 Python 没有 numpy/pxr，要用 `/tmp/claude-1000/-home-muqingj-Projects-ZenoBench/056186d1-9ca7-4c35-ad27-c72a0f7bda7a/scratchpad/venv/bin/python`（装了 usd-core、numpy、trimesh、scipy、pytest）。它在 /tmp 里，可能被清掉，清掉后要重建。
- **常用检查命令**：
  - `python tools/build_skill_library.py --check`，`export_interface_libraries.py`、`render_policy_catalog.py`、`render_contract_layers.py` 同样带 `--check`。
  - `python -m pytest -q benchmark/tests skill_library/tests tests`

## 6. 支撑板全量检查与 VLM 观测（2026-10-24 晚）

检查脚本和结果都在 `/data/zenobench/support_layers/checks/`。

### 6.1 碰撞板和渲染板面对比（离线，`slab_vs_render.py`）

做法：在每块碰撞板的范围内按 2 cm 网格往下打射线到渲染网格上，看渲染板面和碰撞板顶面差多少。

- **基本都对得上**：65 块里有 57 块，渲染板面处处都在碰撞板顶面 ±3 mm 以内。large_shelf、bookcase 的内隔板沿分隔板、侧板各有一列网格点下面是空的，这无所谓。
- **desk_1/top**：渲染桌面本身倾斜约 0.5°，从一角的 -7 mm 到对角的 +6 mm。碰撞板是水平的，放在中间高度 0.700。机器人放铅笔的 -x 那一头，渲染桌面比碰撞板低 4–5 mm。
- **mattress_1/top**：床垫中间比碰撞板高 13–15 mm，放上去的东西看起来会陷进床垫。
- **mattress_2/top**：床垫大部分比碰撞板低 5–10 mm，放上去的东西会悬空。

### 6.2 落块测试（Isaac，`drop_test.py`，结果在 `drop_test_classified.json`）

- **做法**：每块碰撞板放 5 个 5×5×3 cm 的箱子，位置是中心和离四条边各 2.75 cm，从板面以上 5 mm 处落下，2 s 后看停在哪里。
- **顶面层（top）基本都正常**：21 块里只有 mattress_2 异常。它的箱子停在碰撞板顶面以下 14 mm，正好是床垫碰撞网格的高度 0.500，碰撞板好像没起作用，原因还没查。
- **内隔板（shelf_N）问题很多**：44 块里有 31 块至少一个箱子异常（倾斜、滑走、翻倒），其中 shelf_0 是 17 块里有 14 块。
- **主要原因是看不见的竖直碰撞面**：44 个异常箱子在生成时就和这种面重叠了。
  - **这些面是什么**：家具碰撞网格里的板子比渲染板高 1–2 cm。`fit_support_repairs.py` 只删 |n_z| > 0.5 的面，所以这块板的顶面被删掉了，侧边的竖直面却留着，在支撑面上围出了一圈 1–2 cm 高、看不见的矮墙。
  - **例子**：large_shelf_1、large_shelf_3、large_shelf_5、tv_stand_1、cell_shelf_2 的 shelf_0，放在**正中间**的箱子都被撞倒或撞歪了。
  - **前沿挡边**：bookcase_1/shelf_0 前沿还有一道 1.9 cm 高的看不见的挡边，几乎贯穿整条边。cell_shelf_4/shelf_0、cell_shelf_5/shelf_0、tv_stand_1/shelf_0、large_shelf_4/shelf_1 也有局部的。
  - **一个可能的修法**：在支撑面范围内，把只比板面高出几厘米的竖直面也删掉。真正的分隔板和侧板会一直升到上一层板，靠这一点能和它们区分开。
- **cell_shelf_3 的 shelf_1 和 shelf_2**：箱子停在碰撞板以上 5 mm。

### 6.2.1 修了矮墙（`fit_support_repairs.py` 切低矮面）

- **改法**：碰撞面只要伸到碰撞板范围上方（外圈 1 cm 也算），而且最高点离板面不到 `LOW_REACH`（8 cm，同时不超过净空的一半），就把板面以上的部分切掉。切口处补新的点，所以要额外写一份 points 覆盖；板面以下的部分保留，底座前面那块板还在，仍能挡住机器人底盘。分隔板和侧板会一直升到上一层板，整面不动。
- **结果**：
  - **改了哪些**：内隔板一共切了约 4300 个面；desk_3 和 kitchen_counter_1 各有几十个比板面高 2 mm 的面也被切掉。桌面、餐桌、床垫一个面都没动。
  - **幂等**：连跑两次，140 个碰撞网格完全一样。
  - **分隔板**：在板面以上 0.6 倍净空的高度数竖直面，数量没有变少；有些被切在上一层板面处的分隔板，切口把三角形一分为二，所以数量反而变多了。
  - **修之前的备份**：`/data/zenobench/support_layers/zeno_house.before_low_wall_clip.usd`。
- **落块测试重跑**（`checks/drop_test_after_clip.json`）：
  - **内隔板**：异常箱子从 80 个降到 13 个；只算没压到画面上分隔板的测试点，从 49 个降到 7 个。
  - **剩下的有三类**：
    - **侧板偏了**：6 个箱子贴着侧边被平推了 2–2.5 cm，没歪也没翘。原因是碰撞网格里的侧板比画面上的往里偏了约 2 cm，这次没处理。
    - **large_shelf_5/shelf_0 后沿**：箱子垫高了 14 mm，是卧室外墙碰撞体在 0.122 的台阶伸进了书架后沿约 2.5 cm。
    - **mattress_2**：问题出在测试方法上。床上有一条被子 `box_comforter`，碰撞面在 0.528–0.543，测试箱子一开始就卡在被子里，被往下挤穿了碰撞板。实际放上去的东西会落在被子上面，比 `mattress_2/top` 标的高 1.5–3 cm。
- **12 个任务场景重跑 `tools/check_scene.py`**（`checks/scenes_after_clip/`）：全部 PASS。物体没有漂移，柜门保持关着，机器人也没动，所以任务场景不用重新 settle。

### 6.3 VLM 观测（env_service，benchmark profile）

- **怎么测的**：起了 env_service（`--host 127.0.0.1`），用 `/data/zenobench/support_layers/vlm_obs/vlm_client.py` 扮演 VLM，把 T14 book_on_desk 的路线一条一条地调用。每一步的响应在 `vlm_obs/T14/`：JSON 里图片换成了文件名，PNG 单独存放。结果和 run_episode 一致，place 失败。
- **VLM 拿到的东西**：
  - **图像**：一张 640×480 的头部相机 PNG。
  - **视野里的物体**：`visible_objects` 和 `observation_cache`，`last_seen_on` 已经是 `desk_1/top` 这种新名字。
  - **已知地点**：`known_places` 一共 164 项，其中房间 10 个、家具 42 件、支撑面 112 个。支撑面里 65 个来自碰撞板，另外 47 个是 PartNet 柜子自带的 `inside_bottom`、`inside_shelf`、`top`。cabinet_6、cabinet_8、cabinet_9 的 top 高 1.6–1.75 m，机器人够不着，也列在里面。没有残留的 `surface_N` 名字。
  - **其他**：`robot` 状态和 `last_result`。
- **另外注意**：失败结果的 `error` 字符串里带着 GT 坐标（"bottom at (1.36, -0.65, 0.116)"）。
