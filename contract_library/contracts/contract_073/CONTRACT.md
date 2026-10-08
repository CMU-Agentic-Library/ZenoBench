# contract_073 — Touch an object

Bring the closed fingertips onto an object's top and back off without moving it (probe / indicate by contact).

Paired SkillNode: `skill_065` (`touch-object`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=$object)` — GT: base_pose, scene_annotation

## Verifier

- [all paths] `touched(object=$object)` — GT: event_log (fingertip contact), object_pose (before/after)
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `fingertip_top` when always: `policy_107($object)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
