# contract_023 — Point at a target

Point the closed fingers at a target (finger axis within 8 deg) to indicate it.

Paired SkillNode: `skill_015` (`point-target`).

## Precheck

- [all paths] `hand_empty(hand=any)` — GT: gripper_state

## Verifier

- [all paths] `pointing_at(target=$target)` — GT: arm_fk, scene_annotation
- [all paths] `hand_empty(hand=any)` — GT: gripper_state

## Policy paths

- `front` when target.bearing_abs_deg <= 60: `policy_071($target)`
- `turn_and_point` when always: `policy_071($target)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
