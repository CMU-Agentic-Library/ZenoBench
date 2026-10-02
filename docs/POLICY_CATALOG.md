# Zeno House policy 能力目录

本目录列出 **60 个目标能力**。状态记录的是当前代码与物理验证程度，
独立代码入口不等于在目标场景物理通过。通用分发入口 `pick/place/open/close/navigate`
以及顺序组合 `pick_and_carry`、`microwave_door_cycle` 不计入本目录。

- `verified`（54）：可调用，且对应物理动作通过过 Isaac Sim smoke run。
- `callable`（6）：有独立 OOP 入口，但尚无该入口成功通过 Isaac Sim 的物理验证；部分路线正在调试。
- `embedded`（0）：动作片段已在较大 policy 内执行，尚无独立入口和结果检查。
- `planned`（0）：当前没有完成该动作的控制器。

`pick_while_moving` 已在 Isaac Sim 中抓起 toy_block：闭爪与抬起均发生在底盘运动期间。
`pick_and_carry` 则是先抓取后移动。`place_while_moving` 已在底盘继续移动时释放苹果并验证桌面支撑。
`bimanual_flat_pick` 曾在 Isaac Sim 中短时抬起书本，但左手在后续携带中滑脱，稳定抓持仍在调试。

机器可读源文件：[catalog.json](../zeno_skills/policies/catalog.json)。
`input` 和 `effect` 是能力摘要，后续 contract 的 `requires/achieves/verifier`
需要逐项细化，不能直接把本目录当作可执行 contract。

## 导航与携物移动

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `empty_navigate` | 空手移动到底盘目标位姿 | `pose` | `base_at(pose)` | `verified` | empty_navigate |
| `carry_navigate` | 右手持物移动并监测滑落 | `pose, held_object` | `base_at(pose) and held` | `verified` | carry_navigate |
| `carry_height_adjust` | 持物时把物品抬到安全携带高度 | `held_object, min_height` | `held_above(min_height)` | `verified` | carry_height_adjust |
| `back_off_with_load` | 持物从家具旁后退到安全距离 | `held_object, distance` | `base_reversed(distance) and held(object)` | `verified` | back_off_with_load |
| `base_rotate_in_place` | 空手收臂后检查占用空间并原地旋转 | `delta_yaw_deg` | `base_yaw_changed` | `verified` | base_rotate_in_place |
| `base_translate_local` | 空手收臂后沿底盘局部坐标短距离直线移动 | `forward_m, left_m` | `base_translated` | `verified` | base_translate_local |

## 躯干与姿态

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `tuck_arm` | 碰撞检查后收起右臂 | `none` | `right_arm_tucked` | `verified` | tuck_arm |
| `set_torso_height` | 设置躯干升降关节位置 | `height_m` | `torso_at(height_m)` | `verified` | set_torso_height |
| `lower_torso` | 降躯干到低位或指定高度 | `height_m?` | `torso_lowered` | `verified` | lower_torso |
| `raise_torso` | 升躯干到高位或指定高度 | `height_m?` | `torso_raised` | `verified` | raise_torso |
| `set_waist_pitch` | 设置腰部前后俯仰角 | `pitch_rad` | `waist_at(pitch_rad)` | `verified` | set_waist_pitch |
| `lean_forward` | 腰部前俯到指定角度 | `pitch_rad?` | `waist_leaned` | `verified` | lean_forward |
| `straighten_waist` | 腰部返回中立姿态 | `none` | `waist_neutral` | `verified` | straighten_waist |
| `prepare_floor_reach` | 协调躯干、腰部和右臂进入地面可达姿态 | `floor_target` | `floor_target_reachable` | `verified` | prepare_floor_reach |

