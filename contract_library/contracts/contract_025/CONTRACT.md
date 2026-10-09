# contract_025 — Pick an object

Grasp one object with the right gripper and lift it. The grasp is chosen automatically from the object and where it is: from inside a microwave, slide-to-edge + edge pinch for flat items, handle pinch, rectangular or round rim pinch, top pinch, or a two-handed lift for wide items.

Verb: `pick`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation
- [path microwave_cavity] `is_open(articulated=@object.appliance)` — GT: articulation_joint, articulation_annotation
- [path inside_cabinet_or_fridge] `is_open(articulated=@object.appliance)` — GT: articulation_joint, articulation_annotation
- [path on_the_move] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation
- [path two_hand_box] `hand_empty(hand=left)` — GT: gripper_state
- [path two_hand_flat] `hand_empty(hand=left)` — GT: gripper_state
- [path round_rim] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation
- [path top_pinch] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation

## Verifier

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [path two_hand_box] `holding(hand=left, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [path two_hand_flat] `holding(hand=left, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `microwave_cavity` when object.location == 'microwave_cavity': `policy_048($object, @object.appliance)`
- `inside_cabinet_or_fridge` when object.location in ['refrigerator', 'cabinet']: `policy_061($object)`
- `handle_requested` when args.grasp == 'handle' and 'handle_pinch' in object.grasp_types and object.handle_collider: `policy_055($object)`
- `on_the_move` when args.pass_by and 'top_pinch' in object.grasp_types: `policy_052($object, $pass_by)`
- `two_hand_box` when args.hands == 'both' and object.wide_box: `policy_057($object)`
- `two_hand_flat` when args.hands == 'both' and object.flat: `policy_045($object)` -> `policy_056($object)`
- `floor_top` when object.on_floor and 'top_pinch' in object.grasp_types: `policy_065($object)` -> `policy_042($object)` -> `policy_010($object)`
- `flat_overhang_ready` when object.flat and object.edge_ready: `policy_013($object)`
- `flat_edge` when object.flat: `policy_045($object)` -> `policy_013($object)`
- `rect_rim` when 'rim_pinch_rect' in object.grasp_types: `policy_012($object)`
- `round_rim` when 'rim_pinch' in object.grasp_types: `policy_011($object)`
- `handle` when 'handle_pinch' in object.grasp_types and object.handle_collider: `policy_055($object)`
- `top_pinch` when 'top_pinch' in object.grasp_types: `policy_010($object)`
- `annotation_dispatch` when object.grasp_types: `policy_061($object)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
