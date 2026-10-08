# contract_058 — Clear a support

Remove every object from a support surface to a destination receptacle.

Paired SkillNode: `skill_050` (`clear-support`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `support_clear(support=$support)` — GT: object_pose, support_annotation

## Policy paths

- `fetch_each_on_support` when always: `for each item in @support.objects: [fetch](object=$item, receptacle=$receptacle)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
