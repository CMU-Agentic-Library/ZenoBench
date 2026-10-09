# contract_021 — Search for an object

Find an object whose location is unknown: visit the supports of a room in order of distance and aim the head at each surface until the object is seen.

Verb: `search`.

## Precheck

- none

## Verifier

- [all paths] `observed(target=$object)` — GT: robot_memory

## Policy paths

- `room_sweep` when always: `policy_070($object, $region)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