## 抓取

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `pick_top` | 按物品标注的顶部接触点夹取 | `object` | `held(object)` | `verified` | pick_top |
| `pick_round_rim` | 沿圆形容器口沿夹取 | `object` | `held(object)` | `verified` | pick_round_rim |
| `pick_rect_rim` | 沿矩形容器口沿夹取 | `object` | `held(object)` | `verified` | pick_rect_rim；该托盘后续携带时滑脱；单步抓取成功不保证持物移动稳定 |
| `pick_edge` | 先推到桌边，再夹住悬出的平物体 | `object` | `held(object)` | `verified` | pick_edge |
| `pick_floor_corner` | 从地面平物体侧面和顶部夹角抓取 | `object` | `held(object)` | `callable` | pick_floor_corner；toy_car、地面平书和薄 notebook 均未通过稳定夹持；薄 notebook 接触误差 0.0142 m，但抬升 0 m（runs/repair_floor_notebook_v1）；先执行 prepare_floor_reach 的路径也在关节移动时碰撞（v2）。 |
| `grasp_articulated_handle` | 抓住门或抽屉把手 | `articulated_target` | `handle_held` | `verified` | grasp_articulated_handle |
| `release_articulated_handle` | 完成关节移动后放开把手 | `articulated_target` | `handle_released` | `verified` | release_articulated_handle |
| `pick_from_cavity` | 从狭窄腔体正面取物并后撤 | `object, cavity` | `held(object) and outside_cavity` | `verified` | pick_from_cavity；仅验证同一 rig 刚放入杯子的回取路线；预置碗仍无可达抓取记录。中间上方位 TCP 一次短暂偏差 0.182 m，最终接触位偏差 0.0075 m。 |
| `pick_cup_handle` | 从杯把而不是杯沿抓取 | `cup` | `held(cup) by handle` | `verified` | pick_cup_handle；需要实际杯柄接触体：CLI 自动为 pick_cup_handle 目标补充，Python make_rig 需传 handle_objects；仅验证 breakfast_mug 的接触与短距离抬升。 |

## 放置

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `place_surface` | 在指定支撑面寻找空位并放置 | `object, support` | `on(object,support)` | `verified` | place_surface |
| `place_container` | 把物品放进容器 | `object, container` | `inside(object,container)` | `verified` | place_container |
| `place_edge` | 把边缘持握的平物体滑回支撑面 | `object, support` | `on(object,support)` | `verified` | place_edge |
| `microwave_cavity_insert` | 持物从微波炉正面送入腔体，不松爪 | `object, cavity_support` | `held_object_inside_cavity` | `verified` | microwave_cavity_insert |
| `microwave_cavity_release` | 送入腔体后张开夹爪并测量手指位置 | `object` | `object_released_in_cavity` | `verified` | microwave_cavity_release |
| `microwave_cavity_withdraw` | 松爪后撤回手和底盘并验证物体落在炉腔支撑面 | `object` | `on(object,cavity_support)` | `verified` | microwave_cavity_withdraw |
| `place_microwave` | 从正面把物品送入微波炉腔体 | `object, cavity_support` | `inside(object,cavity)` | `verified` | place_microwave |

## 门与抽屉

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `open_handle` | 通过把手打开门或抽屉 | `articulated_target` | `joint_at(open_q)` | `verified` | open_handle |
| `close_handle` | 通过把手关闭门或抽屉 | `articulated_target` | `joint_at(closed_q)` | `verified` | close_handle |
| `open_powered` | 按钮释放并打开动力微波炉门 | `microwave` | `joint_at(open_q)` | `verified` | open_powered |
| `close_powered` | 关闭动力微波炉门 | `microwave` | `joint_at(closed_q)` | `verified` | close_powered |
| `open_revolute_door` | 只选择旋转铰链门的把手轨迹 | `door` | `joint_at(open_q)` | `verified` | open_revolute_door |
| `open_prismatic_drawer` | 只选择滑动抽屉的把手轨迹 | `drawer` | `joint_at(open_q)` | `verified` | open_prismatic_drawer；tidy_toys 的第一只抽屉仍未拉动；另一只厨房抽屉已通过独立物理验证 |

## 推动与接触

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `push` | 按可达性选择推或顶部拖动物品 | `object, support, direction, distance` | `object_displaced` | `verified` | push |
| `push_from_behind` | 从物体后侧水平推动 | `object, support, direction, distance` | `object_displaced` | `verified` | push_from_behind |
| `top_drag` | 压住物体顶部沿支撑面拖动 | `object, support, direction, distance` | `object_displaced` | `verified` | top_drag |
| `slide_to_edge` | 把平物体推到可夹取的支撑面悬边 | `object, support_edge` | `graspable_overhang` | `verified` | slide_to_edge |

