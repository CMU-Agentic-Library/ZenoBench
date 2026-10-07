# ZenoBench Agent SkillNode Library

上层可选择 **50 个 SkillNode**（`skill_001`–`skill_050`）；每个节点恰好对应一个可执行 Contract（`contract_009`–`contract_058`）。节点目录采用 Agent Skill 风格：`SKILL.md` 有名称、用途、参数、前置条件、预期状态变化、调用方式、内部 policy 计划、相关 Skill、失败处理与适用边界；同目录的 `skill.json` 供程序读取。

Contract 是该节点的执行与验证边界。上层 SkillNode 保留抽象的 `object_ref`、`support_ref` 等名词槽位；场景实例 ID 由 Graph Manager grounding 后填入配对 Contract。Contract 对已填名词做标注与状态检查，可在执行前按名词属性选一个 policy 路径，每条路径再顺序组合一个或多个底层 policy。底层现有 64 个公开 policy 入口；不是每个控制阶段都要成为上层节点。任务目标仍由 `TaskEvaluator` 在整条子图执行后判断。

## 能力分组

| 范围 | SkillNode | 上层可规划的变化 |
| --- | --- | --- |
| 底盘、姿态、携物 | `001–002`, `011–013`, `021`, `031–034`, `041–044` | 导航、调整姿态、抬高携物、后退让位 |
| 门与电器 | `003`, `007`, `009–010`, `022–026`, `040`, `047–048`, `050` | 手柄或动力门开关、按钮按压、等待温度达标 |
| 抓取与准备 | `004`, `015–018`, `020`, `027–029`, `035–036`, `049` | 常规、边缘、杯柄、腔体、地面抓取；制造可抓边缘及扶正 |
| 放置与推动 | `005–006`, `008`, `014`, `019`, `030`, `037–039`, `045–046` | 支撑面、容器、炉腔、薄物边缘、指定区域放置；推动 |

`skill_043`–`skill_050` 补充底盘微调、专用接触搬移、门型专用打开、地面预抓取和微波炉门让位。12 个 EmbodiedGen V2 纹理资产、两个任务场景及厨房锅示例的接入方法见 [资产说明](../assets/EMBODIEDGEN_V2_ASSETS.md)。这些动作扩展了可选路径；是否能完成具体任务仍由场景和实测结果决定。旧程序化网格上的首个“抓罐→入盒”链曾通过；V2 网格需要重新执行物理验证，见[验证发现](verification/FINDINGS.md)。

此前的节点补齐任务谓词：`skill_040` 验证食品达到指定温度；`skill_037` 和 `skill_039` 在放下后验证直立；`skill_038` 和 `skill_039` 验证与同一个放置提示点的距离。薄物体可以先用 `skill_035` 制造安全悬边，再尝试 `skill_016` 边缘抓取。每项的物理适用条件和验证状态见其 `SKILL.md`。

## 动作谓词与任务目标

每个 SkillNode 和配对 Contract 都有一个**唯一动词＋名词**的 `action_predicate`，动词在 50 个节点中不重复。它的 `arguments` 是名词或数值槽位，Graph Manager 会绑定到场景实例；Contract 只在 `verified_by` 中的状态事实全部通过后报告 `verified_action_predicate`。例如 `skill_006` 的动作是 `insert_object_in_container(object, container)`，而可共享的实测事实是 `inside` 与 `right_hand_empty`。不同 Skill 可以产生同一个状态事实，这是任务拼接所需要的。

### 任务如何由多个 SkillNode 完成

可以。上层把任务拆成当前子目标，按顺序或依赖关系输出多个 SkillNode；Graph Manager 检查参数、名词绑定和依赖 DAG，再逐个调用配对 Contract。每个 Contract 会选择适用于当前名词和状态的底层 policy 路径，并返回测得的结果。上层依据结果继续执行或重新规划，最后由 `TaskEvaluator` 判断整个任务目标。

例如“把饮料罐放进宽收纳盒”需要先 `skill_004` 抓罐，再 `skill_006` 入盒。`object` 和 `container` 是可填写的输入槽位：

```json
{
  "schema_version": 1,
  "kind": "skill_subgraph",
  "subgoal_id": "sg_store_can",
  "nodes": [
    {"id": "n1", "skill_id": "skill_004", "args": {"object": {"ref": "the soda can"}}, "depends_on": []},
    {"id": "n2", "skill_id": "skill_006", "args": {"object": {"ref": "the soda can"}, "container": {"ref": "the wide storage bin"}}, "depends_on": ["n1"]}
  ]
}
```

