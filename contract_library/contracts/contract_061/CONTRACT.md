# contract_061 — Restore an object to its place

Return an object to the support it occupied at the start of the episode.

Verb: `restore`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `at_initial_place(object=$object)` — GT: object_pose, initial_scene_annotation
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `dispatch_pick_place` when object.initial_support: `policy_092($object)` -> `policy_061($object)` -> `policy_092(@object.initial_support)` -> `policy_015($object, @object.initial_support)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
