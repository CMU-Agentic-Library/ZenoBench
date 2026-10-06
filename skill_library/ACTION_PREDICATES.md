# Skill 动作谓词与任务状态

每个 Skill 有一个唯一的动词＋名词动作谓词；括号内是 Contract 输入槽位，运行时绑定真实场景实例。只有配对 Contract 的 `verified_by` 状态事实全通过，才报告该动作已验证。

同一个 `on`、`inside` 或 `joint_closed` 状态事实可以由多个 Skill 建立，供任务目标和其他 Skill 的前置条件共用。

| Skill | 动作谓词 | verifier 测得的状态事实 |
| --- | --- | --- |
| `skill_001` | `navigate_base(pose)` | `base_at` |
| `skill_002` | `transport_carried_object(object, pose)` | `base_at`, `grasp_preserved` |
| `skill_003` | `open_articulated_joint(articulated)` | `joint_open_enough` |
| `skill_004` | `acquire_object(object)` | `held_by_right_hand`, `object_lifted` |
| `skill_005` | `deposit_object_on_support(object, support)` | `on`, `right_hand_empty` |
| `skill_006` | `insert_object_in_container(object, container)` | `inside`, `right_hand_empty` |
| `skill_007` | `close_articulated_joint(articulated)` | `joint_closed` |
| `skill_008` | `shove_object_along_support(object, support, direction_xy, distance_m)` | `displacement_along` |
| `skill_009` | `press_appliance_door_button(appliance)` | `button_pressed_this_call` |
| `skill_010` | `start_microwave_heating(appliance)` | `button_pressed_this_call`, `heating_active` |
| `skill_011` | `tuck_right_arm()` | `posture_at_target` |
| `skill_012` | `set_torso_height(height_m)` | `posture_at_target` |
| `skill_013` | `pitch_waist(pitch_rad)` | `posture_at_target` |
| `skill_014` | `load_microwave_cavity(object, support)` | `on`, `right_hand_empty` |
| `skill_015` | `retrieve_cavity_object(object, cavity)` | `held_by_right_hand`, `object_lifted` |
| `skill_016` | `pinch_flat_object_edge(object)` | `held_by_right_hand`, `object_lifted` |
| `skill_017` | `grip_cup_handle(object)` | `held_by_right_hand`, `object_lifted` |
| `skill_018` | `intercept_moving_object(object, base_path)` | `held_by_right_hand`, `object_lifted` |
| `skill_019` | `deliver_object(object, support, base_path)` | `on`, `right_hand_empty` |
| `skill_020` | `scoop_floor_object(object)` | `held_by_right_hand`, `object_lifted` |
| `skill_021` | `convoy_bimanual_load(object, pose)` | `base_at`, `grasp_preserved` |
| `skill_022` | `swing_articulated_door(object, articulated)` | `joint_open_enough` |
| `skill_023` | `trigger_microwave_door_opening(appliance)` | `joint_open_enough` |
| `skill_024` | `shut_microwave_door(appliance)` | `joint_closed` |
| `skill_025` | `pull_manual_handle(articulated)` | `joint_open_enough` |
| `skill_026` | `push_manual_handle(articulated)` | `joint_closed` |
| `skill_027` | `clamp_object_top(object)` | `held_by_right_hand`, `object_lifted` |
| `skill_028` | `grasp_round_rim(object)` | `held_by_right_hand`, `object_lifted` |
| `skill_029` | `clasp_rectangular_rim(object)` | `held_by_right_hand`, `object_lifted` |
| `skill_030` | `lay_edge_held_flat_object(object, support)` | `on`, `right_hand_empty` |
| `skill_031` | `lower_torso()` | `posture_at_target` |
| `skill_032` | `raise_torso()` | `posture_at_target` |
| `skill_033` | `lean_waist()` | `posture_at_target` |
| `skill_034` | `straighten_waist()` | `posture_at_target` |
| `skill_035` | `expose_flat_object_edge(object)` | `edge_overhang_ready` |
| `skill_036` | `orient_held_object(object)` | `object_upright` |
| `skill_037` | `stand_object_on_support(object, support)` | `on`, `right_hand_empty`, `object_upright` |
| `skill_038` | `position_object_near_hint(object, support, hint_xy, max_offset_m)` | `on`, `right_hand_empty`, `within_hint_radius` |
| `skill_039` | `align_upright_object_near_hint(object, support, hint_xy, max_offset_m)` | `on`, `right_hand_empty`, `object_upright`, `within_hint_radius` |
| `skill_040` | `attain_food_temperature(object, min_temp_c)` | `temperature_at_least` |
| `skill_041` | `hoist_carried_object(object, min_bottom_z)` | `held_object_above_height` |
| `skill_042` | `retreat_carried_object(object, distance_m)` | `base_backed_off`, `grasp_preserved` |
| `skill_043` | `pivot_base(delta_yaw_deg)` | `base_yaw_changed` |
| `skill_044` | `translate_base(forward_m)` | `base_translated_locally` |
| `skill_045` | `nudge_supported_object(object, support, direction_xy, distance_m)` | `displacement_along` |
| `skill_046` | `drag_supported_object(object, support, direction_xy, distance_m)` | `displacement_along` |
| `skill_047` | `unfold_hinged_door(articulated)` | `joint_open_enough` |
| `skill_048` | `extend_drawer(articulated)` | `joint_open_enough` |
| `skill_049` | `ready_floor_object(object)` | `floor_reach_ready` |
| `skill_050` | `clear_microwave_door_sweep(articulated)` | `microwave_sweep_clear` |

## 与 ZenoBench 任务目标的关系

[goal_predicates.json](goal_predicates.json) 把 8 类目标子句映射到候选动作和最终 TaskEvaluator 检查。[task_coverage.json](task_coverage.json) 对照当前 10 个任务的 42 条子句。

`near` 是组内两两距离，单次 `within_hint_radius` 只检查一个物体到提示点；`not_dropped` 是跨动作的不变量，不可能由单个 Skill 谓词保证。目标可表达不代表所有场景都物理成功。