名词绑定为 `{"the soda can": "soda_can", "the wide storage bin": "wide_storage_bin"}`。更多物品可以继续接在 `depends_on` 链中；需要移动底盘或准备抓取时，也可插入相应节点。完整六节点示例见[收纳子图](examples/recycle_and_store.skill_subgraph.json)。目前 10 个任务的 42 条目标子句都有可表达的调用路径，但这只是规划覆盖。该三物件场景中“抓罐→入盒”已实测通过，完整任务在第二次抓取前的收臂环节失败，见[验证发现](verification/FINDINGS.md)。

### 动词、可填写参数与验证谓词

下表给出全部 50 个动词＋名词动作谓词。上层**填写参数**，不自行填写 `inside`、`on` 等结果谓词：它们由 Contract 在执行后测量。`*_ref` 参数用 `{"ref":"场景中的描述"}`，由 grounding 绑定到实例 ID；`pose2d`、`xy`、`unit_vec2` 和数值参数用 `{"value": ...}`。例如 `{"value":[1.0,2.0,90.0]}` 是一个 `pose2d`，`{"value":[1.0,0.0]}` 是一个二维方向。具体名词资格、前置条件和失败处理以各节点的 `skill.json`／`SKILL.md` 为准。

<!-- action-signatures:start -->
| SkillNode | 动词 | 动词＋名词动作谓词 | 可填写参数及类型 | Contract 验证的状态 |
| --- | --- | --- | --- | --- |
| `skill_001` | `navigate` | `navigate_base` | `pose: pose2d` | `base_at` |
| `skill_002` | `transport` | `transport_carried_object` | `object: object_ref`, `pose: pose2d` | `base_at`, `grasp_preserved` |
| `skill_003` | `open` | `open_articulated_joint` | `articulated: articulated_ref` | `joint_open_enough` |
| `skill_004` | `acquire` | `acquire_object` | `object: object_ref` | `held_by_right_hand`, `object_lifted` |
| `skill_005` | `deposit` | `deposit_object_on_support` | `object: object_ref`, `support: support_ref` | `on`, `right_hand_empty` |
| `skill_006` | `insert` | `insert_object_in_container` | `object: object_ref`, `container: container_ref` | `inside`, `right_hand_empty` |
| `skill_007` | `close` | `close_articulated_joint` | `articulated: articulated_ref` | `joint_closed` |
| `skill_008` | `shove` | `shove_object_along_support` | `object: object_ref`, `support: support_ref`, `direction_xy: unit_vec2`, `distance_m: positive_number` | `displacement_along` |
| `skill_009` | `press` | `press_appliance_door_button` | `appliance: appliance_ref` | `button_pressed_this_call` |
| `skill_010` | `start` | `start_microwave_heating` | `appliance: appliance_ref` | `button_pressed_this_call`, `heating_active` |
| `skill_011` | `tuck` | `tuck_right_arm` | 无 | `posture_at_target` |
| `skill_012` | `set` | `set_torso_height` | `height_m: number` | `posture_at_target` |
| `skill_013` | `pitch` | `pitch_waist` | `pitch_rad: number` | `posture_at_target` |
| `skill_014` | `load` | `load_microwave_cavity` | `object: object_ref`, `support: microwave_support_ref` | `on`, `right_hand_empty` |
| `skill_015` | `retrieve` | `retrieve_cavity_object` | `object: object_ref`, `cavity: appliance_ref` | `held_by_right_hand`, `object_lifted` |
| `skill_016` | `pinch` | `pinch_flat_object_edge` | `object: object_ref` | `held_by_right_hand`, `object_lifted` |
| `skill_017` | `grip` | `grip_cup_handle` | `object: object_ref` | `held_by_right_hand`, `object_lifted` |
| `skill_018` | `intercept` | `intercept_moving_object` | `object: object_ref`, `base_path: pose2d` | `held_by_right_hand`, `object_lifted` |
| `skill_019` | `deliver` | `deliver_object` | `object: object_ref`, `support: support_ref`, `base_path: pose2d` | `on`, `right_hand_empty` |
| `skill_020` | `scoop` | `scoop_floor_object` | `object: object_ref` | `held_by_right_hand`, `object_lifted` |
| `skill_021` | `convoy` | `convoy_bimanual_load` | `object: object_ref`, `pose: pose2d` | `base_at`, `grasp_preserved` |
| `skill_022` | `swing` | `swing_articulated_door` | `object: object_ref`, `articulated: articulated_ref` | `joint_open_enough` |
| `skill_023` | `trigger` | `trigger_microwave_door_opening` | `appliance: appliance_ref` | `joint_open_enough` |
| `skill_024` | `shut` | `shut_microwave_door` | `appliance: appliance_ref` | `joint_closed` |
| `skill_025` | `pull` | `pull_manual_handle` | `articulated: articulated_ref` | `joint_open_enough` |
| `skill_026` | `push` | `push_manual_handle` | `articulated: articulated_ref` | `joint_closed` |
| `skill_027` | `clamp` | `clamp_object_top` | `object: object_ref` | `held_by_right_hand`, `object_lifted` |
| `skill_028` | `grasp` | `grasp_round_rim` | `object: object_ref` | `held_by_right_hand`, `object_lifted` |
| `skill_029` | `clasp` | `clasp_rectangular_rim` | `object: object_ref` | `held_by_right_hand`, `object_lifted` |
| `skill_030` | `lay` | `lay_edge_held_flat_object` | `object: object_ref`, `support: support_ref` | `on`, `right_hand_empty` |
| `skill_031` | `lower` | `lower_torso` | 无 | `posture_at_target` |
| `skill_032` | `raise` | `raise_torso` | 无 | `posture_at_target` |
| `skill_033` | `lean` | `lean_waist` | 无 | `posture_at_target` |
| `skill_034` | `straighten` | `straighten_waist` | 无 | `posture_at_target` |
| `skill_035` | `expose` | `expose_flat_object_edge` | `object: object_ref` | `edge_overhang_ready` |
| `skill_036` | `orient` | `orient_held_object` | `object: object_ref` | `object_upright` |
| `skill_037` | `stand` | `stand_object_on_support` | `object: object_ref`, `support: support_ref` | `on`, `right_hand_empty`, `object_upright` |
| `skill_038` | `position` | `position_object_near_hint` | `object: object_ref`, `support: support_ref`, `hint_xy: xy`, `max_offset_m: positive_number` | `on`, `right_hand_empty`, `within_hint_radius` |
| `skill_039` | `align` | `align_upright_object_near_hint` | `object: object_ref`, `support: support_ref`, `hint_xy: xy`, `max_offset_m: positive_number` | `on`, `right_hand_empty`, `object_upright`, `within_hint_radius` |
| `skill_040` | `attain` | `attain_food_temperature` | `object: object_ref`, `min_temp_c: positive_number` | `temperature_at_least` |
| `skill_041` | `hoist` | `hoist_carried_object` | `object: object_ref`, `min_bottom_z: positive_number` | `held_object_above_height` |
| `skill_042` | `retreat` | `retreat_carried_object` | `object: object_ref`, `distance_m: positive_number` | `base_backed_off`, `grasp_preserved` |
| `skill_043` | `pivot` | `pivot_base` | `delta_yaw_deg: number` | `base_yaw_changed` |
| `skill_044` | `translate` | `translate_base` | `forward_m: number` | `base_translated_locally` |
| `skill_045` | `nudge` | `nudge_supported_object` | `object: object_ref`, `support: support_ref`, `direction_xy: unit_vec2`, `distance_m: positive_number` | `displacement_along` |
| `skill_046` | `drag` | `drag_supported_object` | `object: object_ref`, `support: support_ref`, `direction_xy: unit_vec2`, `distance_m: positive_number` | `displacement_along` |
| `skill_047` | `unfold` | `unfold_hinged_door` | `articulated: articulated_ref` | `joint_open_enough` |
| `skill_048` | `extend` | `extend_drawer` | `articulated: articulated_ref` | `joint_open_enough` |
| `skill_049` | `ready` | `ready_floor_object` | `object: object_ref` | `floor_reach_ready` |
| `skill_050` | `clear` | `clear_microwave_door_sweep` | `articulated: articulated_ref` | `microwave_sweep_clear` |
<!-- action-signatures:end -->

