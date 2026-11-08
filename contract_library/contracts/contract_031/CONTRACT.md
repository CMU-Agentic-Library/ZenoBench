# contract_031 — Lift a held object

Raise the held object until its bottom is at least the given height, in world metres (a table top is about 0.9 m) or above a named reference object (e.g. above a bin rim or a furniture edge before carrying).

Paired SkillNode: `skill_023` (`lift-object`).

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Verifier

- [all paths] `held_above(object=$object, height_m=$height_m)` — GT: object_pose, gripper_state
- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `raise` when always: `policy_034($height_m)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
