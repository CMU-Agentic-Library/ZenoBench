# contract_015 — Bend the waist

Pitch the waist forward to extend the reach over a deep surface. A held object pitches forward with the body by the same angle.

Paired SkillNode: `skill_007` (`bend-waist`).

## Precheck

- none

## Verifier

- [all paths] `not waist_straight()` — GT: waist_joint
- [path to_pitch] `waist_bent(min_pitch_rad=$pitch_rad)` — GT: waist_joint
- [path full] `waist_bent(min_pitch_rad=0.6)` — GT: waist_joint

## Policy paths

- `to_pitch` when args.pitch_rad is given: `policy_007($pitch_rad)`
- `full` when always: `policy_008()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
