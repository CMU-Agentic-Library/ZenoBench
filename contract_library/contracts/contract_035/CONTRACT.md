# contract_035 — Brace an object with the left hand

Pinch a resting container with the left gripper so it cannot slide while the right hand stirs, wipes or pours into it.

Paired SkillNode: `skill_027` (`brace-object`).

## Precheck

- [all paths] `hand_empty(hand=left)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `steadied(object=$object)` — GT: left_gripper_state, object_pose
- [all paths] `holding(hand=left, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk

## Policy paths

- `left_rim_pinch` when object.location in ['support', 'floor', 'container']: `policy_077($object)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
