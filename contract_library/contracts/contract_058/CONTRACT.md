# contract_058 — Clear a support

Remove every object from a support surface to a destination receptacle.

Verb: `clear`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `support_clear(support=$support)` — GT: object_pose, support_annotation

## Policy paths

- `fetch_each_on_support` when always: `for each item in @support.objects: [fetch](object=$item, receptacle=$receptacle)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
