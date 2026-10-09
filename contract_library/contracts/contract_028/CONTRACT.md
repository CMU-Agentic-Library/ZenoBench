# contract_028 — Stack an object on another

Set the held object centred on the top face of another object (block on block, plate on plate).

Verb: `stack`.

## Precheck

- [all paths] `holding(hand=right, object=$object)` — GT: gripper_state, finger_joints, object_pose, arm_fk
- [all paths] `base_near(place=$base)` — GT: base_pose, scene_annotation
- [all paths] `top_clear(object=$base)` — GT: object_pose, asset_annotation

## Verifier

- [all paths] `on_top_of(object=$object, base=$base)` — GT: object_pose, asset_annotation
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `top_face` when always: `policy_074($object, $base)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
