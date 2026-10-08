# contract_049 — Close a door or drawer

Close a door, drawer or appliance door to within 0.10 rad / 4 cm of closed. A powered microwave door closes from its hinge-clearance pose, also while the robot carries a load.

Paired SkillNode: `skill_041` (`close-articulated`).

## Precheck

- [all paths] `base_near(place=$articulated)` — GT: base_pose, scene_annotation
- [path handle_push] `hand_empty(hand=right)` — GT: gripper_state
- [path dispatch] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `is_closed(articulated=$articulated)` — GT: articulation_joint, articulation_annotation

## Policy paths

- `powered_loaded` when articulated.powered and robot.right_held: `policy_030($articulated)` -> `policy_031($articulated, target=close)`
- `powered` when articulated.powered: `policy_025($articulated)`
- `handle_push` when articulated.has_handle: `policy_003()` -> `policy_023($articulated)`
- `dispatch` when always: `policy_063($articulated)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
