# contract_055 — Fetch an object to a receptacle

Bring one object to a support or container: the robot goes to the object, picks it up, carries it to the receptacle and puts it there.

Verb: `fetch`.

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

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
