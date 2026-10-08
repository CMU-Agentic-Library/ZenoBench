# contract_023 — Point at a target

Point the closed right fingers at a target (finger axis within 8 deg) to indicate it.

Paired SkillNode: `skill_015` (`point-target`).

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Verifier

- [all paths] `pointing_at(target=$target)` — GT: arm_fk, scene_annotation
- [all paths] `hand_empty(hand=right)` — GT: gripper_state

## Policy paths

- `front` when target.bearing_abs_deg <= 60: `policy_041()` -> `policy_101($target) as aim` -> `policy_038(#aim.position, #aim.rotation, position_tolerance=0.04, rotation_tolerance=0.2)`
- `turn_and_point` when always: `policy_071($target)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
