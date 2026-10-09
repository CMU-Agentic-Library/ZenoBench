# contract_024 — Present a held object

Hold the carried object in front of the body at 0.9-1.4 m height, inside the head camera view.

Verb: `present`.

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Verifier

- [all paths] `presenting(object=$object)` — GT: object_pose, base_pose, head_fk
- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `front_of_head` when always: `policy_072($object)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
