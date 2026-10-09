# contract_064 — Wait for a duration

Do nothing for the given simulated time (an appliance cycle running, an object settling).

Verb: `wait`.

## Precheck

- none

## Verifier

- [all paths] `waited(seconds=$seconds)` — GT: sim_clock

## Policy paths

- `idle` when always: `policy_103($seconds)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
