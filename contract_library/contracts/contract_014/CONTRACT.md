# contract_014 — Stand up to full height

Raise the torso lift to its top travel height.

Paired SkillNode: `skill_006` (`stand-torso`).

## Precheck

- none

## Verifier

- [all paths] `torso_raised()` — GT: torso_joint

## Policy paths

- `highest` when always: `policy_006()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
