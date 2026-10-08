# contract_032 — Lower a held object

Move the held object down until its bottom is at most the given height (e.g. under a low shelf clearance).

Paired SkillNode: `skill_024` (`lower-object`).

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Verifier

- [all paths] `held_below(object=$object, height_m=$height_m)` — GT: object_pose, gripper_state
- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `descend` when always: `policy_093($object, $height_m)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
