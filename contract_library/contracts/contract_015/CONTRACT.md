# contract_015 — Bend the waist

Pitch the waist forward to extend the reach over a deep surface.

Paired SkillNode: `skill_007` (`bend-waist`).

## Precheck

- none

## Verifier

- [all paths] `waist_bent(min_pitch_rad=0.2)` — GT: waist_joint

## Policy paths

- `to_pitch` when args.pitch_rad: `policy_007($pitch_rad)`
- `full` when always: `policy_008()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
