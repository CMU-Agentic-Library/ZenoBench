# contract_063 — Sidestep the base

Move the base sideways by a signed distance (left positive) without turning, also while carrying a load; aligns the arm with a target that is a little to the side.

Paired SkillNode: `skill_055` (`sidestep-base`).

## Precheck

- none

## Verifier

- [all paths] `sidestepped(distance_m=$distance_m)` — GT: base_pose (before/after)

## Policy paths

- `sideways` when always: `policy_114($distance_m)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
