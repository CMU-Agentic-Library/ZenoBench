# contract_059 — Empty a container

Take every object out of a container and put it on/into a destination receptacle.

Paired SkillNode: `skill_051` (`empty-container`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `uncovered(container=$container)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `container_empty(container=$container)` — GT: object_pose, container_profile

## Policy paths

- `pour_out` when 'rim_pinch' in container.grasp_types and receptacle.kind == 'object': `[navigate](destination=$container)` -> `[pick](object=$container)` -> `[navigate](destination=$receptacle)` -> `[pour](source=$container, target=$receptacle)` -> `[place](object=$container, receptacle=@container.support)`
- `pick_each_inside` when always: `for each item in @container.contents: policy_092($container) -> policy_061($item) -> [navigate](destination=$receptacle) -> [place](object=$item, receptacle=$receptacle)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
