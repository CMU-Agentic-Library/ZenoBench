# contract_013 — Crouch the torso

Lower the torso lift to its bottom (or a requested height) for floor and low-shelf work.

Verb: `crouch`.

## Precheck

- none

## Verifier

- [all paths] `not torso_raised()` — GT: torso_joint
- [path to_height] `torso_at(height_m=$height_m)` — GT: torso_joint
- [path lowest] `torso_lowered()` — GT: torso_joint

## Policy paths

- `to_height` when args.height_m: `policy_004($height_m)`
- `lowest` when always: `policy_005()`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
