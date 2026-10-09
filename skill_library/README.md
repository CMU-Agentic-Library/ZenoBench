# ZenoBench 动词 SkillNode 库（schema 2）

<!-- counts:start -->
**70 个 SkillNode**（`skill_001`–`skill_070`，70 个不同动词）一一对应 **70 个 Contract**（`contract_009`–`contract_078`），共 **120 条按名词选择的 policy 路径**，覆盖 **114/115 个底层 policy**（1 个因物理上不可行而退役，原因见 [POLICY_COVERAGE.md](../policy_library/POLICY_COVERAGE.md)）；前后条件来自 **71 个 GT 谓词**。关系图有 49 条 enables、49 条 then、43 条 fallback （repair 14、recover 26、substitute 3）和 45 条 alternative。[tasks.json](tasks.json) 列出 35 个任务。
<!-- counts:end -->

## 设计

每个 SkillNode 是 **一个动词 + 一个名词**，动词之间不是近义词。同一个动作只保留一个动词：抓取不再拆成 acquire / grasp / clamp / clasp / pinch 等多个节点，只有 `pick(object)`；放置只有 `place(object, receptacle)`。名词绑定到场景实例后，Contract 根据该实例的 GT 标注和实时状态选择 **policy 路径**，每条路径顺序调用一个或多个底层 policy。例如：

| 动词 | 名词绑定 | 选中的路径 | policy 链 |
| --- | --- | --- | --- |
| `pick` | 苹果（`top_pinch` 标注） | `top_pinch` | `policy_010` |
| `pick` | 平放的书（只有 `edge_pinch` 标注） | `flat_edge` | `policy_045` 推到桌边 → `policy_013` 夹悬出部分 |
| `pick` | 地上的积木 | `floor_top` | `policy_065` 靠近 → `policy_042` 降躯干前倾预抓 → `policy_010` 顶部夹取 |
| `pick` | 微波炉腔内的碗 | `microwave_cavity` | `policy_048`（路径前置条件：`is_open(微波炉)`） |
| `heat` | `kitchen_microwave` | `microwave` | `policy_032` 按启动键 → `policy_064` 等待温度 |
| `heat` | `kitchen_stove` | `stove_pot` | `policy_094` 按电源键 → `policy_090` 等待温度并关火 |
| `open` | 冰箱 / 抽屉 / 铰链门 / 微波炉 | 各自路径 | 收臂 → 抓把手 → 随门运动 → 松手；微波炉按门键 + 铰链驱动 |

多物体动词（`fetch`、`collect`、`sort`、`clear`、`empty`、`arrange`、`restore`、`swap`、`hide`）的路径调用其他 Skill Contract，嵌套的每一步都各自检查前后条件。

## 前置条件、后置条件与 verifier

前后条件都是 [`zeno_skills/predicates.py`](../zeno_skills/predicates.py) 中带参数的谓词，例如 `holding(hand=right, object=$object)`、`is_open(articulated=@object.appliance)`、`in_cookware_on_burner(food=$food, appliance=$appliance)`。每个谓词：

- 有类型化参数（`object_ref`、`support_ref`、`hand` …），由检查器核对；
- 有 GT 评估函数，读取仿真器真值：物体位姿、关节角、手指间隙、头相机正运动学、温度状态、事件日志等（每个谓词的 `gt_sources` 写在导出的 JSON 里）；
- 分为 `fluent`（当前状态）、`memory`（机器人记录的事实，如看到过、擦过）和 `relative`（相对 Contract 开始时的变化，如 `object_moved`，只能作后置条件）。

`SkillContractRunner`（[`zeno_skills/skill_runtime.py`](../zeno_skills/skill_runtime.py)）执行一次调用：

1. 校验输入类型，绑定名词并计算 GT 属性（抓取标注、所在支撑面、是否在冰箱或柜子里、盖着的锅盖、离边缘远近等）；
2. **执行前**在实时状态上评估全部前置条件，任何一条为假就不动作并返回 `PRECONDITION_FAILED`；
3. 选择第一条名词条件全部成立的路径，再检查该路径的额外前置条件；
4. 依次执行 policy、嵌套 Contract 或循环；
5. **执行后**评估技能级和路径级后置条件，全部成立才报告成功；
6. 返回实测输出、选中的路径、每个谓词的测量值；失败时附带关系图中可修复失败谓词的 fallback 候选。顶层调用不会自动重试（由上层决定）；多物体技能内部的嵌套调用如果因某个前置条件失败、且关系图里有修复这个谓词的 `repair` fallback（例如 `pick` 的 `grasp_clearance` → `separate`），运行器先执行该修复技能，再重试一次。

