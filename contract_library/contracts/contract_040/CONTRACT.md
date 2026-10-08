# contract_040 — Separate an object from its neighbour

Push an object straight away from its closest neighbour until there is room for a finger (>= 3.5 cm gap) without leaving the support.

Paired SkillNode: `skill_032` (`separate-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation
- [all paths] `not grasp_clearance(object=$object)` — GT: object_pose, asset_annotation

## Verifier

- [all paths] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation

## Policy paths

- `push_apart` when always: `policy_080($object)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
