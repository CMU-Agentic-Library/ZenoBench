# contract_056 — Collect objects into a container

Put every listed object into one container (fetch each in turn).

Paired SkillNode: `skill_048` (`collect-objects`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `uncovered(container=$container)` — GT: object_pose, container_profile, asset_tags

## Verifier

- [all paths] `all_inside(objects=$objects, container=$container)` — GT: object_pose, container_profile

## Policy paths

- `fetch_each` when always: `for each item in $objects: [fetch](object=$item, receptacle=$container)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
