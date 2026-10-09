# contract_016 — Straighten the waist

Return the waist pitch to upright.

Verb: `straighten`.

## Precheck

- none

## Verifier

- [all paths] `waist_straight()` — GT: waist_joint

## Policy paths

- `upright` when always: `policy_009()`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
