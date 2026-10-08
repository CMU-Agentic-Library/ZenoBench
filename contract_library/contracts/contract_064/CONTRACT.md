# contract_064 — Wait for a duration

Do nothing for the given simulated time (an appliance cycle running, an object settling).

Paired SkillNode: `skill_056` (`wait-duration`).

## Precheck

- none

## Verifier

- [all paths] `waited(seconds=$seconds)` — GT: sim_clock

## Policy paths

- `idle` when always: `policy_103($seconds)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