## 按钮与电器

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `microwave_button_approach` | 对齐微波炉开门或启动按钮前方的右手指尖 | `microwave, button` | `tcp_aligned_to_button` | `verified` | microwave_button_approach |
| `microwave_button_press` | 从对齐位姿按下微波炉按钮并测量接触位姿 | `microwave, button` | `button_pressed` | `verified` | microwave_button_press |
| `microwave_button_retract` | 按键后撤回右手并检查离开按钮 | `microwave, button` | `tcp_retracted_from_button` | `verified` | microwave_button_retract |
| `microwave_door_clear` | 收臂并退到微波炉门运动区域之外 | `microwave` | `robot_clear_of_door_sweep` | `verified` | microwave_door_clear |
| `microwave_hinge_drive` | 在机器人退离后驱动微波炉门到开或关位置 | `microwave, target` | `joint_at(target)` | `verified` | microwave_hinge_drive |
| `microwave_start` | 按启动按钮并启动任务级加热 | `microwave` | `heating_active` | `verified` | microwave_start |
| `click` | 物理按下有标注的门/启动按钮 | `microwave, button` | `button_contact` | `verified` | click |

## 右臂运动

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `right_tcp_move` | 右手末端按给定位姿移动 | `tcp_pose` | `tcp_at(pose)` | `verified` | right_tcp_move |
| `right_joint_move` | 右臂关节沿碰撞检查路径移动 | `joint_target` | `arm_at(joint_target)` | `verified` | right_joint_move |

## 右夹爪

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `right_gripper_open` | 张开右夹爪到指定宽度 | `width_m` | `finger_gap_at(width_m)` | `verified` | right_gripper_open |
| `right_gripper_close` | 闭合空右夹爪到指定位置并读回指关节；不单独判定抓取 | `width_m` | `finger_positions_measured` | `verified` | right_gripper_close |

## 移动中操作

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `reach_while_moving` | 底盘行进期间同步右臂接近目标 | `target, base_path` | `tcp_at_pregrasp` | `verified` | reach_while_moving |
| `pick_while_moving` | 底盘未停下时完成接触、闭爪和抬起 | `object, base_path` | `held(object) while base_moves` | `verified` | pick_while_moving |
| `place_while_moving` | 底盘未停下时完成放置和松手 | `object, support, base_path` | `on(object,support) while base_moves` | `verified` | place_while_moving |

## 物体姿态修正

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `upright_object` | 把倾倒的物品扶正 | `object` | `upright(object)` | `verified` | upright_object；要求右手先抓住物体；倾倒物体姿态修正尚待 Isaac Sim 验证 |

## 双臂协作

| ID | 能力 | 输入 | 目标状态 | 状态 | 当前入口或缺口 |
|---|---|---|---|---|---|
| `bimanual_flat_pick` | 左右手同时抓取宽书本或托盘 | `flat_object` | `held_by_both_hands` | `callable` | bimanual_flat_pick；book_red 同步接触后物体偏移 0.034 m、双指闭到零且抬升 0 m（runs/repair_bimanual_book_v7）；接触点移入物体 0.035 m 后无法找到无碰撞共享站位（v8）。旧试验短时抬起 0.037 m 后左手滑脱。 |
| `bimanual_box_lift` | 左右手从两侧协同抬起箱子 | `box` | `box_lifted_by_both_hands` | `callable` | bimanual_box_lift；serving_tray 与地面轻篮的双臂接触搜索在 45 秒预算内均找不到无碰撞共享站位（runs/repair_bimanual_box_v3、repair_bimanual_basket_v3）。 |
| `bimanual_carry` | 两只手共同稳定携带大物品 | `held_large_object, pose` | `base_at(pose) and two_hand_hold` | `callable` | bimanual_carry；旧 book_red 双手短时抬起后左手在底盘移动时滑脱；当前没有稳定双手抓持前置状态（runs/bimanual_carry_new_policy）。 |
| `handover_right_to_left` | 把右手物品交给左手 | `object` | `held_by_left_hand` | `callable` | handover_right_to_left；toy_block 无分离的第二抓点；breakfast_bowl 右手抓取成功，但 15 个独立左手预抓候选即使忽略碰撞也超出关节可达性（runs/repair_handover_bowl_v3）；反向夹爪姿态的 30 个候选仍不可达（v5）。 |
| `open_door_while_left_holds` | 左手持物同时用右手开门 | `object, door` | `left_holds(object) and door_open` | `callable` | open_door_while_left_holds；依赖稳定左手持物；handover 尚未通过，未建立可验证的左手持物开门前置状态。 |