## 关系：上一步、下一步、fallback、alternative

[relations.json](relations.json) 中的每条边都被检查器核对：

- `sequence`（导出为上一步 / 下一步）：`enables` 表示前一技能的某个后置条件与后一技能的某个前置条件在参数绑定下匹配；`then` 是较松的顺序，必须给出共享名词绑定或理由。
- `fallback`：`repair` 表示失败后用另一个技能建立缺失的前置条件再重试，例如 `pick` 夹不起平放物体时先 `expose`（用手把它推出桌边，保证 `edge_overhang`）再 `pick`；`recover` 表示消除导致 policy 失败的状态，需写明理由；`substitute` 表示用其他方式达到同一效果。
- `alternative`：用不同手段达到相同效果，例如 `heat(food, kitchen_microwave)` 不可用时改用 `heat(food, kitchen_stove)`，在灶台上用锅或杯子加热。

## 给上层 VLM 的 JSON

- [vlm_skill_catalog.json](vlm_skill_catalog.json)：全部 SkillNode 的 `skill.json` 和谓词表，可直接放进 VLM 提示。
- `skills/skill_XXX/skill.json`：单个节点，包括 `signature`、`inputs`、`outputs`、带 GT 来源的 `preconditions` / `postconditions`、`invalidates`、按名词选择的 `policy_paths`、`relations.previous/next/fallback/fallback_for/alternative` 和失败码。
- `skills/skill_XXX/SKILL.md`：同一内容的 Agent Skill 格式。

VLM 输出 schema 2 子图（[subgraph.schema.json](subgraph.schema.json)），参数可以是场景名词 `{"ref": "..."}`、字面值 `{"value": ...}`，或前一节点的实测输出 `{"from": "n1.found_on"}`：

```json
{"schema_version": 2, "kind": "skill_subgraph", "subgoal_id": "find_lid", "nodes": [
  {"id": "n1", "skill": "search", "args": {"object": {"ref": "pot_lid"}}, "depends_on": []},
  {"id": "n2", "skill": "navigate", "args": {"destination": {"from": "n1.found_on"}}, "depends_on": ["n1"]},
  {"id": "n3", "skill": "uncover", "args": {"container": {"ref": "handled_cooking_pot"}}, "depends_on": ["n2"]}]}
```

[graph.py](graph.py) 校验与 grounding，[runtime.py](runtime.py) 的 `run_subgraph(rig, graph, bindings)` 执行；失败时返回 `replan_request`。[gpt_experiment.py](gpt_experiment.py) 与 [tools/run_gpt_skill_task.py](../tools/run_gpt_skill_task.py) 用同一组卡片让 GPT 规划。

## 任务可组合性

[tasks.json](tasks.json) 用 GT 谓词描述本场景可完成的任务：10 个原有 ZenoBench 任务，加上厨房场景的灶台煮汤、无微波炉时用灶台加热、冰箱冷却、丢垃圾、叠积木、擦台面、翻书、藏物、找东西、探索房间、计数、敲门、分类、清空等。[planner.py](planner.py) 用同一套 GT 谓词从标注场景构造初始状态，按导出的前置/后置/invalidates 做符号搜索，证明每个任务都能由 SkillNode 链完成，结果写到 [plans/](plans/)。这些是规划层结果；物理执行结果见下节。

## 物理验证

[verification/scenarios.json](verification/scenarios.json) 中的场景在 Isaac Sim 中逐条执行 Contract（`tools/verify_skills.py`），每一步都测量前后条件。结果汇总见 [verification/STATUS.md](verification/STATUS.md)，由 `tools/verify_summary.py --write` 生成。

## 生成与检查

```bash
python tools/build_skill_library.py --check        # 定义 -> 导出是否一致，库是否通过全部静态检查
python -m skill_library.planner --all              # 每个任务的 SkillNode 链
python -m pytest tests skill_library/tests -q
$ISAACLAB_PYTHON tools/verify_skills.py --all --jobs 3   # 物理验证
```

源文件只有 [definitions.py](definitions.py)（技能）和 [zeno_skills/predicates.py](../zeno_skills/predicates.py)（谓词）。`skills/`、`contract_library/`、`relations.json`、`vlm_skill_catalog.json`、`SKILLS.md`、`docs/INTERFACE_IDS.md` 都由 `tools/build_skill_library.py` 生成。