[50 个动作谓词总表](ACTION_PREDICATES.md)列出动作与验证事实，[任务目标映射](goal_predicates.json)把它们接到 `inside`、`on`、`upright`、`near`、`heated`、`closed` 等目标。`near` 要由最终评估器检查组内两两距离；`not_dropped` 是全程不变量，不能由单个动作谓词保证。现有 10 个任务的 42 条目标子句均有名义上的动作路径或最终检查；这不等于物理场景全部成功。

## 与上层如何对接

VLM 根据任务目标及当前观察生成当前子目标的 `skill_subgraph`：每个节点只有 `id`、`skill_id`、`args`、`depends_on`。对象引用用 `{"ref":"the apple"}`；数值用 `{"value":...}`。Grounding 模块另提供 ref 到唯一场景实例 ID 的绑定。见 [四节点水果示例](examples/collect_fruits.skill_subgraph.json)、[六节点收纳示例](examples/recycle_and_store.skill_subgraph.json)、[十二节点新资产示例](examples/organize_utility_items.skill_subgraph.json)、[加热示例](examples/heat_preloaded.skill_subgraph.json) 和 [子图 Schema](subgraph.schema.json)。收纳示例的名词绑定见 [bindings](examples/recycle_and_store.bindings.json)，新资产示例的名词绑定见 [bindings](examples/organize_utility_items.bindings.json)；两者都是模拟器控制图，不是 GPT 生成结果。

