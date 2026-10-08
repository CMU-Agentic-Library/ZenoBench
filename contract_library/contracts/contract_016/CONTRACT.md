# contract_016 — Straighten the waist

Return the waist pitch to upright.

Paired SkillNode: `skill_008` (`straighten-waist`).

## Precheck

- none

## Verifier

- [all paths] `waist_straight()` — GT: waist_joint

## Policy paths

- `upright` when always: `policy_009()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
