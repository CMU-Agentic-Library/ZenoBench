# 三层接口的稳定 ID 与旧名

新子图使用 `skill_001` 等 Skill ID；活跃执行层使用 `contract_009`–`contract_058`；旧 family 层保留 `contract_001`–`contract_008`；
底层使用 `policy_001` 等 policy ID。ID 保持稳定，描述性名称可以在
不改变语义的前提下修改。现有脚本使用的旧 Contract/Policy 名称保留为兼容别名。

## 活跃的一对一 SkillNode / Contract

| SkillNode | Contract |
| --- | --- |
| `skill_001` | `contract_009` |
| `skill_002` | `contract_010` |
| `skill_003` | `contract_011` |
| `skill_004` | `contract_012` |
| `skill_005` | `contract_013` |
| `skill_006` | `contract_014` |
| `skill_007` | `contract_015` |
| `skill_008` | `contract_016` |
| `skill_009` | `contract_017` |
| `skill_010` | `contract_018` |
| `skill_011` | `contract_019` |
| `skill_012` | `contract_020` |
| `skill_013` | `contract_021` |
| `skill_014` | `contract_022` |
| `skill_015` | `contract_023` |
| `skill_016` | `contract_024` |
| `skill_017` | `contract_025` |
| `skill_018` | `contract_026` |
| `skill_019` | `contract_027` |
| `skill_020` | `contract_028` |
| `skill_021` | `contract_029` |
| `skill_022` | `contract_030` |
| `skill_023` | `contract_031` |
| `skill_024` | `contract_032` |
| `skill_025` | `contract_033` |
| `skill_026` | `contract_034` |
| `skill_027` | `contract_035` |
| `skill_028` | `contract_036` |
| `skill_029` | `contract_037` |
| `skill_030` | `contract_038` |
| `skill_031` | `contract_039` |
| `skill_032` | `contract_040` |
| `skill_033` | `contract_041` |
| `skill_034` | `contract_042` |
| `skill_035` | `contract_043` |
| `skill_036` | `contract_044` |
| `skill_037` | `contract_045` |
| `skill_038` | `contract_046` |
| `skill_039` | `contract_047` |
| `skill_040` | `contract_048` |
| `skill_041` | `contract_049` |
| `skill_042` | `contract_050` |
| `skill_043` | `contract_051` |
| `skill_044` | `contract_052` |
| `skill_045` | `contract_053` |
| `skill_046` | `contract_054` |
| `skill_047` | `contract_055` |
| `skill_048` | `contract_056` |
| `skill_049` | `contract_057` |
| `skill_050` | `contract_058` |

## 兼容 family Contract

| 公开 ID | 旧名 |
| --- | --- |
| `contract_001` | `navigate.v1` |
| `contract_002` | `pick.v1` |
| `contract_003` | `place.v1` |
| `contract_004` | `open.v1` |
| `contract_005` | `close.v1` |
| `contract_006` | `push.v1` |
| `contract_007` | `click.v1` |
| `contract_008` | `set_posture.v1` |

## Low-level policy

| 公开 ID | 旧名 |
| --- | --- |
| `policy_001` | `empty_navigate` |
| `policy_002` | `carry_navigate` |
| `policy_003` | `tuck_arm` |
| `policy_004` | `set_torso_height` |
| `policy_005` | `lower_torso` |
| `policy_006` | `raise_torso` |
| `policy_007` | `set_waist_pitch` |
| `policy_008` | `lean_forward` |
| `policy_009` | `straighten_waist` |
| `policy_010` | `pick_top` |
| `policy_011` | `pick_round_rim` |
| `policy_012` | `pick_rect_rim` |
| `policy_013` | `pick_edge` |
| `policy_014` | `pick_floor_corner` |
| `policy_015` | `place_surface` |
| `policy_016` | `place_container` |
| `policy_017` | `place_edge` |
| `policy_018` | `microwave_cavity_insert` |
| `policy_019` | `microwave_cavity_release` |
| `policy_020` | `microwave_cavity_withdraw` |
| `policy_021` | `place_microwave` |
| `policy_022` | `open_handle` |
| `policy_023` | `close_handle` |
| `policy_024` | `open_powered` |
| `policy_025` | `close_powered` |
| `policy_026` | `push` |
| `policy_027` | `microwave_button_approach` |
| `policy_028` | `microwave_button_press` |
| `policy_029` | `microwave_button_retract` |
| `policy_030` | `microwave_door_clear` |
| `policy_031` | `microwave_hinge_drive` |
| `policy_032` | `microwave_start` |
| `policy_033` | `click` |
| `policy_034` | `carry_height_adjust` |
| `policy_035` | `back_off_with_load` |
| `policy_036` | `base_rotate_in_place` |
| `policy_037` | `base_translate_local` |
| `policy_038` | `right_tcp_move` |
| `policy_039` | `right_joint_move` |
| `policy_040` | `right_gripper_open` |
| `policy_041` | `right_gripper_close` |
| `policy_042` | `prepare_floor_reach` |
| `policy_043` | `push_from_behind` |
| `policy_044` | `top_drag` |
| `policy_045` | `slide_to_edge` |
| `policy_046` | `grasp_articulated_handle` |
| `policy_047` | `release_articulated_handle` |
| `policy_048` | `pick_from_cavity` |
| `policy_049` | `open_revolute_door` |
| `policy_050` | `open_prismatic_drawer` |
| `policy_051` | `reach_while_moving` |
| `policy_052` | `pick_while_moving` |
| `policy_053` | `place_while_moving` |
| `policy_054` | `upright_object` |
| `policy_055` | `pick_cup_handle` |
| `policy_056` | `bimanual_flat_pick` |
| `policy_057` | `bimanual_box_lift` |
| `policy_058` | `bimanual_carry` |
| `policy_059` | `handover_right_to_left` |
| `policy_060` | `open_door_while_left_holds` |
| `policy_061` | `pick` |
| `policy_062` | `open` |
| `policy_063` | `close` |
| `policy_064` | `wait_for_temperature` |

## 名词绑定与路径选择

SkillNode 的 `object_ref` 等参数是抽象槽位，上层输出语义 ref，Graph Manager 将 ref 唯一绑定到场景实例 ID。活跃 Contract 的 `noun_bindings` 声明该 ID 应来自 `rig.ann.objects`、支撑面或 articulated 注释，以及容器、右手持有等约束。`policy_plan.kind=choice` 的 Contract 在调用任何 policy 前，按实测/标注属性对 `paths[].when` 顺序匹配；路径内部的 `steps` 顺序执行。执行结果包含 `bound_nouns` 和 `selected_policy_path`。没有匹配路径就停止，不自动转去另一个 SkillNode。

例如 `contract_012` 的 `object=apple` 选择 `top_pinch/policy_010`，`object=bowl_side_table` 选择 `round_rim/policy_011`。`ContractRunner.run_bound("contract_012", object="apple")` 是按字段名填写 Contract 的直接入口；SkillSubgraph 仍使用 `{"object":{"ref":"the apple"}}`。

## 运行时兼容

- `ContractRunner.run("contract_002", "auto", "apple")` 与旧的 `pick.v1` 调用同一路线。
- `PolicySuite(rig).policy_010` 与 `PolicySuite(rig).pick_top` 是同一个绑定实例。
- 旧类名、旧参数签名和原有 task policy 调用保持可用。
- 新代码可通过 `NODE_CONTRACTS[contract_id]` 读取一对一 Contract；`PUBLIC_CONTRACTS` 仅覆盖八个兼容 family。
- Skill ID 是上层接口；它不是 policy ID，也不按 policy 数量机械复制。
