# contract_061 — Restore an object to its place

Return an object to the spot it occupied at the start of the episode (the free spot of its starting support closest to it); also works when it was only moved along that support. Success is judged on the support, not the exact spot.

Paired SkillNode: `skill_053` (`restore-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `at_initial_place(object=$object)` — GT: object_pose, initial_scene_annotation
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `dispatch_pick_place` when object.initial_support: `policy_092($object)` -> `policy_061($object)` -> `policy_092(@object.initial_support)` -> `policy_015($object, @object.initial_support, hint=@object.initial_xy)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
