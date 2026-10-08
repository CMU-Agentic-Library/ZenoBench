# contract_069 — Nod the head

Pitch the head down and up twice (acknowledgement gesture).

Paired SkillNode: `skill_061` (`nod-head`).

## Precheck

- none

## Verifier

- [all paths] `nodded()` — GT: robot_memory (head joint samples)

## Policy paths

- `pitch_cycles` when always: `policy_105()`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
