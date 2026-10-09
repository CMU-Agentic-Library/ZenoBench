# contract_040 — Separate an object from its neighbour

Push an object straight away from its closest neighbour until there is room for a finger (>= 3.5 cm gap) without leaving the support.

Verb: `separate`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `grasp_clearance(object=$object)` — GT: object_pose, asset_annotation

## Policy paths

- `push_apart` when always: `policy_080($object)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