## 验证记录

本地仿真 smoke 记录（日期和动作；`runs/` 默认不纳入 Git）：

- `empty_navigate`：Isaac Sim tidy_toys: empty_goto reached (4.492,-2.146,30°), runs/verify_callable_toy_chain, 2026-10-01
- `carry_navigate`：Isaac Sim: pick_and_carry toy_block, 2026-10-01
- `tuck_arm`：Isaac Sim: lower_torso 自动收臂, 2026-10-01
- `set_torso_height`：Isaac Sim: lower_torso/raise_torso, 2026-10-01
- `lower_torso`：Isaac Sim: lower_torso, 2026-10-01
- `raise_torso`：Isaac Sim: raise_torso, 2026-10-01
- `set_waist_pitch`：Isaac Sim: lean_forward/straighten_waist, 2026-10-01
- `lean_forward`：Isaac Sim: lean_forward, 2026-10-01
- `straighten_waist`：Isaac Sim: straighten_waist, 2026-10-01
- `pick_top`：Isaac Sim: pick_top toy_block, 2026-10-01
- `pick_round_rim`：Isaac Sim: pick_round_rim cup, 2026-10-01
- `pick_rect_rim`：Isaac Sim collect_fruits: serving_tray rim pinch lifted 0.0293 m with both fingers in contact; tray slipped during later carry, runs/verify_callable_rect_tray_v3, 2026-10-01
- `pick_edge`：Isaac Sim: pick_edge book_red, 2026-10-01
- `place_surface`：Isaac Sim collect_fruits: apple placed on dining-table support with 0.0139 m XY error and on_support=true, runs/verify_callable_surface_apple, 2026-10-01
- `place_container`：Isaac Sim collect_fruits: apple placed inside fruit_basket (measured radial offset 0.075 m < 0.143 m), runs/verify_callable_container_apple, 2026-10-01
- `place_edge`：Isaac Sim shelve_books: edge-held book_red released onto desk support, on_support true and tilt 1.1 deg, runs/verify_callable_place_edge, 2026-10-01
- `microwave_cavity_insert`：Isaac Sim: heat_breakfast fridge -> microwave -> dining table, 100% progress, 2026-10-01; runs/heat_breakfast/result.json
- `microwave_cavity_release`：Isaac Sim: heat_breakfast fridge -> microwave -> dining table, 100% progress, 2026-10-01; runs/heat_breakfast/result.json
- `microwave_cavity_withdraw`：Isaac Sim: heat_breakfast fridge -> microwave -> dining table, 100% progress, 2026-10-01; runs/heat_breakfast/result.json
- `place_microwave`：Isaac Sim dedicated appliance fixture: cup picked from cabinet top and physically inserted through open microwave door; measured on inside_floor true, in_cavity true, tilt 0 deg; runs/verify_callable_microwave_cycle_cup, 2026-10-01
- `open_handle`：Isaac Sim: Manual cabinet hinge moved from closed to -1.379 rad, runs/verify_callable_handle_cabinet, 2026-10-01
- `close_handle`：Isaac Sim: Manual cabinet hinge returned from -1.379 to -0.011 rad, runs/verify_callable_handle_cabinet, 2026-10-01
- `open_powered`：Isaac Sim heat_breakfast_combo: powered microwave opened to -1.400 rad, runs/verify_callable_microwave, 2026-10-01
- `close_powered`：Isaac Sim heat_breakfast_combo: powered microwave closed to -0.000002 rad, runs/verify_callable_microwave, 2026-10-01
- `push`：Isaac Sim: pick_edge book_red 内部推书, 2026-10-01
- `microwave_button_approach`：Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
- `microwave_button_press`：Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
- `microwave_button_retract`：Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
- `microwave_door_clear`：Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
- `microwave_hinge_drive`：Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
- `microwave_start`：Isaac Sim heat_breakfast_combo: start button activated heating with oatmeal inside, runs/verify_callable_microwave, 2026-10-01
- `click`：Isaac Sim: click kitchen_microwave door, 2026-10-01
- `carry_height_adjust`：Isaac Sim tidy_toys: held toy_block bottom raised to 0.1459 m for 0.15 m target (0.02 m tolerance), runs/verify_callable_toy_chain, 2026-10-01
- `back_off_with_load`：Isaac Sim tidy_toys: held toy_block while base reversed 0.120 m, runs/verify_callable_toy_chain, 2026-10-01
- `base_rotate_in_place`：Isaac Sim: tuck_arm; base_rotate_in_place 10; base_translate_local 0.1, 2026-10-01; runs/atomic_base_smoke/result.json
- `base_translate_local`：Isaac Sim: tuck_arm; base_rotate_in_place 10; base_translate_local 0.1, 2026-10-01; runs/atomic_base_smoke/result.json
- `right_tcp_move`：Isaac Sim tidy_toys: TCP moved +0.04 m vertically with 0.0039 m position and 0.0086 rad orientation error, runs/verify_callable_arm_v4, 2026-10-01
- `right_joint_move`：Isaac Sim tidy_toys: right_arm_joint_5 moved to 0.0318 rad for 0.04 rad command (0.03 rad tolerance), runs/verify_callable_arm_v4, 2026-10-01
- `right_gripper_open`：Isaac Sim: right_gripper_open 0.04 / right_gripper_close 0.0, 2026-10-01; runs/atomic_gripper_smoke/result.json
- `right_gripper_close`：Isaac Sim: right_gripper_open 0.04 / right_gripper_close 0.0, 2026-10-01; runs/atomic_gripper_smoke/result.json
- `prepare_floor_reach`：Isaac Sim tidy_toys: lowered torso to -0.537 m, pitched waist 0.292 rad, reached collision-checked pregrasp above toy_block with 0.0043 m TCP error, 2026-10-01
- `push_from_behind`：Isaac Sim shelve_books: book_red displaced 0.0568 m along requested 0.060 m push, runs/verify_callable_push_drag, 2026-10-01
- `top_drag`：Isaac Sim shelve_books: book_green moved 0.057 m by a 0.040 m top-contact drag, runs/verify_callable_top_drag_v4, 2026-10-01
- `slide_to_edge`：Isaac Sim: slide_to_edge book_red, 0.0885 m overhang, 2026-10-01
- `grasp_articulated_handle`：Isaac Sim: grasp_articulated_handle breakfast_fridge, both fingers contacted, 2026-10-01
- `release_articulated_handle`：Isaac Sim: release_articulated_handle breakfast_fridge, both fingers opened, 2026-10-01
- `pick_from_cavity`：Isaac Sim dedicated microwave cup fixture: open, rim pick, cavity place, same-rig cavity retrieval; four contract postconditions passed, cup lift 0.0742 m and body 0.047 m outside mouth; runs/final_contract_microwave, 2026-10-02
- `open_revolute_door`：Isaac Sim: open_revolute_door breakfast_fridge, joint reached -0.527 rad for -0.611 rad goal, 2026-10-01
- `open_prismatic_drawer`：Isaac Sim base scene: kitchen drawer joint moved 0 to -0.130 rad/m toward -0.169 target with physical handle contact, runs/verify_callable_drawer, 2026-10-01
- `reach_while_moving`：Isaac Sim: 0.10 m base travel with concurrent right-arm reach, 0.003 m TCP error, 2026-10-01
- `pick_while_moving`：Isaac Sim tidy_toys: toy_block grasped while base traveled 0.072 m; closure tick 1138, lift tick 1255, base motion ended tick 1403; object lifted 0.065 m, 2026-10-01
- `place_while_moving`：Isaac Sim collect_fruits: apple released onto dining table at tick 3257 while base moved 0.078 m; base ended tick 3472, support bottom error 0.0377 m, runs/verify_callable_place_while_moving_apple_v2, 2026-10-01
- `upright_object`：Isaac Sim tidy_toys: toy_block physically tipped to 29.129 deg in right grasp, UprightObjectPolicy reduced tilt to 0.951 deg, runs/verify_callable_upright, 2026-10-01
- `pick_cup_handle`：Isaac Sim breakfast_setup original scene: mug handle pinch lifted 0.0226 m with fingers 0.0121/0.0102 m open; runs/final_mug_handle, 2026-10-02
