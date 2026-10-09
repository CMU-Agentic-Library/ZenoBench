# contract_014 — Stand up to full height

Raise the torso lift to its top travel height.

Verb: `stand`.

## Precheck

- none

## Verifier

- [all paths] `torso_raised()` — GT: torso_joint

## Policy paths

- `highest` when always: `policy_006()`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
