# contract_072 — Square an object

Align an object's edges with its support's edges (yaw within 5 deg): pick it, turn it by the measured yaw error and set it back down at the same spot.

Paired SkillNode: `skill_064` (`square-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `squared(object=$object)` — GT: object_pose, support_annotation
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `pick_rotate_place` when 'top_pinch' in object.grasp_types: `policy_108($object) as sq` -> `policy_010($object)` -> `policy_075($object, #sq.degrees)` -> `policy_015($object, @object.support, hint=#sq.xy)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
