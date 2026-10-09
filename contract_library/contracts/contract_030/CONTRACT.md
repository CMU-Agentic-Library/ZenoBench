# contract_030 — Hand an object over to the left hand

Transfer a right-held object into the left gripper and open the right gripper.

Verb: `handover`.

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `hand_empty(hand=left)` — GT: gripper_state

## Verifier

- [all paths] `holding(hand=left, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `right_to_left` when always: `policy_059($object)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
