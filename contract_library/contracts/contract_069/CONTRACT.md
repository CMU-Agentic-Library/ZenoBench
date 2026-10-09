# contract_069 — Nod the head

Pitch the head down and up twice (acknowledgement gesture).

Verb: `nod`.

## Precheck

- none

## Verifier

- [all paths] `nodded()` — GT: robot_memory (head joint samples)

## Policy paths

- `pitch_cycles` when always: `policy_105()`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
