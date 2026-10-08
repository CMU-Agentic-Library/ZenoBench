# contract_021 — Search for an object

Find an object whose location is unknown: visit the supports of a room in order of distance and aim the head at each surface until the object is seen.

Paired SkillNode: `skill_013` (`search-object`).

## Precheck

- none

## Verifier

- [all paths] `observed(target=$object)` — GT: robot_memory

## Policy paths

- `room_sweep` when always: `policy_070($object, $region)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
