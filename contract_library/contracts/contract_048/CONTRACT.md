# contract_048 — Open a door or drawer

Open a door, drawer, refrigerator door or microwave door to its annotated open value. The path follows the part: powered microwave (door button + hinge), refrigerator handle, drawer handle pull, hinged door side-hook ride, or a door opened by the right hand while the left hand holds a load.

Paired SkillNode: `skill_040` (`open-articulated`).

## Precheck

- [all paths] `base_near(place=$articulated)` — GT: base_pose, scene_annotation
- [path powered_microwave] `hand_empty(hand=right)` — GT: gripper_state
- [path left_holds_load] `hand_empty(hand=right)` — GT: gripper_state
- [path refrigerator] `hand_empty(hand=right)` — GT: gripper_state
- [path drawer] `hand_empty(hand=right)` — GT: gripper_state
- [path hinged_door] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `is_open(articulated=$articulated)` — GT: articulation_joint, articulation_annotation

## Policy paths

- `powered_microwave` when articulated.powered: `policy_024($articulated)`
- `left_holds_load` when robot.left_held and articulated.type == 'revolute': `policy_060(@robot.left_object, $articulated)`
- `refrigerator` when articulated.category == 'refrigerator': `policy_003()` -> `policy_022($articulated, goal=@articulated.wide_open_q)`
- `drawer` when articulated.type == 'prismatic': `policy_003()` -> `policy_046($articulated)` -> `policy_050($articulated)` -> `policy_047($articulated)`
- `hinged_door` when articulated.type == 'revolute': `policy_003()` -> `policy_046($articulated)` -> `policy_049($articulated)` -> `policy_047($articulated)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
