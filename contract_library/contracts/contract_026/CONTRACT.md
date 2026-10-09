# contract_026 — Place a held object

Put the right-held object down on a support surface or into an open container and release it. How it is put down is chosen automatically from the receptacle and grasp: into a microwave (insert, release, withdraw), into a container, an edge-held flat object slid back over an edge, onto an ordinary surface (optionally near a hint point), or while driving past.

Verb: `place`.

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$receptacle)` — GT: base_pose, scene_annotation
- [path microwave_staged] `is_open(articulated=kitchen_microwave)` — GT: articulation_joint, articulation_annotation
- [path microwave] `is_open(articulated=kitchen_microwave)` — GT: articulation_joint, articulation_annotation
- [path cabinet_or_fridge_shelf] `is_open(articulated=@receptacle.appliance)` — GT: articulation_joint, articulation_annotation
- [path container] `uncovered(container=$receptacle)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [path microwave_staged] `on(object=$object, support=$receptacle)` — GT: object_pose, asset_annotation, support_annotation
- [path microwave_staged] `in_appliance(object=$object, appliance=kitchen_microwave)` — GT: object_pose, appliance_annotation
- [path microwave] `on(object=$object, support=$receptacle)` — GT: object_pose, asset_annotation, support_annotation
- [path microwave] `in_appliance(object=$object, appliance=kitchen_microwave)` — GT: object_pose, appliance_annotation
- [path cabinet_or_fridge_shelf] `on(object=$object, support=$receptacle)` — GT: object_pose, asset_annotation, support_annotation
- [path container] `inside(object=$object, container=$receptacle)` — GT: object_pose, container_profile
- [path on_the_move] `on(object=$object, support=$receptacle)` — GT: object_pose, asset_annotation, support_annotation
- [path edge_held_flat] `on(object=$object, support=$receptacle)` — GT: object_pose, asset_annotation, support_annotation
- [path stove_burner] `on(object=$object, support=$receptacle)` — GT: object_pose, asset_annotation, support_annotation
- [path stove_burner] `on_burner(object=$object, appliance=@receptacle.appliance)` — GT: object_pose, appliance_annotation
- [path surface] `on(object=$object, support=$receptacle)` — GT: object_pose, asset_annotation, support_annotation

## Policy paths

- `microwave_staged` when receptacle.kind == 'support' and receptacle.is_microwave_cavity and robot.right_kind == 'pinch': `policy_018($object, $receptacle)` -> `policy_019($object)` -> `policy_020($object)`
- `microwave` when receptacle.kind == 'support' and receptacle.is_microwave_cavity: `policy_021($object, $receptacle)`
- `cabinet_or_fridge_shelf` when receptacle.kind == 'support' and receptacle.category == 'cabinet_inside' and receptacle.appliance: `policy_015($object, $receptacle, hint=$hint_xy)`
- `container` when receptacle.kind == 'object': `policy_016($object, $receptacle)`
- `on_the_move` when receptacle.kind == 'support' and args.pass_by: `policy_053($object, $receptacle, $pass_by, xy=$hint_xy)`
- `edge_held_flat` when receptacle.kind == 'support' and robot.right_kind == 'edge': `policy_017($object, $receptacle, hint=$hint_xy)`
- `stove_burner` when receptacle.kind == 'support' and receptacle.category == 'cooktop': `policy_015($object, $receptacle, hint=@receptacle.burner_xy)`
- `surface` when receptacle.kind == 'support': `policy_015($object, $receptacle, hint=$hint_xy)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
