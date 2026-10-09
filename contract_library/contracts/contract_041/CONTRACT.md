# contract_041 — Center an object on its support

Push an object back from the support edges until every edge margin is at least the requested value (secures an item left overhanging).

Verb: `center`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `away_from_edge(object=$object, margin_m=$margin_m)` — GT: object_pose, support_annotation

## Policy paths

- `push_inward` when always: `policy_083($object, $margin_m)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
