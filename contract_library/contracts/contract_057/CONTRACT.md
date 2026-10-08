# contract_057 — Sort objects by category

Put each listed object into the container mapped to its category tag (e.g. fruit -> basket, toy -> toy box).

Paired SkillNode: `skill_049` (`sort-objects`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `sorted_by_category(objects=$objects, rule=$rule)` — GT: object_pose, asset_tags, container_profile

## Policy paths

- `fetch_by_tag` when always: `for each item in $objects: [fetch](object=$item, receptacle=@item.sort_target)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
