# contract_061 — Restore an object to its place

Return an object to the support it occupied at the start of the episode.

Paired SkillNode: `skill_053` (`restore-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `not at_initial_place(object=$object)` — GT: object_pose, initial_scene_annotation

## Verifier

- [all paths] `at_initial_place(object=$object)` — GT: object_pose, initial_scene_annotation
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `dispatch_pick_place` when object.initial_support: `policy_092($object)` -> `policy_061($object)` -> `policy_092(@object.initial_support)` -> `policy_015($object, @object.initial_support)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
