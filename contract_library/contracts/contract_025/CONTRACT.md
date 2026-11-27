# contract_025 — Pick an object

Grasp one object with either gripper (the park search's choice; ``hands`` may name one) and lift it. The grasp path is chosen from the object's GT annotation and state: microwave cavity grasp, slide-to-edge + edge pinch for flat items, handle pinch, rectangular or round rim pinch, top pinch, or a two-handed lift for wide items. Flat objects lying on the floor cannot be picked. Navigate to the object itself first (navigate(destination=<the object>)): the base must be within 1.3 m of the object (base_near), and a stand-off beside the furniture it is on can be farther than that from it on a long table or counter.

Paired SkillNode: `skill_017` (`pick-object`).

## Precheck

- [all paths] `hand_empty(hand=any)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation
- [path inside_cabinet_or_fridge] `is_open(articulated=@object.appliance)` — GT: articulation_joint, articulation_annotation
- [path pinch_requested] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation
- [path on_the_move] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation
- [path two_hand_box] `hand_empty(hand=left)` — GT: gripper_state
- [path two_hand_flat] `hand_empty(hand=left)` — GT: gripper_state
- [path floor_top] `on_floor(object=$object)` — GT: object_pose, asset_annotation
- [path flat_overhang_ready] `edge_overhang(object=$object)` — GT: object_pose, asset_annotation, support_annotation
- [path round_rim] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation
- [path top_pinch] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation

## Verifier

- [all paths] `holding(hand=any, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [path two_hand_box] `holding(hand=left, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [path two_hand_flat] `holding(hand=left, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `inside_cabinet_or_fridge` when object.location in ['refrigerator', 'cabinet', 'microwave_cavity']: `policy_061($object, grasp=$grasp, hand=$hands)`
- `handle_requested` when args.grasp == 'handle' and 'handle_pinch' in object.grasp_types and object.handle_collider: `policy_055($object, hand=$hands)`
- `pinch_requested` when args.grasp in ['top', 'side']: `policy_061($object, grasp=$grasp, hand=$hands)`
- `on_the_move` when args.pass_by and 'top_pinch' in object.grasp_types: `policy_052($object, $pass_by)`
- `two_hand_box` when args.hands == 'both' and object.wide_box: `policy_057($object)`
- `two_hand_flat` when args.hands == 'both' and object.flat: `policy_045($object)` -> `policy_056($object)`
- `floor_top` when object.on_floor and 'top_pinch' in object.grasp_types: `policy_010($object, hand=$hands)`
- `flat_overhang_ready` when object.flat and object.edge_ready: `policy_013($object, hand=$hands)`
- `flat_edge` when object.flat: `policy_045($object)` -> `policy_013($object, hand=$hands)`
- `rect_rim` when 'rim_pinch_rect' in object.grasp_types: `policy_012($object, hand=$hands)`
- `round_rim` when 'rim_pinch' in object.grasp_types: `policy_011($object, hand=$hands)`
- `handle` when 'handle_pinch' in object.grasp_types and object.handle_collider: `policy_055($object, hand=$hands)`
- `top_pinch` when 'top_pinch' in object.grasp_types: `policy_010($object, hand=$hands)`
- `annotation_dispatch` when object.grasp_types: `policy_061($object, hand=$hands)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