<!-- skills:start -->
## 全部 SkillNode

| SkillNode | Verb + noun | Signature | Paths (noun-selected) | Postconditions |
|---|---|---|---|---|
| `skill_001` | **navigate** place | `navigate(destination)` | two_hand_carry, carry, empty | `base_near` |
| `skill_002` | **approach** target | `approach(target, pass_by?)` | reach_on_the_move, park | `reachable` |
| `skill_003` | **face** target | `face(target)` | rotate_empty, rotate_loaded | `facing` |
| `skill_004` | **retreat** obstacle | `retreat(obstacle, distance_m)` | microwave_door_sweep, bimanual_or_left_load, loaded, empty | `base_clear_of` |
| `skill_005` | **crouch** torso | `crouch(height_m?)` | to_height, lowest | `torso_raised` + `torso_at`, `torso_lowered` |
| `skill_006` | **stand** torso | `stand()` | highest | `torso_raised` |
| `skill_007` | **bend** waist | `bend(pitch_rad?)` | to_pitch, full | `waist_bent` |
| `skill_008` | **straighten** waist | `straighten()` | upright | `waist_straight` |
| `skill_009` | **tuck** arm | `tuck(hand)` | left, right | `arm_stowed` |
| `skill_010` | **reset** posture | `reset()` | joint_home | `arm_stowed`, `torso_raised`, `waist_straight` |
| `skill_011` | **look** target | `look(target)` | head_only, turn_then_head | `in_view`, `observed` |
| `skill_012` | **inspect** receptacle | `inspect(receptacle)` | closed_cabinet, open_view | `observed` |
| `skill_013` | **search** object | `search(object, region?)` | room_sweep | `observed` |
| `skill_014` | **explore** room | `explore(room)` | viewpoints | `room_explored` |
| `skill_015` | **point** target | `point(target)` | front, turn_and_point | `pointing_at`, `hand_empty` |
| `skill_016` | **present** object | `present(object)` | front_of_head | `presenting`, `holding` |
| `skill_017` | **pick** object | `pick(object, hands?, grasp?, pass_by?)` | microwave_cavity, inside_cabinet_or_fridge, handle_requested, on_the_move, two_hand_box, two_hand_flat, floor_top, flat_overhang_ready, flat_edge, rect_rim, round_rim, handle, top_pinch, annotation_dispatch | `holding` + `holding` |
| `skill_018` | **place** object | `place(object, receptacle, hint_xy?, pass_by?)` | microwave_staged, microwave, cabinet_or_fridge_shelf, container, on_the_move, edge_held_flat, stove_burner, surface | `hand_empty` + `in_appliance`, `inside`, `on`, `on_burner` |
| `skill_019` | **drop** object | `drop(object, container)` | above_opening | `inside`, `hand_empty` |
| `skill_020` | **stack** object | `stack(object, base)` | top_face | `on_top_of`, `hand_empty` |
| `skill_021` | **release** object | `release(object, hand)` | open_in_place | `hand_empty` |
| `skill_022` | **handover** object | `handover(object)` | right_to_left | `holding`, `hand_empty` |
| `skill_023` | **lift** object | `lift(object, height_m)` | raise | `held_above`, `holding` |
| `skill_024` | **lower** object | `lower(object, height_m)` | descend | `held_below`, `holding` |
| `skill_025` | **rotate** object | `rotate(object, degrees)` | wrist_yaw | `yaw_rotated`, `holding` |
| `skill_026` | **regrasp** object | `regrasp(object, support)` | set_down_and_pick | `holding` |
| `skill_027` | **brace** object | `brace(object)` | left_rim_pinch | `steadied`, `holding` |
| `skill_028` | **flip** object | `flip(object)` | edge_roll | `flipped`, `hand_empty` |
| `skill_029` | **push** object | `push(object, direction_xy, distance_m)` | drag_from_top, thin_auto, from_behind | `object_moved` |
| `skill_030` | **pull** object | `pull(object, distance_m)` | top_drag | `moved_toward_base`, `reachable` |
| `skill_031` | **expose** object | `expose(object)` | slide_to_edge | `edge_overhang` |
| `skill_032` | **separate** object | `separate(object)` | push_apart | `grasp_clearance` |
| `skill_033` | **center** object | `center(object, margin_m)` | push_inward | `away_from_edge` |
| `skill_034` | **roll** object | `roll(object, distance_m)` | push_above_axis | `object_rolled` |
| `skill_035` | **tip** object | `tip(object)` | push_high | `lying` |
| `skill_036` | **upright** object | `upright(object)` | pick_orient_place | `upright`, `hand_empty` + `on` |
| `skill_037` | **wipe** surface | `wipe(surface, tool)` | sponge_strip | `wiped`, `holding` |
| `skill_038` | **stir** container | `stir(container, tool)` | circle_below_rim | `stirred`, `holding` |
| `skill_039` | **pour** contents | `pour(source, target)` | tilt_over_rim | `poured_into`, `holding` |
| `skill_040` | **open** articulated | `open(articulated)` | powered_microwave, left_holds_load, refrigerator, drawer, hinged_door | `is_open` |
| `skill_041` | **close** articulated | `close(articulated)` | powered_loaded, powered, handle_push, dispatch | `is_closed` |
| `skill_042` | **press** button | `press(button)` | microwave_start_staged, microwave_door_key, generic_key | `button_pressed`, `hand_empty` + `heating` |
| `skill_043` | **heat** food | `heat(food, appliance, temp_c)` | microwave, stove_pot | `temperature_at_least`, `heating` |
| `skill_044` | **chill** food | `chill(food, appliance, temp_c)` | fridge_wait | `temperature_at_most` |
| `skill_045` | **cover** container | `cover(container, lid)` | rim_plane | `covered`, `hand_empty` |
| `skill_046` | **uncover** container | `uncover(container)` | knob_lift_aside | `uncovered`, `hand_empty` + `on` |
| `skill_047` | **fetch** object | `fetch(object, receptacle)` | to_container, to_surface | `hand_empty` + `inside`, `on` |
| `skill_048` | **collect** objects | `collect(objects, container)` | fetch_each | `all_inside` |
| `skill_049` | **sort** objects | `sort(objects, rule)` | fetch_by_tag | `sorted_by_category` |
| `skill_050` | **clear** support | `clear(support, receptacle)` | fetch_each_on_support | `support_clear` |
| `skill_051` | **empty** container | `empty(container, receptacle)` | pick_each_inside, pour_out | `container_empty` |
| `skill_052` | **arrange** objects | `arrange(objects, support, max_dist_m)` | place_near_common_spot | `grouped` |
| `skill_053` | **restore** object | `restore(object)` | dispatch_pick_place | `at_initial_place`, `hand_empty` |
| `skill_054` | **swap** objects | `swap(a, b)` | via_buffer | `positions_swapped`, `hand_empty` |
| `skill_055` | **sidestep** base | `sidestep(distance_m)` | empty_tucked, loaded | `sidestepped` |
| `skill_056` | **wait** duration | `wait(seconds)` | idle | `waited` |
| `skill_057` | **identify** object | `identify(object)` | look_and_label | `identified`, `in_view` |
| `skill_058` | **measure** object | `measure(object)` | look_and_size | `measured`, `in_view` |
| `skill_059` | **count** category | `count(category)` | head_sweep | `counted` |
| `skill_060` | **wave** hand | `wave()` | raised_swing | `waved`, `hand_empty` |
| `skill_061` | **nod** head | `nod()` | pitch_cycles | `nodded` |
| `skill_062` | **shake** object | `shake(object)` | lateral | `shaken`, `holding` |
| `skill_063` | **hover** object | `hover(object, target)` | above_target | `hovering_over`, `holding` |
| `skill_064` | **square** object | `square(object)` | pick_rotate_place | `squared`, `hand_empty` |
| `skill_065` | **touch** object | `touch(object)` | fingertip_top | `touched`, `hand_empty` |
| `skill_066` | **knock** articulated | `knock(articulated)` | panel_taps | `knocked`, `is_closed` |
| `skill_067` | **sweep** objects | `sweep(objects, radius_m)` | push_to_centroid | `clustered` |
| `skill_068` | **stop** appliance | `stop(appliance)` | stove_key_off, microwave_door | `heating` + `is_open` |
| `skill_069` | **dip** utensil | `dip(tool, container)` | tip_below_rim | `dipped`, `holding` |
| `skill_070` | **hide** object | `hide(object, receptacle, lid?)` | container_with_lid, closed_cabinet | `hidden`, `hand_empty` |
<!-- skills:end -->
