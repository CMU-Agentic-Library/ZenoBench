# contract_055 — Fetch an object to a receptacle

Bring one object to a support or container: navigate to it, pick it (noun-selected grasp path), navigate to the receptacle and place it (noun-selected placement path). Each step is a verified Skill Contract.

Paired SkillNode: `skill_047` (`fetch-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [path to_container] `uncovered(container=$receptacle)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [path to_container] `inside(object=$object, container=$receptacle)` — GT: object_pose, container_profile
- [path to_surface] `on(object=$object, support=$receptacle)` — GT: object_pose, asset_annotation, support_annotation

## Policy paths

- `to_container` when receptacle.kind == 'object': `[navigate](destination=$object)` -> `[pick](object=$object)` -> `[navigate](destination=$receptacle)` -> `[place](object=$object, receptacle=$receptacle)`
- `to_surface` when receptacle.kind == 'support': `[navigate](destination=$object)` -> `[pick](object=$object)` -> `[navigate](destination=$receptacle)` -> `[place](object=$object, receptacle=$receptacle)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