[关系目录](relations.json) 提供 47 条**有条件的**准备、使能、后续、替代和恢复提示。例如“微波炉关门 → 启动加热 → 等待温度达标”，以及“薄物制造悬边 → 边缘抓取”。这些关系帮助 VLM 提出 `depends_on`，不是固定的全局任务图；Graph Manager 必须根据实时状态、参数类型和任务目标验证，再按需执行。失败后返回测得的部分状态，上层重新规划；关系和 fallback 不会自动触发其他动作。

上层获取公开目录和失败后的恢复候选可用 [planner_handoff.py](planner_handoff.py)；请求字段、恢复循环和当前边界见 [上层对接说明](UPPER_LAYER_HANDOFF.md)。

Graph Manager 在 [graph.py](graph.py) 中检查 ID、参数、依赖 DAG、场景绑定和 SkillNode／Contract 一对一关系，然后编译为 `ContractRunner.run(contract_id, "compose", *args)`。直接调用时也可用 `ContractRunner.run_bound("contract_012", object="apple")` 按名词槽位填写。选中的路径与绑定属性写入结果的 `selected_policy_path`、`bound_nouns`；无匹配路径时不执行 policy。已有 rig 时使用 `skill_library.runtime.run_subgraph(rig, graph, bindings)`。

## 任务覆盖的含义

[逐任务蓝图](TASK_PLANS.md) 给出条件化动作链；[逐任务审计](task_coverage.json) 对照 `tasks/*/task.json`：10 个任务的 **42 条目标子句**均有可表达的动作路径或终态检查，涉及 `inside`、`on`、直立、成组靠近、加热、关门和 `not_dropped`。例如 `near` 是**成组两两距离**；单次 `skill_038` 只验证一个物体与提示点的距离。上层应选共同提示点，把每个物体放在任务阈值一半以内，再用 `TaskEvaluator` 核对整个组。

[GPT 规划与 ZenoBench 实验协议](../experiments/gpt_skill_baseline/README.md) 区分 JSON 规划有效性、Contract 执行和最终任务成功。

这是**目标表达覆盖**，不等于所有随机场景都物理成功。`not_dropped` 和 `closed: all` 是终态条件，分别要靠各动作维持或逐门修复，并由任务评估器最终核对。可达性、抓持稳定性、候选物是否存在等仍是运行时问题；地面容器翻倒后的复位尚无独立实跑保证。

## 生成与检查

```bash
python -m skill_library.graph --graph skill_library/examples/collect_fruits.skill_subgraph.json \
  --bindings skill_library/examples/collect_fruits.bindings.json \
  --ann tasks/collect_fruits/annotation.json --format upper
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests -q
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill_library/tests -q
PYTHONDONTWRITEBYTECODE=1 python tools/export_agent_skill_docs.py --check
PYTHONDONTWRITEBYTECODE=1 python tools/export_interface_libraries.py --check
PYTHONDONTWRITEBYTECODE=1 python tools/audit_skill_task_coverage.py --check
```

Contract 明细见 [Contract Library](../contract_library/README.md)，policy 明细见 [Policy Library](../policy_library/README.md)，逐技能实跑状态见 [50 节点验证清单](verification/STATUS.md)，未通过的四项见 [物理测试发现](verification/FINDINGS.md)，完整成功与失败轨迹见 [验证摘要](verification/node_contract_smoke.json)。其中温度达到 63.6°C；区域放置误差约 2.1 cm；另有早餐碗搬运滑脱案例。
